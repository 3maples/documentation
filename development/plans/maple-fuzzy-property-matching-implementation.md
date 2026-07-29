# Maple Fuzzy Property Matching — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Maple resolve a property the user names by typo, re-wording, or a `{name} - {street}` composite when linking it to an estimate — confirming before it writes.

**Architecture:** A third, fallback-only tier inside `_resolve_property_address` scores candidates with the repo's existing difflib matcher. Because it fires only where the two substring tiers already returned nothing, no resolution that works today changes. A fuzzy hit on the *write* path stashes a pending confirmation record that pins the resolved property id; the *read* path just names what it matched and proceeds.

**Tech Stack:** Python 3.14, FastAPI, Beanie ODM, pytest. `agents/fuzzy_utils.py` (difflib `SequenceMatcher`) — no new dependency.

**Spec:** `documentation/development/plans/maple-fuzzy-property-matching.md`

## Global Constraints

- **TDD is mandatory.** Write the failing test first, run it, watch it fail for the right reason, then implement. (CLAUDE.md)
- **Never commit or push without fresh explicit approval from Simon.** Each task's commit step is a *request*, not an action — stop and ask. Approval for one commit never carries to the next.
- After any `.py` edit under `platform/`, run `./run_mypy.sh` and `./run_ruff.sh` scoped to the touched subtree. The project sits at zero errors for both; fix new ones in the same task.
- **Do not run the full test suite.** Run only the test files covering what you changed. Simon triggers full runs.
- Local MongoDB must be up before tests: `cd platform && ./scripts/start_test_mongo.sh` (idempotent).
- Fuzzy threshold is the `fuzzy_utils` default **0.65**. Do not introduce a second threshold.
- US spellings throughout (labor, color, behavior).
- All work is in `platform/` unless a task says otherwise. `documentation/` is a separate git repo — commit it separately.

---

### Task 1: Fuzzy tier in the property resolver

Adds tier 3 to `_resolve_property_address` and two new result keys. No user-visible change yet — callers still treat a fuzzy hit exactly like an exact one. That is intentional: this task is provable in isolation.

**Files:**
- Modify: `platform/agents/estimate/crud_helpers.py` (module imports; new constants near the class; `_resolve_property_address` ~line 396-458)
- Test: `platform/tests/test_maple_estimate_field_edits.py` (new class after `TestPropertyResolutionCompositeLabel`, ~line 1050)

**Interfaces:**
- Consumes: `agents.fuzzy_utils.fuzzy_best_matches(query, candidates, text_extractors, threshold=0.65, max_results=5) -> List[FuzzyMatch]`, where `FuzzyMatch` is a `NamedTuple(item, score, matched_text)`.
- Produces: `_resolve_property_address(company_oid, address) -> Dict` with keys `property_id`, `matches`, `error` (all unchanged) **plus** `fuzzy: bool` and `score: float`. Tasks 3 and 4 read `fuzzy` and `score`. Also produces module-level `PROPERTY_FUZZY_THRESHOLD: float` and `_PROPERTY_FUZZY_EXTRACTORS: List[Callable[[Any], str]]`.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_maple_estimate_field_edits.py`:

```python
class TestPropertyFuzzyResolution:
    """Tier 3: when neither substring tier matches, fall back to difflib
    similarity so typos and re-worded addresses still resolve. Fires ONLY
    when tiers 1-2 found nothing, so no existing resolution changes.
    """

    def _patch_properties(self, monkeypatch, properties):
        from models.property import Property

        class _Cursor:
            async def to_list(self):
                return list(properties)

        monkeypatch.setattr(Property, "find", classmethod(lambda cls, *a, **k: _Cursor()))

    def _prop(self, name, street, city=""):
        return type("P", (), {
            "id": f"id-{name}", "name": name, "street": street,
            "city": city, "prov_state": "", "postal_zip": "",
        })()

    def _catalog(self):
        return [
            self._prop("Primavera", "153 Asharoken Ave", "Northport"),
            self._prop("Northside Depot", "9 Elm St"),
            self._prop("Maple Ridge", "12 Oak Rd"),
        ]

    def _resolve(self, monkeypatch, query, catalog=None):
        from beanie import PydanticObjectId

        agent = _agent(monkeypatch)
        self._patch_properties(monkeypatch, catalog or self._catalog())
        return asyncio.run(agent._resolve_property_address(
            PydanticObjectId("507f1f77bcf86cd799439011"), query,
        ))

    @pytest.mark.parametrize("query,expected_name", [
        # The mangled string from the 2026-07-28 bug report. Fuzzy is a safety
        # net for this, NOT the fix — the extraction fix is load-bearing.
        ("of this estimate to Primavera - 153 Asharoken Ave", "Primavera"),
        ("Primavera, 153 Asharoken Avenue", "Primavera"),
        ("primavara", "Primavera"),              # name typo
        ("153 Ashroken Ave", "Primavera"),       # street typo
        ("Maple Rige", "Maple Ridge"),           # name typo, different property
    ])
    def test_near_miss_resolves_via_fuzzy(self, monkeypatch, query, expected_name):
        result = self._resolve(monkeypatch, query)
        assert len(result["matches"]) == 1
        assert result["matches"][0].name == expected_name
        assert result["fuzzy"] is True
        assert result["score"] >= 0.65

    @pytest.mark.parametrize("query", [
        "Bogus Place",
        "the property",
        "somewhere else entirely",
    ])
    def test_noise_still_finds_nothing(self, monkeypatch, query):
        result = self._resolve(monkeypatch, query)
        assert result["matches"] == []
        assert result["fuzzy"] is False

    def test_exact_hit_never_reaches_fuzzy_tier(self, monkeypatch):
        result = self._resolve(monkeypatch, "Primavera")
        assert len(result["matches"]) == 1
        assert result["fuzzy"] is False, "tier 1 must short-circuit before fuzzy"
        assert result["score"] == 0.0

    def test_composite_hit_never_reaches_fuzzy_tier(self, monkeypatch):
        result = self._resolve(monkeypatch, "Primavera - 153 Asharoken Ave")
        assert len(result["matches"]) == 1
        assert result["fuzzy"] is False, "tier 2 must short-circuit before fuzzy"

    def test_ambiguous_fuzzy_returns_all_candidates(self, monkeypatch):
        catalog = [self._prop("Maple Ridge", "12 Oak Rd"),
                   self._prop("Maple Rigde North", "14 Oak Rd")]
        result = self._resolve(monkeypatch, "Maple Rdge", catalog)
        assert len(result["matches"]) > 1, "near-ties must NOT be silently collapsed"
        assert result["property_id"] is None
        assert result["fuzzy"] is True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py -k TestPropertyFuzzyResolution -q
