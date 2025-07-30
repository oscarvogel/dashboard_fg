<!-- src/views/ResumenCombustible.vue -->
<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Filtros -->
    <section class="bg-white p-6 border-b border-gray-200">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <!-- Fecha desde -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Desde</label>
          <input
            v-model="filters.start_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="cargarFiltros"
          />
        </div>
        <!-- Fecha hasta -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
          <input
            v-model="filters.end_date"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="cargarFiltros"
          />
        </div>
        <!-- UN -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
          <select
            v-model="filters.un"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="cargarFiltrosSecundarios"
          >
            <option value="">Todas</option>
            <option v-for="un in unidades" :key="un" :value="un">{{ un }}</option>
          </select>
        </div>
        <!-- Tipo de Operación -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Operación</label>
          <select
            v-model="filters.operacion"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            :disabled="!filters.un"
          >
            <option value="">Todas</option>
            <option v-for="op in operaciones" :key="op" :value="op">{{ op }}</option>
          </select>
        </div>
        <!-- Equipo -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
          <select
            v-model="filters.detalle_equipo"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            :disabled="!filters.un"
          >
            <option value="">Todos</option>
            <option v-for="eq in equipos" :key="eq" :value="eq">{{ eq }}</option>
          </select>
        </div>
        <!-- Botón buscar -->
        <div class="flex items-end">
          <button
            @click="cargarDatos"
            :disabled="loading"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md"
          >
            {{ loading ? 'Cargando...' : 'Buscar' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Contenido principal -->
    <main class="flex-1 p-6 overflow-y-auto">
      <!-- Gráfico: Consumo de combustible por equipo y por día -->
      <div class="bg-white p-6 rounded-lg shadow mb-6">
        <h2 class="text-xl font-semibold mb-4">Consumo de Combustible por Equipo (L/día)</h2>
        <BarChart
          :chart-data="chartDataCombustiblePorEquipo"
          :options="chartOptionsCombustiblePorEquipo"
        />
      </div>

      <!-- Tabla: Cargas por día -->
      <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-lg font-semibold mb-4">Cargas de Combustible por Día</h2>
        <table class="w-full border-collapse border border-gray-300">
          <thead>
            <tr class="bg-gray-100">
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Fecha</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">UN</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Operación</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Equipo</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Combustible (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">Horas Trabajadas</th>
              <th class="border border-gray-300 px-4 py-2 text-sm font-semibold">L/h</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="carga in cargasPorDia" :key="carga.id" class="hover:bg-gray-50">
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ carga.fecha }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ carga.un }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ carga.operacion }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm">{{ carga.equipo }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(carga.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(carga.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(carga.combustible / carga.horas) }}</td>
            </tr>
            <!-- Fila de Totales -->
            <tr v-if="cargasPorDia.length > 0" class="bg-blue-50 font-medium">
              <td class="border border-gray-300 px-4 py-2 text-sm">Total</td>
              <td class="border border-gray-300 px-4 py-2 text-sm"></td>
              <td class="border border-gray-300 px-4 py-2 text-sm"></td>
              <td class="border border-gray-300 px-4 py-2 text-sm"></td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalCombustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalHoras) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalCombustible / totalHoras) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Sin datos -->
      <div v-if="!loading && cargasPorDia.length === 0" class="text-center py-10 text-gray-500">
        No se encontraron registros de combustible para el rango seleccionado.
      </div>

      <!-- Cargando -->
      <div v-if="loading" class="flex justify-center py-6">
        <svg class="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
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
  un: '',
  operacion: '',        // ← Cambiado: operador → operacion
  detalle_equipo: ''
})

// Listas de filtros
const unidades = ref([])
const operaciones = ref([])  // ← Nuevo: operaciones
const equipos = ref([])

// Datos
const registros = ref([])
const loading = ref(false)
const cargasPorDia = ref([])

// Cargar filtros iniciales (UN)
const cargarFiltros = async () => {
  if (!filters.value.start_date || !filters.value.end_date) return
  try {
    const params = {
      start_date: filters.value.start_date,
      end_date: filters.value.end_date
    }
    const response = await api.get('/api/filtros/', { params })
    unidades.value = response.data.unidades
  } catch (error) {
    console.error('Error al cargar UN:', error)
  }
}

// Cargar operaciones y equipos según UN
const cargarFiltrosSecundarios = async () => {
  if (!filters.value.un) {
    operaciones.value = []
    equipos.value = []
    return
  }
  try {
    const params = {
      start_date: filters.value.start_date,
      end_date: filters.value.end_date,
      un: filters.value.un
    }
    const response = await api.get('/api/filtros/', { params })
    operaciones.value = response.data.operaciones
    equipos.value = response.data.equipos
  } catch (error) {
    console.error('Error al cargar operaciones y equipos:', error)
  }
}

