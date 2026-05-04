# Adjust Work Item Total

## Context

Estimators frequently want to round a Work Item's bottom-line total to a clean number (e.g. quote "$2,500.00" instead of "$2,487.43") without manually iterating on the profit-margin %. Today the Total is purely derived (`subtotal × (1 + profit%) × (1 + tax%)`) and the only lever is the profit-margin field, which forces trial-and-error.

This change adds an **Adjust** pill next to the **Work Item Total** line. Clicking it opens a dialog where the user types the desired total; on Set, we back-calculate `profit_margin` so the displayed total matches. We remember the user's original profit margin so we can show the un-adjusted "original amount" beneath the pill and offer a Reset.

Math (validated against [`getWorkItemBreakdown()`](../../platform/portal/src/utils/estimateCalculations.ts) — line 97):

```
new_profit_% = ((new_total / (1 + tax_%)) − subtotal) / subtotal
```

where `subtotal` is `breakdown.subtotal` (the value rendered on the **Subtotal (Materials + Labor)** line — already includes overhead and burden additions).

## Decisions (confirmed with user)

- **Persist to backend.** Add `original_profit_margin: Optional[float]` to `JobItem` so the adjustment context survives reload.
- **Recompute the displayed "original amount" live** from current materials/labour/tax × `original_profit_margin`. It stays accurate as the work item is edited after adjustment.

## Files to modify

### Frontend (portal/)

1. **`src/lib/workItemV2.ts`** (line 37–48)
   - Add `original_profit_margin?: number` to the `WorkItemV2` interface.
   - Pass-through in `emptyWorkItem()` (undefined by default), `workItemV2ToJobItemPayload()` (line 152–189), and the inverse `jobItemToWorkItemV2()` mapping.

2. **`src/api/estimates.ts`** — add `original_profit_margin?: number | null` to the `JobItemPayload` type so it serializes over the wire.

3. **`src/utils/estimateCalculations.ts`** — add a small pure helper:
   ```ts
   export function backCalculateProfitMargin(
     subtotal: number,
     taxPct: number,
     newTotal: number
   ): number  // returns the new profit % (may be negative for discounts)
   ```
   - Throws / returns `null` when `subtotal === 0` (caller must disable Set).
   - Rounds to 2 dp to keep the resulting total stable when echoed back through `getWorkItemBreakdown()`.

4. **`src/components/estimates/AdjustTotalDialog.tsx`** — NEW component.
   - Reuses [`Modal`](../../platform/portal/src/components/common/Modal.tsx) for the chrome.
   - Props: `isOpen`, `onClose`, `currentTotal`, `originalTotal`, `onSet(newTotal: number)`.
   - Layout matches the spec:
     ```
     Adjust Amount
     [ new amount ]   Reset
     [Cancel]  [Set]
     ```
   - `Reset` swaps the field value to `originalTotal` (does **not** close the dialog).
   - `Set` is disabled when input is non-numeric, ≤ 0, or `subtotal === 0`.

5. **`src/components/estimates/WorkItemInlineContent.tsx`** (line 695–698)
   - Add `originalProfitMargin` state, hydrated from `initialData?.original_profit_margin`.
   - Replace the Total row with: label · **Adjust** pill · amount. Style the pill using the existing brand-pill class (`inline-flex items-center gap-1.5 px-3 py-0.5 text-xs font-medium border border-brand rounded-full text-brand hover:bg-brand/10`) — sized down from the line 340 button so it sits inline.
   - Below the row, when `originalProfitMargin !== undefined && originalProfitMargin !== profitMargin`, render `Original: {formatCurrency(originalTotal)}` in a muted style. `originalTotal` comes from `getWorkItemBreakdown({ ...item, profit_margin: originalProfitMargin })`.
   - On dialog Set:
     - If `originalProfitMargin` is undefined, capture the current `profitMargin` into it.
     - Compute `newProfit = backCalculateProfitMargin(breakdown.subtotal, tax, newTotal)` and `setProfitMargin(newProfit)`.
   - Reflect both `profit_margin` and `original_profit_margin` in the WorkItemV2 emitted to the parent (no extra save plumbing needed — they ride the existing onChange path).
   - When the user manually edits the **+ Profit** % NumericInput, clear `originalProfitMargin` (the user has taken explicit control again) — this also hides the "Original:" line and the implicit "adjusted" state.

### Backend (platform/)

6. **`models/estimate.py`** (line 219–235, `JobItem`)
   - Add `original_profit_margin: Optional[float] = None`.
   - No migration needed — Beanie/Mongo tolerates missing fields on existing docs.

## Tests (TDD — write first, per CLAUDE.md)

- **`portal/src/utils/__tests__/estimateCalculations.test.ts`** (new or extend existing)
  - `backCalculateProfitMargin` — happy path: round-trips through `getWorkItemBreakdown` to match `newTotal` within $0.01.
  - Tax = 0 case.
  - Discount case (`newTotal < currentTotal` → negative profit %).
  - `subtotal === 0` returns `null` (or throws) — caller responsibility documented.

- **`portal/src/components/estimates/__tests__/AdjustTotalDialog.test.tsx`** (new)
  - Renders label, input pre-filled with `currentTotal`, Reset, Cancel, Set.
  - Clicking Reset sets the field to `originalTotal`.
  - Set is disabled for invalid input; Cancel calls `onClose` without firing `onSet`.

- **`portal/src/components/estimates/__tests__/WorkItemInlineContent.test.tsx`** (extend if exists, otherwise add a focused test)
  - Adjust pill opens the dialog.
  - Setting a new total updates `profit_margin` such that the displayed Total equals the entered value.
  - "Original: $X" line appears after adjustment with the correctly recomputed un-adjusted total.
  - Editing the profit % NumericInput after adjustment clears `original_profit_margin` and hides the Original line.

- **`platform/tests/test_estimates.py`** (or the closest existing JobItem test file)
  - Round-trip an estimate with a JobItem carrying `original_profit_margin=15.0` through POST + GET.

Run scope (per CLAUDE.md):
```bash
cd portal && npm test -- estimateCalculations AdjustTotalDialog WorkItemInlineContent
cd platform && ./run_tests.sh tests/test_estimates.py
```

## Verification (manual)

1. `cd portal && npm run dev`; open an estimate; expand a Work Item.
2. Note the current Total (e.g. $2,487.43).
3. Click **Adjust**, enter `2500`, click **Set**.
   - Total displays $2,500.00.
   - Profit % field reflects the back-calculated value.
   - "Original: $2,487.43" appears below the pill.
4. Change a material quantity → the displayed Total stays consistent with the new profit %, and the "Original" line recomputes from the original margin.
5. Reopen the dialog → click **Reset** → Set → adjustment is cleared and "Original" line disappears.
6. Save the estimate, reload → the adjusted total and Original line persist.
7. Set tax to 0% and repeat (3) to confirm the no-tax branch.

## Out of scope

- Per-line-item adjustment (this is Work Item-level only).
- Adjusting the estimate-level grand total (different surface; would need its own design).
- Audit trail / who-adjusted-when (not requested).
