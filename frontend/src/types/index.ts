export type UserRole = 'BUYER' | 'SELLER' | 'BROKER' | 'DEVELOPER' | 'ADMIN';

export interface User {
  id: string;
  email: string;
  phone: string;
  full_name: string;
  role: UserRole;
  is_nri?: boolean;
  language_pref?: string;
  language_preference?: string;
  city?: string;
  state?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  phone: string;
  full_name: string;
  password: string;
  role: UserRole;
  is_nri?: boolean;
  language_pref?: string;
  language_preference?: string;
  city?: string;
  state?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Property {
  id: string;
  title?: string;
  name?: string;
  description?: string;
  city: string;
  locality?: string;
  location?: string | Record<string, any>;
  state?: string;
  pincode?: string;
  price: number;
  asking_price?: number;
  property_type: string;
  bhk?: number;
  carpet_area_sqft?: number;
  super_built_up?: number;
  possession_status?: string;
  furnishing_status?: string;
  floor_number?: number;
  total_floors?: number;
  facing?: string;
  amenities?: string[];
  gallery_images?: string[];
  image_url?: string;
  video_url?: string;
  virtual_tour_url?: string;
  residential?: Record<string, any>;
  attributes?: Record<string, any>;
  developer?: {
    id: string;
    name: string;
    city?: string;
    website?: string;
  };
  relevance_score?: number;
  match_reasons?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface PropertyListResponse {
  items: Property[];
  total: number;
  page: number;
  pages: number;
}

export interface OrchestrateRequest {
  message: string;
  session_id?: string;
  lead_id?: string;
}

export interface OrchestrateResponse {
  response: string;
  properties: Property[];
  lead_grade?: string;
  confidence: number;
  session_id: string;
  metadata?: Record<string, any>;
}

export interface AgentChatRequest {
  agent_id: string;
  message: string;
  session_id?: string;
  lead_id?: string;
  property_id?: string;
  context?: Record<string, any>;
}

export interface AgentChatResponse {
  session_id: string;
  agent_id: string;
  agent_name: string;
  response: string;
  tool_calls?: Array<{
    id: string;
    type: string;
    function: {
      name: string;
      arguments: string;
    };
  }>;
  confidence_score?: number;
  escalated?: boolean;
  escalation_reason?: string;
  latency_ms?: number;
  created_at: string;
}

export interface AgentSession {
  id: string;
  agent_id: string;
  agent_name: string;
  session_status: string;
  input_text?: string;
  output_text?: string;
  llm_model?: string;
  input_tokens?: number;
  output_tokens?: number;
  latency_ms?: number;
  confidence_score?: number;
  escalated?: boolean;
  escalation_reason?: string;
  created_at: string;
  completed_at?: string;
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  properties?: Property[];
  confidence?: number;
  leadGrade?: string;
  createdAt?: string;
}

export interface PropertyFilterParams {
  page?: number;
  limit?: number;
  city?: string;
  property_type?: string;
  min_price?: number;
  max_price?: number;
  bhk?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface UserPreferences {
  property_type?: string[];
  budget_min?: number | null;
  budget_max?: number | null;
  preferred_locations?: string[];
  must_haves?: string[];
  deal_breakers?: string[];
  inferred?: Record<string, any>;
}

export interface Lead {
  id: string;
  property_id?: string | null;
  buyer_id?: string | null;
  broker_id?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  source: string;
  channel: string;
  status: string;
  tier: string;
  intent_score: number;
  budget_min?: number | null;
  budget_max?: number | null;
  preferred_bhk?: number | null;
  preferred_localities?: string[] | null;
  possession_timeline_months?: number | null;
  is_loan_required: boolean;
  last_contacted_at?: string | null;
  next_followup_at?: string | null;
  site_visit_scheduled_at?: string | null;
  notes?: string | null;
  agent_notes?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface LeadSummaryStats {
  total: number;
  by_tier: {
    hot: number;
    warm: number;
    cold: number;
  };
  by_status: {
    new: number;
    site_visit_scheduled: number;
    offer_made: number;
    closed_won: number;
    closed_lost: number;
  };
  conversion_rate: number;
}

export interface LeadFilterParams {
  tier?: 'HOT' | 'WARM' | 'COLD' | string;
  status?: string;
  source?: string;
  page?: number;
  page_size?: number;
}

export interface LeadUpdatePayload {
  status?: string;
  tier?: string;
  intent_score?: number;
  assigned_broker_id?: string;
  notes?: string;
  next_followup_at?: string;
  site_visit_scheduled_at?: string;
}

