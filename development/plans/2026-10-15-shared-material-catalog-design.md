# Shared Standard Material Catalog — Design

**Date:** 2026-10-15
**Status:** Decided 2026-10-15 (§11). Stage 1 (platform) implemented 2026-10-15 — plan and as-built notes: [2026-10-15-shared-material-catalog-stage1-plan.md](2026-10-15-shared-material-catalog-stage1-plan.md). Stages 2–6 not started.
**Scope:** `platform/` + `portal/` + `documentation/`
**Related:** [`2026-06-06-settings-materials-actions-menus.md`](2026-06-06-settings-materials-actions-menus.md)
(load-standard / reload endpoints this design retires),
[`.claude/rules/pricing.md`](../../../.claude/rules/pricing.md) (cost vs. price
vs. markup — unchanged by this design, see §4.4)

---

## 1. Problem

Today every company that ticks "Use 3Maples standard materials" gets a **copy**
of the whole standard list written into its own `materials` documents
(`services/material_bootstrap.py::bootstrap_company_materials`). That was the
simplest thing when the list had 150 names, and it gives each company its own
cost and price per size. It stops working as the list grows:

- **Storage multiplies.** The seed is 150 materials / 369 sizes today. At the
  5,000-item target, 200 companies would carry a million size rows that are
  almost all identical.
- **Updates don't propagate.** A new or corrected standard material reaches an
  existing company only through "Load Standard" (`POST /materials/load-standard`),
  which *overwrites every same-name material back to the seed* — including the
  company's own cost and price edits. Nobody can safely run it twice.
- **Every reader loads the whole list.** `GET /materials` returns the entire
  catalog; the portal searches and filters it in the browser; the estimate
  pickers hold it in memory; Maple's Material Agent scans it in Python even to
  look a record up by id; AI generation loads it on every run. None of that
  survives 5,000 items.

The requirements (user, 2026-10-15):

1. One standard list, maintained once.
2. A company that opts in sees the standard materials without owning copies.
3. Cost and price are the company's own: initial cost = standard cost, price =
   cost × company `material_markup`.
4. A company can **duplicate** a standard material; the copy is detached and
   never follows standard updates.
5. A company can **hide/show** any standard material.
6. Owners/Admins choose **which standard categories** are available.
7. The list is **paginated, searchable and filterable**.
8. Restructure the data as needed; add anything else that's a good idea.

---

## 2. What the code depends on today (survey findings)

The three surveys (platform estimate path, Maple/agents, portal) agree on a
small set of load-bearing facts. The design has to preserve every one of them.

**The catalog id on an estimate line is the contract.**
`MaterialItem.material` (`models/estimate.py:245`) is the material's ObjectId
*as a string*, next to a snapshot of `name`, `unit` label, `size`, unit `price`
and unit `cost`. Totals, margins and documents read only the snapshot. The
catalog is consulted at **write time only**: AI generation sets price and cost
from it; manual saves take price and cost from the client and refresh only the
name/unit snapshot; templates and the cost backfill re-derive from it. Joins on
that string id are how "which estimates use Black Mulch?", line-total metrics,
`_in_category` and the delete in-use checks work.

**Two places reject any id that isn't the company's own:**
`routers/estimate_helpers/snapshots.py::assert_own_line_refs` (via
`dependencies.assert_company_refs`, used by estimates **and** templates) and
`_fetch_snapshot_maps`. A shared standard id fails both today.

**Every Maple read is `{company: X}`-scoped**, and most are name lookups that
lean on the `(company, name)` index: `find_records_named`, `exact_name` /
`same_name` / `exact_id` (`agents/conversation/name_lookup.py`),
`find_materials_by_name` (`agents/cross_resource.py`), the planner's
`load_record(Material)`, `_material_sizes`, `_in_category`. The Material Agent
(`agents/material/service.py`) loads the full catalog for list, resolve and
even id lookups, filters price in Python, and counts with `len()`.

**Categories and units are per-company documents**, seeded from
`data/default_material_categories.csv` (19) and `default_material_units.csv`
(12). The standard materials CSV names them by *name*. The portal's category
dropdowns and Maple's "in category X" all speak company category ids.

**Price is derived at write time and never re-derived.** `price = round(cost ×
(1 + markup/100), 2)` is computed when a size is written without a price
(`routers/materials.py::_normalize_size_entry`, mirrored in the portal and in
Maple). Changing `material_markup` later reprices nothing.

