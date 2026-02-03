import os
import faiss
import numpy as np
import pickle
import logging
import threading
import uuid
import chromadb
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from .instructor_service import instructor_service

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, data_dir: str = "data/vector_store"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.faiss_path = self.data_dir / "prism_faiss.index"
        self.metadata_path = self.data_dir / "prism_metadata.pkl"
        
        # Non-negotiable dimension for all-mpnet-base-v2
        self.dimension = 768 
        
        # FAISS: Primary Recall Engine (Exact Similarity)
        self.index = None
        
        # Metadata Management via ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(self.data_dir / "chroma_db"))
        self.collection = self.chroma_client.get_or_create_collection(
            name="prism_metadata",
            metadata={"hnsw:space": "l2"} # Using L2 for alignment with FAISS FlatL2
        )
        
        # In-memory metadata map for fast chunk_id -> chunk resolution
        self.chunk_metadata: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        
        self._load_store()

    def _load_store(self):
        with self._lock:
            if self.faiss_path.exists() and self.metadata_path.exists():
                try:
                    self.index = faiss.read_index(str(self.faiss_path))
                    with open(self.metadata_path, "rb") as f:
                        self.chunk_metadata = pickle.load(f)
                    logger.info(f"Loaded Prism Vector Store: {self.index.ntotal} vectors.")
                except Exception as e:
                    logger.error(f"Failed to load vector store: {e}. Starting fresh.")
                    self._create_new_index()
            else:
                self._create_new_index()

    def _create_new_index(self):
        # Mandatory: Exact similarity search
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_metadata = {}
        logger.info(f"Created new exact-match FAISS index (dim={self.dimension}).")

    def save_store(self):
        """Mandatory: Persist only after full batches or explicit request"""
        with self._lock:
            try:
                faiss.write_index(self.index, str(self.faiss_path))
                with open(self.metadata_path, "wb") as f:
                    pickle.dump(self.chunk_metadata, f)
                logger.info("FAISS and metadata cache saved.")
            except Exception as e:
                logger.error(f"Error saving vector store: {e}")

    def add_documents(self, chunks: List[Dict]):
        """
        Ingestion Logic:
        1. Embed with all-mpnet-base-v2
        2. Normalize
        3. Insert into FAISS
        4. Insert into ChromaDB (Metadata Truth)
        """
        if not chunks:
            return
            
        texts = [c.get("text", "") for c in chunks]
        embeddings = instructor_service.encode_documents(texts)
        
        # Strict Metadata Validation
        required_keys = {
            "chunk_id", "doc_id", "source_file", "file_type", 
            "content_type", "ingestion_method", "chunk_index"
        }

        with self._lock:
            ids = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                # 1. Handle Nested Metadata (Compatibility with Chunker output)
                if "metadata" in chunk and isinstance(chunk["metadata"], dict):
                    # Flatten metadata into a temp copy for validation but keep chunk mostly intact
                    # However, we want these keys in the 'clean_meta' for Chroma
                    for k, v in chunk["metadata"].items():
                        if k not in chunk:
                            chunk[k] = v

                # 2. Ensure stable chunk_id
                cid = chunk.get("chunk_id")
                if cid is None:
                    cid = str(uuid.uuid4())
                    chunk["chunk_id"] = cid
                
                # 3. Check mandatory metadata (Allowing fallback for older docs)
                missing = required_keys - set(chunk.keys())
                if missing:
                    # Attempt to fill from top-level chunk attributes if they exist under different names
                    # or just log warning and fill placeholders if reindexing
                    logger.warning(f"Ingestion: Chunk {cid} missing {missing}. Attempting to fill...")
                    if "doc_id" in missing and "file_id" in chunk: chunk["doc_id"] = chunk["file_id"]
                    if "source_file" in missing and "file_id" in chunk: chunk["source_file"] = chunk["file_id"]
                    if "file_type" in missing: chunk["file_type"] = "unknown"
                    if "content_type" in missing: chunk["content_type"] = chunk.get("type", "text")
                    if "ingestion_method" in missing: chunk["ingestion_method"] = "legacy_reindex"
                    if "chunk_index" in missing: chunk["chunk_index"] = i
                    
                    # Re-check
                    missing = required_keys - set(chunk.keys())
                    if missing:
                        logger.error(f"Ingestion FAILED: Missing mandatory metadata {missing} for chunk {cid}")
                        raise ValueError(f"Missing mandatory metadata: {missing}")

                ids.append(str(cid))
                
                # 4. Clean metadata for Chroma (primitive types only)
                # We include everything at top level that is primitive
                clean_meta = {k: v for k, v in chunk.items() if isinstance(v, (str, int, float, bool))}
                metadatas.append(clean_meta)
                
                # Update FAISS
                vec = embeddings[i].reshape(1, -1)
                self.index.add(vec)
                
                # Track map for retrieval retrieval
                # FAISS internal ID matches the order in metadata list
                faiss_idx = self.index.ntotal - 1
                self.chunk_metadata[str(faiss_idx)] = chunk

            # Insert into ChromaDB
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            # Persist
            self.save_store()
            logger.info(f"Successfully ingested {len(chunks)} chunks into FAISS and ChromaDB.")

    def search(self, query: str, k: int = 30) -> List[Dict]:
        """
        Hybrid Retrieval Logic:
        1. Embed query (all-mpnet-base-v2)
        2. FAISS Recall (Exact Similarity)
        3. Metadata Validation via Chroma
        """
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # 1. Embed & Normalize
        query_vec = instructor_service.encode_query(query).reshape(1, -1)
        
        # 2. FAISS Recall (Primary)
        # We fetch more to allow for filtering/validation
        fetch_k = min(k * 2, self.index.ntotal)
        distances, indices = self.index.search(query_vec, fetch_k)
        
        results = []
        with self._lock:
            for i, idx in enumerate(indices[0]):
                if idx == -1: continue
                
                str_idx = str(idx)
                if str_idx not in self.chunk_metadata:
                    continue
                    
                chunk = self.chunk_metadata[str_idx]
                chunk_id = str(chunk.get("chunk_id"))
                
                # 3. Validate via Chroma as source of truth for persistence
                try:
                    chroma_res = self.collection.get(ids=[chunk_id])
                    if not chroma_res['ids']:
                        logger.warning(f"Chunk {chunk_id} found in FAISS but missing in Chroma Metadata Truth.")
                        continue
                except Exception as e:
                    logger.error(f"Metadata validation error for {chunk_id}: {e}")
                    continue

                results.append({
                    "chunk": chunk,
                    "score": float(distances[0][i]), # distance
                    "faiss_id": idx
                })
                
                if len(results) >= k:
                    break
                    
        return results

    def clear(self):
        with self._lock:
            self._create_new_index()
            # Reset Chroma
            self.chroma_client.delete_collection("prism_metadata")
            self.collection = self.chroma_client.create_collection("prism_metadata")
            self.save_store()

vector_service = VectorStoreService()
