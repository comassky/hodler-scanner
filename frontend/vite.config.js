import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/ticker': { target: 'http://localhost:8000', changeOrigin: true },
      '/health':  { target: 'http://localhost:8000', changeOrigin: true },
      '/cache':   { target: 'http://localhost:8000', changeOrigin: true },
      '/favorites': { target: 'http://localhost:8000', changeOrigin: true },
      '/search':  { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
