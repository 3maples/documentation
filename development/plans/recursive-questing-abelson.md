# Change Log Feature

## Context

Add a new "Change Log" feature so users can browse product release notes from inside the Maple panel. A new button sits next to the existing Feedback button at the bottom of the Maple panel; clicking it opens an overlay (same pattern as `FeedbackPanel`) that lists release entries from a new MongoDB collection. Each entry has a version, a date, and markdown content. Cards render collapsed by default (preview) with a "Show more" toggle to expand. This is read-only in v1 — entries are seeded directly in the DB.

## Decisions (confirmed with user)

- **Scope:** Global change log (no `company_id`). Single source of release notes shared by all companies.
- **Authoring:** DB-seeded only in v1. No POST endpoint, no admin UI.
- **Markdown:** Add `react-markdown` + `remark-gfm` + `@tailwindcss/typography` (`prose` classes for styled output).
- **Panel behavior:** Mutually exclusive with Feedback panel — opening one closes the other.
- **Sort order:** Newest-first by `date` desc, then `version` desc as tiebreaker.

## Backend

### 1. New model — [platform/models/change_log.py](platform/models/change_log.py)

```python
from beanie import Document
from pydantic import Field
from datetime import date, datetime, timezone


class ChangeLogEntry(Document):
    version: str              # e.g. "0.1.1"
    date: date                # YYYY-MM-DD
    content: str              # markdown body
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "change_log_entries"
        indexes = [
            [("date", -1), ("version", -1)],
            "version",
        ]
```

- Mirror the Beanie pattern in [platform/models/audit_log.py](platform/models/audit_log.py).
- No `company_id` (global).

### 2. Register the model

- [platform/models/__init__.py](platform/models/__init__.py): `from .change_log import ChangeLogEntry`, then `ChangeLogEntry.model_rebuild()`.
- [platform/database.py](platform/database.py): import `ChangeLogEntry` and append to `document_models` list (currently lines 24–48).

### 3. New router — [platform/routers/change_logs.py](platform/routers/change_logs.py)

```python
from datetime import date
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from models import ChangeLogEntry
from firebase_auth import verify_verified_firebase_token

router = APIRouter(prefix="/change-logs", tags=["change-logs"])


class ChangeLogEntryResponse(BaseModel):
    id: str
    version: str
    date: date     # serialized as "YYYY-MM-DD"
    content: str


@router.get("", response_model=List[ChangeLogEntryResponse])
async def list_change_logs(
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    entries = (
        await ChangeLogEntry.find_all()
        .sort([("date", -1), ("version", -1)])
        .to_list()
    )
    return [
        ChangeLogEntryResponse(
            id=str(e.id), version=e.version, date=e.date, content=e.content
        )
        for e in entries
    ]
```

- Pattern mirrors [platform/routers/audit_logs.py](platform/routers/audit_logs.py) and [platform/routers/feedback.py](platform/routers/feedback.py).
- Auth-only (no role gate) — anyone signed in can view release notes.

### 4. Register the router

- [platform/routers/__init__.py](platform/routers/__init__.py): `from .change_logs import router as change_logs_router`.
- [platform/main.py](platform/main.py): import `change_logs_router` (line 28 area) and add `app.include_router(change_logs_router, dependencies=protected_route_dependencies)` next to the feedback router (line 165 area).

### 5. Backend tests — [platform/tests/test_change_logs_api.py](platform/tests/test_change_logs_api.py)

Follow patterns in [platform/tests/test_feedback_api.py](platform/tests/test_feedback_api.py) (TestClient + `X-Test-Email` header). Cases:

1. `test_list_empty` — empty collection returns `[]`.
2. `test_list_sorted_newest_first` — three entries with varying dates → asserted in `date` desc order.
3. `test_list_version_tiebreaker` — same date, different versions → version desc.
4. `test_list_response_shape` — `id`, `version`, `date` (string), `content` only; no `created_at`.
5. `test_list_requires_auth` — missing auth header → 401/403.

