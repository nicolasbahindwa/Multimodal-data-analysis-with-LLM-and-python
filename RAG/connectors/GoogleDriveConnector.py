from googleapiclient.discovery import build
from google.oauth2 import service_account
import io
from googleapiclient.http import MediaIoBaseDownload
from typing import List, Dict, Any
import textract
from datetime import datetime

class GoogleDriveConnector:
    def __init__(self, credentials_path: str):
        """
        Initialize Google Drive connector with service account credentials.
        
        Args:
            credentials_path: Path to service account JSON file
        """
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.supported_mime_types = {
            'application/vnd.google-apps.document': 'text/plain',
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/pdf': 'application/pdf',
            'text/plain': 'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }

    def list_files(self, folder_id: str = None, last_run_time: str = None, page_size: int = 100) -> List[Dict[str, Any]]:
        """List files in Google Drive, optionally filtering by folder and time."""
        query = "trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        
        # Add time filter if provided
        if last_run_time:
            query += f" and modifiedTime > '{last_run_time}'"
            
        if folder_id:
            query += f" and '{folder_id}' in parents"

        documents = []
        page_token = None
        
        while True:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, owners, webViewLink)',
                pageToken=page_token,
                pageSize=page_size
            ).execute()
            
            for file in response.get('files', []):
                if file['mimeType'] in self.supported_mime_types:
                    try:
                        content = self._extract_file_content(file)
                        doc = {
                            "content": content,
                            "metadata": {
                                "source": "google_drive",
                                "file_id": file['id'],
                                "file_name": file['name'],
                                "mime_type": file['mimeType'],
                                "created_at": file['createdTime'],
                                "modified_at": file['modifiedTime'],
                                "web_link": file['webViewLink'],
                                "owner": file.get('owners', [{}])[0].get('displayName', 'Unknown')
                            }
                        }
                        documents.append(doc)
                    except Exception as e:
                        print(f"Error processing Google Drive file {file['name']}: {e}")
                    
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
                
        return documents
    
    def _extract_file_content(self, file) -> str:
        """Download and extract content from a Google Drive file."""
        file_id = file['id']
        mime_type = file['mimeType']
        
        if mime_type.startswith('application/vnd.google-apps'):
            # Handle Google native formats (Docs, Sheets, Slides)
            export_mime_type = self.supported_mime_types[mime_type]
            request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
        else:
            # Handle non-Google formats
            request = self.service.files().get_media(fileId=file_id)
        
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_content.seek(0)
        
        # Extract text based on mime type
        if mime_type == 'text/plain':
            return file_content.read().decode('utf-8')
        else:
            # Use textract to extract text from binary formats
            return textract.process(file_content).decode('utf-8')