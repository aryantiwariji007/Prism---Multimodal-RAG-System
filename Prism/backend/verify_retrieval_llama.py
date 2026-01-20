
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from app.services.qa_service import qa_service
from app.services.folder_service import folder_service

def verify_retrieval():
    print("\n--- Verifying LlamaIndex Retrieval ---")
    
    # 1. Inspect a specific file mapping
    target_file_part = "bb29972f"
    files = folder_service.file_map
    target_file_id = None
    for fid, folder_id in files.items():
        if target_file_part in fid:
            target_file_id = fid
            print(f"Found target file: {fid} in folder: {folder_id}")
            break
            
    if not target_file_id:
        print("ERROR: Target file not found in folder map.")
        return

    # 2. Test Retrieval
    question = "what is section 2 of EPI Supplier Questionnaire"
    print(f"\nQuestion: {question}")
    
    # Test WITHOUT folder constraint first
    print("\n[Test 1] Global Search (No Folder)")
    res_global = qa_service._retrieve_pipeline(question, max_chunks=5)
    
    found_global = False
    for chunk in res_global['final_chunks']:
        if target_file_id in chunk.get('file_id', ''):
            found_global = True
            print(f"  SUCCESS: Found chunk from target file. Score: {chunk.get('score', 'N/A')}")
            break
            
    if not found_global:
        print("  FAILURE: Did not find target file in global top-k.")

    # Test WITH folder constraint
    # We find the folder ID for the file
    folder_id = folder_service.get_folder_for_file(target_file_id)
    print(f"\n[Test 2] Folder Scoped Search (Folder: {folder_id})")
    
    res_folder = qa_service._retrieve_pipeline(question, folder_id=folder_id, max_chunks=5)
    
    found_folder = False
    for chunk in res_folder['final_chunks']:
        if target_file_id in chunk.get('file_id', ''):
            found_folder = True
            print(f"  SUCCESS: Found chunk from target file. Score: {chunk.get('score', 'N/A')}")
            break
            
    if not found_folder:
        print("  FAILURE: Did not find target file in folder scope.")

if __name__ == "__main__":
    verify_retrieval()
