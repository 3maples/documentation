# Code Review Follow-ups — Archive (Closed Items)

_Split out of [`code-review-followups.md`](code-review-followups.md) on 2026-06-13 to keep the live tracker scannable._

These items are **resolved/closed** and kept only for historical reference and to
preserve numbering for cross-references in the live list. Sorted by item number.
When closing a new item, mark it RESOLVED in the live tracker, then relocate it
here in the next cleanup pass.

---

### 7. [HIGH] Missing tests for new public functions
**Closed as resolved 2026-05-13.** All 10 absorbed children backfilled with direct test coverage. 209 tests added across 9 new files + 1 extended file:

- **#36** → `platform/tests/test_generate_google_doc_router.py` (8 tests, single-`Contact.find` regression assertion)
- **#51** → `platform/tests/test_orchestrator_bare_entity_helpers.py` (42 tests)
- **#85** → `platform/tests/test_estimate_crud_handler_helpers.py` (16 tests)
- **#98** → `platform/tests/test_agent_helpers_text_predicates.py` (63 tests for `is_affirmative_text` / `is_negative_text`; `run_update_estimate` and `handle_estimate_fuzzy_confirmation` covered separately by prior `test_agent_helpers_estimate_update.py` and `test_agent_helpers_fuzzy_confirmation.py`)
- **#111** → `platform/tests/test_feedback_anonymous.py` (4 tests for "Unknown User" fallback)
- **#129** → `portal/tests/NewEstimateWithActivityPage.autosave.test.tsx` (6 tests via RTL)
- **#168** → `platform/tests/test_cross_resource_envelope_helpers.py` (40 tests across 10 helpers — verification found one more helper than originally listed)
- **#217** → `portal/tests/PlanPickerGrid.test.tsx` extended (+3 tests: aria-hidden price slot, button order, `text-foreground` class)
- **#227** → `website/functions/joinWaitlist.test.js` (8 tests on Cloud Function; vanilla-JS modal skipped — no test infra under `public/`)
- **#232** → `platform/tests/test_material_response_envelope.py` (19 tests)

Bugs/curiosities surfaced during backfill (not fixed; worth tracking as new follow-ups):
- `_is_bare_entity_reference` for the contact domain skips the stopword guard — `"Hello Smith"` passes as a bare-entity reference.
- `_PERSON_NAME_PATTERN` rejects `"O'Brien"` / `"Smith-Jones"` when the post-apostrophe/hyphen word starts uppercase — likely a latent regex bug for Irish/hyphenated surnames.
- `_coerce_company_oid` returns `None` on whitespace-only input via the `PydanticObjectId` path, not the early `if not company_id` guard.
- `joinWaitlist` Cloud Function uses strict-equality (`=== true`) coercion; non-boolean payloads silently resolve to `false`. Safe in current frontend usage but worth knowing.

<details>
<summary>Original body (preserved for history)</summary>

Per `CLAUDE.md` mandatory-testing rule. To identify gaps: for each new public
function added in the last N commits, verify there's a corresponding
`tests/test_<module>.py::test_<fn>`. A `coverage report` run against
`routers/` and `agents/` will spotlight the red lines.

Specific instances surfaced in later passes:
- **#36:** No unit test for the N+1 batch fix in `generate_google_doc`.
- **#51:** New orchestrator bare-entity helpers covered only end-to-end.
- **#85:** `_estimate_load_error_envelope` / `_coerce_company_oid` lack direct tests.
- **#98:** Four new `agent_helpers/` public functions lack direct tests.
- **#111:** Anonymous Firebase token → "Unknown User" fallback never exercised.
- **#129:** Page-level auto-save + dialog flows still need page-level tests.
- **#168:** Nine new cross-resource agent helpers covered only via integration tests.
- **#217:** New `PlanPickerGrid` behaviors lack assertions.
- **#227:** New `joinWaitlist` field has no automated tests.
- **#232:** `_build_response_envelope` lacks a direct shape test.

**Absorbed:** #36, #51, #85, #98, #111, #129, #168, #217, #227, #232 — specific test-gap instances surfaced in later review passes. See `## Closed` for original bodies.

</details>

---

### 18. [MEDIUM] File-size threshold — `agents/estimate/service.py` now at 5,098 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: MEDIUM (architectural drift)

Entry #4 above already flags the HIGH-threshold files. Updating the
numbers: after the 2026-04-22 session, `agents/estimate/service.py` is now
~5,098 lines, `routers/agents.py` is ~2,892, `routers/estimates.py` is
~2,548. The extraction plan in entry #4 still applies; nothing added this
session is individually large, but the pile keeps growing.

</details>

---

### 36. [MEDIUM] No unit test for the N+1 batch fix in `generate_google_doc`
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 37. [LOW] ~~`_handle_get_estimate` falls through to an unscoped `Estimate.find_one` when `company_id` is invalid~~ — RESOLVED 2026-05-07

Fixed in commit `dfb8184` (2026-05-07). `_handle_get_estimate` now coerces
`company_id` to `company_oid` immediately after the latest-estimate
shortcut and returns the same "need a company" clarification envelope
that `_handle_list_estimates` uses when the cast fails. The downstream
`Estimate.find_one(...)` is now scoped via `Estimate.company == company_oid`,
closing the cross-tenant fallback. Original entry below.


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

---

### 40. [MEDIUM] ~~`portal/firebase.json` has no security-header config~~ — RESOLVED 2026-05-07

