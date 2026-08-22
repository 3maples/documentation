# WO-BREVO-EVENTS — App-to-Brevo Lifecycle Events

> **Status: implemented 2026-08-19.** Backend is done and green. What remains
> is the Brevo-side handover in §3 and the two one-off scripts in §6.

## Context

Ron's work order ([3maples-wo-brevo-events.md](3maples-wo-brevo-events.md)) asks the backend to tell Brevo
the moment a user crosses each lifecycle line, so onboarding emails fire on real
behavior instead of timers. Today Brevo automations enter on timed sends; Ron
wants them to enter on real-time custom events (`POST /v3/events`) with contact
attributes carrying the state that stops them.

The app already has a mature Brevo integration — transactional email, a
four-list lifecycle sync, a nightly reconcile cron. What's missing is the
*events* channel and the *activation* attributes. This plan adds one new
service alongside the existing ones, hooks it at five points, and extends the
nightly cron as the safety net.

Decisions taken with Simon before writing this plan:

- **W4** ships as written — `first_document_generated` on Google Doc creation.
  The app never transmits anything to a client, so document generation is the
  only real behavioral signal; see finding 1.
- **Invited joiners** — attributes still written, but the `account_created`
  *event* is suppressed when the signup matches a pending invitation, so a new
  hire at an established customer never enters Cliff 1.
- **Existing users** — attribute backfill only; no events fired, and every event
  pre-marked as sent so nothing re-triggers.
- **`account_created`** fires at signup, with an `EMAIL_VERIFIED` attribute and
  an `email_verified` event so Ron can hold Cliff 1's first send until
  verification lands.

---

## 1. What already exists (do not rebuild)

| Piece | Where | Status |
|---|---|---|
| Server-side Brevo API key | `config.py:145` `brevo_api_key`, set per environment | **P1/P4 already satisfied** — the key is live and used today |
| Transactional email | [services/brevo_email.py](platform/services/brevo_email.py) | verify / reset / invite templates |
| Four lifecycle lists + per-contact sync | [services/brevo_contacts.py](platform/services/brevo_contacts.py) | fail-open, fire-and-forget, per-contact `asyncio.Lock`, `_schedule()` task-retention |
| Nightly reconcile cron | [services/brevo_reconcile.py](platform/services/brevo_reconcile.py) + `render.yaml` `brevo-lifecycle-reconcile` (07:40 UTC) | the safety net that makes fire-and-forget safe |
| Lifecycle hook tests | `tests/test_brevo_lifecycle_hooks.py` | patches the sync `dispatch_*` seam — reuse this convention |

The new work **reuses** `_schedule()`, `_contact_lock()`, `_headers()`,
`_error_code()` and `_format_date()` from `brevo_contacts.py` rather than
duplicating them.

---

## 2. Findings to report back to Ron

These are the parts of the work order that don't survive contact with the code.

1. **W4's open question — answered: yes, document generation is a single
   reliable code path, and it is the *only* honest signal available.**
   `POST /estimates/{id}/generate-doc` is the sole caller of
   `append_doc_version_to_estimate`, so the hook is unambiguous.

   Ron should also know why this is a proxy and not the real thing: **the app
   does not transmit anything to a client.** It produces a Google Doc; the user
   emails or hands it over themselves, outside the product. There *is* a
   `Draft/Review → Sent` status transition
   ([routers/estimates.py:969](platform/routers/estimates.py:969), mirrored for Maple at
   [agents/estimate/crud_handlers.py:2604](platform/agents/estimate/crud_handlers.py:2604)) — but
   it is manual bookkeeping the user may or may not keep up to date, not
   evidence of a send. Generating the customer document is the last thing the
   product actually observes, so it is the better proxy of the two. We treat
   "document generated" as "about to be handed to the customer", which is
   exactly Ron's framing.

   The consequence for Cliff 3's copy: it should not say "you haven't sent it
   yet" — we can't know that. It can only say "you built an estimate and
   haven't produced the customer document". Ron's own caution applies here —
   nagging someone about a quote they already handed over is worse than sending
   nothing.

2. **Brevo-side attributes must exist before the first push — this is a missing
   precondition.** Brevo rejects unknown attribute names on contact upsert. P1–P5
   don't mention creating them. See §3.

