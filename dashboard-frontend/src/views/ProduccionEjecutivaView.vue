<template>
  <div class="min-h-screen bg-primary-50 p-6">
    <div class="max-w-7xl mx-auto space-y-6">
      <section class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h1 class="text-2xl font-bold text-gray-800">Producción Ejecutiva</h1>
        <p class="text-sm text-gray-500 mt-1">Portada principal para seguimiento mensual por unidad de negocio.</p>

        <form class="grid grid-cols-1 md:grid-cols-6 gap-4 mt-5" @submit.prevent="buscarDatos">
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-600 mb-1">Mes / Año</label>
            <input
              v-model="selectedMonth"
              type="month"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            />
          </div>

          <div class="md:col-span-1">
            <label class="block text-sm font-medium text-gray-600 mb-1">Día (opcional)</label>
            <select
              v-model="selectedDay"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Último día con actividad</option>
              <option v-for="day in availableDays" :key="day" :value="day">{{ day }}</option>
            </select>
          </div>

          <div class="md:col-span-3">
            <label class="block text-sm font-medium text-gray-600 mb-1">Unidad de Negocio (activas)</label>
            <select
              v-model="selectedUnidad"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Seleccionar unidad</option>
              <option v-for="un in unidades" :key="un.id" :value="un.id">{{ un.nombre }}</option>
            </select>
          </div>

          <div class="md:col-span-6 flex items-center gap-3">
            <button
              type="submit"
              :disabled="loading || !selectedUnidad"
              class="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300 text-white font-semibold px-6 py-2 rounded-md transition-colors"
            >
              {{ loading ? 'Buscando...' : 'Buscar' }}
            </button>
            <button
              type="button"
              :disabled="loading || !dataLoaded"
              @click="exportarExcel"
              class="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white font-semibold px-4 py-2 rounded-md transition-colors"
            >
              <i class="fas fa-file-excel"></i>
              Exportar a Excel
            </button>
          </div>
        </form>

        <div v-if="periodoInfo.cutoff_date" class="mt-3 text-xs text-gray-500">
          Corte de información: {{ periodoInfo.cutoff_date }}
        </div>
      </section>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 class="text-sm font-medium text-gray-500">Producción Real</h3>
          <p class="text-2xl font-bold text-primary-700 mt-2">{{ formatNumber(totalProduccion) }} {{ unidadProduccion }}</p>
          <p class="text-sm mt-1" :class="colorCumplimiento">
            {{ iconoCumplimiento }} {{ formatNumber(produccionEsperada) }} esperada
          </p>
        </div>

        <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 class="text-sm font-medium text-gray-500">Cumplimiento</h3>
          <p class="text-2xl font-bold mt-2" :class="eficiencia >= 100 ? 'text-primary-700' : 'text-red-700'">
            {{ eficiencia }}%
          </p>
        </div>

        <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 class="text-sm font-medium text-gray-500">Stock ABC</h3>
          <p class="text-2xl font-bold text-primary-700 mt-2">{{ formatNumber(stockAbcTotal) }} TN</p>
        </div>
      </section>

      <section class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 overflow-x-auto">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Consumo por Equipo</h2>
        <table class="min-w-full divide-y divide-gray-200 text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left font-semibold text-gray-600">Máquina (Equipo)</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Lts/Hora Día</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Lts/Hora Acumulado</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Lts/m3 Día</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Lts/m3 Acumulado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="item in tablaConsumo" :key="item.equipo">
              <td class="px-4 py-3 text-gray-800">{{ item.equipo }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.lts_hora_dia) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.lts_hora_acumulado) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.lts_m3_dia) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.lts_m3_acumulado) }}</td>
            </tr>
            <tr v-if="tablaConsumo.length === 0">
              <td colspan="5" class="px-4 py-6 text-center text-gray-500">Sin datos para mostrar</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 overflow-x-auto">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Producción por Equipo</h2>
        <table class="min-w-full divide-y divide-gray-200 text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left font-semibold text-gray-600">Máquina (Equipo)</th>
              <th class="px-4 py-3 text-left font-semibold text-gray-600">Unidad de Producción</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Producción Día</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Producción Acumulada</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Prod/Hora Día</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Prod/Hora Acumulada</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Prod/Árbol Día</th>
              <th class="px-4 py-3 text-right font-semibold text-gray-600">Prod/Árbol Acumulada</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="item in tablaProduccion" :key="item.equipo">
              <td class="px-4 py-3 text-gray-800">{{ item.equipo }}</td>
              <td class="px-4 py-3 text-gray-700">{{ item.unidad_produccion || '-' }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.produccion_dia) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.produccion_acumulada) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.produccion_hora_dia) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.produccion_hora_acumulada) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.produccion_arbol_dia) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatNumber(item.produccion_arbol_acumulada) }}</td>
            </tr>
            <tr v-if="tablaProduccion.length === 0">
              <td colspan="8" class="px-4 py-6 text-center text-gray-500">Sin datos para mostrar</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import * as XLSX from 'xlsx'
import api from '../services/api'

const selectedMonth = ref('')
const selectedDay = ref('')
const selectedUnidad = ref('')

const unidades = ref([])
const loading = ref(false)
const dataLoaded = ref(false)

const periodoInfo = ref({})
const produccionEsperada = ref(0)
const stockAbcTotal = ref(0)
const unidadProduccion = ref('')
const registros = ref([])
const tablaConsumo = ref([])
const tablaProduccion = ref([])

const availableDays = computed(() => {
  if (!selectedMonth.value) return []
  const [year, month] = selectedMonth.value.split('-').map(Number)
  const maxDays = new Date(year, month, 0).getDate()
  return Array.from({ length: maxDays }, (_, i) => i + 1)
})

