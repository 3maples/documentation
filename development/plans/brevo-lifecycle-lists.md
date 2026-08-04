# Brevo Lifecycle Lists — Capture Users in Brevo by Lifecycle Stage

**Date:** 2026-08-01
**Status:** Code complete — all phases implemented and green (85 new backend
tests, 9 new/updated portal tests; full project ruff + mypy + bandit clean;
1417 portal tests pass).

Phase 0 is **resolved** (see Ops prerequisites): DEV list IDs are configured in
`.env.local`, no new Brevo attributes were needed, and a live end-to-end run
confirmed a contact moves cleanly through all four DEV lists.

**DONE 2026-08-03:** the four PROD list IDs (`11`/`12`/`13`/`14`) are set, the
dry run was checked against the ops Users / New Users counts, and `--apply`
seeded all 24 prod contacts (16 Active / 6 Incomplete Setup / 2 Unverified,
0 Orphaned) plus `has_ever_joined_company` on 18 users. The backfill script was
deleted on 2026-08-04 — the nightly cron repeats everything it did.

**Still open:** the `brevo-lifecycle-reconcile` cron reports
`Firebase verification lookup failed`, so stages are being classified from the
stored `email_verified` mirror rather than live Firebase. Same on DEV and PROD.
`FIREBASE_CREDENTIALS_JSON` is set on both services, so the remaining candidates
are an unauthorized service account or blocked egress; the `exc_info` added to
`services/ops_verification.py` on 2026-08-04 will name the cause in the next run
once deployed.

**Scope:** `platform/` backend + `portal/` (reinstate page, ops Last Login column)

## Context

3Maples has four Brevo contact lists per environment that should always reflect where a customer
user sits in their lifecycle — PROD `#11 Active` / `#12 Orphaned` / `#13 Unverified` /
`#14 Incomplete Setup`, and a matching DEV set (`#15` / `#16` / `#17` / **a fourth whose ID is cut
off in the screenshot — must be confirmed, not assumed to be `#18`**). Today nothing in `platform/`
writes to Brevo lists: `services/brevo_email.py` is transactional-only, and the sole contacts/lists
code in the repo is the website's `syncContactToBrevo()` for the marketing form.

The outcome: every customer user belongs to **exactly one** of the four lists at all times, kept
current by lifecycle events, with a last-login timestamp on the Active cohort so dormancy is
visible — surfaced both in Brevo and on the Admin ops Users page.

The company-closure requirement pulls in a second, related change. Closing a company today is a
soft-archive that leaves every member still pointing at the dead company, locked out with a 403.
Per the agreed behavior: **non-owners get detached** (becoming true orphans who must be re-invited),
while **owners keep the link and gain a "Reinstate Company" option** on the existing
`/company-closed` page.

---

## Stage model — the correctness keystone

One pure function, shared by every event hook, the backfill, and the nightly reconcile.

```python
class BrevoStage(str, Enum):
    ACTIVE           = "active"
    ORPHANED         = "orphaned"
    UNVERIFIED       = "unverified"
    INCOMPLETE_SETUP = "incomplete_setup"

def derive_stage(user: "User", company: "Company | None") -> BrevoStage:
    if user.email_verified is False:              # None = "unknown", NEVER unverified
        return BrevoStage.UNVERIFIED
    if user.company is None:
        return (BrevoStage.ORPHANED if user.has_ever_joined_company
                else BrevoStage.INCOMPLETE_SETUP)
    if company is None:                            # dangling ref: company doc gone
        return BrevoStage.ORPHANED
    if company.status is CompanyStatus.ARCHIVED:
        return BrevoStage.ORPHANED                 # incl. owners of an archived company
    if not company.onboarding_completed:
        return BrevoStage.INCOMPLETE_SETUP
    return BrevoStage.ACTIVE
```

Values deliberately match the stage strings `routers/ops.py:441-445` already emits, so ops and
Brevo can't drift.

**Precedence rationale — test each explicitly:**

- **`email_verified is False` wins over everything.** An unverified user *can* be inside a company:
  invitation-accept takes an unverified token by design (`routers/auth.py:851-854`). Checking
  verification first matches `routers/ops.py:441-445`.
- **`email_verified is None` falls through.** `services/user_verification.py:26-36` is emphatic
  that `None` means *unknown*, never unverified (auth-disabled dev tokens, legacy docs). A legacy
  `None` user with a completed company must land in ACTIVE.
- **`onboarding_completed`'s default `True` is trusted as-is.** That default *is* the legacy
  backfill (`models/company.py:113-119`); derivation must not second-guess it. Matches
  `routers/ops.py:158`'s `{"$ne": False}`.
