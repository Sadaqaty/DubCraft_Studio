"""Speaker diarization using WhisperX or pyannote-audio."""
from typing import List, Dict
from pyannote.audio import Pipeline
import os

def diarize_speakers(audio_path: str) -> List[Dict]:
    """
    Return speaker segments with timestamps using pyannote-audio.
    Each segment: {'start': float, 'end': float, 'speaker': str}
    """
    try:
        # You must set PYANNOTE_AUTH_TOKEN in your environment for pretrained pipeline
        token = os.environ.get('PYANNOTE_AUTH_TOKEN', None)
        if not token:
            raise RuntimeError("pyannote-audio token not set in environment variable PYANNOTE_AUTH_TOKEN")
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token=token)
        diarization = pipeline(audio_path)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })
        return segments
    except Exception as e:
        print(f"Diarization error: {e}")
        return [] 