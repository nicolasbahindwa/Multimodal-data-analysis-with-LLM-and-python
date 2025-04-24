"""
Logging module for data connectors.
Sets up logging to both console and file.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """Logger class that handles logging to both console and file."""
    
    def __init__(self, name: str, log_dir: str = "logs", log_level: int = logging.INFO):
        """
        Initialize logger with the given name.
        
        Args:
            name: Name of the logger (usually module or class name)
            log_dir: Directory to store log files
            log_level: Logging level
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.logger = None
        
        # Create logger
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with handlers for console and file output."""
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        
        # Remove existing handlers if any
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # Create file handler - one log file per day
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{today}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)
    
    def exception(self, message: str):
        """Log exception message with traceback."""
        self.logger.exception(message)


def get_logger(name: str, log_dir: str = "logs", log_level: int = logging.INFO) -> Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name of the logger
        log_dir: Directory to store log files
        log_level: Logging level
        
    Returns:
        Logger: Logger instance
    """
    return Logger(name, log_dir, log_level)