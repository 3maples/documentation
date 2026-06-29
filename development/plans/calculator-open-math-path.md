# Calculator: Open Math-Reasoning Path (tier 3)

**Status:** Design approved — ready for implementation plan
**Date:** 2026-06-26
**Area:** `platform/agents/calculator/`
**Feature flag:** `CALCULATOR_OPEN_MATH_ENABLED` (default OFF)

## 1. Problem

A user asked Maple:

> "how many stepping stones do i need if the stones are 3 ft by 2 ft and the path is 20 feet long and I want them to be 3-inches apart"

Maple answered **6.67 pieces** — which is wrong, not merely terse. Tracing the actual code path:

1. The regex fast-path (`text_helpers.extract_parameters_regex`) returned `None` (no `square feet`/`sq ft` token; `3 ft by 2 ft` does not trip `_PAVER_DIM_PATTERN`).
2. The LLM extractor classified it as `linear_material` with `linear_ft=20`, `piece_length_ft=3`.
3. `linear_material_quantity(20, 3)` computed `20 / 3 = 6.67`.

Three independent defects:

- **The 3-inch gap was silently dropped** — `linear_material` is `length ÷ piece` with no spacing term, and there is no field on `CalculationRequest` for a gap on a linear run. Gaps along a path are structurally unrepresentable in the curated formulas today.
- **Fractional count** — `6.67` discrete stones is not actionable.
- **Orientation chosen silently** — the stone is 3×2; the LLM grabbed `3` with no signal that `2` was equally valid.

The correct answers (reproduced and verified): **6 stones** with the 3 ft side along the path (9 in left over), or **9 stones** with the 2 ft side along the path (fills 20 ft exactly).

### Root cause

The Calculator is a deterministic formula engine: the LLM only extracts parameters; all arithmetic is pure-Python in `formulas.py`. That is the right design for **estimate work-item math** (quote numbers must be reproducible and auditable). But this query came through the **standalone calculator** path — a user just wanting to know basic math — which is a *separate subsystem* (confirmed: `agents/estimate/` does not import the calculator at all). For the standalone path, the determinism constraint that protects quotes does not apply, and the engine's inability to model anything that isn't a pre-authored formula forced the LLM to mis-map the query into the nearest formula and lose the gap + orientation.

The insight: a competing tool (Gemini) produced correct answers **because it ran code in a code interpreter**, not because the model did mental arithmetic. The real design lever is *where the arithmetic executes*, not *deterministic vs. LLM*.

## 2. Goals & non-goals

### Goals
- On the standalone calculator path, handle quantity/layout/measurement problems that no curated formula models — making appropriate assumptions and surfacing genuine alternatives (multiple options) — without Gemini-level verbosity.
- Keep every number trustworthy: arithmetic is executed deterministically, never done in the model's head.
- Add no arbitrary-code-execution surface.
- No regression to the curated tier or the estimate path.

### Non-goals (YAGNI / out of scope)
- **No dedicated `stepping_stone_count` curated formula now** — the open path covers it. (Future: promote hot patterns to curated formulas if usage shows they are common.)
- **No fix to the fractional-count bug** in existing curated formulas (`linear_material`, `paver_count`, `plant_count`, `retaining_wall_blocks` all return fractional counts). Real latent issue, separate change — logged as a follow-up.
- **No change to the orchestrator entry gate** (`is_calculation_query`). See §8.
- **No frontend changes** (the chat renders `result.response` markdown — confirmed at `portal/src/lib/orchestratorReply.ts:47`).
- **No change to estimate work-item math** (confirmed separate).
- **No new multi-turn loop** — the open path is single-shot.

## 3. Design decisions (settled in brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Where arithmetic runs | **Safe expression evaluator** — LLM emits arithmetic expressions; a sandboxed numeric evaluator computes them. No `exec`. |
| 2 | Relationship to curated registry | **Fallback tier** — curated formulas stay the fast, audited first tier; open path fires only when no formula fits. |
| 3 | Behavior on ambiguity | **Answer + show options** — never block; state assumptions, give a primary answer, surface genuine alternatives compactly. |
| 4 | Scope of the open path | **Any practical math** (within queries that reach the calculator — see §8). |
| 5 | Model tier | **Researcher** (`gpt-5.4`). |
| 6 | Trigger mechanism | **Extend the existing extractor with an explicit `open_math` type** (approach A). The classifier picks a curated type only when its formula *faithfully* models the request; otherwise `open_math`. |
| 7 | Feature flag | **Yes** — `CALCULATOR_OPEN_MATH_ENABLED`, default OFF. Off-state: `open_math` coerces to the existing canned clarification (an honest "can't model that precisely", not the wrong number). |

