"""Autosave and session restore."""

import json
import os
from typing import Any, Optional

AUTOSAVE_PATH = os.path.join("export", "dubcraft_autosave.json")


def autosave_session(state: dict) -> bool:
    """Save current session state to a JSON file."""
    try:
        os.makedirs(os.path.dirname(AUTOSAVE_PATH), exist_ok=True)
        with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Autosave error: {e}")
        return False


def restore_session() -> Optional[dict]:
    """Restore last session state from JSON file."""
    try:
        if not os.path.exists(AUTOSAVE_PATH):
            return None
        with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Restore session error: {e}")
        return None
