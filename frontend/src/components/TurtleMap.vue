<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Turtle, Dive } from '@/types'

const props = defineProps<{
  turtles: Turtle[]
  dives?: Dive[]
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markersLayer: L.FeatureGroup | null = null

// Custom turtle icon
const turtleIcon = L.divIcon({
  className: 'turtle-marker',
  html: `<div class="marker-dot"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10]
})

function initMap() {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value).setView([20, 0], 2)

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19
  }).addTo(map)

  markersLayer = L.featureGroup().addTo(map)
  updateMarkers()
}

function updateMarkers() {
  if (!markersLayer || !map) return

  markersLayer.clearLayers()

  // Add markers for dives (if available)
  if (props.dives && props.dives.length > 0) {
    props.dives.forEach(dive => {
      if (dive.start_location?.coordinates) {
        const [lng, lat] = dive.start_location.coordinates
        const marker = L.marker([lat, lng], { icon: turtleIcon })
        marker.bindPopup(`
          <strong>${dive.turtle_id}</strong><br>
          Dive #${dive.dive_number}<br>
          Max depth: ${dive.stats?.max_depth_m?.toFixed(1) || '?'}m
        `)
        markersLayer?.addLayer(marker)
      }
    })

    // Fit bounds to markers
    if (markersLayer.getLayers().length > 0) {
      const bounds = markersLayer.getBounds()
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 10 })
    }
  }
}

watch(() => props.dives, updateMarkers, { deep: true })

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  map?.remove()
})
</script>

<template>
  <div class="map-wrapper">
    <div ref="mapContainer" class="map-container"></div>
    <div v-if="!dives || dives.length === 0" class="map-overlay">
      <p>No location data available</p>
    </div>
  </div>
</template>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
  background: #e5e7eb;
}

.map-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-text-muted);
  font-style: italic;
}
</style>

<style>
/* Global styles for markers */
.turtle-marker {
  background: none;
  border: none;
}

.turtle-marker .marker-dot {
  width: 16px;
  height: 16px;
  background: var(--color-primary, #1976d2);
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.leaflet-popup-content-wrapper {
  border-radius: 8px;
}

.leaflet-popup-content {
  margin: 12px;
  font-size: 14px;
  line-height: 1.5;
}
</style>