## 4. Architecture & control flow

The open path is a third tier inside `CalculatorAgent` — not a new agent. It returns the same envelope shape `process()` already returns, so the orchestrator, the `_to_envelope` wrapper, and the i18n translation sandwich all work unchanged (the English `response` markdown is translated back on the way out exactly like curated answers).

```
CalculatorAgent.process(message)
│
├─ 1. extract_parameters_regex(message)        ← unchanged, cheapest path
│       └─ hit → curated formula → done
│
├─ 2. _extract_with_llm(message)  [worker]     ← extraction prompt SHARPENED
│       │   classifier returns one of:
│       │     • a curated type  → faithful fit → curated formula → _finalize()
│       │     • "open_math"      → no curated formula models this
│       │     • "unknown"        → not a calculation at all (noise)
│       │
│       ├─ curated type → _finalize()  (existing path, incl. multi-turn pending)
│       ├─ "unknown"    → existing canned clarification
│       └─ "open_math":
│              ├─ flag OFF → treat as "unknown" → canned clarification (no researcher call)
│              └─ flag ON  → 3. OPEN REASONING PATH
│
└─ 3. _solve_open_math(message)   [researcher]
        ├─ researcher LLM → OpenMathResult {interpretation, assumptions[], options[{label, expression, unit}], note}
        ├─ safe_eval(expression) for each option   ← deterministic arithmetic, no LLM
        ├─ drop+log options whose expression is invalid/unsafe; all-dropped → graceful clarification
        └─ _format_open_math() → markdown into `response`  (no frontend change)
```

Key properties:
- **The mis-map fix lives in the extraction prompt.** Today the classifier is told to pick the closest type, which force-fit stepping-stones into `linear_material`. New rule: pick a curated type only when its formula faithfully models the request (all inputs representable); otherwise return `open_math`. The prompt gains 2–3 worked examples (spaced layout, composite shape, multi-orientation). `open_math` is added to the `calculation_type` `Literal`; `unknown` is reserved for genuine non-calculation noise.
- **Cost:** the researcher call fires only on `open_math` with the flag ON. Regex hits and curated-type hits never reach it.
- **Single-shot:** the open path does not touch the `pending_calculation` continuation flow.

## 5. New components

### (a) Safe arithmetic evaluator — `agents/calculator/safe_eval.py` (new; pure, no LLM/IO)

```python
def safe_eval(expression: str) -> float
```

AST-based, allow-list only:
- Parse with `ast.parse(expr, mode="eval")`, walk the tree.
- **Allowed nodes:** `Expression`, numeric `Constant`, `BinOp` (`+ - * / // % **`), `UnaryOp` (`+ -`), `Call` only to whitelisted names.
- **Allowed functions:** `floor, ceil, round, sqrt, abs, min, max`. **Allowed names:** `pi, e`.
- **Everything else rejected → `UnsafeExpressionError`:** no attribute access, no subscripts, no arbitrary names, no comprehensions, no lambdas, no walrus.
- **DoS guards:** cap `**` exponent magnitude and operand size.
- Division-by-zero / overflow → clean `CalculationError`, never a stack trace.

Mirrors the "all arithmetic lives in code, never the LLM" principle — the LLM proposes the *expression*, this module owns the *math*.

### (b) Output schema — added to `agents/calculator/schemas.py`

```python
class OpenMathOption(BaseModel):
    label: str          # "Long side (3 ft) along the path"
    expression: str     # "floor((240 + 3) / (36 + 3))"   ← arithmetic only
    unit: str           # "stones"
    # result computed by the backend via safe_eval — NOT supplied by the LLM

class OpenMathResult(BaseModel):
    interpretation: str             # one-line restatement
    assumptions: list[str]          # ["a stone sits at each end", "gaps are equal"]
    options: list[OpenMathOption]   # 1..N (one if unambiguous; several if a genuine fork)
    note: str | None = None         # short caveat / which option fits best
```

Researcher prompt instructs: **never put final numbers in the output — put arithmetic in `expression`**; do unit conversion inside the expression (`20 ft → 20*12`); use only the allowed operators/functions; add a second option only on a genuine fork (e.g. orientation).

### (c) Service method — `_solve_open_math(message)` (researcher model, temperature 0)
- Calls the LLM → `OpenMathResult`.
- For each option: `value = safe_eval(option.expression)`; attach the number. An option whose expression is unsafe/invalid is dropped and logged; if all options drop, return a graceful clarification (never blank or wrong).
- `_format_open_math()` renders compact markdown into `response`. Clears pending state (single-shot).
- `result` carries a structured `open_math` payload (backend metadata / audit / tests; the frontend ignores it).

