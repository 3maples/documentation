# Property Activity Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Properties page's estimates block with a fixed-height, tabbed Activity panel showing Estimates and Tasks per property, backed by per-property server queries so the page stops loading every estimate in the company.

**Architecture:** Backend gains per-property filtered list queries (`GET /estimates?property=`, widened `GET /tasks`), an `X-Total-Count` header on both, and a counts endpoint for the tab badges. Frontend extracts a generic status-filter dropdown from the estimates-specific one, adds a self-contained `PropertyActivityPanel` component that owns tabs/filters/fetching, and slims `PropertiesPage.tsx` accordingly. Deep links from the panel require query-param seeding on TasksPage and a new property filter on EstimatesPage.

**Tech Stack:** FastAPI + Beanie/MongoDB (backend), React 18 + TypeScript + Tailwind + Vitest/Testing Library (frontend).

**Spec:** [property-activity-panel.md](property-activity-panel.md)

## Global Constraints

- **TDD is mandatory.** Failing test first, then implementation. Every task below is ordered that way — do not reorder.
- **After any `.py` change under `platform/`:** run `./run_mypy.sh <touched subtree>` and `./run_ruff.sh <touched subtree>`. The project sits at zero errors for both; fix new ones in the same task.
- **After any `.tsx`/`.ts` change under `portal/`:** run `npm run typecheck` and `npm run lint`. `npm run build` is vite-only and does NOT typecheck.
- **Run only the tests related to your change.** Do not run the full suite — the user triggers that manually.
- **Backend tests need the local Mongo running:** `cd platform && ./scripts/start_test_mongo.sh` (idempotent).
- **US spellings** in all code, comments, and copy ("labor", "color", "behavior").
- **Commit message format:** `<type>: <description>` where type ∈ `feat, fix, refactor, docs, test, chore, perf, ci`.
- **Do not push.** Commits are local; the user approves each push separately.
- `PANEL_PAGE_SIZE = 15` — the number of rows the panel fetches per tab. Defined once in `portal/src/components/properties/propertyActivityConstants.ts` and imported everywhere else.

---

### Task 1: `GET /estimates` — property filter, status filter, total-count header

Adds per-property querying to the estimates list, plus the index it needs and the CORS change that makes the count header visible to the browser.

**Files:**
- Modify: `platform/routers/estimates.py:382-416`
- Modify: `platform/models/estimate.py:450-465`
- Modify: `platform/main.py:112-118`
- Test: `platform/tests/test_estimate_api.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `GET /estimates?company=<id>&property=<id>&status=<Value>&status=<Value>&limit=<n>&include_archived=<bool>` returning `List[Estimate]` plus an `X-Total-Count` response header holding the pre-limit match count. `status` values are **exact `EstimateStatus` enum values** ("Draft", "On Hold"), not normalized keys.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_estimate_api.py`. These follow the file's existing create → assert → delete lifecycle; adapt the fixture names to whatever that file already uses for creating an estimate.

```python
def test_list_estimates_filters_by_property(client: TestClient, test_company_id: str):
    """property= returns only that property's estimates."""
    prop_a = client.post("/properties/", json={
        "company": test_company_id, "street": "1 Panel St", "city": "Toronto",
        "prov_state": "ON", "postal_zip": "M1M1M1", "country": "Canada",
    }).json()
    prop_b = client.post("/properties/", json={
        "company": test_company_id, "street": "2 Panel St", "city": "Toronto",
        "prov_state": "ON", "postal_zip": "M2M2M2", "country": "Canada",
    }).json()
    prop_a_id, prop_b_id = prop_a["_id"], prop_b["_id"]

    made = []
    try:
        for title, prop in (("A one", prop_a_id), ("A two", prop_a_id), ("B one", prop_b_id)):
            r = client.post("/estimates/", json={
                "company": test_company_id, "title": title, "property": prop,
                "created_by": "test@example.com", "skip_generation": True,
            })
            assert r.status_code == 200, r.text
            made.append(r.json()["_id"])

        response = client.get(f"/estimates/?company={test_company_id}&property={prop_a_id}")
        assert response.status_code == 200
        titles = sorted(e["title"] for e in response.json())
        assert titles == ["A one", "A two"]
    finally:
        for estimate_id in made:
            client.delete(f"/estimates/{estimate_id}")
        client.delete(f"/properties/{prop_a_id}")
        client.delete(f"/properties/{prop_b_id}")


def test_list_estimates_rejects_malformed_property(client: TestClient, test_company_id: str):
    """A property id that isn't an ObjectId is a client error, not a 500."""
    response = client.get(f"/estimates/?company={test_company_id}&property=not-an-id")
    assert response.status_code == 422


def test_list_estimates_filters_by_multiple_statuses(client: TestClient, test_company_id: str):
    """Repeated status= params return the union of those statuses."""
    made = []
    try:
        for title, status in (("D job", "Draft"), ("S job", "Sent"), ("W job", "Won")):
            r = client.post("/estimates/", json={
                "company": test_company_id, "title": title, "status": status,
                "created_by": "test@example.com", "skip_generation": True,
            })
            assert r.status_code == 200, r.text
            made.append(r.json()["_id"])

        response = client.get(
            f"/estimates/?company={test_company_id}&status=Draft&status=Won"
        )
        assert response.status_code == 200
        titles = {e["title"] for e in response.json()}
        assert "D job" in titles and "W job" in titles
        assert "S job" not in titles
    finally:
        for estimate_id in made:
            client.delete(f"/estimates/{estimate_id}")


def test_list_estimates_rejects_unknown_status(client: TestClient, test_company_id: str):
    """An unknown status value is rejected rather than silently matching nothing."""
    response = client.get(f"/estimates/?company={test_company_id}&status=Bogus")
    assert response.status_code == 422


def test_list_estimates_total_count_header_ignores_limit(
    client: TestClient, test_company_id: str
):
    """X-Total-Count reports matches BEFORE limit — it drives 'showing 1 of N'."""
    prop = client.post("/properties/", json={
        "company": test_company_id, "street": "3 Panel St", "city": "Toronto",
        "prov_state": "ON", "postal_zip": "M3M3M3", "country": "Canada",
    }).json()
    prop_id = prop["_id"]
    made = []
    try:
        for title in ("One", "Two", "Three"):
            r = client.post("/estimates/", json={
                "company": test_company_id, "title": title, "property": prop_id,
                "created_by": "test@example.com", "skip_generation": True,
            })
            made.append(r.json()["_id"])

        response = client.get(
            f"/estimates/?company={test_company_id}&property={prop_id}&limit=1"
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.headers["X-Total-Count"] == "3"
    finally:
        for estimate_id in made:
            client.delete(f"/estimates/{estimate_id}")
        client.delete(f"/properties/{prop_id}")
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_estimate_api.py -k "property or status or total_count" -v
```

Expected: FAIL. The `property`/`status` params are silently ignored by FastAPI today, so the filter tests fail on the assertion (wrong titles returned), and the header test fails with `KeyError: 'X-Total-Count'`.

- [ ] **Step 3: Add the index to the Estimate model**

In `platform/models/estimate.py`, inside `class Settings`, add a second entry to the existing `indexes` list (keep the existing `company_updated_at_status` entry as-is):

```python
            # Backs the Properties page activity panel, which lists one
            # property's estimates newest-first. Without this the panel does a
            # collection scan per property selection.
            pymongo.IndexModel(
                [
                    ("company", pymongo.ASCENDING),
                    ("property", pymongo.ASCENDING),
                    ("updated_at", pymongo.DESCENDING),
                ],
                name="company_property_updated_at",
            ),
```

- [ ] **Step 4: Widen the endpoint**

Replace `get_estimates` and `fetch_estimates` in `platform/routers/estimates.py` (currently lines 382-416). Add `Response` to the `fastapi` imports at the top of the file if it isn't already there.

```python
@router.get("/", response_model=List[Estimate])
async def get_estimates(
    response: Response,
    company: str = Query(...),
    include_archived: bool = Query(False),
    limit: Optional[int] = Query(None, ge=1),
    property: Optional[str] = Query(None, description="Filter by Property id"),
    status: Optional[List[EstimateStatus]] = Query(
        None, description="Filter by status; repeat the param for several"
    ),
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    """Get all estimates for a company. By default, archived estimates are excluded.

    When *limit* is provided the results are sorted by most-recently created
    first and capped at that number – useful for search / agent contexts where
    loading every estimate in the company is unnecessary.

    ``X-Total-Count`` carries the number of matches *before* limit, so a capped
    caller can still say how much it isn't showing.
    """
    await assert_company_access(decoded_token, PydanticObjectId(company))
    estimates, total = await fetch_estimates(
        company,
        include_archived=include_archived,
        limit=limit,
        property_id=property,
        statuses=status,
    )
    response.headers["X-Total-Count"] = str(total)
    return estimates


def _estimate_conditions(
    company: str,
    include_archived: bool,
    property_id: Optional[str],
    statuses: Optional[List[EstimateStatus]],
) -> list:
    """Shared filter set for the list endpoint and its count."""
    conditions: list = [Estimate.company == PydanticObjectId(company)]
    if not include_archived:
        conditions.append(Estimate.status != EstimateStatus.ARCHIVED)
    if property_id:
        try:
            conditions.append({"property": PydanticObjectId(property_id)})
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid property id") from None
    if statuses:
        conditions.append({"status": {"$in": [s.value for s in statuses]}})
    return conditions


async def fetch_estimates(
    company: str,
    include_archived: bool = False,
    limit: Optional[int] = None,
    property_id: Optional[str] = None,
    statuses: Optional[List[EstimateStatus]] = None,
) -> tuple[list, int]:
    """Plain helper for listing estimates — safe to call outside FastAPI.

    Returns (estimates, total_before_limit).
    """
    conditions = _estimate_conditions(company, include_archived, property_id, statuses)
    total = await Estimate.find(*conditions).count()

    query = Estimate.find(*conditions)
    if limit is not None:
        query = query.sort(-Estimate.created_at).limit(limit)  # type: ignore[operator]  # Beanie descriptor unary-minus sort idiom.

    return await query.to_list(), total
```

- [ ] **Step 5: Fix `fetch_estimates` callers**

`fetch_estimates` now returns a tuple. Find every caller and unpack it:

```bash
cd platform && grep -rn "fetch_estimates" --include=*.py .
```

For each hit outside `routers/estimates.py`, change `estimates = await fetch_estimates(...)` to `estimates, _ = await fetch_estimates(...)`. If a caller only needs the list and the tuple return reads badly there, that's still the right change — don't add a second helper.

- [ ] **Step 6: Expose the header through CORS**

