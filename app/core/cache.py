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
