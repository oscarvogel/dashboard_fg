<template>
  <div class="flex flex-col h-screen bg-primary-50 font-sans">
    <!-- Main -->
    <main class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <aside
        class="w-80 bg-white shadow-xl border-r border-gray-100 p-6 overflow-y-auto transform transition-transform duration-300 ease-in-out z-40
                fixed top-0 left-0 bottom-0
                sm:static sm:translate-x-0 sm:shadow-none sm:border-r sm:block"
        :class="{
          '-translate-x-full': isMobile && !showSidebar,
          'translate-x-0': isMobile && showSidebar
        }"
      >
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-semibold text-gray-800">🎛️ Filtros</h3>
          <button
            v-if="isMobile"
            @click="showSidebar = false"
            class="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            ✕
          </button>
        </div>
        <form @submit.prevent="aplicarFiltrosYBuscar" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha desde</label>
            <input
              v-model="filters.start_date"
              type="date"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha hasta</label>
            <input
              v-model="filters.end_date"
              type="date"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Unidades de Negocio</label>
            <div class="relative">
              <select 
                v-model="filters.cod_un" 
                multiple
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm min-h-[2.5rem]"
              >
                <option v-for="un in unidades" :key="un.id" :value="un.id">
                  {{ un.nombre }}
                </option>
              </select>
              <div class="text-xs text-gray-500 mt-1">Mantén Ctrl/Cmd para seleccionar múltiples</div>
              <!-- Mostrar elementos seleccionados -->
              <div v-if="filters.cod_un.length > 0" class="mt-2 flex flex-wrap gap-1">
                <span 
                  v-for="unId in filters.cod_un" 
                  :key="unId" 
                  class="multi-select-tag inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                >
                  {{ unidades.find(u => u.id == unId)?.nombre || unId }}
                  <button 
                    @click="removeUnidad(unId)"
                    class="ml-1 text-primary-600 hover:text-primary-800 rounded-full w-4 h-4 flex items-center justify-center"
                    title="Remover"
                  >
                    ×
                  </button>
                </span>
              </div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Operaciones</label>
            <div class="relative">
              <select
                v-model="filters.operacion"
                multiple
                class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm min-h-[2.5rem]"
              >
                <option v-for="op in operaciones" :key="op" :value="op">{{ op }}</option>
              </select>
              <div class="text-xs text-gray-500 mt-1">Mantén Ctrl/Cmd para seleccionar múltiples</div>
              <!-- Mostrar operaciones seleccionadas -->
              <div v-if="filters.operacion.length > 0" class="mt-2 flex flex-wrap gap-1">
                <span 
                  v-for="op in filters.operacion" 
                  :key="op" 
                  class="multi-select-tag inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                >
                  {{ op }}
                  <button 
                    @click="removeOperacion(op)"
                    class="ml-1 text-green-600 hover:text-green-800 rounded-full w-4 h-4 flex items-center justify-center"
                    title="Remover"
                  >
                    ×
                  </button>
                </span>
              </div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Operador</label>
            <select
              v-model="filters.operador"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Todos</option>
              <option v-for="op in operadores" :key="op.id" :value="op.id">{{ op.nombre }}</option>
            </select>
            <div v-if="loadingFiltros" class="text-xs text-primary-500 mt-1 animate-pulse">Cargando operadores...</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Equipo</label>
            <select
              v-model="filters.detalle_equipo"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Todos</option>
              <option v-for="eq in equipos" :key="eq" :value="eq">{{ eq }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Acta</label>
            <select
              v-model="filters.acta"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Todos</option>
              <option v-for="ac in actas" :key="ac" :value="ac">{{ ac }}</option>
            </select>
          </div>
          <!--Predios-->
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Predios</label>
            <select
              v-model="filters.predio"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
            >
              <option value="">Todos</option>
              <option v-for="pred in predios" :key="pred" :value="pred">{{ pred }}</option>
            </select>
          </div>          
          <button
            type="submit"
            :disabled="loading || loadingFiltros"
            class="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300 text-white font-semibold py-2 rounded-md transition-colors duration-200"
          >
            {{ loading || loadingFiltros ? 'Cargando...' : 'Aplicar Filtros y Buscar' }}
          </button>
        </form>
      </aside>

      <!-- Overlay móvil -->
      <div
        v-if="isMobile && showSidebar"
        @click="showSidebar = false"
        class="fixed inset-0 bg-black bg-opacity-50 z-10 lg:hidden"
      ></div>

      <!-- Contenido principal -->
      <section class="flex-1 p-6 overflow-y-auto">
        <!-- Botón filtros móvil -->
        <button
          v-if="isMobile"
          @click="showSidebar = true"
          class="mb-4 bg-primary-800 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm flex items-center gap-1"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filtros
        </button>

      <!-- KPIs -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-6">

        <!-- 🟩 Producción Total (importante) -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Producción Real</h3>
          <p class="text-xl font-bold text-primary-700">{{ formatNumber(totalProduccion) }} {{ unidad_produccion }}</p>
          <p class="text-sm text-gray-500 mt-1">
            <span :class="colorCumplimiento">{{ iconoCumplimiento }} {{ formatNumber(produccionEsperada) }} esperado</span>
          </p>
        </div>

        <!-- 🟥 Cumplimiento de Meta (NUEVO KPI IMPORTANTE) -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 100ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Cumplimiento</h3>
          <p 
            class="text-xl font-bold"
            :class="eficiencia < 90 ? 'text-primary-700' : eficiencia < 100 ? 'text-yellow-700' : 'text-primary-700'"
          >
            {{ eficiencia }}%
          </p>
          <p class="text-xs text-gray-500 mt-1">
            {{ eficiencia >= 100 ? 'Meta superada' : eficiencia >= 90 ? 'Cerca de la meta' : 'Estamos debajo de la meta' }}
          </p>
        </div>

        <!-- ⚙️ Total Horas -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 200ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Horas Trabajadas</h3>
          <p class="text-xl font-bold text-primary-700">{{ formatNumber(totalHoras) }} h</p>
        </div>

        <!-- ⛽ Combustible -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 300ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Combustible</h3>
          <p class="text-xl font-bold text-primary-700">{{ formatNumber(totalCombustible) }} L</p>
        </div>

        <!-- 🔥 Consumo por Hora -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 400ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Consumo por Hora</h3>
          <p class="text-xl font-bold text-primary-700">{{ consumoPorHora }} L/h</p>
        </div>

        <!-- 📉 Horas No Operativas -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 500ms">
          <div class="inline-flex p-2 bg-gray-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">No Operativas</h3>
          <p class="text-xl font-bold text-gray-700">{{ formatNumber(totalHrsNoOperativas) }} h</p>
        </div>

        <!-- 🏭 Stock ABC (menos prioritario) -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 600ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0v10l-8 4-8-4V7" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Stock ABC</h3>
          <p class="text-xl font-bold text-primary-700">{{ formatNumber(totalStockABC) }} TN</p>
        </div>

        <!-- 🏭 Horas a disposicion -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 600ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Hrs. a Disposición</h3>
          <p class="text-xl font-bold text-primary-700">{{ formatNumber(totalHrsDisposicion) }} Hrs</p>
        </div>

        <!-- 🏭 Horas de remolque -->
        <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 text-center transform hover:-translate-y-1 animate-fade-in-up" style="animation-delay: 700ms">
          <div class="inline-flex p-2 bg-primary-100 rounded-lg mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10m10 0h2m-2 0a2 2 0 11-4 0m4 0a2 2 0 10-4 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0m0 0h1a1 1 0 001-1v-3.586a1 1 0 00-.293-.707l-2.414-2.414A1 1 0 0017.586 8H15" />
            </svg>
          </div>
          <h3 class="text-sm font-medium text-gray-500 mb-1">Hrs. Remolque</h3>
          <p class="text-xl font-bold text-primary-700">{{ formatNumber(totalHrsRemolque) }} Hrs</p>
        </div>

      </div>

        <!-- Pestañas de Gráficos -->
        <div class="bg-white rounded-lg shadow mb-6">
          <!-- Pestañas -->
          <div class="border-b border-gray-200">
            <nav class="flex overflow-x-auto -mb-px">
              <button
                @click="activeTab = 'produccion-horas'"
                :class="[
                  'whitespace-nowrap py-4 px-6 text-sm font-medium border-b-2 transition-colors duration-200',
                  activeTab === 'produccion-horas'
                    ? 'border-primary-500 text-primary-600 bg-primary-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                ]"
              >
                Producción y Horas
              </button>
              <button
                @click="activeTab = 'acumulado'"
                :class="[
                  'whitespace-nowrap py-4 px-6 text-sm font-medium border-b-2 transition-colors duration-200',
                  activeTab === 'acumulado'
                    ? 'border-primary-500 text-primary-600 bg-primary-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                ]"
              >
                Acumulado Real vs Esperado
              </button>
              <button
                @click="activeTab = 'combustible'"
                :class="[
                  'whitespace-nowrap py-4 px-6 text-sm font-medium border-b-2 transition-colors duration-200',
                  activeTab === 'combustible'
                    ? 'border-primary-500 text-primary-600 bg-primary-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                ]"
              >
                Combustible
              </button>
              <button
                @click="activeTab = 'consumo-hora'"
                :class="[
                  'whitespace-nowrap py-4 px-6 text-sm font-medium border-b-2 transition-colors duration-200',
                  activeTab === 'consumo-hora'
                    ? 'border-primary-500 text-primary-600 bg-primary-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                ]"
              >
                Consumo por Hora
              </button>
            </nav>
          </div>

          <!-- Contenido de las pestañas -->
          <div class="p-6">
            <!-- Tab 1: Producción y Horas -->
            <div v-show="activeTab === 'produccion-horas'">
              <h2 class="text-xl font-semibold mb-4">Producción y Horas Trabajadas por Día</h2>
              <div v-if="loading" class="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                  <p class="text-gray-600 font-medium">Cargando datos del gráfico...</p>
                </div>
              </div>
              <BarChart
                v-else
                :chart-data="chartDataProduccionHoras"
                :options="chartOptionsProduccionHoras"
                :height="400"
              />
            </div>

            <!-- Tab 2: Acumulado -->
            <div v-show="activeTab === 'acumulado'">
              <h2 class="text-xl font-semibold mb-4">Avance Acumulado: Real vs Esperado</h2>
              <div v-if="loading" class="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                  <p class="text-gray-600 font-medium">Cargando datos del gráfico...</p>
                </div>
              </div>
              <BarChart
                v-else
                :chart-data="chartDataAcumulado"
                :options="chartOptionsAcumulado"
                :height="400"
              />
            </div>

            <!-- Tab 3: Combustible -->
            <div v-show="activeTab === 'combustible'">
              <h2 class="text-xl font-semibold mb-4">Combustible por Día (L)</h2>
              <div v-if="loading" class="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                  <p class="text-gray-600 font-medium">Cargando datos del gráfico...</p>
                </div>
              </div>
              <BarChart
                v-else
                :chart-data="chartDataCombustible"
                :height="400"
              />
            </div>

            <!-- Tab 4: Consumo por Hora -->
            <div v-show="activeTab === 'consumo-hora'">
              <h2 class="text-xl font-semibold mb-4">Consumo por Hora (L/h)</h2>
              <div v-if="loading" class="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                  <p class="text-gray-600 font-medium">Cargando datos del gráfico...</p>
                </div>
              </div>
              <BarChart
                v-else
                :chart-data="chartDataConsumoHora"
                :options="chartOptionsConsumoHora"
                :height="400"
              />
            </div>
          </div>
        </div>
        
        <!-- Tabla -->
        <div class="bg-white shadow rounded-lg overflow-hidden">
          <!-- Botón Exportar a Excel -->
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div class="text-sm text-gray-600">
              Total registros filtrados: <span class="font-semibold">{{ totalRegistros }}</span>
            </div>
            <button
              @click="exportarRegistrosAExcel"
              :disabled="totalRegistros === 0"
              class="bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium py-2 px-4 rounded-md shadow-sm transition flex items-center gap-2"
            >
              <i class="fas fa-file-excel"></i>
              Exportar a Excel
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-100">
                <tr>
                  <!-- Fecha -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('fecha')"
                  >
                    Fecha
                    <template v-if="ordenarPor === 'fecha'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-primary-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Hr Inicio</th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Hr Fin</th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Hrs Remolque</th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Hrs Disposición</th>

                  <!-- Operación -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('operacion')"
                  >
                    Operacion
                    <template v-if="ordenarPor === 'operacion'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-primary-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">UN Prod</th>
                  
                  <!-- UN -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('un')"
                  >
                    UN
                    <template v-if="ordenarPor === 'un'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-primary-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>

                  <!-- Equipo -->
                  <th 
                    class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200"
                    @click="cambiarOrden('equipo')"
                  >
                    Equipo
                    <template v-if="ordenarPor === 'equipo'">
                      <i v-if="ordenAsc" class="fas fa-sort-up text-primary-600 ml-1"></i>
                      <i v-else class="fas fa-sort-down text-red-600 ml-1"></i>
                    </template>
                    <i v-else class="fas fa-sort text-gray-400 ml-1"></i>
                  </th>
                  <!-- Produccion -->
                  <th class="border border-gray-300 px-3 py-2 text-xs sm:text-sm font-semibold cursor-pointer hover:bg-gray-200">Produccion</th>

                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="r in cargasPaginaActual" :key="r.id" class="hover:bg-primary-50 even:bg-gray-50">
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.fecha }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.hr_inicio }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.hr_fin }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.hr_remolque }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.hr_disposicion }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.operacion }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.unidad_produccion }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.unidad_negocio_detalle }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.equipo_detalle }}</td>
                  <td class="px-6 py-4 text-sm text-gray-800">{{ r.produccion }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="!loading && totalRegistros > 0" class="border-t border-gray-200 px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div class="text-sm text-gray-600">
              Mostrando {{ inicioPagina }}-{{ finPagina }} de {{ totalRegistros }}
            </div>
            <div class="flex items-center gap-3">
              <label class="text-sm text-gray-600" for="filasPorPagina">Filas:</label>
              <select
                id="filasPorPagina"
                v-model.number="filasPorPagina"
                class="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>

              <button
                @click="irPaginaAnterior"
                :disabled="paginaActual === 1"
                class="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-40"
              >
                Anterior
              </button>
              <span class="text-sm text-gray-700">Página {{ paginaActual }} / {{ totalPaginas }}</span>
              <button
                @click="irPaginaSiguiente"
                :disabled="paginaActual === totalPaginas"
                class="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
          <div v-if="loading" class="flex justify-center items-center py-6">
            <svg class="animate-spin h-5 w-5 text-primary-600 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Cargando datos...
          </div>
          <div v-if="!loading && registros.length === 0" class="text-center py-6 text-gray-500">
            No se encontraron registros.
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import api from '../services/api'
import BarChart from '../components/BarChart.vue'

const produccionEsperada = ref(0)
const totalCombustible = ref(0)
const produccionEsperadaPorDia = ref({})
const empleado = ref(null)
const router = useRouter()
const ordenarPor = ref('') // campo por el que se ordena: 'fecha', 'equipo', 'un', 'operacion'
const ordenAsc = ref(true) // true = ascendente, false = descendente
const activeTab = ref('produccion-horas') // Pestaña activa por defecto

const filters = ref({
  start_date: '',
  end_date: '',
  cod_un: [],  // ✅ Array para múltiples IDs
  operacion: [],  // ✅ Array para múltiples operaciones
  detalle_equipo: '',
  operador: '',
  acta: '',
  predio: '',
})

const operaciones = ref([])
const unidades = ref([])
const equipos = ref([])
const operadores = ref([])
const actas = ref([])
const predios = ref([])
const unidad_produccion = ref('')

const registros = ref([])
const registrosResumen = ref([])
const loading = ref(false)
const loadingFiltros = ref(false)
const showSidebar = ref(false)
const isMobile = computed(() => window.innerWidth < 1024)
const paginaActual = ref(1)
const filasPorPagina = ref(20)
const totalRegistros = ref(0)

const normalizarFiltrosParaApi = () => {
  const params = { ...filters.value }

  if (Array.isArray(params.cod_un) && params.cod_un.length > 0) {
    params.cod_un = params.cod_un.join(',')
  } else {
    delete params.cod_un
  }

  if (Array.isArray(params.operacion) && params.operacion.length > 0) {
    params.operacion = params.operacion.join(',')
  } else {
    delete params.operacion
  }

  return params
}

const obtenerTodosLosRegistrosFiltrados = async (paramsBase) => {
  const pageSize = 100
  let firstResponse = null
  const resultados = []

  const primeraResponse = await api.get('/api/produccion-dashboard/', {
    params: { ...paramsBase, page_size: pageSize, page: 1 }
  })

  firstResponse = primeraResponse.data
  resultados.push(...(primeraResponse.data?.results || []))

  const totalPages = Number(primeraResponse.data?.total_pages || 1)

  for (let page = 2; page <= totalPages; page += 1) {
    const response = await api.get('/api/produccion-dashboard/', {
      params: { ...paramsBase, page_size: pageSize, page }
    })
    resultados.push(...(response.data?.results || []))
  }

  return {
    datosMeta: firstResponse || {},
    registros: resultados
  }
}

// KPIs
const totalProduccion = computed(() => {
  return registrosResumen.value.reduce((sum, r) => sum + parseFloat(r.produccion || 0), 0)
})

const totalHrsDisposicion = computed(() => {
  return registrosResumen.value.reduce((sum, r) => sum + parseFloat(r.hr_disposicion || 0), 0)
})

const totalHrsRemolque = computed(() => {
  return registrosResumen.value.reduce((sum, r) => sum + parseFloat(r.hr_remolque || 0), 0)
})

const desvioAbsoluto = computed(() => {
  return totalProduccion.value - parseFloat(produccionEsperada.value || 0)
})

const desvioPorcentual = computed(() => {
  const esperada = parseFloat(produccionEsperada.value || 0)
  const real = totalProduccion.value

  if (esperada === 0) return real > 0 ? Infinity : 0 // Evitar división por cero

  return ((real - esperada) / esperada) * 100
})

const totalStockABC = computed(() => {
  if (registrosResumen.value.length === 0) return 0
  const fechaMaxima = registrosResumen.value.reduce((max, r) => (r.fecha > max ? r.fecha : max), '')
  return registrosResumen.value
    .filter(r => r.fecha === fechaMaxima)
    .reduce((sum, r) => sum + (parseFloat(r.stock_abc) || 0), 0)
})
const totalHrsNoOperativas = computed(() => {
  return registrosResumen.value.reduce((sum, r) => sum + parseFloat(r.hrs_no_operativas || 0), 0)
})
// const totalCombustible = computed(() => {
//   return registros.value.reduce((sum, r) => sum + parseFloat(r.combustible || 0), 0)
// })
const totalHoras = computed(() => {
  return registrosResumen.value.reduce((sum, r) => {
    const inicio = parseFloat(r.hr_inicio || 0)
    const fin = parseFloat(r.hr_fin || 0)
    return sum + Math.max(0, fin - inicio)
  }, 0)
})

// const eficiencia = computed(() => {
//   const prod = totalProduccion.value
//   const comb = totalCombustible.value
//   return comb > 0 ? (prod / comb).toFixed(2) : 0
// })
// const totalProduccion = computed(() => {
//   return registros.value.reduce((sum, r) => sum + parseFloat(r.produccion || 0), 0)
// })

const eficiencia = computed(() => {
  const esperada = parseFloat(produccionEsperada.value || 0)
  const real = totalProduccion.value

  if (esperada === 0) return real === 0 ? 100 : 0 // O Infinity, según tu necesidad

  return parseFloat(((real / esperada) * 100).toFixed(2))
})

const consumoPorHora = computed(() => {
  return totalHoras.value > 0 ? (totalCombustible.value / totalHoras.value).toFixed(2) : 0
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

const chartDataAcumulado = computed(() => {
  const data = {}
  registrosResumen.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!data[fecha]) {
      data[fecha] = { produccion: 0 }
    }
    data[fecha].produccion += parseFloat(r.produccion || 0)
  })

  const labels = Object.keys(data).sort()

  // Producción real diaria
  const produccionReal = labels.map(fecha => data[fecha].produccion)

  // Producción esperada diaria (del backend)
  const produccionEsperadaData = labels.map(fecha => produccionEsperadaPorDia.value[fecha] || 0)

  // Acumulados
  let acumuladoReal = 0
  let acumuladoEsperado = 0
  const acumuladoRealData = []
  const acumuladoEsperadoData = []

  labels.forEach((fecha, index) => {
    acumuladoReal += produccionReal[index]
    acumuladoEsperado += produccionEsperadaData[index]
    acumuladoRealData.push(acumuladoReal)
    acumuladoEsperadoData.push(acumuladoEsperado)
  })

  return {
    labels,
    datasets: [
      {
        label: 'Acumulado Real',
        data: acumuladoRealData,
        borderColor: '#22C55E', // primary-500
        backgroundColor: 'rgba(34, 197, 94, 0.1)', // primary-500 with opacity
        borderWidth: 3,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: '#22C55E', // primary-500
        pointRadius: 4,
        type: 'line'
      },
      {
        label: 'Acumulado Esperado',
        data: acumuladoEsperadoData,
        borderColor: 'rgba(250, 204, 21, 1)', // yellow-400
        backgroundColor: 'rgba(250, 204, 21, 0.1)', // yellow-400
        borderWidth: 3,
        borderDash: [6, 4],
        fill: false,
        tension: 0.3,
        pointBackgroundColor: 'rgba(250, 204, 21, 1)', // yellow-400
        pointRadius: 4,
        type: 'line'
      }
    ]
  }
})