- **Archived company ⇒ Orphaned regardless of role.** This gives a valuable self-healing property:
  even if the close-time detach fan-out partially fails, members still classify as Orphaned.

### `has_ever_joined_company` — a stored flag, not an audit-log query

A verified user with `company is None` is either INCOMPLETE_SETUP (signed up, never joined) or
ORPHANED (was in a team). `services/ops_membership.py` makes this distinction today by querying the
audit log for `USER_REMOVE_FROM_COMPANY` / `USER_LEAVE_COMPANY`.

**Do not reuse that here.** `settings.audit_log_retention_days = 90` means those rows get pruned,
which would silently reclassify long-standing orphans as INCOMPLETE_SETUP on the next reconcile —
the exact hazard `ops_membership.py:18-21` names in its own docstring. A whole-collection `distinct`
is also far too heavy for a per-login hook.

Instead add **`User.has_ever_joined_company: bool = False`** — monotonic, never cleared (a rejoin is
handled by the `user.company is not None` branch, checked first). Set it at the two join sites and,
belt-and-braces, at all four detach sites. The one-time backfill computes it as
`user.company is not None or str(user.id) in fetch_ever_joined_user_ids()` — consulting the audit
log exactly once, before retention can eat it.

Deliberate divergence: the ops New Users page keeps deriving from the audit log (it's a display and
degrades gracefully). **Write this in the module docstring** so a future reader doesn't "fix" one to
match the other.

---

## Components

### 1. `platform/services/brevo_contacts.py` (new)

Mirrors **`services/slack_service.py`** structurally — leaf module, `TYPE_CHECKING`-only model
imports, plain `httpx`, 15s timeout, fail-open, no-op when unconfigured, sync `dispatch_*` wrappers
over `_schedule()` + the `_bg_tasks` strong-ref set with `add_done_callback(discard)` (required:
the event loop holds only a weak ref).

**Configuration gate:** `_is_configured()` requires the API key **and all four list IDs**. Partial
configuration is the dangerous state — you'd add to the target list and fail to remove from the
others, leaving a user in two lists. All-or-nothing.

**Two Brevo v3 calls per sync.** There is no single "set membership to exactly this list" call:
the upsert endpoint takes `listIds` (additive) but not `unlinkListIds`; the update endpoint takes
both but does not create.

1. **Upsert + add to target** — `POST https://api.brevo.com/v3/contacts`
   `{"email", "ext_id": str(user.id), "attributes": {...}, "listIds": [target], "updateEnabled": true}`.
   Same shape the website function already proves against the live API
   (`website/functions/index.js:44-90`). Headers as in `brevo_email.py`.
2. **Remove from the other three** — `PUT https://api.brevo.com/v3/contacts/{quote(email, safe="")}`
   with `{"unlinkListIds": [other three]}`. Use `urllib.parse.quote(email, safe="")` — `+`
   addresses are common and would otherwise decode as a space.

Gate on `response.is_success`, not an equality check (`201` on create, `204` on update).
**Optimization:** when the stage is unchanged (a LAST_LOGIN-only refresh, detectable via
`user.brevo_stage == target`), skip call 2 — halving requests on the common path.

**Attributes:**

| Brevo attribute | Type | Source | Note |
|---|---|---|---|
| *(identifier)* | — | `user.email` | top-level `email`, **not** an attribute |
| `FIRSTNAME` / `LASTNAME` | Text | `user.first_name` / `last_name` | Brevo built-ins |
| `COMPANY_NAME` | Text | `company.name` or `""` | **send `""` for orphans, don't omit** — omitting leaves the stale name |
| `SIGNUP_DATE` | Date | `user.created_at` | `YYYY-MM-DD` |
| `LAST_LOGIN` | Date | `user.last_login_at` | **omit the key when `None`**, never send null |

Nice consequence: with `LAST_LOGIN` as a Brevo **Date** attribute, the 24h throttle below isn't an
approximation — it's exactly the resolution the attribute can represent.

**Logging — one deliberate divergence from `slack_service.py`.** That module logs
`response.text.strip()` on non-2xx; **do not copy it.** Brevo error bodies echo the contact email.
Log the stage, the call, the status, and the parsed `body["code"]` only (Brevo codes are enum-like:
`duplicate_parameter`, `invalid_parameter`) — never the raw body, never `message`, never the email.

**Public seam:**

```python
async def sync_user_stage(user, company=None, *, stage=None) -> None   # never raises
def  dispatch_user_stage_sync(user, company=None, *, stage=None) -> None
```

