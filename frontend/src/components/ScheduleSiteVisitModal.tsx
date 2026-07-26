import { useState } from 'react';
import { scheduleSiteVisit } from '../api/crmApi';

interface Props {
  leadId: string;
  leadName?: string;
  propertyTitle?: string;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function ScheduleSiteVisitModal({
  leadId,
  leadName,
  propertyTitle,
  onClose,
  onSuccess,
}: Props) {
  const [visitDatetime, setVisitDatetime] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!visitDatetime) {
      setError('Please select a visit date and time.');
      return;
    }

    const selectedDate = new Date(visitDatetime);
    if (selectedDate <= new Date()) {
      setError('Visit date and time must be in the future.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await scheduleSiteVisit(leadId, selectedDate.toISOString());
      if (onSuccess) onSuccess();
      onClose();
    } catch (err: unknown) {
      console.error('Schedule site visit error:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error?.response?.data?.detail || 'Failed to schedule site visit.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 text-slate-100"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="font-bold text-base text-white flex items-center gap-2">
              📅 Schedule Property Site Visit
            </h3>
            <p className="text-[11px] text-slate-400">
              Booking for {leadName || 'Prospect'}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="rounded-full p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {propertyTitle && (
            <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-0.5">
                Target Property
              </span>
              <p className="font-semibold text-white">{propertyTitle}</p>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-300">
              Select Future Date & Time
            </label>
            <input
              type="datetime-local"
              required
              value={visitDatetime}
              onChange={(e) => setVisitDatetime(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-slate-100 focus:border-blue-500 focus:outline-none shadow-inner"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-300">
              Notes for Agent / Prospect (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Prospect requested developer representative presence on site..."
              className="w-full h-24 rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none shadow-inner"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-xs font-semibold text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-blue-600 hover:bg-blue-500 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              {loading ? (
                <>
                  <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Scheduling…
                </>
              ) : (
                'Confirm Site Visit ➔'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
