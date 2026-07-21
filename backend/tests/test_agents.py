"""
tests/test_agents.py
AI Agent endpoint tests:
  list agents, agent info, chat (LLM mocked), session CRUD,
  escalate, close, stats (admin)

The LLM (_call_llm) is patched via unittest.mock to avoid hitting the
Anthropic API during CI. All other agent logic (session persistence,
escalation, history tracking) is tested against the real FastAPI stack.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Mocked LLM response ───────────────────────────────────────────────────────

MOCK_RESPONSE = ("This is a mocked agent response for testing.", 0.90)


def _mock_call_llm(*args, **kwargs):
    """Synchronous stand-in for the async _call_llm function."""
    return MOCK_RESPONSE


# ── List agents ───────────────────────────────────────────────────────────────

class TestListAgents:
    def test_list_agents_public(self, client: TestClient):
        """GET /agents/ should be publicly accessible."""
        r = client.get("/api/v1/agents/")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 15
        assert len(data["agents"]) == 15

    def test_list_agents_contains_agt01(self, client: TestClient):
        r = client.get("/api/v1/agents/")
        agents = {a["agent_id"]: a for a in r.json()["agents"]}
        assert "AGT-01" in agents
        assert agents["AGT-01"]["name"] == "Property Discovery Agent"

    def test_all_15_agents_present(self, client: TestClient):
        r = client.get("/api/v1/agents/")
        agent_ids = {a["agent_id"] for a in r.json()["agents"]}
        for i in range(1, 16):
            agt_id = f"AGT-{i:02d}"
            assert agt_id in agent_ids, f"{agt_id} missing from registry"


# ── Agent info ────────────────────────────────────────────────────────────────

class TestAgentInfo:
    def test_valid_agent_info(self, client: TestClient):
        r = client.get("/api/v1/agents/AGT-01/info")
        assert r.status_code == 200
        data = r.json()
        assert data["agent_id"] == "AGT-01"
        assert "role" in data
        assert "kpis" in data
        assert "triggers" in data

    def test_invalid_agent_info(self, client: TestClient):
        r = client.get("/api/v1/agents/AGT-99/info")
        assert r.status_code == 404

    def test_all_agents_have_required_fields(self, client: TestClient):
        for i in range(1, 16):
            r = client.get(f"/api/v1/agents/AGT-{i:02d}/info")
            assert r.status_code == 200
            data = r.json()
            for field in ("name", "cluster", "llm_tier", "role", "kpis", "triggers"):
                assert field in data, f"AGT-{i:02d} missing field: {field}"


# ── Chat ──────────────────────────────────────────────────────────────────────

class TestAgentChat:
    @patch(
        "app.api.v1.endpoints.agents._call_llm",
        new_callable=lambda: lambda *a, **k: AsyncMock(return_value=MOCK_RESPONSE),
    )
    def test_chat_creates_session(self, mock_llm, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post(
            "/api/v1/agents/chat",
            json={
                "agent_id": "AGT-01",
                "message": "Find me a 2BHK in Mumbai under 1 crore",
            },
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["agent_id"] == "AGT-01"
        assert data["agent_name"] == "Property Discovery Agent"
        assert "session_id" in data
        assert "response" in data
        assert isinstance(data["response"], str)
        assert data["escalated"] is False

    @patch(
        "app.api.v1.endpoints.agents._call_llm",
        new_callable=lambda: lambda *a, **k: AsyncMock(return_value=MOCK_RESPONSE),
    )
    def test_chat_continues_session(self, mock_llm, client: TestClient, normal_user):
        _, headers = normal_user
        # First message
        r1 = client.post(
            "/api/v1/agents/chat",
            json={"agent_id": "AGT-01", "message": "Hello"},
            headers=headers,
        )
        session_id = r1.json()["session_id"]

        # Continue same session
        r2 = client.post(
            "/api/v1/agents/chat",
            json={
                "agent_id": "AGT-01",
                "message": "Show me 3BHK options too",
                "session_id": session_id,
            },
            headers=headers,
        )
        assert r2.status_code == 200
        assert r2.json()["session_id"] == session_id

    def test_chat_requires_auth(self, client: TestClient):
        r = client.post(
            "/api/v1/agents/chat",
            json={"agent_id": "AGT-01", "message": "Hello"},
        )
        assert r.status_code == 401

    def test_chat_invalid_agent_id(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post(
            "/api/v1/agents/chat",
            json={"agent_id": "AGT-99", "message": "Hello"},
            headers=headers,
        )
        # Fails Pydantic regex validation
        assert r.status_code == 422

    @patch(
        "app.api.v1.endpoints.agents._call_llm",
        new_callable=lambda: lambda *a, **k: AsyncMock(
            return_value=("I cannot help with that.", 0.50)  # low confidence → escalation
        ),
    )
    def test_low_confidence_triggers_escalation(self, mock_llm, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post(
            "/api/v1/agents/chat",
            json={"agent_id": "AGT-01", "message": "Something very unusual"},
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["escalated"] is True
        assert data["escalation_reason"] is not None

    @patch(
        "app.api.v1.endpoints.agents._call_llm",
        new_callable=lambda: lambda *a, **k: AsyncMock(return_value=MOCK_RESPONSE),
    )
    def test_chat_with_context(self, mock_llm, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.post(
            "/api/v1/agents/chat",
            json={
                "agent_id": "AGT-06",
                "message": "What is the rental yield?",
                "context": {"city": "Pune", "property_type": "commercial"},
            },
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["agent_id"] == "AGT-06"


# ── Session CRUD ──────────────────────────────────────────────────────────────

class TestAgentSessions:
    def _create_session(self, client: TestClient, headers: dict) -> dict:
        with patch(
            "app.api.v1.endpoints.agents._call_llm",
            new=AsyncMock(return_value=MOCK_RESPONSE),
        ):
            r = client.post(
                "/api/v1/agents/chat",
                json={"agent_id": "AGT-01", "message": "Test message"},
                headers=headers,
            )
        assert r.status_code == 200
        return r.json()

    def test_list_sessions(self, client: TestClient, normal_user):
        _, headers = normal_user
        self._create_session(client, headers)
        r = client.get("/api/v1/agents/sessions/", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_list_sessions_filter_by_agent(self, client: TestClient, normal_user):
        _, headers = normal_user
        self._create_session(client, headers)
        r = client.get("/api/v1/agents/sessions/?agent_id=AGT-01", headers=headers)
        assert r.status_code == 200
        for s in r.json():
            assert s["agent_id"] == "AGT-01"

    def test_get_session_detail(self, client: TestClient, normal_user):
        _, headers = normal_user
        chat = self._create_session(client, headers)
        r = client.get(f"/api/v1/agents/sessions/{chat['session_id']}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["agent_id"] == "AGT-01"
        assert data["llm_model"] is not None

    def test_cannot_view_other_users_session(self, client: TestClient, normal_user):
        _, owner_headers = normal_user
        chat = self._create_session(client, owner_headers)

        from utils import register_and_login
        _, other_headers = register_and_login(
            client, email="spy2@example.com", password="SpyPass2"
        )
        r = client.get(
            f"/api/v1/agents/sessions/{chat['session_id']}", headers=other_headers
        )
        assert r.status_code == 403

    def test_close_session(self, client: TestClient, normal_user):
        _, headers = normal_user
        chat = self._create_session(client, headers)
        r = client.delete(
            f"/api/v1/agents/sessions/{chat['session_id']}", headers=headers
        )
        assert r.status_code == 204

    def test_cannot_reuse_closed_session(self, client: TestClient, normal_user):
        _, headers = normal_user
        chat = self._create_session(client, headers)
        session_id = chat["session_id"]

        # Close it
        client.delete(f"/api/v1/agents/sessions/{session_id}", headers=headers)

        # Try to continue the closed session
        r = client.post(
            "/api/v1/agents/chat",
            json={
                "agent_id": "AGT-01",
                "message": "Continue?",
                "session_id": session_id,
            },
            headers=headers,
        )
        assert r.status_code == 400

    def test_escalate_session(self, client: TestClient, normal_user):
        _, headers = normal_user
        chat = self._create_session(client, headers)
        r = client.patch(
            f"/api/v1/agents/sessions/{chat['session_id']}/escalate"
            "?reason=User+requested+human+support",
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["escalated"] is True
        assert "human support" in data["escalation_reason"].lower()


# ── Session stats (admin) ─────────────────────────────────────────────────────

class TestSessionStats:
    def _create_session(self, client: TestClient, headers: dict) -> dict:
        with patch(
            "app.api.v1.endpoints.agents._call_llm",
            new=AsyncMock(return_value=MOCK_RESPONSE),
        ):
            r = client.post(
                "/api/v1/agents/chat",
                json={"agent_id": "AGT-01", "message": "Stats test"},
                headers=headers,
            )
        assert r.status_code == 200
        return r.json()

    def test_admin_can_view_stats(self, client: TestClient, normal_user, admin_user):
        _, user_headers = normal_user
        _, admin_headers = admin_user
        self._create_session(client, user_headers)
        r = client.get("/api/v1/agents/sessions/stats", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_sessions" in data
        assert "escalated" in data
        assert "sessions_by_agent" in data

    def test_non_admin_cannot_view_stats(self, client: TestClient, normal_user):
        _, headers = normal_user
        r = client.get("/api/v1/agents/sessions/stats", headers=headers)
        assert r.status_code == 403

    def test_stats_empty_returns_zero(self, client: TestClient, admin_user):
        _, headers = admin_user
        r = client.get("/api/v1/agents/sessions/stats", headers=headers)
        assert r.status_code == 200
        # May have 0 sessions
        assert "total" in r.json() or "total_sessions" in r.json()
