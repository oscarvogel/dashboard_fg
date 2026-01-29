<template>
  <div class="container mx-auto px-4 py-6">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Desempeño de Servicios</h2>

    <!-- Pestañas -->
    <div class="mb-6">
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex space-x-8">
          <button
            @click="activeTab = 'sector'"
            :class="[
              activeTab === 'sector'
                ? 'border-green-600 text-green-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            Desempeño por Sector
          </button>
          <button
            @click="activeTab = 'empleado'"
            :class="[
              activeTab === 'empleado'
                ? 'border-green-600 text-green-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            Desempeño por Empleado
          </button>
          <button
            @click="activeTab = 'equipo'"
            :class="[
              activeTab === 'equipo'
                ? 'border-green-600 text-green-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            Resumen por Equipo
          </button>
        </nav>
      </div>
    </div>

    <!-- Tabla y Gráfico -->
    <div v-if="activeTab === 'sector'">
      <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
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
              @click="obtenerDatosSector()"
              :disabled="cargandoSector"
              class="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition duration-150 ease-in-out flex items-center justify-center"
            >
              <svg v-if="cargandoSector" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ cargandoSector ? 'Cargando...' : 'Buscar' }}
            </button>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Gráfico de Efectividad</h3>
            </div>
            <div class="p-4 relative">
              <!-- Loading overlay para gráfico -->
              <div v-if="cargandoSector" class="flex items-center justify-center py-12">
                <div class="text-center">
                  <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p class="text-gray-500 text-sm">Generando gráfico...</p>
                </div>
              </div>
              <BarChart v-else :chart-data="sectorChartData" :chart-options="chartOptions" />
            </div>
          </div>

          <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Tabla de Efectividad por Sector</h3>
            </div>
            <div class="overflow-x-auto">
              <!-- Loading overlay para tabla -->
              <div v-if="cargandoSector" class="flex items-center justify-center py-12">
                <div class="text-center">
                  <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p class="text-gray-500 text-sm">Cargando datos...</p>
                </div>
              </div>
              <table v-else class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Prácticas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Downtime</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Extras</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Efectividad</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad Empleados</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="item in datosSector" :key="item.sector" class="hover:bg-green-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.sector }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.horas_practicas }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.downtime }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.horas_extras }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-700">{{ item.efectividad }}%</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ item.cantidad_empleados }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        @click="obtenerDetallesSector(item.sector)"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-xs font-medium transition duration-150 ease-in-out"
                      >
                        Ver Detalles
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="activeTab === 'empleado'">
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
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
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Empleado</label>
            <select
              v-model="empleadoSeleccionado"
              :disabled="cargandoEmpleados"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="" v-if="cargandoEmpleados">Cargando empleados...</option>
              <option value="" v-else>Todos</option>
              <option v-for="emp in empleadosConMovimiento" :key="emp.id" :value="emp.id">
                {{ emp.nombre }}
              </option>
            </select>
          </div>
          <div class="flex items-end">
            <button
              @click="obtenerDatosEmpleado()"
              :disabled="cargandoEmpleado"
              class="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition duration-150 ease-in-out flex items-center justify-center"
            >
              <svg v-if="cargandoEmpleado" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ cargandoEmpleado ? 'Cargando...' : 'Buscar' }}
            </button>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Gráfico de Efectividad por Empleado</h3>
            </div>
            <div class="p-4 relative">
              <!-- Loading overlay para gráfico de empleados -->
              <div v-if="cargandoEmpleado" class="flex items-center justify-center py-12">
                <div class="text-center">
                  <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p class="text-gray-500 text-sm">Generando gráfico...</p>
                </div>
              </div>
              <BarChart v-else :chart-data="empleadoChartData" :chart-options="chartOptions" />
            </div>
          </div>

          <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h3 class="text-lg leading-6 font-medium text-gray-900">Tabla de Efectividad por Empleado</h3>
            </div>
            <div class="overflow-x-auto">
              <!-- Loading overlay para tabla de empleados -->
              <div v-if="cargandoEmpleado" class="flex items-center justify-center py-12">
                <div class="text-center">
                  <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p class="text-gray-500 text-sm">Cargando datos...</p>
                </div>
              </div>
              <table v-else class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Empleado</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Prácticas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Downtime</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Extras</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Efectividad</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Efectividad Total</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <template v-for="empleado in datosEmpleadoConTotal" :key="empleado.empleado_id">
                    <!-- Filas de sectores por empleado -->
                    <tr v-for="(sector, index) in empleado.sectores" :key="`${empleado.empleado_id}-${sector.sector}`" class="hover:bg-green-50">
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <span v-if="index === 0">{{ empleado.empleado }}</span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ sector.sector }}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ sector.horas_practicas }}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ sector.downtime }}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ sector.horas_extras }}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-700">{{ sector.efectividad }}%</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-blue-700">
                        <span v-if="index === 0" class="bg-blue-100 px-2 py-1 rounded-full">{{ empleado.efectividadTotal }}%</span>
                      </td>
                    </tr>
                    <!-- Fila de totales por empleado -->
                    <tr class="bg-gray-50 border-b-2 border-gray-300">
                      <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-gray-900">
                        TOTAL {{ empleado.empleado }}
                      </td>
                      <td class="px-6 py-3 whitespace-nowrap text-sm font-medium text-gray-600">
                        {{ empleado.sectores.length }} sector(es)
                      </td>
                      <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-gray-900">
                        {{ empleado.totalHorasPracticas.toFixed(1) }}
                      </td>
                      <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-gray-900">
                        {{ empleado.totalDowntime.toFixed(1) }}
                      </td>
                      <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-gray-900">
                        {{ empleado.totalHorasExtras.toFixed(1) }}
                      </td>
                      <td class="px-6 py-3 whitespace-nowrap text-sm text-gray-500">-</td>
                      <td class="px-6 py-3 whitespace-nowrap text-sm font-bold text-blue-800">
                        <span class="bg-blue-200 px-3 py-1 rounded-full">{{ empleado.efectividadTotal }}%</span>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Nueva tabla de tareas por empleado -->
          <div v-if="empleadoSeleccionado && tareasEmpleado.length > 0" class="bg-white rounded-lg shadow">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <div class="flex justify-between items-center">
                <div>
                  <h3 class="text-lg leading-6 font-medium text-gray-900">
                    Tareas Realizadas - {{ obtenerNombreEmpleado(empleadoSeleccionado) }}
                  </h3>
                  <p class="mt-1 text-sm text-gray-500">
                    Detalle de todas las tareas realizadas en el período seleccionado ({{ totalTareas }} tareas)
                  </p>
                </div>
                <!-- Control de elementos por página -->
                <div class="flex items-center space-x-2">
                  <label class="text-sm text-gray-700">Mostrar:</label>
                  <select 
                    v-model="tareasPorPagina" 
                    @change="cambiarTareasPorPagina"
                    class="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    <option :value="10">10</option>
                    <option :value="25">25</option>
                    <option :value="50">50</option>
                    <option :value="100">100</option>
                  </select>
                  <span class="text-sm text-gray-700">por página</span>
                </div>
              </div>
            </div>
            <div class="overflow-x-auto">
              <!-- Loading overlay para tareas del empleado -->
              <div v-if="cargandoTareasEmpleado" class="flex items-center justify-center py-12">
                <div class="text-center">
                  <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 814 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p class="text-gray-500 text-sm">Cargando tareas...</p>
                </div>
              </div>
              <table v-else class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hora Inicio</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hora Fin</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Trabajadas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Extras</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Detalle Tarea</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OS</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(tarea, index) in tareasPaginadas" :key="index" class="hover:bg-green-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ formatearFecha(tarea.fecha) }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{{ tarea.sector }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ tarea.hora_inicio }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ tarea.hora_fin }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-700">{{ tarea.horas_trabajadas }}h</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span v-if="tarea.horas_extras" class="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs">
                        {{ tarea.horas_extras }}
                      </span>
                      <span v-else class="text-gray-400">-</span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" :title="tarea.detalle_tarea">
                      {{ tarea.detalle_tarea }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-medium">
                      {{ tarea.orden_servicio }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- Controles de paginación -->
            <div class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
              <div class="flex items-center justify-between">
                <div class="flex-1 flex justify-between sm:hidden">
                  <!-- Controles móviles -->
                  <button 
                    @click="paginaAnterior" 
                    :disabled="paginaActual <= 1"
                    class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button 
                    @click="paginaSiguiente" 
                    :disabled="paginaActual >= totalPaginas"
                    class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Siguiente
                  </button>
                </div>
                <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p class="text-sm text-gray-700">
                      Mostrando 
                      <span class="font-medium">{{ inicioRango }}</span>
                      a 
                      <span class="font-medium">{{ finRango }}</span>
                      de 
                      <span class="font-medium">{{ totalTareas }}</span>
                      tareas
                    </p>
                  </div>
                  <div>
                    <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <!-- Botón página anterior -->
                      <button 
                        @click="paginaAnterior" 
                        :disabled="paginaActual <= 1"
                        class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                        </svg>
                      </button>
                      
                      <!-- Números de página -->
                      <template v-for="pagina in paginasVisibles" :key="pagina">
                        <button 
                          v-if="pagina !== '...'"
                          @click="irAPagina(pagina)"
                          :class="[
                            pagina === paginaActual 
                              ? 'bg-green-50 border-green-500 text-green-600 z-10' 
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50',
                            'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                          ]"
                        >
                          {{ pagina }}
                        </button>
                        <span 
                          v-else
                          class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                        >
                          ...
                        </span>
                      </template>
                      
                      <!-- Botón página siguiente -->
                      <button 
                        @click="paginaSiguiente" 
                        :disabled="paginaActual >= totalPaginas"
                        class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                        </svg>
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Nueva sección para Resumen por Equipo -->
    <div v-if="activeTab === 'equipo'">
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
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
          <div class="relative">
            <label class="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
            <div class="relative">
              <input
                type="text"
                v-model="busquedaEquipo"
                @focus="mostrarDropdownEquipos"
                @blur="ocultarDropdownEquipos"
                @keydown="handleKeyDownEquipo"
                :disabled="cargandoEquipos"
                placeholder="Buscar equipo... (o dejar vacío para todos)"
                class="w-full px-3 py-2 pr-20 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <!-- Botón limpiar -->
              <button
                v-if="busquedaEquipo"
                @click="limpiarBusquedaEquipo"
                type="button"
                class="absolute right-10 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <!-- Icono de búsqueda -->
              <div class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              
              <!-- Dropdown de resultados -->
              <div
                v-if="mostrarListaEquipos && equiposFiltrados.length > 0"
                class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
              >
                <div
                  class="px-3 py-2 text-xs font-medium text-gray-500 bg-gray-50 border-b border-gray-200 cursor-pointer hover:bg-gray-100"
                  @mousedown.prevent="seleccionarEquipo(null)"
                >
                  Todos los equipos
                </div>
                <div
                  v-for="(equipo, index) in equiposFiltrados"
                  :key="equipo.id"
                  @mousedown.prevent="seleccionarEquipo(equipo)"
                  :class="[
                    'px-3 py-2 cursor-pointer',
                    index === equipoFocusIndex ? 'bg-green-100 text-green-900' : 'hover:bg-gray-100'
                  ]"
                >
                  <div class="text-sm font-medium text-gray-900">{{ equipo.nombre }}</div>
                </div>
              </div>
              
              <!-- Mensaje cuando no hay resultados -->
              <div
                v-if="mostrarListaEquipos && equiposFiltrados.length === 0 && busquedaEquipo"
                class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg"
              >
                <div class="px-3 py-2 text-sm text-gray-500 text-center">
                  No se encontraron equipos con "{{ busquedaEquipo }}"
                </div>
              </div>
              
              <!-- Indicador de carga -->
              <div
                v-if="cargandoEquipos"
                class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg"
              >
                <div class="px-3 py-2 text-sm text-gray-500 text-center">
                  <svg class="animate-spin h-5 w-5 text-green-600 inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Cargando equipos...
                </div>
              </div>
            </div>
          </div>
          
          <div class="relative">
            <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de Tarea</label>
            <div class="relative">
              <input
                type="text"
                v-model="busquedaTipoTarea"
                @focus="mostrarDropdownTiposTareas"
                @blur="ocultarDropdownTiposTareas"
                @keydown="handleKeyDownTipoTarea"
                placeholder="Buscar tipo de tarea... (o dejar vacío para todos)"
                class="w-full px-3 py-2 pr-20 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500"
              />
              <!-- Botón limpiar -->
              <button
                v-if="busquedaTipoTarea"
                @click="limpiarBusquedaTipoTarea"
                type="button"
                class="absolute right-10 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <!-- Icono de búsqueda -->
              <div class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              
              <!-- Dropdown de resultados -->
              <div
                v-if="mostrarListaTiposTareas && tiposTareasFiltrados.length > 0"
                class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
              >
                <div
                  class="px-3 py-2 text-xs font-medium text-gray-500 bg-gray-50 border-b border-gray-200 cursor-pointer hover:bg-gray-100"
                  @mousedown.prevent="seleccionarTipoTarea(null)"
                >
                  Todos los tipos de tarea
                </div>
                <div
                  v-for="(tipo, index) in tiposTareasFiltrados"
                  :key="tipo.id"
                  @mousedown.prevent="seleccionarTipoTarea(tipo)"
                  :class="[
                    'px-3 py-2 cursor-pointer',
                    index === tipoTareaFocusIndex ? 'bg-green-100 text-green-900' : 'hover:bg-gray-100'
                  ]"
                >
                  <div class="text-sm font-medium text-gray-900">{{ tipo.tarea }}</div>
                </div>
              </div>
              
              <!-- Mensaje cuando no hay resultados -->
              <div
                v-if="mostrarListaTiposTareas && tiposTareasFiltrados.length === 0 && busquedaTipoTarea"
                class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg"
              >
                <div class="px-3 py-2 text-sm text-gray-500 text-center">
                  No se encontraron tipos de tarea con "{{ busquedaTipoTarea }}"
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Botones de acción -->
        <div class="flex gap-4 mb-6">
          <button
            @click="obtenerDatosEquipo()"
            :disabled="cargandoEquipo"
            class="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2 px-6 rounded-md transition duration-150 ease-in-out flex items-center justify-center"
          >
            <svg v-if="cargandoEquipo" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ cargandoEquipo ? 'Cargando...' : 'Buscar' }}
          </button>
          
          <button
            @click="exportarEquipoAExcel()"
            :disabled="cargandoEquipo || datosEquipo.length === 0"
            class="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2 px-6 rounded-md transition duration-150 ease-in-out flex items-center justify-center"
          >
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 17a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2zM3 7a1 1 0 011-1h12a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V7zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/>
            </svg>
            Exportar Excel
          </button>
        </div>

        <div class="space-y-6">
          <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
              <div class="flex justify-between items-center">
                <div>
                  <h3 class="text-lg leading-6 font-medium text-gray-900">Resumen de Órdenes de Servicio por Equipo</h3>
                  <p class="mt-1 text-sm text-gray-500">
                    {{ equipoSeleccionado ? `Datos del equipo: ${obtenerNombreEquipo(equipoSeleccionado)}` : 'Datos de todos los equipos' }}
                    {{ tipoTareaSeleccionado ? ` - Filtrado por: ${busquedaTipoTarea || 'Tipo de tarea seleccionado'}` : '' }}
                    ({{ totalEquipos }} {{ totalEquipos === 1 ? 'equipo' : 'equipos' }})
                  </p>
                </div>
                <!-- Control de elementos por página -->
                <div class="flex items-center space-x-2">
                  <label class="text-sm text-gray-700">Mostrar:</label>
                  <select 
                    v-model="equiposPorPagina" 
                    @change="cambiarEquiposPorPagina"
                    class="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                  >
                    <option :value="10">10</option>
                    <option :value="25">25</option>
                    <option :value="50">50</option>
                    <option :value="100">100</option>
                  </select>
                  <span class="text-sm text-gray-700">por página</span>
                </div>
              </div>
            </div>
            <div class="overflow-x-auto">
              <!-- Loading overlay para tabla de equipos -->
              <div v-if="cargandoEquipo" class="flex items-center justify-center py-12">
                <div class="text-center">
                  <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <p class="text-gray-500 text-sm">Cargando datos...</p>
                </div>
              </div>
              <table v-else class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Equipo</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unidad de Negocio</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Órdenes</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cerradas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Abiertas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">% Cerradas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Tareas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Preventivas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correctivas</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Trabajo</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Costo Repuestos</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mecánicos</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="equipo in equiposPaginados" :key="equipo.equipo_id" class="hover:bg-green-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        @click="verDetallesEquipo(equipo)"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md text-xs font-medium transition duration-150 ease-in-out"
                      >
                        Ver Órdenes
                      </button>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ equipo.equipo }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ equipo.unidad_negocio }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">{{ equipo.total_ordenes }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-green-600">{{ equipo.ordenes_cerradas }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-orange-600">{{ equipo.ordenes_abiertas }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-blue-700">{{ equipo.porcentaje_cerradas }}%</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">{{ equipo.total_tareas }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-green-700">{{ equipo.tareas_preventivas }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-red-600">{{ equipo.tareas_correctivas }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ equipo.total_horas_trabajo }}h</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${{ equipo.total_costo_repuestos.toLocaleString() }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ equipo.cantidad_mecanicos }}</td>
                  </tr>
                </tbody>
              </table>
              
              <!-- Mensaje cuando no hay datos -->
              <div v-if="!cargandoEquipo && datosEquipo.length === 0" class="text-center py-8">
                <p class="text-gray-500">No se encontraron datos para el rango de fechas seleccionado.</p>
              </div>
            </div>
            
            <!-- Controles de paginación para equipos -->
            <div class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
              <div class="flex items-center justify-between">
                <div class="flex-1 flex justify-between sm:hidden">
                  <!-- Controles móviles -->
                  <button 
                    @click="paginaEquipoAnterior" 
                    :disabled="paginaActualEquipos <= 1"
                    class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button 
                    @click="paginaEquipoSiguiente" 
                    :disabled="paginaActualEquipos >= totalPaginasEquipos"
                    class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Siguiente
                  </button>
                </div>
                <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p class="text-sm text-gray-700">
                      Mostrando 
                      <span class="font-medium">{{ inicioRangoEquipos }}</span>
                      a 
                      <span class="font-medium">{{ finRangoEquipos }}</span>
                      de 
                      <span class="font-medium">{{ totalEquipos }}</span>
                      equipos
                    </p>
                  </div>
                  <div>
                    <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <!-- Botón página anterior -->
                      <button 
                        @click="paginaEquipoAnterior" 
                        :disabled="paginaActualEquipos <= 1"
                        class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                        </svg>
                      </button>
                      
                      <!-- Números de página -->
                      <template v-for="pagina in paginasVisiblesEquipos" :key="pagina">
                        <button 
                          v-if="pagina !== '...'"
                          @click="irAPaginaEquipo(pagina)"
                          :class="[
                            pagina === paginaActualEquipos 
                              ? 'bg-green-50 border-green-500 text-green-600 z-10' 
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50',
                            'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                          ]"
                        >
                          {{ pagina }}
                        </button>
                        <span 
                          v-else
                          class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                        >
                          ...
                        </span>
                      </template>
                      
                      <!-- Botón página siguiente -->
                      <button 
                        @click="paginaEquipoSiguiente" 
                        :disabled="paginaActualEquipos >= totalPaginasEquipos"
                        class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                        </svg>
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal para detalles del sector -->
    <div v-if="mostrarDetallesSector" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <!-- Header del modal -->
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              Detalles de Tareas - Sector: {{ sectorSeleccionado }}
            </h3>
            <button
              @click="cerrarDetallesSector"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>

          </div>

          <!-- Contenido del modal -->
          <div class="max-h-96 overflow-y-auto">
            <!-- Loading de detalles -->
            <div v-if="cargandoDetallesSector" class="flex items-center justify-center py-12">
              <div class="text-center">
                <svg class="animate-spin h-8 w-8 text-blue-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="text-gray-500 text-sm">Cargando detalles...</p>
              </div>
            </div>

            <!-- Tabla de detalles -->
            <div v-else-if="detallesSector.length > 0" class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mecánico</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hora Inicio</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hora Fin</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas Extras</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Observaciones</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OS</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(detalle, index) in detallesSector" :key="index" class="hover:bg-blue-50">
                    <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{{ detalle.fecha }}</td>
                    <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-700">{{ detalle.mecanico }}</td>
                    <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ detalle.hora_inicio }}</td>
                    <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{{ detalle.hora_fin }}</td>
                    <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span v-if="detalle.horas_extras" class="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs">
                        {{ detalle.horas_extras }}
                      </span>
                      <span v-else class="text-gray-400">-</span>
                    </td>
                    <td class="px-4 py-4 text-sm text-gray-500 max-w-xs truncate" :title="detalle.detalle_tarea">
                      {{ detalle.detalle_tarea }}
                    </td>
                    <td class="px-4 py-4 whitespace-nowrap text-sm text-blue-600 font-medium">
                      {{ detalle.orden_servicio }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Mensaje cuando no hay datos -->
            <div v-else class="text-center py-8">
              <p class="text-gray-500">No se encontraron detalles para este sector en el rango de fechas seleccionado.</p>
            </div>
          </div>

          <!-- Footer del modal -->
          <div class="flex justify-end mt-4 pt-4 border-t border-gray-200">
            <button
              @click="exportarDetallesAExcel"
              class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-150 ease-in-out flex items-center"
            >
              <svg class="w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V16a2 2 0 01-2 2z" />
              </svg>
              Exportar a Excel
            </button>            

            <button
              @click="cerrarDetallesSector"
              class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-150 ease-in-out"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal para detalles de órdenes por equipo -->
    <div v-if="mostrarDetallesEquipo" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-full overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <h3 class="text-lg leading-6 font-medium text-gray-900">
                Órdenes de Servicio - {{ equipoDetalleSeleccionado?.equipo }}
              </h3>
              <p class="mt-1 text-sm text-gray-500">
                Período: {{ fechaInicio }} al {{ fechaFin }} • {{ ordenesEquipo.length }} orden(es) encontrada(s)
              </p>
            </div>
            <div class="flex items-center space-x-3">
              <!-- Control de elementos por página -->
              <div class="flex items-center space-x-2">
                <label class="text-sm text-gray-700">Mostrar:</label>
                <select 
                  v-model="detallesPorPagina" 
                  @change="cambiarDetallesPorPagina"
                  class="border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  <option :value="3">3</option>
                  <option :value="5">5</option>
                  <option :value="10">10</option>
                  <option :value="20">20</option>
                </select>
                <span class="text-sm text-gray-700">por página</span>
              </div>
              
              <!-- Botón exportar -->
              <button
                @click="exportarOrdenesEquipoAExcel"
                :disabled="ordenesEquipo.length === 0"
                class="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-3 py-2 rounded-md text-sm font-medium transition duration-150 ease-in-out flex items-center"
              >
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 17a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2zM3 7a1 1 0 011-1h12a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V7zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/>
                </svg>
                Excel
              </button>
              
              <!-- Botón cerrar -->
              <button
                @click="cerrarDetallesEquipo"
                class="text-gray-400 hover:text-gray-600 transition duration-150 ease-in-out"
              >
                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="px-6 py-4">
          <!-- Loading state -->
          <div v-if="cargandoOrdenesEquipo" class="flex items-center justify-center py-12">
            <div class="text-center">
              <svg class="animate-spin h-8 w-8 text-green-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-gray-500 text-sm">Cargando órdenes de servicio...</p>
            </div>
          </div>

          <!-- Lista de órdenes -->
          <div v-else class="space-y-6">
            <div v-for="orden in ordenesPaginadas" :key="orden.orden_servicio" class="border border-gray-200 rounded-lg overflow-hidden">
              <!-- Cabecera de la orden -->
              <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <div class="flex items-center space-x-4">
                      <h4 class="text-lg font-semibold text-gray-900">
                        Orden #{{ orden.orden_servicio }}
                      </h4>
                      <span :class="[
                        'px-2 py-1 text-xs font-medium rounded-full',
                        orden.estado.toLowerCase() === 'cerrado' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      ]">
                        {{ orden.estado }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-600 mt-1">{{ orden.descripcion }}</p>
                    <div class="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <span>📅 {{ orden.fecha }}</span>
                      <span>🏢 {{ orden.unidad_negocio }}</span>
                      <span>⚙️ {{ orden.total_tareas }} tarea(s)</span>
                      <span>⏱️ {{ orden.total_horas_trabajo }}h trabajo</span>
                      <span>💰 ${{ orden.total_costo_repuestos.toLocaleString() }} repuestos</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Resumen de la orden -->
              <div class="px-4 py-3 bg-blue-50">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span class="text-gray-600">Tareas Preventivas:</span>
                    <span class="ml-1 font-medium text-green-600">{{ orden.tareas_preventivas }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Tareas Correctivas:</span>
                    <span class="ml-1 font-medium text-red-600">{{ orden.tareas_correctivas }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Mecánicos:</span>
                    <span class="ml-1 font-medium">{{ orden.cantidad_mecanicos }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Sectores:</span>
                    <span class="ml-1 font-medium">{{ orden.cantidad_sectores }}</span>
                  </div>
                </div>
              </div>

              <!-- Detalles de tareas -->
              <div class="overflow-x-auto max-h-96 overflow-y-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50 sticky top-0">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mecánico</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sector</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">KM/Hora</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horario</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Horas</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/3">Descripción de Tarea</th>
                      <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Repuesto</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="detalle in orden.detalles" :key="detalle.detalle_id" class="hover:bg-gray-50">
                      <td class="px-4 py-3 text-sm text-gray-900">{{ detalle.mecanico }}</td>
                      <td class="px-4 py-3 text-sm text-gray-500">{{ detalle.sector }}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        <div class="flex items-center">
                          <span class="font-medium text-blue-700">{{ detalle.km_hora}}</span>
                        </div>
                      </td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        <div class="text-xs">{{ detalle.hora_inicio }} - {{ detalle.hora_fin }}</div>
                      </td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        <div class="text-sm font-medium">{{ detalle.horas_trabajadas }}h</div>
                        <div v-if="detalle.horas_extras" class="text-xs text-orange-600">+{{ detalle.horas_extras }} extra</div>
                      </td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm">
                        <div class="flex flex-col space-y-1">
                          <span v-if="detalle.preventivo" class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs text-center">Preventivo</span>
                          <span v-if="detalle.correctivo" class="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs text-center">Correctivo</span>
                        </div>
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-900">
                        <div class="max-w-md">
                          <div class="text-sm font-medium text-gray-900 mb-1">{{ detalle.detalle_tarea }}</div>
                          <div v-if="detalle.observaciones && detalle.observaciones !== 'Sin observaciones'" 
                               class="text-xs text-gray-600 italic">
                            <span class="font-medium">Obs:</span> {{ detalle.observaciones }}
                          </div>
                        </div>
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-500">
                        <div v-if="detalle.repuesto" class="text-xs">
                          <div class="font-medium text-gray-900">{{ detalle.repuesto }}</div>
                          <div class="text-gray-500">
                            Cant: {{ detalle.cantidad_repuesto }}
                          </div>
                          <div class="text-gray-500">
                            ${{ detalle.precio_unitario }} c/u
                          </div>
                          <div class="font-medium text-green-600">
                            Total: ${{ detalle.costo_repuesto }}
                          </div>
                        </div>
                        <span v-else class="text-gray-400 text-xs">Sin repuesto</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Observaciones de la orden -->
              <div v-if="orden.observaciones && orden.observaciones !== 'Sin observaciones'" class="px-4 py-3 bg-yellow-50 border-t border-gray-200">
                <h5 class="text-sm font-medium text-gray-900 mb-1">Observaciones:</h5>
                <p class="text-sm text-gray-700">{{ orden.observaciones }}</p>
              </div>
            </div>

            <!-- Mensaje cuando no hay órdenes -->
            <div v-if="ordenesEquipo.length === 0" class="text-center py-8">
              <p class="text-gray-500">No se encontraron órdenes de servicio para este equipo en el período seleccionado.</p>
            </div>
          </div>
          
          <!-- Controles de paginación para detalles -->
          <div v-if="ordenesEquipo.length > 0" class="px-6 py-3 border-t border-gray-200 bg-gray-50">
            <div class="flex items-center justify-between">
              <div class="flex-1 flex justify-between sm:hidden">
                <!-- Controles móviles -->
                <button 
                  @click="paginaDetalleAnterior" 
                  :disabled="paginaActualDetalles <= 1"
                  class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <button 
                  @click="paginaDetalleSiguiente" 
                  :disabled="paginaActualDetalles >= totalPaginasDetalles"
                  class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Siguiente
                </button>
              </div>
              <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p class="text-sm text-gray-700">
                    Mostrando 
                    <span class="font-medium">{{ inicioRangoDetalles }}</span>
                    a 
                    <span class="font-medium">{{ finRangoDetalles }}</span>
                    de 
                    <span class="font-medium">{{ totalDetalles }}</span>
                    órdenes
                  </p>
                </div>
                <div>
                  <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <!-- Botón página anterior -->
                    <button 
                      @click="paginaDetalleAnterior" 
                      :disabled="paginaActualDetalles <= 1"
                      class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                      </svg>
                    </button>
                    
                    <!-- Números de página -->
                    <template v-for="pagina in paginasVisiblesDetalles" :key="pagina">
                      <button 
                        v-if="pagina !== '...'"
                        @click="irAPaginaDetalle(pagina)"
                        :class="[
                          pagina === paginaActualDetalles 
                            ? 'bg-green-50 border-green-500 text-green-600 z-10' 
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50',
                          'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                        ]"
                      >
                        {{ pagina }}
                      </button>
                      <span 
                        v-else
                        class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700"
                      >
                        ...
                      </span>
                    </template>
                    
                    <!-- Botón página siguiente -->
                    <button 
                      @click="paginaDetalleSiguiente" 
                      :disabled="paginaActualDetalles >= totalPaginasDetalles"
                      class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                      </svg>
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pie del modal -->
        <div class="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div class="flex justify-end">
            <button
              @click="cerrarDetallesEquipo"
              class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-150 ease-in-out"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as XLSX from 'xlsx'
import { ref, onMounted, watch, computed } from 'vue'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'

const activeTab = ref('sector')
const fechaInicio = ref('')
const fechaFin = ref('')
const empleadoSeleccionado = ref('')
const datosSector = ref([])
const datosEmpleado = ref([])
const datosEquipo = ref([])
const empleadosConMovimiento = ref([])
const equiposConOrdenes = ref([])
const tiposTareas = ref([])
const tipoTareaSeleccionado = ref('')
const tareasEmpleado = ref([])

// Estados de carga
const cargandoSector = ref(false)
const cargandoEmpleado = ref(false)
const cargandoEmpleados = ref(false)
const cargandoEquipo = ref(false)
const cargandoEquipos = ref(false)
const cargandoDetallesSector = ref(false)
const cargandoTareasEmpleado = ref(false)

// Variables para paginación de tareas
const paginaActual = ref(1)
const tareasPorPagina = ref(10)

// Variables para paginación de equipos
const paginaActualEquipos = ref(1)
const equiposPorPagina = ref(10)

// Datos para detalles por sector
const sectorSeleccionado = ref('')
const detallesSector = ref([])
const mostrarDetallesSector = ref(false)

// Variable para equipo seleccionado
const equipoSeleccionado = ref('')

// Variables para autocomplete de equipos
const busquedaEquipo = ref('')
const mostrarListaEquipos = ref(false)
const equipoFocusIndex = ref(-1)

// Variables para autocomplete de tipos de tareas
const busquedaTipoTarea = ref('')
const mostrarListaTiposTareas = ref(false)
const tipoTareaFocusIndex = ref(-1)

// Variables para detalle de órdenes por equipo
const ordenesEquipo = ref([])
const equipoDetalleSeleccionado = ref(null)
const mostrarDetallesEquipo = ref(false)
const cargandoOrdenesEquipo = ref(false)

// Variables para paginación de detalles de órdenes
const paginaActualDetalles = ref(1)
const detallesPorPagina = ref(5)

// Datos para los gráficos
const sectorChartData = computed(() => {
  return {
    labels: datosSector.value.map(d => d.sector),
    datasets: [
      {
        label: 'Efectividad (%)',
        data: datosSector.value.map(d => d.efectividad),
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1
      }
    ]
  }
})

const empleadoChartData = computed(() => {
  return {
    labels: datosEmpleado.value.map(d => `${d.empleado} - ${d.sector}`),
    datasets: [
      {
        label: 'Efectividad (%)',
        data: datosEmpleado.value.map(d => d.efectividad),
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1
      }
    ]
  }
})

// Calcular efectividad total por empleado
const datosEmpleadoConTotal = computed(() => {
  if (!datosEmpleado.value.length) return []
  
  // Agrupar por empleado
  const empleadosAgrupados = {}
  
  datosEmpleado.value.forEach(item => {
    if (!empleadosAgrupados[item.empleado_id]) {
      empleadosAgrupados[item.empleado_id] = {
        empleado_id: item.empleado_id,
        empleado: item.empleado,
        sectores: [],
        totalHorasPracticas: 0,
        totalDowntime: 0,
        totalHorasExtras: 0
      }
    }
    
    empleadosAgrupados[item.empleado_id].sectores.push({
      sector: item.sector,
      horas_practicas: item.horas_practicas,
      downtime: item.downtime,
      horas_extras: item.horas_extras,
      efectividad: item.efectividad
    })
    
    empleadosAgrupados[item.empleado_id].totalHorasPracticas += parseFloat(item.horas_practicas || 0)
    empleadosAgrupados[item.empleado_id].totalDowntime += parseFloat(item.downtime || 0)
    empleadosAgrupados[item.empleado_id].totalHorasExtras += parseFloat(item.horas_extras || 0)
  })
  
  // Calcular efectividad total para cada empleado
  Object.values(empleadosAgrupados).forEach(empleado => {
    const totalHoras = empleado.totalHorasPracticas + empleado.totalDowntime + empleado.totalHorasExtras
    empleado.efectividadTotal = totalHoras > 0 ? 
      ((empleado.totalHorasPracticas / totalHoras) * 100).toFixed(1) : 0
  })
  
  return Object.values(empleadosAgrupados)
})

// Computed properties para paginación de tareas
const totalTareas = computed(() => tareasEmpleado.value.length)

const totalPaginas = computed(() => Math.ceil(totalTareas.value / tareasPorPagina.value))

const tareasPaginadas = computed(() => {
  const inicio = (paginaActual.value - 1) * tareasPorPagina.value
  const fin = inicio + tareasPorPagina.value
  return tareasEmpleado.value.slice(inicio, fin)
})

const inicioRango = computed(() => {
  if (totalTareas.value === 0) return 0
  return (paginaActual.value - 1) * tareasPorPagina.value + 1
})

const finRango = computed(() => {
  const fin = paginaActual.value * tareasPorPagina.value
  return fin > totalTareas.value ? totalTareas.value : fin
})

const paginasVisibles = computed(() => {
  const total = totalPaginas.value
  const actual = paginaActual.value
  const paginas = []
  
  if (total <= 7) {
    // Si hay 7 páginas o menos, mostrar todas
    for (let i = 1; i <= total; i++) {
      paginas.push(i)
    }
  } else {
    // Lógica para mostrar páginas con puntos suspensivos
    if (actual <= 4) {
      for (let i = 1; i <= 5; i++) {
        paginas.push(i)
      }
      paginas.push('...')
      paginas.push(total)
    } else if (actual >= total - 3) {
      paginas.push(1)
      paginas.push('...')
      for (let i = total - 4; i <= total; i++) {
        paginas.push(i)
      }
    } else {
      paginas.push(1)
      paginas.push('...')
      for (let i = actual - 1; i <= actual + 1; i++) {
        paginas.push(i)
      }
      paginas.push('...')
      paginas.push(total)
    }
  }
  
  return paginas
})

// Computed properties para paginación de equipos
const totalEquipos = computed(() => datosEquipo.value.length)

const totalPaginasEquipos = computed(() => Math.ceil(totalEquipos.value / equiposPorPagina.value))

const equiposPaginados = computed(() => {
  const inicio = (paginaActualEquipos.value - 1) * equiposPorPagina.value
  const fin = inicio + equiposPorPagina.value
  return datosEquipo.value.slice(inicio, fin)
})

const inicioRangoEquipos = computed(() => {
  if (totalEquipos.value === 0) return 0
  return (paginaActualEquipos.value - 1) * equiposPorPagina.value + 1
})

const finRangoEquipos = computed(() => {
  const fin = paginaActualEquipos.value * equiposPorPagina.value
  return fin > totalEquipos.value ? totalEquipos.value : fin
})

const paginasVisiblesEquipos = computed(() => {
  const total = totalPaginasEquipos.value
  const actual = paginaActualEquipos.value
  const paginas = []
  
  if (total <= 7) {
    // Si hay 7 páginas o menos, mostrar todas
    for (let i = 1; i <= total; i++) {
      paginas.push(i)
    }
  } else {
    // Lógica para mostrar páginas con puntos suspensivos
    if (actual <= 4) {
      for (let i = 1; i <= 5; i++) {
        paginas.push(i)
      }
      paginas.push('...')
      paginas.push(total)
    } else if (actual >= total - 3) {
      paginas.push(1)
      paginas.push('...')
      for (let i = total - 4; i <= total; i++) {
        paginas.push(i)
      }
    } else {
      paginas.push(1)
      paginas.push('...')
      for (let i = actual - 1; i <= actual + 1; i++) {
        paginas.push(i)
      }
      paginas.push('...')
      paginas.push(total)
    }
  }
  
  return paginas
})

// Paginación para detalles de órdenes
const totalDetalles = computed(() => {
  return ordenesEquipo.value.length
})

const totalPaginasDetalles = computed(() => {
  return Math.ceil(totalDetalles.value / detallesPorPagina.value)
})

const inicioRangoDetalles = computed(() => {
  return (paginaActualDetalles.value - 1) * detallesPorPagina.value + 1
})

const finRangoDetalles = computed(() => {
  const fin = paginaActualDetalles.value * detallesPorPagina.value
  return fin > totalDetalles.value ? totalDetalles.value : fin
})

const ordenesPaginadas = computed(() => {
  const inicio = (paginaActualDetalles.value - 1) * detallesPorPagina.value
  const fin = inicio + detallesPorPagina.value
  return ordenesEquipo.value.slice(inicio, fin)
})

const paginasVisiblesDetalles = computed(() => {
  const total = totalPaginasDetalles.value
  const actual = paginaActualDetalles.value
  const paginas = []
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      paginas.push(i)
    }
  } else {
    if (actual <= 4) {
      for (let i = 1; i <= 5; i++) {
        paginas.push(i)
      }
      paginas.push('...')
      paginas.push(total)
    } else if (actual >= total - 3) {
      paginas.push(1)
      paginas.push('...')
      for (let i = total - 4; i <= total; i++) {
        paginas.push(i)
      }
    } else {
      paginas.push(1)
      paginas.push('...')
      for (let i = actual - 1; i <= actual + 1; i++) {
        paginas.push(i)
      }
      paginas.push('...')
      paginas.push(total)
    }
  }
  
  return paginas
})

// Filtrar equipos según búsqueda
const equiposFiltrados = computed(() => {
  if (!busquedaEquipo.value) {
    return equiposConOrdenes.value
  }
  const busqueda = busquedaEquipo.value.toLowerCase()
  return equiposConOrdenes.value.filter(equipo => 
    equipo.nombre.toLowerCase().includes(busqueda)
  )
})

// Filtrar tipos de tareas según búsqueda
const tiposTareasFiltrados = computed(() => {
  if (!busquedaTipoTarea.value) {
    return tiposTareas.value
  }
  const busqueda = busquedaTipoTarea.value.toLowerCase()
  return tiposTareas.value.filter(tipo => 
    tipo.tarea.toLowerCase().includes(busqueda)
  )
})

// Opciones del gráfico
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: 'Efectividad (%)'
      }
    }
  }
}

