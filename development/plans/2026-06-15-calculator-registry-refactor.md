# Calculator Registry Refactor + New Primitives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Calculator Agent's hand-synced per-type dicts and `_dispatch()` if-ladder with a single declarative `CalcSpec` registry, so adding a landscaping calculation becomes one formula + one registry entry; then add new deterministic primitives (aggregate tons, mulch bags, retaining-wall blocks, step count) on top of it.

**Architecture:** A new `agents/calculator/registry.py` holds a `CalcSpec` dataclass and a `REGISTRY: dict[str, CalcSpec]`. Each spec carries the type key, friendly label, required params, the pure compute callable (from `formulas.py`), and the one-line extraction-prompt hint. `service.py` derives `_REQUIRED_PARAMS`, the type→label map, the `_dispatch()` body, and the prompt's type list *from* the registry — eliminating the parallel structures. The LLM still only extracts; all math stays in pure `formulas.py`.

**Tech Stack:** Python 3, FastAPI, LangChain (`with_structured_output`), Pydantic, pytest. Gates: `./run_mypy.sh`, `./run_ruff.sh`, `./run_tests.sh`.

**Scope note:** Hydraulics calcs from the wishlist (irrigation TDH/GPM, runoff, pipe sizing) are **deliberately deferred** — they need carefully-reviewed engineering formulas and carry install/liability risk; not in this plan. Plant grid-spacing and grading pitch introduce a string `pattern` field / a no-waste shape and are documented as Phase 3 follow-on, not implemented here.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `agents/calculator/registry.py` | `CalcSpec` dataclass + `REGISTRY` of all calc types; the single source of truth | **Create** |
| `agents/calculator/formulas.py` | Pure math functions returning `CalculationResult` | **Modify** (add new primitives) |
| `agents/calculator/schemas.py` | `CalculationRequest` — add new `Literal` members + new optional fields | **Modify** |
| `agents/calculator/service.py` | Agent orchestration — derive dispatch/labels/required/prompt from registry | **Modify** |
| `tests/test_calculator_registry.py` | Registry-vs-schema drift guard + spec integrity | **Create** |
| `tests/test_calculator_formulas.py` | Formula unit tests | **Modify** (add new-primitive tests) |
| `tests/test_calculator_agent.py` | Agent-level behavior | **Modify** (add new-type end-to-end test) |
| `agents/calculator/text_helpers.py` | Orchestrator pre-classifier unit tokens | **Modify** (add `plants`/`steps` later; tons/bags/blocks already present) |
| `documentation/development/maple-phrasing-reference.md` | Canonical phrasing catalog (CLAUDE.md-mandated) | **Modify** |

---

## Phase 1 — Registry refactor (behavior-preserving)

The existing test suite (`test_calculator_formulas.py`, `test_calculator_agent.py`, `test_agent_helpers_pending_calculation.py`) is the behavior lock. Phase 1 must keep all of it green without edits.

### Task 1: Create the registry module

**Files:**
- Create: `agents/calculator/registry.py`
- Test: `tests/test_calculator_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_calculator_registry.py
"""Registry integrity + drift guard for the Calculator Agent."""

from typing import get_args

from agents.calculator.registry import REGISTRY, CalcSpec
from agents.calculator.schemas import CalculationRequest


def test_registry_entries_are_calcspecs():
    assert REGISTRY
    for key, spec in REGISTRY.items():
        assert isinstance(spec, CalcSpec)
        assert spec.type == key
        assert spec.label
        assert spec.required
        assert callable(spec.compute)
        assert spec.prompt_hint


def test_registry_matches_schema_literal():
    """Every calculation_type in the schema (except 'unknown') has exactly one
    registry entry, and vice-versa. This makes drift a test failure."""
    literal_types = set(get_args(CalculationRequest.model_fields["calculation_type"].annotation))
    literal_types.discard("unknown")
    assert set(REGISTRY.keys()) == literal_types


def test_required_fields_exist_on_schema():
    valid = set(CalculationRequest.model_fields.keys())
    for spec in REGISTRY.values():
        for field in spec.required:
            assert field in valid, f"{spec.type} requires unknown field {field}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform && ./run_tests.sh tests/test_calculator_registry.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.calculator.registry'`

- [ ] **Step 3: Write the registry**

