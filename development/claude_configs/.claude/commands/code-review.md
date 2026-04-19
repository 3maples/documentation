---
description: Comprehensive code review with security, quality, and language-specific checks. Uses a dispatcher pattern — applies backend (Python) or frontend (React) rules only for file types that actually changed.
argument-hint: [optional-file-path]
allowed-tools: Bash, Read, Grep, Glob
---

# Code Review

Comprehensive security and quality review of uncommitted changes. This command uses a **dispatcher pattern**: it inspects which files changed and applies only the relevant checks. Cross-cutting checks always run; backend and frontend sections only run when their file types are in scope.

If `$ARGUMENTS` is provided, review only that file (path relative to repo root). Otherwise, review all uncommitted + untracked changes.

## Step 1 — Discover Changes

1. If `$ARGUMENTS` is set, use that single file path. Otherwise:
   - Tracked changes: `git diff --name-only HEAD`
   - Untracked files: `git ls-files --others --exclude-standard`
   - Combine and deduplicate.
2. Bucket files into:
   - **Backend (Python)**: `.py`
   - **Frontend (React)**: `.jsx`, `.tsx`, `.js`, `.css`
   - **Other**: config, documentation, tests, infra — reviewed only under Step 2 (cross-cutting)
3. Record which buckets have changes. This decides whether Step 3 and/or Step 4 run.

## Step 2 — Cross-Cutting Checks (always run)

Applied to every changed file regardless of language.

**CRITICAL**
- Hardcoded credentials, API keys, tokens — grep for patterns like `sk-`, `AWS_`, `password =`, `token =`, `api_key =`
- Missing input validation on any code path accepting external data
- CORS wildcard (`allow_origins=["*"]`) left in place — fine for dev, but flag before production merges
- Insecure dependencies pinned to known-vulnerable versions (suggest `pip-audit` / `npm audit` for deeper scan)

**HIGH**
- Functions longer than 50 lines
- Files longer than 800 lines
- Nesting depth greater than 4 levels
- Missing error handling around external calls (network, DB, third-party APIs)
- Missing tests for new public functions or API routes (per `CLAUDE.md` mandatory-testing rule)

**MEDIUM**
- TODO / FIXME comments added in this change
- `console.log` or `print` statements left in production code
- Mutation patterns where an immutable return would be clearer
- Missing docstrings on public APIs

## Step 3 — Backend (Python) Checks

**Run only if any `.py` files changed.**

If the tooling is available, run these first:

```bash
cd platform
source .venv/bin/activate
ruff check .                      # if ruff installed
mypy . --ignore-missing-imports   # if mypy installed
bandit -r . -x tests/             # if bandit installed
```

Surface their output in the final report under the appropriate severity.

Then check manually for:

**CRITICAL**
- SQL / NoSQL / command injection — string concatenation into DB queries or `subprocess.run`
- User input concatenated directly into LangChain prompts (prompt injection risk)
- Bare `except:` or `except Exception: pass` hiding errors

**HIGH**
- Missing type hints on public functions
- Mutable default arguments (`def f(x=[])`, `def f(x={})`)
- Blocking calls inside `async def` route handlers (`requests.get`, `time.sleep`, non-async DB drivers)
- Beanie `fetch_link()` called inside a loop (N+1 query pattern)
- Missing Pydantic validation on router inputs (query params, bodies, path params)
- Beanie model added or changed without corresponding `database.py:init_db()` registration update

**MEDIUM**
- `print()` calls where proper logging should be used
- Magic numbers without named constants
- Missing docstrings on public functions

**Note on coverage.** If coverage appears low, report it as a gap — but do **not** run `./run_tests.sh --cov` from this command. Coverage tooling is the responsibility of `/coverage`.

## Step 4 — Frontend (React) Checks

**Run only if any `.jsx`, `.tsx`, `.js`, or `.css` files changed.**

**CRITICAL**
- `dangerouslySetInnerHTML` without sanitisation (XSS risk)
- User input rendered without escaping
- API keys, secrets, or credentials in frontend code (should always be server-side)

**HIGH**
- React hooks with incorrect dependency arrays (stale closures, missing deps, unnecessary deps)
- Missing accessibility attributes — buttons without accessible text, images without `alt`, form inputs without labels, missing ARIA roles
- Unused components or orphaned imports
- `console.log` left in production code

**MEDIUM**
- Tailwind class typos or non-core utility classes (per `CLAUDE.md`, Portal ships only base Tailwind utilities)
- Large components that should be split for readability or reuse
- Inline styles where a Tailwind utility exists

## Step 5 — Severity-Tiered Report

Generate a report with this format for each issue:

```
[SEVERITY] <file>:<line> — <short title>
  Issue: <what's wrong and why it matters>
  Fix:   <suggested remediation>
```

Sort by severity descending (CRITICAL → LOW). Include a count summary at the top of the report:

```
CRITICAL: N
HIGH:     N
MEDIUM:   N
LOW:      N
```

## Step 6 — Recommendation

| Status       | Condition                  | Meaning                                                  |
|--------------|----------------------------|----------------------------------------------------------|
| Approve      | Zero CRITICAL, zero HIGH   | Safe to commit                                           |
| Warning      | MEDIUM issues only         | Safe to commit; address soon                             |
| Block (rec.) | Any CRITICAL or any HIGH   | **Recommend blocking commit until fixed**                |

**Note:** Claude cannot actually block a commit. "Block (rec.)" is advisory — you decide whether to proceed.

## Integration with Other Commands

- Run `/code-review` then `/commit-prep` as the pre-commit pair
- Coverage gaps flagged here: run `/coverage <file>` for specific uncovered lines
- Deeper security audit: use the built-in `/security-review` (ships with Claude Code)
- LangChain prompt changes specifically: use `/agent-prompt-review`
- Build or type errors surfaced: use `/build-fix`
