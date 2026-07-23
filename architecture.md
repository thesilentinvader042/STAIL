# STAIL Realty OS - Architecture Documentation

**Version:** 2.0.0  
**Last Updated:** July 24, 2026  
**Technology Stack:** FastAPI, PostgreSQL 16 (PostGIS + pgvector), Redis 7, Docker, Groq / LLMs

---

## 1. System Overview

STAIL Realty OS is an AI-native real estate operating system engineered for the Indian real estate market. The platform automates end-to-end real estate lifecycle workflows through microservice AI agents, multi-agent pipeline orchestration, autonomous 4-layer memory, and structured audit/error logging:

- **Property Discovery & Matching**: Natural language search, filter extraction, spatial & preference ranking.
- **Lead Qualification & Nurturing**: Intent scoring, financial readiness grading, and automated follow-ups.
- **Buyer & Seller Lifecycle**: Guided property shortlisting, listing optimization, and offer facilitation.
- **Personalized Recommendations**: Context-aware recommendation engine and portfolio matching.
- **CRM & Transaction Automation**: Auto-logging agent actions, interaction histories, and lead activity timelines.
- **Market & Developer Intelligence**: Pricing intelligence, RERA compliance tracking, and demand analytics.

---

## 2. High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CLIENTS                                             │
│                     (Web Application, Mobile App, Third-party APIs, Swagger UI)           │
└─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                              │ HTTP/HTTPS
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                  BACKEND API GATEWAY (Port 8000)                          │
│   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌────────────┐   │
│   │ Auth          │ │ Users         │ │ Properties    │ │ Leads         │ │ Developers │   │
│   │ /auth         │ │ /users        │ │ /properties   │ │ /leads        │ │ /developers│   │
│   └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └────────────┘   │
│   ┌─────────────────────────────────┐ ┌───────────────────────────────────────────────┐   │
│   │ Agents Endpoint Proxy           │ │ Multi-Agent Pipeline Orchestrator             │   │
│   │ POST /api/v1/agents/chat        │ │ POST /api/v1/agents/orchestrate              │   │
│   └─────────────────────────────────┘ └───────────────────────────────────────────────┘   │
│                                                                                           │
│   ┌───────────────────────────────────────────────────────────────────────────────────┐   │
│   │                       SQLAlchemy ORM + Pydantic v2 Schemas                        │   │
│   └───────────────────────────────────────────────────────────────────────────────────┘   │
└───────────┬─────────────────────────────────┬─────────────────────────────────┬───────────┘
            │ Internal HTTP                   │ DB Pool                         │ Redis Async
            ▼                                 ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────┐          ┌──────────────────────┐
│  AI Agent Services   │          │  PostgreSQL + Vector │          │  Redis Cache & State │
│  (Ports 8001 - 8006) │          │  (Port 5432)         │          │  (Port 6379)         │
└───────────┬──────────┘          └──────────────────────┘          └──────────────────────┘
            │
            ├──────────────────────┬──────────────────────┬──────────────────────┐
            ▼                      ▼                      ▼                      ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│  Property Discovery  │ │  Lead Qualification  │ │   Buyer Assistant    │ │   Property Agent     │
│  Agent (AGT-01)      │ │  Agent (AGT-02)      │ │   Agent (AGT-03)     │ │   Agent (AGT-04)     │
│  Port: 8001          │ │  Port: 8002          │ │   Port: 8003         │ │   Port: 8004         │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘
            │                                             │
            ├─────────────────────────────────────────────┘
            ▼
