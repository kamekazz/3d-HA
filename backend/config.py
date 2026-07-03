"""Loads server-side configuration from .env. The HA token lives here only."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

HA_BASE_URL = os.getenv("HA_BASE_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")
APP_SECRET = os.getenv("APP_SECRET", "dev-secret-change-me")
DB_PATH = os.getenv("DB_PATH", str(BACKEND_DIR / "house.db"))

FRONTEND_DIR = BACKEND_DIR.parent / "frontend"


def ha_configured() -> bool:
    return bool(HA_BASE_URL and HA_TOKEN)
