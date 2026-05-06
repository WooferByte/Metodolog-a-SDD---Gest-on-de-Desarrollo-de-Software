import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    cors: true,
  },
  build: {
    minify: 'terser',
    sourcemap: true,
    outDir: 'dist',
    emptyOutDir: true,
  },
  define: {
    'process.env': {},
  },
})
