# Tasks UI improvements — readable IDs, dialog rework, filter pills

## Context

The New/Edit Task dialog asks for information users don't want to give. Field crews
open it to dump a note, a photo, and a voice memo — but the first thing they hit is a
required **Title** and a required **Date**, both of which the app can figure out on its
own. Meanwhile the fields that matter (Description, Record/Photo/Video) sit at the
bottom, below a grid of dropdowns.

At the same time the Tasks surface has outgrown its plumbing: the Property and Assignee
pickers are plain `<select>`s that get unusable past a few dozen rows, active filters are
invisible once the Filter popup closes, and tasks have no human-quotable identifier — you
can't say "look at T0042" to a colleague, and Maple can't resolve one.

**Outcome:** a dialog whose first field is the description, searchable pickers everywhere,
visible/removable filter pills, and a short sequential `T<DDDD>` ID on every task —
displayed on cards, shown read-only in the edit dialog, and searchable from the listing,
the API, and Maple.

### Decisions confirmed with the user

| Question | Decision |
|---|---|
| Card headline once Title is gone | First part of the **description**, ellipsised by available space (CSS `truncate`, not a character count) |
| ID strategy | **Sequential** per-company counter encoded to Crockford Base32 — `T0001`, `T0002` … `T000A` … `T0010` |
| ID scope + existing data | Unique **per company**, with a **backfill** for existing tasks |
| ID searchable in | Tasks page search box **+** `GET /tasks?search=` **+** Maple resolver |
| "created_at date field" | The required **`Date *`** input in New Task — removed; `task_date` is server-stamped |

### Two things I'm doing that weren't literally asked for, and why

1. **`title` stays in the database as a pure derived mirror** of the description's first
   line — recomputed on every create *and* every update, never user-editable. It has to
   stay stored (not computed on read) because the Maple resolver queries it directly with
   `{"title": {"$regex": ...}}`, and it has to stay populated because ~8 `object_link(...)`
   call sites, the fuzzy matcher, the task-details renderer, the delete-confirmation copy,
   and audit before/after snapshots all read it — roughly 198 references across the platform
   test suite. A ~15-line derive helper keeps every one of those working instead of a
   multi-file rewrite.
2. **`SearchableSelect` gains ARIA roles.** The existing component renders a bare
   `<button>` with no `role`/`aria-label`, which makes it untestable and unusable with a
   screen reader. Since four other screens already depend on it, fixing it in place is a
   free win — but their tests need a re-run (trigger queries move from `button` to
   `combobox`).

---

## Design decisions

### Counter: `Company.next_task_seq: int = 0`

Reuses the atomic-counter idiom already in
[services/estimate_quota.py:41](platform/services/estimate_quota.py:41) —
`find_one_and_update({"_id": cid}, {"$inc": {...}}, return_document=AFTER)`. No new
collection, no `database.py` registration. `$inc` on a missing field creates it at 0, so
existing companies need no migration. Respects the models-must-not-import-services rule
(`tests/test_models_layering.py`): the field is on the model, the allocator is in services.

- **Backfill seeds by block reservation**, not by writing a count: one
  `$inc: {next_task_seq: n}` per company returns the block end, and the n tasks are
  numbered in `created_at` order. Race-safe against concurrent creates.
- **Overflow past 1,048,575 widens to 5 chars** (`T10000`) rather than raising. Never
  block a create over a formatting rule.
- **`next_task_seq` is not a task count.** Deletes free a cap slot and leave a permanent
  gap. Comment this on the field so nobody "optimizes" `services/task_quota.py` to read it.

### Modules

