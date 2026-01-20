import logging
import os
from pywhispercpp.model import Model

logger = logging.getLogger(__name__)

class AudioService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "initialized"):
            return
        self.initialized = True
        self.model = None
        # the user requested ggml-base.en-q5.bin
        # pywhispercpp Model class can take a model name or path
        # Available: base.en-q5_1
        self.model_name = "base.en-q5_1" 

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}...")
            try:
                # pywhispercpp will attempt to download if not found, or use the name 
                # to look up the model. 'base.en-q5' implies the quantized version.
                self.model = Model(self.model_name, print_realtime=False, print_progress=False)
                logger.info("Whisper model loaded.")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                # Fallback to standard base.en if q5 fails
                if "q5" in self.model_name:
                    logger.warning("Retrying with 'base.en'...")
                    try:
                        self.model = Model("base.en", print_realtime=False, print_progress=False)
                        logger.info("Whisper base.en model loaded.")
                    except Exception as e2:
                        logger.error(f"Fallback failed: {e2}")
                        raise e
                else:
                    raise

    def transcribe(self, file_path: str) -> str:
        """
        Transcribes the audio file at the given path.
        Returns the transcribed text.
        """
        try:
            self._load_model()
            # transcribe returns valid segments
            segments = self.model.transcribe(file_path, n_threads=6)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            logger.error(f"Transcription error for {file_path}: {e}")
            raise

audio_service = AudioService()
