// Thin fetch wrapper. The token is read from localStorage on each call so it
// stays in sync with login/logout. Base URL defaults to the Vite proxy (/api).
const BASE = import.meta.env.VITE_API_BASE ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers ?? {}),
    },
  });
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (body as { detail?: string }).detail ?? res.statusText;
    throw new ApiError(res.status, detail);
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(data ?? {}) }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(data ?? {}) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// --- Shared types (mirror the backend schemas) ---
export interface Product {
  id: number;
  name: string;
  description: string;
  price_cents: number;
  category: string;
  image_url: string;
  stock: number;
}
export interface ProductList {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
}
export interface User {
  id: number;
  email: string;
  full_name: string;
  display_name: string | null;
  is_admin: boolean;
}
export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
  line_total_cents: number;
}
export interface Cart {
  items: CartItem[];
  total_cents: number;
}
export interface CheckoutResult {
  order_id: number;
  total_cents: number;
  status: string;
  client_secret: string | null;
}

export const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`;
