
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

def debug_moc_retrieval():
    target_file_id = "HD017 MOC Verification Checklist"
    target_folder_name = "Quality"
    question = "what are the questions in MOC of change verification checklist?"

    print(f"--- Debugging Retrieval for {target_file_id} ---")

    # 1. Check consistency in processed docs
    if target_file_id in qa_service.document_chunks:
        print(f"✅ Found in qa_service.document_chunks. Chunk count: {len(qa_service.document_chunks[target_file_id])}")
    else:
        print(f"❌ NOT FOUND in qa_service.document_chunks!")

    # 2. Check Vector Store metadata presence
    found_in_vs = 0
    for item in vector_service.metadata:
        if item.get("file_id") == target_file_id:
            found_in_vs += 1
    
    if found_in_vs > 0:
        print(f"✅ Found {found_in_vs} chunks in Vector Store metadata.")
    else:
        print(f"❌ NOT FOUND in Vector Store metadata! Index likely stale.")

    # 3. Check Folder association
    folder_id = folder_service.get_folder_for_file(target_file_id)
    print(f"Folder ID for file: {folder_id}")
    
    quality_folder_id = None
    for f_id, data in folder_service.folders.items():
        if data["name"] == target_folder_name:
            quality_folder_id = f_id
            break
            
    print(f"Quality Folder ID: {quality_folder_id}")
    
    if folder_id == quality_folder_id:
        print(f"✅ File is correctly assigned to 'Quality' folder.")
    else:
        print(f"❌ File assignment mismatch! File is in {folder_id}, expected {quality_folder_id}")

    # 4. Perform Search (Global)
    print("\n--- Performing Global Search ---")
    results = vector_service.search(question, k=50) # Smaller k to see if it makes top 50
    found_in_search = False
    for i, res in enumerate(results):
        chunk_file_id = res["chunk"].get("file_id")
        score = res["score"]
        if chunk_file_id == target_file_id:
            print(f"Result {i+1}: Score={score:.4f} | Found in TARGET FILE")
            found_in_search = True
        else:
            if i < 5: # Print top 5 others
                print(f"Result {i+1}: Score={score:.4f} | File: {chunk_file_id}")
    
    if not found_in_search:
        print("❌ Target file NOT found in top 50 global results.")

    # 5. Perform QA Service Search (with folder filter)
    if quality_folder_id:
        print(f"\n--- Performing QA Search (Filtered by Folder {quality_folder_id}) ---")
        pipeline_res = qa_service._retrieve_pipeline(question, folder_id=quality_folder_id)
        
        filtered_files = set(c.get("file_id") for c in pipeline_res["final_chunks"])
        print(f"Initial count: {pipeline_res['initial_count']}")
        print(f"Filtered count: {pipeline_res['filtered_count']}")
        print(f"Final chunks count: {len(pipeline_res['final_chunks'])}")
        
        if target_file_id in filtered_files:
             print(f"✅ Target file chunks present in final filtered results.")
        else:
             print(f"❌ Target file chunks NOT in final filtered results.")

if __name__ == "__main__":
    debug_moc_retrieval()