- `platform/services/readable_id.py` — pure codec, no DB, no async. `encode_crockford_base32`,
  `decode_crockford_base32`, `format_task_readable_id`, `normalize_task_readable_id`.
  Alphabet `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (no I/L/O/U); decode folds I/L→1, O→0.
- `platform/services/task_readable_id.py` — async allocator: `allocate_task_readable_id`,
  `reserve_task_readable_id_block`, `insert_task_with_readable_id` (bounded retry on a
  `readable_id` `DuplicateKeyError`, mirroring
  [models/task_status.py:40](platform/models/task_status.py:40)'s recovery pattern).
- `platform/services/task_title.py` — `derive_task_title(description, max_length=80)`.
  Deliberately *not* an import of `agents/task/text_helpers.py::derive_title_from_description`,
  which is tuned for chat phrasings ("remind me to…"). Cross-reference in both docstrings.

### Title lifecycle — fully derived, always

`title` is recomputed from the description in **one place**, on both create and update:
edit the description's first line and the title follows immediately. There is no
preserve-a-manual-rename carve-out — a stored value that can silently diverge from the
description is exactly the staleness the derivation exists to avoid.

Consequence: **Maple's title-rename path must go** (`agents/task/field_flow.py:29,127,278`
and `agents/task/service.py:465-466` currently accept "rename this task to X" and write
`{"title": value}`). Leaving it in place would give users a rename that silently reverts on
the next description edit — worse than not offering one. Drop `title` from the editable-field
list and route the intent at description instead. This is why the Maple copy change is in
the main line (Phase 3) rather than the optional tail phase.

### PUT exclude set — the highest-severity risk

`PUT /tasks/{id}` binds the raw `Task` Document, so **any field the client omits resets to
its model default**. The moment `readable_id`/`title` become `Optional[... ] = None`, a
single un-updated caller nulls them — and `TasksPage.handleMoveTask` fires on *every
kanban drag*. Add `readable_id`, `title`, `task_date` to the exclude set at
[routers/tasks.py:247](platform/routers/tasks.py:247), and give each an explicit
**"PUT omitting the field preserves it"** test, not just "PUT can't change it".

### Unique index — the second landmine

Beanie builds indexes during `init_db`, i.e. **at app boot, before the backfill runs**.
A plain `unique=True` on `(company, readable_id)` would index every pre-backfill doc as
`null` and fail on the second one in any company — taking the service down. Required:

```python
IndexModel(
    [("company", ASCENDING), ("readable_id", ASCENDING)],
    unique=True,
    partialFilterExpression={"readable_id": {"$type": "string"}},
)
```

`sparse=True` does **not** substitute — on a compound index a doc is included if *any*
keyed field exists, and `company` always does.

### Dialog layout (top → bottom)

**Edit mode**
1. ID row — `Task ID T0001` (`font-mono text-xs text-gray-500`, `data-testid="task-readable-id"`),
   with `<TaskSentCheck />` right-aligned (it currently lives inside the deleted Title input
   and needs a new home).
2. Description label + `TaskMediaButtons` (Record / Photo / Video) — the existing row, unchanged.
3. Description `<textarea rows={8}>`.
4. `TaskPhotoGrid` under a "Media" heading — moved up, adjacent to the buttons that fill it.
5. Field grid `grid-cols-1 sm:grid-cols-2 gap-3`: Property (`SearchableSelect`) · Due date
   (native date input) · Status (native `<select>`) · Assigned to (`SearchableSelect`, `autoFlip`).
6. Error paragraph.

**Create mode** — identical minus (1); (4) becomes the staged-photo grid; the assignee
picker gains "Me (default)"; the progress line sits above the error.

Notes: Status stays a **native select** (a company has ~3); only Property and Assignee get
search, per the request. `maxVisible={8}` gives "8 rows then scroll". The
`grid-cols-2 sm:contents` shim at `TaskDialog.tsx:620-626` is deleted — with Status always
rendered, the four fields form a clean 2×2. `canSubmit` becomes `!isSubmitting` (both
gating fields are gone).

**GPS machinery:** delete `UNTITLED_TASK_TITLE`, `applyAutoTitle`, `userEditedTitleRef` and
the reverse-geocode effect. **Keep** `captureCoords` / `propertySnappedRef` / the
nearest-property effect, reduced to `setPropertyId(prev => prev || getEntityId(nearest))` —
GPS now auto-selects the **Property** instead of the title. Check
`lib/locationLabel.ts::reverseGeocodeLabel` for other consumers before removing anything.

### New frontend primitives

**`portal/src/lib/taskDisplay.ts`** — `taskHeadline(task)` (first non-empty description
line → `title` → `"Untitled task"`) and `taskRemainder(task)` (description minus that line).

**`portal/src/components/common/FilterPills.tsx`**

```ts
export interface FilterPillSpec {
  id: string;            // React key + used in the remove button's accessible name
  label: string;         // category, e.g. "Assignee"
  value: string;         // selection, e.g. "Bob Crew"
  onRemove: () => void;
}
export function FilterPills(props: {
  pills: FilterPillSpec[];
  onClearAll?: () => void;   // renders "Clear all" when supplied and pills.length > 1
  className?: string;
}): JSX.Element | null;      // null when empty, so callers need no conditional
```

`<ul aria-label="Active filters">` of chips; each X is
`aria-label={`Remove ${label} filter`}`. Crib the button markup from the staged-photo
remove at `TaskDialog.tsx:734-749`, restyled to `bg-gray-100 text-gray-700 rounded-full
px-2 py-0.5 text-xs`. Lives in `common/` with zero Tasks coupling so `EstimateStatusFilter`
can adopt it next.

**`SearchableSelect` additions** — `ariaLabel?`, `id?`, `triggerClassName?`;
`role="combobox"` + `aria-haspopup="listbox"` + `aria-expanded` + `aria-controls` on the
trigger, `role="listbox"` on the panel, `role="option"` + `aria-selected` on rows, Escape
closes and refocuses the trigger. Arrow-key nav deferred (log as follow-up).

### Maple resolver

New **step 1a** in `agents/task/resolver.py`, after the ObjectId step and before the
positional step (an explicit ID beats "the second one"):

```python
_READABLE_ID_RE = re.compile(r"(?<![0-9A-Za-z])T[0-9A-HJKMNP-TV-Z]{4,7}(?![0-9A-Za-z])")
_READABLE_ID_CUED_RE = re.compile(r"(?:task|#)\s*#?\s*(?P<id>t[0-9a-hjkmnp-tv-z]{4,7})\b", re.IGNORECASE)
```

Bare form is uppercase-only; the case-insensitive form needs a `task`/`#` lead-in.
**On a DB miss, fall through to the next step rather than returning** — that neutralizes
the false-positive risk (uppercase `TASKS` parses as `T`+`ASKS`, all valid Crockford chars)
without brittle word lists.

