# Maple — Fuzzy Property Matching on the Estimate→Property Link

**Status:** spec (not yet implemented)
**Date:** 2026-07-28

## Context

When Maple creates an estimate without a linked property it asks *"Would you like me to link this estimate to a property now?"*. The user's answer is resolved against the company's Property catalog by `_resolve_property_address` in `platform/agents/estimate/crud_helpers.py`.

That resolver matches by **substring only**. Anything the user types that isn't a literal substring of `name` or `street` — a typo, a re-worded address, a label combining both fields — resolves to zero matches and Maple answers *"I couldn't find a property matching …"*, even though the property is sitting right there.

Three defects on this path were fixed earlier on 2026-07-28 (see the change log in `maple-phrasing-reference.md`): the property identifier was being extracted with an `of this estimate to …` preamble attached, a failed lookup silently ended the follow-up, and composite `{name} - {street}` answers matched neither field. This spec covers the remaining gap: **the resolver has no tolerance for near-misses at all.**

Fuzzy matching is the right tool for *user* typos. It is deliberately **not** the fix for parser noise — the extraction fix stays load-bearing, and fuzzy sits behind it as a safety net. A resolver that quietly absorbs our own bad input hides the next parsing bug instead of surfacing it.

### Why difflib, and why this resolver is the odd one out

`agents/fuzzy_utils.py` already provides `fuzzy_best_matches()` (difflib `SequenceMatcher`, best-of whole-string and per-token overlap) and `fuzzy_disclaimer()`. The Property, Contact and Task agents and the estimate resolver all use it. The Estimate Agent's property lookup is the only resolver in the codebase that never adopted it. This is a consistency fix as much as a feature.

No new dependency. Scores below are measured, not estimated.

### Measured behavior

Against a catalog of `Primavera / 153 Asharoken Ave`, `Northside Depot / 9 Elm St`, `Maple Ridge / 12 Oak Rd`, using the extractor set in §2:

| Query | Best match | Score |
|---|---|---|
| `of this estimate to Primavera - 153 Asharoken Ave` (the mangled string from the bug report) | Primavera | 0.711 |
| `Primavera - 153 Asharoken Ave` | Primavera | 0.964 |
| `Primavera, 153 Asharoken Avenue` | Primavera | 0.931 |
| `primavara` (name typo) | Primavera | 0.889 |
| `153 Ashroken Ave` (street typo) | Primavera | 0.980 |
| `Bogus Place` | — | no match |
| `the property` | — | no match |

Signal lands at 0.71–0.98, noise below 0.52. The 0.65 default threshold sits cleanly in the gap. **The combined `name + street` extractor is what carries composite answers** — without it the first row scores 0.310 and misses.

## Design decisions

| Decision | Choice | Why |
|---|---|---|
| Fuzzy hit on a **write** (link) | Confirm before linking | Matches the existing house rule — `routers/agent_helpers/delegate_estimate_ops.py:104` stashes a pending fuzzy-confirmation rather than mutating on a guess. |
| Fuzzy hit on a **read** (list filter) | Proceed, name what matched | A confirmation gate in front of a read-only query is friction for no safety gain. Mirrors how the Property/Contact agents treat reads. |
| Several candidates above threshold | List the top matches, ask which | Reuses the numbered disambiguation the resolver already has for exact multi-matches, so fuzzy and exact behave identically when ambiguous. |
| Threshold | `0.65` (the `fuzzy_utils` default) | One less knob; the measured gap is wide; and confirm-before-write makes a rare false hit cost exactly one "no". |

## Changes

### 1. Add a fuzzy tier to `_resolve_property_address`

**File:** `platform/agents/estimate/crud_helpers.py`

The resolver becomes three tiers, each firing only when the previous found nothing:

```
tier 1   query ⊆ name/street        (strict substring — unchanged)
tier 2   name/street ⊆ query        (composite labels — added 2026-07-28)
tier 3   fuzzy_best_matches(...)    (NEW)
```

