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

## Deferred — not on the fix list

These were considered and intentionally NOT filed as follow-ups:

- **CORS wildcard in dev**: already guarded — production fail-fast landed in
  the critical batch. The wildcard fallback in development is intentional.
- **`ChangeLogEntry` lacking tenant scope**: intentionally global; documented
  in the model's docstring.
- **Firebase/Brevo credentials in `.env`**: correct pattern. Only the
  service-account-key on disk was problematic, and that was rotated.

---

## How to work through this

1. Pick ONE HIGH item per work session. Don't batch.
2. Write the failing test first (TDD per `CLAUDE.md`).
3. Run the related test file, not the full suite.
4. Commit each item as its own PR — easier to revert, easier to review.
5. Delete the bullet from this file in the same PR.

When this file is empty, delete it.
