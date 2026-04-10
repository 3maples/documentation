import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def migrate():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name

    equipment_key_map = {}
    labour_key_map = {}

    async for doc in db.equipments.find({"key": {"$exists": True}}):
        key = doc.get("key")
        if key:
            equipment_key_map[key] = str(doc["_id"])

    async for doc in db.labours.find({"key": {"$exists": True}}):
        key = doc.get("key")
        if key:
            labour_key_map[key] = str(doc["_id"])

    estimates_updated = 0
    async for est in db.estimates.find({}):
        job_items = est.get("job_items", [])
        changed = False

        for item in job_items:
            for e in item.get("equipments", []):
                current = e.get("equipment")
                if current in equipment_key_map:
                    e["equipment"] = equipment_key_map[current]
                    changed = True
            for l in item.get("labours", []):
                current = l.get("labour")
                if current in labour_key_map:
                    l["labour"] = labour_key_map[current]
                    changed = True

        if changed:
            await db.estimates.update_one(
                {"_id": est["_id"]},
                {"$set": {"job_items": job_items}}
            )
            estimates_updated += 1

    equipment_result = await db.equipments.update_many(
        {"key": {"$exists": True}},
        {"$unset": {"key": ""}}
    )
    labour_result = await db.labours.update_many(
        {"key": {"$exists": True}},
        {"$unset": {"key": ""}}
    )

    client.close()

    print(f"Updated estimates: {estimates_updated}")
    print(f"Removed equipment keys: {equipment_result.modified_count}")
    print(f"Removed labour keys: {labour_result.modified_count}")


if __name__ == "__main__":
    asyncio.run(migrate())