const chartOptionsAcumulado = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    tooltip: {
      callbacks: {
        afterLabel: (tooltipItem) => {
          const dataIndex = tooltipItem.dataIndex
          const real = chartDataAcumulado.value.datasets[0].data[dataIndex]
          const esperado = chartDataAcumulado.value.datasets[1].data[dataIndex]
          const porcentaje = esperado > 0 ? ((real / esperado) * 100).toFixed(1) : 0
          return `→ Cumplimiento: ${porcentaje}%`
        }
      }
    }
  },
  scales: {
    y: {
      type: 'linear',
      display: true,
      title: {
        display: true,
        text: 'Producción Acumulada (TN)'
      }
    },
    x: {
      title: {
        display: true,
        text: 'Fecha'
      }
    }
  }
}

// Gráfico Producción y Horas
const chartDataProduccionHoras = computed(() => {
  const data = {}
  registrosResumen.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!data[fecha]) data[fecha] = { produccion: 0, horas: 0 }
    data[fecha].produccion += parseFloat(r.produccion || 0)
    const horas = Math.max(0, parseFloat(r.hr_fin || 0) - parseFloat(r.hr_inicio || 0))
    data[fecha].horas += horas
  })

  const labels = Object.keys(data).sort()
  const produccionReal = labels.map(fecha => data[fecha].produccion)
  
  const produccionEsperadaData = labels.map(fecha => produccionEsperadaPorDia.value[fecha] || 0)
  const horasData = labels.map(fecha => data[fecha].horas)

  return {
    labels,
    datasets: [
      {
        label: 'Producción Esperada',
        data: produccionEsperadaData,
        backgroundColor: 'rgba(250, 204, 21, 0.6)', // yellow-400
        borderColor: 'rgba(250, 204, 21, 1)', // yellow-400
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y',
        order: 1
      },
      {
        label: 'Producción Real',
        data: produccionReal,
        backgroundColor: 'rgba(34, 197, 94, 0.6)', // primary-500
        borderColor: '#22C55E', // primary-500
        borderWidth: 1,
        type: 'bar',
        yAxisID: 'y',
        order: 2
      },
      {
        label: 'Horas Trabajadas',
        data: horasData,
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 2,
        type: 'line',
        fill: false,
        tension: 0.3,
        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
        pointRadius: 4,
        yAxisID: 'y1'
      }
    ]
  }
})

