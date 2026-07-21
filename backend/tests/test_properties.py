"""
tests/test_properties.py
Property endpoint tests — aligned with V001__realty_os_full_schema.sql schema.

Key schema changes from old flat design:
  - PropertyCreate now requires a nested `location` object (LocationCreate)
  - Residential-specific fields go inside a nested `residential` object
  - asking_price (was base_price)
  - listing_status (was status)
  - transaction_type (was listing_type) with uppercase values
  - property_type is uppercase: RESIDENTIAL, COMMERCIAL, etc.
  - is_verified (was verified)
  - views_count (was view_count)
"""
import pytest
from fastapi.testclient import TestClient


# ── Shared fixture ────────────────────────────────────────────────────────────

PROPERTY_PAYLOAD = {
    "title": "2BHK Sea-Facing Apartment",
    "property_type": "RESIDENTIAL",
    "transaction_type": "SALE",
    "asking_price": 8500000.0,
    "description": "Beautiful sea-facing apartment.",
    "carpet_area_sqft": 750.0,
    "built_up_area_sqft": 850.0,
    "super_built_up": 950.0,
    "location": {
        "address_line_1": "101 Marine Drive",
        "locality": "Marine Lines",
        "city": "Mumbai",
        "state_code": "MH",
        "pin_code": "400002",
    },
    "residential": {
        "bhk_type": "2BHK",
        "num_bedrooms": 2,
        "num_bathrooms": 2,
        "furnishing_status": "SEMI_FURNISHED",
        "possession_status": "READY_TO_MOVE",
        "parking_covered": 1,
        "parking_open": 0,
        "is_vastu_compliant": False,
    },
}


