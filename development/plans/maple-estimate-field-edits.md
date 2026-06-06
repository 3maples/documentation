# Maple Estimate Field-Edit & Details Gaps — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Maple correctly handle five estimate phrasings landscapers actually type — update the estimate-level description, link a property by name, append to notes, show full details (with timestamps/ID), and finish the post-creation "link to a property?" follow-up — including informal phrasing and title/anaphora references.

**Architecture:** Five mostly-independent slices over the existing Estimate agent + orchestrator. A shared title-or-code resolver (Task 2) unblocks the three update-path gaps (description, notes, linking). The multi-turn follow-up (Task 7) extends the *existing* `optional_follow_up` state machine rather than building a new one. Routing changes live in `agents/orchestrator/service.py`; handler logic in `agents/estimate/crud_handlers.py` + `crud_helpers.py`.

**Tech Stack:** FastAPI · Beanie/MongoDB · pytest (TestClient + pure-unit) · the rule-based orchestrator (`OrchestratorAgent(use_llm=False)`).

**Reference:** `documentation/development/maple-phrasing-reference.md` §1.2, §1.6, §1.10, §9.4 — flip the ⚠️ rows there to ✅ as each task lands (Task 9).

**Conventions (from CLAUDE.md):**
- TDD is mandatory: write the failing test first, watch it fail, implement minimally, watch it pass.
- After every `.py` change: `./run_mypy.sh <touched subtree>` and `./run_ruff.sh <touched subtree>` must be clean. Full-project `./run_mypy.sh` + `./run_ruff.sh` before final commit-prep.
- Run only the tests related to your change (`./run_tests.sh tests/<file>.py`); the user triggers the full suite.
- Commits need explicit user approval each time — the `git commit` steps below are checkpoints; **pause and ask** before running them. Commit author is already configured (`3maples <admin@3maples.ai>`). Co-author trailer per CLAUDE.md.
- US spelling in all user-facing strings ("labor"); the code domain stays `labour`.

---

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `agents/orchestrator/service.py` | `_classify_specific_phrasings` — add an estimate-level field-edit fast-path so description/notes/property edits route to `update_estimate` (not `update_property`/help) | 1, 6 |
| `agents/estimate/crud_handlers.py` | `_resolve_estimate_code_or_title` (new); estimate description detector + handler (new); notes-cue broadening; link-verb broadening; dispatcher wiring | 2, 4, 5, 6 |
| `agents/estimate/crud_helpers.py` | `_build_estimate_details_text` / `_estimate_summary_payload` enrichment (timestamps, id, property, description, notes); focused single-field lead | 3 |
| `routers/agent_helpers/optional_follow_up.py` | Register the Estimate `create_estimate`→`property` follow-up combo (spec + prompt + synthetic message) | 7 |
| `tests/test_maple_estimate_field_edits.py` (new) | All routing + pure-detector + resolver + render + follow-up unit tests for this plan | 1–7 |
| `documentation/development/maple-phrasing-reference.md` | Flip ⚠️ → ✅ rows; bump "Last updated" | 9 |

---

## Task 1: Orchestrator routing — estimate-level field-edit fast-path

**Why:** "set the property of estimate Spring Cleaning to Bob Residential" contains the word **property** (a Property domain hint) and "estimate Spring Cleaning" has no EST-code, so today it can misroute to `update_property` (or to the field-targeted matcher whose `FIELD_TO_DOMAIN` lacks `description`/`property`). We add a high-confidence rule in `_classify_specific_phrasings` (which runs before `_match_possessive_or_field_targeted` and `_classify_via_action_domain`) that routes any estimate-referencing edit of `description`/`notes`/`property` to `update_estimate`. Work-item edits already short-circuit earlier in the same method, so estimate-level edits won't steal them.

**Files:**
- Modify: `agents/orchestrator/service.py` — inside `_classify_specific_phrasings`, after the work-item blocks and before the template blocks (around line 763, before the `use/apply template` rule).
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing routing tests**

Create `tests/test_maple_estimate_field_edits.py`:

```python
import asyncio

from agents.orchestrator.service import OrchestratorAgent


def _route(text: str):
    """Resolve a message through the rule-based orchestrator and return its intent."""
    result = asyncio.run(OrchestratorAgent(use_llm=False).process(text))
    return result.get("intent")


class TestEstimateFieldEditRouting:
    def test_update_description_by_code_routes_to_update_estimate(self):
        assert _route(
            'update the description of estimate EST-0042 with the following: "new desc"'
        ) == "update_estimate"

    def test_update_description_by_title_routes_to_update_estimate(self):
        assert _route(
            'change the description on the Spring Cleaning quote to "new desc"'
        ) == "update_estimate"

    def test_set_property_of_estimate_routes_to_update_estimate_not_update_property(self):
        # "property" is a Property domain hint — must NOT win here.
        assert _route(
            "set the property of estimate Spring Cleaning to Bob Residential"
        ) == "update_estimate"

    def test_notes_on_estimate_routes_to_update_estimate(self):
        assert _route(
            'for estimate Spring Cleaning, add to the notes the following: "call before 9am"'
        ) == "update_estimate"

    def test_this_quote_is_for_property_routes_to_update_estimate(self):
        assert _route("this quote is for the Bob Residential property") == "update_estimate"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateFieldEditRouting -v`
Expected: failures — at least `test_set_property_of_estimate_routes_to_update_estimate_not_update_property` returns `update_property`, and the title-based ones may return `help`/`update_property`.

- [ ] **Step 3: Add the routing rule**

In `agents/orchestrator/service.py`, inside `_classify_specific_phrasings`, immediately before the `# "use/apply template X ..."` block (≈ line 763), insert:

