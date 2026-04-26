"""One-shot exporter: dump rate cards from the seed company to JSON.

Reads every rate card belonging to the seed company and writes them to
`platform/data/default_rate_cards.json`. That file is the source of truth
for default rate cards going forward — to change the defaults, edit the
JSON directly (do not re-run this script unless you know you want to
overwrite the fixture from the live seed company).

Usage:
    cd platform
    source .venv/bin/activate
    python ../documentation/development/migration_scripts/export_default_rate_cards.py
"""
import asyncio
import json
import sys
from pathlib import Path

platform_dir = Path(__file__).resolve().parent.parent.parent.parent / "platform"
sys.path.insert(0, str(platform_dir))

from bson import ObjectId  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from config import settings  # noqa: E402

SEED_COMPANY_ID = "69b9ce11d58899aa86549b95"
OUTPUT_PATH = platform_dir / "data" / "default_rate_cards.json"


async def export() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.db_name

    cursor = db.rate_cards.find({"company": ObjectId(SEED_COMPANY_ID)})
    cards: list[dict] = []
    async for doc in cursor:
        cards.append(
            {
                "name": doc["name"],
                "items": [
                    {
                        "task": item["task"],
                        "unit": item["unit"],
                        "easy": item["easy"],
                        "standard": item["standard"],
                        "hard": item["hard"],
                    }
                    for item in (doc.get("items") or [])
                ],
            }
        )

    client.close()

    cards.sort(key=lambda c: c["name"].lower())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(cards, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    item_count = sum(len(c["items"]) for c in cards)
    print(f"Exported {len(cards)} rate cards ({item_count} items) to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(export())
