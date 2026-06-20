"""Test fixtures: an in-memory SQLite DB and a TestClient with get_db overridden.

OTEL_ENABLED=false keeps telemetry out of unit tests. SQLite (StaticPool, shared
connection) means tests need no Postgres container — `pytest` just works.
"""

import os

os.environ["OTEL_ENABLED"] = "false"
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-bytes-long-xx")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Product


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_products(db_session):
    products = [
        Product(
            name="Aurora Desk Lamp",
            description="warm light",
            price_cents=4200,
            category="home",
            stock=25,
        ),
        Product(
            name="Trailhead Backpack",
            description="weatherproof daypack",
            price_cents=8900,
            category="outdoor",
            stock=12,
        ),
        Product(
            name="Espresso Beans",
            description="medium roast coffee",
            price_cents=1800,
            category="grocery",
            stock=60,
        ),
    ]
    db_session.add_all(products)
    db_session.commit()
    return products


@pytest.fixture
def auth_headers(client):
    """Register a user and return Authorization headers for it."""
    resp = client.post(
        "/auth/register",
        json={
            "email": "shopper@example.com",
            "password": "hunter2pass",
            "full_name": "Sam Shopper",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
