import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchLeads, fetchLeadSummaryStats } from '../api/crmApi';
import type { Lead, LeadSummaryStats } from '../types';

export default function CrmDashboardPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<LeadSummaryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [selectedTier, setSelectedTier] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const navigate = useNavigate();

  const loadData = () => {
    setLoading(true);
    setError('');

    const params: Record<string, any> = { page, page_size: 20 };
    if (selectedTier !== 'ALL') params.tier = selectedTier;
    if (selectedStatus !== 'ALL') params.status = selectedStatus;

    Promise.all([fetchLeads(params), fetchLeadSummaryStats()])
      .then(([leadsRes, statsRes]) => {
        setLeads(leadsRes.data || []);
        setStats(statsRes.data || null);
      })
      .catch((err) => {
        console.error('Fetch leads CRM error:', err);
        setError('Failed to load CRM leads. Please ensure backend services are running.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [selectedTier, selectedStatus, page]);

  const filteredLeads = leads.filter((l) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      (l.contact_name && l.contact_name.toLowerCase().includes(query)) ||
      (l.contact_phone && l.contact_phone.includes(query)) ||
      (l.contact_email && l.contact_email.toLowerCase().includes(query)) ||
      (l.source && l.source.toLowerCase().includes(query))
    );
  });

  const getTierBadgeClass = (tier: string) => {
    switch (tier?.toUpperCase()) {
      case 'HOT':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'WARM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'COLD':
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
      default:
        return 'bg-slate-700/50 text-slate-300 border-slate-700';
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'NEW':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'QUALIFIED':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'SITE_VISIT_SCHEDULED':
      case 'SITE_VISIT_DONE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'OFFER_MADE':
      case 'NEGOTIATING':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'CLOSED_WON':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'CLOSED_LOST':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6 text-slate-100 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-white">CRM Lead Management</h2>
            <span className="rounded-md bg-blue-500/10 px-2 py-0.5 text-[11px] font-bold text-blue-400 border border-blue-500/20">
              Admin & Broker Portal
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time pipeline metrics, intent scores, AI qualification tiers, and lead interaction records.
          </p>
        </div>

        <button
          onClick={loadData}
          className="rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 transition-colors flex items-center gap-2 w-max"
        >
          <span>🔄</span> Refresh Data
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-400 flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={loadData} className="underline font-bold">Retry</button>
        </div>
      )}

      {/* Summary KPI Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-lg">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Leads</p>
            <p className="text-2xl font-black text-white mt-1">{stats.total}</p>
            <p className="text-[10px] text-slate-500 mt-1">All captured enquiries</p>
          </div>

          <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">Hot Leads</p>
              <span className="text-xs">🔥</span>
            </div>
            <p className="text-2xl font-black text-rose-300 mt-1">{stats.by_tier.hot}</p>
            <p className="text-[10px] text-rose-400/70 mt-1">Score ≥ 70</p>
          </div>

          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Warm Leads</p>
              <span className="text-xs">⚡</span>
            </div>
            <p className="text-2xl font-black text-amber-300 mt-1">{stats.by_tier.warm}</p>
            <p className="text-[10px] text-amber-400/70 mt-1">Score 40–69</p>
          </div>

          <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold text-purple-400 uppercase tracking-wider">Site Visits</p>
              <span className="text-xs">📅</span>
            </div>
            <p className="text-2xl font-black text-purple-300 mt-1">{stats.by_status.site_visit_scheduled}</p>
            <p className="text-[10px] text-purple-400/70 mt-1">Scheduled / Completed</p>
          </div>

          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 shadow-lg col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Win Rate</p>
              <span className="text-xs">🏆</span>
            </div>
            <p className="text-2xl font-black text-emerald-300 mt-1">{stats.conversion_rate}%</p>
            <p className="text-[10px] text-emerald-400/70 mt-1">Closed Won ratio</p>
          </div>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-3">
        {/* Tier Tabs */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          {['ALL', 'HOT', 'WARM', 'COLD'].map((t) => (
            <button
              key={t}
              onClick={() => { setSelectedTier(t); setPage(1); }}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                selectedTier === t
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {t === 'ALL' ? 'All Tiers' : t}
            </button>
          ))}
        </div>

        {/* Status Dropdown & Search Input */}
        <div className="flex flex-1 items-center gap-2 max-w-md">
          <select
            value={selectedStatus}
            onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
          >
            <option value="ALL">All Pipeline Stages</option>
            <option value="NEW">NEW</option>
            <option value="CONTACTED">CONTACTED</option>
            <option value="QUALIFIED">QUALIFIED</option>
            <option value="SITE_VISIT_SCHEDULED">SITE_VISIT_SCHEDULED</option>
            <option value="OFFER_MADE">OFFER_MADE</option>
            <option value="CLOSED_WON">CLOSED_WON</option>
            <option value="CLOSED_LOST">CLOSED_LOST</option>
          </select>

          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search lead name, phone, email..."
            className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Lead Table */}
      {loading ? (
        <div className="flex h-64 items-center justify-center text-xs text-slate-400">
          <div className="flex items-center gap-3">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            Loading CRM lead records...
          </div>
        </div>
      ) : filteredLeads.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center space-y-3">
          <div className="text-3xl">📋</div>
          <h3 className="font-bold text-base text-white">No lead records found</h3>
          <p className="text-xs text-slate-400">
            No leads match the selected filter criteria or search query.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="p-4">Lead Contact</th>
                  <th className="p-4">Tier</th>
                  <th className="p-4">Intent Score</th>
                  <th className="p-4">Stage</th>
                  <th className="p-4">Source</th>
                  <th className="p-4">Created Date</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {filteredLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4">
                      <div>
                        <p className="font-bold text-white text-sm">
                          {lead.contact_name || 'Anonymous Prospect'}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {lead.contact_email || lead.contact_phone || 'No direct contact info'}
                        </p>
                      </div>
                    </td>

                    <td className="p-4">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold border ${getTierBadgeClass(
                          lead.tier
                        )}`}
                      >
                        {lead.tier || 'COLD'}
                      </span>
                    </td>

                    <td className="p-4">
                      <div className="w-28 space-y-1">
                        <div className="flex justify-between text-[10px]">
                          <span className="font-mono text-slate-300 font-semibold">
                            {lead.intent_score ?? 0}/100
                          </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              lead.intent_score >= 70
                                ? 'bg-rose-500'
                                : lead.intent_score >= 40
                                ? 'bg-amber-400'
                                : 'bg-blue-500'
                            }`}
                            style={{ width: `${Math.min(lead.intent_score ?? 0, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="p-4">
                      <span
                        className={`rounded-md px-2 py-0.5 text-[10px] font-mono font-semibold border ${getStatusBadgeClass(
                          lead.status
                        )}`}
                      >
                        {lead.status}
                      </span>
                    </td>

                    <td className="p-4 text-slate-400 uppercase text-[10px] font-mono">
                      {lead.source} · {lead.channel}
                    </td>

                    <td className="p-4 text-slate-400">
                      {new Date(lead.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>

                    <td className="p-4">
                      <button
                        onClick={() => navigate(`/crm/leads/${lead.id}`)}
                        className="rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        View Profile →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer Pagination */}
          <div className="flex items-center justify-between border-t border-slate-800 px-4 py-3 bg-slate-950/40 text-xs text-slate-400">
            <span>
              Showing {filteredLeads.length} record{filteredLeads.length !== 1 ? 's' : ''}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                className="rounded-lg border border-slate-700 px-3 py-1 text-slate-300 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={leads.length < 20}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-lg border border-slate-700 px-3 py-1 text-slate-300 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
