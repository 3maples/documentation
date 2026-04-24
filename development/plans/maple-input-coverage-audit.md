# Maple Input Coverage Audit

A comprehensive reference of every phrasing currently exercised by `platform/tests/test_maple_crud_coverage.py`, plus estimate phrasings (not in the matrix) and gap-hunting suggestions.

**Source of truth:** `platform/tests/_maple_coverage_data.py` (matrix definition) and `platform/tests/reports/maple_crud_gap_report.md` (latest run).

**Total in-matrix phrasings:** 111 = 9 categories × 4 CRUD resources × 3 phrasings + 3 equipment refusals.

---

## Resource tokens

| Resource | Singular / Plural | Name | Filter | Location | Field | Value |
|---|---|---|---|---|---|---|
| Property | property / properties | 123 Main St | Toronto | Toronto | city | Vancouver |
| Contact | contact / contacts | John Doe | Smith | Toronto | phone | 555-1111 |
| Material | material / materials | concrete blocks | concrete | in stock | price | $5 |
| Labour (People) | labour role / labour roles | Landscaper | Foreman | outdoor | cost | $50 |
| Equipment (pseudo) | equipment / equipment | skid steer | excavator | yard | make | Bobcat |

Labour = catalog of *role definitions* (Landscaper, Foreman, Operator) — NOT individuals. Contact is the resource for individuals.

Legend: ✅ = confirmed working on Tier 1 (rule-only) · ⚠️ = known gap (xfail on Tier 1) · 🛑 = safety refusal required

---

## 1. direct_imperative (12 phrasings — all ✅)

| Resource | Phrasings |
|---|---|
| Property | `create a new property` · `list all properties` · `delete the property 123 Main St` |
| Contact | `create a new contact` · `list all contacts` · `delete the contact John Doe` |
| Material | `create a new material` · `list all materials` · `delete the material concrete blocks` |
| Labour | `create a new labour role` · `list all labour roles` · `delete the labour role Landscaper` |

## 2. casual (12 phrasings — all ✅)

| Resource | Phrasings |
|---|---|
| Property | `show me my properties` · `what properties do I have?` · `pull up property 123 Main St` |
| Contact | `show me my contacts` · `what contacts do I have?` · `pull up contact John Doe` |
| Material | `show me my materials` · `what materials do I have?` · `pull up material concrete blocks` |
| Labour | `show me my labour roles` · `what labour roles do I have?` · `pull up labour role Landscaper` |

## 3. possessive (12 phrasings — category default ⚠️)

| Resource | Phrasings |
|---|---|
| Property | `show me 123 Main St's details` ✅ · `what's 123 Main St's city?` ⚠️ · `update 123 Main St's record` ✅ |
| Contact | `show me John Doe's details` ✅ · `what's John Doe's phone?` ⚠️ · `update John Doe's record` ✅ |
| Material | `show me concrete blocks's details` ⚠️ · `what's concrete blocks's price?` ⚠️ · `update concrete blocks's record` ⚠️ |
| Labour | `show me Landscaper's details` ✅ · `what's Landscaper's cost?` ⚠️ · `update Landscaper's record` ✅ |

## 4. count (12 phrasings — all ✅)

| Resource | Phrasings |
|---|---|
| Property | `how many properties do I have?` · `count my properties` · `total number of properties` |
| Contact | `how many contacts do I have?` · `count my contacts` · `total number of contacts` |
| Material | `how many materials do I have?` · `count my materials` · `total number of materials` |
| Labour | `how many labour roles do I have?` · `count my labour roles` · `total number of labour roles` |

## 5. filter_find (12 phrasings — all ✅)

| Resource | Phrasings |
|---|---|
| Property | `find properties named Toronto` · `show properties in Toronto` · `search for properties matching Toronto` |
| Contact | `find contacts named Smith` · `show contacts in Toronto` · `search for contacts matching Smith` |
| Material | `find materials named concrete` · `show materials in in stock` · `search for materials matching concrete` |
| Labour | `find labour roles named Foreman` · `show labour roles in outdoor` · `search for labour roles matching Foreman` |

## 6. field_targeted_update (12 phrasings — category default ⚠️)

| Resource | Phrasings |
|---|---|
| Property | `change the city of 123 Main St to Vancouver` ✅ · `update the city on 123 Main St to Vancouver` ✅ · `set 123 Main St's city to Vancouver` ⚠️ |
| Contact | `change the phone of John Doe to 555-1111` ✅ · `update the phone on John Doe to 555-1111` ✅ · `set John Doe's phone to 555-1111` ⚠️ |
| Material | `change the price of concrete blocks to $5` ⚠️ · `update the price on concrete blocks to $5` ⚠️ · `set concrete blocks's price to $5` ⚠️ |
| Labour | `change the cost of Landscaper to $50` ✅ · `update the cost on Landscaper to $50` ✅ · `set Landscaper's cost to $50` ⚠️ |

## 7. implicit_relationship (12 phrasings — category default ⚠️, cross-resource)

