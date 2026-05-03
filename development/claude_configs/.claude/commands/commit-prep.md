---
description: Pre-commit gauntlet — identifies changed files across platform/, portal/, website/, and documentation/ repos, runs related tests and lint, surfaces failures, and drafts a commit message in the <type>: <description> format from CLAUDE.md.
allowed-tools: Bash, Read, Grep, Glob
---

# Commit Prep

Run the pre-commit gauntlet. Identifies what changed, runs the relevant tests and lint, surfaces any failures, and drafts a commit message following the project's `<type>: <description>` convention.

This command does **not** create the commit. It prepares you to commit cleanly — the actual `git commit` is your call.

## Repository Layout

The workspace root (`3maples/`) is **not** a git repo. Each of the following subfolders is its own independent git repository and must be inspected separately:

- `platform/` — FastAPI backend
- `portal/` — React frontend (in-app)
- `website/` — Vite-built marketing landing page (static HTML + the public Maple widget React bundle)
- `documentation/` — project docs, changelogs, plans

For every git-aware step below, run the command in each of the four repos that has changes. If a repo has no changes, skip it silently. If **none** of the four repos have changes, stop and report "Nothing to commit."

Commits are per-repo: a single `/commit-prep` invocation may produce up to four drafted commit messages, one per repo with changes.

## Step 1: Identify Changed Files

For each repo (`platform`, `portal`, `website`, `documentation`):

```bash
# Tracked changes (staged + unstaged)
git -C <repo> diff --name-only HEAD

# Untracked files
git -C <repo> ls-files --others --exclude-standard
```

Bucket changes by repo:

- **platform** — backend `.py` files (routers, agents, models, services, tests)
- **portal** — frontend `.jsx`, `.tsx`, `.js`, `.css`, test files
- **website** — `index.html`, `pricing.html`, `widget/*` (.tsx/.ts/.css), `vite.config.ts`, `vitest.config.ts`, `.env.*`, `package.json`, `package-lock.json`
- **documentation** — `.md` files, changelogs, plans, diagrams

If a repo reports no changes, skip its test/lint steps entirely.

## Step 2: Run Related Backend Tests (only if `platform` has changes)

For each changed backend file, determine the related test file(s):

- `platform/routers/<name>.py` → `platform/tests/test_<name>.py`
- `platform/agents/<name>.py` → `platform/tests/test_agents_<name>.py` (or the closest match)
- `platform/models/<name>.py` → `platform/tests/test_models.py` or per-model test
- `platform/services/<name>.py` → `platform/tests/test_<name>_service.py` (or closest match)

Then:

```bash
cd platform && ./run_tests.sh tests/test_<module>.py
```

**Do NOT** run the full suite. Per `CLAUDE.md`, full-suite runs are manual.

## Step 3: Run Related Frontend Tests — Portal (only if `portal` has changes)

For each changed frontend file:

```bash
cd portal && npm test -- <test-file-or-pattern>
```

If no test file exists yet for a newly added component, flag it — per the global TDD rule in `CLAUDE.md`, the code change should have been preceded by a failing test.

## Step 4: Run Widget Tests + Build — Website (only if `website` has changes)

The website's React widget at `website/widget/` is bundled separately by Vite. Run vitest for unit coverage and the production build for HTML/asset wiring sanity:

```bash
cd website && npm test                  # vitest run on widget/__tests__/
cd website && npm run build             # rebuilds dist/index.html + dist/maple-widget.js
```

If the build fails (missing entry, broken Rollup input, env-var typo), surface the error verbatim — the dev server (`npm run dev`) often hides these because it serves source modules on demand rather than the rolled-up output.

The website has **no `lint` script** in `package.json`; skip linting for that repo.

## Step 5: Run Lint (scoped to repos with changes)

```bash
# Frontend lint — only if portal changed
cd portal && npm run lint

# Backend lint — only if platform changed (if ruff is installed)
cd platform && source .venv/bin/activate && ruff check .
```

The `website` and `documentation` repos have no lint step; skip them.

## Step 6: Surface Failures

Produce a concise per-repo pass/fail summary. Include only the repos with changes:

```
Commit Prep Report
──────────────────────────────
platform:
  Backend tests:   PASS (3 files, 28 tests)
  Backend lint:    PASS
portal:
  Frontend tests:  PASS (2 files, 14 tests)
  Frontend lint:   FAIL (2 errors in src/Login.jsx)
website:
  Widget tests:    PASS (1 file, 7 tests)
  Build:           PASS (dist/maple-widget.js + dist/index.html clean)
documentation:
  Changes:         2 files (no tests/lint applicable)
──────────────────────────────
```

If anything fails, stop here and report the failures. Do **not** draft a commit message for a failing state.

## Step 7: Draft Commit Messages (one per repo with changes)

Only if all checks pass. Classify each repo's change using CLAUDE.md's type list: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

Read each repo's diff independently to summarise its change. Produce a single-line message per repo in the exact format:

```
<type>: <description>
```

Rules:

- `<description>` is a present-tense verb phrase, lowercase, no trailing period
- Keep it under 72 characters
- Be specific about what changed, not vague (avoid "update code", "misc fixes")
- Changes in `documentation/` should almost always be typed `docs:`

If a repo's diff covers two or more clearly-separable concerns (e.g. the platform repo touches both a new feature and an unrelated bug fix), draft **multiple** suggested messages for that repo and group the files under each. The user can stage selectively before running `git commit`.

Examples:

- `feat: add estimate rejection endpoint with audit trail` (platform)
- `fix: handle empty material list in estimate agent` (platform)
- `refactor: extract pydantic validators to shared helpers` (platform)
- `feat: add login error banner to welcome page` (portal)
- `feat: add public Maple Q&A widget to marketing landing page` (website)
- `docs: add 0.12.0 changelog entry` (documentation)

## Step 8: Final Readout

Present the drafted commit message(s) and the commands to run them, grouped by repo:

```
Suggested commits:

  # platform
  git -C platform commit -m "<type>: <description>"

  # portal
  git -C portal commit -m "<type>: <description>"

  # website
  git -C website commit -m "<type>: <description>"

  # documentation
  git -C documentation commit -m "<type>: <description>"

Ready to commit? (User decides — this command does not run git commit.)
```

Only include the lines for repos that actually have changes.

## Integration with Other Commands

- Run `/code-review` before `/commit-prep` to catch issues early
- If the build is broken, run `/build-fix` first
- After commit, when ready to open a PR: `/pr-description`