```

Expected: FAIL — `KeyError: 'fuzzy'` on the parametrized cases, and the noise/exact cases failing on the missing key too.

- [ ] **Step 3: Add the import and the module-level constants**

In `platform/agents/estimate/crud_helpers.py`, add to the existing module-level import block:

```python
from agents.fuzzy_utils import fuzzy_best_matches
```

Then, immediately **above** `class CrudParsingMixin:` (currently line 137), add:

```python
# Fuzzy property resolution (tier 3 of _resolve_property_address).
# 0.65 is the repo-wide fuzzy_utils default — measured signal for real
# answers lands at 0.71-0.98 and noise below 0.52, so the gap is wide.
PROPERTY_FUZZY_THRESHOLD = 0.65

# Mirrors the Property agent's extractor set (agents/property/service.py:855).
# The combined name+street extractor is the load-bearing one: it is what makes
# a "{name} - {street}" composite score 0.71 instead of 0.31.
_PROPERTY_FUZZY_EXTRACTORS = [
    lambda p: _safe_str(getattr(p, "name", "")),
    lambda p: _safe_str(getattr(p, "street", "")),
    lambda p: (
        f"{_safe_str(getattr(p, 'name', ''))} "
        f"{_safe_str(getattr(p, 'street', ''))}"
    ).strip(),
    lambda p: (
        f"{_safe_str(getattr(p, 'street', ''))}, "
        f"{_safe_str(getattr(p, 'city', ''))} "
        f"{_safe_str(getattr(p, 'prov_state', ''))} "
        f"{_safe_str(getattr(p, 'postal_zip', ''))}"
    ).strip(),
]
```

- [ ] **Step 4: Add tier 3 to the resolver**

In `_resolve_property_address`, change the result initializer (currently line 426) from:

```python
        result: Dict[str, Any] = {"property_id": None, "matches": [], "error": None}
```

to:

```python
        result: Dict[str, Any] = {
            "property_id": None, "matches": [], "error": None,
            "fuzzy": False, "score": 0.0,
        }
```

Then replace the tier-2 block (currently lines 450-452):

```python
        # Tier 2 only when the strict tier came up empty (see docstring).
        if not hits:
            hits = reverse_hits
```

with:

```python
        # Tier 2 only when the strict tier came up empty (see docstring).
        if not hits:
            hits = reverse_hits

        # Tier 3 — fuzzy similarity, only when BOTH substring tiers came up
        # empty. This ordering is the safety property: every resolution that
        # worked before this tier existed is unchanged, because tier 3 only
        # runs where the resolver already returned "no match".
        if not hits:
            fuzzy_results = fuzzy_best_matches(
                lowered,
                properties,
                _PROPERTY_FUZZY_EXTRACTORS,
                threshold=PROPERTY_FUZZY_THRESHOLD,
            )
            if fuzzy_results:
                result["fuzzy"] = True
                result["score"] = fuzzy_results[0].score
                hits = [match.item for match in fuzzy_results]
```

- [ ] **Step 5: Extend the docstring**

In the same method, after the tier-2 bullet, add a third:

```
        3. *fallback, only when tiers 1-2 find nothing* — difflib similarity
           via ``fuzzy_best_matches`` at ``PROPERTY_FUZZY_THRESHOLD``, scoring
           name / street / "name street" / full address. Catches typos and
           re-worded addresses. Callers MUST branch on the returned ``fuzzy``
           flag: a fuzzy hit is a guess, and the write path confirms it with
           the user before saving (see ``pending_property_link.py``).
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py -q
```

Expected: PASS — the whole file, including the pre-existing `TestPropertyResolutionCompositeLabel` cases (they pin that tiers 1-2 still win).

- [ ] **Step 7: Gates**

```bash
cd platform && ./run_mypy.sh agents/estimate && ./run_ruff.sh agents/estimate
```

Expected: both clean. If ruff flags the lambdas in `_PROPERTY_FUZZY_EXTRACTORS` (E731 is not in the enabled ruleset, so it should not), do **not** add a `noqa` — restructure as a module-level function returning the list.

- [ ] **Step 8: Request approval to commit**

Stop and ask Simon. Do not run this yourself until he says yes:

```bash
cd platform && git add agents/estimate/crud_helpers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: fuzzy fallback tier for estimate property resolution"
```

---

### Task 2: Pending property-link confirmation handler

A self-contained state machine. Nothing writes its key yet (Task 3 does), so this task ships inert — but fully tested.

**Files:**
- Create: `platform/routers/agent_helpers/pending_property_link.py`
- Test: `platform/tests/test_agent_helpers_pending_property_link.py` (new)

**Interfaces:**
- Consumes: `_resolve_property_address` from Task 1, called as `agent._resolve_property_address(company_oid, text)`, reading `error` / `matches` / `property_id` / `fuzzy` / `score`.
- Produces:
  - `PENDING_PROPERTY_LINK_CONFIRMATION_KEY = "pending_property_link_confirmation"` — imported by Tasks 3 and 4.
  - `async def handle_pending_property_link_confirmation(message: str, context_payload: Dict[str, Any], agent: Any) -> Optional[Dict[str, Any]]` — returns the 11-key envelope when it owns the turn, `None` when the main pipeline should take over.
  - Record shape written by Task 3: `{"estimate_id": str, "estimate_label": str, "property_id": str, "property_label": str, "score": float}`.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_agent_helpers_pending_property_link.py`:

```python
"""Pending fuzzy property-link confirmation (spec: maple-fuzzy-property-matching.md §4)."""
from __future__ import annotations

import asyncio

import pytest

from routers.agent_helpers import pending_property_link as ppl

KEY = ppl.PENDING_PROPERTY_LINK_CONFIRMATION_KEY


class _Prop:
    def __init__(self, pid, name, street=""):
        self.id, self.name, self.street = pid, name, street


class _FakeAgent:
    """Stands in for EstimateAgent — only _resolve_property_address is used."""

    def __init__(self, resolution=None):
        self.resolution = resolution or {
            "property_id": None, "matches": [], "error": None,
            "fuzzy": False, "score": 0.0,
        }
        self.calls = []

    async def _resolve_property_address(self, company_oid, text):
        self.calls.append(text)
        return self.resolution


@pytest.fixture
def linked(monkeypatch):
    """Capture what gets written to the Estimate, without a DB."""
    captured = {}

    class _Est:
        id = "est-oid-1"

        async def set(self, values):
            captured.update(values)

    async def _get(_id):
        captured["loaded_id"] = _id
        return _Est()

    monkeypatch.setattr(ppl.Estimate, "get", staticmethod(_get))
    return captured


def _ctx():
    return {
        KEY: {
            "estimate_id": "est-oid-1",
            "estimate_label": "EST-DF5EBD1D",
            "property_id": "665f00000000000000000001",
            "property_label": "Primavera - 153 Asharoken Ave",
            "score": 0.711,
        },
        "company_id": "507f1f77bcf86cd799439011",
    }


def _run(message, ctx, agent=None):
    return asyncio.run(ppl.handle_pending_property_link_confirmation(
        message, ctx, agent or _FakeAgent(),
    ))


class TestNoPendingRecord:
    def test_returns_none_without_record(self):
        assert _run("anything", {}) is None


class TestAffirmative:
    def test_links_pinned_property_without_re_resolving(self, linked):
        ctx = _ctx()
        agent = _FakeAgent()
        result = _run("yes", ctx, agent)
        assert result is not None
        assert str(linked.get("property")) == "665f00000000000000000001"
        assert agent.calls == [], "confirmation must reuse the pinned id, not re-resolve"
        assert KEY not in ctx
        assert "Primavera - 153 Asharoken Ave" in result["response"]


class TestNegative:
    def test_declines_and_leaves_unlinked(self, linked):
        ctx = _ctx()
        result = _run("no", ctx)
        assert result is not None
        assert "property" not in linked, "a decline must not write"
        assert KEY not in ctx
        assert "unlinked" in result["response"].lower()


class TestPivot:
    def test_releases_on_unrelated_request(self):
        ctx = _ctx()
        assert _run("show me my estimates", ctx) is None
        assert KEY not in ctx


class TestCorrection:
    """The trap: handing a bare property name back to the classifier
    reproduces the 2026-07-28 bug (it comes back as create_estimate).
    A correction MUST be resolved inside this handler."""

    def test_corrected_name_resolves_inside_handler(self, linked):
        ctx = _ctx()
        agent = _FakeAgent({
            "property_id": "665f00000000000000000002",
            "matches": [_Prop("665f00000000000000000002", "Maple Ridge")],
            "error": None, "fuzzy": False, "score": 0.0,
        })
        result = _run("no, I meant Maple Ridge", ctx, agent)
        assert result is not None, "must own the turn — never hand a bare name to the classifier"
        assert agent.calls, "the corrected text must be re-resolved"
        assert str(linked.get("property")) == "665f00000000000000000002"
        assert KEY not in ctx

    def test_corrected_name_that_is_also_fuzzy_re_asks_with_new_candidate(self):
        ctx = _ctx()
        agent = _FakeAgent({
            "property_id": "665f00000000000000000002",
            "matches": [_Prop("665f00000000000000000002", "Maple Ridge")],
            "error": None, "fuzzy": True, "score": 0.81,
        })
        result = _run("Maple Rige", ctx, agent)
        assert result["needs_clarification"] is True
        assert ctx[KEY]["property_id"] == "665f00000000000000000002"
        assert ctx[KEY]["property_label"] == "Maple Ridge"

    def test_unresolvable_correction_keeps_record_armed(self):
        ctx = _ctx()
        result = _run("Bogus Place", ctx, _FakeAgent())
        assert result["needs_clarification"] is True
        assert KEY in ctx, "an unresolvable answer must not drop the user out of the flow"

    def test_ambiguous_correction_lists_options_and_stays_armed(self):
        ctx = _ctx()
        agent = _FakeAgent({
            "property_id": None,
            "matches": [_Prop("a", "Maple Ridge"), _Prop("b", "Maple Ridge North")],
            "error": None, "fuzzy": True, "score": 0.79,
        })
        result = _run("Maple Rdge", ctx, agent)
        assert result["needs_clarification"] is True
        assert "Maple Ridge North" in result["response"]
        assert KEY in ctx
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_agent_helpers_pending_property_link.py -q
```

Expected: FAIL at collection — `ModuleNotFoundError: No module named 'routers.agent_helpers.pending_property_link'`.

- [ ] **Step 3: Create the module**

Create `platform/routers/agent_helpers/pending_property_link.py`:

```python
"""Pending fuzzy property-link confirmation.

Owns the ``PENDING_PROPERTY_LINK_CONFIRMATION_KEY`` state machine. When the
Estimate Agent resolves a property only *fuzzily* on the link path, it does
not write — it stashes a record pinning the resolved property id and asks the
user to confirm. This handler owns the following turn.

Deliberately NOT the existing ``PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY``
machine: that one replays ``original_message`` after confirmation, which here
would re-run the same ambiguous lookup and loop forever. Pinning the id means
an affirmative reply links directly, with no re-resolution.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from agents.fuzzy_utils import fuzzy_disclaimer
from agents.orchestrator.intents import (
    ACTION_HINTS,
    DOMAIN_HINTS,
    _match_first_hint,
    is_analytics_or_help_query,
    resolve_intent,
)
from models import Estimate
from routers.agent_helpers.text_helpers import is_affirmative_text, is_negative_text
from routers.estimates import parse_object_id

PENDING_PROPERTY_LINK_CONFIRMATION_KEY = "pending_property_link_confirmation"


def _envelope(
    *,
    message: str,
    response: str,
    result: Optional[Dict[str, Any]],
    context_payload: Dict[str, Any],
    success: bool = True,
    needs_clarification: bool = False,
    clarifying_question: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Standard 11-key envelope for every handler return."""
    return {
        "success": success,
        "query": message,
        "intent": "update_estimate",
        "agent": "Estimate Agent",
        "confidence": 1.0,
        "needs_clarification": needs_clarification,
        "clarifying_question": clarifying_question,
        "response": response,
        "result": result,
        "error": error,
        "context": context_payload,
    }


def _property_label(prop: Any, fallback: str) -> str:
    name = str(getattr(prop, "name", "") or "").strip()
    street = str(getattr(prop, "street", "") or "").strip()
    return name or street or fallback


def _is_pivot(message: str) -> bool:
    """True when the message is clearly a different request, not an answer.

    The ``property`` domain is exempt: a property name IS the expected answer
    here, so "the Downtown property" must never read as a pivot.
    """
    lowered = message.lower()
    action = _match_first_hint(lowered, ACTION_HINTS)
    domain = _match_first_hint(lowered, DOMAIN_HINTS)
    new_intent = resolve_intent(action, domain)
    if new_intent and new_intent != "update_estimate" and domain != "property":
        return True
    return is_analytics_or_help_query(message)


async def _write_link(estimate_id: str, property_id: str) -> bool:
    """Set ``Estimate.property``. Returns False when the estimate is gone."""
    estimate = await Estimate.get(estimate_id) if estimate_id else None
    if estimate is None:
        return False
    await estimate.set({
        "property": parse_object_id(property_id, "property ID"),
        "updated_at": datetime.now(timezone.utc),
    })
    return True


def _confirm_prompt(property_label: str, estimate_label: str) -> str:
    return (
        f"{fuzzy_disclaimer(property_label)} "
        f"Please confirm and I'll link it to estimate {estimate_label}."
    )


async def handle_pending_property_link_confirmation(
    message: str, context_payload: Dict[str, Any], agent: Any
) -> Optional[Dict[str, Any]]:
    """Drive the fuzzy property-link confirmation.

    Returns the envelope when this handler owns the turn, or ``None`` when the
    main pipeline should take over (no pending record, or a clear pivot).
    """
    pending = context_payload.get(PENDING_PROPERTY_LINK_CONFIRMATION_KEY)
    if not isinstance(pending, dict):
        return None

    estimate_id = str(pending.get("estimate_id") or "").strip()
    estimate_label = str(pending.get("estimate_label") or "").strip() or "this estimate"
    property_id = str(pending.get("property_id") or "").strip()
    property_label = str(pending.get("property_label") or "").strip() or "that property"
    normalized = str(message or "").strip()

    if is_negative_text(normalized):
        context_payload.pop(PENDING_PROPERTY_LINK_CONFIRMATION_KEY, None)
        return _envelope(
            message=message,
            response=f"Okay, I've left estimate {estimate_label} unlinked.",
            result={"operation": "update_estimate", "linked": False},
            context_payload=context_payload,
        )

    if is_affirmative_text(normalized):
        context_payload.pop(PENDING_PROPERTY_LINK_CONFIRMATION_KEY, None)
        if not await _write_link(estimate_id, property_id):
            return _envelope(
                message=message,
                response=f"I couldn't find estimate {estimate_label} anymore.",
                result=None,
                context_payload=context_payload,
                success=False,
                error="Estimate not found.",
            )
        return _envelope(
            message=message,
            response=f"I've linked estimate {estimate_label} to {property_label}.",
            result={
                "operation": "update_estimate",
                "estimate_id": estimate_label,
                "field": "property",
                "value": property_id,
            },
            context_payload=context_payload,
        )

    if _is_pivot(normalized):
        context_payload.pop(PENDING_PROPERTY_LINK_CONFIRMATION_KEY, None)
        return None

    # Anything else is a CORRECTED property answer. Resolve it here — never
    # hand a bare property name back to the classifier, which would answer it
    # as a brand-new create request (the 2026-07-28 bug).
    company_oid = str(context_payload.get("company_id") or "").strip()
    resolution = await agent._resolve_property_address(company_oid, normalized)

    if resolution.get("error"):
        return _envelope(
            message=message,
            response=(
                "I couldn't reach the properties database just now. "
                "Please try again in a moment."
            ),
            result={"operation": "update_estimate", "linked": False},
            context_payload=context_payload,
            needs_clarification=True,
            clarifying_question="Would you like to try again?",
        )

    matches = resolution.get("matches") or []

    if len(matches) == 0:
        prompt = _confirm_prompt(property_label, estimate_label)
        return _envelope(
            message=message,
            response=f"I couldn't find a property matching \"{normalized}\". {prompt}",
            result={"operation": "update_estimate", "linked": False},
            context_payload=context_payload,
            needs_clarification=True,
            clarifying_question="Which property did you mean?",
        )

    if len(matches) > 1:
        options = "; ".join(
            f"({i + 1}) {_property_label(p, normalized)}"
            for i, p in enumerate(matches[:5])
        )
        return _envelope(
            message=message,
            response=(
                f"I found more than one property matching \"{normalized}\": "
                f"{options}. Which one did you mean?"
            ),
            result={"operation": "update_estimate", "linked": False},
            context_payload=context_payload,
            needs_clarification=True,
            clarifying_question="Which property did you mean?",
        )

    new_label = _property_label(matches[0], normalized)
    new_id = str(resolution.get("property_id") or "")

    if resolution.get("fuzzy"):
        pending.update({
            "property_id": new_id,
            "property_label": new_label,
            "score": float(resolution.get("score") or 0.0),
        })
        context_payload[PENDING_PROPERTY_LINK_CONFIRMATION_KEY] = pending
        prompt = _confirm_prompt(new_label, estimate_label)
        return _envelope(
            message=message,
            response=prompt,
            result={"operation": "update_estimate", "linked": False},
            context_payload=context_payload,
            needs_clarification=True,
            clarifying_question=prompt,
        )

    context_payload.pop(PENDING_PROPERTY_LINK_CONFIRMATION_KEY, None)
    if not await _write_link(estimate_id, new_id):
        return _envelope(
            message=message,
            response=f"I couldn't find estimate {estimate_label} anymore.",
            result=None,
            context_payload=context_payload,
            success=False,
            error="Estimate not found.",
        )
    return _envelope(
        message=message,
        response=f"I've linked estimate {estimate_label} to {new_label}.",
        result={
            "operation": "update_estimate",
            "estimate_id": estimate_label,
            "field": "property",
            "value": new_id,
        },
        context_payload=context_payload,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_agent_helpers_pending_property_link.py -q
```

Expected: PASS, all cases.

- [ ] **Step 5: Gates**

```bash
cd platform && ./run_mypy.sh routers/agent_helpers && ./run_ruff.sh routers/agent_helpers tests/test_agent_helpers_pending_property_link.py
```

Expected: both clean.

- [ ] **Step 6: Request approval to commit**

Stop and ask Simon:

```bash
cd platform && git add routers/agent_helpers/pending_property_link.py tests/test_agent_helpers_pending_property_link.py
git commit -m "feat: pending property-link confirmation state machine"
```

---

### Task 3: Link handler confirms on a fuzzy match, and the router wires it up

