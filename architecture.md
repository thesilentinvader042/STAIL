# STAIL Realty OS - Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** July 13, 2026  
**Technology Stack:** FastAPI, PostgreSQL, Redis, Docker, Groq/LLMs

---

## 1. System Overview

STAIL Realty OS is an AI-native real estate operating system designed to automate:
- Property discovery
- Lead qualification
- Developer intelligence
- Market research
- Customer engagement
- Sales operations
- Investment advisory

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENTS                                      │
│  (Web App, Mobile App, Third-party APIs, Swagger UI)                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTP/HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Port 8000)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Auth      │  │   Users     │  │ Properties  │  │   Leads     │   │
│  │   Endpoints │  │   Endpoints │  │   Endpoints │  │  Endpoints  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│  ┌─────────────┐  ┌─────────────┐                                     │
│  │  Developers │  │   Agents    │                                     │
│  │   Endpoints │  │   Proxy     │                                     │
│  └─────────────┘  └─────────────┘                                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM + Pydantic Schemas                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │ Internal HTTP
                          ▼
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌────────┐          ┌──────────┐         ┌──────────────┐
│PostgreSQL│         │  Redis   │         │    AI        │
│ :5432   │         │  :6379   │         │   Agents     │
└────────┘          └──────────┘         └──────────────┘
                                            │
                      ┌─────────────────────┼─────────────────────┐
                      ▼                     ▼                     ▼
              ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
              │ Property     │     │    Lead      │     │    More      │
              │ Discovery    │     │ Qualification│     │   Agents     │
              │ (AGT-01)     │     │  (AGT-02)    │     │  (Future)    │
              │ Port: 8001   │     │  Port: 8002  │     │              │
              └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 3. Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.115+ |
| Server | Uvicorn | 0.30+ |
| ORM | SQLAlchemy | 2.0+ |
| Database | PostgreSQL | 16+ |
| Cache/Sessions | Redis | 7 |
| Authentication | JWT (python-jose) | 3.3+ |
| Password Hashing | bcrypt | 4.0.1 |
| Data Validation | Pydantic | 2.9+ |
| Migrations | Alembic | 1.13+ |

### Agents
| Component | Technology |
|-----------|------------|
| LLM Provider | Groq |
| Framework | FastAPI + Custom Agent Framework |
| Backend Client | httpx |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Containerization | Docker + Docker Compose |
| Extensions | PostGIS, pgvector |

---

## 4. Database Schema (V001)

### Core Tables

| Table | Purpose |
|-------|---------|
| `organisations` | Developer/broker firm profiles |
| `users` | Platform users (buyers, sellers, brokers, admins) |
| `locations` | Property addresses (linked to properties) |
| `properties` | Base property records |
| `residential_properties` | Residential-specific details |
| `commercial_properties` | Commercial-specific details |
| `villas`, `plots`, `warehouses`, `coworking_spaces` | Property type-specific tables |
| `media_assets` | Property images, videos, documents |
| `enquiries` | Lead/enquiry records |
| `offers` | Property offers |
| `agreements` | Sale/rent agreements |
| `avm_valuations` | Automated Valuation Model results |
| `rera_registrations` | RERA project registrations |
| `site_visits` | Scheduled property visits |
| `neighbourhood_scores` | Area scoring data |

### Extension Tables (Post-V001)

```sql
-- Added via Alembic migration 0001_post_v001_extensions
CREATE TABLE developers (...);       -- Developer profiles (legacy API compat)
CREATE TABLE agent_sessions (...);   -- AI agent conversation tracking

-- Additional columns on users
ALTER TABLE users ADD COLUMN refresh_token VARCHAR(512);
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);

-- Additional columns on enquiries
ALTER TABLE enquiries ADD COLUMN source VARCHAR(30);
ALTER TABLE enquiries ADD COLUMN tier VARCHAR(20);
ALTER TABLE enquiries ADD COLUMN preferred_bhk INTEGER;
ALTER TABLE enquiries ADD COLUMN preferred_localities JSONB;
ALTER TABLE enquiries ADD COLUMN agent_notes JSONB;
-- ... and more
```

