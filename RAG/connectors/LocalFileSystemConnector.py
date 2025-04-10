import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import mimetypes
import textract

class LocalFileSystemConnector:
    def __init__(self, base_directory: str):
        self.base_directory = Path(base_directory)
        self.supported_extensions = ['.txt', '.pdf', '.docx', '.xlsx', '.pptx', '.md', '.csv', '.json']
        
    def scan_directory(self, directory: Path = None, last_run_time: str = None) -> List[Dict[str, Any]]:
        """Recursively scan directory and extract content from files"""
        if directory is None:
            directory = self.base_directory
            
        documents = []
        last_run_datetime = datetime.fromisoformat(last_run_time) if last_run_time else None
        
        for item in directory.iterdir():
            if item.is_dir():
                # Recursively scan subdirectories
                documents.extend(self.scan_directory(item, last_run_time))
            elif item.is_file() and item.suffix.lower() in self.supported_extensions:
                
                # Check if file was modified after last run
                if last_run_datetime:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime <= last_run_datetime:
                        continue  # Skip files not modified since last run
                try:
                    doc = self._process_file(item)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    print(f"Error processing file {item}: {e}")
        return documents
        
    def _process_file(self, file_path: Path) -> Dict[str, Any]:
        """Extract content and metadata from file."""
        try:
            # Extract text content based on file type
            content = textract.process(str(file_path)).decode('utf-8')
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_file_hash(file_path)
            
            # Get file metadata
            stat_info = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Use st_ctime as a fallback for platforms that don't have st_birthtime
            try:
                created_time = stat_info.st_birthtime
            except AttributeError:
                created_time = stat_info.st_ctime
            
            return {
                "content": content,
                "metadata": {
                    "source": "local_filesystem",
                    "file_path": str(file_path.relative_to(self.base_directory)),
                    "file_name": file_path.name,
                    "file_type": file_path.suffix,
                    "mime_type": mime_type,
                    "size_bytes": stat_info.st_size,
                    "created_at": datetime.fromtimestamp(created_time).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "hash": file_hash
                }
            }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
            
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for deduplication."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()