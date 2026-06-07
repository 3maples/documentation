# Settings — Materials Category & Unit Actions Menus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the per-row pencil/trash icons in the Settings → Material Categories and Material Units tabs with three-dot actions menus, and add a tab-level three-dot menu with a "Reload Standard Categories/Units" action that opens a confirmation modal (with an optional "remove all non-standard" checkbox) backed by new `load-standard` endpoints.

**Architecture:** Backend adds `POST /material-categories/load-standard` and `POST /material-units/load-standard` endpoints that reuse the existing bootstrap services (`services/material_category_bootstrap.py`, `services/material_unit_bootstrap.py`) for the upsert, plus new `remove_non_standard_*` service functions that delete non-standard items while **skipping (and reporting) items still in use by materials**. Frontend extracts a generic `ActionsMenu` from the existing `RowActionsMenu` (which becomes a thin wrapper, keeping its public API so `MaterialsTable`, `ActivitiesTable`, and `RateCardsTab` are untouched), then both settings tabs use `ActionsMenu` for the row menu (Edit / Delete) and the header menu (Reload Standard …), plus a reload-confirmation `Modal`.

**Tech Stack:** FastAPI + Beanie (platform), React 18 + TypeScript + Vite + vitest/RTL (portal), Tailwind, lucide-react icons.

