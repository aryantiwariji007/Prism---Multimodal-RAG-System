
# from sentence_transformers import CrossEncoder
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class RerankerService:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Reranker Model: {self.model_name}...")
            self.model = CrossEncoder(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load Reranker Model: {e}. Reranking will be disabled.")
            self.model = None
    
    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Rerank a list of candidates based on query relevance.
        Candidates should be a list of dicts, each containing 'chunk' -> 'text'.
        Returns sorted top_k candidates.
        """
        if not candidates:
            return []
            
        # Prepare pairs for Cross Encoder: [[query, text1], [query, text2], ...]
        pairs = []
        valid_candidates = []
        
        for cand in candidates:
            chunk_text = cand.get("chunk", {}).get("text", "")
            if chunk_text:
                pairs.append([query, chunk_text])
                valid_candidates.append(cand)
                
        if not pairs:
            return []
            
        if not pairs or not self.model:
            # Fallback: return original candidates if model is missing
            return candidates[:top_k]
            
        scores = self.model.predict(pairs)
        
        # Attach scores and sort
        scored_results = []
        for i, cand in enumerate(valid_candidates):
            cand["rerank_score"] = float(scores[i])
            scored_results.append(cand)
            
        # Sort by rerank_score descending (higher is better for CrossEncoder)
        scored_results.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return scored_results[:top_k]

# Singleton
reranker_service = RerankerService()
