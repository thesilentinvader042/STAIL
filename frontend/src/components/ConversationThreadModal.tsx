import { useEffect, useState } from 'react';
import { fetchSessionHistory } from '../api/agentApi';
import type { AgentSession, Message } from '../types';

interface Props {
  session: AgentSession;
  onClose: () => void;
  onResume: (session: AgentSession) => void;
}

export default function ConversationThreadModal({ session, onClose, onResume }: Props) {
  const [turns, setTurns] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');

    fetchSessionHistory(session.id)
      .then((res) => {
        const historyTurns = res.data?.turns ?? [];
        if (historyTurns.length > 0) {
          setTurns(
            historyTurns.map((t, idx) => ({
              id: `turn-${idx}`,
              role: t.role,
              content: t.content,
            }))
          );
        } else {
          // Fallback: show the stored input/output from session row
          const fallback: Message[] = [];
          if (session.input_text) fallback.push({ role: 'user', content: session.input_text });
          if (session.output_text) fallback.push({ role: 'assistant', content: session.output_text });
          setTurns(fallback);
        }
      })
      .catch(() => {
        setError('Could not retrieve full transcript from memory manager. Showing stored snapshot.');
        const fallback: Message[] = [];
        if (session.input_text) fallback.push({ role: 'user', content: session.input_text });
        if (session.output_text) fallback.push({ role: 'assistant', content: session.output_text });
        setTurns(fallback);
      })
      .finally(() => setLoading(false));
  }, [session.id]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="relative w-full max-w-3xl max-h-[85vh] rounded-3xl border border-slate-800 bg-slate-900 shadow-2xl flex flex-col overflow-hidden">

        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60 shrink-0">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white">
                {session.agent_name || session.agent_id}
              </span>
              <span className="rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] px-2 py-0.5 font-semibold font-mono">
                {session.id.substring(0, 8)}…
              </span>
              <span
                className={`rounded-full text-[10px] px-2 py-0.5 font-semibold border ${
                  session.session_status === 'active'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-slate-700/50 text-slate-300 border-slate-700'
                }`}
              >
                {session.session_status}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              {new Date(session.created_at).toLocaleString('en-IN', {
                day: 'numeric', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
              })}
              {session.latency_ms && (
                <span className="ml-3 text-slate-500">· {session.latency_ms}ms</span>
              )}
              {session.confidence_score != null && (
                <span className="ml-3 text-emerald-400">
                  · {(session.confidence_score * 100).toFixed(0)}% confidence
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="rounded-full p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Turn History */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4 min-h-0">
          {error && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-[11px] text-amber-400">
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div className="flex h-48 items-center justify-center gap-3 text-xs text-slate-400">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              Fetching transcript from memory manager…
            </div>
          ) : turns.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-xs text-slate-500 text-center">
              No turn records found for this session.
            </div>
          ) : (
            turns.map((msg, i) => (
              <div
                key={msg.id ?? i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[82%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none shadow-md'
                      : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none'
                  }`}
                >
                  <div className="font-semibold text-[10px] opacity-60 mb-1 uppercase tracking-wide">
                    {msg.role === 'user' ? '👤 You' : '🤖 AI Agent'}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-4 bg-slate-950/60 shrink-0">
          <p className="text-[11px] text-slate-500">
            {turns.length} turn{turns.length !== 1 ? 's' : ''} in this session
          </p>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs font-semibold text-slate-300 transition-colors"
            >
              Close
            </button>
            <button
              onClick={() => { onClose(); onResume(session); }}
              className="rounded-xl bg-blue-600 hover:bg-blue-500 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-blue-500/20 transition-colors"
            >
              Resume Conversation →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
