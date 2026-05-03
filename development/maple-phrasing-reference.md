# Maple Phrasing Reference

Canonical catalog of user phrasings Maple supports, organized by resource. Add new use cases you want Maple to handle; Claude will update the ✅/⚠️ status after wiring the classifier rule or confirming existing behavior.

**Last updated:** 2026-05-02 (Wave 4.1 follow-up #2 — broadened EST-code regex in all 5 estimate-anchored cross-resource patterns and the `get_estimate` total-query short-circuit to accept alphanumeric codes. Previous form `est[-_]\d+` only matched digit-only codes (`EST-0042`); platform routers actually emit alphanumeric codes (`EST-4E73F7BB`, `EST-2026-001`) per the existing `_ESTIMATE_CODE_PATTERN` in `agents/estimate/service.py`. New form `est[-_][a-z0-9][a-z0-9\-_]*` (case-insensitive) brings the cross-resource matcher into sync with the rest of the codebase. Lowercase hex codes still canonicalize to upper-case via the existing normalizer. Token convention table updated to show the broader code shape. Earlier in the day, Wave 4.1 follow-up — `show me estimates for {property} property` suffix form added to `_CROSS_RESOURCE_QUERY_PATTERNS` so phrasings like `Bob Residential property` route as `cross_type=property` (the trailing `property`/`properties` is stripped from the captured name). Contact-anchored gate tightened: replaced `_looks_like_person_name(original_message)` with a `fullmatch` on the captured slice in original case + leading-word stopword check. Phrasings that previously slipped through to the contact handler (`Bob Residential property`, `John Doe house`, `John Doe at 123 Main St`, `Sarah Lee site`) now fail the gate and fall through. Earlier in the day, xfail-wave-4.1 shipped — contact-anchored estimate list closed. New `_CONTACT_ANCHORED_ESTIMATE_PATTERN` (broad shape `estimates? for X`) lives outside the regex tuple so it can apply a person-name shape gate (`_looks_like_person_name`) against the original-case message; phrasings like `estimates for approval` / `estimates for concrete blocks` / lowercase `estimates for bob jones` fail the gate and fall through. Property-anchored pattern still wins for `estimates for property X` (more-specific match runs first inside `_match_cross_resource_query`). Estimate agent's `_handle_list_estimates` extends the cross-resource branch to handle `type=contact`: resolves via `find_contacts_by_full_name`, walks `Property.contacts` to a property-id set, then constrains `Estimate.property` to that set ($in for multi-match, equality for single). New `_format_contact_constraint_label` helper renders the contact display name in the response lead-in. Empty-result copy added: contact-not-found and contact-with-no-properties variants. Coverage matrix `estimate_outbound` category extended to 5 phrasings; Tier 1 now 127/127. Earlier the same day, xfail-wave-4 shipped — estimate ↔ property/contact outbound drilldowns closed. Workstream A: three new patterns in `_CROSS_RESOURCE_QUERY_PATTERNS` route `which property is this estimate {EST} linked to?` → `list_properties` and `which contact is this estimate {EST} for?` / `who is this estimate {EST} for?` → `list_contacts`, both with `filter_by={type=estimate, name=…}`. Property agent's `_list_properties_by_cross_resource` and Contact agent's new `_list_contacts_for_estimate` resolve the EST code via `find_estimate_by_code`, follow `Estimate.property` → load the linked Property, and (for contact target) intersect with `Property.contacts`. Contact responses lead with the property name as the join lead-in. Workstream B: a single combined pattern routes `(show me)? estimates? (for property|linked to (property)?) X` → `list_estimates` with `filter_by={type=property, name=…}`, anchored on the literal "property" or "linked to" so status phrasings like `estimates for approval` don't get claimed. Estimate agent's `_handle_list_estimates` extends the existing labour cross-resource branch to handle `type=property`: resolves via `find_properties_by_name_or_address`, then either pins `Estimate.property == X` (single match) or `{$in: [...]}` (multi-match). Coverage matrix gained `estimate_outbound` category (4 phrasings); Tier 1 now 126/126. §1.8 ⚠️ rows flipped to ✅. Earlier the same day: §1.8 cleanup — removed four stale ⚠️ duplicates that already shipped as ✅ in §1.1 via Workstream C; remaining ⚠️ rows are the four genuine estimate→property/contact outbound drilldowns now tracked by `plans/maple-xfail-wave-4-estimate-outbound.md`. — Earlier the same day, Wave 3 Workstream C shipped — Estimate filters and drilldowns closed: aggregated-value queries (`what is the total value of the open estimates`) compute a single `sum(grand_total)` across `DRAFT/APPROVED/REVIEW/WON`; date-range qualifiers (`from last week`, `this month`) constrain `created_at`; amount-range qualifiers (`over $10k`, `under $5000`) constrain `grand_total` with `k`/`m` suffix support. Estimate-anchored cross-resource drilldowns: `what materials does EST-… use?` and `what roles are on EST-…?` route via `_CROSS_RESOURCE_QUERY_PATTERNS` with `filter_by={type=estimate, name=…}`; Material and Labour agents resolve the estimate via the new `find_estimate_by_code` helper in `agents/cross_resource.py` and project the embedded `materials`/`labours` snapshots. Verbless `{status} {plural-domain}` phrasings now infer `action=list` when paired with a status/date/amount qualifier (`_has_list_qualifier` helper) so phrasings like `approved quotes over $10k` no longer fall through to clarification. — Earlier the same day, Wave 3 Workstream B shipped — Material query variants closed: orchestrator `_match_size_scoped_material_op` extended for `rename size A to B for X` (size_op=rename routing), new top-level rule for `how much does X cost?` (non-possessive cost query → `get_material`), and `_parse_price_range_filter` in `agents/material/service.py` actually filters `_handle_list_materials` results by `under/over $N`. Count-modifier phrasings (`how many different/types of materials`) confirmed already routing via the standard hint flow. Coverage matrix gained `material_query_variants` category (5 phrasings), Tier 1 now 122/122. — Earlier the same day, Wave 3 Workstream A shipped — `_BULK_DELETE_PATTERNS` extended in `agents/text_utils.py` to refuse partial-bulk phrasings (`delete the last/first/next/previous N <plural>`); §7.4 entries flipped ⚠️ → 🛑. — Earlier the same day: Stale-entry sweep — flipped three entries that were tagged ⚠️ but already covered by tests: §4.4 `how many materials do I have?` and `count my materials` exercised by `test_maple_crud_coverage.py` count category, §9.3 `guide to setting up a property` covered by `test_maple_help_coverage.py:445`. Removed a duplicate `How much does {material} cost?` row from §4.3 — canonical entry stays in §4.9. — Earlier the same day, Wave 2 Phase 2 of xfail backlog closed — cross-resource list responses are now actually filtered by the cross-resource constraint. The orchestrator emits a `filter_by` payload on classification; the router threads it into the agent's context dict; Contact, Property, and Estimate agents read it in their list handlers and run the join. Direct lookups (Property.contacts) and transitive joins via Estimate (`materials.material` / `labours.labour`) both supported. Backed by `agents/cross_resource.py` for shared name resolution. — Same day, Wave 2 Phase 1 closed routing for cross-resource phrasings ("who lives at X?", "what properties does X own?", "where is X used?", "what estimates use the X role?") as ✅ rule on Tier 1 across all four CRUD resources via `_match_cross_resource_query`. Tier 1 coverage now 117/117. — Wave 1 Phase 2 closed possessive (`X's <field>`) and field-targeted-update (`set X's <field> to Y`, `change/update the <field> of/on X to Y`) phrasings as ✅ rule across Property, Contact, Material, and Labour via `_match_possessive_or_field_targeted` + `FIELD_TO_DOMAIN`. Wave 1 Phase 1 closed §9.5 help gaps for onboarding synonyms, capability variants, implicit help phrasings, limitation queries, unit enums, work-item how-to, cross-domain link, and the property-pluralization defect. Consolidated §"Coverage blind spots" + §"Highest-value extensions" from the now-deleted `maple-input-coverage-audit.md` into new §11; deleted `maple-coverage-gaps-estimate-material-size.md` as its work shipped in Phase A + Phase B and the locked decisions are captured under §1.1, §1.2, §4.8).

## How to read this doc

Each phrasing shows expected routing — the **intent** the orchestrator picks and the **agent** that handles it — plus its status:

- ✅ **rule** — handled deterministically by the rule-based classifier (`use_llm=False`). Works without an OpenAI key.
- 🤖 **LLM** — works on the live-LLM tier only (`use_llm=True`). Robust to paraphrase but slower and requires an OpenAI key.
- ⚠️ **gap** — not handled today. Use cases here are candidates for new classifier rules or handler work.
- 🛑 **refusal** — Maple is explicitly designed to refuse this phrasing (e.g., bulk delete, equipment management).

Token conventions used throughout:

| Placeholder | Example |
|---|---|
| `{property}` | `123 Main St` |
| `{contact}` | `John Doe` |
| `{material}` | `concrete blocks` |
| `{role}` | `Landscaper` |
| `{EST}` | `EST-0042`, `EST-4E73F7BB`, `EST-2026-001` (alphanumeric — anything matching `EST[-_][A-Za-z0-9\-_]*`) |
| `{size}` | `12x12` |
| `{unit}` | `each`, `sq ft`, `linear ft` |

## Terminology note — the 4 + 1 Maple resources

| User-facing | Code domain | What it represents |
|---|---|---|
| **Property** | `property` | Job sites / addresses |
| **Contact** | `contact` | **Individuals** at a property (homeowner, manager, etc.) |
| **Material** | `material` | Catalog of physical products with sizes/prices |
| **People** | `labour` | Catalog of **role definitions** (Landscaper, Foreman). NOT individuals — that's Contact. |
| **Estimate** | `estimate` | Quotes / job costings. Generated by an AI agent from a job description. |

Equipment is **explicitly blocked** via `is_equipment_request()` at the orchestrator layer — see §7.

## How to add new use cases

1. Add the phrasing under the appropriate resource section with status ⚠️ gap. Include the intended intent/agent if you have one.
2. Ping Claude with "add these phrasings to Maple" — Claude will write failing tests, implement the rule, and flip the status to ✅ here.
3. For phrasings that should be refused, add under §7 with status 🛑 and note why.

Tests live in `platform/tests/test_maple_crud_coverage.py` (matrix) and `platform/tests/test_maple_*.py` (targeted). Running the matrix regenerates `platform/tests/reports/maple_crud_gap_report.md` with live pass/fail counts.

---

# 1. Estimates

Estimate is not in the CRUD coverage matrix — its generation is multi-turn and its operations (status transitions, work items, linking) don't fit the generic category templates. These are curated.

## 1.1 Count & status queries

| Phrasing                                             | Intent → Agent                                                 | Status                                                                                                                                                                                                                                                              |
| ---------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `how many estimates do I have?`                      | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `count my estimates`                                 | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `how many estimates with status draft?`              | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `what's the total estimates with status approved?`   | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `can you add up the estimates with status approved?` | `list_estimates` → Estimate Agent                              | ✅ rule *(closed in Phase A1)*                                                                                                                                                                                                                                       |
| `how many approved estimates do I have?`             | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `count my draft quotes` (quotes = synonym)           | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `what is the total value of the open estimates`      | aggregated `sum(grand_total)` across DRAFT/APPROVED/REVIEW/WON | ✅ rule *(closed in xfail-wave-3 Workstream C — `_AGGREGATE_VALUE_QUERY_PATTERN` + `_OPEN_ESTIMATE_QUERY_PATTERN` short-circuit `_handle_list_estimates` to a single dollar figure)*                                                                                 |
| `show me draft estimates from last week`             | `list_estimates` with `created_at` window                      | ✅ rule *(closed in xfail-wave-3 Workstream C — `_parse_estimate_date_filter` adds a `$gte/$lte` constraint on `created_at`)*                                                                                                                                        |
| `approved quotes over $10k`                          | `list_estimates` with status + `grand_total` range             | ✅ rule *(closed in xfail-wave-3 Workstream C — verbless plural-domain inference + `_parse_estimate_amount_filter` adds a `$gt`/`$lt` constraint on `grand_total`; `k`/`m` suffixes supported)*                                                                      |
| `what materials does {EST} use?`                     | `list_materials` filtered to one estimate's snapshot           | ✅ rule *(closed in xfail-wave-3 Workstream C — orchestrator routes via `_CROSS_RESOURCE_QUERY_PATTERNS` with `filter_by={type=estimate, name=EST-…}`; Material agent's `_handle_list_materials_for_estimate` resolves and projects the embedded `materials` array)* |
| `what roles are on {EST}?`                           | `list_labours` filtered to one estimate's snapshot             | ✅ rule *(closed in xfail-wave-3 Workstream C — symmetric Labour-agent drilldown via `_handle_list_labours_for_estimate`)*                                                                                                                                           |

