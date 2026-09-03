import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from setting import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
    return _redis_client


async def get_cache(key: str) -> Optional[Any]:
    """Retrieve JSON-deserialized value from Redis cache."""
    try:
        client = get_redis_client()
        raw = await client.get(key)
        if raw is not None:
            return json.loads(raw)
        return None
    except Exception as exc:
        logger.warning(f"Redis get_cache error for key '{key}': {exc}")
        return None


async def set_cache(key: str, value: Any, expire_seconds: int = 3600) -> bool:
    """Store JSON-serialized value in Redis cache with an expiration time."""
    try:
        client = get_redis_client()
        serialized = json.dumps(value, default=str)
        await client.set(key, serialized, ex=expire_seconds)
        return True
    except Exception as exc:
        logger.warning(f"Redis set_cache error for key '{key}': {exc}")
        return False


async def delete_cache(*keys: str) -> bool:
    """Delete one or more specific keys from Redis cache."""
    if not keys:
        return True
    try:
        client = get_redis_client()
        await client.delete(*keys)
        return True
    except Exception as exc:
        logger.warning(f"Redis delete_cache error for keys '{keys}': {exc}")
        return False


async def delete_cache_pattern(pattern: str) -> bool:
    """Delete all keys matching a glob pattern (e.g. 'kluda:cache:*')."""
    try:
        client = get_redis_client()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
        return True
    except Exception as exc:
        logger.warning(f"Redis delete_cache_pattern error for pattern '{pattern}': {exc}")
        return False
