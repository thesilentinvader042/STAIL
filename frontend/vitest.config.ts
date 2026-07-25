/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Vitest configuration — separate from vite.config.ts to avoid type conflicts
// Install dependencies first: npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitest/ui
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.ts'],
    include: ['src/__tests__/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**'],
      exclude: ['src/__tests__/**', 'src/main.tsx'],
    },
  },
});
