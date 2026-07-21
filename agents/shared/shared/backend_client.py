"""
agents/shared/backend_client.py
Async HTTP client for agent microservices to read/write data via the
backend REST API. Agents should never access the database directly.

Usage:
    client = BackendClient(base_url="http://localhost:8000", api_key="...")
    properties = await client.get_properties({"city": "Mumbai", "bhk_config": 2})
"""
from typing import Any

import httpx


class BackendClient:
    """
    Thin async wrapper around the backend REST API.
    Agents use this to fetch properties, leads, users, etc.
    without coupling to the database layer.
    """

    def __init__(self, base_url: str, agent_secret: str | None = None, timeout: float = 10.0) -> None:
        """
        Args:
            base_url:     Backend service base URL, e.g. "http://localhost:8000"
            agent_secret: Optional shared secret the backend uses to trust internal calls.
                          Set BACKEND_AGENT_SECRET on both sides.
            timeout:      HTTP request timeout in seconds.
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if agent_secret:
            self._headers["X-Agent-Secret"] = agent_secret

    # ── Properties ────────────────────────────────────────────────────────────

    async def get_properties(self, filters: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        """
        Fetch properties matching the given filters from the backend.
        Returns a list of property dicts sorted by listing_score DESC.

        Args:
            filters: Dict with optional keys: city, locality, state, bhk_config,
                     property_type, listing_type, price_min, price_max,
                     is_ready_to_move, furnishing_status.
            limit:   Maximum number of results.
        """
        params: dict[str, Any] = {"limit": limit}
        params.update({k: v for k, v in filters.items() if v is not None})

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}/api/v1/properties/",
                params=params,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
            # Backend returns {"items": [...], "total": N} or just a list
            if isinstance(data, dict):
                return data.get("items", [])
            return data  # type: ignore[return-value]

    # ── Leads ─────────────────────────────────────────────────────────────────

    async def get_lead(self, lead_id: str) -> dict[str, Any]:
        """Fetch a single lead by ID."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}/api/v1/leads/{lead_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]

    async def update_lead(self, lead_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Partially update a lead (PATCH).
        Common use: update tier, intent_score, status from a qualification agent.
        """
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.patch(
                f"{self._base_url}/api/v1/leads/{lead_id}",
                json=data,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]

    # ── Users ─────────────────────────────────────────────────────────────────

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Fetch a user profile by ID."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}/api/v1/users/{user_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]
