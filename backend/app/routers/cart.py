"""Cart operations, scoped to the authenticated user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Product, User
from ..schemas import CartItemIn, CartItemOut, CartOut

router = APIRouter(prefix="/cart", tags=["cart"])


def _serialize_cart(items: list[CartItem]) -> CartOut:
    out_items = [
        CartItemOut(
            id=item.id,
            product=item.product,
            quantity=item.quantity,
            line_total_cents=item.product.price_cents * item.quantity,
        )
        for item in items
    ]
    return CartOut(items=out_items, total_cents=sum(i.line_total_cents for i in out_items))


def _load_cart(db: Session, user: User) -> list[CartItem]:
    return list(db.scalars(select(CartItem).where(CartItem.user_id == user.id)).all())


@router.get("", response_model=CartOut)
def get_cart(current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CartOut:
    return _serialize_cart(_load_cart(db, current))


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_item(
    body: CartItemIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    product = db.get(Product, body.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    existing = db.scalar(
        select(CartItem).where(
            CartItem.user_id == current.id, CartItem.product_id == body.product_id
        )
    )
    if existing:
        existing.quantity += body.quantity
    else:
        db.add(CartItem(user_id=current.id, product_id=body.product_id, quantity=body.quantity))
    db.commit()
    return _serialize_cart(_load_cart(db, current))


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(
    item_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CartOut:
    item = db.get(CartItem, item_id)
    # Object-level authz: only the owner may remove their cart item.
    if item is None or item.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return _serialize_cart(_load_cart(db, current))
