# Shared Material Catalog — Stage 2 (Portal) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the portal onto the shared material catalog built in stage 1: a paged, searchable, filterable Materials page with standard items, per-company pricing, hide/show, reset and duplicate; the category opt-in in Settings; onboarding that opts in; and estimate/template pickers that search the server instead of loading the whole catalog.

**Architecture:** Every material read goes through new `materialsApi` calls on the stage-1 endpoints. The Materials page keeps its query state in the URL and asks the server for one page at a time. Estimate and template editors stop holding the catalog: a `useMaterialCatalog` hook resolves only the materials on screen (`GET /materials/resolve`) and remembers anything picked; a `MaterialSearchDropdown` (modelled on `PropertySearchDropdown`) searches the server as you type. "(removed)" is decided from the resolve map, which includes hidden and retired items.

**Tech Stack:** React 18 + TypeScript + React Router 7 + Vite + Tailwind 4; Vitest + Testing Library.

**Spec:** [2026-10-15-shared-material-catalog-design.md](2026-10-15-shared-material-catalog-design.md) §7 (decisions §11 are final). **Depends on:** [stage 1](2026-10-15-shared-material-catalog-stage1-plan.md) — its "As built" notes define the API this plan uses.

## Global Constraints

- **TDD is mandatory** for every `.ts`/`.tsx` behavior change: failing test first. Styling-only and copy-only changes (Task 13) need no new test.
- **Plain Vitest assertions, not jest-dom** (house rule): `toBeTruthy()` / `toBeNull()` / `.disabled` / `.getAttribute()` / `.textContent`.
- **Gates per task:** `npm test -- <named files>`, `npm run typecheck`, `npm run lint`. Never the full suite. `npm run build` doesn't type-check.
- **Mock style:** tests mock `../src/api/resources` and `../src/api/client` with `vi.mock`, as `tests/MaterialsPageLoadStandard.test.tsx` does.
- **Commits need the user's explicit approval** (or their `/commit`). The portal is its own git repo. Never push; never `/release`.
- **Ship order:** stage 1 (platform) and this stage ship together through `/release app`. Until then the platform keeps the old bare-array `GET /materials` and `POST /materials/load-standard` working; this stage stops calling both, so stage 6 can remove them.
- **Roles:** cost, price, duplicate, upload, hide/show, reset and the category opt-in are Owner/Admin in the UI as on the server. Members see the Materials page read-only (they can still rename or describe a company material through Edit). The role check stays the existing inline `getCurrentUser()?.role` pattern.
- **Server error shapes** (stage 1): a refusal for a standard's structure is `409 {detail: {message, action: "duplicate"}}`; a name clash is `409 {detail: {message, conflict: {id, name, source}}}`; deleting a standard or an in-use material is `409 {detail: {message, action: "hide"}}`. Show `detail.message` (or the conflict's name) — never "[object Object]".

## Shared interfaces (Tasks 1–3, used by everything after)

```ts
// src/types/api.ts
export interface EffectiveMaterialSize {
  size: string; unit: string | null; unit_name: string | null;
  cost: number; price: number; standard_cost: number | null;
  overridden: boolean; price_recorded: boolean;
}
export interface EffectiveMaterial {
  _id: string; id: string; name: string; description: string | null;
  category: string | null; category_name: string | null;
  sizes: EffectiveMaterialSize[]; company: string;
  source: "standard" | "custom" | "detached";
  standard_id: string | null; hidden: boolean; retired: boolean;
}
export interface MaterialPage { items: EffectiveMaterial[]; total: number; page: number; page_size: number; }
// MaterialCategory gains: standard_key?: string | null; include_standard?: boolean

// src/api/resources.ts — materialsApi additions
page(companyId, q: MaterialListQuery): Promise<MaterialPage>       // GET /materials?…
get(id): Promise<EffectiveMaterial>
resolve(companyId, ids: string[]): Promise<Record<string, EffectiveMaterial>>
lookupNames(companyId, names: string[]): Promise<Record<string, string | null>>
setPricing(id, sizes: { size: string; cost?: number | null; price?: number | null }[])
duplicate(id, name?: string): Promise<EffectiveMaterial>
setVisibility(id, hidden: boolean): Promise<EffectiveMaterial>
resetToStandard(id): Promise<EffectiveMaterial>
resetStandard(companyId, { clear_overrides, remove_unused_custom })
// list() and loadStandard() are removed once nothing calls them (Task 12).
// materialCategoriesApi additions
setIncludeStandard(id, on: boolean)                   // PATCH /material-categories/{id}
setAllStandard(companyId, on: boolean)                // POST /material-categories/standard

// src/lib/materialListQuery.ts
export interface MaterialListQuery {
  search: string; category: string; source: "all" | "standard" | "custom";
  visibility: "visible" | "hidden" | "all"; sort: "name" | "-name" | "price" | "-price";
  page: number; pageSize: number;
}
parseMaterialListQuery(params: URLSearchParams): MaterialListQuery
toSearchParams(q: MaterialListQuery): URLSearchParams      // defaults omitted
toApiParams(q: MaterialListQuery): Record<string, string>  // page/page_size always sent

// src/lib/materialBadges.ts
materialBadge(m: EffectiveMaterial): { label: string; tone: "standard" | "priced" | "mine" | "copy" | "hidden" }

// src/hooks/useDebouncedValue.ts — useDebouncedValue<T>(value: T, delayMs = 300): T
// src/components/common/Pagination.tsx — <Pagination page total pageSize onPage />
// src/hooks/useMaterialCatalog.ts
useMaterialCatalog(companyId, ids: string[]): {
  byId: Map<string, EffectiveMaterial>; loaded: boolean;
  remember(m: EffectiveMaterial): void; search(text: string): Promise<EffectiveMaterial[]>;
}
```

