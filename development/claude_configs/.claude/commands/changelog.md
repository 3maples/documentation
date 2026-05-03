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

Review what was accomplished in the **current conversation** and write a **non-technical, high-level** summary aimed at end users — not developers.

Guidelines:
- Use plain language — no file paths, function names, test names, or code references
- Group items under headers like `## Improvements`, `## Safety`, `## Fixes`, `## New Features` — use only the headers that apply
- Each bullet: `- **Short Title** — one-sentence user-facing description.`
- Focus on what the user can now do, or what is safer/faster/clearer for them
- Use US English spellings (labor, color, behavior)
- Keep it brief — 3–5 bullets total is typical
- Keep it non-technical and easy to understand

If the session did not produce user-visible changes (e.g. only docs, internal refactors, or config tweaks), tell the user and ask whether to still create an entry.

## Step 5: Write the File

Use today's date (from the system context) for both `date` and `created_at`. Write to:

```
/Users/simon/Development/Tangz/3maples/documentation/changelog/change-log-<NEW_VERSION>.md
```

**Do not** insert the entry into the database — this is a file-only artifact.

## Step 6: Confirm

Report the new filename and version, and show the `content` block so the user can verify the summary reads correctly.