## 1.2 Value / total queries for a specific estimate

| Phrasing                               | Intent → Agent                  | Status                        |
| -------------------------------------- | ------------------------------- | ----------------------------- |
| `what is the value of estimate {EST}?` | `get_estimate` → Estimate Agent | ✅ rule                        |
| `what's the total for {EST}?`          | `get_estimate` → Estimate Agent | ✅ rule *(closed in Phase A2)* |
| `how much is {EST}?`                   | `get_estimate` → Estimate Agent | ✅ rule *(closed in Phase A3)* |
| `what's the grand total for {EST}?`    | `get_estimate` → Estimate Agent | ✅ rule                        |
| `worth of {EST}`                       | `get_estimate` → Estimate Agent | ✅ rule                        |

Handler: `_handle_get_estimate` detects `_GRAND_TOTAL_QUERY_PATTERN` and leads the response with the dollar amount.

## 1.3 Generation (multi-turn, LLM-driven)

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `create an estimate for {property} — needs 20 yards of concrete and two landscapers` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `draft a quote for a driveway replacement at 456 Oak Ave` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `I need an estimate for [job description]` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `create a residential estimate` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `new commercial quote` | `create_estimate` → Estimate Agent | 🤖 LLM |

Handled by `agents/estimate/conversation_guide.py`. The EstimateAgent walks the user through job description → material/equipment/labour recommendations → estimate creation.

