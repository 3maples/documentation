---
description: Create a new changelog entry. Finds the latest version in documentation/changelog/, increments it, and writes a non-technical summary of the current session's work.
allowed-tools: Bash, Read, Write, Glob
---

# Changelog

Create a new changelog entry for the work completed in the current conversation session.

## Step 1: Find the Latest Version

```bash
ls /Users/simon/Development/Tangz/3maples/documentation/changelog/ | grep '^change-log-' | sort -V | tail -1
```

Parse the version number from the filename (format: `change-log-X.Y.Z.md`).

## Step 2: Increment the Version

Default: bump the **minor** version (0.12.0 → 0.13.0) and reset patch to 0.

If the user passed `$ARGUMENTS`, interpret it as the bump type:
- `major` → X+1.0.0
- `minor` → X.Y+1.0 (default)
- `patch` → X.Y.Z+1

## Step 3: Read the Previous Entry for Format Reference

Read the most recent changelog file to match its exact structure. The format is **JSON** (despite the `.md` extension):

```json
{
  "version": "X.Y.Z",
  "date": { "$date": "YYYY-MM-DDT00:00:00Z" },
  "content": "## Improvements\n- **Title** — description.\n\n## Safety\n- **Title** — description.",
  "created_at": { "$date": "YYYY-MM-DDT12:00:00.000Z" }
}
```

## Step 4: Summarize the Session

Review what was accomplished in the **current conversation** and write a **non-technical, concise, high-level** summary aimed at end users — not developers. The reader is a customer scanning what's new; they should be able to understand every line without engineering context.

### Style rules

- **Concise.** Aim for **2–4 bullets total** across the whole entry. If you have more than four, you're listing implementation steps instead of user-visible changes — collapse related items into one bullet.
- **High-level.** Group related work under one bullet. Five UI polish tweaks become one "smoother layout in X" bullet. A new feature plus its tests, docs, and supporting refactors is one bullet.
- **Non-technical.** No file paths, function names, endpoint names, component names, framework names, test names, or code references. Speak about *what the user sees or can do*, not how it was built.
- **Plain language.** Prefer short, direct sentences. Avoid jargon ("payload", "endpoint", "schema", "state", "props"). Avoid hedges ("various", "several", "some").
- **US English spellings** (labor, color, behavior, organize).
- **Format.** Group under headers — `## New Features`, `## Improvements`, `## Fixes`, `## Safety` — using only those that apply. Each bullet: `- **Short Title** — one-sentence user-facing description.`

### What to write about

Focus on what a user would notice or care about:
- A new capability they didn't have before → `## New Features`
- An existing capability that's now faster / clearer / easier → `## Improvements`
- A bug that's now fixed → `## Fixes`
- A guardrail that protects their data or money → `## Safety`

Skip:
- Internal refactors, code reorganization, dependency bumps
- Test additions, lint fixes, type fixes
- Docs and changelog entries themselves
- Behavior changes that don't affect what the user sees

### Examples

**Too technical (rewrite):**
- `- **Analytics Endpoint** — added /estimates/analytics with $facet aggregation for headline + by_division + by_status payloads.`
- `- **RowActionsMenu Component** — extracted reusable three-dot menu using portal-rendered dropdown.`
- `- **Maple object_link helper** — agents now embed markdown links to portal routes in their response strings.`

**Right (concise, user-facing):**
- `- **Dashboard Time Filters** — choose This Month, This Quarter, or This Year to scope your division and status charts.`
- `- **Reorder Line Items** — move materials, activities, and rate card rows up or down from a new three-dot menu.`
- `- **Clickable Records in Chat** — when Maple mentions a property, contact, material, person, or estimate, click it to jump straight to that record.`

If the session produced no user-visible changes (only docs, internal refactors, or config tweaks), tell the user and ask whether to still create an entry.

## Step 5: Write the File

Use today's date (from the system context) for both `date` and `created_at`. Write to:

```
/Users/simon/Development/Tangz/3maples/documentation/changelog/change-log-<NEW_VERSION>.md
```

**Do not** insert the entry into the database — this is a file-only artifact.

## Step 6: Confirm

Report the new filename and version, and show the `content` block so the user can verify the summary reads correctly.
