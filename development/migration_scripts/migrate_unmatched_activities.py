"""
Migration: Add unmatched_activities field to all existing estimates.

Adds an empty unmatched_activities array to every job_item in every estimate
that doesn't already have the field. Safe to run multiple times (idempotent).

Usage:
    cd platform
    source .venv/bin/activate
    python scripts/db/migrate_unmatched_activities.py
"""

import asyncio
import sys
from pathlib import Path

# Allow running from the scripts/db directory or project root.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def migrate() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    # Use the same database reference as database.py (client.db_name)
    db = client.db_name
    collection = db["estimates"]

    # Add unmatched_activities: [] to every job_item that lacks it.
    # The array_filters approach handles nested arrays correctly.
    result = await collection.update_many(
        {"job_items.unmatched_activities": {"$exists": False}},
        {"$set": {"job_items.$[item].unmatched_activities": []}},
        array_filters=[{"item.unmatched_activities": {"$exists": False}}],
    )
    print(f"Modified {result.modified_count} estimate document(s)")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
