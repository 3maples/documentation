# Estimate Detail Page — Layout Adjustments

## Context

Reorganize the top section of the estimate detail page so the most-used controls are closer to the primary content. Today, action buttons and metadata sit above the Description + Property grid, and Description/Property are paired side-by-side. The new layout pairs Description with the metadata fields, and Property with the action buttons — giving the Description textarea more breathing room and bringing action buttons closer to the Property context they often relate to.

No API or data changes; this is a pure JSX/Tailwind reshuffle in a single page component.

## Target Layout (edit mode)

```
Row 1: [ Description (taller textarea) ]  [ Created By / Created At / Updated At / Approved By — stacked vertically ]
Row 2: [ Property dropdown + info grid  ]  [ Action buttons (two groups, wrap) ]
```

In **non-edit mode** (new-estimate creation), metadata and action buttons don't exist, so Description and Property simply stack full-width as they do today.

## File to modify

- [portal/src/pages/NewEstimateWithActivityPage.tsx](portal/src/pages/NewEstimateWithActivityPage.tsx) — single file; no other components affected.

## Changes

### 1. Remove the current top edit-mode block (lines ~886–1030)

Break up the existing `{isEditMode && estimate && (...)}` wrapper. Individual pieces move into the new two-row grid; the form-error and generation-error banners stay but get relocated (see step 4).

### 2. Row 1 — Description + Metadata (replace current Description cell at ~1033–1044)

- Keep the existing `grid grid-cols-1 md:grid-cols-2 gap-4 items-stretch` wrapper.
- **Left cell**: existing Description textarea, but bump `min-h-[80px]` → `min-h-[122px]` to add ~2 lines (text-sm at ~21px line-height × 2 ≈ 42px).
- **Right cell** (edit mode only): metadata fields in a vertical stack. Reuse the existing field markup (icon + label + value) from lines 1001–1022, but switch the container from `grid grid-cols-2 xl:grid-cols-4` to `flex flex-col gap-1` so Created By / Created At / Updated At / Approved By render one-per-row, vertically aligned. Keep the `bg-gray-100 rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-700` styling so it visually matches today.
- In non-edit mode, omit the right cell — Description spans alone (acceptable since `md:grid-cols-2` will leave the second cell empty; alternatively drop the grid for non-edit mode and render Description full-width).

### 3. Row 2 — Property + Action buttons (replace current Property cell at ~1047–1086)

- New wrapper: `grid grid-cols-1 md:grid-cols-2 gap-4 items-start`.
- **Left cell**: the existing Property section verbatim — `PropertySearchDropdown` (or read-only fallback) + the property info sub-grid (Street / Contact / Email / Phone).
- **Right cell** (edit mode only): the two existing action-button rows, unchanged content:
  - Top row: Approve/Unapprove, Archive, Delete
  - Bottom row: Checklist, Create PDF, Doc version selector + View + Delete-version
  - Wrap both rows in `flex flex-col gap-3`, keeping each row as `flex flex-wrap items-center gap-2` so buttons wrap gracefully in the narrower column.

### 4. Error banners

- `formError` banner (lines 995–999) — move to sit between Row 1 and Row 2 so it's visible regardless of which field triggered it.
- `generation_error` banner (lines 1024–1028) — move to sit directly below Row 2 (it relates to document generation, which is triggered from the action buttons).
- Settings-load-error banner at lines 876–883 — leave where it is (above the new rows).

### 5. Keep untouched

- Back button + Title + Status badge (lines 825–873).
- Work Items header, table, empty state (lines 1090–1196).
- Grand Total (1200–1207), Notes (1210–1218), Save button (1222–1238).

## Why this works cleanly

- All four pieces being moved are already self-contained JSX blocks — no shared state, no prop drilling, no hooks to rewire.
- The existing `grid grid-cols-1 md:grid-cols-2` pattern already used for Description+Property is reused verbatim for the new Row 2, keeping responsive behavior consistent (stacks on mobile, two-column from `md` up).
- Metadata and action buttons are **only rendered in edit mode** today — the new layout preserves that by making the right-hand cell of each row conditional on `isEditMode && estimate`.

## Verification

Per CLAUDE.md, this is a styling/layout-only change (Tailwind class shuffling and JSX reordering, no behavior change), so TDD does not apply. Verification is manual:

1. `cd portal && npm run dev`
2. **Edit mode** (open an existing estimate at `/estimates/:id/with-activity`):
   - Description textarea is visibly taller (~2 more lines) and still resizable.
   - Created By / Created At / Updated At / Approved By appear as a vertical stack to the right of Description, in the same gray panel style.
   - Property dropdown + info panel sits on the next row, left side.
   - Action buttons sit to the right of Property, still wrapping cleanly. Approve/Unapprove, Archive, Delete, Checklist, Create PDF, Doc-version selector, View, Delete-version all work as before.
   - Narrow the viewport below `md` (≤768px) — each row collapses to single-column stacking (Description → Metadata → Property → Actions).
3. **Non-edit mode** (open `/estimates/new-with-activity`):
   - Only Description and Property render; no metadata panel, no action buttons, no layout oddities.
4. `npm run lint` — should pass without new warnings.
5. `npm test` — no existing page-level tests for this component (confirmed during exploration), so no test updates needed. If lint/typecheck surfaces anything, address it.

## Out of scope (for the initial layout-only phase)

- No changes to property-search behavior or the property info display fields.
- No new tests for the layout-only pieces (styling-only change per CLAUDE.md TDD policy).

---

# Follow-up: Status State Machine

## Context

The action buttons below the title need to reflect a formal state machine. Today the UI has toggle-based Approve/Unapprove and Archive/Unarchive — that doesn't match the new status transition rules. Button visibility should now be driven by the current status of the estimate, and each button moves the estimate to a specific target status.

### State Transition Table

| From     | Allowed transitions                              |
|----------|--------------------------------------------------|
| Draft    | Approved, On Hold, Archived, **Delete** (destroy) |
| Approved | Review, On Hold, Won, Lost, Archived              |
| On Hold  | Review                                            |
| Review   | Approved, On Hold, Archived                       |
| Won      | On Hold, Lost                                     |
| Lost     | Review                                            |
| Archived | Review                                            |

Notes:
- **Delete** is destructive (removes the estimate), not a status. It only surfaces on Draft.
- **Unapprove** as a concept is removed — Approved estimates progress via Review / On Hold / Won / Lost / Archived.
- Statuses not in the table (`Generating`, `Failed`, `Submitted`, `Scheduled`, `Completed`, `Deleted`) render no transition buttons.

## Decisions (confirmed)

- **Enforcement**: frontend-only. The UI only surfaces allowed transitions; backend PUT stays permissive.
- **Unarchive target**: `/unarchive` endpoint changes to restore to **Review** (was Draft) to match `Archived → Review`. Maple's "unarchive" agent verb updates to match so chat and UI behave consistently.
- **Approve role gate**: retain the existing Owner/Admin restriction (`canApprove`). Members can still move through all other transitions but Approve is hidden for them.

## Files to modify

- [portal/src/lib/estimateStatus.ts](portal/src/lib/estimateStatus.ts) — add `getAllowedTransitions(status, { canApprove })` returning an ordered list of transition descriptors.
- [portal/tests/estimateStatus.test.ts](portal/tests/estimateStatus.test.ts) — **new** vitest file with coverage for every row in the state table (TDD).
- [portal/src/pages/NewEstimateWithActivityPage.tsx](portal/src/pages/NewEstimateWithActivityPage.tsx) — replace the hard-coded Approve/Archive/Delete trio (lines ~870–905) with a mapped button list driven by `getAllowedTransitions()`. Add `handleStatusChange(target)` that routes to the right API:
  - `target === "Archived"` → `PATCH /estimates/{id}/archive`
  - current status is `"Archived"` and target is `"Review"` → `PATCH /estimates/{id}/unarchive`
  - otherwise → `PUT /estimates/{id}` with `{ status: target }`
  - `target === "delete"` → keep existing delete modal flow
