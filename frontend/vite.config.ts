import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true
    },
    // Allow ngrok and other external hosts (Vite 5+)
    // Set to true for development to allow any host (including ngrok)
    // In production, specify exact hosts for security
    allowedHosts: true,
    // Disable strict host checking for development
    strictPort: false,
    // Proxy API requests to backend (only used when VITE_API_URL is not set)
    // For local development, set VITE_API_URL=http://localhost:8000
    // For ngrok, leave VITE_API_URL unset to use proxy
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

