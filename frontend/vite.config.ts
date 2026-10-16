import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The browser calls same-origin paths; the dev server forwards them to the API, so CORS is
// not needed during development. Override the target with ALGOLAB_API_URL.
const apiTarget = process.env.ALGOLAB_API_URL ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': apiTarget,
      '/health': apiTarget,
    },
  },
})
