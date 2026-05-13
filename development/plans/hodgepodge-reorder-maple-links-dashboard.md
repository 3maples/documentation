# Hodgepodge: Reorder + UI polish + Maple links + Dashboard windowing

## Context

Five loosely related improvements requested in one batch:

1. Users can't reorder card items / line items in Rate Cards, Templates, and Work Items — items stick in insertion order.
2. The Rate Card name field doesn't auto-focus on create, costing a click and making it easy to save with the placeholder name.
3. When Maple returns an object in chat, the object name is plain text — users can't jump to it.
4. Dashboard headline metrics ("Total Pipeline", "Draft Value", "Won This Month") aren't time-scoped and the label "Won This Month" is misleading once we re-window.
5. The "Estimate Value by Divisions" and "Estimate Value by Status" charts have no time-period control, and the dashboard currently computes everything client-side from the full estimate list — won't scale.

The intent is to ship all five as cohesive UX/analytics polish.

---

## 1. Reorder items in Rate Card / Template / Work Item

### Files
- `portal/src/components/settings/RateCardsTab.tsx` (state at line 32, render at 336–423)
- `portal/src/components/estimates/WorkItemInlineContent.tsx` (state at lines 61–62; used by both `TemplateDialog.tsx` and `WorkItemDialog.tsx` — one edit covers both UIs)
- `portal/src/components/estimates/MaterialsTable.tsx` (row render 163–188)
- `portal/src/components/estimates/ActivitiesTable.tsx` (row render 204–231)

### Approach
Add a tiny shared helper rather than duplicating logic three times:

```ts
// portal/src/lib/arrayReorder.ts
export const moveItem = <T,>(arr: T[], from: number, to: number): T[] => {
  if (to < 0 || to >= arr.length || from === to) return arr;
  const copy = [...arr];
  [copy[from], copy[to]] = [copy[to], copy[from]];
  return copy;
};
```

In each table, append two icon buttons to the row's action column (next to the existing remove button):
- **▲** disabled when `idx === 0`, calls `setRows(prev => moveItem(prev, idx, idx - 1))`
- **▼** disabled when `idx === rows.length - 1`, calls `setRows(prev => moveItem(prev, idx, idx + 1))`

Use the existing button styling already in those rows. State shape stays identical — no schema, no persistence change needed (order is positional in the array, which is what gets serialized on save).

### Tests
- `portal`: add a test for `moveItem` covering swap, no-op at bounds, identity.
- Component tests: assert clicking ▲/▼ on row 1/last is a no-op; clicking ▲ on the second row swaps with the first (check via row text content).

---

## 2. Auto-focus + select Rate Card name on create

### File
- `portal/src/components/settings/RateCardsTab.tsx` — the name `<input>` in the create form.

### Approach
Add a `ref` to the name input. In the create-form mount effect:
```ts
useEffect(() => {
  if (isCreating && nameInputRef.current) {
    nameInputRef.current.focus();
    nameInputRef.current.select();
  }
}, [isCreating]);
```

If create is rendered inline (not via a separate route) the `isCreating` state already exists — wire from that. If create is a separate component, run on mount unconditionally.

### Tests
Component test: after clicking "New Rate Card", `document.activeElement` is the name input and its `selectionStart/selectionEnd` cover the full placeholder.

---

## 3. Clickable objects in Maple responses

### Decision
Use `?open=<id>` query-param links — keeps the existing modal UX, no new routes needed.

### Backend files
- `platform/agents/orchestrator/service.py`
- `platform/agents/property/service.py`
- `platform/agents/contact/service.py`
- `platform/agents/material/service.py`
- `platform/agents/labour/service.py`
- (Estimate already has detail routes; use `/estimates/:id`.)

The CRUD response templates in CLAUDE.md (Get / Create / Update / List) already include the object name. Wrap the name in markdown link syntax at the point the response string is built. Add a small shared helper:

```python
# platform/agents/text_utils.py
LINK_PATH = {
    "property": "/properties",
    "contact": "/contacts",
    "material": "/materials",
    "labour":   "/people",
    "estimate": "/estimates",
}

def object_link(resource: str, obj_id: str, label: str) -> str:
    base = LINK_PATH[resource]
    if resource == "estimate":
        return f"[{label}]({base}/{obj_id})"
    return f"[{label}]({base}?open={obj_id})"
```

Apply in each domain agent's Get/Create/Update/List response builders. For List, link each individual label.

### Frontend files
- `portal/src/pages/PropertiesPage.tsx`, `ContactsPage.tsx`, `MaterialsPage.tsx`, `PeoplePage.tsx` (the four list pages)
- `portal/src/components/Layout/MapleMarkdown.tsx` already renders markdown links via ReactMarkdown — **no change needed** there.

In each list page, on mount, read `?open=<id>` from the URL (`useSearchParams`). If present, find the matching record (already loaded by the page) and open the existing edit/detail modal with it. After opening, clear the param via `setSearchParams({})` so refresh/back doesn't re-trigger.

