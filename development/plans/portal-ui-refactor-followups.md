# Portal UI Refactor Follow-ups

Deferred items from the 2026-05-01 code review of the Work Item dialog / Estimate page mobile-responsiveness work. The two HIGH items (file size of `WorkItemInlineContent.tsx`, fragile modal stacking) were addressed in the same change set; the items below are MEDIUM / LOW and were logged for later.

---

## MEDIUM

### 1. `key={idx}` for editable list rows
**Files:** `portal/src/components/estimates/WorkItemInlineContent.tsx`, `portal/src/components/estimates/MaterialsTable.tsx`, `portal/src/components/estimates/EffortCalculatorDialog.tsx`

Materials rows, Activities rows, and EffortCalculator rows all use the array index as the React key. Removing or reordering a row causes input state, focus, and uncontrolled cursor positions to drift to the wrong row for one render frame.

**Fix:** Generate a stable id when a row is created (e.g., `crypto.randomUUID()` stored on the row object in `addMaterialRow` / `addActivityRow`) and key on that.

---

### 2. Alternating row color computed inline twice
**File:** `portal/src/components/estimates/MaterialsTable.tsx`, `portal/src/components/estimates/WorkItemInlineContent.tsx` (Activities table)

`const rowBg = idx % 2 === 1 ? "bg-emerald-50" : "bg-white"` is duplicated across two map() bodies. Logic is correct (works around the activities table's sub-row Fragment shifting `:nth-child(even)` parity) but the rule is in two places.

**Fix:** Extract a shared `getRowBg(idx: number)` helper into a small utility module or co-locate it where both tables can import it.

---

### 3. `NewEstimateWithActivityPage.tsx` is 1,990+ lines
**File:** `portal/src/pages/NewEstimateWithActivityPage.tsx`

Far over the 800-line guideline. Holds estimate page state, work-item table, status menus, recurrence wiring, checklist dialog, gap dialogs, plus mobile responsive tweaks.

**Fix:** Extract `EstimateHeader`, `WorkItemsTable`, and `EstimateDocumentsSection` as sibling components. Schedule before the file passes 2,500 lines.

---

### 4. App-wide brand color `#4D5589` duplicated in arbitrary Tailwind values
**Files:** ~15 files across `portal/src/`

Used `bg-[#4D5589]`, `hover:bg-[#3f476f]`, `border-[#3f476f]`, `focus:ring-[#4D5589]/40` via a global sed sweep. Works but hex is repeated dozens of times; a future palette change needs another sweep.

**Fix:** Define `--color-brand` / `--color-brand-dark` in the Tailwind v4 `@theme` block (or `tailwind.config` if still on v3 syntax) and rewrite usages as `bg-brand` / `hover:bg-brand-dark`. Single source of truth.

---

### 5. EffortCalculator mobile dropdown initial-render flicker
**File:** `portal/src/components/estimates/EffortCalculatorDialog.tsx`

When the modal opens with `selectedCardId === null` and `rateCards.length > 0`, the mobile `<select>` shows the first card's name while the right panel still reads "Select a rate card to begin" until the parent useEffect fires. Brief visual mismatch.

**Fix:** Initialise `selectedCardId` synchronously via `useState(() => …)` reading the first rate card so there's no null window. Keep the existing useEffect for the open/close transitions.

---

## LOW

### 6. `MaterialsPage` mobile card popup-clip fix is scoped
**File:** `portal/src/pages/MaterialsPage.tsx`

The previous `overflow-hidden` clip was fixed by removing `overflow-hidden` from the card and adding `rounded-b-xl overflow-hidden` to the expanded sizes section. This works for the current popup but if a future popup is added inside the expanded sizes section it'll be clipped again.

**Fix:** If/when that case appears, switch popups to render via React portal so they aren't subject to ancestor clipping.

---

### 7. Three near-identical settings tabs
**Files:** `portal/src/components/settings/MaterialCategoriesTab.tsx`, `portal/src/components/settings/MaterialUnitsTab.tsx`, `portal/src/components/settings/DivisionsTab.tsx`

~95% identical markup and state machinery. Each round of UI work (icon buttons, Actions column width, Name column width) had to be applied three times. Divergence risk grows.

**Fix:** Extract a generic `<NameDescriptionResourceTab>` component parameterised by `api`, singular/plural labels, and any tab-specific extras.
