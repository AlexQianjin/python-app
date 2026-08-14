import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RedisCache:
    """Small fault-tolerant wrapper around the application's Redis client."""

    def __init__(self, url: str | None, *, retry_delay_seconds: float = 5) -> None:
        self._client = (
            Redis.from_url(url, encoding="utf-8", decode_responses=True)
            if url
            else None
        )
        self._retry_delay_seconds = retry_delay_seconds
        self._retry_at = 0.0

    async def _run(
        self, operation: Callable[[Redis], Awaitable[T]]
    ) -> tuple[bool, T | None]:
        if self._client is None or asyncio.get_running_loop().time() < self._retry_at:
            return False, None

        try:
            return True, await operation(self._client)
        except (OSError, RedisError):
            self._retry_at = (
                asyncio.get_running_loop().time() + self._retry_delay_seconds
            )
            logger.warning("Redis cache unavailable; falling back to the database")
            return False, None

    async def get(self, key: str) -> tuple[bool, str | None]:
        return await self._run(lambda client: client.get(key))

    async def set(self, key: str, value: str, *, ttl: int) -> bool:
        succeeded, _ = await self._run(lambda client: client.set(key, value, ex=ttl))
        return succeeded

    async def increment(self, key: str) -> bool:
        succeeded, _ = await self._run(lambda client: client.incr(key))
        return succeeded

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()


redis_cache = RedisCache(settings.redis_url)
