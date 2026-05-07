# Add "Standard Unbillable %" + restructure People pricing

> _Note on file location:_ Per saved preference, plans live in
> `documentation/development/plans/`. After approval, move/copy this file there
> with a descriptive slug (e.g. `people-pricing-unbillable.md`).

## Context

Today, a labour role's **Rate** is computed as `cost × (1 + labor_burden / 100)`
in one step. The user wants to decompose that into three components so the
pricing math is transparent on the People page:

```
unbillable_amt = avg_wage × (standard_unbillable_pct / 100)
labor_burden   = (avg_wage + unbillable_amt) × (labor_burden_pct / 100)
rate           = avg_wage + unbillable_amt + labor_burden
```

To support this we add a new company-wide setting **Standard Unbillable %**
(default 20%) alongside the existing **Labor Burden %**, surface the four
components on the People page, and stop asking the user to enter Rate when
creating a role — the backend now derives it.

User-confirmed decisions:
- **DB names unchanged.** Keep `Labour.cost` / `Labour.price` in MongoDB and the
  API. Only user-facing labels change ("Avg. Wage", "Rate").
- **One-time backfill** of `Labour.price` for existing rows using the new
  formula and each company's percentages.
- **Maple drops `rate` as an input alias.** Wage-style aliases replace it; if a
  user says "set rate to $X", Maple steers them toward `wage`.
- **Onboarding gets the new field too** so new companies confirm the 20%
  default at signup.

---

## Critical files to change

### Backend

- **`platform/models/company.py:42`** — add `standard_unbillable_percent: float = 20.0` next to `labor_burden`.
- **`platform/routers/companies.py:25-42`** — add `standard_unbillable_percent: float = 20.0` to `CompanyWrite`. The existing `set(company.model_dump())` handler already covers persistence + audit.
- **`platform/routers/labours.py`**
  - `_normalize_labour()` (`:31-46`) — now takes both `labor_burden` and `standard_unbillable_percent`; **always** recomputes `price` from `cost` using the new 3-step formula (ignore any client-supplied `price`, since the form no longer sends it).
  - `create_labour` (`:49-77`) and `update_labour` (`:263-299`) — fetch both percentages from the company and pass to `_normalize_labour`.
  - `upload_labours_csv` (`:102-250`):
    - Drop `rate` from the known/optional column set (`:134`) and from the parsed-rows tuple (`:155`, `:166`, `:182-186`, `:188`, `:205`).
    - Always derive `price` from `cost` via the new formula.
    - Update docstring (`:109-114`) to drop the rate-column language.
