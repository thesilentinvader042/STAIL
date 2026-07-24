"""
agents/crm-agent/tests/test_crm_agent.py
Tests for CRM Agent (AGT-06).
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import httpx
from fastapi.testclient import TestClient


# Import the agent
from agent.crm_agent import CRMAgent


# --- FastAPI Client Tests ---

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
    assert data["agent"] == "AGT-06"


def test_info_endpoint(client):
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "AGT-06"
    assert data["agent_name"] == "CRM Agent"


# --- Task 5.2: Property test for grade-conditional follow-up ---
# Property 8: Follow-up note created iff grade is A or B

@pytest.mark.parametrize("grade,should_follow_up", [
    ("A", True),
    ("a", True),  # case insensitive
    ("B", True),
    ("b", True),
    ("C", False),
    ("D", False),
    (None, False),
    ("X", False),
])
@pytest.mark.asyncio
async def test_grade_conditional_follow_up(grade, should_follow_up):
    """Property 8: Follow-up note created iff grade is A or B"""
    from agent.config import settings
    
    # Mock the httpx client
    mock_response_post = MagicMock()
    mock_response_post.is_success = True
    mock_response_post.json.return_value = {"enquiry_id": "lead-123", "id": "lead-123"}
    mock_response_post.raise_for_status = MagicMock()
    
    mock_response_patch = MagicMock()
    mock_response_patch.is_success = True
    mock_response_patch.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_post = AsyncMock(return_value=mock_response_post)
        mock_patch = AsyncMock(return_value=mock_response_patch)
        mock_instance.post = mock_post
        mock_instance.patch = mock_patch
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = AsyncMock()
        
        agent = CRMAgent(groq_api_key="test-key")
        
        context = {
            "user_id": "user-123",
            "grade": grade,
            "score": 75,
        }
        
        result = await agent.handle("Looking for property", [], context)
        
        # For A/B grades, PATCH should be called
        if should_follow_up:
            assert mock_instance.patch.called, f"PATCH should be called for grade {grade}"
        else:
            assert not mock_instance.patch.called, f"PATCH should NOT be called for grade {grade}"


# --- Task 5.3: Property test for missing user_id guard ---
# Property 7: CRM Agent skips HTTP calls on missing required fields

@pytest.mark.asyncio
async def test_missing_user_id_guard():
    """Property 7: CRM Agent skips HTTP calls on missing required fields"""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = AsyncMock()
        
        agent = CRMAgent(groq_api_key="test-key")
        
        # Test with missing user_id
        result = await agent.handle("Looking for property", [], {"grade": "A"})
        
        # HTTP should NOT be called
        assert not mock_instance.post.called, "POST should not be called without user_id"
        assert not mock_instance.patch.called, "PATCH should not be called without user_id"
        
        # Check response
        assert result.metadata.get("stored") == False
        assert "user_id" in result.response.lower() or "missing" in result.response.lower()


@pytest.mark.asyncio
async def test_empty_context_guard():
    """Property 7: CRM Agent skips HTTP calls with empty context"""
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = AsyncMock()
        
        agent = CRMAgent(groq_api_key="test-key")
        
        # Test with None context
        result = await agent.handle("Looking for property", [], None)
        
        # HTTP should NOT be called
        assert not mock_instance.post.called, "POST should not be called with None context"


# --- Task 5.4: Unit test for graceful HTTP failure handling ---
# Requirement 5.5: HTTP failure returns without raising, stored=False

@pytest.mark.asyncio
async def test_graceful_http_failure_handling():
    """Requirement 5.5: HTTP failure returns without raising, stored=False"""
    from agent.config import settings
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        
        # Simulate connection error on POST
        mock_instance.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = AsyncMock()
        
        agent = CRMAgent(groq_api_key="test-key")
        
        # Should NOT raise, should return gracefully
        result = await agent.handle(
            "Looking for property",
            [],
            {"user_id": "user-123", "grade": "A"}
        )
        
        # Verify stored is False and response indicates failure
        assert result.metadata.get("stored") == False
        assert "not" in result.response.lower() or "could not" in result.response.lower()


@pytest.mark.asyncio
async def test_http_status_error_handling():
    """Requirement 5.5: HTTP 4xx/5xx errors handled gracefully"""
    from agent.config import settings
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response
        ))
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = AsyncMock()
        
        agent = CRMAgent(groq_api_key="test-key")
        
        result = await agent.handle(
            "Looking for property",
            [],
            {"user_id": "user-123"}
        )
        
        assert result.metadata.get("stored") == False
