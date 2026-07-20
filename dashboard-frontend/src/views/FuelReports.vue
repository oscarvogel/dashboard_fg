<template>
  <section class="min-h-screen bg-slate-100 p-4 md:p-8">
    <div class="mx-auto max-w-7xl">
      <header class="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide text-emerald-700">Forestal Paraguay</p>
          <h1 class="text-3xl font-bold text-slate-900">Cargas de combustible recibidas</h1>
          <p class="mt-1 text-slate-600">Revisión de datos extraídos de mensajes de Choferes FGPY.</p>
        </div>
        <div class="rounded-xl bg-amber-100 px-4 py-3 text-amber-900">
          <span class="text-2xl font-bold">{{ pendingCount }}</span>
          <span class="ml-2 text-sm">pendientes en esta página</span>
        </div>
      </header>

      <form class="mb-5 grid gap-3 rounded-2xl bg-white p-4 shadow-sm md:grid-cols-5" @submit.prevent="loadReports(1)">
        <input v-model="filters.date" type="date" class="rounded-lg border border-slate-300 px-3 py-2" aria-label="Fecha" />
        <select v-model="filters.vehicle" class="rounded-lg border border-slate-300 px-3 py-2" aria-label="Vehículo">
          <option value="">Todos los vehículos</option>
          <option v-for="item in vehicles" :key="item.id" :value="item.id">{{ item.description || item.original_plate }} · {{ statusLabelsCatalog[item.status] }}</option>
        </select>
        <select v-model="filters.driver" class="rounded-lg border border-slate-300 px-3 py-2" aria-label="Chofer">
          <option value="">Todos los choferes</option>
          <option v-for="item in drivers" :key="item.id" :value="item.id">{{ item.reported_name }} · {{ statusLabelsCatalog[item.status] }}</option>
        </select>
        <select v-model="filters.status" class="rounded-lg border border-slate-300 px-3 py-2" aria-label="Estado">
          <option value="">Todos los estados</option>
          <option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option>
        </select>
        <button class="rounded-lg bg-emerald-700 px-4 py-2 font-semibold text-white hover:bg-emerald-800">Aplicar filtros</button>
      </form>

      <div v-if="error" class="mb-4 rounded-xl bg-red-50 p-4 text-red-800">{{ error }}</div>
      <div v-if="loading" class="rounded-2xl bg-white p-12 text-center text-slate-500">Cargando cargas…</div>
      <div v-else-if="!reports.length" class="rounded-2xl bg-white p-12 text-center text-slate-500">No hay cargas para los filtros elegidos.</div>
      <div v-else class="overflow-hidden rounded-2xl bg-white shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-slate-900 text-white">
              <tr>
                <th class="p-3">Fecha</th><th class="p-3">Vehículo</th><th class="p-3">Chofer</th>
                <th class="p-3">Litros</th><th class="p-3">Odómetro</th><th class="p-3">Confianza</th>
                <th class="p-3">Estado</th><th class="p-3">Observaciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in reports" :key="report.id" class="cursor-pointer border-b border-slate-100 hover:bg-emerald-50" @click="openDetail(report.id)">
                <td class="p-3">{{ formatDate(report.event_at) }}</td>
                <td class="p-3 font-medium">{{ report.vehicle_display || 'Pendiente' }}</td>
                <td class="p-3">{{ report.driver_name || 'Pendiente' }}</td>
                <td class="p-3">{{ report.liters ?? 'Pendiente' }}</td>
                <td class="p-3">{{ report.odometer_total ?? 'Pendiente' }}</td>
                <td class="p-3">{{ confidence(report.overall_confidence) }}</td>
                <td class="p-3"><span class="rounded-full bg-slate-100 px-2 py-1">{{ statusLabels[report.status] }}</span></td>
                <td class="p-3 text-amber-800">{{ report.inconsistencies.map(issueLabel).join(', ') || 'Sin alertas' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="flex items-center justify-between p-4">
          <button :disabled="page === 1" class="rounded border px-3 py-1 disabled:opacity-40" @click="loadReports(page - 1)">Anterior</button>
          <span>Página {{ page }}</span>
          <button :disabled="!next" class="rounded border px-3 py-1 disabled:opacity-40" @click="loadReports(page + 1)">Siguiente</button>
        </div>
      </div>
    </div>

    <div v-if="selected" class="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 p-4" @click.self="closeDetail">
      <article class="mx-auto my-4 max-w-4xl rounded-2xl bg-white p-6 shadow-2xl">
        <div class="flex justify-between gap-4">
          <div><h2 class="text-2xl font-bold">Detalle de la carga</h2><p class="text-slate-500">{{ formatDate(selected.event_at) }}</p></div>
          <button class="text-2xl text-slate-500" aria-label="Cerrar" @click="closeDetail">×</button>
        </div>
        <div class="mt-5 grid gap-4 md:grid-cols-2">
          <label class="text-sm">Vehículo
            <select v-model="edit.vehicle" class="mt-1 w-full rounded border p-2"><option value="">Pendiente</option><option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.description || v.original_plate }} · {{ statusLabelsCatalog[v.status] }}</option></select>
          </label>
          <label class="text-sm">Chofer
            <select v-model="edit.driver" class="mt-1 w-full rounded border p-2"><option value="">Pendiente</option><option v-for="d in drivers" :key="d.id" :value="d.id">{{ d.reported_name }} · {{ statusLabelsCatalog[d.status] }}</option></select>
          </label>
          <label class="text-sm">Litros<input v-model="edit.liters" type="number" step="0.01" class="mt-1 w-full rounded border p-2" /></label>
          <label class="text-sm">Odómetro total<input v-model="edit.odometer_total" type="number" step="0.01" class="mt-1 w-full rounded border p-2" /></label>
        </div>
        <section class="mt-5 rounded-xl border border-slate-200 p-4">
          <h3 class="font-semibold">Catálogos Forestal Paraguay</h3>
          <p class="text-sm text-slate-500">Las propuestas nuevas quedan pendientes hasta confirmación humana.</p>
          <div class="mt-3 grid gap-3 md:grid-cols-2">
            <div class="space-y-2">
              <input v-model="newVehicle.original_plate" class="w-full rounded border p-2" placeholder="Patente informada" />
              <input v-model="newVehicle.description" class="w-full rounded border p-2" placeholder="Descripción legible" />
              <button class="rounded bg-slate-700 px-3 py-2 text-sm text-white" @click="createPendingCatalog('vehicle')">Crear vehículo pendiente</button>
              <button v-if="selectedVehicle" class="ml-2 rounded border border-blue-700 px-3 py-2 text-sm text-blue-800" @click="correctCatalog('vehicle', selectedVehicle.id)">Corregir seleccionado</button>
              <button v-if="selectedVehicle?.status === 'pending'" class="ml-2 rounded bg-emerald-700 px-3 py-2 text-sm text-white" @click="confirmCatalog('vehicle', selectedVehicle.id)">Confirmar seleccionado</button>
            </div>
            <div class="space-y-2">
              <input v-model="newDriver.reported_name" class="w-full rounded border p-2" placeholder="Nombre informado" />
              <button class="rounded bg-slate-700 px-3 py-2 text-sm text-white" @click="createPendingCatalog('driver')">Crear chofer pendiente</button>
              <button v-if="selectedDriver" class="ml-2 rounded border border-blue-700 px-3 py-2 text-sm text-blue-800" @click="correctCatalog('driver', selectedDriver.id)">Corregir seleccionado</button>
              <button v-if="selectedDriver?.status === 'pending'" class="ml-2 rounded bg-emerald-700 px-3 py-2 text-sm text-white" @click="confirmCatalog('driver', selectedDriver.id)">Confirmar seleccionado</button>
            </div>
          </div>
        </section>
        <div class="mt-5 rounded-xl bg-amber-50 p-4"><h3 class="font-semibold">Inconsistencias</h3><p>{{ selected.inconsistencies.map(issueLabel).join(', ') || 'Sin alertas' }}</p></div>
        <section class="mt-5"><h3 class="font-semibold">Mensajes fuente</h3>
          <div v-for="link in selected.source_messages" :key="link.id" class="mt-2 rounded-xl border p-3">
            <p class="text-xs uppercase text-slate-500">{{ link.role }} · {{ formatDate(link.message.timestamp) }}</p>
            <p class="font-medium">{{ link.message.sender_name || 'Remitente no identificado' }}</p>
            <p class="whitespace-pre-wrap">{{ link.message.body || 'Sin texto' }}</p>
            <p v-if="link.message.image_description" class="mt-2 text-sm text-slate-600">Análisis: {{ link.message.image_description }}</p>
          </div>
        </section>
        <section v-if="selected.evidence.length" class="mt-5"><h3 class="font-semibold">Fotografías y comprobantes</h3>
          <div class="mt-2 grid gap-3 md:grid-cols-2">
            <div v-for="item in selected.evidence" :key="item.id" class="rounded-xl border p-2">
              <img v-if="item.mime_type.startsWith('image/') && evidenceUrls[item.id]" :src="evidenceUrls[item.id]" class="max-h-72 w-full rounded object-contain" alt="Evidencia de la carga" />
              <a v-else-if="evidenceUrls[item.id]" :href="evidenceUrls[item.id]" target="_blank" class="text-emerald-700 underline">Abrir comprobante</a>
              <p class="mt-1 text-xs text-slate-500">{{ item.evidence_type }}</p>
            </div>
          </div>
        </section>
        <section class="mt-5"><h3 class="font-semibold">Historial de revisión</h3>
          <p v-if="!selected.revisions.length" class="text-slate-500">Todavía no hay revisiones.</p>
          <ul v-else class="mt-2 space-y-2"><li v-for="rev in selected.revisions" :key="rev.id" class="rounded border p-2 text-sm">{{ rev.created_at }} · {{ rev.user_name }} · {{ rev.field_name }}: {{ rev.previous_value }} → {{ rev.new_value }}</li></ul>
        </section>
        <label class="mt-5 block text-sm">Motivo o nota de revisión<textarea v-model="reason" class="mt-1 w-full rounded border p-2" rows="2"></textarea></label>
        <div v-if="detailError" class="mt-3 rounded bg-red-50 p-3 text-red-800">{{ detailError }}</div>
        <div class="mt-5 flex flex-wrap gap-3">
          <button class="rounded bg-blue-700 px-4 py-2 text-white" @click="review('correct')">Guardar corrección</button>
          <button class="rounded bg-emerald-700 px-4 py-2 text-white" @click="review('confirm')">Confirmar</button>
          <button class="rounded bg-red-700 px-4 py-2 text-white" @click="review('reject')">Rechazar</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../services/api'

