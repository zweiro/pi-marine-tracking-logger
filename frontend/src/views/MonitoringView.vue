<script setup lang="ts">
import { onMounted } from 'vue'
import { useTurtlesStore } from '@/stores/turtles'
import { useDivesStore } from '@/stores/dives'
import TurtleCard from '@/components/TurtleCard.vue'
import TurtleMap from '@/components/TurtleMap.vue'

const turtlesStore = useTurtlesStore()
const divesStore = useDivesStore()

onMounted(() => {
  turtlesStore.fetchTurtles()
  divesStore.fetchAllDives()
})
</script>

<template>
  <div class="monitoring-page">
    <header class="page-header">
      <div class="header-content">
        <h1 class="page-title">Monitoring</h1>
        <p class="page-subtitle">Track sea turtle movements and dive data</p>
      </div>
      <div class="header-stats" v-if="!turtlesStore.loading">
        <div class="stat-badge">
          <span class="stat-value">{{ turtlesStore.turtleCount }}</span>
          <span class="stat-label">Turtles</span>
        </div>
        <div class="stat-badge stat-badge--active">
          <span class="stat-value">{{ turtlesStore.activeTurtles.length }}</span>
          <span class="stat-label">Active</span>
        </div>
        <div class="stat-badge stat-badge--dives">
          <span class="stat-value">{{ divesStore.diveCount }}</span>
          <span class="stat-label">Dives</span>
        </div>
      </div>
    </header>

    <!-- Map section -->
    <section class="map-section">
      <TurtleMap
        :turtles="turtlesStore.turtles"
        :dives="divesStore.divesWithLocation"
      />
    </section>

    <!-- Loading state -->
    <div v-if="turtlesStore.loading" class="loading-state">
      <div class="loader"></div>
      <p>Loading turtles...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="turtlesStore.error" class="error-state">
      <p>{{ turtlesStore.error }}</p>
      <button @click="turtlesStore.fetchTurtles()" class="retry-btn">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="turtlesStore.turtles.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="64" height="64">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          <path d="M8 12h8M12 8v8" stroke-linecap="round"/>
        </svg>
      </div>
      <h3>No turtles yet</h3>
      <p>Turtles will appear here once data is received from the satellite.</p>
    </div>

    <!-- Turtle grid -->
    <div v-else class="content-section">
      <h2 class="section-title">Tracked Turtles</h2>
      <div class="turtle-grid">
        <TurtleCard
          v-for="turtle in turtlesStore.turtles"
          :key="turtle.turtle_id"
          :turtle="turtle"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.monitoring-page {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-2xl);
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.page-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
}

.header-stats {
  display: flex;
  gap: var(--spacing-md);
}

.stat-badge {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  text-align: center;
  min-width: 80px;
}

.stat-badge--active {
  background: #ecfdf5;
  border-color: #a7f3d0;
}

.stat-badge--dives {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.stat-badge--dives .stat-value {
  color: #2563eb;
}

.stat-value {
  display: block;
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.stat-badge--active .stat-value {
  color: #059669;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.map-section {
  height: 350px;
  margin-bottom: var(--spacing-2xl);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.content-section {
  margin-top: var(--spacing-xl);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  color: var(--color-text-primary);
}

.turtle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

/* Loading state */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-md);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error state */
.error-state {
  text-align: center;
  padding: var(--spacing-2xl);
  background: #fef2f2;
  border-radius: var(--radius-lg);
  color: #991b1b;
}

.retry-btn {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: #ef4444;
  color: white;
  border-radius: var(--radius-md);
  font-weight: 500;
}

.retry-btn:hover {
  background: #dc2626;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: var(--spacing-2xl);
  color: var(--color-text-muted);
}

.empty-icon {
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

.empty-state h3 {
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}
</style>
