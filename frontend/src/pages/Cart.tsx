import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, formatPrice, type Cart as CartData } from "../api/client";

export function Cart() {
  const navigate = useNavigate();
  const [cart, setCart] = useState<CartData | null>(null);

  const load = useCallback(async () => {
    setCart(await api.get<CartData>("/cart"));
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const remove = async (itemId: number) => {
    await api.del(`/cart/items/${itemId}`);
    await load();
  };

  if (!cart) return <div className="container">Loading…</div>;

  return (
    <div className="container">
      <h2>Your cart</h2>
      {cart.items.length === 0 ? (
        <p className="muted">Your cart is empty.</p>
      ) : (
        <>
          <table>
            <thead>
              <tr><th>Product</th><th>Qty</th><th>Line total</th><th></th></tr>
            </thead>
            <tbody>
              {cart.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.product.name}</td>
                  <td>{item.quantity}</td>
                  <td>{formatPrice(item.line_total_cents)}</td>
                  <td><button className="link" onClick={() => remove(item.id)}>Remove</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="row" style={{ marginTop: 16, justifyContent: "space-between" }}>
            <strong>Total: {formatPrice(cart.total_cents)}</strong>
            <button onClick={() => navigate("/checkout")}>Checkout</button>
          </div>
        </>
      )}
    </div>
  );
}
