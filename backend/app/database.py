"""SQLAlchemy 2.0 engine, session, and Base.

Sync SQLAlchemy keeps the reference simple and reliable to test. Postgres in
every real environment (psycopg); tests swap in SQLite via the get_db override
in tests/conftest.py.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

_settings = get_settings()

engine = create_engine(_settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency: a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
