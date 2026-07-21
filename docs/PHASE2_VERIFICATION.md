# Phase 2 End-to-End Verification Guide

> Covers all deliverables from **Phase 2** of `implementation_plan_wk2.md`:
> Tasks 6–12 (5 agent microservices + backend orchestrator + error logging).

---

## Prerequisites — confirm everything is running

```bash
cd /Users/adityamaharana/Desktop/stail
docker compose ps
```

Every service should show `healthy` or `running`. If any are stopped:

```bash
docker compose up -d
```

---

## Step 1 — Infrastructure health

Verify each service responds before testing anything else.

```bash
# Backend
curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: {"status": "ok", "version": "1.0.0"}

# Database
docker compose exec db psql -U realty_user -d realty_os \
  -c "SELECT COUNT(*) FROM realty_os.users;"
# Expected: count row (even 0 is fine — proves table exists)

# Redis
docker compose exec redis redis-cli ping
# Expected: PONG

# All 5 agents
curl -s http://localhost:8002/health | python3 -m json.tool  # AGT-02 Lead Qualification
curl -s http://localhost:8003/health | python3 -m json.tool  # AGT-03 Buyer
curl -s http://localhost:8004/health | python3 -m json.tool  # AGT-04 Property
curl -s http://localhost:8005/health | python3 -m json.tool  # AGT-05 Recommendation
curl -s http://localhost:8006/health | python3 -m json.tool  # AGT-06 CRM
```

Each agent should return:
```json
{"status": "ok", "agent": "AGT-0X", "version": "..."}
```

If any agent returns connection refused, check its logs:

```bash
docker compose logs lead-qualification-agent --tail=30
docker compose logs buyer-agent --tail=30
docker compose logs property-agent --tail=30
docker compose logs recommendation-agent --tail=30
docker compose logs crm-agent --tail=30
```

---

## Step 2 — Database migration state

Confirm the `0001_post_v001` columns exist:

```bash
docker compose exec db psql -U realty_user -d realty_os \
  -c "\d realty_os.users" | grep -E "refresh_token|avatar_url"
```

Expected:
```
 refresh_token | character varying(512) | ...
 avatar_url    | character varying(500) | ...
```

If missing, add them manually:

```bash
docker compose exec db psql -U realty_user -d realty_os -c "
ALTER TABLE realty_os.users ADD COLUMN IF NOT EXISTS refresh_token VARCHAR(512);
ALTER TABLE realty_os.users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);
"
```

Confirm `agent_sessions` and `developers` tables exist:

```bash
docker compose exec db psql -U realty_user -d realty_os \
  -c "\dt realty_os.*" | grep -E "agent_sessions|developers"
```

If missing, run migrations:

```bash
docker compose exec backend python -m alembic -c /app/alembic.ini upgrade head
```

---

## Step 3 — Authentication

**3a. Register a user:**

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "aditya@stail.com",
    "password": "Test1234!",
    "full_name": "Aditya Test",
    "role": "BUYER"
  }' | python3 -m json.tool
```

Expected: `201 Created` with a user object containing `user_id`, `email`, `role`, `is_active: true`.

**3b. Login and capture the token:**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "aditya@stail.com", "password": "Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
```

Expected: a long JWT string printed (not empty, not an error).

**3c. Verify the token works:**

```bash
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: your user profile returned.

---

## Step 4 — Backend core APIs

Seed at least one property so AGT-04 has something to search.

**4a. Create a property:**

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
  }' | python3 -m json.tool
```

Expected: `201 Created` with a `property_id`.

**4b. List properties:**

```bash
curl -s "http://localhost:8000/api/v1/properties/?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: `{"total": 1, "items": [...]}` with the property you just created.

---

## Step 5 — Individual agent endpoints (Task 6–10)

Test each agent's `/chat` endpoint directly to isolate failures before running the full pipeline.

**AGT-02 — Lead Qualification (port 8002):**

```bash
curl -s -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGT-02",
    "message": "I want a 3BHK in Mumbai, budget 1.5 crore, need to buy in 3 months",
    "session_id": null,
    "conversation_history": [],
    "context": null
  }' | python3 -m json.tool
```

Expected: `metadata.grade` is one of `"A"`, `"B"`, `"C"`, `"D"` and `confidence_score` is between 0 and 1.

**AGT-03 — Buyer Agent (port 8003):**

```bash
curl -s -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGT-03",
    "message": "Looking for a 3BHK in Mumbai under 1.5 crore",
    "session_id": null,
    "conversation_history": [],
    "context": null
  }' | python3 -m json.tool
```

Expected: `metadata.preferences` contains structured fields:
```json
{
  "bhk_type": ["3BHK"],
  "cities": ["Mumbai"],
  "budget_max": 15000000,
  "confidence_score": 0.8
}
```

**AGT-04 — Property Agent (port 8004):**

```bash
curl -s -X POST http://localhost:8004/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGT-04",
    "message": "Find me properties",
    "session_id": null,
    "conversation_history": [],
    "context": {
      "preferences": {
        "cities": ["Mumbai"],
        "bhk_type": ["3BHK"],
        "budget_max": 15000000,
        "property_types": ["RESIDENTIAL"]
      }
    }
  }' | python3 -m json.tool
```

Expected: `metadata.properties` is a list (may be empty if no properties were seeded in Step 4).

**AGT-05 — Recommendation Agent (port 8005):**

```bash
curl -s -X POST http://localhost:8005/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGT-05",
    "message": "Rank these for me",
    "session_id": null,
    "conversation_history": [],
    "context": {
      "preferences": {
        "cities": ["Mumbai"],
        "bhk_type": ["3BHK"],
        "budget_max": 15000000
      },
      "properties": [
        {
          "title": "3BHK Bandra",
          "city": "Mumbai",
          "asking_price": 14500000,
          "attributes": {"bhk_type": "3BHK"}
        }
      ]
    }
  }' | python3 -m json.tool
