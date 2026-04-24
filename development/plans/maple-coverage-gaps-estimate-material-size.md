# Close Maple coverage gaps: estimate status-count queries & material-size operations

## Context

A coverage audit (`maple-input-coverage-audit.md`) flagged 10 user phrasings that either aren't exercised by the coverage matrix or aren't handled at all by the classifier:

**Estimate status / value queries**
1. "How many estimates with status draft?"
2. "What's the total estimates with status approved?"
3. "Can you add up the estimates with status approved?"
4. "What is the value of estimate EST-0042?"

**Material × size operations**
5. "Find material concrete blocks with size 12x12"
6. "How much is concrete blocks with size 12x12?"
7. "Update the cost for concrete blocks with size 12x12 to $5"
8. "Update the price for concrete blocks with size 12x12 to $5"
9. "Delete size 12x12 for concrete blocks" (reject if it's the last size)
10. "Add size 24x24 to concrete blocks with cost $8 and unit each" (must require both)

## Audit findings

Verified by running the TDD test files (`test_maple_estimate_status_queries.py`, `test_maple_material_size_operations.py`) against the current rule-based classifier (`use_llm=False`):

| # | Phrasing | Tier 1 (rule) | Gap? |
|---|---|---|---|
| 1 | "how many estimates with status draft?" | ✅ `list_estimates` | No — just missing from matrix |
| 1-var | "how many approved estimates do I have?" | ✅ `list_estimates` | No |
| 1-var | "count my draft quotes" | ✅ `list_estimates` | No |
| 2 | "what's the total estimates with status approved?" | ✅ `list_estimates` | No |
| 3 | "can you add up the estimates with status approved?" | ❌ `unknown` | **Yes — "add up" not in `is_count_query`** |
| 4 | "what is the value of estimate EST-0042?" | ✅ `get_estimate` | No |
| 4-var | "what's the total for EST-0042?" | ❌ `unknown` | **Yes — grand-total pattern requires "estimate" keyword** |
| 4-var | "how much is EST-0042?" | ❌ `unknown` | **Yes — "how much is" + bare EST-code doesn't match** |
| 5-10 | All material-size operations | ❌ `unknown` or generic | **Yes — no size-scoped intents exist** |

**Material model invariants** (`platform/models/material.py:8-28`):
- `MaterialSizeCost(size, unit, cost, price)` — cost is required float, unit is required ObjectId, price is optional. **Cost and price are distinct fields.**
- `Material.sizes: List[MaterialSizeCost] = Field(..., min_length=1)` — model-layer guard against empty-sizes state. Unreachable from chat today.

**Bonus finding from running the tests:** sizeless phrasings like "update the cost for concrete blocks to $5" already resolve to `unknown` on Tier 1 (the rule classifier doesn't detect "update the {field} for {name}" phrasings for materials at the material level — it relies on the LLM tier). Negative tests for the new size-intent regexes therefore only assert "does not falsely claim a size intent", not "routes to the correct base intent".

Relevant source:
- `platform/models/material.py:8-28` — `MaterialSizeCost` + `min_length=1` invariant
- `platform/agents/orchestrator/intents.py:29-36` — current Material Agent intents
- `platform/agents/material/service.py` — current Material Agent handlers (no size-scoped logic)
- `platform/agents/estimate/service.py:3535-3670, 3746-3850` — list + grand-total handlers
- `platform/agents/text_utils.py` — `is_count_query`, `format_count_response`, `humanize_field_name`

Relevant source:
- `platform/models/material.py:8-28` — `MaterialSizeCost` (size/unit/cost, price optional) and `min_length=1` invariant
- `platform/agents/orchestrator/intents.py:29-36` — current Material Agent intents
- `platform/agents/material/service.py` — current Material Agent handlers (no size-scoped logic)
- `platform/agents/estimate/service.py:3535-3670, 3746-3850` — list + grand-total handlers already in place
- `platform/agents/text_utils.py` — `is_count_query`, `format_count_response`, `humanize_field_name`

---

## Phase A — Estimate status & value query gaps

**File:** `platform/tests/test_maple_estimate_status_queries.py` (committed)

Status after running against the current classifier:

- 5 phrasings **PASS today** — locked in as regression tests.
- 3 phrasings **fail on Tier 1**, now marked `xfail(strict=True)` so the runs stay green but flip to XPASS (→ failure) the moment they're fixed.

### The three real gaps

**A1. "add up" as a count-query trigger.**
Add "add up" / "add them up" / "sum up" to the patterns in `is_count_query()` at `platform/agents/text_utils.py`. One-line change, plus extend the existing unit tests for `is_count_query`.

**A2. Grand-total pattern when "estimate" keyword is absent.**
"what's the total for EST-0042?" has no "estimate" word — the pattern at `_GRAND_TOTAL_QUERY_PATTERN` (`platform/agents/estimate/service.py:325`) appears to gate on it. Loosen the pattern to also trigger on an explicit EST-code token. Check whether broadening breaks the existing estimate tests.

**A3. "how much is EST-0042?" with no verb.**
The bare-EST-code + "how much" phrasing needs a dedicated rule in the orchestrator or estimate agent's pre-filter: if the phrasing contains an EST-code token AND price-query vocabulary ("how much", "price", "worth"), route to `get_estimate` with the grand-total framing.

All three are small, localized rule additions. No new intents needed — the existing `get_estimate` + `_GRAND_TOTAL_QUERY_PATTERN` handler already returns the correct response shape once the router reaches it.

### Flip sequence (TDD)

1. Remove the `xfail` marker on the "add up" case.
2. Add "add up" / "sum up" / "add them up" to `is_count_query()` patterns.
3. Run `./run_tests.sh tests/test_maple_estimate_status_queries.py` — should go green.
4. Repeat for A2 and A3.

---

## Phase B — Classifier rules for size-scoped phrasings

**Major scope correction.** Walking through `platform/agents/material/service.py` reveals the Material Agent **already implements** size-level CRUD via the `fields` dict on the existing `update_material` / `get_material` intents:

| Capability | Location | Status |
|---|---|---|
| Remove a size from `sizes` list | `_build_sizes_from_fields()` when `size_op="remove"` (service.py:425-430) | ✅ exists |
| Last-size delete refusal | `_handle_update_material()` checks `existing_size_count <= 1` (service.py:1953-1980) | ✅ exists with friendly copy |
| Rename a size | `size_op="rename"` branch (service.py:435-439) | ✅ exists |
| Per-size unit update | Async unit-OID resolution → write to entry (service.py:1985+) | ✅ exists |
| Per-size price/cost update (multi-size material) | `size_value + price/cost` branch (service.py:466-477) | ✅ exists |
| Append new size entry | Same branch — falls through to `base_sizes.append(...)` when no match (service.py:471-478) | ⚠️ exists but auto-fills `cost = price` if cost missing, does NOT enforce "both cost and unit required" |
| Size text normalization | `_normalize_size_text()` | ✅ exists |

**Implication:** Phase B doesn't need 5 new intents or 5 new handlers. It needs:

1. **Classifier rules** that extract `{size, cost, price, unit, size_op}` from the target phrasings and route to the existing `update_material` / `get_material` intents.
2. **A small agent tweak** for the add-size path to refuse instead of silently defaulting `cost := price` when cost is omitted.
3. **A size-scoped response variant** on `get_material` for "how much is X with size Y" (renders a single `MaterialSizeCost` row, not the whole material).

This makes Phase B ~1/3 the original scope. The xfailed tests in `test_maple_material_size_operations.py` need updating — they currently assert `intent == "update_material_size_cost"` (which wouldn't exist); they should assert `intent == "update_material"` with the right `fields` dict.

### B1. Orchestrator rules (additions to `agents/orchestrator/service.py`)

Insert near the existing `add_work_item` rules at `service.py:230-248`. All rules short-circuit only when a **size token is explicitly present** — no size token means the existing `update_material` / `get_material` path applies unchanged.

```python
# Size-token detector — run on the normalized message. Matches "size 12x12",
# "size small", "size 1/2\"", etc. Anchored to require the literal word
# "size" before the token to avoid false positives on dimensions in
# addresses, estimate codes, etc.
_SIZE_TOKEN_PATTERN = re.compile(
    r"\bsize\s+([A-Za-z0-9][\w\-/×x\".\s]*?)"
    r"(?=\s+(?:to|for|with|and|from|on)\b|[?.!,]|\s*$)",
    re.IGNORECASE,
)
```

Five new short-circuits, in this order:

1. **Delete size** — `r"\b(?:delete|remove|drop)\s+size\s+\S+\s+(?:from|for)\s+(?:material\s+)?.+"` → route to `update_material` with `fields={"size": <S>, "size_op": "remove"}`. Covers phrasing 9.

2. **Add size with cost + unit** — `r"\b(?:add|create|new)\s+size\s+\S+\s+(?:to|on|for)\s+(?:material\s+)?.+?\s+(?:with\s+)?cost\s+[$\d]"` → route to `update_material` with `fields={"size": <S>, "cost": <N>, "unit": <U>, ...}`. Covers phrasing 10. If the phrasing has a size + material but is missing cost OR unit, stash `awaiting_size_fields = {"size": S, "material": M, "cost": cost_or_none, "unit": unit_or_none}` and ask for the missing field.

3. **Update cost for size** — `r"\bupdate\s+(?:the\s+)?cost\s+for\s+.+?\s+with\s+size\s+\S+\s+to\s+[$\d]"` → route to `update_material` with `fields={"size": <S>, "cost": <N>}`. Covers phrasing 7.

4. **Update price for size** — same regex with `cost` → `price`, `fields={"size": <S>, "price": <N>}`. Covers phrasing 8.

5. **Find / how-much-is with size** — `r"\b(?:find|show|get|how\s+much\s+is)\s+.+?\s+with\s+size\s+\S+"` → route to `get_material` with `fields={"size": <S>, "view": "size_only"}`. Covers phrasings 5 and 6.

**Key regex behaviors:**
- All rules are **gated on presence of an explicit size token** via `_SIZE_TOKEN_PATTERN` — phrasings without "size X" stay on the existing paths.
- Order matters: delete / add before update-cost / update-price before find (add carries the most specific preconditions).
- Extraction uses named groups so the fields dict is built in one pass; use `_parse_cost()` (already in `material/service.py`) for dollar amounts.

### B2. Agent tweak for add-size (`agents/material/service.py`)

Current `_build_sizes_from_fields()` append path at service.py:471-478:

```python
base_sizes.append({
    "size": size_value,
    "price": float(price_value),
    "cost": float(cost_value) if isinstance(cost_value, (int, float)) else float(price_value),
})
```

This silently defaults `cost := price` when cost is missing. For the add path we want a hard refusal:

- Add a pre-check at the top of `_handle_update_material` (near line 1953 where the last-size refusal lives): when the computed payload would **append a new size entry** AND either `cost` or `unit` is missing in the parsed `fields`, stash the partial payload as a pending intent and return a clarifying question.
- Pending-intent slot name: `awaiting_add_size_for` (distinct from the existing `awaiting_value_for` field-update flow to avoid collision).
- Pending payload: `{"material_id": ..., "size": ..., "cost": <maybe>, "price": <maybe>, "unit": <maybe>}` — stored in session state, keyed by conversation id.
- On next user turn, the agent's pending-intent resolver tries to parse the missing field(s) and either completes the add or re-asks.

Clarification copy:
> "I need a {cost|unit} for size '{size}' on {material_name}. What should I use?"

For the cost-missing case, accept a dollar amount or number on next turn.
For the unit-missing case, accept a unit name and resolve it via the existing async unit-lookup pattern in `_handle_update_material`.

### B3. Size-scoped get response

Extend `_handle_get_material` so when `fields.get("size")` is present:

- Resolve the material as today.
- Scan `material.sizes` for a case-insensitive match on `size`.
- If no match: `"I couldn't find size '{size}' on {material_name}. Available sizes: {list}."`
- If match: render just that one `MaterialSizeCost` row with `"Here are the details for {material_name} (size {size}):\n- Cost: ${cost}\n- Price: ${price or '—'}\n- Unit: {unit_name}"`.

This is the only new response string. Everything else (delete success, delete refusal, update success, add success) is already emitted by the existing `_handle_update_material` success path.

### B4. Response strings (match friendly first-person template)

Already emitted by existing handlers — no new copy needed except the size-scoped get above and the two add-clarification prompts in B2.

Sanity check of the existing `update_material` success path: does it mention the field that changed ("updated the cost", "updated the price") or generic ("updated the material")? Skim `_handle_update_material` and its `_format_update_summary` helper to confirm the diff summary reads naturally for size-scoped updates. If it says generic "updated the material" we might want a size-aware summary branch; punt that as a follow-up only if the copy feels awkward after B1 lands.

---

## Phase C — TDD implementation order

### Step 1. Fix the xfail tests to assert the revised (fields-payload) architecture

The currently-committed `test_maple_material_size_operations.py` asserts `intent == "update_material_size_cost"` etc. — those intents won't exist in the revised plan. Rewrite each xfailed test to assert:

- `intent == "update_material"` or `"get_material"` (existing intents)
- The extracted `fields` dict has the expected keys (requires exposing the parsed fields in the orchestrator return, or a second test pass that goes through the Material Agent's `process()` and inspects the DB state after).

Simpler approach for the classifier-level tests: assert `intent` + `agent` only, and move field-payload assertions to handler integration tests in `test_material_agent.py` (or a new `test_material_agent_size.py`).

Rewrite the 8 xfailed classifier tests as follows (still xfail until B1 lands):

| Phrasing | Expected `intent` | Expected fields (asserted in handler test) |
|---|---|---|
| "find material concrete blocks with size 12x12" | `get_material` | `{"size": "12x12"}` |
| "how much is concrete blocks with size 12x12?" | `get_material` | `{"size": "12x12"}` |
| "update the cost for concrete blocks with size 12x12 to $5" | `update_material` | `{"size": "12x12", "cost": 5}` |
| "update the price for concrete blocks with size 12x12 to $5" | `update_material` | `{"size": "12x12", "price": 5}` |
| "delete size 12x12 for concrete blocks" | `update_material` | `{"size": "12x12", "size_op": "remove"}` |
| "add size 24x24 to concrete blocks with cost $8 and unit each" | `update_material` | `{"size": "24x24", "cost": 8, "unit": "each"}` |
| "add size 24x24 to concrete blocks with cost $8" (missing unit) | `update_material` | needs_clarification, awaiting_add_size_for populated |
| "add size 24x24 to concrete blocks with unit each" (missing cost) | `update_material` | needs_clarification, awaiting_add_size_for populated |

### Step 2. Handler integration tests (new file)

`platform/tests/test_material_agent_size.py` — seed a material with two sizes, then exercise each end-to-end:

1. `get_material` with `size` filter returns just that `MaterialSizeCost` row
2. `update_material` with `size + cost` persists the new cost and leaves price unchanged
3. `update_material` with `size + price` persists the new price and leaves cost unchanged
4. `update_material` with `size + size_op=remove` rejects when `len(sizes) == 1` (use a single-size fixture), succeeds when `len(sizes) > 1`
5. `update_material` appending a new size with `cost + unit + size` — persists
6. `update_material` appending with **missing unit** — returns `needs_clarification`, does not persist, stashes `awaiting_add_size_for`
7. `update_material` appending with **missing cost** — same
8. Follow-up turn providing the missing field — completes the add

### Step 3. Implement Phase B in order

1. Wire the 5 classifier rules (B1) in `agents/orchestrator/service.py`. Flip xfail on the 6 core classifier tests.
2. Add the size-scoped `get_material` response branch (B3). Integration test #1 goes green.
3. Add the add-size missing-field refusal + pending-intent slot (B2). Integration tests #6-8 go green.
4. Run the existing `test_material_agent.py` full file — verify no regression on non-size phrasings.

### Step 4. Add a `material_size` category to the coverage matrix

Once all tests are green, extend `platform/tests/_maple_coverage_data.py` with a new category restricted to the material resource:

```python
def _material_size(tok, _resource) -> PhrasingList:
    # resource is always "material" — see CATEGORIES entry below
    return [
        (f"find material {tok['name']} with size 12x12", "get_material"),
        (f"how much is {tok['name']} with size 12x12?", "get_material"),
        (f"update the cost for {tok['name']} with size 12x12 to $5", "update_material"),
        (f"update the price for {tok['name']} with size 12x12 to $5", "update_material"),
        (f"delete size 12x12 for {tok['name']}", "update_material"),
        (f"add size 24x24 to {tok['name']} with cost $8 and unit each", "update_material"),
    ]

# In CATEGORIES:
("material_size", _material_size, False, False, ("material",)),
```

No new `INTENT_TO_AGENT` entries needed — everything routes to the existing `update_material` / `get_material` → Material Agent mapping.

---

## Risks & open questions

1. **Regex gating on size token.** All five rules must require a literal "size <X>" token to fire. Negative tests (already in the test file) guard against falsely routing sizeless phrasings to size-scoped behavior.

2. **Size token grammar.** "12x12", "12 x 12", "1/2\"", "3/4 inch" should all work. "Small" / "Medium" as sizes are legitimate but risk colliding with adjectives elsewhere in phrasings — the regex accepts them, and the agent falls back to a case-insensitive lookup against `material.sizes`; an unmatched size produces a "no such size" clarification rather than silently failing.

3. **Unit disambiguation UX.** The existing per-size unit update in `_handle_update_material` already does async `MaterialUnit` resolution; reuse it. On 0 matches, clarify with the list of available unit names. On multiple fuzzy matches, list them and ask the user to pick. Exact-match first, then fuzzy.

4. **Multi-turn state: `awaiting_add_size_for` vs existing `awaiting_value_for`.** Two distinct slots. `awaiting_value_for` resolves a bare field name → ask for value (existing Property/Contact/Material/Labour flow). `awaiting_add_size_for` stores a partial `{material_id, size, cost?, price?, unit?}` payload and loops until both cost and unit are present. They should never collide on the same turn — if both would apply, `awaiting_add_size_for` wins because it's the more specific pending intent.

5. **Add-size: user says "cost $8" but not "unit each" (or vice versa).** Stash + ask. **User says only "add size 24x24 to concrete blocks"** (no cost, no unit) — same flow; ask for cost first, then unit. Each clarification turn only asks for one missing field.

6. **Silent `cost := price` fallback in the existing append path** (service.py:471-478) — currently masks missing-cost errors. The B2 pre-check intercepts before the builder runs, so the fallback stays intact for other callers (LLM-extracted fields, API-driven updates) that may still want it.

7. **"Find material X with size Y" vs "list materials with size Y".** Recommendation: treat phrasing 5 as `get_material` with a `size` filter — it's asking for one row on one material, not a collection. If users want "list all materials that have size 12x12" that's a separate future intent.

8. **Phase A gap behavior on Tier 2 (LLM).** The 3 xfailed Phase A tests pass on Tier 1 only after the rule additions. Before committing, spot-check that the LLM tier already handles them (likely yes — LLM is good at "add up" / "how much is"). If so, the Phase A fix just closes the rule-path gap; no LLM prompt changes needed.

9. **`delete_material_size` via HTTP router.** Out of scope. Maple-only policy; if the web UI needs it, spec separately.

10. **Scope reduction.** Original Phase B scoped 5 new intents + 5 handlers + new helpers + unit resolver. Revised Phase B is 5 regex rules + 1 agent pre-check + 1 response variant. Roughly 1/3 the diff. The trade-off is that all size operations land inside `update_material` / `get_material` with `fields` as the discriminator, which keeps the intent surface small but makes the handler logic denser. Acceptable given the handler already has all the branching.

## UX decisions (locked)

- **Unit disambiguation on ambiguous match:** **inline list.** When a user-supplied unit name fuzzy-matches more than one `MaterialUnit`, reply with "I found N units matching '{input}': {name1}, {name2} — which one?" and stash a pending-intent slot for the follow-up. Exact match wins over fuzzy; on zero matches, ask for a valid unit with a short list of available names. User can revisit later if the inline list feels noisy.
- **Last-size delete refusal copy:** keep the existing string in `material/service.py:1958-1963` as-is — "I can't remove the last size from this material — it needs at least one size. Add another size first, or delete the material entirely if that's what you mean."
- **"Delete size X for material Y" confirmation:** no confirm — execute immediately, matches existing Maple delete UX (materials, contacts, etc. all execute without a confirm step).
- **Multi-size operations in one phrasing:** out of scope for v1. "delete sizes 12x12 and 24x24" → ask the user to pick one size. Revisit only if usage signals demand.

---

## Deliverables checklist

**Committed (TDD tests in place):**

- [x] `platform/tests/test_maple_estimate_status_queries.py` — 5 PASS + 3 xfail (Phase A gaps)
- [x] `platform/tests/test_maple_material_size_operations.py` — 10 PASS (negative tests) + 8 xfail (Phase B/C target intents)

**To do:**

- [ ] Phase A1 — widen `is_count_query()` to include "add up" variants
- [ ] Phase A2 — loosen `_GRAND_TOTAL_QUERY_PATTERN` to fire on bare EST-code
- [ ] Phase A3 — add "how much is <EST-code>" rule to orchestrator or estimate pre-filter
- [ ] Phase B1 — `intents.py`: 5 new intents + INTENT_TO_AGENT entries
- [ ] Phase B2 — `orchestrator/service.py`: size-detector regex + routing rules (positive + negative)
- [ ] Phase B3 — `material/service.py`: 5 handlers + `_find_size_row` + unit resolver + last-size guard
- [ ] Phase C3 — new `material_size` category in `_maple_coverage_data.py`
- [ ] All xfail markers flipped to hard assertions, coverage gap report regenerated
