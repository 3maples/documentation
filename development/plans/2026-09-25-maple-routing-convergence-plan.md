# Maple Routing Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/code-review` rounds over Maple's estimate editing converge to no new findings. Rules shrink to a written command list, one module decides whether a message answers an open question, guessed targets are confirmed, and a routing snapshot catches collateral changes.

**Architecture:**
- **Command list.** `agents/estimate/command_grammar.py` holds every phrasing a rule handles: new anchored "core" patterns plus "ported" wrappers around existing detectors that have no planner equivalent. Everything else goes to the existing LLM edit planner (for edits) or the LLM classifier (for routing).
- **Open-question decider.** `routers/agent_helpers/open_question.py` is the only code that decides whether a message answers an Estimate question or the estimate yes/no confirmation.
- **Freshness.** Anchors record the turn they were set, and the edit executor confirms before writing to a stale guessed target.
- **Snapshot.** A checked-in routing snapshot, under `tests/maple_routing/`, shows every behavior change a rule edit causes.

**Tech Stack:** FastAPI + Beanie (Python 3, pytest, mypy, ruff), React 18 + TypeScript + Vitest (portal).

**Spec:** [`2026-09-25-maple-routing-convergence-design.md`](2026-09-25-maple-routing-convergence-design.md). Its parent is [`2026-09-23-maple-estimate-multi-turn-editing.md`](2026-09-23-maple-estimate-multi-turn-editing.md). Read both first.

## Global Constraints

**Commits and backups**
- **Nothing is committed.** Simon chose to keep the work uncommitted (design D4). Wherever a task would commit, it instead writes a patch backup:
  ```bash
  S=/private/tmp/claude-501/-Users-simon-Development-Tangz-3maples/be7231eb-af20-4e40-8dc1-1aac94c6c48b/scratchpad/backups; mkdir -p $S; for r in platform portal documentation; do (cd /Users/simon/Development/Tangz/3maples/$r && git diff > $S/<task>-$r.patch && git ls-files --others --exclude-standard | tar -czf $S/<task>-$r-untracked.tgz -T -); done
  ```
- Commit, push, branch creation and `main → release` each need Simon's explicit approval. Never do them on your own.

**Tests and gates**
- **TDD is mandatory** for every `.py` / `.tsx` / `.ts` behavior change. Write the failing test, watch it fail, then implement.
- **Python gates.** After every `.py` edit, run `./run_mypy.sh <subtree>` and `./run_ruff.sh <subtree>` from `platform/` with the venv active. Both must be clean.
- **Run only the related tests.** Never the full suite; Simon runs that.
- **Start the database first.** Platform tests need `./scripts/start_test_mongo.sh` running.
- **Portal gates.** After `.tsx`/`.ts` edits, run `npm test -- <file>` and `npm run typecheck` from `portal/`.
- **bandit baseline** is 11 `B110`. Never add a bare `except Exception: pass`.

**Conventions**
- **US spelling:** labor, behavior, color.
- **Phrasing reference.** Any change to what Maple accepts updates `documentation/development/maple-phrasing-reference.md` in the same task, including a "Last updated" bump.
- **Pricing parity.** Portal and server pricing change together or not at all (`CLAUDE.md`, "Pricing model").
- **Re-export hubs** (`routers/agents.py`, `routers/estimates.py`, `agents/estimate/service.py`) list re-exported names in `__all__`. Never blanket `ruff --fix` F401 there.
- **No new regex outside `command_grammar.py`** to fix a routing finding (spec §10).
- **`agents/estimate/edit_executor.py` is the only write path** for Maple content edits. No new handler gets its own persistence.

## Review Focus

Each of these has a test in the task named in brackets.

1. **Punctuation on translated replies.** Replies arrive after the translation step with a capital and a full stop ("Yes.", "No thanks."). `is_affirmative_text` does an exact match, so "Yes." must still count as yes. [Task 7]
2. **Typographic variants.** Curly apostrophes ("what’s"), `#` in "work item #2", "20 %" with a space, doubled spaces, and a trailing "please" must match the same entry as the plain form. [Task 6]
3. **Very long messages.** A 10,000-character message must match or fail in under 50 ms. There must be no catastrophic backtracking in the new patterns. [Task 6]
4. **Switching estimates with a question open.** If the user moves to another estimate page while an Estimate question is open, that question is dropped. A "yes" typed next must not confirm an action on the estimate they left. [Task 7]
5. **Page open on a different estimate than the anchor.** An anchor that differs from the estimate on screen counts as fresh only by turn. [Task 8]

---

## File map

**New files (platform)**

| File | Responsibility |
|---|---|
| `agents/estimate/command_grammar.py` | The written command list (spec §4). `ListedCommand`, `match_command(text, agent=None)`, `CORE_ENTRIES`, `PORTED_ENTRIES`, `UPDATE_COMMAND_IDS` |
| `routers/agent_helpers/open_question.py` | The open-question decider (spec §5.1): `OpenQuestion`, `Decision`, `current_question`, `decide`, `drop_question` |
| `agents/estimate/target_freshness.py` | Turn-based freshness (spec §5.2): `TURN_INDEX_KEY`, `ESTIMATE_RESOLVED_BY_KEY`, `estimate_is_fresh`, `work_item_is_fresh`, `freshest_anchor` |
| `tests/maple_routing/corpus.json`, `expected.json`, `snapshot_routing.json`, `snapshot_grammar.json`, `snapshot_decide.json` | Snapshot data |
| `tests/maple_routing/__init__.py`, `tests/maple_routing/states.py` | Anchor and question states |
| `tests/test_maple_routing_snapshot.py` | Snapshot and expected-row tests |
| `tests/test_command_grammar.py`, `tests/test_open_question.py`, `tests/test_target_freshness.py` | Unit tests |

**New files (portal)**

| File | Responsibility |
|---|---|
| `tests/workItemChange.test.ts` | `applyWorkItemChange` unit tests |
| `tests/NewEstimateWithActivityPage.workItemSave.test.tsx` | #1/#11/#12/#24/#25 page tests |

**Modified files**

| Area | Files |
|---|---|
| Router | `routers/agents.py`, `routers/agent_helpers/{finalize_result,fuzzy_confirmation,delegate_estimate_ops,estimate_update,active_estimate,pending_estimate_follow_up}.py` |
| Estimate agent | `agents/estimate/{service,crud_handlers,work_item_context,work_item_handlers,work_item_field_handlers,work_item_edit_detectors,work_item_edit_handlers,edit_executor,edit_planner,assumption_handlers}.py` |
| Services | `services/estimate_delete.py`, `routers/estimate_helpers/calculations.py` |
| Orchestrator | `agents/orchestrator/service.py` |
| Prompt | `prompts/estimate_edit_planner.py` |
| Portal | `src/pages/NewEstimateWithActivityPage.tsx`, `src/lib/workItemV2.ts`, `src/api/estimates.ts` |
| Docs | `documentation/development/{maple-phrasing-reference,code-review-followups}.md`, `CLAUDE.md`, `.claude/commands/code-review.md` |

---

### Task 0: Routing snapshot scaffold and baseline

**Files:**
- Create: `platform/tests/maple_routing/__init__.py` (empty)
- Create: `platform/tests/maple_routing/states.py`
- Create: `platform/tests/maple_routing/corpus.json`, `platform/tests/maple_routing/expected.json`, `platform/tests/maple_routing/snapshot_routing.json`
- Create: `platform/tests/test_maple_routing_snapshot.py`

**Interfaces:**
- Produces:
  - `ANCHOR_STATES: Dict[str, Dict[str, Any]]` with keys `none`, `est`, `wi`, `est_then_mat`.
  - `QUESTION_STATES: Dict[str, Dict[str, Any]]` with keys `yes_no`, `pick`, `free_text`. Tasks 7 and 8 use these.
  - `load_corpus() -> List[str]`.
  - Env var `UPDATE_MAPLE_SNAPSHOT=1`, which rewrites snapshot files instead of comparing.
  - Expected-row schema: `{"phrase", "state", "layer": "routing"|"grammar"|"decide", "expect": {...}, "finding": "#N", "task": <int>}`. `expect` keys:
    - `intent`, `agent`, `intent_not` for routing;
    - `command` (id or `null`) for grammar;
    - `decision` for decide.
  - A row is xfail (strict) until its `task` is done. The task that fixes it removes the `task` key.

- [ ] **Step 1: Back up**

Run the backup command from Global Constraints with `<task>` = `t0`.

- [ ] **Step 2: Copy the corpus**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
mkdir -p tests/maple_routing && touch tests/maple_routing/__init__.py
python3 - <<'EOF'
import json
src = "/private/tmp/claude-501/-Users-simon-Development-Tangz-3maples/be7231eb-af20-4e40-8dc1-1aac94c6c48b/scratchpad/rv6c/corpus.json"
corpus = json.load(open(src))
extra = [
 "jot down a note for John Doe: call after 5", "add a note to concrete blocks: supplier changed",
 "hey, add a note to work item 2: check drainage", "yes, add a note to work item 2: check drainage",
 "great, now add a note to work item 2: check drainage", "quick note on work item 2: check drainage",
 "perfect, add a note to the back patio work item saying check drainage",
 "show me the estimate for the Smith property", "can you show me my estimates", "go back to E0001",
 "what's the total on this estimate?", "list the estimates for Bob Smith",
 "open the Jones backyard estimate please", "actually, show me my estimates",
 "never mind, show my estimates", "and how many estimates do I have?",
 "Remove all debris and haul away", "Show homeowner the revised quote before starting",
 "archive the patio job", "mark the patio job as sent", "set the patio job to approved",
 "change the cost of Landscaper to $50", "update the Foreman cost to $60",
 "set Landscaper's cost to $50", "change the cost of concrete blocks to $5",
 "add a work item called Equipment staging",
 "add a note to work item 2: equipment will be staged on the driveway",
 "12 Equipment Road, Springfield", "set the markup to 20%", "set the overhead to 10%",
 "set the tax to 13%", "make the gross margin 30%", "change the markup to 25 percent",
 "our supplier raised prices, make the pavers $5", "list my contacts",
 "how many properties do I have?", "add a contact named Ana Reyes", "delete it", "remove it",
 "rename it", "add a note: call the supplier about the price", "leave a note that the gate is locked",
 "create a note: follow up tomorrow", "drop a note: check the gate",
 "set the hours on grading to 2 days", "set the quantity of mulch to 3 yards",
]
for p in extra:
    corpus.setdefault(p, {"src": "review-6"})
json.dump(corpus, open("tests/maple_routing/corpus.json", "w"), indent=1, sort_keys=True)
print(len(corpus))
EOF
```
Expected: prints about 980.

Then open `documentation/development/code-review-followups.md`, entries #627–#661. Add every phrasing quoted there to `corpus.json` with `{"src": "followup:#<N>"}`, one entry per phrasing.

- [ ] **Step 3: Write `states.py`**

```python
"""Conversation states the routing snapshot runs every phrasing through.

Anchor states feed ``OrchestratorAgent.process``; question states feed
``open_question.decide`` (from Task 7). Ids are fixed fakes — nothing here
touches the database.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DATA = Path(__file__).parent
CO = "a" * 24
EST_ID = "b" * 24
WI_A = "c" * 24
WI_B = "e" * 24

_EST = {
    "company_id": CO,
    "active_estimate_code": "E0042",
    "active_estimate_id": EST_ID,
    "active_entity_domain": "estimate",
    "turn_index": 5,
    "active_estimate_set_turn": 4,
}

ANCHOR_STATES: Dict[str, Dict[str, Any]] = {
    "none": {"company_id": CO, "turn_index": 5},
    "est": dict(_EST),
    "wi": {
        **_EST,
        "active_work_item": {
            "estimate_code": "E0042", "job_item_id": WI_A, "position": 1,
            "description": "Front yard cleanup", "activities": ["Excavation", "Mowing"],
            "set_at": "2026-09-25T00:00:00+00:00", "set_turn": 5,
        },
    },
    "est_then_mat": {
        **_EST,
        "active_entity_domain": "material",
        "active_material_id": "d" * 24,
        "active_material_name": "Mulch",
    },
}

QUESTION_STATES: Dict[str, Dict[str, Any]] = {
    "yes_no": {
        **_EST,
        "pending_estimate_fuzzy_confirmation": {
            "intent": "update_estimate", "sub_op": "use_active_estimate",
            "estimate_id": EST_ID, "estimate_code": "E0042", "estimate_title": "Rv Yard",
            "original_message": "archive the Henderson job",
            "clarifying_question": "I couldn't find an estimate named 'Henderson'. Did you mean E0042 'Rv Yard'?",
        },
    },
    "pick": {
        **_EST,
        "pending_intents": [{
            "id": "estimate-choose-work-item", "agent": "Estimate Agent",
            "intent": "update_estimate", "fields": {}, "question_id": "q-pick",
            "op": "choose_work_item", "estimate_code": "E0042",
            "original_message": "set the markup to 20%",
            "candidates": [
                {"job_item_id": WI_A, "description": "Front yard cleanup", "position": 1},
                {"job_item_id": WI_B, "description": "Back patio pavers", "position": 2},
            ],
        }],
    },
    "free_text": {
        **_EST,
        "pending_intents": [{
            "id": "estimate-description-value", "agent": "Estimate Agent",
            "intent": "update_estimate", "fields": {}, "question_id": "q-desc",
            "op": "set_description", "awaiting_value_for": "description",
            "estimate_code": "E0042", "original_message": "update the description on work item 2",
        }],
    },
}


def load_corpus() -> List[str]:
    return sorted(json.loads((DATA / "corpus.json").read_text()))
```

- [ ] **Step 4: Write `expected.json`**

This file pins the spec's §8.1 phrasings. Each row has the task that will make it pass:

```json
[
 {"phrase": "jot down a note for John Doe: call after 5", "state": "est", "layer": "routing", "expect": {"agent": "Contact Agent"}, "finding": "#2", "task": 10},
 {"phrase": "add a note to concrete blocks: supplier changed", "state": "est", "layer": "routing", "expect": {"intent_not": "update_estimate"}, "finding": "#2", "task": 10},
 {"phrase": "hey, add a note to work item 2: check drainage", "state": "est", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#3", "task": 10},
 {"phrase": "yes, add a note to work item 2: check drainage", "state": "est", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#3", "task": 10},
 {"phrase": "great, now add a note to work item 2: check drainage", "state": "est", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#3", "task": 10},
 {"phrase": "quick note on work item 2: check drainage", "state": "est", "layer": "routing", "expect": {"intent_not": "create_estimate"}, "finding": "#3", "task": 10},
 {"phrase": "perfect, add a note to the back patio work item saying check drainage", "state": "est", "layer": "grammar", "expect": {"command": "add_note"}, "finding": "#3", "task": 6},
 {"phrase": "show me the estimate for the Smith property", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "can you show me my estimates", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "go back to E0001", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "what's the total on this estimate?", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "list the estimates for Bob Smith", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "open the Jones backyard estimate please", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "actually, show me my estimates", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "never mind, show my estimates", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "and how many estimates do I have?", "state": "free_text", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#4", "task": 7},
 {"phrase": "Remove all debris and haul away", "state": "free_text", "layer": "decide", "expect": {"decision": "answer"}, "finding": "#4", "task": 7},
 {"phrase": "Show homeowner the revised quote before starting", "state": "free_text", "layer": "decide", "expect": {"decision": "answer"}, "finding": "#4", "task": 7},
 {"phrase": "change the cost of Landscaper to $50", "state": "wi", "layer": "routing", "expect": {"intent_not": "update_estimate"}, "finding": "#8", "task": 10},
 {"phrase": "update the Foreman cost to $60", "state": "wi", "layer": "routing", "expect": {"intent_not": "update_estimate"}, "finding": "#8", "task": 10},
 {"phrase": "change the cost of concrete blocks to $5", "state": "wi", "layer": "routing", "expect": {"intent_not": "update_estimate"}, "finding": "#8", "task": 10},
 {"phrase": "add a work item called Equipment staging", "state": "est", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#14", "task": 10},
 {"phrase": "add a note to work item 2: equipment will be staged on the driveway", "state": "est", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#14", "task": 10},
 {"phrase": "set the markup to 20%", "state": "est_then_mat", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#16", "task": 10},
 {"phrase": "set the overhead to 10%", "state": "est_then_mat", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#16", "task": 10},
 {"phrase": "set the tax to 13%", "state": "est_then_mat", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#16", "task": 10},
 {"phrase": "make the gross margin 30%", "state": "est_then_mat", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#16", "task": 10},
 {"phrase": "change the markup to 25 percent", "state": "est_then_mat", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#16", "task": 10},
 {"phrase": "list my contacts", "state": "yes_no", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#19", "task": 7},
 {"phrase": "how many properties do I have?", "state": "yes_no", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#19", "task": 7},
 {"phrase": "add a contact named Ana Reyes", "state": "yes_no", "layer": "decide", "expect": {"decision": "new_message"}, "finding": "#19", "task": 7},
 {"phrase": "delete it", "state": "wi", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#20", "task": 10},
 {"phrase": "remove it", "state": "wi", "layer": "routing", "expect": {"intent": "update_estimate"}, "finding": "#20", "task": 10},
 {"phrase": "add a note: call the supplier about the price", "state": "est_then_mat", "layer": "routing", "expect": {"intent_not": "update_material"}, "finding": "#21", "task": 10},
 {"phrase": "set the hours on grading to 2 days", "state": "wi", "layer": "grammar", "expect": {"command": null}, "finding": "#22", "task": 6}
]
```

- [ ] **Step 5: Write the failing snapshot test**

`tests/test_maple_routing_snapshot.py`:

```python
"""Routing snapshot (design 2026-09-25 §5.5).