const chartOptionsProduccionHoras = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    tooltip: {
      callbacks: {
        afterLabel: (tooltipItem) => {
          const fecha = tooltipItem.label
          const real = tooltipItem.dataset.data[tooltipItem.dataIndex]
          const esperado = chartDataProduccionHoras.value.datasets[0].data[tooltipItem.dataIndex]
          if (tooltipItem.dataset.label === 'Producción Real' && esperado > 0) {
            const porcentaje = ((real / esperado) * 100).toFixed(1)
            return `→ Cumplimiento: ${porcentaje}%`
          }
          return ''
        }
      }
    }
  },
  scales: {
    y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Producción (TN)' } },
    y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Horas trabajadas' }, grid: { drawOnChartArea: false } }
  }
}

// Otros gráficos
const chartDataCombustible = computed(() => {
  const data = {}
  registrosResumen.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    data[fecha] = (data[fecha] || 0) + parseFloat(r.combustible || 0)
  })
  return {
    labels: Object.keys(data),
    datasets: [{ label: 'Combustible (L)', data: Object.values(data), backgroundColor: 'rgba(34, 197, 94, 0.6)', borderColor: '#22C55E', borderWidth: 1 }]
  }
})

const chartDataConsumoHora = computed(() => {
  const dataPorFecha = {}

  registrosResumen.value.forEach(r => {
    const fecha = r.fecha || 'Sin fecha'
    if (!dataPorFecha[fecha]) dataPorFecha[fecha] = { combustible: 0, horas: 0 }

    dataPorFecha[fecha].combustible += parseFloat(r.combustible || 0)
    dataPorFecha[fecha].horas += Math.max(0, parseFloat(r.hr_fin || 0) - parseFloat(r.hr_inicio || 0))
  })

  const fechas = Object.keys(dataPorFecha).sort()

  // Calcular consumo por hora (L/h), evitando división por cero
  const consumoPorHora = fechas.map(fecha => {
    const { combustible, horas } = dataPorFecha[fecha]
    return horas > 0 ? combustible / horas : 0 // Si no hay horas, pones 0 o null si prefieres omitirlo
  })

  return {
    labels: fechas,
    datasets: [
      {
        label: 'Consumo por Hora (L/h)',
        data: consumoPorHora,
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1,
        yAxisID: 'y'
      }
    ]
  }
})

