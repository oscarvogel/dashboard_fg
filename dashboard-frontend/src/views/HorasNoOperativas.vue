<!-- src/views/produccion/HorasNoOperativasDashboard.vue -->
<script setup>
import { ref, onMounted, watch } from 'vue'
import PieChart from '../components/PieChart.vue'
import api from '../services/api'

// Estado
const filtros = ref({
  un: '',
  fecha_inicio: '',
  fecha_fin: '',
  movil_id: ''
})

const resultsGrafico = ref([])
const datosTabla = ref([])
const datosFiltrados = ref([]) // Para tabla filtrada
const unidadesDisponibles = ref([])
const equipos = ref([])
const loading = ref(false)

// Filtro por motivo (desde clic en gráfico)
const filtroMotivo = ref('') // '' = todos

// Fechas por defecto
const hoy = new Date()
const hace30Dias = new Date()
hace30Dias.setDate(hoy.getDate() - 30)

const generarColores = (n) => {
  const colors = []
  const baseHue = 120; // Green hue
  const saturation = 70; // Consistent saturation
  for (let i = 0; i < n; i++) {
    const lightness = 40 + (i * 10) % 40; // Vary lightness for different shades
    colors.push(`hsl(${baseHue}, ${saturation}%, ${lightness}%)`)
  }
  return colors
}

const formatDate = (date) => date.toISOString().split('T')[0]
filtros.value.fecha_inicio = formatDate(hace30Dias)
filtros.value.fecha_fin = formatDate(hoy)

// Datos del gráfico
const chartData = ref({
  labels: [],
  datasets: []
})

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: true, position: 'right' },
    title: {
      display: true,
      text: 'Distribución de Horas No Operativas'
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const label = context.label || ''
          const value = context.parsed || 0
          return `${label}: ${value.toFixed(2)} hrs`
        }
      }
    }
  },
  onClick: (event, elements) => {
    if (elements.length > 0) {
      const index = elements[0].index
      const motivo = chartData.value.labels[index]
      filtroMotivo.value = motivo
    } else {
      filtroMotivo.value = '' // deseleccionar
    }
  }
})

// Actualizar gráfico
const updateChartData = () => {
  if (resultsGrafico.value.length === 0) {
    chartData.value = {
      labels: ['Sin datos'],
      datasets: [{ data: [1], backgroundColor: ['#d1d5db'] }] // bg-gray-300
    }
    return
  }

  const labels = resultsGrafico.value.map(r => r.motivo)
  const data = resultsGrafico.value.map(r => r.total_hrs_no_op)
  const backgroundColors = generarColores(labels.length)

  chartData.value = {
    labels,
    datasets: [{ data, backgroundColor: backgroundColors }]
  }
}

// Filtrar tabla por motivo
const aplicarFiltroTabla = () => {
  if (!filtroMotivo.value) {
    datosFiltrados.value = datosTabla.value
  } else {
    datosFiltrados.value = datosTabla.value.filter(
      item => item.motivo === filtroMotivo.value
    )
  }
}

// Obtener datos
const fetchData = async () => {
  if (!filtros.value.fecha_inicio || !filtros.value.fecha_fin) return

  loading.value = true
  try {
    const response = await api.get('/api/horas-no-operativas/', {
      params: {
        un: filtros.value.un || undefined,
        fecha_inicio: filtros.value.fecha_inicio,
        fecha_fin: filtros.value.fecha_fin,
        movil_id: filtros.value.movil_id || undefined
      }
    })

    const data = response.data
    resultsGrafico.value = data.results_grafico || []
    datosTabla.value = data.datos_tabla || []
    datosFiltrados.value = datosTabla.value // inicial
    unidadesDisponibles.value = data.unidades_disponibles || []
  } catch (error) {
    console.error('Error al cargar datos:', error)
    alert('No se pudieron cargar los datos.')
  } finally {
    loading.value = false
  }
}

// Cargar equipos según fechas y, opcionalmente, unidad seleccionada
const cargarEquipos = async () => {
  equipos.value = []
  if (!filtros.value.fecha_inicio || !filtros.value.fecha_fin) return
  try {
    const params = {
      start_date: filtros.value.fecha_inicio,
      end_date: filtros.value.fecha_fin
    }
    // Si hay una unidad seleccionada, solicitar equipos por esa unidad.
    // Si no hay unidad (valor '' -> "Todas"), no enviamos "un_id" para obtener todos
    if (filtros.value.un) params.un_id = filtros.value.un
    const response = await api.get('/api/equipos-por-un/', { params })
    equipos.value = response.data.equipos || []
  } catch (error) {
    console.error('Error al cargar equipos:', error)
  }
}

