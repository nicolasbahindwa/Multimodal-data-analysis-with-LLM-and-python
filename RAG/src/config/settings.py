# """
# Configuration settings for the data processing pipeline.
# Loads and manages environment variables and configuration settings.
# """

# import os
# import logging
# from typing import Dict, Any, Optional
# from pathlib import Path
# from dotenv import load_dotenv


# # Base directories
# PROJECT_ROOT = Path(__file__).parents[2].resolve()
# SRC_DIR = PROJECT_ROOT / "src"
# DATA_DIR = PROJECT_ROOT / "data"
# RAW_DATA_DIR = DATA_DIR / "raw"
# PROCESSED_DATA_DIR = DATA_DIR / "processed"
# CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
# LOGS_DIR = PROJECT_ROOT / "logs"

# # Ensure directories exist
# for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, CREDENTIALS_DIR, LOGS_DIR]:
#     directory.mkdir(exist_ok=True, parents=True)

# # Load environment variables
# load_dotenv(PROJECT_ROOT / ".env")


# class Settings:
#     """
#     Handles application settings and environment variables.
#     Provides access to configuration across the application.
#     """

#     def __init__(self):
#         # Default settings that can be overridden
#         self.default_settings = {
#             # Chunking settings
#             "CHUNK_SIZE": 1000,
#             "CHUNK_OVERLAP": 200,
            
#             # Embedding settings
#             "EMBEDDING_MODEL": "sentence-transformers/all-mpnet-base-v2",
#             "EMBEDDING_DIMENSION": 768,
            
#             # Processing settings
#             "MAX_WORKERS": 4,
#             "BATCH_SIZE": 10,
            
#             # File handling settings
#             "MAX_FILE_SIZE_MB": 100,
#             "SUPPORTED_EXTENSIONS": [
#                 ".txt", ".pdf", ".docx", ".doc", ".json", 
#                 ".csv", ".xlsx", ".md", ".html", ".xml", 
#                 ".pptx", ".rtf", ".log"
#             ],
#         }
        
#         # Connector configurations
#         self.connector_configs = {
#             "local_file": {
#                 "base_path": str(RAW_DATA_DIR),
#                 "timeout": 30
#             },
#             "google_drive": {
#                 "timeout": 120,
#                 "cache_duration": 300,  # Cache duration in seconds
#                 "folder_id": "",  # Default root folder ID
#                 "credentials_path": str(CREDENTIALS_DIR / "google_service_account.json")
#             },
#             "sql_database": {
#                 "timeout": 60,
#                 "max_connections": 10,
#                 "pool_recycle": 3600,  # Connection recycle time in seconds
#                 "connection_timeout": 30,
#                 "execution_timeout": 120
#             }
#         }
        
#         # Load environment variables
#         self._load_environment_variables()
        
#         # Configure logging
#         self._configure_logging()
        
#     def _load_environment_variables(self):
#         """Load required environment variables with error checking."""
#         # Database settings
#         self.DB_HOST = os.getenv("DB_HOST")
#         self.DB_PORT = os.getenv("DB_PORT")
#         self.DB_NAME = os.getenv("DB_NAME")
#         self.DB_USER = os.getenv("DB_USER")
#         self.DB_PASSWORD = os.getenv("DB_PASSWORD")
#         self.DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")
        
#         # API keys and authentication
#         self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#         self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#         self.GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", 
#                                                    str(CREDENTIALS_DIR / "google_service_account.json"))
        
#         # General settings
#         self.ENV = os.getenv("ENV", "development")
#         self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
#         self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        
#         # Load connector configs from environment
#         for connector_name, config in self.connector_configs.items():
#             env_prefix = f"{connector_name.upper()}_"
#             for key in config:
#                 env_key = f"{env_prefix}{key.upper()}"
#                 env_value = os.getenv(env_key)
#                 if env_value is not None:
#                     config[key] = env_value
        
#         # Override default settings with environment variables if provided
#         for key, default_value in self.default_settings.items():
#             env_value = os.getenv(key)
#             if env_value is not None:
#                 # Convert to appropriate type based on default value
#                 if isinstance(default_value, int):
#                     setattr(self, key, int(env_value))
#                 elif isinstance(default_value, float):
#                     setattr(self, key, float(env_value))
#                 elif isinstance(default_value, bool):
#                     setattr(self, key, env_value.lower() in ("true", "1", "t"))
#                 elif isinstance(default_value, list):
#                     setattr(self, key, env_value.split(","))
#                 else:
#                     setattr(self, key, env_value)
#             else:
#                 setattr(self, key, default_value)
    
