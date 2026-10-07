import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from app.core.auth import get_api_key
from app.core.cache import get_cached_response, make_cache_key, set_cached_response
from app.core.db import get_db
from app.core.logging import get_logger
from app.core.metrics import (
    chat_request_duration_seconds,
    chat_requests_total,
    rate_limit_rejections_total,
)
from app.core.ratelimit import check_rate_limit
from app.core.registry import get_provider, list_providers
from app.models import UsageRecord

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    prompt: str
    provider: str = "mock"
    model: str = "mock-model"


class ChatResponse(BaseModel):
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cached: bool


@router.get("/providers")
def get_providers():
    return {"providers": list_providers()}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    start = time.perf_counter()

    allowed, remaining = check_rate_limit(api_key)
    if not allowed:
        rate_limit_rejections_total.labels(api_key=api_key).inc()
        logger.warning("rate_limit_exceeded", api_key=api_key)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        provider = get_provider(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    cache_key = make_cache_key(request.provider, request.model, request.prompt)
    cached = get_cached_response(cache_key)

    if cached is not None:
        response_data = cached
        was_cached = True
    else:
        result = await provider.complete(request.prompt, request.model)
        response_data = {
            "text": result.text,
            "provider": result.provider,
            "model": result.model,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        }
        set_cached_response(cache_key, response_data)
        was_cached = False

    db.add(
        UsageRecord(
            provider=response_data["provider"],
            model=response_data["model"],
            input_tokens=response_data["input_tokens"],
            output_tokens=response_data["output_tokens"],
            cached=was_cached,
        )
    )
    db.commit()

    duration = time.perf_counter() - start
    chat_requests_total.labels(
        provider=response_data["provider"], model=response_data["model"], cached=str(was_cached)
    ).inc()
    chat_request_duration_seconds.labels(
        provider=response_data["provider"], model=response_data["model"]
    ).observe(duration)

    logger.info(
        "chat_request_completed",
        provider=response_data["provider"],
        model=response_data["model"],
        cached=was_cached,
        duration_ms=round(duration * 1000, 2),
        api_key=api_key,
    )

    return ChatResponse(**response_data, cached=was_cached)


@router.get("/usage")
def get_usage(db: Session = Depends(get_db)):
    rows = (
        db.query(
            UsageRecord.provider,
            UsageRecord.model,
            func.count(UsageRecord.id).label("requests"),
            func.sum(UsageRecord.input_tokens).label("input_tokens"),
            func.sum(UsageRecord.output_tokens).label("output_tokens"),
            func.sum(UsageRecord.cached.cast(Integer)).label("cache_hits"),
        )
        .group_by(UsageRecord.provider, UsageRecord.model)
        .all()
    )

    return {
        "usage": [
            {
                "provider": r.provider,
                "model": r.model,
                "requests": r.requests,
                "input_tokens": int(r.input_tokens or 0),
                "output_tokens": int(r.output_tokens or 0),
                "cache_hits": int(r.cache_hits or 0),
            }
            for r in rows
        ]
    }
