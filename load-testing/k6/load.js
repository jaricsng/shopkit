/**
 * k6 load test — ramp to 50 virtual users, hold for 5 minutes — for ShopKit.
 *
 * Verifies the storefront meets performance SLOs under expected load. Thresholds
 * are the pass/fail gate, so CI can run this as a quality gate.
 *
 * Run: k6 run load-testing/k6/load.js -e BASE_URL=http://localhost:8000
 *
 * Patterns kept from the kit template: staged VU ramp, per-operation Trend
 * metrics, named thresholds per route, and a token pool created once in setup()
 * so auth isn't in the hot path. (ShopKit has no login rate limit, so the pool
 * is created without the inter-login sleeps the original needed.)
 */
import { check, group, sleep } from "k6";
import http from "k6/http";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const searchDuration = new Trend("search_duration", true);
const addToCartDuration = new Trend("add_to_cart_duration", true);
const checkoutDuration = new Trend("checkout_duration", true);

export const options = {
  setupTimeout: "60s",
  stages: [
    { duration: "1m", target: 10 }, // ramp to 10
    { duration: "2m", target: 50 }, // ramp to 50
    { duration: "5m", target: 50 }, // hold at 50
    { duration: "1m", target: 0 }, // ramp down
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"], // <1% overall errors
    http_req_duration: ["p(95)<650", "p(99)<1000"],
    "http_req_duration{name:list_products}": ["p(95)<400"], // public read
    "http_req_duration{name:search_products}": ["p(95)<500"], // ILIKE scan
    "http_req_duration{name:add_to_cart}": ["p(95)<600"],
    "http_req_duration{name:checkout}": ["p(95)<800"], // multi-row write
    errors: ["rate<0.01"],
    search_duration: ["p(95)<500"],
    add_to_cart_duration: ["p(95)<600"],
    checkout_duration: ["p(95)<800"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const JSON_HEADERS = { "Content-Type": "application/json" };
const SEARCH_TERMS = ["coffee", "lamp", "backpack", "keyboard", "blanket"];

export function setup() {
  if (http.get(`${BASE_URL}/health`).status !== 200) throw new Error("health check failed");
  if (http.get(`${BASE_URL}/ready`).status !== 200) throw new Error("readiness check failed");

  // Pre-create a token pool (no rate limit on ShopKit auth, so no sleeps needed).
  const tokens = [];
  for (let i = 0; i < 10; i++) {
    const email = `load_${Date.now()}_${i}@example.com`;
    const r = http.post(
      `${BASE_URL}/auth/register`,
      JSON.stringify({ email, full_name: "k6 Load", password: "K6Load123!" }),
      { headers: JSON_HEADERS },
    );
    if (r.status === 201) tokens.push(r.json("access_token"));
  }
  if (tokens.length === 0) throw new Error("setup: all registrations failed");

  // Grab some product ids to add to carts.
  const list = http.get(`${BASE_URL}/products?page_size=10`);
  const ids = list.status === 200 ? list.json("items").map((p) => p.id) : [];
  if (ids.length === 0) throw new Error("setup: no products seeded");
  return { tokens, ids };
}

export default function ({ tokens, ids }) {
  const token = tokens[(__VU - 1) % tokens.length];
  const headers = { ...JSON_HEADERS, Authorization: `Bearer ${token}` };

  group("browse", () => {
    const list = http.get(`${BASE_URL}/products?page_size=20`, { tags: { name: "list_products" } });
    check(list, { "list 200": (r) => r.status === 200 });
    errorRate.add(list.status !== 200);

    const term = SEARCH_TERMS[Math.floor(Math.random() * SEARCH_TERMS.length)];
    const s0 = Date.now();
    const search = http.get(`${BASE_URL}/products?q=${term}`, { tags: { name: "search_products" } });
    searchDuration.add(Date.now() - s0);
    check(search, { "search 200": (r) => r.status === 200 });
    errorRate.add(search.status !== 200);
    sleep(0.5);
  });

  group("shop", () => {
    const productId = ids[Math.floor(Math.random() * ids.length)];
    const a0 = Date.now();
    const add = http.post(
      `${BASE_URL}/cart/items`,
      JSON.stringify({ product_id: productId, quantity: 1 }),
      { headers, tags: { name: "add_to_cart" } },
    );
    addToCartDuration.add(Date.now() - a0);
    check(add, { "add to cart 201": (r) => r.status === 201 });
    errorRate.add(add.status !== 201);

    const cart = http.get(`${BASE_URL}/cart`, { headers, tags: { name: "view_cart" } });
    check(cart, { "view cart 200": (r) => r.status === 200 });
    errorRate.add(cart.status !== 200);

    // ~20% of iterations check out (empties the cart).
    if (Math.random() < 0.2) {
      const c0 = Date.now();
      const co = http.post(`${BASE_URL}/checkout`, null, { headers, tags: { name: "checkout" } });
      checkoutDuration.add(Date.now() - c0);
      check(co, { "checkout 201": (r) => r.status === 201 });
      errorRate.add(co.status !== 201);
    }
    sleep(1);
  });

  sleep(Math.random() * 2);
}

export function teardown({ tokens }) {
  for (const token of tokens) {
    http.post(`${BASE_URL}/auth/logout`, null, { headers: { Authorization: `Bearer ${token}` } });
  }
}
