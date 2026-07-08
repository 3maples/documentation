# Tasks Feature — Field Capture → Estimate

> **v2 extension** (created-by/assignment, statuses + Settings CRUD, column view, filters):
> see [2026-07-07-tasks-v2-assignment-status-views.md](2026-07-07-tasks-v2-assignment-status-views.md).

## Context

Landscapers currently walk a client's property while the homeowner explains the job, try to remember everything, and only write it down back at the office. This feature adds a **Tasks** capability: start a Task on the phone while on-site, capture what needs doing via **voice (mic button, repeatable recordings) or typed text**, attach **photos** of the work areas, then later **convert the Task into an Estimate** using the existing AI generation pipeline. A new "Tasks" menu in the portal provides list + full CRUD, mobile-first since the primary use is a phone in the field.

**Confirmed product decisions (Simon):**
- Voice = same UX as Maple voice input: press mic → speak → end recording → transcript **appends** to the task description; repeat as needed.
- Conversion = AI-generated work items via the existing estimate-generation flow.
- Photos = human reference only in v1 (not sent to the AI). Stored in **MongoDB GridFS**.
- Maple chat integration out of scope for v1. Conversion offers an option to delete the task.
- A Task always has at least a **title and a date** (set at creation; date defaults to today). Voice input and photo capture happen **inside** the Task view, after it exists.

