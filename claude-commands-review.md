# Review of `.claude/commands/` — Improvements and New Command Proposals

**Date:** 19 April 2026 (updated after user decisions)
**Scope:** All 7 files in `.claude/commands/` plus `.claude/agents/tdd-guide.md` (for dependency tracing). Settings file and agents beyond `tdd-guide` were out of scope.
**Reviewer posture:** This is a report only — no file changes have been made. All proposals below are suggestions awaiting your approval.

**User decisions recorded (19 Apr 2026):**
- `python-review.md` will be **consolidated into `code-review.md` using a dispatcher pattern** (single entry point that branches on changed file types).
- Command files will stay as **prose that Claude reads**, not inline-bash automation. No `!` or `@` prefixes will be introduced in this round.
- The following proposed new commands are **out of scope** and will not be pursued: `/scaffold-router`, `/model-diff`, `/bug-repro`.
- **All remaining proposed new commands are approved** and will be drafted: `/commit-prep`, `/pr-description`, `/agent-prompt-review`.
- **Consolidation approved** — proceed with merging `python-review.md` into `code-review.md`.
- **Short-term improvements approved** — frontmatter, `$ARGUMENTS` support, and completion of the truncated `tdd-guide.md` will be bundled together with the consolidation.
- **No custom security command** — the built-in `/security-review` covers the deeper audit need (see §3.7).
- **`/tdd` command will be deleted** — TDD becomes a global default, enforced by strengthened language in `CLAUDE.md` with explicit carve-outs for non-code changes. The `tdd-guide` agent stays (still callable via the Task tool for focused TDD sessions).
- **No subdirectory namespacing** — all commands stay flat at the top level of `.claude/commands/`. Invocations remain `/code-review`, `/commit-prep`, etc. rather than `/review:code`, `/git:commit-prep`. Decision is firm, not deferred.

---

## 1. Executive Summary

Your command library is in better shape than most projects of this size. Each file reads like it was written with intent: clear step-by-step structure, project-specific details (Beanie, FastAPI, LangChain, the `platform/` and `portal/` layout), and explicit cross-references between commands. The weaknesses are mostly structural rather than conceptual — missing frontmatter, no argument handling, one broken agent reference, and some overlap between `code-review` and `python-review` that could be tightened up.

The single most important issue is a **broken dependency**: `python-review.md` claims to invoke a `python-reviewer` agent, but no such file exists in `.claude/agents/`. This gets resolved automatically by the agreed consolidation — `python-review.md` will be merged into `code-review.md` as a backend section within a dispatcher pattern, and the broken agent claim disappears with it.

Beyond that, the highest-value improvements are (a) adding proper frontmatter to every command so the slash-command picker shows useful descriptions and so tool permissions are scoped, and (b) introducing `$ARGUMENTS` support so commands like `/test-coverage platform/routers/estimates.py` become possible. Per your decision, we are **keeping the prose-that-Claude-reads style** — no inline `!` bash execution or `@` file inclusion in this round.

I've also proposed a small set of new commands that fit your stated workflow in `CLAUDE.md` — `/commit-prep`, `/pr-description`, and `/agent-prompt-review`. Frontend-specific review is handled as a section *inside* the consolidated `/code-review`, not as a separate command.

---

## 2. Overall Strengths

Before the critique, what's working well. Each command has a clear single responsibility — `build-fix` fixes build errors, `test-coverage` raises coverage, `refactor-clean` removes dead code. The files are project-specific rather than generic; for example, `build-fix.md` correctly distinguishes between `./run_tests.sh` for the backend and `npm run build` for the frontend, and `refactor-clean.md` knows to check LangChain agent tool names before deleting functions. The "Integration with Other Commands" sections at the bottom of `tdd.md` and `python-review.md` are a nice touch — they create a mental model of a workflow rather than isolated commands. The severity-tier framing (CRITICAL / HIGH / MEDIUM) in `code-review.md` and `python-review.md` gives Claude a clear way to prioritise output.

---

## 3. Cross-Cutting Issues

