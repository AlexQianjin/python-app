from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Product
from app.schemas import (
    CategorySummary,
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductSummary,
    ProductUpdate,
)

router = APIRouter(prefix="/api/products", tags=["products"])
Session = Annotated[AsyncSession, Depends(get_session)]
LOW_STOCK_THRESHOLD = 25


@router.get("", response_model=ProductPage)
async def list_products(
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(max_length=160)] = None,
) -> ProductPage:
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

    total = await session.scalar(select(func.count(Product.id)).where(*filters))
    total = total or 0
    result = await session.scalars(
        select(Product)
        .where(*filters)
        .order_by(Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return ProductPage(
        items=list(result),
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


@router.get("/summary", response_model=ProductSummary)
async def product_summary(session: Session) -> ProductSummary:
    totals = (
        await session.execute(
            select(
                func.count(Product.id),
                func.coalesce(func.sum(case((Product.is_active, 1), else_=0)), 0),
                func.coalesce(func.sum(Product.stock), 0),
                func.coalesce(func.sum(Product.price * Product.stock), 0),
                func.coalesce(
                    func.sum(case((Product.stock <= LOW_STOCK_THRESHOLD, 1), else_=0)),
                    0,
                ),
            )
        )
    ).one()

    category_rows = (
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
    low_stock_products = await session.scalars(
        select(Product)
        .where(Product.stock <= LOW_STOCK_THRESHOLD)
        .order_by(Product.stock, Product.name)
        .limit(5)
    )
    recently_updated = await session.scalars(
        select(Product).order_by(Product.updated_at.desc(), Product.id.desc()).limit(5)
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
        low_stock_products=list(low_stock_products),
        recently_updated=list(recently_updated),
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, session: Session) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, session: Session) -> Product:
    product = Product(**payload.model_dump())
    session.add(product)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="SKU already exists") from exc
    await session.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, payload: ProductUpdate, session: Session
) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="SKU already exists") from exc
    await session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, session: Session) -> Response:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