const chartOptionsConsumoHora = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { 
    mode: 'index', 
    intersect: false 
  },
  scales: {
    // Eliminamos y1 porque ya no hay horas como dataset
    y: {
      type: 'linear',
      display: true,
      position: 'left',
      title: {
        display: true,
        text: 'Consumo por Hora (L/h)'  // Título actualizado
      }
    }
    // y1 eliminado
  }
}

// Cargar filtros
const cargarFiltros = async () => {
  if (!filters.value.start_date || !filters.value.end_date) return
  loadingFiltros.value = true
  try {
    const params = normalizarFiltrosParaApi()
    if (!params.un) delete params.un
    const response = await api.get('/api/filtros/', { params })
    unidades.value = response.data.unidades || []
    operaciones.value = response.data.operaciones || []
    equipos.value = response.data.equipos || []
    operadores.value = response.data.operadores || []
    actas.value = response.data.actas || []
    predios.value = response.data.predios || []
  } catch (error) {
    console.error('Error al cargar filtros:', error)
  } finally {
    loadingFiltros.value = false
  }
}

// Cargar producción
const fetchProduccion = async (actualizarResumen = false) => {
  loading.value = true
  try {
    const params = normalizarFiltrosParaApi()
    params.page = paginaActual.value
    params.page_size = filasPorPagina.value
    const response = await api.get('/api/produccion-dashboard/', { params })

    registros.value = response.data.results || []
    totalRegistros.value = Number(response.data.count || 0)

    if (actualizarResumen || registrosResumen.value.length === 0) {
      const { datosMeta, registros: registrosCompletos } = await obtenerTodosLosRegistrosFiltrados(normalizarFiltrosParaApi())
      registrosResumen.value = registrosCompletos
      produccionEsperada.value = datosMeta.produccion_esperada_acumulada || 0
      produccionEsperadaPorDia.value = datosMeta.produccion_esperada_por_dia || {}
      totalCombustible.value = datosMeta.consumo_combustible_total || 0
      unidad_produccion.value = datosMeta.unidad_produccion || ''
    }

    showSidebar.value = false
  } catch (error) {
    console.error('Error al cargar producción:', error)
  } finally {
    loading.value = false
  }
}

