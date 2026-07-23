# STAIL Realty OS — Local Setup & Execution Guide

This guide explains how to set up, run, and replicate the full **STAIL Realty OS multi-agent pipeline** locally on your machine.


## 🛠️ Step-by-Step Local Setup

### 1. Prerequisites
Ensure you have the following installed:
* **Docker & Docker Compose** (v2.0+)
* **Python 3.11+**
* **cURL** or **Postman** for API testing
* A **Groq API Key** (Get one for free at [console.groq.com](https://console.groq.com))

---

### 2. Environment Configuration (`.env` setup)

Copy all `.env.example` files to `.env` across the project:

```bash
# 1. Main backend env
cp backend/.env.example backend/.env

# 2. Agent microservice envs
cp agents/buyer-agent/.env.example agents/buyer-agent/.env
cp agents/lead-qualification-agent/.env.example agents/lead-qualification-agent/.env
cp agents/property-agent/.env.example agents/property-agent/.env
cp agents/recommendation-agent/.env.example agents/recommendation-agent/.env
cp agents/crm-agent/.env.example agents/crm-agent/.env
cp agents/property-discovery/.env.example agents/property-discovery/.env
```

> 🔑 **Important:** Open each created `.env` file and replace `your_groq_api_key_here` with your actual **Groq API key**.

---

### 3. Build & Launch Containers

Run the following command to build all 5 agent microservices, backend, database, and Redis containers:

```bash
docker compose up -d --build
```

Verify that all containers are healthy:

```bash
docker compose ps
```

---

### 4. Database Migrations & Schema Fix

Apply the database migrations to ensure all user columns and tables exist:

```bash
# Apply schema columns fix if needed
docker compose exec db psql -U realty_user -d realty_os -c "
ALTER TABLE realty_os.users ADD COLUMN IF NOT EXISTS refresh_token VARCHAR(512);
ALTER TABLE realty_os.users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);
"

# Run Alembic migrations
docker compose exec backend python -m alembic -c /app/alembic.ini upgrade head
```

---

### 5. Replicating the End-to-End Test

#### Step A: Register & Login User
```bash
# Register User
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@stail.com",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "role": "BUYER"
  }'

# Login & Capture JWT Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@stail.com", "password": "TestPassword123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "JWT Token: $TOKEN"
```

#### Step B: Seed a Property
```bash
curl -s -X POST http://localhost:8000/api/v1/properties/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "3BHK in Bandra West",
    "property_type": "RESIDENTIAL",
    "transaction_type": "SALE",
    "asking_price": 15000000,
    "carpet_area_sqft": 950,
    "attributes": {"bhk_type": "3BHK", "num_bedrooms": 3},
    "tags": ["3BHK", "mumbai", "bandra"],
    "location": {
      "address_line_1": "16 Hill Road",
      "locality": "Bandra West",
      "city": "Mumbai",
      "state_code": "MH",
      "pin_code": "400050"
    }
  }'
```

#### Step C: Execute Orchestration Pipeline
Execute the full 5-agent AI pipeline (`AGT-03 → AGT-04 → AGT-05 → AGT-02 → AGT-06`):

```bash
curl -s -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "I want a 3BHK flat in Mumbai under 1.5 crore, ready to move in"}' \
  | python3 -m json.tool
```

---

## 🧹 Useful Operations & Commands

* **Rebuild a specific agent (e.g. after code changes):**
  ```bash
  docker compose up -d --build buyer-agent
  ```
* **View agent logs:**
  ```bash
  docker compose logs -f buyer-agent
  ```
* **Check Service Health:**
  * Backend: `http://localhost:8000/health`
  * AGT-02 (Lead Qualification): `http://localhost:8002/health`
  * AGT-03 (Buyer Agent): `http://localhost:8003/health`
  * AGT-04 (Property Agent): `http://localhost:8004/health`
  * AGT-05 (Recommendation Agent): `http://localhost:8005/health`
  * AGT-06 (CRM Agent): `http://localhost:8006/health`
