# Work Item Markup & True Profit Margin

> **Amended 2026-09-14 — read this first.** Everything below still describes
> the maths correctly, but two things changed after it shipped:
>
> 1. **"Profit Margin" is now "Gross Margin"** throughout the UI, the users
>    guide and the code (`getWorkItemMargin` → `getWorkItemGrossMargin`,
>    `trueProfit` → `grossProfit`, `revenue` → `preTaxRevenue`). §9's mockup
>    and §10's guide table use the old label.
> 2. **The readout moved onto the Markup row and became editable.** §9's
>    "New readout" sketch shows it indented under the Work Item Total; it now
>    sits beside Markup %, with a new **Selling Price** row (subtotal + markup,
>    pre-tax) below carrying the denominator. Typing a target margin solves
>    backwards for the markup via `backCalculateMarkupFromGrossMargin` —
>    which is **not** `markup / (1 + markup)`: that conversion cannot see the
>    profit inside material prices and answers 9.09% for §2's job keeping
>    16.89%.
>
> The numerator is unchanged: **overhead is still deducted**, which is a
> deliberate departure from the textbook reading of "gross" (revenue less
> direct cost only). Decided 2026-09-14, on the grounds that a work item is
> asked "am I making money on this job after overhead?".

**Date:** 2026-09-13
**Status:** Implemented 2026-09-13 (uncommitted)
**Scope:** `portal/` + `platform/` + `documentation/`

---

## 1. Problem

The work item totals ticket labels its uplift percentage **"Profit %"** and the
underlying field is named `profit_margin`. Neither is accurate, for two
independent reasons.

**It is a markup, not a margin.** The math applies the percentage to the base
and adds it on top:

```
profitAmount = subtotal × profit%
afterProfit  = subtotal + profitAmount
```

That is the definition of markup. Margin is `profit ÷ selling price`. A
"10% Profit Margin" entered today delivers a 9.09% margin; a "50%" entry
delivers 33.3%. The gap widens as the number grows.

**The base is price, not cost.** Materials and labor both enter the subtotal at
their *price*, so the subtotal already contains embedded uplift. The displayed
"Profit" dollar figure is therefore neither the markup on cost nor the work
item's actual profit — it is an uplift on an already-uplifted base.

A contractor reading "+ Profit 10% → $3,643.87" reasonably concludes they make
$3,643.87 on the work item. That is wrong in both directions.

---

## 2. Findings — what each price/cost spread actually represents

Tracing every rate-derivation path in the app:

| Layer | How price is derived | Is the spread profit? |
|---|---|---|
| **Material** | `price = cost × (1 + company.material_markup%)` — `routers/materials.py:119` | **Yes.** Real gross profit. |
| **Labor (Rate)** | `rate = wage × (1 + unbillable%) × (1 + burden%)` — `services/labour_pricing.py:12` | **No.** Entirely cost recovery — unbillable time and payroll burden. Zero markup by construction. |
| **Work item Overhead %** | `labourTotal × overhead%` | **No.** Allocated real overhead. |
| **Work item "Profit %"** | `subtotal × profit%` | **Yes.** |

The critical finding is the labor row. `Labour.price` is recomputed server-side
from `Labour.cost` on every write, with any client-supplied value discarded
(`routers/labours.py:51`). The Rate **is** the fully-loaded cost. A naive
"revenue − material cost − labor wage" margin would count every dollar of
payroll burden and unbillable time as profit and wildly overstate the result.

### Worked example (the totals ticket that prompted this)

Assuming the default 10% material markup:

```
Materials (at price)                      $34,376.28
Labor (at loaded rate)                     $1,711.58
Overhead 20.50%                              $350.87
────────────────────────────────────────────────────
Subtotal                                  $36,438.73
Markup 10.00%                              $3,643.87
Pre-tax revenue                           $40,082.61
Tax 8.00%                                  $3,206.61
Work Item Total                           $43,289.22

Material cost  (34,376.28 ÷ 1.10)         $31,251.16
Material profit                            $3,125.12
Labor profit   (rate = loaded cost)            $0.00
Overhead       (real cost)                     $0.00
Markup profit                              $3,643.87
────────────────────────────────────────────────────
True profit                                $6,768.99
True Profit Margin  (6,768.99 ÷ 40,082.61)    16.89%
```

