# Code Review Follow-ups

Follow-up tracker for HIGH and MEDIUM issues surfaced by `/code-review`.
Originally captured on 2026-04-19 after the 18 CRITICAL findings from that
pass were fixed; refreshed 2026-04-20 with new findings from the
material-categories change.

Treat this list as a punch-list, not a sprint plan. Pick what's valuable when
touching the affected area. Items are ordered by impact within each severity.

---

## HIGH

### 3. mypy baseline — themed gaps (271 errors across 38 files)
Generated 2026-04-26 via `mypy . --ignore-missing-imports --explicit-package-bases`
after fixing the 7 implicit-Optional `http_request: Request = None` router
sites (the only mechanically safe category — `Optional[Request]` breaks
FastAPI's request injection, so the kept-default + `# type: ignore[assignment]`
form is the canonical fix). Remaining errors split into the themed entries
below; see [#86](#86-mypy-no_implicit_optional-defaults-on-agentestimateservicepy)
through [#90](#90-models-estimate-arithmetic-on-optional-int-fields) for
specific scopes.

Pre-fix CI gate is **not** recommended yet — too many false positives from
LangChain/Beanie type erasure. The right next move is one of:
- enable `mypy --strict` only on `services/` (the smallest, most type-clean
  package), or
- add a `mypy.ini` with the noisy categories disabled (e.g. `disable_error_code = union-attr,arg-type` while the agents are refactored).

Categories below are sorted by error count.

### 4. File and function size
Files over the 800-line HIGH threshold (line counts refreshed 2026-04-26):
- `routers/agents.py` — 2631 lines (was 2917 before 2026-04-26).
  Orchestrate/estimate endpoints are ~300 lines each. Recent extractions
  landed under `routers/agent_helpers/`:
  - `text_helpers.py` — `is_affirmative_text` / `is_negative_text` (50 lines).
  - `estimate_update.py` — `run_update_estimate` add-items flow (175 lines).
  - `fuzzy_confirmation.py` — `handle_estimate_fuzzy_confirmation` +
    `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY` (180 lines).

  Candidates for the next extraction round:
  - The follow-up-stage machinery (property-select, confirm, optional value)
    → separate from the top-level dispatch. Largest remaining inline closure
    is `_handle_pending_estimate_follow_up` (~530 lines).
  - `_handle_pending_optional_follow_up` and the small builders around it
    (`_build_optional_follow_up_prompt` / `_build_optional_follow_up_update_message`
    / `_get_optional_follow_up_spec`) — natural cluster for an
    `optional_follow_up.py` helper.
- `agents/material/service.py` — 2560 lines. `process()` is a mega-switch
  that inserts a new 50-line inline handler per intent. ~~Easiest extraction
  target: the `list_material_categories` block~~ landed 2026-04-26 as
  `_handle_list_material_categories()` (44 lines) plus a static
  `_format_material_categories_response()` helper. Follow-up extractions
  landed 2026-04-26: `_handle_create_material`, `_handle_get_material`
  (incl. size-scoped lookup), `_handle_delete_material` (post-resolve
  confirmation flow), and `_handle_list_materials` (count + category-filter
  + name-hint dispatch). `process()` is now ~680 lines, down from ~1072.
  Remaining inline blocks: the `update_material` branch (~250 lines,
  tangled with multi-turn field-then-value state + size_op resolution +
  unit-OID lookup) and the `delete_material` early-confirm shortcut that
  fires before `_resolve_target_material`.
- `agents/estimate/service.py` — 5685 lines after the 2026-04-26 #80
  refactor. Similar split: prompt-building / inventory fetch / LLM
  extraction / totals calc / CRUD read handlers are each their own concern.
  Cleanest first cut: move the new CRUD methods
  (`_handle_list_estimates`, `_handle_get_estimate`, `_crud_envelope`, plus
  the small parsing helpers) into `agents/estimate/crud.py` as a mixin.
- `agents/orchestrator/service.py` — 1257 lines (post-2026-04-25
  `_classify_with_rules` extraction). `_classify_with_rules` is now 209
  lines, down from 268, but still over the 50-line ceiling. `process()`
  still duplicates the same short-circuit patterns (see MEDIUM #12).

No function in this repo should exceed 50 lines. Grep for long bodies with
a line-count tool after each refactor pass.

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

### 20. Narrow `except Exception` around `PydanticObjectId(company_id)` cast in `_resolve_latest_estimate`
**File**: `agents/estimate/service.py` — the first of two `except Exception`
clauses in `_resolve_latest_estimate` (around line 3266 post-fix).
**Severity**: MEDIUM (hygiene, matches entry #0 of the original batch)

The `PydanticObjectId(company_id)` cast is wrapped in `except Exception:
return None`. Only `InvalidId` / `TypeError` can arise from a bad cast,
so broadening to `Exception` masks unrelated failures.

The same defect in `_load_estimate_for_update` and `_load_estimate_for_read`
was fixed in the 2026-04-26 #80 refactor by extracting the shared
`_coerce_company_oid` helper with a narrowed `except (InvalidId, TypeError)`.
The same helper can be used here.

Fix: replace the inline cast with `self._coerce_company_oid(company_id)`,
or apply the same `except (InvalidId, TypeError)` narrowing inline.
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

## 2026-04-22 fifth review (post-#1 async-hygiene fix)

Follow-ups from the `/code-review` pass on the #1 fix (Firebase wraps +
Contact N+1 batching). Same-session fixes: silent-swallow logging on
`_fetch_linked_contacts`, and a test-assertion shape cleanup on the new
batched-find test. Residuals below were deferred.

### 36. No unit test for the N+1 batch fix in `generate_google_doc`
**File**: `routers/estimates.py:2368`
**Severity**: MEDIUM

The loop → `Contact.find({"_id": {"$in": list(property_info.contacts)}})`
batch change is covered only by inspection. A targeted unit test requires
a full TestClient + Drive mock + Mongo fixtures, which is why it didn't
land in the #1 fix. The agent-level sibling (`_fetch_linked_contacts`) is
tested in [tests/test_property_agent.py](../../platform/tests/test_property_agent.py).

Fix: either (a) add a TestClient case in
[tests/test_estimate_doc_generator.py](../../platform/tests/test_estimate_doc_generator.py)
that asserts `Contact.find` is called once and `Contact.get` is never
called; or (b) extract the contact-fetch out of the route into a helper
in `services/` and test the helper directly. Option (b) has the side
benefit of letting the same helper back the Maple-side path.

### 37. `_handle_get_estimate` falls through to an unscoped `Estimate.find_one` when `company_id` is invalid
**File**: `agents/estimate/service.py` — inside `_handle_get_estimate`,
around the `if company_oid is not None: ... else: ...` branch
(~lines 3787-3794 post-fix).
**Severity**: LOW (tenant-isolation gap — narrow path, but real)

When `PydanticObjectId(company_id)` fails (invalid hex string), the
narrowed `(InvalidId, TypeError)` except sets `company_oid = None`, and
the subsequent handler runs `await Estimate.find_one(Estimate.estimate_id
== code)` — an **unscoped** query that returns any estimate in the
platform with that code. Pre-existing pattern; the #1 narrow-except
change preserved it rather than introducing it. The sibling
`_handle_list_estimates` already gates behind `company_oid is None` and
returns a clarification envelope — get_estimate should mirror that.

Fix: after the ObjectId cast, if `company_oid is None`, return a
"need a company" clarification envelope (same shape as
`_handle_list_estimates` uses) instead of running the unscoped
`find_one`. Theme-adjacent to entry #20 (narrow-except in the latest
resolver) and the tenant-leak fix that already landed for
`_resolve_latest_estimate`.

---

## 2026-04-22 sixth review (post-#2 Maps rate-limit fix)

Residuals from the `/code-review` pass on the #2 fix (per-company Maps
rate limiting + auth dep on the addresses router). The docstring MEDIUM
was fixed in the same session; these are what's left.

### 39. `_RATE_LIMIT_DETAIL` constant is misplaced in `address_service.py`
**File**: `services/address_service.py:15`
**Severity**: LOW (code layout)

The `_RATE_LIMIT_DETAIL` module-level constant sits between the import
block and the unrelated `SUPPORTED_COUNTRY_CODES` set, separated from
its only caller (`_enforce_maps_rate_limit`) by one line. Cohesion with
the helper would read better.

Fix: either inline the literal as `detail=` inside
`_enforce_maps_rate_limit`, or move the constant to sit directly above
the helper. Cosmetic; do when next touching the file.

---

## 2026-04-23 `/security-review` pass (post-LLM rate-limit fix)

HIGH finding (missing per-company rate limiting on `/agents/orchestrate`
and `/agents/estimate`) was fixed in the same session as the pass. The
two items below are the residual MEDIUM findings. LOW finding
("`_handle_get_estimate` unscoped fallback") duplicates entry #37 and
is not re-filed.

### 40. `portal/firebase.json` has no security-header config
**File**: [portal/firebase.json](portal/firebase.json)
**Severity**: MEDIUM

The hosting block contains only `public`, `ignore`, and `rewrites` — no
`headers` array. That means the deployed portal serves no CSP, no HSTS,
no `X-Frame-Options`, no `X-Content-Type-Options`, no `Referrer-Policy`,
and no `Permissions-Policy`. Firebase Hosting emits these only when
they are explicitly configured.

Fix: add a `headers` array covering at minimum:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

A real CSP is a larger undertaking — enumerate allowed `script-src`
(Vite chunks), `connect-src` (the API host from `VITE_API_URL` plus
Firebase Auth domains), `img-src` (user-uploaded assets, Firebase
Storage if used), and `style-src`. Ship the four simple headers first;
tackle CSP as its own change once the allow-lists are stable.

### 41. `except Exception` around httpx calls in `address_service.py` could mask future `HTTPException`
**File**: [services/address_service.py](platform/services/address_service.py) lines 324-418 (three sites)
**Severity**: MEDIUM (defensive)

Each of `autocomplete`, `resolve_place_id`, and `normalize_address_parts`
has a `try/except Exception:` wrapping the httpx call that returns `[]`
or `{}` on any failure. This is fine today — `_enforce_maps_rate_limit`
runs **before** the `try`, so its `HTTPException(429)` propagates
naturally. The concern is that a future refactor that moves the
enforce call inside the `try` would silently swallow the 429 and turn
a rate-limit rejection into an empty result, defeating the point of
the limiter.

Fix: narrow each `except Exception:` to
`except (httpx.HTTPError, httpx.TimeoutException):` so unrelated
failures (including any `HTTPException` raised from inside the block)
propagate naturally. Zero behaviour change in the happy path; makes
the invariant explicit to the next reader.

---

## 2026-04-23 `/code-review` pass (estimate status state machine + detail-page layout)

MEDIUM and LOW residuals from the `/code-review` pass on the layout +
status-state-machine work. No CRITICAL or HIGH findings. Recommendation
was "Warning — safe to commit" — items below are quality-of-life.

### 42. No unit test for the `handleStatusChange` dispatcher
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — `handleStatusChange` around line 444
**Severity**: MEDIUM

The consolidated handler routes between three API paths (`estimatesApi.archive`,
`estimatesApi.unarchive`, `estimatesApi.update`) based on `target` +
`currentNormalized`. `getAllowedTransitions` is covered by 15 vitest cases,
but the routing decision inside the page is not tested anywhere.
CLAUDE.md's TDD rule applies to `.tsx` behaviour changes.

Fix: extract the routing decision into a pure helper beside
`getAllowedTransitions` — e.g. `resolveStatusChangeApi(currentStatus,
target): { kind: "archive" | "unarchive" | "update", payload?: { status?:
string; approved_by?: string } }` — and unit-test it. The page handler
becomes a thin switch on `kind`. Cheap.

### 43. Trash-icon-only buttons have no accessible name
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — Preview version-row delete (~line 1017) and work-item row delete (~line 1147)
**Severity**: MEDIUM (a11y)

Both buttons render only `<Trash2 />` inside. Each is wrapped in a
`<Tooltip content="Delete this version">` (or similar), but tooltip
content is typically not announced by screen readers — the button has
no accessible name. Same pattern appears on other icon-only trash
buttons across the portal (EquipmentsPage, ContactsPage, PropertiesPage,
RateCardsTab, etc.) — this is a portal-wide gap, not specific to this
change.

Fix: add `aria-label={`Delete version ${v.version}`}` (or equivalent
row-specific label) on every icon-only trash button. Sweep-style PR;
grep for `<Trash2 ` and audit each site.

### 44. `(err as Error).message` fallback in catch blocks can render `undefined`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — three catch blocks: `handleDelete` (~L427), `handleStatusChange` (~L458), `handleGenerateGoogleDoc` (~L481)
**Severity**: MEDIUM

If the rejected value isn't an `Error` instance (plain string from
`ApiError`, JSON object, aborted fetch signal), `(err as Error).message`
evaluates to `undefined` and `setFormError(undefined)` clears the banner
instead of showing a useful message. Pre-existing pattern carried through
the refactor; third catch (`handleGenerateGoogleDoc`) already has an
OR-fallback, the first two do not.

