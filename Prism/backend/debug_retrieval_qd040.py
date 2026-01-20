
import sys
# Add backend to path
sys.path.append(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")

from app.services.vector_service import vector_service
from app.services.reranker_service import reranker_service

def debug_retrieval():
    query = "what is the purpose of Noise Exposure and Hearing Conservation Policy"
    
    # 1. Test Vector Search
    print("\n--- Testing Vector Search ---")
    
    # We don't have the exact folder_id easily available, but we can search globally 
    # to see if the chunk appears in top results.
    # We look for file_id="QD040 Hearing Conservation"
    
    results = vector_service.search(query, k=50) # Fetch top 50
    
    found_in_vector = False
    for i, res in enumerate(results):
        if "QD040" in res['file_id']:
            print(f"Rank {i}: Score {res['score']:.4f} | Chunk {res['chunk_id']} | Text: {res['text'][:100]}...")
            found_in_vector = True
            
    if not found_in_vector:
        print("FAILURE: QD040 chunk NOT found in top 50 vector results.")
    
    # 2. Test Reranking (if we found something)
    if found_in_vector:
        print("\n--- Testing Reranker ---")
        reranked = reranker_service.rerank(query, results, top_n=10)
        
        found_in_rerank = False
        for i, res in enumerate(reranked):
             if "QD040" in res['file_id']:
                print(f"Reranked Rank {i}: Score {res['score']:.4f} | Chunk {res['chunk_id']}")
                found_in_rerank = True
        
        if not found_in_rerank:
             print("FAILURE: QD040 lost during reranking.")

if __name__ == "__main__":
    debug_retrieval()