Three different numbers — 10.00%, 9.09%, 16.89% — none interchangeable, and the
UI currently shows only the one that means the least.

---

## 3. Decisions

| Question | Decision |
|---|---|
| Margin basis | **Net margin.** Cost = material cost + fully-loaded labor rate + overhead. Profit = material markup + work-item markup. |
| Legacy `MaterialItem.cost` | **Fix in place + backfill** from catalog. |
| Rollout scope | **Work item only.** No Grand Total rollup in v1. |
| Maple | **Documentation only.** Explains the concepts correctly; does not report per-work-item values. |
| DB field rename | **No.** `profit_margin` keeps its name; the relabel is UI-only. |

Renaming the persisted field would mean a migration across estimates,
templates, and company defaults for zero user-visible benefit.

---

## 4. The margin formula

A new pure function beside `getWorkItemBreakdown` in
`portal/src/utils/estimateCalculations.ts`:

```
materialCost = Σ(quantity × unit_cost)        // matched materials only
labourCost   = Σ(effort × cost_rate)          // loaded rate, see §5
trueProfit   = (materialsTotal − materialCost)
             + (labourTotal   − labourCost)
             + markupAmount
revenue      = afterMarkup                     // pre-tax
marginPct    = trueProfit / revenue × 100
```

- Overhead is a cost and contributes nothing to profit.
- Tax is excluded from both numerator and denominator (pass-through).
- Unmatched materials are already excluded from pricing and stay excluded here.
- Equipment is excluded from pricing app-wide and is not considered.

### Why labor still needs a stored cost basis

In the normal case `rate == cost_rate` and labor profit is exactly $0, which
looks like the field is redundant. It is not: the activity rate is editable
inline (`ActivitiesTable.tsx:87`). When a user hand-raises a rate above the
role's computed Rate, that excess is real profit and must be counted. Storing
the basis is what lets the formula stay honest in both cases.

Materials behave the same way — the row price is editable, and margin grows
correctly when it is raised.

---

## 5. Data model changes

### `MaterialItem.cost` — widened to Optional

```python
class MaterialItem(BaseModel):
    ...
    price: float          # unit price
    cost: Optional[float] = None   # unit COST — None means "not recorded"
```

`None` is an explicit "unknown", keeping it distinguishable from a genuinely
free item at `0.0`. The request schema `MaterialItemCreate.cost` is already
`OptionalMoneyField = None` (`routers/estimates.py:118`), so only the document
model widens.

The docstring must pin the semantics: **`cost` is a UNIT cost, parallel to
`price`. Extended cost is `quantity × cost`.** Ambiguity on this exact point
caused all four bugs in §7.

### `ActivityItem.cost_rate` — new

```python
class ActivityItem(BaseModel):
    ...
    rate: float = 0.0                    # billed rate per unit
    cost_rate: Optional[float] = None    # fully-loaded labor COST per unit
```

Sourced from the role's **`Labour.price`** (its computed Rate), not
`Labour.cost` (the wage) — see §2. Named `cost_rate` to parallel `rate` rather
than reusing `cost`, whose unit-vs-extended ambiguity is what this design is
cleaning up.

Both fields are **snapshots**, consistent with how `price`, `name` and `unit`
are already handled. A later catalog price change must not silently restate a
signed estimate's margin.

### Templates inherit both

`models/template.py` embeds `MaterialItem` and `ActivityItem` directly, so
templates pick up both changes automatically. Template write paths must
populate them (see §7, `template_bootstrap.py`).

---

## 6. Plumbing

### Portal

| File | Change |
|---|---|
| `src/lib/workItemV2.ts` | `cost` on `MaterialRowV2`, `costRate` on `ActivityRow`; both carried through `jobItemToWorkItemV2` (load) and `workItemV2ToJobItemPayload` (save) |
| `src/components/estimates/WorkItemInlineContent.tsx` | Populate `cost` in `handleMaterialSelect` / `handleSizeSelect`, `costRate` in `handleRoleSelect` |
| `src/types/api.ts` | `cost_rate` on the activity type |

The catalog values are already in hand at every population site —
`sizeEntry.cost` sits beside the `sizeEntry.price` already being read
(`WorkItemInlineContent.tsx:295`), and `costRate` reuses the very same
`person.price` already read for `rate` at `:326`. No new API calls.

