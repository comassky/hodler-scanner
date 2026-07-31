import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import pkg from './package.json' with { type: 'json' }

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
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
