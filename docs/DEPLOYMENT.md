# STAIL Realty OS — Deployment Guide

This guide describes production deployment options for STAIL Realty OS.

---

## 1. Local Containerized Deployment

To deploy the entire platform locally via Docker Compose:

```bash
# 1. Build and launch all services
docker compose up -d --build

# 2. Run database migrations inside backend container
docker compose exec backend alembic upgrade head

# 3. Inspect container status
docker compose ps
```

---

## 2. Environment Variables Checklist (`.env`)

```ini
# Backend Core
PORT=8000
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/realty_os
REDIS_URL=redis://redis:6379/0
SECRET_KEY=production_secret_key_change_me

# AI Providers
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key

# Agent Microservices URLs
BUYER_AGENT_URL=http://buyer-agent:8003
PROPERTY_AGENT_URL=http://property-agent:8004
RECOMMENDATION_AGENT_URL=http://recommendation-agent:8005
LEAD_QUALIFICATION_AGENT_URL=http://lead-qualification-agent:8002
CRM_AGENT_URL=http://crm-agent:8006
```

---

## 3. Production Frontend Build

```bash
cd frontend
npm run build
```

The optimized production assets are generated in `frontend/dist/` and can be served via Nginx or Cloudflare Pages.

---

## 4. Verification Checklist

- [ ] All 5 agent containers report `healthy` on `/health`.
- [ ] Database migrations applied up to `0002_perf_idx`.
- [ ] Redis responds to `PING`.
- [ ] CORS policies allow frontend domain origin.
