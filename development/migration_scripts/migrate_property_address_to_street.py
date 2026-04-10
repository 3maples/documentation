"""
Migration: rename Property.address -> Property.street

Run BEFORE deploying the new application code that expects the `street` field.
This script is idempotent — documents already migrated (have `street`, no `address`)
are skipped.
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database import init_db
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def migrate():
    print("Connecting to database...")
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name
    collection = db["properties"]

    result = await collection.update_many(
        {"address": {"$exists": True}},
        [
            {"$set": {"street": "$address"}},
            {"$unset": "address"},
        ],
    )

    print(f"Migrated {result.modified_count} property document(s): address -> street")


if __name__ == "__main__":
    asyncio.run(migrate())
