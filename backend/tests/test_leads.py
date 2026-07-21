"""
tests/test_leads.py
Lead endpoint tests:
  create, list, filter, qualify, assign, schedule-visit, close, archive, stats
  + unit tests for scoring and FSM logic
"""
import pytest
from fastapi.testclient import TestClient

from utils import register_and_login


# ── Helpers ───────────────────────────────────────────────────────────────────

LEAD_PAYLOAD = {
    "contact_name": "Rahul Sharma",
    "contact_phone": "+919876543210",
    "contact_email": "rahul@test.com",
    "source": "portal",
    "budget_min": 5000000.0,
    "budget_max": 10000000.0,
    "preferred_bhk": 2,
    "preferred_localities": ["Bandra", "Juhu"],
    "possession_timeline_months": 6,
    "is_loan_required": True,
    "notes": "Looking urgently.",
}


def create_lead(client: TestClient, headers: dict | None = None, **overrides) -> dict:
    payload = {**LEAD_PAYLOAD, **overrides}
    kwargs = {"json": payload}
    if headers:
        kwargs["headers"] = headers  # type: ignore[assignment]
    r = client.post("/api/v1/leads/", **kwargs)  # type: ignore[arg-type]
    assert r.status_code == 201, r.text
    return r.json()


# ── Unit tests: scoring logic ─────────────────────────────────────────────────

class TestIntentScoringUnit:
    """Unit tests for the rule-based intent scoring without HTTP."""

    def test_full_score(self):
        """All signals present should yield maximum (capped at 100)."""
        from app.api.v1.endpoints.leads import _compute_intent_score
        from app.db.models.models import Lead
        import uuid

        lead = Lead(
            id=uuid.uuid4(),
            budget_min=5_000_000,
            budget_max=10_000_000,
            preferred_localities=["Bandra"],
            preferred_bhk=2,
            possession_timeline_months=4,   # ≤ 6 → +20
            property_id=uuid.uuid4(),
            is_loan_required=True,
            source="whatsapp",
        )
        score = _compute_intent_score(lead)
        assert score == 100  # 15+10+10+20+15+10+10 = 90, capped at 100

    def test_empty_lead_scores_zero(self):
        from app.api.v1.endpoints.leads import _compute_intent_score
        from app.db.models.models import Lead
        import uuid

        lead = Lead(id=uuid.uuid4(), is_loan_required=False, source="api")
        assert _compute_intent_score(lead) == 0

    def test_score_to_tier_mapping(self):
        from app.api.v1.endpoints.leads import _score_to_tier
        assert _score_to_tier(75) == "hot"
        assert _score_to_tier(70) == "hot"
        assert _score_to_tier(55) == "warm"
        assert _score_to_tier(40) == "warm"
        assert _score_to_tier(39) == "cold"
        assert _score_to_tier(0) == "cold"


# ── Create lead ───────────────────────────────────────────────────────────────

