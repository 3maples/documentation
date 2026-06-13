# Development Process

_Last updated: 2026-06-13_

This document is the canonical, human-readable description of how work flows
through the 3maples project — from idea to merged code. It complements the
machine-facing rules in the root `CLAUDE.md` (which an AI assistant reads on
every session) by explaining the *why* and the *shape* of the process, and by
calling out where the process can be improved.

> **Two audiences.** `CLAUDE.md` tells the AI assistant exactly what to do.
> This file tells a human (or a new contributor) what the system looks like as
> a whole, and is the place to revise the process itself. When the process
> changes, update both.

---

## 1. Repository layout

The working directory is **not** a single git repo. It is a workspace holding
four independent repositories plus AI tooling:

| Path | Repo | Contents |
|---|---|---|
| `platform/` | `3maples/platform` | FastAPI backend (estimates, agents, AI) |
| `portal/` | `3maples/portal` | React 18 + Vite frontend |
| `website/` | `3maples/website` | Marketing site (auto-deploys via GitHub Actions) |
| `documentation/` | `3maples/documentation` | Plans, changelog, design, dev process (this file) |
| `.claude/`, `.remember/`, `.agents/` | — | AI memory, session handoff, agent config (not versioned product code) |

Consequences worth remembering:
- A change that spans backend + frontend touches **two repos** and needs two
  commits / two pushes.
- Each repo has its own git history, author config (`3maples <admin@3maples.ai>`),
  and remote.
- Plans and process docs live in `documentation/`, intentionally versioned
  alongside — but separate from — the code they describe.

---

## 2. The development lifecycle

Every functional change follows the same arc. The steps are enforced today by
**discipline and the AI assistant's instructions**, not by automation (see
§7 for why that matters).

### 2.1 Plan first
- Outline phases, dependencies, and risks before touching code.
- For multi-step work, write a plan file in
  `documentation/development/plans/`, add a row to that folder's `README.md`
  index, and prefer a human-readable name (`auth-screens-overhaul.md`) over the
  random plan-mode slugs (`binary-pondering-seal.md`).
- Plans are not auto-created changelogs — they capture context, approach,
  status, and follow-ups.

### 2.2 Write the failing test (TDD)
- **TDD is mandatory for all functional code changes** — new features, bug
  fixes, refactors, anything that changes behavior in `.py`, `.jsx`, or `.tsx`.
- Write the failing test *first*, then the minimal implementation.
- TDD does **not** apply to docs, config, prompt-text edits, styling-only
  changes, dead-code removal, dependency bumps, or pure renames. For those,
  only update tests the change breaks.
- The `tdd-guide` / `superpowers:test-driven-development` skill is available
  for complex test-scaffolding sessions.

### 2.3 Implement
- Minimal code to make the test pass.
- Match established patterns: Beanie ODM, FastAPI dependency injection, React
  hooks, the Maple text-utility helpers (`agents/text_utils.py`) instead of
  inline regex.
- US spellings everywhere (labor, color, behavior).

### 2.4 Self-review
- Re-read the diff for `async`/`await` correctness, array/dict bounds, N+1
  queries, mutable shared state, and unhandled exceptions.
- Fix any pre-existing tsc/lint/test errors surfaced along the way and report
  them alongside the main task — don't leave a gate dirtier than you found it.

### 2.5 Run the quality gates (see §3)
- Related tests, mypy, ruff for backend; related tests + lint for frontend.

### 2.6 Code review
- Use the `code-review` skill (dispatcher: backend Python rules + frontend
  React rules for the file types that actually changed), or `/code-review ultra`
  for a deeper multi-agent cloud review of the branch/PR.
- `security-review` is available for security-sensitive surfaces.
- HIGH/MEDIUM findings that aren't fixed immediately go into
  `code-review-followups.md` as a punch-list item.

### 2.7 Commit & push (explicit approval each time)
- The flow is **trunk-based**: developers push directly to `main` and
  fast-forward `main → release` to promote. There is no PR-gating step, so
  **the §3 gates must pass locally before every push** — that responsibility
  sits with each developer (and, once built, the shared pre-push hook in §7.1
  enforces it automatically and aborts a failing push).
