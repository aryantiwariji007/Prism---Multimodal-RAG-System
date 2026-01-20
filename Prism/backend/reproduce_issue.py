import sys
import os
import base64
import logging
import io
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)

sys.path.append(os.getcwd())
from app.services.llm_service import LocalLLMService
import ollama

def test_vision():
    service = LocalLLMService()
    
    print("\n--- Test 3: Converted to JPEG ONLY ---")
    image_path = "data/uploads/Dissecting-Microscope-Stereo-Microscope.webp"
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        
        try:
            image = Image.open(io.BytesIO(img_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            buf = io.BytesIO()
            image.save(buf, format='JPEG')
            jpeg_bytes = buf.getvalue()
            jpeg_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            
            print("Sending JPEG...")
            response = service.generate_vision_response("Describe this.", jpeg_base64)
            print("JPEG Success:", response[:50])
        except Exception as e:
            print("JPEG Failed:", e)

if __name__ == "__main__":
    test_vision()
