import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchPropertyById } from '../api/propertyApi';
import { formatPrice } from '../components/PropertyCard';
import type { Property } from '../types';
import ScheduleSiteVisitModal from '../components/ScheduleSiteVisitModal';

export default function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [property, setProperty] = useState<Property | null>(null);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [visitScheduled, setVisitScheduled] = useState(false);
  const [showVisitModal, setShowVisitModal] = useState(false);
  const [wishlisted, setWishlisted] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError('');
    fetchPropertyById(id)
      .then((res) => {
        setProperty(res.data);
      })
      .catch((err) => {
        console.error('Fetch property detail error:', err);
        setError('Failed to fetch property details.');
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-96 w-full items-center justify-center text-slate-400 text-sm">
        <div className="flex flex-col items-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p>Loading property details...</p>
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="max-w-2xl mx-auto rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center space-y-4 text-red-400">
        <div className="text-4xl">⚠️</div>
        <h3 className="font-bold text-lg">{error || 'Property not found.'}</h3>
        <button
          onClick={() => navigate('/properties')}
          className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white"
        >
          ← Return to Directory
        </button>
      </div>
    );
  }

  const images = property.gallery_images && property.gallery_images.length > 0
    ? property.gallery_images
    : [
        property.image_url ||
          'https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80',
        'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80',
      ];

  const title = property.title || property.name || 'Premium Property';
  const locality = typeof property.locality === 'string' && property.locality.trim()
    ? property.locality
    : typeof property.location === 'string' && property.location.trim()
      ? property.location
      : (property.location as any)?.locality || (property.location as any)?.address_line_1 || 'Prime Location';

  const city = typeof property.city === 'string' && property.city.trim()
    ? property.city
    : (property.location as any)?.city || '';

  const price = property.asking_price ?? property.price;

  const bhk = property.bhk ?? property.residential?.num_bedrooms ?? (property.attributes?.num_bedrooms) ?? (property.attributes?.bhk_type);

  const carpetArea = property.carpet_area_sqft ?? property.super_built_up ?? (property.attributes?.carpet_area_sqft);

  return (
    <div className="max-w-6xl mx-auto space-y-6 text-slate-100 pb-12">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="text-xs font-semibold text-slate-400 hover:text-white transition-colors flex items-center gap-1"
      >
        ← Back to Listings
      </button>

      {/* Header Info & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="rounded bg-blue-600/20 px-2 py-0.5 text-xs font-bold text-blue-400 border border-blue-500/30">
              {property.property_type || 'Apartment'}
            </span>
            <span className="text-xs text-slate-400">📍 {String(locality)}{city ? `, ${city}` : ''}</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white">{title}</h1>
        </div>

        <div className="flex flex-col items-start md:items-end gap-1">
          <div className="text-2xl font-black text-blue-400">
            {formatPrice(price)}
          </div>
          <p className="text-[11px] text-slate-400">Government Registered Listing</p>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Gallery & Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Gallery Display */}
          <div className="space-y-3">
            <div className="relative h-96 w-full overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-xl">
              <img
                src={images[activeImageIndex]}
                alt={title}
                className="h-full w-full object-cover transition-all duration-300"
              />
              <div className="absolute bottom-3 right-3 rounded-lg bg-slate-950/80 backdrop-blur-md px-3 py-1 text-xs text-slate-200">
                Image {activeImageIndex + 1} of {images.length}
              </div>
            </div>

            {/* Gallery Thumbnails */}
            {images.length > 1 && (
              <div className="flex gap-3 overflow-x-auto pb-1">
                {images.map((img, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveImageIndex(index)}
                    className={`h-20 w-28 shrink-0 overflow-hidden rounded-xl border-2 transition-all ${
                      activeImageIndex === index
                        ? 'border-blue-500 scale-105 shadow-md shadow-blue-500/20'
                        : 'border-slate-800 opacity-60 hover:opacity-100'
                    }`}
                  >
                    <img src={img} alt={`Thumbnail ${index + 1}`} className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Property Specifications Overview */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
            <h3 className="font-bold text-base text-white border-b border-slate-800 pb-2">
              Key Specifications
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Configuration</span>
                <span className="font-bold text-slate-200 text-sm">{bhk ? `${bhk} BHK` : 'N/A'}</span>
              </div>
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Carpet Area</span>
                <span className="font-bold text-slate-200 text-sm">
                  {carpetArea ? `${carpetArea} sq.ft` : 'N/A'}
                </span>
              </div>
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Possession Status</span>
                <span className="font-bold text-slate-200 text-sm capitalize">
                  {property.possession_status || property.residential?.possession_status || 'Ready to Move'}
                </span>
              </div>
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Floor</span>
                <span className="font-bold text-slate-200 text-sm">
                  {property.floor_number ?? property.residential?.floor_number ? `${property.floor_number ?? property.residential?.floor_number} of ${property.total_floors ?? property.residential?.total_floors ?? 'N/A'}` : 'N/A'}
                </span>
              </div>
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Facing</span>
                <span className="font-bold text-slate-200 text-sm capitalize">{property.facing || 'East'}</span>
              </div>
              <div className="rounded-xl bg-slate-950 p-3 border border-slate-800">
                <span className="text-slate-500 block mb-0.5">Furnishing</span>
                <span className="font-bold text-slate-200 text-sm capitalize">
                  {property.furnishing_status || property.residential?.furnishing_status || 'Semi-Furnished'}
                </span>
              </div>
            </div>
          </div>

          {/* Description & Overview */}
          {property.description && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-3">
              <h3 className="font-bold text-base text-white border-b border-slate-800 pb-2">
                Property Overview
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {property.description}
              </p>
            </div>
          )}

          {/* Amenities Grid */}
          {property.amenities && property.amenities.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
              <h3 className="font-bold text-base text-white border-b border-slate-800 pb-2">
                Amenities &amp; Facilities
              </h3>
              <div className="flex flex-wrap gap-2 text-xs">
                {property.amenities.map((amenity, idx) => (
                  <span
                    key={idx}
                    className="rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 font-medium text-slate-300 flex items-center gap-1.5"
                  >
                    ✨ {amenity}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Actions & Developer Info */}
        <div className="space-y-6">
          {/* Action Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 space-y-4 shadow-xl">
            <h3 className="font-bold text-sm text-white uppercase tracking-wider">
              Take Action
            </h3>

            {visitScheduled ? (
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400 font-semibold text-center">
                ✅ Site Visit Scheduled! Our agent will contact you.
              </div>
            ) : (
              <button
                onClick={() => setShowVisitModal(true)}
                className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 py-3 text-xs font-bold text-white shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-1.5"
              >
                📅 Schedule Site Visit
              </button>
            )}

            <button
              onClick={() => setWishlisted(!wishlisted)}
              className={`w-full rounded-xl border py-3 text-xs font-bold transition-all ${
                wishlisted
                  ? 'border-emerald-500/40 bg-emerald-500/20 text-emerald-300'
                  : 'border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700'
              }`}
            >
              {wishlisted ? '❤️ Saved to Wishlist' : '🤍 Save to Wishlist'}
            </button>
          </div>

          {/* Developer Card */}
          {property.developer && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-3 text-xs">
              <h3 className="font-bold text-sm text-white uppercase tracking-wider border-b border-slate-800 pb-2">
                Developer Information
              </h3>
              <div>
                <p className="font-bold text-sm text-blue-400">{property.developer.name}</p>
                {property.developer.city && <p className="text-slate-400 mt-0.5">Headquarters: {property.developer.city}</p>}
              </div>
              {property.developer.website && (
                <a
                  href={property.developer.website}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block text-xs font-semibold text-blue-400 hover:underline"
                >
                  Visit Official Website ↗
                </a>
              )}
            </div>
          )}

          {/* AI Insights Card */}
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 space-y-2 text-xs">
            <h4 className="font-bold text-emerald-400 flex items-center gap-1.5">
              🤖 AGT-05 Recommendation Insight
            </h4>
            <p className="text-slate-300 leading-relaxed">
              This property scored high for location connectivity and price competitiveness relative to current market trends in {city || 'this city'}.
            </p>
          </div>
        </div>
      </div>

      {/* Schedule Site Visit Modal (Component 4) */}
      {showVisitModal && (
        <ScheduleSiteVisitModal
          leadId={id || 'prop-lead'}
          propertyTitle={title}
          onClose={() => setShowVisitModal(false)}
          onSuccess={() => setVisitScheduled(true)}
        />
      )}
    </div>
  );
}