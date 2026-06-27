# Calculator Open Math-Reasoning Path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a flag-gated tier-3 "open math" path to the standalone Calculator agent that handles quantity/layout problems no curated formula models — making appropriate assumptions and showing multiple options — with arithmetic executed by a safe evaluator, never by the LLM.

**Architecture:** The Calculator's parameter extractor gains an `open_math` classification for requests its formulas can't faithfully model. When `CALCULATOR_OPEN_MATH_ENABLED` is on, those route to a researcher-model call that returns an interpretation, assumptions, and one-or-more options — each carrying an arithmetic *expression* (never a number). A new `safe_eval` AST evaluator computes every expression deterministically. Output is compact markdown in the existing `response` field (no frontend change). Curated formulas, the regex fast-path, the multi-turn flow, and the estimate path are untouched.

**Tech Stack:** Python 3.14, FastAPI, LangChain (`ChatOpenAI` via `services/llm` factory), Pydantic v2, pytest. Design spec: `documentation/development/plans/calculator-open-math-path.md`.

## Global Constraints

- **TDD:** failing test first, then minimal implementation, for every `.py` behavior change. LangChain prompt-text edits are TDD-exempt (validated by the opt-in live test in Task 5).
- **Gates after every `.py` change:** `./run_mypy.sh <touched path>` and `./run_ruff.sh <touched path>` must be clean before each commit. Project sits at zero mypy + zero ruff errors — keep it there.
- **Backend tests run against the local Mongo** only if they touch the DB; the tasks here are pure/unit and do **not** need Mongo. Run via `./run_tests.sh <path>` (activates the venv).
- **US English** in all copy (`color`, `behavior`, …).
- **Commits:** each commit step requires its **own explicit user approval before running** (project rule — never chain off a prior approval). Author is already configured as `3maples <admin@3maples.ai>`. End commit messages with the `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` trailer. Commit-message format: `<type>: <description>`.
- **Feature flag:** `CALCULATOR_OPEN_MATH_ENABLED` defaults **OFF**. With it off, behavior is identical regardless of these changes except that an `open_math` classification yields the existing calculator menu clarification (not a wrong number).
- **No frontend changes.** The portal renders `result.response` markdown (`portal/src/lib/orchestratorReply.ts:47`).

## File Structure

| File | Responsibility | Create/Modify |
|------|----------------|---------------|
| `platform/agents/calculator/safe_eval.py` | AST-based arithmetic evaluator (allow-list only). Pure. | **Create** |
| `platform/agents/calculator/open_math.py` | Researcher reasoning prompt, `solve_open_math` (LLM→eval→format), `format_open_math` (pure renderer). | **Create** |
| `platform/agents/calculator/schemas.py` | Add `OpenMathOption`, `OpenMathResult`; add `open_math` to `calculation_type` `Literal`. | Modify |
| `platform/agents/calculator/service.py` | Sharpen extraction prompt; add `__init__(reasoning_llm=…)`, `_get_reasoning_llm`, `_handle_open_math`; DRY the menu string; route `open_math` in `process()`. | Modify |
| `platform/config.py` | Add `calculator_open_math_enabled` setting. | Modify |
| `platform/.env.example` | Document `CALCULATOR_OPEN_MATH_ENABLED`. | Modify |
| `platform/tests/test_calculator_safe_eval.py` | Unit tests for the evaluator (security-critical). | **Create** |
| `platform/tests/test_calculator_open_math.py` | Tests for schemas, formatter, solver, and `process()` integration (flag on/off, fallback). | **Create** |
| `platform/tests/test_calculator_open_math_live.py` | Opt-in `llm_e2e` classification test (real LLM). | **Create** |

---

### Task 1: Safe arithmetic evaluator

**Files:**
- Create: `platform/agents/calculator/safe_eval.py`
- Test: `platform/tests/test_calculator_safe_eval.py`

**Interfaces:**
- Produces: `safe_eval(expression: str) -> float`; exceptions `UnsafeExpressionError(ValueError)`, `CalculationError(ValueError)`.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_calculator_safe_eval.py`:

```python
"""Unit tests for the Calculator open-math safe arithmetic evaluator."""

import math

import pytest

from agents.calculator.safe_eval import (
    CalculationError,
    UnsafeExpressionError,
    safe_eval,
)


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("1 + 2", 3.0),
        ("10 - 4", 6.0),
        ("3 * 4", 12.0),
        ("20 / 8", 2.5),
        ("20 // 8", 2.0),
        ("20 % 7", 6.0),
        ("2 ** 5", 32.0),
        ("-5 + 2", -3.0),
        ("+7", 7.0),
        ("floor((240 + 3) / (36 + 3))", 6.0),
        ("floor((240 + 3) / (24 + 3))", 9.0),
        ("ceil(20 / 3)", 7.0),
        ("round(3.14159, 2)", 3.14),
        ("sqrt(144)", 12.0),
        ("abs(-9)", 9.0),
        ("min(3, 7)", 3.0),
        ("max(3, 7)", 7.0),
    ],
)
def test_allowed_expressions(expr: str, expected: float) -> None:
    assert safe_eval(expr) == pytest.approx(expected)