3. **W3's condition "the contact has `ACTIVATED: false`" cannot be evaluated the
   way it's written.** Reading contact state back from Brevo on the request path
   violates G1 (a Brevo outage would slow a user action). We guard from our own
   database instead — stricter, faster, and auditable. Same net behavior.

4. **"Account" is per-email, but the tenant is per-Company.** Estimates belong to
   a Company; Brevo contacts to a person. Activation is therefore recorded
   per-user. A teammate who never personally builds an estimate never registers
   as activated even if their company is highly active. This is the right call
   for *email* purposes; it means `FIRST_ESTIMATE_AT` is a **per-person**
   north star, not a per-account one. Ron should know that before it becomes a
   board metric.

5. **`users.email` has no index.** `models/user.py` declares only
   `class Settings: name = "users"`. Every lookup by email — including the new
   guard — is a collection scan. Add a non-unique index in this change.

6. **`estimate_draft_started` fires when the user opens the New Estimate page**,
   not when they type. [portal/src/pages/NewEstimateWithActivityPage.tsx:288](portal/src/pages/NewEstimateWithActivityPage.tsx:288)
   auto-creates a blank Draft on mount. That is an excellent abandoned-draft
   hook, but Cliff 2's copy should read as "you opened the builder", not "you
   started writing an estimate".

7. **G1 says "one retry"; the house pattern is fire-and-forget + nightly
   reconcile.** We do both: one retry inline, plus reconcile re-attempts events
   whose delivery definitively failed.

---

## 3. Brevo-side setup (Verdeck / Ron — blocking, ~15 min)

I can't reach Brevo from here (no connector, no credentials), so this part is a
handover, not something I can execute. What I *can* do is ship a small script
that creates the attributes idempotently via the API — see §6, Phase 0.

**Contact attributes to create** (Brevo → Contacts → Settings → Contact attributes),
or via `POST /v3/contacts/attributes/normal/{NAME}`:

| Attribute | Type | Set by |
|---|---|---|
| `ACCOUNT_CREATED_AT` | Date | W1 |
| `EMAIL_VERIFIED` | Boolean | signup (false) → verification (true) |
| `ACTIVATED` | Boolean | W1 sets false, W3 sets true |
| `ESTIMATE_STARTED_AT` | Date | W2 |
| `FIRST_ESTIMATE_AT` | Date | W3 |
| `DOCUMENT_GENERATED_AT` | Date | W4 |
| `JOINED_EXISTING_TEAM` | Boolean | signup, when a pending invitation matches |

Do **not** reuse `SUBMITTED_AT` — it is already shared between the website
contact form and the app's last-login push, documented at
[services/brevo_contacts.py:227](platform/services/brevo_contacts.py:227).

**Events Ron will see as real-time entry points:** `account_created`,
`email_verified`, `estimate_draft_started`, `first_estimate_built`,
`first_document_generated`.

**Automation wiring.** Simon builds these, not Ron. The Cliff sequences do
**not** exist in the account — nothing to re-point, they are built from nothing.

**Copy is Ron's `Brevo Email Copy Deck` (Aug 20), and it is canonical.** Nine
templates, frozen, paste verbatim; copy changes route through Ron. The earlier
seven-email draft in this repo's history is superseded — do not use it. Ron's
deck also supersedes Section C of his own Aug 11 `Brevo Build: Simon Edition`
handoff, which we do not hold a copy of (it carries the sender table and the
Section E acceptance tests — get it before building).

| Automation | Entry event | Templates | Delays | Check before each send |
|---|---|---|---|---|
| AUTO-1a — welcome | `account_created` | T0 | immediate | none (unconditional) |
| AUTO-1b — nudges | `email_verified` | T1.1, T1.2, T1.3 | +1d, +3d, +6d **from verification** | `ACTIVATED` not true; end if `JOINED_EXISTING_TEAM` |
| AUTO-2 | `estimate_draft_started` | T2.1, T2.2 | +2h, +1d | `ACTIVATED` is not true |
| AUTO-3 | `first_estimate_built` | T3.1, T3.2 | +1d, +3d | `DOCUMENT_GENERATED_AT` is empty |
| Habit | `first_document_generated` | T3.3 | +7d | — |

