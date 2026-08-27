# Task readable ids: Crockford Base32 → decimal (#504)

**Status:** COMPLETE · **Started/finished:** 2026-08-27
**Prerequisite:** #505 (done 2026-08-27) — every layer that reads a task id now
funnels through `task_code_in_text` / `task_codes_in_text`, so the body changes
in one place instead of five.

## Goal

`T4K7Q` → `T0042`. Tasks adopt the same `T` + decimal counter shape estimates
already use, so the id a user reads is the number they count.

## Decisions (taken 2026-08-27, recorded in followups #504)

| Question | Decision |
|---|---|
| Width | 4 digits as a **floor** — the formatter widens past 9,999 rather than failing |
| Existing ids | **Re-render, not renumber** — decode each Crockford body back to its sequence number and re-format it |
| Old-id grace period | **None** — `normalize_task_readable_id` stops accepting Crockford bodies at cutover |
| Portal | Gets `taskCode.ts`, mirroring `estimateCode.ts`, wired into task search |
| Crockford codec | Deleted once the migration has run |
| Index | No work — the unique `(company, readable_id)` partial index already exists |

## Why re-render beats renumber

`Company.next_task_seq` is already a sequential per-company counter, and
Crockford decodes straight back to it (`000A` → 10 → `T0010`). So each task's
new id is a pure function of its old one. That:

* **preserves gaps** — the counter counts allocations, not survivors, so a
  deleted task leaves a permanent hole. Renumbering compacts it and shifts every
  task after the first-ever deletion, by an amount the user cannot derive.
* **stays re-runnable** — the target id doesn't depend on position in an ordered
  set, so a half-finished run resumes cleanly.
* **never touches `next_task_seq`** — no racy counter reset against live creates.
  The estimate backfill needed block reservation precisely because it *was* a
  renumber; this isn't.

## What the decimal body deletes

Three pieces of machinery exist only because the body carries letters:

1. The **uppercase-only rule** on the bare form (lowercased, `tasks` is
   `T`+`ASKS`).
2. The **digit rule** added in #505 to make bare lowercase safe.
3. The **338,250-task edge** where an all-letter body still needs uppercase.

No English word contains a digit, so a decimal body is unambiguous in prose in
either case, and all three disappear. The **spoken form** (`T 0 0 4 2`) becomes
worth supporting for the first time — a Crockford body read aloud lands in the
B/D/E/G/P/T/V/Z speech-recognition confusion set no matter how good the parser
is, which is why #505 deliberately left it out.

## Phases

| # | Phase | Deliverable |
|---|---|---|
| 1 | Codec | `format_task_readable_id` / `normalize_task_readable_id` / `TASK_CODE_*` go decimal; `TASK_CODE_SPOKEN` added; uppercase + digit rules deleted |
| 2 | Readers | Consumers follow the shared constants (should be near-free after #505); test literals updated |
| 3 | Migration | `scripts/migrate_task_readable_ids_to_decimal.py` — decode → re-format, guarded on the value read, re-runnable |
| 4 | Portal | `portal/src/lib/taskCode.ts` + search wiring + tests |
| 5 | Cleanup | Delete `encode_crockford_base32` / `decode_crockford_base32` once the migration is in |
| 6 | Docs | Phrasing reference, CLAUDE.md if needed, close #504 |

All six phases are done. Outstanding operational step: run
`python scripts/migrate_task_readable_ids_to_decimal.py --apply` **once per
environment** (Dev, then production) before the decimal codec reaches it.

## Risks

* **Users holding an old id.** Accepted — no grace period. The re-render keeps
  the ordinal, so `T000A` → `T0010` is task ten either way.
* **The migration must run before the new codec ships**, or a task created in
  the window gets a decimal id while its neighbours are still Crockford. Both
  forms are 4-7 chars of `[0-9A-Z]`, so the unique index is satisfied either
  way and the sequence is untouched — the window is cosmetic, not corrupting.
* **`T0042` is valid in both schemes**, which is why most test literals need no
  change and why the migration's "already decimal" selector is safe.
