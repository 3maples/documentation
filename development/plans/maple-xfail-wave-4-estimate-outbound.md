# Maple xfail backlog — Wave 4 (estimate ↔ property/contact outbound drilldowns)

**Status:** Shipped (2026-05-02 — both workstreams; coverage matrix Tier 1 now 126/126)
**Owner:** TBD
**Date:** 2026-05-02

## Implementation notes (post-ship)

Workstream A and B were combined into a single landing because the patterns extend the same `_CROSS_RESOURCE_QUERY_PATTERNS` table and the agent-side join handlers reuse the existing `cross_resource.py` resolvers (`find_estimate_by_code`, `find_properties_by_name_or_address`).

Differences from the original sketch:
- The "who is this estimate for?" variant does NOT use the `role_hint` slot for an `include_property` flag. Instead the Contact agent unconditionally leads the response with the property name when `filter_by.type == "estimate"` — simpler, and the user always benefits from seeing the join chain. The original plan's `role_hint=include_property` overload was dropped.
- The Workstream B patterns are anchored on either the literal word `property` or the verb phrase `linked to`. The plan's risk register flagged the broad `estimates? for X` shape; the implemented anchor avoids the ambiguity entirely (`estimates for approval` does not match because there's no `property` literal and no `linked to`). The fall-through-on-empty-property mitigation listed in the plan was therefore not needed.
- Multi-match property resolution uses a `{property: {$in: [...]}}` filter on the Beanie query rather than refusing — the user can disambiguate in a follow-up question.
- The Property agent's estimate→property handler shares its plumbing with `_list_properties_by_cross_resource` (extended to accept `cross_type=estimate`). The Contact agent uses a new `_list_contacts_for_estimate` helper since the join chain (estimate → Property.get → contacts intersect) is shaped differently from the existing `_list_contacts_at_property`.

Tests landed in `tests/test_orchestrator_intents.py` (pattern routing — 13 new parametrize cases + 2 negative-case cases) and `tests/test_cross_resource_joins.py` (8 new agent-side handler tests for happy path, missing estimate, missing property link, and Workstream B not-found). Matrix coverage added under category `estimate_outbound` in `_maple_coverage_data.py`.

---
**Depends on:**
- [maple-xfail-wave-1.md](maple-xfail-wave-1.md) (shipped 2026-05-02 — possessive + field-targeted updates)
- [maple-xfail-wave-2.md](maple-xfail-wave-2.md) (shipped 2026-05-02 — `_match_cross_resource_query` + `filter_by` agent contract)
- [maple-xfail-wave-3.md](maple-xfail-wave-3.md) (shipped 2026-05-02 — Workstream C added estimate as a `cross_type` for material/labour drilldowns)

## Goal

Close the four remaining ⚠️ entries in §1.8 of `documentation/development/maple-phrasing-reference.md` — all are estimate↔property/contact outbound drilldowns that the matrix doesn't cover and that Wave 3 left out of scope.

| # | Phrasing | Intended behavior |
|---|---|---|
| 1 | `who is this estimate {EST} for?` | return the property and its contacts attached to the estimate |
| 2 | `which contact is this estimate {EST} for?` | return the contact(s) on the property linked to the estimate |
| 3 | `which property is this estimate {EST} linked to?` | return the property linked to the estimate |
| 4 | `show me estimate for property {property}` | list estimates whose `property` id matches the named property |

## Architecture recap

After Wave 2 + Wave 3 the cross-resource pipeline looks like this:

- **Orchestrator** (`platform/agents/orchestrator/service.py:192`) declares `_CROSS_RESOURCE_QUERY_PATTERNS` as a tuple of `(re.Pattern, intent, cross_type, role_hint)`. `_match_cross_resource_query` walks the tuple, captures `<name>`, and emits `{intent, filter_by={type, name, role_hint?}, …}` on the classification result.
- **Router** threads `filter_by` into the agent's `context` dict.
- **Target agent** reads `context["filter_by"]`, resolves the entity through `agents/cross_resource.py` (e.g. `find_estimate_by_code`, `find_properties_by_name_or_address`), and runs the join.

Wave 3 Workstream C already added `cross_type=estimate` for material/labour drilldowns (`what materials does {EST} use?`). This wave adds `cross_type=estimate` for **property** and **contact** targets, plus a new `cross_type=property` for the **estimate** target.

Relevant model fields already in place:
- `Estimate.property: Optional[PydanticObjectId]` — nullable single property link (`platform/models/estimate.py:258`)
- `Property.contacts: List[PydanticObjectId]` — property holds the contact list (`platform/models/property.py:15`)
- `find_estimate_by_code(company_id, code) -> Estimate | None` (`platform/agents/cross_resource.py:99`)
- `find_properties_by_name_or_address(company_id, query) -> List[Property]` (`platform/agents/cross_resource.py:35`)