### Tests
- `platform/tests/test_maple_crud_coverage.py`: extend a representative Get/Create/Update assertion to check the response contains a `[name](/path?open=id)` markdown link for non-estimate resources and `[name](/estimates/id)` for estimates.
- `portal`: test that mounting `PropertiesPage` with `?open=<id>` triggers the modal open handler.

### Note on phrasing reference
Per CLAUDE.md, any change that affects Maple's user-visible response strings means [`documentation/development/maple-phrasing-reference.md`](documentation/development/maple-phrasing-reference.md) needs the same-PR update (template wording changes from `'{name}'` to `[{name}](...)`).

---

## 4 + 5. Dashboard: rename, 30-day window, period dropdowns

### Frontend file
- `portal/src/pages/DashboardPage.tsx` (cards lines 134–147; division chart 301–339; status chart 342–391)
- Helpers stay reusable but are now driven by API data:
  - `portal/src/lib/wonThisMonth.ts` — rename to `wonValue.ts` (or leave file, just rename export); the helper is no longer needed if the BE returns the value, but keep it for the count fallback if the API only returns sums.
  - `portal/src/lib/divisionResolve.ts`, `portal/src/lib/pipelineStatus.ts` — can stay, but division/status rollups now come from the API rather than being recomputed.

### Backend: new endpoint
Add `GET /estimates/analytics` to `platform/routers/estimates.py`:

```
GET /estimates/analytics?company=<id>&period=<month|quarter|year>
```

Response:
```json
{
  "headline": {
    "total_pipeline": 0,
    "draft_value": 0,
    "won_value": 0,
    "window_days": 30
  },
  "by_division": [{"division": "Landscaping", "value": 12500}, ...],
  "by_status":   [{"status": "draft", "count": 5, "value": 4200}, ...]
}
```

Semantics:
- **Headline metrics** are always last-30-days. Filtering field:
  - Pipeline / Draft → `created_at >= now - 30d`
  - Won → `updated_at >= now - 30d` AND `status == won`
- **By-division / by-status** are filtered by the `period` query param:
  - `month` → start of current calendar month
  - `quarter` → start of current calendar quarter
  - `year` → start of current calendar year (default)
  - Filter on `created_at`.

Implement with a Mongo aggregation pipeline (one `$facet` covering all five buckets) so we don't fetch every estimate into Python. Exclude `status in ["archived"]` from pipeline metric; exclude `["lost", "archived"]` matches what the FE does today (DashboardPage.tsx 134–139) — preserve that behavior. Division comes from `$unwind` over `job_items`; value uses `sub_total` per the existing FE helper. Honor recurrence multiplier if `divisionResolve.ts` does (verify when implementing).

### Frontend changes
1. Replace the `estimatesApi.list()` call in DashboardPage with a new `estimatesApi.analytics(companyId, period)` call.
2. Hold `period` in component state (default `"year"`), pass to API, refetch on change.
3. Cards:
   - Rename "Won This Month" → "Won Value" (line 279).
   - Add a small "Last 30 days" subtitle line under each of the three headline values.
4. Add a small dropdown above each of the two charts (or one shared dropdown if the section is unified visually — check the existing layout) with options "This Month" / "This Quarter" / "This Year", controlled by the same `period` state.

### Tests
- `platform/tests/test_estimates_*.py`: add a test for `/estimates/analytics` covering: (a) headline 30-day filter on created_at and updated_at; (b) period=year/quarter/month filters by-division and by-status correctly; (c) excludes archived from pipeline; (d) default period is year.
- `portal`: DashboardPage test that changing the dropdown refetches with the new period; rename verified by label test.

---

## Verification (end-to-end)

Backend:
```bash
cd platform && source .venv/bin/activate
./run_tests.sh tests/test_estimates_analytics.py  # new file
./run_tests.sh tests/test_maple_crud_coverage.py
uvicorn main:app --reload
# curl http://localhost:8000/estimates/analytics?company=<id>&period=year | jq
```

Frontend:
```bash
cd portal
npm test -- RateCardsTab WorkItemInlineContent DashboardPage MapleMarkdown PropertiesPage
npm run dev
```

Manual smoke (golden path + edges):
1. Rate Cards → New → name input is focused and selected; add 3 items → reorder with ▲/▼ → save → reload → order persisted.
2. Templates → open one → reorder Materials and Activities; same for a Work Item.
3. Dashboard → headline cards show "Last 30 days" subtitle; "Won Value" label; change the chart dropdown → values update; verify by-status totals reconcile against a hand-filtered Mongo query.
4. Maple chat → "show me property 123 Main St" → click the linked name → list page opens with that record's modal already open; URL param clears after open. Repeat for contact, material, person (labour), estimate.

## Out of scope
- Drag-and-drop reorder (using ▲/▼ buttons only).
- Caching the analytics endpoint (compute fresh each request).
- New detail-page routes for non-estimate resources.
- Touching `documentation/changelog/` (per memory: changelog only when explicitly asked).
