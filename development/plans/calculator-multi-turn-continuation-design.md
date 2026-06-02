# Design: Calculator Multi-Turn Continuation

**Date:** 2026-06-01
**Status:** Approved (Approach A)
**Author:** Maple engineering (via Claude Code brainstorming)

## Problem

When a user asks Maple a landscaping calculation (e.g. mulch coverage) and
provides the parameters **piecemeal across conversation turns**, Maple loses
context and misroutes the follow-up answers.

Observed failure (mulch coverage):

1. User: "how many square feet, at 3-inches, will a yard of mulch cover"
2. Maple: "I can help with mulch coverage calculation! I just need a couple
   more details: the area (in square feet)?"
3. User: "750 square feet" → Maple: **"I couldn't find any matching
   properties."** (wrongly routed to the Property Agent)
4. User: "750" → same wrong response
5. User: "can you help with mulch coverage?" → "That's outside what I've got
   in my toolkit right now"

When **all** parameters are supplied up front ("how many yards of mulch do I
need to cover 750 sq ft at 3-inches deep") the calculation works perfectly.

## Root Cause

The Calculator Agent does **not** participate in Maple's multi-turn machinery.

- Other CRUD agents (Contact/Property/etc.) write a `pending_intents` entry
  into the conversation context when they ask a clarifying question. On the
  next turn the router's `_get_pending_fallback_match()` re-routes the reply to
  the same agent.
- The Calculator Agent's `_clarification_response()`
  (`agents/calculator/service.py:300-311`) asks for the missing detail but
  stores **nothing**. The next message is re-classified from scratch:
  - `"750 square feet"` fails `is_calculation_query()` (no question verb), then
    `"square feet"` reads as address-like and routes to the **Property Agent**.
  - bare `"750"` matches no domain → falls through.
  - The partial parameters captured in turn 1 (depth=3, material=mulch) are
    discarded.
- Re-engagement ("can you help with mulch coverage?") also fails
  `is_calculation_query()` (unit present, no trigger verb) → off-topic.

## Scope

**In scope:** multi-turn continuation only — the Calculator remembers partial
parameters across turns and absorbs piecemeal replies until the calculation is
complete.

**Out of scope (explicitly deferred):**

- Re-engagement phrase detection ("can you help with mulch coverage?").
- Inverse coverage calculation ("how many sq ft will a yard cover" → solve for
  area). Note: the gathered *forward* result (6.94 cu yd) happens to match what
  the user wanted, so there is no regression from leaving this unsupported.

**Pivot policy:** if the user clearly switches to a different intent while a
calculation is half-gathered, the pending calculation is **dropped silently**
and normal routing proceeds.

## Approach

**Approach A — dedicated router pre-handler + pending-calc state.** Mirror the
existing `handle_pending_estimate_gathering` precedent.

Rejected alternatives:

- **B — reuse only the `pending_intents` fallback.** That fallback only fires
  when intent classifies as `unknown`; `"750 square feet"` classifies as
  `get_property` at 0.9 confidence, so it would still misroute.
- **C — loosen `is_calculation_query()`.** Makes the pre-classifier greedy;
  bare numbers/units would steal legitimate CRUD messages. High blast radius.

## Components

### 1. Calculator persists pending state

In `agents/calculator/service.py`, the missing-params branch
(`service.py:135-145`) writes a `pending_calculation` blob into the returned
context before asking:

```python
ctx["pending_calculation"] = {
    "calculation_type": params.calculation_type,
    "fields": {<all non-null params as a dict>},   # e.g. {"depth_inches": 3}
    "missing_fields": missing,                       # e.g. ["area_sqft"]
    "material_name": params.material_name,           # "mulch"
}
```

On a **successful** computation, and on the generic "unknown calc type"
clarification, the agent **clears** `pending_calculation` from ctx so stale
state never lingers.

### 2. Targeted continuation extraction

New helper in `agents/calculator/text_helpers.py`:

```python
extract_continuation_values(message, missing_fields, calculation_type) -> dict
```

- Pulls values for the **specific** missing fields using the existing field
  regexes (area, depth, length, width, paver dims, etc.) **without** the
  `is_calculation_query` question-verb gate.
- If exactly one field is missing and the message is a bare number ("750"),
  assigns it to that field.
- Returns only the fields it could fill (possibly empty).

### 3. Calculator continuation entry point

New method `CalculatorAgent.continue_pending(message, pending, context)`:

1. Rebuild a `CalculationRequest` from `pending["fields"]` +
   `calculation_type`.
2. Merge in `extract_continuation_values(...)`.
3. Recompute missing fields:
   - still missing → re-store the updated `pending_calculation`, re-ask with
     the same friendly clarification copy.
   - complete → dispatch the calculation, **clear** `pending_calculation`,
     return the normal result envelope.

### 4. Router pre-handler

New `handle_pending_calculation(message, merged_context, calculator_agent)` in
a small `routers/agent_helpers/` module, wired into the chat endpoint right
after the `is_help_query` short-circuit and alongside the estimate pending
handlers (`agents.py:815-834`):

- No `pending_calculation` in context → return `None` (normal flow).
- Present → decide **continuation vs. pivot**:
  - **Pivot (drop silently):** the message is a clear new command — matches an
    ACTION+DOMAIN CRUD pattern, or is a help / fresh full `is_calculation_query`
    — **and** yields no continuation values. Remove `pending_calculation` from
    `merged_context` and return `None` so normal routing proceeds.
  - **Continuation:** otherwise call `continue_pending(...)` and return its
    result, short-circuiting the orchestrator.

## Data Flow (image 1, fixed)

```
T1 "...3-inches...mulch cover"  → calc, missing area → stores pending_calculation, asks
T2 "750 square feet"           → handle_pending_calculation → extract area_sqft=750
                                  → complete → 6.94 cu yd → clears pending ✓
```

Bare `"750"` works identically (single missing field → bare number assigned).

## Error Handling & Edge Cases

- Pending state lives in the per-conversation context, which is already TTL'd —
  no new persistence surface.
- Pivot-detection failure is graceful: worst case a stray reply re-asks the
  clarification instead of misrouting.
- Clearing `merged_context["pending_calculation"]` in the pivot path mutates the
  same dict that the orchestrator result + `finalize_orchestrate_result` persist,
  so the drop is saved.

## Testing (TDD)

Write failing tests first, then implement.

- `text_helpers`: `extract_continuation_values` — bare number, units-only
  fragment, multi-field, nothing-extractable.
- Calculator: `continue_pending` completes / re-asks / clears state.
- Router handler: continuation path, pivot-drops-silently path, no-pending
  pass-through.
- Update `documentation/development/maple-phrasing-reference.md` (multi-turn
  calc phrasings) per the CLAUDE.md doc-sync rule.
- Run `./run_mypy.sh` after the Python changes (zero-error gate).
```
