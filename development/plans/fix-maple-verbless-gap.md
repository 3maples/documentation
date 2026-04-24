# Plan: Fix Maple's verbless-phrasing classification gap

**Status:** Draft — 2026-04-23
**Target:** `platform/agents/orchestrator/` (intents.py + service.py)
**Coverage goal:** `verbless` category in `tests/test_maple_crud_coverage.py` 0/12 → 12/12 on Tier 1, and close the residual gap on Tier 2.

---

## 1. Problem

The coverage matrix exercises 12 "verbless" phrasings — 3 patterns × 4 resources — and today **none** of them classify correctly on either tier:

| Pattern | Property | Contact | Material | Labour (People) |
|---|---|---|---|---|
| bare name | `123 Main St` | `John Doe` | `concrete blocks` | `Landscaper` |
| details-for | `I want the details for 123 Main St` | `I want the details for John Doe` | `I want the details for concrete blocks` | `I want the details for Landscaper` |
| tell-me-about | `tell me about 123 Main St` | `tell me about John Doe` | `tell me about concrete blocks` | `tell me about Landscaper` |

Expected intent for every row: `get_<resource>` routed to the matching domain agent. Actual result today: `intent=unknown`, `needs_clarification=True` — the user gets "I couldn't determine the intent…" instead of the entity detail they asked for.

## 2. Root cause

Traced through `agents/orchestrator/service.py` and `intents.py`. Four reinforcing gaps combine to produce the failure:

1. **No implicit "get" inference.** `ACTION_HINTS` (intents.py:98–143) has no entry for `tell me about`, `details for`, `details on`, `info on`, `about`. `_classify_with_rules()` (service.py:80–250) requires an action hint to form any intent — so even a correctly-detected domain yields `(unknown, 0.35, needs_clarification=True)` at service.py:226–233.
2. **No bare-entity name detection.** `DOMAIN_HINTS` (intents.py:145–171) is a keyword list. It catches `Landscaper` because "landscaper" is explicitly listed as a labour synonym, but it has no regex for addresses (`123 Main St`), no pattern for capitalized person names (`John Doe`), and no product-catalog lookup (`concrete blocks`). Even if an action were inferred, the domain wouldn't be.
3. **LLM prompt offers no guidance.** `_classify_with_llm()` (service.py:649–736) builds a system message with domain knowledge + entity context + chat history, but contains zero few-shot examples of bare-name or "tell me about X" phrasings. On standalone messages with no history, the LLM sees only the raw token and returns a weak off-topic / help classification.
4. **Low-confidence fallback buries weak signals.** `MIN_CONFIDENT_INTENT_PROBABILITY = 0.75` (service.py:37) plus `_apply_low_confidence_fallback()` (service.py:488–517) and `_prefer_explicit_rule_match()` (service.py:519–647) actively downgrade anything below threshold. When the LLM returns `get_labour` at 0.5 confidence for `Landscaper`, the rule finds no domain match, so the LLM intent is demoted to `off_topic` at service.py:563–581, then flattened to `unknown` by the low-confidence gate.

## 3. Phased fix

The fix needs to span the rule layer and the LLM layer. Neither alone closes all 12 cases: the rule layer is deterministic but can't handle novel names; the LLM handles novelty but still needs explicit prompt guidance and a higher-confidence exit path.

### Phase 1 — Rule-level: add verbless action phrases (fast, deterministic)

**Target:** the 8 `I want the details for X` / `tell me about X` cases (rows 2 and 3 of the matrix).

These phrasings **aren't truly verbless** — they have a stable phrase prefix. Closing them is a three-line change to `ACTION_HINTS`:

```python
# intents.py:131
"get": [
    "get", "show", "view", "find", "search",
    "pull up", "look up", "lookup",
    "what does", "what is",
    # NEW — verbless-ish "get" phrasings
    "tell me about", "about",
    "details for", "details on",
    "info on", "info for", "info about",
    "i want the details for", "i want details for",
],
```

