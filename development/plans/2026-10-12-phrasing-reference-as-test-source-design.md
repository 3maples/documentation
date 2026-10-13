# The phrasing reference as Maple's test source — design (2026-10-12)

**Status:** approved 2026-10-12 — Simon took every recommendation in §8. Phase 1 done 2026-10-12.
**Supersedes, once built:** the parity run's four-source design
(`plans/2026-10-02-maple-planner-shadow-design.md` §4.5, step 11) and the
parity half of follow-up #846.

## 1. Why

The planner became every company's Maple today (`MAPLE_PIPELINE=planner`,
`MAPLE_PLANNER_ONLY` on). The live suite that checks it was built to compare it
with today's pipeline before the switch — a **parity** run. Three of its four
sources record what today's pipeline *did*, not what Maple *should* do:

| Source | Cases | What it pins | Not already in the reference |
|---|---|---|---|
| Routing snapshot (`tests/maple_routing/snapshot_routing.json`) | 3,549 (1,216 phrases × 4 states) | Whatever today's rules routed each phrase to — their mistakes included | 854 phrases |
| CRUD coverage matrix (`tests/_maple_coverage_data.py`) | 206 | Curated, written as today's intent → agent | 147 |
| Design rows (`tests/maple_routing/expected.json`, routing layer) | 107 (69 phrases) | Curated design decisions | 57 |
| Phrasing reference (`maple-phrasing-reference.md`) | 1,059 of 1,331 rows | The human-curated truth | — |

Scoring the planner against the snapshot contradicts the rule that the planner
gives the right answer where today's Maple is wrong; once today's pipeline is
deleted the snapshot describes nothing at all. Meanwhile the one curated source,
the reference, is read by a forgiving regex parser that leaves 272 rows
unchecked, and 536 of its 993 checked supported rows name no expected
operation, so they only have to "not refuse".

**Goal:** one human-curated list of everything Maple supports, refuses and
doesn't yet do — the reference — that a live suite tests the planner against
and an offline test keeps honest.

**Not a goal:** removing the live suite. It is the only test where the real
model plans real messages; the offline tests pin the model off. A prompt,
schema or model change can only be caught there (the 2026-10-12 runs caught
three wrong writes no offline test saw).

## 2. Decisions

- **D1 — The reference is the source of truth for every single-turn
  phrasing.** The live suite reads its rows; nothing else feeds it phrasings.
- **D2 — Multi-turn behaviour stays in code, indexed from the reference.** The
  acceptance conversations (`tests/maple_conversations/corpus.py`, 284
  conversations, 9 marked `gap=`) seed a database and check each turn — more
  than a table row can say. A reference row that takes several steps links to
  the conversation that tests it; every conversation names the reference
  section it covers.
- **D3 — Rows state what the planner should do, in the planner's vocabulary.**
  Today's `intent → Agent` column becomes a **Plan** column: an op from
  `agents/planner/schema.py` (`list_estimates`, `resize_work_item`, …), a
  refusal with its `UnsupportedReason`, or a question asked back.
- **D4 — No row is silently unchecked.** The row format is strict, and a free
  offline test fails on any row it can't read. A row is either a checked
  phrasing, a link to a conversation that exists, or an explicit note.
- **D5 — Curated sources are folded in; the snapshot is mined, not imported.**
  The CRUD matrix and design rows become reference rows. The routing snapshot's
  854 missing phrases are reviewed and only the right ones are added, with the
  planner's answer — never today's — as the expectation.
- **D6 — Today's pipeline keeps its own tests until it is deleted.** The
  routing snapshot test, `command_grammar.py` and its tests, and the CRUD
  matrix test pin today's pipeline; they stop being planner sources now and go
  with today's pipeline when Simon orders it deleted (the standing decision).

## 3. The row format

Every table in §1–§11 uses three columns:

```
| Phrasing | Plan | Status |
|---|---|---|
| `how many estimates do I have?` | `list_estimates` | ✅ |
| `change the patio to 800 sq ft` [wi] | `resize_work_item` | ✅ |
| `delete all my contacts` | refuse `bulk_delete` | 🛑 |
| `update the task` | ask | ✅ |
| `make the patio bigger, then send it` | conversation `wi-resize-then-send` | ✅ |
| `schedule the mowing every two weeks` | refuse `recurring` | ⚠️ gap — #NNN |
```

- **Phrasing** — one or more whole phrasings in backticks, separated by ` / `.
  No ellipses, no arrows; prose goes in the Status cell after the marker.
  An optional **state** in brackets after the phrasings — `[est]`, `[wi]`,
  `[est_then_mat]`, `[<domain>_focus]` — names the starting context from
  `tests/maple_routing/states.py` / `tests/planner_parity/cases.py::FOCUS_STATES`.
  Today the state is guessed from the section number and pronouns; making it
  explicit removes the guess.
