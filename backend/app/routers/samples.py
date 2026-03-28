"""
Sample API Router

Provides endpoints for managing time-series sample data.
Optimized for bulk operations and analytics queries.
"""

from datetime import datetime
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.sample import (
    SampleBulkCreate,
    SampleResponse,
    SampleListResponse,
    SampleStats,
    SampleMetadata,
)

router = APIRouter(
    prefix="/samples",
    tags=["Samples"],
    responses={
        404: {"description": "Sample not found"},
        500: {"description": "Internal server error"},
    },
)


def sample_doc_to_response(doc: dict) -> SampleResponse:
    """Convert MongoDB document to SampleResponse model."""
    metadata = doc.get("metadata", {})
    return SampleResponse(
        id=str(doc["_id"]),
        timestamp=doc["timestamp"],
        sample_index=doc["sample_index"],
        depth_m=doc["depth_m"],
        temperature_c=doc["temperature_c"],
        pressure_hpa=doc["pressure_hpa"],
        metadata=SampleMetadata(
            dive_id=str(metadata.get("dive_id", "")),
            turtle_id=metadata.get("turtle_id", ""),
        ),
    )


@router.get(
    "/dive/{dive_id}",
    response_model=SampleListResponse,
    summary="Get samples for a dive",
    description="""
Retrieve all samples for a specific dive.

Results are sorted by sample_index (chronological order).
Supports pagination for large dives.
""",
)
async def get_samples_by_dive(
    dive_id: Annotated[str, "MongoDB ObjectId of the dive"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    skip: Annotated[
        int,
        Query(ge=0, description="Number of records to skip"),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum records to return"),
    ] = 100,
) -> SampleListResponse:
    """
    Get all samples for a dive.
    """
    try:
        object_id = ObjectId(dive_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dive ID format: '{dive_id}'",
        )

    query = {"metadata.dive_id": object_id}

    total = await db.samples.count_documents(query)

    cursor = (
        db.samples.find(query)
        .sort("sample_index", 1)
        .skip(skip)
        .limit(limit)
    )
    documents = await cursor.to_list(length=limit)

    items = [sample_doc_to_response(doc) for doc in documents]

    return SampleListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/turtle/{turtle_id}",
    response_model=SampleListResponse,
    summary="Get samples for a turtle",
    description="""
Retrieve samples for a specific turtle across all dives.

Results are sorted by timestamp (newest first).
Supports time range filtering.
""",
)
async def get_samples_by_turtle(
    turtle_id: Annotated[str, "Unique turtle identifier"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    start_time: Annotated[
        datetime | None,
        Query(description="Filter samples after this time"),
    ] = None,
    end_time: Annotated[
        datetime | None,
        Query(description="Filter samples before this time"),
    ] = None,
    skip: Annotated[
        int,
        Query(ge=0, description="Number of records to skip"),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum records to return"),
    ] = 100,
) -> SampleListResponse:
    """
    Get samples for a turtle with optional time range filtering.
    """
    query: dict = {"metadata.turtle_id": turtle_id}

    if start_time or end_time:
        query["timestamp"] = {}
        if start_time:
            query["timestamp"]["$gte"] = start_time
        if end_time:
            query["timestamp"]["$lt"] = end_time

    total = await db.samples.count_documents(query)

    cursor = (
        db.samples.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    documents = await cursor.to_list(length=limit)

    items = [sample_doc_to_response(doc) for doc in documents]

    return SampleListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/dive/{dive_id}/stats",
    response_model=SampleStats,
    summary="Get statistics for a dive",
    description="Compute aggregate statistics for all samples in a dive.",
)
async def get_dive_stats(
    dive_id: Annotated[str, "MongoDB ObjectId of the dive"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> SampleStats:
    """
    Compute statistics for samples in a dive.
    """
    try:
        object_id = ObjectId(dive_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dive ID format: '{dive_id}'",
        )

    pipeline = [
        {"$match": {"metadata.dive_id": object_id}},
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "avg_depth_m": {"$avg": "$depth_m"},
                "max_depth_m": {"$max": "$depth_m"},
                "min_depth_m": {"$min": "$depth_m"},
                "avg_temperature_c": {"$avg": "$temperature_c"},
                "min_temperature_c": {"$min": "$temperature_c"},
                "max_temperature_c": {"$max": "$temperature_c"},
            }
        },
    ]

    cursor = db.samples.aggregate(pipeline)
    results = await cursor.to_list(length=1)

    if not results:
        return SampleStats(
            count=0,
            avg_depth_m=None,
            max_depth_m=None,
            min_depth_m=None,
            avg_temperature_c=None,
            min_temperature_c=None,
            max_temperature_c=None,
        )

    result = results[0]
    return SampleStats(
        count=result["count"],
        avg_depth_m=round(result["avg_depth_m"], 2) if result["avg_depth_m"] else None,
        max_depth_m=result["max_depth_m"],
        min_depth_m=result["min_depth_m"],
        avg_temperature_c=round(result["avg_temperature_c"], 2) if result["avg_temperature_c"] else None,
        min_temperature_c=result["min_temperature_c"],
        max_temperature_c=result["max_temperature_c"],
    )


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk insert samples",
    description="""
Insert multiple samples for a dive in a single operation.

This is the preferred method for ingesting dive data from satellite packets.
All samples are associated with the specified dive and turtle.
""",
    responses={
        201: {"description": "Samples inserted successfully"},
        404: {"description": "Dive not found"},
    },
)
async def bulk_create_samples(
    data: SampleBulkCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> dict:
    """
    Bulk insert samples for a dive.
    """
    try:
        dive_object_id = ObjectId(data.dive_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dive ID format: '{data.dive_id}'",
        )

    # Verify dive exists
    dive = await db.dives.find_one({"_id": dive_object_id})
    if not dive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dive '{data.dive_id}' not found",
        )

    # Build documents for bulk insert
    documents = [
        {
            "timestamp": sample.timestamp,
            "metadata": {
                "dive_id": dive_object_id,
                "turtle_id": data.turtle_id,
            },
            "sample_index": sample.sample_index,
            "depth_m": sample.depth_m,
            "temperature_c": sample.temperature_c,
            "pressure_hpa": sample.pressure_hpa,
        }
        for sample in data.samples
    ]

    if documents:
        result = await db.samples.insert_many(documents, ordered=False)
        inserted_count = len(result.inserted_ids)
    else:
        inserted_count = 0

    return {
        "inserted_count": inserted_count,
        "dive_id": data.dive_id,
        "turtle_id": data.turtle_id,
    }


@router.delete(
    "/dive/{dive_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete samples for a dive",
    description="Remove all samples associated with a dive.",
)
async def delete_samples_by_dive(
    dive_id: Annotated[str, "MongoDB ObjectId of the dive"],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> None:
    """
    Delete all samples for a dive.
    """
    try:
        object_id = ObjectId(dive_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dive ID format: '{dive_id}'",
        )

    await db.samples.delete_many({"metadata.dive_id": object_id})