No model changes are required.

## Scope

Four phrasings, two workstreams. Each can ship independently — the phrasings split cleanly along anchor direction.

### Workstream A — Estimate-anchored outbound (3 phrasings)

Phrasings 1, 2, 3 above. The user names an `EST-NNNN` and asks for the people/place attached to it.

**Routing:**

| Phrasing | Intent | `cross_type` | Target agent |
|---|---|---|---|
| `which property is this estimate {EST} linked to?` | `list_properties` | `estimate` | Property |
| `which contact is this estimate {EST} for?` | `list_contacts` | `estimate` | Contact |
| `who is this estimate {EST} for?` | `list_contacts` | `estimate` (with `include_property=True` flag in `filter_by`) | Contact |

Reasoning for #1 routing: "who is this for" semantically prioritizes the contact answer ("the homeowner"), but the response needs to mention the property too. Cleanest is to keep the intent as `list_contacts` and let the Contact agent's join handler decorate the response with the property name when `filter_by["include_property"]` is set. Avoids inventing a fifth pseudo-intent.

**Patterns** (add at the end of `_CROSS_RESOURCE_QUERY_PATTERNS`):

```python
# estimate → property: "which property is (this) estimate EST-N (linked to|for)"
(
    re.compile(
        r"^which\s+property\s+(?:is|does)\s+(?:this\s+|the\s+)?estimate\s+"
        r"(?P<name>[A-Za-z0-9-]+)\s+(?:linked\s+to|for|attached\s+to)\??$",
        re.IGNORECASE,
    ),
    "list_properties",
    "estimate",
    None,
),
# estimate → contact: "which contact is (this) estimate EST-N for"
(
    re.compile(
        r"^which\s+contacts?\s+(?:is|are)\s+(?:this\s+|the\s+)?estimate\s+"
        r"(?P<name>[A-Za-z0-9-]+)\s+for\??$",
        re.IGNORECASE,
    ),
    "list_contacts",
    "estimate",
    None,
),
# estimate → contact (+ property): "who is (this) estimate EST-N for"
(
    re.compile(
        r"^who\s+is\s+(?:this\s+|the\s+)?estimate\s+"
        r"(?P<name>[A-Za-z0-9-]+)\s+for\??$",
        re.IGNORECASE,
    ),
    "list_contacts",
    "estimate",
    "include_property",  # repurpose role_hint slot for the decorator flag
),
```

Repurposing `role_hint` for `include_property` is a slight overload of the existing tuple shape. Acceptable for one new flag; if a second flag arrives, refactor the tuple to a typed dataclass.

**Property agent join handler** — new branch in the Property agent's list/get path (mirrors how Material agent handles `cross_type=estimate` in Wave 3):

1. Read `context["filter_by"]`. If `type == "estimate"`, take `name` as the EST code.
2. `estimate = await find_estimate_by_code(company_id, name)`. If `None`, respond "I couldn't find an estimate with that code."
3. If `estimate.property is None`, respond "Estimate {EST} isn't linked to a property yet."
4. Load `Property.get(estimate.property)`; format as a single-property get response (reuse the existing details renderer).

**Contact agent join handler** — new branch:

1. Read `context["filter_by"]`. If `type == "estimate"`, take `name` as the EST code.
2. Resolve estimate → property as above.
3. Load contacts via `Contact.find({"_id": {"$in": property.contacts}})`.
4. If `filter_by["role_hint"] == "include_property"`, lead the response with the property name/address (e.g. *"Estimate EST-0042 is for John Doe and Jane Doe at 123 Main St, Vancouver."*); otherwise the standard contact-list response copy.
5. Empty-result fallbacks: "Estimate {EST} isn't linked to a property yet." / "The property linked to estimate {EST} has no contacts yet."

### Workstream B — Property-anchored estimate list (1 phrasing)

Phrasing 4. The user names a property and asks for its estimates.

**Routing:**

| Phrasing | Intent | `cross_type` | Target agent |
|---|---|---|---|
| `show me estimate(s) for property {property}` | `list_estimates` | `property` | Estimate |
| `what estimates are for {property}?` (additional) | `list_estimates` | `property` | Estimate |
| `estimates linked to {property}` (additional) | `list_estimates` | `property` | Estimate |

**Pattern** (add to `_CROSS_RESOURCE_QUERY_PATTERNS`):

```python
# property → estimate: "show me estimate(s) for property X" / "what estimates
# are (linked to|for) property X" / "estimates (linked to|for) X"
(
    re.compile(
        r"^(?:show\s+me\s+)?estimates?\s+(?:linked\s+to\s+|for\s+)"
        r"(?:property\s+)?(?P<name>.+?)\??$",
        re.IGNORECASE,
    ),
    "list_estimates",
    "property",
    None,
),
(
    re.compile(
        r"^what\s+estimates?\s+(?:is|are)\s+(?:linked\s+to|for)\s+"
        r"(?:property\s+)?(?P<name>.+?)\??$",
        re.IGNORECASE,
    ),
    "list_estimates",
    "property",
    None,
),
```

