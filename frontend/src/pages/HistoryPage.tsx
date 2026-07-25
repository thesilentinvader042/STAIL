import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatStore } from '../store/chatStore';
import { fetchSessions, fetchSessionHistory } from '../api/agentApi';
import type { AgentSession, Message } from '../types';
import ConversationThreadModal from '../components/ConversationThreadModal';

export default function HistoryPage() {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSession, setSelectedSession] = useState<AgentSession | null>(null);
  const [resumingId, setResumingId] = useState<string | null>(null);

  const loadSessionHistory = useChatStore((s) => s.loadSessionHistory);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    setError('');
    fetchSessions()
      .then((res) => {
        setSessions(res.data || []);
      })
      .catch((err) => {
        console.error('Fetch sessions error:', err);
        setError('Failed to fetch chat session history.');
      })
      .finally(() => setLoading(false));
  }, []);

  const handleViewTranscript = (session: AgentSession) => {
    setSelectedSession(session);
  };

  const handleResumeSession = async (session: AgentSession) => {
    setResumingId(session.id);
    try {
      const res = await fetchSessionHistory(session.id);
      const historyTurns = res.data?.turns || [];

      const messages: Message[] = historyTurns.length > 0
        ? historyTurns.map((t, idx) => ({
            id: `turn-${idx}`,
            role: t.role,
            content: t.content,
          }))
        : [
            ...(session.input_text ? [{ role: 'user' as const, content: session.input_text }] : []),
            ...(session.output_text ? [{ role: 'assistant' as const, content: session.output_text }] : []),
          ];

      const resumedDate = new Date(session.created_at).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });

      loadSessionHistory(session.id, messages, resumedDate);
      navigate('/search');
    } catch (err) {
      console.error('Error resuming session:', err);
      // Graceful fallback: navigate anyway with sessionId
      loadSessionHistory(session.id, [], new Date(session.created_at).toLocaleDateString());
      navigate('/search');
    } finally {
      setResumingId(null);
    }
  };

  return (
    <div className="space-y-6 text-slate-100 max-w-6xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold tracking-tight text-white">Chat Session History</h2>
        <p className="text-xs text-slate-400 mt-1">
          Review past AI agent conversations, view full transcripts, and resume any prior session with full context restored.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-400">
          ⚠️ {error}
        </div>
      )}

      {loading ? (
        <div className="flex h-64 w-full items-center justify-center text-slate-400 text-xs">
          <div className="flex items-center gap-3">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            Loading conversation history...
          </div>
        </div>
      ) : sessions.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center space-y-3">
          <div className="text-4xl">💬</div>
          <h3 className="font-bold text-lg text-white">No prior sessions found</h3>
          <p className="text-xs text-slate-400">
            Start a new conversation with the AI Property Discovery Agent.
          </p>
          <button
            onClick={() => navigate('/search')}
            className="mt-2 inline-block rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 transition-colors"
          >
            Start New AI Search
          </button>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="p-4">Agent</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Input Preview</th>
                  <th className="p-4">Confidence</th>
                  <th className="p-4">Date</th>
                  <th className="p-4">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {sessions.map((session) => (
                  <tr key={session.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 font-bold text-white">
                      {session.agent_name || session.agent_id}
                    </td>
                    <td className="p-4">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                          session.session_status === 'active'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : session.session_status === 'escalated'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            : 'bg-slate-700/50 text-slate-300 border-slate-700'
                        }`}
                      >
                        {session.session_status}
                      </span>
                    </td>
                    <td className="p-4 max-w-xs truncate text-slate-400">
                      {session.input_text || '—'}
                    </td>
                    <td className="p-4">
                      {session.confidence_score != null ? (
                        <span className="font-mono text-emerald-400">
                          {(session.confidence_score * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="p-4 text-slate-400">
                      {new Date(session.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="p-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleViewTranscript(session)}
                          className="rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 font-semibold text-slate-300 transition-colors"
                        >
                          View Transcript
                        </button>
                        <button
                          onClick={() => handleResumeSession(session)}
                          disabled={resumingId === session.id}
                          className="rounded-lg bg-blue-600/80 hover:bg-blue-600 px-3 py-1.5 font-semibold text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
                        >
                          {resumingId === session.id ? (
                            <>
                              <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                              Loading…
                            </>
                          ) : (
                            'Resume →'
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Conversation Thread Modal */}
      {selectedSession && (
        <ConversationThreadModal
          session={selectedSession}
          onClose={() => setSelectedSession(null)}
          onResume={(session) => handleResumeSession(session)}
        />
      )}
    </div>
  );
}
