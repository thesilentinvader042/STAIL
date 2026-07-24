"""
backend/tests/test_retry_logging.py
Tests for retry backoff (Task 7.4) and structured logging (Task 7.5).
"""
from __future__ import annotations

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only")
os.environ.setdefault("APP_ENV", "test")


# ---------------------------------------------------------------------------
# Task 7.4 — Property 12: Retry Logic Eventually Succeeds After Transient Failures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_succeeds_after_1_transient_failure():
    """Property 12: When httpx fails once then succeeds, result is the success response."""
    from app.orchestration.orchestrator import BackendOrchestrator

    orch = BackendOrchestrator()

    success_data = {"response": "ok", "confidence_score": 0.9, "metadata": {}}

    # Build a mock response for the success case
    mock_success_resp = MagicMock()
    mock_success_resp.raise_for_status = MagicMock()
    mock_success_resp.json.return_value = success_data

    call_count = 0

    async def flaky_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("transient network error")
        return mock_success_resp

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(side_effect=flaky_post)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Patch asyncio.sleep to avoid real delays and record calls
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await orch._call_agent(
                "AGT-03",
                "http://localhost:8003/chat",
                {"agent_id": "AGT-03", "message": "test"},
                session_id="session-retry-1",
                user_id="user-001",
            )

    # Property 12a: Result should be the success response
    assert result == success_data, f"Expected success data, got: {result}"

    # Property 12b: Exactly 2 HTTP calls made (1 fail + 1 success)
    assert call_count == 2, f"Expected 2 HTTP calls, got: {call_count}"

    # Property 12c: Backoff sleep was called once (after 1st failure, before retry)
    mock_sleep.assert_called_once_with(1)  # 2 ** 0 = 1


@pytest.mark.asyncio
async def test_retry_succeeds_after_2_transient_failures():
    """Property 12: When httpx fails twice then succeeds (at attempt 2), result is success."""
    from app.orchestration.orchestrator import BackendOrchestrator

    orch = BackendOrchestrator()

    success_data = {"response": "eventually ok", "confidence_score": 0.85, "metadata": {}}

    mock_success_resp = MagicMock()
    mock_success_resp.raise_for_status = MagicMock()
    mock_success_resp.json.return_value = success_data

    call_count = 0

    async def double_flaky_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception(f"transient error #{call_count}")
        return mock_success_resp

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(side_effect=double_flaky_post)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await orch._call_agent(
                "AGT-04",
                "http://localhost:8004/chat",
                {"agent_id": "AGT-04", "message": "test"},
                session_id="session-retry-2",
                user_id="user-002",
            )

    # Property 12a: Result is the success response
    assert result == success_data, f"Expected success data, got: {result}"

    # Property 12b: 3 HTTP calls (fail, fail, success)
    assert call_count == 3, f"Expected 3 HTTP calls, got: {call_count}"

    # Property 12c: Backoff sleeps: 2**0=1 then 2**1=2
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)  # after attempt 0
    mock_sleep.assert_any_call(2)  # after attempt 1


@pytest.mark.asyncio
async def test_retry_exhausted_returns_empty_dict():
    """Property 12 (negative): When all attempts fail, returns {} and records circuit failure."""
    from app.orchestration.orchestrator import BackendOrchestrator

    orch = BackendOrchestrator()

    async def always_fail(*args, **kwargs):
        raise Exception("permanent error")

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(side_effect=always_fail)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await orch._call_agent(
                "AGT-05",
                "http://localhost:8005/chat",
                {"agent_id": "AGT-05", "message": "test"},
            )

    assert result == {}, f"Expected empty dict on exhausted retries, got: {result}"
    # Failure should have been recorded
    assert orch._failure_counts.get("AGT-05", 0) == 1, \
        "One failure should be recorded after exhausted retries"


# ---------------------------------------------------------------------------
# Task 7.5 — Unit test: structured logging on agent calls
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_structured_logging_on_success():
    """Task 7.5: logger.agent() called with AgentLogContext on successful _call_agent."""
    from app.orchestration.orchestrator import BackendOrchestrator

    orch = BackendOrchestrator()

    success_data = {"response": "logged ok", "confidence_score": 0.9, "metadata": {}}
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = success_data

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_resp)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Patch the error_logger that the orchestrator uses
        import app.orchestration.orchestrator as orch_module

        if not orch_module.HAS_ERROR_LOGGING:
            pytest.skip("error_logging not installed — skipping logging assertion test")

        with patch.object(orch_module, "error_logger") as mock_logger:
            result = await orch._call_agent(
                "AGT-03",
                "http://localhost:8003/chat",
                {"agent_id": "AGT-03", "message": "test"},
                session_id="log-session-001",
                user_id="log-user-001",
            )

    assert result == success_data

    # logger.agent() must have been called at least once
    assert mock_logger.agent.called, "error_logger.agent() should be called on success"

    # Inspect the call — should contain AgentLogContext with agent_name and latency_ms > 0
    call_args = mock_logger.agent.call_args
    context = call_args.kwargs.get("context") or (call_args.args[1] if len(call_args.args) > 1 else None)

    if context is not None:
        from error_logging.models import AgentLogContext
        assert isinstance(context, AgentLogContext), \
            f"Expected AgentLogContext, got {type(context)}"
        assert context.agent_name == "AGT-03", \
            f"Expected agent_name='AGT-03', got: {context.agent_name}"
        assert context.latency_ms is not None and context.latency_ms >= 0, \
            f"Expected latency_ms >= 0, got: {context.latency_ms}"


@pytest.mark.asyncio
async def test_structured_logging_on_circuit_breaker_skip():
    """Task 7.5: logger.agent() called with WARNING level when circuit breaker is open."""
    from app.orchestration.orchestrator import BackendOrchestrator

    orch = BackendOrchestrator()

    # Force circuit open for AGT-06
    orch._record_failure("AGT-06")
    orch._record_failure("AGT-06")
    orch._record_failure("AGT-06")
    assert orch._is_circuit_open("AGT-06")

    import app.orchestration.orchestrator as orch_module

    if not orch_module.HAS_ERROR_LOGGING:
        pytest.skip("error_logging not installed — skipping logging assertion test")

    with patch.object(orch_module, "error_logger") as mock_logger:
        result = await orch._call_agent(
            "AGT-06",
            "http://localhost:8006/chat",
            {"agent_id": "AGT-06", "message": "test"},
            session_id="cb-session",
            user_id="cb-user",
        )

    assert result == {}
    # Should log a WARNING about circuit breaker
    assert mock_logger.agent.called, "error_logger.agent() should be called on circuit breaker skip"
    call_kwargs = mock_logger.agent.call_args.kwargs
    assert call_kwargs.get("level") in ("WARNING", "warning"), \
        f"Expected WARNING level, got: {call_kwargs.get('level')}"