Insert via `await ChangeLogEntry(...).insert()` inside the async test, with cleanup in fixture/teardown.

## Frontend

### 6. API client — [portal/src/api/changelog.ts](portal/src/api/changelog.ts)

```ts
import { apiRequest } from "./client";

export type ChangeLogEntry = {
  id: string;
  version: string;
  date: string;    // "YYYY-MM-DD"
  content: string; // markdown
};

export const changeLogApi = {
  list: (): Promise<ChangeLogEntry[]> =>
    apiRequest<ChangeLogEntry[]>("/change-logs", { method: "GET" }),
};
```

- Mirrors [portal/src/api/feedback.ts](portal/src/api/feedback.ts).

### 7. New dependencies

In `portal/`:

```
npm install react-markdown remark-gfm
npm install -D @tailwindcss/typography
```

Add the typography plugin to `portal/tailwind.config.*` (`plugins: [require('@tailwindcss/typography')]`). If Tailwind 4 is in use (the project lists Tailwind CSS 4 in CLAUDE.md), follow the v4 plugin registration syntax — confirm by reading the existing Tailwind config before editing.

### 8. New component — [portal/src/components/common/ChangeLogPanel.tsx](portal/src/components/common/ChangeLogPanel.tsx)

Mirror the structure of [portal/src/components/common/FeedbackPanel.tsx](portal/src/components/common/FeedbackPanel.tsx):

- Container: `<div className="absolute inset-0 bg-white flex flex-col z-10">`
- Header: back button (`ArrowLeft`) + title "Change Log"
- Body: `flex-1 overflow-y-auto p-4 flex flex-col gap-3` containing loading spinner / error / empty state / cards
- Each card (`<article>` with `border border-gray-200 rounded-lg p-3`):
  - Version line: `Change Log: {version}` (`text-sm font-semibold`)
  - Date line: `text-xs text-gray-500`
  - Markdown wrapper: `prose prose-sm max-w-none` with `line-clamp-3` when collapsed
  - "Show more" / "Show less" toggle button
- Per-card expanded state: `useState<Record<string, boolean>>({})`
- Fetch on `open === true` via `useEffect`. Reuse the race-safe pattern from `FeedbackPanel`: `isMountedRef` + `fetchTokenRef` to drop stale responses.
- Errors handled via `ApiError` from `../../types/ApiError`.

Markdown: `<ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.content}</ReactMarkdown>`.

Long expanded content: the parent body is already `overflow-y-auto`, so cards naturally grow and the body scrolls — satisfies "scrollbar appears when content exceeds screen height."

### 9. PortalLayout integration — [portal/src/components/Layout/PortalLayout.tsx](portal/src/components/Layout/PortalLayout.tsx)

- Add state alongside `isFeedbackOpen` (~line 323): `const [isChangeLogOpen, setIsChangeLogOpen] = useState(false);`
- Define mutually exclusive openers:
  ```ts
  const openFeedback  = () => { setIsChangeLogOpen(false); setIsFeedbackOpen(true); };
  const openChangeLog = () => { setIsFeedbackOpen(false); setIsChangeLogOpen(true); };
  ```
  Update existing Feedback button onClicks to use `openFeedback` (replacing the inline `setIsFeedbackOpen(prev => !prev)`).
