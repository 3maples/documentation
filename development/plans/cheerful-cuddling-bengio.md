# Plan: Enhance Maple AI Estimate Creation with Activities

## Context

The Maple AI estimate generation pipeline is currently marked DEPRECATED in favor of a manual activity-based flow. The user wants to **un-deprecate and enhance** this pipeline so it produces estimates with **activities** (task breakdowns with roles and effort), matching the activity-based model already used for manual estimates.

Currently the AI pipeline outputs only materials + labours. The new workflow should:
1. Decompose requirements into Work Items (LLM)
2. Match Work Items against WorkItemSummary via vector search — reuse past estimates when found
3. For unmatched Work Items, determine materials, activities, roles, and effort (LLM + web)
4. Fuzzy match materials and roles against company inventory (~85% confidence)
5. Route unmatched items to inventory gaps (including activities with unknown roles)

### Key Design Decision: Activities Replace Labours in AI Output

The existing manual flow already treats activities as the primary labor cost mechanism (`calculate_activities_total()` adds to `labour_total`). For AI-generated estimates, the LLM should output **activities** (task + role + effort) instead of top-level labours, avoiding double-counting. The `labours` array in AI output will be empty — all labor detail flows through activities.

---

## Phase 0: Remove DEPRECATED Markers

Remove all `DEPRECATED` comments/docstrings from files involved in AI generation:

| File | Action |
|------|--------|
| `platform/agents/estimate/__init__.py` | Remove lines 1-3 DEPRECATED docstring |
| `platform/agents/estimate/service.py` | Remove lines 1-5 DEPRECATED docstring |
| `platform/agents/estimate/tools.py` | Remove lines 1-9 DEPRECATED docstring |
| `platform/agents/estimate/conversation_guide.py` | Remove lines 1-3 DEPRECATED docstring |
| `platform/prompts/estimate_generation.py` | Remove lines 1-6 DEPRECATED docstring |
| `platform/prompts/estimate_architect.py` | Remove lines 1-5 DEPRECATED docstring |
| `platform/prompts/estimate_research.py` | Remove lines 1-6 DEPRECATED docstring |
| `platform/prompts/estimate_react.py` | Remove lines 1-9 DEPRECATED docstring |
| `platform/routers/estimates.py` | Remove 14 `# DEPRECATED:` comment lines (145, 153, 174, 387, 396, 1062, 1107, 1245, 1269, 1298, 1336, 1450, 1478, 1514) |

---

## Phase 1: Model Changes

### 1A. Add `ExtractedActivityLine` to `service.py` (~line 96)

```python
class ExtractedActivityLine(BaseModel):
    name: str = ""
    role: str = ""       # Human-readable role name (e.g. "Landscaper")
    effort: float = 0.0  # Hours of effort
```

### 1B. Add `activities` field to `ExtractedJobItem` (line 98)

```python
class ExtractedJobItem(BaseModel):
    description: str = ""
    materials: List[ExtractedMaterialLine] = Field(default_factory=list)
    labours: List[ExtractedLabourLine] = Field(default_factory=list)
    activities: List[ExtractedActivityLine] = Field(default_factory=list)
```

### 1C. Add `activities` field to `EstimateResearchDeliverable` (line 118)

Add `activities: List[ExtractedActivityLine] = Field(default_factory=list)`.

### 1D. Add `activity_hints` to `ArchitectScope` (line 133)

```python
class ArchitectScope(BaseModel):
    scope_name: str = ""
    description: str = ""
    activity_hints: List[str] = Field(default_factory=list)
```

### 1E. Add `UnmatchedActivityItem` to `platform/models/estimate.py` (after line 92)

```python
class UnmatchedActivityItem(BaseModel):
    name: str
    role_name: str = ""
    effort: float = 0.0
    reason: Optional[str] = None
```

### 1F. Add `unmatched_activities` to `JobItem` (line 95)

Add `unmatched_activities: List[UnmatchedActivityItem] = []` after `unmatched_labours`.

### 1G. Add `UnmatchedActivityItemCreate` to `platform/routers/estimates.py` (after line 556)

```python
class UnmatchedActivityItemCreate(BaseModel):
    model_config = {"extra": "ignore"}
    name: str
    role_name: str = ""
    effort: float = 0.0
    reason: Optional[str] = None
```

Add `unmatched_activities: List[UnmatchedActivityItemCreate] = []` to `JobItemCreate`.

### 1H. Add config setting to `platform/config.py`

```python
estimate_fuzzy_match_threshold: int = 85  # 0-100 scale for inventory matching
```

---

## Phase 2: Prompt Changes

### 2A. Architect Prompt (`platform/prompts/estimate_architect.py`)

Update to instruct the LLM to output work items with activity hints:

- Add rule: "For each scope, suggest the key activities that would be performed. A simple single-task scope (e.g., 'Mow lawn') may have just 1 activity. A complex scope may have several. Activities are task-level descriptions (e.g., 'Excavate and grade area', 'Install paver base')."
- Update OUTPUT SCHEMA to include `"activity_hints": ["<activity 1>", "<activity 2>"]` in each scope.

### 2B. Research Prompt (`platform/prompts/estimate_research.py`)

Add instructions for activities in research output:

- "For each deliverable, include an `activities` array listing key tasks to be performed."
- "Each activity has `name` (task description), `role` (worker role), and `effort` (estimated hours)."
- "Activities replace top-level labours — do NOT include a separate `labours` array. All labor detail flows through activities."

### 2C. Generation Prompt (`platform/prompts/estimate_generation.py`)

Update the Output Format schema to include activities in job items:

```json
"activities": [
  {"name": "Excavate and grade area", "role": "Landscaper", "effort": 4}
]
```

Add activity rules:
- Each job item should have 1 or more activities describing tasks to be performed. Simple single-task work items (e.g., "Mow lawn") may have just 1 activity; complex work items may have several.
- Each activity has `name`, `role` (worker role name), and `effort` (hours)
- Activities replace `labours` — the `labours` array should be empty for AI-generated estimates
- Activity roles should be practical worker titles (Landscaper, Electrician, etc.)

### 2D. ReAct Prompt (`platform/prompts/estimate_react.py`)

Add activity awareness to the final output instructions.

---

## Phase 3: Pipeline Changes in `service.py`

### 3A. `_step3_research_for_scope()` (line 1343)

When flattening deliverables, also collect activities:

```python
all_activities = []
for d in normalized.get("deliverables", []):
    all_activities.extend(d.get("activities", []))
```

Include `"activities": all_activities` in the return dict.

### 3B. `_build_estimate_from_research()` (line 1773)

Include activities when building job items from deliverables:

```python
job_items.append({
    "description": description,
    "materials": deliverable.get("materials", []),
    "labours": [],  # Activities replace labours
    "activities": deliverable.get("activities", []),
    "unmatched_materials": [],
    "unmatched_labours": [],
    "unmatched_activities": [],
    "sub_total": 0.0,
})
```

### 3C. `_fill_prices_and_calculate_totals()` (line 2410) — CRITICAL

After the labour matching block (line 2558), add activity role matching:

```python
valid_activities = []
unmatched_activities = []
for raw_activity in job_item.get("activities", []):
    name = str(raw_activity.get("name") or "").strip()
    role_name = str(raw_activity.get("role") or "").strip()
    effort = float(raw_activity.get("effort", 0) or 0)
    if not name:
        continue
    if not role_name:
        unmatched_activities.append({"name": name, "role_name": "", "effort": effort, "reason": "No role specified"})
        continue
    # Match role against labour catalog using _resolve_labour_inventory_match
    matched = self._resolve_labour_inventory_match({"labour": role_name}, inventory)
    if matched:
        key = str(matched.get("id") or "")
        price = labour_prices.get(key, 0)
        catalog_entry = labour_catalog_by_id.get(key, {})
        valid_activities.append({
            "name": name, "role": key, "role_name": catalog_entry.get("name"),
            "rate": price, "effort": effort,
        })
    else:
        unmatched_activities.append({
            "name": name, "role_name": role_name, "effort": effort,
            "reason": "No inventory match found for role",
        })

job_item["activities"] = valid_activities
job_item["unmatched_activities"] = unmatched_activities
```

Update sub_total calculation (line 2562) to include activities:

```python
activities_total = sum(float(a.get("effort", 0)) * float(a.get("rate", 0)) for a in valid_activities)
sub_total = materials_total + labour_total + activities_total
```

### 3D. `_find_best_catalog_match()` (line 2115)

Change threshold from `60` to `settings.estimate_fuzzy_match_threshold`:

```python
if best_score < settings.estimate_fuzzy_match_threshold:
    return None
```

### 3E. `_normalize_research_result()` and `_normalize_extracted_estimate()`

Add activity normalization loops (similar to material/labour normalization) that extract `name`, `role`, `effort` from raw activity dicts.

### 3F. ReAct loop extraction (line 1661)

Update the extraction prompt building and `ExtractedEstimate` handling to pass through activities.

### 3G. Step 2 vector retrieval enhancement

When a work item closely matches a WorkItemSummary, fetch the linked estimate's job item and reuse its materials + activities directly, skipping web research for that scope. Add a similarity score threshold (e.g., >= 0.85) to determine "close match".

---

## Phase 4: Router Changes in `estimates.py`

### 4A. Import `UnmatchedActivityItem` from models

Add to the imports from `models.estimate`.