```python
        # Estimate-level field edits — description / notes / property link.
        # These reference an estimate (by EST-code, the word "estimate"/"quote"
        # /"bid"/"proposal", or "this/the estimate") AND target one of the
        # estimate-level editable fields. We must claim them here because:
        #   - "property" is a Property domain hint and would otherwise route to
        #     update_property (the estimate, not the property, is the subject);
        #   - title-referenced estimates carry no EST-code for action+domain to
        #     anchor on.
        # Work-item edits are handled by the earlier blocks in this method, so
        # they never reach here.
        _estimate_ref = re.search(
            r"\b(?:est[-_][a-z0-9][a-z0-9\-_]*|estimate|quote|bid|proposal)\b",
            normalized,
        )
        _estimate_field_edit = re.search(
            r"\b(?:set|change|update|edit|modify|add|append|attach|reword|describe|"
            r"link|attach|tie|connect|associate|put|assign)\b",
            normalized,
        ) and re.search(
            r"\b(?:description|write[\s-]?up|overview|notes?|propert\w*|job\s*site)\b",
            normalized,
        )
        if _estimate_ref and _estimate_field_edit:
            return ("update_estimate", INTENT_TO_AGENT["update_estimate"], 0.9, False, None)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateFieldEditRouting -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Guard against regressions in pure Property/Contact routing**

Run: `./run_tests.sh tests/test_orchestrator_intents.py tests/test_maple_crud_coverage.py -v`
Expected: PASS. If any property phrasing that legitimately mentions "estimate" now misroutes, tighten `_estimate_ref` to require the field token to sit *near* the estimate token; record the failing phrasing and fix before continuing.

- [ ] **Step 6: Gates + commit (pause for approval)**

Run: `./run_mypy.sh agents/orchestrator/service.py && ./run_ruff.sh agents/orchestrator/service.py`
Expected: clean.

```bash
git add agents/orchestrator/service.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: route estimate-level field edits (description/notes/property) to update_estimate"
```

---

## Task 2: Shared title-or-code estimate resolver (update path)

**Why:** `_handle_get_estimate` resolves an estimate by code → "latest" → title (`crud_handlers.py:1520-1542`), but every *update* handler resolves by code only (`_resolve_estimate_code`). This is the single root cause behind the title-reference gaps in description, notes, and linking. Add one async helper the update handlers call.

**Files:**
- Modify: `agents/estimate/crud_handlers.py` — add `_resolve_estimate_code_or_title` near `_resolve_estimate_by_title` (≈ after line 1505).
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_maple_estimate_field_edits.py`:

```python
import pytest

from agents.estimate import service as estimate_service


def _agent(monkeypatch):
    monkeypatch.setattr(estimate_service, "ChatOpenAI", lambda **kwargs: object())
    return estimate_service.EstimateAgent()


class _FakeEstimate:
    def __init__(self, estimate_id):
        self.estimate_id = estimate_id


class TestResolveEstimateCodeOrTitle:
    def test_explicit_code_wins_without_title_lookup(self, monkeypatch):
        agent = _agent(monkeypatch)

        async def _boom(*a, **k):  # title lookup must not be called
            raise AssertionError("title lookup should be skipped when a code is present")

        monkeypatch.setattr(agent, "_resolve_estimate_by_title", _boom)
        code, clarify = asyncio.run(
            agent._resolve_estimate_code_or_title("notes on EST-0042: hi", "c", {}, 0.9)
        )
        assert code == "EST-0042"
        assert clarify is None

    def test_falls_back_to_title_when_no_code(self, monkeypatch):
        agent = _agent(monkeypatch)

        async def _by_title(query, company_id, context, probability):
            return _FakeEstimate("EST-0099")

        monkeypatch.setattr(agent, "_resolve_estimate_by_title", _by_title)
        code, clarify = asyncio.run(
            agent._resolve_estimate_code_or_title(
                'notes on the "Spring Cleaning" estimate: hi', "c", {}, 0.9
            )
        )
        assert code == "EST-0099"
        assert clarify is None

    def test_multi_match_returns_clarification_envelope(self, monkeypatch):
        agent = _agent(monkeypatch)

        async def _by_title(query, company_id, context, probability):
            return {"needs_clarification": True, "response": "which one?"}

        monkeypatch.setattr(agent, "_resolve_estimate_by_title", _by_title)
        code, clarify = asyncio.run(
            agent._resolve_estimate_code_or_title("notes on Spring: hi", "c", {}, 0.9)
        )
        assert code == ""
        assert isinstance(clarify, dict) and clarify["needs_clarification"] is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestResolveEstimateCodeOrTitle -v`
Expected: FAIL — `AttributeError: 'EstimateAgent' object has no attribute '_resolve_estimate_code_or_title'`.

- [ ] **Step 3: Implement the resolver**

In `agents/estimate/crud_handlers.py`, after `_resolve_estimate_by_title` ends (≈ line 1505), add:

```python
    async def _resolve_estimate_code_or_title(
        self,
        query: str,
        company_id: str,
        context: Dict[str, Any],
        probability: float,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Resolve the target estimate code for an UPDATE-path query.

        Order mirrors ``_handle_get_estimate``: explicit EST-code (or
        ``active_estimate_code`` anaphora) → "latest estimate" → title
        substring match.

        Returns ``(code, clarification)``:
          * ``(code, None)``        — resolved to a single estimate
          * ("", clarification)     — title matched multiple estimates;
                                       caller should return the envelope as-is
          * ("", None)              — nothing resolved; caller asks for a code
        """
        code = self._resolve_estimate_code(query, context)
        if code:
            return code, None

        if self._looks_like_latest_estimate_query(query):
            latest = await self._resolve_latest_estimate(company_id)
            if latest is not None:
                return (_safe_str(getattr(latest, "estimate_id", "")) or ""), None

        title_result = await self._resolve_estimate_by_title(
            query, company_id, context, probability
        )
        if isinstance(title_result, dict):
            return "", title_result
        if title_result is not None:
            return (_safe_str(getattr(title_result, "estimate_id", "")) or ""), None
        return "", None
```

