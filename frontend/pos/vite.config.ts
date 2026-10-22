import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// PapelMaind POS (Sprint 3) — offline-first, WebUSB/WebSerial/WebHID
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
});
