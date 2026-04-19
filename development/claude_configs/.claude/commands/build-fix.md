---
description: Incrementally fix build, type, and lint errors with minimal, safe changes. Re-runs the relevant build command after each fix to verify no new errors are introduced.
argument-hint: [backend|frontend|lint|all]
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Build and Fix

Incrementally fix build, type, and lint errors with minimal, safe changes.

`$ARGUMENTS` (optional) scopes which build to run: `backend`, `frontend`, `lint`, or `all` (default).

## Step 1: Select Build Target

| `$1` value  | Command(s) to run                                                 |
|-------------|-------------------------------------------------------------------|
| `backend`   | `cd platform && python -m compileall -q .` (and `ruff check .` if installed) |
| `frontend`  | `cd portal && npm run build`                                      |
| `lint`      | `cd portal && npm run lint`                                       |
| `all` (default) | Run backend compile check, frontend build, and lint in sequence |

**Note:** `./run_tests.sh` is *not* a build command — it's the test runner. Use `/code-review` or let `/commit-prep` surface test failures; this command only touches build/compile/lint errors.

## Step 2: Parse and Group Errors

1. Run the build command and capture stderr
2. Group errors by file path
3. Sort by dependency order (fix imports/types before logic errors)
4. Count total errors for progress tracking

## Step 3: Fix Loop (One Error at a Time)

For each error:

1. **Read the file** — see error context (10 lines around the error)
2. **Diagnose** — identify root cause (missing import, wrong type, syntax error)
3. **Fix minimally** — smallest change that resolves the error
4. **Re-run build** — verify the error is gone and no new errors introduced
5. **Move to next** — continue with remaining errors

## Step 4: Guardrails

Stop and ask the user if:

- A fix introduces **more errors than it resolves**
- The **same error persists after 3 attempts** (likely a deeper issue)
- The fix requires **architectural changes** (not just a build fix)
- Build errors stem from **missing dependencies** (need `pip install` or `npm install`)
- A fix would require **changing a test to match** — breaking a test to make a build pass is almost never correct; flag it instead

## Step 5: Summary

Show results:

- Errors fixed (with file paths)
- Errors remaining (if any)
- New errors introduced (should be zero)
- Suggested next steps for unresolved issues

## Recovery Strategies

| Situation                | Action                                                             |
|--------------------------|--------------------------------------------------------------------|
| Missing Python module    | Check venv is activated; suggest `pip install -r requirements.txt` |
| Missing npm package      | Suggest `cd portal && npm install`                                 |
| Beanie model not registered | Check `database.py:init_db()` document list                     |
| Import cycle             | Identify cycle; suggest extraction to shared module                |
| Type mismatch            | Read both type definitions; fix the narrower type                  |

Fix one error at a time for safety. Prefer minimal diffs over refactoring.