> Note: `_resolve_estimate_by_title`'s multi-match envelope uses `intent="get_estimate"`. That's acceptable for now (it only asks "which estimate code?"). If a reviewer objects, parameterize the intent later — out of scope here.

- [ ] **Step 4: Run the test to verify it passes**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestResolveEstimateCodeOrTitle -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Gates + commit (pause for approval)**

Run: `./run_mypy.sh agents/estimate/crud_handlers.py && ./run_ruff.sh agents/estimate/crud_handlers.py`

```bash
git add agents/estimate/crud_handlers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: add title-or-code estimate resolver for update-path handlers"
```

---

## Task 3: Enriched estimate details + single-field leads (item 4)

**Why:** `_build_estimate_details_text` (`crud_helpers.py:446`) renders only Code/Title/Status/Grand total. Users asking "show me everything on Spring Cleaning" / "when was it created?" need `created_at`, `updated_at`, `id`/`estimate_id`, linked property, `description`, `notes`.

**Files:**
- Modify: `agents/estimate/crud_helpers.py` — `_build_estimate_details_text` (≈ 446-454).
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_maple_estimate_field_edits.py`:

```python
import datetime as _dt


class _FullEstimate:
    def __init__(self):
        self.id = "665f1f77bcf86cd799439011"
        self.estimate_id = "EST-0042"
        self.title = "Spring Cleaning"
        self.status = "Draft"
        self.grand_total = 1234.5
        self.description = "Full spring cleanup"
        self.notes = "Customer prefers mornings"
        self.property = None
        self.created_at = _dt.datetime(2026, 5, 1, 9, 0, tzinfo=_dt.timezone.utc)
        self.updated_at = _dt.datetime(2026, 6, 1, 14, 30, tzinfo=_dt.timezone.utc)


class TestEnrichedDetailsText:
    def test_details_text_includes_timestamps_id_and_fields(self, monkeypatch):
        agent = _agent(monkeypatch)
        text = agent._build_estimate_details_text(_FullEstimate())
        assert "EST-0042" in text
        assert "Spring Cleaning" in text
        assert "2026-05-01" in text          # created_at rendered
        assert "2026-06-01" in text          # updated_at rendered
        assert "Full spring cleanup" in text  # description
        assert "Customer prefers mornings" in text  # notes
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEnrichedDetailsText -v`
Expected: FAIL — timestamps/description/notes absent from the rendered text.

- [ ] **Step 3: Enrich the renderer**

Replace `_build_estimate_details_text` in `agents/estimate/crud_helpers.py` with:

```python
    def _build_estimate_details_text(self, estimate) -> str:
        summary = self._estimate_summary_payload(estimate)
        lines = [
            f"Code: {summary['estimate_id'] or '—'}",
            f"Title: {summary['title'] or '—'}",
            f"Status: {summary['status'] or '—'}",
            f"Grand total: {summary['grand_total']:.2f}",
        ]

        def _fmt_dt(value) -> str:
            try:
                return value.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                return _safe_str(value)

        created = getattr(estimate, "created_at", None)
        updated = getattr(estimate, "updated_at", None)
        if created:
            lines.append(f"Created: {_fmt_dt(created)}")
        if updated:
            lines.append(f"Last updated: {_fmt_dt(updated)}")

        description = _safe_str(getattr(estimate, "description", "")).strip()
        if description:
            lines.append(f"Description: {description}")
        notes = _safe_str(getattr(estimate, "notes", "")).strip()
        if notes:
            lines.append(f"Notes: {notes}")

        estimate_id = summary.get("id")
        if estimate_id:
            lines.append(f"ID: {estimate_id}")
        return "\n".join(lines)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEnrichedDetailsText -v`
Expected: PASS.

- [ ] **Step 5: Single-field timestamp leads** (optional within this task; do as a sub-step)

Add a focused-field lead so "when was the Spring Cleaning estimate created?" leads with the date. In `agents/estimate/crud_handlers.py`, in `_handle_get_estimate`, after `target` is loaded and before building the standard details text, detect a focused field and prepend it. Write this test first:

```python
class TestTimestampLead(... )  # see note below
```

> The exact insertion point depends on where `_handle_get_estimate` builds its response (≈ line 1600-1629). Mirror the existing `_GRAND_TOTAL_QUERY_PATTERN` lead-with-value pattern in §1.2: add a `_CREATED_AT_QUERY_PATTERN` / `_UPDATED_AT_QUERY_PATTERN` (e.g. `r"\bwhen\s+(?:was|did).*\b(?:creat|made)\b"` and `r"\bwhen\s+(?:was|did).*\b(?:updat|touch|chang|modif)\b"`) and, when matched, lead the response string with the formatted date. This is a deterministic enhancement; keep it rule-tier. If time-boxed, ship Steps 1-4 first and split the lead into its own commit.

- [ ] **Step 6: Gates + commit (pause for approval)**

Run: `./run_mypy.sh agents/estimate/crud_helpers.py && ./run_ruff.sh agents/estimate/crud_helpers.py`

```bash
git add agents/estimate/crud_helpers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: enrich estimate details with timestamps, id, property, description, notes"
```

---

## Task 4: Estimate-level description update handler (item 1)

**Why:** `Estimate.description` exists, but `_handle_update_estimate` has no description sub-op — the request falls through to the refusal. Work-item description edits are handled by `_detect_work_item_op`; we must detect the **estimate-level** case (no work-item token) and write `Estimate.description`.

**Files:**
- Modify: `agents/estimate/crud_handlers.py` — new `_detect_estimate_description_update`, new `_handle_update_estimate_description`, dispatcher wiring in `_handle_update_estimate`.
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing detector test**

Append:

```python
class TestEstimateDescriptionDetector:
    def test_detects_quoted_description(self, monkeypatch):
        agent = _agent(monkeypatch)
        val = agent._detect_estimate_description_update(
            'update the description of estimate EST-0042 with the following: "Regrade and reseed"'
        )
        assert val == "Regrade and reseed"

    def test_detects_set_form(self, monkeypatch):
        agent = _agent(monkeypatch)
        val = agent._detect_estimate_description_update(
            'set the description of estimate EST-0042 to "New scope text"'
        )
        assert val == "New scope text"

    def test_ignores_work_item_description(self, monkeypatch):
        agent = _agent(monkeypatch)
        # A work-item description edit must NOT be claimed as estimate-level.
        assert agent._detect_estimate_description_update(
            'set the description of work item 1 to "Excavation"'
        ) is None

    def test_ignores_non_description_text(self, monkeypatch):
        agent = _agent(monkeypatch)
        assert agent._detect_estimate_description_update("approve EST-0042") is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateDescriptionDetector -v`
Expected: FAIL — method missing.

- [ ] **Step 3: Implement the detector**

In `agents/estimate/crud_handlers.py`, near `_detect_note_update` (≈ line 300), add module-level patterns and the method. Put the compiled patterns next to the existing `_NOTE_*` patterns (class attributes ≈ 244-272):

```python
    # Estimate-level description edits. The "describe ... as", "write-up",
    # and "overview" synonyms are accepted. Work-item descriptions are
    # excluded by the no-work-item-token guard in the method body.
    _ESTIMATE_DESC_CUES = re.compile(
        r"\b(?:description|write[\s-]?up|overview)\b", re.IGNORECASE
    )
    _ESTIMATE_DESC_QUOTED = re.compile(
        r"(?:description|write[\s-]?up|overview)\b[^\"'\n]*[\"'](?P<value>[^\"']+)[\"']",
        re.IGNORECASE,
    )
    _ESTIMATE_DESC_COLON = re.compile(
        r"(?:description|write[\s-]?up|overview)\b\s*(?:with\s+the\s+following|to|:|->)\s*[:\-]?\s*(?P<value>.+)$",
        re.IGNORECASE,
    )
    _WORK_ITEM_TOKEN = re.compile(
        r"\b(?:work\s*item|job\s*item|scope|line\s*item)\b", re.IGNORECASE
    )
