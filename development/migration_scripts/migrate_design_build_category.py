import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Add platform directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import settings

async def migrate_category():
    print(f"Connecting to MongoDB at {settings.mongodb_url}")
    client = AsyncIOMotorClient(settings.mongodb_url)
    # Using 'db_name' as found from list_database_names()
    db = client['db_name']
    collection = db.estimates

    old_value = "Design & Build"
    new_value = "Design/Build"

    # Count how many records need update
    count = await collection.count_documents({"division": old_value})
    print(f"Found {count} estimates with category '{old_value}'")

    if count > 0:
        result = await collection.update_many(
            {"division": old_value},
            {"$set": {"division": new_value}}
        )
        print(f"Updated {result.modified_count} records.")
    else:
        print("No records to update.")

    # Also check if there are any "Design / Build" (with spaces) from my previous thought/plan
    count_spaced = await collection.count_documents({"division": "Design / Build"})
    if count_spaced > 0:
        print(f"Found {count_spaced} estimates with category 'Design / Build' (with spaces)")
        result = await collection.update_many(
            {"division": "Design / Build"},
            {"$set": {"division": new_value}}
        )
        print(f"Updated {result.modified_count} additional records.")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_category())
