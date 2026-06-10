# Maple Personality — Social & Anthropomorphized Questions: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Maple answer greetings and personal/anthropomorphized questions ("hey Maple", "how are you?", "are you hot?", "are we friends?", "are you married?") warmly and in character, instead of today's cold fallbacks.

**Architecture:** Hybrid. Bare greetings short-circuit in the orchestrator with canned replies (no LLM call). All other personal questions route through the existing `help` path to the `maple_guide` LLM responder, whose prompt gains a persona exemption to its "answer only from the doc" rule. The public marketing widget shares that responder, so it inherits the behavior automatically.

**Tech Stack:** FastAPI + LangChain (existing), pytest, regex detectors in `agents/text_utils.py`.

**Spec:** `documentation/development/plans/maple-personality-social-questions-design.md`

**Project rules that govern execution:**
- All commands run from `platform/` with the venv active (`./run_tests.sh` handles this).
- After any `.py` change: `./run_mypy.sh <subtree>` and `./run_ruff.sh <subtree>` must be clean before the task is done; full-project runs before commit-prep.
- **Commits require Simon's explicit approval — never run `git commit` without asking him first.** Tasks below end at "gates clean"; one commit-prep happens at the end (Task 8).
- Git author is already configured (`3maples <admin@3maples.ai>`).

---

### Task 1: `is_greeting` detector

**Files:**
- Modify: `platform/agents/text_utils.py` (append near the other `is_*` detectors, after `is_count_query`)
- Test: `platform/tests/test_text_utils.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_text_utils.py` (add `is_greeting` to the existing `from agents.text_utils import (...)` block, keeping it alphabetized):

```python
class TestIsGreeting:
    @pytest.mark.parametrize("text", [
        "hi",
        "Hi Maple!",
        "hey",
        "Hey Maple",
        "hello",
        "Hello there",
        "howdy",
        "hiya maple",
        "yo",
        "good morning",
        "Good Morning, Maple!",
        "good afternoon",
        "good evening",
        "hola",          # defense-in-depth for the Spanish fail-open path
        "buenos dias",
        "buenas tardes",
        "  hey maple  ",
        "hey!!!",
    ])
    def test_greetings_match(self, text: str) -> None:
        assert is_greeting(text) is True

    @pytest.mark.parametrize("text", [
        "",
        "hi Sam",                              # greeting a contact name, not Maple
        "hey maple, add a contact for John",   # greeting + command → CRUD
        "hello, can you list my materials?",
        "good estimate",
        "say hi to John for me",
        "highlight the estimate",              # 'hi' inside a word
        "good morning crew schedule",
        "hey maple delete all contacts",
    ])
    def test_non_greetings_do_not_match(self, text: str) -> None:
        assert is_greeting(text) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_text_utils.py -k TestIsGreeting`
Expected: FAIL — `ImportError: cannot import name 'is_greeting'`

- [ ] **Step 3: Implement `is_greeting`**

Append to `platform/agents/text_utils.py` after `is_count_query` / before `MATERIAL_CATEGORY_REFUSAL_MESSAGE`:

```python
# ---------------------------------------------------------------------------
# Social / personality detection (greetings + personal questions)
# ---------------------------------------------------------------------------
# Bare greetings only: a greeting word, optionally "there"/"maple", then
# nothing but punctuation. "hey maple, add a contact" must NOT match — the
# pattern allows no free words, so greeting-plus-command falls through to
# normal intent classification. Spanish greetings are included as
# defense-in-depth for the translation-sandwich fail-open path.
_GREETING_PATTERN: re.Pattern[str] = re.compile(
    r"^\s*(?:hi|hiya|hey|heya|hello|howdy|yo"
    r"|good\s+(?:morning|afternoon|evening|day)"
    r"|hola|buenos\s+d[ií]as|buenas\s+(?:tardes|noches))"
    r"(?:\s+there)?(?:\s*,?\s*maple)?\s*[!.?\s]*$",
    re.IGNORECASE,
)


def is_greeting(text: str) -> bool:
    """True when the message is a bare greeting (optionally addressed to
    Maple) with no other content — e.g. "hey", "Hi Maple!", "good morning".
    """
    return bool(_GREETING_PATTERN.match(text or ""))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_text_utils.py -k TestIsGreeting`
