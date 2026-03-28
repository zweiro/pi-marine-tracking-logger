"""
Dive API Router

Provides endpoints for managing dive records.
All endpoints are documented with OpenAPI metadata.
"""

from datetime import datetime
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.dive import (
    DiveCreate,
    DiveResponse,
    DiveListResponse,
)

router = APIRouter(
    prefix="/dives",
    tags=["Dives"],
    responses={
        404: {"description": "Dive not found"},
        500: {"description": "Internal server error"},
    },
)


def dive_doc_to_response(doc: dict) -> DiveResponse:
    """Convert MongoDB document to DiveResponse model."""
    return DiveResponse(
        id=str(doc["_id"]),
        turtle_id=doc["turtle_id"],
        dive_id=doc["dive_id"],
        start_time=doc["start_time"],
        end_time=doc["end_time"],
        duration_s=doc["duration_s"],
        start_location=doc["start_location"],
        end_location=doc.get("end_location"),
        stats=doc["stats"],
        packet_metadata=doc.get("packet_metadata"),
        created_at=doc["created_at"],
    )


@router.get(
    "",
    response_model=DiveListResponse,
    summary="List dives",
    description="""
Retrieve a paginated list of dive records.

Supports filtering by turtle_id with pagination controls.
Results are sorted by start_time (newest first).
""",
)
async def list_dives(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    turtle_id: Annotated[
        str | None,
        Query(description="Filter by turtle ID"),
    ] = None,
    skip: Annotated[
        int,
        Query(ge=0, description="Number of records to skip"),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum records to return"),
    ] = 20,
) -> DiveListResponse:
    """
    List dives with optional filtering and pagination.
    """
    query = {}
    if turtle_id:
        query["turtle_id"] = turtle_id

    total = await db.dives.count_documents(query)

    cursor = db.dives.find(query).sort("start_time", -1).skip(skip).limit(limit)
    documents = await cursor.to_list(length=limit)

    items = [dive_doc_to_response(doc) for doc in documents]

    return DiveListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{dive_id}",
    response_model=DiveResponse,
    summary="Get dive by MongoDB ID",
    description="Retrieve a single dive by its MongoDB ObjectId.",
)
async def get_dive(
    dive_id: Annotated[str, "MongoDB ObjectId of the dive"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> DiveResponse:
    """
    Get a specific dive by its MongoDB ID.
    """
    try:
        object_id = ObjectId(dive_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dive ID format: '{dive_id}'",
        )

    document = await db.dives.find_one({"_id": object_id})

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dive with ID '{dive_id}' not found",
        )

    return dive_doc_to_response(document)


@router.get(
    "/turtle/{turtle_id}/dive/{dive_number}",
    response_model=DiveResponse,
    summary="Get dive by turtle and dive number",
    description="Retrieve a dive using turtle_id and dive_id from the packet.",
)
async def get_dive_by_number(
    turtle_id: Annotated[str, "Unique turtle identifier"],
    dive_number: Annotated[int, "Dive number from satellite packet"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> DiveResponse:
    """
    Get a specific dive by turtle_id and dive number.
    """
    document = await db.dives.find_one({
        "turtle_id": turtle_id,
        "dive_id": dive_number,
    })

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dive {dive_number} for turtle '{turtle_id}' not found",
        )

    return dive_doc_to_response(document)


@router.post(
    "",
    response_model=DiveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dive",
    description="""
Record a new dive in the system.

The combination of turtle_id and dive_id must be unique.
Statistics should be pre-computed from samples before insertion.
""",
    responses={
        201: {"description": "Dive created successfully"},
        409: {"description": "Dive already exists for this turtle"},
    },
)
async def create_dive(
    dive: DiveCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> DiveResponse:
    """
    Create a new dive record.
    """
    # Check for duplicate
    existing = await db.dives.find_one({
        "turtle_id": dive.turtle_id,
        "dive_id": dive.dive_id,
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dive {dive.dive_id} already exists for turtle '{dive.turtle_id}'",
        )

    # Verify turtle exists
    turtle = await db.turtles.find_one({"turtle_id": dive.turtle_id})
    if not turtle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Turtle '{dive.turtle_id}' not found",
        )

    now = datetime.utcnow()
    document = {
        **dive.model_dump(),
        "created_at": now,
    }

    result = await db.dives.insert_one(document)
    document["_id"] = result.inserted_id

    return dive_doc_to_response(document)


@router.delete(
    "/{dive_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dive",
    description="""
Remove a dive and its associated samples from the system.

This action is permanent and cannot be undone.
""",
    responses={
        204: {"description": "Dive deleted successfully"},
        404: {"description": "Dive not found"},
    },
)
async def delete_dive(
    dive_id: Annotated[str, "MongoDB ObjectId of the dive"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> None:
    """
    Delete a dive and its samples.
    """
    try:
        object_id = ObjectId(dive_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dive ID format: '{dive_id}'",
        )

    # Delete associated samples first
    await db.samples.delete_many({"metadata.dive_id": object_id})

    # Delete the dive
    result = await db.dives.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dive with ID '{dive_id}' not found",
        )
