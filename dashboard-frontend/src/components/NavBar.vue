<!-- src/components/Navbar.vue -->
<template>
  <nav class="bg-gradient-to-r from-gray-900 to-gray-800 text-white shadow-xl border-b border-gray-700">
    <div class="max-w-full px-4 mx-auto">
      <!-- Barra superior -->
      <div class="flex justify-between items-center h-16">
        <!-- Logo / Nombre de la app -->
        <div class="flex items-center space-x-6">
          <router-link
            to="/"
            class="text-xl font-bold hover:text-emerald-300 transition-all duration-300 flex items-center gap-2"
          >
            <div class="p-2 bg-emerald-600 rounded-lg shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-8 8" />
              </svg>
            </div>
            <span class="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
              FG Producción
            </span>
          </router-link>

          <!-- Botón de hamburguesa (solo en móvil) -->
          <button
            @click="toggleMobileMenu"
            class="md:hidden p-2 rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all duration-200"
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
        <div class="hidden md:flex items-center space-x-1" @click="closeDropdowns">
          <div v-for="item in menuItems" :key="item.path">
            <template v-if="item.name !== 'Produccion'">
              <router-link
                :to="item.path"
                class="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-200 backdrop-blur-sm"
                active-class="bg-emerald-600 text-white font-semibold shadow-lg"
              >
                <svg :xmlns="item.xmlns" :class="item.iconClass" :viewBox="item.viewBox" stroke="currentColor" fill="none">
                  <path :d="item.iconPath" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                </svg>
                <span>{{ item.name }}</span>
              </router-link>
            </template>
            <template v-else>
              <div class="relative inline-block">
                <button
                  @click.stop="toggleProduccionDropdown"
                  class="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-200 backdrop-blur-sm group"
                  :class="{ 'bg-emerald-600 text-white font-semibold shadow-lg': $route.path.startsWith('/reporte-produccion') || $route.path.startsWith('/kpis-choferes') || $route.path.startsWith('/dashboard-detallado') }"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-300 group-hover:text-white transition-colors" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                    <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                  </svg>
                  <span>Producción</span>
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform duration-200 text-slate-400" :class="{ 'rotate-180': showProduccionDropdown }" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                    <path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                  </svg>
                </button>

                <div v-show="showProduccionDropdown" class="absolute right-0 mt-2 w-64 bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl border border-gray-200/20 z-50 overflow-hidden">
                  <div class="py-2">
                    <router-link to="/dashboard-detallado" class="flex items-center space-x-3 px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 transition-all duration-200 group" @click="closeDropdowns">
                      <div class="p-1 rounded-md bg-gray-100 group-hover:bg-emerald-100 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-600 group-hover:text-emerald-600" viewBox="0 0 24 24" stroke="currentColor" fill="none"><path d="M3 7h18M3 12h18M3 17h18" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                      </div>
                      <span class="font-medium">Dashboard Actual</span>
                    </router-link>
                    <router-link to="/reporte-produccion" class="flex items-center space-x-3 px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 transition-all duration-200 group" @click="closeDropdowns">
                      <div class="p-1 rounded-md bg-gray-100 group-hover:bg-emerald-100 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-600 group-hover:text-emerald-600" viewBox="0 0 24 24" stroke="currentColor" fill="none"><path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                      </div>
                      <span class="font-medium">Reporte de Producción</span>
                    </router-link>
                    <router-link to="/kpis-choferes" class="flex items-center space-x-3 px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 transition-all duration-200 group" @click="closeDropdowns">
                      <div class="p-1 rounded-md bg-gray-100 group-hover:bg-emerald-100 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-600 group-hover:text-emerald-600" viewBox="0 0 24 24" stroke="currentColor" fill="none"><path d="M3 7h18M3 12h18M3 17h18" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/></svg>
                      </div>
                      <span class="font-medium">KPIs Choferes</span>
                    </router-link>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- Dropdown para Control Operativo -->
          <div class="relative">
            <button
              @click.stop="toggleControlOperativoDropdown"
              class="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium hover:bg-white/10 transition-all duration-200 backdrop-blur-sm group"
              :class="{ 
                'bg-emerald-600 text-white font-semibold shadow-lg': $route.path === '/maquinas-frente-operador' || $route.path === '/efectividad-servicios',
                'hover:bg-white/10': !($route.path === '/maquinas-frente-operador' || $route.path === '/efectividad-servicios')
              }"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-300 group-hover:text-white transition-colors" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h.01M9 13h.01M15 13h.01M9 17h.01M15 17h.01" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
              <span>Control Operativo</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform duration-200 text-slate-400" :class="{ 'rotate-180': showControlOperativoDropdown }" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                <path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
            </button>
            
            <!-- Dropdown menu -->
            <div
              v-show="showControlOperativoDropdown"
              class="absolute right-0 mt-2 w-64 bg-white/95 backdrop-blur-lg rounded-xl shadow-2xl border border-gray-200/20 z-50 overflow-hidden"
            >
              <div class="py-2">
                <router-link
                  v-for="subItem in controlOperativoSubmenu"
                  :key="subItem.path"
                  :to="subItem.path"
                  class="flex items-center space-x-3 px-4 py-3 text-sm text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 transition-all duration-200 group"
                  active-class="bg-emerald-100 text-emerald-800 font-semibold border-r-4 border-emerald-500"
                  @click="closeDropdowns"
                >
                  <div class="p-1 rounded-md bg-gray-100 group-hover:bg-emerald-100 transition-colors">
                    <svg :xmlns="subItem.xmlns" class="h-4 w-4 text-gray-600 group-hover:text-emerald-600" :viewBox="subItem.viewBox" stroke="currentColor" fill="none">
                      <path :d="subItem.iconPath" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                    </svg>
                  </div>
                  <span class="font-medium">{{ subItem.name }}</span>
                </router-link>
              </div>
            </div>
          </div>

          <!-- Bienvenida y Cerrar sesión (solo desktop) -->
          <div class="flex items-center space-x-4 text-sm ml-6 border-l border-gray-600/50 pl-6">
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 bg-gradient-to-r from-emerald-400 to-blue-500 rounded-full flex items-center justify-center">
                <span class="text-white font-bold text-xs">{{ empleado?.nombre?.charAt(0).toUpperCase() }}</span>
              </div>
              <span class="text-gray-300">Hola, <strong class="text-white">{{ empleado?.nombre }}</strong></span>
            </div>
            <button
              @click="logout"
              class="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 px-4 py-2 rounded-lg transition-all duration-200 text-xs font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>

      <!-- Menú móvil desplegable -->
      <div
        v-show="showMobileMenu"
        class="md:hidden border-t border-gray-700/50 bg-gradient-to-r from-gray-900 to-gray-800"
      >
        <div class="flex flex-col space-y-1 px-4 py-4">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center space-x-3 p-3 rounded-lg hover:bg-white/10 transition-all duration-200"
            active-class="bg-emerald-600 font-medium shadow-lg"
            @click="showMobileMenu = false"
          >
            <svg :xmlns="item.xmlns" :class="item.iconClass" :viewBox="item.viewBox" stroke="currentColor" fill="none">
              <path :d="item.iconPath" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
            </svg>
            <span class="font-medium">{{ item.name }}</span>
          </router-link>

          <!-- Control Operativo en móvil -->
          <!-- Producción en móvil -->
          <div class="space-y-1">
            <button
              @click="toggleProduccionDropdown"
              class="flex items-center justify-between w-full p-3 rounded-lg hover:bg-white/10 transition-all duration-200"
              :class="{ 'bg-emerald-600 font-medium shadow-lg': $route.path.startsWith('/reporte-produccion') || $route.path.startsWith('/kpis-choferes') || $route.path.startsWith('/dashboard-detallado') }"
            >
              <div class="flex items-center space-x-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-300" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                  <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                </svg>
                <span class="font-medium">Producción</span>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform duration-200 text-slate-400" :class="{ 'rotate-180': showProduccionDropdown }" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                <path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
            </button>
            <div v-show="showProduccionDropdown" class="ml-6 space-y-1 pl-4 border-l-2 border-emerald-500/30">
              <router-link to="/dashboard-detallado" class="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/10 transition-all duration-200 text-sm" @click="showMobileMenu = false; closeDropdowns()">Dashboard Actual</router-link>
              <router-link to="/reporte-produccion" class="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/10 transition-all duration-200 text-sm" @click="showMobileMenu = false; closeDropdowns()">Reporte de Producción</router-link>
              <router-link to="/kpis-choferes" class="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/10 transition-all duration-200 text-sm" @click="showMobileMenu = false; closeDropdowns()">KPIs Choferes</router-link>
            </div>
          </div>

          <div class="space-y-1">
            <button
              @click="toggleControlOperativoDropdown"
              class="flex items-center justify-between w-full p-3 rounded-lg hover:bg-white/10 transition-all duration-200"
              :class="{ 'bg-emerald-600 font-medium shadow-lg': $route.path === '/maquinas-frente-operador' || $route.path === '/efectividad-servicios' }"
            >
              <div class="flex items-center space-x-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-300" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h.01M9 13h.01M15 13h.01M9 17h.01M15 17h.01" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                </svg>
                <span class="font-medium">Control Operativo</span>
              </div>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform duration-200 text-slate-400" :class="{ 'rotate-180': showControlOperativoDropdown }" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                <path d="M19 9l-7 7-7-7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
            </button>
            
            <!-- Submenú móvil -->
            <div v-show="showControlOperativoDropdown" class="ml-6 space-y-1 pl-4 border-l-2 border-emerald-500/30">
              <router-link
                v-for="subItem in controlOperativoSubmenu"
                :key="subItem.path"
                :to="subItem.path"
                class="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/10 transition-all duration-200 text-sm"
                active-class="bg-emerald-600 font-medium shadow-lg"
                @click="showMobileMenu = false; closeDropdowns()"
              >
                <div class="p-1 rounded-md bg-gray-700">
                  <svg :xmlns="subItem.xmlns" class="h-4 w-4 text-slate-300" :viewBox="subItem.viewBox" stroke="currentColor" fill="none">
                    <path :d="subItem.iconPath" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                  </svg>
                </div>
                <span class="font-medium">{{ subItem.name }}</span>
              </router-link>
            </div>
          </div>

          <!-- Bienvenida y Cerrar sesión (móvil) -->
          <div class="pt-4 mt-4 border-t border-gray-700/50">
            <div class="flex items-center space-x-3 mb-4 p-3 bg-white/5 rounded-lg">
              <div class="w-10 h-10 bg-gradient-to-r from-emerald-400 to-blue-500 rounded-full flex items-center justify-center">
                <span class="text-white font-bold text-sm">{{ empleado?.nombre?.charAt(0).toUpperCase() }}</span>
              </div>
              <div>
                <p class="text-gray-300 text-sm">Bienvenido</p>
                <p class="text-white font-medium">{{ empleado?.nombre }}</p>
              </div>
            </div>
            <button
              @click="logout"
              class="w-full bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 px-4 py-3 rounded-lg text-sm font-medium shadow-lg transition-all duration-200"
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
const showControlOperativoDropdown = ref(false)
const showProduccionDropdown = ref(false)
const empleado = ref(JSON.parse(localStorage.getItem('empleado')))

