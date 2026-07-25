import React, { useState } from 'react';
import type { PropertyFilterParams } from '../types';

interface FilterPanelProps {
  filters: PropertyFilterParams;
  onApplyFilters: (filters: PropertyFilterParams) => void;
  onResetFilters: () => void;
}

const CITIES = ['Mumbai', 'Bengaluru', 'Delhi NCR', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata'];
const PROPERTY_TYPES = ['APARTMENT', 'VILLA', 'PLOT', 'COMMERCIAL', 'STUDIO', 'PENTHOUSE'];

export default function FilterPanel({ filters, onApplyFilters, onResetFilters }: FilterPanelProps) {
  const [city, setCity] = useState(filters.city || '');
  const [propertyType, setPropertyType] = useState(filters.property_type || '');
  const [bhk, setBhk] = useState<number | undefined>(filters.bhk);
  const [minPrice, setMinPrice] = useState<string>(filters.min_price ? (filters.min_price / 100000).toString() : '');
  const [maxPrice, setMaxPrice] = useState<string>(filters.max_price ? (filters.max_price / 100000).toString() : '');
  const [sortBy, setSortBy] = useState(filters.sort_by || 'created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(filters.sort_order || 'desc');

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    onApplyFilters({
      city: city || undefined,
      property_type: propertyType || undefined,
      bhk: bhk || undefined,
      min_price: minPrice ? Number(minPrice) * 100000 : undefined,
      max_price: maxPrice ? Number(maxPrice) * 100000 : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      page: 1,
    });
  };

  const handleReset = () => {
    setCity('');
    setPropertyType('');
    setBhk(undefined);
    setMinPrice('');
    setMaxPrice('');
    setSortBy('created_at');
    setSortOrder('desc');
    onResetFilters();
  };

  return (
    <form onSubmit={handleApply} className="rounded-xl border border-slate-700/60 bg-slate-800/80 p-4 text-slate-100 shadow-md">
      <div className="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
        <h3 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center gap-2">
          🔍 Filter Properties
        </h3>
        <button
          type="button"
          onClick={handleReset}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          Reset All
        </button>
      </div>

      <div className="space-y-4 text-xs">
        {/* City Filter */}
        <div>
          <label className="block font-medium text-slate-400 mb-1">City</label>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Cities</option>
            {CITIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Property Type Filter */}
        <div>
          <label className="block font-medium text-slate-400 mb-1">Property Type</label>
          <select
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Types</option>
            {PROPERTY_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        {/* BHK Filter */}
        <div>
          <label className="block font-medium text-slate-400 mb-1">BHK Bedrooms</label>
          <div className="flex gap-1.5">
            {[1, 2, 3, 4, 5].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => setBhk(bhk === num ? undefined : num)}
                className={`flex-1 rounded-lg py-1.5 font-semibold transition-all ${
                  bhk === num
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {num} BHK
              </button>
            ))}
          </div>
        </div>

        {/* Budget Range */}
        <div>
          <label className="block font-medium text-slate-400 mb-1">Price Range (₹ Lakhs)</label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              placeholder="Min"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-slate-200 focus:border-blue-500 focus:outline-none"
            />
            <span className="text-slate-500">-</span>
            <input
              type="number"
              placeholder="Max"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-slate-200 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Sort By */}
        <div>
          <label className="block font-medium text-slate-400 mb-1">Sort By</label>
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2.5 py-1.5 text-slate-200 focus:border-blue-500 focus:outline-none"
            >
              <option value="created_at">Date Added</option>
              <option value="price">Price</option>
            </select>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
              className="w-28 rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-slate-200 focus:border-blue-500 focus:outline-none"
            >
              <option value="desc">High → Low</option>
              <option value="asc">Low → High</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          className="w-full rounded-lg bg-blue-600 hover:bg-blue-500 py-2.5 font-bold text-white shadow-lg transition-colors mt-2"
        >
          Apply Filters
        </button>
      </div>
    </form>
  );
}
