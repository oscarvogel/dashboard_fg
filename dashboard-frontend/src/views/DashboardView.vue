<!-- src/views/DashboardView.vue -->
<template>
  <div class="flex flex-col h-screen bg-gray-50">

    <!-- Main -->
    <main class="flex flex-1 overflow-hidden">
              <!-- Backdrop para mobile -->
        <div
          v-if="isMobile && showSidebar"
          @click="showSidebar = false"
          class="fixed inset-0 bg-black bg-opacity-40 z-30 transition-opacity duration-300"
        ></div>

        <!-- Sidebar/modal -->
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
            <!-- Botón cerrar solo en mobile -->
            <button
              v-if="isMobile"
              @click="showSidebar = false"
              class="text-gray-500 hover:text-gray-700 focus:outline-none"
            >
              ✕
            </button>
          </div>

          <form @submit.prevent="fetchProduccion" class="space-y-6">
            <!-- Fecha desde -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Fecha desde</label>
              <input
                v-model="filters.start_date"
                type="date"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              />
            </div>

            <!-- Fecha hasta -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Fecha hasta</label>
              <input
                v-model="filters.end_date"
                type="date"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              />
            </div>

            <!-- UN -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Unidad de Negocio</label>
              <select
                v-model="filters.un"
                @change="cargarFiltros"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              >
                <option value="">Todas</option>
                <option v-for="un in unidades" :key="un" :value="un">{{ un }}</option>
              </select>
            </div>

            <!-- Operación -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Operación</label>
              <select
                v-model="filters.operacion"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              >
                <option value="">Todas</option>
                <option v-for="op in operaciones" :key="op" :value="op">{{ op }}</option>
              </select>
            </div>

            <!-- Operador -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Operador</label>
              <select
                v-model="filters.operador"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              >
                <option value="">Todos</option>
                <option v-for="op in operadores" :key="op" :value="op">{{ op }}</option>
              </select>
              <div v-if="loadingFiltros" class="text-xs text-blue-500 mt-1 animate-pulse">Cargando operadores...</div>
            </div>

            <!-- Equipo -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Equipo</label>
              <select
                v-model="filters.detalle_equipo"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              >
                <option value="">Todos</option>
                <option v-for="eq in equipos" :key="eq" :value="eq">{{ eq }}</option>
              </select>
            </div>
            
            <!-- Actas -->
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Equipo</label>
              <select
                v-model="filters.acta"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
              >
                <option value="">Todos</option>
                <option v-for="ac in actas" :key="ac" :value="ac">{{ ac }}</option>
              </select>
            </div>

            <!-- Botón -->
            <button
              type="submit"
              :disabled="loading"
              class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-2 rounded-md transition-colors duration-200"
            >
              {{ loading ? 'Cargando...' : 'Buscar' }}
            </button>
          </form>
        </aside>


      <!-- Overlay en móvil -->
      <div
        v-if="isMobile && showSidebar"
        @click="showSidebar = false"
        class="fixed inset-0 bg-black bg-opacity-50 z-10 lg:hidden"
      ></div>

      <!-- Contenido principal -->
      <section class="flex-1 p-6 overflow-y-auto">
        <!-- Botón para abrir sidebar en móvil -->
        <button
          v-if="isMobile"
          @click="showSidebar = true"
          class="mb-4 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros
        </button>

        <!-- KPIs -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 mb-6">
          <!-- Producción Total -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up"
              style="animation-delay: 0ms">
            <div class="inline-flex p-2 bg-blue-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Producción Total</h3>
            <p class="text-xl md:text-2xl font-bold text-blue-700">{{ formatNumber(totalProduccion) }}</p>
            <p class="text-xs text-gray-500 mt-1"> 
              <span :class="colorCumplimiento">{{ iconoCumplimiento }} {{ formatNumber(produccionEsperada) }}</span></p>
          </div>

          <!-- Combustible Total -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up"
              style="animation-delay: 100ms">
            <div class="inline-flex p-2 bg-orange-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Combustible Total</h3>
            <p class="text-xl md:text-2xl font-bold text-orange-700">{{ formatNumber(totalCombustible) }} L</p>
          </div>

          <!-- Eficiencia -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up"
              style="animation-delay: 200ms">
            <div class="inline-flex p-2 bg-green-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-8 8" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Eficiencia</h3>
            <p class="text-xl md:text-2xl font-bold text-green-700">{{ eficiencia }} prod/L</p>
            <p class="text-xs text-gray-500 mt-1">producción / combustible</p>
          </div>

          <!-- Horas No Operativas -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up"
              style="animation-delay: 300ms">
            <div class="inline-flex p-2 bg-red-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Horas No Operativas</h3>
            <p class="text-xl md:text-2xl font-bold text-red-700">{{ formatNumber(totalHrsNoOperativas) }} h</p>
          </div>

          <!-- Consumo por Hora -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up"
              style="animation-delay: 400ms">
            <div class="inline-flex p-2 bg-amber-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Consumo por Hora</h3>
            <p class="text-xl md:text-2xl font-bold text-amber-700">{{ consumoPorHora }} L/h</p>
            <p class="text-xs text-gray-500 mt-1">litros por hora trabajada</p>
          </div>

          <!-- Stock ABC -->
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up"
              style="animation-delay: 500ms">
            <div class="inline-flex p-2 bg-red-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0v10l-8 4-8-4V7" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Stock ABC</h3>
            <p class="text-xl md:text-2xl font-bold text-red-700">{{ formatNumber(totalStockABC) }} TN</p>
          </div>
        </div>
      <!-- Gráfico de Producción (barras) y Horas (línea) -->
      <div class="bg-white p-6 rounded-lg shadow mb-6">
        <h2 class="text-xl font-semibold mb-4">Producción y Horas Trabajadas por Día</h2>
        <BarChart
          :chart-data="chartDataProduccionHoras"
          :options="chartOptionsProduccionHoras"
        />
      </div>
        <!-- Gráfico de combustible -->
      <div class="bg-white p-6 rounded-lg shadow mb-6">
        <h2 class="text-xl font-semibold mb-4">Combustible por Día (L)</h2>
        <BarChart :chart-data="chartDataCombustible" />
      </div>
      <!-- Gráfico: Combustible vs Horas -->
        <div class="bg-white p-6 rounded-lg shadow mb-6">
          <h2 class="text-xl font-semibold mb-4">Combustible vs. Horas Trabajadas</h2>
            <BarChart
              :chart-data="chartDataConsumoHora" 
              :options="chartOptionsConsumoHora" 
            />
        </div>
        <!-- Tabla -->
        <div class="bg-white shadow rounded-lg overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 bg-white shadow-md rounded-lg overflow-hidden">
              <thead class="bg-gray-100">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Fecha</th>
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Operación</th>
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">UN</th>
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Equipo</th>
                  <th class="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Producción</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr
                  v-for="r in registros"
                  :key="r.id"
                  class="transition hover:bg-blue-50 even:bg-gray-50"
                >
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{{ r.fecha }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{{ r.operacion }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{{ r.UN }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{{ r.equipo_detalle }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800">{{ r.produccion }}</td>
                </tr>
              </tbody>
            </table>
          </div>


          <div v-if="loading" class="flex justify-center items-center py-6">
            <svg class="animate-spin h-5 w-5 text-blue-600 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Cargando datos...
          </div>

          <div v-if="!loading && registros.length === 0" class="text-center py-6 text-gray-500">
            No se encontraron registros.
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'
const produccionEsperada = ref(0)

const empleado = ref(null)
const router = useRouter()

// Filtros
const filters = ref({
  start_date: '',
  end_date: '',
  un: '',
  operacion: '',
  detalle_equipo: '',
  operador: '' 
})

// Listas
const operaciones = ref([])
const unidades = ref([])
const equipos = ref([])
const operadores = ref([])
const actas = ref([])

const registros = ref([])
const loading = ref(false)
const loadingFiltros = ref(false)
const showSidebar = ref(false)

const isMobile = computed(() => window.innerWidth < 1024)

// KPIs
const totalProduccion = computed(() => {
  return registros.value.reduce((sum, r) => sum + parseFloat(r.produccion || 0), 0)
})

const totalStockABC = computed(() => {
  if (registros.value.length === 0) return 0;

  // Encontrar la fecha más reciente (máxima)
  const fechaMaxima = registros.value.reduce((maxFecha, registro) => {
    const fechaActual = registro.fecha;
    return fechaActual > maxFecha ? fechaActual : maxFecha;
  }, '');

  // Sumar todos los stock_abc que tengan esa fecha máxima
  return registros.value
    .filter(r => r.fecha === fechaMaxima)
    .reduce((suma, r) => suma + (parseFloat(r.stock_abc) || 0), 0);
});

const totalHrsNoOperativas = computed(() => {
  return registros.value.reduce((sum, r) => sum + parseFloat(r.hrs_no_operativas || 0), 0)
})

const eficiencia = computed(() => {
  const produccionTotal = registros.value.reduce((sum, r) => sum + parseFloat(r.produccion || 0), 0)
  const combustibleTotal = registros.value.reduce((sum, r) => sum + parseFloat(r.combustible || 0), 0)

  if (combustibleTotal === 0) return 0

  return (produccionTotal / combustibleTotal).toFixed(2)
})

const chartDataProduccionHoras = computed(() => {
  const data = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!data[fecha]) {
      data[fecha] = { produccion: 0, horas: 0 }
    }
    data[fecha].produccion += parseFloat(r.produccion || 0)
    const horas = Math.max(0, parseFloat(r.hr_fin || 0) - parseFloat(r.hr_inicio || 0))
    data[fecha].horas += horas
  })

  const labels = Object.keys(data).sort()
  const produccionData = labels.map(fecha => data[fecha].produccion)
  const horasData = labels.map(fecha => data[fecha].horas)

  return {
    labels,
    datasets: [
      {
        label: 'Producción',
        data: produccionData,
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y'
      },
      {
        label: 'Horas Trabajadas',
        data: horasData,
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 2,
        type: 'line',
        fill: false,
        tension: 0.3,
        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
        pointRadius: 4,
        yAxisID: 'y1'
      }
    ]
  }
})

const cumplimiento = computed(() => {
  const real = totalProduccion.value
  const esperada = produccionEsperada.value
  if (real > esperada * 1.05) return 'superior'
  if (real < esperada * 0.95) return 'inferior'
  return 'normal'
})

const colorCumplimiento = computed(() => {
  const estado = cumplimiento.value
  if (estado === 'superior') return 'text-green-600'
  if (estado === 'inferior') return 'text-red-600'
  return 'text-yellow-600'
})

const iconoCumplimiento = computed(() => {
  const estado = cumplimiento.value
  if (estado === 'superior') return '↑'
  if (estado === 'inferior') return '↓'
  return '–'
})

// opciones del grafico de producción y horas
const chartOptionsProduccionHoras = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  scales: {
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: {
        display: true,
        text: 'Producción'
      }
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: {
        display: true,
        text: 'Horas trabajadas'
      },
      grid: {
        drawOnChartArea: false
      }
    }
  }
}