Scripts must `await sync_user_stage(...)` directly — `dispatch_*` needs a running loop.

> The `_schedule`/`_bg_tasks` duplication with `slack_service.py` is knowingly accepted to keep this
> change additive; file the extraction to a shared `services/fire_and_forget.py` as a follow-up and
> mention it in the PR so `/code-review` doesn't re-litigate it.

### 2. `platform/config.py`

Four fields directly after the existing `brevo_*_template_id` block (`config.py:124-129`):

```python
brevo_active_list_id: int | None = Field(default=None, validation_alias="BREVO_ACTIVE_LIST_ID")
brevo_orphaned_list_id: int | None = Field(default=None, validation_alias="BREVO_ORPHANED_LIST_ID")
brevo_unverified_list_id: int | None = Field(default=None, validation_alias="BREVO_UNVERIFIED_LIST_ID")
brevo_incomplete_setup_list_id: int | None = Field(default=None, validation_alias="BREVO_INCOMPLETE_SETUP_LIST_ID")
```

DEV/PROD separation is **per-deployment env vars only — no `sentry_environment` branch**.
`.env` unset (safe off default) · `.env.local` DEV IDs · `.env.production` PROD IDs ·
`.env.example` all four present but empty with the "all four or nothing" comment.

Two notes:
- `Settings` forbids extra env keys, so these must be declared before any `.env` carrying them loads.
- **`tests/test_settings_repr_masking.py` does *not* need updating** — `_is_secret_field` returns
  `False` for these names, so they land in neither the `classified` nor the `known_secret` set
  (precedent: the existing `trello_*_list_id` fields). Optionally add them to
  `test_leaves_ordinary_config_alone`'s parametrize list as a deliberate positive assertion.

### 3. `platform/models/user.py`

All `Optional`/defaulted → no migration, same trick as `email_verified`:

```python
last_login_at: Optional[datetime] = None
has_ever_joined_company: bool = False
brevo_stage: Optional[str] = None          # last stage successfully pushed
brevo_synced_at: Optional[datetime] = None
```

**The login throttle needs no extra field** — read the old `last_login_at` before overwriting:

```python
previous = user.last_login_at
now = datetime.now(timezone.utc)
await User.get_pymongo_collection().update_one({"_id": user.id}, {"$set": {"last_login_at": now}})
user.last_login_at = now
should_push = previous is None or (now - previous) >= timedelta(hours=24)
```

Exactly one Brevo call per user per 24h, zero additional state. If the push fails the timestamp has
still advanced and Brevo lags ≤24h — the nightly reconcile heals it. **State the trade-off plainly:
`last_login_at` has day granularity, not per-request precision.** That is the right resolution for a
dormancy signal (and for the Brevo Date attribute).

**Use a targeted `$set`, never `user.save()`.** `User` has `@before_event([Replace, Insert])
update_timestamp` (`models/user.py:50-52`); a `save()` per login would make `updated_at` mean "last
login" — silently changing a field the ops pages display. Follow the existing precedent at
`routers/users.py:429-433`. **Assert this in a test** — it's exactly what a later refactor breaks.

`brevo_stage` / `brevo_synced_at` serve a different purpose: they let the nightly reconcile skip
no-ops instead of re-pushing everyone every night. Without them the reconcile degrades to "push
everyone nightly" — tolerable below ~2k users, but it burns quota and gives no observability.

### 4. `platform/models/audit_log.py`

Add `COMPANY_REINSTATE = "company_reinstate"` to `AuditAction` (Company block, `:60-65`).

---

## Wiring — every insertion point

All calls are `dispatch_user_stage_sync(...)`, fire-and-forget, **after** the DB write.

| # | Event | File : function | Placement / stage |
|---|---|---|---|
| 1 | Signup | `routers/auth.py:449-462` `signup()` | after `dispatch_user_signup_notification` (`:461`) → UNVERIFIED |
| 2 | Verified (token) | `services/user_verification.py:54-68` | inside the existing changed-guard, after `user.save()` |
| 3 | Verified (ops write-back) | `services/user_verification.py:39-51` `set_email_verified()` | **add a `if verified == user.email_verified: return` guard first** — it's a public function, and unguarded this means one Brevo call per user per ops page render |
| 4 | Login | `routers/auth.py:383-404` `authenticate()` | see ordering below |
| 5 | Company created | `routers/auth.py:967-998` | set `has_ever_joined_company = True` before `user.save()` (`:996`); dispatch after `:997` → INCOMPLETE_SETUP. This is "leaves Orphaned when they create a new company" |
| 6 | Invitation accepted | `routers/auth.py:866-871` | set the flag in the `should_update_company` block; dispatch before the return (`:896`) with the loaded company → "…or join a new company" |
| 7 | Onboarding completed | `routers/auth.py:1001-1030` | capture `was_completed` **before** `:1025-1026`; dispatch after `company.save()` **only on the `False→True` transition** → ACTIVE. Avoids a call on every step advance |
| 8-10 | Orphan ×3 | `routers/users.py` `update_user()` (`is_company_removal` branch), `leave_company()` (`:285`), `delete_user()` (`:437`) | after `create_audit_log`, before the return → ORPHANED |
| 11 | Company closed | `routers/companies.py:225-267` | §Company closure |
| 12 | Reinstated | new endpoint | §Reinstate |

