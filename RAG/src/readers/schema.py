# # src/readers/schema.py
# from datetime import datetime
# from pathlib import Path
# from typing import Any, Dict, List, Optional, Union
# from uuid import uuid4

# from pydantic import BaseModel, Field, model_validator, field_validator


# class FileMetadata(BaseModel):
#     """Metadata about a file processed by a reader."""
#     file_path: str
#     file_name: str
#     file_extension: str
#     file_size_bytes: int
#     last_modified: Optional[datetime] = None
#     reader_type: str
#     content_type: Optional[str] = None
#     num_pages: Optional[int] = None
#     word_count: Optional[int] = None
#     character_count: Optional[int] = None
#     author: Optional[str] = None
#     creation_date: Optional[datetime] = None
#     source_id: Optional[str] = None  # Unique identifier for tracking source
#     # You could optionally add chunking metadata here too if needed, e.g.:
#     # chunking_method: Optional[str] = None
#     # chunk_size: Optional[int] = None
#     # chunk_overlap: Optional[int] = None

#     @field_validator('last_modified', mode='before')
#     @classmethod
#     def set_last_modified(cls, v, info):
#         """Set last_modified from file_path if not provided."""
#         if v is None and 'file_path' in info.data:
#             try:
#                 path = Path(info.data['file_path'])
#                 if path.exists():
#                     return datetime.fromtimestamp(path.stat().st_mtime)
#             except Exception:
#                 pass # Ignore errors if file path is invalid or stat fails
#         return v


# class Document(BaseModel):
#     """
#     Base model for document content with metadata.
#     This keeps content and its metadata together for better traceability in RAG.
#     """
#     content: str = Field(..., description="The extracted text content")
#     metadata: FileMetadata
#     # >>> ADD THIS FIELD <<<
#     chunks: List[str] = Field(default_factory=list, description="List of text chunks derived from the content")
#     # >>> ADD THIS FIELD <<<

#     @field_validator('content')
#     @classmethod
#     def validate_content_not_empty(cls, v):
#         """Validate that content is not empty."""
#         if not v or not v.strip():
#             # Note: Depending on pipeline design, you might want to allow empty content
#             # for certain file types or handle this case differently.
#             # The chunker already handles documents with no content by returning early.
#             pass # Removing the ValueError to align with chunker's empty content handling
#         return v

#     def get_source_info(self) -> str:
#         """Get a formatted string with source information for citations."""
#         return f"Source: {self.metadata.file_name} (from {self.metadata.file_path})"


# # Subclasses inherit fields from Document, including 'chunks'
# class TextDocument(Document):
#     """Model for plain text document."""
#     pass


# class PDFDocument(Document):
#     """Model for PDF document."""
#     page_texts: Optional[List[str]] = Field(None, description="Text content separated by pages")


# class DocxDocument(Document):
#     """Model for DOCX document."""
#     paragraphs: Optional[List[str]] = Field(None, description="List of paragraphs")
#     tables: Optional[List[List[List[str]]]] = Field(None, description="List of tables (table -> row -> cell)")


# class ExcelDocument(Document):
#     """Model for Excel document."""
#     # Note: Content in ExcelDocument will be a string representation, potentially from sheets/data
#     sheets: Dict[str, List[List[Any]]] = Field(..., description="Dictionary of sheets with their data")
#     sheet_names: List[str] = Field(..., description="List of sheet names")


# class CSVDocument(Document):
#     """Model for CSV document."""
#     # Note: Content in CSVDocument will be a string representation, potentially from data
#     data: List[Dict[str, Any]] = Field(..., description="List of dictionaries representing CSV rows")
#     headers: List[str] = Field(..., description="CSV column headers")
#     num_rows: int = Field(..., description="Number of rows in the CSV")


# class HTMLDocument(Document):
#     """Model for HTML document."""
#     title: Optional[str] = Field(None, description="HTML title")
#     headings: Optional[List[Dict[str, str]]] = Field(None, description="List of headings with level and text")
#     links: Optional[List[Dict[str, str]]] = Field(None, description="List of links with href and text")


# class XMLDocument(Document):
#     """Model for XML document."""
#     structure: Dict[str, Any] = Field(..., description="Parsed XML structure")


# class PPTXDocument(Document):
#     """Model for PPTX document."""
#     slides: List[Dict[str, Any]] = Field(..., description="List of slides with their content")
#     num_slides: int = Field(..., description="Number of slides in the presentation")


# # The DocumentChunk model is fine as is, it represents individual chunks
# class DocumentChunk(BaseModel):
#     """
#     A chunk of a document used for embedding and retrieval.
#     Contains the chunk text, position in original document, and original metadata.
#     """
#     text: str = Field(..., description="The chunk text content")
#     chunk_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the chunk")
#     document_id: str = Field(..., description="ID of the source document")
#     chunk_index: int = Field(..., description="Position of chunk in document")
#     metadata: FileMetadata = Field(..., description="Original document metadata")
#     # You might add a reference to page/paragraph number here if applicable,
#     # possibly within metadata or as a separate field.

