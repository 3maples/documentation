# Code Review Follow-ups

Follow-up tracker for HIGH and MEDIUM issues surfaced by `/code-review`.
Originally captured on 2026-04-19 after the 18 CRITICAL findings from that
pass were fixed; refreshed 2026-04-20 with new findings from the
material-categories change.

Treat this list as a punch-list, not a sprint plan. Pick what's valuable when
touching the affected area. Items are ordered by impact within each severity.

---

## HIGH

### 0. Bare `except Exception` in material-agent category filter + estimate CRUD handlers
**Files**: `agents/material/service.py`, `agents/estimate/service.py`
**Lines**: material ~980 and ~987 (inside `_resolve_category_filter`); estimate
~2949 and ~3024 (inside `_handle_list_estimates` / `_handle_get_estimate`,
around the `PydanticObjectId(company_id)` coercion).

**Why it matters**: same class of defect as the ones narrowed in the
2026-04-19 critical sweep. The first except catches the `PydanticObjectId`
cast failure (should be `(InvalidId, TypeError)`). The second catches
`MaterialCategory.find(...)` failures and silently returns `None`, which the
caller interprets as "no category filter" — so a MongoDB outage would degrade
a filtered list request into an *unfiltered* one with no log. User sees every
material in the catalog instead of the filtered subset they asked for.

The estimate variant (added 2026-04-20 in the Estimates drilldown) re-uses the
same broad `except Exception` pattern for the `PydanticObjectId(company_id)`
coercion. The Beanie query failures in those handlers were fixed in the same
review (they now return an error envelope), so only the coercion except
remains.

Fix:
- Narrow the first except to `except (InvalidId, TypeError)` (import from
  `bson.errors`).
- On the second except, `logger.exception(...)` and re-raise — or at minimum
  log and return an explicit sentinel that the caller treats as "DB unhappy,
  surface a friendly error" rather than silently unfiltering.
- Same review also flagged an unchecked `PydanticObjectId(company_id)` in the
  `list_material_categories` branch at ~line 1944 — validate once at the top
  of `process()` rather than letting `InvalidId` bubble into a 500.
- Apply the same narrow-except treatment to the new estimate handlers.

### 1. Async hygiene in route handlers
**Why it matters**: blocking calls inside `async def` freeze the event loop —
other requests stall for the duration of the blocking call.

- `services/google_drive_service.py` — the `googleapiclient` client is
  synchronous; all Drive/Docs calls inside `async def` route handlers
  (`routers/estimates.py` Drive folder + Doc endpoints) block the loop. Wrap
  with `asyncio.to_thread(...)` or switch to an async Drive client.
- Audit `routers/` for `requests.get`, `time.sleep`, and any sync DB drivers
  inside `async def`. Known suspects: any code path that calls
  `GoogleDriveService._initialize()` or `httpx.Client` (sync) — use the async
  `httpx.AsyncClient` instead.
- `fetch_link()` inside loops — known N+1 pattern. Replace with a single
  `fetch_all_links=True` fetch or a manual `$in` batch query. Grep for
  `fetch_link` inside `for`/`async for` bodies.

### 2. Per-company rate limiting — Google Maps
**File**: `services/address_service.py`
**Scope**: `autocomplete`, `resolve_place_id`, `normalize_address_parts`
**Why it matters**: without per-tenant throttling, one company can exhaust the
platform-wide Google Maps quota and deny service to all other tenants. Also
protects against accidental runaway retries in an agent loop.

Implementation sketch:
- Thread `company_id: str` through each public method signature.
- Wire `services/request_protection.py`'s existing limiter (the same primitive
  `auth_rate_limiter` uses) keyed by `f"maps:{company_id}"`.
- Caller audit: `routers/addresses.py` already has `company_id` from auth
  context, so threading is local. Add a test that confirms a second request
  within the window gets a `429`.

### 3. Type hints on public functions
Scattered across `routers/` and `agents/`. The ones that matter are public
functions exported across package boundaries — start with:
- `agents/orchestrator/service.py` — `process()` and the rule/intent helpers
- `agents/estimate/service.py` — public methods called from routers
- `services/` — any module exporting a function consumed by a router

