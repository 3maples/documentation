---
description: Analyze test coverage, identify gaps, and suggest where tests are needed. Accepts an optional file path to scope analysis to one module.
argument-hint: [optional-file-path]
allowed-tools: Bash, Read, Grep, Glob
---

# Coverage

Analyze test coverage, identify gaps, and report where tests are missing.

If `$ARGUMENTS` is provided, scope the report to that single file (path relative to repo root). Otherwise, analyze full project coverage.

## Step 1: Run Coverage

If `$ARGUMENTS` is set and points to a backend file:

```bash
cd platform && ./run_tests.sh --cov=<module> --cov-report=term-missing
```

If `$ARGUMENTS` is set and points to a frontend file:

```bash
cd portal && npm test -- --coverage --collectCoverageFrom=<file>
```

Otherwise, run full-project coverage:

```bash
# Backend
cd platform && ./run_tests.sh --cov --cov-report=term-missing

# Frontend
cd portal && npm test -- --coverage
```

## Step 2: Analyze Coverage Report

1. List files **below 80% coverage**, sorted worst-first
2. For each under-covered file, identify:
   - Untested functions or methods
   - Missing branch coverage (if/else, error paths)
   - Dead code that inflates the denominator (flag for `/dead-code` cleanup)

## Step 3: Report Gaps

For each under-covered file, produce a list of specific missing cases:

1. **Happy path** — Core functionality with valid inputs
2. **Error handling** — Invalid inputs, missing data, network failures
3. **Edge cases** — Empty arrays, null/None, boundary values (0, -1)
4. **Branch coverage** — Each if/else, early return, exception handler

Example output:

```
platform/routers/estimates.py  45% coverage
  Missing:
  - Error path: 404 when company not found (lines 34-38)
  - Edge case: empty material list (line 52)
  - Branch: status="on_hold" transition (lines 88-91)
```

## Step 4: Hand Off

This command **reports** gaps; it does not write tests. To address the gaps, request the code changes you need — per `CLAUDE.md`, TDD is the global default, so Claude will write failing tests first, then the minimum implementation.

### Test Writing Rules (for reference — applied by the TDD flow)

- Place backend tests in `platform/tests/test_<module>.py`
- Use existing fixtures from `tests/conftest.py` (`client`, `test_company_id`)
- Mock external dependencies (OpenAI, Firebase) — don't hit real APIs
- Each test should be independent — no shared mutable state
- Name tests descriptively: `test_create_estimate_with_missing_company_returns_404`

## Step 5: Summary

Show a coverage snapshot:

```
Coverage Gap Report
──────────────────────────────
File                               Coverage  Missing
platform/routers/estimates.py       45%       12 lines
platform/agents/estimate.py         32%       28 lines
──────────────────────────────
Overall:                            67%
Target:                             80%
```

## Focus Areas

- FastAPI route handlers (request → response flow, status codes)
- LangChain agent error paths (OpenAI down, invalid response)
- Pydantic model validators and edge cases
- Utility functions used across routers
