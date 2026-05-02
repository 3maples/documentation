# Maple xfail backlog — Wave 2 (cross-resource relationship queries)

**Status:** Draft
**Owner:** TBD
**Date:** 2026-05-02
**Depends on:** [maple-xfail-wave-1.md](maple-xfail-wave-1.md) (shipped 2026-05-02)

## Goal

Close the 9 remaining `implicit_relationship` xfails in `tests/test_maple_crud_coverage.py` by adding a cross-resource relationship-query layer to Maple — a hybrid of orchestrator-level shape detection and agent-level join queries. Lifts Tier 1 coverage from 108/117 to **117/117** (full).

## What's in scope

The 9 xfails fall into four shape families:

| # | Shape | Phrasings | Expected intent |
|---|---|---|---|
| 1 | **property → contact** | `who lives at {property}?`, `what contacts are at {property}?`, `who owns {property}?` | `list_contacts` (filtered by property) |
| 2 | **contact → property** | `what properties does {contact} own?`, `where does {contact} live?` | `list_properties` (filtered by contact) |
| 3 | **material → property** | `which properties use {material}?`, `where is {material} used?` | `list_properties` (joined via estimates) |
| 4 | **labour → property/estimate** | `which properties need a {role}?`, `what estimates use the {role} role?` | `list_properties` / `list_estimates` (joined via estimates) |

Three confirmed-working sibling phrasings already pass on Tier 1 via plural-aware routing (`show me {contact}'s properties`, `find estimates with {material}`, `show me jobs needing a {role}`) — they're the proof the existing list-intent path can carry the response, we just need shape detection for the question phrasings.

## What's out of scope

- Estimate-anchored relationship queries (`who worked on EST-0042?`, `which materials does EST-0042 use?`) — distinct shape; queue for Wave 3 if asked.
- Aggregation phrasings (`how many properties use {material}?`) — `is_count_query` already exists but needs a count-aware list response; queue separately.
- LLM tier improvements — Tier 2 already partially rescues these; this plan focuses on Tier 1 rules.

## Data model recap (verified 2026-05-02)

| Relationship | Storage | Query path |
|---|---|---|
| Property → Contact | `Property.contacts: List[PydanticObjectId]` | direct lookup |
| Contact → Property | (no reverse field) | `Property.find({"contacts": contact_id})` |
| Material → Estimate | `Estimate.materials[].material: str` (id as string) | `Estimate.find({"materials.material": material_id_str})` |
| Labour → Estimate | `Estimate.labours[].labour: str` | `Estimate.find({"labours.labour": labour_id_str})` |
| Estimate → Property | `Estimate.property: Optional[PydanticObjectId]` | direct |
| Material/Labour → Property | (transitive) | distinct properties of estimates referencing the entity |

All six paths are achievable without new collections — the data is there, only the query and the routing are missing.

## Architecture

### Approach: hybrid (rules + agent join)

Rules detect the cross-resource shape and the **anchor entity name**; route to the **target agent** (Contact / Property / Estimate) with a `filter_by` payload identifying the cross-resource constraint. The target agent does name-resolution on the constraint and runs the join.

**Why hybrid, not new intents:** The phrasings answer with a list of an existing resource (`list_contacts`, `list_properties`, `list_estimates`) — the response shape is already supported. Inventing `list_contacts_at_property` etc. would multiply intents 6× without changing what the response looks like. The hybrid approach reuses the existing list-handler templates and only adds a filter clause.

**Why not LLM-only:** Tier 2 rescues 4/12 today (probably better with current LLM rev), but the Tier 1 contract is what users without a key get. The shape is regular enough that a small set of rules can cover the high-frequency phrasings.

### New `filter_by` payload contract

`process()` returns a `filter_by` dict on the result when a cross-resource constraint applied:

```python
{
    "intent": "list_contacts",
    "agent": "Contact Agent",
    "filter_by": {
        "type": "property",            # cross-resource type
        "name": "123 Main St",          # raw entity name from the message
        "role_hint": "owner",           # optional — set when verb implies a role
    },
}
```

The target agent resolves `name` via its existing fuzzy-name lookup against the cross-resource collection, then runs the join query. If name resolution returns 0 or >1 candidate, the agent emits the existing fuzzy-confirmation flow.

## Phase 1 — Orchestrator rules (~half day)

Add `_match_cross_resource_query` to `agents/orchestrator/service.py`, called between `_match_possessive_or_field_targeted` and the standard action+domain match. Each shape gets one regex.

