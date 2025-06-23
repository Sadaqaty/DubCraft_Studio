"""Subtitle generation (SRT)."""

from typing import List, Dict, Optional
import re


def generate_srt(
    segments: List[Dict], srt_path: str, speaker_names: Optional[Dict[int, str]] = None
) -> None:
    """
    Generate SRT file from segments and speaker names.
    segments: list of dicts with keys: 'start', 'end', 'text', 'speaker' (optional)
    speaker_names: dict mapping speaker id to name
    """
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = format_timestamp(seg["start"])
                end = format_timestamp(seg["end"])
                speaker = seg.get("speaker")
                speaker_str = (
                    f"[{speaker_names[speaker]}] "
                    if speaker_names and speaker in speaker_names
                    else ""
                )
                f.write(f"{i}\n{start} --> {end}\n{speaker_str}{seg['text']}\n\n")
    except Exception as e:
        print(f"SRT generation error: {e}")


def parse_srt(srt_path: str) -> List[Dict]:
    """Parse SRT file into a list of segments."""
    segments = []
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        blocks = re.split(r"\n\s*\n", content)
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                idx = lines[0]
                times = lines[1]
                text = " ".join(lines[2:])
                start, end = times.split(" --> ")
                segments.append(
                    {
                        "start": parse_timestamp(start),
                        "end": parse_timestamp(end),
                        "text": text,
                    }
                )
    except Exception as e:
        print(f"SRT parsing error: {e}")
    return segments


def format_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse_timestamp(ts: str) -> float:
    """Parse SRT timestamp to seconds."""
    h, m, s_ms = ts.split(":")
    s, ms = s_ms.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