// Cargar empleados con movimiento cuando cambian las fechas
watch([fechaInicio, fechaFin], async () => {
  if (fechaInicio.value && fechaFin.value) {
    await cargarEmpleadosConMovimiento()
    await cargarEquiposConOrdenes()
    await cargarTiposTareas()
    // Limpiar tareas cuando cambian las fechas
    tareasEmpleado.value = []
    datosEquipo.value = []
  }
})

// Cargar tareas cuando cambia el empleado seleccionado
watch(empleadoSeleccionado, async (nuevoEmpleado) => {
  if (nuevoEmpleado && fechaInicio.value && fechaFin.value) {
    await obtenerTareasEmpleado(nuevoEmpleado)
    paginaActual.value = 1 // Resetear paginación
  } else {
    tareasEmpleado.value = []
    paginaActual.value = 1
  }
})

// Resetear paginación cuando cambian las tareas
watch(tareasEmpleado, () => {
  paginaActual.value = 1
})

// Resetear paginación cuando cambian los datos de equipos
watch(datosEquipo, () => {
  paginaActualEquipos.value = 1
})

// Resetear paginación cuando cambian las órdenes de equipo
watch(ordenesEquipo, () => {
  paginaActualDetalles.value = 1
})

// Cargar empleados con movimiento en rango de fechas
async function cargarEmpleadosConMovimiento() {
  try {
    cargandoEmpleados.value = true
    const response = await api.get('/api/mantenimiento/empleados-con-movimiento/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value
      }
    })
    empleadosConMovimiento.value = response.data
  } catch (error) {
    console.error("Error cargando empleados:", error)
    empleadosConMovimiento.value = []
  } finally {
    cargandoEmpleados.value = false
  }
}

