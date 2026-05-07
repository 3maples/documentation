"""
Migration script: Recalculate every labour's stored Rate (`price`) using the
new pricing formula:

    unbillable = cost * (standard_unbillable_percent / 100)
    burden     = (cost + unbillable) * (labor_burden / 100)
    price      = round(cost + unbillable + burden, 2)

Run once after deploying the People-pricing change so legacy rows whose
`price` was computed via the old single-step `cost * (1 + labor_burden/100)`
formula reconcile with the new four-component breakdown surfaced on the
People page.

Idempotent — running it twice produces the same result.

Usage:
    cd platform
    source .venv/bin/activate
    python ../documentation/development/migration_scripts/migrate_labour_recalculate_prices.py
"""

import asyncio
import sys
from pathlib import Path

# Add platform/ to sys.path so the script can import the app's modules.
project_root = Path(__file__).resolve().parents[3] / "platform"
sys.path.insert(0, str(project_root))

from database import init_db  # noqa: E402
from models import Company, Labour  # noqa: E402
from services.labour_pricing import compute_labour_price  # noqa: E402


async def migrate():
    print("Initializing database...")
    await init_db()
    print("Database initialized.\n")

    companies = await Company.find_all().to_list()
    if not companies:
        print("No companies found.")
        return

    total_labours_updated = 0
    companies_processed = 0

    for company in companies:
        # Read percentages explicitly — `or` would treat a legitimate 0% as missing
        # and silently overwrite it with the default.
        unbillable_pct = getattr(company, "standard_unbillable_percent", None)
        if unbillable_pct is None:
            unbillable_pct = 20.0
        burden_pct = getattr(company, "labor_burden", None)
        if burden_pct is None:
            burden_pct = 20.0

        labours = await Labour.find(Labour.company == company.id).to_list()
        if not labours:
            continue

        company_updates = 0
        for labour in labours:
            cost = float(labour.cost or 0)
            new_price = compute_labour_price(cost, unbillable_pct, burden_pct)
            current_price = round(float(labour.price or 0), 2)
            if current_price == new_price:
                continue
            await labour.set({"price": new_price})
            company_updates += 1

        if company_updates:
            print(
                f"  {company.name}: recomputed Rate on {company_updates} of "
                f"{len(labours)} labour row(s) "
                f"(Unbillable {unbillable_pct}%, Burden {burden_pct}%)"
            )
        else:
            print(f"  {company.name}: already in sync ({len(labours)} row(s))")

        total_labours_updated += company_updates
        companies_processed += 1

    print(
        f"\nDone. Updated {total_labours_updated} labour row(s) "
        f"across {companies_processed} company(ies)."
    )


if __name__ == "__main__":
    asyncio.run(migrate())
