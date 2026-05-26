import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Use backend service name in Docker, localhost otherwise
const apiTarget = process.env.DOCKER_ENV ? 'http://backend:8000' : 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    host: true, // Listen on all interfaces (needed for Docker)
    watch: {
      usePolling: true // Needed for hot-reload in Docker on some systems
    },
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true
      }
    }
  }
})
