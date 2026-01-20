
try:
    from llama_index.core.postprocessor import SentenceTransformerRerank
    print("SUCCESS: from llama_index.core.postprocessor import SentenceTransformerRerank")
except ImportError as e:
    print(f"FAIL 1: {e}")

try:
    from llama_index.postprocessor.sentence_transformer_rerank import SentenceTransformerRerank
    print("SUCCESS: from llama_index.postprocessor.sentence_transformer_rerank import SentenceTransformerRerank")
except ImportError as e:
    print(f"FAIL 2: {e}")
