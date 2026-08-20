from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.products.schemas import ProductRead


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=999)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=999)


class CartItemRead(BaseModel):
    id: int
    product: ProductRead
    quantity: int
    line_total: Decimal


class CartRead(BaseModel):
    items: list[CartItemRead]
    total_quantity: int
    subtotal: Decimal


class OrderItemRead(BaseModel):
    id: int
    product_id: int | None
    sku: str
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class OrderRead(BaseModel):
    id: int
    status: str
    total: Decimal
    created_at: datetime
    items: list[OrderItemRead]


class OrderPage(BaseModel):
    items: list[OrderRead]
    total: int
    page: int
    page_size: int
    pages: int
