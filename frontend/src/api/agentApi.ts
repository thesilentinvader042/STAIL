import apiClient from './client';
import type {
  AgentChatRequest,
  AgentChatResponse,
  AgentSession,
  OrchestrateResponse,
} from '../types';

export const orchestrateChat = (message: string, sessionId?: string | null, leadId?: string | null) =>
  apiClient.post<OrchestrateResponse>('/api/v1/agents/orchestrate', {
    message,
    session_id: sessionId || undefined,
    lead_id: leadId || undefined,
  });

export const sendAgentChat = (payload: AgentChatRequest) =>
  apiClient.post<AgentChatResponse>('/api/v1/agents/chat', payload);

export const fetchSessions = (agentId?: string, page = 1, pageSize = 20) =>
  apiClient.get<AgentSession[]>('/api/v1/agents/sessions/', {
    params: {
      agent_id: agentId || undefined,
      page,
      page_size: pageSize,
    },
  });

export const fetchSessionById = (sessionId: string) =>
  apiClient.get<AgentSession>(`/api/v1/agents/sessions/${sessionId}`);

export const fetchSessionHistory = (sessionId: string) =>
  apiClient.get<{
    session_id: string;
    turns: Array<{ role: 'user' | 'assistant'; content: string }>;
    current_search_filters?: Record<string, any>;
  }>(`/api/v1/agents/sessions/${sessionId}/history`);