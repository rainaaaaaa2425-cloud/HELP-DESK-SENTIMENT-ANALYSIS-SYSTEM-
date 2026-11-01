import os
import re
import wave
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def sanitize_filename(filename: str) -> str:
    # Ensure standard filename without path traversals
    base = os.path.basename(filename)
    # Remove characters that are not letters, numbers, hyphens, dots, or underscores
    clean = re.sub(r"[^\w\.\-]", "_", base)
    return clean

def validate_audio_file(filename: str, file_size: int) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file type uploaded: {ext}")
        return False
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File size {file_size} exceeds safety limit of {MAX_FILE_SIZE} bytes.")
        return False
    return True

def estimate_audio_duration(file_path: str) -> float:
    ext = os.path.splitext(file_path.lower())[1]
    
    if ext == ".wav":
        try:
            with wave.open(file_path, "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                if rate > 0:
                    duration = frames / float(rate)
                    return round(duration, 2)
        except Exception as e:
            logger.warning(f"Failed to read WAV duration via native wave module: {e}")
            
    # For MP3/M4A or corrupted WAVs, estimate based on size at standard 128 kbps (16 KB/sec)
    try:
        size = os.path.getsize(file_path)
        estimated = size / 16000.0
        return round(estimated, 2)
    except Exception as e:
        logger.warning(f"Could not calculate audio file size: {e}")
        return 30.0
