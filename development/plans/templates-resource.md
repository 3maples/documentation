# Templates Resource

## Context

Estimates today are composed of Work Items (description + division + materials + activities + pricing knobs). Users frequently rebuild the same kind of work item across estimates and want a reusable catalog. This change introduces a **Template** resource: a standalone, named Work Item that lives in its own collection and gets its own left-nav entry, list page, and create/edit dialog.

This iteration is **CRUD only**. A Template stores everything `WorkItemV2` stores plus a `name`. The dialog reuses the existing Work Item form (`WorkItemInlineContent`) verbatim with the only addition being a Template Name field at the top. "Apply template to an estimate" is intentionally out of scope and tracked as a follow-up.

Decisions captured up-front:
- **Field parity**: Full Work Item parity (description, division, recurring/recurrence, materials, activities, profit_margin, overhead_allocation, labor_burden, tax). No field gating.
- **Name uniqueness**: Unique per company (enforced by Mongo compound index). Duplicate action suffixes `" (copy)"` and increments if needed.
- **Form pattern**: Dialog (matches user request explicitly), reusing `WorkItemDialog.tsx` with a Template Name field added above `WorkItemInlineContent`.

---

## Backend

### New model — `platform/models/template.py`

Beanie `Document` named `templates`:

```python
class Template(Document):
    name: str                      # required, min_length=1
    description: str = ""          # same field as JobItem.description — single source of truth
    division: Optional[str] = None
    recurring: bool = False
    recurrence: Optional[RecurrenceSchedule] = None
    materials: List[MaterialItem] = []
    activities: List[ActivityItem] = []
    unmatched_materials: List[UnmatchedMaterialItem] = []
    unmatched_labours: List[UnmatchedLabourItem] = []
    unmatched_activities: List[UnmatchedActivityItem] = []
    profit_margin: float = 15.0
    overhead_allocation: float = 0.0
    labor_burden: float = 0.0
    tax: float = 0.0
    sub_total: float = 0.0
    company: PydanticObjectId
    created_at / updated_at  # same pattern as Labour
```

- Reuse the embedded models already defined in `platform/models/estimate.py` (`MaterialItem`, `ActivityItem`, `RecurrenceSchedule`, `UnmatchedMaterialItem`, `UnmatchedLabourItem`, `UnmatchedActivityItem`) — **do not redefine**. Import from `models.estimate`.
- `description` is the **same** field that `JobItem.description` holds in an estimate — there is no separate template-level description. The Templates list table renders this field as its "Description" column.
- Indexes: `IndexModel([("company", ASCENDING)])` and `IndexModel([("company", ASCENDING), ("name", ASCENDING)], unique=True)`.
- `@before_event([Replace, Insert])` to bump `updated_at` (same pattern as `Labour`).

### New router — `platform/routers/templates.py`

Mirror `routers/labours.py` exactly, scoped to `/templates`. Endpoints:

- `POST /templates/` — create. Validate name not empty. Catch `DuplicateKeyError` and return 409 with a friendly message.
- `GET /templates/?company={id}` — list for company.
- `GET /templates/id/{template_id}` — fetch one.
- `PUT /templates/id/{template_id}` — update (with audit logging). Same duplicate-key handling.
- `POST /templates/id/{template_id}/duplicate` — server-side duplicate. Loads the source, computes a unique `"<name> (copy)"`, `"<name> (copy 2)"`, … name, and inserts a copy.
- `DELETE /templates/id/{template_id}` — delete one.

**Maple bulk-delete policy** does not apply directly (Maple is not gaining a Template domain in this plan), but per the project convention the HTTP router may still expose `DELETE /templates/?company={id}` for future UI workflows. Skip it for now — out of scope and YAGNI.

### Wiring

- `platform/database.py` — add `Template` to the `init_beanie` document_models list (currently line ~44 next to `Labour`).
- `platform/main.py` — `from routers import templates as templates_router`, then `app.include_router(templates_router.router, ...)` alongside the other protected routers.

### Tests — `platform/tests/test_template_api.py`

Mirror `tests/test_labour_api.py`. Cover:
- Create with minimal fields → 200, returns id.
- Create duplicate name in same company → 409.
- Create same name in *different* companies → both succeed.
- Update name to existing one → 409.
- Get list by company filters correctly.
- Duplicate endpoint produces `" (copy)"` suffix; second duplicate produces `" (copy 2)"`.
- Delete removes the doc.
- Update writes an audit log entry (assert via the existing audit-log fixtures used in `test_labour_api.py`).

---

## Frontend

### New API client — `portal/src/api/templates.ts`

Mirror `portal/src/api/estimates.ts` style. Export `templatesApi` with `list(companyId)`, `get(id)`, `create(payload)`, `update(id, payload)`, `duplicate(id)`, `delete(id)`. Payload shape: a thin wrapper around the existing `JobItemPayload` converter from `lib/workItemV2.ts` plus `name` and top-level `description`.

### New types

In `portal/src/types/api.ts` add a `Template` interface that is `WorkItemV2 & { id: string; name: string; company: string; created_at: string; updated_at: string }`. (Note: `WorkItemV2` already carries `description` — no separate field.) Export a `TemplatePayload` type for the create/update body.

### New page — `portal/src/pages/TemplatesPage.tsx`

Build by **copying `PeoplePage.tsx` as the structural skeleton**, then swapping the form contents. Specifically:

