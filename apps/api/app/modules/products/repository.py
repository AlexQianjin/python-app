from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Product

LOW_STOCK_THRESHOLD = 25


async def list_products(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    search: str | None,
) -> tuple[list[Product], int]:
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.category.ilike(term),
            )
        )

    total = await session.scalar(select(func.count(Product.id)).where(*filters)) or 0
    products = await session.scalars(
        select(Product)
        .where(*filters)
        .order_by(Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(products), total


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    return await session.get(Product, product_id)


async def add_product(session: AsyncSession, product: Product) -> Product:
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def save_product(session: AsyncSession, product: Product) -> Product:
    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product: Product) -> None:
    await session.delete(product)
    await session.commit()


async def get_summary_rows(
    session: AsyncSession,
) -> tuple[object, list[object], list[Product], list[Product]]:
    totals = (
        await session.execute(
            select(
                func.count(Product.id),
                func.coalesce(func.sum(case((Product.is_active, 1), else_=0)), 0),
                func.coalesce(func.sum(Product.stock), 0),
                func.coalesce(func.sum(Product.price * Product.stock), 0),
                func.coalesce(
                    func.sum(
                        case((Product.stock <= LOW_STOCK_THRESHOLD, 1), else_=0)
                    ),
                    0,
                ),
            )
        )
    ).one()
    categories = list(
        (
            await session.execute(
                select(
                    Product.category,
                    func.count(Product.id),
                    func.coalesce(func.sum(Product.stock), 0),
                )
                .group_by(Product.category)
                .order_by(func.count(Product.id).desc(), Product.category)
            )
        ).all()
    )
    low_stock = list(
        await session.scalars(
            select(Product)
            .where(Product.stock <= LOW_STOCK_THRESHOLD)
            .order_by(Product.stock, Product.name)
            .limit(5)
        )
    )
    recent = list(
        await session.scalars(
            select(Product)
            .order_by(Product.updated_at.desc(), Product.id.desc())
            .limit(5)
        )
    )
    return totals, categories, low_stock, recent
