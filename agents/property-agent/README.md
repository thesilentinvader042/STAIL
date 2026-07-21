# AGT-04: Property Agent

Microservice that fetches and filters properties from the backend based on buyer preferences.

## Overview

- **Agent ID**: AGT-04
- **Cluster**: Discovery & Matching
- **Port**: 8004
- **Framework**: FastAPI + Groq LLM (llama3-8b-8192)
- **Status**: Phase 1 stub — returns placeholder responses

## Endpoints

| Method | Path     | Description                |
|--------|----------|----------------------------|
| POST   | /chat    | Process a property query   |
| GET    | /info    | Agent metadata             |
| GET    | /health  | Liveness probe             |
| GET    | /docs    | OpenAPI docs               |

## Running Locally

```bash
cd agents/property-agent
cp .env.example .env
pip install -e ".[dev]"
uvicorn agent.main:app --reload --port 8004
```

## Running Tests

```bash
pytest tests/
```

## Docker

```bash
docker compose up property-agent
```
