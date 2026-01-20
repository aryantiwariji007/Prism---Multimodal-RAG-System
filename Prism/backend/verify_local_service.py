import sys
import os
import base64

# Ensure backend directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Mock env vars if needed
if "TEXT_MODEL_ID" not in os.environ:
    os.environ["TEXT_MODEL_ID"] = "llama3.2"
if "VISION_MODEL_ID" not in os.environ:
    os.environ["VISION_MODEL_ID"] = "llava"

from app.services.llm_service import ollama_llm
from app.services.audio_service import audio_service

def test_text():
    print("\n--- Testing Text Generation ---")
    try:
        response = ollama_llm.generate_response("Hello, are you working?")
        print(f"Response: {response}")
        if response:
            print("✅ Text Generation Success")
        else:
            print("❌ Text Generation Failed (Empty)")
    except Exception as e:
        print(f"❌ Text Generation Error: {e}")

def test_vision():
    print("\n--- Testing Vision Generation ---")
    try:
        # Create a tiny 1x1 black pixel image
        dummy_image = base64.b64decode("R0lGODlhAQABAIAAAAAAAAAAACH5BAAAAAAALAAAAAABAAEAAAICTAEAOw==")
        b64_str = base64.b64encode(dummy_image).decode('utf-8')
        response = ollama_llm.generate_vision_response("What is in this image?", b64_str)
        print(f"Response: {response}")
        if response:
            print("✅ Vision Generation Success")
        else:
            print("❌ Vision Generation Failed (Empty)")
    except Exception as e:
        print(f"❌ Vision Generation Error: {e}")

def test_audio():
    print("\n--- Testing Audio Transcription ---")
    # We need a dummy audio file. 
    # For now, just check if model loads? Or try to transribe a non-existent file to check import at least.
    # Actually, let's just check if we can instantiate the service and load model (if exposed)
    try:
        if audio_service.initialized:
            print("✅ Audio Service Initialized")
        # Trying to transcribe a missing file will raise error, but confirms library is working if it gets that far
        try:
            audio_service.transcribe("non_existent_audio.wav")
        except Exception as e:
            if "No such file" in str(e) or "failed to open" in str(e).lower():
                print("✅ Audio Service called pywhispercpp (File not found as expected)")
            else:
                print(f"⚠️ Audio Service Error: {e}")
                # It might be a real error or just the file missing. 
                # If 'pywhispercpp' is missing it would have crashed at import time (top of file in audio_service)
    except Exception as e:
        print(f"❌ Audio Service Error: {e}")

if __name__ == "__main__":
    print("Verifying Integrations...")
    test_text()
    test_vision()
    test_audio()
