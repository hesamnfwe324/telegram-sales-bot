import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger
from typing import Optional, Any
import json

logger = get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=2,
            )
            await client.ping()
            _redis_client = client
            logger.info("redis_connected", url=settings.REDIS_URL)
        except Exception as e:
            logger.warning("redis_unavailable_using_fakeredis", error=str(e))
            import fakeredis.aioredis as fakeredis
            _redis_client = fakeredis.FakeRedis(decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None


async def cache_set(key: str, value: Any, ttl: int = None) -> None:
    r = await get_redis()
    ttl = ttl or settings.REDIS_CACHE_TTL
    if value is None:
        serialized = "null"
    elif isinstance(value, str):
        serialized = value
    else:
        serialized = json.dumps(value)
    await r.setex(key, ttl, serialized)


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    value = await r.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str) -> int:
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        return await r.delete(*keys)
    return 0


async def cache_incr(key: str, amount: int = 1, ttl: int = 3600) -> int:
    r = await get_redis()
    pipe = r.pipeline()
    if amount == 1:
        await pipe.incr(key)
    else:
        await pipe.incrby(key, amount)
    await pipe.expire(key, ttl)
    results = await pipe.execute()
    return results[0]


async def cache_get_int(key: str) -> int:
    r = await get_redis()
    value = await r.get(key)
    return int(value) if value else 0


async def cache_exists(key: str) -> bool:
    r = await get_redis()
    return bool(await r.exists(key))


async def cache_ttl(key: str) -> int:
    r = await get_redis()
    return await r.ttl(key)
