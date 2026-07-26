import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../api/authApi';
import type { UserRole } from '../types';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('BUYER');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [isNri, setIsNri] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!fullName || !email || !password || !phone) {
      setError('Please fill in all required fields.');
      return;
    }

    setLoading(true);
    try {
      await register({
        email: email.trim(),
        phone: phone.trim(),
        full_name: fullName.trim(),
        password,
        role,
        city: city.trim() || undefined,
        state: state.trim() || undefined,
        is_nri: isNri,
        language_pref: 'en',
        language_preference: 'en',
      });
      navigate('/login', { state: { registered: true } });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      const msg = error?.response?.data?.detail || 'Registration failed. Please check details.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-8 text-slate-100 antialiased">
      <div className="w-full max-w-lg space-y-6 rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl backdrop-blur-xl">
        <div className="text-center space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-white">Create Account</h2>
          <p className="text-xs text-slate-400">Join STAIL Realty OS Network</p>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400 font-medium">
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-300 mb-1">Full Name *</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Aditya Maharana"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="block font-medium text-slate-300 mb-1">Phone Number *</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 9876543210"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                required
              />
            </div>
          </div>

          <div>
            <label className="block font-medium text-slate-300 mb-1">Email Address *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-300 mb-1">Password *</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                required
              />
            </div>

            <div>
              <label className="block font-medium text-slate-300 mb-1">Role *</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 focus:border-blue-500 focus:outline-none"
              >
                <option value="BUYER">Property Buyer</option>
                <option value="SELLER">Property Owner / Seller</option>
                <option value="BROKER">Real Estate Broker</option>
                <option value="DEVELOPER">Property Developer</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-300 mb-1">City</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Mumbai"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block font-medium text-slate-300 mb-1">State</label>
              <input
                type="text"
                value={state}
                onChange={(e) => setState(e.target.value)}
                placeholder="Maharashtra"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="isNri"
              checked={isNri}
              onChange={(e) => setIsNri(e.target.checked)}
              className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0"
            />
            <label htmlFor="isNri" className="text-xs text-slate-300">
              I am an NRI (Non-Resident Indian) Buyer
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 py-3 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 mt-2"
          >
            {loading ? 'Creating Account...' : 'Register Account'}
          </button>
        </form>

        <div className="text-center text-xs text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-blue-400 hover:underline">
            Sign in here
          </Link>
        </div>
      </div>
    </div>
  );
}