- Header: `Templates` title, search input ("Search templates…"), `New Template` button (Plus icon), `PageActionsMenu` for any future bulk actions (leave empty for now or omit).
- Desktop table columns: **Name**, **Description**, **Division**, **Actions** (the three-dot `MoreVertical` menu with Edit, Duplicate, Delete — reuse the `PeopleActionsMenu` pattern by extracting it to a shared component or by inlining a `TemplateActionsMenu` analogous to `PeopleActionsMenu`).
- Mobile card view: same compact card as `PeoplePage.tsx` adapted to Name / Description / Division.
- State: `templates`, `searchQuery`, `isFormOpen`, `editingTemplate`, `isSubmitting`, `formError`, `deleteTarget`. Same load/refresh pattern as `PeoplePage`.
- Form is **not** an inline modal copy of the People form — it is `WorkItemDialog` extended (see next section).

### Extend `WorkItemDialog` — `portal/src/components/estimates/WorkItemDialog.tsx`

Add two optional props: `nameValue?: string`, `onNameChange?: (v: string) => void`, plus an optional `title` prop (default `"Work Item"`, set to `"New Template"` / `"Edit Template"` from the page).

- When `nameValue` is provided, render a labeled `<input>` for **Template Name** at the very top of the modal body, above `<WorkItemInlineContent>`.
- `canSave` becomes `existing checks && (nameValue === undefined || nameValue.trim().length > 0)`.

This keeps a single dialog component used by both estimates (no name field) and templates (with name field). The user explicitly asked for "everything to work the same as creating a Work Item inside an Estimate" — sharing the component is the cleanest way to honor that.

If extending the existing dialog risks regressions on the Estimate flow (it currently isn't used in the main estimate path per the earlier exploration, but check before editing), prefer creating a thin `TemplateDialog.tsx` wrapper that internally renders `<Modal>` + name input + `<WorkItemInlineContent>` and reuses the same Save/Cancel footer logic.

**Recommended path: thin `TemplateDialog.tsx` wrapper** — lower blast radius, no risk to estimate flow.

### Sidebar nav — `portal/src/components/Layout/PortalLayout.tsx`

Add to the `navItems` array (after `/people`):

```ts
{ path: "/templates", label: "Templates", icon: LayoutTemplate }
```

Import `LayoutTemplate` from `lucide-react`.

### Router — `portal/src/App.tsx`

Add route under the protected layout next to People:

```tsx
<Route path="/templates" element={<TemplatesPage />} />
```

### Frontend tests — `portal/src/pages/__tests__/TemplatesPage.test.tsx`

Mirror existing PeoplePage test patterns. Cover:
- Renders empty state when no templates.
- Renders rows with Name / Description / Division.
- Search filter narrows the list.
- Clicking "New Template" opens the dialog with empty name and empty work-item form.
- Clicking Edit opens the dialog pre-populated.
- Clicking Duplicate calls the duplicate API and refreshes.
- Clicking Delete confirms then calls delete and refreshes.
- Save is disabled if Template Name is blank.

---

## Critical files

**New (backend):**
- `platform/models/template.py`
- `platform/routers/templates.py`
- `platform/tests/test_template_api.py`

**New (frontend):**
- `portal/src/api/templates.ts`
- `portal/src/pages/TemplatesPage.tsx`
- `portal/src/components/estimates/TemplateDialog.tsx` *(thin wrapper around `Modal` + `WorkItemInlineContent`)*
- `portal/src/pages/__tests__/TemplatesPage.test.tsx`

**Modified:**
- `platform/database.py` — register `Template` document.
- `platform/main.py` — include `templates_router`.
- `portal/src/types/api.ts` — add `Template` and `TemplatePayload`.
- `portal/src/components/Layout/PortalLayout.tsx` — add nav entry.
- `portal/src/App.tsx` — add `/templates` route.

**Reused (no change):**
- `platform/models/estimate.py` — `MaterialItem`, `ActivityItem`, `RecurrenceSchedule`, `Unmatched*Item`.
- `portal/src/components/estimates/WorkItemInlineContent.tsx` — full form body.
- `portal/src/lib/workItemV2.ts` — `WorkItemV2`, `workItemV2ToJobItemPayload`, `jobItemToWorkItemV2`.
- `portal/src/components/common/Modal.tsx` — modal shell.

---

## Verification

Backend:

```bash
cd platform && source .venv/bin/activate
./run_tests.sh tests/test_template_api.py -v
```

Frontend:

```bash
cd portal && npm test -- TemplatesPage
```

End-to-end manual:

1. `cd platform && uvicorn main:app --reload`
2. `cd portal && npm run dev`
3. Sign in, click **Templates** in the left nav → empty list page renders.
4. Click **New Template** → dialog opens with empty Template Name + the same form body used inside an Estimate. Save disabled until name and at least one material/activity (matches existing `canSave`).
5. Add name "Lawn Mowing", description, division, one material row, one activity row → Save. Row appears in the table.
6. **Edit** action → dialog pre-populated with all fields → change division → Save → row reflects update.
7. **Duplicate** action → new row appears named `Lawn Mowing (copy)`. Duplicate again → `Lawn Mowing (copy 2)`.
8. **Delete** action → confirm → row disappears.
9. Search bar filters by name + description.
10. Try to rename a template to an existing name → dialog shows the 409 error inline.

---

## Open questions / follow-ups

- Maple (the orchestrator) does **not** gain a Template domain agent in this plan. Adding "create/list/delete templates via chat" is a separate, larger piece of work.
- "Apply template to estimate" UI is the natural next plan and was deferred per the user's scope choice.
