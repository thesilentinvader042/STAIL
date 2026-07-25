import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchLeadById, updateLead, qualifyLead } from '../api/crmApi';
import { fetchSessions, fetchSessionHistory } from '../api/agentApi';
import type { AgentSession, Lead, Message } from '../types';
import FollowUpPanel from '../components/FollowUpPanel';
import ScheduleSiteVisitModal from '../components/ScheduleSiteVisitModal';

// Valid status transitions per leads.py FSM
const VALID_TRANSITIONS: Record<string, string[]> = {
  NEW: ['CONTACTED', 'QUALIFIED', 'CLOSED_LOST'],
  CONTACTED: ['QUALIFIED', 'CLOSED_LOST', 'DORMANT'],
  QUALIFIED: ['SITE_VISIT_SCHEDULED', 'OFFER_MADE', 'CLOSED_LOST'],
  SITE_VISIT_SCHEDULED: ['SITE_VISIT_DONE', 'QUALIFIED', 'CLOSED_LOST'],
  SITE_VISIT_DONE: ['OFFER_MADE', 'CLOSED_LOST', 'DORMANT'],
  OFFER_MADE: ['NEGOTIATING', 'CLOSED_WON', 'CLOSED_LOST'],
  NEGOTIATING: ['AGREEMENT_SIGNED', 'CLOSED_LOST'],
  AGREEMENT_SIGNED: ['CLOSED_WON'],
  CLOSED_WON: [],
  CLOSED_LOST: ['NEW'],
  DORMANT: ['NEW', 'CONTACTED'],
};