**Login ordering in `authenticate()`** — staff early-return first (staff have no `User` doc and must
**never** enter these lists) → resolve user → `sync_email_verified_from_token` → **`$set`
`last_login_at` here** (they did log in, even if archived) → load company → the `COMPANY_ARCHIVED`
raise → then, **on the success path only**, `if should_push: dispatch(...)`. Archived owners get
their stage from the nightly reconcile — one less race, and much simpler than dispatching before a
`raise`.

**Why verification hooks into `user_verification.py`:** there is no server-side "user verified"
event — Firebase owns verification and the platform only *mirrors* the claim
(`services/user_verification.py:1-16`). The `False`/`None` → `True` transition inside those two
functions **is** the event, and hooking there picks up the ops live-Firebase write-back for free.

---

## Company closure: detach non-owners

New behavior in `close_company_account()` (`routers/companies.py:225-267`), after the archive
`set()` and the `COMPANY_CLOSE` audit log. Extract the mechanism to
**`services/company_service.py::detach_non_owner_members(company)`** so the reconcile job can reuse
it for healing.

```python
await User.get_pymongo_collection().update_many(
    {"company": company.id, "role": {"$ne": UserRole.OWNER.value}},
    {"$set": {"company": None, "has_ever_joined_company": True}},
)
# then per-member audit rows + Brevo dispatch, chunked
```

- **The audit action must be `USER_REMOVE_FROM_COMPANY`.** `ops_membership.MEMBERSHIP_REMOVAL_ACTIONS`
  is the only signal the ops New Users page has; a new action would make these users read as "never
  joined". Add `metadata={"reason": "company_closed"}` to keep the paths distinguishable without
  touching ops semantics. Anchor `company_id=company.id`, `resource_id=str(member.id)`, matching
  `routers/users.py:262-267`.
- **No transactionality, by design** — the repo uses no Mongo sessions anywhere (`grep start_session`
  → zero hits). **Archive first**: that single write is what revokes access for everyone via
  `dependencies._assert_company_not_archived`. The detach loop is then best-effort; a partial failure
  leaves some members attached to an archived company — already locked out, no security hole, and
  they still derive as ORPHANED.
- **Owners keep `company`** so they can reinstate. Multiple owners → all keep it, all → ORPHANED.
- **`await` the audit rows in bounded chunks** (`asyncio.gather` over slices of ~20) rather than
  fire-and-forget: tests need to assert on those rows, and `create_task` makes that flaky under
  `TestClient`. Member counts are seat-billed and realistically <100.
- **Idempotency:** the existing already-archived early return (`:239-243`) must be preserved.
- **Document the downstream consequence:** detached members now show as `orphaned` on the ops pages
  instead of `active`. That is intended — say so in the changelog so it isn't read as a regression.

---

## Reinstate flow

### Backend — `POST /companies/me/reinstate`

Declared **above** the `/{company_id}` routes (same convention as `/companies/industries` at `:102`).

**No company ID in the path**, deliberately: `portal/src/api/client.ts:65-76` calls `setCompanyId("")`
before `/company-closed` renders, and `LoginPage.tsx:206-208` navigates without an id. The page has
no ID to send. Resolving from the token is also strictly safer.

- **Auth:** `Depends(verify_verified_firebase_token)` plus a new `_require_owner_of_own_company()`
  modelled on `_require_owner_company_access` (`routers/companies.py:65-84`) minus the path param.
  That helper is **archive-agnostic** (it never calls `_reject_if_archived`), which is exactly what's
  needed. It must **not** use `assert_company_access` / `_assert_company_not_archived` — both 403 on
  ARCHIVED, the state this endpoint exists to exit. (`assert_is_manager` would also permit Admins;
  owner-only is required.)