┌──────────────────────┐ ┌──────────────────────┐
│    Recommendation    │ │     CRM Agent        │
│    Agent (AGT-05)    │ │     (AGT-06)         │
│    Port: 8005        │ │     Port: 8006       │
└──────────────────────┘ └──────────────────────┘
```

---

## 3. Technology Stack

### Core Infrastructure
| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **API Framework** | FastAPI | 0.115+ | High-performance asynchronous REST API framework |
| **App Server** | Uvicorn | 0.30+ | ASGI web server |
| **ORM** | SQLAlchemy | 2.0+ | Asynchronous & synchronous relational data mapping |
| **Database** | PostgreSQL | 16+ | Primary transactional & analytical store |
| **Spatial DB** | PostGIS | 3.4+ | Geospatial index & spatial queries |
| **Vector DB** | pgvector | 0.7+ | Embedding storage & similarity vector search |
| **Cache & State** | Redis | 7-alpine | In-memory session state, caching, & memory TTL |
| **Auth** | JWT (python-jose) | 3.3+ | Stateless JWT authentication & token management |
| **Password Hashing**| passlib + bcrypt | 4.0.1 | Secure credentials storage |
| **Data Validation** | Pydantic | 2.9+ | Request/response schema validation |
| **Migrations** | Alembic | 1.13+ | Database schema versioning & migration manager |

### Microservice AI Agents & LLM Infrastructure
| Component | Technology | Description |
|-----------|------------|-------------|
| **LLM Inference** | Groq Cloud API | High-throughput LLM execution (`llama-3.1-8b-instant`, `llama3-70b-8192`, `llama-3.3-70b-versatile`) |
| **Agent Framework** | Custom Shared Framework (`agents/shared`) | Base agent class (`BaseAgent`), standard request/response models, latency & confidence metrics |
| **HTTP Inter-Service Client**| `httpx` | Asynchronous HTTP client for agent proxy & orchestrator calls |

### Containerization & Tooling
| Component | Technology | Description |
|-----------|------------|-------------|
| **Orchestration** | Docker Compose v2 | Multi-container environment management |
| **Environment Config** | Pydantic Settings | Environment-variable driven settings management |
| **Testing** | pytest + fakeredis | Unit and integration testing framework |

---

## 4. Deployed Services & Ports

| Service Name | Container Name | Port | Description |
|--------------|----------------|------|-------------|
| `backend` | `realty_os_backend` | `8000` | Core API Gateway, Auth, Database ORM, Agent Proxy & Orchestrator |
| `db` | `realty_os_db` | `5432` | PostgreSQL 16 + PostGIS + pgvector container |
| `redis` | `realty_os_redis` | `6379` | Redis key-value cache and session store |
| `property-discovery-agent` | `realty_os_agt01` | `8001` | **AGT-01**: Natural language property search and shortlist extraction |
| `lead-qualification-agent` | `realty_os_agt02` | `8002` | **AGT-02**: Lead scoring, intent classification, and tiering (HOT/WARM/COLD) |
| `buyer-agent` | `realty_os_agt03` | `8003` | **AGT-03**: Buyer assistant for guided search and preference refining |
| `property-agent` | `realty_os_agt04` | `8004` | **AGT-04**: Property seller assistant and listing metadata management |
| `recommendation-agent` | `realty_os_agt05` | `8005` | **AGT-05**: Personalized listing recommendation engine |
| `crm-agent` | `realty_os_agt06` | `8006` | **AGT-06**: Automatic CRM logging, lead interaction tracking, & timeline updates |

---

## 5. Agent Architecture & Catalog

The platform defines **15 specialized AI agents** organized across 4 operational clusters:

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                   AGENT CATALOG (15 AGENTS)                               │
├────────────────────────────┬────────────────────────────┬─────────────────────────────────┤
│ Discovery & Matching       │ Buyer & Seller Engagement │ Intelligence & Analytics        │
├────────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ AGT-01 Property Discovery* │ AGT-02 Lead Qualification* │ AGT-05 Developer Intelligence   │
│ AGT-07 Recommendation*     │ AGT-03 Buyer Assistant*    │ AGT-06 Investment Advisor       │
│ AGT-14 Inventory Management│ AGT-04 Seller Assistant*   │ AGT-08 Market Research          │
│                            │ AGT-11 Follow-up Agent     │ AGT-12 Property Valuation (AVM) │
├────────────────────────────┴────────────────────────────┴─────────────────────────────────┤
│ Transaction Execution                                                                     │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ AGT-09 Legal Due Diligence  │ AGT-10 CRM Automation*     │ AGT-13 Site Visit Coordinator     │
│ AGT-15 Negotiation Agent   │                            │                                   │
└────────────────────────────┴────────────────────────────┴─────────────────────────────────┘
* Indicates dedicated deployed microservice agent
```

### Deployed Microservice Agents Detail

1. **AGT-01: Property Discovery Agent** (`:8001`)
   - **Role**: Parses unstructured natural language user prompts into structured filters (locality, price range, BHK, amenities) and queries the backend database for matching property records.
   - **LLM Tier**: `llama-3.1-8b-instant`

