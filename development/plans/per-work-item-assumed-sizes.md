# Per-work-item assumed sizes — decompose first, then assume

Status: **COMPLETE — all four phases built 2026-08-10**
Created: 2026-08-10
Related: [estimate-effort-calibration.md](estimate-effort-calibration.md) — sizes
feed `work_quantity`, so a wrong size multiplies straight into anchored hours.

## Context

A multi-item request gets **one** assumed size for the whole message.
`resolve_assumptions` runs during gathering — before the architect decomposes
anything — and does a single first-match-wins keyword lookup:

```
"build a paver patio and mow the lawn"  →  average lawn (5,000 sq ft)
```

That one number is injected into the requirement as
`Area size (assumed): 5000 square feet`, and architect rule 7 then tells the
model that "(assumed)" values are settled — *use them as given, do NOT
re-report them*. The architect is actively discouraged from inventing a sane
per-scope size. Result: a 5,000 sq ft paver patio.

The lawn recalibration (500 → 5,000 sq ft) made the single-scope numbers right
and this multi-scope interaction 10× worse. With effort anchoring in place
(`effort = size ÷ production rate`), a wrong size now multiplies into both
material quantities and labor hours on every scope it doesn't belong to.

## The design (decided)

> Decompose the request into work items first. Then, for each work item, check
> whether the user stated a size. Only the ones missing a size get an assumed
> value, according to **their own** job type.

```
architect decomposes → scopes (one scope = one work item)
for each scope:
    stated = parse_job_size(scope description)      # user gave THIS item a size?
    if stated:  nothing to assume — use it
    else:
        history = infer_area_from_history(company_id, scope text)   # per-scope query
        entry   = classify_work_type(scope_name, scope description) # per-scope match
        assume history → table → architect invents (rule 8) as today
        record EstimateAssumption(key="area_size", scope=<this work item>)
```

Two decisions taken with Simon (2026-08-10):

1. **Assume over asking.** The up-front "what's the area?" gathering question is
   dropped for area. Decomposition happens first; every work item missing a
   size gets an assumption the user can adjust afterward. Fewer questions,
   consistent with the existing "assume instead of ask" direction.
2. **The adjustment flow is redone properly, not patched.** "Change the lawn to
   800 sq ft" must find the *right* work item's assumption, not the first one.

What already exists in our favor:

- `EstimateAssumption.scope` — `"estimate"` today, documented as the
  *"Forward hook for per-job-item assumptions"*. The model anticipated this;
  no migration needed.
- `parse_job_size` — extracts stated sizes from free text.
- `infer_area_from_history` — per-company history median; currently queried
  with the whole mixed message, so per-scope queries make it *more* accurate.
- The architect prompt already instructs scopes to carry user-stated sizes into
  their descriptions ("400 sq ft patio" survives decomposition).
- `match_positional_reference` / `resolve_listed_reference` in
  `agents/text_utils.py` — the established machinery for "the second one" /
  name-based work-item targeting.

## Phases

TDD throughout. Ordered so the wrong-size bug dies first.

### Phase 1 — Per-scope resolution in the pipeline

The core fix. In `_run_pipeline`, after `_decompose_requirement` returns
scopes, resolve sizes per scope as above. Enrich each scope's research input
with **its own** `Area size (assumed)` line; stop injecting one global assumed
area into the shared requirement.

- New `resolve_scope_assumptions(scope, company_id)` in
  `assumption_defaults.py`, built from the existing pieces
  (`parse_job_size` → `infer_area_from_history` → `classify_work_type`).
  The per-scope history query uses the scope text, not the whole message.
- Each produced assumption carries `scope=<work item identifier>` and the
  existing `source` field (`history` / `table`).
- A scope with a stated size produces **no** assumption (nothing was assumed).
- Discrete-item scopes ("replace two cherry laurels") produce no area
  assumption — reuse the existing `is_discrete_item_job` classification
  per scope instead of per message.
- Material assumption gets the same treatment for free: `material_default`
  rides on the same `classify_work_type` entry, so a patio scope suggests
  pavers and a sod scope suggests sod — instead of the first match's material
  stamping the whole request.

