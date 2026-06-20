"""ShopKit API entrypoint.

Exposes /health (liveness) and /ready (readiness — checks the DB), mounts
/metrics via telemetry, and wires the feature routers. The /health + /ready
pair is what doctor.py, ci.yml's smoke job, and every deploy post-check rely on.
"""

import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .routers import auth, cart, checkout, products, users
from .telemetry import setup_telemetry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ShopKit", version="0.1.0")

# Local dev convenience — the React dev server runs on :5173. Tighten in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_telemetry(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness — cheap, no dependencies."""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness — verifies the database is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # pragma: no cover - exercised only when DB is down
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable"
        ) from exc


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"service": "shopkit", "docs": "/docs", "see": "/health, /ready, /metrics"}
