
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path("c:/Users/ASUS/Desktop/Prism for ScotAI/Prism/backend")
sys.path.insert(0, str(backend_dir))

from app.services.qa_service import qa_service
from app.services.folder_service import folder_service

def verify():
    # Folder ID for "Quality"
    folder_id = "65c61565-a807-4aa1-93b8-feb3c675ec45"
    
    # 1. Verify Folder Exists
    folder = folder_service.get_folder(folder_id)
    print(f"Folder: {folder['name'] if folder else 'NOT FOUND'}")
    
    if not folder:
        print("ERROR: Quality folder not found.")
        return

    # 2. Check Files in Folder
    files = folder_service.get_files_in_folder(folder_id)
    print(f"Files in folder: {len(files)}")
    
    # Check if QF006 is in there
    qf006_found = any("QF006" in f for f in files)
    print(f"QF006 valid file linked? {qf006_found}")
    
    # 3. Perform Retrieval Query
    # Asking about Section 4, which we know exists in QF006
    query = "What does Section 4 of the EPI Supplier Questionnaire cover regarding Occupational Health and Safety?"
    print(f"\nQuerying: '{query}' in folder '{folder['name']}'...")
    
    result = qa_service.answer_question(query, folder_id=folder_id)
    
    if result["success"]:
        print("\n--- Retrieval Success ---")
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Chunks Used: {result['chunks_used']}")
        print("Sources:")
        for s in result.get("sources", []):
            print(f" - {s.get('file_name')} (Page {s.get('page')})")
            
        if result['chunks_used'] > 0:
            print("\nVERIFICATION PASSED: Retrieved content successfully.")
        else:
            print("\nVERIFICATION WARNING: Success but 0 chunks used (LLM answered from internal knowledge?).")
    else:
        print("\n--- Retrieval Failed ---")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    verify()
