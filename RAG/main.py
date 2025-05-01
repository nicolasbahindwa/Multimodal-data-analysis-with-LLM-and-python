# # # main.py
# # import os
# # import sys
# # from pathlib import Path

# # # Add the project directory to Python path
# # project_root = os.path.dirname(os.path.abspath(__file__))
# # # Add it to Python's path
# # sys.path.append(project_root)

# # def main():
# #     try:
# #         # Import functionality
# #         from src.readers.factory import get_supported_formats
# #         from src.connectors.local_file import LocalFileConnector
        
# #         # Display supported formats
# #         print(f"Supported formats: {get_supported_formats()}")
        
# #         # Create data directories if they don't exist
# #         project_path = Path(project_root)
# #         data_dir = project_path / "data" / "raw" / "local"
# #         data_dir.mkdir(parents=True, exist_ok=True)
        
# #         # Create a connector to the local file system
# #         print("\nTesting LocalFileConnector...")
# #         connector = LocalFileConnector(base_path=str(data_dir))
        
# #         # Ensure connection
# #         connector.connect()
        
# #         # List all documents in the data directory
# #         print("\nListing available documents:")
# #         documents = connector.list_files()
        
# #         if not documents:
# #             print("No documents found in the directory.")
# #         else:
# #             for i, doc in enumerate(documents):
# #                 print(f"{i+1}. {doc['name']} (extension: {doc['extension']})")
            
# #             # If we have documents, try to read the first one
# #             print("\nReading the first document:")
# #             first_doc = documents[0]
# #             try:
# #                 content_bytes = connector.get_file(first_doc["path"])
                
# #                 print(f"Document: {first_doc['name']}")
# #                 print(f"Extension: {first_doc['extension']}")
                
# #                 # Convert bytes to string and print a preview
# #                 content = content_bytes.decode('utf-8')
# #                 preview = content[:500] + "..." if len(content) > 500 else content
# #                 print(f"Content preview: {preview}")
                
# #                 # Print file metadata from the documents list
# #                 print("\nMetadata:")
# #                 for key, value in first_doc.items():
# #                     if key != 'path':  # Skip path as it might be long
# #                         print(f"  {key}: {value}")
# #             except Exception as e:
# #                 print(f"Error reading document: {str(e)}")
        
# #     except Exception as e:
# #         print(f"Error: {str(e)}")
# #         import traceback
# #         traceback.print_exc()

# # if __name__ == "__main__":
# #     main()


# from src.readers.factory import read_document

# # Read a text file

# # Read a doc file with custom parameters
# content = read_document("data/raw/local/meeting.txt", encoding="utf-8")
# print(content.content)
# print(content.metadata)


# content = read_document("data/raw/local/invoice.docx")
# print(content)
# print(content.metadata)

# # if __name__ == "__main__":
# #     main()


from src.pipeline import run_pipeline

# Run on all supported files in the default directories
summary = run_pipeline()

# Or specify directories and extensions
summary = run_pipeline(
    input_dir="data/raw/local", 
    output_dir="data/processed",
    extensions=[".txt", ".docx", ".pdf"]
)

print(f"Processed {summary['total_files']} files with {summary['overall_progress']:.2f}% success rate")