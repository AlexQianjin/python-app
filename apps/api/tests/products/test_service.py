from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ProductNotFoundError
from app.modules.products import repository, service

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


async def test_get_product_raises_when_product_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(repository, "get_product", AsyncMock(return_value=None))

    with pytest.raises(ProductNotFoundError):
        await service.get_product(AsyncMock(), product_id=404)
