import hashlib
import json
from typing import cast

import redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        # redis-py's from_url() has partially-untyped kwargs in its stubs;
        # the return type itself is correctly `Redis`, so this is safe to ignore.
        _client = redis.Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
            settings.redis_url, decode_responses=True
        )
    return _client


def make_cache_key(provider: str, model: str, prompt: str) -> str:
    raw = f"{provider}:{model}:{prompt}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"chat:{digest}"


def get_cached_response(key: str) -> dict | None:
    client = get_redis_client()
    value = cast("str | None", client.get(key))
    if value is None:
        return None
    return json.loads(value)


def set_cached_response(key: str, value: dict, ttl_seconds: int = 3600) -> None:
    client = get_redis_client()
    client.set(key, json.dumps(value), ex=ttl_seconds)
