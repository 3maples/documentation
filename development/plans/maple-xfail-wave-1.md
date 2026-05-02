# Maple xfail backlog — Wave 1 (cheap wins)

**Status:** Draft (revised after re-grounding against current help architecture)
**Owner:** TBD
**Date:** 2026-05-01

## Goal

Close the cheap, high-value xfails in `tests/test_maple_help_coverage.py` and `tests/test_maple_crud_coverage.py` by extending three shared mechanisms — help-topic detection, refusal-guard gating, and possessive/field-targeted regex helpers — and adding missing content to `platform/user_guides/users_guide.md`.

## Current help architecture (verified 2026-05-01)

Before describing changes, the existing flow:

- **`agents/maple_guide/service.py:answer_from_guide`** is the canonical help responder. It builds a system prompt that embeds the entire `platform/user_guides/users_guide.md` and sends the user's message to the LLM. The LLM is instructed to answer ONLY from the guide.
- **`agents/orchestrator/help_handler.py:HelpHandler.detect_topic`** classifies a help query into a topic key (`capabilities`, `contact_roles`, `how_to_create_contact`, etc.). Topic keys are metadata only — they don't change the response text. `build_result` always calls `answer_from_guide` regardless of topic.
- **`agents/orchestrator/service.py:_apply_low_confidence_fallback` (lines 756-827)** is a last-chance guide fallback. When the rule classifier and LLM classifier both return low-confidence/unknown AND the message looks interrogative (`_looks_interrogative`), it routes to `help` with `topic="general_question"` and uses `answer_from_guide` for the response. This already handles many interrogative phrasings — `test_informational_queries_route_to_help_via_fallback` and `test_limitation_queries_route_to_help_via_fallback` pass via this path.
- **Refusal guards (`service.py:190-211` and `1228-1259`)** fire BEFORE the fallback. `is_equipment_request` / `is_bulk_delete_request` short-circuit to a refusal response regardless of whether the phrasing is interrogative.

Implication: the "right text" for almost any help question is already produced by the guide LLM if we route correctly. Most xfails are about (a) **routing** (getting `intent=help` set), (b) **topic-key precision** (test assertions on `topic` strings), and (c) **guide content gaps** (where the LLM has nothing to ground its answer in).

## Scope

**In scope (Wave 1):** 35 xfails total
- 23 help xfails (`test_maple_help_coverage.py` §9.5)
- 12 CRUD xfails covering `possessive` + `field_targeted_update` across property/contact/material/labour

**Out of scope (Wave 2 — separate plan):** 9 `implicit_relationship` xfails ("who lives at X", "what properties does Y own"). Requires a new cross-collection relationship-query intent — not a gap-fix, a feature.

## Current state

From the latest full backend run:

| Bucket | Count | File | Marker |
|---|---|---|---|
| Help: onboarding synonyms | 4 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: capability variants | 10 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: limitation queries | 2 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: unit enum queries | 2 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: implicit ("I am lost/stuck") | 2 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: work-item how-to | 1 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: cross-domain link how-to | 1 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| Help: property pluralization defect | 1 | `test_maple_help_coverage.py` | `xfail(strict=True)` |
| CRUD: possessive (4 resources × ~2 phrasings) | 6 | `test_maple_crud_coverage.py` | `xfail(strict=False)` |
| CRUD: field_targeted_update (4 resources) | 6 | `test_maple_crud_coverage.py` | `xfail(strict=False)` |

Reference doc: `documentation/development/maple-phrasing-reference.md` §2.9, §3.8, §4 (possessive/field-update gaps), §9.5 (help gaps).
Live runtime gap report: `platform/tests/reports/maple_crud_gap_report.md`.

## Phase 1 — Help-handler extensions (~1–1.5 days)

The 23 help xfails split across the help_handler topic detector, the refusal-guard gating in `service.py`, and the user guide content. Topic-key precision matters because tests assert specific strings like `topic == "capabilities"` — the guide-fallback's generic `topic = "general_question"` doesn't satisfy those assertions even though the response text would be fine.