| Resource (asked from) | Phrasings → expected intent |
|---|---|
| Property | `who lives at 123 Main St?` → list_contacts ⚠️ · `what contacts are at 123 Main St?` → list_contacts ⚠️ · `who owns 123 Main St?` → list_contacts ⚠️ |
| Contact | `what properties does John Doe own?` → list_properties ⚠️ · `where does John Doe live?` → list_properties ⚠️ · `show me John Doe's properties` → list_properties ✅ |
| Material | `which properties use concrete blocks?` → list_properties ⚠️ · `where is concrete blocks used?` → list_properties ⚠️ · `find estimates with concrete blocks` → list_estimates ✅ |
| Labour | `which properties need a Landscaper?` → list_properties ⚠️ · `what estimates use the Landscaper role?` → list_estimates ⚠️ · `show me jobs needing a Landscaper` → list_properties ✅ |

## 8. bulk — must refuse (12 phrasings — all 🛑)

| Resource | Phrasings |
|---|---|
| Property | `delete all properties` · `remove every property` · `wipe my properties` |
| Contact | `delete all contacts` · `remove every contact` · `wipe my contacts` |
| Material | `delete all materials` · `remove every material` · `wipe my materials` |
| Labour | `delete all labour roles` · `remove every labour role` · `wipe my labour roles` |

Every phrasing must resolve to `intent=unknown`, `agent=None`, `needs_clarification=True`. Policy enforced in `agents/orchestrator/service.py` and defensively at the top of each domain agent's `process()`.

## 9. verbless (12 phrasings — category default ⚠️, most confirmed working)

| Resource | Phrasings |
|---|---|
| Property | `123 Main St` ✅ · `I want the details for 123 Main St` ✅ · `tell me about 123 Main St` ✅ |
| Contact | `John Doe` ✅ · `I want the details for John Doe` ✅ · `tell me about John Doe` ✅ |
| Material | `concrete blocks` ✅ · `I want the details for concrete blocks` ✅ · `tell me about concrete blocks` ✅ |
| Labour | `Landscaper` ✅ · `I want the details for Landscaper` ✅ · `tell me about Landscaper` ✅ |

## 10. equipment_blocked — must refuse (3 phrasings — all 🛑)

`show all my equipment` · `create a new equipment` · `delete the excavator equipment`

Every phrasing must return the refusal shape. Policy enforced via `is_equipment_request()` in `agents/text_utils.py`, canonical copy in `EQUIPMENT_REFUSAL_MESSAGE`.

---

## Estimate phrasings (NOT currently in the matrix)

Estimate is deliberately excluded from `_CRUD_RESOURCES` because:

1. **Creation isn't a one-shot imperative.** Estimates are generated by the LangChain EstimateAgent from a job description, embedding MaterialItem/EquipmentItem/LabourItem sub-items from the catalog. "Create a new estimate" kicks off a multi-turn conversation (`agents/estimate/conversation_guide.py`).
2. **Generic templates produce nonsense.** `_possessive` emits `"show me EST-0042's details"` (nobody talks that way); `_verbless` emits bare `"EST-0042"` (ambiguous with property names); `_field_targeted_update` assumes a flat scalar when estimates have nested sub-items and a status state machine.
3. **The real API is different.** Intents like `add_work_item`, `link_estimate_property`, and status transitions (`draft → review → approved/rejected/on_hold`) don't fit the 3-phrasings-per-category template.

### Token suggestions

singular=`estimate`, plural=`estimates`, name=`EST-0042`, filter=`draft`, location=`draft` (status), field=`status`, value=`approved`. Synonyms `quote`/`quotes` also route to Estimate Agent (`agents/orchestrator/intents.py:165`).

### What the generic template *would* emit if estimate were plugged in

#### direct_imperative (realistic)
`create a new estimate` · `list all estimates` · `delete the estimate EST-0042`

#### casual (realistic)
`show me my estimates` · `what estimates do I have?` · `pull up estimate EST-0042`

#### possessive (awkward — users don't talk this way about estimates)
`show me EST-0042's details` · `what's EST-0042's status?` · `update EST-0042's record`

More natural: `what's the status of EST-0042?` — see the "Real estimate phrasings" section below.

#### count (realistic)
`how many estimates do I have?` · `count my estimates` · `total number of estimates`

#### filter_find (realistic and useful)
`find estimates named draft` · `show estimates in draft` · `search for estimates matching draft`

More natural variants worth covering: `show me draft estimates`, `list approved quotes`, `estimates for 123 Main St`.

#### field_targeted_update (works well — status is the real field users change)
`change the status of EST-0042 to approved` · `update the status on EST-0042 to approved` · `set EST-0042's status to approved`

#### implicit_relationship (outbound — estimate as the source)
Estimate is already the *target* in the existing matrix (`find estimates with concrete blocks`, `what estimates use the Landscaper role?`). Outbound would be:
- `which property is EST-0042 for?` → get_property (or get_estimate with property hint)
- `what materials does EST-0042 use?` → list_materials
- `what roles are on EST-0042?` → list_labours