- [platform/routers/estimates.py](platform/routers/estimates.py) — `unarchive_estimate` (line 2241): change `EstimateStatus.DRAFT` → `EstimateStatus.REVIEW` and update the docstring.
- [platform/agents/estimate/service.py](platform/agents/estimate/service.py) — line ~3973 (`_resolve_status_transition` or similar): return `EstimateStatus.REVIEW` for the unarchive verb. Line ~4303: update response text from "now Draft" to "now Review".
- [platform/tests/test_estimate_api.py](platform/tests/test_estimate_api.py) — line 3774: update assertion to expect `"Review"`.
- [platform/tests/test_estimate_agent.py](platform/tests/test_estimate_agent.py) — line ~2889: update assertion to expect `"Review"` and update docstring comment on line 2866.

## Button set (edit mode, below title)

Ordered left-to-right per transition-table order, with existing icons where sensible:

| Label      | Icon       | Target         | Shows when                                    |
|------------|------------|----------------|-----------------------------------------------|
| Approve    | `Check`    | Approved       | status ∈ {Draft, Review} AND canApprove       |
| Review     | `RotateCcw`| Review         | status ∈ {On Hold, Lost, Archived, Approved}  |
| On Hold    | `Pause`    | On Hold        | status ∈ {Draft, Approved, Review, Won}       |
| Won        | `Trophy`   | Won            | status ∈ {Approved}                           |
| Lost       | `XCircle`  | Lost           | status ∈ {Approved, Won}                      |
| Archive    | `Archive`  | Archived       | status ∈ {Draft, Approved, Review}            |
| Delete     | `Trash2`   | (destroy)      | status ∈ {Draft} only                         |

Missing icons (`RotateCcw`, `Pause`, `Trophy`, `XCircle`) get added to the lucide-react import.

## Helper signature

```ts
export type EstimateTransitionTarget = "Approved" | "Review" | "On Hold" | "Won" | "Lost" | "Archived" | "delete";

export interface EstimateTransition {
  target: EstimateTransitionTarget;
  label: string;
}

export function getAllowedTransitions(
  status: string | null | undefined,
  opts: { canApprove: boolean }
): EstimateTransition[];
```

The helper uses `normalizeEstimateStatus()` to canonicalize input (handles "On Hold" vs "on_hold" vs "onhold"). `getArchiveToggleAction` stays for any remaining callers but is no longer used in the detail page.

## TDD order

1. **Red**: write `portal/tests/estimateStatus.test.ts` covering all 7 source statuses + `canApprove: true/false` splits for Draft and Review.
2. **Green**: add `getAllowedTransitions` to `estimateStatus.ts`. Run `npm test -- estimateStatus` — tests pass.
3. **Red**: flip backend unarchive test (`test_unarchive_estimate_succeeds`) and agent test (`test_estimates_status_transition_unarchive`) to expect `"Review"` — fails.
4. **Green**: update `/unarchive` endpoint + agent service to return REVIEW. Run `./run_tests.sh tests/test_estimate_api.py tests/test_estimate_agent.py -k "unarchive"` — passes.
5. **Wire UI**: replace the button trio with `getAllowedTransitions().map(...)`. Add `handleStatusChange()` that dispatches to the three API paths. Delete button keeps the confirm modal.

## Verification

1. `cd portal && npm test -- estimateStatus` — new helper tests pass.
2. `cd platform && source .venv/bin/activate && ./run_tests.sh tests/test_estimate_api.py tests/test_estimate_agent.py -k "unarchive"` — updated tests pass.
3. `cd portal && npm run lint && npx tsc --noEmit` — clean.
4. `npm run dev`, open an estimate in each status (manually flip the DB if needed or walk the state machine via the UI):
   - **Draft**: Approve (if admin), On Hold, Archive, Delete visible.
   - **Approved**: Review, On Hold, Won, Lost, Archive visible. No Approve/Unapprove.
   - **On Hold**: only Review visible.
   - **Review**: Approve (if admin), On Hold, Archive visible.
   - **Won**: On Hold, Lost visible.
   - **Lost**: only Review visible.
   - **Archived**: only Review visible. Clicking Review calls `/unarchive` and lands in Review.

## Out of scope (state machine phase)

- Server-side state-machine enforcement in PUT `/estimates/{id}` — deferred; frontend is the single source of truth for now.
- Changing the status dropdown used elsewhere (estimates list filters, etc.) — only the detail-page action buttons are affected.
- Reworking audit log action names; existing `ESTIMATE_STATUS_CHANGE` and `ESTIMATE_ARCHIVE` are reused.