const chartDataCombustible = computed(() => {
  const data = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    data[fecha] = (data[fecha] || 0) + parseFloat(r.combustible || 0)
  })

  return {
    labels: Object.keys(data),
    datasets: [
      {
        label: 'Combustible (L)',
        data: Object.values(data),
        backgroundColor: 'rgba(135, 206, 250, 0.6)',
        borderColor: 'rgba(30, 144, 255, 1)',
        borderWidth: 1
      }
    ]
  }
})
// Total combustible
const totalCombustible = computed(() => {
  return registros.value.reduce((sum, r) => sum + parseFloat(r.combustible || 0), 0)
})

// Total horas trabajadas
const totalHoras = computed(() => {
  return registros.value.reduce((sum, r) => {
    const inicio = parseFloat(r.hr_inicio || 0)
    const fin = parseFloat(r.hr_fin || 0)
    const horas = fin - inicio
    return sum + horas
  }, 0)
})

// Consumo por hora (L/h)
const consumoPorHora = computed(() => {
  if (totalHoras.value === 0) return 0
  return (totalCombustible.value / totalHoras.value).toFixed(2)
})

// Cargar filtros dinámicos
const cargarFiltros = async () => {
  if (!filters.value.start_date || !filters.value.end_date) {
    operaciones.value = []
    equipos.value = []
    operadores.value = []
    actas.value = []
    return
  }

  loadingFiltros.value = true
  try {
    const params = {
      start_date: filters.value.start_date,
      end_date: filters.value.end_date
    }

    // Solo incluir UN si está seleccionada
    if (filters.value.un) {
      params.un = filters.value.un
    }

    const response = await api.get('/api/filtros/', { params })

    // Actualizar listas
    unidades.value = response.data.unidades
    operaciones.value = response.data.operaciones
    equipos.value = response.data.equipos
    operadores.value = response.data.operadores
    actas.value = response.data.actas

    // Limpiar filtros hijos si ya no son válidos
    if (filters.value.operacion && !operaciones.value.includes(filters.value.operacion)) {
      filters.value.operacion = ''
    }
    if (filters.value.detalle_equipo && !equipos.value.includes(filters.value.detalle_equipo)) {
      filters.value.detalle_equipo = ''
    }
    if (filters.value.operador && !operadores.value.includes(filters.value.operador)) {
      filters.value.operador = ''
    }
    if (filters.value.acta && !actas.value.includes(filters.value.acta)) {
      filters.value.acta = ''
    }

  } catch (error) {
    console.error('Error al cargar filtros:', error)
    operaciones.value = []
    equipos.value = []
    operadores.value = []
    actas.value = []
  } finally {
    loadingFiltros.value = false
  }
}