## 1.4 Status transitions

EstimateStatus values: `DRAFT`, `APPROVED`, `WON`, `LOST`, `ONHOLD`, `SCHEDULED`, `COMPLETED`, `SUBMITTED`, `REVIEW`, `ARCHIVED`.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `approve {EST}` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `mark {EST} as approved` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `reject the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `send {EST} for review` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `put {EST} on hold` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `move this estimate to draft` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `what's the status of {EST}?` | `get_estimate` → Estimate Agent | 🤖 LLM |

## 1.5 Work-item / line-item management

Regex rules live at `agents/orchestrator/service.py:230-248`.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add a work item to the estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a job item to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a scope to the last estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a line item to this estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `create another scope on {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `change work item #1 in {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove work item 2 from this estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `rename the scope to Foundation` | `update_estimate` → Estimate Agent | ✅ rule |

## 1.6 Linking

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `link {EST} to {property}` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `attach this estimate to {property}` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `which property is this estimate for?` | `get_estimate` → Estimate Agent | 🤖 LLM |

## 1.7 Anaphora / active estimate

When session context carries `active_estimate_code` (user recently worked on an estimate):

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add a Landscaper to the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM + context |
| `update the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM + context |
| `show me the estimate` | `get_estimate` → Estimate Agent | 🤖 LLM + context |
| `this estimate` / `the last estimate` / `that one` | resolves via `active_estimate_code` | 🤖 LLM + context |

## 1.8 Estimate ↔ property/contact outbound drilldowns

Closed in xfail-wave-4 + 4.1 (plan: [maple-xfail-wave-4-estimate-outbound.md](plans/maple-xfail-wave-4-estimate-outbound.md)). Routes through `_CROSS_RESOURCE_QUERY_PATTERNS` with three cross-types:
- `cross_type=estimate` (Wave 4 Workstream A) — Property/Contact agents resolve the EST code via `find_estimate_by_code` and follow `Estimate.property` → `Property.contacts`.
- `cross_type=property` (Wave 4 Workstream B) — Estimate agent resolves the property via `find_properties_by_name_or_address` and constrains by `Estimate.property`.
- `cross_type=contact` (Wave 4.1) — Estimate agent resolves the contact via `find_contacts_by_full_name`, walks `Property.contacts` to a property-id set, then constrains `Estimate.property in [...]`.

| Phrasing                                           | Intent → Agent                                                                       | Status |
| -------------------------------------------------- | ------------------------------------------------------------------------------------ | ------ |
| `which property is this estimate {EST} linked to?` | `list_properties` → Property Agent (resolve estimate → return its linked property)   | ✅ rule *(Workstream A)* |
| `which contact is this estimate {EST} for?` (also without the `this`, e.g. `which contact is estimate EST-4E73F7BB for?`) | `list_contacts` → Contact Agent (resolve estimate → property → contacts) | ✅ rule *(Workstream A)* |
| `who is this estimate {EST} for?`                  | `list_contacts` → Contact Agent (response leads with the property name as join lead-in) | ✅ rule *(Workstream A)* |
| `show me estimates for property {property}`        | `list_estimates` → Estimate Agent (resolve property by name/address → constrain by `Estimate.property`) | ✅ rule *(Workstream B)* |
| `estimates linked to {property}` / `what estimates are for property {property}` | same as above | ✅ rule *(Workstream B)* |
| `show me estimates for {property} property` (suffix form, e.g. `Bob Residential property`) | `list_estimates` → Estimate Agent (suffix `property` strips from captured name) | ✅ rule *(Wave 4.1 follow-up)* |
| `show me estimates for {contact}` (capitalized name) | `list_estimates` → Estimate Agent (transitive: resolve contact → properties → estimates) | ✅ rule *(Wave 4.1)* |

**Empty-result copy** (so the user sees why nothing matched, instead of an empty list):
- Estimate not found → *"I couldn't find an estimate with code '{EST}'."*
- Estimate exists but `property` is `None` → *"Estimate {EST} isn't linked to a property yet."*
- Property linked but missing contacts → *"Estimate {EST} is linked to {property}, but that property has no contacts yet."*
- No property matches the constraint name → *"I couldn't find a property matching '{name}'."*
- No contact matches the constraint name → *"I couldn't find a contact matching '{name}'."*
- Contact resolves but isn't linked to any property → *"{Name} isn't linked to any properties yet, so there are no estimates to show."*

**Anchoring rules:**
- Property-anchored Workstream B fires on either the prefix form (`for property X` / `linked to (property)? X`) OR the suffix form (`for X property` / `for X properties`). Status phrasings like `estimates for approval` / `estimates for review` don't match (no `property` or `linked to` token).
- Contact-anchored Wave 4.1 uses a broad `estimates? for X` shape gated by a `fullmatch` on the captured slice in original case: it must be exactly a 2+ word capitalized name. `Bob Residential property` (trailing noun), `John Doe at 123 Main St` (locator suffix), and `bob jones` (lowercase) all fail the gate and fall through. Property-anchored patterns are checked first inside the same matcher, so `estimates for property Bob Jones` and `estimates for Bob Residential property` both win as `cross_type=property` before the contact gate runs.

---

# 2. Properties

## 2.1 Direct imperatives (all ✅ rule)

| Phrasing | Intent → Agent |
|---|---|
| `create a new property` | `create_property` → Property Agent |
| `list all properties` | `list_properties` → Property Agent |
| `delete the property {property}` | `delete_property` → Property Agent |

## 2.2 Casual phrasings (all ✅ rule)

| Phrasing | Intent → Agent |
|---|---|
| `show me my properties` | `list_properties` → Property Agent |
| `what properties do I have?` | `list_properties` → Property Agent |
| `pull up property {property}` | `get_property` → Property Agent |

## 2.3 Possessive

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me {property}'s details` | `get_property` → Property Agent | ✅ rule |
| `what's {property}'s city?` | `get_property` → Property Agent | ✅ rule |
| `update {property}'s record` | `update_property` → Property Agent | ✅ rule |

