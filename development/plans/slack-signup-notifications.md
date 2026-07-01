# Slack Signup Notifications — Design

**Date:** 2026-07-01
**Status:** Implemented (backend). Pending: manual end-to-end verification against the real webhook.
**Scope:** `platform/` backend only

## Purpose

Post an **internal** Slack notification whenever a new user signs up or a new
company is onboarded in 3Maples. This is an ops/growth signal for the 3Maples
team — **not** a client-facing feature. All notifications go to a single
internal Slack channel.

## Trigger events

Both signup pathways in `platform/routers/auth.py`:

| Event | Endpoint | Insert point | Message |
|---|---|---|---|
| New user account | `POST /auth/signup` → `signup()` (`routers/auth.py`) | after `user.insert()` | "🆕 New user signup" |
| New company / tenant | `POST /auth/company-onboarding` → `create_company_with_bootstrap()` (`services/company_service.py`) | after `company.insert()` | "🏢 New company onboarded" |

## Architecture

Follows the established outbound-integration pattern already used by
`services/brevo_email.py` (email) and `services/trello_service.py` (Trello
cards): a small service module using `httpx.AsyncClient`, one config secret,
invoked as a fire-and-forget side effect via `asyncio.create_task(...)`.

**This does NOT route through the Maple agent system.** Maple agents are
user-chat-driven CRUD; a signup notification is a plain backend side effect. The
Slack sender identity/branding lives in the Slack app config, not in agent code.

```
POST /auth/signup ──────────────► user.insert() ──► asyncio.create_task(notify_user_signup(user))
                                                                     │
POST /auth/company-onboarding ──► company.insert() ► asyncio.create_task(notify_company_signup(company))
                                                                     │
                                                                     ▼
                                      services/slack_service.py  ──httpx POST──► Slack Incoming Webhook
```

## Components

### 1. `config.py`
Add one optional setting following the existing convention:

```python
slack_webhook_url: str | None = Field(default=None, validation_alias="SLACK_WEBHOOK_URL")
```

Unset ⇒ feature is disabled (no-op). Note: `Settings` forbids extra env keys,
so this field must be declared before `.env.local`'s `SLACK_WEBHOOK_URL` will
load at all. Set in `.env.local` (dev) and the prod
environment as `SLACK_WEBHOOK_URL`.

### 2. `services/slack_service.py` (new)
Mirrors `brevo_email.py` / `trello_service.py`:

- `notify_user_signup(user: User) -> None` — builds the user-signup message, delegates.
- `notify_company_signup(company: Company) -> None` — builds the company message, delegates.
- `_post_to_slack(blocks: list, fallback_text: str) -> None` — private; `httpx.AsyncClient` with a 15s timeout, POSTs the Block Kit JSON payload to `settings.slack_webhook_url`.

**Message format** — simple Slack Block Kit:
- Header line: "🆕 New user signup" / "🏢 New company onboarded".
- Fields section:
  - User event: name, email, phone (if present), created_at.
  - Company event: company name, industry, email, phone, created_at.
- An **environment label** (`[dev]` / `[prod]`) derived from a settings/env
  value, so signups produced while testing against the Dev cluster are visually
  distinct from real production signups in the same channel.
- `fallback_text` provides the plain-text notification/summary line.

Both notify functions accept the already-built `User` / `Company` document and
read fields off it; they never touch the DB.

The environment label reuses the existing `settings.sentry_environment`
(`"development"` / `"production"`) rather than adding a new setting.

### 3. Wiring
Both wired at the **auth endpoints** (not the shared
`create_company_with_bootstrap` service), via thin sync `dispatch_*` helpers
that call `asyncio.create_task(...)` — matching the existing
`asyncio.create_task(create_audit_log(...))` usage in `routers/auth.py`:

- `routers/auth.py::signup()` — after `user.insert()`, add
  `dispatch_user_signup_notification(user)`.
- `routers/auth.py::complete_company_onboarding()` — after the company is
  created and the owner linked, add `dispatch_company_signup_notification(company)`.

**Why the endpoint, not `create_company_with_bootstrap`:** that service is also
called directly by seed/bootstrap and test code
(`test_audit_integration.py`, `test_template_bootstrap.py`). Wiring the
notification there would fire on programmatic company creation, not just real
signups. The onboarding endpoint is the true "a company signed up" event.

## Error handling (fail-open)

- **Disabled when unconfigured:** if `slack_webhook_url` is `None`, the notify
  functions return early (no-op). Keeps local dev, tests, and any secret-less
  environment working with zero config.
- **Never breaks signup:** the httpx call is wrapped so any failure (timeout,
  non-2xx, network error) is logged and swallowed. A Slack outage must never
  break or delay a signup. Consistent with the "outbound fails open" philosophy
  already used in the translation layer.
- **Never blocks the response:** fire-and-forget via `create_task` means the
  signup HTTP response does not wait on Slack.

## Testing (TDD)

- `tests/test_slack_service.py` (httpx mocked):
  - correct webhook URL + payload contains expected user/company fields;
  - no-op when `slack_webhook_url` is `None`;
  - exceptions are swallowed (function never raises).
- Wiring tests (`test_auth_api.py`): patch the sync `dispatch_*` helpers on the
  auth router and assert the signup / company-onboarding endpoints call them
  with the right document (avoids asserting on a raw `create_task`).
- Test-suite safety: a session-scoped autouse fixture in `tests/conftest.py`
  forces `slack_webhook_url = None` so the existing signup/onboarding tests
  (which now hit `dispatch_*`) never POST to the real channel via `.env.local`.
  The `slack_service` tests re-enable it with a function-scoped monkeypatch.
- Gates: `./run_mypy.sh` + `./run_ruff.sh` on `config.py`, `services/`,
  `routers/auth.py` before completion. **Both pass; all 40 slack+auth tests green.**

## Ops / secrets

- Slack app → **Incoming Webhooks** → one webhook bound to the internal channel.
- Store the URL as `SLACK_WEBHOOK_URL` in `.env.local` (dev) and prod env.
  **Done — user has configured `.env.local`.**
- Add `SLACK_WEBHOOK_URL` to `.env.example` / config docs. No real webhook is
  committed.

## Out of scope (YAGNI)

- No retry / queue / dead-letter — fire-and-forget only.
- No per-company or per-event channel routing — single internal channel.
- No Slack interactivity (buttons, threads, slash commands).
- No client-facing notifications — internal team use only.
