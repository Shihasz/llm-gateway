from fastapi import FastAPI

from app.core.cache import get_redis_client
from app.core.config import settings
from app.routers import chat

app = FastAPI(title=settings.app_name)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/cache/ping")
def cache_ping():
    client = get_redis_client()  # pyright: ignore[reportUnknownMemberType]
    client.set("ping", "pong", ex=30)
    value = client.get("ping")
    return {"redis": "reachable", "value": value}
