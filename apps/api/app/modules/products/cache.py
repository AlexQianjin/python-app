import hashlib
from typing import Protocol

from pydantic import BaseModel

from app.core.cache import redis_cache
from app.core.config import settings
from app.modules.products.schemas import ProductPage, ProductRead, ProductSummary


class CacheBackend(Protocol):
    async def get(self, key: str) -> tuple[bool, str | None]: ...

    async def set(self, key: str, value: str, *, ttl: int) -> bool: ...

    async def increment(self, key: str) -> bool: ...


class ProductCache:
    _version_key = "products:version"

    def __init__(self, cache: CacheBackend, *, ttl: int) -> None:
        self._cache = cache
        self._ttl = ttl

    async def _version(self) -> str | None:
        available, value = await self._cache.get(self._version_key)
        if not available:
            return None
        return value or "0"

    async def _get(self, key: str, schema: type[BaseModel]) -> BaseModel | None:
        available, value = await self._cache.get(key)
        if not available or value is None:
            return None
        try:
            return schema.model_validate_json(value)
        except ValueError:
            return None

    async def _set(self, key: str, value: BaseModel) -> None:
        await self._cache.set(key, value.model_dump_json(), ttl=self._ttl)

    async def get_page(
        self, *, page: int, page_size: int, search: str | None
    ) -> ProductPage | None:
        version = await self._version()
        if version is None:
            return None
        value = await self._get(
            self._page_key(version, page, page_size, search), ProductPage
        )
        return value if isinstance(value, ProductPage) else None

    async def set_page(self, value: ProductPage, *, search: str | None) -> None:
        version = await self._version()
        if version is not None:
            await self._set(
                self._page_key(version, value.page, value.page_size, search), value
            )

    async def get_product(self, product_id: int) -> ProductRead | None:
        version = await self._version()
        if version is None:
            return None
        value = await self._get(f"products:{version}:item:{product_id}", ProductRead)
        return value if isinstance(value, ProductRead) else None

    async def set_product(self, value: ProductRead) -> None:
        version = await self._version()
        if version is not None:
            await self._set(f"products:{version}:item:{value.id}", value)

    async def get_summary(self) -> ProductSummary | None:
        version = await self._version()
        if version is None:
            return None
        value = await self._get(f"products:{version}:summary", ProductSummary)
        return value if isinstance(value, ProductSummary) else None

    async def set_summary(self, value: ProductSummary) -> None:
        version = await self._version()
        if version is not None:
            await self._set(f"products:{version}:summary", value)

    async def invalidate(self) -> None:
        # Versioned keys avoid expensive wildcard deletes. Old entries expire by TTL.
        await self._cache.increment(self._version_key)

    @staticmethod
    def _page_key(version: str, page: int, page_size: int, search: str | None) -> str:
        normalized_search = (search or "").strip().casefold()
        search_hash = hashlib.sha256(normalized_search.encode()).hexdigest()[:16]
        return f"products:{version}:page:{page}:{page_size}:{search_hash}"


product_cache = ProductCache(redis_cache, ttl=settings.product_cache_ttl_seconds)
