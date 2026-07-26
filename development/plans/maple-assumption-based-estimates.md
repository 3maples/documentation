# Maple: Assumption-Based Estimate Completion (+ generation perf check)

> On approval, copy this plan to `documentation/development/plans/maple-assumption-based-estimates.md` (plans live in-repo).

## Context

Today Maple blocks estimate generation when info is missing: `assess_sufficiency` requires `work_type`, `area_measurements`, and `material_preferences`, and enters a multi-turn gathering Q&A ([delegate_create_estimate.py:175-221](platform/routers/agent_helpers/delegate_create_estimate.py)). Better UX: **assume** missing info, generate immediately, tell the user what was assumed, and let them adjust via follow-up ("change the lawn to 800 sq ft") — Maple resolves the estimate from `active_estimate_code`, rescales deterministically, recomputes totals, and confirms.

**Decisions (confirmed with Simon):**
1. Ask only when **work type** is unknowable; assume everything else.
2. Assumed values priority: **company history → curated defaults table → LLM fallback** (Simon: "there are past estimates/work items the agent can reference when making assumptions").
3. Adjustments **rescale deterministically** (factor = new/old via existing `scale_job_item`); material changes swap the catalog match + re-price — no regeneration.
4. At the end, **check generation performance** — Simon reports estimate generation feels slower than before.

## Current-state facts (verified)

**Creation path**: gathering gate `delegate_create_estimate.py:175-221`; enriched description at `:225`; save via `save_generated_estimate` (`routers/estimate_helpers/ai_generation.py:395`); response built at `:302-369` (optional_follow_up appended last). Detail catalog + guards: `agents/estimate/conversation_guide.py` (`CONVERSATION_DETAILS`, `get_next_missing_detail` — work_type is priority 1, `AREA_NOT_APPLICABLE_VALUE`, `build_enriched_description`); `assess_sufficiency` guards at `agents/estimate/service.py:215-300`. Multi-turn handler: `routers/agent_helpers/estimate_gathering.py` (`_finalize_gathering:282`; note `_maybe_skip_area_question:130` runs a *second* `assess_sufficiency`).

**Past-job signal**: one `WorkItemSummary` doc per job item of every Sent/Approved estimate (`models/work_item_summary.py`, written by `embed_approved_estimate`, `services/work_item_summary.py:172`). `summary` text embeds description + materials/qty/price + activities/effort; area sizes appear as prose ("Install 400 sq ft paver patio"). `search_similar_work_items` (`services/work_item_summary.py:115`) does per-company `$vectorSearch` (text-embedding-3-small). The pipeline already reuses a ≥0.85 match verbatim (`_reuse_past_work_item`, `llm_pipeline.py:456` — quantities/effort survive; prices re-resolved from current catalog) and feeds lower-scoring summaries to the researcher as guidance. **No structured size field exists** on JobItem/Estimate — only `Template.size/unit`. `parse_job_size` (`agents/estimate/template_scaling.py:96`) can extract sizes from summary prose.

