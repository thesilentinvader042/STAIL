import { useEffect, useRef, useState } from 'react';
import { useChatStore } from '../store/chatStore';
import { orchestrateChat } from '../api/agentApi';
import ChatMessage from '../components/ChatMessage';
import PropertyResultsPanel from '../components/PropertyResultsPanel';

const SUGGESTIONS = [
  '3BHK apartment in Mumbai under 2.5 Cr',
  'Luxury 4BHK villa in Bengaluru with pool',
  '2BHK near Hinjewadi Pune under 80 Lakhs',
  'Commercial office space in Gurgaon',
];

export default function SearchPage() {
  const {
    messages,
    addMessage,
    sessionId,
    setSessionId,
    loading,
    setLoading,
    setError,
    setMetadata,
    isResumedSession,
    resumedDate,
    clearChat,
  } = useChatStore();

  const [input, setInput] = useState('');
  const [showResumeBanner, setShowResumeBanner] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Re-show banner whenever the component mounts with a resumed session
  useEffect(() => {
    if (isResumedSession) setShowResumeBanner(true);
  }, [isResumedSession]);

  const handleSend = async (customText?: string) => {
    const textToSend = customText || input;
    if (!textToSend.trim() || loading) return;

    addMessage({ role: 'user', content: textToSend.trim() });
    if (!customText) setInput('');

    setLoading(true);
    setError(null);

    try {
      const { data } = await orchestrateChat(textToSend.trim(), sessionId);
      setSessionId(data.session_id);
      setMetadata(data.lead_grade, data.confidence);
      addMessage({
        role: 'assistant',
        content: data.response,
        properties: data.properties,
        confidence: data.confidence,
        leadGrade: data.lead_grade,
      });
    } catch (err: unknown) {
      console.error('Orchestration error:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      const errMsg =
        error?.response?.data?.detail || 'Failed to reach AI agents. Please check backend service.';
      setError(errMsg);
      addMessage({ role: 'assistant', content: `⚠️ Error: ${errMsg}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-4xl mx-auto text-slate-100">

      {/* ── Session Resumption Banner (Component 4) ── */}
      {isResumedSession && showResumeBanner && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 mb-3 text-xs text-amber-300 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-base">🔁</span>
            <span>
              Continuing conversation from{' '}
              <strong className="text-amber-200">{resumedDate}</strong>
              {' '}— your prior context and memory preferences have been restored.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => clearChat()}
              className="rounded-lg border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 px-2.5 py-1 font-semibold transition-colors"
            >
              New Search
            </button>
            <button
              onClick={() => setShowResumeBanner(false)}
              aria-label="Dismiss banner"
              className="rounded-full p-1 hover:bg-amber-500/20 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 shrink-0">
        <div>
          <h2 className="font-bold text-lg text-white flex items-center gap-2">
            🤖 AI Property Discovery Agent
          </h2>
          <p className="text-xs text-slate-400">
            Powered by 5-Agent Sequential Pipeline (AGT-01 to AGT-06)
          </p>
        </div>
        <div className="flex items-center gap-2">
          {sessionId && (
            <span className="rounded-md bg-blue-500/10 px-2.5 py-1 text-[11px] font-mono text-blue-400 border border-blue-500/20">
              Session: {sessionId.substring(0, 8)}...
            </span>
          )}
          {messages.length > 0 && (
            <button
              onClick={() => clearChat()}
              className="rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-2.5 py-1 text-[11px] font-semibold text-slate-400 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6 py-12">
            <div className="h-16 w-16 rounded-3xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-3xl shadow-xl shadow-blue-500/20">
              💬
            </div>
            <div className="space-y-2 max-w-md">
              <h3 className="font-bold text-xl text-white">What property are you looking for?</h3>
              <p className="text-xs text-slate-400">
                Ask in plain English or Hinglish. Our AI pipeline will extract preferences, search
                database listings, and rank top recommendations for you.
              </p>
            </div>
            <div className="w-full max-w-md space-y-2 pt-2">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-left">
                Suggested Searches:
              </p>
              <div className="flex flex-col gap-2">
                {SUGGESTIONS.map((sug, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(sug)}
                    className="text-left rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 p-3 text-xs text-slate-300 transition-colors hover:border-blue-500/40"
                  >
                    💡 &ldquo;{sug}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={m.id || i} className="w-full space-y-2">
              <ChatMessage message={m} />
              {m.properties && m.properties.length > 0 && (
                <PropertyResultsPanel properties={m.properties} />
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800 w-max text-xs text-slate-400">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            Agents processing query through 5-stage pipeline…
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Chat Input ── */}
      <div className="mt-3 pt-3 border-t border-slate-800 shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Type your property request (e.g. 3BHK in Bandra West under 2.5 Crore)..."
            className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-xs md:text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none shadow-inner"
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 px-6 py-3 text-xs md:text-sm font-bold text-white shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            Send ➔
          </button>
        </div>
      </div>
    </div>
  );
}