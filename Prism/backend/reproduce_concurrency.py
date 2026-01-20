import sys
import os
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from app.services.vector_service import vector_service
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def simulate_upload(file_id):
    """Simulate a file upload and vector addition"""
    # Create dummy chunks
    chunks = [
        {"text": f"This is test content for file {file_id} chunk 1", "file_id": file_id},
        {"text": f"This is test content for file {file_id} chunk 2", "file_id": file_id}
    ]
    
    # Random sleep to simulate embedding time
    time.sleep(random.uniform(0.1, 0.5))
    
    try:
        print(f"Adding documents for {file_id}...")
        vector_service.add_documents(chunks)
        print(f"Finished {file_id}")
        return True
    except Exception as e:
        print(f"FAILED {file_id}: {e}")
        return False

def main():
    print("Starting Concurrency Test...")
    print(f"Initial Index Size: {vector_service.index.ntotal}")
    
    num_files = 20
    workers = 5
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i in range(num_files):
            file_id = f"concurrency_test_{i}"
            futures.append(executor.submit(simulate_upload, file_id))
            
    print("All tasks submitted.")
    
    success_count = 0
    for f in futures:
        if f.result():
            success_count += 1
            
    print(f"\nTest Complete.")
    print(f"Successful: {success_count}/{num_files}")
    print(f"Final Index Size: {vector_service.index.ntotal}")
    
    # Clean up (optional, but good for repetitive testing)
    # vector_service.clear() 

if __name__ == "__main__":
    main()
