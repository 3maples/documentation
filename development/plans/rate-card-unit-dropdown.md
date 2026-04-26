# Rate Card Unit — Dropdown + Effort Calculator Column

## Context

The Rate Card creation page (`portal/src/components/settings/RateCardsTab.tsx`) currently lets users type any free-text value into the **Unit** field, leading to inconsistent values across cards (`SF/HOUR`, `LF/HOUR`, `sf/hour`, etc.). We want to standardize to four canonical options and surface the selected unit in the Effort Calculator so users see the unit alongside Size when estimating.

**Allowed unit values (canonical strings):**
- `square feet/hour`
- `square yard/hour`
- `linear feet/hour`
- `linear yard/hour`

Validation will be enforced at both the Pydantic model (server-side) and the React UI (client-side dropdown). Existing legacy data (`SF/HOUR`, `LF/HOUR`) will be migrated in-place via a one-shot script before the new validation goes live.

## Changes

### 1. Backend — restrict `CardItem.unit` to a Literal

**File:** `platform/models/rate_card.py`

- Add a module-level constant tuple `ALLOWED_UNITS = ("square feet/hour", "square yard/hour", "linear feet/hour", "linear yard/hour")`.
- Change `CardItem.unit` from `str = Field(..., min_length=1)` to `Literal[...ALLOWED_UNITS]` (use `typing.Literal` with the four string literals).
- This gives 422 validation errors at the API layer for any non-matching value.

### 2. Backend — data migration

**File (new):** `documentation/development/migration_scripts/migrate_rate_card_units.py`
(directory already exists alongside other migration scripts)

- Connect to MongoDB using the same `config.Settings` as the platform.
- For every document in `rate_cards`, walk `items[]` and apply the map:
  - `SF/HOUR` → `square feet/hour`
  - `LF/HOUR` → `linear feet/hour`
  - Any value already in `ALLOWED_UNITS` → leave unchanged
  - Anything else → log the rate card name + item index + bad value, **do not write**
- Print summary: total cards scanned, items updated, items flagged for manual cleanup.
- Idempotent — safe to re-run.
- Must be run before deploying the Literal-type change, otherwise existing documents will fail Pydantic validation when read.

### 3. Frontend — TypeScript type + shared constant

**File:** `portal/src/types/api.ts`

- Replace `unit: string` on `CardItem` with `unit: RateCardUnit`.
- Export `RateCardUnit = "square feet/hour" | "square yard/hour" | "linear feet/hour" | "linear yard/hour"` and a sibling `RATE_CARD_UNITS: readonly RateCardUnit[]` array for iteration in the dropdown.

### 4. Frontend — Rate Card form dropdown

**File:** `portal/src/components/settings/RateCardsTab.tsx` (lines 356–364)

- Replace the `<input type="text">` for `item.unit` with a `<select>` whose options come from `RATE_CARD_UNITS`.
- Add a leading placeholder option (`value=""`, label `"Select unit…"`, disabled) so empty selection is visible until the user picks.
- Keep the existing Tailwind classes for visual parity with the Difficulty dropdown in the Effort Calculator (the `<select>` styling at `EffortCalculatorDialog.tsx:227–239` is the reference pattern).

**File:** `portal/src/lib/rateCards.ts`

- `createBlankCardItem()` — initialize `unit` as `""` (still empty so the validation error fires until user picks).
- `validateRateCardForm()` — keep the empty check, **and** add a check that `unit` is in `RATE_CARD_UNITS`; otherwise return `"Item ${i+1}: Unit must be one of the allowed values."`.
- `buildRateCardPayload()` — drop the `.trim()` on `unit` (no longer free-text).

### 5. Frontend — Effort Calculator: new "Unit" column

**File:** `portal/src/components/estimates/EffortCalculatorDialog.tsx`

- Add a new `<th>` "Unit" between **Task** and **Size** (insert at line ~197). Width `w-36` to fit `square feet/hour`.
- Add a corresponding `<td>` per row (insert at line ~219) rendering `row.unit` as static text — not editable, since the unit is a property of the rate-card item, not the calculator row.
- Update the `tfoot` `colSpan={3}` → `colSpan={4}` (line 253) so "Total Effort" stays right-aligned over the four non-total columns.
- `CalculatorRow.unit` already exists (lines 32–35) and is populated when rows are derived from card items, so no data wiring needed.

### 6. Tests

**Backend** — `platform/tests/test_rate_cards_api.py`
- Update `SAMPLE_ITEMS` (lines 15–18) to use new canonical strings.
- Add a test asserting that `POST /rate-cards` with `unit="SF/HOUR"` returns 422.
- Add a test asserting that `POST /rate-cards` with each of the four allowed values succeeds.

**Frontend** — `portal/tests/rateCards.test.ts`
- Update existing fixtures to use canonical unit strings.
- Add a `validateRateCardForm` case asserting an unknown unit returns the new error message.

**Frontend** — `portal/tests/effortCalculator.test.ts`
- No new logic test needed (Unit is display-only), but if the file renders the table, add a render assertion that the Unit column appears with the expected text. If purely logic-level, leave alone.

## Critical files

- `platform/models/rate_card.py` — Literal validation
- `platform/tests/test_rate_cards_api.py` — backend tests
- `portal/src/types/api.ts` — shared type + constant
- `portal/src/lib/rateCards.ts` — form validation
- `portal/src/components/settings/RateCardsTab.tsx` — dropdown
- `portal/src/components/estimates/EffortCalculatorDialog.tsx` — new column
- `portal/tests/rateCards.test.ts` — frontend tests
- `documentation/development/migration_scripts/migrate_rate_card_units.py` — new

## Deployment order

1. Merge code with new Literal type + dropdown + migration script.
2. **Run migration script against the production DB.** Resolve any flagged items manually.
3. Deploy backend (Pydantic Literal will now accept all stored values).
4. Deploy frontend.

Doing it in this order avoids a window where deployed backend rejects reads of un-migrated documents.

## Verification

1. **Backend tests:** `cd platform && ./run_tests.sh tests/test_rate_cards_api.py`
2. **Frontend tests:** `cd portal && npm test -- rateCards.test.ts effortCalculator.test.ts`
3. **Manual smoke (frontend):**
   - `cd portal && npm run dev`
   - Settings → Rate Cards → create a card → confirm Unit field is a dropdown with exactly four options and no free-text path.
   - Edit an existing card with a (now-migrated) unit → confirm the dropdown shows the migrated value pre-selected.
   - Estimates → Effort Calculator → pick a rate card → confirm the new **Unit** column appears between Task and Size, populated for every row, and that the "Total Effort" footer alignment still looks correct.
4. **Migration dry-run:** run `migrate_rate_card_units.py` against a staging DB first; review the "flagged for manual cleanup" output before touching prod.
