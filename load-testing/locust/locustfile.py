"""Locust load test scenarios — for ShopKit.

Reusable PATTERNS (kept from the kit template): weighted HttpUser classes mixing
read-heavy / write-heavy / auth-lifecycle traffic, on_start() registering a token
once per user, named requests for grouped stats. Endpoints/payloads are ShopKit's.

Usage:
    locust -f locustfile.py --host http://localhost:8000
    locust -f locustfile.py --host http://localhost:8000 --headless -u 50 -r 5 -t 5m

Users:
    ShopperBrowseUser   — browses + searches the catalog (60% of traffic)
    ShopperBuyUser      — adds to cart and checks out (30%)
    AuthVerifyUser      — register → login → /users/me → logout (10%)

ShopKit has no login rate limit, so users register once in on_start() and reuse
the token; no inter-request sleeps are needed to dodge a limiter.
"""
import random
import time

from locust import HttpUser, TaskSet, between, events, task


def _unique_email() -> str:
    return f"user_{time.time_ns()}_{random.randint(1000, 9999)}@example.com"


def _register(client) -> str | None:
    """Register a new user and return the JWT access token, or None on failure."""
    email = _unique_email()
    reg = client.post(
        "/auth/register",
        json={"email": email, "full_name": "Load Tester", "password": "LoadTest123!"},
        name="/auth/register",
        catch_response=True,
    )
    with reg:
        if reg.status_code not in (200, 201):
            reg.failure(f"register failed: {reg.status_code}")
            return None
        reg.success()
        return reg.json().get("access_token")


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _product_ids(client) -> list[int]:
    r = client.get("/products?page_size=20", name="/products [GET]")
    if r.status_code != 200:
        return []
    return [p["id"] for p in r.json().get("items", [])]


# ── Task Sets ─────────────────────────────────────────────────────────────────


class BrowseCatalog(TaskSet):
    """Read-heavy: browse + search the catalog (public, highest volume)."""

    SEARCH_TERMS = ["coffee", "lamp", "backpack", "keyboard", "blanket"]

    def on_start(self):
        self.token = _register(self.client)
        if not self.token:
            self.interrupt()

    @task(8)
    def list_products(self):
        self.client.get("/products?page_size=20", name="/products [GET]")

    @task(5)
    def search_products(self):
        term = random.choice(self.SEARCH_TERMS)
        self.client.get(f"/products?q={term}", name="/products?q= [GET search]")

    @task(2)
    def filter_by_category(self):
        self.client.get("/products?category=home", name="/products?category= [GET]")

    @task(2)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(1)
    def ready_check(self):
        self.client.get("/ready", name="/ready")


class ShopAndCheckout(TaskSet):
    """Write-heavy: add to cart, view cart, occasionally check out."""

    def on_start(self):
        self.token = _register(self.client)
        if not self.token:
            self.interrupt()
        self.ids = _product_ids(self.client)
        if not self.ids:
            self.interrupt()

    @task(6)
    def add_to_cart(self):
        product_id = random.choice(self.ids)
        self.client.post(
            "/cart/items",
            json={"product_id": product_id, "quantity": 1},
            headers=_auth_headers(self.token),
            name="/cart/items [POST]",
        )

    @task(4)
    def view_cart(self):
        self.client.get("/cart", headers=_auth_headers(self.token), name="/cart [GET]")

    @task(1)
    def checkout(self):
        # Empties the cart; only fires occasionally to keep carts non-empty.
        self.client.post(
            "/checkout",
            headers=_auth_headers(self.token),
            name="/checkout [POST]",
            catch_response=True,
        ).success()

    @task(2)
    def view_profile(self):
        self.client.get("/users/me", headers=_auth_headers(self.token), name="/users/me [GET]")


# ── User Classes ──────────────────────────────────────────────────────────────


class ShopperBrowseUser(HttpUser):
    """A visitor who mostly browses and searches."""

    tasks = [BrowseCatalog]
    wait_time = between(1, 3)
    weight = 6


class ShopperBuyUser(HttpUser):
    """A shopper who fills a cart and sometimes checks out."""

    tasks = [ShopAndCheckout]
    wait_time = between(2, 5)
    weight = 3


class AuthVerifyUser(HttpUser):
    """Exercises the full auth lifecycle: register → /users/me → logout."""

    wait_time = between(3, 6)
    weight = 1

    @task
    def full_auth_lifecycle(self):
        token = _register(self.client)
        if not token:
            return
        self.client.get("/users/me", headers=_auth_headers(token), name="/users/me [GET auth-verify]")
        self.client.post("/auth/logout", headers=_auth_headers(token), name="/auth/logout")


# ── Event hooks (summary stats) ───────────────────────────────────────────────


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    stats = environment.stats
    total = stats.total
    print(f"\n{'=' * 60}")
    print("  Load Test Summary")
    print(f"{'=' * 60}")
    print(f"  Total requests : {total.num_requests}")
    print(f"  Failures       : {total.num_failures} ({100 * total.fail_ratio:.1f}%)")
    print(f"  Median (p50)   : {total.median_response_time} ms")
    print(f"  95th pct (p95) : {total.get_response_time_percentile(0.95)} ms")
    print(f"  99th pct (p99) : {total.get_response_time_percentile(0.99)} ms")
    print(f"  Peak RPS       : {total.current_rps:.1f}")
    print(f"{'=' * 60}\n")