// Cargar equipos con órdenes en rango de fechas
async function cargarEquiposConOrdenes() {
  try {
    cargandoEquipos.value = true
    const response = await api.get('/api/mantenimiento/equipos-con-ordenes/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value
      }
    })
    equiposConOrdenes.value = response.data
  } catch (error) {
    console.error("Error cargando equipos:", error)
    equiposConOrdenes.value = []
  } finally {
    cargandoEquipos.value = false
  }
}

// Cargar tipos de tareas que tuvieron movimiento en el rango
async function cargarTiposTareas() {
  if (!fechaInicio.value || !fechaFin.value) {
    tiposTareas.value = []
    return
  }
  try {
    const response = await api.get('/api/mantenimiento/tipos-tareas-con-movimiento/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value
      }
    })
    tiposTareas.value = response.data
  } catch (error) {
    console.error('Error cargando tipos de tareas:', error)
    tiposTareas.value = []
  }
}

// Obtener datos por equipo
async function obtenerDatosEquipo() {
  if (!fechaInicio.value || !fechaFin.value) {
    alert('Por favor seleccione fechas')
    return
  }
  try {
    cargandoEquipo.value = true
    const params = {
      fecha_inicio: fechaInicio.value,
      fecha_fin: fechaFin.value
    }
    if (equipoSeleccionado.value) {
      params.equipo = equipoSeleccionado.value
    }
    if (tipoTareaSeleccionado.value) {
      params.tipo_tarea = tipoTareaSeleccionado.value
      console.log('Filtrando por tipo de tarea:', tipoTareaSeleccionado.value, busquedaTipoTarea.value)
    }
    console.log('Params enviados a resumen-por-equipo:', params)
    const response = await api.get('/api/mantenimiento/resumen-por-equipo/', { params })
    datosEquipo.value = response.data
  } catch (error) {
    console.error("Error obteniendo datos del equipo:", error)
    alert('Error al obtener datos del equipo')
  } finally {
    cargandoEquipo.value = false
  }
}