- **Plan** — exactly one of:
  - an op, optionally with the fields that are the point of the row, a
    nested field as a dotted path, a bare name for a flag:
    `` `list_estimates` filter.sold count ``,
    `` `list_estimates` filter.statuses=Draft,Sent ``, `` `metric` before_tax ``.
    A value has no spaces;
  - `refuse <reason>` (an `UnsupportedReason`; `refuse out_of_chat <capability>`);
  - `ask` — the planner's question (a clarify plan);
  - `answer` / `help` / `social` — no action;
  - `conversation <id>` — tested by that acceptance conversation (D2).
- **Status** — `✅` supported, `🛑` refused by design, `⚠️ gap` not done yet
  (with its follow-up number). Free text after the marker is kept.

The tier tags (`✅ rule`, `🤖 LLM`, `🤖 planner`) go: there is one pipeline in
production, and the tags described today's. The section-level "all ✅ rule"
default goes too — every row carries its own status.

Placeholders stay (`{EST}`, `{property}`, …), filled from the seeded world as
now; the five the parser doesn't know today (`{X}`, `{Y}`, `{old}`,
`{custom division}`, `{T0001}`) are renamed to known ones or added to the fill
table.

## 4. What happens to the 272 unreadable rows

From `scripts/phrasing_reference_rows.py` today:

| Why it can't be read | Rows | Becomes |
|---|---|---|
| Several steps (an arrow) | 84 | A `conversation <id>` row; a missing conversation is written (D2) |
| Needs a state it can't build | 59 | A `[state]` row where a state from `states.py` fits; otherwise a conversation |
| An ellipsis | 49 | Written out as whole phrasings |
| No backticked phrasing | 49 | A note (moved out of the table) or a real phrasing |
| An identifier, not a phrasing | 11 | A note |
| A placeholder it can't fill | 15 | Renamed or added to the fill table |
| A refusal that depends on role or status | 5 | A conversation (the policy check runs after the plan, against the database) |

The 2026-10-12 offline audit (`plans/2026-10-12-planner-reference-row-audit.md`)
already sorted these rows into COVERED / MODEL / GAP; it is the worklist.

## 5. The two tests

### 5.1 Offline, every run, free — `tests/test_phrasing_reference_rows.py`

The parser becomes strict and the test asserts:

- every table row in §1–§11 parses (phrasing, plan, status), and none is left
  unchecked;
- every op is one the planner's schema defines (`schema.INTENT_OF_OP`), every
  refusal reason an `UnsupportedReason`, every state a known state;
- every `conversation <id>` names a conversation in the corpus, and every
  conversation's `reference` section exists;
- no phrasing appears twice with different plans.

This is what keeps the reference a test source rather than a document that
drifts: an edit that breaks the format fails in the normal suite.

### 5.2 Live, on request — `tests/test_planner_live.py`

Replaces `test_planner_parity_live.py` and `test_planner_acceptance_live.py`
(`-m llm_e2e`, still run only when Simon asks — before a big push to `main`):

- **Rows:** every ✅ and 🛑 row with an op or a refusal, planned by the real
  model in its state; scored on the op (and named fields) exactly — no more
  "ran" rows that only had to not refuse. ⚠️ rows are run and reported, not
  scored: one that starts passing is news.
- **Conversations:** every acceptance conversation on the planner pipeline, as
  `test_planner_acceptance_live.py` runs them today, scored on reply fragments
  and `after` checks; with the company's task statuses in state (#846's
  "planned blind" item).
- **Explained differences** stay in `tests/planner_parity/explained.py` (moved
  to `tests/planner_live/explained.py`), each with its reason — never silenced.
- **Reports:** `tests/reports/planner_live.md` and `.json`, diffed against the
  last run as now.

The shadow-comparison half of the parity run (`test_conversations_parity`,
today vs planner per turn through `maple_compare`) is retired: there is no
"today" to compare with in production.

Cost: about 1,300 row calls plus about 540 conversation turns — roughly a
third of the parity run's ~5,700 calls, so well under its ~$2 and 30 minutes.

## 6. Phases

Each phase is its own commit, failing test first where code changes.