// KPIs - Exactamente igual que DashboardView.vue
const totalProduccion = computed(() => {
  return registros.value.reduce((sum, r) => sum + parseFloat(r.produccion || 0), 0)
})


const eficiencia = computed(() => {
  const esperada = parseFloat(produccionEsperada.value || 0)
  const real = totalProduccion.value

  if (esperada === 0) return real === 0 ? 100 : 0 // Evitar división por cero

  return parseFloat(((real / esperada) * 100).toFixed(2))
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
  return { superior: 'text-primary-600', inferior: 'text-red-600', normal: 'text-yellow-600' }[cumplimiento.value]
})

const iconoCumplimiento = computed(() => {
  const estado = cumplimiento.value
  if (estado === 'superior') return '↑'
  if (estado === 'inferior') return '↓'
  return '–'
})

const formatNumber = (num) => {
  const n = isNaN(parseFloat(num)) ? 0 : parseFloat(num)
  return n.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
}

const parseMonth = () => {
  if (!selectedMonth.value) return null
  const [year, month] = selectedMonth.value.split('-').map(Number)
  if (!year || !month) return null
  return { year, month }
}

const cargarUnidadesActivas = async () => {
  const parsed = parseMonth()
  if (!parsed) return

  try {
    const response = await api.get('/api/produccion-ejecutiva-filtros/', {
      params: {
        month: parsed.month,
        year: parsed.year,
      }
    })

    unidades.value = response.data.unidades || []

    const exists = unidades.value.some((u) => String(u.id) === String(selectedUnidad.value))
    if (!exists) {
      selectedUnidad.value = unidades.value[0]?.id || ''
    }
  } catch (error) {
    console.error('Error al cargar unidades activas:', error)
    unidades.value = []
    selectedUnidad.value = ''
  }
}

const buscarDatos = async () => {
  const parsed = parseMonth()
  if (!parsed || !selectedUnidad.value) return

  loading.value = true
  try {
    const params = {
      month: parsed.month,
      year: parsed.year,
      cod_un: selectedUnidad.value,
    }
    if (selectedDay.value) {
      params.day = selectedDay.value
    }

    const response = await api.get('/api/produccion-ejecutiva/', { params })

    periodoInfo.value = response.data.periodo || {}
    unidadProduccion.value = response.data.unidad_produccion || ''
    produccionEsperada.value = response.data.produccion_esperada_acumulada || 0
    stockAbcTotal.value = response.data.stock_abc_total || 0
    registros.value = response.data.registros || []
    tablaConsumo.value = response.data.tabla_consumo || []
    tablaProduccion.value = response.data.tabla_produccion || []
    dataLoaded.value = true
  } catch (error) {
    console.error('Error al buscar producción ejecutiva:', error)
    dataLoaded.value = false
  } finally {
    loading.value = false
  }
}

const exportarExcel = () => {
  if (!dataLoaded.value) return

  const unidadSeleccionada = unidades.value.find((u) => String(u.id) === String(selectedUnidad.value))

  const wb = XLSX.utils.book_new()

  const portadaData = [
    ['Reporte', 'Producción Ejecutiva'],
    ['Fecha de exportación', new Date().toLocaleString()],
    ['Mes/Año', selectedMonth.value || '-'],
    ['Día', selectedDay.value || 'Último día con actividad'],
    ['Unidad de negocio', unidadSeleccionada?.nombre || '-'],
    ['Corte de información', periodoInfo.value.cutoff_date || '-'],
    [],
    ['KPI', 'Valor'],
    ['Producción real', totalProduccion.value],
    ['Producción esperada', produccionEsperada.value],
    ['Cumplimiento %', eficiencia.value],
    ['Stock ABC', stockAbcTotal.value],
  ]

  const wsPortada = XLSX.utils.aoa_to_sheet(portadaData)
  wsPortada['!cols'] = [{ wch: 30 }, { wch: 40 }]
  XLSX.utils.book_append_sheet(wb, wsPortada, 'Portada')

  const wsConsumo = XLSX.utils.json_to_sheet(
    tablaConsumo.value.map((x) => ({
      'Maquina (Equipo)': x.equipo,
      'Lts/Hora Dia': x.lts_hora_dia,
      'Lts/Hora Acumulado': x.lts_hora_acumulado,
      'Lts/m3 Dia': x.lts_m3_dia,
      'Lts/m3 Acumulado': x.lts_m3_acumulado,
    }))
  )
  XLSX.utils.book_append_sheet(wb, wsConsumo, 'Consumos')

  const wsProduccion = XLSX.utils.json_to_sheet(
    tablaProduccion.value.map((x) => ({
      'Maquina (Equipo)': x.equipo,
      'Unidad de Produccion': x.unidad_produccion,
      'Produccion Dia': x.produccion_dia,
      'Produccion Acumulada': x.produccion_acumulada,
      'Produccion/Hora Dia': x.produccion_hora_dia,
      'Produccion/Hora Acumulada': x.produccion_hora_acumulada,
      'Produccion/Arbol Dia': x.produccion_arbol_dia,
      'Produccion/Arbol Acumulada': x.produccion_arbol_acumulada,
    }))
  )
  XLSX.utils.book_append_sheet(wb, wsProduccion, 'Produccion')

  XLSX.writeFile(wb, `Produccion_Ejecutiva_${selectedMonth.value || 'reporte'}.xlsx`)
}

watch(selectedMonth, async () => {
  selectedDay.value = ''
  dataLoaded.value = false
  await cargarUnidadesActivas()
})

onMounted(async () => {
  const now = new Date()
  selectedMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  await cargarUnidadesActivas()
  if (selectedUnidad.value) {
    await buscarDatos()
  }
})
</script>
