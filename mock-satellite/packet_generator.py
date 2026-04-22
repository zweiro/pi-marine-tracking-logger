"""
Satellite Packet Generator

Generates simulated dive packets matching the binary format
defined in the packet-reading notebook.
"""

import struct
import random
import math
from datetime import datetime, timedelta
from dataclasses import dataclass

# Binary formats (little-endian)
HEADER_FMT = "<B H H I i i H H"  # 21 bytes
SAMPLE_FMT = "<h H"  # 4 bytes

# GPS epoch: January 6, 1980
GPS_EPOCH = datetime(1980, 1, 6)


@dataclass
class DiveConfig:
    """Configuration for generating a simulated dive."""

    turtle_id: str
    dive_id: int
    latitude: float = 46.2044  # Default: near Geneva
    longitude: float = 6.1432
    sample_count: int = 600
    sample_period_ms: int = 1000
    max_depth_m: float = 50.0
    surface_temp_c: float = 22.0
    deep_temp_c: float = 15.0


def datetime_to_gps(dt: datetime) -> tuple[int, int]:
    """Convert datetime to GPS week and time of week."""
    delta = dt - GPS_EPOCH
    total_seconds = delta.total_seconds()
    gps_week = int(total_seconds // (7 * 24 * 3600))
    gps_tow_s = int(total_seconds % (7 * 24 * 3600))
    return gps_week, gps_tow_s


def generate_dive_profile(config: DiveConfig) -> list[dict]:
    """
    Generate a realistic dive profile with temperature and pressure.

    Simulates:
    - Descent, bottom time, ascent phases
    - Temperature decrease with depth
    - Pressure increase with depth
    """
    samples = []
    total_time = config.sample_count * config.sample_period_ms / 1000

    for i in range(config.sample_count):
        t = i / config.sample_count  # Normalized time [0, 1]

        # Depth profile: sine-like curve with descent/ascent
        # Starts at surface, goes down, stays, comes back up
        if t < 0.15:
            # Descent phase
            depth_ratio = t / 0.15
        elif t < 0.85:
            # Bottom phase with small variations
            depth_ratio = 1.0 + 0.1 * math.sin(t * 20)
        else:
            # Ascent phase
            depth_ratio = (1.0 - t) / 0.15

        depth_ratio = max(0, min(1, depth_ratio))
        depth_m = depth_ratio * config.max_depth_m

        # Add some noise
        depth_m += random.gauss(0, 0.5)
        depth_m = max(0, depth_m)

        # Temperature decreases with depth (thermocline simulation)
        temp_c = config.surface_temp_c - (config.surface_temp_c - config.deep_temp_c) * depth_ratio
        temp_c += random.gauss(0, 0.2)

        # Convert to raw values
        # Pressure: surface = 1013 hPa, +100 hPa per 10m depth
        pressure_hpa = int(1013 + depth_m * 10)
        temperature_raw = int(temp_c * 100)

        samples.append({
            "index": i,
            "depth_m": round(depth_m, 2),
            "temperature_c": round(temp_c, 2),
            "temperature_raw": temperature_raw,
            "pressure_hpa": pressure_hpa,
        })

    return samples


def encode_packet(config: DiveConfig, timestamp: datetime) -> bytes:
    """
    Encode a dive packet in binary format.

    Returns the complete packet as bytes.
    """
    gps_week, gps_tow_s = datetime_to_gps(timestamp)

    # Convert coordinates to raw format (1e7)
    lat_raw = int(config.latitude * 1e7)
    lon_raw = int(config.longitude * 1e7)

    # Encode header
    header = struct.pack(
        HEADER_FMT,
        21,  # header_len
        config.dive_id,
        gps_week,
        gps_tow_s,
        lat_raw,
        lon_raw,
        config.sample_period_ms,
        config.sample_count,
    )

    # Generate and encode samples
    samples = generate_dive_profile(config)
    sample_bytes = b""
    for sample in samples:
        sample_bytes += struct.pack(
            SAMPLE_FMT,
            sample["temperature_raw"],
            sample["pressure_hpa"],
        )

    return header + sample_bytes


def generate_packet_hex(
    turtle_id: str,
    dive_id: int,
    timestamp: datetime | None = None,
    **kwargs
) -> dict:
    """
    Generate a complete packet and return it with metadata.

    Returns:
        dict with turtle_id, dive_id, timestamp, and hex-encoded data
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    config = DiveConfig(
        turtle_id=turtle_id,
        dive_id=dive_id,
        **kwargs
    )

    packet_bytes = encode_packet(config, timestamp)

    return {
        "turtle_id": turtle_id,
        "dive_id": dive_id,
        "timestamp": timestamp.isoformat() + "Z",
        "data": packet_bytes.hex(),
        "sample_count": config.sample_count,
    }
