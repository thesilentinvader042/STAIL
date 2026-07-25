import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import PreferencePanel from '../components/PreferencePanel';

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6 text-slate-100 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-r from-blue-900/40 via-indigo-900/20 to-slate-900 p-6 md:p-8 backdrop-blur-xl shadow-xl">
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400 border border-blue-500/20">
            ✨ STAIL Realty OS • Phase 1–4 Active
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            Welcome back, {user?.full_name || 'Partner'} 👋
          </h1>
          <p className="max-w-2xl text-xs md:text-sm text-slate-300 leading-relaxed">
            Your AI-orchestrated real estate dashboard is running. 5 microservice agents + autonomous memory system are active to discover, qualify, and recommend properties in real time.
          </p>
          <div className="pt-2 flex flex-wrap gap-3">
            <Link
              to="/search"
              className="rounded-xl bg-blue-600 hover:bg-blue-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition-colors flex items-center gap-2"
            >
              🤖 Launch AI Conversational Search
            </Link>
            <Link
              to="/properties"
              className="rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-800 px-4 py-2.5 text-xs font-bold text-slate-200 transition-colors flex items-center gap-2"
            >
              🏢 Browse Property Catalog
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Microservice Agents</span>
            <span className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">🤖</span>
          </div>
          <p className="mt-3 text-2xl font-black text-white">5 Active</p>
          <p className="mt-1 text-[11px] text-slate-400">AGT-01 to AGT-06 Pipeline</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Memory Subsystem</span>
            <span className="rounded-lg bg-blue-500/10 p-2 text-blue-400">🧠</span>
          </div>
          <p className="mt-3 text-2xl font-black text-white">4 Scopes</p>
          <p className="mt-1 text-[11px] text-slate-400">Redis + Postgres Dual-Write</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">User Account</span>
            <span className="rounded-lg bg-amber-500/10 p-2 text-amber-400">👤</span>
          </div>
          <p className="mt-3 text-2xl font-black text-white capitalize">{user?.role?.toLowerCase() || 'Buyer'}</p>
          <p className="mt-1 text-[11px] text-slate-400">{user?.email}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Database Context</span>
            <span className="rounded-lg bg-purple-500/10 p-2 text-purple-400">💾</span>
          </div>
          <p className="mt-3 text-2xl font-black text-white">PostgreSQL</p>
          <p className="mt-1 text-[11px] text-slate-400">Alembic Migrated &amp; Verified</p>
        </div>
      </div>

      {/* Preference Panel Component */}
      <PreferencePanel />

      {/* Workflow Navigation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
          <h3 className="font-bold text-base text-white flex items-center gap-2">
            🤖 Natural Language Search
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            State your buyer intent in plain English or Hinglish (e.g. "Looking for a 3BHK in Bandra West under 2.5 Crore"). AGT-03 will extract requirements, AGT-04 will search the DB, AGT-05 will rank matches, and AGT-02 will score the lead.
          </p>
          <Link
            to="/search"
            className="inline-block rounded-xl bg-blue-600/90 hover:bg-blue-600 px-4 py-2.5 text-xs font-semibold text-white transition-colors"
          >
            Start Conversation →
          </Link>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
          <h3 className="font-bold text-base text-white flex items-center gap-2">
            🏢 Property Listing Directory
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Filter properties by city, property type, price range, BHK configuration, and amenities. View full property details, image galleries, and developer notes.
          </p>
          <Link
            to="/properties"
            className="inline-block rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 px-4 py-2.5 text-xs font-semibold text-slate-200 transition-colors"
          >
            Explore Catalog →
          </Link>
        </div>
      </div>
    </div>
  );
}