- **Promoting `main → release` happens only on explicit instruction.** That
  fast-forward ships to production, so it is never automatic, never inferred
  from a prior approval, and never chained off a `main` push — it is always its
  own standalone, explicit go-ahead.
- Use `commit-prep` to gather changed files across repos, run related tests +
  lint, and draft a `<type>: <description>` message.
- **Commit and push each require fresh explicit approval** — never chained off
  a prior "proceed with X". Same for **branch creation**: don't auto-pivot to a
  feature branch when a main push is blocked; ask first.
- Never `--amend` without checking `HEAD` first (main moves mid-session).
- Changelog entries (`documentation/changelog/`, non-technical, version-
  incremented) are written **only when explicitly asked**.

---

## 3. Quality gates

These are the hard gates for `platform/`. They are currently **local and
manual** — run before considering work complete.

| Gate | Command | Standard |
|---|---|---|
| Tests (backend) | `./run_tests.sh tests/test_<module>.py` | Related tests pass |
| Type-check | `./run_mypy.sh` (scope, then full before commit) | **Zero errors** (since 2026-05-22) |
| Lint | `./run_ruff.sh` (full project; `--fix` for safe fixes) | **Zero errors** (since 2026-06-04) |
| Tests (frontend) | `npm test -- <file>` | Related tests pass |
| Lint (frontend) | `npm run lint` | Clean |

Rules:
- **Run only the tests related to your change.** The full suite is triggered
  **manually by the user**, not automatically.
- mypy and ruff are gates, not suggestions. New errors are fixed in the same
  change. The recurring playbooks (assert-narrowing for Beanie `.id`,
  `Dict[str, Any]` annotations, `# type: ignore[code]` with justification, the
  ruff re-export-hub `__all__` caveat, B904 `raise ... from`) live in
  `CLAUDE.md` and `code-review-followups.md` #3 / #323.
- Configs are pinned (`mypy.ini`, `ruff.toml`) — change the config file, never
  pass ad-hoc flags, so every session shares one baseline.

---

## 4. Testing strategy

- Backend: pytest + FastAPI `TestClient`, fixtures in `tests/conftest.py`,
  always inside the activated venv (`run_tests.sh` handles this).
- Frontend: `npm test`, component behavior + interactions + API integration.
- Maple has a dedicated coverage matrix (`test_maple_crud_coverage.py`, 117
  phrasings) with a two-tier model: Tier 1 rules-only (default, free), Tier 2
  live LLM (opt-in, costs ~$0.05). The auto-generated gap report
  (`tests/reports/maple_crud_gap_report.md`) is the runtime truth;
  `maple-phrasing-reference.md` is the curated human truth — **keep them in
  sync in the same change** that touches a phrasing.

---

## 5. AI agent / Maple conventions

(Summarized here because they shape day-to-day changes; `CLAUDE.md` is the
detailed source.)

- All agents use LangChain `ChatOpenAI`, **temperature 0**, async `ainvoke`,
  singleton per router. Models are configured in `config.py`
  (`architect` / `researcher` / `worker`), overridable via env.
- Maple is the orchestrator brand; four CRUD domains (Property, Contact,
  Material, People=labour) plus Estimates.
- Policy guards are centralized in `agents/text_utils.py` — bulk-delete refusal,
  equipment refusal, count-query detection. Reuse the helpers; don't re-inline.
- Any-language support via the translation sandwich (`services/translation.py`):
  inbound fails **closed**, outbound fails **open**, persisted history stays
  English.

---

## 6. Knowledge & memory systems

Context is spread across several stores. They overlap, which is powerful but
easy to misuse — the same fact ending up in three places goes stale in two of
them. This section is the **decision guide**: it defines what each store is for
and, below, exactly where a given piece of information belongs.

### 6.1 The stores

| Store | Lifetime | Versioned? | Owner | Purpose |
|---|---|---|---|---|
| `CLAUDE.md` (per repo) | Permanent | Yes (in repo) | Whole team | Hard rules the AI must follow on every session |
| `documentation/` | Permanent | Yes (docs repo) | Whole team | Plans, changelog, design, this process doc — durable shared knowledge |
| `.claude/.../memory/` (auto-memory) | Permanent | No (local) | This machine's AI | Durable facts/preferences not derivable from code; indexed by `MEMORY.md` |
| `.remember/` | Rolling (now → today → recent → archive) | No (local) | Session continuity | "What happened when" handoff log between sessions |

