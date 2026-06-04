# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a field service management web app with two main components:
- **Platform** (`platform/`): FastAPI backend for managing estimates, materials, equipment, labour, and AI-powered estimate generation
- **Portal** (`portal/`): React frontend for user interaction

## Architecture

### Backend (Platform)

**Tech Stack**: FastAPI + MongoDB (Beanie ODM) + LangChain + OpenAI

**Core Components Framework**:
- `main.py` / `database.py` / `config.py`: Standard FastAPI app initialization, MongoDB configuration, and settings management.
- `models/`: Beanie document models. Always check this directory for the latest schema definitions and relationships.
- `routers/`: API endpoints categorized by resource.
- `agents/` & `prompts/`: LangChain-based AI agents and their system prompts.
- `tests/`: pytest test suite.

**Estimate Workflow**:
1. User provides job description
2. Estimate agent (LangChain ChatOpenAI; models configured via `config.py` — `architect_model` / `researcher_model` / `worker_model`) analyzes description
3. Agent recommends materials, equipment, and labour with quantities/costs
4. Estimate created with status (draft/review/approved/rejected/on_hold)
5. Estimate stored with MaterialItem, EquipmentItem, LabourItem lists

**Data Model & Relationships**:
Always inspect the `models/` directory for the most up-to-date document structures. Important patterns include:
- Estimates embed sub-items which reference base collections.
- Cross-collection links utilize `PydanticObjectId`.
- The `Company` model acts as a tenant owning both users and resources.

### Frontend (Portal)

**Tech Stack**: React 18 + React Router + Vite + Tailwind CSS 4

**Structure**:
- `src/App.jsx`: Main router with routes for Login, Welcome, Error
- `src/Login.jsx`: Authentication view
- Styling via Tailwind CSS with PostCSS processing

**Deployment**: Firebase Hosting (configured via firebase.json and .firebaserc)

## Common Commands

### Platform (Backend)

```bash
# Setup
cd platform
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run tests (RECOMMENDED - automatically uses venv)
./run_tests.sh              # Linux/Mac

# Or manually activate venv first, then run pytest
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pytest

# Run specific test file
./run_tests.sh tests/test_agents_api.py

# Run tests with coverage
./run_tests.sh --cov --cov-report=html

# Run tests with verbose output
./run_tests.sh -v -s

# Type-check (RECOMMENDED — keeps the project at zero mypy errors)
./run_mypy.sh                          # full project (default)
./run_mypy.sh agents/material          # scope to a subtree (faster)
./run_mypy.sh routers/materials.py     # one file

# Lint (RECOMMENDED — keeps the project at zero ruff errors)
./run_ruff.sh                          # full project (default)
./run_ruff.sh agents/material          # scope to a subtree (faster)
./run_ruff.sh routers/materials.py     # one file
./run_ruff.sh --fix                    # apply safe auto-fixes, then report
```

### Portal (Frontend)

```bash
# Setup
cd portal
npm install

# Run development server
npm run dev

# Run tests (MANDATORY after any changes)
npm test

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Deploy to Firebase
firebase deploy
```

## Environment Configuration

### Platform `.env` (required)
Refer to `platform/config.py` (specifically the `Settings` class) to see the current required `.env` variables (e.g., MongoDB credentials, AI API keys).

## Testing Strategy

### Run Tests Related to Your Changes
**After making code changes, run the tests that are directly related to the files you modified:**

```bash
# Backend: run specific test file(s) related to your changes
cd platform
./run_tests.sh tests/test_<relevant_module>.py

# Frontend: run specific test file(s) related to your changes
cd portal
npm test -- <relevant_test_file>
```

**Do NOT auto-run the full test suite.** The user will manually trigger the complete test suite when ready. Only run the tests that directly cover the code you changed or added.

### mypy is a Gate, Not a Suggestion

