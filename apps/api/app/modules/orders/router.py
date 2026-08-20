from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies.auth import AuthenticatedUser
from app.dependencies.database import DatabaseSession
from app.modules.orders import service
from app.modules.orders.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartRead,
    OrderPage,
    OrderRead,
)

router = APIRouter(tags=["cart and orders"])


@router.get("/cart", response_model=CartRead)
async def get_cart(session: DatabaseSession, user: AuthenticatedUser) -> CartRead:
    return await service.get_cart(session, user.id)


@router.post(
    "/cart/items", response_model=CartRead, status_code=status.HTTP_201_CREATED
)
async def add_to_cart(
    payload: CartItemCreate, session: DatabaseSession, user: AuthenticatedUser
) -> CartRead:
    return await service.add_to_cart(session, user.id, payload)


@router.put("/cart/items/{item_id}", response_model=CartRead)
async def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    session: DatabaseSession,
    user: AuthenticatedUser,
) -> CartRead:
    return await service.update_cart_item(session, user.id, item_id, payload)


@router.delete("/cart/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: int, session: DatabaseSession, user: AuthenticatedUser
) -> Response:
    await service.remove_cart_item(session, user.id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/cart", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(session: DatabaseSession, user: AuthenticatedUser) -> Response:
    await service.clear_cart(session, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout(session: DatabaseSession, user: AuthenticatedUser) -> OrderRead:
    return await service.checkout(session, user.id)


@router.get("/orders", response_model=OrderPage)
async def list_orders(
    session: DatabaseSession,
    user: AuthenticatedUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrderPage:
    return await service.list_orders(session, user.id, page=page, page_size=page_size)


@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int, session: DatabaseSession, user: AuthenticatedUser
) -> OrderRead:
    return await service.get_order(session, user.id, order_id)
