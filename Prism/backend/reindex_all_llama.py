
import sys
import os
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from app.services.llama_service import llama_service
from app.services.qa_service import qa_service

def reindex_all():
    logger.info("Starting Re-indexing for LlamaIndex...")
    
    # 1. Clear existing index
    logger.info("Clearing existing LlamaIndex...")
    llama_service.clear_index()
    
    # 2. Iterate processed documents
    processed_dir = Path(qa_service.processed_dir)
    json_files = list(processed_dir.glob("*.json"))
    
    logger.info(f"Found {len(json_files)} processed documents to re-index.")
    
    success_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            metadata = data.get("metadata", {})
            chunks = data.get("chunks", [])
            
            if not chunks:
                continue
                
            file_id = json_file.stem
            metadata["file_id"] = file_id # Ensure ID is present for LlamaIndex
            
            # 3. Create Nodes
            nodes = llama_service.create_nodes_from_chunks(chunks, metadata)
            
            # 4. Add to Index
            llama_service.add_nodes(nodes)
            
            success_count += 1
            if success_count % 10 == 0:
                logger.info(f"Processed {success_count}/{len(json_files)} files...")
                
        except Exception as e:
            logger.error(f"Failed to re-index {json_file.name}: {e}")

    logger.info(f"Re-indexing complete. Successfully indexed {success_count} documents.")

if __name__ == "__main__":
    reindex_all()
