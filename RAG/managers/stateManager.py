import json
import os
from datetime import datetime
from typing import Dict, Any

class StateManager:
    def __init__(self, state_file_path: str):
        self.state_file_path = state_file_path
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file or initialize if doesn't exist."""
        if os.path.exists(self.state_file_path):
            with open(self.state_file_path, 'r') as f:
                return json.load(f)
        return {
            "last_run": None,
            "processed_items": {
                "sql_database": {},
                "local_filesystem": {},
                "google_drive": {}
            }
        }
    
    def save_state(self):
        """Save current state to file."""
        with open(self.state_file_path, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_last_run_time(self) -> str:
        """Get timestamp of last pipeline run."""
        return self.state["last_run"]
    
    def update_last_run_time(self):
        """Update the last run timestamp to current time."""
        self.state["last_run"] = datetime.now().isoformat()
        self.save_state()
    
    def is_item_processed(self, source: str, item_id: str) -> bool:
        """Check if an item has been processed before."""
        return item_id in self.state["processed_items"].get(source, {})
    
    def mark_item_processed(self, source: str, item_id: str, metadata: Dict = None):
        """Mark an item as processed with optional metadata."""
        if source not in self.state["processed_items"]:
            self.state["processed_items"][source] = {}
        
        self.state["processed_items"][source][item_id] = {
            "first_processed": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.save_state()