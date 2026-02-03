import logging
import numpy as np
from typing import Dict, List
from .vector_service import vector_service

logger = logging.getLogger(__name__)

class ParityHarness:
    """
    MANDATORY VALIDATION & PARITY HARNESS
    Ensures FAISS and ChromaDB are in sync and retrieval is deterministic.
    """
    
    def check_parity(self) -> Dict:
        """
        Check chunk count parity: FAISS count == ChromaDB count
        """
        faiss_count = vector_service.index.ntotal
        chroma_count = vector_service.collection.count()
        
        status = "OK"
        severity = "LOW"
        
        if faiss_count != chroma_count:
            status = "MISMATCH"
            severity = "CRITICAL"
            logger.error(f"PARITY ERROR: FAISS ({faiss_count}) != ChromaDB ({chroma_count})")
            
        return {
            "faiss_count": faiss_count,
            "chroma_count": chroma_count,
            "status": status,
            "severity": severity
        }

    def validate_retrieval(self, test_query: str) -> Dict:
        """
        Validates recall consistency.
        FAISS-only top-10 vs Hybrid results.
        Minimum acceptable overlap: 70%
        """
        # 1. FAISS Only (Raw indices)
        from .instructor_service import instructor_service
        query_vec = instructor_service.encode_query(test_query).reshape(1, -1)
        _, raw_indices = vector_service.index.search(query_vec, 10)
        faiss_ids = set(str(idx) for idx in raw_indices[0] if idx != -1)
        
        # 2. Hybrid Search
        hybrid_results = vector_service.search(test_query, k=10)
        hybrid_ids = set(str(res.get("faiss_id")) for res in hybrid_results)
        
        # Calculate overlap
        intersection = faiss_ids.intersection(hybrid_ids)
        overlap_pct = (len(intersection) / 10.0) * 100 if faiss_ids else 100
        
        status = "OK"
        if overlap_pct < 70:
            status = "RETRIEVAL_DRIFT"
            logger.warning(f"RETRIEVAL DRIFT: Overlap is {overlap_pct}% for query '{test_query}'")
            
        return {
            "query": test_query,
            "overlap_percent": overlap_pct,
            "status": status,
            "faiss_top_10": list(faiss_ids),
            "hybrid_top_10": list(hybrid_ids)
        }

parity_harness = ParityHarness()
