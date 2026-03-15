"""
Database Connection Module

Provides async MongoDB connection using Motor driver with
connection pooling and dependency injection support.
"""

from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager
from pymongo.errors import CollectionInvalid

from app.config import get_settings


class Database:
    """
    MongoDB database connection manager.

    Handles connection lifecycle and provides access to the database instance.
    """

    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None

    @classmethod
    async def connect(cls) -> None:
        """
        Establish connection to MongoDB.

        Creates a new Motor client with connection pooling.
        Should be called during application startup.
        """
        settings = get_settings()
        cls.client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000,
        )
        cls.database = cls.client[settings.mongodb_database]

        # Verify connection
        await cls.client.admin.command("ping")

        # Initialize collections and indexes
        await cls._init_collections()

    @classmethod
    async def _init_collections(cls) -> None:
        """
        Initialize collections with proper configuration.

        Creates time-series collection for samples and sets up indexes.
        """
        if cls.database is None:
            return

        # Create time-series collection for samples
        await cls._create_samples_timeseries()

        # Create indexes
        await cls._create_indexes()

    @classmethod
    async def _create_samples_timeseries(cls) -> None:
        """
        Create the samples time-series collection if it doesn't exist.
        """
        if cls.database is None:
            return

        try:
            await cls.database.create_collection(
                "samples",
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "metadata",
                    "granularity": "seconds",
                },
            )
        except CollectionInvalid:
            # Collection already exists
            pass

    @classmethod
    async def _create_indexes(cls) -> None:
        """
        Create indexes for all collections.
        """
        if cls.database is None:
            return

        # Turtles indexes
        await cls.database.turtles.create_index("turtle_id", unique=True)
        await cls.database.turtles.create_index("status")
        await cls.database.turtles.create_index([("species", 1), ("status", 1)])

        # Dives indexes
        await cls.database.dives.create_index(
            [("turtle_id", 1), ("start_time", -1)]
        )
        await cls.database.dives.create_index([("start_time", -1)])
        await cls.database.dives.create_index(
            [("turtle_id", 1), ("dive_id", 1)], unique=True
        )
        await cls.database.dives.create_index(
            [("start_location", "2dsphere")]
        )

        # Samples indexes (time-series auto-creates on timeField + metaField)
        await cls.database.samples.create_index(
            [("metadata.dive_id", 1), ("timestamp", 1)]
        )
        await cls.database.samples.create_index(
            [("metadata.turtle_id", 1), ("timestamp", -1)]
        )

    @classmethod
    async def disconnect(cls) -> None:
        """
        Close MongoDB connection.

        Should be called during application shutdown.
        """
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.database = None

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get the database instance.

        Returns:
            AsyncIOMotorDatabase: The MongoDB database instance.

        Raises:
            RuntimeError: If database is not connected.
        """
        if cls.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.database


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Dependency injection function for database access.

    Use this with FastAPI's Depends() to inject the database
    into route handlers.

    Yields:
        AsyncIOMotorDatabase: The MongoDB database instance.

    Example:
        ```python
        @router.get("/items")
        async def get_items(db: AsyncIOMotorDatabase = Depends(get_database)):
            items = await db.items.find().to_list(100)
            return items
        ```
    """
    yield Database.get_database()


@asynccontextmanager
async def lifespan_manager():
    """
    Async context manager for database lifecycle.

    Connects to database on enter and disconnects on exit.
    """
    await Database.connect()
    try:
        yield
    finally:
        await Database.disconnect()
