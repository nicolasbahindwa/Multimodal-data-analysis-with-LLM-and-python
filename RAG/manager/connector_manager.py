"""
Connector Manager module.
Manages and coordinates all data connectors.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connectors.connector_base import ConnectorBase, FileMetadata, TableMetadata
from settings.config import Config
from settings.logger import get_logger

# Import connectors - handle if modules are not found
try:
    from connectors.local_file_connector import LocalFileConnector
except ImportError:
    LocalFileConnector = None

try:
    from connectors.google_drive_connector import GoogleDriveConnector
except ImportError:
    GoogleDriveConnector = None

try:
    from connectors.sql_connector import SQLConnector
except ImportError:
    SQLConnector = None


class ConnectorManager:
    """Manager class for all data connectors."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the connector manager.
        
        Args:
            config: Configuration object, if None a default one will be created
        """
        self.config = config or Config()
        self.connectors = {}
        self.queue_file = Path(self.config.config_dir) / "processing_queue.json"
        self.queue = []
        
        # Initialize logger
        self.logger = get_logger(
            name=self.__class__.__name__,
            log_dir=self.config.log_folder,
            log_level=self.config.log_level
        )
        
        self.logger.info(f"Initialized ConnectorManager")
        
        # Initialize and register connectors
        self._register_connectors()
        self._load_queue()
    
    def _register_connectors(self) -> None:
        """Initialize and register all available connectors."""
        # Register Local File Connector
        if LocalFileConnector is not None:
            local_path = self.config.local_file_path
            try:
                if not os.path.exists(local_path):
                    self.logger.warning(f"Local file path does not exist: {local_path}")
                    # Try to create the directory
                    Path(local_path).mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created local file directory: {local_path}")
                
                self.connectors['local_file'] = LocalFileConnector(self.config)
                self.logger.info(f"Registered Local File Connector with path: {local_path}")
            except Exception as e:
                self.logger.error(f"Failed to register Local File Connector: {e}")
        else:
            self.logger.warning("LocalFileConnector module not found")
        
        # Register Google Drive Connector if credentials exist
        if GoogleDriveConnector is not None:
            creds_path = self.config.google_credentials_path
            try:
                if not os.path.exists(creds_path):
                    self.logger.warning(f"Google Drive credentials not found: {creds_path}")
                    # Create directory for credentials
                    Path(creds_path).parent.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created directory for credentials: {Path(creds_path).parent}")
                else:
                    self.connectors['google_drive'] = GoogleDriveConnector(self.config)
                    self.logger.info(f"Registered Google Drive Connector with credentials: {creds_path}")
            except Exception as e:
                self.logger.error(f"Failed to register Google Drive Connector: {e}")
        else:
            self.logger.warning("GoogleDriveConnector module not found")
        
        # Register SQL Connector if connection string is provided
        if SQLConnector is not None and self.config.sql_connection_string:
            try:
                self.connectors['sql'] = SQLConnector(self.config)
                self.logger.info(f"Registered SQL Connector")
            except Exception as e:
                self.logger.error(f"Failed to register SQL Connector: {e}")
        else:
            if not self.config.sql_connection_string:
                self.logger.info("SQL connection string not provided, skipping SQL Connector")
            elif SQLConnector is None:
                self.logger.warning("SQLConnector module not found")
    
    def scan_all(self) -> List[Union[FileMetadata, TableMetadata]]:
        """
        Scan all data sources for unprocessed items.
        
        Returns:
            List[Union[FileMetadata, TableMetadata]]: List of metadata for unprocessed items
        """
        self.logger.info("Starting scan of all data sources")
        all_items = []
        
        if not self.connectors:
            self.logger.warning("No connectors registered")
            return all_items
        
        for name, connector in self.connectors.items():
            try:
                self.logger.info(f"Scanning {name}...")
                items = connector.scan()
                self.logger.info(f"Found {len(items)} unprocessed items in {name}")
                all_items.extend(items)
            except Exception as e:
                self.logger.error(f"Error scanning {name}: {e}")
        
        self.logger.info(f"Found {len(all_items)} total unprocessed items across all connectors")
        return all_items
    
    def scan_and_queue(self) -> int:
        """
        Scan all data sources and add unprocessed items to the processing queue.
        
        Returns:
            int: Number of items added to the queue
        """
        self.logger.info("Scanning all data sources and adding to queue")
        items = self.scan_all()
        
        # Filter out already queued items
        queued_ids = {item['id'] for item in self.queue}
        new_items = [item for item in items if item.id not in queued_ids]
        
        # Add new items to the queue
        for item in new_items:
            self.queue.append(item.to_dict())
        
        # Save queue
        self._save_queue()
        
        self.logger.info(f"Added {len(new_items)} new items to the processing queue")
        return len(new_items)
    
    def get_queue(self) -> List[Dict[str, Any]]:
        """
        Get the current processing queue.
        
        Returns:
            List[Dict[str, Any]]: Current processing queue
        """
        return self.queue
    
    def mark_as_processed(self, item_id: str, last_key: Optional[Any] = None) -> None:
        """
        Mark an item as processed in both the queue and the source connector.
        
        Args:
            item_id: Identifier of the processed item
            last_key: Latest processed key value (for SQL tables)
        """
        self.logger.info(f"Marking item as processed: {item_id}")
        
        # Find the item in the queue
        for i, item in enumerate(self.queue):
            if item['id'] == item_id:
                # Remove from queue
                processed_item = self.queue.pop(i)
                self._save_queue()
                
                # Mark as processed in the source connector
                source = processed_item.get('source')
                if source:
                    connector_name = source.lower().replace('connector', '')
                    connector = self.connectors.get(connector_name)
                    
                    if connector:
                        self.logger.debug(f"Marking item as processed in source connector: {connector_name}")
                        if isinstance(connector, SQLConnector) and last_key is not None:
                            connector.mark_as_processed(item_id, last_key)
                        else:
                            connector.mark_as_processed(item_id)
                    else:
                        self.logger.warning(f"Source connector '{connector_name}' not found for item {item_id}")
                else:
                    self.logger.warning(f"No source specified for item {item_id}")
                
                return
        
        self.logger.warning(f"Item {item_id} not found in queue")
    
    def _load_queue(self) -> None:
        """Load the processing queue from disk."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r") as f:
                    self.queue = json.load(f)
                self.logger.info(f"Loaded {len(self.queue)} items from processing queue: {self.queue_file}")
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in queue file: {self.queue_file}")
                self.queue = []
            except Exception as e:
                self.logger.error(f"Error loading processing queue: {e}")
                self.queue = []
        else:
            self.logger.info(f"Queue file not found, starting with empty queue: {self.queue_file}")
            self.queue = []
    
    def _save_queue(self) -> None:
        """Save the processing queue to disk."""
        try:
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.queue_file, "w") as f:
                json.dump(self.queue, f, indent=2)
            self.logger.info(f"Saved {len(self.queue)} items to processing queue: {self.queue_file}")
        except PermissionError:
            self.logger.error(f"Permission denied: Cannot write to {self.queue_file}")
        except Exception as e:
            self.logger.error(f"Error saving processing queue: {e}")
    
    def close(self) -> None:
        """Close all connectors and save state."""
        self.logger.info("Closing ConnectorManager and all connectors")
        self._save_queue()
        
        for name, connector in self.connectors.items():
            try:
                self.logger.debug(f"Closing connector: {name}")
                connector.close()
            except Exception as e:
                self.logger.error(f"Error closing connector {name}: {e}")
    
    def download_item(self, item_id: str, destination_path: Optional[str] = None) -> Optional[str]:
        """
        Download an item from its source connector.
        
        Args:
            item_id: Identifier of the item to download
            destination_path: Optional destination path
            
        Returns:
            Optional[str]: Path to the downloaded item or None if download failed
        """
        self.logger.info(f"Downloading item: {item_id}")
        
        # Find the item in the queue
        item = None
        for queued_item in self.queue:
            if queued_item['id'] == item_id:
                item = queued_item
                break
        
        if not item:
            self.logger.warning(f"Item {item_id} not found in queue")
            return None
        
        # Get the source connector
        source = item.get('source')
        if not source:
            self.logger.warning(f"No source specified for item {item_id}")
            return None
        
        connector_name = source.lower().replace('connector', '')
        connector = self.connectors.get(connector_name)
        
        if not connector:
            self.logger.warning(f"Source connector '{connector_name}' not found for item {item_id}")
            return None
        
        # Determine destination path
        dest_path = None
        if destination_path:
            dest_path = Path(destination_path)
        
        # Download the item
        if hasattr(connector, 'download_file'):
            downloaded_path = connector.download_file(item_id, dest_path)
            if downloaded_path:
                self.logger.info(f"Successfully downloaded item {item_id} to {downloaded_path}")
                return str(downloaded_path)
            else:
                self.logger.error(f"Failed to download item {item_id}")
                return None
        else:
            self.logger.warning(f"Connector {connector_name} does not support downloading")
            return None

    def download_queue(self, destination_path: Optional[str] = None, item_type: Optional[str] = None) -> List[str]:
        """
        Download all items in the queue.
        
        Args:
            destination_path: Optional destination path
            item_type: Optional item type filter (e.g., 'google_drive', 'local_file', 'sql')
            
        Returns:
            List[str]: List of paths to downloaded items
        """
        self.logger.info("Downloading all items in the queue")
        
        downloaded_paths = []
        
        for item in self.queue:
            item_id = item.get('id')
            if not item_id:
                continue
                
            # Apply type filter if specified
            if item_type:
                source = item.get('source', '').lower()
                if item_type.lower() not in source:
                    continue
                    
            # Download the item
            downloaded_path = self.download_item(item_id, destination_path)
            if downloaded_path:
                downloaded_paths.append(downloaded_path)
        
        self.logger.info(f"Downloaded {len(downloaded_paths)} items from the queue")
        return downloaded_paths