Tiering is the safety property: **every resolution that works today is byte-identical**, because tier 3 only runs where the current code already returns "no match".

Extractors passed to `fuzzy_best_matches`, mirroring the Property agent's set at `agents/property/service.py:855`:

- `name`
- `street`
- `f"{name} {street}"` — the combined form (see §Measured behavior)
- `f"{street}, {city} {prov_state} {postal_zip}"` — full address

Threshold `0.65`, `max_results=5`.

The return dict gains two keys alongside the existing `property_id` / `matches` / `error`:

- `fuzzy: bool` — True when the result came from tier 3
- `score: float` — best score, `0.0` for tiers 1–2

Callers vary their UX off `fuzzy` without re-scoring. Existing keys keep their current meaning, so no caller breaks.

Import `fuzzy_best_matches` at module level (not inside the function) — `crud_helpers.py` has no circular-import constraint with `agents/fuzzy_utils.py`.

### 2. Link handler — confirm a fuzzy match before writing

**File:** `platform/agents/estimate/crud_handlers.py` (the `link_op == "link"` branch, ~line 2858)

Behavior by resolution outcome:

| Outcome | Response |
|---|---|
| 0 matches | Unchanged — `I couldn't find a property matching "{identifier}".` |
| 1 match, not fuzzy | Unchanged — link and confirm |
| **1 match, fuzzy** | **New** — stash the pending record (§4), do **not** write |
| >1 match | Unchanged numbered disambiguation, now also reachable from tier 3 |

The fuzzy question reuses `fuzzy_disclaimer()` so the wording matches every other fuzzy confirmation in the app:

> I believe you are looking for 'Primavera - 153 Asharoken Ave'. If this is not the right one, please let me know. Please confirm and I'll link it to estimate 'EST-DF5EBD1D'.

Returned via `_crud_envelope(..., needs_clarification=True, clarifying_question=…, context=context)` — `_crud_envelope` passes `context` through unmodified, which is how the pending record reaches the next turn.

### 3. List handler — disclose, don't gate

**File:** `platform/agents/estimate/crud_handlers.py` (`_handle_list_estimates`, ~line 970)

On a single fuzzy hit, filter as normal and name the resolved property in the lead-in:

> Showing estimates for 'Primavera - 153 Asharoken Ave': …

Zero and multi-match paths are unchanged.

### 4. New pending record: `pending_property_link_confirmation`

**File (new):** `platform/routers/agent_helpers/pending_property_link.py`

A small state machine in the shape of the existing `pending_estimate_follow_up.py`. It is deliberately **not** the existing `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY`: that machine replays `original_message` after confirmation, which here would re-run the same ambiguous lookup and loop forever. The new record **pins the already-resolved `property_id`**, so an affirmative reply links directly with no re-resolution.

Record:

```python
{
    "estimate_id": "<Estimate _id>",
    "estimate_label": "EST-DF5EBD1D",
    "property_id": "<Property _id>",
    "property_label": "Primavera - 153 Asharoken Ave",
    "score": 0.711,
}
```

`handle_pending_property_link_confirmation(message, context_payload, agent)` returns the envelope when it owns the turn, else `None`. The Estimate Agent is injected (as `handle_estimate_fuzzy_confirmation` already does) so the handler can re-resolve without duplicating the tier logic from §1.

- **affirmative** → write the link via Beanie (`Estimate.get` → `.set({"property": …, "updated_at": …})`, the same seam `pending_estimate_follow_up.py:364` uses), clear the record, confirm
- **negative** → clear the record, *"Okay, I've left estimate 'EST-…' unlinked."*
- **clear pivot** (a different resolved intent, or an analytics/help query — with the `property` domain exempt, since a property name is a legitimate answer here) → clear the record, return `None` so the main pipeline takes the turn
- **anything else** → treat it as a **corrected property answer** and re-resolve it *inside the handler*, against the pinned estimate:
  - exact hit → link and confirm, clear the record
  - fuzzy hit → replace the record with the new candidate and ask again
  - no hit → report it and **keep the record armed**

