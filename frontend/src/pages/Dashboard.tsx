import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, formatPrice, type Cart, type ProductList } from "../api/client";
import { useAuth } from "../auth/context";

export function Dashboard() {
  const { user } = useAuth();
  const [catalogCount, setCatalogCount] = useState<number | null>(null);
  const [cartCount, setCartCount] = useState<number | null>(null);
  const [cartTotal, setCartTotal] = useState(0);

  useEffect(() => {
    void api.get<ProductList>("/products?page_size=1").then((d) => setCatalogCount(d.total));
    if (user) {
      void api.get<Cart>("/cart").then((c) => {
        setCartCount(c.items.reduce((n, i) => n + i.quantity, 0));
        setCartTotal(c.total_cents);
      });
    }
  }, [user]);

  return (
    <div className="container">
      <h2>Welcome{user ? `, ${user.display_name || user.full_name || user.email}` : " to ShopKit"}</h2>
      <p className="muted">A capstone reference storefront. Browse the catalog, fill a cart, check out.</p>

      <div className="stats">
        <div className="stat">
          <div className="value">{catalogCount ?? "…"}</div>
          <div className="label">Products in catalog</div>
        </div>
        {user && (
          <>
            <div className="stat">
              <div className="value">{cartCount ?? "…"}</div>
              <div className="label">Items in your cart</div>
            </div>
            <div className="stat">
              <div className="value">{formatPrice(cartTotal)}</div>
              <div className="label">Cart total</div>
            </div>
          </>
        )}
      </div>

      <div className="row">
        <Link to="/catalog"><button>Browse catalog</button></Link>
        {user && <Link to="/cart"><button className="secondary">View cart</button></Link>}
        {!user && <Link to="/register"><button className="secondary">Create an account</button></Link>}
      </div>
    </div>
  );
}