2. **AGT-02: Lead Qualification Agent** (`:8002`)
   - **Role**: Analyzes buyer messages and profiles to evaluate purchase intent, budget suitability, and timeline readiness; assigns a lead score and tier (`HOT`, `WARM`, `COLD`).
   - **LLM Tier**: `llama-3.3-70b-versatile`

3. **AGT-03: Buyer Assistant Agent** (`:8003`)
   - **Role**: Assists prospective buyers through personalized dialog, answering property queries, refining criteria, and guiding the buyer towards site visit scheduling.
   - **LLM Tier**: `llama3-70b-8192`

4. **AGT-04: Seller Assistant Agent** (`:8004`)
   - **Role**: Guides property sellers through listing creation, property detail validation, media attachment, and price sanity checking.
   - **LLM Tier**: `llama-3.1-8b-instant`

5. **AGT-05: Property Recommendation Agent** (`:8005`)
   - **Role**: Generates personalized property recommendations based on buyer interaction history, saved searches, and vector-similarity matching.
   - **LLM Tier**: `llama-3.1-8b-instant`

6. **AGT-06: CRM Automation Agent** (`:8006`)
   - **Role**: Processes conversation events and agent interactions to automatically update lead stage, log notes, and update activity timelines in the CRM database.
   - **LLM Tier**: `llama-3.1-8b-instant`

---

## 6. Multi-Agent Pipeline Orchestrator

The system includes a dedicated multi-agent orchestration engine (`BackendOrchestrator` in `backend/app/orchestration/` and `agents/orchestrator/`), accessible via the `POST /api/v1/agents/orchestrate` endpoint.

```
                  POST /api/v1/agents/orchestrate
                                │
                                ▼
                   ┌──────────────────────────┐
                   │   Backend Orchestrator   │
                   └────────────┬─────────────┘
                                │
   ┌────────────────────────────┼────────────────────────────┐
   ▼                            ▼                            ▼
┌──────────────┐         ┌──────────────┐             ┌──────────────┐
│ Step 1:      │────────▶│ Step 2:      │────────────▶│ Step 3:      │
│ AGT-03 Buyer │         │ AGT-04 Prop  │             │ AGT-05 Reco  │
└──────────────┘         └──────────────┘             └──────────────┘
                                                             │
   ┌─────────────────────────────────────────────────────────┘
   ▼
┌──────────────┐         ┌──────────────┐             ┌──────────────┐
│ Step 4:      │────────▶│ Step 5:      │────────────▶│ Consolidated │
│ AGT-02 Lead  │         │ AGT-06 CRM   │             │ JSON Output  │
└──────────────┘         └──────────────┘             └──────────────┘
```

### Pipeline Flow
1. **Buyer Engagement (AGT-03)**: Extracts user intent and formats initial query context.
2. **Property Matching (AGT-04)**: Queries catalog for matching listings and attributes.
3. **Recommendation Enrichment (AGT-05)**: Enhances matches with similarity scoring.
4. **Lead Qualification (AGT-02)**: Evaluates buyer intent signals and updates lead score/tier.
5. **CRM Synchronization (AGT-06)**: Logs the interaction sequence and updates lead history in the database.
6. **Consolidated Response**: Returns execution traces, agent responses, confidence scores, and latency metrics.

---

## 7. Autonomous Memory Subsystem

The `memory_system/` package provides a 4-tier autonomous memory architecture:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                            MEMORY MANAGER FACADE                          │
│                            (memory/manager.py)                            │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ Session Memory   │         │ Long-Term Memory │         │ User Preferences │
│ (Redis Hash)     │         │ (PostgreSQL)     │         │ (PG + Redis)     │
│ TTL: 30-60 min   │         │ Permanent Log    │         │ Permanent/Cache  │
└──────────────────┘         └──────────────────┘         └──────────────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ Lead History     │
                             │ (PostgreSQL)     │
                             │ Append-Only Log  │
                             └──────────────────┘