### 1.1 Property → Contact (3 phrasings)

```python
_PROPERTY_CONTACT_QUERY_PATTERNS: Tuple[Tuple[re.Pattern[str], Optional[str]], ...] = (
    # "who lives at <property>", "who owns <property>"
    (re.compile(r"^who\s+(?P<role>lives|owns|works)\s+(?:at|in|on)\s+(?P<name>.+?)\??$",
                re.IGNORECASE), None),
    # "what contacts are at <property>"
    (re.compile(r"^what\s+contacts?\s+(?:are|live)\s+(?:at|in|on)\s+(?P<name>.+?)\??$",
                re.IGNORECASE), None),
)
```

`role` capture maps `owns→owner`, `lives→resident`, `works→worker` for `role_hint`.

### 1.2 Contact → Property (2 phrasings)

```python
# "what properties does <contact> own", "where does <contact> live"
re.compile(
    r"^(?:what\s+propert(?:ies|y)\s+does\s+(?P<name>.+?)\s+own|"
    r"where\s+does\s+(?P<name2>.+?)\s+(?:live|reside))\??$",
    re.IGNORECASE,
)
```

### 1.3 Material → Property (2 phrasings)

```python
# "which properties use <material>", "where is <material> used"
re.compile(
    r"^(?:which\s+propert(?:ies|y)\s+use\s+(?P<name>.+?)|"
    r"where\s+is\s+(?P<name2>.+?)\s+used)\??$",
    re.IGNORECASE,
)
```

### 1.4 Labour → Property/Estimate (2 phrasings)

```python
# "which properties need a <role>"
_LABOUR_PROP_PATTERN = re.compile(
    r"^which\s+propert(?:ies|y)\s+need\s+(?:a\s+|an\s+)?(?P<name>.+?)\??$",
    re.IGNORECASE,
)
# "what estimates use the <role> role"
_LABOUR_EST_PATTERN = re.compile(
    r"^what\s+estimates?\s+use\s+(?:the\s+)?(?P<name>.+?)\s+role\??$",
    re.IGNORECASE,
)
```

### 1.5 Wiring

In `_classify_with_rules`, after the possessive matcher returns None:

```python
cross_op = self._match_cross_resource_query(normalized, original)
if cross_op is not None:
    return cross_op
```

Each pattern match returns a classification tuple where the **5th element** (currently `clarification`) carries the `filter_by` payload — or, cleaner, extend the tuple to include a 6th `filter_by` slot. (Decide during implementation; both are acceptable. The 6-tuple is clearer; the existing 5-tuple shape avoids churn in callers that destructure it.)

### Phase 1 deliverable

- 9 new test rows in `_maple_coverage_data.py` flip from xfail → passing (asserted via `_CONFIRMED_WORKING_CASE_IDS`).
- `filter_by` payload appears on the `process()` result for cross-resource queries.

## Phase 2 — Agent-side join handlers (~1 day)

Each target agent (Contact / Property / Estimate) gains a `filter_by`-aware list path.

### 2.1 Contact Agent — `filter_by={type=property, name=...}`

In `agents/contact/service.py:_handle_list_contacts`:

1. Resolve the property by `name` via the existing fuzzy-name resolver (`_resolve_property_by_name(name, company_id)` — add if missing). Returns property_id or fuzzy-confirmation prompt.
2. Once resolved, query `Contact.find({"_id": {"$in": property.contacts}, "company": company_id})`.
3. If `role_hint == "owner"`, additionally filter on `Contact.role == "owner"` (if such a role exists; if not, skip the hint silently).
4. Render via the existing list-response template ("Here are the contacts at 123 Main St: …").

### 2.2 Property Agent — `filter_by={type=contact|material|labour, name=...}`

Three sub-cases, dispatched on `filter_by.type`:

- **type=contact**: resolve contact_id, then `Property.find({"contacts": contact_id, "company": company_id})`.
- **type=material**: resolve material_id, gather distinct property_ids from `Estimate.find({"materials.material": str(material_id), "company": company_id})`, fetch those properties.
- **type=labour**: same as material but on `labours.labour`.

The transitive material/labour queries use a Beanie aggregation pipeline (one `find` + one `$group` on `property`) — single round-trip, no per-estimate fan-out.

### 2.3 Estimate Agent — `filter_by={type=labour, name=...}`

Resolve labour_id, then `Estimate.find({"labours.labour": str(labour_id), "company": company_id})`.