### 1.1 Onboarding synonyms — non-interrogative cues
File: `agents/orchestrator/help_handler.py:44-55` (`has_capability_cue` token list).

Bare nouns like `tutorial` and `docs` aren't questions, so the interrogative guide-fallback ignores them. They must be caught by the rule classifier's help-topic detector.

- Add `tutorial`, `getting started`, `documentation`, `docs` to the `has_capability_cue` list. They map to `topic = "capabilities"`.
- Closes 4 onboarding-synonym xfails.
- Verify `users_guide.md` §3.12 "Getting started" already covers tutorial/onboarding — yes it does, no guide edits needed.

### 1.2 Capability variants — topic-key precision
File: `help_handler.py:44-55`.

Many of these are interrogative ("how does this work?", "what do you do?") and would route to `help` via the guide fallback — but with `topic = "general_question"`, not `topic = "capabilities"` which the tests assert.

- Add `examples`, `give me`, `what kinds`, `what should i ask`, `what can i do`, `list your features`, `what do you do`, `explain maple`, `how does maple work`, `how does this work` to `has_capability_cue`.
- Bare `examples` is a risk — could collide with "examples of materials". Anchor with `give me examples` / `list examples` rather than the bare word, and adjust the test phrasing list if needed (it currently includes `"examples"` as a bare phrasing — confirm with reference doc §9.5 before promoting/demoting).
- Closes 10 capability-variant xfails.

### 1.3 Implicit "lost / stuck" phrasings
File: `help_handler.py:44-55`.

`i am lost` / `i am stuck` are not interrogative and not currently caught. They misroute to `get_material` via the filter-find fallback (per the test comment).

- Add `i am lost`, `i am stuck`, `i'm lost`, `i'm stuck` cues → `topic = "capabilities"`. Make sure they're matched as substrings, not whole tokens.
- Closes 2 implicit-help xfails.

### 1.4 Pluralization defect
File: `help_handler.py:87` — the line `return f"how_to_manage_{domain_name}s"` produces `how_to_manage_propertys`.

- Replace with a small irregular-plural map: `{"property": "properties"}`, fallback appends `s`. Apply the same map at any other `f"...{domain_name}s"` spots in the same function (none others spotted, but verify).
- Closes 1 property-pluralization xfail.

### 1.5 Work-item domain aliasing
File: `help_handler.py:73-89`.

`how do I add a work item?` should resolve into the estimate domain. The test asserts `topic == "how_to_manage_estimates"` (not `how_to_add_estimate`), which means the path through `for action in action_hints` needs to NOT match for line-item phrasings — they should fall through to the manage form.

- Add a tuple of estimate-scoped line-item aliases (`work item`, `job item`, `line item`, `scope`). Reuse the existing `ORCHESTRATOR_EXTRA_FIELD_KEYWORDS` from `text_utils.py` — same vocabulary, don't duplicate.
- When the message contains any of those aliases AND an estimate domain word OR the alias alone, force the topic to `how_to_manage_estimates` (skip the action-hint branch for these).
- Closes 1 work-item xfail.

### 1.6 Cross-domain link topic
File: `help_handler.py:73-89` + `users_guide.md`.

`how do I link a contact to a property?` currently picks the first matching domain in the list (`contact`) → `how_to_manage_contacts`. The test wants its own topic `how_to_link_contact_property`.

- Add detection: when the message contains an instructional verb (`link`, `connect`, `associate`) AND both a contact alias AND a property alias, return `topic = "how_to_link_contact_property"`.
- Add a "Linking contacts and properties" subsection to `users_guide.md` (the existing §3.10 "How to create a property" mentions linking but no dedicated topic). Without guide content the LLM will say "I'm not sure" even with correct routing.
- Closes 1 cross-domain-link xfail.

### 1.7 Unit-enum topics + guide content
File: `help_handler.py:30-91` + `users_guide.md`.

`what are the labour units?` / `what are the material units?` need both topic detection AND guide content (verified missing — `grep` for `labour units` / `material units` in the guide returns nothing).

