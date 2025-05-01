"""
State manager module for tracking the processing state of files in the pipeline.

This module provides functionality to track the state of files as they are processed
through the various stages of the pipeline, enabling monitoring, reporting, and
recovery from failures.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..config.settings import settings
from ..utils.logger import logger


class StateManager:
    """
    Manages the state of files being processed through the pipeline.
    
    This class maintains a record of the processing state for each file,
    tracking which stages have been completed and any errors encountered.
    """
    
    def __init__(self, state_file: Optional[str] = None):
        """
        Initialize the state manager.
        
        Args:
            state_file: Path to the state file. If None, defaults to a file in the logs directory.
        """
        self.state_file = state_file or str(settings.logs_dir / "pipeline_state.json")
        self.state: Dict[str, Dict[str, Any]] = {}
        self._load_state()
    
    def _load_state(self) -> None:
        """Load the state from the state file if it exists."""
        state_path = Path(self.state_file)
        
        if state_path.exists():
            try:
                with open(state_path, "r") as f:
                    self.state = json.load(f)
                logger.debug(f"Loaded state from {self.state_file}")
            except Exception as e:
                logger.warning(f"Failed to load state from {self.state_file}: {str(e)}")
                # Initialize with empty state
                self.state = {}
        else:
            # Ensure the directory exists
            state_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"State file {self.state_file} does not exist, starting with empty state")
            self.state = {}
    
    def _save_state(self) -> None:
        """Save the current state to the state file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state to {self.state_file}: {str(e)}")
    
    def get_file_state(self, file_id: str) -> Dict[str, Any]:
        """
        Get the current state of a file.
        
        Args:
            file_id: Unique identifier for the file.
            
        Returns:
            Dictionary containing the state of the file.
        """
        return self.state.get(file_id, {})
    
    def update_file_state(
        self, 
        file_id: str, 
        stage: str, 
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the state of a file for a specific processing stage.
        
        Args:
            file_id: Unique identifier for the file.
            stage: Processing stage (e.g., "read", "processed", "chunked").
            success: Whether the stage completed successfully.
            error: Error message if success is False.
            metadata: Additional metadata to store.
        """
        # Initialize file state if not exists
        if file_id not in self.state:
            self.state[file_id] = {
                "started_at": datetime.now().isoformat(),
                "stages": {}
            }
        
        # Update stage information
        self.state[file_id]["stages"][stage] = {
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add error information if provided
        if error:
            self.state[file_id]["stages"][stage]["error"] = error
        
        # Add metadata if provided
        if metadata:
            if "metadata" not in self.state[file_id]:
                self.state[file_id]["metadata"] = {}
            self.state[file_id]["metadata"].update(metadata)
        
        # Update last modified timestamp
        self.state[file_id]["last_modified"] = datetime.now().isoformat()
        
        # Save the updated state
        self._save_state()
    
    def get_file_progress(self, file_id: str) -> Dict[str, Any]:
        """
        Get the progress of a file through the pipeline.
        
        Args:
            file_id: Unique identifier for the file.
            
        Returns:
            Dictionary containing the progress information.
        """
        file_state = self.get_file_state(file_id)
        
        if not file_state:
            return {"file_id": file_id, "status": "unknown", "progress": 0}
        
        # Define expected stages in order
        expected_stages = ["read", "processed", "chunked", "embedded", "loaded"]
        
        # Count completed stages
        completed_stages = 0
        failed_stage = None
        
        for stage in expected_stages:
            stage_info = file_state.get("stages", {}).get(stage, {})
            
            if stage_info.get("success", False):
                completed_stages += 1
            elif stage in file_state.get("stages", {}):
                # Stage was attempted but failed
                failed_stage = stage
                break
            else:
                # Stage not yet attempted
                break
        
        # Calculate progress percentage
        progress = (completed_stages / len(expected_stages)) * 100
        
        # Determine overall status
        if failed_stage:
            status = f"failed_at_{failed_stage}"
        elif completed_stages == len(expected_stages):
            status = "completed"
        elif completed_stages == 0:
            status = "not_started"
        else:
            status = "in_progress"
        
        return {
            "file_id": file_id,
            "status": status,
            "progress": progress,
            "completed_stages": completed_stages,
            "total_stages": len(expected_stages),
            "started_at": file_state.get("started_at"),
            "last_modified": file_state.get("last_modified")
        }
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the pipeline's overall progress.
        
        Returns:
            Dictionary containing the summary information.
        """
        total_files = len(self.state)
        completed_files = 0
        failed_files = 0
        in_progress_files = 0
        not_started_files = 0
        
        # Count files by status
        for file_id in self.state:
            progress = self.get_file_progress(file_id)
            status = progress.get("status", "")
            
            if status == "completed":
                completed_files += 1
            elif status.startswith("failed"):
                failed_files += 1
            elif status == "in_progress":
                in_progress_files += 1
            elif status == "not_started":
                not_started_files += 1
        
        # Calculate overall progress
        overall_progress = 0
        if total_files > 0:
            file_progresses = [
                self.get_file_progress(file_id).get("progress", 0)
                for file_id in self.state
            ]
            overall_progress = sum(file_progresses) / total_files
        
        return {
            "total_files": total_files,
            "completed_files": completed_files,
            "failed_files": failed_files,
            "in_progress_files": in_progress_files,
            "not_started_files": not_started_files,
            "overall_progress": overall_progress
        }
    
    def mark_pipeline_started(self, run_id: Optional[str] = None) -> str:
        """
        Mark the pipeline as started with a new run ID.
        
        Args:
            run_id: Optional run ID. If None, a timestamp-based ID is generated.
            
        Returns:
            The run ID.
        """
        # Generate run ID if not provided
        if run_id is None:
            run_id = f"run_{int(time.time())}"
        
        # Create or update pipeline metadata
        if "pipeline_metadata" not in self.state:
            self.state["pipeline_metadata"] = {}
        
        if "runs" not in self.state["pipeline_metadata"]:
            self.state["pipeline_metadata"]["runs"] = {}
        
        # Record run start
        self.state["pipeline_metadata"]["runs"][run_id] = {
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Update current run
        self.state["pipeline_metadata"]["current_run"] = run_id
        
        # Save state
        self._save_state()
        
        return run_id
    
    def mark_pipeline_completed(self, run_id: Optional[str] = None, success: bool = True) -> None:
        """
        Mark the pipeline as completed.
        
        Args:
            run_id: Run ID. If None, the current run is used.
            success: Whether the pipeline completed successfully.
        """
        # Get current run if run_id not provided
        if run_id is None:
            run_id = self.state.get("pipeline_metadata", {}).get("current_run")
        
        if run_id is None:
            logger.warning("Cannot mark pipeline completed: no run ID provided and no current run found")
            return
        
        # Update run status
        if (
            "pipeline_metadata" in self.state
            and "runs" in self.state["pipeline_metadata"]
            and run_id in self.state["pipeline_metadata"]["runs"]
        ):
            self.state["pipeline_metadata"]["runs"][run_id].update({
                "completed_at": datetime.now().isoformat(),
                "status": "success" if success else "failed"
            })
            
            # Add summary if available
            summary = self.get_pipeline_summary()
            self.state["pipeline_metadata"]["runs"][run_id]["summary"] = summary
            
            # Save state
            self._save_state()
        else:
            logger.warning(f"Cannot mark pipeline completed: run {run_id} not found")
    
    def reset_state(self) -> None:
        """Reset the state to empty and save."""
        self.state = {}
        self._save_state()
    
    def get_failed_files(self) -> List[Dict[str, Any]]:
        """
        Get a list of files that failed processing.
        
        Returns:
            List of dictionaries containing information about failed files.
        """
        failed_files = []
        
        for file_id, file_state in self.state.items():
            # Skip pipeline metadata
            if file_id == "pipeline_metadata":
                continue
                
            # Check each stage for failures
            for stage, stage_info in file_state.get("stages", {}).items():
                if not stage_info.get("success", True):
                    failed_files.append({
                        "file_id": file_id,
                        "failed_stage": stage,
                        "error": stage_info.get("error", "Unknown error"),
                        "timestamp": stage_info.get("timestamp")
                    })
                    # Only record the first failure for each file
                    break
        
        return failed_files
    
    def get_successful_files(self) -> List[str]:
        """
        Get a list of files that completed all stages successfully.
        
        Returns:
            List of file IDs that completed processing.
        """
        successful_files = []
        
        for file_id in self.state:
            # Skip pipeline metadata
            if file_id == "pipeline_metadata":
                continue
                
            progress = self.get_file_progress(file_id)
            if progress.get("status") == "completed":
                successful_files.append(file_id)
        
        return successful_files