// Observar cambios en fechas
watch(() => [filters.value.start_date, filters.value.end_date], () => {
  if (filters.value.start_date && filters.value.end_date) {
    cargarFiltros()
  }
})

// No cargar automáticamente los componentes al cambiar filtros
// El usuario debe hacer clic en "Actualizar" para cargar los datos

// Logout
const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('empleado')
  router.push('/')
}

// Formatear números
const formatNumber = (num) => {
  const n = isNaN(parseFloat(num)) ? 0 : parseFloat(num)
  return n.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')
}

onMounted(() => {
  const emp = localStorage.getItem('empleado')
  if (!emp) return router.push('/')
  empleado.value = JSON.parse(emp)
  const today = new Date()
  const from = new Date()
  from.setDate(today.getDate() - 30)
  filters.value.start_date = from.toISOString().split('T')[0]
  filters.value.end_date = today.toISOString().split('T')[0]
  cargarFiltros()
  fetchProduccion(true)
})

const exportarRegistrosAExcel = () => {
  if (!filters.value.start_date || !filters.value.end_date) return

  const params = normalizarFiltrosParaApi()

  obtenerTodosLosRegistrosFiltrados(params)
    .then(({ registros: registrosCompletos }) => {
      const datos = registrosCompletos.map(r => ({
        'Fecha': r.fecha,
        'Hora Inicio': r.hr_inicio,
        'Hora Fin': r.hr_fin,
        'Horas Remolque': r.hr_remolque,
        'Horas a Disposición': r.hr_disposicion,
        'Operación': r.operacion,
        'Unidad de Producción': r.unidad_produccion,
        'Unidad de Negocio': r.unidad_negocio_detalle,
        'Equipo': r.equipo_detalle,
        'Producción': r.produccion
      }))

      const ws = XLSX.utils.json_to_sheet(datos)
      ws['!cols'] = [
        { wch: 12 },
        { wch: 15 },
        { wch: 15 },
        { wch: 18 },
        { wch: 20 },
        { wch: 15 },
        { wch: 15 },
        { wch: 20 },
        { wch: 25 },
        { wch: 15 }
      ]

      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, 'Registros de Producción')
      XLSX.writeFile(wb, `Registros_Produccion_${new Date().toISOString().slice(0,10)}.xlsx`)
    })
    .catch((error) => {
      console.error('Error al exportar Excel:', error)
    })
}

