import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import { Navbar } from "./Navbar";

function renderNavbar() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <Navbar />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Navbar", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });
  afterEach(() => localStorage.clear());

  it("shows Log in / Register when logged out", async () => {
    // No token → AuthProvider resolves to no user without calling the API.
    renderNavbar();
    expect(await screen.findByRole("link", { name: "Log in" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Register" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Log out" })).not.toBeInTheDocument();
  });

  it("shows the user + Log out when authenticated", async () => {
    localStorage.setItem("token", "tok123");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => ({
          id: 1,
          email: "sam@example.com",
          full_name: "Sam",
          display_name: "Sammy",
          is_admin: false,
        }),
      } as Response),
    );
    renderNavbar();
    // After the /users/me fetch resolves, the navbar swaps to the signed-in view.
    expect(await screen.findByRole("button", { name: "Log out" })).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByRole("link", { name: "Sammy" })).toBeInTheDocument(),
    );
  });
});
