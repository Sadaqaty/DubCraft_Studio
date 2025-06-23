"""Text-to-speech using Tortoise-TTS or Bark."""
from typing import List, Optional
import os
import tempfile

try:
    from tortoise.api import TextToSpeech
    from tortoise.utils.audio import load_voice
except ImportError:
    TextToSpeech = None
    load_voice = None

def list_voices() -> List[str]:
    """Return a list of available voices (Tortoise-TTS)."""
    voices_dir = os.environ.get('TORTOISE_VOICES_DIR', 'tortoise/voices')
    if not os.path.isdir(voices_dir):
        return []
    return [d for d in os.listdir(voices_dir) if os.path.isdir(os.path.join(voices_dir, d))]

def synthesize_speech(text: str, voice: str, emotion: Optional[str] = None) -> str:
    """
    Generate speech audio for given text, voice, and emotion (if supported).
    Returns path to generated wav file.
    """
    if TextToSpeech is None:
        raise ImportError("Tortoise-TTS is not installed.")
    tts = TextToSpeech()
    voices_dir = os.environ.get('TORTOISE_VOICES_DIR', 'tortoise/voices')
    voice_path = os.path.join(voices_dir, voice)
    voice_samples, conditioning_latents = load_voice(voice_path)
    preset = "fast"  # Could be parameterized
    # Tortoise-TTS does not natively support emotion, but can be extended in future
    gen = tts.tts_with_preset(text, voice_samples=voice_samples, conditioning_latents=conditioning_latents, preset=preset)
    out_path = tempfile.mktemp(suffix=f"_{voice}.wav")
    gen.save(out_path)
    return out_path

def preview_voice(voice: str, emotion: Optional[str] = None) -> str:
    """
    Generate a short preview for a given voice and emotion.
    Returns path to preview wav file.
    """
    preview_text = "This is a sample preview of the selected voice."
    return synthesize_speech(preview_text, voice, emotion)

def batch_synthesize_speech(texts: List[str], voices: List[str], emotions: Optional[List[str]] = None) -> List[str]:
    """
    Batch synthesize speech for multiple texts and voices.
    Returns list of output wav file paths.
    """
    results = []
    for i, (text, voice) in enumerate(zip(texts, voices)):
        emotion = emotions[i] if emotions and i < len(emotions) else None
        out_path = synthesize_speech(text, voice, emotion)
        results.append(out_path)
    return results 