#!/usr/bin/env bash
# =============================================================================
# Manual Penetration Test Checks — OWASP Top 10 — adapted for ShopKit.
#
# AUTHORIZATION NOTICE: Run this ONLY against your own running instance.
# Unauthorised testing of systems you do not own is illegal in most places.
#
# Usage:
#   ./security/manual-checks.sh http://localhost:8000
#
# Two severities:
#   FAIL (❌)  — a real vulnerability (authz/auth/injection/business-logic).
#               Exits non-zero. For the ShopKit reference this should be 0.
#   WARN (⚠️)  — missing defence-in-depth (security headers, rate limiting,
#               security.txt, body-size limits). ShopKit deliberately omits
#               these as a minimal teaching app — they're REQUIRED in production.
#               See SECURITY-FINDINGS.md. WARN does not fail the run.
#
# ShopKit surfaces this targets: /auth/*, /users/me, /products, /cart, /checkout.
# Adapt the ENDPOINTS block to your own API.
# =============================================================================

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0
WARN=0

# ─── ENDPOINTS — adjust to your API ─────────────────────────────────────────
AUTH_REGISTER="/auth/register"
AUTH_LOGIN="/auth/login"
AUTH_LOGOUT="/auth/logout"
PROFILE="/users/me"          # owned, token-scoped (no /users/{id} → no IDOR by id)
PRODUCTS="/products"         # public catalog
CART="/cart"                 # owned cart
CART_ITEMS="/cart/items"     # owned cart items
CHECKOUT="/checkout"
HEALTH="/health"
READY="/ready"
METRICS="/metrics"

_pass() { echo "  ✅  PASS — $1"; ((PASS++)); }
_fail() { echo "  ❌  FAIL — $1"; ((FAIL++)); }
_warn() { echo "  ⚠️   WARN — $1"; ((WARN++)); }
_info() { echo ""; echo "── $1 ──────────────────────────────────────────"; }
_json() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)" 2>/dev/null; }

echo ""
echo "ShopKit — Manual Penetration Test Checks"
echo "Target: $BASE_URL"
echo "================================================================="

# Two users + tokens
EMAIL_A="pentest_a_$(date +%s)@example.com"
EMAIL_B="pentest_b_$(date +%s)@example.com"
for e in "$EMAIL_A" "$EMAIL_B"; do
  curl -sf -X POST "$BASE_URL$AUTH_REGISTER" -H "Content-Type: application/json" \
    -d "{\"email\":\"$e\",\"full_name\":\"PenTest\",\"password\":\"PenTest123!\"}" >/dev/null
done
TOKEN_A=$(curl -sf -X POST "$BASE_URL$AUTH_LOGIN" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL_A\",\"password\":\"PenTest123!\"}" | _json "['access_token']")
TOKEN_B=$(curl -sf -X POST "$BASE_URL$AUTH_LOGIN" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL_B\",\"password\":\"PenTest123!\"}" | _json "['access_token']")
PID=$(curl -sf "$BASE_URL$PRODUCTS?page_size=1" | _json "['items'][0]['id']")

# ─── A01: Broken Access Control ──────────────────────────────────────────────
_info "A01 — Broken Access Control"

# Unauthenticated access to owned resources
for path in "$PROFILE" "$CART"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$path")
  if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
    _pass "Unauthenticated GET $path returns $STATUS"
  else
    _fail "Unauthenticated GET $path returned $STATUS (expected 401)"
  fi
done

# Object-level authz / IDOR: B must not touch A's cart item
if [ -n "$TOKEN_A" ] && [ -n "$TOKEN_B" ] && [ -n "$PID" ]; then
  curl -s -o /dev/null -X POST "$BASE_URL$CART_ITEMS" \
    -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
    -d "{\"product_id\":$PID,\"quantity\":1}"
  A_ITEM=$(curl -sf "$BASE_URL$CART" -H "Authorization: Bearer $TOKEN_A" | _json "['items'][0]['id']")
  if [ -n "$A_ITEM" ]; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
      -H "Authorization: Bearer $TOKEN_B" "$BASE_URL$CART_ITEMS/$A_ITEM")
    if [ "$STATUS" = "404" ] || [ "$STATUS" = "403" ]; then
      _pass "IDOR: User B cannot delete User A's cart item (HTTP $STATUS)"
    else
      _fail "IDOR: User B got HTTP $STATUS deleting User A's cart item — broken object-level authz"
    fi
  fi
  # A's cart must not leak into B's cart
  B_COUNT=$(curl -sf "$BASE_URL$CART" -H "Authorization: Bearer $TOKEN_B" | _json "['items'].__len__()")
  if [ "$B_COUNT" = "0" ]; then
    _pass "Cart isolation: User A's items do not appear in User B's cart"
  else
    _fail "Cart isolation: User B sees $B_COUNT item(s) — cross-user data exposure"
  fi