Fix: unify to `setFormError(err instanceof Error ? err.message :
"Failed to update status")` (pick appropriate fallback copy per handler).
One-line change per catch.

### 45. `.gitignore` widened from filename to directory without comment
**File**: [platform/.gitignore](../../platform/.gitignore):145
**Severity**: LOW

`service-account-key.json` → `secrets/` is functionally fine (the
`service-account-key*.json` and `*-key.json` sibling patterns still
catch loose keys), but the diff reads as "why did a specific-file rule
become a directory rule?" without context.

Fix: add a one-line comment above the `secrets/` entry — e.g.
`# local secrets directory (service-account keys, tokens, etc.)` — so
the next reader understands the broadening.

### 46. State machine is frontend-only (by design, re-filed for visibility)
**File**: [platform/routers/estimates.py](../../platform/routers/estimates.py) — `update_estimate` handler (~L1777), `unarchive_estimate` (~L2244)
**Severity**: LOW

Per the plan (see `documentation/development/plans/create-a-plan-to-lively-karp.md`),
backend PUT `/estimates/{id}` still accepts any `{status: "..."}` value.
An API caller bypassing the UI can drive invalid transitions (e.g. Lost →
Won, or reopening Archived via PUT instead of `/unarchive`). The UI
enforces the state table via `getAllowedTransitions`; the backend does
not.

Fix: when a non-UI API surface matters (public API, external
integrations, Maple agent moves beyond current verbs), add a
`validate_transition(current, target)` check in the PUT handler before
`estimate.set(...)`. Shape: raise `HTTPException(status_code=400,
detail=f"Invalid transition: {current.value} → {target.value}")`. Mirror
the `TRANSITIONS_BY_STATUS` map from the frontend, or better, define it
once in `models/estimate.py` and import from both.

---

## 2026-04-23 `/code-review` pass (verbless-gap fix)

Residuals from the `/code-review` pass on the Phase 1 + 2a + 2b verbless
classification fix. No CRITICAL or HIGH findings blocked commit;
recommendation was "Warning — safe to commit." Items below are quality
debt from the heuristic-driven implementation of Phase 2b that the
original plan's catalog-backed Phase 2a-proper would largely retire.

Plan: [plans/fix-maple-verbless-gap.md](plans/fix-maple-verbless-gap.md).

