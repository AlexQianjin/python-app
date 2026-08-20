from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import CartEmptyError, InsufficientStockError
from app.modules.orders import repository, service
from app.modules.orders.schemas import CartItemCreate

pytestmark = pytest.mark.asyncio


async def test_get_cart_calculates_quantity_and_subtotal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = SimpleNamespace(
        id=4,
        sku="SKU-4",
        name="Desk lamp",
        description="",
        category="Lighting",
        price=Decimal("12.50"),
        stock=10,
        is_active=True,
        created_at="2026-08-20T00:00:00Z",
        updated_at="2026-08-20T00:00:00Z",
    )
    item = SimpleNamespace(id=7, product=product, quantity=3)
    monkeypatch.setattr(repository, "get_cart_items", AsyncMock(return_value=[item]))

    result = await service.get_cart(AsyncMock(), "user-1")

    assert result.total_quantity == 3
    assert result.subtotal == Decimal("37.50")
    assert result.items[0].product.name == "Desk lamp"


async def test_add_to_cart_rejects_quantity_above_stock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    product = SimpleNamespace(id=4, is_active=True, stock=2)
    monkeypatch.setattr(
        repository, "get_product_for_update", AsyncMock(return_value=product)
    )
    monkeypatch.setattr(
        repository, "get_cart_item_for_product", AsyncMock(return_value=None)
    )

    with pytest.raises(InsufficientStockError):
        await service.add_to_cart(
            AsyncMock(), "user-1", CartItemCreate(product_id=4, quantity=3)
        )


async def test_checkout_rejects_empty_cart(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(repository, "get_cart_items", AsyncMock(return_value=[]))

    with pytest.raises(CartEmptyError):
        await service.checkout(AsyncMock(), "user-1")