---

# Phase A — Foundations

### Task 1: Types and API client

**Files:** `src/types/api.ts`, `src/api/resources.ts`. **Test:** `tests/materialsApi.test.ts` (new).

- [ ] **Failing tests:** each new call sends the right method, URL and body (mock `apiRequest`): `page` serializes only the given params and always `page`/`page_size`; `resolve` joins ids with commas and short-circuits to `{}` for none; `lookupNames` POSTs `{names}`; `setPricing` PATCHes `/materials/{id}/pricing`; `duplicate` POSTs `{name}` only when given; `setVisibility`, `resetToStandard`, `resetStandard`, `setIncludeStandard`, `setAllStandard`.
- [ ] Implement. Gates. **Commit (ask):** `feat: shared material catalog API client`.

### Task 2: `useDebouncedValue` and `Pagination`

**Files:** `src/hooks/useDebouncedValue.ts`, `src/components/common/Pagination.tsx`. **Tests:** `tests/useDebouncedValue.test.tsx`, `tests/Pagination.test.tsx`.

- [ ] **Failing tests:** the value settles after the delay with fake timers and resets the timer on change; Pagination shows "1–50 of 230", disables Previous on page 1 and Next on the last page, calls `onPage`, renders nothing for one page.
- [ ] Implement. Gates. **Commit (ask):** `feat: debounced value hook and pagination control`.

### Task 3: List query and badges

**Files:** `src/lib/materialListQuery.ts`, `src/lib/materialBadges.ts`. **Tests:** `tests/materialListQuery.test.ts`, `tests/materialBadges.test.ts`.

- [ ] **Failing tests:** parse → serialize round-trips; unknown or invalid values fall back to defaults (page < 1, page size > 100, bad sort); defaults stay out of the URL; a search change resets page to 1 (helper `withFilter`). Badges: standard untouched → "Standard"; standard with any overridden size → "Standard · priced"; custom → "Mine"; detached → "Copy of standard"; hidden wins over all.
- [ ] Implement. Gates. **Commit (ask):** `feat: material list query state and badges`.

# Phase B — Materials page

### Task 4: Server-driven list

**Files:** `src/pages/MaterialsPage.tsx`. **Test:** `tests/MaterialsPageServerList.test.tsx` (new); update `tests/MaterialsPageDiffSave.test.tsx`, `tests/CatalogMobileReadOnly.test.tsx` mocks.

- [ ] **Failing tests:** on mount it asks `materialsApi.page` with the URL's query; typing in search asks again once after the debounce, with page 1, and writes `?q=` to the URL; category / Source / Show hidden / sort change the query; the pager asks for page 2; the total shows; `?open=<id>` calls `materialsApi.get` and opens that row's dialog even when it isn't on the page; `portal:materials:changed` refetches the current page.
- [ ] Implement: replace `materials` + client-side filtering with `page` results; category options from `materialCategoriesApi.list`; Source select (All / Standard / My materials); "Show hidden" toggle; sort select; `Pagination`; empty states ("No materials match" vs "No materials yet — turn on standard categories in Settings").
- [ ] Gates. **Commit (ask):** `feat: paged, searchable materials page`.

