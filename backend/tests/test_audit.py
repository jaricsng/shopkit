"""Audit-logging tests — security events are emitted to the shopkit.audit logger."""

import json
import logging


def _audit_events(caplog):
    out = []
    for r in caplog.records:
        if r.name == "shopkit.audit":
            out.append(json.loads(r.getMessage()))
    return out


def test_register_and_login_emit_audit(client, caplog):
    with caplog.at_level(logging.INFO, logger="shopkit.audit"):
        client.post("/auth/register", json={"email": "a@example.com", "password": "password123"})
        client.post("/auth/login", json={"email": "a@example.com", "password": "password123"})
    events = _audit_events(caplog)
    kinds = {(e["event"], e["outcome"]) for e in events}
    assert ("user.register", "success") in kinds
    assert ("auth.login", "success") in kinds
    # the actor is recorded, never the password
    assert all("password" not in json.dumps(e) for e in events)


def test_failed_login_is_audited_as_failure(client, caplog):
    client.post("/auth/register", json={"email": "b@example.com", "password": "password123"})
    with caplog.at_level(logging.INFO, logger="shopkit.audit"):
        client.post("/auth/login", json={"email": "b@example.com", "password": "wrongpass1"})
    events = _audit_events(caplog)
    assert any(e["event"] == "auth.login" and e["outcome"] == "failure" for e in events)


def test_checkout_emits_audit(client, seeded_products, auth_headers, caplog):
    pid = seeded_products[0].id
    client.post("/cart/items", headers=auth_headers, json={"product_id": pid, "quantity": 1})
    with caplog.at_level(logging.INFO, logger="shopkit.audit"):
        client.post("/checkout", headers=auth_headers)
    events = _audit_events(caplog)
    assert any(e["event"] == "checkout" and "order_id" in e for e in events)
