"""
Migration script to convert existing Material.unit strings to MaterialUnit ObjectId references.

This script:
1. Finds all unique unit strings in existing materials grouped by company
2. Creates MaterialUnit records for each unique string (if not exists)
3. Updates each Material to reference the corresponding MaterialUnit ObjectId
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

from beanie import PydanticObjectId
from database import init_db
from models import MaterialUnit


async def migrate_material_units():
    """Migrate existing material string units to MaterialUnit references."""
    await init_db()

    from motor.motor_asyncio import AsyncIOMotorClient
    from config import settings

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name
    materials_collection = db.materials

    all_materials_raw = await materials_collection.find({}).to_list(None)
    print(f"Found {len(all_materials_raw)} materials to migrate")

    company_units = {}  # {company_id: {unit_string: [material_ids]}}
    skipped = 0

    for material_raw in all_materials_raw:
        company_id = str(material_raw.get('company'))
        unit = material_raw.get('unit')

        # Skip if already migrated (unit is ObjectId)
        if isinstance(unit, PydanticObjectId) or not isinstance(unit, str):
            skipped += 1
            continue

        unit_str = str(unit).strip()
        if not unit_str:
            skipped += 1
            continue

        if company_id not in company_units:
            company_units[company_id] = {}
        if unit_str not in company_units[company_id]:
            company_units[company_id][unit_str] = []
        company_units[company_id][unit_str].append(material_raw['_id'])

    print(f"Skipped {skipped} materials (already migrated or invalid unit)")

    migrated_count = 0
    for company_id, units in company_units.items():
        company_obj_id = PydanticObjectId(company_id)
        print(f"\nProcessing company {company_id}: {len(units)} unique units")

        for unit_str, material_ids in units.items():
            existing_unit = await MaterialUnit.find_one({
                "name": unit_str,
                "company": company_obj_id,
            })

            if existing_unit:
                unit_id = existing_unit.id
                print(f"  Found existing unit: {unit_str}")
            else:
                new_unit = MaterialUnit(
                    name=unit_str,
                    description=None,
                    company=company_obj_id,
                )
                await new_unit.insert()
                unit_id = new_unit.id
                print(f"  Created unit: {unit_str}")

            result = await materials_collection.update_many(
                {"_id": {"$in": material_ids}},
                {"$set": {"unit": unit_id}}
            )
            migrated_count += result.modified_count
            print(f"    Updated {result.modified_count} materials")

    print(f"\nMigration complete: {migrated_count} materials updated")


if __name__ == "__main__":
    asyncio.run(migrate_material_units())