### 4B. Update `_build_merged_request_job_item()` (line 244)

Add `"activities"`, `"unmatched_activities"` to the returned dict from parsed_payload.

### 4C. Update `build_job_items_from_parsed()` (line 1108)

Construct `ActivityItem` and `UnmatchedActivityItem` lists from parsed data. Include them in the `JobItem()` constructor. The `calculate_activities_total()` function (line 346) already exists and will automatically include activity costs.

### 4D. Update `build_full_job_items_from_request()` (~line 911)

Handle `unmatched_activities` from the request similarly to `unmatched_labours`.

---

## Phase 5: WorkItemSummary Enhancement

### 5A. Update `build_job_item_summary()` in `platform/services/work_item_summary.py`

Include activities in the text summary for better future vector search matches:

```python
if job_item.activities:
    lines.append("Activities:")
    for a in job_item.activities:
        role_info = f" ({a.role_name})" if a.role_name else ""
        lines.append(f"- {a.name}{role_info}: {a.effort} hrs")
```

---

## Phase 6: Migration Script

### 6A. Create `platform/scripts/migrate_unmatched_activities.py`

A one-time migration script to add the `unmatched_activities` field to all existing estimate documents in MongoDB. Existing documents won't have this field, and while Pydantic defaults it to `[]` on read, the field should be persisted for consistency and queryability.

```python
"""
Migration: Add unmatched_activities field to all existing estimates.

Adds an empty unmatched_activities array to every job_item in every estimate
that doesn't already have the field. Safe to run multiple times (idempotent).

Usage:
    cd platform
    source .venv/bin/activate
    python scripts/migrate_unmatched_activities.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

async def migrate():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client.get_default_database()
    collection = db["estimates"]

    # Add unmatched_activities: [] to every job_item that lacks it
    result = await collection.update_many(
        {"job_items.unmatched_activities": {"$exists": False}},
        {"$set": {"job_items.$[item].unmatched_activities": []}},
        array_filters=[{"item.unmatched_activities": {"$exists": False}}],
    )
    print(f"Modified {result.modified_count} estimate documents")

if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## Phase 7: Tests

Update test files to cover the new activity flow:

- `platform/tests/test_estimate_agent.py` — Test activity extraction, role matching, unmatched activities
- `platform/tests/test_estimate_api.py` — Test AI-generated estimates with activities, unmatched_activities in JobItem
- `platform/tests/test_estimate_tools.py` — Test tool output includes activities
- `platform/tests/test_fuzzy_utils.py` — Test with 0.85 threshold behavior
- Migration script test — verify idempotency and correct field addition

---

## Verification Plan

1. **Unit tests**: Run `./run_tests.sh tests/test_estimate_agent.py tests/test_estimate_api.py` after each phase
2. **Integration test**: Create an estimate via AI generation (async_mode) and verify the response includes:
   - `job_items[*].activities` with matched roles (role ID, role_name, rate, effort)
   - `job_items[*].unmatched_activities` for roles not in catalog
   - `job_items[*].unmatched_materials` for materials not in catalog
   - Correct `sub_total` calculation including activity costs
3. **Manual flow**: Verify `skip_generation=true` still works unchanged
4. **Frontend**: Verify inventory gaps page shows unmatched activities

---

## Implementation Order

```
Phase 0 (un-deprecate) ──> Phase 1 (models) ──> Phase 2 (prompts) ──> Phase 3 (pipeline) ──> Phase 4 (router) ──> Phase 5 (summaries) ──> Phase 6 (migration) ──> Phase 7 (tests)
```

Phases 2 and 1H (config) can be done in parallel. Phase 5 can be done in parallel with Phases 3-4. Phase 6 (migration) can run after Phase 1 model changes are deployed. Frontend changes (inventory gaps for unmatched activities) are deferred — backend-first.

## Critical Files

| File | Changes |
|------|---------|
| `platform/models/estimate.py` | Add `UnmatchedActivityItem`, update `JobItem` |
| `platform/agents/estimate/service.py` | Activity extraction, role matching, pipeline updates |
| `platform/prompts/estimate_generation.py` | Activity output schema and rules |
| `platform/prompts/estimate_architect.py` | Activity hints in scopes |
| `platform/prompts/estimate_research.py` | Activities in research output |
| `platform/prompts/estimate_react.py` | Activity awareness |
| `platform/routers/estimates.py` | Router handling for activities + unmatched activities |
| `platform/services/work_item_summary.py` | Include activities in summary text |
| `platform/config.py` | Fuzzy match threshold setting |
| `platform/agents/estimate/tools.py` | Un-deprecate |
| `platform/agents/estimate/conversation_guide.py` | Un-deprecate |
| `platform/agents/estimate/__init__.py` | Un-deprecate |
