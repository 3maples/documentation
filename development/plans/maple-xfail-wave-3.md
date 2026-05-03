# Maple xfail backlog — Wave 3 (remaining gaps)

**Status:** Shipped (2026-05-02 — all three workstreams)
**Owner:** TBD
**Date:** 2026-05-02
**Depends on:**
- [maple-xfail-wave-1.md](maple-xfail-wave-1.md) (shipped 2026-05-02)
- [maple-xfail-wave-2.md](maple-xfail-wave-2.md) (shipped 2026-05-02)

## Goal

Close the 8 remaining genuine ⚠️ gaps in `documentation/development/maple-phrasing-reference.md` after Wave 1 + Wave 2 shipped. Tier 1 coverage in `test_maple_crud_coverage.py` is already 117/117 — these gaps live outside that matrix in:
- §1 Estimates (filters and drilldowns)
- §4 Materials (count variants, price range, size rename)
- §7.4 Safety (partial-bulk refusal)

## Scope

8 gaps split into three workstreams. Each can ship independently — the partial-bulk fix is essentially independent of the others.

### Workstream A — Partial-bulk refusal (1 gap, ~15 min)

| Phrasing | Intended behavior | Currently |
|---|---|---|
| `delete the last 5 contacts` | 🛑 refusal (N>1 but not "all") | falls through to unknown / single-contact ambiguity |

**Plan:**
1. Extend `_BULK_DELETE_PATTERNS` in `platform/agents/text_utils.py:166` with two more patterns:
   - `\b(?:delete|remove|clear|drop)s?\b.{0,30}\b(?:last|first|next|previous)\s+\d+\b`
   - `\b(?:last|first|next|previous)\s+\d+\b.{0,30}\b(?:delete|remove|clear|drop)s?\b`
2. Add coverage rows to `tests/test_text_utils.py:test_is_bulk_delete_request_matches_bulk_phrasings` for `"delete the last 5 contacts"`, `"remove the first 10 properties"`, `"drop the next 3 materials"`.
3. Flip §7.4 line 456 ⚠️→🛑 in `documentation/development/maple-phrasing-reference.md`.

**Done criteria:** the new phrasings hit the existing `BULK_DELETE_REFUSAL_MESSAGE`, `is_bulk_delete_request` returns `True` for them, the doc reflects shipped status.

### Workstream B — Material query variants (3 gaps, ~half day)

| # | Phrasing | Intended behavior | Notes |
|---|---|---|---|
| 1 | `How much does {material} cost?` | `get_material` field focus | non-possessive cost query — currently no rule |
| 2 | `How many different materials I have?` | `list_materials` (count) | "different"/"types of" modifiers vs. plain "how many" |
| 3 | `How many types of materials I have?` | `list_materials` (count) | same family as #2 |
| 4 | `list materials under $10` | `list_materials` with price range | needs price-range filter on Material agent |
| 5 | `rename size {old} to {new} for {material}` | `update_material` (size_op=rename) | handler exists; classifier needs to route |

**Note:** that's actually 4 gaps in §4.9 (`How much does X cost?` is also listed in §4.3) plus 1 in §4.4. Total: 5 phrasings, 4 distinct gaps after dedup.

**Plan sketch:**
- **#1** (`How much does X cost?`) — add a new rule in orchestrator's `_classify_with_rules` (or extend `_match_possessive_or_field_targeted`): pattern `\bhow\s+much\s+does\s+(?P<name>.+?)\s+cost\??$`. Domain via `FIELD_TO_DOMAIN["price"] = material` already in place.
- **#2 / #3** (count modifiers) — extend `is_count_query` in `agents/text_utils.py` with patterns matching `how\s+many\s+(?:different|types?\s+of)\s+\w+`. Risk: must NOT flip "how many estimates with status approved?" — that's already a working count phrasing.
- **#4** (price range) — new pattern in orchestrator + new filter pathway in Material agent's `_handle_list_materials`. Range parser: `(under|over|less\s+than|more\s+than|below|above)\s+\$?(\d+(?:\.\d+)?)`. Pairs with the existing material-shape residual for the entity.
- **#5** (size rename) — orchestrator pattern: `\brename\s+size\s+(?P<old>\S+)\s+to\s+(?P<new>\S+)\s+(?:for|on|of)\s+(?P<name>.+?)\??$`. Routes to `update_material` with `size_op=rename`. Material agent's `_handle_update_material` already supports the op per §4.8 of the reference doc.

**Tests:**
- Add a new category to `_maple_coverage_data.py` — `material_query_variants` — with 5 phrasings.
- Per-rule unit tests in `test_text_utils.py` and `test_orchestrator_intents.py`.

**Done criteria:** all 5 phrasings classify on Tier 1; matrix gap report shows the new category at 5/5; reference doc §4.4/§4.9 entries flipped.

### Workstream C — Estimate filters & drilldowns (5 gaps, ~1 day)

| Phrasing | Intended behavior |
|---|---|
| `what is the total value of the open estimates` | aggregated value across status DRAFT/APPROVED/REVIEW/WON |
| `show me draft estimates from last week` | `list_estimates` with date + status filter |
| `approved quotes over $10k` | `list_estimates` with status + amount filter |
| `what materials does {EST} use?` | `list_materials` scoped to one estimate |
| `what roles are on {EST}?` | `list_labours` scoped to one estimate |

