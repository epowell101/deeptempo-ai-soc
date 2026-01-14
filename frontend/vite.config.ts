import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 6988,
    host: '127.0.0.1', // Use IPv4 explicitly
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:6987', // Use IPv4 explicitly instead of localhost
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'build',
  },
})

