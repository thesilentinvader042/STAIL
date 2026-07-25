import { useNavigate } from 'react-router-dom';
import type { Property } from '../types';

export function formatPrice(amount?: number): string {
  if (amount === undefined || amount === null || isNaN(amount)) return 'Price on Request';
  if (amount >= 10000000) {
    return `₹ ${(amount / 10000000).toFixed(2)} Cr`;
  }
  if (amount >= 100000) {
    return `₹ ${(amount / 100000).toFixed(2)} Lakh`;
  }
  return `₹ ${amount.toLocaleString('en-IN')}`;
}

export default function PropertyCard({ property }: { property: Property }) {
  const navigate = useNavigate();

  const title = property.title || property.name || 'Premium Property';
  
  const locality = typeof property.locality === 'string' && property.locality.trim()
    ? property.locality
    : typeof property.location === 'string' && property.location.trim()
      ? property.location
      : (property.location as any)?.locality || (property.location as any)?.address_line_1 || 'Prime Location';

  const displayCity = typeof property.city === 'string' && property.city.trim()
    ? `, ${property.city}`
    : (property.location as any)?.city ? `, ${(property.location as any).city}` : '';

  const price = property.asking_price ?? property.price;

  const bhk = property.bhk ?? property.residential?.num_bedrooms ?? (property.attributes?.num_bedrooms) ?? (property.attributes?.bhk_type);

  const carpetArea = property.carpet_area_sqft ?? property.super_built_up ?? (property.attributes?.carpet_area_sqft);

  const imageUrl =
    property.image_url ||
    (property.gallery_images && property.gallery_images.length > 0 ? property.gallery_images[0] : null) ||
    'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=600&q=80';

  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-slate-700/60 bg-slate-800/90 shadow-lg transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/50 hover:shadow-blue-500/10">
      <div className="relative h-40 w-full overflow-hidden bg-slate-900">
        <img
          src={imageUrl}
          alt={title}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />
        
        <span className="absolute top-2 left-2 rounded-md bg-blue-600/90 px-2 py-0.5 text-[11px] font-semibold text-white backdrop-blur-sm">
          {property.property_type || 'Apartment'}
        </span>

        {property.relevance_score !== undefined && (
          <span className="absolute top-2 right-2 rounded-md bg-emerald-600/90 px-2 py-0.5 text-[11px] font-bold text-white backdrop-blur-sm">
            {(property.relevance_score * 100).toFixed(0)}% Match
          </span>
        )}

        <div className="absolute bottom-2 left-2 right-2 font-bold text-lg text-white">
          {formatPrice(price)}
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-between p-3.5 space-y-3">
        <div>
          <h3 className="line-clamp-1 font-semibold text-slate-100 group-hover:text-blue-400 transition-colors">
            {title}
          </h3>
          <p className="line-clamp-1 text-xs text-slate-400 mt-0.5">
            📍 {String(locality)}{displayCity}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 rounded-lg bg-slate-900/50 p-2 text-xs text-slate-300">
          <div>
            <span className="text-slate-500">BHK:</span>{' '}
            <span className="font-semibold text-slate-200">{bhk ? `${bhk} BHK` : 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500">Area:</span>{' '}
            <span className="font-semibold text-slate-200">
              {carpetArea ? `${carpetArea} sq.ft` : 'N/A'}
            </span>
          </div>
        </div>

        {property.match_reasons && property.match_reasons.length > 0 && (
          <div className="text-[11px] text-emerald-400 bg-emerald-500/10 p-1.5 rounded border border-emerald-500/20 line-clamp-1">
            ✨ {property.match_reasons[0]}
          </div>
        )}

        <button
          onClick={() => navigate(`/properties/${property.id}`)}
          className="w-full rounded-lg bg-blue-600/90 hover:bg-blue-600 py-2 text-xs font-semibold text-white shadow-md transition-colors flex items-center justify-center gap-1"
        >
          View Full Details →
        </button>
      </div>
    </div>
  );
}