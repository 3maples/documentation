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
2. Estimate agent (GPT-4o-mini via LangChain) analyzes description
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
The EstimateAgent uses LangChain's ChatOpenAI with:
- System prompts from `prompts/` module
- Temperature 0.7 for balanced creativity/consistency
- Async methods (`ainvoke`) for non-blocking API calls
- Singleton pattern in router for agent instance reuse

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
