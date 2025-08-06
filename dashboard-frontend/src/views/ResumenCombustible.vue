<!-- src/views/ResumenCombustible.vue -->
<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Botón para mostrar/ocultar filtros en móvil -->
    <div class="md:hidden px-6 pt-4">
      <button
        @click="mostrarFiltros = !mostrarFiltros"
        class="w-full bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-md shadow-sm"
      >
        {{ mostrarFiltros ? 'Ocultar Filtros' : 'Mostrar Filtros' }}
      </button>
    </div>
    <!-- Filtros -->
    <section
      v-show="mostrarFiltros"
      class="bg-white p-6 border-b border-gray-200 md:block"
    >
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
        <!-- Fecha desde -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Desde</label>
          <input
            v-model="filters.start_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            @change="cargarUnidades"
          />
        </div>
        <!-- Fecha hasta -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
          <input
            v-model="filters.end_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            @change="cargarUnidades"
          />
        </div>
        <!-- UN -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
          <select
            v-model="filters.un_id"
            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            @change="cargarEquipos"
          >
            <option value="">Todas</option>
            <option v-for="un in unidades" :key="un.id" :value="un.id">
              {{ un.nombre }}
            </option>
          </select>
        </div>
        <!-- Equipo -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
          <select
            v-model="filters.movil_id"
            class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            :disabled="!filters.un_id"
          >
            <option value="">Todos</option>
            <option v-for="eq in equipos" :key="eq.id" :value="eq.id">
              {{ eq.detalle }} ({{ eq.patente }})
            </option>
          </select>
        </div>
        <!-- Botón buscar -->
        <div class="flex items-end sm:col-span-2 lg:col-span-2">
          <button
            @click="cargarDatos"
            :disabled="loading"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md text-sm transition"
          >
            {{ loading ? 'Cargando...' : 'Buscar' }}
          </button>
        </div>
      </div>
    </section>
    <!-- KPIs Responsivos -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-6 gap-4 px-6 mb-6">
      <!-- Ingreso de Combustible -->
      <!-- En Ingreso -->
      <div class="bg-white p-4 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Ingresos</h3>
        <p class="text-2xl font-bold text-green-600 flex items-center justify-center gap-1">
          <i class="fas fa-arrow-up"></i> {{ redondear(totalLitrosIngreso) }} L
        </p>
      </div>

      <!-- En Egreso -->
      <div class="bg-white p-4 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Egresos</h3>
        <p class="text-2xl font-bold text-red-600 flex items-center justify-center gap-1">
          <i class="fas fa-arrow-down"></i> {{ redondear(totalLitrosEgreso) }} L
        </p>
      </div>
      
      <!-- Balance Neto -->
       <div class="bg-white p-4 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Balance Neto</h3>
        <p class="text-2xl font-bold flex items-center justify-center gap-1" :class="balanceNeto >= 0 ? 'text-green-600' : 'text-red-600'">
          <i :class="balanceNeto >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"></i> {{ redondear(balanceNeto) }} L
        </p>
      </div>
      
      <!-- Total Horas/Km -->
      <div class="bg-white p-4 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Horas/Km Trabajados</h3>
        <p class="text-2xl font-bold text-blue-600">{{ redondear(totalHorasKm) }} h/km</p>
      </div>
      <!-- Consumo Medio -->
      <div class="bg-white p-4 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Consumo Medio</h3>
        <p class="text-2xl font-bold text-green-600">{{ consumoMedioGlobal }} L/h/km</p>
        <p class="text-xs text-gray-500">litros por hora/km</p>
      </div>
      <!-- Número de Cargas -->
      <div class="bg-white p-4 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Cargas Realizadas</h3>
        <p class="text-2xl font-bold text-purple-600">{{ totalCargas }}</p>
      </div>
    </div>
    <!-- Contenido Principal -->
    <main class="flex-1 px-6 pb-6 overflow-y-auto">
      <!-- Gráfico: Litros por día -->
      <div class="bg-white p-6 rounded-lg shadow mb-6">
        <h2 class="text-xl font-semibold mb-4">Litros por Día</h2>
        <div class="h-72"> <!-- Altura fija para gráfico -->
          <BarChart
            :chart-data="chartDataCombustiblePorEquipo"
            :options="chartOptionsCombustiblePorEquipo"
          />
        </div>
      </div>

      <!-- Detalles de Cargas -->
      <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Detalles de Cargas de Combustible</h2>
        <!-- Botón Exportar a Excel -->
      <div class="flex justify-end mb-4">
        <button
          @click="exportarAExcel"
          class="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-md shadow-sm transition flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3M3 17h18M3 12h18M3 7h18" />
          </svg>
          Exportar a Excel
        </button>
      </div>
        <!-- Tabla (solo en escritorio/tablet) -->
        <div class="overflow-x-auto sm:block hidden">
          <table class="min-w-full border-collapse border border-gray-300">
            <thead class="bg-gray-100">
              <tr>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">Fecha</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">Tipo Movimiento</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">KM/Hora</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">Litros</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">Horas Trab.</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">L/h</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">Lugar Carga</th>
                <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold">Equipo</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in cargasConIndicadores"
                :key="c.id"
                class="hover:bg-gray-50 text-sm"
              >
                <td class="border border-gray-300 px-3 py-2 text-center">{{ c.fecha }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ c.tipo_mov_display }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ redondear(parseFloat(c.km)) }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ redondear(parseFloat(c.litros)) }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ redondear(c.horas_trabajadas) }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ redondear(c.consumo_hora) }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ c.lugar_carga_detalle }}</td>
                <td class="border border-gray-300 px-3 py-2 text-center">{{ c.movil_detalle }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Tarjetas (solo en móvil) -->
        <div class="space-y-4 sm:hidden">
          <div
            v-for="c in cargasConIndicadores"
            :key="c.id"
            class="border border-gray-300 rounded-lg p-4 bg-white"
          >
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div><strong>Fecha:</strong> {{ c.fecha }}</div>
              <div><strong>KM/Hora:</strong> {{ redondear(c.km) }}</div>
              <div><strong>Litros:</strong> {{ redondear(c.litros) }}</div>
              <div><strong>Horas:</strong> {{ redondear(c.horas_trabajadas) }}</div>
              <div><strong>L/h:</strong> {{ redondear(c.consumo_hora) }}</div>
              <div><strong>Lugar:</strong> {{ c.lugar_carga_detalle }}</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'
import * as XLSX from 'xlsx'

// Estado para controlar visibilidad de filtros en móvil
const mostrarFiltros = ref(true)
const router = useRouter()

// Filtros
const filters = ref({
  start_date: '',
  end_date: '',
  un_id: '',
  movil_id: ''
})

// Datos
const unidades = ref([])
const equipos = ref([])
const cargas = ref([])
const totalLitrosEgreso = ref(0)
const totalLitrosIngreso = ref(0)
const loading = ref(false)

// Cargar UN
const cargarUnidades = async () => {
  if (!filters.value.start_date || !filters.value.end_date) return
  try {
    const params = {
      start_date: filters.value.start_date,
      end_date: filters.value.end_date
    }
    const response = await api.get('/api/filtros-combustible/', { params })
    unidades.value = response.data.unidades
  } catch (error) {
    console.error('Error al cargar UN:', error)
  }
}

// Cargar equipos por UN
const cargarEquipos = async () => {
  console.log('Cargando equipos para UN:', filters.value.un_id)
  equipos.value = []
  if (!filters.value.un_id) {
    equipos.value = []
    return
  }
  try {
    const params = {
      start_date: filters.value.start_date,
      end_date: filters.value.end_date,
      un_id: filters.value.un_id
    }
    const response = await api.get('/api/equipos-por-un/', { params })
    equipos.value = response.data.equipos
  } catch (error) {
    console.error('Error al cargar equipos:', error)
  }
}

// Datos procesados con indicadores
const cargasConIndicadores = ref([])

// Cargar datos
const cargarDatos = async () => {
  if (!filters.value.start_date || !filters.value.end_date) return
  loading.value = true
  try {
    const params = { ...filters.value }
    const response = await api.get('/api/cargas-combustible/', { params })
    let cargasRaw = response.data.results
    totalLitrosEgreso.value = response.data.totales.Egreso || 0
    totalLitrosIngreso.value = response.data.totales.Ingreso || 0

    console.log('Cargas recibidas:', response.data)

    // Agrupar por equipo
    const cargasPorEquipo = {}
    cargasRaw.forEach(c => {
      const key = c.movil || 'sin_equipo'
      if (!cargasPorEquipo[key]) {
        cargasPorEquipo[key] = []
      }
      cargasPorEquipo[key].push({ ...c })
    })

    // Calcular diferencias y L/h
    const resultado = []
    Object.keys(cargasPorEquipo).forEach(equipo => {
      const cargasEq = cargasPorEquipo[equipo].sort((a, b) => new Date(a.fecha) - new Date(b.fecha))

      cargasEq.forEach((actual, i) => {
        if (i === 0) {
          // Primer registro: no hay anterior
          resultado.push({
            ...actual,
            horas_trabajadas: 0,
            consumo_hora: 0
          })
        } else {
          const anterior = cargasEq[i - 1]
          const kmActual = parseFloat(actual.km) || 0
          const kmAnterior = parseFloat(anterior.km) || 0
          const horas = Math.max(0, kmActual - kmAnterior) // evitar valores negativos
          const litros = parseFloat(actual.litros) || 0
          const lth = horas > 0 ? litros / horas : 0

          resultado.push({
            ...actual,
            horas_trabajadas: parseFloat(horas.toFixed(2)),
            consumo_hora: parseFloat(lth.toFixed(2))
          })
        }
      })
    })

    cargasConIndicadores.value = resultado
    console.log('Cargas con indicadores:', cargasConIndicadores.value)
  } catch (error) {
    console.error('Error al cargar datos de combustible:', error)
  } finally {
    loading.value = false
  }
}

const balanceNeto = computed(() => {
  return totalLitrosIngreso.value - totalLitrosEgreso.value
})
// KPIs Computados
const totalCargas = computed(() => {
  return cargasConIndicadores.value.length
})

const totalLitros = computed(() => {
  return totalLitrosIngreso.value - totalLitrosEgreso.value
})

const totalHorasKm = computed(() => {
  if (cargasConIndicadores.value.length === 0) return 0
  const total = cargasConIndicadores.value.reduce((sum, c) => sum + (parseFloat(c.horas_trabajadas) || 0), 0)
  return parseFloat(total.toFixed(2))
})

const consumoMedioGlobal = computed(() => {
  if (cargasConIndicadores.value.length === 0) return 0
  const total = cargasConIndicadores.value.reduce((sum, c) => sum + c.consumo_hora, 0)
  return parseFloat((total / cargasConIndicadores.value.length).toFixed(2))
})

// Gráfico: Litros por Día
const chartDataCombustiblePorEquipo = computed(() => {
  const dataPorEquipo = {}
  const fechasSet = new Set()

  cargasConIndicadores.value.forEach(c => {
    const fecha = c.fecha || 'Sin fecha'
    const equipo = c.movil || 'Sin equipo'
    const litros = parseFloat(c.litros) || 0

    if (!dataPorEquipo[equipo]) {
      dataPorEquipo[equipo] = {}
    }
    if (!dataPorEquipo[equipo][fecha]) {
      dataPorEquipo[equipo][fecha] = 0
    }
    dataPorEquipo[equipo][fecha] += litros
    fechasSet.add(fecha)
  })

  const fechas = Array.from(fechasSet).sort()

  const datasets = Object.keys(dataPorEquipo).map((equipo, index) => {
    const cores = [
      'rgba(59, 130, 246, 0.7)',
      'rgba(16, 185, 129, 0.7)',
      'rgba(245, 158, 11, 0.7)',
      'rgba(239, 68, 68, 0.7)',
      'rgba(139, 92, 246, 0.7)',
      'rgba(14, 165, 233, 0.7)',
      'rgba(217, 119, 6, 0.7)',
    ]
    const color = cores[index % cores.length]
    return {
      label: equipo,
      data: fechas.map(fecha => dataPorEquipo[equipo][fecha] || 0),
      backgroundColor: color,
      borderColor: color.replace('0.7', '1'),
      borderWidth: 1,
      type: 'bar',
      yAxisID: 'y'
    }
  })

  // Línea de consumo medio
  datasets.push({
    label: `Consumo Medio: ${consumoMedioGlobal.value} L/h`,
    data: fechas.map(() => consumoMedioGlobal.value),
    borderColor: 'rgba(255, 99, 132, 1)',
    backgroundColor: 'rgba(255, 99, 132, 0.2)',
    borderWidth: 3,
    type: 'line',
    fill: false,
    tension: 0.3,
    pointBackgroundColor: 'rgba(255, 99, 132, 1)',
    pointRadius: 4,
    yAxisID: 'y1'
  })

  return {
    labels: fechas,
    datasets
  }
})

const chartOptionsCombustiblePorEquipo = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Combustible (L)'
      }
    },
    y1: {
      beginAtZero: true,
      position: 'right',
      title: {
        display: true,
        text: 'Consumo Medio (L/h)'
      },
      grid: {
        drawOnChartArea: false
      }
    },
    x: {
      ticks: {
        autoSkip: true,
        maxRotation: 45,
        minRotation: 0,
        callback: function(value) {
          return this.getLabelForValue(value).slice(5) // "2025-07-22" → "07-22"
        }
      }
    }
  },
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 15,
        boxWidth: 8
      }
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          if (context.dataset.label.includes('Consumo Medio')) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} L/h`
          }
          return `${context.dataset.label}: ${context.parsed.y} L`
        }
      }
    }
  }
}

// Formato numérico
const redondear = (val) => {
  const num = parseFloat(val)
  if (isNaN(num) || !isFinite(num)) return '0.00'
  return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// Cargar al inicio
onMounted(() => {
  const emp = localStorage.getItem('empleado')
  if (!emp) return router.push('/')

  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 30)
  filters.value.start_date = from.toISOString().split('T')[0]
  filters.value.end_date = today.toISOString().split('T')[0]

  const actualizarVisibilidad = () => {
    mostrarFiltros.value = window.innerWidth >= 768
  }

  actualizarVisibilidad()
  window.addEventListener('resize', actualizarVisibilidad)
  onUnmounted(() => {
    window.removeEventListener('resize', actualizarVisibilidad)
  })

  cargarUnidades()
})
const exportarAExcel = () => {
  // Definir las columnas del Excel
  const datos = cargasConIndicadores.value.map(c => ({
    'Fecha': c.fecha,
    'Tipo Movimiento': c.tipo_mov_display,
    'KM/Hora': redondear(c.km),
    'Litros': redondear(c.litros),
    'Horas Trabajadas': redondear(c.horas_trabajadas),
    'Consumo L/h': redondear(c.consumo_hora),
    'Lugar de Carga': c.lugar_carga_detalle || '',
    'Equipo': c.movil_detalle,
    'Patente': c.movil_patente,
    'Unidad de Negocio': c.unidad_negocio_nombre
  }))

  // Crear una hoja de cálculo
  const ws = XLSX.utils.json_to_sheet(datos)

  // Ajustar ancho de columnas
  const columnWidths = [
    { wch: 12 }, // Fecha
    { wch: 15 }, // Tipo Movimiento
    { wch: 10 }, // KM/Hora
    { wch: 10 }, // Litros
    { wch: 15 }, // Horas Trabajadas
    { wch: 12 }, // L/h
    { wch: 18 }, // Lugar de Carga
    { wch: 20 }, // Equipo
    { wch: 12 }, // Patente
    { wch: 20 }  // Unidad de Negocio
  ]
  ws['!cols'] = columnWidths

  // Crear libro
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Cargas Combustible')

  // Exportar
  XLSX.writeFile(wb, `Cargas_Combustible_${filters.value.start_date}_a_${filters.value.end_date}.xlsx`)
}
</script>