### Schema Design Patterns

- **UUID Primary Keys**: All tables use `UUID` as primary key
- **Soft Deletes**: `deleted_at` timestamp column for data retention
- **Timestamps**: `created_at`, `updated_at` on all tables via `TimestampMixin`
- **Enums**: PostgreSQL ENUM types for type safety (property_type_enum, listing_status_enum, etc.)
- **Geospatial**: PostGIS for geo_point geography column
- **Vectors**: pgvector for embedding-based search (description_vector)

---

## 5. API Architecture

### Base URL
```
http://localhost:8000/api/v1
```

### API Domains

| Domain | Endpoints | Description |
|--------|-----------|-------------|
| **Auth** | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me` | User authentication |
| **Users** | `/users/`, `/users/{id}` | User management |
| **Properties** | `/properties/`, `/properties/{id}`, `/properties/{id}/media` | Property CRUD |
| **Leads** | `/leads/`, `/leads/{id}`, `/leads/stats` | Lead/enquiry management |
| **Agents** | `/agents/`, `/agents/chat`, `/agents/sessions` | AI agent proxy |
| **Developers** | `/developers/`, `/developers/{id}` | Developer profiles |

### Request/Response Patterns

```python
# Pagination Request
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20  # max 100

# Paginated Response
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[Any]
```

---

## 6. Authentication & Authorization

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  /login  │────▶│ Generate │
└──────────┘     └──────────┘     │  Tokens  │
                                  └────┬─────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
            ┌─────────────┐   ┌──────────────┐   ┌─────────────┐
            │ access_token│   │refresh_token │   │ Store in DB │
            │ (30 min)    │   │  (7 days)    │   │ (users table)│
            └─────────────┘   └──────────────┘   └─────────────┘
```

### Token Structure

**Access Token Payload:**
```json
{
  "sub": "user_uuid",
  "exp": 1800,
  "type": "access"
}
```

**Refresh Token Payload:**
```json
{
  "sub": "user_uuid",
  "exp": 604800,
  "type": "refresh"
}
```

### Authorization Roles

| Role | Description |
|------|-------------|
| `BUYER` | End user searching/buying properties |
| `SELLER` | Property owner listing |
| `BROKER` | Real estate agent |
| `DEVELOPER` | Property developer |
| `ADMIN` | Platform administrator |

### Role Guards (Code)

```python
# Only authenticated users
CurrentUser = Annotated[User, Depends(get_current_active_user)]

# Admin only
AdminUser = Annotated[User, Depends(require_admin)]

# Brokers + Admins
BrokerOrAdmin = Annotated[User, Depends(require_role("broker", "admin"))]

# Developers + Admins
DeveloperOrAdmin = Annotated[User, Depends(require_role("developer", "admin"))]
```

---

## 7. Agent Architecture

### Current Agents

#### Property Discovery Agent (AGT-01)
- **Port:** 8001
- **Purpose:** Converts natural language intent into ranked property shortlists
- **LLM Model:** llama3-8b-8192
- **Flow:**
  1. Extract structured preferences from user message
  2. Fetch matching properties from backend
  3. Return ranked property list

#### Lead Qualification Agent (AGT-02)
- **Port:** 8002
- **Purpose:** Scores and tiers incoming leads
- **LLM Model:** llama-3.3-70b-versatile
- **Flow:**
  1. Extract buying signals using LLM
  2. Score budget, timeline, intent
  3. Grade lead (HOT/WARM/COLD)

### Agent Communication

```
Backend                        Property Discovery Agent
    │                                    │
    │  POST /agents/chat                │
    │  { agent_id: "AGT-01",            │
    │    message: "3BHK in Mumbai" }    │
    ├───────────────────────────────────▶│
    │                                    │ (Process with LLM)
    │                                    │
    │  { response, properties[],        │
    │    confidence_score }             │
    ◀───────────────────────────────────┤
```

