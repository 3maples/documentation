# Tasks v2 — Assignment, Statuses, Column View, Filters

> Extends the shipped v1 feature ([2026-07-06-tasks-feature.md](2026-07-06-tasks-feature.md)).
> Everything here stays behind the existing `TASKS_ENABLED` / `VITE_TASKS_ENABLED` flags.

## Context

v1 Tasks capture field notes and convert to estimates, but have no ownership or workflow state. v2 adds:
- **Created by** — surfaced on each task (already stored as `created_by_email`).
- **Assigned to** — a task can be assigned to a team member; defaults to the creator.
- **Status** — predefined **To Do / In Progress / Done**, plus company-defined statuses managed (full CRUD) from the Settings page.
- **Column view** — the Tasks page gains a Card ⇄ Column toggle; Column view maps one column per status, horizontally swipeable on mobile.
- **Filters** — Assigned-to and Status filters on the main Tasks page.

## Design

### Data model

**New collection `task_statuses`** (`platform/models/task_status.py`), patterned on `Division`:
```python
class TaskStatus(Document):
    name: str
    order: int = 0                      # column order; drives Column view
    company: PydanticObjectId
    created_at / updated_at             # standard @before_event hook
    Settings: name="task_statuses", index (company, order)
```
- **Seeding:** lazy — `GET /task-statuses` seeds `To Do (0)`, `In Progress (1)`, `Done (2)` when the company has none. Covers existing companies with no migration.
- Register in `models/__init__.py` + `database.py`; add `AuditAction.TASK_STATUS_*` + `ResourceType.TASK_STATUS`.

**`Task` model additions** (`platform/models/task.py`):
```python
assigned_to_email: Optional[str] = None   # server defaults to created_by_email on insert
status: Optional[PydanticObjectId] = None # ref to TaskStatus; None renders as the first status
```
- `created_by_email` already exists (set server-side on create) — no schema change, just surface it in the UI.
- On task create: if `assigned_to_email` empty → creator's email; if `status` empty → company's first status (seeding statuses if needed).
- Existing v1 tasks have `status=None`: UI treats `None` as the first (lowest-order) status; the next PUT normalizes it. No migration script.

### Backend endpoints

**New router `platform/routers/task_statuses.py`** — prefix `/task-statuses`, same `require_tasks_feature` 404-gate as `/tasks`, conventions from `routers/divisions.py`:
- `GET /task-statuses/?company=` — list ordered by `order` (lazy-seeds defaults).
- `POST /task-statuses/` — create (manager-only, like other settings resources).
- `PUT /task-statuses/{id}` — rename / reorder.
- `DELETE /task-statuses/{id}` — **blocked with 409 if any task references it** ("N task(s) still use this status — move them first"). Deleting the last remaining status is also refused. Safer and more informative than silent reassignment.

**`GET /tasks/` filters** — new optional query params, combinable with `search`:
- `assigned_to=<email>` — exact match on `assigned_to_email`.
- `status=<status_id>` — matches `Task.status`; passing the first status's id also matches `status=None` (legacy tasks), so the default column is complete.

### Portal

**API/types** (`src/api/tasks.ts`, `src/types/api.ts`): `TaskStatus` type; `taskStatusesApi` (list/create/update/remove); `tasksApi.list` gains `{assignedTo, status}` params; `Task` type gains `assigned_to_email`, `status`, and `created_by_email` is already present.
Team members for the assignee picker/filter come from the existing `GET /users/?company=` (used by Settings → Team).

**Settings page — "Task Statuses" tab** (`SettingsPage.tsx` tabs array + new `components/settings/TaskStatusesTab.tsx`, patterned on the Divisions/Material Units tabs):
- Table of statuses with inline rename, add, delete (surfacing the 409 message), and ▲/▼ reorder (swaps `order`).
- Tab only appears when `isTasksFeatureEnabled()`.

**Task capture page** (`TaskCapturePage.tsx`):
- Details card gains **Status** (dropdown of company statuses) and **Assigned to** (dropdown of team members) selects beside Date/Property; both autosave like the other fields.
- Read-only "Created by {name/email}" line in the header area.

**Task dialog** (revised 2026-07-08, twice — Simon wants tasks fully dialog-based like the other resources): a single `TaskDialog` handles **create and edit**. Create mode: title/date/property + notes (typed **or dictated via the mic**) + photos staged locally (removable previews) and uploaded right after create; on success the dialog closes back to the list (no navigation). The title defaults to the GPS place name (`Guelph, Ontario`) via `src/lib/locationLabel.ts` — browser Geolocation + BigDataCloud's keyless client reverse-geocode endpoint; "Untitled Task" shows until the lookup resolves and stays when no location is available, and the lookup never overwrites a title the user has started editing. Edit mode: clicking a task card or column-view card opens the same dialog prefilled, adding Status + Assignee selects; photo add/delete hits the server immediately, text fields save on Save. Assignment and status still default server-side on create. `NewTaskDialog` was superseded; the `/tasks/:id` capture page and route remain for deep links but the list flow no longer navigates there.

