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

The arc is **plan → iterate per phase → push**. Steps are enforced today by
**discipline and the AI assistant's instructions** plus the pre-push hook (§7.1)
— not by CI (see §7 for why that matters). Commits accumulate locally across
phases; the push (and its full gate run) happens once, when you decide.

### 2.1 Plan
- **Generate the plan; if the work is large, break it into multiple phases.**
- For multi-step work, write a plan file in
  `documentation/development/plans/` (named `YYYY-MM-DD-short-topic.md`) and add
  a row to that folder's `README.md` index. Plans capture context, approach,
  status, and follow-ups — they are not auto-created changelogs.
- **Manually review the plan and adjust** before touching code.

### 2.2 Implement & verify — the per-phase loop
Work one phase at a time. Repeat this loop for each phase:

1. **Implement (TDD).** Write the failing test *first*, then the minimal code to
   pass it. TDD is mandatory for functional changes in `.py`/`.jsx`/`.tsx`; it
   does **not** apply to docs, config, prompt-text, styling-only, dead-code
   removal, dep bumps, or pure renames (see the TDD Policy in `CLAUDE.md`).
   Match established patterns (Beanie ODM, FastAPI DI, React hooks, the
   `agents/text_utils.py` helpers over inline regex); US spellings throughout.
   Run only **scoped** gates on touched files for fast feedback
   (`./run_mypy.sh <subtree>`, `./run_ruff.sh <subtree>`, the related test
   file) — **not** the full project (§3.1). Self-review the diff for
   `async`/`await`, bounds, N+1 queries, mutable shared state, and unhandled
   exceptions; fix any pre-existing errors you surface and report them.
2. **Manual test.** Once the phase's implementation is complete, run the app and
   exercise the change end-to-end.
3. **Fix any issues** that manual testing surfaces.
4. **`/code-review`** once it works as expected (`/code-review ultra` for larger
   work). It reviews logic, security, and quality — it does **not** run ruff or
   mypy (the pre-push hook does); it may run `bandit`. It produces a **numbered**
   findings list (`#N [SEVERITY] file:line — title`) and writes them to a ledger;
   it does **not** decide what to fix.
5. **You decide which findings to fix now** and run
   `/fix-issues <numbers | all | none>` (e.g. `/fix-issues 1, 2, 5`). It applies
   the fixes you chose and **auto-logs every unselected finding** to
   `code-review-followups.md` — nothing is silently dropped. The fix-vs-defer
   call is always explicitly yours, not the reviewer's.
6. **Manual test again** if `/fix-issues` applied any fixes.
7. **Commit the phase.** Use `commit-prep` to draft the `<type>: <description>`
   message (it doesn't re-run platform/portal gates — the hook does; it runs the
   `website/` build + tests only). Commit needs fresh explicit approval; never
   `--amend` without checking `HEAD` first (main moves mid-session).
8. **Decide: push now, or continue to the next phase.** Commits accumulate
   locally until you push.

### 2.3 Push — pre-push tasks, then `main`
When all phases are done (or you decide to push mid-way):

- **The pre-push hook runs automatically and aborts the push on any failure**
  (§3.1, §7.1) — `platform`: **ruff + mypy** (fast, no DB); `portal`: lint +
  typecheck + tests. The platform **full pytest suite is not in the hook** (too
  slow + needs the Dev MongoDB) — run it separately (`./run_tests.sh`) when you
  want full-suite confidence; it is not gated at push.
- On green, **push to `main`**. Push needs its own fresh explicit approval,
  separate from commit — never chained off a prior "proceed with X". Don't
  auto-pivot to a feature branch if a push is blocked; ask first.
- Changelog entries (`documentation/changelog/`, non-technical, version-
  incremented) are written **only when explicitly asked**.

### 2.4 Promote to production (`/release`)
Promotion is a **separate, deliberate** event — not every push. Production ships
by fast-forwarding a repo's `release` branch to `main`, done via the `/release`
command:

- `/release portal` · `/release platform` · `/release website` · `/release app`
  (`app` = platform + portal, promoted atomically — if either fails its gate,
  neither is promoted).
- `/release` runs the **full production gate first** — `platform`: ruff + mypy +
  the **full pytest suite** (vs the Dev MongoDB); `portal`: lint + typecheck +
  tests; `website`: build + widget tests — then fast-forwards `release` to `main`
  and pushes it. This is where the full test suite runs (§3.1).
