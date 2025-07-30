<!-- src/components/Navbar.vue -->
<template>
  <nav class="bg-gray-800 text-white shadow-lg">
    <div class="max-w-full px-4 mx-auto">
      <!-- Barra superior -->
      <div class="flex justify-between items-center h-16">
        <!-- Logo / Nombre de la app -->
        <div class="flex items-center space-x-6">
          <router-link
            to="/"
            class="text-xl font-bold hover:text-blue-300 transition flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-8 8" />
            </svg>
            FG Producción
          </router-link>

          <!-- Botón de hamburguesa (solo en móvil) -->
          <button
            @click="toggleMobileMenu"
            class="md:hidden p-2 rounded hover:bg-gray-700 focus:outline-none"
            aria-label="Menú"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                v-if="!showMobileMenu"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Menú de navegación (solo desktop) -->
        <div class="hidden md:flex items-center space-x-2">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center space-x-2 px-3 py-2 rounded text-sm font-medium hover:bg-gray-700 transition duration-200"
            active-class="bg-blue-600 text-white font-semibold"
          >
            <svg :xmlns="item.xmlns" :class="item.iconClass" :viewBox="item.viewBox" stroke="currentColor" fill="none">
              <path :d="item.iconPath" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
            </svg>
            <span>{{ item.name }}</span>
          </router-link>

          <!-- Bienvenida y Cerrar sesión (solo desktop) -->
          <div class="flex items-center space-x-4 text-sm ml-6 border-l border-gray-600 pl-4">
            <span>Bienvenido, <strong>{{ empleado?.nombre }}</strong></span>
            <button
              @click="logout"
              class="bg-red-600 hover:bg-red-700 px-3 py-1 rounded transition text-xs"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>

      <!-- Menú móvil desplegable -->
      <div
        v-show="showMobileMenu"
        class="md:hidden border-t border-gray-700 bg-gray-800"
      >
        <div class="flex flex-col space-y-2 px-2 py-3">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center space-x-3 p-2 rounded hover:bg-gray-700 transition"
            active-class="bg-blue-600 font-medium"
            @click="showMobileMenu = false"
          >
            <svg :xmlns="item.xmlns" :class="item.iconClass" :viewBox="item.viewBox" stroke="currentColor" fill="none">
              <path :d="item.iconPath" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
            </svg>
            <span class="capitalize">{{ item.name }}</span>
          </router-link>

          <!-- Bienvenida y Cerrar sesión (móvil) -->
          <div class="pt-2 mt-2 border-t border-gray-700 text-center text-sm">
            <p>Bienvenido, <strong>{{ empleado?.nombre }}</strong></p>
            <button
              @click="logout"
              class="mt-2 w-full bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-xs"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showMobileMenu = ref(false)
const empleado = ref(JSON.parse(localStorage.getItem('empleado')))

// Definición del menú con íconos (usando Heroicons)
const menuItems = [
  {
    name: 'Dashboard',
    path: '/',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-5 w-5 text-blue-300',
    iconPath: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
  },
  {
    name: 'Resumen',
    path: '/resumen-operacional',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-5 w-5 text-green-300',
    iconPath: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-1.618a1 1 0 00-.67.253l-2.322 1.68A1 1 0 019 17z'
  },
  {
  name: 'Combustible',
  path: '/resumen-combustible',
  xmlns: 'http://www.w3.org/2000/svg',
  viewBox: '0 0 24 24',
  iconClass: 'h-5 w-5 text-orange-300',
  iconPath: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.676-2.154-1.415-3.414l5-5A2 2 0 009 10.172V5L8 4z'
  },{
  name: 'Produccion',
  path: '/reporte-produccion',
  xmlns: 'http://www.w3.org/2000/svg',
  viewBox: '0 0 24 24',
  iconClass: 'h-5 w-5 text-green-300', // color verde para asociarlo con producción
  iconPath: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2z'
}
]

const toggleMobileMenu = () => {
  showMobileMenu.value = !showMobileMenu.value
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('empleado')
  showMobileMenu.value = false
  router.push('/')
}
</script>