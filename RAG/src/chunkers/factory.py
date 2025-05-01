# src/chunkers/factory.py
from typing import Dict, List, Optional, Type

# from ..utils.error_handler import ChunkingError
from ..utils.logger import logger
from ..readers.schema import Document, DocumentChunk
from .base_chunker import BaseChunker
from .text_chunker import TextChunker
# Import other chunkers when they are created


class ChunkerFactory:
    """
    Factory class for creating appropriate document chunkers.
    Manages the registry of available chunkers and delegates document chunking.
    """
    
    def __init__(self):
        """Initialize the chunker factory with available chunkers."""
        self._chunkers: List[BaseChunker] = []
        
        # Register built-in chunkers
        self.register_chunker(TextChunker())
        # Register other chunkers as they become available
    
    def register_chunker(self, chunker: BaseChunker) -> None:
        """
        Register a chunker.
        
        Args:
            chunker: The chunker instance to register.
        """
        self._chunkers.append(chunker)
        logger.info(f"Registered {chunker.__class__.__name__}")
    
    def get_chunker_for_document(self, document: Document) -> Optional[BaseChunker]:
        """
        Get the appropriate chunker for a given document.
        
        Args:
            document: Document to chunk.
            
        Returns:
            A chunker instance if a suitable one is found, None otherwise.
        """
        for chunker in self._chunkers:
            if chunker.can_handle(document):
                return chunker
        
        return None
    
    def chunk_document(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """
        Chunk a document using the appropriate chunker.
        
        Args:
            document: Document to chunk.
            **kwargs: Additional chunker-specific parameters.
            
        Returns:
            List of document chunks.
            
        Raises:
            ChunkingError: If no suitable chunker is found or chunking fails.
        """
        from ..utils.error_handler import ChunkingError
        # Get the appropriate chunker
        chunker = self.get_chunker_for_document(document)
        
        if chunker is None:
            raise ChunkingError(
                f"No chunker found for document type: {document.__class__.__name__}"
            )
        
        # Chunk the document
        logger.info(f"Using {chunker.__class__.__name__} to chunk {document.metadata.file_name}")
        return chunker.chunk(document, **kwargs)


# Create a singleton instance of the factory
chunker_factory = ChunkerFactory()


def chunk_document(document: Document, **kwargs) -> List[DocumentChunk]:
    """
    Convenience function to chunk a document using the factory.
    
    Args:
        document: Document to chunk.
        **kwargs: Additional chunker-specific parameters.
        
    Returns:
        List of document chunks.
    """
    return chunker_factory.chunk_document(document, **kwargs)