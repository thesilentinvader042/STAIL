import { create } from 'zustand';
import type { Message } from '../types';

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  loading: boolean;
  error: string | null;
  leadGrade: string | null;
  confidence: number | null;
  /** Set to true when the chat was restored from a past session */
  isResumedSession: boolean;
  /** Formatted date string of the resumed session, e.g. "25 Jul 2026" */
  resumedDate: string | null;
  addMessage: (message: Message) => void;
  setSessionId: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setMetadata: (leadGrade?: string, confidence?: number) => void;
  /** Hydrate store with a prior session's history and mark it as resumed */
  loadSessionHistory: (sessionId: string, messages: Message[], resumedDate?: string) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: null,
  loading: false,
  error: null,
  leadGrade: null,
  confidence: null,
  isResumedSession: false,
  resumedDate: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: message.id || `msg-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
          createdAt: message.createdAt || new Date().toISOString(),
        },
      ],
    })),

  setSessionId: (id) => set({ sessionId: id }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setMetadata: (leadGrade, confidence) =>
    set({
      leadGrade: leadGrade !== undefined ? leadGrade : null,
      confidence: confidence !== undefined ? confidence : null,
    }),

  loadSessionHistory: (sessionId, messages, resumedDate) =>
    set({
      sessionId,
      messages,
      isResumedSession: true,
      resumedDate: resumedDate ?? new Date().toLocaleDateString('en-IN'),
      error: null,
    }),

  clearChat: () =>
    set({
      messages: [],
      sessionId: null,
      error: null,
      leadGrade: null,
      confidence: null,
      isResumedSession: false,
      resumedDate: null,
    }),
}));