- **Fast-forward only**; if `release` has diverged it aborts (never force-push).
- **Pushing `release` triggers the production deploy** (website → GitHub Actions,
  platform → Render, portal → Firebase). So `/release` ships to prod, and per the
  hardened rule it runs **only when the user explicitly invokes it** — never
  automatically, never inferred, never chained. (Typing `/release <target>` *is*
  that explicit instruction.)

---

## 3. Quality gates

These are the hard gates. The standards never relax; what's optimized is **how
many times each gate runs** — see §3.1.

| Gate | Command | Standard | Gated at push? |
|---|---|---|---|
| Lint (backend) | `./run_ruff.sh` (`--fix` for safe fixes) | **Zero errors** (since 2026-06-04) | **Yes** — platform hook |
| Type-check (backend) | `./run_mypy.sh` | **Zero errors** (since 2026-05-22) | **Yes** — platform hook |
| Tests (backend) | `./run_tests.sh` (scoped `tests/test_<module>.py` during impl) | All pass | No — runs separately vs Dev MongoDB (§4) |
| Lint (frontend) | `npm run lint` | Clean | **Yes** — portal hook |
| Type-check (frontend) | `npm run typecheck` | Clean | **Yes** — portal hook |
| Tests (frontend) | `npm test` (scoped `-- <file>` during impl) | All pass | **Yes** — portal hook (~15s, no DB) |

Rules:
- mypy and ruff are gates, not suggestions. New errors are fixed in the same
  change. The recurring playbooks (assert-narrowing for Beanie `.id`,
  `Dict[str, Any]` annotations, `# type: ignore[code]` with justification, the
  ruff re-export-hub `__all__` caveat, B904 `raise ... from`) live in
  `CLAUDE.md` and `code-review-followups.md` #3 / #323.
- Configs are pinned (`mypy.ini`, `ruff.toml`) — change the config file, never
  pass ad-hoc flags, so every session shares one baseline.

### 3.1 Where each gate runs — run once, not four times

A change passes through implementation → manual test → `/code-review` →
`/fix-issues` → `/commit-prep` → commit → push. To avoid running the same gate at
every step, each gate runs at exactly one authoritative point, with only
*scoped* checks before it:

| Step | ruff | mypy | tests | Notes |
|---|---|---|---|---|
| Implementation | **scoped** | **scoped** | **related** | Fast feedback on touched files only — not the gate |
| `/code-review` | — | — | — | Logic/security/quality only (may run `bandit`); reports numbered findings, fixes nothing |
| `/fix-issues` | **scoped** | **scoped** | **related** | Only on the files its fixes touched; auto-logs unselected findings to follow-ups |
| `/commit-prep` | — | — | — | Changed-file detection + message draft; runs `website/` build/tests only (no hook there) |
| **Pre-push hook** | **full** | **full** | **portal only** | The push gate (§7.1). Platform: ruff + mypy. Portal: lint + typecheck + tests (~15s, no DB). Aborts the push on failure. |
| `/release` (production gate) | **full** | **full** | **full** | The full suite's home: ruff + mypy + full pytest (`platform`, vs Dev MongoDB) / lint + typecheck + tests (`portal`) / build + tests (`website`) before fast-forwarding `release` to `main`. Runs only when you invoke `/release` (§2.4). |

So ruff and mypy run **once at full scope** in the pre-push hook; before that
they're scoped, so they aren't re-run redundantly. The platform **test suite is
deliberately out of the hook** — it's ~20 min and needs the Dev MongoDB, too
heavy for a per-push gate — so it's a separate on-demand run. The trade-off: a
backend regression that the scoped/related tests missed isn't caught at push;
it's caught by the **full suite that `/release` runs before promoting to
production** (§2.4) — the natural home for the slow, DB-dependent suite. Lint
and type errors *are* still gated at every push, and nothing reaches `main`
without passing them. Net: two tiers — fast gate on every push (hook), full
gate before prod (`/release`).

`website/` and `documentation/` have **no** pre-push hook: `website/`'s build +
widget tests run in `/commit-prep`; `documentation/` has no gates.

---

## 4. Testing strategy

- Backend: pytest + FastAPI `TestClient`, fixtures in `tests/conftest.py`,
  always inside the activated venv (`run_tests.sh` handles this).