Verification: `tell me about Landscaper` → action=`get`, domain=`labour` (already in `DOMAIN_HINTS`) → `get_labour`. Covers the 2 labour rows in patterns 2 and 3 immediately. For the non-labour resources, also need Phase 2.

### Phase 2 — Rule-level: bare-name domain resolution

**Target:** the 4 truly-bare-name cases + the 6 non-labour "tell me about" / "details for" cases that need a name-based domain signal.

The bare-name problem is fundamentally an **entity resolution** problem: given a string, which resource does it refer to? Three layers, in priority order:

**2a. Pattern-level resolvers** in `intents.py` — cheap, no DB hit:
- **Address regex** → `property`: `^\d+\s+\S+(\s+\S+){0,3}\s+(st|street|rd|road|ave|avenue|blvd|dr|drive|ln|lane|way|court|ct|pl|place)\.?$` (case-insensitive). Matches `123 Main St`, `42 Oak Ave`, etc.
- **Known role tokens** → `labour`: already works via DOMAIN_HINTS for `landscaper`, `operator`, `foreman`. Extend with a small seed list of common role titles (see `RoleCategory` in the Labour model for the authoritative list).

**2b. DB-backed entity lookup** — the robust fallback. Add `_resolve_name_to_domain(normalized, company_id)` in `service.py` that runs before the ACTION_HINTS / DOMAIN_HINTS match at service.py:173–174. Queries:

```python
# Pseudo — actual implementation uses Beanie's .find_one() with case-insensitive regex
if await Property.find_one({"company_id": cid, "address": ci(normalized)}):
    return "property"
if await Contact.find_one({"company_id": cid, "name": ci(normalized)}):
    return "contact"
if await Material.find_one({"company_id": cid, "name": ci(normalized)}):
    return "material"
if await Labour.find_one({"company_id": cid, "role_title": ci(normalized)}):
    return "labour"
return None
```

Concerns to address when implementing:
- **Latency.** Four sequential DB queries per message is too much. Options: (i) a single `$facet` aggregation, (ii) parallel queries with `asyncio.gather`, or (iii) a per-company in-memory LRU cache of known entity names keyed by company_id, invalidated on CRUD mutations. Recommend (iii) plus (ii) on cache miss.
- **Ambiguity.** If a material is named "Landscaper" and a role exists named "Landscaper", we need a deterministic tie-break. Precedence: exact-match on role title > property address > contact name > material name. Document this in the resolver.
- **When to run.** Only when `action` or `domain` is `None` after the existing hint match — don't second-guess strong keyword matches.

**2c. Implicit "get" inference when domain resolved from a name.** If the message is *just* an entity name (no other action words, length ≤ 4 tokens), assume the user wants `get_<resource>`. Set confidence high (≥0.8) so it survives the low-confidence gate. Implemented in `_classify_with_rules()` as a new branch between the current action/domain resolution (service.py:173–174) and the partial-match fallback (service.py:226).

### Phase 3 — LLM prompt enhancement

**Target:** residual Tier 2 cases that don't hit a known entity (typos, new names not yet in the DB cache, LLM-only paths).

Augment the system message in `_classify_with_llm()` (service.py:674–701) with a short examples block:

```
## Verbless phrasings
When the user sends only a name, address, or role — or a short phrase like
"tell me about X" / "details for X" / "what about X" — treat it as a GET
request for the matching resource:

- "123 Main St" → get_property
- "John Doe" → get_contact
- "concrete blocks" → get_material
- "Landscaper" → get_labour
- "tell me about John Doe" → get_contact
- "I want the details for concrete blocks" → get_material

Return intent with probability ≥ 0.8 when the message is just an entity
reference with no other action signal. Prefer the resource whose catalog
actually contains the referenced name.
```

Also: lower the effective LLM-confidence gate for verbless phrasings. Today, `_prefer_explicit_rule_match()` at service.py:563–581 overrides LLM CRUD intents to `off_topic` when the rule found no domain — but that's exactly the case where we *want* the LLM answer. Tighten the override to only fire when the LLM confidence is <0.6, so a 0.8-confident LLM `get_contact` on `John Doe` survives.