1. **Format and parser.** Write the strict parser and the offline test against
   a sample (TDD). Teach it both formats for one phase, so the reference can be
   migrated section by section with the test reporting what's left.
   *Done 2026-10-12:* `scripts/phrasing_reference_rows.py` reads both formats
   (`read`, `problems`, `Plan`, `Vocabulary`);
   `tests/planner_parity/cases.py::reference_vocabulary` builds the vocabulary
   from the planner's schema (nested fields as dotted paths), the routing and
   focus states and the conversation corpus; `reference_cases` scores a Plan
   row on its op and skips gaps and conversation rows. The offline test fails
   on any Plan-row problem and ratchets the old-format rows of §1–§11
   (`LEGACY_ROWS_LEFT = 983` — lower it as sections move; `python
   scripts/phrasing_reference_rows.py` reports them by section). Reading table
   headers properly also stopped 5 header rows being listed as unreadable
   phrasings (272 → 267). §1.3.2's free-form table, the one already headed
   `Phrasing | Plan | Status`, was renamed `Planned as` to stay old-format
   until phase 3 writes the conversations its state-dependent rows need.
2. **Bootstrap the Plan column.** For the 536 checked rows with no op, propose
   one from the last live run (`tests/reports/planner_parity.json`) where the
   planner's plan agreed; Simon or the session reviews each section's
   proposals before they're written. Rows where the planner differed are read
   by hand.
3. **Convert the 272 unreadable rows** (§4), writing the missing conversations.
4. **Fold in the curated sources.** The CRUD matrix's 147 and the design rows'
   57 missing phrases become rows in their sections.
5. **Mine the routing snapshot.** List its 854 missing phrases by section;
   review; add what's right with the planner's expected answer. Duplicates of
   an existing row (a reworded "list my contacts") are dropped, not added.
6. **Switch the live suite.** `test_planner_live.py` reads only the reference
   and the conversations; the old parity sources and the shadow comparison are
   removed from it. Its first run is #846's owed run of the 2026-10-11
   changes; diff it against the 2026-10-12 parity report.
   - **The package.** `git mv tests/planner_parity tests/planner_live`. In
     `cases.py`, delete the parity-only builders — `routing_snapshot_cases`,
     `expected_cases`, `crud_cases`, `all_corpus_cases` — and keep `Case`,
     `FOCUS_STATES`, `reference_rows` / `reference_cases` and
     `reference_vocabulary`; `run.py`, `score.py`, `report.py`, `explained.py`
     and `acceptance.py` carry over as the suite's machinery. Delete
     `test_planner_parity_live.py` and `test_planner_acceptance_live.py`, and
     move the harness tests' surviving cases to the new package's names.
   - **Scoring the whole row** (review 2026-10-12 #2, #10, #11). Carry a Plan
     row's named fields, its refusal reason and capability, and whether it
     asks onto `Case`, and compare each in `score.py` with the plan's action
     fields, `plan.unsupported.reason` / `.capability` and `plan.clarify`. Until
     then `ask` rows are not scored (phase 1 skips them) and fields and reasons
     are read but not compared.
7. **Docs.** Rewrite the reference's "How to read this doc", "How to add new
   use cases" and §12 (tests, how to run, the live report's numbers in place of
   the Tier 1 / Tier 2 matrix score). Update `CLAUDE.md`'s Maple sections
   (the parity run, the coverage matrix, the phrasing reference paragraph) and
   the saved memory about the parity run. Mark #846's parity items resolved.
8. **When today's pipeline is deleted** (Simon's order, separate): delete the
   routing snapshot test and corpus, `command_grammar.py`'s tests, the CRUD
   matrix and its gap report, and the shadow tooling the planner no longer
   uses.

## 7. Risks

- **The Plan column takes real reading.** 536 rows need an op, and a wrong op
  written in becomes a wrong spec. Mitigation: proposals come from the
  planner's own agreed plans, reviewed by section; anything it differed on is
  read by hand.
- **Exact op scoring is stricter.** Rows that "ran" before may now flag. That
  is the point, but the first run will have more to read; budget for it.
- **The reference gets longer.** Folding in ~250 rows and mining the snapshot
  adds to a 2,846-line file. The "Recent changes" block at the top (~280 lines
  of dated prose, kept despite the changelog having its own file) can move to
  `maple-phrasing-changelog.md` to compensate — see Q4.
- **Today's pipeline drifts untested against the reference.** Accepted: it is
  not in production, and its own tests stay until it is deleted (D6).

## 8. Decisions taken (Simon, 2026-10-12)

Each question was answered with the recommendation:

- **Q1 — Tier tags:** dropped now. Rows carry ✅ / 🛑 / ⚠️ only (§3).
- **Q2 — Multi-step rows:** linked to acceptance conversations, not a step
  syntax in the reference — conversations check what was written (D2, §4).
- **Q3 — Snapshot mining:** reviewed section by section, stopping a section
  early once it stops yielding phrasings the reference lacks (phase 5).
- **Q4 — "Recent changes" block:** moved to `maple-phrasing-changelog.md` in
  phase 7; the reference is the spec, not the history.
- **Q5 — Scoring:** the op always; the fields a row names (a status set,
  `before_tax`, a window) only where it names them (§3, §5.2).