- **Backend test database: the Dev MongoDB cluster.** The connection URL lives in
  `.env.local` (which `config.py` loads with precedence over `.env`); no local
  container needed. Running the full suite requires the machine's IP in the Atlas
  allowlist. **Because the suite shares the Dev cluster, every test must be
  self-sufficient — set up the data it needs and clean up everything it creates.**
  Never depend on pre-existing data; never leave residue. (This is also why the
  full suite is out-of-band, not in the pre-push hook — see §3.1.)
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

> **Status (updated 2026-06-14):** §7.1, §7.3, §7.4, §7.6, and §7.7 are done —
> the local pre-push hook (§7.1) is built and armed in `platform/` and
> `portal/`, plus the knowledge decision guide (§6.2), the archived closed-items
> backlog, standardized plan filenames, and the §8 checklist. The platform hook
> was **revised 2026-06-14** to ruff + mypy only after a real push showed the
> full suite is ~20 min + Dev-MongoDB-dependent (§7.1). §7.2 (CI backstop) was
> evaluated and **deliberately not built**. Remaining open items — §7.5
> (coverage) and §7.8 (security-review cadence).

### 7.1 Local pre-push hook (the chosen gate) — ✅ DONE 2026-06-13
Tests / mypy / ruff used to be enforced only by remembering to run them — a
single tired session or hand-off could ship a regression.

The team runs **trunk-based**: developers push directly to `main` and
fast-forward `main → release`; there is no PR-gating step (and we don't want
one). For a small team, the correct enforcement point is a **local pre-push git
hook** on each developer's machine — it runs the fast gates and aborts the push
if anything fails, so broken code never reaches the shared `main`.

**Implemented:** a committed, dependency-free `pre-push` script lives in each
repo and is wired up with `core.hooksPath` (chosen over `lefthook`/`pre-commit`
to avoid adding a tool — consistent with the project's conservative dependency
stance):
- `platform/.githooks/pre-push` → `./run_ruff.sh` → `./run_mypy.sh`.
- `portal/.githooks/pre-push` → `npm run lint` → `npm run typecheck` → `npm test`.

**Why the platform test suite is NOT in the hook (revised 2026-06-14):** the
first real push attempt showed the full backend suite takes ~20 min and needs
the Dev MongoDB — far too heavy for a gate that fires on every push in a
frequent direct-to-`main` flow. So the platform hook runs only the fast,
DB-free gates (ruff + mypy); the full suite is an on-demand run against the Dev
cluster (§4). Portal's suite stays in its hook because it's ~15s with no
external dependency.

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

This is the canonical checklist, mirroring the §2 lifecycle. The full gate run
is the pre-push hook's job (run once at push), so the per-phase boxes use only
**scoped** checks.

**Per phase (the §2.2 loop):**
- [ ] Plan written/reviewed (if multi-step); broken into phases if large
- [ ] Failing test written first, now passing (TDD)
- [ ] Scoped `./run_mypy.sh <subtree>` + `./run_ruff.sh <subtree>` + related
      tests green on the touched files (`platform/`); for `portal/`, the scoped
      `npm test -- <file>`
- [ ] Self-review done (async, bounds, N+1, exceptions); pre-existing errors
      surfaced this session fixed + reported
- [ ] Manual testing passed
- [ ] `/code-review` run (produces numbered findings + ledger)
- [ ] `/fix-issues <numbers | all | none>` run — you chose what to fix; the rest
      auto-logged to `code-review-followups.md`
- [ ] Re-tested manually if `/fix-issues` applied fixes
- [ ] Docs synced in the same change (CLAUDE.md / maple-phrasing-reference / etc.)
- [ ] Phase committed via `commit-prep` draft (`<type>: <description>`), with
      fresh explicit approval

**Before push (once — after the last phase, or when you decide to push):**
- [ ] Pre-push hook green — ruff + mypy (`platform`) / lint + typecheck + tests (`portal`)
- [ ] Full backend suite (`./run_tests.sh` vs Dev MongoDB) run on demand if the
      change warrants full-suite confidence — it is **not** gated by the hook
- [ ] Fresh explicit approval to push to `main` (separate from commit approval)
- [ ] Changelog entry only if explicitly requested
- [ ] `main → release` promotion only on explicit instruction
