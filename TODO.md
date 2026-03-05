# PI Web App Tasks - Sea Turtle Tracking

## Backend

### MongoDB Database Container
- [ ] Create a docker container for a MongoDB database to store satellite data
  - [ ] Define Dockerfile with MongoDB image and persistent volume
  - [ ] Create database schema for turtle tracking:
    - `turtles`: turtle_id, name, species, tag_date, sensor_id, notes
    - `readings`: turtle_id, timestamp, latitude, longitude, temperature, pressure, depth
    - `tracks`: aggregated movement paths per turtle

### FastAPI Backend Container
- [ ] Create a docker container for a FastAPI backend
  - [ ] Create REST API endpoints:
    - `GET /turtles` - list all tracked turtles
    - `GET /turtles/{id}` - turtle details and latest reading
    - `GET /turtles/{id}/readings` - sensor history with date filters
    - `GET /readings/latest` - latest readings for all turtles
    - `GET /readings/area` - query readings within geographic bounds
  - [ ] Add Pydantic models for request/response validation
  - [ ] Configure CORS for frontend access

### Data Ingestion
- [ ] Create a CRON job to fetch satellite data from the API every 20 minutes
  - [ ] Integrate with satellite company's existing API
  - [ ] Parse incoming data: position, temperature, pressure readings
  - [ ] Calculate depth from pressure sensor data
  - [ ] Add error handling and retry logic

### Docker Compose
- [ ] Create docker-compose.yml to orchestrate all containers

---

## Seeding and Setup for Testing

### Mock Satellite API
- [ ] Create a container to mock the satellite data API for testing
  - [ ] Generate realistic turtle movement patterns (migration routes)
  - [ ] Simulate temperature variations by depth/location

### Real Data Sample
- [ ] Find a real data sample with open data
  - [ ] Research sources: Movebank
  - [ ] Process the data to fit the database schema
    - [ ] Parse Argos or GPS satellite formats
    - [ ] Convert coordinates and timestamps
    - [ ] Validate temperature/pressure ranges
  - [ ] Seed the MongoDB database with processed data
    - [ ] Include multiple turtle species
    - [ ] Cover different geographic regions and seasons

---

## Web App

### Vue.js Frontend
- [ ] Create a Vue.js frontend app to display the satellite data
  - [ ] Initialize with Vite + Vue 3 + TypeScript
  - [ ] Set up Vue Router and Pinia state management
  - [ ] Create API service layer

### About Page
- [ ] Create an about page to explain the purpose of the app
  - [ ] Describe sea turtle conservation goals
  - [ ] Explain satellite tracking methodology
  - [ ] Credit research institutions and data sources

### Dashboard
- [ ] Create a dashboard to display satellite data
  - [ ] Summary cards: active turtles, total readings, coverage area
  - [ ] Temperature/pressure charts over time (per turtle)
  - [ ] Depth profile visualizations
  - [ ] Recent activity table with sorting/filtering
  - [ ] Species distribution breakdown

### Map View
- [ ] Create a map view to visualize turtle movements
  - [ ] Display turtle positions with species-specific icons
  - [ ] Draw migration tracks as colored polylines
  - [ ] Popup with turtle info and latest sensor readings
  #### if time allows:
  - [ ] Heatmap layer for frequently visited areas
  - [ ] Time slider to animate movement over time

### Export Page
- [ ] Create an export page for data download
  - [ ] Export formats:
    - CSV (for spreadsheets/R/Python analysis)

---

## Report Documentation
- [ ] System architecture diagram
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Database schema documentation
- [ ] User guide with screenshots