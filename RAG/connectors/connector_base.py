"""
Base module for data connectors.
Defines common interfaces and data structures.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


class FileType(Enum):
    """Enum representing different file types."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "xlsx"
    PDF = "pdf"
    TEXT = "txt"
    OTHER = "other"
    
    @classmethod
    def from_extension(cls, extension: str) -> 'FileType':
        """Get file type from file extension."""
        extension = extension.lower().lstrip('.')
        for file_type in cls:
            if file_type.value == extension:
                return file_type
        return cls.OTHER


@dataclass
class FileMetadata:
    """Metadata for a file to be processed."""
    id: str  # Unique identifier for the file
    name: str  # File name
    path: str  # Original path or location identifier
    size: int  # File size in bytes
    type: FileType  # File type
    last_modified: datetime  # Last modification timestamp
    source: str  # Source connector identifier
    additional_metadata: Dict[str, Any] = field(default_factory=dict)  # Additional source-specific metadata
    checksum: Optional[str] = None  # File checksum for deduplication if available
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "size": self.size,
            "type": self.type.value,
            "last_modified": self.last_modified.isoformat(),
            "source": self.source,
            "additional_metadata": self.additional_metadata,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, metadata_dict: Dict[str, Any]) -> 'FileMetadata':
        """Create metadata from dictionary."""
        return cls(
            id=metadata_dict["id"],
            name=metadata_dict["name"],
            path=metadata_dict["path"],
            size=metadata_dict["size"],
            type=FileType(metadata_dict["type"]),
            last_modified=datetime.fromisoformat(metadata_dict["last_modified"]),
            source=metadata_dict["source"],
            additional_metadata=metadata_dict.get("additional_metadata", {}),
            checksum=metadata_dict.get("checksum")
        )


@dataclass
class TableMetadata:
    """Metadata for a database table to be processed."""
    id: str  # Unique identifier for the table
    name: str  # Table name
    schema: str  # Schema name
    source: str  # Source connector identifier
    last_processed_key: Optional[Any] = None  # Last processed primary key or timestamp
    columns: List[str] = field(default_factory=list)  # List of column names
    row_count: Optional[int] = None  # Total row count if available
    additional_metadata: Dict[str, Any] = field(default_factory=dict)  # Additional source-specific metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "schema": self.schema,
            "source": self.source,
            "last_processed_key": self.last_processed_key,
            "columns": self.columns,
            "row_count": self.row_count,
            "additional_metadata": self.additional_metadata
        }
    
    @classmethod
    def from_dict(cls, metadata_dict: Dict[str, Any]) -> 'TableMetadata':
        """Create metadata from dictionary."""
        return cls(
            id=metadata_dict["id"],
            name=metadata_dict["name"],
            schema=metadata_dict["schema"],
            source=metadata_dict["source"],
            last_processed_key=metadata_dict.get("last_processed_key"),
            columns=metadata_dict.get("columns", []),
            row_count=metadata_dict.get("row_count"),
            additional_metadata=metadata_dict.get("additional_metadata", {})
        )


class ConnectorBase(ABC):
    """Base class for all data connectors."""
    
    def __init__(self, config: Any):
        """
        Initialize the connector.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def scan(self) -> List[Any]:
        """
        Scan the data source for unprocessed items.
        
        Returns:
            List[Any]: List of metadata for unprocessed items
        """
        pass
    
    @abstractmethod
    def get_processed_items(self) -> Set[str]:
        """
        Get the set of already processed item identifiers.
        
        Returns:
            Set[str]: Set of processed item identifiers
        """
        pass
    
    @abstractmethod
    def mark_as_processed(self, item_id: str) -> None:
        """
        Mark an item as processed.
        
        Args:
            item_id: Identifier of the processed item
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the connector and release any resources."""
        pass