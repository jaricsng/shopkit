# ShopKit — Security Findings (Module 06)

The graded artifact for the security module: a threat model, the manual review
performed, and findings with remediations. This is the *reference* review —
yours covers your own app's surfaces.

> Scope: the ShopKit reference, run locally. Only ever test your own instance.

## Threat model (STRIDE, by entry point)

| Entry point | Top risks (STRIDE) | Mitigation in the reference |
|-------------|--------------------|------------------------------|
| `POST /auth/register`,`/login` | **S**poofing, weak creds | PBKDF2-HMAC-SHA256 hashing; min-8-char password; identical 401 for bad email/password (no user enumeration) |
| `GET/PUT/DELETE /users/me` | **T**ampering, info **D**isclosure (IDOR) | Always scoped to the token's user — no `/users/{id}`, so no object-level authz gap |
| `POST/DELETE /cart/items` | **E**levation (act on another's cart) | `remove_item` checks `item.user_id == current.id` → 404 otherwise |
| `POST /checkout` | **T**ampering (price/total), **R**epudiation | Total computed server-side from cart, never trusted from client; order is the record of truth |
| `POST /products` (admin) | **E**levation | `require_admin` dependency gates write access |
| Stripe webhook (exercise) | **S**poofing forged events, **R**eplay | Signature verification + idempotency (see `../assets/stripe-webhook/`) |

## Manual checks performed

Against `http://localhost:8000` with two test users (A, B):

| Check | Result |
|-------|--------|
| Unauthenticated `GET /users/me` | ✅ 401 (auth required) |
| Unauthenticated `GET /cart` | ✅ 401 |
| User B deletes user A's cart item (`DELETE /cart/items/{A_item}`) | ✅ 404 — object-level authz holds |
| Duplicate registration | ✅ 409, no detail leak |
| Login with wrong password | ✅ 401, same message as unknown email (no enumeration) |
| Checkout with empty cart | ✅ 400 |
| `POST /products` as non-admin | ✅ 403 |

These are encoded as assertions in the backend test suite
(`backend/tests/test_auth.py`, `test_catalog_cart.py`) so they don't regress.

## Findings & remediations

| # | Severity | Finding | Status |
|---|----------|---------|--------|
| 1 | Medium | **Stateless JWT can't be revoked** — `logout` is client-side; a leaked token is valid until expiry. | Accepted for the reference (60-min TTL). Production: short TTL + refresh tokens + a revocation list. Documented. |
| 2 | Low | **Password hashing is PBKDF2**, not a memory-hard KDF. | Accepted (stdlib, no build deps). Production: bcrypt/argon2. Documented in `backend/app/security.py`. |
| 3 | Low | **CORS allows the local dev origin** (`:5173`). | Intended for local dev; tighten `allow_origins` per environment before shipping. |
| 4 | Low | **No rate limiting on `/auth/*`.** | Add a reverse-proxy / API-gateway rate limit (out of scope for the kit's app layer). Flagged WARN by `manual-checks.sh`. |
| 6 | Low | **Security headers absent** (X-Content-Type-Options, X-Frame-Options, HSTS, CSP, Referrer-Policy) and the `Server` header discloses the stack. | Accepted for the teaching app; add a security-headers middleware / strip `Server` at the proxy in production. Flagged WARN by `manual-checks.sh`. |
| 5 | (exercise) | **Webhook must verify signature + be idempotent.** | Implemented in the `assets/stripe-webhook/` template; required if you enable webhooks. |

## Tooling

- `bash security/manual-checks.sh http://localhost:8000` — OWASP harness
  **adapted to ShopKit** (IDOR on cart items, token/JWT integrity, injection,
  business-logic, auth). Verified run: **18 PASS, 7 WARN, 0 FAIL** — the WARNs
  are the accepted defence-in-depth gaps (findings 4 & 6); the script separates
  real vulnerabilities (FAIL, exits non-zero) from accepted hardening gaps (WARN).
- `bash security/zap-scan.sh http://localhost:8000` — OWASP ZAP baseline DAST;
  triage headers/error-verbosity findings.
- `pip-audit` / `npm audit` (CI `security` job) — dependency CVEs.