---

## Phases

Each phase is independently testable and shippable. TDD throughout — failing test first.

### Phase 1 — Crockford codec (pure)

**Tests first:** `platform/tests/test_readable_id.py` — `encode(0)=="0000"`, `(10)=="000A"`,
`(32)=="0010"`, `(1048575)=="ZZZZ"`, `(1048576)=="10000"`; alphabet excludes I/L/O/U;
`decode(encode(n))==n` round-trip; decode folds I/l→1 and O/o→0;
`format_task_readable_id(1)=="T0001"`; `normalize` handles `"t4k7q"`/`"#T4K7Q"`/`"T-4K7Q"`
→ `"T4K7Q"` and `"hello"` → `""`; negative input raises `ValueError`.

**Create:** `platform/services/readable_id.py`
**Gates:** `./run_tests.sh tests/test_readable_id.py` · `./run_mypy.sh services/readable_id.py` · `./run_ruff.sh services/readable_id.py`

### Phase 2 — `readable_id` field, counter, create-time allocation, PUT protection

**Tests first:**
- `platform/tests/test_task_readable_id.py` (new; include the autouse `_enable_tasks_feature`
  fixture from the start) — two creates in one company give `T0001`/`T0002`; two companies
  each start at `T0001`; a Company with no `next_task_seq` yields `T0001`;
  `insert_task_with_readable_id` retries a `readable_id` duplicate and re-raises others;
  `reserve_task_readable_id_block(cid, 3)` returns a contiguous range and advances by 3.
- `platform/tests/test_tasks_api.py` — create returns a `T`+4-char `readable_id`;
  `test_put_cannot_change_readable_id`; **`test_put_without_readable_id_preserves_it`**
  (the kanban-drag regression).
- `platform/tests/test_maple_task_crud.py` — a Maple-created task has a `readable_id`.

