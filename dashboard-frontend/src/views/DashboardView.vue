<!-- src/views/DashboardView.vue -->
<template>
  <div class="flex flex-col h-screen bg-gray-50">
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
        <form @submit.prevent="fetchProduccion" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha desde</label>
            <input
              v-model="filters.start_date"
              type="date"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha hasta</label>
            <input
              v-model="filters.end_date"
              type="date"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Unidad de Negocio</label>
            <select v-model="filters.cod_un" @change="cargarFiltros"
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm">
              <option value="">Todas</option>
              <option v-for="un in unidades" :key="un.id" :value="un.id">
                {{ un.nombre }}
              </option>
            </select>
          </div>
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
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Acta</label>
            <select
              v-model="filters.acta"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
            >
              <option value="">Todos</option>
              <option v-for="ac in actas" :key="ac" :value="ac">{{ ac }}</option>
            </select>
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-2 rounded-md transition-colors duration-200"
          >
            {{ loading ? 'Cargando...' : 'Buscar' }}
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
          class="mb-4 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros
        </button>

        <!-- KPIs -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-6 mb-6">
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up">
            <div class="inline-flex p-2 bg-blue-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Producción Total</h3>
            <p class="text-xl md:text-2xl font-bold text-blue-700">{{ formatNumber(totalProduccion) }}</p>
            <p class="text-xs text-gray-500 mt-1">
              <span :class="colorCumplimiento">{{ iconoCumplimiento }} {{ formatNumber(produccionEsperada) }}</span>
            </p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up" style="animation-delay: 100ms">
            <div class="inline-flex p-2 bg-purple-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Total de Horas</h3>
            <p class="text-xl md:text-2xl font-bold text-orange-700">{{ formatNumber(totalHoras) }} Hrs</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up" style="animation-delay: 100ms">
            <div class="inline-flex p-2 bg-orange-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Combustible Total</h3>
            <p class="text-xl md:text-2xl font-bold text-orange-700">{{ formatNumber(totalCombustible) }} L</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up" style="animation-delay: 200ms">
            <div class="inline-flex p-2 bg-green-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-8 8" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Eficiencia</h3>
            <p class="text-xl md:text-2xl font-bold text-green-700">{{ eficiencia }} prod/L</p>
            <p class="text-xs text-gray-500 mt-1">producción / combustible</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up" style="animation-delay: 300ms">
            <div class="inline-flex p-2 bg-red-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Horas No Operativas</h3>
            <p class="text-xl md:text-2xl font-bold text-red-700">{{ formatNumber(totalHrsNoOperativas) }} h</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up" style="animation-delay: 400ms">
            <div class="inline-flex p-2 bg-amber-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Consumo por Hora</h3>
            <p class="text-xl md:text-2xl font-bold text-amber-700">{{ consumoPorHora }} L/h</p>
            <p class="text-xs text-gray-500 mt-1">litros por hora trabajada</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-300 text-center transform hover:-translate-y-1 transition-transform duration-300 animate-fade-in-up" style="animation-delay: 500ms">
            <div class="inline-flex p-2 bg-red-100 rounded-lg mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0v10l-8 4-8-4V7" />
              </svg>
            </div>
            <h3 class="text-sm font-medium text-gray-500 mb-1">Stock ABC</h3>
            <p class="text-xl md:text-2xl font-bold text-red-700">{{ formatNumber(totalStockABC) }} TN</p>
          </div>
        </div>

        <!-- Gráfico Producción y Horas -->
        <div class="bg-white p-6 rounded-lg shadow mb-6">
          <h2 class="text-xl font-semibold mb-4">Producción y Horas Trabajadas por Día</h2>
          <BarChart
            :chart-data="chartDataProduccionHoras"
            :options="chartOptionsProduccionHoras"
          />
        </div>
        
        <!-- Gráfico: Acumulado Real vs Esperado -->
        <div class="bg-white p-6 rounded-lg shadow mb-6">
          <h2 class="text-xl font-semibold mb-4">Avance Acumulado: Real vs Esperado</h2>
          <BarChart
            :chart-data="chartDataAcumulado"
            :options="chartOptionsAcumulado"
          />
        </div>
        
        <!-- Otros gráficos -->
        <div class="bg-white p-6 rounded-lg shadow mb-6">
          <h2 class="text-xl font-semibold mb-4">Combustible por Día (L)</h2>
          <BarChart :chart-data="chartDataCombustible" />
        </div>
        <div class="bg-white p-6 rounded-lg shadow mb-6">
          <h2 class="text-xl font-semibold mb-4">Combustible vs. Horas Trabajadas</h2>
          <BarChart
            :chart-data="chartDataConsumoHora"
            :options="chartOptionsConsumoHora"
          />
        </div>

        <!-- Tabla -->
        <div class="bg-white shadow rounded-lg overflow-hidden">
          <!-- Botón Exportar a Excel -->
          <div class="flex justify-end mb-4">
            <button
              @click="exportarRegistrosAExcel"
              class="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-md shadow-sm transition flex items-center gap-2"
            >
              <i class="fas fa-file-excel"></i>
              Exportar a Excel
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-100">
                <tr>
                  <!-- Fecha -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('fecha')"
                  >
                    Fecha
                    <template v-if="ordenarPor === 'fecha'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-green-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Hr Inicio</th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Hr Fin</th>

                  <!-- Operación -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('operacion')"
                  >
                    Operacion
                    <template v-if="ordenarPor === 'operacion'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-green-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">UN Prod</th>
                  
                  <!-- UN -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('un')"
                  >
                    UN
                    <template v-if="ordenarPor === 'un'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-green-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>

                  <!-- Equipo -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('equipo')"
                  >
                    Equipo
                    <template v-if="ordenarPor === 'equipo'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-green-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>
                  <!-- Produccion -->
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Produccion</th>

                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="r in cargasParaTabla" :key="r.id" class="hover:bg-blue-50 even:bg-gray-50">
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.fecha }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.hr_inicio }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.hr_fin }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.operacion }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.unidad_produccion }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.UN }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.equipo_detalle }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.produccion }}</td>
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
import * as XLSX from 'xlsx'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'

