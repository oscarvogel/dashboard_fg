<!-- src/views/ResumenCombustible.vue -->
<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Filtros -->
    <section class="bg-white p-6 border-b border-gray-200">
      <div class="grid grid-cols-1 md:grid-cols-6 gap-4">
        <!-- Fecha desde -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Desde</label>
          <input v-model="filters.start_date" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-md" @change="cargarUnidades" />
        </div>
        <!-- Fecha hasta -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
          <input v-model="filters.end_date" type="date" class="w-full px-3 py-2 border border-gray-300 rounded-md" @change="cargarUnidades" />
        </div>
        <!-- UN -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
          <select v-model="filters.un_id" class="w-full px-3 py-2 border border-gray-300 rounded-md" @change="cargarEquipos">
            <option value="">Todas</option>
            <option v-for="un in unidades" :key="un.id" :value="un.id">{{ un.nombre }}</option>
          </select>
        </div>
        <!-- Equipo -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
          <select v-model="filters.movil_id" class="w-full px-3 py-2 border border-gray-300 rounded-md" :disabled="!filters.un_id">
            <option value="">Todos</option>
            <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.detalle }} ({{ eq.patente }})</option>
          </select>
        </div>
        <!-- Botón buscar -->
        <div class="flex items-end md:col-span-2">
          <button @click="cargarDatos" :disabled="loading" class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md">
            {{ loading ? 'Cargando...' : 'Buscar' }}
          </button>
        </div>
      </div>
    </section>
    <!-- KPIs -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
      <!-- Total Litros -->
      <div class="bg-white p-6 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Total Litros</h3>
        <p class="text-2xl font-bold text-orange-600">{{ redondear(totalLitros) }} L</p>
      </div>

      <!-- Total Horas/Km -->
      <div class="bg-white p-6 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Horas/Km Trabajados</h3>
        <p class="text-2xl font-bold text-blue-600">{{ redondear(totalHorasKm) }} h/km</p>
      </div>

      <!-- Consumo Medio -->
      <div class="bg-white p-6 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Consumo Medio</h3>
        <p class="text-2xl font-bold text-green-600">{{ consumoMedioGlobal }} L/h/KM</p>
        <p class="text-xs text-gray-500">litros por hora/km</p>
      </div>

      <!-- Número de Cargas -->
      <div class="bg-white p-6 rounded-lg shadow text-center">
        <h3 class="text-sm font-medium text-gray-500">Cargas Realizadas</h3>
        <p class="text-2xl font-bold text-purple-600">{{ totalCargas }}</p>
      </div>
    </div>
    <!-- Contenido -->
    <main class="flex-1 p-6 overflow-y-auto">
      <!-- Gráfico: Litros por día -->
      <div class="bg-white p-6 rounded-lg shadow mb-6">
        <h2 class="text-xl font-semibold mb-4">Litros por Día</h2>
        <BarChart 
          :chart-data="chartDataCombustiblePorEquipo" 
          :options="chartOptionsCombustiblePorEquipo"
        />      
      </div>

      <!-- Tabla: Cargas -->
      <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Detalles de Cargas de Combustible</h2>
        <!-- Tabla -->
        <table class="w-full border-collapse border border-gray-300">
          <thead class="bg-gray-100">
            <tr>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Fecha</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">KM/Hora</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Litros</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Horas Trab.</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">L/h</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Lugar Carga</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in cargasConIndicadores" :key="c.id" class="hover:bg-gray-50">
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ c.fecha }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(parseFloat(c.km)) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(parseFloat(c.litros)) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(c.horas_trabajadas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(c.consumo_hora) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ c.lugar_carga_detalle }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'

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
    console.error('Error al cargar operadores y equipos:', error)
  }
}

// // Cargar datos
// const cargarDatos = async () => {
//   if (!filters.value.start_date || !filters.value.end_date) return
//   loading.value = true
//   try {
//     const params = { ...filters.value }
//     const response = await api.get('/api/cargas-combustible/', { params })
//     cargas.value = response.data.results
//     console.log('Cargas:', cargas.value)
//   } catch (error) {
//     console.error('Error al cargar cargas:', error)
//   } finally {
//     loading.value = false
//   }
// }
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

    // Agrupar por equipo
    const cargasPorEquipo = {}
    cargasRaw.forEach(c => {
      if (!cargasPorEquipo[c.movil]) {
        cargasPorEquipo[c.movil] = []
      }
      cargasPorEquipo[c.movil].push({ ...c })
    })

    // Calcular diferencias y L/h
    const resultado = []
    Object.keys(cargasPorEquipo).forEach(equipo => {
      // Ordenar por fecha
      const cargasEq = cargasPorEquipo[equipo].sort((a, b) => new Date(a.fecha) - new Date(b.fecha))

      for (let i = 1; i < cargasEq.length; i++) {
        const actual = cargasEq[i]
        const anterior = cargasEq[i - 1]

        const kmActual = parseFloat(actual.km) || 0
        const kmAnterior = parseFloat(anterior.km) || 0
        const horas = kmActual - kmAnterior // Diferencia de km como horas trabajadas
        const litros = parseFloat(actual.litros) || 0

        const lth = horas > 0 ? litros / horas : 0

        resultado.push({
          ...actual,
          horas_trabajadas: parseFloat(horas.toFixed(2)),
          consumo_hora: parseFloat(lth.toFixed(2))
        })
      }
    })

    cargasConIndicadores.value = resultado
    // console.log('Cargas con indicadores:', cargasConIndicadores.value)
  } catch (error) {
    console.error('Error al cargar datos de combustible:', error)
  } finally {
    loading.value = false
  }
}

const consumoMedioGlobal = computed(() => {
  if (cargasConIndicadores.value.length === 0) return 0
  const total = cargasConIndicadores.value.reduce((sum, c) => sum + c.consumo_hora, 0)

  return parseFloat((total / cargasConIndicadores.value.length).toFixed(2))
})

const totalCargas = computed(() => {
  return cargasConIndicadores.value.length
})

const totalLitros = computed(() => {
  return cargasConIndicadores.value.reduce((sum, c) => sum + (parseFloat(c.litros) || 0), 0)
})

const chartDataCombustiblePorEquipo = computed(() => {
  const dataPorEquipo = {}
  const fechasSet = new Set()

  // Agrupar litros por equipo y fecha (solo para el gráfico de barras)
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

  // Datasets: barras por equipo
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

  // Añadir línea de consumo medio (L/h)
  datasets.push({
    label: `Consumo Medio: ${consumoMedioGlobal.value} L/h`,
    data:fechas.map(() => consumoMedioGlobal.value),
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

// Formato
const redondear = (val) => {
  return typeof val === 'number' ? val.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : '0'
}

const totalHorasKm = computed(() => {
  if (cargasConIndicadores.value.length === 0) return 0
  const total = cargasConIndicadores.value.reduce((sum, c) => sum + (parseFloat(c.horas_trabajadas) || 0), 0)
  return parseFloat(total.toFixed(2))
})
// Cargar al inicio
onMounted(() => {
  const emp = localStorage.getItem('empleado')
  if (!emp) return router.push('/')
  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 30) // 30 días atrás
  filters.value.start_date = from.toISOString().split('T')[0]
  filters.value.end_date = today.toISOString().split('T')[0]
  cargarUnidades()
})

const calcular = (val) => {
  if (typeof val !== 'number' || isNaN(val) || !isFinite(val)) return '0'
  return val.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}
</script>