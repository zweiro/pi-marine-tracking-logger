<script setup lang="ts">
import type { Turtle } from '@/types'

const props = defineProps<{
  turtle: Turtle
}>()

const speciesLabels: Record<string, string> = {
  green: 'Green turtle',
  loggerhead: 'Loggerhead',
  leatherback: 'Leatherback',
  hawksbill: 'Hawksbill',
  olive_ridley: 'Olive ridley',
  kemps_ridley: "Kemp's ridley",
  flatback: 'Flatback'
}

const statusColors: Record<string, string> = {
  active: '#10b981',
  inactive: '#f59e0b',
  lost: '#ef4444'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}
</script>

<template>
  <div class="turtle-card">
    <div class="turtle-header">
      <div class="turtle-avatar">
        <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
        </svg>
      </div>
      <div class="turtle-info">
        <h3 class="turtle-name">{{ turtle.name || turtle.turtle_id }}</h3>
        <span class="turtle-id">{{ turtle.turtle_id }}</span>
      </div>
      <span
        class="turtle-status"
        :style="{ backgroundColor: statusColors[turtle.status] }"
      >
        {{ turtle.status }}
      </span>
    </div>

    <div class="turtle-details">
      <div class="detail-row">
        <span class="detail-label">Species</span>
        <span class="detail-value">{{ speciesLabels[turtle.species] || turtle.species }}</span>
      </div>
      <div class="detail-row" v-if="turtle.sensor_id">
        <span class="detail-label">Sensor</span>
        <span class="detail-value">{{ turtle.sensor_id }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Added</span>
        <span class="detail-value">{{ formatDate(turtle.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.turtle-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  transition: box-shadow var(--transition-fast), transform var(--transition-fast);
}

.turtle-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.turtle-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.turtle-avatar {
  width: 44px;
  height: 44px;
  background: var(--color-primary-light);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.turtle-info {
  flex: 1;
  min-width: 0;
}

.turtle-name {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.turtle-id {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-family: monospace;
}

.turtle-status {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: white;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  text-transform: capitalize;
}

.turtle-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.detail-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: 500;
}
</style>
