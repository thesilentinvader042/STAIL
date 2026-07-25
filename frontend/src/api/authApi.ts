import apiClient from './client';
import type { RegisterPayload, TokenResponse, User } from '../types';

export const login = (email: string, password: string) =>
  apiClient.post<TokenResponse>('/api/v1/auth/login', { email, password });

export const register = (payload: RegisterPayload) =>
  apiClient.post<User>('/api/v1/auth/register', payload);

export const refreshToken = (refreshTokenStr: string) =>
  apiClient.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: refreshTokenStr });

export const fetchCurrentUser = () =>
  apiClient.get<User>('/api/v1/auth/me');

export const logoutApi = () =>
  apiClient.post('/api/v1/auth/logout');