### 3.1 Missing frontmatter on 5 of 7 commands

Only `python-review.md` and `tdd.md` have YAML frontmatter. The other five (`build-fix`, `code-review`, `refactor-clean`, `test-coverage`, `update-docs`) have none. Frontmatter matters for three reasons: it supplies the description that appears in the slash-command picker, it can restrict which tools the command is allowed to use (`allowed-tools`), and it can declare `argument-hint` so the user sees what arguments are expected when they type `/command-name `.

A good template is:

```yaml
---
description: One-line summary that shows in the / picker
argument-hint: [optional-file-path]
allowed-tools: Bash, Read, Edit, Grep, Glob
model: sonnet
---
```

Even the two commands that have frontmatter don't declare `allowed-tools` or `argument-hint`. In a codebase with real secrets (your `.env`), scoping `allowed-tools` is a small but meaningful defence-in-depth win.

### 3.2 No `$ARGUMENTS` usage anywhere

Every command operates on the entire working tree or on `git diff`. None of them accept arguments. This makes them less composable than they could be. Candidates for argument support include `/test-coverage <file-path>` to focus on a single file, `/build-fix <backend|frontend|lint>` to scope which build to run, `/python-review <file-path>` to review a single module rather than all changed files, and `/update-docs <section>` to target a specific CLAUDE.md section. The Claude Code convention is `$ARGUMENTS` for the whole string or `$1`, `$2` for positional arguments.

### 3.3 Prose-only commands — kept by design

Every command lists bash commands in fenced code blocks and relies on the model to read the prose and run them. Claude Code also supports a `!` prefix for inline bash execution and `@` for file inclusion, which would make commands more deterministic.

**Decision recorded:** we are *keeping the prose-that-Claude-reads style* for now. This section is retained for completeness so a future reader understands the tradeoff. The cost is that commands behave more like guides than automations; the benefit is they remain human-readable, easier to edit, and portable across Claude sessions. Revisit if commands start misfiring.

### 3.4 Broken reference: the `python-reviewer` agent does not exist

`python-review.md` line 5 says *"This command invokes the python-reviewer agent for comprehensive Python-specific code review."* There is no `.claude/agents/python-reviewer.md`. **Resolution path (approved):** consolidate `python-review.md` into `code-review.md` as a Backend (Python) section under a dispatcher structure. The broken reference disappears because the file disappears; no new agent needs to be created. See §3.6 and §4.2 for the dispatcher design.

### 3.5 Inconsistent command-to-command referencing

`tdd.md` and `python-review.md` both have "Integration with Other Commands" sections, but the other five don't. If this is a pattern you like, it should be in every file; if it isn't, those two are over-formatted relative to the rest. My recommendation is to keep the pattern but move it to a uniform short footer so readers of any command learn the workflow.

### 3.6 Consolidation plan: dispatcher pattern (approved)

`python-review.md` will be folded into `code-review.md`. The merged file will use a **dispatcher pattern** — a single entry point that inspects the changed files and applies only the relevant rules.

**Structure of the new `code-review.md`:**

1. **Step 1 — Discover changes.** `git diff --name-only HEAD` (prose instruction, as today). Bucket files into `.py` (backend), `.jsx`/`.tsx`/`.js`/`.css` (frontend), and other (config, docs, tests).
2. **Step 2 — Cross-Cutting checks (always run).** Secrets, hardcoded credentials, missing input validation, TODO/FIXME hygiene, missing tests for new code, large functions/files/nesting. These apply regardless of language.
3. **Step 3 — Backend (Python) checks (only if `.py` changed).** The full content currently in `python-review.md`: ruff/mypy/bandit guidance, Beanie N+1 patterns, async-purity inside route handlers, Pydantic validation, mutable default arguments, LangChain prompt-injection, CORS, bare except clauses.
4. **Step 4 — Frontend (React) checks (only if `.jsx`/`.tsx` changed).** Accessibility (a11y), React hook correctness (deps arrays, stale closures), Tailwind class misuse in artifact-style code, unused components, console.log left in, XSS via `dangerouslySetInnerHTML`. Lighter than the Python section for now; can grow.
5. **Step 5 — Severity-tiered report.** Keep the existing CRITICAL / HIGH / MEDIUM / LOW framing from today's `code-review.md`, apply tiers across whichever sections ran.
6. **Step 6 — Recommendation.** "Recommend blocking commit if CRITICAL or HIGH" (softened from today's inaccurate "Block commit" wording — Claude can't actually block commits).

