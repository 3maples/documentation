# Work-item summaries as a standalone corpus

**Status:** IMPLEMENTED 2026-09-21 (#557). Written 2026-09-20 after Simon ruled
on the question during a `/code-review`; the three open decisions were settled
the same day and are marked **DECIDED** below.

All four decided sections shipped. Two things this plan said, which the
implementation could not close:

- **§3's side-by-side** on a few real scopes before shipping did NOT happen. It
  needs live generation against real company data, which no test substitutes
  for. Prices that were copied verbatim from a past job are now re-researched;
  that is the intended change, but nobody has looked at the result yet.
- **§4's conclusion was right; its reasoning was not, and the gap cost a
  round trip.** It removed `job_item_id` because `_reuse_past_work_item` was
  "its only reader", overlooking `_find_existing_summary`, the upsert probe.
  With the field gone the probe went positional, and deleting a work item from
  an indexed estimate then overwrote its summary and duplicated the survivor
  (**#563**).

  The first fix proposed was to restore the field for the probe. Simon rejected
  it: no reader needs a back-reference to the original work item, so a field
  carried for one writer is the wrong shape. The actual question was whether
  re-indexing should update rows at all — and it should not. `embed_won_estimate`
  is now **append-only**, probing by the summary TEXT and inserting only what it
  has not seen. No identity is needed on either path. §4's removal therefore
  stands, and the corpus is additive in the write path as well as the read path.
  Resolved 2026-09-21; the accepted cost is that an edit adds a row instead of
  replacing one.

**§6 (retention)** remains out of scope and is logged as **#562**. The now-vestigial
second key of the collection's compound index is logged as **#564**.

## The ruling

> The work item summary should not be linked back to the actual estimate. The
> purpose of the summary is to capture a collection of past work items as
> references for future estimates/work items. Hence, even if the original
> estimates were deleted, they should not affect the summaries. For LLMs, even
> if the new estimates are not matching exactly to the past work items, they
> should be able to infer from historical data to produce the new estimate.

A summary is a record of work this company actually did. Once captured it is
history, and history does not stop having happened because the paperwork was
deleted.

## Where the code disagrees today

Three of five paths make a summary's fate depend on a live `Estimate` document.

| Path | Where | What it does today |
|---|---|---|
| Status filter | `search_similar_work_items`, `$lookup` + `$match` on `HISTORY_ELIGIBLE_STATUSES` | A summary is invisible unless its estimate is *currently* Won / Scheduled / Completed. |
| Deleted estimate | the same `$lookup` | The join yields `[]`, so the row never matches again. **Deleting an estimate silently erases its work items from the corpus** — the code comment calls this "drops orphans", which is the reading this plan reverses. |
| Retraction | `delete_work_item_summaries`, on `leaves_history` | Won → Lost / On Hold deletes the rows outright. |
| Structural reuse | `_reuse_past_work_item` → `Estimate.get()` → read `job_items[…]` | Needs the estimate document to exist and to still contain the item. |
| Text context | step-3 research context, `assumption_defaults` | Reads `summary` only. **Already standalone.** |

`routers/estimates.py::delete_estimate` cascades notes but not summaries, so
after a delete the rows survive in the collection and are merely unreachable —
which means this change is mostly about *reading*, not about recovering data.

## What has to change

### 1. Stop joining to `estimates` on read

Drop the `$lookup` / `$match` pair from the aggregation. Eligibility becomes a
property of the row, captured when it was written, not a question asked of a
document that may no longer exist.

### 2. Retraction — **DECIDED: keep the summary, never retract**

Today, Won → Lost deletes the summaries, with a deliberate rationale on record:
work the customer did not buy must stop teaching Maple what a job costs. I
recommended keeping that. Simon decided the other way on 2026-09-20: the corpus
is purely additive, and a summary is kept whatever later happens to the estimate.

**Work:** unwire `delete_work_item_summaries` from `leaves_history` in
`routers/estimates.py`, and decide whether the function survives at all — the
only remaining caller would be a manual cleanup. `tests/test_history_eligibility.py`
pins the current behaviour and inverts with this.

**Consequence to accept knowingly:** an estimate that was Won and is later
marked Lost keeps teaching Maple. The mitigation, if this ever bites, is that a
summary is a reference among many rather than a price that gets copied — which
is exactly what §3 makes true.

### 3. Make reuse read the summary, not the estimate

`_reuse_past_work_item` copies materials, labours and activities out of the live
job item above a 0.85 match. That is the one consumer that cannot survive its
estimate being deleted. Two ways out:

**DECIDED: Option B.** Simon chose inference over copying on 2026-09-20.

- **Option A (not chosen) — snapshot the line items onto the summary.** Add a
  `line_items` field holding what `_project_past_line_items` already builds
  (names, quantities, prices, `cost` / `cost_rate`). Reuse then reads the row
  and never touches `Estimate`. Keeps today's behaviour, including the verbatim
  price copy and the full-confidence division override. Costs a schema field, a
  backfill for existing rows, and duplicated price data that no longer tracks
  the catalog.
- **Option B (chosen) — drop structural reuse entirely.** Delete
  `_reuse_past_work_item` and let every scope run research with the matching
  summaries as context, which is what the ruling's second sentence describes:
  the model infers from historical data rather than copying a row. Simpler, and
  it removes the only path that can quote a stale price verbatim. Costs an LLM
  call on scopes that currently short-circuit, and gives up the "a human
  reviewed this exact item" division signal.

This is a behaviour change to estimate generation, not a refactor: prices that
are currently copied verbatim from a past job will start being re-researched,
and the "a human reviewed this exact item" division signal disappears with the
reuse path that set it. A side-by-side on a few real scopes before this ships is
still worth the hour.

**Work:** delete `_reuse_past_work_item`, `_resolve_past_job_item`,
`_project_past_line_items`, `_WORK_ITEM_REUSE_SCORE_FLOOR` and the
`qualifying`/`best` block in `_step2_and_3_for_scope`, so every scope reaches
`_step3_research_for_scope` with `past_work_items` as context. Tests that pin
reuse — `test_line_item_cost_basis.py::test_reused_past_work_item_carries_both_cost_bases`,
the reuse cases in `test_estimate_division_classification.py`,
`test_scope_assumptions.py` and `test_history_recency.py` — either move to the
research path or go.

### 4. `job_item_id` — **DECIDED: remove it**

The field was added on 2026-09-20 for exactly one consumer — `_reuse_past_work_item`
resolving the right item — so Option B leaves it with no reader. Simon confirmed
on 2026-09-20 that it goes.

**Work:** remove `WorkItemSummary.job_item_id`, the id branch of
`_find_existing_summary` (the upsert probe returns to `(estimate_id,
job_item_index)`), the projection and result key in `search_similar_work_items`,
and `tests/test_work_item_identity.py`. Stored documents keep a harmless extra
key; no migration is needed, and none should be written to strip it.

Worth doing in the same change as §3, not before it: until reuse is gone, the
field is the only thing standing between a shifted index and another job's
prices.

### 5. Keep `estimate_id` as provenance

Nothing above requires dropping the field. It stays for debugging, auditing and
"where did this come from", and `delete_work_item_summaries` still uses it. The
rule is that no *read path* may require the referenced estimate to exist.

### 6. Retention

A corpus that never loses rows grows with the business forever, and every row
carries a 1536-float embedding. Today the status filter keeps the working set
small by accident. Once it is gone, nothing does. A retention or archival
policy (age, or per-company row cap) is not part of this change, but it becomes
a real question the first time a large customer's corpus outgrows the
`$vectorSearch` candidate window.

## Testing

- `search_similar_work_items` returns a row whose estimate has been **deleted**
  — the test that fails today.
- The same for an estimate moved to a non-eligible status, matching whichever
  way §2 is decided.
- A scope with a 0.99-scoring past match still reaches
  `_step3_research_for_scope`, and its `past_work_items` context contains that
  match — the replacement for reuse, and the test that would have failed under
  the old short-circuit.
- Existing coverage to keep in step: `tests/test_history_eligibility.py` pins
  today's join behaviour and will need rewriting against the decision in §2.