const reports = ref([]), vehicles = ref([]), drivers = ref([])
const selected = ref(null), loading = ref(false), error = ref(''), detailError = ref('')
const page = ref(1), next = ref(null), reason = ref('')
const evidenceUrls = reactive({})
const filters = reactive({ date: '', vehicle: '', driver: '', status: '' })
const edit = reactive({ vehicle: '', driver: '', liters: '', odometer_total: '' })
const newVehicle = reactive({ original_plate: '', description: '' })
const newDriver = reactive({ reported_name: '' })
const statusLabels = { received: 'Recibida', requires_review: 'Requiere revisión', confirmed: 'Confirmada', corrected: 'Corregida', rejected: 'Rechazada' }
const statusLabelsCatalog = { pending: 'Pendiente', confirmed: 'Confirmado', inactive: 'Inactivo' }
const selectedVehicle = computed(() => vehicles.value.find(item => item.id === edit.vehicle))
const selectedDriver = computed(() => drivers.value.find(item => item.id === edit.driver))
const issueLabels = {
  missing_vehicle: 'Falta vehículo', missing_liters: 'Faltan litros', missing_odometer: 'Falta odómetro',
  low_confidence_vehicle: 'Vehículo dudoso', low_confidence_liters: 'Litros dudosos',
  low_confidence_odometer: 'Odómetro dudoso', odometer_regression: 'Odómetro menor al anterior',
  duplicate_receipt: 'Comprobante repetido', duplicate_evidence: 'Evidencia repetida',
  possible_duplicate_fuel_event: 'Posible carga repetida', event_date_mismatch: 'Fecha a revisar',
  possible_capacity_exceeded: 'Cantidad a revisar'
}
const pendingCount = computed(() => reports.value.filter(item => item.status === 'requires_review').length)
const issueLabel = code => issueLabels[code] || code
const formatDate = value => value ? new Date(value).toLocaleString('es-AR') : 'Pendiente'
const confidence = value => value == null ? 'Sin dato' : `${Math.round(Number(value) * 100)}%`

