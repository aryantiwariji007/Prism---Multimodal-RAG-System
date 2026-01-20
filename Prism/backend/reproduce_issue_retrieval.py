
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from app.services.vector_service import vector_service

def test_retrieval():
    print(f"Total vectors in index: {vector_service.index.ntotal}")
    
    query = "what is section 2 of EPI Supplier Questionnaire"
    target_file_id_substring = "bb29972f" # The one we inspected
    
    print(f"\nSearching for: '{query}'")
    
    k_values = [50, 300, 1000, 5000]
    
    for k in k_values:
        print(f"\n--- Testing k={k} ---")
        results = vector_service.search(query, k=k)
        
        found = False
        rank = -1
        
        for i, res in enumerate(results):
            file_id = res['chunk'].get('file_id', '')
            if target_file_id_substring in file_id:
                # Check snippet text
                text_snippet = res['chunk']['text'][:100].replace('\n', ' ')
                print(f"FOUND at Rank {i}: {file_id}")
                print(f"Snippet: {text_snippet}...")
                found = True
                rank = i
                break
        
        if not found:
            print(f"NOT FOUND in top {k}")
        else:
            # If found, no need to check larger K usually, but good to see stability
            pass

if __name__ == "__main__":
    test_retrieval()