### Platform

| File | Change |
|---|---|
| `routers/estimates.py` | `cost_rate` on `ActivityItemCreate`; pass through in the inline material/activity builders (`:1169`, `:1234`) |
| `routers/estimate_helpers/job_item_builders.py` | Same, across all four builder functions |

**Remove the `cost=... if ... is not None else m.price` fallbacks**
(`estimates.py:1169`, `job_item_builders.py:107`, `:344`, `:372`, `:387`).
Falling back to price fabricates a zero margin from missing data; `None` is the
honest answer and the UI renders it as such.

---

## 7. Cost/price confusion — four sites to fix

All four predate this work. The backfill in §8 cannot produce a sane cost basis
while any of them is still scrambling the two fields.

| # | Location | Bug | Fix |
|---|---|---|---|
| 1 | `portal/src/lib/workItemV2.ts:179` | `cost: m.quantity * m.price` — extended *price* into a unit-*cost* field | `cost: m.cost` |
| 2 | `platform/services/template_bootstrap.py:150` | `cost=price * quantity` — same mistake; every seeded template for every new company carries it | `cost=float(size.cost)` |
| 3 | `platform/agents/estimate/assumption_handlers.py:383` | `line.cost = replacement["price"]` | `line.cost = replacement["cost"]` |
| 4 | `platform/agents/estimate/assumption_handlers.py:336` | `"price": getattr(first, "cost", 0.0)` — the line's **selling price** is set to the catalog **cost** | Carry both: `"price"` from `_size_price(first)`, new `"cost"` from `first.cost` |

**Site 4 is a live revenue leak independent of this feature.** Any material
swapped through Maple loses the entire material markup — a $1,000 material at a
10% markup is re-priced at $909.09. It is in scope here because it writes the
same two fields, but it is worth fixing regardless of whether the rest of this
design ships.

Each of the four gets a named regression test.

---

## 8. Backfill

`platform/scripts/backfill_estimate_line_costs.py`, following the conventions
of the existing `scripts/backfill_brevo_lifecycle.py` (dry-run by default,
`--apply` to write).

**Behaviour**

- Material lines: resolve `material` id + `size` against the company catalog,
  set `cost` to that size's `cost`.
- Activity lines: resolve `role` against the People catalog, set `cost_rate` to
  that role's `price` (its computed Rate).
- **Unresolvable** (deleted material, renamed size, removed role) → set `None`
  and count as unresolved. The existing corrupt value is always overwritten or
  nulled, never left in place.
- Prints a per-status summary (draft / review / approved / rejected / on_hold)
  before writing.

**Flags**

| Flag | Default | Purpose |
|---|---|---|
| `--apply` | off | Write. Without it, dry-run only. |
| `--status draft,review` | all | Limit to estimate statuses. |
| `--company <id>` | all | Limit to one tenant. |

**Accepted risk, stated once:** this stamps *today's* catalog cost onto
historical estimates. An estimate approved six months ago will report its
margin against current costs, not the costs in force at the time. The
`--status` filter exists so drafts can be backfilled first and approved
estimates decided on separately. This was a deliberate choice over adding a
parallel `unit_cost` field.

---

## 9. UI

### Relabels (UI only — no DB field renames)

| Location | From | To |
|---|---|---|
| `WorkItemInlineContent.tsx:669` | `+ Profit` | `+ Markup` |
| `WorkItemInlineContent.tsx:46` (`PROFIT_TOOLTIP`) | "This Work Item's profit margin…" | Rewritten for markup, noting the margin line below |
| `FinancialTab.tsx:58` | `Default Profit Margin` | `Overall Markup` |
| `FinancialTab.tsx:62` | tooltip copy | Rewritten |
| `estimateCalculations.ts` | `backCalculateProfitMargin` | `backCalculateMarkup` |

### New readout

```
Work Item Total   (Adjust)                    $43,289.22
  Profit Margin ⓘ              16.89%          $6,768.99
```

- **Read-only.** No input, no Adjust affordance.
- Recomputed by `useMemo` on the same dependency list as `breakdown`, so it
  tracks every subtotal, percentage, and line-item edit live.
