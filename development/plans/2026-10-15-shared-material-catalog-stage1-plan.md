# Shared Material Catalog — Stage 1 (Platform Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace per-company copies of the standard material list with one global `standard_materials` collection plus per-company overrides, behind a single effective-catalog service that every platform reader and writer uses — with paged, searchable, filterable listing.

**Architecture:** `standard_materials` (global) + `material_overrides` (company × standard: hidden, per-size cost/price) + the existing company `materials` (custom and detached items). Category opt-in is `MaterialCategory.include_standard`; item opt-out is `MaterialOverride.hidden`. `services/material_catalog.py` is the only module that queries those three collections; it merges them into `EffectiveMaterial` records, applies live markup to un-overridden standard sizes, and pages/searches/filters in one aggregation. Estimate and template lines keep storing a plain id string — for a standard material, the standard's `_id`.

**Tech Stack:** FastAPI + Beanie + Motor + pytest against the local `mongodb-atlas-local` container.

**Spec:** [2026-10-15-shared-material-catalog-design.md](2026-10-15-shared-material-catalog-design.md) — §11 decisions are final.

**Status:** Implemented 2026-10-15, all 15 tasks. See "As built" at the end for where the code departs from the text below. Not yet run: the seed and migration scripts on Dev or production (stage 3), and the live planner parity run that the Task 13 policy change owes.

**Out of scope for stage 1** (design §10.2): the portal (stage 2), running the migration on Dev/prod (stage 3), new Maple phrasings and the duplicate-offer copy (stage 4), the ops UI/import endpoints (stage 5), and removal of the compatibility paths (stage 6).

## Global Constraints

- **TDD is mandatory** (CLAUDE.md). Failing test first, then implementation. Every task is ordered that way; do not reorder.
- **Commits need explicit user approval each time.** Each "Commit" step names what to commit; ask before running it, or wait for the user's `/commit`. Never chain one approval into the next. Never `--amend` without checking `HEAD`. Never push.
- Commit message format `<type>: <description>`, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Gates after every `.py` edit:** `./run_mypy.sh <touched path>` and `./run_ruff.sh <touched path>`, zero errors. `./run_bandit.sh <touched path>` must not raise the B110 baseline of 11.
- **Run only the test files each task names.** Never the full suite. Local Mongo first: `cd platform && ./scripts/start_test_mongo.sh`.
- **Separate git repos:** `platform/` and `documentation/` each commit on their own.
- **Tenant scope** (CLAUDE.md): every read of company data filters on `company`. Standard rows are global and hold no tenant data; overrides are always queried with `company`. Hidden is a list/search concern, never a permission boundary — `resolve_many` and `get_effective` return hidden and category-disabled items so existing lines always resolve.
- **Roles** (decision §11.4): any write that sets a size's cost or price is Owner/Admin — in REST and in Maple. Name/description/category edits on custom materials stay any role.
- **Pricing** (`.claude/rules/pricing.md`): `price = round(cost × (1 + markup/100), 2)`. The rounding helper is shared, not re-typed. Estimate lines keep snapshotting price and cost at write time; nothing in this plan re-prices an estimate.
- **Datetimes are aware UTC.** `models/` never imports `services/` (`tests/test_models_layering.py`).
- **Beanie `Document.aggregate().to_list()` is broken under the pinned driver.** Use `Model.get_pymongo_collection().aggregate(pipeline)` with `async for` (precedent: `routers/tasks.py:177`).
- **Tests own their data.** The standard collection is global, so every test that inserts standard materials uses a unique key prefix and deletes what it inserted (fixture in Task 2).
- **Phrasing reference:** where a task changes what Maple replies, update the matching rows of `documentation/development/maple-phrasing-reference.md` in the same task. Add no changelog entries.

## Shared interfaces (produced by Tasks 1–5, consumed by everything after)

```python
# models/standard_material.py
class StandardMaterialSize(BaseModel): size: str; unit_key: str; cost: float
class StandardMaterial(Document):     # collection "standard_materials"
    key: str; name: str; name_norm: str; description: Optional[str]
    category_key: str; sizes: List[StandardMaterialSize]
    industries: List[CompanyIndustry] = []; retired_at: Optional[datetime] = None
    version: int = 1; created_at; updated_at

# models/material_override.py
class MaterialSizeOverride(BaseModel): size: str; cost: Optional[float] = None; price: Optional[float] = None
class MaterialOverride(Document):     # collection "material_overrides"
    company: PydanticObjectId; standard: PydanticObjectId
    hidden: bool = False; sizes: List[MaterialSizeOverride] = []; updated_at

# services/material_catalog.py
class EffectiveSize(BaseModel):
    size: str; unit: Optional[PydanticObjectId]; unit_name: Optional[str]
    cost: float; price: float
    standard_cost: Optional[float] = None; overridden: bool = False
class EffectiveMaterial(BaseModel):
    id: str; name: str; description: Optional[str]
    category: Optional[PydanticObjectId]; category_name: Optional[str]
    sizes: List[EffectiveSize]
    company: PydanticObjectId
    source: Literal["standard", "custom", "detached"]
    standard_id: Optional[str]; hidden: bool; retired: bool; updated_at: datetime
    def to_api(self) -> dict          # adds "_id" == id for the portal's `_id ?? id`
class Page(BaseModel, Generic[T]): items: List[T]; total: int; page: int; page_size: int

# services/material_keys.py: slug(name), norm_name(name)   (re-exported by material_catalog)
# services/material_vocabulary.py: vocabulary(company) -> Vocabulary, ensure_standard_vocabulary(...)
def markup_price(cost: float, markup_pct: float) -> float
async def get_effective(company, material_id) -> Optional[EffectiveMaterial]
async def resolve_many(company, ids) -> Dict[str, EffectiveMaterial]
async def list_effective(company, *, search=None, category=None, source="all",
                         visibility="visible", sort="name",
                         price_filters=(),     # Maple's (direction, threshold) pairs; one size meets all
                         page=1, page_size=50) -> Page[EffectiveMaterial]
async def count_effective(company, **same_filters) -> int
async def find_by_name(company, text, *, exact=False, limit=10) -> List[EffectiveMaterial]
async def iter_effective(company, *, visibility="visible") -> AsyncIterator[EffectiveMaterial]
async def assert_name_available(company, name, *, ignore_id=None) -> None     # 409
async def set_size_pricing(company, standard_id, size, *, cost=None, price=None) -> EffectiveMaterial
async def set_hidden(company, material_id, hidden: bool) -> EffectiveMaterial
async def reset_to_standard(company, standard_id) -> EffectiveMaterial
async def duplicate(company, material_id, *, name=None) -> Material
async def set_standard_categories(company, *, enable: bool, category_ids=None) -> int
```

