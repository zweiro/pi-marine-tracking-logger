/**
 * Navigation item type for sidebar
 */
export interface NavItem {
  name: string
  path: string
  icon?: string
}

/**
 * Turtle model
 */
export interface Turtle {
  turtle_id: string
  name?: string
  species: TurtleSpecies
  status: TurtleStatus
  sensor_id?: string
  created_at: string
  updated_at: string
}

export type TurtleSpecies =
  | 'green'
  | 'loggerhead'
  | 'leatherback'
  | 'hawksbill'
  | 'olive_ridley'
  | 'kemps_ridley'
  | 'flatback'

export type TurtleStatus = 'active' | 'inactive' | 'lost'

/**
 * Dive model
 */
export interface Dive {
  id: string
  turtle_id: string
  dive_id: number
  start_time: string
  start_location: GeoJSONPoint
  stats: DiveStats
  packet_metadata?: PacketMetadata
}

export interface GeoJSONPoint {
  type: 'Point'
  coordinates: [number, number] // [longitude, latitude]
}

export interface DiveStats {
  sample_count: number
  max_depth_m: number
  avg_depth_m?: number
  avg_temperature_c?: number
  min_temperature_c?: number
  max_temperature_c?: number
}

export interface PacketMetadata {
  gps_week: number
  gps_tow_s: number
  sample_period_ms: number
  received_at: string
}

/**
 * Sample model
 */
export interface Sample {
  _id: string
  timestamp: string
  metadata: SampleMetadata
  temperature_c: number
  pressure_hpa: number
  depth_m: number
  sample_index: number
}

export interface SampleMetadata {
  turtle_id: string
  dive_id: string
}

/**
 * API response types
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  version: string
  database: string
  scheduler?: {
    enabled: boolean
    running: boolean
  }
}
