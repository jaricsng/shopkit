"""Pydantic request/response models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Users ---
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    display_name: str | None = None
    is_admin: bool


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)


# --- Products ---
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    price_cents: int
    category: str
    image_url: str
    stock: int


class ProductIn(BaseModel):
    name: str = Field(max_length=255)
    description: str = ""
    price_cents: int = Field(ge=0)
    category: str = Field(default="general", max_length=100)
    image_url: str = Field(default="", max_length=500)
    stock: int = Field(default=0, ge=0)


class ProductList(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


# --- Cart ---
class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemOut(BaseModel):
    id: int
    product: ProductOut
    quantity: int
    line_total_cents: int


class CartOut(BaseModel):
    items: list[CartItemOut]
    total_cents: int


# --- Checkout ---
class CheckoutResponse(BaseModel):
    order_id: int
    total_cents: int
    status: str
    client_secret: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total_cents: int
    status: str
    created_at: datetime