// Exportar datos de equipos a Excel
function exportarEquipoAExcel() {
  if (!datosEquipo.value || datosEquipo.value.length === 0) {
    alert('No hay datos para exportar.')
    return
  }

  // Mapear los datos al formato deseado en Excel
  const datosParaExportar = datosEquipo.value.map(equipo => ({
    'Equipo': equipo.equipo,
    'Unidad de Negocio': equipo.unidad_negocio,
    'Total Órdenes': equipo.total_ordenes,
    'Órdenes Cerradas': equipo.ordenes_cerradas,
    'Órdenes Abiertas': equipo.ordenes_abiertas,
    '% Cerradas': equipo.porcentaje_cerradas,
    'Total Tareas': equipo.total_tareas,
    'Tareas Preventivas': equipo.tareas_preventivas,
    'Tareas Correctivas': equipo.tareas_correctivas,
    'Promedio Tareas/Orden': equipo.promedio_tareas_por_orden,
    'Total Horas Trabajo': equipo.total_horas_trabajo,
    'Total Horas Extras': equipo.total_horas_extras,
    'Promedio Horas/Orden': equipo.promedio_horas_por_orden,
    'Costo Total Repuestos': equipo.total_costo_repuestos,
    'Cantidad Repuestos': equipo.cantidad_repuestos,
    'Cantidad Mecánicos': equipo.cantidad_mecanicos,
    'Cantidad Sectores': equipo.cantidad_sectores,
    'Mecánicos Involucrados': equipo.mecanicos.join(', '),
    'Sectores Involucrados': equipo.sectores.join(', ')
  }))

  // Crear una hoja de cálculo
  const worksheet = XLSX.utils.json_to_sheet(datosParaExportar)

  // Ajustar el ancho de las columnas
  const columnWidths = [
    { wch: 25 }, // Equipo
    { wch: 20 }, // Unidad de Negocio
    { wch: 12 }, // Total Órdenes
    { wch: 12 }, // Órdenes Cerradas
    { wch: 12 }, // Órdenes Abiertas
    { wch: 10 }, // % Cerradas
    { wch: 15 }, // Órdenes Preventivas
    { wch: 15 }, // Órdenes Correctivas
    { wch: 15 }, // Total Horas Trabajo
    { wch: 15 }, // Total Horas Extras
    { wch: 18 }, // Promedio Horas/Orden
    { wch: 18 }, // Costo Total Repuestos
    { wch: 15 }, // Cantidad Repuestos
    { wch: 15 }, // Cantidad Mecánicos
    { wch: 15 }, // Cantidad Sectores
    { wch: 40 }, // Mecánicos Involucrados
    { wch: 40 }  // Sectores Involucrados
  ]
  worksheet['!cols'] = columnWidths

  // Crear libro de trabajo
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Resumen por Equipo')

  // Generar y descargar el archivo
  const equipoFiltro = equipoSeleccionado.value ? 
    equiposConOrdenes.value.find(e => e.id == equipoSeleccionado.value)?.nombre || 'equipo_especifico' : 
    'todos_equipos'
  XLSX.writeFile(workbook, `resumen_equipos_${equipoFiltro}_${fechaInicio.value}_a_${fechaFin.value}.xlsx`)
}