In `platform/main.py`, add `expose_headers` to the `CORSMiddleware` block (lines 112-118). Without this the browser can read the response body but **not** the header, and the frontend's "Showing 15 of 31" silently never renders:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=bool(cors_origins),  # credentials only with explicit origins
    allow_methods=["*"],
    allow_headers=["*"],
    # X-Total-Count is unreadable from JS unless explicitly exposed — CORS hides
    # every non-safelisted response header by default.
    expose_headers=["X-Total-Count"],
)
```

- [ ] **Step 7: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_estimate_api.py -v
```

Expected: PASS, including the pre-existing tests in that file (the tuple change to `fetch_estimates` must not break them).

- [ ] **Step 8: Run the gates**

```bash
cd platform && ./run_mypy.sh routers/estimates.py && ./run_ruff.sh routers/estimates.py
```

Expected: zero errors from both.

- [ ] **Step 9: Commit**

```bash
cd platform && git add routers/estimates.py models/estimate.py main.py tests/test_estimate_api.py
git commit -m "feat: filter estimates by property and status with a total-count header"
```

---

### Task 2: `GET /tasks` — multi-status, created_at sort, total-count header

**Files:**
- Modify: `platform/routers/tasks.py:160-225`
- Modify: `platform/models/task.py:72-98`
- Test: `platform/tests/test_tasks_api.py`

**Interfaces:**
- Consumes: nothing from Task 1 (independent).
- Produces: `GET /tasks?company=<id>&property=<id>&status=<id>&status=<id>&sort=created_at&limit=<n>` returning `List[Task]` plus `X-Total-Count`. `sort` now accepts `"due_date"` **or** `"created_at"`; absent still means `updated_at` descending.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_tasks_api.py`, following that file's `_task_payload` helper and delete-in-finally convention.

```python
def test_list_tasks_accepts_multiple_statuses(client: TestClient, test_company_id: str):
    """Repeated status= returns the union of those statuses."""
    statuses = client.get(f"/task-statuses/?company={test_company_id}").json()
    first_id, second_id = statuses[0]["_id"], statuses[1]["_id"]

    made = []
    try:
        for description, status_id in (
            ("In first", first_id), ("In second", second_id), ("Also second", second_id),
        ):
            r = client.post("/tasks/", json=_task_payload(
                test_company_id, description=description, status=status_id))
            assert r.status_code == 200, r.text
            made.append(r.json()["_id"])

        response = client.get(
            f"/tasks/?company={test_company_id}&status={first_id}&status={second_id}"
        )
        assert response.status_code == 200
        descriptions = {t["description"] for t in response.json()}
        assert {"In first", "In second", "Also second"} <= descriptions
    finally:
        for task_id in made:
            client.delete(f"/tasks/{task_id}")


def test_list_tasks_single_status_still_works(client: TestClient, test_company_id: str):
    """Regression: existing single-value callers are unaffected by the widening."""
    statuses = client.get(f"/task-statuses/?company={test_company_id}").json()
    second_id = statuses[1]["_id"]

    made = []
    try:
        r = client.post("/tasks/", json=_task_payload(
            test_company_id, description="Only mine", status=second_id))
        made.append(r.json()["_id"])

        response = client.get(f"/tasks/?company={test_company_id}&status={second_id}")
        assert response.status_code == 200
        assert "Only mine" in {t["description"] for t in response.json()}
    finally:
        for task_id in made:
            client.delete(f"/tasks/{task_id}")


def test_list_tasks_first_status_still_matches_null(
    client: TestClient, test_company_id: str
):
    """Regression: v1 tasks (status=None) belong to the first status, and that
    must survive multi-status filtering."""
    statuses = client.get(f"/task-statuses/?company={test_company_id}").json()
    first_id, second_id = statuses[0]["_id"], statuses[1]["_id"]

    made = []
    try:
        r = client.post("/tasks/", json=_task_payload(
            test_company_id, description="Legacy task"))
        task_id = r.json()["_id"]
        made.append(task_id)
        # Force the legacy shape the special case exists for.
        updated = client.put(f"/tasks/{task_id}", json={"status": None})
        assert updated.status_code == 200

        response = client.get(
            f"/tasks/?company={test_company_id}&status={first_id}&status={second_id}"
        )
        assert "Legacy task" in {t["description"] for t in response.json()}
    finally:
        for task_id in made:
            client.delete(f"/tasks/{task_id}")


def test_list_tasks_sort_created_at_is_newest_first(
    client: TestClient, test_company_id: str
):
    """sort=created_at returns most-recently-created first."""
    made = []
    try:
        for description in ("Oldest", "Middle", "Newest"):
            r = client.post("/tasks/", json=_task_payload(
                test_company_id, description=description))
            made.append(r.json()["_id"])

        response = client.get(f"/tasks/?company={test_company_id}&sort=created_at")
        assert response.status_code == 200
        ordered = [t["description"] for t in response.json()]
        # Only assert about the three this test owns; the company may hold others.
        mine = [d for d in ordered if d in {"Oldest", "Middle", "Newest"}]
        assert mine == ["Newest", "Middle", "Oldest"]
    finally:
        for task_id in made:
            client.delete(f"/tasks/{task_id}")


def test_list_tasks_sort_due_date_unchanged(client: TestClient, test_company_id: str):
    """Regression: adding created_at must not disturb the due_date sort."""
    made = []
    try:
        for description, due in (("Later", "2030-12-01"), ("Sooner", "2030-01-01")):
            r = client.post("/tasks/", json=_task_payload(
                test_company_id, description=description, due_date=due))
            made.append(r.json()["_id"])

        response = client.get(f"/tasks/?company={test_company_id}&sort=due_date")
        ordered = [t["description"] for t in response.json()]
        mine = [d for d in ordered if d in {"Later", "Sooner"}]
        assert mine == ["Sooner", "Later"]
    finally:
        for task_id in made:
            client.delete(f"/tasks/{task_id}")


def test_list_tasks_total_count_header_ignores_limit(
    client: TestClient, test_company_id: str
):
    """X-Total-Count reports matches before limit."""
    prop = client.post("/properties/", json={
        "company": test_company_id, "street": "9 Task St", "city": "Toronto",
        "prov_state": "ON", "postal_zip": "M9M9M9", "country": "Canada",
    }).json()
    prop_id = prop["_id"]
    made = []
    try:
        for description in ("T1", "T2", "T3"):
            r = client.post("/tasks/", json=_task_payload(
                test_company_id, description=description, property=prop_id))
            made.append(r.json()["_id"])

        response = client.get(
            f"/tasks/?company={test_company_id}&property={prop_id}&limit=1"
        )
        assert len(response.json()) == 1
        assert response.headers["X-Total-Count"] == "3"
    finally:
        for task_id in made:
            client.delete(f"/tasks/{task_id}")
        client.delete(f"/properties/{prop_id}")
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_tasks_api.py -k "multiple_statuses or single_status or null or created_at or due_date_unchanged or total_count" -v
```

Expected: FAIL — `sort=created_at` is rejected by the `Literal["due_date"]` annotation (422), multi-status returns a 422 or ignores the repeat, and the header lookup raises `KeyError`.

- [ ] **Step 3: Extend the Task index**

In `platform/models/task.py`, **replace** the existing `IndexModel([("company", 1), ("property", 1)])` entry (line 78) with:

```python
            # (company, property) plus the panel's created_at sort. The shorter
            # (company, property) index this replaces is a prefix of it, so
            # nothing that used the old one regresses. Beanie does not drop
            # indexes it no longer declares — the leftover is harmless but
            # should be dropped manually in Dev/Prod during rollout.
            IndexModel([("company", 1), ("property", 1), ("created_at", DESCENDING)]),
```

- [ ] **Step 4: Widen the endpoint**

In `platform/routers/tasks.py`, add a sort helper next to `_find_tasks_by_due_date`, then modify `get_tasks`. Add `Response` to the `fastapi` imports.

```python
async def _count_tasks(conditions: list) -> int:
    """Match count before limit — drives the X-Total-Count header."""
    return await Task.find(*conditions).count()
