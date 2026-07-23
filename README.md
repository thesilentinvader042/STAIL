# STAIL Realty OS — Monorepo

AI-native real estate operating system for the Indian market featuring microservice AI agents, multi-agent orchestration, autonomous memory, and high-performance property search.

---

## Repository Structure

```
stail/
├── backend/                             # Core FastAPI backend service & gateway (port 8000)
│   ├── app/
│   │   ├── api/v1/endpoints/           # Auth, Users, Properties, Leads, Agents, Developers
│   │   ├── core/                       # Config, security (JWT), exceptions
│   │   ├── db/                         # SQLAlchemy models + database session
│   │   ├── orchestration/              # Backend multi-agent orchestrator engine
│   │   └── schemas/                    # Pydantic v2 schemas
│   ├── alembic/                        # Database migrations
│   └── tests/                          # Backend test suite
│
├── agents/                             # Microservice AI Agents & Shared Framework
│   ├── shared/                         # Shared BaseAgent, HTTP backend client, & schemas
│   ├── property-discovery/             # AGT-01: Property Discovery Agent (port 8001)
│   ├── lead-qualification-agent/       # AGT-02: Lead Qualification Agent (port 8002)
│   ├── buyer-agent/                    # AGT-03: Buyer Assistant Agent (port 8003)
│   ├── property-agent/                 # AGT-04: Seller & Property Agent (port 8004)
│   ├── recommendation-agent/           # AGT-05: Recommendation Agent (port 8005)
│   ├── crm-agent/                      # AGT-06: CRM Automation Agent (port 8006)
│   └── orchestrator/                   # Standalone agent orchestration package
│
├── memory_system/                      # 4-Scope Autonomous Memory Subsystem (Redis + Postgres)
├── error_logging/                      # Centralized Structured Error & Audit Logging Subsystem
├── db/                                 # PostgreSQL 16 + PostGIS + pgvector Docker build setup
├── docs/                               # Phase verification & schema guides
└── docker-compose.yml                  # Full stack orchestration (Backend + DB + Redis + 6 Agents)
```

---

## Services & Port Map

| Service Name | Port | Container Name | Description |
|---|---|---|---|
| **backend** | `8000` | `realty_os_backend` | Core API Gateway — Auth, Properties, Leads, Users, Developers, Agent Proxy & Orchestrator |
| **db** | `5432` | `realty_os_db` | PostgreSQL 16 + PostGIS + pgvector database (`realty_os`) |
| **redis** | `6379` | `realty_os_redis` | Redis cache and session store |
| **property-discovery-agent** | `8001` | `realty_os_agt01` | **AGT-01** — Natural language property search & preference extraction |
| **lead-qualification-agent** | `8002` | `realty_os_agt02` | **AGT-02** — Lead scoring, intent classification, & tiering (HOT/WARM/COLD) |
| **buyer-agent** | `8003` | `realty_os_agt03` | **AGT-03** — Buyer assistant for property shortlisting and criteria refinement |
| **property-agent** | `8004` | `realty_os_agt04` | **AGT-04** — Seller assistant for listing creation & property metadata management |
| **recommendation-agent** | `8005` | `realty_os_agt05` | **AGT-05** — Personalized listing recommendation engine |
| **crm-agent** | `8006` | `realty_os_agt06` | **AGT-06** — Automatic CRM interaction logging and lead timeline updates |

---

## Architecture Overview

```
[Client App / Swagger UI]
         │
         ▼
[backend :8000] ─── POST /api/v1/agents/chat (Proxies to target agent service)
         │
         ├─── POST /api/v1/agents/orchestrate (Executes 5-agent pipeline workflow)
         │
         ├── AGT-01 → property-discovery-agent  :8001
         ├── AGT-02 → lead-qualification-agent  :8002
         ├── AGT-03 → buyer-agent               :8003
         ├── AGT-04 → property-agent            :8004
         ├── AGT-05 → recommendation-agent      :8005
         ├── AGT-06 → crm-agent                 :8006
         │
         └── AGT-07..15 → handled directly via Groq LLM (llama3-70b-8192)
```

---

## Core Subsystems

