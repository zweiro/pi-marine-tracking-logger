"""
Pydantic Models

This module exports all Pydantic models used for request/response
validation and serialization.
"""

from app.models.turtle import (
    TurtleSpecies,
    TurtleStatus,
    TurtleBase,
    TurtleCreate,
    TurtleUpdate,
    TurtleResponse,
    TurtleListResponse,
)
from app.models.dive import (
    GeoJSONPoint,
    DiveStats,
    PacketMetadata,
    DiveBase,
    DiveCreate,
    DiveResponse,
    DiveListResponse,
)
from app.models.sample import (
    SampleMetadata,
    SampleBase,
    SampleCreate,
    SampleBulkCreate,
    SampleResponse,
    SampleListResponse,
    SampleStats,
)

__all__ = [
    # Turtle models
    "TurtleSpecies",
    "TurtleStatus",
    "TurtleBase",
    "TurtleCreate",
    "TurtleUpdate",
    "TurtleResponse",
    "TurtleListResponse",
    # Dive models
    "GeoJSONPoint",
    "DiveStats",
    "PacketMetadata",
    "DiveBase",
    "DiveCreate",
    "DiveResponse",
    "DiveListResponse",
    # Sample models
    "SampleMetadata",
    "SampleBase",
    "SampleCreate",
    "SampleBulkCreate",
    "SampleResponse",
    "SampleListResponse",
    "SampleStats",
]