This is the largest workstream. The Estimate Agent (`platform/agents/estimate/service.py`) is the most complex — 5,098 lines, multiple interaction patterns. Touching its list / get handlers carries the highest regression risk in the codebase.

**Plan sketch:**

1. **Aggregated value** — extend `_handle_list_estimates` to detect "total value" + "open estimates" / "open status set" and emit a single sum across the matching set instead of a list. Reuse `_GRAND_TOTAL_QUERY_PATTERN`.
2. **Date range filter** — add a date parser to the orchestrator (or to `_handle_list_estimates`): `(this|last|past)\s+(?:week|month|quarter|year)`, mapping to a `created_at` range. Add `Estimate.find({"created_at": {"$gte": ..., "$lte": ...}})` filter.
3. **Amount range filter** — same shape as Workstream B #4 but for `grand_total` field on Estimate.
4. **Estimate→materials drilldown** — new orchestrator rule, new `filter_by={"type": "estimate", "name": <EST-code>}` payload, Material Agent learns to honor it (resolve estimate by code → return its `materials` embedded list).
5. **Estimate→labour drilldown** — symmetric to #4 for labours.

**Cross-cutting risk:** drilldowns #4/#5 mirror the Wave 2 cross-resource pattern — adding `estimate` as a new `cross_type` value. Should reuse the existing `filter_by` payload contract from Wave 2 to avoid a parallel mechanism.

**Tests:**
- New `_maple_coverage_data.py` category — `estimate_filters_and_drilldowns` — with 5 phrasings.
- Service tests in `test_estimate_agent.py` for the aggregated-value path and date/amount range filters.
- Cross-resource service tests in `test_cross_resource_joins.py` for the drilldowns.

**Done criteria:** all 5 phrasings classify and respond correctly; reference doc §1 entries flipped; coverage report shows the new category at 5/5.

## Out of scope

- **LLM-only entries (🤖 markers, ~15 phrasings)** in §1.2 / §1.3 / §1.4 / §1.5 / §1.7. Not strictly gaps — they work via Tier 2 (`use_llm=True`) with an OpenAI key. Promoting them to Tier 1 rules is not scheduled; an alternative is integrating Tier 2 into CI (~$0.05 per run) so the matrix records LLM-tier truth.
- **Code-review followups** — tracked separately in `documentation/development/code-review-followups.md` (136 entries), to be worked through one HIGH per session per the file's own guidance.
- **Mypy baseline cleanup** (271 errors across 38 files, followup #3) — separate workstream from feature gaps.

## PR strategy

Three independent PRs, in roughly increasing order of complexity:

1. **`fix: refuse partial-bulk delete phrasings`** — Workstream A. Tiny, low-risk, self-contained.
2. **`feat: route material query variants (cost/count/price-range/size-rename)`** — Workstream B. Touches orchestrator + Material Agent + new test category.
3. **`feat: estimate filters and drilldowns`** — Workstream C. Largest; touches Estimate Agent + extends cross-resource `filter_by` to estimate-scoped queries.

PR ordering matters because Workstream C reuses the `filter_by` plumbing from Wave 2, and Workstream B's count-variant extensions might subtly affect estimate `count` phrasings — running C after B reduces churn.

## Risks

- **Workstream B count-variant** must not capture estimate count phrasings (`how many approved estimates`) that already work. Mitigation: anchor `different`/`types of` patterns specifically; add an explicit anti-regression test.
- **Workstream B size rename** — orchestrator rule must not steal the existing `size_op=add`/`size_op=remove` patterns in `_match_size_scoped_material_op`. Mitigation: pattern order matters; add `rename` as a new branch above the others.
- **Workstream C aggregated value** — risks double-counting if the user has stale estimates in soft-deleted state. Mitigation: scope filter to active estimates per the existing `_handle_list_estimates` filter chain.
- **Workstream C drilldowns** — `filter_by={"type": "estimate"}` is new; must not collide with the existing estimate-anchored `active_estimate_id` context flow. Mitigation: filter_by takes precedence over active_estimate when explicitly named in the message.

## Done criteria (overall)

- All 8 unique gaps in §1 / §4 / §7.4 of `maple-phrasing-reference.md` flipped to ✅ rule (or 🛑 refusal for §7.4).
- Coverage matrix in `_maple_coverage_data.py` extended with two new categories (`material_query_variants`, `estimate_filters_and_drilldowns`); both at 100%.
- Tier 1 still 117/117 for the original matrix; new categories add to the count.
- "Last updated" header bumped with a Wave 3 note.
- This plan flipped to "Shipped".

## Future hooks (Wave 4 candidates — not in this plan)

- **Tier 2 LLM-tier matrix integration** — replace ~15 🤖 LLM-only entries with hard-asserted tests by running Tier 2 in CI nightly. Cost-budget question.
- **Multi-intent / conjunction phrasings** — `create a contact AND link it to {property}`, `delete the Foreman role AND add Operator instead` (§11.1 of the reference doc).
- **Cross-resource filter pivot** — `which contacts at {property} have role=owner?` (composing the property→contact join with a contact-side filter).
- **Range filters on labour cost** — `labour roles costing more than $40/hr` (§11.2).