async function loadCatalogs() {
  const [vehicleResponse, driverResponse] = await Promise.all([
    api.get('api/bot/fgpy-vehicles/', { params: { active: true } }),
    api.get('api/bot/fgpy-drivers/', { params: { active: true } })
  ])
  vehicles.value = vehicleResponse.data
  drivers.value = driverResponse.data
}
async function createPendingCatalog(kind) {
  detailError.value = ''
  try {
    const isVehicle = kind === 'vehicle'
    const payload = {
      organization_key: 'forestal-paraguay',
      ...(isVehicle ? newVehicle : newDriver)
    }
    const response = await api.post(`api/bot/fgpy-${isVehicle ? 'vehicles' : 'drivers'}/`, payload)
    await loadCatalogs()
    edit[isVehicle ? 'vehicle' : 'driver'] = response.data.id
    if (isVehicle) Object.assign(newVehicle, { original_plate: '', description: '' })
    else newDriver.reported_name = ''
  } catch (err) { detailError.value = JSON.stringify(err.response?.data || 'No se pudo crear la entrada pendiente.') }
}
async function confirmCatalog(kind, id) {
  detailError.value = ''
  try {
    await api.patch(`api/bot/fgpy-${kind === 'vehicle' ? 'vehicles' : 'drivers'}/${id}/`, { action: 'confirm', confirmed_aliases: [] })
    await loadCatalogs()
  } catch (err) { detailError.value = JSON.stringify(err.response?.data || 'No se pudo confirmar la entrada.') }
}
async function correctCatalog(kind, id) {
  detailError.value = ''
  try {
    const changes = kind === 'vehicle'
      ? Object.fromEntries(Object.entries(newVehicle).filter(([, value]) => value.trim()))
      : Object.fromEntries(Object.entries(newDriver).filter(([, value]) => value.trim()))
    if (!Object.keys(changes).length) throw new Error('Ingresá al menos un dato corregido.')
    await api.patch(`api/bot/fgpy-${kind === 'vehicle' ? 'vehicles' : 'drivers'}/${id}/`, { action: 'correct', changes })
    await loadCatalogs()
  } catch (err) { detailError.value = err.response ? JSON.stringify(err.response.data) : err.message }
}
async function loadReports(target = 1) {
  loading.value = true; error.value = ''
  try {
    const params = { page: target, organization_key: 'forestal-paraguay', origin_group_key: 'choferes-fgpy' }
    Object.entries(filters).forEach(([key, value]) => { if (value) params[key] = value })
    const response = await api.get('api/bot/fuel-reports/', { params })
    reports.value = response.data.results; page.value = target; next.value = response.data.next
  } catch (err) { error.value = err.response?.data?.detail || 'No se pudieron cargar las cargas.' }
  finally { loading.value = false }
}
async function openDetail(id) {
  detailError.value = ''
  const response = await api.get(`api/bot/fuel-reports/${id}/`)
  selected.value = response.data
  Object.assign(edit, { vehicle: selected.value.vehicle || '', driver: selected.value.driver || '', liters: selected.value.liters ?? '', odometer_total: selected.value.odometer_total ?? '' })
  for (const item of selected.value.evidence) {
    const file = await api.get(item.download_url, { responseType: 'blob' })
    evidenceUrls[item.id] = URL.createObjectURL(file.data)
  }
}
function closeDetail() {
  Object.values(evidenceUrls).forEach(URL.revokeObjectURL)
  Object.keys(evidenceUrls).forEach(key => delete evidenceUrls[key])
  selected.value = null
}
async function review(action) {
  detailError.value = ''
  const payload = { action, reason: reason.value }
  if (action === 'correct') payload.changes = {
    vehicle: edit.vehicle || null, driver: edit.driver || null,
    liters: edit.liters === '' ? null : edit.liters,
    odometer_total: edit.odometer_total === '' ? null : edit.odometer_total
  }
  try {
    const response = await api.patch(`api/bot/fuel-reports/${selected.value.id}/`, payload)
    selected.value = response.data; reason.value = ''; await loadReports(page.value)
  } catch (err) { detailError.value = JSON.stringify(err.response?.data || 'No se pudo completar la revisión.') }
}
onMounted(async () => {
  try { await Promise.all([loadCatalogs(), loadReports()]) }
  catch { error.value = 'No se pudieron cargar los catálogos.' }
})
</script>
