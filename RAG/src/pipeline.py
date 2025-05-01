# src/pipeline.py
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import hashlib
import time

from .readers.factory import read_document, get_supported_formats
from .utils.logger import logger
from .utils.error_handler import PipelineError
from .config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR
from .readers.schema import Document
from .utils.state_manager import StateManager
from .chunkers.text_chunker import TextChunker
from .embeddings.embedding_processor import EmbeddingProcessor

# Note: The Document class structure is defined in .readers.schema.py.
# The error observed indicates that the Document class definition in schema.py
# does not include a field or attribute named 'chunks', and likely prevents
# dynamic attribute assignment. This file (pipeline.py) calls the chunker,
# which attempts to add 'chunks', leading to the error. The fix is in schema.py.


class DocumentPipeline:
    """
    Main pipeline for processing documents through various stages.
    Currently implements the reading stage with tracking.
    """

    def __init__(self, input_dir: Optional[Union[str, Path]] = None, output_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the document processing pipeline.

        Args:
            input_dir: Directory containing files to process. Defaults to RAW_DATA_DIR.
            output_dir: Directory to store processed outputs. Defaults to PROCESSED_DATA_DIR.
        """
        self.input_dir = Path(input_dir) if input_dir else RAW_DATA_DIR
        self.output_dir = Path(output_dir) if output_dir else PROCESSED_DATA_DIR
        # Pass the correct path to the state file for StateManager
        self.state_manager = StateManager(state_file=str(LOGS_DIR / "pipeline_state.json"))

        # Ensure directories exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize run_id
        self.run_id = None

        logger.info(f"Pipeline initialized with input directory: {self.input_dir}")
        logger.info(f"Pipeline initialized with output directory: {self.output_dir}")

    def generate_file_id(self, file_path: Path) -> str:
        """
        Generate a unique file ID based on the file path and stats.

        Args:
            file_path: Path to the file.

        Returns:
            A unique identifier for the file.
        """
        file_stat = file_path.stat()
        unique_str = f"{file_path.absolute()}_{file_stat.st_mtime}_{file_stat.st_size}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def get_files_to_process(self, extensions: Optional[List[str]] = None) -> List[Path]:
        """
        Get list of files to process from the input directory.

        Args:
            extensions: Optional list of extensions to filter by. If None, uses all supported formats.

        Returns:
            List of file paths to process.
        """
        if extensions is None:
            extensions = get_supported_formats()

        files = []
        for ext in extensions:
            # Normalize extension format
            if not ext.startswith('.'):
                ext = f".{ext}"

            # Find files with this extension
            files.extend(list(self.input_dir.glob(f"**/*{ext}")))

        logger.info(f"Found {len(files)} files to process in {self.input_dir}")
        return files

    def read_document(self, file_path: Path) -> Document:
        """
        Read a document and track the process.

        Args:
            file_path: Path to the document.

        Returns:
            The read Document object.

        Raises:
            PipelineError: If reading fails.
        """
        file_id = self.generate_file_id(file_path)

        try:
            # Mark stage as started
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="read",
                success=False,  # Initially mark as unsuccessful
                metadata={
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "file_extension": file_path.suffix,
                    "file_size_bytes": file_path.stat().st_size
                }
            )

            # Read the document
            logger.info(f"Reading document: {file_path}")
            document = read_document(file_path)

            # Mark stage as successful
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="read",
                success=True,
                metadata={
                    "document_type": document.__class__.__name__,
                    "word_count": getattr(document.metadata, "word_count", None),
                    "character_count": getattr(document.metadata, "character_count", None)
                }
            )

            return document

        except Exception as e:
            # Mark stage as failed
            error_message = f"Failed to read document {file_path}: {str(e)}"
            logger.error(error_message)
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="read",
                success=False,
                error=error_message
            )
            raise PipelineError(error_message, original_error=e)

    # def process_file(self, file_path: Path) -> Optional[Document]:
    #     """
    #     Process a single file through all implemented pipeline stages with
    #     special handling for large files.

    #     Args:
    #         file_path: Path to the file to process.

    #     Returns:
    #         The processed Document or None if processing failed (specifically if read fails).
    #     """
    #     file_id = self.generate_file_id(file_path)
    #     document = None # Initialize document to None

    #     try:
    #         # Reading stage
    #         document = self.read_document(file_path)

    #     except PipelineError:
    #         # If reading fails, process_file returns None and the file is marked as failed in read_document
    #         return None # Stop processing this file

    #     # Chunking stage (only proceeds if reading was successful)
    #     # We wrap this in a try-except block to catch errors but allow
    #     # processing to potentially continue to the next file.
    #     try:
    #         # Mark stage as started
    #         self.state_manager.update_file_state(
    #             file_id=file_id,
    #             stage="chunk",
    #             success=False,  # Initially mark as unsuccessful
    #         )

    #         # Create a text chunker with default settings
    #         # You can customize these settings as needed
    #         chunker = TextChunker(
    #             chunk_size=1000,  # Characters per chunk
    #             chunk_overlap=200,  # Characters overlap between chunks
    #             chunking_method="recursive"  # Using recursive text splitter
    #         )

    #         # Chunk the document
    #         logger.info(f"Chunking document: {file_path}")
    #         # The potential AttributeError is caught within chunker.chunk_document now
            
       
    #         document = chunker.chunk_document(document)
            
    #         # >>> ADD THESE PRINT STATEMENTS TO INSPECT CHUNKS <<<
    #         print(f"\n--- Chunks for file: {file_path.name} ---")
    #         if hasattr(document, 'chunks') and isinstance(document.chunks, list):
    #             print(f"Total chunks created: {len(document.chunks)}")
    #             # Print the first few chunks (e.g., up to 3) for inspection
    #             for i, chunk in enumerate(document.chunks[:3]):
    #                 print(f"\nChunk {i+1}:")
    #                 print(f"Content preview: {chunk[:500]}{'...' if len(chunk) > 500 else ''}") # Print first 500 chars
    #                 print(f"Full Content: {chunk}") # Uncomment this if you want to see the full chunk, but be cautious with large chunks

    #             if len(document.chunks) > 3:
    #                 print("\n... and more chunks.")
    #         else:
    #             print("Chunking failed or 'chunks' attribute not found/is not a list on the document object.")
    #         print("---------------------------------------------\n")
    #         # >>> END PRINT STATEMENTS <<<
            

    #         # Mark stage as successful
    #         self.state_manager.update_file_state(
    #             file_id=file_id,
    #             stage="chunk",
    #             success=True,
    #             metadata={
    #                 # Check if chunks attribute exists before accessing it for count
    #                 "chunks_count": len(document.chunks) if hasattr(document, "chunks") and isinstance(document.chunks, list) else 0,
    #                 "chunking_method": "recursive",
    #             }
    #         )

    #     except PipelineError as pe:
    #         # Catch the PipelineError raised by TextChunker on failure (including AttributeError)
    #         error_message = f"Failed to chunk document {file_path}: {pe}"
    #         logger.error(error_message)
    #         self.state_manager.update_file_state(
    #             file_id=file_id,
    #             stage="chunk",
    #             success=False,
    #             error=error_message
    #         )
    #         # The document object might be partially updated or not at all,
    #         # but the pipeline run will continue to the next file.
    #         # The pipeline's run method considers the file successful if process_file
    #         # returns a document, regardless of chunking failure.
    #         # If you want chunking failure to mark the file as overall failed,
    #         # you would return None here. Keeping current behavior where only read failure fails the file.
    #         pass # Continue with other stages if implemented, despite chunking failure

    #     except Exception as e:
    #          # Catch any other unexpected errors during process_file stages after reading
    #          error_message = f"An unexpected error occurred during processing file {file_path}: {str(e)}"
    #          logger.error(error_message)
    #          # Decide if a general unexpected error should fail the file processing entirely
    #          # For now, log and let the state manager handle potential partial state.
    #          # Consider adding more granular state updates for other stages here.
    #          pass


    #     # Continue with other pipeline stages if implemented (embedding, loading, etc.)
    #     # Example placeholder:
    #     # try:
    #     #     self.embed_document(document)
    #     #     self.state_manager.update_file_state(file_id=file_id, stage="embed", success=True)
    #     # except Exception as e:
    #     #     self.state_manager.update_file_state(file_id=file_id, stage="embed", success=False, error=str(e))

    #     # The document object, potentially with chunks (or without if chunking failed), is returned.
    #     # The success/failure of the file in the overall run summary depends on the return value of this method.
    #     # As currently implemented, it returns 'document' (making the file successful in the summary)
    #     # unless the read stage failed (which would return None).
    #     return document
    
    def process_file(self, file_path: Path) -> Optional[Document]:
        """
        Process a single file through all implemented pipeline stages with
        special handling for large files.
        """
        file_id = self.generate_file_id(file_path)
        document = None

        try:
            # Reading stage
            document = self.read_document(file_path)
        except PipelineError:
            return None # Stop processing if reading fails

        # Chunking stage
        # Note: This stage proceeds even if reading succeeded but returned empty content.
        # The chunker handles documents with no content or no chunks gracefully.
        try:
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="chunk",
                success=False,
            )

            chunker = TextChunker(
                chunk_size=1000,
                chunk_overlap=200,
                chunking_method="recursive"
            )
            document = chunker.chunk_document(document) # document.chunks should now be populated

            # Optional: Keep your chunk inspection prints here if needed for debugging
            # print(f"\n--- Chunks for file: {file_path.name} ---")
            # ... print logic ...
            # print("---------------------------------------------\n")


            self.state_manager.update_file_state(
                file_id=file_id,
                stage="chunk",
                success=True,
                metadata={
                    "chunks_count": len(document.chunks) if hasattr(document, "chunks") and isinstance(document.chunks, list) else 0,
                    "chunking_method": "recursive", # Add chunking method to state metadata
                }
            )

        except PipelineError as pe:
            # Catch PipelineError from chunking (e.g., schema errors on 'chunks')
            error_message = f"Chunking failed for {file_path}: {pe}"
            logger.error(error_message)
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="chunk",
                success=False,
                error=error_message
            )
            # Decide if chunking failure should stop the file processing
            # Currently, it logs and continues to the embedding stage.
            # If embedding REQUIRES chunks, the embedder will handle the 'no chunks' case.


        # Embedding stage  <--- NEW EMBEDDING STAGE
        # This stage proceeds even if chunking failed, the embedder will handle no chunks.
        try:
            # Mark stage as started
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="embed",
                success=False,
            )

            # Initialize embedding processor with app settings
            # Ensure settings object is accessible or passed correctly
            embedder = EmbeddingProcessor()

            # Generate embeddings
            logger.info(f"Generating embeddings for {file_path}")
            # The embedder expects document.chunks to exist and be a list (even if empty)
            document = embedder.embed_chunks(document) # document.chunk_embeddings should now be populated

            # Optional: Keep your embedding inspection prints here if needed
            if document and hasattr(document, 'chunk_embeddings') and document.chunk_embeddings is not None:
                print(f"\n--- Embedded Document Structure: {file_path.name} ---")
                print("Metadata:", document.metadata) # Metadata should now include embeddings_info
                print(f"Number of chunks: {len(document.chunks) if hasattr(document, 'chunks') and isinstance(document.chunks, list) else 0}")
                print(f"Number of embeddings: {len(document.chunk_embeddings)}")
                if document.chunks and document.chunk_embeddings:
                    print("\nFirst chunk preview:")
                    print(f"Content: {document.chunks[0][:200]}...")
                    print(f"Embedding (first 5 dim): {document.chunk_embeddings[0][:5]}...")
                print("---------------------------------------------\n")
            else:
                print(f"\n--- No embeddings generated for {file_path.name} ---")


            # Update metadata in state manager
            embedding_info = {
                "model": embedder.model_name,
                "type": embedder.embedding_type,
                "count": len(document.chunk_embeddings) if hasattr(document, "chunk_embeddings") and isinstance(document.chunk_embeddings, list) else 0,
                "dimensions": (
                    len(document.chunk_embeddings[0])
                    if hasattr(document, "chunk_embeddings") and document.chunk_embeddings and len(document.chunk_embeddings) > 0
                    else 0
                )
            }


            # Mark stage as successful
            self.state_manager.update_file_state(
                file_id=file_id,
                stage="embed",
                success=True,
                metadata=embedding_info # Store embedding info in state metadata
            )

        except PipelineError as pe:
             # Catch PipelineError from embedding (e.g., schema errors on 'chunk_embeddings')
             error_message = f"Embedding failed for {file_path}: {pe}"
             logger.error(error_message)
             self.state_manager.update_file_state(
                 file_id=file_id,
                 stage="embed",
                 success=False,
                 error=error_message
             )
             # Decide if embedding failure should stop the file processing
             # Currently, it logs and continues.

        except Exception as e:
            # Catch any other unexpected errors during embedding
            error_message = f"An unexpected error occurred during embedding for {file_path}: {str(e)}"
            logger.error(error_message)
            self.state_manager.update_file_state(
                 file_id=file_id,
                 stage="embed",
                 success=False,
                 error=error_message
             )


        # Continue with other stages if needed (e.g., loading into vector database)
        # Example placeholder:
        # try:
        #     self.load_document(document) # Assuming load_document handles document with/without chunks/embeddings
        #     self.state_manager.update_file_state(file_id=file_id, stage="load", success=True)
        # except Exception as e:
        #     self.state_manager.update_file_state(file_id=file_id, stage="load", success=False, error=str(e))

        # The document object, potentially with chunks and embeddings, is returned.
        # The overall file success in the run summary still depends on the read stage.
        return document

    def run(self, file_paths: Optional[List[Path]] = None, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the pipeline on a set of files.

        Args:
            file_paths: Optional list of specific files to process. If None, all files in input_dir are processed.
            extensions: Optional list of file extensions to filter by.

        Returns:
            Summary dictionary of the pipeline run.
        """
        # Start timing
        start_time = time.time()

        # Start a new pipeline run
        self.run_id = self.state_manager.mark_pipeline_started()
        logger.info(f"Starting pipeline run {self.run_id}")

        # Get files to process if not provided
        if file_paths is None:
            file_paths = self.get_files_to_process(extensions)

        # Track success and failure based on the return value of process_file
        successful_files = []
        failed_files = []

        # Process each file
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            # process_file returns Document on success (even if stages after read failed)
            # and None if the read stage failed.
            document = self.process_file(file_path)

            if document is not None:
                successful_files.append(file_path)
            else:
                # The failure reason is already logged by process_file (specifically read_document)
                failed_files.append(file_path)

        # Calculate duration
        duration = time.time() - start_time

        # Mark pipeline as completed
        # Note: The overall pipeline success here means 'all files attempted processing'.
        # Individual stage successes/failures are tracked per file in the state manager.
        # The run summary uses the count of files where process_file returned None vs Document.
        success = len(failed_files) == 0 and len(successful_files) > 0 # Consider run successful if some files succeeded and none failed at read stage
        if len(file_paths) == 0: # Handle case with no files found
            success = True
        self.state_manager.mark_pipeline_completed(self.run_id, success)

        # Get summary from state manager. Remove the 'run_id' argument as it's not supported.
        summary = self.state_manager.get_pipeline_summary()
        summary.update({
            "run_id": self.run_id,
            "duration_seconds": duration,
            "successful_files_count": len(successful_files),
            "failed_files_count": len(failed_files),
             # Add total files attempted for clarity
            "total_files_attempted": len(file_paths)
        })

        logger.info(f"Pipeline run completed in {duration:.2f} seconds. "
                    f"Processed {len(file_paths)} files: "
                    f"{len(successful_files)} successful (read stage), {len(failed_files)} failed (read stage). "
                    f"Check state logs for individual stage failures (e.g., chunking).")

        return summary

    def get_progress(self) -> Dict[str, Any]:
        """
        Get the current progress of the pipeline.

        Returns:
            Dictionary with progress information.
        """
        # Get summary from state manager. Remove the 'run_id' argument as it's not supported.
        return self.state_manager.get_pipeline_summary()


    def get_failed_files(self) -> List[Dict[str, Any]]:
        """
        Get information about files that failed processing in the last run.
        Note: This currently returns files that failed *any* stage according to state,
        not just those where process_file returned None.

        Returns:
            List of dictionaries with info about failed files.
        """
        # State manager tracks stage failures. This method gets files with any failed stage.
        # If you strictly want files where process_file returned None, you'd need to track that separately.
        # Assuming get_failed_files might implicitly use the last run ID if state manager supports runs,
        # but explicitly removing the argument based on the error.
        # If your StateManager's get_failed_files also takes run_id, you might need to add it back
        # here if you want failed files *for a specific run*. Based on the error, it seems not.
        return self.state_manager.get_failed_files()


def run_pipeline(input_dir: Optional[str] = None,
                output_dir: Optional[str] = None,
                extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function to run the document pipeline.

    Args:
        input_dir: Directory containing files to process. Defaults to RAW_DATA_DIR.
        output_dir: Directory to store processed outputs. Defaults to PROCESSED_DATA_DIR.
        extensions: List of file extensions to process.

    Returns:
        Summary of the pipeline run.
    """
    pipeline = DocumentPipeline(input_dir, output_dir)
    return pipeline.run(extensions=extensions)


if __name__ == "__main__":
    # This allows running the pipeline directly as a script
    import argparse

    parser = argparse.ArgumentParser(description="Run the document processing pipeline")
    parser.add_argument("--input", "-i", help=f"Input directory with files to process (default: {RAW_DATA_DIR})")
    parser.add_argument("--output", "-o", help=f"Output directory for processed files (default: {PROCESSED_DATA_DIR})")
    parser.add_argument("--extensions", "-e", nargs="+", help="File extensions to process")

    args = parser.parse_args()

    summary = run_pipeline(
        input_dir=args.input,
        output_dir=args.output,
        extensions=args.extensions
    )

    print("Pipeline completed:")
    print(f"Total files attempted: {summary.get('total_files_attempted', 'N/A')}")
    print(f"Successful (read stage): {summary.get('successful_files_count', 'N/A')}")
    print(f"Failed (read stage): {summary.get('failed_files_count', 'N/A')}")
    print(f"Overall progress (based on state): {summary.get('overall_progress', 'N/A'):.2f}%")
    print(f"Duration: {summary.get('duration_seconds', 'N/A'):.2f} seconds")

    # Provide more detail from state for failed stages if overall progress is less than 100%
    # The summary from get_pipeline_summary doesn't inherently know about specific runs
    # unless the StateManager is designed to track runs in its summary output.
    # If you need per-run stage failure details in the final printout, you'd need
    # to enhance the StateManager or the pipeline's tracking.
    if summary.get('overall_progress', 0) < 100:
         print("\nNote: Some files may have failed stages (e.g., chunking). Check the pipeline state file for details.")