const irPaginaAnterior = async () => {
  if (paginaActual.value <= 1) return
  paginaActual.value -= 1
  await fetchProduccion(false)
}

const irPaginaSiguiente = async () => {
  if (paginaActual.value >= totalPaginas.value) return
  paginaActual.value += 1
  await fetchProduccion(false)
}

const cargasOrdenadas = computed(() => {
  const arr = [...registros.value]

  if (!ordenarPor.value) return arr

  arr.sort((a, b) => {
    let valA
    let valB

    switch (ordenarPor.value) {
      case 'fecha':
        valA = a.fecha
        valB = b.fecha
        break
      case 'equipo':
        valA = a.equipo_detalle?.toLowerCase() || ''
        valB = b.equipo_detalle?.toLowerCase() || ''
        break
      case 'un':
        valA = a.unidad_negocio_detalle?.toLowerCase() || ''
        valB = b.unidad_negocio_detalle?.toLowerCase() || ''
        break
      case 'operacion':
        valA = a.operacion?.toLowerCase() || ''
        valB = b.operacion?.toLowerCase() || ''
        break
      default:
        return 0
    }

    if (valA < valB) return ordenAsc.value ? -1 : 1
    if (valA > valB) return ordenAsc.value ? 1 : -1
    return 0
  })

  return arr
})

