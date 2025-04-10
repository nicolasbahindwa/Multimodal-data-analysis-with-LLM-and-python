import sqlalchemy
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

class SQLDatabaseConnector:
    """
    This class is used as a connector for the SQL database
    """
    
    def __init__(self, connection_string: str):
        self.engine = sqlalchemy.create_engine(connection_string)
        self.metadata = {}
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database
        """
        inspector = sqlalchemy.inspect(self.engine)
        return inspector.get_table_names()
    
    def _table_has_timestamp_column(self, table_name: str) -> bool:
        """Check if the table has a timestamp column for incremental loading."""
        timestamp_columns = ['updated_at', 'modified_at', 'last_modified', 
                           'update_time', 'modification_date', 'modified_on']
        
        inspector = sqlalchemy.inspect(self.engine)
        table_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        return any(ts_col in table_columns for ts_col in timestamp_columns)
    
    def _get_timestamp_column(self, table_name: str) -> str:
        """Get the name of a suitable timestamp column for incremental loading."""
        timestamp_columns = ['updated_at', 'modified_at', 'last_modified', 
                           'update_time', 'modification_date', 'modified_on']
        
        inspector = sqlalchemy.inspect(self.engine)
        table_columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        for ts_col in timestamp_columns:
            if ts_col in table_columns:
                return ts_col
        
        raise ValueError(f"No suitable timestamp column found in table '{table_name}'")
    
    def extract_table_data(self, table_name: str, last_run_time: str = None, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """Extract data from a specific table in batches."""
        query = f"SELECT * FROM {table_name}"
        
        # Add incremental processing filter if last run time is provided
        if last_run_time and self._table_has_timestamp_column(table_name):
            timestamp_col = self._get_timestamp_column(table_name)
            query += f" WHERE {timestamp_col} > '{last_run_time}'"
            
        documents = []
        offset = 0
        
        while True:
            batch_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
            df = pd.read_sql(batch_query, self.engine)
            
            if df.empty:
                break
            
            for _, row in df.iterrows():
                doc = {
                    "content": self._row_to_text(row),
                    "metadata": {
                        "source": "sql_database",
                        "table": table_name,
                        "id": row.get("id", f"{table_name}_{offset}"),
                        "extracted_at": datetime.now().isoformat(),
                        "field_names": list(row.index)
                    }
                }
                documents.append(doc)
            
            offset += batch_size
            if len(df) < batch_size:
                break
        return documents
    
    def _row_to_text(self, row) -> str:
        """Convert a dataframe row to text format."""
        text_parts = []
        for col, value in row.items():
            text_parts.append(f"{col}: {value}")
        return "\n".join(text_parts)