def create_property(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {**PROPERTY_PAYLOAD, **overrides}
    r = client.post("/api/v1/properties/", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateProperty:
    def test_create_success(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post("/api/v1/properties/", json=PROPERTY_PAYLOAD, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "2BHK Sea-Facing Apartment"
        assert data["property_type"] == "RESIDENTIAL"
        assert data["transaction_type"] == "SALE"
        assert data["asking_price"] == 8500000.0
        # Nested location should be returned
        assert data["location"]["city"] == "Mumbai"
        assert data["location"]["state_code"] == "MH"

    def test_create_requires_auth(self, client: TestClient):
        r = client.post("/api/v1/properties/", json=PROPERTY_PAYLOAD)
        assert r.status_code == 401

    def test_create_missing_required_field(self, client: TestClient, normal_user):
        """Missing `location` object → 422."""
        _, headers = normal_user
        bad = {k: v for k, v in PROPERTY_PAYLOAD.items() if k != "location"}
        r = client.post("/api/v1/properties/", json=bad, headers=headers)
        assert r.status_code == 422

    def test_create_commercial_property(self, client: TestClient, normal_user):
        _, headers = normal_user
        payload = {
            "title": "BKC Commercial Office",
            "property_type": "COMMERCIAL",
            "transaction_type": "LEASE",
            "asking_price": 25000000.0,
            "location": {
                "address_line_1": "1 BKC Tower",
                "locality": "BKC",
                "city": "Mumbai",
                "state_code": "MH",
                "pin_code": "400051",
            },
        }
        r = client.post("/api/v1/properties/", json=payload, headers=headers)
        assert r.status_code == 201
        assert r.json()["property_type"] == "COMMERCIAL"


# ── List / filter ─────────────────────────────────────────────────────────────

class TestListProperties:
    def test_list_returns_active_only(self, client: TestClient, normal_user):
        _, headers = normal_user
        create_property(client, headers)
        r = client.get("/api/v1/properties/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        for p in r.json():
            assert p["listing_status"] == "ACTIVE"

    def test_filter_by_price_max(self, client: TestClient, normal_user):
        _, headers = normal_user
        create_property(client, headers, asking_price=5000000.0)
        create_property(client, headers, asking_price=20000000.0)
        r = client.get("/api/v1/properties/?price_max=10000000")
        assert r.status_code == 200
        for p in r.json():
            assert p["asking_price"] <= 10000000

    def test_filter_by_city(self, client: TestClient, normal_user):
        _, headers = normal_user
        create_property(client, headers)
        r = client.get("/api/v1/properties/?city=Mumbai")
        assert r.status_code == 200
        assert all(p["location"]["city"] == "Mumbai" for p in r.json())

    def test_pagination(self, client: TestClient, normal_user):
        _, headers = normal_user
        for _ in range(3):
            create_property(client, headers)
        r = client.get("/api/v1/properties/?page=1&page_size=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2


# ── Get ───────────────────────────────────────────────────────────────────────

class TestGetProperty:
    def test_get_by_id(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        r = client.get(f"/api/v1/properties/{prop['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == prop["id"]

    def test_get_not_found(self, client: TestClient):
        r = client.get("/api/v1/properties/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdateProperty:
    def test_update_own_listing(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        r = client.patch(
            f"/api/v1/properties/{prop['id']}",
            json={"asking_price": 9500000.0, "description": "Updated description"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["asking_price"] == 9500000.0

    def test_update_forbidden_for_other_user(self, client: TestClient, normal_user, admin_user):
        _, user_headers = normal_user
        _, admin_headers = admin_user
        prop = create_property(client, user_headers)
        # Create a different non-admin user
        r2 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "other2@example.com",
                "full_name": "Other Two",
                "password": "Secret123",
            },
        )
        assert r2.status_code == 201
        tok = client.post(
            "/api/v1/auth/login",
            json={"email": "other2@example.com", "password": "Secret123"},
        ).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {tok}"}
        r = client.patch(
            f"/api/v1/properties/{prop['id']}",
            json={"asking_price": 1.0},
            headers=other_headers,
        )
        assert r.status_code == 403


# ── Delete (soft) ─────────────────────────────────────────────────────────────

class TestDeleteProperty:
    def test_soft_delete(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        r = client.delete(f"/api/v1/properties/{prop['id']}", headers=headers)
        assert r.status_code == 204
        # Should no longer show in ACTIVE listings
        r2 = client.get("/api/v1/properties/")
        ids = [p["id"] for p in r2.json()]
        assert prop["id"] not in ids


# ── View counter ──────────────────────────────────────────────────────────────

class TestViewCounter:
    def test_increment_view(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        initial_views = prop.get("views_count", 0)
        r = client.post(f"/api/v1/properties/{prop['id']}/view")
        assert r.status_code == 204
        r2 = client.get(f"/api/v1/properties/{prop['id']}")
        assert r2.json()["views_count"] == initial_views + 1


# ── Verify (admin) ────────────────────────────────────────────────────────────

class TestVerifyProperty:
    def test_verify_as_admin(self, client: TestClient, normal_user, admin_user):
        _, user_headers = normal_user
        _, admin_headers = admin_user
        prop = create_property(client, user_headers)
        assert prop.get("is_verified") is False
        r = client.patch(
            f"/api/v1/properties/{prop['id']}/verify",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_verified"] is True

    def test_verify_requires_admin(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        r = client.patch(
            f"/api/v1/properties/{prop['id']}/verify",
            headers=headers,
        )
        assert r.status_code == 403


# ── Feature (admin) ───────────────────────────────────────────────────────────

class TestFeatureProperty:
    def test_feature_as_admin(self, client: TestClient, normal_user, admin_user):
        _, user_headers = normal_user
        _, admin_headers = admin_user
        prop = create_property(client, user_headers)
        r = client.patch(
            f"/api/v1/properties/{prop['id']}/feature?featured=true",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_featured"] is True

    def test_unfeature_as_admin(self, client: TestClient, normal_user, admin_user):
        _, user_headers = normal_user
        _, admin_headers = admin_user
        prop = create_property(client, user_headers)
        r = client.patch(
            f"/api/v1/properties/{prop['id']}/feature?featured=false",
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_featured"] is False


# ── Media assets ──────────────────────────────────────────────────────────────

class TestMediaAsset:
    def test_add_media(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        r = client.post(
            f"/api/v1/properties/{prop['id']}/media",
            params={
                "url": "https://example.com/img.jpg",
                "asset_type": "IMAGE",
                "is_primary": True,
            },
            headers=headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert "asset_id" in data
        assert data["url"] == "https://example.com/img.jpg"

    def test_add_media_forbidden_for_non_owner(self, client: TestClient, normal_user):
        _, headers = normal_user
        prop = create_property(client, headers)
        r2 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "media_other@example.com",
                "full_name": "Media Other",
                "password": "Secret123",
            },
        )
        tok = client.post(
            "/api/v1/auth/login",
            json={"email": "media_other@example.com", "password": "Secret123"},
        ).json()["access_token"]
        r = client.post(
            f"/api/v1/properties/{prop['id']}/media",
            params={"url": "https://example.com/x.jpg", "asset_type": "IMAGE"},
            headers={"Authorization": f"Bearer {tok}"},
        )
        assert r.status_code == 403
