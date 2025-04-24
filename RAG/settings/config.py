"""
Configuration module for data connectors.
Loads configuration from environment variables.
"""
import os
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Configuration class for data connectors."""
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize configuration from environment variables.
        
        Args:
            env_file: Path to the .env file
        """
        # Initialize basic logger first so we can log the debugging info
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Define the location of the shared .env file
        current_dir = Path(os.path.abspath(__file__)).parent  # settings dir
        rag_dir = current_dir.parent  # RAG dir
        project_root = rag_dir.parent  # Parent of RAG dir (multimodal data analysis...)
        
        # Print debugging information
        print("=== ENV FILE DEBUGGING INFO ===")
        print(f"env_file parameter: {env_file}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Current script directory: {current_dir}")
        print(f"RAG directory: {rag_dir}")
        print(f"Project root directory: {project_root}")
        
        # Possible locations for the .env file
        possible_env_paths = [
            # If an absolute path was provided, use it directly
            Path(env_file) if os.path.isabs(env_file) else None,
            # Check in current working directory
            Path(os.getcwd()) / env_file,
            # Check in project root
            project_root / env_file,
            # Check in RAG directory
            rag_dir / env_file,
            # Check in settings directory
            current_dir / env_file,
        ]
        
        # Filter out None values
        possible_env_paths = [p for p in possible_env_paths if p is not None]
        
        # Try to load the .env file from the possible locations
        env_loaded = False
        for env_path in possible_env_paths:
            print(f"Checking for .env file at: {env_path}")
            if env_path.exists():
                print(f"Found .env file at: {env_path}")
                load_dotenv(str(env_path))
                env_loaded = True
                self.logger.info(f"Loaded environment variables from: {env_path}")
                break
            else:
                print(f"No .env file found at: {env_path}")
        
        print("=== END ENV FILE DEBUGGING INFO ===")
        
        if not env_loaded:
            self.logger.warning("No .env file found in any of the following locations:")
            for path in possible_env_paths:
                self.logger.warning(f"  - {path}")
            self.logger.warning("Using default configuration values")
        
        # Set base directory for relative paths
        self.base_dir = rag_dir
        
        # Folders configuration
        self.input_folder = self._resolve_path(os.getenv("INPUT_FOLDER", "data/input"))
        self.output_folder = self._resolve_path(os.getenv("OUTPUT_FOLDER", "data/output"))
        self.temp_folder = self._resolve_path(os.getenv("TEMP_FOLDER", "data/temp"))
        self.local_file_path = self._resolve_path(os.getenv("LOCAL_FILE_PATH", "data/input/localfile"))
        self.google_drive_file_path = self._resolve_path(os.getenv("GOOGLE_DRIVE_FILE_PATH", "data/input/googlefile"))
        self.log_folder = self._resolve_path(os.getenv("LOG_FOLDER", "logs"))
        
        # SQL Database configuration
        self.sql_connection_string = os.getenv("SQL_CONNECTION_STRING", "")
        
        # Google Drive configuration
        self.google_credentials_path = self._resolve_path(os.getenv("GOOGLE_CREDENTIALS_PATH", "auth/service_account.json"))
        self.google_drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
        
        # Run configuration
        self.config_dir = self._resolve_path(os.getenv("CONFIG_DIR", "config"))
        self.output_filename = os.getenv("OUTPUT_FILENAME", "extracted_data.json")
        self.incremental = os.getenv("INCREMENTAL", "true").lower() == "true"
        self.deduplicate = os.getenv("DEDUPLICATE", "true").lower() == "true"
        
        # Logging configuration
        log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_level = getattr(logging, log_level_name, logging.INFO)
        
        # Print configuration summary
        self.logger.info("Using configuration:")
        self.logger.info(f"  - Base directory: {self.base_dir}")
        self.logger.info(f"  - Input folder: {self.input_folder}")
        self.logger.info(f"  - Output folder: {self.output_folder}")
        self.logger.info(f"  - Log folder: {self.log_folder}")
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _resolve_path(self, path_str: str) -> str:
        """
        Resolve a path that might be relative to the base directory.
        
        Args:
            path_str: Path string from configuration
            
        Returns:
            str: Resolved absolute path
        """
        path = Path(path_str)
        
        # If it's already an absolute path, return it as is
        if path.is_absolute():
            return str(path)
        
        # Otherwise, resolve it relative to the base directory
        return str(self.base_dir / path)
    
    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.input_folder, self.output_folder, self.temp_folder, 
                         self.config_dir, Path(self.local_file_path).parent, self.log_folder]:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {directory}")
            except Exception as e:
                self.logger.warning(f"Could not create directory {directory}: {e}")