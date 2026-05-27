<script setup lang="ts">
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import type { Dive } from '@/types'

const props = defineProps<{
  dives: Dive[]
}>()

const recentDives = computed(() => props.dives.slice(0, 10))

// Map turtle IDs to short names
const turtleNames: Record<string, string> = {
  'HONU-001': 'Honu',
  'CARI-002': 'Caribe',
  'MEDI-003': 'Medi',
  'GALA-004': 'Darwin',
  'AUST-005': 'Coral',
}

const getDiveLabel = (d: Dive) => {
  const name = turtleNames[d.turtle_id] || d.turtle_id.split('-')[0]
  return `${name} #${d.dive_id}`
}

// Chart 1: Donut - Dives per turtle
const donutOptions = computed(() => ({
  chart: { type: 'donut', fontFamily: 'inherit' },
  labels: [...new Set(props.dives.map(d => d.turtle_id))],
  colors: ['#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'],
  legend: { position: 'bottom', fontSize: '12px' },
  dataLabels: { enabled: true },
  plotOptions: {
    pie: {
      donut: {
        size: '60%',
        labels: {
          show: true,
          total: { show: true, label: 'Total', fontSize: '14px' }
        }
      }
    }
  }
}))

const donutSeries = computed(() => {
  const turtleIds = [...new Set(props.dives.map(d => d.turtle_id))]
  return turtleIds.map(id => props.dives.filter(d => d.turtle_id === id).length)
})

// Chart 2: Range Bar - Temperature min/max per dive
const tempRangeOptions = computed(() => ({
  chart: { type: 'rangeBar', toolbar: { show: false }, fontFamily: 'inherit' },
  colors: ['#f97316'],
  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 4,
      barHeight: '60%'
    }
  },
  xaxis: {
    title: { text: 'Temperature (°C)' },
    labels: { formatter: (val: number) => `${val.toFixed(1)}°C` }
  },
  yaxis: {
    labels: { style: { fontSize: '11px' } }
  },
  dataLabels: { enabled: false },
  tooltip: {
    y: {
      formatter: (_: number, { seriesIndex, dataPointIndex, w }: any) => {
        const data = w.config.series[seriesIndex].data[dataPointIndex]
        return `${data.y[0].toFixed(1)}°C - ${data.y[1].toFixed(1)}°C`
      }
    }
  }
}))

const tempRangeSeries = computed(() => [{
  name: 'Temperature',
  data: recentDives.value
    .filter(d => d.stats?.min_temperature_c != null && d.stats?.max_temperature_c != null)
    .map(d => ({
      x: getDiveLabel(d),
      y: [d.stats!.min_temperature_c!, d.stats!.max_temperature_c!]
    }))
}])

// Chart 3: Bar - Sample count per dive
const sampleCountOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'inherit' },
  colors: ['#8b5cf6'],
  plotOptions: {
    bar: { borderRadius: 4, columnWidth: '60%' }
  },
  xaxis: {
    categories: recentDives.value.map(d => getDiveLabel(d)),
    labels: { style: { fontSize: '11px' } }
  },
  yaxis: {
    title: { text: 'Samples' }
  },
  dataLabels: { enabled: false }
}))

const sampleCountSeries = computed(() => [{
  name: 'Samples',
  data: recentDives.value.map(d => d.stats?.sample_count || 0)
}])

// Chart 4: Bar - Max depth per dive
const depthOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'inherit' },
  colors: ['#0ea5e9'],
  plotOptions: {
    bar: { borderRadius: 4, columnWidth: '60%' }
  },
  xaxis: {
    categories: recentDives.value.map(d => getDiveLabel(d)),
    labels: { style: { fontSize: '11px' } }
  },
  yaxis: {
    title: { text: 'Depth (m)' },
    reversed: true
  },
  dataLabels: { enabled: false }
}))

const depthSeries = computed(() => [{
  name: 'Max Depth',
  data: recentDives.value.map(d => d.stats?.max_depth_m || 0)
}])

const hasData = computed(() => props.dives.length > 0)
const hasTempRange = computed(() => tempRangeSeries.value[0].data.length > 0)
const hasSampleCount = computed(() => sampleCountSeries.value[0].data.some(v => v > 0))
const hasDepth = computed(() => depthSeries.value[0].data.some(v => v > 0))
</script>

<template>
  <div class="charts-section" v-if="hasData">
    <h2 class="section-title">Dive Analytics</h2>
    <div class="charts-container">
      <!-- Donut: Dives per turtle -->
      <div class="chart-card">
        <h3>Dives by Turtle</h3>
        <VueApexCharts
          type="donut"
          height="280"
          :options="donutOptions"
          :series="donutSeries"
        />
      </div>

      <!-- Range Bar: Temperature min/max -->
      <div class="chart-card" v-if="hasTempRange">
        <h3>Temperature Range</h3>
        <VueApexCharts
          type="rangeBar"
          height="280"
          :options="tempRangeOptions"
          :series="tempRangeSeries"
        />
      </div>

      <!-- Bar: Sample count per dive -->
      <div class="chart-card" v-if="hasSampleCount">
        <h3>Samples per Dive</h3>
        <VueApexCharts
          type="bar"
          height="280"
          :options="sampleCountOptions"
          :series="sampleCountSeries"
        />
      </div>

      <!-- Bar: Max depth per dive -->
      <div class="chart-card" v-if="hasDepth">
        <h3>Max Depth</h3>
        <VueApexCharts
          type="bar"
          height="280"
          :options="depthOptions"
          :series="depthSeries"
        />
      </div>

    </div>
  </div>
</template>

<style scoped>
.charts-section {
  margin-top: var(--spacing-2xl);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-primary);
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.chart-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.chart-card h3 {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}
</style>
