"""
Migration script: Replace all labours for all companies from default_labours.csv.

For each company:
  - Deletes all existing labours
  - Inserts fresh labours from the default template CSV

Usage:
    cd platform
    source .venv/bin/activate
    python scripts/db/migrate_labours.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database import init_db
from models import Company, Labour
from services.company_bootstrap import bootstrap_company_labours


async def migrate():
    print("Initializing database...")
    await init_db()
    print("Database initialized.\n")

    companies = await Company.find_all().to_list()
    if not companies:
        print("No companies found in the database.")
        return

    print(f"Found {len(companies)} company(ies). Replacing labours...\n")

    total = 0
    for company in companies:
        deleted = await Labour.find(Labour.company == company.id).delete()
        deleted_count = deleted.deleted_count if deleted else 0
        print(f"  {company.name}: deleted {deleted_count} existing labour(s)")

        count = await bootstrap_company_labours(company.id)
        print(f"  {company.name}: inserted {count} labour(s)")
        total += count

    print(f"\nDone. {total} total labour record(s) inserted across {len(companies)} company(ies).")


if __name__ == "__main__":
    asyncio.run(migrate())