Tasks 1 and 2 are inert until this one. Handler change and router wiring ship **together** — splitting them would put a question on `main` that nothing can answer.

**Files:**
- Modify: `platform/agents/estimate/crud_handlers.py` (`_handle_update_estimate_property_link`, insert after the estimate load at ~line 2928)
- Modify: `platform/routers/agents.py` (imports ~line 61; handler chain ~line 1110)
- Modify: `platform/routers/agent_helpers/optional_follow_up.py` (`_rearm_on_unresolved`)
- Test: `platform/tests/test_maple_estimate_field_edits.py`

**Interfaces:**
- Consumes: `PENDING_PROPERTY_LINK_CONFIRMATION_KEY` and `handle_pending_property_link_confirmation` (Task 2); `resolution["fuzzy"]` and `resolution["score"]` (Task 1).
- Produces: nothing new for later tasks.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_maple_estimate_field_edits.py`:

```python
class TestFuzzyLinkConfirmation:
    """A fuzzy property match on the WRITE path must ask before saving —
    the house rule for fuzzy + mutation (delegate_estimate_ops.py:104)."""

    def _agent_with_resolution(self, monkeypatch, resolution, saved):
        agent = _agent(monkeypatch)

        class _Est:
            id = "est-oid-1"
            estimate_id = "EST-DF5EBD1D"
            property = None

            async def save(self):
                saved["property"] = self.property

        async def _load(query, company_id, code, context):
            return _Est(), None

        async def _resolve(company_oid, identifier):
            return resolution

        monkeypatch.setattr(agent, "_load_estimate_for_update", _load)
        monkeypatch.setattr(agent, "_resolve_property_address", _resolve)
        return agent

    def _prop(self, name):
        return type("P", (), {"id": "prop-oid-1", "name": name, "street": ""})()

    def test_fuzzy_match_asks_and_does_not_write(self, monkeypatch):
        from routers.agent_helpers.pending_property_link import (
            PENDING_PROPERTY_LINK_CONFIRMATION_KEY,
        )

        saved, ctx = {}, {"active_estimate_code": "EST-DF5EBD1D"}
        agent = self._agent_with_resolution(monkeypatch, {
            "property_id": "prop-oid-1",
            "matches": [self._prop("Primavera - 153 Asharoken Ave")],
            "error": None, "fuzzy": True, "score": 0.711,
        }, saved)

        result = asyncio.run(agent._handle_update_estimate(
            "set the property of this estimate to primavara",
            "507f1f77bcf86cd799439011", ctx,
        ))
        assert result["needs_clarification"] is True
        assert "Primavera - 153 Asharoken Ave" in result["response"]
        assert saved == {}, "a fuzzy guess must never write"
        pending = result["context"][PENDING_PROPERTY_LINK_CONFIRMATION_KEY]
        assert pending["property_id"] == "prop-oid-1"
        assert pending["estimate_label"] == "EST-DF5EBD1D"

    def test_exact_match_still_links_in_one_turn(self, monkeypatch):
        from routers.agent_helpers.pending_property_link import (
            PENDING_PROPERTY_LINK_CONFIRMATION_KEY,
        )

        saved, ctx = {}, {"active_estimate_code": "EST-DF5EBD1D"}
        agent = self._agent_with_resolution(monkeypatch, {
            "property_id": "prop-oid-1",
            "matches": [self._prop("Primavera")],
            "error": None, "fuzzy": False, "score": 0.0,
        }, saved)

        result = asyncio.run(agent._handle_update_estimate(
            "set the property of this estimate to Primavera",
            "507f1f77bcf86cd799439011", ctx,
        ))
        assert saved["property"] == "prop-oid-1"
        assert result["needs_clarification"] is False
        assert PENDING_PROPERTY_LINK_CONFIRMATION_KEY not in result["context"]


class TestFuzzyConfirmNotEatenByFollowUp:
    """The re-arm fix (2026-07-28) restores the create-estimate follow-up
    whenever the delegate asks a question — including the fuzzy confirm.
    Without the guard, the user's "yes" hits the follow-up machine first and
    re-asks "Which property should I link…?" forever."""

    def test_rearm_skipped_when_property_confirm_pending(self):
        from routers.agent_helpers import optional_follow_up as _ofu
        from routers.agent_helpers.pending_property_link import (
            PENDING_PROPERTY_LINK_CONFIRMATION_KEY,
        )

        ctx = {
            _ofu.PENDING_OPTIONAL_FOLLOW_UP_KEY: {
                "agent": "Estimate Agent", "operation": "create_estimate",
                "update_intent": "update_estimate", "entity_type": "estimate",
                "entity_label": "EST-DF5EBD1D", "field": "property",
                "question": "Would you like me to link this estimate to a property now?",
                "stage": _ofu.OPTIONAL_FOLLOW_UP_STAGE_COLLECT_VALUE,
            },
        }

        class _Proc:
            async def process(self, message, context=None):
                return {
                    "success": True, "needs_clarification": True,
                    "clarifying_question": "Please confirm.",
                    "response": "I believe you are looking for 'Primavera'.",
                    "result": {}, "intent": "update_estimate",
                    "agent": "Estimate Agent",
                    "context": {PENDING_PROPERTY_LINK_CONFIRMATION_KEY: {
                        "estimate_id": "est-oid-1", "estimate_label": "EST-DF5EBD1D",
                        "property_id": "prop-oid-1", "property_label": "Primavera",
                        "score": 0.711,
                    }},
                }

        result = asyncio.run(_ofu.handle_pending_optional_follow_up(
            "primavara", ctx, lambda name: _Proc(),
        ))
        assert PENDING_PROPERTY_LINK_CONFIRMATION_KEY in result["context"]
        assert _ofu.PENDING_OPTIONAL_FOLLOW_UP_KEY not in result["context"], (
            "only one flow may own the turn — the property confirmation wins"
        )