### 1. Multi-Agent Pipeline Orchestration
The backend orchestrator coordinates multi-agent execution sequences (e.g. `AGT-03 → AGT-04 → AGT-05 → AGT-02 → AGT-06`) via `POST /api/v1/agents/orchestrate`. It aggregates agent outputs, confidence scores, and latency metrics into a single response payload.

### 2. Autonomous Memory Subsystem (`memory_system/`)
Implements a 4-scope memory manager (`MemoryManager` facade):
- **Session Memory**: In-memory Redis store with TTL (30–60 min).
- **Long-Term Memory**: Permanent append-only PostgreSQL store with LLM summarization.
- **User Preferences**: Dual-write PostgreSQL (source of truth) and Redis cache.
- **Lead History**: Append-only PostgreSQL lead interaction timeline.

### 3. Structured Logging & Auditing (`error_logging/`)
Provides unified multi-handler logging across services supporting stdout console output, size-rotated log files, and direct PostgreSQL audit log table writing.

---

## Quick Start (Docker Compose — Recommended)

### 1. Copy Environment Files
```bash
# Copy environment files for backend and all 6 agents
cp backend/.env.example backend/.env
cp agents/property-discovery/.env.example agents/property-discovery/.env
cp agents/lead-qualification-agent/.env.example agents/lead-qualification-agent/.env
cp agents/buyer-agent/.env.example agents/buyer-agent/.env
cp agents/property-agent/.env.example agents/property-agent/.env
cp agents/recommendation-agent/.env.example agents/recommendation-agent/.env
cp agents/crm-agent/.env.example agents/crm-agent/.env
```

> 🔑 **Note:** Open each `.env` file and set your **`GROQ_API_KEY`**.

### 2. Start Full Stack
```bash
docker compose up -d --build
```

### 3. Run Database Migrations
```bash
docker compose exec backend python -m alembic -c /app/alembic.ini upgrade head
```

### 4. Verify Services Health
```bash
./check_agents.sh
```

---

## Quick Start (Local Development)

### 1. Start Infrastructure (PostgreSQL & Redis)
```bash
cd backend && docker compose up db redis -d
```

### 2. Start Core Backend API
```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Start Agent Microservices (Separate Terminals)
```bash
# Shared library setup (once)
pip install -e agents/shared

# AGT-01 Property Discovery
cd agents/property-discovery && uvicorn agent.main:app --reload --port 8001

# AGT-02 Lead Qualification
cd agents/lead-qualification-agent && uvicorn agent.main:app --reload --port 8002

# AGT-03 Buyer Assistant
cd agents/buyer-agent && uvicorn agent.main:app --reload --port 8003

# AGT-04 Property Seller Agent
cd agents/property-agent && uvicorn agent.main:app --reload --port 8004

# AGT-05 Recommendation Agent
cd agents/recommendation-agent && uvicorn agent.main:app --reload --port 8005

# AGT-06 CRM Agent
cd agents/crm-agent && uvicorn agent.main:app --reload --port 8006
```

---

## API Documentation

- **Core Backend API Gateway**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **AGT-01 Property Discovery**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **AGT-02 Lead Qualification**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **AGT-03 Buyer Assistant**: [http://localhost:8003/docs](http://localhost:8003/docs)
- **AGT-04 Property Seller Agent**: [http://localhost:8004/docs](http://localhost:8004/docs)
- **AGT-05 Recommendation Agent**: [http://localhost:8005/docs](http://localhost:8005/docs)
- **AGT-06 CRM Agent**: [http://localhost:8006/docs](http://localhost:8006/docs)

---

## Orchestration Example

To send a message through the 5-agent multi-agent pipeline:

```bash
curl -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
    "message": "I am looking for a 3BHK flat in Bandra West under 2.5 Crore"
  }'
```

---

## Adding a New Agent Microservice

1. Create a new directory in `agents/` using `agents/buyer-agent/` as a reference.
2. Implement your agent class extending `BaseAgent` from `agents/shared/base_agent.py`.
3. Map your service URL setting in `backend/app/core/config.py` and `AGENT_SERVICE_URLS` in `backend/app/api/v1/endpoints/agents.py`.
4. Add service block to `docker-compose.yml`.