```

Then the method:

```python
    def _detect_estimate_description_update(self, text: str) -> Optional[str]:
        """Return the new estimate-level description value, or ``None``.

        Returns ``None`` when the text references a work item (those are
        handled by ``_detect_work_item_op``) or carries no description cue.
        """
        if not text or not self._ESTIMATE_DESC_CUES.search(text):
            return None
        if self._WORK_ITEM_TOKEN.search(text):
            return None
        match = self._ESTIMATE_DESC_QUOTED.search(text)
        if match:
            value = match.group("value").strip()
            return value or None
        match = self._ESTIMATE_DESC_COLON.search(text)
        if match:
            value = match.group("value").strip().strip("\"'").strip()
            return value or None
        return None
```

- [ ] **Step 4: Run detector test to verify pass**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateDescriptionDetector -v`
Expected: PASS.

- [ ] **Step 5: Write the failing handler test**

Append (monkeypatches the DB load + save):

```python
class TestEstimateDescriptionHandler:
    def test_sets_estimate_description(self, monkeypatch):
        agent = _agent(monkeypatch)
        saved = {}

        class _Est:
            estimate_id = "EST-0042"
            description = "old"
            async def save(self):
                saved["description"] = self.description

        async def _resolve(query, company_id, context, probability):
            return "EST-0042", None

        async def _load(query, company_id, code, context):
            return _Est(), None

        monkeypatch.setattr(agent, "_resolve_estimate_code_or_title", _resolve)
        monkeypatch.setattr(agent, "_load_estimate_for_update", _load)

        result = asyncio.run(
            agent._handle_update_estimate(
                'update the description of estimate EST-0042 with the following: "Regrade and reseed"',
                "507f1f77bcf86cd799439011",
                {},
            )
        )
        assert saved["description"] == "Regrade and reseed"
        assert "EST-0042" in result["response"]
```

- [ ] **Step 6: Run to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateDescriptionHandler -v`
Expected: FAIL — dispatcher returns the generic "What would you like to change?" refusal; `saved` is empty.

- [ ] **Step 7: Implement the handler + wire the dispatcher**

Add the handler method (place near `_handle_update_estimate_notes`, ≈ line 1874):

```python
    async def _handle_update_estimate_description(
        self, query: str, company_id: str, context: Dict[str, Any], value: str
    ) -> Dict[str, Any]:
        """Set the top-level ``Estimate.description`` field."""
        probability = float(context.get("orchestrator_confidence") or 0.9)
        code, clarify = await self._resolve_estimate_code_or_title(
            query, company_id, context, probability
        )
        if clarify is not None:
            return clarify
        if not code:
            return self._crud_envelope(
                query=query,
                intent="update_estimate",
                probability=probability,
                response="Which estimate should I update? Please share the estimate code (e.g. EST-2026-001) or its title.",
                needs_clarification=True,
                clarifying_question="Which estimate?",
                context=context,
            )

        target, err = await self._load_estimate_for_update(query, company_id, code, context)
        if err is not None:
            return err

        target.description = value
        await target.save()
        return self._crud_envelope(
            query=query,
            intent="update_estimate",
            probability=probability,
            response=(
                f"I've updated the description on estimate {code} for you.\n"
                f"Description:\n{value}"
            ),
            result={
                "operation": "update_estimate_description",
                "estimate_id": code,
                "description": value,
            },
            context=context,
        )
