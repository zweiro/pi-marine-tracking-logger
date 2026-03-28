"""
Sea Turtle Tracking API

Main FastAPI application entry point with comprehensive OpenAPI documentation.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Database
from app.routers import turtles_router, dives_router, samples_router
from app.services.scheduler import PollingScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: PollingScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for database connections and scheduler.
    """
    global scheduler
    settings = get_settings()

    # Startup: Connect to MongoDB
    await Database.connect()
    logger.info("Connected to MongoDB")

    # Start satellite polling scheduler
    db = Database.get_database()
    scheduler = PollingScheduler(
        db=db,
        satellite_api_url=settings.satellite_api_url,
        interval_seconds=settings.satellite_polling_interval_seconds,
        enabled=settings.satellite_polling_enabled,
    )
    await scheduler.start()

    yield

    # Shutdown: Stop scheduler and disconnect from MongoDB
    if scheduler:
        await scheduler.stop()
        logger.info("Scheduler stopped")

    await Database.disconnect()
    logger.info("Disconnected from MongoDB")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "Health",
                "description": "Health check and system status endpoints",
            },
            {
                "name": "Turtles",
                "description": "Manage tracked sea turtles. Create, read, update, and delete turtle records.",
            },
            {
                "name": "Dives",
                "description": "Dive records with metadata and pre-computed statistics.",
            },
            {
                "name": "Samples",
                "description": "Time-series sensor samples with depth, temperature, and pressure measurements.",
            },
            {
                "name": "Sync",
                "description": "Satellite data synchronization and scheduler management.",
            },
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "Sea Turtle Research Team",
            "email": "research@seaturtletracking.org",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(turtles_router, prefix=settings.api_prefix)
    app.include_router(dives_router, prefix=settings.api_prefix)
    app.include_router(samples_router, prefix=settings.api_prefix)

    return app


# Create application instance
app = create_application()


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="""
Check the health status of the API and its dependencies.

Returns the current status of:
- API server
- Database connection
- Satellite polling scheduler

Use this endpoint for monitoring and load balancer health checks.
""",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-03-15T14:30:00Z",
                        "version": "1.0.0",
                        "database": "connected",
                        "scheduler": {"enabled": True, "running": True},
                    }
                }
            },
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2024-03-15T14:30:00Z",
                        "version": "1.0.0",
                        "database": "disconnected",
                        "error": "Database connection failed",
                    }
                }
            },
        },
    },
)
async def health_check():
    """
    Perform health check on the API and its dependencies.
    """
    settings = get_settings()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.app_version,
        "database": "connected",
        "scheduler": scheduler.get_status() if scheduler else None,
    }

    # Check database connection
    try:
        db = Database.get_database()
        await db.command("ping")
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status,
        )

    return health_status


@app.get(
    "/",
    tags=["Health"],
    summary="API root",
    description="Returns basic API information and links to documentation.",
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Sea Turtle Tracking API",
                        "version": "1.0.0",
                        "docs": "/docs",
                        "redoc": "/redoc",
                        "openapi": "/openapi.json",
                    }
                }
            },
        },
    },
)
async def root():
    """
    Return API information and documentation links.
    """
    settings = get_settings()

    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.get(
    "/sync/status",
    tags=["Sync"],
    summary="Get sync status",
    description="Returns the current status of the satellite polling scheduler.",
)
async def get_sync_status():
    """
    Get the current sync/scheduler status.
    """
    if not scheduler:
        return {"error": "Scheduler not initialized"}

    # Get last sync timestamp from database
    db = Database.get_database()
    state = await db.sync_state.find_one({"_id": "satellite_sync"})
    last_sync = state.get("last_timestamp") if state else None
    last_sync_at = state.get("updated_at") if state else None

    return {
        **scheduler.get_status(),
        "last_sync_timestamp": last_sync,
        "last_sync_at": last_sync_at.isoformat() + "Z" if last_sync_at else None,
    }


@app.post(
    "/sync/trigger",
    tags=["Sync"],
    summary="Trigger sync now",
    description="Manually trigger a satellite data fetch operation.",
)
async def trigger_sync():
    """
    Manually trigger a fetch from the satellite API.
    """
    if not scheduler:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Scheduler not initialized"},
        )

    result = await scheduler.trigger_now()
    return result
