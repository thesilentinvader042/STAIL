"""
tests/test_orchestrator.py
Stub tests for Orchestrator.
"""
import pytest
from orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_returns_stub():
    orch = Orchestrator(agent_urls={})
    result = await orch.orchestrate(
        user_query="3BHK in Mumbai",
        session_id="test-session",
        user_id="test-user",
    )
    assert result["response"] is not None
    assert result["properties"] == []
