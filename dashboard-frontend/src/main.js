// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// ✅ Importa Tailwind
import './index.css'

// Crear la app
const app = createApp(App)

// Instalar el router → ¡esto es clave!
app.use(router)

// Montar en #app
app.mount('#app')