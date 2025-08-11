<!-- src/components/PieChart.vue -->
<template>
  <div class="chart-container">
    <Pie :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { Pie } from 'vue-chartjs'

// Importar y registrar componentes de Chart.js
import {
  Chart,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  CategoryScale
} from 'chart.js'

Chart.register(Title, Tooltip, Legend, ArcElement, CategoryScale)

defineProps({
  chartData: {
    type: Object,
    required: true
  },
  chartOptions: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.chart-container {
  height: 400px;
  position: relative;
}
</style>