# Work Item Template Feature — Implementation Plan

## Context

Users currently build estimates from scratch or via Maple (AI), which researches and assembles materials/people for each work item every time. Many jobs reuse the same combinations of materials and people (e.g., "Paver Patio Installation" always needs the same base materials and labor roles). Work Item Templates let users save these combinations once and reuse them — both manually in the estimate form and automatically when Maple matches a template to a job scope. This reduces repetitive data entry and improves Maple's accuracy by leveraging company-specific knowledge.

---

## Phase 1: Backend Model & CRUD

### 1.1 New Model — `platform/models/work_item_template.py`

```python
class TemplateMaterialItem(BaseModel):
    material: str             # Material ID reference
    name: Optional[str]       # Snapshot
    unit: Optional[str]       # Snapshot
    size: Optional[str]       # Snapshot
    price: float
    cost: float = 0.0

class TemplateLabourItem(BaseModel):
    labour: str               # Labour ID reference
    name: Optional[str]       # Snapshot
    unit: Optional[str]       # Snapshot
    price: float
    cost: float = 0.0

class WorkItemTemplate(Document):
    title: str                          # required
    description: str                    # required
    company: PydanticObjectId           # company-scoped
    materials: List[TemplateMaterialItem] = []
    labours: List[TemplateLabourItem] = []
    created_by: Optional[str] = None
    created_by_email: Optional[str] = None
    embedding: Optional[List[float]] = None  # for AI matching
    created_at / updated_at              # standard timestamp pattern
```

- No `quantity` on template items — quantities are job-specific
- No equipment — per requirements
- No subtotals — can't calculate without quantities
- `embedding` stores vector of `title + " " + description` for semantic matching

### 1.2 Registration
- Add to `platform/models/__init__.py` (import + `model_rebuild()`)
- Add to `platform/database.py` `document_models` list
- Add audit enums: `TEMPLATE_CREATE`, `TEMPLATE_UPDATE`, `TEMPLATE_DELETE` + `WORK_ITEM_TEMPLATE` resource type

### 1.3 New Router — `platform/routers/work_item_templates.py`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/work-item-templates?company={id}` | List templates for company |
| `POST` | `/work-item-templates/` | Create template (+ generate embedding) |
| `GET` | `/work-item-templates/{id}` | Get single template |
| `PUT` | `/work-item-templates/{id}` | Update template (+ regenerate embedding) |
| `DELETE` | `/work-item-templates/{id}` | Delete template |
| `POST` | `/work-item-templates/from-estimate` | Create from an estimate's job item |

**`from-estimate` endpoint** accepts `{ estimate_id, job_item_index, title, description? }`:
- Fetches estimate, validates company access
- Copies materials/labours from `job_items[index]` dropping quantities
- Defaults description to job item description if not provided
- Generates embedding, inserts template

Embedding generation reuses `generate_embedding()` from `platform/services/work_item_summary.py`.

### 1.4 Register router in `platform/routers/__init__.py` and `platform/main.py`

### 1.5 Tests — `platform/tests/test_work_item_templates.py`
- CRUD operations, validation, company scoping
- `from-estimate` endpoint: copies materials/labours without quantities

---

## Phase 2: Frontend Templates CRUD

### 2.1 Types — `portal/src/types/api.ts`
Add `TemplateMaterialItem`, `TemplateLabourItem`, `WorkItemTemplate` interfaces.

### 2.2 API Client — `portal/src/api/workItemTemplates.ts`
Standard CRUD methods + `createFromEstimate()`.

### 2.3 New Page — `portal/src/pages/WorkItemTemplatesPage.tsx`
- Table: Title, Description, Materials count, People count, Created date
- Search/filter bar
- Create/Edit modal with:
  - Title (required), Description (required)
  - Material picker (from company catalog, no quantity field)
  - People picker (from company catalog, no quantity field)
- Delete confirmation modal
- Follow patterns from `PeoplePage.tsx` / `MaterialsPage.tsx`

### 2.4 Navigation & Routing
- Add `{ path: "/templates", label: "Templates", icon: ClipboardList }` to `navItems` in `portal/src/components/Layout/PortalLayout.tsx` (line 127)
- Add `<Route path="/templates" element={<WorkItemTemplatesPage />} />` in `portal/src/App.tsx`

### 2.5 "Save as Template" on Estimate Details
- Add button per job item in `portal/src/pages/EstimateDetailsPage.tsx`
- Small modal: Title (pre-filled), Description (pre-filled from job item), read-only preview of materials/people
- Calls `POST /work-item-templates/from-estimate`