```python
# agents/calculator/registry.py
"""Declarative registry of landscaping calculations.

Single source of truth: each ``CalcSpec`` binds a calculation_type to its
friendly label, required parameters, the pure compute callable from
``formulas.py``, and the one-line hint injected into the extraction prompt.
``service.py`` derives its dispatch table, required-params map, label map, and
the prompt's type list from this registry — so adding a calculation is one
entry here plus one formula function, nothing scattered across the agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from agents.calculator.formulas import (
    CalculationResult,
    area_coverage_volume,
    concrete_volume,
    linear_material_quantity,
    paver_stone_count,
    seed_fertilizer_coverage,
    unit_conversion,
)
from agents.calculator.schemas import CalculationRequest


@dataclass(frozen=True)
class CalcSpec:
    type: str
    label: str
    required: Tuple[str, ...]
    compute: Callable[[CalculationRequest], CalculationResult]
    prompt_hint: str


def _area_coverage(p: CalculationRequest) -> CalculationResult:
    assert p.area_sqft is not None
    assert p.depth_inches is not None
    return area_coverage_volume(p.area_sqft, p.depth_inches, p.waste_factor_pct or 0.0)


def _concrete(p: CalculationRequest) -> CalculationResult:
    assert p.length_ft is not None
    assert p.width_ft is not None
    assert p.depth_inches is not None
    return concrete_volume(p.length_ft, p.width_ft, p.depth_inches, p.waste_factor_pct or 0.0)


def _seed(p: CalculationRequest) -> CalculationResult:
    assert p.area_sqft is not None
    assert p.application_rate is not None
    return seed_fertilizer_coverage(p.area_sqft, p.application_rate, p.waste_factor_pct or 0.0)


def _linear(p: CalculationRequest) -> CalculationResult:
    assert p.linear_ft is not None
    return linear_material_quantity(p.linear_ft, p.piece_length_ft or 1.0, p.waste_factor_pct or 0.0)


def _paver(p: CalculationRequest) -> CalculationResult:
    assert p.area_sqft is not None
    assert p.paver_length_inches is not None
    assert p.paver_width_inches is not None
    return paver_stone_count(
        p.area_sqft, p.paver_length_inches, p.paver_width_inches, p.waste_factor_pct or 0.0
    )


def _conversion(p: CalculationRequest) -> CalculationResult:
    assert p.value is not None
    assert p.from_unit is not None
    assert p.to_unit is not None
    return unit_conversion(p.value, p.from_unit, p.to_unit)


REGISTRY: Dict[str, CalcSpec] = {
    "area_coverage": CalcSpec(
        type="area_coverage",
        label="coverage",
        required=("area_sqft", "depth_inches"),
        compute=_area_coverage,
        prompt_hint="area_coverage: mulch, topsoil, gravel coverage (needs area_sqft + depth_inches)",
    ),
    "concrete_volume": CalcSpec(
        type="concrete_volume",
        label="concrete",
        required=("length_ft", "width_ft", "depth_inches"),
        compute=_concrete,
        prompt_hint="concrete_volume: concrete slabs/footings (needs length_ft + width_ft + depth_inches)",
    ),
    "seed_coverage": CalcSpec(
        type="seed_coverage",
        label="seed/fertilizer",
        required=("area_sqft", "application_rate"),
        compute=_seed,
        prompt_hint="seed_coverage: seed, fertilizer, lime (needs area_sqft + application_rate per 1000 sq ft)",
    ),
    "linear_material": CalcSpec(
        type="linear_material",
        label="linear material",
        required=("linear_ft",),
        compute=_linear,
        prompt_hint="linear_material: fencing, edging, borders (needs linear_ft, optionally piece_length_ft)",
    ),
    "paver_count": CalcSpec(
        type="paver_count",
        label="paver",
        required=("area_sqft", "paver_length_inches", "paver_width_inches"),
        compute=_paver,
        prompt_hint="paver_count: pavers, bricks, stones (needs area_sqft + paver_length_inches + paver_width_inches)",
    ),
    "unit_conversion": CalcSpec(
        type="unit_conversion",
        label="conversion",
        required=("value", "from_unit", "to_unit"),
        compute=_conversion,
        prompt_hint="unit_conversion: convert between units (needs value + from_unit + to_unit)",
    ),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform && ./run_tests.sh tests/test_calculator_registry.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Gates**

Run: `cd platform && ./run_ruff.sh agents/calculator/registry.py && ./run_mypy.sh agents/calculator/registry.py`
Expected: clean

### Task 2: Derive service.py internals from the registry

**Files:**
- Modify: `agents/calculator/service.py`

- [ ] **Step 1: Replace the type-keyed constants with registry derivations.**

Delete `_REQUIRED_PARAMS` (lines ~81-88) and `_CALC_TYPE_LABELS` (lines ~105-112). Replace the import block + constants region so the file imports the registry and derives:

```python
from agents.calculator.registry import REGISTRY