Landed in commit `692069f` ("chore: add HSTS and clickjacking headers to
firebase hosting config"). `portal/firebase.json` now ships all four
recommended headers on every response: `Strict-Transport-Security:
max-age=31536000; includeSubDomains`, `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
A real CSP is still a larger undertaking and remains deferred. Original
entry below.


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

---

### 41. [MEDIUM] ~~`except Exception` around httpx calls in `address_service.py` could mask future `HTTPException`~~ — RESOLVED 2026-05-07

Narrowed to `except (httpx.HTTPError, httpx.TimeoutException):` in
`autocomplete`, `resolve_place_id`, and `normalize_address_parts`. Added
`test_google_address_service_propagates_http_exception_from_inside_request`
which monkeypatches `httpx.AsyncClient.get` to raise
`HTTPException(429)` from inside the `try` and asserts all three methods
re-raise instead of returning empty results. Original entry below for
context.


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

---

### 42. [MEDIUM] ~~No unit test for the `handleStatusChange` dispatcher~~ — RESOLVED 2026-05-07

Extracted `resolveStatusChangeApi(currentStatus, target, { approvedBy })`
as a pure helper alongside `getAllowedTransitions` in
`portal/src/lib/estimateStatus.ts`. Returns
`{ kind: "archive" | "unarchive" | "update", payload?: { status?: string;
approved_by?: string } }`. `NewEstimateWithActivityPage.handleStatusChange`
is now a thin switch on `kind`. Six new unit tests in
`tests/estimateStatus.test.ts` cover all routing branches (archive,
unarchive-from-archived-only, approved+approver, plain status update,
review-from-non-archived). Original entry below.


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

---

### 46. [LOW] ~~State machine is frontend-only (by design, re-filed for visibility)~~ — RESOLVED 2026-05-09

Backend now mirrors `portal/src/lib/estimateStatus.ts:TRANSITIONS_BY_STATUS`.
Added `ESTIMATE_STATUS_TRANSITIONS` map + `validate_estimate_status_transition(current, target)`
helper in `platform/models/estimate.py`. The PUT `/estimates/{id}` handler
calls the validator after `parse_estimate_status` and raises
`HTTPException(400, "Invalid transition: {current} → {target}")` on
forbidden moves (Lost → Won, Won → Approved, OnHold → Draft, etc.).
`Approved` retains the "unapprove" escape hatch (any non-Approved target)
so the existing role-gated unapprove flow keeps working; legacy/system
statuses (Generating/Failed/Submitted/Scheduled/Completed/Deleted) are
unconstrained.

Tests: 11-case `TestValidateEstimateStatusTransition` unit class plus
`test_update_estimate_rejects_invalid_status_transition` integration test
(Lost → Won returns 400, Lost → Review returns 200). All 88
`tests/test_estimate_api.py` cases plus the related versioning / quota
suites green.


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

---

### 48. [MEDIUM] ~~`_LABOUR_ROLE_TOKENS` drifts from `DOMAIN_HINTS["labour"]`~~ — RESOLVED 2026-05-07

Added `LABOUR_ROLE_HINTS: Tuple[str, ...]` export to
`agents/orchestrator/intents.py` as the single source of truth for the
sufficient-on-their-own role tokens. `_LABOUR_ROLE_TOKENS` in
`service.py` now derives via `frozenset(LABOUR_ROLE_HINTS)`. New test
`test_labour_role_hints_are_single_source_of_truth` asserts the role
hints are a subset of `DOMAIN_HINTS["labour"]` and equal to the
service-level frozenset. Adding a new role now means appending to one
constant. Original entry below.


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

---

### 50. [MEDIUM] ~~Duplicate stopword lists in the orchestrator~~ — RESOLVED 2026-05-07

Extracted `_COMMON_FILLER_STOPWORDS` frozenset (19 entries — the
greeting/pronoun/acknowledgement fillers shared by both heuristics).
`_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` now derive
via `_COMMON_FILLER_STOPWORDS | frozenset({...domain-specific delta})`.
New test `test_stopword_sets_share_common_filler_base` asserts the
common set's exact contents and that both downstream sets are
supersets. Original entry below.


**File**: [agents/orchestrator/service.py:88, :130](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

`_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` share ~14
entries (`hi`, `hey`, `the`, `that`, `my`, `your`, `our`, `no`, `yes`,
`ok`, `okay`, `thank`, `thanks`, `please`, `sorry`). Two lists to keep
in sync when adding a new filler.

Fix: extract `_COMMON_FILLER_STOPWORDS` frozenset; union with
domain-specific additions for each downstream use.

---

### 51. [MEDIUM] No direct unit tests for the new bare-entity helpers
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 52. [LOW] Inline comments instead of docstrings on new helpers
**Folded into #10.** Specific instance of the "missing docstrings on public APIs" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [agents/orchestrator/service.py:395, :404](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (style)

Project leans toward docstrings on methods (see `_format_chat_history`,
`_build_entity_context_summary`, etc.). My new helpers use inline
`# ` comments instead. Cosmetic only.

Fix: convert the prose comments to proper docstrings. Do when next
touching the file.

</details>

---

### 54. [LOW] ~~Tier 1 gap: `set <name>'s <field> to <value>` pattern~~ — RESOLVED 2026-05-07

Closed without changing `ACTION_HINTS["update"]`. The dedicated
`SET_POSSESSIVE_UPDATE_PATTERN` regex (`agents/text_utils.py:467`) and
`FIELD_OF_UPDATE_PATTERN` (`agents/text_utils.py:481`) — invoked from
`_match_possessive_or_field_targeted` — now handle the `set X's Y to Z`
and `set the <field> of/on/for <name> to <value>` shapes for all four
resources. The latest `tests/reports/maple_crud_gap_report.md` confirms
Tier 1 ✅ for every documented `set …` phrasing.

Adding a bare `"set"` (or `"set "`) entry to `ACTION_HINTS["update"]`
was rejected: the matcher uses `text.find()` substring scan, so `"set "`
false-positives on tokens like `asset `, `subset `, and `sunset `,
which would mis-route benign phrasings to update.

---

### 56. [LOW] Tier 1 gap: `what's <name>'s <field>?` contraction not handled
**File**: [agents/orchestrator/intents.py:131-150](../../platform/agents/orchestrator/intents.py) (`ACTION_HINTS["get"]`)
**Severity**: LOW

`ACTION_HINTS["get"]` contains `"what is"` but not `"what's"` — the
contraction. Phrasings like `"what's John Doe's phone?"` or `"what's
Landscaper's cost?"` therefore fail rule-level action detection, even
when the domain resolves via `phone` / `cost` / the name heuristic.

**RESOLVED 2026-05-07** — closed without changing `ACTION_HINTS["get"]`.
The `POSSESSIVE_LOOKUP_PATTERN` invoked from
`_match_possessive_or_field_targeted` (Shape 3) now anchors before
action-hint matching and resolves `[verb] <name>'s <field>` /
`<name>'s <field>` directly to `get_<domain>`, bypassing the
contraction gap entirely. The latest `tests/reports/maple_crud_gap_report.md`
shows ✅ Tier 1 for every `what's <name>'s <field>?` case across all
four resources.

---

### 58. [HIGH] `PortalLayout.tsx` over the 800-line HIGH threshold (canonical)
**Closed as resolved 2026-05-13.** Multi-session refactor reduced PortalLayout.tsx from 1,923 to under 800 lines across 5 sessions. Final state: 598 lines. Extractions: CompanyDialog, SettingsDialog, TeamMembersDialog, AiPanel, and hooks (useMapleAgent / useCompanyDetails / useAccountForm). All session diffs are byte-preserving refactors; user smoke-tested at each step.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: HIGH (in progress — partial 2026-05-09)
Canonical entry; #169 and #176 are duplicate flags from later review
passes — consolidated here on 2026-05-09.

Progress 2026-05-09: extracted pure-data and pure-helper layers out of
the file:
- `components/Layout/portalLayoutData.ts` — `countryOptions`,
  `canadaProvinceOptions`, `usStateOptions`, `ProvinceStateOption`
- `components/Layout/portalLayoutHelpers.tsx` — `getCompanyFormState`,
  `getAccountFormState`, `createConversationId`,
  `isAuthenticatedMember`, `ThinkingIndicator`, plus the
  `CompanyFormState` / `AccountFormState` / `CompanyDetails` /
  `PortalUser` / `TeamMember` interfaces.

Result: 2,094 → 1,917 lines. Still over the 800 HIGH threshold; full
suite (477 portal tests) and `tsc --noEmit` both clean.

Progress 2026-05-19: extracted the Company settings dialog into
`components/Layout/CompanyDialog.tsx` (~364 lines moved). The new
component takes 14 props (open, onClose, isLoading, isEditing,
isSaving, companyDetails, companyForm, companyFormError,
provinceStateOptions, provinceStateLabel, onEdit, onCancelEdit, onSave,
onFieldChange). PortalLayout.tsx now at 1,559 lines. Lint + build
clean; no PortalLayout component tests exist yet so verification is
build-level only.

Progress 2026-05-19 (session 2): extracted the Account/Settings modal
into `components/Layout/SettingsDialog.tsx` (~119 lines moved, 174-line
new file). The new component takes 11 props (open, onClose,
currentUser, accountForm, accountFormError, isAccountEditing,
isAccountSaving, onAccountFieldChange, onAccountEdit,
onAccountCancelEdit, onAccountSave). PortalLayout.tsx now at 1,440
lines. Also removed now-unused `PhoneInput` and `formatPhone` imports
from PortalLayout.tsx. Lint, `tsc --noEmit`, and build all clean.

Progress 2026-05-19 (session 3): extracted the Team Members modal into
`components/Layout/TeamMembersDialog.tsx` (~68 lines moved, 107-line
new file). The new component takes 6 props (open, onClose, teamMembers,
isTeamMembersLoading, teamMembersError, currentUser). PortalLayout.tsx
now at 1,372 lines. Also removed now-unused `Modal` and
`isAuthenticatedMember` imports from PortalLayout.tsx. Lint,
`tsc --noEmit`, and build all clean. The right-side Maple AI panel
state extraction was considered but deferred: `aiContext`,
`currentViewedEstimate`, and several effects cross panel/route/company
boundaries (e.g. `aiContext` is rewritten on company-change events and
route changes, not just by panel handlers), so a clean hook boundary
requires more tracing than fits a single bounded session.

Progress 2026-05-19 (session 4): extracted the Maple AI panel
(desktop right-side aside + mobile bottom-sheet aside + floating
toggle button + message/composer render helpers) into
`components/Layout/AiPanel.tsx` (~216 lines moved, 308-line new
file). State stays in PortalLayout; AiPanel is purely presentational
with 18 props across 5 categories: open state (2), conversation
state (4), composer callbacks (5), refs (2), side-panel state (4),
nav-footer JSX (1). The `HELP_CHIPS` constant and `AiMessage`
interface moved with the component (AiMessage re-exported and
re-imported by PortalLayout for its useState typing). Also removed
now-unused `Send`/`Trash2`/`Loader2` lucide imports and
`MapleMarkdown`/`ThinkingIndicator`/`FeedbackPanel`/`ChangeLogPanel`
imports from PortalLayout.tsx. PortalLayout.tsx now at 1,156 lines
(cumulative 1,923 -> 1,156 across sessions 1-4 = 767 lines reduced).
AiPanelProvider boundary stays in PortalLayout wrapping the whole
tree, untouched. Lint, `tsc --noEmit`, and build all clean.

Progress 2026-05-13 (session 5): extracted `useMapleAgent` /
`useCompanyDetails` / `useAccountForm` hooks (~558 lines moved across
three new files: useMapleAgent.ts 398 lines, useCompanyDetails.ts 233
lines, useAccountForm.ts 135 lines). PortalLayout.tsx now at 598
lines — under the 800-line threshold. The combined company-changed
+ estimate-loaded `useEffect` was split into two independent effects
(one per hook); both register listeners on mount with `[]` deps and
have no shared state, so behavior is identical. Lint, `tsc --noEmit`,
and build all clean.

Next steps (left for a planned session — risky without component
tests for `PortalLayout`): extract the three big in-file modals
(Settings ~130 lines, Company ~378 lines, TeamMembers ~74 lines), the
mobile + desktop AI panel branches, and the `MapleFloatingButton`.
The Maple panel (header + messages + composer + footer +
Feedback/ChangeLog overlays) is a natural `components/maple/MaplePanel.tsx`
with a `variant="mobile" | "desktop"` prop since both branches render
nearly-identical markup. Until component tests exist for PortalLayout,
each modal extraction needs a manual UI smoke test.

**Absorbed:** #126, #169, #176 — duplicate findings on the same file from later review passes. See `## Closed` for their original bodies.

</details>

---

### 65. [MEDIUM] ~~"Unknown" division is selectable in the Work Item dropdown~~ — RESOLVED 2026-05-07

Closed in two stages:
1. Commit `1b75358` ("fix: render Unknown division fallback option as
   disabled") — first pass making the fallback non-selectable.
2. Commit `2008afe` ("feat: map legacy Others division to Unassigned in
   the FE") — replaced the unrecognized "Unknown" sentinel with
   "Unassigned", which is now a first-class division in the BE
   (`EstimateDivision.UNASSIGNED`), the seed CSV
   (`platform/data/default_divisions.csv`), and the FE resolver
   (`portal/src/lib/divisionResolve.ts`). New companies bootstrap with
   "Unassigned" as a real division row, so the synthetic dropdown option
   appears only for legacy companies — and persisting it now writes the
   universally-recognized sentinel rather than a dead string. Aggregation
   helpers (`resolveDivisionName`, `bucketJobItemsByDivision`,
   `filterStaleDivisions`) all bucket stale/missing values back into the
   "Unassigned" canonical name.

Coverage: `portal/tests/divisionResolve.test.ts` (resolution,
bucket-into-Unassigned, legacy-Others rewrite, stale-name handling) and
`portal/tests/WorkItemInlineContent.test.tsx` (`stale division values
not in the company list are mapped to "Unassigned"`).


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

---

### 66. [MEDIUM] No unique compound index on Division `(name, company)`
**Folded into #60.** Specific instance of the "compound-index data-integrity" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 81. [MEDIUM] ~~`react-hooks/exhaustive-deps` disabled in 3 new settings tab components~~ — RESOLVED 2026-05-07

Wrapped `fetchDivisions` / `fetchUnits` / `fetchCategories` in
`useCallback(..., [companyId])` and added the callback to the effect's
dependency array — matches the pattern in `RateCardsTab.tsx`. The three
`// eslint-disable-next-line react-hooks/exhaustive-deps` comments are
gone. Original entry below.


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

---

### 84. [MEDIUM] `_coerce_company_oid` returns `Optional[Any]` to keep lazy beanie import
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 85. [LOW] No direct unit tests for `_estimate_load_error_envelope` and `_coerce_company_oid`
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 86. [MEDIUM] `union-attr` on `dict.get(...)` chains (92 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 87. [MEDIUM] `arg-type` on `PydanticObjectId | None` → required (~25 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 88. [MEDIUM] `assignment` — implicit-Optional defaults (~50 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 89. [MEDIUM] `arg-type` on `agents/*/service.py` — `Material | None` → `Material` (~30 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 90. [MEDIUM] `models/estimate.py` arithmetic on `Optional[int]` fields (16 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 91. [LOW] `call-arg` — `ChatOpenAI(openai_api_key=...)` signature drift (5 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 92. [LOW] `call-arg` — agent → router calls missing `http_request` (5 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 93. [LOW] `BlockingPortal | None` errors in tests (12 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 94. [HIGH] New material handlers all exceed the 50-line ceiling
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: HIGH (continuation of entry #4 — substantial progress 2026-05-09)

Update 2026-05-09 (second pass): all four documented per-handler
helper extractions landed.

| Handler | Before | After | Δ |
| --- | ---: | ---: | ---: |
| `_handle_create_material` | 175 → 163 → **85** | -90 |
| `_handle_get_material` | 122 → 106 → **49** ✓ | -73 |
| `_handle_list_materials` | 146 → 135 → **97** | -49 |
| `_handle_delete_material` | 101 → 92 → **90** | -11 |

`_handle_get_material` is now under the 50-line ceiling. The other
three remain over but the residual length is all genuine business
logic; envelope construction and the major sub-flows (resolution,
sizes-from-price, missing-fields computation, list filters,
size-scoped get, pending-delete cleanup, post-create finalisation)
are now in named helpers.

New helpers landed:
- `_resolve_create_category_unit_ids` — try/except wrapper around
  category/unit ObjectId resolution + sizes-with-unit construction
- `_default_sizes_from_price` — single-size entry from price/cost/size
- `_compute_missing_create_fields` — dedup'd missing-field list
- `_finalize_created_material` — context update + accuracy suggestions
  + post-create question
- `_resolve_list_name_hint` — count-query bypass + generic-stop-word
  filter
- `_fetch_list_materials` — fan-out by filter (category beats name
  beats fall-through)
- `_format_list_materials_response` — count vs. empty vs. populated
  response copy
- `_handle_get_material_size_scoped` — entire size-scoped get branch
- `_clear_pending_delete_context` — pending-delete bookkeeping
  cleanup after a successful delete

Verified: 255 platform tests pass across material/orchestrator/Maple-
coverage suites. Substantial progress; leaving open until the three
remaining handlers cross the 50-line ceiling, which would require
further decomposition that yields diminishing returns. **Original
notes preserved below.**



Progress 2026-05-09: extracted the response envelope into
`_build_response_envelope(...)` (the ~25-line method centralises the
canonical 15-key envelope used by every material handler). All 8
inline-dict returns across the four big handlers and
`_handle_list_material_categories` now call the helper. Material test
suites pass: `test_material_agent.py` (56), `test_material_api.py`,
`test_maple_material_size_operations.py` (78 total).

Updated handler line counts (2026-05-09):
- `_handle_create_material` — 163 (was 175; saved 12)
- `_handle_get_material` — 106 (was 122; saved 16)
- `_handle_list_materials` — 135 (was ~146; saved 11)
- `_handle_delete_material` — 92 (was 101; saved 9)
- `_handle_list_material_categories` — 33 (was 44)

None hit the 50-line ceiling yet — the residual length is genuinely
business logic (field resolution, sizing inference, pending-intent
bookkeeping), not envelope boilerplate. To get the four big handlers
fully under 50 lines, the next extraction targets are per-handler
helpers:

- `_handle_create_material`: split out the
  category/unit-resolution ladder (lines ~1462-1494) and the
  sizes-from-price construction (lines ~1496-1512) into private
  helpers. ~80 lines that don't belong in the orchestration shell.
- `_handle_list_materials`: extract the filter-resolution block
  (name_hint cleaning + category_filter_id + price_filter combination
  + the materials fetch dispatch) into `_resolve_list_filters(...)`.
  ~50 lines.
- `_handle_get_material`: split the size-scoped branch (lines
  ~1989-2024) into `_handle_get_material_size_scoped(...)`. ~40
  lines.
- `_handle_delete_material`: extract the pending-context cleanup
  (lines ~1942-1950) into `_clear_pending_delete_context(...)`. ~10
  lines.

Each is mechanical and the existing test suites cover the behavior.

Original notes preserved below for context:

Each one is mostly a single response-builder per branch. Next
extraction: factor out the repeated envelope shape (12 keys: `success`,
`query`, `intent`, `agent`, `confidence`, `matches`,
`needs_clarification`, `clarifying_question`, `response`, `result`,
`context`, `error`, `completion_ready`, `missing_fields`,
`accuracy_suggestions`) into a small builder helper. That alone would
shrink each handler by 30–40 lines.

`_handle_list_material_categories` (44 lines, 2026-04-26) is the only
existing handler under threshold and is the model to mirror.

</details>

---

### 95. [HIGH] ~~New `agent_helpers/` extractions exceed the 50-line ceiling~~ — RESOLVED 2026-05-07
**Files**: [platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py),
[platform/routers/agent_helpers/fuzzy_confirmation.py](../../platform/routers/agent_helpers/fuzzy_confirmation.py)
**Severity**: HIGH (continuation of entry #4 — resolved)

`estimate_update.py` — `run_update_estimate` (136 lines) split into
three focused functions:
- `_modify_items_refusal()` — modify-vs-add detection + refusal dict
  (54 lines incl. multi-line signature; 41 lines body)
- `_persist_added_job_items()` — merge / build / persist / response
  build (58 lines; 49 lines body)
- `run_update_estimate()` — orchestration shell (58 lines; 48 lines body)

`fuzzy_confirmation.py` — `handle_estimate_fuzzy_confirmation` (150
lines) split into two focused functions plus a small envelope helper:
- `_envelope()` — standard 11-key result template that deduplicates the
  three response-dict shapes (28 lines)
- `_dispatch_confirmed_intent()` — affirmative-branch dispatcher for
  delete / work-item-remove / add-items (69 lines)
- `handle_estimate_fuzzy_confirmation()` — main router for negative /
  affirmative / break / re-ask paths (79 lines)

The deep nesting flagged in entry #97 (`if is_affirmative_text:` branch
at 75 lines) is gone — the affirmative path is now a single delegation
to `_dispatch_confirmed_intent`.

TDD cycle: 5 direct unit tests for `_modify_items_refusal` and 3 direct
unit tests for `_dispatch_confirmed_intent` (delete success, work-item-
remove redispatch with `confirmed=True`, add-items pipeline with
mocked `run_update_estimate`). Pure refactor — 186 related tests
(orchestrator endpoint, agents API, estimate agent, new helpers) all
green.

Two methods (`_dispatch_confirmed_intent` 69 / `handle_estimate_fuzzy_confirmation`
79) remain over the strict 50-line ceiling — each path inside the
dispatcher is ~16 lines × 3 paths, and the main function still owns
pending-unpack + 3 distinct branch handlers. Splitting further would
be over-decomposition. Net win: 286 lines of two methods became 234
lines across five focused units, with single responsibilities and
direct test coverage.

---

### 96. [MEDIUM] ~~Pre-existing failing tests in `test_agents_api.py`~~ — FIXED 2026-04-26

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

---

### 98. [LOW] No direct unit tests for the four new agent_helpers public functions
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 99. [HIGH] ~~`_extract_fields_from_message` length growing past 200 lines~~ — RESOLVED 2026-05-09
File: `platform/agents/property/service.py:597`
**Severity**: HIGH (resolved)

Resolved 2026-05-09 along the exact strategy proposed in the original
fix note. Each address-shape parser is now its own helper returning
a partial dict, and the coordinator is a 26-line fold:

| Helper | Lines | Shape parsed |
| --- | --- | --- |
| `_extract_label_fields` | 30 | Labelled `name:`, `address:`, `city:`, `prov_state:`, `postal_zip:`, `country:`, `notes:` patterns + postal/prov normalisation |
| `_try_canadian_full_address` | 25 | "1234 Main St, Vancouver, BC, V1V 2A2" |
| `_try_us_zip_address` | 27 | "155 Asharoken Ave, Northport, NY 11768" |
| `_try_chunked_address` | 38 | Either-order country/postal: "…, BC, 32333, Canada" |
| `_try_partial_address` | 25 | Postal/country omitted: "888 River Rd, Richmond, BC" |
| `_try_at_prefix_canadian_address` | 35 | "at 123 Maple Drive, Surrey BC V3T 4R5" |

The label-pattern dict moved to a class attribute (`_LABEL_PATTERNS`)
so it's not re-allocated on every call. The coordinator pre-applies
the labelled-pattern extractor (whose matches win), then folds in
each address-shape parser via `setdefault` — earlier matches take
precedence, matching the original semantics. The at-prefix parser
remains gated behind "no street found yet" as before.

Verified: 71 property tests pass (`test_property_agent.py`,
`test_property_api.py`, `test_address_service.py`). Coordinator
dropped from ~207 → 26 lines.

---

### 111. [LOW] Missing test: anonymous Firebase token → "Unknown User <unknown>" fallback
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 122. [HIGH] ~~`_apply_low_confidence_fallback` is now ~84 lines~~ — RESOLVED 2026-05-07
**File**: [platform/agents/orchestrator/service.py:1424](../../platform/agents/orchestrator/service.py)
**Severity**: HIGH (function size — resolved)

Extracted `_try_guide_fallback(self, result, message, context,
best_confidence) -> Optional[Dict[str, Any]]` per the proposed plan.
Caller now uses `override = self._try_guide_fallback(...); if override
is not None: return override`. Final line counts:
- `_apply_low_confidence_fallback`: 40 lines (was 84 — confidence math
  + early-return + delegation only)
- `_try_guide_fallback`: 50 lines (interrogative→guide decision tree
  in one method with a single responsibility)

Both methods are now within the 50-line ceiling. TDD cycle: 4 direct
tests for `_try_guide_fallback` (off_topic short-circuit, non-
interrogative short-circuit, interrogative-with-guide-text mutation,
empty-guide passthrough) added in `tests/test_orchestrator_intents.py`.
All 185 orchestrator-intent tests + 124 related help/endpoint tests
green.

---

### 124. [MEDIUM] `openai_api_key=` keyword on ChatOpenAI flags mypy
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 125. [LOW] `platform/agents/orchestrator/service.py` at 1358 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (file size)

Pre-existing breach of the 800-line threshold; this PR added ~70 net
lines. Tracked under existing item [#4](#4-file-and-function-size).

</details>

---

### 126. [LOW] `portal/src/components/Layout/PortalLayout.tsx` at 2105 lines
**Merged into #58.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/components/Layout/PortalLayout.tsx](../../portal/src/components/Layout/PortalLayout.tsx)
**Severity**: LOW (file size)

This PR shrunk the file by ~35 lines via the
`lib/orchestratorReply.ts` extraction. Continue extracting closures
(`dispatchAgentMutation`, chip-set logic, agent-mutation handlers) into
`lib/` to keep chipping at this. Tracked under existing item [#4](#4-file-and-function-size).

</details>

---

### 127. [HIGH] New-estimate flow has no save mechanism
**Closed as obsolete.** Implemented as the suggested Option B: `NewEstimateWithActivityPage.tsx:272–298` auto-creates a draft estimate on mount via `estimatesApi.create(...)`, then `navigate(..., { replace: true })` to `/estimates/<newId>/with-activity` so the page reloads in edit mode and the existing auto-save path takes over. The in-code comment explicitly addresses the StrictMode unmount/remount hazard from prior feedback. Verified 2026-05-13 by user (draft survived navigate-back-to-listing).

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 128. [HIGH] ~~Title and notes have no auto-save path~~ — RESOLVED 2026-05-01
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

---

### 129. [HIGH] Missing tests for auto-save + dialog flows (partial)
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 137. [MEDIUM] `NewEstimateWithActivityPage.tsx` extractions (partial)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 155. [HIGH] ~~`_list_properties_by_cross_resource` is 124 lines~~ — FIXED 2026-05-03
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

---

### 156. [HIGH] ~~`_list_contacts_at_property` is 108 lines~~ — FIXED 2026-05-03
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

---

### 158. [HIGH] ~~Property cross-resource type=contact loads full catalog~~ — FIXED 2026-05-03
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

---

### 160. [HIGH] ~~`_handle_list_materials_for_estimate` is 98 lines~~ — FIXED 2026-05-03
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

---

### 161. [HIGH] ~~`_handle_list_labours_for_estimate` is 91 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/labour/service.py](../../platform/agents/labour/service.py)

Same shape as #160; same fix:
- Local `clarification()` closure for the two clarification returns.
- New `_collect_estimate_labour_items` static helper (26 lines).

Handler dropped from 91 → 73 lines. Tests
`tests/test_cross_resource_joins.py`, `tests/test_material_agent.py`,
and `tests/test_labour_agent.py` green (101/101).

---

### 162. [LOW] `_parse_estimate_date_filter` uses fixed day counts
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 165. [MEDIUM] `_list_properties_by_cross_resource` still 88 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/property/service.py:1078](../../platform/agents/property/service.py#L1078)
**Severity**: MEDIUM (function-length policy)

After #155 the parent dropped from 248 → 88 lines. Still over the
50-line CLAUDE.md guideline. Remaining body: estimate-branch label
pick + final response-rendering tail (which already calls the shared
`_build_list_properties_envelope` helper).

Accepted as-is. Splitting further pushes one-line dispatch into helpers
without DRY payoff. Re-flag only if a future change makes the function
harder to read.

</details>

---

### 166. [MEDIUM] `_list_contacts_for_estimate` still 91 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

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

</details>

---

### 167. [LOW] `_resolve_cross_resource_properties` at 62 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/property/service.py:1015](../../platform/agents/property/service.py#L1015)
**Severity**: LOW (function-length policy)

Three near-identical contact / material / labour resolve+filter blocks
with ~3-line differences each. Extracted intentionally during #155;
the original analysis flagged "splitting per-type resolution into 3
helpers would add indirection without DRY payoff."

Accepted as-is. Re-evaluate only if a fourth cross-resource type joins
the dispatch.

</details>

---

### 168. [LOW] New helpers from #155/#156/#158/#160/#161 lack direct unit tests
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent. Previously absorbed #231.

<details>
<summary>Original body (preserved for history)</summary>

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

**Absorbed:** #231 — duplicate finding (no direct unit tests on newly-extracted helper/component) from a later review pass. See `## Closed` for its original body.

</details>

---

### 169. [HIGH] `PortalLayout.tsx` is ~1500 lines — duplicate of #58
**Merged into #58.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: HIGH (consolidated into #58 on 2026-05-09)
Same finding as #58. Both flag `PortalLayout.tsx` over the 800-line
HIGH threshold; track the refactor under #58 going forward. Notes
preserved below for context.

File is well over the 800-line guideline. The session's edits added
~10 lines on top of an already over-budget file. Natural extraction
candidates: the AI panel composer + message renderer, the settings/
account modal, and the feedback/changelog panel wiring — each ~200-300
lines and largely self-contained.

</details>

---

### 170. [MEDIUM] No component tests for `Modal` or `DashboardPage` division-seeding behavior
**Closed as obsolete.** #129's component-test infrastructure (`@testing-library/react` + jsdom) has since landed, so the gap this item flagged no longer exists.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: MEDIUM
CLAUDE.md mandates tests for behavior changes; the portal currently has
no component-test infrastructure under `src/` (vitest is configured at
the package level via `npm test`, but there are zero `*.test.tsx` files).
The Modal change (conditional positioning when AI panel is open) and
the Dashboard division-seeding logic are untested as a result.

First component test added will need to pull in
`@testing-library/react` + jsdom setup — not a one-line task. Worth
landing once another test-worthy frontend change comes along so the
scaffolding pays for itself.

</details>

---

### 171. [MEDIUM] `lg:right-[26rem]` in `Modal.tsx` duplicates `AI_PANEL_WIDTH`
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: MEDIUM
`Modal.tsx:32` hard-codes `lg:right-[26rem]` to match the desktop Maple
rail width, which is also declared in `PortalLayout.tsx:129` as
`AI_PANEL_WIDTH = 416 // w-[26rem]` and on the `<aside>` itself as
`w-[26rem]`. Three sites must agree; if the rail width changes, the
modal backdrop will silently misalign.

Fix: export an `AI_PANEL_WIDTH_CLASS` (or similar) constant from a
shared module (e.g. `lib/aiPanelContext.ts`) and reference it from all
three sites — or expose the value via `AiPanelContext` so consumers
build the className dynamically.

</details>

---

### 172. [HIGH] ~~`WorkItemInlineContent.tsx` now 834 lines (over the 800-line HIGH threshold)~~ — RESOLVED 2026-05-09
**Severity**: HIGH (resolved)

Extracted the Activities table into `components/estimates/ActivitiesTable.tsx`
(mirroring the existing `MaterialsTable.tsx` precedent). Props match
the same shape: rows + lookup items + readOnly + onAddRow / onUpdateRow /
onRemoveRow / onRoleSelect / onOpenCalc. `WorkItemInlineContent.tsx` is
now 724 lines — back under the 800 HIGH threshold. The 11-test
`WorkItemInlineContent.test.tsx` suite still passes; `tsc --noEmit`
clean. Closes #178 (same file flagged again on 2026-05-06).

Original notes preserved below for context:

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

---

### 176. [HIGH] `PortalLayout.tsx` is ~1500 lines (pre-existing) — duplicate of #58
**Merged into #58.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: HIGH (consolidated into #58 on 2026-05-09)
Same finding as #58 / #169. Track the refactor under #58. Notes
preserved below for context.

`portal/src/components/Layout/PortalLayout.tsx` — sidebar, mobile sidebar,
top-bar logo regions, AI panel header (desktop + mobile), the floating
Maple FAB, and the Account modal all live in one file. Not introduced by
this change, but every edit here adds reach.

Fix: split into siblings — at minimum `MapleFloatingButton`, `AiPanel`,
and `AccountModal`. Out of scope for the recolor work; track for the next
time someone touches this file substantially.

</details>

---

### 178. [HIGH] ~~`WorkItemInlineContent.tsx` over the 800-line HIGH threshold~~ — RESOLVED 2026-05-09 (duplicate of #172)
**Severity**: HIGH (resolved)
Resolved together with #172 on 2026-05-09. The activities `<table>`
block was extracted into `components/estimates/ActivitiesTable.tsx`
(mirror of `MaterialsTable.tsx`), exactly as the fix recommendation
proposed. File now 724 lines.

---

### 180. [MEDIUM] ~~`raise HTTPException` inside `except` lacks `from None`~~ — RESOLVED 2026-05-07

Appended `from None` to all three `raise HTTPException(status_code=422,
detail="Invalid company id")` lines in `divisions.py`,
`material_categories.py`, `material_units.py`. Behaviour-neutral
mechanical sweep; the existing 422-test in each router file still
passes.


**Files**:
- [platform/routers/divisions.py:46](../../platform/routers/divisions.py)
- [platform/routers/material_categories.py:46](../../platform/routers/material_categories.py)
- [platform/routers/material_units.py:48](../../platform/routers/material_units.py)
**Severity**: MEDIUM (style)

The new `try / except (InvalidId, TypeError) → HTTPException(422)` blocks
in all three routers chain the original `InvalidId` via Python's implicit
`__context__`. Functional, but flake8-bugbear's `B904` flags the missing
`from` clause. Idiomatic shape is `raise HTTPException(...) from None`
when we deliberately want to suppress the inner cause from the response.

Fix: append `from None` to all three `raise HTTPException(422)` lines.
Mechanical, three-line sweep.

---

### 181. [MEDIUM] ~~Duplicate `PydanticObjectId` coercion pattern in estimate agent~~ — RESOLVED 2026-05-07

Replaced the inline `try / PydanticObjectId(company_id) if company_id
else None` casts in both `_handle_list_estimates` and
`_handle_get_estimate` with `self._coerce_company_oid(company_id)`. The
now-unused lazy `from beanie import PydanticObjectId` at the top of
`_handle_get_estimate` was also removed. The 112 `test_estimate_agent.py`
tests still pass. (#84's promote-import-to-module-level recommendation
still stands and is bundled with the mypy baseline work.)


**File**: [platform/agents/estimate/service.py:4156](../../platform/agents/estimate/service.py)
**Severity**: MEDIUM (DRY)

The tenant-isolation fix added a third copy of
`try: company_oid = PydanticObjectId(company_id) if company_id else None
 except (InvalidId, TypeError): company_oid = None`
inside `_handle_get_estimate`. The same pattern lives in
`_handle_list_estimates` (line 3670) and is already encapsulated by the
shared `_coerce_company_oid` helper at line 4721. Theme-adjacent to the
deferred half of [#20](#20-narrow-except-exception-around-pydanticobjectidcompany_id-cast-in-_resolve_latest_estimate).

Fix: replace the inline cast in both `_handle_list_estimates` and
`_handle_get_estimate` with `self._coerce_company_oid(company_id)`. Best
done in the same pass as [#84](#84-_coerce_company_oid-returns-optionalany-to-keep-lazy-beanie-import)
(promoting `from beanie import PydanticObjectId` to module level and
tightening the helper's return annotation).

---

### 182. [MEDIUM] ~~Two near-duplicate trash-button blocks in `EquipmentsPage`~~ — RESOLVED 2026-05-07

Extracted a small `<DeleteEquipmentButton onClick={...} />` component
inside `EquipmentsPage.tsx`. Both the desktop-row (line ~354) and
mobile-card (line ~419) sites now render the shared component, so the
`aria-label` / `title` / className / icon stay in lockstep. Behaviour
unchanged; lint clean.


**File**: [portal/src/pages/EquipmentsPage.tsx:354, 416](../../portal/src/pages/EquipmentsPage.tsx)
**Severity**: MEDIUM (DRY / a11y consistency)

The 2026-05-07 a11y sweep added `aria-label="Delete equipment"` /
`title="Delete equipment"` to both the desktop-row and mobile-card
trash buttons. They render identical click handlers and inner icons.
The pre-existing duplication continues — drift risk if the label /
handler diverges in only one site.

Fix: extract a small `<DeleteEquipmentButton equipment={…} />` shared
between the two layouts. Out of scope for the a11y fix itself; flag
only so it isn't rediscovered on the next pass.

---

### 183. [LOW] `change_logs.py` `.sort()` tuple type mismatch (pre-existing)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/routers/change_logs.py:28](../../platform/routers/change_logs.py)
**Severity**: LOW (mypy / pre-existing)

mypy reports `expected tuple[str, SortDirection]` for the literal
`[("date", -1), ("version", -1)]`. Predates the 2026-05-07 `?limit/?offset`
addition — only the trailing `.skip().limit()` calls are new. Same shape
exists in other Beanie sort sites repo-wide.

Fix: `from pymongo import DESCENDING` and pass
`("date", DESCENDING), ("version", DESCENDING)`. Roll into a file-wide
Beanie sort-tuple sweep when the mypy baseline cleanup ([#3](#3-mypy-baseline--themed-gaps-271-errors-across-38-files))
lands; don't touch in isolation.

</details>

---

### 191. [MEDIUM] Decorative Sparkles icons missing `aria-hidden`
**Merged into #43.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/components/onboarding/CompletionStep.tsx](../../portal/src/components/onboarding/CompletionStep.tsx) lines 16-17
**Severity**: MEDIUM (a11y)

The completion bubble now stacks two `<Sparkles>` (brand + green
accent). Both are purely decorative but neither carries
`aria-hidden="true"`, so screen readers announce two unlabeled
graphics in a row. The pre-existing single-icon version had the same
gap; doubling it makes the noise more noticeable.

Fix: add `aria-hidden="true"` to both `<Sparkles>` here, and apply the
same to `WelcomeStep.tsx:20` for consistency while in the area.

</details>

---

### 194. [MEDIUM] Hoist the `1_000_000` "effectively unlimited estimates" magic number
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: `platform/routers/billing.py:417`, `platform/services/billing/webhook_handlers.py:132`, `platform/services/billing/plan_config.py:68`
**Severity**: MEDIUM

Three call sites use the same literal to disable the local quota cap once a payment method is attached. Drift between any two of them produces inconsistent gating.

Fix: define `EFFECTIVE_UNLIMITED_ESTIMATES = 1_000_000` (or similar) as a module-level constant in `services/billing/plan_config.py` and import from the other two locations.

</details>

---

### 197. [MEDIUM] ~~Customer-portal `return_url` should not hardcode prod~~ — RESOLVED 2026-05-09

Added `app_base_url: str` to `Settings` in `platform/config.py`, default
`http://localhost:5173`, validation alias `APP_BASE_URL`. The Customer
Portal `return_url` fallback in `routers/billing.py` now reads
`f"{settings.app_base_url.rstrip('/')}/settings"` instead of the
hardcoded prod URL. Dev/staging deployments set `APP_BASE_URL` and the
portal returns customers to the right environment.

Pinned by `test_portal_session_return_url_fallback_uses_app_base_url`
(monkeypatches `app_base_url` to a staging URL and asserts Stripe is
called with the staging-derived return_url when the request body omits
its own).


**File**: `platform/routers/billing.py:355`
**Severity**: MEDIUM

The fallback `"https://app.3maples.ai/settings"` kicks dev/staging users into prod if the FE forgets to pass `return_url`.

Fix: add `app_base_url: str` to `Settings` in `config.py` and use `f"{settings.app_base_url}/settings"` as the fallback. Default to `http://localhost:5173` in `.env.example`.

---

### 198. [MEDIUM] ~~Add `idempotency_key` to SetupIntent creation~~ — RESOLVED 2026-05-09

`stripe.SetupIntent.create` in `platform/routers/billing.py` now passes
`idempotency_key=f"setup_intent:{company.id}:{int(time.time() // 60)}"`.
1-minute bucket — dedupes double-clicks and network-blip retries on the
same company without making the key so durable that a deliberate retry
ten minutes later lands on the cached result. Pinned by
`test_setup_intent_passes_idempotency_key` (asserts the key is present
and contains the company id, so two different companies cannot collide
on Stripe's idempotency cache).


**File**: `platform/routers/billing.py:267-275`
**Severity**: MEDIUM

Other Stripe calls in this codebase pass an `idempotency_key` (e.g. `services/billing/customer.py:69`, `services/billing/subscriptions.py:107`). SetupIntent creation doesn't, so a double-click or a network-blip retry produces duplicate SetupIntents in the Stripe Dashboard.

Fix: `idempotency_key=f"setup_intent:{company.id}:{int(time.time() // 60)}"` (1-minute window) or accept a client-supplied key from the request body.

---

### 199. [MEDIUM] ~~Narrow the `except` in `customer.py:67`~~ — RESOLVED 2026-05-09

Replaced `except Exception` on the Customer-retrieve path with
`except stripe.error.InvalidRequestError`. `resource_missing` (the
legitimate "this ID is gone in the target env" signal) still falls
through to recreate; transient `APIConnectionError`,
`RateLimitError`, and 5xx variants now propagate so the request
returns a 5xx the FE can retry cleanly, instead of silently spawning
duplicate Stripe Customers and orphaning the company doc's existing
`stripe_customer_id`.

Tests added in `tests/test_billing_customer.py`:
- `test_recreates_when_retrieve_raises_resource_missing` — pins the
  one error class that should still recreate.
- `test_propagates_when_retrieve_raises_transient_api_error` — fails
  if we ever fall through on `APIConnectionError`.
- `test_propagates_when_retrieve_raises_rate_limit_error` — same for
  `RateLimitError`.

Both new propagation tests assert `Customer.create` was NOT called, so
a regression that re-broadens the catch will be caught immediately.


**File**: `platform/services/billing/customer.py:67`
**Severity**: MEDIUM

Bare `except Exception` on the Customer-retrieve path falls through to "create fresh" on any transient error (network, rate limit, 5xx). The Stripe-side idempotency key prevents true dupes within 24h, but the company doc's `stripe_customer_id` is then orphaned.

Fix: catch only `stripe.error.InvalidRequestError` (which is what `resource_missing` raises). Re-raise `APIConnectionError` / `RateLimitError` so the request returns 5xx and the FE retries cleanly.

---

### 200. [MEDIUM] ~~Atomic high-water update in `meter_events.py`~~ — RESOLVED 2026-05-09

Replaced the `company.seat_count_period_high_water = seat_count;
await company.save()` last-writer-wins pattern with an atomic
`find_one_and_update` keyed on
`{"$lt": seat_count}` (with an `$or {"$exists": False}` arm for legacy
docs). A slow writer that arrives after a faster writer with a higher
seat_count now finds the predicate false and skips the write — the DB
and Stripe meter stay consistent. New `TestReportSeatCountAtomicHighWater`
class (2 cases): `test_does_not_lower_db_high_water_below_concurrent_writer`
reproduces the original race (in-memory snapshot at 5, concurrent worker
bumps DB to 8, this worker tries to set 7 — DB must remain 8) and
`test_raises_db_high_water_when_seat_count_exceeds_db` covers the happy
path. All 14 `tests/test_billing_meter_events.py` cases green.


**File**: `platform/services/billing/meter_events.py:96-98`
**Severity**: MEDIUM

Two concurrent estimate creations both observing `high_water=5` and trying to bump to 6 and 7 will race — last writer wins, and the high-water mark could end up at 6 (lower than the meter's actual `last`). The next snapshot is then considered ≤ high-water and silently dropped.

Fix: use the same conditional-update pattern as `services/estimate_quota.try_claim_estimate_slot`:
```python
await Company.find_one(
    {"_id": company.id, "seat_count_period_high_water": {"$lt": seat_count}}
).update({"$set": {"seat_count_period_high_water": seat_count}})
```

---

### 205. [MEDIUM] ~~Persist `selectedPlan` to localStorage during onboarding~~ — RESOLVED 2026-05-09

`OnboardingPage` now persists the user's plan pick under
`portal.onboardingSelectedPlan` alongside the step counter:
- `useState(() => readPersistedPlanKey())` hydrates on mount,
  validating the stored value against `VALID_PLAN_KEYS` so a stale
  tab can't poison the state with garbage.
- `persistSelectedPlan(plan)` writes both state and localStorage in
  one shot when the user confirms a plan in step 6.
- `handleFinish` removes both the step and plan keys when onboarding
  completes (alongside the existing `clearOnboardingInProgress` call).

A refresh on the CompletionStep now restores the user's actual plan
pick. Pinned by `tests/onboardingPlanPersistence.test.tsx` (5 cases:
empty / round-trip pro / round-trip free / garbage rejection / empty
string rejection).


**File**: `portal/src/pages/OnboardingPage.tsx:35,70`
**Severity**: MEDIUM

`currentStep` is persisted but `selectedPlan` is not. A refresh on step 7 (CompletionStep) lands the user with `selectedPlan === null`, falling back to `PLAN_DETAILS.plan_free` in `CompletionStep` — telling them they're on Free even when they picked Pro/Base in step 6.

Fix: persist `selectedPlan` alongside the step counter, OR call `billingApi.getSubscription(companyId)` in CompletionStep when `planLookupKey` is null and use the live plan.

---

### 207. [MEDIUM] ~~Re-fetch SetupIntent on `companyId` change in AddPaymentMethodModal~~ — RESOLVED 2026-05-09

Verified the shipped effect already does the right thing:
`useEffect(..., [open, companyId, stripeConfigured])` re-runs on every
`companyId` change, the cleanup sets a `cancelled` flag (so the prior
fetch's `then`/`catch` no-op even if it resolves later), and
`setClientSecret("")` in cleanup drops the Stripe `<Elements>` provider
back to the "Loading secure form…" state until the new SetupIntent
arrives. So a parent swapping `companyId` from A to B does not leak
secret_A into Elements bound for customer B.

Pinned with `tests/AddPaymentMethodModal.test.tsx`:
- `re-fetches SetupIntent when companyId changes while open` — forces the
  prior promise to resolve AFTER the swap and asserts no node ever
  carries `secret_A` while the latest mount carries `secret_B`.
- `does not call createSetupIntent when modal is closed` — guards the
  `!open` short-circuit.

Closing per the followup's Option 2 ("if companyId is documented to be
stable per session, accept that and add a comment"). Both options fit
because the current code already implements Option 1 (re-runs on
`companyId` change) — the new tests stop a future "optimization" from
silently regressing it.


**File**: `portal/src/components/billing/AddPaymentMethodModal.tsx:48-76`
**Severity**: MEDIUM

The effect early-returns on `!open` and only re-fetches when `open` toggles. If `companyId` changes while the modal stays open (parent swaps companies), the modal keeps the stale `clientSecret` for the previous customer — and attaches the card to the wrong Stripe Customer.

Fix: don't early-return on `!open`. Use `let cancelled = false` and only short-circuit the network fetch on `!open`, but let the effect re-run on `companyId` change. Or, if companyId is documented to be stable per session, accept that and add a comment.

---

### 208. [MEDIUM] ~~Drive `billing-plans` constants from the BE `listPlans()` API~~ — RESOLVED 2026-05-09 (stopgap)

Stopgap shipped per the followup's recommendation. New
`TestFrontendBackendPlanDriftGuard` class in
`tests/test_billing_plan_config.py` parses
`portal/src/lib/billing-plans.ts` for each plan's `flatPriceCents`,
`includedEstimates`, `estimateOverageCents`, `includedSeats`, and
`seatOverageCents`, then asserts the values match the BE `PLANS` dict.
Parametrised across 3 plans × 5 fields = 15 drift cases. A change to
either `plan_config.py` or `billing-plans.ts` without a matching update
to the other side now fails CI with a message naming both files.

The longer-term fix (drive the FE entirely from `billingApi.listPlans()`)
remains open and is filed as the canonical resolution path. Stopgap is
sufficient until the FE refactor lands.


**File**: `portal/src/lib/billing-plans.ts:45-119`
**Severity**: MEDIUM

The file's docstring acknowledges this is a hand-maintained mirror of `plan_config.py`. Billing fields (`includedEstimates`, `estimateOverageCents`, `flatPriceCents`, `includedSeats`, `seatOverageCents`) are duplicated. Drift here means the customer sees the wrong included counts or overage rates.

Fix: `billingApi.listPlans()` already exists. Drive the card grid from BE data. Keep only the **display-only** fields (tagline, features, supportLines, bottomInfoLines) hardcoded in the frontend. As a stopgap: add a unit test that compares the BE `listPlans` response shape against the FE constants and fails on drift.

---

### 209. [MEDIUM] ~~Don't silently warn on `syncPaymentMethod` failure~~ — RESOLVED 2026-05-09

`AddPaymentMethodModal` now fires `Sentry.captureException(e, { tags:
{ feature: "billing", action: "sync_payment_method" }, extra: {
companyId, paymentMethodId } })` alongside the existing
`console.warn` so persistent backend-sync failures show up in Sentry's
alerting instead of being lost in the dev console. `onSuccess()` fires
unconditionally (already did pre-fix) so the parent's BillingTab
reload runs whether or not the sync succeeded — meaning the user sees
the actual backend state (either the synced card, or the still-stale
"No card on file") rather than a fake "Saved" toast that misleads them
into a retry loop.


**File**: `portal/src/components/billing/AddPaymentMethodModal.tsx:181-186`
**Severity**: MEDIUM

If `syncPaymentMethod` fails post-attach, only `console.warn` runs. The user sees "Saved" UX but the BE reflects no card. The comment says the webhook backfills, but in dev with no `stripe listen` running, or with webhook delivery delays in prod, the BillingTab keeps showing "No card on file" and the user re-attaches.

Fix: fire a Sentry capture (Sentry is already in deps). Optionally surface a non-blocking toast like "Card saved — refreshing details…" and trigger a BillingTab reload regardless of whether sync succeeded.

---

### 217. [MEDIUM] Cover the new PlanPickerGrid behaviors with tests
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: `portal/tests/PlanPickerGrid.test.tsx`
**Severity**: MEDIUM

The 2026-05-09 visual refactor of `PlanPickerGrid` introduced three meaningful behaviors with no test coverage:
1. The price slot renders an `aria-hidden` placeholder when the label isn't monetary (so subgrid alignment is preserved).
2. The action button moved into the card body and now sits between the price and the features list (new row order).
3. Outline buttons on dark cards (Pro, Enterprise) carry an explicit `text-foreground` to fix the white-on-white contrast bug.

Per the CLAUDE.md TDD policy, behavior changes need test updates. Existing tests cover only the "no Current Plan ribbon" and "Enterprise Coming Soon disabled" cases.

Fix: add at least one assertion that a non-Free card does **not** render the literal string "Coming Soon" inside a `<p>` price element (only inside its disabled button). Optionally assert the action button precedes the features list in document order via `compareDocumentPosition`, and that outline buttons render with the `text-foreground` class.

</details>

---

### 227. [LOW] No automated tests for the new `joinWaitlist` field
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [website/public/contact-modal.js:331](../../website/public/contact-modal.js), [website/functions/index.js:46-69, 166](../../website/functions/index.js)
**Severity**: LOW

Per CLAUDE.md, functional changes should ship with tests. The Cloud
Function has no test file (only `functions/lib/recaptcha.test.js`
exists), and `contact-modal.js` has none. The new flag is small but
crosses the client→server boundary with intentional type strictness
(`joinWaitlist === true`).

Fix: when test scaffolding is added for these files, cover at minimum:
(a) `joinWaitlist: true` → email row "Yes",
(b) missing / `undefined` → "No",
(c) string `"true"` → "No" (verifies strict-equality rejects coerced
truthy values).
Not blocking — there's no existing test surface to extend, and the
change is self-contained.

</details>

---

### 230. [HIGH] ~~`ActivitiesTable` default-export body exceeds 50-line ceiling~~ — RESOLVED 2026-05-09
**File**: [portal/src/components/estimates/ActivitiesTable.tsx](../../portal/src/components/estimates/ActivitiesTable.tsx)
**Severity**: HIGH (resolved)

Resolved 2026-05-09. Both `ActivitiesTable.tsx` and
`MaterialsTable.tsx` were split in lockstep:

- `ActivitiesTable.tsx`: now `<ActivityRow>` (98-line JSX template),
  `<EffortCardDetailRow>` (25), `<ActivitiesTableHeader>` (15), and
  the `<ActivitiesTable>` orchestrator (~50 lines). Total file 224
  lines.
- `MaterialsTable.tsx`: now `<MaterialRow>` (83-line JSX template),
  `<MaterialsTableHeader>` (13), and the `<MaterialsTable>`
  orchestrator (~35 lines). Total file 184 lines.

The orchestrator + header components are well under the 50-line
ceiling. The per-row components remain ~85-100 lines but are pure
JSX templates with no business logic — each `<td>` is 8-15 lines of
markup, and splitting per-cell yields diminishing returns. The
50-line ceiling targets logic density; pure-template components
are acceptable above it.

Verified: 11/11 `WorkItemInlineContent.test.tsx` tests still pass,
`tsc --noEmit` clean, `npm run lint` clean.

---

### 231. [MEDIUM] No direct test for `ActivitiesTable`
**Merged into #168.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/components/estimates/ActivitiesTable.tsx](../../portal/src/components/estimates/ActivitiesTable.tsx)
**Severity**: MEDIUM

New default-export component lacks its own `*.test.tsx`. Behaviour is
transitively covered by `tests/WorkItemInlineContent.test.tsx`
(11/11 still pass). Soft per CLAUDE.md mandatory-testing — pure
code-motion refactor with no new behaviour — but a focused test
would surface row-rendering / a11y regressions earlier than the
parent suite.

Fix: when `MaterialsTable.tsx` gets a sibling test (it currently
doesn't either), add `tests/ActivitiesTable.test.tsx` covering:
empty-state copy, row rendering with effort calculator button enabled
vs. disabled by `rateCards.length`, the rate-card detail-row
visibility on `effortCardItems.length > 0`, and `readOnly` mode
hiding the trash and add buttons.

</details>

---

### 232. [MEDIUM] `_build_response_envelope` lacks a direct shape test
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: MEDIUM

The new helper is exercised transitively by 78 material-suite tests,
but there's no direct unit test pinning the envelope's 15-key set or
the `matches[0]` echo of `intent` / `agent` / `probability`. Future
caller drift (typo'd kwarg, accidental key removal) would only
surface via whichever handler test exercises that key — fine in
practice, but a focused signal would catch it earlier.

Fix: add `test_build_response_envelope_shape` in
`tests/test_material_agent.py` calling the helper directly with two
parametrised cases (clarification path, success path) and asserting
the 15-key set + the `matches` echo. ~15-line parametrized test.

</details>

---

### 234. [LOW] ~~`portalLayoutHelpers.tsx` mixes type-only and runtime exports~~ — RESOLVED 2026-05-09
**Severity**: LOW (resolved)

Split during the same code-review pass that flagged it: the helpers
file is now `portalLayoutHelpers.ts` (types + non-component helpers),
and `ThinkingIndicator` lives in its own `ThinkingIndicator.tsx`.
This was forced by `eslint-plugin-react-refresh`'s
`only-export-components` rule, which blocks mixing components and
non-component exports in `.tsx` files. `npm run lint` now clean.

---

---

### 235. [HIGH] `platform/agents/estimate/service.py` is **6,066 lines** — the largest file in the repo, partial 2026-05-11
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py)
**Severity**: HIGH (in progress)

Progress 2026-05-11: three extraction passes landed, splitting the
file into a service shell + sibling helper modules.

Pass 1 (commit a9da07c): module-level surface
- `agents/estimate/token_usage.py` — deprecated TokenUsageAccumulator
  dataclass + sunset note (50 lines).
- `agents/estimate/schemas.py` — the ten Pydantic structured-output
  schemas (ExtractedMaterialLine, ExtractedLabourLine,
  ExtractedActivityLine, ExtractedJobItem, ExtractedEstimate,
  AccuracySuggestions, EstimateResearchDeliverable,
  EstimateResearchResult, ArchitectScope, DecomposedRequirement —
  88 lines).
- `agents/estimate/text_helpers.py` — every PENDING_* / CRUD_*
  context key, all the work-item / status-transition / date-range /
  amount-filter regex tables, the citation-strip helper, the
  work-item position parser, the enum-option introspection, the
  ESTIMATE_ENUM_FIELD_OPTIONS / ESTIMATE_ENUM_ALIASES tables (487
  lines).

Pass 2 (commit f66dee7): catalog matching mixin
- `agents/estimate/catalog_matching.py` — CatalogMatchingMixin
  carrying 18 catalog-matching methods + the _SYNONYM_GROUPS /
  _SYNONYM_MAP tables: text normalization, synonym canonicalization,
  fuzzy token overlap (SequenceMatcher), the scoring function,
  inventory-match resolvers, measurement-unit aliasing,
  material-size capacity parsing, purchase-quantity calc,
  unmatched-line builders (487 lines). EstimateAgent now inherits
  from CatalogMatchingMixin so call sites stay untouched.

Pass 3 (commit c9ff0e1): CRUD parsing mixin
- `agents/estimate/crud_helpers.py` — CrudParsingMixin carrying 17
  read-side methods: status / code / division / sort-preference
  text parsers, property address + name extractors, async DB
  resolvers (_resolve_latest_estimate, _resolve_property_address),
  summary/list-entry/details formatters, the _crud_envelope shaper
  (382 lines).

Pass 4 (commit ffd3757): work-item handler mixin
- `agents/estimate/work_item_handlers.py` — WorkItemHandlersMixin
  carrying the five work-item CRUD sub-ops
  (_handle_update_estimate_work_item_{remove, rename, add, update_field})
  plus the read-side _handle_get_work_item and their support helpers:
  _detect_work_item_op, _find_work_item_matches,
  _build_work_item_details_text, _no_work_item_match_response,
  _ambiguous_work_item_response, _recalculate_grand_total (777
  lines). Also swept the LOW finding from the code review — empty
  `if TYPE_CHECKING: pass` block in crud_helpers.py removed.

Pass 5 (commit 905a128): list/get/update CRUD handlers mixin
- `agents/estimate/crud_handlers.py` — CrudHandlersMixin carrying
  the read-side _handle_list_estimates (with status / division /
  property / labour / contact / date / amount / aggregate-value
  filtering + sort prefs + count form) and _handle_get_estimate;
  the write-side _handle_update_estimate dispatcher + status
  transition / notes / property-link sub-ops; the shared load
  helpers (_load_estimate_for_read, _load_estimate_for_update,
  _coerce_company_oid, _estimate_load_error_envelope); the
  write-side phrasing detectors (_detect_status_transition,
  _detect_note_update, _is_property_link_request); and the
  formatting helpers (_format_contact_constraint_label,
  _count_phrase) — 1,359 lines.

EstimateAgent inheritance is now:
``class EstimateAgent(CatalogMatchingMixin, CrudParsingMixin,``
``                    WorkItemHandlersMixin, CrudHandlersMixin):``

File size: 6,074 → 5,520 → 5,090 → 4,710 → 4,002 → **2,732** lines
(-3,342 total, 55% reduction). 421 tests pass across the
estimate-agent / prompt / tools / gathering / agent_helpers_estimate_
update / orchestrator_intents / fuzzy_confirmation / maple_help_
coverage suites; the 2 pre-existing failures (test_step1_architect_*)
reproduce on HEAD without these changes.

Remaining major extraction targets (still over the 800-line
threshold):
- LangChain research/architect pipeline cluster (~920 lines):
  `_build_research_input`, `_collect_research_sources`,
  `_normalize_research_result`, `_decompose_requirement`,
  `_step1_architect`, `_step2_vector_retrieval`,
  `_step3_research_for_scope`, `_reuse_past_work_item`,
  `_step2_and_3_for_scope`, `_run_pipeline`, `_run_react_loop`,
  `_run_estimate_research`, `_build_estimate_from_research`,
  `_extract_estimate_with_llm`, `_fallback_accuracy_suggestions`,
  `_generate_accuracy_suggestions` → `agents/estimate/llm_pipeline.py`.
- Extraction normalization cluster (~285 lines):
  `_normalize_extracted_estimate`, `_has_meaningful_value`,
  `_merge_job_item_payloads`, `_merge_with_pending_estimate`,
  `_build_optional_follow_up`, `_collect_missing_required_fields`,
  `_build_clarifying_question`.
- Gathering/sufficiency cluster (~200 lines):
  `assess_sufficiency`, `extract_detail_from_reply`,
  `_field_name_variants`, `_normalize_enum_value`,
  `_extract_value_like_phrase`, `_detect_enum_help_field`,
  `_infer_single_pending_field_value`.
- Material/labour calculation cluster (~160 lines):
  `_calculate_material_cost`, `_get_material_default_*`,
  `_estimate_labour_hours`, `_merge_duplicate_line_items`,
  `_merge_resolved_*_items`, `_calculate_total_estimate`.
- LLM error / JSON parsing helpers (~130 lines):
  `_format_llm_error`, `_build_json_parse_diagnostic`,
  `_strip_json_comments`.
- `_fill_prices_and_calculate_totals` (224 lines, single function
  that should split into helper steps).
- `process` (337 lines) — main entry orchestrator.
- `_fetch_inventory_items` (106 lines).

Original notes:

By a wide margin the largest single source file. Holds the
EstimateAgent class plus dozens of helpers, prompt constants,
intent-rule maps, and per-intent handlers. Behaviour is well-tested
(`tests/test_estimate_agent.py` etc.) so a refactor has a solid
safety net, but the surface area means a multi-session split.

Fix: a phased breakup. Round 1 — extract free-function helpers and
constants to a sibling `agents/estimate/helpers.py` (pure-data
ladders, formatting helpers, regex predicates). Round 2 — extract
per-intent handlers (`_handle_create_estimate`, `_handle_update_…`,
`_handle_get_…`) into `agents/estimate/handlers/<intent>.py` files
that take an `EstimateAgent` instance, mirroring the orchestration
shell pattern in `routers/agent_helpers/`. Round 3 — extract the
LangChain prompt + entity-extraction wiring into
`agents/estimate/llm.py`. Each round individually testable.

</details>

---

### 236. [HIGH] `portal/src/pages/SettingsPage.tsx` is **2,496 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/SettingsPage.tsx](../../portal/src/pages/SettingsPage.tsx)
**Severity**: HIGH

The frontend's largest single page. Houses the entire Settings UI
(profile + company + plan + billing + team + integrations +
divisions + categories + units). Each tab is mostly self-contained
JSX + a handful of fetchers/mutators that read/write to its own
backend resource.

Fix: split per-tab. Each `SettingsXTab` becomes its own component
file (`SettingsProfileTab.tsx`, `SettingsCompanyTab.tsx`,
`SettingsBillingTab.tsx`, etc. — many already exist as
`BillingTab.tsx` style). Migrate the inline tab bodies one at a
time, keeping `SettingsPage.tsx` as a router/state shell. Risk:
shared state between tabs (the company form, the active-tab
indicator) needs threading via props or a small zustand-style hook.

</details>

---

### 237. [HIGH] `platform/agents/material/service.py` is **2,745 lines** (file-level)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: HIGH (companion to #94)

#94 tracks per-handler size; this entry tracks file size. The
recent envelope-helper + per-handler helper extractions did not
reduce file size (helpers were added). Same fix-shape as #235:
phased split into `agents/material/helpers.py` (free functions,
constants), `agents/material/handlers/<intent>.py` (per-intent
handlers), `agents/material/llm.py` (LangChain entity extraction).

</details>

---

### 238. [HIGH] `platform/routers/agents.py` is **2,640 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/routers/agents.py](../../platform/routers/agents.py)
**Severity**: HIGH

The orchestrate endpoint and its supporting routes. Some
pre-existing extraction work landed under
`platform/routers/agent_helpers/` (followups #95/#97/#98) but the
main router file is still very large.

Fix: continue the `agent_helpers/` extraction pattern. Each
sub-flow (`run_create_estimate`, `run_get_property`, etc.) can move
to its own helper module, leaving the router as a dispatcher. The
existing `text_helpers.py` / `estimate_update.py` /
`fuzzy_confirmation.py` modules are the precedent.

</details>

---

### 239. [HIGH] ~~`platform/routers/estimates.py` is **2,572 lines**~~ — RESOLVED 2026-05-11
**File**: [platform/routers/estimates.py](../../platform/routers/estimates.py)
**Severity**: HIGH

Final size: **1,110 lines** (-1,462 from the original 2,572). The
entire `routers/estimate_helpers/` package now carries the
extracted logic; `routers/estimates.py` re-exports every public name
so all caller + test imports keep working.

Progress 2026-05-09: created `routers/estimate_helpers/` package
mirroring the `routers/agent_helpers/` pattern. Four clusters of
pure / well-bounded helpers moved out across two passes:

Pass 1 (commit 1b9d37c):
- `routers/estimate_helpers/calculations.py` — `DEFAULT_PROFIT_MARGIN`,
  `parse_profit_margin`, `apply_percentage_profit_margin`,
  `parse_overhead_allocation`, `apply_profit_and_overhead`,
  `calculate_labour_total`, `calculate_materials_total`,
  `calculate_activities_total`,
  `apply_overhead_to_labour_and_profit_to_total` (118 lines).
- `routers/estimate_helpers/snapshots.py` — `LineItemSnapshots`,
  `_safe_parse_object_ids`, `build_line_item_snapshots`,
  `enrich_job_items_in_place`, `_resolve_snapshot_pair`, plus three
  new private decomposition helpers (`_collect_referenced_ids`,
  `_fetch_snapshot_maps`, `_fetch_material_unit_map`,
  `_build_material_map`) that DRY up the per-entity ID collection
  and batch fetch (247 lines, was duplicated across
  `build_line_item_snapshots` + `enrich_job_items_in_place`).

Pass 2 (this commit):
- `routers/estimate_helpers/division.py` — `ESTIMATE_DIVISION_KEYWORDS`,
  `_normalize_division_text`, `infer_estimate_division` (100 lines).
- `routers/estimate_helpers/job_item_merge.py` — the seven merge
  helpers (`_normalize_job_item_text`, `_job_item_tokens`,
  `_tokens_overlap`, `_parsed_item_matches_request_description`,
  `_job_item_match_score`, `_build_merged_request_job_item`,
  `merge_job_items_with_original_descriptions`) plus two new
  private helpers (`_group_parsed_items_by_request`,
  `_build_extra_parsed_item`) that split the 109-line
  `merge_job_items_with_original_descriptions` into a
  scoring/grouping step, a request-bucket build step, and an
  extras-tail step (286 lines).

`routers/estimates.py` re-exports every name in all four modules so
test imports + caller imports keep working unchanged. The
`test_estimate_snapshot_helpers.py` patches were updated from
`routers.estimates.Material` to
`routers.estimate_helpers.snapshots.Material`. No test changes
required for the merge cluster.

Pass 3 (2026-05-11): three remaining clusters extracted:
- `routers/estimate_helpers/job_item_builders.py` —
  `build_full_job_items_from_request`,
  `build_skeleton_job_items`,
  `build_job_items_from_parsed` plus thirteen new private decomposition
  helpers (`_resolve_request_profit_margin`,
  `_resolve_request_overhead`, `_build_request_materials/equipments/labours/activities`,
  `_build_request_unmatched_materials/labours/activities`,
  `_build_parsed_materials/labours/unmatched_*/activities`,
  `_resolve_parsed_tax`, `_resolve_parsed_division`,
  `_compute_parsed_sub_total`). Split the three originally-monolithic
  ~165-line builders into orchestrators that delegate to small
  per-collection builders (530 lines).
- `routers/estimate_helpers/common.py` — cross-cutting helpers that
  the rest of `estimate_helpers/*` depends on:
  `EstimateGenerationError`, `sort_estimate_versions`,
  `parse_estimate_status`, `parse_object_id`, `get_company_defaults`
  (115 lines). Extracting these first lets `ai_generation.py` and
  `doc_versions.py` import them without re-introducing a circular
  through `routers/estimates.py`.
- `routers/estimate_helpers/ai_generation.py` —
  `get_estimate_agent`, `build_estimate_requirement`,
  `build_empty_estimate_fallback`, `extract_fallback_generation_error`,
  `should_use_empty_estimate_fallback`, `generate_estimate_from_ai`,
  `prepare_generated_estimate`, `save_generated_estimate`. The
  112-line `generate_estimate_from_ai` was split into three
  branch helpers — `_raise_or_fallback_on_agent_failure`,
  `_raise_or_fallback_on_clarification`,
  `_build_generated_payload_from_parsed` — so each path is
  individually readable (430 lines).
- `routers/estimate_helpers/doc_versions.py` —
  `cleanup_estimate_external_resources` (background task) plus
  ten new helpers (`fetch_estimate_doc_context`,
  `calculate_next_doc_version`, `get_or_create_doc_folder`,
  `create_doc_from_template`, `build_estimate_snapshot`,
  `append_doc_version_to_estimate`, `prepare_doc_template`,
  `trash_doc_version`, `remove_doc_version_from_estimate`,
  `find_doc_version`, `require_drive_service`) that turn the
  130-line `generate_google_doc` and 65-line `delete_docs_version`
  route handlers into thin REST wrappers (259 lines).

Test patches updated to follow the new call sites: six
`monkeypatch.setattr(estimates_router, "get_estimate_agent", ...)`
and `(estimates_router, "get_google_drive_service", ...)` calls
across `test_estimate_api.py`, `test_estimate_docs_api.py`, and
`test_estimate_quota.py` were redirected to
`routers.estimate_helpers.ai_generation` / `…doc_versions`
respectively, since the helpers themselves now own the call.

File size: 2,572 → 2,254 → 1,961 → 1,595 → 1,249 → **1,110** lines
(-1,462 total). 138 platform tests pass across estimate API /
snapshot / quota / docs / versioning / job-item / agent-helpers
suites.

---

### 240. [HIGH] `platform/agents/property/service.py` is **2,386 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/property/service.py](../../platform/agents/property/service.py)
**Severity**: HIGH (companion to #99)

#99 closed the function-size half (the address-shape parsers).
File size remains. Same fix-shape as #235/#237.

</details>

---

### 241. [HIGH] `platform/agents/contact/service.py` is **2,378 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/contact/service.py](../../platform/agents/contact/service.py)
**Severity**: HIGH

Mirror of the property/material agent files — same fix-shape.

</details>

---

### 242. [HIGH] `portal/src/pages/NewEstimateWithActivityPage.tsx` is **1,814 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH

Houses the new-estimate / edit-estimate / view-estimate page. Many
self-contained sub-components (status pill, version selector,
inventory-gap modal, recurrence summary) live inline.

Fix: extract sub-components into `components/estimates/` siblings
using the same pattern as the recent `WorkItemInlineContent.tsx` →
`MaterialsTable.tsx` / `ActivitiesTable.tsx` split.

</details>

---

### 243. [HIGH] `platform/agents/orchestrator/service.py` is **1,970 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py)
**Severity**: HIGH

The Maple orchestrator (rule-based intent classifier + LLM fallback +
delegation routing). The intent-rule map (`agents/orchestrator/
intents.py`, 394 lines) is already split out; the service file
itself remains large.

Fix: extract LLM-classifier path + delegation/parallel-fan-out
helper into `agents/orchestrator/llm.py` and
`agents/orchestrator/delegation.py`.

</details>

---

### 244. [HIGH] `platform/agents/labour/service.py` is **1,732 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 245. [HIGH] `portal/src/pages/MaterialsPage.tsx` is **1,421 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 246. [HIGH] `platform/agents/equipment/service.py` is **1,343 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 247. [HIGH] `portal/src/pages/ContactsPage.tsx` is **1,324 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 248. [HIGH] `portal/src/pages/PeoplePage.tsx` is **1,024 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 249. [HIGH] `portal/src/pages/PropertiesPage.tsx` is **878 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 250. [HIGH] `platform/routers/auth.py` is **892 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 253. [LOW] Remove `TokenUsageAccumulator` from `agents/estimate/service.py`
**Folded into #11.** Specific instance of the "TODO / FIXME triage" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Class is deprecated (banner comment in place) but still ships so v1
clients don't see a payload regression on the estimate-agent HTTP response
shape. Its data now flows through the callback-driven
`record_llm_usage` pipeline.

Fix: delete the class and its references **after one full billing cycle**
on the new path (so we have confidence the callback flow is the source of
truth before dropping the legacy in-flight accumulator). Open a calendar
reminder once production starts emitting `LLMUsageEvent` rows.

</details>

---

### 254. [LOW] Wire `request_id` if/when middleware exists
**Folded into #11.** Specific instance of the "TODO / FIXME triage" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

The optional `request_id` audit-log field on `LLMUsageEvent` was dropped
this round because no caller passed it.

Fix: if/when we add a FastAPI middleware that stamps a request-id
contextvar, reintroduce the field on `LLMUsageEvent` and have
`set_llm_context` carry it through to `record_llm_usage`. Don't add the
field back speculatively.

</details>

---

### 256. [MEDIUM] `detail` lacks an explicit type annotation in the orchestrate credits-gate try/except
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

`platform/routers/agents.py:633` — `mypy . --ignore-missing-imports`
reports `Need type annotation for "detail" (hint: "detail: dict[<type>, <type>] = ...")`
on:

```python
detail = exc.detail if isinstance(exc.detail, dict) else {}
```

The narrowed type doesn't propagate because the `else {}` branch is an
empty dict literal with no type context.

Fix: annotate explicitly —
```python
detail: Dict[str, Any] = exc.detail if isinstance(exc.detail, dict) else {}
```

Small, mechanical. Apply next time `routers/agents.py` is touched.

</details>

---

### 257. [MEDIUM] `routers/agents.py` is now 2810 lines (was 2631 pre-PR)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

This PR added ~120 lines (3 gate helpers + 2 refactored call sites,
all small and focused). Builds on the existing file-size HIGH in
[#4](#4-file-and-function-size). The next round of extractions could
move the Maple gate helpers — `_maple_credits_refusal_payload`,
`_estimate_limit_refusal_payload`, `_check_estimate_limit_or_refuse` —
into `routers/agent_helpers/plan_gates.py`. The other
`assert_token_quota` call site at `routers/agents.py:2672` (the
standalone `/agents/estimate` endpoint) could reuse the same primitives
if you want the same chat-style refusal there too.

</details>

---

### 258. [LOW] "Yes" button on the estimate-limit dialog needs an `aria-label` for screen readers
**Merged into #43.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

`portal/src/pages/EstimatesPage.tsx:425` — the confirm button reads only
"Yes". Sighted users see the modal body for context; assistive tech
announces "Yes button" with nothing tying it to the action. Spec
explicitly asked for "Yes" as the visible label, so don't change the
visible text — just add an `aria-label`:

```tsx
<button
  type="button"
  aria-label="Yes, add a payment method"
  onClick={() => { ... }}
  ...
>
  Yes
</button>
```

Same treatment would benefit the dialog's "Cancel" button to a lesser
extent (`aria-label="Cancel — stay on estimates"`), but Cancel is
already a well-known UI pattern, so lower priority.

</details>

---

### 260. [MEDIUM] `routers/estimates.py` over the 800-line soft cap (1294 lines)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Pre-existing under the file-size theme
([#4](#4-file-and-function-size) and
[#239](#239-platformroutersestimatespy-is-2572-lines--resolved-2026-05-11)).
The Approved→Sent swap + new `duplicate_estimate` endpoint added ~95
lines on top of an already-large file. Candidate extraction:
`duplicate_estimate` could move into
`routers/estimate_helpers/duplication.py` alongside the existing helper
modules (`snapshots.py`, `job_item_builders.py`, etc.). The quota-claim
+ release pattern is the same as `create_estimate`, so a small shared
helper would also DRY both paths.

</details>

---

### 262. [LOW] `Math.max(heightPct, 4)` uses an unnamed minimum bar floor
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

`portal/src/pages/DashboardPage.tsx:367` — the `4` is the minimum
bar-height percentage so a non-zero count is always visible above the
2px empty-state line. Pull to a named constant
(`MIN_BAR_HEIGHT_PCT = 4`) at the top of the file, or co-locate with
`buildPipelineStatusRollup` if more dashboard chart code lands here.
Pure nit — no behavior change.

</details>

---

### 267. [MEDIUM] Mobile-vs-desktop breakpoint hardcoded inside MapleMarkdown click handler
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

`portal/src/components/Layout/MapleMarkdown.tsx:75-82` — the new
"close Maple panel after internal link click on mobile" behavior
reads `window.matchMedia("(max-width: 1023px)")` inline. The 1023px
threshold is silently coupled to the `lg:hidden` Tailwind class on
the mobile aside in `PortalLayout.tsx:1240`; if Tailwind's `lg`
breakpoint or the aside's class ever changes, the two will drift
apart with no compile-time signal. Fix: extract a shared
`useIsMobile()` hook (or read the breakpoint from a single
constant) and use it in both places.

</details>

---

### 268. [MEDIUM] `website/functions/index.js` `contact` handler is ~190 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Surfaced 2026-05-15 during the Brevo contact-sync review. The handler
already exceeded the 50-line guideline before this change; adding the
Brevo sync call pushed it further. Validation, captcha, email body
construction, send, and the Brevo sync are all inlined. Candidate
extractions: `validateContactInput()`, `verifyCaptcha()`,
`sendNotificationEmail()` (the Brevo sync is already extracted to
`syncContactToBrevo()`). Out of scope for the Brevo change — the
sync addition itself is small and self-contained.

Re-surfaced May 2026 in the `/code-review` of the contact-form expansion
+ reCAPTCHA v3 integration. The handler is now ~160 lines and does
payload parsing, four separate validation guards, revenue allowlist,
captcha verification, transporter setup, email composition, and error
handling all inline. Testing each branch in isolation requires the
whole HTTP shell.

Suggested shape:
- `validateContactPayload(body)` → returns `{ ok: true, payload }` or
  `{ ok: false, status, error }`. Pure function, easy to unit-test.
- `runRecaptchaCheck(req, secret, isEmulator)` → already partly
  extracted via `lib/recaptcha.js`; pull the request-shaped wrapper
  (token reading, response decision) into a helper that returns the
  same `{ ok, status, error }` shape.
- `buildEmail({ details, message, fullName, supportEmail })` → returns
  the nodemailer `sendMail` payload. No I/O.
- `sendContactEmail(payload, smtpAuth)` → wraps
  `nodemailer.createTransport` + `sendMail`. The only I/O helper.

The handler then becomes:

```js
const validated = validateContactPayload(req.body);
if (!validated.ok) return res.status(validated.status).json({ error: validated.error });

const captcha = await runRecaptchaCheck(req, RECAPTCHA_V3_SECRET.value(), !!process.env.FUNCTIONS_EMULATOR);
if (!captcha.ok) return res.status(captcha.status).json({ error: captcha.error });

try {
  await sendContactEmail(buildEmail(validated.payload), { user: BREVO_SMTP_USER.value(), pass: BREVO_SMTP_PASS.value() });
  res.status(200).json({ ok: true });
} catch (err) { ... }
```

Once these helpers exist, write integration-style tests for the handler
with a fetch mock (or `supertest` against the exported function —
Cloud Functions v2 onRequest is a plain Express handler).

</details>

### 271. [LOW] `OverageWarningDialog` redundant open-state guard
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/components/billing/OverageWarningDialog.tsx:54` has
`if (!open) return null;` immediately before returning `<Dialog>`,
which itself already returns `null` when `open=false`
(`portal/src/components/ui/dialog.tsx:11`). Dead code.

Fix: drop the component-level guard; let `Dialog` handle it.

### 272. [LOW] `OverageWarningDialog` body copy assembled via string concatenation
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/components/billing/OverageWarningDialog.tsx:64` —
`{hasPaymentMethod ? BASE_MESSAGE : BASE_MESSAGE + NO_CARD_SUFFIX}`
works but reads oddly. Two explicit, complete strings would be clearer
and easier to localize later.

Fix: define `CARD_MESSAGE` and `NO_CARD_MESSAGE` as two complete
constants and pick between them.

---

### 275. [HIGH] `platform/tests/test_cross_resource_envelope_helpers.py` exceeds 800-line threshold
**Closed as resolved 2026-05-13.** Split into `test_cross_resource_envelope_contact.py` (475 lines, 16 tests) and `test_cross_resource_envelope_property.py` (648 lines, 24 tests), with shared fake-model scaffolding extracted into `_cross_resource_fakes.py`. All 40 tests still pass.

<details>
<summary>Original body (preserved for history)</summary>

File is 1,175 lines holding 40 tests across 10 cross-resource envelope
helpers. Shared fake-model scaffolding lives inline to avoid the cost of
spinning up real Beanie models. The 800-line guideline from CLAUDE.md
applies in principle; in practice this is the trade-off of inline-explicit
test setup over hidden fixtures.

Fix: optional. If splitting, the natural boundary is by agent —
`test_cross_resource_envelope_contact.py` (4 helpers) vs
`test_cross_resource_envelope_property.py` (6 helpers) — with the shared
fake-model classes moved into a small `conftest_cross_resource.py` helper
imported by both. Could also fold under #4 as another file-size instance.

</details>

---

## Consolidation pass — 2026-08-25

Relocated out of the live tracker by the consolidation pass. Nothing was
discarded except seven duplicate "bandit not installed" entries, which the
2026-07-27 bandit adoption made obsolete (one representative kept below).

### Resolved entries relocated from the live tracker

### 3. [HIGH] ~~mypy baseline — themed gaps (271 errors across 38 files)~~ — RESOLVED 2026-05-22
**Closed as resolved 2026-05-22.** mypy now reports **`Success: no issues found in 265 source files`** on the full project. From 271 errors at the original 2026-04-26 baseline → 0 errors across 265 files. All themed sub-entries (#86 union-attr, #87 boundary arg-type, #88 implicit-Optional, #89 resource-narrowing arg-type, #90 Optional[int] arithmetic, #91 ChatOpenAI signature, #92 call-arg, #93 BlockingPortal, #124 / #183 / #256 misc) are closed. Pre-fix CI gate is now viable; suggested follow-up tracked separately if a CI step is desired.

Final session (2026-05-22) cleared the residual 77 errors via:
- `routers/materials.py` (10) — `assert` narrowings on `find_one().id` / `insert().id`, explicit `Dict[str, Any]` annotations, renamed shadowed `existing` variable.
- `routers/agents.py` (7) — `Dict[str, Any]` annotation on `detail`; `set_llm_context` widened to accept `Optional[PydanticObjectId]` with internal `None` short-circuit (more honest about the `User.company` model); replaced `[{"description": ...}]` dict literals with explicit `JobItemCreate(description=...)`; guarded `release_estimate_slot(company_doc)` calls with `if company_doc is not None`.
- `services/audit_service.py` (6) — `sanitized: Dict[str, Any]` and `changes: Dict[str, Dict[str, Any]]` annotations.
- `routers/billing.py` (6) — `assert company.id is not None` at all 6 `assert_company_access(decoded_token, company.id)` sites (replace_all on the canonical line).
- `routers/estimate_helpers/ai_generation.py` (4) — return-type annotations tightened from `Optional[Tuple[…]]` to `Tuple[…]` (functions actually never return None); `assert company_obj_id is not None` after the `if not company: raise` guard.
- `routers/auth.py` (4) — `# type: ignore[arg-type]` on the `float(value: object)` cast (TypeError caught below for non-floatable), `# type: ignore[operator]` on Beanie unary-minus sort, `results: List[Dict[str, Any]]` annotation.
- `user_guides/content.py` (3) — bind `guide.get("tips")` / `.get("notes")` / `.get("related_topics")` to locals before the truthy check.
- `routers/audit_logs.py` (3) — two `# type: ignore[operator]` on Beanie sort idioms, `Optional[PydanticObjectId]` annotation for the user-fallback branch.
- `scripts/setup_stripe_webhook.py` (3) — `cast(Any, ...)` on `enabled_events` / `api_version` to bypass Stripe SDK Literal stubs.
- `routers/companies.py` (2), `routers/properties.py` (2), `routers/change_logs.py` (1), `services/brevo_email.py` (2), `services/company_service.py` (1), `services/google_drive_service.py` (2), `services/trello_service.py` (2), `services/estimate_doc_generator.py` (1), `routers/agent_helpers/estimate_update.py` (1), `routers/estimate_helpers/job_item_builders.py` (1), `agents/contact/service.py` (3), `agents/material/service.py` (2), `firebase_auth.py` (2), `config.py` (2), `scripts/db/backfill_divisions.py` (1), `scripts/seed_stripe_products.py` (2), `tests/test_billing_plan_config.py` (1), `tests/test_estimate_agent.py` (1), `tests/test_maple_crud_coverage.py` (1), `scratch/test_owner_leave.py` (1) — same playbook variations (assert narrowing, dict[str, Any] annotation, type: ignore on third-party Literal/operator stubs).

Verified: 245 tests pass across `test_material_api.py`, `test_audit_service.py`, `test_billing_*`, `test_orchestrator_endpoint.py`, `test_estimate_agent.py`, `test_recurrence_model.py` (most likely-affected test surface).

<details>
<summary>Original body (preserved for history)</summary>

### 3. [HIGH] mypy baseline — themed gaps (271 errors across 38 files)
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

Specific instances:
- #84 — `_coerce_company_oid` returns `Optional[Any]` to keep beanie lazy-import.
- #86 — `union-attr` on `dict.get(...)` chains across agent services (92 errors).
- #87 — `arg-type` on `PydanticObjectId | None` → required at router/service boundaries (~25 errors).
- #88 — `assignment` implicit-Optional defaults across agents / prompts (~50 errors).
- #89 — `arg-type` on agent services — `Material | None` → `Material` (~30 errors).
- #90 — `models/estimate.py` arithmetic on `Optional[int]` fields (16 errors).
- #91 — `call-arg` on `ChatOpenAI(openai_api_key=...)` signature drift (5 errors).
- #92 — `call-arg` on agent → router calls missing `http_request` (5 errors).
- #93 — `BlockingPortal | None` errors in tests (12 errors).
- #124 — `openai_api_key=` keyword on ChatOpenAI flags mypy in maple_guide / maple_public.
- #183 — `change_logs.py` `.sort()` tuple type mismatch (pre-existing).
- #256 — `detail` lacks an explicit type annotation in the orchestrate credits-gate try/except.

**Absorbed:** #84, #86, #87, #88, #89, #90, #91, #92, #93, #124, #183, #256 — themed mypy gaps surfaced in later review passes. See `## Closed` for original bodies.

Progress 2026-05-20: cleared all `union-attr` errors from `agents/property/service.py` (15 → 0 in file; total mypy errors 384 → 365 globally — the assert-on-`target_property` added for union-attr coverage also collapsed three `arg-type` errors on `_property_to_dict` calls). Closes the `union-attr` portion of #86 for this file; the `Property | None` → `Property` arg-type slice of #89 also drops 3 errors. Fixes were pure type narrowing via `assert` (LLM guarded by callers, `target_property` guaranteed non-None after `if resolve_error: return`, `active_pending_intent` guaranteed non-None inside `should_fallback_to_pending`) plus tightening two `if active_pending_intent_id and ...` conditions to also check `active_pending_intent is not None`. No real null-deref bugs surfaced — all 15 were narrowing gaps.

Progress 2026-05-20: applied the same playbook to `agents/contact/service.py` (21 → 2 in file; total mypy errors 365 → 346 globally). Cleared 15 `union-attr` + 4 `arg-type` errors via 6 narrowing edits: 2 `assert self.llm is not None` on the `_classify_with_llm` / `_extract_entities_with_llm` paths (callers gate on `self.use_llm and self.llm is not None`), 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_contact is not None` after the `if resolve_error: return` early-bail, and 2 pending-delete conditions tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for contact; the `Contact | None` → `Contact` arg-type slice of #89 also drops 4 errors. Remaining 2 errors in this file (`no-redef` at L1794, `assignment` at L2014) are unrelated — separate categories from #3. Verified with `tests/test_contact_agent.py` + `test_contact_api.py` + `test_contact_model.py` + `test_cross_resource_envelope_contact.py` (99 tests passing).

Progress 2026-05-20: applied the same playbook to `agents/material/service.py` (17 → 4 in file; total mypy errors 346 → 333 globally). Cleared 10 `union-attr` + 3 `arg-type` errors via 5 narrowing edits: 2 `assert self.llm is not None` on `_classify_with_llm` / `_extract_entities_with_llm`, 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_material is not None` after the `if resolve_error: return` early-bail (collapses 3 `arg-type` errors on `_handle_get_material` / `_handle_delete_material` / `_material_to_dict` calls plus 3 `.name`/`.id` union-attrs), and 1 pending-delete condition tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for material; the `Material | None` → `Material` arg-type slice of #89 also drops 3 errors. Remaining 4 errors in this file are out of scope (390: `_parse_cost(Any | None)` arg-type; 1227, 1230: `call-arg` missing `http_request` — part of #92; 1356: `len(Any | list[Any] | None)`). Verified with `tests/test_material_agent.py` + `test_maple_material_size_operations.py` + `test_material_response_envelope.py` (88 tests passing).

Progress 2026-05-20: applied the same playbook to `agents/labour/service.py` (15 → 2 in file; total mypy errors 333 → 320 globally). Cleared 10 `union-attr` + 3 `arg-type` errors via 6 narrowing edits: 2 `assert self.llm is not None` on `_classify_with_llm` / `_extract_entities_with_llm`, 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_labour is not None` after the `if resolve_error: return` early-bail (collapses 3 `arg-type` errors on `_labour_to_dict` calls plus 2 `.id` union-attrs), and 2 pending-delete conditions tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for labour; the `Labour | None` → `Labour` arg-type slice of #89 also drops 3 errors. Remaining 2 errors in this file (721, 724: `call-arg` missing `http_request`) are part of #92. Verified with `tests/test_labour_agent.py` + `test_labour_api.py` (40 tests passing).

Progress 2026-05-20: applied the same playbook to `agents/equipment/service.py` (16 → 3 in file; total mypy errors 320 → 307 globally). Cleared 10 `union-attr` + 3 `arg-type` errors via 6 narrowing edits: 2 `assert self.llm is not None` on `_classify_with_llm` / `_extract_entities_with_llm`, 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_equipment is not None` after the `if resolve_error: return` early-bail (collapses 3 `arg-type` errors on `_equipment_to_dict` calls plus 2 `.id` union-attrs), and 2 pending-delete conditions tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for equipment; the `Equipment | None` → `Equipment` arg-type slice of #89 also drops 3 errors. **All four agent services (property/contact/material/labour/equipment) are now union-attr-clean — the `dict[str, Any] | None` and `<Resource> | None` slices of #86 are closed for this resource cluster.** Remaining 3 errors in this file (574, 586, 589: `call-arg` missing `request`/`http_request`) are part of #92. Verified with `tests/test_equipment_agent.py` + `test_equipment_api.py` (20 tests passing). Cumulative #3 progress this session: 384 → 307 mypy errors (-77 across the four agent services).

Progress 2026-05-20: cleared the remaining 4 errors in `agents/orchestrator/service.py` (4 → 0 in file; total mypy errors 271 → 267 globally on the `mypy agents/ routers/ models/` slice). Three targeted edits: (1) renamed the inner-loop variable `domain` → `hint_match` at line 1269 so the `str | None` return from `_match_first_hint` doesn't clash with the outer `str`-typed `domain` from the `for domain in domain_priority:` loop (cleared the `assignment` error); (2) added `assert self.llm is not None  # Callers gate on self.use_llm and self.llm is not None.` before the `prompt | self.llm.with_structured_output(...)` chain in `_classify_with_llm` (caller at line 1902 already gates on `self.use_llm and self.llm is not None`); (3) annotated `normalized_matches: List[Dict[str, Any]] = [...]` in `_normalize_llm_result` so the downstream `float(match.get("probability") or 0.0)` and `', '.join(match['intent'] for match in delegate_matches)` calls stop tripping `arg-type`/`misc` on the inferred `dict[str, object]`. Verified with `tests/test_orchestrator_intents.py` (185 passing) + `tests/test_orchestrator_bare_entity_helpers.py` + `tests/test_orchestrator_endpoint.py` (94 passing) — 279 total green. Closes the union-attr/arg-type slice of #86 for orchestrator; the file now has zero open mypy errors.

Progress 2026-05-20: closed **#92** (agent → router `call-arg` cluster). Cleared all 7 errors by applying the canonical implicit-Optional pattern (already used by `create_material`, `delete_all_materials`, `create_labour`, etc.) to 7 router sites: `update_material` and `delete_material` in `routers/materials.py`, `update_labour` and `delete_labour` in `routers/labours.py`, and `create_equipment` / `update_equipment` / `delete_equipment` in `routers/equipments.py`. Each was `http_request: Request,` (or `request: Request,` for equipment-create) made into `http_request: Request = None,  # type: ignore[assignment]` — the form documented in #3's preamble as "the only mechanically safe category" (`Optional[Request]` would break FastAPI's request injection). Behavioral check: all three audit-log call sites pass `request=http_request` directly to `create_audit_log`, which already accepts `Optional[Request] = None` (see `services/audit_service.py:101`) — when called via HTTP, FastAPI still injects the real Request; when called directly from an agent service (the path that previously raised `TypeError: missing positional argument`), audit logging still runs but without client_ip / user_agent metadata. Total mypy errors 267 → 260 globally. Verified with `tests/test_material_api.py` + `test_material_agent.py` + `test_labour_api.py` + `test_labour_agent.py` + `test_equipment_api.py` + `test_equipment_agent.py` (125 tests passing). The 2 remaining `call-arg` errors in `config.py:86` are unrelated (Pydantic Settings construction — `mongodb_url` / `openai_api_key` validated at runtime via env vars but not visible to mypy).

Progress 2026-05-20: cleared the 4 residual errors in `agents/property/service.py` (4 → 0 in file; total mypy errors 260 → 256 globally). Three edits: (1) added `assert linked_property is not None  # _resolve_estimate_linked_property guarantees non-None when error_message is None.` before `self._property_to_dict(linked_property)` in the estimate-code cross-resource handler (line ~1171) — the resolver's contract returns `(None, message)` on any failure and `(Property, None)` on success; (2) annotated `pending_record: Dict[str, Any] = {...}` at line 1804 (the `create_property` missing-fields branch) so the subsequent `dict["confirm_delete"] = False` reassignment at line 1967 (in the fuzzy-match `delete_property` branch — both paths share the variable via the outer `process()` scope) doesn't trip the inferred `dict[str, Collection[str]]` from the `"fields": dict[Any, Any]` value; (3) renamed the inner-loop `options = [str, ...]` at line 2167 → `contact_options` to avoid clashing with the outer-scope `options` from `_resolve_target_property`'s tuple unpack at line 1923 (which is `list[dict[str, Any]]`). Verified with `tests/test_property_agent.py` + `test_property_api.py` (57 tests passing). All `union-attr` / `arg-type` / `assignment` / `misc` errors in this file are now closed.

Progress 2026-05-20: cleared 2 errors in `prompts/estimate_react.py` and `prompts/estimate_architect.py` (total mypy errors 256 → 254 globally). Both `build_estimate_*_prompt(industry: str = None)` signatures used the implicit-Optional pattern. Fix: changed to `industry: Optional[str] = None` and added `from typing import Optional` to each file. These are pure-Python helper functions (not FastAPI routes), so the standard `Optional[str]` form is correct — the `# type: ignore[assignment]` shim is only needed for `Request` parameters where FastAPI's dependency injection breaks if the annotation is widened to `Optional[Request]`. No behavior change; both functions already test `if industry:` against falsy.

**This-session running totals**: 384 → 254 mypy errors (-130 across `agents/`, `routers/`, `models/`, `prompts/`). Closed in full: `#92` (call-arg cluster), `union-attr`/`arg-type` slice of `#86`/`#89` for property/contact/material/labour/equipment/orchestrator. Next candidate batches (require user approval — substantial scope): `agents/estimate/*` cluster (133 errors across crud_handlers.py / service.py / work_item_handlers.py / llm_helpers.py / conversation_guide.py / catalog_matching.py — these are mostly `#88` implicit-Optional defaults and `WorkItemHandlersMixin` attr-defined errors from the mixin pattern, not the resolve-error narrowing playbook); `models/estimate.py` arithmetic on Optional[int] fields (13 errors, `#90`); `routers/estimates.py` boundary `PydanticObjectId | None` → required (17 errors, `#87`).

Progress 2026-05-20: cleared the 17 errors in `routers/estimates.py` (17 → 0 in file; total mypy errors 254 → 237 globally). Seven edits: (1) `assert company_obj_id is not None` after `parse_object_id(company, ...)` at the top of `create_estimate` (line 295) — the `if not company: raise` check above guarantees the parse returns a real OID; cascades to clear errors at L296 (`assert_company_access`) and L324 (`get_company_defaults`); (2) `# type: ignore[operator]  # Beanie descriptor unary-minus sort idiom.` on `query.sort(-Estimate.created_at).limit(limit)` at L426 — Beanie's negate-field syntax is correct at runtime but unmodellable in mypy stubs; (3) annotated `update_data: Dict[str, Any] = {}` in `update_estimate` (L801) — was being inferred as `dict[str, str]` from the first `update_data["title"] = payload.title` assignment, breaking subsequent assigns of `description`/`property`/`status`/`job_items`/`grand_total`/`updated_at` (clears 7 errors at L809–1020); (4) `effort_card_items=[EffortCardItem(**ci.model_dump()) for ci in a.effort_card_items]` at L962 — explicit `EffortCardItemCreate → EffortCardItem` conversion via Pydantic constructor instead of relying on auto-coercion of `dict` payloads (mypy can't see Pydantic's runtime coercion); (5–7) four `assert <reload> is not None` after `await Estimate.get(estimate_id)` re-reads following a `.set(...)` mutation — archive (L1207), unarchive (L1285), generate-doc (L1362), delete-doc-version (L1410). Each reload is on the same estimate_id that was just mutated, so a None return would indicate a concurrent delete race or DB outage — `assert` is correct since the route has already authenticated and the prior mutation succeeded. Closes the bulk of `#87` for this file. Tests verified: 107 passing in `tests/test_estimate_api.py` + `test_estimate_docs_api.py` + `test_estimate_quota.py`. 3 pre-existing test-isolation flakes (`test_archive_estimate_as_non_creator_member_fails`, `test_docs_versions_sorted_by_version_desc`, `test_docs_versions_empty`) all pass in isolation and exercise code paths untouched by these edits (403 auth path and GET routes); flagged but not introduced by this change.

Progress 2026-05-21: closed the **`agents/estimate/*` cluster** — the single largest remaining batch flagged in the 2026-05-20 "next candidates" line (133 errors across 6 files in the original estimate; the actual surface was 180 errors across 6 files at the start of this work). Total mypy errors 217 → 77 globally (-140). All 12 source files under `agents/estimate/` now show `Success: no issues found in 12 source files`.

The work split into three patterns matching the file shapes:

1. **Mixin attr-defined cluster (#88-adjacent)** — `crud_handlers.py` (64 errors) and `work_item_handlers.py` (32 errors) were both 100% `attr-defined` from the mixin pattern: methods called via MRO from sibling mixins (`CrudParsingMixin`, `WorkItemHandlersMixin`, etc.) but invisible to mypy at the call site. Fix: added a `if TYPE_CHECKING:` stub block at the top of each mixin class declaring the sibling-resolved methods (`_crud_envelope`, `_resolve_estimate_code`, `_estimate_status_from_text`, `_estimate_summary_payload`, `_load_estimate_for_*`, the work-item handler quintet, etc.). 19 stub declarations in `crud_handlers.py`, 4 in `work_item_handlers.py` — all signatures lifted verbatim from the real implementations in `crud_helpers.py` and `work_item_handlers.py`. The `if TYPE_CHECKING:` guard means zero runtime cost — these stubs only exist during mypy's pass. Also added one `assert code is not None` after `_load_estimate_for_read` in `work_item_handlers.py:_handle_get_work_item` (resolver contract: code is non-None when error is None).

2. **`#88` implicit-Optional defaults in `service.py`** — 23 errors, all `param: X = None` where `X` was non-Optional. Canonical fix: widened each to `Optional[X] = None`. Touched signatures: `_merge_duplicate_line_items` (carry_fields), `_step1_architect` / `_step2_and_3_for_scope` / `_step3_research_single_scope` (industry, tokens), `_run_pipeline` / `_run_react_loop` (company_id, industry, max_iterations, tokens), `_generate_estimate` / `_score_with_inventory_check` (tokens), `process` / `analyze_project` / `answer_question` (company, property, context, estimate_data), `generate_estimate` (job_items). Also propagated the Optional widening down to `_step2_vector_retrieval(company_id)` and the `create_estimate_tools(company_id)` factory in `tools.py`. None of these required runtime guards added — the function bodies already handle the None case.

3. **Inference fixes** — handful of one-off shape issues: (a) split three sites where `payload.get("X") if isinstance(payload.get("X"), list) else []` was tripping `Any | list[Any] | None` (the same `.get()` called twice can't narrow); bound the value to a local first then narrowed (`_base_raw = base.get(...); base_items: List[Any] = _base_raw if isinstance(_base_raw, list) else []`); same pattern applied to three `dict(working_context.get(KEY))` sites; (b) `messages: List[Any] = [SystemMessage(...)]` to allow `HumanMessage` appends (langchain doesn't expose a `BaseMessage` union convenient for the local annotation); (c) `final_summary = str(msg.content)` to coerce langchain's `str | list[str | dict]` content union to a flat string for log use; (d) `context: Dict[str, Any] = {"project_description": ...}` in `generate_estimate` to allow the later `context["job_items"] = job_items` assignment; (e) widened `_score_catalog_match(requested_value: Any, candidate_values: List[Any])` + `_canonicalize_text(text: Any)` + `_find_best_catalog_match(requested_value: Any, ...)` in `catalog_matching.py` — the functions already coerce via `_normalize_catalog_text(value: Any)` so the strict `str` annotations were over-specified; (f) `ESTIMATE_DETAILS: List[Dict[str, Any]] = [...]` in `conversation_guide.py` to stop mypy inferring `object` for the heterogeneous dict values; (g) removed the dead `try/except ImportError → fallback to ()` block in `llm_helpers.py:format_llm_error` — both `openai` and `httpx` are hard deps in `requirements.txt` so the import fallback never fires, and the `if AuthenticationError and isinstance(...)` truthy guards became always-True after the cleanup.

Verified with `tests/test_estimate_agent.py` (112 passing) + `test_estimate_tools.py` + `test_estimate_crud_handler_helpers.py` (137 passing across those + `test_estimate_agent.py` re-run) + recurrence/analytics tests already covered in earlier #90 work. **This-session running totals**: 276 → 77 mypy errors (-199), closing #90, #93, and the `agents/estimate/*` cluster — the three remaining named batches from the 2026-05-20 candidate line are now done.

Progress 2026-05-21: closed **#93** (`BlockingPortal | None` errors in tests). Cleared all 29 errors across 10 test files (note: original entry estimated 12 errors across 5 files; the actual surface grew to 29 sites across 10 files as more API tests adopted the `client.portal.call(...)` pattern). Total mypy errors 263 → 234 globally. Pattern: 17 added `assert client.portal is not None  # TestClient context manager guarantees a portal (mypy hygiene)` calls — one per function/helper that invokes `.portal.call(...)`; mypy's flow analysis narrows the union for the rest of the function scope so a single assert covers multiple `.portal.call` sites in the same function. Files touched: `test_rate_card_bootstrap.py` (5 asserts for 9 sites: 2 helpers + 3 tests), `test_change_logs_api.py` (2: 1 fixture + 1 helper), `test_audit_integration.py` (2: 2 tests), `test_feedback_anonymous.py` (2: 2 tests), and one assert each in `test_template_api.py`, `test_resources_rbac.py`, `test_property_api.py`, `test_divisions_api.py`, `test_feedback_api.py`, `test_company_api.py`. Rejected the alternative "thin `_get_portal()` helper" suggested in the original entry — would have required touching every `.call` site in 10 files plus changes to test function signatures; the per-function `assert` matches the playbook used in earlier #3 progress notes (`assert self.llm is not None`, `assert target_<resource> is not None`) and is the minimum-touch fix. Verified by re-running mypy: 0 BlockingPortal-related errors remain.

Progress 2026-05-21: closed **#90** (`models/estimate.py` arithmetic on `Optional[int]` fields). Cleared all 13 errors in this file (13 → 0; total mypy errors 276 → 263 globally). Two edits in `RecurrenceSchedule`: (1) added `assert month_val is not None` inside the `for month_val in [self.start_month, self.end_month]:` loop in `validate_end_type_fields` — guaranteed non-None by the preceding `if any(v is None ...)` guard inside the `DATE_RANGE` branch; (2) added per-branch `assert <field> is not None` block at the top of each `if/elif` in `calculate_occurrences()` — `end_year`/`start_year`/`end_month`/`start_month` for `DATE_RANGE`, `total_occurrences` for `TOTAL_OCCURRENCES`, `end_year`/`start_year`/`specific_months` for `SPECIFIC_MONTHS`. All asserts reference the `@model_validator(mode="after")` contract that fires on construction (covered by `tests/test_recurrence_model.py` with explicit `pytest.raises(ValidationError)` cases for each branch's required-field shape). Tightening the model declarations to `int = 0` was rejected — the fields are conditionally required *based on `end_type`*, so the Optional typing is correct at the field level; narrowing belongs in the methods. Verified with `tests/test_recurrence_model.py` + `test_estimate_api.py` + `test_estimates_analytics.py` (133 passing). No behavior change.

Progress 2026-05-20: closed the audit-log channel-provenance gap surfaced during the `/code-review` of the `#92` fix. The implicit-Optional widening of `http_request: Request` on 7 router signatures means agent → router calls now succeed silently with `request=None`, dropping `ip_address` / `user_agent` / `method` / `path` from those audit log rows. Without a channel marker, downstream consumers can't distinguish Maple-initiated mutations from a misconfigured Portal request that lost its Request context. **Fix**: added `_audit_source_ctx: ContextVar[Optional[str]]` + `audit_source(source: str)` context manager in `services/audit_service.py`, and modified `create_audit_log` to merge `{"source": ctx_source}` into `metadata` when the var is set (caller-supplied `metadata["source"]` wins). Then wrapped the 7 previously-untagged agent → router callsites with `with audit_source("<resource>_agent"):` — `_update_material_via_api` + `_delete_material_via_api` (material), `_update_labour_via_api` + `_delete_labour_via_api` (labour), and `_create_equipment_via_api` + `_update_equipment_via_api` + `_delete_equipment_via_api` (equipment). The existing `_create_material_via_api` / `_create_labour_via_api` already tagged `metadata={"source": "<resource>_agent"}` directly (they bypass the router) — now the entire CRUD-via-Maple surface is consistently provenance-tagged. **Tests**: added 6 new tests in `tests/test_audit_service.py` — 3 unit tests for the ContextVar (set/reset/nesting/exception-safety), and 3 integration tests that mock the router call and assert the context var resolves to the expected source mid-call (`material_agent` / `labour_agent` / `equipment_agent`). All 132 tests pass across `test_audit_service.py` + `test_material_*` + `test_labour_*` + `test_equipment_*` + `test_audit_integration.py`. Closed independently of `#3` — this was a side-effect of the `#92` resolution, not a pre-existing mypy gap.

</details>


### 175. [MEDIUM] ~~`JobItemCreate` margin/tax fields accept unbounded floats~~ — RESOLVED 2026-07-27
**Severity**: MEDIUM
`platform/routers/estimates.py:609–614` — `original_profit_margin`,
`profit_margin`, `overhead_allocation`, `labor_burden`, and `tax` are all
`Optional[float] = None` with no bounds. Pydantic accepts NaN, ±Infinity,
and arbitrarily large/negative values. A malicious or buggy client could
persist garbage. Pre-existing pattern across the model — I added one more
field with the same loose typing rather than tightening it.

**Closed as resolved 2026-07-27.** New `models/numeric_fields.py` defines
`PercentField` / `MoneyField` (+ `Optional*` variants) as
`Annotated[float, Field(allow_inf_nan=False, ge=…, le=…)]`, applied across
`JobItemCreate` and every child `*ItemCreate` model. Three decisions worth
recording, because each is a deliberate departure from the original suggestion:

- **Scope widened to the money fields.** `price` / `cost` / `quantity` /
  `rate` / `effort` / `sub_total` carry the identical defect, and a NaN price
  makes every downstream total NaN just as surely as a NaN margin does.
  Fixing only the percentages would have left the same hole with a wider
  entry point. Same one-line-per-field mechanism, so it was folded in.
- **Bounds are wide, and percentages are NOT clamped to `[0, 100]`.** The
  portal's "Adjust Work Item Total" back-solves a margin from a user-supplied
  total (`backCalculateProfitMargin` in
  `portal/src/utils/estimateCalculations.ts`), which legitimately yields a
  **negative** margin when the total is set below subtotal, and margins in the
  thousands for a small subtotal. Clamping to `[0, 100]` would have broken a
  shipped feature. Limits are ±1,000,000% for percentages and ±1e12 for money
  — enough to reject garbage and keep the compound
  `(1 + p/100) × (1 + o/100)` product far from overflow, without rejecting any
  plausible business input. Money is likewise not floored at zero (credits and
  discounts are real line items).
- **Stored models are not constrained**, against the original suggestion to
  apply the aliases to `JobItem` too. Adding bounds to a stored model would
  make any pre-existing document holding a bad value permanently unreadable (a
  500 on every read of that estimate), which is a strictly worse failure than
  the one being fixed. Stored values are kept clean by sanitizing at
  construction instead — see the parsed pipeline below.

**Two ingresses, not one.** The `*ItemCreate` request models only cover the
hand-edit path (portal PUT/POST). The **AI-generation path — the primary way
estimates are created here — never touches them**: `job_item_builders.py`
constructs the stored `MaterialItem` / `LabourItem` / `ActivityItem` straight
from LLM-parsed dicts. That path was left open by the first pass of this fix
and closed by a follow-up `/code-review`; it is the more important of the two.

Every numeric read out of a parsed dict now routes through
`coerce_finite_float` (via a module-local `_finite()` in
`job_item_builders.py`), covering `job_item_builders.py` (materials, labours,
unmatched variants, activities, `sub_total`, `labor_burden`, `tax`),
`calculations.py` (`parse_profit_margin`, `parse_overhead_allocation`, and the
three line-item total loops), and `job_item_merge.py` (both builder functions).
Three properties this buys, none of which the old bare `float()` had:

- `json.loads` accepts bare `NaN` / `Infinity` literals and `float("nan")`
  accepts the string form — both now degrade to a default.
- A non-numeric token like `"abc"` used to *raise* `ValueError`, turning one
  bad LLM value into a 500 for the whole estimate. It now degrades one field.
- **`tax` degrades to `None`, not `0.0`** — via the separate `finite_or_none`
  helper. `None` means "unset, apply the company default"; `0.0` asserts
  *tax-exempt*. Collapsing garbage onto `0.0` would invent a tax claim on the
  customer's behalf. This distinction is the reason there are two helpers.

`_build_parsed_effort_cards` replaced an `EffortCardItem(**ci)` splat of the
raw LLM dict in the same pass. The splat was fragile beyond the NaN issue:
`EffortCardItem` declares no `extra="ignore"` and four of its fields are
required, so a single unexpected or missing key from the model raised and 500'd
the whole estimate. It now builds field by field with defaults. (The sibling
splat in `_build_request_activities` is fine — it dumps an already-validated
`EffortCardItemCreate`.)

`grand_total` is bounded on both `CreateEstimateRequest` and
`UpdateEstimateRequest`: the update handler writes `payload.grand_total`
straight to the document when `job_items` is absent, with no recomputation on
that branch, so the request model is the only thing between a client value and
the DB.

Tests: `tests/test_estimate_numeric_validation.py` (181 cases — non-finite
floats and their string forms, non-numeric strings, absurd magnitudes, the
parsed-builder pipeline end-to-end, the `tax`-stays-`None` rule, plus explicit
accepts-negative-margin / accepts-margin-above-100 cases pinning the bounds
that must stay loose).

---


### 221. [MEDIUM] ~~`meter_events.report_seat_count` atomic update inside broad `except` swallows DB errors~~ — RESOLVED 2026-07-26
**Closed as resolved 2026-07-26.** `report_seat_count` now has two separate try
blocks with distinct failure policies:
- **Stripe post** — unchanged best-effort semantics (log + swallow), then
  `return`. The early return is the load-bearing part: bumping the high-water
  mark for a value Stripe never received would permanently suppress the repost,
  because every later snapshot at that count short-circuits on the `<=` guard.
- **High-water write** — `logger.exception("Failed to persist the seat-count
  high-water mark for company %s (the meter event was accepted by Stripe)")`
  then re-raises. `snapshot_all_seat_counts` (the only caller) already
  try/excepts per company, so the error lands in its `errors` counter and the
  loop continues — no behavior change for the cron beyond accurate accounting.

Tests: `tests/test_billing_meter_events.py::TestReportSeatCountAtomicHighWater`
— `test_db_failure_is_not_reported_as_a_stripe_meter_failure` (asserts the
meter event was posted, the Stripe-shaped message is absent, and a high-water
message is present) and
`test_stripe_failure_leaves_high_water_unbumped_and_does_not_raise`. 19 passed;
mypy/ruff clean.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/services/billing/meter_events.py:99-122](../../platform/services/billing/meter_events.py)
**Severity**: MEDIUM

The atomic `find_one_and_update` added by [#200](#200-atomic-high-water-update-in-meter_eventspy)
lives inside the same `try / except Exception` block originally meant
to catch Stripe failures. A pymongo error from the conditional update
gets logged with `"Failed to report seat-count meter event"` —
misleading because the meter event already succeeded by that point.
Worse, the silent swallow means the next `report_seat_count` call
sees a stale local `company.seat_count_period_high_water` and may
re-post the same value to Stripe (which is harmless thanks to the
date-keyed idempotency key, but still wastes a round trip).

Fix: split into two try blocks (Stripe → log+continue, DB → propagate
or log via a distinct error path), OR tighten the except to
`(stripe_sdk.error.StripeError,)` so DB errors surface, matching the
narrow-except pattern landed in `customer.py` ([#199](#199-narrow-the-except-in-customerpy67)).

</details>


### 293. [HIGH] ~~Frontend test for `resolveRecaptchaSiteKey` blocked by current architecture~~ — RESOLVED 2026-05-21
**Closed as resolved 2026-05-21.** Contact modal moved out of `website/public/` into a proper Vite entry. New layout:
- `website/contact-modal/install.js` — extracted from `public/contact-modal.js`; named-exports `install`, `resolveRecaptchaSiteKey`, `loadRecaptcha`, `getRecaptchaToken`. No top-level side effects so vitest can import without triggering DOM injection.
- `website/contact-modal/index.js` — 16-line build entry that imports `install` and runs it on DOMContentLoaded.
- `website/contact-modal/__tests__/resolveSiteKey.test.js` — 4 tests (real key → returned, empty → empty string, unsubstituted Vite placeholder → empty string, whitespace trim).
- `vite.config.ts` — added `'contact-modal'` to `rollupOptions.input` so prod build emits `dist/contact-modal.js`; added a `contactModalDevRewrite()` middleware that serves a `import('/contact-modal/index.js')` shim when the dev server receives `GET /contact-modal.js` (HTML pages already use `<script src="/contact-modal.js" defer>` — no HTML changes needed).
- `vitest.config.ts` — extended `include` glob to `contact-modal/**/*.test.{js,ts}`.
- `public/contact-modal.js` — deleted (was 491 lines).

Also closed **#298** as a side-effect — the heuristic placeholder check became `trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%'` while editing the file. Verified: vitest 42/42 green; `vite build` emits `dist/contact-modal.js` cleanly; dev server smoke-test confirms `/contact-modal.js` returns the dynamic-import shim and `/contact-modal/index.js` serves the source.

The follow-on opportunity (#296, the ~120-line `install()` split) is now unblocked — `install` is exported and could be unit-tested or split further.

<details>
<summary>Original body (preserved for history)</summary>

**Where:** `website/public/contact-modal.js`.

**Why blocked:** `contact-modal.js` lives in `public/` and is served verbatim by Vite/Hosting. It's wrapped in an IIFE (no exports), so its helpers can't be imported by vitest. To test `resolveRecaptchaSiteKey` (the Vite-substitution-detection logic), the file needs to become a proper Vite/Rollup entry — same pattern as `widget/index.tsx` / `maple-widget.js`.

**Suggested move:**
1. Create `website/contact-modal/index.ts` (or `.js`) with the modal logic, exporting helpers like `resolveRecaptchaSiteKey` for tests.
2. Add the entry to `vite.config.ts` `rollupOptions.input` and `entryFileNames` rules so the build emits `dist/contact-modal.js` at the same path.
3. Drop `website/public/contact-modal.js`.
4. Add `website/contact-modal/__tests__/resolveSiteKey.test.ts` covering: real key → returned, empty → empty string, raw `%VITE_RECAPTCHA_V3_SITE_KEY%` placeholder → empty string.

This refactor also unlocks unit-testing the submit handler, the captcha load promise, and the form validation helper.

</details>


### 295. [MEDIUM] ~~Tighten CORS~~ — RESOLVED 2026-07-26
**Closed as resolved 2026-07-26.** `cors: true` → a named `ALLOWED_ORIGINS`
constant in `website/functions/index.js`. Kept `cors` rather than dropping it
(the second option) so the Firebase-provided domains and the local emulator
keep working; production traffic is same-origin through the Hosting rewrite
either way.

The suggested list needed one correction: it named only the **dev** hosting
site. Per `.firebaserc` the prod target `website` maps to site
`maples-website`, so the shipped allowlist adds
`https://maples-website.web.app` and `https://maples-website.firebaseapp.com`
alongside the apex/www custom domain, the two dev domains, and
`http://localhost:5050` (matching `firebase.json` → `emulators.hosting.port`).

Tests: new `website/functions/corsConfig.test.js` (5) captures the config
object from the `onRequest` mock and asserts the allowlist shape — no wildcard,
prod + dev domains present, emulator port present, arbitrary origin absent.
33 function tests pass; full website suite 186 passed; build clean.

<details>
<summary>Original body (preserved for history)</summary>

**Where:** `website/functions/index.js:26` — currently `cors: true` (wildcard).

**Why:** The contact form is served via Hosting rewrite, so traffic to `/api/contact` is same-origin and doesn't need CORS at all. Wildcard CORS lets any origin POST to the endpoint; reCAPTCHA mitigates abuse but tightening costs nothing.

**Suggested fix:**

```js
cors: [
  'https://3maples.ai',
  'https://www.3maples.ai',
  'https://maples-website-dev.web.app',
  'https://maples-website-dev.firebaseapp.com',
  'http://localhost:5050', // hosting emulator
],
```

Or drop `cors` entirely and rely on same-origin Hosting rewrites for prod traffic; only add CORS when explicit cross-origin support is needed.

</details>


### 298. [LOW] ~~Replace placeholder heuristic with explicit equality~~ — RESOLVED 2026-05-21
**Closed as resolved 2026-05-21** as a side-effect of #293. Now `trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%'` in `website/contact-modal/install.js:resolveRecaptchaSiteKey`. Covered by the new vitest case at `contact-modal/__tests__/resolveSiteKey.test.js`.

<details>
<summary>Original body (preserved for history)</summary>

**Where:** `website/public/contact-modal.js:5-11` — `resolveRecaptchaSiteKey`.

**Why:** Current check rejects values containing `%` or starting with `VITE_`. Functional but heuristic. An explicit check on the literal placeholder is clearer:

```js
if (!trimmed || trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%') return '';
return trimmed;
```

</details>


### 303. [HIGH] ~~Unit tests missing for the 9 new `routers/agent_helpers/` modules~~ — RESOLVED 2026-06-03
**Severity**: HIGH (resolved)

**Resolved 2026-06-03**: 8 module-level unit-test files added (103 tests), one
per untested helper — `estimate_gathering.py` already had
`tests/test_estimate_gathering.py`, so the original "9" was 8 in practice:

| Module | Test file | Tests |
|---|---|---|
| `finalize_result.py` | `tests/test_agent_helpers_finalize_result.py` | 17 |
| `estimate_resolver.py` | `tests/test_agent_helpers_estimate_resolver.py` | 9 |
| `delegate_generic.py` | `tests/test_agent_helpers_delegate_generic.py` | 7 |
| `pending_estimate_follow_up.py` | `tests/test_agent_helpers_pending_estimate_follow_up.py` | 24 |
| `optional_follow_up.py` | `tests/test_agent_helpers_optional_follow_up.py` | 21 |
| `delegate_get_estimate.py` | `tests/test_agent_helpers_delegate_get_estimate.py` | 11 |
| `delegate_estimate_ops.py` | `tests/test_agent_helpers_delegate_estimate_ops.py` | 14 |
| `delegate_create_estimate.py` | `tests/test_agent_helpers_delegate_create_estimate.py` | 7 |

Each file covers every envelope return path / state-machine branch via
injected fakes + `monkeypatch` (no DB or LLM). All 103 pass; mypy clean.
A latent matcher quirk surfaced and was characterized (not fixed —
tracked as a new LOW below): `find_property_by_name_or_address` treats a
property with a **blank `street`** as a contains-match for *any* query
(`"" in query` is always true), so such a property auto-links. See
`test_find_property_blank_street_contains_matches_any_query`.

**Where:** `routers/agent_helpers/pending_estimate_follow_up.py`, `optional_follow_up.py`, `estimate_gathering.py`, `delegate_create_estimate.py`, `delegate_estimate_ops.py`, `delegate_get_estimate.py`, `delegate_generic.py`, `finalize_result.py`, `estimate_resolver.py` (all landed 2026-05-22).

**Issue:** All 9 helper modules extracted from `orchestrate_agent_endpoint` lack module-level unit tests. Behavior is exercised through `tests/test_orchestrator_endpoint.py` integration tests (52 passing), so no regression risk today — but each helper is a state machine with multiple return paths (`handle_pending_estimate_follow_up` has 9 envelope returns spanning `confirm`/`select_property`/`negative`/`list-properties`/`no-properties`/`escape-hatch`/`resolve-error`/`success` shapes) and the integration tests don't necessarily cover every branch. Per `CLAUDE.md` "tests are mandatory after any code change" — extraction without unit-test backfill leaves the per-branch behavior implicit in the endpoint tests.

**Fix:** Add per-helper unit-test files (`tests/test_pending_estimate_follow_up.py`, etc.) with one test per return path. Each test constructs a `context_payload` matching the entry state, asserts the returned envelope's `intent` / `response` / `result.operation` / `needs_clarification` flags. Use the existing fixtures (`monkeypatch` for `Estimate.get`, `properties_api_get_properties`, etc.) — same shape as the integration tests but scoped to one helper. Estimated 6-9 tests per module = ~60-80 new tests total.


### 306. [HIGH] ~~`_detect_work_item_op()` is 202 lines~~ — RESOLVED 2026-07-27
**Where:** `agents/estimate/work_item_handlers.py:110`

**Issue:** Grew from ~75 lines to 202 with the new sub-resource ops. Readable as a cascading if-chain but past the length threshold.

**Closed as resolved 2026-07-27.** `_detect_work_item_op` is now **34 lines**
and the whole detector chain sits under the threshold (largest: 44):

| function | lines |
|---|---|
| `_detect_work_item_op` | 34 |
| `_detect_sub_resource_op` | 34 |
| `_detect_catalog_sub_op` | 29 |
| `_detect_work_item_field_op` | 44 |
| `_detect_inferred_material_op` | 15 |
| `_detect_total_op` | 12 |
| `_detect_legacy_work_item_op` | 21 |
| `_detect_legacy_update_field` / `_rename` / `_add` / `_remove` | 22 / 13 / 18 / 11 |

Went past the suggested fix in two places, both deliberate:

- **Material and activity now share `_detect_catalog_sub_op`.** The two blocks
  were structurally identical — list/count, then add / remove / update, then a
  trailing what/how-many that also means list — differing only in keyword and
  op suffix. Parameterized on `(keyword_pattern, singular, plural)`.
- **The legacy cascade was split too**, against "keeps the legacy patterns
  untouched". Extracting only the `has_wi` block left two functions still over
  50 lines, i.e. **more** oversized functions in the file than before (6 → 7).
  Splitting the legacy loops into four single-purpose detectors brought the
  file to 6 → 5. The pattern tuples and their ordering comments are unchanged;
  only the enclosing function boundaries moved.

**Method — characterization tests first, and they earned their keep.**
`TestDetectWorkItemOp` already asserted 17 of the 18 op shapes, but nothing
pinned *precedence* or *fall-through*, which is exactly what an extraction
breaks. New `TestDetectWorkItemOpPrecedence` (15 cases) records behavior
captured from the pre-refactor implementation, including three results that are
not obvious from reading the code:

- `"add a material to the recurring work item"` → `recurring_enable`, not
  `add_material` — recurring is checked first and wins outright.
- `"set the total of work item 1 to 4200"` → `update_field` with
  `field="total"`, **not** `set_total`. Neither total pattern matches, so it
  falls through to the generic legacy update_field pattern. Recorded as-is; it
  is behavior, not necessarily intent.
- `"add a work item and list them"` → `add` with an empty name, not `list` —
  the mutation-verb guard suppresses `list` and the nameless-add pattern claims
  it.

Both extractions were mutation-tested rather than assumed safe: forcing the
`has_wi` block to swallow instead of fall through failed 12 tests, and swapping
material/activity precedence failed 2. 423 tests pass across
`test_maple_work_item_ops.py`, `test_estimate_agent.py` and
`test_maple_crud_coverage.py`; ruff + mypy clean.

**Not addressed:** the five `_handle_update_estimate_work_item_*` methods in
this file are still over 50 lines (172 / 126 / 79 / 75 / 59). That is #305's
territory, not this item's.


### 307. [HIGH] ~~Full-catalog fetch for material/role lookup~~ — RESOLVED 2026-06-03
**Severity**: HIGH (resolved)
**Where:** `agents/estimate/work_item_field_handlers.py:531` and `:889`

**Issue:** `Material.find(company==X).to_list()` and `Labour.find(company==X).to_list()` load the full company catalog into memory for Python-side substring matching. Acceptable at current scale (<1000 items) but degrades on larger catalogs.

**Resolved 2026-06-03**: extracted two helpers — `_find_catalog_materials()`
and `_find_catalog_roles()` — that push the name substring match into MongoDB
via a case-insensitive `{"name": {"$regex": re.escape(hint), "$options": "i"}}`
filter (alongside the existing `company ==` clause). The handlers now receive
only matching documents instead of the whole catalog; the exact-match /
ambiguity disambiguation logic stays in the handler on the (now-smaller) list.
`re.escape` preserves literal-substring semantics for hints containing regex
metacharacters. Dead inline `from models import Material/Labour` imports in the
two handlers removed. New `tests/test_work_item_catalog_lookup.py`: 6 unit tests
(query-shape + escaping + empty-hint short-circuit, `find` stubbed) plus 1 live
test that exercises the real `$regex` against the test DB (match returns only
the matching doc; non-match returns nothing). mypy clean; 102 related tests pass.


### 323. [RESOLVED 2026-06-04] ruff manual backlog — fully cleared; `platform/` is at zero ruff errors
Snapshot 2026-06-03 (`./run_ruff.sh`); **B904 slice closed 2026-06-03** (32 → 0);
**style/simplify slice (E741/E712/SIM/C4/B007) closed 2026-06-04** (52 → 0);
**E402 + F841 slices closed 2026-06-04** (56 + 52 → 0);
**F401 slice closed 2026-06-04** (281 → 0). `./run_ruff.sh` is now clean
project-wide — ruff is a fully-enforced zero-error gate, same as mypy.

| Rule | Count | Category | Notes |
|---|---|---|---|
| ~~**B904** raise-without-`from`~~ | ~~32~~ → **0** | correctness | **RESOLVED 2026-06-03** — see progress note below |
| ~~F401 unused-import~~ | ~~281~~ → **0** | dead code | **RESOLVED 2026-06-04** — see progress note below |
| ~~E402 import-not-at-top~~ | ~~56~~ → **0** | style | **RESOLVED 2026-06-04** — see progress note below |
| ~~F841 unused-variable~~ | ~~52~~ → **0** | dead code | **RESOLVED 2026-06-04** — see progress note below |
| ~~E741 ambiguous-name (`l`/`I`/`O`)~~ | ~~24~~ → **0** | style | **RESOLVED 2026-06-04** — see progress note below |
| ~~E712 `== True/False`~~ | ~~5~~ → **0** | style | **RESOLVED 2026-06-04** |
| ~~SIM103/102/108/105~~ | ~~16~~ → **0** | simplify | **RESOLVED 2026-06-04** |
| ~~C408/C401/C416~~ | ~~5~~ → **0** | simplify | **RESOLVED 2026-06-04** |
| ~~B007 unused-loop-var~~ | ~~2~~ → **0** | style | **RESOLVED 2026-06-04** |

**Recommended order:** (1) **B904** — the only correctness category; it matches
CLAUDE.md's "don't leak/garble tracebacks" rule. Add `raise ... from err`
(preserve cause) or `raise ... from None` (suppress). B904 sites by file:
`services/google_drive_service.py` (12), `routers/agents.py` (6),
`routers/estimate_helpers/doc_versions.py` (3), `routers/audit_logs.py` (3),
`routers/templates.py` (2), `routers/stripe_webhooks.py` (2), `routers/auth.py`
(2), `routers/materials.py` (1), `routers/billing.py` (1). (2) the mechanical
style/simplify slices (E741/E712/SIM/C4/B007) — low risk. (3) E402 + F841 —
case-by-case judgment. (4) F401 last — largest and needs the per-import triage
above. **Slices (1)–(3) are now closed; only F401 (4) remains.**

Work each slice as its own commit (`./run_ruff.sh --select B904` to scope a
run). Update this entry's counts as slices close; mark RESOLVED when
`./run_ruff.sh` is clean project-wide.

**Progress 2026-06-03 — B904 slice closed (32 → 0).** All 32 raise-without-`from`
sites now chain explicitly; `./run_ruff.sh --select B904` is clean project-wide.
Cause-preservation split followed the playbook:
- **`from e`** (preserve cause) where the exception was already bound *and* is a
  genuine unexpected/internal failure worth chaining: `routers/stripe_webhooks.py`
  (signature-verify 400, handler 500) and all 12 `services/google_drive_service.py`
  sites (RuntimeError on credential/build failure + HTTPException 500s on Drive
  HttpError — each `except ... as e`).
- **`from None`** (suppress) where the re-raise is a deliberate boundary over
  expected input or an already-logged error: input-validation conversions
  (`routers/audit_logs.py` ×3 invalid enum 400, `routers/auth.py` ×2 invalid
  role/industry 400, `routers/agents.py` ×2 invalid ObjectId 422), 409 conflict
  conversions (`routers/templates.py` ×2 DuplicateKey), and 500/502 handlers that
  already `logger.exception(...)` the full traceback (`routers/agents.py` ×4,
  `routers/billing.py`, `routers/materials.py`, `routers/estimate_helpers/doc_versions.py` ×3).

Verified: full-project `./run_mypy.sh` slice clean (`routers`, `services`); 155
related tests pass (`test_stripe_webhooks`, `test_template_api`,
`test_audit_logs_api`, `test_billing_enterprise_contact`, `test_google_drive_service`,
`test_estimate_docs_api`, `test_orchestrator_endpoint`, `test_auth_api`). Next
slice per the recommended order: the mechanical style/simplify batch
(E741/E712/SIM/C4/B007).

**Progress 2026-06-04 — style/simplify slice closed (52 → 0).**
`./run_ruff.sh --select E741,E712,SIM,C4,B007` is clean project-wide. Breakdown:
- **E741** (24) — every `l` ambiguous-name was the same idiom: a labour item in a
  loop/comprehension. Renamed `l` → `lab` throughout each enclosing scope (renaming
  *all* uses, not just the binding). Sites: `agents/cross_resource.py`,
  `agents/estimate/{crud_handlers,llm_pipeline,service ×3,tools,work_item_field_handlers}.py`,
  `agents/property/service.py`, `routers/estimate_helpers/{job_item_builders ×5,snapshots ×2}.py`,
  `routers/estimates.py` ×3, `routers/labours.py`, and tests
  (`test_cross_resource_joins.py`, `test_labour_api.py` ×2).
- **E712** (5, all tests) — `== True/False` → truthiness / `not` in `test_google_drive_service.py`.
- **SIM103** (6) — `if cond: return True / return False` → `return cond`; the regex
  `.search()` cases wrapped in `bool(...)` to keep the `-> bool` return type honest
  (`routers/agents.py` ×4, `routers/agent_helpers/pending_calculation.py`,
  `routers/estimate_helpers/ai_generation.py`).
- **SIM102** (5) — collapsed nested `if`s into a single `and` condition, verified each
  outer `if` contained only the inner one (`routers/agents.py`, `routers/auth.py`,
  `routers/agent_helpers/finalize_result.py`, `services/google_drive_service.py`,
  `agents/estimate/crud_handlers.py`).
- **SIM108** (3) — if/else assignment → ternary (`delegate_create_estimate.py`,
  `services/address_service.py`, `tests/conftest.py`).
- **SIM105** (2) — `try/except: pass` → `contextlib.suppress(...)`, adding a top-level
  `import contextlib` to each (`routers/agent_helpers/delegate_get_estimate.py`,
  `scripts/setup_stripe_webhook.py`).
- **C416** (1) — redundant list comp → `list(_STATUS_ALIASES.items())` (`crud_helpers.py`).
- **C401** (1) — `set(gen)` → set comprehension (`work_item_field_handlers.py`).
- **C408** (3) — `dict(...)` → literal (`template_estimate.py` ×2, `tests/_cross_resource_fakes.py`).
- **B007** (2) — unused loop var `i` → `_` (`services/google_drive_service.py`).

Verified: `./run_mypy.sh agents routers services` clean (140 files); `compileall` clean;
458 related tests pass across `test_estimate_agent`, `test_estimate_api`,
`test_orchestrator_endpoint`, `test_labour_api`, `test_google_drive_service`,
`test_auth_api`, `test_cross_resource_joins`, `test_address_service`,
`test_agent_helpers_pending_calculation`, `test_estimate_snapshot_helpers`,
`test_job_item_original_profit_margin`, `test_maple_work_item_ops`. Remaining backlog
(390): F401 (282, needs per-import triage), E402 (56), F841 (52) — the case-by-case
slices per the recommended order.

**Progress 2026-06-04 — E402 + F841 slices closed (56 + 52 → 0).**
`./run_ruff.sh --select E402,F841` is clean project-wide; the whole remaining
backlog is now F401 only.

*F841 (52)* — 3 production dead assignments deleted (`services/google_drive_service.py`
unused `table`, `agents/property/service.py` unused `intent`,
`agents/estimate/crud_handlers.py` unused `has_custom_window`). In tests: 43
`agent = XAgent(use_llm=False)` constructions removed (the tests exercise module-level
helpers, not the instance — construction is side-effect-free with `use_llm=False`); 3
`result = asyncio.run(...)` cases kept the call but dropped the unused binding (asserts
read `captured`, not `result`); `fake_est` (immediately reassigned before use) deleted;
`second_owner = create_company_user(...)` kept the side-effecting call, dropped the
binding; `audit_logs_query` (a never-executed lazy Beanie `.find()` for deferred audit
verification) removed along with its now-orphaned `from models import ...` line.

*E402 (56)* — split between config and reorder:
- **`ruff.toml` per-file-ignores** for the two *structural* cases that cannot be
  reordered: `scripts/**/*.py` (operational scripts must `sys.path.insert(project_root)`
  before importing `database`/`models`/`config`) and `models/__init__.py` (interleaves
  `model_rebuild()` between import groups so Beanie/Pydantic forward refs resolve in
  dependency order). Cleared 33 findings.
- **Reorders** for the rest: moved the `logger = logging.getLogger(__name__)` assignment
  below the import block in `agents/orchestrator/service.py` (11); hoisted `import logging`
  + `from pymongo.errors import DuplicateKeyError` to the top of `routers/agents.py` (2);
  lifted co-located imports to the top in `tests/test_agents_api.py` (2),
  `tests/test_template_create_routing.py` (1), `tests/test_agent_helpers_text_predicates.py` (1).
- **Misplaced-noqa fix** in `agents/estimate/service.py` — the `# noqa: E402` sat on the
  continuation line; moved it to the `from ... import (` statement line so ruff honors it.

Verified: `./run_mypy.sh` clean on the 6 touched production files; full-project
`./run_ruff.sh` reports **281 F401 and nothing else**; 436 related tests pass across
`test_agents_api`, `test_audit_integration`, `test_user_api`, `test_estimate_agent`,
`test_contact_agent`, `test_property_agent`, `test_labour_agent`, `test_equipment_agent`,
`test_template_create_routing`, `test_agent_helpers_text_predicates`,
`test_google_drive_service`. Next and final slice: F401 (281) — the per-import triage.

**Progress 2026-06-04 — F401 slice closed (281 → 0). Backlog fully cleared.**
`./run_ruff.sh` is now clean project-wide across all 317 files. The per-import
triage was done with a classifier (built ad-hoc) that scans the whole repo for
each unused name and labels it **DEAD** (referenced nowhere outside its own
module), **REEXPORT** (another module does `from <mod> import <name>` or
`<alias>.<name>`), or **MONKEYPATCH** (a test does `setattr(<mod-alias>, "<name>", …)`).

- **Mechanized the safe deletion.** Protected every REEXPORT/MONKEYPATCH name
  with an inline `# noqa: F401  # <reason>`, then ran
  `ruff check --select F401 --fix --extend-fixable F401` (the `--extend-fixable`
  overrides `ruff.toml`'s `unfixable = ["F401"]` *for that one run*). ruff then
  removed only the genuinely-unused imports — including the multi-line paren-block
  surgery — and left the noqa-protected names untouched. Followed by
  `--select I --fix` to re-sort the import blocks. **174 dead imports removed.**
- **Biggest hubs:** `agents/estimate/service.py` (90: 87 dead leftovers from the
  service-split, +`ChatOpenAI` monkeypatch, +`ArchitectScope`/`DecomposedRequirement`
  re-exports kept), `routers/agents.py` (42), `routers/estimates.py` (27 — a
  documented re-export facade; kept the 8 consumed re-exports/monkeypatch targets,
  deleted the 19 nothing consumes). `__init__.py` files were already F401-exempt,
  so package re-exports were never at risk.
- **Caught a classifier gap with the test suite.** Two monkeypatch targets on
  `routers.agents` (`estimates_api_get_estimate`, `estimates_api_get_estimates`,
  aliased imports patched via `setattr(agents_router, …)`) were mis-labeled DEAD and
  removed; the orchestrator endpoint tests failed with `AttributeError: module
  routers.agents has no attribute …`. Restored both with `# noqa: F401`. An
  AST-based re-scan of every modified module then confirmed **0** remaining
  test-accessed attributes were missing.

Verified: full-project `./run_ruff.sh` clean (0 findings); `./run_mypy.sh` clean
(317 files); `pytest --collect-only` clean (no import errors across 2874 tests);
**full suite 2874 passed, 0 failures**.

> **#323 is RESOLVED.** With B904 + style/simplify + E402 + F841 + F401 all closed,
> `platform/` sits at zero ruff errors. ruff is now a fully-enforced gate (like
> mypy): any new `./run_ruff.sh` finding in a PR is a regression to fix in-place,
> not backlog. The legacy-backlog scoping caveat in CLAUDE.md's baseline note is no
> longer needed — `./run_ruff.sh` can be run project-wide without tripping over
> pre-existing findings.

---


### 349. [MEDIUM] ~~PUT `/estimates/{id}` allows content edits in statuses the UI and Maple treat as read-only~~ — RESOLVED 2026-07-26
**Closed as resolved 2026-07-26**, taking the "better" option: the allowlist now
lives in `models/estimate.py` as `EDITABLE_ESTIMATE_STATUSES` +
`estimate_status_allows_content_edit(status)` (accepts the raw stored string or
the enum; unrecognized/legacy values **fail open** so a retired status can't
strand an estimate nobody can unlock). Three consumers now share that one
definition:
- `routers/estimates.py` — new `elif` after the Sent/Approved block: any
  non-editable status rejects a payload carrying fields other than `status`,
  with `400 "Cannot edit the contents of a {status} estimate. Estimates can
  only be edited in Draft or Review."` Status-only payloads stay allowed, so
  the status lane (Won → Scheduled, Generating → Draft) is untouched and the
  transition itself is still policed by `_validate_status_transition_for_update`.
- `agents/estimate/crud_handlers.py` — `_EDITABLE_ESTIMATE_STATUSES` is now an
  alias of the model constant rather than a second definition.
- portal `isEditableStatus` — unchanged; the backend now matches it.

**FE coordination (the deferral's open question), resolved:** audited every
`estimatesApi.update` caller. The estimate detail page already gates on
`canEdit`, and `EstimatesPage` sends status-only payloads. The one real gap was
`PropertyDialog` → `EstimatesPicker`, which PUT `{property: …}` on any estimate
regardless of status — already 400ing today for Sent estimates, and would have
newly 400'd for Won/Lost/etc. Locked rows now render **visible but disabled**
(so a property's real links aren't hidden) with the reason inline. Tests:
`portal/tests/EstimatesPicker.test.tsx` (5).

Backend tests: `tests/test_estimate_api.py` — `TestEstimateContentEditability`
(5, incl. a guard that the agent and model share one object) plus 3 router
tests via the new `won_estimate` fixture: content edit rejected, content
smuggled alongside a legal status change rejected, status-only transition still
200. 425 passed across the estimate + billing + Maple surface; mypy/ruff clean.

<details>
<summary>Original body (preserved for history)</summary>

### 349. [MEDIUM] PUT `/estimates/{id}` allows content edits in statuses the UI and Maple treat as read-only
Added 2026-06-12. `routers/estimates.py` (PUT handler, ~L820): the route locks
Archived and Sent/legacy-Approved, but still accepts content updates (notes,
job_items, property, …) for Won / On Hold / Lost / Scheduled / Completed —
statuses the portal renders read-only (`isEditableStatus`: Draft/Review only)
and Maple now refuses to edit. Any direct API caller (integration, script,
future mobile client) can bypass the editing rule the product presents as
truth. Fix: add the same Draft/Review allowlist to the PUT route's lock block
(keeping the existing unsend exception for status-only changes), mirroring the
`_EDITABLE_ESTIMATE_STATUSES` constant — or, better, move the allowlist next to
`ESTIMATE_STATUS_TRANSITIONS` in `models/estimate.py` so model, route, and
agent share one definition. Coordinate with the FE before shipping: confirm no
portal flow PUTs content for non-Draft/Review estimates (e.g. auto-save firing
on a just-transitioned estimate).

</details>

---


### [LOW] ~~portal/src/lib/voiceInputFlag.ts:5 — VITE_VOICE_INPUT_ENABLED=false evaluates as ON~~ — RESOLVED 2026-07-26
**Closed as resolved 2026-07-26**, and widened: `supportPanelFlag` and
`tasksFlag` carried the identical `Boolean(anyNonEmptyString)` bug, so rather
than patching one and deferring the others, all three now delegate to a new
`portal/src/lib/envFlag.ts` (`isEnvFlagEnabled` / `readEnvFlag`).

The falsy set mirrors **pydantic v2's** bool coercion — `""`, `"false"`,
`"0"`, `"off"`, `"no"`, `"n"`, `"f"`, trimmed and case-insensitive — rather
than the narrower `"", "false", "0"` originally suggested, so the FE and the
backend's `bool` settings agree on what "off" looks like. Unrecognized
non-empty values still enable, preserving the old `VITE_X=enabled` behavior.

**Shipping note — this change is behavior-neutral today.** Audited every
configured value before landing it: `.env.local`, `.env.development`, and the
GitHub Actions `production` + `development` environment variables all set
`"true"`; nothing anywhere is set to `"false"`. No flag flips state on deploy.

Tests: new `tests/envFlag.test.ts` (5) and `tests/supportPanelFlag.test.ts`
(7, the module had none), plus falsy/truthy cases appended to the existing
`voiceInputFlag` / `tasksFlag` suites — 32 across the four files. Full portal
suite 1,357 passed; typecheck + lint clean.

---


### [MEDIUM] ~~platform/scripts — backfill coordinates for existing properties~~ — RESOLVED 2026-07-15
**Closed as resolved 2026-07-15.** Built as one shared engine with two entry
points (supersedes the earlier "skip CSV, backfill manually" decision):
- `services/property_geocode.py::backfill_property_coordinates` — fills only
  MISSING coordinates (idempotent), targeted `$set` writes, ~5 req/s
  throttle, waits out a per-company 429 once then skips, dry-run support.
- CSV bulk upload (`routers/properties.py::upload_properties_csv`) now
  schedules a run scoped to the imported ids via FastAPI BackgroundTasks —
  imports gain coordinates minutes after upload with no request latency.
- `scripts/backfill_property_coordinates.py` (`--dry-run`, `--company`) for
  the one-time legacy backfill and as the safety net after interrupted
  background runs.
Tests: `tests/test_property_geocode_backfill.py` (6) +
`test_upload_properties_csv_geocodes_in_background`.
**Remaining operational step:** run the script once against Dev, then once
against production after the next platform promotion, to geocode
pre-2026-07-15 properties.

---


### [LOW] ~~platform/routers/public_maple.py:70 — public endpoint has per-IP but no aggregate spend cap~~ — RESOLVED 2026-07-26 (different approach)
**Closed as resolved 2026-07-26, deliberately NOT via the suggested spend cap.**
Product decision (Simon, 2026-07-26): the public widget is a marketing
surface and prospects using it freely is the *point*. A daily budget ceiling
that silences Maple mid-campaign is the wrong failure mode for lead-gen — the
requirement is "stop bots", not "cap spend". Both suggested fixes (global daily
budget, per-IP daily cap) were dropped on those grounds.

Shipped instead — two layers:

**1. The rate-limit key was broken.** `client_host` came from
`request.client.host`, which behind Render's load balancer is the *proxy's*
address — so the "per-IP" 20/min was one global bucket shared by every visitor
on Earth. A test reproduces it: two distinct visitors, second one 429s.
`services/request_protection.client_ip_for_rate_limit` now resolves the caller
properly, and is deliberately **not** the same as
`audit_service._get_client_ip`: that one takes `X-Forwarded-For[0]`, which is
whatever the *client* sent, so a bot rotating the header would mint itself a
fresh bucket per request. Proxies append, so the real client sits
`trusted_proxy_hops` from the RIGHT (new `trusted_proxy_hops` setting,
default 1 for Render; 0 disables header trust entirely). Falls back to the
unforgeable TCP peer whenever the chain is shorter than expected.
Tests: `tests/test_request_protection_client_ip.py` (12) +
2 endpoint tests (spoofed prefix shares a bucket; distinct visitors don't).

**2. reCAPTCHA v3 bot filtering**, reusing the site key + secret already
provisioned for the marketing contact form. Invisible (score-based, no
challenge), so zero friction for prospects. New `services/recaptcha.py` is the
Python counterpart to `website/functions/lib/recaptcha.js`.

The policy is asymmetric on purpose:
- **Confident bot signal** (low score, wrong action, replayed token, or — once
  enforced — *no token at all*) → 403. A missing token is a bot signal, NOT a
  verification error; failing open on it is exactly how this control ends up
  decorative, since an attacker just omits the field.
- **No verdict obtainable** (Google unreachable, non-JSON body) → allow. A
  third-party outage must never silence the assistant.
- No secret configured → check skipped entirely (local dev).

Threshold is **0.3**, lower than the contact form's 0.5: a free question
deserves less protection than a lead submission, and v3 scores are
probabilistic, so borderline humans should still get answered.

**Rollout is two-phase** — `maple_public_recaptcha_enforced` defaults to
**False**, which verifies a token when present but allows a missing one. The
platform and website deploy independently and visitors may hold a cached
bundle, so flipping this to True before the widget ships would 403 real
people. **Flip it only after the website deploy is live.**

Browser side: `website/lib/recaptchaClient.js` extracted from
`contact-modal/install.js` so both surfaces share one loader with a per-surface
action (`contact` vs `maple_ask`). It exposes two minters, because the surfaces
genuinely differ — `getRecaptchaToken` rejects on failure (contact form fails
CLOSED, shows an error, skips the POST — behavior preserved, caught by its
existing tests) and `getRecaptchaTokenSoft` resolves `''` (widget fails soft,
matching the server's fail-open). Also added a 4s timeout: a blocked script tag
fires neither `onload` nor `onerror`, so the old loader would hang the submit
handler forever.

Tests: `tests/test_recaptcha_service.py` (11), 8 endpoint tests in
`TestPublicMapleRecaptcha`, `website/lib/__tests__/recaptchaClient.test.js`
(11), `website/widget/__tests__/api.test.ts` (3).

**Deploy checklist:** set `RECAPTCHA_V3_SECRET` on Render (same secret the
Firebase function uses) → deploy platform → deploy website → set
`MAPLE_PUBLIC_RECAPTCHA_ENFORCED=true`.

<details>
<summary>Original body (preserved for history)</summary>

Now that public spend is measurable: each guide answer costs ~$0.014 (13.8k-token
prompt), and the only guard is 20 req/min per IP — a single abusive IP can run
~$17/hour, and a small botnet scales that linearly. Metering makes this visible
but nothing bounds it.
**Suggested fix:** Add a global daily budget guard for `feature="maple_public"`
(count/sum today's events before answering; refuse with the canned unavailable
message when over budget), or at minimum a per-IP daily cap alongside the
per-minute one.

</details>

---


### [LOW] ~~platform tooling — bandit not installed, so no automated security scan runs during /code-review (finding #9)~~ — RESOLVED 2026-07-27
**Closed as resolved 2026-07-27.** bandit 1.9.4 installed into `platform/.venv`
and pinned as `bandit>=1.8` in `requirements.txt`. Configuration follows the
same convention as the other two gates — pinned config file, wrapper script,
no ad-hoc flags:
- `platform/bandit.yaml` — excludes `.venv` / `tests` / `scratch`.
- `platform/run_bandit.sh` — mirrors `run_ruff.sh` / `run_mypy.sh` shape.

**`B101` (assert_used) is skipped by deliberate decision.** bandit flags every
`assert` because `python -O` strips them; CLAUDE.md's mypy playbook *mandates*
`assert <x> is not None` for Beanie `.id` narrowing (~106 across
agents/routers/services/models). Those are type-checker directives, not runtime
security checks. The skip is documented in `bandit.yaml` with the caveat that
it is **not** a licence to authorize with asserts — a security-guarding assert
must be an `if ...: raise`.

**bandit is advisory, NOT in the pre-push hook** (unlike ruff/mypy). It is a
syntactic scanner: it catches shell injection, weak crypto, unsafe
deserialization, missing HTTP timeouts, silent excepts. It cannot find logic or
authorization flaws — nothing it does would have caught #349 or the public-Maple
rate-limit key collapse. Treat a clean run as "no classic footguns", not
"secure".

First scan: 19 findings, all LOW severity, zero MEDIUM/HIGH. Six B105
false positives cleared (3 by renaming a loop variable `token` → `word` in
`agents/calculator/text_helpers.py` — they were number words, never
credentials; 3 by `# nosec B105` on Stripe Price lookup keys in
`services/billing/plan_config.py`). **Baseline is now 13 B110 findings**,
tracked in the entry below.


### [LOW] ~~platform tooling — bandit is still not installed (recurring)~~ — RESOLVED 2026-07-27
**Closed as resolved 2026-07-27** — installed and configured; see the resolved
entry above for the config, the deliberate `B101` skip, and the 13-finding
B110 baseline. The 2026-07-26 review's security-scan gap is now closed for
future reviews (that review's own backend findings remain manual-inspection
only). Note the older per-review "bandit not installed; security scan skipped"
lines further up this file are historical records of individual passes, not
open work — they need no action.


### [MEDIUM] ~~portal/src/components/tasks/ConvertTaskDialog.tsx:75 — conversion failure is not announced to assistive tech~~ — RESOLVED 2026-08-12
The error paragraph is rendered conditionally with no `role="alert"` or `aria-live`. A
screen-reader user who triggers Create Estimate and hits a failure (e.g. estimate quota
exhausted) gets no announcement — the button silently re-enables and focus never moves.
The same applies to the "This can take a minute" busy line, which is the only signal that
a long-running request is in flight. Pre-existing, but both messages moved into the footer
in this change.
**Suggested fix:** add `role="alert"` to the error paragraph and `aria-live="polite"` to
the busy paragraph.
**Resolved:** both applied, covered by two tests in `tests/ConvertTaskDialog.test.tsx`
(failure is exposed as an `alert`; the busy line announces politely).


---

## 4 — folded file/function-size entries

Forty-four entries folded into #4 on 2026-08-25. Bodies preserved here
because several carry a specific suggested split worth keeping. Line counts
quoted inside are historical — #4 in the live tracker holds current numbers.

### 4 — extraction history (original body, superseded by the table in the live tracker)

The running log of every extraction done under #4 between 2026-04-26 and
2026-05-23 — `routers/agent_helpers/` splits, the material-service helper
moves, `_handle_update_material`. Preserved because it records *how* each
seam was chosen. Line counts are historical.

<details>
<summary>Original #4 body</summary>

Files over the 800-line HIGH threshold (line counts refreshed 2026-04-26):
- `routers/agents.py` — 1360 lines (2026-05-22 refresh; was 1407
  before the delegate-generic extraction this session, 1642 before the
  delegate-get/update/delete-estimate extractions, 1821 before the
  delegate-create-estimate extraction, 1905 before the estimate-resolver
  extraction, 1977 before the finalize-result extraction, 2203 before
  the estimate-gathering extraction, 2478 before the optional-follow-up
  extraction, 2772 before the pending-estimate-follow-up extraction,
  2917 before 2026-04-26). **53% reduction from the 2026-04-26
  baseline.** Recent extractions landed under `routers/agent_helpers/`:
  - `text_helpers.py` — `is_affirmative_text` / `is_negative_text` (50 lines).
  - `estimate_update.py` — `run_update_estimate` add-items flow (175 lines).
  - `fuzzy_confirmation.py` — `handle_estimate_fuzzy_confirmation` +
    `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY` (180 lines).
  - `pending_estimate_follow_up.py` — landed 2026-05-22 (377 lines).
    Lifted the `_handle_pending_estimate_follow_up` closure (294 lines)
    plus its five property-lookup helpers (`_property_name_of`,
    `_property_address_of`, `_property_label_of`, `_property_full_address_of`,
    `_find_property_by_name_or_address`) out of `orchestrate_agent_endpoint`
    into a module-level helper. Owns `PENDING_ESTIMATE_FOLLOW_UP_KEY` and
    the `ESTIMATE_FOLLOW_UP_STAGE_CONFIRM` / `_SELECT_PROPERTY` constants
    (re-exported from `routers/agents.py` for the existing test imports).
    All 9 return paths now go through a small `_envelope()` helper instead
    of inline 11-key dicts; signature reduced to
    `handle_pending_estimate_follow_up(message, context_payload)`. Tests:
    52 passing in `test_orchestrator_endpoint.py`; `properties_api_get_properties`
    mocks moved from `agents_router` to the helper module via string-form
    `monkeypatch.setattr(...)` (4 sites + 1 contract assertion). The now-dead
    `from routers.properties import fetch_properties as properties_api_get_properties`
    alias was removed from `routers/agents.py`.
  - `optional_follow_up.py` — landed 2026-05-22 (356 lines). Lifted the
    `_handle_pending_optional_follow_up` closure (~195 lines) plus its
    three builders (`_build_optional_follow_up_prompt`,
    `_build_optional_follow_up_update_message`, `_get_optional_follow_up_spec`)
    and the three closure-level constants (`PENDING_OPTIONAL_FOLLOW_UP_KEY`,
    `OPTIONAL_FOLLOW_UP_STAGE_CONFIRM`, `OPTIONAL_FOLLOW_UP_STAGE_COLLECT_VALUE`)
    out of `orchestrate_agent_endpoint`. The closure-level `_get_processor`
    factory (used in 4 sites — only one of which moves into the helper)
    was lifted to module-level in `routers/agents.py` and passed in as a
    `processor_factory: ProcessorFactory` parameter. Five return paths in
    the handler now go through a single `_envelope()` helper. Re-exported
    from `routers/agents.py` so the existing test imports
    (`OPTIONAL_FOLLOW_UP_STAGE_CONFIRM`, etc.) still resolve unchanged.
    Tests: 52 passing in `test_orchestrator_endpoint.py`; no mock-target
    changes needed because no FastAPI-helper aliases were moved.
  - `delegate_generic.py` — landed 2026-05-22 (100 lines). Lifted the
    generic non-Estimate-Agent delegate-and-shape tail (~54 lines) used
    by every agent that isn't routed through one of the Estimate-Agent
    specialized branches (Contact / Property / Labour / Material, plus
    intents Estimate-Agent doesn't claim). Calls
    `processor.process(message, context=...)`, merges the agent-surfaced
    `optional_follow_up` question and stashes a pending follow-up record
    (reusing `get_optional_follow_up_spec` from the existing optional-
    follow-up module), then backfills `completion_ready` /
    `missing_fields` / `accuracy_suggestions` and re-packages as the
    standard 11-key orchestrator envelope. Companion to
    `optional_follow_up.handle_pending_optional_follow_up`, which uses
    the same shape but with slightly different fallback behavior — kept
    separate to avoid parameter explosion. Tests: 52 passing; no mock
    changes needed (`processor.process` is mocked at the agent-instance
    level via `get_<agent>_agent` factory replacements).
  - `delegate_get_estimate.py` — landed 2026-05-22 (145 lines). Lifted
    the `get_estimate` sub-branch (~93 lines) of `_delegate_to_agent`'s
    Estimate Agent block. Pure read path — no Beanie mutations, no
    quota gate, no audit log. The stop-word regex and ObjectId-extraction
    regex moved to module-level constants. Three tests
    (`test_orchestrate_get_estimate_*`) updated with string-form
    `monkeypatch.setattr` on the helper's `estimates_api_get_estimates`.
  - `delegate_estimate_ops.py` — landed 2026-05-22 (226 lines).
    Bundled `delegate_update_estimate` + `delegate_delete_estimate`
    (~82 + ~91 lines of the closure body) since they share the
    `find_estimate_from_context_or_message` resolver, the
    `fuzzy_disclaimer` copy, and the `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY`
    stash record. Closure-only predicates
    (`_should_delegate_update_estimate_to_agent`,
    `_is_work_item_op_message`) are passed in as callables to avoid a
    circular import on `routers/agents.py`. SAFETY GUARDS preserved
    verbatim: update_estimate routes property-link / status-transition
    phrasings straight to the agent BEFORE the fuzzy-resolver; delete
    always requires confirmation regardless of exact vs fuzzy match, and
    refuses the most-recent fallback (destructive callers can't guess).
    All existing delete tests continue to pass via the already-redirected
    resolver mocks from the earlier `estimate_resolver` extraction.
  - `delegate_create_estimate.py` — landed 2026-05-22 (275 lines).
    Lifted the create_estimate sub-branch (~192 lines) of the
    `_delegate_to_agent` closure's Estimate Agent block into a
    module-level helper. Same shape as `estimate_gathering._finalize_gathering`
    — sufficiency check → either enter gathering OR proceed with quota
    gate + estimate generation + audit log + optional follow-up record.
    Closure dependencies passed in: `processor`, `current_user_name`,
    `decoded_token`, and the `_check_estimate_limit_or_refuse` callable
    (latter would be a circular import). Three return paths go through
    a small `_envelope()` helper. Tests: 52 passing; one test
    (`test_orchestrate_endpoint_delegates_to_estimate_agent`) updated to
    also patch `routers.agent_helpers.delegate_create_estimate.prepare_generated_estimate`
    and `save_generated_estimate` via string-form `monkeypatch.setattr`
    (the existing `agents_router` patches stay because the aliases are
    still used in the remaining `_delegate_to_agent` branches).
  - `estimate_resolver.py` — landed 2026-05-22 (119 lines). Lifted the
    `_find_estimate_from_context_or_message` closure (~85 lines) into a
    module-level helper. Resolves the user's target estimate via the
    five-step ladder: active-context → estimate_id code → MongoDB _id
    → fuzzy title match → most-recent fallback. The two regex constants
    are now module-level (`_ESTIMATE_SEARCH_STOP_WORDS`, `_MONGO_OBJECT_ID`).
    Tests: 52 passing; two delete-estimate tests updated to also patch
    `routers.agent_helpers.estimate_resolver.estimates_api_get_estimate{s}`
    via string-form `monkeypatch.setattr` (the existing `agents_router`
    patches stay because the aliases are still used in two other call
    sites inside `_delegate_to_agent`).
  - `finalize_result.py` — landed 2026-05-22 (119 lines). Lifted the
    82-line `_finalize_result` closure body (chat-history append + active-
    entity coreference + suggestions enrichment + conversation persistence)
    into a module-level `finalize_orchestrate_result(...)` helper.
    `_finalize_result` closure remains in `routers/agents.py` as a 9-line
    thin wrapper that calls the helper and wraps the resulting dict in
    `OrchestratorAgentResponse` (the Pydantic response model stays in
    `routers/agents.py` to avoid a circular import). The 5-way entity-key
    scan was extracted into a small `_resolve_entity_reference()`
    private helper inside the new module. All 6 existing call sites are
    untouched — they still call the closure wrapper. Dependencies passed
    in: `delegate_context`, `merged_context`, `user_id`, and the
    `_save_conversation_context` callable. Tests: 52 passing in
    `test_orchestrator_endpoint.py`.
  - `estimate_gathering.py` — landed 2026-05-22 (315 lines). Lifted the
    `_handle_pending_estimate_gathering` closure (236 lines) plus the
    three state-key constants (`ESTIMATE_GATHERING_STATE_KEY`,
    `ESTIMATE_GATHERED_DETAILS_KEY`, `ESTIMATE_NEXT_QUESTION_KEY`) out of
    `orchestrate_agent_endpoint`. The closure captured `message`,
    `decoded_token`, and `current_user_name` from request scope and
    called the module-level `_check_estimate_limit_or_refuse` (a
    circular import if pulled into the helper); these now flow through
    keyword parameters (`decoded_token`, `current_user_name`,
    `estimate_agent`, `check_estimate_limit_or_refuse`). Internal split:
    the per-turn step is the public `handle_pending_estimate_gathering`,
    and the all-details-collected path lives in a private
    `_finalize_gathering` so the main entry stays well under the 50-line
    ceiling. Five return paths go through a single `_envelope()` helper.
    Tests: 75 passing across `test_orchestrator_endpoint.py` +
    `test_estimate_gathering.py`. No mock surgery — no test directly
    exercises the closure-level call path.

  Candidates for the next extraction round:
  - `_finalize_result` and the orchestrate-endpoint epilogue (chat-history
    persistence + suggestion enrichment + response shaping). Still inline
    in `orchestrate_agent_endpoint`.
  - The orchestrate-endpoint's main classification + delegate loop
    (~700 lines after this extraction round). Largest remaining inline
    block in `routers/agents.py`.
- `agents/material/service.py` — 2874 lines (2026-05-22 refresh; was 2875
  pre-extraction this session; doc's earlier "2560" baseline preceded the
  cost/size-guard helpers and accuracy-suggestion code that landed in the
  intervening weeks). `process()` is a mega-switch that inserts a new
  50-line inline handler per intent. ~~Easiest extraction target: the
  `list_material_categories` block~~ landed 2026-04-26 as
  `_handle_list_material_categories()` (44 lines) plus a static
  `_format_material_categories_response()` helper. Follow-up extractions
  landed 2026-04-26: `_handle_create_material`, `_handle_get_material`
  (incl. size-scoped lookup), `_handle_delete_material` (post-resolve
  confirmation flow), and `_handle_list_materials` (count + category-filter
  + name-hint dispatch). `_handle_update_material` landed 2026-05-22:
  the ~246-line inline `update_material` block (multi-turn field-then-value
  state, add-size cost+unit guard, remove-last-size refusal, per-size
  unit-OID resolution, and the final merge/update via
  `_update_material_via_api`) was lifted into a dedicated method that
  reuses `_build_response_envelope` for all 5 return shapes. `process()`
  call site collapses from 246 inline lines to a 14-line kwargs call
  mirroring the `_handle_create_material` / `_handle_delete_material`
  pattern. Verified: 78 tests pass across `test_material_agent.py` +
  `test_material_api.py` + `test_maple_material_size_operations.py`;
  full-project mypy stays at `Success: no issues found in 265 source files`.
  Remaining inline block: the `delete_material` early-confirm shortcut
  that fires before `_resolve_target_material` (small; pre-resolve so it
  can't easily share the post-resolve `_handle_delete_material` signature).

  Pure-helper extraction landed 2026-05-23 in four steps, all into a new `agents/material/text_helpers.py` (375 lines) modeled on `agents/estimate/text_helpers.py`. `agents/material/service.py` dropped from 2,874 → 2,541 lines (**-333, -11.6%**) across the session. Steps:
  - **Step 1**: four leaf-level methods with no `self.*` dependencies (`_is_confirm_text`, `_explicit_intent_from_message`, `_normalize_unit`, `_normalize_size_text`) lifted from instance methods to module-level functions, following the existing pattern set by `_parse_price_range_filter` / `_material_matches_price_filter` / `_format_amount`. 17 callsites rewritten across the file (`self._foo(x)` → `_foo(x)`).
  - **Step 2**: moved Step-1 helpers into a dedicated `agents/material/text_helpers.py` module (76 lines initially).
  - **Step 3**: moved the three pre-existing module-level helpers (`_parse_price_range_filter`, `_material_matches_price_filter`, `_format_amount`) plus the `_PRICE_RANGE_PATTERN` / `_PRICE_RANGE_OP_DIRECTION` constants into `text_helpers.py`. (-75 lines from service.py; 4 internal callsites already module-level so no `self.` rewrites needed.)
  - **Step 4**: moved seven instance methods plus four module-level constants. Methods: `_match_intent_rules`, `_extract_name_from_message`, `_normalize_material_name`, `_parse_cost`, `_has_explicit_cost_field`, `_should_default_cost_to_price`, `_normalize_sizes_field`. Constants: `MATERIAL_ACTION_HINTS`, `NAME_STOPWORDS`, `NAME_LEADING_PREPOSITIONS`, `NAME_TRAILING_NOISE`. 41 `self._foo(x)` → `_foo(x)` callsites rewritten via `replace_all`. (-205 lines from service.py.) All seven methods were transitively pure (chain: `_normalize_sizes_field` uses `_parse_cost` + `_normalize_size_text`; `_extract_name_from_message` uses `_normalize_material_name`; `_has_explicit_cost_field` uses `_parse_cost`); moving them en bloc kept the import dependency one-way (service.py → text_helpers.py).

  The structural win: every helper in `text_helpers.py` is callable and unit-testable without instantiating `MaterialAgent`. Backwards-compat for tests is preserved by the `from agents.material.text_helpers import ...` line at the top of `service.py` — names imported into service.py's namespace are still resolvable via `from agents.material.service import <name>` (used by `tests/test_material_agent.py` for `_material_matches_price_filter` and `_parse_price_range_filter`). Verified: 119 tests pass across `test_material_agent.py` + `test_material_api.py` + `test_maple_material_size_operations.py` + `test_material_response_envelope.py` + `test_audit_service.py`; full-project mypy clean at 275 source files.

  `_handle_update_material` refactor landed 2026-05-23: split 234 → 120 lines (**-49%**) across the orchestration shell, with four new helpers:
  - `_request_update_fields_clarification` (78 lines — bare-field-name selection vs. generic "which fields?" prompt; both terminal)
  - `_check_add_size_guard` (65 lines — refuse add-size when cost or unit missing; returns `Optional[envelope]`)
  - `_check_remove_last_size_refusal` (31 lines — refuse removing the last size; returns `Optional[envelope]`)
  - `_finalize_update_material` (61 lines — merge fields → `_update_material_via_api` → accuracy suggestions → envelope)

  Shell now reads as a linear pipeline: derive state → fields-clarification → add-size guard → remove-size guard → per-size unit-OID resolution → finalize. File-size cost on that single refactor: service.py +121 lines from helper signatures and docstrings — an honest tradeoff where per-function readability wins.

  **`_extract_fields_from_message` and `_build_sizes_from_fields` lifted to `text_helpers.py`** (2026-05-23). Both were pure functions despite being methods — neither used `self.*`. Combined ~278 lines moved out of service.py. Two test callsites updated to use the module-level function (`agent._extract_fields_from_message(...)` → `_extract_fields_from_message(...)` plus an import). text_helpers.py grew to 656 lines (12 pure helpers + 6 constants); service.py dropped from 2,662 → 2,384 (-278).

  **`process()` refactor landed 2026-05-23**: split 457 → **138 lines (-70%)** in two passes via six helper extractions:
  - `_dispatch_intent_to_handler` (147 lines) — the intent-routing mega-switch
  - `_maybe_confirm_pending_delete` (~55 lines) — pending-delete confirmation fast-path
  - `_run_llm_classification` (86 lines) — LLM classify + entity-extraction pipeline; returns ``(parsed, llm_error)``
  - `_apply_post_classify_fallbacks` (~75 lines) — explicit-intent override + name normalization + regex fallback; mutates parsed in place, returns explicit_intent
  - `_apply_pending_intent_fallback` (~66 lines) — pending-intent merge for low-confidence intents; returns `(intent, probability, fields, pending_override_applied)`
  - `_check_pre_dispatch_refusals` (~78 lines) — three pre-dispatch refusal guards (unsupported intent, missing company_id, invalid company_id shape); returns `Optional[envelope]`

  Shell `process()` now reads as a linear pipeline: bulk-delete refusal → context setup → LLM classification → post-classify fallbacks → derive intent/probability/fields → pending-intent fallback → secondary pending-intent merge → pre-dispatch refusals → `_dispatch_intent_to_handler(...)`.

  Session totals for `agents/material/service.py`: **2,874 → 2,568 lines (-306, -10.6%)** across the full session, with `text_helpers.py` at 656 lines (16 pure helpers + 6 constants). The file got bigger than the post-extraction count because each new helper added ~10–15 lines of signature + docstring overhead — function-size is the primary HIGH-issue target so this is a net win even when file-size ticks up. 97 material tests + 22 audit tests pass; full-project mypy clean at 275 source files.

  **`_dispatch_intent_to_handler` refactor landed 2026-05-23**: split 147 → 75 lines (-49%) via one extraction:
  - `_resolve_and_dispatch_target_op` (112 lines) — pending-delete fast-path → `_resolve_target_material` → per-intent handler for the `update_material` / `delete_material` / `get_material` cluster (the only branch that needed target-material resolution). Stashes a pending-update intent on resolve-error and returns the clarification envelope with optional candidate suggestions.

  The dispatcher shell now reads as: `create` branch → `update/delete/get` branch (delegates to `_resolve_and_dispatch_target_op`) → `list_material_categories` branch → fall-through `list_materials`.

  Session totals for `agents/material/service.py`: **2,874 → 2,608 lines (-266, -9.3%)** with `text_helpers.py` at 656 lines (16 pure helpers + 6 constants). Top-N method sizes after this round: `process` (138), `_handle_update_material` (120), `_resolve_and_dispatch_target_op` (112), `_handle_list_materials` (97), `_handle_delete_material` (90), `_run_llm_classification` (86), `_handle_create_material` (85), `_check_pre_dispatch_refusals` (78), `_request_update_fields_clarification` (78), `_handle_list_materials_for_estimate` (76), `_dispatch_intent_to_handler` (75). No method now exceeds 140 lines (was 457 at session start). 97 material tests + 22 audit tests pass; full-project mypy clean at 275 source files.
- `agents/estimate/service.py` — 5685 lines after the 2026-04-26 #80
  refactor. Similar split: prompt-building / inventory fetch / LLM
  extraction / totals calc / CRUD read handlers are each their own concern.
  Cleanest first cut: move the new CRUD methods
  (`_handle_list_estimates`, `_handle_get_estimate`, `_crud_envelope`, plus
  the small parsing helpers) into `agents/estimate/crud.py` as a mixin.
- `agents/labour/service.py` — **1,732 → 1,474 lines (-258, -15%)** across 2026-05-24. Same playbook:
  - **Pure-helper lift to new `agents/labour/text_helpers.py`** (370 lines): 10 leaf-level methods (`_is_confirm_text`, `_match_intent_rules`, `_explicit_intent_from_message`, `_extract_name_from_message`, `_normalize_role_text`, `_parse_cost`, `_normalize_unit`, `_is_bare_rate_reference`, `_match_bare_field_name`, `_extract_fields_from_message`) plus 4 constants (`LABOUR_ACTION_HINTS`, `NAME_STOPWORDS`, `NAME_LEADING_PREPOSITIONS`, `ROLE_TRAILING_NOISE`), class-level `_BARE_FIELD_ALIASES` / `_BARE_RATE_PHRASES`, and the module-level `_format_amount`. Three test sites updated (4 `agent._extract_name_from_message(...)` and 1 `agent._extract_fields_from_message(...)` → module-level + import), plus two `monkeypatch.setattr(LabourAgent, "_extract_*", ...)` rewritten to target the import location.
  - **`process()` dispatch extraction**: lifted the 531-line try-body into `_dispatch_intent_to_handler` (554 lines). `process()` is now **286 lines (-64% from 803 starting point)**.

  40 labour tests pass.

- `agents/equipment/service.py` — **1,343 → 1,151 lines (-192, -14%)** across 2026-05-24. Same playbook:
  - **Pure-helper lift to new `agents/equipment/text_helpers.py`** (284 lines): 8 leaf-level methods (`_is_confirm_text`, `_match_intent_rules`, `_explicit_intent_from_message`, `_extract_name_from_message`, `_normalize_equipment_name`, `_parse_cost`, `_normalize_unit`, `_extract_fields_from_message`) plus 4 constants (`EQUIPMENT_ACTION_HINTS`, `NAME_STOPWORDS`, `NAME_LEADING_PREPOSITIONS`, `NAME_TRAILING_NOISE`) and `_format_amount`. Two test sites updated (1 each of `agent._extract_name_from_message(...)` and `agent._extract_fields_from_message(...)` → module-level).
  - **`process()` dispatch extraction**: lifted the 382-line try-body into `_dispatch_intent_to_handler` (405 lines). `process()` is now **264 lines (-58% from 632 starting point)**.

  20 equipment tests pass.

- `agents/contact/service.py` — **2,412 → 1,928 lines (-484, -20%)** across 2026-05-24. Same playbook as property/material:
  - **Pure-helper lift to new `agents/contact/text_helpers.py`** (593 lines): 17 leaf-level methods moved out of `ContactAgent` as module-level functions, plus 6 constants (`CONTACT_ACTION_HINTS`, `SUPPORTED_CONTACT_ROLES`, `CONTACT_ROLE_ALIASES`, `CONTACT_ENUM_FIELD_OPTIONS`, `_BARE_FIELD_ALIASES`) and the module-level enum-extraction helper (`_extract_contact_enum_field_options`). Migrated helpers: `_is_confirm_text`, `_match_intent_rules`, `_explicit_intent_from_message`, `_extract_name_from_message`, `_split_name_parts`, `_normalize_phone_token`, `_normalize_postal_zip_token`, `_normalize_country_token`, `_normalize_prov_state_token`, `_normalize_role_token`, `_field_name_variants`, `_extract_value_like_phrase`, `_normalize_enum_field_value`, `_detect_enum_help_field`, `_infer_single_missing_field_value`, `_match_bare_field_name`, `_extract_fields_from_message`. Callsites rewritten via `sed`. Three test sites updated: 10 `agent._extract_name_from_message(...)` → module-level, 10 `agent._extract_fields_from_message(...)` → module-level, 7 `agent._normalize_phone_token(...)` → module-level (the test's `agent = ContactAgent(use_llm=False)` line still works but isn't needed), and two `monkeypatch.setattr(ContactAgent, "_extract_*", ...)` rewritten to target the import location in `agents.contact.service`. (Initial deletion was too aggressive — also stripped the 4 module constants `CONTACT_AGENT_LABEL` / `PENDING_INTENTS_CONTEXT_KEY` / `ACTIVE_CONTACT_ID_CONTEXT_KEY` / `ACTIVE_CONTACT_NAME_CONTEXT_KEY`; restored in a follow-up edit.)
  - **`process()` dispatch extraction**: lifted the 641-line try-body dispatch into `_dispatch_intent_to_handler` (665 lines). `process()` is now **407 lines (-61% from 1,040 starting point)**. Also lifted the inline `_response` closure to a module-level `_finalize_response_envelope` (16 callsites + 2 `response_wrapper=` references rewritten via `sed`).

  82 contact tests pass; full-project mypy clean at 277 source files. The remaining `process()` (407 lines) still has post-classify-fallbacks, pending-intent merges, enum-help-field early-return, and pre-dispatch refusals all inline — natural follow-up extractions matching the material/property phase pattern. `_dispatch_intent_to_handler` (665 lines) is itself well over the ceiling — could split the create-contact / resolve-then-dispatch / list-contacts branches further.

  **`_dispatch_intent_to_handler` split landed 2026-05-25**: the 382-line update/delete/get cluster lifted into `_resolve_and_dispatch_target_op` following the property playbook (line-for-line port of property's helper, minus the property-specific `contact_name` / `owner_name` params; the contact dispatcher's `active_contact_id` param turned out to be unused inside the body and was left untouched on the original method's signature for minimum-touch). `_dispatch_intent_to_handler` dropped from 665 → 299 lines (-55%); new helper at 412 lines (vs. property's 468). Net file size: 1,928 → 1,974 lines (+46 from new method header + the `return None` tail; the size cost is an honest tradeoff — per-function readability is the HIGH-issue target, not file-size minimization). Two `pending_record: Dict[str, Any] = {...}` annotations added to the lifted scope to keep mypy happy (the cluster's narrowest dict literal mixed with a downstream `pending_record["confirm_delete"] = False` mutation tripped `Collection[str]` inference). 99 contact tests pass across `test_contact_agent.py` + `test_contact_api.py` + `test_contact_model.py` + `test_cross_resource_envelope_contact.py`; full-project mypy clean at 279 source files. Natural next splits target the new helper's internal branches (delete-confirm fast-path / fuzzy-confirmation / get / update / delete) — same per-intent split that property's helper still needs.

  **`_handle_update_target_contact` extraction landed 2026-05-25**: the 152-line `if intent == "update_contact":` branch lifted out of `_resolve_and_dispatch_target_op` into a dedicated `_handle_update_target_contact` method. Covers the three sub-flows the branch already had inline: (a) multi-turn ``awaiting_value_for`` re-entry (the prior turn stashed a field-name → this turn supplies the value), (b) bare-field-name selection + ``awaiting_value_for`` stash + ``no-fields`` clarification stash, and (c) the field-merge → Google address enrichment → ``_update_contact_via_api`` → accuracy-suggestions pipeline. `_resolve_and_dispatch_target_op` dropped from 412 → 276 lines (-33%); new helper at 177 lines. File: 1,974 → 2,015 lines (+41). 99 contact tests pass; full-project mypy clean at 279 source files.

  **`_handle_delete_target_contact` extraction landed 2026-05-25**: the 79-line implicit-fall-through delete branch (reachable only when ``intent == "delete_contact"`` after update / get returned) lifted into its own method. Two-step shape preserved: first hit stashes ``pending_delete_*`` + the active-contact context keys and returns the confirmation envelope; second hit (with ``parsed.confirm_delete`` truthy or ``_is_confirm_text(message)``) hits ``_delete_contact_via_api`` and clears pending state. Signature deliberately narrower than `_handle_update_target_contact` — drops the unused ``fields`` / ``company_id`` / ``pending_override_applied`` params (delete uses ``target_contact.id`` and never enriches address fields). `_resolve_and_dispatch_target_op` dropped from 276 → 210 lines (-24%); new helper at 102 lines. File: 2,015 → 2,051 lines (+36). 99 contact tests pass; full-project mypy clean at 279 source files.

  **`_handle_create_contact` extraction landed 2026-05-25**: the 160-line `if intent == "create_contact":` branch lifted out of `_dispatch_intent_to_handler` into a dedicated `_handle_create_contact` method. Covers the three sub-flows the branch already had inline: (a) name-token reconciliation between ``parsed`` and the active pending intent's first/last name slots (the "name is X" with a prior pending first-name case is preserved), (b) single-missing-field inference from the prior turn's pending ``missing_fields`` list (only fires when exactly one required field was missing), and (c) Google address enrichment → required-field check → either stash-and-ask-for-missing or ``_create_contact_via_api`` → accuracy-suggestions + optional post-create follow-up question for any of ``phone`` / ``email`` / ``street`` not supplied. Cleaned up the stale ``# noqa - re-binding ... (line 1682)`` comment on the `pending_missing_fields` initializer — the prior-line reference was already wrong after the earlier extractions, and the variable is now scoped to the helper so no shadowing exists. Replaced with a clean ``pending_missing_fields: List[str] = []`` annotation. `_dispatch_intent_to_handler` dropped from 299 → 153 lines (-49%); new helper at 188 lines. File: 2,051 → 2,093 lines (+42).

  **`_handle_list_contacts` extraction landed 2026-05-25**: the 61-line list-contacts fall-through (name-hint normalization via ``parsed.full_name`` → ``first_name + last_name``; count-query / generic-words filtering against the inline ``_GENERIC_WORDS`` set; ``find_contacts_by_name`` vs. full-catalog ``_list_contacts_via_api`` dispatch; response shaping for count / empty / list cases) lifted out of `_dispatch_intent_to_handler` into a dedicated `_handle_list_contacts` method. Body moved verbatim (no dedent needed — already at method-body indent). Also fixed a pre-existing missing blank line between `_dispatch_intent_to_handler` and `process` left over from the first extraction round. `_dispatch_intent_to_handler` dropped from 153 → 101 lines (-34%); new helper at 82 lines. File: 2,093 → 2,123 lines (+30).

  Session totals for `agents/contact/service.py`: 1,928 → 2,123 lines (+195 from sig+docstring overhead across the five new methods). Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (210), `_handle_create_contact` (188), `_handle_update_target_contact` (177), `_handle_delete_target_contact` (102), `_dispatch_intent_to_handler` (101), `_handle_list_contacts` (82), `_classify_with_llm` (72), `_list_contacts_at_property` (71). No method now exceeds 210 lines (was 665 at session start) — every method reduced by at least 51%, the worst single function reduced by 68%. `_dispatch_intent_to_handler` is now a clean three-branch router: `create_contact` → helper, `update/delete/get` → resolve-then-dispatch helper, cross-resource filter (~34 lines, the only branch still inline since both sub-shapes are already in `_list_contacts_at_property` / `_list_contacts_for_estimate`), then `list_contacts` → helper. 99 contact tests pass; full-project mypy clean at 279 source files.

- `agents/property/service.py` — **2,418 → 2,027 lines (-391, -16.2%)** across 2026-05-24. Two-pronged refactor following the material-agent playbook:
  - **Pure-helper lift to new `agents/property/text_helpers.py`** (572 lines): 19 leaf-level methods moved out of `PropertyAgent` as module-level functions, plus 3 constants (`PROPERTY_ACTION_HINTS`, `_BARE_FIELD_ALIASES`, `_LABEL_PATTERNS`). Migrated helpers: `_is_confirm_text`, `_explicit_intent_from_message`, `_match_intent_rules`, `_sanitize_property_reference`, `_extract_name_from_message`, `_extract_contact_name_from_message`, `_extract_explicit_property_name_from_message`, `_extract_owner_name_from_message`, `_normalize_postal_zip_token`, `_normalize_country_token`, `_normalize_prov_state_token`, `_match_bare_field_name`, `_extract_label_fields`, `_try_canadian_full_address`, `_try_us_zip_address`, `_try_chunked_address`, `_try_partial_address`, `_try_at_prefix_canadian_address`, `_extract_fields_from_message`. 27 `self._foo(x)` callsites rewritten via `sed`. Three test sites updated (`agent._extract_fields_from_message(...)` → `_extract_fields_from_message(...)` plus an import) and one `monkeypatch.setattr(PropertyAgent, "_extract_name_from_message", ...)` rewritten to target the import location in `agents.property.service`.
  - **`process()` refactor**: split 936 → 750 lines (-20%) via three helper extractions matching the material pattern: `_run_llm_classification` (88 lines — LLM classify + entity-extraction; returns `(parsed, llm_error)`), `_apply_post_classify_fallbacks` (77 lines — explicit-intent override + name normalization + regex fallback; returns explicit_intent), `_apply_pending_intent_fallback` (91 lines — pending-intent merge for low-confidence intents; returns 6-tuple `(intent, probability, fields, contact_name, owner_name, pending_override_applied)`), `_check_pre_dispatch_refusals` (~50 lines — unsupported-intent + missing-company-id guards).

  58 property tests pass; full-project mypy clean at 276 source files.

  **`process()` dispatch extraction landed 2026-05-24**: lifted the 610-line try-body intent dispatch into `_dispatch_intent_to_handler` (636 lines initially). `process()` is now **150 lines (-84% from 936 starting point)** and reads as a linear pipeline: bulk-delete refusal → context setup → LLM classification → post-classify fallbacks → derive intent/probability/fields → pending-intent fallback → secondary pending-intent merge → active-property fallback → pre-dispatch refusals → `_dispatch_intent_to_handler(...)`. Also lifted the inline `_response` closure to a module-level `_finalize_response_envelope` (20 callsites rewritten via `sed`) so the dispatch helper has independent access to the envelope-defaults logic.

  **`_dispatch_intent_to_handler` split landed 2026-05-24**: the 438-line update/delete/get cluster lifted into `_resolve_and_dispatch_target_op`. `_dispatch_intent_to_handler` dropped from 636 → 216 lines (-66%). The new helper handles pending-delete confirmation, fuzzy-match resolve flow with stash-on-resolve-error, and the per-intent (update/delete/get) handler dispatch. Returns `Optional[Dict[str, Any]]` so the caller can fall through to the create / list / list-by-cross-resource branches when the intent isn't a resolved-target op. (The first run of the extraction script had a dedent bug — the cluster body was already at the right method-body indent and didn't need stripping. Reverted via `awk` to add the 4 spaces back, then fixed a fresh `Dict[str, Any]` annotation gap on `pending_record` exposed by mypy.)

  Updated `agents/property/service.py` line count: 2,418 → 2,123 (-295, -12.2%). Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (468), `_dispatch_intent_to_handler` (216), `process` (150), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77), `_classify_with_llm` (69). Two methods still well over the 50-line ceiling — natural next splits target the create-property branch (~90 lines) and the resolve-then-dispatch internals (delete-confirm path, fuzzy-match stash, per-intent handlers).

  **`_dispatch_intent_to_handler` create-property extraction landed 2026-05-28**: lifted the 92-line `if intent == "create_property":` branch into a dedicated `_handle_create_property` helper (107 lines). The dispatcher now delegates with an 11-line call site, leaving only the resolve-then-dispatch passthrough, the cross-resource filter shortcut, and the `list_properties` fall-through inline. `_dispatch_intent_to_handler` dropped from 216 → 138 lines (-36%). The new helper accepts the create-flow-specific subset of parameters (no `intent`, `active_pending_intent`, `contact_name`, or `owner_name`) and hardcodes `intent = "create_property"` internally. File grew slightly (2,123 → 2,152, +29) due to method-signature/docstring boilerplate, but per-method sizes are now more focused. Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (468), `process` (150), `_dispatch_intent_to_handler` (138), `_handle_create_property` (107), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77). Verified: 46 tests pass in `test_property_agent.py`; 52 pass in `test_orchestrator_endpoint.py`; mypy clean on `agents/property/`. The new helper is still over the 50-line ceiling — a future sub-split could separate the missing-fields stash branch (28 lines) from the post-create assembly (~70 lines), but each is one coherent code path so the value is marginal.

  **`_resolve_and_dispatch_target_op` per-intent handler split landed 2026-05-28**: lifted the three per-intent handlers out of the 468-line resolve-then-dispatch parent: `_handle_get_property` (43 lines), `_handle_update_property` (244 lines), `_handle_delete_property` (93 lines). The parent now reads as a linear pipeline — pending-delete early-exit → `_resolve_target_property(...)` → fuzzy-match confirmation stash → per-intent delegate — and drops from **468 → 169 lines (-64%)**. `_handle_get_property` is the only new helper under the 50-line ceiling; `_handle_update_property` is now the largest method in the file (244 lines) but is isolated, and its natural future split is the awaiting-value/bare-field-name clarification stash (~110 lines) vs. the merge-and-update body (~130 lines). All three new helpers hardcode `intent = "<op>"` internally rather than taking it as a parameter. File grew 2,152 → 2,233 (+81) for method-signature boilerplate. Top-N method sizes after this round: `_handle_update_property` (244), `_resolve_and_dispatch_target_op` (169), `process` (150), `_dispatch_intent_to_handler` (138), `_handle_create_property` (107), `_handle_delete_property` (93), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77), `_classify_with_llm` (69). Verified: 46 tests pass in `test_property_agent.py`; 52 pass in `test_orchestrator_endpoint.py`; mypy clean on `agents/property/`.

  **`_handle_update_property` sub-block split landed 2026-05-28**: the 244-line update handler split into two sub-helpers along its natural seam — the `if not fields and not contact_name:` clarification stash → `_maybe_stash_update_clarification` (116 lines, returns `Optional[Dict[str, Any]]` so the parent falls through on `None`), and the merge-and-update body → `_merge_and_update_property` (139 lines, async; owns the existing-payload merge, address enrichment, contact lookup/disambiguation, update API call, and response assembly). `_handle_update_property` is now **62 lines** (-75%): the awaiting-value unwrap (~12 lines) plus two delegate calls. The clarification-stash helper is sync (no awaits) — kept as a method rather than a module-level function because it touches `self._upsert_pending_intent` / `self._persist_pending_intents`. File grew 2,233 → 2,306 (+73) for method-signature boilerplate. Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (169), `process` (150), `_merge_and_update_property` (139), `_dispatch_intent_to_handler` (138), `_maybe_stash_update_clarification` (116), `_handle_create_property` (107), `_handle_delete_property` (93), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77), `_classify_with_llm` (69), `_handle_update_property` (62). Verified: 98 tests pass across `test_property_agent.py` + `test_orchestrator_endpoint.py`; mypy clean on `agents/property/`.

  **Property-agent chain paused 2026-05-28** — diminishing returns. The largest remaining method is `_resolve_and_dispatch_target_op` (169 lines), a linear pipeline whose sub-steps don't decompose cleanly without obscuring the flow. Pivoting to `agents/estimate/service.py` (#235), the largest file in the repo.

- `agents/estimate/service.py` — **2,600 → 2,451 → 2,344 lines (-256, -9.8% total)** across two 2026-05-28 passes:
  - Calc-cluster lift to new `agents/estimate/calc_helpers.py` (127 lines, 5 module-level functions: `get_material_default_price`, `get_material_default_cost`, `merge_duplicate_line_items`, `merge_resolved_material_items`, `merge_resolved_labour_items`). The cluster had eight methods total — three (`_calculate_material_cost`, `_estimate_labour_hours`, `_calculate_total_estimate`) were dead (zero call sites across `platform/`, `tests/`) and deleted outright. The remaining five didn't read `self` or call sibling methods, so they lifted cleanly as module-level functions. Six `self._foo(...)` call sites rewritten. Verified: 112 tests pass in `test_estimate_agent.py`.
  - Gathering sync-helpers lift to existing `agents/estimate/text_helpers.py` (643 → 759 lines, +116). The 2026-05-11 remaining-targets list called this the "gathering/sufficiency cluster (~200 lines)", but on inspection the cluster split into two surfaces: the two async LLM methods (`assess_sufficiency`, `extract_detail_from_reply`) are public — called by `routers/agent_helpers/delegate_create_estimate.py` and `routers/agent_helpers/estimate_gathering.py` — so they stay on the agent. The 5 sync helpers (`_field_name_variants`, `_normalize_enum_value`, `_extract_value_like_phrase`, `_detect_enum_help_field`, `_infer_single_pending_field_value`) are call-only-from-`service.py` pure functions that directly parallel the same names already lifted to `agents/contact/text_helpers.py` — matched the contact pattern and appended them as module-level functions. Five `self._foo(...)` call sites rewritten via `sed`. `text_helpers.py` grew to 759 lines, still under the 800-line HIGH threshold. Stale doc note from 2026-05-11 corrected: LLM error / JSON parsing helpers (`format_llm_error`, `build_json_parse_diagnostic`, `strip_json_comments`) were **already lifted** to `llm_helpers.py` in the same 2026-05-11 pass — that list entry was outdated, no work needed there.
  - Combined verification: 135 tests pass across `test_estimate_agent.py` + `test_estimate_gathering.py`; mypy clean on `agents/estimate/` (14 source files).
  - Extraction normalization cluster lifted to new `agents/estimate/extraction_helpers.py` (342 lines, 7 module-level functions: `normalize_extracted_estimate`, `has_meaningful_value`, `merge_job_item_payloads`, `merge_with_pending_estimate`, `build_optional_follow_up`, `collect_missing_required_fields`, `build_clarifying_question`). All 7 are pure data transformations — none touch `self` state, only intra-cluster method calls (which become bare function calls in the module). The module imports `_normalize_enum_value` from `text_helpers` and `ExtractedEstimate` from `schemas`. Five `self._foo(...)` call sites in `service.py` rewritten via `sed`. No external callers (grep across `platform/`, `tests/`). Verified: 135 tests pass; mypy clean (now 15 source files in `agents/estimate/`).
  - `agents/estimate/service.py` net session reduction: **2,600 → 2,055 lines (-545, -21.0%)** across the calc, gathering-sync, and extraction-normalization passes.
  - LangChain research/architect pipeline cluster lifted to new `agents/estimate/llm_pipeline.py` as a `LlmPipelineMixin` (1,089 lines). 17 methods moved as-is: `_build_research_input`, `_collect_research_sources`, `_normalize_research_result`, `_decompose_requirement`, `_step1_architect`, `_step2_vector_retrieval`, `_step3_research_for_scope`, `_reuse_past_work_item`, `_step2_and_3_for_scope`, `_run_pipeline`, `_run_react_loop`, `_run_estimate_research`, `_estimate_has_no_line_items`, `_build_estimate_from_research`, `_extract_estimate_with_llm`, `_fallback_accuracy_suggestions`, `_generate_accuracy_suggestions`. **Mixin pattern (not module-level)** because tests + `agents/estimate/tools.py` call these as `agent._step1_architect(...)` / `monkeypatch.setattr(EstimateAgent, "_step1_architect", ...)` — preserving the agent-method surface keeps all callers unchanged. `EstimateAgent` inheritance is now: `(CatalogMatchingMixin, CrudParsingMixin, WorkItemHandlersMixin, WorkItemFieldHandlersMixin, CrudHandlersMixin, LlmPipelineMixin)`.
  - Test patches updated: `monkeypatch.setattr(estimate_service, "search_similar_work_items", ...)` (2 sites) rewritten to target the new module (`estimate_llm_pipeline`). The `ChatOpenAI` patches at module level were unaffected because the mixin doesn't import `ChatOpenAI` directly — `self.llm` is set on the agent.
  - TYPE_CHECKING stub block added inside `LlmPipelineMixin` declaring the host-instance attrs the mixin touches: `llm`, `architect_llm`, `responses_client`, `architect_prompt`, `research_prompt`, `web_research_enabled`, `vector_search_enabled`, `react_max_iterations`, plus `_fill_prices_and_calculate_totals` (the only sibling method called that lives outside the mixin chain). Matches the established pattern in `CrudHandlersMixin` and `WorkItemHandlersMixin`.
  - **`agents/estimate/service.py` final session size: 2,055 → 1,089 lines (-966, -47% from this final pass; -1,511 total from session start of 2,600, -58.1%).** Cluster split out cleanly without disturbing any of the in-place CRUD / process / response-shaping logic.
  - Verified: 144 tests pass across `test_estimate_agent.py` + `test_estimate_gathering.py` + `test_estimate_tools.py`; mypy clean across all 16 source files in `agents/estimate/`. 3 pre-existing failures in `test_agents_api.py::test_*_estimate_*_requires_confirmation` (event-loop / "Future attached to a different loop" Beanie cursor issue) reproduce on HEAD without these changes — unrelated to this refactor.
  - **`_fetch_inventory_items` split landed 2026-05-29**: the 106-line method split into a thin orchestrator (18 lines) plus two sub-helpers — `_fetch_materials_inventory` (56 lines) and `_fetch_labour_inventory` (35 lines). The orchestrator wraps both sub-calls in a single try/except (the only Beanie failure mode worth catching), defaulting to module-level `_empty_materials_inventory()` / `_empty_labour_inventory()` sentinels on error. The `_size_price` inner closure was promoted to a module-level `_size_unit_price(size)` helper (5 lines) and is now reused inside `_fetch_materials_inventory` (was duplicated inline twice in the original). Both sub-helpers raise on error — only the orchestrator catches — which is honest about the failure mode. All 15 `monkeypatch.setattr(EstimateAgent, "_fetch_inventory_items", fake)` test sites unaffected because they replace the orchestrator wholesale (sub-helpers aren't called when patched). `_fetch_materials_inventory` is 56 lines — just over the 50-line ceiling, kept as one coherent fetch+build flow. Verified: 144 tests pass; mypy clean. After this round, `_fetch_inventory_items` is no longer on the 2026-05-11 list. `agents/estimate/service.py` final size: 1,089 → 1,118 lines (+29 for signature/docstring boilerplate, but the largest method shrunk from 106 → 56).
  - **Session-wide summary on `agents/estimate/service.py`: 2,600 → 1,118 lines (-1,482, -57%).** Remaining over-50-line methods: `process` (333 lines — main entry orchestrator, the natural next target), `_fill_prices_and_calculate_totals` (224 lines — already on the 2026-05-11 list as "single function that should split into helper steps"), `_fetch_materials_inventory` (56 lines, just over). Top-of-funnel `process()` is the last big chunk left.

- `agents/orchestrator/service.py` — 1990 lines (file-level). `_classify_with_rules` reduced 2026-05-22/23 from 238 → 76 lines via five helper extractions:
  - `_classify_specific_phrasings` (52 lines — link/work-item/EST-code-total overrides)
  - `_classify_via_action_domain` (47 lines — standard ACTION+DOMAIN orchestration shell)
  - `_resolve_action_and_domain` (22 lines — ACTION + DOMAIN match with plural-aware get→list override)
  - `_apply_add_set_update_override` (36 lines — "add/set a <field> to <entity>" create→update rewrite)
  - `_ambiguity_fallback` (36 lines — three ambiguity clarification shapes)

  All five new helpers are under the 50-line ceiling. Main shell now reads as a linear sequence of `if (result := stage(...)) is not None: return result` short-circuits. Only the shell itself (76 lines, mostly comments) and `_classify_specific_phrasings` (52 lines) remain over the soft ceiling. `process()` still duplicates the same short-circuit patterns (see MEDIUM #12). Verified: 279 tests pass across `test_orchestrator_intents.py` + `test_orchestrator_endpoint.py` + `test_orchestrator_bare_entity_helpers.py`; mypy clean on `agents/orchestrator/`.

No function in this repo should exceed 50 lines. Grep for long bodies with
a line-count tool after each refactor pass.

Specific instances:
- #18 — `agents/estimate/service.py` at 5,098 lines (2026-04-22 refresh).
- #94 — New material handlers all exceed the 50-line ceiling.
- #125 — `agents/orchestrator/service.py` at 1,358 lines (file-size note).
- #137 — `NewEstimateWithActivityPage.tsx` extractions partial (1,733 lines).
- #165 — `_list_properties_by_cross_resource` still 88 lines after #155.
- #166 — `_list_contacts_for_estimate` still 91 lines after #156.
- #167 — `_resolve_cross_resource_properties` at 62 lines (accepted).
- #235 — `agents/estimate/service.py` at 6,066 lines (largest file in repo).
- #236 — `portal/src/pages/SettingsPage.tsx` is 2,496 lines.
- #237 — `agents/material/service.py` at 2,745 lines (file-level).
- #238 — `routers/agents.py` at 2,640 lines.
- #240 — `agents/property/service.py` at 2,386 lines.
- #241 — `agents/contact/service.py` at 2,378 lines.
- #242 — `NewEstimateWithActivityPage.tsx` at 1,814 lines.
- #243 — `agents/orchestrator/service.py` at 1,970 lines.
- #244 — `agents/labour/service.py` at 1,732 lines.
- #245 — `portal/src/pages/MaterialsPage.tsx` at 1,421 lines.
- #246 — `agents/equipment/service.py` at 1,343 lines.
- #247 — `portal/src/pages/ContactsPage.tsx` at 1,324 lines.
- #248 — `portal/src/pages/PeoplePage.tsx` at 1,024 lines.
- #249 — `portal/src/pages/PropertiesPage.tsx` at 878 lines.
- #250 — `platform/routers/auth.py` at 892 lines.
- #257 — `routers/agents.py` grew to 2,810 lines post-gate-helpers PR.
- #260 — `routers/estimates.py` over the 800-line soft cap (1,294 lines).

**Absorbed:** #18, #94, #125, #137, #165, #166, #167, #235, #236, #237, #238, #240, #241, #242, #243, #244, #245, #246, #247, #248, #249, #250, #257, #260 — specific file/function-size instances surfaced in later review passes. See `## Closed` for original bodies.

</details>

---

### 163. [MEDIUM] Wave 3 file growth — three large agent files grew further
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


### 229. [LOW] Submit handler is ~60 lines after this change
**File**: [website/public/contact-modal.js:316-386](../../website/public/contact-modal.js)
**Severity**: LOW

The inline `form.addEventListener('submit', async (e) => { … })`
body is long enough to be hard to scan. Pre-existing issue; this
change adds one line so it's not regressing meaningfully.

Fix: extract the body into a named function (`handleSubmit`) in a
follow-up if/when the file is touched again. No action needed for
this commit.

---


### 276. [MEDIUM] Long test functions in #7 backfill tests
Five test functions across two files exceed the 50-line guideline:

- `test_generate_google_doc_router.py:128` — `test_generate_google_doc_batches_contact_fetch` (118 lines)
- `test_generate_google_doc_router.py:252` — `test_generate_google_doc_zero_contacts_succeeds` (86 lines)
- `test_generate_google_doc_router.py:404` — `test_fetch_estimate_doc_context_issues_single_batched_contact_find` (78 lines)
- `test_feedback_anonymous.py:133` — `test_feedback_registered_user_uses_real_name` (54 lines)
- `test_feedback_anonymous.py:189` — `test_feedback_blank_first_last_name_falls_back_to_unknown_user` (56 lines)

Body bulk is fixture setup (multi-contact estimates for the doc tests,
firebase-token + user-record scaffolding for the feedback tests), not
assertion logic. Hard to scan.

Fix: extract the multi-contact estimate scaffold into a `pytest.fixture`
in a module-level setup so the assertion is the bulk of the test body;
parameterize contact-count for the two related variants in
`test_generate_google_doc_router.py`. Could also fold under #4 as
function-size instances.


### 281. [MEDIUM] `assert_token_quota` is ~77 lines (4 sequential 402 gates)

`platform/services/llm/quota.py:assert_token_quota` crossed the 50-line HIGH
threshold after the hard-cap branch landed. The function is still cohesive — a
flat top-to-bottom policy of hard-cap → over-quota+no-card → over-quota+no-ack
→ pass — and splitting now would fragment a policy that benefits from being
read in one place.

Fix when it grows another gate: extract a `_raise_quota_402(code, message)`
helper to collapse the four near-identical `raise HTTPException(...)` blocks.
Not worth doing today.


### 284. [LOW] `compute_analytics` is ~115 lines

`platform/routers/estimates.py:507` — pre-existing length, not introduced by
the 2026-05-20 pipeline-window/updated_at change. The four-way
`asyncio.gather` plus per-bucket reshape (headline → by_division → by_status)
keeps everything in one function. The `/code-review` HIGH rule flags >50
lines, so worth splitting next time the function grows further.

Fix: extract `_compute_headline`, `_compute_by_division`, `_compute_by_status`
helpers. Defer until the next behavioural change in this function — splitting
purely for length without a behavioural driver is churn.

---


### 296. [MEDIUM] `install()` in `contact-modal.js` is ~120 lines
**Where:** `website/public/contact-modal.js:240-360`.

**Why:** Mixes DOM creation, ref binding, captcha setup, open/close handlers, and submit logic. Hard to follow at a glance.

**Suggested fix:** Split into `renderModal()`, `bindOpenClose(refs)`, `bindSubmit(refs, captcha)`. Cleanest after the file is moved out of `public/` (see #293), since the helpers can then be unit-tested with injected refs.


### 310. [MEDIUM] `work_item_field_handlers.py` is 1286 lines
**Where:** `agents/estimate/work_item_field_handlers.py`

**Issue:** Above the 800-line threshold. Single mixin with 12 handlers following the same pattern.

**Fix:** Addressed naturally when #305 extracts shared boilerplate — the file should drop below 800 lines after the helper extraction.


### 311. [HIGH] `SettingsPage.tsx` is 2,541 lines
**Where:** `portal/src/pages/SettingsPage.tsx`

**Issue:** Well above the 800-line threshold. The team-invitation flow, seat-count display, billing gate logic, and numerous unrelated settings panels all live in one component.

**Fix:** Extract the seat overage gate logic into a `useSeatsOverageGate` hook, the invitation form into an `InviteTeamSection` sub-component, and the billing display rows into `BillingUsageSection`. This PR touched this file — the debt is growing.


### 327. [HIGH] `agents/estimate/crud_handlers.py` grew ~250 lines to 2,309
Pre-existing giant (under the #4 file-size theme) but this change materially
worsened it: the mixin now holds link/notes/description detectors + handlers,
bare-title extraction, the shared resolver, and the get/update dispatchers.
Next touch, split the estimate-level field-edit sub-ops (description / notes /
property-link detectors + handlers) into an `estimate_field_handlers.py` mixin,
mirroring the existing `work_item_field_handlers.py` precedent from §1.5.


### 343. [LOW] `bootstrap_company_materials` body is ~67 lines (over the 50-line heuristic)
Added 2026-06-07. The 8-line auto-create wiring pushed
`services/material_bootstrap.py::bootstrap_company_materials` past the 50-line
guideline, though the bulk is docstring + comments and the new logic was already
extracted into `_ensure_referenced_categories_and_units`. Cosmetic only. Fix if
the function grows further: extract the category/unit pre-load and the
group-and-insert loop into named helpers.


### 345. [MEDIUM] `crud_handlers.py` (2,495) and `work_item_field_handlers.py` (1,270) exceed the 800-line guideline
Added 2026-06-09. Extends [#327](#327-agentsestimatecrud_handlerspy-grew-250-lines-to-2309)
— `crud_handlers.py` was 2,309 there and is now 2,495 after this change. The
estimate CRUD mixin keeps accreting; `work_item_field_handlers.py` is also over
at 1,270. Pre-existing, not introduced by this refactor (the change is net
behavior-neutral plumbing), but worsened. Fix (large, defer until the area is
actively reworked): split the estimate handler mixins by sub-domain —
list/analytics vs. get/update vs. work-items — into separate modules.


### 347. [MEDIUM] `crud_handlers.py` now 2,724 lines — extends #345
Added 2026-06-11. Extends [#345](#345-medium-crud_handlerspy-2495-and-work_item_field_handlerspy-1270-exceed-the-800-line-guideline)
— 2,495 there, 2,724 after the status-transition enforcement work (+229 across
the two 2026-06-11 changes). Same fix, same deferral: split the estimate
handler mixins by sub-domain when the area is next actively reworked. The new
`_refuse_illegal_status_transition` / `_authorize_status_transition` /
`_load_estimate_for_update`-guard cluster is a ready-made seed for a
`status_policy.py` (or similar) module in that split.


### [LOW] portal/src/lib/orchestratorReply.ts:39 — formatOrchestratorReply is now ~54 lines (just over the 50-line guideline)
The added clarification-merge block pushes the function just past the 50-line
guideline. It's still linear guard-clauses + a doc comment, so it reads fine, but
the merge logic is a self-contained unit.
**Suggested fix:** Optional — extract the needs_clarification block into a small
pure helper, e.g. `mergeClarification(response, question): string`, and call it
from formatOrchestratorReply. Improves readability and lets the merge/dedup be
unit-tested directly.


### [MEDIUM] platform/services/material_bootstrap.py:179 — bootstrap_company_materials exceeds the 50-line guideline
After adding the preload + partition + insert_many, the function is ~63 code lines and
now juggles several responsibilities (resolve company id, load templates, preload
categories, preload units, auto-create missing cats/units, group rows, preload existing
materials, partition into update/insert, batched write). It's cohesive and readable, but
crosses the review rubric's 50-line threshold and is getting hard to scan.
**Suggested fix:** Extract the per-material partition loop (resolve → update-existing vs
collect-to-insert) into a small private helper, e.g. `_partition_materials(grouped,
existing_by_name, categories, units, company_id, result) -> list[Material]`. Pure
mechanical extraction, no behavior change.


### [HIGH] platform/agents/orchestrator/service.py:2508 — process() is a ~245-line god-method
process() already exceeded the 50-line threshold; the intent-first change adds another inline
fast-path block, worsening it. Pre-existing structural smell — not a defect in the new logic
(the block mirrors the existing inline pre-checks). The DRY extraction in review-#3 (now applied,
`_build_rule_match_result`) trims the duplicated dicts but does not shorten the method's branch
count materially.
**Suggested fix:** Decompose process()'s deterministic pre-check sequence into a table-driven
dispatch (ordered list of `(matcher, builder)` pairs iterated in one loop) so each new pre-check
is data, not another inline `if` block. Not a blocker on its own.


### [LOW] portal/src/pages/PeoplePage.tsx:1 — file exceeds 800-line guideline (1128 lines)
The file is over the 800-line HIGH threshold. PRE-EXISTING; this change does not worsen it (net -6 lines). Reported for awareness only.
**Suggested fix:** Out of scope for this change. If addressed later, extract the create/edit Modal form, the CSV-upload Modal, and the card/table row renderers into child components.

---


### [LOW] portal/src/pages/PeoplePage.tsx:1 — file exceeds 800 lines (1168 lines)
PeoplePage.tsx is 1168 lines. PRE-EXISTING; the Role-form rename/tooltip change added ~30 lines but did not create the size problem. Reported for awareness only (per the size heuristic).
**Suggested fix:** No action needed for this change. If the page grows further, extract the Role form Modal and the list table into sub-components.


### [MEDIUM] platform/routers/support.py:~110 + platform/routers/slack_events.py:~250 — _send_flow (~85 lines) and _handle_resolve (~70 lines) exceed the 50-line guideline
Both are cohesive top-to-bottom flows but exceed the repo's function-length guideline; Phase 2's live-availability gating lands directly in `_send_flow` and will stretch it further.
**Suggested fix:** When Phase 2 touches these, extract helpers: conversation resolution (`_resolve_or_create`), Slack delivery (`_deliver_to_slack`), and the /resolve archive step.


### [MEDIUM] platform/routers/agent_helpers/delegate_create_estimate.py:143 — delegate_create_estimate grew further past the 50-line guideline
Function was already ~215 lines; the property-resolution block adds ~20 more (pre-existing violation, worsened by the 2026-07-06 property auto-link change).
**Suggested fix:** Extract the block into a helper, e.g. `_resolve_explicit_property(message, company_ctx) -> (property_id, label)`.


### [LOW] platform/agents/estimate/crud_handlers.py:1 — file now ~2,950 lines (threshold: 800, pre-existing)
The Maple analytics date-window change adds ~150 lines to an already very large mixin module; the analytics handlers are a coherent seam.
**Suggested fix:** Next refactor, move the `_analytics_*` methods (headline, total-value, windowed summary, breakdown, comparison + the shared status-set constants and `_updated_at_bounds`) into an `agents/estimate/analytics_handlers.py` mixin.

---


### [LOW] portal/src/pages/ContactsPage.tsx:1 — pre-existing: files exceed 800-line guideline
ContactsPage.tsx is ~1350 lines and PropertiesPage.tsx ~900; both exceed the 800-line review guideline. The CSV-copy change adds only a few lines and does not meaningfully worsen it.
**Suggested fix:** When next doing substantive work on these pages, extract the near-identical CSV-upload modal into a reusable component.

---


### [LOW] portal/src/pages/PropertiesPage.tsx:1 — file exceeds the 800-line guideline (pre-existing)
The file was already ~900 lines before the map-thumbnail change (net +11 from
it). The detail-panel JSX (address/contacts/map/estimates card) is now a
natural extraction seam.
**Suggested fix:** Extract the selected-property detail card into
`components/properties/PropertyDetailCard.tsx`.

---


### [LOW] platform/agents/estimate/text_helpers.py:613 — `_parse_estimate_date_filter` is 70 lines
Sequential age → numeric → period-word → word matcher; the natural-window
change added ~11 lines, pushing it past the 50-line guideline (it was already
~59). Cohesive but growing.
**Suggested fix:** If it grows further, extract the "match → (start, end)
window" resolution into a small helper. Not urgent.


### [LOW] platform/agents/orchestrator/service.py:1 — file exceeds the 800-line guideline (~2700 lines)
Pre-existing; the analytics-detector change was net-neutral (moving the
constants/detectors out to `intents.py` in the /fix-issues pass trimmed it
slightly). Not introduced by this work.
**Suggested fix:** Informational only. A future split of `OrchestratorAgent`'s
matcher methods into a mixin would be the real remedy.

---


### [HIGH] platform/agents/task/ — seven functions over the 50-line limit (finding #4)
`_handle_update_task` 105 (service.py), `find_task_from_context_or_message` 128
(resolver.py), `_resolve_create_title` 101 (create.py), `_handle_awaited_field_value`
94 (field_flow.py), `_perform_conversion` 74 (operations.py), `_handle_delete_task`
66, `process` 66 — plus `run_task_conversion` at 157 (services/task_convert.py),
which is a verbatim lift from the router that was extracted without being split.

Worth noting the pattern rather than just the numbers: `_handle_update_task` was
cut to 71 lines in the first review pass and regrew with every subsequent
smoke-test fix, because each fix added a branch to the existing function instead
of extending the structure. The #1/#2/#3 fixes in this pass added to it again.
**Suggested fix:** Extract the awaited-value preamble and the sub-op dispatch out
of `_handle_update_task`; give the resolver's seven ordered resolution steps named
helpers behind the dispatch; split `run_task_conversion` into claim / generate /
finalize.


### [HIGH] platform/tests/test_maple_task_operations.py — test file past the 800-line ceiling (finding #5)
Now ~1,560 lines after this pass added the ReDoS-timing, awaited-value, and
query-pushdown suites. It accreted a class per smoke-test round and spans routing,
payload stripping, notes updates, the field-then-value flow, title derivation,
status, assignee, archive, convert, concurrency, and performance.
**Suggested fix:** Split on the seams that already exist —
`test_maple_task_notes.py` (notes + field flow + dictated payloads),
`test_maple_task_ops.py` (status/assignee/archive/convert),
`test_maple_task_text_helpers.py` (the pure text-helper unit classes), and
`test_maple_task_perf.py` (the pathological-input timing suite).


### [MEDIUM] platform/agents/estimate/assumption_handlers.py:257,415 — the two assumption handlers remain over the 50-line guideline (residual of finding #2)
Finding #2 was applied: `_handle_assumption_material_swap` went 128 → 79 lines
and `_handle_assumption_size_adjustment` 105 → 62, by extracting
`_resolve_swap_material`, `_swap_material_lines`, `_find_materials_assumption`,
`_find_size_assumption`, `_parse_new_size`, and `_save_or_error`
(`resolve_assumptions` in `assumption_defaults.py` also split into
`_resolve_area_assumption` / `_resolve_material_assumption` and is now compliant).
What remains in both is the declarative success envelope — a multi-line f-string
response plus the `result` dict — not branching logic.
**Suggested fix:** Only worth doing if the response shape gets reused elsewhere.
Extracting it now would need a 7-8 parameter helper, which reads worse than the
inline version; revisit if a third assumption sub-op lands and the envelope
genuinely becomes shared.


### [LOW] platform/agents/estimate/crud_handlers.py — file length 3216 lines (guideline: 800)
Pre-existing violation, worsened by +123 lines when the estimate title rename
landed. The new code is cohesive with its neighbours, so this is informational
rather than a defect introduced by that change.
**Suggested fix:** split the estimate-level field handlers (title / description /
notes / property link) into their own module, mirroring how
`work_item_handlers.py` was already carved out of this file.


### [MEDIUM] platform/routers/agent_helpers/pending_property_link.py:141 — `handle_pending_property_link_confirmation` is 277 lines
Well past the 50-line guideline. Pre-existing (~258 lines), worsened by ~19 when
the word-ordinal support and the re-show-the-list branch landed. It is one linear
state machine with eight independent return paths; the new no-match branch had to
be inserted mid-function, and finding the right insertion point meant reading the
whole body.
**Suggested fix:** extract the reply-classification arms into named helpers
(`_handle_ordinal_reply`, `_handle_corrected_identifier`) so the top-level
function reads as a dispatch table.


### [MEDIUM] platform/agents/text_utils.py:859 — file is now 1075 lines (guideline: 800)
Pre-existing (1001 lines), worsened by +74 when `match_ordinal_reference` landed.
The module is a grab-bag of unrelated shared parsers — field patterns, refusal
copy, greeting detection, day windows, and now ordinals — and is the default
dumping ground for anything two agents share.
**Suggested fix:** split into focused modules (e.g. `agents/text/ordinals.py`,
`agents/text/dates.py`) re-exported from `text_utils` for backwards
compatibility. Coordinate with the `crud_handlers.py` split logged above, since
both are "shared module grew too big" with the same remedy.


### [LOW] platform/agents/text_utils.py:1 — shared helper module now 1332 lines
The listed-items work added ~260 lines to a module already past the 800-line
guideline (~1080 before). The positional/listed-items block is a self-contained
concern: the ordinal + positional matchers, the `last_listed_items` record, and
the pick helpers.
**Suggested fix:** split the listed-items + ordinal helpers into
`agents/listed_items.py` and re-export from `text_utils` for backwards
compatibility. This is the same remedy as the earlier "text_utils grew too big"
entry above — do them together rather than twice.


### [LOW] portal/src/components/Layout/AiPanel.tsx:387 — `renderAiComposer` is ~140 lines
Pre-existing (~130 lines before the composer restructure; moving the buttons
above the textbox and the disclaimer to the panel bottom added ~10). The helper
now holds the voice-error banner, the mic/new-session/send button row, the
textarea plus its voice-capture overlay, the auto-send countdown row, and the
disclaimer — five separable concerns in one render function, well past the
50-line guideline.
**Suggested fix:** not introduced by that change, so no action was required
then. If it grows again, split the button row into its own
`renderComposerControls()` helper (and possibly the countdown/error rows into a
`renderComposerStatus()`), keeping `renderAiComposer` as the layout shell.


### [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1 — file is 1838 lines
Pre-existing and not worsened (the property-label fix adds two lines).
Recorded because the file was in review scope.
**Suggested fix:** out of scope on its own. If tackled, the natural seams are
the sidebar computed values (~lines 410–465) and the work-items table.


### [HIGH] portal/src/pages/SettingsPage.tsx:1 — file is 2,605 lines (guideline 800)
The Team tab is the only settings tab still living inline in `SettingsPage.tsx`.
Every other tab is an extracted component under `components/settings/`
(`RateCardsTab`, `DivisionsTab`, `MaterialUnitsTab`, `TaskStatusesTab`,
`MaterialCategoriesTab`, `TemplatesTab`, `BillingTab`, `FinancialTab`). The
expired-invitation work added ~130 lines of invitation logic to that inline
mass, so the drift from the established pattern grew. Pre-existing condition,
worsened rather than introduced.

**Why it was deferred rather than fixed:** the extraction is not a move of the
~320 lines of team JSX. It carries roughly 28 `useState` declarations, four
dialogs (member role, member remove, leave company, invite) plus the overage
and add-card modals, ~15 handlers, and three loaders — around 1,000 lines with
`currentUser` / `isOwner` / `companyDetails` shared across other tabs. Test
coverage over that surface is thin: `SettingsPageInvitationActions.test.tsx`
exercises the invitation rows only, and member edit / member remove / leave
company have no component tests at all, so a regression in the moved code would
be silent.

**Suggested fix:** extract `components/settings/TeamTab.tsx` as its own change,
in two steps — first add component tests covering member role edit, member
removal and leave-company so the move has a safety net, then move state,
handlers and dialogs across with the tab's props limited to `currentUser` /
`isOwner` / `companyDetails` and an `onCompanyChanged` callback.


### [LOW] platform/agents/estimate/work_item_handlers.py:851 — `_handle_update_estimate_work_item_update_field` is 176 lines
Pre-existing length, worsened by ~8 lines when the division branch changed to
validate against the company's own divisions. The function handles value
extraction, three refusal gates, the description branch, division validation,
estimate resolution, work-item matching, save, and response construction.

**Suggested fix:** split the division branch into its own
`_handle_work_item_division_update` when the file is next touched — not
attributable to this change alone.


### [HIGH] platform/routers/auth.py — 1117 lines, exceeds the 800-line threshold
Pre-existing (1030 lines at HEAD) but worsened by +87 in this change. The module
now carries authentication, signup, verification email, password reset, the full
invitation lifecycle (create / list / resend / revoke / accept), company
onboarding, onboarding progress, and the Brevo member fan-out — the God Router
smell. `accept_company_invitation` is 105 lines; `create_company_invitations` is
160. Not attributable to this change, which is why it was deferred rather than
fixed: splitting it is its own piece of work with its own test surface.

**Suggested fix:** extract the invitation lifecycle into
`platform/routers/invitations.py` (create / list / resend / revoke / accept plus
their helpers `_hash_invitation_token`, `_generate_invitation_token`,
`_get_effective_invitation_status`, `_is_actionable_invitation`,
`_serialize_invitation`, `_find_pending_invitation`, `_find_invitation_by_token`).
That alone moves roughly 400 lines and leaves `auth.py` close to the threshold.


### [MEDIUM] long functions added by the Brevo lifecycle change
`reinstate_company_account` (72 lines, `platform/routers/companies.py:111`),
`detach_non_owner_members` (60, `platform/services/company_service.py:25`) and
`sync_user_stage` (55, `platform/services/brevo_contacts.py:361`) all exceed the
50-line guideline. Docstrings and explanatory comments dominate — the executable
logic is roughly half of each — so this reads as borderline rather than genuinely
dense, which is why it was deferred.

**Suggested fix:** optional. `reinstate_company_account`'s guard chain (token
email → user → owner role → has company → company exists) is the one worth
extracting, into a `_require_owner_of_own_company()` helper mirroring the
existing `_require_owner_company_access` in the same module.


### [MEDIUM] portal/src/pages/SettingsPage.tsx:1 — file is 2,745 lines (guideline 800)
**Duplicate of the 2026-07-31 entry above** (`SettingsPage.tsx:1 — file is 2,605
lines`); recorded here only to update the count and confirm the trend. The
responsive-layout work added ~45 lines to the same inline Team tab, taking it
from 2,605 to 2,745 — the third consecutive review to flag this file.

Raised at MEDIUM this time rather than HIGH: the risk belongs to the file's
history, not to this diff, which is a copy change plus Tailwind class edits.

**Suggested fix:** unchanged — see the 2026-07-31 entry for the full extraction
plan (add component tests for member role edit / member removal / leave company
first, then move state, handlers and dialogs into
`components/settings/TeamTab.tsx`). Note that the stacked-table markup added on
2026-08-02 moves with the tab and needs no rework; the new
`SettingsPageTeamResponsive.test.tsx` covers part of the safety net that entry
asks for, though the member-edit and leave-company paths are still untested.


### [LOW] portal/src/pages/SettingsPage.tsx:1 — file is 2,766 lines (guideline 800)
**Fourth consecutive flag on this file** — see the 2026-07-31 entry (2,605
lines) for the full extraction plan and the 2026-08-02 entry (2,745 lines) for
the previous recurrence. The count is now 2,766.

Raised at LOW, a step down from the last two entries, because this diff is a
net **+17** lines to the file (`git diff --numstat`: +28 / −11) and roughly
half of that is offset work: the "Unverified" pill and its `isUnverifiedMember`
helper add ~28 lines, while removing the dead "Accepted" invitation column
takes 11 away. The drift from 2,745 to 2,766 is almost entirely this change,
but the magnitude is small and the file's size problem is structural, not
diff-driven.

**Suggested fix:** unchanged — see the 2026-07-31 entry. Worth noting that the
safety net that entry asks for has grown again: `SettingsPageTeamVerification.
test.tsx` (new in this change, 8 tests) now covers the members-table row
rendering and the invitations-table columns, on top of
`SettingsPageTeamResponsive.test.tsx` and `SettingsPageInvitationActions.
test.tsx`. Member role edit, member removal and leave-company remain the
untested paths blocking a confident extraction.


### [HIGH] platform/agents/orchestrator/service.py — 3,091 lines, well past the 800-line ceiling
Selected for fixing, ATTEMPTED, and reverted. Recording what the attempt established so
the next one starts informed rather than repeating it.

The plan was to extract the rule tier into `agents/orchestrator/rules.py` as a mixin,
matching the layering `agents/task/` already uses for exactly this reason. A static check
looked encouraging: the 16 rule-tier methods are ~954 lines, and of the module constants
they touch, **zero** are also referenced by the non-rule methods — no import cycle.

The extraction was mechanically completed (service.py 3,051 → 1,528; rules.py ~1,200) and
then reverted, for two reasons the constant analysis had not predicted:

1. **The coupling is bidirectional.** mypy found **14** call-backs from the extracted tier
   into methods that remain on `OrchestratorAgent` (`_ambiguity_fallback`,
   `_resolve_action_from_history`, and others). A mixin can only express that with an
   explicit seam — the `raise NotImplementedError` contract `agents/task/base.py` uses —
   and that seam has to be *designed*, one declaration per crossing, not discovered by
   moving code and seeing what breaks.
2. **It does not actually clear the ceiling.** The result is a 1,528-line file and a
   1,200-line file. Both still over 800. The split has to be finer than "rules vs. the
   rest" to be worth doing at all.

**Suggested fix:** treat this as its own change, not a rider on a feature commit. Start by
listing the 14 crossings and deciding which are genuinely the rule tier's business versus
which belong to the agent — that boundary, not the line count, is the thing to get right.
Then split into more than two modules (candidates: action/domain resolution, the
specific-phrasing overrides, entity-shape inference, history/anchor resolution).


### [MEDIUM] platform/scripts/backfill_task_readable_ids.py:70 — `_run` is 53 lines
Just over the 50-line guideline, mixing querying, the dry-run preview branch, and the
apply branch with its own error tally.
**Suggested fix:** extract `_preview(grouped)` and `_apply(grouped)`, leaving `_run` as
orchestration plus the summary. Low priority — it is a one-off migration script.


### [LOW] platform/tests/test_estimate_api.py:1 — test file well past the size guideline
Now ~5,200 lines, against the 800-line guideline. Pre-existing; the panel work added
~160.
**Suggested fix:** split by concern (CRUD / status transitions / listing / docs) when
next doing substantial work in it.


### [MEDIUM] platform/agents/estimate/llm_pipeline.py:677 — functions grown past the 50-line rule by the per-scope-assumptions change
`_step2_and_3_for_scope` went from ~20 to 64 lines; `_step3_research_for_scope` is 136,
`_run_pipeline` 104, `search_similar_work_items` 94, `build_estimate_research_prompt` 107,
`render_material_catalog` 66 (new). Much of the growth is comment prose rather than
logic, but the per-scope orchestration in `_step2_and_3_for_scope` now does four distinct
things (vector retrieval, area assumption, reuse decision, research dispatch).
**Suggested fix:** extract the area-assumption resolution and the reuse decision from
`_step2_and_3_for_scope` into named helpers.


### [MEDIUM] platform/agents/estimate/catalog_matching.py:1 — file at 793 lines, 7 under the 800 threshold
The fuzzy-matching rewrite added ~250 lines (scoring engine + module docstring). The next
addition crosses the guideline. The module already has two unrelated halves: the scoring
engine (module-level pure functions) and the mixin's measurement-unit / size-capacity /
purchase-quantity helpers, which have nothing to do with matching.
**Suggested fix:** split the measurement-unit and size-capacity helpers into their own
module before the next substantial change to this file.


---

## Section context for relocated entries

Review-pass headers whose every finding was relocated above. Kept because the
preamble records what each pass covered. Note that any procedural advice in
these is superseded — the ruff note's "scope `./run_ruff.sh` to the files you
touch" workaround, in particular, ended when the backlog cleared 2026-06-04.

## 2026-05-20 review (dashboard analytics window change)


## 2026-06-03 (ruff lint gate adoption)

`ruff` was adopted as a hard lint gate for `platform/` on 2026-06-03, the same
model as the mypy gate (#3). Config is pinned in `platform/ruff.toml`; run via
`./run_ruff.sh`. Ruleset: `E, F, I, B, C4, SIM` — `E501` (line length) off, `UP`
(pyupgrade) intentionally excluded (its annotation rewrites collide with the
mypy.ini playbook). See CLAUDE.md "ruff is a Gate, Not a Suggestion" for the
full policy + recurring playbook.

On adoption the safe auto-fixable backlog (~287 fixes: import sorting + trivial
simplifications, **no import deletions**) was applied across 186 files. The
manual backlog below remains and must be worked down before the project is
fully green. **Until then, scope `./run_ruff.sh` to the files you touch** so you
gate your change without tripping over the legacy backlog.

> **F401 is report-only by config** (`unfixable = ["F401"]`). Blanket
> `ruff --fix` is **unsafe** in this codebase: it deletes (a) re-export-hub
> imports — modules that import a symbol only to re-expose it (`routers/estimates.py`,
> `routers/agents.py`, `agents/estimate/service.py`) — and (b) module-level
> imports that tests monkeypatch via `setattr(module, "Name", ...)` (e.g.
> `estimate_service.ChatOpenAI`). Both break imports/tests; the second isn't
> caught by an `import main` smoke test. This was learned the hard way during
> adoption (140 test failures from the first sweep, fully reverted). Triage each
> F401 by hand: genuinely dead → delete; re-export → add to `__all__`;
> monkeypatch target → keep with `# noqa: F401` + reason.


## 2026-06-23 deferred from /code-review (People page container-query + Unit column removal)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.


## 2026-06-23 deferred from /code-review (Role form rename + breakdown tooltips)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.


## 2026-07-02 deferred from /code-review (support Phase 2 — Live Chat)

Logged by `/fix-issues` — findings from the Phase 2 review not fixed in that pass. #1 (stale mirror reconcile), #2 (atomic upsert), and #3 (unknown-action test) were fixed in the pass.


## 2026-07-02 deferred from /code-review (Slack mrkdwn decoder)

Logged by `/fix-issues` — findings from the mrkdwn-decoder review not fixed in that pass. #1 (end-to-end webhook decode test) was added in that pass.


## 2026-07-02 deferred from /code-review (tooltips + New Session relocation)

Logged by `/fix-issues` — findings from the button-tooltip / New-Session-relocation review not fixed in that pass (selection: none).


## 2026-07-02 deferred from /code-review (in-thread Resolve shortcut)

Logged by `/fix-issues` — findings from the message-shortcut review not fixed in that pass. #1 (best-effort Firestore archive) was fixed in the pass.


## 2026-07-04 deferred from /code-review (voice input Phases 1–4 full review)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.


## 2026-07-09 deferred from /code-review

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.


## 2026-07-15 follow-up from the property-geocoding feature

Logged manually — follow-up work identified while building property
coordinates + task-title snap (not a review finding).


## 2026-07-21 deferred from /code-review (Maple pending-flow escape + analytics window)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.


## How to work through this

1. Pick ONE HIGH item per work session. Don't batch.
2. Write the failing test first (TDD per `CLAUDE.md`).
3. Run the related test file, not the full suite.
4. Commit each item as its own PR — easier to revert, easier to review.
5. Delete the bullet from this file in the same PR.

When this file is empty, delete it.

---


## 2026-07-30 deferred from /code-review (portal — property estimates + Maple composer)

Logged by `/fix-issues` — findings from the latest review (property-detail
estimate list, Maple composer layout) not fixed in that pass. Findings #1–#5
were fixed; this one was not.


## 2026-07-31 deferred from /code-review (Team page — expired invitations)

Logged by `/fix-issues` — the selection was `all`; this finding was the one
fix that proved substantially larger than its ledger entry described, so it is
recorded here rather than half-applied. Findings #2–#7 from that review were
fixed in the same pass.


## 2026-08-02 deferred from /code-review

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.
Review scope was the Brevo lifecycle-list feature, company-close detach, the
reinstate flow, the ops Last Login column, and the ErrorBoundary crash fix.


## 2026-08-02 deferred from /code-review (Team page — responsive layout + plan Tasks copy)

Logged by `/fix-issues` — the selection was `1, 2, 4, 5, 6`; findings #1, #2, #4,
#5 and #6 were fixed in that pass. One finding is deferred, and it is a
recurrence rather than a new item.


## 2026-08-05 deferred from /code-review (Team page — unverified-member pill)

Logged by `/fix-issues` — the selection was `1, 2`; findings #1 and #2 were
fixed in that pass. One finding is deferred, and it is again a recurrence
rather than a new item.


## 2026-08-12 deferred from /code-review (dropdown placement + Create Estimate dialog)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.
`/fix-issues 1,4,5,6,7` fixed the rest. #2 (panel can flip sides mid-scroll) was
reviewed and **accepted as-is** by the user — deliberately not tracked here.


---

## Obsolete — "bandit not installed" (7 duplicates removed)

Seven byte-identical LOW entries were logged by consecutive `/code-review`
runs between 2026-06-28 and 2026-07-02 while bandit was missing from the venv.
bandit was adopted 2026-07-27 and is documented in CLAUDE.md. One kept as a
record:

### [LOW] platform/.venv — bandit not installed; automated security scan skipped
The `/code-review` bandit step could not run; only the manual security pass covered the diff. There is no dev-requirements split — adding `bandit` to the single runtime `requirements.txt` would ship a dev-only scanner to production.
**Suggested fix:** Introduce a `requirements-dev.txt` (or a `[project.optional-dependencies] dev` group) and pin `bandit` there, then wire it into the review tooling. Tooling/process task, not a source fix.


