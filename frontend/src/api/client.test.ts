import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, formatPrice } from "./client";

describe("formatPrice", () => {
  it("formats whole dollars", () => expect(formatPrice(4200)).toBe("$42.00"));
  it("formats sub-dollar amounts", () => expect(formatPrice(600)).toBe("$6.00"));
  it("formats zero", () => expect(formatPrice(0)).toBe("$0.00"));
});

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });
  afterEach(() => localStorage.clear());

  function mockFetch(status: number, body: unknown) {
    return vi.fn().mockResolvedValue({
      status,
      ok: status >= 200 && status < 300,
      json: async () => body,
    } as Response);
  }

  it("GET parses a JSON body", async () => {
    vi.stubGlobal("fetch", mockFetch(200, { items: [], total: 0 }));
    const out = await api.get<{ total: number }>("/products");
    expect(out.total).toBe(0);
  });

  it("attaches the bearer token when present", async () => {
    const f = mockFetch(200, {});
    vi.stubGlobal("fetch", f);
    localStorage.setItem("token", "tok123");
    await api.get("/users/me");
    const headers = (f.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok123");
  });

  it("omits Authorization when no token", async () => {
    const f = mockFetch(200, {});
    vi.stubGlobal("fetch", f);
    await api.get("/products");
    const headers = (f.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it("throws ApiError with the server detail on a 4xx", async () => {
    vi.stubGlobal("fetch", mockFetch(409, { detail: "Email already registered" }));
    await expect(api.post("/auth/register", {})).rejects.toMatchObject({
      status: 409,
      message: "Email already registered",
    });
  });

  it("returns undefined on 204 No Content", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status: 204, ok: true } as Response));
    await expect(api.del("/cart/items/1")).resolves.toBeUndefined();
  });

  it("ApiError carries the status code", () => {
    expect(new ApiError(503, "down").status).toBe(503);
  });
});