- **`platform/services/company_bootstrap.py`** — `_build_labour_price` (`:16-17`) and the CSV row parsing (`:40-46`, `:52-53`, `:73-74`) currently honor an optional `rate`/`price` from the seed CSV. Switch to the new formula using `Company.labor_burden` + `Company.standard_unbillable_percent` (passed from caller). The seed-CSV `rate` column becomes unused and can be ignored on read.
- **`platform/agents/labour/service.py:41-57`**
  - `LABOUR_REQUIRED_FIELDS` — replace `"price"` with `"cost"` (the agent now collects wage; backend derives price).
  - `LABOUR_ALLOWED_FIELDS` — drop `"price"`.
  - `LABOUR_FIELD_ALIASES` — remove `"rate": "price"` and `"cost": "price"`. Add `{"wage": "cost", "average wage": "cost", "avg wage": "cost", "rate": "cost"}` so wage phrasings are recognized. (Keeping `"rate"` aliased to `cost` is the pragmatic compromise: if a user says "rate $50" we treat it as the wage and Maple's confirmation message shows "Avg. Wage: $50.00", which makes the rename visible.)
  - `LABOUR_USER_FIELD_LABELS` — change `"cost": "cost"` → `"cost": "wage"`; drop `"price"` row.
  - In the field-prompt copy (search for `"What's the cost"` / `humanize_field_name` callers in this file) update prompts so Maple asks for **wage**, not cost or rate.

### Frontend

- **`portal/src/types/api.ts:252, 279`** — add `standard_unbillable_percent?: number;` to both `Company` interfaces.
- **`portal/src/pages/SettingsPage.tsx`**
  - `:48` (`CompanyDetails`-shaped type) — add the field.
  - `:73` (`CompanyFormData`) — add `standard_unbillable_percent: string`.
  - `:208` (`getCompanyFormState`) — init `formatFixedDecimal(company?.standard_unbillable_percent ?? 20, 1)`.
  - `:666` (`handleCompanySave`) — add `standard_unbillable_percent: parsePercentInput(companyForm.standard_unbillable_percent, 20)` to the PUT payload.
  - `:1083-1086` (`companyReadOnlyFields`) — insert a "Standard Unbillable" row directly before "Labor Burden", using `formatPercent(companyDetails?.standard_unbillable_percent ?? 20)`.
  - `:1934-1954` (edit-mode input block) — clone the Labor Burden block, change `id`, label ("Standard Unbillable (%)"), and `companyForm.standard_unbillable_percent`/`handleCompanyFieldChange("standard_unbillable_percent", …)`. Render it directly above Labor Burden.
- **`portal/src/components/onboarding/CompanyStep.tsx`**
  - `:32` (`CompanyFormData`) — add `standard_unbillable_percent: string`.
  - `:51` (`getEmptyCompanyForm`) — default `"20"`.
  - `:189` (POST payload) — add `standard_unbillable_percent: parsePercentInput(companyForm.standard_unbillable_percent, 20)`.
  - `:434-443` — add an Input block above the Labor Burden one with id `ob_standard_unbillable_percent`, label "Standard Unbillable (%)".
- **`portal/src/pages/PeoplePage.tsx`**
  - `:16-22, 31-37` — drop `price` from `LabourFormData` and `initialForm`; the form no longer collects rate.
  - `:62-68` — extend the company fetch to also store `standardUnbillablePct` (rename hook to `companyPct = { laborBurden, standardUnbillable }` or add a second `useState`).
  - `:110-147` (`handleSubmit`) — payload becomes `{ name, description, unit, cost: parseFloat(formData.cost), company: COMPANY_ID }`. Drop `price` and the `parsedPrice` validation; the backend recomputes.
  - `:308-323` (desktop table header) — replace the two `Cost` / `Rate` columns with **four**: `Avg. Wage`, `Unbillable Amt.`, `Labor Burden`, `Rate`. Adjust column widths (the existing `7rem` cells are reusable).
  - `:343-348` (desktop row cells) — render four computed values:
    ```
    avgWage      = labour.cost ?? 0
    unbillable   = avgWage × (standardUnbillablePct / 100)
    laborBurden  = (avgWage + unbillable) × (laborBurdenPct / 100)
    rate         = labour.price ?? (avgWage + unbillable + laborBurden)
    ```
    Use `formatCurrency` for all four. Keep `labour.price` as the source of truth for Rate (already-persisted, includes any per-row drift) and only fall back to the live formula if it's missing.
  - `:367-409` (mobile card) — show **Wage** and **Rate** only on mobile to save space (the two intermediate values are derivable; the user just needs the input and final).
  - `:494-541` (Add/Edit Role form) — rename "Cost *" label to "Avg. Wage *", **delete the Rate input** entirely, drop the `onBlur` cost→rate auto-calc (`:506-516`). The grid becomes 2-col (`md:grid-cols-2`) with Unit + Avg. Wage.
  - `:575-578` (CSV help text) — change to: `Expected columns: name, description, unit, cost. (Cost is the Avg. Wage; Rate is computed.)`
  - `:583` (CSV template) — `"name,description,unit,cost\nElectrician,Licensed electrician,Hourly,75.00"`. Drop the rate column.
- **`portal/src/lib/people.ts` + `portal/tests/people.test.ts`** — `buildDuplicateLabourPayload` currently preserves `price`; that's harmless because the backend now always recomputes. Update the "falls back to price when cost is missing" test: cost is now the canonical field, and a labour record without a cost shouldn't survive duplication — adjust the test to assert the new behavior (or delete the fallback path).

### Documentation

- **`platform/user_guides/users_guide.md`**
  - Section 5 People (around `:539-542` and the role/cost/price text) — rename "cost / price" to "Avg. Wage / Rate" in the user-facing description; add a one-paragraph explainer of how Rate is built from Avg. Wage + Standard Unbillable + Labor Burden.
  - Section 6 "How the price is calculated" (`:623-634`) — update the bullet that says "Add profit margin, overhead, labour burden, and tax on top": call out that the labour Rate already includes Standard Unbillable and Labor Burden at the role level, so the work-item-level labour burden line is on top of that.
### Tests

Run only files relevant to changed code (per CLAUDE.md):

- `platform/tests/conftest.py:43` — add `standard_unbillable_percent=20.0` to the test company fixture.
- `platform/tests/test_company_api.py` — extend the create/update/get tests at `:71, :91, :267, :522` to cover the new field.
- `platform/tests/test_labour_api.py`
  - Update `test_create_labour_with_explicit_price` to assert that an explicit `price` is **ignored** (server recomputes).
  - Add `test_create_labour_uses_unbillable_and_burden` — given `cost=100`, `standard_unbillable_percent=20`, `labor_burden=20`, expect `price=144.00` (`100 + 20 + (120×0.2) = 144`).
- `platform/tests/test_labour_upload_api.py`
  - Drop / rewrite `test_upload_labours_csv_with_explicit_price` — CSV no longer accepts a rate column; the expected behavior is "rate column ignored if present".
  - Add a test asserting CSV-only `cost` rows produce `price` via the new formula.
- `platform/tests/test_labour_agent.py` — update tests that exercise `cost`/`rate` aliases:
  - "create a Foreman with rate $50" should now set `cost=50` (alias maps `rate → cost`), and the confirmation message uses "wage" / "Avg. Wage".
  - Update `test_labour_update_parses_cost_of_phrasing` and the field-then-value multi-turn test to expect the wage-renamed prompt copy.
- `portal/tests/people.test.ts` — adjust `buildDuplicateLabourPayload falls back to price when cost is missing` (see above).

### Migration

- **New file: `documentation/development/migration_scripts/migrate_labour_recalculate_prices.py`**
  - Connect to MongoDB using the same pattern as `migrate_labours.py` (in the same dir).
  - For each `Company`, read `labor_burden` and `standard_unbillable_percent` (default 20 if missing).
  - For each `Labour` in that company, recompute `price = cost + (cost × U) + ((cost + cost × U) × B)` and update.
  - Idempotent (running twice produces the same result). Print summary: `companies_processed`, `labours_updated`.
  - User runs once after deploy.

---

## Verification

Backend tests (only the ones touching changed code):

```bash
cd platform && source .venv/bin/activate
./run_tests.sh tests/test_company_api.py tests/test_labour_api.py tests/test_labour_upload_api.py tests/test_labour_agent.py
```

Frontend tests:

```bash
cd portal
npm test -- people.test.ts
# plus any SettingsPage / CompanyStep tests that exist
```

Manual smoke test (start dev servers, run in browser):

1. **Settings → Company** shows "Standard Unbillable" read-only at 20.0%; clicking Edit reveals an input with `step="0.1"` directly above Labor Burden. Save; reload; value persists.
2. **Onboarding** new-company form has the same field with default `"20"`.
3. **People page**:
   - Table has four numeric columns: Avg. Wage, Unbillable Amt., Labor Burden, Rate. For an existing role with `cost=$50` and 20% / 20% percentages, Rate shows `$72.00`.
   - Add Role form has only Wage + Unit on the right (no Rate input). Submitting `cost=50` returns a row whose Rate displays `$72.00`.
   - Upload CSV modal text says "Expected columns: name, description, unit, cost"; the template download produces a 4-column file with no rate column. Upload a CSV with an extra `rate` column — it's silently ignored and rates are recomputed.
4. **Maple**:
   - "Create a Foreman role at $50/hr" → confirms with "Avg. Wage $50.00" and computed Rate.
   - "Set the rate of Foreman to $60" → maps `rate → cost`, sets wage to $60, recomputes Rate.
   - "How much is the Foreman?" → shows wage and rate.
5. Run the migration script against a dev/staging DB; verify `price` values reconcile with `cost + (cost × U) + ((cost + cost × U) × B)` for every labour row.

