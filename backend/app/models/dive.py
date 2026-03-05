"""
Dive Pydantic Models

Defines request/response schemas for dive-related API endpoints
with comprehensive field documentation for OpenAPI.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry for location data."""

    type: Annotated[
        str,
        Field(default="Point", description="GeoJSON geometry type"),
    ]

    coordinates: Annotated[
        list[float],
        Field(
            min_length=2,
            max_length=2,
            description="Coordinates as [longitude, latitude]",
            examples=[[6.1432, 46.2044]],
        ),
    ]


class DiveStats(BaseModel):
    """Pre-computed statistics for a dive."""

    sample_count: Annotated[
        int,
        Field(ge=0, description="Number of samples in the dive"),
    ]

    sample_period_ms: Annotated[
        int,
        Field(ge=1, description="Sampling period in milliseconds"),
    ]

    max_depth_m: Annotated[
        float | None,
        Field(default=None, ge=0, description="Maximum depth reached in meters"),
    ]

    avg_depth_m: Annotated[
        float | None,
        Field(default=None, ge=0, description="Average depth in meters"),
    ]

    min_temperature_c: Annotated[
        float | None,
        Field(default=None, description="Minimum temperature in Celsius"),
    ]

    max_temperature_c: Annotated[
        float | None,
        Field(default=None, description="Maximum temperature in Celsius"),
    ]

    avg_temperature_c: Annotated[
        float | None,
        Field(default=None, description="Average temperature in Celsius"),
    ]


class PacketMetadata(BaseModel):
    """Raw packet metadata for debugging/reprocessing."""

    gps_week: Annotated[
        int,
        Field(ge=0, description="GPS week number"),
    ]

    gps_tow_s: Annotated[
        int,
        Field(ge=0, description="GPS time of week in seconds"),
    ]

    header_len: Annotated[
        int,
        Field(ge=0, description="Original packet header length in bytes"),
    ]


class DiveBase(BaseModel):
    """Base dive schema with common fields."""

    turtle_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="Reference to the turtle this dive belongs to",
            examples=["TRT-2024-001"],
        ),
    ]

    dive_id: Annotated[
        int,
        Field(
            ge=0,
            description="Dive identifier from satellite packet",
            examples=[1, 42, 156],
        ),
    ]

    start_time: Annotated[
        datetime,
        Field(
            description="Start time of the dive",
            examples=["2024-06-15T14:30:00Z"],
        ),
    ]

    end_time: Annotated[
        datetime,
        Field(
            description="End time of the dive",
            examples=["2024-06-15T14:40:00Z"],
        ),
    ]

    duration_s: Annotated[
        int,
        Field(
            ge=0,
            description="Total dive duration in seconds",
            examples=[600],
        ),
    ]

    start_location: Annotated[
        GeoJSONPoint,
        Field(description="GPS location at dive start (surface)"),
    ]

    end_location: Annotated[
        GeoJSONPoint | None,
        Field(default=None, description="GPS location at dive end (surface)"),
    ]

    stats: Annotated[
        DiveStats,
        Field(description="Pre-computed dive statistics"),
    ]

    packet_metadata: Annotated[
        PacketMetadata | None,
        Field(default=None, description="Raw packet metadata for debugging"),
    ]


class DiveCreate(DiveBase):
    """Schema for creating a new dive record."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "turtle_id": "TRT-2024-001",
                "dive_id": 1,
                "start_time": "2024-06-15T14:30:00Z",
                "end_time": "2024-06-15T14:40:00Z",
                "duration_s": 600,
                "start_location": {
                    "type": "Point",
                    "coordinates": [6.1432, 46.2044],
                },
                "stats": {
                    "sample_count": 600,
                    "sample_period_ms": 1000,
                    "max_depth_m": 45.2,
                    "avg_depth_m": 28.7,
                    "avg_temperature_c": 20.1,
                },
            }
        }
    )


class DiveResponse(DiveBase):
    """Schema for dive responses."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "turtle_id": "TRT-2024-001",
                "dive_id": 1,
                "start_time": "2024-06-15T14:30:00Z",
                "end_time": "2024-06-15T14:40:00Z",
                "duration_s": 600,
                "start_location": {
                    "type": "Point",
                    "coordinates": [6.1432, 46.2044],
                },
                "stats": {
                    "sample_count": 600,
                    "sample_period_ms": 1000,
                    "max_depth_m": 45.2,
                    "avg_depth_m": 28.7,
                    "avg_temperature_c": 20.1,
                },
                "created_at": "2024-06-15T14:45:00Z",
            }
        },
    )

    id: Annotated[
        str,
        Field(
            description="MongoDB document ID",
            examples=["507f1f77bcf86cd799439011"],
        ),
    ]

    created_at: Annotated[
        datetime,
        Field(description="Timestamp when the record was created"),
    ]


class DiveListResponse(BaseModel):
    """Schema for paginated dive list responses."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "turtle_id": "TRT-2024-001",
                        "dive_id": 1,
                        "start_time": "2024-06-15T14:30:00Z",
                        "end_time": "2024-06-15T14:40:00Z",
                        "duration_s": 600,
                        "start_location": {
                            "type": "Point",
                            "coordinates": [6.1432, 46.2044],
                        },
                        "stats": {
                            "sample_count": 600,
                            "sample_period_ms": 1000,
                            "max_depth_m": 45.2,
                            "avg_depth_m": 28.7,
                        },
                        "created_at": "2024-06-15T14:45:00Z",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 20,
            }
        }
    )

    items: Annotated[
        list[DiveResponse],
        Field(description="List of dive records"),
    ]

    total: Annotated[
        int,
        Field(ge=0, description="Total number of dives matching the query"),
    ]

    skip: Annotated[
        int,
        Field(ge=0, description="Number of records skipped (offset)"),
    ]

    limit: Annotated[
        int,
        Field(ge=1, description="Maximum number of records returned"),
    ]
