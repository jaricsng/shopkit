"""Integration tests — against a REAL Postgres, exercising the REAL migrations.

This is the layer most people fake with SQLite/mocks (see the unit tests in
tests/test_*.py, which override the DB for speed). Faking it means migrations,
constraints, and dialect-specific SQL are never tested — so here we don't fake:
we run `alembic upgrade head` on a real Postgres and assert against it.

Marked `integration` so the default `pytest` run (unit, no DB) skips it. Run
explicitly with a Postgres available:

    docker compose up -d db
    DATABASE_URL=postgresql+psycopg://shopkit:shopkit@localhost:5432/shopkit \
      pytest -m integration

Skips cleanly (not fails) when no Postgres URL is reachable, so CI without a DB
service and laptops without Docker stay green.
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product, User

pytestmark = pytest.mark.integration

DB_URL = os.environ.get("INTEGRATION_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def pg_engine():
    if not DB_URL.startswith("postgresql"):
        pytest.skip("set DATABASE_URL (or INTEGRATION_DATABASE_URL) to a Postgres URL")
    engine = create_engine(DB_URL, future=True)
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any connection failure -> skip, not fail
        pytest.skip(f"Postgres not reachable at {DB_URL}: {exc}")

    # Apply the REAL migrations (not Base.metadata.create_all) so this test
    # actually exercises Alembic. env.py reads DATABASE_URL for the URL.
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    yield engine
    command.downgrade(cfg, "base")
    engine.dispose()


@pytest.fixture
def session(pg_engine):
    # Each test runs in a transaction that is rolled back, so the DB is left clean.
    conn = pg_engine.connect()
    trans = conn.begin()
    sess = Session(bind=conn)
    try:
        yield sess
    finally:
        sess.close()
        if trans.is_active:  # a failed flush may have already aborted it
            trans.rollback()
        conn.close()


def test_migrations_created_the_schema(session):
    # The migration (not create_all) produced every table.
    for table in ("users", "products", "cart_items", "orders", "order_items"):
        exists = session.execute(text("SELECT to_regclass(:t)"), {"t": f"public.{table}"}).scalar()
        assert exists is not None, f"table {table} missing after alembic upgrade"


def test_unique_email_constraint_is_real(session):
    # The unique index from the migration is enforced by Postgres itself.
    session.add(User(email="dup@example.com", hashed_password="x", full_name="A"))
    session.flush()
    session.add(User(email="dup@example.com", hashed_password="y", full_name="B"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_search_uses_real_sql(session):
    session.add_all(
        [
            Product(
                name="Espresso Beans",
                description="medium roast coffee",
                price_cents=1800,
                category="grocery",
            ),
            Product(
                name="Aurora Desk Lamp", description="warm light", price_cents=4200, category="home"
            ),
        ]
    )
    session.flush()
    like = "%coffee%"
    stmt = (
        select(func.count()).select_from(Product).where(func.lower(Product.description).like(like))
    )
    assert session.execute(stmt).scalar() == 1
