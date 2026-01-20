
import sys
import logging
from pathlib import Path

# Add backend to path
backend_dir = Path(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.vector_service import vector_service
from app.services.qa_service import qa_service
from app.services.folder_service import folder_service

def verify_fix():
    target_file_id = "HD017 MOC Verification Checklist"
    target_folder_name = "Quality"
    question = "what are the questions in MOC of change verification checklist?"

    print(f"--- Verifying Fix for {target_file_id} ---")

    # 1. Reload Vector Store (it might have changed on disk)
    vector_service._load_store()
    
    # 2. Check Vector Store Metadata
    found_in_vs = 0
    for item in vector_service.metadata:
        if item.get("file_id") == target_file_id:
            found_in_vs += 1
    
    print(f"Chunks in Vector Store: {found_in_vs}")
    
    if found_in_vs == 0:
        print("❌ FAIL: Target file still NOT in vector store metadata.")
        return

    # 3. Perform Search with Folder Filter
    quality_folder_id = None
    for f_id, data in folder_service.folders.items():
        if data["name"] == target_folder_name:
            quality_folder_id = f_id
            break
            
    if not quality_folder_id:
        print("❌ FAIL: Could not find Quality folder.")
        return

    print(f"\n--- Performing QA Search (Filtered by Folder {quality_folder_id}) ---")
    pipeline_res = qa_service._retrieve_pipeline(question, folder_id=quality_folder_id)
    
    relevant_chunks = pipeline_res["final_chunks"]
    print(f"Retrieved {len(relevant_chunks)} final chunks.")
    
    found_target = False
    for chunk in relevant_chunks:
        if chunk.get("file_id") == target_file_id:
            found_target = True
            print(f"✅ Found relevant chunk: {chunk.get('text')[:100]}...")
            break
            
    if found_target:
        print("\n✅ SUCCESS: Fix verified! The questions are now retrievable.")
    else:
        print("\n❌ FAIL: Target file chunks were not retrieved even after re-indexing.")

if __name__ == "__main__":
    verify_fix()