```

### Memory Layers
1. **Session Memory**: In-memory Redis state capturing recent conversation turns per `session_id`. Expired via configurable TTL (30–60 minutes).
2. **Long-Term Memory**: Append-only PostgreSQL log tracking user interactions, summarized periodically using an LLM summarizer for prompt injection.
3. **User Preferences**: Dual-write pattern storing user criteria (preferred localities, budget, BHK) in PostgreSQL (source of truth) with Redis cache invalidation.
4. **Lead History**: Append-only interaction and status timeline linked to specific `lead_id` records in PostgreSQL.

---

## 8. Structured Error & Audit Logging Subsystem

The `error_logging/` package provides unified structured logging across all services:

- **Multi-Handler Architecture**:
  - **Console Handler**: Standard output with configurable minimum log level (`LOG_MIN_LEVEL_CONSOLE`).
  - **Rotating File Handler**: Log files written to `LOG_DIR` with configurable size rotation (`10 MB` default, 5 backups).
  - **PostgreSQL Handler**: Direct database logging pool persisting warning/error logs for centralized dashboard auditing.
- **Trace Context**: Injects `trace_id`, `user_id`, `agent_id`, and `session_id` into log records.

---

## 9. Database Architecture & Schema (V001 + Extensions)

The database schema (`V001__realty_os_full_schema.sql` plus migration `0001_post_v001_extensions`) operates in the `realty_os` PostgreSQL schema.

```
                    ┌─────────────────────────┐
                    │      organisations      │
                    └────────────┬────────────┘
                                 │
                                 ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│     locations    │◀──────│    properties    │──────▶│   media_assets   │
└──────────────────┘       └────────┬─────────┘       └──────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  residential_    │       │   commercial_    │       │  villas, plots,  │
│  properties      │       │   properties     │       │  warehouses      │
└──────────────────┘       └──────────────────┘       └──────────────────┘
       │                                                         │
       ▼                                                         ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      enquiries   │──────▶│      offers      │──────▶│    agreements    │
└──────────────────┘       └──────────────────┘       └──────────────────┘
       ▲
       │
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  agent_sessions  │       │    developers    │       │      users       │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

### Key Tables
- **`users`**: Platform users with role-based attributes (`BUYER`, `SELLER`, `BROKER`, `DEVELOPER`, `ADMIN`), auth tokens (`refresh_token`), and profile metadata.
- **`properties`**: Core listing entity containing pricing, transaction type, status, geometry (`geo_point` via PostGIS), and embeddings (`description_vector` via pgvector).
- **`residential_properties` / `commercial_properties`**: Property-type specific specifications (BHK, carpet area, floor number, zoning).
- **`locations`**: Normalized address and spatial location records.
- **`enquiries`**: Lead records with qualification tier (`HOT`, `WARM`, `COLD`), preferred localities, budget constraints, and agent interaction notes.
- **`agent_sessions`**: Tracks agent chat sessions, active agent IDs, interaction logs, and escalation status.
- **`developers`**: Developer firm profiles and project catalog metadata.

---

## 10. API Endpoints Reference

Base URL: `http://localhost:8000/api/v1`

### Endpoint Domains
- **Auth (`/auth`)**:
  - `POST /auth/register` — Register a new user
  - `POST /auth/login` — Login and obtain JWT access & refresh tokens
  - `POST /auth/refresh` — Refresh access token
  - `GET /auth/me` — Retrieve current authenticated user profile
- **Users (`/users`)**:
  - `GET /users/` — List users (Admin)
  - `GET /users/{id}` — Retrieve user profile
- **Properties (`/properties`)**:
  - `GET /properties/` — Filter and search property listings
  - `POST /properties/` — Create new property listing
  - `GET /properties/{id}` — Retrieve property details
  - `POST /properties/{id}/media` — Upload property media assets
- **Leads (`/leads`)**:
  - `GET /leads/` — List leads
  - `POST /leads/` — Create new lead
  - `GET /leads/stats` — Lead conversion & tier analytics
- **Developers (`/developers`)**:
  - `GET /developers/` — List developers
  - `POST /developers/` — Register developer firm profile
- **AI Agents (`/agents`)**:
  - `POST /agents/chat` — Proxy chat message to specific microservice agent
  - `POST /agents/orchestrate` — Trigger multi-agent orchestration pipeline
  - `GET /agents/` — List agent catalog & status
  - `GET /agents/{agent_id}/info` — Get agent specification and KPIs
  - `GET /agents/sessions/` — List active agent chat sessions
  - `GET /agents/sessions/{id}` — Retrieve session history
  - `PATCH /agents/sessions/{id}/escalate` — Escalate session to human broker

