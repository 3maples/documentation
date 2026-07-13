# Tasks v3 — Create-mode Assignee, Video, Due Dates, Timestamp Hardening, Age Pill, Combined Filter

> Extends the shipped v2 feature ([2026-07-07-tasks-v2-assignment-status-views.md](2026-07-07-tasks-v2-assignment-status-views.md)).
> Everything stays behind the existing `TASKS_ENABLED` / `VITE_TASKS_ENABLED` flags.

## Context

Tasks v1 (capture + convert) and v2 (assignment, statuses, kanban, filters) are shipped. v3 adds:

1. **Assigned To** available during new-task creation (today it's edit-mode only in `TaskDialog`).
2. **Video attachments** on tasks (photos-only today).
3. **Due Date** on tasks, default None.
4. **created_at / updated_at read-only** — today a client can backdate `created_at` on POST (raw `Task` body) and overwrite `updated_at` on PUT (`.set()` bypasses the Beanie `before_event` hook and doesn't exclude it).
5. **Age** derived from `created_at`.
6. **Age pill**: GREEN by default; AMBER on the due date's day; RED past due; no due date → always GREEN.
7. **One Filter button** combining Assignee + Status, plus a new **Property** filter.

## Design decisions

### D1. Video — reuse the photo pipeline, don't fork it
- Keep the `photos` field and `TaskPhoto` model; `content_type` is the image/video discriminator. Videos store `thumb_file_id=None` (already Optional). No migration, endpoints stay `/tasks/{id}/photos...`.
- Allowlist `video/mp4`, `video/quicktime`, `video/webm` with magic-byte sniffing in `platform/services/task_photos.py` (MP4/MOV: `content[4:8] == b"ftyp"`; WebM: EBML `b"\x1a\x45\xdf\xa3"`).
- `MAX_VIDEO_SIZE_BYTES = 100MB` (images stay 10MB). The router's early `file.size` header check picks the cap by declared content type so a 50MB video isn't rejected at the header stage.
- New `validate_media_upload(content, content_type)` dispatcher → existing `validate_image_upload` or new `validate_video_upload`. `store_photo_blobs` skips `build_thumbnail` for `video/*` and returns `(file_id, None)`.
- `GET .../photos/{id}?size=thumb` for a **video** returns **404** (the current thumb→full fallback would ship 100MB to a 64px tile). Images keep the fallback.
- No HTTP Range support needed: the portal fetches auth'd blobs into object URLs, and `<video src={blobUrl}>` seeks client-side. No ffmpeg poster frames (future work).
- Portal: a separate "Add video" button + second hidden input (`accept="video/mp4,video/quicktime,video/webm"`) so the photo input's iOS camera behavior is untouched; skip `downscaleImage` for `file.type.startsWith("video/")` in both upload paths; client-side 100MB pre-check.
- Display: video tiles show a dark placeholder with lucide `Video` icon (never fetch `size=thumb`); `PhotoViewer` renders `<video controls playsInline>` for videos; `TaskCardThumb` picks the first **image** or the video placeholder; cards get a video-count chip beside the photo count.
- Convert/delete cascades already work: convert never copies photos, and `delete_photo_blobs` already skips `None` thumb ids.

### D2. Timestamp hardening (server-enforced)
- POST: force `task.created_at = datetime.now(timezone.utc)` next to the existing `created_by_email` forcing. (`updated_at` on insert is already covered by the hook.)
- PUT: add `updated_at` to the `.set()` exclude set and stamp `payload["updated_at"] = now(utc)` explicitly.
- Same phase: also exclude `company` and `created_by_email` from the PUT payload — today a forged PUT can move a task cross-company / rewrite attribution. Portal resends these unchanged, so behavior-compatible.

### D3. Due date
- `due_date: Optional[datetime] = None` on `Task`; legacy docs deserialize as None — no migration.
- Date-only semantics, evaluated in the viewer's local timezone client-side. Portal stores it like `task_date`: midnight local as an instant; empty ↔ `null`.
- **Propagation trap**: PUT is a full replace, so every PUT payload builder must carry `due_date` or it silently clears — three call sites: `TaskDialog.saveTask`, `TasksPage.handleMoveTask` (kanban move), `TaskCapturePage` save payload. Each gets a regression test.
- UI: "Due date" `type="date"` input in TaskDialog (create + edit), default empty.

### D4. Age pill
- Pure module `portal/src/lib/taskAge.ts`: `taskAgeLabel(createdAt, now?)` — floored whole-local-calendar-day age (`"Today"`, `"1d"`, `"12d"`); `taskAgeTone(dueDate, now?)` → green (no due date or before due day) / amber (due today) / red (past due day).
- `portal/src/components/tasks/TaskAgePill.tsx` using the existing rounded-full pill idiom (`bg-green-100 text-green-700` / amber / red), `title` tooltip with created + due dates. Shown on card-view and column-view cards.

### D5. Combined Filter button + Property filter
- New `portal/src/components/tasks/TaskFilterButton.tsx` patterned on `EstimateStatusFilter.tsx` (trigger + absolute panel, outside-click/Escape close).
- Trigger: lucide `Filter` icon + active-count badge (0–3). Panel: Assignee / Status / Property selects + "Clear filters".
- Replaces the two toolbar selects on `TasksPage`; adds `propertyFilter` state; `loadTasks` passes `property`. Column-view status-narrowing keeps reading `statusFilter` unchanged.
- Backend: `GET /tasks/` gains `property` query param (invalid id → 422, like `status`); `(company, property)` index on Task.

### D6. Assignee on create
- Un-gate only the **Assignee** select in create mode (Status stays edit-only — it defaults server-side and kanban is where it changes). Load team members regardless of `isEdit`.
- Create mode gets `<option value="">Me (default)</option>`; create payload includes `assigned_to_email` only when the user picked someone, so the server default (creator) still applies.

### Declined / deferred
- `formatDate` consolidation (TasksPage local vs `src/lib/format.ts`) — different visible formats, no user value; skip.
- ffmpeg poster frames, Range streaming, chunked GridFS upload streaming, "No property" filter sentinel — future work.

## Phases (TDD — failing test first)

| # | Work | Files | Tests first |
|---|---|---|---|
| 1 | Timestamp hardening | `platform/routers/tasks.py` | extend `tests/test_tasks_api.py` |
| 2 | `due_date` field + `property` list filter + index | `platform/models/task.py`, `platform/routers/tasks.py` | extend `tests/test_tasks_api.py` |
| 3 | Video upload backend | `platform/services/task_photos.py`, `platform/routers/tasks.py` | extend `tests/test_task_photos_api.py` |
| 4 | Portal types/API + age lib | `src/types/api.ts`, `src/api/tasks.ts`; new `src/lib/taskAge.ts`, `src/lib/media.ts` | new `tests/taskAge.test.ts` |
| 5 | TaskDialog: create-mode assignee + due-date input; due_date in all PUT payloads | `TaskDialog.tsx`, `TasksPage.tsx`, `TaskCapturePage.tsx` | update `TaskDialog.test.tsx`, extend `TasksPage.test.tsx`, `TaskCapturePage.test.tsx` |
| 6 | Video in UI | `TaskDialog.tsx`, `TaskPhotoGrid.tsx`, `TasksPage.tsx`, `TaskColumnView.tsx` | extend dialog/grid/page tests |
| 7 | Age pill placement | new `TaskAgePill.tsx`; `TasksPage.tsx`, `TaskColumnView.tsx` | new `TaskAgePill.test.tsx` |
| 8 | Filter button | new `TaskFilterButton.tsx`; `TasksPage.tsx` | rewrite filter tests in `TasksPage.test.tsx` |

Platform stream (1–3) and portal stream (4–8) are independent; 5 depends on 2+4, 6 on 3+4, 8 on 2.

## Edge cases
- Legacy tasks: missing `due_date` → None → always-green pill; age still from `created_at`.
- Any PUT payload builder missing `due_date` silently wipes it (three call sites covered).
- Video `size=thumb` must 404 server-side and never be requested client-side.
- First media item is a video → card thumb picks first image or placeholder.
- Filters combine as AND; first-status filter still folds in legacy `status=None`.
- Header-stage size check must use the per-type cap.

## Risks
- 100MB `await file.read()` buffers in RAM per upload (consistent with the photo path); chunked streaming is a follow-up.
- GridFS/Atlas storage grows much faster with video — monitor; cap can drop to 50MB if preferred.
- No client-side video compression → slow cell-data uploads; existing staged-retry UX covers failures.
- Blob-URL playback downloads the full video before play; Range streaming is future work.

## Verification
1. Backend: `./run_tests.sh tests/test_tasks_api.py tests/test_task_photos_api.py tests/test_task_convert_api.py tests/test_tasks_feature_flag.py` + `./run_mypy.sh` + `./run_ruff.sh`.
2. Portal: scoped `npm test` files + `npm run typecheck` + `npm run lint` + `npm run build`.
3. Manual: create a task picking a teammate as assignee (and once untouched → defaults to creator); attach an `.mp4` and an iPhone `.mov`, play both in the lightbox, delete one; set due dates of today/yesterday/none and confirm amber/red/green pills + age labels; curl a forged `created_at`/`updated_at` and confirm server values win; combine assignee+status+property in the Filter button; move a task across kanban columns and confirm its due date survives; convert a task with a video (keep and delete variants).
