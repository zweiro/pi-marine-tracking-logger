/**
 * API Service
 *
 * Centralized HTTP client for backend communication.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>
}

class ApiService {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value))
        }
      })
    }

    return url.toString()
  }

  async get<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(endpoint, params)

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      },
      ...fetchOptions
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async post<T>(endpoint: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(endpoint, params)

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      },
      body: data ? JSON.stringify(data) : undefined,
      ...fetchOptions
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async put<T>(endpoint: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(endpoint, params)

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      },
      body: data ? JSON.stringify(data) : undefined,
      ...fetchOptions
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async delete<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options
    const url = this.buildUrl(endpoint, params)

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      },
      ...fetchOptions
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  async downloadBlob(endpoint: string, data?: unknown): Promise<Blob> {
    const url = this.buildUrl(endpoint)

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: data ? JSON.stringify(data) : undefined
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return response.blob()
  }
}

export const api = new ApiService(API_BASE)

// Typed API methods for specific resources
export const turtlesApi = {
  getAll: (params?: { species?: string; status?: string }) =>
    api.get('/turtles', { params }),

  getById: (turtleId: string) =>
    api.get(`/turtles/${turtleId}`)
}

export const divesApi = {
  getAll: (params?: { turtle_id?: string }) =>
    api.get('/dives', { params }),

  getById: (id: string) =>
    api.get(`/dives/${id}`)
}

export const samplesApi = {
  getByDive: (diveId: string) =>
    api.get(`/samples/dive/${diveId}`),

  getStats: (diveId: string) =>
    api.get(`/samples/dive/${diveId}/stats`)
}

export const exportApi = {
  getDarwinCoreJson: (request: unknown) =>
    api.post('/export/darwin-core', request),

  downloadDarwinCoreZip: (request: unknown) =>
    api.downloadBlob('/export/darwin-core/zip', request),

  getVocabularies: () =>
    api.get('/export/darwin-core/vocabularies')
}