Every corpus phrasing runs through each state, rules only. ``recorded``
layers compare against ``tests/maple_routing/snapshot_*.json``; rerun with
``UPDATE_MAPLE_SNAPSHOT=1`` only after reviewing the diff. ``expected.json``
rows assert what the design requires; a row with a ``task`` key is a strict
xfail until that task removes the key.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
from typing import Any, Dict, List

import pytest

from agents.orchestrator.service import OrchestratorAgent
from tests.maple_routing.states import ANCHOR_STATES, DATA, load_corpus

UPDATE = os.environ.get("UPDATE_MAPLE_SNAPSHOT") == "1"


@pytest.fixture(autouse=True)
def _no_guide_llm(monkeypatch):
    async def _stub(*_a, **_k):
        return "GUIDE"
    import agents.maple_guide as mg
    import agents.orchestrator.help_handler as hh
    import agents.orchestrator.service as svc
    for mod in (svc, hh, mg):
        if hasattr(mod, "answer_from_guide"):
            monkeypatch.setattr(mod, "answer_from_guide", _stub)


def _route_row(agent: OrchestratorAgent, phrase: str, state: str) -> List[Any]:
    result = asyncio.run(agent.process(phrase, copy.deepcopy(ANCHOR_STATES[state])))
    return [result.get("intent"), result.get("agent")]


def _compare(name: str, actual: Dict[str, Any]) -> None:
    path = DATA / name
    if UPDATE or not path.exists():
        path.write_text(json.dumps(actual, indent=1, sort_keys=True) + "\n")
        return
    recorded = json.loads(path.read_text())
    changed = [
        f"{key}: {recorded.get(key)!r} -> {actual.get(key)!r}"
        for key in sorted(set(recorded) | set(actual))
        if recorded.get(key) != actual.get(key)
    ]
    assert not changed, (
        f"{len(changed)} {name} rows changed (review, then UPDATE_MAPLE_SNAPSHOT=1):\n"
        + "\n".join(changed[:80])
    )


def test_routing_snapshot():
    agent = OrchestratorAgent(use_llm=False)
    actual = {
        phrase: {state: _route_row(agent, phrase, state) for state in ANCHOR_STATES}
        for phrase in load_corpus()
    }
    _compare("snapshot_routing.json", actual)


def _expected_rows() -> List[Any]:
    rows = json.loads((DATA / "expected.json").read_text())
    return [
        pytest.param(
            row, id=f"{row['finding']}-{row['layer']}-{row['state']}-{row['phrase'][:40]}",
            marks=[pytest.mark.xfail(strict=True, reason=f"fixed in Task {row['task']}")]
            if "task" in row else [],
        )
        for row in rows
    ]


@pytest.mark.parametrize("row", _expected_rows())
def test_expected_row(row: Dict[str, Any]) -> None:
    expect = row["expect"]
    if row["layer"] == "routing":
        intent, agent_name = _route_row(OrchestratorAgent(use_llm=False), row["phrase"], row["state"])
        if "intent" in expect:
            assert intent == expect["intent"]
        if "agent" in expect:
            assert agent_name == expect["agent"]
        if "intent_not" in expect:
            assert intent != expect["intent_not"]
    elif row["layer"] == "grammar":
        from agents.estimate.command_grammar import match_command  # Task 6
        found = match_command(row["phrase"])
        assert (found.id if found else None) == expect["command"]
    else:
        from routers.agent_helpers.open_question import current_question, decide  # Task 7
        from tests.maple_routing.states import QUESTION_STATES
        question = current_question(QUESTION_STATES[row["state"]])
        assert question is not None
        assert decide(row["phrase"], question).value == expect["decision"]
```

- [ ] **Step 6: Record the baseline and check the xfails**

```bash
cd /Users/simon/Development/Tangz/3maples/platform && source .venv/bin/activate
time ./run_tests.sh tests/test_maple_routing_snapshot.py -q
```
Expected:
- `test_routing_snapshot` passes. The first run writes `snapshot_routing.json`.
- Every `test_expected_row` case is xfail (strict).
- Runtime: note it. If it is over 90 s, write `Task 0: Ruling: snapshot runtime <N>s` in the ledger. Then restrict `test_routing_snapshot` to phrasings whose `src` is not `matrix`; `tests/test_maple_crud_coverage.py` already covers the matrix ones.

An expected row that unexpectedly passes (XPASS strict) means today's code already does it. Remove that row's `task` key.

Run again with no changes. Expected: all pass, and the snapshot is stable.

- [ ] **Step 7: Lint**

Run `./run_ruff.sh tests/test_maple_routing_snapshot.py tests/maple_routing` and `./run_mypy.sh tests/test_maple_routing_snapshot.py`. Expected: clean.

---

### Task 1: Server write safety (#7, #9, #10, #18)

**Files:**
- Modify: `platform/routers/agent_helpers/estimate_update.py`
- Modify: `platform/routers/agent_helpers/finalize_result.py:57-71`
- Modify: `platform/routers/agent_helpers/pending_estimate_follow_up.py:414`
- Modify: `platform/routers/agent_helpers/delegate_estimate_ops.py`
- Modify: `platform/routers/agent_helpers/fuzzy_confirmation.py`
- Modify: `platform/services/estimate_delete.py`
- Test: `platform/tests/test_agent_helpers_estimate_update.py`, `test_agent_helpers_finalize_result.py`, `test_agent_helpers_delegate_estimate_ops.py`, `test_agent_helpers_fuzzy_confirmation.py`, `test_orchestrator_endpoint.py`

**Interfaces:**
- Produces: `services.estimate_delete.maple_delete_refusal(title: str) -> str`. `TRANSIENT_KEYS` now includes `"filter_by"` and `"property_id"`.

- [ ] **Step 1: Back up** (`<task>` = `t1`).

- [ ] **Step 2: Failing test for #7 (locked estimate)**

In `tests/test_agent_helpers_estimate_update.py`, next to `test_priced_work_is_appended_to_the_estimate_as_reloaded_after_generation` (line ~363), add a test that reuses that test's fakes:
- the target estimate has `status=EstimateStatus.APPROVED`;
- the fake agent gets a `_locked_status_edit_refusal` that returns `{"success": True, "response": "LOCKED", "intent": "update_estimate"}` whenever the status is not draft/review.

```python
def test_new_work_is_not_added_to_a_locked_estimate(monkeypatch):
    # Arrange exactly as the reloaded-after-generation test, but APPROVED.
    ...  # copy that test's arrange block; set target.status = EstimateStatus.APPROVED
    result = asyncio.run(run_update_estimate(**kwargs))
    assert result["response"] == "LOCKED"
    assert persisted == []   # _persist_added_job_items never ran
    assert agent.process_calls == []  # no paid generation either
```
Copy the arrange block verbatim from the neighbor test; do not invent fakes.

Run: `./run_tests.sh tests/test_agent_helpers_estimate_update.py -k locked -q`. Expected: FAIL (the work is persisted).

- [ ] **Step 3: Implement #7**

In `routers/agent_helpers/estimate_update.py`, add near the top:

```python
def _locked_refusal(agent: Any, msg: str, context_payload: Dict[str, Any], estimate: Any) -> Optional[Dict[str, Any]]:
    """The agent's Draft/Review edit-lock refusal for ``estimate``, or None.

    The add-items path reaches generation and ``_persist_added_job_items``
    without the agent's own lock check (review 2026-09-25 sixth pass #7).
    """
    refuse = getattr(agent, "_locked_status_edit_refusal", None)
    if not callable(refuse):
        return None
    code = str(getattr(estimate, "estimate_id", "") or "")
    return refuse(msg, dict(context_payload), code, estimate)
```

Call it in two places, each as `locked = _locked_refusal(agent, msg, context_payload, target_estimate)` followed by `if locked is not None: return locked`:
- in the `describes_new_work` branch, immediately before the main `agent.process` call (~line 258);
- again right after the reload at ~line 298, before `_persist_added_job_items`.

Run the test. Expected: PASS.

- [ ] **Step 4: Failing tests for #9 and #10**

In `tests/test_agent_helpers_finalize_result.py`:

```python
@pytest.mark.parametrize("key", ["filter_by", "property_id"])
def test_per_turn_keys_are_not_persisted(key):
    saved = {}
    async def _save(uid, ctx):
        saved.update(ctx); return "c1"
    result = {"success": True, "response": "ok", "context": {key: {"type": "property"} if key == "filter_by" else "p1"}}
    asyncio.run(finalize_orchestrate_result(result, delegate_context={}, merged_context={}, user_id="u1", save_conversation_context=_save))
    assert key not in saved
```

In `tests/test_orchestrator_endpoint.py`, add a test that seeds a persisted `property_id` with `call_with_seeded_state`, sends "create an estimate for a 200 sq ft patio" with no `request.property`, and asserts that the context the stub Estimate Agent receives has no `property_id`. Use the stub-agent pattern already in that file; see `falls_back_to_pending_agent` (~line 362).

Run both. Expected: FAIL.

- [ ] **Step 5: Implement #9 and #10**

- In `finalize_result.py`, add `"filter_by",` and `"property_id",` to `TRANSIENT_KEYS`, with the comment `# per-turn: a list filter and a request's page property (sixth pass #9, #10)`. The load-time pop at `routers/agents.py:1056` already loops over `TRANSIENT_KEYS`, and `property_id` is re-set from `request.property` at 1075.
- In `pending_estimate_follow_up.py:414`, delete `context_payload["property_id"] = property_doc_id`. Keep the `active_property_id` line.
- Check `tests/test_agent_helpers_pending_estimate_follow_up.py` (or grep `property_id` in tests) for an assertion on the deleted key. Update it to assert `active_property_id`.

Run the tests from Step 4 plus `./run_tests.sh tests/test_agent_helpers_finalize_result.py tests/test_orchestrate_client_context.py -q`. Expected: PASS.

- [ ] **Step 6: Failing test for #18 (delete permission before confirming)**

In `tests/test_agent_helpers_delegate_estimate_ops.py`, next to `test_delete_exact_match_requires_confirmation` (~line 160):

```python
def test_a_member_is_refused_before_being_asked_to_confirm(monkeypatch):
    # Arrange as test_delete_exact_match_requires_confirmation, with the
    # estimate created_by_email="owner@x.com" and context
    # current_user_email="member@x.com", current_user_role="Member".
    ...
    result = asyncio.run(delegate_delete_estimate(**kwargs))
    assert result["success"] is False
    assert "Only the estimate's creator or an Owner" in result["response"]
    assert PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY not in context_payload
```

In `tests/test_agent_helpers_fuzzy_confirmation.py`, change `test_a_member_cannot_delete_another_users_estimate` to also assert `result["success"] is False`.

Run both. Expected: FAIL.

- [ ] **Step 7: Implement #18**

In `services/estimate_delete.py`:

```python
def maple_delete_refusal(title: str) -> str:
    """What Maple says when the user may not delete the estimate."""
    return f"Only the estimate's creator or an Owner can delete estimate '{title}', so I've left it as is."
```

In `delegate_estimate_ops.py`, after the no-target branch (~line 197) and before the pending record is stashed:

```python
if not may_delete_estimate(
    target_estimate,
    str(context_payload.get("current_user_email") or ""),
    context_payload.get("current_user_role"),
):
    refused = _envelope(
        message=message, intent=intent, probability=probability,
        response=maple_delete_refusal(est_title), result=None,
        context_payload=context_payload,
    )
    refused["success"] = False
    return refused
```
`est_title` is built just above; move the check below it if needed.

In `fuzzy_confirmation.py:88-98`:
- use `maple_delete_refusal(estimate_title)` for the response;
- set `success=False` on the returned envelope. Use the same "build, then set `success`" pattern if `_envelope` there takes no `success` argument.

Run both test files. Expected: PASS.

- [ ] **Step 8: Gates**

```bash
./run_mypy.sh routers/agent_helpers services && ./run_ruff.sh routers/agent_helpers services
./run_tests.sh tests/test_agent_helpers_estimate_update.py tests/test_agent_helpers_finalize_result.py tests/test_agent_helpers_delegate_estimate_ops.py tests/test_agent_helpers_fuzzy_confirmation.py tests/test_maple_routing_snapshot.py -q
```
Expected: clean, all pass, and the snapshot is unchanged.

---

### Task 2: Assumption swap scope and pricing parity (#6, #23)

**Files:**
- Modify: `platform/agents/estimate/assumption_handlers.py:382-464`
- Modify: `platform/routers/estimate_helpers/calculations.py:187-272`
- Modify: `platform/agents/estimate/work_item_field_handlers.py:968-981`, `platform/agents/estimate/work_item_handlers.py:91-126`
- Test: `platform/tests/test_estimate_assumption_adjustment.py`, `platform/tests/test_estimate_calculations_gross_margin.py`, `portal/tests/estimateCalculations.test.ts` (read only; parity check)

**Interfaces:**
- Produces: `work_item_breakdown(item)`, which no longer counts `item.labours`. Signature unchanged.

- [ ] **Step 1: Back up** (`t2`).

- [ ] **Step 2: Failing test for #6**

In `TestMaterialAssumptionSwap` (`tests/test_estimate_assumption_adjustment.py:341`), copy the arrange block from `test_swaps_matching_lines_and_reprices`, but with:
- one work item holding the lines "Standard pavers", "Paver base", "Polymeric paver sand" and "Paver edge restraint";
- a second work item, "Fence", holding "Standard pavers";
- the materials assumption `display_text="standard pavers"` and `scope="Front patio"`, where the first item's description is "Front patio pavers".

```python
def test_swap_touches_only_the_best_line_in_the_assumptions_work_item(self):
    ...
    first, second = target.job_items
    assert [m.name for m in first.materials] == ["Premium pavers", "Paver base", "Polymeric paver sand", "Paver edge restraint"]
    assert [m.name for m in second.materials] == ["Standard pavers"]

def test_two_close_lines_ask_instead_of_swapping(self):
    # lines "Standard pavers" and "Standard paver caps" (both score >= 85)
    ...
    assert result["needs_clarification"] is True
    assert not persisted
```
Run: `./run_tests.sh tests/test_estimate_assumption_adjustment.py -k "best_line or close_lines" -q`. Expected: FAIL.

- [ ] **Step 3: Implement #6**