class TestRouterOrdering:
    def test_property_confirm_runs_before_the_follow_up_machines(self):
        """Source-order guard: the property-link confirmation must be
        dispatched before either follow-up handler in the endpoint chain."""
        import inspect

        from routers import agents as agents_router

        src = inspect.getsource(agents_router.orchestrate_agent_endpoint)
        i_prop = src.index("handle_pending_property_link_confirmation")
        i_legacy = src.index("handle_pending_estimate_follow_up")
        i_generic = src.index("handle_pending_optional_follow_up")
        assert i_prop < i_legacy < i_generic
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py -k "TestFuzzyLinkConfirmation or TestFuzzyConfirmNotEatenByFollowUp or TestRouterOrdering" -q
```

Expected: FAIL — the fuzzy case writes instead of asking; the re-arm test finds the follow-up key still present; the ordering test raises `ValueError: substring not found`.

- [ ] **Step 3: Gate the write in the link handler**

In `platform/agents/estimate/crud_handlers.py`, inside `_handle_update_estimate_property_link`, insert **after** the estimate load (currently lines 2926-2928, ending `return err`) and **before** `target.property = resolved_property_id`:

```python
        # A fuzzy resolution is a GUESS — confirm before writing. Stash the
        # already-resolved property id so the confirmation turn links directly
        # instead of re-running this ambiguous lookup. Imported inside the
        # function: agents/ -> routers/ at module scope risks an import cycle.
        if link_op == "link" and resolution_was_fuzzy:
            from routers.agent_helpers.pending_property_link import (
                PENDING_PROPERTY_LINK_CONFIRMATION_KEY,
            )
            from agents.fuzzy_utils import fuzzy_disclaimer

            context[PENDING_PROPERTY_LINK_CONFIRMATION_KEY] = {
                "estimate_id": str(getattr(target, "id", "") or ""),
                "estimate_label": code,
                "property_id": str(resolved_property_id),
                "property_label": resolved_address_label,
                "score": resolution_score,
            }
            clarify = (
                f"{fuzzy_disclaimer(resolved_address_label)} "
                f"Please confirm and I'll link it to estimate {code}."
            )
            return self._crud_envelope(
                query=query,
                intent="update_estimate",
                probability=probability,
                response=clarify,
                needs_clarification=True,
                clarifying_question=clarify,
                result={"operation": "update_estimate", "linked": False},
                context=context,
            )
```

This needs three values carried down from the resolution block above. In the `link_op == "link"` branch, initialize alongside the existing locals:

```python
        resolved_property_id = None
        resolved_address_label = ""
        resolution_was_fuzzy = False
        resolution_score = 0.0
```

and in the single-match path (currently lines 2922-2923) replace:

```python
            resolved_property_id = resolution["property_id"]
            resolved_address_label = identifier
```

with:

```python
            resolved_property_id = resolution["property_id"]
            resolution_was_fuzzy = bool(resolution.get("fuzzy"))
            resolution_score = float(resolution.get("score") or 0.0)
            # On a fuzzy hit the user's text was only an approximation — echo
            # the catalog's own label back so they confirm against real data.
            if resolution_was_fuzzy:
                matched = matches[0]
                resolved_address_label = (
                    _safe_str(getattr(matched, "name", ""))
                    or _safe_str(getattr(matched, "street", ""))
                    or identifier
                )
            else:
                resolved_address_label = identifier
```

- [ ] **Step 4: Guard the re-arm**

In `platform/routers/agent_helpers/optional_follow_up.py`, at the top of `_rearm_on_unresolved`, replace:

```python
    if not delegated.get("needs_clarification"):
        return
```

with:

```python
    if not delegated.get("needs_clarification"):
        return
    # A fuzzy property-link confirmation owns the next turn on its own. If we
    # re-armed here too, the user's "yes" would hit this machine first and
    # re-ask "Which property should I link…?" forever. Same precedent as the
    # legacy follow-up handler deferring to this one. Local import: the
    # module-level cycle runs through routers/estimates.
    from routers.agent_helpers.pending_property_link import (
        PENDING_PROPERTY_LINK_CONFIRMATION_KEY,
    )

    delegated_context = delegated.get("context")
    if isinstance(delegated_context, dict) and delegated_context.get(
        PENDING_PROPERTY_LINK_CONFIRMATION_KEY
    ):
        context_payload.pop(PENDING_OPTIONAL_FOLLOW_UP_KEY, None)
        return
```

- [ ] **Step 5: Wire the handler into the endpoint**

In `platform/routers/agents.py`, add to the import block (alphabetically, after the `optional_follow_up` import at ~line 61):

```python
from routers.agent_helpers.pending_property_link import (
    PENDING_PROPERTY_LINK_CONFIRMATION_KEY,  # noqa: F401  # re-exported for tests
    handle_pending_property_link_confirmation,
)
```

Then in `orchestrate_agent_endpoint`, insert **immediately before** the `handle_pending_estimate_follow_up` call (currently line 1110):

```python
        pending_property_link_result = await handle_pending_property_link_confirmation(
            message, merged_context, get_estimate_agent()
        )
        if pending_property_link_result is not None:
            return await _finalize_result(pending_property_link_result)
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py tests/test_agent_helpers_pending_property_link.py tests/test_agent_helpers_optional_follow_up.py tests/test_orchestrator_endpoint.py -q
```

Expected: PASS. `TestFollowUpSurvivesUnresolvedValue` (2026-07-28) must still pass — the re-arm still fires when no property confirmation is pending.

- [ ] **Step 7: Gates**

```bash
cd platform && ./run_mypy.sh agents/estimate routers && ./run_ruff.sh agents/estimate routers
```

Expected: both clean.

- [ ] **Step 8: Request approval to commit**

Stop and ask Simon:

```bash
cd platform && git add agents/estimate/crud_handlers.py routers/agents.py routers/agent_helpers/optional_follow_up.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: confirm fuzzy property matches before linking an estimate"
```

---

### Task 4: List filter discloses its fuzzy match

Reads get no confirmation gate — they name what matched and proceed.

**Files:**
- Modify: `platform/agents/estimate/crud_handlers.py` (`_handle_list_estimates`, ~lines 969-1015 and ~1032)
- Test: `platform/tests/test_maple_estimate_field_edits.py`

**Interfaces:**
- Consumes: `resolution["fuzzy"]` (Task 1); the existing `property_constraint_label` local, which already drives the `Estimates for '{label}':` lead-in at line 1358.
- Produces: nothing for later tasks.

- [ ] **Step 1: Write the failing test**

Append to `platform/tests/test_maple_estimate_field_edits.py`:

```python
class TestFuzzyListFilterDisclosure:
    """A read needs no confirmation gate — but it must say WHICH property it
    matched, so a wrong fuzzy hit is visible rather than silent."""

    def test_fuzzy_address_filter_names_the_match(self, monkeypatch):
        from models import Estimate

        agent = _agent(monkeypatch)
        prop = type("P", (), {"id": "prop-oid-1", "name": "Primavera",
                              "street": "153 Asharoken Ave"})()

        async def _resolve(company_oid, identifier):
            return {"property_id": "prop-oid-1", "matches": [prop],
                    "error": None, "fuzzy": True, "score": 0.98}

        # _handle_list_estimates calls Estimate.find(*filters) directly
        # (crud_handlers.py:1229) and then .limit(...).to_list(). Stub the
        # whole chain so the test needs no DB. Zero estimates is fine — the
        # assertion is about the property named in the response, and the
        # empty-result branch uses the same property_constraint_label.
        class _Cursor:
            def sort(self, *a, **k):
                return self

            def limit(self, *a, **k):
                return self

            async def to_list(self):
                return []

            async def count(self):
                return 0

        monkeypatch.setattr(agent, "_resolve_property_address", _resolve)
        monkeypatch.setattr(Estimate, "find", classmethod(lambda cls, *a, **k: _Cursor()))

        result = asyncio.run(agent._handle_list_estimates(
            "show me estimates for 153 Ashroken Ave",
            "507f1f77bcf86cd799439011", {},
        ))
        assert "Primavera" in result["response"], (
            "a fuzzy read must name the property it resolved to"
        )