// Obtener datos por sector
async function obtenerDatosSector() {
  if (!fechaInicio.value || !fechaFin.value) {
    alert('Por favor seleccione fechas')
    return
  }
  try {
    cargandoSector.value = true
    const response = await api.get('/api/mantenimiento/efectividad-sector/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value
      }
    })
    datosSector.value = response.data
  } catch (error) {
    console.error("Error obteniendo datos:", error)
    alert('Error al obtener datos del sector')
  } finally {
    cargandoSector.value = false
  }
}

// Obtener datos por empleado
async function obtenerDatosEmpleado() {
  if (!fechaInicio.value || !fechaFin.value) {
    alert('Por favor seleccione fechas')
    return
  }
  try {
    cargandoEmpleado.value = true
    const params = {
      fecha_inicio: fechaInicio.value,
      fecha_fin: fechaFin.value
    }
    if (empleadoSeleccionado.value) {
      params.empleado = empleadoSeleccionado.value
    }
    const response = await api.get('/api/mantenimiento/efectividad-empleado/', { params })
    datosEmpleado.value = response.data
    
    // Si hay un empleado seleccionado, cargar sus tareas
    if (empleadoSeleccionado.value) {
      await obtenerTareasEmpleado(empleadoSeleccionado.value)
    }
  } catch (error) {
    console.error("Error obteniendo datos:", error)
    alert('Error al obtener datos del empleado')
  } finally {
    cargandoEmpleado.value = false
  }
}

