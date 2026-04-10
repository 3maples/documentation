import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


def _build_default_size(doc: dict) -> dict:
    unit = (doc.get("unit") or "").strip()
    size_label = f"1 {unit}" if unit else "default"
    price = doc.get("price")
    if price is None:
        price = doc.get("cost")
    normalized_price = price if price is not None else 0
    return {"size": size_label, "price": normalized_price, "cost": normalized_price}


async def migrate_materials():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name
    materials = db.materials

    total = 0
    updated = 0

    async for doc in materials.find({}):
        total += 1
        sizes = doc.get("sizes")
        needs_sizes = not sizes or not isinstance(sizes, list) or len(sizes) == 0
        normalized_sizes = []
        sizes_changed = False
        if isinstance(sizes, list):
            for size_row in sizes:
                if not isinstance(size_row, dict):
                    continue
                size_label = (size_row.get("size") or "").strip() or "default"
                price = size_row.get("price")
                if price is None:
                    price = size_row.get("cost")
                normalized_price = price if price is not None else 0
                cost = size_row.get("cost")
                normalized_cost = cost if cost is not None else normalized_price
                normalized_entry = {"size": size_label, "price": normalized_price, "cost": normalized_cost}
                normalized_sizes.append(normalized_entry)
                if normalized_entry != size_row:
                    sizes_changed = True

        update = {}
        unset = {}

        if needs_sizes:
            update["sizes"] = [_build_default_size(doc)]
        elif sizes_changed:
            update["sizes"] = normalized_sizes

        if "cost" in doc:
            unset["cost"] = ""
        if "retail" in doc:
            unset["retail"] = ""
        if "key" in doc:
            unset["key"] = ""
        if "subcategory" in doc:
            unset["subcategory"] = ""

        if update or unset:
            await materials.update_one(
                {"_id": doc["_id"]},
                {"$set": update, "$unset": unset} if unset else {"$set": update},
            )
            updated += 1

    client.close()
    print(f"Migrated materials: {updated}/{total} updated")


if __name__ == "__main__":
    asyncio.run(migrate_materials())
