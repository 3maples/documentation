# Follow-ups: verbless-gap fix (Phase 1 + 2)

**Origin:** [fix-maple-verbless-gap.md](fix-maple-verbless-gap.md)
**Shipped:** 2026-04-23 — Phase 1 (new `get` action hints) + Phase 2a (address regex + labour role implicit-get) + Phase 2b (heuristic person-name + material-shape residual)
**Result:** Tier 1 72 → 90/111, Tier 2 77 → 92/111, verbless category 0 → 12/12 on both tiers

## Issues logged from the /code-review pass

### HIGH

#### [H1] `_classify_with_rules` is 215 lines
**Where:** `platform/agents/orchestrator/service.py:156`
**Issue:** Function was ~180 lines before Phase 2. The new domain-supplementation and implicit-get branches (lines 294–335) are logically distinct and should live in named helpers.
**Fix:** Extract:
- `_supplement_domain_from_entity_signals(normalized, original, action) -> Optional[str]`
- `_infer_implicit_get(normalized, original, domain) -> Optional[str]` (merges with existing `_is_bare_entity_reference`)

Gets `_classify_with_rules` back below 180 lines.

#### [H2] `service.py` is 1185 lines
**Where:** `platform/agents/orchestrator/service.py` (entire file)
**Issue:** Pre-existing; Phase 2 added ~165 lines. File now mixes rule classification, LLM classification, history resolution, rule/LLM merging, and entity-signal heuristics.
**Fix (separate refactor PR):** Split `agents/orchestrator/` into
- `classifier.py` — rules + entity-signal helpers
- `llm.py` — LLM integration
- `merger.py` — `_prefer_explicit_rule_match`, `_apply_low_confidence_fallback`

Out of scope for the verbless fix. Track independently.

### MEDIUM

#### [M1] `_LABOUR_ROLE_TOKENS` drifts from `DOMAIN_HINTS["labour"]`
**Where:** `platform/agents/orchestrator/service.py:77`
**Issue:** The frozenset is maintained manually with a "kept in sync with intents.py" comment. If a new role is added to `DOMAIN_HINTS["labour"]`, this set won't auto-update and verbless-labour bare tokens silently stop working.
**Fix:** Either (a) derive the set at import time by filtering generic keywords out of `DOMAIN_HINTS["labour"]`, or (b) split the hints into `_GENERIC_LABOUR_HINTS` + `_LABOUR_ROLE_HINTS` in `intents.py` and let both consumers share the role set.

#### [M2] `_ADDRESS_PATTERN` can false-match "N <word>+ way/court"
**Where:** `platform/agents/orchestrator/service.py:65`
**Issue:** Pattern uses `.search()` (not `.fullmatch()`) with permissive suffixes including `way`, `court`, `ct`. Phrasings like `"3 days back way"` or `"60 minutes one way"` trigger domain=property → get_property. Low frequency in practice but demonstrably hijackable.
**Fix options:**
- (a) Drop the most-ambiguous suffixes (`way`, `court`, `ct`). Smaller coverage but fewer false positives.
- (b) Require the match to be the entire residual after stripping the action prefix (via `_bare_entity_residual`).
- (c) Require a minimum street-name word-count AND the street-name to not be a common English noun — brittle.

Recommendation: (a) as a quick win; (b) as a follow-up once Phase 2a-proper (catalog lookup) lands.

#### [M3] Duplicate stopword lists
**Where:** `platform/agents/orchestrator/service.py:88` and `:130`
**Issue:** `_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` share ~14 entries (`hi`, `hey`, `the`, `that`, `my`, `your`, `our`, `no`, `yes`, `ok`, `okay`, `thank`, `thanks`, `please`, `sorry`).
**Fix:** Extract a shared `_COMMON_FILLER_STOPWORDS` frozenset; union with domain-specific additions.

#### [M4] New helpers have no direct unit tests
**Where:** `platform/agents/orchestrator/service.py:372,395,404`
**Issue:** `_is_bare_entity_reference`, `_looks_like_person_name`, `_bare_entity_residual` are covered end-to-end by the coverage matrix but not directly tested. Edge cases (empty string, unicode like "Renée Dupont", punctuation-heavy input, adversarial input) are not exercised. CLAUDE.md TDD policy expects direct tests on new functional code.
**Fix:** Add `tests/test_orchestrator_bare_entity_helpers.py` with ~10 parametrized cases per helper.

### LOW

#### [L1] Inline comments instead of docstrings on new helpers
**Where:** `platform/agents/orchestrator/service.py:395,404`
**Issue:** Project convention leans toward docstrings on methods. My new helpers use inline `# ` comments.
**Fix:** Convert the inline prose to proper docstrings. Style only.

#### [L2] `_CONFIRMED_WORKING_CASE_IDS` has no entry-validation
**Where:** `platform/tests/_maple_coverage_data.py` (the `frozenset` literal)
**Issue:** The set grows monotonically and is manually curated. A mistyped case ID silently does nothing (the override never applies), and the phrasing it refers to stays as an XFAIL marker.
**Fix:** At module load, validate each entry corresponds to a real `case_id` in the matrix; raise `ValueError` on mismatch. ~5 lines.

## Phase 2a-proper (deferred)

The plan's original Phase 2a — **catalog-backed DB lookup with `company_id` threaded through the classifier** — is still the right long-term answer. Doing so would:

- Retire `_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` (the heuristic gates become unnecessary when we can ask the DB "is this a real name in this company's catalog?")
- Remove the false-positive risk on `_ADDRESS_PATTERN` for ambiguous suffixes
- Drop the 4-word-length cap on bare-entity detection (catalog confirmation > shape heuristic)

**Scope reminder:** requires `company_id` in `OrchestratorAgent.process()`, async-conversion of `_classify_with_rules` (or a pre-pass in `process()`), per-company in-memory name cache with CRUD invalidation, and a `seeded_catalog` test fixture.

## Other deferred gaps surfaced by Tier 2

Not related to verbless, but flagged while the coverage matrix was in focus:

- **`set X's Y to Z` pattern** — 4/4 resources fail on Tier 1; Tier 2 closes 2. Likely closed by adding `"set"` to `ACTION_HINTS["update"]` in `intents.py`. ~15-minute change with regression shake-out.
- **Implicit-relationship questions** (`who owns X`, `where does Y live`, `which properties use Z`) — 9/12 fail on both tiers. Would need cross-resource reasoning (probably an LLM prompt enhancement rather than rule patterns).
- **`what's <name>'s <field>?`** — Tier 1 doesn't handle the `'s` contraction; `ACTION_HINTS["get"]` has `"what is"` but not `"what's"`. Closing this means expanding the hint list or normalizing contractions before matching.

These are separate plans, not verbless-gap follow-ups. Listed here for visibility.
