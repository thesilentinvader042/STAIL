import PropertyCard from './PropertyCard';
import type { Property } from '../types';

export default function PropertyResultsPanel({ properties }: { properties: Property[] }) {
  if (!properties || properties.length === 0) return null;

  return (
    <div className="my-3 w-full rounded-2xl border border-slate-700/60 bg-slate-900/60 p-4 backdrop-blur-md">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Matched Properties ({properties.length})
        </h4>
        <span className="text-[11px] font-medium text-blue-400">AI Verified Shortlist</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {properties.map((property) => (
          <PropertyCard key={property.id} property={property} />
        ))}
      </div>
    </div>
  );
}