## 4. Test strategy

Tests already exist for all 12 cases — this work is about making them *pass*, not about writing new ones. Workflow:

1. **Baseline snapshot.** Commit the current Tier 1 + Tier 2 gap report (`platform/tests/reports/maple_crud_gap_report.md`) so the diff is visible after each phase.
2. **Phase 1 TDD.** Before touching `ACTION_HINTS`, run `./run_tests.sh tests/test_maple_crud_coverage.py::test_rule_only_classification -k "verbless"` and confirm failures. Apply the edit; re-run; confirm `tell me about Landscaper` and `I want the details for Landscaper` flip to pass. The other 10 remain XFAIL.
3. **Phase 2a TDD** (patterns). Address regex first — confirm `123 Main St` variants resolve to `property`. Then seed role tokens.
4. **Phase 2b integration.** The DB resolver needs the coverage tests extended with a `setup_entities` fixture that seeds one Property / Contact / Material / Labour matching the matrix tokens in the test company. Without seeded entities, Phase 2b can't be exercised by the existing matrix. This is the one place new test infrastructure is required.
5. **Phase 3.** Re-run Tier 2 (`./run_tests.sh tests/test_maple_crud_coverage.py -m ""`, ~3 min, ~$0.05). Diff the gap report against the baseline. Expectation: `verbless` goes to 12/12 on Tier 2; Tier 1 stays ≥10/12 (the two that can't be resolved without DB lookup — e.g. an empty-catalog company — stay as intentional XFAIL).
6. **Coverage-case reclassification.** For every phrasing that now passes reliably on Tier 1, add its `case_id` to `_CONFIRMED_WORKING_CASE_IDS` in `tests/_maple_coverage_data.py` so regressions fail hard instead of silently flipping to XPASS.

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| DB lookup adds perceptible latency to every message | In-memory per-company name cache; invalidate on CRUD mutations. Only run lookup when keyword match is empty. |
| False positives from over-aggressive name matching (e.g. "Hello" matches a contact named "Hello") | Require *exact* case-insensitive match of the *entire* normalized message, not substring. Skip resolution if the message contains any ACTION_HINT word. |
| Multiple resources share a name (material "Landscaper" vs role "Landscaper") | Deterministic precedence: role > property > contact > material. Document in resolver docstring. Consider surfacing ambiguity as a clarifying question when two resources match. |
| LLM over-eagerly classifies arbitrary short messages as `get_*` after prompt change | Keep the 0.8 probability threshold in the prompt; require the name to plausibly match a catalog. In eval, watch `bulk` + `equipment_blocked` categories — they must stay at 12/12 and 3/3 respectively. |
| Address regex misses Canadian / international formats | Start with the North American pattern that covers the test matrix; extend only on real user reports. Don't try to boil the ocean. |
| Phase 2b DB resolver pulls orchestrator into the data layer | It already imports the domain agents, which hit the DB — the orchestrator is already data-aware. Keep the new resolver in `service.py` as a private helper, not a public abstraction. |

## 6. Out of scope

- **Multi-entity disambiguation UX.** If "Landscaper" matches both a role and a material, a polished product would ask "Did you mean the Landscaper role or the Landscaper material?". For this plan, the precedence rule + a clarifying fallback is enough.
- **Fuzzy name matching.** "Jon Doe" → `John Doe`. Out of scope — exact match only in v1.
- **Verbless phrasings that are genuinely ambiguous between list and get.** "contacts" alone is already handled elsewhere (count/list category). Don't touch that path.
- **Non-English phrasings.** English only in v1.

## 7. Sequencing recommendation

Phase 1 is ~30 minutes and should be merged first as its own PR — it's a pure data change with minimal risk and closes 2/12 cases on Tier 1 immediately. Phases 2 and 3 are larger and should ship together, since Phase 2's rule-level resolution and Phase 3's LLM prompt reinforce each other and will be evaluated against the same gap-report diff.
