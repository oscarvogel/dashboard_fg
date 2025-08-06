<!-- src/views/ResumenOperacional.vue -->
<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Filtros -->
    <section class="bg-white p-6 border-b border-gray-200">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- Mes y Año -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Mes y Año</label>
          <input
            v-model="mesAno"
            type="month"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="cargarUnidades"
          />
        </div>

        <!-- Día específico -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Día (opcional)</label>
          <input
            v-model="dia"
            type="date"
            :min="`${mesAno}-01`"
            :max="ultimoDiaDelMes"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <!-- UN -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
          <select
            v-model="unSeleccionada"
            class="w-full px-3 py-2 border border-gray-300 rounded-md"
            @change="cargarDatos"
          >
            <option value="">Todas</option>
            <!-- 
            
            <option v-for="un in unidadesDisponibles" :key="un" :value="un">{{ un }}</option> -->
              <option v-for="un in unidadesDisponibles" :key="un.id" :value="un.id">
                {{ un.nombre }}
              </option>

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
      <!-- Datos del Día -->
      <div class="bg-white p-6 rounded-lg shadow mb-8" v-if="datosDiarios.length > 0">
        <h2 class="text-lg font-semibold mb-4">Datos del Día</h2>
        <table class="w-full border-collapse border border-gray-300">
          <thead>
            <tr class="bg-gray-100">
              <th class="border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 uppercase">Máquina</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Horas</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">N° árboles</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³ elaborado</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Toneladas carga</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Viajes</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Combustible (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Lubricante (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/árbol</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">árbol/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/m³</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/litro</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/viaje</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fila in datosDiarios" :key="fila.maquina">
              <td class="border border-gray-300 px-4 py-2 text-sm font-medium">{{ fila.maquina }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.arboles) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.toneladas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.viajes) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.lubricante) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.arboles) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.arboles / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.viajes) }}</td>
            </tr>
            <!-- Fila de Totales -->
            <tr v-if="datosDiarios.length > 0" class="bg-blue-50 font-medium">
                <td class="border border-gray-300 px-4 py-2 text-sm">Total</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.arboles) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.m3) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.toneladas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.viajes) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.combustible) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.lubricante) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.m3 / totalDiario.arboles) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.arboles / totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.m3 / totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.toneladas / totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.combustible / totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.combustible / totalDiario.m3) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.toneladas / totalDiario.combustible) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.toneladas / totalDiario.viajes) }}</td>
            </tr>            
          </tbody>
        </table>
      </div>

      <!-- Acumulado del Mes -->
      <div class="bg-white p-6 rounded-lg shadow" v-if="datosMes.length > 0">
        <h2 class="text-lg font-semibold mb-4">Acumulado del Mes</h2>
        <table class="w-full border-collapse border border-gray-300">
          <thead>
            <tr class="bg-gray-100">
              <th class="border border-gray-300 px-4 py-2 text-xs font-semibold text-gray-700 uppercase">Máquina</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Horas</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">N° árboles</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³ elaborado</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Toneladas carga</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Viajes</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Combustible (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Lubricante (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/árbol</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">árbol/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/m³</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/litro</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/viaje</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fila in datosMes" :key="fila.maquina">
              <td class="border border-gray-300 px-4 py-2 text-sm font-medium">{{ fila.maquina }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.arboles) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.toneladas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.viajes) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.lubricante) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.arboles) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.arboles / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.viajes) }}</td>
            </tr>
            <!-- Fila de Totales -->
            <tr v-if="datosMes.length > 0" class="bg-green-50 font-medium">
            <td class="border border-gray-300 px-4 py-2 text-sm">Total</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.arboles) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.m3) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.toneladas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.viajes) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.combustible) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.lubricante) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.m3 / totalMes.arboles) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.arboles / totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.m3 / totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.toneladas / totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.combustible / totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.combustible / totalMes.m3) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.toneladas / totalMes.combustible) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.toneladas / totalMes.viajes) }}</td>
            </tr>    
          </tbody>
        </table>
      </div>

      <!-- Sin datos -->
      <div v-if="!loading && datosDiarios.length === 0 && datosMes.length === 0" class="text-center py-10 text-gray-500">
        No se encontraron datos para el rango seleccionado.
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

const router = useRouter()

// Filtros
const mesAno = ref(new Date().toISOString().slice(0, 7)) // YYYY-MM actual
const dia = ref('')
const unSeleccionada = ref('')
const unidadesDisponibles = ref([])
const datosDiarios = ref([])
const datosMes = ref([])
const loading = ref(false)

// Calcular último día del mes
const ultimoDiaDelMes = computed(() => {
  const [year, month] = mesAno.value.split('-')
  return new Date(year, month, 0).toISOString().slice(0, 10)
})

// Cargar UN disponibles en el mes
const cargarUnidades = async () => {
  if (!mesAno.value) return
  const [year, month] = mesAno.value.split('-')
  const start_date = `${year}-${month}-01`
  const end_date = new Date(year, month, 0).toISOString().slice(0, 10)

  try {
    const params = { start_date, end_date }
    const response = await api.get('/api/filtros/', { params })
    unidadesDisponibles.value = response.data.unidades || []
  } catch (error) {
    console.error('Error al cargar UN:', error)
    unidadesDisponibles.value = []
  }
}

// Cargar datos diarios y mensuales
const cargarDatos = async () => {
  if (!mesAno.value) return
  loading.value = true

  const [year, month] = mesAno.value.split('-')
  const start_date = `${year}-${month}-01`
  const end_date = new Date(year, month, 0).toISOString().slice(0, 10)

  try {
    // Parámetros base
    const params = { start_date, end_date }
    if (unSeleccionada.value) params.un = unSeleccionada.value
    if (dia.value) params.fecha = dia.value

    const response = await api.get('/api/resumen-operacional/', { params })

    // Datos del día
    datosDiarios.value = response.data.diario || []

    // Acumulado del mes
    datosMes.value = response.data.acumulado_mes || []
  } catch (error) {
    console.error('Error al cargar resumen operacional:', error)
    datosDiarios.value = []
    datosMes.value = []
  } finally {
    loading.value = false
  }
}

const totalDiario = computed(() => calcularTotales(datosDiarios.value))

const totalMes = computed(() => calcularTotales(datosMes.value))

// Calcular totales de un array de filas
const calcularTotales = (filas) => {
  if (!filas || filas.length === 0) {
    return {
      maquina: 'Total',
      horas: 0,
      arboles: 0,
      m3: 0,
      toneladas: 0,
      viajes: 0,
      combustible: 0,
      lubricante: 0
    }
  }

  const total = filas.reduce((acc, fila) => {
    acc.horas += parseFloat(fila.horas) || 0
    acc.arboles += parseFloat(fila.arboles) || 0
    acc.m3 += parseFloat(fila.m3) || 0
    acc.toneladas += parseFloat(fila.toneladas) || 0
    acc.viajes += parseFloat(fila.viajes) || 0
    acc.combustible += parseFloat(fila.combustible) || 0
    acc.lubricante += parseFloat(fila.lubricante) || 0
    return acc
  }, {
    maquina: 'Total',
    horas: 0,
    arboles: 0,
    m3: 0,
    toneladas: 0,
    viajes: 0,
    combustible: 0,
    lubricante: 0
  })

  return total
}


// Funciones de utilidad
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
  cargarUnidades()
  cargarDatos()
})
</script>