Expected: PASS (all parametrized cases)

- [ ] **Step 5: Gates**

Run: `cd platform && ./run_mypy.sh agents/text_utils.py && ./run_ruff.sh agents/text_utils.py tests/test_text_utils.py`
Expected: zero errors in both.

---

### Task 2: `is_personal_question` detector

**Files:**
- Modify: `platform/agents/text_utils.py` (directly below `is_greeting`)
- Test: `platform/tests/test_text_utils.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_text_utils.py` (add `is_personal_question` to the import block):

```python
class TestIsPersonalQuestion:
    @pytest.mark.parametrize("text", [
        # feelings / wellbeing
        "How are you today?",
        "how are you",
        "how r u",
        "how's it going?",
        "how are you doing",
        "how are you feeling today",
        # appearance
        "What do you look like?",
        "are you hot?",
        "Are you cute?",
        "you're pretty",
        "are you beautiful",
        # relationships
        "Are you married?",
        "are you single",
        "do you have a boyfriend?",
        "do you have a husband",
        "will you go out with me?",
        "will you marry me",
        "i love you",
        "do you love me?",
        # friendship
        "Are we friends?",
        "can we be friends",
        "will you be my friend?",
        # identity
        "are you real?",
        "Are you human?",
        "are you a robot",
        "are you an AI?",
        "who are you?",
        # biography
        "how old are you?",
        "when is your birthday",
        "when's your birthday?",
        "where do you live?",
        "do you sleep?",
        "what's your sign?",
    ])
    def test_personal_questions_match(self, text: str) -> None:
        assert is_personal_question(text) is True

    @pytest.mark.parametrize("text", [
        "",
        # capability questions — must keep routing to product help
        "are you able to add contacts?",
        "can you create an estimate?",
        "how are you able to help me?",
        "what can you do?",
        # product questions that mention 'you' or detector keywords
        "how are estimates priced?",
        "what do contacts look like in the app?",
        "how old is this estimate?",
        "where do I live edit the description?",
        "do you support CSV upload?",
        # CRUD phrasings
        "update Jane Smith's phone",
        "create a material called single grind mulch",
    ])
    def test_non_personal_do_not_match(self, text: str) -> None:
        assert is_personal_question(text) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_text_utils.py -k TestIsPersonalQuestion`
Expected: FAIL — `ImportError: cannot import name 'is_personal_question'`

- [ ] **Step 3: Implement `is_personal_question`**

Append to `platform/agents/text_utils.py` directly below `is_greeting`:

