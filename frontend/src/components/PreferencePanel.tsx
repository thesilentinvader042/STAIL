import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { fetchUserPreferences, updateUserPreferences } from '../api/preferenceApi';
import type { UserPreferences } from '../types';

export default function PreferencePanel() {
  const user = useAuthStore((s) => s.user);
  const [preferences, setPreferences] = useState<UserPreferences>({
    property_type: [],
    budget_min: null,
    budget_max: null,
    preferred_locations: [],
    must_haves: [],
    deal_breakers: [],
  });
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Form states for array/string inputs
  const [locationsInput, setLocationsInput] = useState('');
  const [mustHavesInput, setMustHavesInput] = useState('');
  const [dealBreakersInput, setDealBreakersInput] = useState('');

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    fetchUserPreferences(user.id)
      .then((res) => {
        const data = res.data || {};
        setPreferences(data);
        setLocationsInput((data.preferred_locations || []).join(', '));
        setMustHavesInput((data.must_haves || []).join(', '));
        setDealBreakersInput((data.deal_breakers || []).join(', '));
      })
      .catch((err) => {
        console.error('Failed to load preferences:', err);
      })
      .finally(() => setLoading(false));
  }, [user?.id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.id) return;

    setSaving(true);
    setMessage(null);

    const payload: UserPreferences = {
      ...preferences,
      preferred_locations: locationsInput.split(',').map((s) => s.trim()).filter(Boolean),
      must_haves: mustHavesInput.split(',').map((s) => s.trim()).filter(Boolean),
      deal_breakers: dealBreakersInput.split(',').map((s) => s.trim()).filter(Boolean),
    };

    try {
      const res = await updateUserPreferences(user.id, payload);
      setPreferences(res.data || payload);
      setIsEditing(false);
      setMessage('Preferences saved successfully!');
      setTimeout(() => setMessage(null), 3000);
    } catch (err: unknown) {
      console.error('Error saving preferences:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(error?.response?.data?.detail || 'Failed to save preferences. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const togglePropertyType = (type: string) => {
    const current = preferences.property_type || [];
    const updated = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    setPreferences({ ...preferences, property_type: updated });
  };

  const formatPriceInr = (val?: number | null) => {
    if (!val) return 'Not set';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-slate-400 text-xs flex justify-center items-center h-48">
        Loading preferences memory...
      </div>
    );
  }

  const PROPERTY_TYPES = ['Apartment', 'Villa', 'Penthouse', 'Plot', 'Studio', 'Duplex'];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🧠</span> Autonomous Preference Memory
          </h3>
          <p className="text-xs text-slate-400">
            Learned and stated criteria used by AI agents for personalized property matching.
          </p>
        </div>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs font-semibold text-white transition-colors"
        >
          {isEditing ? 'Cancel' : 'Edit Preferences'}
        </button>
      </div>

      {message && (
        <div
          className={`rounded-xl p-3 text-xs font-medium border ${
            message.includes('success')
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
              : 'border-red-500/30 bg-red-500/10 text-red-400'
          }`}
        >
          {message}
        </div>
      )}

      {isEditing ? (
        <form onSubmit={handleSave} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Min Budget (₹)</label>
              <input
                type="number"
                value={preferences.budget_min || ''}
                onChange={(e) =>
                  setPreferences({
                    ...preferences,
                    budget_min: e.target.value ? Number(e.target.value) : null,
                  })
                }
                placeholder="e.g. 5000000"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Max Budget (₹)</label>
              <input
                type="number"
                value={preferences.budget_max || ''}
                onChange={(e) =>
                  setPreferences({
                    ...preferences,
                    budget_max: e.target.value ? Number(e.target.value) : null,
                  })
                }
                placeholder="e.g. 25000000"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-2">Property Types</label>
            <div className="flex flex-wrap gap-2">
              {PROPERTY_TYPES.map((type) => {
                const selected = (preferences.property_type || []).includes(type);
                return (
                  <button
                    type="button"
                    key={type}
                    onClick={() => togglePropertyType(type)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold border transition-all ${
                      selected
                        ? 'bg-blue-600/30 text-blue-400 border-blue-500/50'
                        : 'bg-slate-800/60 text-slate-400 border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    {type} {selected ? '✓' : ''}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Preferred Locations (comma-separated)
            </label>
            <input
              type="text"
              value={locationsInput}
              onChange={(e) => setLocationsInput(e.target.value)}
              placeholder="e.g. Bandra West, Worli, Powai"
              className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Must-Haves (comma-separated)
              </label>
              <input
                type="text"
                value={mustHavesInput}
                onChange={(e) => setMustHavesInput(e.target.value)}
                placeholder="e.g. Sea View, Gated Community"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">
                Deal-Breakers (comma-separated)
              </label>
              <input
                type="text"
                value={dealBreakersInput}
                onChange={(e) => setDealBreakersInput(e.target.value)}
                placeholder="e.g. High Maintenance, Ground Floor"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 p-2.5 text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="rounded-xl bg-slate-800 hover:bg-slate-700 px-4 py-2 text-xs font-semibold text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-xl bg-blue-600 hover:bg-blue-500 px-4 py-2 text-xs font-semibold text-white shadow-lg transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
          </div>
        </form>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-1">
            <span className="text-slate-400 font-medium">Budget Range</span>
            <div className="text-sm font-bold text-emerald-400">
              {formatPriceInr(preferences.budget_min)} – {formatPriceInr(preferences.budget_max)}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-1">
            <span className="text-slate-400 font-medium">Property Types</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {(preferences.property_type || []).length > 0 ? (
                preferences.property_type?.map((t) => (
                  <span
                    key={t}
                    className="rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 text-[10px]"
                  >
                    {t}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">None specified</span>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-1">
            <span className="text-slate-400 font-medium">Preferred Locations</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {(preferences.preferred_locations || []).length > 0 ? (
                preferences.preferred_locations?.map((loc) => (
                  <span
                    key={loc}
                    className="rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 text-[10px]"
                  >
                    📍 {loc}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">None specified</span>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-1">
            <span className="text-slate-400 font-medium">Must-Haves & Limits</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {(preferences.must_haves || []).map((m) => (
                <span
                  key={m}
                  className="rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 text-[10px]"
                >
                  ✓ {m}
                </span>
              ))}
              {(preferences.deal_breakers || []).map((d) => (
                <span
                  key={d}
                  className="rounded-md bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 text-[10px]"
                >
                  ✕ {d}
                </span>
              ))}
              {(!preferences.must_haves?.length && !preferences.deal_breakers?.length) && (
                <span className="text-slate-500 italic">None specified</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