// Obtener tareas de un empleado específico
async function obtenerTareasEmpleado(empleadoId) {
  if (!fechaInicio.value || !fechaFin.value || !empleadoId) {
    return
  }
  try {
    cargandoTareasEmpleado.value = true
    const response = await api.get('/api/mantenimiento/tareas-empleado/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value,
        empleado_id: empleadoId
      }
    })
    tareasEmpleado.value = response.data
  } catch (error) {
    console.error("Error obteniendo tareas del empleado:", error)
    alert('Error al obtener tareas del empleado')
  } finally {
    cargandoTareasEmpleado.value = false
  }
}

// Obtener nombre del empleado por ID
function obtenerNombreEmpleado(empleadoId) {
  const empleado = empleadosConMovimiento.value.find(emp => emp.id == empleadoId)
  return empleado ? empleado.nombre : 'Empleado'
}

// Formatear fecha para mostrar
function formatearFecha(fecha) {
  const date = new Date(fecha)
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

// Funciones de paginación
function irAPagina(pagina) {
  if (pagina !== '...' && pagina >= 1 && pagina <= totalPaginas.value) {
    paginaActual.value = pagina
  }
}

function paginaAnterior() {
  if (paginaActual.value > 1) {
    paginaActual.value--
  }
}

function paginaSiguiente() {
  if (paginaActual.value < totalPaginas.value) {
    paginaActual.value++
  }
}

function cambiarTareasPorPagina() {
  paginaActual.value = 1 // Resetear a la primera página
}

// Funciones de paginación para equipos
function irAPaginaEquipo(pagina) {
  if (pagina !== '...' && pagina >= 1 && pagina <= totalPaginasEquipos.value) {
    paginaActualEquipos.value = pagina
  }
}

function paginaEquipoAnterior() {
  if (paginaActualEquipos.value > 1) {
    paginaActualEquipos.value--
  }
}

function paginaEquipoSiguiente() {
  if (paginaActualEquipos.value < totalPaginasEquipos.value) {
    paginaActualEquipos.value++
  }
}

function cambiarEquiposPorPagina() {
  paginaActualEquipos.value = 1 // Resetear a la primera página
}

// Funciones de paginación para detalles de órdenes
function irAPaginaDetalle(pagina) {
  if (pagina !== '...' && pagina >= 1 && pagina <= totalPaginasDetalles.value) {
    paginaActualDetalles.value = pagina
  }
}

function paginaDetalleAnterior() {
  if (paginaActualDetalles.value > 1) {
    paginaActualDetalles.value--
  }
}

function paginaDetalleSiguiente() {
  if (paginaActualDetalles.value < totalPaginasDetalles.value) {
    paginaActualDetalles.value++
  }
}

function cambiarDetallesPorPagina() {
  paginaActualDetalles.value = 1 // Resetear a la primera página
}

// Obtener nombre del equipo por ID
function obtenerNombreEquipo(equipoId) {
  const equipo = equiposConOrdenes.value.find(eq => eq.id == equipoId)
  return equipo ? equipo.nombre : 'Equipo'
}

// Ver detalles de órdenes de un equipo específico
async function verDetallesEquipo(equipo) {
  if (!fechaInicio.value || !fechaFin.value) {
    alert('Por favor seleccione fechas')
    return
  }
  try {
    cargandoOrdenesEquipo.value = true
    equipoDetalleSeleccionado.value = equipo
    const response = await api.get('/api/mantenimiento/ordenes-por-equipo/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value,
        equipo_id: equipo.equipo_id
      }
    })
    ordenesEquipo.value = response.data
    mostrarDetallesEquipo.value = true
  } catch (error) {
    console.error('Error al obtener órdenes del equipo:', error)
    alert('Error al cargar las órdenes del equipo')
  } finally {
    cargandoOrdenesEquipo.value = false
  }
}