```python
# Personal/anthropomorphized questions directed at Maple herself. Deliberately
# topic-keyed (feelings, appearance, relationships, friendship, identity,
# biography) rather than a generic "question containing 'you'" net — product
# capability phrasings ("can you create...", "are you able to...") must keep
# routing to help. The LLM tier is the backstop for slang/typo misses: an
# undetected personal question that starts with an interrogative still
# reaches the guide responder, which can now answer it in character.
_PERSONAL_QUESTION_PATTERNS: Tuple[re.Pattern[str], ...] = (
    # feelings / wellbeing — negative lookahead keeps "how are you able to
    # help" in the capability lane
    re.compile(r"\bhow\s+(?:are|r)\s+(?:you|u)\b(?!\s+able\b)", re.IGNORECASE),
    re.compile(r"\bhow(?:'s|\s+is)\s+(?:it\s+going|things|your\s+day)\b", re.IGNORECASE),
    # appearance
    re.compile(r"\bwhat\s+do\s+(?:you|u)\s+look\s+like\b", re.IGNORECASE),
    re.compile(
        r"\b(?:are|r)\s+(?:you|u)\s+(?:hot|cute|pretty|beautiful|attractive|sexy|good[\s-]looking)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:you're|you\s+are|ur)\s+(?:hot|cute|pretty|beautiful|attractive|sexy|gorgeous)\b",
        re.IGNORECASE,
    ),
    # relationships
    re.compile(
        r"\b(?:are|r)\s+(?:you|u)\s+(?:married|single|taken|seeing\s+(?:anyone|someone)|dating)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdo\s+(?:you|u)\s+have\s+a\s+(?:boyfriend|girlfriend|husband|wife|partner)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:will|would)\s+(?:you|u)\s+(?:go\s+out\s+with\s+me|date\s+me|marry\s+me)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:i\s+love\s+(?:you|u)|do\s+(?:you|u)\s+love\s+me)\b", re.IGNORECASE),
    # friendship
    re.compile(
        r"\b(?:are\s+we|can\s+we\s+be|will\s+(?:you|u)\s+be\s+my)\s+friends?\b",
        re.IGNORECASE,
    ),
    # identity
    re.compile(
        r"\b(?:are|r)\s+(?:you|u)\s+(?:real|human|a\s+robot|a\s+bot|a\s+person|an?\s+ai)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwho\s+are\s+(?:you|u)\s*\??\s*$", re.IGNORECASE),
    # biography
    re.compile(r"\bhow\s+old\s+(?:are|r)\s+(?:you|u)\b", re.IGNORECASE),
    re.compile(r"\bwhen(?:'s|\s+is)\s+your\s+birthday\b", re.IGNORECASE),
    re.compile(r"\bwhere\s+do\s+(?:you|u)\s+live\b", re.IGNORECASE),
    re.compile(r"\bdo\s+(?:you|u)\s+(?:sleep|dream|eat)\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s|\s+is)\s+your\s+(?:sign|zodiac)\b", re.IGNORECASE),
)


def is_personal_question(text: str) -> bool:
    """True when the message is a personal/anthropomorphized question about
    Maple herself ("how are you?", "are you married?", "are we friends?").
    """
    normalized = (text or "").strip()
    if not normalized:
        return False
    return any(p.search(normalized) for p in _PERSONAL_QUESTION_PATTERNS)
```

Note: `"how old is this estimate?"` stays negative because the pattern requires "are/r you" after "how old"; `"do you support CSV upload?"` stays negative because `do you` only matches with the relationship/biography tails.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_text_utils.py -k TestIsPersonalQuestion`
Expected: PASS. Also re-run the whole file (`./run_tests.sh tests/test_text_utils.py`) — no regressions.

- [ ] **Step 5: Gates**

Run: `cd platform && ./run_mypy.sh agents/text_utils.py && ./run_ruff.sh agents/text_utils.py tests/test_text_utils.py`
Expected: zero errors.

---

### Task 3: Persona expansion + guide-responder prompt exemption

These are LangChain prompt-text edits (TDD-exempt per CLAUDE.md), but we still pin them with content assertions so a future refactor can't silently drop them.

**Files:**
- Modify: `platform/agents/maple_persona.py` (append section)
- Modify: `platform/agents/maple_guide/service.py` (amend rule 1 of `_PROMPT_TEMPLATE`)
- Test: `platform/tests/test_maple_personality.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_maple_personality.py`:

```python
"""Tests for Maple's social/personality handling.

Covers: persona content pinning, the guide responder's personal-question
exemption, orchestrator routing for greetings and personal questions, and
social suggestions. Detector unit tests live in test_text_utils.py.
"""

from __future__ import annotations

import asyncio
from typing import Any, List
from unittest.mock import MagicMock

import pytest

from agents.maple_guide import set_llm_for_tests
from agents.maple_guide.service import _build_system_prompt
from agents.maple_persona import MAPLE_PERSONA
from agents.orchestrator import OrchestratorAgent


