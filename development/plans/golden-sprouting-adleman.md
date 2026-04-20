# Customer Feedback & Support — Implementation Plan

## Context

The app currently has no in-product channel for users to report issues, request features, or share general feedback. We want to capture this feedback directly from the Maple Panel (the AI chat sidebar) and pipe it into the team's Trello board so issues, feature requests, and general feedback land in the right backlog list automatically. The user experience should feel lightweight: a single button at the bottom of the Maple Panel reveals an in-panel form, the user picks a category and types a message, hits submit, and sees a thank-you confirmation. No data is persisted in MongoDB — Trello is the source of truth.

## Approach Summary

- **Frontend:** Add a Feedback button to the Maple Panel composer area. Clicking it toggles an in-panel overlay (absolute-positioned within the Maple `<aside>`) that covers the messages + composer area but leaves the panel header visible. The overlay contains a back arrow, a category dropdown, a message textarea, and a submit button. On success, the overlay swaps to a "Thank you" state.
- **Backend:** New `POST /feedback` endpoint that accepts `{category, message}`, looks up the current user's name/email from the Firebase token + Users collection, and creates a Trello card via `httpx` in the list mapped to the chosen category. No DB writes.

## Frontend Changes

### 1. New component: [portal/src/components/common/FeedbackPanel.tsx](portal/src/components/common/FeedbackPanel.tsx)

A self-contained in-panel overlay component. Props:
```ts
type FeedbackPanelProps = {
  open: boolean;
  onClose: () => void;
};
```

Internal state:
- `category: "general_feedback" | "report_issue" | "feature_request"` (default `"general_feedback"`)
- `message: string`
- `isSubmitting: boolean`
- `submitted: boolean` (controls thank-you view)
- `error: string | null`

