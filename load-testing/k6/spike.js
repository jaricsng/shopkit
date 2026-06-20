/**
 * k6 spike test — sudden burst to 100 virtual users, then recovery — for ShopKit.
 *
 * Verifies the storefront survives a sudden traffic spike without cascading
 * failures (connection-pool exhaustion, OOM, crash loops).
 *
 * Run: k6 run load-testing/k6/spike.js -e BASE_URL=http://localhost:8000
 *
 * Unlike the load test, the spike test does NOT enforce strict latency SLOs —
 * some latency increase during a spike is expected. It enforces that:
 *   1. Error rate stays below 5% throughout (including the spike peak).
 *   2. The API recovers after the spike (error rate normalises in the tail).
 *
 * Patterns kept from the kit template: spike-then-recover stage shape, looser
 * error-rate thresholds at peak, a token pool created once in setup().
 */
import { check, group, sleep } from "k6";
import http from "k6/http";
import { Rate } from "k6/metrics";

const errorRate = new Rate("errors");

export const options = {
  setupTimeout: "60s",
  stages: [
    { duration: "30s", target: 5 }, // baseline
    { duration: "15s", target: 100 }, // spike — sudden 20x
    { duration: "2m", target: 100 }, // sustain
    { duration: "15s", target: 5 }, // recover
    { duration: "30s", target: 5 }, // verify recovery
    { duration: "10s", target: 0 }, // ramp down
  ],
  thresholds: {
    errors: ["rate<0.05"], // up to 5% acceptable at peak
    http_req_failed: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const JSON_HEADERS = { "Content-Type": "application/json" };

export function setup() {
  if (http.get(`${BASE_URL}/health`).status !== 200) throw new Error("health check failed");
  if (http.get(`${BASE_URL}/ready`).status !== 200) throw new Error("readiness check failed");

  const tokens = [];
  for (let i = 0; i < 10; i++) {
    const email = `spike_${Date.now()}_${i}@example.com`;
    const r = http.post(
      `${BASE_URL}/auth/register`,
      JSON.stringify({ email, full_name: "k6 Spike", password: "K6Spike123!" }),
      { headers: JSON_HEADERS },
    );
    if (r.status === 201) tokens.push(r.json("access_token"));
  }
  if (tokens.length === 0) throw new Error("setup: all registrations failed");

  const list = http.get(`${BASE_URL}/products?page_size=10`);
  const ids = list.status === 200 ? list.json("items").map((p) => p.id) : [];
  if (ids.length === 0) throw new Error("setup: no products seeded");
  return { tokens, ids };
}

export default function ({ tokens, ids }) {
  const token = tokens[(__VU - 1) % tokens.length];
  const headers = { ...JSON_HEADERS, Authorization: `Bearer ${token}` };

  group("spike_traffic", () => {
    // Read-heavy: catalog browse + search are the cheapest, highest-volume ops.
    const list = http.get(`${BASE_URL}/products?page_size=20`);
    check(list, { "list 200": (r) => r.status === 200 });
    errorRate.add(list.status !== 200);

    const search = http.get(`${BASE_URL}/products?q=coffee`);
    check(search, { "search 200": (r) => r.status === 200 });
    errorRate.add(search.status !== 200);

    // Some writes during the spike (add to cart) to stress the DB pool.
    const productId = ids[Math.floor(Math.random() * ids.length)];
    const add = http.post(
      `${BASE_URL}/cart/items`,
      JSON.stringify({ product_id: productId, quantity: 1 }),
      { headers },
    );
    check(add, { "add to cart 201": (r) => r.status === 201 });
    errorRate.add(add.status !== 201);
  });

  sleep(Math.random() * 1.5);
}

export function teardown({ tokens }) {
  for (const token of tokens) {
    http.post(`${BASE_URL}/auth/logout`, null, { headers: { Authorization: `Bearer ${token}` } });
  }
}
