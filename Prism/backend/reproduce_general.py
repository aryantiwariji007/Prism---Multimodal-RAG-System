import sys
import os
import logging
from pathlib import Path

# Configure logging to show info
logging.basicConfig(level=logging.INFO)

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from app.services.qa_service import qa_service
    from app.services.progress_service import progress_service
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def find_file(partial_name):
    # Try to find the file in uploads
    upload_dir = Path("data/uploads")
    if not upload_dir.exists():
        print("data/uploads does not exist")
        return None
        
    for f in upload_dir.glob(f"*{partial_name}*"):
        return f
    return None

def main():
    # Files to test
    files_to_test = [
        "Incident Report 10 - Consultant First Aid Case ADNOC - Jan 2021.xlsx",
        "01. COSHH Assessment_01 Print Toner.doc",
        "Wayte Bros Ltd Due Diligence ABC Questionnaire 2022.pdf"
    ]

    for filename in files_to_test:
        print(f"\n--- Testing {filename} ---")
        
        # Loose match because of UUID prefix
        file_path = find_file(Path(filename).name)
        
        if not file_path:
            print(f"File containing '{filename}' not found in data/uploads")
            continue

        print(f"Found file: {file_path}")
        file_id = "test_repro_" + Path(filename).stem.replace(" ","_")

        try:
            # We use process_document_with_progress directly
            # We define a dummy progress ID
            progress_id = "repro_progress"
            progress_service.start_processing(progress_id)
            
            result = qa_service.process_document_with_progress(str(file_path), file_id=file_id, progress_file_id=progress_id)
            
            if result.get("success"):
                print("Success!")
            else:
                print(f"Failed: {result.get('error')}")
                
        except Exception as e:
            print(f"Exception during processing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