**The portal has no server-side list pattern for customers yet.** The only
paged tables are the staff ops pages (`{items, total, page, page_size}`,
300 ms debounced search). The closest server-backed picker is
`PropertySearchDropdown` (first 10 + debounced search + pinned selection).
`snapshotFallbackLabel` decides "(removed)" by *absence from the loaded list* —
wrong the moment the list is a page.

**Defects found along the way** (fixed by or alongside this work; §9):
the research prompt renders the category as an ObjectId hex string, not a
name; `template_bootstrap` snapshots the unit *id* rather than its label;
`AddMaterialGapDialog` hardcodes markup to 10; `estimate_cost_backfill`
fetches materials with no company filter; snapshots take the unit from
`sizes[0]` rather than the line's size; `DELETE /materials/{id}` has no in-use
check; Maple's create bypasses `_assert_own_catalog_refs`; the `materials-sample.csv`
header says `units` while the inline template says `unit`; there is no index
on `job_items.materials.material`; the seed CSV has four duplicate rows.

---

## 3. Design in one paragraph

A new global collection, **`standard_materials`**, holds the one list. Company
documents in **`materials`** keep holding only what the company created itself
(custom items, and copies detached from the standard). A small per-company
**`material_overrides`** collection records *only deviations* from the
standard: a hidden flag and per-size cost/price. Opt-in is a flag on the
company's existing **`MaterialCategory`** documents, which gain a
`standard_key`. One service, **`services/material_catalog.py`**, is the only
code that merges the three into the **effective catalog** a company sees —
paged, searched and filtered in one aggregation — and every reader (REST,
estimates, templates, Maple, metrics, backfills) goes through it. Estimate
lines keep storing a plain ObjectId string; for a standard material it is the
standard's id, identical for every company.

```
                 standard_materials (global, ops-maintained)
                 ┌──────────────────────────────────┐
                 │ key, name, category_key,          │
                 │ sizes[{size, unit_key, cost}]     │
                 └──────────────┬───────────────────┘
                                │  _id referenced by estimate lines
   material_overrides (company) │          materials (company-owned)
   ┌────────────────────────┐   │          ┌──────────────────────────┐
   │ company, standard,      │   │          │ company, name, category,  │
   │ hidden,                 │   │          │ sizes[{size,unit,cost,    │
   │ sizes[{size,cost?,price?}]  │          │        price}], hidden,   │
   └───────────┬────────────┘   │          │ derived_from?            │
               │                │          └────────────┬─────────────┘
               ▼                ▼                       ▼
        services/material_catalog.py  ── effective catalog (merge + markup)
               │
   ┌───────────┼───────────────┬───────────────┬─────────────────┐
   REST /materials   estimates/templates   Maple + planner   metrics/backfill
```

---

## 4. Data model

### 4.1 `standard_materials` (new, global — no `company`)

```python
class StandardMaterialSize(BaseModel):
    size: str
    unit_key: str          # → standard unit key (§4.4)
    cost: float            # 3Maples' reference wholesale cost

class StandardMaterial(Document):
    key: str               # stable slug, e.g. "black-mulch"; import upsert key
    name: str
    name_norm: str         # lower-cased, whitespace-collapsed; exact-match + dedupe
    description: Optional[str]
    category_key: str      # → standard category key (§4.4)
    sizes: List[StandardMaterialSize]  # min 1
    industries: List[CompanyIndustry] = []   # optional tagging (§8.1)
    retired_at: Optional[datetime] = None    # soft-retire; never hard-delete
    version: int = 1       # bumped on every content change
    created_at / updated_at

    indexes: key unique; name_norm; (category_key, name); retired_at
```

- **No `price` column.** The standard carries a cost; price is always the
  company's markup applied to the effective cost (§4.5). The current CSV's
  `price` column is dropped on import (decision §11.7).
- **Never deleted.** Retiring keeps every existing estimate line resolvable
  (name/price snapshots still render, `resolve` still returns it) and drops it
  from lists and search. Companies that overrode or hid it are untouched.
- `key` makes CSV re-imports idempotent: the `_id` lines reference never
  changes when a name is corrected.

### 4.2 `materials` (existing, company-owned) — two new fields

```python
class Material(Document):
    ...existing fields...
    hidden: bool = False                         # hide/show for custom items too
    derived_from: Optional[PydanticObjectId] = None   # standard it was duplicated from (provenance only)
```