- In `detect_topic`: detect when the message contains `unit`/`units` AND a domain hint (labour/labor/material) → return `topic = "labour_units"` or `"material_units"`.
- In `users_guide.md`: add two new subsections under §3 listing the LabourUnit and MaterialUnit enum members. Source the values from `models/labour.py` and `models/material.py` (or wherever the enums live — verify path during implementation; don't hardcode values that will drift from the enum). Consider whether to auto-generate this section via `loader.py` to avoid drift.
- Closes 2 unit-enum xfails.

### 1.8 Limitation-query reframe — gate the refusal guards
File: `agents/orchestrator/service.py:190-211` and `1228-1259`.

The 2 limitation xfails (`does Maple support equipment?`, `is there a way to bulk delete contacts?`) hit the equipment / bulk-delete refusal short-circuits BEFORE the guide fallback.

- Wrap each refusal short-circuit in `if not _looks_interrogative(normalized): ...refuse...`. Interrogative forms fall through to the guide fallback, which already covers equipment limitations (§"What Maple won't do (on purpose)" in the guide) and bulk-delete policy.
- Imperative forms (`delete all contacts`, `wipe my materials`, `manage equipment`) still refuse — they're not interrogative.
- The fallback's `topic = "general_question"` is sufficient: the limitation-query xfail tests only assert `intent == "help"`, not a specific topic.
- Closes 2 limitation-query xfails.

### Phase 1 summary
| Sub-phase | Closes | Surface |
|---|---|---|
| 1.1 Onboarding synonyms | 4 | help_handler.py |
| 1.2 Capability variants | 10 | help_handler.py |
| 1.3 Implicit lost/stuck | 2 | help_handler.py |
| 1.4 Pluralization fix | 1 | help_handler.py |
| 1.5 Work-item alias | 1 | help_handler.py + text_utils import |
| 1.6 Cross-domain link | 1 | help_handler.py + users_guide.md |
| 1.7 Unit-enum topics | 2 | help_handler.py + users_guide.md |
| 1.8 Refusal-guard gating | 2 | orchestrator/service.py |
| **Phase 1 total** | **23** | |

## Phase 2 — Possessive + field-targeted-update helper (~1 day)

All 12 CRUD xfails share one root cause: no parser for `<entity-name>'s <field>` or `set <entity>'s <field> to <value>`.

### 2.1 New helpers in `agents/text_utils.py`

Following the existing `build_add_set_field_pattern` / `build_bare_field_pattern` style:

```python
def build_possessive_field_pattern(field_keywords: Iterable[str]) -> re.Pattern[str]:
    """Match `<name>'s <field>` and `<name>s <field>` (typo-tolerant)."""
    # captures: 1=entity name, 2=field

def build_field_targeted_update_pattern(field_keywords: Iterable[str]) -> re.Pattern[str]:
    """Match `set <name>'s <field> to <value>` and
    `change/update the <field> of <name> to <value>`."""
    # captures: 1=entity name, 2=field, 3=value
```

Reuse `SHARED_UPDATE_FIELD_KEYWORDS` (already exists, line 48) so all four resources stay consistent. Keep the per-resource subset hooks (`CONTACT_UPDATE_FIELD_KEYWORDS` style) as the seam if a resource needs to exclude a keyword.

### 2.2 Wire into the four agents

For each of `agents/{property,contact,material,labour}/service.py`:

- In the rule-classification path, run the possessive pattern **before** the existing entity-lookup logic. On match → `get_<resource>` with field focus stored in result payload (so the response can surface "John's phone is 555-1234" rather than the full record).
- Run the field-targeted-update pattern before the bare-name fallback. On match → `update_<resource>` with `{field, value}` already extracted, skipping the multi-turn `awaiting_value_for` flow.
- Add new tests alongside the existing service tests (one happy-path + one ambiguous-name case per resource).

The xfail markers in `test_maple_crud_coverage.py` are `strict=False`, so they auto-flip to PASS without code changes to the test file. Once green, **promote them to `strict=True`** in a follow-up commit so they can't silently regress.

### 2.3 Gap report regeneration

`tests/conftest.py` already regenerates `tests/reports/maple_crud_gap_report.md` on every run. Verify the Tier-1 numbers move from `96/117 → 108/117` after Phase 2.

## Phase 3 — Documentation sync

Per CLAUDE.md, every Maple phrasing change must update `documentation/development/maple-phrasing-reference.md` in the same change:

- Flip ⚠️ gap → ✅ rule in §2.9, §3.8, §4 (and any equivalent in §5/§9.5) for each phrasing closed.
- Update §9.3 snapshot counts.
- Bump the "Last updated" date.

## Test strategy

- Per CLAUDE.md TDD policy: failing test first, implementation after. The xfails *are* the failing tests — removing the marker (or letting `strict=False` flip) is the green signal.
- After each phase, run only the relevant test file (`./run_tests.sh tests/test_maple_help_coverage.py` or `tests/test_maple_crud_coverage.py`).
- Do not run the full suite — user runs that manually.
- After Phase 2, also run `tests/test_property_agent.py`, `tests/test_contact_agent.py`, `tests/test_material_agent.py`, `tests/test_labour_agent.py` to confirm no regression in existing rules.

## PR strategy

Four small PRs, not one mega-PR:

1. **`feat: widen Maple help-topic detection for synonyms, capability variants, and stuck phrasings`** — Phases 1.1 + 1.2 + 1.3 + 1.4 (low-risk: additions to the cue list + plural map fix). 17 xfails closed. No guide edits.
2. **`feat: add work-item, cross-domain-link, and unit-enum help topics`** — Phases 1.5 + 1.6 + 1.7 (touches help_handler logic AND adds three new sections to `users_guide.md`). 4 xfails closed.
3. **`feat: route interrogative equipment and bulk-delete questions to help`** — Phase 1.8 (touches refusal guards in orchestrator/service.py — needs careful review for regressions in existing refusal tests). 2 xfails closed.
4. **`feat: parse possessive and field-targeted-update phrasings across Maple agents`** — Phase 2. 12 xfails closed.

Each PR includes the relevant `maple-phrasing-reference.md` updates per CLAUDE.md.

## Risks

- **Capability-variant cues like `examples` are very generic.** "Examples of materials" should still route to material CRUD, not help. Mitigation: anchor cues (`give me examples`, `list examples`) instead of bare `examples`. Confirm against the test list before promoting.
- **Possessive parsing collides with bare-name lookup.** "John's phone" must not trigger `delete_contact("John's phone")`. Mitigation: possessive pattern runs *first*; bare-name fallback never sees the apostrophe-s form.
- **Cross-domain link detection** could over-fire on "create a contact at this property" (single-resource intent with two domain words). Mitigation: gate strictly on the instructional verb `link`/`connect`/`associate`.
- **Refusal-guard gating regression risk.** Existing tests already cover imperative refusals — verify `tests/test_orchestrator_endpoint.py` and `tests/test_orchestrator_intents.py` still pass. The two interrogative phrasings now route to help; the imperative variants must still refuse.
- **Unit-enum guide content drift.** Hardcoding the enum values in markdown means the guide drifts when enums change. Mitigation: prefer auto-generation via `user_guides/loader.py` (it already exists for `users_guide.md` loading). Investigate the loader before committing to a hand-written section.

## Done criteria

- All 35 in-scope xfails either flip to passing (and have markers removed) or are explicitly re-categorized in the reference doc with a justification.
- `tests/reports/maple_crud_gap_report.md` shows Tier-1 ≥ 108/117.
- `documentation/development/maple-phrasing-reference.md` snapshot counts and "Last updated" reflect the new state.
- Full backend suite still green (user-run).

## Wave 2 preview (not in this plan)

The remaining 9 `implicit_relationship` xfails ("who lives at X", "what properties does Y own", "where is `concrete blocks` used") need a new `relate_<a>_to_<b>` intent and a join-style query handler. Worth its own design doc — flag for follow-up after Wave 1 ships.