**Modify:** `models/task.py` (field + partial unique index) · `models/company.py`
(`next_task_seq`) · **create** `services/task_readable_id.py` · `routers/tasks.py`
(allocate in the server-owned block at 101-120, *after* the cap check so a 409 doesn't burn
a number; `insert_task_with_readable_id` replaces `task.insert()`; add `readable_id` to the
PUT exclude set) · `agents/task/create.py:94` (route through the same insert) ·
`portal/src/types/api.ts` (`readable_id?: string | null`).

**Gates:** `./run_tests.sh tests/test_task_readable_id.py tests/test_tasks_api.py tests/test_maple_task_crud.py` · `./run_mypy.sh services routers/tasks.py models agents/task` · `./run_ruff.sh services routers models agents/task`

### Phase 3 — `title` optional, `task_date` server-stamped

**Tests first:**
- `platform/tests/test_task_title.py` (new) — first line extraction; whitespace-only →
  `"Untitled task"`; >80 chars truncates on a word boundary; a single over-long word hard-cuts.
- `platform/tests/test_tasks_api.py` — **rewrite** `test_create_task_requires_title_and_date`
  (48-57) into `test_create_task_without_title_or_date_derives_both`; amend `test_create_task`
  so a client-supplied `task_date` is *ignored* and the stamp is ~now;
  `test_put_cannot_set_title_directly` (a client-supplied `title` is ignored);
  **`test_put_rederives_title_from_the_new_description`** — PUT a changed description, the
  stored title tracks its new first line; `test_put_with_an_unchanged_description_keeps_the_title`.
- `platform/tests/test_maple_task_crud.py` — "rename this task to X" no longer offers a
  title edit; the refusal/redirect names the description instead.

**Modify:** `models/task.py` (`title: Optional[str] = None`; `task_date` gains a
`default_factory` and stays **non-Optional** so the ~20 `task_date.date()` read sites need
no narrowing) · **create** `services/task_title.py` · `routers/tasks.py` (stamp `task_date`;
derive the title from the description on create **and** on PUT — one shared call site; add
`title`/`task_date` to the exclude set) · `agents/task/base.py::_apply_task_update` (re-derive
after any description change, so Maple edits stay consistent with HTTP edits) ·
`agents/task/field_flow.py:29,127,278` + `agents/task/service.py:465-466` (drop `title` from
the editable-field list) · fix the stale module docstring in `tests/test_tasks_api.py`.

**Gates:** `./run_tests.sh tests/test_task_title.py tests/test_tasks_api.py tests/test_task_convert_api.py tests/test_task_photos_api.py tests/test_task_quota.py tests/test_tasks_feature_flag.py` then the whole `tests/test_maple_task_*.py tests/test_task_resolver.py` set (all ~198 title refs must stay green) · **full** `./run_mypy.sh` (the `Optional` relaxation can surface narrowing errors anywhere) · `./run_ruff.sh`

### Phase 4 — ID search: API, Maple resolver, task details

**Tests first:**
- `test_tasks_api.py` — `search=T0001` and `search=t0001` both match; a term matching none
  of title/description/readable_id returns nothing.
- `test_task_resolver.py` — `"show me task T0001"` and the lowercase cued form resolve; an
  uppercase Crockford-shaped token with no match **falls through** to the fuzzy step; a
  foreign-company ID doesn't resolve; the ID step beats a positional reference.
- `test_maple_task_operations.py` — `_build_task_details` emits `- ID: T0001`; the agent's
  list search matches on `readable_id`.

**Modify:** `routers/tasks.py:179-186` (add `readable_id` to the `$or`, update the `search`
Query description) · `agents/task/base.py` (`_list_conditions` `$or`; `- ID:` line in
`_build_task_details` at ~295) · `agents/task/resolver.py` (step 1a + module-docstring
resolution order).

**Gates:** `./run_tests.sh tests/test_tasks_api.py tests/test_task_resolver.py tests/test_maple_task_operations.py tests/test_maple_task_routing.py tests/test_maple_task_context.py` · `./run_mypy.sh agents/task routers/tasks.py` · `./run_ruff.sh agents/task routers`

