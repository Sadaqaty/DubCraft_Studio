"""Shared utility functions."""

import tempfile
from typing import Any


def format_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def get_temp_file(suffix: str = "") -> str:
    """Return a path to a new temp file."""
    return tempfile.mktemp(suffix=suffix)


def safe_read_file(path: str) -> Any:
    """Read file contents safely."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"File read error: {e}")
        return None


def safe_write_file(path: str, data: str) -> bool:
    """Write data to file safely."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"File write error: {e}")
        return False
