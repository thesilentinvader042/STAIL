import { describe, it, expect } from 'vitest';
import { formatPrice } from '../components/PropertyCard';

describe('formatPrice – INR currency formatting', () => {
  describe('Crore range (≥ ₹1 Cr)', () => {
    it('formats 2.5 Cr correctly', () => {
      expect(formatPrice(25000000)).toBe('₹ 2.50 Cr');
    });

    it('formats 1.5 Cr correctly', () => {
      expect(formatPrice(15000000)).toBe('₹ 1.50 Cr');
    });

    it('formats exactly 1 Cr correctly', () => {
      expect(formatPrice(10000000)).toBe('₹ 1.00 Cr');
    });

    it('formats 5 Cr correctly', () => {
      expect(formatPrice(50000000)).toBe('₹ 5.00 Cr');
    });

    it('formats 10 Cr correctly', () => {
      expect(formatPrice(100000000)).toBe('₹ 10.00 Cr');
    });
  });

  describe('Lakh range (≥ ₹1 Lakh, < ₹1 Cr)', () => {
    it('formats 85 Lakh correctly', () => {
      expect(formatPrice(8500000)).toBe('₹ 85.00 Lakh');
    });

    it('formats 50 Lakh correctly', () => {
      expect(formatPrice(5000000)).toBe('₹ 50.00 Lakh');
    });

    it('formats 25 Lakh correctly', () => {
      expect(formatPrice(2500000)).toBe('₹ 25.00 Lakh');
    });

    it('formats exactly 1 Lakh correctly', () => {
      expect(formatPrice(100000)).toBe('₹ 1.00 Lakh');
    });
  });

  describe('Invalid / edge cases', () => {
    it('returns "Price on Request" for undefined', () => {
      expect(formatPrice(undefined)).toBe('Price on Request');
    });

    it('returns "Price on Request" for NaN', () => {
      expect(formatPrice(NaN)).toBe('Price on Request');
    });

    it('returns "Price on Request" for null-like values', () => {
      expect(formatPrice(undefined)).toBe('Price on Request');
    });
  });
});
