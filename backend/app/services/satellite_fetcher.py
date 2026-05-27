"""
Satellite Fetcher Service

Fetches packets from the satellite API and stores them in the database.
"""

import logging
from datetime import datetime

import httpx
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.packet_decoder import PacketDecoder

logger = logging.getLogger(__name__)

# Turtle profile mapping for auto-creation
TURTLE_PROFILES = {
    "HONU": {"name": "Honu", "species": "green"},
    "CARI": {"name": "Caribe", "species": "hawksbill"},
    "MEDI": {"name": "Mediterraneo", "species": "loggerhead"},
    "GALA": {"name": "Darwin", "species": "green"},
    "AUST": {"name": "Coral", "species": "flatback"},
}


class SatelliteFetcher:
    """
    Fetches and processes satellite packets.

    Handles:
    - Fetching new packets from satellite API
    - Decoding packets
    - Creating dive and sample records
    - Tracking last fetch timestamp
    """

    def __init__(self, db: AsyncIOMotorDatabase, satellite_api_url: str):
        self.db = db
        self.satellite_api_url = satellite_api_url.rstrip("/")
        self.decoder = PacketDecoder()
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def get_last_fetch_timestamp(self) -> str | None:
        """
        Get the last fetch timestamp from the database.

        Stores sync state in a dedicated collection.
        """
        state = await self.db.sync_state.find_one({"_id": "satellite_sync"})
        if state:
            return state.get("last_timestamp")
        return None

    async def update_last_fetch_timestamp(self, timestamp: str):
        """Update the last fetch timestamp."""
        await self.db.sync_state.update_one(
            {"_id": "satellite_sync"},
            {"$set": {"last_timestamp": timestamp, "updated_at": datetime.utcnow()}},
            upsert=True,
        )

    async def fetch_packets(self, since: str | None = None) -> list[dict]:
        """
        Fetch packets from the satellite API.

        Args:
            since: ISO timestamp to fetch packets after

        Returns:
            List of packet dictionaries
        """
        url = f"{self.satellite_api_url}/packets"
        params = {}
        if since:
            params["since"] = since

        try:
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("packets", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch packets: {e}")
            raise

    async def ensure_turtle_exists(self, turtle_id: str) -> bool:
        """
        Check if turtle exists, create with profile data if not.

        Returns True if turtle exists or was created.
        """
        turtle = await self.db.turtles.find_one({"turtle_id": turtle_id})
        if turtle:
            return True

        # Extract prefix to get profile (e.g., "HONU-001" -> "HONU")
        prefix = turtle_id.split("-")[0] if "-" in turtle_id else turtle_id
        profile = TURTLE_PROFILES.get(prefix, {"name": turtle_id, "species": "green"})

        logger.info(f"Creating turtle: {turtle_id} ({profile['name']})")
        await self.db.turtles.insert_one({
            "turtle_id": turtle_id,
            "name": profile["name"],
            "species": profile["species"],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        return True

    async def process_packet(self, packet_data: dict) -> dict | None:
        """
        Process a single packet: decode and store in database.

        Args:
            packet_data: Raw packet from satellite API with turtle_id, data, timestamp

        Returns:
            Created dive document or None if skipped/failed
        """
        turtle_id = packet_data.get("turtle_id")
        hex_data = packet_data.get("data")
        packet_timestamp = packet_data.get("timestamp")

        if not turtle_id or not hex_data:
            logger.warning(f"Invalid packet data: missing turtle_id or data")
            return None

        try:
            # Decode the packet
            decoded = self.decoder.decode_hex(hex_data)
            header = decoded.header
            samples = decoded.samples

            # Check if dive already exists
            existing = await self.db.dives.find_one({
                "turtle_id": turtle_id,
                "dive_id": header.dive_id,
            })
            if existing:
                logger.debug(
                    f"Dive {header.dive_id} for {turtle_id} already exists, skipping"
                )
                return None

            # Ensure turtle exists
            await self.ensure_turtle_exists(turtle_id)

            # Compute statistics
            stats = self.decoder.compute_dive_stats(samples)
            stats["sample_period_ms"] = header.sample_period_ms

            # Calculate dive duration
            duration_s = len(samples) * header.sample_period_ms // 1000
            end_time = header.timestamp

            # For end_time, use last sample timestamp if available
            if samples:
                end_time = samples[-1].timestamp

            # Create dive document
            dive_doc = {
                "turtle_id": turtle_id,
                "dive_id": header.dive_id,
                "start_time": header.timestamp,
                "end_time": end_time,
                "duration_s": duration_s,
                "start_location": {
                    "type": "Point",
                    "coordinates": [header.longitude, header.latitude],
                },
                "end_location": None,
                "stats": stats,
                "packet_metadata": {
                    "gps_week": header.gps_week,
                    "gps_tow_s": header.gps_tow_s,
                    "header_len": header.header_len,
                },
                "created_at": datetime.utcnow(),
            }

            # Insert dive
            result = await self.db.dives.insert_one(dive_doc)
            dive_id = result.inserted_id

            # Prepare sample documents for bulk insert
            sample_docs = [
                {
                    "timestamp": sample.timestamp,
                    "metadata": {
                        "dive_id": dive_id,
                        "turtle_id": turtle_id,
                    },
                    "sample_index": sample.sample_index,
                    "depth_m": sample.depth_m,
                    "temperature_c": sample.temperature_c,
                    "pressure_hpa": sample.pressure_hpa,
                }
                for sample in samples
            ]

            # Bulk insert samples
            if sample_docs:
                await self.db.samples.insert_many(sample_docs, ordered=False)

            logger.info(
                f"Processed dive {header.dive_id} for {turtle_id}: "
                f"{len(samples)} samples, max depth {stats.get('max_depth_m')}m"
            )

            dive_doc["_id"] = dive_id
            return dive_doc

        except Exception as e:
            logger.error(f"Failed to process packet for {turtle_id}: {e}")
            return None

    async def fetch_and_process(self) -> dict:
        """
        Main method: fetch new packets and process them.

        Returns:
            Summary of processing results
        """
        # Get last timestamp
        last_timestamp = await self.get_last_fetch_timestamp()
        logger.info(f"Fetching packets since: {last_timestamp or 'beginning'}")

        # Fetch packets
        try:
            packets = await self.fetch_packets(since=last_timestamp)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "packets_fetched": 0,
                "dives_created": 0,
            }

        if not packets:
            logger.info("No new packets to process")
            return {
                "success": True,
                "packets_fetched": 0,
                "dives_created": 0,
            }

        logger.info(f"Fetched {len(packets)} packets")

        # Process each packet
        dives_created = 0
        latest_timestamp = last_timestamp

        for packet in packets:
            result = await self.process_packet(packet)
            if result:
                dives_created += 1

            # Track latest timestamp
            packet_ts = packet.get("timestamp")
            if packet_ts:
                if not latest_timestamp or packet_ts > latest_timestamp:
                    latest_timestamp = packet_ts

        # Update last fetch timestamp
        if latest_timestamp and latest_timestamp != last_timestamp:
            await self.update_last_fetch_timestamp(latest_timestamp)

        return {
            "success": True,
            "packets_fetched": len(packets),
            "dives_created": dives_created,
            "last_timestamp": latest_timestamp,
        }
