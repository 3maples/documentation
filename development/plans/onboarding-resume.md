# Onboarding Resume — Design Spec

**Date:** 2026-06-19
**Status:** Approved design — ready for implementation planning

## Problem

A new signup whose onboarding is interrupted (e.g. they quit at the Materials
step) is **dropped straight into the main app with a half-set-up company** on
their next login, and has **no way back into the onboarding flow** to finish.

Root cause: onboarding progress lives **only in browser localStorage**
(`portal.onboardingStep`, `portal.onboardingInProgress`). There is no
server-side record of onboarding state. The only login gate is whether
`user.company` exists — and the company is created at **Step 1**, so by the time
the user reaches any later step the gate already says "go to dashboard." The
localStorage step counter is ignored on re-login (and lost on a different device
or cleared browser).

### Current flow (verified)

- Onboarding has 8 UI steps (0 Welcome, 1 Company, 2 Contacts, 3 Properties,
  4 Materials, 5 People, 6 Plan, 7 Completion) —
  [OnboardingPage.tsx](../../../portal/src/pages/OnboardingPage.tsx).
- Company is created at Step 1 via `POST /auth/company-onboarding` →
  `create_company_with_bootstrap` (sets `user.company`, bootstraps categories /
  units / divisions / rate cards).
- `_serialize_user` returns `company_id`
  ([routers/auth.py](../../../platform/routers/auth.py)).
- Routing is driven by `onIdTokenChanged` in
  [App.tsx](../../../portal/src/App.tsx): `company_id` present → set session →
  dashboard; absent → onboarding.
- Latent bug: [LoginPage.tsx:167](../../../portal/src/pages/auth/LoginPage.tsx)
  checks `authData?.company` (always `undefined` — the API returns
  `company_id`). The check is dead code, masked by the `App.tsx` listener which
  is the real router. Will be corrected as part of this work.

## Goals

- A returning user with incomplete onboarding **resumes at the exact step they
  left**.
- Onboarding is **mandatory until finished** — every login re-routes an
  incomplete user back into the flow until they complete it.
- Resume works **across devices / cleared browser storage** (server is the
  source of truth).
- **No migration** for existing companies — they must never be dragged back into
  onboarding.

## Non-goals

- Resuming a quit at Step 0 (Welcome) or Step 1 (Company) **before the company
  is created** — there is nothing to persist server-side. The existing
  `company_id == null` gate already restarts these users at Welcome. Inherent
  limitation, accepted.
- "Smart-skip" of already-populated steps. We resume at the **saved** step, not
  a step computed from data presence.
- An escape hatch to skip onboarding into the app. Onboarding is mandatory until
  finished.

## Design

### 1. Source of truth: the `Company` model

Onboarding state lives on `Company` (not `User`): the company is created at
Step 1 and is the entity being set up, and all resumable steps happen after it
exists.

New fields on `Company` ([models/company.py](../../../platform/models/company.py)):

```python
class OnboardingStep(str, Enum):
    CONTACTS = "contacts"      # UI step 2
    PROPERTIES = "properties"  # UI step 3
    MATERIALS = "materials"    # UI step 4
    PEOPLE = "people"          # UI step 5
    PLAN = "plan"              # UI step 6

# on Company:
onboarding_completed: bool = True
onboarding_step: OnboardingStep = OnboardingStep.CONTACTS
```

**Semantic enum, not the raw UI integer** — reordering UI steps later must not
silently corrupt stored progress. The frontend owns the enum ↔ UI-index map.

**`default = True` is the backfill.** Existing companies lack these fields, so
Beanie loads them as `completed=True` and they are never routed into onboarding.
Only the onboarding endpoint explicitly sets `completed=False`. No migration
script.

Pre-company steps (0 Welcome, 1 Company) are intentionally **not** represented
in the enum — there is no company to store them on. Server-side step tracking
begins at `CONTACTS`, the first post-company step.

### 2. Backend changes

- **`complete_company_onboarding`** (Step 1, company creation): after
  `create_company_with_bootstrap`, set `onboarding_completed = False` and
  `onboarding_step = OnboardingStep.CONTACTS`, then save. (Set in the endpoint,
  keeping `create_company_with_bootstrap` generic.)
- **New `PATCH /auth/onboarding-progress`**: body accepts `{step}` (advance the
  saved step) and/or `{completed: true}` (mark finished). Resolves user →
  company via the verified Firebase token (same pattern as
  `company-onboarding`), validates the enum value, updates and saves. Returns
  the serialized user. Unknown step → 400. Missing/unauthorized user → 401.
