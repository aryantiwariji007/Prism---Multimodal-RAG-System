import requests
import sys

BASE_URL = "http://localhost:8000"

def test_global_rag():
    print("\n--- Testing Global RAG (Vector + Reranker) ---")
    
    # 1. Ask a question without file_id (Global)
    question = "What is the conclusion of the dataset paper?" 
    # Use a question likely to hit one of the docs
    
    print(f"Query: '{question}'")
    print("Sending Global Request...", end=" ")
    
    try:
        res = requests.post(f"{BASE_URL}/api/question", json={"question": question})
        data = res.json()
        print(f"Status: {res.status_code}")
        
        if data.get("success"):
            print("\n[Answer]")
            print(data.get("answer"))
            print("\n[Sources]")
            for src in data.get("sources", []):
                print(f" - {src['file_name']} (Page {src.get('page')})")
                
            print("\nPASS: Received reasoning and sources.")
        else:
            print(f"FAIL: {data.get('error')}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_global_rag()
