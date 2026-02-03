
import sys
import logging
from pathlib import Path

# Setup environment
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.services.qa_service import qa_service
from app.services.vector_service import vector_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reindex_all():
    print("Starting Global Re-indexing...")
    
    # QA Service auto-loads processed docs from disk on init
    docs = qa_service.list_documents()
    print(f"Found {len(docs)} documents in QA Service.")
    
    # Clear existing indices to avoid duplicates/conflicts during re-run
    print("Clearing Vector Stores...")
    vector_service.clear()
    try:
        from app.services.llama_service import llama_service
        llama_service.clear_index()
    except Exception as e:
        print(f"Warning: Could not clear LlamaIndex/Chroma: {e}")
    
    total_chunks = 0
    
    for doc in docs:
        file_id = doc['file_id']
        print(f"Indexing {doc['file_name']}...")
        
        chunks = qa_service.document_chunks.get(file_id, [])
        if chunks:
            # Ensure each chunk has at least basic metadata if missing
            for i, chunk in enumerate(chunks):
                if 'doc_id' not in chunk: chunk['doc_id'] = file_id
                if 'file_id' not in chunk: chunk['file_id'] = file_id
                if 'chunk_index' not in chunk: chunk['chunk_index'] = i
            
            # Fix legacy integer/string chunk_ids to be globally unique
            for chunk in chunks:
                cid = chunk.get("chunk_id")
                # If cid is int, or if it doesn't start with file_id (heuristic), prefix it
                if isinstance(cid, int) or (isinstance(cid, str) and not cid.startswith(file_id)):
                     chunk["chunk_id"] = f"{file_id}_{cid}"
            
            # 1. Sync to FAISS (via vector_service)
            vector_service.add_documents(chunks)
            
            # 2. Sync to Chroma (via llama_service) for Parity
            try:
                from app.services.llama_service import llama_service
                # We use the document metadata derived from the doc list
                nodes = llama_service.create_nodes_from_chunks(chunks, doc)
                llama_service.add_nodes(nodes)
            except Exception as e:
                print(f"Warning: Failed to sync {file_id} to Chroma: {e}")

            total_chunks += len(chunks)
            
    print(f"\n--- Re-indexing Complete ---")
    print(f"Total Documents: {len(docs)}")
    print(f"Total Chunks: {total_chunks}")
    print("Vector Store is ready for Global RAG.")

if __name__ == "__main__":
    reindex_all()