## 2.4 Count (all ✅ rule)

`how many properties do I have?` · `count my properties` · `total number of properties`

## 2.5 Filter / find (all ✅ rule)

`find properties named Toronto` · `show properties in Toronto` · `search for properties matching Toronto`

## 2.6 Field-targeted update

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `change the city of {property} to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `update the city on {property} to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `set {property}'s city to Vancouver` | `update_property` → Property Agent | ✅ rule |

## 2.7 Address formats accepted on create (all ✅ rule)

The regex fallback in `_extract_fields_from_message` parses these single-line formats so the user can supply a complete address in one message:

| Format | Example |
|---|---|
| Canadian, comma-separated with postal | `123 Main Street, Vancouver, BC, V1V 2A2` |
| Canadian, comma-separated with country | `123 Main Street, Vancouver, BC, Canada, V1V 2A2` (or postal-then-country) |
| Canadian, partial (street + city + state) | `888 River Road, Richmond, BC` |
| Canadian, "at" prefix space-separated state | `at 123 Maple Drive, Surrey BC V3T 4R5` |
| **US, "City, ST ZIP"** (no comma between state and ZIP) | `155 Asharoken Ave, Northport, NY 11768` |
| **US, ZIP+4** | `155 Asharoken Ave, Northport, NY 11768-1234` |

Comma-less unformatted addresses (`1036 Fort Salonga Rd Northport NY`) are intentionally **not** parsed by regex — the LLM entity extractor handles them.

## 2.8 Verbless (all ✅ rule — Phase 2a address-pattern resolver)

| Phrasing | Intent → Agent |
|---|---|
| `{property}` (bare address) | `get_property` → Property Agent |
| `I want the details for {property}` | `get_property` → Property Agent |
| `tell me about {property}` | `get_property` → Property Agent |

## 2.9 Property gaps

No outstanding property-specific gaps in scope for the current backlog. Cross-resource phrasings (e.g. `who lives at {property}?`) are tracked under §6.

---

# 3. Contacts

## 3.1 Direct imperatives (all ✅ rule)

`create a new contact` · `list all contacts` · `delete the contact {contact}`

## 3.2 Casual phrasings (all ✅ rule)

`show me my contacts` · `what contacts do I have?` · `pull up contact {contact}`

## 3.3 Possessive

| Phrasing | Status |
|---|---|
| `show me {contact}'s details` | ✅ rule |
| `what's {contact}'s phone?` | ✅ rule |
| `update {contact}'s record` | ✅ rule |

## 3.4 Count (all ✅ rule)

`how many contacts do I have?` · `count my contacts` · `total number of contacts`

## 3.5 Filter / find (all ✅ rule)

`find contacts named Smith` · `show contacts in Toronto` · `search for contacts matching Smith`

## 3.6 Field-targeted update

| Phrasing | Status |
|---|---|
| `change the phone of {contact} to 555-1111` | ✅ rule |
| `update the phone on {contact} to 555-1111` | ✅ rule |
| `set {contact}'s phone to 555-1111` | ✅ rule |

## 3.7 Verbless (all ✅ rule — Phase 2b person-name heuristic)

`{contact}` (bare name) · `I want the details for {contact}` · `tell me about {contact}`

## 3.8 Contact gaps

No outstanding contact-specific gaps in scope for the current backlog. Cross-resource phrasings (e.g. `where does {contact} live?`) are tracked under §6.

---

# 4. Materials

## 4.1 Direct imperatives (all ✅ rule)

`create a new material` · `list all materials` · `delete the material {material}`

## 4.2 Casual phrasings (all ✅ rule)

`show me my materials` · `what materials do I have?` · `pull up material {material}`

## 4.3 Possessive

| Phrasing                         | Intended behavior          | Status |
| -------------------------------- | -------------------------- | ------ |
| `show me {material}'s details`   | `get_material`             | ✅ rule |
| `what's {material}'s price?`     | `get_material` field focus | ✅ rule |
| `update {material}'s record`     | `update_material`          | ✅ rule |

## 4.4 Count

| Phrasing                                  | Intended behavior | Status |
| ----------------------------------------- | ----------------- | ------ |
| `how many different materials do I have?` | count materials   | ✅ rule |
| `how many types of materials do I have?`  | count materials   | ✅ rule |
| `how many materials do I have?`           | count materials   | ✅ rule |
| `count my materials`                      | count materials   | ✅ rule |

The "different" / "types of" modifiers don't change the routing — `how many` already pins the action to ``list`` and the trailing ``materials`` pins the domain. Confirmed via `material_query_variants` coverage category.

## 4.5 Filter / find (all ✅ rule)

`find materials named concrete` · `show materials in in stock` · `search for materials matching concrete`

## 4.6 Field-targeted update (material-level)

