import logging
import os
import cv2
import tempfile
from pathlib import Path
from moviepy.editor import VideoFileClip
from typing import List, Dict

from ingestion.audio_ingestor import ingest_audio
from ingestion.image_ingestor import ingest_image

logger = logging.getLogger(__name__)

def ingest_video(file_path: str, file_id: str, progress_callback=None) -> List[Dict]:
    """
    Ingest a video file:
    1. Extract audio -> Transcribe (Whisper)
    2. Extract keyframes -> Caption/OCR (LLaVA/PaddleOCR)
    3. Aggregate all chunks
    """
    path = Path(file_path)
    all_chunks = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # --- 1. Audio Processing ---
        if progress_callback:
            progress_callback(5, "Extracting audio from video...", 10)
            
        audio_path = temp_path / "extracted_audio.wav"
        has_audio = False
        
        try:
            # Load video and extract audio
            clip = VideoFileClip(str(path))
            if clip.audio is not None:
                clip.audio.write_audiofile(str(audio_path), logger=None)
                has_audio = True
            clip.close()
        except Exception as e:
            logger.error(f"Failed to extract audio from {path}: {e}")
            
        if has_audio:
            if progress_callback:
                progress_callback(10, "Transcribing video audio...", 25)
            try:
                # Reuse audio ingestor logic, but perhaps we should modify metadata to indicate it's from video
                audio_chunks = ingest_audio(str(audio_path), file_id)
                for chunk in audio_chunks:
                    chunk["metadata"]["source_type"] = "video_audio"
                    chunk["metadata"]["original_video"] = str(path)
                    # Adjust text to indicate it's from video
                    chunk["text"] = f" [VIDEO AUDIO TRANSCRIPT: {path.name}]\n" + chunk["text"].replace(f" [AUDIO: {audio_path.name}]", "")
                
                all_chunks.extend(audio_chunks)
            except Exception as e:
                logger.error(f"Audio transcription failed for video {path}: {e}")

        # --- 2. Visual Processing (Keyframes) ---
        if progress_callback:
            progress_callback(30, "Extracting keyframes from video...", 40)
            
        frame_interval = 10 # Extract one frame every 10 seconds
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_step = int(fps * frame_interval)
        
        frame_count = 0
        success = True
        extracted_frames = []
        
        while success:
            success, frame = cap.read()
            if not success:
                break
                
            if frame_count % frame_step == 0:
                # timestamp in seconds
                timestamp = frame_count / fps
                frame_filename = f"frame_{int(timestamp)}.jpg"
                frame_path = temp_path / frame_filename
                cv2.imwrite(str(frame_path), frame)
                extracted_frames.append((timestamp, frame_path))
                
            frame_count += 1
            
        cap.release()
        
        # Process extracted frames
        total_frames = len(extracted_frames)
        for idx, (timestamp, frame_p) in enumerate(extracted_frames):
            if progress_callback:
                pct = 40 + int((idx / total_frames) * 50)
                progress_callback(pct, f"Analyzing frame at {int(timestamp)}s...", pct + 5)
                
            try:
                # Ingest as image
                image_chunks = ingest_image(str(frame_p), file_id)
                
                for chunk in image_chunks:
                    chunk["metadata"]["source_type"] = "video_frame"
                    chunk["metadata"]["original_video"] = str(path)
                    chunk["metadata"]["timestamp"] = timestamp
                    
                    # Update text header
                    mins, secs = divmod(int(timestamp), 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    chunk["text"] = f" [VIDEO FRAME: {path.name} at {time_str}]\n" + chunk["text"].replace(f" [IMAGE: {frame_p.name}]", "")
                    
                all_chunks.extend(image_chunks)
                
            except Exception as e:
                logger.error(f"Failed to process frame {frame_p}: {e}")

    return all_chunks