def test_pi_and_e_constants() -> None:
    assert safe_eval("pi") == pytest.approx(math.pi)
    assert safe_eval("e") == pytest.approx(math.e)


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os')",
        "os.system('ls')",
        "(1).__class__",
        "eval('1 + 1')",
        "open('x')",
        "[n for n in range(3)]",
        "lambda: 1",
        "x",
        "1 if True else 2",
        "a[0]",
        "True",
        "'string'",
    ],
)
def test_rejects_unsafe(expr: str) -> None:
    with pytest.raises(UnsafeExpressionError):
        safe_eval(expr)


def test_rejects_huge_exponent() -> None:
    with pytest.raises(UnsafeExpressionError):
        safe_eval("9 ** 9 ** 9")


def test_rejects_huge_result() -> None:
    with pytest.raises(UnsafeExpressionError):
        safe_eval("10 ** 50")


def test_division_by_zero() -> None:
    with pytest.raises(CalculationError):
        safe_eval("1 / 0")


def test_empty_expression() -> None:
    with pytest.raises(UnsafeExpressionError):
        safe_eval("   ")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `./run_tests.sh tests/test_calculator_safe_eval.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.calculator.safe_eval'`.

- [ ] **Step 3: Implement the evaluator**

Create `platform/agents/calculator/safe_eval.py`:

```python
"""Safe arithmetic evaluator for the Calculator Agent's open-math path.

The LLM proposes an arithmetic *expression*; this module owns the *math*.
Only a fixed allow-list of numeric operations and functions is permitted —
no names, attributes, calls, subscripts, or comprehensions outside the
whitelist — so an LLM-proposed string can never reach ``eval``/``exec`` or
touch the runtime.
"""

from __future__ import annotations

import ast
import math
from typing import Union

Number = Union[int, float]

# Guards to stop e.g. ``9 ** 9 ** 9`` pinning the CPU / exhausting memory.
_MAX_EXPONENT = 100
_MAX_OPERAND = 1e15

_ALLOWED_BINOPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)

_ALLOWED_FUNCS = {
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "sqrt": math.sqrt,
    "abs": abs,
    "min": min,
    "max": max,
}

_ALLOWED_NAMES = {
    "pi": math.pi,
    "e": math.e,
}


class UnsafeExpressionError(ValueError):
    """The expression contains a construct outside the arithmetic allow-list."""


class CalculationError(ValueError):
    """The expression is well-formed but cannot be evaluated (e.g. div by zero)."""


def safe_eval(expression: str) -> float:
    """Evaluate a numeric arithmetic expression from a restricted grammar.

    Raises ``UnsafeExpressionError`` for disallowed syntax and
    ``CalculationError`` for arithmetic failures. Always returns a float.
    """
    if not expression or not expression.strip():
        raise UnsafeExpressionError("empty expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"could not parse expression: {exc}") from exc
    try:
        result = _eval_node(tree.body)
    except ZeroDivisionError as exc:
        raise CalculationError("division by zero") from exc
    except OverflowError as exc:
        raise CalculationError("number too large") from exc
    return float(result)


def _eval_node(node: ast.AST) -> Number:
    if isinstance(node, ast.Constant):
        # bool is a subclass of int — reject it before the numeric check.
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise UnsafeExpressionError("only numeric constants are allowed")
        _check_magnitude(node.value)
        return node.value
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise UnsafeExpressionError(
                f"operator not allowed: {type(node.op).__name__}"
            )
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise UnsafeExpressionError("exponent too large")
        value = _apply_binop(node.op, left, right)
        _check_magnitude(value)
        return value
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARYOPS):
            raise UnsafeExpressionError(
                f"unary operator not allowed: {type(node.op).__name__}"
            )
        operand = _eval_node(node.operand)
        return +operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.Call):
        return _eval_call(node)
    if isinstance(node, ast.Name):
        if node.id not in _ALLOWED_NAMES:
            raise UnsafeExpressionError(f"name not allowed: {node.id}")
        return _ALLOWED_NAMES[node.id]
    raise UnsafeExpressionError(f"syntax not allowed: {type(node).__name__}")


def _eval_call(node: ast.Call) -> Number:
    if not isinstance(node.func, ast.Name):
        raise UnsafeExpressionError("only direct function calls are allowed")
    name = node.func.id
    if name not in _ALLOWED_FUNCS:
        raise UnsafeExpressionError(f"function not allowed: {name}")
    if node.keywords:
        raise UnsafeExpressionError("keyword arguments are not allowed")
    args = [_eval_node(arg) for arg in node.args]
    try:
        result = _ALLOWED_FUNCS[name](*args)
    except (TypeError, ValueError) as exc:
        raise CalculationError(f"invalid call to {name}: {exc}") from exc
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise CalculationError(f"{name} did not return a number")
    return result


def _apply_binop(op: ast.operator, left: Number, right: Number) -> Number:
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.Div):
        return left / right
    if isinstance(op, ast.FloorDiv):
        return left // right
    if isinstance(op, ast.Mod):
        return left % right
    # Only Pow remains from _ALLOWED_BINOPS.
    return left**right


def _check_magnitude(value: Number) -> None:
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        raise CalculationError("non-finite number")
    if abs(value) > _MAX_OPERAND:
        raise UnsafeExpressionError("number too large")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `./run_tests.sh tests/test_calculator_safe_eval.py`
Expected: PASS (all parametrized cases).

- [ ] **Step 5: Gates**

Run: `./run_mypy.sh agents/calculator/safe_eval.py && ./run_ruff.sh agents/calculator/safe_eval.py tests/test_calculator_safe_eval.py`
Expected: no errors.

- [ ] **Step 6: Commit** *(requires explicit user approval first)*

```bash
git -C platform add agents/calculator/safe_eval.py tests/test_calculator_safe_eval.py
git -C platform commit -m "feat: add safe arithmetic evaluator for calculator open-math path

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Output schemas + `open_math` calc type