The merged file will be larger but still readable — target around 150 lines. `python-review.md` will be deleted after the merge.

### 3.7 Security coverage: layered with Claude Code's built-in `/security-review`

Worth recording explicitly so it isn't forgotten. The consolidated `/code-review` will include security checks as part of Step 2 (cross-cutting: hardcoded credentials, missing input validation, insecure dependencies, CORS wildcards) and Step 3 (backend: injection, LangChain prompt injection, bare except clauses, unsafe async patterns). This is a "top-of-funnel" security pass suitable for running on every change.

It is **not** a full security audit. Known gaps in the current `/code-review` coverage: authentication/authorization decorators on routes, missing role checks, JWT/session handling, rate limiting, SSRF, path traversal, unsafe deserialization (`pickle`, `yaml.load`, `eval`), secrets leaking into logs, supply-chain CVE scanning (`pip-audit`, `npm audit`), error-message information disclosure (stack traces returned to clients), file upload validation, and regex DoS (ReDoS).

**Claude Code already ships with a built-in `/security-review` command** (*"Complete a security review of the pending changes on the current branch"*). It is available today without any file being added to `.claude/commands/`. Recommendation: treat the two as **layered**, not alternatives.

- `/code-review` — lightweight security pass run as part of every pre-commit review. Catches the high-frequency issues.
- `/security-review` (built-in) — deeper audit run before release candidates, or after touching authentication, session management, file upload, or dependency updates.

**Do not add a third custom security command** to `.claude/commands/`. It would duplicate the built-in `/security-review` and create confusion about which command to run when.

---

## 4. Per-File Review

### 4.1 `build-fix.md`

The detection table on lines 8–14 conflates running tests with running the build. `./run_tests.sh` is a test runner, not a build command; if the goal of this command is "fix compile/type errors before tests even run", the backend row should probably be `python -m compileall -q .` or `ruff check` rather than the test runner. The frontend row is correct.

The "Fix Loop" section is solid — incremental, one-at-a-time, with re-verification. The guardrails (stop after 3 failed attempts, stop if a fix introduces more errors, stop if architectural) are good. I'd consider adding one more guardrail: "Stop if a fix would require changing a test — fixing a build by breaking a test is almost never right."

Suggested rename: keep `build-fix`. Suggested argument: `$1` for `backend | frontend | lint | all`.

### 4.2 `code-review.md` — becomes the dispatcher

This file absorbs `python-review.md` per §3.6 and becomes the single review entry point. Concrete edits needed:

Add frontmatter: `description`, `argument-hint: [file-path]` (optional, to scope review to one file), `allowed-tools: Bash, Read, Grep, Glob`.

Make scoping explicit. `git diff --name-only HEAD` covers staged + unstaged changes but not untracked files. Add `git ls-files --others --exclude-standard` so new files also get reviewed.

Soften the "Block commit" wording on line 39 to "Recommend blocking commit…" — Claude can't actually block a commit, and the file should be honest about that.

Restructure into the six-step dispatcher outlined in §3.6: discover → cross-cutting → backend (conditional) → frontend (conditional) → tiered report → recommendation.

**No rename.** Since `python-review.md` is being consumed, there's no more naming collision, and `/code-review` remains the natural single-command name.

### 4.3 `python-review.md` — deleted after merge

All content moves into `code-review.md` Step 3 (Backend checks). The one exception is the automated-tooling block (`ruff check`, `mypy`, `bandit`) — keep that in the new Backend section, but drop the `./run_tests.sh --cov --cov-report=term-missing` line because that overlaps with `/test-coverage`. A review command should report coverage gaps, not re-run coverage tooling; call out the gap and let the user invoke `/test-coverage` separately.

