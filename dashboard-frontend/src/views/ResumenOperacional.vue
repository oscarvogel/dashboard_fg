<!-- src/views/ResumenOperacional.vue -->
<template>
  <div class="flex flex-col h-screen bg-primary-50">
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

        <!-- Botones buscar y exportar -->
        <div class="flex items-end gap-2">
          <button
            @click="cargarDatos"
            :disabled="loading"
            class="flex-1 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white font-medium py-2 px-4 rounded-md"
          >
            {{ loading ? 'Cargando...' : 'Buscar' }}
          </button>
          <button
            @click="exportarExcel"
            :disabled="loading || (datosDiarios.length === 0 && datosMes.length === 0)"
            class="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-md flex items-center gap-2"
            title="Exportar a Excel"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 17a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2zM3 7a1 1 0 011-1h12a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V7zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/>
            </svg>
            Excel
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
              <th class="border border-gray-300 px-4 py-2 text-xs">m³ elaborado</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Viajes</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Combustible (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Lubricante (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/árbol</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">árboles/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/m³</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">ton/litro</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fila in datosDiarios" :key="fila.maquina">
              <td class="border border-gray-300 px-4 py-2 text-sm font-medium">{{ fila.maquina }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.viajes) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.lubricante) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.arboles) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.arboles / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.toneladas / fila.combustible) }}</td>
            </tr>
            <!-- Fila de Totales -->
            <tr v-if="datosDiarios.length > 0" class="bg-primary-50 font-medium">
                <td class="border border-gray-300 px-4 py-2 text-sm">Total</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.m3) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.viajes) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.combustible) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalDiario.lubricante) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.m3 / totalDiario.arboles) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(calcularPromedioM3Hora(datosDiarios)) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(calcularPromedioArbolesHora(datosDiarios)) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.combustible / totalDiario.horas) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(calcularPromedioLitrosM3(datosDiarios)) }}</td>
                <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalDiario.toneladas / totalDiario.combustible) }}</td>
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
              <th class="border border-gray-300 px-4 py-2 text-xs">m³ elaborado</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Combustible (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">Lubricante (L)</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/árbol</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">m³/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">árboles/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/hora</th>
              <th class="border border-gray-300 px-4 py-2 text-xs">litros/m³</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fila in datosMes" :key="fila.maquina">
              <td class="border border-gray-300 px-4 py-2 text-sm font-medium">{{ fila.maquina }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.m3) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.combustible) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(fila.lubricante) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.arboles) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.m3 / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.arboles / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.horas) }}</td>
              <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(fila.combustible / fila.m3) }}</td>
            </tr>
            <!-- Fila de Totales -->
            <tr v-if="datosMes.length > 0" class="bg-green-50 font-medium">
            <td class="border border-gray-300 px-4 py-2 text-sm">Total</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.m3) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.combustible) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ redondear(totalMes.lubricante) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.m3 / totalMes.arboles) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(calcularPromedioM3Hora(datosMes)) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(calcularPromedioArbolesHora(datosMes)) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(totalMes.combustible / totalMes.horas) }}</td>
            <td class="border border-gray-300 px-4 py-2 text-sm text-center">{{ calcular(calcularPromedioLitrosM3(datosMes)) }}</td>
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
        <svg class="animate-spin h-6 w-6 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
import * as XLSX from 'xlsx'
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

// Calcular promedio de m³/hora considerando solo filas con producción real
const calcularPromedioM3Hora = (filas) => {
  if (!filas || filas.length === 0) return 0

  // Filtrar solo filas donde hay producción real (m3 > 0 y horas > 0)
  const filasConProduccion = filas.filter(fila => {
    const m3 = parseFloat(fila.m3) || 0
    const horas = parseFloat(fila.horas) || 0
    return m3 > 0 && horas > 0
  })

  if (filasConProduccion.length === 0) return 0

  // Sumar m³/hora de cada fila
  const sumPromedios = filasConProduccion.reduce((sum, fila) => {
    const m3 = parseFloat(fila.m3) || 0
    const horas = parseFloat(fila.horas) || 0
    return sum + (horas > 0 ? m3 / horas : 0)
  }, 0)

  // Devolver promedio
  return sumPromedios / filasConProduccion.length
}