| Phrasing | Status |
|---|---|
| `change the price of {material} to $5` | ✅ rule |
| `update the price on {material} to $5` | ✅ rule |
| `set {material}'s price to $5` | ✅ rule |

Closed by Phase 2 of xfail-wave-1 — `_match_possessive_or_field_targeted` resolves the missing material domain via `FIELD_TO_DOMAIN["price"] → material` plus the material-shape residual on the captured entity name.

## 4.7 Verbless (all ✅ rule — Phase 2b material-shape residual)

`{material}` · `I want the details for {material}` · `tell me about {material}`

## 4.8 Size-scoped operations *(shipped in Phase B — all ✅ rule)*

All size-scoped phrasings require an explicit `size <X>` token to fire. Material Agent's `_build_sizes_from_fields` handles the payload; `_handle_update_material` enforces the last-size refusal and add-size missing-field refusal.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `find material {material} with size {size}` | `get_material` (size-scoped) | ✅ rule |
| `how much is {material} with size {size}?` | `get_material` (size-scoped) | ✅ rule |
| `update the cost for {material} with size {size} to $5` | `update_material` (size-scoped cost) | ✅ rule |
| `update the price for {material} with size {size} to $5` | `update_material` (size-scoped price) | ✅ rule |
| `delete size {size} for {material}` | `update_material` (size_op=remove) | ✅ rule |
| `add size {size} to {material} with cost $8 and unit each` | `update_material` (append) | ✅ rule |

**Invariants:**
- **Last-size delete refusal** — cannot remove the only remaining size on a material. Copy: *"I can't remove the last size from this material — it needs at least one size. Add another size first, or delete the material entirely if that's what you mean."*
- **Add-size requires BOTH cost and unit** — `add size {size} to {material} with cost $8` (no unit) refuses and prompts for the unit. Same if cost is missing.

## 4.9 Material gaps

| Phrasing | Intended behavior | Status |
|---|---|---|
| `How much does {material} cost?` | `get_material` field focus | ✅ rule *(closed in xfail-wave-3 Workstream B — non-possessive cost-query rule in orchestrator)* |
| `list materials under $10` | `list_materials` with price range | ✅ rule *(closed in xfail-wave-3 Workstream B — `_parse_price_range_filter` in `agents/material/service.py` filters the list response by `under/over/below/above $N`)* |
| `rename size {old} to {new} for {material}` | `update_material` (size_op=rename) | ✅ rule *(closed in xfail-wave-3 Workstream B — orchestrator `_match_size_scoped_material_op` rule routes the rename verb)* |
| `show all sizes for {material}` | `get_material` | 🤖 LLM |

---

# 5. People (roles) — a.k.a. Labour

Labour = catalog of **role definitions** (Landscaper, Foreman, Operator). Individuals go under Contact.

## 5.1 Direct imperatives (all ✅ rule)

`create a new labour role` · `list all labour roles` · `delete the labour role {role}`

## 5.2 Casual phrasings (all ✅ rule)

`show me my labour roles` · `what labour roles do I have?` · `pull up labour role {role}`

## 5.3 Possessive

| Phrasing | Status |
|---|---|
| `show me {role}'s details` | ✅ rule |
| `what's {role}'s cost?` | ✅ rule |
| `update {role}'s record` | ✅ rule |

## 5.4 Count (all ✅ rule)

`how many labour roles do I have?` · `count my labour roles` · `total number of labour roles`

## 5.5 Filter / find (all ✅ rule)

`find labour roles named Foreman` · `show labour roles in outdoor` · `search for labour roles matching Foreman`

## 5.6 Field-targeted update

| Phrasing | Status |
|---|---|
| `change the cost of {role} to $50` | ✅ rule |
| `update the cost on {role} to $50` | ✅ rule |
| `set {role}'s cost to $50` | ✅ rule |

## 5.7 Verbless (all ✅ rule — DOMAIN_HINTS include role names)

`{role}` · `I want the details for {role}` · `tell me about {role}`

## 5.8 People gaps

No outstanding people-specific gaps in scope for the current backlog. Cross-resource phrasings (e.g. `which properties need a {role}?`) are tracked under §6.

---

# 6. Cross-resource / implicit relationships

Questions users ask when they think about the domain rather than the database. Routing is via `_match_cross_resource_query` in the orchestrator (Wave 2 Phase 1); the join is performed by the target agent reading a `filter_by` payload off `context` (Wave 2 Phase 2). Direct lookups (Property↔Contact) hit the linked-id list on the Property document; transitive joins (material/labour → property) go through the Estimate collection's embedded `materials.material` / `labours.labour` lists.

## 6.1 Property ↔ Contact

| Phrasing | Intended behavior | Status |
|---|---|---|
| `who lives at {property}?` | `list_contacts` filtered by property | ✅ rule |
| `what contacts are at {property}?` | `list_contacts` filtered by property | ✅ rule |
| `who owns {property}?` | `list_contacts` filtered by property + role=owner | ✅ rule |
| `what properties does {contact} own?` | `list_properties` filtered by contact | ✅ rule |
| `where does {contact} live?` | `list_properties` filtered by contact | ✅ rule |
| `show me {contact}'s properties` | `list_properties` filtered by contact | ✅ rule (possessive flow) |

## 6.2 Material → Property / Estimate

| Phrasing | Intended behavior | Status |
|---|---|---|
| `which properties use {material}?` | `list_properties` joined via estimates | ✅ rule |
| `where is {material} used?` | `list_properties` joined via estimates | ✅ rule |
| `find estimates with {material}` | `list_estimates` filtered by material | ✅ rule (plural-aware list flip) |

## 6.3 Labour → Property / Estimate

| Phrasing | Intended behavior | Status |
|---|---|---|
| `which properties need a {role}?` | `list_properties` joined via estimates | ✅ rule |
| `what estimates use the {role} role?` | `list_estimates` filtered by labour | ✅ rule |
| `show me jobs needing a {role}` | `list_properties` joined via estimates | ✅ rule (plural-aware list flip) |

---

# 7. Safety refusals

## 7.1 Bulk delete — 🛑 refused

Phrasings with quantifier + delete verb. Enforced at the orchestrator layer AND defensively at each domain agent's `process()`.