```

Change the signature (lines 161-177) — `status` becomes a list, `sort` gains a value, and `response` is injected:

```python
async def get_tasks(
    response: Response,
    company: str = Query(..., description="Company ObjectId to filter tasks"),
    # ge=1: Mongo's $limit rejects 0/negative (500 on the sort path), and the
    # find path treated 0 as "no limit" — neither is a sane client request.
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of tasks to return"),
    sort: Optional[Literal["due_date", "created_at"]] = Query(
        None,
        description="due_date: due-dated tasks first ascending (past-due on top), "
        "then undated tasks by updated_at ascending. created_at: newest created "
        "first. Default: updated_at descending.",
    ),
    search: Optional[str] = Query(None, description="Search term matched against title, description, and readable_id"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee email (exact match)"),
    status: Optional[List[str]] = Query(
        None, description="Filter by TaskStatus id; repeat the param for several"
    ),
    property: Optional[str] = Query(None, description="Filter by Property id"),
    include_archived: bool = Query(False, description="Include archived tasks (hidden by default)"),
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
```

Replace the status block (lines 207-218) with a multi-value version that preserves the first-status/`null` special case:

```python
    if status:
        try:
            status_ids = [PydanticObjectId(value) for value in status]
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid status id") from None
        statuses = await ensure_default_statuses(company_id)
        # v1 tasks predate the status field; None belongs to the first status so
        # the default column/filter stays complete.
        first_selected = bool(statuses) and statuses[0].id in status_ids
        clause: dict = {"$or": [{"status": {"$in": status_ids}}]}
        if first_selected:
            clause["$or"].append({"status": None})
        conditions.append(clause)
```

Replace the tail (lines 219-225) with the count + new sort branch:

```python
    total = await _count_tasks(conditions)
    response.headers["X-Total-Count"] = str(total)

    if sort == "due_date":
        return await _find_tasks_by_due_date(conditions, limit)

    order = -Task.created_at if sort == "created_at" else -Task.updated_at  # type: ignore[operator]  # Beanie descriptor unary-minus sort idiom
    query = Task.find(*conditions).sort(order)
    if limit is not None:
        query = query.limit(limit)
    return await query.to_list()
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_tasks_api.py -v
```

Expected: PASS, including the file's pre-existing tests.

- [ ] **Step 6: Run the gates**

```bash
cd platform && ./run_mypy.sh routers/tasks.py models/task.py && ./run_ruff.sh routers/tasks.py models/task.py
```

- [ ] **Step 7: Commit**

```bash
cd platform && git add routers/tasks.py models/task.py tests/test_tasks_api.py
git commit -m "feat: accept multiple task statuses and a created_at sort"
```

---

### Task 3: `GET /properties/{id}/activity-summary`

**Files:**
- Modify: `platform/routers/properties.py` (add after `get_property`, around line 285)
- Create: `platform/tests/test_property_activity_summary.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `GET /properties/{property_id}/activity-summary` → `{"estimate_count": int, "task_count": int}`. Both counts are unfiltered by status and **exclude archived records**, matching what the panel's tabs list by default.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_property_activity_summary.py`:

```python
"""Property activity-summary counts — the Properties page tab badges.

The panel lists at most PANEL_PAGE_SIZE rows per tab, so the totals behind
those tabs can only come from the server. Tests own their data lifecycle.
"""

from fastapi.testclient import TestClient


def _property_payload(company_id: str, street: str) -> dict:
    return {
        "company": company_id, "street": street, "city": "Toronto",
        "prov_state": "ON", "postal_zip": "M4M4M4", "country": "Canada",
    }


def test_activity_summary_counts_are_property_scoped(
    client: TestClient, test_company_id: str
):
    prop_a = client.post("/properties/", json=_property_payload(test_company_id, "1 Sum St")).json()
    prop_b = client.post("/properties/", json=_property_payload(test_company_id, "2 Sum St")).json()
    a_id, b_id = prop_a["_id"], prop_b["_id"]

    estimates, tasks = [], []
    try:
        for prop in (a_id, a_id, b_id):
            r = client.post("/estimates/", json={
                "company": test_company_id, "title": "Job", "property": prop,
                "created_by": "test@example.com", "skip_generation": True,
            })
            estimates.append(r.json()["_id"])
        for prop in (a_id, b_id, b_id):
            r = client.post("/tasks/", json={
                "company": test_company_id, "description": "Note", "property": prop,
            })
            tasks.append(r.json()["_id"])

        response = client.get(f"/properties/{a_id}/activity-summary")
        assert response.status_code == 200
        assert response.json() == {"estimate_count": 2, "task_count": 1}
    finally:
        for estimate_id in estimates:
            client.delete(f"/estimates/{estimate_id}")
        for task_id in tasks:
            client.delete(f"/tasks/{task_id}")
        client.delete(f"/properties/{a_id}")
        client.delete(f"/properties/{b_id}")


def test_activity_summary_excludes_archived(client: TestClient, test_company_id: str):
    """Archived records are hidden from the tabs, so they must not be counted."""
    prop = client.post("/properties/", json=_property_payload(test_company_id, "3 Sum St")).json()
    prop_id = prop["_id"]
    estimates, tasks = [], []
    try:
        live = client.post("/estimates/", json={
            "company": test_company_id, "title": "Live", "property": prop_id,
            "created_by": "test@example.com", "skip_generation": True,
        }).json()
        estimates.append(live["_id"])
        gone = client.post("/estimates/", json={
            "company": test_company_id, "title": "Gone", "property": prop_id,
            "status": "Archived", "created_by": "test@example.com", "skip_generation": True,
        }).json()
        estimates.append(gone["_id"])

        live_task = client.post("/tasks/", json={
            "company": test_company_id, "description": "Live", "property": prop_id,
        }).json()
        tasks.append(live_task["_id"])
        gone_task = client.post("/tasks/", json={
            "company": test_company_id, "description": "Gone", "property": prop_id,
        }).json()
        tasks.append(gone_task["_id"])
        client.post(f"/tasks/{gone_task['_id']}/archive", json={"archived": True})

        response = client.get(f"/properties/{prop_id}/activity-summary")
        assert response.json() == {"estimate_count": 1, "task_count": 1}
    finally:
        for estimate_id in estimates:
            client.delete(f"/estimates/{estimate_id}")
        for task_id in tasks:
            client.delete(f"/tasks/{task_id}")
        client.delete(f"/properties/{prop_id}")


def test_activity_summary_zero_for_empty_property(
    client: TestClient, test_company_id: str
):
    """A property with no activity returns zeros, not a 404."""
    prop = client.post("/properties/", json=_property_payload(test_company_id, "4 Sum St")).json()
    prop_id = prop["_id"]
    try:
        response = client.get(f"/properties/{prop_id}/activity-summary")
        assert response.status_code == 200
        assert response.json() == {"estimate_count": 0, "task_count": 0}
    finally:
        client.delete(f"/properties/{prop_id}")


def test_activity_summary_unknown_property_is_404(client: TestClient):
    response = client.get("/properties/507f1f77bcf86cd799439011/activity-summary")
    assert response.status_code == 404
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_property_activity_summary.py -v
```

Expected: FAIL with 404 on every case — the route doesn't exist, so FastAPI falls through to `GET /{property_id}` with `property_id="…/activity-summary"`.

- [ ] **Step 3: Implement the endpoint**

In `platform/routers/properties.py`, add after `get_property`. Import `Estimate`, `EstimateStatus` and `Task` at the top of the file if they aren't already imported.

```python
class PropertyActivitySummary(BaseModel):
    """Unfiltered per-property counts backing the activity panel's tab badges."""

    estimate_count: int
    task_count: int


@router.get("/{property_id}/activity-summary", response_model=PropertyActivitySummary)
async def get_property_activity_summary(
    property_id: str,
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    """Counts of the estimates and tasks linked to a property.

    The panel fetches only a page of rows per tab, so the totals — including
    for the tab the user hasn't opened — have to come from the server. Archived
    records are excluded on both sides, matching what the tabs list.
    """
    property = await Property.get(property_id)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    await assert_company_access(decoded_token, property.company)

    estimate_count = await Estimate.find(
        Estimate.company == property.company,
        {"property": property.id},
        Estimate.status != EstimateStatus.ARCHIVED,
    ).count()
    task_count = await Task.find(
        Task.company == property.company,
        {"property": property.id},
        {"archived": {"$ne": True}},
    ).count()

    return PropertyActivitySummary(
        estimate_count=estimate_count, task_count=task_count
    )
```

**Route ordering matters:** this must be declared *before* any `@router.get("/{property_id}")` catch-all would shadow it. `get_property` is declared with an exact `/{property_id}` path so FastAPI matches the longer literal path first, but keep this route adjacent to `/{property_id}/map.png` to make the grouping obvious.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_property_activity_summary.py -v
```

- [ ] **Step 5: Run the gates**

```bash
cd platform && ./run_mypy.sh routers/properties.py && ./run_ruff.sh routers/properties.py
```

- [ ] **Step 6: Commit**

```bash
cd platform && git add routers/properties.py tests/test_property_activity_summary.py
git commit -m "feat: add property activity-summary counts endpoint"
```

---

### Task 4: Frontend API layer — total-count reads and the new calls

**Files:**
- Modify: `portal/src/api/client.ts` (add after `apiRequest`, ~line 277)
- Modify: `portal/src/api/estimates.ts`
- Modify: `portal/src/api/tasks.ts`
- Modify: `portal/src/api/resources.ts`
- Modify: `portal/src/lib/estimateStatusFilter.ts`
- Test: `portal/tests/apiRequestWithTotal.test.ts`, `portal/tests/estimateStatusApiValues.test.ts`

**Interfaces:**
- Consumes: the three endpoints from Tasks 1–3.
- Produces:
  - `apiRequestWithTotal<T>(path: string): Promise<{ data: T | null; total: number | null }>`
  - `estimatesApi.listForProperty(companyId, { propertyId, statuses, includeArchived, limit })` → `{ data: Estimate[]; total: number | null }`
  - `tasksApi.listForProperty(companyId, { propertyId, statusIds, includeArchived, limit })` → `{ data: Task[]; total: number | null }`
  - `propertiesApi.activitySummary(propertyId)` → `{ estimate_count: number; task_count: number }`
  - `toApiStatusValues(selected: string[]): string[]` in `estimateStatusFilter.ts`

- [ ] **Step 1: Write the failing tests**

Create `portal/tests/apiRequestWithTotal.test.ts`:

```ts
/**
 * apiRequestWithTotal — reads X-Total-Count alongside the JSON body.
 *
 * apiRequest throws the response away after parsing, so a caller that needs
 * the header has no way to get at it. The panel's "Showing 15 of 31" needs it.
 */
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("../src/firebase", () => ({
  firebaseApp: {}, firebaseAuth: {}, firebaseAppCheck: {},
  waitForAuthReady: async () => undefined,
}));
vi.mock("firebase/app-check", () => ({ getToken: async () => ({ token: "t" }) }));
vi.mock("firebase/auth", () => ({ signOut: async () => undefined }));

const originalFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = originalFetch; vi.restoreAllMocks(); });

function mockResponse(body: unknown, headers: Record<string, string> = {}) {
  return {
    ok: true, status: 200,
    headers: { get: (name: string) => headers[name] ?? null },
    text: async () => JSON.stringify(body),
  } as unknown as Response;
}

describe("apiRequestWithTotal", () => {
  beforeEach(() => { vi.resetModules(); });

  test("returns the parsed body and the header total", async () => {
    globalThis.fetch = vi.fn(async () =>
      mockResponse([{ id: "a" }], { "X-Total-Count": "31" })) as unknown as typeof fetch;
    const { apiRequestWithTotal } = await import("../src/api/client");

    const result = await apiRequestWithTotal<{ id: string }[]>("/estimates/");

    expect(result.data).toEqual([{ id: "a" }]);
    expect(result.total).toBe(31);
  });

  test("total is null when the header is absent", async () => {
    globalThis.fetch = vi.fn(async () => mockResponse([])) as unknown as typeof fetch;
    const { apiRequestWithTotal } = await import("../src/api/client");

    const result = await apiRequestWithTotal("/estimates/");

    // null, not 0 — "we don't know" must not render as "there are none".
    expect(result.total).toBeNull();
  });

  test("total is null when the header is not a number", async () => {
    globalThis.fetch = vi.fn(async () =>
      mockResponse([], { "X-Total-Count": "lots" })) as unknown as typeof fetch;
    const { apiRequestWithTotal } = await import("../src/api/client");

    expect((await apiRequestWithTotal("/estimates/")).total).toBeNull();
  });
});
```

Create `portal/tests/estimateStatusApiValues.test.ts`:

```ts
/**
 * toApiStatusValues — turns normalized filter keys into the exact status
 * values the API stores, preserving the aliases the client-side filter used.
 */
import { describe, test, expect } from "vitest";
import {
  toApiStatusValues,
  ALL_FILTER_STATUS_VALUES,
} from "../src/lib/estimateStatusFilter";