### 2.4 Name-resolution shared concern

Each agent already has fuzzy-name lookup against its **own** collection. Cross-resource lookup needs `_resolve_<other>_by_name` helpers. Three options:

- **A.** Each agent writes its own (e.g. Contact Agent gets `_resolve_property_by_name`). Duplicates code.
- **B.** Shared resolver in `agents/name_resolver.py` keyed by domain. Cleaner but a new module.
- **C.** Each agent imports the relevant resolver from the *other* agent (Contact Agent imports `PropertyAgent._resolve_by_name`). Tight coupling.

Recommendation: **B**. Create `agents/name_resolver.py` exposing `resolve_entity_by_name(domain, name, company_id)` which dispatches to the per-collection lookup. Each existing agent's `_resolve_by_name` becomes a thin wrapper around this. Total churn: ~80 lines.

### Phase 2 deliverable

- All 9 cross-resource Tier-1 cases produce the **right list response** (not just classify correctly).
- Fuzzy-confirmation flow works on the cross-resource entity (e.g. "Did you mean John Doe or John Smith?" when "show me john's properties" is ambiguous).

## Phase 3 — Tests + docs

### 3.1 Tests

- Promote the 9 xfail rows to `_CONFIRMED_WORKING_CASE_IDS`.
- Add per-agent service tests covering: happy path, ambiguous-name fuzzy flow, missing-entity refusal, transitive (material→property) join correctness with a fixture estimate.
- Add an orchestrator test for the `filter_by` payload shape on each of the 4 shape families.

### 3.2 Docs

Per CLAUDE.md, the same change updates `documentation/development/maple-phrasing-reference.md`:

- Flip 9 ⚠️→✅ in §6 (Cross-resource / implicit relationships).
- Update §10.3 snapshot to **117/117 Tier 1**.
- Bump "Last updated" with Wave 2 note.
- Add a §6 lead paragraph documenting the `filter_by` contract so future contributors know how to extend.

## PR strategy

Two PRs, in order:

1. **`feat: add cross-resource query rules + filter_by payload`** — Phase 1 only. Coverage tests show classification working but agent responses still emit unfiltered lists. Hard-asserts the routing without committing to the join handler design.
2. **`feat: implement cross-resource list joins in target agents`** — Phase 2 + 3. Closes the loop.

Splitting like this lets Phase 1 land standalone (with a "join handler is no-op for now" caveat in tests) if Phase 2 needs more design iteration.

## Risks

- **Name-collision across resources.** "John" could be a contact or a property name (`John's Place`). The fuzzy resolver must scope to the correct collection per `filter_by.type`. Existing per-agent resolvers do this implicitly; the shared resolver in §2.4 must preserve that scoping.
- **Regex over-fitting on shape families.** "where does John live" must NOT match for properties named "John" — the verb (`live`) pins the target to property-of-contact, not lookup-of-property. The patterns in §1.2 anchor on the verbs `live`/`reside`/`own` with the contact subject in the middle.
- **Transitive join cardinality.** A material used in 500 estimates produces 500 estimate documents but should collapse to ≤500 distinct properties. Use `$group` to deduplicate at the DB layer rather than client-side `set()`.
- **Role-hint semantics.** "Who owns 123 Main St?" implies the contact has `role=owner`. If the data doesn't track contact-roles uniformly, the hint becomes a no-op. Verify the Contact model's role enum during implementation; degrade silently if absent.
- **Ambiguity between cross-resource and possessive.** `show me John's properties` already routes via the possessive flow + plural-aware list flip (confirmed working). The new rules must NOT regress this — anchor on the question forms (`what properties does X own?`) rather than possessive forms.

## Done criteria

- 9 implicit_relationship xfails passing on Tier 1 + promoted to `_CONFIRMED_WORKING_CASE_IDS`.
- `tests/reports/maple_crud_gap_report.md` Tier 1 = **117/117**.
- Each cross-resource list response is correct (not just classified) — verified by per-agent service tests.
- `maple-phrasing-reference.md` §6 flipped to ✅, §10.3 snapshot bumped, "Last updated" carries the Wave 2 note.

## Future hooks (Wave 3 candidates — not in this plan)

- Estimate-anchored joins: `who worked on EST-0042?`, `what materials does EST-0042 use?`
- Aggregations: `how many properties use {material}?`, `total cost across all estimates needing a Foreman`.
- Filter chaining: `which properties in Toronto use concrete blocks?` (geographic + material constraint together).
