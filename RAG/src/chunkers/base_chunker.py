# src/chunkers/base_chunker.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..readers.schema import Document, DocumentChunk
from ..utils.logger import logger
from ..utils.error_handler import ChunkingError, error_handler
from ..config.settings import settings


class BaseChunker(ABC):
    """
    Abstract base class for all document chunkers.
    Defines the common interface that all specific chunker implementations must follow.
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize the base chunker.
        
        Args:
            chunk_size: Size of each chunk in characters or tokens.
            chunk_overlap: Number of characters or tokens to overlap between chunks.
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        self.logger = logger
    
    @abstractmethod
    def can_handle(self, document: Document) -> bool:
        """
        Check if this chunker can handle the given document type.
        
        Args:
            document: Document to check.
            
        Returns:
            True if the chunker can handle this document, False otherwise.
        """
        pass
    
    @error_handler(
        error_type=ChunkingError,
        message="Failed to chunk document",
        log_traceback=True,
        raise_error=True
    )
    def chunk(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """
        Split the document into chunks.
        
        Args:
            document: Document to split into chunks.
            **kwargs: Additional chunker-specific parameters.
            
        Returns:
            List of DocumentChunk objects.
            
        Raises:
            ChunkingError: If chunking fails.
        """
        self.logger.info(f"Chunking document: {document.metadata.file_name}")
        
        # Call the implementation-specific chunking method
        chunks = self._chunk_document(document, **kwargs)
        
        # Set document_id and chunk_index for each chunk
        document_id = document.metadata.source_id
        for i, chunk in enumerate(chunks):
            chunk.document_id = document_id
            chunk.chunk_index = i
        
        self.logger.info(f"Created {len(chunks)} chunks from document: {document.metadata.file_name}")
        return chunks
    
    @abstractmethod
    def _chunk_document(self, document: Document, **kwargs) -> List[DocumentChunk]:
        """
        Implementation-specific method to chunk the document.
        Must be implemented by subclasses.
        
        Args:
            document: Document to split into chunks.
            **kwargs: Additional chunker-specific parameters.
            
        Returns:
            List of DocumentChunk objects.
        """
        pass