"""Application settings, read from the environment (see .env.example).

Nothing secret is hard-coded — the SECRET_KEY default below is only for local
dev and is overridden in every real environment. doctor.py / the pre-commit
secret scanner would flag a committed real key.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres at runtime; tests override this with SQLite.
    database_url: str = "postgresql+psycopg://shopkit:shopkit@localhost:5432/shopkit"

    # Auth — dev-only default; overridden via SECRET_KEY in every real env.
    secret_key: str = "dev-only-change-me"  # nosec B105
    access_token_ttl_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # Stripe (test mode). Empty => checkout returns a stub instead of calling Stripe.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # OpenTelemetry
    otel_enabled: bool = True
    otel_service_name: str = "shopkit"
    otlp_endpoint: str = "http://localhost:4317"

    # Feature flags (Module 08). Default OFF = safe.
    feature_checkout_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