**Tasks page** (`TasksPage.tsx`):
- **View toggle** Card ⇄ Column in the toolbar (lucide `LayoutGrid`/`Columns3`), persisted in `localStorage` (`portal.tasksView`), default Card.
- **Filters** in the toolbar (both views): *Assigned to* (All / each team member) and *Status* (All / each status) — same select styling as the Properties city filter.
- **Cards** (both views) additionally show the status as a small badge and the assignee (initials chip or short name).
- **Card view**: unchanged otherwise (Date/Title sort).
- **Column view** (`components/tasks/TaskColumnView.tsx`):
  - One column per status, in `order`; tasks grouped by `status` (`None` → first column), newest-updated first within a column.
  - Column: header (status name + count), vertically scrollable card stack (same card component).
  - **Mobile**: horizontal swipe — container `flex overflow-x-auto snap-x snap-mandatory`, columns `snap-start shrink-0 w-[85vw] sm:w-72`.
  - **Status change**: a status dropdown on each card (in Column view) moves the task between columns via `tasksApi.update`. Drag-and-drop is deliberately **out of scope for v2** (adds a DnD dependency + touch complexity); can be a v3 if the dropdown feels clunky.
  - Status filter while in Column view shows only the matching column.

## Implementation phases (TDD — failing test first)

| # | Work | Files (new unless noted) | Tests |
|---|---|---|---|
| 1 | TaskStatus model + `/task-statuses` CRUD, lazy seeding, delete protection, flag gate | `platform/models/task_status.py`, `platform/routers/task_statuses.py`; edit `models/__init__.py`, `models/audit_log.py`, `database.py`, `routers/__init__.py`, `main.py` | `platform/tests/test_task_statuses_api.py` |
| 2 | Task fields: `assigned_to_email` default, `status` default-first, list filters (`assigned_to`, `status` incl. legacy-None) | edit `platform/models/task.py`, `platform/routers/tasks.py` | extend `platform/tests/test_tasks_api.py` |
| 3 | Portal API/types + Settings "Task Statuses" tab (flag-gated) | `portal/src/components/settings/TaskStatusesTab.tsx`; edit `src/api/tasks.ts`, `src/types/api.ts`, `src/pages/SettingsPage.tsx` | `portal/tests/TaskStatusesTab.test.tsx` |
| 4 | Capture page: status + assignee selects, created-by display; card badges | edit `TaskCapturePage.tsx`, `TasksPage.tsx` card | extend `portal/tests/TaskCapturePage.test.tsx` |
| 5 | Tasks page: Assigned/Status filters + view toggle persistence | edit `TasksPage.tsx` | extend `portal/tests/TasksPage.test.tsx` |
| 6 | Column view: per-status columns, mobile snap scroll, card status dropdown, column-status filter | `portal/src/components/tasks/TaskColumnView.tsx`; edit `TasksPage.tsx` | `portal/tests/TaskColumnView.test.tsx` |

Per-phase gates as usual: platform `./run_mypy.sh` + `./run_ruff.sh` + scoped `./run_tests.sh`; portal `npm run typecheck` + `npm run lint` + scoped `npm test`.

## Decision points (recommendations baked in above)

1. **Status deletion policy**: block with 409 while in use (vs auto-reassign). Chosen: block — explicit and reversible.
2. **Column-view status change**: dropdown on card now, drag-and-drop deferred.
3. **Assignee identity**: email (consistent with `created_by_email` and auth identity throughout the app), not user ObjectId.
4. **Legacy tasks without status**: rendered/filtered as the first status; normalized on next save. No migration.

## Verification

1. Backend: `./run_tests.sh tests/test_task_statuses_api.py tests/test_tasks_api.py tests/test_task_convert_api.py tests/test_tasks_feature_flag.py`.
2. Portal: scoped vitest files + `npm run typecheck` + `npm run build`.
3. Manual: Settings → Task Statuses (add "Waiting on client", rename, reorder, delete-blocked when used); new task defaults to creator + To Do; reassign + change status from capture page; Tasks page filters by assignee/status; toggle Column view, move a task between columns via dropdown, verify mobile swipe in devtools + on phone; convert flow unaffected.
