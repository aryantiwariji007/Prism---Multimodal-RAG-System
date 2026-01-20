import requests
import sys

BASE_URL = "http://localhost:8000"

def check_status():
    print(f"Checking Model Status at {BASE_URL}/api/model/status...")
    try:
        res = requests.get(f"{BASE_URL}/api/model/status")
        print(f"Status: {res.status_code}")
        print(res.json())
    except Exception as e:
        print(f"Error connecting: {e}")
        return

def check_apis():
    print("\n--- Checking API Listings ---")
    
    # Check Images API (lists from disk)
    try:
        res_img = requests.get(f"{BASE_URL}/api/images")
        print(f"GET /api/images: {res_img.status_code}")
        images_on_disk = res_img.json().get('images', [])
        print(f"Found {len(images_on_disk)} images via API (Disk scan)")
        for img in images_on_disk:
            print(f" - {img['file_name']} (ID: {img['file_id']})")
    except Exception as e:
        print(f"Failed to check images: {e}")
        images_on_disk = []

    # Check Documents API (lists from qa_service memory)
    try:
        res_docs = requests.get(f"{BASE_URL}/api/documents")
        print(f"GET /api/documents: {res_docs.status_code}")
        processed_docs = res_docs.json().get('documents', [])
        print(f"Found {len(processed_docs)} processed docs via API (QA Service)")
        for doc in processed_docs:
            print(f" - {doc.get('file_name')} (ID: {doc['file_id']}, Type: {doc.get('type')})")
            
        return images_on_disk, processed_docs
    except Exception as e:
        print(f"Failed to check documents: {e}")
        return [], []

def verify_consistency(images_on_disk, processed_docs):
    print("\n--- Verifying Consistency ---")
    
    processed_ids = {d['file_id'] for d in processed_docs}
    
    for img in images_on_disk:
        img_id = img['file_id']
        if img_id not in processed_ids:
            print(f"ISSUE DETECTED: Image '{img['file_name']}' is listed in /api/images but NOT in /api/documents (QA Service).")
            print(f"  -> Selecting this image in UI will likely fail RAG because QA Service doesn't know it.")
        else:
            print(f"OK: Image '{img['file_name']}' is properly indexed.")

if __name__ == "__main__":
    check_status()
    images, docs = check_apis()
    verify_consistency(images, docs)
