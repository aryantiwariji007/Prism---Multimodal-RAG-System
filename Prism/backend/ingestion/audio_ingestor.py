import logging
from pathlib import Path

from app.services.audio_service import audio_service

logger = logging.getLogger(__name__)

def ingest_audio(file_path: str, file_id: str, progress_callback=None) -> list:
    """
    Ingest an audio file:
    1. Transcribe using Whisper
    2. Return as a text chunk
    """
    try:
        path = Path(file_path)
        
        if progress_callback:
            progress_callback(1, "Transcribing audio (this may take a moment)...", 10)

        # 1. Transcribe
        # This is a blocking call that might take time
        transcript = audio_service.transcribe(str(path))
        
        if progress_callback:
            progress_callback(3, "Indexing audio transcript...", 90)

        # 2. Create Chunk
        chunk_text = f" [AUDIO: {path.name}]\nTranscript:\n{transcript}"
        
        return [{
            "file_id": file_id,
            "page": 0,
            "text": chunk_text,
            "metadata": {
                "type": "audio",
                "original_path": str(path)
            }
        }]

    except Exception as e:
        logger.error(f"Error ingesting audio {file_path}: {e}")
        raise e
