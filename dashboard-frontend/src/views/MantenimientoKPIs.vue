<template>
  <div class="flex flex-col h-screen bg-primary-50 font-sans">
    <!-- Main -->
    <main class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <aside
        class="w-80 bg-white shadow-xl border-r border-gray-100 p-6 overflow-y-auto transform transition-transform duration-300 ease-in-out z-40
                fixed top-0 left-0 bottom-0
                sm:static sm:translate-x-0 sm:shadow-none sm:border-r sm:block"
        :class="{
          '-translate-x-full': isMobile && !showSidebar,
          'translate-x-0': isMobile && showSidebar
        }"
      >
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-semibold text-gray-800">🎛️ Filtros</h3>
          <button
            v-if="isMobile"
            @click="showSidebar = false"
            class="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            ✕
          </button>
        </div>
        <form @submit.prevent="fetchKPIs" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha desde</label>
            <input
              v-model="filters.fecha_inicio"
              type="date"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha hasta</label>
            <input
              v-model="filters.fecha_fin"
              type="date"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Unidad de Negocio</label>
            <select 
              v-model="filters.unidad_negocio" 
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Todas</option>
              <option v-for="un in unidades" :key="un.id" :value="un.id">
                {{ un.nombre }}
              </option>
            </select>
          </div>
          
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300 text-white font-semibold py-2 rounded-md transition-colors duration-200"
          >
            {{ loading ? 'Cargando...' : 'Calcular KPIs' }}
          </button>
        </form>
      </aside>

      <!-- Overlay móvil -->
      <div
        v-if="isMobile && showSidebar"
        @click="showSidebar = false"
        class="fixed inset-0 bg-black bg-opacity-50 z-10 lg:hidden"
      ></div>

      <!-- Contenido principal -->
      <section class="flex-1 p-6 overflow-y-auto">
        <!-- Botón filtros móvil -->
        <button
          v-if="isMobile"
          @click="showSidebar = true"
          class="mb-4 bg-primary-800 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros
        </button>

        <h2 class="text-2xl font-bold text-gray-800 mb-6">KPIs de Mantenimiento</h2>

        <!-- KPIs -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">

          <!-- MTBF -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up">
            <div class="inline-flex p-2 bg-blue-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">MTBF (Tiempo Medio Entre Fallas)</h3>
            <p class="text-xl font-bold text-blue-700">{{ kpis.mtbf }} horas</p>
            <p class="text-xs text-gray-500 mt-1">Intervalo promedio entre fallas correctivas</p>
          </div>

          <!-- MTTR -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 100ms">
            <div class="inline-flex p-2 bg-yellow-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">MTTR (Tiempo Medio de Reparación)</h3>
            <p class="text-xl font-bold text-yellow-700">{{ kpis.mttr }} horas</p>
            <p class="text-xs text-gray-500 mt-1">Tiempo promedio para reparar una avería</p>
          </div>

          <!-- Downtime -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 200ms">
            <div class="inline-flex p-2 bg-red-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Downtime (Tiempo de Inactividad)</h3>
            <p class="text-xl font-bold text-red-700">{{ kpis.downtime }} horas</p>
            <p class="text-xs text-gray-500 mt-1">Total de horas perdidas por fallas</p>
          </div>

          <!-- Disponibilidad Global -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 300ms">
            <div class="inline-flex p-2 bg-green-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Disponibilidad Global</h3>
            <p class="text-xl font-bold text-green-700">{{ kpis.disponibilidad_global }}%</p>
            <p class="text-xs text-gray-500 mt-1">Porcentaje de tiempo operativo</p>
          </div>

        </div>

        <!-- Detalles adicionales -->
        <div class="bg-white shadow rounded-lg p-6 mb-6">
          <h3 class="text-lg font-semibold mb-4">Detalles del Cálculo</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div class="flex justify-between border-b py-2">
              <span class="text-gray-600">Cantidad de Fallas Correctivas:</span>
              <span class="font-medium">{{ kpis.cantidad_fallas }}</span>
            </div>
            <div class="flex justify-between border-b py-2">
              <span class="text-gray-600">Equipos Analizados:</span>
              <span class="font-medium">{{ kpis.equipos_analizados }}</span>
            </div>
            <div class="flex justify-between border-b py-2">
              <span class="text-gray-600">Total Horas Trabajadas:</span>
              <span class="font-medium">{{ kpis.total_horas_trabajadas }} h</span>
            </div>
          </div>
        </div>

        <!-- Tabla de KPIs por Equipo -->
        <div v-if="kpis.equipos && kpis.equipos.length > 0" class="bg-white shadow rounded-lg overflow-hidden">
          <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h3 class="text-lg font-semibold text-gray-800">KPIs por Equipo</h3>
            <p class="text-sm text-gray-600 mt-1">Detalle de indicadores de mantenimiento para cada equipo</p>
          </div>
          
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-100">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Equipo
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unidad de Negocio
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Horas Trabajadas
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    MTBF (h)
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    MTTR (h)
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Downtime (h)
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Disponibilidad
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fallas
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="equipo in kpis.equipos" :key="equipo.equipo_id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ equipo.equipo_nombre }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {{ equipo.unidad_negocio }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-700">
                    <span class="font-semibold">{{ equipo.horas_trabajadas }}</span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-700">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {{ equipo.mtbf }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-700">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      {{ equipo.mttr }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-700">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      {{ equipo.downtime }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-700">
                    <div class="flex items-center justify-center">
                      <div class="w-full max-w-xs">
                        <div class="flex items-center">
                          <div class="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              class="h-2 rounded-full transition-all duration-300"
                              :class="equipo.disponibilidad >= 90 ? 'bg-green-500' : equipo.disponibilidad >= 75 ? 'bg-yellow-500' : 'bg-red-500'"
                              :style="`width: ${equipo.disponibilidad}%`"
                            ></div>
                          </div>
                          <span class="text-xs font-semibold">{{ equipo.disponibilidad }}%</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-700">
                    <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-800 font-semibold">
                      {{ equipo.cantidad_fallas }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Mensaje cuando no hay datos por equipo -->
        <div v-else-if="!loading && filters.unidad_negocio" class="bg-white shadow rounded-lg p-6">
          <div class="text-center text-gray-500">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-lg font-medium">No hay datos disponibles</p>
            <p class="text-sm mt-1">No se encontraron fallas correctivas para los equipos en el período seleccionado</p>
          </div>
        </div>

      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'

const filters = ref({
  fecha_inicio: '',
  fecha_fin: '',
  unidad_negocio: ''
})

const unidades = ref([])
const kpis = ref({
  mtbf: 0,
  mttr: 0,
  downtime: 0,
  cantidad_fallas: 0,
  equipos_analizados: 0,
  total_horas_trabajadas: 0,
  disponibilidad_global: 0,
  equipos: []
})

const loading = ref(false)
const showSidebar = ref(false)
const isMobile = computed(() => window.innerWidth < 1024)

const fetchUnidades = async () => {
  try {
    // El endpoint de filtros requiere fechas, enviamos las que ya están configuradas
    const params = {
      start_date: filters.value.fecha_inicio,
      end_date: filters.value.fecha_fin
    }
    const response = await api.get('/api/filtros/', { params })
    unidades.value = response.data.unidades || []
  } catch (error) {
    console.error('Error al cargar unidades:', error)
  }
}

const fetchKPIs = async () => {
  if (!filters.value.fecha_inicio || !filters.value.fecha_fin) {
    alert('Por favor seleccione un rango de fechas')
    return
  }
  
  loading.value = true
  try {
    const response = await api.get('/api/mantenimiento/kpis-mantenimiento/', { params: filters.value })
    kpis.value = response.data
    showSidebar.value = false
  } catch (error) {
    console.error('Error al calcular KPIs:', error)
    alert('Error al calcular KPIs')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 30)
  filters.value.fecha_inicio = from.toISOString().split('T')[0]
  filters.value.fecha_fin = today.toISOString().split('T')[0]
  
  // Cargar unidades después de configurar las fechas
  fetchUnidades()
  fetchKPIs()
})
</script>

<style scoped>
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fade-in-up 0.5s ease-out forwards; }
</style>
