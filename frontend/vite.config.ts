import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

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
        target: process.env.VITE_API_BASE_URL || 'https://razorpay-recovery-agent-rnq8.onrender.com',
        changeOrigin: true,
        secure: false,
      },
      '/create-test-order': {
        target: process.env.VITE_API_BASE_URL || 'https://razorpay-recovery-agent-rnq8.onrender.com',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
