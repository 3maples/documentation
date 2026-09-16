"""One-time migration: set industry to 'Landscaping & Hardscape' for existing companies.

SUPERSEDED 2026-09-16. The CompanyIndustry enum dropped "& Hardscape"; the
value this script writes no longer parses. Kept for the record only — do not
run it. The current value is written by
`platform/scripts/migrate_landscaping_industry.py`.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def migrate():
    mongo_client = AsyncIOMotorClient(settings.mongodb_url)
    db = mongo_client.db_name

    result = await db.companies.update_many(
        {"$or": [{"industry": {"$exists": False}}, {"industry": None}]},
        {"$set": {"industry": "Landscaping & Hardscape"}},
    )

    print(f"Updated {result.modified_count} companies with industry='Landscaping & Hardscape'")
    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
