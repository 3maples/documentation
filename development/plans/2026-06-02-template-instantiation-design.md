# Template-Driven Estimate Instantiation — Design Spec

**Date:** 2026-06-02
**Status:** Approved (design); implementing
**Related:** follows the gathering no-cancel fix (`2026-06-02` negative-reply work); the materials-question-on-template bug that motivated this.

## Goal

When a user's create-estimate request names a template, **skip AI generation entirely** and instantiate the estimate from the template:

- **No baseline** (template `size`/`unit` both null) → create a draft estimate with the template applied as a single Work Item, verbatim.
- **Has baseline** (`size` + `unit` set) → obtain the job size and **scale the template linearly** (`factor = job_size ÷ baseline_size`) before creating the estimate.

This removes the materials/activities AI-generation step (and its "Any material preferences?" question) for template-based requests.

## Approved decisions

| Decision | Choice |
|---|---|
| Scaling | **Linear** — multiply line-item quantities/effort and the work-item `sub_total` by `factor`; recompute grand total. |
| Size already in request | **Use it, don't ask.** Only prompt when no size is present. |
| Unit mismatch | **Convert within a family** (sq ft↔sq yd, lin ft↔lin yd); **incompatible family (area vs length) → ask** for the size in the baseline's unit. |
| Decline size ("No"/"skip") | **Baseline 1×** (no scaling) and proceed — consistent with the gathering no-cancel fix. |
| Generation when template named | **Skipped entirely** — even a richly-described request instantiates from the template, never AI-generates. |

## Data model (existing)

- `Template`: `size: Optional[float]`, `unit: Optional[TemplateSizeUnit]` (`"square feet" | "square yard" | "linear feet" | "linear yard"`); baseline = both set, validated by `Template._validate_baseline`. Plus `materials`, `activities`, `unmatched_*`, cost params (`profit_margin`/`overhead_allocation`/`labor_burden`/`tax`), `sub_total`, `recurring`/`recurrence`, `division`.
- `JobItem.sub_total` is **stored** (not derived); `effective_sub_total()` applies the recurrence multiplier. So scaling multiplies line quantities **and** the stored `sub_total` by `factor` (internally consistent since `sub_total ≈ Σ qty×price`).
- Existing template-apply code reused: `_create_estimate_from_template`, `_build_job_item_from_template`, `_resolve_template_by_name` (in `agents/estimate/crud_handlers.py`).

## Flow

```
create_estimate request
  └─ detect template name?  ── no ──▶ existing AI generation / gathering (UNCHANGED)
        │ yes
        ▼
   resolve template (substring, first match)
     ├─ not found ──▶ "I couldn't find a template called 'X'." + offer (generate / list templates)
     └─ found
          ├─ NO baseline ──▶ create estimate, template as ONE work item verbatim, link property, done
          └─ HAS baseline
                ├─ size in request?
                │     ├─ unit compatible ──▶ convert → scale → create
                │     └─ unit incompatible ──▶ ask size in baseline unit (pending)
                └─ no size ──▶ ask "What size is the job? (in <baseline unit>)" (pending)
                       └─ on reply: parse (default to baseline unit) → convert/scale → create
                            • incompatible unit ──▶ re-ask in baseline unit
                            • decline ("No"/"skip") ──▶ factor = 1× → create
                            • explicit cancel ──▶ cancel
```

## Scaling

`factor = job_size_in_baseline_unit ÷ template.size`. Applied to the work item built from the template:
- `MaterialItem.quantity`, `LabourItem.quantity`, `EquipmentItem.quantity` ×= factor
- `ActivityItem.effort` ×= factor (rate unchanged)
- `UnmatchedMaterialItem.quantity`, `UnmatchedLabourItem.quantity`, `UnmatchedActivityItem.effort` ×= factor
- `JobItem.sub_total` ×= factor; `Estimate.grand_total = Σ effective_sub_total()`
- Prices/rates unchanged. **Caveat:** all lines scale linearly — no fixed-fee exemption (no per-item flag exists in the model).