### Agent Schemas

```python
class AgentChatRequest(BaseModel):
    agent_id: str
    message: str
    lead_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    context: dict | None = None

class AgentChatResponse(BaseModel):
    agent_id: str
    response: str
    confidence_score: float | None
    escalated: bool
    escalation_reason: str | None
    latency_ms: int | None
    metadata: dict | None
```

---

## 8. Project Structure

```
stail/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/     # API route handlers
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── properties.py
│   │   │   │   ├── leads.py
│   │   │   │   ├── agents.py
│   │   │   │   └── developers.py
│   │   │   ├── dependencies/
│   │   │   │   └── auth.py    # Auth guards
│   │   │   ├── router.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py      # Settings
│   │   │   ├── security.py    # JWT, passwords
│   │   │   └── exceptions.py  # Custom errors
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   └── models.py  # SQLAlchemy models
│   │   │   ├── session.py     # DB connection
│   │   │   └── seeds/         # Seed data
│   │   ├── schemas/
│   │   │   └── schemas.py     # Pydantic schemas
│   │   └── main.py            # FastAPI app
│   ├── alembic/               # DB migrations
│   ├── tests/                 # Test suite
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
│
├── agents/                    # AI Agent Microservices
│   ├── property-discovery/
│   │   ├── agent/
│   │   │   ├── main.py        # FastAPI app
│   │   │   ├── config.py
│   │   │   ├── discovery_agent.py
│   │   │   └── schemas.py
│   │   ├── config/
│   │   ├── models/
│   │   ├── scoring/
│   │   ├── tools/
│   │   └── Dockerfile
│   │
│   └── lead-qualification-agent/
│       ├── agent/
│       ├── config/
│       ├── models/
│       ├── scoring/
│       └── Dockerfile
│
├── db/                        # Database Docker
│   └── Dockerfile             # PostgreSQL + PostGIS + pgvector
│
├── docker-compose.yml         # Full stack orchestration
├── V001__realty_os_full_schema.sql
├── memory.md
└── architecture.md
```

---

## 9. Docker Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| `backend` | realty_os_backend | 8000 | FastAPI application |
| `db` | realty_os_db | 5432 | PostgreSQL + PostGIS + pgvector |
| `redis` | realty_os_redis | 6379 | Redis cache |
| `property-discovery-agent` | realty_os_agt01 | 8001 | Property Discovery Agent |
| `lead-qualification-agent` | realty_os_agt02 | 8002 | Lead Qualification Agent |

### Starting the Stack

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

---

## 10. Key Configuration

### Environment Variables (.env)

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://realty_user:realty_pass@localhost:5432/realty_os

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Auth
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
GROQ_API_KEY=<your-groq-api-key>

# Agent URLs
PROPERTY_DISCOVERY_AGENT_URL=http://localhost:8001
LEAD_QUALIFICATION_AGENT_URL=http://localhost:8002
```

---

## 11. Security Features

| Feature | Implementation |
|---------|----------------|
| Password Hashing | bcrypt (via passlib) |
| JWT Tokens | Access (30 min) + Refresh (7 days) |
| Role-Based Access | Role guards on endpoints |
| CORS | Configurable allowed origins |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| Input Validation | Pydantic schemas |
| Error Handling | Global exception handler |

---

## 12. Future Considerations

### Planned Agents (15 total)
1. Property Discovery Agent (AGT-01) ✅
2. Lead Qualification Agent (AGT-02) ✅
3. Developer Intelligence Agent
4. Market Research Agent
5. Pricing Agent
6. Mortgage Advisor Agent
7. Legal Compliance Agent
8. Property Inspection Agent
9. ... and more

### Planned Features
- Vector search with pgvector
- Advanced AI memory system
- Real-time notifications
- WebSocket support
- Advanced analytics dashboard

---

## 13. API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

*Document generated on July 13, 2026*