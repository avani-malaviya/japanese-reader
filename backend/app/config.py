"""Settings that differ between machines come from the environment (see `Settings`); product
rules that are the same everywhere stay plain constants."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

APP_NAME = "Japanese Reader"
APP_VERSION = "0.1.0"

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_LOOKUP_CHARS = 50
MAX_CONTEXT_CHARS = 5000
MAX_MEANING_ENTRIES = 3

MAX_NAME_CHARS = 100


class Settings(BaseSettings):
    """Read from environment variables of the same name (case-insensitive), or `backend/.env`."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    library_db: Path = BACKEND_DIR / "data" / "library.sqlite"
    # Set to put the whole app behind a password (see app/access.py).
    reader_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
