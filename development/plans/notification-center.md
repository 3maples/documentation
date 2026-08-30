# In-App Notification Center (Task Assignment Notifications)

## Context

When someone assigns a Task to another user, the assignee currently gets no signal — they only discover it by browsing the Tasks page. This adds an in-app notification center: a bell at the bottom of the left nav panel with an unread-count badge, a dialog listing notifications with click-through to the Task detail dialog, per-notification delete, and a schema deliberately extensible to future notification types. Works on mobile.

**User-confirmed decisions:**
- Bell placement: bottom of the left panel (desktop sidebar footer + mobile nav drawer).
- Freshness: polling ~60s + refresh on window focus/visibility (no SSE/WebSocket/Firestore).
- Read model (GitHub-style): opening the dialog marks all as **seen** → badge clears; each item keeps an unread dot until individually clicked → **read**.

**Key facts from exploration:** assignee is `Task.assigned_to_email` (an email string, defaults to creator); no notification infra exists; a Beanie `@after_event` hook can't see the old assignee (transition, not state), so producers are explicit calls at the write sites; frontend has a shared `Modal` with nested-dialog support (`modalCloseStack`), an established badge pattern, and `useSupportUnread` as the layout-level badge-hook precedent. TDD is mandatory (failing test first, per CLAUDE.md).

---

## Backend (platform/)

### 1. Model — new `platform/models/notification.py`

