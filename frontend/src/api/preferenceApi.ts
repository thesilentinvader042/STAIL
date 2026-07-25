import apiClient from './client';
import type { UserPreferences } from '../types';

export const fetchUserPreferences = (userId: string) =>
  apiClient.get<UserPreferences>(`/api/v1/users/${userId}/preferences`);

export const updateUserPreferences = (userId: string, payload: Partial<UserPreferences>) =>
  apiClient.patch<UserPreferences>(`/api/v1/users/${userId}/preferences`, payload);