Nothing else changes: a company material still references the company's own
category and unit ids, still stores cost **and** price per size, still goes
through `_normalize_material_payload`.

`derived_from` is informational ("Duplicated from standard *Black Mulch*") and
lets "Reset to standard" offer to re-link later. It creates **no coupling**:
standard updates never touch a detached copy (requirement 4).

### 4.3 `material_overrides` (new, per company × standard)

```python
class MaterialSizeOverride(BaseModel):
    size: str                  # matches StandardMaterialSize.size
    cost: Optional[float] = None
    price: Optional[float] = None

class MaterialOverride(Document):
    company: PydanticObjectId
    standard: PydanticObjectId  # → StandardMaterial._id
    hidden: bool = False
    sizes: List[MaterialSizeOverride] = []
    updated_at

    indexes: (company, standard) unique; (company, hidden)
```

- Created **lazily**, only when a company first hides or re-prices a standard
  item. A company that accepts the standard as-is has zero override documents
  no matter how big the list is.
- Deleted when it carries nothing (not hidden, no size with a value) — "Reset
  to standard" is a delete.
- A size override whose `size` no longer exists on the standard is ignored
  (and reported by the ops drift report, §8.4). A new standard size simply
  falls back to standard cost × markup.

### 4.4 Categories and units: keep them per-company, add a key

`MaterialCategory` and `MaterialUnit` stay exactly where the portal and Maple
expect them. Two fields are added to each:

```python
standard_key: Optional[str] = None   # set on seeded docs; None on company-created ones
include_standard: bool = False       # MaterialCategory only — the opt-in (requirement 6)
```

The seed CSVs gain a `key` column. `standard_materials.category_key` /
`sizes[].unit_key` are validated against those keys at import.

Why not a global category collection: the effective catalog has to answer
"category = X" with a *company* category id, because every dropdown, every
`MaterialItem` writer and Maple's `_in_category` already use that id space.
Mapping `standard_key ↔ company category id` is a ≤30-row in-memory table per
request; two id spaces in the UI would be a permanent source of bugs.

**Two levels of opt-in, and how they compose (decision §11.2):**

| Level | Where | Who | Effect |
|---|---|---|---|
| Category opt-in | `MaterialCategory.include_standard` | Owner/Admin | The category's standard materials appear in the company's list, search, pickers and Maple. Off = none of them do. |
| Item opt-out | `MaterialOverride.hidden` | Owner/Admin | One standard material drops out of list, search, pickers and Maple while its category stays on. |

A standard item is **visible** iff its category is enabled **and** it is not
hidden. The two flags never write each other: turning a category off leaves
every per-item hide in place, so turning it back on restores exactly the
previous view. Hidden and category-disabled items both still **resolve** on
existing estimate and template lines (§5), and a hidden item is listed under
*Show hidden* so it can be shown again. "Reset standard materials" (§6.3) is
the only thing that clears per-item hides in bulk.

Consequences:
- Enabling a category whose seeded doc the company deleted (or that was added
  to the standard after they signed up) **re-creates** the doc from the seed —
  same path as today's `_ensure_referenced_categories_and_units`, run on
  enable rather than on every read.
- A category or unit with a `standard_key` **cannot be deleted** while any
  standard material references it; it can be renamed (the company's label is
  theirs) and the category can be toggled off. Custom ones delete as today.
- "Reload Standard Categories/Units" survives unchanged in meaning: refresh
  descriptions, add any new standard ones, optionally drop unused custom ones.

### 4.5 The effective record

What every consumer sees for one material, regardless of where it lives:

```python
class EffectiveMaterial(BaseModel):
    id: str                      # standard _id or company material _id — what lines store
    name, description
    category: PydanticObjectId   # company category id (mapped for standard items)
    sizes: List[EffectiveSize]   # size, unit (company unit id), cost, price,
                                 #   standard_cost (standard items only), overridden: bool
    company: PydanticObjectId    # always the caller's — existing readers keep working
    source: Literal["standard", "custom", "detached"]
    standard_id: Optional[str]   # == id for standard; derived_from for detached
    hidden: bool
    retired: bool                # standard items only
    updated_at
```

Pricing rule (the only place it lives, `material_catalog.effective_sizes`):