```

Note the empty-result branch (`'{property_constraint_label}' doesn't have any estimates yet.`, line 1327-1331) also reads `property_constraint_label`, so this test passes through the same label plumbing as the populated case.

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py -k TestFuzzyListFilterDisclosure -q
```

Expected: FAIL — the response is the generic empty/list text with no property named.

- [ ] **Step 3: Capture the fuzzy label**

In `_handle_list_estimates`, in the `if address_requested:` block, replace the single-match tail (currently line 1015):

```python
            property_filter_id = resolution["property_id"]
```

with:

```python
            property_filter_id = resolution["property_id"]
            # A fuzzy address hit is an approximation — surface the catalog's
            # own label so a wrong guess is visible in the answer rather than
            # silently changing what the user sees. Reads don't gate on it.
            if resolution.get("fuzzy") and matches:
                address_fuzzy_label = (
                    _safe_str(getattr(matches[0], "name", ""))
                    or _safe_str(getattr(matches[0], "street", ""))
                )
```

and initialize it just above `address_requested = self._extract_property_address(query)` (line 970):

```python
        address_fuzzy_label = ""
```

- [ ] **Step 4: Feed it into the existing lead-in**

Immediately **after** `property_constraint_label = ""` (currently line 1032), add:

```python
        # A fuzzy address match reuses the constraint-label lead-in
        # ("Estimates for 'X':") so the resolved property is named. Set only
        # for fuzzy hits — exact address filters keep their current wording.
        if address_fuzzy_label:
            property_constraint_label = address_fuzzy_label
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py tests/test_estimate_agent.py -q
```

Expected: PASS, including the existing list-estimates tests (exact address filters keep their wording).

- [ ] **Step 6: Gates**

```bash
cd platform && ./run_mypy.sh agents/estimate && ./run_ruff.sh agents/estimate
```

- [ ] **Step 7: Request approval to commit**

Stop and ask Simon:

```bash
cd platform && git add agents/estimate/crud_handlers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: name the property a fuzzy estimate-list filter resolved to"
```

---

### Task 5: End-to-end replay and documentation

The unit tests cover each seam; this proves the whole conversation. The phrasing reference is the human-readable source of truth and CLAUDE.md requires it move in the same change as any Maple phrasing behavior.

**Files:**
- Test: `platform/tests/test_maple_estimate_field_edits.py`
- Modify: `documentation/development/maple-phrasing-reference.md` (§1.6 table, §10.4 table, change log, "Last updated")

**Interfaces:**
- Consumes: everything from Tasks 1-4.
- Produces: nothing.

- [ ] **Step 1: Write the end-to-end replay test**

Append to `platform/tests/test_maple_estimate_field_edits.py`:

```python
class TestFuzzyLinkEndToEnd:
    """create → 'yes' → misspelled property → 'yes' → linked.
    The final 'yes' is the turn that loops if the router ordering or the
    re-arm guard is wrong."""

    def test_full_conversation_links_the_property(self, monkeypatch):
        from routers.agent_helpers import optional_follow_up as _ofu
        from routers.agent_helpers import pending_property_link as _ppl

        agent = _agent(monkeypatch)
        prop = type("P", (), {"id": "prop-oid-1", "name": "Primavera",
                              "street": "153 Asharoken Ave"})()
        written = {}

        class _Est:
            id = "est-oid-1"
            estimate_id = "EST-DF5EBD1D"
            property = None

            async def save(self):
                written["property"] = self.property

            async def set(self, values):
                written.update(values)

        async def _load(query, company_id, code, context):
            return _Est(), None

        async def _resolve(company_oid, identifier):
            return {"property_id": "prop-oid-1", "matches": [prop],
                    "error": None, "fuzzy": True, "score": 0.889}

        monkeypatch.setattr(agent, "_load_estimate_for_update", _load)
        monkeypatch.setattr(agent, "_resolve_property_address", _resolve)
        monkeypatch.setattr(_ppl.Estimate, "get", staticmethod(lambda _id: _as_async(_Est())))

        ctx = {
            _ofu.PENDING_OPTIONAL_FOLLOW_UP_KEY: {
                "agent": "Estimate Agent", "operation": "create_estimate",
                "update_intent": "update_estimate", "entity_type": "estimate",
                "entity_label": "EST-DF5EBD1D", "field": "property",
                "question": "Would you like me to link this estimate to a property now?",
                "stage": _ofu.OPTIONAL_FOLLOW_UP_STAGE_CONFIRM,
            },
            "active_estimate_code": "EST-DF5EBD1D",
            "company_id": "507f1f77bcf86cd799439011",
        }

        # Turn 1: "yes" -> asks which property
        r1 = asyncio.run(_ofu.handle_pending_optional_follow_up(
            "yes", ctx, lambda name: agent))
        assert r1["needs_clarification"] is True

        # Turn 2: misspelled name -> fuzzy confirm, nothing written yet
        r2 = asyncio.run(_ofu.handle_pending_optional_follow_up(
            "primavara", ctx, lambda name: agent))
        ctx = r2["context"]
        assert _ppl.PENDING_PROPERTY_LINK_CONFIRMATION_KEY in ctx
        assert written == {}, "fuzzy guess must not write"

        # Turn 3: "yes" -> the confirmation handler owns it and links
        r3 = asyncio.run(_ppl.handle_pending_property_link_confirmation(
            "yes", ctx, agent))
        assert r3 is not None, "the confirmation handler must own this turn"
        assert str(written.get("property")) == "prop-oid-1"
        assert "Primavera" in r3["response"]
