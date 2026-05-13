# Hodgepodge follow-ups

Carried over from the `/code-review` of the hodgepodge change (2026-05-13). The two HIGHs (sequential analytics awaits, unescaped markdown labels) shipped with the original change; the items below are deferred MEDIUMs/LOWs.

## MEDIUM

### 1. `compute_analytics` doesn't validate company ID shape
- **Where:** `platform/routers/estimates.py` (the `get_analytics` route + `compute_analytics(company)` call sites)
- **Issue:** `PydanticObjectId(company)` raises `InvalidId` on a malformed value, which currently bubbles as an HTTP 500. The list endpoint above has the same gap, so this isn't a regression introduced by this change — but the new analytics endpoint inherits the same shape.
- **Fix:** Catch `InvalidId` and raise `HTTPException(400, "Invalid company id")`, or change the route param type so FastAPI validates it and returns 422. Apply consistently to both routes while we're there.

### 2. `useEffect` references function declared later in the same component
- **Where:** `portal/src/pages/MaterialsPage.tsx` and `portal/src/pages/PeoplePage.tsx` — the `?open=<id>` effect calls `openEditMaterial` / `openEditLabour` declared further down. (Note: this was originally flagged when those effects opened the edit modal; the modal logic has since been removed, so the *symptom* is gone — but the pattern of effect-before-declaration may still apply if either page picks up a similar handler later.)
- **Issue:** Works at runtime because effects fire after the component body finishes evaluating, but it's brittle, future-hostile, and would silently fail eslint's `react-hooks/exhaustive-deps` rule.
- **Fix:** When adding any new effect in those files, declare its dependencies above the effect, or wrap helpers in `useCallback`.

### 3. Dashboard analytics fetch error is silent
- **Where:** `portal/src/pages/DashboardPage.tsx` — the `estimatesApi.analytics(...).catch(() => setAnalytics(null))` branch.
- **Issue:** Network/server errors are swallowed and the page silently shows `$0` cards. A user can't distinguish "no estimates yet" from "the API is down".
- **Fix:** Track an `analyticsError` state and render a small inline note ("Couldn't load analytics — retry") when set.

### 4. `test_estimates_analytics.py` exclusion assertion is brittle
- **Where:** `platform/tests/test_estimates_analytics.py:163-164` (`test_analytics_excludes_lost_and_archived_from_pipeline`)
- **Issue:** The assertion is `777.0 not in (pipeline, pipeline - 4000.0, pipeline - 3500.0)` against hand-computed offsets. A subtle inclusion-bug could pass the assertion. The test also relies on the test runner's wall-clock to align with the seeded `now`, which has caused at least one false alarm during development.
- **Fix:** Either (a) plumb `now` through `compute_analytics` as a hook for testing and pin it via the route, then assert exact totals, or (b) use `freezegun` to pin time. Simplest near-term: rebuild the assertion as `assert pipeline == <explicit_in_window_sum>` with no clock dependency.

## LOW

### 5. `RowActionsMenu` has two near-identical menu-item buttons
- **Where:** `portal/src/components/common/RowActionsMenu.tsx` — the Move up and Move down `<button>` blocks differ only in icon, label, and onClick.
- **Issue:** Minor duplication. Refactor only worthwhile if a fourth/fifth menu item lands.
- **Fix:** Extract a small `<MenuItem icon={…} label={…} disabled={…} onClick={…} />` helper if the menu grows.
