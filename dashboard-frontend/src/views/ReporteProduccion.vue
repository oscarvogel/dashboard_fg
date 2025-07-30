<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
    <div class="max-w-7xl mx-auto">
      <!-- Título -->
      <h1 class="text-3xl font-extrabold text-gray-900 mb-8 text-center">Reporte de Producción</h1>

      <!-- Filtros -->
      <div class="bg-white shadow-lg rounded-xl p-6 mb-8 transition-all duration-300">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Fecha Inicio -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Fecha Inicio</label>
            <input
              v-model="startDate"
              type="date"
              class="w-full border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- Fecha Fin -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Fecha Fin</label>
            <input
              v-model="endDate"
              type="date"
              class="w-full border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <!-- UN -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">UN</label>
            <select
              v-model="selectedUN"
              @change="loadEquipos"
              class="w-full border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Seleccionar UN --</option>
              <option v-for="un in unidades" :key="un" :value="un">{{ un }}</option>
            </select>
          </div>

          <!-- Equipo -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Equipo</label>
            <select
              v-model="selectedEquipo"
              @change="loadCampos"
              class="w-full border-gray-300 rounded-lg shadow-sm focus:ring-green-500 focus:border-green-500"
            >
              <option value="">-- Seleccionar Equipo --</option>
              <option v-for="eq in equipos" :key="eq" :value="eq">{{ eq }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Selección de campos -->
      <div
        v-if="campos.length > 0"
        class="bg-white shadow-lg rounded-xl p-6 mb-8 transition-all duration-300"
      >
        <h3 class="text-lg font-semibold text-gray-800 mb-4">Campos a mostrar</h3>
        <div class="flex flex-wrap gap-4">
          <div
            v-for="campo in campos"
            :key="campo.value"
            class="flex items-center"
          >
            <input
              :id="'campo-' + campo.value"
              :value="campo.value"
              v-model="selectedCampos"
              type="checkbox"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label :for="'campo-' + campo.value" class="ml-2 text-sm text-gray-700">
              {{ campo.label }}
            </label>
          </div>
        </div>
      </div>

      <!-- Tabla -->
      <div v-if="tabla.length > 0" class="bg-white shadow-lg rounded-xl overflow-hidden">
        <!-- Botón de exportación -->
        <div class="p-6 pb-4 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-800">Datos de Producción</h3>
          <button
            @click="exportarExcel"
            class="flex items-center space-x-1 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200 shadow-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 7H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Exportar a Excel</span>
          </button>
        </div>

        <!-- Tabla -->
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th
                  class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  Día
                </th>
                <th
                  v-for="campo in selectedCamposDisplay"
                  :key="campo.value"
                  class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {{ campo.label }}
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="fila in tabla"
                :key="fila.fecha"
                class="hover:bg-gray-50 transition duration-150"
              >
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatDate(fila.fecha) }}
                </td>
                <td
                  v-for="campo in selectedCamposDisplay"
                  :key="campo.value"
                  class="px-6 py-4 whitespace-nowrap text-sm text-gray-700"
                >
                  {{ fila[campo.value] || '–' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Sin datos -->
      <div
        v-else-if="loaded && tabla.length === 0"
        class="text-center py-10"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-500">No hay datos disponibles</h3>
        <p class="mt-1 text-sm text-gray-500">Intenta ajustar los filtros para ver resultados.</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api';
import * as XLSX from 'xlsx';
const CAMPOS_STORAGE_KEY = 'produccion_selectedCampos';

export default {
  name: 'ReporteProduccion',
  data() {
    const storedCampos = localStorage.getItem(CAMPOS_STORAGE_KEY);
    let selectedCampos = [];

    // Si hay campos guardados y son válidos, usarlos
    if (storedCampos) {
        try {
        const parsed = JSON.parse(storedCampos);
        // Validar que estén en los campos disponibles
        const validValues = [
            'operacion', 'operador', 'equipo', 'hr_inicio', 'hr_fin', 'm3',
            'tn_despachadas', 'produccion', 'unidad_produccion', 'hrs_no_op',
            'plantas', 'combustible', 'aceite_cadena', 'predio', 'stock_abc', 'acta'
        ];
        selectedCampos = parsed.filter(campo => validValues.includes(campo));
        } catch (e) {
        selectedCampos = []; // Si hay error, usar vacío
        }
    }

    // Si no hay ninguno guardado, usar un conjunto por defecto (opcional)
    if (selectedCampos.length === 0) {
        selectedCampos = ['operacion', 'equipo', 'hr_inicio', 'hr_fin', 'combustible']; // ejemplo
    }
    return {
      startDate: '',
      endDate: '',
      selectedUN: '',
      selectedEquipo: '',
      unidades: [],
      equipos: [],
      selectedCampos, // ←inicia con los guardados
      tabla: [],
      tablaOriginal: [],
      loaded: false,
      loading: false,

      // Campos disponibles para mostrar
      campos: [
        { value: 'operacion', label: 'Operación' },
        { value: 'operador', label: 'Operador' },
        { value: 'equipo', label: 'Equipo' },
        { value: 'hr_inicio', label: 'Hora Inicio' },
        { value: 'hr_fin', label: 'Hora Fin' },
        { value: 'm3', label: 'm³' },
        { value: 'tn_despachadas', label: 'TN Despachadas' },
        { value: 'produccion', label: 'Producción' },
        { value: 'unidad_produccion', label: 'Unidad Producción' },
        { value: 'hrs_no_op', label: 'Hrs No Operativas' },
        { value: 'plantas', label: 'Plantas' },
        { value: 'combustible', label: 'Combustible (L)' },
        { value: 'aceite_cadena', label: 'Aceite Cadena (L)' },
        { value: 'predio', label: 'Predio' },
        { value: 'stock_abc', label: 'Stock ABC' },
        { value: 'acta', label: 'Acta' },
      ],
    };
  },

  computed: {
    selectedCamposDisplay() {
      return this.campos.filter((c) => this.selectedCampos.includes(c.value));
    },
  },

  methods: {
    // Cargar UN y equipos disponibles según fechas y UN
    async loadFiltros() {
      if (!this.startDate || !this.endDate) {
        this.resetFilters();
        return;
      }

      this.loading = true;
      try {
        const params = new URLSearchParams({
          start_date: this.startDate,
          end_date: this.endDate,
        });
        if (this.selectedUN) params.append('un', this.selectedUN);

        const res = await api.get('/api/filtros/', { params });
        const data = res.data;

        this.unidades = data.unidades || [];
        this.equipos = data.equipos || [];

        // Limpiar selecciones si ya no son válidas
        if (this.selectedUN && !this.unidades.includes(this.selectedUN)) {
          this.selectedUN = '';
          this.equipos = [];
          this.selectedEquipo = '';
        }
        if (this.selectedEquipo && !this.equipos.includes(this.selectedEquipo)) {
          this.selectedEquipo = '';
        }
      } catch (error) {
        console.error('Error al cargar filtros:', error);
        this.unidades = [];
        this.equipos = [];
      } finally {
        this.loading = false;
      }
    },

    // Cargar datos de producción al seleccionar equipo
    async loadCampos() {
      if (!this.selectedEquipo || !this.startDate || !this.endDate) {
        this.tabla = [];
        this.tablaOriginal = [];
        this.loaded = false;
        return;
      }

      this.loading = true;
      try {
        const params = new URLSearchParams({
          start_date: this.startDate,
          end_date: this.endDate,
          un: this.selectedUN,
          detalle_equipo: this.selectedEquipo,
        });

        const res = await api.get('/api/produccion-dashboard/', { params });
        const registros = res.data.results || [];

        this.tablaOriginal = registros;
        this.rebuildTabla();
        this.loaded = true;
      } catch (error) {
        console.error('Error al cargar datos de producción:', error);
        this.tabla = [];
        this.tablaOriginal = [];
        this.loaded = false;
      } finally {
        this.loading = false;
      }
    },

    // Reconstruir tabla con los campos actualmente seleccionados
    rebuildTabla() {
      if (!this.tablaOriginal.length) {
        this.tabla = [];
        return;
      }

      const agrupado = {};
      this.tablaOriginal.forEach((reg) => {
        const fecha = reg.fecha;
        if (!agrupado[fecha]) {
          agrupado[fecha] = { fecha };
        }
        this.selectedCampos.forEach((campo) => {
          agrupado[fecha][campo] = reg[campo] ?? '–';
        });
      });

      this.tabla = Object.values(agrupado).sort((a, b) => a.fecha.localeCompare(b.fecha));
    },

    // Formatear fecha de YYYY-MM-DD a DD/MM/YYYY
    formatDate(dateStr) {
      if (!dateStr) return '';
      const [year, month, day] = dateStr.split('-');
      return `${day}/${month}/${year}`;
    },

    // Exportar a Excel
    exportarExcel() {
      const headers = ['Día', ...this.selectedCamposDisplay.map((c) => c.label)];
      const data = [
        headers,
        ...this.tabla.map((fila) => [
          this.formatDate(fila.fecha),
          ...this.selectedCampos.map((campo) => fila[campo] || ''),
        ]),
      ];

      const ws = XLSX.utils.aoa_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Reporte Producción');
      XLSX.writeFile(wb, `Reporte_Produccion_${this.startDate}_a_${this.endDate}.xlsx`);
    },

    // Resetear filtros y tablas
    resetFilters() {
      this.unidades = [];
      this.equipos = [];
      this.selectedUN = '';
      this.selectedEquipo = '';
      this.tabla = [];
      this.tablaOriginal = [];
      this.loaded = false;
    },
  },

  watch: {
    startDate() {
      if (this.startDate && this.endDate) {
        this.loadFiltros();
      } else {
        this.resetFilters();
      }
    },
    endDate() {
      if (this.startDate && this.endDate) {
        this.loadFiltros();
      } else {
        this.resetFilters();
      }
    },
    selectedUN() {
      if (this.startDate && this.endDate) {
        this.loadFiltros();
      }
    },
    // Reconstruir tabla cuando se cambien los campos seleccionados
    selectedCampos: {
      handler() {
        if (this.tablaOriginal.length > 0) {
          this.rebuildTabla();
        }
      },
      deep: true,
    },
    selectedCampos: {
        handler() {
        // Guardar en localStorage cada vez que cambia
        try {
            localStorage.setItem(CAMPOS_STORAGE_KEY, JSON.stringify(this.selectedCampos));
        } catch (e) {
            console.warn('No se pudo guardar en localStorage', e);
        }

        // Reconstruir tabla si hay datos
        if (this.tablaOriginal.length > 0) {
            this.rebuildTabla();
        }
        },
        deep: true
    }    
  },

  mounted() {
    // Si ya hay fechas predefinidas, cargar filtros
    if (this.startDate && this.endDate) {
      this.loadFiltros();
    }
  },
};
</script>