// Calcular promedio de árboles/hora excluyendo filas sin árboles o sin horas válidas
const calcularPromedioArbolesHora = (filas) => {
  if (!filas || filas.length === 0) return 0

  const filasValidas = filas.filter(fila => {
    const arboles = parseFloat(fila.arboles) || 0
    const horas = parseFloat(fila.horas) || 0
    return arboles > 0 && horas > 0
  })

  if (filasValidas.length === 0) return 0

  const sumPromedios = filasValidas.reduce((sum, fila) => {
    const arboles = parseFloat(fila.arboles) || 0
    const horas = parseFloat(fila.horas) || 0
    return sum + (horas > 0 ? arboles / horas : 0)
  }, 0)

  return sumPromedios / filasValidas.length
}

// Calcular promedio de litros/m³ considerando solo filas con producción real
const calcularPromedioLitrosM3 = (filas) => {
  if (!filas || filas.length === 0) return 0

  // Filtrar solo filas donde hay producción real (m3 > 0)
  const filasConProduccion = filas.filter(fila => {
    const m3 = parseFloat(fila.m3) || 0
    return m3 > 0
  })

  if (filasConProduccion.length === 0) return 0

  // Sumar litros/m³ de cada fila
  const sumPromedios = filasConProduccion.reduce((sum, fila) => {
    const m3 = parseFloat(fila.m3) || 0
    const combustible = parseFloat(fila.combustible) || 0
    return sum + (m3 > 0 ? combustible / m3 : 0)
  }, 0)

  // Devolver promedio
  return sumPromedios / filasConProduccion.length
}

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
    const horas = parseFloat(fila.horas) || 0
    // Solo sumar valores de filas con horas > 0 (datos válidos)
    if (horas > 0) {
      acc.horas += horas
      acc.arboles += parseFloat(fila.arboles) || 0
      acc.m3 += parseFloat(fila.m3) || 0
      acc.toneladas += parseFloat(fila.toneladas) || 0
      acc.viajes += parseFloat(fila.viajes) || 0
      acc.combustible += parseFloat(fila.combustible) || 0
      acc.lubricante += parseFloat(fila.lubricante) || 0
    }
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

