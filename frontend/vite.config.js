import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const FRONTEND_PORT = Number(process.env.HEIMDALL_FRONTEND_PORT ?? 4173)
const API_PORT = Number(process.env.HEIMDALL_API_PORT ?? 8000)

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '127.0.0.1',
    port: FRONTEND_PORT,
    strictPort: true,
    proxy: {
      '/api': {
        target: `http://localhost:${API_PORT}`,
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, ''), // FastAPI有/api前缀，不需要rewrite
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('lightweight-charts')) {
              return 'lightweight-charts-vendor'
            }
            if (
              id.includes('chart.js') ||
              id.includes('chartjs-adapter-date-fns') ||
              id.includes('chartjs-plugin-annotation') ||
              id.includes('date-fns')
            ) {
              return 'chartjs-vendor'
            }
            if (id.includes('echarts') || id.includes('vue-echarts')) {
              return 'echarts-vendor'
            }
            if (
              id.includes('vue') ||
              id.includes('vue-router') ||
              id.includes('pinia') ||
              id.includes('vue-i18n')
            ) {
              return 'vue-vendor'
            }
            if (
              id.includes('@heroicons') ||
              id.includes('lucide-vue-next')
            ) {
              return 'icons-vendor'
            }
            return 'vendor'
          }
        },
      },
    },
  }
})