```

Wire it into `_handle_update_estimate` — add this block **after** the work-item dispatch and status-transition checks, and **before** the notes block (≈ insert just above line 1707's `note_op = ...`):

```python
        description_value = self._detect_estimate_description_update(query)
        if description_value is not None:
            return await self._handle_update_estimate_description(
                query, company_id, context, description_value,
            )
```

> Ordering rationale: work-item ops are checked first (they own `description of work item N`), so by the time we reach this block any remaining `description` cue is estimate-level. Keep it above notes so a "description" cue never falls into the notes branch.

- [ ] **Step 8: Run handler test to verify pass**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateDescriptionHandler -v`
Expected: PASS.

- [ ] **Step 9: Regression — work-item description still works**

Run: `./run_tests.sh tests/test_maple_work_item_ops.py -v`
Expected: PASS (no estimate-level handler stealing `description of work item N`).

- [ ] **Step 10: Gates + commit (pause for approval)**

Run: `./run_mypy.sh agents/estimate/crud_handlers.py && ./run_ruff.sh agents/estimate/crud_handlers.py`

```bash
git add agents/estimate/crud_handlers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: handle estimate-level description updates via Maple"
```

---

## Task 5: Notes — title resolution + informal cues (item 3)

**Why:** Notes append already works by code (`_handle_update_estimate_notes`), but (a) it resolves by code only — a titled estimate prompts for a code; (b) `_detect_note_update` requires the literal word "note"/"notes", so "jot down", "FYI", "remember", "write down" aren't recognized.

**Files:**
- Modify: `agents/estimate/crud_handlers.py` — broaden `_NOTE_UPDATE_CUES`; swap the resolver in `_handle_update_estimate_notes`.
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing cue test**

Append:

```python
class TestNoteCueBroadening:
    @pytest.mark.parametrize("text,expected", [
        ('jot down on the Spring Cleaning estimate: "call first"', "call first"),
        ('FYI on the Smith job: "gate code 1234"', "gate code 1234"),
        ('remember on this estimate that the dog is friendly', "the dog is friendly"),
    ])
    def test_informal_note_cues_detected(self, monkeypatch, text, expected):
        agent = _agent(monkeypatch)
        detected = agent._detect_note_update(text)
        assert detected is not None
        value, mode = detected
        assert expected in value
        assert mode == "append"
```

- [ ] **Step 2: Run to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestNoteCueBroadening -v`
Expected: FAIL — `_detect_note_update` returns `None` (no "note" word).

- [ ] **Step 3: Broaden the note cues**

In `agents/estimate/crud_handlers.py`, locate `_NOTE_UPDATE_CUES`, `_NOTE_WITH_COLON_SEP`, `_NOTE_WITH_IMPLICIT_TAIL`, and `_NOTE_ADD_VERB_PATTERN` (≈ 244-272). Broaden them so the informal cues count as note triggers and as append verbs. Concretely:
- `_NOTE_UPDATE_CUES` — add `jot`, `fyi`, `remember`, `write down`:
  ```python
  _NOTE_UPDATE_CUES = re.compile(
      r"\b(?:notes?|jot|fyi|remember|write\s+down)\b", re.IGNORECASE
  )
  ```
- Add a colon/implicit body extractor that fires for these cues. Extend `_NOTE_WITH_COLON_SEP` to also match `jot down on ... :`, `fyi on ... :`, and add an implicit "remember ... that <body>" extractor:
  ```python
  _NOTE_WITH_COLON_SEP = re.compile(
      r"(?:notes?|jot\s+down|fyi)\b[^:\n]*:\s*(?P<value>.+)$", re.IGNORECASE
  )
  _NOTE_REMEMBER_TAIL = re.compile(
      r"\bremember\b[^.\n]*?\bthat\b\s+(?P<value>.+)$", re.IGNORECASE
  )
  ```
  Then in `_detect_note_update`, after the existing extractors and before the `if value is None: return None`, add:
  ```python
        if value is None:
            match = self._NOTE_REMEMBER_TAIL.search(text)
            if match:
                value = match.group("value").strip() or None
  ```
- `_NOTE_ADD_VERB_PATTERN` — add the informal verbs so mode defaults to append:
  ```python
  _NOTE_ADD_VERB_PATTERN = re.compile(
      r"\b(?:add|append|attach|jot|tack|write\s+down|fyi|remember)\b", re.IGNORECASE
  )
  ```

> Verify the exact current regex strings before editing — match them precisely. Keep set-mode (`set|change|replace|overwrite|rewrite`) taking precedence over append.

- [ ] **Step 4: Run the cue test to verify pass**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestNoteCueBroadening -v`
Expected: PASS.

- [ ] **Step 5: Swap the resolver for title support**

In `_handle_update_estimate_notes` (≈ line 1890), replace:

```python
        code = self._resolve_estimate_code(query, context)
        if not code:
            return self._crud_envelope(... "Please share the estimate code ..." ...)
```

with:

```python
        code, clarify = await self._resolve_estimate_code_or_title(
            query, company_id, context, probability
        )
        if clarify is not None:
            return clarify
        if not code:
            return self._crud_envelope(
                query=query,
                intent="update_estimate",
                probability=probability,
                response="Which estimate should I update? Please share the estimate code (e.g. EST-2026-001) or its title.",
                needs_clarification=True,
                clarifying_question="Which estimate?",
                context=context,
            )
```

(Keep `probability` defined just above, as it already is.)

- [ ] **Step 6: Write + run the title-resolution handler test**

Append:

```python
class TestNotesByTitle:
    def test_appends_note_resolving_estimate_by_title(self, monkeypatch):
        agent = _agent(monkeypatch)
        saved = {}

        class _Est:
            estimate_id = "EST-0099"
            notes = ""
            async def save(self):
                saved["notes"] = self.notes

        async def _by_title(query, company_id, context, probability):
            return type("E", (), {"estimate_id": "EST-0099"})()

        async def _load(query, company_id, code, context):
            return _Est(), None

        monkeypatch.setattr(agent, "_resolve_estimate_by_title", _by_title)
        monkeypatch.setattr(agent, "_load_estimate_for_update", _load)

        result = asyncio.run(
            agent._handle_update_estimate(
                'for estimate Spring Cleaning, add to the notes the following: "call before 9am"',
                "507f1f77bcf86cd799439011",
                {},
            )
        )
        assert "call before 9am" in saved["notes"]
        assert "EST-0099" in result["response"]
```

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestNotesByTitle -v`
Expected: PASS.

- [ ] **Step 7: Regression**

Run: `./run_tests.sh tests/test_estimate_agent.py tests/test_maple_work_item_ops.py -v`
Expected: PASS.

- [ ] **Step 8: Gates + commit (pause for approval)**

Run: `./run_mypy.sh agents/estimate/crud_handlers.py && ./run_ruff.sh agents/estimate/crud_handlers.py`

```bash
git add agents/estimate/crud_handlers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: support estimate notes by title and informal cues (jot/FYI/remember)"
```

---

## Task 6: Linking — title resolution + relationship phrasings (item 2)

**Why:** The link handler fires on "set ... property" but resolves the estimate by code only, and `_is_property_link_request` only recognizes `link`/`attach`/`set/change/update ... property`. Landscapers say "this quote is for X", "tie it to X", "the job is at <address>".

**Files:**
- Modify: `agents/estimate/crud_handlers.py` — broaden `_LINK_PROPERTY_PATTERN` (and the link-verb fallback) in/around `_is_property_link_request` (≈ 341-358); swap the resolver in `_handle_update_estimate_property_link` (≈ 1943).
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing detector test**

Append:

```python
class TestLinkVerbBroadening:
    @pytest.mark.parametrize("text", [
        "this quote is for the Bob Residential property",
        "tie the estimate to the Bob Residential property",
        "connect the Spring Cleaning quote to Bob Residential",
        "associate EST-0042 with the Bob Residential property",
        "the property for this quote is Bob Residential",
    ])
    def test_relationship_phrasings_detected_as_link(self, monkeypatch, text):
        agent = _agent(monkeypatch)
        assert agent._is_property_link_request(text) == "link"
```

- [ ] **Step 2: Run to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestLinkVerbBroadening -v`
Expected: FAIL — relationship phrasings return `None`.

- [ ] **Step 3: Broaden link detection**

Inspect `_LINK_PROPERTY_PATTERN` (a class attribute used by `_is_property_link_request`). Broaden it to add the relationship verbs and the "is for"/"property for" shapes. Replace its definition with (verify the exact current pattern first and preserve any unlink guard):

```python
    _LINK_PROPERTY_PATTERN = re.compile(
        r"\b(?:link|attach|tie|connect|associate|assign|set|change|update|put)\b[^.?!]*\bpropert",
        re.IGNORECASE,
    )
    _LINK_RELATIONSHIP_PATTERN = re.compile(
        r"\b(?:quote|estimate|bid|proposal|it|this)\b[^.?!]*\bis\s+for\b[^.?!]*\bpropert",
        re.IGNORECASE,
    )
```

Then in `_is_property_link_request`, after the existing `_LINK_PROPERTY_PATTERN` check, add a relationship check and broaden the address fallback verb set:

```python
        if self._LINK_RELATIONSHIP_PATTERN.search(text):
            return "link"
        # "tie/connect/... estimate X to 123 Main St" — verb + address, no
        # literal "property" word.
        if re.search(
            r"\b(?:link|attach|tie|connect|associate|assign)\b", text, re.IGNORECASE
        ) and self._extract_property_address(text):
            return "link"
```

> Keep the unlink check first (it already guards "remove the property"). Confirm "the property for this quote is X" matches — if `_LINK_RELATIONSHIP_PATTERN` doesn't catch the "property for ... is" word order, add a second alternation: `\bpropert\w*\s+for\b[^.?!]*\bis\b`.

