import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "").strip()
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID", "").strip()
NOTION_ASSETS_DB_ID = os.getenv("NOTION_ASSETS_DB_ID", "").strip()

if not NOTION_API_KEY:
    raise ValueError("CRITICAL: NOTION_API_KEY is not set as an environment variable or deployment secret.")
if not NOTION_TASKS_DB_ID:
    raise ValueError("CRITICAL: NOTION_TASKS_DB_ID is not set as an environment variable or deployment secret.")

def _parse_max_active_tasks(
    raw_val: str, default: int = 50, min_val: int = 1, max_val: int = 500
) -> int:
    """Parses and validates MAX_ACTIVE_TASKS environment variable with actionable error messages."""
    clean_val = (raw_val or "").strip()
    if not clean_val:
        return default
    try:
        val = int(clean_val)
    except ValueError:
        raise ValueError(
            f"Invalid configuration for 'MAX_ACTIVE_TASKS': '{raw_val}'. "
            f"Expected a positive integer between {min_val} and {max_val} (default: {default})."
        )
    if val < min_val or val > max_val:
        raise ValueError(
            f"Configuration 'MAX_ACTIVE_TASKS' out of allowed bounds ({val}). "
            f"Must be between {min_val} and {max_val}."
        )
    return val


MAX_ACTIVE_TASKS = _parse_max_active_tasks(os.getenv("MAX_ACTIVE_TASKS", "50"))