| Phrasing | Behavior |
|---|---|
| `delete all {plural}` | 🛑 refusal message, `needs_clarification=True` |
| `remove every {singular}` | 🛑 refusal |
| `wipe my {plural}` | 🛑 refusal |

Applies to all 4 CRUD resources. Maple-only policy — HTTP routers may still expose bulk delete for UI workflows.

## 7.2 Equipment — 🛑 refused

Equipment isn't a Maple resource. Any phrasing mentioning equipment (excavator, skid steer, bobcat, etc.) refuses with `EQUIPMENT_REFUSAL_MESSAGE`.

| Phrasing | Behavior |
|---|---|
| `show all my equipment` | 🛑 refusal |
| `create a new equipment` | 🛑 refusal |
| `delete the excavator equipment` | 🛑 refusal |

## 7.3 Material category management — 🛑 refused

Material categories (Hardscape, Masonry, etc.) live in the catalog UI. Maple can list/filter/reassign but not create/rename/delete them.

| Phrasing | Behavior |
|---|---|
| `create a new category` | 🛑 refusal via `is_material_category_management_request` |
| `rename the Masonry category` | 🛑 refusal |
| `delete the Hardscape category` | 🛑 refusal |

## 7.4 Partial bulk / small-N destructive — 🛑 refusal

| Phrasing | Intended behavior | Status |
|---|---|---|
| `delete the last 5 contacts` | Refuse (N > 1 but not "all") | 🛑 refusal — extended `_BULK_DELETE_PATTERNS` to catch `last/first/next/previous N` quantifiers (xfail-wave-3 Workstream A) |
| `remove the first 10 properties` | Refuse | 🛑 refusal |
| `drop the next 3 materials` | Refuse | 🛑 refusal |

---

# 8. Multi-turn patterns

## 8.1 Field-then-value flow (all 4 CRUD resources)

User responds to "What fields should I update?" with a bare field name:

```
User: update Landscaper
Maple: What fields should I update? (options: cost, description, ...)
User: cost
Maple: What's the new cost?
User: $50
Maple: I've updated the cost for Landscaper for you.
```

Pending-intent slot: `awaiting_value_for`. Canonical implementation: `agents/property/service.py`.

## 8.2 Add-size missing-field flow (materials)

When user says "add size {size} to {material}" without providing cost or unit:

```
User: add size 24x24 to concrete blocks with cost $8
Maple: I need a unit for size '24x24' on concrete blocks. Try again with cost and unit — for example: "add size 24x24 to concrete blocks with cost $10 and unit each".
```

Currently refuses and requests a retry with complete info (pending-intent persistence is a future UX refinement).

---

# 9. Help intent

Handled by `agents/orchestrator/help_handler.py` via the `HelpHandler` class. The orchestrator routes to it when `is_help_query()` returns True (see `agents/orchestrator/intents.py:296`). The agent is always the **Orchestrator Agent** itself — help never dispatches to a downstream domain agent.

Three topic families, in order of priority inside `HelpHandler.detect_topic()`:

1. **Enum queries** — contact roles, estimate statuses, estimate divisions. Returns the enum's valid values plus a `valid_values` list in the result payload.
2. **Capabilities** — "what can you do?". Returns the `SUPPORTED_INTENTS_BY_AGENT` mapping under `result.capabilities`.
3. **Procedural (how-to)** — instructional patterns like "how do I", "steps to", "walk me through". Attempts to load a user guide from `user_guides/content.py`; falls back to a contextual example from `_CONTEXTUAL_EXAMPLES` if no guide exists.

The result payload always has `operation="help"`, `read_only=True`, and an `intent="help"` on the envelope. Help queries are rule-only — they bypass the LLM even when `use_llm=True` (see `test_orchestrator_help_query_bypasses_llm`).

## 9.1 Capability queries

Direct capability questions. Match via `HELP_DIRECT_HINTS` (`intents.py:184`).

| Phrasing | Topic | Status |
|---|---|---|
| `help` | `capabilities` | ✅ rule |
| `help me` | `capabilities` | ✅ rule |
| `help please` | `capabilities` | ✅ rule |
| `I need help` | `capabilities` | ✅ rule |
| `what can you help me with?` | `capabilities` | ✅ rule |
| `what can you do?` | `capabilities` | ✅ rule |
| `how can you help me?` | `capabilities` | ✅ rule |
| `what can I ask?` | `capabilities` | ✅ rule |
| `supported intents` | `capabilities` | ✅ rule |
| `capabilities` | `capabilities` | ✅ rule |

## 9.2 Enum queries

Match via `HELP_ENUM_KEYWORDS` + `HELP_QUESTION_CUES` (`intents.py:194-218`). `HelpHandler.detect_topic()` disambiguates by domain keyword.

### Contact roles — returns `["Home Owner", "Manager", "Administrator"]`

| Phrasing | Status |
|---|---|
| `what are the contact roles?` | ✅ rule |
| `what are the valid contact roles?` | ✅ rule |
| `what roles are available?` | ✅ rule |
| `what are the valid roles for a contact?` | ✅ rule |
| `available values for role` | ✅ rule |
| `choices for contact role` | ✅ rule |

### Estimate statuses — returns the 10 EstimateStatus enum values

| Phrasing | Status |
|---|---|
| `what are the estimate statuses?` | ✅ rule |
| `what statuses can an estimate have?` | ✅ rule |
| `what are the valid estimate statuses?` | ✅ rule |

### Estimate divisions — returns EstimateDivision enum values

| Phrasing | Status |
|---|---|
| `what are the estimate divisions?` | ✅ rule |
| `what are the valid estimate divisions?` | ✅ rule |
| `which divisions can an estimate have?` | ✅ rule |

## 9.3 Procedural how-to queries

Match via `HELP_INSTRUCTIONAL_PATTERNS` (`intents.py:220-237`): `how do i`, `how can i`, `how to`, `how would i`, `how should i`, `steps to`, `step by step`, `process for`, `process to`, `guide for`, `guide to`, `explain how`, `show me how`, `walk me through`, `what are the steps`, `what's the process`.

When an instructional pattern hits, `detect_topic()` tries to match an action keyword (`create`, `update`, `delete`, `list`, `get`, `find`, `add`, `edit`, `remove`) and a domain keyword (`contact(s)`, `estimate`/`quote(s)`, `property`/`properties`, `material(s)`, `labour`/`labor`). Result is a `how_to_<action>_<domain>` topic; falls back to `how_to_manage_<domain>s` if only domain matched, or `how_to_use_system` if neither.

