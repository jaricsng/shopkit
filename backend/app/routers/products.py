"""Catalog browse + search. Public (no auth) so the storefront is browsable."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import audit
from ..database import get_db
from ..deps import require_admin
from ..models import Product, User
from ..schemas import ProductIn, ProductList, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductList)
def list_products(
    q: str | None = Query(default=None, description="search term (name/description)"),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductList:
    stmt = select(Product)
    count_stmt = select(func.count()).select_from(Product)
    if q:
        like = f"%{q.lower()}%"
        cond = func.lower(Product.name).like(like) | func.lower(Product.description).like(like)
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if category:
        stmt = stmt.where(Product.category == category)
        count_stmt = count_stmt.where(Product.category == category)

    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)
    items = list(db.scalars(stmt).all())
    return ProductList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# --- Admin product CRUD (stretch exercise; guarded by require_admin) ---
@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductIn,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Product:
    product = Product(
        name=body.name,
        description=body.description,
        price_cents=body.price_cents,
        category=body.category,
        image_url=body.image_url,
        stock=body.stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    audit("admin.product_create", actor=admin.email, product_id=product.id)
    return product