```
standard item:  cost  = override.cost  ?? standard.cost
                price = override.price ?? round(cost × (1 + company.material_markup/100), 2)
custom item:    cost, price as stored (unchanged)
```

For a standard item that nobody has touched, **price follows the company's
markup live**. That is new (today a markup change reprices nothing) and it is
what requirement 3 literally asks for. Estimates are unaffected — they
snapshot price at write time, by design. Overriding a price pins it. See
decision §11.1.

---

## 5. The service: `services/material_catalog.py`

One module, no Mongo access to materials anywhere else. Signatures:

```python
async def enabled_category_keys(company) -> dict[str, PydanticObjectId]   # standard_key → company category id
async def list_effective(company, *, search=None, category=None,          # company category id
                         source=None,        # "standard" | "custom" | "all"
                         visibility="visible",   # "visible" | "hidden" | "all"
                         sort="name", page=1, page_size=50) -> Page[EffectiveMaterial]
async def get_effective(company, material_id) -> EffectiveMaterial | None  # works for either id space
async def resolve_many(company, ids) -> dict[str, EffectiveMaterial]       # hidden + retired included
async def find_by_name(company, text, *, exact=False, limit=10) -> list[EffectiveMaterial]
async def iter_effective(company, *, fields=...) -> AsyncIterator[EffectiveMaterial]   # projection-light, for AI inventory + metrics
async def count_effective(company, **filters) -> int
# writes
async def set_size_pricing(company, standard_id, size, *, cost=None, price=None)   # override; prunes empty docs
async def set_hidden(company, material_id, hidden)                                 # override or Material.hidden
async def duplicate(company, material_id, *, name=None) -> Material          # "<name> copy" unless name given
async def reset_to_standard(company, standard_id)                                  # delete override
```

`list_effective` is one aggregation on `standard_materials`:

```
$match  { category_key: {$in: enabled}, retired_at: null, <search regex on name/description> }
$lookup material_overrides on (standard = _id, company)      → ov
$addFields source:"standard", hidden: ov.hidden, sizes: merged cost/price (markup applied with $multiply/$round)
$unionWith materials [ $match {company, <search regex>, category?}, $addFields source: custom|detached ]
$match  hidden filter, source filter, (price filters for Maple)
$sort   name_norm, _id
$facet  { total: [$count], items: [$skip, $limit] }
```

Search is an escaped, case-insensitive `$regex` on `name` and `description`,
the same approach as tasks, estimates and properties. At 5,000 standard rows a
regex scan over the enabled categories is single-digit milliseconds; Atlas
Search is the upgrade path (§8.3), not a prerequisite.

Computing effective cost/price *inside* the pipeline (not after paging) is
what lets Maple's "materials under $50" and "most expensive material" stay
database-side instead of loading everything, and lets the list sort by price.

`resolve_many` is two `$in` queries (standard by `_id`, company by `_id` +
`company`) plus one override lookup — the replacement for every
`Material.find({_id: {$in}, company})` the surveys found. It deliberately
returns hidden and retired items: a line on an estimate must always resolve.
**Hidden is a list/search concern, not a permission boundary.** Standard rows
are global and contain nothing tenant-specific; the override is the only
tenant data and it is always queried by `company`.

### 5.1 Who moves onto the service