### 6.2 Where does X belong? (decision guide)

| If the information is… | Put it in… | Not in… |
|---|---|---|
| A rule every contributor/AI must obey ("run mypy before done") | `CLAUDE.md` | memory (it's team-wide, must be versioned) |
| How the process works as a whole | this `development-process.md` | `CLAUDE.md` (which is rules, not narrative) |
| The plan/approach for a specific piece of work | `documentation/development/plans/` | `.remember/` (plans must survive + be shareable) |
| A user-facing summary of shipped work | `documentation/changelog/` (only when asked) | memory or `.remember/` |
| A durable preference or non-obvious fact about *this user/project* ("commits authored as 3maples", "root isn't a git repo") | auto-memory (`memory/` + `MEMORY.md` line) | `.remember/` (which rolls off) |
| What I did this session, for next-session pickup | `.remember/` | auto-memory (not a durable fact) or changelog |
| A fact already recorded in code, git history, or `CLAUDE.md` | nowhere — don't duplicate it | memory (redundant, goes stale) |

### 6.3 Anti-duplication rules

- **One home per fact.** If it's a rule, it lives in `CLAUDE.md`; if it's
  durable user/project context, in auto-memory; if it's session continuity, in
  `.remember/`. Don't copy across stores — link instead (`[[name]]` in memory).
- **Changelog vs. `.remember/recent.md`** overlap is the most common trap: the
  changelog is the *curated, user-facing* record (written only when asked);
  `.remember/recent.md` is the *raw, internal* session log. Keep the narrative
  detail in `.remember/`, not the changelog.
- Run the `consolidate-memory` skill periodically to merge duplicate memories,
  fix stale facts, and prune the `MEMORY.md` index.

---

## 7. Review: opportunities for improvement

The process is mature and well-documented. The biggest weaknesses are all about
**enforcement living in human/AI discipline rather than automation**, and about
**knowledge sprawl**. Prioritized:

> **Status (2026-06-13):** §7.1, §7.3, §7.4, §7.6, and §7.7 are done — the
> local pre-push hook (§7.1) is built and armed in `platform/` and `portal/`,
> plus the knowledge decision guide (§6.2), the archived closed-items backlog,
> standardized plan filenames, and the §8 checklist. §7.2 (CI backstop) was
> evaluated and **deliberately not built** for the current trunk-based flow.
> Remaining open items — §7.5 (coverage) and §7.8 (security-review cadence).

### 7.1 Local pre-push hook (the chosen gate) — ✅ DONE 2026-06-13
Tests / mypy / ruff used to be enforced only by remembering to run them — a
single tired session or hand-off could ship a regression.

The team runs **trunk-based**: developers push directly to `main` and
fast-forward `main → release`; there is no PR-gating step (and we don't want
one). For a small team, the correct enforcement point is a **local pre-push git
hook** on each developer's machine — it runs the full §3 gate set and aborts the
push if anything fails, so broken code never reaches the shared `main`.

**Implemented:** a committed, dependency-free `pre-push` script lives in each
repo and is wired up with `core.hooksPath` (chosen over `lefthook`/`pre-commit`
to avoid adding a tool — consistent with the project's conservative dependency
stance):
- `platform/.githooks/pre-push` → `./run_ruff.sh` → `./run_mypy.sh` →
  `./run_tests.sh` (full suite pre-push catches the cross-module regressions the
  "related tests only" local loop misses — see §3).
- `portal/.githooks/pre-push` → `npm run lint` → `npm run typecheck` → `npm test`.

Any failing gate aborts the push; emergency bypass is `git push --no-verify`.
Because the hook is committed (not a hand-rolled `.git/hooks/` file) every
developer runs the identical gate — but `core.hooksPath` is per-clone local
config, so **each clone must activate it once**:

```bash
git -C platform config core.hooksPath .githooks
git -C portal   config core.hooksPath .githooks
```

This makes the §3 gates self-enforcing rather than discipline-dependent —
**without** adopting a PR workflow.

### 7.2 CI backstop — not needed now (revisit-if note)
A `push: [main]` GitHub Actions workflow was considered as a backstop to the
§7.1 hook. **Decision (2026-06-13): not building it.** Because the flow is
direct-to-`main`, CI can't *gate* a merge without forcing PRs — it could only
alarm *after* a bad commit is already on `main` (and possibly fast-forwarded
toward `release`), which the §7.1 pre-push hook prevents strictly earlier.

The only gap a hook can't cover is a **clean-environment** check (it passes on
my machine with my cached deps) and a hook that was **bypassed/never installed**.
For a small disciplined team that residual risk doesn't justify the cost (the
`platform/` suite would need a `mongo` service container plus workflow upkeep).