// Cargar datos
const cargarDatos = async () => {
  if (!filters.value.start_date || !filters.value.end_date) return
  loading.value = true
  try {
    const response = await api.get('/api/produccion-dashboard/', { params: filters.value })
    registros.value = response.data.results

    // Procesar cargas por día
    const datos = {}
    registros.value.forEach(r => {
      const fecha = r.fecha || 'Sin fecha'
      if (!datos[fecha]) {
        datos[fecha] = {
          fecha,
          un: r.UN,
          operacion: r.operacion,
          equipo: r.equipo_detalle,
          combustible: 0,
          horas: 0
        }
      }
      datos[fecha].combustible += parseFloat(r.combustible) || 0
      const horas = Math.max(0, (r.hr_fin || 0) - (r.hr_inicio || 0))
      datos[fecha].horas += horas
    })
    cargasPorDia.value = Object.values(datos)
  } catch (error) {
    console.error('Error al cargar datos de combustible:', error)
  } finally {
    loading.value = false
  }
}

// Totales
const totalCombustible = computed(() => {
  return cargasPorDia.value.reduce((sum, c) => sum + c.combustible, 0)
})
const totalHoras = computed(() => {
  return cargasPorDia.value.reduce((sum, c) => sum + c.horas, 0)
})

// --- GRÁFICO: Combustible por equipo y por día (con línea de consumo medio L/h) ---
const chartDataCombustiblePorEquipo = computed(() => {
  const dataPorEquipo = {};
  const dataPorFecha = {}; // Para calcular consumo medio diario
  const fechasSet = new Set();

  // Agrupar por equipo y por fecha
  registros.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha';
    const equipo = r.equipo_detalle || 'Sin equipo';
    const combustible = parseFloat(r.combustible) || 0;
    if (!dataPorEquipo[equipo]) {
      dataPorEquipo[equipo] = {};
    }
    if (!dataPorEquipo[equipo][fecha]) {
      dataPorEquipo[equipo][fecha] = 0;
    }
    dataPorEquipo[equipo][fecha] += combustible;
    if (!dataPorFecha[fecha]) {
      dataPorFecha[fecha] = { combustible: 0, horas: 0 };
    }
    dataPorFecha[fecha].combustible += combustible;
    const horas = Math.max(0, (r.hr_fin || 0) - (r.hr_inicio || 0));
    dataPorFecha[fecha].horas += horas;
    fechasSet.add(fecha);
  });

  // Ordenar fechas
  const fechas = Array.from(fechasSet).sort();

  // Calcular consumo medio diario (L/h) para todos los equipos
  const consumoMedioData = fechas.map(fecha => {
    const { combustible, horas } = dataPorFecha[fecha];
    return horas > 0 ? combustible / horas : 0;
  });

  // Crear datasets por equipo
  const datasets = Object.keys(dataPorEquipo).map((equipo, index) => {
    const cores = [
      'rgba(59, 130, 246, 0.7)',
      'rgba(16, 185, 129, 0.7)',
      'rgba(245, 158, 11, 0.7)',
      'rgba(239, 68, 68, 0.7)',
      'rgba(139, 92, 246, 0.7)',
      'rgba(14, 165, 233, 0.7)',
      'rgba(217, 119, 6, 0.7)',
    ];
    const color = cores[index % cores.length];
    return {
      label: equipo,
      data: fechas.map(fecha => dataPorEquipo[equipo][fecha] || 0),
      backgroundColor: color,
      borderColor: color.replace('0.7', '1'),
      borderWidth: 1,
      type: 'bar',
      yAxisID: 'y', // Asignar al eje y principal
    };
  });

  // Añadir línea de consumo medio (L/h)
  datasets.push({
    label: 'Consumo Medio (L/h)',
    data: consumoMedioData,
    borderColor: 'rgba(255, 99, 132, 1)',
    backgroundColor: 'rgba(255, 99, 132, 0.2)',
    borderWidth: 3,
    type: 'line',
    fill: false,
    tension: 0.3,
    pointBackgroundColor: 'rgba(255, 99, 132, 1)',
    pointRadius: 4,
    yAxisID: 'y1', // Asignar al eje y secundario
  });

  return {
    labels: fechas,
    datasets,
  };
});


// Opciones del gráfico (con doble eje Y)
const chartOptionsCombustiblePorEquipo = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Combustible (L/día)',
      },
      ticks: {
        callback: (value) => `${value} L`,
      },
    },
    y1: {
      beginAtZero: true,
      position: 'right',
      title: {
        display: true,
        text: 'Consumo Medio (L/h)',
      },
      ticks: {
        callback: (value) => `${value.toFixed(2)} L/h`,
      },
      grid: {
        drawOnChartArea: false,
      },
    },
  },
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 15,
        boxWidth: 8,
      },
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          if (context.dataset.label === 'Consumo Medio (L/h)') {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} L/h`;
          }
          return `${context.dataset.label}: ${context.parsed.y} L`;
        },
      },
    },
  },
};

// Funciones de formato
const redondear = (val) => {
  if (typeof val !== 'number' || isNaN(val)) return '0'
  return val.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}
const calcular = (val) => {
  if (typeof val !== 'number' || isNaN(val) || !isFinite(val)) return '0'
  return val.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// Cargar al inicio
onMounted(() => {
  const emp = localStorage.getItem('empleado')
  if (!emp) return router.push('/')
  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 7)
  filters.value.start_date = from.toISOString().split('T')[0]
  filters.value.end_date = today.toISOString().split('T')[0]
  cargarFiltros()
})
</script>