#     def _configure_logging(self):
#         """Configure logging based on environment settings."""
#         log_level_str = self.LOG_LEVEL.upper()
#         log_level = getattr(logging, log_level_str, logging.INFO)
        
#         # Create logs directory if it doesn't exist
#         os.makedirs(LOGS_DIR, exist_ok=True)
        
#         log_file = LOGS_DIR / f"pipeline_{self.ENV}.log"
        
#         logging.basicConfig(
#             level=log_level,
#             format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#             handlers=[
#                 logging.FileHandler(log_file),
#                 logging.StreamHandler()
#             ]
#         )
        
#         # Set specific loggers to different levels if needed
#         if self.DEBUG:
#             logging.getLogger("src").setLevel(logging.DEBUG)
        
#         # Suppress noisy loggers
#         logging.getLogger("urllib3").setLevel(logging.WARNING)
#         logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        
#     def get(self, key: str, default: Any = None) -> Any:
#         """Get a configuration value with a fallback default."""
#         return getattr(self, key, default)
    
#     def get_connector_config(self, connector_name: str) -> Dict[str, Any]:
#         """
#         Get configuration for a specific connector.
        
#         Args:
#             connector_name: Name of the connector to get configuration for.
            
#         Returns:
#             Dictionary containing connector configuration.
#         """
#         return self.connector_configs.get(connector_name, {})
    
#     def get_db_connection_string(self) -> Optional[str]:
#         """
#         Construct database connection string from components or return the predefined one.
#         """
#         if self.DB_CONNECTION_STRING:
#             return self.DB_CONNECTION_STRING
        
#         if all([self.DB_HOST, self.DB_PORT, self.DB_NAME, self.DB_USER, self.DB_PASSWORD]):
#             return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
#         return None
    
#     def to_dict(self) -> Dict[str, Any]:
#         """Convert settings to a dictionary, omitting private attributes."""
#         return {
#             key: value for key, value in self.__dict__.items()
#             if not key.startswith('_') and key != 'default_settings'
#         }


# # Create a singleton instance
# settings = Settings()


# # Exports
# __all__ = [
#     "settings", 
#     "PROJECT_ROOT", 
#     "SRC_DIR", 
#     "DATA_DIR", 
#     "RAW_DATA_DIR", 
#     "PROCESSED_DATA_DIR", 
#     "CREDENTIALS_DIR", 
#     "LOGS_DIR"
# ]