### Task 5: Badges, standard-item editing, Members read-only

**Files:** `src/pages/MaterialsPage.tsx` (+ a `StandardPricingDialog` extracted to `src/components/materials/` if the page grows). **Test:** `tests/MaterialsPageStandardEdit.test.tsx` (new).

- [ ] **Failing tests:** each row shows its badge; opening a standard item shows name, description, category and sizes read-only, with cost/price inputs per size and the standard cost as a hint; saving sends only changed sizes to `setPricing`; the per-size ↺ sends `{size, cost: null, price: null}`; "Duplicate to edit" calls `duplicate` then opens the copy; a Member sees no cost/price inputs, no Duplicate and no Upload; a company material's dialog still saves through `update` (diff save unchanged); a 409 shows its `detail.message`.
- [ ] Implement. Gates. **Commit (ask):** `feat: standard material pricing and duplicate on the materials page`.

### Task 6: Row and page menus

**Files:** `src/pages/MaterialsPage.tsx` (row and page menus move onto the shared `ActionsMenu`). **Tests:** `tests/MaterialsPageMenus.test.tsx` (new); `tests/MaterialsPageLoadStandard.test.tsx` is replaced by it (Load Standard goes away).

- [ ] **Failing tests:** row menu — Hide / Show (`setVisibility`), Reset to standard (only on a priced or hidden standard; `resetToStandard`), Duplicate, Delete (company materials only; a 409 shows its message and offers Hide); page menu — Upload CSV, Reset standard materials (modal with "Clear my prices and hides" and "Remove my unused materials"; calls `resetStandard`; reports cleared / removed / kept-in-use / hidden-by-name), Delete all my materials (reports skipped in-use names); Owner/Admin only for each except Edit; a hide of a standard whose name a company material holds shows the server's conflict.
- [ ] Implement. Gates. **Commit (ask):** `feat: hide, show, reset and duplicate on the materials page`.

# Phase C — Settings and onboarding

### Task 7: Category opt-in in Settings

**Files:** `src/components/settings/MaterialCategoriesTab.tsx`. **Test:** extend `tests/MaterialCategoriesTab.test.tsx`.

