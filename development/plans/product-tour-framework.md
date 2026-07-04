# Product Tour Framework

## Context

New users land in the portal with no guidance. We want a reusable **product tour framework**: named sets of callout popovers that point at UI elements, triggered by entering a page (Dashboard, Estimates, …). Each callout shows description text with **Next** (→ **Done** on the last step) and **Skip** (dismisses the whole set). Each set shows **once per user**, persisted server-side so it survives devices; per-set toggles in Settings → Account let the user re-enable any tour.

Decisions confirmed with Simon:
- Seen-state persisted on the backend `User` record (not localStorage-only).
- Tour definitions live as a versioned TypeScript registry in the portal repo (no DB/admin surface).
- Custom lightweight callout component — no react-joyride/driver.js dependency.
- `tooltips.csv` (field-level help copy) is a **separate feature**, out of scope.

**Two repos, two independent changes** (platform/ and portal/ are separate git repos). Ship backend first; commit/push each only with fresh explicit approval. TDD (failing test first) throughout.

Also per Simon's preference: save a copy of this plan to `documentation/development/plans/product-tour-framework.md` when implementation starts.

## Architecture

The only contract between repos is the **tour id** (opaque slug, e.g. `"dashboard-v1"`). Versioning = bump the id; stale ids in users' lists become inert, no migration.

