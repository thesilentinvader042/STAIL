import apiClient from './client';
import type {
  Lead,
  LeadFilterParams,
  LeadSummaryStats,
  LeadUpdatePayload,
} from '../types';

export const fetchLeads = (params?: LeadFilterParams) =>
  apiClient.get<Lead[]>('/api/v1/leads/', { params });

export const fetchLeadSummaryStats = () =>
  apiClient.get<LeadSummaryStats>('/api/v1/leads/stats/summary');

export const fetchLeadById = (leadId: string) =>
  apiClient.get<Lead>(`/api/v1/leads/${leadId}`);

export const updateLead = (leadId: string, payload: LeadUpdatePayload) =>
  apiClient.patch<Lead>(`/api/v1/leads/${leadId}`, payload);

export const qualifyLead = (leadId: string) =>
  apiClient.patch<Lead>(`/api/v1/leads/${leadId}/qualify`);

export const scheduleSiteVisit = (leadId: string, visitDatetime: string) =>
  apiClient.post<Lead>(`/api/v1/leads/${leadId}/schedule-visit`, null, {
    params: { visit_datetime: visitDatetime },
  });

export const assignLead = (leadId: string, brokerId: string) =>
  apiClient.patch<Lead>(`/api/v1/leads/${leadId}/assign`, null, {
    params: { broker_id: brokerId },
  });

export const closeLead = (leadId: string, outcome: 'won' | 'lost', reason?: string) =>
  apiClient.patch<Lead>(`/api/v1/leads/${leadId}/close`, null, {
    params: { outcome, reason },
  });