### Full how-to (action + domain matched)

| Phrasing                             | Topic                     | Status                                                       |
| ------------------------------------ | ------------------------- | ------------------------------------------------------------ |
| `how do I create an estimate?`       | `how_to_create_estimate`  | ✅ rule (guide loaded from `user_guides/content.py`)          |
| `how do I update a contact?`         | `how_to_update_contact`   | ✅ rule (guide loaded)                                        |
| `how do I create a contact?`         | `how_to_create_contact`   | ✅ rule (guide loaded)                                        |
| `how do I create a property?`        | `how_to_create_property`  | ✅ rule (guide loaded)                                        |
| `how do I archive an estimate?`      | `how_to_manage_estimates` | ✅ rule *(no action keyword "archive", falls back to manage)* |
| `steps to add a material`            | `how_to_add_material`     | ✅ rule (no guide; contextual example)                        |
| `explain how to create an estimate`  | `how_to_create_estimate`  | ✅ rule                                                       |
| `walk me through making a contact`   | `how_to_manage_contacts`  | ✅ rule *("making" isn't an action keyword)*                  |
| `how can I update a material price?` | `how_to_update_material`  | ✅ rule                                                       |
| `how do I approve an estimate?`      | `how_to_manage_estimates` | ✅ rule *("approve" not an action keyword)*                   |

### Domain-only how-to (no action keyword matched)

| Phrasing | Topic | Status |
|---|---|---|
| `guide to setting up a property` | `how_to_manage_properties` | ✅ rule (pluralization defect closed by Wave 1 Phase 1) |
| `what's the process for archiving an estimate?` | `how_to_manage_estimates` | ✅ rule |

### Generic how-to (no action, no domain)

| Phrasing | Topic | Status |
|---|---|---|
| `how do I use this system?` | `how_to_use_system` | ✅ rule |
| `show me how to use Maple` | `how_to_use_system` | ✅ rule |
| `how to get started` | `how_to_use_system` | ✅ rule |

## 9.4 Help vs. CRUD precedence

When a message contains **both** a CRUD intent (firm action+domain match) and an enum keyword, CRUD usually wins. Two important carve-outs:

| Phrasing | Result | Why |
|---|---|---|
| `help me create a contact for Jane` | `create_contact` → Contact Agent | "help me" is a polite prefix, not an instructional question. CRUD action+domain is firm. |
| `how many labour roles do I have?` | `list_labours` → Labour Agent | `action == "list"` short-circuit at `intents.py:321` prefers CRUD over help even though "roles" is an enum keyword. |
| `what are the material categories?` | `list_material_categories` → Orchestrator Agent | Rule-level CRUD match fires before help classifier. See §7.3 refusal for create/delete variants. |
| `how do I create a contact?` | `help` → Orchestrator Agent | Instructional pattern ("how do i") always wins over CRUD — `intents.py:310-311`. |

## 9.5 Help gaps

Phase 1 of the xfail backlog (plan: `documentation/development/plans/maple-xfail-wave-1.md`) closed most §9.5 entries on 2026-05-02. Remaining gaps below are awaiting Wave 2 design work.

| Phrasing | Intended behavior | Status |
|---|---|---|
| `tutorial` / `getting started` / `docs` / `documentation` | `capabilities` topic via `HELP_DIRECT_HINTS` | ✅ rule (Phase 1). |
| `examples` / `give me some examples` / `what kinds of things can I ask?` | `capabilities` topic | ✅ rule (Phase 1). |
| `what can't you do?` / `what are your limitations?` | `general_question` via interrogative guide-fallback | ✅ rule (already covered before Phase 1). |
| `does Maple support X?` / `is there a way to do X?` | `capabilities` / `general_question` via help routing | ✅ rule (Phase 1) — equipment refusal now gated by `_looks_interrogative`; `is there a way` and `does maple support` added to `HELP_INSTRUCTIONAL_PATTERNS`. |
| `what is a work item?` / `what's a property?` | Glossary / terminology help via guide-fallback | ✅ rule (already covered). |
| `what fields does a contact have?` | Schema help — return Pydantic model fields | ✅ rule (already covered via fallback). |
| `what happens when I approve an estimate?` / `what does archive do?` | Action-semantics help | ✅ rule (already covered via fallback). |
| `how does Maple work?` / `explain Maple to me` / `what do you do?` | `capabilities` topic | ✅ rule (Phase 1). |
| `what are the labour units?` / `what are the material units?` | `labour_units` / `material_units` topics | ✅ rule (Phase 1) — `unit`/`units` added to `HELP_ENUM_KEYWORDS`; new §3.13 + §3.14 in `users_guide.md` provide source content. |
| `I am lost` / `I am stuck` | `capabilities` topic | ✅ rule (Phase 1). |
| `what should I ask?` / `what can I do?` | `capabilities` topic | ✅ rule (Phase 1). |
| `list your features` | `capabilities` topic | ✅ rule (Phase 1). |
| `how do I add a work item?` | `how_to_manage_estimates` (estimate line-item alias) | ✅ rule (Phase 1) — `work item`/`job item`/`line item` detected and routed to estimate scope. |
| `how do I link a contact to a property?` | `how_to_link_contact_property` topic | ✅ rule (Phase 1) — cross-domain detection runs before single-domain loop; new §3.12 in `users_guide.md`. |

### Pluralization defect — `how_to_manage_propertys` (closed Phase 1)

`HelpHandler.detect_topic` previously returned `f"how_to_manage_{domain_name}s"`, which produced `how_to_manage_propertys` for the property domain. Phase 1 introduced an inline `plural_topic` map (`property → properties`, others append `s`) so the topic key round-trips correctly to `how_to_manage_properties`.

---

# 10. Appendix

## 10.1 Where tests live

| Path | Purpose |
|---|---|
| `platform/tests/test_maple_crud_coverage.py` | Matrix — 117 phrasings × Tier 1 + Tier 2 |
| `platform/tests/_maple_coverage_data.py` | Matrix data (10 categories × 5 resources) |
| `platform/tests/test_maple_estimate_status_queries.py` | Estimate count + value queries (Phase A) |
| `platform/tests/test_maple_material_size_operations.py` | Material size ops (Phase B) |
| `platform/tests/test_maple_help_coverage.py` | HELP intent — supported phrasings + xfail gaps (§9) |
| `platform/tests/test_material_agent.py` | Material Agent handler integration |
| `platform/tests/test_estimate_agent.py` | Estimate Agent handler integration |
| `platform/tests/test_orchestrator_intents.py` | Orchestrator intent resolution |
| `platform/tests/reports/maple_crud_gap_report.md` | Auto-generated gap report (regenerates each test run) |

## 10.2 How to run

```bash
cd platform
./run_tests.sh tests/test_maple_crud_coverage.py                     # Tier 1 only (~8s)
./run_tests.sh tests/test_maple_crud_coverage.py -m ""               # Tier 1 + Tier 2 (~3min, ~$0.05, needs OPENAI_API_KEY)
./run_tests.sh tests/test_maple_estimate_status_queries.py tests/test_maple_material_size_operations.py
./run_tests.sh tests/test_maple_help_coverage.py                     # HELP intent (74 passing, 0 xfail after Phase 1)
```

## 10.3 Current matrix score (Tier 1 / Tier 2)

Snapshot as of 2026-05-02 — regenerate with the coverage test.

| Category | Tier 1 | Tier 2 | Verdict |
|---|---|---|---|
| direct_imperative | 12/12 | 9/12 | covered (LLM flubs "create a new X") |
| casual | 12/12 | 12/12 | covered |
| possessive | 12/12 | 6/12 | covered (Wave 1 Phase 2) |
| count | 12/12 | 12/12 | covered |
| filter_find | 12/12 | 12/12 | covered |
| field_targeted_update | 12/12 | 8/12 | covered (Wave 1 Phase 2) |
| implicit_relationship | 12/12 | 4/12 | covered (Wave 2 — orchestrator routing + agent-side join) |
| bulk | 12/12 | 12/12 | refused correctly |
| verbless | 12/12 | 11/12 | covered |
| material_size | 6/6 | 6/6 | covered |
| material_query_variants | 5/5 | n/a | covered (Wave 3 Workstream B) |
| estimate_outbound | 5/5 | n/a | covered (Wave 4 + 4.1 — orchestrator routing + Property/Contact/Estimate agent cross-resource branches; contact-anchored variant gated on person-name shape) |
| equipment_blocked | 3/3 | 3/3 | refused correctly |

**Totals: Tier 1 127/127 · Tier 2 95/117** (Tier 2 is unchanged — Wave 4/4.1 hasn't been re-run on the LLM tier; new categories aren't included in the Tier 2 coverage column above). All Tier 1 categories pass and cross-resource list responses are correctly filtered. The `cross_resource` join layer lives in `agents/cross_resource.py`; per-agent join handlers in Contact / Property / Estimate read `context.filter_by` to apply the constraint, including the Wave 4/4.1 `estimate`, `property`, and `contact` cross-types.

## 10.4 Related docs

- `CLAUDE.md` > "Maple (Orchestrator) — CRUD assistant policies" — architectural overview
- `documentation/development/plans/maple-xfail-wave-1.md` — active plan for closing the remaining xfail backlog

---

# 11. Coverage blind spots & extension ideas

The matrix is shape-complete for the nine CRUD categories but never exercises several phrasing families real users will type. This section is the gap-hunting backlog — entries here aren't tracked as ⚠️ gaps in §1–§7 because they're conceptual classes, not specific phrasings ready to wire. Promote an entry to a per-resource ⚠️ gap row once you've picked a concrete phrasing and a target intent.

## 11.1 Language / phrasing variation

- **Negations:** `I don't need the Landscaper role anymore`, `remove John Doe — he moved`
- **Conjunctions / multi-action:** `create a contact and link it to {property}`, `delete the Foreman role and add Operator instead`
- **Typos / stemming:** `delet the proprty at 123 Main`, `contacs`, `labours` vs `labour roles` — partly mitigated by `agents/fuzzy_utils.py`
- **Pronouns / anaphora across turns:** `update it`, `that one`, `the last one I created` (estimate-scoped anaphora exists in §1.7; cross-resource anaphora is the gap)
- **Questions that imply get vs list:** `is there a contact named John?`, `do I have concrete blocks?`

## 11.2 Value / field shapes not exercised

- **Dates / date ranges:** `contacts added this month`, `estimates from last week`
- **Numeric ranges / comparisons:** `materials under $10` (already in §4.9), `labour roles costing more than $40/hr`
- **Multi-field update:** `set John Doe's phone to X and email to Y`
- **Nullable / clearing:** `remove John Doe's phone number`, `clear the description on {material}`

## 11.3 Domain overlap ambiguity

The matrix uses disjoint tokens by design — real users won't:

- Same name across domains: a contact and a property both called "John's Place"
- Role-name collisions: a contact named "Foreman Smith"
- Addresses that look like material names

A small `ambiguity` test category would assert the classifier's tiebreak behavior.

## 11.4 Refusal surface beyond bulk + equipment

- **Destructive at smaller scale:** `delete the last 5 contacts` (N>1 but not "all") — listed as a §7.4 ⚠️ gap
- **Cross-tenant / out-of-scope:** `show me other companies' estimates`
- **Non-CRUD slipping through:** `email John Doe`, `schedule a visit`

## 11.5 Highest-value extensions (ranked by ROI)

If we want to expand coverage, here's the order:

1. **`status_transition` matrix category for estimates** — fixed verb set × 5 EstimateStatus values × 2-3 subjects. ~30 new cases. Cleanest starter; status transitions already exist in §1.4.
2. **Active-entity anaphora** — exercises the `active_estimate_code` session path beyond what §1.7 currently asserts.
3. **Filter by status / date** — `show me draft estimates from last week`, `approved quotes over $10k`. Needs date-range parsing.
4. **Direct coverage of the add-work-item regex path** — `agents/orchestrator/service.py` work-item rules; today only hit by orchestrator unit tests.
5. **Cross-resource outbound from estimate** — mirrors §6.2 / §6.3 inbound pattern (e.g. `which property is {EST} for?`, `what materials does {EST} use?`).
6. **Ambiguity fixtures** — see §11.3.
7. **Typo / stemming fixtures** — 5–10 common misspellings per resource to catch fuzzy-match regressions.
