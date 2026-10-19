import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// Assets stay local. Offline deployments still call their local HTTP backend.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, watch: { ignored: ['**/*.md', '**/tests/**'] }, proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } } },
});