`factor = 1.0` for no-baseline and decline cases → identity scaling, so a single code path handles both.

## Unit conversion

Families: area `{square feet, square yard}` (1 yd² = 9 ft²); length `{linear feet, linear yard}` (1 yd = 3 ft). `convert_size(value, from_unit, to_unit)` returns the converted value, or `None` when the families differ.

## Size parsing (rule tier)

`parse_job_size(text) -> Optional[(value, unit|None)]` handles:
- `"600 square feet"`, `"600 sq ft"`, `"600 sqft"`, `"600 sf"` → (600, "square feet")
- `"200 square yards"`, `"linear feet"/"lin ft"/"lf"` variants
- `"20x20"` / `"20 x 20 ft"` → 400 (area, default sq ft unless yd stated)
- bare number `"600"` → (600, None) → caller defaults to the baseline unit
Returns `None` when no size is found.

## New / changed code

| File | Change |
|---|---|
| `agents/estimate/template_scaling.py` *(new)* | `convert_size`, `parse_job_size`, `scale_job_item(job_item, factor)` — pure, unit-tested. |
| `agents/estimate/crud_handlers.py` | `_create_estimate_from_template` gains property linkage; reuse `_build_job_item_from_template` + `scale_job_item`. |
| `routers/agent_helpers/delegate_create_estimate.py` | Detect a template name before `assess_sufficiency`; branch to template instantiation (no-baseline → create now; baseline+size → scale+create; baseline+no-size/incompatible → set `pending_template_size` and ask). |
| `routers/agent_helpers/pending_template_size.py` *(new)* | `handle_pending_template_size` pre-handler — absorbs the size reply, converts/scales/creates; reuses `is_cancellation_text` and decline→1×. Mirrors `handle_pending_estimate_gathering`. |
| `routers/agents.py` | Wire the new pre-handler into the orchestrate flow (alongside pending-calculation / gathering). |
| `agents/estimate/conversation_guide.py` or a small detector | `detect_template_in_create_request(text) -> Optional[str]` — catches "use (the) template X", "using/with (the) X template", "from template X" in a create message. |

## Testing (TDD)

| File | Coverage |
|---|---|
| `tests/test_template_scaling.py` *(new)* | `convert_size` (same/cross family, both directions), `parse_job_size` (units, AxB, bare number, none), `scale_job_item` (quantities/effort/sub_total/factor=1 identity). |
| `tests/test_template_create_routing.py` *(new)* or extend gathering tests | `detect_template_in_create_request`; `delegate_create_estimate` diverts a template request (no-baseline → creates; baseline+size → scales; baseline+no-size → pending+asks). |
| `tests/test_pending_template_size.py` *(new)* | size reply → scale+create; incompatible unit → re-ask; decline → 1×; explicit cancel → cancel. |
| `tests/test_maple_template_crud.py` (existing) | regression — existing apply/create-from-template phrasings still work. |

DB-touching handler tests stub `Template.find` / save like the existing template + gathering tests. mypy after each `.py` change.

## Out of scope
- Per-item fixed-vs-scalable distinction (linear scaling only).
- Ambiguous template name disambiguation (first substring match; note it).
- Non-linear/area-vs-volume scaling models.
- Changing the AI-generation path for non-template requests (untouched).

## Risks / watch-items
- **Routing precedence:** template detection must run before `assess_sufficiency` in the create path, and the new pending-size pre-handler must run before orchestrator classification (like pending-calculation) so a bare size reply isn't misrouted.
- **Don't hijack non-create template phrasings:** "apply template X to EST-…" must still go through the existing `update_estimate` apply path, not the create path.
- **Size parser false positives:** must not treat a property address number or unrelated number as a job size; require a unit token or an explicit AxB / "size"/"sq" cue, except in the pending-size turn where a bare number is expected.
