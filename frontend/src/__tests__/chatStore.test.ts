import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../store/chatStore';
import type { Message } from '../types';

beforeEach(() => {
  useChatStore.getState().clearChat();
});

describe('ChatStore – Initial State', () => {
  it('should have empty messages array', () => {
    expect(useChatStore.getState().messages).toHaveLength(0);
  });

  it('should have null sessionId', () => {
    expect(useChatStore.getState().sessionId).toBeNull();
  });

  it('should have loading=false', () => {
    expect(useChatStore.getState().loading).toBe(false);
  });

  it('should have null error', () => {
    expect(useChatStore.getState().error).toBeNull();
  });

  it('should have null leadGrade', () => {
    expect(useChatStore.getState().leadGrade).toBeNull();
  });

  it('should have null confidence', () => {
    expect(useChatStore.getState().confidence).toBeNull();
  });
});

describe('ChatStore – addMessage', () => {
  const userMessage: Message = {
    role: 'user',
    content: '3BHK in Bandra West under 2.5 Crore',
  };

  it('should add a user message to the list', () => {
    useChatStore.getState().addMessage(userMessage);
    expect(useChatStore.getState().messages).toHaveLength(1);
  });

  it('should store the message content correctly', () => {
    useChatStore.getState().addMessage(userMessage);
    expect(useChatStore.getState().messages[0].content).toBe('3BHK in Bandra West under 2.5 Crore');
  });

  it('should auto-generate an id for the message', () => {
    useChatStore.getState().addMessage(userMessage);
    expect(useChatStore.getState().messages[0].id).toBeTruthy();
  });

  it('should auto-generate a createdAt timestamp', () => {
    useChatStore.getState().addMessage(userMessage);
    expect(useChatStore.getState().messages[0].createdAt).toBeTruthy();
  });

  it('should accumulate multiple messages', () => {
    useChatStore.getState().addMessage({ role: 'user', content: 'Query 1' });
    useChatStore.getState().addMessage({ role: 'assistant', content: 'Response 1', properties: [] });
    useChatStore.getState().addMessage({ role: 'user', content: 'Query 2' });
    expect(useChatStore.getState().messages).toHaveLength(3);
  });

  it('should store properties on assistant messages', () => {
    const properties = [{ id: 'p-1', city: 'Mumbai', price: 25000000, property_type: 'APARTMENT' }];
    useChatStore.getState().addMessage({ role: 'assistant', content: 'Found properties', properties });
    expect(useChatStore.getState().messages[0].properties).toHaveLength(1);
  });
});

describe('ChatStore – setSessionId', () => {
  it('should set a session ID', () => {
    useChatStore.getState().setSessionId('sess-abc-123');
    expect(useChatStore.getState().sessionId).toBe('sess-abc-123');
  });

  it('should allow resetting session ID to null', () => {
    useChatStore.getState().setSessionId('sess-abc-123');
    useChatStore.getState().setSessionId(null);
    expect(useChatStore.getState().sessionId).toBeNull();
  });
});

describe('ChatStore – setMetadata (orchestration results)', () => {
  it('should set lead grade', () => {
    useChatStore.getState().setMetadata('A', 0.95);
    expect(useChatStore.getState().leadGrade).toBe('A');
  });

  it('should set confidence score', () => {
    useChatStore.getState().setMetadata('B', 0.72);
    expect(useChatStore.getState().confidence).toBe(0.72);
  });

  it('should accept grade without confidence', () => {
    useChatStore.getState().setMetadata('C');
    expect(useChatStore.getState().leadGrade).toBe('C');
    expect(useChatStore.getState().confidence).toBeNull();
  });
});

describe('ChatStore – setLoading', () => {
  it('should set loading to true', () => {
    useChatStore.getState().setLoading(true);
    expect(useChatStore.getState().loading).toBe(true);
  });

  it('should set loading back to false', () => {
    useChatStore.getState().setLoading(true);
    useChatStore.getState().setLoading(false);
    expect(useChatStore.getState().loading).toBe(false);
  });
});

describe('ChatStore – setError', () => {
  it('should set an error message', () => {
    useChatStore.getState().setError('Agent timeout');
    expect(useChatStore.getState().error).toBe('Agent timeout');
  });

  it('should clear error when set to null', () => {
    useChatStore.getState().setError('error');
    useChatStore.getState().setError(null);
    expect(useChatStore.getState().error).toBeNull();
  });
});

describe('ChatStore – clearChat', () => {
  it('should clear all messages', () => {
    useChatStore.getState().addMessage({ role: 'user', content: 'Test' });
    useChatStore.getState().clearChat();
    expect(useChatStore.getState().messages).toHaveLength(0);
  });

  it('should reset sessionId', () => {
    useChatStore.getState().setSessionId('sess-xyz');
    useChatStore.getState().clearChat();
    expect(useChatStore.getState().sessionId).toBeNull();
  });

  it('should reset leadGrade and confidence', () => {
    useChatStore.getState().setMetadata('A', 0.9);
    useChatStore.getState().clearChat();
    expect(useChatStore.getState().leadGrade).toBeNull();
    expect(useChatStore.getState().confidence).toBeNull();
  });

  it('should reset error', () => {
    useChatStore.getState().setError('something broke');
    useChatStore.getState().clearChat();
    expect(useChatStore.getState().error).toBeNull();
  });
});
