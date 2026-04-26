"""Backfill: seed default rate cards for every existing company.

For each company in the database, runs ``bootstrap_company_rate_cards``,
which creates any missing default rate cards by name. Existing cards are
left untouched, so this is safe to re-run.

Usage:
    cd platform
    source .venv/bin/activate
    python ../documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py
"""
import asyncio
import sys
from pathlib import Path

platform_dir = Path(__file__).resolve().parent.parent.parent.parent / "platform"
sys.path.insert(0, str(platform_dir))

from database import init_db  # noqa: E402
from models import Company  # noqa: E402
from services.rate_card_bootstrap import bootstrap_company_rate_cards  # noqa: E402


async def backfill() -> None:
    await init_db()

    companies = await Company.find_all().to_list()
    print(f"Found {len(companies)} companies. Seeding default rate cards…")

    total_created = 0
    for company in companies:
        try:
            created = await bootstrap_company_rate_cards(company.id)
        except Exception as exc:
            print(f"  ✖ {company.name} ({company.id}): {exc!r}")
            continue
        total_created += created
        marker = "+" if created else " "
        print(f"  {marker} {company.name} ({company.id}): {created} created")

    print(f"\nDone. {total_created} rate cards created across {len(companies)} companies.")


if __name__ == "__main__":
    asyncio.run(backfill())
