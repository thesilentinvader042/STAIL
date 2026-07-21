# STAIL Realty OS — Property Discovery Agent

[![CI](https://github.com/<your-org>/PropertyDiscoveryAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-org>/PropertyDiscoveryAgent/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Task 13 — Working Agent V1**  
> An AI-native backend for Indian real estate — natural language property search, lead qualification, and 15 specialised AI agents powered by Anthropic Claude.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Database Migrations (Alembic)](#database-migrations-alembic)
- [Running Locally](#running-locally)
- [API Reference](#api-reference)
- [AI Agent Registry](#ai-agent-registry)
- [Running Tests](#running-tests)
- [CI/CD](#cicd)
- [Project Structure](#project-structure)

---

## Overview

STAIL Realty OS is a backend API for an AI-native Indian real estate platform. It exposes five core domains:

| Domain | Description |
|--------|-------------|
| **Auth** | JWT-based authentication (access + refresh tokens) |
| **Users** | Multi-role user management (buyer, seller, broker, developer, investor, admin) |
| **Properties** | Full property CRUD with search, filtering, media, and AI-powered ranking |
| **Leads** | CRM pipeline with intent scoring, FSM status transitions, and broker assignment |
| **AI Agents** | 15 specialised Claude-powered agents across 4 clusters |

### Property Discovery Agent (AGT-01)

The flagship agent converts natural-language buyer intent into a ranked property shortlist:

1. **Understands** free-text requirements ("2BHK in Bandra under 1.2 crore, ready to move")
2. **Extracts** structured preferences (city, BHK, price, furnishing, possession timeline)
3. **Generates** SQL search criteria applied against the property database
4. **Ranks** results by listing score, features, and match confidence

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI App                          │
│                                                          │
│  /api/v1/                                                │
│  ├── auth/          JWT register, login, refresh         │
│  ├── users/         Profile CRUD, role management        │
│  ├── properties/    Listings, search, media              │
│  ├── leads/         CRM pipeline, intent scoring         │
│  └── agents/        15 AI agents via Anthropic Claude    │
│                                                          │
│  app/core/          Settings, security, exceptions       │
│  app/db/            SQLAlchemy models + session          │
│  app/schemas/       Pydantic v2 request/response models  │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │   PostgreSQL    │   (Alembic migrations)
       └───────┬────────┘
               │
       ┌───────┴────────┐
       │  Anthropic API  │   (Claude Sonnet / Opus)
       └────────────────┘
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| PostgreSQL | 15+ |
| pip | Latest |

Optional:
- Redis 7+ (for future caching / rate limiting)
- Docker + Docker Compose (for local infrastructure)

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/<your-org>/PropertyDiscoveryAgent.git
cd PropertyDiscoveryAgent

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values (see Environment Variables section below)
```

### 3. Set up the database

```bash
# Create PostgreSQL database
createdb realty_os

# Run Alembic migrations
alembic -c alembic/alembic.ini upgrade head
```

### 4. Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Environment Variables

Create a `.env` file in the project root:

```ini
# Application
APP_ENV=development
APP_NAME=STAIL Realty OS
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# API
API_V1_PREFIX=/api/v1
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Database (PostgreSQL)
DATABASE_URL=postgresql://realty_user:realty_pass@localhost:5432/realty_os
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# JWT Auth
SECRET_KEY=your-very-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI (Anthropic)
ANTHROPIC_API_KEY=sk-ant-...

# AWS (for media storage)
AWS_REGION=ap-south-1
S3_BUCKET_NAME=realty-os-media
```

> ⚠️ **Never commit `.env` to version control.** It is already in `.gitignore`.

---

## Database Migrations (Alembic)

Alembic is configured with autogenerate — it diffs your ORM models against the live DB schema.

```bash
# Apply all pending migrations
alembic -c alembic/alembic.ini upgrade head

# Generate a new migration after changing ORM models
alembic -c alembic/alembic.ini revision --autogenerate -m "add_xyz_column"

# Downgrade one step
alembic -c alembic/alembic.ini downgrade -1

# Show current revision
alembic -c alembic/alembic.ini current

# Show migration history
alembic -c alembic/alembic.ini history --verbose
```

> The `alembic.ini` is located at `alembic/alembic.ini`. Always pass `-c alembic/alembic.ini` from the project root.

---

## Running Locally

```bash
# Development server with auto-reload
uvicorn app.main:app --reload

# Production-style (4 workers)
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0"}

# Readiness check (tests DB connectivity)
curl http://localhost:8000/readiness
```

### Docker Compose (local infrastructure)

```yaml
# docker-compose.yml (example)
version: "3.9"
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: realty_os
      POSTGRES_USER: realty_user
      POSTGRES_PASSWORD: realty_pass
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

```bash
docker compose up -d
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create new account |
| `POST` | `/auth/login` | Email + password → JWT pair |
| `POST` | `/auth/refresh` | Rotate access token |
| `POST` | `/auth/logout` | Invalidate refresh token |
| `GET` | `/auth/me` | Current user profile |
| `POST` | `/auth/password/change` | Change password |
| `POST` | `/auth/password/reset` | Request reset email |
| `POST` | `/auth/password/confirm` | Confirm reset with token |

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/users/` | Admin | List all users |
| `GET` | `/users/{id}` | Self/Admin | Get user profile |
| `PATCH` | `/users/{id}` | Self/Admin | Update profile |
| `DELETE` | `/users/{id}` | Admin | Deactivate user |
| `GET` | `/users/{id}/properties` | Self/Admin | User's listings |
| `GET` | `/users/{id}/leads` | Self/Admin | User's leads |

### Properties

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/properties/` | Required | Create listing |
| `GET` | `/properties/` | Public | Search/filter listings |
| `GET` | `/properties/{id}` | Public | Property detail |
| `PATCH` | `/properties/{id}` | Owner/Admin | Update listing |
| `DELETE` | `/properties/{id}` | Owner/Admin | Soft delete (off_market) |
| `POST` | `/properties/{id}/view` | Public | Increment view counter |
| `POST` | `/properties/{id}/media` | Owner/Admin | Attach media URL |
| `DELETE` | `/properties/{id}/media/{mid}` | Owner/Admin | Remove media |
| `GET` | `/properties/{id}/similar` | Public | Similar listings |
| `PATCH` | `/properties/{id}/verify` | Admin | Mark as verified |
| `PATCH` | `/properties/{id}/feature` | Admin | Toggle featured |

**Search parameters for `GET /properties/`:**

```
city, locality, state, property_type, listing_type, status,
bhk_config, price_min, price_max, area_sqft_min, area_sqft_max,
is_ready_to_move, furnishing_status, is_featured, verified,
page, page_size
```

### Leads

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/leads/` | Optional | Create lead (anonymous OK) |
| `GET` | `/leads/` | Required | List leads |
| `GET` | `/leads/stats/summary` | Required | Pipeline summary |
| `GET` | `/leads/{id}` | Buyer/Broker/Admin | Lead detail |
| `PATCH` | `/leads/{id}` | Buyer/Broker/Admin | Update lead |
| `PATCH` | `/leads/{id}/qualify` | Required | Re-run intent scoring |
| `PATCH` | `/leads/{id}/assign` | Broker/Admin | Assign to broker |
| `POST` | `/leads/{id}/schedule-visit` | Required | Schedule site visit |
| `PATCH` | `/leads/{id}/close` | Required | Close won/lost |
| `DELETE` | `/leads/{id}` | Broker/Admin | Archive lead |

**Intent Scoring Rules (AGT-02 simplified):**

| Signal | Score |
|--------|-------|
| Budget range declared | +15 |
| Preferred localities | +10 |
| Specific BHK preference | +10 |
| Timeline ≤ 6 months | +20 |
| Timeline ≤ 12 months | +10 |
| Inquiry on specific property | +15 |
| Loan required | +10 |
| High-intent channel (WhatsApp/direct) | +10 |

Tiers: **Hot** ≥ 70 | **Warm** ≥ 40 | **Cold** < 40

### AI Agents

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/agents/chat` | Required | Send message to any agent |
| `GET` | `/agents/` | Public | List all 15 agents |
| `GET` | `/agents/{agent_id}/info` | Public | Agent specification |
| `GET` | `/agents/sessions/` | Required | My sessions |
| `GET` | `/agents/sessions/{id}` | Required | Session detail |
| `PATCH` | `/agents/sessions/{id}/escalate` | Required | Escalate to human |
| `DELETE` | `/agents/sessions/{id}` | Required | Close session |
| `GET` | `/agents/sessions/stats` | Admin | Usage summary |

**Chat request example:**

```json
POST /api/v1/agents/chat
{
  "agent_id": "AGT-01",
  "message": "I need a 2BHK in Bandra or Juhu under 1.2 crore, ready to move",
  "context": {
    "user_budget_confirmed": true,
    "preferred_floor": "high"
  }
}
```

---

## AI Agent Registry

15 agents across 4 clusters, each powered by Claude Sonnet or Opus:

| Agent ID | Name | Cluster | Model |
|----------|------|---------|-------|
| AGT-01 | **Property Discovery Agent** | Discovery & Matching | Sonnet |
| AGT-02 | Lead Qualification Agent | Buyer & Seller Engagement | Sonnet |
| AGT-03 | Buyer Assistant Agent | Buyer & Seller Engagement | Opus |
| AGT-04 | Seller Assistant Agent | Buyer & Seller Engagement | Sonnet |
| AGT-05 | Developer Intelligence Agent | Intelligence & Analytics | Opus |
| AGT-06 | Investment Advisor Agent | Intelligence & Analytics | Opus |
| AGT-07 | Property Recommendation Agent | Discovery & Matching | Sonnet |
| AGT-08 | Market Research Agent | Intelligence & Analytics | Opus |
| AGT-09 | Legal Due Diligence Agent | Transaction Execution | Opus |
| AGT-10 | CRM Automation Agent | Transaction Execution | Sonnet |
| AGT-11 | Follow-up Agent | Buyer & Seller Engagement | Sonnet |
| AGT-12 | Property Valuation Agent | Intelligence & Analytics | Sonnet |
| AGT-13 | Site Visit Coordinator Agent | Transaction Execution | Sonnet |
| AGT-14 | Inventory Management Agent | Discovery & Matching | Sonnet |
| AGT-15 | Negotiation Agent | Transaction Execution | Opus |

**Escalation:** Sessions with confidence < 0.65 are automatically escalated to human support.

---

## Running Tests

The test suite uses **SQLite in-memory** — no PostgreSQL required.

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run a specific domain
pytest tests/test_agents.py -v
pytest tests/test_properties.py -v

# Run with coverage HTML report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Test structure

```
tests/
├── conftest.py          # SQLite engine, session fixture, auth helpers
├── test_auth.py         # 18 tests — register, login, tokens, passwords
├── test_users.py        # 13 tests — CRUD, admin, scoping
├── test_properties.py   # 22 tests — full property lifecycle + admin
├── test_leads.py        # 20 tests — scoring unit tests, FSM, pipeline
└── test_agents.py       # 20 tests — all 15 agents, sessions, mocked LLM
```

---

## CI/CD

GitHub Actions runs on every push and PR to `main`:

```
lint  →  ruff format check + ruff lint
  ↓
test  →  pytest (SQLite) + coverage ≥ 60% + coverage.xml artifact
  ↓
security (advisory)  →  pip-audit vulnerability scan
```

Configure Codecov by adding `CODECOV_TOKEN` to your repository secrets.

---

## Project Structure

```
PropertyDiscoveryAgent/
├── alembic/
│   ├── alembic.ini          # Alembic configuration
│   ├── env.py               # Migration environment
│   └── versions/            # Generated migration scripts
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── dependencies/
│   │       │   └── auth.py  # JWT guards, role dependencies
│   │       └── endpoints/
│   │           ├── agents.py
│   │           ├── auth.py
│   │           ├── leads.py
│   │           ├── properties.py
│   │           └── users.py
│   ├── core/
│   │   ├── config.py        # Pydantic settings
│   │   ├── exceptions.py    # HTTP exception classes
│   │   └── security.py      # JWT + bcrypt helpers
│   ├── db/
│   │   ├── models/
│   │   │   └── models.py    # SQLAlchemy ORM (User, Property, Lead, …)
│   │   └── session.py       # Engine + SessionLocal + get_db
│   └── schemas/
│       └── schemas.py       # Pydantic v2 request/response models
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_properties.py
│   ├── test_leads.py
│   └── test_agents.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env                     # Local secrets (not committed)
├── .gitignore
├── pyproject.toml           # Build config + dev deps
├── requirements.txt
└── README.md
```

---

## Contributing

1. Fork the repo and create a feature branch
2. Make your changes and add/update tests
3. Run `ruff check . && ruff format .` before committing
4. Open a pull request — CI must pass before merging

---

## License

MIT © STAIL Technologies
