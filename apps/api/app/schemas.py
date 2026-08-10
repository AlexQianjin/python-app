from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    category: str = Field(min_length=1, max_length=80)
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
    pages: int


class CategorySummary(BaseModel):
    name: str
    product_count: int
    stock: int


class ProductSummary(BaseModel):
    total_products: int
    active_products: int
    total_stock: int
    inventory_value: Decimal
    low_stock_count: int
    categories: list[CategorySummary]
    low_stock_products: list[ProductRead]
    recently_updated: list[ProductRead]
