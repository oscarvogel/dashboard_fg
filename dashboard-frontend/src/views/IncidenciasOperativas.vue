<template>
  <div class="min-h-screen bg-slate-50">
    <NavBar />
    <main class="mx-auto max-w-7xl px-4 py-8">
      <div class="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide text-emerald-700">Control operativo</p>
          <h1 class="text-3xl font-bold text-slate-900">Incidencias</h1>
          <p class="mt-1 text-slate-600">Equipos y personal, con el grupo de WhatsApp que originó cada registro.</p>
        </div>
        <div class="flex gap-3">
          <select v-model="estado" class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" @change="cargar">
            <option value="true">Abiertas</option>
            <option value="false">Cerradas</option>
            <option value="">Todas</option>
          </select>
          <select v-model="grupo" class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" @change="cargar">
            <option value="">Todos los grupos</option>
            <option v-for="nombre in grupos" :key="nombre" :value="nombre">{{ nombre }}</option>
          </select>
        </div>
      </div>

      <div v-if="error" class="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{{ error }}</div>
      <div v-if="cargando" class="py-16 text-center text-slate-500">Cargando incidencias…</div>
      <template v-else>
        <section class="mb-8 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div class="border-b border-slate-200 px-5 py-4"><h2 class="font-semibold text-slate-900">Equipos ({{ equiposFiltrados.length }})</h2></div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-xs uppercase text-slate-500"><tr><th class="px-5 py-3">Equipo</th><th class="px-5 py-3">Incidencia</th><th class="px-5 py-3">Grupo de origen</th><th class="px-5 py-3">Inicio</th><th class="px-5 py-3">Estado</th></tr></thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="item in equiposFiltrados" :key="`e-${item.id}`"><td class="px-5 py-4 font-medium text-slate-900">{{ item.equipo_nombre }}</td><td class="max-w-lg px-5 py-4 text-slate-700">{{ item.descripcion }}</td><td class="px-5 py-4"><span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">{{ item.grupo_origen_nombre }}</span></td><td class="px-5 py-4 text-slate-600">{{ fecha(item.inicio) }}</td><td class="px-5 py-4"><span :class="item.abierta ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'" class="rounded-full px-2.5 py-1 text-xs font-semibold">{{ item.abierta ? 'Abierta' : 'Cerrada' }}</span></td></tr>
                <tr v-if="!equiposFiltrados.length"><td colspan="5" class="px-5 py-10 text-center text-slate-500">Sin incidencias de equipos para este filtro.</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div class="border-b border-slate-200 px-5 py-4"><h2 class="font-semibold text-slate-900">Personal ({{ personasFiltradas.length }})</h2></div>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-xs uppercase text-slate-500"><tr><th class="px-5 py-3">Persona</th><th class="px-5 py-3">Motivo</th><th class="px-5 py-3">Grupo de origen</th><th class="px-5 py-3">Fecha</th><th class="px-5 py-3">Estado</th></tr></thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="item in personasFiltradas" :key="`p-${item.id}`"><td class="px-5 py-4 font-medium text-slate-900">{{ item.persona_nombre }}</td><td class="max-w-lg px-5 py-4 text-slate-700">{{ item.motivo }}</td><td class="px-5 py-4"><span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">{{ item.grupo_origen_nombre }}</span></td><td class="px-5 py-4 text-slate-600">{{ item.fecha }}</td><td class="px-5 py-4"><span :class="item.abierta ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'" class="rounded-full px-2.5 py-1 text-xs font-semibold">{{ item.abierta ? 'Abierta' : 'Cerrada' }}</span></td></tr>
                <tr v-if="!personasFiltradas.length"><td colspan="5" class="px-5 py-10 text-center text-slate-500">Sin incidencias de personal para este filtro.</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import api from '../services/api'

const equipos = ref([])
const personas = ref([])
const estado = ref('true')
const grupo = ref('')
const cargando = ref(false)
const error = ref('')
const grupos = computed(() => [...new Set([...equipos.value, ...personas.value].map(x => x.grupo_origen_nombre).filter(Boolean))].sort())
const equiposFiltrados = computed(() => grupo.value ? equipos.value.filter(x => x.grupo_origen_nombre === grupo.value) : equipos.value)
const personasFiltradas = computed(() => grupo.value ? personas.value.filter(x => x.grupo_origen_nombre === grupo.value) : personas.value)
const fecha = value => value ? new Intl.DateTimeFormat('es-AR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—'

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const params = estado.value === '' ? {} : { abierta: estado.value }
    const { data } = await api.get('api/incidencias/dashboard/', { params })
    equipos.value = data.equipos || []
    personas.value = data.personas || []
  } catch (_) {
    error.value = 'No se pudieron cargar las incidencias.'
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>
