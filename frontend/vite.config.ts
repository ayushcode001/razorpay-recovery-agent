import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const BACKEND_TARGET = process.env.BACKEND_URL || 'http://localhost:5000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_TARGET,
        changeOrigin: true,
        secure: false,
      },
      '/create-test-order': {
        target: BACKEND_TARGET,
        changeOrigin: true,
        secure: false,
      },
      '/webhook': {
        target: BACKEND_TARGET,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
