"""ASGI factory: navigator-runtime serve or uvicorn backend.api.app:create_app --factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.api.errors import install_errors
from backend.api.middleware import RequestBoundary
from backend.api.routes import router
from backend.application.bootstrap import Registry


def create_app(registry=None):
    registry = registry or Registry()
    @asynccontextmanager
    async def lifespan(app):
        yield
        registry.close()
    app = FastAPI(title="Bern Research & Expertise Navigator", version="1.0.0", lifespan=lifespan)
    app.state.registry = registry
    install_errors(app)
    app.include_router(router)
    @app.get("/healthz")
    async def health():
        return {"status": "ok", "live_inference": False}
    if registry.settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(registry.settings.cors_origins),
            allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "PUT"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"])
    app.add_middleware(RequestBoundary, limit=registry.settings.max_request_bytes)
    return app