describe("toApiStatusValues", () => {
  test("draft also matches Generating, mirroring matchesStatusSelection", () => {
    expect(toApiStatusValues(["draft"]).sort()).toEqual(["Draft", "Generating"]);
  });

  test("sent also matches the legacy Approved value", () => {
    expect(toApiStatusValues(["sent"]).sort()).toEqual(["Approved", "Sent"]);
  });

  test("maps the underscore key to its spaced status value", () => {
    expect(toApiStatusValues(["on_hold"])).toEqual(["On Hold"]);
  });

  test("archived is excluded — it travels as include_archived, not a status", () => {
    expect(toApiStatusValues(["archived"])).toEqual([]);
  });

  test("every non-archived option selected returns empty: 'send no filter'", () => {
    // Narrowing to the 8 known values would drop statuses the filter list
    // doesn't name (Failed, Deleted) from a view that shows them today.
    const allButArchived = ALL_FILTER_STATUS_VALUES.filter((v) => v !== "archived");
    expect(toApiStatusValues(allButArchived)).toEqual([]);
  });

  test("archived on top of everything else still sends no status filter", () => {
    // Archived widens the result via include_archived; it must not flip the
    // status param back on and re-narrow what that flag just opened up.
    expect(toApiStatusValues([...ALL_FILTER_STATUS_VALUES])).toEqual([]);
  });

  test("an empty selection is distinguishable from all-selected", () => {
    // Empty selection means "match nothing"; the caller checks length itself.
    expect(toApiStatusValues([])).toEqual([]);
  });
});
```

Create `portal/tests/listForPropertyParams.test.ts` — the query strings the two
wrappers build are the contract with Tasks 1 and 2, and nothing else asserts them:

```ts
/**
 * listForProperty query construction. The panel delegates ordering, paging and
 * archived-visibility to these wrappers, so the params they build are the only
 * place that contract is pinned.
 */
import { describe, test, expect, vi, beforeEach } from "vitest";

const apiRequestWithTotal = vi.fn(async () => ({ data: [], total: 0 }));
vi.mock("../src/api/client", () => ({
  apiRequestWithTotal: (...args: unknown[]) => apiRequestWithTotal(...args),
  apiRequest: vi.fn(),
  getEntityId: (v: { _id?: string }) => v?._id ?? "",
}));

beforeEach(() => apiRequestWithTotal.mockClear());

function lastPath(): string {
  return apiRequestWithTotal.mock.calls.at(-1)?.[0] as string;
}

describe("tasksApi.listForProperty", () => {
  test("always asks for newest-created first", async () => {
    const { tasksApi } = await import("../src/api/tasks");
    await tasksApi.listForProperty("co-1", {
      propertyId: "p1", statusIds: [], includeArchived: false, limit: 15,
    });
    // Not inherited from the endpoint default (updated_at) — asked for.
    expect(lastPath()).toContain("sort=created_at");
    expect(lastPath()).toContain("limit=15");
    expect(lastPath()).not.toContain("include_archived");
  });

  test("repeats status for each id and flags archived", async () => {
    const { tasksApi } = await import("../src/api/tasks");
    await tasksApi.listForProperty("co-1", {
      propertyId: "p1", statusIds: ["s1", "s2"], includeArchived: true, limit: 15,
    });
    expect(lastPath()).toContain("status=s1&status=s2");
    expect(lastPath()).toContain("include_archived=true");
  });
});

