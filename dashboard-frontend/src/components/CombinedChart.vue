<!-- src/components/CombinedChart.vue -->
<template>
  <div class="chart-container">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { Bar } from 'chart.js/auto'

const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    required: true
  }
})

const chartCanvas = ref(null)
let chartInstance = null

onMounted(() => {
  if (chartCanvas.value) {
    chartInstance = new Bar(chartCanvas.value, {
      data: props.chartData,
      options: props.options
    })
  }
})

watch([() => props.chartData, () => props.options], ([newChartData, newOptions]) => {
  if (chartInstance) {
    chartInstance.data = newChartData
    chartInstance.options = newOptions
    chartInstance.update()
  }
})
</script>

<style scoped>
.chart-container {
  max-height: 400px;
  overflow-y: auto;
}
</style>