> **Note:** per project convention, copy this plan to `documentation/development/plans/2026-07-06-tasks-feature.md` as the first implementation step (plan mode couldn't write there).

## Design

### Task model (`platform/models/task.py`) — minimal, no status enum
```python
class TaskPhoto(BaseModel):
    file_id: PydanticObjectId          # GridFS file _id (full-size, client-downscaled)
    thumb_file_id: Optional[PydanticObjectId] = None  # GridFS _id of server-generated ~320px thumbnail
    filename: str
    content_type: str                  # image/jpeg|png|webp
    size_bytes: int
    uploaded_at: datetime

class Task(Document):
    title: str                         # REQUIRED — set when the task is created
    task_date: datetime                # REQUIRED — date of the site visit, defaults to today in the UI
    description: str = ""              # accumulated typed + voice text, captured inside the task
    photos: List[TaskPhoto] = []
    property: Optional[PydanticObjectId] = None   # optional link; contacts hang off Property — no contact link in v1
    estimate: Optional[PydanticObjectId] = None   # set on convert; presence == converted (YAGNI on enum)
    company: PydanticObjectId
    created_by_email: Optional[str] = None
    created_at / updated_at            # standard @before_event([Replace, Insert]) hook
    Settings: name="tasks", index (company, updated_at DESC)
```
Register in `models/__init__.py` and `database.py:init_db()`. Add `AuditAction.TASK_CREATE/UPDATE/DELETE/CONVERT` + `ResourceType.TASK`.

### Backend routes (`platform/routers/tasks.py`) — copy conventions from `routers/properties.py`
Auth: `Depends(verify_verified_firebase_token)` + `require_authenticated_user`, `assert_company_access`/`assert_user_company_access`, `@audit_log`, manager-only DELETE.
- `POST /tasks/` , `GET /tasks/?company=&search=`, `GET /tasks/{id}`, `PUT /tasks/{id}`, `DELETE /tasks/{id}` (cascades GridFS photo deletion)
- **Photos** (service `platform/services/task_photos.py`, GridFS bucket `task_photos` via `AsyncIOMotorGridFSBucket`):
  - `POST /tasks/{id}/photos` — multipart `UploadFile`; validate magic bytes (jpeg/png/webp allowlist) + 10MB cap, mirroring `services/transcription.py` validation style. On upload, also generate a **thumbnail** server-side with Pillow (already pinned): ~320px JPEG (~20-40KB), stored as a second GridFS file; `TaskPhoto` gains `thumb_file_id`. Write blobs first, then append `TaskPhoto` metadata (failure leaves a harmless orphan, never a broken ref).
  - `GET /tasks/{id}/photos/{photo_id}?size=full|thumb` — `StreamingResponse` with content-type (`thumb` used by list cards and grid tiles; `full` by the viewer)
  - `DELETE /tasks/{id}/photos/{photo_id}`
- **Convert**: `POST /tasks/{id}/convert  {delete_task: bool}` — synchronous (the existing AI create path is synchronous; verified [estimates.py:349-373](platform/routers/estimates.py:349)). Mirrors `create_estimate`'s AI branch:
  1. 409 if `task.estimate` already set; 422 if description empty.
  2. **Claim billing slot** — `claim_estimate_slot_with_status(company_doc)` with the same 402/429 mapping; `release_estimate_slot` on generation failure (Tasks must not bypass estimate metering).
  3. `CreateEstimateRequest(description=task.description, property=task.property, company=...)` → `prepare_generated_estimate()` → `save_generated_estimate()` (from `routers/estimate_helpers/ai_generation.py`).
  4. `delete_task=true` → delete GridFS photos + task; else set `task.estimate = estimate.id`.
  5. Return the estimate; portal navigates to `/estimates/{id}/with-activity`.

### Portal
- **Nav/routes**: add `Tasks` to `navItems` in `src/components/Layout/PortalLayout.tsx` (lucide icon, e.g. `ClipboardList`); routes in `src/App.tsx` under `ProtectedLayout`: `/tasks` (list) and `/tasks/:id` (full-screen capture page — a dedicated route, not a modal: capture needs the whole phone viewport; precedent `/estimates/new-with-activity`). Task *creation* is a small modal on the list page (title + date + property).
- **API**: `src/api/tasks.ts` (list/get/create/update/remove/uploadPhoto/removePhoto/convert) via `apiRequest<T>`; add `apiRequestBlob()` to `src/api/client.ts` for photo bytes (`<img src>` can't send bearer headers → fetch blob + `URL.createObjectURL`; the fetch interceptor at client.ts:189 injects auth for API-origin URLs). Types in `src/types/`.
- **TasksPage.tsx** — mobile-first **card list**, one card per task:
  - Card contents: **title**, first ~2-3 lines of the description (line-clamped), a **photo thumbnail** (first photo, if any), photo count, **last-updated date**, property name, and a "Converted" badge when `estimate` is set.
  - **Sort control**: by **Date** (last updated, newest first — default) or **Title** (A–Z); client-side sort. Plus text search.
  - Layout: single-column cards on phones, 2–3 column grid `md:`/`lg:`; tapping a card opens `/tasks/:id`. Prominent "+ New Task" button; delete via card menu with confirm — conventions from `PropertiesPage.tsx`.
  - Card thumbnails use a dedicated **thumbnail variant** (below) so the list doesn't pull full-size images over cell data.
- **Two-step flow — create first, capture inside the Task**:
  1. **NewTaskDialog** (`components/tasks/NewTaskDialog.tsx`, modal like `PropertyDialog.tsx`): required **title**, required **date** (defaults to today), optional property picker → `POST /tasks/` → navigate into the task.
  2. **TaskCapturePage.tsx** (`/tasks/:id`) — all voice/photo capture happens *inside* the existing Task, so every upload has a task to attach to (no lazy-create complexity):
     - Header: title + date (editable inline), property, converted badge.
     - Big textarea + **mic button** via new `components/tasks/TaskVoiceButton.tsx` wrapping `useVoiceInput({onTranscript})` ([useVoiceInput.ts](portal/src/components/Layout/useVoiceInput.ts)); each transcript **appends** (with separating newline) to the description; hide button when `!isSupported`; surface voice errors visibly. Description autosaves (debounced — precedent: NewEstimateWithActivityPage autosave).
     - **Photos**: `components/tasks/TaskPhotoGrid.tsx` + hidden `<input type="file" accept="image/*" capture="environment">`; each photo is downscaled client-side (`lib/downscaleImage.ts`: canvas, max 1600px, JPEG q0.8 → ~150-500KB; also normalizes iOS HEIC) and uploaded immediately — durable in the field; thumbnail grid with delete + full-size viewer.
- **ConvertTaskDialog.tsx**: confirm dialog with "Delete task after conversion" checkbox, blocking "Generating estimate…" busy state (double-submit guarded), on success navigate to `/estimates/{id}/with-activity`; on timeout, message points user to the Estimates list (estimate may still have been created — same exposure as today's create flow).

## Implementation Phases (TDD — failing test first in every phase)

| # | Work | Files (new unless noted) | Tests |
|---|---|---|---|
| 1 | Task model + CRUD API | `platform/models/task.py`; edit `models/__init__.py`, `database.py`, `models/audit_log.py` (actions), `routers/tasks.py`, edit `routers/__init__.py`, `main.py` | `platform/tests/test_tasks_api.py` |
| 2 | Photo upload/serve/delete + cascade | `platform/services/task_photos.py`; edit `routers/tasks.py` | `platform/tests/test_task_photos_api.py` |
| 3 | Convert endpoint (billing slot + AI reuse, agent stubbed like existing generation tests) | edit `routers/tasks.py` | `platform/tests/test_task_convert_api.py` |
| 4 | Portal API + nav + list page + create dialog (title/date/property) | `portal/src/api/tasks.ts`, `src/pages/TasksPage.tsx`, `src/components/tasks/NewTaskDialog.tsx`; edit `src/api/client.ts` (apiRequestBlob), `PortalLayout.tsx`, `App.tsx` | `portal/tests/TasksPage.test.tsx` |
| 5 | In-task capture page (voice + photos) | `src/pages/TaskCapturePage.tsx`, `src/components/tasks/TaskVoiceButton.tsx`, `TaskPhotoGrid.tsx`, `src/lib/downscaleImage.ts` | `portal/tests/TaskCapturePage.test.tsx` |
| 6 | Conversion UI | `src/components/tasks/ConvertTaskDialog.tsx`; wire into list + capture pages | `portal/tests/ConvertTaskDialog.test.tsx` |

Per-phase gates: platform — `./run_mypy.sh <touched subtree>` + `./run_ruff.sh <touched>` + `./run_tests.sh tests/test_task*.py`; portal — `npm run typecheck` + `npm test -- <file>`. Commits/pushes each need Simon's explicit approval; author `3maples <admin@3maples.ai>`.

## Risks
- **`voice_input_enabled` flag**: `/agents/transcribe` 403s when off — confirm it's enabled in the target envs; per-company transcribe rate limiter may bite repeated field captures.
- **Sync convert latency** on mobile networks — busy dialog + "check Estimates list" timeout message.
- **Memory**: photos processed one at a time; 10MB server cap (UploadFile reads into memory, same pattern as transcribe's 20MB).
- **iOS quirks**: mic (mp4 fallback) already handled by `useVoiceInput`; HEIC normalized by canvas re-encode; camera capture attr is a hint, file picker is the fallback.

## Verification
1. Backend: `./run_tests.sh tests/test_tasks_api.py tests/test_task_photos_api.py tests/test_task_convert_api.py` (local test mongo — GridFS works there natively), plus mypy/ruff on touched trees.
2. Portal: `npm test` for the three new test files, `npm run typecheck`, `npm run build`.
3. Manual dev-server pass (uvicorn + `npm run dev`): create task via dialog (title + date required, date defaults to today) → land in the task → dictate twice (transcripts append) → add 2 photos from picker → reload (persisted) → convert with AI (work items appear) → land on `/estimates/{id}/with-activity` → task shows converted badge; repeat with "delete after conversion" checked; verify manager-only task delete removes GridFS blobs (full + thumb). On the list: cards show title / snippet / thumbnail / last-updated date, and sorting toggles between Date and Title.
4. Mobile check: browser devtools mobile viewport for layout, then a real-iPhone pass (mic requires HTTPS, camera capture, convert round-trip).
