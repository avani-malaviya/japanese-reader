from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

APP_NAME = "Japanese Reader"
APP_VERSION = "0.1.0"

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_LOOKUP_CHARS = 50
MAX_CONTEXT_CHARS = 5000