"""
Configuration settings for the data processing pipeline.
Loads and manages environment variables and configuration settings.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


# Base directories
PROJECT_ROOT = Path(__file__).parents[2].resolve()
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"

# Input and output directories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"
EXTRACT_DIR = DATA_DIR / "extracted"

# Connector-specific directories
LOCAL_FILE_PATH = RAW_DATA_DIR / "local"
LOCAL_PROCESSED_PATH = OUTPUT_DIR / "local_process_files"
GOOGLE_DRIVE_FILE_PATH = INPUT_DIR / "googlefile"
GOOGLE_DRIVE_PROCESSED_FILE_PATH = OUTPUT_DIR / "google_process_file"

# Authentication and credentials
CREDENTIALS_DIR = PROJECT_ROOT / "auth"
LOGS_DIR = PROJECT_ROOT / "logs"

# Embedding-specific directories
EMBEDDING_CACHE_DIR = PROCESSED_DATA_DIR / "embeddings_cache"

# Ensure directories exist
for directory in [
    DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, CREDENTIALS_DIR, LOGS_DIR,
    INPUT_DIR, OUTPUT_DIR, TEMP_DIR, EXTRACT_DIR, 
    LOCAL_FILE_PATH, LOCAL_PROCESSED_PATH,
    GOOGLE_DRIVE_FILE_PATH, GOOGLE_DRIVE_PROCESSED_FILE_PATH,
    EMBEDDING_CACHE_DIR
]:
    directory.mkdir(exist_ok=True, parents=True)

# Load environment variables
ENV_FILE = os.getenv("ENV_FILE", PROJECT_ROOT / ".env")
load_dotenv(ENV_FILE)


class Settings:
    """
    Handles application settings and environment variables.
    Provides access to configuration across the application.
    """

    def __init__(self):
        # Default settings that can be overridden
        self.default_settings = {
            # Chunking settings
            "CHUNK_SIZE": 1000,
            "CHUNK_OVERLAP": 200,
            
            # Embedding settings
            "EMBEDDING_MODEL": "sentence-transformers/all-mpnet-base-v2",
            "EMBEDDING_DIMENSION": 768,
            "USE_GPU": False,
            
            # Processing settings
            "MAX_WORKERS": 4,
            "BATCH_SIZE": 10,
            "MAX_FILE_SIZE_MB": 100,
            
            # Run configuration
            "INCREMENTAL": True,
            "DEDUPLICATE": True,
            "CLEAR_CACHE": False,
            "OUTPUT_FILENAME": "extracted_data.json",
            
            # File handling settings
            "SUPPORTED_EXTENSIONS": [
                ".txt", ".pdf", ".docx", ".doc", ".json", 
                ".csv", ".xlsx", ".md", ".html", ".xml", 
                ".pptx", ".rtf", ".log"
            ],
        }
        
        # Connector configurations
        self.connector_configs = {
            "local_file": {
                "base_path": str(LOCAL_FILE_PATH),
                "processed_path": str(LOCAL_PROCESSED_PATH),
                "timeout": 30
            },
            "google_drive": {
                "file_path": str(GOOGLE_DRIVE_FILE_PATH),
                "processed_file_path": str(GOOGLE_DRIVE_PROCESSED_FILE_PATH),
                "timeout": 120,
                "cache_duration": 300,  # Cache duration in seconds
                "folder_id": "",  # Default root folder ID
                "credentials_path": str(CREDENTIALS_DIR / "service_account.json")
            },
            "sql_database": {
                "timeout": 60,
                "max_connections": 10,
                "pool_recycle": 3600,  # Connection recycle time in seconds
                "connection_timeout": 30,
                "execution_timeout": 120
            }
        }
        
        # API Keys
        self.api_keys = {
            "openai": None,
            "anthropic": None,
            "tavily": None,
            "google": None
        }
        
        # Load environment variables
        self._load_environment_variables()
        
        # Configure logging
        self._configure_logging()

        # Initialize embedding settings
        self._initialize_embedding_settings()
        
    def _load_environment_variables(self):
        """Load required environment variables with error checking."""
        # Database settings
        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT")
        self.DB_NAME = os.getenv("DB_NAME")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD")
        self.DB_CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")
        
        # API keys and authentication
        self.api_keys["openai"] = os.getenv("OPENAI_API_KEY")
        self.api_keys["anthropic"] = os.getenv("ANTHROPIC_API_KEY")
        self.api_keys["tavily"] = os.getenv("TAVILY_API_KEY")
        self.api_keys["google"] = os.getenv("GOOGLE_API_KEY")
        
        self.GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", 
                                            str(CREDENTIALS_DIR / "service_account.json"))
        self.GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
        
        # General settings
        self.ENV = os.getenv("ENV", "development")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
        
        # Directory settings
        self.INPUT_FOLDER = os.getenv("INPUT_FOLDER", str(INPUT_DIR))
        self.OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", str(OUTPUT_DIR))
        self.TEMP_FOLDER = os.getenv("TEMP_FOLDER", str(TEMP_DIR))
        self.LOG_FOLDER = os.getenv("LOG_FOLDER", str(LOGS_DIR))
        
        # Load connector configs from environment
        for connector_name, config in self.connector_configs.items():
            env_prefix = f"{connector_name.upper()}_"
            for key in config:
                env_key = f"{env_prefix}{key.upper()}"
                env_value = os.getenv(env_key)
                if env_value is not None:
                    config[key] = env_value
        
        # Override default settings with environment variables if provided
        for key, default_value in self.default_settings.items():
            env_value = os.getenv(key)
            if env_value is not None:
                # Convert to appropriate type based on default value
                if isinstance(default_value, int):
                    # First check if it might be a boolean string
                    if env_value.lower() in ("true", "false", "t", "f", "yes", "no", "y", "n"):
                        # Treat it as a boolean instead
                        setattr(self, key, env_value.lower() in ("true", "t", "yes", "y", "1"))
                    else:
                        # Try integer conversion with fallback to default
                        try:
                            setattr(self, key, int(env_value))
                        except ValueError:
                            print(f"Warning: Failed to convert '{env_value}' to int for '{key}'. Using default: {default_value}")
                            setattr(self, key, default_value)
                elif isinstance(default_value, float):
                    try:
                        setattr(self, key, float(env_value))
                    except ValueError:
                        print(f"Warning: Failed to convert '{env_value}' to float for '{key}'. Using default: {default_value}")
                        setattr(self, key, default_value)
                elif isinstance(default_value, bool):
                    setattr(self, key, env_value.lower() in ("true", "1", "t", "yes", "y"))
                elif isinstance(default_value, list):
                    setattr(self, key, env_value.split(","))
                else:
                    setattr(self, key, env_value)
            else:
                setattr(self, key, default_value)
    
    def _configure_logging(self):
        """Configure logging based on environment settings."""
        log_level_str = self.LOG_LEVEL.upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        log_file = LOGS_DIR / f"pipeline_{self.ENV}.log"
        
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Set specific loggers to different levels if needed
        if self.DEBUG:
            logging.getLogger("src").setLevel(logging.DEBUG)
        
        # Suppress noisy loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    def _initialize_embedding_settings(self):
        """Initialize embedding-specific settings."""
        # Embedding models configuration
        self.DEFAULT_EMBEDDING_MODELS = {
            "huggingface": {
                "default": "sentence-transformers/all-mpnet-base-v2",  # Default HF model
                "small": "sentence-transformers/all-MiniLM-L6-v2",     # Smaller, faster model
                "large": "sentence-transformers/all-mpnet-base-v2",    # Larger, more accurate model
            },
            "openai": {
                "default": "text-embedding-3-small",                   # Default OpenAI model
                "small": "text-embedding-3-small",                     # Smaller, cost-effective model
                "large": "text-embedding-3-large",                     # Larger, most accurate model
            }
        }

        # Model dimension mapping (useful for verification and vector DB setup)
        self.EMBEDDING_DIMENSIONS = {
            # HuggingFace models
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/multi-qa-mpnet-base-dot-v1": 768,
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
            
            # OpenAI models
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536  # Legacy model
        }

        # Auto-detect embedding type based on model name
        if "text-embedding" in self.EMBEDDING_MODEL.lower():
            self.EMBEDDING_TYPE = "openai"
        else:
            self.EMBEDDING_TYPE = "huggingface"

        # Get expected dimension for the selected model
        self.EMBEDDING_DIMENSION = self.EMBEDDING_DIMENSIONS.get(
            self.EMBEDDING_MODEL, 
            getattr(self, "EMBEDDING_DIMENSION", 768)  # Fallback to setting or default value
        )
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with a fallback default."""
        return getattr(self, key, default)
    
    def get_connector_config(self, connector_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific connector.
        
        Args:
            connector_name: Name of the connector to get configuration for.
            
        Returns:
            Dictionary containing connector configuration.
        """
        return self.connector_configs.get(connector_name, {})
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a specific service.
        
        Args:
            service: Name of service (openai, anthropic, tavily, google)
            
        Returns:
            API key or None if not configured
        """
        return self.api_keys.get(service)
    
    def get_db_connection_string(self) -> Optional[str]:
        """
        Construct database connection string from components or return the predefined one.
        """
        if self.DB_CONNECTION_STRING:
            return self.DB_CONNECTION_STRING
        
        if all([self.DB_HOST, self.DB_PORT, self.DB_NAME, self.DB_USER, self.DB_PASSWORD]):
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
        return None
    
    def get_embedding_config(self, model_name=None, embedding_type=None):
        """
        Get configuration for embedding based on model name and type.
        
        Args:
            model_name: Name of embedding model. Defaults to settings value.
            embedding_type: Type of embedding provider. Auto-detected if not provided.
            
        Returns:
            Dictionary with embedding configuration.
        """
        # Use default values if not provided
        if not model_name:
            model_name = self.EMBEDDING_MODEL
            
        # Auto-detect embedding type if not specified
        if not embedding_type:
            if "text-embedding" in model_name.lower():
                embedding_type = "openai"
            else:
                embedding_type = "huggingface"
        
        # Get dimension for this model
        dimension = self.EMBEDDING_DIMENSIONS.get(model_name, self.EMBEDDING_DIMENSION)
        
        # Return config
        return {
            "model_name": model_name,
            "embedding_type": embedding_type,
            "dimension": dimension,
            "cache_dir": EMBEDDING_CACHE_DIR,
            "use_gpu": self.USE_GPU
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to a dictionary, omitting private attributes."""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') and key != 'default_settings'
        }


# Create a singleton instance
settings = Settings()


# Exports
__all__ = [
    "settings", 
    "PROJECT_ROOT", 
    "SRC_DIR", 
    "DATA_DIR", 
    "RAW_DATA_DIR", 
    "PROCESSED_DATA_DIR", 
    "INPUT_DIR",
    "OUTPUT_DIR",
    "TEMP_DIR",
    "EXTRACT_DIR",
    "LOCAL_FILE_PATH",
    "LOCAL_PROCESSED_PATH",
    "GOOGLE_DRIVE_FILE_PATH",
    "GOOGLE_DRIVE_PROCESSED_FILE_PATH",
    "CREDENTIALS_DIR", 
    "LOGS_DIR",
    "EMBEDDING_CACHE_DIR"
]