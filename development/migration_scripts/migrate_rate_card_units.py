"""Migration script: Map legacy rate-card unit strings to canonical values.

Maps known legacy values inside each `rate_cards.items[].unit` field:
  SF/HOUR, sqft, SQFT → square feet/hour
  LF/HOUR, Feet       → linear feet/hour

Items already on a canonical value are left alone. Items on any other
non-canonical value are flagged for manual cleanup (not written), so the
operator can decide what to do before the new Pydantic Literal validation
goes live.

Idempotent — safe to re-run.

Usage:
    cd platform
    source .venv/bin/activate
    python ../documentation/development/migration_scripts/migrate_rate_card_units.py
"""
import asyncio
import sys
from pathlib import Path

# Make `platform/` importable so we can reuse `config.settings`.
platform_dir = Path(__file__).resolve().parent.parent.parent.parent / "platform"
sys.path.insert(0, str(platform_dir))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from config import settings  # noqa: E402


CANONICAL_UNITS = {
    "square feet/hour",
    "square yard/hour",
    "linear feet/hour",
    "linear yard/hour",
}

LEGACY_MAP: dict[str, str] = {
    "SF/HOUR": "square feet/hour",
    "sqft": "square feet/hour",
    "SQFT": "square feet/hour",
    "LF/HOUR": "linear feet/hour",
    "Feet": "linear feet/hour",
}


async def migrate() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name

    cards_scanned = 0
    items_updated = 0
    cards_modified = 0
    flagged: list[str] = []

    async for doc in db.rate_cards.find({}):
        cards_scanned += 1
        items = doc.get("items") or []
        new_items = []
        modified = False

        for idx, item in enumerate(items):
            raw_unit = item.get("unit", "")
            new_item = dict(item)

            if raw_unit in CANONICAL_UNITS:
                new_items.append(new_item)
                continue

            mapped = LEGACY_MAP.get(raw_unit) if isinstance(raw_unit, str) else None
            if mapped is not None:
                new_item["unit"] = mapped
                items_updated += 1
                modified = True
            else:
                flagged.append(
                    f"  ⚠ Card '{doc.get('name', '?')}' (id={doc['_id']}) "
                    f"item #{idx} task='{item.get('task', '?')}': "
                    f"non-canonical unit '{raw_unit}' — left unchanged"
                )

            new_items.append(new_item)

        if modified:
            await db.rate_cards.update_one(
                {"_id": doc["_id"]},
                {"$set": {"items": new_items}},
            )
            cards_modified += 1

    client.close()

    print(f"Migration complete: {cards_scanned} rate cards scanned")
    print(f"  Cards modified: {cards_modified}")
    print(f"  Items updated:  {items_updated}")
    if flagged:
        print(f"  Flagged for manual review ({len(flagged)}):")
        for line in flagged:
            print(line)
        print(
            "\nResolve flagged items before deploying the new Pydantic Literal "
            "validation, otherwise reads of those documents will fail."
        )
    else:
        print("  No items needed manual review.")


if __name__ == "__main__":
    asyncio.run(migrate())
