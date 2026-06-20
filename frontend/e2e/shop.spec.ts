import { expect, test } from "@playwright/test";

// End-to-end: a real browser drives the whole stack (nginx → API → Postgres).
// This is the top of the test pyramid — it would catch wiring failures that
// unit/integration tests can't (routing, the proxy, the build, CORS).

test("storefront loads and shows the catalog", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "ShopKit" })).toBeVisible();

  await page.getByRole("link", { name: "Catalog", exact: true }).click();
  await expect(page).toHaveURL(/\/catalog$/);
  // The seeded catalog renders at least one product card with a price.
  await expect(page.locator(".card").first()).toBeVisible();
  await expect(page.getByText(/\$\d+\.\d{2}/).first()).toBeVisible();
});

test("a shopper can register, add to cart, and check out", async ({ page }) => {
  const email = `e2e_${Date.now()}@example.com`;

  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password (min 8 chars)").fill("e2epassword123");
  await page.getByRole("button", { name: "Register" }).click();

  // Logged in → navbar shows the user and a Log out button.
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();

  // Add the first catalog item to the cart.
  await page.getByRole("link", { name: "Catalog", exact: true }).click();
  await page.getByRole("button", { name: "Add to cart" }).first().click();
  await expect(page.getByText("Added to cart")).toBeVisible();

  // Cart → checkout → order confirmation.
  await page.getByRole("link", { name: "Cart", exact: true }).click();
  await page.getByRole("button", { name: "Checkout" }).click();
  await page.getByRole("button", { name: "Place order" }).click();
  await expect(page.getByText(/Order placed/i)).toBeVisible();
});
