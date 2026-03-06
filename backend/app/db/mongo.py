from functools import lru_cache

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.config import Settings, get_settings


@lru_cache
def get_client(mongo_uri: str) -> AsyncIOMotorClient:
    """Return a cached Motor client for MongoDB."""
    return AsyncIOMotorClient(mongo_uri)


def get_collection(
    settings: Settings = Depends(get_settings),
) -> AsyncIOMotorCollection:
    """Provide the Mongo collection via FastAPI dependency."""
    client = get_client(settings.mongo_uri)
    return client[settings.mongo_db][settings.mongo_collection]


async def init_indexes(settings: Settings) -> None:
    """Ensure required indexes exist."""
    client = get_client(settings.mongo_uri)
    coll = client[settings.mongo_db][settings.mongo_collection]
    await coll.create_index("note_id", unique=True)
    await coll.create_index("owner_id")
