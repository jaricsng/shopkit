def test_browse_and_search(client, seeded_products):
    r = client.get("/products")
    assert r.status_code == 200
    assert r.json()["total"] == 3

    r = client.get("/products", params={"q": "coffee"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert "Espresso" in items[0]["name"]

    r = client.get("/products", params={"category": "home"})
    assert r.json()["total"] == 1


def test_pagination(client, seeded_products):
    r = client.get("/products", params={"page": 1, "page_size": 2})
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_cart_flow(client, seeded_products, auth_headers):
    pid = seeded_products[0].id
    r = client.post("/cart/items", headers=auth_headers, json={"product_id": pid, "quantity": 2})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_cents"] == seeded_products[0].price_cents * 2

    r = client.get("/cart", headers=auth_headers)
    assert len(r.json()["items"]) == 1

    item_id = r.json()["items"][0]["id"]
    r = client.delete(f"/cart/items/{item_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_cart_requires_auth(client, seeded_products):
    assert client.get("/cart").status_code == 401


def test_add_unknown_product(client, auth_headers):
    r = client.post("/cart/items", headers=auth_headers, json={"product_id": 9999, "quantity": 1})
    assert r.status_code == 404


def test_checkout(client, seeded_products, auth_headers):
    pid = seeded_products[1].id
    client.post("/cart/items", headers=auth_headers, json={"product_id": pid, "quantity": 1})
    r = client.post("/checkout", headers=auth_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_cents"] == seeded_products[1].price_cents
    assert body["status"] == "pending"
    assert body["client_secret"]  # stub secret when no Stripe key configured
    # cart emptied after checkout
    assert client.get("/cart", headers=auth_headers).json()["items"] == []


def test_checkout_empty_cart(client, auth_headers):
    r = client.post("/checkout", headers=auth_headers)
    assert r.status_code == 400
