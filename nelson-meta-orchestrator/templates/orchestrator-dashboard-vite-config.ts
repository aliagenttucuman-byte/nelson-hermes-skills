// vite.config.ts — template para dashboard del orquestador Nelson
// Incluye proxy hacia los 3 servicios del stack
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    allowedHosts: true,  // necesario para Cloudflare tunnel
    proxy: {
      '/api/tasks':       { target: 'http://localhost:8742', rewrite: p => p.replace('/api/tasks', '/tasks'),       changeOrigin: true },
      '/api/route':       { target: 'http://localhost:8743', rewrite: p => p.replace('/api/route', ''),             changeOrigin: true },
      '/api/taxonomy':    { target: 'http://localhost:8743', rewrite: p => p.replace('/api/taxonomy', '/taxonomy'), changeOrigin: true },
      '/api/orchestrate': { target: 'http://localhost:8744', rewrite: p => p.replace('/api/orchestrate', ''),       changeOrigin: true },
    },
  },
})
