# Featurebase Feedback Widget Integration

## Context

We need an in-app channel for users to send feedback and feature requests directly to us. Today the portal has no help/support UI at all — users have no way to reach us from inside the app. Featurebase is a hosted feedback/roadmap tool whose JS SDK lets us drop in a feedback widget that posts directly to our Featurebase workspace, with the logged-in user pre-identified so we know who said what.

**Two design constraints driven by user requirements:**
1. **Auth-gated:** Only signed-in portal users may submit feedback, and submissions must be cryptographically tied to their real identity (no email spoofing). This rules out the simpler "pass an `email` string to the widget" pattern, because the widget runs in the browser and a hostile user could swap any email in. Featurebase's documented solution is to sign a JWT on our backend with a shared secret and pass it as `featurebaseJwt` to the widget; their server verifies the signature before accepting the submission. We will additionally mark the Featurebase workspace as **private** in their dashboard so any non-JWT visitor is bounced to a login page rather than allowed to post anonymously.
2. **Two-way conversation:** Confirmed supported. Admin replies on a feedback item email the original submitter; users can reply back inside the widget; status changes (in-progress, completed) auto-notify upvoters. So once a user submits, we have a real round-trip channel with no extra work on our side beyond responding inside the Featurebase admin UI.

## Approach

### Backend: JWT signing endpoint

1. **Add the secret to settings.** In [platform/config.py](platform/config.py) `Settings`, add `featurebase_jwt_secret: str | None = None` (mirrors the optional-key pattern used by `brevo_api_key`). Document it in the platform `.env.example` if one exists.

2. **Add `pyjwt` to [platform/requirements.txt](platform/requirements.txt).** It is not currently a dependency. Use `PyJWT>=2.8`.