// Definición del menú con íconos (usando Heroicons)
const menuItems = [
  {
    name: 'Producción Ejecutiva',
    path: '/dashboard',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-5 w-5 text-slate-300',
    iconPath: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
  },
  {
    name: 'Dashboard Actual',
    path: '/dashboard-detallado',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-5 w-5 text-slate-300',
    iconPath: 'M3 7h18M3 12h18M3 17h18'
  },
  {
    name: 'Resumen',
    path: '/resumen-operacional',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-5 w-5 text-slate-300',
    iconPath: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-1.618a1 1 0 00-.67.253l-2.322 1.68A1 1 0 019 17z'
  },
  {
  name: 'Combustible',
  path: '/resumen-combustible',
  xmlns: 'http://www.w3.org/2000/svg',
  viewBox: '0 0 24 24',
  iconClass: 'h-5 w-5 text-slate-300',
  iconPath: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.676-2.154-1.415-3.414l5-5A2 2 0 009 10.172V5L8 4z'
  },{
  name: 'Produccion',
  path: '/reporte-produccion',
  xmlns: 'http://www.w3.org/2000/svg',
  viewBox: '0 0 24 24',
  iconClass: 'h-5 w-5 text-slate-300',
  iconPath: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2z'
},{
  name: 'No Operativas',
  path: '/horas-no-operativas',
  xmlns: 'http://www.w3.org/2000/svg',
  viewBox: '0 0 24 24',
  iconClass: 'h-5 w-5 text-slate-300',
  iconPath: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
}
]

