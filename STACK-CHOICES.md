# ShopKit — Stack Choices & Swaps (rubric item 16)

## What ShopKit is

A small e-commerce storefront: user accounts, a browsable/searchable product
catalog, a cart, and Stripe-test-mode checkout. Chosen because it exercises
auth, an authz boundary, a relational data model, a payment integration, and a
real UI — a broad surface for the DevSecOps wrapper to act on.

## The stack (the kit's golden path)

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **FastAPI** (Python 3.12) | Matches the kit's minimal-service + `check-python`; first-class OpenAPI + OTel |
| ORM / migrations | **SQLAlchemy 2.0 + Alembic** | Matches `check-db` + the `check_migrations.py` gate |
| Database | **Postgres** | The kit's default CI service container; `doctor.py` recognizes it |
| Frontend | **React + TypeScript (Vite)** | Matches `ci.yml`'s frontend job + `check-frontend` |
| Payments | **Stripe (test mode)** | Free sandbox; PaymentIntent server-side, stub fallback offline |
| Deploy target | **GCP Cloud Run** (`--cloud gcp`) | The only Terraform module the kit ships |

Everything lines up with the kit's defaults, so no asset needed swapping to
reach green — which is exactly why it's the reference.

## A swap we evaluated (required reflection)

**Database: Postgres → SQLite.** We evaluated SQLite to drop the Postgres
container for local dev.

- *Pros:* zero-dependency local runs; the test suite already uses it.
- *Cons:* `doctor.py`'s DB check expects a Postgres client; `ci.yml` ships a
  Postgres service container; Cloud SQL (the Terraform module) is Postgres;
  SQLite lacks concurrent-writer semantics a storefront needs.
- *Per `docs/TECH-STACK-SWAP-GUIDE.md` ("database" row):* swapping would mean
  changing the CI service block, the `DATABASE_URL` driver, and the IaC — a
  real but contained change.
- **Decision:** keep Postgres for parity with the kit and production realism;
  use SQLite only as the test backend (via the `get_db` override in
  `backend/tests/conftest.py`). Best of both.

## Other swaps a different capstone might make

- **Cloud: GCP → AWS/Azure** — `--cloud aws|azure` gives deploy jobs but no
  Terraform (kit ships GCP only); see the swap guide's "IaC" row.
- **Backend: Python → Node/Go** — keep the `/health`+`/ready`+OTLP shape; swap
  the CI test job + `doctor.py` DB detection per the swap guide.