**Files:**
- Modify: `platform/agents/calculator/schemas.py`
- Test: `platform/tests/test_calculator_open_math.py` (created here; extended in later tasks)

**Interfaces:**
- Produces: `OpenMathOption(label: str, expression: str, unit: str, detail: str | None)`; `OpenMathResult(interpretation: str, assumptions: list[str], options: list[OpenMathOption], note: str | None)`; `"open_math"` is a valid `CalculationRequest.calculation_type`.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_calculator_open_math.py`:

```python
"""Tests for the Calculator open-math path: schemas, formatter, solver, routing."""

import asyncio
from typing import Any, Dict, Optional

import pytest

from agents.calculator.schemas import (
    CalculationRequest,
    OpenMathOption,
    OpenMathResult,
)


class TestSchemas:
    def test_open_math_is_a_valid_calc_type(self) -> None:
        req = CalculationRequest(calculation_type="open_math")
        assert req.calculation_type == "open_math"

    def test_open_math_result_defaults(self) -> None:
        result = OpenMathResult(
            interpretation="stones along a path",
            options=[OpenMathOption(label="L", expression="1 + 1", unit="stones")],
        )
        assert result.assumptions == []
        assert result.note is None
        assert result.options[0].detail is None
```

- [ ] **Step 2: Run to verify failure**

Run: `./run_tests.sh tests/test_calculator_open_math.py::TestSchemas`
Expected: FAIL — `ImportError: cannot import name 'OpenMathOption'`.

- [ ] **Step 3: Implement the schema changes**

In `platform/agents/calculator/schemas.py`:

3a. Update the imports line `from typing import Literal, Optional` to:

```python
from typing import List, Literal, Optional
```

3b. Add `"open_math"` to the `calculation_type` `Literal` (immediately before `"unknown"`):

```python
        "plant_count",
        "open_math",
        "unknown",
    ] = Field(description="The type of landscaping calculation the user wants.")
```

3c. Append the two new models at the end of the file:

```python


class OpenMathOption(BaseModel):
    """One way to answer an open-math query. ``expression`` is computed by the
    backend safe evaluator — the LLM never supplies the final number."""

    label: str = Field(
        description="Short label for this option, e.g. 'Long side (3 ft) along the path'"
    )
    expression: str = Field(
        description=(
            "A single arithmetic expression to compute, e.g. "
            "'floor((240 + 3) / (36 + 3))'. Allowed: numbers, + - * / // % **, "
            "and floor/ceil/round/sqrt/abs/min/max. Do unit conversions inside "
            "the expression. No prose, no variables."
        )
    )
    unit: str = Field(description="Unit of the computed result, e.g. 'stones'")
    detail: Optional[str] = Field(
        default=None,
        description="Optional one-clause note, e.g. 'fills the 20 ft exactly'",
    )