describe("estimatesApi.listForProperty", () => {
  test("expands normalized keys into stored status values", async () => {
    const { estimatesApi } = await import("../src/api/estimates");
    await estimatesApi.listForProperty("co-1", {
      propertyId: "p1", statuses: ["draft"], includeArchived: false, limit: 15,
    });
    expect(lastPath()).toContain("status=Draft&status=Generating");
  });

  test("sends no status param when the selection covers everything", async () => {
    const { estimatesApi } = await import("../src/api/estimates");
    const { ALL_FILTER_STATUS_VALUES } = await import("../src/lib/estimateStatusFilter");
    await estimatesApi.listForProperty("co-1", {
      propertyId: "p1", statuses: [...ALL_FILTER_STATUS_VALUES],
      includeArchived: true, limit: 15,
    });
    expect(lastPath()).not.toContain("status=");
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd portal && npm test -- apiRequestWithTotal estimateStatusApiValues listForPropertyParams
```

Expected: FAIL — `apiRequestWithTotal`, `toApiStatusValues` and both `listForProperty` methods are all unexported.

- [ ] **Step 3: Add `apiRequestWithTotal`**

In `portal/src/api/client.ts`, immediately after `apiRequest`:

```ts
/**
 * Like {@link apiRequest}, but also surfaces the `X-Total-Count` header.
 *
 * List endpoints cap their rows with `limit`, so the caller needs the
 * pre-limit total to say how much it isn't showing. `total` is null when the
 * header is missing or unparseable — callers must treat that as "unknown"
 * rather than zero. Requires the server to expose the header via CORS.
 */
export async function apiRequestWithTotal<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<{ data: T | null; total: number | null }> {
  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(await getAppCheckHeader()),
      ...(await getAuthorizationHeader()),
      ...((options.headers as Record<string, string>) || {}),
    },
  });

  if (!response.ok) {
    // Delegate error shaping to apiRequest's handling by re-running it; the
    // failed request is cheap and this keeps one error-translation path.
    return { data: (await apiRequest<T>(path, options)) as T | null, total: null };
  }

  const rawTotal = response.headers.get("X-Total-Count");
  const parsedTotal = rawTotal === null ? Number.NaN : Number(rawTotal);
  const total = Number.isFinite(parsedTotal) ? parsedTotal : null;

  const text = await response.text();
  return { data: text ? (JSON.parse(text) as T) : null, total };
}
```

- [ ] **Step 4: Add `toApiStatusValues`**

In `portal/src/lib/estimateStatusFilter.ts`, append:

```ts
/**
 * The exact stored status values behind each filter key.
 *
 * Mirrors the aliasing in {@link matchesStatusSelection}: Generating estimates
 * surface under "Draft" and legacy "Approved" records under "Sent". "archived"
 * is deliberately absent — it rides on the API's include_archived flag.
 */
const API_STATUS_VALUES: Record<string, string[]> = {
  draft: ["Draft", "Generating"],
  sent: ["Sent", "Approved"],
  review: ["Review"],
  won: ["Won"],
  lost: ["Lost"],
  on_hold: ["On Hold"],
  scheduled: ["Scheduled"],
  completed: ["Completed"],
};

/** Every filter key except "archived", which is a visibility flag. */
const NON_ARCHIVED_FILTER_VALUES = ALL_FILTER_STATUS_VALUES.filter(
  (value) => value !== "archived",
);

/**
 * Convert a filter selection into `status=` query values.
 *
 * Returns an empty array when every non-archived option is selected, which the
 * caller must read as "send no status filter at all". Narrowing to the eight
 * known values would silently drop statuses the filter doesn't list (Failed,
 * Deleted) from a view that shows them today. Archived is deliberately not
 * part of that test: it widens results through include_archived, so letting it
 * re-enable the status param would re-narrow what it just opened up.
 */
export function toApiStatusValues(selected: string[]): string[] {
  const coversEverything = NON_ARCHIVED_FILTER_VALUES.every((value) =>
    selected.includes(value),
  );
  if (coversEverything) return [];
  const values = selected.flatMap((key) => API_STATUS_VALUES[key] ?? []);
  return Array.from(new Set(values));
}
```

- [ ] **Step 5: Add the three API calls**

In `portal/src/api/estimates.ts`, add to the `estimatesApi` object (import `apiRequestWithTotal` from `./client` and `toApiStatusValues` from `../lib/estimateStatusFilter`):

```ts
  /** One property's estimates, newest-updated first, capped at `limit`.
   *  `statuses` are normalized filter keys — the expansion to stored values
   *  happens here so callers never hand-build status params. */
  listForProperty: async (
    companyId: string | null | undefined,
    {
      propertyId,
      statuses,
      includeArchived,
      limit,
    }: {
      propertyId: string;
      statuses: string[];
      includeArchived: boolean;
      limit: number;
    },
  ): Promise<{ data: Estimate[]; total: number | null }> => {
    const params = new URLSearchParams({
      company: requireCompanyId(companyId),
      property: propertyId,
      limit: String(limit),
    });
    if (includeArchived) params.set("include_archived", "true");
    for (const value of toApiStatusValues(statuses)) params.append("status", value);
    const { data, total } = await apiRequestWithTotal<Estimate[]>(`/estimates/?${params}`);
    return { data: data || [], total };
  },
```

In `portal/src/api/tasks.ts`, add to `tasksApi`:

```ts
  /** One property's tasks, newest-created first, capped at `limit`. */
  listForProperty: async (
    companyId: string | null | undefined,
    {
      propertyId,
      statusIds,
      includeArchived,
      limit,
    }: {
      propertyId: string;
      statusIds: string[];
      includeArchived: boolean;
      limit: number;
    },
  ): Promise<{ data: Task[]; total: number | null }> => {
    const params = new URLSearchParams({
      company: requireCompanyId(companyId),
      property: propertyId,
      sort: "created_at",
      limit: String(limit),
    });
    if (includeArchived) params.set("include_archived", "true");
    for (const id of statusIds) params.append("status", id);
    const { data, total } = await apiRequestWithTotal<Task[]>(`/tasks?${params}`);
    return { data: data || [], total };
  },
```

In `portal/src/api/resources.ts`, add to `propertiesApi`:

```ts
  /** Unfiltered estimate/task counts for the activity panel's tab badges. */
  activitySummary: (propertyId: string) =>
    apiRequest<{ estimate_count: number; task_count: number }>(
      `/properties/${encodeURIComponent(propertyId)}/activity-summary`,
    ),
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd portal && npm test -- apiRequestWithTotal estimateStatusApiValues listForPropertyParams
```

- [ ] **Step 7: Run the gates**

```bash
cd portal && npm run typecheck && npm run lint
```

- [ ] **Step 8: Commit**

```bash
cd portal && git add src/api/client.ts src/api/estimates.ts src/api/tasks.ts src/api/resources.ts src/lib/estimateStatusFilter.ts tests/apiRequestWithTotal.test.ts tests/estimateStatusApiValues.test.ts tests/listForPropertyParams.test.ts
git commit -m "feat: add per-property list calls and total-count reads"
```

---

### Task 5: Extract a generic `StatusFilterDropdown`

`EstimateStatusFilter` hardcodes `ESTIMATE_FILTER_STATUSES`. The tasks tab needs the same control driven by options fetched at runtime, because task statuses are company-configurable.

**Files:**
- Create: `portal/src/components/common/StatusFilterDropdown.tsx`
- Modify: `portal/src/components/common/EstimateStatusFilter.tsx`
- Test: `portal/tests/StatusFilterDropdown.test.tsx`
- Verify unchanged: `portal/tests/EstimatesPageStatusFilter.test.tsx`

**Interfaces:**
- Consumes: nothing.
- Produces: `StatusFilterDropdown` with props `{ options: FilterOption[]; selected: string[]; onChange: (next: string[]) => void; allLabel?: string; label?: string }` where `FilterOption = { value: string; label: string }`. `allLabel` defaults to `"All Status"`; `label` is the dropdown's `aria-label`, defaulting to `"Filter by status"`.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/StatusFilterDropdown.test.tsx`:

```tsx
/**
 * StatusFilterDropdown — the generic multi-select behind both the estimates
 * status filter and the property activity panel's per-tab filters.
 */
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StatusFilterDropdown } from "../src/components/common/StatusFilterDropdown";

afterEach(cleanup);

const OPTIONS = [
  { value: "todo", label: "To Do" },
  { value: "doing", label: "In Progress" },
  { value: "done", label: "Done" },
];

describe("StatusFilterDropdown", () => {
  test("summarizes an all-selected state", () => {
    render(<StatusFilterDropdown options={OPTIONS}
      selected={["todo", "doing", "done"]} onChange={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveTextContent("All Status");
  });

  test("names the single selected option", () => {
    render(<StatusFilterDropdown options={OPTIONS} selected={["doing"]} onChange={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveTextContent("In Progress");
  });

  test("counts a partial selection", () => {
    render(<StatusFilterDropdown options={OPTIONS} selected={["todo", "done"]} onChange={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveTextContent("2 statuses");
  });

  test("toggling an option adds it in the options' own order", async () => {
    const onChange = vi.fn();
    render(<StatusFilterDropdown options={OPTIONS} selected={["done"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button"));
    await userEvent.click(screen.getByLabelText("To Do"));
    // Canonical order, not click order — persisted selections stay stable.
    expect(onChange).toHaveBeenCalledWith(["todo", "done"]);
  });

  test("the All row selects everything when not all are selected", async () => {
    const onChange = vi.fn();
    render(<StatusFilterDropdown options={OPTIONS} selected={["todo"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button"));
    await userEvent.click(screen.getByLabelText("All Status"));
    expect(onChange).toHaveBeenCalledWith(["todo", "doing", "done"]);
  });

  test("the All row clears everything when all are selected", async () => {
    const onChange = vi.fn();
    render(<StatusFilterDropdown options={OPTIONS}
      selected={["todo", "doing", "done"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button"));
    await userEvent.click(screen.getByLabelText("All Status"));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  test("Escape closes the open dropdown", async () => {
    render(<StatusFilterDropdown options={OPTIONS} selected={[]} onChange={vi.fn()} />);
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("group")).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("group")).not.toBeInTheDocument();
  });

  test("an empty options list still renders without crashing", () => {
    render(<StatusFilterDropdown options={[]} selected={[]} onChange={vi.fn()} />);
    // Task statuses arrive asynchronously; the control must survive the gap.
    expect(screen.getByRole("button")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- StatusFilterDropdown
```

Expected: FAIL — the module doesn't exist.

- [ ] **Step 3: Create the generic component**

Create `portal/src/components/common/StatusFilterDropdown.tsx`. This is the body of `EstimateStatusFilter` with the option list and summary logic lifted into props:

```tsx
import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

export interface FilterOption {
  /** Stable key sent to the API / persisted. */
  value: string;
  /** User-facing label. */
  label: string;
}

export interface StatusFilterDropdownProps {
  options: FilterOption[];
  selected: string[];
  onChange: (next: string[]) => void;
  /** Label for the select-all row and the all-selected summary. */
  allLabel?: string;
  /** aria-label for the dropdown panel. */
  label?: string;
}

interface CheckboxRowProps {
  label: string;
  checked: boolean;
  onToggle: () => void;
}

function CheckboxRow({ label, checked, onToggle }: CheckboxRowProps) {
  return (
    <label className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer select-none">
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        aria-label={label}
        className="h-4 w-4 rounded border-gray-300 text-brand focus:ring-slate-500"
      />
      {label}
    </label>
  );
}

/** Every option selected. An empty option list is never "all selected" —
 *  otherwise a still-loading filter would claim to show everything. */
export function isAllOf(options: FilterOption[], selected: string[]): boolean {
  return options.length > 0 && options.every((o) => selected.includes(o.value));
}

/** Toggle one option, re-ordered to the options' canonical order so persisted
 *  selections and summaries stay stable regardless of click order. */
export function toggleOption(
  options: FilterOption[],
  selected: string[],
  value: string,
): string[] {
  const next = selected.includes(value)
    ? selected.filter((entry) => entry !== value)
    : [...selected, value];
  return options.map((o) => o.value).filter((entry) => next.includes(entry));
}

function summarize(
  options: FilterOption[],
  selected: string[],
  allLabel: string,
): string {
  if (isAllOf(options, selected)) return allLabel;
  if (selected.length === 0) return "No statuses";
  if (selected.length === 1) {
    const match = options.find((o) => o.value === selected[0]);
    return match ? match.label : "1 status";
  }
  return `${selected.length} statuses`;
}

/**
 * Multi-select status filter: a trigger button summarizing the selection over a
 * dropdown of checkboxes. Options are injected so the same control serves both
 * the fixed estimate statuses and the company-configurable task statuses.
 */
export function StatusFilterDropdown({
  options,
  selected,
  onChange,
  allLabel = "All Status",
  label = "Filter by status",
}: StatusFilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isOpen) return undefined;
    const onPointerDown = (event: MouseEvent) => {
      if (containerRef.current?.contains(event.target as Node)) return;
      setIsOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onEscape);
    };
  }, [isOpen]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-haspopup="true"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center justify-between gap-2 min-w-[150px] px-4 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-500"
      >
        <span className="text-sm text-gray-700">
          {summarize(options, selected, allLabel)}
        </span>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </button>
      {isOpen && (
        /* Anchored left on mobile: the trigger sits at the viewport's left
           edge there, so a right-anchored panel (wider than the trigger)
           would overhang off-screen and clip its checkboxes. */
        <div
          role="group"
          aria-label={label}
          className="absolute left-0 sm:left-auto sm:right-0 z-50 mt-1 w-56 rounded-lg border border-gray-200 bg-white py-1 shadow-lg"
        >
          <CheckboxRow
            label={allLabel}
            checked={isAllOf(options, selected)}
            onToggle={() =>
              onChange(isAllOf(options, selected) ? [] : options.map((o) => o.value))
            }
          />
          <div className="my-1 border-t border-gray-100" />
          {options.map((option) => (
            <CheckboxRow
              key={option.value}
              label={option.label}
              checked={selected.includes(option.value)}
              onToggle={() => onChange(toggleOption(options, selected, option.value))}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default StatusFilterDropdown;
```

- [ ] **Step 4: Rewrite `EstimateStatusFilter` as a wrapper**

Replace the whole body of `portal/src/components/common/EstimateStatusFilter.tsx` with:

```tsx
import { ESTIMATE_FILTER_STATUSES } from "../../lib/estimateStatusFilter";
import { StatusFilterDropdown } from "./StatusFilterDropdown";

export interface EstimateStatusFilterProps {
  /** Currently selected status values (normalized keys). */
  selected: string[];
  /** Called with the next selection whenever a checkbox is toggled. */
  onChange: (next: string[]) => void;
}

/**
 * Multi-select status filter for the Estimates page — the generic
 * {@link StatusFilterDropdown} bound to the fixed estimate status list.
 */
export function EstimateStatusFilter({
  selected,
  onChange,
}: EstimateStatusFilterProps) {
  return (
    <StatusFilterDropdown
      options={ESTIMATE_FILTER_STATUSES}
      selected={selected}
      onChange={onChange}
    />
  );
}

export default EstimateStatusFilter;
```

- [ ] **Step 5: Run both test files to verify the extraction is behavior-preserving**

```bash
cd portal && npm test -- StatusFilterDropdown EstimatesPageStatusFilter
```

Expected: PASS. **`EstimatesPageStatusFilter.test.tsx` must pass without being edited** — it is the regression net for this refactor. If it fails, the extraction changed behavior; fix the component, not the test.

- [ ] **Step 6: Run the gates**

```bash
cd portal && npm run typecheck && npm run lint
```

- [ ] **Step 7: Commit**

```bash
cd portal && git add src/components/common/StatusFilterDropdown.tsx src/components/common/EstimateStatusFilter.tsx tests/StatusFilterDropdown.test.tsx
git commit -m "refactor: extract a generic status filter dropdown"
```

---

### Task 6: `PropertyActivityPanel`

The panel itself: tabs, per-tab filters, fetching, scroll box, footer.

**Files:**
- Create: `portal/src/components/properties/propertyActivityConstants.ts`
- Create: `portal/src/components/properties/PropertyActivityPanel.tsx`
- Test: `portal/tests/PropertyActivityPanel.test.tsx`

**Interfaces:**
- Consumes: `estimatesApi.listForProperty`, `tasksApi.listForProperty`, `propertiesApi.activitySummary` (Task 4); `StatusFilterDropdown` (Task 5); `taskHeadline` from `../../lib/taskDisplay`; `getStatusColor` from `../../lib/estimateStatusColors`; `formatCurrency` from `../../lib/format`; `getEstimateDetailsPath` from `../../lib/estimateNavigation`; `getEntityId` from `../../api/client`.
- Produces: `<PropertyActivityPanel propertyId={string} taskStatuses={TaskStatus[]} />`.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/PropertyActivityPanel.test.tsx`:

```tsx
/**
 * PropertyActivityPanel — the Properties page's Estimates/Tasks surface.
 *
 * The panel's job is to stay one fixed-height box whatever the data: tabs
 * carry unfiltered totals, the body shows a page of rows, and the jump-out
 * link is always there — including when the property has nothing on it.
 */
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import type { Estimate, Task, TaskStatus } from "../src/types/api";

afterEach(cleanup);

const PROPERTY_ID = "prop-1";

const TASK_STATUSES: TaskStatus[] = [
  { _id: "s1", name: "To Do", order: 0 },
  { _id: "s2", name: "Done", order: 1 },
] as unknown as TaskStatus[];

function makeEstimate(id: string, title: string): Estimate {
  return {
    _id: id, title, status: "draft", property: PROPERTY_ID,
    grand_total: 100, updated_at: "2026-07-01T00:00:00+00:00",
  } as unknown as Estimate;
}

function makeTask(id: string, description: string, createdAt: string): Task {
  return {
    _id: id, description, property: PROPERTY_ID, photos: [],
    status: "s1", created_at: createdAt,
  } as unknown as Task;
}

const listForProperty = vi.fn();
const tasksListForProperty = vi.fn();
const activitySummary = vi.fn();

vi.mock("../src/api/estimates", () => ({
  estimatesApi: { listForProperty: (...args: unknown[]) => listForProperty(...args) },
}));
vi.mock("../src/api/tasks", () => ({
  tasksApi: { listForProperty: (...args: unknown[]) => tasksListForProperty(...args) },
}));
vi.mock("../src/api/resources", () => ({
  propertiesApi: { activitySummary: (...args: unknown[]) => activitySummary(...args) },
}));

async function renderPanel() {
  const { PropertyActivityPanel } = await import(
    "../src/components/properties/PropertyActivityPanel"
  );
  return render(
    <MemoryRouter>
      <PropertyActivityPanel propertyId={PROPERTY_ID} taskStatuses={TASK_STATUSES} />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  sessionStorage.clear();
  listForProperty.mockReset();
  tasksListForProperty.mockReset();
  activitySummary.mockReset();
  listForProperty.mockResolvedValue({
    data: [makeEstimate("e1", "Spring cleanup")], total: 1,
  });
  tasksListForProperty.mockResolvedValue({
    data: [
      makeTask("t1", "Newer note", "2026-07-02T00:00:00+00:00"),
      makeTask("t2", "Older note", "2026-07-01T00:00:00+00:00"),
    ],
    total: 2,
  });
  activitySummary.mockResolvedValue({ estimate_count: 47, task_count: 12 });
});

describe("PropertyActivityPanel", () => {
  test("shows unfiltered totals on both tabs", async () => {
    await renderPanel();
    expect(await screen.findByRole("tab", { name: /Estimates 47/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Tasks 12/ })).toBeInTheDocument();
  });

  test("opens on Estimates and switches to Tasks", async () => {
    await renderPanel();
    expect(await screen.findByText("Spring cleanup")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: /Tasks/ }));

    expect(await screen.findByText("Newer note")).toBeInTheDocument();
    expect(screen.queryByText("Spring cleanup")).not.toBeInTheDocument();
  });

  test("renders tasks in the order the server returned them", async () => {
    await renderPanel();
    await userEvent.click(screen.getByRole("tab", { name: /Tasks/ }));

    const rows = await screen.findAllByRole("link");
    expect(rows[0]).toHaveTextContent("Newer note");
    expect(rows[1]).toHaveTextContent("Older note");
  });

  test("requests tasks newest-created first", async () => {
    await renderPanel();
    await userEvent.click(screen.getByRole("tab", { name: /Tasks/ }));

    await waitFor(() => expect(tasksListForProperty).toHaveBeenCalled());
    // Ordering itself is pinned in the API wrapper (see the listForProperty
    // test in Task 4); what the panel owns is asking for one page of this
    // property's tasks.
    const [, options] = tasksListForProperty.mock.calls[0];
    expect(options).toMatchObject({ propertyId: PROPERTY_ID, limit: 15 });
  });

  test("shows the truncation note only when rows are capped", async () => {
    listForProperty.mockResolvedValue({
      data: Array.from({ length: 15 }, (_, i) => makeEstimate(`e${i}`, `Job ${i}`)),
      total: 31,
    });
    await renderPanel();
    expect(await screen.findByText(/Showing 15 of 31/)).toBeInTheDocument();
  });

  test("hides the truncation note when everything is shown", async () => {
    await renderPanel();
    await screen.findByText("Spring cleanup");
    expect(screen.queryByText(/Showing/)).not.toBeInTheDocument();
  });

  test("always offers a jump-out link, even with no rows at all", async () => {
    listForProperty.mockResolvedValue({ data: [], total: 0 });
    activitySummary.mockResolvedValue({ estimate_count: 0, task_count: 0 });
    await renderPanel();

    const link = await screen.findByRole("link", { name: /View all estimates/ });
    expect(link).toHaveAttribute(
      "href", `/estimates?propertyId=${PROPERTY_ID}`);
  });

  test("the tasks tab links out to the tasks page for this property", async () => {
    await renderPanel();
    await userEvent.click(screen.getByRole("tab", { name: /Tasks/ }));

    const link = await screen.findByRole("link", { name: /View all tasks/ });
    expect(link).toHaveAttribute("href", `/tasks?propertyId=${PROPERTY_ID}`);
  });

  test("distinguishes an empty property from an empty filter result", async () => {
    listForProperty.mockResolvedValue({ data: [], total: 0 });
    activitySummary.mockResolvedValue({ estimate_count: 0, task_count: 0 });
    await renderPanel();
    expect(await screen.findByText("No estimates yet.")).toBeInTheDocument();
  });

  test("says no matches when a filter empties a non-empty property", async () => {
    listForProperty.mockResolvedValue({ data: [], total: 0 });
    await renderPanel(); // summary still reports 47 estimates
    expect(
      await screen.findByText("No estimates match this filter."),
    ).toBeInTheDocument();
  });

  test("keeps each tab's filter independent", async () => {
    await renderPanel();
    await screen.findByText("Spring cleanup");

    await userEvent.click(screen.getByRole("button", { name: /All Status/ }));
    await userEvent.click(screen.getByLabelText("Won"));
    await userEvent.keyboard("{Escape}");

    await userEvent.click(screen.getByRole("tab", { name: /Tasks/ }));
    // The tasks tab must not inherit the estimates tab's narrowed selection.
    expect(screen.getByRole("button", { name: /All Status/ })).toBeInTheDocument();
  });

  test("estimate rows navigate on Enter", async () => {
    await renderPanel();
    const row = await screen.findByRole("link", { name: /Spring cleanup/ });
    row.focus();
    await userEvent.keyboard("{Enter}");
    // Navigation is asserted by the row exposing a link role with an href;
    // the router records the change.
    expect(row).toHaveAttribute("href");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- PropertyActivityPanel
```

Expected: FAIL — the component module doesn't exist.

- [ ] **Step 3: Add the shared constant**

Create `portal/src/components/properties/propertyActivityConstants.ts`:

```ts
/** Rows fetched per tab in the property activity panel.
 *  The panel's box shows about seven at a time; the rest are reached by
 *  scrolling inside it. Anything beyond this is the "View all" link's job. */
export const PANEL_PAGE_SIZE = 15;

/** sessionStorage key holding both tabs' status selections. */
export const ACTIVITY_FILTER_STORAGE_KEY = "propertyActivityFilters";
```

- [ ] **Step 4: Implement the panel**

Create `portal/src/components/properties/PropertyActivityPanel.tsx`. Build it in this shape:

```tsx
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { estimatesApi } from "../../api/estimates";
import { tasksApi } from "../../api/tasks";
import { propertiesApi } from "../../api/resources";
import { getEntityId } from "../../api/client";
import { formatCurrency } from "../../lib/format";
import { taskHeadline } from "../../lib/taskDisplay";
import { getStatusColor } from "../../lib/estimateStatusColors";
import { getEstimateDetailsPath } from "../../lib/estimateNavigation";
import {
  ALL_FILTER_STATUS_VALUES,
  ESTIMATE_FILTER_STATUSES,
  selectionIncludesArchived,
} from "../../lib/estimateStatusFilter";
import { StatusFilterDropdown } from "../common/StatusFilterDropdown";
import type { Estimate, Task, TaskStatus } from "../../types/api";
import {
  ACTIVITY_FILTER_STORAGE_KEY,
  PANEL_PAGE_SIZE,
} from "./propertyActivityConstants";

type TabKey = "estimates" | "tasks";

/** Archived rides alongside the configured task statuses, mirroring how the
 *  estimates filter treats it — it is a visibility flag, not a status. */
const TASK_ARCHIVED_VALUE = "__archived__";

export interface PropertyActivityPanelProps {
  propertyId: string;
  /** Company-configured task statuses, fetched once by the page. */
  taskStatuses: TaskStatus[];
}
```

Implementation requirements, each covered by a test above:

1. **State:** `activeTab`, `estimateFilter: string[]`, `taskFilter: string[]`, one `{ rows, total, isLoading, error }` slice per tab, and `summary: { estimate_count, task_count } | null`. The render skeleton below reads the active tab's slice destructured as `{ rows, total: rowTotal, isLoading }` — keep those names so the two match.
2. **Filter defaults — archived excluded on both tabs**, matching what both endpoints do by default and therefore what the Properties page shows today. Estimates default to every option *except* `"archived"`; tasks default to every configured status id *without* `TASK_ARCHIVED_VALUE`. Define these as module constants so the persistence fallback and any reset path share them:

```tsx
const DEFAULT_ESTIMATE_FILTER = ALL_FILTER_STATUS_VALUES.filter(
  (value) => value !== "archived",
);
const defaultTaskFilter = (statuses: TaskStatus[]): string[] =>
  statuses.map((status) => getEntityId(status));
```

3. **Persistence:** hydrate both selections from `sessionStorage[ACTIVITY_FILTER_STORAGE_KEY]`, shaped `{ estimates: string[]; tasks: string[] }`; write on every change. A malformed or absent value falls back to the defaults — wrap the `JSON.parse` in try/catch.
4. **Task filter options:** `taskStatuses.map((s) => ({ value: getEntityId(s), label: s.name }))` plus a trailing `{ value: TASK_ARCHIVED_VALUE, label: "Archived" }`.
5. **Fetching:** one `useEffect` keyed on `[propertyId, activeTab, activeFilter]`. Only the active tab fetches rows; the summary fetches on `propertyId` alone. Guard against out-of-order responses with a `let cancelled = false` flag set in the effect **body** (re-armed each run, not only in cleanup — a cleanup-only flag stays stuck after StrictMode's double-invoke).
5a. **Cache.** Results are memoized in a `useRef<Map<string, { rows; total }>>` keyed by `` `${propertyId}|${activeTab}|${selection.join(",")}` ``, so re-selecting a property or flipping back to a tab paints immediately instead of re-fetching. On a cache hit, render from it and skip the request. The cache is cleared wholesale when `PROPERTIES_CHANGED_EVENT` fires (imported from `../Layout/agentMutationEvents`, the same event `PropertiesPage` already listens to) — a Maple-driven create or delete invalidates counts the panel can't otherwise know changed.
6. **Status params:** estimates pass the normalized keys straight to `estimatesApi.listForProperty` (which expands them) plus `includeArchived: selectionIncludesArchived(estimateFilter)`. Tasks pass `statusIds: taskFilter.filter((v) => v !== TASK_ARCHIVED_VALUE)` and `includeArchived: taskFilter.includes(TASK_ARCHIVED_VALUE)`.
7. **Empty selection short-circuit:** if a tab's selection is empty, render "No estimates match this filter." without issuing a request — an empty `status` list would otherwise mean "no filter" server-side and show everything.
8. **Markup:** `role="tablist"` wrapping two `role="tab"` buttons labelled `Estimates {summary.estimate_count}` / `Tasks {summary.task_count}`; the filter dropdown on the same row; a `max-h-80 overflow-y-auto` body holding a `table` with the sticky `thead` pattern from the old page code; a footer with the truncation note (only when `rows.length < total`) and the always-rendered `<Link>`.
9. **Rows:** estimate rows keep `role="link"`, `tabIndex={0}`, click + Enter/Space navigation via `getEstimateDetailsPath`. Task rows do the same, targeting `/tasks?propertyId=<id>&taskId=<id>`.
10. **Status pills:** estimates reuse `getStatusColor`; tasks render the status name from `taskStatuses` in a neutral gray pill (task statuses are user-defined and have no color mapping).
11. **Mobile.** The panel sits inside the page's existing `@container` (`PropertiesPage.tsx:531`), so use container queries, not viewport breakpoints. Below `@lg`: the tab strip goes full-width (`flex-1` on each tab) with the filter dropping to its own row beneath, and column 2 (Value / Created date) moves into a subline under the title — hide the `<th>`/`<td>` with `hidden @lg:table-cell` and render the same value inside column 1 as a `<span className="block @lg:hidden text-xs text-gray-500">`. The "View all →" link stays visible at every width; it's the primary escape hatch on a small screen.

The render skeleton, with the two tabs sharing one body so the box height can't
drift between them:

```tsx
  const isEstimates = activeTab === "estimates";
  const total = isEstimates ? summary?.estimate_count : summary?.task_count;
  const viewAllHref = isEstimates
    ? `/estimates?propertyId=${encodeURIComponent(propertyId)}`
    : `/tasks?propertyId=${encodeURIComponent(propertyId)}`;

  return (
    <div className="rounded-lg border border-gray-200">
      <div className="flex flex-col @lg:flex-row @lg:items-center gap-2 border-b border-gray-200 px-3 py-2">
        <div role="tablist" aria-label="Property activity" className="flex flex-1 gap-1">
          {(["estimates", "tasks"] as TabKey[]).map((tab) => (
            <button
              key={tab}
              role="tab"
              type="button"
              aria-selected={activeTab === tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 @lg:flex-none rounded-lg px-3 py-1.5 text-sm ${
                activeTab === tab
                  ? "bg-gray-100 font-semibold text-gray-900"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {tab === "estimates" ? "Estimates" : "Tasks"}{" "}
              <span className="text-gray-500">
                {tab === "estimates" ? summary?.estimate_count ?? "" : summary?.task_count ?? ""}
              </span>
            </button>
          ))}
        </div>
        <StatusFilterDropdown
          options={isEstimates ? ESTIMATE_FILTER_STATUSES : taskFilterOptions}
          selected={isEstimates ? estimateFilter : taskFilter}
          onChange={isEstimates ? setEstimateFilter : setTaskFilter}
        />
      </div>

      <div className="max-h-80 overflow-y-auto overflow-x-auto">
        {/* One table element per tab, but identical structure and heights. */}
        {rows.length > 0 && (isEstimates ? renderEstimateTable() : renderTaskTable())}
        {rows.length === 0 && !isLoading && (
          <p className="px-4 py-10 text-sm text-gray-500">{emptyMessage}</p>
        )}
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-gray-200 px-3 py-2 text-sm">
        <span className="text-gray-500">
          {rowTotal !== null && rows.length < rowTotal
            ? `Showing ${rows.length} of ${rowTotal} matching`
            : ""}
        </span>
        <Link to={viewAllHref} className="text-blue-700 hover:underline whitespace-nowrap">
          {isEstimates
            ? `View all${total ? ` ${total}` : ""} estimates →`
            : `View all${total ? ` ${total}` : ""} tasks →`}
        </Link>
      </div>
    </div>
  );
```

`emptyMessage` distinguishes the two empty states from the summary, not the row
count — that's what separates "nothing here" from "nothing matches":

```tsx
  const hasAnyAtAll = isEstimates
    ? (summary?.estimate_count ?? 0) > 0
    : (summary?.task_count ?? 0) > 0;
  const noun = isEstimates ? "estimates" : "tasks";
  const emptyMessage = hasAnyAtAll
    ? `No ${noun} match this filter.`
    : `No ${noun} yet.`;
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd portal && npm test -- PropertyActivityPanel
```

- [ ] **Step 6: Run the gates**

```bash
cd portal && npm run typecheck && npm run lint
```

- [ ] **Step 7: Commit**

```bash
cd portal && git add src/components/properties/PropertyActivityPanel.tsx src/components/properties/propertyActivityConstants.ts tests/PropertyActivityPanel.test.tsx
git commit -m "feat: add the property activity panel"
```

---

### Task 7: Wire the panel into PropertiesPage and defer the dialog's estimate load

**Files:**
- Modify: `portal/src/pages/PropertiesPage.tsx`
- Modify: `portal/src/components/properties/PropertyDialog.tsx`
- Test: `portal/tests/PropertiesPageEstimates.test.tsx` (rework), `portal/tests/PropertyDialogLazyEstimates.test.tsx` (new)

**Interfaces:**
- Consumes: `PropertyActivityPanel` (Task 6).
- Produces: a `PropertiesPage` that never calls `estimatesApi.list()`.

- [ ] **Step 1: Rewrite the existing estimates test**

`portal/tests/PropertiesPageEstimates.test.tsx` covers the block being deleted. Rewrite it to assert the page mounts the panel and no longer bulk-loads estimates. Keep the file's existing mocks for `propertiesApi`/`contactsApi`/`auth` and add:

```tsx
const listAllEstimates = vi.fn(async () => []);
vi.mock("../src/api/estimates", () => ({
  estimatesApi: {
    list: (...args: unknown[]) => listAllEstimates(...args),
    listForProperty: vi.fn(async () => ({ data: [], total: 0 })),
  },
}));

test("does not bulk-load company estimates on page render", async () => {
  render(<MemoryRouter><PropertiesPage /></MemoryRouter>);
  await screen.findByText("Maple House");
  // The whole point of the change: the page used to fetch every estimate in
  // the company and filter client-side.
  expect(listAllEstimates).not.toHaveBeenCalled();
});

test("renders the activity panel for the selected property", async () => {
  render(<MemoryRouter><PropertiesPage /></MemoryRouter>);
  expect(await screen.findByRole("tab", { name: /Estimates/ })).toBeInTheDocument();
});
```

- [ ] **Step 2: Write the dialog test**

Create `portal/tests/PropertyDialogLazyEstimates.test.tsx`:

```tsx
/**
 * PropertyDialog fetches the company estimate list itself, on open.
 *
 * Its EstimatesPicker is the only consumer of the full list once the activity
 * panel queries per property — leaving the fetch at page level would keep the
 * page-load cost the panel exists to remove.
 */
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

afterEach(cleanup);

const listEstimates = vi.fn(async () => []);
vi.mock("../src/api/estimates", () => ({
  estimatesApi: { list: (...args: unknown[]) => listEstimates(...args) },
}));
vi.mock("../src/api/resources", () => ({
  propertiesApi: { create: vi.fn(), update: vi.fn() },
  contactsApi: { list: vi.fn(async () => []) },
}));

beforeEach(() => listEstimates.mockClear());

describe("PropertyDialog estimate loading", () => {
  test("does not fetch while closed", async () => {
    const { PropertyDialog } = await import(
      "../src/components/properties/PropertyDialog");
    render(<MemoryRouter>
      <PropertyDialog open={false} onClose={vi.fn()} editingProperty={null}
        availableContacts={[]} onSubmitted={vi.fn()} />
    </MemoryRouter>);
    expect(listEstimates).not.toHaveBeenCalled();
  });

  test("fetches once the dialog opens", async () => {
    const { PropertyDialog } = await import(
      "../src/components/properties/PropertyDialog");
    render(<MemoryRouter>
      <PropertyDialog open onClose={vi.fn()} editingProperty={null}
        availableContacts={[]} onSubmitted={vi.fn()} />
    </MemoryRouter>);
    await waitFor(() => expect(listEstimates).toHaveBeenCalledTimes(1));
  });
});
```

- [ ] **Step 3: Run both tests to verify they fail**

```bash
cd portal && npm test -- PropertiesPageEstimates PropertyDialogLazyEstimates
```

Expected: FAIL — the page still calls `estimatesApi.list`, renders no tabs, and the dialog still takes estimates as a prop.

- [ ] **Step 4: Slim down `PropertiesPage.tsx`**

Delete from `portal/src/pages/PropertiesPage.tsx`:

- the `estimates` state and its `estimatesApi.list(COMPANY_ID)` call inside `loadData` (lines 99, 137-144)
- the `selectedPropertyEstimates` memo (lines 301-314)
- `handleEstimateRowNavigation` / `handleEstimateRowKeyDown` (lines 372-382)
- the helpers `normalizeEstimateStatus`, `estimateStatusLabel`, `estimateStatusStyle` (lines 46-64) and the now-unused imports (`formatCurrency`, `getEstimateDetailsPath`, `getStatusColor`, `estimatesApi`, `Estimate`, `useNavigate` if nothing else uses it)
- the whole Estimates `<div className="space-y-2">` block (lines 584-675)
- the `availableEstimates={estimates}` prop on `<PropertyDialog>`

Add task-status loading and render the panel where the estimates block was:

```tsx
const [taskStatuses, setTaskStatuses] = useState<TaskStatus[]>([]);
```

Inside `loadData`, add `taskStatusesApi.list(COMPANY_ID)` to the existing `Promise.all` and `setTaskStatuses(statusData || [])`. Then, replacing the deleted block:

```tsx
                  <PropertyActivityPanel
                    propertyId={getEntityId(selectedProperty)}
                    taskStatuses={taskStatuses}
                  />
```

- [ ] **Step 5: Move the estimate fetch into `PropertyDialog`**

In `portal/src/components/properties/PropertyDialog.tsx`, drop `availableEstimates` from the props interface and load it internally:

```tsx
  const [availableEstimates, setAvailableEstimates] = useState<Estimate[]>([]);

  // Fetched on open, not at page level: the picker is the only consumer of the
  // full company list, and hoisting it would restore the page-load cost the
  // activity panel exists to remove.
  useEffect(() => {
    if (!open) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const data = await estimatesApi.list(COMPANY_ID);
        if (!cancelled) setAvailableEstimates(data || []);
      } catch {
        // The picker degrades to "No estimates available to link."
        if (!cancelled) setAvailableEstimates([]);
      }
    })();
    return () => { cancelled = true; };
  }, [open]);
```

Note `cancelled` is declared inside the effect body, so StrictMode's double-invoke re-arms it — a flag hoisted outside would stay `true` after the first cleanup and silently discard the second run's data.

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd portal && npm test -- PropertiesPageEstimates PropertyDialogLazyEstimates PropertyActivityPanel
```

- [ ] **Step 7: Run the gates**

```bash
cd portal && npm run typecheck && npm run lint
```

- [ ] **Step 8: Commit**

```bash
cd portal && git add src/pages/PropertiesPage.tsx src/components/properties/PropertyDialog.tsx tests/PropertiesPageEstimates.test.tsx tests/PropertyDialogLazyEstimates.test.tsx
git commit -m "feat: show estimates and tasks in the property activity panel"
```

---

### Task 8: TasksPage deep links

**Files:**
- Modify: `portal/src/pages/TasksPage.tsx`
- Test: `portal/tests/TasksPageDeepLink.test.tsx`

**Interfaces:**
- Consumes: the links produced by Task 6.
- Produces: `/tasks?propertyId=<id>&taskId=<id>` seeding the property filter and opening that task's dialog.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/TasksPageDeepLink.test.tsx`:

```tsx
/**
 * TasksPage query-param seeding.
 *
 * The property activity panel links here; without seeding, "View all tasks"
 * would dump the user into every task in the company.
 */
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { Property, Task } from "../src/types/api";

afterEach(cleanup);

const PROPERTY_ID = "prop-1";
const property = {
  _id: PROPERTY_ID, name: "Maple House", street: "1 Maple St", city: "Toronto",
} as unknown as Property;
const task = {
  _id: "task-1", description: "Fix the gate", property: PROPERTY_ID, photos: [],
} as unknown as Task;

const tasksList = vi.fn(async () => [task]);
vi.mock("../src/api/tasks", () => ({
  tasksApi: { list: (...a: unknown[]) => tasksList(...a) },
  taskStatusesApi: { list: vi.fn(async () => []) },
}));
vi.mock("../src/api/resources", () => ({
  propertiesApi: { list: vi.fn(async () => [property]) },
  contactsApi: { list: vi.fn(async () => []) },
}));
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => ({ role: "Owner" }) }));

async function renderAt(path: string) {
  const { default: TasksPage } = await import("../src/pages/TasksPage");
  return render(<MemoryRouter initialEntries={[path]}><TasksPage /></MemoryRouter>);
}

describe("TasksPage deep links", () => {
  test("propertyId seeds the property filter", async () => {
    await renderAt(`/tasks?propertyId=${PROPERTY_ID}`);
    await waitFor(() => expect(tasksList).toHaveBeenCalled());
    const [, options] = tasksList.mock.calls.at(-1) as [unknown, { property?: string }];
    expect(options.property).toBe(PROPERTY_ID);
  });

  test("taskId opens that task's dialog", async () => {
    await renderAt(`/tasks?taskId=task-1`);
    expect(await screen.findByDisplayValue("Fix the gate")).toBeInTheDocument();
  });

  test("no params leaves the page unfiltered", async () => {
    await renderAt("/tasks");
    await waitFor(() => expect(tasksList).toHaveBeenCalled());
    const [, options] = tasksList.mock.calls.at(-1) as [unknown, { property?: string }];
    expect(options.property).toBeUndefined();
  });

  test("an unknown taskId degrades to the plain list", async () => {
    await renderAt("/tasks?taskId=does-not-exist");
    // No dialog, no crash — the list still renders.
    expect(await screen.findByText("Fix the gate")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- TasksPageDeepLink
```

Expected: FAIL — `TasksPage` reads no URL parameters.

- [ ] **Step 3: Seed from the URL**

In `portal/src/pages/TasksPage.tsx`, import `useSearchParams` from `react-router-dom` and seed both pieces of state. Initialize `propertyFilter` from the param so the first fetch already carries it — setting it in an effect would fire an unfiltered request first:

```tsx
const [searchParams, setSearchParams] = useSearchParams();
const [propertyFilter, setPropertyFilter] = useState(
  () => searchParams.get("propertyId") || "",
);
```

Then, once tasks have loaded, open the requested task and clear the param so a refresh doesn't reopen it:

```tsx
  const requestedTaskId = searchParams.get("taskId") || "";

  useEffect(() => {
    if (!requestedTaskId || tasks.length === 0) return;
    const match = tasks.find((candidate) => getEntityId(candidate) === requestedTaskId);
    // An unknown id is not an error: the task may have been deleted since the
    // link was made. Fall through to the plain list.
    if (match) setEditingTask(match);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete("taskId");
      return next;
    }, { replace: true });
  }, [requestedTaskId, tasks, setSearchParams]);
```

Match the existing state-setter names in that file — if the dialog is driven by something other than `setEditingTask`, use whatever it actually is.

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- TasksPageDeepLink
```

- [ ] **Step 5: Run the gates and the page's existing tests**

```bash
cd portal && npm run typecheck && npm run lint && npm test -- TasksPage
```

- [ ] **Step 6: Commit**

```bash
cd portal && git add src/pages/TasksPage.tsx tests/TasksPageDeepLink.test.tsx
git commit -m "feat: seed the tasks page from propertyId and taskId params"
```

---

### Task 9: EstimatesPage property filter

The last dependency of the panel's "View all estimates →" link. EstimatesPage has search and status filters but nothing for property.

**Files:**
- Modify: `portal/src/pages/EstimatesPage.tsx`
- Test: `portal/tests/EstimatesPagePropertyFilter.test.tsx`

**Interfaces:**
- Consumes: the link produced by Task 6.
- Produces: `/estimates?propertyId=<id>` showing only that property's estimates.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/EstimatesPagePropertyFilter.test.tsx`:

```tsx
/**
 * EstimatesPage property filter — the target of the activity panel's
 * "View all estimates" link.
 */
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import type { Estimate, Property } from "../src/types/api";

afterEach(cleanup);

const A = "prop-a";
const B = "prop-b";

const properties = [
  { _id: A, name: "Maple House", street: "1 Maple St", city: "Toronto" },
  { _id: B, name: "Oak Lodge", street: "2 Oak Ave", city: "Toronto" },
] as unknown as Property[];

function estimate(id: string, title: string, propertyId: string): Estimate {
  return {
    _id: id, title, status: "draft", property: propertyId, grand_total: 10,
    updated_at: "2026-07-01T00:00:00+00:00", created_at: "2026-07-01T00:00:00+00:00",
  } as unknown as Estimate;
}

vi.mock("../src/api/estimates", () => ({
  estimatesApi: {
    list: vi.fn(async () => [
      estimate("e1", "Maple job", A),
      estimate("e2", "Oak job", B),
    ]),
  },
}));
vi.mock("../src/api/resources", () => ({
  propertiesApi: { list: vi.fn(async () => properties) },
}));
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => ({ role: "Owner" }) }));

async function renderAt(path: string) {
  const { default: EstimatesPage } = await import("../src/pages/EstimatesPage");
  return render(
    <MemoryRouter initialEntries={[path]}><EstimatesPage /></MemoryRouter>);
}

describe("EstimatesPage property filter", () => {
  test("propertyId in the URL narrows to that property", async () => {
    await renderAt(`/estimates?propertyId=${A}`);
    expect(await screen.findByText("Maple job")).toBeInTheDocument();
    expect(screen.queryByText("Oak job")).not.toBeInTheDocument();
  });

  test("without the param every estimate shows", async () => {
    await renderAt("/estimates");
    expect(await screen.findByText("Maple job")).toBeInTheDocument();
    expect(screen.getByText("Oak job")).toBeInTheDocument();
  });

  test("an unknown propertyId shows nothing rather than everything", async () => {
    await renderAt("/estimates?propertyId=gone");
    // Failing open here would misrepresent a deleted property's estimates as
    // the whole company's.
    expect(await screen.findByText(/No estimates/i)).toBeInTheDocument();
  });

  test("the filter composes with search", async () => {
    await renderAt(`/estimates?propertyId=${A}`);
    await screen.findByText("Maple job");
    await userEvent.type(screen.getByPlaceholderText(/Search/i), "Oak");
    expect(screen.queryByText("Maple job")).not.toBeInTheDocument();
  });
});
```

Check the actual default status selection on that page before running — it persists to `sessionStorage` and defaults to `["draft"]`. The fixtures above all use `status: "draft"` so they survive it; if the page's default changes, these fixtures must match.

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- EstimatesPagePropertyFilter
```

Expected: FAIL — `propertyId` is ignored, so both estimates render in the first test.

- [ ] **Step 3: Add the filter**

In `portal/src/pages/EstimatesPage.tsx`:

```tsx
const [searchParams] = useSearchParams();
const propertyFilter = searchParams.get("propertyId") || "";
```

Add the predicate to the existing `filteredEstimates` memo, before the search filter, and add `propertyFilter` to its dependency array:

```tsx
      .filter((estimate) =>
        // Unknown ids match nothing rather than falling through to "show all":
        // a stale link must not present the whole company's estimates as one
        // property's.
        !propertyFilter || String(estimate.property || "") === propertyFilter)
```

Surface it visibly — a filter the user can't see or clear is a trap. Reuse the existing `FilterPills` component (`portal/src/components/common/FilterPills.tsx`), which `TasksPage` already uses for exactly this, adding a pill labelled with the property name whose dismiss clears the param.

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- EstimatesPagePropertyFilter
```

- [ ] **Step 5: Run the gates and the page's existing tests**

```bash
cd portal && npm run typecheck && npm run lint && npm test -- EstimatesPage
```

- [ ] **Step 6: Verify the full round trip by hand**

Start the dev servers, open a property with several estimates and tasks, and confirm: both tabs show counts; the filter narrows each independently; the panel's height doesn't change between tabs; "View all estimates →" lands on a filtered Estimates page; "View all tasks →" lands on a filtered Tasks page; clicking a task row opens that task.

- [ ] **Step 7: Commit**

```bash
cd portal && git add src/pages/EstimatesPage.tsx tests/EstimatesPagePropertyFilter.test.tsx
git commit -m "feat: filter the estimates page by property"
```

---

## Post-implementation

- **Drop the superseded task index.** Task 2 replaces `(company, property)` with `(company, property, created_at desc)`. Beanie does not drop indexes it no longer declares, so the old one lingers in Dev and Prod. Drop it manually during rollout: `db.tasks.dropIndex("company_1_property_1")`.
- **Documentation.** No CLAUDE.md change is required — this adds no new convention. The spec at [property-activity-panel.md](property-activity-panel.md) is the design record.
- **Changelog.** Not written automatically; the user triggers `/changelog` when they want one.
