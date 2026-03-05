"""
Sample Pydantic Models

Defines request/response schemas for time-series sample data.
Samples are stored in a MongoDB Time Series collection for optimal
analytics performance.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class SampleMetadata(BaseModel):
    """Metadata fields for time-series collection."""

    dive_id: Annotated[
        str,
        Field(
            description="Reference to the dive this sample belongs to",
            examples=["507f1f77bcf86cd799439011"],
        ),
    ]

    turtle_id: Annotated[
        str,
        Field(
            description="Denormalized turtle ID for efficient queries",
            examples=["TRT-2024-001"],
        ),
    ]


class SampleBase(BaseModel):
    """Base sample schema with measurement fields."""

    timestamp: Annotated[
        datetime,
        Field(
            description="Timestamp of the measurement",
            examples=["2024-06-15T14:30:05Z"],
        ),
    ]

    sample_index: Annotated[
        int,
        Field(
            ge=0,
            description="Position in dive sequence (0-indexed)",
            examples=[0, 5, 599],
        ),
    ]

    depth_m: Annotated[
        float,
        Field(
            ge=0,
            description="Depth in meters (calculated from pressure)",
            examples=[12.5, 45.2],
        ),
    ]

    temperature_c: Annotated[
        float,
        Field(
            description="Water temperature in Celsius",
            examples=[21.3, 18.5],
        ),
    ]

    pressure_hpa: Annotated[
        int,
        Field(
            ge=0,
            description="Raw pressure reading in hectopascals",
            examples=[1013, 2263, 5520],
        ),
    ]


class SampleCreate(SampleBase):
    """Schema for creating a new sample."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-06-15T14:30:05Z",
                "sample_index": 5,
                "depth_m": 12.5,
                "temperature_c": 21.3,
                "pressure_hpa": 2263,
            }
        }
    )

    metadata: Annotated[
        SampleMetadata,
        Field(description="Time-series metadata (dive and turtle references)"),
    ]


class SampleBulkCreate(BaseModel):
    """Schema for bulk inserting samples for a dive."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dive_id": "507f1f77bcf86cd799439011",
                "turtle_id": "TRT-2024-001",
                "samples": [
                    {
                        "timestamp": "2024-06-15T14:30:00Z",
                        "sample_index": 0,
                        "depth_m": 0.0,
                        "temperature_c": 22.0,
                        "pressure_hpa": 1013,
                    },
                    {
                        "timestamp": "2024-06-15T14:30:01Z",
                        "sample_index": 1,
                        "depth_m": 2.5,
                        "temperature_c": 21.8,
                        "pressure_hpa": 1263,
                    },
                ],
            }
        }
    )

    dive_id: Annotated[
        str,
        Field(description="MongoDB ID of the parent dive"),
    ]

    turtle_id: Annotated[
        str,
        Field(description="Turtle ID for denormalization"),
    ]

    samples: Annotated[
        list[SampleBase],
        Field(description="List of samples to insert"),
    ]


class SampleResponse(SampleBase):
    """Schema for sample responses."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "timestamp": "2024-06-15T14:30:05Z",
                "sample_index": 5,
                "depth_m": 12.5,
                "temperature_c": 21.3,
                "pressure_hpa": 2263,
                "metadata": {
                    "dive_id": "507f1f77bcf86cd799439011",
                    "turtle_id": "TRT-2024-001",
                },
            }
        },
    )

    id: Annotated[
        str,
        Field(
            description="MongoDB document ID",
            examples=["507f1f77bcf86cd799439012"],
        ),
    ]

    metadata: Annotated[
        SampleMetadata,
        Field(description="Time-series metadata"),
    ]


class SampleListResponse(BaseModel):
    """Schema for paginated sample list responses."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439012",
                        "timestamp": "2024-06-15T14:30:05Z",
                        "sample_index": 5,
                        "depth_m": 12.5,
                        "temperature_c": 21.3,
                        "pressure_hpa": 2263,
                        "metadata": {
                            "dive_id": "507f1f77bcf86cd799439011",
                            "turtle_id": "TRT-2024-001",
                        },
                    }
                ],
                "total": 600,
                "skip": 0,
                "limit": 100,
            }
        }
    )

    items: Annotated[
        list[SampleResponse],
        Field(description="List of sample records"),
    ]

    total: Annotated[
        int,
        Field(ge=0, description="Total number of samples matching the query"),
    ]

    skip: Annotated[
        int,
        Field(ge=0, description="Number of records skipped (offset)"),
    ]

    limit: Annotated[
        int,
        Field(ge=1, description="Maximum number of records returned"),
    ]


class SampleStats(BaseModel):
    """Schema for sample statistics/aggregations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 600,
                "avg_depth_m": 28.7,
                "max_depth_m": 45.2,
                "min_depth_m": 0.0,
                "avg_temperature_c": 20.1,
                "min_temperature_c": 18.5,
                "max_temperature_c": 22.3,
            }
        }
    )

    count: Annotated[
        int,
        Field(ge=0, description="Total number of samples"),
    ]

    avg_depth_m: Annotated[
        float | None,
        Field(description="Average depth in meters"),
    ]

    max_depth_m: Annotated[
        float | None,
        Field(description="Maximum depth in meters"),
    ]

    min_depth_m: Annotated[
        float | None,
        Field(description="Minimum depth in meters"),
    ]

    avg_temperature_c: Annotated[
        float | None,
        Field(description="Average temperature in Celsius"),
    ]

    min_temperature_c: Annotated[
        float | None,
        Field(description="Minimum temperature in Celsius"),
    ]

    max_temperature_c: Annotated[
        float | None,
        Field(description="Maximum temperature in Celsius"),
    ]
