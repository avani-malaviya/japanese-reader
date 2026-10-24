"""Identifies the running version of the app, so a browser tab opened on an older version can
tell it is out of date instead of failing on a response shape it doesn't know."""

import hashlib
import time

from app.config import FRONTEND_DIR

# Changes whenever the server restarts (backend code changed) ...
_STARTED = str(time.time_ns())


def build_id() -> str:
    # ... or any frontend file changes (the server doesn't restart for those).
    digest = hashlib.sha1(_STARTED.encode())
    for path in sorted(FRONTEND_DIR.rglob("*")):
        if path.is_file():
            digest.update(f"{path.relative_to(FRONTEND_DIR)}:{path.stat().st_mtime_ns}".encode())
    return digest.hexdigest()[:12]
