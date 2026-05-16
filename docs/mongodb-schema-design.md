# MongoDB Schema Design - Turtle Biologging System

## Architecture Overview

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────────┐
│   turtles   │ 1───N │    dives    │ 1───N │      samples        │
│ (standard)  │       │ (standard)  │       │ (time-series coll.) │
└─────────────┘       └─────────────┘       └─────────────────────┘
```

**Design Philosophy**: Hybrid architecture separating metadata from high-volume time-series data for optimal query performance and scalability.

---

## Collection Schemas

### 1. `turtles` Collection (Standard)

```javascript
{
  _id: ObjectId("..."),
  turtle_id: "TRT-2024-001",        // Unique business identifier
  name: "Marina",
  species: "green",                  // enum: green, loggerhead, leatherback, etc.
  sensor_id: "SAT-2024-001",        // Satellite tag ID
  tag_date: ISODate("2024-03-15T10:30:00Z"),
  status: "active",                  // enum: active, inactive, lost

  // Denormalized stats (updated periodically)
  stats: {
    total_dives: 156,
    last_dive_at: ISODate("2024-06-15T14:30:00Z"),
    max_depth_m: 127.5,
    total_dive_duration_s: 892340
  },

  created_at: ISODate("2024-03-15T10:30:00Z"),
  updated_at: ISODate("2024-06-15T14:35:00Z")
}
```

### 2. `dives` Collection (Standard)

```javascript
{
  _id: ObjectId("..."),
  dive_id: 1,                        // From satellite packet
  turtle_id: "TRT-2024-001",         // Reference to turtle

  // Timing
  start_time: ISODate("2024-06-15T14:30:00Z"),
  end_time: ISODate("2024-06-15T14:40:00Z"),
  duration_s: 600,

  // Location (GPS at surface before/after dive)
  start_location: {
    type: "Point",
    coordinates: [6.1432, 46.2044]   // [longitude, latitude] GeoJSON
  },
  end_location: {
    type: "Point",
    coordinates: [6.1435, 46.2046]
  },

  // Computed statistics from samples
  stats: {
    sample_count: 600,
    sample_period_ms: 1000,
    max_depth_m: 45.2,
    avg_depth_m: 28.7,
    min_temperature_c: 18.5,
    max_temperature_c: 22.3,
    avg_temperature_c: 20.1
  },

  // Raw packet metadata (for debugging/reprocessing)
  packet_metadata: {
    gps_week: 2300,
    gps_tow_s: 250000,
    header_len: 21
  },

  created_at: ISODate("2024-06-15T14:45:00Z")
}
```

### 3. `samples` Collection (Time Series)

```javascript
// MongoDB Time Series Collection configuration
db.createCollection("samples", {
  timeseries: {
    timeField: "timestamp",
    metaField: "metadata",
    granularity: "seconds"
  },
  expireAfterSeconds: 94608000  // Optional: 3 years retention
})

// Document structure
{
  timestamp: ISODate("2024-06-15T14:30:05Z"),

  metadata: {
    dive_id: ObjectId("..."),        // Reference to dive
    turtle_id: "TRT-2024-001"        // Denormalized for efficient queries
  },

  // Measurements
  sample_index: 5,                   // Position in dive sequence
  depth_m: 12.5,
  temperature_c: 21.3,
  pressure_hpa: 2263                 // Raw sensor value
}
```

---

## Recommended Indexes

### `turtles` Collection

```javascript
// Unique business identifier
db.turtles.createIndex({ "turtle_id": 1 }, { unique: true })

// Status filtering (active turtles)
db.turtles.createIndex({ "status": 1 })

// Species-based queries
db.turtles.createIndex({ "species": 1, "status": 1 })
```

### `dives` Collection

```javascript
// Primary query pattern: dives by turtle, ordered by time
db.dives.createIndex({ "turtle_id": 1, "start_time": -1 })

// Time-range queries across all turtles
db.dives.createIndex({ "start_time": -1 })

// Geospatial queries (find dives near location)
db.dives.createIndex({ "start_location": "2dsphere" })

// Filter by depth statistics
db.dives.createIndex({ "turtle_id": 1, "stats.max_depth_m": -1 })
```

### `samples` Collection (Time Series)

```javascript
// Time series collections auto-create indexes on timeField + metaField
// Additional compound index for dive-specific queries
db.samples.createIndex({ "metadata.dive_id": 1, "timestamp": 1 })

// Turtle-level time series queries
db.samples.createIndex({ "metadata.turtle_id": 1, "timestamp": -1 })
```

---

## Example Queries

### 1. Retrieve all dives for one turtle

```javascript
// Basic query with pagination
db.dives.find({
  turtle_id: "TRT-2024-001"
})
.sort({ start_time: -1 })
.limit(20)

// With date range filter
db.dives.find({
  turtle_id: "TRT-2024-001",
  start_time: {
    $gte: ISODate("2024-06-01T00:00:00Z"),
    $lt: ISODate("2024-07-01T00:00:00Z")
  }
})
.sort({ start_time: -1 })
```

### 2. Retrieve all samples for one dive

```javascript
// Get samples ordered by time
db.samples.find({
  "metadata.dive_id": ObjectId("...")
})
.sort({ timestamp: 1 })

