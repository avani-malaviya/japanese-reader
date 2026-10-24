from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from app.api import health, lookup, ocr
from app.build import build_id
from app.config import APP_NAME, APP_VERSION, FRONTEND_DIR


class FrontendFiles(StaticFiles):
    """Static files the browser must revalidate on every load (cheap 304s), so an updated
    frontend never runs against a stale cached module."""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)

    @app.middleware("http")
    async def stamp_build(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            response.headers["X-App-Build"] = build_id()
        return response

    app.include_router(health.router, prefix="/api")
    app.include_router(ocr.router, prefix="/api")
    app.include_router(lookup.router, prefix="/api")
    # Mounted last so /api routes take precedence over static files.
    app.mount("/", FrontendFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
