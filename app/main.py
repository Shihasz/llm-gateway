from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings
from app.core.db import init_db
from app.core.logging import configure_logging
from app.core.tracing import configure_tracing
from app.routers import chat

app = FastAPI(title=settings.app_name)
app.include_router(chat.router)
configure_tracing(app)


@app.on_event("startup")
def on_startup():
    configure_logging()
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
