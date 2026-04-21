# Plan: Maple CRUD Coverage Test Suite + Gap Report

> **Status:** Most of this plan has shipped. The "What shipped" section is the source of truth for current behavior; the "What's open" section is the punch list.

## Context

Maple is the Orchestrator agent ([platform/agents/orchestrator/service.py](platform/agents/orchestrator/service.py)) — a hybrid rule-based + LLM intent classifier that routes user messages to specialized agents (Contact, Property, Material, Labour, Estimate). The user wants confidence that Maple correctly handles realistic CRUD-style user questions for four resources:

- **Property** — job sites / addresses
- **Contact** — *individuals* associated with a property
- **Material** — catalog of physical products
- **People / Labour** — catalog of *role definitions* (Landscaper, Foreman, etc.) — **distinct from Contact**

**Equipment** is explicitly blocked (see policy below). **Estimate** was originally out of scope (different ReAct + generation architecture); the *Estimates drilldown* section below adds a query + light-CRUD surface for Maple without changing the existing generation pipeline.

**Goal**: a parametrized phrasing matrix exercised at two tiers (rule-only, live LLM) producing a dual-column gap report that shows, per phrasing, whether rules handle it AND/OR whether the LLM rescues it.

## What shipped

### Two-tier coverage matrix
- **111 cases** = 9 categories × 4 CRUD resources × 3 phrasings + 3 equipment refusal phrasings
- Tier 1 (`use_llm=False`) runs by default; Tier 2 (`@pytest.mark.llm_e2e`) opt-in via `-m "" / -m llm_e2e`
- Dual-column markdown report at `platform/tests/reports/maple_crud_gap_report.md` (gitignored)
- Files: [tests/_maple_coverage_data.py](platform/tests/_maple_coverage_data.py), [tests/test_maple_crud_coverage.py](platform/tests/test_maple_crud_coverage.py), [tests/conftest.py](platform/tests/conftest.py) (terminal-summary hook + `llm_e2e` marker), [pytest.ini](platform/pytest.ini)

### Safety policies (rules + agent defenses)
- **Bulk delete forbidden via Maple**: `is_bulk_delete_request()` + `BULK_DELETE_REFUSAL_MESSAGE` in [agents/text_utils.py](platform/agents/text_utils.py); guards wired into orchestrator `_classify_with_rules` AND `process()`, plus belt-and-braces refusals at top of every domain agent's `process()`. HTTP routers untouched (UI-driven bulk delete still possible).
- **Equipment requests refused**: `is_equipment_request()` + `EQUIPMENT_REFUSAL_MESSAGE`; same wiring pattern as bulk delete.

### Cheap rule wins (closed real coverage gaps)
- `ACTION_HINTS["list"]` extended with `count`, `total`, `how many`
- `ACTION_HINTS["get"]` extended with `search`
- New `PLURAL_DOMAIN_TOKENS` mapping powers a plural-aware flip: when action is `get` but the message contains a plural domain form (incl. colloquial "people"/"workers"/"labour roles"), action flips to `list` so "find contacts named Smith" routes to `list_contacts`, not `get_contact`
- `is_help_query` smarter: when CRUD intent is firm and action is `list`, prefers CRUD over help even with enum keywords ("how many labour roles" no longer misroutes to help via "roles")

### People / Labour (the user's "People" UI label = the `labour` code domain)
- Bulk-delete defensive refusal in [agents/labour/service.py](platform/agents/labour/service.py)
- Field-extraction `of` separator in `_extract_fields_from_message`
- `_match_bare_field_name()` + `awaiting_value_for` multi-turn flow in `update_labour` branch
- Matrix uses `labour role` / `labour roles` + role-titles (Landscaper / Foreman) as `{NAME}` to avoid implying individual people
- Disambiguation regression tests prove "Update John Doe's role to Manager" never misroutes to `update_labour`

### Property / Contact / Material parity
Same fixes applied across all three:
- Bulk-delete defensive refusal in each agent's `process()`
- `of` separator in `_extract_fields_from_message`
- `_match_bare_field_name()` helper + `awaiting_value_for` multi-turn flow in each agent's `update_*` branch
- Reuses the `humanize_field_name` helper for clarification messages

### UX: count + tone
- `is_count_query(text)` + `format_count_response(count, singular, plural)` helpers
- All four CRUD agents: count queries return a count summary ("You have 7 contacts right now."), not a list dump. Name-based filtering is skipped for count queries so the count operates on the full catalog.
- All response strings rewritten to first-person friendly tone:
  - Create / Update / Delete / Get: "I've ___ for you. Here are the details: …"
  - List: "Here are your ___: …"
  - Empty list: "I couldn't find any matching ___."
  - Count: "You have N ___ right now." / "You have 1 ___ right now." / "You don't have any ___ yet."
- Labour agent uses "labour role" terminology in responses (not "person") to honor the People-vs-Contact disambiguation

### Test coverage
- 439 Maple-layer tests passing, zero regressions
- Per-agent regression tests for: tone (create/update/delete/list), count queries (N>1), empty-list, alt count phrasings ("count my", "total number"), singular grammar (N=1), multi-turn field-then-value flow, "with X of Y" extraction
- Helper unit tests for `is_bulk_delete_request`, `is_equipment_request`, `is_count_query`, `format_count_response`, refusal-message content invariants — all parameterized for edge cases

