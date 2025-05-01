# src/readers/txt_reader.py
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from ..utils.error_handler import ReadError, error_handler
from .base_reader import BaseReader


class TxtReader(BaseReader):
    """Reader for plain text files (.txt)."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions."""
        return [".txt", ".text"]
    
    @error_handler(
        error_type=ReadError,
        message="Failed to read text file {args[0]}",
        log_traceback=True,
        raise_error=True
    )
    def _read_file(self, file_path: Path, **kwargs) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Read the content of a text file.
        
        Args:
            file_path: Path to the text file.
            **kwargs: Additional parameters, including:
                - encoding: File encoding (default is instance encoding).
            
        Returns:
            A tuple containing:
                - The text content as a string
                - A dictionary with metadata like character and word counts
        """
        encoding = kwargs.get("encoding", self.encoding)
        
        try:
            with open(file_path, "r", encoding=encoding) as file:
                content = file.read()
        except UnicodeDecodeError:
            # Try to detect encoding if specified encoding fails
            self.logger.warning(f"Failed to decode {file_path} with {encoding} encoding, trying to detect encoding...")
            import chardet
            
            with open(file_path, "rb") as file:
                raw_data = file.read()
                detected = chardet.detect(raw_data)
                detected_encoding = detected["encoding"]
                
            self.logger.info(f"Detected encoding: {detected_encoding} with confidence {detected['confidence']}")
            
            with open(file_path, "r", encoding=detected_encoding) as file:
                content = file.read()
        
        # Calculate additional metadata
        word_count = len(content.split())
        character_count = len(content)
        
        additional_metadata = {
            "word_count": word_count,
            "character_count": character_count,
            "content_type": "text/plain"
        }
        
        return content, additional_metadata