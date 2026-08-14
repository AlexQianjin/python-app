from math import ceil

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateSKUError, ProductNotFoundError
from app.modules.products import repository
from app.modules.products.cache import product_cache
from app.modules.products.models import Product
from app.modules.products.schemas import (
    CategorySummary,
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductSummary,
    ProductUpdate,
)


async def list_products(
    session: AsyncSession, *, page: int, page_size: int, search: str | None
) -> ProductPage:
    cached = await product_cache.get_page(page=page, page_size=page_size, search=search)
    if cached is not None:
        return cached

    products, total = await repository.list_products(
        session, page=page, page_size=page_size, search=search
    )
    result = ProductPage(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )
    await product_cache.set_page(result, search=search)
    return result


async def get_product(session: AsyncSession, product_id: int) -> ProductRead:
    cached = await product_cache.get_product(product_id)
    if cached is not None:
        return cached

    product = await repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError
    result = ProductRead.model_validate(product)
    await product_cache.set_product(result)
    return result


async def create_product(session: AsyncSession, payload: ProductCreate) -> Product:
    try:
        product = await repository.add_product(session, Product(**payload.model_dump()))
        await product_cache.invalidate()
        return product
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateSKUError from exc


async def update_product(
    session: AsyncSession, product_id: int, payload: ProductUpdate
) -> Product:
    product = await repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    try:
        product = await repository.save_product(session, product)
        await product_cache.invalidate()
        return product
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateSKUError from exc


async def delete_product(session: AsyncSession, product_id: int) -> None:
    product = await repository.get_product(session, product_id)
    if product is None:
        raise ProductNotFoundError
    await repository.delete_product(session, product)
    await product_cache.invalidate()


async def product_summary(session: AsyncSession) -> ProductSummary:
    cached = await product_cache.get_summary()
    if cached is not None:
        return cached

    totals, category_rows, low_stock, recent = await repository.get_summary_rows(
        session
    )
    result = ProductSummary(
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
    await product_cache.set_summary(result)
    return result
