<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type { NavItem } from '@/types'
import logoImg from '@/assets/logo.png'

const route = useRoute()

const navItems: NavItem[] = [
  { name: 'About', path: '/about' },
  { name: 'Monitoring', path: '/monitoring' },
  { name: 'Open Data', path: '/open-data' }
]

const isActive = (path: string) => computed(() => route.path === path)
</script>

<template>
  <aside class="sidebar">
    <!-- Logo Section -->
    <div class="sidebar-header">
      <div class="logo">
        <img :src="logoImg" alt="OceanPulse" class="logo-icon" />
        <div class="logo-text">
          <span class="logo-title">OceanPulse</span>
          <span class="logo-subtitle">PI MONIT</span>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <ul class="nav-list">
        <li v-for="item in navItems" :key="item.path" class="nav-item">
          <RouterLink
            :to="item.path"
            class="nav-link"
            :class="{ 'nav-link--active': isActive(item.path).value }"
          >
            {{ item.name }}
          </RouterLink>
        </li>
      </ul>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <span class="version">v0.1.0</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.sidebar-header {
  padding: var(--spacing-xl);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.logo-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: white;
  line-height: 1.2;
}

.logo-subtitle {
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.7);
  font-weight: 400;
}

.sidebar-nav {
  flex: 1;
  padding: var(--spacing-lg) 0;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.nav-item {
  padding: 0 var(--spacing-md);
}

.nav-link {
  display: block;
  padding: var(--spacing-md) var(--spacing-lg);
  color: rgba(255, 255, 255, 0.85);
  font-size: var(--font-size-base);
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link--active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  font-weight: 600;
}

.sidebar-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.version {
  font-size: var(--font-size-xs);
  color: rgba(255, 255, 255, 0.5);
}
</style>