### Rendered output (stepping-stones, from `response`)

> Here's how I'd work that out — you've got 3 ft × 2 ft stones along a 20 ft path with 3-inch gaps. The count depends on which way the stones face, so here are both:
>
> - **Long side (3 ft) along the path: 6 stones** — leaves 9 inches to split between the ends.
> - **Short side (2 ft) along the path: 9 stones** — fills the 20 ft exactly.
>
> Assumptions: a stone sits at each end; gaps are equal.
> Working: `floor((240 + 3) / (36 + 3))` = 6 · `floor((240 + 3) / (24 + 3))` = 9

### Residual risk (stated honestly)
The LLM cannot get the *arithmetic* wrong (the evaluator owns it), but it could choose a wrong *expression structure* (a modeling error). The `Working:` line is the mitigation — it is inspectable, and temperature-0 keeps it stable.

## 6. Feature flag

`config.py` `Settings`, following the existing `billing_meter_enabled` pattern:

```python
calculator_open_math_enabled: bool = Field(
    default=False, validation_alias="CALCULATOR_OPEN_MATH_ENABLED"
)
```

- Gates **only** the tier-3 reasoning branch.
- **Off-state:** `open_math` coerces to `unknown` → existing canned clarification; the researcher LLM is never called. This trades today's confidently-wrong `6.67` for an honest "I can help with… what would you like to calculate?" — strictly better, and avoids maintaining two classifier prompts.
- Rationale: ships straight to prod on the trunk-based flow (no PR gate), adds a paid researcher call, and changes user-facing answer style. Flag → enable in dev, validate, flip on in prod via env, kill instantly if cost/quality misbehaves.

## 7. Error handling
- Unsafe/invalid expression → option dropped + logged; all-dropped → graceful clarification, no traceback (matches "don't leak tracebacks").
- Researcher call failure/timeout → caught → graceful fallback message; outbound translation still applies.
- Magnitude/exponent guards prevent DoS.
- Entire branch behind the flag.

## 8. Important boundary: the orchestrator entry gate

`is_calculation_query` (the orchestrator pre-classifier) requires a **measurement-unit token** to route a message into the Calculator — deliberately, to avoid stealing CRUD count queries like "how many contacts do I have?". So this design delivers "any practical math" **for queries that already reach the calculator**. A purely unitless question (e.g. "what's 15% of 240?") may not pass the front door today. Broadening that gate risks misrouting CRUD queries and is a **separate follow-up decision**, not part of this change.

## 9. Testing strategy (TDD — failing test first)

- **`tests/test_calculator_safe_eval.py`** (pure, fast, security-critical):
  - Computes correctly: every allowed op (`+ - * / // % **`), every allowed fn (`floor/ceil/round/sqrt/abs/min/max`), `pi`/`e`.
  - Rejects (→ `UnsafeExpressionError`): arbitrary names (`__import__`, `os`), attribute access (`(1).__class__`), non-whitelisted calls (`eval`, `open`), subscripts, comprehensions, lambdas, walrus.
  - Guards: `9**9**9`-style blow-ups rejected; divide-by-zero/overflow → clean `CalculationError`.
- **`tests/test_calculator_open_math.py`**:
  - `_format_open_math()` over a hand-built `OpenMathResult` (no LLM) → asserts assumptions line, options with computed numbers, `Working:` line.
  - Bad-expression option dropped; all-bad → graceful clarification.
  - **Flag OFF** → `open_math` coerces to canned clarification; researcher LLM never called (stub asserts).
  - **Flag ON** with a **stubbed researcher LLM** returning a canned stepping-stones `OpenMathResult` → `process()` succeeds; `response` contains "6 stones" and "9 stones". Reuses the `CalculatorAgent(use_llm=…, llm=…)` injection pattern.
- **Classifier (Tier 2, live LLM, opt-in marker)** — same gating as `test_maple_crud_coverage.py` Tier 2 (needs `OPENAI_API_KEY`): stepping-stones / spaced-layout / composite-shape phrasings classify as `open_math`, not a curated mis-map.
- **Regression:** existing `test_calculator_*` suites and the 117-phrasing matrix stay green — the sharpened prompt must not push curated queries into `open_math`.
- **Gates:** `./run_mypy.sh` + `./run_ruff.sh` on all new files.

