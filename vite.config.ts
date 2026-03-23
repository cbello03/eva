import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { TanStackRouterVite } from '@tanstack/router-plugin/vite';

export default defineConfig({
  plugins: [
    TanStackRouterVite(), // <-- ¡Este es el plugin mágico!
    react()
  ],
  server: {
    port: 3000,
  },
  test: {
    passWithNoTests: true,
  },
});