const chartDataConsumoHora = computed(() => {
  const labels = []
  const combustibleData = []
  const horasData = []

  const dataPorFecha = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!dataPorFecha[fecha]) {
      dataPorFecha[fecha] = { combustible: 0, horas: 0 }
    }
    dataPorFecha[fecha].combustible += parseFloat(r.combustible || 0)
    const horas = Math.max(0, parseFloat(r.hr_fin || 0) - parseFloat(r.hr_inicio || 0))
    dataPorFecha[fecha].horas += horas
  })

  const fechas = Object.keys(dataPorFecha).sort().slice(-10)
  fechas.forEach(fecha => {
    labels.push(fecha)
    combustibleData.push(dataPorFecha[fecha].combustible)
    horasData.push(dataPorFecha[fecha].horas)
  })
  console.log('Labels:', labels)
  console.log('Combustible Data:', combustibleData)
  console.log('Horas Data:', horasData)
  return {
    labels,
    datasets: [
      {
        label: 'Combustible (L)',
        data: combustibleData,  // ✅ Corregido
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
        yAxisID: 'y'
      },
      {
        label: 'Horas Trabajadas',
        data: horasData,  // ✅ Corregido
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        yAxisID: 'y1'
      }
    ]
  }
})

const chartOptionsConsumoHora = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  stacked: false,
  scales: {
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: {
        display: true,
        text: 'Litros de combustible'
      }
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: {
        display: true,
        text: 'Horas trabajadas'
      },
      grid: {
        drawOnChartArea: false
      }
    }
  }
}