**AUTO-1 is split in two — decided 2026-08-20, see §3.1 item 2.** T0 is
unconditional and immediate on the transactional stream; the three nudges wait
for verification, because an unverified user gets a **403 from `POST /estimates`**
([firebase_auth.py:137](platform/firebase_auth.py:137)) and cannot do the thing T1.1–T1.3 ask
for. Ron's check-before-each-send structure is otherwise kept exactly — attributes
are the durable state, which is why each moment writes an event *and* an
attribute. His §6 makes the same argument from the copy side: the IF conditions
are the honesty mechanism, not an optimization.

**W4 is ruled: ship it.** Ron gated T3.1/T3.2/T3.3 and all of AUTO-3 on this,
and listed a replacement email (his open item 5) against the possibility it
died. It doesn't die. Document generation is a single reliable code path and the
only signal the product actually observes — see finding 1. Ron can close his
open items 1 and 5, unblock three templates, and drop the nag-only coverage hole
he flagged.

**`email_verified` has no copy, by design.** Ron's matrix covers the four events
in the work order; we ship five. The fifth is a gate, not a send. See §3.1 for
the decision it forces.

**Ordering trap:** Brevo lists an event name as a selectable entry point only
once it has *received* one. The backfill fires nothing, so it won't populate the
picker — run one test account end to end first, then build.

### 3.1 Reconciling Ron's deck with what shipped

Four places where the deck and the code disagree. None is fatal; two need a
decision before anything is activated.

**1. Sender — RESOLVED (2026-08-20).** Ron's split stands, on two addresses:

| | Sender | Address |
|---|---|---|
| T0 | Brad | `brad@3maples.ai` |
| T1.1 – T3.3 | Maple | `support@3maples.ai` |

