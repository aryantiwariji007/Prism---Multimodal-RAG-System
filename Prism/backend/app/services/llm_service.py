import os
import logging
import base64
import ollama

logger = logging.getLogger(__name__)

# Configuration
# Default to llama3.2 for text as requested/implied context, and llava for vision
TEXT_MODEL_ID = os.getenv("TEXT_MODEL_ID", "llama3.2")
VISION_MODEL_ID = os.getenv("VISION_MODEL_ID", "llava")

class LocalLLMService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return
        self.initialized = True
        logger.info(f"LocalLLMService initialized using Ollama. Text: {TEXT_MODEL_ID}, Vision: {VISION_MODEL_ID}")

    def is_ready(self) -> bool:
        try:
            # Quick check to see if we can connect to Ollama
            ollama.list()
            return True
        except Exception:
            return False

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 400, # Note: Ollama handles max tokens differently via options
        temperature: float = 0.3,
    ) -> str:
        try:
            response = ollama.chat(
                model=TEXT_MODEL_ID,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'num_predict': max_tokens,
                    'temperature': temperature,
                }
            )
            return response['message']['content']

        except Exception as e:
            logger.error(f"Ollama text generation error: {e}")
            return f"Error generating response: {str(e)}"

    def generate_vision_response(
        self,
        prompt: str,
        image_base64: str,
        model: str = "llava", # Legacy param
        max_tokens: int = 400,
        temperature: float = 0.3,
    ) -> str:
        try:
            # Allow overriding vision model if provided, else use default
            model_to_use = VISION_MODEL_ID
            
            response = ollama.chat(
                model=model_to_use,
                messages=[{
                    'role': 'user', 
                    'content': prompt, 
                    'images': [image_base64]
                }],
                options={
                    'num_predict': max_tokens,
                    'temperature': temperature,
                }
            )
            return response['message']['content']

        except Exception as e:
            logger.error(f"Ollama vision generation error: {e}")
            return f"Error generating vision response: {str(e)}"

    def answer_question(self, context: str, question: str) -> str:
        prompt = f"""You are an intelligent enterprise assistant called Prism.
You are provided with a Context below, which may include a "System Context" (metadata about folders/files) and "Document Chunks" (content from files).

Instructions:
1. Answer the user's question based on the provided Context.
2. You CAN use the "System Context" to answer questions about what files are present, folder names, etc.
3. For specific document content, rely on the [Section: Name | Page N] blocks.
4. If the answer is not present in the context at all, state "I cannot answer this question based on the provided information."
5. At the end of your answer, include a "References" section listing the source sections and pages used, in the following format:
   **References**
   * Section: [Section Name]
   * Page [Page Number]

Context:
{context}

Question:
{question}

Answer:"""
        # Grounded reasoning requires low temperature (deterministic)
        return self.generate_response(prompt, max_tokens=1000, temperature=0.0)


# Global instance
# We strictly expose 'ollama_llm' as the variable name for backward compatibility with main.py
ollama_llm = LocalLLMService()