// Submenú para Control Operativo
const controlOperativoSubmenu = [
  {
    name: 'Máquinas por Frente',
    path: '/maquinas-frente-operador',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-4 w-4 text-cyan-300',
    iconPath: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h.01M9 13h.01M15 13h.01M9 17h.01M15 17h.01'
  },
  {
    name: 'Efectividad Servicios',
    path: '/efectividad-servicios',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-4 w-4 text-cyan-300',
    iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
  },
  {
    name: 'Resumen Máquinas',
    path: '/resumen-maquinas-componentes',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-4 w-4 text-cyan-300',
    iconPath: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z'
  },
  {
    name: 'KPIs Mantenimiento',
    path: '/mantenimiento-kpis',
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    iconClass: 'h-4 w-4 text-cyan-300',
    iconPath: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
  }
]

const toggleMobileMenu = () => {
  showMobileMenu.value = !showMobileMenu.value
}

const toggleControlOperativoDropdown = () => {
  showControlOperativoDropdown.value = !showControlOperativoDropdown.value
}

const toggleProduccionDropdown = () => {
  showProduccionDropdown.value = !showProduccionDropdown.value
}

const closeDropdowns = () => {
  showControlOperativoDropdown.value = false
  showProduccionDropdown.value = false
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('empleado')
  showMobileMenu.value = false
  router.push('/')
}
</script>