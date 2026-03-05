"""
Turtle Pydantic Models

Defines request/response schemas for turtle-related API endpoints
with comprehensive field documentation for OpenAPI.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class TurtleSpecies(str, Enum):
    """
    Sea turtle species enumeration.

    Includes all seven species of sea turtles recognized worldwide.
    """

    GREEN = "green"
    LOGGERHEAD = "loggerhead"
    LEATHERBACK = "leatherback"
    HAWKSBILL = "hawksbill"
    OLIVE_RIDLEY = "olive_ridley"
    KEMP_RIDLEY = "kemp_ridley"
    FLATBACK = "flatback"


class TurtleStatus(str, Enum):
    """
    Turtle tracking status enumeration.

    Indicates the current state of the satellite tracker.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    LOST = "lost"


class TurtleBase(BaseModel):
    """
    Base turtle schema with common fields.

    This schema contains fields shared between create and response models.
    """

    name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=100,
            description="Name given to the turtle by researchers",
            examples=["Marina", "Captain Jack", "Shelly"],
        ),
    ]

    species: Annotated[
        TurtleSpecies,
        Field(
            description="Species of the sea turtle",
            examples=[TurtleSpecies.GREEN, TurtleSpecies.LOGGERHEAD],
        ),
    ]

    sensor_id: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=50,
            description="Unique identifier of the satellite sensor/tag attached to the turtle",
            examples=["SAT-2024-001", "ARGOS-12345"],
        ),
    ]

    tag_date: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Date and time when the turtle was tagged with the sensor",
            examples=["2024-03-15T10:30:00Z"],
        ),
    ]

    status: Annotated[
        TurtleStatus,
        Field(
            default=TurtleStatus.ACTIVE,
            description="Current tracking status of the turtle",
        ),
    ]


class TurtleCreate(TurtleBase):
    """
    Schema for creating a new turtle.

    Extends TurtleBase with turtle_id which must be unique.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "turtle_id": "TRT-2024-001",
                "name": "Marina",
                "species": "green",
                "sensor_id": "SAT-2024-001",
                "tag_date": "2024-03-15T10:30:00Z",
                "status": "active",
            }
        }
    )

    turtle_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="Unique identifier for the turtle in the system",
            examples=["TRT-2024-001", "GREEN-FL-042"],
        ),
    ]


class TurtleUpdate(BaseModel):
    """
    Schema for updating an existing turtle.

    All fields are optional to allow partial updates.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Marina II",
                "status": "inactive",
            }
        }
    )

    name: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=100,
            description="Updated name for the turtle",
        ),
    ]

    species: Annotated[
        TurtleSpecies | None,
        Field(
            default=None,
            description="Updated species classification",
        ),
    ]

    sensor_id: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=50,
            description="Updated sensor identifier",
        ),
    ]

    tag_date: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Updated tag date",
        ),
    ]

    status: Annotated[
        TurtleStatus | None,
        Field(
            default=None,
            description="Updated tracking status",
        ),
    ]


class TurtleResponse(TurtleBase):
    """
    Schema for turtle responses.

    Includes all base fields plus system-generated fields.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "turtle_id": "TRT-2024-001",
                "name": "Marina",
                "species": "green",
                "sensor_id": "SAT-2024-001",
                "tag_date": "2024-03-15T10:30:00Z",
                "status": "active",
                "created_at": "2024-03-15T10:30:00Z",
                "updated_at": "2024-03-15T10:30:00Z",
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

    turtle_id: Annotated[
        str,
        Field(
            description="Unique identifier for the turtle",
            examples=["TRT-2024-001"],
        ),
    ]

    created_at: Annotated[
        datetime,
        Field(
            description="Timestamp when the record was created",
        ),
    ]

    updated_at: Annotated[
        datetime,
        Field(
            description="Timestamp when the record was last updated",
        ),
    ]


class TurtleListResponse(BaseModel):
    """
    Schema for paginated turtle list responses.

    Includes pagination metadata alongside the turtle data.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "turtle_id": "TRT-2024-001",
                        "name": "Marina",
                        "species": "green",
                        "sensor_id": "SAT-2024-001",
                        "tag_date": "2024-03-15T10:30:00Z",
                        "status": "active",
                        "created_at": "2024-03-15T10:30:00Z",
                        "updated_at": "2024-03-15T10:30:00Z",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10,
            }
        }
    )

    items: Annotated[
        list[TurtleResponse],
        Field(description="List of turtle records"),
    ]

    total: Annotated[
        int,
        Field(
            ge=0,
            description="Total number of turtles matching the query",
        ),
    ]

    skip: Annotated[
        int,
        Field(
            ge=0,
            description="Number of records skipped (offset)",
        ),
    ]

    limit: Annotated[
        int,
        Field(
            ge=1,
            description="Maximum number of records returned",
        ),
    ]
