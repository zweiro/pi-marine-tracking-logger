import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Dive, PaginatedResponse } from '@/types'
import { api } from '@/services/api'

export const useDivesStore = defineStore('dives', () => {
  const dives = ref<Dive[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const diveCount = computed(() => dives.value.length)

  const divesWithLocation = computed(() =>
    dives.value.filter(d => d.start_location?.coordinates)
  )

  async function fetchDives(turtleId?: string) {
    loading.value = true
    error.value = null
    try {
      const params = turtleId ? { turtle_id: turtleId } : undefined
      const response = await api.get<PaginatedResponse<Dive>>('/dives', { params })
      dives.value = response.items
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch dives'
    } finally {
      loading.value = false
    }
  }

  async function fetchAllDives() {
    return fetchDives()
  }

  return {
    dives,
    loading,
    error,
    diveCount,
    divesWithLocation,
    fetchDives,
    fetchAllDives
  }
})
