"""
agents/buyer-agent/tests/test_buyer_agent.py
Minimal tests for Buyer Agent (AGT-03).
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    import os
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    from agent.main import app
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent"] == "AGT-03"


def test_info_endpoint(client):
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "AGT-03"
    assert data["agent_name"] == "Buyer Agent"