const cargasPaginaActual = computed(() => cargasOrdenadas.value)

const totalPaginas = computed(() => {
  if (totalRegistros.value === 0) return 1
  return Math.max(1, Math.ceil(totalRegistros.value / filasPorPagina.value))
})

const inicioPagina = computed(() => {
  if (totalRegistros.value === 0) return 0
  return (paginaActual.value - 1) * filasPorPagina.value + 1
})

const finPagina = computed(() => {
  if (totalRegistros.value === 0) return 0
  return Math.min(paginaActual.value * filasPorPagina.value, totalRegistros.value)
})

const removeUnidad = (unidadId) => {
  filters.value.cod_un = filters.value.cod_un.filter(id => id != unidadId)
}

const removeOperacion = (operacion) => {
  filters.value.operacion = filters.value.operacion.filter(op => op !== operacion)
}

const aplicarFiltrosYBuscar = async () => {
  paginaActual.value = 1
  await cargarFiltros()
  await fetchProduccion(true)
}

const cambiarOrden = (campo) => {
  if (ordenarPor.value === campo) {
    ordenAsc.value = !ordenAsc.value
  } else {
    ordenarPor.value = campo
    ordenAsc.value = true
  }
}

watch(filasPorPagina, async () => {
  paginaActual.value = 1
  await fetchProduccion(false)
})

watch(totalPaginas, (nuevoTotal) => {
  if (paginaActual.value > nuevoTotal) {
    paginaActual.value = nuevoTotal
  }
})
</script>

<style>
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fade-in-up 0.5s ease-out forwards; }

/* Estilos para multi-select tags */
.multi-select-tag {
  transition: all 0.2s ease;
}

.multi-select-tag:hover {
  transform: scale(1.05);
}

.multi-select-tag button:hover {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 50%;
}

/* Estilos para móviles */
@media (max-width: 640px) {
  nav.flex {
    padding-bottom: 0.5rem;
  }
  
  nav.flex button {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
  }
  
  .p-6 {
    padding: 1rem;
  }
}
</style>
