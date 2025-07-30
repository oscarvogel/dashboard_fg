<!-- src/App.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'

const router = useRouter()
const route = useRoute()

// Estado de autenticación
const isAuthenticated = ref(false)

// Verificar autenticación al montar
const checkAuth = () => {
  const token = localStorage.getItem('access_token')
  const empleado = localStorage.getItem('empleado')
  isAuthenticated.value = !!(token && empleado)
}

// Redirección inteligente
const handleRedirect = () => {
  const token = localStorage.getItem('access_token')
  const empleado = localStorage.getItem('empleado')
  const isLoggedIn = !!(token && empleado)

  // Si está logueado y va a /login, redirige al dashboard
  if (isLoggedIn && route.path === '/login') {
    router.push('/')
  }

  // Si no está logueado y intenta acceder a una ruta protegida
  if (!isLoggedIn && route.meta.requiresAuth) {
    router.push('/login') // Asume que tienes una vista de login
  }

  // Actualizar estado
  isAuthenticated.value = isLoggedIn
}

// Ejecutar al montar
onMounted(() => {
  checkAuth()
  handleRedirect()
})

// Escuchar cambios de ruta
router.afterEach(() => {
  handleRedirect()
})
</script>

<template>
  <div class="flex flex-col min-h-screen bg-gray-50">
    <!-- Mostrar Navbar solo si está autenticado -->
    <Navbar v-if="isAuthenticated" />

    <!-- Contenido principal -->
    <main class="flex-1 pt-0">
      <router-view />
    </main>
  </div>
</template>

<style>
.app-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>