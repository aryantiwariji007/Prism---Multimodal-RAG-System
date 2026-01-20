
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import torch
    print(f"DEBUG: Torch imported successfully. Version: {torch.__version__}, CUDA: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"DEBUG: Failed to import torch: {e}")

from app.services.qa_service import qa_service
from app.services.folder_service import folder_service

def debug_query():
    print("Listing folders...")
    folders = folder_service.list_folders()
    target_folder = None
    for f in folders:
        print(f"Folder: {f['id']} - {f['name']}")
        if "OneDrive" in f['name']:
            target_folder = f
    
    if target_folder:
        print(f"\nTargeting folder: {target_folder['name']} ({target_folder['id']})")
        question = "what if someone is found guilty in a bribery case"
        print(f"Asking: {question}")
        
        try:
            result = qa_service.answer_question(
                question=question,
                folder_id=target_folder['id']
            )
            print("\nResult:", result)
        except Exception as e:
            print(f"\nEXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nCould not find the target folder from screenshot.")
        # Try a general query
        question = "what if someone is found guilty in a bribery case"
        print(f"Asking (no folder): {question}")
        try:
             result = qa_service.answer_question(question=question)
             print("\nResult:", result)
        except Exception as e:
             print(f"\nEXCEPTION: {e}")
             traceback.print_exc()

if __name__ == "__main__":
    debug_query()
