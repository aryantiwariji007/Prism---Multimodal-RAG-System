
import sys
import os
import json
from pathlib import Path

# Add backend directory to sys.path to import modules
backend_dir = Path(r"c:\Users\ASUS\Desktop\Prism for ScotAI\Prism\backend")
sys.path.append(str(backend_dir))

from app.services.audit_service import audit_service

def test_history_retrieval():
    print("Testing history retrieval from audit service...")
    try:
        history = audit_service.get_history(limit=5)
        print(f"Successfully retrieved {len(history)} history items.")
        
        if len(history) > 0:
            print("\nMost recent item:")
            print(json.dumps(history[0], indent=2))
            
            # Verify structure
            item = history[0]
            assert "query" in item, "Missing 'query' field"
            assert "answer" in item, "Missing 'answer' field"
            assert "timestamp" in item, "Missing 'timestamp' field"
            print("\nStructure verification passed.")
        else:
            print("\nWarning: No history found. Verify that rag_audit_log.jsonl is not empty.")
            
    except Exception as e:
        print(f"\nError testing history retrieval: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_history_retrieval()