---

# Phase A — Data model and seed

### Task 1: New documents, new fields, indexes, audit actions

**Files:**
- Create: `platform/models/standard_material.py`, `platform/models/material_override.py`
- Modify: `platform/models/material.py` (`hidden`, `derived_from`; index `(company, hidden)`)
- Modify: `platform/models/material_category.py`, `platform/models/material_unit.py` (`standard_key`; category also `include_standard`; index `(company, standard_key)`)
- Modify: `platform/models/estimate.py` (`Estimate.Settings.indexes` += `job_items.materials.material`), `platform/models/template.py` (same field path)
- Modify: `platform/models/audit_log.py` (`MATERIAL_OVERRIDE`, `MATERIAL_VISIBILITY`, `MATERIAL_CATEGORY_STANDARD_TOGGLE`; `ResourceType.STANDARD_MATERIAL`)
- Modify: `platform/models/__init__.py`, `platform/database.py` (register both new documents)
- Test: `platform/tests/test_material_catalog_models.py` (new)

**Interfaces:** produces the documents and fields in "Shared interfaces".

- [ ] **Step 1: Write the failing tests**

```python
"""Shared-catalog documents (2026-10-15 design §4)."""
import pytest
from pydantic import ValidationError


def test_standard_material_requires_a_size():
    from models.standard_material import StandardMaterial
    with pytest.raises(ValidationError):
        StandardMaterial(key="k", name="K", name_norm="k", category_key="c", sizes=[])


def test_standard_material_has_no_company_and_no_price():
    from models.standard_material import StandardMaterial, StandardMaterialSize
    fields = set(StandardMaterial.model_fields)
    assert "company" not in fields
    assert "price" not in StandardMaterialSize.model_fields


def test_new_material_fields_default_to_today():
    from models.material import Material
    assert Material.model_fields["hidden"].default is False
    assert Material.model_fields["derived_from"].default is None


def test_category_opt_in_defaults_off():
    from models.material_category import MaterialCategory
    assert MaterialCategory.model_fields["include_standard"].default is False
    assert MaterialCategory.model_fields["standard_key"].default is None


def test_override_is_unique_per_company_and_standard():
    from models.material_override import MaterialOverride
    keys = [tuple(i.document["key"]) for i in MaterialOverride.Settings.indexes]
    unique = [i for i in MaterialOverride.Settings.indexes if i.document.get("unique")]
    assert (("company", 1), ("standard", 1)) in keys and unique


def test_estimate_lines_are_indexed_by_material_id():
    from models.estimate import Estimate
    keys = [dict(i.document["key"]) for i in Estimate.Settings.indexes]
    assert {"job_items.materials.material": 1} in keys


def test_new_documents_are_registered(client):
    import database
    source = open(database.__file__).read()
    assert "StandardMaterial" in source and "MaterialOverride" in source
```

- [ ] **Step 2:** `./run_tests.sh tests/test_material_catalog_models.py` — expect failures (imports and fields missing).
- [ ] **Step 3: Implement.** Field shapes exactly as "Shared interfaces". `StandardMaterial` indexes: `key` unique, `name_norm`, `(category_key, name_norm)`, `retired_at`. Both new documents keep the `@before_event([Replace, Insert])` timestamp hook; `StandardMaterial`'s hook also refuses an empty `sizes` like `Material` does. `MaterialOverride` indexes: unique `(company, standard)`, `(company, hidden)`.
- [ ] **Step 4:** re-run the test file; then `./run_tests.sh tests/test_models_layering.py tests/test_material_api.py` to confirm nothing regressed.
- [ ] **Step 5: Gates** — `./run_mypy.sh models database.py`, `./run_ruff.sh models database.py`.
- [ ] **Step 6: Commit (ask first)** — platform: `feat: add standard material and override documents`.

### Task 2: Standard seed loader, seed script and test fixture

**Files:**
- Create: `platform/services/standard_material_seed.py`, `platform/scripts/seed_standard_materials.py`
- Modify: `platform/services/material_category_bootstrap.py`, `platform/services/material_unit_bootstrap.py` (`load_default_*_templates` return a `key` per row)
- Modify: `platform/tests/conftest.py` (fixture `standard_catalog`)
- Test: `platform/tests/test_standard_material_seed.py` (new)