#     def get_retrieval_context(self) -> str:
#         """Format chunk for inclusion in retrieval context."""
#         source_info = f"{self.metadata.file_name}"
#         # The check for 'page_number' might fail if it's not added to metadata
#         # or DocumentChunk. Consider adding it explicitly if needed.
#         # if self.metadata.num_pages and hasattr(self, 'page_number'):
#         #     source_info += f" (page {self.page_number})"
#         return f"[{source_info}]\n{self.text}"


# src/readers/schema.py
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator, field_validator


class FileMetadata(BaseModel):
    """Metadata about a file processed by a reader."""
    file_path: str
    file_name: str
    file_extension: str
    file_size_bytes: int
    last_modified: Optional[datetime] = None
    reader_type: str
    content_type: Optional[str] = None
    num_pages: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    source_id: Optional[str] = None  # Unique identifier for tracking source
    chunks_info: Optional[Dict[str, Any]] = Field(None, description="Information about chunking applied") # Added/Updated chunking metadata
    embeddings_info: Optional[Dict[str, Any]] = Field(None, description="Information about embeddings generated") # Added embedding metadata


    @field_validator('last_modified', mode='before')
    @classmethod
    def set_last_modified(cls, v, info):
        """Set last_modified from file_path if not provided."""
        if v is None and 'file_path' in info.data:
            try:
                path = Path(info.data['file_path'])
                if path.exists():
                    return datetime.fromtimestamp(path.stat().st_mtime)
            except Exception:
                pass # Ignore errors if file path is invalid or stat fails
        return v


class Document(BaseModel):
    """
    Base model for document content with metadata.
    This keeps content and its metadata together for better traceability in RAG.
    """
    content: str = Field(..., description="The extracted text content")
    metadata: FileMetadata
    chunks: List[str] = Field(default_factory=list, description="List of text chunks derived from the content")
    # >>> ADD THIS FIELD FOR EMBEDDINGS <<<
    chunk_embeddings: Optional[List[List[float]]] = Field(default=None, description="List of embeddings for each chunk")
    # >>> ADD THIS FIELD FOR EMBEDDINGS <<<


    @field_validator('content')
    @classmethod
    def validate_content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v or not v.strip():
            pass # Allow empty content/handle downstream

        return v

    def get_source_info(self) -> str:
        """Get a formatted string with source information for citations."""
        return f"Source: {self.metadata.file_name} (from {self.metadata.file_path})"


# Subclasses inherit fields from Document, including 'chunks' and 'chunk_embeddings'
class TextDocument(Document):
    """Model for plain text document."""
    pass

# ... other document types (PDFDocument, DocxDocument, etc.) remain the same ...
class PDFDocument(Document):
    """Model for PDF document."""
    page_texts: Optional[List[str]] = Field(None, description="Text content separated by pages")


class DocxDocument(Document):
    """Model for DOCX document."""
    paragraphs: Optional[List[str]] = Field(None, description="List of paragraphs")
    tables: Optional[List[List[List[str]]]] = Field(None, description="List of tables (table -> row -> cell)")


class ExcelDocument(Document):
    """Model for Excel document."""
    # Note: Content in ExcelDocument will be a string representation, potentially from sheets/data
    sheets: Dict[str, List[List[Any]]] = Field(..., description="Dictionary of sheets with their data")
    sheet_names: List[str] = Field(..., description="List of sheet names")


class CSVDocument(Document):
    """Model for CSV document."""
    # Note: Content in CSVDocument will be a string representation, potentially from data
    data: List[Dict[str, Any]] = Field(..., description="List of dictionaries representing CSV rows")
    headers: List[str] = Field(..., description="CSV column headers")
    num_rows: int = Field(..., description="Number of rows in the CSV")


class HTMLDocument(Document):
    """Model for HTML document."""
    title: Optional[str] = Field(None, description="HTML title")
    headings: Optional[List[Dict[str, str]]] = Field(None, description="List of headings with level and text")
    links: Optional[List[Dict[str, str]]] = Field(None, description="List of links with href and text")


class XMLDocument(Document):
    """Model for XML document."""
    structure: Dict[str, Any] = Field(..., description="Parsed XML structure")


class PPTXDocument(Document):
    """Model for PPTX document."""
    slides: List[Dict[str, Any]] = Field(..., description="List of slides with their content")
    num_slides: int = Field(..., description="Number of slides in the presentation")


class DocumentChunk(BaseModel):
    """
    A chunk of a document used for embedding and retrieval.
    Contains the chunk text, position in original document, and original metadata.
    """
    text: str = Field(..., description="The chunk text content")
    chunk_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the chunk")
    document_id: str = Field(..., description="ID of the source document")
    chunk_index: int = Field(..., description="Position of chunk in document")
    metadata: FileMetadata = Field(..., description="Original document metadata")
    # Optional: Add the embedding for this specific chunk here if storing chunks separately
    # embedding: Optional[List[float]] = Field(None, description="Embedding vector for this chunk")

    def get_retrieval_context(self) -> str:
        """Format chunk for inclusion in retrieval context."""
        source_info = f"{self.metadata.file_name}"
        # The check for 'page_number' might fail if it's not added to metadata
        # or DocumentChunk. Consider adding it explicitly if needed.
        # if self.metadata.num_pages and hasattr(self, 'page_number'):
        #     source_info += f" (page {self.page_number})"
        return f"[{source_info}]\n{self.text}"