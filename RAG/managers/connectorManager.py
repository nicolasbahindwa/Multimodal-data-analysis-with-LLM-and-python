from typing import List, Dict, Any
import importlib
import hashlib
from datetime import datetime
from pathlib import Path
from stateManager import StateManager

class ConnectorManager:
    def __init__(self, state_manager: StateManager):
        self.connectors = {}
        self.state_manager = state_manager
        
    def register_connector(self, name: str, connector):
        """Register a data source connector."""
        self.connectors[name] = connector
    
    def extract_all(self, incremental: bool = True) -> List[Dict[str, Any]]:
        """
        Extract data from all registered connectors.
        
        Args:
            incremental: If True, only extract data changed since last run
        """
        all_documents = []
        last_run_time = self.state_manager.get_last_run_time() if incremental else None
        
        for name, connector in self.connectors.items():
            print(f"Extracting data from {name}...")
            
            try:
                if name == 'sql_database':
                    tables = connector.list_tables()
                    for table in tables:
                        documents = connector.extract_table_data(table, last_run_time=last_run_time)
                        # Filter out already processed items
                        documents = self._filter_processed_items(name, documents)
                        all_documents.extend(documents)
                        
                elif name == 'local_filesystem':
                    # Pass last_run_time to the scan_directory method
                    documents = connector.scan_directory(last_run_time=last_run_time)
                    # Filter based on file hash or modification date
                    documents = self._filter_processed_items(name, documents)
                    all_documents.extend(documents)
                    
                elif name == 'google_drive':
                    documents = connector.list_files(last_run_time=last_run_time)
                    documents = self._filter_processed_items(name, documents)
                    all_documents.extend(documents)
                
                else:
                    # Fallback for unknown connector types
                    print(f"Warning: Unknown connector type '{name}', trying to use dynamic dispatch")
                    if hasattr(connector, 'extract_data'):
                        documents = connector.extract_data(last_run_time=last_run_time)
                        documents = self._filter_processed_items(name, documents)
                        all_documents.extend(documents)
                    else:
                        print(f"Error: Connector '{name}' has no recognized extraction method")
            
            except Exception as e:
                print(f"Error extracting data from '{name}': {e}")
                # Continue with other connectors even if one fails
        
        if all_documents:
            # Mark all extracted documents as processed
            self._mark_documents_processed(all_documents)
            
            # Update last run time
            self.state_manager.update_last_run_time()
        else:
            print("No new documents found to process")
        
        return all_documents
    
    def _filter_processed_items(self, source: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out already processed items."""
        filtered_docs = []
        
        for doc in documents:
            try:
                # Determine unique ID based on source
                if source == 'sql_database':
                    item_id = f"{doc['metadata']['table']}_{doc['metadata']['id']}"
                elif source == 'local_filesystem':
                    item_id = doc['metadata']['hash']
                elif source == 'google_drive':
                    item_id = doc['metadata']['file_id']
                else:
                    # Default to hash of content if no specific ID
                    item_id = hashlib.md5(doc['content'].encode()).hexdigest()
                
                # Add document if not already processed
                if not self.state_manager.is_item_processed(source, item_id):
                    # Store the item_id for later marking as processed
                    doc['metadata']['item_id'] = item_id
                    filtered_docs.append(doc)
            except KeyError as e:
                print(f"Warning: Document from {source} missing required metadata: {e}")
            except Exception as e:
                print(f"Error filtering document from {source}: {e}")
        
        return filtered_docs
    
    def _mark_documents_processed(self, documents: List[Dict[str, Any]]):
        """Mark all documents as processed."""
        for doc in documents:
            try:
                source = doc['metadata']['source']
                item_id = doc['metadata']['item_id']
                self.state_manager.mark_item_processed(source, item_id)
            except KeyError as e:
                print(f"Warning: Cannot mark document as processed, missing metadata: {e}")