- [ ] **Failing tests:** a "Standard materials" column with a toggle on standard-keyed rows (a dash on the company's own); toggling calls `setIncludeStandard` and refreshes; header menu "Turn on all standard materials" / "Turn off all" calls `setAllStandard`; a non-empty `hidden_for_name` is reported ("Hidden because you have your own: …"); Delete is disabled on standard-keyed rows with a tooltip; Members see the toggles read-only.
- [ ] Implement. Gates. **Commit (ask):** `feat: standard material opt-in per category`.

### Task 8: Onboarding opts in

**Files:** `src/pages/OnboardingPage.tsx`, `src/components/onboarding/CompletionStep.tsx` (copy). **Tests:** extend `tests/CsvUploadStep.test.tsx` or the onboarding page test.

- [ ] **Failing tests:** "Use 3Maples standard materials" (desktop checkbox and phone button) calls `materialCategoriesApi.setAllStandard(companyId, true)`, not `materialsApi.loadStandard`.
- [ ] Implement; completion copy says the standard list is turned on (not copied). Gates. **Commit (ask):** `feat: onboarding turns on the standard materials`.

# Phase D — Estimates and templates

### Task 9: `useMaterialCatalog`

**Files:** `src/hooks/useMaterialCatalog.ts`. **Test:** `tests/useMaterialCatalog.test.tsx`.

- [ ] **Failing tests:** resolves the given ids once (batched, ≤ 200 per call), only new ids when the list grows; `loaded` false until the first resolve settles (and stays false after a failed one, so nothing is called "removed"); `remember` adds a picked material; `search` asks `page` with `search` and page size 10.
- [ ] Implement. Gates. **Commit (ask):** `feat: on-screen material catalog hook`.

### Task 10: `MaterialSearchDropdown`

**Files:** `src/components/common/MaterialSearchDropdown.tsx`. **Test:** `tests/MaterialSearchDropdown.test.tsx`.

- [ ] **Failing tests:** opening shows the first 10 visible materials; typing 2+ characters searches after the debounce; each option shows name, category and its sizes; choosing one calls `onChange(material)`; the trigger shows the selected material's name from the catalog, else the line's snapshot name, tagged "(removed)" only when the catalog has loaded and doesn't know the id (`snapshotFallbackLabel` semantics); a hidden or retired selected material shows "(hidden)" / "(retired)"; read-only mode renders text.
- [ ] Implement with the `SearchableSelect` styling props (`triggerClassName`, `ariaLabel`, `placeholder`). Gates. **Commit (ask):** `feat: server-searched material picker`.

### Task 11: Editors stop loading the catalog

**Files:** `src/components/estimates/WorkItemInlineContent.tsx`, `MaterialsTable.tsx`, `WorkItemDialog.tsx`, `TemplateDialog.tsx`, `src/pages/NewEstimateWithActivityPage.tsx`, `src/components/settings/TemplatesTab.tsx`, `src/lib/estimateChecklist.ts` (name fallback), `src/components/common/snapshotFallbackLabel.ts` (doc). **Tests:** update `tests/MaterialsTableTotalAlignment.test.tsx`, `tests/DeletedCatalogLineLabel.test.tsx`, `tests/NewEstimateWithActivityPage.*.test.tsx` mocks, `tests/snapshotFallbackLabel.test.ts`; new `tests/WorkItemMaterialPicker.test.tsx`.

- [ ] **Failing tests:** picking a material fills name, first size, unit (`unit_name`), price and cost from the effective record (the company's prices); changing the size refills price and cost; the estimate page calls `resolve` with its lines' material ids and never `materialsApi.list`; a line whose id the catalog doesn't know is "(removed)" only after `resolve` settled; a hidden material on a line still shows its sizes.
- [ ] Implement: replace the `materials: Material[]` prop with the catalog from `useMaterialCatalog` (byId, loaded, remember, search); `MaterialsTable` renders `MaterialSearchDropdown`; the size select reads the resolved record. Gates. **Commit (ask):** `feat: estimate and template editors search the material catalog`.

### Task 12: Inventory gaps

**Files:** `src/lib/estimateInventoryGaps.ts`, `src/components/estimates/AddMaterialGapDialog.tsx`, `src/pages/NewEstimateWithActivityPage.tsx`, `src/api/resources.ts` (drop `list` and `loadStandard`). **Tests:** update `tests/estimateInventoryGap*.test.ts`, `tests/AddMaterialGapDialog*.test.tsx`.

- [ ] **Failing tests:** gap suppression takes the names `lookupNames` resolved (one call per estimate load, not per keystroke) instead of the full catalog; "Choose existing" in the gap dialog uses `MaterialSearchDropdown` and resolves the gap with the effective prices; the dialog's create mode prices from the company's real `material_markup` (it was hardcoded to 10); after creating, the new material is remembered by the catalog, no list refetch.
- [ ] Implement; remove `materialsApi.list` / `loadStandard` once a search shows no caller. Gates. **Commit (ask):** `feat: inventory gaps use the material catalog`.

### Task 13: Financial tab copy

**Files:** `src/components/settings/FinancialTab.tsx`. Copy only (no TDD); update `tests/FinancialTab.test.tsx` only if it pins the text.

- [ ] Material Markup help: "Applies to every standard material you haven't priced yourself. Your own materials keep the price you saved." Gates. **Commit (ask):** `docs: explain material markup on standard materials`.

# Phase E — Verification

### Task 14: In the browser

- [ ] Start the `platform` and `portal` preview servers (`.claude/launch.json`); the user signs in in the browser pane (Claude never enters credentials).
- [ ] Check: Materials page search / filters / sort / pager / URL state; a standard item's pricing, reset, duplicate, hide/show; Members read-only; Settings category toggles; an estimate's material picker and "(removed)" label; a gap's "Choose existing". Console clean; screenshots shared.
- [ ] **Needs standard materials in the database the local platform reads** — see Decision 1.

## Done when

- Every task's named tests pass; `npm run typecheck` and `npm run lint` are clean.
- No portal code calls `materialsApi.list` or `materialsApi.loadStandard`.
- Task 14 is checked in the browser, or its blocker is reported.
- Nothing is pushed.

## Decisions needed before Task 14

1. **Data for the browser check.** The local platform reads the Dev cluster, which has no standard materials yet. Options: (a) run `scripts/seed_standard_materials.py --apply` against Dev (adds the global list; no company sees it until it opts in), then opt one Dev test company in from Settings; or (b) skip the browser check until stage 3. Recommended: (a), after its dry run.
