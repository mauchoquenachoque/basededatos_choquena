import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** Must match the port where you run uvicorn (see README: --port 8000). */
const backendTarget = process.env.VITE_BACKEND_PROXY_URL || 'http://localhost:8000'

const apiProxy = {
  '/api': {
    target: backendTarget,
    changeOrigin: true,
  },
  '/health': {
    target: backendTarget,
    changeOrigin: true,
  },
} as const

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: { ...apiProxy },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    proxy: { ...apiProxy },
  },
})