- Import: `import { ScrollText } from "lucide-react";` and `import ChangeLogPanel from "../common/ChangeLogPanel";`
- In **both** Maple asides (mobile [PortalLayout.tsx:1319-1331](portal/src/components/Layout/PortalLayout.tsx#L1319-L1331) and desktop [PortalLayout.tsx:1406-1418](portal/src/components/Layout/PortalLayout.tsx#L1406-L1418)):
  - Add a "Change Log" button next to the Feedback button (same `mt-3 w-full inline-flex items-center justify-center gap-2 px-3 py-2 ...` classes), with `<ScrollText className="w-4 h-4" />` icon. Wrap both buttons in a `flex gap-2` row so they sit side-by-side, or stack — match whatever layout the user sees as natural; default to a horizontal `flex gap-2` row of two equal-width buttons.
  - Render `<ChangeLogPanel open={isChangeLogOpen} onClose={() => setIsChangeLogOpen(false)} />` next to the existing `<FeedbackPanel ... />`.

### 10. Frontend tests — [portal/tests/ChangeLogPanel.test.tsx](portal/tests/ChangeLogPanel.test.tsx)

Use Vitest + React Testing Library (confirm setup matches existing tests under `portal/tests/`). Mock `../../api/changelog` via `vi.mock`. Cases:

1. Renders nothing when `open={false}`.
2. Shows spinner then renders entries (mocked list of 2).
3. Empty state message when API returns `[]`.
4. Error state message when API rejects with `ApiError`.
5. "Show more" toggles to "Show less" on click.
6. Back button calls `onClose`.

## Verification

### Seed sample data
```
mongosh "mongodb://localhost:27017/<db>"
db.change_log_entries.insertMany([
  {
    version: "0.1.1",
    date: new Date("2026-04-01"),
    content: "## Fixes\n- Fixed bug X\n- Improved Y\n\n## New\n- Added Z feature with extra detail to test the show-more toggle behavior.",
    created_at: new Date()
  },
  {
    version: "0.1.0",
    date: new Date("2026-03-15"),
    content: "Initial release.",
    created_at: new Date()
  }
]);
```

### Run services
- Backend: `cd platform && source .venv/bin/activate && uvicorn main:app --reload`
- Frontend: `cd portal && npm run dev`

### Manual smoke test
1. Sign in to the portal and open the Maple panel (Sparkles icon, top-right header).
2. Confirm a "Change Log" button appears next to "Feedback" at the bottom.
3. Click "Change Log" → spinner briefly → two cards appear, newest (`0.1.1`, `2026-04-01`) on top.
4. Each card shows version + date + ~3 lines of markdown preview.
5. Click "Show more" → card expands to full markdown; "Show less" collapses.
6. Verify body scrolls when expanded content exceeds the panel height.
7. Click the back arrow → returns to the Maple panel.
8. Open Feedback while Change Log is open → Change Log closes (mutual exclusion).

### Test commands
- Backend: `cd platform && ./run_tests.sh tests/test_change_logs_api.py`
- Frontend: `cd portal && npm test -- ChangeLogPanel`

## Critical Files

**New:**
- [platform/models/change_log.py](platform/models/change_log.py)
- [platform/routers/change_logs.py](platform/routers/change_logs.py)
- [platform/tests/test_change_logs_api.py](platform/tests/test_change_logs_api.py)
- [portal/src/api/changelog.ts](portal/src/api/changelog.ts)
- [portal/src/components/common/ChangeLogPanel.tsx](portal/src/components/common/ChangeLogPanel.tsx)
- [portal/tests/ChangeLogPanel.test.tsx](portal/tests/ChangeLogPanel.test.tsx)

**Edited:**
- [platform/models/__init__.py](platform/models/__init__.py)
- [platform/database.py](platform/database.py)
- [platform/routers/__init__.py](platform/routers/__init__.py)
- [platform/main.py](platform/main.py)
- [portal/src/components/Layout/PortalLayout.tsx](portal/src/components/Layout/PortalLayout.tsx)
- [portal/package.json](portal/package.json) (new deps)
- [portal/tailwind.config.*](portal/) (typography plugin)

## Reference Patterns Reused
- Overlay shell, race-safe async, back button — [portal/src/components/common/FeedbackPanel.tsx](portal/src/components/common/FeedbackPanel.tsx)
- Beanie Document + indexes — [platform/models/audit_log.py](platform/models/audit_log.py)
- Auth-protected list endpoint — [platform/routers/audit_logs.py](platform/routers/audit_logs.py)
- Tiny API client wrapper — [portal/src/api/feedback.ts](portal/src/api/feedback.ts)
- Backend test fixtures + `X-Test-Email` — [platform/tests/test_feedback_api.py](platform/tests/test_feedback_api.py)