- [ ] **Step 4: Run detector test to verify pass**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestLinkVerbBroadening -v`
Expected: PASS. Fix the word-order alternation if "property for ... is" still fails.

- [ ] **Step 5: Swap the resolver in the link handler**

In `_handle_update_estimate_property_link` (≈ line 1943), replace `code = self._resolve_estimate_code(query, context)` and its empty-code guard with the same `_resolve_estimate_code_or_title` pattern used in Tasks 4 and 5 (clarify passthrough + "code or title" prompt).

- [ ] **Step 6: Write + run the by-title link handler test**

Append (mirror `TestNotesByTitle`; monkeypatch `_resolve_estimate_by_title`, `_load_estimate_for_update`, and `_extract_property_name` to return a known property, then assert the estimate's `property` field is set and saved). Run:

`./run_tests.sh tests/test_maple_estimate_field_edits.py -k "Link" -v`
Expected: PASS.

> The property-resolution internals (`_extract_property_name` / `_extract_property_address` / the property lookup) already exist and are out of scope — monkeypatch them in the test so this task stays focused on estimate resolution + verb detection.

- [ ] **Step 7: Regression**

Run: `./run_tests.sh tests/test_estimate_agent.py tests/test_maple_crud_coverage.py -v`
Expected: PASS — especially that plain Property CRUD ("create a new property", "show properties in Toronto") is unaffected.

- [ ] **Step 8: Gates + commit (pause for approval)**

Run: `./run_mypy.sh agents/estimate/crud_handlers.py && ./run_ruff.sh agents/estimate/crud_handlers.py`

```bash
git add agents/estimate/crud_handlers.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: link estimates to properties by title and relationship phrasings"
```

---

## Task 7: Multi-turn "link to a property?" follow-up (item 5)

**Why:** A full `optional_follow_up` state machine already exists (`routers/agent_helpers/optional_follow_up.py` + `delegate_generic.py`) for Contact-email / Property-contact / Material-size offers. The Estimate Agent's create path emits the property follow-up question (`extraction_helpers.build_optional_follow_up`, surfaced in `service.py:907`) but **isn't in the `get_optional_follow_up_spec` allowlist**, so no pending record is persisted and "Yes, link it to Bob Residential" is dropped. Register the estimate combo.

**Files:**
- Modify: `routers/agent_helpers/optional_follow_up.py` — `get_optional_follow_up_spec` (specs map, line 103-129), `build_optional_follow_up_prompt` (line 46-61), `build_optional_follow_up_update_message` (line 64-86).
- Verify: the estimate create response flows through the spec-persistence step. `delegate_generic.py` persists the spec, but estimate creation is multi-turn (gathering). Confirm whether the final create response passes through `delegate_generic`, `delegate_create_estimate`, or `estimate_gathering`; if not, persist the spec there too.
- Verify: `active_estimate_code` is set in context on creation (so the synthetic "set the property of this estimate to X" resolves via anaphora). There's already `active_*_name` for other agents — check `service.py` ≈ 935 where `optional_follow_up` and active context are written.
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1: Write the failing spec/prompt/message tests**

Append:

```python
from routers.agent_helpers import optional_follow_up as ofu


class TestEstimateOptionalFollowUp:
    def test_spec_registered_for_estimate_property(self):
        spec = ofu.get_optional_follow_up_spec(
            "Estimate Agent",
            "create_estimate",
            {"field": "property", "question": "Would you like me to link this estimate to a property now?"},
            {"active_estimate_code": "EST-0042"},
        )
        assert spec is not None
        assert spec["update_intent"] == "update_estimate"
        assert spec["entity_type"] == "estimate"
        assert spec["field"] == "property"

    def test_prompt_for_estimate_property(self):
        prompt = ofu.build_optional_follow_up_prompt(
            {"agent": "Estimate Agent", "field": "property", "entity_label": "EST-0042"}
        )
        assert "propert" in prompt.lower()

    def test_synthetic_message_for_estimate_property(self):
        msg = ofu.build_optional_follow_up_update_message(
            {"agent": "Estimate Agent", "field": "property"}, "Bob Residential"
        )
        assert msg is not None
        assert "Bob Residential" in msg
        assert "propert" in msg.lower()
```

- [ ] **Step 2: Run to verify it fails**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateOptionalFollowUp -v`
Expected: FAIL — `get_optional_follow_up_spec` returns `None`; prompt/message hit the generic fallback.

- [ ] **Step 3: Register the estimate combo**

In `get_optional_follow_up_spec`'s `specs` dict (line 103-129), add:

```python
        ("Estimate Agent", "create_estimate", "property"): {
            "update_intent": "update_estimate",
            "entity_label_key": "active_estimate_code",
            "entity_type": "estimate",
        },
```

In `build_optional_follow_up_prompt` (line 46-61), add before the final `return`:

```python
    if agent_name == "Estimate Agent" and field == "property":
        return f"Which property should I link estimate '{entity_label}' to?"
```

In `build_optional_follow_up_update_message` (line 64-86), add before the final `return`:

```python
    if agent_name == "Estimate Agent" and field == "property":
        return f"set the property of this estimate to {normalized_value}"
```