| Condition | Response |
|---|---|
| owner, ARCHIVED | 200 · `status=ACTIVE`, `archived_at=None`, `updated_at=now` · `COMPANY_REINSTATE` audit · Brevo dispatch |
| owner, already ACTIVE | 200, same body, **no second audit row** (idempotent) |
| role ≠ OWNER | 403 "Only company owners can perform this action" |
| `user.company` is None | 400 |
| company doc missing (future purge) | 404 |

Response body carries `{message, status, company_id, onboarding_completed, onboarding_step}` — enough
for the portal to route, without importing `routers/auth.py`'s serializer (avoids router→router
coupling). **Detached members are not restored**; say so in the `message` and the UI copy.

### Portal — `src/pages/CompanyClosedPage.tsx`

- `src/api/companies.ts`: add `reinstateCompany()`.
- `handleReinstate` → on success `setCompanyId(res.company_id)`, `setAuthenticatedSession()`, then
  `navigate(res.onboarding_completed ? "/dashboard" : "/onboarding", { replace: true })`; the second
  branch also needs `setOnboardingInProgress()`.
- **Promote "Reinstate Company" to the primary button**, demote "Create New Company" to secondary,
  and reword the heading — reinstating is now the expected action for an owner. Add a line that
  members removed at closure must be re-invited.
- 403 (non-owner) / 404 (purged) → show the message and hide the reinstate button, leaving "Create
  New Company" usable. Add `isReinstating` to the existing disabled pattern.
- No `client.ts` changes: `/company-closed` is already in `COMPANY_ARCHIVED_SELF_HANDLED_ROUTES`
  (`:57-63`), so the call won't trigger the redirect loop.

---

## Admin ops UI: last-login column

- **`platform/routers/ops.py::_serialize_user_summary` (`:277-299`)** — add
  `"last_login_at": user.last_login_at.isoformat() if user.last_login_at else None`, alongside the
  existing `created_at`. `None` renders as "Never" (a real signal, distinct from a missing value).
- **`portal/src/api/ops.ts`** — add `last_login_at: string | null` to `OpsUser`, with a comment noting
  the ≤24h day-granularity staleness so nobody reads it as a live timestamp.
- **`portal/src/pages/ops/OpsUsersPage.tsx`** — add a `Last Login` column (`FIT` width) after
  `Created`. Two things that must be updated in the same edit or the table silently breaks: the empty
  row's **`colSpan={6}` → `7`**, and the table's **`min-w-[820px]`** allowance.
- Render `new Date(row.last_login_at).toLocaleDateString()`, falling back to `"Never"`.
- Server-side sorting is out of scope — `GET /ops/users` sorts on `-User.created_at` (`:357`) and
  adding a sort parameter is a larger change. Note it as a possible follow-up.

---

## Backfill + nightly reconcile

`platform/services/brevo_reconcile.py::reconcile_all(*, apply: bool, concurrency: int = 4)` — one
pass, shared by both entry points so there is one classification path and no drift:

all Users → Companies keyed by id (no N+1) → **one** `fetch_ever_joined_user_ids()` (the single
moment `has_ever_joined_company` is backfilled) → chunked `fetch_email_verified_lookup()` in 100s
reusing `services/ops_verification.py` exactly as `scripts/backfill_email_verified.py:63-67` does
(this makes UNVERIFIED accurate rather than trusting a possibly-stale mirror) → skip rule →
bounded-concurrency push → write `brevo_stage` / `brevo_synced_at` **on success only** → **heal
non-owner members still attached to ARCHIVED companies** via `detach_non_owner_members`.

- `scripts/backfill_brevo_contacts.py` — dry-run default, `--apply` to write; same argparse shape and
  "would →" output as `scripts/backfill_email_verified.py`. **Removed 2026-08-04** once DEV and PROD
  were both seeded; recover from git history if a new environment needs a preview.
- `scripts/reconcile_brevo_contacts.py` — Render cron entry point mirroring
  `scripts/snapshot_seat_counts.py` (Sentry init, `init_db()`, per-item try/except,
  `capture_exception` + `sys.exit(1)` on top-level failure).
- `platform/render.yaml` — new `type: cron`, `schedule: "40 7 * * *"` (after the 06:15 seat snapshot).
  **The four list-ID env vars must be set on the cron service too** — `render.yaml` only declares
  `PYTHON_VERSION`; the rest come from the dashboard. Manual deploy step; call it out in the PR.
- **Staff users are excluded** — separate collection, never customer-facing.

---

## Testing (TDD — failing test first, per CLAUDE.md)

