# STAIL Realty OS — Monorepo

AI-native real estate operating system for the Indian market.

## Repository Structure

```
stail/
├── backend/                        # Core FastAPI backend service (port 8000)
│   ├── app/
│   │   ├── api/v1/endpoints/       # Auth, Users, Properties, Leads, Agents (router)
│   │   ├── core/                   # Config, security, exceptions
│   │   ├── db/                     # SQLAlchemy models + session
│   │   └── schemas/                # Pydantic schemas
│   ├── alembic/                    # DB migrations
│   └── tests/
│
├── agents/
│   ├── shared/                     # Shared base classes + HTTP client
│   │   ├── base_agent.py           # Abstract BaseAgent (LLM, confidence, timing)
│   │   ├── backend_client.py       # HTTP client for backend REST API
│   │   └── schemas.py              # Shared request/response schemas
│   │
│   └── property-discovery/         # AGT-01: Property Discovery Agent (port 8001)
│       ├── agent/
│       │   ├── main.py             # FastAPI app
│       │   ├── config.py           # Service settings
│       │   ├── discovery_agent.py  # Business logic (NL → prefs → properties)
│       │   └── schemas.py          # AGT-01-specific schemas
│       ├── Dockerfile
│       └── README.md
│
└── docker-compose.yml              # Full stack orchestration
```

## Services

| Service | Port | Description |
|---|---|---|
| **backend** | `8000` | Core API — Auth, Users, Properties, Leads, Agent session management |
| **property-discovery-agent** | `8001` | AGT-01 — Natural language property search |

## Agent Architecture

```
[Client]
   │
   ▼
[backend :8000]  POST /api/v1/agents/chat
   │  Validates JWT, creates AgentSession in DB
   │
   ├── AGT-01 → proxies to property-discovery-agent :8001
   │
   └── AGT-02..15 → handled directly via Groq LLM
```

All agents that have dedicated services are listed in `AGENT_SERVICE_URLS` in `backend/app/api/v1/endpoints/agents.py`.

## Quick Start (Docker)

```bash
# Copy and fill in environment files
cp backend/.env.example backend/.env
cp agents/property-discovery/.env.example agents/property-discovery/.env

# Start the full stack
docker compose up --build

# Run DB migrations
docker compose exec backend alembic upgrade head
```

## Quick Start (Local Development)

```bash
# 1. Start infrastructure
cd backend && docker compose up db redis -d

# 2. Start backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Start Property Discovery Agent
cd agents/property-discovery
pip install -e ".[dev]"
pip install -e "../shared"
uvicorn agent.main:app --reload --port 8001
```

## API Documentation

- Backend: http://localhost:8000/docs
- Property Discovery Agent: http://localhost:8001/docs

## Adding a New Agent

1. Copy `agents/property-discovery/` as a template.
2. Implement `agent/discovery_agent.py` → your own agent class inheriting `BaseAgent`.
3. Add the service URL to `AGENT_SERVICE_URLS` in `backend/app/api/v1/endpoints/agents.py`.
4. Add a new service block to `docker-compose.yml`.
