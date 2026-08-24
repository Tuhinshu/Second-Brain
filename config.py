import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "").strip()
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID", "").strip()
NOTION_ASSETS_DB_ID = os.getenv("NOTION_ASSETS_DB_ID", "").strip()

if not NOTION_API_KEY:
    raise ValueError("CRITICAL: NOTION_API_KEY is not set in .env")
if not NOTION_TASKS_DB_ID:
    raise ValueError("CRITICAL: NOTION_TASKS_DB_ID is not set in .env")