// Aplicar filtros principales
const aplicarFiltros = () => {
  filtroMotivo.value = '' // resetear filtro de gráfico
  fetchData()
}

// Exportar a Excel
const exportarAExcel = () => {
  import('xlsx').then(xlsx => {
    const ws = xlsx.utils.json_to_sheet(
      datosFiltrados.value.map(row => ({
        'Unidad de Negocio': row.un,
        'Equipo': row.equipo || row.movil_detalle || '-',
        'Fecha': row.fecha,
        'Horas No Operativas': row.hrs_no_operativas,
        'Motivo': row.motivo,
        'Observaciones': row.observaciones
      }))
    )
    const wb = xlsx.utils.book_new()
    xlsx.utils.book_append_sheet(wb, ws, 'Horas No Operativas')
    xlsx.writeFile(wb, 'horas_no_operativas.xlsx')
  }).catch(() => {
    alert('Error al cargar la librería xlsx. Instala con: npm install xlsx')
  })
}

// Hooks
onMounted(() => {
  fetchData()
  cargarEquipos()
})

watch(resultsGrafico, updateChartData, { immediate: true })
watch(datosTabla, aplicarFiltroTabla, { immediate: true })
watch(filtroMotivo, aplicarFiltroTabla)
</script>

<template>
  <div class="p-6 bg-primary-50 min-h-screen font-sans">
    <!-- Título -->
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Dashboard: Horas No Operativas</h1>

    <!-- Filtros -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
        <select
          v-model="filtros.un"
          @change="() => { aplicarFiltros(); cargarEquipos(); }"
          class="w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Todas las unidades</option>
          <option
            v-for="un in unidadesDisponibles"
            :key="un.id"
            :value="un.id"
          >
            {{ un.nombre }}
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
        <select
          v-model="filtros.movil_id"
          @change="aplicarFiltros"
          class="w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Todos los equipos</option>
          <option v-for="eq in equipos" :key="eq.id" :value="eq.id">
            {{ eq.detalle }} ({{ eq.patente }})
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
        <input
          v-model="filtros.fecha_inicio"
          type="date"
          @change="() => { aplicarFiltros(); cargarEquipos(); }"
          class="w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Fin</label>
        <input
          v-model="filtros.fecha_fin"
          type="date"
          @change="() => { aplicarFiltros(); cargarEquipos(); }"
          class="w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>
    </div>

    <!-- Botones -->
    <div class="flex flex-wrap gap-4 mb-6">
      <button
        @click="aplicarFiltros"
        :disabled="loading"
        class="px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300 text-white font-medium rounded-md transition"
      >
        {{ loading ? 'Cargando...' : 'Actualizar' }}
      </button>

      <button
        @click="exportarAExcel"
        :disabled="loading || datosFiltrados.length === 0"
        class="px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300 text-white font-medium rounded-md transition"
      >
        Exportar a Excel
      </button>

      <button
        v-if="filtroMotivo"
        @click="filtroMotivo = ''"
        class="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white font-medium rounded-md transition"
      >
        Limpiar filtro: {{ filtroMotivo }}
      </button>
    </div>

    <!-- Gráfico -->
    <div class="bg-white p-6 rounded-lg shadow-md mb-6">
      <div v-if="loading" class="flex justify-center items-center h-64">
        <p class="text-gray-500">Cargando datos...</p>
      </div>
      <PieChart v-else :chart-data="chartData" :chart-options="chartOptions" />
    </div>

    <!-- Tabla -->
    <div class="bg-white p-6 rounded-lg shadow-md">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">
        Detalle de Registros
        <span v-if="filtroMotivo" class="text-sm font-normal text-primary-600">(Filtrado por: "{{ filtroMotivo }}")</span>
      </h2>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UN</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Equipo</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">HNO</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Motivo</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Observaciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="(item, index) in datosFiltrados" :key="index">
              <td class="px-6 py-4 text-sm text-gray-900">{{ item.un }}</td>
              <td class="px-6 py-4 text-sm text-gray-800">{{ item.equipo || item.movil_detalle || '-' }}</td>
              <td class="px-6 py-4 text-sm text-gray-700">{{ item.fecha }}</td>
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ item.hrs_no_operativas }}</td>
              <td class="px-6 py-4 text-sm text-gray-800 font-medium">{{ item.motivo }}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{{ item.observaciones }}</td>
            </tr>
            <tr v-if="datosFiltrados.length === 0">
              <td colspan="5" class="px-6 py-4 text-sm text-gray-500 text-center">
                No hay datos disponibles
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>