_REQUIRED_PARAMS: Dict[str, List[str]] = {t: list(s.required) for t, s in REGISTRY.items()}
_CALC_TYPE_LABELS: Dict[str, str] = {t: s.label for t, s in REGISTRY.items()}
```

Keep `_MISSING_PARAM_LABELS` as-is (field-keyed, shared across types — not registry-derived).

- [ ] **Step 2: Build the extraction prompt's type list from the registry.**

Replace the hardcoded `Calculation types:` block inside `_EXTRACTION_SYSTEM_PROMPT` with a composed constant. Above the prompt:

```python
_TYPE_HINTS = "\n".join(f"- {s.prompt_hint}" for s in REGISTRY.values())

_EXTRACTION_SYSTEM_PROMPT = f"""\
You are a parameter extractor for landscaping calculations.
Given a user message, extract the calculation type and numeric parameters.
Do NOT perform any math — just identify what the user wants calculated
and extract the numbers they provided.

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

(Note: this is now an f-string — the only braces in the body are the literal rules above, which contain none, so no escaping is needed.)

- [ ] **Step 3: Replace the `_dispatch()` if-ladder with a registry lookup.**

Replace the entire `_dispatch` method body (lines ~286-347) with:

```python
    def _dispatch(self, params: CalculationRequest) -> CalculationResult:
        spec = REGISTRY.get(params.calculation_type)
        if spec is None:
            raise ValueError(f"Unsupported calculation type: {params.calculation_type}")
        return spec.compute(params)
```

Remove the now-unused direct formula imports from `service.py` (`area_coverage_volume`, `concrete_volume`, `linear_material_quantity`, `paver_stone_count`, `seed_fertilizer_coverage`, `unit_conversion`) — keep `CalculationResult` (still referenced in type hints). `CalculationRequest` stays.

- [ ] **Step 4: Derive `_PERSISTED_PARAM_FIELDS` from the schema (kill the manual list).**

Replace the hardcoded tuple (lines ~42-54) with:

```python
# Numeric/value params that survive into a pending-calculation record.
# Derived from the schema so a new field can never silently desync. Excludes
# the type key, material name, and the free-text conversion units (re-parsed).
_PERSISTED_PARAM_FIELDS = tuple(
    f for f in CalculationRequest.model_fields
    if f not in {"calculation_type", "material_name", "from_unit", "to_unit"}
)
```

- [ ] **Step 5: Run the full calculator test suite to verify behavior is preserved.**

Run: `cd platform && ./run_tests.sh tests/test_calculator_agent.py tests/test_calculator_formulas.py tests/test_calculator_registry.py tests/test_agent_helpers_pending_calculation.py -q`
Expected: PASS (all existing tests green, no edits to them)

- [ ] **Step 6: Gates**

Run: `cd platform && ./run_ruff.sh agents/calculator/ && ./run_mypy.sh agents/calculator/`
Expected: clean (watch for F401 on the removed formula imports — that's the signal they were correctly dropped)

### Task 3: Commit Phase 1

- [ ] **Step 1: Stage + request approval, then commit**

```bash
git add agents/calculator/registry.py agents/calculator/service.py tests/test_calculator_registry.py
git commit -m "refactor: drive Calculator Agent from a CalcSpec registry"
```

(Commit needs explicit user approval per CLAUDE.md — do not chain.)

---

## Phase 2 — New primitives (one entry each, proving the refactor)

Each task: add the pure formula (+ tests), add the `Literal` member and any new schema fields, add one `CalcSpec` entry with its compute wrapper, add field labels. No `service.py` `_dispatch` edits — that's the payoff.

### Task 4: Aggregate tonnage (gravel/crushed-stone base by weight)

**Files:**
- Modify: `agents/calculator/formulas.py`, `schemas.py`, `registry.py`, `service.py` (`_MISSING_PARAM_LABELS` only)
- Test: `tests/test_calculator_formulas.py`

- [ ] **Step 1: Write the failing formula test**

```python
# in tests/test_calculator_formulas.py
from agents.calculator.formulas import aggregate_tonnage


class TestAggregateTonnage:
    def test_basic(self):
        # 100 sq ft x 4 in / 12 = 33.33 cu ft / 27 = 1.2346 cu yd x 1.5 = 1.85 tons
        r = aggregate_tonnage(area_sqft=100, depth_inches=4)
        assert r.unit == "tons"
        assert r.quantity == pytest.approx(1.85, abs=0.01)

    def test_custom_density(self):
        r = aggregate_tonnage(area_sqft=100, depth_inches=4, tons_per_cubic_yard=1.6)
        assert r.quantity == pytest.approx(1.98, abs=0.01)

    def test_with_waste(self):
        r = aggregate_tonnage(area_sqft=100, depth_inches=4, waste_factor_pct=10)
        assert r.total_quantity == pytest.approx(2.04, abs=0.01)

    def test_rejects_zero_area(self):
        with pytest.raises(ValueError, match="area"):
            aggregate_tonnage(area_sqft=0, depth_inches=4)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd platform && ./run_tests.sh tests/test_calculator_formulas.py::TestAggregateTonnage -q`
Expected: FAIL — `ImportError: cannot import name 'aggregate_tonnage'`

- [ ] **Step 3: Implement the formula**

```python
# in agents/calculator/formulas.py
_DEFAULT_TONS_PER_CUYD = 1.5


def aggregate_tonnage(
    area_sqft: float,
    depth_inches: float,
    tons_per_cubic_yard: float = _DEFAULT_TONS_PER_CUYD,
    waste_factor_pct: float = 0.0,
) -> CalculationResult:
    if area_sqft <= 0:
        raise ValueError("area must be a positive number")
    if depth_inches <= 0:
        raise ValueError("depth must be a positive number")
    if tons_per_cubic_yard <= 0:
        raise ValueError("density (tons per cubic yard) must be a positive number")
    if waste_factor_pct < 0:
        raise ValueError("waste factor must be non-negative")

    cu_ft = area_sqft * depth_inches / 12
    cu_yd = cu_ft / 27
    tons = cu_yd * tons_per_cubic_yard
    base, waste, total = _apply_waste(tons, waste_factor_pct)

    parts = [
        f"{_fmt(area_sqft)} sq ft x {_fmt(depth_inches)} in / 12 / 27 = {_fmt(cu_yd)} cu yd",
        f"{_fmt(cu_yd)} cu yd x {_fmt(tons_per_cubic_yard)} tons/cu yd = {_fmt(base)} tons",
    ]
    if waste_factor_pct:
        parts.append(f"+ {waste_factor_pct}% waste ({_fmt(waste)} tons) = {_fmt(total)} tons")

    return CalculationResult(
        quantity=base,
        unit="tons",
        waste_quantity=waste,
        total_quantity=total,
        formula_description=" → ".join(parts),
        inputs={
            "area_sqft": area_sqft,
            "depth_inches": depth_inches,
            "tons_per_cubic_yard": tons_per_cubic_yard,
            "waste_factor_pct": waste_factor_pct,
        },
    )
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd platform && ./run_tests.sh tests/test_calculator_formulas.py::TestAggregateTonnage -q`
Expected: PASS

- [ ] **Step 5: Wire schema + registry + labels**

In `schemas.py`: add `"aggregate_tons"` to the `Literal`, and add field:
```python
    tons_per_cubic_yard: Optional[float] = Field(
        default=None, description="Density of the aggregate in tons per cubic yard (default 1.5)"
    )
```

In `registry.py`: import `aggregate_tonnage`, add compute wrapper + spec:
```python
def _aggregate_tons(p: CalculationRequest) -> CalculationResult:
    assert p.area_sqft is not None
    assert p.depth_inches is not None
    kwargs = {} if p.tons_per_cubic_yard is None else {"tons_per_cubic_yard": p.tons_per_cubic_yard}
    return aggregate_tonnage(
        p.area_sqft, p.depth_inches, waste_factor_pct=p.waste_factor_pct or 0.0, **kwargs
    )

# add to REGISTRY:
    "aggregate_tons": CalcSpec(
        type="aggregate_tons",
        label="gravel tonnage",
        required=("area_sqft", "depth_inches"),
        compute=_aggregate_tons,
        prompt_hint="aggregate_tons: crushed stone / gravel base by weight (needs area_sqft + depth_inches; optional tons_per_cubic_yard)",
    ),
```

In `service.py` `_MISSING_PARAM_LABELS`: no new required fields (area/depth already labeled) — nothing to add.

- [ ] **Step 6: Run registry drift + formula tests**

Run: `cd platform && ./run_tests.sh tests/test_calculator_registry.py tests/test_calculator_formulas.py::TestAggregateTonnage -q`
Expected: PASS (drift guard confirms schema Literal ↔ registry stay in sync)

- [ ] **Step 7: Gates**

Run: `cd platform && ./run_ruff.sh agents/calculator/ && ./run_mypy.sh agents/calculator/`
Expected: clean

### Task 5: Mulch by the bag

**Files:** `formulas.py`, `schemas.py`, `registry.py`, tests.

- [ ] **Step 1: Failing test**

```python
# tests/test_calculator_formulas.py
from agents.calculator.formulas import mulch_bag_count


class TestMulchBagCount:
    def test_two_cuft_bags(self):
        # 100 sq ft x 3 in / 12 = 25 cu ft / 2 cu ft per bag = 12.5 bags
        r = mulch_bag_count(area_sqft=100, depth_inches=3)
        assert r.unit == "bags"
        assert r.quantity == pytest.approx(12.5, abs=0.01)

    def test_three_cuft_bags(self):
        r = mulch_bag_count(area_sqft=100, depth_inches=3, bag_size_cuft=3)
        assert r.quantity == pytest.approx(8.33, abs=0.01)

    def test_rejects_zero_bag_size(self):
        with pytest.raises(ValueError, match="bag"):
            mulch_bag_count(area_sqft=100, depth_inches=3, bag_size_cuft=0)
```

- [ ] **Step 2: Verify fail** — `./run_tests.sh tests/test_calculator_formulas.py::TestMulchBagCount -q` → ImportError

- [ ] **Step 3: Implement**

```python
# agents/calculator/formulas.py
_DEFAULT_BAG_SIZE_CUFT = 2.0


def mulch_bag_count(
    area_sqft: float,
    depth_inches: float,
    bag_size_cuft: float = _DEFAULT_BAG_SIZE_CUFT,
    waste_factor_pct: float = 0.0,
) -> CalculationResult:
    if area_sqft <= 0:
        raise ValueError("area must be a positive number")
    if depth_inches <= 0:
        raise ValueError("depth must be a positive number")
    if bag_size_cuft <= 0:
        raise ValueError("bag size must be a positive number")
    if waste_factor_pct < 0:
        raise ValueError("waste factor must be non-negative")

    cu_ft = area_sqft * depth_inches / 12
    bags = cu_ft / bag_size_cuft
    base, waste, total = _apply_waste(bags, waste_factor_pct)

    parts = [
        f"{_fmt(area_sqft)} sq ft x {_fmt(depth_inches)} in / 12 = {_fmt(cu_ft)} cu ft",
        f"{_fmt(cu_ft)} cu ft / {_fmt(bag_size_cuft)} cu ft per bag = {_fmt(base)} bags",
    ]
    if waste_factor_pct:
        parts.append(f"+ {waste_factor_pct}% waste ({_fmt(waste)} bags) = {_fmt(total)} bags")

    return CalculationResult(
        quantity=base,
        unit="bags",
        waste_quantity=waste,
        total_quantity=total,
        formula_description=" → ".join(parts),
        inputs={
            "area_sqft": area_sqft,
            "depth_inches": depth_inches,
            "bag_size_cuft": bag_size_cuft,
            "waste_factor_pct": waste_factor_pct,
        },
    )
```

- [ ] **Step 4: Verify pass**

- [ ] **Step 5: Wire schema + registry**

`schemas.py`: add `"mulch_bags"` to `Literal`; add field:
```python
    bag_size_cuft: Optional[float] = Field(
        default=None, description="Volume of one mulch/material bag in cubic feet (default 2)"
    )
```
`registry.py`: import `mulch_bag_count`; add:
```python
def _mulch_bags(p: CalculationRequest) -> CalculationResult:
    assert p.area_sqft is not None
    assert p.depth_inches is not None
    kwargs = {} if p.bag_size_cuft is None else {"bag_size_cuft": p.bag_size_cuft}
    return mulch_bag_count(
        p.area_sqft, p.depth_inches, waste_factor_pct=p.waste_factor_pct or 0.0, **kwargs
    )

    "mulch_bags": CalcSpec(
        type="mulch_bags",
        label="mulch bag",
        required=("area_sqft", "depth_inches"),
        compute=_mulch_bags,
        prompt_hint="mulch_bags: bagged mulch/material count (needs area_sqft + depth_inches; optional bag_size_cuft, default 2)",
    ),
```

- [ ] **Step 6: Drift + formula tests pass** — `./run_tests.sh tests/test_calculator_registry.py tests/test_calculator_formulas.py::TestMulchBagCount -q`

- [ ] **Step 7: Gates** — `./run_ruff.sh agents/calculator/ && ./run_mypy.sh agents/calculator/`

### Task 6: Retaining-wall block count

**Files:** `formulas.py`, `schemas.py`, `registry.py`, `service.py` (`_MISSING_PARAM_LABELS`), tests.

- [ ] **Step 1: Failing test**

```python
# tests/test_calculator_formulas.py
from agents.calculator.formulas import retaining_wall_blocks


class TestRetainingWallBlocks:
    def test_basic(self):
        # 20 ft long x 3 ft high; 12 in long x 8 in high blocks
        # cols = 240/12 = 20; rows = 36/8 = 4.5; blocks = 90
        r = retaining_wall_blocks(
            wall_length_ft=20, wall_height_ft=3,
            block_length_inches=12, block_height_inches=8,
        )
        assert r.unit == "blocks"
        assert r.quantity == pytest.approx(90.0, abs=0.01)

    def test_with_waste(self):
        r = retaining_wall_blocks(
            wall_length_ft=20, wall_height_ft=3,
            block_length_inches=12, block_height_inches=8, waste_factor_pct=10,
        )
        assert r.total_quantity == pytest.approx(99.0, abs=0.01)

    def test_rejects_zero_block_length(self):
        with pytest.raises(ValueError, match="block"):
            retaining_wall_blocks(
                wall_length_ft=20, wall_height_ft=3,
                block_length_inches=0, block_height_inches=8,
            )
```

- [ ] **Step 2: Verify fail**

- [ ] **Step 3: Implement**

```python
# agents/calculator/formulas.py
def retaining_wall_blocks(
    wall_length_ft: float,
    wall_height_ft: float,
    block_length_inches: float,
    block_height_inches: float,
    waste_factor_pct: float = 0.0,
) -> CalculationResult:
    if wall_length_ft <= 0:
        raise ValueError("wall length must be a positive number")
    if wall_height_ft <= 0:
        raise ValueError("wall height must be a positive number")
    if block_length_inches <= 0:
        raise ValueError("block length must be a positive number")
    if block_height_inches <= 0:
        raise ValueError("block height must be a positive number")
    if waste_factor_pct < 0:
        raise ValueError("waste factor must be non-negative")

    cols = wall_length_ft * 12 / block_length_inches
    rows = wall_height_ft * 12 / block_height_inches
    blocks = cols * rows
    base, waste, total = _apply_waste(blocks, waste_factor_pct)

    parts = [
        f"Courses: {_fmt(wall_height_ft)} ft x 12 / {_fmt(block_height_inches)} in = {_fmt(rows)} rows",
        f"Per course: {_fmt(wall_length_ft)} ft x 12 / {_fmt(block_length_inches)} in = {_fmt(cols)} blocks",
        f"{_fmt(rows)} x {_fmt(cols)} = {_fmt(base)} blocks",
    ]
    if waste_factor_pct:
        parts.append(f"+ {waste_factor_pct}% waste ({_fmt(waste)}) = {_fmt(total)} blocks")

    return CalculationResult(
        quantity=base,
        unit="blocks",
        waste_quantity=waste,
        total_quantity=total,
        formula_description=" → ".join(parts),
        inputs={
            "wall_length_ft": wall_length_ft,
            "wall_height_ft": wall_height_ft,
            "block_length_inches": block_length_inches,
            "block_height_inches": block_height_inches,
            "waste_factor_pct": waste_factor_pct,
        },
    )
```

- [ ] **Step 4: Verify pass**

- [ ] **Step 5: Wire schema + registry + labels**

`schemas.py`: add `"retaining_wall_blocks"` to `Literal`; add fields:
```python
    wall_length_ft: Optional[float] = Field(default=None, description="Retaining wall length in feet")
    wall_height_ft: Optional[float] = Field(default=None, description="Retaining wall height in feet")
    block_length_inches: Optional[float] = Field(default=None, description="Block length in inches")
    block_height_inches: Optional[float] = Field(default=None, description="Block height in inches")
```
`registry.py`: import `retaining_wall_blocks`; add:
```python
def _wall_blocks(p: CalculationRequest) -> CalculationResult:
    assert p.wall_length_ft is not None
    assert p.wall_height_ft is not None
    assert p.block_length_inches is not None
    assert p.block_height_inches is not None
    return retaining_wall_blocks(
        p.wall_length_ft, p.wall_height_ft,
        p.block_length_inches, p.block_height_inches,
        waste_factor_pct=p.waste_factor_pct or 0.0,
    )

    "retaining_wall_blocks": CalcSpec(
        type="retaining_wall_blocks",
        label="retaining wall",
        required=("wall_length_ft", "wall_height_ft", "block_length_inches", "block_height_inches"),
        compute=_wall_blocks,
        prompt_hint="retaining_wall_blocks: wall block count (needs wall_length_ft + wall_height_ft + block_length_inches + block_height_inches)",
    ),
```
`service.py` `_MISSING_PARAM_LABELS`: add
```python
    "wall_length_ft": "the wall length (in feet)",
    "wall_height_ft": "the wall height (in feet)",
    "block_length_inches": "the block length (in inches)",
    "block_height_inches": "the block height (in inches)",
```

- [ ] **Step 6: Drift + formula tests pass**

- [ ] **Step 7: Gates** — clean

### Task 7: Step count (rise over run)

**Files:** `formulas.py`, `schemas.py`, `registry.py`, `service.py` (`_MISSING_PARAM_LABELS`), `text_helpers.py`, tests.

- [ ] **Step 1: Failing test**

```python
# tests/test_calculator_formulas.py
from agents.calculator.formulas import step_count


class TestStepCount:
    def test_basic(self):
        # 42 in total rise / 7 in target riser = 6 steps
        r = step_count(total_rise_inches=42)
        assert r.unit == "steps"
        assert r.quantity == pytest.approx(6.0, abs=0.01)

    def test_custom_riser(self):
        r = step_count(total_rise_inches=48, target_riser_inches=6)
        assert r.quantity == pytest.approx(8.0, abs=0.01)

    def test_rejects_zero_rise(self):
        with pytest.raises(ValueError, match="rise"):
            step_count(total_rise_inches=0)
```

- [ ] **Step 2: Verify fail**

- [ ] **Step 3: Implement** (no waste concept — pass through 0)

```python
# agents/calculator/formulas.py
_DEFAULT_RISER_INCHES = 7.0


def step_count(
    total_rise_inches: float,
    target_riser_inches: float = _DEFAULT_RISER_INCHES,
) -> CalculationResult:
    if total_rise_inches <= 0:
        raise ValueError("total rise must be a positive number")
    if target_riser_inches <= 0:
        raise ValueError("target riser height must be a positive number")

    steps = total_rise_inches / target_riser_inches
    base = round(steps, 2)

    return CalculationResult(
        quantity=base,
        unit="steps",
        waste_quantity=0.0,
        total_quantity=base,
        formula_description=(
            f"{_fmt(total_rise_inches)} in rise / {_fmt(target_riser_inches)} in per riser "
            f"= {_fmt(base)} steps"
        ),
        inputs={
            "total_rise_inches": total_rise_inches,
            "target_riser_inches": target_riser_inches,
        },
    )
```

- [ ] **Step 4: Verify pass**

- [ ] **Step 5: Wire schema + registry + labels + detection**

`schemas.py`: add `"step_count"` to `Literal`; add fields:
```python
    total_rise_inches: Optional[float] = Field(default=None, description="Total vertical rise in inches")
    target_riser_inches: Optional[float] = Field(default=None, description="Target step riser height in inches (default 7)")
```
`registry.py`: import `step_count`; add:
```python
def _steps(p: CalculationRequest) -> CalculationResult:
    assert p.total_rise_inches is not None
    kwargs = {} if p.target_riser_inches is None else {"target_riser_inches": p.target_riser_inches}
    return step_count(p.total_rise_inches, **kwargs)

    "step_count": CalcSpec(
        type="step_count",
        label="step",
        required=("total_rise_inches",),
        compute=_steps,
        prompt_hint="step_count: number of steps for a slope (needs total_rise_inches; optional target_riser_inches, default 7)",
    ),
```
`service.py` `_MISSING_PARAM_LABELS`: add
```python
    "total_rise_inches": "the total rise (in inches)",
    "target_riser_inches": "the target riser height (in inches)",
```
`text_helpers.py`: add `steps?` to the `_MEASUREMENT_UNITS` alternation so the orchestrator pre-classifier recognizes "how many steps…".

- [ ] **Step 6: Drift + formula tests pass**

- [ ] **Step 7: Gates** — clean

### Task 8: Agent-level end-to-end test for a new type

**Files:** `tests/test_calculator_agent.py`

- [ ] **Step 1: Add a monkeypatched end-to-end test proving a new type flows through `process()`**

```python
# tests/test_calculator_agent.py
class TestAggregateTons:
    def test_gravel_tonnage(self, monkeypatch: Any):
        async def fake_extract(self: Any, message: str, context=None) -> CalculationRequest:
            return CalculationRequest(
                calculation_type="aggregate_tons", area_sqft=100, depth_inches=4,
            )

        agent = _make_agent(monkeypatch, fake_extract)
        result = _run(agent.process("how many tons of gravel for 100 sq ft 4 inches deep?"))

        assert result["success"] is True
        calc = result["result"]["calculation"]
        assert calc["unit"] == "tons"
        assert calc["quantity"] == pytest.approx(1.85, abs=0.01)
```

- [ ] **Step 2: Run** — `./run_tests.sh tests/test_calculator_agent.py::TestAggregateTons -q` → PASS

### Task 9: Update the phrasing-reference doc (CLAUDE.md-mandated)

**Files:** `documentation/development/maple-phrasing-reference.md`

- [ ] **Step 1:** Add the four new calculation types (gravel tons, mulch bags, retaining-wall blocks, step count) to the Estimates/Calculator section with ✅ status tags, bump §9.3 snapshot counts, and update the "Last updated" date to 2026-06-15. (No test — doc change.)

### Task 10: Commit Phase 2

- [ ] **Step 1: Stage + request approval, then commit**

```bash
git add agents/calculator/ tests/test_calculator_formulas.py tests/test_calculator_agent.py \
        documentation/development/maple-phrasing-reference.md
git commit -m "feat: add gravel-tonnage, mulch-bag, wall-block, and step-count calculations"
```

(Commit needs explicit user approval per CLAUDE.md.)

---

## Phase 3 — Deferred (documented, not implemented here)

- **Plant grid-spacing** (square / triangular): introduces a string `pattern` field; formula `area_sqft / spacing_ft²` (square) and `/ (spacing_ft² × 0.866)` (triangular). Add `plants?` to `_MEASUREMENT_UNITS`.
- **Grading pitch**: `run_ft × 12 × slope_pct/100` total drop; no-waste shape; default 2% / quarter-inch-per-foot.
- **Hydraulics** (irrigation TDH/GPM, surface runoff, drainage pipe sizing): out of scope — need reviewed engineering formulas and carry install/liability risk. Recommend an "explain the formula + required inputs" response rather than an auto-quoted number.

---

## Self-Review

- **Spec coverage:** Registry refactor (Tasks 1-3) covers the "scale cheaply" goal; Tasks 4-7 add the four simple primitives the recommendation named; Task 8 proves end-to-end flow; Task 9 satisfies the CLAUDE.md phrasing-doc rule; Phase 3 records the deferred items so nothing is silently dropped.
- **Drift guard:** `test_registry_matches_schema_literal` makes any Literal/registry mismatch a test failure — the one sync point the registry can't auto-derive.
- **Type consistency:** compute-wrapper names (`_aggregate_tons`, `_mulch_bags`, `_wall_blocks`, `_steps`) and formula names (`aggregate_tonnage`, `mulch_bag_count`, `retaining_wall_blocks`, `step_count`) are used identically across schema/registry/tests. New schema fields (`tons_per_cubic_yard`, `bag_size_cuft`, `wall_*`, `block_*`, `total_rise_inches`, `target_riser_inches`) are referenced consistently.
- **Behavior preservation:** Phase 1 edits no existing test; the existing suite is the lock. `_PERSISTED_PARAM_FIELDS` derivation reproduces the original 11-field tuple exactly (schema minus `{calculation_type, material_name, from_unit, to_unit}`).
