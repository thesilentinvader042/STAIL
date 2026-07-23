"""
agents/buyer-agent/tests/test_buyer_agent.py
Minimal tests for Buyer Agent (AGT-03).
"""
import pytest
from fastapi.testclient import TestClient

from agent.buyer_agent import _parse_inr


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
@pytest.mark.parametrize("input_val,expected", [
    ("1.5Cr", 15000000),
    ("50L", 5000000),
    ("2 crore", 20000000),
    ("invalid", None),
    ("30 lakh", 3000000),
    ("1cr", 10000000),
    ("75L", 7500000),
    ("1.2Cr", 12000000),
    ("", None),
    ("random text", None),
])
def test_parse_inr(input_val, expected):
    assert _parse_inr(input_val) == expected
"""
agents/buyer-agent/tests/test_buyer_agent.py
Minimal tests for Buyer Agent (AGT-03).
"""
import json
import asyncio
from unittest.mock import patch, AsyncMock
from hypothesis import given, settings, example
from hypothesis import strategies as st

import pytest
from fastapi.testclient import TestClient

from agent.buyer_agent import BuyerAgent


# --- Task 2.3: Property test for preference extraction schema validity ---
# Validates: Requirements 2.2, 2.4

@given(st.text())
@settings(max_examples=50, deadline=10000)
@example("3BHK in Mumbai under 1.5Cr")
@example("I want a property")
@example("")
def test_preference_extraction_returns_valid_schema(message):
    """
    Property 1: Always returns valid BuyerPreferences with confidence in [0,1].
    Validates: Requirements 2.2, 2.4
    """
    import os
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    
    # Mock LLM to return a valid JSON response
    mock_json = {
        "budget_min": None,
        "budget_max": 15000000,
        "bhk_type": ["3BHK"],
        "cities": ["Mumbai"],
        "property_types": ["apartment"],
        "timeline_months": None,
        "investment_goal": "end_use",
        "confidence_score": 0.85
    }
    
    async def mock_call_llm(self, user_message, history, context, max_tokens=400):
        return (json.dumps(mock_json), 0.85)
    
    with patch.object(BuyerAgent, 'call_llm', mock_call_llm):
        agent = BuyerAgent(groq_api_key="test-key")
        
        # Run extraction
        result = asyncio.get_event_loop().run_until_complete(
            agent.handle(message, [], None)
        )
        
        # Property 1: metadata["preferences"] must be valid dict with all required fields
        prefs = result.metadata.get("preferences", {})
        assert "budget_min" in prefs, "Missing budget_min in preferences"
        assert "budget_max" in prefs, "Missing budget_max in preferences"
        assert "bhk_type" in prefs, "Missing bhk_type in preferences"
        assert "cities" in prefs, "Missing cities in preferences"
        assert "property_types" in prefs, "Missing property_types in preferences"
        assert "timeline_months" in prefs, "Missing timeline_months in preferences"
        assert "investment_goal" in prefs, "Missing investment_goal in preferences"
        assert "confidence_score" in prefs, "Missing confidence_score in preferences"
        
        # Property 1: confidence_score in [0, 1]
        confidence = prefs.get("confidence_score", 0.0)
        assert 0.0 <= confidence <= 1.0, f"confidence_score {confidence} not in [0, 1]"


# --- Task 2.4: Property test for low-confidence clarifying questions ---
# Validates: Requirement 2.3

@given(st.floats(min_value=-1.0, max_value=0.49))
@settings(max_examples=20, deadline=10000)
def test_low_confidence_includes_clarifying_questions(low_confidence):
    """
    Property 2: confidence_score < 0.5 triggers non-empty clarifying_questions.
    Validates: Requirement 2.3
    """
    import os
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    
    mock_json = {
        "budget_min": None,
        "budget_max": None,
        "bhk_type": [],
        "cities": [],
        "property_types": [],
        "timeline_months": None,
        "investment_goal": None,
        "confidence_score": low_confidence
    }
    
    async def mock_call_llm(self, user_message, history, context, max_tokens=400):
        return (json.dumps(mock_json), low_confidence)
    
    with patch.object(BuyerAgent, 'call_llm', mock_call_llm):
        agent = BuyerAgent(groq_api_key="test-key")
        
        result = asyncio.get_event_loop().run_until_complete(
            agent.handle("I want a property", [], None)
        )
        
        prefs = result.metadata.get("preferences", {})
        
        # Property 2: if confidence < 0.5, clarifying_questions must be non-empty
        if low_confidence < 0.5:
            assert len(prefs.get("clarifying_questions", [])) > 0, \
                f"Expected non-empty clarifying_questions for confidence={low_confidence}"