// Cerrar el modal de detalles de equipo
function cerrarDetallesEquipo() {
  mostrarDetallesEquipo.value = false
  equipoDetalleSeleccionado.value = null
  ordenesEquipo.value = []
  paginaActualDetalles.value = 1 // Resetear paginación
}

// Funciones para autocomplete de equipos
function seleccionarEquipo(equipo) {
  if (equipo) {
    equipoSeleccionado.value = equipo.id
    busquedaEquipo.value = equipo.nombre
  } else {
    equipoSeleccionado.value = ''
    busquedaEquipo.value = ''
  }
  mostrarListaEquipos.value = false
  equipoFocusIndex.value = -1
}

function mostrarDropdownEquipos() {
  mostrarListaEquipos.value = true
  equipoFocusIndex.value = -1
}

function ocultarDropdownEquipos() {
  // Usar timeout para permitir que el click en la lista se registre
  setTimeout(() => {
    mostrarListaEquipos.value = false
    equipoFocusIndex.value = -1
  }, 200)
}

function handleKeyDownEquipo(event) {
  if (!mostrarListaEquipos.value) {
    if (event.key === 'ArrowDown' || event.key === 'Enter') {
      mostrarListaEquipos.value = true
      return
    }
  }

  const equipos = equiposFiltrados.value
  
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    equipoFocusIndex.value = Math.min(equipoFocusIndex.value + 1, equipos.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    equipoFocusIndex.value = Math.max(equipoFocusIndex.value - 1, -1)
  } else if (event.key === 'Enter') {
    event.preventDefault()
    if (equipoFocusIndex.value >= 0 && equipoFocusIndex.value < equipos.length) {
      seleccionarEquipo(equipos[equipoFocusIndex.value])
    } else if (equipos.length === 1) {
      seleccionarEquipo(equipos[0])
    }
  } else if (event.key === 'Escape') {
    mostrarListaEquipos.value = false
    equipoFocusIndex.value = -1
  }
}

function limpiarBusquedaEquipo() {
  busquedaEquipo.value = ''
  equipoSeleccionado.value = ''
  mostrarListaEquipos.value = false
  equipoFocusIndex.value = -1
}

// Funciones para autocomplete de tipos de tareas
function seleccionarTipoTarea(tipo) {
  if (tipo) {
    tipoTareaSeleccionado.value = tipo.id
    busquedaTipoTarea.value = tipo.tarea
    console.log('Tipo de tarea seleccionado:', tipo.id, tipo.tarea)
  } else {
    tipoTareaSeleccionado.value = ''
    busquedaTipoTarea.value = ''
    console.log('Tipo de tarea limpiado')
  }
  mostrarListaTiposTareas.value = false
  tipoTareaFocusIndex.value = -1
}

function mostrarDropdownTiposTareas() {
  mostrarListaTiposTareas.value = true
  tipoTareaFocusIndex.value = -1
}

function ocultarDropdownTiposTareas() {
  // Usar timeout para permitir que el click en la lista se registre
  setTimeout(() => {
    mostrarListaTiposTareas.value = false
    tipoTareaFocusIndex.value = -1
  }, 200)
}

function handleKeyDownTipoTarea(event) {
  if (!mostrarListaTiposTareas.value) {
    if (event.key === 'ArrowDown' || event.key === 'Enter') {
      mostrarListaTiposTareas.value = true
      return
    }
  }

  const tipos = tiposTareasFiltrados.value
  
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    tipoTareaFocusIndex.value = Math.min(tipoTareaFocusIndex.value + 1, tipos.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    tipoTareaFocusIndex.value = Math.max(tipoTareaFocusIndex.value - 1, -1)
  } else if (event.key === 'Enter') {
    event.preventDefault()
    if (tipoTareaFocusIndex.value >= 0 && tipoTareaFocusIndex.value < tipos.length) {
      seleccionarTipoTarea(tipos[tipoTareaFocusIndex.value])
    } else if (tipos.length === 1) {
      seleccionarTipoTarea(tipos[0])
    }
  } else if (event.key === 'Escape') {
    mostrarListaTiposTareas.value = false
    tipoTareaFocusIndex.value = -1
  }
}

function limpiarBusquedaTipoTarea() {
  busquedaTipoTarea.value = ''
  tipoTareaSeleccionado.value = ''
  mostrarListaTiposTareas.value = false
  tipoTareaFocusIndex.value = -1
}

// Watch para abrir el dropdown cuando se escribe
watch(busquedaEquipo, (newVal) => {
  if (newVal && newVal.length > 0) {
    mostrarListaEquipos.value = true
    equipoFocusIndex.value = -1
  }
})

