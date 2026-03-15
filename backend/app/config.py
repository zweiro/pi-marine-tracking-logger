"""
Application Configuration

Uses pydantic-settings to load configuration from environment variables
with sensible defaults for development.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        app_name: Name of the application displayed in API docs.
        app_version: Current version of the API.
        debug: Enable debug mode for development.
        mongodb_url: MongoDB connection string.
        mongodb_database: Name of the MongoDB database.
        cors_origins: List of allowed CORS origins.
        api_prefix: Prefix for all API routes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = "Sea Turtle Tracking API"
    app_version: str = "1.0.0"
    app_description: str = """
## Sea Turtle Tracking API

This API provides endpoints for tracking and monitoring sea turtle movements
using satellite data. It supports researchers and conservationists in gathering
valuable data about sea turtle migration patterns and behavior.

### Features

* **Turtle Management** - Register and manage tracked turtles
* **Sensor Readings** - Store and retrieve GPS, temperature, and depth data
* **Geospatial Queries** - Filter readings by location and time range
* **Data Export** - Export tracking data in various formats

### Data Sources

Satellite tracking data is ingested from tagged sea turtles equipped with
GPS sensors that transmit location, temperature, and pressure readings.
"""

    # Debug mode
    debug: bool = False

    # MongoDB settings
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "turtle_tracking"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # API settings
    api_prefix: str = "/api/v1"

    # Satellite polling settings
    satellite_polling_enabled: bool = True
    satellite_polling_interval_seconds: int = 300
    satellite_api_url: str = "http://localhost:8001"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.

    Returns:
        Settings: Application configuration instance.
    """
    return Settings()
