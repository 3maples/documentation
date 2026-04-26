# Default Rate Cards — Seed + Bootstrap

## Context

Company `69b9ce11d58899aa86549b95` has 7 hand-curated rate cards (now all on canonical unit values after the unit-dropdown migration). We want those same cards to be the default starter set for **every** company:

1. **Snapshot them** as a checked-in JSON fixture in `platform/data/`.
2. **Backfill** every existing company that doesn't already have them.
3. **Bootstrap** them automatically when a new company is created.

The JSON file becomes the source of truth — future tweaks to defaults happen by editing JSON, not by editing the seed company. Cards are seeded **by name with skip-on-collision**, so any company that has already customized (or named) a card is left untouched.

## Changes

### 1. One-shot export → `platform/data/default_rate_cards.json`

A small one-shot script reads the 7 rate cards belonging to `69b9ce11d58899aa86549b95` and writes them as JSON. After this runs, the script is no longer needed (the JSON is the source of truth) but we keep it in `documentation/development/migration_scripts/` for reproducibility.

**File (new):** `documentation/development/migration_scripts/export_default_rate_cards.py`

- Connect to MongoDB via `config.settings.mongodb_url`.
- Find all `rate_cards` documents where `company == ObjectId("69b9ce11d58899aa86549b95")`.
- For each card, write `{name, items: [{task, unit, easy, standard, hard}, …]}` (drop `_id`, `company`, timestamps).
- Sort cards alphabetically by `name`, items in their existing order.
- Pretty-print with 2-space indent into `platform/data/default_rate_cards.json`.

**File (new, generated):** `platform/data/default_rate_cards.json` — the fixture itself.

### 2. Bootstrap service

**File (new):** `platform/services/rate_card_bootstrap.py`

Mirror the shape of `services/division_bootstrap.py`:

```python
DEFAULT_RATE_CARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "default_rate_cards.json"

def load_default_rate_card_templates() -> list[dict]:
    """Load default rate card templates from JSON."""
    with DEFAULT_RATE_CARDS_PATH.open("r", encoding="utf-8") as fh:
        templates = json.load(fh)
    # Validate each template has name + items[] with required item fields.
    return templates

async def bootstrap_company_rate_cards(company_id: str | PydanticObjectId) -> int:
    """Seed default rate cards for one company. Skips any name that already exists."""
    normalized = PydanticObjectId(str(company_id))
    templates = load_default_rate_card_templates()
    created = 0
    for tpl in templates:
        existing = await RateCard.find_one({"name": tpl["name"], "company": normalized})
        if existing:
            continue  # never touch user-customized cards
        items = [CardItem(**ci) for ci in tpl["items"]]
        await RateCard(name=tpl["name"], items=items, company=normalized).insert()
        created += 1
    return created
```

Note: because `CardItem.unit` is now a Literal, an invalid unit in the JSON will raise a `ValidationError` at load time — desirable, fails fast.

### 3. Wire into new-company flow

**File:** `platform/services/company_service.py`

- Import `bootstrap_company_rate_cards`.
- Add `(bootstrap_company_rate_cards, "rate cards")` to the `always_bootstrap` list (lines 41–45). Existing try/except wrapper already swallows + logs failures so a seeding error won't block company creation.

### 4. One-time backfill for existing companies

**File (new):** `documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py`

- Initialize Beanie via `database.init_db()` so document operations work.
- Iterate every `Company` document.
- For each, call `bootstrap_company_rate_cards(company.id)`.
- Print per-company `created` counts and grand total.
- Idempotent — safe to re-run; already-named cards are skipped.

### 5. Tests

**File (new):** `platform/tests/test_rate_card_bootstrap.py`

- `test_load_default_rate_card_templates_parses_json` — fixture file loads with at least one card and CardItem validation passes.
- `test_bootstrap_creates_cards_for_new_company` — empty company → cards created, count matches template length.
- `test_bootstrap_is_idempotent` — second call creates 0 new cards.
- `test_bootstrap_skips_existing_card_by_name` — pre-create one card with a default name + custom items; bootstrap leaves its items untouched and only creates the others.

No changes needed to existing `test_rate_cards_api.py`.

## Critical files

- `platform/data/default_rate_cards.json` — the fixture (generated)
- `platform/services/rate_card_bootstrap.py` — new bootstrap (mirrors `division_bootstrap.py`)
- `platform/services/company_service.py` — add to `always_bootstrap`
- `platform/tests/test_rate_card_bootstrap.py` — new tests
- `documentation/development/migration_scripts/export_default_rate_cards.py` — one-shot exporter
- `documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py` — backfill

## Reused patterns

- Bootstrap shape — `platform/services/division_bootstrap.py:1-44` (CSV → JSON is the only departure, since rate cards are nested).
- Wiring point — `platform/services/company_service.py:41-45` (`always_bootstrap` tuple list).
- Migration script template — `documentation/development/migration_scripts/migrate_rate_card_units.py` (motor + `config.settings.mongodb_url` + path-mangling for cross-package import).

## Verification

1. **Export & inspect:** run the exporter, then `cat platform/data/default_rate_cards.json` — confirm 7 cards present, all unit values in the canonical four.
2. **Backend tests:** `cd platform && ./run_tests.sh tests/test_rate_card_bootstrap.py`.
3. **Backfill dry-run:** before touching prod, run `seed_rate_cards_for_existing_companies.py` against staging; check the per-company counts. Should be 7 for empty companies, 0 for `69b9ce11d58899aa86549b95` (already has them).
4. **New-company smoke test:**
   - `cd platform && uvicorn main:app --reload`
   - `cd portal && npm run dev`
   - Sign up a brand-new company via the UI → Settings → Rate Cards → confirm all 7 default cards appear immediately.
5. **Run prod backfill:** once staging looks clean, run the same script against prod.
