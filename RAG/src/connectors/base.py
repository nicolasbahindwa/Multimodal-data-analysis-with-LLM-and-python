"""
Base connector module for handling connections to various data sources.

This module provides the BaseConnector abstract class that defines the interface
for all connectors in the pipeline system.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO

from ..utils.logger import logger
from ..utils.error_handler import ConnectionError, error_handler


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.
    
    Defines the interface that all connector implementations must follow
    to ensure consistent behavior across different data sources.
    """
    
    def __init__(self):
        """Initialize the connector."""
        logger.debug(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish a connection to the data source.
        
        Returns:
            True if connection is successful, False otherwise.
            
        Raises:
            ConnectionError: If the connection fails.
        """
        pass
    
    @abstractmethod
    def list_files(self, path: str) -> List[Dict[str, Any]]:
        """
        List available files in the specified path.
        
        Args:
            path: Path to list files from.
            
        Returns:
            List of dictionaries containing file metadata.
            
        Raises:
            ConnectionError: If listing files fails.
        """
        pass
    
    @abstractmethod
    def get_file(self, file_id: str) -> bytes:
        """
        Retrieve a file's contents.
        
        Args:
            file_id: Unique identifier or path of the file to retrieve.
            
        Returns:
            File contents as bytes.
            
        Raises:
            ConnectionError: If retrieving the file fails.
        """
        pass
    
    @error_handler(ConnectionError, "Failed to check if file exists: {args[0]}")
    def file_exists(self, file_id: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_id: Unique identifier or path of the file to check.
            
        Returns:
            True if the file exists, False otherwise.
            
        Raises:
            ConnectionError: If checking file existence fails.
        """
        try:
            # Default implementation tries to list files and check
            # if the specified file_id is in the results
            files = self.list_files(os.path.dirname(file_id))
            for file in files:
                if file.get("id") == file_id or file.get("path") == file_id:
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking if file {file_id} exists: {str(e)}")
            return False
    
    def close(self) -> None:
        """
        Close the connection to the data source.
        
        This method should be overridden by connectors that require
        explicit connection closing, such as database connections.
        """
        logger.debug(f"Closing connection for {self.__class__.__name__}")
    
    def __enter__(self):
        """Context manager entry that ensures connection is established."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit that ensures connection is closed."""
        self.close()