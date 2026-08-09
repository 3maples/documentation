# Property activity panel — Estimates + Tasks in one bounded, filterable surface

## Context

The Properties page details pane lists every estimate linked to the selected property, in a
scrolling table. Tasks are also linked to properties (`Task.property`) but appear nowhere on
this page — to see the work outstanding at a site you have to leave for the Tasks page and set
a filter by hand.

The obvious move — bolt a second table underneath the first — makes the pane roughly twice as
tall and pushes the details card past a screen on laptops. It also doubles down on a scaling
problem that is already there: the page fetches **every estimate in the company** via
`estimatesApi.list(COMPANY_ID)` and filters client-side (`PropertiesPage.tsx:137`, `:301`).
At a few hundred estimates that is a slow page load; at a few thousand it is an unusable one.
Estimates also have no `property` index, so no amount of frontend work fixes it alone.

**Outcome:** a single fixed-height **Activity** panel replacing today's estimates block. Tabs
switch between Estimates and Tasks; tab badges carry unfiltered counts so you can read both
without switching; a per-tab status filter narrows the list; the body is a scroll box holding
the first ~15 matching rows with a jump-out link to the full page. The panel's height never
changes — not with the tab, not with the filter, not with the data volume — and the page stops
loading company-wide data entirely.

### Decisions confirmed with the user

| Question | Decision |
|---|---|
| What the panel is for | **Quick glance + jump out** — see what's there, then use the Estimates/Tasks pages for heavy browsing |
| Layout | **Tabs**, not side-by-side columns and not a merged timeline |
| Filter control | **Multi-select status dropdown only** — reuse the existing EstimatesPage pattern, no Open/Closed presets |
| How many rows in place | **Scroll box, ~15 loaded**, then "View all N →" |
| Task ordering | **Newest created first** (`created_at` desc) — not by due date |
| Overdue badge | **Dropped.** Task statuses are company-configurable, so "past due but not finished" can't be computed honestly; the count would overstate on any property whose work is done |
| "View all" links | **Always present** on both tabs, whatever the count — so the jump-out is never conditional on how much data there is |

### Why tabs and not the alternatives

Two side-by-side cards would show both lists at once, but the estimates table already declares
`min-w-[520px]`; at half the pane width it scrolls horizontally on anything short of a wide
desktop. A merged "recent activity" timeline is the shortest option, but estimates and tasks
carry different columns (value/status vs due date/assignee), and a combined top-N shows zero
tasks on a property with many estimates. Tabs keep the full width for whichever list you're
reading, and putting counts on the tab labels recovers most of what side-by-side would give you.

---

## Layout

