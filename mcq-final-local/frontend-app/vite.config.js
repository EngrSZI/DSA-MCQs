import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  // Local/Cloudflare mode serves the application at the domain root.
  // GitHub Pages can override this with VITE_BASE_PATH=/dsaquestion/.
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['.trycloudflare.com'],
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/exams': 'http://127.0.0.1:8000',
      '/subjects': 'http://127.0.0.1:8000',
      '/questions': 'http://127.0.0.1:8000',
      '/exam-questions': 'http://127.0.0.1:8000',
      '/attempts': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
    },
  },
})
