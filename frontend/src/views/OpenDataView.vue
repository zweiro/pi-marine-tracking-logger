<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTurtlesStore } from '@/stores/turtles'
import { useDivesStore } from '@/stores/dives'
import { exportApi } from '@/services/api'

const turtlesStore = useTurtlesStore()
const divesStore = useDivesStore()

const exporting = ref(false)
const exportError = ref<string | null>(null)

onMounted(() => {
  turtlesStore.fetchTurtles()
  divesStore.fetchAllDives()
})

async function downloadDarwinCore() {
  exporting.value = true
  exportError.value = null

  try {
    const blob = await exportApi.downloadDarwinCoreZip({
      dataset_name: 'OceanPulse Sea Turtle Tracking',
      institution_code: 'HES-SO and University of Bern/BFH master',
      include_samples: false
    })

    // Download the blob
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dwca_turtle_tracking_${new Date().toISOString().slice(0, 10)}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    exportError.value = e instanceof Error ? e.message : 'Export failed'
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="open-data-page">
    <header class="page-header">
      <h1 class="page-title">Open Data</h1>
      <p class="page-subtitle">Access and download sea turtle tracking data for scientific research</p>
    </header>

    <!-- Stats -->
    <section class="stats-section">
      <div class="stat-card">
        <span class="stat-value">{{ turtlesStore.turtleCount }}</span>
        <span class="stat-label">Turtles tracked</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ divesStore.diveCount }}</span>
        <span class="stat-label">Dives recorded</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">{{ turtlesStore.activeTurtles.length }}</span>
        <span class="stat-label">Currently active</span>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Data Access</h2>
      <p class="section-content">
        Our data is made available under open data principles to support marine biology
        research and conservation efforts. Data can be exported in Darwin Core Archive
        format compatible with EMODnet Biology and EurOBIS.
      </p>
    </section>

    <section class="section">
      <h2 class="section-title">Download Data</h2>

      <!-- Error message -->
      <div v-if="exportError" class="error-message">
        {{ exportError }}
      </div>

      <div class="export-cards">
        <div class="export-card">
          <div class="export-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="32" height="32">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="export-info">
            <h3>Darwin Core Archive</h3>
            <p>Standard format for biodiversity data (ZIP with CSV + metadata)</p>
            <p class="export-detail">Includes: Event Core, Occurrence Extension, eMoF Extension</p>
          </div>
          <button
            class="export-button"
            :disabled="exporting || divesStore.diveCount === 0"
            @click="downloadDarwinCore"
          >
            <span v-if="exporting" class="loading-spinner"></span>
            {{ exporting ? 'Exporting...' : 'Download ZIP' }}
          </button>
        </div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">Data Standards</h2>
      <div class="standards-list">
        <div class="standard-item">
          <strong>Darwin Core</strong>
          <span>Biodiversity data standard</span>
        </div>
        <div class="standard-item">
          <strong>WoRMS</strong>
          <span>World Register of Marine Species (taxonomic IDs)</span>
        </div>
        <div class="standard-item">
          <strong>NERC Vocabulary</strong>
          <span>Standardized measurement types and units</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.open-data-page {
  max-width: 900px;
}

.page-header {
  margin-bottom: var(--spacing-2xl);
}

.page-title {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.page-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
}

.stats-section {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
  flex-wrap: wrap;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg) var(--spacing-xl);
  text-align: center;
  flex: 1;
  min-width: 140px;
}

.stat-card .stat-value {
  display: block;
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--color-primary);
}

.stat-card .stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.section {
  margin-bottom: var(--spacing-2xl);
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.section-content {
  font-size: var(--font-size-base);
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.error-message {
  background: #fef2f2;
  color: #991b1b;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
}

.export-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.export-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.export-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.export-info {
  flex: 1;
}

.export-info h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.export-info p {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
}

.export-detail {
  margin-top: var(--spacing-xs) !important;
  font-size: var(--font-size-xs) !important;
}

.export-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-xl);
  background: var(--color-primary);
  color: white;
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
  white-space: nowrap;
}

.export-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.export-button:disabled {
  background: var(--color-border);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.standards-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.standard-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-surface-variant);
  border-radius: var(--radius-md);
}

.standard-item strong {
  min-width: 150px;
  color: var(--color-text-primary);
}

.standard-item span {
  color: var(--color-text-secondary);
}

.link {
  color: var(--color-primary);
  text-decoration: underline;
}

.link:hover {
  color: var(--color-primary-dark);
}
</style>