Tooling: `mypy . --ignore-missing-imports` will surface the list. Consider
adding mypy to CI once the baseline is clean.

### 4. File and function size
Files over the 800-line HIGH threshold:
- `routers/agents.py` — 2670 lines. Orchestrate/estimate endpoints are
  ~300 lines each. Candidates for extraction:
  - The fuzzy-confirmation state machine (pending intent store, match lookup,
    confirm/deny routing) → its own module under `routers/agent_helpers/`.
  - The follow-up-stage machinery (property-select, confirm, optional value)
    → separate from the top-level dispatch.
- `agents/material/service.py` — 2078 lines. `process()` is a mega-switch
  that inserts a new 50-line inline handler per intent. Easiest extraction
  target: the recently-added `list_material_categories` block
  ([service.py:1942](../../platform/agents/material/service.py:1942)) → a
  `_handle_list_material_categories()` method. Apply the same pattern to the
  other branches over time.
- `agents/estimate/service.py` — ~3500 lines after the 2026-04-20 Maple CRUD
  handlers landed. Similar split: prompt-building / inventory fetch / LLM
  extraction / totals calc / CRUD read handlers are each their own concern.
  Cleanest first cut: move the new CRUD methods
  (`_handle_list_estimates`, `_handle_get_estimate`, `_crud_envelope`, plus
  the small parsing helpers) into `agents/estimate/crud.py` as a mixin.