```python
class NotificationType:  # str constants, NOT an Enum — unknown types must still deserialize
    TASK_ASSIGNED = "task_assigned"

class Notification(Document):
    company: PydanticObjectId
    recipient_email: str          # ALWAYS lowercased on write
    type: str                     # NotificationType.* constant
    title: str                    # server-rendered display string
    body: str                     # server-rendered display string
    payload: Dict[str, Any] = Field(default_factory=dict)  # click-through data
    seen_at: Optional[datetime] = None   # badge tier — cleared when dialog opens
    read_at: Optional[datetime] = None   # dot tier — cleared when item clicked
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
- Collection `notifications`. Indexes: `(company, recipient_email, created_at desc)`; `(company, recipient_email, seen_at)` for the badge count; TTL on `created_at` with `expireAfterSeconds=90*24*3600` (auto-prune; add the "Mongo won't drop/modify undeclared indexes — changing TTL needs collMod" warning comment, style of `models/task.py:70-87`).
- Server-rendered `title`/`body` + typed `payload` means future notification types render in old portal builds; `task_assigned` payload: `{"task_id", "task_readable_id", "task_title", "assigned_by_email"}`.

**Registration (3 edits):** `models/__init__.py` (import + `Notification.model_rebuild()`), `database.py` `document_models` list, and `tests/conftest.py` `COMPANY_SCOPED_COLLECTIONS` += `("notifications", "company")` (tuple-of-tuples format verified at conftest.py:124-145) — `tests/test_test_data_cleanup_coverage.py` failing without it is the phase's red test. The conftest entry also makes the test suite's session-level cleanup cascade-delete notifications created by tests.

### 1b. Cascade delete on company deletion

There is no in-app company hard-delete (ops only archives); the cascade deleters are two scripts, each with its own hardcoded model list:
- [scripts/cleanup/cleanup_company.py](platform/scripts/cleanup/cleanup_company.py) (`cleanup_company_resources`, L90-163) — add `Notification` (`Notification.company == company_id`) via `_delete_collection`, and update the docstring.
- [scripts/cleanup/cleanup_test_data.py](platform/scripts/cleanup/cleanup_test_data.py) (its own `cleanup_company_resources`, L140+) — add `Notification` the same way.

**Pre-existing gap, fixed in passing (house rule: fix and report):** both scripts are stale — they predate Tasks and are missing `Task`, `TaskStatus`, `SupportConversation`, `Template`, `Division`, `RateCard`, `WorkItemSummary` (and `LlmUsageEvent`/`BillingEvent`, which are nullable-company — delete by explicit company id only, matching conftest's `NULLABLE_COMPANY_COLLECTIONS` note). Add all current company-scoped models to both scripts so `cleanup_company.py`'s "deletes ALL data" docstring is true again.

**Durable guard:** extend `tests/test_test_data_cleanup_coverage.py` (or a sibling test) to also assert the two scripts' model lists cover every collection in `COMPANY_SCOPED_COLLECTIONS` — so the next new company-scoped model can't silently miss the cascade again. (Import each script's module and compare the models it deletes against the conftest registry.)

### 2. Producer — new `platform/services/notifications.py`

- `create_notification(*, company, recipient_email, type, title, body, payload)` — lowercases recipient, inserts. The only generic write path.
- `notify_task_assignment(task, previous_assignee, actor_email)` — rules (each a unit test):
  - no-op if `task.assigned_to_email` falsy;
  - normalize all emails `.strip().lower()` before comparing;
  - no-op if new == previous (case-insensitive) — unchanged PUTs;
  - no-op if new == actor — no self-notification (covers create's default-to-creator and Maple create, which always assigns to the acting user);
  - **fail-open**: whole body in `try/except Exception: logger.warning(...)` — a notification insert must never fail a task save;
  - no recipient validation (Maple accepts arbitrary emails; an unaddressable notification is inert and TTL-pruned);
  - content: `title="Task assigned to you"`, `body=f"{actor or 'Someone'} assigned you {task.readable_id}: {task.title}"`.

**Wiring — exactly 3 call sites (all verified):**
1. [routers/tasks.py:131](platform/routers/tasks.py:131) `create_task` — after `insert_task_with_readable_id(task)`: `notify_task_assignment(task, previous_assignee=None, actor_email=current_user.email)`.
2. [routers/tasks.py:307](platform/routers/tasks.py:307) `update_task` — after `existing_task.set(...)`, only `if "assigned_to_email" in patch`; old value from `before_state.get("assigned_to_email")` (already snapshotted at L292); actor from `decoded_token.get("email")` (this handler has no `current_user`).
3. [agents/task/operations.py:65](platform/agents/task/operations.py:65) `_finish_task_update` — the single Maple choke point (`_handle_task_assign` and `field_flow.py` both funnel here). Capture `previous_assignee = task.assigned_to_email` **before** `_apply_task_update`; after it, `if "assigned_to_email" in changes`, notify with `actor_email=working_context.get("current_user_email")` (verified: that key already exists — operations.py:253, 459). Do NOT put this in `_apply_task_update` (a `@staticmethod` with no actor context).

Explicitly **not** a Beanie `@after_event` hook — assignment is a transition and after-event hooks only see new state.

### 3. Router — new `platform/routers/notifications.py`

`APIRouter(prefix="/notifications", tags=["notifications"])`, **not** gated by `require_tasks_feature` (generic center; the `task_assigned` producers already live behind task paths). All endpoints: `current_user: User = Depends(require_authenticated_user)`; identity = `user.email.strip().lower()`; tenancy via `assert_user_company_access(user, company_id)`.

| Endpoint | Behavior |
|---|---|
| `GET /notifications?company=&limit=` | Caller's own only, `-created_at`, style-A pagination (`limit ge=1` + `X-Total-Count`, copy routers/tasks.py:161-238), `response_model=List[Notification]` |
| `GET /notifications/unread-count?company=` | `{"count": N}` counting `seen_at == None` — the cheap 60s poll target |
| `POST /notifications/mark-seen?company=` | `update_many` set `seen_at=now` where `seen_at == None`; `{"status": "ok"}` |
| `POST /notifications/{id}/mark-read` | 404 on missing **or recipient mismatch** (don't leak existence); sets `read_at`, and `seen_at` too if still None; returns doc |
| `DELETE /notifications/{id}` | Same 404-on-mismatch; delete; `{"status": "ok"}` |

Declare `/unread-count` and `/mark-seen` before the `/{notification_id}` routes. Register in `routers/__init__.py` + `main.py` with `protected_route_dependencies`.

---

## Frontend (portal/)

### 4. API modules
- New `portal/src/api/notifications.ts` (model on `src/api/support.ts`): `AppNotification` type (`_id, type, title, body, payload, seen_at, read_at, created_at`) + `notificationsApi = {list, unreadCount, markSeen, markRead, remove}`, company via `requireCompanyId()`.
- Edit `portal/src/api/tasks.ts`: add `get(id)` → backend `GET /tasks/{id}` exists (routers/tasks.py:241). Needed because `TaskDialog` takes a full `Task` object and the `?taskId=` deep link only matches currently-loaded/filtered tasks.

### 5. Hook — new `portal/src/lib/useNotifications.ts`
`useNotifications(enabled): {unreadCount, refresh}` — mirrors `useSupportUnread.ts` (mounted at layout level so the badge works with the dialog closed) but polls: initial fetch, `setInterval` 60s with cleanup, `window focus` + `visibilitychange` (only when visible) listeners, errors swallowed. `refresh()` stable, used by the dialog after mark-seen/read/delete.

### 6. Bell UI — edit `portal/src/components/Layout/PortalLayout.tsx`
- Mount `useNotifications` next to `useSupportUnread` (~L119); add `showNotifications` state; lucide `Bell`; badge markup copied from the Support-tab pattern (L180-184: `absolute -top-1 -right-1 min-w-4 h-4 px-1 rounded-full bg-red-500 text-white text-[10px] …`).
- Desktop footer block (L430-509): collapsed branch — bell button in the stacked column between expand button and avatar; expanded branch — bell button (same styling as the collapse button) in the row before the collapse button. `aria-label="Notifications"`.
- Mobile drawer (L553-681): full-width "Notifications" row (Bell + label + badge) in the drawer's account area; tap → close drawer, open dialog.
- Hamburger button (L686-695): overlay the same badge when `unreadCount > 0` so mobile users see unread without opening the drawer.
- Render `<NotificationsDialog open={showNotifications} onClose onBadgeRefresh={refresh} />` once near the layout root. The existing `canOpenMobileMenu()` `[aria-modal="true"]` guard already suppresses drawer swipe while it's open.

### 7. Dialog — new `portal/src/components/notifications/NotificationsDialog.tsx`
Built on `src/components/common/Modal.tsx` (NOT the legacy `ui/dialog.tsx`), `fullScreenOnMobile` (TaskDialog precedent; `modalCloseStack` makes the nested TaskDialog own Escape/focus).
- On open: `list()` → local state, then `markSeen()` → `onBadgeRefresh()` (badge clears; just-fetched items keep local `read_at`, so unread dots stay).
- Item: registry icon, title (medium weight when unread), body, relative timestamp, brand-colored unread dot when `!read_at`, trash button (`stopPropagation` → `remove(id)` → drop row → `onBadgeRefresh()`). Empty state: Bell + "You're all caught up".
- **Extensibility registry:** `NOTIFICATION_HANDLERS: Record<string, {icon, onClick?}>` — unknown types render title/body with a default icon and no click action.
- `task_assigned` click: optimistic `markRead(id)` + local `read_at`; `tasksApi.get(payload.task_id)` → nested `<TaskDialog>` (UpcomingTasksCard precedent); `onSaved` → dispatch `TASKS_CHANGED_EVENT` so an open TasksPage refreshes. 404 (task deleted) → inline "This task no longer exists"; do **not** auto-delete (deletion stays the user's explicit action).

---

## Test plan

**Backend — new `tests/test_notifications_api.py`:** list scoped to caller + newest-first + limit + `X-Total-Count`; cross-company → 403; unread-count counts `seen_at==None` only; mark-seen zeroes badge but leaves `read_at` (two-tier assertion); mark-read sets both, other user's id → 404; delete + 404-on-mismatch (doc survives).

**Backend — new `tests/test_task_assignment_notifications.py`** (autouse tasks-feature monkeypatch, copy test_tasks_api.py:19-21): POST with other-user assignee → 1 notification with correct payload + lowercased recipient; POST defaulting to creator → 0; PUT reassign → 1 with actor; PUT same assignee different case → 0; PUT self-assign → 0; direct unit tests of `notify_task_assignment` rule matrix incl. fail-open (patched `Notification.insert` raising must not propagate); extend existing `_handle_task_assign` agent tests for the Maple path if a harness exists.

**Backend — updated:** `tests/conftest.py` `COMPANY_SCOPED_COLLECTIONS`.

**Frontend — new:** `tests/useNotifications.test.tsx` (fake timers: initial/60s/focus/visibility fetch, cleanup, disabled); `tests/NotificationsDialog.test.tsx` (render, unread dots, markSeen-on-open + badge refresh, task click → markRead + `tasksApi.get` + TaskDialog mount, 404 message, delete, empty state); `tests/PortalLayoutNotifications.test.tsx` (bell present, badge count / hidden at 0, opens dialog, drawer row).

**Frontend — updated (will break otherwise):** `tests/PortalLayoutSwipe.test.tsx` (stub block L17-72) and `tests/PortalLayoutTourPanel.test.tsx` — add `vi.mock` stub for `useNotifications`.

---

## Phasing (TDD, each phase independently green/committable)

0. **Plan doc** → `documentation/development/plans/notification-center.md` (documentation repo). No changelog (user-triggered separately).
1. **Model + registration + cascade delete** (platform) — red via cleanup-coverage test (extended to pin the two cleanup scripts' model lists). Includes updating both `scripts/cleanup/*` scripts with `Notification` and the other missing company-scoped models (§1b). Gates: `./run_mypy.sh`, `./run_ruff.sh` scoped, targeted pytest.
2. **Notifications router** (platform) — red: `test_notifications_api.py`.
3. **Producer + 3 wiring sites** (platform) — red: `test_task_assignment_notifications.py`; regression: `test_tasks_api.py` stays green.
4. **API modules + hook** (portal) — red: `useNotifications.test.tsx`. Gates: scoped `npm test`, `npm run typecheck`, lint.
5. **Bell UI in PortalLayout** (portal) — red: `PortalLayoutNotifications.test.tsx`; update the two existing PortalLayout test stubs in the same commit.
6. **NotificationsDialog + click-through** (portal) — red: `NotificationsDialog.test.tsx`.

Commits/pushes each need fresh explicit approval per house rules.

## Verification (end-to-end)
- Backend: `./run_tests.sh tests/test_notifications_api.py tests/test_task_assignment_notifications.py tests/test_tasks_api.py` (local test Mongo via `./scripts/start_test_mongo.sh`); `./run_mypy.sh` / `./run_ruff.sh` scoped per touched subtree.
- Frontend: scoped `npm test` per phase; `npm run typecheck` + `npm run lint` before any push (pre-push hook enforces).
- Manual: run platform + portal dev servers; as user A assign a task to user B; in user B's browser confirm badge appears within ~60s (and immediately on tab refocus), dialog lists it with unread dot, badge clears on open, dot clears on click, TaskDialog opens with the task, delete removes it. Check mobile viewport (~375px): drawer row, hamburger badge, full-screen dialogs, swipe suppressed while dialog open.

## Risks / edge cases
- **Email casing** is the highest-likelihood silent-failure bug (`assigned_to_email` is raw; `User.email` matching is case-insensitive) — lowercase on write, lowercase queries, lowercase comparisons; pinned by Phase 3 tests.
- A→B→A flip-flop yields two notifications — accepted, each was a real event; no dedupe/transaction.
- Orphan notifications (arbitrary Maple assignee emails) are inert and TTL-pruned at 90 days.
- Badge truth is always `unread-count`; the dialog refreshes it rather than decrementing locally.
- Notifications router ungated; if a future gated feature needs gating, gate the *producer*, never the center.