```

Expected: `metadata.ranked_properties` list where each item has `composite_score` and `annotation` fields.

**AGT-06 — CRM Agent (port 8006):**

```bash
curl -s -X POST http://localhost:8006/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGT-06",
    "message": "Store this lead",
    "session_id": null,
    "conversation_history": [],
    "context": {
      "user_id": "00000000-0000-0000-0000-000000000001",
      "grade": "A",
      "score": 85,
      "source": "AGENT_CHAT"
    }
  }' | python3 -m json.tool
```

Expected: `metadata.stored` is `true` and `metadata.follow_up_created` is `true` (because grade is A).

---

## Step 6 — Full orchestration pipeline (Task 11)

This is the Phase 2 core test. It calls `POST /agents/orchestrate` which runs the complete
AGT-03 → AGT-04 → AGT-05 → AGT-02 → AGT-06 sequence through `BackendOrchestrator`.

Watch backend logs in one terminal while running the request in another:

```bash
# Terminal 1 — watch the pipeline execute
docker compose logs -f backend | grep -E "Orchestrate|AGT-0|circuit|retry"
```

```bash
# Terminal 2 — fire the request
curl -s -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "I want a 3BHK flat in Mumbai under 1.5 crore, ready to move in"}' \
  | python3 -m json.tool
```

Expected log output (Terminal 1):
```
Orchestrate: calling AGT-03 (Buyer Agent)
Orchestrate: calling AGT-04 (Property Agent)
Orchestrate: calling AGT-05 (Recommendation Agent)
Orchestrate: calling AGT-02 (Lead Qualification Agent)
Orchestrate: calling AGT-06 (CRM Agent)
```

Expected response (Terminal 2):
```json
{
  "response": "...(combined text from all agents)...",
  "properties": [...up to 5 property dicts with composite_score and annotation...],
  "lead_grade": "A",
  "confidence": 0.75,
  "session_id": "some-uuid",
  "metadata": {
    "preferences": {"cities": ["Mumbai"], "bhk_type": ["3BHK"], "budget_max": 15000000},
    "total_properties": 1,
    "ranked_count": 1,
    "grade": "A",
    "score": 85
  }
}
```

---

## Step 7 — Circuit breaker and resilience (Task 12)

Verify the orchestrator degrades gracefully when an agent is down.

```bash
# Stop one agent
docker compose stop buyer-agent

# Fire orchestrate — should still return 200, not 500
curl -s -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "3BHK Mumbai"}' | python3 -m json.tool
```

Expected: `200 OK` with an empty `preferences: {}` (AGT-03 skipped) but the rest of the pipeline
runs. After 3 failed attempts you should see in the logs:

```
Agent AGT-03 failed after 3 attempts: ...
Circuit breaker OPEN for AGT-03 after 3 failures
```

Restore the agent:

```bash
docker compose start buyer-agent
```

---

## Step 8 — Session continuity

Verify a second call with the same `session_id` reuses the session.

```bash
# First call — capture the session_id
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "3BHK in Pune under 80 lakhs"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

echo "Session ID: $SESSION_ID"

# Follow-up in the same session
curl -s -X POST http://localhost:8000/api/v1/agents/orchestrate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\": \"What about 2BHK options instead?\", \"session_id\": \"$SESSION_ID\"}" \
  | python3 -m json.tool
```

Expected: second response contains the same `session_id` and the pipeline runs again with the new query.

---

## Step 9 — OpenAPI docs

Open in your browser: **http://localhost:8000/docs**

Confirm these endpoints are visible under the **AI Agents** section:

- `POST /api/v1/agents/chat`
- `POST /api/v1/agents/orchestrate`
- `GET  /api/v1/agents/`
- `GET  /api/v1/agents/sessions/`

You can also use the Swagger UI to fire the `orchestrate` endpoint interactively after
clicking **Authorize** and pasting your JWT token.

---

## Implementation status reference

| Component | Status | Notes |
|---|---|---|
| Backend auth (register/login/me) | Full | JWT access + refresh tokens |
| AGT-02 Lead Qualification | Full | Groq LLM grades leads A/B/C/D |
| AGT-03 Buyer Agent | Full | Groq extracts structured preferences |
| AGT-04 Property Agent | Full | Queries backend DB, scores results |
| AGT-05 Recommendation Agent | Full | Composite scoring + LLM annotations |
| AGT-06 CRM Agent | Full | Creates lead in DB, follow-up for A/B |
| Backend orchestrator pipeline | Full | Circuit breaker + exponential backoff retry |
| Memory system | Optional | Disabled if `memory.manager` not importable — pipeline still works |
| Error logging | Optional | Falls back to stdlib logging if `error_logging` not importable |

---

## Troubleshooting quick reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `"An unexpected error occurred"` on register/login | `refresh_token` column missing | Run Step 2 ALTER TABLE commands |
| `connection refused` on agent port | Agent container not started | `docker compose up -d <agent-name>` |
| Orchestrate returns empty `properties` | No properties seeded in DB | Run Step 4a to create a property |
| Agent returns `confidence_score: 0.0` | Groq API key invalid or rate limited | Check `GROQ_API_KEY` in `backend/.env` and each agent's `.env` |
| `Circuit breaker OPEN` in logs | Agent failed 3 consecutive times | Check agent logs; fix and restart; breaker resets after 60s |
| `alembic: not found` | Container running old image | `docker compose build --no-cache backend && docker compose up -d backend` |
| `No script_location key` | Running alembic from wrong directory | Use `python -m alembic -c /app/alembic.ini upgrade head` |
