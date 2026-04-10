"""
Migration script: Move overhead allocation from estimate-level to job-item-level.

This script:
1. Finds all estimates with estimate-level overhead_allocation > 0
2. Distributes overhead to all job items in each estimate
3. Recalculates sub_totals with compound calculation (profit + overhead)
4. Updates grand_total to sum of job item sub_totals
5. Sets estimate.overhead_allocation to 0.0

Run with:
    cd platform
    source .venv/bin/activate
    python scripts/migrate_overhead_to_job_items.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from models.estimate import Estimate
from database import init_db


async def migrate_overhead():
    """Migrate estimate-level overhead to job items."""
    print("Starting overhead allocation migration...")
    print(f"Connecting to MongoDB: {settings.mongodb_url}")

    client = AsyncIOMotorClient(settings.mongodb_url)

    try:
        # Initialize Beanie
        await init_db()

        # Find estimates with overhead
        print("\nSearching for estimates with overhead_allocation > 0...")
        query = Estimate.find(Estimate.overhead_allocation > 0)
        
        estimates_count = await query.count()
        print(f"Found {estimates_count} estimates with overhead allocation")

        if estimates_count == 0:
            print("No estimates to migrate. Exiting.")
            return

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        async for estimate in query:
            try:
                if not estimate.job_items:
                    print(f"⚠️  Skip {estimate.estimate_id}: no job items")
                    skipped_count += 1
                    continue

                overhead = estimate.overhead_allocation
                print(f"\n📋 Processing {estimate.estimate_id} (overhead: {overhead}%)")

                # Distribute overhead to all job items
                for idx, job_item in enumerate(estimate.job_items):
                    # Set overhead allocation on job item
                    job_item.overhead_allocation = overhead

                    # Recalculate sub_total with compound calculation
                    # First, we need to reverse engineer the base from current sub_total
                    # Current: base * (1 + profit/100) = sub_total
                    # So: base = sub_total / (1 + profit/100)

                    profit_margin = job_item.profit_margin or 0.0
                    current_sub_total = job_item.sub_total or 0.0

                    if current_sub_total > 0:
                        # Calculate base from current sub_total (which has profit applied)
                        base = current_sub_total / (1 + profit_margin / 100.0) if profit_margin > 0 else current_sub_total
                    else:
                        # Calculate base from materials, equipment, labour
                        base = 0.0
                        for material in job_item.materials:
                            base += material.quantity * material.price
                        for equipment in job_item.equipments:
                            base += equipment.quantity * equipment.price
                        for labour in job_item.labours:
                            base += labour.quantity * labour.price

                    # Apply compound calculation: base → +profit → +overhead
                    with_profit = base * (1 + profit_margin / 100.0)
                    with_overhead = with_profit * (1 + overhead / 100.0)
                    new_sub_total = round(with_overhead, 2)

                    print(f"  Item {idx + 1}: base=${base:.2f} → profit({profit_margin}%) → overhead({overhead}%) → ${new_sub_total:.2f}")

                    job_item.sub_total = new_sub_total

                # Update grand_total (sum of job item sub_totals)
                new_grand_total = round(sum(item.sub_total for item in estimate.job_items), 2)
                old_grand_total = estimate.grand_total

                print(f"  Grand total: ${old_grand_total:.2f} → ${new_grand_total:.2f}")

                estimate.grand_total = new_grand_total

                # Clear estimate-level overhead
                estimate.overhead_allocation = 0.0

                # Save changes
                await estimate.save()
                migrated_count += 1
                print(f"✅ Migrated {estimate.estimate_id}")

            except Exception as e:
                print(f"❌ Error migrating {estimate.estimate_id}: {e}")
                error_count += 1

        print("\n" + "="*60)
        print("Migration Summary:")
        print(f"  ✅ Successfully migrated: {migrated_count}")
        print(f"  ⚠️  Skipped (no job items): {skipped_count}")
        print(f"  ❌ Errors: {error_count}")
        print(f"  📊 Total processed: {len(estimates)}")
        print("="*60)

    finally:
        client.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    asyncio.run(migrate_overhead())
