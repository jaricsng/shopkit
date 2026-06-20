import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, formatPrice, type CheckoutResult } from "../api/client";

// The backend creates a Stripe (test-mode) PaymentIntent and returns its
// client_secret — or a stub when no STRIPE_SECRET_KEY is set, so the flow
// completes offline. Wiring Stripe Elements with the client_secret +
// VITE_STRIPE_PUBLISHABLE_KEY is a documented next step (see the lab's Stripe
// asset); for the reference we confirm the order server-side.
export function Checkout() {
  const navigate = useNavigate();
  const [result, setResult] = useState<CheckoutResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const placeOrder = async () => {
    setError("");
    setBusy(true);
    try {
      setResult(await api.post<CheckoutResult>("/checkout"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setBusy(false);
    }
  };

  if (result) {
    return (
      <div className="container form-narrow">
        <h2>Order placed 🎉</h2>
        <div className="notice">
          <p>Order <strong>#{result.order_id}</strong> — {formatPrice(result.total_cents)}</p>
          <p className="muted">Status: {result.status}</p>
          {result.client_secret?.startsWith("pi_stub") && (
            <p className="muted">
              (Stripe not configured — this is a stub PaymentIntent. Set
              STRIPE_SECRET_KEY to create a real test-mode intent.)
            </p>
          )}
        </div>
        <button onClick={() => navigate("/catalog")}>Keep shopping</button>
      </div>
    );
  }

  return (
    <div className="container form-narrow">
      <h2>Checkout</h2>
      <p className="muted">Confirm your order. Payment runs against Stripe test mode.</p>
      {error && <p className="error">{error}</p>}
      <button onClick={placeOrder} disabled={busy}>{busy ? "Placing…" : "Place order"}</button>
    </div>
  );
}
