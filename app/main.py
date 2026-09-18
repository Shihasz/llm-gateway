from fastapi import FastAPI

from app.core.config import settings
from app.routers import chat

app = FastAPI(title=settings.app_name)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}
