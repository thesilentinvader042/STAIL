# STAIL Realty OS — Agent Architecture & Pipeline

This document details the multi-agent AI architecture powering the conversational property search and lead management system.

---

## 5-Agent Pipeline Architecture

```
                               ┌─────────────────────────┐
                               │     User Query / Chat   │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │     Backend Router      │
                               └────────────┬────────────┘
                                            │
           ┌────────────────────────────────┼────────────────────────────────┐
           │                                │                                │
           ▼                                ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│    Buyer Agent      │          │   Property Agent    │          │Recommendation Agent │
│   (Port 8003)       │          │   (Port 8004)       │          │   (Port 8005)       │
│ Profiles user intent│          │ Queries DB catalog  │          │ Scores & ranks fits │
└──────────┬──────────┘          └──────────┬──────────┘          └──────────┬──────────┘
           │                                │                                │
           └────────────────────────────────┼────────────────────────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Lead Qualification Agt  │
                               │   (Port 8002)           │
                               │ Scores buyer intent 0-100│
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │       CRM Agent         │
                               │   (Port 8006)           │
                               │  Schedules visits & FSM │
                               └─────────────────────────┘
```

---

## Agent Specifications

### 1. Buyer Agent (`buyer-agent`)
- **Port**: 8003
- **Purpose**: Extracts structured buyer preferences (budget range, location, BHK requirements, family size, amenities) from raw natural language input.
- **Model**: Groq Llama 3 / Claude

### 2. Property Agent (`property-agent`)
- **Port**: 8004
- **Purpose**: Translates structured buyer criteria into precise SQL filter queries against the property database catalog.

### 3. Recommendation Agent (`recommendation-agent`)
- **Port**: 8005
- **Purpose**: Ranks matching properties using semantic matching score and generates personalized highlights for each listing.

### 4. Lead Qualification Agent (`lead-qualification-agent`)
- **Port**: 8002
- **Purpose**: Computes lead intent score (0 to 100) and categorizes lead into COLD, WARM, or HOT tiers.

### 5. CRM Agent (`crm-agent`)
- **Port**: 8006
- **Purpose**: Manages lead state machine transitions (NEW -> QUALIFIED -> VISITED -> CLOSED), site visit bookings, and follow-up tasks.

---

## Session Memory & Context Injection

- **Redis Session Cache**: Stores transient message context per `session_id`.
- **Durable Preferences**: Persisted in PostgreSQL database per `user_id`.
- **Memory Injection Strategy**: On every turn, the Backend Orchestrator fetches historical preferences and injects them into the agent system prompt context.
