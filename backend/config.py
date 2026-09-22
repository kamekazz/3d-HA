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

# Where the dev server listens. 0.0.0.0 on purpose: the app has to open on a
# phone on the same Wi-Fi, and 127.0.0.1 is reachable only from this machine.
# Set HOST=127.0.0.1 to keep it local; PORT for a second instance.
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

FRONTEND_DIR = BACKEND_DIR.parent / "frontend"


def ha_configured() -> bool:
    return bool(HA_BASE_URL and HA_TOKEN)