```
┌ Details ─────────────────────────────────────── ✎ 🗑 ┐
│  41 Maple Drive                                      │
│  ADDRESS / CONTACTS              ┌────── map ──────┐ │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ [Estimates 47]  [Tasks 12]             [All ▾] │  │
│  ├────────────────────────────────────────────────┤  │
│  │ TITLE                    VALUE       STATUS  ▲ │  │
│  │ Spring cleanup          $4,200     [Approved]│ │  │
│  │ Irrigation repair         $980     [Draft]   │ │  │
│  │ Aeration                  $610     [Sent]    ▼ │  │
│  ├────────────────────────────────────────────────┤  │
│  │ Showing 15 of 31 matching   View all 47 →      │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Tab strip.** Two tabs, left-aligned; the status filter dropdown right-aligned on the same
row. Badges show *unfiltered* totals for the property, so they stay stable while the filter
moves and they tell you what's behind the tab you haven't opened. Nothing else rides on the
badge — see "No overdue signal" below.

**Body.** Fixed-height scroll box (`max-h-80`, matching today) with the sticky `thead` pattern
already used at `PropertiesPage.tsx:604`. Two different numbers are in play and shouldn't be
conflated: the box is **320px tall** — about seven rows visible — and holds
**`PANEL_PAGE_SIZE = 15`** fetched rows, which you reach by scrolling inside it. Columns are
deliberately parallel so switching tabs isn't jarring:

| | Column 1 | Column 2 | Column 3 |
|---|---|---|---|
| Estimates | Title (or `estimate_id`) | Value, right-aligned | Status pill |
| Tasks | `taskHeadline()` | Created date, right-aligned | Status pill |

Column 2 on the Tasks tab shows the field the list is sorted by, so the ordering is legible
rather than mysterious.

Rows keep the existing click/Enter/Space navigation and `role="link"` treatment. Estimate rows
use the existing `getEstimateDetailsPath` helper. **Task rows have nowhere to go today** —
`TasksPage` reads no URL parameters at all, and `/tasks/:id` is deliberately redirected to
`/tasks` (`App.tsx:295`). Rather than resurrect a task detail route, task rows navigate to
`/tasks?propertyId=<id>&taskId=<id>`, and TasksPage gains query-param seeding that applies the
property filter and opens that task's existing dialog. The `propertyId` half of that work is
needed for the "View all →" link regardless, so this adds one parameter, not a route.

**Footer.** `Showing 15 of 31 matching` on the left, rendered only when the loaded count is
less than the filtered total. `View all 47 estimates →` / `View all 12 tasks →` on the right,
**always rendered on both tabs** — including when the property has few rows, or none. The
jump-out is a fixed affordance, not something that appears once a list gets long enough; a
user who wants the full Tasks page filtered to this property shouldn't have to first own
enough tasks to earn the link. When the count is zero the link still routes to the filtered
page, which shows its own empty state.

**Ordering.** Both tabs read newest-first, on their own clock: estimates by `updated_at` desc
(as today), tasks by `created_at` desc. `created_at` is the timestamp the task UI already
treats as canonical — `TaskAgePill` derives task age from it, while `task_date` is server-owned
and never displayed.

**No overdue signal.** An earlier draft badged the Tasks tab with a past-due count. It's
dropped: task statuses are company-configurable, so there is no dependable "finished" status to
exclude, and a count that ignores status overstates on every property whose work is complete.
Assuming the last-ordered status is terminal would make the number wrong for anyone who
reordered their columns. Due dates remain a first-class concept on the Tasks page, which is
where past-due work should be triaged.

**Mobile.** Tabs become a full-width segmented control; the middle column (Value / Created
date) collapses into a subline beneath the title so three columns don't crush at 375px. The
"View all →" link stays visible — it's the primary escape hatch on a small screen.

**Empty states.** Per tab, distinguishing no data from no matches: "No estimates yet." vs
"No estimates match this filter." Same for tasks.

## Filtering

The dropdown is the existing multi-select checkbox control, with **independent selection per
tab**. Both default to **all statuses selected**, which preserves today's Properties-page
behavior of listing every linked estimate whatever its status (`PropertiesPage.tsx:304`).
This is deliberately *not* EstimatesPage's default, which is the legacy `["draft"]`.

Selections persist to `sessionStorage` under a single key (`propertyActivityFilters`, holding
both tabs), so they survive switching between properties within a session — matching how
EstimatesPage persists `estimatesStatusFilter`.

**Estimates options** — the nine in `ESTIMATE_FILTER_STATUSES` (`draft, sent, review, won,
lost, on_hold, scheduled, completed, archived`). `archived` is not a real filter value: ticking
it sets `include_archived=true`, the coupling EstimatesPage already handles through
`selectionIncludesArchived`. Reuse that helper rather than re-deriving it.

**Task options** — fetched from `taskStatusesApi.list(COMPANY_ID)`, because task statuses are
company-configurable (seeded To Do / In Progress / Done, but editable). A separate `Archived`
row maps to the `include_archived` flag, mirroring the estimates treatment. Note the backend's
existing first-status special case: filtering by the first status must also match tasks with
`status: null` (v1 tasks predate the field) — that logic already lives in
`routers/tasks.py:212` and must survive the widening to multi-status.

## Frontend changes

**1. Extract `StatusFilterDropdown`** from `components/common/EstimateStatusFilter.tsx`.
Today that component hardcodes `ESTIMATE_FILTER_STATUSES`; the task filter needs the same
control driven by options fetched at runtime. New generic component takes
`{ options: {value,label}[], selected, onChange, allLabel }`; `EstimateStatusFilter` becomes a
thin wrapper passing the estimate list. No behavior change on EstimatesPage —
`tests/EstimatesPageStatusFilter.test.tsx` should pass untouched, which is the regression net
for the extraction.

**2. New `components/properties/PropertyActivityPanel.tsx`** owning the tab state, both filter
selections, fetching, caching and rendering. The estimates-table markup and its helpers move
out of `PropertiesPage.tsx` into this component. That file is already 916 lines; adding a
second table plus filters and fetch orchestration inline would push it past 1,300.

**3. `PropertiesPage.tsx` slims down.** It drops `estimatesApi.list(COMPANY_ID)`, the
`selectedPropertyEstimates` memo, the estimate row-navigation handlers, and the four estimate
formatting helpers, and renders `<PropertyActivityPanel propertyId={…} />` in their place. It
gains one call to `taskStatusesApi.list()` (passed down as filter options).

**4. `PropertyDialog` fetches estimates lazily.** Its `EstimatesPicker` needs the full company
estimate list to link/unlink, and is the only remaining consumer once the panel fetches
per-property. Move the fetch inside the dialog, triggered on open. This is what actually
removes the company-wide load from page render.

**5. Deep links.** Neither destination page reads URL parameters today, so both need seeding:

- **TasksPage** — `?propertyId=` seeds the `propertyFilter` it already holds in state
  (`TasksPage.tsx:131`); `?taskId=` opens that task's dialog. Both are new but small; the page
  needs a `useSearchParams` hook it currently lacks.
- **EstimatesPage** — `?propertyId=` has nothing to seed: the page has **no property filter at
  all**, only search and status. It needs a real one built. Prefilling the search box with an
  address string was considered and rejected — it breaks the moment a property is renamed, and
  it silently matches unrelated estimates whose titles contain the same word.

This is the largest piece of work outside the panel itself, and it is **required, not
optional**. An earlier draft floated descoping it so "View all →" would land on the unfiltered
page; that's incompatible with the decision that both links are always present. A permanent
link that dumps you into every estimate in the company is worse than no link — it looks broken
precisely when a property has a lot of work on it, which is the case the link exists for.

**6. Cache.** Panel results are memoized in a `Map<propertyId+tab+filterKey, …>` so
re-selecting a property or flipping back to a tab is instant. Invalidated on the mutation
events already wired at `PropertiesPage.tsx:187`, and on any create/update/delete the panel
itself triggers.

## Backend changes

**1. `GET /estimates` gains `property` and repeatable `status`.** Currently only
`company`, `include_archived`, `limit` (`routers/estimates.py:383`). `property` mirrors the
tasks implementation, including its 422 on an unparseable ObjectId. `status` accepts repeated
values; absent means all.

**2. `GET /tasks` widens `status` to repeatable and gains `sort=created_at`.** `status` takes a
single `TaskStatus` id today (`routers/tasks.py:173`) — widen to `List[str]`, preserving
single-value callers and the `status: null` first-status special case. `sort` is currently
`Literal["due_date"]` with an `updated_at` desc default; add `created_at` (desc) as a second
accepted value. The panel passes it explicitly rather than leaning on the default, so a future
change to that default can't silently reorder the panel. `property` and `limit` already exist.

**3. `X-Total-Count` response header** on both list endpoints — the count of documents matching
the filter *before* `limit`. Drives "Showing 15 of 31 matching". One `count_documents` on an
already-indexed query. Chosen over fetching `limit + 1` and rendering "15+", which is a worse
answer to the same question.

**4. New `GET /properties/{property_id}/activity-summary`** → `{estimate_count, task_count}`,
unfiltered, for the tab badges. Not redundant with #3: badges must show unfiltered totals
*including for the tab that hasn't been opened*, which a header on a filtered list can't
provide. Route sits alongside the existing `/{property_id}/map.png`; company access asserted the
same way as its siblings. Both counts exclude archived records, matching what the tabs list by
default.

**5. Indexes for the two per-property sorts.**

- Estimates: new `(company, property, updated_at desc)`. The collection has only
  `(company, updated_at, status)` today (`models/estimate.py:457`), so a per-property query
  would collection-scan.
- Tasks: extend `(company, property)` (`models/task.py:78`) to
  `(company, property, created_at desc)`, so the panel's sort is index-served rather than an
  in-memory sort of every task at the property.

### Resulting load profile

| | Before | After |
|---|---|---|
| Properties page load | Every estimate in the company | Properties + contacts + task statuses |
| Selecting a property | 0 requests (client filter) | ≤15 docs + 3 indexed counts |
| Changing tab or filter | n/a | ≤15 docs + 1 indexed count |
| Panel height | Grows with content | Fixed |

## Testing

TDD throughout — failing test first, per the repository policy.

**Backend** (`./run_tests.sh tests/<file>`)

- `test_estimate_api.py` — `property` filter returns only that property's estimates; rejects a
  malformed id with 422; combines with `limit`; repeatable `status` filters correctly; ticking
  archived reaches archived estimates and omitting it does not; `X-Total-Count` reports the
  pre-limit total.
- `test_tasks_api.py` — multi-value `status` returns the union; a single value still behaves as
  before (regression); the first-status/`null` special case survives multi-status;
  `sort=created_at` returns newest-created first and `sort=due_date` is unchanged (regression);
  `X-Total-Count` matches.
- New `test_property_activity_summary.py` — counts are property-scoped and company-scoped;
  archived excluded from both counts; unknown property id → 404; cross-company access → 403.

**Frontend** (`npm test -- <file>`)

- `PropertiesPageEstimates.test.tsx` — **existing, will need updating**: it covers the block
  being replaced. Rework to assert the panel renders estimates in the Estimates tab.
- `EstimatesPageStatusFilter.test.tsx` — must pass **unmodified** after the dropdown extraction.
- New `PropertyActivityPanel.test.tsx` — tab switching renders the other resource; badges show
  unfiltered totals while a filter is applied; filter selections are independent per tab and
  persist across property switches; tasks render newest-created first; "Showing X of Y" appears
  only when truncated; **"View all" renders on both tabs even at zero rows, and carries the
  property id**; empty-vs-no-match states; rows navigate on click and on Enter/Space.
- New `PropertyDialogLazyEstimates.test.tsx` — no estimate fetch on page render; fetch fires on
  dialog open; `EstimatesPicker` still lists and links.
- New `TasksPageDeepLink.test.tsx` — `?propertyId=` applies the property filter on mount;
  `?taskId=` opens that task's dialog; both absent leaves the page unchanged (regression);
  an unknown id degrades to the plain list rather than erroring.
- New `EstimatesPagePropertyFilter.test.tsx` — the new filter narrows to one property, composes
  with the existing status filter and search, and is seeded by `?propertyId=`.

**Gates.** `./run_mypy.sh` and `./run_ruff.sh` scoped to touched subtrees for every Python
change; `npm run typecheck` and `npm run lint` for the portal.

## Out of scope

- Paging beyond the first ~15 rows in the panel — that is what "View all →" is for, and it
  follows from the quick-glance decision above.
- The left-hand properties list, which still loads and filters every property client-side. Real
  at large tenants, but a separate change with a separate design.
- Any change to how estimates or tasks are created, edited, or linked to properties.
