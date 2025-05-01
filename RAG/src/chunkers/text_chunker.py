"""
Text chunking module for document pipeline.
This module provides chunking capabilities using LangChain.
"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)

# Assuming Document is imported from .readers.schema
from ..readers.schema import Document
from ..utils.logger import logger
from ..utils.error_handler import PipelineError


class TextChunker:
    """
    Handles chunking of document text using various LangChain text splitters.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_method: str = "recursive",
        separators: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Target size of each text chunk
            chunk_overlap: Number of characters/tokens to overlap between chunks
            chunking_method: Method to use for chunking ("recursive", "character", "token")
            separators: List of separators to consider for splitting (for recursive and character methods)
            **kwargs: Additional arguments to pass to the text splitter
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_method = chunking_method.lower()

        # Default separators if none provided
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

        # Initialize the appropriate text splitter based on method
        if self.chunking_method == "recursive":
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
                **kwargs
            )
        elif self.chunking_method == "character":
            self.text_splitter = CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator=self.separators[0] if self.separators else "\n",
                **kwargs
            )
        elif self.chunking_method == "token":
            self.text_splitter = TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported chunking method: {self.chunking_method}. "
                           f"Choose from 'recursive', 'character', or 'token'.")

        logger.info(f"Initialized TextChunker with method: {self.chunking_method}, "
                   f"chunk_size: {self.chunk_size}, chunk_overlap: {self.chunk_overlap}")

    def _build_text_from_docx(self, document: Document) -> str:
        parts = []

        if hasattr(document, 'paragraphs') and document.paragraphs:
            parts.extend(document.paragraphs)
        elif document.content:
            parts.append(document.content)

        if hasattr(document, 'tables') and document.tables:
            for table_index, table in enumerate(document.tables):
                parts.append(f"\n\n--- Table {table_index + 1} ---")
                for row in table:
                    row_str = " | ".join("".join(cell).strip() for cell in row)
                    parts.append(row_str)
                parts.append("--- End Table ---\n\n")

        combined = "\n\n".join(parts).strip()
        return combined if combined else document.content

    def _build_text_from_pdf(self, document: Document) -> str:
        if hasattr(document, 'page_texts') and document.page_texts:
            return "\n\n".join(
                f"--- Page {i+1} ---\n{page}" for i, page in enumerate(document.page_texts)
            )
        return document.content

    def _build_text_from_generic(self, document: Document) -> str:
        return document.content

    def _build_text_for_chunking(self, document: Document) -> str:
        doc_type = type(document).__name__
        if doc_type == "DocxDocument":
            return self._build_text_from_docx(document)
        elif doc_type == "PDFDocument":
            return self._build_text_from_pdf(document)
        else:
            return self._build_text_from_generic(document)

    def chunk_document(self, document: Document) -> Document:
        try:
            print(f"DEBUG: Document type: {type(document).__name__}")
            print(f"DEBUG: Document has content attribute: {hasattr(document, 'content')}")
            print(f"DEBUG: Document content type: {type(document.content) if hasattr(document, 'content') else 'N/A'}")
            
            if not hasattr(document, 'content') or not document.content:
                logger.warning(f"Document has no content to chunk: {document.metadata.file_name}")
                document.chunks = []
                return document

            text_to_chunk = self._build_text_for_chunking(document)

            if not text_to_chunk.strip():
                logger.warning(f"Empty chunk input for: {document.metadata.file_name}")
                try:
                    document.chunks = []
                except AttributeError:
                    pass
                return document

            logger.info(f"Chunking {len(text_to_chunk)} characters from {type(document).__name__}")
            chunks = self.text_splitter.split_text(text_to_chunk)

            try:
                document.chunks = chunks
            except AttributeError as ae:
                error_message = (
                    f"'chunks' not settable on {type(document).__name__}. "
                    f"Ensure schema defines: chunks: List[str] = Field(default_factory=list)"
                )
                raise PipelineError(error_message, ae)

            if document.metadata:
                try:
                    if isinstance(document.metadata, dict):
                        document.metadata["chunks_info"] = {
                            "count": len(chunks),
                            "chunk_size": self.chunk_size,
                            "chunk_overlap": self.chunk_overlap,
                            "chunking_method": self.chunking_method,
                        }
                    else:
                        document.metadata.chunks_info = {
                            "count": len(chunks),
                            "chunk_size": self.chunk_size,
                            "chunk_overlap": self.chunk_overlap,
                            "chunking_method": self.chunking_method,
                        }
                except Exception as e:
                    logger.warning(f"Could not attach chunk metadata: {e}")

            logger.info(f"Document chunked into {len(chunks)} chunks")
            return document

        except PipelineError:
            raise
        except Exception as e:
            raise PipelineError(f"Unexpected error during chunking: {e}", e)