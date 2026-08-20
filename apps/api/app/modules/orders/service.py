from decimal import Decimal
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CartEmptyError,
    CartItemNotFoundError,
    InsufficientStockError,
    OrderNotFoundError,
    ProductUnavailableError,
)
from app.modules.orders import repository
from app.modules.orders.models import CartItem, Order, OrderItem
from app.modules.orders.schemas import (
    CartItemCreate,
    CartItemRead,
    CartItemUpdate,
    CartRead,
    OrderItemRead,
    OrderPage,
    OrderRead,
)
from app.modules.products.cache import product_cache


def _cart_read(items: list[CartItem]) -> CartRead:
    rows = [
        CartItemRead(
            id=item.id,
            product=item.product,
            quantity=item.quantity,
            line_total=item.product.price * item.quantity,
        )
        for item in items
    ]
    return CartRead(
        items=rows,
        total_quantity=sum(row.quantity for row in rows),
        subtotal=sum((row.line_total for row in rows), start=Decimal("0.00")),
    )


def _order_read(order: Order) -> OrderRead:
    return OrderRead(
        id=order.id,
        status=order.status,
        total=order.total,
        created_at=order.created_at,
        items=[
            OrderItemRead.model_validate(item, from_attributes=True)
            for item in order.items
        ],
    )


async def get_cart(session: AsyncSession, user_id: str) -> CartRead:
    return _cart_read(await repository.get_cart_items(session, user_id))


async def add_to_cart(
    session: AsyncSession, user_id: str, payload: CartItemCreate
) -> CartRead:
    product = await repository.get_product_for_update(session, payload.product_id)
    if product is None or not product.is_active:
        raise ProductUnavailableError
    item = await repository.get_cart_item_for_product(session, user_id, product.id)
    quantity = payload.quantity + (item.quantity if item else 0)
    if quantity > product.stock:
        raise InsufficientStockError
    if item:
        item.quantity = quantity
    else:
        session.add(CartItem(user_id=user_id, product_id=product.id, quantity=quantity))
    await session.commit()
    return await get_cart(session, user_id)


async def update_cart_item(
    session: AsyncSession, user_id: str, item_id: int, payload: CartItemUpdate
) -> CartRead:
    item = await repository.get_cart_item(session, user_id, item_id)
    if item is None:
        raise CartItemNotFoundError
    product = await repository.get_product_for_update(session, item.product_id)
    if product is None or not product.is_active:
        raise ProductUnavailableError
    if payload.quantity > product.stock:
        raise InsufficientStockError
    item.quantity = payload.quantity
    await session.commit()
    return await get_cart(session, user_id)


async def remove_cart_item(session: AsyncSession, user_id: str, item_id: int) -> None:
    item = await repository.get_cart_item(session, user_id, item_id)
    if item is None:
        raise CartItemNotFoundError
    await session.delete(item)
    await session.commit()


async def clear_cart(session: AsyncSession, user_id: str) -> None:
    await repository.clear_cart(session, user_id)
    await session.commit()


async def checkout(session: AsyncSession, user_id: str) -> OrderRead:
    cart_items = await repository.get_cart_items(session, user_id)
    if not cart_items:
        raise CartEmptyError

    order_items: list[OrderItem] = []
    total = Decimal("0.00")
    for cart_item in cart_items:
        product = await repository.get_product_for_update(session, cart_item.product_id)
        if product is None or not product.is_active:
            await session.rollback()
            raise ProductUnavailableError
        if cart_item.quantity > product.stock:
            await session.rollback()
            raise InsufficientStockError
        line_total = product.price * cart_item.quantity
        total += line_total
        product.stock -= cart_item.quantity
        order_items.append(
            OrderItem(
                product_id=product.id,
                sku=product.sku,
                product_name=product.name,
                unit_price=product.price,
                quantity=cart_item.quantity,
                line_total=line_total,
            )
        )

    order = Order(user_id=user_id, status="placed", total=total, items=order_items)
    session.add(order)
    await repository.clear_cart(session, user_id)
    await session.commit()
    await session.refresh(order, attribute_names=["items"])
    await product_cache.invalidate()
    return _order_read(order)


async def list_orders(
    session: AsyncSession, user_id: str, *, page: int, page_size: int
) -> OrderPage:
    orders, total = await repository.list_orders(
        session, user_id, page=page, page_size=page_size
    )
    return OrderPage(
        items=[_order_read(order) for order in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


async def get_order(session: AsyncSession, user_id: str, order_id: int) -> OrderRead:
    order = await repository.get_order(session, user_id, order_id)
    if order is None:
        raise OrderNotFoundError
    return _order_read(order)
