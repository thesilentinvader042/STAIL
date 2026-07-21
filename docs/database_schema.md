# STAIL Realty OS - Database Schema

This document outlines the master database architecture for STAIL Realty OS, aligned with the Task 5 Database Framework.

## Core Models

### 1. User
Represents all platform personas: buyers, sellers, brokers, developers, investors, and admins.
- **Identity**: `email`, `phone`, `full_name`
- **Role**: `role` (enum), `is_active`, `is_verified`
- **Profile**: `city`, `state`, `language_preference`, `avatar_url`

### 2. Property
The master property record, supporting 6 distinct property types using single-table inheritance (discriminated by `property_type`).
- **Classification**: `property_type` (residential, commercial, plot, villa, warehouse, coworking), `listing_type` (sale, rent, lease, fractional), `status`
- **Ownership**: `owner_id` (User), `developer_id` (Developer), `broker_id` (User)
- **Location**: `address_line1`, `locality`, `city`, `state`, `pin_code`, `lat/lng`
- **Pricing**: `base_price`, `price_psf`
- **RERA**: `rera_number`, `possession_date`, `is_ready_to_move`, `construction_stage`
- **Area**: `carpet_area_sqft`, `built_up_area_sqft`, `super_built_up_area_sqft`
- **Residential Config**: `bhk_config`, `bedrooms`, `bathrooms`, `furnishing_status`

### 3. PropertyMedia
Assets attached to properties.
- **Attributes**: `media_type` (photo, floor_plan, virtual_tour, etc.), `url`, `is_primary`, `sequence`
- **AI Additions**: `ai_tags` (JSONB), `ai_quality_score`

### 4. Developer
Master records of top real estate developers (Task 4).
- **Identity**: `name`, `website`, `city`, `state`
- **Contact**: `contact_email`, `contact_phone`
- **Portfolio**: `inventory_types` (JSONB), `projects` (JSONB)
- **Meta**: `is_verified`, `ranking`

### 5. Lead
Tracks buyer/investor interest in properties and handles the Lead Qualification Agent pipeline.
- **Actors**: `property_id`, `buyer_id`, `broker_id`
- **Qualification**: `source`, `status`, `tier` (hot, warm, cold, unqualified), `intent_score` (0-100)
- **Preferences**: `budget_min`, `budget_max`, `preferred_bhk`, `preferred_localities` (JSONB)
- **Tracking**: `last_contacted_at`, `agent_notes` (JSONB)

### 6. AgentSession
Tracks conversations between users and AI agents (AGT-01 through AGT-15).
- **Session**: `user_id`, `lead_id`, `agent_id`, `session_status`
- **Conversation**: `input_text`, `output_text`, `conversation_history` (JSONB), `context_snapshot` (JSONB)
- **Performance**: `llm_model`, `latency_ms`, `confidence_score`, `escalated`

## Memory System Tables
The memory system maintains its own isolated tables inside the same database for contextual AI features (Task 15).

### user_memory
Append-only log for long-term semantic memory retrieval.
- `user_id`, `memory_type`, `content` (JSONB)

### user_preferences
Mutable record of known user preferences (both explicit and inferred).
- `user_id`, `preferences` (JSONB)

### lead_events
Event sourcing for lead lifecycle changes.
- `lead_id`, `event_type`, `payload` (JSONB), `agent_id`