**Update path**: intent `update_estimate` → `delegate_estimate_ops.py:53-141`; `_should_delegate_update_estimate_to_agent` (`routers/agents.py:221-241`) gates agent-path vs router-path (router path's `_modify_items_refusal` refuses "change/adjust quantity/material" phrasings). Agent dispatch `_handle_update_estimate` (`crud_handlers.py:2267-2382`), fallback capabilities refusal. Estimate resolution `_resolve_update_estimate_code` (`crud_handlers.py:2038-2069`, explicit title > `active_estimate_code`). Locked-status guard inside `_load_estimate_for_update` (Draft/Review only). Reuse: `scale_job_item`/`convert_size`; `_recalculate_sub_total` (`work_item_field_handlers.py:76-98`); `_recalculate_grand_total` (`work_item_handlers.py:421-437`); `object_link`; catalog matching + `_resolve_material_inventory_match`.

**Gotchas**: `parse_job_size(allow_bare_number=True)` only matches a whole-string number — "make it 800" needs the handler to extract a trailing number itself. `_handle_work_item_set_total` writes `sub_total` directly (manual override); blind recompute clobbers it. `Estimate` is Beanie — adding a defaulted list field needs no migration. Update handlers see no chat history (only `active_estimate_code` + query).

**Performance facts** (Explore-verified): no timing instrumentation exists anywhere. One-shot generation = 7 OpenAI round-trips (orchestrator classify, `assess_sufficiency`, architect terra-reasoning, 2× embedding, 2× researcher terra + web_search, plus `_generate_accuracy_suggestions` worker call serialized *after* the estimate is built, `service.py:985`). Likely slowdown cause: commits `0cc8cfd`/`ae95e08`/`2d5e199` (07-15/16) — before the API-mode fix, architect + researcher calls silently **errored and degraded** (fast but broken single-scope, empty research); now they really run (reasoning + per-scope web search). Additional fixable drag: sequential inventory fetches (`service.py:370-371`), duplicate `assess_sufficiency` in gathering, inline token-metering (3 serial Mongo RTTs per LLM call, `services/llm/callback.py:70`), `openai_max_retries=2` × 90s timeout = invisible 270s worst-case per degraded step, per-company concurrency cap of 3 (`config.py:42`).

---

## Phase 0 — Model + assumption sources (history → table → LLM)

**Tests first**: new `platform/tests/test_assumption_defaults.py` —
- `classify_work_type`: lawn/patio/unknown, case-insensitive, falls back to raw message.
- `infer_area_from_history` (mock `search_similar_work_items`): summaries containing "400 sq ft" / "600 sq ft" → median 500 sq ft with sample count; mixed-unit summaries converted via `convert_size`; linear-vs-area families never mixed; no parseable sizes → None; empty results → None.
- `resolve_assumptions`: history hit → area assumption `source="history"`, display "500 sq ft (based on your past jobs)"; no history → table value `source="table"`, "500 sq ft (average lawn)"; no area assumption when gathered or `AREA_NOT_APPLICABLE_VALUE`; materials default from table or generic skip-value; unknown work type + no history → no table area assumption (LLM fallback covers it).
- `format_assumptions_block` rendering + empty case; `EstimateAssumption` roundtrip; `Estimate(assumptions=[])` default.

**Implement**:
- `models/estimate.py`: `EstimateAssumption(BaseModel)`: `key` ("area_size" | "materials" | free-form LLM keys), `label`, `assumed_value: Optional[float]` (baseline for rescaling — overwritten on each adjustment so 500→800→1000 compounds), `unit: Optional[str]` (canonical `template_scaling` units), `display_text`, `scope: str = "estimate"` (per-job-item forward hook), `source: str = "table"` ("history"|"table"|"llm"|"user"). Add `Estimate.assumptions: List[EstimateAssumption] = []`.
- New `agents/estimate/assumption_defaults.py`:
  - `WORK_TYPE_DEFAULTS` (ordered keyword entries; starter set — **Simon to sanity-check values**): lawn/sod/turf/grass → 500 sq ft / "standard sod"; patio/paver → 200 sq ft / "standard concrete pavers"; mulch/beds/planting → 300 sq ft; driveway → 600 sq ft; deck → 150 sq ft; hedge/fence line → 100 linear ft; retaining wall → 40 linear ft; irrigation → 500 sq ft. Use `SQUARE_FEET`/`LINEAR_FEET` constants from `template_scaling.py`.
  - `classify_work_type(work_type_text, message) -> Optional[entry]` — deterministic, first match wins.
  - `async infer_area_from_history(company_id, query_text) -> Optional[HistoryArea]` — call `search_similar_work_items` (one embedding round-trip, already company-scoped), run `parse_job_size` over each result's `summary`, convert to a common unit per family, take the **median** of the dominant family (≥2 samples required; else None). Rounds to a friendly value (nearest 50).
  - `async resolve_assumptions(gathered, missing, message, company_id) -> (updates, assumptions)` — area: history → table; materials: table default → generic skip-value. `updates` feeds `gathered`.
  - `format_assumptions_block(assumptions)` — friendly first-person: "I made a few assumptions — let me know if you'd like to adjust any:\n• Area: 500 sq ft (based on your past jobs)\n• Materials: standard sod".
- `conversation_guide.py`: `build_enriched_description(gathered, assumed_keys=None)` renders assumed values as `Area size (assumed): 500 sq ft`. Keep `get_assumption_value` untouched (still backs skip replies in the surviving work_type question).

**History/reuse coherence note**: `infer_area_from_history` uses the same `search_similar_work_items` results the pipeline uses, so when the ≥0.85 verbatim-reuse path fires, the assumed area tends to come from the same past job whose quantities were copied — consistent by construction. Not guaranteed for multi-scope jobs; accepted v1.

## Phase 1 — Creation path: assume instead of ask

**Tests first**: `test_agent_helpers_delegate_create_estimate.py` — "create an estimate for lawn care" (work type known) generates immediately: no gathering state, assumptions persisted, response has assumptions block + "adjust"; "I need an estimate" (no work type) still asks the work_type question; per-item job ("replace one dead tree") → no area assumption; fully-specified message → no assumptions, unchanged response (regression). `test_estimate_gathering.py` — answering the work_type question finalizes immediately with assumptions (update/retire multi-question walk tests, incl. `test_no_to_material_preferences_finalizes_with_assumption`). `save_generated_estimate` persists `assumptions`.

**Implement**:
- `delegate_create_estimate.py:182`: enter gathering **only if `"work_type" in missing`**. Otherwise `resolve_assumptions(...)` (async, company-scoped); `gathered.update(updates)`; enriched description with `assumed_keys`; after save, append `format_assumptions_block(...)` to the response *before* the optional_follow_up append.
- `estimate_gathering.py`: once `gathered["work_type"]` is present after a reply, run the deterministic `is_discrete_item_job` check (sets `AREA_NOT_APPLICABLE_VALUE`), `resolve_assumptions` for the rest, and `_finalize_gathering(..., assumptions=...)` immediately. Delete now-unreachable `_maybe_skip_area_question` + tests (also removes its duplicate `assess_sufficiency` LLM call). `_finalize_gathering` gains `assumptions` param, persists + renders block.
- `ai_generation.py` `save_generated_estimate`: optional `assumptions` kwarg → set on `Estimate(...)`. Other callers unaffected.

**Gathering flow disposition**: kept as the work_type-only fallback question, not dead code.

## Phase 2 — LLM fallback assumptions (architect structured output)

**Tests first**: architect prompt contains assumptions schema + "treat '(assumed)' values as given, don't re-report" rule; monkeypatched `_step1_architect` returning an assumption → `agent_result["assumptions"]` surfaces; merge precedence — history/table assumption suppresses same-key LLM assumption.

**Implement**:
- `agents/estimate/schemas.py`: `ArchitectAssumption` model; `DecomposedRequirement.assumptions: List[ArchitectAssumption] = []`.
- `prompts/estimate_architect.py`: "(assumed)" values are given; anything invented (size/quantity/material neither stated nor assumed) goes into the `assumptions` output array (numeric value + unit when scalable). Extend output schema block.
- `llm_pipeline.py` `_run_pipeline`: thread `decomposed.assumptions` into `research_context`; `service.py` success dict gains top-level `"assumptions"`.
- `delegate_create_estimate.py` / `_finalize_gathering`: convert `agent_result["assumptions"]` → `EstimateAssumption(source="llm")`, append those not key-covered; persist + render all.
- ReAct path (`estimate_react_mode_enabled`, default False = dead in prod): skip LLM-assumption reporting in v1, note in code.

## Phase 3 — Follow-up adjustment: detector + deterministic size rescale

**Tests first**: new `platform/tests/test_estimate_assumption_adjustment.py` (mocked `find_one`/`save`, `test_maple_work_item_ops.py` style):
- Detector positives: "change the lawn to be 800 sq ft instead", "make it 800 square feet", "the area is actually 20x30", "adjust the assumed area to 1000 sq ft", "assume premium pavers instead".
- Detector negatives: "change the quantity of mulch in work item 2", "remove the patio work item", "set the status to Sent", "change the description to X", "add sod to the estimate".
- Happy path: area assumption 500 sq ft + 2 job items (one recurring) → "800 sq ft": quantities/effort ×1.6, sub_totals recomputed, grand_total recurrence-aware, assumption now 800/"(adjusted)"/`source="user"`, response says "from 500 sq ft to 800 sq ft" + new total.
- Edges: bare "make it 800" (unit from assumption); sq-yd input via `convert_size`; linear-vs-area mismatch → clarify; value ≤ 0 or factor outside [0.01, 100] → clarify, no mutation; manual `set_total` override preserved proportionally; legacy estimate without assumptions → graceful "no stored assumptions" + suggest the estimate editor; locked status → existing refusal; per-item estimate + size request → graceful message; no active estimate → existing "which estimate?" prompt.
- Routing: `_should_delegate_update_estimate_to_agent` True for these phrasings; never reach `_modify_items_refusal` (`test_agent_helpers_delegate_estimate_ops.py`). Add orchestrator intent cases if misrouted (verify during implementation).

**Implement**:
- New `agents/estimate/assumption_handlers.py` — `AssumptionAdjustmentMixin` (mirror `WorkItemFieldHandlersMixin`; TYPE_CHECKING stubs for MRO helpers):
  - `_detect_assumption_adjustment(text)` → `{"kind": "size"}` | `{"kind": "material", "new_material": ...}` | None. Guards: None on work-item/status nouns. Size: change/make/set/adjust/update/assume/"is actually"/"should be" + `parse_job_size` hit or trailing-number extraction. Material: assume/use/swap/switch + "instead" or "material assumption", capturing new material text.
  - `_handle_assumption_adjustment`: (1) `_resolve_update_estimate_code`; (2) `_load_estimate_for_update` (locked-status guard free); (3) find `key=="area_size"` assumption (fallback: first numeric+unit); (4) parse value, unit-default from assumption, `convert_size` on mismatch, clarify cross-family; (5) factor + guards; (6) per job item: if stored `sub_total` ≈ recompute-from-lines (±$0.01) and item has priced lines → `scale_job_item` then `_recalculate_sub_total`; else keep proportionally scaled `sub_total` (preserves `set_total` overrides / empty-line items); (7) `_recalculate_grand_total`, update assumption record, save; (8) respond "I've updated the area from 500 sq ft to 800 sq ft and recalculated estimate {link} — new grand total: $X."
- `crud_handlers.py` `_handle_update_estimate`: dispatch after `_detect_work_item_op`, before status transition. Add "adjust the assumptions I made (area size, materials)" to the fallback capabilities list.
- Compose mixin into `EstimateAgent` (`service.py:156-163`). Public seam `owns_assumption_adjustment(text)` next to `owns_update_sub_op`; OR into `_should_delegate_update_estimate_to_agent`.

## Phase 4 — Material-type assumption swap

**Tests first** (same file): "assume premium pavers instead" with stored materials assumption → matching lines swapped to catalog match (id/name/unit/price/cost), quantity preserved, totals recomputed, assumption updated, response confirms + new total; no catalog match → clarify, no mutation; no materials assumption → graceful message.

**Implement** in `assumption_handlers.py`: find `key=="materials"` assumption; candidate lines via token overlap vs old assumed material text (reuse `_score_catalog_match`/`_fuzzy_token_overlap`); resolve new material via `_resolve_material_inventory_match` (follow `_handle_work_item_add_material` for inventory loading); swap + re-price; recompute per Phase-3 override rule; update assumption; save; respond.

## Phase 5 — Gates, docs, cleanup

- Update `test_estimate_area_applicability.py` / `test_estimate_area_grounding.py` expectations (guards now decide assume-vs-honor, not ask-vs-proceed). Add new phrasings to `test_maple_crud_coverage.py`.
- `./run_mypy.sh` + `./run_ruff.sh` scoped to `agents/estimate`, `routers/agent_helpers`, `routers/estimate_helpers`, `models`, `services`; `./run_tests.sh` on touched test files (local Mongo up first).
- Update `documentation/development/maple-phrasing-reference.md` (separate repo): response shape, adjustment phrasings, capability list, status tags, §9.3 counts, "Last updated".

## Phase 6 — Generation performance: instrument, quick wins, measure & report

Simon reports generation is slower than before. Likely systematic cause (from git archaeology): the 07-15/16 gpt-5.6 upgrade — before `ae95e08`, architect/researcher calls silently errored and degraded (fast but broken); now they genuinely run reasoning + per-scope web search. That part is "doing the work it was supposed to"; the deliverable here is visibility + cheap wins + a measured report.

**Tests first**: timing-span helper unit test (records step name + duration, logs one structured line per generation); accuracy-suggestions-backgrounded test (response returns without awaiting it; suggestions still persisted/attached when done — or dropped from the sync path, see below).

**Implement**:
1. **Instrumentation**: small `services/timing.py` context-manager (`perf_counter` spans) → one INFO log line per generation: `estimate_generation timings step=architect 12.3s | vector=0.4s | research=28.1s | build=0.2s | suggestions=6.5s | total=48s`, plus per-step degraded/timeout flags (a silently-swallowed 270s retry storm is currently invisible). Wire into `_run_pipeline` steps, `assess_sufficiency`, and `prepare_generated_estimate`.
2. **Quick wins** (each small, test-covered):
   - Move `_generate_accuracy_suggestions` (`service.py:985`) off the critical path — run it concurrently with `_fill_prices_and_calculate_totals` via `asyncio.gather`, or fall back to its existing rule-based generator on the sync path. Saves a full worker LLM round-trip of wall clock.
   - `asyncio.gather` the sequential inventory fetches (`service.py:370-371`) and `Company.get` + `_fetch_material_unit_names` (`service.py:803/862`).
   - The duplicate `assess_sufficiency` in gathering is already deleted in Phase 1; note the assumption-first flow itself removes 1-3 whole gathering round-trips per estimate — the biggest perceived-latency win of this feature.
3. **Measure & report**: with instrumentation in, run 3 representative generations locally (lawn 1-scope, patio+lighting 2-scope, template path) before/after the quick wins; write a short findings note in `documentation/development/notes.md` with the step breakdown, the gpt-5.6 explanation, and recommendations needing a product decision (e.g. researcher back to a faster tier or `search_context_size: "low"`, raising `openai_max_concurrency_per_company` from 3, retry/timeout tuning) — **recommend only, don't change model tiers without Simon's sign-off**.

## Verification (end-to-end)

1. `./run_tests.sh tests/test_assumption_defaults.py tests/test_agent_helpers_delegate_create_estimate.py tests/test_estimate_gathering.py tests/test_estimate_assumption_adjustment.py tests/test_agent_helpers_delegate_estimate_ops.py`
2. Manual (local uvicorn + portal, Maple chat): "create an estimate for mowing the lawn at 12 Oak St" → created with assumptions block (history-sourced if past lawn jobs exist, else table); "change the lawn to be 800 sq ft instead" → 1.6× rescale + new grand total; "assume premium sod instead" → material swap + re-price.
3. Regression: fully-specified request → no assumptions; "I need an estimate" → asks work type; locked estimate refuses adjustment.
4. Perf: timing log line present per generation; before/after numbers in the findings note.

## Risks / notes

- **Whole-estimate scaling (v1)**: area factor scales ALL job items — patio+lighting over-scales lighting. Accepted; `EstimateAssumption.scope` is the forward hook.
- **History inference is prose-parsing** (median of `parse_job_size` over similar summaries, ≥2 samples) — deliberately conservative; falls back to table.
- **Material-swap line mapping is heuristic**; ambiguous/zero matches clarify instead of mutating.
- **Legacy estimates** (no assumptions) get a graceful reply — not treated as a generic size change (no baseline).
- **Portal rendering** of `assumptions` (flows into API JSON automatically) is out of scope — follow-up task.
- Flagged in passing (separate follow-ups, not this change): researcher `responses.parse` tokens are never metered into `LLMUsageEvent`/company counters (billing gap, `services/llm/callback.py` bypassed); `_reuse_past_work_item` doesn't re-verify `estimate.company` (tenant boundary rests solely on the `$vectorSearch` filter); reuse path copies quantities with no size normalization (500 sq ft quantities reused for a 2000 sq ft job — the assumption feature makes this more visible and `scale_job_item` is the natural fix).