### 48. `_LABOUR_ROLE_TOKENS` drifts from `DOMAIN_HINTS["labour"]`
**File**: [agents/orchestrator/service.py:77](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

The frozenset is maintained manually with a "kept in sync with
intents.py" comment. If a new role is added to `DOMAIN_HINTS["labour"]`,
the set won't auto-update and verbless-labour bare tokens silently stop
working.

Fix: split `DOMAIN_HINTS["labour"]` in `intents.py` into
`_GENERIC_LABOUR_HINTS` + `_LABOUR_ROLE_HINTS`, export the role-hints
list, and re-use it in `service.py`. Cleaner than the alternative of
filtering generic keywords out of the combined list at import time.

### 49. `_ADDRESS_PATTERN` can false-match "N <word>+ way/court"
**File**: [agents/orchestrator/service.py:65](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

Pattern uses `.search()` (not `.fullmatch()`) with permissive suffixes
including `way`, `court`, `ct`. Phrasings like `"3 days back way"` or
`"60 minutes one way"` trigger `domain=property` → `get_property`. Low
real-world frequency but demonstrably triggerable.

Fix (quick win): drop the most-ambiguous suffixes (`way`, `court`,
`ct`). Smaller coverage, fewer false positives. For the permanent fix,
require the match to be the entire residual after stripping any
action-phrase prefix via `_bare_entity_residual`. Catalog-backed
lookup (per the plan's deferred Phase 2a-proper) would retire the
concern entirely.

### 50. Duplicate stopword lists in the orchestrator
**File**: [agents/orchestrator/service.py:88, :130](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

`_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` share ~14
entries (`hi`, `hey`, `the`, `that`, `my`, `your`, `our`, `no`, `yes`,
`ok`, `okay`, `thank`, `thanks`, `please`, `sorry`). Two lists to keep
in sync when adding a new filler.

Fix: extract `_COMMON_FILLER_STOPWORDS` frozenset; union with
domain-specific additions for each downstream use.

### 51. No direct unit tests for the new bare-entity helpers
**File**: [agents/orchestrator/service.py:372, :395, :404](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM (TDD policy)

`_is_bare_entity_reference`, `_looks_like_person_name`, and
`_bare_entity_residual` are covered end-to-end via
`tests/test_maple_crud_coverage.py` but have no direct unit tests.
Edge cases (empty string, unicode names like "Renée Dupont",
punctuation-heavy input, adversarial input) aren't exercised.
CLAUDE.md's TDD rule applies to new `.py` behaviour.

Fix: add `tests/test_orchestrator_bare_entity_helpers.py` with ~10
parametrized cases per helper — edge cases plus golden paths.

### 52. Inline comments instead of docstrings on new helpers
**File**: [agents/orchestrator/service.py:395, :404](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (style)

Project leans toward docstrings on methods (see `_format_chat_history`,
`_build_entity_context_summary`, etc.). My new helpers use inline
`# ` comments instead. Cosmetic only.

Fix: convert the prose comments to proper docstrings. Do when next
touching the file.

### 53. `_CONFIRMED_WORKING_CASE_IDS` has no entry-validation
**File**: [tests/_maple_coverage_data.py](../../platform/tests/_maple_coverage_data.py)
**Severity**: LOW

The override set grows monotonically and is manually curated. A
mistyped case ID silently does nothing — the override never applies,
and the phrasing stays marked as an XFAIL without the reviewer
realizing.

Fix: at module load, assert that every entry in
`_CONFIRMED_WORKING_CASE_IDS` corresponds to a real `case_id` in the
matrix; raise `ValueError` on mismatch. ~5 lines.

### 54. Tier 1 gap: `set <name>'s <field> to <value>` pattern
**File**: [agents/orchestrator/intents.py:106-111](../../platform/agents/orchestrator/intents.py) (`ACTION_HINTS["update"]`)
**Severity**: MEDIUM (surfaced by the coverage matrix)

4/4 resources fail on Tier 1 for the `set X's Y to Z` phrasing because
`ACTION_HINTS["update"]` has no `"set"` entry. Tier 2 LLM rescues 2/4
but not reliably.

Fix: add `"set"` to `ACTION_HINTS["update"]`. Shake out regressions
carefully — `set` is also referenced in the work-item-edit regex at
service.py:244 and the `ADD_SET_FIELD_PATTERN_ORCHESTRATOR` guard at
service.py:279, so check both paths still behave.

### 55. Tier 2 gap: implicit-relationship cross-resource phrasings
**Files**: LLM system prompt in
[agents/orchestrator/service.py:~674](../../platform/agents/orchestrator/service.py) (and entity-knowledge graph if extended)
**Severity**: MEDIUM (Tier 2 coverage 4/12)

Phrasings like `who owns 123 Main St?`, `where does John Doe live?`,
`which properties use concrete blocks?`, `what estimates use the
Landscaper role?` expect Maple to return `list_<related_resource>`
intents. LLM handles these inconsistently and rules can't infer
cross-resource semantics at all.

Fix (sketch): add 4–6 few-shot examples to the LLM system prompt that
pair each implicit-relationship phrasing with the expected
`list_<related_resource>` intent. Then re-run Tier 2 and see whether
the LLM picks them up. If prompt alone doesn't close it, the
orchestrator would need to resolve the referenced entity first, then
infer the target resource based on the relationship verb — that's a
larger design change.

### 56. Tier 1 gap: `what's <name>'s <field>?` contraction not handled
**File**: [agents/orchestrator/intents.py:131-150](../../platform/agents/orchestrator/intents.py) (`ACTION_HINTS["get"]`)
**Severity**: LOW

`ACTION_HINTS["get"]` contains `"what is"` but not `"what's"` — the
contraction. Phrasings like `"what's John Doe's phone?"` or `"what's
Landscaper's cost?"` therefore fail rule-level action detection, even
when the domain resolves via `phone` / `cost` / the name heuristic.

Fix: either add `"what's"` to `ACTION_HINTS["get"]`, or pre-normalize
common contractions (`what's` → `what is`, `who's` → `who is`, etc.)
in `_classify_with_rules` before hint matching. Normalizing is more
general; adding hints is cheaper.

---

## 2026-04-23 review (Estimate Detail + Maple panel session)

Findings deferred from the `/code-review` pass on the Estimate Detail page
polish, Maple list-formatting helper, and Maple-panel footer nav work.
HIGH items in that review were fixed in-session; these are the MEDIUM /
LOW items the user chose not to land right now.

### 57. Stale closure of `estimate` in `handleGenerateGoogleDoc`
In `portal/src/pages/NewEstimateWithActivityPage.tsx`, after
`await handleSaveEstimate()` resolves, the local `estimate` identifier
still refers to the pre-save snapshot — only `getEntityId(estimate)` is
read afterward, and the ID doesn't change, so no current bug. But anyone
extending this path to read a field that can change mid-save (e.g.,
`estimate.status`, `estimate.updated_at`) will silently use stale data.

Fix: widen `handleSaveEstimate` to return
`Promise<EstimateWithExtras | null>` and use the resolved value instead
of the closure reference.

### 58. `PortalLayout.tsx` is now 2,148 lines
Preexisting; this session added ~45 lines (`openMaple`, `openFeedback`,
`openChangeLog`, `mapleNavFooter`, ESC wiring on the panels) and removed
the two composer-level button rows for a net +20. Still well over the
800-line HIGH threshold.

Fix: extract the Maple panel (header + messages + composer + footer +
Feedback/ChangeLog overlays) into `components/maple/MaplePanel.tsx`.
Both the mobile and desktop branches render nearly-identical markup and
could share one component with a `variant="mobile" | "desktop"` prop.

### 59. Drive-filename filename-collision policy still implicit
The 2026-04-23 fix put the estimate_id back into the Drive filename
(`Estimate-{estimate_id}-V{n}`), which resolves traceability. However,
Drive still permits duplicate filenames within a folder — there is no
enforcement that `(estimate_id, version)` is globally unique *as a
filename*. If two concurrent generate-doc requests race, they could
produce two Drive files with the same name. The version-number
computation in `routers/estimates.py:2376-2379` is also read-modify-
write without a lock.

Fix: add a unique index on `(estimate_id, version)` inside the
`GoogleDocsVersion` embedded array, or wrap the version-bump + create
in an optimistic-concurrency retry keyed on `estimate.updated_at`.
Low priority — the user would need to double-click "New Version" within
the Drive latency window to trigger the race.

---

## 2026-04-24 external review (indexes + httpx + DB-side sort)

Three warnings raised by an external reviewer; each verified against
current source before filing. None are active bugs. Filed per user
request for later triage.

### 60. No unique compound index on Material / Contact
**Files**: [platform/models/material.py:32](../../platform/models/material.py),
[platform/models/contact.py:45](../../platform/models/contact.py)
**Severity**: LOW–MEDIUM (data integrity, not an active bug)

Both models declare only `IndexModel([("company", ASCENDING)])`. Concurrent
inserts can produce duplicates for the same `(company, name)`.

The reviewer's proposed fix — "compound unique index on (company, name)
for all inventory models" — is correct for Material but **wrong for
Contact**. Two contacts can legitimately share a full name (two different
"John Smith" homeowners). A Contact uniqueness constraint would need to
include email/phone, and even that is debatable.

Fix: for Material, add `IndexModel([("company", ASCENDING), ("name",
ASCENDING)], unique=True)` — but only after auditing prod data for
existing duplicates; index creation fails if violations exist. For
Contact, no unique index (reviewer was wrong on this one); if
deduplication is a real concern, surface it in the UI on create/update
instead.

### 61. Trello httpx client rebuilt per request
**File**: [platform/services/trello_service.py:40](../../platform/services/trello_service.py)
**Severity**: TRIVIAL (don't fix unless path becomes hot)

`async with httpx.AsyncClient(timeout=15.0) as client:` inside
`create_trello_card` tears down the connection pool on every call.
Reviewer correctly flagged that a module-scoped client would enable
connection pooling.

In practice: this endpoint fires once per estimate → card creation. The
pool-churn cost is microseconds on a call that already takes hundreds of
ms over the network. Premature optimization at current volume.

Fix (if it ever matters): promote to a module-level
`_client = httpx.AsyncClient(timeout=15.0)` and swap the `async with`
for `await _client.post(...)`. Add a FastAPI lifespan hook to close it
on shutdown.

### 62. Python-side sort in `get_material_categories` / `get_material_units`
**Files**: [platform/routers/material_categories.py:48](../../platform/routers/material_categories.py),
[platform/routers/material_units.py:49](../../platform/routers/material_units.py)
**Severity**: LOW (cleanliness, not performance)

Both handlers call `sorted(items, key=lambda x: x.name.lower())` after
`.to_list()`. Reviewer framed this as "unscalable" — overstated, since
category/unit counts per company are dozens, not millions. Real reason
to fix is consistency, not throughput.

Caveat on the fix: the reviewer's proposed
`.sort(+MaterialCategory.name)` is byte-order (case-sensitive) unless a
collation is attached. The current Python sort is case-insensitive via
`.name.lower()`. A straight DB-side sort would change ordering for
mixed-case names (e.g., "apple" vs "Banana").

Fix (when next touching these files): switch to
`await MaterialCategory.find(...).sort(+MaterialCategory.name).to_list()`
**with a collation** `{locale: "en", strength: 2}` so case-insensitive
order is preserved. Same shape for `MaterialUnit`. If attaching a
collation is awkward via Beanie, leave the Python sort — clarity beats
a half-done DB push-down.

---

## 2026-04-25 review (configurable divisions session)

Findings from `/code-review` after migrating Work Item divisions from a
hardcoded `EstimateDivision` enum to a per-company configurable list
(see [`plans/configurable-divisions.md`](plans/configurable-divisions.md)).
Zero CRITICAL, one HIGH (pre-existing file size), three MEDIUM, three LOW.

### 64. WorkItem divisions fetch swallows errors silently
**File**: [portal/src/components/estimates/WorkItemInlineContent.tsx:73](../../portal/src/components/estimates/WorkItemInlineContent.tsx)
**Severity**: MEDIUM

`.catch(() => setDivisions([]))` hides API failures. If the divisions
endpoint is down, users see an empty dropdown with no signal whether
it's a transient failure or just a freshly-created company. Mirrors the
pre-existing rate-cards pattern, so consistent — but support has no
breadcrumb when this fires.

Fix: log via `console.error` (or a shared error reporter if one exists
later) before the empty fallback. Apply the same change to the
rate-cards `.catch` for consistency.

### 65. "Unknown" division is selectable in the Work Item dropdown
**File**: [portal/src/components/estimates/WorkItemInlineContent.tsx:236-238](../../portal/src/components/estimates/WorkItemInlineContent.tsx)
**Severity**: MEDIUM

When the stored `division` value isn't in the company's fetched list,
the dropdown renders `"Unknown"` as the displayed value. The locked
spec said "Unknown" should be a display-only fallback — but the option
is currently `<option value="Unknown">Unknown</option>`, so a user
clicking it persists the literal string `"Unknown"` to the DB. That
value will never match a real division on subsequent loads, so it
self-perpetuates.

Fix: render the Unknown `<option>` with `disabled`, or in the `onChange`
handler ignore the literal `"Unknown"` value and keep the prior state.
Add a frontend test that exercises the fallback path with a stale
division name.

### 66. No unique compound index on Division `(name, company)`
**Files**: [platform/models/division.py](../../platform/models/division.py),
[platform/services/division_bootstrap.py](../../platform/services/division_bootstrap.py)
**Severity**: MEDIUM

The Division model indexes `company` only. The bootstrap's "find then
insert" pattern and the POST endpoint both check existence before
inserting, but there's no unique constraint backing them — two
concurrent POSTs with the same name produce two rows. Same gap exists
on `MaterialCategory` (entry #60), so this is propagating a known
pattern rather than introducing a new one. Flagging it explicitly so
both can be fixed together.

Fix: add `IndexModel([("company", ASCENDING), ("name", ASCENDING)],
unique=True)` to `Division.Settings.indexes` (and to MaterialCategory
in the same pass). Backfill existing duplicates via a one-off cleanup
script before applying the index in production.

### 67. `PydanticObjectId(company)` returns 500 on garbage input
**File**: [platform/routers/divisions.py:44](../../platform/routers/divisions.py)
**Severity**: LOW

A malformed `?company=xyz` query raises `bson.errors.InvalidId` →
unhandled → 500 instead of a clean 422. Mirrors `material_categories`
and `material_units`. Pre-existing pattern; defer.

Fix: wrap in try/except → `HTTPException(422, "Invalid company id")`,
or factor a Pydantic dependency that validates ObjectIds and use it
across all `?company=` query routers.

### 68. `backfill_divisions.py` uses broad `except Exception`
**File**: [platform/scripts/db/backfill_divisions.py:54](../../platform/scripts/db/backfill_divisions.py)
**Severity**: LOW (script context, not a service handler)

The script intentionally swallows per-company exceptions to keep going
through the company list, then reports failures and exits non-zero.
Acceptable for a one-off backfill — flagging only because spec calls
broad excepts CRITICAL by default. No action expected unless the script
gets reused for repeated migrations.

### 69. Bootstrap services log nothing on success
**Files**: [platform/services/division_bootstrap.py](../../platform/services/division_bootstrap.py),
[platform/services/material_category_bootstrap.py](../../platform/services/material_category_bootstrap.py),
[platform/services/material_unit_bootstrap.py](../../platform/services/material_unit_bootstrap.py)
**Severity**: LOW

All three bootstrap helpers run silently on success. The wrapper in
`company_service.py` does `logger.exception(...)` on failure, so
failures are observable, but successful seeding leaves no audit trail.
Useful diagnostic when investigating "why does this company not have X"
questions.

Fix (low value, low effort): emit `logger.info("Seeded N {resource}
templates for company %s", company_id)` from each bootstrap function.

## 2026-04-25 review (configurable material units session)

### 70. Missing type hints in `backfill_material_units.py` helpers
**File**: [platform/scripts/db/backfill_material_units.py:50, 68](../../platform/scripts/db/backfill_material_units.py)
**Severity**: MEDIUM (script context, not production code)

`remap_materials_for_unit(company_id, old_unit_id, new_unit_id)` and
`migrate_company(company)` lack annotations. The divisions backfill set
the same precedent, but for consistency with the model APIs these would
be more self-documenting as
`remap_materials_for_unit(company_id: PydanticObjectId, old_unit_id: PydanticObjectId, new_unit_id: PydanticObjectId) -> int`
and `migrate_company(company: Company) -> dict`.

### 71. Sequential `material.replace()` per remap is slow at scale
**File**: [platform/scripts/db/backfill_material_units.py:60](../../platform/scripts/db/backfill_material_units.py)
**Severity**: MEDIUM (performance, fine for current scale)

`remap_materials_for_unit` iterates materials and calls
`await material.replace()` one at a time, so the cost is roughly
`O(companies × renamed_units × materials_per_company)`. The 2026-04-25
production run touched 191 materials in seconds; at 10k+ materials per
company this would hurt.

Fix (if reused): batch via
```python
Material.find_many({"company": company_id, "sizes.unit": old_unit_id}).update_many(
    {"$set": {"sizes.$[el].unit": new_unit_id, "updated_at": now}},
    array_filters=[{"el.unit": old_unit_id}],
)
```
Skips the `before_event` hook, so set `updated_at` explicitly.

### 72. `getCategoryName` / `getUnitName` re-allocated each render
**File**: [portal/src/pages/MaterialsPage.tsx:183-193](../../portal/src/pages/MaterialsPage.tsx)
**Severity**: LOW (pre-existing pattern; not introduced by the
configurable-units change)

Both helpers are defined in the component body, so they're new function
references on every render. No memoized child currently depends on
referential equality, so this is purely cosmetic — flagging only because
the same lookup pattern shows up across `MaterialsPage`,
`AddMaterialGapDialog`, and the (eventual) inventory drawer. A shared
`useMemo`-wrapped lookup hook would centralise the cache.

---

## 2026-04-26 review (rate-card unit dropdown + default seeding session)

MEDIUM and LOW residuals from the `/code-review` pass after the rate-card
unit Literal, dropdown, Effort Calculator column, JSON-fixture seeding, and
on-signup bootstrap landed. The HIGH finding from that pass (missing
`aria-label`s on the rate-card row inputs) was fixed in the same session.

### 73. N+1 `find_one` inside bootstrap loops
**File**: [platform/services/rate_card_bootstrap.py:48-54](../../platform/services/rate_card_bootstrap.py)
**Severity**: MEDIUM
**Why it's MEDIUM, not HIGH**: matches the existing pattern in
`division_bootstrap.py`, `material_category_bootstrap.py`, and
`material_unit_bootstrap.py`. Volume is small today (6 templates × 12
companies = 72 queries during backfill), but the cost compounds as more
bootstrappers join the chain.

Fix: pre-load existing names with one query and check membership in the
loop, e.g.
```python
existing_names = {
    rc.name for rc in await RateCard.find({
        "company": normalized_company_id,
        "name": {"$in": [t["name"] for t in templates]},
    }).to_list()
}
```
Apply consistently across all `*_bootstrap.py` modules in one pass to keep
them aligned.

### 74. JSON re-parsed on every `bootstrap_company_rate_cards` call
**File**: [platform/services/rate_card_bootstrap.py:20](../../platform/services/rate_card_bootstrap.py)
**Severity**: MEDIUM
The loader reads + parses `default_rate_cards.json` on every call. Cheap
individually, wasteful in the backfill loop (12× during the recent
backfill, more whenever a new bootstrapper is added).

Fix: `@functools.lru_cache(maxsize=1)` on `load_default_rate_card_templates`,
or assign at module import. Tests already monkey-patch
`DEFAULT_RATE_CARDS_PATH`, so any cache must be invalidated in those tests
(via `cache_clear()` in a fixture).

### 75. `CardItem.easy/standard/hard` unbounded
**File**: [platform/models/rate_card.py:26-28](../../platform/models/rate_card.py)
**Severity**: MEDIUM
**Why it's MEDIUM**: pre-existing — predates the unit-Literal change. But
the dropdown work tightened `unit` validation, and the same rigour should
apply to the rate fields: today negative, zero, NaN, and Infinity all pass
Pydantic. Frontend rejects negatives (`min="0"`); a direct API client or
malformed `default_rate_cards.json` can poison data and break effort
calculations (division by zero on a row's chosen difficulty).

Fix: `easy: float = Field(..., gt=0)` (and same for `standard`/`hard`).
Will require touching test fixtures that pass `0` and updating the frontend
helper text. Coordinate with whoever owns the Effort Calculator's
zero-handling so we don't change semantics underneath.

### 76. Backfill swallows per-company exceptions
**File**: [documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py:32](../../documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py)
**Severity**: MEDIUM
The backfill catches every `Exception` per company and prints a one-liner.
A misconfigured DB (auth failure, etc.) scrolls past silently as N
identical errors. Pre-existing convention across migration scripts.

Fix: differentiate infrastructure errors (`ServerSelectionTimeoutError`,
`OperationFailure`) from per-document validation errors and let the former
propagate. Apply the same shape to other migration scripts in one pass.

### 77. `SEED_COMPANY_ID` is a magic constant tied to live data
**File**: [documentation/development/migration_scripts/export_default_rate_cards.py:26](../../documentation/development/migration_scripts/export_default_rate_cards.py)
**Severity**: MEDIUM
The hard-coded ObjectId is documented in the module docstring but not
guarded. If this script is re-run after the seed company evolves, it
silently overwrites `default_rate_cards.json`.

Fix: either accept the company id as a CLI arg with no default, or refuse
to overwrite an existing `default_rate_cards.json` without a `--force`
flag. Low priority since the script is clearly labeled "one-shot".

### 78. Validation error message doesn't list allowed units
**File**: [portal/src/lib/rateCards.ts:28](../../portal/src/lib/rateCards.ts)
**Severity**: LOW
`"Item ${i+1}: Unit must be one of the allowed values."` is unactionable
for any user who hits it (which shouldn't happen via the UI, but could from
a stale tab or a copy-paste).

Fix: include the list:
```ts
` Item ${i + 1}: Unit must be one of: ${RATE_CARD_UNITS.join(", ")}.`
```

### 79. `load_default_rate_card_templates` returns loose `list[dict]`
**File**: [platform/services/rate_card_bootstrap.py:13](../../platform/services/rate_card_bootstrap.py)
**Severity**: LOW
Returning `list[dict]` loses the schema; callers can't tell what keys
exist without reading the validator.

Fix: define `RateCardTemplate` and `CardItemTemplate` as `TypedDict`s in
the same module and return `list[RateCardTemplate]`. Pure ergonomics — no
runtime change.

---

## 2026-04-26 `/code-review` pass (HIGH cleanup session — #19, #38, #47, #63)

Findings from the `/code-review` after the four HIGH refactors landed
(`_classify_with_rules` extraction, `_handle_get_work_item` extraction,
`_enrich_address_fields_with_google` shared helper, SettingsPage tab
extractions). The HIGH (`_load_estimate_for_read` / `_load_estimate_for_update`
both over 50 lines, originally filed as #80) was fixed in the same
session via the shared `_estimate_load_error_envelope` and
`_coerce_company_oid` helpers — that fix also resolved the
`_load_estimate_for_read` and `_load_estimate_for_update` portions of
entry #20. Two MEDIUM (#81, #84) and three LOW (#82, #83, #85) remain
below.

### 81. `react-hooks/exhaustive-deps` disabled in 3 new settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx:55](../../portal/src/components/settings/DivisionsTab.tsx),
[portal/src/components/settings/MaterialUnitsTab.tsx:55](../../portal/src/components/settings/MaterialUnitsTab.tsx),
[portal/src/components/settings/MaterialCategoriesTab.tsx:56](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
**Severity**: MEDIUM

All three new tab components use
`// eslint-disable-next-line react-hooks/exhaustive-deps` on the
`useEffect` that calls `fetchX()` when `active` flips to true. Disabling
the rule masks a stale-closure risk if `companyId` ever changes between
renders. The existing `RateCardsTab.tsx` solves the same problem cleanly
with `useCallback`.

Fix: wrap each fetch helper in
`useCallback(async () => { ... }, [companyId])`, list the callback in the
effect's deps, and drop the eslint-disable comment. ~6 lines per file.
Mirror the pattern in `portal/src/components/settings/RateCardsTab.tsx`
(lines 46-61).

### 82. `alert(...)` for save errors in 3 settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx) (`handleSaveDivision`),
[portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx) (`handleSaveUnit`),
[portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx) (`handleSaveCategory`)
**Severity**: LOW (UX inconsistency)

The save handlers surface API errors via browser `alert(...)`. The delete
flows in the same files render an inline error inside the modal instead.
Pattern was preserved verbatim from the pre-extraction `SettingsPage.tsx`
during the 2026-04-26 #63 fix — pre-existing, not introduced.

Fix: lift the error into a `formError` state inside the dialog, displayed
above the action buttons. Consistent with the delete-modal pattern in the
same files. Theme-adjacent to entry #44.

### 83. Inconsistent ID extraction across settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx),
[portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx),
[portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
**Severity**: LOW (style)

The new tab components use the non-null assertion operator
(`editingDivision.id!`, `categoryToDelete!.id!`) when calling the API.
The sibling `RateCardsTab.tsx` instead uses `extractEntityId(rc)` from
`lib/entityId`, which handles the union shape from the API response
without requiring a non-null assertion. Pattern was preserved verbatim
during the 2026-04-26 #63 extraction — pre-existing, not introduced.

Fix: switch to `extractEntityId(...)` for consistency with `RateCardsTab`.
~6 call sites across the three files.

### 84. `_coerce_company_oid` returns `Optional[Any]` to keep lazy beanie import
**File**: [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) — `_coerce_company_oid` (added 2026-04-26)
**Severity**: MEDIUM (style / future-proofing)

The new helper has return annotation `Optional[Any]` so the
`from beanie import PydanticObjectId` import can stay lazy (inside the
function body), matching ~20 other lazy-import sites in this file. The
docstring documents the actual return shape, but static-typing precision
is lost at every call site.

The lazy-import pattern itself looks like a leftover artifact rather
than a deliberate decision — `bson.ObjectId` is already imported at
module level (line 22), and beanie is fully loaded by the time
`agents/estimate/service.py` is evaluated. There's no obvious circular
import to defend against.

Fix: when entry #3 (mypy baseline) lands, promote
`from beanie import PydanticObjectId` to module level and tighten
`_coerce_company_oid`'s return annotation to `Optional[PydanticObjectId]`.
~20 in-function `from beanie import PydanticObjectId` lines can also be
removed at the same time. Don't fix in isolation — bundle with the mypy
work since it's the easiest place to verify nothing breaks.

### 85. No direct unit tests for `_estimate_load_error_envelope` and `_coerce_company_oid`
**File**: [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) — both helpers added 2026-04-26 in the #80 refactor
**Severity**: LOW (TDD policy, private helpers)

Both helpers are exercised transitively via `_load_estimate_for_update`
and `_load_estimate_for_read`, but lack direct tests. Edge cases worth
pinning: empty `company_id`, malformed ObjectId hex (e.g. "abc"),
`TypeError` cast input (e.g. `None`), and the `probability` fallback
when `orchestrator_confidence` is missing from the context dict.

Theme-adjacent to entry #51 (`_is_bare_entity_reference` etc. covered
only end-to-end). CLAUDE.md's TDD rule applies softly to private
helpers, so this is filed as LOW rather than MEDIUM.

Fix: add ~6-8 parametrized cases to a new
`tests/test_estimate_load_helpers.py` (or extend `test_estimate_agent.py`
with a small section). Quick to write since both helpers are pure or
near-pure.

---

## 2026-04-26 mypy baseline (themed entries from #3)

The themed split of the 271-error mypy baseline. See entry #3 for the run
command and the rationale for not gating CI yet.

### 86. `union-attr` on `dict.get(...)` chains (92 errors)
**Files**: `agents/property/service.py`, `agents/contact/service.py`,
`agents/material/service.py`, `agents/labour/service.py`,
`agents/equipment/service.py` — typically `context.get("...")` followed by
attribute access without a None guard.
**Severity**: MEDIUM (mostly false positives — context is always a dict in
practice, but mypy can't see the call-site contract)

The agent `process()` methods all accept `context: Optional[dict[str, Any]] =
None` and call `context.get(...)` deep in the body. Pydantic narrows the
type at the entry point, but mypy doesn't see the early `if context is
None: context = {}` guard because it's done implicitly via `.get()`-on-None
(which crashes at runtime if it ever happens).

Fix (per-agent): early in each `process()`, normalize the context with
`context = context or {}` and re-bind to a `dict[str, Any]` local. Mypy
sees the narrowed type and the 92 false positives collapse. Apply
opportunistically when next refactoring each agent.

### 87. `arg-type` on `PydanticObjectId | None` → required (~25 errors)
**Files**: `routers/companies.py`, `routers/estimates.py`,
`routers/materials.py`, `routers/properties.py`,
`services/company_service.py`, `scripts/db/backfill_divisions.py`
**Severity**: MEDIUM (legitimate gap)

`current_user.company` is `Optional[PydanticObjectId]` because users can
exist without a company (pre-onboarding). Functions like
`assert_company_access` and `get_company_defaults` declare a required
`PydanticObjectId` param. The handlers should explicitly raise 401/403
when `current_user.company is None` instead of leaning on Pydantic's
runtime coercion.

Fix: add a `_require_company(current_user)` helper in `dependencies.py`
that returns `PydanticObjectId` or raises `HTTPException(401, "User has
no company")`. Use it at the top of every handler that currently passes
`current_user.company` to a function expecting required ObjectId.

### 88. `assignment` — implicit-Optional defaults (~50 errors)
**Files**: `agents/estimate/service.py` (~20 sites including 7 `tokens:
TokenUsageAccumulator = None`), `agents/orchestrator/service.py`,
`prompts/estimate_react.py`, `prompts/estimate_architect.py`,
`agents/estimate/conversation_guide.py`
**Severity**: MEDIUM (mechanical, but high volume)

Pattern is `def f(x: T = None)` where T is non-Optional. Two fixes:
- For agent helpers where None is a real signal (e.g.
  `tokens: TokenUsageAccumulator = None`), change to `Optional[T] = None`.
- For prompt-builder kwargs (`property: str = None`, `industry: str =
  None`, `company: str = None`), change to `str = ""` if empty-string is
  the actual sentinel — many of these immediately do `(value or "").strip()`
  so the empty-string default is closer to the true contract.

Do NOT apply to FastAPI `Request = None` params (see entry #3 fix notes).

### 89. `arg-type` on `agents/*/service.py` — `Material | None` → `Material` (~30 errors)
**Files**: `agents/material/service.py`, `agents/labour/service.py`,
`agents/equipment/service.py`, `agents/property/service.py`,
`agents/contact/service.py`
**Severity**: MEDIUM (real defensiveness gap)

After `await Material.find_one(...)` the result is `Material | None`,
but the result is passed directly to `_material_to_dict(material)`
without checking. If the lookup misses, the helper crashes with
`AttributeError`. In practice the find calls are guarded by an earlier
existence check, so the misses don't reach the dict helper — but the
guards are easy to forget when adding new branches.

Fix: in each agent, change `_material_to_dict(material: Material)` to
accept `Optional[Material]` and return an empty-dict envelope on None.
Callers no longer need to guard. Same shape for Labour, Equipment,
Property, Contact.

### 90. `models/estimate.py` arithmetic on `Optional[int]` fields (16 errors)
**File**: [models/estimate.py:157, 206-215](../../platform/models/estimate.py)
**Severity**: MEDIUM (latent bug if any nullable field is actually null)

Several `EstimateVersion` / `Estimate` fields are typed `Optional[int]`
but used in arithmetic (`<=`, `>=`, `-`, `len()`) without None guards.
Today they're always populated (the create/update handlers fill defaults),
but the types disagree with the runtime invariant.

Fix: tighten the model declarations to `int = 0` (or whatever the real
invariant is), or add `assert version.foo is not None` guards at the
arithmetic sites. Tightening the model is cleaner — touch a fixture or
two and the arithmetic just works.

### 91. `call-arg` — `ChatOpenAI(openai_api_key=...)` signature drift (5 errors)
**Files**: `agents/orchestrator/service.py:148`,
`agents/material/service.py:167`, `agents/labour/service.py:125`,
`agents/equipment/service.py:115`, `agents/contact/service.py:112`,
`agents/property/service.py:88`
**Severity**: LOW (langchain version skew, runtime works)

mypy says `ChatOpenAI` doesn't accept `openai_api_key=`. The langchain
stub is out of date — the kwarg exists at runtime and the call works.

Fix: either upgrade `langchain-openai` to a version with synced stubs
(check the pin in `requirements.txt`), or pass the key via env-var
(`OPENAI_API_KEY`) and drop the kwarg. The env-var path is more
idiomatic and removes the dependency on stub freshness.

### 92. `call-arg` — agent → router calls missing `http_request` (5 errors)
**Files**: `agents/material/service.py:1154-1157`,
`agents/labour/service.py:719-722`,
`agents/equipment/service.py:571-586`
**Severity**: LOW (agents pass None but the router's `http_request: Request
= None` default accepts it, see entry #3)

Each Maple CRUD agent calls the corresponding router function directly
(e.g. `await update_material(...)`) but doesn't pass `http_request`. The
router's `# type: ignore[assignment]` default makes this work at runtime.

Fix (long-term): extract the router body into a service helper that
doesn't need `http_request`, and have both the HTTP route and the agent
call the service. Audit logging would shift into the service or wrap the
service call. Big refactor — not blocking. In the short term, suppress
with `# type: ignore[call-arg]` at the agent call sites.

### 93. `BlockingPortal | None` errors in tests (12 errors)
**Files**: `tests/test_rate_card_bootstrap.py` (9 sites),
`tests/test_audit_integration.py` (3 sites),
`tests/test_feedback_api.py` (2 sites),
`tests/test_company_api.py` (1 site),
`tests/test_divisions_api.py` (1 site)
**Severity**: LOW (tests, not production)

`pytest-anyio` returns `BlockingPortal | None` from the
`portal_blocking_portal` fixture. Tests call `portal.call(...)` without a
None guard.

Fix: add `assert portal is not None` (or a thin `_get_portal()` helper) at
the top of each test that uses the fixture. Pure mypy hygiene.

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

## 2026-04-26 `/code-review` pass (post-#4 material + routers extractions)

Findings from the `/code-review` after the material-service handler
extractions (`_handle_create_material`, `_handle_get_material`,
`_handle_delete_material`, `_handle_list_materials`) and the
`routers/agent_helpers/` package landed (`text_helpers.py`,
`estimate_update.py`, `fuzzy_confirmation.py`). Zero CRITICAL, three
HIGH, three MEDIUM, two LOW. The HIGH items are all function-size
inheritances from the original closures — they came over verbatim during
the extraction and remain as the next iteration's target.

### 94. New material handlers all exceed the 50-line ceiling
**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: HIGH (continuation of entry #4)

Extracted handlers and their line counts:
- `_handle_create_material` — 175 lines (1366)
- `_handle_get_material` — 122 lines (1757)
- `_handle_list_materials` — 112 lines (1542)
- `_handle_delete_material` — 101 lines (1655)

Each one is mostly a single response-builder per branch. Next
extraction: factor out the repeated envelope shape (12 keys: `success`,
`query`, `intent`, `agent`, `confidence`, `matches`,
`needs_clarification`, `clarifying_question`, `response`, `result`,
`context`, `error`, `completion_ready`, `missing_fields`,
`accuracy_suggestions`) into a small builder helper. That alone would
shrink each handler by 30–40 lines.

`_handle_list_material_categories` (44 lines, 2026-04-26) is the only
existing handler under threshold and is the model to mirror.

### 95. New `agent_helpers/` extractions exceed the 50-line ceiling
**Files**: [platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py),
[platform/routers/agent_helpers/fuzzy_confirmation.py](../../platform/routers/agent_helpers/fuzzy_confirmation.py)
**Severity**: HIGH (continuation of entry #4)

- `run_update_estimate` — 136 lines (estimate_update.py:40). The
  modify-vs-add detection block (~30 lines) and the
  parsed-job-items-to-grand-total tail (~30 lines) split out cleanly.
- `handle_estimate_fuzzy_confirmation` — 150 lines
  (fuzzy_confirmation.py:31). The `if is_affirmative_text(message):`
  branch is 75 lines; extract `_dispatch_confirmed_intent(...)` for the
  delete / update / work-item-remove sub-dispatch. That also flattens
  entry #97's nesting issue.

Same as #94, these came across verbatim from the original closures and
are next-iteration work.

### 96. ~~Pre-existing failing tests in `test_agents_api.py`~~ — FIXED 2026-04-26

Both tests were stale assertions left over from before the 2026-04-21
delete-safety hardening (`routers/agents.py:1975-1982`), which unified
exact-code and fuzzy-title delete paths to always require confirmation.

- `test_fuzzy_estimate_delete_requires_confirmation`: assertion at
  line 526 changed from `["fuzzy_confirmation"]` to `["confirmation"]`
  to match the unified envelope. The `is_fuzzy_match` flag still
  distinguishes the two paths on the result side.
- `test_exact_estimate_delete_executes_directly` → renamed to
  `test_exact_estimate_delete_requires_confirmation` and the assertions
  flipped: `needs_clarification=True`, `deleted_flags["deleted"] is
  False`, plus `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY` IS now
  present. Source unchanged.

### 97. `text_helpers` import uses private aliases at the call site
**File**: [platform/routers/agents.py:54-56](../../platform/routers/agents.py)
**Severity**: MEDIUM (style)

`routers/agent_helpers/text_helpers.py` exports
`is_affirmative_text` / `is_negative_text` as public functions. The
caller imports them with leading-underscore aliases (`as
_is_affirmative_text`) to avoid touching ~10 call sites inside
`orchestrate_agent_endpoint`. Hides the public/private boundary at the
call site.

Fix: rename the call sites to drop the underscore prefix and remove
the `as` clause. Mechanical, ~10 substitutions.

### 98. No direct unit tests for the four new agent_helpers public functions
**Files**: [platform/routers/agent_helpers/text_helpers.py](../../platform/routers/agent_helpers/text_helpers.py),
[platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py),
[platform/routers/agent_helpers/fuzzy_confirmation.py](../../platform/routers/agent_helpers/fuzzy_confirmation.py)
**Severity**: LOW (refactor, transitively covered)

Public functions added 2026-04-26:
- `is_affirmative_text(text: str) -> bool`
- `is_negative_text(text: str) -> bool`
- `run_update_estimate(...)` (async)
- `handle_estimate_fuzzy_confirmation(...)` (async)

End-to-end coverage exists via `tests/test_agents_api.py` (64 passing)
and `tests/test_orchestrator_endpoint.py`. CLAUDE.md's mandatory-testing
rule applies softly to refactors — but the two text predicates are pure
and would be a 5-minute parametrized test file. The async helpers carry
the same dependencies (DB + EstimateAgent) as the orchestrate endpoint
and are harder to pin in isolation.

Fix: add `tests/test_agent_helpers_text.py` with ~10 parametrized cases
covering each predicate (affirmative, negative, empty, whitespace,
mixed-case, leading/trailing punctuation). Defer the async-helper
direct tests until #94/#95 are split — easier to test smaller units.

---

## 2026-04-27 review (US address parsing + estimate navigation session)

### 99. `_extract_fields_from_message` length growing past 200 lines
File: `platform/agents/property/service.py:369`

Now ~210 lines after the US-style "City, ST ZIP" regex was added. It's a
sequence of 6 independent regex parsers chained by `setdefault`, and every
new address shape will keep accreting. Pre-existing — not introduced by
the US address fix — but worth tracking under the file/function-size theme
in #4.

Fix: when next touched, extract each address-shape parser into a small
helper (e.g. `_try_us_zip_address`, `_try_partial_canadian_address`,
`_try_chunked_canadian_address`) returning a partial dict, with
`_extract_fields_from_message` reduced to a fold:

```python
for parser in (_try_canadian_full, _try_us_zip, _try_chunked, _try_partial, _try_at_prefix):
    for k, v in parser(normalized).items():
        extracted.setdefault(k, v)
```

Each parser becomes individually unit-testable and the coordinator drops
under 50 lines.

### 100. Defensive `|| canEdit` clause in estimate-page row visibility is dead today
File: `portal/src/pages/NewEstimateWithActivityPage.tsx:879`

```tsx
{isEditMode && estimate && (allowedTransitions.length > 0 || canEdit) && (
```

`canEdit` is true only for `draft`/`review`. Both statuses have ≥2
transitions even after the non-admin Approve filter, so
`allowedTransitions.length > 0` is always true when `canEdit` is true.
The `|| canEdit` clause is dead today.

Keeping it is defensible — it documents intent ("show the row when we have
either buttons or a Save to render") and the cost is one boolean OR. But
if `isEditableStatus` or `TRANSITIONS_BY_STATUS` ever changes such that
the implication breaks, the clause would silently start mattering, which
is the kind of thing that surfaces only via a runtime regression.

Fix: either drop `|| canEdit` or add a one-line comment noting the
defensive intent. No runtime impact today.

### 101. US-address regex could match noisy mid-message text
File: `platform/agents/property/service.py:457-480`

The new pattern matches anywhere in the message:
`\d{1,6}` + 3-120 chars + `,` + city + `,` + 2-letter state + space + ZIP.
A free-form sentence like "I owe 23456 dollars, paid via bank, NY 11768
reference" technically matches and would produce spurious `street`/`city`/
`prov_state`/`postal_zip` extractions. The same false-positive surface
exists in the pre-existing Canadian regex variants in this file, so it's
consistent — but worth noting.

Fix: acceptable for now. The downstream Google address-enrichment step or
LLM extraction usually overrides nonsense. If false positives surface in
production, anchor the pattern to the start of a line or after a verb hint
(`at|address[: ]`).

---

## 2026-04-28 `/code-review` pass (Templates resource)

After implementing the Templates CRUD page (model + router + dialog + list).
HIGH (`PUT /templates/id/{id}` allowed cross-tenant move via the request body)
and MEDIUMs (missing `role="alert"` on the dialog error banner; race between
page mount and "New Template" click before company defaults loaded) were
fixed in the same change. The four LOW findings below remain.

### 102. `duplicate` insert lacks 409 fallback
File: `platform/routers/templates.py:120-136`

`_next_copy_name` does a `find_one` for the candidate name, then
`copy.insert()`. Between those two awaits, another caller could insert the
same name, and the unique `(company, name)` index would surface a
`DuplicateKeyError` to the client as a 500 instead of a clean 409.

Fix: wrap the insert in `try/except DuplicateKeyError` and either retry
once with the next `(copy N)` suffix or raise 409. Low likelihood — the
window is sub-millisecond and same-user duplicate spam is the only realistic
trigger.

### 103. `delete_template` returns 200 on non-existent id
File: `platform/routers/templates.py:158-160`

```python
if not template:
    return {"message": "Template not found"}
```

200 with a body that says "not found" is misleading. Mirrors
`routers/labours.py:336-338`, so it's a project convention rather than a
regression. If we ever standardize, fix all four (labours, templates, etc.)
together.

Fix: change to `raise HTTPException(404, "Template not found")` and update
the parallel routers in the same PR.

### 104. `TemplateDialog` captures `initialName` only on mount
File: `portal/src/components/estimates/TemplateDialog.tsx:36`

`useState(initialName ?? "")` reads `initialName` only on first render.
Switching from create-mode to edit-mode without remount would leave `name`
empty. Currently safe because `TemplatesPage.tsx` passes `key={dialogKey}`
and gates with `{isFormOpen && <TemplateDialog ... />}`, forcing a fresh
mount each time.

Fix: only required if either the key or the gate is removed. If so, sync
`name` via a `useEffect` on `initialName` change.

### 105. Templates page re-fetches `/companies/{id}` on every mount
File: `portal/src/pages/TemplatesPage.tsx:60-74`

Every visit to `/templates` re-fetches the company doc just to read profit
margin / overhead / labor burden / tax. Other pages
(`NewEstimateWithActivityPage`, `PeoplePage`) do the same, so it's a
codebase-wide convention.

Fix: hoist company defaults to a context provider or React Query cache in
a follow-up that addresses all the consumers at once. Not worth a one-page
change.

---

## 2026-04-28 `/code-review` pass (Use Template on estimate page)

After wiring `UseTemplateDialog` + the split-button on the estimate detail
page. Two MEDIUMs (search input missing `aria-label`; `setExpandedWorkItemIndex`
read stale closure of `workItems.length`) were fixed in the same change.
The deferred MEDIUM and two LOWs remain.

### 106. `autoFocus` on dialog open may interrupt screen-reader announcements
File: `portal/src/components/estimates/UseTemplateDialog.tsx:84`

`autoFocus` on the search input pulls focus immediately when the dialog
opens. On some assistive tech this races with the modal's open
announcement, so the user hears a partial label. Same pattern is used in
several other dialogs (e.g. `TemplateDialog.tsx`), so it's a codebase-wide
concern, not specific to this dialog.

The standard fix is to focus the modal container (or first heading) on
open and let the user Tab into the search field. That requires changes
inside `components/common/Modal.tsx` and ripples to every dialog. Not
worth a one-dialog fix — defer until an a11y pass that addresses Modal
focus management as a single change.

Fix: address as part of a future Modal a11y refactor; do not patch
per-dialog.

### 107. Inventory-gaps panel does not reflect template-inserted work items until save
File: `portal/src/pages/NewEstimateWithActivityPage.tsx:418-424`

`inventoryGaps` is memoized off `estimate` (the server snapshot), not
`workItems` (the editor state). When a user inserts a template, any
unmatched materials/activities the template carries don't surface in the
gaps panel until the estimate is saved and reloaded. Same behavior as
`handleAddWorkItem` — pre-existing limitation, not a regression — but
worth knowing because templates are more likely to carry unmatched items
than from-scratch work items.

Fix: rebuild gaps from `workItems` rather than `estimate.job_items` so
in-progress edits surface immediately. Out of scope for the Templates
feature; revisit if the gaps panel becomes a primary editing surface.

### 108. `templates.find()` could return undefined on stale state
File: `portal/src/components/estimates/UseTemplateDialog.tsx:51`

If templates were re-fetched mid-confirm and the list shrank,
`templates.find((t) => getEntityId(t) === selectedId)` returns undefined.
The `if (chosen)` guard handles it correctly (the OK click silently does
nothing), so the path is safe. Could improve UX by clearing `selectedId`
when it disappears from the list — but with the dialog gated by
conditional mount, the templates list never refreshes mid-session.

Fix: none required while the dialog is mounted-on-open. If we ever switch
to keep-mounted-with-refresh, add `useEffect` to clear `selectedId` when
it disappears from `templates`.

---

## 2026-04-29 review (improvements.md consolidation)

Items consolidated from `documentation/development/improvements.md`. The
".gitignore `*-key.json` is broad" suggestion from that file was dropped as
already covered by #45 (which explicitly notes the `*-key.json` sibling
pattern is functionally fine).

### 110. `FeedbackPanel` error message has no live-region announcement
**File**: [portal/src/components/common/FeedbackPanel.tsx:169](../../portal/src/components/common/FeedbackPanel.tsx)
**Severity**: LOW (accessibility)

The submission-error div is a plain `<div className="text-xs text-red-600">{error}</div>`.
Screen readers don't announce it when it appears, so a visually impaired
user gets no audible signal that submission failed — they have to walk the
DOM to find out why nothing happened.

Fix: add `role="alert"` (or `aria-live="polite"`) to the error div. The
same applies to `ChangeLogPanel.tsx:166`, which uses the identical
pattern.

### 111. Missing test: anonymous Firebase token → "Unknown User <unknown>" fallback
**File**: [platform/tests/test_feedback_api.py](../../platform/tests/test_feedback_api.py), [platform/routers/feedback.py:87-89](../../platform/routers/feedback.py)
**Severity**: LOW (test gap)

Every existing feedback test injects `X-Test-Email`, so the defensive
branch in `submit_feedback` that handles a verified token *without* an
email (`full_name = "Unknown User"`, `email = "unknown"`) never runs in
the test suite. A regression that breaks the fallback (e.g. a future
refactor that drops the `or "unknown"` clause and 500s instead) would
ship undetected.

Fix: add a test that posts with a token that has `uid` but no `email`,
and assert the Trello card payload is built with `Unknown User <unknown>`.

### 112. Replace `isMountedRef`/`fetchTokenRef` race-guards with `AbortController`
**Files**: [portal/src/components/common/ChangeLogPanel.tsx](../../portal/src/components/common/ChangeLogPanel.tsx), [portal/src/components/common/FeedbackPanel.tsx](../../portal/src/components/common/FeedbackPanel.tsx), [portal/src/api/client.ts](../../portal/src/api/client.ts)
**Severity**: LOW (refactor)

Both panels copy a manual race-guard pattern (`isMountedRef`,
`submitTokenRef` / `fetchTokenRef`, post-await staleness checks) to drop
results from superseded fetches. The cleaner shape is `AbortController`
+ `signal`, but it requires changing the shared API client.

Fix:
1. Teach `apiRequest` in `portal/src/api/client.ts` to accept an
   `AbortSignal` and pass it through to `fetch`.
2. Migrate `ChangeLogPanel` and `FeedbackPanel` together — abort the
   in-flight request on unmount or on a new submit/fetch, then drop the
   ref-based guards.

Migrate both call sites in the same PR so the pattern is consistent.

### 113. Test bypass `FIREBASE_AUTH_DISABLED=true` hides unauthenticated paths
**File**: [platform/tests/conftest.py:7](../../platform/tests/conftest.py)
**Severity**: LOW (testing infra)

The whole suite runs with `os.environ.setdefault("FIREBASE_AUTH_DISABLED", "true")`,
so a test that hits a router without `X-Test-Email` doesn't actually
exercise the Firebase verification path — it just routes through the
test bypass. Endpoints that *should* 401 for missing auth are not
verifying that behavior.

Fix: add a fixture that temporarily clears (or sets to `"false"`) the
flag for the duration of one test, so router-level auth dependencies are
genuinely exercised. Apply it to at least one endpoint per router family
(feedback, change-logs, companies). Treat as shared testing-infra work
rather than per-PR add-ons.

---

## 2026-04-29 `/code-review` pass (public Maple widget)

Hygiene findings from the post-implementation review of the public Maple
Q&A widget (marketing site). HIGH `/code-review` items #3, #5, and #6
landed in the same session; these are the residual MEDIUM/LOW items.

### 114. Unused `Optional` import in `refusal.py`
**File**: [platform/agents/maple_public/refusal.py:21](../../platform/agents/maple_public/refusal.py)
**Severity**: LOW (hygiene)

`from typing import Optional` is imported but no symbol from this module
references it. (Was used before the instructional-question short-circuit
landed and the function signature changed.)

Fix: drop the line.

### 115. Mixed string-vs-regex tuples in `refusal.py`
**File**: [platform/agents/maple_public/refusal.py:27-55](../../platform/agents/maple_public/refusal.py)
**Severity**: MEDIUM (maintainability)

`_ACTION_VERBS` and `_DOMAIN_NOUNS` mostly hold plain strings, but a few
entries embed raw regex fragments (`"set\\s*up"`, `"job\\s*site"`,
`"team\\s*member"`, `"work\\s*item"`, `"rate\\s*card"`). The values are
joined into a `|` alternation and never `re.escape`d. A maintainer
adding a literal noun with a regex metacharacter (e.g. a hyphen, parens,
or a dot) would silently get the wrong match.

Fix: either (a) add a one-line comment near the tuples saying "values
are raw regex fragments — do NOT pre-escape", or (b) split into two
tuples (literal vs regex), `re.escape` the literal one before joining.

### 116. Duplicated "I'm not sure" fallback copy in `service.py`
**File**: [platform/agents/maple_public/service.py:90-91, 194-198](../../platform/agents/maple_public/service.py)
**Severity**: LOW (maintainability)

The "I'm not sure — that's not something I can answer from here. Sign
up at {signup_url} and I can help you with that in the app." line lives
both inside the LLM strict prompt (rule 5) and as the Python-side
fallback when the LLM returns empty content. They will drift over time.

Fix: extract a small helper or module constant that produces the
phrasing; reuse from both sites.

### 117. `_LLMHolder` class is more scaffolding than the use needs
**File**: [platform/agents/maple_public/service.py:99-127](../../platform/agents/maple_public/service.py)
**Severity**: LOW (style)

The lazy-init holder class plus `set_llm_for_tests` is more structure
than the single-LLM use needs. A module-level
`_llm: Optional[ChatOpenAI] = None` plus a getter and a test-only
setter would be flatter.

Fix: optional refactor; not blocking. Keeps the test injection path
clean either way.

### 118. Hand-rolled `import.meta` cast in widget API client
**File**: [website/widget/api.ts:25-27](../../website/widget/api.ts)
**Severity**: MEDIUM (DX)

`(import.meta as { env?: ... }).env?.VITE_PUBLIC_API_URL` works but
exists because the website project doesn't pull in Vite's client
types. Every future env-var lookup in the widget will repeat the cast.

Fix: add a one-line `website/widget/vite-env.d.ts` containing
`/// <reference types="vite/client" />`. Drop the cast and read
`import.meta.env.VITE_PUBLIC_API_URL` directly.

### 119. URL build via string concatenation in widget API client
**File**: [website/widget/api.ts:36](../../website/widget/api.ts)
**Severity**: LOW (robustness)

`resolveApiUrl().replace(/\/+$/, "") + "/public/maple/ask"` hand-rolls
the join. A misconfigured env (e.g. trailing whitespace, missing
scheme, accidental query string) builds a broken URL silently.

Fix: use `new URL("/public/maple/ask", base)`. Surface a clear error
if the base is malformed.

### 120. Unused CSS variable in widget palette
**File**: [website/widget/widget.css:6](../../website/widget/widget.css)
**Severity**: LOW (hygiene)

`--mw-bg-alt: #3b3f5c;` is declared but never referenced.

Fix: remove the line.

### 121. Implicit "welcome bubble has id 0" coupling
**Files**: [website/widget/MapleWidget.tsx:31, 69, 108](../../website/widget/MapleWidget.tsx)
**Severity**: LOW (style)

The widget treats the welcome bubble specially in two unrelated places:
- Line 69: `bubbles.filter((b) => b.id !== 0)` — strip the welcome
  before building the API history.
- Line 108: `showStarterChips = bubbles.length === 1 && !pending` —
  show starter chips only on initial state.

Both rely on the convention that the welcome bubble has id 0 and is
the only bubble at start. A rename / re-numbering would have to touch
both spots.

Fix: tag the welcome bubble with a flag (`isWelcome: true`) on the
`Bubble` type, or move the welcome state into a separate variable
outside the `bubbles` array.

---

## 2026-04-30 `/code-review` pass (HELP intent → users-guide refactor)

Scope: shared `agents.maple_guide` responder, `HelpHandler` rewrite,
public-widget refactor, orchestrator interrogative→guide fallback,
extracted `formatOrchestratorReply` portal utility.

### 122. `_apply_low_confidence_fallback` is now ~84 lines
**File**: [platform/agents/orchestrator/service.py:756-838](../../platform/agents/orchestrator/service.py)
**Severity**: HIGH (function size)

Two responsibilities co-mingled: (1) confidence math + early-return,
(2) the new interrogative→guide fallback decision tree (~50 lines).
Original method was ~30 lines.

Fix: extract `_try_guide_fallback(self, result, message, context,
best_confidence) -> Optional[Dict[str, Any]]`. Caller does
`if (override := self._try_guide_fallback(...)): return override`.
Each method then under ~40 lines.

### 123. `formatOrchestratorReply` mutates input parameter
**File**: [portal/src/lib/orchestratorReply.ts:54](../../portal/src/lib/orchestratorReply.ts)
**Severity**: MEDIUM (mutation)

Sets `result._outOfScope = true` so the caller can read it. Inherited
from the original closure inside `PortalLayout.tsx`, copied verbatim
during the extraction. The extraction was the right time to fix this
contract; we kept it for parity instead.

Fix: return `{ text, outOfScope }` (or a tuple). Caller assigns
`result._outOfScope = outOfScope` explicitly. Cleaner contract; easier
to test side effects independently.

### 124. `openai_api_key=` keyword on ChatOpenAI flags mypy
**Files**:
- [platform/agents/maple_guide/service.py:111](../../platform/agents/maple_guide/service.py)
- [platform/agents/maple_public/service.py](../../platform/agents/maple_public/service.py) (pre-existing — pattern was copied into the new shared module)

**Severity**: MEDIUM (type hygiene)

`openai_api_key` is accepted via Pydantic alias on `ChatOpenAI`, but
mypy reports `Unexpected keyword argument` because the public type
signature uses `api_key`. Pre-existing pattern that propagated into
the new shared service.

Fix: rename to `api_key=settings.openai_api_key` everywhere. Functional
behavior identical; mypy clean.

### 125. `platform/agents/orchestrator/service.py` at 1358 lines
**File**: [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (file size)

Pre-existing breach of the 800-line threshold; this PR added ~70 net
lines. Tracked under existing item [#4](#4-file-and-function-size).

### 126. `portal/src/components/Layout/PortalLayout.tsx` at 2105 lines
**File**: [portal/src/components/Layout/PortalLayout.tsx](../../portal/src/components/Layout/PortalLayout.tsx)
**Severity**: LOW (file size)

This PR shrunk the file by ~35 lines via the
`lib/orchestratorReply.ts` extraction. Continue extracting closures
(`dispatchAgentMutation`, chip-set logic, agent-mutation handlers) into
`lib/` to keep chipping at this. Tracked under existing item [#4](#4-file-and-function-size).

---

## 2026-05-01 `/code-review` pass (Estimate detail UI overhaul + Work Item dialog refactor)

Items below were called out across two `/code-review` passes during a UI
overhaul of `NewEstimateWithActivityPage.tsx` (info/notes/status/docs
icons, auto-saving description+property, Documents dropdown, status
dropdown, Work Items table redesign, and the Work Item editor refactor
from inline expansion to a Cancel/Save dialog).

The two HIGH items addressed in-session:
- Dialog now stays open during save with a "Saving…" state and an
  inline error banner; revert path on failure.
- Material/role gap resolvers fold their resolution into
  `workItemDraft` when the dialog is open, bumping `workItemDialogKey`
  to remount `WorkItemInlineContent` so the change is visible. The Save
  Work Item button is now the persistence path for those edits.

### 127. New-estimate flow has no save mechanism
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH

`persistWorkItems` falls back to `setIsDirty(true)` when not in edit
mode. Save Estimate was removed earlier in the session, so a user on
the new-estimate flow can fill in title/description/work items but has
no UI affordance to actually create the estimate. Pre-existing problem
that the dialog refactor cements.

Fix options:
- Re-introduce a "Create Estimate" button that's only visible on the
  new flow.
- Auto-create the estimate on first interaction (e.g., title blur)
  then fall through to the auto-save path for subsequent edits.

### 128. ~~Title and notes have no auto-save path~~ — RESOLVED 2026-05-01
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH (resolved)

Both fields now auto-save:
- Title: `commitTitle` runs on blur + Enter → `autoSaveField({ title })`,
  with diff guard against `estimate.title`.
- Notes: `saveNotesDialog` runs from the Notes dialog Save button →
  `estimatesApi.update({ notes })`. Diff-guarded against `notes`. Dialog
  stays open during save, shows "Saving…" + inline error on failure;
  Cancel and backdrop close are blocked while saving. Mirrors the work
  item dialog pattern.

### 129. Missing tests for auto-save + dialog flows (partial)
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH

Component-level testing infrastructure landed 2026-05-02:
`@testing-library/react` + `jsdom` added, `vite.config.js` matches
`*.test.tsx` against jsdom. 29 component tests now cover the
extracted dialog/bar wrappers:

- `WorkItemDialog`: title text, Cancel/Save callbacks, disabled state
  while saving, errorMessage rendering.
- `DocumentsBar`: empty-state, auto-seed selection, re-seed when
  current selection becomes stale, generate/delete callbacks.
- `EstimateTitleBar`: read-only ↔ edit transition, blur/Enter commit,
  Details/Notes/Delete callbacks, status menu open + transition.

Still TODO (require deeper page-level mocking):
- `autoSaveField` race-handling end-to-end (the `sequenceGuard`
  helper is unit-tested in `tests/sequenceGuard.test.ts`; the wiring
  inside the page is not).
- `persistWorkItems` insert-vs-replace path.
- `saveWorkItemDialog` failure branches.
- Description blur ↔ stale-comparison wiring (the
  `lastSavedDescriptionRef` invariant; the helper-equivalent test
  for sequence guards is the closest existing coverage).

### 131. `saveError` displayed far from origin
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM

`saveError` (description / property auto-save failures) is rendered in
the Work Items header; users blurring the description at the top of
the page won't see the message if scrolled. Work item dialog now uses
its own `workItemDialogError` so this affects only description and
property.

Fix: render `saveError` adjacent to the field that failed, or use a
toast. Simplest: append a small inline error under the description /
property when their auto-save fails.

### 132. Description read-only color is dead CSS
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM

`className={'... ${canEdit ? "..." : "bg-gray-50 ... text-gray-500"} ${!description ? "text-gray-400" : "text-gray-900"}'}`.
The trailing ternary always wins over the `!canEdit` `text-gray-500`
because Tailwind utilities at the same specificity resolve by
stylesheet source order, not className order. Read-only state ends up
visually identical to editable.

Fix: collapse to one expression:
`canEdit ? (description ? "text-gray-900" : "text-gray-400") : "text-gray-500"`.

### 135. Description "button" wraps multi-line content
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (accessibility)

The read-only description div has `role="button"` and `tabIndex={0}`,
so screen readers announce the entire description as the button's
accessible name. Fine for short text, awkward for long ones.

Fix: add `aria-label="Edit description"` so the announced label is
concise; the visible text remains content.

### 136. Docs menu items missing `role="menuitem"`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (accessibility)

The status dropdown items use `role="menuitem"`; the docs dropdown's
`<a>` / `<button>` items inside `role="menu"` do not. Inconsistent
ARIA.

Fix: add `role="menuitem"` to each item inside the docs `<li>`.

### 137. `NewEstimateWithActivityPage.tsx` extractions (partial)
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (file size)

The three named extraction targets landed 2026-05-02:
`<WorkItemDialog>`, `<DocumentsBar>`, `<EstimateTitleBar>`. Page is
now 1733 lines, down from 2044 — still over the 800-line guideline.
Further reductions need additional extractions:

- Work items table (~250 lines) — header row + map + per-row controls.
- Gap dialogs / inventory gap helpers — currently inline.
- Notes / Details / Delete / Delete-doc modals (small but repetitive).
- `handleChecklistPdfDownload` (currently inline in JSX).

Tracked under existing item [#4](#4-file-and-function-size). Next
single extraction round should target the work-items table.

### 139. Pre-existing `printWindow.document.write` deprecation hint
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW

TS `6387` hint at line ~545 in `handleChecklistPdfDownload`. Predates
this session. Replace with `printWindow.document.body.innerHTML = …`
or build the document via DOM APIs.

---

## 2026-05-01 `/code-review` pass (Green table headings + auto-create estimate)

### 142. Table heading weight drift (`font-medium` → `font-semibold`)
**Files**:
- [portal/src/components/common/EstimatesTable.tsx](../../portal/src/components/common/EstimatesTable.tsx)
- [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx)
- [portal/src/pages/PeoplePage.tsx](../../portal/src/pages/PeoplePage.tsx)

**Severity**: LOW

The 2026-05-01 "apply emerald-100 heading color" change also bumped
`<th>` font weight from `font-medium` to `font-semibold` while
recoloring. The user only asked for a color change. Other tables in
the app still use `font-medium` headers, so this is now inconsistent.

Fix: pick one and apply globally. Either revert these three files to
`font-medium`, or sweep the rest of the codebase up to `font-semibold`.

---

## 2026-05-01 review (Work Item dialog / Estimate page mobile-responsiveness — consolidated from `plans/portal-ui-refactor-followups.md`)

The two HIGH items from this pass (file size of `WorkItemInlineContent.tsx`,
fragile modal stacking) were addressed in the same change set; the items
below are MEDIUM / LOW and were logged for later.

### 144. Alternating row color computed inline twice
**Files**:
- [portal/src/components/estimates/MaterialsTable.tsx](../../portal/src/components/estimates/MaterialsTable.tsx)
- [portal/src/components/estimates/WorkItemInlineContent.tsx](../../portal/src/components/estimates/WorkItemInlineContent.tsx) (Activities table)

**Severity**: MEDIUM

`const rowBg = idx % 2 === 1 ? "bg-emerald-50" : "bg-white"` is
duplicated across two `map()` bodies. Logic is correct (works around
the activities table's sub-row Fragment shifting `:nth-child(even)`
parity) but the rule is in two places.

Fix: extract a shared `getRowBg(idx: number)` helper into a small
utility module or co-locate it where both tables can import it.

### 146. EffortCalculator mobile dropdown initial-render flicker
**File**: [portal/src/components/estimates/EffortCalculatorDialog.tsx](../../portal/src/components/estimates/EffortCalculatorDialog.tsx)

**Severity**: MEDIUM

When the modal opens with `selectedCardId === null` and
`rateCards.length > 0`, the mobile `<select>` shows the first card's
name while the right panel still reads "Select a rate card to begin"
until the parent useEffect fires. Brief visual mismatch.

Fix: initialise `selectedCardId` synchronously via `useState(() => …)`
reading the first rate card so there's no null window. Keep the
existing useEffect for the open/close transitions.

### 147. `MaterialsPage` mobile card popup-clip fix is scoped
**File**: [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx)

**Severity**: LOW

The previous `overflow-hidden` clip was fixed by removing
`overflow-hidden` from the card and adding `rounded-b-xl
overflow-hidden` to the expanded sizes section. This works for the
current popup but if a future popup is added inside the expanded sizes
section it'll be clipped again.

Fix: if/when that case appears, switch popups to render via React
portal so they aren't subject to ancestor clipping.

### 148. Three near-identical settings tabs
**Files**:
- [portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
- [portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx)
- [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx)

**Severity**: LOW

~95% identical markup and state machinery. Each round of UI work
(icon buttons, Actions column width, Name column width) had to be
applied three times. Divergence risk grows.

Fix: extract a generic `<NameDescriptionResourceTab>` component
parameterised by `api`, singular/plural labels, and any tab-specific
extras.

> Note: the seventh portal item ("`NewEstimateWithActivityPage.tsx` is
> 1,990+ lines") duplicates existing finding [#137](#137-newestimatewithactivitypagetsx-at-1900-lines)
> and is tracked there.

---

## 2026-05-02 `/code-review` pass (post-#143/#130/#133/#138 batch)

### 149. `lastSavedDescriptionRef` / `lastSavedTitleRef` initial-value window
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW

The two refs added by #133 (and the title fix that landed alongside)
are initialized to `""` and only seeded to the canonical server value
inside the estimate-load `useEffect`. There is a brief window between
mount and load where the ref is stale.

In practice no save can fire during that window — `autoSaveField`
returns early when `!estimateId`, and the title/description fields
are not interactive until the page renders post-load — so this is
theoretical only. Worth noting for future maintainers who might
introduce a save path that bypasses those guards.

Fix: optional. Either fold the seeding into the `useState` initializer
(reading from a route loader), or leave a stronger inline contract
comment near the ref declarations.

## 2026-05-02 `/code-review` pass (post-#12/#109/#150/#151/#152 batch)

### 153. `_PolicyShortCircuit.response` field name overloaded
**File**: [platform/agents/orchestrator/service.py:188](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (naming clarity)

Found by `/code-review` 2026-05-02 after the #12 extraction landed. The
`response` field on `_PolicyShortCircuit` carries either a refusal
message (negative case — bulk-delete / equipment / category-management)
or `None` (positive `list_material_categories` case, where
`_build_short_circuit_response` hardcodes `"I can help you with that."`).
The polymorphic meaning isn't obvious from the field name and the class
docstring doesn't mention it.

Fix: either rename to `clarification` to match the legacy 5-tuple's
last-position semantics in `_classify_with_rules`, or add a one-line
note in the docstring: "None for positive routings; refusal copy for
negative routings." Cosmetic only — behavior is correct and tested.

### 154. `_TopicFlags.property` field name shadows Python builtin
**File**: [platform/agents/orchestrator/help_handler.py:38](../../platform/agents/orchestrator/help_handler.py)
**Severity**: LOW (naming clarity)

Found by `/code-review` 2026-05-02 after the #150 split landed. The
`_TopicFlags` dataclass field `property` shadows the `property` builtin
within the dataclass scope. Attribute access (`flags.property`) is
safe, but if anyone later writes a bare `property` reference inside
`help_handler.py` they'll get the boolean instead of the decorator.

Fix: optional. Either accept the shadowing trade-off (current state
keeps symmetry with the other domain flags), or rename every flag to
`is_*` for consistency (`is_property`, `is_contact`, etc.).

---

## 2026-05-02 `/code-review` pass (xfail-wave-2 Phase 2)

### 155. ~~`_list_properties_by_cross_resource` is 124 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/property/service.py](../../platform/agents/property/service.py)

Resolved by extracting three helpers:
- `_build_list_properties_envelope` (32 lines) — single response-shape
  builder, replaces 5 duplicate envelope literals.
- `_resolve_estimate_linked_property` (33 lines) — three-step estimate→
  property resolution with `(property, error_message)` return.
- `_resolve_cross_resource_properties` (62 lines) — contact/material/
  labour dispatch returning `(properties, not_found_kind)`. Stays
  slightly over the 50-line ceiling per the original analysis (each
  branch differs by ~3 lines; further splitting is indirection without
  DRY payoff).

Parent function dropped from 248 → 88 lines. Tests
`tests/test_cross_resource_joins.py` and `tests/test_property_agent.py`
both green (67/67).

### 156. ~~`_list_contacts_at_property` is 108 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/contact/service.py](../../platform/agents/contact/service.py)

Resolved by extracting two helpers:
- `_build_list_contacts_envelope` (32 lines) — shared response-shape
  builder, used by both cross-resource handlers in this file.
- `_resolve_contacts_at_properties` (32 lines) — encapsulates the
  property-IDs → contacts join with optional `role_hint == "owner"`
  HOME_OWNER filter.

`_list_contacts_at_property` dropped from 108 → 70 lines.
`_list_contacts_for_estimate` got a free win too (135 → 91 lines)
since both call sites now share the envelope helper. Tests
`tests/test_cross_resource_joins.py` and `tests/test_contact_agent.py`
green (88/88).

### 157. Cross-resource transitive join uses two round-trips instead of $lookup
**File**: [platform/agents/property/service.py:1071](../../platform/agents/property/service.py)
**Severity**: MEDIUM (perf hook)

`_properties_with_estimates_referencing` does TWO Beanie queries —
`Estimate.find` to collect property IDs, then `Property.find` with
those IDs. For tenants with thousands of estimates the first query
loads full estimate documents just to read the `.property` field.

Fix: replace with a single Mongo aggregation pipeline:
```python
Estimate.aggregate([
    {"$match": {"company": ..., "<field>": {"$in": ids}}},
    {"$group": {"_id": "$property"}},
    {"$lookup": {"from": "properties", "localField": "_id",
                 "foreignField": "_id", "as": "property"}},
])
```

Defer until perf measurements demand it; current shape is correct
and clear. Worth coupling with a fixture-based perf test.

### 158. ~~Property cross-resource type=contact loads full catalog~~ — FIXED 2026-05-03
**File**: [platform/agents/property/service.py](../../platform/agents/property/service.py)

Resolved by introducing a `_properties_linked_to_contacts(company_id,
contact_ids)` helper (paralleling `_properties_with_estimates_referencing`)
that runs a single indexed Mongo query
(`Property.find({"company": ..., "contacts": {"$in": contact_ids}})`)
instead of loading the full property catalog and filtering in Python.

The contact path in `_resolve_cross_resource_properties` now calls
this helper. Test
`test_property_agent_lists_properties_for_contact` was updated to stub
the new helper instead of `_list_properties_via_api`. Tests
`tests/test_cross_resource_joins.py` and `tests/test_property_agent.py`
green (67/67).

The pre-existing in-memory pattern in `_find_properties_by_owner_name`
and `_find_properties_by_name_or_address` is a separate refactor —
flagged in #159.

### 159. `agents/cross_resource.py` filters in-Python on full collections
**File**: [platform/agents/cross_resource.py](../../platform/agents/cross_resource.py)
**Severity**: LOW (scaling)

All four `find_X_by_name` helpers load the full collection and filter
in Python. Acceptable for typical company sizes (<1k materials, <100
labour roles, <100 properties) but won't scale to enterprise tenants.

Fix: document the scaling boundary in the module docstring (already
present — "pragmatic for typical company sizes; revisit if a tenant
exceeds ~10k properties"). Future refactor: push substring matching
to MongoDB via `$regex` filters with case-insensitive option.

---

## 2026-05-02 `/code-review` pass (xfail-wave-3 — all three workstreams)

Surfaced after shipping `documentation/development/plans/maple-xfail-wave-3.md`
(partial-bulk delete refusal + material query variants + estimate filters &
drilldowns). Code review found 0 CRITICAL / 0 HIGH; only MEDIUM / LOW
follow-ups below. The `_OPEN_ESTIMATE_STATUSES` hardcoded-strings
fragility was caught and fixed inline during the review (now derived
from `EstimateStatus.{DRAFT,APPROVED,REVIEW,WON}.value`).

### 160. ~~`_handle_list_materials_for_estimate` is 98 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)

Resolved by:
- Local `clarification()` closure dedupes the two clarification-shape
  envelope returns inside the handler.
- New `_collect_estimate_material_items` static helper (27 lines) flattens
  matched + unmatched materials into display dicts (was a 22-line inline
  loop with `(unmatched)` suffix duplication).

Handler dropped from 98 → 74 lines. Still slightly over the 50-line
guideline, but the remaining body is the final result-shape dict
(used once) plus the items-empty / items-present branching — extracting
further would add indirection without DRY payoff.

The followup's "agent-wide envelope helper across `_handle_list_estimates`,
`_handle_create_material`, etc." is a separate, larger pass — out of
scope for this fix.

### 161. ~~`_handle_list_labours_for_estimate` is 91 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/labour/service.py](../../platform/agents/labour/service.py)

Same shape as #160; same fix:
- Local `clarification()` closure for the two clarification returns.
- New `_collect_estimate_labour_items` static helper (26 lines).

Handler dropped from 91 → 73 lines. Tests
`tests/test_cross_resource_joins.py`, `tests/test_material_agent.py`,
and `tests/test_labour_agent.py` green (101/101).

### 162. `_parse_estimate_date_filter` uses fixed day counts
**File**: [platform/agents/estimate/service.py:354](../../platform/agents/estimate/service.py#L354)
**Severity**: LOW

`days_per_unit = {"day":1, "week":7, "month":30, "quarter":91, "year":365}`
— calendar-month edges and leap years are not handled. "Estimates from
this month" on Jan 31 will look back to Jan 1, but on Mar 1 will look
back to Jan 30, not Feb 1. Matches the docstring's "no calendar-month
edge cases" note but worth flagging.

Fix: swap to `dateutil.relativedelta` (already a transitive dep of
`langchain` so no new requirement) for strict calendar-aligned windows
when a user complaint surfaces. Defer until then.

### 163. Wave 3 file growth — three large agent files grew further
**Files**:
- [platform/agents/material/service.py](../../platform/agents/material/service.py) — 2,560 → 2,659 lines
- [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) — 5,719 → 5,873 lines
- [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py) — 1,712 → 1,830 lines

**Severity**: MEDIUM

Pre-existing condition (all three were already far above the 800-line
CLAUDE.md guideline before Wave 3); this change does not make it
materially worse but contributes ~370 lines across the three files.
Tracked here so the pressure stays visible.

Fix: one of three options for each file —
- Material: extract `_handle_list_materials_for_estimate`, `_handle_get_material`, `_handle_list_materials` into a `material/handlers/` package.
- Estimate: split the 5,873-line file by phase (generation / extraction / CRUD / status-transitions are natural seams).
- Orchestrator: extract `_match_size_scoped_material_op`, `_match_possessive_or_field_targeted`, `_match_cross_resource_query` into `orchestrator/matchers/` modules.

Out of scope for any single feature commit; would warrant its own refactor PR.

### 164. `find_estimate_by_code` loads full estimate collection
**File**: [platform/agents/cross_resource.py:97](../../platform/agents/cross_resource.py#L97)
**Severity**: LOW (scaling)

Mirrors the existing `find_properties_by_name_or_address` /
`find_materials_by_name` pattern (in-memory linear scan after loading
the company's full estimate collection). Pragmatic for typical company
sizes; could matter once a tenant exceeds ~1k estimates.

Fix: replace with a Beanie indexed lookup —
```python
return await Estimate.find_one(
    Estimate.company == PydanticObjectId(company_id),
    Estimate.estimate_id == code_text.upper(),
)
```
Requires confirming there's an index on `(company, estimate_id)`; if
not, add one in `database.py:init_db()`.

---

## 2026-05-03 `/code-review` pass (post-#155/#156/#158/#160/#161 batch)

Surfaced after the five-item refactor batch landed. No CRITICAL / HIGH
findings; the four notes below are accepted trade-offs from the batch
itself, logged for visibility so future refactors don't re-discover
the same questions.

### 165. `_list_properties_by_cross_resource` still 88 lines
**File**: [platform/agents/property/service.py:1078](../../platform/agents/property/service.py#L1078)
**Severity**: MEDIUM (function-length policy)

After #155 the parent dropped from 248 → 88 lines. Still over the
50-line CLAUDE.md guideline. Remaining body: estimate-branch label
pick + final response-rendering tail (which already calls the shared
`_build_list_properties_envelope` helper).

Accepted as-is. Splitting further pushes one-line dispatch into helpers
without DRY payoff. Re-flag only if a future change makes the function
harder to read.

### 166. `_list_contacts_for_estimate` still 91 lines
**File**: [platform/agents/contact/service.py:1092](../../platform/agents/contact/service.py#L1092)
**Severity**: MEDIUM (function-length policy)

Got a free DRY win during #156 (135 → 91 lines via shared envelope
helper) but remains over 50. Three guard clauses (estimate not found /
property not linked / property deleted) + property_label compute +
items-empty branching.

Fix (deferred): extract `_resolve_estimate_linked_property` (currently
only on the property agent) into `agents/cross_resource.py` so both
agents share a single estimate→property resolver. Drops the contact
helper to ~50 lines and removes the parallel implementation.

### 167. `_resolve_cross_resource_properties` at 62 lines
**File**: [platform/agents/property/service.py:1015](../../platform/agents/property/service.py#L1015)
**Severity**: LOW (function-length policy)

Three near-identical contact / material / labour resolve+filter blocks
with ~3-line differences each. Extracted intentionally during #155;
the original analysis flagged "splitting per-type resolution into 3
helpers would add indirection without DRY payoff."

Accepted as-is. Re-evaluate only if a fourth cross-resource type joins
the dispatch.

### 168. New helpers from #155/#156/#158/#160/#161 lack direct unit tests
**Files**: property / contact / material / labour `service.py`
**Severity**: LOW (test coverage)

Nine new private helpers landed across the batch:
- `_build_list_properties_envelope`, `_resolve_estimate_linked_property`,
  `_resolve_cross_resource_properties`, `_properties_linked_to_contacts`
  (property agent)
- `_build_list_contacts_envelope`, `_resolve_contacts_at_properties`
  (contact agent)
- `_collect_estimate_material_items` (material agent)
- `_collect_estimate_labour_items` (labour agent)

All are exercised end-to-end by the existing 67–101 integration tests
(`tests/test_cross_resource_joins.py`, `test_property_agent.py`,
`test_contact_agent.py`, `test_material_agent.py`, `test_labour_agent.py`)
that pass after the refactor.

Per CLAUDE.md "Don't docstring private helpers" / pragmatic-coverage
norms: integration coverage is sufficient for pure refactors. Re-flag
only if these helpers grow public-facing semantics or if a regression
slips through that a unit test would have caught.

---

## 2026-05-03 `/code-review` pass (Maple FAB + Modal AI-panel awareness)

Findings from the session that introduced `AiPanelContext`, the Modal
backdrop carve-out for the desktop Maple rail, and the bottom-right
floating Sparkles button. The actionable items (decoupling divisions
fetch, FAB ARIA, removing the unused `coverAiPanel` prop) were fixed in
the same change. The items below were deferred.

### 169. `PortalLayout.tsx` is ~1500 lines
File is well over the 800-line guideline. The session's edits added
~10 lines on top of an already over-budget file. Natural extraction
candidates: the AI panel composer + message renderer, the settings/
account modal, and the feedback/changelog panel wiring — each ~200-300
lines and largely self-contained.

Pre-existing; flagging here so it's recorded against this file
specifically rather than rediscovered each pass.

### 170. No component tests for `Modal` or `DashboardPage` division-seeding behavior
CLAUDE.md mandates tests for behavior changes; the portal currently has
no component-test infrastructure under `src/` (vitest is configured at
the package level via `npm test`, but there are zero `*.test.tsx` files).
The Modal change (conditional positioning when AI panel is open) and
the Dashboard division-seeding logic are untested as a result.

First component test added will need to pull in
`@testing-library/react` + jsdom setup — not a one-line task. Worth
landing once another test-worthy frontend change comes along so the
scaffolding pays for itself.

### 171. `lg:right-[26rem]` in `Modal.tsx` duplicates `AI_PANEL_WIDTH`
`Modal.tsx:32` hard-codes `lg:right-[26rem]` to match the desktop Maple
rail width, which is also declared in `PortalLayout.tsx:129` as
`AI_PANEL_WIDTH = 416 // w-[26rem]` and on the `<aside>` itself as
`w-[26rem]`. Three sites must agree; if the rail width changes, the
modal backdrop will silently misalign.

Fix: export an `AI_PANEL_WIDTH_CLASS` (or similar) constant from a
shared module (e.g. `lib/aiPanelContext.ts`) and reference it from all
three sites — or expose the value via `AiPanelContext` so consumers
build the className dynamically.

---

## 2026-05-04 `/code-review` pass (Adjust Work Item Total feature)

Findings from the session that added the "Adjust" pill on the Work Item
Total row, the `AdjustTotalDialog` component, the `original_profit_margin`
field round-trip (frontend type + backend `JobItem`), the
`backCalculateProfitMargin` helper, and the `NumericInput` precision-
preserving blur. The lint error caught during review
(`react-hooks/set-state-in-effect` on `AdjustTotalDialog`) was fixed in
the same change by remounting the dialog via a `key` prop on open. All
items below were deferred.

### 172. `WorkItemInlineContent.tsx` now 834 lines (over the 800-line HIGH threshold)
This change pushed the file from ~760 to 834 lines (Adjust pill + dialog
mount + Original line + handleAdjustSet + handleProfitMarginChange +
originalTotal useMemo). The component was already at the limit before
this feature.

Natural extraction: the entire Pricing Breakdown block (Materials/Labor
subtotals → Overhead → Subtotal → + Profit → Tax → Work Item Total → Adjust
pill → Original line) is a self-contained ~150-line slice that takes only
the breakdown numbers and a handful of setters as props. Pulling it into
a `WorkItemPricingBreakdown` component would restore this file to under
800 lines and isolate the back-calc / Original-line logic with the rest
of the pricing UI.

### 173. `<input>` in `AdjustTotalDialog` uses `aria-label`, not a real `<label>`
`AdjustTotalDialog.tsx:65–73` — the visible "Adjust Amount" text comes
from the modal title (`<h3>`), not from a `<label htmlFor=…>` on the
input. The input has `aria-label="Adjust Amount"`, so screen readers do
announce the field correctly, but there's no clickable visual association
between the heading and the input.

Fix: render an explicit `<label htmlFor="adjust-amount-input">Adjust
Amount</label>` inside the modal body and drop the `aria-label`. Keep
the modal's `<h3>` title as-is for the dialog heading. Minor a11y polish.

### 174. Reset button doesn't refocus the input
`AdjustTotalDialog.tsx:77` — clicking Reset replaces the input value but
leaves keyboard focus on the Reset button. Users frequently want to
glance at or tweak the field before clicking Set.

Fix: hold a `useRef` on the input and call `inputRef.current?.focus()`
inside the Reset handler. Tiny UX polish.

### 175. `JobItemCreate` margin/tax fields accept unbounded floats
`platform/routers/estimates.py:609–614` — `original_profit_margin`,
`profit_margin`, `overhead_allocation`, `labor_burden`, and `tax` are all
`Optional[float] = None` with no bounds. Pydantic accepts NaN, ±Infinity,
and arbitrarily large/negative values. A malicious or buggy client could
persist garbage. Pre-existing pattern across the model — I added one more
field with the same loose typing rather than tightening it.

Fix: introduce shared `Annotated[float, Field(ge=…, le=…, allow_inf_nan=False)]`
type aliases for percentage fields (e.g. `PercentField`) and apply across
`JobItemCreate` + the corresponding `JobItem` model fields. Coordinate so
existing data still validates on read (use `model_validate` not strict
parsing on legacy docs).

---

## 2026-05-05 `/code-review` pass (header recolor + Maple FAB realignment + NumericInput blur-format)

### 176. `PortalLayout.tsx` is ~1500 lines (pre-existing)
`portal/src/components/Layout/PortalLayout.tsx` — sidebar, mobile sidebar,
top-bar logo regions, AI panel header (desktop + mobile), the floating
Maple FAB, and the Account modal all live in one file. Not introduced by
this change, but every edit here adds reach.

Fix: split into siblings — at minimum `MapleFloatingButton`, `AiPanel`,
and `AccountModal`. Out of scope for the recolor work; track for the next
time someone touches this file substantially.

### 177. Grand Total contrast borderline at small text sizes
`portal/src/pages/NewEstimateWithActivityPage.tsx:1273` — the new
`bg-total-bg` (`#38A776`) with `text-white` measures ~3.03:1. Passes WCAG
AA only via the large-bold exemption (text is `text-lg font-bold`).
Acceptable here, but if the same token is reused for normal-weight or
smaller text it will fail AA.

Fix: if reuse is needed, define a darker variant (e.g.
`--total-bg-strong: #2E8A60`) for normal-weight text. Or document on the
token in `theme.css` that it's only safe for large-bold copy.

---

## How to work through this

1. Pick ONE HIGH item per work session. Don't batch.
2. Write the failing test first (TDD per `CLAUDE.md`).
3. Run the related test file, not the full suite.
4. Commit each item as its own PR — easier to revert, easier to review.
5. Delete the bullet from this file in the same PR.

When this file is empty, delete it.
