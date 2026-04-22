"""
Mock Satellite API

Simulates a satellite data provider API for development and testing.
Generates realistic dive packets on demand or automatically.
"""

import os
import random
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, BackgroundTasks
from pydantic import BaseModel
import asyncio

from packet_generator import generate_packet_hex

# Configuration from environment
AUTO_GENERATE_ENABLED = os.getenv("AUTO_GENERATE_ENABLED", "true").lower() == "true"
AUTO_GENERATE_INTERVAL_SECONDS = int(os.getenv("AUTO_GENERATE_INTERVAL_SECONDS", "60"))
TURTLE_IDS = os.getenv("TURTLE_IDS", "TRT-2024-001,TRT-2024-002").split(",")

# In-memory packet store
packets_store: list[dict] = []
dive_counters: dict[str, int] = {tid: 0 for tid in TURTLE_IDS}
auto_generate_task: asyncio.Task | None = None


class PacketResponse(BaseModel):
    """Response model for packet endpoints."""

    packets: list[dict]
    count: int
    last_timestamp: str | None


class StatsResponse(BaseModel):
    """Response model for stats endpoint."""

    total_packets: int
    packets_by_turtle: dict[str, int]
    auto_generate_enabled: bool
    auto_generate_interval_seconds: int


async def auto_generate_packets():
    """Background task that generates packets automatically."""
    while True:
        await asyncio.sleep(AUTO_GENERATE_INTERVAL_SECONDS)

        # Generate a packet for a random turtle
        turtle_id = random.choice(TURTLE_IDS)
        dive_counters[turtle_id] += 1

        packet = generate_packet_hex(
            turtle_id=turtle_id,
            dive_id=dive_counters[turtle_id],
            sample_count=random.randint(300, 600),
            max_depth_m=random.uniform(20, 80),
            surface_temp_c=random.uniform(20, 26),
            deep_temp_c=random.uniform(12, 18),
        )

        packets_store.append(packet)
        print(f"Auto-generated packet for {turtle_id}, dive {dive_counters[turtle_id]}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global auto_generate_task

    # Generate some initial packets
    for turtle_id in TURTLE_IDS:
        for _ in range(2):
            dive_counters[turtle_id] += 1
            packet = generate_packet_hex(
                turtle_id=turtle_id,
                dive_id=dive_counters[turtle_id],
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(5, 60)),
            )
            packets_store.append(packet)

    print(f"Initialized with {len(packets_store)} packets")

    # Start auto-generation if enabled
    if AUTO_GENERATE_ENABLED:
        auto_generate_task = asyncio.create_task(auto_generate_packets())
        print(f"Auto-generation enabled (interval: {AUTO_GENERATE_INTERVAL_SECONDS}s)")

    yield

    # Cleanup
    if auto_generate_task:
        auto_generate_task.cancel()
        try:
            await auto_generate_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Mock Satellite API",
    description="Simulates satellite data provider for turtle tracking",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/packets", response_model=PacketResponse)
async def get_packets(
    since: Annotated[
        str | None,
        Query(description="ISO timestamp to filter packets after this time"),
    ] = None,
    turtle_id: Annotated[
        str | None,
        Query(description="Filter by turtle ID"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum packets to return"),
    ] = 50,
) -> PacketResponse:
    """
    Get packets, optionally filtered by timestamp and turtle.

    The `since` parameter is used for incremental polling - only packets
    with timestamps after this value are returned.
    """
    filtered = packets_store

    # Filter by timestamp
    if since:
        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00").replace("+00:00", ""))
        filtered = [
            p for p in filtered
            if datetime.fromisoformat(p["timestamp"].replace("Z", "")) > since_dt
        ]

    # Filter by turtle
    if turtle_id:
        filtered = [p for p in filtered if p["turtle_id"] == turtle_id]

    # Sort by timestamp and limit
    filtered = sorted(filtered, key=lambda p: p["timestamp"])[:limit]

    last_timestamp = filtered[-1]["timestamp"] if filtered else None

    return PacketResponse(
        packets=filtered,
        count=len(filtered),
        last_timestamp=last_timestamp,
    )


@app.post("/packets/generate")
async def generate_packet(
    turtle_id: Annotated[
        str,
        Query(description="Turtle ID for the packet"),
    ] = "TRT-2024-001",
    sample_count: Annotated[
        int,
        Query(ge=10, le=1000, description="Number of samples"),
    ] = 600,
) -> dict:
    """
    Manually generate a new packet for testing.
    """
    if turtle_id not in dive_counters:
        dive_counters[turtle_id] = 0

    dive_counters[turtle_id] += 1

    packet = generate_packet_hex(
        turtle_id=turtle_id,
        dive_id=dive_counters[turtle_id],
        sample_count=sample_count,
    )

    packets_store.append(packet)

    return {
        "message": "Packet generated",
        "packet": packet,
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get statistics about the mock satellite."""
    packets_by_turtle = {}
    for packet in packets_store:
        tid = packet["turtle_id"]
        packets_by_turtle[tid] = packets_by_turtle.get(tid, 0) + 1

    return StatsResponse(
        total_packets=len(packets_store),
        packets_by_turtle=packets_by_turtle,
        auto_generate_enabled=AUTO_GENERATE_ENABLED,
        auto_generate_interval_seconds=AUTO_GENERATE_INTERVAL_SECONDS,
    )


@app.delete("/packets")
async def clear_packets() -> dict:
    """Clear all packets (for testing)."""
    packets_store.clear()
    return {"message": "All packets cleared"}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "packets_count": len(packets_store)}
