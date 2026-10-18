import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// All assets are bundled locally; the build makes no runtime network requests
// so it can run in the air-gapped target described in docs/plans/ARCHITECTURE.md.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
});
