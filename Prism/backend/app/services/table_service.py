import duckdb
import pandas as pd
import uuid
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class TableService:
    def __init__(self, db_path="data/tabular.duckdb"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        """Get a connection to DuckDB"""
        # DuckDB connections are cheap, but in a real app might want a pool or persistent singleton
        # For this architecture, connecting on demand used to be standard, 
        # but concurrent writes in DuckDB need care.
        # We'll use a standard connection.
        return duckdb.connect(str(self.db_path))

    def _init_db(self):
        """Initialize the metadata table for tracking stored tables"""
        con = self._get_connection()
        try:
            con.execute("""
                CREATE TABLE IF NOT EXISTS table_metadata (
                    table_id VARCHAR PRIMARY KEY,
                    file_id VARCHAR,
                    source_file VARCHAR,
                    page_number INTEGER,
                    columns_json VARCHAR,
                    summary VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        finally:
            con.close()

    def _sanitize_column_name(self, col_name: str) -> str:
        """Sanitize column name for SQL safety"""
        # Replace non-alphanumeric with _
        clean = re.sub(r'[^a-zA-Z0-9]', '_', str(col_name))
        # Ensure it doesn't start with a number
        if clean and clean[0].isdigit():
            clean = f"_{clean}"
        # Ensure it's not empty
        if not clean:
            clean = "col"
        return clean

    def add_table(self, df: pd.DataFrame, file_id: str, source_file: str, page: int, summary: str = "") -> str:
        """
        Store a dataframe as a dedicated DuckDB table.
        Returns the table_id.
        """
        table_id = str(uuid.uuid4())
        
        # 1. Sanitize Headers
        clean_cols = []
        seen = set()
        for c in df.columns:
            clean = self._sanitize_column_name(c)
            # Deduplicate
            original_clean = clean
            dup_count = 1
            while clean in seen:
                clean = f"{original_clean}_{dup_count}"
                dup_count += 1
            seen.add(clean)
            clean_cols.append(clean)
        
        # Create a copy to avoid mutating original df passed by reference
        df_clean = df.copy()
        df_clean.columns = clean_cols
        
        # 2. Store Metadata
        columns_json = json.dumps(clean_cols)
        
        # 3. DuckDB Interaction
        con = self._get_connection()
        try:
            # Insert Metadata
            con.execute(
                "INSERT INTO table_metadata (table_id, file_id, source_file, page_number, columns_json, summary) VALUES (?, ?, ?, ?, ?, ?)",
                [table_id, file_id, source_file, page, columns_json, summary]
            )
            
            # Store Data
            # DuckDB is great at ingesting pandas dataframes
            table_name = f"tab_{table_id.replace('-', '_')}"
            
            # Register the dataframe as a view/temp table for this connection context
            con.register('temp_ingest_df', df_clean)
            
            # Create persistent table from the view
            # DuckDB infers types automatically
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_ingest_df")
            
            # Cleanup registry
            con.unregister('temp_ingest_df')
            
        except Exception as e:
            logger.error(f"Failed to store table in DuckDB: {e}")
            raise e
        finally:
            con.close()
            
        logger.info(f"Stored table {table_id} for file {file_id} (Page {page}) in DuckDB")
        return table_id

    def get_table_metadata(self, table_id: str) -> Optional[Dict]:
        """Get metadata for a specific table"""
        con = self._get_connection()
        try:
            result = con.execute("SELECT * FROM table_metadata WHERE table_id = ?", [table_id]).fetchone()
            if result:
                # DuckDB fetchone returns tuple, need to map to columns manually or use specific fetch
                # Metadata columns: table_id, file_id, source_file, page_number, columns_json, summary, created_at
                d = {
                    "table_id": result[0],
                    "file_id": result[1],
                    "source_file": result[2],
                    "page_number": result[3],
                    "columns_json": result[4],
                    "summary": result[5],
                    "created_at": result[6],
                    "table_name": f"tab_{result[0].replace('-', '_')}"
                }
                
                if d.get("columns_json"):
                    d["columns"] = json.loads(d["columns_json"])
                return d
        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
        finally:
            con.close()
        return None

    def execute_sql(self, table_id: str, sql_query: str) -> Dict:
        """
        Execute a SELECT query against the table.
        """
        table_name = f"tab_{table_id.replace('-', '_')}"
        
        # Security Guardrails
        if not sql_query.strip().lower().startswith("select"):
             return {"success": False, "error": "Only SELECT queries are allowed for safety."}
        
        if ";" in sql_query:
             # Basic injection prevention
             return {"success": False, "error": "Multiple statements not allowed."}

        # Check if table exists (optional, but good practice)
        
        con = self._get_connection()
        try:
            # DuckDB execution returns a relation object or cursor. 
            # We can convert directly to df
            df = con.sql(sql_query).df()
            
            # Limit rows to prevent massive context overflow
            if len(df) > 100:
                df = df.head(100)
                truncated = True
            else:
                truncated = False
                
            result = {
                "success": True,
                "columns": list(df.columns),
                "data": df.values.tolist(),
                "truncated": truncated,
                "row_count": len(df)
            }
            
            # Convert to csv string for easy LLM consumption
            result["csv_string"] = df.to_csv(index=False)
            return result
            
        except Exception as e:
            logger.error(f"DuckDB SQL execution failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            con.close()

    def get_all_tables_for_file(self, file_id: str) -> List[Dict]:
        con = self._get_connection()
        try:
            rows = con.execute("SELECT * FROM table_metadata WHERE file_id = ?", [file_id]).fetchall()
            results = []
            for result in rows:
                d = {
                    "table_id": result[0],
                    "file_id": result[1],
                    "source_file": result[2],
                    "page_number": result[3],
                    "columns_json": result[4],
                    "summary": result[5],
                    "created_at": result[6]
                }
                results.append(d)
            return results
        finally:
            con.close()

# Global Instance
table_service = TableService()