| Today | After |
|---|---|
| `routers/materials.py` `GET /` full list | `list_effective` (§6.1) |
| `snapshots._fetch_snapshot_maps`, `enrich_job_items_in_place` | `resolve_many` — and take the unit from the **line's** size, not `sizes[0]` (bug fix) |
| `snapshots.assert_own_line_refs` → `assert_company_refs(Material…)` | `assert_line_refs_resolvable`: every id is a non-retired standard **or** the company's own material. Equipment/labour/rate-card checks unchanged. |
| `agents/estimate/service._fetch_materials_inventory`, `tools.lookup_materials` | `iter_effective` (id, name, description, category *name*, sizes) — fixes the ObjectId-as-category bug |
| `agents/material/service.py` list / resolve / find-by-name / count / price filters | `list_effective` / `get_effective` / `find_by_name` / `count_effective` with filters pushed down; `len()` counts go away |
| `cross_resource.find_materials_by_name`, `record_names.find_records_named("material")`, `name_lookup.exact_name/exact_id/same_name`, `named_kinds._lookup_name_kinds` | `find_by_name(exact=…)` — both id spaces, enabled categories only, hidden excluded |
| `planner/policy._material_sizes`, `execute_base.load_record(Material)`, `execute_records._in_category`, `execute_estimates` material filter, `viewed_record` | `get_effective` / `resolve_many` |
| `services/catalog_metrics` (`_sizes`, counts by category, extremes, averages) | one `iter_effective` / aggregation with effective prices |
| `services/maple_metrics._line_units`, `work_item_summary.resolve_inventory_names`, `estimate_cost_backfill._fetch_catalog` | `resolve_many` (also fixes the backfill's missing company filter) |
| `template_bootstrap` name resolution; `routers/templates` ref check | `find_by_name(exact=True)`; `assert_line_refs_resolvable` |
| category/unit delete in-use checks | custom category/unit: company materials only (as today); standard-keyed: refuse while referenced (§4.4) |

Everything in the right column is one of six functions. That is the whole
point of the service: the next catalog change is one file, not twenty.

---

## 6. API

### 6.1 Listing — breaking change, shipped with the portal

```
GET /materials?company=&search=&category=&source=all|standard|custom
              &visibility=visible|hidden|all&sort=name|-name|price|-price
              &page=1&page_size=50          (page_size ≤ 100)
→ { items: EffectiveMaterial[], total, page, page_size }
```

Envelope follows the ops pages (`routers/ops.py`) — the one existing paged
table with page controls — rather than the `limit` + `X-Total-Count` header
the estimate and task lists use, because Maple's `show_more` wants
`page`/`total` too. Decision §11.5.

The old "whole catalog as a bare array" shape goes away. Platform and portal
ship together via `/release app`; during the window before the portal is
promoted the endpoint returns the old array when **no** paging/search
parameter is present, and the envelope otherwise. The compatibility branch is
removed in the following release.

### 6.2 Reads

```
GET  /materials/{id}                 → EffectiveMaterial (standard or company id; hidden ok; 404 if neither)
GET  /materials/resolve?ids=a,b,c    → { [id]: EffectiveMaterial }  (hidden + retired included; estimate pages)
POST /materials/lookup-names         { names: [...] } → { [name]: id | null }   (gap suppression, CSV preview)
GET  /material-categories            + standard_key, include_standard on each row
```

### 6.3 Writes

| Endpoint | Standard item | Company item | Role |
|---|---|---|---|
| `POST /materials/` | — | create custom (name must not collide with a *visible* standard, §6.5) | Owner/Admin when sizes carry cost/price (always, on create) |
| `PUT /materials/{id}` | only `sizes[].cost` / `sizes[].price` accepted → override; any other field → `409 {detail: "standard material; duplicate it to edit", action: "duplicate"}` | sparse patch as today | `sizes` in the patch → Owner/Admin; name/description/category only → any role |
| `POST /materials/{id}/duplicate` `{ name? }` | copy → company material named **"<name> copy"** (or `name` if given and unique), `derived_from` set | plain copy, same naming (replaces the portal's client-side duplicate) | Owner/Admin (it writes cost/price) |
| `PATCH /materials/{id}/visibility` `{ hidden }` | override.hidden | Material.hidden | Owner/Admin |
| `DELETE /materials/{id}/overrides` ("reset to standard") | delete override | — | Owner/Admin |
| `DELETE /materials/{id}` | `409` → use visibility | refuse with `409` when any estimate or template line references it (new in-use check); suggest hide | Owner/Admin |
| `DELETE /materials/?company=` | — | custom materials not in use; reports skipped | Owner/Admin |
| `PATCH /material-categories/{id}` `{ include_standard }` | toggles one category; enabling ensures seeded category/unit docs exist | Owner/Admin |
| `POST /material-categories/standard` `{ include_standard: bool }` | enable/disable all | Owner/Admin |
| `POST /materials/load-standard` | **retired**. Replaced by: enable-all categories + `POST /materials/reset-standard { clear_overrides, remove_unused_custom }` | Owner/Admin |
| `POST /materials/upload` | rows whose name exactly matches an **enabled, visible standard** write a size override (cost/price) instead of creating a duplicate; all other rows create/update custom materials as today | Owner/Admin (was: any) |

**Role rule (decision §11.4):** any write that sets a size's cost or price is
Owner/Admin — overrides, custom sizes, duplicate, CSV upload, and Maple's
cost/price commands. Today any role can edit a material; this tightens it,
and the portal hides the cost/price inputs (and Duplicate) from Members
rather than letting the server refuse. Enforcement is one dependency on the
server, `assert_is_manager`, applied per endpoint or, for `PUT`, when the
patch contains `sizes`.

Every write is audit-logged with the existing `MATERIAL_*` actions plus three
new ones: `MATERIAL_OVERRIDE` (price/cost/reset), `MATERIAL_VISIBILITY`,
`MATERIAL_CATEGORY_STANDARD_TOGGLE`.

### 6.4 Ops (staff) — the standard list has to be editable somewhere

```
GET    /ops/standard-materials?search=&category=&retired=&page=        (ops_viewer+)
POST   /ops/standard-materials/import   (CSV, upsert by key, dry_run=true preview)   (ops_admin+)
PATCH  /ops/standard-materials/{id}     (name, description, category_key, sizes, industries)
POST   /ops/standard-materials/{id}/retire | /unretire
GET    /ops/standard-materials/drift    (overrides pointing at sizes that no longer exist)
```

`data/default_materials.csv` stops being read at runtime. It becomes the seed
for `scripts/seed_standard_materials.py` (idempotent, by `key`, used by tests
and by the first deploy) and the ops import accepts the same columns.

### 6.5 Name uniqueness in the effective list

A company's visible list must not show two "Black Mulch" rows, or Maple's
"update black mulch cost" becomes a which-one question for every company that
duplicated. Rules (decision §11.8):

- Names are unique, case-insensitively, across the company's **effective**
  list: its own materials plus the visible standard ones.
- `duplicate` names the copy **"<name> copy"** (then "<name> copy 2", …), so a
  duplicate never collides. The user renames it afterwards if they like.
- Creating, renaming or uploading a custom material to a name that matches a
  visible standard, or another custom material, returns `409` with the
  colliding record. Hidden standards and disabled categories don't count, so
  re-showing a standard whose name a custom item took is refused with the
  same `409` the other way, naming the custom item.
- Maple resolves names against the same effective list and nothing else: a
  hidden or category-disabled standard is, to Maple, a material the company
  doesn't have.

Templates already enforce unique `(company, name)`; this extends the idea to
the merged view.

---

## 7. Portal

### 7.1 Materials page (`src/pages/MaterialsPage.tsx`)

- Server-driven: search (300 ms debounce), category select, **Source**
  (All / Standard / My materials), **Show hidden** toggle, sort, page
  controls. State lives in the URL (`?q=&category=&source=&hidden=&page=`)
  so the back button and `?open=<id>` deep links work; `?open=` now fetches
  `GET /materials/{id}` and opens the row's dialog instead of needing it on
  the page.
- Row badges: **Standard** / **Standard · priced** (has override) /
  **Hidden** — the company's own materials and copies of a standard carry
  none (decision 2026-10-17). A standard row's cost/price inputs
  show the standard cost as a hint and an "↺ standard" reset per size.
- Edit dialog on a standard item: name, description, category and size list
  read-only, cost/price editable (Owner/Admin), with one call-to-action,
  **Duplicate to edit**, which creates "<name> copy" and opens it.
- Members see every row read-only: no cost/price inputs, no Duplicate, no
  Upload. They can still open a material and read it.
- Row menu: Edit · Duplicate · Hide/Show · Reset to standard · Delete
  (custom only, disabled with a tooltip when in use).
- Page menu: Upload CSV · Reset standard materials · Delete all my materials.
  "Load Standard" disappears.
- A small `Pagination` component and a `useDebouncedValue` hook go in
  `src/components/common/` / `src/hooks/` — neither exists yet, and the
  ops pages' inline versions can adopt them later.
- Mobile stays read-only, as today, but gets the same search/pager.

### 7.2 Settings → Material Categories

A **Standard** column: seeded categories show a toggle (`include_standard`);
custom ones show "—". Header menu gains "Enable all standard" / "Disable all
standard". Delete is disabled on standard-keyed rows with a tooltip. Units tab:
delete disabled on standard-keyed units referenced by standard materials.

### 7.3 Onboarding

"Use 3Maples standard materials list" enables all standard categories
(pre-ticked to the company's `industry` tags once §8.1 lands) instead of
copying rows. The CSV path is unchanged. The phone path's "Use Standard List"
becomes the same enable-all call.

### 7.4 Estimate and template pickers

- `MaterialsTable` and `AddMaterialGapDialog` switch from the full-list
  `SearchableSelect` to a `MaterialSearchDropdown` modelled on
  `PropertySearchDropdown`: first 10 visible items, debounced `search`, and
  the selected line pinned by `GET /materials/{id}`.
- `NewEstimateWithActivityPage` and `TemplatesTab` stop loading the catalog.
  They call `GET /materials/resolve?ids=` once for the lines on screen; that
  map feeds `getMaterialById`, size dropdowns and the checklist.
- `snapshotFallbackLabel`: "(removed)" is decided by **absence from the
  resolve map**, never from the picker's items. A hidden or retired item
  renders as its snapshot name with a muted "(hidden)" / "(retired)".
- `buildEstimateInventoryGaps` name-suppression → `POST /materials/lookup-names`
  for the gap names (one call per estimate load, not per keystroke).
- `AddMaterialGapDialog` reads the company's real `material_markup` (bug fix).

### 7.5 Financial tab

Help text under Material Markup gains one line: "Applies to every standard
material you haven't priced yourself (N items); your own materials keep the
price you saved." The count comes from `count_effective(source=standard,
overridden=false)`.

---

## 8. Other good ideas (included or staged)

### 8.1 Industry-tagged standard categories (include)
`CompanyIndustry` already exists on `Company`. Tagging standard materials (or
categories) with industries lets onboarding pre-tick the right categories for
a roofer vs. a landscaper and lets ops grow the list for a new industry
without every landscaping company seeing roofing shingles.

### 8.2 "Your price list" CSV upload (include — §6.3)
Uploading a CSV whose names match standard items becomes the fastest way for a
company to load supplier pricing onto the standard list without owning copies.

### 8.3 Atlas Search for search and for AI matching (stage 2)
The test container is `mongodb-atlas-local` specifically for `$search` parity.
A single search index on `standard_materials` + `materials` gives
typo-tolerant search for the portal and Maple, and — more importantly —
replaces the O(labels × catalog) Python `SequenceMatcher` in
`agents/estimate/catalog_matching.py`, which at 5,000 items × 30 labels per
generation is seconds of CPU. Interim mitigation in stage 1: prefilter
candidates with `find_by_name` on each label's significant tokens, then
fuzzy-score only those.

### 8.4 Standard-change visibility (stage 2)
Because `version` bumps on every standard edit, a company can be shown "12
standard materials changed since you last looked" and ops can see which
overrides point at sizes that no longer exist (`/ops/standard-materials/drift`).
No subscription or notification plumbing in stage 1.

### 8.5 Apply the same pattern to labour roles and templates (later)
`default_labours.csv` and `default_templates.json` have the identical copy
problem at a smaller scale. Templates already reference materials by name;
with standard materials sharing ids, a shared template could reference them by
`key`. Out of scope here; the service boundary is designed so it can follow.

---

## 9. Maple

Maple keeps working through the service with no phrasing change for reads
("list materials", "how many materials", "materials under $50", "which
estimates use black mulch", "what sizes does X come in", counts by category).
Writes change meaning on standard items:

| Phrasing | Standard item | Custom item |
|---|---|---|
| "set black mulch cost to 22" / "price to 30" | override that size — **Owner/Admin**, via `assert_manager_role` like delete | write the size — **Owner/Admin** (was any role) |
| "add a 2 yd size to black mulch", "rename X", "move X to Drainage", "describe X as …" | refuse with offer: *"Black Mulch is a standard material, so its sizes can't change. Want me to make you a copy — Black Mulch copy — and add the size there?"* → `duplicate` + the edit (Owner/Admin) | as today; size edits Owner/Admin |
| "delete black mulch" | *"Black Mulch is standard, so I'll hide it from your list instead."* → hide, after the usual confirmation (Owner/Admin) | delete; refused with the in-use reason when estimates/templates use it |
| new: "hide X", "show X again", "show hidden materials", "reset X to standard", "is X standard?", "turn on the Irrigation standard materials" | hide / unhide / list hidden / reset override / answer / toggle category | — |

Each new phrasing gets rows in `maple-phrasing-reference.md` (the test source)
before implementation, per the phrasing-reference rule. The planner's
`WRITE_OPS` gain `hide_material`, `show_material`, `reset_material`,
`toggle_standard_category`; `delete_material` on a standard id is rewritten
to `hide_material` in `execute_records._deleter` so the confirmation copy is
honest. Maple's create goes through the router's `_assert_own_catalog_refs`
(bug fix) and the uniqueness rule in §6.5.

---

## 10. Migration and rollout

### 10.1 Existing company copies
`scripts/migrate_materials_to_standard.py --company <id>|--all [--apply]`
(dry-run by default, prints a per-company report):

1. Match each company material to a standard by `name_norm` **and** identical
   size names.
2. **Identical copy** (sizes' costs equal the standard, prices equal the
   markup-derived price or the seed's price column): delete the copy and
   rewrite every estimate and template line `material: <copy id>` to the
   standard id via `persist_fields` (precedent: `backfill_estimate_line_costs`).
   Snapshots are untouched; one audit entry per estimate.
3. **Edited copy** (any cost/price/description differs, extra or fewer sizes):
   keep it as a **detached** custom material (`derived_from` set), and hide
   the standard twin so the list shows one row. The company gets exactly what
   it has today and can "reset to standard" later.
4. Enable all standard categories for any company that had at least one
   standard-named material; enable none for the rest.
5. Add the `job_items.materials.material` index while here.

Rule 2 is the only step that touches estimates. It is safe because every
reader uses the snapshot, and the id it writes resolves for every company.
Decision §11.3.

### 10.2 Sequence
1. **Platform, stage 1** — models + indexes, `seed_standard_materials.py`,
   `material_catalog` service, new/changed endpoints (with the compatibility
   branch on `GET /materials`), readers moved onto the service (§5.1), the
   migration script in dry-run, tests. Nothing user-visible changes until the
   portal ships; existing copies keep working because company materials still
   resolve.
2. **Portal** — §7. `/release app` promotes both.
3. **Migration** — dry-run on Dev, review the report, `--apply` on Dev, then
   production in the same release window.
4. **Maple** — §9 phrasings and planner ops; parity run before the push (the
   live parity suite costs ~$1.50 and runs only when asked).
5. **Ops UI + import** — §6.4; until then ops seeds via the script.
6. **Cleanup** — remove the compatibility branch, `bootstrap_company_materials`,
   `remove_non_standard_materials`, the runtime read of `default_materials.csv`,
   and the portal's client-side duplicate helper.

### 10.3 Tests
TDD per CLAUDE.md. New suites: `test_material_catalog_service.py` (merge,
markup, hidden, retired, uniqueness, paging/facets, both id spaces),
`test_materials_api_paged.py`, `test_material_overrides_api.py`,
`test_material_migration.py` (dry-run report, identical vs. edited copies,
line rewrite), ops import; portal: `MaterialsPage` paging/filters/URL state,
`MaterialSearchDropdown`, `snapshotFallbackLabel` against a resolve map,
`MaterialCategoriesTab` toggle. Existing suites that assert a bare array from
`GET /materials` or the "(removed)" rule are updated, not left stale.

---

## 11. Decisions (Simon, 2026-10-15)

1. **Live markup for untouched standard items** (§4.5) — **yes.** An
   un-overridden standard size's price is computed from the company's
   markup at read time. Custom materials keep stored prices.
2. **Two levels of opt-in** (§4.4, §4.3) — **both.** A company opts **in** per
   standard category (`MaterialCategory.include_standard`) and opts **out**
   per standard item (`MaterialOverride.hidden`). Disabling a category hides
   everything in it without touching per-item hides; re-enabling it brings
   back exactly what was visible before.
3. **Migration rule for edited copies** (§10.1) — keep the copy as a
   detached custom material and hide its standard twin.
4. **Role gates** — **every cost/price write is Owner/Admin**: standard
   overrides, a custom material's size costs/prices, the CSV upload and
   Maple's "set X cost to …". This tightens today's any-role material edit.
   Name, description and category edits on custom materials stay any role,
   as today. Hide/show, category toggles, reset and delete: Owner/Admin.
5. **Pagination envelope** `{items, total, page, page_size}` (§6.1).
6. **"Delete" on a standard item hides it** in the portal and in Maple
   (§6.3, §9).
7. **Drop the seed's `price` column** — the seed CSV is being updated.
8. **Names are unique across the company's effective list** (§6.5). Maple
   only ever sees materials accessible to the company (enabled categories,
   not hidden). A duplicate is named **"<name> copy"**, which is what the
   portal's `getDuplicateMaterialName` already does.
