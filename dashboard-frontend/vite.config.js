import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const isDevelopment = mode === 'development'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      }
    },
    server: isDevelopment
      ? {
          port: 5176,
          proxy: {
            '/api': {
              target: 'http://localhost:8000',
              changeOrigin: true,
              secure: false,
            },
          },
          // 👇 Aquí va usePolling
          watch: {
            usePolling: true,
            interval: 1000,
          }
        }
      : undefined,
  }
})