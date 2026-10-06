import time
from typing import cast

from app.core.cache import get_redis_client

DEFAULT_CAPACITY = 10
DEFAULT_REFILL_RATE = 1.0  # tokens per second


def check_rate_limit(
    api_key: str,
    capacity: int = DEFAULT_CAPACITY,
    refill_rate: float = DEFAULT_REFILL_RATE,
) -> tuple[bool, int]:
    """
    Returns (allowed, remaining_tokens).
    Uses a Redis hash to track {tokens, last_refill} per key.
    """
    client = get_redis_client()
    key = f"ratelimit:{api_key}"
    now = time.time()

    bucket = cast("dict[str, str]", client.hgetall(key))

    if bucket:
        tokens = float(bucket.get("tokens", capacity))
        last_refill = float(bucket.get("last_refill", now))
    else:
        tokens = float(capacity)
        last_refill = now

    elapsed = max(0.0, now - last_refill)
    tokens = min(capacity, tokens + elapsed * refill_rate)

    if tokens < 1:
        client.hset(key, mapping={"tokens": tokens, "last_refill": now})
        client.expire(key, 3600)
        return False, int(tokens)

    tokens -= 1
    client.hset(key, mapping={"tokens": tokens, "last_refill": now})
    client.expire(key, 3600)
    return True, int(tokens)
