"""Checkout: turn the cart into an Order and a Stripe (test-mode) PaymentIntent.

Two teaching points wired in here:
  * Feature flag — checkout is gated by FEATURE_CHECKOUT_ENABLED (Module 08), so
    the team can deploy this code dark and release it with a toggle.
  * Stripe is optional locally — with no STRIPE_SECRET_KEY we still create the
    order and return a stub client_secret, so the lab runs without credentials.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Order, OrderItem, User
from ..schemas import CheckoutResponse

router = APIRouter(tags=["checkout"])


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    settings = get_settings()
    if not settings.feature_checkout_enabled:
        # Safe default when the flag is off: don't charge, tell the client.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Checkout is not available right now",
        )

    items = list(db.scalars(select(CartItem).where(CartItem.user_id == current.id)).all())
    if not items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total = sum(i.product.price_cents * i.quantity for i in items)
    order = Order(user_id=current.id, total_cents=total, status="pending")
    order.items = [
        OrderItem(
            product_id=i.product_id,
            quantity=i.quantity,
            unit_price_cents=i.product.price_cents,
        )
        for i in items
    ]
    db.add(order)
    db.flush()  # assign order.id

    client_secret = _create_payment_intent(total, order, settings.stripe_secret_key)

    # Empty the cart; the order is the source of truth from here.
    for i in items:
        db.delete(i)
    db.commit()
    db.refresh(order)
    return CheckoutResponse(
        order_id=order.id,
        total_cents=order.total_cents,
        status=order.status,
        client_secret=client_secret,
    )


def _create_payment_intent(total_cents: int, order: Order, api_key: str) -> str | None:
    if not api_key:
        # No Stripe configured (default for the lab): return a stub so the flow
        # completes end-to-end without credentials.
        order.stripe_payment_intent_id = f"pi_stub_{order.id}"
        return f"pi_stub_{order.id}_secret"
    import stripe

    stripe.api_key = api_key
    intent = stripe.PaymentIntent.create(
        amount=total_cents,
        currency="usd",
        metadata={"order_id": str(order.id)},
    )
    order.stripe_payment_intent_id = intent["id"]
    return intent["client_secret"]
