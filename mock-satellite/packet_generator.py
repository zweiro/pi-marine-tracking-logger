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
    latitude: float = 21.4691  # Default: Hawaiian coast
    longitude: float = -157.9847
    sample_count: int = 600
    sample_period_ms: int = 1000
    max_depth_m: float = 50.0
    surface_temp_c: float = 26.0
    deep_temp_c: float = 18.0


# Realistic turtle profiles with coastal locations where sea turtles are found
TURTLE_PROFILES = {
    "HONU-001": {  # Green sea turtle - Hawaii
        "name": "Honu",
        "species": "green",
        "base_lat": 21.4691,
        "base_lon": -157.9847,
        "max_depth_range": (15, 40),
        "surface_temp_range": (24, 27),
        "deep_temp_range": (18, 22),
    },
    "CARI-002": {  # Hawksbill - Caribbean
        "name": "Caribe",
        "species": "hawksbill",
        "base_lat": 18.2208,
        "base_lon": -66.5901,
        "max_depth_range": (20, 50),
        "surface_temp_range": (26, 29),
        "deep_temp_range": (20, 24),
    },
    "MEDI-003": {  # Loggerhead - Mediterranean
        "name": "Mediterraneo",
        "species": "loggerhead",
        "base_lat": 36.7525,
        "base_lon": 14.5147,
        "max_depth_range": (30, 80),
        "surface_temp_range": (22, 26),
        "deep_temp_range": (14, 18),
    },
    "GALA-004": {  # Green turtle - Galapagos
        "name": "Darwin",
        "species": "green",
        "base_lat": -0.9538,
        "base_lon": -90.9656,
        "max_depth_range": (10, 35),
        "surface_temp_range": (21, 25),
        "deep_temp_range": (16, 20),
    },
    "AUST-005": {  # Flatback - Australia Great Barrier Reef
        "name": "Coral",
        "species": "flatback",
        "base_lat": -16.9186,
        "base_lon": 145.7781,
        "max_depth_range": (20, 60),
        "surface_temp_range": (25, 29),
        "deep_temp_range": (19, 23),
    },
}


def get_turtle_dive_config(turtle_id: str, dive_id: int) -> DiveConfig:
    """Generate dive config based on turtle profile with realistic variations."""
    profile = TURTLE_PROFILES.get(turtle_id)

    if profile:
        # Add small random offset to position (turtles move around)
        lat = profile["base_lat"] + random.uniform(-0.05, 0.05)
        lon = profile["base_lon"] + random.uniform(-0.05, 0.05)
        max_depth = random.uniform(*profile["max_depth_range"])
        surface_temp = random.uniform(*profile["surface_temp_range"])
        deep_temp = random.uniform(*profile["deep_temp_range"])
        sample_count = random.randint(200, 500)
    else:
        # Fallback defaults
        lat = 21.4691 + random.uniform(-0.05, 0.05)
        lon = -157.9847 + random.uniform(-0.05, 0.05)
        max_depth = random.uniform(20, 50)
        surface_temp = random.uniform(24, 27)
        deep_temp = random.uniform(18, 22)
        sample_count = random.randint(200, 500)

    return DiveConfig(
        turtle_id=turtle_id,
        dive_id=dive_id,
        latitude=lat,
        longitude=lon,
        sample_count=sample_count,
        max_depth_m=max_depth,
        surface_temp_c=surface_temp,
        deep_temp_c=deep_temp,
    )


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
        # Pressure: surface = 1013 hPa, +100 hPa per 1m depth (water pressure)
        pressure_hpa = int(1013 + depth_m * 100)
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
    use_profile: bool = True,
    **kwargs
) -> dict:
    """
    Generate a complete packet and return it with metadata.

    Args:
        turtle_id: ID of the turtle
        dive_id: Dive number
        timestamp: Optional timestamp (defaults to now)
        use_profile: Use turtle profile for realistic data (default True)
        **kwargs: Override specific config values

    Returns:
        dict with turtle_id, dive_id, timestamp, and hex-encoded data
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    # Use profile-based config if available and no overrides provided
    if use_profile and not kwargs and turtle_id in TURTLE_PROFILES:
        config = get_turtle_dive_config(turtle_id, dive_id)
    else:
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