#### bulk — must refuse
`delete all estimates` · `remove every estimate` · `wipe my estimates`

#### verbless (ambiguous — bare `EST-0042` is fine, but users rarely say just the code)
`EST-0042` · `I want the details for EST-0042` · `tell me about EST-0042`

### Real estimate phrasings the orchestrator already handles

These exist in `agents/orchestrator/service.py` and `suggestions.py` but aren't covered by any matrix.

**Status transitions**
- `approve EST-0042` · `mark EST-0042 as approved`
- `reject the estimate` · `send EST-0042 for review`
- `put EST-0042 on hold` · `move this estimate to draft`
- `what's the status of EST-0042?`

**Work-item / line-item flow** (`service.py:230-248`)
- `add a work item to the estimate` · `add a job item to EST-0042`
- `add a scope to the last estimate` · `add a line item to this estimate`
- `create another scope on EST-0042`

**Linking**
- `link EST-0042 to 123 Main St` · `attach this estimate to 123 Main St`
- `which property is this estimate for?`

**Active-estimate anaphora** (`service.py:479`, `active_estimate_code`)
- `add a Landscaper to the estimate` (resolves via session's `active_estimate_code`)
- `update the estimate` · `show me the estimate` · `this estimate` · `the last estimate` · `that one`

**Generation (multi-turn)** handled by `agents/estimate/conversation_guide.py`
- `create an estimate for 123 Main St — needs 20 yards of concrete and two landscapers`
- `draft a quote for a driveway replacement at 456 Oak Ave`
- `I need an estimate for [job description]`

**Division / shape** (`EstimateDivision` enum, `service.py:22`)
- `create a residential estimate` · `new commercial quote`

---

## Coverage blind spots (to hunt for gaps)

The matrix is shape-complete for the 9 CRUD categories but never exercises these phrasing families users will actually type:

### Language / phrasing variation
- **Negations:** "I don't need the Landscaper role anymore", "remove John Doe — he moved"
- **Conjunctions / multi-action:** "create a contact and link it to 123 Main St", "delete the Foreman role and add Operator instead"
- **Typos / stemming:** "delet the proprty at 123 Main", "contacs", "labours" vs "labour roles"
- **Pronouns / anaphora across turns:** "update it", "that one", "the last one I created"
- **Questions that imply get vs list:** "is there a contact named John?", "do I have concrete blocks?"

### Value / field shapes not tested
- **Dates / date ranges:** "contacts added this month", "estimates from last week"
- **Numeric ranges / comparisons:** "materials under $10", "labour roles costing more than $40/hr"
- **Multi-field update:** "set John Doe's phone to X and email to Y"
- **Nullable / clearing:** "remove John Doe's phone number"

### Domain overlap ambiguity
The matrix uses disjoint tokens by design — real users won't.
- Same name across domains: a contact and a property both called "John's Place"
- Role-name collisions: a contact named "Foreman Smith"
- Addresses that look like material names

### Intents outside the 9 categories
- Estimate status transitions (draft → review → approved / rejected / on_hold)
- Add-work-item / line-item flows
- link_estimate_property, assign role to estimate
- Pending-intent / multi-turn: "update" (no field) → "phone" → "555-1111" — `_match_bare_field_name` flow documented in `CLAUDE.md` but not in the matrix

### Refusal surface beyond bulk + equipment
- Destructive at smaller scale: "delete the last 5 contacts" (N>1 but not "all")
- Cross-tenant / out-of-scope: "show me other companies' estimates"
- Non-CRUD slipping through: "email John Doe", "schedule a visit"

---

## Highest-value extensions

If we want to expand coverage, ranked by return-on-effort:

1. **`status_transition` category (estimates)** — cleanest starter. Fixed verb set × 5 EstimateStatus values × 2-3 subject phrasings. ~30 new cases.
2. **Active-entity anaphora** — "update the estimate", "delete it", "show me the last one". Tests the `active_estimate_code` session path.
3. **Filter by status / date** — `show me draft estimates from last week`, `approved quotes over $10k`.
4. **Add-work-item regex path** — the 4 patterns at `service.py:234` deserve direct coverage; currently only hit by orchestrator unit tests.
5. **Cross-resource outbound from estimate** — mirrors existing inbound implicit_relationship rows.
6. **Ambiguity fixtures** — a small category where the same token exists in two domains, to assert the classifier's tiebreak.
7. **Typo / stemming fixtures** — 5-10 common misspellings per resource to catch regressions in the fuzzy-match layer (`agents/fuzzy_utils.py`).

---

## How to run

```bash
cd platform
./run_tests.sh tests/test_maple_crud_coverage.py            # Tier 1 (rules only, ~5s)
./run_tests.sh tests/test_maple_crud_coverage.py -m ""      # Tier 1 + Tier 2 (live LLM, ~3min, ~$0.05, needs OPENAI_API_KEY)
```

Gap report is written to `platform/tests/reports/maple_crud_gap_report.md` after every run.
