"""
Google Drive Connector module.
Authenticates and scans Google Drive for files to process.
"""
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

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account
except ImportError:
    # Log the error during initialization
    pass


class GoogleDriveConnector(ConnectorBase):
    """Connector for processing files from Google Drive."""
    
    # Define scopes needed for accessing Google Drive
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, config):
        """
        Initialize the Google Drive connector.
        
        Args:
            config: Configuration object with google_credentials_path and google_drive_folder_id
        """
        super().__init__(config)
        self.credentials_path = Path(config.google_credentials_path)
        self.folder_id = config.google_drive_folder_id
        self.processed_file = Path(config.config_dir) / "google_drive_processed_files.json"
        self.drive_service = None
        self._processed_files = set()
        
        # Initialize logger
        self.logger = get_logger(
            name=self.__class__.__name__,
            log_dir=config.log_folder,
            log_level=config.log_level
        )
        
        self.logger.info(f"Initialized {self.__class__.__name__} with credentials path: {self.credentials_path}")
        
        # Check if required libraries are installed
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            from google.oauth2 import service_account
        except ImportError as e:
            self.logger.error(f"Required Google Drive libraries not installed: {e}")
            self.logger.error("Please install them using: pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib")
        
        self._load_processed_files()
    
    def connect(self) -> bool:
        """
        Authenticate and connect to Google Drive.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        self.logger.info("Connecting to Google Drive")
        
        if not self.credentials_path.exists():
            self.logger.error(f"Error: Google Drive credentials file {self.credentials_path} does not exist")
            
            # Try to create parent directories for the credentials file
            try:
                self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory for credentials: {self.credentials_path.parent}")
                self.logger.warning(f"You need to place your Google service account JSON file at: {self.credentials_path}")
                return False
            except Exception as e:
                self.logger.error(f"Failed to create directory for credentials: {e}")
                return False
        
        try:
            # Check if required libraries are available
            try:
                from googleapiclient.discovery import build
                from googleapiclient.errors import HttpError
                from google.oauth2 import service_account
            except ImportError as e:
                self.logger.error(f"Required libraries not installed: {e}")
                return False
            
            # Load credentials
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    str(self.credentials_path), scopes=self.SCOPES)
            except Exception as e:
                self.logger.error(f"Error loading credentials from {self.credentials_path}: {e}")
                self.logger.error("Make sure the credentials file is a valid Google service account JSON file")
                return False
            
            # Build drive service
            try:
                self.drive_service = build('drive', 'v3', credentials=credentials)
            except Exception as e:
                self.logger.error(f"Error building drive service: {e}")
                return False
            
            # Test connection by fetching the folder info if folder_id is provided
            if self.folder_id:
                try:
                    self.drive_service.files().get(fileId=self.folder_id).execute()
                    self.logger.info(f"Successfully connected to Google Drive folder: {self.folder_id}")
                except HttpError as e:
                    if e.resp.status == 404:
                        self.logger.error(f"Folder not found: {self.folder_id}")
                    else:
                        self.logger.error(f"Error accessing folder {self.folder_id}: {e}")
                    return False
            else:
                self.logger.warning("No folder ID specified, will scan all accessible files")
            
            self.logger.info("Successfully connected to Google Drive")
            return True
            
        except Exception as e:
            self.logger.exception(f"Error connecting to Google Drive: {e}")
            return False
    
    def scan(self) -> List[FileMetadata]:
        """
        Scan Google Drive for unprocessed files.
        
        Returns:
            List[FileMetadata]: List of metadata for unprocessed files
        """
        self.logger.info("Starting scan of Google Drive")
        
        if not self.drive_service and not self.connect():
            self.logger.warning("Scan aborted: Could not connect to Google Drive")
            return []
        
        unprocessed_files = []
        
        try:
            # Query for files in the specified folder
            query = f"'{self.folder_id}' in parents" if self.folder_id else "trashed = false"
            
            # Get fields we need for metadata
            fields = "files(id, name, mimeType, size, modifiedTime, parents, md5Checksum)"
            
            # Execute query
            self.logger.info(f"Executing query: {query}")
            response = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields=fields,
                pageSize=1000
            ).execute()
            
            files = response.get('files', [])
            self.logger.info(f"Found {len(files)} total files in Google Drive")
            
            # Process file list
            for file in files:
                file_id = file['id']
                
                # Skip processed files
                if file_id in self._processed_files:
                    continue
                
                # Skip folders
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    continue
                
                try:
                    # Determine file type
                    file_type = self._get_file_type(file['name'], file['mimeType'])
                    
                    # Get file size (could be missing for Google Docs)
                    file_size = int(file.get('size', 0))
                    
                    # Parse modified time
                    try:
                        last_modified = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))
                    except (ValueError, KeyError):
                        self.logger.warning(f"Invalid modifiedTime for file {file['name']}, using current time")
                        last_modified = datetime.now()
                    
                    # Create file metadata
                    metadata = FileMetadata(
                        id=file_id,
                        name=file['name'],
                        path=f"drive://{file_id}",
                        size=file_size,
                        type=file_type,
                        last_modified=last_modified,
                        source=self.name,
                        additional_metadata={
                            "mime_type": file['mimeType'],
                            "parents": file.get('parents', []),
                            "google_drive_id": file_id
                        },
                        checksum=file.get('md5Checksum')
                    )
                    
                    unprocessed_files.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error processing file {file.get('name', 'unknown')}: {e}")
            
            self.logger.info(f"Found {len(unprocessed_files)} unprocessed files in Google Drive")
            return unprocessed_files
        
        except HttpError as error:
            self.logger.error(f"HTTP error scanning Google Drive: {error}")
            return []
        except Exception as e:
            self.logger.exception(f"Error scanning Google Drive: {e}")
            return []
    
    def _get_file_type(self, file_name: str, mime_type: str) -> FileType:
        """
        Determine file type from name and MIME type.
        
        Args:
            file_name: Name of the file
            mime_type: MIME type from Google Drive
            
        Returns:
            FileType: Determined file type
        """
        # First try to get from file extension
        extension = Path(file_name).suffix.lower().lstrip('.')
        if extension:
            return FileType.from_extension(extension)
        
        # If no extension, try to determine from MIME type
        mime_map = {
            'text/csv': FileType.CSV,
            'application/json': FileType.JSON,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileType.EXCEL,
            'application/vnd.ms-excel': FileType.EXCEL,
            'application/pdf': FileType.PDF,
            'text/plain': FileType.TEXT
        }
        
        return mime_map.get(mime_type, FileType.OTHER)
    
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
            item_id: Identifier of the processed file (Google Drive file ID)
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
        # No need to close the drive_service explicitly
        
    
    def download_file(self, file_id: str, destination_path: Optional[Path] = None) -> Optional[Path]:
        """
        Download a file from Google Drive to the local machine.
        
        Args:
            file_id: Google Drive file ID
            destination_path: Optional path where to save the file, if None will use google_drive_file_path from config
            
        Returns:
            Optional[Path]: Path to the downloaded file or None if download failed
        """
        self.logger.info(f"Downloading file with ID: {file_id}")
        
        if not self.drive_service and not self.connect():
            self.logger.error("Download failed: Could not connect to Google Drive")
            return None
        
        try:
            # Get file metadata to determine file name
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            file_name = file_metadata.get('name', f"downloaded_file_{file_id}")
            mime_type = file_metadata.get('mimeType', 'application/octet-stream')
            
            self.logger.info(f"File metadata: name={file_name}, mimeType={mime_type}")
            
            # Determine destination path
            if destination_path is None:
                destination_path = Path(self.config.google_drive_file_path)
                
            # Create directories if they don't exist
            destination_path.mkdir(parents=True, exist_ok=True)
            
            # Determine export method and destination file path
            output_file = destination_path / file_name
            self.logger.info(f"Downloading to: {output_file}")
            
            # Download the file
            if 'application/vnd.google-apps' in mime_type:
                # Handle Google Docs, Sheets, etc.
                export_mime_type = self._get_export_mime_type(mime_type)
                if export_mime_type:
                    self.logger.info(f"Exporting Google Workspace file as {export_mime_type}")
                    response = self.drive_service.files().export(
                        fileId=file_id,
                        mimeType=export_mime_type
                    ).execute()
                    
                    # Adjust file extension based on export type
                    extension = self._get_extension_for_mime_type(export_mime_type)
                    if extension and not output_file.name.endswith(extension):
                        output_file = output_file.with_suffix(extension)
                else:
                    self.logger.error(f"Unsupported Google Workspace file type: {mime_type}")
                    return None
            else:
                # Download regular file
                self.logger.info("Downloading regular file")
                response = self.drive_service.files().get_media(fileId=file_id).execute()
            
            # Write the file to disk
            with open(output_file, 'wb') as f:
                f.write(response)
                
            self.logger.info(f"Successfully downloaded file to {output_file}")
            return output_file
            
        except HttpError as e:
            self.logger.error(f"HTTP error downloading file {file_id}: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"Error downloading file {file_id}: {e}")
            return None

    def _get_export_mime_type(self, mime_type: str) -> Optional[str]:
        """
        Determine the export MIME type for Google Workspace files.
        
        Args:
            mime_type: Google Drive MIME type
            
        Returns:
            Optional[str]: Export MIME type or None if not supported
        """
        # Mapping of Google Workspace MIME types to export formats
        export_map = {
            'application/vnd.google-apps.document': 'application/pdf',  # Docs to PDF
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Sheets to XLSX
            'application/vnd.google-apps.presentation': 'application/pdf',  # Slides to PDF
            'application/vnd.google-apps.drawing': 'application/pdf',  # Drawings to PDF
        }
        
        return export_map.get(mime_type)

    def _get_extension_for_mime_type(self, mime_type: str) -> Optional[str]:
        """
        Get file extension for a MIME type.
        
        Args:
            mime_type: MIME type
            
        Returns:
            Optional[str]: File extension with dot or None if unknown
        """
        # Mapping of MIME types to file extensions
        extension_map = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'text/csv': '.csv',
            'application/json': '.json',
            'text/plain': '.txt',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif'
        }
        
        return extension_map.get(mime_type)