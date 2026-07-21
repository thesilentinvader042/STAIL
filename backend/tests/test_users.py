"""
tests/test_users.py
User endpoint tests:
  list (admin), get, update profile, deactivate, user properties, user leads
"""
import pytest
from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from utils import register_and_login


class TestGetUser:
    def test_get_own_profile(self, client: TestClient, normal_user):
        user, headers = normal_user
        r = client.get(f"/api/v1/users/{user['id']}", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "buyer@example.com"

    def test_cannot_view_other_user(self, client: TestClient, normal_user):
        _, headers = normal_user
        # Register a second user
        other, _ = register_and_login(
            client, email="other@example.com", password="OtherPass1"
        )
        r = client.get(f"/api/v1/users/{other['id']}", headers=headers)
        assert r.status_code == 403

    def test_unauthenticated_get(self, client: TestClient, normal_user):
        user, _ = normal_user
        r = client.get(f"/api/v1/users/{user['id']}")
        assert r.status_code == 401

    def test_get_nonexistent_user(self, client: TestClient, normal_user):
        _, headers = normal_user
        import uuid
        r = client.get(f"/api/v1/users/{uuid.uuid4()}", headers=headers)
        # Own user check fails first → 403 (not their own ID)
        assert r.status_code in (403, 404)


class TestUpdateUser:
    def test_update_own_profile(self, client: TestClient, normal_user):
        user, headers = normal_user
        r = client.patch(
            f"/api/v1/users/{user['id']}",
            json={"full_name": "Updated Name", "city": "Mumbai"},
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["full_name"] == "Updated Name"
        assert data["city"] == "Mumbai"

    def test_cannot_update_other_user(self, client: TestClient, normal_user):
        _, headers = normal_user
        other, _ = register_and_login(
            client, email="other2@example.com", password="OtherPass1"
        )
        r = client.patch(
            f"/api/v1/users/{other['id']}",
            json={"full_name": "Hacked"},
            headers=headers,
        )
        assert r.status_code == 403

    def test_update_language_preference(self, client: TestClient, normal_user):
        user, headers = normal_user
        r = client.patch(
            f"/api/v1/users/{user['id']}",
            json={"language_pref": "hi"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["language_pref"] == "hi"


class TestAdminListUsers:
    def test_admin_can_list_users(self, client: TestClient, admin_user):
        _, headers = admin_user
        r = client.get("/api/v1/users/", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_non_admin_cannot_list_users(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.get("/api/v1/users/", headers=headers)
        assert r.status_code == 403

    def test_admin_filter_by_role(self, client: TestClient, admin_user):
        _, headers = admin_user
        r = client.get("/api/v1/users/?role=buyer", headers=headers)
        assert r.status_code == 200
        for u in r.json():
            assert u["role"] == "buyer"


class TestDeactivateUser:
    def test_admin_can_deactivate(self, client: TestClient, admin_user):
        _, admin_headers = admin_user
        # Create a user to deactivate
        other, _ = register_and_login(
            client, email="todeactivate@example.com", password="DeactPass1"
        )
        r = client.delete(
            f"/api/v1/users/{other['id']}", headers=admin_headers
        )
        assert r.status_code == 204

    def test_non_admin_cannot_deactivate(self, client: TestClient, normal_user, admin_user):
        _, buyer_headers = normal_user
        admin_data, _ = admin_user
        r = client.delete(
            f"/api/v1/users/{admin_data['id']}", headers=buyer_headers
        )
        assert r.status_code == 403


class TestUserProperties:
    def test_user_properties_empty(self, client: TestClient, normal_user):
        user, headers = normal_user
        r = client.get(f"/api/v1/users/{user['id']}/properties", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_user_properties_after_creating(self, client: TestClient, normal_user):
        user, headers = normal_user
        # Create a property
        client.post(
            "/api/v1/properties/",
            json={
                "property_type": "residential",
                "listing_type": "sale",
                "address_line1": "123 Test Street",
                "locality": "Bandra",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pin_code": "400001",
                "base_price": 5000000.0,
            },
            headers=headers,
        )
        r = client.get(f"/api/v1/users/{user['id']}/properties", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestUserLeads:
    def test_user_leads_empty(self, client: TestClient, normal_user):
        user, headers = normal_user
        r = client.get(f"/api/v1/users/{user['id']}/leads", headers=headers)
        assert r.status_code == 200
        assert r.json() == []