- Renders `—` when any matched line lacks cost data, with a tooltip naming the
  cause ("cost not recorded for 2 material lines").
- Renders in red when negative. A work item priced below cost is worth seeing,
  not hiding.
- Tooltip states what is counted: material markup + work-item markup, net of
  overhead, before tax.

---

## 10. Documentation

### `platform/user_guides/users_guide.md`

Maple's ground truth. Loaded **whole** into the prompt via `get_users_guide()`
(`agents/maple_guide/service.py:66`) — no vector index, so an edit takes effect
on the next request with no re-index step.

The guide currently teaches the error outright. `:911` reads *"**Profit %** —
applied to the work item subtotal"* under a glossary heading that calls it a
margin. Maple is presently trained to give users the wrong answer.

| Line(s) | Change |
|---|---|
| 321, 323 | "Adjust the Profit Percentage" → Markup |
| 762 | "**Default Profit Margin** — your standard target margin" → Markup, rewritten |
| 799 | work item field list → markup |
| 816 | pricing formula → `× (1 + Markup %)` |
| 823, 825 | "**Overhead %**, **Profit %**, **Tax %**" → Markup |
| 831 | Adjust auto-adjusts the **markup** % |
| 905–911 | Glossary: `Profit %` → `Markup %`; **new** `Profit Margin` entry |
| 41, 114, 621 | Incidental "profit margin" phrasing where it means the field |

**New subsection** under *How the price is calculated* — **"Markup vs. Profit
Margin"**. This is the substantive addition, not a relabel. It carries the
worked example from §2 so that "is my 10% markup the same as a 10% margin?"
gets answered correctly rather than confidently wrong, and explains why labor
contributes no profit (the Rate is fully-loaded cost).

Written in the guide's existing second-person voice. Per project convention,
Maple must never refer to the guide in third person — the content becomes her
own knowledge.

### `documentation/development/maple-phrasing-reference.md`

Required by CLAUDE.md in the same change as any Maple phrasing addition,
closure, or reclassification.

- Retitle §1.5.7 "Cost adjustments (profit margin, overhead, labor burden,
  tax)" → "(markup, overhead, labor burden, tax)".
- Split the table: **write** phrasings stay 🛑 refused (financial writes belong
  in the UI, unchanged policy); **read** phrasings for the concept route to
  help.
- `what's the profit margin on {WI}?` stays 🛑 for the *value*, with a note that
  the conceptual question is now answered from the guide.
- Update the §12.3 snapshot counts and the "Last updated" date at the top.

### `CLAUDE.md`

A short **Pricing model** section under *Key Implementation Notes* pinning the
semantics: what `cost` and `price` mean on each catalog model, that
`Labour.price` is a derived fully-loaded cost rather than a marked-up rate, that
`MaterialItem.cost` is a *unit* cost, and that `profit_margin` is a markup whose
UI label is "Markup".

Four separate sites have already confused cost with price (§7). A dozen lines
of prose is cheap insurance against a fifth.

### Not touched

- `website/` — no marketing copy references the field.
- `documentation/development/plans/*` — historical plan docs are point-in-time
  records. `adjust-work-item-total.md` describes what was true when written.
- No changelog entry (added on request only, per project convention).

---

## 11. Testing

TDD per CLAUDE.md — failing test first, then implementation.

### Portal (`npm test`, `npm run typecheck`)

Pure-function tests lead, since the formula is the whole feature:

- Known cost basis → expected margin (the §2 worked example as a fixture)
- Missing `unit_cost` on any line → `null`, renders `—`
- Missing `cost_rate` → `null`
- Hand-marked-up activity rate → labor profit appears correctly
- Hand-lowered material price below cost → negative margin
- `subtotal === 0` → `null`, no division by zero
- Unmatched materials excluded from both cost and revenue
- Round-trip: `jobItemToWorkItemV2` → `workItemV2ToJobItemPayload` preserves
  `cost` and `costRate` (regression for bug #1)
- Component test: margin row is read-only and recomputes on a price edit

### Platform (`./run_tests.sh`, `./run_mypy.sh`, `./run_ruff.sh` scoped)

- `MaterialItem.cost` accepts `None`; round-trips through Beanie
- `ActivityItem.cost_rate` accepts `None` and a float
- All four builders in `job_item_builders.py` pass both fields through
- The removed `cost → price` fallbacks no longer fire
- One named regression test per bug in §7, including a
  `test_maple_material_swap_preserves_price` for the revenue leak (#4)
- `template_bootstrap` seeds unit cost, not extended (#2)
- Backfill: seeded estimates with corrupt/missing costs → correct values;
  unresolvable lines → `None`; dry-run writes nothing; `--status` filter honored

### Documentation

- `test_maple_help_coverage.py` — the markup-vs-margin conceptual question
  routes to help
- Existing `test_maple_crud_coverage.py` Tier 1 must stay green after the
  §1.5.7 phrasing-reference edits

---

## 12. Files touched

**Portal (6)**
```
src/lib/workItemV2.ts
src/utils/estimateCalculations.ts
src/components/estimates/WorkItemInlineContent.tsx
src/components/estimates/WorkItemTotalsTicket.tsx     (new — see below)
src/components/settings/FinancialTab.tsx
src/types/api.ts
```

`WorkItemTotalsTicket.tsx` was split out during code-review follow-up: the
margin row pushed `WorkItemInlineContent` past 800 lines. The ticket is purely
presentational — every number arrives computed — so the pricing model still
lives only in `utils/estimateCalculations.ts`.

**Platform (6)**
```
models/estimate.py
routers/estimates.py
routers/estimate_helpers/job_item_builders.py
services/template_bootstrap.py
agents/estimate/assumption_handlers.py
scripts/backfill_estimate_line_costs.py          (new)
```

**Documentation (3)**
```
platform/user_guides/users_guide.md
documentation/development/maple-phrasing-reference.md
CLAUDE.md
```

Plus test files in both repos.

---

## 13. Out of scope

| Item | Why |
|---|---|
| Estimate-level margin under Grand Total | Deferred to v2; prove the cost data in the field first |
| Maple reporting per-work-item margin values | Needs the formula ported to Python + new classifier rules + Tier 1/2 coverage; deferred |
| Renaming the `profit_margin` DB field | Migration across estimates, templates and company defaults for no user benefit |
| Historical cost-at-time-of-estimate | Would need a price-history collection; the §8 accepted risk covers this |
| Capturing the raw wage (`Labour.cost`) on activities | Only needed for a direct-cost margin, which was explicitly not chosen |

---

## 14. Risks

| Risk | Mitigation |
|---|---|
| Backfill restates historical margins with today's costs | Accepted (§8). `--status` filter allows drafts-first. Dry-run default. |
| A user reads the margin as a guarantee rather than an estimate | Tooltip states exactly what is counted; guide subsection explains the basis |
| Users surprised that labor shows zero profit | Guide subsection explains the Rate is fully-loaded cost — this is correct, not a bug |
| `unit_cost` absent on older estimates post-backfill (deleted catalog entries) | `—` with an explanatory tooltip; never a fabricated number |
| Widening `MaterialItem.cost` to Optional breaks a reader | `agents/estimate/llm_pipeline.py:625` is the only reader; covered by tests and mypy |

---

## 15. Implementation notes

Implemented 2026-09-13. Two things came out differently than designed:

**§10 — one phrasing does not route to help.** `why does labor show no profit?`
classifies as `get_labour`, because "labor" is a domain keyword that beats the
conceptual reading. This is the general keyword-beats-concept routing problem
rather than anything specific to markup/margin, so it was left alone and
catalogued as a ⚠️ gap in the phrasing reference. A strict `xfail` in
`test_maple_help_coverage.py` pins it — when routing is fixed, that test turns
red and the doc row gets updated. The other five conceptual phrasings verified
as routing to help.

**§6 — unmatched materials keep their old coercion.** The optional-cost
treatment applies only to *matched* material lines. `UnmatchedMaterialItem` is
informational, excluded from pricing and from the margin, and its `cost` stays
a plain `float = 0.0`.

Everything else shipped as designed. Final state: portal 2219 tests green,
typecheck and lint clean; platform 1071 tests green across the affected
suites, zero mypy, zero ruff, bandit B110 at 11 (baseline 13).

### Follow-ups not done here

- Estimate-level margin rollup under Grand Total (§13)
- Maple reporting per-work-item margin values (§13)
- `why does labor show no profit?` routing (above)