3. **New router [platform/routers/featurebase.py](platform/routers/featurebase.py).**
   - `GET /featurebase/widget-token`
   - Depends on `verify_verified_firebase_token` (the same dep used by [routers/users.py:84](platform/routers/users.py#L84)) — this is what guarantees only authenticated portal users can mint a token.
   - Loads the matching `User` document (same lookup pattern as [routers/auth.py:238-246](platform/routers/auth.py#L238-L246)).
   - Builds the JWT payload per Featurebase spec:
     ```python
     {
       "email": user.email,                # required
       "name": f"{user.first_name} {user.last_name}".strip() or user.email,
       "userId": str(user.id),             # our internal id
       "iat": int(time.time()),
       "exp": int(time.time()) + 60 * 60,  # 1 hour
     }
     ```
   - Signs with `jwt.encode(payload, settings.featurebase_jwt_secret, algorithm="HS256")`.
   - Returns `{"token": "<jwt>"}`.
   - Returns `503` if `featurebase_jwt_secret` is unset (clean degradation in dev).

4. **Wire it up in [platform/main.py](platform/main.py)** alongside the other protected routers (~lines 149-165), using `protected_route_dependencies` so Firebase + App Check are enforced.

5. **Backend tests [platform/tests/test_featurebase_api.py](platform/tests/test_featurebase_api.py):**
   - Authenticated request returns a token; decode it with the test secret and assert the payload's `email`, `userId`, and `exp`.
   - Unauthenticated request returns `401` (handled by the global dep).
   - Missing `featurebase_jwt_secret` returns `503`.
   - Use `monkeypatch.setattr(settings, "featurebase_jwt_secret", "test-secret")` per test.

### Frontend: SDK loader, widget init, header button

6. **New helper [portal/src/lib/featurebase.ts](portal/src/lib/featurebase.ts):**
   - `loadFeaturebaseSdk()` — idempotent injection of `https://do.featurebase.app/js/sdk.js` plus the queued-call shim from Featurebase's snippet
   - `initFeaturebaseFeedbackWidget({ organization, jwt })` — calls `window.Featurebase("initialize_feedback_widget", { organization, theme: "light", locale: "en", featurebaseJwt: jwt })`. **Omits `placement`** so Featurebase does not render its own floating bubble — our header button is the only entry point.
   - `openFeaturebaseFeedbackWidget()` — `window.postMessage({ target: "FeaturebaseWidget", data: { action: "openFeedbackWidget" } }, "*")`
   - `fetchFeaturebaseToken()` — calls our new `/featurebase/widget-token` endpoint via the existing [api/client](portal/src/api/client.ts) (so the auth interceptor adds the Firebase token automatically)
   - Minimal `Window.Featurebase` type augmentation

7. **Bootstrap in [portal/src/main.tsx](portal/src/main.tsx).** After the existing Sentry block ([main.tsx:10-27](portal/src/main.tsx#L10-L27)), if `import.meta.env.VITE_FEATUREBASE_ORG` is set, call `loadFeaturebaseSdk()`. The SDK script is harmless to load before login; it does nothing until we call `initialize_feedback_widget`.

8. **Initialize per-user inside [portal/src/components/Layout/PortalLayout.tsx](portal/src/components/Layout/PortalLayout.tsx).**
   - PortalLayout already wraps every authenticated route and already reads `getCurrentUser()` at [PortalLayout.tsx:422-423](portal/src/components/Layout/PortalLayout.tsx#L422-L423).
   - Add a `useEffect` that, when a current user is present and `VITE_FEATUREBASE_ORG` is set, fetches a fresh JWT via `fetchFeaturebaseToken()` and calls `initFeaturebaseFeedbackWidget(...)`. Re-run when the user changes (logout → login).
   - Catch + swallow fetch errors (logged to Sentry) so a transient backend hiccup never breaks the portal shell. The button can simply be disabled until a token is obtained.

9. **Header Feedback button.** In [PortalLayout.tsx:1349-1361](portal/src/components/Layout/PortalLayout.tsx#L1349-L1361), add a new `<button>` immediately to the left of the existing Sparkles/Maple toggle. Use `MessageSquare` from `lucide-react` (already used elsewhere). Match the existing button's color tokens. `onClick` calls `openFeaturebaseFeedbackWidget()`. Hide the button (or disable it) when `VITE_FEATUREBASE_ORG` is unset OR a token has not yet been minted, so dev builds don't show a dead control.

10. **Type & env plumbing.**
    - Add `VITE_FEATUREBASE_ORG: string` to `ImportMetaEnv` in [portal/src/vite-env.d.ts](portal/src/vite-env.d.ts).
    - Add `VITE_FEATUREBASE_ORG=` to [portal/.env.example](portal/.env.example) with a comment pointing at the workspace subdomain.

11. **Frontend tests [portal/tests/featurebase.test.ts](portal/tests/featurebase.test.ts)** (Vitest, mirroring [tests/companyLogo.test.ts](portal/tests/companyLogo.test.ts)):
    - `loadFeaturebaseSdk()` injects exactly one `<script id="featurebase-sdk">` even when called twice.
    - `loadFeaturebaseSdk()` installs the queued-call shim (`window.Featurebase` becomes a function and pushes to `Featurebase.q`).
    - `initFeaturebaseFeedbackWidget(...)` calls `window.Featurebase` with `("initialize_feedback_widget", { organization, theme: "light", featurebaseJwt: "<token>", ... })` and never passes `placement`.
    - `openFeaturebaseFeedbackWidget()` calls `window.postMessage` with the documented payload.
    - Reset DOM + `window.Featurebase` between tests.

## Reused existing utilities

- `getCurrentUser()` — [portal/src/api/auth.ts:131](portal/src/api/auth.ts#L131)
- `AuthUser` type — [portal/src/types/api.ts](portal/src/types/api.ts)
- API client + auth interceptor — [portal/src/api/client.ts](portal/src/api/client.ts) and [portal/src/main.tsx:29](portal/src/main.tsx#L29)
- `lucide-react` icons — already throughout PortalLayout
- Backend `verify_verified_firebase_token` dep — used in [routers/users.py:84](platform/routers/users.py#L84)
- Backend `Settings` env-var pattern — [platform/config.py](platform/config.py)
- Backend test fixture & `X-Test-Email` header — [platform/tests/conftest.py](platform/tests/conftest.py), [tests/test_user_api.py:79](platform/tests/test_user_api.py#L79)
- Vitest pattern — [portal/tests/companyLogo.test.ts](portal/tests/companyLogo.test.ts)

## Files to modify / create

**Backend**
| File | Change |
|------|--------|
| [platform/config.py](platform/config.py) | Add `featurebase_jwt_secret: str \| None = None` |
| [platform/requirements.txt](platform/requirements.txt) | Add `PyJWT>=2.8` |
| [platform/routers/featurebase.py](platform/routers/featurebase.py) | **New.** `GET /featurebase/widget-token` |
| [platform/routers/__init__.py](platform/routers/__init__.py) | Export the new router |
| [platform/main.py](platform/main.py) | `app.include_router(featurebase_router, dependencies=protected_route_dependencies)` |
| [platform/tests/test_featurebase_api.py](platform/tests/test_featurebase_api.py) | **New.** Auth + 503 + payload tests |

**Frontend**
| File | Change |
|------|--------|
| [portal/src/lib/featurebase.ts](portal/src/lib/featurebase.ts) | **New.** Loader, init, open, token-fetch helpers |
| [portal/src/main.tsx](portal/src/main.tsx) | Call `loadFeaturebaseSdk()` after Sentry block when env set |
| [portal/src/components/Layout/PortalLayout.tsx](portal/src/components/Layout/PortalLayout.tsx) | `useEffect` to fetch token + init; new header Feedback button |
| [portal/src/vite-env.d.ts](portal/src/vite-env.d.ts) | Add `VITE_FEATUREBASE_ORG` to `ImportMetaEnv` |
| [portal/.env.example](portal/.env.example) | Document `VITE_FEATUREBASE_ORG` |
| [portal/tests/featurebase.test.ts](portal/tests/featurebase.test.ts) | **New.** Helper unit tests |

## One-time Featurebase dashboard config (manual, not code)

- Mark the workspace **private** so non-authenticated visitors are bounced — defense in depth on top of JWT.
- Generate the JWT signing secret at *Settings → Security → Get JWT Secret* and put it in `platform/.env.local` and the production secret store as `FEATUREBASE_JWT_SECRET`.
- Note the workspace subdomain → goes into `VITE_FEATUREBASE_ORG`.

## Verification

1. **Backend tests:** `cd platform && ./run_tests.sh tests/test_featurebase_api.py`
2. **Frontend tests:** `cd portal && npm test -- featurebase`
3. **Local end-to-end:**
   - Set `FEATUREBASE_JWT_SECRET` in `platform/.env.local`, `VITE_FEATUREBASE_ORG` in `portal/.env.local`
   - Run backend (`uvicorn main:app --reload`) and portal (`npm run dev`)
   - Log in, click the new Feedback icon, confirm the modal opens with the user's identity already filled in (no email field shown to fill in)
   - Submit a test item; confirm in the Featurebase admin UI it is tagged to the correct user with our internal `userId` in metadata
4. **Two-way smoke:** Reply to the test item from the Featurebase admin UI; confirm the user receives an email and that opening the widget again shows the reply in their thread.
5. **Spoofing check:** In DevTools, manually call `window.Featurebase("initialize_feedback_widget", { organization: "<our-org>", theme: "light" })` (no JWT) and try to submit. With the workspace marked private, Featurebase should refuse the submission.
6. **No-op safety:** Unset `VITE_FEATUREBASE_ORG`, restart `npm run dev`, confirm the Feedback button is hidden and `do.featurebase.app/js/sdk.js` is **not** loaded (Network tab).
7. **Backend degradation:** With `FEATUREBASE_JWT_SECRET` unset, hit `/featurebase/widget-token` while authenticated and confirm `503`.

## Out of scope (deferred)

- **In-app unread badge on the Feedback button.** Featurebase's native unread-badge mechanism (`fb-update-badge` span + `unreadCount` callback) is documented for the **changelog** widget only — the feedback widget exposes no equivalent event for new admin replies. Users will instead be notified of replies via the email Featurebase sends automatically when an admin comments. Building a custom badge would require a backend Featurebase API integration, per-user last-seen state, and polling — explicitly deferred.
- Changelog widget, survey widget, embedded help center
- Routing feedback into Linear/Slack (configured inside Featurebase, not in our app)
- A custom in-app inbox showing the user their own threads — they will get email notifications for replies, and can reopen the widget to see replies inline

Sources:
- [Feedback widget installation — Featurebase](https://help.featurebase.app/articles/1261560-feedback-widget-installation)
- [Secure your installation (required by default) — Featurebase](https://help.featurebase.app/articles/5402549-secure-your-installation-required-by-default)
- [Creating and signing a JWT — Featurebase](https://help.featurebase.app/articles/5257986-creating-and-signing-a-jwt)
- [Support your customers (two-way conversations) — Featurebase](https://help.featurebase.app/articles/6884621-support-your-customers)
