# Sentry Integration Plan — Frontend & Backend

## Context

There is currently no error tracking or monitoring in the app. When errors occur in production, they go unnoticed unless a user reports them. This plan integrates Sentry for error tracking only (no performance/replay) in production, with authenticated user context (Firebase UID + email) attached to events.

---

## Step 0: Sentry Account Setup (Manual)

You need to do this before I start coding:

1. Create a Sentry account at **sentry.io**
2. Create an organization (e.g., "3Maples")
3. Create **2 projects**:
   - `3maples-platform` — platform type: **Python (FastAPI)** → gives you a backend DSN
   - `3maples-portal` — platform type: **React** → gives you a frontend DSN
4. Copy both DSN strings — you'll add them to env vars
5. Optionally disable Performance and Session Replay in project settings to avoid accidental quota usage

---

## Step 1: Backend — Install dependency

**File:** [requirements.txt](platform/requirements.txt)

Add `sentry-sdk[fastapi]` — the `[fastapi]` extra auto-registers the ASGI middleware for error capture.

---

## Step 2: Backend — Add config fields

**File:** [config.py](platform/config.py) (after line 47, audit logging block)

Add two new settings:
```python
sentry_dsn: str | None = None
sentry_environment: str = "development"
```

When `sentry_dsn` is `None` (default in dev), Sentry won't initialize. Production sets `SENTRY_DSN` and `SENTRY_ENVIRONMENT=production`.

---

## Step 3: Backend — Initialize Sentry in app startup

**File:** [main.py](platform/main.py)

- Add `import sentry_sdk` at top
- Add `_init_sentry()` helper that gates on `settings.sentry_dsn` presence:
  - `traces_sample_rate=0`, `enable_tracing=False` — no performance monitoring
  - `send_default_pii=False` — we set user context manually
- Call `_init_sentry()` as the **first line** in `lifespan()`, before Firebase/DB init

---

## Step 4: Backend — Global exception handler (filter 4xx noise)

**File:** [main.py](platform/main.py)

Add `@app.exception_handler(Exception)` that:
- Passes through 4xx `HTTPException` without reporting to Sentry
- Calls `sentry_sdk.capture_exception()` for 5xx and unhandled exceptions
- Returns 500 JSON response for unhandled exceptions

---

## Step 5: Backend — Set user context per request

**File:** [firebase_auth.py](platform/firebase_auth.py)

- Add `import sentry_sdk` (conditional, with try/except)
- Add `_set_sentry_user(decoded_token)` helper that calls `sentry_sdk.set_user({"id": uid, "email": email})`
- Call it in `verify_firebase_token()` at:
  - Line 91 (auth-disabled path) — before return
  - Line 103 (successful verification) — before return

This naturally covers all protected routes since they depend on `verify_firebase_token`.

---

## Step 6: Frontend — Install dependency

**File:** [package.json](portal/package.json)

Add `@sentry/react` to dependencies. This includes the browser SDK.

---

## Step 7: Frontend — Add env var type declaration

**File:** [vite-env.d.ts](portal/src/vite-env.d.ts)

Add `VITE_SENTRY_DSN: string;` to the `ImportMetaEnv` interface.

---

## Step 8: Frontend — Initialize Sentry in entry point

**File:** [main.tsx](portal/src/main.tsx)

Add `Sentry.init()` at the very top, **before** `createRoot`:
- Gate on DSN presence + `import.meta.env.PROD` (Vite built-in, true only in production builds)
- `tracesSampleRate: 0`, `replaysSessionSampleRate: 0`, `replaysOnErrorSampleRate: 0`
- Hydrate user context from `getCurrentUser()` if already logged in (page refresh scenario)

---

## Step 9: Frontend — Report errors from ErrorBoundary

**File:** [ErrorBoundary.tsx](portal/src/components/ErrorBoundary.tsx)

In `componentDidCatch` (line 32), add `Sentry.captureException(error)` with React component stack as context, alongside the existing `console.error`.

---

## Step 10: Frontend — Set/clear user context on auth changes

**File:** [auth.ts](portal/src/api/auth.ts)

- In `setCurrentUser()` (line 116): call `Sentry.setUser({id, email})` when user is set, `Sentry.setUser(null)` when cleared
- In `clearSessionAndCache()` (line 149): call `Sentry.setUser(null)` before/after clearing storage

---

## Step 11: Frontend — Environment variables

- Add `VITE_SENTRY_DSN` comment to `.env.example`
- Set actual DSN in `.env.production`
- Do NOT add DSN to `.env` or `.env.local` — absence = disabled in dev

---

## Files Modified Summary

| File | Change |
|------|--------|
| `platform/requirements.txt` | Add `sentry-sdk[fastapi]` |
| `platform/config.py` | Add `sentry_dsn`, `sentry_environment` fields |
| `platform/main.py` | Add `_init_sentry()`, call in lifespan, add global exception handler |
| `platform/firebase_auth.py` | Add `_set_sentry_user()`, call in `verify_firebase_token` |
| `portal/package.json` | Add `@sentry/react` |
| `portal/src/vite-env.d.ts` | Add `VITE_SENTRY_DSN` type |
| `portal/src/main.tsx` | Add `Sentry.init()` + user hydration |
| `portal/src/components/ErrorBoundary.tsx` | Add `Sentry.captureException()` |
| `portal/src/api/auth.ts` | Add `Sentry.setUser()` / `Sentry.setUser(null)` |

---

## Verification

1. **Backend**: Set `SENTRY_DSN` in `.env.local`, start server, hit an endpoint that raises a 500 → verify event appears in Sentry dashboard with user context
2. **Frontend**: Set `VITE_SENTRY_DSN` in `.env.local`, run `npm run build && npm run preview`, trigger an error → verify event in Sentry (won't fire in `npm run dev` due to `PROD` gate — temporarily remove that gate for testing)
3. **4xx filter**: Trigger a 404/401 on backend → confirm NO event in Sentry
4. **User context**: Verify logged-in errors show UID + email in Sentry event details
5. **Dev silence**: Remove DSN from local env, restart → confirm zero Sentry traffic

---

## Testing

- **Backend**: Add a test that verifies `_init_sentry()` doesn't crash when `sentry_dsn` is `None` (the default test env case). Verify the global exception handler returns correct status codes for 4xx vs 5xx.
- **Frontend**: Verify ErrorBoundary still renders correctly. The Sentry import is a no-op when not initialized, so existing tests should pass without modification.