class OpenMathResult(BaseModel):
    """Structured reasoning the researcher model returns for an open-math query."""

    interpretation: str = Field(
        description="One-line restatement of the problem in plain language"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made to solve it, e.g. 'a stone sits at each end'",
    )
    options: List[OpenMathOption] = Field(
        description="One option if unambiguous; several only on a genuine fork"
    )
    note: Optional[str] = Field(
        default=None, description="Optional short caveat or which option fits best"
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `./run_tests.sh tests/test_calculator_open_math.py::TestSchemas`
Expected: PASS.

- [ ] **Step 5: Gates**

Run: `./run_mypy.sh agents/calculator/schemas.py && ./run_ruff.sh agents/calculator/schemas.py tests/test_calculator_open_math.py`
Expected: no errors.

- [ ] **Step 6: Commit** *(requires explicit user approval first)*

```bash
git -C platform add agents/calculator/schemas.py tests/test_calculator_open_math.py
git -C platform commit -m "feat: add open-math schemas and calc type to calculator

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Open-math module — renderer + solver

**Files:**
- Create: `platform/agents/calculator/open_math.py`
- Test: `platform/tests/test_calculator_open_math.py` (extend)

**Interfaces:**
- Consumes: `safe_eval` + exceptions (Task 1); `OpenMathResult`, `OpenMathOption` (Task 2).
- Produces:
  - `format_open_math(interpretation: str, assumptions: list[str], computed_options: list[dict], note: str | None) -> str` — each dict has keys `label, expression, unit, detail, value`.
  - `async solve_open_math(message: str, llm: Any) -> OpenMathSolution | None`.
  - `OpenMathSolution(response: str, payload: dict)` dataclass.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_calculator_open_math.py`:

```python
from langchain_core.runnables import RunnableLambda  # noqa: E402

from agents.calculator.open_math import (  # noqa: E402
    OpenMathSolution,
    format_open_math,
    solve_open_math,
)


class _FakeLLM:
    """Stub matching the `llm.with_structured_output(...).ainvoke(...)` shape."""

    def __init__(self, result: OpenMathResult) -> None:
        self._result = result

    def with_structured_output(self, schema: Any, method: Optional[str] = None) -> Any:
        result = self._result

        async def _return(_: Any) -> OpenMathResult:
            return result

        return RunnableLambda(_return)


class TestFormatOpenMath:
    def test_renders_options_assumptions_and_working(self) -> None:
        md = format_open_math(
            interpretation="3 ft x 2 ft stones along a 20 ft path.",
            assumptions=["a stone sits at each end"],
            computed_options=[
                {
                    "label": "Long side (3 ft) along the path",
                    "expression": "floor((240 + 3) / (36 + 3))",
                    "unit": "stones",
                    "detail": "leaves 9 inches",
                    "value": 6.0,
                },
                {
                    "label": "Short side (2 ft) along the path",
                    "expression": "floor((240 + 3) / (24 + 3))",
                    "unit": "stones",
                    "detail": "fills the 20 ft exactly",
                    "value": 9.0,
                },
            ],
            note="9 fits exactly.",
        )
        assert "**Long side (3 ft) along the path: 6 stones**" in md
        assert "leaves 9 inches" in md
        assert "**Short side (2 ft) along the path: 9 stones**" in md
        assert "Assumptions: a stone sits at each end" in md
        assert "`floor((240 + 3) / (36 + 3))` = 6" in md
        assert md.strip().endswith("9 fits exactly.")


class TestSolveOpenMath:
    def test_computes_and_builds_payload(self) -> None:
        result = OpenMathResult(
            interpretation="stones along a path",
            assumptions=["a stone sits at each end"],
            options=[
                OpenMathOption(
                    label="Long side (3 ft)",
                    expression="floor((240 + 3) / (36 + 3))",
                    unit="stones",
                ),
                OpenMathOption(
                    label="Short side (2 ft)",
                    expression="floor((240 + 3) / (24 + 3))",
                    unit="stones",
                ),
            ],
        )
        solution = asyncio.run(solve_open_math("q", _FakeLLM(result)))
        assert isinstance(solution, OpenMathSolution)
        assert [o["value"] for o in solution.payload["options"]] == [6.0, 9.0]
        assert "6 stones" in solution.response
        assert "9 stones" in solution.response

    def test_drops_unsafe_option_keeps_safe(self) -> None:
        result = OpenMathResult(
            interpretation="x",
            options=[
                OpenMathOption(label="good", expression="floor(20 / 3)", unit="stones"),
                OpenMathOption(label="bad", expression="os.system('x')", unit="stones"),
            ],
        )
        solution = asyncio.run(solve_open_math("q", _FakeLLM(result)))
        assert solution is not None
        assert len(solution.payload["options"]) == 1
        assert solution.payload["options"][0]["value"] == 6.0

    def test_returns_none_when_all_options_unsafe(self) -> None:
        result = OpenMathResult(
            interpretation="x",
            options=[
                OpenMathOption(label="bad", expression="__import__('os')", unit="u"),
            ],
        )
        solution = asyncio.run(solve_open_math("q", _FakeLLM(result)))
        assert solution is None
```

- [ ] **Step 2: Run to verify failure**

Run: `./run_tests.sh tests/test_calculator_open_math.py::TestFormatOpenMath tests/test_calculator_open_math.py::TestSolveOpenMath`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.calculator.open_math'`.

- [ ] **Step 3: Implement the module**

Create `platform/agents/calculator/open_math.py`:

```python
"""Open math-reasoning path for the Calculator Agent (tier 3).

Fires only when the parameter extractor classifies a query as ``open_math``
(no curated formula models it) and ``CALCULATOR_OPEN_MATH_ENABLED`` is on.
The researcher model proposes an interpretation, assumptions, and one or more
options — each carrying an arithmetic *expression*, never a final number.
``safe_eval`` computes every expression, so the arithmetic is exact and
auditable while the model only supplies the reasoning structure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from agents.calculator.safe_eval import (
    CalculationError,
    UnsafeExpressionError,
    safe_eval,
)
from agents.calculator.schemas import OpenMathResult

logger = logging.getLogger(__name__)

_REASONING_SYSTEM_PROMPT = """\
You are a calculator for a landscaping / field-service app. The user asks a
quantity, layout, spacing, or measurement question. Work it out and return
structured reasoning — DO NOT put final numbers in any field.

Hard rules:
- Put ALL arithmetic in each option's `expression` field as ONE formula.
- `expression` may use only: numbers, + - * / // % **, and the functions
  floor, ceil, round, sqrt, abs, min, max. Do unit conversions inside the
  expression (e.g. 20 feet -> 20*12 for inches). Never write prose in it.
- Counts of physical items must be whole: wrap them in floor(...) or ceil(...)
  as appropriate (you cannot buy a fraction of a stone, paver, or plant).
- State the assumptions you made (e.g. "a stone sits at each end").
- Add a SECOND option ONLY when there is a genuine fork in the problem (for
  example two possible orientations). One option otherwise. Never more than 3.
- `unit` is the unit of the computed result (e.g. "stones", "bags").
- Keep `interpretation`, each `detail`, and `note` to one short clause.
"""


@dataclass
class OpenMathSolution:
    response: str
    payload: Dict[str, Any]


def _fmt_value(value: float) -> str:
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.2f}"


def format_open_math(
    interpretation: str,
    assumptions: List[str],
    computed_options: List[Dict[str, Any]],
    note: Optional[str],
) -> str:
    """Render the markdown shown to the user. Pure — no LLM, no IO."""
    lines: List[str] = [interpretation, ""]
    for opt in computed_options:
        line = f"- **{opt['label']}: {_fmt_value(opt['value'])} {opt['unit']}**"
        if opt.get("detail"):
            line += f" — {opt['detail']}"
        lines.append(line)
    lines.append("")
    if assumptions:
        lines.append("Assumptions: " + "; ".join(assumptions))
    working = " · ".join(
        f"`{opt['expression']}` = {_fmt_value(opt['value'])}" for opt in computed_options
    )
    lines.append(f"Working: {working}")
    if note:
        lines.extend(["", note])
    return "\n".join(lines)


async def solve_open_math(message: str, llm: Any) -> Optional[OpenMathSolution]:
    """Run the researcher reasoning call, evaluate expressions, format output.

    Returns ``None`` when no option could be safely evaluated, so the caller
    can fall back to a graceful clarification instead of a wrong/blank answer.
    """
    prompt = ChatPromptTemplate.from_messages(
        [("system", _REASONING_SYSTEM_PROMPT), ("human", "{message}")]
    )
    chain = prompt | llm.with_structured_output(
        OpenMathResult, method="function_calling"
    )
    result: OpenMathResult = await chain.ainvoke({"message": message})

    computed_options: List[Dict[str, Any]] = []
    for opt in result.options:
        try:
            value = safe_eval(opt.expression)
        except (UnsafeExpressionError, CalculationError) as exc:
            logger.warning("open_math: dropped option %r (%s)", opt.expression, exc)
            continue
        computed_options.append(
            {
                "label": opt.label,
                "expression": opt.expression,
                "unit": opt.unit,
                "detail": opt.detail,
                "value": value,
            }
        )

    if not computed_options:
        return None

    response = format_open_math(
        result.interpretation, result.assumptions, computed_options, result.note
    )
    payload: Dict[str, Any] = {
        "interpretation": result.interpretation,
        "assumptions": result.assumptions,
        "options": computed_options,
        "note": result.note,
    }
    return OpenMathSolution(response=response, payload=payload)
```

- [ ] **Step 4: Run to verify pass**

Run: `./run_tests.sh tests/test_calculator_open_math.py::TestFormatOpenMath tests/test_calculator_open_math.py::TestSolveOpenMath`
Expected: PASS.

- [ ] **Step 5: Gates**

Run: `./run_mypy.sh agents/calculator/open_math.py && ./run_ruff.sh agents/calculator/open_math.py tests/test_calculator_open_math.py`
Expected: no errors. (Note: the `# noqa: E402` on the mid-file test imports is intentional — they sit below the first test class.)

- [ ] **Step 6: Commit** *(requires explicit user approval first)*

```bash
git -C platform add agents/calculator/open_math.py tests/test_calculator_open_math.py
git -C platform commit -m "feat: add open-math researcher solver and renderer

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Config flag + service routing

**Files:**
- Modify: `platform/config.py`
- Modify: `platform/agents/calculator/service.py`
- Modify: `platform/.env.example`
- Test: `platform/tests/test_calculator_open_math.py` (extend)

**Interfaces:**
- Consumes: `solve_open_math`, `OpenMathSolution` (Task 3); `settings.calculator_open_math_enabled` (this task).
- Produces: `CalculatorAgent(__init__)` gains `reasoning_llm: Any | None = None`; `process()` routes `calculation_type == "open_math"` to `_handle_open_math`, which returns the standard envelope with `result = {"operation": "calculate", "open_math": <payload>}` (flag on, success) or a menu clarification (flag off / all-unsafe).

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_calculator_open_math.py`:

```python
from agents.calculator.service import CalculatorAgent  # noqa: E402


async def _fake_extract_open_math(
    self: Any, message: str, context: Optional[Dict[str, Any]] = None
) -> CalculationRequest:
    return CalculationRequest(calculation_type="open_math")


class TestProcessRouting:
    def test_flag_on_routes_to_open_math(self, monkeypatch: Any) -> None:
        from config import settings

        monkeypatch.setattr(settings, "calculator_open_math_enabled", True)
        monkeypatch.setattr(
            CalculatorAgent, "_extract_with_llm", _fake_extract_open_math
        )

        async def fake_solve(message: str, llm: Any) -> OpenMathSolution:
            return OpenMathSolution(
                response="- **Short side: 9 stones**",
                payload={"options": [{"value": 9.0}]},
            )

        monkeypatch.setattr(
            "agents.calculator.service.solve_open_math", fake_solve
        )

        agent = CalculatorAgent(use_llm=True, llm=object(), reasoning_llm=object())
        result = asyncio.run(
            agent.process("how many 2 ft stones along a 20 ft path 3 inches apart")
        )

        assert result["success"] is True
        assert result["needs_clarification"] is False
        assert "9 stones" in result["response"]
        assert result["result"]["open_math"]["options"][0]["value"] == 9.0

    def test_flag_off_falls_back_without_calling_solver(
        self, monkeypatch: Any
    ) -> None:
        from config import settings

        monkeypatch.setattr(settings, "calculator_open_math_enabled", False)
        monkeypatch.setattr(
            CalculatorAgent, "_extract_with_llm", _fake_extract_open_math
        )

        called = {"solve": False}

        async def fake_solve(message: str, llm: Any) -> OpenMathSolution:
            called["solve"] = True
            return OpenMathSolution(response="x", payload={})

        monkeypatch.setattr(
            "agents.calculator.service.solve_open_math", fake_solve
        )

        agent = CalculatorAgent(use_llm=True, llm=object())
        result = asyncio.run(
            agent.process("how many 2 ft stones along a 20 ft path 3 inches apart")
        )

        assert called["solve"] is False
        assert result["needs_clarification"] is True
        assert "calculate" in result["response"].lower()

    def test_flag_on_all_unsafe_falls_back(self, monkeypatch: Any) -> None:
        from config import settings

        monkeypatch.setattr(settings, "calculator_open_math_enabled", True)
        monkeypatch.setattr(
            CalculatorAgent, "_extract_with_llm", _fake_extract_open_math
        )

        async def fake_solve(message: str, llm: Any) -> None:
            return None

        monkeypatch.setattr(
            "agents.calculator.service.solve_open_math", fake_solve
        )

        agent = CalculatorAgent(use_llm=True, llm=object(), reasoning_llm=object())
        result = asyncio.run(agent.process("compute something impossible"))

        assert result["needs_clarification"] is True
        assert result["result"] is None
```

- [ ] **Step 2: Run to verify failure**

Run: `./run_tests.sh tests/test_calculator_open_math.py::TestProcessRouting`
Expected: FAIL — `AttributeError: ... 'Settings' object has no attribute 'calculator_open_math_enabled'` (or `_handle_open_math` missing).

- [ ] **Step 3a: Add the config flag**

In `platform/config.py`, alongside the other agent toggles (e.g. just after `estimate_react_mode_enabled`), add:

```python
    calculator_open_math_enabled: bool = Field(
        default=False, validation_alias="CALCULATOR_OPEN_MATH_ENABLED"
    )
```

(`Field` is already imported in `config.py`.)

- [ ] **Step 3b: Wire the service**

In `platform/agents/calculator/service.py`:

3b-i. Add a module logger and the open-math import near the top imports:

```python
import logging
```

and below the existing `from agents.calculator.text_helpers import (...)` block:

```python
from agents.calculator.open_math import OpenMathSolution, solve_open_math
```

then after the `CALCULATOR_AGENT_LABEL = "Calculator Agent"` line:

```python
logger = logging.getLogger(__name__)
```

3b-ii. Extract the menu string to a module constant (DRY — it is reused by the `open_math`-off branch). Add near the other module constants:

```python
_CALCULATOR_MENU = (
    "I can help with landscaping calculations! What would you like to calculate?\n\n"
    "I can do:\n"
    "- **Area coverage** (mulch, topsoil, gravel)\n"
    "- **Concrete volume** (slabs, footings)\n"
    "- **Seed/fertilizer** coverage\n"
    "- **Linear materials** (fencing, edging)\n"
    "- **Paver/stone count**\n"
    "- **Unit conversions**"
)

_OPEN_MATH_FALLBACK = (
    "I couldn't work that one out reliably. Could you give me the measurements "
    "and tell me what you'd like to calculate?"
)
```

3b-iii. Replace the inline menu string in `process()` with the constant. The existing block:

```python
        if params is None or params.calculation_type == "unknown":
            # Abandon any half-gathered calculation — the user is starting over.
            ctx.pop(PENDING_CALCULATION_CONTEXT_KEY, None)
            return self._clarification_response(
                message,
                "I can help with landscaping calculations! What would you like to calculate?\n\n"
                "I can do:\n"
                "- **Area coverage** (mulch, topsoil, gravel)\n"
                "- **Concrete volume** (slabs, footings)\n"
                "- **Seed/fertilizer** coverage\n"
                "- **Linear materials** (fencing, edging)\n"
                "- **Paver/stone count**\n"
                "- **Unit conversions**",
                ctx,
            )

        return self._finalize(message, params, ctx)
```

becomes:

```python
        if params is None or params.calculation_type == "unknown":
            # Abandon any half-gathered calculation — the user is starting over.
            ctx.pop(PENDING_CALCULATION_CONTEXT_KEY, None)
            return self._clarification_response(message, _CALCULATOR_MENU, ctx)

        if params.calculation_type == "open_math":
            return await self._handle_open_math(message, ctx)

        return self._finalize(message, params, ctx)
```

3b-iv. Extend `__init__` to accept an injectable reasoning LLM. The existing signature:

```python
    def __init__(self, use_llm: bool = True, llm: Optional[Any] = None) -> None:
        self.use_llm = use_llm
        self.llm = llm
        if self.use_llm and self.llm is None:
            from services.llm import create_chat_model

            self.llm = create_chat_model(
                "worker",
                temperature=0,
                openai_api_key=settings.openai_api_key,
            )
```

becomes:

```python
    def __init__(
        self,
        use_llm: bool = True,
        llm: Optional[Any] = None,
        reasoning_llm: Optional[Any] = None,
    ) -> None:
        self.use_llm = use_llm
        self.llm = llm
        # Lazily constructed on first open_math hit so the researcher client is
        # never created when the flag is off or the path is never used.
        self.reasoning_llm = reasoning_llm
        if self.use_llm and self.llm is None:
            from services.llm import create_chat_model

            self.llm = create_chat_model(
                "worker",
                temperature=0,
                openai_api_key=settings.openai_api_key,
            )
```

3b-v. Add the handler + lazy getter (place near `_finalize`):

```python
    def _get_reasoning_llm(self) -> Any:
        if self.reasoning_llm is None:
            from services.llm import create_chat_model

            self.reasoning_llm = create_chat_model(
                "researcher",
                temperature=0,
                openai_api_key=settings.openai_api_key,
            )
        return self.reasoning_llm

    async def _handle_open_math(
        self, message: str, ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tier-3 path: only when the flag is on and the LLM is available."""
        if not (settings.calculator_open_math_enabled and self.use_llm):
            ctx.pop(PENDING_CALCULATION_CONTEXT_KEY, None)
            return self._clarification_response(message, _CALCULATOR_MENU, ctx)

        solution: Optional[OpenMathSolution]
        try:
            solution = await solve_open_math(message, self._get_reasoning_llm())
        except Exception:  # broad by design — any LLM/parse failure must fail soft
            logger.exception("open_math solve failed for %r", message)
            solution = None

        # Single-shot path — never leaves pending state behind.
        ctx.pop(PENDING_CALCULATION_CONTEXT_KEY, None)

        if solution is None:
            return self._clarification_response(message, _OPEN_MATH_FALLBACK, ctx)

        return {
            "success": True,
            "query": message,
            "intent": "calculate",
            "response": solution.response,
            "result": {"operation": "calculate", "open_math": solution.payload},
            "needs_clarification": False,
            "context": ctx,
        }
```

3b-vi. Sharpen the extraction prompt (TDD-exempt prompt text). In `_EXTRACTION_SYSTEM_PROMPT`, change the type list tail and rules. The existing tail:

```python
Calculation types:
{_TYPE_HINTS}
- unknown: cannot determine the calculation type

Rules:
- "3 inches" or "3-inch" or "3 in" → depth_inches=3
- "2000 sq ft" or "2000 square feet" → area_sqft=2000
- "10% waste" → waste_factor_pct=10
- "10x12 slab" → length_ft=10, width_ft=12
- If a parameter is not mentioned, leave it as null.
- If you can't determine the calculation type, set it to "unknown".
- Extract material_name when mentioned (e.g. "mulch", "topsoil", "gravel").
"""
```

becomes:

```python
Calculation types:
{_TYPE_HINTS}
- open_math: a quantity/layout/measurement problem that NONE of the formulas
  above models faithfully — e.g. items spaced along a run with gaps between
  them, composite or irregular shapes, or a count with two possible
  orientations. Pick this instead of forcing a poor fit.
- unknown: the message is not a calculation request at all.

Rules:
- "3 inches" or "3-inch" or "3 in" → depth_inches=3
- "2000 sq ft" or "2000 square feet" → area_sqft=2000
- "10% waste" → waste_factor_pct=10
- "10x12 slab" → length_ft=10, width_ft=12
- Choose a specific type ONLY when its formula faithfully represents the
  request (every value the user gave maps to one of its parameters). If the
  request needs something the formula can't express — gaps between spaced
  pieces, more than one orientation, multiple shapes — set type to "open_math".
- Use "unknown" only when the message is not a calculation at all.
- If a parameter is not mentioned, leave it as null.
- Extract material_name when mentioned (e.g. "mulch", "topsoil", "gravel").

Examples:
- "how many 16x16 in pavers for a 200 sq ft patio" → paver_count
- "how many plants for a 10x12 bed at 18 inch spacing" → plant_count
- "how many 2 ft stones along a 20 ft path, 3 inches apart" → open_math
  (gaps along a linear run are not representable by linear_material)
"""
```

- [ ] **Step 3c: Document the env var**

In `platform/.env.example`, add (near other feature toggles):

```bash
# Enable the Calculator agent's open math-reasoning path (tier 3). When off,
# queries no curated formula models return a clarification instead.
CALCULATOR_OPEN_MATH_ENABLED=false
```

- [ ] **Step 4: Run to verify pass**

Run: `./run_tests.sh tests/test_calculator_open_math.py::TestProcessRouting`
Expected: PASS (all three).

- [ ] **Step 5: Regression + gates**

Run: `./run_tests.sh tests/test_calculator_agent.py tests/test_calculator_registry.py tests/test_calculator_text_helpers.py tests/test_calculator_formulas.py`
Expected: PASS (no curated regression).

Run: `./run_mypy.sh agents/calculator/service.py config.py && ./run_ruff.sh agents/calculator/service.py config.py tests/test_calculator_open_math.py`
Expected: no errors.

- [ ] **Step 6: Commit** *(requires explicit user approval first)*

```bash
git -C platform add agents/calculator/service.py config.py .env.example tests/test_calculator_open_math.py
git -C platform commit -m "feat: route open_math queries through flag-gated reasoning path

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Opt-in live classification test

**Files:**
- Create: `platform/tests/test_calculator_open_math_live.py`

**Interfaces:**
- Consumes: the sharpened extractor (Task 4) and the real worker model. Excluded from the default run by the `llm_e2e` marker; skipped without `OPENAI_API_KEY`.

- [ ] **Step 1: Write the test**

Create `platform/tests/test_calculator_open_math_live.py`:

```python
"""Opt-in live-LLM checks that the sharpened extractor classifies non-curated
layout queries as `open_math` rather than force-fitting a curated formula.

Run with: ./run_tests.sh tests/test_calculator_open_math_live.py -m llm_e2e
"""

import asyncio
from typing import Any

import pytest

from agents.calculator.service import CalculatorAgent
from config import settings

_SKIP = "requires OPENAI_API_KEY (opt-in llm_e2e test)"


@pytest.mark.llm_e2e
@pytest.mark.skipif(not settings.openai_api_key, reason=_SKIP)
@pytest.mark.parametrize(
    "query",
    [
        "how many stepping stones do i need if the stones are 3 ft by 2 ft "
        "and the path is 20 feet long and I want them to be 3-inches apart",
        "how many 18 inch pavers along a 30 ft walkway with 2 inch gaps",
    ],
)
def test_spaced_layout_classifies_as_open_math(query: str) -> None:
    agent = CalculatorAgent(use_llm=True)
    extracted: Any = asyncio.run(agent._extract_with_llm(query))
    assert extracted.calculation_type == "open_math"
```

- [ ] **Step 2: Run it (only meaningful with a key)**

Run: `./run_tests.sh tests/test_calculator_open_math_live.py -m llm_e2e`
Expected: PASS if `OPENAI_API_KEY` is set; otherwise SKIPPED. Also confirm the default run excludes it:
Run: `./run_tests.sh tests/test_calculator_open_math_live.py` → reports 0 selected / deselected by the `-m "not ... llm_e2e"` default in `pytest.ini`.

- [ ] **Step 3: Gates**

Run: `./run_ruff.sh tests/test_calculator_open_math_live.py && ./run_mypy.sh tests/test_calculator_open_math_live.py`
Expected: no errors. (Accessing `agent._extract_with_llm` in a test mirrors the existing suite's use of internals.)

- [ ] **Step 4: Commit** *(requires explicit user approval first)*

```bash
git -C platform add tests/test_calculator_open_math_live.py
git -C platform commit -m "test: add opt-in live classification check for open_math

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Post-implementation verification (manual, by the user)

1. Set `CALCULATOR_OPEN_MATH_ENABLED=true` in `.env.local`, run `uvicorn main:app --reload`, and ask Maple the stepping-stones query. Expect both orientations (6 and 9) with a stated assumption and a `Working:` line.
2. Run the full backend suite (`./run_tests.sh`) and the live tier (`./run_tests.sh tests/test_calculator_open_math_live.py -m llm_e2e`) when ready.
3. Update `documentation/development/maple-phrasing-reference.md` if this changes the supported-phrasing snapshot (per CLAUDE.md's Maple-phrasing rule) — spaced-layout queries move from a mis-map to `open_math`.

## Related follow-ups (NOT in this plan — see design §10)

1. Whole-number rounding for the fractional-count curated formulas (`linear_material`, `paver_count`, `plant_count`, `retaining_wall_blocks`).
2. Deciding whether to broaden the orchestrator entry gate (`is_calculation_query`) so unitless math reaches the calculator.
3. Promoting hot open-math patterns to curated formulas.