### Documentation
- Maple section added to [CLAUDE.md](CLAUDE.md) covering: supported resources, People-vs-Contact distinction, equipment block, bulk-delete policy, shared text-utility helpers, friendly-tone template, multi-turn flow, coverage matrix invocation

## What's open

| Item | Effort | Value | Notes |
|---|---|---|---|
| **Materials drilldown** (see section below) | small fix + medium coverage | **high — live bugs** | List + get-by-name return generic error in production |
| **Estimates drilldown** (see section below) | **large** — new CRUD branch + nested Work Item/Activity ops | **high — Maple has no query surface today** | 5 estimate intents are registered in the orchestrator but EstimateAgent.process() only runs the generation pipeline, so list/count/filter queries have no handler. Scope now covers: read surface, status transitions, property-link management, and full CRUD on Work Items + Activities (nested ops pattern mirroring Materials sizes). Line-item cost catalog (material/labour/equipment rows inside a Work Item) stays UI-only. |
| Architectural gaps in matrix (`verbless` 0/12, `implicit_relationship` 3/12, `possessive` 2/12 rules-only) | hours / design | high | Need a name resolver + cross-resource query model — not regex tweaks. **Next conversation, not next commit.** |
| Labour `_extract_name_from_message` over-eagerness | small | low | Patched the symptom (skip name extraction for count queries) but the underlying regex still over-matches phrases like "labour roles do I have". Tighten the regex to require role-title shapes. |
| Field-extraction parity for Labour and Equipment if they ever come back into scope | medium | low | Equipment is currently blocked; replicating fixes would only matter if it's unblocked |
| Stale xfail markers in coverage matrix (9 `XPASS` in Tier 1) | small | low | Cases in the `possessive` / `field_targeted_update` / `implicit_relationship` gap categories that now pass — e.g. `possessive/labour/show_me_landscapers_details`, `field_targeted_update/contact/change_the_phone_of_john_doe_to_555-1111`, `implicit_relationship/material/find_estimates_with_concrete_blocks`. Markers are category-wide booleans in [_maple_coverage_data.py](platform/tests/_maple_coverage_data.py); tightening means adding per-case exemption lists. `xfail(strict=False)` so they don't fail the suite. |

## Materials drilldown — live bugs + coverage gaps

### Reported symptoms

- "How many materials do I have?" → **"I could not complete the material request."** (expected: count summary like "You have N materials right now.")
- "Show me the details for the material Screened Topsoil" → **same generic error** (expected: get_material with details)

### Root cause (single underlying bug — both symptoms share it)

The Material agent is the **only CRUD agent** that calls a FastAPI router function for its list query, while every other agent queries Beanie directly:

| Agent | List implementation |
|---|---|
| Property | `await Property.find(Property.company == PydanticObjectId(company_id)).to_list()` ([property/service.py:837](platform/agents/property/service.py#L837)) |
| Contact | `await Contact.find(Contact.company == ...).to_list()` ([contact/service.py:960](platform/agents/contact/service.py#L960)) |
| Labour | `await Labour.find(Labour.company == ...).to_list()` ([labour/service.py:674](platform/agents/labour/service.py#L674)) |
| **Material** | **`return await materials_api_get_materials(company=company_id)`** ([material/service.py:969-970](platform/agents/material/service.py#L969-L970)) ← the router function |

`materials_api_get_materials` in [routers/materials.py:159](platform/routers/materials.py#L159) requires `decoded_token: dict = Depends(verify_verified_firebase_token)`. When the agent calls this function directly (outside a FastAPI route handler), the `Depends` machinery has no request context to inject the token from, so the call raises an exception. The exception is swallowed by the broad `try/except` at [material/service.py:1947-1964](platform/agents/material/service.py#L1947-L1964), which returns the generic `"I could not complete the material request."` message and stashes the real exception in the response's `error` field.

This breaks **both** symptoms because:
- Count query path: `process()` → list_materials branch → `_list_materials_via_api()` → router → auth failure
- Get-by-name path: `process()` → get_material branch → `_resolve_target_material()` → `_find_materials_by_name()` → `_list_materials_via_api()` → router → auth failure

### Why tests didn't catch it

Every existing Material test mocks `_list_materials_via_api` (e.g. [test_material_agent.py:700](platform/tests/test_material_agent.py#L700), [726](platform/tests/test_material_agent.py#L726)), so the auth failure never surfaces in the test suite. The mocks return fake `FakeMaterialDoc` objects directly, masking the real router-call indirection.

### Fix (minimal, matches the other 3 agents)

Rewrite [material/service.py:969-970](platform/agents/material/service.py#L969-L970) to query Beanie directly:

```python
async def _list_materials_via_api(self, company_id: str) -> List[Material]:
    return await Material.find(Material.company == PydanticObjectId(company_id)).to_list()
```

That single change resolves both symptoms (count query + get-by-name). No router/auth changes needed.

### Coverage gaps to close (CRUD on name, description, category, sizes)

Material's domain is richer than the others — `sizes` is a list of `MaterialSizeCost` objects (each with `size`, `unit`, `cost`, `price`). Plus `category` is a `PydanticObjectId` reference to `MaterialCategory`. Existing tests only exercise simple `cost`/`size` scalar updates. Add coverage for:

1. **Anti-regression for the bug above** — one integration test that calls `_list_materials_via_api` *unmocked* through a stubbed Beanie layer, proving the agent doesn't depend on FastAPI's `Depends`. Pin the contract at [test_material_agent.py](platform/tests/test_material_agent.py).
2. **Get-by-name with multi-word names** — e.g. "Screened Topsoil", "Premium Concrete Mix". Verify `_find_materials_by_name` matches via case-insensitive substring and the response uses the friendly tone.
3. **Field-level update coverage** — separate test per field:
   - `name` update (rename material)
   - `description` update (set / replace / clear)
   - `category` update (resolve category by name → ObjectId, or via existing category ID)
   - `sizes`: update cost on a specific size, update price, add a new size, remove a size, rename a size
4. **Count query through the orchestrator-context path** — exercise with `orchestrator_intent="list_materials"` in context (the path the live app uses), not just isolated agent invocation. We added this for Contact in the empty-list test; replicate for Material.
5. **Get-by-name confirmation flow** — when multiple materials match a fuzzy name, the agent should ask the user to disambiguate.

### Implementation order

1. Ship the Beanie fix in `_list_materials_via_api` first (single line; closes both live bugs immediately) ✅
2. Add an integration test that fails without the fix (would have caught the bug) ✅
3. Add the field-level + multi-size coverage (separate commits per concern if desired) ✅
4. Re-run Tier 1 + Tier 2 — Material's score should hold or improve ✅

## Materials drilldown phase 2 — categories + nested sizes CRUD

The previous drilldown closed the live bugs and added field-level coverage. Phase 2 expands Maple's Material vocabulary to handle category-aware queries and richer size operations.

**Status:** Categories shipped ✅. Sizes CRUD shipped ✅ (5 new tests: per-size price update without clobbering cost, per-size unit update, remove one of many, rename size label, refuse to remove the last size).

### Category support (new) ✅ shipped

`MaterialCategory` is a separate `Document` model ([models/material_category.py](platform/models/material_category.py)) with just `name` and `company`. The Material agent already auto-creates categories on demand via `_find_or_create_category` ([material/service.py:932-944](platform/agents/material/service.py#L932-L944)) — but there's no Maple surface for **listing**, **filtering by**, or **inspecting** a category, and no policy preventing a user from asking Maple to manage categories directly.

**Phrasings to support:**
| Phrasing | Behavior |
|---|---|
| "List available material categories" / "what categories do I have?" / "show me categories" | New intent: `list_material_categories` (read-only) — returns the company's categories |
| "Find materials in the Hardscape category" / "show me materials in Masonry" | `list_materials` filtered by category name |
| "What category is Concrete Mix in?" / "what's the category of X?" | `get_material` (existing) — response surfaces the category prominently |
| "Change Concrete Mix category to Masonry" | `update_material` with `category` field (already partially covered — extend tests to cover category-by-name resolution) |
| "Create a new category called Hardscape" / "delete the Hardscape category" / "rename Masonry" | **Refused** with policy message: *"Material categories are managed in the catalog UI — I can't create, rename, or delete them from chat. I can list categories, find materials in a category, or change which category a material belongs to."* |

**Implementation (all ✅ shipped):**
1. ✅ `list_material_categories` registered in `SUPPORTED_INTENTS_BY_AGENT["Material Agent"]` and `MATERIAL_SUPPORTED_INTENTS`.
2. ✅ `is_material_category_management_request()` + `MATERIAL_CATEGORY_REFUSAL_MESSAGE` in [agents/text_utils.py](platform/agents/text_utils.py). Verbs disjoint from "change"/"set" so material-update phrasings ("change Concrete Mix category to Masonry") do NOT trip the refusal.
3. ✅ Refusal guard wired into both `_classify_with_rules` and `process()`.
4. ✅ `_LIST_CATEGORIES_PATTERN` + `_LIST_CATEGORIES_QUESTION_PATTERN` short-circuit BOTH in `_classify_with_rules` AND ahead of `is_help_query` in `process()` (otherwise the "categories" enum keyword would route to help).
5. ✅ `list_material_categories` branch in [agents/material/service.py](platform/agents/material/service.py) — queries `MaterialCategory.find(MaterialCategory.company == ...).to_list()` (Beanie direct, same pattern as the bug fix), friendly tone, count form via `format_count_response`.
6. ✅ `_resolve_category_filter()` helper + category-filter branch in `list_materials`. Runs *before* `name_hint` lookup because phrases like "find materials in the Hardscape category" cause the name extractor to grab "Hardscape" — the category lookup disambiguates and wins when it matches.

### Sizes CRUD (extend) — ✅ shipped

Previously tested:
- ✅ Update cost on a specific size (via existing `cost` alias that writes both price+cost)
- ✅ Add a new size (merges with existing)

Now added:
- ✅ **Update price on a specific size** — separate from cost. Previously a price-only update silently overwrote cost (because `_build_sizes_from_fields` set `item["cost"] = price` as a fallback). The update-existing branch now only touches cost when the caller explicitly supplied it.
- ✅ **Update unit on a specific size** — resolves the unit name to a `MaterialUnit` ObjectId and writes it into the matching size entry only. Other sizes retain their unit.
- ✅ **Remove a size from a material** — drops the matching entry by size label.
- ✅ **Rename a size label** — changes the `size` text on the matching entry; price/cost/unit carry through.
- ✅ **Refuse to remove the last size** — `MaterialSizeCost` requires `min 1 item` per the model. The Material agent returns a clarification ("I can't remove the last size from this material …") instead of producing a zero-size payload Pydantic would reject.

**Implementation (all shipped):**
1. ✅ New allowed fields: `size_op ∈ {"remove","rename"}`, `new_size`, `unit_oid` — registered in [agents/material/service.py](platform/agents/material/service.py) `MATERIAL_ALLOWED_FIELDS` and handled in `_normalize_fields`.
2. ✅ `_build_sizes_from_fields` extended with branches for `size_op=="remove"`, `size_op=="rename"`, and per-size unit-only updates. The price-update branch no longer clobbers cost.
3. ✅ `_normalize_sizes_field` + the existing-sizes block in `_material_payload_from_fields` preserve the per-size `unit` field so size-level ops don't drop it.
4. ✅ `process()` update_material branch: detects `size_op=="remove"` with `len(existing_sizes) <= 1` and returns a clarification response *before* building the payload; resolves `unit` (string) → ObjectId via `_find_or_create_unit` and stashes as `fields["unit_oid"]` when the update is a pure per-size unit change.

**Deferred (low value for this commit):**
- Regex extraction in `_extract_fields_from_message` for size-op phrasings. The tests mock `_classify_with_llm` to emit `size_op`/`new_size` directly; in production the LLM is expected to emit these fields (the extraction prompt will be updated alongside). Rule-level regex fallback can land later if production phrasings drift.

### Test coverage

| Test | Status |
|---|---|
| `test_list_material_categories_returns_friendly_list` | ✅ |
| `test_list_material_categories_count_query` | ✅ |
| `test_list_material_categories_empty_uses_friendly_form` | ✅ (added) |
| `test_orchestrator_routes_list_material_categories` | ✅ |
| `test_orchestrator_routes_what_categories_do_i_have` | ✅ (added — short-circuits the help handler) |
| `test_orchestrator_routes_count_material_categories` | ✅ (added) |
| `test_orchestrator_refuses_create/delete/rename_material_category` | ✅ (3 cases) |
| `test_orchestrator_change_material_category_value_is_not_refused` | ✅ (added — proves "change Concrete Mix category to Masonry" still routes as a material update) |
| `test_list_materials_filters_by_category_name` | ✅ |
| `test_list_materials_no_category_match_falls_back_to_unfiltered` | ✅ (added) |
| `is_material_category_management_request` parametrized helper tests | ✅ (10 positive + 10 negative) |
| `test_material_category_refusal_message_names_what_maple_can_do` | ✅ |
| **Sizes CRUD coverage** (shipped) | |
| `test_material_size_update_price_preserves_cost` | ✅ |
| `test_material_size_update_unit` | ✅ |
| `test_material_size_remove_one_of_many` | ✅ |
| `test_material_size_rename_label` | ✅ |
| `test_material_size_remove_last_size_refuses` | ✅ |

Deferred from the original spec (low value relative to current coverage; revisit if needed):
- `test_get_material_response_surfaces_category` — already covered indirectly by existing get_material tests + the response template
- `test_update_material_category_by_name` — partial coverage exists in `test_material_update_category_field`; add an end-to-end variant alongside sizes work if it matters

### Implementation order — categories + sizes phases complete

1. ✅ Helper + refusal message in `agents/text_utils.py`
2. ✅ Intent registration + orchestrator rule + orchestrator-level tests
3. ✅ Material agent: `list_material_categories` branch + Beanie call + friendly response
4. ✅ Material agent: category-filter branch in `list_materials`
5. ✅ Material agent: size update/remove/rename helpers + per-size unit resolution + refuse-last-size guard
6. ✅ Tests at each step (TDD)
7. ⏳ Re-run Tier 1 + Tier 2 after sizes ship (Tier 1 clean; Tier 2 requires `OPENAI_API_KEY`)

### Out of scope for this phase

- A standalone Category agent (premature; the Material agent owns the surface)
- Multi-category filters ("materials in Hardscape OR Masonry") — single-category filter only
- Equipment alignment — equipment remains explicitly blocked (see policy below)

## Estimates drilldown — add query + light-CRUD surface to Maple

Originally out of scope because the EstimateAgent is architecturally different from the other four CRUD agents — it's a generative pipeline (conversational gathering → extraction → assembly → optional ReAct loop) that produces estimates from a description. That pipeline is not changing. What *is* changing: Maple needs to answer questions about existing estimates, handle a small set of state transitions, manage the **property link** on an estimate, and do **nested CRUD on Work Items (`JobItem`) and their Activities (`ActivityItem`)** — the two layers that represent user-authored scope. Material / labour / equipment line items inside a Work Item stay UI-only, because they couple cost-catalog resolution with the totals pipeline.

### Gap analysis — current state

1. **Intents are registered, handlers are not.** [agents/orchestrator/intents.py](platform/agents/orchestrator/intents.py) already wires `create_estimate`, `update_estimate`, `delete_estimate`, `list_estimates`, `get_estimate` to "Estimate Agent", and "estimate"/"quotes" appear in `PLURAL_DOMAIN_TOKENS` + `DOMAIN_HINTS`. The orchestrator routes to EstimateAgent correctly — but [agents/estimate/service.py](platform/agents/estimate/service.py) `process(query, company, property, context)` only implements the generation flow plus enum-help. There is no `list` / `get-by-code` / `count` / `filter` / `sort` / `status-transition` / `delete` branch. In production, `"list my estimates"` is a live dead-end.
2. **Signature mismatch with the other CRUD agents.** Property/Contact/Material/Labour agents expose `process(message, context)` returning the standard CRUD envelope (`intent`, `matches`, `needs_clarification`, `response`, `result`, …). EstimateAgent's signature is `process(query, company, property, context)` and it returns a generation-shaped envelope (`completion_ready`, `accuracy_suggestions`, `parsed`). The orchestrator's delegation path assumes the CRUD envelope; the impedance mismatch needs to be resolved before the CRUD branch can return clean responses.
3. **No Maple-layer estimate tests.** [tests/test_estimate_agent.py](platform/tests/test_estimate_agent.py) only covers the generation pipeline. There are no orchestrator-level tests for "list estimates" / "how many won estimates?" / etc. `test_maple_crud_coverage.py` excludes estimate entirely (see `_CRUD_RESOURCES` in [tests/_maple_coverage_data.py](platform/tests/_maple_coverage_data.py) — only property/contact/material/labour).
4. **HTTP surface is rich, not chat-exposed.** [routers/estimates.py](platform/routers/estimates.py) has GET list (with filters), GET by id, PUT update, DELETE soft-delete, PATCH archive/unarchive, and doc-version endpoints. Maple can delegate to the same Beanie queries these routers use.
5. **Domain is much richer than the other agents.** 13 `EstimateStatus` values, 7 `EstimateDivision` values, nested job_items with profit_margin / overhead / tax, grand_total. The user explicitly wants aggregate queries (count by status, highest/latest) that the other agents don't have.

### Phrasings Maple should handle

| Category | Example phrasings | Intent |
|---|---|---|
| List | "list my estimates", "show all estimates" | `list_estimates` |
| List with filter | "show me draft estimates", "list estimates in the Maintenance division", "estimates for 123 Main St" | `list_estimates` (+ `status` / `division` / `property` filter) |
| Count | "how many estimates do I have?", "how many won estimates?", "count estimates in Design & Build" | `list_estimates` (count form, reuses `is_count_query` + `format_count_response`) |
| Sort + limit | "what's my highest estimate?", "show me the latest estimate", "top 5 estimates by value" | `list_estimates` (+ `sort`, `limit`) |
| Get by code/id | "show estimate EST-2026-001", "details for estimate EST-2026-001" | `get_estimate` |
| Status transition | "archive estimate EST-2026-001", "mark EST-2026-001 as won", "unarchive EST-2026-001" | `update_estimate` (restricted to status changes from chat) |
| Property link | "link estimate EST-2026-001 to 123 Main St", "change the property on EST-2026-001 to 456 Oak Ave", "remove the property from EST-2026-001" | `update_estimate` with `property` field (resolve by address → `PydanticObjectId`) |
| Work Item add | "add a work item 'build patio' to EST-2026-001" | `update_estimate` with `work_item_op=add` (the orchestrator already has a partial match for "add … job/work item" — see [agents/orchestrator/service.py:155](platform/agents/orchestrator/service.py#L155)) |
| Work Item remove | "remove the patio work item from EST-2026-001" | `update_estimate` with `work_item_op=remove`. **Requires confirmation** (2026-04-21 safety decision): agent sets pending fuzzy-confirmation on first call; user's "yes"/"confirm" re-dispatches with `context["confirmed"]=True` and the mutation runs. Mirrors the delete-estimate confirmation pattern. |
| Work Item rename | "rename the patio work item to stone patio" | `update_estimate` with `work_item_op=rename` + `new_name` |
| Work Item field update | "change the division of the patio work item to Design/Build" | `update_estimate` with `work_item_op=update_field` (field ∈ {division}). **Scope decision 2026-04-21**: `profit_margin`, `overhead_allocation`, `labor_burden`, `tax`, `recurring`, `recurrence` are UI-only — user adjusts those manually. Chat-driven updates here would risk accidental financial changes with less context than the UI gives. |
| Work Items list | "list work items on EST-2026-001", "show me the work items for EST-2026-001" | `get_estimate` (response surfaces the `job_items` list rather than the full estimate blob) |
| Activity add | "add a 'laying sod' activity to the patio work item in EST-2026-001" | `update_estimate` with `activity_op=add` |
| Activity remove | "remove the excavation activity from the patio work item" | `update_estimate` with `activity_op=remove` |
| Activity rename | "rename laying sod activity to sod installation" | `update_estimate` with `activity_op=rename` + `new_name` |
| Activity field update | "change the role on the excavation activity to Foreman", "set hours on laying sod to 4" | `update_estimate` with `activity_op=update_field` (field ∈ {role, hours, effort rate-card reference}) |
| Activities list | "list activities in the patio work item", "show me the activities for the patio work item" | `get_estimate` (narrowed to one `JobItem`'s `activities`) |
| Delete | "delete estimate EST-2026-001" | `delete_estimate` (with confirm flow; bulk-delete already refused by `is_bulk_delete_request`) |
| Enum help | "what estimate statuses are there?", "what divisions are available?" | `help` (reuse HELP_ENUM pattern) |

### What stays the pipeline's job (refuse or defer from CRUD branch)

- **Generation from description** — "create an estimate for repaving the Smith property" still goes through the existing generation pipeline. The CRUD branch for `create_estimate` should delegate there (not reimplement).
- **Material/labour/equipment line items inside a Work Item** — `MaterialItem` / `LabourItem` / `EquipmentItem` are cost-catalog line items auto-sized by the pipeline. Editing them from chat mixes cost arithmetic with catalog resolution; the UI owns that surface. Chat CRUD stops at the Activity level (which is the user-facing unit of work).
- **Effort rate card + effort card items** — deep cross-references inside Activities. Chat can *set* an activity's role and basic hours; swapping the rate-card reference itself stays UI-only.
- **Numeric recalculation** — sub_total / grand_total / labour & material totals are computed, not user-set. The CRUD branch should recalculate after any work-item or activity mutation, never accept them as chat inputs.
- **Financial fields on Work Items** (scope decision 2026-04-21) — `profit_margin`, `overhead_allocation`, `labor_burden`, `tax`, `recurring`, `recurrence` are user-adjusted via the UI, not via chat. A one-word chat mistake could push margin to 0% on a six-figure estimate; the UI gives the numeric context (current value, company default, effective $ impact) that a chat confirmation can't. Chat can update a work item's `division` (enum-validated, reversible) and nothing else on the financial surface.
- **Doc generation** — Google Docs export lives on its own endpoint; out of Maple's chat surface.

### Implementation approach

1. **Normalize the agent envelope.** Either (a) split EstimateAgent into a thin `process(message, context)` dispatcher that routes query intents to new CRUD handlers and generation intents to the existing pipeline; or (b) keep the current signature and have the orchestrator adapt. (a) is cleaner and matches the other agents.
2. **Beanie-direct queries** for the read surface — follow the Materials-drilldown fix pattern, no FastAPI router indirection.
3. **Status-transition whitelist** — only a small set of status values is user-facing for chat: DRAFT → SUBMITTED/REVIEW, REVIEW → APPROVED/REJECTED/ONHOLD, any → ARCHIVED, ARCHIVED → previous. Hard-fail on anything outside the whitelist with a clarification.
4. **Confirm-delete flow** — reuse the `is_bulk_delete_request` guard and add a single-item confirmation flow mirroring Material delete.
5. **Extend `is_count_query` coverage** — already works at the helper level; just verify "how many {status} estimates" and "how many estimates in {division}" thread through cleanly.
6. **Property-link field resolution** — address/label → `PydanticObjectId` lookup following the Material category pattern in `_resolve_category_filter`. Refuse the update if the address doesn't uniquely match one property.
7. **Nested-op pattern for Work Items + Activities** — reuse the shape Materials established for sizes (`size_op`). Introduce `work_item_op ∈ {add, remove, rename, update_field}` and `activity_op ∈ {add, remove, rename, update_field}` as fields on `update_estimate` intent, threaded through `_normalize_fields`. Targeting is by **name** (case-insensitive) with an **index disambiguation fallback** ("which patio work item — the first or the second?") — same UX as the Material multi-match confirmation flow.
8. **Recalculation after every mutation** — after any work-item or activity mutation, invoke the existing totals path (`_fill_prices_and_calculate_totals`) so `sub_total` and `grand_total` stay consistent without the user setting them. This reuses the generation pipeline's totals code, not a parallel implementation.
9. **Ambiguity refusal policy** — when a work-item name matches multiple entries, or an activity name matches multiple activities across work items, the agent returns a numbered clarification rather than guessing. Mirrors the Material multi-match resolver.

### Test coverage to add

Following the [test_material_agent.py](platform/tests/test_material_agent.py) pattern (mock classify → mock Beanie query → assert envelope).

| Test | Purpose |
|---|---|
| `test_estimates_list_returns_friendly_list` | Beanie-direct list, friendly tone, includes code + status + total |
| `test_estimates_count_all` | "how many estimates" → count form |
| `test_estimates_count_by_status` | "how many won estimates" → Beanie filter + count form |
| `test_estimates_count_by_division` | "how many in Design & Build" → Beanie filter + count form |
| `test_estimates_filter_by_status` | "show me draft estimates" → filtered list |
| `test_estimates_filter_by_division` | "list estimates in Maintenance" → filtered list |
| `test_estimates_sort_highest_total` | "what's my highest estimate?" → sorted + limit=1 |
| `test_estimates_sort_latest` | "show me the latest estimate" → sort by created_at desc, limit=1 |
| `test_estimates_sort_latest_n_with_explicit_count` | "show me the 5 most recent estimates" → sort by created_at desc, limit=5 |
| `test_estimates_sort_top_n_by_value` | "top 3 estimates" → sort by grand_total desc, limit=3 |
| `test_estimates_get_by_code` | "show estimate EST-2026-001" → get by `estimate_id` |
| `test_estimates_status_transition_archive` | "archive estimate EST-2026-001" → PATCH archive |
| `test_estimates_status_transition_won` | "mark EST-2026-001 as won" → update status |
| `test_estimates_status_transition_invalid_refuses` | "mark EST-2026-001 as generating" → refuse (not a user-facing status) |
| `test_estimates_delete_requires_confirmation` | "delete EST-2026-001" → confirm flow |
| `test_estimates_bulk_delete_refused` | "delete all estimates" → `BULK_DELETE_REFUSAL_MESSAGE` (existing guard) |
| `test_estimates_generate_phrasing_routes_to_pipeline` | "create an estimate for repaving …" — the CRUD branch must NOT short-circuit generation |
| `test_estimates_enum_help_statuses` | "what estimate statuses are there?" → enum help |
| `test_estimates_enum_help_divisions` | "what divisions are available?" → enum help |
| **Property link** | |
| `test_estimates_link_property_by_address` | "link EST-2026-001 to 123 Main St" → address resolves to property id, payload carries `property: ObjectId` |
| `test_estimates_unlink_property` | "remove the property from EST-2026-001" → payload sets `property: None` |
| `test_estimates_link_property_ambiguous_refuses` | Address matches two properties — returns numbered clarification |
| `test_estimates_filter_by_property` | "show estimates for 123 Main St" → filtered list |
| **Work Items** | |
| `test_estimates_add_work_item` | "add a work item 'build patio' to EST-2026-001" → `work_item_op=add`, new entry in `job_items` |
| `test_estimates_remove_work_item` | "remove the patio work item from EST-2026-001" → filtered out |
| `test_estimates_rename_work_item` | "rename the patio work item to stone patio" → `work_item_op=rename`, description updated |
| `test_estimates_update_work_item_division` | "change the division of the patio work item to Design/Build" → division enum validated |
| `test_estimates_update_work_item_invalid_division_refuses` | "change the division of the patio work item to Nonsense" → refuse (not an enum value) |
| `test_estimates_update_work_item_profit_margin_refuses` | "set profit margin on the patio work item to 20%" → refuse with a pointer to the UI (scope decision 2026-04-21) |
| `test_estimates_remove_last_work_item_refuses` | Mirrors the Materials "refuse to remove last size" guard — an estimate with zero work items makes no sense |
| `test_estimates_list_work_items_for_estimate` | "show me the work items for EST-2026-001" → list of names + divisions |
| `test_estimates_work_item_ambiguous_name_refuses` | Two work items share a name — return numbered clarification |
| **Activities** | |
| `test_estimates_add_activity_to_work_item` | "add a laying sod activity to the patio work item in EST-2026-001" → `activity_op=add`, new entry in the target work item's `activities` |
| `test_estimates_remove_activity_from_work_item` | "remove the excavation activity from the patio work item" → filtered out |
| `test_estimates_rename_activity` | "rename laying sod activity to sod installation" |
| `test_estimates_update_activity_role` | "change the role on the excavation activity to Foreman" → role_id resolved + snapshot updated |
| `test_estimates_list_activities_in_work_item` | "list activities in the patio work item" → response lists activity names |
| `test_estimates_activity_ambiguous_work_item_refuses` | Activity name exists in multiple work items — return clarification asking which work item |
| `test_estimates_mutation_triggers_recalculation` | Adding/removing a work item or activity re-runs the totals path; `sub_total` / `grand_total` reflect the change |
| `test_orchestrator_routes_list_estimates` | rule-layer routes plain "list estimates" without LLM |
| `test_orchestrator_routes_count_estimates_by_status` | rule-layer handles "how many won estimates" |
| `test_orchestrator_routes_add_work_item` | "add a work item to EST-2026-001" → the existing pattern at [agents/orchestrator/service.py:155](platform/agents/orchestrator/service.py#L155) resolves to `update_estimate` |

Once the Estimate agent is green on these, add estimate as a 5th resource to [_maple_coverage_data.py](platform/tests/_maple_coverage_data.py) `_CRUD_RESOURCES` so the 9-category Tier 1/Tier 2 matrix covers it automatically — same invariants as the other four.

### Implementation order

1. **Baseline failing tests** (TDD red) for the list/count/get surface — these will all fail against the current generation-only agent. ✅ shipped (4 agent tests red, 5 orchestrator tests already green)
2. **Envelope refactor** in EstimateAgent so `process(message, context)` returns the CRUD envelope when intent is a query; generation path keeps its existing shape internally but wraps into the CRUD envelope on return. ✅ shipped as a CRUD short-circuit at the top of `process()` — full signature normalization deferred (legacy generation keys still returned alongside the CRUD envelope for backward compatibility).
3. **Read surface** — list, get, count, filter by status/division, sort by total/date. ✅ shipped: status/division/property filters, count form, sort by `grand_total` / `created_at` with explicit-count support ("top 3 estimates", "5 most recent estimates"), ambiguity refusal for multi-match addresses.
4. **Status transitions** — archive / unarchive / mark won/lost/approved, with the whitelist guard. ✅ shipped.
5. **Property link** — resolve address → property id, support set/change/clear. Add the ambiguity refusal. ✅ shipped: `_handle_update_estimate` handles `link` / `unlink` sub-ops. Other `update_estimate` phrasings return an explicit "not yet supported" clarification pointing at the UI.
6. **Work Items CRUD — Phase 6a (remove + rename)** ✅ shipped with confirmation flow for remove (2026-04-21 safety decision mirrors delete-estimate). Refuse-remove-last guard + ambiguity refusal included.
6b. **Work Items CRUD — Phase 6b (add + update_field division)** — not yet shipped. Add sub-op interops with the router's existing generation-based "add work items" flow; update_field restricted to `division` per 2026-04-21 scope decision (financial fields UI-only).
7. **Activities CRUD** — **DROPPED 2026-04-21** at user direction. Activity-level mutations stay UI-only for now. Chat CRUD stops at the Work Item level.
8. **Delete with confirmation** ✅ shipped: every delete (exact or fuzzy match) prompts for confirmation via the pending state; only "yes" executes the hard-delete. Also added a work-item-op guard at the top of the delete_estimate router handler so phrasings like "remove work item X from estimate Y" misclassified as delete_estimate are redirected to the agent instead of destroying the estimate.
9. **Enum help** for statuses + divisions (reuse the existing HELP_ENUM path).
10. **Matrix extension** — add `"estimate"` to `_CRUD_RESOURCES`, regenerate the gap report, drive any remaining phrasings green.
11. **Docs** — add an Estimate section to [CLAUDE.md](CLAUDE.md) under the Maple policies block, including the work-item vocabulary, the confirmation-required policy for destructive mutations (delete_estimate, work_item_remove), and the ambiguity-refusal policy.

### Out of scope for this phase

- **Activities CRUD (dropped 2026-04-21)** — add/remove/rename/update_field on `ActivityItem` entries nested inside a Work Item is deferred indefinitely at user direction. Chat CRUD stops at the Work Item level. Activity management stays in the UI.
- **Material / Labour / Equipment line items inside a Work Item** — the cost-catalog line items remain UI-only regardless of what happens with Activities.
- **Numeric totals as user input** — `sub_total` / `grand_total` / line-item totals are computed. Chat never accepts them as inputs.
- **Arithmetic / reporting queries** ("what's the total of all won estimates this quarter?") — BI, not CRUD. Out of this phase.
- **Google Docs version management** from chat — out of Maple's chat surface.
- **Property / contact sub-filtering richer than a single-field equality match** — one filter field at a time for now.

## Out of scope (decided)

- **Equipment agent CRUD** — explicitly blocked by policy. See "Equipment requests are refused" section (kept below for reference). Not tested as a CRUD surface.
- **Estimate generation from chat** — the existing ReAct + gathering pipeline owns creation. Maple's Estimate drilldown adds the *query* and *light-CRUD* surface only; generation phrasings still delegate to the pipeline unchanged.
- **Test grouping under `tests/maple/`** — considered, **declined**. The current per-file structure (`test_<agent>.py` + `test_orchestrator_intents.py` + `test_maple_crud_coverage.py` + `test_text_utils.py`) is already thematic; the grouping suggested earlier would be pure file moves (no behavior change) with import-path churn that affects every existing test. The cost (touching ~10 imports across the codebase) outweighs the benefit (slightly tidier discovery). Revisit if/when the test directory grows past ~50 files.
- **Multi-turn / contextual follow-ups beyond field-then-value** — out of the current matrix scope. The implemented multi-turn flow handles "Update X" → "phone" → "555-1234" (a 3-turn pending-intent fulfillment). Anything richer ("...and its email?" anaphora, multi-resource cross-references) is deferred to the architectural-gaps conversation above.

---

## Reference: detailed policy texts (kept for posterity)

### Policy: bulk delete is forbidden (Maple only)

**Scope**: Maple (the AI agent) only. The HTTP API layer (`routers/*.py`) remains free to expose bulk-delete endpoints for UI-driven workflows. The concern is that Maple must never execute a bulk delete from a natural-language message; a single misclassification of "delete all contacts" could destroy all of a tenant's data.

Required behavior for any phrasing matching the bulk-delete pattern (delete verb + `all`/`every`/`wipe`/`my` + plural domain):
1. Classifier refuses to return `delete_{singular}` as a confident intent.
2. Response sets `needs_clarification=True` with `BULK_DELETE_REFUSAL_MESSAGE`.
3. Downstream agents reject bulk payloads defensively (belt-and-braces).

The `bulk` test category in [_maple_coverage_data.py](platform/tests/_maple_coverage_data.py) asserts the refusal — any phrasing that returns `delete_{singular}` is a **failing test** (safety violation).

### Policy: equipment requests are refused (not yet supported)

Equipment management isn't exposed through Maple at this time. Phrasings whose domain is equipment return an explicit refusal naming the four supported resources (`EQUIPMENT_REFUSAL_MESSAGE`) — not a generic "I didn't understand". The `equipment_blocked` test category asserts the refusal across both tiers.

### Vocabulary: People (Labour) vs Contact

- **Contact** = an individual associated with a property (e.g. "John Doe"). Has fields `first_name`, `last_name`, `phone`, `email`, `role` (HOME_OWNER / MANAGER / ADMINISTRATOR), address.
- **People** (a.k.a. **Labour** in code) = a catalog of role definitions (e.g. "Landscaper @ $50/hr"). Has fields `name` (the role title), `description`, `unit`, `cost`. Labour entries are templates, not individuals.

`DOMAIN_HINTS` for `contact` and `labour` are disjoint at the rule level (no shared keywords). The Contact `role` field is unrelated to the Labour resource — phrasings like "Update John Doe's role to Manager" must route to `update_contact` (or fall through to LLM rescue), and must **never** classify as `update_labour`. Regression tests in [tests/test_orchestrator_intents.py](platform/tests/test_orchestrator_intents.py) enforce this.

### Verification

1. **Tier 1 only (default, no API key needed)**: `cd platform && ./run_tests.sh tests/test_maple_crud_coverage.py -v` → green session with XFAIL markers on the architectural-gap categories.
2. **Full two-tier (requires `OPENAI_API_KEY`)**: `cd platform && ./run_tests.sh tests/test_maple_crud_coverage.py -m "" -v` → adds 111 real OpenAI calls, takes ~2-3 min. Both columns populate in the report.
3. **Read the report**: `platform/tests/reports/maple_crud_gap_report.md` shows per-category and per-resource counts, plus a per-case verdict (covered / LLM rescues / real gap).
