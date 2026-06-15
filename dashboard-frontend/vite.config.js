import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { existsSync } from 'fs'

const cwdRoot = process.cwd()
const altMappedRoot = cwdRoot.replace(/^O:/i, 'V:')
const projectRoot = existsSync(altMappedRoot) ? altMappedRoot : cwdRoot

export default defineConfig(({ mode }) => {
  const isDevelopment = mode === 'development'

  return {
    root: projectRoot,
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(projectRoot, 'src'),
      }
    },
    build: {
      rollupOptions: {
        input: {
          app: resolve(projectRoot, 'index.html'),
        },
      },
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