**Revisit if:** the team grows, or a bypassed/missing hook or an
environment-drift bug actually bites — then add the `push: [main]` workflow
(`mongo` service container; the default pytest run excludes
`llm_e2e`/`evaluation`, so no API keys/cost).

### 7.3 Consolidate the knowledge stores — ✅ DONE 2026-06-13
There are effectively four places context lives (`CLAUDE.md`, auto-memory,
`.remember/`, `documentation/`). The roles overlap — e.g. "what we did this
week" exists in both `.remember/recent.md` and the changelog.
**Addressed:** §6 is now a full "where does X belong?" decision guide (§6.2)
with explicit anti-duplication rules (§6.3), and points at the
`consolidate-memory` skill for periodic cleanup.

### 7.4 Tame `code-review-followups.md` — ✅ DONE 2026-06-13
It was the single source of truth for follow-ups but had grown to ~407 KB —
hard to navigate and expensive to load.
**Addressed:** the 106-item `## Closed` block (130 KB) was extracted into
[`code-review-followups-archive.md`](code-review-followups-archive.md);
numbering is preserved for cross-references and the live file now carries a
short pointer in its place. Live tracker is down to ~277 KB / 228 active items.
Repeat the archive pass for any future RESOLVED items that accumulate.

### 7.5 Make TDD and coverage observable
TDD is mandatory but unverifiable after the fact, and the `tdd-guide`'s "80%+
coverage" target isn't measured anywhere in the gate. Consider a coverage report
in CI (`./run_tests.sh --cov`) — not necessarily a hard gate, but a visible
trend so coverage can't silently erode.

### 7.6 Standardize plan filenames — ✅ DONE 2026-06-13
The plans `README.md` already flagged that random-word slugs are unscannable.
**Addressed:** the plans `README.md` now mandates `YYYY-MM-DD-short-topic.md`
for new plans and grandfathers the legacy slugs to age out.

### 7.7 Define "done" in one checklist — ✅ DONE 2026-06-13
The definition of done was spread across several `CLAUDE.md` sections (tests,
mypy, ruff, docs sync, changelog policy, approval rules).
**Addressed:** §8 is now the canonical, copy-pasteable pre-handoff checklist.

### 7.8 Clarify when security-review runs
`security-review` exists as a skill but has no defined trigger in the standard
flow. Decide a cadence — e.g. on any change touching auth, billing, file
storage, or external API surfaces — and write it into the lifecycle.

---

## 8. Definition of done

This is the canonical pre-handoff checklist. A functional change is not "done"
until every applicable box is checked. For a change in `platform/`:

- [ ] Plan written/updated (if multi-step) in `documentation/development/plans/`
- [ ] Failing test written first, now passing
- [ ] Related tests green (`./run_tests.sh tests/test_<module>.py`)
- [ ] `./run_mypy.sh` — zero errors
- [ ] `./run_ruff.sh` — zero errors
- [ ] Self-review done (async, bounds, N+1, exceptions)
- [ ] Pre-existing errors surfaced this session fixed + reported
- [ ] Docs synced in the same change (CLAUDE.md / maple-phrasing-reference / etc.)
- [ ] Code review run (`code-review`, or `/code-review ultra` for larger work)
- [ ] Commit message drafted via `commit-prep` (`<type>: <description>`)
- [ ] Explicit approval obtained before commit **and** before push
- [ ] Changelog entry only if explicitly requested

For `portal/`: substitute `npm test -- <file>` and `npm run lint`.
