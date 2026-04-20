# Monthly Estimate Quota Per Company

## Context
Companies need a monthly cap on estimate creation (25/month). New companies joining mid-month get a prorated allowance. The counter resets on the 1st of each month.

## Approach: Lazy Reset (No New Dependencies)
Instead of adding APScheduler (new dependency, multi-worker issues), use a **lazy reset** pattern:
- Store `quota_reset_at` on each Company
- On estimate creation, check if the month has rolled over — if so, reset atomically
- On app startup, bulk-reset any stale companies (covers server downtime)

This is idempotent, handles edge cases, and requires zero new dependencies.

## Changes

### 1. Company Model — `platform/models/company.py`
Add `MAX_ESTIMATES = 25` constant and three fields:
- `total_estimates_allowed: float = 25.0` (prorated on creation)
- `number_of_estimates_created: int = 0`
- `quota_reset_at: datetime` (tracks last reset)

### 2. New Service — `platform/services/estimate_quota.py`
Utility functions:
- `calculate_prorated_quota(date)` — `MAX_ESTIMATES * (days_left / total_days)`
- `needs_quota_reset(quota_reset_at, now)` — checks if month rolled over
- `ensure_quota_reset(company)` — lazy reset if needed
- `increment_estimate_count(company)` — atomic `$inc`
- `check_quota_exceeded(company)` — returns bool after ensuring reset; uses `math.ceil(total_estimates_allowed)` so fractional quotas round **up** (e.g., 20.16 → allows 21)

### 3. Company Creation — `platform/services/company_service.py`
Compute prorated quota using `calculate_prorated_quota(now)` and pass to `Company()` constructor.

### 4. Estimate Endpoint — `platform/routers/estimates.py`
In `create_estimate()` (line 1264):
- After `assert_company_access`, fetch `Company` doc and call `check_quota_exceeded()`
- If exceeded, return HTTP 429 with message: *"You have exceeded your monthly allocated quota to create estimates. It will reset at the beginning of the month. If you need help, please contact support@3maples.ai."*
- After each of the 3 estimate insert paths (skip_generation, async, sync), call `increment_estimate_count()`

### 5. Startup Reset — `platform/main.py`
Add `reset_stale_estimate_quotas()` to lifespan:
- Bulk `update_many` for companies with `quota_reset_at < first_of_month`
- Also backfills existing companies missing the new fields

### 6. Frontend Type — `portal/src/types/api.ts`
Add `total_estimates_allowed?: number` and `number_of_estimates_created?: number` to `Company` interface.

### 7. Settings UI — `portal/src/pages/SettingsPage.tsx`
Add two read-only entries to `companyReadOnlyFields`:
- "Estimates Created This Month" — `number_of_estimates_created`
- "Monthly Estimate Allowance" — `total_estimates_allowed` (formatted as whole number)

These are always read-only (not in the edit form), so no changes to `CompanyFormData` or save logic.

## Edge Cases
- **Race conditions**: `$inc` is atomic in MongoDB. The check-then-act window is small and acceptable for a 25-estimate cap.
- **Fractional quota**: e.g., allowance 20.16 → `math.ceil(20.16)` = 21 estimates allowed. Always rounds up in the company's favor.
- **Deleted estimates**: Counter is append-only within a month — deletions don't decrement.
- **Existing companies**: Backfilled on startup with full 25 allowance.

## Verification
1. Run backend tests: `./run_tests.sh tests/test_estimates_api.py` and `./run_tests.sh tests/test_companies_api.py`
2. Run frontend tests: `npm test`
3. Manual: create a company mid-month, verify prorated allowance. Create estimates until quota exceeded, verify 429 response.
