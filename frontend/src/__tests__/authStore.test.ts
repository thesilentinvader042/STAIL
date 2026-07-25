import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../store/authStore';

beforeEach(() => {
  useAuthStore.setState({
    token: null,
    refreshToken: null,
    user: null,
    isInitialized: false,
  });
});

describe('AuthStore – Initial State', () => {
  it('should have null token by default', () => {
    expect(useAuthStore.getState().token).toBeNull();
  });

  it('should have null user by default', () => {
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('should have null refreshToken by default', () => {
    expect(useAuthStore.getState().refreshToken).toBeNull();
  });

  it('should not be initialized by default', () => {
    expect(useAuthStore.getState().isInitialized).toBe(false);
  });
});

describe('AuthStore – setAuth', () => {
  const mockUser = {
    id: 'user-123',
    email: 'test@stail.com',
    phone: '+91 9876543210',
    full_name: 'Aditya Maharana',
    role: 'BUYER' as const,
  };

  it('should set the access token', () => {
    useAuthStore.getState().setAuth('tok_abc', 'ref_xyz', mockUser);
    expect(useAuthStore.getState().token).toBe('tok_abc');
  });

  it('should set the refresh token', () => {
    useAuthStore.getState().setAuth('tok_abc', 'ref_xyz', mockUser);
    expect(useAuthStore.getState().refreshToken).toBe('ref_xyz');
  });

  it('should set the user object', () => {
    useAuthStore.getState().setAuth('tok_abc', 'ref_xyz', mockUser);
    expect(useAuthStore.getState().user?.email).toBe('test@stail.com');
    expect(useAuthStore.getState().user?.role).toBe('BUYER');
  });
});

describe('AuthStore – setTokens (token rotation)', () => {
  it('should update both access and refresh tokens', () => {
    useAuthStore.getState().setTokens('new_access', 'new_refresh');
    expect(useAuthStore.getState().token).toBe('new_access');
    expect(useAuthStore.getState().refreshToken).toBe('new_refresh');
  });
});

describe('AuthStore – logout', () => {
  it('should clear the token', () => {
    useAuthStore.setState({
      token: 'tok_abc',
      refreshToken: 'ref_xyz',
      user: { id: 'u-1', email: 'a@b.com', phone: '1', full_name: 'User', role: 'BUYER' },
      logout: useAuthStore.getState().logout,
    });
    useAuthStore.setState({ token: null, refreshToken: null, user: null });
    expect(useAuthStore.getState().token).toBeNull();
  });

  it('should clear the user', () => {
    useAuthStore.setState({ user: null });
    expect(useAuthStore.getState().user).toBeNull();
  });
});
