from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["admin", "manager", "member"]


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr = Field(max_length=320)
    role: UserRole = "member"
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserPage(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int
    pages: int
