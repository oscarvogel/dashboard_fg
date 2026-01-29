<template>
  <div class="min-h-screen bg-primary-50 py-8 px-4 sm:px-6 lg:px-8">
    <div class="max-w-6xl mx-auto">
      <h1 class="text-2xl font-extrabold text-gray-900 mb-6">KPIs de los Choferes</h1>

      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha desde</label>
            <input v-model="startDate" type="date" class="w-full border-gray-300 rounded-md p-2" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha hasta</label>
            <input v-model="endDate" type="date" class="w-full border-gray-300 rounded-md p-2" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Chofer</label>
            <select v-model="selectedChofer" class="w-full border-gray-300 rounded-md p-2">
              <option value="">Todos</option>
              <option v-for="op in operadores" :key="op" :value="op">{{ op }}</option>
            </select>
          </div>
        </div>
        <div class="mt-4 flex items-center gap-3">
          <button @click="buscar" :disabled="loading" class="bg-primary-600 text-white px-4 py-2 rounded-md">{{ loading ? 'Cargando...' : 'Buscar' }}</button>
          <button @click="reset" class="bg-gray-200 px-4 py-2 rounded-md">Limpiar</button>
          <button @click="exportExcel" :disabled="loading || registros.length===0" class="bg-emerald-600 text-white px-4 py-2 rounded-md">Exportar Excel</button>
        </div>
      </div>

      <div v-if="!loaded && !loading" class="text-gray-500">Seleccione filtros y presione Buscar.</div>

      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin h-8 w-8 border-b-2 border-primary-600 rounded-full mx-auto"></div>
      </div>

      <div v-if="loaded && !loading">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div class="flex items-center justify-center gap-3">
              <svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 12h3l3-8 4 16 3-8h4"/></svg>
              <div>
                <h4 class="text-sm text-gray-500">Horas (mes)</h4>
                <div class="text-xl font-bold text-primary-700 mt-2">{{ formatNumber(totalKm) }} h</div>
              </div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div class="flex items-center justify-center gap-3">
              <svg class="kpi-icon-emerald" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7h18M3 12h18M3 17h18"/></svg>
              <div>
                <h4 class="text-sm text-gray-500">TN transportadas (mes)</h4>
                <div class="text-xl font-bold text-primary-700 mt-2">{{ formatNumber(totalTN) }} TN</div>
              </div>
            </div>
          </div>

          

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div class="flex items-center justify-center gap-3">
              <svg class="kpi-icon-red" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 12h3l3-8 4 16 3-8h4"/></svg>
              <div>
                <h4 class="text-sm text-gray-500">Consumo total</h4>
                <div class="text-xl font-bold text-primary-700 mt-2">{{ formatNumber(totalCombustible) }} L</div>
              </div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div class="flex items-center justify-center gap-3">
              <svg class="kpi-icon-indigo" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 10h18M3 6h18M3 14h12"/></svg>
              <div>
                <h4 class="text-sm text-gray-500">Consumo por km</h4>
                <div class="text-xl font-bold text-primary-700 mt-2">{{ consumoPorKm }}</div>
              </div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">Consumo / 100 km</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ consumo100km }}</div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">Viajes realizados</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ viajes }}</div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">Km por viaje</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ kmPorViaje }}</div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">TN por viaje</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ tnPorViaje }}</div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">Horas trabajadas (mes)</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ formatNumber(horasTrabajadas) }} h</div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">TN / h</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ tnPorHora }}</div>
            </div>
          </div>

          <div class="kpi-card p-4 rounded-xl shadow text-center transform transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
            <div>
              <h4 class="text-sm text-gray-500">Eficiencia (TN/L)</h4>
              <div class="text-xl font-bold text-primary-700 mt-2">{{ eficiencia }}</div>
            </div>
          </div>
        </div>

        <!-- Filtro y paginado -->
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
          <div class="flex items-center gap-3">
            <input v-model="filterText" placeholder="Filtrar por chofer/operación/fecha" class="px-3 py-2 border border-gray-200 rounded-md w-64" />
            <select v-model.number="pageSize" class="px-3 py-2 border border-gray-200 rounded-md">
              <option v-for="s in pageSizes" :key="s" :value="s">Mostrar {{ s }}</option>
            </select>
          </div>
          <div class="text-sm text-gray-500">Mostrando {{ startItem }} - {{ endItem }} de {{ totalCount }}</div>
        </div>

        <!-- Tabla simple de registros -->
        <div class="bg-white shadow rounded-lg overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="table-header">
              <tr>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Fecha</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Unidad de Negocios</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Nº Remito Bitren</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Patente Camión</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Origen / Destino</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">TN (Producción)</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Hr Inicio</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Hr Fin</th>
                <th class="px-4 py-2 text-left text-xs text-gray-500">Combustible (L)</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-100">
              <tr v-for="r in registros" :key="r.id || r.fecha + r.operacion" class="hover:bg-primary-50 transition-colors duration-150">
                <td class="px-4 py-2 text-sm text-gray-800">{{ formatDate(r.fecha) }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.unidad_negocio_detalle || r.UN || '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.remito_bitren || r.remito || r.acta || '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.equipo_patente || r.movil_patente || '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ (r.predio || r.origen || r.destino) ? [r.predio, r.origen, r.destino].filter(Boolean).join(' / ') : '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.produccion || r.tn_despachadas || '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.hr_inicio !== undefined ? r.hr_inicio : '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.hr_fin !== undefined ? r.hr_fin : '-' }}</td>
                <td class="px-4 py-2 text-sm text-gray-800">{{ r.combustible || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Controles de paginado -->
        <div class="flex items-center justify-between mt-3">
          <div class="flex items-center gap-2">
            <button @click="prevPage" :disabled="page <= 1" class="px-3 py-1 bg-gray-100 rounded-md disabled:opacity-50">Anterior</button>
            <button @click="nextPage" :disabled="page >= totalPages" class="px-3 py-1 bg-gray-100 rounded-md disabled:opacity-50">Siguiente</button>
          </div>
          <div class="text-sm text-gray-500">Página {{ page }} / {{ totalPages }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../services/api'
import * as XLSX from 'xlsx'

// default date range: last 30 days to today
const _today = new Date()
const _endDefault = _today.toISOString().slice(0, 10)
const _start = new Date(_today)
_start.setDate(_start.getDate() - 30)
const _startDefault = _start.toISOString().slice(0, 10)

const startDate = ref(_startDefault)
const endDate = ref(_endDefault)
const operadores = ref([])
const selectedChofer = ref('')
const registros = ref([])
const loading = ref(false)
const loaded = ref(false)

const OPERATION_FILTER = 'TRANSPORTE'

const totalCount = ref(0)

let debounceTimer = null

const buscar = async (opts = {}) => {
  loading.value = true
  loaded.value = false
  try {
    const params = new URLSearchParams()
    if (startDate.value) params.append('start_date', startDate.value)
    if (endDate.value) params.append('end_date', endDate.value)
    if (selectedChofer.value) params.append('operador', selectedChofer.value)
    // Filtrar solo operaciones de transporte
    params.append('operacion', OPERATION_FILTER)

    // backend paging & filtering
    params.append('page', page.value)
    params.append('page_size', pageSize.value)

    // If user typed a free-text filter, try sending it as `operador` if it matches known operadores, otherwise as `search`
    if (filterText.value) {
      const q = filterText.value.toString().trim()
      const match = operadores.value.find(o => o.toString().toLowerCase() === q.toLowerCase())
      if (match) params.set('operador', match)
      else params.append('search', q)
    }

    const res = await api.get('/api/produccion-dashboard/', { params })
    // Expecting paginated response: { results: [...], count: N }
    registros.value = res.data.results || res.data || []
    totalCount.value = res.data.count != null ? res.data.count : registros.value.length
    loaded.value = true
  } catch (e) {
    console.error(e)
    registros.value = []
    totalCount.value = 0
    loaded.value = false
  } finally {
    loading.value = false
  }
}

const reset = () => {
  // restore default 30-day range
  startDate.value = _startDefault
  endDate.value = _endDefault
  selectedChofer.value = ''
  registros.value = []
  loaded.value = false
}

const loadOperadores = async () => {
  try {
    const params = new URLSearchParams()
    // si hay fechas, pasar para obtener operadores disponibles en ese rango
    if (startDate.value) params.append('start_date', startDate.value)
    if (endDate.value) params.append('end_date', endDate.value)
    // pedir solo operadores asociados a TRANSPORTE
    params.append('operacion', OPERATION_FILTER)

    const res = await api.get('/api/filtros/', { params })
    operadores.value = res.data.operadores || res.data.operador || []
  } catch (e) {
    console.error('Error cargando operadores', e)
    operadores.value = []
  }
}

onMounted(() => {
  loadOperadores()
  // load initial page
  buscar()
})

// Cuando cambian las fechas, recargar operadores disponibles para ese rango
watch([startDate, endDate], ([ns, ne]) => {
  if (ns || ne) loadOperadores()
  // when date range changes, reset page and search
  page.value = 1
  buscar()
})

const sumField = (fieldNames) => {
  return registros.value.reduce((s, r) => {
    for (const f of fieldNames) {
      const v = parseFloat(r[f])
      if (!isNaN(v)) return s + v
    }
    return s
  }, 0)
}

// Total km: usar la propiedad `horas_del_dia` del registro (o calcular hr_fin-hr_inicio si no existe)
const horasDelRegistro = (r) => {
  const v = parseFloat(r.horas_del_dia)
  if (!isNaN(v)) return v
  const hi = parseFloat(r.hr_inicio)
  const hf = parseFloat(r.hr_fin)
  if (!isNaN(hi) && !isNaN(hf) && hf >= hi) return hf - hi
  return 0
}

const totalKm = computed(() => {
  return registros.value.reduce((s, r) => s + horasDelRegistro(r), 0)
})
// TN transportadas: usar únicamente el campo `produccion`
const totalTN = computed(() => {
  return registros.value.reduce((s, r) => {
    const v = parseFloat(r.produccion)
    return s + (isNaN(v) ? 0 : v)
  }, 0)
})
const totalCombustible = computed(() => sumField(['combustible']))
const viajes = computed(() => registros.value.length)

const horasTrabajadas = computed(() => {
  return registros.value.reduce((sum, r) => {
    const hi = parseFloat(r.hr_inicio)
    const hf = parseFloat(r.hr_fin)
    if (!isNaN(hi) && !isNaN(hf) && hf >= hi) return sum + (hf - hi)
    return sum
  }, 0)
})

const consumoPorKm = computed(() => {
  const km = totalKm.value
  const comb = totalCombustible.value
  if (km === 0) return '-'
  return (comb / km).toFixed(3) + ' L/km'
})

// Server-side filtering & pagination state
const filterText = ref('')
const page = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 25, 50]

const nextPage = async () => { if (page.value < totalPages.value) { page.value += 1; await buscar() } }
const prevPage = async () => { if (page.value > 1) { page.value -= 1; await buscar() } }

const totalPages = computed(() => Math.max(1, Math.ceil((totalCount.value || 0) / pageSize.value)))
const startItem = computed(() => totalCount.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1)
const endItem = computed(() => Math.min(totalCount.value, page.value * pageSize.value))

// debounce filterText -> trigger buscar
watch(filterText, (nv) => {
  page.value = 1
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => buscar(), 400)
})

// when page size changes, reset page and fetch
watch(pageSize, (nv) => { page.value = 1; buscar() })

const horasDelDiaDisplay = (r) => {
  const v = r.horas_del_dia !== undefined ? parseFloat(r.horas_del_dia) : NaN
  if (!isNaN(v)) return (Math.round((v + Number.EPSILON) * 100) / 100).toLocaleString() + ' h'
  const hi = parseFloat(r.hr_inicio)
  const hf = parseFloat(r.hr_fin)
  if (!isNaN(hi) && !isNaN(hf) && hf >= hi) return ((hf - hi).toFixed(2)).toString() + ' h'
  return '-'
}

const consumo100km = computed(() => {
  const km = totalKm.value
  const comb = totalCombustible.value
  if (km === 0) return '-'
  return ((comb / km) * 100).toFixed(2) + ' L/100km'
})

const kmPorViaje = computed(() => {
  return viajes.value === 0 ? '-' : (totalKm.value / viajes.value).toFixed(1) + ' km'
})

const tnPorViaje = computed(() => {
  return viajes.value === 0 ? '-' : (totalTN.value / viajes.value).toFixed(2) + ' TN'
})

const tnPorHora = computed(() => {
  return horasTrabajadas.value === 0 ? '-' : (totalTN.value / horasTrabajadas.value).toFixed(2) + ' TN/h'
})

const eficiencia = computed(() => {
  return totalCombustible.value === 0 ? '-' : (totalTN.value / totalCombustible.value).toFixed(3) + ' TN/L'
})

const formatNumber = (v) => {
  return (Math.round((v + Number.EPSILON) * 100) / 100).toLocaleString()
}

const formatDate = (d) => {
  if (!d) return '-'
  // accept Date or ISO string
  const dt = typeof d === 'string' ? new Date(d) : d
  if (Number.isNaN(dt.getTime && dt.getTime())) return d
  const day = String(dt.getDate()).padStart(2, '0')
  const month = String(dt.getMonth() + 1).padStart(2, '0')
  const year = dt.getFullYear()
  return `${day}-${month}-${year}`
}

const exportExcel = () => {
  const parseNum = (v) => {
    const n = parseFloat(v)
    return isNaN(n) ? null : n
  }

  const rows = registros.value.map(r => ({
    Fecha: formatDate(r.fecha),
    'Unidad de Negocio': r.unidad_negocio_detalle || r.UN || null,
    'Nro Remito Bitren': r.remito_bitren || r.remito || r.acta || null,
    'Patente Camión': r.equipo_patente || r.movil_patente || null,
    'Origen / Destino': (r.predio || r.origen || r.destino) ? [r.predio, r.origen, r.destino].filter(Boolean).join(' / ') : null,
    'TN (Producción)': parseNum(r.produccion || r.tn_despachadas),
    'Hr Inicio': parseNum(r.hr_inicio),
    'Hr Fin': parseNum(r.hr_fin),
    'Combustible (L)': parseNum(r.combustible)
  }))

  const ws = XLSX.utils.json_to_sheet(rows, {raw: false})
  // set reasonable column widths
  ws['!cols'] = [{wch:12},{wch:20},{wch:18},{wch:15},{wch:25},{wch:12},{wch:10},{wch:10},{wch:14}]
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Registros')
  XLSX.writeFile(wb, `KPIs_Choferes_${new Date().toISOString().slice(0,10)}.xlsx`)
}

</script>

<style scoped>
.card-value { font-size: 1.25rem; font-weight: 700 }

.kpi-card {
  background: #ffffff;
  position: relative;
  overflow: hidden;
}
.kpi-card::after {
  content: '';
  position: absolute;
  right: -48px;
  top: -48px;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(34,197,94,0.18) 0%, rgba(34,197,94,0.08) 35%, rgba(34,197,94,0.03) 55%, transparent 60%);
  pointer-events: none;
}
.kpi-icon, .kpi-icon-emerald, .kpi-icon-red, .kpi-icon-indigo {
  width: 40px;
  height: 40px;
}
.kpi-icon { color: transparent; background: linear-gradient(135deg,#34d399,#059669); -webkit-background-clip: text; background-clip: text; }
.kpi-icon-emerald { color: transparent; background: linear-gradient(135deg,#86efac,#16a34a); -webkit-background-clip: text; background-clip: text; }
.kpi-icon-red { color: transparent; background: linear-gradient(135deg,#feb2b2,#f56565); -webkit-background-clip: text; background-clip: text; }
.kpi-icon-indigo { color: transparent; background: linear-gradient(135deg,#c7d2fe,#4f46e5); -webkit-background-clip: text; background-clip: text; }

.table-header {
  background: linear-gradient(90deg, rgba(16,185,129,0.04), rgba(34,197,94,0.02));
}

.kpi-card .text-primary-700 { color: #166534; }

</style>
