<template>
  <div class="container mx-auto px-4 py-6">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Resumen de Máquinas y Componentes</h2>

    <!-- Filtros de fecha -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Inicio</label>
          <input
            type="date"
            v-model="fechaInicio"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha Fin</label>
          <input
            type="date"
            v-model="fechaFin"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
          />
        </div>
        <div class="flex items-end">
          <button
            @click="cargarDatos"
            :disabled="cargando || !fechaInicio || !fechaFin"
            class="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition duration-150 ease-in-out flex items-center justify-center"
          >
            <svg v-if="cargando" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ cargando ? 'Cargando...' : 'Consultar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Estadísticas resumen -->
    <div v-if="datos.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5"></path>
              </svg>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 truncate">Total Máquinas</dt>
              <dd class="text-lg font-medium text-gray-900">{{ totalMaquinas }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 truncate">Total Horas</dt>
              <dd class="text-lg font-medium text-gray-900">{{ totalHoras }}h</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
              </svg>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 truncate">Total Cadenas</dt>
              <dd class="text-lg font-medium text-gray-900">{{ totalCadenas }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
              </svg>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 truncate">Total m³</dt>
              <dd class="text-lg font-medium text-gray-900">{{ totalM3 }}</dd>
            </dl>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
              </svg>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 truncate">Aceite Cadena</dt>
              <dd class="text-lg font-medium text-gray-900">{{ totalAceiteCadena }}L</dd>
            </dl>
          </div>
        </div>
      </div>

      <!-- Tarjeta única de Total Cambios -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.5 12.75l6 6 9-13.5"></path>
              </svg>
            </div>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl>
              <dt class="text-sm font-medium text-gray-500 truncate">Total Cambios</dt>
              <dd class="text-lg font-medium text-gray-900">{{ totalCambiosComponentes }}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <!-- Cards de equipos -->
    <div>
      <div class="mb-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900">
          Máquinas con Cambios de Componentes
        </h3>
        <p class="mt-1 text-sm text-gray-500">
          Solo se muestran equipos que tuvieron cambios de espada, puntera, piñón o giro piñón en el período seleccionado
        </p>
      </div>

      <!-- Loading overlay -->
      <div v-if="cargando" class="flex items-center justify-center py-12">
        <div class="text-center">
          <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-gray-500 text-sm">Cargando datos...</p>
        </div>
      </div>

      <!-- Mensaje sin datos -->
      <div v-else-if="datos.length === 0" class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Sin cambios de componentes</h3>
        <p class="mt-1 text-sm text-gray-500">No se encontraron máquinas con cambios de espada, puntera, piñón o giro piñón en el rango de fechas seleccionado.</p>
      </div>

      <!-- Grid de cards -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="(item, index) in datos"
          :key="index"
          class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden"
        >
          <!-- Header del card -->
          <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-bold text-white">{{ item.maquina }}</h3>
                <p class="text-blue-100 text-sm">{{ item.patente }}</p>
              </div>
              <div class="bg-white/20 rounded-full p-3">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
                </svg>
              </div>
            </div>
          </div>

          <!-- Contenido del card -->
          <div class="p-6">
            <!-- Información general -->
            <div class="mb-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-600">Unidad de Negocio</span>
                <span class="text-sm text-gray-900">{{ item.unidad_negocio }}</span>
              </div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-600">Cadenas Utilizadas</span>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {{ item.cantidad_cadenas_utilizadas }}
                </span>
              </div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-600">Última Hr Registrada</span>
                <span class="text-sm font-mono text-gray-900">{{ item.ultima_hr_registrada }}h</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-600">Total Horas Trabajadas</span>
                <span class="text-sm font-bold text-gray-900">{{ item.total_horas_trabajadas }}h</span>
              </div>
            </div>

            <!-- Divisor -->
            <div class="border-t border-gray-200 my-4"></div>

            <!-- Métricas de producción -->
            <div class="mb-4">
              <h4 class="text-sm font-semibold text-gray-700 mb-3">Métricas de Producción</h4>
              <div class="grid grid-cols-2 gap-3">
                <div class="bg-gray-50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 mb-1">Total m³</div>
                  <div class="text-lg font-bold text-blue-600">{{ item.total_m3 || 0 }}</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 mb-1">Rendimiento/Cadena M3</div>
                  <div class="text-lg font-bold text-green-600">
                    {{ item.cantidad_cadenas_utilizadas > 0 ? (item.total_m3 / item.cantidad_cadenas_utilizadas).toFixed(2) : '0.00' }}
                  </div>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 mb-1">Aceite Cadena</div>
                  <div class="text-lg font-bold text-orange-600">{{ (item.total_aceite_cadena || 0).toFixed(1) }}L</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 mb-1">m³ desde Último Cambio</div>
                  <div class="text-sm">
                    <div v-if="item.m3_desde_ultimo_cambio_espada > 0" class="text-green-600">
                      Espada: {{ item.m3_desde_ultimo_cambio_espada }}
                    </div>
                    <div v-if="item.m3_desde_ultimo_cambio_puntera > 0" class="text-yellow-600">
                      Puntera: {{ item.m3_desde_ultimo_cambio_puntera }}
                    </div>
                    <div v-if="item.m3_desde_ultimo_cambio_pinon > 0" class="text-purple-600">
                      Piñón: {{ item.m3_desde_ultimo_cambio_pinon }}
                    </div>
                    <div v-if="!item.m3_desde_ultimo_cambio_espada && !item.m3_desde_ultimo_cambio_puntera && !item.m3_desde_ultimo_cambio_pinon" class="text-gray-400 text-xs">
                      Sin datos
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Divisor -->
            <div class="border-t border-gray-200 my-4"></div>

            <!-- Cambios de componentes -->
            <div>
              <h4 class="text-sm font-semibold text-gray-700 mb-3">Últimos Cambios de Componentes</h4>
              <div class="space-y-2">
                <!-- Espada -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span class="text-sm text-gray-600">Espada</span>
                  </div>
                  <span v-if="item.ultima_hr_cambio_espada" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {{ item.ultima_hr_cambio_espada }}h
                  </span>
                  <span v-else class="text-xs text-gray-400">Sin cambios</span>
                </div>

                <!-- Puntera -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <div class="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span class="text-sm text-gray-600">Puntera</span>
                  </div>
                  <span v-if="item.ultima_hr_cambio_puntera" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    {{ item.ultima_hr_cambio_puntera }}h
                  </span>
                  <span v-else class="text-xs text-gray-400">Sin cambios</span>
                </div>

                <!-- Piñón -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <div class="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                    <span class="text-sm text-gray-600">Piñón</span>
                  </div>
                  <span v-if="item.ultima_hr_cambio_pinon" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    {{ item.ultima_hr_cambio_pinon }}h
                  </span>
                  <span v-else class="text-xs text-gray-400">Sin cambios</span>
                </div>

                <!-- Giro Piñón -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <div class="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                    <span class="text-sm text-gray-600">Giro Piñón</span>
                  </div>
                  <span v-if="item.ultima_hr_cambio_giro_pinon" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    {{ item.ultima_hr_cambio_giro_pinon }}h
                  </span>
                  <span v-else class="text-xs text-gray-400">Sin cambios</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'

// Variables reactivas
const fechaInicio = ref('')
const fechaFin = ref('')
const datos = ref([])
const cargando = ref(false)

// Computed properties para estadísticas
const totalMaquinas = computed(() => datos.value.length)

const totalHoras = computed(() => {
  return datos.value.reduce((sum, item) => sum + item.total_horas_trabajadas, 0).toFixed(1)
})

const totalCadenas = computed(() => {
  return datos.value.reduce((sum, item) => sum + item.cantidad_cadenas_utilizadas, 0)
})

const totalCambiosComponentes = computed(() => {
  return datos.value.reduce((total, item) => {
    let cambios = 0
    if (item.ultima_hr_cambio_espada !== null) cambios++
    if (item.ultima_hr_cambio_puntera !== null) cambios++
    if (item.ultima_hr_cambio_pinon !== null) cambios++
    if (item.ultima_hr_cambio_giro_pinon !== null) cambios++
    return total + cambios
  }, 0)
})

const totalM3 = computed(() => {
  return datos.value.reduce((sum, item) => sum + (item.total_m3 || 0), 0)
})

const totalAceiteCadena = computed(() => {
  return datos.value.reduce((sum, item) => sum + (item.total_aceite_cadena || 0), 0).toFixed(2)
})

// Inicialización
onMounted(() => {
  // Establecer fechas por defecto (últimos 30 días)
  const hoy = new Date()
  const hace30Dias = new Date()
  hace30Dias.setDate(hoy.getDate() - 30)

  fechaFin.value = hoy.toISOString().split('T')[0]
  fechaInicio.value = hace30Dias.toISOString().split('T')[0]
})

// Función para cargar datos
async function cargarDatos() {
  if (!fechaInicio.value || !fechaFin.value) {
    alert('Por favor seleccione ambas fechas')
    return
  }

  try {
    cargando.value = true

    const response = await api.get('/api/resumen-maquinas-componentes/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value
      }
    })

    // Filtrar solo máquinas que tengan al menos un cambio de componente
    const datosFiltrados = response.data.data?.filter(item =>
      item.ultima_hr_cambio_espada !== null ||
      item.ultima_hr_cambio_puntera !== null ||
      item.ultima_hr_cambio_pinon !== null ||
      item.ultima_hr_cambio_giro_pinon !== null
    ) || []

    datos.value = datosFiltrados

    if (datos.value.length === 0) {
      console.log('No se encontraron datos para el rango de fechas seleccionado')
    }
  } catch (error) {
    console.error('Error al cargar datos:', error)
    alert('Error al cargar los datos. Por favor intente nuevamente.')
    datos.value = []
  } finally {
    cargando.value = false
  }
}
</script>