# Maple Phrasing Expansion — Design Spec

**Date:** 2026-06-02
**Status:** Approved (design); pending implementation plan
**Scope:** Four new Maple phrasing capabilities + landscaper-friendly adjacent metrics, with the phrasing-reference doc kept in sync and duplicates removed.

## Goal

Extend Maple's deterministic (rule-tier) coverage with phrasings landscapers actually type:

1. **Status comparisons / ratios** — "what is my won-lost ratio?" and generic "X vs Y" status comparisons.
2. **Age filter** — "show me estimates that are X days old".
3. **Material qualifier list** — "what {X} materials do I have?" (partial match on name + category, shows the list).
4. **Status filter via `in`** — "find estimates in {status}".

Plus adjacent, non-technical metrics (win rate over a window, count-in-status, materials-by-category count). Audience is non-technical (landscapers) — all phrasings and response copy must read naturally.

## Approved decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Ratio basis | **Generic status-vs-status**, count-based. WON-vs-LOST is the default when no statuses named. Headline phrasing "won-lost ratio". |
| Ratio architecture | **Approach A** — extend the existing analytics path (`_match_analytics_query` → `analytics_estimates` → `compute_analytics`). |
| "X days old" semantics | **At least X days old**, measured against `updated_at`. |
| Age consistency | **Both** age phrasings (`older than X days` AND `X days old`/stale) use `updated_at`. Relative date-range phrasings (`from last week`, `this month`) stay on `created_at`. |
| Material qualifier `{X}` | Substring match against **name OR category**; show the matching list. |
| Coverage scope | The 4 asks + **adjacent metrics**, all in landscaper-friendly phrasing. |

---

## Section 1 — Status comparisons / ratios (Estimates)

**Routing.** Add ratio/comparison detection to `_ANALYTICS_PATTERNS` + `_match_analytics_query` in `agents/orchestrator/service.py`. A query matches when it contains a ratio/comparison cue — `ratio`, `win[/ -]loss` / `won.*lost`, `versus` / `vs`, `compared to`, `win vs lose` — optionally naming two `EstimateStatus` values. The parsed payload is tagged `analytics_kind="comparison"` with the two resolved statuses (default WON vs LOST).

**Computation.** `compute_analytics()` (`routers/estimates.py`) gains a comparison branch: count estimates per status, honoring any time window from `_parse_estimate_date_filter`. Returns `{a_status, a_count, b_status, b_count, ratio_text, win_rate_pct}`. `ratio_text` is reduced-or-raw counts (e.g. `12:5`); `win_rate_pct` is `a / (a + b)` only when the pair is WON/LOST.

**Response.** Estimate Agent formats landscaper-friendly copy:
- WON/LOST: *"You've won 12 and lost 5 — that's a 12:5 win-loss ratio (about 71% win rate)."*
- Other pairs: *"You have 8 in draft and 3 approved — a 8:3 ratio."*
- Zero-denominator: graceful copy (e.g. *"You've won 4 and haven't lost any yet."*).

**Touch points:** `agents/orchestrator/service.py` (`_ANALYTICS_PATTERNS`, `_match_analytics_query`), `routers/estimates.py` (`compute_analytics`, `AnalyticsResponse`), Estimate Agent analytics handler.

---

## Section 2 — Age filter "X days old" (against `updated_at`)

**Parsing.** Extend the age pattern in `agents/estimate/text_helpers.py` to also match `X days/weeks/months old` and natural variants: `that are 30 days old`, `aged 2 weeks`, `untouched for 30 days`, `not touched in a month`, `haven't been updated in 30 days`. Semantics: **at least X days old** → `(None, cutoff)` window.

**Field selection.** `_parse_estimate_date_filter` is extended to also return the target field. Both age phrasings (existing `older than X days` and new `X days old`/stale) target `updated_at`. Date-range phrasings keep `created_at`. The list handler (`agents/estimate/crud_handlers.py::_handle_list_estimates`) applies the `$gte/$lte` window to the returned field.

**Touch points:** `agents/estimate/text_helpers.py` (`_AGE_FILTER_PATTERN` + sibling, `_parse_estimate_date_filter` return shape), `agents/estimate/crud_handlers.py` (apply window to selected field).

---