**Anti-flake rule for every hook test:** monkeypatch `dispatch_user_stage_sync` and assert on the
*call*, never on the network. `asyncio.create_task` inside a handler runs on the `TestClient` portal
loop and may not finish before assertions. (This is the convention the Slack signup work established.)

**New backend files**

1. `tests/test_brevo_stage_derivation.py` — pure unit, no DB/network. **Write this first, in full.**
   `False` + no company → UNVERIFIED · `False` + completed company → UNVERIFIED (verification wins) ·
   `None` + completed company → ACTIVE · `None` + no company + never joined → INCOMPLETE_SETUP ·
   verified + no company + never joined → INCOMPLETE_SETUP · verified + no company +
   `has_ever_joined_company` → ORPHANED · verified + ARCHIVED (owner) → ORPHANED · verified +
   `onboarding_completed=False` → INCOMPLETE_SETUP · verified + legacy default `True` → ACTIVE ·
   dangling ref → ORPHANED · all four list IDs distinct and every stage maps to one.
2. `tests/test_brevo_contacts.py` — `httpx.MockTransport`, cloning `tests/test_slack_service.py:29-37`.
   Each of the five settings nulled in turn → **zero** requests · POST URL/header/`updateEnabled`/
   `listIds` / attribute map · `LAST_LOGIN` omitted when `None` · `COMPANY_NAME == ""` for an orphan ·
   PUT path URL-encodes a `+` address and unlinks exactly the other three · non-2xx → no raise **and
   `caplog` contains neither the email nor the raw body** · exception → no raise · stage-unchanged
   skips the PUT · dispatch retains a strong ref.
3. `tests/test_brevo_reconcile.py` — skip rule; push on stage change; mirror fields written on success
   but **not** on failure; one failing user doesn't abort; `StaffUser` never included; heals
   still-attached members of an ARCHIVED company.
4. `tests/test_company_close_detach.py` — non-owners detached, owners keep `company` · one
   `USER_REMOVE_FROM_COMPANY` row per member with the right `company_id` and
   `metadata.reason == "company_closed"` · **`ops_membership.fetch_ever_joined_user_ids()` includes
   them** (the ops-regression guard) · flag set · idempotent second close · zero-member company ·
   dispatch for owner + each member.
5. `tests/test_company_reinstate_api.py` — owner reinstates → 200 and a subsequent
   `GET /companies/{id}` succeeds · idempotent, no second audit row · Admin 403 · Member 403 ·
   no company 400 · missing doc 404 · audit row shape · one dispatch · detached members **not** restored.

**Extended existing files**

6. `tests/test_auth_api.py` — `POST /auth` sets `last_login_at` and **does not change `updated_at`** ·
   second login <24h doesn't re-dispatch, one >24h does (backdate directly) · staff login never
   dispatches · signup dispatches once · onboarding `completed=true` dispatches once, a repeat doesn't ·
   company-onboarding and invitation-accept dispatch and set the flag.
7. `tests/test_user_email_verification.py` — the `False→True` transition dispatches in **both**
   functions; a no-change call does not.
8. `tests/test_user_api.py` — all three orphan paths dispatch ORPHANED and set the flag.
9. `tests/test_ops_users_api.py` — `last_login_at` present in the payload; `None` when never logged in.
10. `tests/conftest.py` — session-scoped autouse `_disable_brevo_contact_sync` cloning
    `_disable_slack_webhook` (`:348-360`): null the four list IDs, restore on teardown. Null the
    **IDs, not `brevo_api_key`** — other suites use the key for transactional email. Without this the
    suite would POST into the real DEV lists via `.env.local`.

**Portal**

11. `portal/tests/CompanyClosedPage.test.tsx` *(new)* — all three buttons render · reinstate POSTs to
    `/companies/me/reinstate`, sets the company id, navigates `/dashboard` · `onboarding_completed:false`
    → `/onboarding` · 403 → error shown, reinstate hidden, "Create New Company" still usable · 404 →
    "no longer available" · all buttons disabled in flight.
12. `portal/tests/OpsUsersPage.test.tsx` *(extend)* — the Last Login column renders a formatted date,
    and `"Never"` when `last_login_at` is null.

**Gates:** `./run_ruff.sh` + `./run_mypy.sh` scoped to each touched subtree after every phase, and
`npm run typecheck` in `portal/` (`npm run build` is vite-only and will not catch type errors).

---

## Phasing

- **Phase 0 — Brevo dashboard (manual, blocking).** Resolve the verification items below *before* any
  code is written.
- **Phase 1 — Config + derivation (no I/O).** Test 1 → the four `Settings` fields + env files →
  `BrevoStage` / `derive_stage` / `_is_configured` → conftest fixture 10.
