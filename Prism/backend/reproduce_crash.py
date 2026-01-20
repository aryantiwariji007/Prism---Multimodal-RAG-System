import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("--- Test: Mimic App Startup Order ---")

try:
    print("1. Initializing PaddleOCR (mimicking ocr_image.py)...")
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    print("PaddleOCR initialized.")
except Exception as e:
    print(f"PaddleOCR failed: {e}")

try:
    print("2. Initializing SentenceTransformer (mimicking vector_service.py)...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("SentenceTransformer initialized.")
except Exception as e:
    print(f"SentenceTransformer failed: {e}")
