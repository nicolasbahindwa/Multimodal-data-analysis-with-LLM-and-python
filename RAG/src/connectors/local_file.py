"""
Local file connector module for working with files in the local filesystem.

This module provides the LocalFileConnector class for reading files from the local
filesystem in a standardized way.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO

from .base import BaseConnector
from ..utils.logger import logger
from ..utils.error_handler import ConnectionError, error_handler
from ..config.settings import settings


class LocalFileConnector(BaseConnector):
    """
    Connector for accessing files in the local filesystem.
    
    This connector allows the pipeline to read files from the local filesystem,
    supporting various file operations such as listing files and retrieving content.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the local file connector.
        
        Args:
            base_path: Base directory path for file operations.
                       If None, the path from settings is used.
        """
        super().__init__()
        
        # Use settings-provided base_path if none specified
        if base_path is None:
            connector_config = settings.get_connector_config("local_file")
            base_path = connector_config.get("base_path")
            logger.debug(f"Using base_path from settings: {base_path}")
        
        # Use current working directory as fallback if still None
        if base_path is None:
            base_path = os.getcwd()
            logger.debug(f"No base_path specified, using current directory: {base_path}")
        
        # Convert to Path object for safer handling
        path_obj = Path(base_path)
        
        # Convert to absolute path if it's relative
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj
            logger.debug(f"Converting relative path to absolute: {path_obj}")
        
        # Store as normalized string path
        self.base_path = str(path_obj.resolve())
        
        logger.debug(f"Initialized LocalFileConnector with base path: {self.base_path}")
    
    @error_handler(ConnectionError, "Failed to connect to local filesystem")
    def connect(self, check_directory: bool = True) -> bool:
        """
        Verify that the base path exists and is accessible.
        
        Args:
            check_directory: If True, verify and potentially create directory.
                            If False, only check if directory exists.
        
        Returns:
            True if the base path exists and is accessible, False otherwise.
            
        Raises:
            ConnectionError: If the base path doesn't exist or isn't accessible.
        """
        base_dir = Path(self.base_path)
        
        if not base_dir.exists():
            if check_directory:
                logger.info(f"Base path {self.base_path} doesn't exist, creating it")
                try:
                    base_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ConnectionError(
                        f"Failed to create base path {self.base_path}",
                        original_error=e
                    )
            else:
                raise ConnectionError(f"Base path {self.base_path} doesn't exist and will not be created")
        
        if not base_dir.is_dir():
            raise ConnectionError(f"Base path {self.base_path} is not a directory")
        
        if not os.access(self.base_path, os.R_OK):
            raise ConnectionError(f"Base path {self.base_path} is not readable")
        
        logger.info(f"Successfully connected to local filesystem at {self.base_path}")
        return True
    
    @error_handler(ConnectionError, "Failed to list files in {args[0]}")
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List files in the specified path.
        
        Args:
            path: Relative path from the base path to list files from.
                 If empty, files are listed from the base path.
                 
        Returns:
            List of dictionaries containing file metadata.
            
        Raises:
            ConnectionError: If listing files fails.
        """
        # Resolve the full path
        full_path = os.path.join(self.base_path, path) if path else self.base_path
        full_path = os.path.abspath(full_path)
        
        # Print debug info about the path
        logger.debug(f"Listing files from: {full_path}")
        logger.debug(f"Directory exists: {os.path.exists(full_path)}")
        logger.debug(f"Is directory: {os.path.isdir(full_path) if os.path.exists(full_path) else 'N/A'}")
        
        # Ensure the path exists
        if not os.path.exists(full_path):
            logger.warning(f"Path {full_path} does not exist")
            return []
        
        # Ensure the path is a directory
        if not os.path.isdir(full_path):
            logger.warning(f"Path {full_path} is not a directory")
            return []
        
        # List files
        files = []
        
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                
                # Skip directories
                if os.path.isdir(item_path):
                    logger.debug(f"Skipping directory: {item}")
                    continue
                
                # Get file metadata
                stats = os.stat(item_path)
                
                # Create file info dictionary
                file_info = {
                    "id": str(item_path),
                    "name": item,
                    "path": str(item_path),
                    "size": stats.st_size,
                    "modified": stats.st_mtime,
                    "created": stats.st_ctime,
                    "type": "file",
                    "extension": os.path.splitext(item)[1].lower().lstrip("."),
                    "source": "local_file"
                }
                
                files.append(file_info)
                logger.debug(f"Found file: {item} ({stats.st_size} bytes)")
            
            logger.info(f"Found {len(files)} files in {full_path}")
            return files
            
        except Exception as e:
            raise ConnectionError(
                f"Failed to list files in {full_path}",
                original_error=e
            )
    
    @error_handler(ConnectionError, "Failed to retrieve file {args[0]}")
    def get_file(self, file_id: str) -> bytes:
        """
        Retrieve a file's contents.
        
        Args:
            file_id: Path of the file to retrieve.
            
        Returns:
            File contents as bytes.
            
        Raises:
            ConnectionError: If retrieving the file fails.
        """
        # Check if file_id is a relative path
        if not os.path.isabs(file_id):
            file_path = os.path.join(self.base_path, file_id)
        else:
            file_path = file_id
        
        # Ensure the file exists
        if not os.path.exists(file_path):
            raise ConnectionError(f"File {file_path} does not exist")
        
        # Ensure the file is readable
        if not os.path.isfile(file_path):
            raise ConnectionError(f"Path {file_path} is not a file")
        
        if not os.access(file_path, os.R_OK):
            raise ConnectionError(f"File {file_path} is not readable")
        
        # Read the file
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            logger.info(f"Successfully retrieved file {file_path} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            raise ConnectionError(
                f"Failed to read file {file_path}",
                original_error=e
            )
    
    @error_handler(ConnectionError, "Failed to check if file exists: {args[0]}")
    def file_exists(self, file_id: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_id: Path of the file to check.
            
        Returns:
            True if the file exists, False otherwise.
        """
        # Check if file_id is a relative path
        if not os.path.isabs(file_id):
            file_path = os.path.join(self.base_path, file_id)
        else:
            file_path = file_id
        
        exists = os.path.exists(file_path) and os.path.isfile(file_path)
        logger.debug(f"Checking if file exists: {file_path} - Result: {exists}")
        return exists