const produccionEsperada = ref(0)
const totalCombustible = ref(0)
const produccionEsperadaPorDia = ref({})
const empleado = ref(null)
const router = useRouter()
const ordenarPor = ref('') // campo por el que se ordena: 'fecha', 'equipo', 'un', 'operacion'
const ordenAsc = ref(true) // true = ascendente, false = descendente

const filters = ref({
  start_date: '',
  end_date: '',
  cod_un: '',  // ✅ ID, no nombre
  operacion: '',
  detalle_equipo: '',
  operador: '',
  acta: ''
})

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
  if (registros.value.length === 0) return 0
  const fechaMaxima = registros.value.reduce((max, r) => (r.fecha > max ? r.fecha : max), '')
  return registros.value
    .filter(r => r.fecha === fechaMaxima)
    .reduce((sum, r) => sum + (parseFloat(r.stock_abc) || 0), 0)
})
const totalHrsNoOperativas = computed(() => {
  return registros.value.reduce((sum, r) => sum + parseFloat(r.hrs_no_operativas || 0), 0)
})
// const totalCombustible = computed(() => {
//   return registros.value.reduce((sum, r) => sum + parseFloat(r.combustible || 0), 0)
// })
const totalHoras = computed(() => {
  return registros.value.reduce((sum, r) => {
    const inicio = parseFloat(r.hr_inicio || 0)
    const fin = parseFloat(r.hr_fin || 0)
    return sum + Math.max(0, fin - inicio)
  }, 0)
})
const eficiencia = computed(() => {
  const prod = totalProduccion.value
  const comb = totalCombustible.value
  return comb > 0 ? (prod / comb).toFixed(2) : 0
})
const consumoPorHora = computed(() => {
  return totalHoras.value > 0 ? (totalCombustible.value / totalHoras.value).toFixed(2) : 0
})

// Cumplimiento global
const cumplimiento = computed(() => {
  const real = totalProduccion.value
  const esperada = produccionEsperada.value
  if (real > esperada * 1.05) return 'superior'
  if (real < esperada * 0.95) return 'inferior'
  return 'normal'
})
const colorCumplimiento = computed(() => {
  return { superior: 'text-green-600', inferior: 'text-red-600', normal: 'text-yellow-600' }[cumplimiento.value]
})
const iconoCumplimiento = computed(() => {
  const estado = cumplimiento.value
  if (estado === 'superior') return '↑'
  if (estado === 'inferior') return '↓'
  return '–'
})

