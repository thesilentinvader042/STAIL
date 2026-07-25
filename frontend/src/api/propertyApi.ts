import apiClient from './client';
import type { Property, PropertyFilterParams, PropertyListResponse } from '../types';

export const fetchProperties = (params: PropertyFilterParams = {}) =>
  apiClient.get<PropertyListResponse>('/api/v1/properties/', { params });

export const fetchPropertyById = (id: string) =>
  apiClient.get<Property>(`/api/v1/properties/${id}`);