Two registered sender records, no From-name override needed. T0's copy stays
honest (*"this is the only email you'll get from me, the rest come from Maple
itself"*), replies to T0 reach Brad directly, and the eight Maple sends keep
landing in the monitored support inbox — which is what makes the P4 reply lines
answerable (§3.3).

**New dependency: `brad@3maples.ai` must be a receivable mailbox.** Brevo
validates a new sender address by emailing it; someone has to open that and
click through. A forwarding alias is fine, a non-existent mailbox blocks T0. No
DNS work either way — domain authentication on `3maples.ai` is already live per
P3 (Brevo TXT, both DKIM CNAMEs, DMARC at quarantine), so the new address
inherits it.

**The app's transactional sender is unaffected, despite sharing an address with
Maple.** `.env.production` sets `BREVO_SENDER_EMAIL=support@3maples.ai` with
`BREVO_SENDER_NAME=3Maples.ai`, so "3Maples.ai" and "Maple" are two display names
on one address — but they travel different paths.
[services/brevo_email.py](platform/services/brevo_email.py) passes `sender: {email, name}` inline
on every `/v3/smtp/email` call, while automations pick from the registered
sender list. The inline name wins per send; that is already observable today in
any verification email. Registering **Maple &lt;support@3maples.ai&gt;** for the
automations does not rename what the app sends — and if Brevo keys sender
records on email, renaming that record to "Maple" *is* how you register the
automation sender.

**Do not set `BREVO_SENDER_NAME=Maple` to match.** It governs five app-sent
emails and Maple is wrong for most of them: password reset and verification want
the brand, not a persona (auth mail from a persona is weaker against phishing),
and the support-reply notification's own body reads *"Our support team replied
to your message"* — a persona announcing a human team is the failure mode Ron's
§6 exists to prevent. Brand name on system mail, persona on lifecycle mail is
the convention, not a compromise.

So a new user sees three display names across two addresses in their first day:
the verification email as *3Maples.ai*, T0 as *Brad*, T1.1 as *Maple*. That's
fine — nobody reads "verify your email" as coming from a person — but it does
mean T0's claim is about the lifecycle stream only. Don't reconcile it later by
renaming the transactional sender.

No code change anywhere: the nine are Brevo automation sends.

**2. Verification gating — RESOLVED (2026-08-20): split AUTO-1 in two.**
Ron's deck enters the whole of Cliff 1 on `account_created`, which fires at
signup, before verification. That is not a matter of taste: an unverified user
gets a **403 from `POST /estimates`** ([firebase_auth.py:137](platform/firebase_auth.py:137)),
so T1.1–T1.3 would be nudging someone to do a thing the API refuses them.

The obvious single-automation fix — keep Ron's entry, add `EMAIL_VERIFIED is
true` to T1.1/T1.2/T1.3 — was considered and rejected. It silently skips any
send whose moment passed while the user was unverified, so someone who verifies
on day 4 has T1.1 and T1.2 dropped and meets Maple for the first time through
T1.3, *"Should I stop?"*.

So: **AUTO-1a** carries T0 alone on `account_created` (immediate, unconditional),
and **AUTO-1b** carries T1.1/T1.2/T1.3 on `email_verified` with the +1d/+3d/+6d
delays measured from verification. Everyone gets the full arc in order whenever
they verify; a never-verifier gets the welcome and nothing else.

For anyone who verifies promptly — nearly everyone — all three designs behave
identically. This only changes the tails.

*One line for Ron:* T1.3 opens *"You signed up six days ago"*, now measured from
verification rather than signup. Identical for prompt verifiers, wrong for the
late tail. His copy, his call — not worth blocking on.

**3. `JOINED_EXISTING_TEAM` — and the split makes this load-bearing.** The guard
isn't in Ron's deck, and it now matters more than it did. The backend suppresses
the `account_created` *event* for a signup matching a live invitation, so
AUTO-1a already skips invited joiners for free. But `email_verified` is **not**
suppressed — it fires for everyone — so **AUTO-1b would nudge invited teammates
unless the attribute guard is on it.** Without it a new hire at an established
customer gets T1.3's *"you signed up six days ago and I haven't written a single
estimate for you"* six days into a job at a company that has been estimating for
months. Put `end if JOINED_EXISTING_TEAM is true` on AUTO-1b. No copy change, no
code change — deliberately a Brevo-side condition so it stays reversible without
a deploy.

**4. T2.1/T2.2 claim content that may not exist — flag to Ron.**
`estimate_draft_started` fires when the user *opens* the estimate builder: the
portal auto-creates a blank draft on mount
([NewEstimateWithActivityPage.tsx:288](portal/src/pages/NewEstimateWithActivityPage.tsx:288)),
before anything is typed. Ron's copy assumes otherwise — *"I saved your estimate
right where you left it"*, *"You're not starting over"*, *"That estimate you
started is still half-built"*. For someone who opened the builder and bounced,
none of that is true, and by the standard Ron sets in his own §6 that is Maple
being wrong about something it claimed to know.

**Resolved 2026-08-20: T2.1 and T2.2 rewritten around "opened", in-house.**
Simon took the call rather than waiting on Ron; both are drafted, reviewed and
folded into the build doc. The alternative — firing the event on first *content*
save so Ron's copy became true verbatim — was rejected because it guts the
sequence's reach: open-and-bounce is both the largest slice of this cohort and
the one most worth catching, and that fix would send them nothing at all.

The rewrite constraint was that each line read true **whether or not anything was
typed**, since the event fires on open and the `ACTIVATED` gate only proves the
estimate wasn't finished. Three things moved in each: the claim about a saved
part-written draft, the button label (Ron's *"Finish where I left off"* assumed
content *and* pointed at a builder the link doesn't reach), and T2.1's preview.
Ron's P4 paragraph in T2.2 is untouched.

AUTO-2's structure, timing and conditions are unaffected — only words changed.
**Ron still needs telling that two of his nine moved**, since the frozen-copy
rule and the C-checklist are his.

### 3.2 Button URLs (Ron's open item 4 — answered)

Portal is `https://app.3maples.ai`. Per the CTA decision above, no per-user deep
links; Ron's own fallback rule applies — *a working generic link beats a broken
personalized one*.

| Placeholder | Value | Templates |
|---|---|---|
| `{{BUILD_URL}}` | `https://app.3maples.ai/estimates` | T0, T1.1, T1.2, T1.3, T3.3 |
| `{{DRAFT_URL}}` | `https://app.3maples.ai/estimates` | T2.1, T2.2 |
| `{{ESTIMATE_URL}}` | `https://app.3maples.ai/estimates` | T3.1, T3.2 |

**Do not point `{{BUILD_URL}}` at `/estimates/new-with-activity`,** even though
it looks like the better deep link. That route auto-creates a blank draft on
mount, and `create_estimate` claims a billable quota slot *before* the
skip-generation branch ([routers/estimates.py:302](platform/routers/estimates.py:302)) — so every
click burns one of the Free plan's 20 estimates
([models/company.py:20](platform/models/company.py:20)) and posts a Stripe meter event. A user
clicking through all four AUTO-1 emails would spend a fifth of their allowance
on empty drafts. It would also fire `estimate_draft_started` from an email
click, dropping them into AUTO-2 and producing T2.1's "I saved your estimate" two
hours later about a draft they never touched.

**Also note for the deck's `{{ESTIMATE_URL}}` button label.** T3.1's button reads
*"Send it to my customer →"*. The app has no send — it generates a Google Doc the
user hands over themselves. The button lands them on the estimates list, from
where the real action is the **New Version** button in the **Documents** row.
T3.2's body handles this correctly (*"Getting it in front of the customer is your
half"*); T3.1's button label doesn't. Ron's call, flagged rather than edited.

### 3.3 The P4 lines — probably satisfiable

Ron's open item 2 needs a named human answering the Maple inbox before T1.2,
T2.2 and T3.2 can keep their reply invitations. Worth telling him: replies to
`support@3maples.ai` already land in a monitored flow — the in-app support system
routes to Slack ([services/support_notifications.py](platform/services/support_notifications.py),
[services/slack_support.py](platform/services/slack_support.py)). The inbox exists and is
watched; what Ron still needs is someone who owns *answering in Maple's voice
within one business day*. That's a staffing answer, not a plumbing one.

**`Onboarding — New Signups` list (P5):** optional, per Ron's own note. If he
sends a numeric list ID we set `BREVO_ONBOARDING_LIST_ID` per environment (DEV
and PROD are separate lists in the same account, same as the existing four). If
unset, W1 drops the `listIds` line and everything else works identically.

---

## 4. Backend design

### 4.1 New module — `platform/services/brevo_lifecycle.py`

Sibling to `brevo_contacts.py`, same conventions (fail-open, never logs a
response body, only the parsed `code`).

```python
class LifecycleEvent(str, Enum):
    ACCOUNT_CREATED = "account_created"
    EMAIL_VERIFIED = "email_verified"
    ESTIMATE_DRAFT_STARTED = "estimate_draft_started"
    FIRST_ESTIMATE_BUILT = "first_estimate_built"
    FIRST_DOCUMENT_GENERATED = "first_document_generated"
```

Public surface:

- `is_configured()` → `bool(settings.brevo_api_key) and settings.brevo_lifecycle_events_enabled`.
  Deliberately **independent of the four list IDs** — events must work even if a
  deployment has no lists configured.
- `async def emit(user, event, *, attributes=None, list_ids=None, fire_event=True)`
- `def dispatch(...)` — fire-and-forget wrapper over `emit`, reusing
  `brevo_contacts._schedule`.

`emit()` sequence:

1. **Atomic once-ever claim.**
   `User.get_pymongo_collection().find_one_and_update({"_id": uid, "brevo_events_sent": {"$ne": event}}, {"$addToSet": {"brevo_events_sent": event}})`.
   `None` back → another request already claimed it → return. This is G3, and it
   is race-proof in a way a read-then-write check is not.
2. `POST https://api.brevo.com/v3/events` with
   `{"event_name": ..., "identifiers": {"email_id": <lowercased email>}}` (G2, G5).
   Skipped when `fire_event=False` (the invited-joiner and backfill paths).
3. `POST https://api.brevo.com/v3/contacts` with `updateEnabled: true` and the
   attribute payload (+ `listIds` when configured), **inside
   `brevo_contacts._contact_lock(email)`** so it can't interleave with a
   concurrent list-stage sync on the same contact.
4. **One retry** on connect/read error, 429, or 5xx (G1). A 4xx is not retried.
5. On definitive failure, `$pull` the claim so the nightly reconcile can retry.
   Log `(event, status, code)` only — never the body, never `logger.exception`
   (Sentry attaches frame locals holding the email).

Attribute values use `brevo_contacts._format_date` (G4, `YYYY-MM-DD`).

An in-process bounded cache (`email → frozenset of confirmed-sent events`) keeps
the steady state at **zero database round-trips** for the high-frequency estimate
hook; Mongo remains the authority, the cache only skips work already known done.

### 4.2 Model changes

**`platform/models/user.py`**
```python
# Once-ever guard for Brevo lifecycle events (services/brevo_lifecycle.py).
# Membership means "claimed"; a delivery failure pulls the entry back out so
# the nightly reconcile can retry. Never re-fired on a second occurrence.
brevo_events_sent: List[str] = Field(default_factory=list)
```
and, per finding 5:
```python
class Settings:
    name = "users"
    indexes = [IndexModel([("email", ASCENDING)])]
```
Non-unique deliberately — a unique index would fail the migration if any
duplicate rows exist; tightening it is a separate, checked change.

**`platform/models/estimate.py`** — one new hook on `Estimate`:
```python
@after_event([Insert, Replace, Save, SaveChanges, Update])
async def _note_brevo_lifecycle(self):
    from services.brevo_lifecycle import note_estimate_write
    note_estimate_write(self)   # sync, never raises, never awaits I/O
```
Beanie 2.0 routes `.set()` and `.save()` through `Document.update()`
(`@wrap_with_actions(EventTypes.UPDATE)`), and the instance is synced to the
post-update state — verified against the installed version. The wide event list
is belt-and-braces; the atomic claim makes double-firing free.

**Why a model hook rather than explicit call sites:** estimates are written from
six files — `routers/estimates.py`, `routers/estimate_helpers/doc_versions.py`,
`routers/agent_helpers/estimate_update.py`, `agents/estimate/crud_handlers.py`,
`agents/estimate/work_item_handlers.py`, `agents/estimate/work_item_field_handlers.py`.
Hooking each is where a missed path becomes a silently-never-activated user.
This does depart from the "whoever owns the request dispatches once" rule
documented at [services/user_verification.py:86](platform/services/user_verification.py:86) — that rule
exists to stop two *stage syncs* racing to a different answer; lifecycle events
are single-valued and claim-guarded, so the hazard doesn't apply.

`note_estimate_write(estimate)` is pure and cheap:

| Predicate on the persisted document | Event |
|---|---|
| the document exists | `estimate_draft_started` |
| `grand_total > 0` (or ≥1 job item with a priced line) | `first_estimate_built` |
| `google_docs_versions` non-empty | `first_document_generated` |

Actor = `estimate.created_by_email`. **Gap to fix in the same change:**
[agents/estimate/crud_handlers.py:660](platform/agents/estimate/crud_handlers.py:660) creates a
template-based estimate without setting `created_by_email` — set it from
`context["current_user_email"]`, which the orchestrate endpoint already carries.

### 4.3 Hook sites

| # | Event | File | Placement |
|---|---|---|---|
| 1 | `account_created` | [routers/auth.py:510](platform/routers/auth.py:510) | beside the existing `dispatch_user_stage_sync(..., UNVERIFIED)`. First check `Invitation.find_one(email == request_email, status == PENDING)`; if found → `fire_event=False` and `JOINED_EXISTING_TEAM: true` |
| 2 | `email_verified` | [routers/auth.py:446](platform/routers/auth.py:446) (`POST /auth`) and [routers/auth.py:932](platform/routers/auth.py:932) (invitation accept) | on the `just_verified` edge only — the flag both call sites already compute |
| 3–5 | estimate events | `models/estimate.py` after-event hook | as §4.2 |

All five go through `dispatch(...)`, so no request path ever awaits Brevo.

### 4.4 Config — `platform/config.py`

```python
brevo_onboarding_list_id: int | None = None       # P5, optional
brevo_lifecycle_events_enabled: bool = True       # kill switch (acceptance test 6)
brevo_lifecycle_reconcile_enabled: bool = False   # see §4.5 — OFF until backfilled
```
Documented in `.env.example`. No `render.yaml` change is needed for the web
service; the reconcile cron already inherits `BREVO_API_KEY`.

### 4.5 Reconcile + backfill

**`services/brevo_lifecycle_reconcile.py`** — a sibling module rather than an
extension of `brevo_reconcile.py` (the two channels are configured
independently, and folding them together would couple the events pass to the
four list IDs). The nightly cron script runs both, and runs the events pass even
when the list pass is skipped for want of list IDs.

The pass is one rule: **for each user, emit every event whose line has been
crossed but whose claim is missing.** Crossed-ness comes from `User.created_at`
(always), `email_verified is True`, and one aggregate over `estimates` grouped
by lowercased `created_by_email`. Attributes ride along with each emit rather
than being pushed separately, so a steady-state night costs zero Brevo writes.

**Two guards, and both are load-bearing.** On its first run in an environment,
every pre-existing user is indistinguishable from a user whose events all
failed — an unguarded pass would drop the entire customer base into Cliff 1.

1. `brevo_lifecycle_reconcile_enabled` defaults to **False**. Turning the events
   channel on does not, by itself, arm the sweep.
2. **`scripts/backfill_brevo_lifecycle.py`** (dry-run by default) claims the
   lines each existing user has already crossed and writes their attributes,
   firing nothing. Run once per environment, *then* arm the sweep.

The backfill deliberately does **not** claim all five events for everyone. That
would be simpler and would permanently suppress activation for every existing
customer who hasn't built an estimate yet — the north-star metric wrong forever,
silently. Only lines already behind a user are claimed.

One documented approximation: the backfill decides "has built an estimate" from
`grand_total > 0`, where the live hook also counts priced job items on a
document with a stale cached total. The gap is theoretical (every write path
recomputes the total) and costs at most a delayed activation, which the next
estimate write corrects.

---

## 5. What this does *not* do

- No `first_estimate_sent` event. The `Sent` status is manual bookkeeping, not a
  transmission, so it would be a weaker signal than the one we already have. If
  the app ever gains real sending, that becomes the hook and this is one
  predicate + one enum member — the estimate hook already sees `status`.
- No Brevo automation building — that is Ron's, and needs P2.
- No change to the four existing lifecycle lists or their sync, per the work
  order's own note.
- No portal/frontend change. Every signal is already observable server-side.

---

## 6. What shipped

| Piece | File |
|---|---|
| Event service (claim, retry, attributes, estimate predicates) | `platform/services/brevo_lifecycle.py` |
| Nightly re-emit sweep + one-off backfill | `platform/services/brevo_lifecycle_reconcile.py` |
| Once-ever guard + `users.email` index | `platform/models/user.py` |
| Single estimate-write hook | `platform/models/estimate.py` (`note_brevo_lifecycle`) |
| `account_created` (with invited-joiner carve-out) + `email_verified` ×2 | `platform/routers/auth.py` |
| `created_by_email` on Maple's template path | `platform/agents/estimate/crud_handlers.py` |
| Attribute bootstrap (run once per Brevo **account**) | `platform/scripts/create_brevo_attributes.py` |
| State backfill (run once per **environment**) | `platform/scripts/backfill_brevo_lifecycle.py` |
| Events pass wired into the existing nightly cron | `platform/scripts/reconcile_brevo_contacts.py` |

**Tests** (151 across the Brevo suites, all green):
`test_brevo_lifecycle.py` (wire layer + the claim against the real database),
`test_brevo_estimate_hook.py` (every Beanie write style reaches the hook; the
state predicates), `test_brevo_estimate_lifecycle_api.py` (the real HTTP routes
produce documents attributable to the acting user),
`test_brevo_lifecycle_hooks.py` (signup / invited-joiner / verification),
`test_brevo_lifecycle_reconcile.py` (what the sweep retries, and the two guards
that stop it mailing the whole base).

Two things worth knowing for the next person in here:

- **The suite must never reach Brevo.** `_disable_brevo_lifecycle_events` in
  `conftest.py` is a session-wide kill switch, because the events channel needs
  only an API key — which `.env.local` carries. A test that turns it on must
  patch `services.brevo_lifecycle.emit` at the *source* module, not just on an
  importer; patching only the importer let a real 401 out of the test suite once.
- **Signup's dispatch is fire-and-forget**, so a test that asserts on what a
  later sweep found has to drain the shared `brevo_contacts._bg_tasks` first, or
  it races.

---

## 7. Verification

```bash
cd platform && ./run_tests.sh tests/test_brevo_lifecycle.py tests/test_brevo_estimate_hook.py tests/test_brevo_estimate_lifecycle_api.py tests/test_brevo_lifecycle_reconcile.py tests/test_brevo_lifecycle_hooks.py tests/test_brevo_contacts.py tests/test_brevo_reconcile.py tests/test_brevo_stage_derivation.py tests/test_reconcile_brevo_contacts.py
```
```bash
cd platform && ./run_mypy.sh && ./run_ruff.sh && ./run_bandit.sh
```

Then, against the DEV Brevo account — **`create_brevo_attributes.py --apply`
first**, then `BREVO_LIFECYCLE_EVENTS_ENABLED=true` — walk Ron's acceptance
table end to end:

1. Sign up a fresh test account → contact shows `ACCOUNT_CREATED_AT`,
   `ACTIVATED false`, `EMAIL_VERIFIED false`; `account_created` in Brevo's event log.
2. Verify the email → `email_verified` fires, `EMAIL_VERIFIED` flips true.
3. Open `/estimates/new-with-activity`, abandon it → `estimate_draft_started`
   once, `ESTIMATE_STARTED_AT` set.
4. Fill in and save line items → `first_estimate_built`, `ACTIVATED true`,
   `FIRST_ESTIMATE_AT` set.
5. Create a second estimate → **no** second `first_estimate_built`.
6. Generate the customer document → `first_document_generated` once.
7. Set `BREVO_API_KEY` to garbage → signup and estimate flows still complete
   normally; only warnings in the log (acceptance test 6).
8. Ron confirms all five event names appear as real-time entry points in the
   automation editor (acceptance test 7).

Finally, the one-off sequence per environment:

```bash
cd platform && python scripts/backfill_brevo_lifecycle.py
```
Eyeball the tally against the ops Users count, then re-run with `--apply`, and
only then set `BREVO_LIFECYCLE_RECONCILE_ENABLED=true`. Doing it in the other
order mails the entire customer base.

---

## 8. Open items

Ron's copy deck closes with its own blocker list. Mapped against where things
actually stand:

| Ron's item | Owner | Status |
|---|---|---|
| 1. W4 ruling — is document generation a reliable "sent" proxy? | Simon | **Answered: yes, ship it.** Unblocks T3.1, T3.2, T3.3, AUTO-3 |
| 2. Name the Maple inbox operator, or strip the P4 lines | Ron / Brad | **Open.** Inbox is already monitored — §3.3; what's missing is who answers as Maple |
| 3. Confirm Brad's sender address | Brad | **Answered:** T0 as Brad `<brad@3maples.ai>`, the rest as Maple `<support@3maples.ai>` — §3.1 item 1. Brad still has to click Brevo's sender-validation email |
| 4. Real button URLs | Simon | **Answered** — §3.2 |
| 5. Replacement post-activation email if W4 dies | Ron | **Moot.** W4 lives |

Still ours, and none of it blocked on Ron:

- **Get the Aug 11 `Brevo Build: Simon Edition` handoff.** We don't hold it. It
  carries the Section B sender table (which item 3 turns on) and the Section E
  acceptance tests that R10 gates every template on.
- **All four §3.1 items are resolved and all nine templates are pasteable.**
  Nothing is blocked on Ron any more, but three things are owed to him as
  notifications: the T2.1/T2.2 rewrite, T1.1's *"you made an account
  yesterday"* and T1.3's *"six days ago"* (both now counted from verification,
  not signup), and T3.1's *"Send it to my customer"* button on an app that has
  no send.
- **Run the DEV sequence.** `--verify`, backfill dry run, `--apply`, then one
  test account end to end. That walkthrough is what makes the five event names
  appear in Brevo's entry-point picker, so **no automation can be built until it
  has run.** This is the next action.
- **Flag §3.1 item 4 to Ron** — T2.1/T2.2 claim a draft has content when the
  event only proves the builder was opened. His §6 rule, his call.
- **P5** — Ron's numeric `Onboarding — New Signups` list ID, per environment.
  Not blocking; W1 works without it.
- **P2** — Ron needs a Brevo user account if he is to touch any of this himself.
- Attribute creation (§3) must land **before** the first push, or every contact
  upsert 4xx's. `scripts/create_brevo_attributes.py --verify` confirms it.
- Nothing in this change is committed yet.
