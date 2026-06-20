import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import { Login } from "./Login";

describe("Login", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });
  afterEach(() => localStorage.clear());

  it("shows the server's error message on bad credentials", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 401,
        ok: false,
        json: async () => ({ detail: "Invalid credentials" }),
      } as Response),
    );
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrongpass1" } });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
  });
});
