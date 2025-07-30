<!-- src/components/ProduccionList.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const registros = ref([])
const loading = ref(false)

// Filtros
const filters = ref({
  start_date: '',
  end_date: '',
  un: '',
  operador: '',
  patente: '',
  equipo: ''
})

const fetchProduccion = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/produccion-dashboard/', { params: filters.value })
    registros.value = response.data.results
  } catch (error) {
    console.error('Error al cargar producción:', error)
  } finally {
    loading.value = false
  }
}

// Cargar al inicio
onMounted(() => {
  // Fecha por defecto: últimos 7 días
  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 7)
  
  filters.value.start_date = from.toISOString().split('T')[0]
  filters.value.end_date = today.toISOString().split('T')[0]

  fetchProduccion()
})
</script>

<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <!-- Filtros -->
    <div class="bg-white shadow-md rounded-lg p-4 sm:p-6 mb-6">
      <h3 class="text-lg font-medium text-gray-800 mb-4">Filtros</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Fecha desde -->
        <div class="filter-group">
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha desde</label>
          <input v-model="filters.start_date" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <!-- Fecha hasta -->
        <div class="filter-group">
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha hasta</label>
          <input v-model="filters.end_date" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <!-- UN -->
        <div class="filter-group">
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad (UN)</label>
          <input v-model="filters.un" placeholder="Ej: Minería" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <!-- Operador -->
        <div class="filter-group">
          <label class="block text-sm font-medium text-gray-700 mb-1">Operador</label>
          <input v-model="filters.operador" placeholder="Nombre" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <!-- Patente -->
        <div class="filter-group">
          <label class="block text-sm font-medium text-gray-700 mb-1">Patente equipo</label>
          <input v-model="filters.patente" placeholder="AB1234" class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
        </div>
      </div>
      <div class="mt-4">
        <button @click="fetchProduccion" :disabled="loading" class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md transition">
          {{ loading ? 'Cargando...' : 'Buscar' }}
        </button>
      </div>
    </div>

    <!-- Tabla de resultados -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UN</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Operador</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Equipo</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patente</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tn Despachadas</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="r in registros" :key="r.id" class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ r.fecha }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ r.UN }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ r.operador }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ r.equipo_detalle }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ r.equipo_patente }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ r.tn_despachadas }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ (r.hr_fin - r.hr_inicio).toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="flex justify-center items-center py-6">
        <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="ml-2 text-gray-600">Cargando datos...</span>
      </div>
      <div v-if="!loading && registros.length === 0" class="text-center py-6 text-gray-500">
        No se encontraron registros.
      </div>
    </div>
  </div>
</template>
