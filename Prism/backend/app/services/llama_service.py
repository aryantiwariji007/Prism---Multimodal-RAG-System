import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import shutil

# LlamaIndex Imports
from llama_index.core import (
    VectorStoreIndex, 
    StorageContext, 
    load_index_from_storage, 
    Document,
    Settings
)
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
# Local Embeddings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# Local Reranker
from llama_index.core.postprocessor import SentenceTransformerRerank
# Vector Store - CHROMA
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

# LLM for generation (Ollama)
from llama_index.llms.ollama import Ollama

logger = logging.getLogger(__name__)

class LlamaIndexService:
    def __init__(self, data_dir: str = "data/llama_store"):
        self.data_dir = Path(data_dir)
        self.chroma_db_path = self.data_dir / "chroma_db_new"
        self.persist_dir = self.data_dir / "persist" # Still used for index metadata if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # --- 1. Global Settings Configuration ---
        # Embedding: Local Nomic Embed Text
        logger.info("Loading Embedding Model: nomic-ai/nomic-embed-text-v1.5 ...")
        self.embed_model = HuggingFaceEmbedding(
            model_name="nomic-ai/nomic-embed-text-v1.5",
            trust_remote_code=True,
            embed_batch_size=32
        )
        Settings.embed_model = self.embed_model
        
        # LLM: Ollama (Llama 3.2 default)
        self.llm = Ollama(model="llama3.2", request_timeout=300.0)
        Settings.llm = self.llm
        
        # --- 2. Load/Initialize Vector Store (Chroma) ---
        self.index = self._initialize_index()
        
        # --- 3. Reranker ---
        logger.info("Loading Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2 ...")
        self.reranker = SentenceTransformerRerank(
            model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            top_n=5 
        )

    def _initialize_index(self) -> VectorStoreIndex:
        """Load existing index or create new one with ChromaDB."""
        try:
            logger.info(f"Initializing ChromaDB at {self.chroma_db_path}...")
            # 1. Initialize Chroma Client
            self.db = chromadb.PersistentClient(path=str(self.chroma_db_path))
            
            # 2. Get/Create Collection
            self.chroma_collection = self.db.get_or_create_collection("prism_documents")
            
            # 3. Create Vector Store
            vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # 4. Load Index
            # With Chroma, we can load from vector_store directly
            index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=storage_context,
            )
            logger.info("ChromaDB Index initialized.")
            return index
            
        except Exception as e:
            logger.error(f"Failed to initialize Chroma index: {e}")
            # Fallback to in-memory if persistent fails (Not ideal, but keeps app alive)
            return VectorStoreIndex([])

    def add_nodes(self, nodes: List[TextNode]):
        """Add prepared TextNodes to the index."""
        if not nodes:
            return
        self.index.insert_nodes(nodes)
        # Chroma persists automatically usually, but standard persist call is good practice
        # self.index.storage_context.persist(persist_dir=str(self.persist_dir))
        logger.info(f"Added {len(nodes)} nodes to index.")

    def create_nodes_from_chunks(self, chunks: List[Dict], metadata_base: Dict) -> List[TextNode]:
        """
        Convert raw chunk dicts into LlamaIndex TextNodes with rich metadata.
        """
        nodes = []
        for chunk in chunks:
            text = chunk.get("text", "")
            
            node_metadata = {
                "file_id": metadata_base.get("file_id"),
                "file_name": metadata_base.get("file_name"),
                "source_file": metadata_base.get("file_path"),
                "modality": metadata_base.get("type", "text"),
                "chunk_id": chunk.get("chunk_id"),
                "page_number": chunk.get("page"),
                "section_heading": self._extract_section_heading(text),
                "timestamp_start": chunk.get("start_time"),
                "timestamp_end": chunk.get("end_time"),
            }
            
            node = TextNode(text=text)
            # Filter None
            clean_metadata = {k: v for k, v in node_metadata.items() if v is not None}
            node.metadata = clean_metadata
            node.id_ = f"{metadata_base.get('file_id')}_{chunk.get('chunk_id')}"
            
            nodes.append(node)
        return nodes

    def _extract_section_heading(self, text: str) -> Optional[str]:
        first_line = text.split('\n')[0].strip()
        if len(first_line) < 100 and any(x in first_line.lower() for x in ["section", "chapter", "table", "part"]):
            return first_line
        return None

    def query(
        self, 
        query_text: str, 
        folder_file_ids: List[str] = None, 
        target_file_id: str = None,
        k: int = 25, 
        n: int = 5
    ) -> Dict:
        """
        Execute Retrieval + Reranking using LlamaIndex with Metadata Filters.
        """
        from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, FilterCondition

        # Construct Filters
        query_filters = None
        if target_file_id:
             query_filters = MetadataFilters(
                 filters=[ExactMatchFilter(key="file_id", value=target_file_id)]
             )
        elif folder_file_ids is not None:
             # Folder Scope
             if not folder_file_ids:
                 # Empty folder = No results
                 return {"results": [], "initial_count": 0, "final_count": 0}
                 
             # Use OR condition for files in folder
             # Chroma supports this well
             filters_list = [
                 ExactMatchFilter(key="file_id", value=fid) for fid in folder_file_ids
             ]
             query_filters = MetadataFilters(
                 filters=filters_list,
                 condition=FilterCondition.OR 
             )

        # 2. Retrieve
        retriever = self.index.as_retriever(
            similarity_top_k=k,
            filters=query_filters
        )
        nodes = retriever.retrieve(query_text)
        
        # 3. Rerank
        self.reranker.top_n = n
        reranked_nodes = self.reranker.postprocess_nodes(nodes, query_str=query_text)
        
        # 4. Format Result
        results = []
        for node_with_score in reranked_nodes:
            text_node = node_with_score.node
            results.append({
                "text": text_node.get_content(),
                "score": node_with_score.score,
                "metadata": text_node.metadata,
                "chunk": {
                    "text": text_node.get_content(),
                    **text_node.metadata
                }
            })
            
        return {
            "results": results,
            "initial_count": len(nodes),
            "final_count": len(results)
        }
    
    def delete_file(self, file_id: str):
        """Delete all nodes associated with a file_id."""
        try:
            self.chroma_collection.delete(where={"file_id": file_id})
            logger.info(f"Deleted vectors for file_id: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id} from Chroma: {e}")
            return False

    def clear_index(self):
        """Reset the index by deleting the collection."""
        try:
            self.db.delete_collection("prism_documents")
            logger.info("Deleted existing Chroma collection.")
        except Exception as e:
            logger.warning(f"Could not delete collection (might not exist): {e}")
            
        # Re-initialize collection
        self.chroma_collection = self.db.get_or_create_collection("prism_documents")
        
        # Re-bind index
        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        self.index = VectorStoreIndex.from_vector_store(
             vector_store,
             storage_context=storage_context,
        )

# Global Instance
llama_service = LlamaIndexService()