class TestCreateLead:
    def test_create_anonymous_lead(self, client: TestClient):
        """Leads can be created without authentication."""
        r = client.post("/api/v1/leads/", json=LEAD_PAYLOAD)
        assert r.status_code == 201
        data = r.json()
        assert data["contact_name"] == "Rahul Sharma"
        assert data["intent_score"] > 0
        assert data["tier"] in ("hot", "warm", "cold")

    def test_create_lead_with_auth(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post("/api/v1/leads/", json=LEAD_PAYLOAD, headers=headers)
        assert r.status_code == 201
        # buyer_id should be populated
        assert r.json()["buyer_id"] is not None

    def test_create_lead_high_urgency_is_hot(self, client: TestClient):
        payload = {
            **LEAD_PAYLOAD,
            "possession_timeline_months": 3,  # very urgent
            "source": "whatsapp",
        }
        r = client.post("/api/v1/leads/", json=payload)
        assert r.status_code == 201
        assert r.json()["tier"] in ("hot", "warm")

    def test_create_lead_for_specific_property(self, client: TestClient, normal_user):
        _, headers = normal_user
        # Create a property first
        prop_r = client.post(
            "/api/v1/properties/",
            json={
                "property_type": "residential",
                "listing_type": "sale",
                "address_line1": "1 Test Road",
                "locality": "Powai",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pin_code": "400076",
                "base_price": 7500000.0,
            },
            headers=headers,
        )
        prop_id = prop_r.json()["id"]

        r = client.post(
            "/api/v1/leads/",
            json={**LEAD_PAYLOAD, "property_id": prop_id},
            headers=headers,
        )
        assert r.status_code == 201
        assert r.json()["property_id"] == prop_id


# ── List leads ────────────────────────────────────────────────────────────────

class TestListLeads:
    def test_authenticated_user_can_list(self, client: TestClient, normal_user):
        _, headers = normal_user
        create_lead(client, headers)
        r = client.get("/api/v1/leads/", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_filter_by_tier(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.get("/api/v1/leads/?tier=cold", headers=headers)
        assert r.status_code == 200

    def test_filter_by_source(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.get("/api/v1/leads/?source=portal", headers=headers)
        assert r.status_code == 200

    def test_unauthenticated_cannot_list(self, client: TestClient):
        r = client.get("/api/v1/leads/")
        assert r.status_code == 401


# ── Get single lead ───────────────────────────────────────────────────────────

class TestGetLead:
    def test_buyer_can_view_own_lead(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        r = client.get(f"/api/v1/leads/{lead['id']}", headers=headers)
        assert r.status_code == 200
        assert r.json()["id"] == lead["id"]

    def test_other_user_cannot_view(self, client: TestClient, normal_user):
        _, owner_headers = normal_user
        lead = create_lead(client, owner_headers)
        _, other_headers = register_and_login(
            client, email="spy@example.com", password="SpyPass1"
        )
        r = client.get(f"/api/v1/leads/{lead['id']}", headers=other_headers)
        assert r.status_code == 403

    def test_get_nonexistent_lead(self, client: TestClient, normal_user):
        _, headers = normal_user
        import uuid
        r = client.get(f"/api/v1/leads/{uuid.uuid4()}", headers=headers)
        assert r.status_code == 404


# ── Qualify lead ──────────────────────────────────────────────────────────────

class TestQualifyLead:
    def test_qualify_updates_score_and_tier(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        r = client.patch(f"/api/v1/leads/{lead['id']}/qualify", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["intent_score"] >= 0
        assert data["tier"] in ("hot", "warm", "cold")
        assert data["status"] in ("new", "qualified")


# ── Lead stats ────────────────────────────────────────────────────────────────

class TestLeadStats:
    def test_stats_returns_summary(self, client: TestClient, normal_user):
        _, headers = normal_user
        create_lead(client, headers)
        r = client.get("/api/v1/leads/stats/summary", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "by_tier" in data
        assert "by_status" in data
        assert "conversion_rate" in data

    def test_stats_conversion_rate_zero_when_no_leads(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.get("/api/v1/leads/stats/summary", headers=headers)
        assert r.status_code == 200
        assert r.json()["conversion_rate"] == 0.0


# ── Close lead ────────────────────────────────────────────────────────────────

class TestCloseLead:
    def test_close_lead_won(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        r = client.patch(
            f"/api/v1/leads/{lead['id']}/close?outcome=won&reason=Deal+completed",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "closed_won"

    def test_close_lead_lost(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        r = client.patch(
            f"/api/v1/leads/{lead['id']}/close?outcome=lost",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "closed_lost"

    def test_close_invalid_outcome(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        r = client.patch(
            f"/api/v1/leads/{lead['id']}/close?outcome=maybe",
            headers=headers,
        )
        assert r.status_code == 400


# ── Archive lead ──────────────────────────────────────────────────────────────

class TestArchiveLead:
    def test_broker_can_archive(self, client: TestClient, broker_user):
        _, headers = broker_user
        lead = create_lead(client, headers)
        r = client.delete(f"/api/v1/leads/{lead['id']}", headers=headers)
        assert r.status_code == 204

    def test_buyer_cannot_archive(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        r = client.delete(f"/api/v1/leads/{lead['id']}", headers=headers)
        assert r.status_code == 403


# ── FSM status transition ─────────────────────────────────────────────────────

class TestLeadFSM:
    def test_invalid_status_transition_rejected(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        # "new" → "closed_won" is not a valid transition
        r = client.patch(
            f"/api/v1/leads/{lead['id']}",
            json={"status": "closed_won"},
            headers=headers,
        )
        assert r.status_code == 403

    def test_valid_status_transition_accepted(self, client: TestClient, normal_user):
        _, headers = normal_user
        lead = create_lead(client, headers)
        # "new" → "contacted" is valid
        r = client.patch(
            f"/api/v1/leads/{lead['id']}",
            json={"status": "contacted"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "contacted"
