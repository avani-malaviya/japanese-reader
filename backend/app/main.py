from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import health, lookup, ocr
from app.config import APP_NAME, APP_VERSION, FRONTEND_DIR


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.include_router(health.router, prefix="/api")
    app.include_router(ocr.router, prefix="/api")
    app.include_router(lookup.router, prefix="/api")
    # Mounted last so /api routes take precedence over static files.
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
