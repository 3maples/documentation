"""
Migration script: Convert estimate labors to activities.

This script:
1. Finds all estimates with job items that have labors but no activities
2. For each labor, creates an activity named "All" with effort = labor quantity
3. Clears the labors list on migrated job items
4. Everything else remains unchanged

Run with:
    cd platform
    source .venv/bin/activate
    python ../documentation/development/migration_scripts/migrate_labours_to_activities.py
"""

import asyncio
import sys
from pathlib import Path

# Add platform directory to path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "platform"))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from models.estimate import Estimate, ActivityItem
from database import init_db


async def migrate_labours_to_activities():
    """Convert labor items to activity items on estimates."""
    print("Starting labor-to-activity migration...")
    print(f"Connecting to MongoDB: {settings.mongodb_url}")

    client = AsyncIOMotorClient(settings.mongodb_url)

    try:
        await init_db()

        print("\nSearching for estimates with labor items...")
        all_estimates = Estimate.find()
        total_count = await all_estimates.count()
        print(f"Total estimates to scan: {total_count}")

        migrated_count = 0
        skipped_count = 0
        error_count = 0
        job_items_migrated = 0

        async for estimate in Estimate.find():
            try:
                estimate_modified = False

                for job_item in estimate.job_items:
                    # Skip job items that already have activities or have no labors
                    if job_item.activities or not job_item.labours:
                        continue

                    # Convert each labor to an activity
                    for labour in job_item.labours:
                        activity = ActivityItem(
                            name="All",
                            role=labour.labour,
                            role_name=labour.name,
                            rate=labour.price,
                            effort=labour.quantity,
                        )
                        job_item.activities.append(activity)

                    # Clear labors
                    job_item.labours = []
                    estimate_modified = True
                    job_items_migrated += 1

                if estimate_modified:
                    await estimate.save()
                    migrated_count += 1
                    print(f"  Migrated {estimate.estimate_id}")
                else:
                    skipped_count += 1

            except Exception as e:
                print(f"  Error migrating {estimate.estimate_id}: {e}")
                error_count += 1

        print("\n" + "=" * 60)
        print("Migration Summary:")
        print(f"  Successfully migrated: {migrated_count} estimates")
        print(f"  Job items converted:   {job_items_migrated}")
        print(f"  Skipped (no changes):  {skipped_count}")
        print(f"  Errors:                {error_count}")
        print(f"  Total scanned:         {total_count}")
        print("=" * 60)

    finally:
        client.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    asyncio.run(migrate_labours_to_activities())