- Add `_SWAP_MATCH_THRESHOLD = 85  # a swap rewrites a line's identity — stricter than the size path's 60 (sixth pass #6)`.
- Change `_swap_material_lines(self, job_items, old_text, replacement, *, only_index: Optional[int] = None) -> Tuple[int, List[str]]`:
  1. Score every material line in scope (skip `index != only_index` when `only_index` is set).
  2. Keep the lines scoring ≥ `_SWAP_MATCH_THRESHOLD`.
  3. If more than one line has the top score, return `(0, [names…])` and swap nothing.
  4. Otherwise swap only the single top line, and return `(1, [])`.
- In `_handle_assumption_material_swap`, pass `only_index=self._job_item_index_for(materials_assumption, job_items)`.
- When the returned names list is non-empty, return a clarification: "Which line should I swap: {a}, {b}…?". Use `_crud_envelope(..., needs_clarification=True)` as the `swapped == 0` branch at line 445 does, and persist nothing.

Run the two new tests plus the whole `TestMaterialAssumptionSwap` class. Expected: PASS. If `test_swaps_matching_lines_and_reprices` relied on multi-line swapping, update its assertion to the single best line and name #6 in a comment.

- [ ] **Step 4: Failing tests for #23**

In `tests/test_estimate_calculations_gross_margin.py`:

```python
def test_legacy_labours_are_not_priced_matching_the_portal():
    item = _item(materials=[_mat(1, 100)], activities=[_act(10, 60, cost_rate=60)],
                 labours=[_lab(5, 40)], profit_margin=20)
    assert work_item_breakdown(item).total == pytest.approx(840.0)

def test_margin_readout_ignores_a_stored_burden():
    item = _item(materials=[_mat(1, 100)], activities=[_act(10, 60, cost_rate=50)],
                 profit_margin=20, labor_burden=25)
    assert work_item_gross_margin(item).gross_margin_pct == pytest.approx(
        work_item_gross_margin(_item(materials=[_mat(1, 100)], activities=[_act(10, 60, cost_rate=50)], profit_margin=20)).gross_margin_pct)
```
Use the file's existing item and line builders. If the names differ (`_item`, `_mat`, `_act`, `_lab`), use what the file defines.

Run. Expected: FAIL ($1,080; 36.27 vs 40.48).

- [ ] **Step 5: Implement #23**

In `calculations.py`:
- `_labour_lines(item)` (~line 187) yields activities only. Drop the `labours` loop, with the comment `# legacy labours are not priced: the portal never reads them and saves send [] (sixth pass #23)`.
- `work_item_breakdown` and `work_item_gross_margin` compute on `_unburdened(item)`, defined as:

```python
def _unburdened(item: Any) -> Any:
    """``item`` with burden 0 — the portal prices at burden 0."""
    if not float(getattr(item, "labor_burden", 0) or 0):
        return item
    clone = copy.copy(item)
    clone.labor_burden = 0.0
    return clone
```

Then:
- delete the now-redundant copy in `_recalculate_sub_total` (`work_item_field_handlers.py:114-128`);
- remove the comment at `calculations.py:246-248` that says legacy labours are billed.

Run the whole `test_estimate_calculations_gross_margin.py` plus `tests/test_estimate_edit_executor.py` and `tests/test_estimate_assumption_adjustment.py`. Expected: PASS. Update any test that asserted legacy labours in a total, citing #23.

- [ ] **Step 6: Check portal parity**

Open `portal/tests/estimateCalculations.test.ts` and confirm the portal has no case that counts `labours`. The portal is unchanged, so parity holds. Record `Task 2: portal parity checked, no portal change` in the ledger.

- [ ] **Step 7: Gates**

Run mypy and ruff on `agents/estimate routers/estimate_helpers`, then the tests above plus `tests/test_maple_routing_snapshot.py`. Expected: clean, all pass, and the snapshot is unchanged.

---

### Task 3: Delete, audit and log hygiene (#26, #27, #29, #30, #653)

**Files:**
- Modify: `platform/routers/agents.py:902-907,1175-1182`
- Modify: `platform/routers/agent_helpers/fuzzy_confirmation.py`, `platform/services/estimate_delete.py:33-40`
- Modify: `platform/agents/estimate/edit_executor.py:623-632`, `platform/agents/estimate/work_item_handlers.py:960-968`
- Modify: `platform/routers/agent_helpers/active_estimate.py:152-158`, `platform/routers/agent_helpers/finalize_result.py:139-142`
- Modify: `platform/agents/estimate/work_item_field_handlers.py` (lines 568, 594, 741, 768, 893), `platform/agents/estimate/work_item_handlers.py` (910, 1121, 1140)
- Test: `tests/test_agent_helpers_fuzzy_confirmation.py`, `tests/test_orchestrator_endpoint.py`, `tests/test_estimate_edit_executor.py`, `tests/test_maple_work_item_ops.py`, `tests/test_agent_helpers_active_estimate.py`

**Interfaces:**
- Produces: `handle_estimate_fuzzy_confirmation(..., schedule: Optional[Scheduler] = None)`.
- Produces: `EstimateAgent._command(cls, query, context, **fields) -> Tuple[Optional[EditCommand], Optional[Dict]]`.

- [ ] **Step 1: Back up** (`t3`).

- [ ] **Step 2: Failing tests for #26 and #27**

In `tests/test_agent_helpers_fuzzy_confirmation.py`, extend `test_an_owner_delete_cascades_notes_and_is_audited`:
- pass `schedule=scheduled.append` and assert `len(scheduled) >= 2`, so the cleanups were deferred rather than run inline;
- assert the audit call's `user_id == "uid-1"` with `context_payload["user_id"] = "uid-1"`.

Add:

```python
def test_owner_role_matches_case_insensitively():
    assert may_delete_estimate(SimpleNamespace(created_by_email="a@x.com"), "b@x.com", "owner")
```
Run. Expected: FAIL.

- [ ] **Step 3: Implement #26 and #27**

- In `may_delete_estimate`, change to `role_value.strip().lower() == UserRole.OWNER.value.lower()`.
- Give `handle_estimate_fuzzy_confirmation` and `_dispatch_confirmed_intent` a keyword `schedule: Optional[Scheduler] = None`. Pass it to `delete_estimate_and_cascade(target, schedule=schedule)`, and pass `user_id=str(context_payload.get("user_id") or "") or None` to `create_audit_log`.
- In `routers/agents.py`, add `background_tasks: BackgroundTasks` to `orchestrate_agent_endpoint`'s parameters (import from `fastapi`), and pass `schedule=background_tasks.add_task` at the fuzzy call (~1175).
- Update the test wrapper `orchestrate_agent_endpoint` in `tests/test_orchestrator_endpoint.py:93` so it supplies `background_tasks=BackgroundTasks()` when the caller doesn't.

Run the fuzzy and endpoint tests. Expected: PASS.

- [ ] **Step 4: Failing tests for #29 (company defaults unavailable)**

In `tests/test_estimate_edit_executor.py`, monkeypatch `agents.estimate.edit_executor.get_company_defaults` to raise `RuntimeError("db down")`. Run an `AddWorkItem` batch and assert that the response contains "couldn't read your default markup". Add the same assertion to `tests/test_estimate_agent.py::test_estimates_work_item_add_survives_a_company_defaults_failure`.

Run. Expected: FAIL.

- [ ] **Step 5: Implement #29**

- Add a module constant in `edit_executor.py`:
  ```python
  DEFAULTS_UNAVAILABLE_LINE = "I couldn't read your default markup, overhead and tax, so they're 0% on this work item — set them on the item."
  ```
- In the except branch at 628-630, keep the warning and add `batch.lines.append(DEFAULTS_UNAVAILABLE_LINE)`. Use whatever line list `_edit_add_work_item` appends to.
- Do the same in `work_item_handlers.py:960-968`. There, also replace `logger.exception(...)` with `logger.warning("work item add: company defaults lookup failed (%s)", type(err).__name__)` (the no-exc_info rule at `crud_handlers.py:850`) and bind `except Exception as err:`.

Run. Expected: PASS.

- [ ] **Step 6: #30 (log the exception type)**

This is a log-only change, so no TDD. Bind `except Exception as err:` in `active_estimate.py:155` and `finalize_result.py:141`. Include `type(err).__name__` in each message, for example `logger.warning("Viewed-estimate lookup failed (%s); keeping the current anchor", type(err).__name__)`. Do not add `exc_info`, per the Sentry frame-locals rule.

- [ ] **Step 7: Failing tests for #653 (validation errors escape the agent)**

In `tests/test_maple_work_item_ops.py`:

```python
@pytest.mark.parametrize("query", [
    "add 2000000 bags of mulch to work item 1",
    "set the total on work item 1 to $500000000",
    "add an activity Grading 200000 hours to work item 1",
])
def test_out_of_range_values_are_explained_not_raised(query):
    result = _run_update(query)   # the file's existing helper for a fake estimate
    assert result["needs_clarification"] is True
```
Run. Expected: FAIL with `ValidationError`.

- [ ] **Step 8: Implement #653**

Add to `EditExecutorMixin` in `edit_executor.py`:

```python
def _command(self, cls: Any, query: str, context: Dict[str, Any], **fields: Any) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """Build an EditCommand, or a clarification when a value is out of
    range (#653) — never let ValidationError escape ``process``."""
    try:
        return cls(**fields), None
    except ValidationError as err:
        problem = err.errors()[0] if err.errors() else {}
        field = ".".join(str(p) for p in problem.get("loc", ())) or "value"
        return None, self._crud_envelope(
            query=query, intent="update_estimate", probability=1.0,
            response=f"That {humanize_field_name(field)} is out of range: {problem.get('msg', 'invalid value')}.",
            needs_clarification=True, context=context,
        )
```
Match `_crud_envelope`'s real keyword names from `crud_helpers.py:618`.

Replace each direct construction at `work_item_field_handlers.py` 568, 594, 741, 768, 893 and `work_item_handlers.py` 910, 1121, 1140 with `cmd, err = self._command(Cls, query, context, …)` followed by `if err: return err`.

Run the new tests plus `tests/test_maple_work_item_ops.py`. Expected: PASS.

- [ ] **Step 9: Gates**

Run mypy and ruff on `routers agents/estimate services`, then all test files named in this task plus the snapshot. Run `./run_bandit.sh routers agents/estimate services`. Expected: clean; bandit still reports 11 B110 over the full project.

---

### Task 4: Portal work-item saves merge by id (#1, #11, #12, #24)

**Files:**
- Modify: `portal/src/lib/workItemV2.ts` (add `WorkItemChange`, `applyWorkItemChange`)
- Modify: `portal/src/api/estimates.ts:33-43` (`base_version?: number`)
- Modify: `portal/src/pages/NewEstimateWithActivityPage.tsx:841-863,1117-1140,1174-1195,1217-1224,1226-1279`
- Test: `portal/tests/workItemChange.test.ts` (new), `portal/tests/NewEstimateWithActivityPage.workItemSave.test.tsx` (new; copy the mocks block from `tests/NewEstimateWithActivityPage.mapleWrites.test.tsx:26-222`)

**Interfaces:**
- Produces:
  ```ts
  export type WorkItemChange = { kind: "upsert"; item: WorkItemV2 } | { kind: "remove"; id: string };
  export function applyWorkItemChange(serverItems: EstimateJobItem[], change: WorkItemChange, localRaw?: EstimateJobItem): WorkItemV2JobItemPayload[]
  ```
  The page's `persistWorkItemChange(change, localRaw?) => Promise<boolean>` replaces `persistWorkItems`.

- [ ] **Step 1: Back up** (`t4`).

- [ ] **Step 2: Failing unit tests**

`portal/tests/workItemChange.test.ts`:

```ts
import { describe, expect, test } from "vitest";
import { applyWorkItemChange, jobItemToWorkItemV2 } from "../src/lib/workItemV2";

const raw = (id: string, extra: Record<string, unknown> = {}) =>
  ({ id, description: id, division: "Unassigned", materials: [], activities: [], ...extra }) as never;

describe("applyWorkItemChange", () => {
  test("keeps an item Maple added while the dialog was open (#1)", () => {
    const server = [raw("w1"), raw("w2"), raw("w3")];
    const edited = { ...jobItemToWorkItemV2(raw("w1")), description: "Edited" };
    const out = applyWorkItemChange(server, { kind: "upsert", item: edited });
    expect(out.map((p) => p.id)).toEqual(["w1", "w2", "w3"]);
    expect(out[0].description).toBe("Edited");
  });

  test("removes by id and keeps each item's own gaps (#12)", () => {
    const server = [raw("w1", { unmatched_materials: [{ name: "Gap stone" }] }), raw("w2")];
    const out = applyWorkItemChange(server, { kind: "remove", id: "w1" });
    expect(out.map((p) => p.id)).toEqual(["w2"]);
    expect(out[0].unmatched_materials ?? []).toEqual([]);
  });

  test("appends a new item", () => {
    const item = { ...jobItemToWorkItemV2(raw("new")), id: "new" };
    expect(applyWorkItemChange([raw("w1")], { kind: "upsert", item }).map((p) => p.id)).toEqual(["w1", "new"]);
  });

  test("takes the changed item's gaps from the local copy (a dismissal survives)", () => {
    const server = [raw("w1", { unmatched_materials: [{ name: "A" }, { name: "B" }] })];
    const local = raw("w1", { unmatched_materials: [{ name: "B" }] });
    const out = applyWorkItemChange(server, { kind: "upsert", item: jobItemToWorkItemV2(local) }, local);
    expect(out[0].unmatched_materials).toEqual([{ name: "B" }]);
  });
});
```
Run: `cd portal && npm test -- workItemChange`. Expected: FAIL (the function isn't exported).

- [ ] **Step 3: Implement `applyWorkItemChange`**

Append to `src/lib/workItemV2.ts`:

```ts
/** One work-item edit, applied to the server's latest list by id — never a
 *  whole-array save from a possibly stale copy (sixth pass #1, #12). */
export type WorkItemChange = { kind: "upsert"; item: WorkItemV2 } | { kind: "remove"; id: string };

export function applyWorkItemChange(
  serverItems: EstimateJobItem[],
  change: WorkItemChange,
  localRaw?: EstimateJobItem,
): WorkItemV2JobItemPayload[] {
  const payloads = serverItems.map((raw) => workItemV2ToJobItemPayload(jobItemToWorkItemV2(raw), raw));
  if (change.kind === "remove") {
    return payloads.filter((_, i) => serverItems[i].id !== change.id);
  }
  const idx = serverItems.findIndex((raw) => raw.id === change.item.id);
  const payload = workItemV2ToJobItemPayload(change.item, localRaw ?? (idx >= 0 ? serverItems[idx] : undefined));
  if (idx < 0) return [...payloads, payload];
  payloads[idx] = payload;
  return payloads;
}
```
Add `base_version?: number;` to `UpdateEstimatePayload` in `src/api/estimates.ts`.

Run. Expected: PASS.

- [ ] **Step 4: Failing page tests**

Create `portal/tests/NewEstimateWithActivityPage.workItemSave.test.tsx`:
- Copy the imports, `vi.mock` block, stubs and helpers (`makeEstimate`, `renderEditMode`, `deferred`, `mapleChanged`) from `tests/NewEstimateWithActivityPage.mapleWrites.test.tsx:1-222`.
- Add `const { isConflictError } = …` only if needed.

Tests:
- **#1:**
  1. `getMock` returns `makeEstimate()` with w1 and w2 first.
  2. Open work item 1 for editing through the dialog stub. Use the same button the mapleWrites fourth-pass #13 test uses.
  3. Set `getMock` to return an estimate with w1, w2 and w3 and `version: 7`.
  4. Click `work-item-save`.
  5. Assert that `updateMock` was called with `job_items.map(j => j.id)` equal to `["w1","w2","w3"]` and `base_version: 7`.
- **#1 conflict retry:** `updateMock` rejects once with `new ApiError("Conflict", 409, "conflict", { code: "conflict", current_version: 8 })`, then resolves. Assert that `getMock` was called again and `updateMock` twice, and that no error banner appears.
- **#11:**
  1. Render.
  2. Call the dialog stub's `onDismissGap`. Extend the `WorkItemDialog` stub to render a `data-testid="dismiss-gap"` button that calls `onDismissGap({ workItemIndex: 0, kind: "material", gapIndex: 0 })`, matching the prop shape at page line 841.
  3. Then `mapleChanged({ operation: "update_estimate", estimate_id: "E0042" })`.
  4. Assert that `getMock` was called again (the reload was not blocked) and that `updateMock` was called once for the dismissal.
- **#24:** `updateMock` rejects with `new Error("server down")` on delete. Assert that the row "Install pavers" is still rendered, the text "server down" appears, and there is no unhandled rejection. Use Vitest's `onUnhandledRejection` spy on `process`.

Run: `npm test -- NewEstimateWithActivityPage.workItemSave`. Expected: FAIL.

- [ ] **Step 5: Implement on the page**

Replace `persistWorkItems` (1117-1140) with:

```ts
/** Apply one work-item change to the server's latest copy, by id, with the
 *  version it was read at; one retry on a version conflict. Resolves false
 *  when the user has moved to another estimate (sixth pass #1). */
const persistWorkItemChange = async (change: WorkItemChange, localRaw?: EstimateJobItem): Promise<boolean> => {
  if (!isEditMode || !estimateId) {
    setIsDirty(true);
    return true;
  }
  if (!isLoadedForWrite()) throw new Error("This estimate hasn't loaded, so nothing was saved.");
  const writes = writesRef.current;
  const attempt = async () => {
    const latest = (await estimatesApi.get(estimateId)) as EstimateWithExtras;
    return estimatesApi.update(estimateId, {
      job_items: applyWorkItemChange(latest.job_items || [], change, localRaw),
      base_version: latest.version,
    }) as Promise<EstimateWithExtras>;
  };
  let updated: EstimateWithExtras;
  try {
    updated = await trackWrite(attempt);
  } catch (err) {
    if (!isConflict(err) || !isCurrentEstimate(writes)) throw err;
    updated = await trackWrite(attempt);
  }
  if (!isCurrentEstimate(writes)) return false;
  setEstimate(updated);
  setWorkItems((updated.job_items || []).map(jobItemToWorkItemV2));
  return true;
};
```
- Import `isConflict` from `../lib/conflict`, and `applyWorkItemChange`, `WorkItemChange` from `../lib/workItemV2`.
- **Create mode.** Keep the old behavior there: `setIsDirty(true)` and no network call. `saveWorkItemDialog` still computes `nextWorkItems` for create mode.
- **`saveWorkItemDialog`:**
  - In edit mode, call `persistWorkItemChange({ kind: "upsert", item: draft }, rawById.get(draft.id))`, where `rawById = new Map((estimate?.job_items || []).map((r) => [r.id, r]))`.
  - Stop calling `setWorkItems(next)` after a successful edit-mode save; `persistWorkItemChange` sets the list from the server.
  - In create mode, keep `setWorkItems(nextWorkItems)`.
- **`handleConfirmDeleteWorkItem`:**

```ts
const handleConfirmDeleteWorkItem = async () => {
  if (deletingWorkItemIndex === null) return;
  const previous = workItems;
  const removed = previous[deletingWorkItemIndex];
  const writes = writesRef.current;
  setWorkItems(previous.filter((_, i) => i !== deletingWorkItemIndex));
  setDeletingWorkItemIndex(null);
  try {
    await persistWorkItemChange({ kind: "remove", id: removed.id });
  } catch (err) {
    if (!isCurrentEstimate(writes)) return;
    setWorkItems(previous);
    setSaveError(err instanceof Error ? err.message : "Failed to delete the work item.");
  }
};
```
- **`handleDismissGap`:** build the updated raw item from `estimate` exactly as today and `setEstimate` it. Instead of `setIsDirty(true)`, call:
  ```ts
  void persistWorkItemChange({ kind: "upsert", item: workItems[gap.workItemIndex] }, updatedRaw).catch((err) => setSaveError(err instanceof Error ? err.message : "Failed to save."))
  ```
  Add `workItems` to its `useCallback` dependencies, together with the functions it uses.
- **`handleSaveEstimate` (1233-1236):** replace `rawJobItems[idx]` with `rawById.get(wi.id)` (#12).
- **Modal copy (~1826):** change the confirm text "You'll still need to save the estimate for this change to take effect" to "This removes the work item from the estimate." (the delete saves immediately).

Run the new page test, `npm test -- NewEstimateWithActivityPage`, and `npm test -- workItemChange`. Expected: PASS. Update any mapleWrites assertion that expected a whole-array payload without a GET first, and cite #1 in the comment.

- [ ] **Step 6: Gates**

`npm run typecheck && npm run lint`. Expected: clean.

---

### Task 5: Portal page lifecycle (#25, #28, #31, #32)

**Files:**
- Modify: `portal/src/pages/NewEstimateWithActivityPage.tsx:498-526,573-604,1046-1069,1289-1304`
- Test: `portal/tests/NewEstimateWithActivityPage.workItemSave.test.tsx` (append)

- [ ] **Step 1: Back up** (`t5`).

- [ ] **Step 2: Failing tests**

Append to the Task 4 test file:
- **#25:** `mapleChanged({ operation: "delete_estimate", estimate_id: "est-1" })`. Assert `navigateMock` was called with `"/estimates"`. Also assert that a `portal:estimate:unloaded` listener got `{ id: "est-1" }`. Do the same with `estimate_id: "E0042"` when the loaded estimate code is E0042. A different id must not navigate.
- **#28:**
  1. Autosave the description to X (update deferred, rejected later) and then to Y (update resolves).
  2. Reject the X update.
  3. Then `mapleChanged(update)`.
  4. Assert that `getMock` is called again. The reload was not left deferred, because the stale rollback didn't run.
- **#31:** make a save fail on est-1 so "Failed to save." shows. Click `go-b`. Assert that "Failed to save." is gone.
- **#32:** fail the first load. Assert that `document.activeElement` is the Retry button, and that a link named "Back to Estimates" exists and navigates to `/estimates`.

Run. Expected: FAIL.

- [ ] **Step 3: Implement**

- **Mutation handler (573-604):** compute `isThisEstimate` before any early return, and include `detail.estimate_id === estimateId` (Maple's delete result carries the Mongo id). Then:

```ts
if (detail.operation === "delete_estimate") {
  if (isThisEstimate) {
    window.dispatchEvent(new CustomEvent(ESTIMATE_UNLOADED_EVENT, { detail: { id: estimateId } }));
    navigate("/estimates", { replace: true });
  }
  return;
}
```
Add `navigate` to the effect's dependencies.

- **`autoSaveField`:** pass `rollback ? () => { if (guard.isLatest(seq)) rollback(); } : undefined` to `trackWrite`.
- **Reset effect (498-526):** add `setSaveError(""); setFormError(""); setWorkItemDialogError("");`.
- **Retry screen:**
  - Add `const retryButtonRef = useRef<HTMLButtonElement>(null);` and `useEffect(() => { if (loadError) retryButtonRef.current?.focus(); }, [loadError]);`. Place both with the other hooks, before any early return.
  - Put `ref={retryButtonRef}` on the button.
  - After it, add a second button: `<button type="button" onClick={() => navigate("/estimates")} className="mt-2 ml-2 px-3 py-1.5 rounded-md border border-red-300 bg-white text-red-700 hover:bg-red-100">Back to Estimates</button>`.
  - Check the test's accessible-name query against it.

Run the page tests plus `tests/NewEstimateWithActivityRetry.test.tsx` and `mapleWrites`. Expected: PASS.

- [ ] **Step 4: Gates**

`npm run typecheck && npm run lint`. Expected: clean.

---

### Task 6: The written command list (not yet wired)

**Files:**
- Create: `platform/agents/estimate/command_grammar.py`
- Create: `platform/tests/test_command_grammar.py`
- Create: `platform/tests/maple_routing/snapshot_grammar.json` (recorded)
- Modify: `platform/tests/test_maple_routing_snapshot.py` (grammar layer)
- Modify: `platform/tests/maple_routing/expected.json` (remove `task` from task-6 rows)

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class ListedCommand:
      id: str
      slots: Dict[str, str]
      ref_form: str        # "code" | "title" | "ordinal" | "number" | "label" | "pronoun" | "this" | "none"
      ported: bool = False
  def match_command(text: str, agent: Any = None) -> Optional[ListedCommand]
  CORE_IDS: FrozenSet[str]; PORTED_IDS: FrozenSet[str]; READ_IDS: FrozenSet[str]; UPDATE_COMMAND_IDS: FrozenSet[str]
  def normalize(text: str) -> str
  ```
  With `agent=None`, only core entries are tried. With an `EstimateAgent`, ported entries are tried after core.

- [ ] **Step 1: Back up** (`t6`).

- [ ] **Step 2: Failing tests**

`tests/test_command_grammar.py`. Every example comes from the spec §4.2/§4.3 tables:

```python
import time

import pytest

from agents.estimate.command_grammar import match_command

ACCEPT = [
    ("show me my estimates", "list_estimates", "none"),
    ("list the estimates for Bob Smith", "list_estimates", "none"),
    ("can you show me my estimates", "list_estimates", "none"),
    ("never mind, show my estimates", "list_estimates", "none"),
    ("how many estimates do I have?", "list_estimates", "none"),
    ("open E0042", "get_estimate", "code"),
    ("show me this estimate", "get_estimate", "this"),
    ("open the Jones backyard estimate please", "get_estimate", "title"),
    ("show me the estimate for the Smith property", "get_estimate", "title"),
    ("show the work items on E0042", "list_work_items", "code"),
    ("show work item 2", "get_work_item", "number"),
    ("open the patio work item", "get_work_item", "label"),
    ("create an estimate for sod at 12 Oak St", "create_estimate", "none"),
    ("rename this estimate to Spring Cleanup", "rename_estimate", "this"),
    ("add a work item called Fence to E0042", "add_work_item", "code"),
    ("add a work item called Equipment staging", "add_work_item", "none"),
    ("delete work item 2", "remove_work_item", "number"),
    ("remove the second work item", "remove_work_item", "ordinal"),
    ("delete it", "remove_pronoun", "pronoun"),
    ("remove it", "remove_pronoun", "pronoun"),
    ("rename work item 2 to Back Fence", "rename_work_item", "number"),
    ("set the markup on work item 2 to 20%", "set_percentage", "number"),
    ("set the markup to 20%", "set_percentage", "none"),
    ("change the markup to 25 percent", "set_percentage", "none"),
    ("set the tax to 13 %", "set_percentage", "none"),
    ("make the gross margin 30%", "set_gross_margin", "none"),
    ("set the total on work item 1 to $1,000", "set_total", "number"),
    ("hey, add a note to work item 2: check drainage", "add_note", "number"),
    ("yes, add a note to work item 2: check drainage", "add_note", "number"),
    ("great, now add a note to work item 2: check drainage", "add_note", "number"),
    ("add a note to this estimate saying call first", "add_note", "this"),
    ("perfect, add a note to the back patio work item saying check drainage", "add_note", "label"),
    ("add a note to work item #2: check drainage", "add_note", "number"),
    ("what’s up — show me my estimates", None, None),
]

REJECT = [
    "anything open for Bob?", "what's going on with Jones?", "what's in there?",
    "the patio one", "hey, add a fence", "call it Spring Cleanup", "add a fence",
    "get rid of the fence stuff", "call the second one Back Fence", "bump the markup a bit",
    "I want 30% profit", "make it an even thousand", "jot down a note for John Doe: call after 5",
    "add a note to concrete blocks: supplier changed", "Remove all debris and haul away",
    "Show homeowner the revised quote before starting", "set the hours on grading to 2 days",
    "quick note on work item 2: check drainage", "change the cost of Landscaper to $50",
]

@pytest.mark.parametrize("text,command_id,ref_form", [a for a in ACCEPT if a[1]])
def test_accepts(text, command_id, ref_form):
    found = match_command(text)
    assert found is not None and found.id == command_id
    assert found.ref_form == ref_form

@pytest.mark.parametrize("text", REJECT + [a[0] for a in ACCEPT if a[1] is None])
def test_rejects(text):
    assert match_command(text) is None

def test_note_body_and_target_slots():
    found = match_command("add a note to work item 2: check drainage")
    assert found.slots == {"target": "work item 2", "work_item_number": "2", "body": "check drainage"}

def test_note_without_body_is_the_prompt_form():
    found = match_command("add a note to work item 2")
    assert found.id == "add_note" and found.slots.get("body", "") == ""

@pytest.mark.parametrize("text,command_id", [
    ("set  the  markup  to  20%", "set_percentage"),
    ("set the markup to 20% please", "set_percentage"),
    ("set the markup to 20 %", "set_percentage"),
    ("rename work item #2 to Back Fence", "rename_work_item"),
    ("open the O’Brien backyard estimate", "get_estimate"),
])
def test_typographic_variants_match(text, command_id):
    found = match_command(text)
    assert found is not None and found.id == command_id

@pytest.mark.parametrize("text", [
    "add a note to work item 2: " + "x " * 985,          # just under the 2,000-char cap
    "show me " + "the " * 495 + "estimate",
    "set the " + "markup " * 280 + "to 20%",
    "add a work item called " + "a " * 985,
])
def test_long_input_is_fast(text):
    assert len(text) < 2000
    start = time.perf_counter()
    match_command(text)
    assert time.perf_counter() - start < 0.05
```
Run: `./run_tests.sh tests/test_command_grammar.py -q`. Expected: FAIL (import error).

- [ ] **Step 3: Implement the core entries**

`agents/estimate/command_grammar.py`:

```python
"""The written list of estimate phrasings Maple handles by rule.

Design: documentation/development/plans/2026-09-25-maple-routing-convergence-design.md §4.
A rule that isn't in this module doesn't exist — a phrasing no entry accepts
goes to the edit planner (edits) or the LLM classifier (routing). To support a
new phrasing, add an entry here, a row in the phrasing reference's rule table
and accept/reject examples in tests/test_command_grammar.py; never a regex
elsewhere (design §10).

Core entries are new anchored patterns: an optional lead from a closed list,
the command, an optional courtesy tail, end of text. Ported entries wrap
detectors that have no planner equivalent, unchanged (design §4.3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Pattern, Tuple

__all__ = [
    "ListedCommand", "match_command", "normalize",
    "CORE_IDS", "PORTED_IDS", "READ_IDS", "UPDATE_COMMAND_IDS",
]

_MAX_LEN = 2000


@dataclass(frozen=True)
class ListedCommand:
    """A matched entry: its id, its parsed slots, and how it named its target."""

    id: str
    slots: Dict[str, str] = field(default_factory=dict)
    ref_form: str = "none"
    ported: bool = False


def normalize(text: str) -> str:
    """Straight quotes, single spaces, trimmed — so typographic variants match
    the same entry as the plain form."""
    text = (text or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


_LEADS = (
    r"hey|hi|ok|okay|yes|great|perfect|thanks|please|now|also|and|actually|"
    r"never\s+mind|one\s+more\s+thing|quick|can\s+you|could\s+you"
)
_LEAD = rf"^(?:(?:{_LEADS})[,!.]?\s+){{0,2}}"
_TAIL = r"(?:,?\s+(?:please|thanks|thank\s+you))?\s*[.!?]?$"

_CODE = r"[Ee]-?\d{4,7}"
_EST_NOUN = r"(?:estimate|quote|bid|proposal)"
_WORD = r"[\w&'#.-]+"
_ORDINALS = r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last"

_EST_REF = (
    rf"(?:(?P<est_code>{_CODE})"
    rf"|(?P<est_this>(?:this|the|current|my)\s+{_EST_NOUN})"
    rf"|the\s+{_EST_NOUN}\s+(?:for|called|named)\s+(?P<est_title_after>{_WORD}(?:\s+{_WORD}){{0,6}})"
    rf"|the\s+(?P<est_title>{_WORD}(?:\s+{_WORD}){{0,4}})\s+(?:{_EST_NOUN}|job))"
)
_WI_NAMED = (
    rf"(?:work\s+item\s*#?\s*(?P<wi_number>\d{{1,3}})"
    rf"|the\s+(?P<wi_ordinal>{_ORDINALS})\s+work\s+item"
    rf"|the\s+(?P<wi_label>{_WORD}(?:\s+{_WORD}){{0,4}})\s+work\s+item)"
)
_ON_WI = rf"(?:\s+(?:on|for)\s+{_WI_NAMED})?"
_PCT = r"(?P<value>-?\d+(?:\.\d+)?)\s*(?:%|percent)"
_MONEY = r"\$\s?(?P<amount>\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)"
_NOTE_TARGET = (
    rf"(?:(?P<est_code>{_CODE})|(?P<est_this>(?:this|the)\s+{_EST_NOUN})"
    rf"|work\s+item\s*#?\s*(?P<wi_number>\d{{1,3}})"
    rf"|the\s+(?P<wi_ordinal>{_ORDINALS})\s+work\s+item"
    rf"|the\s+(?P<wi_label>{_WORD}(?:\s+{_WORD}){{0,4}})\s+work\s+item"
    rf"|(?P<pronoun>it|this))"
)


def _core(pattern: str) -> Pattern[str]:
    return re.compile(_LEAD + pattern + _TAIL, re.IGNORECASE)


# (id, compiled pattern). Order matters only where two could match; the more
# specific entry comes first.
_CORE: List[Tuple[str, Pattern[str]]] = [
    ("create_estimate", _core(rf"(?:create|start|make|build|new)(?:\s+(?:a|an))?(?:\s+new)?\s+{_EST_NOUN}\s+(?:for|to)\s+(?P<scope>.+?)")),
    ("list_estimates", _core(r"(?:how\s+many\s+(?:estimates|quotes|bids|proposals)\b.*|(?:list|show|see|view)(?:\s+me)?(?:\s+(?:all|my|the))*\s+(?:estimates|quotes|bids|proposals)(?:\s+for\s+(?P<name>.+?))?)")),
    ("list_work_items", _core(rf"(?:list|show)(?:\s+me)?(?:\s+the)?\s+work\s+items(?:\s+(?:on|for|in)\s+{_EST_REF})?")),
    ("get_work_item", _core(rf"(?:show|open)(?:\s+me)?\s+{_WI_NAMED}")),
    ("get_estimate", _core(rf"(?:show|open|view|get|pull\s+up)(?:\s+me)?\s+{_EST_REF}")),
    ("rename_estimate", _core(rf"rename\s+{_EST_REF}\s+to\s+(?P<title>.+?)")),
    ("rename_work_item", _core(rf"rename\s+{_WI_NAMED}\s+to\s+(?P<name>.+?)")),
    ("add_work_item", _core(rf"add(?:\s+(?:a|another))?(?:\s+new)?\s+work\s+item\s+(?:called|named)\s+(?P<name>.+?)(?:\s+(?:to|on)\s+{_EST_REF})?")),
    ("remove_work_item", _core(rf"(?:remove|delete)\s+{_WI_NAMED}")),
    ("remove_pronoun", _core(r"(?:remove|delete)\s+(?P<pronoun>it|that\s+one)")),
    ("set_gross_margin", _core(rf"(?:set|change|make|update)\s+(?:the\s+)?gross\s+margin{_ON_WI}(?:\s+(?:to|at))?\s+{_PCT}")),
    ("set_percentage", _core(rf"(?:set|change|make|update)\s+(?:the\s+)?(?P<field>markup|overhead|tax){_ON_WI}(?:\s+(?:to|at))?\s+{_PCT}")),
    ("set_total", _core(rf"(?:set|change|make|update)\s+(?:the\s+)?(?:work\s+item\s+)?total{_ON_WI}(?:\s+(?:to|at))?\s+{_MONEY}")),
    ("add_note", _core(rf"(?:add|leave|put|write)\s+(?:a\s+)?note\s+(?:to|on|for)\s+(?P<target>{_NOTE_TARGET})(?:\s*:\s*|\s+saying\s+|\s+that\s+)(?P<body>.+?)")),
    ("add_note", _core(rf"(?:add|leave|put|write)\s+(?:a\s+)?note\s+(?:to|on|for)\s+(?P<target>{_NOTE_TARGET})")),
]

READ_IDS: FrozenSet[str] = frozenset({"list_estimates", "get_estimate", "list_work_items", "get_work_item"})
CORE_IDS: FrozenSet[str] = frozenset(cid for cid, _ in _CORE)


def _ref_form(groups: Dict[str, Optional[str]]) -> str:
    if groups.get("est_code"):
        return "code"
    if groups.get("est_title") or groups.get("est_title_after"):
        return "title"
    if groups.get("wi_number"):
        return "number"
    if groups.get("wi_ordinal"):
        return "ordinal"
    if groups.get("wi_label"):
        return "label"
    if groups.get("pronoun"):
        return "pronoun"
    if groups.get("est_this"):
        return "this"
    return "none"


def _slots(groups: Dict[str, Optional[str]]) -> Dict[str, str]:
    renamed = {"wi_number": "work_item_number", "wi_ordinal": "work_item_ordinal", "wi_label": "work_item_label",
               "est_code": "estimate_code", "est_title": "estimate_title", "est_title_after": "estimate_title"}
    out: Dict[str, str] = {}
    for key, value in groups.items():
        if value and key not in ("est_this", "pronoun"):
            out[renamed.get(key, key)] = value.strip()
    return out


# Ported entries: (id, detector). A detector takes (agent, text) and returns
# a truthy value when its existing rule accepts the text.
_PortedDetector = Callable[[Any, str], Any]


def _work_item_op_in(ops: FrozenSet[str]) -> _PortedDetector:
    def detect(agent: Any, text: str) -> bool:
        found = agent._detect_work_item_op(text)
        return bool(found) and str(found.get("op", "")) in ops
    return detect


def _ported() -> List[Tuple[str, _PortedDetector]]:
    from agents.estimate.assumption_handlers import detect_assumption_adjustment
    from agents.estimate.text_helpers import parse_status_transition
    from agents.estimate.work_item_edit_detectors import _detect_generate

    return [
        ("set_status", lambda _agent, text: parse_status_transition(text)),
        ("set_estimate_description", lambda agent, text: agent._detect_estimate_description_update(text)),
        ("generate_work_item", lambda _agent, text: _detect_generate(text)),
        ("set_recurring", _work_item_op_in(frozenset({"recurring_enable", "recurring_disable", "recurring_query"}))),
        ("list_work_item_lines", _work_item_op_in(frozenset({"list_materials", "list_activities"}))),
        ("query_work_item_field", _work_item_op_in(frozenset({"query"}))),
        ("adjust_assumption", lambda _agent, text: detect_assumption_adjustment(text)),
        ("apply_template", lambda agent, text: agent._detect_template_application(text)),
        ("link_property", lambda agent, text: agent._is_property_link_request(text)),
    ]


PORTED_IDS: FrozenSet[str] = frozenset({
    "set_status", "set_estimate_description", "generate_work_item", "set_recurring",
    "list_work_item_lines", "query_work_item_field", "adjust_assumption", "apply_template", "link_property",
})
UPDATE_COMMAND_IDS: FrozenSet[str] = (CORE_IDS | PORTED_IDS) - READ_IDS - {"create_estimate"}


def match_command(text: str, agent: Any = None) -> Optional[ListedCommand]:
    """The listed command ``text`` is, or None. Core entries only unless an
    Estimate Agent is passed, in which case ported entries are tried next."""
    clean = normalize(text)
    if not clean or len(clean) > _MAX_LEN:
        return None
    for command_id, pattern in _CORE:
        found = pattern.match(clean)
        if found:
            groups = found.groupdict()
            return ListedCommand(id=command_id, slots=_slots(groups), ref_form=_ref_form(groups))
    if agent is None:
        return None
    for command_id, detect in _ported():
        if detect(agent, clean):
            return ListedCommand(id=command_id, ported=True)
    return None
```

The note slots test expects `target`, so keep `target` as a named group. Run the tests and adjust the patterns until every ACCEPT/REJECT case passes. Two rules for those adjustments:
- **Never loosen a REJECT case to make an ACCEPT pass.** A conflict between the two is a spec question. Record `Task 6: Ruling:` in the ledger with the phrasing and the side you chose.
- **If a ported detector's real signature differs** from the lambda (for example, it needs `context`), wrap it to pass `None`, and record a ledger ruling.

Also add a test for the ported entries:

```python
def test_ported_entries_need_the_agent():
    from agents.estimate.service import EstimateAgent
    agent = EstimateAgent()
    assert match_command("mark E0042 as sent") is None or match_command("mark E0042 as sent").id != "set_status"
    assert match_command("mark E0042 as sent", agent).id == "set_status"
    assert match_command("apply the Driveway Maintenance template", agent).id == "apply_template"
```
If `EstimateAgent()` needs an OpenAI key, reuse the construction pattern from `tests/test_estimate_agent.py` (grep `EstimateAgent(`).

- [ ] **Step 4: Record the grammar layer**

Add to `tests/test_maple_routing_snapshot.py`:

```python
def test_grammar_snapshot():
    from agents.estimate.command_grammar import match_command
    actual = {phrase: (lambda f: f.id if f else None)(match_command(phrase)) for phrase in load_corpus()}
    _compare("snapshot_grammar.json", actual)
```
Remove the `task` key from the two `expected.json` rows with `"task": 6`. Run the snapshot test twice. Expected: the first run writes the file, the second passes, and the task-6 rows pass.

Then review the grammar snapshot. For every corpus phrasing that maps to a command id, check that the id is right. Record any surprise as a ledger ruling, or fix the pattern with an added REJECT example.

- [ ] **Step 5: Gates**

Run mypy and ruff on `agents/estimate/command_grammar.py tests/test_command_grammar.py`, then run the tests. Expected: clean, all pass.

---

### Task 7: The open-question decider (#4, #15, #19)

**Files:**
- Create: `platform/routers/agent_helpers/open_question.py`
- Create: `platform/tests/test_open_question.py`
- Modify: `platform/routers/agents.py` (insert the decider; delete `_message_breaks_pending_confirmation` 274-305 and `_PENDING_RELEASE_READ_VERB_PATTERN` 267-271; delete the get_estimate branch 1241-1254, the Estimate check in the awaited-value override 1353-1358, the Estimate check and the `policy_refusal` clause in the pending fallback 1453-1490)
- Modify: `platform/routers/agent_helpers/fuzzy_confirmation.py` (drop the `message_breaks_pending` param and the re-ask branch 260-273)
- Modify: `platform/routers/agent_helpers/estimate_update.py:168-174,212`, `platform/routers/agent_helpers/delegate_estimate_ops.py:81` (delete their `answers_open_question` branches)
- Modify: `platform/routers/agent_helpers/active_estimate.py` (drop Estimate questions when the viewed estimate changes)
- Modify: `platform/agents/estimate/work_item_context.py` (delete `answers_open_question`, `_abandons_value_prompt`, `_ESTIMATE_REQUEST_RE`, `_HOW_MANY_RE` and their calls in `_prepare_estimate_turn`)
- Modify: `platform/agents/orchestrator/service.py` (delete `_answers_estimate_question` 1010-1030 and its step at 2001-2005; delete the `policy_refusal` flag at 1351-1354)
- Test: `tests/test_orchestrator_endpoint.py`, `tests/test_maple_work_item_context.py`, `tests/test_agent_helpers_fuzzy_confirmation.py`, `tests/test_maple_estimate_targeting.py`, `tests/test_agent_helpers_active_estimate.py`, `tests/test_maple_task_operations.py::TestAwaitedValueWins`, snapshot

**Interfaces:**
- Consumes: `match_command(text, agent)` (Task 6), `estimate_question(context)` (`finalize_result.py:112`), `WorkItemContextMixin._pick_candidate` (static), `is_bare_estimate_code_reply`, `estimate_code_in_text`, `is_affirmative_text` / `is_negative_text` / `is_cancellation_text`.
- Produces:
  ```python
  class Decision(str, Enum): ANSWER = "answer"; NEW_MESSAGE = "new_message"; CANCEL = "cancel"
  @dataclass(frozen=True)
  class OpenQuestion: kind: str; source: str; record: Dict[str, Any]   # kind: yes_no|pick|free_text; source: fuzzy|estimate
  def current_question(context: Dict[str, Any]) -> Optional[OpenQuestion]
  def decide(message: str, question: OpenQuestion, agent: Any = None) -> Decision
  def drop_question(context: Dict[str, Any], question: OpenQuestion) -> None
  ```

- [ ] **Step 1: Back up** (`t7`).

- [ ] **Step 2: Failing unit tests**

`tests/test_open_question.py`:

```python
import pytest

from routers.agent_helpers.open_question import Decision, current_question, decide, drop_question
from tests.maple_routing.states import QUESTION_STATES


def q(kind):
    return current_question(dict(QUESTION_STATES[kind]))


@pytest.mark.parametrize("text", ["yes", "Yes.", "YES!", "yes please", "ok", "confirm", "no", "No thanks.", "nope"])
def test_yes_no_answers_including_translated_punctuation(text):
    assert decide(text, q("yes_no")) is Decision.ANSWER

@pytest.mark.parametrize("text", ["cancel", "never mind", "Cancel."])
def test_yes_no_cancel(text):
    assert decide(text, q("yes_no")) is Decision.CANCEL

@pytest.mark.parametrize("text", [
    "yes, add a note to work item 2: check drainage", "list my contacts",
    "how many properties do I have?", "add a contact named Ana Reyes",
])
def test_yes_no_anything_else_is_a_new_message(text):
    assert decide(text, q("yes_no")) is Decision.NEW_MESSAGE

@pytest.mark.parametrize("text", ["2", "the second one", "Back patio pavers", "the patio one"])
def test_pick_answers(text):
    assert decide(text, q("pick")) is Decision.ANSWER

@pytest.mark.parametrize("text", ["set the tax to 13%", "show me my estimates", "E0042"])
def test_pick_non_answers(text):
    assert decide(text, q("pick")) is Decision.NEW_MESSAGE

@pytest.mark.parametrize("text", ["Remove all debris and haul away", "Equipment rental and delivery", "Show homeowner the revised quote before starting"])
def test_free_text_values(text):
    assert decide(text, q("free_text")) is Decision.ANSWER

@pytest.mark.parametrize("text", ["what's the total on this estimate?", "go back to E0001", "show me my estimates"])
def test_free_text_releases(text):
    assert decide(text, q("free_text")) is Decision.NEW_MESSAGE

def test_free_text_cancel():
    assert decide("cancel", q("free_text")) is Decision.CANCEL

def test_no_question():
    assert current_question({"company_id": "x"}) is None

def test_other_agents_records_are_not_estimate_questions():
    ctx = {"pending_intents": [{"agent": "Task Agent", "intent": "update_task", "awaiting_value_for": "title"}]}
    assert current_question(ctx) is None

def test_drop_question_removes_only_that_record():
    ctx = dict(QUESTION_STATES["pick"])
    ctx["pending_intents"] = list(ctx["pending_intents"]) + [{"agent": "Task Agent", "awaiting_value_for": "title"}]
    question = current_question(ctx)
    drop_question(ctx, question)
    assert [r["agent"] for r in ctx["pending_intents"]] == ["Task Agent"]
```
Run. Expected: FAIL (import error).

- [ ] **Step 3: Implement `open_question.py`**

```python
"""The one place that decides whether a message answers Maple's open
Estimate question (design 2026-09-25 §5.1).

It owns the Estimate Agent's pending records and the estimate yes/no
(``pending_estimate_fuzzy_confirmation``). Other agents' pending records keep
the router's awaited-value override and pending fallback — out of scope.
A message that isn't an answer drops the question; no question traps later
messages.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from agents.estimate.command_grammar import match_command
from agents.estimate.text_helpers import ESTIMATE_AGENT_LABEL
from agents.estimate.text_helpers import PENDING_FUZZY_CONFIRMATION_CONTEXT_KEY as PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY
from agents.estimate.work_item_context import WorkItemContextMixin, is_bare_estimate_code_reply
from routers.agent_helpers.text_helpers import is_affirmative_text, is_cancellation_text, is_negative_text
from services.readable_id import estimate_code_in_text

_FREE_TEXT_FIELDS = frozenset({"description", "note", "work_item_name"})
_COURTESY_TAIL_RE = re.compile(r"[\s,]*(?:please|thanks|thank\s+you)?[\s.!]*$", re.IGNORECASE)


class Decision(str, Enum):
    ANSWER = "answer"
    NEW_MESSAGE = "new_message"
    CANCEL = "cancel"


@dataclass(frozen=True)
class OpenQuestion:
    kind: str      # "yes_no" | "pick" | "free_text"
    source: str    # "fuzzy" | "estimate"
    record: Dict[str, Any]


def _estimate_record(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    records = context.get("pending_intents")
    if not isinstance(records, list):
        return None
    for record in reversed(records):
        if isinstance(record, dict) and record.get("agent") == ESTIMATE_AGENT_LABEL:
            return record
    return None


def current_question(context: Dict[str, Any]) -> Optional[OpenQuestion]:
    fuzzy = context.get(PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY)
    if isinstance(fuzzy, dict):
        return OpenQuestion("yes_no", "fuzzy", fuzzy)
    record = _estimate_record(context)
    if record is None:
        return None
    if record.get("op") in ("choose_work_item", "choose_estimate"):
        return OpenQuestion("pick", "estimate", record)
    if str(record.get("awaiting_value_for") or "") in _FREE_TEXT_FIELDS:
        return OpenQuestion("free_text", "estimate", record)
    return None


def _bare(text: str) -> str:
    return _COURTESY_TAIL_RE.sub("", text.strip()).strip().lower()


def decide(message: str, question: OpenQuestion, agent: Any = None) -> Decision:
    text = (message or "").strip()
    bare = _bare(text)
    if is_cancellation_text(bare) or bare in ("cancel", "never mind", "nevermind"):
        return Decision.CANCEL
    if question.kind == "yes_no":
        if is_affirmative_text(bare) or is_negative_text(bare) or is_affirmative_text(text.lower().rstrip(".!")):
            return Decision.ANSWER
        return Decision.NEW_MESSAGE
    if question.kind == "pick":
        record = question.record
        if record.get("op") == "choose_estimate":
            return Decision.ANSWER if is_bare_estimate_code_reply(text) else Decision.NEW_MESSAGE
        candidates = record.get("candidates") or []
        return Decision.ANSWER if WorkItemContextMixin._pick_candidate(text, candidates) else Decision.NEW_MESSAGE
    # free text
    if text.endswith("?") or estimate_code_in_text(text) or match_command(text, agent) is not None:
        return Decision.NEW_MESSAGE
    return Decision.ANSWER


def drop_question(context: Dict[str, Any], question: OpenQuestion) -> None:
    if question.source == "fuzzy":
        context.pop(PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY, None)
        return
    records = context.get("pending_intents")
    if isinstance(records, list):
        context["pending_intents"] = [r for r in records if r is not question.record]
```

Run the unit tests. Two cases may fail:
- **"the patio one":** `_pick_candidate` rejects it. Extend `_pick_candidate` in `work_item_context.py` so a reply of at most five words, whose content words (minus `the/one/item/work`) all appear in exactly one candidate description, picks that candidate. Record a ledger ruling that cites spec §5.1.
- **The key import.** `open_question` takes the key from `agents.estimate.text_helpers` (the same string `fuzzy_confirmation` uses). This avoids importing the router helper, which imports the agent.

Expected after fixes: PASS.

- [ ] **Step 4: Record the decisions layer; the #4 and #19 rows**

Add to the snapshot test:

```python
def test_decide_snapshot():
    from routers.agent_helpers.open_question import current_question, decide
    from tests.maple_routing.states import QUESTION_STATES
    questions = {k: current_question(dict(v)) for k, v in QUESTION_STATES.items()}
    actual = {phrase: {k: decide(phrase, qn).value for k, qn in questions.items()} for phrase in load_corpus()}
    _compare("snapshot_decide.json", actual)
```
Remove `task` from every `"task": 7` row. Run twice. Expected: PASS.

- [ ] **Step 5: Failing endpoint tests**

In `tests/test_orchestrator_endpoint.py`:

```python
async def test_a_request_during_a_yes_no_question_is_handled_not_re_asked(...):
    # seed QUESTION_STATES["yes_no"] via call_with_seeded_state; message "list my contacts"
    # assert the Contact stub agent handled it and the persisted context has no
    # pending_estimate_fuzzy_confirmation (#19)

async def test_a_description_prompt_does_not_swallow_a_request(...):
    # seed QUESTION_STATES["free_text"]; message "show me the estimate for the Smith property"
    # assert the orchestrator ran (stub estimate agent got orchestrator_intent get_estimate)
    # and no set_description happened (#4)

async def test_an_answer_goes_straight_to_the_estimate_agent(...):
    # seed QUESTION_STATES["free_text"]; message "Remove all debris and haul away"
    # assert the stub orchestrator was NOT called and the estimate stub got the message with
    # orchestrator_intent "update_estimate"

async def test_a_property_details_reply_naming_equipment_reaches_the_property_agent(...):
    # seed a Property Agent pending record without awaiting_value_for (missing details);
    # message "12 Equipment Road, Springfield" -> Property stub handles it (#15)

async def test_switching_estimate_pages_drops_the_open_question(...):
    # seed QUESTION_STATES["yes_no"] + last_viewed_estimate for E0042; client_context
    # viewed_estimate for another estimate id with a new nonce; message "yes"
    # assert the fuzzy handler did not run (no confirmed dispatch) — Review Focus 4
```
Write each using the file's existing stub-agent fixtures and `call_with_seeded_state`. For the last one, reuse the active-estimate fake from `tests/test_agent_helpers_active_estimate.py`: the viewed estimate must load.

Run. Expected: FAIL.

- [ ] **Step 6: Wire the decider into the router**

In `routers/agents.py`, immediately before the fuzzy-confirmation call (~1175), replace that call with:

```python
question = current_question(merged_context)
if question is not None:
    decision = decide(message, question, get_estimate_agent())
    if decision is Decision.NEW_MESSAGE:
        drop_question(merged_context, question)
    elif question.source == "fuzzy":
        if decision is Decision.CANCEL:
            drop_question(merged_context, question)
            return _finalize_result(cancelled_envelope(message, merged_context))
        fuzzy_confirm_result = await handle_estimate_fuzzy_confirmation(
            agent=get_estimate_agent(), message=message,
            context_payload=merged_context, schedule=background_tasks.add_task,
        )
        if fuzzy_confirm_result is not None:
            return _finalize_result(fuzzy_confirm_result)
    else:
        # Same call shape as the get_estimate answers branch this replaces
        # (1241-1254): pass company/property exactly as it does.
        answered = await get_estimate_agent().process(
            message,
            context={**merged_context, "orchestrator_intent": str(question.record.get("intent") or "update_estimate")},
        )
        return _finalize_result(answered)
```
- **`cancelled_envelope`:** use the same envelope shape `fuzzy_confirmation` returns for its negative branch ("Cancelled..."). Move that branch's construction into a small helper in `fuzzy_confirmation.py` named `cancelled_envelope(message, context_payload)`, and reuse it there.
- **Imports:** import `Decision, current_question, decide, drop_question` from `routers.agent_helpers.open_question`.
- **Delete:**
  - `_message_breaks_pending_confirmation` and `_PENDING_RELEASE_READ_VERB_PATTERN`;
  - the `get_estimate` answers branch at 1241-1254;
  - the `if awaiting_value_match … == "Estimate Agent"` block at 1353-1358. Also make `_get_awaiting_value_match` skip records whose `agent == ESTIMATE_AGENT_LABEL`: the decider owns them, and after it runs none remain on a new message;
  - in the pending fallback, the `and not result.get("policy_refusal")` clause and the Estimate `answers_open_question` block. Make `_get_pending_fallback_match` skip Estimate records.
- **In `fuzzy_confirmation.py`:**
  - remove the `message_breaks_pending` parameter;
  - replace the re-ask branch (260-273) with `return None`. It is unreachable now, but it stays safe;
  - remove the now-unused import in `routers/agents.py`.
- **In `orchestrator/service.py`:**
  - delete `_answers_estimate_question` and its step (2001-2005);
  - delete `payload["policy_refusal"] = True` (1351-1354);
  - keep `_POLICY_REFUSALS` only if something else uses it; otherwise delete it.
- **In `estimate_update.py` and `delegate_estimate_ops.py`,** delete the `answers_open_question` branches (168-174 + 212, 81). With the decider in front, an Estimate question never survives to them.
- **In `work_item_context.py`:**
  - delete `answers_open_question`, `_abandons_value_prompt`, `_ESTIMATE_REQUEST_RE`, `_HOW_MANY_RE` and `_LEFT_AS_IS`, if unused;
  - in `_prepare_estimate_turn`, delete the three `_abandons_value_prompt` checks (497, 502, 511). A pending record that reaches the agent is being answered;
  - keep the cancel branch.
- **In `active_estimate.apply_viewed_estimate_signal`:** when the signal moves the anchor to a different estimate, also call `context.pop(PENDING_FUZZY_CONFIRMATION_CONTEXT_KEY, None)` and remove Estimate `pending_intents` records. Put this in `_drop_other_estimate_memory` (Review Focus 4).

Run the endpoint tests from Step 5. Expected: PASS.

- [ ] **Step 7: Fix the tests the deletions break**

```bash
./run_tests.sh tests/test_orchestrator_endpoint.py tests/test_maple_work_item_context.py tests/test_agent_helpers_fuzzy_confirmation.py tests/test_maple_estimate_targeting.py tests/test_agent_helpers_estimate_update.py tests/test_agent_helpers_delegate_estimate_ops.py tests/test_maple_task_operations.py tests/test_maple_estimate_field_edits.py tests/test_agent_helpers_active_estimate.py -q 2>&1 | tail -40
```
For each failure:
- **A test of a deleted function** (`answers_open_question`, `_abandons_value_prompt`, `_answers_estimate_question`, `message_breaks_pending`, `_message_breaks_pending_confirmation`, `names_estimate_title`-based release): move its phrasing and expected outcome into `tests/test_open_question.py` as a `decide` case. If it was a routing claim, add it to `expected.json`. Then delete the old test. Never delete a phrasing without re-homing it.
- **A test that now routes differently:** decide from spec §5.1 whether the new result is intended. If it is, update the assertion with a `# design 2026-09-25 §5.1` comment. If it is not, fix the code.

Expected: all green.

- [ ] **Step 8: Snapshot review and gates**

- Run `./run_tests.sh tests/test_maple_routing_snapshot.py -q`.
- The routing snapshot should move only where `_answers_estimate_question` used to fire. No anchor state has pending intents, so expect no change. If rows moved, review them, then run `UPDATE_MAPLE_SNAPSHOT=1`.
- Run mypy and ruff on `routers agents`.

---

### Task 8: Target freshness and guessed-target confirmation (#20)

**Files:**
- Create: `platform/agents/estimate/target_freshness.py`, `platform/tests/test_target_freshness.py`
- Modify: `platform/routers/agents.py` (increment the turn index after the context is built, ~1066)
- Modify: `platform/routers/agent_helpers/active_estimate.py:62-97` (`anchor_estimate` records the set turn)
- Modify: `platform/agents/estimate/work_item_context.py:230-249` (`_set_active_work_item` records `set_turn`), `TRANSIENT_KEYS` (+ `ESTIMATE_RESOLVED_BY_KEY`)
- Modify: `platform/agents/estimate/crud_handlers.py:1976-2060` (`_resolve_estimate_code_or_title` records how the estimate was resolved)
- Modify: `platform/agents/estimate/edit_executor.py:209-260,389-424,530-560` (record anchor use; confirm stale)
- Test: `tests/test_estimate_edit_executor.py`, `tests/test_agent_helpers_active_estimate.py`, `tests/test_maple_work_item_context.py`

**Interfaces:**
- Produces:
  ```python
  TURN_INDEX_KEY = "turn_index"
  ESTIMATE_SET_TURN_KEY = "active_estimate_set_turn"
  ESTIMATE_RESOLVED_BY_KEY = "estimate_resolved_by"          # transient: "named" | "anchor"
  def estimate_is_fresh(context: Dict[str, Any], estimate_id: str) -> bool
  def work_item_is_fresh(context: Dict[str, Any]) -> bool
  def freshest_anchor(context: Dict[str, Any]) -> str       # "work_item" | "estimate" | ""
  ```

- [ ] **Step 1: Back up** (`t8`).

- [ ] **Step 2: Failing unit tests**

`tests/test_target_freshness.py`:

```python
from agents.estimate.target_freshness import estimate_is_fresh, freshest_anchor, work_item_is_fresh

def ctx(**kw):
    base = {"turn_index": 10, "active_estimate_id": "E1", "active_estimate_set_turn": 9}
    base.update(kw); return base

def test_set_on_the_previous_turn_is_fresh():
    assert estimate_is_fresh(ctx(), "E1")

def test_older_is_stale():
    assert not estimate_is_fresh(ctx(active_estimate_set_turn=7), "E1")

def test_the_estimate_on_screen_is_fresh():
    assert estimate_is_fresh(ctx(active_estimate_set_turn=2, viewed_estimate={"id": "E1", "at": 1}), "E1")

def test_a_different_estimate_on_screen_does_not_freshen_the_anchor():
    assert not estimate_is_fresh(ctx(active_estimate_set_turn=2, viewed_estimate={"id": "E2", "at": 1}), "E1")

def test_work_item_freshness():
    assert work_item_is_fresh(ctx(active_work_item={"set_turn": 10}))
    assert not work_item_is_fresh(ctx(active_work_item={"set_turn": 3}))
    assert not work_item_is_fresh(ctx())

def test_freshest_anchor():
    assert freshest_anchor(ctx(active_work_item={"set_turn": 10})) == "work_item"
    assert freshest_anchor(ctx(active_work_item={"set_turn": 4})) == "estimate"
    assert freshest_anchor({"turn_index": 1}) == ""
```
Run. Expected: FAIL (import error).

- [ ] **Step 3: Implement `target_freshness.py`**

```python
"""How fresh an inferred target is (design 2026-09-25 §5.2).

A target set on this turn or the previous one — or the estimate the portal
page is showing — is fresh: Maple applies the edit and names it. Anything
older is stale: Maple asks first.
"""
from __future__ import annotations

from typing import Any, Dict

TURN_INDEX_KEY = "turn_index"
ESTIMATE_SET_TURN_KEY = "active_estimate_set_turn"
ESTIMATE_RESOLVED_BY_KEY = "estimate_resolved_by"
_WORK_ITEM_KEY = "active_work_item"
_VIEWED_KEY = "viewed_estimate"


def _turn(context: Dict[str, Any]) -> int:
    return int(context.get(TURN_INDEX_KEY) or 0)


def _recent(set_turn: Any, context: Dict[str, Any]) -> bool:
    try:
        return int(set_turn) >= _turn(context) - 1
    except (TypeError, ValueError):
        return False


def estimate_is_fresh(context: Dict[str, Any], estimate_id: str) -> bool:
    viewed = context.get(_VIEWED_KEY)
    if isinstance(viewed, dict) and str(viewed.get("id") or "") == str(estimate_id):
        return True
    return _recent(context.get(ESTIMATE_SET_TURN_KEY), context)


def work_item_is_fresh(context: Dict[str, Any]) -> bool:
    anchor = context.get(_WORK_ITEM_KEY)
    return isinstance(anchor, dict) and _recent(anchor.get("set_turn"), context)


def freshest_anchor(context: Dict[str, Any]) -> str:
    anchor = context.get(_WORK_ITEM_KEY)
    wi_turn = int(anchor.get("set_turn") or -1) if isinstance(anchor, dict) else -1
    est_turn = int(context.get(ESTIMATE_SET_TURN_KEY) or -1) if context.get("active_estimate_id") or context.get("active_estimate_code") else -1
    if wi_turn < 0 and est_turn < 0:
        return ""
    return "work_item" if wi_turn >= est_turn else "estimate"
```
Run. Expected: PASS.

- [ ] **Step 4: Record the turns (failing tests first)**

- In `tests/test_agent_helpers_active_estimate.py`: after `anchor_estimate(ctx, …)` with `ctx["turn_index"] = 7`, assert `ctx["active_estimate_set_turn"] == 7`.
- In `tests/test_maple_work_item_context.py`: after the anchor is set with `turn_index` 7, assert `context["active_work_item"]["set_turn"] == 7`.
- In `tests/test_orchestrator_endpoint.py`: two turns in a row, and the saved context's `turn_index` goes 1, then 2.

Run. Expected: FAIL.

Implement:
- in the router, `merged_context[TURN_INDEX_KEY] = int(merged_context.get(TURN_INDEX_KEY) or 0) + 1` right after `append_user_turn`;
- in `anchor_estimate`, `context[ESTIMATE_SET_TURN_KEY] = int(context.get(TURN_INDEX_KEY) or 0)`;
- in `_set_active_work_item`, `"set_turn": int(context.get(TURN_INDEX_KEY) or 0)`.

`turn_index` persists; it is not transient. Run. Expected: PASS.

- [ ] **Step 5: Failing executor tests**

In `tests/test_estimate_edit_executor.py`, reuse the file's fake estimate and `_run` helper:

```python
def test_a_fresh_anchored_work_item_is_edited_and_named():
    ctx = {..., "turn_index": 5, "active_estimate_set_turn": 5, "estimate_resolved_by": "anchor",
           "active_work_item": {..., "set_turn": 5}}
    result = _run([SetWorkItemPercentage(target=WorkItemRef(use_active=True), field="markup", value=20)], ctx)
    assert "Front yard cleanup" in result["response"] and "E0042" in result["response"]
    assert persisted

def test_a_stale_anchored_work_item_asks_first():
    ctx = {... "active_work_item": {..., "set_turn": 1}, "turn_index": 5}
    result = _run([...same...], ctx)
    assert result["needs_clarification"] is True
    assert ctx["pending_estimate_fuzzy_confirmation"]["sub_op"] == "edit_commands"
    assert not persisted

def test_a_stale_anchored_estimate_asks_first():
    ctx = {"turn_index": 9, "active_estimate_set_turn": 2, "estimate_resolved_by": "anchor", ...}
    ...  # AddWorkItem
    assert result["needs_clarification"] is True

def test_a_named_target_never_asks():
    ctx = {"turn_index": 9, "active_estimate_set_turn": 2, "estimate_resolved_by": "named", ...}
    result = _run([SetWorkItemPercentage(target=WorkItemRef(position=1), field="tax", value=13)], ctx)
    assert persisted

def test_confirmed_stale_edit_applies():
    # run_confirmed_edits with the stashed record -> persisted
```
Run. Expected: FAIL.

- [ ] **Step 6: Implement the confirmation**

- **`_resolve_estimate_code_or_title`:** set `context[ESTIMATE_RESOLVED_BY_KEY] = "anchor"` on the two branches that return the active code (the open-work-item branch ~2032 and the active anaphora branch ~2051). Set it to `"named"` on every other successful return, including the forced code (a confirmed or picked estimate counts as named).
- **Transient key:** add `ESTIMATE_RESOLVED_BY_KEY` to `work_item_context.TRANSIENT_KEYS`.
- **`_Batch`:** add `used_anchor: bool = False`. In `_resolve_target`, set `batch.used_anchor = True` on the branch that resolves `use_active` through `_anchored_index`. Do not set it for the `added_id`, single-item or holds-the-named-line branches: those identify the item from the estimate itself.
- **`_run_edit_commands`:** after the removal check (~line 253), when `not confirmed`:

```python
stale = (
    (context.get(ESTIMATE_RESOLVED_BY_KEY) == "anchor" and not estimate_is_fresh(context, str(target.id)))
    or (dry_batch.used_anchor and not work_item_is_fresh(context))
)
if stale:
    return self._confirm_target(query, context, commands, pins, dry)
```
`dry_batch` is the dry run over copies; reuse the one the removal check builds. If it only builds one for removals, build it for this check too: same code path, no persistence.

- **`_confirm_target`:** mirrors `_confirm_removal` (389-424) with the same pending record shape and a different question. Extract the shared body into `_stash_edit_confirmation(query, context, commands, pins, dry, question, result)` and have both call it.

```python
question = f"Just to check: apply this to {target_label} on {dry.code} '{title}'? (yes/no)"
```
`target_label` is the anchored item's label when `used_anchor` is set, otherwise "the estimate".

Run the executor tests plus `tests/test_agent_helpers_fuzzy_confirmation.py`. Expected: PASS.

- [ ] **Step 7: Fix tests that relied on silent anchor writes**

```bash
./run_tests.sh tests/test_estimate_edit_executor.py tests/test_maple_work_item_edits.py tests/test_maple_work_item_context.py tests/test_maple_edit_planner.py tests/test_maple_estimate_targeting.py tests/test_maple_work_item_ops.py -q 2>&1 | tail -40
```
Tests that seed an anchor without `turn_index` or `set_turn` now get a question. For each one, decide which case it is:
- **The scenario is "the user just did this":** seed fresh turns (`turn_index` equal to `set_turn`) in the shared fixture, e.g. `_ON_A_WORK_ITEM` in `test_maple_work_item_edits.py:204-206`.
- **The scenario is a stale anchor:** assert the question.

Expected: all green.

- [ ] **Step 8: Gates**

Run mypy and ruff on `agents/estimate routers`, then the snapshot test. Expected: the snapshot is unchanged, since the routing layer doesn't reach the executor.

---

### Task 9: Estimate Agent uses only the command list (#5, #13, #17 part, #22)

**Files:**
- Modify: `platform/agents/estimate/crud_handlers.py:2366-2436` (`owns_update_sub_op`, `has_update_sub_op`, `_handle_update_estimate`), `2068-2100` (`_job_name_is_an_open_work_item` gated to work-item commands)
- Modify: `platform/agents/estimate/service.py:845-855` (delete the agent's policy guard)
- Modify: `platform/agents/estimate/work_item_edit_detectors.py` (delete the value detectors, `compound` / `multi_target` and `relative_percentage`; keep `_detect_generate` and the `WorkItemEdit` dataclass)
- Modify: `platform/agents/estimate/work_item_handlers.py:266` (`_detect_work_item_op`: delete ops the planner owns), `work_item_field_handlers.py` (delete handlers left without callers)
- Modify: `platform/agents/estimate/note_handlers.py:112` (the estimate note refuses a head that names another record)
- Test: `tests/test_work_item_edit_detectors.py`, `tests/test_maple_work_item_ops.py`, `tests/test_maple_work_item_edits.py`, `tests/test_maple_estimate_field_edits.py`, `tests/test_maple_estimate_targeting.py`, `tests/test_estimate_agent.py`, and the other `test_maple_*` files listed in Step 7

**Interfaces:**
- Consumes: `match_command(text, agent)`, `UPDATE_COMMAND_IDS`, `READ_IDS` (Task 6).
- Produces: `owns_update_sub_op(text) -> bool`, which is now `match_command(text, self) is not None and found.id in UPDATE_COMMAND_IDS`. `has_update_sub_op` is identical.

- [ ] **Step 1: Back up** (`t9`).

- [ ] **Step 2: Failing tests**

In `tests/test_maple_estimate_field_edits.py`, add:

```python
def test_archive_the_patio_job_targets_the_estimate_titled_patio():   # #5
    # E0042 open (work item "Front patio pavers"), E0001 titled "Patio"
    # "archive the patio job" -> E0001 archived, E0042 untouched

def test_a_note_to_another_named_record_is_refused_by_the_estimate():   # #2 handler side
    # "add a note to John Doe: call back" reaching _handle_update_estimate -> no Note created,
    # response says it can't file a note for John Doe on the estimate

@pytest.mark.parametrize("value", ["Remove all debris and haul away", "Equipment rental and delivery"])
def test_value_replies_are_not_policy_refused(value):   # #13
    # description prompt pending, reply value -> description set, no refusal

def test_an_unlisted_edit_goes_to_the_planner():   # #22
    # "set the hours on grading to 2 days" with a fake planner -> planner called with the message
```
Also add `test_a_listed_percentage_never_calls_the_planner`, using the fake planner from `tests/test_maple_edit_planner.py`: the planner is not called for "set the markup on work item 2 to 20%".

Run. Expected: FAIL.

- [ ] **Step 3: Rewire `_handle_update_estimate`**

Replace the cascade body (2452-2595) with a dispatch on `match_command(query, self)`. Keep every handler call exactly as today's cascade makes it: same arguments, and the same pre-extracted values from the detector where the handler takes one. For each id:

| id | Call (today's line) |
|---|---|
| `add_work_item` | `_handle_update_estimate_work_item_add` (2468) |
| `remove_work_item` | `_handle_update_estimate_work_item_remove` (2459) |
| `rename_work_item` | `_handle_update_estimate_work_item_rename` (2463) |
| `rename_estimate` | `_handle_update_estimate_title` (2534). Re-run `_detect_estimate_title_update(query)` to get its tuple |
| `set_percentage` | `_handle_work_item_edit(query, company_id, context, WorkItemEdit(kind="percentage", fields={"field": slots["field"].lower(), "value": float(slots["value"])}, name_hint=<work-item hint>))` |
| `set_gross_margin` | `_handle_work_item_edit(..., WorkItemEdit(kind="gross_margin", fields={"margin_pct": float(slots["value"])}, name_hint=...))` |
| `set_total` | `_handle_work_item_set_total` (2503) |
| `add_note` | Estimate target (`ref_form` `code`/`this`, or pronoun `this`): `_handle_add_estimate_note` (2552). Work-item target: `_handle_work_item_edit(..., WorkItemEdit(kind="note" if body else "note_prompt", fields={"body": body}, name_hint=...))` |
| `set_status` | `_handle_update_estimate_status_transition` (2524) |
| `set_estimate_description` | `_handle_update_estimate_description` (2541) |
| `generate_work_item` | `_handle_work_item_edit(..., _detect_generate(query))` |
| `set_recurring` | the recurring handler matching `_detect_work_item_op(query)["op"]` (2485-2490) |
| `list_work_item_lines` | the list-materials / list-activities handler (2495, 2501) |
| `query_work_item_field` | `_handle_query_work_item_field` (2505) |
| `adjust_assumption` | the size/swap branch (2514) |
| `apply_template` | `_handle_update_estimate_apply_template` (2563) |
| `link_property` | `_handle_update_estimate_property_link` (2557) |
| `get_work_item` / `list_work_items` | `_handle_get_work_item` / `_handle_list_work_items` (2479) |
| `remove_pronoun` | `_handle_update_estimate_work_item_remove` (2459) with an empty name hint (the anchored item). The orchestrator only sends it here when the work item is the freshest anchor (Task 10) |
| anything else, or no match | capabilities envelope (2569-2592), then `return await self._plan_and_apply_edits(query, company_id, context, capabilities)` |

The work-item hint for `name_hint` comes from the slots, in this order:
1. `work_item_label`;
2. `"work item N"` from `work_item_number`;
3. the ordinal mapped to its position;
4. otherwise `""`, which means the anchor.

Put this in a helper:
```python
def _hint(self, slots: Dict[str, str]) -> str:
    """The work-item reference a listed command named, as today's handlers
    take it ("" = the anchored item)."""
```

- **`owns_update_sub_op` and `has_update_sub_op`:** implement as
  ```python
  found = match_command(text, self); return found is not None and found.id in UPDATE_COMMAND_IDS
  ```
- **`_job_name_is_an_open_work_item` (#5):** in `_resolve_estimate_code_or_title`, call it only when the listed command is a work-item command. Estimate-level commands (`set_status`, `rename_estimate`, `set_estimate_description`, `link_property`, `apply_template`, `get_estimate`) try the title lookup first. Pass the command id in through the context as a transient key:
  - `context["listed_command"] = found.id`, set in `_handle_update_estimate` before resolution;
  - add `"listed_command"` to `work_item_context.TRANSIENT_KEYS`.

  When the work-item reading and a title match both apply to an estimate-level command, return a `pick` question listing both, using the existing multi-match envelope.
- **Agent policy guard (#13):** delete `service.py:845-855`. The orchestrator is now the only place that runs it (Task 10).
- **Other-record note (#2, handler side):** in `note_handlers._detect_note_update` callers, when the note head names a target that is not this/it/the estimate/an E-code/a work item, return:
  > "I can only file that note on an estimate or a work item — tell me which, or add it from John Doe's page."

  Build it from the named target. The check is: `match_command(query)` is None and the head contains `(to|for|on) <words>`. This lives inside the agent, not in routing; routing sends such messages to the classifier.

Run the Step 2 tests. Expected: PASS.

- [ ] **Step 4: Delete what no longer has a caller**

1. In `work_item_edit_detectors.py`, delete:
   - `_detect_material_update`, `_detect_activity_update` (with `_ACT_EFFORT` and the related patterns) and `_detect_percentage`;
   - the relative-percentage, `compound` and `multi_target` logic;
   - `_VALUE_DETECTORS`, `_SECOND_CLAUSE` and `_MULTI_TARGET`;
   - `_NOTE_PATTERNS` and `_NOTE_PROMPT`, now covered by `add_note`.

   Reduce `detect_work_item_edit` to the generate detector, or delete it and import `_detect_generate` directly.
2. In `_detect_work_item_op`, delete the branches for `add`, `remove`, `rename`, `update_field`, `add_material`, `remove_material`, `update_material`, `add_activity`, `remove_activity`, `update_activity` and `set_total`. Keep `list`, `recurring_*`, `list_materials`, `list_activities` and `query`.
3. Delete the handlers whose only caller was a removed branch: `_handle_work_item_add_material`, `_remove_material`, `_add_activity`, `_remove_activity`, `_update_field`, and any others step 4 finds.
4. Confirm every deletion has no remaining caller:

```bash
cd /Users/simon/Development/Tangz/3maples/platform
for f in _detect_material_update _detect_activity_update _detect_percentage _handle_work_item_add_material _handle_work_item_remove_material _handle_work_item_add_activity _handle_work_item_remove_activity INFERRED_ADD_MATERIAL_RE INFERRED_REMOVE_MATERIAL_RE; do echo "== $f"; grep -rn "$f" --include=*.py . | grep -v "^./tests/" ; done
```
Expected: no production references remain. `INFERRED_*_RE` is used by `orchestrator/service.py:2501`. Leave that for Task 10, which deletes the orchestrator side.

Record each deleted function in the ledger as `Task 9: deleted <name> — planner owns <op>`.

- [ ] **Step 5: Planner cost backstop (#17, agent side)**

Delete `_COST_CUE_RE`, `_PRICE_CUE_RE`, `prices_a_stated_cost` and the call at `edit_planner.py:269`. The planner's `material_cost` reason stays (Task 11 prompt). In `tests/test_maple_edit_planner.py`, add:

```python
@pytest.mark.parametrize("message", ["our supplier raised prices, make the pavers $5", "bump the mulch to $45 a yard since our cost went up"])
def test_a_price_edit_that_mentions_cost_is_applied(message):
    # fake planner returns UpdateMaterial(price=5) -> applied, response names the price
```
Run it: it passes after the deletion (it would have failed before, so this is the RED→GREEN pair; write it first and watch it fail).

- [ ] **Step 6: Phrasing reference**

In `documentation/development/maple-phrasing-reference.md` §1:
- the rule table becomes the §4 list: core and ported;
- rows for phrasings that moved to the planner flip from ✅ to 🤖;
- bump "Last updated" to today;
- add a change-log entry: "Rules reduced to the written command list; line edits go to the planner."

- [ ] **Step 7: Fix the tests the deletions break**

```bash
./run_tests.sh tests/test_work_item_edit_detectors.py tests/test_maple_work_item_ops.py tests/test_maple_work_item_edits.py tests/test_maple_estimate_field_edits.py tests/test_maple_estimate_targeting.py tests/test_estimate_agent.py tests/test_maple_work_item_context.py tests/test_maple_new_phrasings.py tests/test_maple_phrasing_expansion.py tests/test_maple_bare_note_routing.py tests/test_maple_assigned_value_routing.py tests/test_maple_description_after_remove.py tests/test_maple_work_item_division_update.py tests/test_maple_material_size_operations.py tests/test_maple_listed_positional_reference.py tests/test_work_item_corpus.py tests/test_division_best_guess.py tests/test_agent_helpers_estimate_update.py -q 2>&1 | tail -60
```
Each failure falls into one of three cases:
- **A detector test for a deleted pattern:** move the phrasing into `tests/test_command_grammar.py` REJECT, or ACCEPT if a core entry covers it. Also add it to `corpus.json` if it isn't there already. Then delete the old test.
- **A handler test driven by a now-unlisted phrasing:** keep the scenario, but drive it through the fake planner. Make the fake return the command the old detector produced, and assert the same outcome. Pattern: `tests/test_maple_edit_planner.py`.
- **A test whose expected outcome contradicts spec §4:** update it and cite the spec section.

Never delete a phrasing without re-homing it. Expected: all green.

- [ ] **Step 8: Snapshot and gates**

- Run the snapshot test.
- The grammar snapshot must not move: core `match_command` is unchanged.
- The routing snapshot may move where the orchestrator used `owns_update_sub_op` indirectly. Review each moved row against spec §4, then `UPDATE_MAPLE_SNAPSHOT=1`.
- Run mypy and ruff on `agents/estimate`.

---

### Task 10: Orchestrator routing (#2, #3, #8, #14, #16, #20, #21)

**Files:**
- Modify: `platform/agents/orchestrator/service.py`
- Test: `tests/test_maple_routing_snapshot.py` (remove the task-10 keys), `tests/test_orchestrator_intents.py`, `tests/test_maple_estimate_targeting.py`, `tests/test_maple_work_item_edits.py`, `tests/test_maple_bare_note_routing.py`, `tests/test_maple_task_routing.py`, `tests/test_maple_task_context.py`

**Interfaces:**
- Consumes: `match_command` / `READ_IDS` / `UPDATE_COMMAND_IDS` (Task 6) and `freshest_anchor` (Task 8).
- Produces: `OrchestratorAgent._route_listed_command(message, context) -> Optional[Dict[str, Any]]`.

- [ ] **Step 1: Back up** (`t10`).

- [ ] **Step 2: Confirm the failing rows**

Remove the `task` key from every `"task": 10` row in `expected.json`. Run `./run_tests.sh tests/test_maple_routing_snapshot.py -k expected -q`. Expected: those rows FAIL.

- [ ] **Step 3: Listed commands route by rule**

Add to `OrchestratorAgent`:

```python
def _route_listed_command(self, message: str, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Route a §4 command by rule (design 2026-09-25 §5.3). Everything else
    is left to the other rules and the classifier."""
    found = match_command(message)
    if found is None:
        return None
    ctx = context or {}
    has_estimate = bool(ctx.get("active_estimate_code") or ctx.get("active_estimate_id"))
    named = found.ref_form in ("code", "title")
    if found.id == "create_estimate":
        intent = "create_estimate"
    elif found.id in ("list_estimates",):
        intent = "list_estimates"
    elif found.id == "get_estimate":
        intent = "get_estimate"
    elif found.id in ("list_work_items", "get_work_item"):
        intent = WORK_ITEM_READ_INTENT  # see below
    elif found.id == "remove_pronoun":
        anchor = freshest_anchor(ctx)
        if anchor == "work_item":
            intent = "update_estimate"
        elif anchor == "estimate":
            intent = "delete_estimate"
        else:
            return None
    elif found.id == "add_note" and found.ref_form == "pronoun":
        return None   # "add a note to it" — whichever record "it" is; history/classifier decide
    elif found.id in UPDATE_COMMAND_IDS and (named or has_estimate):
        intent = "update_estimate"
    else:
        return None
    return self._build_rule_match_result(message, context, intent=intent, confidence=0.9)
```
Use `_build_rule_match_result`'s real signature, which is already used at step 3 (`process` 1986-1996). Adapt the call to it.

For `WORK_ITEM_READ_INTENT`, look up "show the work items on E0042" and "show work item 2" in `snapshot_routing.json`, state `est`. Use the intent the baseline recorded (`get_estimate` or `update_estimate`) as a module constant, so the work-item reads keep today's route. Record it as a ledger ruling.

In `process()`, insert `listed = self._route_listed_command(normalized_message, context); if listed: return listed` at the slot freed by `_answers_estimate_question` (after the positional follow-up, before cross-resource).

- [ ] **Step 4: Delete the anchor heuristics**

1. Delete `_is_work_item_edit` and its step (2012-2015), `_LINE_EDIT_KINDS`, `_PRICING_EDIT_KINDS`, `_names_an_anchored_activity` and the `detect_work_item_edit` import.
2. Delete the inline work-item question regex step (2072-2080).
3. Delete the use of `INFERRED_ADD_MATERIAL_RE` / `INFERRED_REMOVE_MATERIAL_RE` at ~2501, then delete both constants in `work_item_edit_detectors.py` (Task 9 Step 4 left them).
4. In `_resolve_intent_with_history` (3250), right after `history_domain = self._resolve_domain_from_history(context)`:
   ```python
   if history_domain == "estimate": return None  # estimate follow-ups go to the classifier (design §5.3)
   ```
5. In `_classify_via_action_domain` (2754-2833), call `_supplement_domain_from_entity_signals(head, original, action)` for note requests too. Take the head's note-target words as the text: the words after `(note )?(to|for|on)`. This makes "jot down a note for John Doe: …" resolve to contact (#2).
6. After the domain is known, if the request is a note and the domain is `material` or `labour`, return a short-circuit response (#21):
   > "Materials and roles don't take notes. I can add notes to estimates, work items, properties, contacts and tasks."

   Build it with the same `_PolicyShortCircuit` / `_build_short_circuit_response` path, with agent None.
7. In `_detect_policy_short_circuit` (350-405), run the bulk-delete and equipment checks on `strip_assigned_value(strip_dictated_payload(original)).lower()` instead of `normalized` (#14). Leave the other checks as they are.

- [ ] **Step 5: Tell the classifier what's open**

In `_build_entity_context_summary` (1208-1256), after the active fields, add:

```python
work_item = context.get("active_work_item")
if isinstance(work_item, dict) and work_item.get("description"):
    lines.append(f"Open work item: {work_item['description']} (work item {work_item.get('position')} of {work_item.get('estimate_code')})")
```
Add a test in `tests/test_orchestrator_intents.py` next to `test_orchestrator_passes_chat_history_context_to_llm` (1123) that asserts the line reaches the fake LLM's `entity_context`. Write it first and watch it fail.

- [ ] **Step 6: Run the expected rows**

Run `./run_tests.sh tests/test_maple_routing_snapshot.py -k expected -q`. Expected: all PASS. If a row fails, trace it with `OrchestratorAgent(use_llm=False).process(phrase, ANCHOR_STATES[state])` and fix the rule. Never add a regex outside `command_grammar.py`.

- [ ] **Step 7: Fix the tests the deletions break**

```bash
./run_tests.sh tests/test_orchestrator_intents.py tests/test_maple_estimate_targeting.py tests/test_maple_work_item_edits.py tests/test_maple_bare_note_routing.py tests/test_maple_task_routing.py tests/test_maple_task_context.py tests/test_maple_assigned_value_routing.py tests/test_maple_listed_positional_reference.py tests/test_maple_crud_coverage.py -q 2>&1 | tail -60
```
For each failure:
- **Tests of deleted lanes** (`_is_work_item_edit`, the last-touched gate, inferred-material, history-to-estimate): the phrasing goes into `expected.json` with the outcome spec §5.3 gives. Usually that is `update_estimate` when a core command matches; otherwise `intent_not` for the old wrong target, or unknown in Tier 1 because the classifier decides. Then delete the old test.
- **`test_maple_crud_coverage.py` Tier 1 counts:** update §12.3 of the phrasing reference with the new counts.

Expected: all green.

- [ ] **Step 8: Review the snapshot**

- Run the routing snapshot.
- Many rows will move. Review the diff file section by section (the assertion prints the first 80; for the rest, write the full diff to the scratchpad):
  - every move to `update_estimate` must be a core command;
  - every move away from `update_estimate` must be a phrasing that §4 doesn't list, now left to the classifier.
- Record the counts in the ledger, then `UPDATE_MAPLE_SNAPSHOT=1`.

- [ ] **Step 9: Prompt review and gates**

- The classifier's context changed, so run `/agent-prompt-review agents/orchestrator/service.py` and fix any CRITICAL or HIGH.
- Run mypy and ruff on `agents/orchestrator agents/estimate`.
- Run `./run_bandit.sh agents/orchestrator`.

---

### Task 11: Planner prompt and the live check

**Files:**
- Modify: `platform/prompts/estimate_edit_planner.py`, `platform/agents/estimate/edit_planner.py:52` (`unsupported_reason` += `"labor_burden"`)
- Create: `platform/tests/test_maple_routing_live.py` (`@pytest.mark.llm_e2e`)
- Modify: `platform/tests/test_maple_edit_planner.py`, `platform/tests/test_maple_edit_planner_llm.py`

- [ ] **Step 1: Back up** (`t11`).

- [ ] **Step 2: Failing test for the labor-burden reason**

```python
def test_labor_burden_reason_returns_the_burden_refusal():
    # fake planner returns EditPlan(commands=[], unsupported_reason="labor_burden")
    # -> response is the existing burden refusal text (text_helpers.py:911 constant)
```
Run. Expected: FAIL (the Literal rejects the value).

- [ ] **Step 3: Implement**

- Add `"labor_burden"` to the `unsupported_reason` Literal.
- In `_plan_and_apply_edits`, map it to the existing burden refusal constant, found by grepping `text_helpers.py:~911`.
- Prompt text (TDD-exempt, but still reviewed). Add these rules to `prompts/estimate_edit_planner.py`:
  - "Effort is in hours. If the user gives days, weeks or minutes, set needs_clarification and ask how many hours."
  - "Labor burden is never editable here: return unsupported_reason 'labor_burden'."
  - "When the user states what something costs them (not what to charge), return unsupported_reason 'material_cost'."
  - "Every work-item command names its target by job_item_id from the snapshot."

Run the planner tests. Expected: PASS.

- [ ] **Step 4: Live test file**

`tests/test_maple_routing_live.py` runs every `expected.json` routing row and the #17 and #22 planner phrasings through the real classifier (`OrchestratorAgent()` with the LLM) and the real planner. It is skipped without `openai_api_key`, like `test_maple_crud_coverage.py:141`.

```python
pytestmark = pytest.mark.llm_e2e

@pytest.mark.parametrize("row", [r for r in json.loads((DATA / "expected.json").read_text()) if r["layer"] == "routing"])
def test_expected_routing_holds_with_the_live_classifier(row): ...
```
The planner cases:
- "set the hours on grading to 2 days" → `needs_clarification`;
- "our supplier raised prices, make the pavers $5" → `UpdateMaterial(price=5)`;
- "the pavers cost us $4" → `material_cost`;
- "set the labor burden to 20%" → `labor_burden`.

- [ ] **Step 5: Run live once**

```bash
./run_tests.sh tests/test_maple_routing_live.py tests/test_maple_edit_planner_llm.py -m llm_e2e -q
```
Expected: pass. For each live failure:
- **The prompt is at fault:** fix the prompt and rerun. At most two prompt iterations.
- **Otherwise:** record `Task 11: Ruling: live <phrase> -> <result>`. Whether that ruling is acceptable is Simon's call; list it in the final message.

- [ ] **Step 6: Prompt review**

Run `/agent-prompt-review platform/prompts/estimate_edit_planner.py and platform/agents/estimate/edit_planner.py`. Fix any CRITICAL or HIGH.

---

### Task 12: Docs and the review contract

**Files:**
- Modify: `.claude/commands/code-review.md` (root repo)
- Modify: `CLAUDE.md` (root repo), Maple section
- Modify: `documentation/development/maple-phrasing-reference.md`
- Modify: `documentation/development/code-review-followups.md`

TDD does not apply here (documentation).

- [ ] **Step 1: Back up** (`t12`).

- [ ] **Step 2: The `/code-review` contract**

In `.claude/commands/code-review.md`, add a section `## Maple phrasing findings` after Step 4, containing spec §6's quoted block verbatim, including "Known findings are not new".

In Step 5, "Numbered, Severity-Tiered Findings", add:
> Before numbering, drop every finding already logged in `code-review-followups.md` (same place, same cause) into an unnumbered **Already tracked** list with its follow-up number.

- [ ] **Step 3: `CLAUDE.md`**

In the Maple section, replace the "**One write path for Maple estimate edits:**" paragraph's first sentence group with:
> Rule-handled phrasings are the written list in `agents/estimate/command_grammar.py` — core entries plus ported detectors. A rule that isn't there doesn't exist; everything else goes to the edit planner or the classifier. Whether a message answers an open Estimate question is decided only by `routers/agent_helpers/open_question.py`. Writes to a guessed target that isn't fresh (`agents/estimate/target_freshness.py`) ask first. `tests/test_maple_routing_snapshot.py` shows every routing change; update it with `UPDATE_MAPLE_SNAPSHOT=1` only after reviewing the diff.

Keep the rest of the paragraph (the executor, the planner flag, markup, and the refusals).

- [ ] **Step 4: Follow-ups**

In `code-review-followups.md`:
- mark #627, 628, 629, 630, 632, 633, 634, 636, 637, 642, 643, 646, 647, 648, 649, 650, 652, 656, 657 and 658 as `~~…~~ — RESOLVED 2026-09-25 (routing convergence: replaced by the command list and snapshot rows)`, in the file's resolved style;
- mark #653 resolved (Task 3);
- in entry #4's size tables, update the rows for `crud_handlers.py`, `orchestrator/service.py`, `routers/agents.py`, `NewEstimateWithActivityPage.tsx`, `edit_executor.py` and `work_item_edit_detectors.py` with `wc -l` counts, each with a "2026-09-25 routing convergence" note.

- [ ] **Step 5: Phrasing reference**

Finish §1's rule table (§4 core and ported, one row each, with an example) and the gaps list (⚠️) for phrasings the corpus shows as classifier-only. Update the §12.3 counts from Task 10 and the change log.

---

### Task 13: Gate

- [ ] **Step 1:** Tell Simon the implementation is complete and ask him to run the full suite (`./run_tests.sh` and `npm test`). Do not run it yourself.
- [ ] **Step 2:** After he reports green, he runs `/code-review`, then `/fix-issues <his selection>`. Repeat until a round reports no new findings (spec §2).
- [ ] **Step 3:** Commit and push only on his explicit approval, repo by repo, using the 3maples identity and the Co-Authored-By trailer.

---

## Self-review notes

**Spec coverage**

| Spec section | Task |
|---|---|
| §4 core entries | Task 6 |
| §4.3 ported entries | Task 6 (registry), Task 9 (dispatch) |
| §5.1 | Task 7 |
| §5.2 | Task 8, Task 9 (title first) |
| §5.3 | Task 9 (agent), Task 10 (orchestrator), Task 11 (planner prompt) |
| §5.4 | Task 1 |
| §5.5 | Task 0, extended in Tasks 6 and 7 |
| §6 | Task 12 |
| §8.2 | Tasks 1–3 |
| §8.3 | Tasks 4–5 |
| §8.4 | Task 12 |

**Known deviations**, each recorded as a ruling when executed:
- **Typed values.** No Estimate record awaits a typed value (only description, note and work-item name, which are all free text), so `decide` has no typed-value branch. YAGNI; spec §5.1 lists it for completeness.
- **Grammar and decisions snapshot layers** start in Tasks 6 and 7 (spec §5.5 as amended).
