import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Turtle, PaginatedResponse } from '@/types'
import { api } from '@/services/api'

export const useTurtlesStore = defineStore('turtles', () => {
  const turtles = ref<Turtle[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeTurtles = computed(() =>
    turtles.value.filter(t => t.status === 'active')
  )

  const turtleCount = computed(() => turtles.value.length)

  async function fetchTurtles() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<PaginatedResponse<Turtle>>('/turtles')
      turtles.value = response.items
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch turtles'
    } finally {
      loading.value = false
    }
  }

  function getTurtleById(id: string) {
    return turtles.value.find(t => t.turtle_id === id)
  }

  return {
    turtles,
    loading,
    error,
    activeTurtles,
    turtleCount,
    fetchTurtles,
    getTurtleById
  }
})