### Phase 5 — Backfill script

**Tests first:** `platform/tests/test_backfill_task_readable_ids.py`, following
`tests/test_backfill_email_verified.py` exactly (`sys.path.insert` to `scripts/`,
monkeypatched `init_db`) — dry run writes nothing; `--apply` numbers `T0001…T000N` per
company in `created_at` order; already-ID'd tasks are skipped and burn no sequence; two
companies number independently; `next_task_seq` ends at the highest assigned; a second
`--apply` is a no-op; non-zero exit on any failure.

**Create:** `platform/scripts/backfill_task_readable_ids.py` — the Convention A template
from [scripts/backfill_email_verified.py](platform/scripts/backfill_email_verified.py):
usage docstring, `sys.path.insert` + `# noqa: E402`, `await init_db()`, dry-run default with
`--apply`, per-company chunked iteration via `reserve_task_readable_id_block`, tally,
`raise SystemExit(main())`.

**Gates:** `./run_tests.sh tests/test_backfill_task_readable_ids.py` · `./run_mypy.sh scripts/backfill_task_readable_ids.py` · `./run_ruff.sh scripts`

> **Deploy checkpoint.** Phases 1–5 are a complete backend release that works with
> `tasks_enabled` off (the backfill bypasses the router). Ship, run the backfill, then
> proceed to the frontend.

### Phase 6 — Frontend shared primitives

**Tests first:** `portal/tests/taskDisplay.test.ts` (headline/remainder, incl. a
whitespace-only description falling through to `title` then `"Untitled task"`) ·
`portal/tests/SearchableSelect.test.tsx` (combobox role + `ariaLabel`; `aria-expanded`
toggles; typing filters the `option` rows; `aria-selected`; select calls `onChange` and
closes; Escape closes without changing the value; `maxVisible={8}` → `maxHeight: 18rem`) ·
`portal/tests/FilterPills.test.tsx` (empty → nothing; `Label: Value`; clicking
`Remove Assignee filter` calls only that `onRemove`; "Clear all" only with >1 pill).

**Create:** `src/lib/taskDisplay.ts`, `src/components/common/FilterPills.tsx`
**Modify:** `src/components/common/SearchableSelect.tsx`, `src/types/api.ts`
(`title?: string | null`, `task_date?: string`)

**Regression sweep:** grep the four existing consumers' tests (`MaterialsTable`,
`ActivitiesTable`, `AddRoleGapDialog`, `AddMaterialGapDialog`) for trigger queries that move
from `getByRole("button")` to `getByRole("combobox")`, and re-run them.

**Gates:** `npm test -- taskDisplay SearchableSelect FilterPills MaterialsTable ActivitiesTable AddRoleGapDialog AddMaterialGapDialog` · `npm run typecheck` · `npm run lint`

### Phase 7 — TaskDialog rework

**Tests first, in `portal/tests/TaskDialog.test.tsx`:**
- create: no Title input; no `Date *` input; the create payload carries **no** `title` and
  **no** `task_date` key
- create: the Description textarea precedes the Property combobox in DOM order
  (`compareDocumentPosition`, same idiom as the existing test at :242 — which must be
  re-pointed since the grid moved)
- create: a Status control exists, defaults to the first status, and ships in the payload —
  **inverts** the existing `"create mode shows the assignee select but no status select"`
- create: open Property, type `"Maple"`, only the matching `role="option"` remains
- create: Save is enabled with an empty description
- edit: `getByTestId("task-readable-id")` shows `T0001` and nothing can change it
- edit: the update payload carries no `title` / `task_date`; `TaskSentCheck` still renders
  for a converted task
- the three `userEvent.selectOptions` sites (:479, :499, :547) become open-then-click for
  Property/Assignee; Status keeps `selectOptions`
- **remove** the GPS auto-title tests (~:353, incl. the StrictMode one); **replace** with one
  asserting GPS auto-selects the **Property** under StrictMode