**Interfaces:**
- Produces: `slug(name) -> str`; `load_standard_rows(path) -> SeedRows` (grouped by key, `(name, size)` duplicates dropped and reported, `price` column ignored, optional `key` column preferred over `slug(name)`, category/unit names mapped to keys, unknown names reported as errors); `async upsert_standard_materials(rows) -> SeedReport{created, updated, unchanged, duplicates_dropped, errors}` (by `key`; bumps `version` only when content changed; never retires or deletes).
- Produces fixture `standard_catalog(client)`: inserts three standard materials under keys prefixed `test-std-<uuid8>-` in two categories (`aggregates`, `bulk-material`) — one with two sizes — yields their `{key: id}` map, and deletes them plus any `material_overrides` pointing at them on teardown.

- [ ] **Step 1: Write the failing tests** — named cases:
  - `test_rows_group_sizes_by_material` (two rows, one name → one material, two sizes)
  - `test_exact_duplicate_rows_are_dropped_and_counted` (the real CSV's four Rhododendron duplicates: `duplicates_dropped == 4`)
  - `test_price_column_is_ignored` (row with `price` → no price anywhere in the output)
  - `test_key_column_wins_over_slug`
  - `test_unknown_category_or_unit_is_an_error_not_a_skip`
  - `test_upsert_is_idempotent_and_versions_only_on_change` (insert → `created`; same rows again → `unchanged`, version 1; changed cost → `updated`, version 2; ids stable throughout)
  - `test_upsert_never_retires_missing_rows`
  - `test_real_seed_file_loads_without_errors` (loads `data/default_materials.csv`; asserts 150 materials and no errors)
- [ ] **Step 2:** run, expect failures.
- [ ] **Step 3: Implement.** The script is a thin CLI over the service: `python scripts/seed_standard_materials.py [--file data/default_materials.csv] [--apply]`, dry-run by default, prints the report. The seed is changing soon (decision §11.7); the loader reads by header name so the new file drops in.
- [ ] **Step 4:** run the test file, then `./run_tests.sh tests/test_material_categories_api.py tests/test_material_units_api.py`.
- [ ] **Step 5: Gates** on `services scripts/seed_standard_materials.py tests/conftest.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: seed the standard material catalog by key`.

### Task 3: Standard vocabulary on company categories and units

**Files:**
- Modify: `platform/services/material_category_bootstrap.py`, `platform/services/material_unit_bootstrap.py`, `platform/services/bootstrap_helpers.py` (`upsert_named_templates` writes `standard_key` on insert and backfills it on a same-name doc that lacks one)
- Create: `platform/services/material_vocabulary.py`
- Modify: `platform/routers/material_categories.py`, `platform/routers/material_units.py` (delete guards; serialize the new fields)
- Test: `platform/tests/test_material_vocabulary.py` (new); extend `tests/test_material_categories_api.py`, `tests/test_material_units_api.py`

**Interfaces:**
- Produces `Vocabulary{category_by_key: Dict[str, oid], key_by_category: Dict[oid, str], enabled_keys: Set[str], unit_by_key: Dict[str, oid], unit_name: Dict[oid, str], category_name: Dict[oid, str]}` and `async vocabulary(company) -> Vocabulary` (two queries).
- Produces `async ensure_standard_vocabulary(company, category_keys, unit_keys)` — re-creates seeded categories/units the company deleted or never had, from the seed CSVs, by key.

- [ ] **Step 1: Failing tests:**
  - `test_bootstrap_stamps_standard_keys`
  - `test_bootstrap_backfills_a_key_onto_an_existing_same_name_category` (pre-existing companies)
  - `test_vocabulary_maps_both_ways_and_lists_enabled_keys`
  - `test_ensure_recreates_a_deleted_standard_category_with_its_key`
  - `test_a_standard_keyed_category_cannot_be_deleted_while_standard_materials_use_it` (409, uses `standard_catalog`)
  - `test_a_standard_keyed_unit_cannot_be_deleted_while_standard_materials_use_it`
  - `test_a_custom_category_still_deletes_when_unused` (unchanged behavior)
  - `test_category_list_includes_standard_key_and_include_standard`
- [ ] **Step 2–4:** fail, implement, pass. The delete guard asks `standard_materials` for any non-retired row with that `category_key` / `sizes.unit_key` (one `find_one`). Existing company-material in-use checks stay as they are.
- [ ] **Step 5: Gates** on `services routers/material_categories.py routers/material_units.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: key company categories and units to the standard vocabulary`.

---

# Phase B — The effective catalog service

### Task 4: Read side — merge, live markup, resolve, list, search

**Files:**
- Create: `platform/services/material_catalog.py`
- Modify: `platform/routers/materials.py` (`_normalize_size_entry` uses `material_catalog.markup_price`)
- Test: `platform/tests/test_material_catalog_service.py` (new)

**Interfaces:** produces every read function in "Shared interfaces".

Effective rules (design §4.5, decisions §11.1–§11.2):
- standard size: `cost = override.cost ?? standard.cost`; `price = override.price ?? markup_price(cost, company.material_markup)`; `overridden = override has cost or price for that size`; `standard_cost = standard.cost`. An override for a size the standard no longer has is ignored.
- custom/detached: stored cost and price; `source = "detached"` when `derived_from` is set.
- **visible** = (custom and not `hidden`) or (standard, category key in `enabled_keys`, not `override.hidden`, not retired).
- `category` on a standard item is the company's category id for its key (`None` if the company has no doc for that key — `ensure_standard_vocabulary` runs on enable, so this only happens for a disabled category); `unit` likewise.

- [ ] **Step 1: Write the failing tests** (all use `standard_catalog` and their own company via `tests/helpers.onboard_owner`, cleaned up at the end):

```python
async def test_untouched_standard_price_follows_company_markup(...):
    # markup 25%, standard cost 20.00 -> price 25.00; change markup to 10% -> 22.00
async def test_cost_override_reprices_from_markup_and_price_override_pins(...):
async def test_override_on_a_size_the_standard_dropped_is_ignored(...):
async def test_disabled_category_hides_its_standard_items_from_lists(...):
async def test_hidden_item_stays_hidden_when_its_category_is_toggled_off_and_on(...):   # §11.2
async def test_hidden_and_disabled_items_still_resolve(...):                           # resolve_many + get_effective
async def test_retired_standard_resolves_but_never_lists(...):
async def test_get_effective_never_returns_another_companys_custom_material(...):      # tenant scope
async def test_list_pages_with_stable_total_and_name_order(...):                       # page 1/2, total unchanged
async def test_search_matches_name_and_description_case_insensitively_and_escapes_regex(...):
async def test_filters_source_category_visibility_and_price_range(...):                # price on effective price
async def test_sort_by_effective_price(...):
async def test_find_by_name_exact_and_partial_skip_hidden(...):
async def test_iter_effective_yields_category_names_not_ids(...):                      # fixes research-prompt bug
async def test_count_matches_list_total(...):
```

- [ ] **Step 2:** run, expect failures.
- [ ] **Step 3: Implement.**
  - `list_effective` is one pipeline on `standard_materials`: `$match` enabled keys + not retired + search → `$lookup` overrides (`company`, `standard`) → `$addFields` merged sizes with `$multiply`/`$round` → `$unionWith` company `materials` (`$match company` + search) → visibility/source/category/price `$match` → `$sort {name_norm, _id}` → `$facet {total, items}`. Company materials gain `name_norm` in the pipeline via `$toLower`; no stored field needed.
  - `markup_price` rounds half-up to the cent, matching the existing `round(..., 2)` call sites within one cent; the test pins `round(cost * (1 + m/100), 2)` equality for the seed's cost values so nothing already stored drifts.
  - `resolve_many` / `get_effective`: split ids into valid ObjectIds; one `$in` on `standard_materials`, one `$in` + `company` on `materials`, one `$in` + `company` on `material_overrides`. Invalid ids resolve to nothing.
- [ ] **Step 4:** run the test file and `./run_tests.sh tests/test_material_api.py`.
- [ ] **Step 5: Gates** on `services/material_catalog.py routers/materials.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: effective material catalog read service`.

### Task 5: Write side — overrides, hide/show, reset, duplicate, uniqueness, category opt-in

**Files:**
- Modify: `platform/services/material_catalog.py`
- Test: `platform/tests/test_material_catalog_writes.py` (new)

**Interfaces:** produces the write functions in "Shared interfaces". Callers do role checks and audit logging; the service does neither.

- [ ] **Step 1: Failing tests:**
  - `test_first_override_creates_the_document_and_reset_deletes_it`
  - `test_override_that_carries_nothing_is_pruned` (clear the last size value on a not-hidden override → document gone)
  - `test_override_for_an_unknown_size_is_refused` (`ValueError` → callers map to 422)
  - `test_hide_and_show_a_standard_item_and_a_custom_item`
  - `test_duplicate_names_the_copy_name_copy_then_copy_2` (decision §11.8)
  - `test_duplicate_of_a_standard_copies_effective_cost_and_price_and_sets_derived_from`
  - `test_duplicate_is_detached_from_later_standard_changes` (upsert a new standard cost → copy unchanged)
  - `test_name_must_be_unique_across_custom_and_visible_standard` (409 both directions, case-insensitive)
  - `test_a_hidden_or_disabled_standard_does_not_reserve_its_name`
  - `test_showing_a_standard_whose_name_a_custom_item_took_is_refused`
  - `test_enabling_categories_recreates_missing_vocabulary_and_leaves_hides_alone`
  - `test_disable_all_then_enable_all_restores_the_same_visible_set`
  - `test_enabling_a_category_hides_standards_whose_name_a_custom_material_holds` (a company that still holds copies, or later uses the old Load Standard button, must never see two rows of one name; the result reports the hidden names)
- [ ] **Step 2–4:** fail, implement, pass. `assert_name_available` raises `HTTPException(409, {"detail": ..., "conflict": {"id", "name", "source"}})`. `duplicate` resolves the next free "`<name> copy`", "`<name> copy 2`" … via one `find_by_name(..., exact=False)` call over the `<name> copy` prefix. Override writes use `find_one_and_update` with `upsert=True` on `(company, standard)` so two concurrent writes can't create two documents.
- [ ] **Step 5: Gates** on `services/material_catalog.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: material overrides, visibility, duplicate and opt-in writes`.

---

# Phase C — REST API

### Task 6: Listing and reads

**Files:**
- Modify: `platform/routers/materials.py` (`GET /`, `GET /{id}`; new `GET /resolve`, `POST /lookup-names`)
- Test: `platform/tests/test_materials_api_paged.py` (new); update `tests/test_material_api.py::test_get_materials`

**Interfaces:**
- `GET /materials?company=&search=&category=&source=&visibility=&sort=&min_price=&max_price=&page=&page_size=` → `{items, total, page, page_size}` (`min_price`/`max_price` become `("gte", …)` / `("lte", …)` price filters) (`page_size` 1–100, default 50; `search` max 200 chars). **Compatibility:** with none of those parameters present it returns the bare array of every *visible* effective material, as today, until stage 6. Each item is `EffectiveMaterial.to_api()` so `_id` is present.
- `GET /materials/{id}` → effective record for a standard or own id; 404 for missing or another company's.
- `GET /materials/resolve?company=&ids=a,b` → `{id: record}` (≤ 200 ids; hidden and retired included).
- `POST /materials/lookup-names?company=` `{names: [...]}` → `{name: id | null}` (exact, visible only, ≤ 200 names).

- [ ] **Step 1: Failing tests:** envelope shape and paging; compat array when no parameters; `_id` on every item; each filter reaches the service; `page_size=101` → 422; another company's id → 404 on `GET /{id}` and absent from `resolve`; `lookup-names` returns `null` for hidden.
- [ ] **Step 2–4:** fail, implement, pass. Also run `./run_tests.sh tests/test_material_api.py tests/test_resources_rbac.py`.
- [ ] **Step 5: Gates** on `routers/materials.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: paged, searchable materials listing`.

### Task 7: Writes, roles and the opt-in endpoints

**Files:**
- Modify: `platform/routers/materials.py`, `platform/routers/material_categories.py`
- Test: `platform/tests/test_material_overrides_api.py` (new); update `tests/test_material_api.py`, `tests/test_material_upload_api.py`, `tests/test_resources_rbac.py`, `tests/test_audit_integration.py`

**Interfaces** (design §6.3 with decision §11.4):

| Endpoint | Behavior | Role |
|---|---|---|
| `POST /materials/` | custom create; `assert_name_available` | Owner/Admin |
| `PUT /materials/{id}` standard | `sizes[].cost/price` → `set_size_pricing`; any other field → `409 {action: "duplicate"}` | Owner/Admin |
| `PUT /materials/{id}` custom | sparse patch as today; rename → `assert_name_available` | `sizes` present → Owner/Admin; otherwise any |
| `PATCH /materials/{id}/pricing` `{sizes: [{size, cost?, price?}]}` | per-size override; omitted = leave, null = clear (the portal's per-size reset, design §7.1); all sizes checked before any write. *Added during implementation.* | Owner/Admin |
| `POST /materials/{id}/duplicate` `{name?}` | `duplicate` | Owner/Admin |
| `PATCH /materials/{id}/visibility` `{hidden}` | `set_hidden` | Owner/Admin |
| `DELETE /materials/{id}/overrides` | `reset_to_standard` | Owner/Admin |
| `DELETE /materials/{id}` standard | `409 {action: "hide"}` | Owner/Admin |
| `DELETE /materials/{id}` custom | `409` with the count when any estimate or template line references it | Owner/Admin |
| `DELETE /materials/?company=` | custom materials not in use; `{deleted, skipped_in_use}` | Owner/Admin |
| `POST /materials/reset-standard` `{clear_overrides, remove_unused_custom}` | bulk reset | Owner/Admin |
| `POST /materials/load-standard` | **compat:** enable all standard categories; `remove_non_standard` → remove unused custom | Owner/Admin |
| `POST /materials/upload` | name matching an enabled, visible standard → size override (cost may be blank when a price is given; only changed values are written); else custom create/update, matched case-insensitively | Owner/Admin |
| `PATCH /material-categories/{id}` `{include_standard}` | `set_standard_categories` for one | Owner/Admin |
| `POST /material-categories/standard` `{include_standard}` | all standard categories | Owner/Admin |

The role check for `PUT` runs **inside the handler**, not only as a `Depends`, because Maple calls `update_material` directly with `acting_user()` (`agents/material/service.py:675`); a dependency would be skipped on that path. Audit: overrides and reset → `MATERIAL_OVERRIDE`; visibility → `MATERIAL_VISIBILITY`; toggles → `MATERIAL_CATEGORY_STANDARD_TOGGLE`; duplicate → `MATERIAL_CREATE` with `metadata.derived_from`.

- [ ] **Step 1: Failing tests** — one per table row, plus: a Member gets 403 on every Owner/Admin row and on a custom `PUT` with `sizes`, but 200 on a custom rename; upload as Member → 403; an upload row named like a standard writes an override and creates no material; every write lands one audit entry of the right action.
- [ ] **Step 2–4:** fail, implement, pass. Existing tests that create materials as the default Owner keep passing; tests that relied on Member edits of cost/price are updated to the new rule, not deleted.
  - **Fixed in Task 7.** Pre-existing isolation bug (found 2026-10-15 in Task 5): `test_material_upload_api.py::test_upload_csv_category_mismatch` leaves "Patio Stone" (Hardscape, sq ft) in the shared test company, so the two `load_standard_*_removes_non_standard_when_requested` tests fail whenever the upload suite runs first. Reproduced on committed code. The test must delete what its first row created.
- [ ] **Step 5: Gates** on `routers/materials.py routers/material_categories.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: material override, visibility and opt-in endpoints with Owner/Admin pricing`.

---

# Phase D — Platform readers onto the service

Each task below swaps direct `Material` / `MaterialUnit` queries for the service and changes nothing else. A grep at the end of Task 12 proves no reader is left.

### Task 8: Estimate and template lines

**Files:**
- Modify: `platform/routers/estimate_helpers/snapshots.py` (`assert_own_line_refs` → material ids via `resolve_many`; `_fetch_snapshot_maps` and `enrich_job_items_in_place` via `resolve_many`; unit label from the **line's** size, falling back to the first size)
- Modify: `platform/routers/templates.py` (no change beyond the shared helper), `platform/services/template_bootstrap.py` (resolve by `find_by_name(exact=True)`; snapshot the unit **label**, not its id)
- Test: extend `tests/test_tenant_refs.py`, `tests/test_estimate_snapshot_helpers.py`, `tests/test_template_bootstrap.py`

- [ ] **Step 1: Failing tests:**
  - `test_an_estimate_can_carry_a_standard_material_line` (create + PUT accept a standard id)
  - `test_a_retired_standard_cannot_be_added_but_an_existing_line_keeps_saving`
  - `test_an_estimate_still_rejects_another_companys_custom_material` (existing case keeps passing)
  - `test_snapshot_unit_comes_from_the_lines_size`
  - `test_template_bootstrap_resolves_standard_names_and_snapshots_unit_labels`
- [ ] **Step 2–4:** fail, implement, pass; also run `./run_tests.sh tests/test_estimate_api.py tests/test_template_api.py tests/test_template_scaling.py`.
- [ ] **Step 5: Gates** on `routers/estimate_helpers routers/templates.py services/template_bootstrap.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: estimate and template lines resolve standard materials`.

### Task 9: Onboarding seeds opt-in, not copies

**Files:**
- Modify: `platform/services/company_service.py` (`include_standard_materials` → `set_standard_categories(enable=True)` instead of `bootstrap_company_materials`; templates still seeded when both flags are set)
- Test: extend `tests/test_template_bootstrap.py` (the one suite that passes `include_standard_materials`) and add `tests/test_onboarding_standard_materials.py`

- [ ] **Step 1: Failing tests:** a company onboarded with the flag has **zero** `materials` documents, every standard category enabled, and a non-empty `GET /materials` page; templates bootstrapped for it reference standard ids; without the flag no category is enabled.
- [ ] **Step 2–4:** fail, implement, pass.
- [ ] **Step 5: Gates** on `services/company_service.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: onboarding opts into standard materials instead of copying them`.

### Task 10: AI estimate generation

**Files:**
- Modify: `platform/agents/estimate/service.py` (`_fetch_materials_inventory` from `iter_effective`; category **name** into the catalog rows), `platform/agents/estimate/tools.py` (`lookup_materials` reads `iter_effective` once per call and scores through the matcher's word prefilter — *changed during implementation*: a per-term `find_by_name` would lose the matcher's synonyms, e.g. "foreman" ↔ "crew lead", "paving" ↔ "paver")
- Modify: `platform/agents/estimate/catalog_matching.py` — interim prefilter (design §8.3): score only candidates sharing a significant token with the label, falling back to the full inventory when the prefilter yields nothing
- Modify: `platform/prompts/material_catalog.py` (drop the stale "~148 tokens per material dump" paragraph — docstring only)
- Test: extend `tests/test_estimate_material_catalog_prompt.py`, `tests/test_estimate_agent.py`, `tests/test_estimate_tools.py`

- [ ] **Step 1: Failing tests:** inventory includes visible standard items with effective prices and excludes hidden ones; rendered catalog lines show the category name; the prefilter returns the same best match as the full scan on the existing matching fixtures and falls back when it finds nothing.
- [ ] **Step 2–4:** fail, implement, pass. No live LLM calls (the existing mocks).
- [ ] **Step 5: Gates** on `agents/estimate prompts/material_catalog.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: estimate generation reads the effective material catalog`.

### Task 11: Maple reads

**Files:**
- Modify: `platform/agents/material/service.py` (`_list_materials_via_api`, `_find_materials_by_name*`, `_resolve_target_material`, `_fetch_list_materials`, `list_materials_reply` → service with filters and counts pushed down; `_with_catalog_names` via `vocabulary`)
- Modify: `platform/agents/cross_resource.py` (`find_materials_by_name`), `platform/agents/conversation/record_names.py` (`"material"` kind), `platform/agents/conversation/name_lookup.py` callers for materials, `platform/agents/planner/named_kinds.py`, `platform/agents/planner/resolve.py` (`_load` for materials), `platform/agents/planner/execute_base.py` (`load_record` dispatches `Material` to `get_effective`), `platform/agents/planner/policy.py` (`_material_sizes`), `platform/agents/planner/execute_records.py` (`_in_category`), `platform/agents/planner/execute_estimates.py`, `platform/routers/agent_helpers/named_answers.py`, `platform/routers/agent_helpers/viewed_record.py` (drop the bare `Material.get`)
- Test: extend `tests/test_material_agent.py`, `tests/test_record_names.py`, `tests/test_catalog_name_lookup.py`, `tests/test_planner_resolve.py`, `tests/test_planner_execute_reads.py`, `tests/test_cross_resource_joins.py`, `tests/test_named_answers.py`

Rule (decision §11.8): Maple sees only the company's **visible** effective list for names, lists and counts. Ids Maple already carries (`last_listed_items`, `active_*_id`) resolve through `get_effective`, so a material hidden mid-conversation still answers "the second one".

- [ ] **Step 1: Failing tests:** "list materials" includes a standard item and its effective price; "how many materials" equals `count_effective`; a hidden standard isn't found by name; "which estimates use <standard name>" finds lines carrying the standard id; `_in_category` works for a standard line; "what sizes does X come in" reads standard sizes; another company's custom material is never named.
- [ ] **Step 2–4:** fail, implement, pass. Then run the planner suites these files feed: `./run_tests.sh tests/test_planner_execute_reads.py tests/test_planner_list_filters.py tests/test_planner_read_shapes.py`.
- [ ] **Step 5: Gates** on `agents routers/agent_helpers`.
- [ ] **Step 6: Commit (ask first)** — `feat: Maple reads the effective material catalog`.

### Task 12: Metrics, summaries and the cost backfill

**Files:**
- Modify: `platform/services/catalog_metrics.py` (`material_counts_by_category`, `_sizes` → one effective aggregation; extremes and averages on effective prices), `platform/services/maple_metrics.py` (`_line_units`), `platform/services/work_item_summary.py` (`resolve_inventory_names`), `platform/services/estimate_cost_backfill.py` (`_fetch_catalog` → `resolve_many` **per company**; the cross-company cache goes)
- Test: extend `tests/test_catalog_metrics.py`, `tests/test_metric_lines.py`, `tests/test_work_item_summary.py`, `tests/test_estimate_cost_backfill.py`

- [ ] **Step 1: Failing tests:** counts by category include standard items under the company's category name; most-expensive uses effective price; backfill fills a standard line's cost from the effective cost of **that line's company**, never another's.
- [ ] **Step 2–4:** fail, implement, pass.
- [ ] **Step 5: Leftover-reader check.** This must print nothing outside `services/material_catalog.py`, the migration script, models and tests:

```bash
cd platform && grep -rnE "Material\.(find|find_one|get|get_pymongo_collection)\b|\"materials\"\]|db\.materials" --include='*.py' . | grep -v -E "\.venv|tests/|services/material_catalog.py|scripts/migrate_materials_to_standard.py|models/"
```

  Any hit is either moved onto the service in this task or written into the commit message with the reason it stays.
- [ ] **Step 6: Gates** on `services`.
- [ ] **Step 7: Commit (ask first)** — `feat: metrics and backfills read the effective material catalog`.

---

# Phase E — Maple writes (minimum for stage 1)

### Task 13: Cost/price role gate and standard-item outcomes

Stage 4 adds the new phrasings and the duplicate offer. Stage 1 only makes existing commands safe once standard items are visible to Maple.

**Files:**
- Modify: `platform/agents/planner/policy.py` (new `_check_pricing`: `create_material`, and `update_material` with any of `cost`, `price`, `add_size`, `remove_size`, `rename_size`, `unit` → refuse for non-elevated roles with `manager_denial("change material prices")`), wired in `_check_rules`
- Modify: `platform/agents/material/service.py` (`_create_material_via_api` runs `_assert_own_catalog_refs` and `assert_name_available`; update on a standard id: cost/price → `set_size_pricing`, anything else → a plain refusal reply; `_deleter("material")` on a standard id → `set_hidden(True)`, reply "I've hidden <name> from your materials.")
- Modify: `documentation/development/maple-phrasing-reference.md` (rows whose reply changes: Member cost/price edits, delete of a standard material)
- Test: extend `tests/test_maple_catalog_writes_auth.py`, `tests/test_planner_policy.py`, `tests/test_planner_execute_writes.py`, `tests/test_planner_deletes.py`

- [ ] **Step 1: Failing tests:** a Member's "set black mulch cost to 22" is refused and writes nothing; an Owner's overrides the standard size; "add a size to <standard>" is refused and writes nothing; "delete <standard>" (after confirmation) hides it and it drops out of "list materials"; Maple create refuses a name a visible standard holds; a Member renaming a custom material still works.
- [ ] **Step 2–4:** fail, implement, pass. The policy gate runs before any execution, so a refused plan never reaches `update_material`.
- [ ] **Step 5: Gates** on `agents`.
- [ ] **Step 6: Commit (ask first)** — platform: `feat: Maple prices materials as Owner/Admin and hides standard ones on delete`; documentation: `docs: phrasing reference rows for standard material outcomes`.

---

# Phase F — Migration and documentation

### Task 14: `scripts/migrate_materials_to_standard.py`

**Files:**
- Create: `platform/services/material_migration.py`, `platform/scripts/migrate_materials_to_standard.py`
- Test: `platform/tests/test_material_migration.py` (new)

**Interfaces:** `async plan_company(company_id) -> CompanyMigrationPlan{identical: [(material_id, standard_id)], detached: [(material_id, standard_id)], custom: [material_id], line_rewrites: int, categories_to_enable: [oid], keys_to_backfill: int}`; `async apply_company(plan) -> CompanyMigrationReport`. CLI: `--company <id> | --all`, `--apply` (dry-run default), prints one report per company and a total.

Rules (design §10.1, decision §11.3):
1. Backfill `standard_key` onto the company's seeded categories and units by name.
2. Match each company material to a standard by `norm_name` **and** the same set of size names.
3. **Identical** — every size's cost equals the standard cost, and price equals the markup price or the seed's former price within one cent: rewrite `job_items[].materials[].material` from the copy id to the standard id on the company's estimates **and templates** (`persist_fields`, one audit entry per document), then delete the copy.
4. **Edited** — anything else differs (cost, price, description, sizes): keep it, set `derived_from`, hide the standard twin.
5. A company with any standard match gets every standard category enabled; others get none.
6. Idempotent: a second `--apply` finds nothing to do.

- [ ] **Step 1: Failing tests:** identical copy → deleted and its lines rewritten (snapshots untouched, totals unchanged); edited copy → kept, `derived_from` set, twin hidden, list shows one row; extra-size copy counts as edited; custom-only company → nothing enabled; dry-run writes nothing; second apply is a no-op; another company's estimates are never touched.
- [ ] **Step 2–4:** fail, implement, pass.
- [ ] **Step 5: Gates** on `services/material_migration.py scripts/migrate_materials_to_standard.py`.
- [ ] **Step 6: Commit (ask first)** — `feat: migrate company material copies onto the standard catalog`.

Running it on Dev and production is stage 3 and needs its own approval.

### Task 15: Rule file and docs

Docs only — no TDD.

**Files:**
- Create: `.claude/rules/materials.md` (paths: `platform/models/material*.py`, `platform/models/standard_material.py`, `platform/services/material_*.py`, `platform/routers/material*.py`, `platform/agents/material/**`): the three collections, "only `material_catalog` queries them", visibility = category on and not hidden, hidden never a permission boundary, Owner/Admin for every cost/price write, names unique across the effective list, duplicates named "<name> copy", standards are retired never deleted.
- Modify: `CLAUDE.md` domain-rules table (one row), `.claude/rules/pricing.md` (material row: un-overridden standard price is live; custom price is stored)
- Modify: the design doc's status line and the plans `README.md` index (this plan)

- [ ] **Step 1:** write the files.
- [ ] **Step 2: Commit (ask first)** — workspace root and documentation: `docs: material catalog rules and stage-1 plan status`.

---

## Done when

- Every task's tests pass and the scoped gates are clean.
- The leftover-reader grep in Task 12 prints nothing unexplained.
- A company onboarded with standard materials has no `materials` documents, sees the standard list paged and priced from its markup, and can override (Owner/Admin), hide, show, reset and duplicate.
- An existing company that still holds copies works unchanged until the migration runs (copies are custom materials; their lines resolve).
- Nothing is pushed. Stage 2 (portal) starts from the `GET /materials` envelope and the endpoints in Tasks 6–7.

---

## As built (2026-10-15)

Where the implementation departs from, or adds to, the tasks above:

- **Task 1.** `material_overrides` joined the test-data sweep list in
  `tests/conftest.py` (the coverage guard caught it), and the sweep also
  deletes `test-std-` standard materials.
- **Task 2.** `slug` / `norm_name` live in `services/material_keys.py` (the
  catalog re-exports `norm_name`). A repeated size with a different cost is an
  error, not a dropped duplicate.
- **Task 3.** Also fixed two pre-existing gaps: the category and unit PUT wrote
  the whole model, so an ordinary rename reset `standard_key` and
  `include_standard` (both now server-owned); and reload matched by name only,
  so a renamed seeded category would be seeded again beside itself (now by key
  first).
- **Task 4.** `list_effective` takes Maple's `price_filters` pairs (one size
  meets all), not min/max. `EffectiveMaterial` gained `category_name`,
  `EffectiveSize` gained `unit_name` and (Task 12) `price_recorded`. Measured on
  5,000 standards: searches and filters under 10 ms, an unfiltered page about
  47 ms (the override lookup runs per row before paging; moving it after paging
  for name sorts is the optimization if needed).
- **Task 5.** Also `materials_in_use`, `clear_overrides`, `delete_unused_custom`
  (used by Task 7), and `ids_by_exact_names`, `find_named` (Tasks 6 and 11).
- **Task 7.** Added `PATCH /materials/{id}/pricing` (per size; null clears) for
  the portal's per-size reset. A PUT on a standard writes only values that
  differ from what the company sees, so re-sent sizes don't become overrides.
  Upload rows naming a standard may leave cost blank. Fixed the pre-existing
  upload-test leak described above.
- **Task 10.** The ReAct lookup tool reads the visible catalog once per call and
  uses the matcher's synonym-aware word prefilter (from 200 rows), instead of a
  per-term name search that would lose synonyms.
- **Task 11.** Maple's Material Agent unit tests run on
  `tests/fake_material_catalog.py`. A count reply carries `count`, not every
  row. `load_record(Material, …)` returns the effective record.
- **Task 12.** The cost backfill used to read materials with no company filter;
  it now resolves each estimate's lines within its own company (roles too).
  Price figures still leave out a company material with no recorded price.
- **Task 13.** Refusal words live in `agents/role_utils.py`
  (`MATERIAL_PRICES_ACTION`, `MATERIAL_CREATE_ACTION`). The phrasing reference
  records the new outcomes as notes in §4.1, §4.6 and the delete-rules
  paragraph; the plans and phrasings are unchanged.
- **Task 14.** Checked on a local copy of the real seed: all 150 copies from
  the old loader are identical, 31 keys backfill, a second run is a no-op.
  `former_seed_prices` reads the seed's price column while it exists; once the
  new seed drops it, copies match on the markup price only — run the migration
  before replacing the seed file, or keep the old file for it.

