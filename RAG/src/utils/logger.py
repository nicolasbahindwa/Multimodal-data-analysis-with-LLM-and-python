# src/utils/logger.py
import logging
import sys
from pathlib import Path
from typing import Optional, Union

from ..config.settings import settings

class PipelineLogger:
    """Custom logger for the data processing pipeline."""
    
    def __init__(
        self, 
        name: str, 
        log_level: Optional[str] = None,
        log_file: Optional[Union[str, Path]] = None
    ):
        """
        Initialize a logger instance.
        
        Args:
            name: The name of the logger.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            log_file: Path to the log file.
        """
        self.logger = logging.getLogger(name)
        
        # Set log level - strip any comments that might be in the environment variable
        log_level = log_level or settings.LOG_LEVEL  # Changed from loglevel to LOG_LEVEL
        if log_level:
            # Extract just the level name (strip any comments)
            log_level = log_level.split('#')[0].strip()
            
        self.logger.setLevel(getattr(logging, log_level))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler if log file is specified
        log_file = log_file or settings.get('LOG_FILE')  # Use get method with proper capitalization
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log an exception message."""
        self.logger.exception(message, *args, **kwargs)

# Create a default logger instance
logger = PipelineLogger("data_pipeline")