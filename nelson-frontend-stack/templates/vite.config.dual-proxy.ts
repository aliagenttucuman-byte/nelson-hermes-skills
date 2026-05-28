// vite.config.ts — patrón proxy dual (ej: Task Memory :8742 + Router :8743)
// Usar cuando el frontend necesita hablar con dos backends distintos
// y no queremos CORS ni hardcodear puertos en el frontend.
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
    allowedHosts: true,   // necesario para cloudflared / ngrok
    proxy: {
      // Prefijo /api/tasks → backend A en :8742
      '/api/tasks': {
        target: 'http://localhost:8742',
        rewrite: (p) => p.replace('/api/tasks', '/tasks'),
        changeOrigin: true,
      },
      // Prefijo /api/route → backend B en :8743
      '/api/route': {
        target: 'http://localhost:8743',
        rewrite: (p) => p.replace('/api/route', ''),
        changeOrigin: true,
      },
      '/api/taxonomy': {
        target: 'http://localhost:8743',
        rewrite: (p) => p.replace('/api/taxonomy', '/taxonomy'),
        changeOrigin: true,
      },
    },
  },
})