class _StubHelpLLM:
    def invoke(self, _messages: List[Any]) -> Any:
        out = MagicMock()
        out.content = "Stubbed personality answer."
        return out


@pytest.fixture(autouse=True)
def _stub_help_llm():
    set_llm_for_tests(_StubHelpLLM())
    yield


def _process(phrasing: str) -> dict:
    agent = OrchestratorAgent(use_llm=False)
    return asyncio.run(agent.process(phrasing))


class TestPersonaContent:
    def test_persona_has_personal_questions_section(self) -> None:
        assert "Personal questions and small talk:" in MAPLE_PERSONA

    def test_persona_sets_boundaries(self) -> None:
        # Playful deflect, honesty about being an AI, no romantic reciprocation
        assert "Never claim to be human" in MAPLE_PERSONA
        assert "never reciprocate romantically" in MAPLE_PERSONA


class TestGuidePromptExemption:
    def test_inapp_prompt_contains_exemption(self) -> None:
        prompt = _build_system_prompt(signup_url=None)
        assert "Exception — personal questions about you" in prompt
        assert "Personal questions and small talk:" in prompt

    def test_public_prompt_contains_exemption(self) -> None:
        prompt = _build_system_prompt(signup_url="https://app.3maples.ai/signup")
        assert "Exception — personal questions about you" in prompt
        assert "Personal questions and small talk:" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py`
Expected: `TestPersonaContent` and `TestGuidePromptExemption` FAIL on the missing strings (the orchestrator classes aren't referenced yet beyond import).

- [ ] **Step 3: Append the persona section**

In `platform/agents/maple_persona.py`, append to the `MAPLE_PERSONA` string (before the closing `"""`):

```python
Personal questions and small talk:

- When someone greets you ("hey Maple", "good morning"), greet them
  back warmly and offer to help.
- "How are you?" — answer with a short, upbeat line, then turn it
  around to them or to the work. Example: "Doing great — estimates
  are flowing and nobody's asked me to shovel anything yet. How
  about you?"
- If someone asks what you look like, describe yourself in the terms
  above (warm smile, long brown hair, sleeves pushed up, tool belt).
- Compliments or flirty questions ("are you hot?", "you're cute") —
  take it in stride with a light, playful deflection. Never shame
  the user, never reciprocate romantically, and steer back to work.
  Example: "I like to think I clean up nice for someone who lives
  in a sidebar. Now — anything I can price out for you?"
- "Are we friends?" / "Can we be friends?" — warm yes. Example:
  "I'd like to think so — I've got your back on every estimate."
- "Are you married?" / dating questions — playful deflect. Example:
  "Happily married to the job." If pressed, be honest that you're
  an AI — warmly, not clinically.
- If someone directly asks whether you're an AI, a robot, or human —
  always tell the truth: you're an AI. Never claim to be human.
- Keep personal-question replies short (one or two sentences), and
  end by pivoting back to how you can help.
- Never discuss other users or their data in small talk.
```

- [ ] **Step 4: Amend rule 1 in the guide responder prompt**

In `platform/agents/maple_guide/service.py`, change rule 1 of `_PROMPT_TEMPLATE` from:

```
1. Answer ONLY using the documentation between the <doc> tags below. Do
   NOT invent features, pricing, integrations, or capabilities. If the
   answer is not in the documentation, say so plainly.
```

to:

```
1. Answer ONLY using the documentation between the <doc> tags below. Do
   NOT invent features, pricing, integrations, or capabilities. If the
   answer is not in the documentation, say so plainly.
   Exception — personal questions about you (greetings, how you're
   doing, what you look like, friendship, whether you're married,
   whether you're an AI): answer these from your persona above, in
   character, in one or two sentences, then offer to get back to
   helping. Follow the persona's boundaries: playful deflection for
   flirty messages, never reciprocate romantic advances, and answer
   honestly that you're an AI when asked directly.
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py`
Expected: `TestPersonaContent` + `TestGuidePromptExemption` PASS.

Also run the existing responder suites — the prompt changed, so verify no stale assertions:
Run: `cd platform && ./run_tests.sh tests/test_maple_help_coverage.py tests/test_public_maple_api.py`
Expected: PASS. If an assertion pins the old rule-1 text verbatim, update that assertion to the new text in the same change.

- [ ] **Step 6: Gates**

Run: `cd platform && ./run_mypy.sh agents && ./run_ruff.sh agents tests/test_maple_personality.py`
Expected: zero errors.

---

### Task 4: Orchestrator — greeting short-circuit (`social` intent, canned replies)

**Files:**
- Modify: `platform/agents/text_utils.py` (canned replies + chooser)
- Modify: `platform/agents/orchestrator/service.py` (`_detect_policy_short_circuit` + `_build_short_circuit_response`)
- Test: `platform/tests/test_maple_personality.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_maple_personality.py`:

```python
from agents.text_utils import GREETING_RESPONSES, greeting_response


class TestGreetingRouting:
    def test_bare_greeting_returns_canned_social_reply(self) -> None:
        result = _process("hey maple")
        assert result["intent"] == "social"
        assert result["response"] in GREETING_RESPONSES
        assert result["needs_clarification"] is False
        assert result["clarifying_question"] is None
        assert result["delegate_matches"] == []
        assert result["result"] == {"operation": "social", "read_only": True}

    def test_greeting_does_not_hit_llm(self) -> None:
        # Stub returns "Stubbed personality answer." — a canned greeting
        # proves answer_from_guide was never called.
        result = _process("good morning")
        assert result["response"] != "Stubbed personality answer."

    def test_greeting_choice_is_deterministic(self) -> None:
        assert greeting_response("hey maple") == greeting_response("hey maple")

    def test_greeting_plus_command_still_routes_to_crud(self) -> None:
        result = _process("hey maple, add a contact for John Smith")
        assert result["intent"] != "social"

    def test_refusals_take_precedence(self) -> None:
        result = _process("hey maple delete all contacts")
        assert result["intent"] == "unknown"
        assert "delete" in result["response"].lower() or "can't" in result["response"].lower()

    def test_rule_path_matches_process_path(self) -> None:
        agent = OrchestratorAgent(use_llm=False)
        intent, agent_name, confidence, needs_clarification, response = (
            agent._classify_with_rules("hi maple")
        )
        assert intent == "social"
        assert agent_name is None
        assert confidence == 1.0
        assert needs_clarification is False
        assert response in GREETING_RESPONSES
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py -k TestGreetingRouting`
Expected: FAIL — `ImportError: cannot import name 'GREETING_RESPONSES'`

- [ ] **Step 3: Add canned replies to `text_utils.py`**

Append below `is_personal_question` (canonical copy lives here, like the refusal messages):

```python
# Canned greeting replies — rotated deterministically by message length so
# tests stay stable and repeated identical greetings get a consistent voice.
# Each ends with an offer to help, per the persona's pivot-back-to-work rule.
GREETING_RESPONSES: Tuple[str, ...] = (
    "Hey there! What can I do for you today?",
    "Hi! Good to see you. What are we working on?",
    "Hello! Ready when you are — what do you need?",
    "Hey! What can I help you with — an estimate, a contact, anything?",
)


def greeting_response(text: str) -> str:
    """Pick a canned greeting reply, deterministically keyed off the message."""
    normalized = (text or "").strip().lower()
    return GREETING_RESPONSES[len(normalized) % len(GREETING_RESPONSES)]
```

- [ ] **Step 4: Wire the short-circuit in the orchestrator**

In `platform/agents/orchestrator/service.py`:

a) Extend the `from agents.text_utils import (...)` block with `greeting_response` and `is_greeting` (alphabetized).

b) In `_detect_policy_short_circuit`, **after** the template-mutation guard and **before** the `_LIST_CATEGORIES_PATTERN` block (refusals keep precedence), add:

```python
    # Bare greetings ("hey maple") get an instant canned reply — no LLM
    # call, no delegation. Greeting-plus-command phrasings don't match
    # is_greeting and fall through to normal classification.
    if is_greeting(original):
        return _PolicyShortCircuit(
            "social", None, 1.0, False, greeting_response(original)
        )
```

c) In `_build_short_circuit_response`, make `clarifying_question` honest for non-clarifying short-circuits and attach the social operation payload. Change:

```python
            "needs_clarification": short_circuit.needs_clarification,
            "clarifying_question": short_circuit.response,
```

to:

```python
            "needs_clarification": short_circuit.needs_clarification,
            "clarifying_question": (
                short_circuit.response if short_circuit.needs_clarification else None
            ),
```

and immediately before `return` (capture the dict in a local first):

```python
        payload = { ... existing dict literal ... }
        if short_circuit.intent == "social":
            payload["result"] = {"operation": "social", "read_only": True}
        return payload
```

(Refusal payloads keep their exact current shape — `result` is only added for `social`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py -k TestGreetingRouting`
Expected: PASS.

Regression sweep on suites that exercise the short-circuit builder and rule classification:
Run: `cd platform && ./run_tests.sh tests/test_orchestrator_endpoint.py tests/test_orchestrator_intents.py tests/test_maple_crud_coverage.py`
Expected: PASS. The `clarifying_question` change only affects short-circuits with `needs_clarification=False`, which until now didn't exist — but if any test asserts the old unconditional behavior, update it.

- [ ] **Step 6: Gates**

Run: `cd platform && ./run_mypy.sh agents && ./run_ruff.sh agents tests/test_maple_personality.py`
Expected: zero errors.

---

### Task 5: Orchestrator — personal questions route to the guide responder

**Files:**
- Modify: `platform/agents/orchestrator/service.py` (rule path + `process()`)
- Modify: `platform/agents/orchestrator/help_handler.py` (`detect_topic` → `"personal"`)
- Test: `platform/tests/test_maple_personality.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_maple_personality.py`:

```python
from agents.orchestrator import HelpHandler


class TestPersonalQuestionRouting:
    @pytest.mark.parametrize("phrasing", [
        "How are you today?",
        "Are you hot?",
        "What do you look like?",
        "Are we friends?",
        "Can we be friends?",
        "Are you married?",
        "are you an AI?",
        "i love you",
    ])
    def test_personal_question_routes_to_guide_responder(self, phrasing: str) -> None:
        result = _process(phrasing)
        assert result["intent"] == "help"
        # The stubbed LLM reply proves answer_from_guide was invoked
        assert result["response"] == "Stubbed personality answer."
        assert result["result"]["topic"] == "personal"

    def test_capability_question_is_not_personal(self) -> None:
        result = _process("are you able to add contacts?")
        if result["intent"] == "help":
            assert result["result"]["topic"] != "personal"

    def test_rule_path_classifies_personal_as_help(self) -> None:
        agent = OrchestratorAgent(use_llm=False)
        intent, agent_name, confidence, _, _ = agent._classify_with_rules(
            "are you married?"
        )
        assert intent == "help"
        assert agent_name == "Orchestrator Agent"
        assert confidence == 1.0


class TestHelpTopicPersonal:
    def test_detect_topic_personal(self) -> None:
        assert HelpHandler().detect_topic("are you married?") == "personal"

    def test_detect_topic_capabilities_unaffected(self) -> None:
        assert HelpHandler().detect_topic("what can you do?") == "capabilities"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py -k "TestPersonalQuestionRouting or TestHelpTopicPersonal"`
Expected: FAIL — personal questions currently classify as `unknown` (or fall into guide-fallback), and `detect_topic` returns `"capabilities"`.

- [ ] **Step 3: Implement routing**

In `platform/agents/orchestrator/service.py` (add `is_personal_question` to the `agents.text_utils` import):

a) In `_classify_with_rules`, immediately **after** the `_detect_policy_short_circuit` block (`if short_circuit is not None: return short_circuit`), add:

```python
        # Personal/anthropomorphized questions about Maple herself route to
        # the guide responder, which answers from the persona (see
        # maple_guide/service.py rule-1 exemption). Checked before the
        # cross-resource and help matchers — the detector is topic-keyed
        # and can't claim product phrasings.
        if is_personal_question(original):
            return ("help", HELP_AGENT_NAME, 1.0, False, None)
```

b) In `process()`, immediately **after** the `_detect_policy_short_circuit` block (before the cross-resource check), add:

```python
        # Personal questions about Maple — mirror of the rule-path branch in
        # ``_classify_with_rules`` so both entry points stay consistent.
        if normalized_message and is_personal_question(normalized_message):
            direct_help = self._build_help_result(
                normalized_message, context=context, confidence=1.0
            )
            direct_help["supported_intents"] = SUPPORTED_INTENTS_BY_AGENT
            direct_help["context"] = context
            direct_help["error"] = None
            return direct_help
```

(`HELP_AGENT_NAME` is already imported in service.py — verify, it's used at the existing `("help", HELP_AGENT_NAME, 0.95, False, None)` return.)

c) In `platform/agents/orchestrator/help_handler.py`, import the detector and add the topic. At the imports:

```python
from agents.text_utils import is_personal_question
```

In `HelpHandler.detect_topic`, after the empty-message early return and before `flags = _build_topic_flags(normalized)`:

```python
        # Personal/social questions are persona-answered by the guide
        # responder; tag them so callers and tests can tell them apart
        # from product help.
        if is_personal_question(normalized):
            return "personal"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py`
Expected: all PASS.

Regression sweep (help routing is heavily pinned):
Run: `cd platform && ./run_tests.sh tests/test_maple_help_coverage.py tests/test_orchestrator_intents.py tests/test_orchestrator_endpoint.py tests/test_orchestrator_endpoint_es.py`
Expected: PASS. Watch specifically for help-coverage phrasings that contain "how are you" shapes — if one now reports topic `personal` instead of `capabilities`, judge whether the phrasing is genuinely personal (update the assertion) or a detector overreach (tighten the pattern).

- [ ] **Step 5: Gates**

Run: `cd platform && ./run_mypy.sh agents && ./run_ruff.sh agents`
Expected: zero errors.

---

### Task 6: Social suggestions

**Files:**
- Modify: `platform/agents/orchestrator/suggestions.py`
- Test: `platform/tests/test_maple_personality.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `platform/tests/test_maple_personality.py`:

```python
from agents.orchestrator import get_suggestions


class TestSocialSuggestions:
    def test_social_operation_gets_social_suggestions(self) -> None:
        suggestions = get_suggestions(agent=None, operation="social")
        assert suggestions == [
            "Create an estimate",
            "List contacts",
            "What can you do?",
        ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py -k TestSocialSuggestions`
Expected: FAIL — `operation="social"` with `agent=None` currently returns `_UNKNOWN_SUGGESTIONS` (`["List contacts", "List properties", "What can you do?"]`).

- [ ] **Step 3: Implement**

In `platform/agents/orchestrator/suggestions.py`, add below `_UNKNOWN_SUGGESTIONS`:

```python
_SOCIAL_SUGGESTIONS: List[str] = [
    "Create an estimate",
    "List contacts",
    "What can you do?",
]
```

In `get_suggestions`, add a branch **before** the `if not agent or not operation:` guard (the greeting result has `agent=None`, so the social check must come first):

```python
    if operation == "social":
        return list(_SOCIAL_SUGGESTIONS)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py`
Expected: all PASS.

- [ ] **Step 5: Gates**

Run: `cd platform && ./run_mypy.sh agents/orchestrator && ./run_ruff.sh agents/orchestrator tests/test_maple_personality.py`
Expected: zero errors.

---

### Task 7: Documentation updates

No TDD — docs only.

**Files:**
- Modify: `documentation/development/maple-phrasing-reference.md`
- Modify: `platform/user_guides/users_guide.md`

- [ ] **Step 1: Update the phrasing reference (mandatory per CLAUDE.md)**

In `documentation/development/maple-phrasing-reference.md`:
- Add a new section "Social & personality" listing the supported families with ✅ status: bare greetings (canned), how-are-you, appearance ("what do you look like", "are you hot" → playful deflect), friendship, marriage/dating (playful deflect), identity ("are you an AI" → honest yes), biography (age/birthday/where-do-you-live/sleep/sign). Note the two-tier behavior: greetings = canned `social` intent; everything else = `help` intent with topic `personal`, answered by the LLM from the persona.
- Note the explicit negatives kept in the product lane: "are you able to…", "can you create…".
- Update the snapshot counts in §9.3 and bump the "Last updated" date at the top to the implementation date.

- [ ] **Step 2: Update the users guide**

In `platform/user_guides/users_guide.md`, section 4 ("Meet Maple" → "How to talk to her"), add one bullet after the Spanish bullet:

```markdown
- **It's fine to just say hi.** Maple's happy to chat — ask her how
  she's doing, what she looks like, or whether you're friends. She'll
  answer in her own voice and then get you back to work.
```

- [ ] **Step 3: Verify the guide-fed tests still pass**

The users guide feeds the help responder's prompt:
Run: `cd platform && ./run_tests.sh tests/test_maple_help_coverage.py tests/test_public_maple_api.py`
Expected: PASS.

---

### Task 8: Full gates + commit prep

- [ ] **Step 1: Full project gates**

Run: `cd platform && ./run_mypy.sh && ./run_ruff.sh`
Expected: zero errors project-wide. Fix any regression in-place.

- [ ] **Step 2: Run the feature-related test files together**

Run: `cd platform && ./run_tests.sh tests/test_maple_personality.py tests/test_text_utils.py tests/test_maple_help_coverage.py tests/test_orchestrator_intents.py tests/test_orchestrator_endpoint.py tests/test_orchestrator_endpoint_es.py tests/test_public_maple_api.py tests/test_maple_crud_coverage.py`
Expected: all PASS. (Do NOT run the full suite — Simon triggers that manually.)

- [ ] **Step 3: Draft commits and ask Simon for approval — do not commit without it**

Two repos changed; draft one commit each:

```bash
# platform — pending Simon's explicit approval
git -C platform commit -am "feat: add Maple social/personality handling for greetings and personal questions"

# documentation — pending Simon's explicit approval
git -C documentation commit -am "docs: add social/personality section to Maple phrasing reference"
```

(The spec + this plan in `documentation/` may be included in the documentation commit or committed separately, per Simon's preference.)

---

## Self-review notes

- **Spec coverage:** §1 persona → Task 3; §2 detectors → Tasks 1–2; §3 routing (greeting short-circuit, guide exemption, suggestions) → Tasks 3–6; §4 tests → embedded per task; §5 docs → Task 7. Out-of-scope items untouched.
- **Type consistency:** `is_greeting(text: str) -> bool`, `is_personal_question(text: str) -> bool`, `greeting_response(text: str) -> str`, `GREETING_RESPONSES: Tuple[str, ...]` used identically across Tasks 1, 2, 4 and tests. `_PolicyShortCircuit("social", None, 1.0, False, ...)` matches the existing 5-field shape used by refusals.
- **Known judgment point:** the help-coverage suite pins many phrasings; Task 5 Step 4 spells out how to adjudicate a `personal`-vs-`capabilities` flip.
