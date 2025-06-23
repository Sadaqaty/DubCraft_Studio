from moviepy.editor import VideoFileClip
import os
from typing import Optional


def extract_audio(video_path: str, audio_out_path: str) -> bool:
    """
    Extract audio from video and save as wav.
    Returns True on success, False on error.
    """
    try:
        with VideoFileClip(video_path) as video:
            audio = video.audio
            if audio is None:
                return False
            audio.write_audiofile(audio_out_path, codec="pcm_s16le")
        return True
    except Exception as e:
        print(f"Audio extraction error: {e}")
        return False


def convert_audio_format(
    input_path: str, output_path: str, codec: str = "pcm_s16le"
) -> bool:
    """
    Convert audio file to a different format/codec.
    """
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav", codec=codec)
        return True
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return False


def separate_background_music(
    audio_path: str, out_voice_path: str, out_bgm_path: str
) -> bool:
    """
    Separate background music from voice (stub).
    """
    # TODO: Implement with Spleeter or Demucs
    raise NotImplementedError


def normalize_audio(audio_path: str, output_path: Optional[str] = None) -> str:
    """
    Normalize audio volume (stub).
    """
    # TODO: Implement normalization
    raise NotImplementedError