The last rule is the one that needs care. The obvious implementation — clear the record and return `None` so the main pipeline re-resolves — recreates the bug fixed earlier on 2026-07-28: with no pending state, a bare `"Maple Ridge"` falls through to intent classification and comes back as *"Sure, I'll help you create an estimate!"*. **The correction must be handled inside the flow, never by handing a bare property name back to the classifier.** This is also why "no, I meant Maple Ridge" recovers in a single turn instead of requiring a bare "no" first.

### 5. Turn ordering and the re-arm interaction

**File:** `platform/routers/agents.py`

`handle_pending_property_link_confirmation` must run **before** `handle_pending_optional_follow_up` (currently line 1114).

This ordering is load-bearing, not cosmetic. The re-arm fix landed earlier today (`_rearm_on_unresolved`) restores the create-estimate follow-up at its collect-value stage whenever the delegated agent returns `needs_clarification` — which the new fuzzy question does. Without the ordering guard the user's "yes" would hit the follow-up machine first, match its `stage == COLLECT_VALUE and affirmative` branch, and re-ask *"Which property should I link estimate 'EST-…' to?"* — an infinite loop.

Second guard, belt-and-braces: `_rearm_on_unresolved` in `optional_follow_up.py` skips re-arming when the delegated context carries `PENDING_PROPERTY_LINK_CONFIRMATION_KEY`. One flow owns the turn — the same precedent as the legacy follow-up handler deferring to the generic one.

## Testing

TDD — failing tests first, per the CLAUDE.md policy.

**Resolver tiers** (`tests/test_maple_estimate_field_edits.py`, extending `TestPropertyResolutionCompositeLabel`)
- each tier in isolation; a tier-1 hit must never reach tier 3 (assert `fuzzy is False`)
- the measured table in §Measured behavior becomes a parametrized case set — **including the `Bogus Place` / `the property` rows that must NOT match**
- multi-match above threshold returns >1 candidate rather than silently picking the top score

**Link handler**
- fuzzy hit stashes the pending record and writes nothing (assert `save` was not called)
- exact hit still links in one turn with no confirmation

**Pending record** (new `tests/test_agent_helpers_pending_property_link.py`)
- affirmative links the pinned `property_id` without re-resolving (assert the resolver is never called)
- negative leaves the estimate unlinked
- pivot releases and returns `None`
- **a corrected property name is re-resolved inside the handler and never returns `None`** — the regression guard for the §4 trap; assert the record is either cleared-with-a-link or still armed, but the turn is always owned
- a corrected name that also matches only fuzzily re-asks with the *new* candidate

**Interaction / end-to-end**
- replay create → "yes" → fuzzy answer → "yes" and assert the link is written — this is the case that loops if §5's ordering is wrong
- the pivot escape still fires while a property confirmation is pending

**Gates:** `./run_mypy.sh` and `./run_ruff.sh` on `agents/estimate` + `routers/agent_helpers`; run the related test files only (not the full suite).

## Out of scope

- **No new fuzzy dependency.** difflib via `agents/fuzzy_utils.py` is the house standard; rapidfuzz/Levenshtein would be a project-wide decision, not one this feature should make unilaterally.
- **No fuzzy on the estimate side** of the link — estimate resolution already has its own fuzzy path (`estimate_resolver.py`) and its own confirmation machine.
- **No threshold tuning UI or per-company override.** One constant until there's evidence it needs to vary.
- **No change to the soft-negative gap** (`not right now`, `nah, leave it` are still read as property answers) — tracked separately in §10.4 of the phrasing reference.

## Follow-ups this may surface

The two parallel follow-up state machines (`optional_follow_up` + the legacy `pending_estimate_follow_up`) are now joined by a third pending record on the same user journey. All three bugs fixed on 2026-07-28 were cases where the newer machine lacked behavior the older one already had. Collapsing them is out of scope here but is getting harder to defer.
