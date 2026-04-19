---
description: Pre-commit gauntlet — identifies changed files, runs related backend and frontend tests, runs lint, surfaces failures, and drafts a commit message in the <type>: <description> format from CLAUDE.md.
allowed-tools: Bash, Read, Grep, Glob
---

# Commit Prep

Run the pre-commit gauntlet. Identifies what changed, runs the relevant tests and lint, surfaces any failures, and drafts a commit message following the project's `<type>: <description>` convention.

This command does **not** create the commit. It prepares you to commit cleanly — the actual `git commit` is your call.

## Step 1: Identify Changed Files

```bash
# Tracked changes (staged + unstaged)
git diff --name-only HEAD

# Untracked files
git ls-files --others --exclude-standard
```

Bucket into:

- **Backend (`.py` in `platform/`)**
- **Frontend (`.jsx`, `.tsx`, `.js`, `.css` in `portal/`)`**
- **Tests (`.py` under `platform/tests/` or `.test.*` under `portal/`)**
- **Other** (docs, config, CLAUDE.md, etc.)

If no files changed, stop and report "Nothing to commit."

## Step 2: Run Related Backend Tests

For each changed backend file, determine the related test file(s):

- `platform/routers/<name>.py` → `platform/tests/test_<name>.py`
- `platform/agents/<name>.py` → `platform/tests/test_agents_<name>.py` (or the closest match)
- `platform/models/<name>.py` → `platform/tests/test_models.py` or per-model test

Then:

```bash
cd platform && ./run_tests.sh tests/test_<module>.py
```

**Do NOT** run the full suite. Per `CLAUDE.md`, full-suite runs are manual.

## Step 3: Run Related Frontend Tests

For each changed frontend file:

```bash
cd portal && npm test -- <test-file-or-pattern>
```

If no test file exists yet for a newly added component, flag it — per the global TDD rule in `CLAUDE.md`, the code change should have been preceded by a failing test.

## Step 4: Run Lint

```bash
# Frontend lint
cd portal && npm run lint

# Backend lint (if ruff is installed)
cd platform && source .venv/bin/activate && ruff check .
```

## Step 5: Surface Failures

Produce a concise pass/fail summary:

```
Commit Prep Report
──────────────────────────────
Backend tests:   PASS (3 files, 28 tests)
Frontend tests:  PASS (2 files, 14 tests)
Frontend lint:   FAIL (2 errors in src/Login.jsx)
Backend lint:    PASS
──────────────────────────────
```

If anything fails, stop here and report the failures. Do **not** draft a commit message for a failing state.

## Step 6: Draft Commit Message

Only if all checks pass. Classify the change using CLAUDE.md's type list: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

Read the diff to summarise the change. Produce a single-line message in the exact format:

```
<type>: <description>
```

Rules:

- `<description>` is a present-tense verb phrase, lowercase, no trailing period
- Keep it under 72 characters
- Be specific about what changed, not vague (avoid "update code", "misc fixes")

Examples:

- `feat: add estimate rejection endpoint with audit trail`
- `fix: handle empty material list in estimate agent`
- `refactor: extract pydantic validators to shared helpers`

## Step 7: Final Readout

Present the drafted commit message and the command to run it:

```
Suggested commit:

  git commit -m "<type>: <description>"

Ready to commit? (User decides — this command does not run git commit.)
```

## Integration with Other Commands

- Run `/code-review` before `/commit-prep` to catch issues early
- If the build is broken, run `/build-fix` first
- After commit, when ready to open a PR: `/pr-description`