- **platform/**: `completed_tours: List[str]` on `User`; two atomic self-scoped endpoints modeled on `record_overage_event` ([routers/users.py:327](platform/routers/users.py:327)); `completed_tours` added to the `/auth` login payload.
- **portal/**: tour registry module → pure selection helper → `TourCallout` popover (positioning modeled on `InfoTooltip`) → `TourManager` mounted once in `PortalLayout`, watching route changes. Settings card maps the registry to toggles.

## Backend (platform/)

New test file: `platform/tests/test_tour_state_api.py` (helpers: `onboard_owner`, `unique_email`, `X-Test-Email` header). Start local mongo first: `./scripts/start_test_mongo.sh`.

1. **Model** — [models/user.py](platform/models/user.py): add `completed_tours: List[str] = Field(default_factory=list)` (membership = "seen, don't show"). Test: new user defaults to `[]`.
2. **Complete endpoint** — `POST /users/me/tours/{tour_id}/complete` in [routers/users.py](platform/routers/users.py), following the `record_overage_event` pattern (`_require_authenticated_platform_user`, `User.get_pymongo_collection()`):
   ```python
   result = await collection.update_one(
       {"_id": actor.id},
       {"$addToSet": {"completed_tours": tour_id}, "$set": {"updated_at": now}},
   )
   return {"completed": True, "first_time": result.modified_count > 0}
   ```
   `tour_id` constrained by `Path(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")` (backend can't see the portal registry). No audit log — UX preference state, not billing/security (note in docstring). Tests: id added; second call idempotent (`first_time` false); bad slug → 422; unauthenticated → 401. (No route conflict with `/users/{user_id}` — different segment counts; `/users/me/company` sets precedent.)
3. **Reset endpoint** — `DELETE /users/me/tours/{tour_id}`: `$pull` the id, return `{"reset": True}`. Tests: removes id; never-completed id is a 200 no-op; auth required.
4. **Login payload** — add `"completed_tours": list(user.completed_tours)` to `_serialize_user` ([routers/auth.py:67](platform/routers/auth.py:67)) so a new device learns seen-state at login. Test: `/auth` response contains it, populated after a complete call.
5. Gates: `./run_tests.sh tests/test_tour_state_api.py`, `./run_mypy.sh models routers`, `./run_ruff.sh models routers`. Datetimes: `datetime.now(timezone.utc)` only.

## Frontend (portal/)

Tests in `portal/tests/` (Vitest + testing-library, conventions per `tests/SupportPanel.test.tsx`).

6. **Registry** — new `src/tours/registry.ts`:
   ```ts
   export interface TourStep { target: string; /* data-tour attr value */ text: string; placement?: "top"|"bottom"|"left"|"right"; }
   export interface TourDefinition { id: string; name: string; settingsDescription: string; triggerPath: string; steps: TourStep[]; }
   export const TOUR_REGISTRY: TourDefinition[] = [/* dashboard-v1, estimates-v1 */];
   ```
   Initial content: a Dashboard tour (e.g. nav, key metric cards) and an Estimates tour — placeholder-quality copy, Simon refines later. Add `completed_tours?: string[]` to `AuthUser` in [src/types/api.ts](portal/src/types/api.ts). Test (`tourRegistry.test.ts`): ids unique + slug-shaped, ≥1 step each, triggerPaths are real routes.
7. **Selection** — new `src/tours/selectTour.ts`: pure `selectTour(pathname, registry, completedTours, startedThisSession)` → first matching incomplete tour or null. Test: path match, completed skipped, session-started skipped, ordering.
8. **API wrappers** — new `src/api/tours.ts`: `completeTour(id)` / `resetTour(id)` via `apiRequest` ([src/api/client.ts](portal/src/api/client.ts)), each also updating the localStorage user cache (`getCurrentUser`/`persistCurrentUser` in [src/api/auth.ts](portal/src/api/auth.ts)) so `completed_tours` stays consistent app-wide. Test with `vi.mock` of the client: method/path correct, cache updated both directions.
9. **TourCallout** — new `src/components/tours/TourCallout.tsx`: portaled-to-body, fixed-position bubble with arrow, positioning/viewport-clamping modeled on [InfoTooltip.tsx](portal/src/components/ui/InfoTooltip.tsx) (incl. its jsdom zero-width guard), but **repositions** on scroll/resize (rAF-throttled) instead of dismissing. Shows: description text, step counter ("2 of 3"), Skip (secondary), Next/Done (brand Button). Escape = Skip. Highlight = positioned ring div around the target; no dim overlay in v1. Test: text + counter render, Next vs Done on last step, Skip/Escape fire onSkip.
10. **TourManager** — new `src/components/tours/TourManager.tsx` + `src/tours/waitForElement.ts`. Mounted once next to `<Outlet />` in `src/components/Layout/PortalLayout.tsx`. On `useLocation` change: `selectTour(...)`; resolve each step's `[data-tour="…"]` target via immediate `querySelector`, else `MutationObserver` with ~8s timeout; `scrollIntoView({block:"center"})` before showing. Missing target → skip that step; if **no** step resolves, end attempt **without** marking complete (retry on next navigation) but session-guard the current visit. Skip and Done both: optimistic cache update, then `completeTour(id)`. Module-scope session `Set` prevents mid-session restart. Test (MemoryRouter at `/dashboard`, mocked tours API + `getCurrentUser`): starts when target exists; waits for late-inserted target; Next advances; Done and Skip both call `completeTour`; completed tour never shows; unresolvable targets → no complete call.
11. **Targets** — add `data-tour="…"` attributes (refactor-safe vs CSS selectors) to the elements the two initial tours point at: PortalLayout nav items, DashboardPage metric widgets, EstimatesPage list/new-estimate button. Assert in tests that every registry `target` exists in the rendered page (or at minimum keep registry↔attribute greppable consistency).
12. **Settings card** — new `src/components/settings/ProductToursCard.tsx` (own file; SettingsPage is already ~2.5k lines), rendered in the Account tab of [SettingsPage.tsx](portal/src/pages/SettingsPage.tsx) near the overage-notification preference. One row per `TOUR_REGISTRY` entry (name + settingsDescription) with a toggle: **checked = will show** (id ∉ `completed_tours`). Check → `resetTour(id)`, uncheck → `completeTour(id)` — saves immediately with per-row pending/disabled state (matches "inline live editing" preference; these are instant-save toggles, not part of the account form's Edit/Save cycle). Test: rows render, checked-state mapping, toggle calls the right API, pending disables.
13. Gates: `npm test -- <new test files>` then `npm run typecheck` (build alone doesn't typecheck).

## Verification (end-to-end)

1. Backend: `cd platform && ./scripts/start_test_mongo.sh && ./run_tests.sh tests/test_tour_state_api.py && ./run_mypy.sh && ./run_ruff.sh`.
2. Portal: `cd portal && npm test && npm run typecheck`.
3. Manual smoke (uvicorn + `npm run dev`): log in as a fresh test user → Dashboard tour fires; step through Next/Done → reload, tour does not reappear; navigate to Estimates → that tour fires once; Skip it; Settings → Account → Product Tours: both toggles off; flip Dashboard on → revisit Dashboard → tour fires again; check `completed_tours` round-trips through `/auth` on re-login.
