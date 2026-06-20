import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import { Catalog } from "./Catalog";

const PRODUCTS = {
  items: [
    { id: 1, name: "Aurora Desk Lamp", description: "warm light", price_cents: 4200, category: "home", image_url: "", stock: 5 },
    { id: 2, name: "Espresso Beans", description: "coffee", price_cents: 1800, category: "grocery", image_url: "", stock: 9 },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

describe("Catalog", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ status: 200, ok: true, json: async () => PRODUCTS } as Response),
    );
  });
  afterEach(() => localStorage.clear());

  it("renders products from the API with prices", async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Catalog />
        </AuthProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText("Aurora Desk Lamp")).toBeInTheDocument();
    expect(screen.getByText("Espresso Beans")).toBeInTheDocument();
    expect(screen.getByText("$42.00")).toBeInTheDocument();
    expect(screen.getByText("2 products")).toBeInTheDocument();
  });
});
