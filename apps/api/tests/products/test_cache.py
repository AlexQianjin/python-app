import pytest

from app.modules.products.cache import ProductCache
from app.modules.products.schemas import ProductPage

pytestmark = pytest.mark.asyncio


class MemoryCache:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> tuple[bool, str | None]:
        return True, self.values.get(key)

    async def set(self, key: str, value: str, *, ttl: int) -> bool:
        self.values[key] = value
        return True

    async def increment(self, key: str) -> bool:
        self.values[key] = str(int(self.values.get(key, "0")) + 1)
        return True


async def test_page_cache_normalizes_search_terms() -> None:
    cache = ProductCache(MemoryCache(), ttl=60)
    page = ProductPage(items=[], total=0, page=1, page_size=100, pages=0)

    await cache.set_page(page, search="  LaMP ")

    assert await cache.get_page(page=1, page_size=100, search="lamp") == page


async def test_invalidation_moves_reads_to_a_new_namespace() -> None:
    cache = ProductCache(MemoryCache(), ttl=60)
    page = ProductPage(items=[], total=0, page=1, page_size=100, pages=0)
    await cache.set_page(page, search=None)

    await cache.invalidate()

    assert await cache.get_page(page=1, page_size=100, search=None) is None
