
try:
    import llama_index.core
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.faiss import FaissVectorStore
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