// Project only essential fields
db.samples.find(
  { "metadata.dive_id": ObjectId("...") },
  {
    timestamp: 1,
    depth_m: 1,
    temperature_c: 1,
    sample_index: 1,
    _id: 0
  }
).sort({ sample_index: 1 })
```

### 3. Compute average depth across samples

```javascript
// Average depth for a specific dive
db.samples.aggregate([
  { $match: { "metadata.dive_id": ObjectId("...") } },
  { $group: {
      _id: null,
      avg_depth: { $avg: "$depth_m" },
      max_depth: { $max: "$depth_m" },
      min_depth: { $min: "$depth_m" },
      sample_count: { $sum: 1 }
  }}
])

// Average depth per dive for a turtle (last 30 days)
db.samples.aggregate([
  { $match: {
      "metadata.turtle_id": "TRT-2024-001",
      timestamp: { $gte: ISODate("2024-05-25T00:00:00Z") }
  }},
  { $group: {
      _id: "$metadata.dive_id",
      avg_depth: { $avg: "$depth_m" },
      max_depth: { $max: "$depth_m" },
      dive_start: { $min: "$timestamp" }
  }},
  { $sort: { dive_start: -1 } }
])

// Daily average depth for a turtle (time-series bucketing)
db.samples.aggregate([
  { $match: { "metadata.turtle_id": "TRT-2024-001" } },
  { $group: {
      _id: {
        $dateTrunc: { date: "$timestamp", unit: "day" }
      },
      avg_depth: { $avg: "$depth_m" },
      avg_temp: { $avg: "$temperature_c" },
      sample_count: { $sum: 1 }
  }},
  { $sort: { _id: -1 } }
])
```

### 4. Additional useful queries

```javascript
// Find deepest dives for a turtle
db.dives.find({ turtle_id: "TRT-2024-001" })
  .sort({ "stats.max_depth_m": -1 })
  .limit(10)

// Find dives within geographic area
db.dives.find({
  start_location: {
    $near: {
      $geometry: { type: "Point", coordinates: [6.14, 46.20] },
      $maxDistance: 10000  // 10km radius
    }
  }
})

// Get dive with its samples (application-level join)
const dive = db.dives.findOne({ _id: ObjectId("...") })
const samples = db.samples.find({
  "metadata.dive_id": dive._id
}).toArray()
```

---

## Advantages / Inconvenients

| Aspect | Avantages | Inconvénients |
|--------|-----------|---------------|
| **Scalabilité** | ✅ Samples en time-series = compression native, meilleure perf sur gros volumes | ⚠️ Nécessite MongoDB 5.0+ pour time-series |
| **Performance lecture** | ✅ Statistiques pré-calculées dans `dives` évitent les aggregations coûteuses | ⚠️ Stats dénormalisées doivent être recalculées à l'insertion |
| **Requêtes analytiques** | ✅ Time-series optimisé pour bucketing, window functions | ⚠️ Pas de jointures natives, nécessite `$lookup` ou requêtes multiples |
| **Flexibilité** | ✅ Collections séparées = schémas indépendants, migrations faciles | ⚠️ Cohérence référentielle non garantie (pas de FK) |
| **Stockage** | ✅ Compression time-series ~10x sur données répétitives | ⚠️ `turtle_id` dénormalisé dans samples = duplication |
| **Ingestion** | ✅ Inserts bulk rapides dans samples | ⚠️ Pipeline nécessaire: décoder packet → insérer samples → calculer stats → insérer dive |
| **Rétention** | ✅ TTL natif sur time-series pour archivage automatique | ⚠️ Supprimer un dive ne supprime pas ses samples automatiquement |

---

## Data Flow (Ingestion Pipeline)

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Satellite    │────▶│ Decode Packet   │────▶│ Compute Stats    │
│ Packet (hex) │     │ (header+samples)│     │ (aggregations)   │
└──────────────┘     └─────────────────┘     └──────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌─────────────────┐     ┌──────────────────┐
                     │ Insert Samples  │     │ Insert Dive      │
                     │ (bulk write)    │     │ (with stats)     │
                     └─────────────────┘     └──────────────────┘
                              │                       │
                              ▼                       ▼
                     ┌─────────────────────────────────────────┐
                     │ Update Turtle Stats (async/periodic)    │
                     └─────────────────────────────────────────┘
```

---

## Python/Motor Implementation Notes

```python
# Creating the time-series collection with Motor
async def create_samples_collection(db):
    try:
        await db.create_collection(
            "samples",
            timeseries={
                "timeField": "timestamp",
                "metaField": "metadata",
                "granularity": "seconds"
            }
        )
    except Exception:
        pass  # Collection already exists

# Bulk insert samples for a dive
async def insert_dive_samples(db, dive_id: str, turtle_id: str, samples: list):
    documents = [
        {
            "timestamp": sample["timestamp"],
            "metadata": {
                "dive_id": ObjectId(dive_id),
                "turtle_id": turtle_id
            },
            "sample_index": sample["index"],
            "depth_m": sample["depth"],
            "temperature_c": sample["temperature"],
            "pressure_hpa": sample["pressure"]
        }
        for sample in samples
    ]
    await db.samples.insert_many(documents, ordered=False)
```