else
  _warn "A01 IDOR setup incomplete (registration/login/product lookup failed) — skipped"
fi

# ─── A02: Cryptographic / Token Failures ─────────────────────────────────────
_info "A02 — Authentication Token Integrity"

NONE_TOKEN="eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIn0."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $NONE_TOKEN" "$BASE_URL$PROFILE")
[ "$STATUS" = "401" ] && _pass "JWT alg:none rejected ($STATUS)" || _fail "JWT alg:none accepted ($STATUS) — auth bypass"

TAMPERED="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdHRhY2tlciJ9.INVALIDSIGNATURE"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TAMPERED" "$BASE_URL$PROFILE")
[ "$STATUS" = "401" ] && _pass "Tampered JWT rejected ($STATUS)" || _fail "Tampered JWT accepted ($STATUS) — signature check broken"

# ─── A03: Injection ───────────────────────────────────────────────────────────
_info "A03 — Injection"

# SQL injection probe in the catalog search (parameterized query → treated as data)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$PRODUCTS?q=%27%20OR%20%271%27%3D%271")
if [ "$STATUS" = "200" ]; then
  _pass "SQLi probe in $PRODUCTS?q= handled as data (HTTP $STATUS, no 500)"
else
  _fail "SQLi probe returned HTTP $STATUS — investigate (a 500 suggests SQL executed)"
fi

# XSS payload stored via profile update — API returns JSON, so it's data not markup
if [ -n "$TOKEN_A" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL$PROFILE" \
    -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" \
    -d '{"display_name":"<script>alert(1)</script>"}')
  if [ "$STATUS" = "200" ] || [ "$STATUS" = "422" ]; then
    _pass "XSS payload in display_name handled safely (HTTP $STATUS; API serves JSON)"
  else
    _fail "XSS probe returned HTTP $STATUS — investigate"
  fi
fi

# ─── A04: Insecure Design / Business Logic ───────────────────────────────────
_info "A04 — Business Logic"

if [ -n "$TOKEN_B" ]; then
  # Checkout with an empty cart must be rejected (B's cart is empty)
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$CHECKOUT" -H "Authorization: Bearer $TOKEN_B")
  [ "$STATUS" = "400" ] && _pass "Checkout with empty cart rejected (400)" || _fail "Empty-cart checkout returned $STATUS (expected 400)"

  # Quantity tampering: schema must reject out-of-range quantity
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$CART_ITEMS" \
    -H "Authorization: Bearer $TOKEN_B" -H "Content-Type: application/json" \
    -d "{\"product_id\":$PID,\"quantity\":-5}")
  [ "$STATUS" = "422" ] && _pass "Negative quantity rejected (422)" || _fail "Negative quantity returned $STATUS (expected 422)"

  # Adding a non-existent product must 404 (no orphan cart rows)
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$CART_ITEMS" \
    -H "Authorization: Bearer $TOKEN_B" -H "Content-Type: application/json" \
    -d '{"product_id":999999,"quantity":1}')
  [ "$STATUS" = "404" ] && _pass "Add non-existent product rejected (404)" || _fail "Adding bogus product returned $STATUS (expected 404)"
fi

# ─── A07: Authentication Failures ─────────────────────────────────────────────
_info "A07 — Authentication Failures"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$AUTH_REGISTER" \
  -H "Content-Type: application/json" -d "{\"email\":\"weak_$(date +%s)@example.com\",\"password\":\"123\"}")
[ "$STATUS" = "422" ] && _pass "Weak password '123' rejected (422)" || _fail "Weak password accepted ($STATUS) — no min length"

