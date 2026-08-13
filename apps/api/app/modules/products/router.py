from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import require_user
from app.dependencies.database import DatabaseSession
from app.modules.products import service
from app.modules.products.models import Product
from app.modules.products.schemas import (
    ProductCreate,
    ProductPage,
    ProductRead,
    ProductSummary,
    ProductUpdate,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=ProductPage)
async def list_products(
    session: DatabaseSession,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(max_length=160)] = None,
) -> ProductPage:
    return await service.list_products(
        session, page=page, page_size=page_size, search=search
    )


@router.get("/summary", response_model=ProductSummary)
async def product_summary(session: DatabaseSession) -> ProductSummary:
    return await service.product_summary(session)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, session: DatabaseSession) -> Product:
    return await service.get_product(session, product_id)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, session: DatabaseSession) -> Product:
    return await service.create_product(session, payload)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, payload: ProductUpdate, session: DatabaseSession
) -> Product:
    return await service.update_product(session, product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, session: DatabaseSession) -> Response:
    await service.delete_product(session, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