### 2.6 Tests — `portal/tests/workItemTemplates.test.ts`

---

## Phase 3: Manual Template Usage in Estimates

### 3.1 Template Picker in `portal/src/components/common/EstimateForm.tsx`
- When adding a new work item, offer: "Start from scratch" or "Start from template"
- "Start from template" opens searchable dropdown/modal listing company templates
- On select: pre-fill materials (quantity=0), labours (quantity=0), description from template
- User fills in quantities and can modify/add/remove items

### 3.2 Tests

---

## Phase 4: AI Agent Integration (Maple)

### 4.1 Template Matching Service — `platform/services/work_item_template_matching.py`

```python
async def match_templates_for_scopes(
    scopes: List[ArchitectScope],
    company_id: PydanticObjectId,
    similarity_threshold: float = 0.75,
) -> Dict[int, WorkItemTemplate]:
```

- Fetch all templates with embeddings for the company
- For each scope, embed `scope_name + " " + scope_description`
- Cosine similarity against all template embeddings
- Return best match per scope if above threshold
- Client-side comparison (template count per company is small, <100)

### 4.2 Pipeline Integration — `platform/agents/estimate/service.py`

In `_run_pipeline()` (line 1451), after Step 1 architect decomposition:

```python
# Step 1.5 — Template matching
template_matches = await match_templates_for_scopes(decomposed.scopes, company_id)
```

Modify the per-scope loop (line 1454): for matched scopes, skip Steps 2+3 (vector retrieval + research) and build job items directly from template materials/labours. For unmatched scopes, proceed with existing pipeline unchanged.

### 4.3 Quantity Assignment via LLM
Template-matched items have materials/labours but no quantities. Pass them as context to `_extract_estimate_with_llm()` with instructions to assign quantities based on the job description.

### 4.4 Prompt Updates
- `platform/prompts/estimate_generation.py`: Add section for handling template-prefilled items (assign quantities, don't invent new line items for matched scopes)

### 4.5 ReAct Tool (Optional Enhancement)
- Add `lookup_templates` tool to `platform/agents/estimate/tools.py`
- Update ReAct system prompt to mention templates should be checked first

### 4.6 Tests — `platform/tests/test_work_item_template_matching.py`

---

## Implementation Order

1. **Phase 1** — Backend model + CRUD (foundation for everything)
2. **Phase 2** — Frontend templates page + save-from-estimate
3. **Phase 3** — Template picker in estimate form
4. **Phase 4** — AI agent integration

Each phase is independently deployable and testable.

---

## Key Files to Modify

| File | Change |
|------|--------|
| `platform/models/work_item_template.py` | **New** — model |
| `platform/models/__init__.py` | Register model |
| `platform/models/audit_log.py` | Add enums |
| `platform/database.py` | Register in Beanie init |
| `platform/routers/work_item_templates.py` | **New** — CRUD router |
| `platform/routers/__init__.py` | Export router |
| `platform/main.py` | Mount router |
| `platform/services/work_item_template_matching.py` | **New** — matching service |
| `platform/agents/estimate/service.py` | Insert template matching in `_run_pipeline()` |
| `platform/prompts/estimate_generation.py` | Template-aware generation instructions |
| `portal/src/types/api.ts` | Template types |
| `portal/src/api/workItemTemplates.ts` | **New** — API client |
| `portal/src/pages/WorkItemTemplatesPage.tsx` | **New** — templates page |
| `portal/src/pages/EstimateDetailsPage.tsx` | "Save as Template" button |
| `portal/src/components/common/EstimateForm.tsx` | Template picker for new work items |
| `portal/src/components/Layout/PortalLayout.tsx` | Nav item |
| `portal/src/App.tsx` | Route |

## Verification

1. **Backend CRUD**: Create/list/update/delete templates via API; create from estimate job item
2. **Frontend CRUD**: Navigate to Templates tab, create/edit/delete, verify material/people pickers
3. **Save from Estimate**: Open an estimate, save a job item as template, verify it appears in templates list
4. **Manual Usage**: Create new estimate, add work item from template, verify materials/people pre-filled with quantity=0
5. **AI Integration**: Create templates, then generate an estimate with Maple for a matching job — verify matched scopes use template materials/people with AI-assigned quantities; unmatched scopes follow normal flow
6. **Run related tests**: `./run_tests.sh tests/test_work_item_templates.py` and `npm test -- workItemTemplates`
