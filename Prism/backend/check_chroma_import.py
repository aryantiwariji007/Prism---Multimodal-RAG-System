
try:
    import chromadb
    from llama_index.vector_stores.chroma import ChromaVectorStore
    print("SUCCESS: ChromaVectorStore imported.")
except ImportError as e:
    print(f"FAIL: {e}")