---

## 11. Complete Project Structure

```
stail/
├── backend/                             # Core FastAPI Gateway & Service (Port 8000)
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/              # Auth, Users, Properties, Leads, Agents, Developers
│   │   │   │   ├── agents.py           # Agent proxy & session endpoints
│   │   │   │   ├── auth.py             # Auth endpoints
│   │   │   │   ├── developers.py       # Developer endpoints
│   │   │   │   ├── leads.py            # Lead management endpoints
│   │   │   │   ├── properties.py       # Property endpoints
│   │   │   │   └── users.py            # User management endpoints
│   │   │   ├── dependencies/           # Auth guards & permission checkers
│   │   │   └── router.py               # Main API v1 router aggregator
│   │   ├── core/                       # App settings, security (JWT), exceptions
│   │   ├── db/                         # SQLAlchemy models & session factory
│   │   ├── orchestration/              # Multi-agent backend orchestrator engine
│   │   ├── schemas/                    # Pydantic v2 schemas
│   │   └── main.py                     # FastAPI application entrypoint
│   ├── alembic/                        # Alembic database migrations
│   ├── Dockerfile
│   └── pyproject.toml
│
├── agents/                             # AI Agent Microservices & Framework
│   ├── shared/                         # Common base agent, HTTP client, & schemas
│   │   ├── base_agent.py               # Abstract BaseAgent class
│   │   ├── backend_client.py           # Asynchronous backend HTTP client
│   │   └── schemas.py                  # Shared agent request/response schemas
│   │
│   ├── property-discovery/             # AGT-01: Property Discovery Agent (Port 8001)
│   ├── lead-qualification-agent/       # AGT-02: Lead Qualification Agent (Port 8002)
│   ├── buyer-agent/                    # AGT-03: Buyer Assistant Agent (Port 8003)
│   ├── property-agent/                 # AGT-04: Property Seller Agent (Port 8004)
│   ├── recommendation-agent/           # AGT-05: Recommendation Agent (Port 8005)
│   ├── crm-agent/                      # AGT-06: CRM Automation Agent (Port 8006)
│   └── orchestrator/                   # Standalone agent orchestration package
│
├── memory_system/                      # 4-Layer Autonomous Memory Subsystem
│   ├── memory/                         # Session, Long-Term, Preferences, Lead History managers
│   ├── memory_db/                      # Postgres & Redis client connections
│   ├── memory_models/                  # Pydantic schemas for memory objects
│   ├── memory_settings.py              # Memory configuration
│   └── README.md
│
├── error_logging/                      # Centralized Structured Logging Subsystem
│   ├── handlers/                       # Console, Rotating File, & Postgres DB handlers
│   ├── config.py                       # Logging settings
│   └── logger.py                       # Logger initialization & facade
│
├── db/                                 # PostgreSQL + PostGIS + pgvector Docker setup
│   └── Dockerfile
│
├── docs/                               # Documentation & Verification Guides
│   ├── database_schema.md
│   └── PHASE2_VERIFICATION.md
│
├── V001__realty_os_full_schema.sql     # Full SQL DDL schema initialization script
├── docker-compose.yml                  # Full-stack Docker orchestration
├── check_agents.sh                     # Automated agent health check script
├── instruction.md                      # Local setup and execution guide
├── architecture.md                     # System architecture documentation
└── README.md                           # Main repository README
```

---

## 12. Security Architecture

| Security Domain | Strategy & Implementation |
|-----------------|---------------------------|
| **Authentication** | JSON Web Tokens (JWT) using HS256 algorithm; 30-min access token expiry, 7-day refresh token expiry. |
| **Password Storage** | Passlib with `bcrypt` password hashing scheme. |
| **Role-Based Control** | Endpoint guards enforcing user roles (`BUYER`, `SELLER`, `BROKER`, `DEVELOPER`, `ADMIN`). |
| **Data Isolation** | Tenant and user isolation at database query layer. |
| **Injection Defense** | Parameterized queries enforced via SQLAlchemy ORM; strict schema validation via Pydantic v2. |
| **Sensitive Data** | Environment variables for API keys and secrets; strictly excluded from version control. |

---

*Document updated on July 24, 2026*