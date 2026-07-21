# Agent Orchestrator

Central coordination layer for multi-agent workflows in STAIL Realty OS.

## Overview

The orchestrator coordinates sequential calls to all agents:
1. AGT-03 (Buyer Agent) — Extract requirements
2. AGT-04 (Property Agent) — Search and filter
3. AGT-05 (Recommendation Agent) — Rank and annotate
4. AGT-02 (Lead Qualification Agent) — Score lead
5. AGT-06 (CRM Agent) — Store conversation and follow-ups

## Phase 1 Status

**Stub implementation only.** Directory structure created; full pipeline deferred to Phase 2.

## Configuration

Agent URLs loaded from environment via `config.py`:
- `BUYER_AGENT_URL` (default: http://localhost:8003)
- `PROPERTY_AGENT_URL` (default: http://localhost:8004)
- `RECOMMENDATION_AGENT_URL` (default: http://localhost:8005)
- `LEAD_QUALIFICATION_AGENT_URL` (default: http://localhost:8002)
- `CRM_AGENT_URL` (default: http://localhost:8006)
