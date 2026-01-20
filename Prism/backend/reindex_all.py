
import sys
import logging
from pathlib import Path

# Setup environment
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.qa_service import qa_service
from app.services.vector_service import vector_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reindex_all():
    print("Starting Global Re-indexing...")
    
    # QA Service auto-loads processed docs from disk on init
    docs = qa_service.list_documents()
    print(f"Found {len(docs)} documents in QA Service.")
    
    # Clear existing index to avoid duplicates during re-run
    vector_service.clear()
    
    total_chunks = 0
    
    for doc in docs:
        file_id = doc['file_id']
        print(f"Indexing {doc['file_name']}...")
        
        chunks = qa_service.document_chunks.get(file_id, [])
        if chunks:
            vector_service.add_documents(chunks)
            total_chunks += len(chunks)
            
    print(f"\n--- Re-indexing Complete ---")
    print(f"Total Documents: {len(docs)}")
    print(f"Total Chunks: {total_chunks}")
    print("Vector Store is ready for Global RAG.")

if __name__ == "__main__":
    reindex_all()