// Función para exportar a Excel
const exportarExcel = () => {
  const workbook = XLSX.utils.book_new()

  // Obtener nombre de la unidad seleccionada
  const unidadNombre = unSeleccionada.value ?
    unidadesDisponibles.value.find(un => un.id == unSeleccionada.value)?.nombre || 'Todas' :
    'Todas'

  // Información del archivo
  const fechaExport = new Date().toLocaleDateString('es-CL')
  const periodo = mesAno.value
  const diaEspecifico = dia.value ? new Date(dia.value).toLocaleDateString('es-CL') : 'Todo el mes'

  // Datos diarios (si existen)
  if (datosDiarios.value.length > 0) {
    const datosDiariosParaExcel = datosDiarios.value.map(fila => ({
      'Máquina': fila.maquina,
      'Horas': parseFloat(fila.horas) || 0,
      'm³ elaborado': parseFloat(fila.m3) || 0,
      'Viajes': parseFloat(fila.viajes) || 0,
      'Combustible (L)': parseFloat(fila.combustible) || 0,
      'Lubricante (L)': parseFloat(fila.lubricante) || 0,
      'm³/árbol': calcularValor(fila.m3 / fila.arboles),
      'm³/hora': calcularValor(fila.m3 / fila.horas),
      'árboles/hora': calcularValor(fila.arboles / fila.horas),
      'litros/hora': calcularValor(fila.combustible / fila.horas),
      'litros/m³': calcularValor(fila.combustible / fila.m3)
    }))

    // Agregar fila de totales
    datosDiariosParaExcel.push({
      'Máquina': 'TOTAL',
      'Horas': totalDiario.value.horas,
      'm³ elaborado': totalDiario.value.m3,
      'Viajes': totalDiario.value.viajes,
      'Combustible (L)': totalDiario.value.combustible,
      'Lubricante (L)': totalDiario.value.lubricante,
      'm³/árbol': calcularValor(totalDiario.value.m3 / totalDiario.value.arboles),
      'm³/hora': calcularValor(calcularPromedioM3Hora(datosDiarios.value)),
      'árboles/hora': calcularValor(calcularPromedioArbolesHora(datosDiarios.value)),
      'litros/hora': calcularValor(totalDiario.value.combustible / totalDiario.value.horas),
      'litros/m³': calcularValor(calcularPromedioLitrosM3(datosDiarios.value))
    })

    const wsDiario = XLSX.utils.json_to_sheet(datosDiariosParaExcel)
    XLSX.utils.book_append_sheet(workbook, wsDiario, 'Datos del Día')
  }

  // Datos mensuales (si existen)
  if (datosMes.value.length > 0) {
    const datosMesParaExcel = datosMes.value.map(fila => ({
      'Máquina': fila.maquina,
      'Horas': parseFloat(fila.horas) || 0,
      'm³ elaborado': parseFloat(fila.m3) || 0,
      'Viajes': parseFloat(fila.viajes) || 0,
      'Combustible (L)': parseFloat(fila.combustible) || 0,
      'Lubricante (L)': parseFloat(fila.lubricante) || 0,
      'm³/árbol': calcularValor(fila.m3 / fila.arboles),
      'm³/hora': calcularValor(fila.m3 / fila.horas),
      'árboles/hora': calcularValor(fila.arboles / fila.horas),
      'litros/hora': calcularValor(fila.combustible / fila.horas),
      'litros/m³': calcularValor(fila.combustible / fila.m3)
    }))

    // Agregar fila de totales
    datosMesParaExcel.push({
      'Máquina': 'TOTAL',
      'Horas': totalMes.value.horas,
      'm³ elaborado': totalMes.value.m3,
      'Viajes': totalMes.value.viajes,
      'Combustible (L)': totalMes.value.combustible,
      'Lubricante (L)': totalMes.value.lubricante,
      'm³/árbol': calcularValor(totalMes.value.m3 / totalMes.value.arboles),
      'm³/hora': calcularValor(calcularPromedioM3Hora(datosMes.value)),
      'árboles/hora': calcularValor(calcularPromedioArbolesHora(datosMes.value)),
      'litros/hora': calcularValor(totalMes.value.combustible / totalMes.value.horas),
      'litros/m³': calcularValor(calcularPromedioLitrosM3(datosMes.value))
    })

    const wsMes = XLSX.utils.json_to_sheet(datosMesParaExcel)
    XLSX.utils.book_append_sheet(workbook, wsMes, 'Acumulado del Mes')
  }

  // Crear hoja de información
  const infoData = [
    ['RESUMEN OPERACIONAL'],
    [''],
    ['Período:', periodo],
    ['Día específico:', diaEspecifico],
    ['Unidad de Negocio:', unidadNombre],
    ['Fecha de exportación:', fechaExport],
    [''],
    ['Este archivo contiene:'],
    ...(datosDiarios.value.length > 0 ? [['- Datos del día seleccionado']] : []),
    ...(datosMes.value.length > 0 ? [['- Acumulado del mes']] : [])
  ]

  const wsInfo = XLSX.utils.aoa_to_sheet(infoData)
  XLSX.utils.book_append_sheet(workbook, wsInfo, 'Información', 0)

  // Generar nombre del archivo
  const nombreArchivo = `resumen_operacional_${periodo}${dia.value ? '_' + dia.value : ''}_${unidadNombre.replace(/\s+/g, '_')}.xlsx`

  // Descargar archivo
  XLSX.writeFile(workbook, nombreArchivo)
}

// Función auxiliar para calcular valores numéricos
const calcularValor = (val) => {
  if (typeof val !== 'number' || isNaN(val) || !isFinite(val)) return 0
  return parseFloat(val.toFixed(2))
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