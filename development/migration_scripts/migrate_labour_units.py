"""Migration script: Convert labour unit strings to LabourUnit enum values.

Maps known legacy values to the new enum:
  hour, hourly, hr  → Hourly
  day, daily        → Daily
  each, ea          → Each

Unknown values default to 'Hourly' with a warning printed to stdout.

Usage:
    cd platform
    source .venv/bin/activate
    python scripts/db/migrate_labour_units.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Mapping of legacy unit strings (lowercased) to canonical enum values
UNIT_MAP: dict[str, str] = {
    "hour": "Hourly",
    "hourly": "Hourly",
    "hr": "Hourly",
    "day": "Daily",
    "daily": "Daily",
    "each": "Each",
    "ea": "Each",
}

VALID_VALUES = {"Hourly", "Daily", "Each"}


async def migrate():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name

    total = 0
    updated = 0
    skipped = 0
    warnings: list[str] = []

    async for doc in db.labours.find({}):
        total += 1
        raw_unit = doc.get("unit", "")

        # Already a valid enum value — skip
        if raw_unit in VALID_VALUES:
            skipped += 1
            continue

        normalized = UNIT_MAP.get(raw_unit.strip().lower() if isinstance(raw_unit, str) else "")
        if normalized is None:
            normalized = "Hourly"
            warnings.append(
                f"  ⚠ Labour '{doc.get('name', '?')}' (id={doc['_id']}): "
                f"unknown unit '{raw_unit}' → defaulted to 'Hourly'"
            )

        await db.labours.update_one(
            {"_id": doc["_id"]},
            {"$set": {"unit": normalized}},
        )
        updated += 1

    client.close()

    print(f"Migration complete: {total} documents scanned")
    print(f"  Updated: {updated}")
    print(f"  Already valid: {skipped}")
    if warnings:
        print(f"  Warnings ({len(warnings)}):")
        for w in warnings:
            print(w)


if __name__ == "__main__":
    asyncio.run(migrate())
