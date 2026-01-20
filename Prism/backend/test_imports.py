import sys
import os

print(f"Python: {sys.version}")

print("--- Test 1: Import Torch ---")
try:
    import torch
    print(f"Torch Version: {torch.__version__}")
    print("Torch imported successfully")
except Exception as e:
    print(f"Torch import failed: {e}")

print("\n--- Test 2: Import Paddle ---")
try:
    import paddle
    print(f"Paddle Version: {paddle.__version__}")
    print("Paddle imported successfully")
except Exception as e:
    print(f"Paddle import failed: {e}")

print("\n--- Test 3: Import PaddleOCR ---")
try:
    from paddleocr import PaddleOCR
    print("PaddleOCR imported successfully")
except Exception as e:
    print(f"PaddleOCR import failed: {e}")
