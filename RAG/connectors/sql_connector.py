"""
SQL Connector module.
Connects to SQL databases and processes tables incrementally.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Tuple

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .connector_base import ConnectorBase, TableMetadata
from settings.logger import get_logger

try:
    import sqlalchemy
    from sqlalchemy import create_engine, MetaData, Table, select, inspect
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    # Log the error during initialization
    pass


class SQLConnector(ConnectorBase):
    """Connector for processing SQL database tables."""
    
    def __init__(self, config):
        """
        Initialize the SQL connector.
        
        Args:
            config: Configuration object with sql_connection_string attribute
        """
        super().__init__(config)
        self.connection_string = config.sql_connection_string
        self.state_file = Path(config.config_dir) / "sql_connector_state.json"
        self.engine = None
        self.connection = None
        self.metadata = None
        self.inspector = None
        self._state = {}
        
        # Initialize logger
        self.logger = get_logger(
            name=self.__class__.__name__,
            log_dir=config.log_folder,
            log_level=config.log_level
        )
        
        self.logger.info(f"Initialized {self.__class__.__name__}")
        
        # Check if required libraries are installed
        try:
            import sqlalchemy
        except ImportError as e:
            self.logger.error(f"Required SQL libraries not installed: {e}")
            self.logger.error("Please install them using: pip install sqlalchemy")
            if "postgresql" in self.connection_string:
                self.logger.error("For PostgreSQL, also install: pip install psycopg2-binary")
            elif "mysql" in self.connection_string:
                self.logger.error("For MySQL, also install: pip install pymysql")
        
        self._load_state()
    
    def connect(self) -> bool:
        """
        Connect to the SQL database.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not self.connection_string:
            self.logger.error("Error: SQL connection string is not provided")
            return False
        
        self.logger.info(f"Connecting to SQL database: {self._mask_connection_string()}")
        
        try:
            # Check if required libraries are available
            try:
                import sqlalchemy
                from sqlalchemy import create_engine
            except ImportError as e:
                self.logger.error(f"Required libraries not installed: {e}")
                return False
            
            # Create engine and connect
            try:
                self.engine = create_engine(self.connection_string)
                self.connection = self.engine.connect()
                self.logger.info("Successfully connected to SQL database")
            except SQLAlchemyError as e:
                self.logger.error(f"Error connecting to database: {e}")
                return False
            
            # Reflect metadata and create inspector
            try:
                self.metadata = MetaData()
                self.metadata.reflect(bind=self.engine)
                self.inspector = inspect(self.engine)
                self.logger.info(f"Successfully reflected metadata")
                return True
            except SQLAlchemyError as e:
                self.logger.error(f"Error reflecting database metadata: {e}")
                if self.connection:
                    self.connection.close()
                if self.engine:
                    self.engine.dispose()
                self.connection = None
                self.engine = None
                return False
            
        except Exception as e:
            self.logger.exception(f"Unexpected error connecting to SQL database: {e}")
            return False
    
    def _mask_connection_string(self) -> str:
        """
        Mask sensitive information in connection string for logging.
        
        Returns:
            str: Masked connection string
        """
        if not self.connection_string:
            return ""
        
        try:
            # Simple masking for common connection string formats
            import re
            
            # Handle username:password@ pattern
            masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', self.connection_string)
            
            # Handle other potential password parameters
            masked = re.sub(r'password=([^&;]+)', r'password=***', masked)
            masked = re.sub(r'pwd=([^&;]+)', r'pwd=***', masked)
            
            return masked
        except Exception:
            # If anything goes wrong, return a generic string
            return "[Connection string available but hidden for security]"
    
    def scan(self) -> List[TableMetadata]:
        """
        Scan SQL database for tables to process.
        
        Returns:
            List[TableMetadata]: List of metadata for tables to process
        """
        self.logger.info("Starting scan of SQL database")
        
        if not self.connection and not self.connect():
            self.logger.warning("Scan aborted: Could not connect to SQL database")
            return []
        
        tables_metadata = []
        
        try:
            # Get all schemas in the database
            schemas = self.inspector.get_schema_names()
            self.logger.info(f"Found {len(schemas)} schemas")
            
            for schema in schemas:
                # Skip system schemas
                if schema.lower() in ('information_schema', 'pg_catalog', 'sys'):
                    self.logger.debug(f"Skipping system schema: {schema}")
                    continue
                
                # Get all tables in the schema
                try:
                    table_names = self.inspector.get_table_names(schema=schema)
                    self.logger.info(f"Found {len(table_names)} tables in schema '{schema}'")
                except SQLAlchemyError as e:
                    self.logger.error(f"Error getting tables for schema '{schema}': {e}")
                    continue
                
                for table_name in table_names:
                    table_id = f"{schema}.{table_name}"
                    self.logger.debug(f"Processing table: {table_id}")
                    
                    try:
                        # Get columns
                        columns = [col['name'] for col in self.inspector.get_columns(table_name, schema=schema)]
                        
                        # Get primary key
                        pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
                        pk_columns = pk_constraint.get('constrained_columns', []) if pk_constraint else []
                        
                        # Get row count (approximate)
                        row_count = self._get_row_count(schema, table_name)
                        
                        # Get last processed key from state
                        last_processed_key = self._state.get(table_id, {}).get('last_processed_key')
                        
                        # Create table metadata
                        metadata = TableMetadata(
                            id=table_id,
                            name=table_name,
                            schema=schema,
                            source=self.name,
                            last_processed_key=last_processed_key,
                            columns=columns,
                            row_count=row_count,
                            additional_metadata={
                                'primary_key_columns': pk_columns
                            }
                        )
                        
                        tables_metadata.append(metadata)
                    except SQLAlchemyError as e:
                        self.logger.error(f"Error processing table '{table_id}': {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error processing table '{table_id}': {e}")
            
            self.logger.info(f"Found {len(tables_metadata)} tables to process")
            return tables_metadata
        
        except SQLAlchemyError as e:
            self.logger.error(f"SQL error scanning database: {e}")
            return []
        except Exception as e:
            self.logger.exception(f"Unexpected error scanning SQL database: {e}")
            return []
    
    def get_new_rows(self, table_metadata: TableMetadata, batch_size: int = 1000) -> Tuple[List[Dict], Any]:
        """
        Get new rows from a table that haven't been processed yet.
        
        Args:
            table_metadata: Table metadata
            batch_size: Maximum number of rows to return
            
        Returns:
            Tuple[List[Dict], Any]: List of rows as dictionaries and the latest key value
        """
        schema = table_metadata.schema
        table_name = table_metadata.name
        table_id = f"{schema}.{table_name}"
        last_processed_key = table_metadata.last_processed_key
        
        self.logger.info(f"Fetching new rows from table: {table_id}")
        self.logger.debug(f"Last processed key: {last_processed_key}")
        
        if not self.connection and not self.connect():
            self.logger.warning(f"Could not fetch rows: Failed to connect to database")
            return [], None
        
        try:
            # Get the table object
            try:
                table = Table(table_name, self.metadata, schema=schema, autoload_with=self.engine)
            except SQLAlchemyError as e:
                self.logger.error(f"Error loading table '{table_id}': {e}")
                return [], None
            
            # Determine primary key or incremental column
            pk_columns = table_metadata.additional_metadata.get('primary_key_columns', [])
            
            if not pk_columns:
                self.logger.debug(f"No primary key columns specified for {table_id}, looking for suitable columns")
                # Try to find a suitable incremental column (timestamp or auto-increment)
                timestamp_cols = [col.name for col in table.columns 
                                 if 'timestamp' in str(col.type).lower() or 
                                    'datetime' in str(col.type).lower() or
                                    'date' in str(col.type).lower()]
                
                if timestamp_cols:
                    incremental_col = table.columns[timestamp_cols[0]]
                    self.logger.info(f"Using timestamp column '{incremental_col.name}' for incremental processing")
                else:
                    # Try to find an auto-increment column
                    for col in table.columns:
                        if col.autoincrement:
                            incremental_col = col
                            self.logger.info(f"Using auto-increment column '{incremental_col.name}' for incremental processing")
                            break
                    else:
                        # No suitable column found
                        self.logger.warning(f"No primary key or incremental column found for {table_id}")
                        return [], None
            else:
                incremental_col = table.columns[pk_columns[0]]
                self.logger.info(f"Using primary key column '{incremental_col.name}' for incremental processing")
            
            # Build query
            query = select(table)
            
            if last_processed_key is not None:
                self.logger.debug(f"Filtering for rows with {incremental_col.name} > {last_processed_key}")
                query = query.where(incremental_col > last_processed_key)
            
            # Order by the incremental column and limit results
            query = query.order_by(incremental_col).limit(batch_size)
            
            # Execute query
            try:
                result = self.connection.execute(query)
                rows = [dict(row) for row in result]
                self.logger.info(f"Fetched {len(rows)} rows from {table_id}")
            except SQLAlchemyError as e:
                self.logger.error(f"Error executing query on '{table_id}': {e}")
                return [], None
            
            # Get the latest key value
            latest_key = None
            if rows:
                latest_key = rows[-1][incremental_col.name]
                self.logger.debug(f"Latest key value: {latest_key}")
            
            return rows, latest_key
        
        except SQLAlchemyError as e:
            self.logger.error(f"SQL error retrieving rows from {table_id}: {e}")
            return [], None
        except Exception as e:
            self.logger.exception(f"Unexpected error retrieving rows from {table_id}: {e}")
            return [], None
    
    def _get_row_count(self, schema: str, table_name: str) -> Optional[int]:
        """
        Get approximate row count for a table.
        
        Args:
            schema: Schema name
            table_name: Table name
            
        Returns:
            Optional[int]: Approximate row count or None if not available
        """
        table_id = f"{schema}.{table_name}"
        self.logger.debug(f"Getting row count for table: {table_id}")
        
        try:
            # Try PostgreSQL specific approach first (fast for large tables)
            try:
                query = f"SELECT reltuples::bigint AS approximate_row_count FROM pg_class WHERE relname = '{table_name}'"
                result = self.connection.execute(sqlalchemy.text(query))
                row = result.fetchone()
                if row and row[0]:
                    count = int(row[0])
                    self.logger.debug(f"Got approximate row count for {table_id} from pg_class: {count}")
                    return count
            except SQLAlchemyError:
                self.logger.debug("Postgres-specific row count query failed, trying standard COUNT(*)")
            
            # Fallback to actual count if the above doesn't work
            # Note: This can be slow for large tables
            try:
                query = f"SELECT COUNT(*) FROM {schema}.{table_name}"
                result = self.connection.execute(sqlalchemy.text(query))
                row = result.fetchone()
                if row:
                    count = int(row[0])
                    self.logger.debug(f"Got row count for {table_id} using COUNT(*): {count}")
                    return count
            except SQLAlchemyError as e:
                self.logger.warning(f"Error getting row count with COUNT(*) for {table_id}: {e}")
            
            self.logger.warning(f"Could not determine row count for {table_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error getting row count for {table_id}: {e}")
            return None
    
    def get_processed_items(self) -> Set[str]:
        """
        Get the set of already processed table identifiers.
        
        Returns:
            Set[str]: Set of processed table identifiers
        """
        return set(self._state.keys())
    
    def mark_as_processed(self, item_id: str, last_key: Any = None) -> None:
        """
        Mark a table as processed with the latest processed key.
        
        Args:
            item_id: Table identifier (schema.table_name)
            last_key: Latest processed key value
        """
        self.logger.info(f"Marking item as processed: {item_id}")
        if last_key is not None:
            self.logger.debug(f"Setting last processed key to: {last_key}")
        
        if item_id not in self._state:
            self._state[item_id] = {}
        
        if last_key is not None:
            # Convert datetime to ISO format string for serialization
            if isinstance(last_key, datetime):
                last_key = last_key.isoformat()
            
            self._state[item_id]['last_processed_key'] = last_key
        
        # Update last processed timestamp
        self._state[item_id]['last_processed_time'] = datetime.now().isoformat()
        
        self._save_state()
    
    def _load_state(self) -> None:
        """Load connector state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    self._state = json.load(f)
                self.logger.info(f"Loaded state for {len(self._state)} tables from {self.state_file}")
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in state file: {self.state_file}")
                self._state = {}
            except Exception as e:
                self.logger.error(f"Error loading SQL connector state: {e}")
                self._state = {}
        else:
            self.logger.info(f"State file not found: {self.state_file}")
            self._state = {}
    
    def _save_state(self) -> None:
        """Save connector state to disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
            self.logger.info(f"Saved state for {len(self._state)} tables to {self.state_file}")
        except PermissionError:
            self.logger.error(f"Permission denied: Cannot write to {self.state_file}")
        except Exception as e:
            self.logger.error(f"Error saving SQL connector state: {e}")
    
    def close(self) -> None:
        """Close the connector and release resources."""
        self.logger.info(f"Closing {self.__class__.__name__}")
        self._save_state()
        
        if self.connection:
            try:
                self.connection.close()
                self.logger.debug("Closed database connection")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
        
        if self.engine:
            try:
                self.engine.dispose()
                self.logger.debug("Disposed database engine")
            except Exception as e:
                self.logger.error(f"Error disposing engine: {e}")