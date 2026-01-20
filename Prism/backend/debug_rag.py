import sys
import os
import json
from pathlib import Path

sys.path.append(os.getcwd())

# Initialize Vector Service
try:
    from app.services.vector_service import vector_service
    from app.services.reranker_service import reranker_service
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def main():
    target_part = "Verified Report 06"
    query = "what is verified report 6"
    print(f"\n--- Debugging Query: '{query}' ---\n")
    
    # 1. Vector Search (Retrieval) - Large K to find where it hides
    k_search = 1000
    results = vector_service.search(query, k=k_search)
    print(f"Vector Search retrieved {len(results)} chunks (k={k_search}).")

    found_idx = -1
    found_score = -1
    
    for i, res in enumerate(results):
        fid = res['chunk'].get('file_id', '')
        if target_part.lower() in fid.lower():
            found_idx = i
            found_score = res['score']
            print(f"\n✅ Found Target '{fid}' at Rank {i+1} with Score {found_score:.4f}")
            print(f"Content preview: {res['chunk'].get('text', '')[:200]}")
            break
            
    if found_idx == -1:
        print(f"\n❌ Target '{target_part}' NOT found in top {k_search} vector results.")
    
    # 2. Reranking (if applicable)
    # ... (omit reranking for now, we care about retrieval recall first)

if __name__ == "__main__":
    main()
