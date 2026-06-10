# Maple Personality — Social & Anthropomorphized Questions (Design)

**Date:** 2026-06-09
**Status:** Approved design, pending implementation plan
**Owner:** Simon

## Goal

Let Maple handle greetings and personal/anthropomorphized questions ("Hey
Maple", "How are you today?", "Are you hot?", "What do you look like?",
"Are we friends?", "Are you married?") with warm, in-character responses
aligned with her persona — instead of today's cold fallbacks.

## Current behavior (the gap)

- "Hey Maple" / "Hi Maple" → orchestrator "unknown" intent → *"I'm not
  sure how to help with that…"*
- "How are you today?" / "Are you married?" → the interrogative detector
  routes them to the `maple_guide` LLM responder, but its prompt rule #1
  ("answer ONLY from users_guide.md") forces the *"that's outside my
  toolkit"* fallback.
- `agents/maple_persona.py` already defines her voice and self-image
  (including appearance), but no social message ever reaches a path that
  is allowed to use it.

## Decisions (made with Simon, 2026-06-09)

1. **Hybrid approach** — bare greetings get instant canned replies (free,
   zero latency); all other personal questions go to the LLM responder
   with the persona (covers the unpredictable long tail).
2. **Playful deflect** for flirty/romantic questions — light humor, never
   shames the user, pivots back to work. Honest that she's an AI when
   directly asked; never claims to be human.
3. **Both surfaces** — in-app chat AND the public marketing widget. The
   canned-greeting tier is in-app only (the widget has no orchestrator);
   the LLM persona mode is shared automatically via `maple_guide`.

## Design

### 1. Persona expansion — `platform/agents/maple_persona.py`

Append a new section to `MAPLE_PERSONA` (draft text, tune wording in
implementation):

```
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

### 2. Detection — `platform/agents/text_utils.py`

Two new helpers (shared, consistent with existing helper conventions —
no inline regex in agents):

- **`is_greeting(text) -> bool`** — matches bare greetings only:
  "hi", "hey", "hello", "howdy", "hiya", "yo", "good morning /
  afternoon / evening", optionally followed by "maple" and punctuation.
  Length-gated (≤ ~4 words) so "hey maple, add a contact for John"
  does NOT match and still routes to CRUD.
- **`is_personal_question(text) -> bool`** — keyword-anchored detector
  for personal topics directed at Maple. Topic groups:
  - feelings: "how are you", "how's it going", "how are you doing/feeling"
  - appearance: "what do you look like", "are you hot/cute/pretty/beautiful"
  - relationships: "are you married/single", "do you have a
    boyfriend/girlfriend/husband/wife/partner", "will you go out with
    me", "do you love me", "i love you"
  - friendship: "are we friends", "can we be friends", "will you be my friend"
  - identity: "are you real", "are you human", "are you a robot",
    "are you an ai", "who are you"
  - biography: "how old are you", "when is your birthday", "where do
    you live", "do you sleep", "what's your sign"
  Deliberately topic-keyed, NOT a generic "question containing 'you'"
  net — "can you create an estimate?" and "are you able to add
  contacts?" must keep routing to product help.

Greeting + personal in one message ("hey maple, are you married?"):
the personal-question path wins (LLM handles both naturally).

### 3. Routing

**Orchestrator (`platform/agents/orchestrator/service.py`):**

- New early rule (after the refusal guards, before domain matching):
  - `is_greeting` → return a canned reply chosen from a small rotating
    set (~4 variants, e.g. "Hey there! What can I do for you today?"),
    with the existing suggestion buttons ("Create an estimate",
    "List contacts", "What can you do?"). Intent: a new `social`
    result with confidence 1.0, no delegation.
  - `is_personal_question` → route to `answer_from_guide` (same path
    help questions take today), so the LLM answers from the persona.
- The Spanish translation sandwich already wraps this boundary —
  greetings and personal questions in Spanish translate in, route the
  same way, and translate back out. No changes needed.

**Guide responder (`platform/agents/maple_guide/service.py`):**

- Add one rule to `_PROMPT_TEMPLATE` (applies to both in-app and public
  mode blocks automatically): personal/social questions about Maple
  herself — greetings, how she's doing, what she looks like, friendship,
  marriage, whether she's an AI — are **exempt from rule 1** (the
  answer-only-from-doc restriction). Answer them from the persona, in
  character, one or two sentences, then offer to help. Flirty or
  romantic messages get the playful deflection defined in the persona.
- The existing fallback directives stay for genuinely unanswerable
  questions; personal questions no longer fall into them.

### 4. Tests (TDD — failing tests first)

- **`tests/test_text_utils.py`** (existing file — extend it):
  - `is_greeting` positives: "hey", "Hi Maple!", "good morning", "hiya maple"
  - `is_greeting` negatives: "hey maple add a contact for John",
    "hi Sam" (existing stopword behavior unaffected), "good estimate"
  - `is_personal_question` positives: each topic group above, including
    "Are you hot?", "are we friends", "u married?" (light slang noted
    but exhaustive slang coverage out of scope)
  - negatives: "are you able to add contacts?", "can you create an
    estimate?", "how are estimates priced?", "what do contacts look like
    in the app?"
- **Orchestrator routing tests** (mocked LLM):
  - greeting → canned reply + suggestions, no LLM call
  - personal question → delegated to guide responder
  - "hey maple, add a contact for John" → still CRUD (contact agent)
  - bulk-delete / equipment refusals still take precedence
- **Guide responder prompt tests**: the persona-exemption rule is
  present in the built system prompt for both in-app and public modes.
- Canned greeting rotation: deterministic under test (seed or
  index-based), so assertions are stable.

### 5. Documentation updates (same change)

- **`documentation/development/maple-phrasing-reference.md`** — new
  social/personality section, status flags for each phrasing family,
  snapshot-count update in §9.3, "Last updated" bump. (Mandatory per
  CLAUDE.md whenever Maple phrasings are added.)
- **`platform/user_guides/users_guide.md`** — one or two lines in
  section 4 ("Meet Maple") noting she's happy to chat — say hi, ask how
  she's doing. Keeps the guide (and the help responder's source doc)
  honest about what she handles.

## Out of scope

- Memory of social context across sessions ("you asked me that yesterday").
- Exhaustive slang/typo coverage in detectors (LLM tier catches misses:
  an undetected personal question that starts with an interrogative
  still reaches the guide responder, which can now answer it).
- Moderation/escalation flows for abusive content (existing behavior
  unchanged).
- Equipment/bulk-delete policy changes (untouched; refusal guards keep
  precedence).

## Risks & mitigations

- **Detector overreach** — a product question misrouted to small talk
  would be annoying. Mitigation: topic-keyed patterns + explicit
  negative tests for capability phrasings ("can you…", "are you able…").
- **LLM tone drift** on flirty inputs — mitigated by explicit persona
  rules (never reciprocate, always honest about being an AI when asked)
  and temperature 0 per project standard.
- **Public widget abuse** — visitors may probe with crude messages; the
  playful-deflect + pivot pattern plus existing public-mode restrictions
  bound the blast radius.