## 10. Related follow-ups (out of scope, logged here so they are not lost)
1. **Fractional-count rounding** — discrete-item curated formulas (`linear_material`, `paver_count`, `plant_count`, `retaining_wall_blocks`) return fractional counts (the original `6.67`). Counts should round up on the total. Separate change to curated formulas + tests.
2. **Entry-gate broadening** — decide whether/how to let unitless math ("15% of 240") reach the calculator without misrouting CRUD queries.
3. **Promote hot open-math patterns to curated formulas** — if telemetry shows a pattern (e.g. spaced stepping stones) is common, author a deterministic formula so it moves to the fast/audited tier.

## 11. Files touched (anticipated)
- `platform/agents/calculator/safe_eval.py` — new.
- `platform/agents/calculator/schemas.py` — add `OpenMathOption`, `OpenMathResult`; add `open_math` to `calculation_type` `Literal`.
- `platform/agents/calculator/service.py` — sharpen extraction prompt; add `_solve_open_math`, `_format_open_math`, flag branch.
- `platform/config.py` — add `calculator_open_math_enabled`.
- `platform/prompts/` — researcher reasoning prompt (new) + extraction-prompt examples.
- `platform/tests/test_calculator_safe_eval.py`, `platform/tests/test_calculator_open_math.py` — new.
- `.env.example` — document `CALCULATOR_OPEN_MATH_ENABLED`.

## 12. Extension — labor-time questions ("how long") via assumed-rate open-math *(2026-06-29)*

**Problem.** "How long does it take to edge 800 linear feet of beds?" never reached the
Calculator: the orchestrator's calculation gate (`is_calculation_query`) keys on
"how many / how much", so "how long" fell through to a graceful-but-non-answering
decline. It is a labor-time question — `time = quantity ÷ production_rate` — with no
curated formula (production rates are company-specific). A small, three-touch
extension of the open-math path handles it. This realizes a narrow slice of §10
follow-up #2 (entry-gate broadening), scoped to time questions that still carry a
spatial unit.

**Design decisions:**
- **Gate** (`agents/calculator/text_helpers.py`): add `\bhow\s+long\b` to
  `_CALC_QUESTION_PATTERNS`. A measurement unit is still required, so "how long to
  edge 800 linear feet" passes (question + "feet") while "how long until my estimate
  is approved" does not (no spatial unit). No `_CRUD_OVERRIDE_PATTERNS` entry collides.
- **Classifier** (`service.py` `_EXTRACTION_SYSTEM_PROMPT`): labor-time questions
  ("how long to do *X* amount of work") classify as `open_math` — there is no
  labor-time formula. One rule line + one worked example.
- **Reasoner** (`open_math.py` `_REASONING_SYSTEM_PROMPT`): for a labor-time question,
  **assume a typical production rate, state it explicitly as an assumption**, and
  compute `time = quantity / rate`. The existing "second option only on a genuine
  fork" rule lets *by hand* vs *power tool* rates surface as two options when they
  genuinely differ.
- **Rate source:** LLM-assumed rate only — **no rate-card data lookup** (deliberate;
  keeps the change small). **No rate-card pointer** in the reply (product decision —
  clean estimate only).
- Behind the same `CALCULATOR_OPEN_MATH_ENABLED` flag; no new calc type.

**Rendered example:**
> Edging 800 linear feet. **By hand: ~5.3 hours · with a power edger: ~2.7 hours.**
> Assumptions: ~150 linear ft/hour by hand, ~300 with a power edger.
> Working: `800 / 150` = 5.3 · `800 / 300` = 2.7

**Non-goals:** no rate-card lookup; unit-less "how long" stays out of the Calculator;
no new calc type.

**Testing:**
- *Tier-1 (rule, no LLM)* in `test_calculator_text_helpers.py`:
  `is_calculation_query("how long does it take to edge 800 linear feet of beds")` →
  True; negative guard ("how long until my estimate is approved" → False — no unit).
- *Live (opt-in `llm_e2e`)* in `test_calculator_open_math_live.py`: the labor-time
  query classifies as `open_math`, and the open-math answer contains an hours figure
  and a stated rate assumption.

**Residual risk:** "how long" is broad, but the spatial-unit requirement plus the
reasoner's graceful handling keep misroutes harmless (e.g. "how long is 800 ft of
fence" → open_math → trivially answers "800 ft").

**Files touched:** `agents/calculator/text_helpers.py` (gate),
`agents/calculator/service.py` (extraction prompt), `agents/calculator/open_math.py`
(reasoning prompt), `tests/test_calculator_text_helpers.py`,
`tests/test_calculator_open_math_live.py`.
