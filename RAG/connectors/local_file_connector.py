"""
Local File Connector module.
Scans local directories for files to process.
"""
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .connector_base import ConnectorBase, FileMetadata, FileType
from settings.logger import get_logger

class LocalFileConnector(ConnectorBase):
    """Connector for processing local files."""
    
    def __init__(self, config):
        """
        Initialize the local file connector.
        
        Args:
            config: Configuration object with local_file_path attribute
        """
        super().__init__(config)
        self.root_path = Path(config.local_file_path)
        self.processed_file = Path(config.config_dir) / "local_processed_files.json"
        self._processed_files = set()
        
        # Initialize logger
        self.logger = get_logger(
            name=self.__class__.__name__,
            log_dir=config.log_folder,
            log_level=config.log_level
        )
        
        self.logger.info(f"Initialized {self.__class__.__name__} with root path: {self.root_path}")
        self._load_processed_files()
    
    def connect(self) -> bool:
        """
        Check if the local directory exists and is accessible.
        
        Returns:
            bool: True if the directory exists and is accessible, False otherwise
        """
        self.logger.info(f"Connecting to local directory: {self.root_path}")
        
        if not self.root_path.exists():
            error_msg = f"Error: Local path {self.root_path} does not exist"
            self.logger.error(error_msg)
            
            # Try to create the directory
            try:
                self.logger.info(f"Attempting to create directory: {self.root_path}")
                self.root_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Successfully created directory: {self.root_path}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create directory: {e}")
                return False
        
        if not self.root_path.is_dir():
            self.logger.error(f"Error: {self.root_path} is not a directory")
            return False
        
        # Check if directory is readable
        try:
            next(self.root_path.iterdir(), None)
            self.logger.info(f"Successfully connected to: {self.root_path}")
            return True
        except PermissionError:
            self.logger.error(f"Permission denied: Cannot read from {self.root_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error accessing directory {self.root_path}: {e}")
            return False
    
    def scan(self) -> List[FileMetadata]:
        """
        Scan the local directory for unprocessed files.
        
        Returns:
            List[FileMetadata]: List of metadata for unprocessed files
        """
        self.logger.info(f"Starting scan of directory: {self.root_path}")
        
        if not self.connect():
            self.logger.warning("Scan aborted: Could not connect to local directory")
            return []
        
        unprocessed_files = []
        
        try:
            scanned_files = self._scan_directory(self.root_path)
            self.logger.info(f"Found {len(scanned_files)} total files")
            
            for file_path in scanned_files:
                relative_path = str(file_path.relative_to(self.root_path))
                file_id = self._generate_file_id(file_path)
                
                if file_id not in self._processed_files:
                    try:
                        # Get file metadata
                        file_stats = file_path.stat()
                        file_type = FileType.from_extension(file_path.suffix[1:] if file_path.suffix else "")
                        
                        # Calculate checksum for the file
                        checksum = self._calculate_checksum(file_path)
                        
                        # Create file metadata
                        metadata = FileMetadata(
                            id=file_id,
                            name=file_path.name,
                            path=str(file_path),
                            size=file_stats.st_size,
                            type=file_type,
                            last_modified=datetime.fromtimestamp(file_stats.st_mtime),
                            source=self.name,
                            additional_metadata={
                                "relative_path": relative_path,
                                "creation_time": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                                "is_directory": False
                            },
                            checksum=checksum
                        )
                        
                        unprocessed_files.append(metadata)
                    except (PermissionError, FileNotFoundError) as e:
                        self.logger.warning(f"Skipping file {file_path}: {e}")
                    except Exception as e:
                        self.logger.error(f"Error processing file {file_path}: {e}")
            
            self.logger.info(f"Found {len(unprocessed_files)} unprocessed files")
            return unprocessed_files
            
        except Exception as e:
            self.logger.exception(f"Error during scan: {e}")
            return []
    
    def _scan_directory(self, directory: Path) -> List[Path]:
        """
        Recursively scan a directory for files.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            List[Path]: List of file paths
        """
        files = []
        
        try:
            for item in directory.iterdir():
                if item.is_file():
                    files.append(item)
                elif item.is_dir():
                    try:
                        files.extend(self._scan_directory(item))
                    except PermissionError:
                        self.logger.warning(f"Permission denied: Cannot access subdirectory {item}")
                    except Exception as e:
                        self.logger.warning(f"Error scanning subdirectory {item}: {e}")
        except PermissionError:
            self.logger.warning(f"Permission denied: Cannot access directory {directory}")
        except Exception as e:
            self.logger.warning(f"Error scanning directory {directory}: {e}")
        
        return files
    
    def _generate_file_id(self, file_path: Path) -> str:
        """
        Generate a unique identifier for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Unique identifier
        """
        rel_path = str(file_path.relative_to(self.root_path))
        # Include last modified time to detect changes
        try:
            last_modified = file_path.stat().st_mtime
        except (FileNotFoundError, PermissionError) as e:
            self.logger.warning(f"Error getting stats for {file_path}: {e}")
            last_modified = 0
        
        return f"local_{hash(rel_path)}_{int(last_modified)}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate MD5 checksum for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MD5 checksum
        """
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}")
            return ""
        except PermissionError:
            self.logger.warning(f"Permission denied: Cannot read file {file_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def get_processed_items(self) -> Set[str]:
        """
        Get the set of already processed file identifiers.
        
        Returns:
            Set[str]: Set of processed file identifiers
        """
        return self._processed_files
    
    def mark_as_processed(self, item_id: str) -> None:
        """
        Mark a file as processed.
        
        Args:
            item_id: Identifier of the processed file
        """
        self.logger.info(f"Marking item as processed: {item_id}")
        self._processed_files.add(item_id)
        self._save_processed_files()
    
    def _load_processed_files(self) -> None:
        """Load the set of processed files from disk."""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, "r") as f:
                    data = json.load(f)
                    self._processed_files = set(data.get("processed_files", []))
                self.logger.info(f"Loaded {len(self._processed_files)} processed files from {self.processed_file}")
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in processed files file: {self.processed_file}")
                self._processed_files = set()
            except Exception as e:
                self.logger.error(f"Error loading processed files: {e}")
                self._processed_files = set()
        else:
            self.logger.info(f"Processed files file not found: {self.processed_file}")
            self._processed_files = set()
    
    def _save_processed_files(self) -> None:
        """Save the set of processed files to disk."""
        try:
            self.processed_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.processed_file, "w") as f:
                json.dump({"processed_files": list(self._processed_files)}, f)
            self.logger.info(f"Saved {len(self._processed_files)} processed files to {self.processed_file}")
        except PermissionError:
            self.logger.error(f"Permission denied: Cannot write to {self.processed_file}")
        except Exception as e:
            self.logger.error(f"Error saving processed files: {e}")
    
    def close(self) -> None:
        """Close the connector and save processed files."""
        self.logger.info(f"Closing {self.__class__.__name__}")
        self._save_processed_files()