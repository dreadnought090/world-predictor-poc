import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8080', rewrite: p => p.replace(/^\/api/, '') },
      '/predictions': 'http://localhost:8080',
      '/country': 'http://localhost:8080',
      '/history': 'http://localhost:8080',
      '/events': 'http://localhost:8080',
      '/news': 'http://localhost:8080',
      '/agents': 'http://localhost:8080',
      '/fetch_news': 'http://localhost:8080',
      '/simulate': 'http://localhost:8080',
      '/institutions': 'http://localhost:8080',
      '/relations': 'http://localhost:8080',
      '/global': 'http://localhost:8080',
      '/market': 'http://localhost:8080',
      '/policies': 'http://localhost:8080',
      '/scenarios': 'http://localhost:8080',
      '/validation': 'http://localhost:8080',
      '/presets': 'http://localhost:8080',
      '/status': 'http://localhost:8080',
      '/countries': 'http://localhost:8080',
      '/viz': 'http://localhost:8080',
    },
  },
  build: {
    outDir: 'dist',
  },
})
