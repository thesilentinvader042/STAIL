"""
agents/lead-qualification-agent/tests/test_buyer_agent.py
Smoke tests for Lead Qualification Agent (AGT-02) endpoint contract.
"""
import os
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GROQ_API_KEY", "test-key")


@pytest.fixture
def client():
    """Create test client with mocked agent."""
    # Create mock result
    mock_result = MagicMock()
    mock_result.response = "Grade: **B** | Score: 75/100\nAction: Nurture\nReasoning: Good fit"
    mock_result.confidence = 0.85
    mock_result.escalated = False
    mock_result.escalation_reason = None
    mock_result.latency_ms = 100
    mock_result.metadata = {"grade": "B", "score": 75}

    # Create mock agent instance with async run method
    mock_agent_instance = MagicMock()
    mock_agent_instance.run = AsyncMock(return_value=mock_result)

    # Patch the _agent global before creating the TestClient
    with MagicMock():
        import agent.main
        original_agent = getattr(agent.main, '_agent', None)
        agent.main._agent = mock_agent_instance
        
        from agent.main import app
        from contextlib import asynccontextmanager

        # Override lifespan to not initialize the real agent
        @asynccontextmanager
        async def mock_lifespan(app):
            yield

        app.router.lifespan_context = mock_lifespan
        
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
        
        # Restore original agent
        if original_agent is not None:
            agent.main._agent = original_agent


def test_chat_endpoint_response_shape(client):
    """Smoke test for POST /chat endpoint contract.
    
    **Validates: Requirements 1.1, 1.2**
    """
    payload = {
        "agent_id": "AGT-02",
        "message": "I'm looking to buy a home in the next 6 months",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()

    # Assert agent_id is AGT-02 (Requirement 1.1)
    assert data["agent_id"] == "AGT-02"

    # Assert confidence_score is in [0, 1] (Requirement 1.2)
    assert 0.0 <= data["confidence_score"] <= 1.0

    # Assert response is non-empty (Requirement 1.5)
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


def test_health_endpoint(client):
    """Liveness probe test."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent"] == "AGT-02"


def test_info_endpoint(client):
    """Agent metadata test."""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "AGT-02"
    assert data["agent_name"] == "Lead Qualification Agent"