def test_register_then_login(client):
    r = client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "password123", "full_name": "A"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["token_type"] == "bearer"

    r = client.post("/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_duplicate_email_rejected(client):
    body = {"email": "dup@example.com", "password": "password123"}
    assert client.post("/auth/register", json=body).status_code == 201
    assert client.post("/auth/register", json=body).status_code == 409


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "b@example.com", "password": "password123"})
    r = client.post("/auth/login", json={"email": "b@example.com", "password": "wrongpass1"})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "c@example.com", "password": "short"})
    assert r.status_code == 422


def test_me_requires_auth(client):
    assert client.get("/users/me").status_code == 401


def test_profile_crud(client, auth_headers):
    r = client.get("/users/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "shopper@example.com"

    r = client.put("/users/me", headers=auth_headers, json={"display_name": "Sammy"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "Sammy"
