import base64
import logging
from pathlib import Path
from PIL import Image
import io

# Import from app.services instead of relative (to avoid circular or path issues if moved)
from app.services.llm_service import ollama_llm
from ingestion.ocr_image import prism_ocr

logger = logging.getLogger(__name__)

def ingest_image(file_path: str, file_id: str, progress_callback=None) -> list:
    """
    Ingest an image file:
    1. Read the image
    2. Extract text using PaddleOCR
    3. Generate detailed caption using Vision LLM
    4. Return as a combined text chunk
    """
    try:
        path = Path(file_path)
        
        if progress_callback:
            progress_callback(1, "Reading image...", 10)

        # 1. Read and Process Image
        with open(path, "rb") as img_file:
            img_bytes = img_file.read()

        # Convert to base64 for Ollama
        try:
             # Validate/Convert to JPEG/PNG if needed, similar to main.py
            image = Image.open(io.BytesIO(img_bytes))
            if image.mode in ('RGBA', 'P', 'LA'):
                image = image.convert('RGB')
            
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=95)
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            logger.warning(f"Image conversion warning: {e}. Using raw bytes.")
            image_base64 = base64.b64encode(img_bytes).decode('utf-8')

        if progress_callback:
            progress_callback(2, "Extracting text specific to image (OCR)...", 40)

        # 2. Extract Text with OCR
        ocr_text = prism_ocr.extract_text(str(path))
        
        if progress_callback:
            progress_callback(3, "Generating detailed image description...", 60)

        # 3. Generate Description
        # We ask for a detailed description suitable for retrieval
        prompt = "Describe this image in great detail. Include all visible text, objects, relationships, and context. This description will be used to search for this image later."
        
        caption = ollama_llm.generate_vision_response(
            prompt=prompt,
            image_base64=image_base64,
            temperature=0.2 # Lower temperature for more factual description
        )

        if progress_callback:
            progress_callback(4, "Indexing image content...", 90)

        # 4. Create Chunk
        # We prefix with a clear marker so the LLM knows this is an image description
        chunk_text = f" [IMAGE: {path.name}]\n"
        if ocr_text:
            chunk_text += f"Extracted Text:\n{ocr_text}\n\n"
        chunk_text += f"Visual Description:\n{caption}"
        
        return [{
            "file_id": file_id,
            "page": 0,
            "text": chunk_text,
            "metadata": {
                "type": "image",
                "original_path": str(path),
                "has_ocr": bool(ocr_text)
            }
        }]

    except Exception as e:
        logger.error(f"Error ingesting image {file_path}: {e}")
        raise e
