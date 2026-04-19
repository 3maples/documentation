---
description: Draft a pull request description from the current branch. Analyzes git diff and log against the base branch and produces Summary / Test Plan / Risk sections per the CLAUDE.md Git Workflow format.
argument-hint: [optional-base-branch]
allowed-tools: Bash, Read, Grep
---

# PR Description

Draft a comprehensive pull request description from the current branch's full history — not just the latest commit. Produces Summary, Test Plan, and Risk sections following the `CLAUDE.md` Git Workflow format.

`$ARGUMENTS` (optional) overrides the base branch. Defaults to `main`.

## Step 1: Determine Base Branch

```bash
# If $ARGUMENTS is set, use it. Otherwise default to "main".
BASE="${1:-main}"

# Verify the branch exists
git rev-parse --verify "$BASE" > /dev/null
```

If the base branch doesn't exist locally, fetch it or ask the user which base to use.

## Step 2: Collect Full Branch History

```bash
# Commit list — all commits on this branch since it diverged
git log "$BASE"..HEAD --oneline

# Full diff against the merge base (not just the last commit)
git diff "$BASE"...HEAD

# Which files changed
git diff --name-only "$BASE"...HEAD
```

Per `CLAUDE.md`, review **all commits** that will be included in the PR, not just the latest. Do not base the description on `HEAD` alone.

## Step 3: Analyze the Changes

Bucket the changes:

- **What's new** — new files, new endpoints, new components, new features
- **What changed** — behaviour changes, bug fixes, refactors
- **What's removed** — deleted files, removed endpoints, deprecated features
- **Tests** — what test files were added or modified; which suites cover the change
- **Docs / config** — CLAUDE.md, .env.example, package.json, requirements.txt

Look for patterns that belong in the Risk section: schema changes, deletions, config changes, auth changes, anything under `platform/database.py`, anything that touches CORS, anything that changes external API contracts.

## Step 4: Draft the PR Description

Produce output in this format (note: the title should be short, under 70 characters, as per `CLAUDE.md`):

```markdown
## Summary

<2-4 bullet points describing what changed and why. Use the highest-signal framing — a
reviewer should understand the change's purpose from this section alone.>

## Changes

<Grouped list of specific changes. Group by area: Backend, Frontend, Tests, Docs.
Skip any group that has no changes.>

### Backend
- <file>: <change>

### Frontend
- <file>: <change>

### Tests
- <file>: <new/updated tests covering X>

## Test Plan

<Bulleted checklist of what was tested, matching the test files modified. Per CLAUDE.md,
include which test files were run locally.>

- [ ] Backend: ran `./run_tests.sh tests/test_<module>.py` locally
- [ ] Frontend: ran `npm test -- <file>` locally
- [ ] Lint: `npm run lint` clean
- [ ] Manual verification: <brief description of manual testing, if applicable>

## Risk

<Anything reviewers should scrutinize carefully. If low-risk, say so explicitly.
Topics to surface if present:
- Schema / Beanie model changes
- Deletions of routes or public functions
- Auth / CORS / session changes
- External API contract changes
- Dependency version bumps
- Anything that touches database.py init_db()>
```

## Step 5: Suggest a Title

Draft a title under 70 characters. Prefer the imperative mood, matching the commit type convention from `CLAUDE.md`:

- `feat: add estimate rejection endpoint with audit trail`
- `fix: handle empty material list in estimate agent`
- `refactor: consolidate review commands into dispatcher`

## Step 6: Final Output

Present the suggested title and the full description. Offer the `gh pr create` command the user can copy:

```bash
gh pr create --title "<suggested title>" --body "$(cat <<'EOF'
<description content>
EOF
)"
```

**This command does not create the PR.** The user decides when to run the `gh pr create`.

## Integration with Other Commands

- Run `/commit-prep` to make sure all commits are clean before generating this
- If the description references test files, those files should have already been updated as part of the TDD flow (per `CLAUDE.md`)
- For security-sensitive changes, also surface "run the built-in `/security-review` before merge" in the Risk section
