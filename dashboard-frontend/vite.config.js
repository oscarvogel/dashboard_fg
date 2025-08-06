import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    watch: {
      usePolling: true,  // <-- Fuerza el uso de polling
      interval: 1000     // <-- Intervalo de verificación en ms
    }
  }
})