export default function LeadDetailPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const navigate = useNavigate();

  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Status transition state
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // Notes state
  const [notesInput, setNotesInput] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const [notesSuccess, setNotesSuccess] = useState(false);

  // Re-scoring state
  const [qualifying, setQualifying] = useState(false);

  // Modal state
  const [showVisitModal, setShowVisitModal] = useState(false);

  // Chat Transcript state
  const [transcriptTurns, setTranscriptTurns] = useState<Message[]>([]);
  const [loadingTranscript, setLoadingTranscript] = useState(false);

  const loadLeadDetails = async () => {
    if (!leadId) return;
    setLoading(true);
    setError('');

    try {
      const res = await fetchLeadById(leadId);
      const data = res.data;
      setLead(data);
      setNotesInput(data.notes || '');

      // Attempt to load conversation transcript
      loadTranscriptForLead(data);
    } catch (err: any) {
      console.error('Fetch lead detail error:', err);
      setError(err.response?.data?.detail || 'Failed to fetch lead profile.');
    } finally {
      setLoading(false);
    }
  };

  const loadTranscriptForLead = async (leadData: Lead) => {
    setLoadingTranscript(true);
    try {
      // Find session matching lead or fetch latest active session
      const sessionsRes = await fetchSessions();
      const allSessions: AgentSession[] = sessionsRes.data || [];

      if (allSessions.length > 0) {
        // Pick top session
        const topSession = allSessions[0];
        const historyRes = await fetchSessionHistory(topSession.id);
        const turns = historyRes.data?.turns || [];

        if (turns.length > 0) {
          setTranscriptTurns(
            turns.map((t, idx) => ({
              id: `turn-${idx}`,
              role: t.role,
              content: t.content,
            }))
          );
        } else {
          // Fallback to session input/output
          const fallback: Message[] = [];
          if (topSession.input_text) fallback.push({ role: 'user', content: topSession.input_text });
          if (topSession.output_text) fallback.push({ role: 'assistant', content: topSession.output_text });
          setTranscriptTurns(fallback);
        }
      }
    } catch (err) {
      console.warn('Could not load transcript for lead:', err);
    } finally {
      setLoadingTranscript(false);
    }
  };

  useEffect(() => {
    loadLeadDetails();
  }, [leadId]);

  const handleStatusChange = async (newStatus: string) => {
    if (!leadId || !lead) return;
    setUpdatingStatus(true);
    try {
      const res = await updateLead(leadId, { status: newStatus });
      setLead(res.data);
    } catch (err: any) {
      console.error('Status change error:', err);
      alert(err.response?.data?.detail || 'Failed to update lead status.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleSaveNotes = async () => {
    if (!leadId) return;
    setSavingNotes(true);
    setNotesSuccess(false);
    try {
      const res = await updateLead(leadId, { notes: notesInput });
      setLead(res.data);
      setNotesSuccess(true);
      setTimeout(() => setNotesSuccess(false), 3000);
    } catch (err: any) {
      console.error('Save notes error:', err);
      alert(err.response?.data?.detail || 'Failed to save notes.');
    } finally {
      setSavingNotes(false);
    }
  };

  const handleReQualify = async () => {
    if (!leadId) return;
    setQualifying(true);
    try {
      const res = await qualifyLead(leadId);
      setLead(res.data);
    } catch (err: any) {
      console.error('Re-scoring error:', err);
      alert(err.response?.data?.detail || 'Failed to re-score lead.');
    } finally {
      setQualifying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 w-full items-center justify-center text-xs text-slate-400">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          Loading lead profile...
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="max-w-4xl mx-auto space-y-4 text-slate-100">
        <button
          onClick={() => navigate('/crm/leads')}
          className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
        >
          ← Back to CRM Leads
        </button>
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-xs text-red-400 space-y-2">
          <p className="font-bold text-sm">Error Loading Lead</p>
          <p>{error || 'Lead profile not found.'}</p>
        </div>
      </div>
    );
  }

  const allowedTransitions = VALID_TRANSITIONS[lead.status] || [];

  return (
    <div className="space-y-6 text-slate-100 max-w-6xl mx-auto pb-16">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="space-y-1">
          <button
            onClick={() => navigate('/crm/leads')}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
          >
            ← Back to CRM Leads
          </button>
          <div className="flex items-center gap-3 pt-1">
            <h2 className="text-2xl font-bold tracking-tight text-white">
              {lead.contact_name || 'Anonymous Prospect'}
            </h2>
            <span
              className={`rounded-full px-3 py-0.5 text-xs font-bold border ${
                lead.tier === 'HOT'
                  ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                  : lead.tier === 'WARM'
                  ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                  : 'bg-blue-500/15 text-blue-400 border-blue-500/30'
              }`}
            >
              {lead.tier} Lead
            </span>
          </div>
          <p className="text-xs text-slate-400">
            ID: <span className="font-mono text-slate-300">{lead.id}</span> · Created on{' '}
            {new Date(lead.created_at).toLocaleDateString('en-IN', {
              day: 'numeric',
              month: 'short',
              year: 'numeric',
            })}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowVisitModal(true)}
            className="rounded-xl border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 px-3.5 py-2 text-xs font-semibold text-amber-300 transition-colors flex items-center gap-1.5"
          >
            📅 Schedule Site Visit
          </button>

          <button
            onClick={handleReQualify}
            disabled={qualifying}
            className="rounded-xl border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 px-3.5 py-2 text-xs font-semibold text-purple-300 transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            {qualifying ? (
              <>
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-purple-400 border-t-transparent" />
                Scoring…
              </>
            ) : (
              '⚡ Re-Run AI Scoring'
            )}
          </button>

          <button
            onClick={() => navigate('/search')}
            className="rounded-xl bg-blue-600 hover:bg-blue-500 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-blue-500/20 transition-colors"
          >
            Open AI Search ➔
          </button>
        </div>
      </div>

      {/* Grid Overview Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column (2 cols): Contact, Intent Meter, Preferences, Transcript */}
        <div className="lg:col-span-2 space-y-6">

          {/* Key Prospect Metrics Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">
              Prospect Overview & Intent Meter
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <p className="text-[11px] text-slate-400">Phone</p>
                <p className="font-medium text-slate-200 mt-0.5">
                  {lead.contact_phone || '—'}
                </p>
              </div>

              <div>
                <p className="text-[11px] text-slate-400">Email</p>
                <p className="font-medium text-slate-200 mt-0.5 truncate">
                  {lead.contact_email || '—'}
                </p>
              </div>

              <div>
                <p className="text-[11px] text-slate-400">Source / Channel</p>
                <p className="font-medium text-slate-200 mt-0.5 uppercase">
                  {lead.source} · {lead.channel}
                </p>
              </div>
            </div>

            {/* Intent Score Bar */}
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300">AI Intent & Qualification Score</span>
                <span className="font-mono font-bold text-emerald-400 text-sm">
                  {lead.intent_score}/100
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    lead.intent_score >= 70
                      ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                      : lead.intent_score >= 40
                      ? 'bg-gradient-to-r from-blue-500 to-amber-400'
                      : 'bg-blue-600'
                  }`}
                  style={{ width: `${Math.min(lead.intent_score, 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500">
                Calculated using AGT-02 intent model evaluating budget precision, timelines, and loan status.
              </p>
            </div>
          </div>

          {/* Follow-Up Task Management Panel (Component 3) */}
          <FollowUpPanel leadId={lead.id} leadName={lead.contact_name || undefined} />

          {/* Extracted Buyer Preferences Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">
              Extracted Buyer Requirements
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="rounded-xl bg-slate-950/60 p-3 border border-slate-800">
                <p className="text-[11px] text-slate-400">Budget Range</p>
                <p className="font-bold text-white mt-1">
                  {lead.budget_min || lead.budget_max
                    ? `₹${((lead.budget_min || 0) / 100000).toFixed(0)}L – ₹${(
                        (lead.budget_max || 0) / 10000000
                      ).toFixed(2)} Cr`
                    : 'Not specified'}
                </p>
              </div>

              <div className="rounded-xl bg-slate-950/60 p-3 border border-slate-800">
                <p className="text-[11px] text-slate-400">Preferred BHK</p>
                <p className="font-bold text-white mt-1">
                  {lead.preferred_bhk ? `${lead.preferred_bhk} BHK` : 'Flexible'}
                </p>
              </div>

              <div className="rounded-xl bg-slate-950/60 p-3 border border-slate-800">
                <p className="text-[11px] text-slate-400">Possession Timeline</p>
                <p className="font-bold text-white mt-1">
                  {lead.possession_timeline_months
                    ? `Within ${lead.possession_timeline_months} months`
                    : 'Immediate'}
                </p>
              </div>

              <div className="rounded-xl bg-slate-950/60 p-3 border border-slate-800 col-span-2 sm:col-span-1">
                <p className="text-[11px] text-slate-400">Home Loan Required</p>
                <p className="font-bold text-white mt-1">
                  {lead.is_loan_required ? 'Yes (Pre-Approved)' : 'No (Self-Funded)'}
                </p>
              </div>

              <div className="rounded-xl bg-slate-950/60 p-3 border border-slate-800 col-span-2">
                <p className="text-[11px] text-slate-400">Preferred Localities</p>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {lead.preferred_localities && lead.preferred_localities.length > 0 ? (
                    lead.preferred_localities.map((loc, idx) => (
                      <span
                        key={idx}
                        className="rounded-md bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 text-[10px] font-semibold text-blue-300"
                      >
                        📍 {loc}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 text-[11px]">No specific localities saved</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* AI Conversation History Transcript */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                AI Conversation Transcript
              </h3>
              <span className="text-xs text-slate-400">
                {transcriptTurns.length} turn{transcriptTurns.length !== 1 ? 's' : ''} recorded
              </span>
            </div>

            {loadingTranscript ? (
              <div className="flex h-32 items-center justify-center text-xs text-slate-500">
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                  Fetching memory transcript…
                </div>
              </div>
            ) : transcriptTurns.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-xs text-slate-500 text-center">
                No chat history turns recorded yet for this prospect.
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {transcriptTurns.map((turn, idx) => (
                  <div
                    key={turn.id ?? idx}
                    className={`flex ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                        turn.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-slate-950 text-slate-200 border border-slate-800 rounded-bl-none'
                      }`}
                    >
                      <div className="font-semibold text-[10px] opacity-60 mb-1 uppercase tracking-wide">
                        {turn.role === 'user' ? '👤 Prospect' : '🤖 AI Agent'}
                      </div>
                      <div className="whitespace-pre-wrap">{turn.content}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Right Column (1 col): FSM Status Change, Broker Notes, Timestamps */}
        <div className="space-y-6">

          {/* FSM Status Transition Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">
              Pipeline Stage & Status
            </h3>

            <div className="space-y-2">
              <label className="text-[11px] font-semibold text-slate-400">Current Stage</label>
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800 flex items-center justify-between">
                <span className="font-mono font-bold text-blue-400 text-xs">{lead.status}</span>
                <span className="text-[10px] text-slate-500">FSM Active</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-semibold text-slate-400">
                Advance Pipeline Stage
              </label>
              {allowedTransitions.length === 0 ? (
                <p className="text-xs text-slate-500 italic">
                  Terminal stage reached ({lead.status}). No further status transitions allowed.
                </p>
              ) : (
                <div className="space-y-2">
                  <select
                    value=""
                    disabled={updatingStatus}
                    onChange={(e) => e.target.value && handleStatusChange(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="" disabled>
                      Select next stage…
                    </option>
                    {allowedTransitions.map((t) => (
                      <option key={t} value={t}>
                        ➔ Move to {t}
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-slate-500">
                    Transitions are enforced according to the backend Finite State Machine.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Broker Notes Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Broker Notes
              </h3>
              {notesSuccess && (
                <span className="text-[10px] font-bold text-emerald-400 animate-fade-in">
                  ✓ Notes saved
                </span>
              )}
            </div>

            <textarea
              value={notesInput}
              onChange={(e) => setNotesInput(e.target.value)}
              placeholder="Record offline conversation notes, site visit outcomes, or special requests..."
              className="w-full h-36 rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none shadow-inner"
            />

            <button
              onClick={handleSaveNotes}
              disabled={savingNotes}
              className="w-full rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 px-4 py-2.5 text-xs font-bold text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {savingNotes ? (
                <>
                  <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Saving Notes…
                </>
              ) : (
                '💾 Save Broker Notes'
              )}
            </button>
          </div>

          {/* Metadata Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2 text-[11px] text-slate-400">
            <div className="flex justify-between">
              <span>Assigned Broker</span>
              <span className="font-mono text-slate-300">
                {lead.broker_id ? lead.broker_id.substring(0, 8) + '…' : 'Unassigned'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Last Contacted</span>
              <span className="text-slate-300">
                {lead.last_contacted_at
                  ? new Date(lead.last_contacted_at).toLocaleDateString()
                  : '—'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Site Visit Scheduled</span>
              <span className="text-amber-400 font-semibold">
                {lead.site_visit_scheduled_at
                  ? new Date(lead.site_visit_scheduled_at).toLocaleString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : 'Not scheduled'}
              </span>
            </div>
          </div>

        </div>

      </div>

      {/* Schedule Site Visit Modal (Component 4) */}
      {showVisitModal && (
        <ScheduleSiteVisitModal
          leadId={lead.id}
          leadName={lead.contact_name || undefined}
          onClose={() => setShowVisitModal(false)}
          onSuccess={() => loadLeadDetails()}
        />
      )}
    </div>
  );
}
