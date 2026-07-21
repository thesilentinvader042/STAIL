# Property Discovery Agent (AGT-01)

> **Cluster:** Discovery & Matching  
> **Model:** `llama3-8b-8192` (Groq)  
> **Port:** `8001`

Converts natural language property search queries into ranked shortlists using a two-phase pipeline.

## Pipeline

```
User message (NL)
      │
      ▼  Phase 1 — Preference Extraction
  Groq LLM (llama3-8b-8192)
  → Structured JSON: {city, locality, bhk_config, price_max, ...}
      │
      ▼  Phase 2 — Property Search
  Backend REST API  GET /api/v1/properties/?city=...
  → Ranked list sorted by listing_score DESC (featured first)
      │
      ▼
  Formatted markdown response to user
```

## KPIs

| KPI | Target |
|---|---|
| Search-to-shortlist latency | < 3 seconds |
| Intent parse accuracy | > 92% |

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Process a discovery request (called by backend proxy) |
| `GET` | `/info` | Agent metadata and KPIs |
| `GET` | `/health` | Liveness probe |

## Local Development

```bash
# 1. Install dependencies (from this directory)
pip install -e ".[dev]"
pip install -e "../shared"

# 2. Copy and fill in .env
cp .env.example .env

# 3. Start the agent (backend must be running on :8000)
uvicorn agent.main:app --reload --port 8001
```

The agent is available at http://localhost:8001  
Interactive docs: http://localhost:8001/docs

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Groq API key |
| `BACKEND_API_URL` | `http://localhost:8000` | Core backend URL |
| `BACKEND_AGENT_SECRET` | — | Shared secret for internal calls |
| `PORT` | `8001` | Service port |

## Architecture

This service is called by the **backend** (`POST /api/v1/agents/chat` with `agent_id=AGT-01`).  
It reads property data via `BackendClient` and never accesses the database directly.
