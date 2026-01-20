
import pandas as pd
import logging
from typing import List, Dict
import sys
from pathlib import Path

# Add the backend directory to the Python path for progress service
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.services.progress_service import progress_service
except ImportError:
    progress_service = None

logger = logging.getLogger(__name__)

def ingest_excel(
    file_path: str,
    file_id: str,
    progress_callback=None
) -> List[Dict]:
    """
    Ingest Excel / CSV file.
    Converts each row into a text representation for RAG.
    """
    chunks = []
    file_path_obj = Path(file_path)
    suffix = file_path_obj.suffix.lower()

    if progress_callback:
        progress_callback(1, f"Reading {suffix} file...", 10)

    try:
        # Load Data
        if suffix in ['.xlsx', '.xls']:
            dfs = pd.read_excel(file_path, sheet_name=None) # Read all sheets
        elif suffix == '.csv':
            df = pd.read_csv(file_path)
            dfs = {"Sheet1": df}
        else:
            raise ValueError(f"Unsupported Excel format: {suffix}")

        total_sheets = len(dfs)
        current_sheet_idx = 0

        for sheet_name, df in dfs.items():
            current_sheet_idx += 1
            
            # Clean data: drop empty rows/cols, fill NaN
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df = df.fillna("")

            # Convert to string to ensure consistent formatting
            df = df.astype(str)

            rows = df.to_dict('records')
            total_rows = len(rows)
            
            if total_rows == 0:
                continue

            logger.info(f"Processing sheet '{sheet_name}' with {total_rows} rows")

            # Create text chunks from rows
            # Strategy: Group a few rows into a chunk, or 1 row per chunk if large?
            # Better: "Row X: ColA=ValA, ColB=ValB..."
            
            current_chunk_text = []
            current_char_count = 0
            MAX_CHUNK_SIZE = 1500 # Characters
            
            header_str = f"Sheet: {sheet_name}\nColumns: {', '.join(map(str, df.columns))}\n"
            current_chunk_text.append(header_str)
            current_char_count += len(header_str)

            for i, row in enumerate(rows):
                # Format row
                row_parts = []
                for col, val in row.items():
                    if val and val.strip():
                        row_parts.append(f"{col}: {val}")
                
                if not row_parts:
                    continue

                row_str = f"Row {i+2}: " + " | ".join(row_parts) + "\n"
                
                # Check strict size limit
                if current_char_count + len(row_str) > MAX_CHUNK_SIZE and len(current_chunk_text) > 1:
                    # Finalize current chunk
                    full_text = "".join(current_chunk_text)
                    chunks.append({
                        "file_id": file_id,
                        "text": full_text,
                        "page": 1, # Use 1 as proxy for 'sheet data'
                        "chunk_id": len(chunks)
                    })
                    
                    # Start new chunk with context
                    current_chunk_text = [header_str, row_str]
                    current_char_count = len(header_str) + len(row_str)
                else:
                    current_chunk_text.append(row_str)
                    current_char_count += len(row_str)
                
                # Progress
                if progress_callback and i % 50 == 0:
                    percent = 10 + int((current_sheet_idx / total_sheets) * 80 * (i / total_rows))
                    progress_callback(1, f"Processing {sheet_name}: Row {i}/{total_rows}", percent)

            # Final flush
            if current_chunk_text:
                full_text = "".join(current_chunk_text)
                chunks.append({
                    "file_id": file_id,
                    "text": full_text,
                    "page": 1,
                    "chunk_id": len(chunks)
                })

        logger.info(f"Excel ingestion complete. Created {len(chunks)} chunks.")
        
        if progress_callback:
            progress_callback(1, "Excel processing passed", 100)

        return chunks

    except Exception as e:
        logger.error(f"Error ingesting Excel: {e}")
        raise e
