"""
Turtle API Router

Provides CRUD endpoints for managing tracked sea turtles.
All endpoints are documented with OpenAPI metadata.
"""

from datetime import datetime
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.turtle import (
    TurtleCreate,
    TurtleUpdate,
    TurtleResponse,
    TurtleListResponse,
    TurtleSpecies,
    TurtleStatus,
)

router = APIRouter(
    prefix="/turtles",
    tags=["Turtles"],
    responses={
        404: {"description": "Turtle not found"},
        500: {"description": "Internal server error"},
    },
)


def turtle_doc_to_response(doc: dict) -> TurtleResponse:
    """Convert MongoDB document to TurtleResponse model."""
    return TurtleResponse(
        id=str(doc["_id"]),
        turtle_id=doc["turtle_id"],
        name=doc["name"],
        species=doc["species"],
        sensor_id=doc.get("sensor_id"),
        tag_date=doc.get("tag_date"),
        status=doc["status"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get(
    "",
    response_model=TurtleListResponse,
    summary="List all turtles",
    description="""
Retrieve a paginated list of all tracked turtles.

Supports filtering by species and status, with pagination controls.
Results are sorted by creation date (newest first).
""",
    responses={
        200: {
            "description": "List of turtles retrieved successfully",
            "content": {
                "application/json": {
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
            },
        }
    },
)
async def list_turtles(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    species: Annotated[
        TurtleSpecies | None,
        Query(description="Filter by turtle species"),
    ] = None,
    status: Annotated[
        TurtleStatus | None,
        Query(description="Filter by tracking status"),
    ] = None,
    skip: Annotated[
        int,
        Query(ge=0, description="Number of records to skip"),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum records to return"),
    ] = 10,
) -> TurtleListResponse:
    """
    List all turtles with optional filtering and pagination.
    """
    # Build filter query
    query = {}
    if species:
        query["species"] = species.value
    if status:
        query["status"] = status.value

    # Get total count
    total = await db.turtles.count_documents(query)

    # Fetch paginated results
    cursor = db.turtles.find(query).sort("created_at", -1).skip(skip).limit(limit)
    documents = await cursor.to_list(length=limit)

    items = [turtle_doc_to_response(doc) for doc in documents]

    return TurtleListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{turtle_id}",
    response_model=TurtleResponse,
    summary="Get turtle by ID",
    description="""
Retrieve a single turtle by its unique turtle_id.

Returns the full turtle record including all metadata and timestamps.
""",
    responses={
        200: {"description": "Turtle found and returned"},
        404: {"description": "Turtle with the specified ID not found"},
    },
)
async def get_turtle(
    turtle_id: Annotated[str, "Unique turtle identifier"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TurtleResponse:
    """
    Get a specific turtle by its turtle_id.
    """
    document = await db.turtles.find_one({"turtle_id": turtle_id})

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Turtle with ID '{turtle_id}' not found",
        )

    return turtle_doc_to_response(document)


@router.post(
    "",
    response_model=TurtleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new turtle",
    description="""
Register a new turtle in the tracking system.

The turtle_id must be unique across the system. If a turtle with the
same turtle_id already exists, a 409 Conflict error will be returned.
""",
    responses={
        201: {"description": "Turtle created successfully"},
        409: {"description": "Turtle with this ID already exists"},
    },
)
async def create_turtle(
    turtle: TurtleCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TurtleResponse:
    """
    Create a new turtle record.
    """
    # Check for duplicate turtle_id
    existing = await db.turtles.find_one({"turtle_id": turtle.turtle_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Turtle with ID '{turtle.turtle_id}' already exists",
        )

    now = datetime.utcnow()
    document = {
        **turtle.model_dump(),
        "created_at": now,
        "updated_at": now,
    }

    result = await db.turtles.insert_one(document)
    document["_id"] = result.inserted_id

    return turtle_doc_to_response(document)


@router.put(
    "/{turtle_id}",
    response_model=TurtleResponse,
    summary="Update a turtle",
    description="""
Update an existing turtle's information.

Only provided fields will be updated; omitted fields remain unchanged.
The turtle_id cannot be changed.
""",
    responses={
        200: {"description": "Turtle updated successfully"},
        404: {"description": "Turtle not found"},
    },
)
async def update_turtle(
    turtle_id: Annotated[str, "Unique turtle identifier"],
    turtle_update: TurtleUpdate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TurtleResponse:
    """
    Update an existing turtle record.
    """
    # Build update document with only provided fields
    update_data = turtle_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    update_data["updated_at"] = datetime.utcnow()

    result = await db.turtles.find_one_and_update(
        {"turtle_id": turtle_id},
        {"$set": update_data},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Turtle with ID '{turtle_id}' not found",
        )

    return turtle_doc_to_response(result)


@router.delete(
    "/{turtle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a turtle",
    description="""
Remove a turtle from the tracking system.

This action is permanent and cannot be undone. Associated readings
are NOT automatically deleted.
""",
    responses={
        204: {"description": "Turtle deleted successfully"},
        404: {"description": "Turtle not found"},
    },
)
async def delete_turtle(
    turtle_id: Annotated[str, "Unique turtle identifier"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> None:
    """
    Delete a turtle record.
    """
    result = await db.turtles.delete_one({"turtle_id": turtle_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Turtle with ID '{turtle_id}' not found",
        )
