"""Advanced drag & drop logic."""

from PyQt6.QtGui import QDropEvent
from typing import List
import os


def handle_drag_event(event: QDropEvent) -> List[str]:
    """Handle drag event, return list of valid video file paths."""
    paths = []
    if event.mimeData().hasUrls():
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.splitext(path)[1].lower() in [".mp4", ".mkv", ".mov", ".avi"]:
                paths.append(path)
    return paths
