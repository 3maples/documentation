# Work Item Template — size-based scaling

> Note: per project convention, after approval this file should be moved to `documentation/development/plans/work-item-template-size-scaling.md`. Plan mode restricts edits to the prescribed path during the planning phase only.

## Context

Today, a Work Item template captures a fixed bundle of materials and activities — when a user picks "Use Template" on an estimate, the items are inserted at exactly the quantities/efforts stored on the template. That forces the user to either keep many near-duplicate templates (one per job size) or to manually edit every line after insertion.

This change makes templates size-aware. A template now carries a baseline size + unit (e.g. "1000 sq ft"), the Use Template dialog asks the user for the actual job size, and a simple linear scaling factor (`new / baseline`) is applied to every material quantity and labour effort before the items land in the estimate draft. The user still gets a chance to fine-tune in the Work Item dialog before saving.

Decisions from clarifying questions + follow-up:
- **Per-template opt-in**: the New/Edit Template dialog includes a checkbox **"Include baseline size"**. Unchecked = template has no baseline (size/unit hidden, scaling never applies). Checked = size + unit inputs reveal and become required. Legacy templates load with the checkbox unchecked, so they keep working untouched.
- **Use Template dialog adapts dynamically**: the size input is only rendered when the *currently selected* template has a baseline. Selecting a non-baselined template removes the input; selecting a baselined one shows it (with the template's unit beside it).
- **Scaling scope**: `MaterialItem.quantity` and `ActivityItem.effort` only. We deliberately do **not** scale `ActivityItem.effort_card_items[].effort` or any unmatched-* rows in this iteration — see Caveats below.
- **Unit UX (when shown)**: inline next to the size input ("Size: [____] sq ft").

## Supported units

A new `TemplateSizeUnit` enum is added in both backend and frontend with exactly four values:

```
"square feet" | "square yard" | "linear feet" | "linear yard"
```

Display labels (frontend only): `sq ft`, `sq yd`, `ln ft`, `ln yd`.

## Backend changes

### `platform/models/template.py`
Add to the `Template` document:
```python
size: Optional[float] = None
unit: Optional[Literal["square feet", "square yard", "linear feet", "linear yard"]] = None
```
- Both `None` ⇒ template has no baseline (the "checkbox unchecked" state). Legacy documents in MongoDB round-trip cleanly because Beanie defaults missing fields to `None`.
- A Pydantic `model_validator` enforces: either `size is None && unit is None`, or `size > 0 && unit is not None`. Mixed states (`size=5, unit=None` or `size=None, unit="square feet"`) → 422.

### `platform/routers/templates.py`
- The create / update payloads accept the two new fields. No additional logic — the `Template(**payload)` call covers it once the model validator is in place.

### `platform/tests/test_template_api.py`
Add tests for:
- POST/GET roundtrip with `size=1000, unit="square feet"`.
- POST without `size`/`unit` → 200 (no-baseline template).
- POST with `size=1500` and missing unit → 422.
- POST with `unit="square feet"` and missing/null size → 422.
- POST with `size=-1` → 422.
- PUT toggling a template from no-baseline to baseline (and back) keeps materials/activities intact.

No estimate-side backend changes — scaling happens client-side before the work item draft is opened.

## Frontend changes

### `portal/src/types/api.ts`
- Add `export type TemplateSizeUnit = "square feet" | "square yard" | "linear feet" | "linear yard"`.
- Extend the `Template` interface with `size?: number` and `unit?: TemplateSizeUnit | null`.

### `portal/src/lib/templates.ts` (new helpers + edits)
- Extend `TemplatePayloadShape` with `size: number` and `unit: TemplateSizeUnit | null`.
- Update `workItemToTemplatePayload(name, workItem, companyId, source?, size, unit)` to thread the new params through. (Add as additional named params so existing call sites that pass `size=0, unit=null` continue to work.)
- Add a new pure helper:
  ```ts
  export function scaleWorkItem(wi: WorkItemV2, factor: number): WorkItemV2
  ```
  - Clones via `structuredClone`.
  - For each `material`: `quantity = round(material.quantity * factor, 4)`.
  - For each `activity`: `effort = round(activity.effort * factor, 4)`.
  - `effort_card_items` and unmatched rows are passed through unchanged.
  - If `factor === 1` the function still returns a fresh clone (caller relies on identity-fresh draft state).
- Add `getScaleFactor(baseline: number, target: number): number` returning `1` when `baseline <= 0 || target <= 0` (legacy + invalid input shortcut).
- Add a frontend constant `TEMPLATE_SIZE_UNITS` with `{ value, label }` pairs for use by both dialogs.

### `portal/src/components/estimates/TemplateDialog.tsx`
- Add three state hooks: `hasBaseline: boolean`, `size: number | ""`, `unit: TemplateSizeUnit | "")`.
- Render in this order under the name input:
  1. Checkbox: **"Include baseline size"** (defaults `false` for new templates, seeded from `initialSize != null` when editing).
  2. *When checked only*, a single row containing:
     - "Size" — `NumericInput` (already used in MaterialsTable).
     - "Unit" — native `<select>` populated from `TEMPLATE_SIZE_UNITS`.
  3. The existing `WorkItemInlineContent`.
- Toggling the checkbox off clears `size` / `unit` local state so unintentional values aren't persisted.
- Validation extends `canSave`:
  - If `hasBaseline` is true → `size > 0` and `unit !== ""` are required.
  - If `hasBaseline` is false → no extra requirement (existing rules apply).
- `onSave` signature becomes `(name, workItem, size: number | null, unit: TemplateSizeUnit | null)` — passing `null`/`null` when the checkbox is unchecked.
- Add `initialSize` and `initialUnit` props alongside `initialName`; the checkbox seeds to `initialSize != null && initialUnit != null`.
- Update the call site that mounts `TemplateDialog` (located via `grep -n "TemplateDialog" portal/src`) to forward the new args into `workItemToTemplatePayload`.

### `portal/src/components/estimates/UseTemplateDialog.tsx`
- Add state: `targetSize: number | ""`. Reset whenever the selected template changes.
- Compute `selectedHasBaseline = selectedTemplate?.size != null && selectedTemplate.size > 0 && !!selectedTemplate.unit`.
- New dynamic layout — the size row is conditionally rendered above the search bar **only when `selectedHasBaseline` is true**:
  ```
  ┌──────────────────────────────────────┐
  │ Size: [        ] {selected unit}     │   ← shown only after a baselined
  │                                      │     template is selected
  │ ─────────────────────────────────────│
  │ ○ Patio Install      (500 sq ft)     │
  │ ● Mulch Refresh                      │   ← no baseline — size row hidden
  │ ○ Spring Cleanup     (1000 sq ft)    │
  └──────────────────────────────────────┘
  ```
- In each radio row, append the template's baseline next to the name when present (e.g. "Patio Install — 500 sq ft"); show no suffix for templates without baseline.
- `handleConfirm`:
  ```ts
  const factor = selectedHasBaseline
    ? getScaleFactor(chosen.size!, Number(targetSize) || 0)
    : 1;
  onSelect(chosen, factor);
  ```
- Update prop signature: `onSelect: (template: Template, scaleFactor: number) => void`.
- OK button disabled when `selectedHasBaseline && (!targetSize || targetSize <= 0)`. Always enabled for non-baselined selections.

### `portal/src/pages/NewEstimateWithActivityPage.tsx`
- `openTemplateWorkItemDialog` accepts the new `scaleFactor` arg and applies it:
  ```ts
  const openTemplateWorkItemDialog = (template: Template, scaleFactor: number) => {
    const base = templateToWorkItem(template);
    const scaled = scaleFactor !== 1 ? scaleWorkItem(base, scaleFactor) : base;
    setWorkItemDraft(scaled);
    setWorkItemEditIndex(null);
    setWorkItemDialogError("");
    setIsUseTemplateOpen(false);
  };
  ```

### Frontend tests
- New: `portal/src/lib/__tests__/templates.test.ts`
  - `getScaleFactor(1000, 1500) === 1.5`
  - `getScaleFactor(0, 1500) === 1` (legacy)
  - `getScaleFactor(1000, 0) === 1` (no target)
  - `scaleWorkItem` multiplies material quantities, activity effort; leaves `effort_card_items`, unmatched rows, and prices/rates unchanged.
- Update: `UseTemplateDialog` test file (if present) — assert size input is **hidden** until a baselined template is selected, **revealed** once one is, **hidden again** when switching to a non-baselined template, OK disabled until size provided for baselined picks, factor=1 path for non-baselined picks.
- Update: `TemplateDialog` test file — assert checkbox toggles the size/unit row, validation gates Save on (size>0 + unit) only when checked, payload sends nulls when unchecked, editing a baselined template seeds the checkbox to `true`.

(If those test files don't exist yet, create them following the patterns of the existing dialog tests in `portal/src/components/estimates/__tests__/`.)

## Caveats / explicit non-goals

- **Activity vs effort-card drift**: scaling `activity.effort` without scaling `effort_card_items[].effort` means the breakdown will no longer sum to the total. This is intentional for v1 — the Work Item dialog already reconciles these on edit, and the user gets a chance to review before saving the estimate. Worth a follow-up if it confuses users.
- **Unmatched rows** (manual fallback materials/labour) are not scaled — they're rare and represent items the agent couldn't auto-match, often with looser semantics.
- **No estimate-level scaling re-application**: once items are inserted into the estimate, changing the size again means re-running Use Template (i.e. the scaling factor is not stored on the work item).
- **Money fields untouched**: `price`, `cost`, `rate` are per-unit values, not totals — they correctly stay constant as quantity scales.

### Known low-severity items

- **`TemplateDialog.tsx` unit cast**: the `useState<TemplateSizeUnit | "">` generic and the `e.target.value as TemplateSizeUnit | ""` cast in the `<select>` `onChange` are both required (the `<select>` value comes back as plain `string`). Logged as a code-review LOW; not actionable but noted here so a future reader doesn't try to "simplify" the cast away.

## Critical files

- `platform/models/template.py` — add `size`, `unit`.
- `platform/routers/templates.py` — validation only.
- `platform/tests/test_template_api.py` — extend.
- `portal/src/types/api.ts` — `TemplateSizeUnit`, extend `Template`.
- `portal/src/lib/templates.ts` — `scaleWorkItem`, `getScaleFactor`, `TEMPLATE_SIZE_UNITS`, payload extension.
- `portal/src/components/estimates/TemplateDialog.tsx` — size + unit inputs.
- `portal/src/components/estimates/UseTemplateDialog.tsx` — size input + dynamic unit, scale factor passthrough.
- `portal/src/pages/NewEstimateWithActivityPage.tsx` — apply scaling in `openTemplateWorkItemDialog`.
- (TBD via grep) the page that mounts `TemplateDialog` for create/edit — forward new fields to `workItemToTemplatePayload`.

## Verification

1. **Backend**:
   ```bash
   cd platform && source .venv/bin/activate
   ./run_tests.sh tests/test_template_api.py
   ```
2. **Frontend**:
   ```bash
   cd portal && npm test -- templates
   cd portal && npm test -- TemplateDialog UseTemplateDialog
   ```
3. **End-to-end manual** (`npm run dev` + `uvicorn main:app --reload`):
   - Create a new template "Patio v1", **check** "Include baseline size", set size `1000`, unit `square feet`, add two materials (10 bags, 5 ea) and one activity (8 hr effort). Save.
   - Create a second template "Mulch Basic" without checking the baseline box. Save.
   - Open a draft estimate → Use Template → confirm no size field is shown initially. Pick "Patio v1" → size field appears with "sq ft" suffix. Enter `1500`, click OK. Confirm the work item dialog opens with material quantities 15 and 7.5, and activity effort 12 hr. Save and verify estimate totals.
   - Re-open Use Template → pick "Mulch Basic" → confirm size field is hidden. OK should be enabled and insertion happens at 1.0x.
   - Switch selection between "Patio v1" and "Mulch Basic" → size field should appear/disappear accordingly; targetSize resets between switches.
   - Edit "Patio v1" → uncheck the baseline checkbox → save. Use Template again → "Patio v1" no longer shows a baseline next to its name and the size field stays hidden when selected.
   - Re-edit "Patio v1" → re-check the box, set size `2000`. Save. Use Template with size `1000` → factor 0.5x, quantities halve.
   - Verify backend rejection: `curl POST /templates` with `size=500, unit=null` → 422.
