"""
Migration: rename 'category' field to 'division' in all Estimate documents.
Run this once against the database after deploying the code change.
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import settings


async def migrate():
    print(f"Connecting to MongoDB at {settings.mongodb_url}")
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client["db_name"]
    collection = db.estimates

    count = await collection.count_documents({"category": {"$exists": True}})
    print(f"Found {count} estimate documents with 'category' field")

    if count > 0:
        result = await collection.update_many(
            {"category": {"$exists": True}},
            {"$rename": {"category": "division"}}
        )
        print(f"Renamed 'category' to 'division' in {result.modified_count} documents.")
    else:
        print("No documents to update.")

    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
