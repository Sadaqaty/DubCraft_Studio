"""Audio/video preview logic."""

import os
import sys
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaContent
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
import subprocess


def preview_audio(audio_path: str) -> None:
    """Play audio preview using QMediaPlayer."""
    app = QApplication.instance() or QApplication(sys.argv)
    player = QMediaPlayer()
    audio_output = QAudioOutput()
    player.setAudioOutput(audio_output)
    player.setSource(QUrl.fromLocalFile(audio_path))
    audio_output.setVolume(50)
    player.play()
    # Let it play for the duration of the audio
    import time
    from pydub import AudioSegment

    duration = AudioSegment.from_file(audio_path).duration_seconds
    time.sleep(duration)
    player.stop()


def preview_video(video_path: str) -> None:
    """Play video preview using system default player."""
    try:
        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", video_path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", video_path])
        elif sys.platform == "win32":
            os.startfile(video_path)
    except Exception as e:
        print(f"Video preview error: {e}")
