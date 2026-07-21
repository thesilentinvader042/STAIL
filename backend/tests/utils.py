from fastapi.testclient import TestClient

def make_user_payload(
    email: str = "test@example.com",
    password: str = "TestPass1",
    role: str = "buyer",
    full_name: str = "Test User",
) -> dict:
    return {
        "email": email,
        "full_name": full_name,
        "password": password,
        "role": role,
    }

def register_and_login(client: TestClient, **kwargs) -> tuple[dict, dict]:
    """Register a user and return (user_json, auth_headers)."""
    payload = make_user_payload(**kwargs)
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text
    user = r.json()

    login_r = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login_r.status_code == 200, login_r.text
    token = login_r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers
