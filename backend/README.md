# ShopKit backend

FastAPI + SQLAlchemy 2.0 + Alembic + Postgres. The reference API for the
capstone. **Teaching artifact — not production code.**

## Layout

```
backend/
  app/
    main.py        # FastAPI app: /health, /ready, /metrics, routers
    config.py      # env-driven settings (pydantic-settings)
    database.py    # SQLAlchemy engine/session + get_db dependency
    models.py      # User, Product, CartItem, Order, OrderItem
    schemas.py     # Pydantic request/response models
    security.py    # PBKDF2 password hashing + JWT
    deps.py        # get_current_user / require_admin
    telemetry.py   # OpenTelemetry wiring (mirrors the kit's minimal-service)
    seed.py        # `python -m app.seed` — sample catalog
    routers/       # auth, users, products, cart, checkout
  alembic/         # migrations (0001_initial is the baseline)
  tests/           # pytest (SQLite-backed; no DB container needed)
  Dockerfile
  pyproject.toml   # deps + tool config (black/isort/ruff/pytest), single source
```

## Run it

### With Docker (recommended — from the repo root, one level up)
```bash
docker compose up -d --build      # app on :8000 + Postgres; migrates + seeds on boot
curl -sf localhost:8000/health
make obs-up                       # add Jaeger/Prometheus/Grafana (Module 04)
```

### Locally without Docker
```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"           # deps live in pyproject.toml (single source)
cp .env.example .env              # set DATABASE_URL (sqlite is fine for a spin-up)
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Test
```bash
pytest          # 16 tests, SQLite-backed, OTel disabled
```

## Endpoints
- `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`
- `GET/PUT/DELETE /users/me`
- `GET /products?q=&category=&page=&page_size=`, `GET /products/{id}`, `POST /products` (admin)
- `GET /cart`, `POST /cart/items`, `DELETE /cart/items/{id}`
- `POST /checkout` (Stripe test-mode PaymentIntent; offline stub when no key)
- `GET /health`, `GET /ready`, `GET /metrics`

## Notes for the security review (Module 06)
- Passwords: PBKDF2-HMAC-SHA256 (stdlib). Production would prefer bcrypt/argon2.
- JWT is stateless — logout is client-side; consider short TTLs + refresh + a
  revocation list for a real system.
- Object-level authz is enforced on cart items and `/users/me`.
- CORS is permissive for the local dev frontend (`:5173`) — tighten for prod.