const chartDataAcumulado = computed(() => {
  const data = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!data[fecha]) {
      data[fecha] = { produccion: 0 }
    }
    data[fecha].produccion += parseFloat(r.produccion || 0)
  })

  const labels = Object.keys(data).sort()

  // Producción real diaria
  const produccionReal = labels.map(fecha => data[fecha].produccion)

  // Producción esperada diaria (del backend)
  const produccionEsperadaData = labels.map(fecha => produccionEsperadaPorDia.value[fecha] || 0)

  // Acumulados
  let acumuladoReal = 0
  let acumuladoEsperado = 0
  const acumuladoRealData = []
  const acumuladoEsperadoData = []

  labels.forEach((fecha, index) => {
    acumuladoReal += produccionReal[index]
    acumuladoEsperado += produccionEsperadaData[index]
    acumuladoRealData.push(acumuladoReal)
    acumuladoEsperadoData.push(acumuladoEsperado)
  })

  return {
    labels,
    datasets: [
      {
        label: 'Acumulado Real',
        data: acumuladoRealData,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: 'rgba(75, 192, 192, 1)',
        pointRadius: 4,
        type: 'line'
      },
      {
        label: 'Acumulado Esperado',
        data: acumuladoEsperadoData,
        borderColor: 'rgba(255, 159, 64, 1)',
        backgroundColor: 'rgba(255, 159, 64, 0.1)',
        borderWidth: 3,
        borderDash: [6, 4],
        fill: false,
        tension: 0.3,
        pointBackgroundColor: 'rgba(255, 159, 64, 1)',
        pointRadius: 4,
        type: 'line'
      }
    ]
  }
})

const chartOptionsAcumulado = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    tooltip: {
      callbacks: {
        afterLabel: (tooltipItem) => {
          const dataIndex = tooltipItem.dataIndex
          const real = chartDataAcumulado.value.datasets[0].data[dataIndex]
          const esperado = chartDataAcumulado.value.datasets[1].data[dataIndex]
          const porcentaje = esperado > 0 ? ((real / esperado) * 100).toFixed(1) : 0
          return `→ Cumplimiento: ${porcentaje}%`
        }
      }
    }
  },
  scales: {
    y: {
      type: 'linear',
      display: true,
      title: {
        display: true,
        text: 'Producción Acumulada (TN)'
      }
    },
    x: {
      title: {
        display: true,
        text: 'Fecha'
      }
    }
  }
}

// Gráfico Producción y Horas
const chartDataProduccionHoras = computed(() => {
  const data = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!data[fecha]) data[fecha] = { produccion: 0, horas: 0 }
    data[fecha].produccion += parseFloat(r.produccion || 0)
    const horas = Math.max(0, parseFloat(r.hr_fin || 0) - parseFloat(r.hr_inicio || 0))
    data[fecha].horas += horas
  })

  const labels = Object.keys(data).sort()
  const produccionReal = labels.map(fecha => data[fecha].produccion)
  
  const produccionEsperadaData = labels.map(fecha => produccionEsperadaPorDia.value[fecha] || 0)
  const horasData = labels.map(fecha => data[fecha].horas)

  return {
    labels,
    datasets: [
      {
        label: 'Producción Esperada',
        data: produccionEsperadaData,
        backgroundColor: 'rgba(255, 193, 7, 0.6)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y',
        order: 1
      },
      {
        label: 'Producción Real',
        data: produccionReal,
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y',
        order: 2
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

const chartOptionsProduccionHoras = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    tooltip: {
      callbacks: {
        afterLabel: (tooltipItem) => {
          const fecha = tooltipItem.label
          const real = tooltipItem.dataset.data[tooltipItem.dataIndex]
          const esperado = chartDataProduccionHoras.value.datasets[0].data[tooltipItem.dataIndex]
          if (tooltipItem.dataset.label === 'Producción Real' && esperado > 0) {
            const porcentaje = ((real / esperado) * 100).toFixed(1)
            return `→ Cumplimiento: ${porcentaje}%`
          }
          return ''
        }
      }
    }
  },
  scales: {
    y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Producción (TN)' } },
    y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Horas trabajadas' }, grid: { drawOnChartArea: false } }
  }
}

// Otros gráficos
const chartDataCombustible = computed(() => {
  const data = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    data[fecha] = (data[fecha] || 0) + parseFloat(r.combustible || 0)
  })
  return {
    labels: Object.keys(data),
    datasets: [{ label: 'Combustible (L)', data: Object.values(data), backgroundColor: 'rgba(135, 206, 250, 0.6)', borderColor: 'rgba(30, 144, 255, 1)', borderWidth: 1 }]
  }
})

const chartDataConsumoHora = computed(() => {
  const dataPorFecha = {}
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!dataPorFecha[fecha]) dataPorFecha[fecha] = { combustible: 0, horas: 0 }
    dataPorFecha[fecha].combustible += parseFloat(r.combustible || 0)
    dataPorFecha[fecha].horas += Math.max(0, parseFloat(r.hr_fin || 0) - parseFloat(r.hr_inicio || 0))
  })
  const fechas = Object.keys(dataPorFecha).sort()
  return {
    labels: fechas,
    datasets: [
      { label: 'Combustible (L)', data: fechas.map(f => dataPorFecha[f].combustible), backgroundColor: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgba(255, 99, 132, 1)', borderWidth: 1, yAxisID: 'y' },
      { label: 'Horas Trabajadas', data: fechas.map(f => dataPorFecha[f].horas), backgroundColor: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgba(54, 162, 235, 1)', borderWidth: 1, yAxisID: 'y1' }
    ]
  }
})

