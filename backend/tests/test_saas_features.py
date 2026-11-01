import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_signup_and_login_flow():
    # 1. Signup new user with unique username
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"user_{unique_suffix}"
    email = f"{username}@example.com"
    signup_payload = {
        "email": email,
        "username": username,
        "password": "strongPassword123!",
        "full_name": "Test User SaaS",
    }
    res = client.post("/api/v1/auth/signup", json=signup_payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == username
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Login with credentials
    login_payload = {
        "username_or_email": username,
        "password": "strongPassword123!",
    }
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data

    # 3. Check onboarding status
    res_onb = client.get("/api/v1/users/onboarding", headers=headers)
    assert res_onb.status_code == 200
    onb_data = res_onb.json()
    assert onb_data["onboarding_completed"] is False
    assert onb_data["onboarding_step"] == 1

    # 4. Update onboarding step
    res_patch = client.patch(
        "/api/v1/users/onboarding",
        json={"onboarding_step": 3, "onboarding_completed": False},
        headers=headers,
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["onboarding_step"] == 3

    # 5. Check evaluations endpoint
    res_eval = client.get("/api/v1/evaluations", headers=headers)
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert "items" in eval_data
    assert eval_data["total"] >= 1
    assert round(eval_data["items"][0]["accuracy"], 3) == 0.781

    # 6. Check GitHub status endpoint
    res_gh = client.get("/api/v1/github/status", headers=headers)
    assert res_gh.status_code == 200
    gh_data = res_gh.json()
    assert "is_connected" in gh_data