```

Add this helper near the top of the file, beside `_agent`, if no equivalent exists:

```python
def _as_async(value):
    """Wrap a value in an awaitable, for monkeypatching async classmethods."""
    async def _inner():
        return value
    return _inner()
```

- [ ] **Step 2: Run it to verify it fails, then passes**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py -k TestFuzzyLinkEndToEnd -q
```

If Tasks 1-4 are complete this may pass immediately. **If it does, prove it is a real test** by temporarily reverting the Task 3 Step 4 re-arm guard and confirming turn 3 loops instead of linking. Restore the guard afterwards.

- [ ] **Step 3: Update the phrasing reference change log**

In `documentation/development/maple-phrasing-reference.md`, set `**Last updated:** 2026-07-28` (already correct) and add a change-log entry directly beneath the existing 2026-07-28 one:

```markdown
**2026-07-28 (b) — Fuzzy property matching on the estimate link (§1.6, §10.4)**
- **Near-misses now resolve.** `_resolve_property_address` gained a third, fallback-only tier using the repo's shared difflib matcher (`agents/fuzzy_utils.fuzzy_best_matches`, threshold 0.65) scoring name / street / **name+street** / full address. Typos (`primavara`, `153 Ashroken Ave`), re-wordings (`Primavera, 153 Asharoken Avenue`) and composite labels resolve; noise (`Bogus Place`, `the property`) still doesn't. The tier fires only where the two substring tiers found nothing, so no existing resolution changed.
- **A fuzzy match on a WRITE confirms first**, per the house rule for fuzzy + mutation. New `pending_property_link_confirmation` record pins the resolved property id so the confirming turn links directly rather than re-running the ambiguous lookup. A corrected name ("no, I meant Maple Ridge") is re-resolved *inside* the handler — handing a bare property name back to the classifier is what produced the "Sure, I'll help you create an estimate!" bug.
- **A fuzzy match on a READ discloses instead of gating** — "Estimates for 'Primavera':".
- Tests: `tests/test_agent_helpers_pending_property_link.py`, and `TestPropertyFuzzyResolution` / `TestFuzzyLinkConfirmation` / `TestFuzzyConfirmNotEatenByFollowUp` / `TestFuzzyLinkEndToEnd` in `tests/test_maple_estimate_field_edits.py`.
```

- [ ] **Step 4: Update the §1.6 and §10.4 tables**

In §1.6, append to the `set the property of estimate {EST} to {property}` row's status note:

```
 **2026-07-28 (b)** — a near-miss ("primavara") now resolves fuzzily and asks for confirmation before linking.
```

In the §10.4 table, add a row after the `{name} - {street}` composite row:

```markdown
| misspelled or re-worded property (`primavara`, `153 Ashroken Ave`) | fuzzy-resolve, then confirm before linking | ✅ rule *(**2026-07-28 (b)** — tier 3 of `_resolve_property_address` + `pending_property_link_confirmation`. Reads disclose instead of confirming.)* |
```

- [ ] **Step 5: Run the full affected set**

```bash
cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py tests/test_agent_helpers_pending_property_link.py tests/test_agent_helpers_optional_follow_up.py tests/test_agent_helpers_pending_estimate_follow_up.py tests/test_estimate_agent.py tests/test_orchestrator_endpoint.py tests/test_maple_crud_coverage.py -q
```

Expected: PASS.

- [ ] **Step 6: Request approval to commit (two repos)**

Stop and ask Simon. `platform/` and `documentation/` are separate git repos and need separate commits:

```bash
cd platform && git add tests/test_maple_estimate_field_edits.py
git commit -m "test: end-to-end fuzzy property link confirmation"
```

```bash
cd documentation && git add development/maple-phrasing-reference.md
git commit -m "docs: record fuzzy property matching in the phrasing reference"
```

---

## Self-review notes

- **Every score in Task 1's tests was measured, not guessed.** Run against `fuzzy_utils` with the Task 1 extractor set: `of this estimate to Primavera - 153 Asharoken Ave` → Primavera 0.711; `primavara` → 0.889; `153 Ashroken Ave` → 0.980; `Maple Rige` (3-property catalog) → Maple Ridge 0.952, single hit; `Maple Rdge` (against `Maple Ridge` + `Maple Rigde North`) → two candidates at 0.952 / 0.833, which is what the ambiguity test asserts; `Bogus Place` / `the property` / `somewhere else entirely` → no match. If the implementer sees different numbers, the extractor set has drifted from Task 1 Step 3 — fix that rather than relaxing the threshold.
- **Spec coverage:** §1 resolver tier → Task 1. §2 scoring/extractors → Task 1 Step 3. §3 link UX → Task 3; list UX → Task 4. §4 pending record incl. the corrected-answer rule → Task 2. §5 turn ordering + re-arm guard → Task 3 Steps 4-5. Spec testing section → distributed across every task plus Task 5. Out-of-scope items are not implemented anywhere.
- **Type consistency:** `PENDING_PROPERTY_LINK_CONFIRMATION_KEY` and the five record fields (`estimate_id`, `estimate_label`, `property_id`, `property_label`, `score`) are written in Task 3 Step 3 and read in Task 2 — spellings match. `resolution["fuzzy"]` / `["score"]` defined in Task 1 are consumed identically in Tasks 3 and 4.
- **Seams verified against source, not assumed:** `_handle_list_estimates` calls `Estimate.find(*filters)` directly (`crud_handlers.py:1229`) — there is no repository-style helper, so Task 4's test stubs the cursor chain (`sort`/`limit`/`to_list`/`count`). `_handle_update_estimate` dispatches to `_handle_update_estimate_property_link` at `crud_handlers.py:2377-2379`, which is why Task 3's tests can drive the public handler. `_crud_envelope` returns `context` unmodified (`crud_helpers.py:559`), which is how the pending record survives the turn.
- **Import cycles:** `agents/` importing `routers/` at module scope is cycle-prone (`agents/__init__` → `routers/__init__` → `routers/agents` → `agents`). Task 3 Step 3 and the Task 3 Step 4 guard therefore both use function-local imports, with the reason in a comment. `pending_property_link.py` itself imports `routers.estimates` at module scope, matching `pending_estimate_follow_up.py`, which already does exactly that safely.
