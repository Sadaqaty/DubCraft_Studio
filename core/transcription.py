"""Transcription using faster-whisper."""
from typing import List, Dict, Any
from faster_whisper import WhisperModel
import os

def load_transcription_model(model_size: str = 'medium') -> WhisperModel:
    """Load and return the faster-whisper model."""
    try:
        model = WhisperModel(model_size, device="auto", compute_type="auto")
        return model
    except Exception as e:
        print(f"Transcription model loading error: {e}")
        raise

def transcribe_audio(audio_path: str, model_size: str = 'medium') -> List[Dict]:
    """Transcribe audio and return segments with timestamps."""
    try:
        model = load_transcription_model(model_size)
        segments, _ = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
        results = []
        for seg in segments:
            results.append({
                'start': seg.start,
                'end': seg.end,
                'text': seg.text.strip()
            })
        return results
    except Exception as e:
        print(f"Transcription error: {e}")
        return []

def format_segments(segments: List[Dict]) -> List[Dict]:
    """Format raw segments into a standard structure."""
    # Already formatted above, but can be extended for custom formatting
    return segments 