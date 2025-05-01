# src/readers/factory.py
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from ..utils.error_handler import ReadError
from ..utils.logger import logger
from .base_reader import BaseReader
from .txt_reader import TxtReader
from .doc_reader import DocReader
# Import other readers when they are created
# from .pdf_reader import PDFReader
# from .docx_reader import DocxReader
# from .csv_reader import CSVReader
# and so on...



class ReaderFactory:
    """
    Factory class for creating appropriate document readers based on file extensions.
    Manages the registry of available readers and delegates file reading to the appropriate reader.
    """
    
    def __init__(self):
        """Initialize the reader factory with available readers."""
        self._readers: Dict[str, Type[BaseReader]] = {}
        self._reader_instances: Dict[str, BaseReader] = {}
        
        # Register built-in readers
        self.register_reader(TxtReader)
        self.register_reader(DocReader)
        # Register other readers as they become available
        # self.register_reader(PDFReader)
        # self.register_reader(CSVReader)
        # etc.
    
    def register_reader(self, reader_class: Type[BaseReader]) -> None:
        """
        Register a reader class for specific file extensions.
        
        Args:
            reader_class: The reader class to register.
        """
        # Initialize the reader instance
        reader_instance = reader_class()
        
        # Register the reader for each supported extension
        for ext in reader_instance.supported_extensions:
            ext = ext.lower()  # Normalize extension to lowercase
            if ext in self._readers:
                logger.warning(
                    f"Reader for extension '{ext}' is being overridden from "
                    f"{self._readers[ext].__name__} to {reader_class.__name__}"
                )
            self._readers[ext] = reader_class
            self._reader_instances[ext] = reader_instance
            
        logger.info(
            f"Registered {reader_class.__name__} for extensions: {', '.join(reader_instance.supported_extensions)}"
        )
    
    def unregister_reader(self, extension: str) -> None:
        """
        Unregister a reader for a specific file extension.
        
        Args:
            extension: The file extension to unregister.
        """
        extension = extension.lower()
        if extension in self._readers:
            reader_class = self._readers[extension]
            del self._readers[extension]
            if extension in self._reader_instances:
                del self._reader_instances[extension]
            logger.info(f"Unregistered {reader_class.__name__} for extension '{extension}'")
        else:
            logger.warning(f"No reader registered for extension '{extension}'")
    
    def get_reader_for_file(self, file_path: Union[str, Path]) -> Optional[BaseReader]:
        """
        Get the appropriate reader for a given file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            A reader instance if a suitable reader is found, None otherwise.
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        extension = file_path.suffix.lower()
        
        if extension in self._reader_instances:
            return self._reader_instances[extension]
        
        # Try to find a reader that can handle this file
        for reader_instance in self._reader_instances.values():
            if reader_instance.can_handle(file_path):
                return reader_instance
        
        return None
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get a list of all supported file extensions.
        
        Returns:
            A list of supported file extensions.
        """
        return list(self._readers.keys())
    
    def read_file(self, file_path: Union[str, Path], **kwargs):
        """
        Read a file using the appropriate reader.
        
        Args:
            file_path: Path to the file to read.
            **kwargs: Additional reader-specific parameters.
            
        Returns:
            The file content and metadata as returned by the specific reader.
            
        Raises:
            ReadError: If no suitable reader is found or if reading fails.
        """
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        
        # Get the appropriate reader
        reader = self.get_reader_for_file(file_path)
        
        if reader is None:
            extension = file_path.suffix.lower()
            supported = ", ".join(self.get_supported_extensions())
            raise ReadError(
                f"No reader found for file extension '{extension}'. "
                f"Supported extensions are: {supported}"
            )
        
        # Read the file
        logger.info(f"Using {reader.__class__.__name__} to read {file_path}")
        return reader.read(file_path, **kwargs)


# Create a singleton instance of the factory
reader_factory = ReaderFactory()


def read_document(file_path: Union[str, Path], **kwargs):
    """
    Convenience function to read a document using the factory.
    
    Args:
        file_path: Path to the file to read.
        **kwargs: Additional reader-specific parameters.
        
    Returns:
        The file content and metadata as returned by the specific reader.
    """
    return reader_factory.read_file(file_path, **kwargs)


def get_supported_formats() -> List[str]:
    """
    Get a list of all supported file formats/extensions.
    
    Returns:
        A list of supported file extensions.
    """
    return reader_factory.get_supported_extensions()


def register_custom_reader(reader_class: Type[BaseReader]) -> None:
    """
    Register a custom reader with the factory.
    
    Args:
        reader_class: The reader class to register.
    """
    reader_factory.register_reader(reader_class)