# User enumeration: identical response for wrong-password vs unknown-email
R1=$(curl -s -X POST "$BASE_URL$AUTH_LOGIN" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL_A\",\"password\":\"wrongpass1\"}")
R2=$(curl -s -X POST "$BASE_URL$AUTH_LOGIN" -H "Content-Type: application/json" -d '{"email":"nobody@example.com","password":"wrongpass1"}')
[ "$R1" = "$R2" ] && _pass "Login errors identical (no user enumeration)" || _fail "Login responses differ — user enumeration possible"

# ─── A05/A09: Hardening & Misconfiguration (advisory for the teaching app) ────
_info "A05 — Security Misconfiguration (defence-in-depth)"

# Strict CORS IS enforced by ShopKit (allow_origins is an explicit list) — hard check
CORS=$(curl -sI -X OPTIONS "$BASE_URL$PRODUCTS" -H "Origin: https://evil.example.com" \
  -H "Access-Control-Request-Method: GET" | grep -i "access-control-allow-origin")
if echo "$CORS" | grep -q "evil.example.com"; then
  _fail "CORS reflects evil.example.com — tighten allow_origins"
else
  _pass "CORS does not reflect an arbitrary origin"
fi

# The following are defence-in-depth ShopKit omits as a teaching app → WARN.
HEADERS=$(curl -sI "$BASE_URL$HEALTH")
for h in "x-content-type-options" "x-frame-options" "strict-transport-security" "content-security-policy" "referrer-policy"; do
  echo "$HEADERS" | grep -qi "$h" && _pass "Security header $h present" || _warn "Security header $h missing — add a security-headers middleware in production"
done
echo "$HEADERS" | grep -qiE "^server:.*(uvicorn|python)" && _warn "Server header discloses the stack — strip it at the proxy in production" || _pass "Server header does not disclose the stack"

# Rate limiting on login (ShopKit has none → WARN)
LIMITED=0
for i in $(seq 1 25); do
  S=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL$AUTH_LOGIN" \
    -H "Content-Type: application/json" -d "{\"email\":\"rl$i@example.com\",\"password\":\"x\"}")
  [ "$S" = "429" ] && { LIMITED=1; break; }
done
[ "$LIMITED" = "1" ] && _pass "Login rate limiting active (429 observed)" || _warn "No login rate limiting — add one at the gateway/proxy in production"

# ─── Governance / Observability (hard) ────────────────────────────────────────
_info "Governance & Observability"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$READY")
[ "$STATUS" = "200" ] && _pass "Readiness GET $READY → 200" || _fail "Readiness $READY → $STATUS"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL$METRICS")
[ "$STATUS" = "200" ] && _pass "Metrics GET $METRICS → 200" || _fail "Metrics $METRICS → $STATUS (is OTel enabled?)"

# Logout + account deletion on a throwaway user
DEL_EMAIL="del_$(date +%s)@example.com"
curl -sf -X POST "$BASE_URL$AUTH_REGISTER" -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEL_EMAIL\",\"password\":\"DelTest123!\"}" >/dev/null
DEL_TOKEN=$(curl -sf -X POST "$BASE_URL$AUTH_LOGIN" -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEL_EMAIL\",\"password\":\"DelTest123!\"}" | _json "['access_token']")
if [ -n "$DEL_TOKEN" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE -H "Authorization: Bearer $DEL_TOKEN" "$BASE_URL$PROFILE")
  if [ "$STATUS" = "204" ]; then
    _pass "Account deletion DELETE $PROFILE → 204"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $DEL_TOKEN" "$BASE_URL$PROFILE")
    [ "$STATUS" = "401" ] && _pass "Deleted user's token rejected (401)" || _fail "Deleted user's token still works ($STATUS)"
  else
    _fail "Account deletion returned $STATUS (expected 204)"
  fi
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "================================================================="
echo "  Pen Test Summary"
echo "  PASS: $PASS   WARN: $WARN   FAIL: $FAIL"
echo "================================================================="
echo ""
if [ "$WARN" -gt 0 ]; then
  echo "  ⚠️   $WARN advisory finding(s): defence-in-depth ShopKit omits as a"
  echo "      teaching app. Required for production — tracked in SECURITY-FINDINGS.md."
fi
if [ "$FAIL" -gt 0 ]; then
  echo "  ❌  $FAIL vulnerability check(s) failed — fix, or document accepted risk."
  exit 1
fi
echo "  ✅  No vulnerabilities found (authz/auth/injection/business-logic)."
exit 0