**Modify:** `src/components/tasks/TaskDialog.tsx` per the layout spec — plus: fetch statuses
unconditionally (drop the `if (isEdit)` at :131 and its dep), include `status` in the create
payload, rewrite the stale focus-effect comment at :157-159 (Modal's first focusable is now
the Record button), and replace the local `getPropertyLabel` (:57-61) with the shared
`propertyLabel` from `lib/propertyDisplay`. Drop `title` from the `ConvertTaskDialog` prop spread.

**Gates:** `npm test -- TaskDialog ConvertTaskDialog` · `npm run typecheck` · `npm run lint`

### Phase 8 — TasksPage: pills, ID chip, description headline

**Tests first, in `portal/tests/TasksPage.test.tsx`:**
- a card shows `T0001`; the headline is the description's first line and carries `truncate`
- **a task with a null `title` renders without crashing** — `task.title.toLowerCase()` at
  :257 and `a.title.localeCompare(b.title)` at :263 throw on `undefined` today
- searching `"T0001"` / `"t0001"` narrows to that task
- an assignee filter renders `Assignee: Bob Crew`; `Remove Assignee filter` clears it and
  reloads with `assignedTo: undefined`; status / property / Show archived each get a pill;
  three filters → three pills; none active → no pills
- A–Z sort orders by headline
- **rewrite** the filter tests at :299-385 — `getByLabelText(/filter by assignee/i)` still
  works, but `selectOptions` becomes click-trigger → click-option for assignee and property
- the card `aria-label` uses the headline

**Modify:** `src/pages/TasksPage.tsx` — `visibleTasks` searches `readable_id` + headline +
description and sorts by headline (`SortKey` `"title"` → `"name"`); `<FilterPills>` inserted
between the toolbar (ends :447) and the `moveError` alert (:449), specs built from the four
filter states via `getMemberLabel` / `statusNameById` / `propertyLabel`; the card gains a
`font-mono text-[11px] text-gray-400` ID chip, headlines via `taskHeadline`, and shows
`taskRemainder` as the body only when non-empty; `handleMoveTask` (:278-289) drops `title`
and `task_date`. Collapse `TaskFilterButton`'s duplicate `getPropertyLabel` (:22-26) and swap
its Assignee/Property selects for `SearchableSelect` (`maxVisible={8}`, empty-id "All …" row
prepended since the component has no clear affordance) — Status stays native.

**Gates:** `npm test -- TasksPage TasksPageNewTaskGate` · `npm run typecheck` · `npm run lint`

### Phase 9 — Remaining `task.title` consumers

**Tests first:** `TaskColumnView.test.tsx` (title-less task renders its headline; card and
move-select `aria-label`s use it) · `ConvertTaskDialog.test.tsx` (copy names the headline) ·
`UpcomingTasksCard.test.tsx` (keep the `data-testid="upcoming-task-title"` contract; content
becomes the headline).

**Modify:** `TaskColumnView.tsx:98,111,151` · `ConvertTaskDialog.tsx:93` ·
`UpcomingTasksCard.tsx:135-138` — all via `taskHeadline`.

**Gates:** `npm test -- TaskColumnView ConvertTaskDialog UpcomingTasksCard DashboardPage` · `npm run typecheck` · `npm run lint`

### Phase 10 (optional, decoupled) — Maple stops asking for a title on create

`agents/task/create.py` still asks "What should the task be called?" when a message has
neither a title cue nor usable content. Change the copy to "What should the task say?" and
route the bare reply into `description`, letting the title derive from it. Deferred because
it touches `_resolve_create_title` / `_CREATE_TITLE_PENDING_ID` / `_stash_awaiting_title`
and three agent test files, and the branch is rare. (The *rename* path is not deferred — it
is removed in Phase 3.)

**Tests:** `platform/tests/test_maple_task_crud.py`
**Gates:** `./run_tests.sh tests/test_maple_task_crud.py tests/test_maple_task_routing.py` · `./run_mypy.sh agents/task` · `./run_ruff.sh agents/task`

---

## Verification

**Backend, after Phases 1–5** (start the local DB first: `cd platform && ./scripts/start_test_mongo.sh`)