- [ ] **Step 4: Run to verify it passes**

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py::TestEstimateOptionalFollowUp -v`
Expected: PASS.

> Note: the synthetic message "set the property of this estimate to X" relies on `active_estimate_code` in context. `handle_pending_optional_follow_up` forces `orchestrator_intent="update_estimate"` (line 290) before delegating, and the link handler now resolves via code/anaphora (Task 6 + `_resolve_estimate_code` reads `active_estimate_code`). Confirm `active_estimate_code` is populated on the create turn (Step 5).

- [ ] **Step 5: Verify create-path persistence + active code (integration)**

Read `agents/estimate/service.py` ≈ 900-940 and `routers/agent_helpers/delegate_create_estimate.py` / `estimate_gathering.py`. Confirm two things:
1. After a successful create whose `optional_follow_up.field == "property"`, the response path calls `get_optional_follow_up_spec` and writes `PENDING_OPTIONAL_FOLLOW_UP_KEY` into the returned context (this is what `delegate_generic.py` does at lines 60-75). If the estimate create response does NOT pass through `delegate_generic`, replicate that persistence block in the estimate create path.
2. The create response sets `context["active_estimate_code"]` to the new estimate's code.

Write an integration test using the FastAPI `client` fixture (mirror `test_estimate_agent_returns_optional_follow_up_and_active_title` in `tests/test_estimate_agent.py`): create an estimate with no property, assert the response context carries `pending_optional_follow_up` with `field="property"` and `active_estimate_code` set. Then post "Yes, link it to <existing property>" and assert the estimate is linked.

Run: `./run_tests.sh tests/test_maple_estimate_field_edits.py -k "FollowUp or follow_up" -v`
Expected: PASS. If persistence was missing, add it and re-run.

- [ ] **Step 6: Gates + commit (pause for approval)**

Run: `./run_mypy.sh routers/agent_helpers/optional_follow_up.py && ./run_ruff.sh routers/agent_helpers/optional_follow_up.py`
(plus any create-path file you touched in Step 5)

```bash
git add routers/agent_helpers/optional_follow_up.py tests/test_maple_estimate_field_edits.py
git commit -m "feat: finish post-creation estimate property-link follow-up"
```

---

## Task 8 (stretch): Estimate synonyms + job-name reference

**Why:** Surfaced while brainstorming variants — `bid`/`proposal` aren't recognized as "estimate", and "the Smith job" / "Bob's quote" means resolving via the linked customer/property name, not the title. Lower priority; ship Tasks 1-7 first.

**Files:**
- Modify: `agents/orchestrator/intents.py` (DOMAIN_HINTS — add `bid`, `proposal`); `agents/estimate/crud_handlers.py` (`_extract_title_from_query` / a new customer-name → estimate resolver).
- Test: `tests/test_maple_estimate_field_edits.py`

- [ ] **Step 1:** Write a routing test asserting `_route("show me everything on the Smith proposal")` and `"... bid"` resolve to `get_estimate`. Run, watch fail.
- [ ] **Step 2:** Add `bid`, `proposal` to the estimate entry in `DOMAIN_HINTS` (verify the synonym list location — `quote` is already there). Run, watch pass.
- [ ] **Step 3:** Write a test for job-name resolution ("notes on the Smith job: ...") that resolves the estimate via its linked property/contact name. Implement a `_resolve_estimate_by_job_name` that, when title lookup misses, resolves a property/contact by name → finds estimates linked to it (mirror the §1.8 cross-resource joins). Wire it as a final fallback inside `_resolve_estimate_code_or_title`.
- [ ] **Step 4:** Gates + commit (pause for approval).

> If job-name resolution proves ambiguous (multiple estimates per property), return the existing multi-match clarification envelope rather than guessing.

---

## Task 9: Flip the reference-doc statuses + final gates

**Files:**
- Modify: `documentation/development/maple-phrasing-reference.md`

- [ ] **Step 1:** In §1.2, §1.6, §1.10, §9.4, flip the ⚠️ gap rows implemented above to ✅ rule (leave Task 8 rows ⚠️ if not done). Update each row's note to point at the new handler/method names. Add a dated change-log entry at the top and bump "Last updated".
- [ ] **Step 2:** Run the Maple coverage matrix to regenerate the live gap report:
  `./run_tests.sh tests/test_maple_crud_coverage.py`
  Expected: PASS; `tests/reports/maple_crud_gap_report.md` regenerates.
- [ ] **Step 3:** Full-project gates before commit-prep:
  `./run_mypy.sh && ./run_ruff.sh`
  Expected: zero errors (the project sits at zero for both).
- [ ] **Step 4:** Run the full new test file + the touched neighbors:
  `./run_tests.sh tests/test_maple_estimate_field_edits.py tests/test_estimate_agent.py tests/test_maple_work_item_ops.py tests/test_orchestrator_intents.py -v`
  Expected: PASS.
- [ ] **Step 5:** Docs-only commit (pause for approval):

```bash
git add documentation/development/maple-phrasing-reference.md tests/reports/maple_crud_gap_report.md
git commit -m "docs: mark estimate field-edit phrasings as handled in Maple reference"
```

---

## Self-Review checklist (run before handing off)

- **Spec coverage:** item 1 → Task 4; item 2 → Tasks 1+6; item 3 → Tasks 1+5; item 4 → Task 3; item 5 → Task 7. Routing for all update-path items → Task 1. Shared resolver → Task 2. ✅
- **No placeholders:** every code step shows real code; the two "verify exact current regex" notes (Tasks 5, 6) are deliberate guardrails because those patterns must be read before editing — not deferred work.
- **Type consistency:** `_resolve_estimate_code_or_title` returns `Tuple[str, Optional[Dict[str, Any]]]` and is consumed identically in Tasks 4, 5, 6. `_detect_estimate_description_update` returns `Optional[str]`; `_detect_note_update` keeps its `Optional[Tuple[str, str]]` contract.
- **Ordering invariant:** in `_handle_update_estimate`, dispatch order is work-item → status → **description (new)** → notes → property-link → template. Description sits above notes so a "description" cue never lands in notes; work-item stays first so work-item description edits are untouched.

---

## Execution notes

- **Risk hotspot:** Task 1's routing rule is the broadest change — re-run `tests/test_maple_crud_coverage.py` and `tests/test_orchestrator_intents.py` after it (Task 1 Step 5) to catch any Property/Contact phrasing that happens to mention "estimate".
- **DB-free by default:** Tasks 1-6 tests use orchestrator routing + monkeypatched DB access (no live Mongo), matching `tests/test_maple_work_item_ops.py` and `tests/test_estimate_agent.py`. Only Task 7 Step 5 uses the TestClient fixture for the true multi-turn round-trip.
- **Commit discipline:** every commit step is a checkpoint — pause and get explicit approval before running `git commit` (CLAUDE.md / project policy).
