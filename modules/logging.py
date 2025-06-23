"""Error and debug logging."""
import os
from datetime import datetime

LOG_PATH = os.path.join('export', 'dubcraft.log')

def log_error(msg: str) -> None:
    """Log an error message with timestamp."""
    _log(msg, level='ERROR')

def log_debug(msg: str) -> None:
    """Log a debug message with timestamp."""
    _log(msg, level='DEBUG')

def _log(msg: str, level: str) -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception as e:
        print(f"Logging to file failed: {e}") 