The approval criteria table (Approve / Warning / Block) is worth preserving in the merged file as part of Step 6.

The broken "invokes the python-reviewer agent" claim on line 5 simply goes away when the file is deleted. No new agent gets created.

### 4.4 `refactor-clean.md`

The three-tier safety classification (SAFE / CAUTION / DANGER) is excellent and I'd copy it into any future command that removes things. The "run tests between every deletion" discipline is the right discipline.

One subtle issue: the command suggests `pip install vulture` inline during the run. This is fine for ad-hoc use, but it means every invocation of the command may attempt an install. Better practice is to add `vulture` to a `requirements-dev.txt` and check if it's present before falling back to grep.

Suggested rename: `dead-code` or `cleanup`. `refactor-clean` slightly overpromises — this command removes dead code, it doesn't refactor. Refactoring is a separate (and more dangerous) activity.

### 4.5 `tdd.md`

This one has frontmatter and correctly references the `tdd-guide` agent that does exist. The content is mostly process description (Red-Green-Refactor), which is fine but somewhat redundant with the agent's own instructions. A tighter version would be: "This command invokes the tdd-guide agent. See `.claude/agents/tdd-guide.md` for the methodology." — and then the command file just needs to handle the user-facing framing and the `$ARGUMENTS` parsing (e.g., `/tdd <feature-description>`).

The "MANDATORY: Tests must be written BEFORE implementation" and "Never skip the RED phase" lines are important — keep those in the command itself so they're visible every time, not just in the agent.

### 4.6 `test-coverage.md`

Clean, focused command. Two improvements. First, it should accept a file-path argument so you can target a specific module. Right now `/test-coverage` runs coverage across everything, which is slow for a focused session. Second, the "generate missing tests" step overlaps with `/tdd` — arguably, `/test-coverage` should identify gaps and hand off to `/tdd` for the actual writing, rather than doing both.

Suggested rename: just `coverage` is shorter and equivalent.

### 4.7 `update-docs.md`

