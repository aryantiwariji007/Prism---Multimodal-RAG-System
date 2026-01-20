
import sys
import os
from pathlib import Path
import logging

# Setup environment
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.qa_service import qa_service
from app.services.progress_service import progress_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reingest_orphaned_files():
    print("Starting re-ingestion of orphaned files...")
    
    upload_dir = Path("data/uploads")
    processed_count = 0
    error_count = 0
    skipped_count = 0
    
    if not upload_dir.exists():
        print("Uploads directory not found.")
        return

    # Get current known files
    known_files = {doc['file_id'] for doc in qa_service.list_documents()}
    print(f"Known files in QA Service: {len(known_files)}")
    
    # Iterate over physical files
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            file_id = file_path.stem
            
            # Skip if already known
            if file_id in known_files:
                skipped_count += 1
                continue
                
            suffix = file_path.suffix.lower()
            if suffix not in {'.pdf', '.docx', '.jpg', '.jpeg', '.png', '.webp', '.mp3', '.wav', '.m4a'}:
                continue
                
            print(f"Processing orphan: {file_path.name}...")
            
            # Mock a processing ID
            processing_id = f"repair_{file_id}"
            progress_service.start_processing(processing_id, total_steps=3)
            
            try:
                result = qa_service.process_document_with_progress(
                    str(file_path),
                    file_id=file_id,
                    progress_file_id=processing_id
                )
                
                if result.get("success"):
                    print(f"  > Successfully re-ingested: {file_path.name}")
                    processed_count += 1
                else:
                    print(f"  > Failed to ingest: {file_path.name}. Error: {result.get('error')}")
                    error_count += 1
                    
            except Exception as e:
                print(f"  > Exception processing {file_path.name}: {e}")
                error_count += 1

    print(f"\n--- Summary ---")
    print(f"Skipped (Already OK): {skipped_count}")
    print(f"Repaired: {processed_count}")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    reingest_orphaned_files()
