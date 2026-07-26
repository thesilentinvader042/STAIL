import { useEffect, useState } from 'react';
import FilterPanel from '../components/FilterPanel';
import PropertyCard from '../components/PropertyCard';
import { fetchProperties } from '../api/propertyApi';
import type { Property, PropertyFilterParams } from '../types';

export default function PropertyListPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<PropertyFilterParams>({ page: 1, limit: 12 });

  const loadProperties = async (currentFilters: PropertyFilterParams) => {
    setLoading(true);
    setError('');
    try {
      const { data } = await fetchProperties(currentFilters);
      if (Array.isArray(data.items)) {
        setProperties(data.items);
        setTotal(data.total || data.items.length);
        setPage(data.page || 1);
        setTotalPages(data.pages || 1);
      } else if (Array.isArray(data as any)) {
        setProperties(data as any);
        setTotal((data as any).length);
        setPage(1);
        setTotalPages(1);
      }
    } catch (err: unknown) {
      console.error('Fetch properties error:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error?.response?.data?.detail || 'Failed to load properties from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProperties(filters);
  }, [filters]);

  const handleApplyFilters = (newFilters: PropertyFilterParams) => {
    const updated = { ...filters, ...newFilters, page: 1 };
    setFilters(updated);
  };

  const handleResetFilters = () => {
    setFilters({ page: 1, limit: 12 });
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setFilters((prev) => ({ ...prev, page: newPage }));
    }
  };

  return (
    <div className="space-y-6 text-slate-100 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Properties Directory</h2>
          <p className="text-xs text-slate-400">
            Browse verified listings across top Indian metropolitan cities ({total} total properties)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filter Panel Column */}
        <div className="lg:col-span-1">
          <FilterPanel
            filters={filters}
            onApplyFilters={handleApplyFilters}
            onResetFilters={handleResetFilters}
          />
        </div>

        {/* Property Grid Column */}
        <div className="lg:col-span-3 space-y-6">
          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-400">
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-72 rounded-xl bg-slate-900 border border-slate-800 animate-pulse" />
              ))}
            </div>
          ) : properties.length === 0 ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center space-y-3">
              <div className="text-4xl">🔍</div>
              <h3 className="font-bold text-lg text-white">No properties found</h3>
              <p className="text-xs text-slate-400">
                Try adjusting your search filters or resetting to view all listings.
              </p>
              <button
                onClick={handleResetFilters}
                className="mt-2 inline-block rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {properties.map((property) => (
                <PropertyCard key={property.id} property={property} />
              ))}
            </div>
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-800 pt-4 text-xs text-slate-400">
              <span>
                Page {page} of {totalPages} ({total} properties)
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => handlePageChange(page - 1)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-medium text-slate-300 disabled:opacity-40"
                >
                  ← Previous
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => handlePageChange(page + 1)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 font-medium text-slate-300 disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}