watch(busquedaTipoTarea, (newVal) => {
  if (newVal && newVal.length > 0) {
    mostrarListaTiposTareas.value = true
    tipoTareaFocusIndex.value = -1
  }
})

// Exportar órdenes de equipo a Excel
function exportarOrdenesEquipoAExcel() {
  if (!ordenesEquipo.value || ordenesEquipo.value.length === 0) {
    alert('No hay datos de órdenes para exportar.')
    return
  }

  // Crear datos para la hoja de resumen de órdenes
  const datosResumenOrdenes = ordenesEquipo.value.map(orden => ({
    'Orden de Servicio': orden.orden_servicio,
    'Fecha': orden.fecha,
    'Estado': orden.estado,
    'Equipo': orden.equipo,
    'Unidad de Negocio': orden.unidad_negocio,
    'Descripción': orden.descripcion,
    'Total Tareas': orden.total_tareas,
    'Tareas Preventivas': orden.tareas_preventivas,
    'Tareas Correctivas': orden.tareas_correctivas,
    'Horas Trabajo': orden.total_horas_trabajo,
    'Horas Extras': orden.total_horas_extras,
    'Costo Repuestos': orden.total_costo_repuestos,
    'Cantidad Mecánicos': orden.cantidad_mecanicos,
    'Mecánicos': orden.mecanicos_involucrados.join(', '),
    'Sectores': orden.sectores_involucrados.join(', '),
    'Observaciones': orden.observaciones
  }))

  // Crear datos para la hoja de detalles de tareas
  const datosDetallesTareas = []
  ordenesEquipo.value.forEach(orden => {
    orden.detalles.forEach(detalle => {
      datosDetallesTareas.push({
        'Orden de Servicio': orden.orden_servicio,
        'Fecha Orden': orden.fecha,
        'Estado Orden': orden.estado,
        'Mecánico': detalle.mecanico,
        'Sector': detalle.sector,
        'KM/Hora': detalle.km_hora || 0,
        'Hora Inicio': detalle.hora_inicio,
        'Hora Fin': detalle.hora_fin,
        'Horas Trabajadas': detalle.horas_trabajadas,
        'Horas Extras': detalle.horas_extras || '',
        'Tipo Preventivo': detalle.preventivo ? 'Sí' : 'No',
        'Tipo Correctivo': detalle.correctivo ? 'Sí' : 'No',
        'Detalle Tarea': detalle.detalle_tarea,
        'Observaciones': detalle.observaciones,
        'Repuesto': detalle.repuesto || '',
        'Cantidad Repuesto': detalle.cantidad_repuesto || '',
        'Precio Unitario': detalle.precio_unitario || '',
        'Costo Repuesto': detalle.costo_repuesto || ''
      })
    })
  })

  // Crear hojas de cálculo
  const worksheetResumen = XLSX.utils.json_to_sheet(datosResumenOrdenes)
  const worksheetDetalles = XLSX.utils.json_to_sheet(datosDetallesTareas)

  // Ajustar anchos de columnas para resumen
  const columnWidthsResumen = [
    { wch: 15 }, // Orden de Servicio
    { wch: 12 }, // Fecha
    { wch: 10 }, // Estado
    { wch: 25 }, // Equipo
    { wch: 20 }, // Unidad de Negocio
    { wch: 30 }, // Descripción
    { wch: 12 }, // Total Tareas
    { wch: 15 }, // Tareas Preventivas
    { wch: 15 }, // Tareas Correctivas
    { wch: 12 }, // Horas Trabajo
    { wch: 12 }, // Horas Extras
    { wch: 15 }, // Costo Repuestos
    { wch: 15 }, // Cantidad Mecánicos
    { wch: 40 }, // Mecánicos
    { wch: 30 }, // Sectores
    { wch: 40 }  // Observaciones
  ]

  // Ajustar anchos de columnas para detalles
  const columnWidthsDetalles = [
    { wch: 15 }, // Orden de Servicio
    { wch: 12 }, // Fecha Orden
    { wch: 10 }, // Estado Orden
    { wch: 20 }, // Mecánico
    { wch: 15 }, // Sector
    { wch: 12 }, // KM/Hora
    { wch: 12 }, // Hora Inicio
    { wch: 12 }, // Hora Fin
    { wch: 15 }, // Horas Trabajadas
    { wch: 12 }, // Horas Extras
    { wch: 15 }, // Tipo Preventivo
    { wch: 15 }, // Tipo Correctivo
    { wch: 50 }, // Detalle Tarea
    { wch: 30 }, // Observaciones
    { wch: 20 }, // Repuesto
    { wch: 15 }, // Cantidad Repuesto
    { wch: 15 }, // Precio Unitario
    { wch: 15 }  // Costo Repuesto
  ]

  worksheetResumen['!cols'] = columnWidthsResumen
  worksheetDetalles['!cols'] = columnWidthsDetalles

  // Crear libro de trabajo
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheetResumen, 'Resumen Órdenes')
  XLSX.utils.book_append_sheet(workbook, worksheetDetalles, 'Detalle Tareas')

  // Nombre del archivo
  const nombreEquipo = equipoDetalleSeleccionado.value?.equipo || 'Equipo'
  const fechaExportacion = new Date().toISOString().split('T')[0]
  const nombreArchivo = `Ordenes_${nombreEquipo.replace(/[^a-zA-Z0-9]/g, '_')}_${fechaInicio.value}_${fechaFin.value}_${fechaExportacion}.xlsx`

  // Descargar archivo
  XLSX.writeFile(workbook, nombreArchivo)
}

// Obtener detalles de un sector específico
async function obtenerDetallesSector(sector) {
  if (!fechaInicio.value || !fechaFin.value) {
    alert('Por favor seleccione fechas')
    return
  }
  try {
    cargandoDetallesSector.value = true
    sectorSeleccionado.value = sector
    const response = await api.get('/api/mantenimiento/detalles-sector/', {
      params: {
        fecha_inicio: fechaInicio.value,
        fecha_fin: fechaFin.value,
        sector: sector
      }
    })
    detallesSector.value = response.data
    mostrarDetallesSector.value = true
  } catch (error) {
    console.error("Error obteniendo detalles del sector:", error)
    alert('Error al obtener detalles del sector')
  } finally {
    cargandoDetallesSector.value = false
  }
}

// Cerrar modal de detalles
function cerrarDetallesSector() {
  mostrarDetallesSector.value = false
  sectorSeleccionado.value = ''
  detallesSector.value = []
}

onMounted(() => {
  // Establecer fechas por defecto (últimos 30 días)
  const hoy = new Date()
  const hace30Dias = new Date()
  hace30Dias.setDate(hoy.getDate() - 30)
  
  fechaFin.value = hoy.toISOString().split('T')[0]
  fechaInicio.value = hace30Dias.toISOString().split('T')[0]
})
function exportarDetallesAExcel() {
  if (!detallesSector.value || detallesSector.value.length === 0) {
    alert('No hay datos para exportar.')
    return
  }

  // Mapear los datos al formato deseado en Excel
  const datosParaExportar = detallesSector.value.map(detalle => ({
    'Fecha': detalle.fecha,
    'Mecánico': detalle.mecanico,
    'Hora Inicio': detalle.hora_inicio,
    'Hora Fin': detalle.hora_fin,
    'Horas Extras': detalle.horas_extras || '',
    'Observaciones': detalle.detalle_tarea,
    'OS': detalle.orden_servicio
  }))

  // Crear una hoja de cálculo
  const worksheet = XLSX.utils.json_to_sheet(datosParaExportar)

  // Ajustar el ancho de las columnas
  const columnWidths = [
    { wch: 12 }, // Fecha
    { wch: 20 }, // Mecánico
    { wch: 12 }, // Hora Inicio
    { wch: 12 }, // Hora Fin
    { wch: 12 }, // Horas Extras
    { wch: 40 }, // Observaciones
    { wch: 15 }  // OS
  ]
  worksheet['!cols'] = columnWidths

  // Crear libro de trabajo
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Detalles Sector')

  // Generar y descargar el archivo
  XLSX.writeFile(workbook, `detalles_sector_${sectorSeleccionado.value}_${fechaInicio.value}_a_${fechaFin.value}.xlsx`)
}
</script>