- **`_serialize_user`**: add `onboarding_completed` and `onboarding_step` to the
  `/auth` response.

All new datetimes (if any) follow the aware-UTC convention already in the file.

### 3. Frontend routing — reuse existing guards

The existing guards already route correctly when **both** the authenticated
session and the `onboardingInProgress` localStorage flag are set:
`ProtectedLayout` bounces to `/onboarding`; `OnboardingRoute` renders the page
(because `hasAuthenticatedSession() && !isOnboardingInProgress()` is false).

Only the two auth entry points change —
[App.tsx](../../../portal/src/App.tsx) `onIdTokenChanged` and
[LoginPage.tsx](../../../portal/src/pages/auth/LoginPage.tsx):

> When `company_id` is present **but `onboarding_completed === false`**: call
> `setOnboardingInProgress()`, write the mapped UI step into the
> `portal.onboardingStep` localStorage key, set company id + current user, then
> proceed as authenticated. The guards carry the user to `/onboarding`, and
> `OnboardingPage`'s existing localStorage-step read drops them at the exact
> step.

This satisfies "force resume until finished" automatically — every login
re-derives the in-progress flag from the server flag. The dead
`authData?.company` check in `LoginPage` is corrected to `company_id` in the
same edit.

Enum ↔ UI-index map (frontend helper):

| `onboarding_step` | UI step index |
|---|---|
| `contacts`   | 2 |
| `properties` | 3 |
| `materials`  | 4 |
| `people`     | 5 |
| `plan`       | 6 |

`onboarding_completed === true` → dashboard (no onboarding seeding).

### 4. Onboarding page wiring

[OnboardingPage.tsx](../../../portal/src/pages/OnboardingPage.tsx):

- `goToStep` (for steps ≥ 2) also calls `PATCH /auth/onboarding-progress` with
  the mapped enum to persist the server step. localStorage remains the fast
  local mirror.
- `handleFinish` calls `PATCH /auth/onboarding-progress` with
  `{completed: true}` **before** clearing local flags and redirecting.
- On resume, `pendingAuthData` is null (it is only set during the live
  company-creation flow). Hydrate `currentUser` from the `/auth` data already
  fetched at login so `handleFinish` still records the user correctly.

### 5. Error handling

- Progress PATCH failures are **non-fatal to navigation**: the local step still
  advances and the server reconciles on the next successful call. Failures are
  logged, never block a user mid-flow.
- The PATCH validates company ownership via the Firebase token and rejects
  unknown step values with 400.

## Testing (TDD — write tests first)

### Backend (`platform/tests/`)

- `onboarding_completed` defaults to `True` for a bare `Company()`.
- `complete_company_onboarding` sets `onboarding_completed=False` and
  `onboarding_step=CONTACTS`.
- `_serialize_user` / `POST /auth` response includes both new fields.
- `PATCH /auth/onboarding-progress`:
  - advances the saved step;
  - marks `completed=true`;
  - rejects an unknown step value (400);
  - enforces ownership / rejects unauthenticated (401).

### Frontend (`portal/tests/`)

- Re-login with `onboarding_completed=false` seeds the in-progress flag + mapped
  step and routes to `/onboarding` at the correct step.
- `onboarding_completed=true` routes to dashboard (no seeding).
- `goToStep` (step ≥ 2) and `handleFinish` call `PATCH /auth/onboarding-progress`
  with the expected payloads.

## Gates

- Backend: `./run_mypy.sh` + `./run_ruff.sh` scoped to touched subtrees; related
  `./run_tests.sh tests/<...>` pass. Full ruff/mypy run by the pre-push hook.
- Frontend: `npm test -- <relevant>` pass; `npm run build` clean.

## Files touched (anticipated)

- `platform/models/company.py` — `OnboardingStep` enum + two fields.
- `platform/routers/auth.py` — serializer fields, company-onboarding default
  set, new `PATCH /auth/onboarding-progress` endpoint.
- `portal/src/types/api.ts` — `AuthUser` gains `onboarding_completed` /
  `onboarding_step`.
- `portal/src/api/auth.ts` — `updateOnboardingProgress` client fn.
- `portal/src/App.tsx` + `portal/src/pages/auth/LoginPage.tsx` — resume branch +
  `company_id` fix.
- `portal/src/pages/OnboardingPage.tsx` — persist step on advance, mark complete
  on finish, hydrate user on resume.
- Backend + frontend tests as above.