Layout (rendered only when `open`):
- Outer container: `absolute inset-0 bg-white flex flex-col` so it covers the messages + composer area within the Maple `<aside>` (the parent must be `relative`).
- Header row inside the overlay: back arrow button (`ArrowLeft` from lucide-react) + title "Send Feedback". Clicking the back arrow calls `onClose`.
- Body: form with
  - Category `<select>` styled to match existing inputs: `px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500`. Three options: General Feedback, Report Issue, Feature Request.
  - Message `<textarea>` (rows={6}) using the same class set as the Maple composer textarea ([PortalLayout.tsx:1034](portal/src/components/Layout/PortalLayout.tsx#L1034)).
  - Submit button styled like the existing "Clear" button in the Maple header ([PortalLayout.tsx:1380](portal/src/components/Layout/PortalLayout.tsx#L1380)), but full-width and primary. Disabled while `!message.trim() || isSubmitting`.
  - Inline error text below the form when `error` is set.
- Thank-you state (when `submitted === true`): replaces the form with a centered "Thanks for your feedback!" message and a "Send another" button that resets state.

On submit: call `submitFeedback({ category, message })` from the new API wrapper. On success → set `submitted = true`. On failure → set `error`.

When `onClose` is called, reset `submitted`, `message`, and `error` so the next open starts fresh.

### 2. New API wrapper: [portal/src/api/feedback.ts](portal/src/api/feedback.ts)

Mirrors the pattern from existing API modules using `apiRequest` from [portal/src/api/client.ts](portal/src/api/client.ts):

```ts
import { apiRequest } from "./client";

export type FeedbackCategory = "general_feedback" | "report_issue" | "feature_request";

export type SubmitFeedbackPayload = {
  category: FeedbackCategory;
  message: string;
};

export const submitFeedback = async (payload: SubmitFeedbackPayload): Promise<void> => {
  await apiRequest("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};
```

### 3. Wire into Maple Panel: [portal/src/components/Layout/PortalLayout.tsx](portal/src/components/Layout/PortalLayout.tsx)

- Import `FeedbackPanel` and a `MessageSquare` icon from `lucide-react`.
- Add state near the other AI panel state (around [line 320](portal/src/components/Layout/PortalLayout.tsx#L320)):
  ```ts
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  ```
- In the desktop Maple `<aside>` ([lines 1372-1390](portal/src/components/Layout/PortalLayout.tsx#L1372-L1390)):
  - Add `relative` to the `<aside>` className so the overlay can position against it.
  - Wrap the `flex-1` messages container + composer container in a `relative flex-1 flex flex-col min-h-0` div, OR position the `FeedbackPanel` `absolute inset-0` at the bottom of the panel above the composer area (covering messages + composer but leaving the header). Render `<FeedbackPanel open={isFeedbackOpen} onClose={() => setIsFeedbackOpen(false)} />` as the last child of the `<aside>`.
  - In the composer area ([lines 1386-1388](portal/src/components/Layout/PortalLayout.tsx#L1386-L1388)), add a Feedback button below `renderAiComposer()`:
    ```tsx
    <button
      type="button"
      onClick={() => setIsFeedbackOpen((prev) => !prev)}
      className="mt-3 w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
    >
      <MessageSquare className="w-4 h-4" />
      Feedback
    </button>
    ```
  - Toggling the button while the overlay is open closes it (the `setIsFeedbackOpen((prev) => !prev)` already handles this), satisfying "click Feedback button again to close it".
- Apply the same wiring inside the mobile Maple drawer ([lines 1283-1316](portal/src/components/Layout/PortalLayout.tsx#L1283-L1316)) for parity.

## Backend Changes

### 1. Config: [platform/config.py](platform/config.py)

Add Trello fields to the `Settings` class (placeholders, no values in repo):
```python
trello_api_key: str | None = None
trello_api_token: str | None = None
trello_general_feedback_list_id: str | None = None
trello_report_issue_list_id: str | None = None
trello_feature_request_list_id: str | None = None
```

**Environment variables to add to `platform/.env.local`:**

```bash
TRELLO_API_KEY=...
TRELLO_API_TOKEN=...
TRELLO_GENERAL_FEEDBACK_LIST_ID=...
TRELLO_REPORT_ISSUE_LIST_ID=...
TRELLO_FEATURE_REQUEST_LIST_ID=...
```

Pydantic Settings reads env vars case-insensitively, so the lowercase field names on `Settings` bind to the uppercase env vars automatically.

#### How to obtain each value (current Trello flow, 2026)

Trello no longer has a standalone "app key" page — you must create a Power-Up to get credentials. This is a one-time setup.

**1. `TRELLO_API_KEY`**
1. Log into Trello as the account that owns the feedback board.
2. Go to https://trello.com/power-ups/admin
3. Click **New** and create a Power-Up (e.g. name it "3Maples Feedback Intake"). You can leave the iframe URL blank — we only need it as a credential container, not a real Power-Up.
4. Open the Power-Up → **API Key** tab → click **Generate a new API Key**.
5. Copy the key shown — this is `TRELLO_API_KEY`.

**2. `TRELLO_API_TOKEN`**
1. On the same **API Key** tab, to the right of the generated API key there is a small text link that reads **"Token"** (it says something like *"you can manually generate a Token"*). Click it.
2. You'll be taken to an authorization page asking to allow the Power-Up to access your Trello account. Click the green **Allow** button.
3. You'll be redirected to a page that displays your token as a long string. Copy it — this is `TRELLO_API_TOKEN`.
4. Treat this token as a secret — it has full write access to your Trello account.

**3. The three list IDs** (`TRELLO_GENERAL_FEEDBACK_LIST_ID`, `TRELLO_REPORT_ISSUE_LIST_ID`, `TRELLO_FEATURE_REQUEST_LIST_ID`)

The Trello UI does not surface list IDs anywhere, so fetch them via the API once you have the key + token:

1. In Trello, open the board that will receive feedback. Make sure it has three lists named (or whatever you prefer): "General Feedback", "Report Issue", "Feature Request".
2. Find the **board ID**: in the browser URL bar, append `.json` to the board URL, e.g. `https://trello.com/b/AbCdEfGh/my-board.json`. The top-level `id` field in the JSON response is the board ID. (Or use the short ID `AbCdEfGh` from the URL — Trello accepts both.)
3. Run this curl from your terminal, substituting your key, token, and board ID:
   ```bash
   curl "https://api.trello.com/1/boards/<BOARD_ID>/lists?key=<TRELLO_API_KEY>&token=<TRELLO_API_TOKEN>"
   ```
4. The response is a JSON array of lists, each with `id` and `name`. Copy the `id` of each list into the matching env var.

> If running curl is inconvenient, paste the same URL into a browser tab while logged into Trello — the JSON renders directly.

### 2. New service: [platform/services/trello_service.py](platform/services/trello_service.py)

Follow the pattern of [platform/services/brevo_email.py](platform/services/brevo_email.py):

```python
import httpx
from config import settings

TRELLO_BASE_URL = "https://api.trello.com/1"

CATEGORY_TO_LIST_ID = {
    "general_feedback": lambda: settings.trello_general_feedback_list_id,
    "report_issue": lambda: settings.trello_feature_request_list_id,  # use correct setting
    "feature_request": lambda: settings.trello_feature_request_list_id,
}

def _require_trello_config() -> None:
    if not settings.trello_api_key or not settings.trello_api_token:
        raise RuntimeError("Trello API credentials are not configured")

async def create_trello_card(*, list_id: str, name: str, desc: str) -> dict:
    _require_trello_config()
    params = {
        "key": settings.trello_api_key,
        "token": settings.trello_api_token,
        "idList": list_id,
        "name": name,
        "desc": desc,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(f"{TRELLO_BASE_URL}/cards", params=params)
    if not response.is_success:
        raise RuntimeError(f"Trello card creation failed ({response.status_code}): {response.text}")
    return response.json()
```

(Use a real dict mapping each category to its own setting attribute — the lambda above is illustrative.)

### 3. New router: [platform/routers/feedback.py](platform/routers/feedback.py)

Follow the pattern of [platform/routers/users.py](platform/routers/users.py).

```python
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from config import settings
from firebase_auth import verify_verified_firebase_token
from models.user import User  # confirm exact import path
from services.trello_service import create_trello_card

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackCategory(str, Enum):
    GENERAL_FEEDBACK = "general_feedback"
    REPORT_ISSUE = "report_issue"
    FEATURE_REQUEST = "feature_request"

CATEGORY_LABELS = {
    FeedbackCategory.GENERAL_FEEDBACK: "General Feedback",
    FeedbackCategory.REPORT_ISSUE: "Report Issue",
    FeedbackCategory.FEATURE_REQUEST: "Feature Request",
}

def _list_id_for(category: FeedbackCategory) -> str:
    mapping = {
        FeedbackCategory.GENERAL_FEEDBACK: settings.trello_general_feedback_list_id,
        FeedbackCategory.REPORT_ISSUE: settings.trello_report_issue_list_id,
        FeedbackCategory.FEATURE_REQUEST: settings.trello_feature_request_list_id,
    }
    list_id = mapping[category]
    if not list_id:
        raise HTTPException(status_code=500, detail="Trello list is not configured for this category")
    return list_id

class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: FeedbackCategory
    message: str = Field(min_length=1, max_length=5000)

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackRequest,
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    firebase_uid = decoded_token.get("uid")
    token_email = decoded_token.get("email") or ""

    user = await User.find_one(User.firebase_uid == firebase_uid)  # confirm field name
    full_name = (
        f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
        if user else ""
    ) or "Unknown User"
    email = (user.email if user and user.email else token_email) or "unknown"

    label = CATEGORY_LABELS[payload.category]
    card_name = f"[{label}] {full_name}"
    card_desc = (
        f"**From:** {full_name} <{email}>\n"
        f"**Category:** {label}\n\n"
        f"---\n\n"
        f"{payload.message}"
    )

    try:
        await create_trello_card(
            list_id=_list_id_for(payload.category),
            name=card_name,
            desc=card_desc,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to submit feedback: {exc}") from exc

    return {"status": "ok"}
```

> Verify the exact `User` model import path and field names (`firebase_uid`, `first_name`, `last_name`, `email`) when implementing — match what's in [platform/models/](platform/models/).

### 4. Register the router

- Export `feedback_router` from [platform/routers/__init__.py](platform/routers/__init__.py).
- Import and `app.include_router(feedback_router, dependencies=protected_route_dependencies)` in [platform/main.py](platform/main.py) alongside existing routers.

### 5. Tests: [platform/tests/test_feedback_api.py](platform/tests/test_feedback_api.py)

Following the pattern of [platform/tests/test_agents_api.py](platform/tests/test_agents_api.py):

- Fixture that monkeypatches `routers.feedback.create_trello_card` with an `AsyncMock` so no real HTTP call is made.
- `test_submit_feedback_success`: POST `/feedback` with valid payload → 201, mock called once with the right `list_id` (assert mapping for each of the 3 categories), and card name/desc include the user's name/email.
- `test_submit_feedback_invalid_category`: POST with bad category → 422.
- `test_submit_feedback_empty_message`: POST with empty message → 422.
- `test_submit_feedback_trello_failure`: mock raises `RuntimeError` → 502.
- `test_submit_feedback_missing_list_id`: monkeypatch settings to clear one list ID → 500 for that category.

## Files to Modify / Create

**Frontend**
- Create: [portal/src/components/common/FeedbackPanel.tsx](portal/src/components/common/FeedbackPanel.tsx)
- Create: [portal/src/api/feedback.ts](portal/src/api/feedback.ts)
- Modify: [portal/src/components/Layout/PortalLayout.tsx](portal/src/components/Layout/PortalLayout.tsx) (state, button, render `FeedbackPanel`, both desktop + mobile Maple panels)

**Backend**
- Modify: [platform/config.py](platform/config.py) (Trello settings)
- Create: [platform/services/trello_service.py](platform/services/trello_service.py)
- Create: [platform/routers/feedback.py](platform/routers/feedback.py)
- Modify: [platform/routers/__init__.py](platform/routers/__init__.py) (export)
- Modify: [platform/main.py](platform/main.py) (include router)
- Create: [platform/tests/test_feedback_api.py](platform/tests/test_feedback_api.py)

## Verification

1. **Backend unit tests (related only):**
   ```bash
   cd platform && ./run_tests.sh tests/test_feedback_api.py
   ```
   All cases pass; Trello service is fully mocked.

2. **Backend manual smoke test:**
   - Set the 5 Trello env vars in `platform/.env.local` to real values from a test Trello board.
   - `uvicorn main:app --reload`
   - With a valid Firebase token, POST `/feedback` with each of the 3 categories and verify that real cards appear in the corresponding Trello lists, with name/email in the description.

3. **Frontend manual flow:**
   - `cd portal && npm run dev`
   - Open the Maple Panel → confirm Feedback button shows below the composer.
   - Click it → in-panel overlay appears, header still shows "Maple", chat is hidden.
   - Click the back arrow → overlay closes; click Feedback again to verify toggle behavior.
   - Pick each category, type a message, submit → "Thank you" view appears.
   - Submit with empty message → button disabled.
   - Force a backend error → inline error shows; overlay stays open.
   - Verify mobile Maple drawer behaves the same.
