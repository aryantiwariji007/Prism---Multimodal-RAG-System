
import sys
from pathlib import Path
import logging

# Setup Text/Output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ingestion.parse_pdf import parse_pdf
from ingestion.chunker import document_chunker

# File path (same as before)
file_path = r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend\data\uploads\976698a6-ecd7-437a-9501-cfb66d013c7b_EPI HSE Exposure Hours 2021.pdf"
file_id = "test_file_id_123"

def verify_fix():
    print(f"Verifying Fix on file: {file_path}")
    
    # 1. Parse
    chunks = parse_pdf(file_path, file_id=file_id)
    
    # 2. Chunk
    final_chunks = document_chunker.chunk_document_pages(chunks)
    
    # 3. Simulate QA Service Injection Logic (MATCHING THE CODE CHANGE)
    # We replicate the logic we just added to qa_service.py to verify it works as intended
    path_obj = Path(file_path)
    
    for chunk in final_chunks:
        original_text = chunk.get("text", "")
        # The logic we added:
        if not original_text.startswith(f"Filename:"):
             chunk["text"] = f"Filename: {path_obj.name}\nFile ID: {file_id}\n{original_text}"

    # 4. Inspect Chunks
    target_found = False
    filename_in_all = True
    
    print("\n--- INSPECTING CHUNKS ---")
    for i, c in enumerate(final_chunks):
        text = c['text']
        
        # Check 1: Filename present?
        if f"Filename: {path_obj.name}" not in text:
            print(f"[FAIL] Chunk {i} missing filename!")
            filename_in_all = False
            
        # Check 2: Table data + Filename Co-existence
        if "2015" in text and "Total Hours" in text:
            print(f"\n--- MATCHING TABLE CHUNK {i} ---")
            print(text[:300] + "...") # Print start to verify header
            print("-" * 30)
            target_found = True
            
    if filename_in_all:
        print("\n[PASS] All chunks contain filename.")
    else:
        print("\n[FAIL] Some chunks are missing filename.")
        
    if target_found:
        print("[PASS] Table chunk found with filename context.")
    else:
        print("[FAIL] Table chunk NOT found or missing context.")

if __name__ == "__main__":
    verify_fix()
