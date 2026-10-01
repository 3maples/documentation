# Maple metrics, and the next batch after the phrasing push

**Date:** 2026-09-30 · **Status:** all decisions made (§8); two review rounds against the
code the same day (§7); nothing built

Inputs: a full read of `maple-phrasing-reference.md` (51 ⚠️ gap rows) and
`code-review-followups.md` (Maple section, #669–#780), plus the current
aggregation, status-write and date-filter code.

## 1. Where things stand

The phrasing push closed the multi-turn and name-answer work. What is left
falls into three groups:

| Group | What | Weight |
|---|---|---|
| **Metrics** | Maple can count and list, but cannot *compute*. Totals exist only for the whole company or an open/sold status set. **§1.1 row 323 is already logged as a gap:** "total value of sold estimates for Bob Lee" ignores the customer. | New capability, highest user value |
| **Routing hazards on the metric path** | #719, #720, #721, #779, #780 — analytics and list patterns that catch messages they shouldn't, or read a surname as a status. Each new metric pattern would add to this. | Fix *before* metrics |
| **Phrasing gaps** | Status verbs (`approve`, `reject`, `send for review`, `move to draft`, `put {title} on hold`), "when was X created / updated", task bare-title forms, "Elm House" read as a contact, #759 and "the city there" | Small, mostly independent |

Also open: **#762 (the only HIGH)** — negated task edits still write. Fix
approach confirmed (decision 4). #706 (question gate) and #710 (task
due-date question becomes a write) are Maple routing bugs too, but not on the
metric path; they stay in the followups queue.

## 2. What exists today (verified 2026-09-30)

- **Sums.** Six places sum `grand_total` independently, each loading whole
  estimate documents and adding in Python: in `agents/estimate/crud_handlers.py`
  the `_handle_list_estimates` aggregate branch, `_analytics_headline_value`,
  `_analytics_total_value` and `_analytics_windowed_summary`; in
  `routers/estimates.py` `compute_status_comparison` and `compute_analytics`
  (the dashboard).
- **What `grand_total` contains.** It is the sum of each work item's
  `effective_sub_total()`, so it **includes tax** (`final_total = after_profit +
  tax`) and **multiplies a recurring work item by its occurrences**. Every
  dashboard figure is tax-inclusive today.
- **Divisions live on work items, not estimates.** The dashboard's
  `_rollup_divisions` sums work-item `effective_sub_total` per division and
  leaves Lost estimates out. The Maple list handler's division filter
  (`job_items.division`) plus its aggregate branch sums the **whole**
  `grand_total` of every estimate that has one work item in the division, which
  overstates a multi-division estimate. Not yet confirmed that a phrasing
  reaches that combination; Phase 1 checks and fixes it.
- **Status sets** are named (`_SOLD_ESTIMATE_STATUSES`,
  `_OPEN_ESTIMATE_STATUSES`; pipeline/backlog/completed mirror the dashboard).
  With no status named, `_analytics_total_value` excludes Archived, Generating
  and Failed and keeps Lost. `Deleted` is only a transient soft-mark before the
  document is removed (`services/estimate_delete.py`).
- **The question reader.** `list_query.read_list_query` reads status,
  customer/property name, period and amount in one pass. It is the front half
  of a metric question.
- **Margin math.** `routers/estimate_helpers/calculations.py` has
  `work_item_breakdown` / `work_item_gross_margin`, already ported for Maple.
- **Dates.** `Estimate` has `created_at` and `updated_at` only. List filters
  (`_parse_estimate_date_filter`) are **rolling windows in UTC** ("this month"
  = the last 30 days). The dashboard's chart periods (`_period_range`) are
  **calendar periods**, also UTC. Tasks already use the user's time zone
  (`client_context.timezone`, `agents/local_time.py`); estimates do not.
- **Status writes all bypass the model hooks.** Every status change is a
  `.set()` (`persist_fields` → `versioned_set` for Maple; `estimate.set(...)`
  in the PUT, archive, unarchive and delete routes), and `.set()` does not run
  `before_event`. The write sites are listed under Phase 1.
- **Status history exists, partly.** The portal's PUT writes an
  `ESTIMATE_UPDATE` audit entry with full `before_state` / `after_state`, and
  unarchive writes `ESTIMATE_STATUS_CHANGE`, since 2026-03-15. **Maple's
  status transitions write no audit entry** (`crud_handlers.py:3503`).
- **Follow-up replay.** `agents/conversation/followup.py` replays a read only
  when its intent matches `^(get|list|count)_|^analytics_`, and swaps a period
  only for `^analytics_` or `list_estimates` / `list_tasks`.

## 3. The design: one metrics engine, math never in the LLM

