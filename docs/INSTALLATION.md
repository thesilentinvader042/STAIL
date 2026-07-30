# STAIL Realty OS — Installation & Setup Guide

This guide details the step-by-step installation process for running the STAIL Realty OS platform locally for development and testing.

---

## Prerequisites

Ensure your system has the following software installed:

- **Python**: 3.11 or higher
- **Node.js**: v18.0.0 or higher
- **Docker & Docker Compose**: latest desktop or engine release
- **PostgreSQL**: v15 or higher (or via Docker container)
- **Redis**: v7.0 or higher (or via Docker container)

---

## 1. Environment Setup & Repository Cloning

```bash
# Clone the repository
git clone https://github.com/thesilentinvader042/STAIL.git
cd STAIL

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Backend Setup

```bash
# Install backend dependencies in editable mode
pip install -e .

# Configure environment variables
cp backend/.env.example backend/.env

# Run database migrations
cd backend
alembic upgrade head
cd ..
```

---

## 3. Microservices (Docker Compose)

Start the agent microservices and infrastructure containers:

```bash
docker compose up -d
```

This starts:
- `buyer-agent` (Port 8003)
- `property-agent` (Port 8004)
- `recommendation-agent` (Port 8005)
- `lead-qualification-agent` (Port 8002)
- `crm-agent` (Port 8006)
- `postgres` (Port 5432)
- `redis` (Port 6379)

---

## 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The web application will be accessible at `http://localhost:5173`.

---

## 5. Health Check Verification

Verify system readiness:

```bash
# Backend health endpoint
curl http://localhost:8000/health

# Check running Docker services
docker compose ps
```

---

## Troubleshooting & Common Issues

- **Port Conflicts**: If port `8000`, `5432`, or `6379` is in use, modify `.env` ports accordingly.
- **Database Connection Refused**: Ensure PostgreSQL container or service is up and running before running Alembic migrations.
- **Missing API Keys**: Ensure `GROQ_API_KEY` or `OPENAI_API_KEY` is supplied in `backend/.env` for AI features.