- **Phase 2 — Wire layer.** Test 2 → upsert / unlink / `sync_user_stage` / dispatch.
- **Phase 3 — Model + login.** Four `User` fields → tests in 6 → `authenticate()` `$set` + throttle.
  Check `tests/test_test_data_cleanup_coverage.py` and any User-shape assertions first.
- **Phase 4 — Lifecycle hooks 1,2,3,5,6,7,8,9,10** (dispatch-only, no behavior change) + tests 6,7,8.
- **Phase 5 — Close fan-out.** Test 4 → `detach_non_owner_members` → wire into `close_company_account`.
- **Phase 6 — Reinstate.** Audit action → test 5 → endpoint → portal page + test 11.
- **Phase 7 — Ops last-login column** (backend field + portal column) + tests 9, 12.
- **Phase 8 — Backfill + reconcile + Render cron.** Run against DEV: `--dry-run`, review the tally
  against the ops Users / New Users counts, then `--apply`.
- **Phase 9 — Docs.** In-repo plan doc, `.env.example`, changelog noting the close-detach change.

Phases 1-4 are independently shippable and deliver three of the four lists on their own.

---

## Ops prerequisites — RESOLVED 2026-08-01

All of Phase 0 was settled against the live account rather than the docs:

- **DEV list IDs confirmed: `15` Active / `16` Orphaned / `17` Unverified / `18` Incomplete Setup**,
  set in `.env.local`. PROD remains `11`/`12`/`13`/`14`.
- **No new Brevo attributes were created.** `GET /v3/contacts/attributes` showed the account already
  carries everything needed, so the sync reuses it:

  | Meaning | Brevo attribute | Type | Note |
  |---|---|---|---|
  | Company | `COMPANY` | text | shared with the website contact form |
  | Last login | `SUBMITTED_AT` | date | shared with the website contact form |
  | Name | `FIRSTNAME` / `LASTNAME` | text | Brevo built-ins |
  | Signup date | *(none)* | — | Brevo's own read-only "Creation date" |

- **`BREVO_API_KEY` has Contacts scope** — confirmed by a successful live run.

**Live end-to-end verification** (a throwaway contact walked through all four stages against the DEV
lists, then deleted) confirmed every open API question:

- `updateEnabled: true` **adds** to `listIds` rather than replacing membership.
- `PUT /v3/contacts/{url-encoded email}` accepts the email as the identifier and honours
  `unlinkListIds`, so the compact two-call sync stands — the four-call
  `POST /v3/contacts/lists/{id}/contacts/remove` fallback is not needed.
- A contact not in a list is tolerated (the normal steady state).
- `YYYY-MM-DD` is accepted for the Date attribute.
- `ext_id` is accepted on this account.
- **The contact sat in exactly one list at each of the four stages** — the invariant the whole design
  rests on.
- An attribute sent as `""` is **cleared** by Brevo, which is what blanks a departing user's `COMPANY`.

### Post-implementation fix: one dispatch per request (2026-08-02)

Manual testing surfaced odd list counts in the Brevo UI (Unverified showing `-4`).
The membership itself was always correct — the counters were transient UI artifacts — but
investigating found a genuine race.

`sync_email_verified_from_token` / `set_email_verified` used to sync Brevo themselves, *and*
every caller synced again after finishing its own mutations. One request therefore fired **two
concurrent syncs for the same contact**:

- In `POST /auth` both computed the same stage — merely double the API calls and needless churn.
- In **invitation-accept they computed different stages**: the verification sync ran *before*
  `user.company` was assigned (deriving Incomplete Setup), the caller's ran after (deriving
  Active). Two fire-and-forget tasks racing on one contact, last writer wins — so a new team
  member could be stranded in the wrong list.

Fixed on two levels:

1. **Those functions now return a `bool` instead of dispatching.** The rule is now *whoever owns
   the request dispatches exactly once, at the end, with the user fully mutated* — written up at
   the bottom of `services/user_verification.py`. Callers OR the flag into their existing
   dispatch condition, which also closes a gap the old code had: verifying in another tab and
   returning inside the 24h login throttle no longer leaves the user in Unverified.
2. **`sync_user_stage` serializes per contact** via a refcounted lock registry
   (`_contact_guards`). The upsert-then-unlink pair is not atomic, so any residual concurrency
   the rule can't cover — two browser tabs, the onboarding fan-out overlapping a login — can no
   longer interleave. Different contacts still sync concurrently, which the reconcile sweep needs.

