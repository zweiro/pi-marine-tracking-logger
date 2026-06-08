# PI MONIT - Sea Turtle Tracking

A web application for monitoring sea turtle movements using satellite data. The system fetches dive telemetry from satellite APIs, stores it in MongoDB, and visualizes turtle tracking data through a Vue.js frontend.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Vue.js Frontend │────▶│ FastAPI Backend │────▶│    MongoDB      │
│    (port 5173)  │     │   (port 8000)   │     │   (port 27017)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Satellite API   │
                        │   (port 8001)   │
                        └─────────────────┘
```

### Data Model

```
Turtle (1) --> Dive (N) --> Sample (N)
```

- **Turtle**: Tracked animal with species, sensor ID, and status
- **Dive**: Dive session with computed statistics (max depth, avg temperature)
- **Sample**: Time-series sensor measurements (depth, temperature, pressure)

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pi-marine-tracking-app
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs
   - Mock Satellite: http://localhost:8001

## Running Tests

```bash
docker-compose exec backend pytest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `turtle_tracking` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:5173"]` |
| `API_PREFIX` | API route prefix | `/api/v1` |
| `SATELLITE_POLLING_ENABLED` | Enable satellite polling | `true` |
| `SATELLITE_POLLING_INTERVAL_SECONDS` | Polling interval | `300` |
| `SATELLITE_API_URL` | Satellite API endpoint | `http://localhost:8001` |

## API Endpoints

### Turtles
- `GET /api/v1/turtles` - List all turtles
- `GET /api/v1/turtles/{turtle_id}` - Get turtle by ID
- `POST /api/v1/turtles` - Create a new turtle
- `PUT /api/v1/turtles/{turtle_id}` - Update turtle
- `DELETE /api/v1/turtles/{turtle_id}` - Delete turtle

### Dives
- `GET /api/v1/dives` - List dives (filter by turtle_id)
- `GET /api/v1/dives/{id}` - Get dive by ID
- `POST /api/v1/dives` - Create a dive
- `DELETE /api/v1/dives/{id}` - Delete dive

### Samples
- `GET /api/v1/samples/dive/{dive_id}` - Get samples for a dive
- `GET /api/v1/samples/turtle/{turtle_id}` - Get samples for a turtle
- `GET /api/v1/samples/dive/{dive_id}/stats` - Get dive statistics

### Sync
- `GET /sync/status` - Get satellite sync status
- `POST /sync/trigger` - Manually trigger satellite fetch

## Project Structure

```
pi-marine-tracking-app/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── config.py       # Configuration settings
│   │   ├── database.py     # MongoDB connection
│   │   ├── models/         # Pydantic schemas
│   │   ├── routers/        # API endpoints
│   │   └── services/       # Business logic
│   └── tests/              # Backend tests
├── frontend/               # Vue.js application
├── mock-satellite/         # Satellite API simulator
├── notebooks/              # Jupyter notebooks for analysis
├── docker-compose.yml      # Docker services configuration
└── .env.example            # Environment variables template
```

## Contributors

- Jeyapiragash Jeyapalan - jeyapiragash.jeyapalan@master.hes-so.ch
- Benoit Schick - benoit.schick@hes-so.ch
- Daryl Warpelin - daryl.warpelin@students.hevs.ch
- Robin Zweifel - robin.zweifel@heig-vd.ch

## License

This is an academic project developed for educational purposes.
