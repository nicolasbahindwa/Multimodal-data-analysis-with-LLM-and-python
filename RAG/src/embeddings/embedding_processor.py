"""
Document embedding module for document pipeline.
This module provides embedding capabilities using LangChain with application settings.
"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from langchain.embeddings import (
    HuggingFaceEmbeddings,
    OpenAIEmbeddings, 
    CacheBackedEmbeddings
)
from langchain.storage import LocalFileStore

# Import from your existing modules
from ..readers.schema import Document
from ..utils.logger import logger
from ..utils.error_handler import PipelineError
from ..config.settings import settings  # Ensure this import path matches your project structure


class EmbeddingProcessor:
    """
    Handles embedding of document chunks using various LangChain embedding models.
    Configuration is managed through the application's Settings class.
    """

    def __init__(self, **kwargs):
        """
        Initialize the embedding processor using application settings.
        
        Args:
            **kwargs: Additional arguments to pass to the embedding model initializers
        """
        try:
            # Retrieve embedding configuration from settings
            embedding_config = settings.get_embedding_config()
            self.model_name = embedding_config["model_name"]
            self.embedding_type = embedding_config["embedding_type"].lower()
            cache_dir = embedding_config["cache_dir"]
            use_gpu = embedding_config["use_gpu"]

            # Initialize the appropriate embedding model
            if self.embedding_type == "huggingface":
                # Configure device with GPU support from settings
                model_kwargs = {"device": "cuda" if use_gpu else "cpu"}
                # Merge with any user-provided model_kwargs
                model_kwargs.update(kwargs.pop("model_kwargs", {}))
                
                base_embeddings = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs=model_kwargs,
                    **kwargs
                )
            elif self.embedding_type == "openai":
                # Validate OpenAI API key
                openai_api_key = settings.get_api_key("openai")
                if not openai_api_key:
                    raise PipelineError(
                        "OpenAI API key required but not found. Set OPENAI_API_KEY in environment/config."
                    )
                
                base_embeddings = OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=openai_api_key,
                    **kwargs
                )
            else:
                raise ValueError(f"Unsupported embedding type: {self.embedding_type}")

            # Configure caching if enabled in settings
            if cache_dir:
                cache_dir = Path(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                store = LocalFileStore(str(cache_dir))
                self.embeddings = CacheBackedEmbeddings.from_bytes_store(
                    base_embeddings, store, namespace=self.model_name
                )
            else:
                self.embeddings = base_embeddings

            logger.info(
                f"Initialized EmbeddingProcessor with: "
                f"Model: {self.model_name}, "
                f"Type: {self.embedding_type}, "
                f"Cache: {cache_dir if cache_dir else 'Disabled'}, "
                f"GPU: {'Enabled' if use_gpu else 'Disabled'}"
            )

        except Exception as e:
            logger.error("Failed to initialize EmbeddingProcessor", exc_info=True)
            raise PipelineError(f"EmbeddingProcessor initialization failed: {e}", e)

    def embed_chunks(self, document: Document) -> Document:
        """
        Generate embeddings for document chunks.
        
        Args:
            document: Document object with chunks
            
        Returns:
            Document with embeddings added
            
        Raises:
            PipelineError: If embedding fails
        """
        try:
            if not hasattr(document, 'chunks') or not document.chunks:
                logger.warning(f"Document has no chunks to embed: {document.metadata.file_name}")
                document.chunk_embeddings = []
                return document

            logger.info(f"Embedding {len(document.chunks)} chunks from {document.metadata.file_name}")
            
            # Generate embeddings for all chunks
            embeddings = self.embeddings.embed_documents(document.chunks)
            
            # Attach embeddings to document
            try:
                document.chunk_embeddings = embeddings
            except AttributeError as ae:
                error_message = (
                    f"'chunk_embeddings' not settable on {type(document).__name__}. "
                    f"Ensure schema defines: chunk_embeddings: Optional[List[List[float]]] = Field(default=None)"
                )
                raise PipelineError(error_message, ae)
                
            # Update metadata with embedding information
            if document.metadata:
                embeddings_info = {
                    "model": self.model_name,
                    "type": self.embedding_type,
                    "count": len(embeddings),
                    "dimensions": len(embeddings[0]) if embeddings else 0,
                }
                
                try:
                    if isinstance(document.metadata, dict):
                        document.metadata["embeddings_info"] = embeddings_info
                    else:
                        document.metadata.embeddings_info = embeddings_info
                except Exception as e:
                    logger.warning(f"Could not attach embedding metadata: {e}")
                    
            logger.info(
                f"Generated {len(embeddings)} embeddings "
                f"({len(embeddings[0]) if embeddings else 0}-dimensional)"
            )
            return document
            
        except PipelineError:
            raise
        except Exception as e:
            logger.error(f"Embedding failed for document: {document.metadata.file_name}", exc_info=True)
            raise PipelineError(f"Unexpected error during embedding: {e}", e)