```bash
cd platform && ./run_tests.sh tests/test_readable_id.py tests/test_task_readable_id.py tests/test_task_title.py tests/test_tasks_api.py tests/test_task_resolver.py tests/test_maple_task_operations.py tests/test_maple_task_crud.py tests/test_backfill_task_readable_ids.py
```

Then the full-project gates (also enforced by the pre-push hook):

```bash
cd platform && ./run_mypy.sh && ./run_ruff.sh && ./run_bandit.sh
```

Backfill dry run against Dev before applying:

```bash
cd platform && source .venv/bin/activate && python scripts/backfill_task_readable_ids.py
```

**Frontend, after Phases 6–9**

```bash
cd portal && npm test && npm run typecheck && npm run lint
```

**End-to-end, manually** — `cd platform && uvicorn main:app --reload` (Dev cluster) plus
`cd portal && npm run dev`:

1. New Task → confirm no Title and no Date inputs, Description + Record/Photo/Video at the
   top, Status present and defaulting to the first status.
2. Type into Property with 20+ properties → search filters, list caps at 8 rows and scrolls.
   Same for Assign To.
3. Save → the new card shows a `T####` ID and headlines with the description, ellipsised.
4. Reopen it → the ID shows read-only in the dialog; edit the description and save; confirm
   the ID is unchanged (this is the PUT-preservation path).
5. Drag the card between kanban columns → confirm the ID and title survive
   (`handleMoveTask` is the highest-risk caller).
6. Filter popup → set assignee + property; confirm pills appear below the toolbar, each X
   clears just its own filter, and the Filter badge count follows.
7. Type the ID into the Tasks search box → the task is found.
8. Ask Maple "show me task T0001" → it resolves; confirm the returned details include the
   `- ID:` line.
9. Confirm a backfilled legacy task (one created before this change) shows its ID everywhere.

## Risks

| Risk | Mitigation |
|---|---|
| **PUT full-replace nulls server-owned fields** — `handleMoveTask` fires on every kanban drag | `readable_id`/`title`/`task_date` in the exclude set, each with an explicit "PUT omitting it preserves it" test. Log a follow-up for a real `TaskUpdate` schema. |
| **Unique index bricks app startup** — Beanie builds indexes at boot, before the backfill | `partialFilterExpression={"readable_id": {"$type": "string"}}`. `sparse=True` does not work on a compound index. |
| **Maple-created task shows a blank ID** — `TASKS_CHANGED_EVENT` repaints the open grid instantly | `agents/task/create.py` routes through `insert_task_with_readable_id`; guarded by a `test_maple_task_crud.py` assertion. |
| **Feature flag** — `require_tasks_feature` 404s the whole router | Every new backend test file needs the autouse `_enable_tasks_feature` fixture. The backfill bypasses the router, so it works with the flag off — that's the safe rollout order. |
| **Free-plan cap vs. sequence** — deletes free a slot but leave an ID gap | Allocate *after* `is_task_limit_reached`. Comment on `next_task_seq` that it is never a count. |
| **Derived titles drift from the description** | Re-derive on every write (HTTP PUT *and* Maple's `_apply_task_update`) from one shared helper. Maple's title-rename path is removed in Phase 3 so nothing can write a title that the next description edit would revert. |
| **`SearchableSelect` a11y change breaks 4 estimate test files** | Grep and re-run them in Phase 6 before touching Tasks. |
| **Slower interaction tests** — open-and-click beats `selectOptions` for wall time in two 800-line files | `TaskDialog.test.tsx` / `TasksPage.test.tsx` already set `HEAVY_FILE_TIMEOUT_MS`; re-check the tier in `tests/helpers/testTimeouts.ts` if flakes appear. |

## Documentation

- `documentation/development/code-review-followups.md` — log the deferred `SearchableSelect`
  arrow-key navigation and the `TaskUpdate` Pydantic schema.
- `documentation/development/maple-phrasing-reference.md` — Phase 4 **adds** a supported
  phrasing ("show me task T0001") and Phase 3 **removes** one (task rename-by-title). Per
  CLAUDE.md this must be updated in the same change: flip both status tags, update the §12.3
  counts, bump "Last updated".
- Changelog entries only on request (not added automatically).
