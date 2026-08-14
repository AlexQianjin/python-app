from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ProductNotFoundError
from app.modules.products import repository, service
from app.modules.products.cache import product_cache
from app.modules.products.schemas import ProductPage

pytestmark = pytest.mark.asyncio


async def test_list_products_calculates_page_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    list_mock = AsyncMock(return_value=([], 201))
    monkeypatch.setattr(repository, "list_products", list_mock)

    result = await service.list_products(
        AsyncMock(), page=2, page_size=100, search="lamp"
    )

    assert result.total == 201
    assert result.pages == 3
    assert result.page == 2


async def test_list_products_returns_cached_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached = ProductPage(items=[], total=0, page=1, page_size=100, pages=0)
    get_cache_mock = AsyncMock(return_value=cached)
    list_mock = AsyncMock()
    monkeypatch.setattr(product_cache, "get_page", get_cache_mock)
    monkeypatch.setattr(repository, "list_products", list_mock)

    result = await service.list_products(
        AsyncMock(), page=1, page_size=100, search=None
    )

    assert result is cached
    list_mock.assert_not_awaited()


async def test_get_product_raises_when_product_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repository, "get_product", AsyncMock(return_value=None))

    with pytest.raises(ProductNotFoundError):
        await service.get_product(AsyncMock(), product_id=404)


async def test_delete_product_invalidates_cache_after_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = object()
    delete_mock = AsyncMock()
    invalidate_mock = AsyncMock()
    monkeypatch.setattr(repository, "get_product", AsyncMock(return_value=product))
    monkeypatch.setattr(repository, "delete_product", delete_mock)
    monkeypatch.setattr(product_cache, "invalidate", invalidate_mock)

    await service.delete_product(AsyncMock(), product_id=7)

    delete_mock.assert_awaited_once()
    invalidate_mock.assert_awaited_once_with()
