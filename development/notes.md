# Engineering Notes

Running log of non-obvious decisions and behaviors worth remembering — the kind
of context that isn't self-evident from the code. Append a dated entry per note.

---

## 2026-06-21 — Default template seeding is gated on both standard catalogs

Default estimate templates (`platform/data/default_templates.json`, seeded via
`platform/services/template_bootstrap.py::bootstrap_company_templates`) are wired
into new-company creation through
`platform/services/company_service.py::create_company_with_bootstrap`, which the
live signup endpoint `POST /auth/company-onboarding`
(`platform/routers/auth.py`) calls.

The template step runs **last** and only when **both**
`include_standard_materials` **and** `include_standard_labour_roles` are True.
Both flags default to **False** on `CompanyOnboardingRequest` (auth.py ~271-272),
so a company gets default templates only if onboarding opts into both standard
catalogs. Skip either → no templates seeded (this is intended, not a bug).

**Why:** templates resolve their material/role line items by *name* against the
company's own freshly-seeded catalog; without both catalogs present every item
would fall into `unmatched_*`, so seeding them would just create noise.

**Decision:** keep it gated on both flags — confirmed intentional. If product
later wants every company to get templates regardless, the alternatives are:
always seed (accept `unmatched_*`), or gate on a partial catalog.

---

## 2026-07-03 — Operations UI: StaffUser as a separate collection, not a role extension

Shipped the internal Operations dashboard (staff-only back office: company list,
user list, "new users" funnel, staff management). The core design decision was
**where staff accounts live**, and the answer is a dedicated `staff_users`
Beanie collection (`platform/models/staff_user.py`), deliberately isolated from
the customer `users` collection.

**Alternatives considered:**
- **Extend `UserRole` on the existing `User` model** (add `staff`/`ops_admin`
  style values alongside the current tenant roles). Rejected — `User` is
  structurally company-scoped (every document carries a `company` reference,
  and most CRUD queries filter or assert on it). Roughly **9 routers**
  (`contacts.py`, `billing.py`, `equipments.py`, `material_categories.py`,
  `materials.py`, `estimates.py`, `properties.py`, `labours.py`,
  `divisions.py`, `templates.py`, `rate_cards.py`, `audit_logs.py`,
  `material_units.py`, `companies.py` — company-scoping shows up across more
  than 9 call sites) do explicit `company_id ==` / `assert_company_access`
  checks. Adding a company-less user variant into that model would have meant
  auditing and special-casing every one of those sites to handle a `User` with
  no `company`, for a real regression risk on tenant isolation — the exact
  thing those checks exist to guarantee.
- **`user_type` discriminator field on `User`** (customer vs. staff, single
  collection). Rejected for the same reason as above, plus it blurs a
  collection whose entire purpose is "belongs to a company" with accounts that
  by definition don't.
- **Separate `StaffUser` collection (chosen).** Zero regression surface on the
  company-scoped call sites above — staff accounts simply never appear in any
  `User` query. Trade-off: a few things are duplicated (a second auth check in
  `POST /auth` via `resolve_active_staff`, a second Firebase-backed
  provisioning path), but that duplication is small, explicit, and isolated to
  `dependencies.py` / `services/staff_service.py` / `routers/ops.py`.

**Role names** (`StaffRole` enum in `models/staff_user.py`): `root`,
`ops_admin`, `ops_viewer`. **Naming is provisional** — cheap to rename while
only one staff user (root) exists; the enum values, not just labels, would
need a migration once a second staff user is provisioned, so any rename should
happen soon if at all.

**Root bootstrap procedure** — there is no UI path to create the first root
(by design: `POST /ops/staff` is root-only, so someone has to exist first).
Run once, from `platform/`, venv active, `.env.local` pointed at the target
cluster:

```bash
python scripts/create_root_user.py simon@tangz.com Simon <LastName>
```

`scripts/create_root_user.py` refuses to run if a `root` `StaffUser` already
exists (`StaffUser.find_one(StaffUser.staff_role == StaffRole.ROOT)`), creates
the Firebase account pre-verified, and sends a password-reset email to set the
password — same provisioning path (`services/staff_service.py::provision_staff_user`)
as `POST /ops/staff` uses for subsequent staff.