**UX decisions (confirmed with Simon 2026-06-06):**
- **Split menus**: each table row gets a three-dot menu containing Edit + Delete (replacing the pencil/trash icon pair). A *separate* three-dot menu sits to the right of the "Add Category"/"Add Unit" button and contains the single tab-wide item "Reload Standard Categories"/"Reload Standard Units".
- **In-use non-standard items are skipped, not deleted**: when "Remove all non-standard …" is checked, items referenced by materials are kept and reported back to the user (`skipped_in_use` list in the response; surfaced via `alert()` in the UI, matching the tabs' existing error conventions).

**Repo layout note:** `platform/` and `portal/` are **separate git repos** (the project root is not a repo). Tasks 1–2 commit in `platform/`; Tasks 3–5 commit in `portal/`.

> ⚠️ **Standing project rule:** ask Simon for explicit approval before running **any** `git commit`. The commit steps below are checkpoints — pause and ask at each one. Commits in Tangz repos are authored as `3maples <admin@3maples.ai>` (already configured via local git config).

**Reference files (read before starting if anything is unclear):**
- `portal/src/components/settings/MaterialCategoriesTab.tsx` / `MaterialUnitsTab.tsx` — the two tabs being changed
- `portal/src/components/common/RowActionsMenu.tsx` — source of the portal-positioning logic being generalized
- `portal/src/components/common/Modal.tsx` — shared modal (props: `open`, `title`, `onClose`, `maxWidth`, `children`)
- `platform/services/material_category_bootstrap.py` / `material_unit_bootstrap.py` — existing upsert ("reload") logic
- `platform/routers/materials.py:184` — existing `POST /materials/load-standard` precedent
- `platform/tests/test_material_categories_api.py` / `test_material_units_api.py` — test conventions (TestClient, manual cleanup)
- `portal/tests/FinancialTab.test.tsx` — frontend test conventions (mocking `../src/api/client`)

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `platform/services/material_category_bootstrap.py` | Modify | Add `remove_non_standard_material_categories()` |
| `platform/services/material_unit_bootstrap.py` | Modify | Add `remove_non_standard_material_units()` |
| `platform/routers/material_categories.py` | Modify | Add `POST /material-categories/load-standard` |
| `platform/routers/material_units.py` | Modify | Add `POST /material-units/load-standard` |
| `platform/tests/test_material_categories_api.py` | Modify | Reload endpoint tests (categories) |
| `platform/tests/test_material_units_api.py` | Modify | Reload endpoint tests (units) |
| `portal/src/components/common/ActionsMenu.tsx` | Create | Generic three-dot menu (trigger + portal dropdown + item list) |
| `portal/src/components/common/RowActionsMenu.tsx` | Modify | Becomes a thin wrapper over `ActionsMenu` (public API unchanged) |
| `portal/src/api/resources.ts` | Modify | `loadStandard` methods on `materialCategoriesApi` / `materialUnitsApi` |
| `portal/src/components/settings/MaterialCategoriesTab.tsx` | Modify | Row menu, header menu, reload modal |
| `portal/src/components/settings/MaterialUnitsTab.tsx` | Modify | Row menu, header menu, reload modal |
| `portal/tests/ActionsMenu.test.tsx` | Create | Menu open/close/item-click behavior |
| `portal/tests/MaterialCategoriesTab.test.tsx` | Create | Tab integration: menus + reload modal + API calls |
| `portal/tests/MaterialUnitsTab.test.tsx` | Create | Same for units |

---

### Task 1: Backend — `POST /material-categories/load-standard`

**Files:**
- Modify: `platform/services/material_category_bootstrap.py`
- Modify: `platform/routers/material_categories.py`
- Test: `platform/tests/test_material_categories_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_material_categories_api.py`:

```python
# ---------------------------------------------------------------------------
# Reload standard categories (POST /material-categories/load-standard)
# ---------------------------------------------------------------------------

def _category_ids(client: TestClient, company_id: str) -> set:
    """Snapshot helper: ids of every category currently on the company."""
    return {c["id"] for c in client.get(f"/material-categories/?company={company_id}").json()}


def _cleanup_new_categories(client: TestClient, company_id: str, pre_existing: set) -> None:
    """Delete categories created during a test, leaving pre-existing ones alone."""
    for cat_id in _category_ids(client, company_id) - pre_existing:
        client.delete(f"/material-categories/{cat_id}")


def test_load_standard_categories_creates_and_overwrites_descriptions(
    client: TestClient, test_company_id: str
):
    """Reload seeds every standard category and resets edited descriptions."""
    from services.material_category_bootstrap import load_default_category_templates

    templates = load_default_category_templates()
    first = templates[0]
    pre_existing = _category_ids(client, test_company_id)

    # A standard-named category with a user-edited description
    created = client.post(
        "/material-categories/",
        json={
            "name": first["name"],
            "description": "user-edited description",
            "company": test_company_id,
        },
    ).json()

    response = client.post(f"/material-categories/load-standard?company={test_company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["loaded"] == len(templates)
    assert data["removed"] == 0
    assert data["skipped_in_use"] == []

    refreshed = client.get(f"/material-categories/{created['_id']}").json()
    assert refreshed["description"] == first["description"], \
        "Reload must overwrite user-edited descriptions of standard categories"

    _cleanup_new_categories(client, test_company_id, pre_existing)


def test_load_standard_categories_keeps_non_standard_by_default(
    client: TestClient, test_company_id: str
):
    """Without remove_non_standard, custom categories survive a reload."""
    pre_existing = _category_ids(client, test_company_id)
    client.post(
        "/material-categories/",
        json={"name": "My Custom Category", "company": test_company_id},
    )

    response = client.post(f"/material-categories/load-standard?company={test_company_id}")
    assert response.status_code == 200
    assert response.json()["removed"] == 0

    names = [c["name"] for c in client.get(f"/material-categories/?company={test_company_id}").json()]
    assert "My Custom Category" in names

    _cleanup_new_categories(client, test_company_id, pre_existing)


def test_load_standard_categories_removes_non_standard_when_requested(
    client: TestClient, test_company_id: str
):
    """remove_non_standard=true deletes categories not in the standard list."""
    pre_existing = _category_ids(client, test_company_id)
    client.post(
        "/material-categories/",
        json={"name": "Doomed Custom Category", "company": test_company_id},
    )

    response = client.post(
        f"/material-categories/load-standard?company={test_company_id}&remove_non_standard=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] >= 1
    assert data["skipped_in_use"] == []

    names = [c["name"] for c in client.get(f"/material-categories/?company={test_company_id}").json()]
    assert "Doomed Custom Category" not in names

    _cleanup_new_categories(client, test_company_id, pre_existing)


def test_load_standard_categories_skips_in_use_non_standard(
    client: TestClient, test_company_id: str
):
    """A non-standard category referenced by a material is kept and reported."""
    pre_existing = _category_ids(client, test_company_id)
    cat = client.post(
        "/material-categories/",
        json={"name": "In Use Custom Category", "company": test_company_id},
    ).json()
    cat_id = cat["_id"]

    material = client.post(
        "/materials/",
        json={
            "name": "Reload Guard Slab",
            "category": cat_id,
            "sizes": [{"size": "1 sq ft", "unit": cat_id, "cost": 10.0}],
            "company": test_company_id,
        },
    ).json()
    material_id = material.get("_id")

    response = client.post(
        f"/material-categories/load-standard?company={test_company_id}&remove_non_standard=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert "In Use Custom Category" in data["skipped_in_use"]

    names = [c["name"] for c in client.get(f"/material-categories/?company={test_company_id}").json()]
    assert "In Use Custom Category" in names, "In-use category must NOT be deleted"

    # Cleanup: material first (releases the in-use lock), then categories
    if material_id:
        client.delete(f"/materials/{material_id}")
    _cleanup_new_categories(client, test_company_id, pre_existing)


def test_load_standard_categories_invalid_company_returns_422(client: TestClient):
    """Garbage company id returns 422, not 500."""
    response = client.post("/material-categories/load-standard?company=not-an-objectid")
    assert response.status_code == 422
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_tests.sh tests/test_material_categories_api.py -v
```

Expected: the 5 new tests FAIL with `405 Method Not Allowed` or `404` on the `load-standard` POSTs (route doesn't exist yet). All pre-existing tests still PASS.

- [ ] **Step 3: Add the removal service function**

In `platform/services/material_category_bootstrap.py`, change the models import and append the new function:

```python
from models import Material, MaterialCategory
```

```python
async def remove_non_standard_material_categories(
    company_id: str | PydanticObjectId,
) -> tuple[list[dict], list[str]]:
    """Delete company categories whose names are not in the standard CSV.

    Categories still referenced by materials are kept (deleting them would
    strand the materials). Returns (removed_before_states, skipped_in_use_names)
    so the caller can audit-log each deletion and report skips to the user.
    """
    normalized_company_id = PydanticObjectId(str(company_id))
    standard_names = {template["name"] for template in load_default_category_templates()}
    removed: list[dict] = []
    skipped_in_use: list[str] = []

    categories = await MaterialCategory.find(
        MaterialCategory.company == normalized_company_id
    ).to_list()
    for category in categories:
        if category.name in standard_names:
            continue
        in_use = await Material.find(Material.category == category.id).count()
        if in_use > 0:
            skipped_in_use.append(category.name)
            continue
        removed.append(category.model_dump(mode="json"))
        await category.delete()

    return removed, skipped_in_use
```

- [ ] **Step 4: Add the endpoint**

In `platform/routers/material_categories.py`, add to the imports block:

```python
import logging

from services.material_category_bootstrap import (
    bootstrap_company_material_categories,
    remove_non_standard_material_categories,
)

logger = logging.getLogger(__name__)
```

(`assert_is_manager` and `assert_user_company_access` are already imported from `dependencies`.)

Append the endpoint at the end of the file (no path conflict: the only other POST route is `/`):

```python
@router.post("/load-standard")
async def load_standard_material_categories(
    request: Request,
    company: str = Query(..., description="Company ObjectId"),
    remove_non_standard: bool = Query(
        False, description="Also delete categories not in the standard list"
    ),
    current_user: User = Depends(assert_is_manager),
):
    """Reload standard categories; optionally remove non-standard ones.

    Upserts every standard category (overwriting descriptions). When
    remove_non_standard is set, deletes non-standard categories that are not
    referenced by any material; in-use ones are kept and reported back.
    """
    try:
        company_id = PydanticObjectId(company)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=422, detail="Invalid company id") from None
    await assert_user_company_access(current_user, company_id)

    try:
        loaded = await bootstrap_company_material_categories(company_id)
    except Exception:
        logger.exception(
            "Failed to reload standard categories for company %s", company_id
        )
        raise HTTPException(
            status_code=502, detail="Failed to reload standard categories"
        ) from None

    removed_states: list[dict] = []
    skipped_in_use: list[str] = []
    if remove_non_standard:
        removed_states, skipped_in_use = await remove_non_standard_material_categories(
            company_id
        )
        for before_state in removed_states:
            await create_audit_log(
                request=request,
                decoded_token={"email": current_user.email, "uid": str(current_user.id)},
                action=AuditAction.MATERIAL_CATEGORY_DELETE,
                resource_type=ResourceType.MATERIAL_CATEGORY,
                resource_id=str(before_state.get("_id") or before_state.get("id")),
                company_id=company_id,
                before_state=before_state,
            )

    return {
        "loaded": loaded,
        "removed": len(removed_states),
        "skipped_in_use": skipped_in_use,
    }
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_tests.sh tests/test_material_categories_api.py -v
```

Expected: ALL tests PASS (old + 5 new).

- [ ] **Step 6: Run mypy and ruff on the touched files**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_mypy.sh routers/material_categories.py services/material_category_bootstrap.py
./run_ruff.sh routers/material_categories.py services/material_category_bootstrap.py tests/test_material_categories_api.py
```

Expected: zero errors from both. Fix any findings in this same task before proceeding.

- [ ] **Step 7: Commit (ASK SIMON FIRST)**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
git add routers/material_categories.py services/material_category_bootstrap.py tests/test_material_categories_api.py
git commit -m "feat: add load-standard endpoint for material categories"
```

---

### Task 2: Backend — `POST /material-units/load-standard`

Mirror of Task 1 for units. The in-use check for units queries embedded sizes: `Material.find({"sizes.unit": unit.id})` (see `routers/material_units.py:113`).

**Files:**
- Modify: `platform/services/material_unit_bootstrap.py`
- Modify: `platform/routers/material_units.py`
- Test: `platform/tests/test_material_units_api.py`

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_material_units_api.py`:

```python
# ---------------------------------------------------------------------------
# Reload standard units (POST /material-units/load-standard)
# ---------------------------------------------------------------------------

def _unit_ids(client: TestClient, company_id: str) -> set:
    """Snapshot helper: ids of every unit currently on the company."""
    return {u["id"] for u in client.get(f"/material-units/?company={company_id}").json()}


def _cleanup_new_units(client: TestClient, company_id: str, pre_existing: set) -> None:
    """Delete units created during a test, leaving pre-existing ones alone."""
    for unit_id in _unit_ids(client, company_id) - pre_existing:
        client.delete(f"/material-units/{unit_id}")


def test_load_standard_units_creates_and_overwrites_descriptions(
    client: TestClient, test_company_id: str
):
    """Reload seeds every standard unit and resets edited descriptions."""
    from services.material_unit_bootstrap import load_default_unit_templates

    templates = load_default_unit_templates()
    first = templates[0]
    pre_existing = _unit_ids(client, test_company_id)

    created = client.post(
        "/material-units/",
        json={
            "name": first["name"],
            "description": "user-edited description",
            "company": test_company_id,
        },
    ).json()

    response = client.post(f"/material-units/load-standard?company={test_company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["loaded"] == len(templates)
    assert data["removed"] == 0
    assert data["skipped_in_use"] == []

    refreshed = client.get(f"/material-units/{created['_id']}").json()
    assert refreshed["description"] == first["description"], \
        "Reload must overwrite user-edited descriptions of standard units"

    _cleanup_new_units(client, test_company_id, pre_existing)


def test_load_standard_units_keeps_non_standard_by_default(
    client: TestClient, test_company_id: str
):
    """Without remove_non_standard, custom units survive a reload."""
    pre_existing = _unit_ids(client, test_company_id)
    client.post(
        "/material-units/",
        json={"name": "My Custom Unit", "company": test_company_id},
    )

    response = client.post(f"/material-units/load-standard?company={test_company_id}")
    assert response.status_code == 200
    assert response.json()["removed"] == 0

    names = [u["name"] for u in client.get(f"/material-units/?company={test_company_id}").json()]
    assert "My Custom Unit" in names

    _cleanup_new_units(client, test_company_id, pre_existing)


def test_load_standard_units_removes_non_standard_when_requested(
    client: TestClient, test_company_id: str
):
    """remove_non_standard=true deletes units not in the standard list."""
    pre_existing = _unit_ids(client, test_company_id)
    client.post(
        "/material-units/",
        json={"name": "Doomed Custom Unit", "company": test_company_id},
    )

    response = client.post(
        f"/material-units/load-standard?company={test_company_id}&remove_non_standard=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["removed"] >= 1
    assert data["skipped_in_use"] == []

    names = [u["name"] for u in client.get(f"/material-units/?company={test_company_id}").json()]
    assert "Doomed Custom Unit" not in names

    _cleanup_new_units(client, test_company_id, pre_existing)


def test_load_standard_units_skips_in_use_non_standard(
    client: TestClient, test_company_id: str
):
    """A non-standard unit referenced by a material size is kept and reported."""
    pre_existing = _unit_ids(client, test_company_id)
    unit = client.post(
        "/material-units/",
        json={"name": "In Use Custom Unit", "company": test_company_id},
    ).json()
    unit_id = unit["_id"]

    material = client.post(
        "/materials/",
        json={
            "name": "Reload Guard Mulch",
            "category": unit_id,
            "sizes": [{"size": "1 yd", "unit": unit_id, "cost": 10.0}],
            "company": test_company_id,
        },
    ).json()
    material_id = material.get("_id")

    response = client.post(
        f"/material-units/load-standard?company={test_company_id}&remove_non_standard=true"
    )
    assert response.status_code == 200
    data = response.json()
    assert "In Use Custom Unit" in data["skipped_in_use"]

    names = [u["name"] for u in client.get(f"/material-units/?company={test_company_id}").json()]
    assert "In Use Custom Unit" in names, "In-use unit must NOT be deleted"

    # Cleanup: material first (releases the in-use lock), then units
    if material_id:
        client.delete(f"/materials/{material_id}")
    _cleanup_new_units(client, test_company_id, pre_existing)


def test_load_standard_units_invalid_company_returns_422(client: TestClient):
    """Garbage company id returns 422, not 500."""
    response = client.post("/material-units/load-standard?company=not-an-objectid")
    assert response.status_code == 422
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_tests.sh tests/test_material_units_api.py -v
```

Expected: the 5 new tests FAIL (405/404 on `load-standard`); pre-existing tests PASS.

- [ ] **Step 3: Add the removal service function**

In `platform/services/material_unit_bootstrap.py`, change the models import and append:

```python
from models import Material, MaterialUnit
```

```python
async def remove_non_standard_material_units(
    company_id: str | PydanticObjectId,
) -> tuple[list[dict], list[str]]:
    """Delete company units whose names are not in the standard CSV.

    Units still referenced by any material size are kept. Returns
    (removed_before_states, skipped_in_use_names) so the caller can audit-log
    each deletion and report skips to the user.
    """
    normalized_company_id = PydanticObjectId(str(company_id))
    standard_names = {template["name"] for template in load_default_unit_templates()}
    removed: list[dict] = []
    skipped_in_use: list[str] = []

    units = await MaterialUnit.find(
        MaterialUnit.company == normalized_company_id
    ).to_list()
    for unit in units:
        if unit.name in standard_names:
            continue
        in_use = await Material.find({"sizes.unit": unit.id}).count()
        if in_use > 0:
            skipped_in_use.append(unit.name)
            continue
        removed.append(unit.model_dump(mode="json"))
        await unit.delete()

    return removed, skipped_in_use
```

- [ ] **Step 4: Add the endpoint**

In `platform/routers/material_units.py`, add to the imports block:

```python
import logging

from services.material_unit_bootstrap import (
    bootstrap_company_material_units,
    remove_non_standard_material_units,
)

logger = logging.getLogger(__name__)
```

Append the endpoint at the end of the file:

```python
@router.post("/load-standard")
async def load_standard_material_units(
    request: Request,
    company: str = Query(..., description="Company ObjectId"),
    remove_non_standard: bool = Query(
        False, description="Also delete units not in the standard list"
    ),
    current_user: User = Depends(assert_is_manager),
):
    """Reload standard units; optionally remove non-standard ones.

    Upserts every standard unit (overwriting descriptions). When
    remove_non_standard is set, deletes non-standard units that are not
    referenced by any material size; in-use ones are kept and reported back.
    """
    try:
        company_id = PydanticObjectId(company)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=422, detail="Invalid company id") from None
    await assert_user_company_access(current_user, company_id)

    try:
        loaded = await bootstrap_company_material_units(company_id)
    except Exception:
        logger.exception(
            "Failed to reload standard units for company %s", company_id
        )
        raise HTTPException(
            status_code=502, detail="Failed to reload standard units"
        ) from None

    removed_states: list[dict] = []
    skipped_in_use: list[str] = []
    if remove_non_standard:
        removed_states, skipped_in_use = await remove_non_standard_material_units(
            company_id
        )
        for before_state in removed_states:
            await create_audit_log(
                request=request,
                decoded_token={"email": current_user.email, "uid": str(current_user.id)},
                action=AuditAction.MATERIAL_UNIT_DELETE,
                resource_type=ResourceType.MATERIAL_UNIT,
                resource_id=str(before_state.get("_id") or before_state.get("id")),
                company_id=company_id,
                before_state=before_state,
            )

    return {
        "loaded": loaded,
        "removed": len(removed_states),
        "skipped_in_use": skipped_in_use,
    }
```

Note: if `assert_is_manager` / `assert_user_company_access` are not already imported in `material_units.py`'s `dependencies` import block, add them there (they are in `material_categories.py`'s block).

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_tests.sh tests/test_material_units_api.py -v
```

Expected: ALL tests PASS.

- [ ] **Step 6: Run mypy and ruff on the touched files**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_mypy.sh routers/material_units.py services/material_unit_bootstrap.py
./run_ruff.sh routers/material_units.py services/material_unit_bootstrap.py tests/test_material_units_api.py
```

Expected: zero errors. Fix any findings in this same task.

- [ ] **Step 7: Commit (ASK SIMON FIRST)**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
git add routers/material_units.py services/material_unit_bootstrap.py tests/test_material_units_api.py
git commit -m "feat: add load-standard endpoint for material units"
```

---

### Task 3: Frontend — generic `ActionsMenu` component

Extract the portal/positioning logic from `RowActionsMenu` into a generic items-driven menu; `RowActionsMenu` becomes a thin wrapper with an **unchanged public API** (its three consumers — `MaterialsTable.tsx`, `ActivitiesTable.tsx`, `RateCardsTab.tsx` — are not modified).

**Files:**
- Create: `portal/src/components/common/ActionsMenu.tsx`
- Modify: `portal/src/components/common/RowActionsMenu.tsx`
- Test: `portal/tests/ActionsMenu.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `portal/tests/ActionsMenu.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { Pencil, Trash2 } from "lucide-react";
import { ActionsMenu } from "../src/components/common/ActionsMenu";

afterEach(cleanup);

describe("ActionsMenu", () => {
  test("menu is closed until the trigger is clicked", () => {
    render(
      <ActionsMenu
        ariaLabel="Row actions"
        items={[{ label: "Edit", icon: Pencil, onClick: () => {} }]}
      />,
    );
    expect(screen.queryByRole("menu")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Row actions" }));
    expect(screen.getByRole("menu")).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Edit" })).toBeTruthy();
  });

  test("clicking an item fires its handler and closes the menu", () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(
      <ActionsMenu
        ariaLabel="Row actions"
        items={[
          { label: "Edit", icon: Pencil, onClick: onEdit },
          { label: "Delete", icon: Trash2, onClick: onDelete, variant: "danger" },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Row actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Delete" }));
    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onEdit).not.toHaveBeenCalled();
    expect(screen.queryByRole("menu")).toBeNull();
  });

  test("disabled items do not fire their handler", () => {
    const onClick = vi.fn();
    render(
      <ActionsMenu
        ariaLabel="Row actions"
        items={[{ label: "Edit", onClick, disabled: true }]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Row actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    expect(onClick).not.toHaveBeenCalled();
  });

  test("Escape closes the menu", () => {
    render(
      <ActionsMenu
        ariaLabel="Row actions"
        items={[{ label: "Edit", onClick: () => {} }]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Row actions" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- ActionsMenu.test.tsx
```

Expected: FAIL — `Cannot find module '../src/components/common/ActionsMenu'` (or equivalent resolve error).

- [ ] **Step 3: Create `ActionsMenu`**

Create `portal/src/components/common/ActionsMenu.tsx`:

```tsx
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { MoreVertical } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface ActionsMenuItem {
  label: string;
  icon?: LucideIcon;
  onClick: () => void;
  /** "danger" renders the red destructive styling (e.g. Delete). */
  variant?: "default" | "danger";
  disabled?: boolean;
}

export interface ActionsMenuProps {
  items: ActionsMenuItem[];
  /** Accessible name for the trigger button (e.g. "Aggregates actions"). */
  ariaLabel?: string;
  /** Dropdown width in px; widen for long labels like "Reload Standard Categories". */
  menuWidth?: number;
}

const MENU_GAP = 4;
const MENU_VIEWPORT_MARGIN = 8;

/**
 * Generic three-dot actions menu. Renders the dropdown into a portal so it
 * can't be clipped by `overflow-*` ancestors — the trigger button stays in
 * place but the menu floats over the rest of the UI.
 */
export function ActionsMenu({
  items,
  ariaLabel = "Actions",
  menuWidth = 160,
}: ActionsMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [menuPos, setMenuPos] = useState<{ top: number; left: number } | null>(
    null,
  );
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const computePosition = (menuHeight: number) => {
    if (!buttonRef.current) return null;
    const rect = buttonRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const dropUp = spaceBelow < menuHeight + MENU_GAP;
    const top = dropUp
      ? rect.top - menuHeight - MENU_GAP
      : rect.bottom + MENU_GAP;
    const left = Math.max(
      MENU_VIEWPORT_MARGIN,
      Math.min(
        rect.right - menuWidth,
        window.innerWidth - menuWidth - MENU_VIEWPORT_MARGIN,
      ),
    );
    return { top, left };
  };

  const reposition = () => {
    const height = menuRef.current?.offsetHeight ?? 0;
    if (height === 0) return;
    setMenuPos(computePosition(height));
  };

  useLayoutEffect(() => {
    if (!isOpen) return;
    reposition();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (menuRef.current?.contains(target) || buttonRef.current?.contains(target)) {
        return;
      }
      setIsOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onEscape);
    window.addEventListener("scroll", reposition, true);
    window.addEventListener("resize", reposition);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onEscape);
      window.removeEventListener("scroll", reposition, true);
      window.removeEventListener("resize", reposition);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const close = () => {
    setIsOpen(false);
    setMenuPos(null);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        className="inline-flex items-center justify-center w-8 h-8 rounded-full text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
        onClick={(event) => {
          event.stopPropagation();
          setIsOpen((prev) => !prev);
        }}
      >
        <MoreVertical className="w-4 h-4" />
      </button>
      {isOpen &&
        createPortal(
          <div
            ref={menuRef}
            role="menu"
            style={{
              top: menuPos?.top ?? -9999,
              left: menuPos?.left ?? -9999,
              width: menuWidth,
              visibility: menuPos ? "visible" : "hidden",
            }}
            className="fixed z-50 rounded-lg bg-white py-1 shadow-lg"
            onClick={(event) => event.stopPropagation()}
          >
            {items.map((item) => (
              <button
                key={item.label}
                type="button"
                role="menuitem"
                disabled={item.disabled}
                className={
                  item.variant === "danger"
                    ? "w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                    : "w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent"
                }
                onClick={(event) => {
                  event.stopPropagation();
                  close();
                  item.onClick();
                }}
              >
                {item.icon && <item.icon className="w-4 h-4" />}
                {item.label}
              </button>
            ))}
          </div>,
          document.body,
        )}
    </>
  );
}
```

- [ ] **Step 4: Refactor `RowActionsMenu` to delegate**

Replace the entire body of `portal/src/components/common/RowActionsMenu.tsx` with:

```tsx
import { ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import { ActionsMenu } from "./ActionsMenu";
import type { ActionsMenuItem } from "./ActionsMenu";

export interface RowActionsMenuProps {
  index: number;
  totalRows: number;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  onDelete: () => void;
  /** Accessible name for the trigger button (e.g. "Material 2 actions"). */
  ariaLabel?: string;
}

/**
 * Three-dot menu that consolidates row reorder + delete actions. Thin wrapper
 * over the generic ActionsMenu (which handles the portal positioning).
 */
export function RowActionsMenu({
  index,
  totalRows,
  onMoveUp,
  onMoveDown,
  onDelete,
  ariaLabel = "Row actions",
}: RowActionsMenuProps) {
  const items: ActionsMenuItem[] = [];
  if (onMoveUp) {
    items.push({
      label: "Move up",
      icon: ChevronUp,
      onClick: onMoveUp,
      disabled: index <= 0,
    });
  }
  if (onMoveDown) {
    items.push({
      label: "Move down",
      icon: ChevronDown,
      onClick: onMoveDown,
      disabled: index >= totalRows - 1,
    });
  }
  items.push({
    label: "Delete",
    icon: Trash2,
    onClick: onDelete,
    variant: "danger",
  });
  return <ActionsMenu items={items} ariaLabel={ariaLabel} />;
}
```

- [ ] **Step 5: Run the tests and typecheck**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- ActionsMenu.test.tsx
npm run typecheck
```

Expected: 4 tests PASS; typecheck clean (verifies the RowActionsMenu refactor compiles against its three consumers).

- [ ] **Step 6: Commit (ASK SIMON FIRST)**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
git add src/components/common/ActionsMenu.tsx src/components/common/RowActionsMenu.tsx tests/ActionsMenu.test.tsx
git commit -m "refactor: extract generic ActionsMenu from RowActionsMenu"
```

---

### Task 4: Frontend — Material Categories tab

**Files:**
- Modify: `portal/src/api/resources.ts` (add `loadStandard` to `materialCategoriesApi`, around line 131)
- Modify: `portal/src/components/settings/MaterialCategoriesTab.tsx`
- Test: `portal/tests/MaterialCategoriesTab.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `portal/tests/MaterialCategoriesTab.test.tsx`:

```tsx
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  cleanup,
  waitFor,
  fireEvent,
} from "@testing-library/react";

afterEach(cleanup);

const apiRequestMock = vi.fn();
vi.mock("../src/api/client", () => ({
  apiRequest: (...args: unknown[]) => apiRequestMock(...args),
}));

// Modal reads the AI-panel context; stub it so tests don't need the provider.
vi.mock("../src/lib/aiPanelContext", () => ({
  useAiPanel: () => ({ isOpen: false }),
}));

import MaterialCategoriesTab from "../src/components/settings/MaterialCategoriesTab";

const categories = [
  { id: "cat1", name: "Aggregates", description: "Gravel and sand", company: "c1" },
  { id: "cat2", name: "Concrete", description: null, company: "c1" },
];

beforeEach(() => {
  apiRequestMock.mockReset();
  apiRequestMock.mockImplementation(
    (_path: string, options?: { method?: string }) => {
      if (options?.method === "POST") {
        return Promise.resolve({ loaded: 19, removed: 0, skipped_in_use: [] });
      }
      return Promise.resolve(categories);
    },
  );
});

function renderTab() {
  return render(
    <MaterialCategoriesTab companyId="c1" canManageResources active />,
  );
}

describe("MaterialCategoriesTab actions menus", () => {
  test("rows show a three-dot menu instead of pencil/trash icon buttons", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Aggregates")).toBeTruthy());
    expect(screen.getByRole("button", { name: "Aggregates actions" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Edit category" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete category" })).toBeNull();
  });

  test("row menu Edit opens the edit dialog prefilled", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Aggregates")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Aggregates actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    expect(screen.getByText("Edit Category")).toBeTruthy();
    expect(screen.getByDisplayValue("Aggregates")).toBeTruthy();
  });

  test("row menu Delete opens the delete confirmation", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Aggregates")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Aggregates actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Delete" }));
    expect(screen.getByText("Delete Category")).toBeTruthy();
  });

  test("header menu opens the reload modal with required copy and unchecked checkbox", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Aggregates")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Category actions" }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Reload Standard Categories" }),
    );
    expect(
      screen.getByText(
        "Standard categories will be loaded. Any updates to their descriptions will be overwritten.",
      ),
    ).toBeTruthy();
    const checkbox = screen.getByRole("checkbox", {
      name: "Remove all non-standard categories.",
    }) as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
  });

  test("confirming reload posts with remove_non_standard=false and refetches", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Aggregates")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Category actions" }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Reload Standard Categories" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() =>
      expect(apiRequestMock).toHaveBeenCalledWith(
        "/material-categories/load-standard?company=c1&remove_non_standard=false",
        { method: "POST" },
      ),
    );
    // Initial list fetch + post-reload refetch (recompute inside waitFor —
    // the calls array grows asynchronously after the POST resolves)
    await waitFor(() => {
      const listCalls = apiRequestMock.mock.calls.filter(
        (call) => call[0] === "/material-categories?company=c1",
      );
      expect(listCalls.length).toBeGreaterThanOrEqual(2);
    });
  });

  test("checking the checkbox sends remove_non_standard=true", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Aggregates")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Category actions" }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Reload Standard Categories" }),
    );
    fireEvent.click(
      screen.getByRole("checkbox", { name: "Remove all non-standard categories." }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() =>
      expect(apiRequestMock).toHaveBeenCalledWith(
        "/material-categories/load-standard?company=c1&remove_non_standard=true",
        { method: "POST" },
      ),
    );
  });
});
```

Note: the exact list-fetch path in the first `apiRequestMock` assertions must match `materialCategoriesApi.list` (`/material-categories?company=c1`). If a test fails on a path mismatch, check `src/api/resources.ts` for the canonical string rather than changing the implementation.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- MaterialCategoriesTab.test.tsx
```

Expected: FAIL — no buttons named "Aggregates actions"/"Category actions" exist yet (the old pencil/trash UI renders instead).

- [ ] **Step 3: Add the API method**

In `portal/src/api/resources.ts`, add to `materialCategoriesApi` (after `remove`):

```ts
  loadStandard: (
    companyId: string | null | undefined,
    removeNonStandard: boolean,
  ) =>
    apiRequest<{ loaded: number; removed: number; skipped_in_use: string[] }>(
      `/material-categories/load-standard?company=${encodeParam(requireCompanyId(companyId))}&remove_non_standard=${removeNonStandard}`,
      { method: "POST" },
    ),
```

- [ ] **Step 4: Update `MaterialCategoriesTab.tsx`**

Apply these edits:

**(a) Imports** — replace the lucide import and add `ActionsMenu`:

```tsx
import { Pencil, RefreshCw, Trash2 } from "lucide-react";
import { ActionsMenu } from "../common/ActionsMenu";
```

**(b) New state** — add below the existing delete-dialog state (after `deleteCategoryError`):

```tsx
  const [showReloadDialog, setShowReloadDialog] = useState(false);
  const [removeNonStandard, setRemoveNonStandard] = useState(false);
  const [reloading, setReloading] = useState(false);
  const [reloadError, setReloadError] = useState("");
```

**(c) New handlers** — add after `confirmDeleteCategory`:

```tsx
  const handleOpenReloadDialog = () => {
    setRemoveNonStandard(false);
    setReloadError("");
    setShowReloadDialog(true);
  };

  const confirmReloadStandard = async () => {
    try {
      setReloading(true);
      setReloadError("");
      const result = await materialCategoriesApi.loadStandard(
        companyId,
        removeNonStandard,
      );
      setShowReloadDialog(false);
      await fetchCategories();
      if (result.skipped_in_use.length > 0) {
        alert(
          `Reload complete. These categories were kept because they are in use by materials: ${result.skipped_in_use.join(", ")}`,
        );
      }
    } catch (error: unknown) {
      setReloadError((error as Error).message);
    } finally {
      setReloading(false);
    }
  };
```

**(d) Header** — replace the existing `{canManageResources && (<button ...Add Category...</button>)}` block with:

```tsx
          {canManageResources && (
            <div className="flex items-center gap-1">
              <button
                onClick={handleAddCategory}
                className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark"
              >
                <span className="text-xl leading-none">+</span>
                Add Category
              </button>
              <ActionsMenu
                ariaLabel="Category actions"
                menuWidth={240}
                items={[
                  {
                    label: "Reload Standard Categories",
                    icon: RefreshCw,
                    onClick: handleOpenReloadDialog,
                  },
                ]}
              />
            </div>
          )}
```

**(e) Row actions cell** — replace the `<div className="flex items-center justify-end gap-1">…</div>` block (the two pencil/trash buttons inside the `{canManageResources && (...)}` of the actions `<td>`) with:

```tsx
                          <ActionsMenu
                            ariaLabel={`${category.name} actions`}
                            items={[
                              {
                                label: "Edit",
                                icon: Pencil,
                                onClick: () => handleEditCategory(category),
                              },
                              {
                                label: "Delete",
                                icon: Trash2,
                                onClick: () => handleDeleteCategory(category),
                                variant: "danger",
                              },
                            ]}
                          />
```

**(f) Reload modal** — add after the existing Delete `<Modal>` (before the closing `</>`):

```tsx
      <Modal
        open={showReloadDialog}
        title="Reload Standard Categories"
        maxWidth="max-w-md"
        onClose={() => setShowReloadDialog(false)}
      >
        <p className="text-sm text-gray-600 mb-4">
          Standard categories will be loaded. Any updates to their descriptions
          will be overwritten.
        </p>
        <label className="flex items-center gap-2 text-sm text-gray-700 mb-4">
          <input
            type="checkbox"
            checked={removeNonStandard}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setRemoveNonStandard(e.target.checked)
            }
            className="h-4 w-4 rounded border-gray-300"
          />
          Remove all non-standard categories.
        </label>
        {reloadError && (
          <p className="text-sm text-red-600 mb-4" role="alert">
            {reloadError}
          </p>
        )}
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => setShowReloadDialog(false)}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg border border-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={confirmReloadStandard}
            disabled={reloading}
            className="px-4 py-2 text-sm bg-brand text-white rounded-lg hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {reloading ? "Reloading..." : "Reload"}
          </button>
        </div>
      </Modal>
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- MaterialCategoriesTab.test.tsx
npm run typecheck
```

Expected: 6 tests PASS; typecheck clean.

- [ ] **Step 6: Commit (ASK SIMON FIRST)**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
git add src/api/resources.ts src/components/settings/MaterialCategoriesTab.tsx tests/MaterialCategoriesTab.test.tsx
git commit -m "feat: add actions menus and standard-reload dialog to Material Categories tab"
```

---

### Task 5: Frontend — Material Units tab

Exact mirror of Task 4 with unit naming. Copy substitutions: `Category→Unit`, `categories→units`, `materialCategoriesApi→materialUnitsApi`, `/material-categories→/material-units`, "Reload Standard Categories"→"Reload Standard Units", modal copy "Standard units will be loaded. Any updates to their descriptions will be overwritten.", checkbox label "Remove all non-standard units.", header menu aria-label `"Unit actions"`.

**Files:**
- Modify: `portal/src/api/resources.ts` (add `loadStandard` to `materialUnitsApi`)
- Modify: `portal/src/components/settings/MaterialUnitsTab.tsx`
- Test: `portal/tests/MaterialUnitsTab.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `portal/tests/MaterialUnitsTab.test.tsx`:

```tsx
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  cleanup,
  waitFor,
  fireEvent,
} from "@testing-library/react";

afterEach(cleanup);

const apiRequestMock = vi.fn();
vi.mock("../src/api/client", () => ({
  apiRequest: (...args: unknown[]) => apiRequestMock(...args),
}));

// Modal reads the AI-panel context; stub it so tests don't need the provider.
vi.mock("../src/lib/aiPanelContext", () => ({
  useAiPanel: () => ({ isOpen: false }),
}));

import MaterialUnitsTab from "../src/components/settings/MaterialUnitsTab";

const units = [
  { id: "unit1", name: "Bag", description: "Bagged goods", company: "c1" },
  { id: "unit2", name: "Pallet", description: null, company: "c1" },
];

beforeEach(() => {
  apiRequestMock.mockReset();
  apiRequestMock.mockImplementation(
    (_path: string, options?: { method?: string }) => {
      if (options?.method === "POST") {
        return Promise.resolve({ loaded: 12, removed: 0, skipped_in_use: [] });
      }
      return Promise.resolve(units);
    },
  );
});

function renderTab() {
  return render(<MaterialUnitsTab companyId="c1" canManageResources active />);
}

describe("MaterialUnitsTab actions menus", () => {
  test("rows show a three-dot menu instead of pencil/trash icon buttons", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Bag")).toBeTruthy());
    expect(screen.getByRole("button", { name: "Bag actions" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Edit unit" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete unit" })).toBeNull();
  });

  test("row menu Edit opens the edit dialog prefilled", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Bag")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Bag actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    expect(screen.getByText("Edit Unit")).toBeTruthy();
    expect(screen.getByDisplayValue("Bag")).toBeTruthy();
  });

  test("row menu Delete opens the delete confirmation", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Bag")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Bag actions" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Delete" }));
    expect(screen.getByText("Delete Unit")).toBeTruthy();
  });

  test("header menu opens the reload modal with required copy and unchecked checkbox", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Bag")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Unit actions" }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Reload Standard Units" }),
    );
    expect(
      screen.getByText(
        "Standard units will be loaded. Any updates to their descriptions will be overwritten.",
      ),
    ).toBeTruthy();
    const checkbox = screen.getByRole("checkbox", {
      name: "Remove all non-standard units.",
    }) as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
  });

  test("confirming reload posts with remove_non_standard=false", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Bag")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Unit actions" }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Reload Standard Units" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() =>
      expect(apiRequestMock).toHaveBeenCalledWith(
        "/material-units/load-standard?company=c1&remove_non_standard=false",
        { method: "POST" },
      ),
    );
  });

  test("checking the checkbox sends remove_non_standard=true", async () => {
    renderTab();
    await waitFor(() => expect(screen.getByText("Bag")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Unit actions" }));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Reload Standard Units" }),
    );
    fireEvent.click(
      screen.getByRole("checkbox", { name: "Remove all non-standard units." }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() =>
      expect(apiRequestMock).toHaveBeenCalledWith(
        "/material-units/load-standard?company=c1&remove_non_standard=true",
        { method: "POST" },
      ),
    );
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- MaterialUnitsTab.test.tsx
```

Expected: FAIL — no "Bag actions"/"Unit actions" buttons yet.

- [ ] **Step 3: Add the API method**

In `portal/src/api/resources.ts`, add to `materialUnitsApi` (after `remove`):

```ts
  loadStandard: (
    companyId: string | null | undefined,
    removeNonStandard: boolean,
  ) =>
    apiRequest<{ loaded: number; removed: number; skipped_in_use: string[] }>(
      `/material-units/load-standard?company=${encodeParam(requireCompanyId(companyId))}&remove_non_standard=${removeNonStandard}`,
      { method: "POST" },
    ),
```

- [ ] **Step 4: Update `MaterialUnitsTab.tsx`**

Same six edits as Task 4 Step 4, with unit naming:

**(a) Imports:**

```tsx
import { Pencil, RefreshCw, Trash2 } from "lucide-react";
import { ActionsMenu } from "../common/ActionsMenu";
```

**(b) New state** (after `deleteUnitError`):

```tsx
  const [showReloadDialog, setShowReloadDialog] = useState(false);
  const [removeNonStandard, setRemoveNonStandard] = useState(false);
  const [reloading, setReloading] = useState(false);
  const [reloadError, setReloadError] = useState("");
```

**(c) New handlers** (after `confirmDeleteUnit`):

```tsx
  const handleOpenReloadDialog = () => {
    setRemoveNonStandard(false);
    setReloadError("");
    setShowReloadDialog(true);
  };

  const confirmReloadStandard = async () => {
    try {
      setReloading(true);
      setReloadError("");
      const result = await materialUnitsApi.loadStandard(
        companyId,
        removeNonStandard,
      );
      setShowReloadDialog(false);
      await fetchUnits();
      if (result.skipped_in_use.length > 0) {
        alert(
          `Reload complete. These units were kept because they are in use by materials: ${result.skipped_in_use.join(", ")}`,
        );
      }
    } catch (error: unknown) {
      setReloadError((error as Error).message);
    } finally {
      setReloading(false);
    }
  };
```

**(d) Header** — replace the `{canManageResources && (<button ...Add Unit...</button>)}` block with:

```tsx
          {canManageResources && (
            <div className="flex items-center gap-1">
              <button
                onClick={handleAddUnit}
                className="flex items-center gap-2 px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-dark"
              >
                <span className="text-xl leading-none">+</span>
                Add Unit
              </button>
              <ActionsMenu
                ariaLabel="Unit actions"
                menuWidth={240}
                items={[
                  {
                    label: "Reload Standard Units",
                    icon: RefreshCw,
                    onClick: handleOpenReloadDialog,
                  },
                ]}
              />
            </div>
          )}
```

**(e) Row actions cell** — replace the pencil/trash button pair with:

```tsx
                          <ActionsMenu
                            ariaLabel={`${unit.name} actions`}
                            items={[
                              {
                                label: "Edit",
                                icon: Pencil,
                                onClick: () => handleEditUnit(unit),
                              },
                              {
                                label: "Delete",
                                icon: Trash2,
                                onClick: () => handleDeleteUnit(unit),
                                variant: "danger",
                              },
                            ]}
                          />
```

**(f) Reload modal** — add after the existing Delete `<Modal>`:

```tsx
      <Modal
        open={showReloadDialog}
        title="Reload Standard Units"
        maxWidth="max-w-md"
        onClose={() => setShowReloadDialog(false)}
      >
        <p className="text-sm text-gray-600 mb-4">
          Standard units will be loaded. Any updates to their descriptions will
          be overwritten.
        </p>
        <label className="flex items-center gap-2 text-sm text-gray-700 mb-4">
          <input
            type="checkbox"
            checked={removeNonStandard}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setRemoveNonStandard(e.target.checked)
            }
            className="h-4 w-4 rounded border-gray-300"
          />
          Remove all non-standard units.
        </label>
        {reloadError && (
          <p className="text-sm text-red-600 mb-4" role="alert">
            {reloadError}
          </p>
        )}
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => setShowReloadDialog(false)}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg border border-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={confirmReloadStandard}
            disabled={reloading}
            className="px-4 py-2 text-sm bg-brand text-white rounded-lg hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {reloading ? "Reloading..." : "Reload"}
          </button>
        </div>
      </Modal>
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- MaterialUnitsTab.test.tsx
npm run typecheck
```

Expected: 6 tests PASS; typecheck clean.

- [ ] **Step 6: Commit (ASK SIMON FIRST)**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
git add src/api/resources.ts src/components/settings/MaterialUnitsTab.tsx tests/MaterialUnitsTab.test.tsx
git commit -m "feat: add actions menus and standard-reload dialog to Material Units tab"
```

---

### Task 6: Final gates (pre-handoff verification)

No code changes — verification only. Do NOT run the full test suites (user-triggered per CLAUDE.md); run only the project-wide static gates plus the test files touched by this work.

- [ ] **Step 1: Platform gates — full-project mypy and ruff (both are zero-error gates)**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_mypy.sh
./run_ruff.sh
```

Expected: zero errors from both. Any finding is a regression from Tasks 1–2 — fix it before handing off.

- [ ] **Step 2: Platform — re-run the touched test files together**

```bash
cd /Users/simon/Development/Tangz/3maples/platform
./run_tests.sh tests/test_material_categories_api.py tests/test_material_units_api.py tests/test_material_bootstrap.py -v
```

Expected: ALL PASS (`test_material_bootstrap.py` is included because the bootstrap service modules were modified).

- [ ] **Step 3: Portal gates — touched tests, typecheck, lint**

```bash
cd /Users/simon/Development/Tangz/3maples/portal
npm test -- ActionsMenu.test.tsx MaterialCategoriesTab.test.tsx MaterialUnitsTab.test.tsx
npm run typecheck
npm run lint
```

Expected: all tests PASS, typecheck and lint clean. (Per Simon's standing preference: if lint/typecheck surfaces pre-existing errors, fix them and report alongside this work.)

- [ ] **Step 4: Report**

Summarize to Simon: endpoints added, UI changes, test counts, gate results — then ask whether to proceed with anything further (e.g. a manual smoke test in the running app). Do not push.