// Cargar producción
const fetchProduccion = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/produccion-dashboard/', { params: filters.value })
    registros.value = response.data.results
    // ✅ Producción esperada del backend
    produccionEsperada.value = response.data.produccion_esperada_acumulada || 0
    console.log('Producción esperada:', produccionEsperada.value)
    showSidebar.value = false
  } catch (error) {
    console.error('Error al cargar producción:', error)
  } finally {
    loading.value = false
  }
}

// Observar cambios en fechas
watch(
  () => [filters.value.start_date, filters.value.end_date],
  () => {
    if (filters.value.start_date && filters.value.end_date) {
      cargarFiltros()
    }
  },
  { immediate: false }
)

// Logout
const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('empleado')
  router.push('/')
}

// Formatear números
const formatNumber = (num) => {
  // Convertir a número y manejar valores no válidos
  const n = isNaN(parseFloat(num)) ? 0 : parseFloat(num)
  return n.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
}

// Cargar al inicio
onMounted(() => {
  const emp = localStorage.getItem('empleado')
  if (!emp) return router.push('/')
  empleado.value = JSON.parse(emp)

  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 30)
  filters.value.start_date = from.toISOString().split('T')[0]
  filters.value.end_date = today.toISOString().split('T')[0]

  cargarFiltros()
  fetchProduccion()
})
</script>

<style>
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.animate-fade-in-up {
  animation: fade-in-up 0.5s ease-out forwards;
}
</style>