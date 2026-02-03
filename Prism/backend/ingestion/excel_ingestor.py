
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
            
            # 1. Clean data: drop empty rows/cols
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if df.empty:
                continue

            # 2. Heuristic Header Detection:
            # Check if headers look bad (mostly 'Unnamed' or 'Col_')
            header_str_preview = "".join([str(c) for c in df.columns])
            if "Unnamed" in header_str_preview or "Col_" in header_str_preview:
                best_header_row_idx = None
                best_header_score = 0
                
                # Scan first 5 rows to find a better header
                rows_to_scan = min(5, len(df))
                for i in range(rows_to_scan):
                    row = df.iloc[i]
                    # Score based on:
                    # - Ratio of non-null values
                    # - Ratio of string values (headers define meaning, usually strings)
                    non_null_count = row.count()
                    total_cols = len(row)
                    
                    if total_cols == 0: continue

                    # Check for meaningful strings
                    string_count = sum(1 for x in row if isinstance(x, str) and len(x.strip()) > 1)
                    
                    # Score: weighed towards having many strings and valid values
                    validity_ratio = non_null_count / total_cols
                    string_ratio = string_count / total_cols
                    
                    # Heuristic score
                    score = validity_ratio + (string_ratio * 1.5)
                    
                    if score > best_header_score and score > 1.0: # Threshold
                        best_header_score = score
                        best_header_row_idx = i
                
                if best_header_row_idx is not None:
                     # Promote row to header
                    new_header = df.iloc[best_header_row_idx].values
                    # Handle duplicate headers or empty ones
                    new_header = [str(h).strip() if pd.notna(h) and str(h).strip() != "" else f"Col_{j}" for j, h in enumerate(new_header)]
                    
                    # Deduplicate
                    seen = {}
                    final_header = []
                    for h in new_header:
                        if h in seen:
                            seen[h] += 1
                            final_header.append(f"{h}_{seen[h]}")
                        else:
                            seen[h] = 0
                            final_header.append(h)

                    df.columns = final_header
                    df = df.iloc[best_header_row_idx+1:].reset_index(drop=True)

            df = df.fillna("")
            df = df.astype(str)
            
            rows = df.to_dict('records')
            total_rows = len(rows)
            
            # --- AGGREGATE REPRESENTATION: Markdown Table (Excellent for RAG accuracy) ---
            # We add a full (or partial) markdown version of the sheet to help with 2D lookup
            # Only for reasonably sized tables (e.g. up to 100 rows)
            if total_rows < 150:
                md_table = df.to_markdown(index=False)
                table_chunk = f"### [Sheet: {sheet_name}]\nFull Table Representation:\n\n{md_table}"
                chunks.append({
                    "file_id": file_id,
                    "text": table_chunk,
                    "type": "table",
                    "page": 1,
                    "chunk_id": len(chunks),
                    "metadata": {"content_type": "markdown_table"}
                })

            # --- ROW-WISE REPRESENTATION ---
            current_chunk_text = []
            current_char_count = 0
            MAX_CHUNK_SIZE = 1500 
            
            header_str = f"Sheet: {sheet_name}\nColumns: {', '.join(map(str, df.columns))}\n"
            current_chunk_text.append(header_str)
            current_char_count += len(header_str)

            for i, row in enumerate(rows):
                # Format row
                row_parts = []
                for col, val in row.items():
                    # Paranoid Check: Force string conversion for everything
                    col_str = str(col).strip()
                    val_str = str(val).strip()
                    
                    if val_str:
                        row_parts.append(f"{col_str}: {val_str}")
                
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
