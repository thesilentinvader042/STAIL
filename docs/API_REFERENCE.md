# STAIL Realty OS — API Reference

All backend endpoints are exposed under `/api/v1`.

---

## Authentication & Headers

Standard requests use Bearer JWT token authentication:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Endpoint Domains Summary

| Domain | Base Path | Description |
|---|---|---|
| Auth | `/api/v1/auth` | User registration, login, token refresh, and logout |
| Users | `/api/v1/users` | User profile management and preference storage |
| Properties | `/api/v1/properties` | Property listings search, filter, creation, and detail |
| Leads | `/api/v1/leads` | CRM pipeline management, FSM state updates, and visits |
| Agents | `/api/v1/agents` | AI multi-agent chat orchestration and session memory |

---

## 1. Authentication Endpoints

### `POST /api/v1/auth/register`
Register a new user account.
- **Request Body**:
  ```json
  {
    "email": "buyer@example.com",
    "password": "Password123!",
    "full_name": "Jane Doe",
    "role": "BUYER"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "email": "buyer@example.com",
    "full_name": "Jane Doe",
    "role": "BUYER"
  }
  ```

### `POST /api/v1/auth/login`
Authenticate credentials and receive access tokens.
- **Request Body**:
  ```json
  {
    "email": "buyer@example.com",
    "password": "Password123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

## 2. Properties Endpoints

### `GET /api/v1/properties/`
Search and filter property listings with optional Redis caching.
- **Query Parameters**: `city`, `locality`, `property_type`, `price_min`, `price_max`, `page`, `page_size`
- **Response** (`200 OK`):
  ```json
  [
    {
      "property_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      "title": "Modern 3BHK Apartment",
      "asking_price": 25000000,
      "property_type": "RESIDENTIAL",
      "listing_status": "ACTIVE",
      "location": {
        "city": "Mumbai",
        "locality": "Bandra West"
      }
    }
  ]
  ```

---

## 3. Leads (CRM) Endpoints

### `GET /api/v1/leads/`
Fetch lead pipeline (broker access).
- **Query Parameters**: `status`, `tier`, `assigned_broker_id`
- **Response** (`200 OK`):
  ```json
  [
    {
      "enquiry_id": "c395b669-e092-4217-bf41-69276fa4d033",
      "contact_name": "John Smith",
      "status": "QUALIFIED",
      "tier": "HOT",
      "intent_score": 85
    }
  ]
  ```

### `PATCH /api/v1/leads/{id}/qualify`
Advance lead status state machine.
- **Request Body**:
  ```json
  {
    "status": "QUALIFIED",
    "notes": "Verified budget and timeline"
  }
  ```

---

## 4. AI Agents Endpoints

### `POST /api/v1/agents/orchestrate`
Orchestrate chat message through the 5-agent pipeline.
- **Request Body**:
  ```json
  {
    "message": "Looking for 3BHK in Bandra under 3 Cr",
    "session_id": "d1a8e994-0000-4000-8000-000000000000"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "session_id": "d1a8e994-0000-4000-8000-000000000000",
    "reply": "Here are top 3BHK options matching your criteria in Bandra West...",
    "recommended_properties": []
  }
  ```
