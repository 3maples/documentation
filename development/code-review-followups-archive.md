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
