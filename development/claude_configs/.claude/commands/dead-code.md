---
description: Safely identify and remove dead code (unused functions, imports, dependencies) with test verification at every step.
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Dead Code Cleanup

Safely identify and remove dead code with test verification at every step.

## Step 1: Detect Dead Code

Run analysis tools:

| Tool     | What It Finds           | Command                                                                                           |
|----------|-------------------------|---------------------------------------------------------------------------------------------------|
| vulture  | Unused Python code      | `cd platform && source .venv/bin/activate && pip install vulture && vulture . --min-confidence 80` |
| depcheck | Unused npm dependencies | `cd portal && npx depcheck`                                                                       |

If tools aren't available, use grep to find exports with zero imports:

```bash
# Find unused Python functions/classes
grep -rn "^def \|^class " platform/ --include="*.py"
```

## Step 2: Categorize Findings

Sort findings into safety tiers:

| Tier      | Examples                                                           | Action                         |
|-----------|--------------------------------------------------------------------|--------------------------------|
| **SAFE**  | Unused utility functions, internal helpers, unused imports         | Delete with confidence         |
| **CAUTION** | Router endpoints, agent tools, model fields                     | Verify no external callers     |
| **DANGER** | Config files, `main.py`, `database.py`, model base classes       | Investigate before touching    |

## Step 3: Safe Deletion Loop

For each SAFE item:

1. **Run related tests** — establish baseline (all green)
   ```bash
   cd platform && ./run_tests.sh tests/test_<module>.py
   ```
2. **Delete the dead code** — surgical removal
3. **Re-run tests** — verify nothing broke
4. **If tests fail** — immediately revert with `git checkout -- <file>` and skip this item
5. **If tests pass** — move to next item

## Step 4: Handle CAUTION Items

Before deleting CAUTION items:

- Search for dynamic references: route names in frontend, agent tool names in prompts
- Check if exported from a public API route
- Verify no LangChain agent tools reference the function by name

## Step 5: Consolidate Duplicates

After removing dead code, look for:

- Near-duplicate Pydantic models — merge into one base
- Repeated validation logic in multiple routers — extract to shared utility
- Duplicated agent prompt snippets — consolidate into `prompts/` module

## Step 6: Summary

```
Dead Code Cleanup
──────────────────────────────
Deleted:   N unused functions
           N unused imports
Skipped:   N items (tests failed or DANGER tier)
──────────────────────────────
All related tests passing
```

## Rules

- **Never delete without running tests first**
- **One deletion at a time** — atomic changes make rollback easy
- **Skip if uncertain** — better to keep dead code than break production
- **Don't refactor while cleaning** — separate concerns (clean first, refactor later)
- **TDD exemption:** per `CLAUDE.md`, dead code removal does not require writing new tests — just verify that existing tests still pass after each deletion
