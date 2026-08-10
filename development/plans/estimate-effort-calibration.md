# Estimate effort calibration — anchor generated hours to real production rates

Status: **IN PROGRESS — Phase 1 built 2026-08-10** (research prompt + rate→hours
conversion + history gate); Phases 2-4 pending
Created: 2026-08-09
Related: [per-work-item-assumed-sizes.md](per-work-item-assumed-sizes.md) — the
size that feeds `work_quantity` must be resolved per work item, or one wrong
size multiplies into every scope's hours

## Context

Generated estimate totals land materially below what the same job sells for. The
totals formula is correct, and the company's configured percentages (tax, profit
margin, overhead, markup, burden) are the company's own business inputs — not
ours to calibrate.

**The symptom is specific: the activities themselves are right, but their efforts
skew low.** This is not a scope or decomposition problem. Maple picks sensible
tasks and assigns too few hours to them. So the target is the hours per activity,
and a fix that changes which activities get generated is solving the wrong thing.

### The problem, precisely

Across all three estimate prompts, this is the *entire* specification for effort:

- `prompts/estimate_generation.py:299` — "Each activity must have a `name`, `role`, and `effort` (hours for one person)."
- `prompts/estimate_generation.py:364` — "Every quantity, price, and effort must be numeric and > 0."
- `prompts/estimate_research.py:69` — same structural restatement.

No production rates. No plausibility band. No post-generation check. The LLM
free-hands the hours off nothing, and it free-hands them low.

Materials, by contrast, are anchored to the company's real catalog, get a
coverage audit (rules 9a–9d), unit-mapping rules, and a researcher step that can
web-verify coverage and pricing. Effort gets none of it.

### What already exists

| Piece | Where | Relevance |
|---|---|---|
| `search_similar_work_items()` per-company vector search | `services/work_item_summary.py:115` | The retrieval a history tier would build on |
| `infer_area_from_history()` — median-of-samples with a floor | `agents/estimate/assumption_defaults.py:191` | The pattern to follow; does this for *size* today |
| `build_job_item_summary()` — writes `"- {name} ({role}): {effort} hrs"` | `services/work_item_summary.py:39` | Effort **is** already in the indexed prose |
| `embed_approved_estimate()` — indexes on SENT/APPROVED only | `services/work_item_summary.py:172` | Defines what "history" means — see below |
| `effort = size ÷ rate` | `portal/src/lib/effortCalculator.ts:21` | Frontend only; backend has no equivalent |

### History is won work — but still estimated hours, not recorded ones

`embed_won_estimate` indexes a work item once its estimate is locked in:
`HISTORY_ELIGIBLE_STATUSES` = Won, Scheduled, Completed. The gate previously
fired on Sent/Approved, which are both pre-win — a quote that had gone out, or
been internally signed off to go out, with nobody having accepted the price.
Tightening it means the corpus is now work the customer actually bought.

Two caveats remain:

- **It is still the estimated hours, not the hours the crew recorded.** A won
  estimate proves the customer accepted the price, not that the effort was
  right.
- **Existing summaries predate the tighter gate**, so the stored corpus still
  contains never-won quotes until it is cleaned.

Both argue for the hard tier-1 gate below, independent of the
wrong-activity-match concern.

## Design

Job history is consulted first but must clear a **high similarity bar**. Anything
short of a confident match goes to web research instead — a researched rate for
the right task beats a borrowed rate from the wrong one.

```
For each generated activity:

  1. Company job history ───────── search_similar_work_items(), gated on:
     (only on a close match)         • high similarity score, not merely the
                                       best available match
                                     • unit-family agreement
                                     • minimum sample count
                                   Implied rate = past effort ÷ past size,
                                   median across qualifying matches.
                                   Fails closed: below the bar → tier 2.

  2. Web research ──────────────── researcher agent looks up a published
     (the common path, and the      production rate for the task + unit.
      primary corrective lever)     Sanity-band validated. NOT persisted.

  3. Scale ─────────────────────── effort = job size ÷ rate
                                   size from the existing chain:
                                   user-stated → history → WORK_TYPE_DEFAULTS.

  Fallback: no rate from either tier → keep today's LLM-estimated effort.
```

Given the gating and the history-provenance problem above, **tier 2 is the
primary fix, not the fallback.** Most activities will reach it, at least until
post-fix estimates accumulate. The phases are ordered accordingly.

### The only output is a corrected `ActivityItem.effort`

Production rates are an internal calculation input and are **not surfaced to the
user**. Nothing new appears in the UI, no new fields are written, and
`effort_card_items` is left alone.

