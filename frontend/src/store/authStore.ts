import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';
import { fetchCurrentUser, login, logoutApi } from '../api/authApi';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isInitialized: boolean;
  setAuth: (token: string, refreshToken: string, user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  loginUser: (email: string, password: string) => Promise<User>;
  fetchProfile: () => Promise<User>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      isInitialized: false,

      setAuth: (token, refreshToken, user) => set({ token, refreshToken, user }),
      setTokens: (token, refreshToken) => set({ token, refreshToken }),
      setUser: (user) => set({ user }),

      logout: () => {
        const { token } = get();
        if (token) {
          logoutApi().catch(() => {});
        }
        set({ token: null, refreshToken: null, user: null });
      },

      loginUser: async (email, password) => {
        const { data } = await login(email, password);
        set({ token: data.access_token, refreshToken: data.refresh_token });
        const userRes = await fetchCurrentUser();
        set({ user: userRes.data, isInitialized: true });
        return userRes.data;
      },

      fetchProfile: async () => {
        const { data } = await fetchCurrentUser();
        set({ user: data });
        return data;
      },

      checkAuth: async () => {
        const { token } = get();
        if (!token) {
          set({ isInitialized: true });
          return;
        }
        try {
          const { data } = await fetchCurrentUser();
          set({ user: data, isInitialized: true });
        } catch {
          set({ token: null, refreshToken: null, user: null, isInitialized: true });
        }
      },
    }),
    {
      name: 'stail-auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
);