"""ORM models. Kept intentionally small — enough to exercise auth, a browsable
catalog, a cart, and checkout.

Note `User.display_name` is nullable: it's the EXPAND side of the
expand/contract migration story used in Module 07 (added alongside full_name,
dual-written, before any rename/drop).
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price_cents: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(100), index=True, default="general")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    stock: Mapped[int] = mapped_column(Integer, default=0)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    total_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_cents: Mapped[int] = mapped_column(Integer)

    order: Mapped["Order"] = relationship(back_populates="items")