What the user sees is what they see today: the activity, its hours, and its
role's hourly rate from the People catalog. Money is still `effort × People
rate`, unchanged. This work only makes the hours right.

That keeps the blast radius small — the entire change is a better number in an
existing field — and removes any need for a display decision.

### No rate store — the feedback loop runs through job history

Researched rates are not persisted. They are used to compute hours for this
estimate and then discarded. The loop closes through tier 1: a good estimate
becomes history, and the next close match picks the effort up from work the
company actually approved.

Consequences, accepted:

- No unverified data becomes indistinguishable from the company's own.
- No provenance field, review surface, or revocation story needed.
- Web research re-runs until a company has close-matching history.

## Phases

TDD throughout — failing test first, per CLAUDE.md. Ordered so the primary
corrective lever lands first.

### Phase 1 — Web-researched production rates (the primary fix)

- Extend the researcher agent (`prompts/estimate_research.py`) to look up a
  production rate for each activity's task + unit.
- Sanity-band validation before acceptance: reject a rate outside a plausible
  range for its unit rather than trusting the model.
- Convert to hours: `effort = job size ÷ rate`, writing the result to
  `ActivityItem.effort`. Nothing else is written.
- Not persisted — used for this estimate, then discarded.

Tests: a researched rate replaces the LLM's effort; an out-of-band rate is
rejected and the LLM effort is kept; no rate document is created by a run;
`effort_card_items` is untouched.

**This phase alone should move the numbers.** Phases 2–3 refine it.

### Phase 2 — Make size discoverable in work-item history

Effort is already in the indexed prose (`"- Lay Pavers (Foreman): 16 hrs"`).
Size is not — it is recoverable only by parsing `job_item.description` with
`parse_job_size` (`agents/estimate/template_scaling.py:96`), which is fragile.
A rate needs both.

- Prefer a structured size on the summary over prose parsing where that is a
  small change; otherwise extend the parse and treat failures as "no sample".

Tests: a saved work item is retrievable with both effort and size; an
unparseable one is excluded rather than guessed at.

### Phase 3 — Tier 1: close-match history rates

- Add `infer_effort_rate_from_history` alongside `infer_area_from_history`,
  reusing the same retrieval and median aggregation.
- **Gate hard**: a similarity floor (not just "best match"), unit-family
  agreement, and a minimum sample count. Below any of them, fall through to the
  researched rate.
- The threshold is the whole safety property here and needs tuning against real
  data before this phase ships.
- All indexed history is eligible, including estimates predating this work.

Tests: a close match overrides the researched rate; a loose match does **not**
and falls through; below-threshold sample count falls through; unit-family
mismatch is rejected.

### Phase 4 — Observability

Internal only — no user-facing output.

- Log which tier anchored each activity (history / research / unanchored) and
  the rate used, so the similarity threshold and sanity bands can be tuned
  against real generations rather than guessed at.

## Risks

| Risk | Mitigation |
|---|---|
| **History re-teaches the low bias.** Past estimates came from the under-estimating generator, so anchoring to them imports the bug as "company data". | Reduced by restricting the corpus to won work. Otherwise accepted knowingly — no cutoff date. Mitigated by phase ordering (research lands first and is the common path), by the hard tier-1 gate, and by median-over-samples rather than last-value. Phase 4 logging will show whether it bites. |
| **A stale summary survives a status change.** Indexing is transition-triggered, and the state machine allows `Won → Lost` / `Won → On Hold`. | Closed three ways: `leaves_history` deletes on exit; `search_similar_work_items` filters on the estimate's *current* status so a missed path can never surface one; and the Dev corpus was cleaned (14 of 27 removed, all pre-win). |
| **History matches the wrong past job.** A patio anchored to a mulch job produces confidently wrong hours — worse than today's honest guess. | Similarity floor, unit-family agreement, sample-count floor. Fails closed to research. Log every anchor. |
| **Researched rates are unverified.** | Never persisted, so a bad one is confined to the estimate that used it. Sanity-band validation catches obvious errors. |
| **Research adds latency and cost** to every generation, since it is now the common path rather than a fallback. | Measure before and after. Batch rate lookups per estimate rather than per activity where possible. |
| **Size parsed from prose is fragile.** | Phase 3 addresses directly. A failed parse is "no sample", never a guess. |
| **Count-based work has no rate** — "install one catch basin" is not size-scalable. | Out of scope. Keeps LLM-estimated effort. |
| **Seeded template data is incomplete** — "Paver Patio Install" has effort `0` on all four activities. | Independent data bug. Worth fixing regardless; this plan does not depend on it. |

## Out of scope

- **`RateCard` / the rate-card system.** Not consulted by this work. The
  company-configured rate cards, their seeded defaults, and the
  `ActivityItem.effort_rate_card_id` / `effort_card_items` fields are left
  exactly as they are. Decided deliberately.
- **Any user-facing change.** Production rates stay internal; the only thing
  that changes is the value in `ActivityItem.effort`.
- **Reference rates baked into the generation prompt.** Considered and declined.
- Company pricing percentages. Applied exactly as configured.
- Any change to the totals formula, or to which activities get generated.
- Frontend work.

## Decisions taken

1. **The only output is a corrected `ActivityItem.effort`.** Production rates are
   internal; nothing new is shown to the user. Money remains `effort × People
   rate`.
2. **History is gated on a close match**, and fails closed to web research. A
   researched rate for the right task beats a borrowed rate from the wrong one.
3. **Web research is the primary corrective lever**, not a fallback — Phase 1.
4. **Researched rates are not persisted.** The loop closes through job history.
5. **No history cutoff.** All indexed history is eligible, pre-fix included, with
   the risk accepted and monitored via Phase 4 logging.
6. **Rate cards are not used.**
7. **No reference rates in the generation prompt.**
8. **Company pricing percentages are out of scope** and applied as configured.
   The pricing-defaults change that prompted this work has been reverted.
