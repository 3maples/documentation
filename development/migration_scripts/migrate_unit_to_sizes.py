"""
One-time migration script: copy material.unit → material.sizes[i].unit for all documents,
then unset the top-level unit field.

Usage:
    cd platform
    source .venv/bin/activate
    python migrate_unit_to_sizes.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def migrate():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name
    collection = db["materials"]

    # Find all materials that have a top-level unit set
    cursor = collection.find({"unit": {"$exists": True, "$ne": None}})
    updated_count = 0
    skipped_count = 0

    async for doc in cursor:
        top_level_unit = doc.get("unit")
        if not top_level_unit:
            skipped_count += 1
            continue

        sizes = doc.get("sizes", [])
        # For each size that doesn't already have a unit, copy from top-level
        updated_sizes = []
        for size in sizes:
            if not size.get("unit"):
                size = {**size, "unit": top_level_unit}
            updated_sizes.append(size)

        await collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {"sizes": updated_sizes},
                "$unset": {"unit": ""},
            }
        )
        updated_count += 1

    print(f"Migration complete: {updated_count} materials updated, {skipped_count} skipped.")
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
