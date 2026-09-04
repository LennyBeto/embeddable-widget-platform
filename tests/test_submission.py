def test_valid_submission_is_stored(client, owner_and_widget):
    widget_id = owner_and_widget["widget_id"]
    resp = client.post(f"/widgets/{widget_id}/submissions", json={
        "data": {"email": "visitor@example.com"}, "hp_field": "",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["email"] == "visitor@example.com"
    assert body["email_side_effect_status"] in ("sent", "failed")


def test_missing_required_field_returns_422(client, owner_and_widget):
    widget_id = owner_and_widget["widget_id"]
    resp = client.post(f"/widgets/{widget_id}/submissions", json={"data": {}, "hp_field": ""})
    assert resp.status_code == 422


def test_oversized_payload_returns_422(client, owner_and_widget):
    widget_id = owner_and_widget["widget_id"]
    resp = client.post(f"/widgets/{widget_id}/submissions", json={
        "data": {"email": "x" * 5000}, "hp_field": "",
    })
    assert resp.status_code == 422


def test_honeypot_filled_rejects_submission(client, owner_and_widget):
    widget_id = owner_and_widget["widget_id"]
    resp = client.post(f"/widgets/{widget_id}/submissions", json={
        "data": {"email": "bot@example.com"}, "hp_field": "i-am-a-bot",
    })
    assert resp.status_code == 400


def test_unknown_widget_returns_404(client):
    resp = client.post("/widgets/00000000-0000-0000-0000-000000000000/submissions", json={
        "data": {"email": "x@example.com"}, "hp_field": "",
    })
    assert resp.status_code == 404


def test_tenant_isolation_on_widget_routes(client, owner_and_widget):
    # A second tenant must not be able to read the first tenant's widget.
    signup2 = client.post("/auth/signup", json={
        "tenant_name": "Other Co", "email": "other@test.com", "password": "supersecret123",
    })
    other_headers = {"Authorization": f"Bearer {signup2.json()['access_token']}"}

    widget_id = owner_and_widget["widget_id"]
    resp = client.get(f"/widgets/{widget_id}", headers=other_headers)
    assert resp.status_code == 404


def test_dashboard_shows_submission(client, owner_and_widget):
    widget_id = owner_and_widget["widget_id"]
    client.post(f"/widgets/{widget_id}/submissions", json={
        "data": {"email": "visitor@example.com"}, "hp_field": "",
    })
    resp = client.get("/dashboard/stats", headers=owner_and_widget["headers"])
    assert resp.status_code == 200
    assert resp.json()["total_submissions"] >= 1
