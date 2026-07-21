# agents/shared

Shared utilities for all STAIL Realty OS agent microservices.

## Modules

| Module | Purpose |
|---|---|
| `base_agent.py` | Abstract `BaseAgent` class with LLM integration, confidence scoring, and session reporting |
| `backend_client.py` | Async HTTP client for reading/writing data via the backend REST API |
| `schemas.py` | Shared Pydantic request/response schemas used across all agents |

## Usage

Each agent microservice installs this package as a local dependency:

```toml
# In each agent's pyproject.toml
dependencies = [
    "stail-agents-shared @ file:///${PROJECT_ROOT}/agents/shared",
    ...
]
```