- `agents/orchestrator/service.py` — 1007 lines. Not the worst, but the
  `_classify_with_rules()` and `process()` methods both duplicate the
  same short-circuit patterns (see MEDIUM #12 below).

No function in this repo should exceed 50 lines. Grep for long bodies with
a line-count tool after each refactor pass.

### 5. Pydantic validation on router inputs
Grep pattern: `request: Request` or raw `dict` in a POST/PUT handler. Each one
is an opportunity to define a Pydantic model and move validation out of the
handler body. Start with any handler that reaches into `await request.json()`
directly.

### 6. Mutable default arguments
Scattered `def f(x=[])` / `def f(x={})` — classic Python gotcha. A single PR
can sweep all of them. `ruff check` with `B006` enabled finds them for free.

### 7. Missing tests for new public functions
Per `CLAUDE.md` mandatory-testing rule. To identify gaps: for each new public
function added in the last N commits, verify there's a corresponding
`tests/test_<module>.py::test_<fn>`. A `coverage report` run against
`routers/` and `agents/` will spotlight the red lines.

---

## MEDIUM — ~45 findings

Cosmetic / hygiene. Safe to batch into a single "chore: code hygiene" PR, or
clean up opportunistically when editing a file.

### 8. `print()` → `logging`
Any `print()` left in `services/`, `routers/`, `agents/`, or `models/`. Keep
`print()` in `scripts/` (operator-facing CLIs) — that's appropriate there.

### 9. Magic numbers → named constants
Examples found: timeout values, quota limits, retry counts, score thresholds.
Give each a module-level constant with a short comment explaining its source.

### 10. Missing docstrings on public APIs
Focus only on functions exported across package boundaries. Don't docstring
private helpers — named variables beat comments.

### 11. TODO / FIXME triage
Grep for `TODO` and `FIXME` added in recent changes. Each should either:
- be resolved, or
- be converted into a GitHub issue with a link back to the code.
Comments that just say "TODO" with no owner / date / issue will rot.

### 12. Duplicated short-circuit logic in the orchestrator
**File**: `agents/orchestrator/service.py`
The `_classify_with_rules()` method and the top of `process()` both match the
same regex patterns (list-categories, bulk-delete refusal, equipment refusal,
material-category-management refusal) and build near-identical result dicts
in each branch. Two code paths can drift — a phrasing fixed in one can still
misroute through the other.

Fix: extract a single `_try_policy_short_circuits(message) ->
Optional[Result]` helper and call it from both entry points. Same applies to
the list-categories pattern match.

### 13. Mutation where immutable return would be clearer
Case-by-case judgment. Only refactor if it actually simplifies the reader's
job; don't chase stylistic purity.

---

## 2026-04-22 review (Maple estimate flow session)

MEDIUM and LOW findings from the `/code-review` pass after the tax / division
/ description / work-item-delete work. The HIGH finding from that pass
("last work item" inconsistency) was fixed in the same session; these are
the residuals.

### 14. Unused `ESTIMATE_GENERATION_PROMPT` import
**File**: `agents/estimate/service.py:15`
**Severity**: MEDIUM (hygiene)

The module-level `ESTIMATE_GENERATION_PROMPT` constant is imported but never
referenced — only `build_estimate_generation_prompt()` function calls are
used (lines 446, 2008, 4830). Pre-existing; surfaced during investigation of
why prompt edits weren't taking effect.

Fix: drop the import.

### 15. Split Example block may anchor LLM back to terse descriptions
**File**: `prompts/estimate_generation.py`, ~lines 99-109
**Severity**: MEDIUM (prompt quality)

Rule 4d now requires 1-2 sentence (~15-40 word) descriptions with materials,
sizes, and method. The Split Example block still shows short labels like
`Paver patio installation`, `Low-voltage landscape lighting installation`,
`Lawn refresh and grading`. LLMs latch onto examples as implicit targets, so
these short labels may be undermining rule 4d's guidance.

Fix: rewrite each Split Example entry to the richer 4d shape, e.g.
`Paver patio installation — 400 sq ft porcelain pavers on compacted base
with edge restraints and polymeric sand joints`. Low effort, likely
meaningful impact on what Maple actually emits.

### 16. Delete-button propagation on touch devices
**File**: `portal/src/pages/NewEstimateWithActivityPage.tsx` (trash button
per work item row)
**Severity**: LOW (needs manual verification)

The row has an `onClick` that opens the work-item editor, and the trash
button inside the row calls `e.stopPropagation()`. On some touch devices a
long-press can fire both `pointerdown`/`click` paths and both handlers run.
Not verifiable from source — needs a mobile-browser test.

Fix (if the test shows leakage): add
`onPointerDown={(e) => e.stopPropagation()}` alongside the existing
`onClick` on the trash button.

### 17. Architect prompt rule 5 still mentions "quantities" ambiguously
**File**: `prompts/estimate_architect.py`, rule 5
**Severity**: LOW (prompt quality)

Rule 5 now says "DO NOT include prices, labour rates, or inventory IDs/SKUs.
Sizes and quantities … ARE allowed." A stricter LLM may read the word
"quantities" as still-discouraged overall, because this rule used to ban all
quantities.

Fix: tighten to "DO NOT include prices, labour rates, inventory IDs, or
**purchase quantities** (how many to buy). Scope-describing sizes,
dimensions, coverage area, linear feet, and spacing ARE allowed."

### 18. File-size threshold — `agents/estimate/service.py` now at 5,098 lines
**Severity**: MEDIUM (architectural drift)

Entry #4 above already flags the HIGH-threshold files. Updating the
numbers: after the 2026-04-22 session, `agents/estimate/service.py` is now
~5,098 lines, `routers/agents.py` is ~2,892, `routers/estimates.py` is
~2,548. The extraction plan in entry #4 still applies; nothing added this
session is individually large, but the pile keeps growing.

---

## 2026-04-22 second review (six-phrasing coverage session)

HIGH tenant-leak (`_resolve_latest_estimate` unscoped fallback) and the
notes-overwrite safety finding were fixed in the same session. Residuals
below were deferred per reviewer direction.

### 19. `_handle_get_work_item` is 112 lines
**File**: `agents/estimate/service.py:4385-4497`
**Severity**: HIGH (code hygiene, per the 50-line threshold)

The handler mixes estimate-loading, not-found / DB-error branches, work-item
resolution, and response formatting in a single body. Consistent with other
oversized handlers in this file (see entry #4) but the new landing for
get-work-item work is a clean place to start the extraction pattern.

Fix: extract `_load_estimate_for_read(query, company_id, context)` returning
`(target, error_envelope)` (mirroring `_load_estimate_for_update`), and
split the response formatting into `_build_work_item_details_text(idx,
item)`. Handler body should shrink to ~30 lines. Same treatment applies
to `_handle_get_estimate` now that the latest-estimate logic landed.

### 20. Narrow `except Exception` in the latest-estimate resolver's ObjectId cast
**File**: `agents/estimate/service.py` — the first of two `except Exception`
clauses in `_resolve_latest_estimate` (around line 3266 post-fix).
**Severity**: MEDIUM (hygiene, matches entry #0 of the original batch)

The `PydanticObjectId(company_id)` cast is wrapped in `except Exception:
return None`. Only `InvalidId` / `TypeError` can arise from a bad cast, so
broadening to `Exception` masks unrelated failures.

Fix: narrow to `except (InvalidId, TypeError)` (import from `bson.errors`).
Keep the second broad-except (around line 3277 post-fix) — it logs via
`logger.exception` so a surprise failure is still observable.

### 21. Module-scope vs. method-scope inconsistency for note/work-item helpers
**File**: `agents/estimate/service.py`
**Severity**: MEDIUM (style)

`_detect_note_update`, `_is_property_link_request`, and
`_detect_status_transition` are all instance methods on the agent class,
but `_detect_get_work_item_request` and `_parse_work_item_position` live at
module scope. Callers have to know which helper is where.

Fix: promote the two module-level helpers to methods, or demote the three
instance methods to module functions and thread any needed state through.
Low effort; no behavior change.

### 22. "Last estimate" with zero estimates falls back to generic "Which estimate?"
**File**: `agents/estimate/service.py` — the `_handle_get_estimate` branch
that falls through when `_resolve_latest_estimate` returns `None`.
**Severity**: LOW (UX polish)

When a user asks "what is the grand total for the last estimate" and the
company has no estimates yet, the handler shows the generic "Which
estimate? Please share the estimate code (e.g. EST-2026-001)." prompt.
Correct behavior but confusing for a new user.

Fix: detect the latest-estimate intent (via `_looks_like_latest_estimate_query`)
before the generic clarification and respond with "You don't have any
estimates yet."

### 23. `_NOTE_WITH_IMPLICIT_TAIL` can false-positive on descriptive phrasings
**File**: `agents/estimate/service.py` — the `_NOTE_WITH_IMPLICIT_TAIL`
regex inside `_detect_note_update`.
**Severity**: LOW (edge-case UX)

The pattern `\b(?:with|add(?:ing)?|append(?:ing)?)\s+(?:a(?:nother)?\s+)?
notes?\s+(?P<value>.+?)\s*$` will match phrasings like "update estimate X
with notes about the call" and capture "about the call" as a note body.
Very unlikely in practice (users rarely ask Maple to describe things), but
the capture is silent so a false positive would append unwanted text to
the estimate.

Fix: require a cue token after `note/notes` signaling that a value is
coming — e.g. a quote, a colon, or a preposition like `to`/`saying`/
`that reads`. Or fall back to the quoted-only path when the implicit tail
looks descriptive.

---

## 2026-04-22 third review (external warnings triage)

Eight warnings raised by an external pass; each verified against current
source before filing. One was a hallucination and is noted under Deferred.

### 25. Regex email lookup in `_resolve_user()`
**File**: `dependencies.py:17-26`
**Severity**: MEDIUM

Email is `.lower()`'d at line 17, then looked up with
`User.find_one({"email": {"$regex": f"^{escaped_email}$", "$options": "i"}})`
at line 25-26. The case-insensitive regex defeats index usage on the
`email` field and runs on every authenticated request. `User.email` in
`models/user.py` is stored without normalization, so the regex is defending
against historical mixed-case data rather than the current write path.

Fix: two-step. (a) Add a one-shot backfill script under
`scripts/` that lowercases `User.email` for all existing rows. (b) Normalize
on write (override `__init__` / validator so any create or update lowercases
the field). (c) Replace the regex with `User.find_one(User.email == email)`.
Don't do (c) before (a) — a stray capitalized row would silently fail auth.

### 26. `find_contacts_by_name` fetches whole company, filters in Python
**File**: `agents/contact/utils.py:158-170`
**Severity**: MEDIUM

`Contact.find(Contact.company == ...).to_list()` pulls every contact for
the tenant, then lines 163-170 iterate and match names in Python. Fine at
dozens of contacts; degrades linearly with tenant size.

Fix: push the name match into Mongo. Either a `$regex` with
`^<escaped>$` and `$options: "i"` (bearable here because the query is
per-tenant-scoped and low-frequency), or — better — a case-insensitive
collation index on `first_name` / `last_name` with an equality query. If
fuzzy matching is required, keep the Python filter but pre-narrow with a
Mongo text-ish prefix filter so the in-memory set is small.

### 27. Inefficient merge pattern in bulk work-item endpoint
**File**: `routers/agents.py:1621-1632`
**Severity**: LOW (code clarity)

The code calls
`merge_job_items_with_original_descriptions([], new_job_items_raw, ...)`
with an empty first argument, which turns the helper into a no-op, then
manually appends the parsed items to `target_estimate.job_items`. The
helper at `routers/estimates.py:404-415` is designed for reconciliation
between an existing request list and newly parsed items — passing `[]`
bypasses that contract. Canonical usage is in `prepare_generated_estimate`.

Fix: either call the helper with the real existing items (if reconciliation
is wanted) or drop the call entirely and just build items from
`new_job_items_raw` via `build_job_items_from_parsed`. Works fine today; the
concern is that the next reader will assume reconciliation is happening.

### 28. Unbounded `ChangeLogEntry.find_all()`
**File**: `routers/change_logs.py:23-26`
**Severity**: LOW

`ChangeLogEntry.find_all().sort(...).to_list()` with no `.limit()`. Current
volume is small (curated changelog), so this is an anti-pattern waiting to
bite rather than an active problem.

Fix: add `.limit(100)` and accept an optional `?limit=` / `?offset=` query
param. Cheap to do; reviewer should have filed as LOW, not WARNING.

### 29. `update_estimate` recalculates totals on any `job_items`-present edit
**File**: `routers/estimates.py:1868-2016`
**Severity**: LOW (likely won't fix)

When `payload.job_items is not None`, the handler recalculates the entire
estimate's totals — even if the client sent back unchanged items alongside a
notes/title edit. Overhead is real but CPU-bound and negligible at normal
estimate sizes.

The reviewer framed this as waste, but the *safer* reading is that
gating recalculation on change-detection would risk stale totals if the
change-detector missed a case. Leave alone unless profiling shows latency.
Filed so we don't re-litigate.

### 30. `[A-Z]{2}` with `re.IGNORECASE` for state-code parsing
**File**: `agents/property/service.py:520` (regex) and `:527` (flag)
**Severity**: LOW (nit)

The compiled pattern matches any two-letter substring when run with
`IGNORECASE` — "in", "or", "to", "me" all pass. In practice the match runs
against address-shaped input and the result flows through
`_normalize_prov_state_token` (`service.py:298-323`) which does additional
validation, so false positives in free prose aren't reaching users.

Fix (when touching this file): drop the `IGNORECASE` flag and match
`[A-Z]{2}` strictly, or validate the token against a `VALID_STATES` /
`VALID_PROVINCES` set inside `_normalize_prov_state_token`. No hurry.

---

## 2026-04-22 fourth review (post-#24 bulk-fetch fix)

Follow-ups from the `/code-review` pass on the #24 fix (bulk-fetch in CSV
upload handlers). The fix itself is good — these are residuals that didn't
warrant blocking the commit.

### 31. Intra-CSV duplicate rows now upsert silently instead of erroring
**Files**: `routers/equipments.py:148-170`, `routers/labours.py:204-229`
**Severity**: MEDIUM

Before the #24 fix, a CSV with two rows sharing the same `(name, unit)`
would insert the first and crash the second (captured into `errors[]`).
After the fix, the handler registers each newly-inserted row back into
`existing_by_key`, so the second occurrence upserts the first. The behavior
is arguably friendlier, but (a) it's undocumented, (b) no test exercises
it, and (c) the response payload reports N `created` IDs for an N-row
upload even when the user effectively paid for duplicate rows.

Fix: pick one of — (i) add a test pinning the new upsert-on-duplicate
behavior; (ii) or revert to the pre-fix error behavior by omitting the
`existing_by_key[(name, unit)] = row` registration line. If staying with
(i), consider splitting the response into `created` vs `updated` lists so
the caller can see what actually happened (materials.py already does this).

### 32. `hasattr(l.unit, "value")` defensive check with unclear motivation
**File**: `routers/labours.py:202`
**Severity**: MEDIUM

`existing_by_key = {(l.name, l.unit.value if hasattr(l.unit, "value") else l.unit): l for l in candidates}` —
the `Labour.unit` field is typed as `LabourUnit` enum in the model, so
`.value` should always work. The `hasattr` fallback either (a) defends
against legacy string-valued rows in prod, or (b) is defensive coding
without cause. If (a), document it; if (b), drop it.

Fix: grep production data once to check whether any `Labour` rows have
`unit` stored as a raw string. If none, simplify to `l.unit.value`. If
some, add a one-line comment and file a data-migration task.

### 33. `$in` × `$in` bulk-fetch over-fetches the cross-product
**Files**: `routers/equipments.py:138-144`, `routers/labours.py:195-201`
**Severity**: MEDIUM (theoretical) / LOW (in practice)

For a CSV with N distinct names and M distinct units, the query
`{"name": {"$in": names}, "unit": {"$in": units}}` matches every name ×
unit combination in Mongo — up to N×M rows — even though only exact-tuple
matches are used. The Python-side filter `existing_by_key.get((name, unit))`
discards the extras. Harmless for typical CSVs (one unit type, many
names), grows quadratically with mixed CSVs.

Fix (when it bites): switch to `{"$or": [{"name": n, "unit": u} for ...]}`
— exact tuples, no bloat. Not worth doing until we see a CSV where this
matters.

### 34. Missing type hint on `existing_by_key` dict
**Files**: `routers/equipments.py:136`, `routers/labours.py:193`
**Severity**: LOW

Materials.py added the annotation (`existing_by_key: Dict[str, Material] = {}`);
equipments.py and labours.py did not. Consistency gap introduced by the
same commit.

Fix: `existing_by_key: Dict[Tuple[str, str], Equipment] = {}` (and
similarly for Labour). Import `Dict, Tuple` from typing.

### 35. `names` list in materials bulk-fetch may contain casing duplicates
**File**: `routers/materials.py:295`
**Severity**: LOW

`names = [md["name"] for md in grouped.values()]` — `grouped` is keyed by
`name.lower()`, so names are unique by casefold but not by original
casing. A CSV with both `"Patio Stone"` and `"patio stone"` would produce
two `$in` entries that both resolve to the same Mongo row.

Fix: `list({md["name"] for md in grouped.values()})`. Micro-optimization;
skip unless already editing the file.

---

## Deferred — not on the fix list

These were considered and intentionally NOT filed as follow-ups:

- **CORS wildcard in dev**: already guarded — production fail-fast landed in
  the critical batch. The wildcard fallback in development is intentional.
- **`ChangeLogEntry` lacking tenant scope**: intentionally global; documented
  in the model's docstring.
- **Firebase/Brevo credentials in `.env`**: correct pattern. Only the
  service-account-key on disk was problematic, and that was rotated.
- **Duplicate `getEstimateDivision` in DashboardPage + EstimatesTable**
  (2026-04-22 third review): verified and rejected. No such function
  exists anywhere in `portal/`. Division aggregation lives only in
  `DashboardPage.tsx:169-184` as a `useMemo`; `EstimatesTable.tsx` is a
  generic props-driven table with no division logic. No `divisionBadge.ts`
  file exists. Reviewer appears to have described a state of the code
  that is not present in this repo.

---

## How to work through this

1. Pick ONE HIGH item per work session. Don't batch.
2. Write the failing test first (TDD per `CLAUDE.md`).
3. Run the related test file, not the full suite.
4. Commit each item as its own PR — easier to revert, easier to review.
5. Delete the bullet from this file in the same PR.

When this file is empty, delete it.
