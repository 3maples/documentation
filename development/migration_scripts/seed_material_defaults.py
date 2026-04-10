"""
One-off script to seed default Material Categories and Material Units
for all existing companies, excluding the specified company ID.

Usage (from platform/ directory, with venv activated):
    python scripts/seed_material_defaults.py
"""

import asyncio
import sys
from pathlib import Path

# Allow imports from platform/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import init_db
from models import Company
from beanie import PydanticObjectId
from services.material_category_bootstrap import bootstrap_company_material_categories
from services.material_unit_bootstrap import bootstrap_company_material_units

EXCLUDED_COMPANY_ID = "69642e3c585ba3375df8fe2b"


async def main():
    await init_db()

    companies = await Company.find_all().to_list()
    excluded_id = PydanticObjectId(EXCLUDED_COMPANY_ID)

    targets = [c for c in companies if c.id != excluded_id]

    print(f"Found {len(companies)} companies. Excluding 1. Processing {len(targets)}.\n")

    for company in targets:
        print(f"  Company: {company.id} — {getattr(company, 'name', '(no name)')}")
        try:
            cat_count = await bootstrap_company_material_categories(company.id)
            unit_count = await bootstrap_company_material_units(company.id)
            print(f"    ✓ {cat_count} categories, {unit_count} units")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