**New Users stage definitions** (`GET /ops/new-users`, `routers/ops.py`) —
staff-visible funnel over customers who haven't finished onboarding.
Candidates are users with no company or whose company has
`onboarding_completed == False`; email-verification status comes from Firebase
via `services/ops_verification.py` (fails open to `"unknown"` on lookup
failure — an ops dashboard on a Firebase hiccup should degrade to
"can't tell," not crash). Each candidate is bucketed into exactly one stage:

- `unverified` — Firebase reports `email_verified == False`.
- `no_company` — verified (or unknown), but `user.company is None`.
- `onboarding_incomplete` — has a company, but that company's
  `onboarding_completed` is still `False`.

## 2026-07-26 — Estimate generation performance: why it got slower + what we instrumented

**Why generation feels slower since mid-July.** Three platform commits (07-15/16)
upgraded the agents to gpt-5.6 (`0cc8cfd`) and then fixed the API modes
(`ae95e08`, `2d5e199`). Before the fix, the architect call (function tools on
chat completions with a reasoning model) and the researcher call (temperature
on a raw Responses call) **silently errored** — architect degraded to a
single-scope wrapper, research returned empty deliverables. Generation was
fast because it was *broken*: no scope fan-out, no web research, no reasoning
tokens. Since 07-16 the pipeline genuinely runs — N research calls (one per
scope) on gpt-5.6-terra with real web search — so the slowdown is largely the
pipeline doing the work it was always supposed to do. The failure was invisible
because every step degrades silently (that's now flagged — see below).

**What one generation costs (LLM round-trips).** Orchestrator classify →
`assess_sufficiency` (worker) → architect (terra, reasoning) → per-scope
embedding + researcher (terra + web_search, parallel across scopes, capped by
`openai_max_concurrency_per_company=3`) → accuracy suggestions (worker, on the
response path). Wall clock is dominated by the architect + researcher
reasoning calls.

**Instrumentation added (`services/timing.py`).** Every generation now logs a
single INFO line, e.g.:

```
estimate_generation timings total=48.21s company_defaults=0.11s inventory_fetch=0.42s architect=12.30s vector_research=28.10s build_estimate=0.15s suggestions=6.50s
```

plus degradation flags (`architect_fallback`, `research_empty`,
`extraction_fallback`, `suggestions_fallback`) — a silently-degraded step is
now visible in the logs instead of masquerading as a fast success.
`assess_sufficiency` logs its own duration line (it runs before the
generation scope starts).

**Cheap wins shipped in the same change:**
- **Accuracy suggestions are time-boxed** (`estimate_suggestions_timeout`,
  default 10s). They sit on the response critical path with a full rule-based
  fallback; the SDK worst case (90s timeout × 3 attempts ≈ 270s) could hold a
  *finished* estimate hostage. Now they fall back after 10s.
- **Inventory + company reads parallelized** (materials ∥ labour ∥ company
  doc — were 3 sequential Mongo round-trips against the cross-region Dev
  cluster).
- **The assumption-first flow removes 1–3 whole gathering round-trips** per
  estimate (each was an LLM call + a user wait). The duplicate
  `assess_sufficiency` call in `_maybe_skip_area_question` is gone entirely.
  This is the biggest *perceived* latency win: users get an estimate on the
  first message instead of answering 2–3 questions first.

**Shipped with Simon's approval (2026-07-26, same day):**
- **Researcher latency knobs**: both raw researcher calls now use
  `search_context_size` from `settings.researcher_search_context_size`
  (default **"low"**, was hardcoded "medium") and pin
  `reasoning={"effort": settings.researcher_reasoning_effort}` (default
  **"low"**) — the researcher stays on gpt-5.6-terra with web search, but
  stops spending long reasoning chains on pricing lookups. Both are
  env-overridable (`RESEARCHER_SEARCH_CONTEXT_SIZE`,
  `RESEARCHER_REASONING_EFFORT`) to revert without a deploy. The `reasoning`
  parameter is omitted automatically for non-gpt-5 researcher overrides
  (`_is_gpt5_reasoning_family` guard — non-reasoning models reject it).
- **`openai_max_concurrency_per_company` 3 → 8**: a 3-scope generation's
  embedding+research fan-out (6 slots) now runs in one wave instead of two.
  The global cap (24) still bounds the org rate limit.

**Measured (2026-07-26, Dev cluster + live OpenAI, single runs — treat as
directional):** two scenarios via `EstimateAgent.process` against the
Dev One company (151 materials).

| Scenario | Before (medium ctx/reasoning, cap 3) | After (low/low, cap 8) | Δ |
|---|---|---|---|
| Lawn, 1 scope | 15.7s (research 10.8s) | 15.1s (research 9.7s) | ~flat |
| Patio+lighting, 2 scopes | **42.3s** (research 35.7s) | **27.5s** (research 21.5s) | **−35%** |
| 2-scope token usage | 63.9k | 45.5k | −29% |

Single-scope jobs are bounded by one research call either way; the win shows
up exactly where it should — multi-scope fan-out with less web content per
call. Both runs produced the correct scope counts and successful estimates.

**These measurements calibrate the chat panel's progress wording.** The Maple
panel waits on a single buffered POST (no SSE anywhere in either codebase), so
`portal/src/lib/thinkingStages.ts` advances its labels on a timer whose
thresholds come from the table above: "Planning the work" at 2.5s (architect
~3s), "Researching materials and pricing" at 5.5s (the long pole),
"Calculating costs" at 20s, "Almost there" at 35s. If the pipeline's step
durations shift materially, re-check those thresholds. The wording is
**time-based, not event-based** — a stalled research call will still advance
on schedule; making it truthful would require the SSE work.

**Still open (decide with data from the new timing lines):**
- Retry budget: `openai_max_retries=2` × 90s timeout means a degraded step
  can burn up to 270s before falling back. The `architect_fallback` /
  `research_empty` flags now make the frequency visible — revisit after a
  week of logs; the fix would be retries=1 on the gracefully-degrading
  pipeline steps.
- Researcher model tier (gpt-5.6-luna) remains the bigger lever if "low"
  reasoning isn't enough.
- Metering gap (separate follow-up): the researcher's raw `responses.parse`
  calls bypass the langchain token callback — researcher tokens are never
  recorded in `LLMUsageEvent` / company counters.

---

## 2026-07-29 — Ops user lists: verified-only, and orphaned vs never-joined

Two related decisions about who belongs on `/ops/users` vs `/ops/new-users`.

### Orphaned users are derived from the audit log, not stored on the User doc

A user removed from a team has `company = None`, which on the document alone is
indistinguishable from a signup that never created a company. The distinguishing
fact already exists in `audit_logs`: every removal path writes one of two
actions, both anchored to the prior company —

- `USER_REMOVE_FROM_COMPANY` — `PUT /users/{id}` with a null company **and**
  `DELETE /users/{id}` (routers/users.py deliberately emits the same action for
  both so audit queries can't miss a path)
- `USER_LEAVE_COMPANY` — `DELETE /users/me/company`, the self-leave

`services/ops_membership.py::fetch_ever_joined_user_ids` runs one `distinct` on
the indexed `action` field and returns those user ids. `/ops/users` includes
"anyone in a company **or** in that set"; `/ops/new-users` excludes the set.

**Why derive rather than add `previous_company` to the User model:** no schema
change, no backfill, and it answers correctly for removals that already happened.
It also self-clears — `company` becoming non-null ends the orphan state because
that is checked first, so there is no field to remember to reset on the two join
paths (invitation accept, company onboarding). The rejected alternative's failure
mode is worse: a future removal path that forgets to maintain the field
mislabels that user permanently and invisibly, whereas this approach degrades
only if someone adds audit retention.

**The one thing that would break it:** a retention policy that prunes those two
actions would silently turn orphans back into "never joined" (i.e. back to the
pre-2026-07-29 behaviour). If audit pruning is ever introduced, either exempt
membership transitions or switch to the stored field. Sorting or filtering the
Users list *by* orphan status would also force the stored field, since you can't
sort on another collection.

### `/ops/users` hides unverified emails — with an inexact `total`

Verification lives in Firebase, not Mongo, so it cannot be part of the query.
The lookup is scoped to the rendered page (one batched call; `page_size <= 100`
is Firebase's per-call limit) and only an explicit `False` excludes a row —
`None` means "couldn't ask" (lookup failed, or `firebase_auth_disabled` in dev),
and treating that as unverified would blank the page during an outage.

Consequence: `total` is counted pre-filter, so it reads high by the number of
unverified accounts and a page can come back short. Mirroring `email_verified`
onto the User document (synced from the token claim on `/auth`, which every
login hits) would make it exact — deferred, because a mirrored flag goes stale
when a user verifies without returning to the app.

**Known gap:** `/auth/company-invitations/accept` uses `verify_firebase_token`,
not the `verify_verified_firebase_token` variant, so an unverified user *can*
accept an invite and join an established company. Such a user is now excluded
from `/ops/users` but is not picked up by `/ops/new-users` either (that query
only looks at company-less users and incomplete-onboarding companies), so they
are invisible to ops. Fix by either widening the New Users query or requiring a
verified email to accept an invitation — not yet decided.

---

## 2026-08-11 — Estimate catalog matching had no fuzzy path at all

`agents/estimate/catalog_matching.py::_score_catalog_match` returned three
discrete bands — 100 (exact), 80 (substring), <=60 (token overlap) — while
`_find_best_catalog_match` gated at `estimate_fuzzy_match_threshold` (85).
**Only the exact band could ever clear that gate.** The substring band and the
entire fuzzy-token band were unreachable dead code at the estimate-generation
call site, so AI generation matched inventory by exact string equality only.

Reported symptom: an LLM line named "Bulk compost soil amendment" scored 45
against the catalog's "Compost / organic soil amendment" and was silently
dropped into `unmatched_materials`. The module's own docstring advertised
"excavtor" → "excavator", which scored -1 (no match) — synonym canonicalization
rewrote "excavator" to "excavate" and only the canonical form was ever compared.
There was zero test coverage on the scorer, which is why this went unnoticed.

**Rewrite:** continuous 0-100 weighted token coverage,
`0.6 * coverage(requested) + 0.4 * coverage(candidate)`, with:

- **Alias splitting** on `/` — catalogs write alternate names that way. Numeric
  fragments are skipped so "3/4 inch" stays a size, not an alias.
- **Token weighting, not stopword removal** — qualifiers ("bulk", "premium",
  "organic") and unit words score 0.25, bare numbers 0.5, content 1.0.
  *Dropping* qualifiers would make "Organic fertilizer" and "Synthetic
  fertilizer" identical; down-weighting keeps them apart (80) while still
  letting "bulk compost" reach "compost" (92).
- **Raw AND canonical forms both scored, max wins** — fixes the excavator case.
- **Head-noun guard** — if neither side's last full-weight token matches, the
  score is capped at 60, below the review bar. Stops "Cedar post" being priced
  as "Cedar compost".
- **Field weighting** — `name` x1.0, `description` x0.9, `category` x0.75, so a
  shared category can never on its own produce a confident match.

**Two bars, not one** (`config.Settings`): at/above
`estimate_fuzzy_match_threshold` (85) the match applies silently; at/above
`estimate_fuzzy_review_threshold` (65) it still applies but the line is stamped
with `match_confidence` + `matched_from` (new optional fields on `MaterialItem`,
`LabourItem`, `ActivityItem`) and logged at INFO. **Why not one threshold:** a
silently mispriced line is worse than an unmatched one, but so is discarding a
correct match — the review stamp keeps recall without hiding the guess. Merging
duplicate lines inherits the *lowest* confidence of its parts, so a merge can't
launder a guess into a confident line.

**Perf:** the scorer runs per line per catalog entry. Memoizing token
similarity plus a length-ratio pre-filter (a SequenceMatcher ratio is bounded by
`2*min/(min+max)`, so tokens differing in length by more than 0.82/1.18 can't
clear the match bar) took a 250-item catalog from ~64 ms/line to ~3 ms/line.

**Known adjacent gap (not fixed):** `agents/estimate/llm_pipeline.py` sends only
`material_catalog[:50]` to the LLM, so companies with more than 50 materials
never show the model the rest — better matching can't recover a line the LLM
never knew existed.

**Not done:** no portal UI surfaces `match_confidence` yet; the flag is
persisted and returned by the API only.

---

## 2026-08-11 — The researcher never saw the material catalog (the `[:50]` was a red herring)

Follow-up to the catalog-matching rewrite above. The reported problem — the AI
inventing generic product names for materials the company already stocks — was
attributed to `llm_pipeline.py`'s `material_catalog[:50]`. That slice is real
but it is **not** the cause: it lives in `_generate_accuracy_suggestions`, a
post-generation advisory audit with a full rule-based fallback.

Actual exposure per path, before the fix:

| Path | Material catalog seen by the model |
|---|---|
| Pipeline researcher `_step3_research_for_scope` — **primary** | **none at all** |
| LLM extraction fallback (`service.py`, `available_materials`) | full, untruncated JSON |
| ReAct loop (`estimate_react_mode_enabled`, default **off**) | first 30 names + "and N more" + `lookup_materials` tool |
| Accuracy suggestions | first 50, as JSON |

The primary path builds its research prompt with
`build_estimate_research_prompt(..., labour_catalog=...)` — the **labour**
catalog was threaded through so activities could be assigned to real roles, but
the material catalog never was. The researcher named products from web search
with no idea what the company stocks, and the catalog matcher was left to
reconcile an invented name after the fact.

**Fix:** `prompts/material_catalog.py::render_material_catalog`, mirroring
`role_catalog.py`, threaded `_run_pipeline` -> `_step2_and_3_for_scope` ->
`_step3_research_for_scope`, plus a "use the EXACT catalog name" rule.

**Why name lines, not JSON:** measured at ~148 tokens per material as
pretty-printed JSON (id, description, category, every size with price and cost)
versus ~13 for a `` - `Name` (Category) `` line. A 300-item catalog is ~44k
tokens as JSON, ~3.9k as lines. The researcher only needs to know *what exists*
in order to name it; prices come from the catalog after matching. Rows past
the cap are **disclosed** ("... and N more not shown") and rows are ordered by
relevance to the scope text so the cut falls on the irrelevant tail. Rendering
also carries the same injection hardening as roles — note that the
control-character check must run **before** whitespace collapsing, or an
embedded newline is folded to a space and waved through.

**Two caps, because the researcher runs once per scope.** A scoped render
(`scope_text` supplied) uses `estimate_prompt_max_scoped_materials` (40); an
unscoped one uses `estimate_prompt_max_materials` (300). Injecting 300 rows
into every per-scope researcher call cost ~4.5k tokens *per scope* — ~13.6k on
a 3-scope job — for scopes that each concern a handful of products. The tight
cap is 86% cheaper (651 vs 4,543 tokens per scope) and loses nothing that
matters, because relevant rows are ordered first. The remaining slots are
deliberately **filled with non-matching rows rather than hard-filtered**:
relevance is crude token overlap and will miss materials a scope genuinely
needs (a paver patio needs base fabric, which shares no token with "paver
patio"), so a strict filter would recreate the original bug. Accuracy
suggestions passes `scope_text` for ordering but overrides back to the wide
cap — it is one call whose job is spotting what is *missing*, so it wants
breadth.

**Why inject at all when step 4 already fuzzy-matches?** The two cover
different failure modes. The matcher is string similarity, so it closes
*near*-misses ("Bulk compost soil amendment" -> "Compost / organic soil
amendment", 92) but provably cannot bridge a vocabulary gap — "Geotextile weed
barrier" vs "Landscape fabric", "Decomposed granite" vs "Crushed stone
screenings", "Screened loam" vs "Topsoil" all score **0**, with no signal to
threshold on. Only a model that has seen the catalog picks the right name. This
matters beyond cosmetics: `materials_total` sums matched lines only, so an
unmatched material contributes **$0** and silently under-prices the job.

Also fixed: `render_labour_role_catalog` capped at 40 roles **silently**. The
cap stays (role rows carry up to 300 chars of responsibility text, so they cost
several times a material line) but now discloses the remainder — silently
truncating lets the model believe it has seen every role and confidently invent
one that already exists further down.

Token effect on the suggestions prompt: catalogs up to ~120 materials got
*cheaper* and complete (50-item catalog: 3,020 -> 793 tokens); a 300-item
catalog costs ~1.5k more but shows 6x the materials.

**Not changed:** the extraction-fallback path still dumps the full catalog as
JSON (`service.py`, `available_materials`) — ~44k tokens for a 300-item
catalog. It is a genuine cost problem but it is the *fallback*, and switching it
to name lines would drop the size/price detail that path's prompt relies on.
Worth revisiting separately.

---

## 2026-08-14 — HSTS on the marketing site, staged rollout

`website/firebase.json` carried no `headers` block, while `portal/firebase.json`
has sent `max-age=31536000; includeSubDomains` for months. Firebase does redirect
http→https, but that redirect happens *after* a plaintext request has left the
browser — so anyone typing the domain or following a scheme-less link made one
cleartext round trip, URL and `utm_*` parameters included. The marketing site is
the property most likely to be typed into an address bar, so it was the wrong one
to be missing it.

**Which domains firebase.json actually governs** — measured, because assuming
this wrong is easy and the first version of this note did:

| Domain | `Strict-Transport-Security` | Set by |
|---|---|---|
| `app.3maples.ai` (custom) | `max-age=31536000; includeSubDomains` | `portal/firebase.json` |
| `fieldservice-portal-tangz.web.app` | `max-age=31556926; includeSubDomains; preload` | Firebase, forced |
| `maples-website*.web.app` | `max-age=31556926; includeSubDomains; preload` | Firebase, forced |

Firebase sends its own HSTS on every `*.web.app` host regardless of config — the
whole TLD is on the browser preload list — and it **overrides** whatever
`firebase.json` says. Only custom domains take the configured value, which the
portal row proves: it returns exactly the value its config sets, `preload`
absent.

Two consequences. The ramp below governs **`3maples.com` only**; the `.web.app`
mirrors are already permanently preloaded and nothing here changes them. And
"does the site send HSTS?" cannot be answered by curling a `.web.app` URL — that
always says yes. It has to be the custom domain.

**Currently deployed: `max-age=300` (5 minutes), no `includeSubDomains`.**
That is stage 1 of a deliberate ramp, not a final value. A short max-age is the
standard way to introduce HSTS: the commitment is nearly free to reverse while
you confirm nothing on the domain needs plaintext.

Ramp, raising only after each stage is confirmed healthy:

| Stage | Value | Confirm before advancing |
|---|---|---|
| 1 (now) | `max-age=300` | Site loads normally; no mixed-content or redirect loops. |
| 2 | `max-age=86400; includeSubDomains` | **Every** `*.3maples.com` subdomain serves https. This is the risky step — it binds subdomains too, and a plaintext-only one breaks for a day. |
| 3 | `max-age=31536000; includeSubDomains; preload` | Only if we actually want browser-preload-list inclusion, which is effectively permanent and removal takes months. |

Note `includeSubDomains` on `3maples.com` does **not** affect `app.3maples.ai` —
different apex (`.ai` vs `.com`), so the portal is unaffected either way.

Config lives in `website/firebase.json` under `hosting.headers`. JSON allows no
comments, which is why the ramp is recorded here: a bare `max-age=300` left in
place indefinitely provides almost no protection, and raising it blind skips the
subdomain check that stage 2 exists for.

**Not yet verified on the domain that matters.** `3maples.com` is unreachable
from the office network — something terminates port 443 and answers in plaintext
with `HTTP/1.1 302 → safebrowse.io/warn.html`, which is a filtering proxy, not
Firebase (`app.3maples.ai` on the same infrastructure returns a normal TLS
handshake). So the header's arrival on the custom domain has to be confirmed from
an unfiltered network — a phone on cellular is enough:

    curl -sI https://3maples.com/ | grep -i strict-transport

Expect `max-age=300` after the release promotion. Anything else — including the
`31556926 … preload` value — means you hit a `.web.app` host rather than the
custom domain. The same proxy will make GA4/pixel acceptance tests against
`3maples.com` fail for reasons unrelated to the code, so check it before
debugging anything else.