Good command. The "Single source of truth" rule is the correct principle. The one gap is that it only considers `CLAUDE.md` — it doesn't cover the `documentation/` folder in your project, nor the `website/` folder. If those also need to be kept in sync with code, the command should list them. If they don't (e.g., they're marketing content), say so explicitly so the reader knows.

The GEMINI.md exclusion on line 54 is a good guard. Worth noting that GEMINI.md contains Antigravity review rules — if those rules reference commands or file paths that change, they'll drift too. Consider a separate `/update-gemini-docs` command (or extending this one with a flag).

### 4.8 `.claude/agents/tdd-guide.md` (agent, in scope per your answer)

The file is truncated at line 95 — it ends mid-sentence under the "Frontend (React + Vite)" header. This looks like a copy-paste or save truncation. The agent is otherwise well-structured: clear role, explicit workflow, edge-case checklist, anti-patterns section. Worth finishing the Frontend Patterns section and adding a final "Definition of Done" checklist. Also, the `tools` array on line 4 is `["Read", "Write", "Edit", "Bash", "Grep"]` — consider adding `Glob` since test-discovery often uses glob patterns.

---

## 5. Naming and Organisation

Your current convention — kebab-case, all lowercase — is correct and matches Claude Code's standard. Revised rename suggestions (reflecting the consolidation):

`build-fix` → keep (clear enough).
`code-review` → **keep** (now the single unified review command — no more collision).
`python-review` → **deleted** (content merged into `code-review`).
`refactor-clean` → **`dead-code`** (honest about what it does).
`tdd` → keep.
`test-coverage` → `coverage` (shorter).
`update-docs` → keep.

**Namespacing via subdirectories — decided against (19 Apr 2026).** Claude Code supports `.claude/commands/<group>/<command>.md` invoked as `/<group>:<command>`. Per user decision, this will **not** be adopted. All commands stay flat at the top level of `.claude/commands/`, invoked as `/code-review`, `/commit-prep`, and so on.

Reasoning recorded for future readers: after the consolidation, the final command list is short enough that flat organisation stays readable, and flat means no muscle-memory change from today's usage. Revisit only if the list grows beyond ~15 commands or if groupings become obvious.

Final flat structure after all changes:

```
.claude/commands/
  build-fix.md
  code-review.md          (dispatcher, absorbs python-review)
  commit-prep.md          (new)
  coverage.md             (renamed from test-coverage.md)
  dead-code.md            (renamed from refactor-clean.md)
  pr-description.md       (new)
  agent-prompt-review.md  (new)
  update-docs.md
```

---

## 6. Proposed New Commands

These are the new commands I'd add, ranked by how often I think you'd use them in this project. Each is described at the level of detail you'd need to decide whether you want it; I have not drafted the actual command files.

**`/commit-prep`** (high value). Runs the pre-commit gauntlet in one shot: identifies changed files, runs the relevant tests (`./run_tests.sh tests/test_<module>.py` on the backend, `npm test -- <file>` on the frontend), runs lint, and surfaces anything failing. Optionally drafts a commit message in your `<type>: <description>` format. This codifies step 4 of the Development Workflow in your `CLAUDE.md`.

**`/pr-description`** (high value). Given the current branch, runs `git diff main...HEAD` and `git log main..HEAD`, then drafts a PR description with Summary, Test Plan, and Risk sections. Your `CLAUDE.md` Git Workflow section describes this process — a command turns it into one keystroke.

**Frontend review — no longer a separate command.** Per the dispatcher decision, frontend checks live as Step 4 inside the unified `/code-review`. The substantive rules I'd have put in a `/frontend-review` command (accessibility, React hook correctness with deps arrays and stale closures, Tailwind misuse, unused components, Vite build concerns, `dangerouslySetInnerHTML` XSS) should be written into that Step 4 section of `code-review.md`.

**`/agent-prompt-review`** (lower but valuable for your project). Your backend has LangChain agents in `platform/agents/` with prompts in `platform/prompts/`. Review these for prompt-injection risk, instruction clarity, token efficiency, and temperature/model appropriateness. Because you're shipping agents in production, a dedicated review-the-agents command is more useful here than it would be in a typical FastAPI app.

**Explicitly not pursuing** (per your decision 19 Apr 2026): `/scaffold-router`, `/model-diff`, `/bug-repro`. Recorded here so the reasoning isn't lost: `/scaffold-router` was intended for bootstrapping new FastAPI routers with all the project wiring (Beanie registration, main.py include, test stub), but only pays off if routers are added frequently. `/model-diff` was intended to catch Beanie schema-change landmines but overlaps with what a careful `/code-review` already flags. `/bug-repro` was intended to write a failing test from a bug description, but `/tdd` already handles this when the user starts with a bug as their test case.

I also deliberately did not propose `/security-scan`, `/explain`, or `/debug` — those would either duplicate `/code-review` or be too generic to justify a command.

---

## 7. Recommended Priority

Updated ordering based on the consolidation decision.

Immediate (correctness and consolidation): Merge `python-review.md` into `code-review.md` using the dispatcher pattern from §3.6. Delete `python-review.md` after the merge. This simultaneously removes the broken `python-reviewer` agent reference and eliminates the duplication.

Short-term (quality of life): Add frontmatter (description, argument-hint, allowed-tools) to every remaining command. Add `$ARGUMENTS` support to `/test-coverage`, `/build-fix`, and the new `/code-review` (for optional file-path scoping). Finish the truncated `tdd-guide.md` agent file.

Medium-term (workflow): Add `/commit-prep` and `/pr-description` — they encode workflow steps already described in `CLAUDE.md`. Rename `refactor-clean` → `dead-code`. Optionally rename `test-coverage` → `coverage`.

Longer-term (optional): Add `/agent-prompt-review` if you're iterating heavily on LangChain prompts. Grow Step 4 (Frontend) of `/code-review` over time as you find patterns worth encoding. Subdirectory namespacing has been declined — see §5.

---

## 8. Approved Plan of Action

All decisions are now made. This section lists every concrete change that will be executed in order. Please review and confirm before I touch any files in `.claude/`.

### Phase 1 — Consolidation (single biggest change)

**Target file:** `.claude/commands/code-review.md` (rewritten), `.claude/commands/python-review.md` (deleted).

Rewrite `code-review.md` as the six-step dispatcher described in §3.6:

1. *Step 1 — Discover changes.* Run `git diff --name-only HEAD` plus `git ls-files --others --exclude-standard` (to cover untracked files, which today's command misses). Bucket files into backend (`.py`), frontend (`.jsx`/`.tsx`/`.js`/`.css`), and other.
2. *Step 2 — Cross-Cutting checks (always run).* Hardcoded credentials, missing input validation, insecure dependencies, CORS wildcards, TODO/FIXME hygiene, function/file/nesting size, missing tests for new code.
3. *Step 3 — Backend (Python) checks.* Run only if `.py` files changed. Carries over everything currently in `python-review.md`: ruff/mypy/bandit invocation, Beanie N+1 patterns, async purity in route handlers, Pydantic validation, mutable default arguments, LangChain prompt injection, bare except clauses. **Drops** the `./run_tests.sh --cov` line — coverage belongs to `/test-coverage`, and the review command should report gaps rather than re-run tooling.
4. *Step 4 — Frontend (React) checks.* Run only if `.jsx`/`.tsx` changed. Accessibility, React hook correctness (deps arrays, stale closures), Tailwind class misuse, unused components, console.log left in code, `dangerouslySetInnerHTML` XSS. Lighter than the backend section for now; can grow.
5. *Step 5 — Severity-tiered report.* Keep today's CRITICAL / HIGH / MEDIUM / LOW framing. Preserve the approval criteria table from today's `python-review.md` (Approve / Warning / Block).
6. *Step 6 — Recommendation.* Soften today's "Block commit if CRITICAL or HIGH issues found" to "**Recommend** blocking commit…" — honest about what Claude can actually do.

Add frontmatter: `description`, `argument-hint: [file-path]` (optional), `allowed-tools: Bash, Read, Grep, Glob`.

Then delete `python-review.md` from the repo.

### Phase 2 — Improvements to existing commands

**`build-fix.md`:** Add frontmatter. Add `$ARGUMENTS` support for `backend | frontend | lint | all` as `$1`. Fix the misclassification on line 11 — replace `./run_tests.sh` (a test runner) with a real build/typecheck command such as `ruff check` or `python -m compileall -q .` since the command is about build/compile errors, not test failures. Add guardrail: "Stop if a fix would require changing a test."

**`refactor-clean.md` → `dead-code.md`:** Rename. Add frontmatter. No content changes — the three-tier safety classification (SAFE / CAUTION / DANGER) stays.

**`tdd.md` — delete.** TDD becomes a global default via `CLAUDE.md` (see below) rather than an opt-in command. The `tdd-guide` agent stays, still invokable via the Task tool when deep TDD guidance is wanted.

**`CLAUDE.md` — update the TDD section.** Replace the current one-line `"2. **TDD** — write tests before implementation (use the tdd-guide agent if unsure)"` in the Development Workflow block with a stronger rule plus a carve-out list:

> **TDD is mandatory for all functional code changes** — new features, bug fixes, refactors, or any change to behaviour in `.py`, `.jsx`, or `.tsx` files. Write the failing test first, then the implementation.
>
> **TDD does not apply to:** documentation, configuration, **LangChain prompt text edits**, styling-only changes, dead code removal, dependency bumps, or file renames without behaviour change. For these, update relevant tests if the change breaks them, but do not invent new tests.
>
> **The `tdd-guide` agent is still available** as a specialist sub-agent for complex TDD sessions — invoke it directly when you want deep methodology guidance.

**`test-coverage.md` → `coverage.md`:** Rename. Add frontmatter. Add `$ARGUMENTS` support for an optional file path so `/coverage platform/routers/estimates.py` scopes to one module. Hand off generation of new tests to the global TDD flow (previously this section said "to `/tdd`", but since `/tdd` is being deleted, `/coverage` simply reports gaps and the user triggers a normal code change where TDD is now the default).

**`update-docs.md`:** Add frontmatter. Keep content — the `CLAUDE.md`/`GEMINI.md` boundary and the "single source of truth" rule are correct.

**`.claude/agents/tdd-guide.md`:** Finish the truncated file (currently ends mid-sentence at line 95). Complete the Frontend (React + Vite) patterns section. Add a "Definition of Done" checklist. Add `Glob` to the `tools` array on line 4 (test discovery often needs globbing).

### Phase 3 — New commands

**`/commit-prep`** — New file `.claude/commands/commit-prep.md`. Runs the pre-commit gauntlet: identifies changed files, runs related backend tests (`./run_tests.sh tests/test_<module>.py`), runs related frontend tests (`npm test -- <file>`), runs lint, surfaces anything failing. Drafts a commit message in your `<type>: <description>` format. Encodes step 4 of the CLAUDE.md Development Workflow.

**`/pr-description`** — New file `.claude/commands/pr-description.md`. Given the current branch, runs `git diff main...HEAD` and `git log main..HEAD`, drafts a PR description with Summary / Test Plan / Risk sections following the CLAUDE.md Git Workflow format.

**`/agent-prompt-review`** — New file `.claude/commands/agent-prompt-review.md`. Reviews `platform/agents/` and `platform/prompts/` for prompt injection risk, instruction clarity, token efficiency, and temperature/model appropriateness. Specifically called out because you ship LangChain agents in production.

### Phase 4 — Explicitly not doing

Not introducing inline `!bash` or `@file` prefixes (keeping prose style).
Not creating `/scaffold-router`, `/model-diff`, or `/bug-repro`.
Not adding a third custom security command (built-in `/security-review` covers the deep-audit need — see §3.7).
Not adopting subdirectory namespacing (`/review:code` etc.) — firm decision, all commands stay flat at the top level of `.claude/commands/`.

### Summary of file changes

| File | Action |
|------|--------|
| `.claude/commands/code-review.md` | Rewrite as dispatcher, add frontmatter, soften "block" wording, add untracked-file coverage |
| `.claude/commands/python-review.md` | **Delete** after content merged into `code-review.md` |
| `.claude/commands/build-fix.md` | Add frontmatter, `$ARGUMENTS`, fix misclassified test-runner line |
| `.claude/commands/refactor-clean.md` | **Rename** → `dead-code.md`, add frontmatter |
| `.claude/commands/tdd.md` | **Delete** — TDD becomes a global default via `CLAUDE.md` |
| `.claude/commands/test-coverage.md` | **Rename** → `coverage.md`, add frontmatter, add `$ARGUMENTS` |
| `.claude/commands/update-docs.md` | Add frontmatter |
| `.claude/agents/tdd-guide.md` | Finish truncated file, add `Glob` to tools. **Not deleted** — still callable as a sub-agent |
| `.claude/commands/commit-prep.md` | **New** |
| `.claude/commands/pr-description.md` | **New** |
| `.claude/commands/agent-prompt-review.md` | **New** |
| `CLAUDE.md` | **Update** — replace one-line TDD rule with stronger rule + carve-out list (see Phase 2) |

That's **12 files touched** (4 edits, 2 renames, 2 deletes, 3 new, 1 agent completion) including one change outside `.claude/` — the `CLAUDE.md` TDD section update.

### Confirmation needed

Please review the table above. If everything looks right, say "go" and I'll execute Phase 1 first (consolidation + `CLAUDE.md` TDD update, since they're both structural), then Phase 2 (remaining improvements including `/tdd` deletion and renames), then Phase 3 (new commands), stopping between phases to let you spot-check. If anything in the table should be changed or removed, let me know before I start.
