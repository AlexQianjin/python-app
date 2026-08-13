from math import ceil

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateSKUError, ProductNotFoundError
from app.modules.products import repository
from app.modules.products.models import Product
from app.modules.products.schemas import (
    CategorySummary,
    ProductCreate,
    ProductPage,
    ProductSummary,
    ProductUpdate,
)


async def list_products(
    session: AsyncSession, *, page: int, page_size: int, search: str | None
) -> ProductPage:
    products, total = await repository.list_products(
        session, page=page, page_size=page_size, search=search
    )
    return ProductPage(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


async def get_product(session: AsyncSession, product_id: int) -> Product:
    product = await repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError
    return product


async def create_product(session: AsyncSession, payload: ProductCreate) -> Product:
    try:
        return await repository.add_product(session, Product(**payload.model_dump()))
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateSKUError from exc


async def update_product(
    session: AsyncSession, product_id: int, payload: ProductUpdate
) -> Product:
    product = await get_product(session, product_id)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    try:
        return await repository.save_product(session, product)
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateSKUError from exc


async def delete_product(session: AsyncSession, product_id: int) -> None:
    product = await get_product(session, product_id)
    await repository.delete_product(session, product)


async def product_summary(session: AsyncSession) -> ProductSummary:
    totals, category_rows, low_stock, recent = await repository.get_summary_rows(
        session
    )
    return ProductSummary(
        total_products=totals[0],
        active_products=totals[1],
        total_stock=totals[2],
        inventory_value=totals[3],
        low_stock_count=totals[4],
        categories=[
            CategorySummary(name=name, product_count=count, stock=stock)
            for name, count, stock in category_rows
        ],
        low_stock_products=low_stock,
        recently_updated=recent,
    )
