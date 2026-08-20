from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.orders.models import CartItem, Order
from app.modules.products.models import Product


async def get_cart_items(session: AsyncSession, user_id: str) -> list[CartItem]:
    result = await session.scalars(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
        .order_by(CartItem.created_at, CartItem.id)
    )
    return list(result)


async def get_cart_item(
    session: AsyncSession, user_id: str, item_id: int
) -> CartItem | None:
    return await session.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user_id)
    )


async def get_cart_item_for_product(
    session: AsyncSession, user_id: str, product_id: int
) -> CartItem | None:
    return await session.scalar(
        select(CartItem).where(
            CartItem.user_id == user_id, CartItem.product_id == product_id
        )
    )


async def get_product_for_update(
    session: AsyncSession, product_id: int
) -> Product | None:
    return await session.scalar(
        select(Product).where(Product.id == product_id).with_for_update()
    )


async def clear_cart(session: AsyncSession, user_id: str) -> None:
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))


async def list_orders(
    session: AsyncSession, user_id: str, *, page: int, page_size: int
) -> tuple[list[Order], int]:
    total = (
        await session.scalar(
            select(func.count(Order.id)).where(Order.user_id == user_id)
        )
        or 0
    )
    result = await session.scalars(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result), total


async def get_order(session: AsyncSession, user_id: str, order_id: int) -> Order | None:
    return await session.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(selectinload(Order.items))
    )