Tests: mixed request yields one correctly-sized assumption per unsized scope;
a scope with a stated size is left alone; discrete-item scope gets none;
single-scope behavior unchanged; assumptions carry the right `scope` and land
on the saved estimate.

### Phase 2 — Stop asking for the area up front

- `area_measurements` drops out of the required gathering details. Work type
  (and material preference behavior) stay as they are.
- Stated sizes still flow through: extraction keeps capturing them when the
  user volunteers ("400 sq ft patio"), and the architect keeps carrying them
  into scope descriptions. Only the *question* disappears.
- The gathering-time `resolve_assumptions` area branch is retired; Phase 1 owns
  area assumptions now. (Its guards — `is_discrete_item_job`, the
  not-applicable sentinel — move down with it, not get deleted.)

Tests: "build a patio and mow the lawn" goes straight to generation with no
area question; a user-stated size still round-trips; the response's assumption
list shows the per-item assumed sizes.

### Phase 3 — Adjustment flow targets one work item

The part explicitly not to rush.

- "Change the lawn to 800 sq ft" resolves which work item via the existing
  reference machinery: match by work-item description keywords first
  ("the lawn", "the patio"), positional reference second ("the second one"),
  and — when exactly one work item has an area assumption — that one by
  default.
- Ambiguous ("change it to 800 sq ft" with two assumed areas): ask which,
  listing the work items via `format_and_record_list_response` so the reply
  "the first one" resolves.
- Rescaling becomes per-work-item: `_rescaled_job_items` applies the factor to
  the targeted work item only, and only that assumption's `assumed_value`
  updates. Today it rescales *every* job item — correct when the single
  assumption described the whole estimate, wrong the moment assumptions are
  per-item.
- Legacy estimates (one assumption, `scope="estimate"`): current whole-estimate
  rescale behavior is preserved for them.

Tests: named targeting, positional targeting, single-assumption default,
ambiguity clarify + follow-up resolution, per-item rescale leaves sibling work
items untouched, legacy scope="estimate" path unchanged.

### Phase 4 — Docs + phrasing reference

- Update `maple-phrasing-reference.md` (§ estimates) for the retired area
  question and the new per-item adjustment phrasings, per the CLAUDE.md rule.
- CLAUDE.md estimate-workflow blurb if it mentions the area question.

## Risks

| Risk | Mitigation |
|---|---|
| **Architect drops a user-stated size from a scope description**, so Phase 1 wrongly assumes over it. | The architect prompt already mandates carrying stated sizes; add a test with a stated-size multi-scope request pinning that no assumption is created for it. If it flakes in practice, thread the extracted `gathered` sizes through to matching scopes deterministically. |
| **One history vector-search per scope** adds latency. | Scopes already run per-scope vector retrieval for reuse; this rides the same per-scope fan-out (`_step2_and_3_for_scope` runs scopes concurrently). Measure, don't guess. |
| **Adjustment ambiguity annoys** ("change it to 800") when several items have assumptions. | Default rules above keep the question rare: named match → positional → only-one-candidate. Clarify only when genuinely ambiguous. |
| **Existing estimates** carry a single `scope="estimate"` assumption. | Adjustment handler branches on scope value; legacy behavior pinned by test. |
| **Dropping the area question surprises users** who expect to be asked. | The response surfaces every assumed size prominently as adjustable assumptions — same pattern already used for assume-instead-of-ask elsewhere. |

## Out of scope

- Effort anchoring itself — [estimate-effort-calibration.md](estimate-effort-calibration.md).
  This plan only makes the `work_quantity` inputs per-item correct.
- The curated size table's values (recalibrated 2026-08-10, separate change).
- Template baseline sizes and template scaling — untouched.
- Multi-area single scopes ("mulch the front *and back* beds") — one scope
  still gets one size.

## Decisions taken

1. **Decompose first, assume per work item** — sizes are resolved after the
   architect splits the request, never from the raw message.
2. **Assume over asking** — the up-front area question is dropped; users adjust
   afterward.
3. **Stated sizes always win** — an item whose size the user gave produces no
   assumption at all.
4. **Adjustments target one work item** and rescale only it; done properly with
   the existing reference-resolution machinery, ambiguity resolved by asking.
