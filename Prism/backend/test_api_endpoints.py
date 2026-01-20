import requests
import sys

BASE_URL = "http://localhost:8000"

def test_question_api():
    print("\n--- Testing /api/question Endpoint ---")
    
    # Test 1: Invalid/Missing File ID
    print("Test 1: Requesting with non-existent File ID (expecting error)...")
    payload = {
        "question": "What is this?",
        "file_id": "non_existent_file_id_12345"
    }
    try:
        res = requests.post(f"{BASE_URL}/api/question", json=payload)
        data = res.json()
        if not data.get("success") and "No relevant documents" in data.get("error", ""):
             print("  > PASS: Correctly returned error for missing file.")
        else:
             print(f"  > FAIL: Unexpected response: {data}")
    except Exception as e:
        print(f"  > ERROR: {e}")

    # Test 2: Valid File (if any exist)
    # We'll fetch documents first to find a valid one
    try:
        docs = requests.get(f"{BASE_URL}/api/documents").json().get('documents', [])
        if not docs:
            print("  > SKIP: No documents available to test positive case.")
            return

        target_doc = docs[0]
        print(f"Test 2: Requesting with valid File ID: {target_doc['file_id']}...")
        payload = {
            "question": "What is the summary?",
            "file_id": target_doc['file_id']
        }
        res = requests.post(f"{BASE_URL}/api/question", json=payload)
        data = res.json()
        
        if data.get("success"):
            print("  > PASS: Getting answer for valid file.")
        else:
            print(f"  > FAIL: Failed to get answer: {data.get('error')}")

    except Exception as e:
        print(f"  > ERROR: {e}")

if __name__ == "__main__":
    test_question_api()
