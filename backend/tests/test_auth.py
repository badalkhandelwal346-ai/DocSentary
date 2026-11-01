from backend.app.core.security import decode_access_token


def test_direct_login_and_me_endpoint(client):
    # 1. Direct login
    resp = client.post("/api/v1/auth/direct", json={"username": "devuser"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "devuser"
    assert data["user"]["organization"] is not None

    token = data["access_token"]
    payload = decode_access_token(token)
    assert payload["username"] == "devuser"

    # 2. Call /auth/me with token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "devuser"
    assert me_data["organization"]["slug"] == "devuser-workspace"

    # 3. Call /auth/logout
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "logged_out"


def test_unauthenticated_requests_fail(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "Missing authentication credentials" in resp.json()["detail"]


def test_github_oauth_honest_unconfigured_state(client):
    # When GitHub credentials are not configured, server must return honest 503
    resp = client.post("/api/v1/auth/github", json={"code": "dummy_code"})
    assert resp.status_code == 503
    assert "GitHub OAuth is not configured" in resp.json()["detail"]
