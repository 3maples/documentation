"""
Migration script to convert existing Material.category strings to MaterialCategory ObjectId references.

This script:
1. Finds all unique category strings in existing materials grouped by company
2. Creates MaterialCategory records for each unique string (if not exists)
3. Updates each Material to reference the corresponding MaterialCategory ObjectId
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

from beanie import PydanticObjectId
from database import init_db
from models import Material, MaterialCategory

async def migrate_material_categories():
    """Migrate existing material string categories to MaterialCategory references."""
    await init_db()

    # Get all materials using raw MongoDB to bypass validation
    # This is necessary because the model expects ObjectId but data has strings
    from motor.motor_asyncio import AsyncIOMotorClient
    from config import settings

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name
    materials_collection = db.materials

    all_materials_raw = await materials_collection.find({}).to_list(None)
    print(f"Found {len(all_materials_raw)} materials to migrate")

    # Group by company and category
    company_categories = {}  # {company_id: {category_string: [material_ids]}}
    skipped = 0

    for material_raw in all_materials_raw:
        company_id = str(material_raw.get('company'))
        category = material_raw.get('category')

        # Skip if already migrated (category is ObjectId)
        if isinstance(category, PydanticObjectId) or not isinstance(category, str):
            skipped += 1
            continue

        category_str = str(category).strip()
        if not category_str:
            skipped += 1
            continue

        if company_id not in company_categories:
            company_categories[company_id] = {}
        if category_str not in company_categories[company_id]:
            company_categories[company_id][category_str] = []
        company_categories[company_id][category_str].append(material_raw['_id'])

    print(f"Skipped {skipped} materials (already migrated or invalid category)")

    # Create MaterialCategory for each unique category string
    migrated_count = 0
    for company_id, categories in company_categories.items():
        company_obj_id = PydanticObjectId(company_id)
        print(f"\nProcessing company {company_id}: {len(categories)} unique categories")

        for category_str, material_ids in categories.items():
            # Find or create MaterialCategory
            existing_category = await MaterialCategory.find_one({
                "name": category_str,
                "company": company_obj_id,
            })

            if existing_category:
                category_id = existing_category.id
                print(f"  Found existing category: {category_str}")
            else:
                new_category = MaterialCategory(
                    name=category_str,
                    description=None,
                    company=company_obj_id,
                )
                await new_category.insert()
                category_id = new_category.id
                print(f"  Created category: {category_str}")

            # Update all materials with this category using raw MongoDB
            result = await materials_collection.update_many(
                {"_id": {"$in": material_ids}},
                {"$set": {"category": category_id}}
            )
            migrated_count += result.modified_count
            print(f"    Updated {result.modified_count} materials")

    print(f"\nMigration complete: {migrated_count} materials updated")

if __name__ == "__main__":
    asyncio.run(migrate_material_categories())
