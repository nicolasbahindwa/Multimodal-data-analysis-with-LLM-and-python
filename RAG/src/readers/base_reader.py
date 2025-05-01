# src/readers/base_reader.py
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union, Tuple

from ..utils.error_handler import ReadError, error_handler
from ..utils.logger import logger
from ..config.settings import settings
from .schema import Document, FileMetadata, TextDocument, PDFDocument, DocxDocument, ExcelDocument, CSVDocument, HTMLDocument, XMLDocument, PPTXDocument


class BaseReader(ABC):
    """
    Abstract base class for all document readers.
    Defines the common interface that all specific reader implementations must follow.
    """

    def __init__(self, encoding: str = "utf-8"):
        """
        Initialize the base reader.
        
        Args:
            encoding: The character encoding to use for text files.
        """
        self.encoding = encoding
        self.logger = logger
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this reader can process.
        Must be implemented by subclasses.
        
        Returns:
            List of supported file extensions (e.g., [".txt", ".text"]).
        """
        pass
    
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        """
        Check if this reader can handle the given file based on its extension.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file extension is supported, False otherwise.
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        return file_path.suffix.lower() in self.supported_extensions
    
    def _generate_source_id(self, file_path: Path) -> str:
        """
        Generate a unique source ID for the document.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            A unique source ID as a hexadecimal string.
        """
        # Use file path and last modified time to create a unique identifier
        file_stat = file_path.stat()
        unique_str = f"{file_path.absolute()}_{file_stat.st_mtime}_{file_stat.st_size}"
        
        # Create a hash of the unique string
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    @error_handler(
        error_type=ReadError,
        message="Failed to read file {args[0]}",
        log_traceback=True,
        raise_error=True
    )
    def read(self, file_path: Union[str, Path], **kwargs) -> Document:
        """
        Read the file and extract its content.
        
        Args:
            file_path: Path to the file to read.
            **kwargs: Additional reader-specific parameters.
            
        Returns:
            A Document object containing the file content and metadata.
            
        Raises:
            ReadError: If the file cannot be read.
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        
        # Validate file existence
        if not file_path.exists():
            raise ReadError(f"File not found: {file_path}")
        
        # Validate file size
        max_size_mb = settings.MAX_FILE_SIZE_MB
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ReadError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
            )
        
        # Log the reading operation
        self.logger.info(f"Reading file: {file_path}")
        
        # Call the implementation-specific read method
        content, additional_metadata = self._read_file(file_path, **kwargs)
        
        # Generate a unique source ID
        source_id = self._generate_source_id(file_path)
        
        # Create metadata
        metadata = FileMetadata(
            file_path=str(file_path),
            file_name=file_path.name,
            file_extension=file_path.suffix.lower(),
            file_size_bytes=file_path.stat().st_size,
            reader_type=self.__class__.__name__,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
            source_id=source_id
        )
        
        # Update metadata with additional information
        if additional_metadata and isinstance(additional_metadata, dict):
            for key, value in additional_metadata.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
        
        # Create the document based on reader type and file extension
        document = self._create_document(content, metadata)
        
        self.logger.info(f"Successfully read file: {file_path}")
        return document
    
    def _create_document(self, content: Any, metadata: FileMetadata) -> Document:
        """
        Create a Document instance of the appropriate type based on file extension.
        
        Args:
            content: The file content.
            metadata: The file metadata.
            
        Returns:
            A Document object of the appropriate type.
        """
        ext = metadata.file_extension.lower()
        
        # Convert content to raw text if it's not already
        if isinstance(content, dict) and "text" in content:
            raw_text = content["text"]
        elif isinstance(content, str):
            raw_text = content
        else:
            raw_text = str(content)
            
        # Create the appropriate document type based on file extension
        if ext in [".txt", ".log", ".md", ".rtf"]:
            return TextDocument(content=raw_text, metadata=metadata)
        elif ext == ".pdf":
            page_texts = content.get("page_texts") if isinstance(content, dict) else None
            return PDFDocument(content=raw_text, page_texts=page_texts, metadata=metadata)
        elif ext in [".docx", ".doc"]:
            paragraphs = content.get("paragraphs") if isinstance(content, dict) else None
            tables = content.get("tables") if isinstance(content, dict) else None
            return DocxDocument(content=raw_text, paragraphs=paragraphs, tables=tables, metadata=metadata)
        elif ext in [".xlsx", ".xls"]:
            sheets = content.get("sheets") if isinstance(content, dict) else {}
            sheet_names = content.get("sheet_names") if isinstance(content, dict) else []
            return ExcelDocument(content=raw_text, sheets=sheets, sheet_names=sheet_names, metadata=metadata)
        elif ext == ".csv":
            data = content.get("data") if isinstance(content, dict) else []
            headers = content.get("headers") if isinstance(content, dict) else []
            num_rows = content.get("num_rows") if isinstance(content, dict) else 0
            return CSVDocument(content=raw_text, data=data, headers=headers, num_rows=num_rows, metadata=metadata)
        elif ext == ".html":
            title = content.get("title") if isinstance(content, dict) else None
            headings = content.get("headings") if isinstance(content, dict) else None
            links = content.get("links") if isinstance(content, dict) else None
            return HTMLDocument(content=raw_text, title=title, headings=headings, links=links, metadata=metadata)
        elif ext == ".xml":
            structure = content.get("structure") if isinstance(content, dict) else {}
            return XMLDocument(content=raw_text, structure=structure, metadata=metadata)
        elif ext == ".pptx":
            slides = content.get("slides") if isinstance(content, dict) else []
            num_slides = content.get("num_slides") if isinstance(content, dict) else 0
            return PPTXDocument(content=raw_text, slides=slides, num_slides=num_slides, metadata=metadata)
        else:
            # Default to TextDocument for unsupported extensions
            return TextDocument(content=raw_text, metadata=metadata)
    
    @abstractmethod
    def _read_file(self, file_path: Path, **kwargs) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """
        Implementation-specific method to read the file content.
        Must be implemented by subclasses.
        
        Args:
            file_path: Path to the file to read.
            **kwargs: Additional reader-specific parameters.
            
        Returns:
            A tuple containing:
                - The file content in a format specific to the reader implementation
                - A dictionary containing additional metadata (optional)
        """
        pass