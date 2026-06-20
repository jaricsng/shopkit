import { useCallback, useEffect, useState } from "react";

import { api, formatPrice, type Product, type ProductList } from "../api/client";
import { useAuth } from "../auth/context";

export function Catalog() {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [q, setQ] = useState("");
  const [total, setTotal] = useState(0);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    const data = await api.get<ProductList>(`/products?${params.toString()}`);
    setProducts(data.items);
    setTotal(data.total);
  }, [q]);

  useEffect(() => {
    void load();
  }, [load]);

  const addToCart = async (productId: number) => {
    setMessage("");
    try {
      await api.post("/cart/items", { product_id: productId, quantity: 1 });
      setMessage("Added to cart");
    } catch {
      setMessage("Could not add to cart");
    }
  };

  return (
    <div className="container">
      <h2>Catalog</h2>
      <div className="toolbar">
        <input
          placeholder="Search products…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search products"
        />
      </div>
      {message && <div className="notice">{message}</div>}
      <p className="muted">{total} product{total === 1 ? "" : "s"}</p>
      <div className="grid">
        {products.map((p) => (
          <div className="card" key={p.id}>
            <h3>{p.name}</h3>
            <p className="muted">{p.description}</p>
            <p className="price">{formatPrice(p.price_cents)}</p>
            {user && <button onClick={() => addToCart(p.id)}>Add to cart</button>}
          </div>
        ))}
      </div>
    </div>
  );
}
