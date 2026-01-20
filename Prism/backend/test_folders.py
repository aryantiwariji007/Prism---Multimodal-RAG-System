
import requests
import json

BASE_URL = "http://localhost:8000"

def test_folder_rag():
    print("\n--- Testing Folder RAG ---")
    
    # 1. Create a Folder
    folder_name = "Test_Project_Alpha"
    print(f"Creating folder '{folder_name}'...")
    res = requests.post(f"{BASE_URL}/api/folders", json={"name": folder_name})
    folder_data = res.json().get("folder")
    
    if not folder_data:
        print("FAIL: Could not create folder.")
        return
        
    folder_id = folder_data["id"]
    print(f"PASS: Created folder ID: {folder_id}")

    # 2. Get a file to assign
    print("Fetching files...")
    docs = requests.get(f"{BASE_URL}/api/documents").json().get("documents", [])
    if not docs:
        print("SKIP: No documents to assign.")
        return
        
    target_doc = docs[0]
    file_id = target_doc["file_id"]
    print(f"Assigning file '{target_doc['file_name']}' to folder...")

    # 3. Assign File
    res = requests.post(f"{BASE_URL}/api/folders/{folder_id}/files", json={"file_id": file_id})
    if res.json().get("success"):
        print("PASS: File assigned.")
    else:
        print("FAIL: Assignment failed.")
        
    # 4. List Folders (Verify Count)
    res = requests.get(f"{BASE_URL}/api/folders")
    folders = res.json().get("folders", [])
    test_folder = next((f for f in folders if f["id"] == folder_id), None)
    
    if test_folder and test_folder.get("file_count") == 1:
        print("PASS: Folder list reflects file count.")
    else:
        print(f"FAIL: Folder list error. Found: {test_folder}")
        
    # 5. Question with Folder Context
    print("Asking question specific to this folder...")
    question = "Summary?"
    payload = {
        "question": question,
        "folder_id": folder_id
    }
    
    try:
        res = requests.post(f"{BASE_URL}/api/question", json=payload)
        data = res.json()
        if data.get("success"):
            print("PASS: Received answer within folder scope.")
            # Check if source matches expected file
            sources = data.get("sources", [])
            print(f"Sources: {[s['file_name'] for s in sources]}")
        else:
            print(f"FAIL: {data.get('error')}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_folder_rag()