const chartOptionsConsumoHora = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  scales: {
    y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Litros de combustible' } },
    y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Horas trabajadas' }, grid: { drawOnChartArea: false } }
  }
}

// Cargar filtros
const cargarFiltros = async () => {
  if (!filters.value.start_date || !filters.value.end_date) return
  loadingFiltros.value = true
  try {
    const params = { ...filters.value }
    if (!params.un) delete params.un
    const response = await api.get('/api/filtros/', { params })
    unidades.value = response.data.unidades || []
    operaciones.value = response.data.operaciones || []
    equipos.value = response.data.equipos || []
    operadores.value = response.data.operadores || []
    actas.value = response.data.actas || []
  } catch (error) {
    console.error('Error al cargar filtros:', error)
  } finally {
    loadingFiltros.value = false
  }
}

// Cargar producción
const fetchProduccion = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/produccion-dashboard/', { params: filters.value })
    registros.value = response.data.results || []
    produccionEsperada.value = response.data.produccion_esperada_acumulada || 0
    produccionEsperadaPorDia.value = response.data.produccion_esperada_por_dia || {}
    totalCombustible.value = response.data.consumo_combustible_total || 0
    showSidebar.value = false
  } catch (error) {
    console.error('Error al cargar producción:', error)
  } finally {
    loading.value = false
  }
}

// Observar cambios en fechas
watch(() => [filters.value.start_date, filters.value.end_date], () => {
  if (filters.value.start_date && filters.value.end_date) cargarFiltros()
})

// Logout
const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('empleado')
  router.push('/')
}

// Formatear números
const formatNumber = (num) => {
  const n = isNaN(parseFloat(num)) ? 0 : parseFloat(num)
  return n.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
}

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

const exportarRegistrosAExcel = () => {
  // Mapea los registros al formato deseado
  const datos = cargasParaTabla.value.map(r => ({
    'Fecha': r.fecha,
    'Hora Inicio': r.hr_inicio,
    'Hora Fin': r.hr_fin,
    'Operación': r.operacion,
    'Unidad de Producción': r.unidad_produccion,
    'Unidad de Negocio': r.UN,
    'Equipo': r.equipo_detalle,
    'Producción': r.produccion
  }))

  // Crear hoja de cálculo
  const ws = XLSX.utils.json_to_sheet(datos)

  // Ajustar ancho de columnas
  ws['!cols'] = [
    { wch: 12 }, // Fecha
    { wch: 15 }, // Hora Inicio
    { wch: 15 }, // Hora Fin
    { wch: 15 }, // Operación
    { wch: 15 }, // Unidad de Producción
    { wch: 20 }, // Unidad de Negocio
    { wch: 25 }, // Equipo
    { wch: 15 }  // Producción
  ]

  // Crear libro
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Registros de Producción')

  // Descargar archivo
  XLSX.writeFile(wb, `Registros_Produccion_${new Date().toISOString().slice(0,10)}.xlsx`)
}

const cargasParaTabla = computed(() => {
  let arr = [...registros.value]

  if (!ordenarPor.value) return arr

  arr.sort((a, b) => {
    let valA, valB

    switch (ordenarPor.value) {
      case 'fecha':
        valA = a.fecha
        valB = b.fecha
        break
      case 'equipo':
        valA = a.equipo_detalle?.toLowerCase() || ''
        valB = b.equipo_detalle?.toLowerCase() || ''
        break
      case 'un':
        valA = a.UN?.toLowerCase() || ''
        valB = b.UN?.toLowerCase() || ''
        break
      case 'operacion':
        valA = a.operacion?.toLowerCase() || ''
        valB = b.operacion?.toLowerCase() || ''
        break
      default:
        return 0
    }

    if (valA < valB) return ordenAsc.value ? -1 : 1
    if (valA > valB) return ordenAsc.value ? 1 : -1
    return 0
  })

  return arr
})

const cambiarOrden = (campo) => {
  if (ordenarPor.value === campo) {
    // Si ya está ordenado por este campo, cambia dirección
    ordenAsc.value = !ordenAsc.value
  } else {
    // Nuevo campo: orden ascendente por defecto
    ordenarPor.value = campo
    ordenAsc.value = true
  }
}
</script>

<style>
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fade-in-up 0.5s ease-out forwards; }
</style>