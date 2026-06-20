# ShopKit frontend

React + TypeScript (Vite), light theme. The reference storefront UI.

## Pages
- **Dashboard** (`/`) — welcome + stat tiles (catalog size, cart count/total)
- **Catalog** (`/catalog`) — browse + search, add to cart
- **Login / Register** — JWT auth (token in `localStorage`)
- **Cart** (`/cart`) — review + remove items, go to checkout
- **Checkout** (`/checkout`) — places the order (Stripe test mode / offline stub)
- **Profile** (`/profile`) — edit full name / display name

A `Navbar` is shown on every page; protected routes use a `RequireAuth` guard.

## Develop
```bash
npm install
cp .env.example .env      # optional; defaults work with the Vite proxy
npm run dev               # http://localhost:5173 (proxies /api -> :8000)
```
Run the backend (`docker compose up -d` one level up) so `/api` resolves.

## Quality gates (Module 03)
```bash
npm run lint              # eslint (flat config)
npm run build             # tsc -b && vite build (type-check + bundle)
```

## Stripe Elements (documented enhancement)
Checkout currently confirms the order server-side and shows the PaymentIntent
result. To take a real test-mode payment in the browser, add
`@stripe/stripe-js` + `@stripe/react-stripe-js`, set
`VITE_STRIPE_PUBLISHABLE_KEY` (`pk_test_…`), and mount a `PaymentElement` with
the `client_secret` the backend returns. See the lab's `assets/stripe-webhook/`
for the matching server-side confirmation path.

> Teaching artifact — CORS is permissive and error handling is minimal by design.
