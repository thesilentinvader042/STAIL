"""
tests/test_auth.py
Authentication endpoint tests:
  register, login, refresh, logout, me, password change, password reset
"""
import pytest
from fastapi.testclient import TestClient

from .utils import register_and_login


# ── Register ─────────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "full_name": "New User",
                "password": "NewPass1",
                "role": "buyer",
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "buyer"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient):
        payload = {
            "email": "dup@example.com",
            "full_name": "Dup User",
            "password": "DupPass1",
            "role": "buyer",
        }
        client.post("/api/v1/auth/register", json=payload)
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 409
        assert "already exists" in r.json()["detail"].lower()

    def test_register_weak_password_rejected(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "full_name": "Weak User",
                "password": "short",  # < 8 chars
                "role": "buyer",
            },
        )
        assert r.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "full_name": "Bad Email",
                "password": "GoodPass1",
                "role": "buyer",
            },
        )
        assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "full_name": "Login User",
                "password": "LoginPass1",
                "role": "buyer",
            },
        )
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "LoginPass1"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800

    def test_login_wrong_password(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@example.com",
                "full_name": "Wrong PW",
                "password": "RealPass1",
                "role": "buyer",
            },
        )
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "WrongPass1"},
        )
        assert r.status_code == 401

    def test_login_unknown_email(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "AnyPass1"},
        )
        assert r.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

class TestMe:
    def test_me_authenticated(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.get("/api/v1/auth/me", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "buyer@example.com"

    def test_me_unauthenticated(self, client: TestClient):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401


# ── Refresh token ─────────────────────────────────────────────────────────────

class TestRefresh:
    def test_refresh_success(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "full_name": "Refresh User",
                "password": "RefreshPass1",
                "role": "buyer",
            },
        )
        login_r = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "RefreshPass1"},
        )
        refresh_token = login_r.json()["refresh_token"]

        r = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_refresh_invalid_token(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "totally.invalid.token"},
        )
        assert r.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_success(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post("/api/v1/auth/logout", headers=headers)
        assert r.status_code == 204

    def test_logout_unauthenticated(self, client: TestClient):
        r = client.post("/api/v1/auth/logout")
        assert r.status_code == 401


# ── Password change ───────────────────────────────────────────────────────────

class TestPasswordChange:
    def test_change_password_success(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "pwchange@example.com",
                "full_name": "PW Change",
                "password": "OldPass1",
                "role": "buyer",
            },
        )
        login_r = client.post(
            "/api/v1/auth/login",
            json={"email": "pwchange@example.com", "password": "OldPass1"},
        )
        headers = {"Authorization": f"Bearer {login_r.json()['access_token']}"}

        r = client.post(
            "/api/v1/auth/password/change",
            json={"current_password": "OldPass1", "new_password": "NewPass2"},
            headers=headers,
        )
        assert r.status_code == 204

    def test_change_password_wrong_current(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post(
            "/api/v1/auth/password/change",
            json={"current_password": "WrongOld1", "new_password": "NewPass2"},
            headers=headers,
        )
        assert r.status_code == 400


# ── Password reset ────────────────────────────────────────────────────────────

class TestPasswordReset:
    def test_reset_request_always_202(self, client: TestClient):
        # Should return 202 regardless of whether email exists (anti-enumeration)
        r = client.post(
            "/api/v1/auth/password/reset",
            json={"email": "nobody@example.com"},
        )
        assert r.status_code == 202

    def test_reset_confirm_invalid_token(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/password/confirm",
            json={"token": "bad.token.here", "new_password": "NewPass1"},
        )
        assert r.status_code == 400


# ── Health endpoints ──────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
