/**
 * k6 smoke test — 1 virtual user, 60 seconds — for ShopKit.
 *
 * Verifies the API handles a realistic shopper journey without errors before
 * heavier load. The reusable PATTERN (setup() one-time auth, check()-driven
 * thresholds, BASE_URL parameterization) is unchanged from the kit's template;
 * only the endpoints/payloads are ShopKit's.
 *
 * Run: k6 run load-testing/k6/smoke.js -e BASE_URL=http://localhost:8000
 */
import { check, sleep } from "k6";
import http from "k6/http";

export const options = {
  vus: 1,
  duration: "60s",
  setupTimeout: "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"], // zero tolerance for errors in smoke
    http_req_duration: ["p(95)<1000"], // p95 under 1 s (lenient for smoke)
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const JSON_HEADERS = { "Content-Type": "application/json" };

// setup() runs once before all VUs — register + login a shopper.
export function setup() {
  check(http.get(`${BASE_URL}/health`), { "setup: health 200": (r) => r.status === 200 });
  check(http.get(`${BASE_URL}/ready`), { "setup: ready 200": (r) => r.status === 200 });

  const email = `smoke_${Date.now()}@example.com`;
  const reg = http.post(
    `${BASE_URL}/auth/register`,
    JSON.stringify({ email, full_name: "k6 Smoke", password: "K6Smoke123!" }),
    { headers: JSON_HEADERS },
  );
  check(reg, { "setup: register 201": (r) => r.status === 201 });
  return { token: reg.json("access_token") };
}

export default function ({ token }) {
  const headers = { ...JSON_HEADERS, Authorization: `Bearer ${token}` };

  // 1. Liveness + readiness
  check(http.get(`${BASE_URL}/health`), { "health 200": (r) => r.status === 200 });
  check(http.get(`${BASE_URL}/ready`), { "ready 200": (r) => r.status === 200 });

  // 2. Browse + search the catalog (public)
  const list = http.get(`${BASE_URL}/products?q=coffee`);
  check(list, { "search products 200": (r) => r.status === 200 });

  // 3. Pick a product to add to the cart
  const all = http.get(`${BASE_URL}/products?page_size=1`);
  check(all, { "list products 200": (r) => r.status === 200 });
  const productId = all.json("items.0.id");

  if (productId !== undefined && productId !== null) {
    // 4. Add to cart
    const add = http.post(
      `${BASE_URL}/cart/items`,
      JSON.stringify({ product_id: productId, quantity: 1 }),
      { headers },
    );
    check(add, { "add to cart 201": (r) => r.status === 201 });

    // 5. View cart
    check(http.get(`${BASE_URL}/cart`, { headers }), { "view cart 200": (r) => r.status === 200 });

    // 6. Checkout
    const checkout = http.post(`${BASE_URL}/checkout`, null, { headers });
    check(checkout, { "checkout 201": (r) => r.status === 201 });
  }

  // 7. Profile read
  check(http.get(`${BASE_URL}/users/me`, { headers }), { "profile 200": (r) => r.status === 200 });

  sleep(1);
}

// teardown() runs once after all VUs finish.
export function teardown({ token }) {
  const r = http.post(`${BASE_URL}/auth/logout`, null, {
    headers: { Authorization: `Bearer ${token}` },
  });
  check(r, { "teardown: logout 204": (r) => r.status === 204 });
}
