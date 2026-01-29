<template>
  <div class="min-h-screen bg-primary-50 py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <!-- Título -->
      <h2 class="text-3xl font-bold text-gray-800 mb-6 text-center">
        Control de Máquinas por Frente y Operador
      </h2>

      <!-- Fila 1: Fechas y Frente -->
      <div class="bg-white shadow-md rounded-lg p-6 mb-4 border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-700 mb-4">Filtros principales</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha Inicio</label>
            <input
              type="date"
              v-model="fechaInicio"
              @change="guardarFechas"
              class="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 transition"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Fecha Fin</label>
            <input
              type="date"
              v-model="fechaFin"
              @change="guardarFechas"
              class="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 transition"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Frente de Trabajo</label>
            <div class="relative">
              <select
                v-model="frenteSeleccionado"
                :disabled="cargandoFrentes"
                class="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 transition bg-white disabled:bg-gray-100"
              >
                <option value="">Todos los frentes</option>
                <option v-for="frente in frentes" :key="frente.id" :value="frente.id">
                  {{ frente.nombre }}
                </option>
              </select>
              <div v-if="cargandoFrentes" class="absolute inset-y-0 right-3 flex items-center">
                <svg class="animate-spin h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Fila 2: Búsqueda interactiva (opcional: puedes combinar con anterior)
      <div class="bg-white shadow-md rounded-lg p-6 mb-4 border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-700 mb-4">Búsqueda rápida</h3>
        <div class="flex flex-col md:flex-row gap-4">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-600 mb-1 sr-only">Buscar equipo</label>
            <input
              v-model="busqueda"
              type="text"
              placeholder="Buscar por patente o detalle del equipo..."
              class="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 transition"
            />
          </div>
        </div>
      </div> -->

      <!-- Fila 3: Botones de acción -->
      <div class="flex flex-wrap gap-3 justify-center mb-6">
        <button
          @click="obtenerDatos"
          :disabled="cargando || !fechaInicio || !fechaFin"
          class="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white font-medium py-2 px-6 rounded-md shadow transition flex items-center"
        >
          <svg v-if="cargando" class="animate-spin -ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ cargando ? 'Cargando...' : 'Actualizar Datos' }}
        </button>

        <button
          @click="exportarAExcel"
          :disabled="datos.length === 0 || cargando"
          class="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white font-medium py-2 px-6 rounded-md shadow transition flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Exportar a Excel
        </button>

        <button
          @click="limpiarFiltros"
          class="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-6 rounded-md shadow transition"
        >
          Limpiar Filtros
        </button>
      </div>

      <!-- Tabla de resultados -->
      <div v-if="resultadosFiltrados.length > 0" class="bg-white shadow-md rounded-lg overflow-hidden border border-gray-200">
        <div class="p-4 bg-gray-50 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-700">
            Resultados ({{ resultadosFiltrados.length }} de {{ datos.length }})
          </h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full table-auto">
            <thead class="bg-gray-100 text-gray-700 text-sm uppercase tracking-wider">
              <tr>
                <th class="px-6 py-3 text-left font-semibold">Patente</th>
                <th class="px-6 py-3 text-left font-semibold">Detalle Equipo</th>
                <th class="px-6 py-3 text-left font-semibold">Frente</th>
                <th class="px-6 py-3 text-left font-semibold">Operador</th>
                <th class="px-6 py-3 text-left font-semibold">Última Fecha</th>
                <th class="px-6 py-3 text-left font-semibold">Última Hr Fin</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr
                v-for="item in resultadosFiltrados"
                :key="item.cod_equipo + '-' + item.ultima_fecha"
                class="hover:bg-primary-50 transition duration-150"
              >
                <td class="px-6 py-4 text-sm text-gray-800 font-mono">{{ item.cod_equipo }}</td>
                <td class="px-6 py-4 text-sm text-gray-700">{{ item.detalle_equipo }}</td>
                <td class="px-6 py-4 text-sm text-gray-800">{{ item.frente || 'N/A' }}</td>
                <td class="px-6 py-4 text-sm text-gray-800">{{ item.operador }}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{{ item.ultima_fecha }}</td>
                <td class="px-6 py-4 text-sm text-gray-600 font-mono">{{ item.ultima_hr_fin }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Estado: Cargando -->
      <div v-else-if="cargando" class="flex justify-center items-center py-12">
        <div class="flex flex-col items-center">
          <svg class="animate-spin h-10 w-10 text-primary-600 mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-gray-600 text-lg">Cargando datos...</p>
        </div>
      </div>

      <!-- Estado: Sin datos -->
      <div v-else class="bg-white border border-gray-200 rounded-lg p-8 text-center shadow-sm">
        <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p class="text-gray-500 text-lg">
          {{
            !fechaInicio || !fechaFin
              ? 'Selecciona un rango de fechas para comenzar.'
              : frentes.length === 0
                ? 'No hay frentes con registros en este periodo.'
                : resultadosFiltrados.length === 0
                  ? 'No se encontraron equipos que coincidan con la búsqueda.'
                  : 'No hay máquinas asignadas para los filtros seleccionados.'
          }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';
import * as XLSX from 'xlsx';

export default {
  name: 'MaquinasPorFrente',
  data() {
    return {
      fechaInicio: '',
      fechaFin: '',
      frenteSeleccionado: '',
      busqueda: '',           // Búsqueda específica (patente o detalle)
      busquedaGlobal: '',     // Opcional: puedes usar solo una
      frentes: [],
      datos: [],
      cargando: false,
      cargandoFrentes: false,
      keyFechas: 'rangoFechas_MaquinasFrente'
    };
  },
  computed: {
    resultadosFiltrados() {
      const busq = this.busqueda.toLowerCase().trim();
      if (!busq) return this.datos;

      return this.datos.filter(item =>
        (item.cod_equipo && item.cod_equipo.toLowerCase().includes(busq)) ||
        (item.detalle_equipo && item.detalle_equipo.toLowerCase().includes(busq))
      );
    }
  },
  mounted() {
    this.cargarFechasGuardadas();
    if (this.fechaInicio && this.fechaFin) {
      this.cargarFrentes();
    }
  },
  methods: {
    formatearFecha(date) {
      const d = new Date(date);
      return d.toISOString().split('T')[0];
    },
    obtenerRangoDefault() {
      const hoy = new Date();
      const inicio = new Date();
      inicio.setDate(hoy.getDate() - 7);
      return {
        inicio: this.formatearFecha(inicio),
        fin: this.formatearFecha(hoy)
      };
    },
    cargarFechasGuardadas() {
      const guardado = localStorage.getItem(this.keyFechas);
      if (guardado) {
        const { inicio, fin } = JSON.parse(guardado);
        this.fechaInicio = inicio;
        this.fechaFin = fin;
      } else {
        const { inicio, fin } = this.obtenerRangoDefault();
        this.fechaInicio = inicio;
        this.fechaFin = fin;
      }
    },
    guardarFechas() {
      localStorage.setItem(this.keyFechas, JSON.stringify({
        inicio: this.fechaInicio,
        fin: this.fechaFin
      }));
      this.cargarFrentes();
    },
    async cargarFrentes() {
      if (!this.fechaInicio || !this.fechaFin) return;

      this.cargandoFrentes = true;
      try {
        const response = await api.get('/api/filtros/', {
          params: {
            start_date: this.fechaInicio,
            end_date: this.fechaFin
          }
        });
        this.frentes = response.data.unidades || [];
        this.frenteSeleccionado = '';
      } catch (error) {
        console.error('Error al cargar frentes:', error);
        this.frentes = [];
      } finally {
        this.cargandoFrentes = false;
      }
    },
    async obtenerDatos() {
      if (!this.fechaInicio || !this.fechaFin) {
        alert('Por favor, selecciona ambas fechas.');
        return;
      }

      this.cargando = true;
      this.datos = [];

      try {
        const params = {
          fecha_inicio: this.fechaInicio,
          fecha_fin: this.fechaFin
        };
        if (this.frenteSeleccionado) {
          params.cod_un = this.frenteSeleccionado;
        }

        const response = await api.get('/api/maquinas-frente-operador/', { params });
        this.datos = response.data.data || [];
      } catch (error) {
        console.error('Error al obtener datos:', error);
        alert('No se pudieron cargar los datos. Revisa la conexión.');
      } finally {
        this.cargando = false;
      }
    },
    exportarAExcel() {
      if (this.resultadosFiltrados.length === 0) return;

      const wsData = [
        ['Patente', 'Detalle Equipo', 'Frente', 'Operador', 'Última Fecha', 'Última Hr Fin'],
        ...this.resultadosFiltrados.map(item => [
          item.cod_equipo,
          item.detalle_equipo,
          item.frente || '',
          item.operador,
          item.ultima_fecha,
          item.ultima_hr_fin
        ])
      ];

      const ws = XLSX.utils.aoa_to_sheet(wsData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Control de Máquinas');
      const filename = `Control_Maquinas_${this.fechaInicio}_a_${this.fechaFin}.xlsx`;
      XLSX.writeFile(wb, filename);
    },
    limpiarFiltros() {
      // Resetear filtros
      this.frenteSeleccionado = '';
      this.busqueda = '';
      this.busquedaGlobal = '';
      // No resetear fechas ni localStorage
      // Si quieres resetear fechas, descomenta:
      // const { inicio, fin } = this.obtenerRangoDefault();
      // this.fechaInicio = inicio;
      // this.fechaFin = fin;
      // this.guardarFechas();
      // this.cargarFrentes();
    }
  }
};
</script>