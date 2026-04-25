# Configurable Work Item Divisions

## Context

Today, Work Item divisions are a fixed 7-value Python enum (`EstimateDivision` in `platform/models/estimate.py:31-38`) that the React frontend mirrors as a hardcoded array (`ESTIMATE_DIVISIONS` in `portal/src/lib/workItemV2.ts:6-14`). Customers can't tailor the list to their own service mix. We're making divisions per-company configurable — same shape and UX as Material Categories — while keeping the existing enum-based agent/keyword inference logic intact for the original 7 defaults.

Decisions already locked in:
- **"Unknown"** is a frontend-only display fallback — never seeded, never stored.
- **Agent / keyword inference** keeps using the hardcoded 7 in `routers/estimates.py` and `agents/estimate/service.py`. Custom user-added divisions will be selectable in the UI but won't be auto-inferred from job descriptions (acceptable for v1).
- **`EstimateDivision` enum stays** but only as the seed source for the default CSV. `JobItem.division` becomes `Optional[str]` so any string from the configurable list is valid.

## Backend

### 1. Default CSV — new file
`platform/data/default_divisions.csv` (mirror format of `default_material_categories.csv`):
```csv
name,description
Design/Build,
Irrigation & Lighting,
Maintenance,
Snow & Ice,
Tree Care,
Turf & Plant Care,
Others,
```
Descriptions can stay blank for v1 (column kept for parity with material categories so the bootstrap helper doesn't need a special case).

### 2. New model — `platform/models/division.py`
Mirror `models/material_category.py` exactly:
- Fields: `name: str` (min_length=1), `description: Optional[str]`, `company: PydanticObjectId` (indexed), `created_at`, `updated_at` (auto-managed via `before_event(Insert, Replace)`).
- Collection name: `"divisions"`.
- Indexes: `[("company", ASCENDING)]`.

Register in:
- `platform/models/__init__.py` — add `Division` to exports.
- `platform/database.py` — add `Division` to `init_db()` document model list.

### 3. Bootstrap service — `platform/services/division_bootstrap.py`
Copy/adapt `services/material_category_bootstrap.py`. Public function `bootstrap_company_divisions(company_id)` reads `data/default_divisions.csv` and upserts per-company rows (idempotent name+company match, same as material categories).

Wire into `platform/services/company_service.py`:
- Import `bootstrap_company_divisions`.
- Add `(bootstrap_company_divisions, "divisions")` to the `always_bootstrap` list (line 40-43).

### 4. CRUD router — `platform/routers/divisions.py`
Copy `routers/material_categories.py` line-for-line. Differences:
- `prefix="/divisions"`, `tags=["divisions"]`.
- Replace `MaterialCategory` → `Division`.
- **Skip the "in-use" delete guard.** Unlike materials referencing a category by ObjectId, `JobItem.division` is just a string snapshot. Deleting a division leaves work items with the orphan name; UI will render those as "Unknown". This matches the user's stated fallback behaviour.
- Add `AuditAction` entries `DIVISION_CREATE / DIVISION_UPDATE / DIVISION_DELETE` and `ResourceType.DIVISION` to `models/audit_log.py` (or wherever those enums live — same place as `MATERIAL_CATEGORY_*`).

Register router in `platform/main.py` (next to `material_categories` router include).

### 5. Loosen `JobItem.division`
In `platform/models/estimate.py:233`:
```python
division: Optional[str] = None
```
(was `division: EstimateDivision = EstimateDivision.OTHERS`)

Audit every reference flagged in exploration and update accordingly:
- `routers/estimates.py` line 7 import + the `ESTIMATE_DIVISION_KEYWORDS` map (line 54-119) — leave keyword logic as-is, but where it assigns the inferred value, store the enum's `.value` string. Inference fallback stays `"Others"` (string literal) to match the seeded default name.
- `agents/estimate/service.py` lines 32, 544-552, 3301-3318 — same treatment, store strings.
- `agents/orchestrator/service.py` and `agents/orchestrator/help_handler.py:168` — these list valid divisions. **Change help_handler to query `Division` for the current company** so help text reflects the user's actual list.
- Tests under `platform/tests/test_estimate_*.py` and `test_work_item_summary.py` — replace `EstimateDivision.X` references with the literal string equivalents (or import the enum and use `.value`).

Keep the `EstimateDivision` enum class itself in `models/estimate.py` — the seed CSV is built from it conceptually, and the keyword-inference map keys off it.

### 6. Tests (TDD per CLAUDE.md)
New file `platform/tests/test_divisions_api.py` mirroring `test_material_categories_api.py` — create / list (alphabetical) / get / update / delete / 404 / cross-company access denied.

Bootstrap test in `platform/tests/test_company_service.py` (or wherever material category bootstrap is currently tested) — assert all 7 default division names exist after `create_company_with_bootstrap`.

Existing estimate tests stay green after the enum→string conversion.

## Frontend

### 7. API client — `portal/src/api/resources.ts`
Add `divisionsApi` exactly mirroring `materialCategoriesApi` (lines 116-134), and a `Division` type in `portal/src/types/api.ts` next to `MaterialCategory` (line 50-55).

### 8. Replace the hardcoded list
`portal/src/lib/workItemV2.ts:6-14` — delete the `ESTIMATE_DIVISIONS` constant. Audit imports of it (exploration found `WorkItemInlineContent.tsx:13-17`) and switch consumers to a fetched list.

In `portal/src/components/estimates/WorkItemInlineContent.tsx`:
- Add a `useEffect` that calls `divisionsApi.list(COMPANY_ID)` on mount and stores `Division[]` in local state.
- Replace `{ESTIMATE_DIVISIONS.map(...)}` (line 236-238) with the fetched list.
- For the value resolution: if `division` is null/undefined or doesn't match any fetched name, render `"Unknown"` as a disabled-or-special option and treat it as the displayed value. Keep the underlying state as the original string so saving doesn't accidentally overwrite a valid-but-deleted name.
- Default for *new* work items: first division in the fetched list, or `null` if the list is empty (UI shows "Unknown").

If multiple Work Item screens re-fetch divisions independently, consider lifting the fetch to a parent (`EstimatesPage` or a small `DivisionsContext`) — but only if existing patterns already do that for material categories. If material categories are re-fetched per dialog today, match that.

### 9. New Settings tab
`portal/src/pages/SettingsPage.tsx`:
- Add `{ id: "divisions", label: "Divisions" }` to the `tabs` array (line 297-304).
- Duplicate the entire Material Categories block — state (line 370-382), `fetchCategories` (line 540-552), CRUD handlers (line 1186-1243), tab render block (line 2394-2473), and dialog modal (line 2751-2810) — and rename `category/categories` → `division/divisions` throughout. Reuse `CategoryDetails`-style local interface with `name` + `description`.
- Permission gate: same `canManageResources` check used by Material Categories.

### 10. Tests
Add a frontend test mirroring existing material-categories tab coverage if any (run `rg -l "material.categor" portal/src` to find the pattern). At minimum: render the divisions tab, mock `divisionsApi.list`, verify list rows render and the Add/Edit/Delete dialogs invoke the API.

## Critical files

**Read / model after:**
- `platform/models/material_category.py` — model template
- `platform/services/material_category_bootstrap.py` — bootstrap template
- `platform/routers/material_categories.py` — router template
- `portal/src/api/resources.ts:116-134` — API client template
- `portal/src/pages/SettingsPage.tsx:2394-2473, 2751-2810` — settings-tab template

**Modify:**
- `platform/models/estimate.py` — loosen `JobItem.division` to `Optional[str]`
- `platform/models/__init__.py`, `platform/database.py` — register `Division`
- `platform/services/company_service.py` — wire bootstrap call
- `platform/main.py` — include divisions router
- `platform/routers/estimates.py`, `platform/agents/estimate/service.py`, `platform/agents/orchestrator/help_handler.py` — replace enum references with strings; help_handler queries DB
- `portal/src/lib/workItemV2.ts` — delete hardcoded constant
- `portal/src/components/estimates/WorkItemInlineContent.tsx` — fetch list, "Unknown" fallback
- `portal/src/pages/SettingsPage.tsx` — add tab
- `portal/src/types/api.ts` — add `Division` type

**Create:**
- `platform/data/default_divisions.csv`
- `platform/models/division.py`
- `platform/services/division_bootstrap.py`
- `platform/routers/divisions.py`
- `platform/tests/test_divisions_api.py`

## Verification

1. **Backend unit tests** (related only — per CLAUDE.md, don't auto-run full suite):
   ```bash
   cd platform && ./run_tests.sh tests/test_divisions_api.py tests/test_company_service.py tests/test_estimate_api.py tests/test_estimate_agent.py
   ```
2. **Bootstrap smoke test** — start the backend, create a new company via the existing onboarding flow, verify 7 division rows appear in MongoDB scoped to the new `company` ObjectId.
3. **End-to-end UI**:
   - `cd platform && uvicorn main:app --reload` and `cd portal && npm run dev`.
   - Open Settings → Divisions: list shows the 7 defaults. Add a custom division (e.g. "Hardscape"), edit its description, delete one of the defaults.
   - Open Estimates → create a Work Item: division dropdown reflects the live list including the new "Hardscape" and excludes the deleted one.
   - Manually edit a Work Item document in Mongo to a non-existent division name; reload UI — dropdown shows "Unknown" without crashing.
4. **Frontend tests**: `cd portal && npm test -- SettingsPage WorkItemInlineContent`.
