"""Seed the catalog with sample products.

Run once locally:  python -m app.seed
Idempotent: skips if products already exist. Loads ../assets/seed/products.json
if present, otherwise a small built-in set. Never run against production.
"""

import json
import logging
from pathlib import Path

from sqlalchemy import func, select

from .database import SessionLocal, engine
from .models import Base, Product

logger = logging.getLogger("shopkit.seed")

_BUILTIN = [
    {
        "name": "Aurora Desk Lamp",
        "description": "Warm-white LED lamp",
        "price_cents": 4200,
        "category": "home",
        "stock": 25,
    },
    {
        "name": "Trailhead Backpack",
        "description": "28L weatherproof daypack",
        "price_cents": 8900,
        "category": "outdoor",
        "stock": 12,
    },
    {
        "name": "Espresso Beans 1kg",
        "description": "Single-origin medium roast",
        "price_cents": 1800,
        "category": "grocery",
        "stock": 60,
    },
    {
        "name": "Mechanical Keyboard",
        "description": "Hot-swappable, tactile switches",
        "price_cents": 11900,
        "category": "electronics",
        "stock": 8,
    },
    {
        "name": "Linen Throw Blanket",
        "description": "Stonewashed, 130x170cm",
        "price_cents": 5400,
        "category": "home",
        "stock": 18,
    },
]


def _load_products() -> list[dict]:
    # Look upward for the lab's assets/seed/products.json (present when running
    # from the lab checkout; NOT copied into the Docker image, where we fall
    # back to the built-in set). Walking parents avoids an IndexError when the
    # path is shallow (e.g. /app/app/seed.py in the container).
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "assets" / "seed" / "products.json"
        if candidate.exists():
            try:
                return json.loads(candidate.read_text())
            except (json.JSONDecodeError, OSError):
                logger.warning("Could not parse %s — using built-in seed set", candidate)
            break
    return _BUILTIN


def seed() -> int:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if (db.scalar(select(func.count()).select_from(Product)) or 0) > 0:
            logger.info("Catalog already seeded — skipping")
            return 0
        products = [Product(**p) for p in _load_products()]
        db.add_all(products)
        db.commit()
        logger.info("Seeded %d products", len(products))
        return len(products)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