## Section 3 — Status filter via `in` + coverage

**Parsing.** Add `in` as a recognized connector in `_estimate_status_from_text()` (`agents/estimate/crud_helpers.py`), firing only when the token after `in` resolves to a known `EstimateStatus` alias (so `estimates in Toronto` still routes to the property cross-resource path). Supported: `find estimates in draft`, `estimates in won status`, `show me the estimates in review`.

**Coverage additions** (compose with existing date/amount/property qualifiers — no new stacking code): `show me draft estimates`, `which estimates are in draft`, `pull up my won jobs`, `what's in review`.

**Touch points:** `agents/estimate/crud_helpers.py` (`_estimate_status_from_text`), regression check against property cross-resource matcher ordering in `agents/orchestrator/service.py`.

---

## Section 4 — "What {X} materials do I have?" (name + category substring)

**Parsing.** Add a material-list pattern (in `agents/material/text_helpers.py`, picked up by `_resolve_list_name_hint`) capturing a qualifier between the lead-in and `materials`: `what {X} materials do I have?`, `show me my {X} materials`, `list my {X} materials`, `do I have any {X} materials?`, `which {X} materials do I have?`. Captured `{X}` becomes a search hint. Stopword/empty guard so `what materials do I have?` (no qualifier) still lists all.

**Matching.** Extend material list filtering so the hint matches as a **substring against name OR category** (today `_find_materials_by_name` checks name only; add an OR-combined category-substring check). Response reuses existing list/empty copy.

**Touch points:** `agents/material/text_helpers.py` (new capture pattern + stopword guard), `agents/material/service.py` (`_find_materials_by_name` / `_handle_list_materials` to OR-in category match).

---

## Section 5 — Adjacent metrics (landscaper-friendly)

- **Win rate over a window** — *"what's my win rate this month?"*, *"how am I doing on bids?"* → analytics, `win_rate` over parsed window.
- **Count in a status** — *"how many jobs are sitting in draft?"*, *"how many estimates am I waiting to hear back on?"* (→ SENT/REVIEW) → status filter + count (mostly existing plumbing).
- **Materials by category count** — *"how many hardscape materials do I have?"* → count variant of Section 4.

---

## Testing (TDD — tests written first)

| File | Coverage |
|---|---|
| `tests/test_maple_new_phrasings.py` | Orchestrator routing for all new phrasings: ratio/comparison, age-old, status-`in`, material qualifier, adjacent metrics. |
| `tests/test_estimate_agent.py` | Comparison/ratio handler output; `updated_at` age window. |
| `tests/test_estimates_analytics.py` | `compute_analytics()` comparison branch (counts, ratio_text, win_rate, zero-denominator). |
| `tests/test_material_agent.py` | Name+category substring qualifier filtering; no-qualifier still lists all. |

Run scoped: `./run_tests.sh tests/test_maple_new_phrasings.py` etc. mypy after every `.py` change (`./run_mypy.sh agents/estimate`, scoped, then full before commit-prep).

## Documentation

Update `documentation/development/maple-phrasing-reference.md`:
- §1.1 — add status-`in` and age-old rows.
- §1.9 — add ratio/comparison + win-rate rows.
- §4.5 / §4.9 — material qualifier + count-by-category.
- **Remove duplicates** — e.g. the §1.1 overlap between `show only estimates with Won status this month` and `how many estimates did I win this month?` vs the new status rows; dedupe rather than add near-identical lines.
- Add a change-log entry; bump "Last updated" to 2026-06-02; refresh §9.3 snapshot counts.

## Out of scope

- Value-based (dollar-weighted) ratios — counts only.
- LLM-tier paraphrase robustness beyond what the rules cover.
- Changing relative date-range phrasings to `updated_at` (they stay on `created_at`).
- Material qualifier matching against description (name + category only).

## Risks / watch-items

- **Connector collision:** `in` must not hijack property/location phrasings — gate strictly on EstimateStatus alias.
- **Age field split:** date-range vs age now target different timestamp fields; doc must state this clearly so future edits don't "fix" the perceived inconsistency.
- **Stopword guard:** material qualifier must not swallow the bare "what materials do I have?" list-all case.
- **Pre-help ordering:** ratio/comparison analytics must run before `is_help_query` (existing analytics path already does).