**Anchoring caveat:** the first pattern's broad shape (`estimates? for X`) risks eating phrasings like "estimates for review" if the matcher doesn't anchor to a real property. Mitigations:
- Require anchoring at start/end (already enforced by `^…$`).
- If `find_properties_by_name_or_address` returns 0 matches, fall through to the existing `list_estimates` status-keyword path rather than refusing — the user probably meant the status filter.
- Keep the property-pattern AFTER the existing status-filter rules in `_CROSS_RESOURCE_QUERY_PATTERNS` ordering so the more specific match wins. (The matcher walks in declaration order — verify by reading `_match_cross_resource_query` before adding.)

**Estimate agent join handler** — extend the existing Wave 3 cross-resource branch in `_handle_list_estimates`:

1. Read `context["filter_by"]`. If `type == "property"`:
   - `properties = await find_properties_by_name_or_address(company_id, name)`
   - 0 matches → "I couldn't find a property matching '{name}'."
   - 2+ matches → existing disambiguation copy
   - 1 match → query `Estimate.find({"company": company_id, "property": property._id})`, format as standard estimate-list response with the property name in the lead-in.
2. Empty estimate list → "{property name} doesn't have any estimates yet."

## Tests

Add to `platform/tests/`:

- **`test_orchestrator_intents.py`** — unit tests for the four new patterns: each must classify to the right intent + `cross_type`, including the `include_property` flag for the "who is" variant.
- **`test_estimate_agent.py`** — integration test for the property-anchored estimate list (Workstream B): seed a property + 2 estimates linked to it, query `show me estimates for property {addr}`, assert the list contains both.
- **`test_property_agent.py`** / **`test_contact_agent.py`** — symmetric integration tests for the estimate-anchored handlers (Workstream A): seed an estimate with a linked property and 2 contacts, query each phrasing, assert the right entities + lead-in copy.
- **`test_maple_crud_coverage.py`** — extend the existing `cross_resource` category in `_maple_coverage_data.py` with the four new phrasings (or add a small `estimate_outbound` category if mixing them muddles the per-resource counts). Tier 1 target after this wave: 121/121.
- **Reference doc** — flip the four §1.8 ⚠️ rows to ✅ with a "closed in xfail-wave-4" note, update the snapshot count in §10.3, bump "Last updated" in the header.

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Pattern #4's broad `estimates? for X` swallows status phrasings (`estimates for approval`) | Medium | Anchor + ordering; fall through on 0-property-matches; add explicit negative test for `estimates for approval`, `estimates for review`. |
| `Estimate.property` is nullable so old estimates won't match — existing data may surprise users | Low | Empty-list copy explicitly says "isn't linked to a property yet" so the user understands why. |
| `include_property` overloading the `role_hint` slot ages poorly | Low | Acceptable for one flag; refactor `_CROSS_RESOURCE_QUERY_PATTERNS` element shape to a dataclass if a second flag lands. |
| LLM tier (Tier 2) classifies these phrasings differently — false positives in Tier 1 vs Tier 2 disagreement | Medium | These are rule-tier additions; Tier 2 already routes most via LLM today. Run Tier 2 once after shipping to confirm no regression. |

## Out of scope

- Multi-property estimate links (current `Estimate.property` is a single id; extending to a list is a separate model change).
- Editing the link via Maple (`link {EST} to {property}` is already covered by §1.6, currently 🤖 LLM — promoting it to a rule is a separate workstream).
- §11 conceptual blind spots (date/numeric/multi-action/anaphora/ambiguity) — those remain a backlog, not gaps.

## Done criteria

1. The four phrasings classify on Tier 1 with the right intent + agent + `filter_by` payload.
2. The four §1.8 ⚠️ rows in `maple-phrasing-reference.md` flip to ✅ with the wave-4 note.
3. `tests/reports/maple_crud_gap_report.md` regenerates clean (no new failures).
4. `test_maple_crud_coverage.py` passes on Tier 1 with the new rows added.
5. The header's "Last updated" line and §10.3 snapshot reflect the new totals.

## Estimated effort

~½ day for Workstream A (3 phrasings, mostly mechanical pattern additions plus two agent-side join branches that mirror Wave 3 Workstream C).
~¼ day for Workstream B (1 phrasing, 1 agent-side branch in the Estimate agent's list handler).
~¼ day for tests + doc updates.

Total: ~1 working day. Lower priority than other backlog items unless a user explicitly asks one of these phrasings.
