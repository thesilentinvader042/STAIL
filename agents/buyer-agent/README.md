# AGT-03: Buyer Agent

Microservice that extracts structured buyer requirements from natural language queries.

## Overview

- **Agent ID**: AGT-03
- **Cluster**: Buyer & Seller Engagement
- **Port**: 8003
- **Framework**: FastAPI + Groq LLM (llama3-8b-8192)
- **Status**: Phase 1 stub — returns placeholder responses

## Endpoints

| Method | Path     | Description              |
|--------|----------|--------------------------|
| POST   | /chat    | Process a buyer message  |
| GET    | /info    | Agent metadata           |
| GET    | /health  | Liveness probe           |
| GET    | /docs    | OpenAPI docs             |

## Running Locally

```bash
cd agents/buyer-agent
cp .env.example .env
pip install -e ".[dev]"
uvicorn agent.main:app --reload --port 8003
```

## Running Tests

```bash
pytest tests/
```

## Docker

Built as part of the root `docker compose up` from the `agents/` context:

```bash
docker compose up buyer-agent
```
