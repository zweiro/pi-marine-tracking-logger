"""
Packet Decoder Service

Decodes binary satellite packets into structured dive and sample data.
Based on the format defined in notebooks/packet-reading.ipynb.
"""

import struct
from datetime import datetime, timedelta
from dataclasses import dataclass

# Binary formats (little-endian, no padding)
HEADER_FMT = "<B H H I i i H H"  # 21 bytes
SAMPLE_FMT = "<h H"  # 4 bytes (int16 temp, uint16 pressure)

HEADER_SIZE = struct.calcsize(HEADER_FMT)
SAMPLE_SIZE = struct.calcsize(SAMPLE_FMT)

# GPS epoch: January 6, 1980
GPS_EPOCH = datetime(1980, 1, 6)

# Pressure at sea level (hPa)
SEA_LEVEL_PRESSURE_HPA = 1013


@dataclass
class DiveHeader:
    """Decoded dive header."""

    header_len: int
    dive_id: int
    gps_week: int
    gps_tow_s: int
    latitude: float
    longitude: float
    sample_period_ms: int
    sample_count: int
    timestamp: datetime


@dataclass
class DecodedSample:
    """Decoded sample data."""

    sample_index: int
    timestamp: datetime
    temperature_c: float
    pressure_hpa: int
    depth_m: float


@dataclass
class DecodedPacket:
    """Complete decoded packet."""

    header: DiveHeader
    samples: list[DecodedSample]


class PacketDecoder:
    """
    Decodes binary satellite packets.

    Usage:
        decoder = PacketDecoder()
        packet = decoder.decode_hex(hex_string)
        # packet.header contains dive metadata
        # packet.samples contains all measurements
    """

    @staticmethod
    def gps_to_datetime(gps_week: int, gps_tow_s: int) -> datetime:
        """Convert GPS week and time-of-week to datetime."""
        total_seconds = gps_week * 7 * 24 * 3600 + gps_tow_s
        return GPS_EPOCH + timedelta(seconds=total_seconds)

    @staticmethod
    def pressure_to_depth(pressure_hpa: int) -> float:
        """
        Convert pressure to depth in meters.

        Uses hydrostatic pressure formula:
        depth = (pressure - surface_pressure) / (density * g)

        Simplified: ~10m per 1000 hPa above sea level pressure
        """
        if pressure_hpa <= SEA_LEVEL_PRESSURE_HPA:
            return 0.0
        return round((pressure_hpa - SEA_LEVEL_PRESSURE_HPA) / 100, 2)

    def decode_header(self, data: bytes) -> DiveHeader:
        """Decode the packet header."""
        if len(data) < HEADER_SIZE:
            raise ValueError(
                f"Packet too short for header: {len(data)} bytes, "
                f"expected at least {HEADER_SIZE}"
            )

        values = struct.unpack_from(HEADER_FMT, data, 0)

        (
            header_len,
            dive_id,
            gps_week,
            gps_tow_s,
            lat_raw,
            lon_raw,
            sample_period_ms,
            sample_count,
        ) = values

        # Convert coordinates (stored as 1e7)
        latitude = lat_raw / 1e7
        longitude = lon_raw / 1e7

        # Convert GPS time to datetime
        timestamp = self.gps_to_datetime(gps_week, gps_tow_s)

        return DiveHeader(
            header_len=header_len,
            dive_id=dive_id,
            gps_week=gps_week,
            gps_tow_s=gps_tow_s,
            latitude=latitude,
            longitude=longitude,
            sample_period_ms=sample_period_ms,
            sample_count=sample_count,
            timestamp=timestamp,
        )

    def decode_samples(
        self, data: bytes, header: DiveHeader
    ) -> list[DecodedSample]:
        """Decode all samples from the packet."""
        offset = header.header_len
        expected_size = offset + header.sample_count * SAMPLE_SIZE

        if len(data) < expected_size:
            raise ValueError(
                f"Incomplete packet: {len(data)} bytes, "
                f"expected {expected_size} bytes"
            )

        samples = []
        sample_period_s = header.sample_period_ms / 1000

        for i in range(header.sample_count):
            temp_raw, pressure_hpa = struct.unpack_from(SAMPLE_FMT, data, offset)
            offset += SAMPLE_SIZE

            # Convert temperature (stored as raw * 100)
            temperature_c = temp_raw / 100

            # Calculate depth from pressure
            depth_m = self.pressure_to_depth(pressure_hpa)

            # Calculate sample timestamp
            sample_timestamp = header.timestamp + timedelta(seconds=i * sample_period_s)

            samples.append(
                DecodedSample(
                    sample_index=i,
                    timestamp=sample_timestamp,
                    temperature_c=round(temperature_c, 2),
                    pressure_hpa=pressure_hpa,
                    depth_m=depth_m,
                )
            )

        return samples

    def decode(self, data: bytes) -> DecodedPacket:
        """
        Decode a complete packet from bytes.

        Args:
            data: Raw packet bytes

        Returns:
            DecodedPacket with header and samples
        """
        header = self.decode_header(data)
        samples = self.decode_samples(data, header)
        return DecodedPacket(header=header, samples=samples)

    def decode_hex(self, hex_string: str) -> DecodedPacket:
        """
        Decode a complete packet from hex string.

        Args:
            hex_string: Hex-encoded packet data

        Returns:
            DecodedPacket with header and samples
        """
        data = bytes.fromhex(hex_string.strip())
        return self.decode(data)

    def compute_dive_stats(self, samples: list[DecodedSample]) -> dict:
        """
        Compute statistics from decoded samples.

        Returns dict compatible with DiveStats model.
        """
        if not samples:
            return {
                "sample_count": 0,
                "sample_period_ms": 0,
                "max_depth_m": None,
                "avg_depth_m": None,
                "min_temperature_c": None,
                "max_temperature_c": None,
                "avg_temperature_c": None,
            }

        depths = [s.depth_m for s in samples]
        temps = [s.temperature_c for s in samples]

        return {
            "sample_count": len(samples),
            "sample_period_ms": 1000,  # Will be overridden from header
            "max_depth_m": round(max(depths), 2),
            "avg_depth_m": round(sum(depths) / len(depths), 2),
            "min_temperature_c": round(min(temps), 2),
            "max_temperature_c": round(max(temps), 2),
            "avg_temperature_c": round(sum(temps) / len(temps), 2),
        }
