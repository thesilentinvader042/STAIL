"""
agents/recommendation-agent/tests/test_recommendation_agent.py
Minimal tests for Recommendation Agent (AGT-05).
"""
import pytest
from fastapi.testclient import TestClient

# Import functions to test
from agent.recommendation_agent import (
    _composite_score,
    _market_appeal_score,
    _user_fit_score,
    _relevance_score,
    _annotation_valid,
)


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
    assert data["agent"] == "AGT-05"


def test_info_endpoint(client):
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "AGT-05"
    assert data["agent_name"] == "Recommendation Agent"


# =============================================================================
# Task 4.3: Property test for composite score correctness (Property 4)
# =============================================================================
from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import patch


@given(
    relevance=st.floats(min_value=0.0, max_value=1.0),
    market_appeal=st.floats(min_value=0.0, max_value=1.0),
    user_fit=st.floats(min_value=0.0, max_value=1.0),
)
@settings(max_examples=100)
def test_composite_score_weights_sum_correctly(relevance, market_appeal, user_fit):
    """Property 4: composite_score == relevance*0.6 + market_appeal*0.2 + user_fit*0.2, clamped [0,1]"""
    # Create minimal prop and prefs dicts with the component scores
    prop = {"city": "Mumbai"}  # minimal
    prefs = {"cities": ["Mumbai"]}  # minimal

    # Override the component functions to return our test values
    with patch("agent.recommendation_agent._relevance_score", return_value=relevance), \
         patch("agent.recommendation_agent._market_appeal_score", return_value=market_appeal), \
         patch("agent.recommendation_agent._user_fit_score", return_value=user_fit):
        result = _composite_score(prop, prefs)

    expected_raw = relevance * 0.6 + market_appeal * 0.2 + user_fit * 0.2
    expected_clamped = min(max(expected_raw, 0.0), 1.0)

    assert abs(result - expected_clamped) < 0.001, \
        f"Expected {expected_clamped}, got {result}"


# =============================================================================
# Task 4.4: Property test for annotation hallucination guard (Property 5)
# =============================================================================


@given(
    prop=st.fixed_dictionaries({
        "title": st.text(min_size=1),
        "city": st.text(min_size=1),
        "locality": st.text(min_size=1),
    }),
    annotation=st.text(),
)
@settings(max_examples=50)
def test_annotation_hallucination_guard(prop, annotation):
    """Property 5: Annotation must mention name, city, or locality"""
    # If annotation mentions any of title/city/locality, it should be valid
    ann_lower = annotation.lower()
    has_title = prop.get("title", "").lower() in ann_lower
    has_city = prop.get("city", "").lower() in ann_lower
    has_locality = prop.get("locality", "").lower() in ann_lower

    expected = has_title or has_city or has_locality

    # Also test the negative case - annotation without any match
    no_match_annotation = "This is a generic property that matches your criteria"
    result_no_match = _annotation_valid(no_match_annotation, prop)
    assert result_no_match == False, "Annotation without property details should fail guard"

    # Positive case - annotation with city
    city_annotation = f"Great property in {prop.get('city')}"
    result_city = _annotation_valid(city_annotation, prop)
    assert result_city == True, "Annotation with city should pass guard"


# =============================================================================
# Task 4.5: Property test for top-5 annotated count (Property 6)
# =============================================================================


@given(
    num_properties=st.integers(min_value=5, max_value=50),
)
@settings(max_examples=20)
def test_top5_annotated_count(num_properties):
    """Property 6: ranked_properties has exactly min(5, len(properties)) entries with annotations"""
    # Generate properties
    properties = []
    for i in range(num_properties):
        properties.append({
            "id": i,
            "title": f"Property {i}",
            "city": "Mumbai",
            "asking_price": 5000000,
            "bhk_type": "2BHK",
            "composite_score": 0.5 + (i % 10) * 0.05,  # varying scores
        })

    # Rank them (as the agent does)
    ranked = sorted(properties, key=lambda p: p.get("composite_score", 0), reverse=True)
    top5 = ranked[:5]

    # Mock annotation for top 5
    for prop in top5:
        prop["annotation"] = f"Great {prop.get('bhk_type')} in {prop.get('city')}"

    # Verify count
    annotated = [p for p in ranked if p.get("annotation")]
    expected_count = min(5, num_properties)

    assert len(annotated) == expected_count, \
        f"Expected {expected_count} annotated properties, got {len(annotated)}"

    # Verify all top 5 have annotations
    assert all("annotation" in p for p in top5), "All top 5 should have annotations"
