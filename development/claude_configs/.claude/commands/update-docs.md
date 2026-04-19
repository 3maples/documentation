---
description: Sync CLAUDE.md and project documentation with the current codebase. Flags stale docs and generates updates from source-of-truth files like config.py and routers.
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Update Documentation

Sync documentation with the codebase, generating from source-of-truth files.

## Step 1: Identify Sources of Truth

| Source | Documents |
|--------|-----------| 
| `platform/config.py` Settings class | Required environment variables |
| `platform/routers/` route files | API endpoint reference |
| `platform/models/` Beanie models | Data model documentation |
| `portal/package.json` scripts | Frontend available commands |
| `platform/run_tests.sh` | Backend test commands |
| `.env.example` (if exists) | Environment variable reference |

## Step 2: Check CLAUDE.md Accuracy

1. Read `CLAUDE.md`
2. Cross-reference with actual files:
   - Are all listed commands still correct?
   - Are the file/directory descriptions accurate?
   - Are the environment variable names still current?
3. Flag any stale content

## Step 3: Update Environment Documentation

1. Read `platform/config.py` Settings class
2. Extract all fields with their types and defaults
3. Generate or update the "Environment Configuration" section in `CLAUDE.md`

## Step 4: Staleness Check

1. Find documentation files not modified in 90+ days
2. Cross-reference with recent source code changes (`git log --since="90 days ago"`)
3. Flag potentially outdated docs for manual review

## Step 5: Show Summary

```
Documentation Update
──────────────────────────────
Updated:   CLAUDE.md (environment variables section)
Flagged:   docs/API.md (142 days stale)
Skipped:   README.md (no changes detected)
──────────────────────────────
```

## Rules

- **Single source of truth**: Generate from code, never manually edit generated sections
- **Preserve manual sections**: Only update generated sections; leave hand-written prose intact
- **Don't create docs unprompted**: Only create new doc files if the command explicitly requests it
- **GEMINI.md is separate**: That file contains Antigravity review rules — don't overwrite it