Verified live: four concurrent syncs for one contact, each targeting a different stage, leave it
in exactly one list. Regression tests in `test_brevo_lifecycle_hooks.py` (dispatch-once) and
`test_brevo_contacts.py` (non-interleaving, registry doesn't leak).

**Ruled out along the way:** spurious `unlinkListIds` calls for lists a contact isn't in do *not*
decrement Brevo's counters (probed directly — the counter held at 0 across repeated unlinks), and
the resend-invitation endpoint touches Brevo not at all.

### Two consequences of reusing existing attributes — worth knowing

1. **`SUBMITTED_AT` is shared with the website contact form**, which writes the form-submission time
   there. For someone who both filled in that form and uses the app, whichever wrote last wins. Give
   it a dedicated attribute if that ambiguity ever matters.
2. **Backfilled users get the wrong "Creation date."** Brevo stamps it when the contact is created,
   so it equals the signup date for everyone who signs up from now on — but for the users seeded by
   the one-time backfill (2026-08-03) it reads as the backfill date. Only a dedicated
   `SIGNUP_DATE` attribute would fix that.

Still unverified (neither is blocking): whether the upsert can reset `emailBlacklisted` — we never
send the field, so it shouldn't, but a silently un-unsubscribed user is a compliance problem worth
confirming — and the Contacts-API rate limit, which only matters for the backfill's concurrency
ceiling (currently 4).

## Verification

1. `cd platform && ./run_tests.sh tests/test_brevo_stage_derivation.py tests/test_brevo_contacts.py
   tests/test_company_reinstate_api.py tests/test_company_close_detach.py` plus the touched existing
   files; `cd portal && npm test -- CompanyClosedPage OpsUsersPage`.
2. With DEV IDs in `.env.local` and `uvicorn main:app --reload` against the Dev cluster, walk one user
   end to end and watch them move between DEV lists in the Brevo UI: sign up → **Unverified** → verify
   + log in → **Incomplete Setup** → finish onboarding → **Active** (confirm `LAST_LOGIN` populated) →
   leave the team → **Orphaned** → create a new company → **Active**.
3. As an owner: close the company from Settings → confirm non-owners are detached and everyone lands in
   **Orphaned** → log in as the owner → `/company-closed` → **Reinstate Company** → lands in the app and
   returns to **Active**. Confirm the removed members are *not* back.
4. Ops portal → Users: the Last Login column shows a date for the walked-through user and "Never" for a
   user who has never logged in.
5. ~~`python scripts/backfill_brevo_contacts.py` (dry run) — confirm the tally matches the ops Users /
   New Users counts before `--apply`.~~ Done 2026-08-03; script removed 2026-08-04.

## Risks / out of scope

**Risks**

1. **Audit-log retention vs. orphan detection** — the biggest correctness risk, and the reason for the
   stored `has_ever_joined_company` flag. Audit-log derivation would silently reclassify orphans after
   90 days.
2. **Unverified Brevo API contract** — the Phase 0 list above. All of it confirmed before coding.
3. **Rate limits on backfill/reconcile.** Bounded concurrency (start at 4); no retry logic in v1 —
   fail-open plus the next nightly run *is* the retry.
4. **Email change orphans a Brevo contact.** `PUT /users/{id}` can change `email`; the old contact
   stays behind. Sending `ext_id` now costs nothing and makes the eventual fix
   (`PUT /v3/contacts/{ext_id}?identifierType=ext_id`) possible. **Not fixed here** — flagged.
5. **Consent/GDPR.** These are lifecycle segments for existing customers, not a marketing opt-in. If
   they're ever used for campaigns an opt-out path is needed, and "we never reset `emailBlacklisted`"
   becomes load-bearing.
6. **`platform/.env.production` holds a live `BREVO_API_KEY` in plaintext** (line 8). Confirm that
   file's git-tracking status before adding four more values to it.

**Out of scope** — the 60-day archived-company purge cron (a separate session; when it lands it should
also detach owners, at which point they become true orphans under the existing rules) · deleting or
blacklisting Brevo contacts when a user is purged · email-change contact migration · retry-in-request ·
extracting the shared `_schedule`/`_bg_tasks` helper · server-side sorting on the ops Last Login column ·
website lists `#6`/`#7` and `website/functions/index.js`, both untouched.

**Known UX gap, flagged not fixed:** after the detach fan-out, non-owner members of a closed company no
longer hold a company link, so they never see `COMPANY_ARCHIVED` and never reach `/company-closed` —
`POST /auth` returns `company_id: null` and routes them to `/onboarding` with no explanation. That is
the correct Orphaned *state*, but a "your team's account was closed" interstitial would be the humane
version. Out of scope unless you want it.