The `platform/` project sits at **zero mypy errors** as of 2026-05-22 (#3 in `documentation/development/code-review-followups.md`). Keep it there — letting errors accumulate re-creates the 200+-error backlog that took an entire session to clear.

**Rule**: after any `.py` change in `platform/`, run `./run_mypy.sh` *before* considering the work complete. Scope to the touched subtree (`./run_mypy.sh agents/material`) for a fast loop, then re-run the full project (`./run_mypy.sh`) before commit-prep to catch cross-file regressions.

If new errors appear:
- Fix them in the same change. Don't ship a Python edit that adds a mypy error.
- The playbook in #3's body covers every recurring pattern: `assert <x> is not None` for Beanie `.id`, `Dict[str, Any]` annotations on inferred-too-narrow locals, `Optional[X]` widening for honest signatures, `# type: ignore[<code>]` only when a third-party stub is genuinely wrong (always include a one-line justification comment).
- If a batch grows past ~10 errors, treat it like a sub-task — fix and commit separately rather than bundling.

`./run_mypy.sh` uses the pinned config in `platform/mypy.ini`. Don't pass mypy flags ad-hoc — update `mypy.ini` instead, so every session uses the same baseline.

### ruff is a Gate, Not a Suggestion

`platform/` adopted **ruff** as a hard lint gate on 2026-06-03 (same model as mypy). The pinned config lives in `platform/ruff.toml`; run it via `./run_ruff.sh`.

**Ruleset** (deliberately conservative — signal, not style noise):
- `E, F` — pyflakes + pycodestyle (dead imports/vars, real defects)
- `I` — import sorting (replaces isort)
- `B` — flake8-bugbear (real bug patterns, e.g. missing exception chaining)
- `C4` — flake8-comprehensions; `SIM` — flake8-simplify
- **`E501` (line-too-long) is OFF** by choice — pure style, not a defect.
- **`UP` (pyupgrade) is intentionally NOT enabled.** Its annotation rewrites (`Dict`→`dict`, `Optional[X]`→`X | None`) collide with the mypy.ini playbook above and would be one giant diff. Don't add `UP` without a deliberate decision + a coordinated mypy-playbook update.

**Rule**: after any `.py` change in `platform/`, run `./run_ruff.sh` *before* considering the work complete. Scope to the touched subtree (`./run_ruff.sh agents/material`) for a fast loop, then re-run the full project before commit-prep. New errors are fixed in the same change — don't let them accumulate.

Recurring playbook:
- `./run_ruff.sh --fix` clears the **safe** auto-fixable ones (unused imports, import order, simple simplifications). Never pass `--unsafe-fixes` without reviewing each change — those can alter behavior.
- **B904** (raise-without-`from` inside `except`): add `raise ... from err` (preserve cause) or `raise ... from None` (suppress) — matches the "don't leak/garble tracebacks" rule.
- **F841** unused vars: usually safe to delete; in tests, confirm the assignment isn't documenting an intentional call before removing.
- **E402** import-not-at-top: reorder when possible; for genuine circular-import / ordering needs, keep the import where it is and add `# noqa: E402` with a one-line reason.
- **Re-export hubs**: a module that imports a symbol only to re-expose it (e.g. `routers/estimates.py`, `routers/agents.py`, `agents/estimate/service.py`) must list those names in a module-level `__all__`, or F401 will delete the import and break downstream importers. `__all__` marks them as intentional re-exports. **Never blanket-`--fix` F401 without checking for re-export hubs first.**
- `# noqa: <CODE>` only when ruff is genuinely wrong — always with a one-line justification.

`./run_ruff.sh` uses the pinned config in `platform/ruff.toml`. Don't pass rule flags ad-hoc — update `ruff.toml` instead, so every session uses the same baseline.

> **Baseline status (2026-06-03):** the safe auto-fixable backlog (import sorting + trivial simplifications, ~287 fixes) has been applied. A manual backlog of ~474 remains (tracked as **#323 in `documentation/development/code-review-followups.md`**): the bulk is **F401** (~284, report-only by config — triage each per the playbook above), plus E402 (~56), F841 (~52), B904 (~32, the only correctness slice — do first), E741 (~23), and a few SIM/C4. Work it down (or relax rules consciously) before the project is fully green. Until then, scope `./run_ruff.sh` to the files you touched so you gate *your* change without tripping over the legacy backlog.

### Backend Testing
- **Environment**: All tests MUST be run within the activated Python virtual environment (`source .venv/bin/activate`).
- Backend tests use FastAPI TestClient
- Fixtures in `tests/conftest.py` provide shared test setup (client, test_company_id)
- Tests create and cleanup test data (companies, materials, etc.)
- Agent tests verify LangChain integration and response structure

### Frontend Testing
- Tests run via `npm test` using the configured test runner
- Tests should verify component behavior, user interactions, and API integration
- Ensure all tests pass before considering work complete

## Key Implementation Notes

### AI Agent Pattern
All Maple agents use LangChain's ChatOpenAI with:
- System prompts from `prompts/` and per-agent service modules
- **Models** configured in `config.py`: `architect_model` (gpt-5.5, complex
  decomposition), `researcher_model` (gpt-5.4, web search / pricing),
  `worker_model` (gpt-5.4-mini, CRUD / extraction / Maple-help answering).
  All overridable via the corresponding `OPENAI_MODEL_*` env vars.
- **Temperature 0** everywhere — every agent service constructs its
  `ChatOpenAI` with `temperature=0` for deterministic-as-possible output.
  Don't introduce non-zero temperatures without a documented reason; higher
  values increase cross-lingual token bleed and other sampling drift.
- Async methods (`ainvoke`) for non-blocking API calls
- Singleton pattern in router for agent instance reuse

### Maple (Orchestrator) — CRUD assistant policies

**Maple** is the user-facing brand for the Orchestrator agent at `agents/orchestrator/service.py`. It's a hybrid rule-based + LLM intent classifier that routes user messages to specialized agents (Property, Contact, Material, Labour). The four supported resources are:

| User-facing label | Code domain | What it represents |
|---|---|---|
| Property | `property` | Job sites / addresses |
| Contact | `contact` | **Individuals** at a property (homeowner, manager, etc.) |
| Material | `material` | Catalog of physical products with sizes/prices |
| **People** | `labour` | Catalog of **role definitions** (Landscaper, Foreman, Operator). NOT individuals — that's Contact. |

**Equipment is explicitly blocked** — see `is_equipment_request()` in `agents/text_utils.py`. Any equipment phrasing returns `EQUIPMENT_REFUSAL_MESSAGE` rather than silently falling through to "unknown".

**Bulk delete is forbidden via Maple** (Maple-only policy; HTTP routers may still expose bulk-delete for UI workflows). The `is_bulk_delete_request()` guard runs in both the rule path and the `process()` path of the orchestrator AND defensively at the top of each domain agent's `process()` (belt-and-braces). Phrasings like "delete all contacts" / "wipe my materials" return `BULK_DELETE_REFUSAL_MESSAGE`.

**Shared text-utility helpers** in `agents/text_utils.py`:
- `is_bulk_delete_request(text)` — quantifier + delete verb detector
- `is_equipment_request(text)` — equipment domain detector
- `is_count_query(text)` — "how many" / "count" / "total number" / "number of"
- `format_count_response(count, singular, plural)` — friendly count phrasing with N=0 / N=1 / N=many grammar
- `BULK_DELETE_REFUSAL_MESSAGE`, `EQUIPMENT_REFUSAL_MESSAGE` — canonical refusal copy
- `humanize_field_name(field)` — snake_case → user-friendly label

When extending Maple's CRUD surface to a new field or phrasing pattern, **don't write inline regex** for these — use the helpers so the count-query / bulk-delete / equipment policies stay consistent across all four agents.

**Friendly first-person tone** — all CRUD response strings in Property/Contact/Material/Labour agents follow this template:
- Create: `"I've created the {resource} for you. Here are the details:\n{details}"`
- Update: `"I've updated the {resource} for you. Here are the updated details:\n{details}"`
- Delete: `"I've deleted the {resource} '{name}' for you."`
- Get:    `"Here are the details for that {resource}:\n{details}"`
- List:   `"Here are your {plurals}: {labels}"`
- Empty:  `"I couldn't find any matching {plurals}."`
- Count:  `format_count_response(N, singular, plural)`

**Multi-turn field-then-value flow** — every CRUD agent has a `_match_bare_field_name()` helper + `awaiting_value_for` pending-intent state. When a user replies to "What fields should I update?" with a bare field name (e.g. "phone"), the agent stores the selection and asks for the value, instead of looping the same question. See [agents/property/service.py](platform/agents/property/service.py) for the canonical implementation.

**Coverage matrix** — `tests/test_maple_crud_coverage.py` exercises 117 phrasings (10 categories × resources + equipment refusal). Run with `./run_tests.sh tests/test_maple_crud_coverage.py` for Tier 1 (rules only, default) or `./run_tests.sh tests/test_maple_crud_coverage.py -m ""` for both tiers (Tier 2 hits the live LLM, requires `OPENAI_API_KEY`, ~3 min, ~$0.05). The auto-generated dual-column gap report is written to `tests/reports/maple_crud_gap_report.md`.

**Phrasing reference (human-curated)** — [`documentation/development/maple-phrasing-reference.md`](documentation/development/maple-phrasing-reference.md) is the canonical catalog of supported and gap phrasings across all 5 Maple resources (Estimates, Properties, Contacts, Materials, People/Labour). It is the single source of truth that users extend with new use cases. **Whenever you add, close, or reclassify a Maple phrasing — whether via a new classifier rule, a handler change, or a refusal policy — update this doc in the same change.** Flip ✅ / 🤖 / ⚠️ / 🛑 status tags, update the snapshot counts in §9.3, and bump the "Last updated" date at the top. The auto-generated `tests/reports/maple_crud_gap_report.md` is the live runtime truth; the reference doc is the human-readable truth that survives test runs.

### Database Initialization
- MongoDB connection established in `lifespan` context manager
- Beanie initialization happens before app starts accepting requests
- All models must be registered in `database.py:init_db()`

### API Router Organization
All routers follow pattern:
- Import from `routers` in main.py
- Each router has a dedicated file.
- Prefix and tags defined per router
- CRUD operations follow REST conventions

### CORS Configuration
Currently allows all origins (`allow_origins=["*"]`) - suitable for development but should be restricted for production deployment.

## AI Assistant Guidelines & Best Practices

When writing code or proposing changes in this repository, you **must** adhere strictly to the following rules to ensure production stability, security, and high code quality:

### 1. Robust Testing (CRITICAL)
- **Always update tests**: Any new features, logic changes, or bug fixes MUST include corresponding updates or additions to the test files.
- **Adjust existing tests**: When adding a new feature or modifying existing behavior, review and update all affected tests to reflect the changes. Tests must stay in sync with the current implementation—stale or outdated assertions are not acceptable.
- **Run only related tests**: After making changes, run the specific test file(s) that cover the code you modified. Do NOT auto-run the full test suite — the user will trigger full test runs manually.
  ```bash
  # Backend: run specific tests related to your changes
  cd platform && ./run_tests.sh tests/test_<relevant_module>.py

  # Frontend: run specific tests related to your changes
  cd portal && npm test -- <relevant_test_file>
  ```
- **Use the Virtual Environment**: Always ensure backend tests are run within the Python virtual environment (`source .venv/bin/activate`).
- **Full suite is manual**: Do not run the complete backend + frontend test suites automatically. The user will decide when to run the full suite.
- **mypy is mandatory for backend changes**: After any `.py` edit under `platform/`, run `./run_mypy.sh` (scoped to the touched subtree for speed, full project before commit-prep). Project sits at zero mypy errors — fix new errors in the same change, don't let them accumulate. See "mypy is a Gate, Not a Suggestion" above for the recurring playbook.
- **ruff is mandatory for backend changes**: After any `.py` edit under `platform/`, also run `./run_ruff.sh` (scope to the touched files while the legacy backlog is worked down). Fix new lint errors in the same change. See "ruff is a Gate, Not a Suggestion" above — note the re-export-hub caveat before ever running `--fix` broadly.

### 2. Code Quality & Maintainability
- **Minimize redundant code**: Follow DRY (Don't Repeat Yourself) principles. Refactor reusable logic into helper functions, hooks, or shared components.
- **Pattern consistency**: Match the established architectural patterns (e.g., Beanie ODM for MongoDB, FastAPI dependency injection, standard React hook patterns).
- **Function design**: Keep functions small, testable, and heavily focused on a single responsibility.
- **Proper error handling**: Gracefully handle missing data, external API failures, or unexpected inputs without crashing. Use proper HTTP status codes and don't leak stack traces.

### 3. Security & Operations
- **Validate Everything**: Ensure Pydantic is utilized to validate exactly what the application requires on the backend. Handle undefined/null edge cases safely on the frontend.
- **Careful Self-Review**: Validate your own code before outputting it: verify correct `async`/`await` usage, verify dictionary/array bounds, and ensure no obvious memory leaks or n+1 queries.

## Git Workflow

### Commit Message Format

```
<type>: <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

### Pull Request Process

1. Use `git diff [base-branch]...HEAD` to review all changes — not just the last commit
2. Write a comprehensive PR summary covering all changes
3. Include a short test plan (what was tested, which test files)
4. Push with `git push -u origin <branch>` for new branches

## Development Workflow

Before writing any new feature:

1. **Plan first** — outline phases, dependencies, and risks before touching code
2. **TDD** — write the failing test first, then the implementation (see TDD Policy below)
3. **Implement** — write minimal code to make tests pass
4. **Self-review** — run related tests, check for N+1 queries, mutable state, and unhandled exceptions before handing off to Antigravity for full code review

### TDD Policy

**TDD is mandatory for all functional code changes** — new features, bug fixes, refactors, or any change to behaviour in `.py`, `.jsx`, or `.tsx` files. Write the failing test first, then the implementation. This is the default whenever the user asks for a code change; it is not opt-in.

**TDD does not apply to:** documentation (`.md`, docstrings), configuration files (`.env.example`, `pyproject.toml`, `firebase.json`, etc.), LangChain prompt text edits, styling-only changes (Tailwind classes, CSS), dead code removal, dependency version bumps, and file renames without behaviour change. For these, update relevant tests only if the change breaks them — do not invent new tests.

**The `tdd-guide` agent remains available** as a specialist sub-agent for complex TDD sessions. Invoke it directly via the Task tool when deep methodology guidance is wanted (e.g., designing the test scaffold for a new agent tool or router resource).