Every number comes from deterministic code over the database. The LLM tier may
*parse* a question into a spec; it never does arithmetic (same rule as the
Calculator agent's curated formulas).

```
MetricQuery(
  metric:   total | average | largest | smallest | win_rate | margin | markup
  statuses: one status, or a named set (sold, open, pipeline, backlog, completed)
  subject:  company | property | contact/customer | division | material | role
  period:   all_time | this/last month|quarter|year | last N days
  group_by: None | customer | property | division | status | month
  rank:     None | top N | bottom N
)
```

- **New module `services/maple_metrics.py`**, one entry point, always
  `$match`ing `company` first.
  - Estimate-level figures (total, average, largest, per-status,
    per-property) use a Mongo `$match` + `$group` on the stored `grand_total`.
  - Work-item figures (division, margin, markup, line-level) need
    `effective_sub_total()` and `work_item_gross_margin`, which are Python. Load
    them with a **projection** of the fields they read, never whole documents.
- **Counts stay where they are.** `list_estimates` counts are already correct,
  scoped and remembered as lists. The engine takes over sums, averages and
  extremes; the list handler's aggregate branch ("total value of the open
  estimates", "what's the total of those?") calls the engine.
- **Consolidate the six sums onto it**, the dashboard included.
  `test_dashboard_backlog_parity.py` and the analytics tests are the regression
  net; the dashboard must not move by a cent except the Completed card (decision 5).
- **Default status set** when none is named: every estimate except Archived,
  Generating, Failed and Deleted (Lost stays in), the same as
  `_analytics_total_value` today.
- **Periods** are calendar periods ("this month" = since the 1st) in the
  user's time zone from `client_context.timezone`, falling back to UTC. "Last N
  days" stays rolling. This matches the dashboard's `_period_range`, not the
  list filters (decision 7).
- **Routing.** A new intent named **`analytics_metric`** — the `analytics_`
  prefix is what makes `followup.py` replay it ("and last year?", "what about
  Elm House?"). Its phrasings are `command_grammar.py` entries (the
  written-list rule: no regex elsewhere), each with accept and **reject**
  tests and a phrasing-reference row. The reject rows must cover the words it
  shares with existing features:
  - "how much": `how much is E0042?` (§1.2), `how much mulch do I need for 200
    sq ft?` (Calculator).
  - "average": `what's the average wage for Foreman?` (§5.8), "an average
    patio" in a create.
  - "total": `what's the total on it?` (one estimate), `what's the total of
    those?` (list follow-up).
  - superlatives: `show me estimates with the highest total` stays the sorted
    list (#722).
- **LLM tier.** The classifier learns the intent. When the grammar cannot
  parse a question, a structured-output call fills `MetricQuery` with
  enum-constrained fields (Pydantic-validated, values outside the enums
  refused). An ambiguous spec asks one question through the question gate
  (`open_question.py`).
- **Replies name what was counted**, as list replies now do: *"Lifetime won
  value for 12 Oak St: $48,250.00 across 4 estimates (Won, Scheduled,
  Completed)."* A single-estimate
  answer (largest, smallest) records the row as a listed item and anchors it,
  as `get_estimate` does, so "what's its status?" and "open it" work next turn.
- **Public Maple** (`agents/maple_public`) answers from the guide only. A
  metric question there must get the sign-up refusal, never a guide answer
  with made-up figures; add a test.
- **"This property", "them", "here".** A metric question with no name takes
  its subject from the record in focus (`agents/conversation/focus.py`), which
  includes the property or contact open on the portal page (`viewed_record`):
  "what's the lifetime value of this property?", "how much have we sold
  them?". Company-wide wording ("my", "all my", no pronoun) never takes the
  focused record — #719 is that bug for single-estimate questions, fixed in
  Phase 0.
- **Nothing to count vs. nothing found.** "12 Oak St has no won estimates."
  is not "I couldn't find a property called 12 Oak St.", and neither is
  "$0.00". An average or a largest over nothing says so instead of dividing.
- **Money.** Sum unrounded, round to cents once for the reply.
- **Recurring work items** count in full, all occurrences, in the period the
  estimate's status changed — as `grand_total` and the dashboard already do.
  The reply notes it when a recurring item is included.
- **LLM usage.** The spec-parsing call logs an `LLMUsageEvent` under its own
  feature tag (e.g. `orchestrator.metric_spec`), like the other agents.

### Reading "won" *(decided 2026-09-30, decision 8 option A)*

A **won** job is one the customer said yes to, whatever has happened since. In
money and win-rate questions "won" is the sold set, **Won + Scheduled +
Completed**, so a job doesn't leave "won" when it gets scheduled or finished:

- "lifetime won amount from 12 Oak St" and "how much have I sold to Bob Lee"
  sum the same set;
- win rate = sold ÷ (sold + Lost);
- "in Won status", "currently Won" and "still Won" mean the literal status.

Every reply names the statuses it summed. Counts and lists are unchanged by
this decision: "how many won estimates do I have?" and "show me won
estimates" stay Won-only (§1.1, "a named status still wins"). That is a known
difference between "how much did I win?" and "how many won estimates?"; the
reply's status list makes it visible. Aligning counts is a separate call.

**When a job was won.** A period on "won" / "sold" filters **`sold_at`** — the
moment the estimate entered the sold set — not `status_changed_at`, which moves
again on Scheduled and Completed. Without it, "how much did I win this month?"
would count jobs completed this month that were won in the spring. `sold_at`
is added with `status_changed_at` in Phase 1a.

## 4. Phases

Phase 0 ships on its own. Phase 1 is the first metrics release. Each phase
ends with tests, the phrasing reference updated (§12.3 counts, "Last
updated"), a `test_maple_conversations.py` row, and a reviewed
`test_maple_routing_snapshot.py` diff.

### Phase 0 — Make the ground safe (small, do first) — **done 2026-09-30**

All five shipped: #762 (`756303b`), #721 (`fae3e11`), #719 + #720 (`77e55ef`,
the grammar move split out as #781), #779 + #780. Found along the way: #782, a
pre-existing test failure.

1. **#762** (HIGH) — anchor the task edit patterns with `_COMMAND_LEAD`, no
   negation rules; the phrasings in the entry become `_NEGATED_EDITS` rows, plus
   a note whose body contains "don't" that still appends.
2. **#721** — anchor the pipeline/backlog analytics patterns to a question head
   and skip them when `match_command` parses the message. Metrics add patterns
   in the same function; unanchored ones would make this worse.
3. **#719 + #720** (same file, `focus_questions.py`) — with an estimate in
   focus, a definitional, comparative, catalog or company-wide question is not
   a question about that estimate ("what is markup?", "how much does mulch
   cost?"), and superlatives are never one ("which estimate has the highest
   total?"). The no-reference fallback needs "it", "this" or "the estimate",
   and the phrasings move into a grammar entry with accept/reject tests. Left
   alone, "what's my average markup?" with an estimate open would answer with
   that estimate's markup. Until Phase 1 the superlative falls back to the
   sorted list; after it, the engine answers.
4. **#779 + #780** — keep the unsplit name on `ListQuery` and look it up first;
   ask when two statuses disagree. Metrics reuse this reader, so a surname
   "Won" or a conflicting status must not silently miscount money.

### Phase 1 — Status timestamp, then scoped value metrics (the core)

**1a. `Estimate.status_changed_at`** *(decision 2)*

A `before_event` cannot set it: every status write is a `.set()`. Instead:

- One helper (e.g. `services/estimate_status.py::status_patch(current, new)`)
  returns `{"status": new, "status_changed_at": now}` when the status actually
  moves, and `{"status": new}` when it doesn't, so a PUT that re-sends the
  same status keeps the date. Every write site uses it:
  - Maple's transition, `crud_handlers.py:3503` (`persist_fields(target,
    "status")` must write both fields).
  - The PUT, `routers/estimates.py` `update_estimate` (`update_data["status"]`).
  - Archive and unarchive, `routers/estimates.py` (`estimate.set({...})`).
  - Generation finishing, `agents/estimate/llm_pipeline.py:1076`
    (Generating → Draft).
  - The delete soft-mark in `services/estimate_delete.py` does not need it (the
    document is removed straight after).
- **`sold_at`** is set by the same helper when the status enters the sold set
  (Won, Scheduled, Completed) from outside it, and left alone on moves
  *within* it (Won → Scheduled → Completed). Leaving the set (Won → Lost) keeps
  the old value, which no sold-set query reads; re-entering stamps it again.
  An insert straight into the sold set stamps it. Same fallback as
  `status_changed_at`: missing means `updated_at`. Index
  `(company, sold_at)`.
- **Inserts** default the field to the insert time. The generation-shell
  creates (`delegate_create_estimate.py`, `estimate_gathering.py`), the POST
  and the clone (`routers/estimates.py:943`, which must **not** copy the
  source's date) all get it that way.
- It is **server-owned**: not in `UpdateEstimateRequest`, never read from a
  client.
- A **guard test** fails if any module writes `status` on an estimate without
  the helper (scan for `"status":` / `.status =` against the `Estimate` model,
  in the manner of `test_models_layering.py`), so a seventh write site cannot
  quietly skip it.
- **Maple's status transitions start writing an audit entry**, as the portal's
  do. Today a status changed in chat leaves no trace.
- **Index** `(company, status, status_changed_at)`.
- **No backfill** *(decided 2026-09-30)*. An estimate without the field uses
  `updated_at`. A period filter is written as
  `$or: [{status_changed_at: <range>}, {status_changed_at: null, updated_at: <range>}]`
  rather than an `$ifNull` expression, so both branches can use an index
  (`(company, updated_at)` already exists). Every status change from deploy
  onward sets the field, so the fallback only covers estimates whose status
  hasn't moved since, and nothing has to run before or after the deploy.

  **Accepted limitation:** for those older estimates, "won this month" means
  "Won and last edited this month", as today, and an edit that doesn't change
  the status moves them into the current period. Lifetime questions are
  unaffected. If this shows up in real answers, an optional backfill can
  fill the field from the portal's audit entries (before/after status since
  2026-03-15), then `created_at` for an estimate still in its first status,
  then `updated_at`.

**1b. The engine and scoped totals**

The scopes that already resolve by name: **company, property, customer
(contact → properties), division, status or set, period**.

| Phrasing | Metric |
|---|---|
| `what's the lifetime won amount from {property}?` | total, sold set (won = Won + Scheduled + Completed), all time, property |
| `how much have I sold to Bob Lee this year?` | total, sold set, this calendar year (by `sold_at`), customer |
| `what's the average estimate value?` / `… for won estimates?` | average |
| `what's my biggest / smallest estimate?` | largest / smallest, with code and title |
| `what's Bob Lee's average job size?` | average, customer |
| `what's the value of Landscaping vs Hardscape?` | work-item sums per division |
| `how much is still in draft for Elm House?` | total, Draft, property |

- **Customer** = contact. A contact on several properties sums those
  properties' estimates, each counted once. A property with two contacts
  appears under both when grouped by customer; the reply for a ranking says
  so. A contact with no property answers as the list does ("… isn't linked to
  any properties yet").
- **Which date a period filters.** With a status or set named, the period
  filters `status_changed_at` ("drafts from this month" = became Draft this
  month); with "won" or "sold" it filters `sold_at` ("won this year" = the
  customer said yes this year). With no status, `created_at`.
- **Division** sums work items, never `grand_total`; Lost left out, matching
  the dashboard. Fixes the list handler's division aggregate if it overstates.
- **Before tax** (decision 6): `… before tax` / `pre-tax` / `excluding tax`
  sums work-item pre-tax revenue (`work_item_breakdown`); otherwise totals are
  tax-inclusive, and the reply says which.
- **Dashboard Completed card** (decision 5) moves to `status_changed_at` in
  the same change that puts `compute_analytics` on the engine, so the card and
  Maple's "completed value" never disagree. Portal copy unchanged; the parity
  tests are updated to the new meaning.
- Closes §1.1 row 323 and the "Elm House" gap (row 734), since the subject
  resolver is shared.

### Phase 1 — task breakdown *(2026-09-30)*

Checked against the code before writing. Two findings shape it:

- **Inserts run model hooks; `.set()` does not.** Every new estimate goes
  through `insert` — the portal POST, the clone, AI generation
  (`ai_generation.py`, which also inserts the generation shells) and Maple's
  create (`crud_handlers.py:792`). So a `before_event(Insert)` hook stamps
  both dates on every new estimate, and only **four** `.set()` sites need the
  helper: Maple's transition (`crud_handlers.py:3548`), the PUT
  (`update_data["status"]`), archive and unarchive. The delete soft-mark is
  exempt (the document is removed next). The clone builds a fresh `Estimate`
  and copies no dates.
- **#721's gate and the metric grammar collide.** Since #721,
  `match_analytics_query` returns None for any message `match_command`
  parses. Metric phrasings become grammar entries, so they must route through
  `_route_listed_command` to the new intent — not through the analytics
  matcher, which would now skip them.

One commit per task, failing test first, related tests plus mypy/ruff each
time, phrasing reference in the same commit as the phrasing.

| # | Task | Size | Repos |
|---|---|---|---|
| **1a — the dates** — done 2026-09-30 (`b799caf`, `12b4ebe`, `9e42ae1`, task 4) ||||
| 1 | **Fields and helper.** `Estimate.status_changed_at` / `sold_at` (`Optional[datetime]`). Move the sold set to `models/estimate.py` (`SOLD_STATUSES`) so services can use it; `agents/estimate/text_helpers._SOLD_ESTIMATE_STATUSES` reads it. `services/estimate_status.py::status_patch(current, new, now)` → `{"status"}` plus `status_changed_at` when the status moves, plus `sold_at` when it enters the sold set from outside. A `before_event(Insert)` hook stamps both on a new estimate. Tests: every transition shape (move, no move, into / within / out of / back into the sold set), insert into Draft and into Won. | S | platform |
| 2 | **Wire the four write sites** and a **guard test** that fails if a module writes an estimate's `status` without `status_patch` (allowlist: `services/estimate_delete.py`). Endpoint tests: a PUT status change sets the date; a PUT re-sending the same status keeps it; archive / unarchive; Won → Scheduled keeps `sold_at`; a client-sent `status_changed_at` is ignored. Maple: a chat transition sets both. | M | platform |
| 3 | **Maple status transitions write an audit entry** (`ESTIMATE_STATUS_CHANGE`, before/after status), as the portal's do. | S | platform |
| 4 | **Indexes** `(company, status, status_changed_at)` and `(company, sold_at)`; non-unique, safe at boot. CLAUDE.md: the two dates, the helper rule, the `updated_at` fallback. | S | platform, workspace |
| **1b — the engine** — tasks 5–10 done 2026-09-30 (`98649b1`, `5549429`, `9ee1f68`, `0909d49`, `d8dada8`, task 10) ||||
| 5 | **Periods.** Move `_period_range` out of `routers/estimates.py` into the metrics service, add the user's time zone (`agents/local_time.user_zone`, UTC fallback) and "last N days". Tests include a month boundary in a non-UTC zone. | S | platform |
| 6 | **Engine core**, `services/maple_metrics.py`: `MetricQuery` (Pydantic, enum fields) → `MetricResult` (value, count, statuses summed, period, rows for largest/smallest). Estimate-level `$match` + `$group` on `grand_total`: total, average, largest, smallest; status or set (won/sold = sold set, decision 8); period on `sold_at` / `status_changed_at` / `created_at` with the `$or` fallback to `updated_at`; default set excludes Archived, Generating, Failed, Deleted. Tests against the local Mongo with a seeded company: each metric × status × period, the fallback (documents without the fields), empty set, rounding. | L | platform |
| 7 | **Work-item figures**: division sums (`effective_sub_total`, Lost out), "before tax" (pre-tax revenue from `work_item_breakdown` × occurrences), via a projection. Tests: a two-division estimate, a recurring item, tax on and off. | M | platform |
| 8 | **Subjects**: company, property, customer (contact → properties, estimate ids deduped), division; a name resolved like the list's (exact whole name first, #779); "this property" / "them" from focus and `viewed_record`, never for "my / all my". Not-found vs nothing-to-count replies. Tests: two-contact property, two-property contact, a property open on the page. | M | platform |
| 9 | **Maple's sums onto the engine**: the list handler's aggregate branch and `_analytics_headline_value` / `_analytics_total_value` / `_analytics_windowed_summary`. Fix the division aggregate if it overstates (test first). Existing analytics tests unchanged except where a figure was wrong. | M | platform |
| 10 | **Dashboard onto the engine** — `compute_analytics`, `compute_status_comparison` — with the Completed card on `status_changed_at` (decision 5). Parity tests updated to the new meaning; every other card unchanged to the cent. Portal: the Completed tooltip says "marked Completed in the last 30 days" (copy only). | M | platform, portal |
| **1b — Maple** — tasks 11–14 done 2026-09-30 (`4c1a29c`, `d49c964`, `5030b8a`, task 14) ||||
| 11 | **Routing.** `analytics_metric` in the intent registry (→ Estimate Agent); grammar entries in `command_grammar.py` (`READ_IDS`) for the §4 Phase 1 table, with accept/reject tests — rejects for "how much is E0042?", "how much mulch do I need …", "average wage", "the total on it", "the total of those", "show me estimates with the highest total"; `_route_listed_command` sends them to the new intent. Reviewed routing-snapshot diff. | M | platform |
| 12 | **Handler and replies**: the Estimate Agent answers `analytics_metric` from the engine — statuses, scope, period and tax named; recurring note; a single-estimate answer recorded as a listed row and anchored. Follow-ups "and last year?" / "what about Elm House?" replay (the `analytics_` prefix). Public Maple refuses metric questions. | M | platform |
| 13 | **LLM tier**: the classifier learns the intent; a structured-output call fills `MetricQuery` when the grammar can't, usage-tagged `orchestrator.metric_spec`, off in tests; an ambiguous spec asks through the question gate. Live-tier rows in the coverage matrix. | M | platform |
| 14 | **Docs and corpus**: phrasing reference §1.12 (new), §1.1 row 323 and §1.8 row 734 ✅, §1.9 Completed meaning, §12.3 counts; `test_maple_conversations.py` rows (lifetime won for a property, sold to a customer this year, "and last year?"); followups. | S | platform, documentation |

**Order and release points.** 1–4 can ship on their own (the dates start
filling from that deploy, which shortens the fallback period — worth shipping
early). 5–8 have no user-visible effect. 9–10 move existing figures onto the
engine; 10 changes the Completed card, so it's its own release note. 11–14
switch the feature on. Tasks 11–13 are the ones to review most carefully:
they change routing.

**Phase 1 done, 2026-09-30.** What changed on the way, against the table above:

- "What's the value of Landscaping vs Hardscape?" moved to Phase 2 (a
  two-division breakdown); one division's total shipped.
- Two latent bugs fixed in passing: a list total summed only the first page
  of 20, and a division total summed each estimate's whole value (task 9).
- A Phase 0 regression caught and fixed: the #719 fix stopped reading "its"
  as "it" ("what's its status?"), task 12.
- The router's generation-shaped fallback for Estimate intents dropped the
  metric result; `analytics_metric` now returns whole (task 12).
- Left open: #783 (an estimate title as a subject), #784 (won in counts vs
  money); the LLM tier's live run of `metrics_paraphrase` is the user's.

**Code review of Phases 0–1, 2026-09-30** — 20 findings, all fixed. The ones
that change how Phase 2 should be built:

- **A metric question's tail must be fully read.** `metric_query._peel` now
  refuses (returns None) when words are left that aren't "for <name>";
  "excluding X", "since …", "in 2025" were read as names. Phase 2's ranking
  and comparison entries reuse `_M_TAIL`, so they inherit this.
- **Subjects match whole words, never the reverse.** `metric_subject._by_name`
  no longer trusts the finders' two-way substring match; same-named records
  merge, and a customer/property clash is offered as "X (customer)".
- **`sold_at` for pre-deploy sales**: `status_patch(..., record=)` dates one on
  its first move within the sold set (decision 2 refined; still no backfill).
- **The engine pre-filters a division in Mongo** (`division_clause`, shared
  with the list filter), computes `has_recurring` in its `$group`, and
  `run_metric` is split into `_estimate_metric` / `_item_metric` — the place
  Phase 2's breakdowns attach.
- **The LLM tier's subject must be words of the message**, and its prompt
  declines scopes the choices can't express.

### Phase 2 — Rankings and breakdowns
- `who are my top 5 customers by won value?`, `which property has the most
  estimates?`, `which division earns the most?`, `value by month this year`.
- Ranked rows go through `format_and_record_list_response`, so "the second
  one" and "show more" work on them.
- Follow-ups replay through `followup.py` because of the `analytics_` intent:
  `and last year?`, `what about Elm House?`, `just the drafts`.
- **Period comparisons**: `how does this month compare to last month?`, `am I
  up on last year?`, `sold this quarter vs last quarter`. Two engine calls and
  the difference in dollars and percent. "Last year so far" compares like
  with like: the same number of days into the period, not a whole year
  against a partial one.

### Phase 2 — task breakdown *(2026-09-30)*

Checked against the code before writing:

- **The division ranking exists in all but name.** `run_division_breakdown`
  already sums work items by division (Lost left out, as the dashboard's
  chart). "Which division earns the most?" is that list ranked; "breakdown of
  estimates by division" and "estimate value by division" stay the dashboard's
  answer (`analytics_estimates`, §1.9) — reject rows, not new entries.
- **Month grouping can happen in Mongo, on the user's clock.** `$dateTrunc`
  takes a time zone (Mongo 5.0+; local is 8.3 — confirm Dev and Prod Atlas
  before task 2 ships). The date is `$ifNull: [<date field>, "$updated_at"]`,
  the same fallback the period filter uses.
- **Follow-ups mostly come free.** `followup.py` replays any `analytics_`
  read, so "and last year?" and "what about Elm House?" work once a ranking or
  comparison is an `analytics_metric` answer with `filter_by.name`. Refining
  ("just the won ones") only knows `list_estimates` / `list_tasks` today —
  task 8 decides whether a metric answer joins them.
- **Ranked customers and properties are records.** Recorded with
  `format_and_record_list_response` as contact / property rows, "the second
  one" opens the record and "show more" pages, like any list.

One commit per task, failing test first, related tests plus mypy/ruff each
time, phrasing reference in the same commit as the phrasing. A `/code-review`
round before the push, as for Phase 1.

| # | Task | Size | Repos |
|---|---|---|---|
| **2a — the engine** ||||
| 1 | **Rankings** (decisions 9, 12). `run_ranking(company_id, query, by, measure, limit, offset)` → rows (id, label, value, count) and the number of rows in all. `by`: property (`$group` on `property`), customer (the properties' `contacts`, one `Property` query; a shared property counts for each customer), division (the breakdown's per-item sums; count = estimates with work in it). `measure`: value or count. Ties by label. Tests: seeded company with a two-contact property, a two-property contact, a contact on none, a division-split estimate, `offset` paging. | M | platform |
| 2 | **By month.** `run_by_month(company_id, query, zone)` — `$group` on `$dateTrunc` (month, the user's zone) of the date field with the `updated_at` fallback; every month in the period, $0 where empty; value and count. Tests: an estimate sold 11 p.m. Sept 30 in Toronto is September; fallback documents; empty months; a period across New Year. | M | platform |
| 3 | **Comparison periods** (decision 11). `metric_periods.comparison(name, now, *, whole=False)` → (current, previous): like with like by default — this month so far against the same days of last month; "this year" against the same days last year; a whole previous period only when it is asked for ("all of last month") or the current one is over. Day 31 against a 30-day month ends at the month's end; Feb 29 handled. Labels say the days ("Sept 1–15"). | S | platform |
| 4 | **Comparisons in the engine** (decision 10). `run_comparison` — two `run_metric` calls (gathered) → both results, the difference in dollars and percent (no percent when the earlier figure is $0). Tests: up, down, flat, from nothing, with a subject and a status. | S | platform |
| **2b — Maple** ||||
| 5 | **Routing.** `analytics_metric` grammar entries for rankings ("top 5 customers by won value", "who are my best customers", "which property has the most estimates", "which division earns the most"), by month ("value by month this year", "how much did I sell each month") and comparisons ("how does this month compare to last month", "this quarter vs last quarter", "am I up on last year?"). Reject rows: the sorted estimate list ("show me estimates with the highest total", "top 5 estimates", #722), Phase 1's biggest ("which estimate has the highest total?"), the dashboard breakdowns ("breakdown of estimates by division", "pipeline by status"), status comparisons ("won vs lost", "draft vs approved") and win rate (Phase 3). Reviewed routing-snapshot diff. | M | platform |
| 6 | **Reading.** `MetricAsk` gains `shape` (figure / ranking / by_month / comparison), `by`, `measure`, `limit` and the comparison's terms; `read_metric_query` fills them from the slots, and every unread word is still refused (`_peel`). Reading tests per entry. | M | platform |
| 7 | **Answers.** Ranking: numbered rows with value and count, naming statuses, period and tax, and the shared-property note when a property counts twice; rows recorded as records, so "the second one" opens it and "show more" pages. By month: one line per month and the total. Comparison: both figures, their days, and the change — *"Sold this month so far (Sept 1–15): $12,400 across 6 estimates; the same days last month: $9,800 across 5 — up $2,600 (+27%)."* Subject-scoped versions ("by month for Bob Lee", "compare Elm House to last year"). Seeded answer tests pin exact figures. | L | platform |
| 8 | **Follow-ups.** "and last year?" and "what about Elm House?" for each shape; "top 10" / "show more" after a ranking; "the second one" after a ranking opens the contact or property. "Just the won ones" after a metric answer stays a gap (decision 13) — a ⚠️ row, no code. | M | platform |
| 9 | **LLM tier.** `MetricSpec` gains `shape`, `by`, `measure`, `limit` and `compare` as fixed choices; prompt and `ask_from_spec` follow; the subject-in-message check still applies. Tests as task 13 of Phase 1. | S | platform |
| 10 | **Docs and corpus.** Phrasing reference §1.12 (rankings, by month, comparisons, their follow-ups), the "Recent changes" paragraph, open gaps, §12.3; coverage-matrix categories `metrics_ranking` / `metrics_compare`; corpus conversations (top customers → "the second one" → "and last year?"; this month vs last month); CLAUDE.md "Metric questions" bullets; this plan. | S | platform, documentation, workspace |

**Order and release points.** 1–4 add engine functions nothing calls yet, so
they ship without a visible change. 5–8 switch the feature on; 5 is the one
to review most carefully, since it changes routing. 9 can follow separately.

**Phase 2 done, 2026-09-30** (`f08c68c` … task 10). What changed on the way:

- Tasks 5 and 6 each kept the feature off until the next landed: task 5's
  reader declined the new shapes and task 6's answer handed them to the
  dashboard, so no commit could answer a ranking as a single total.
- "Which property has the most estimates?" and "my best customer" — a
  singular — answer the top one, not a list of 5.
- A comparison that also names a period ("this month vs last month this
  year") is said back as a scope Maple can't narrow by, not guessed.
- A day the earlier period doesn't have runs to the end of the day it becomes:
  Mar 31 compares with all of February, Feb 29 with all of Feb 28.
- "Show more" uses the task list's wording ("That's 1–5 of 12 — say "show
  more" for the next 5.").
- Left open: "just the won ones" after a metric answer (decision 13);
  `$dateTrunc` needs MongoDB 5.0+ — confirm Dev and Prod Atlas before
  release; the live tier of the coverage matrix (`metrics_ranking`,
  `metrics_compare`, `metrics_paraphrase`) is the user's to run.

### Phase 3 — Ratios and margin
- `win_rate` per customer / property / period: sold ÷ (sold + Lost)
  (decision 8). This **changes the existing answer** to "what's my win
  rate?", which counts current Won against Lost today, so a job leaves the
  wins when it's scheduled; the §1.9 rows and their tests change with it.
  Period: wins by `sold_at`, losses by `status_changed_at`. "won vs lost" as a
  status comparison ("how many estimates did I win vs lose?") follows the same
  rule; "Won vs Lost status" stays literal. Extends `parse_status_comparison`.
- **Gross margin across estimates**: weighted by pre-tax selling price from
  `work_item_breakdown`, not an average of percentages. It dashes when any
  included activity lacks a cost basis, as the portal does, and says how many.
  Recurring work items weight by occurrences, like `grand_total`.
- **Average markup** from `profit_margin`, weighted the same way.
- **No role gate** *(decision 3)*: anyone in the company may ask.
- Changes to the math follow CLAUDE.md's rule for the gross-margin port:
  portal and platform change together or not at all.

### Phase 4 — Other resources (lower value, cheap after the engine)
- **Line-level:** `how much have I quoted using Black Mulch?`, `how many hours
  of Foreman are in open estimates?`. Reads work items
  (`cross_resource.estimate_material_names / estimate_role_names`); `Estimate`
  has no top-level materials/labours.
- **Tasks:** overdue count by assignee, tasks per property.
- **Catalog:** average material price, priciest role, materials per category.
- **Capability help (§11.1):** "what can you calculate?" / "can you tell me my
  sales?" answer with the metrics Maple has.

### Documentation, per phase

`maple-phrasing-reference.md` is updated **in the same commit** as the code it
describes: its rows, the "Recent changes" paragraph, the section's **Open
gaps** line, the §12.3 counts and "Last updated". No entries in
`maple-phrasing-changelog.md` (not maintained since 2026-09-28).

| Phase | Phrasing reference | Also |
|---|---|---|
| 0 | §7.6 / §7.6.1: negated task edits (#762) become rows that change nothing, and a note containing "don't" still appends. §1.9: "add a note …: locate the pipeline" and "rename work item 2 to the pipeline trench" are writes, not analytics (#721). §1.8: "which estimate has the highest total?" is the sorted list (#720). §1.2: with an estimate open, "what is markup?" and "how much does mulch cost?" aren't answered from it (#719). §1.1: a customer surname that is a status word ("Min Won") and a question naming two statuses (#779, #780) | Mark the six followups RESOLVED |
| 1 | **New §1.12 "Metrics"**: every grammar entry's phrasings with the answer shape, what "won" / "sold" sum (the same set; "in Won status" is literal), tax-inclusive vs. "before tax", calendar periods in the user's time zone, which date a period filters (`sold_at` for won/sold, `status_changed_at` for another status, `created_at` without). §1.1 row 323 ✅. §1.8 row 734 ("Elm House") ✅. §1.9: Completed = *became* Completed in the last 30 days (decision 5); note the list filters are still rolling. The collision reject rows as ✅ "not a metric" rows in §1.2, §5.8 and §10.3 | CLAUDE.md: `services/maple_metrics.py`, `status_changed_at` / `sold_at` and their helper, what "won" means (decision 8), the rule that a status write goes through it, and the `updated_at` fallback for older estimates. Portal: the Completed card's tooltip (`DashboardPage.tsx:302`) says "marked Completed in the last 30 days" — copy only. `users_guide.md` §7.1 already says "marked Completed", which the code now matches; Maple's help answers "how is the completed value calculated?" from it (§1.9) |
| 2 | §1.12: rankings, breakdowns, period comparisons and their follow-ups ("and last year?", "the second one") | — |
| 3 | §1.9: the win-rate and won-vs-lost rows change to the sold set. §1.12: win rate by customer / property / period, gross margin and average markup across estimates, and when margin dashes | CLAUDE.md pricing section: the cross-estimate margin weighting |
| 4 | §8 line-level metrics; §7 task metrics; §4 / §5 catalog metrics; §11.1 capability answers | — |

## 5. Risks

| Risk | Handling |
|---|---|
| Wrong money answer given confidently | Replies name statuses, scope and period; seeded-database answer tests (`test_estimate_list_answers.py` style) pin exact totals |
| A status write path skips `status_changed_at` / `sold_at` | One helper plus the guard test |
| Older estimates fall back to `updated_at`, which moves on any edit | Accepted (no backfill); only status-plus-period questions are affected, and the set shrinks as statuses change; optional backfill described in 1a |
| Dashboard and Maple disagree | One engine for both; parity tests; the Completed card and Maple move together (decision 5) |
| "Customer" = contact, but money lives on properties | Sum via `Property.contacts`, dedupe estimate ids, test a two-contact property and a two-property contact |
| Division totals overstated | Work-item sums only; test a two-division estimate |
| Tax and recurrence surprise the user | Tax-inclusive by default with a "before tax" phrasing (decision 6); recurring items say so in the reply |
| A company-wide question answered from the record in focus | #719 in Phase 0; the focus rule in §3; tests with an estimate and a property open |
| Routing regressions from new patterns | Phase 0 first; reject rows per collision above; reviewed snapshot diff |
| Time-zone edge ("this month" at 8 p.m. on the 31st) | User's zone from `client_context`; a test at a month boundary |
| Whole-document loads on a hot path | `$group` for estimate-level; projections for work-item-level; new index |
| LLM-parsed spec is wrong or injected | Enum-constrained, Pydantic-validated; the LLM never sees or produces a number |

## 6. Suggested order

1. Phase 0 (#762, #721, #719, #720, #779, #780), a day or a little more.
2. Phase 1a (`status_changed_at`, helper, guard test, Maple audit),
   then 1b (engine, consolidation, scoped totals). Ships the lifetime-won
   example.
3. Phase 2, then Phase 3.
4. Phase 4 opportunistically.

Independent quick wins to batch alongside, none blocked on the above: the five
estimate status verbs (`approve`, `reject`, `send for review`, `move to draft`,
`put {title} on hold`, §1.4), which would go through the new status helper once
it exists; "when was {EST/title} created / last updated" and "what's the ID"
(§1.2 rows 360–362, answered by `focus_questions.py`); the task bare-title
forms (§7, five rows).

## 7. Review, 2026-09-30

A check of the first draft against the code changed these points:

| First draft said | Code shows | Now |
|---|---|---|
| Set `status_changed_at` in a `before_event` | Every status write is a `.set()`, which skips `before_event` | Shared helper at each write site, plus a guard test (1a) |
| Backfill from `updated_at` | Not needed for correctness once readers fall back to `updated_at` | Dropped (user, 2026-09-30); fallback in the query; Maple transitions audited from now on |
| `$match` + `$group`, nothing loads whole documents | Division, margin and recurrence math is Python | `$group` for estimate-level figures, projections for work-item figures |
| Division = filter `job_items.division`, sum totals | That overstates a multi-division estimate; the dashboard sums work items | Division sums work items |
| Five places sum totals | Six | Six, all consolidated |
| Periods unspecified | List filters are rolling UTC, the dashboard is calendar UTC, tasks use the user's zone | Calendar, user's zone (decision 7) |
| Intent `metric_query` | `followup.py` only replays `get_`/`list_`/`count_`/`analytics_` intents | `analytics_metric` |
| Collisions not listed | "how much", "average", "total", superlatives already belong to other features | Reject rows listed in §3 |
| Metric counts | `list_estimates` already counts correctly, scoped and remembered | Counts stay there |
| Dashboard unaffected by the new date | The Completed card filters Completed estimates by `updated_at` | Decision 5 |
| Tax not mentioned | `grand_total` includes tax and recurrence occurrences | Decision 6 |
| Example reply named Won, Scheduled, Completed | Contradicted decision 1 at the time | Correct again after decision 8 |
| Nothing on public Maple, capability help, anchoring a single answer | All three are reachable | Added (§3, Phase 4) |
| Deploy order: backfill before the reader | A missing value would read as empty | Reader falls back to `updated_at`; no deploy step |

**Second round** (same day, after decisions 5–7 and dropping the backfill):

| Gap | Found | Now |
|---|---|---|
| "Won" only vs. the status lifecycle | Won → Scheduled → Completed, so a Won-only total drops completed work and shrinks as jobs finish; the existing win rate (`text_helpers.py:629`) counts current Won vs Lost and has the same flaw | Decision 8 (option A), plus `sold_at` so "won this month" is the win date |
| #719 not in Phase 0 | With an estimate open, `focus_questions.py` answers "what is markup?" or "how much does mulch cost?" from it; "what's my average markup?" would be next | Merged with #720 in Phase 0 |
| No subject from focus | "this property", "them", or the property open on the page had no rule | §3 |
| Empty vs. not found | Not specified; an average over nothing divides by zero | §3 |
| Period comparisons | "this month vs last month", "am I up on last year?" had no home | Phase 2 |
| Completed card copy | The tooltip reads "in Completed status over the last 30 days"; the guide already says "marked Completed" | Phase 1 docs row |
| Recurring items, rounding, LLM usage tag | Unstated | §3 |

Checked and fine: estimate reads are company-wide for every role (no Member
scoping in `routers/estimates.py`), so decision 3 exposes nothing the portal
hides. Maple has no entry point outside the portal that lacks a time zone,
other than tests. `_COMMAND_LEAD` and `match_command`, which Phase 0 relies on,
exist.

## 8. Decisions

All made 2026-09-30.

1. ~~"Won" = status Won only~~ — superseded by 8. "Sold" stays Won +
   Scheduled + Completed.
2. Add `status_changed_at` now, with **no backfill**: a missing value falls
   back to `updated_at`.
3. No role gate on metric, margin or cost questions.
4. #762: anchor the task edit patterns with `_COMMAND_LEAD`, no negation rules.
5. **Dashboard Completed card** switches to estimates *completed* (by
   `status_changed_at`) in the last 30 days, and Maple's "completed value"
   with it, in the same change (Phase 1b, when `compute_analytics` moves onto
   the engine). Pipeline stays on `updated_at`; Backlog stays all-time. The
   card's label is unchanged; the parity tests are updated to the new meaning.
6. **Tax.** Money answers are tax-inclusive (`grand_total`), matching the
   dashboard. "Before tax" / "pre-tax" / "excluding tax" is a supported
   phrasing, summing work-item pre-tax revenue. Margin is always pre-tax.
7. **Calendar periods** for metrics: "this month" is since the 1st, in the
   user's time zone (UTC when the portal sent none). List filters stay rolling
   for now; moving them is a separate change.
8. **"Won" in money and win-rate questions = the sold set** (option A,
   superseding 1). A won job is one the customer said yes to: Won + Scheduled
   + Completed. "In Won status" / "currently Won" is the literal status. Win
   rate = sold ÷ (sold + Lost). A period on won/sold filters `sold_at`, added
   in Phase 1a. Counts and lists of "won estimates" stay Won-only for now.

Phase 2 decisions, also 2026-09-30:

9. **A ranking with no measure named ranks by sold value** (Won + Scheduled +
   Completed, decision 8), and the reply says so. "Most estimates" / "most
   jobs" ranks by count.
10. **A period comparison with no measure named compares sold value.** The
    reply names how many estimates each figure covers, as every metric reply
    does.
11. **Like with like by default.** "This month vs last month" on Sept 15 is
    Sept 1–15 against Aug 1–15; "all of last month", or a current period that
    is over, compares whole periods. The reply names the days.
12. **List size:** 5 when no number is given, at most 25; "show more" pages.
13. **"Just the won ones" after a metric answer** is a gap for now (phrasing
    reference ⚠️), not part of Phase 2.
