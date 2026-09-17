# Notes v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the three plain-text `notes` strings with a shared, authored, timestamped notes feed (markdown body, image/video/PDF attachments) on work items, properties and contacts.

**Architecture:** One `notes` collection with a polymorphic parent (`work_item` / `property` / `contact`) served by one router, one service and one set of portal components. Work items gain a stable `id` so notes can point at them across the whole-array `PUT /estimates` write. Attachments reuse the Task GridFS pipeline, extracted into a bucket-parameterized `services/media_blobs.py`. Notes persist on their own endpoints, independent of whatever host dialog they live in.

**Tech Stack:** FastAPI + Beanie + Motor GridFS + Pillow + pytest (platform). React 18 + TypeScript + Vite + Tailwind 4 + react-markdown/remark-gfm + @mdxeditor/editor + vitest/@testing-library (portal).

**Spec:** [2026-09-17-notes-design.md](2026-09-17-notes-design.md)

## Global Constraints

- **TDD is mandatory** (CLAUDE.md). Failing test first, then implementation. Every task is ordered that way; do not reorder.
- **US spellings** in all code, comments, copy and test names.
- **Commits need explicit user approval each time** (CLAUDE.md). Each "Commit" step says what to commit; ask before running it. Never chain a commit off a prior approval. Never `--amend` without checking `HEAD` first.
- Commit message format: `<type>: <description>`, type ∈ `feat|fix|refactor|docs|test|chore|perf|ci`. End every commit message with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **Platform gates:** `./run_mypy.sh <path>` and `./run_ruff.sh <path>` scoped to touched files after every `.py` edit. `./run_bandit.sh` B110 count must stay at 13. Zero-error baseline for all three.
- **Portal gates:** `npm run typecheck` and the named `npm test -- <file>`. `npm run build` does not type-check.
- **Portal test assertions use plain vitest, NOT jest-dom** (controller ruling R1, pre-flight). `@testing-library/jest-dom` is a dependency but is never registered: `vite.config.js` has no `setupFiles`, no test imports it, and `tests/ThinkingIndicator.test.tsx` documents the choice. Any test block in this plan spelled with `toBeInTheDocument()`, `toBeDisabled()`, `toHaveAttribute()`, `toHaveTextContent()` or `toBeVisible()` must be rewritten in the house idiom. The assertion's *intent* is binding; its spelling is not. Translations, all in use by existing tests: present -> `expect(screen.getByRole(...)).toBeTruthy()`; absent -> `expect(screen.queryByText(...)).toBeNull()`; disabled -> `expect((el as HTMLButtonElement).disabled).toBe(true)`; attribute -> `expect(el.getAttribute("target")).toBe("_blank")`; text -> `expect(el.textContent).toContain("Notes")`.
- **Do not run the full test suite.** Run only the test files named in each task. Local MongoDB must be up: `cd platform && ./scripts/start_test_mongo.sh`.
- **Five separate git repos.** `platform/`, `portal/` and `documentation/` are each their own repo. Commit in the repo you changed.
- **Datetimes are aware UTC**: `datetime.now(timezone.utc)`. Never `utcnow()`.
- **`models/` never imports from `services/`** (`tests/test_models_layering.py`).
- **Beanie `Document.aggregate().to_list()` is broken** under the pinned driver. Use `Model.get_pymongo_collection().aggregate(pipeline)` + `async for`.
- **Decisions D1–D7** from the spec are final: `Estimate.notes` untouched; Owner may delete any note but not edit it; notes writable on every estimate status including Archived; duplicate does not copy notes; GridFS storage; collapsible bottom section in the Work Item dialog; migrated legacy notes are authored by the company's earliest-created Owner. **D8 (added 2026-09-17):** the estimate as a whole is a fourth parent type, `estimate`, shown at the bottom of the estimate page; `Estimate.notes` stays untouched and separate.
- **Cross-repo ordering:** platform Phase 1 deploys before portal Phase 1; platform Phase 2 deploys **and the backfill runs on prod** before portal Phase 4 ships. Phase 5's field removals ship only after the migration script has run on Dev and prod.
- Markdown rendering is a new `NoteMarkdown` component (Task 11); `ChangeLogPanel` and `MapleMarkdown` are dark-on-brand and are not touched.

---

# Phase 1 — Work item identity

### Task 1: `JobItem.id` on the model, request DTO and every constructor

**Files:**
- Modify: `platform/models/estimate.py:462-488` (`JobItem`) and its imports at `:1-17`
- Modify: `platform/routers/estimates.py:193-211` (`JobItemCreate`), `:919` (duplicate), `:1144-1294` (PUT rebuild)
- Modify: `platform/routers/estimate_helpers/job_item_builders.py:263`, `:302`, `:588` (the three `JobItem(` constructions)
- Test: `platform/tests/test_job_item_ids.py` (new)

**Interfaces:**
- Consumes: nothing new.
- Produces: `JobItem.id: str` (32-char hex by default; any `^[A-Za-z0-9-]{8,64}$` accepted from clients), `JobItemCreate.id: Optional[str]`, and the PUT preservation rules that Task 2 (portal) and Task 8 (cascade) rely on: an incoming `id` is kept; when **no** incoming item carries an id, ids are reused by position from the stored document; otherwise a missing id gets a fresh one.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_job_item_ids.py`:

```python
"""Work items carry a stable id so notes (and anything else) can point at them
across the whole-array PUT /estimates write. See the 2026-09-17 notes design."""

import re

from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from tests.helpers import run_on_portal

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def _insert_estimate(client: TestClient, company_id: str, descriptions: list[str]) -> dict:
    """Insert an estimate straight through Beanie (no AI path) and return its raw dict."""

    async def _insert():
        from models.estimate import Estimate, EstimateStatus, JobItem
        from services.estimate_readable_id import insert_estimate_with_readable_id

        estimate = Estimate(
            title="Id test",
            company=PydanticObjectId(company_id), status=EstimateStatus.DRAFT,
            created_by="tests",
            created_by_email="default.owner@example.com",
            job_items=[JobItem(description=d) for d in descriptions],
        )
        estimate = await insert_estimate_with_readable_id(estimate)
        return estimate.model_dump(mode="json", by_alias=True)

    return run_on_portal(client, _insert)


def test_job_item_gets_a_hex_id_by_default():
    from models.estimate import JobItem

    item = JobItem(description="Sod")
    assert _HEX32.match(item.id), item.id
    assert JobItem(description="Sod").id != item.id


def test_job_item_create_accepts_a_client_id():
    from routers.estimates import JobItemCreate

    dto = JobItemCreate(description="Sod", id="3f2a9c1e-7b4d-4e8a-9c2d-1a2b3c4d5e6f")
    assert dto.id == "3f2a9c1e-7b4d-4e8a-9c2d-1a2b3c4d5e6f"
    assert JobItemCreate(description="Sod").id is None


def test_put_preserves_ids_when_the_client_sends_them(client: TestClient, test_company_id: str):
    created = _insert_estimate(client, test_company_id, ["A", "B"])
    a, b = created["job_items"]

    # Reverse the order and edit a description: ids must follow their items.
    response = client.put(
        f"/estimates/{created['_id']}",
        json={"job_items": [
            {"id": b["id"], "description": "B edited"},
            {"id": a["id"], "description": "A"},
        ]},
    )
    assert response.status_code == 200, response.text
    items = response.json()["job_items"]
    assert [i["id"] for i in items] == [b["id"], a["id"]]
    assert items[0]["description"] == "B edited"

    client.delete(f"/estimates/{created['_id']}")


def test_put_without_any_ids_reuses_ids_by_position(client: TestClient, test_company_id: str):
    """A legacy client (a portal tab open across the deploy) sends no ids.
    Its items must keep the ids they already have, or every note orphans."""
    created = _insert_estimate(client, test_company_id, ["A", "B"])
    a, b = created["job_items"]

    response = client.put(
        f"/estimates/{created['_id']}",
        json={"job_items": [{"description": "A2"}, {"description": "B2"}, {"description": "C"}]},
    )
    assert response.status_code == 200, response.text
    items = response.json()["job_items"]
    assert items[0]["id"] == a["id"]
    assert items[1]["id"] == b["id"]
    assert _HEX32.match(items[2]["id"]) and items[2]["id"] not in {a["id"], b["id"]}

    client.delete(f"/estimates/{created['_id']}")


def test_put_with_some_ids_gives_the_rest_fresh_ids(client: TestClient, test_company_id: str):
    """Once any item carries an id the client is id-aware, so an id-less item
    is a new item — never a positional match onto a stored one."""
    created = _insert_estimate(client, test_company_id, ["A", "B"])
    a, b = created["job_items"]

    response = client.put(
        f"/estimates/{created['_id']}",
        json={"job_items": [{"description": "New first"}, {"id": b["id"], "description": "B"}]},
    )
    assert response.status_code == 200, response.text
    items = response.json()["job_items"]
    assert items[0]["id"] not in {a["id"], b["id"]}
    assert items[1]["id"] == b["id"]

    client.delete(f"/estimates/{created['_id']}")


def test_put_rejects_a_malformed_id(client: TestClient, test_company_id: str):
    created = _insert_estimate(client, test_company_id, ["A"])
    response = client.put(
        f"/estimates/{created['_id']}",
        json={"job_items": [{"id": "not valid!", "description": "A"}]},
    )
    assert response.status_code == 422
    client.delete(f"/estimates/{created['_id']}")


def test_duplicate_gives_the_copy_fresh_ids(client: TestClient, test_company_id: str):
    created = _insert_estimate(client, test_company_id, ["A", "B"])
    source_ids = {i["id"] for i in created["job_items"]}

    response = client.post(f"/estimates/{created['_id']}/duplicate")
    assert response.status_code == 200, response.text
    copy_ids = {i["id"] for i in response.json()["job_items"]}
    assert len(copy_ids) == 2
    assert copy_ids.isdisjoint(source_ids)

    client.delete(f"/estimates/{created['_id']}")
    client.delete(f"/estimates/{response.json()['_id']}")
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_job_item_ids.py -v
```

Expected: FAIL. `test_job_item_gets_a_hex_id_by_default` with `AttributeError: 'JobItem' object has no attribute 'id'`; the PUT tests with `KeyError: 'id'`.

- [ ] **Step 3: Add the field to the model**

In `platform/models/estimate.py`, add `from uuid import uuid4` to the imports, then inside `class JobItem(BaseModel)` add as the first field:

```python
class JobItem(BaseModel):
    # Stable identity for a work item. Everything else addresses a work item
    # by its position in `Estimate.job_items`, which shifts on every insert
    # or delete; notes (models/note.py) need something that does not.
    # Server-generated; the PUT path preserves whatever the client echoes
    # back (routers/estimates.py). Documents written before this field
    # existed get a fresh id on every load until
    # scripts/backfill_job_item_ids.py persists one — which is why that
    # backfill is a prerequisite for the notes feature.
    id: str = Field(default_factory=lambda: uuid4().hex)
    description: str
    ...
```

- [ ] **Step 4: Add the DTO field and pass it through every constructor**

In `platform/routers/estimates.py`, `JobItemCreate`:

```python
class JobItemCreate(BaseModel):
    model_config = {"extra": "ignore"}
    # Optional: absent from legacy clients. Validated loosely enough to
    # accept both the server's uuid4().hex and the portal's crypto.randomUUID().
    id: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9-]{8,64}$")
    description: Optional[str] = "Job Item"
    ...
```

Add `from pydantic import BaseModel, Field` (Field is not imported there today) and `from uuid import uuid4`.

In the PUT handler, just before `job_items = []` (line ~1152), add the id resolution rule, then use it in the `JobItem(...)` construction:

```python
        # Id preservation (see models.estimate.JobItem.id). Three cases:
        #   1. the client sent an id           -> keep it
        #   2. NO incoming item has an id      -> legacy client; reuse by position
        #   3. some have ids, this one doesn't -> a new item; fresh id
        stored_ids = [ji.id for ji in existing_estimate.job_items]
        client_is_id_aware = any(item.id for item in payload.job_items)

        def _resolve_job_item_id(index: int, incoming: Optional[str]) -> str:
            if incoming:
                return incoming
            if not client_is_id_aware and index < len(stored_ids):
                return stored_ids[index]
            return uuid4().hex

        job_items = []
        for index, item in enumerate(payload.job_items):
```

and in the construction at line ~1270:

```python
            job_items.append(JobItem(
                id=_resolve_job_item_id(index, item.id),
                description=item.description or "Job Item",
```

In the duplicate handler (line ~919):

```python
    # exclude={"id"}: the copy's work items are new items (D4 — notes do not
    # follow a duplicate), so they must not share ids with the source.
    cloned_job_items = [JobItem(**ji.model_dump(exclude={"id"})) for ji in source.job_items]
```

In `platform/routers/estimate_helpers/job_item_builders.py`, each of the three `JobItem(` constructions gets `id=item.id or uuid4().hex,` as its first keyword **only where the loop variable is a `JobItemCreate`** (`build_full_job_items_from_request` at `:263` and `build_skeleton_job_items` at `:302`). `build_job_items_from_parsed` at `:588` builds from LLM dicts and has no client id: leave it to the default factory. Add `from uuid import uuid4`.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_job_item_ids.py -v
```

Expected: 7 passed.

- [ ] **Step 6: Run the neighbors that exercise job items, then the gates**

```bash
cd platform && ./run_tests.sh tests/test_estimate_api.py -k "job_items or duplicate or update_estimate" -q
./run_mypy.sh routers/estimates.py routers/estimate_helpers models/estimate.py
./run_ruff.sh routers/estimates.py routers/estimate_helpers models/estimate.py
```

Expected: all green, zero mypy/ruff findings.

- [ ] **Step 7: Commit (ask first)**

```bash
cd platform && git add models/estimate.py routers/estimates.py routers/estimate_helpers/job_item_builders.py tests/test_job_item_ids.py
git commit -m "feat: give work items a stable id preserved across PUT

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Backfill script for existing estimates

**Files:**
- Create: `platform/scripts/backfill_job_item_ids.py`
- Test: `platform/tests/test_backfill_job_item_ids.py` (new)

**Interfaces:**
- Consumes: `JobItem.id` from Task 1.
- Produces: `backfill_job_item_ids(apply: bool) -> dict` with keys `estimates_scanned`, `items_assigned`, `items_skipped`; CLI `python scripts/backfill_job_item_ids.py [--apply]`.

- [ ] **Step 1: Write the failing test**

Create `platform/tests/test_backfill_job_item_ids.py`:

```python
"""scripts/backfill_job_item_ids.py — persist an id on every stored work item.

Writes a per-index $set guarded by "this index still has no id", so a
concurrent edit that already assigned one is never overwritten and a second
run is a no-op."""

import re
from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from tests.helpers import run_on_portal

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def _insert_raw_estimate(client: TestClient, company_id: str, job_items: list[dict]) -> str:
    """Insert straight into Mongo so the document lacks `id`s the way a
    pre-feature document does (Beanie would add them on insert)."""

    async def _insert():
        from models.estimate import Estimate

        now = datetime.now(timezone.utc)
        result = await Estimate.get_pymongo_collection().insert_one({
            "estimate_id": "",
            "title": "Backfill test",
            "company": PydanticObjectId(company_id),
            "status": "Draft",
            "created_by": "tests",
            "job_items": job_items,
            "grand_total": 0.0,
            "created_at": now,
            "updated_at": now,
        })
        return str(result.inserted_id)

    return run_on_portal(client, _insert)


def _raw_job_items(client: TestClient, estimate_id: str) -> list[dict]:
    async def _read():
        from models.estimate import Estimate

        doc = await Estimate.get_pymongo_collection().find_one({"_id": PydanticObjectId(estimate_id)})
        return doc["job_items"]

    return run_on_portal(client, _read)


def test_dry_run_reports_but_writes_nothing(client: TestClient, test_company_id: str):
    from scripts.backfill_job_item_ids import backfill_job_item_ids

    estimate_id = _insert_raw_estimate(client, test_company_id, [
        {"description": "A", "sub_total": 0.0},
        {"description": "B", "sub_total": 0.0},
    ])
    summary = run_on_portal(client, backfill_job_item_ids, False)
    assert summary["items_assigned"] >= 2
    assert all("id" not in item for item in _raw_job_items(client, estimate_id))
    client.delete(f"/estimates/{estimate_id}")


def test_apply_assigns_ids_only_where_missing_and_is_idempotent(client: TestClient, test_company_id: str):
    from scripts.backfill_job_item_ids import backfill_job_item_ids

    estimate_id = _insert_raw_estimate(client, test_company_id, [
        {"description": "A", "sub_total": 0.0},
        {"id": "keepme-keepme-keepme", "description": "B", "sub_total": 0.0},
    ])
    first = run_on_portal(client, backfill_job_item_ids, True)
    items = _raw_job_items(client, estimate_id)
    assert _HEX32.match(items[0]["id"])
    assert items[1]["id"] == "keepme-keepme-keepme"
    assert first["items_assigned"] >= 1

    second = run_on_portal(client, backfill_job_item_ids, True)
    assert _raw_job_items(client, estimate_id) == items
    # Nothing left for this estimate; the count can only come from other tests' residue.
    assert second["items_assigned"] <= first["items_assigned"]
    client.delete(f"/estimates/{estimate_id}")
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd platform && ./run_tests.sh tests/test_backfill_job_item_ids.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.backfill_job_item_ids'`.

- [ ] **Step 3: Write the script**

Create `platform/scripts/backfill_job_item_ids.py`:

```python
#!/usr/bin/env python3
"""Persist an `id` on every stored work item (Estimate.job_items[].id).

`JobItem.id` has a default_factory, so a document written before the field
existed gets a *different* id on every load and nothing can safely point at
it. Notes (models/note.py) do exactly that, which makes this backfill a hard
prerequisite for enabling the notes feature — run it on every environment
before the portal's notes UI ships.

Each assignment is a targeted `$set` on `job_items.<index>.id`, filtered on
that index still lacking an id, so a concurrent edit that already assigned
one is never overwritten and re-running is a no-op.

Usage:
    python scripts/backfill_job_item_ids.py          # dry run (default)
    python scripts/backfill_job_item_ids.py --apply  # persist
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import init_db  # noqa: E402
from models.estimate import Estimate  # noqa: E402

_BATCH = 500


async def backfill_job_item_ids(apply: bool) -> dict:
    """Assign ids to work items missing one. Returns a summary dict."""
    collection = Estimate.get_pymongo_collection()
    cursor = collection.find(
        {"job_items": {"$elemMatch": {"id": {"$exists": False}}}},
        {"job_items.id": 1},
    ).batch_size(_BATCH)

    scanned = assigned = skipped = 0
    async for doc in cursor:
        scanned += 1
        for index, item in enumerate(doc.get("job_items") or []):
            if item.get("id"):
                continue
            if not apply:
                assigned += 1
                continue
            result = await collection.update_one(
                {"_id": doc["_id"], f"job_items.{index}.id": {"$exists": False}},
                {"$set": {f"job_items.{index}.id": uuid4().hex}},
            )
            if result.modified_count == 1:
                assigned += 1
            else:
                skipped += 1  # someone assigned it between the find and the set
    return {
        "estimates_scanned": scanned,
        "items_assigned": assigned,
        "items_skipped": skipped,
    }


async def _main(apply: bool) -> int:
    await init_db()
    summary = await backfill_job_item_ids(apply)
    mode = "APPLIED" if apply else "DRY RUN"
    print(f"[{mode}] estimates scanned: {summary['estimates_scanned']}")
    print(f"[{mode}] work item ids {'assigned' if apply else 'to assign'}: {summary['items_assigned']}")
    if summary["items_skipped"]:
        print(f"[{mode}] work items skipped (id assigned concurrently): {summary['items_skipped']}")
    if not apply:
        print("Nothing written. Re-run with --apply to persist.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="persist the ids (default is a dry run)")
    args = parser.parse_args()
    sys.exit(asyncio.run(_main(args.apply)))
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd platform && ./run_tests.sh tests/test_backfill_job_item_ids.py -v
./run_mypy.sh scripts/backfill_job_item_ids.py && ./run_ruff.sh scripts/backfill_job_item_ids.py
```

Expected: 2 passed, gates clean (`scripts/**` has the E402 carve-out in `ruff.toml`).

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add scripts/backfill_job_item_ids.py tests/test_backfill_job_item_ids.py
git commit -m "feat: backfill script for work item ids

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

After this lands on Dev: run `python scripts/backfill_job_item_ids.py` (dry run) then `--apply` against Dev. Prod is run at the Phase 2 deploy, before Phase 4 ships.

---

### Task 3: Portal carries `id` on `WorkItemV2` and round-trips it

**Files:**
- Modify: `portal/src/types/api.ts:267` (`EstimateJobItem`)
- Modify: `portal/src/lib/workItemV2.ts` (`WorkItemV2`, `emptyWorkItem`, `WorkItemV2JobItemPayload`, `jobItemToWorkItemV2`, `workItemV2ToJobItemPayload`, `jobItemsPayloadDiffers`)
- Modify: `portal/src/components/estimates/WorkItemInlineContent.tsx:57-125` (state + the `onChange` effect)
- Test: `portal/tests/workItemV2.test.ts` (append), `portal/tests/WorkItemInlineContent.test.tsx` (append)

**Interfaces:**
- Consumes: `EstimateJobItem.id?: string` from the server (Task 1).
- Produces: `WorkItemV2.id: string` (always present client-side), sent as `id` in every job item payload. Task 17 reads `draft.id` to open the notes panel.

- [ ] **Step 1: Write the failing tests**

Append to `portal/tests/workItemV2.test.ts`:

```ts
describe("work item ids", () => {
  test("emptyWorkItem generates an id", () => {
    const a = emptyWorkItem();
    const b = emptyWorkItem();
    expect(a.id).toMatch(/^[0-9a-f-]{32,36}$/);
    expect(a.id).not.toBe(b.id);
  });

  test("jobItemToWorkItemV2 keeps the server id and invents one when absent", () => {
    expect(jobItemToWorkItemV2({ id: "abc12345", description: "x" }).id).toBe("abc12345");
    expect(jobItemToWorkItemV2({ description: "x" }).id).toMatch(/^[0-9a-f-]{32,36}$/);
  });

  test("workItemV2ToJobItemPayload sends the id", () => {
    const wi = { ...emptyWorkItem(), id: "keep-me-keep-me" };
    expect(workItemV2ToJobItemPayload(wi).id).toBe("keep-me-keep-me");
  });

  test("jobItemsPayloadDiffers ignores ids so a pre-backfill server item does not read as changed", () => {
    const server: EstimateJobItem = { description: "Same", division: "Unassigned" };
    const payload = workItemV2ToJobItemPayload(jobItemToWorkItemV2(server), server);
    // A second projection of the same server item gets a different invented id.
    expect(jobItemsPayloadDiffers([payload], [server])).toBe(false);
  });
});
```

Append to `portal/tests/WorkItemInlineContent.test.tsx`:

```tsx
test("emits the initial work item id on every change", async () => {
  const onChange = vi.fn();
  render(
    <WorkItemInlineContent
      {...baseProps}
      initialData={{ ...workItem(), id: "wi-fixed-id" }}
      onChange={onChange}
    />,
  );
  await act(async () => {});
  // Not .at(-1): this project's tsconfig targets ES2020, which predates
  // Array.prototype.at. Use the indexing idiom the file already uses.
  const last = onChange.mock.calls[onChange.mock.calls.length - 1][0] as WorkItemV2;
  expect(last.id).toBe("wi-fixed-id");
});
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd portal && npm test -- tests/workItemV2.test.ts tests/WorkItemInlineContent.test.tsx
```

Expected: FAIL. `expect(a.id)` receives `undefined`; the typecheck also fails on `id` not existing on `WorkItemV2`.

- [ ] **Step 3: Add the field everywhere**

`portal/src/types/api.ts`, in `EstimateJobItem`:

```ts
export interface EstimateJobItem {
  /** Stable server id (models/estimate.py JobItem.id). Absent on documents
   *  written before 2026-09 until the backfill has run. */
  id?: string;
  description?: string;
```

`portal/src/lib/workItemV2.ts`:

```ts
export interface WorkItemV2 {
  /**
   * Stable identity, echoed to the server on every save so notes keyed on it
   * survive the whole-array PUT. Generated client-side for a new item; kept
   * from the server for an existing one.
   */
  id: string;
  division: string;
  ...
}

export function emptyWorkItem(defaults?: {...}): WorkItemV2 {
  return {
    id: newRowId(),
    division: "Unassigned",
    ...
  };
}

export interface WorkItemV2JobItemPayload {
  id: string;
  description: string;
  ...
}

export function jobItemToWorkItemV2(item: EstimateJobItem): WorkItemV2 {
  return {
    id: item.id || newRowId(),
    division: item.division || "Unassigned",
    ...
  };
}

export function workItemV2ToJobItemPayload(wi, rawItem?): WorkItemV2JobItemPayload {
  return {
    id: wi.id,
    description: wi.description || wi.division,
    ...
  };
}
```

And in `jobItemsPayloadDiffers`, strip ids before comparing (a server item with no id gets a random one on every projection, which would otherwise make every save look dirty and re-send `job_items`, defeating the sparse-write guard):

```ts
export function jobItemsPayloadDiffers(
  payloadItems: WorkItemV2JobItemPayload[],
  rawItems: EstimateJobItem[],
): boolean {
  if (payloadItems.length !== rawItems.length) return true;
  const withoutId = ({ id: _id, ...rest }: WorkItemV2JobItemPayload) => rest;
  const serverProjection = rawItems.map((ji) =>
    withoutId(workItemV2ToJobItemPayload(jobItemToWorkItemV2(ji), ji)),
  );
  return !isDeepEqual(payloadItems.map(withoutId), serverProjection);
}
```

`portal/src/components/estimates/WorkItemInlineContent.tsx`: add one state line beside the others and include it in the emitted object.

```tsx
  // Fixed for the life of this editor: the id never changes while editing.
  const [workItemId] = useState(() => initialData?.id ?? newRowId());
  ...
  useEffect(() => {
    onChange({
      id: workItemId,
      division: resolvedDivision,
      ...
    });
  }, [onChange, workItemId, resolvedDivision, ...]);
```

Fix any other `WorkItemV2` literal the typecheck flags (search `tests/` and `src/` for objects spread from `emptyWorkItem()` — those are fine; hand-built literals need `id`).

- [ ] **Step 4: Run the tests and the typecheck**

```bash
cd portal && npm test -- tests/workItemV2.test.ts tests/WorkItemInlineContent.test.tsx tests/WorkItemDialog.test.tsx tests/NewEstimateWithActivityPage.autosave.test.tsx
npm run typecheck
```

Expected: all pass; typecheck clean.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/types/api.ts src/lib/workItemV2.ts src/components/estimates/WorkItemInlineContent.tsx tests/workItemV2.test.ts tests/WorkItemInlineContent.test.tsx
git commit -m "feat: carry the work item id through the editor and payload

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

# Phase 2 — Notes backend

### Task 4: Extract `services/media_blobs.py`; `task_photos.py` becomes a wrapper

**Files:**
- Create: `platform/services/media_blobs.py`
- Modify: `platform/services/task_photos.py` (whole file becomes wrappers)
- Test: `platform/tests/test_media_blobs.py` (new); `platform/tests/test_task_photos_api.py` (unchanged, must stay green)

**Interfaces:**
- Consumes: nothing.
- Produces (all in `services/media_blobs.py`):
  - `class MediaValidationError(ValueError)`
  - constants `MAX_IMAGE_SIZE_BYTES`, `MAX_VIDEO_SIZE_BYTES`, `MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024`, `ALLOWED_IMAGE_CONTENT_TYPES`, `ALLOWED_VIDEO_CONTENT_TYPES`, `PDF_CONTENT_TYPE = "application/pdf"`, `THUMBNAIL_MAX_PX`, `THUMBNAIL_JPEG_QUALITY`, `VIDEO_STREAM_CHUNK_BYTES`
  - `normalize_content_type(raw: str) -> str`, `is_video_content_type(raw) -> bool`, `is_pdf_content_type(raw) -> bool`, `max_media_size_bytes(raw) -> int`
  - `validate_image_upload(content, content_type) -> str`, `validate_pdf_upload(content, content_type) -> str`, `build_thumbnail(content) -> bytes`
  - `get_bucket(bucket_name: str) -> AsyncIOMotorGridFSBucket`
  - `store_image_blobs(bucket_name, content, filename, content_type) -> tuple[PydanticObjectId, PydanticObjectId]`
  - `store_blob(bucket_name, content, filename, content_type) -> PydanticObjectId`
  - `store_video_stream(bucket_name, file: UploadFile, filename, content_type) -> tuple[PydanticObjectId, int]`
  - `read_blob(bucket_name, file_id) -> bytes | None`, `delete_blobs(bucket_name, *file_ids) -> None`
- `services/task_photos.py` keeps **every** name it exports today with identical signatures (`ImageValidationError`, `get_photo_bucket`, `store_photo_blobs`, `store_video_stream`, `read_photo_blob`, `delete_photo_blobs`, `validate_image_upload`, `normalize_image_content_type`, `is_video_content_type`, `max_media_size_bytes`, `build_thumbnail`, and the constants) bound to bucket `"task_photos"`.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_media_blobs.py`:

```python
"""services/media_blobs.py — bucket-agnostic validation and GridFS storage
shared by task photos and note attachments."""

import io

import pytest
from PIL import Image


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), (10, 20, 30)).save(buf, format="JPEG")
    return buf.getvalue()


def test_normalize_content_type_strips_parameters():
    from services.media_blobs import normalize_content_type

    assert normalize_content_type("Image/JPEG; charset=binary") == "image/jpeg"
    assert normalize_content_type("") == ""


def test_pdf_detection_and_caps():
    from services.media_blobs import (
        MAX_PDF_SIZE_BYTES,
        MAX_VIDEO_SIZE_BYTES,
        is_pdf_content_type,
        max_media_size_bytes,
    )

    assert is_pdf_content_type("application/pdf")
    assert not is_pdf_content_type("image/png")
    assert max_media_size_bytes("application/pdf") == MAX_PDF_SIZE_BYTES
    assert max_media_size_bytes("video/mp4") == MAX_VIDEO_SIZE_BYTES


def test_validate_pdf_upload_checks_magic_bytes():
    from services.media_blobs import MediaValidationError, validate_pdf_upload

    assert validate_pdf_upload(b"%PDF-1.7\n%...", "application/pdf") == "application/pdf"
    with pytest.raises(MediaValidationError):
        validate_pdf_upload(b"MZ\x90\x00 not a pdf", "application/pdf")
    with pytest.raises(MediaValidationError):
        validate_pdf_upload(b"%PDF-1.7", "image/png")
    with pytest.raises(MediaValidationError):
        validate_pdf_upload(b"", "application/pdf")


def test_validate_image_upload_still_works_from_the_new_module():
    from services.media_blobs import MediaValidationError, validate_image_upload

    assert validate_image_upload(_jpeg(), "image/jpeg") == "image/jpeg"
    with pytest.raises(MediaValidationError):
        validate_image_upload(b"\x89PNG not really", "image/jpeg")


def test_task_photos_module_keeps_its_public_names():
    """routers/tasks.py and its tests import these by name; the extraction
    must not rename anything Tasks uses."""
    import services.task_photos as task_photos
    from services.media_blobs import MediaValidationError

    for name in (
        "ImageValidationError", "get_photo_bucket", "store_photo_blobs",
        "store_video_stream", "read_photo_blob", "delete_photo_blobs",
        "validate_image_upload", "normalize_image_content_type",
        "is_video_content_type", "max_media_size_bytes", "build_thumbnail",
        "MAX_IMAGE_SIZE_BYTES", "MAX_VIDEO_SIZE_BYTES",
    ):
        assert hasattr(task_photos, name), name
    assert task_photos.ImageValidationError is MediaValidationError
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_media_blobs.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.media_blobs'`.

**Controller ruling R8 (pre-flight) — the caps must stay injectable, or an existing task test breaks.**

`tests/test_task_photos_api.py::test_upload_video_rejects_oversize` does
`monkeypatch.setattr(task_photos, "MAX_VIDEO_SIZE_BYTES", 1024)` so it does not
have to allocate 50MB. Rebinding that name in the `task_photos` namespace has no
effect on a function living in `media_blobs` that reads `media_blobs`'s own
global, so a naive re-export wrapper makes the oversize upload succeed and the
test fail. Since "the task suite stays green untouched" is the whole safety
property of this refactor, the cap becomes a parameter:

- `media_blobs.store_video_stream(bucket_name, file, filename, content_type, *, max_size_bytes)` — required keyword.
- `media_blobs.validate_image_upload(content, content_type, *, max_size_bytes=MAX_IMAGE_SIZE_BYTES)`.
- `media_blobs.validate_pdf_upload(content, content_type, *, max_size_bytes=MAX_PDF_SIZE_BYTES)`.
- Each wrapper in `task_photos.py` reads its own module-level constant **at call
  time** and passes it down, e.g.
  `return await media_blobs.store_video_stream(TASK_PHOTO_BUCKET, file, filename, content_type, max_size_bytes=MAX_VIDEO_SIZE_BYTES)`.
  Reading it inside the function body is what keeps the monkeypatch effective.
- `task_photos.max_media_size_bytes` is likewise a real wrapper function reading
  the task module's own constants, not a re-export of the `media_blobs` one.
- `note_attachments.py` (Task 8) passes the `media_blobs` defaults and needs no
  constants of its own.

The size message inside each validator must be derived from the cap actually in
force, not from the module constant, so a patched cap reports the patched number.

- [ ] **Step 3: Create `media_blobs.py` by moving the code**

Create `platform/services/media_blobs.py`. Move the body of `task_photos.py` (everything from the constants through `delete_photo_blobs`) into it with these changes and nothing else:

- Rename `ImageValidationError` → `MediaValidationError`; `normalize_image_content_type` → `normalize_content_type`.
- Every function that touched `get_photo_bucket()` takes `bucket_name: str` as its **first** parameter and calls `get_bucket(bucket_name)`. Renames: `get_photo_bucket` → `get_bucket(bucket_name)`, `store_photo_blobs` → `store_image_blobs`, `read_photo_blob` → `read_blob`, `delete_photo_blobs` → `delete_blobs`. `store_video_stream` keeps its name.
- `get_bucket` resolves the database without importing `Task` (the module must not depend on a model): use `from database import get_database` if it exists; otherwise add this helper at the top of `media_blobs.py`:

```python
def _database():
    # Any registered Document reaches the same Motor database; Estimate is
    # always registered. Imported lazily so this module has no model import
    # at load time.
    from models import Estimate
    return Estimate.get_pymongo_collection().database
```

- Add PDF support:

```python
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
PDF_CONTENT_TYPE = "application/pdf"
_PDF_MAGIC = b"%PDF-"


def is_pdf_content_type(raw: str) -> bool:
    return normalize_content_type(raw) == PDF_CONTENT_TYPE


def max_media_size_bytes(raw_content_type: str) -> int:
    """The upload cap for a declared content type."""
    if is_video_content_type(raw_content_type):
        return MAX_VIDEO_SIZE_BYTES
    if is_pdf_content_type(raw_content_type):
        return MAX_PDF_SIZE_BYTES
    return MAX_IMAGE_SIZE_BYTES


def validate_pdf_upload(content: bytes, content_type: str) -> str:
    """Validate PDF bytes; returns the normalized content type or raises."""
    normalized_type = normalize_content_type(content_type)
    if normalized_type != PDF_CONTENT_TYPE:
        raise MediaValidationError("This file is not a PDF.")
    if not content:
        raise MediaValidationError("The PDF is empty.")
    if len(content) > MAX_PDF_SIZE_BYTES:
        raise MediaValidationError(f"PDFs are limited to {MAX_PDF_SIZE_BYTES // (1024 * 1024)}MB.")
    if not content.startswith(_PDF_MAGIC):
        raise MediaValidationError("The file bytes don't match a PDF.")
    return normalized_type


async def store_blob(bucket_name: str, content: bytes, filename: str, content_type: str) -> PydanticObjectId:
    """Store one blob with no thumbnail (PDFs)."""
    file_id = await get_bucket(bucket_name).upload_from_stream(
        filename, content, metadata={"contentType": content_type}
    )
    return PydanticObjectId(file_id)
```

- [ ] **Step 4: Rewrite `task_photos.py` as a wrapper**

Replace the whole of `platform/services/task_photos.py` with:

```python
"""Task media storage — the "task_photos" GridFS bucket.

The validation, thumbnail and streaming code lives in services/media_blobs.py
(bucket-agnostic; note attachments use the same code against their own
bucket). This module binds it to the task bucket under the names
routers/tasks.py and the task tests have always used.
"""
from __future__ import annotations

from beanie import PydanticObjectId
from fastapi import UploadFile

from services.media_blobs import (  # noqa: F401  # re-exported for routers/tasks.py and tests
    ALLOWED_IMAGE_CONTENT_TYPES,
    ALLOWED_VIDEO_CONTENT_TYPES,
    MAX_IMAGE_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
    THUMBNAIL_JPEG_QUALITY,
    THUMBNAIL_MAX_PX,
    VIDEO_STREAM_CHUNK_BYTES,
    MediaValidationError,
    build_thumbnail,
    is_video_content_type,
    max_media_size_bytes,
    validate_image_upload,
)
from services import media_blobs

TASK_PHOTO_BUCKET = "task_photos"

# Historic names, kept so nothing under routers/tasks.py or tests/ changes.
ImageValidationError = MediaValidationError
normalize_image_content_type = media_blobs.normalize_content_type


def get_photo_bucket():
    return media_blobs.get_bucket(TASK_PHOTO_BUCKET)


async def store_photo_blobs(content: bytes, filename: str, content_type: str) -> tuple[PydanticObjectId, PydanticObjectId]:
    return await media_blobs.store_image_blobs(TASK_PHOTO_BUCKET, content, filename, content_type)


async def store_video_stream(file: UploadFile, filename: str, content_type: str) -> tuple[PydanticObjectId, int]:
    return await media_blobs.store_video_stream(TASK_PHOTO_BUCKET, file, filename, content_type)


async def read_photo_blob(file_id: PydanticObjectId) -> bytes | None:
    return await media_blobs.read_blob(TASK_PHOTO_BUCKET, file_id)


async def delete_photo_blobs(*file_ids: PydanticObjectId | None) -> None:
    await media_blobs.delete_blobs(TASK_PHOTO_BUCKET, *file_ids)
```

Before running anything: `grep -rn "task_photos\." tests/ routers/` and confirm every attribute referenced exists in the wrapper (monkeypatched names included).

- [ ] **Step 5: Run the new tests and the untouched task tests**

```bash
cd platform && ./run_tests.sh tests/test_media_blobs.py tests/test_task_photos_api.py -v
./run_mypy.sh services/media_blobs.py services/task_photos.py routers/tasks.py
./run_ruff.sh services/media_blobs.py services/task_photos.py routers/tasks.py
```

Expected: all pass, zero findings. If a task test fails, the wrapper is missing a name — fix the wrapper, never the test.

- [ ] **Step 6: Commit (ask first)**

```bash
cd platform && git add services/media_blobs.py services/task_photos.py tests/test_media_blobs.py
git commit -m "refactor: extract bucket-agnostic media blob storage from task photos

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: The `Note` model, registration and test-cleanup coverage

**Files:**
- Create: `platform/models/note.py`
- Modify: `platform/models/__init__.py` (export + `model_rebuild()`), `platform/database.py` (`document_models`), `platform/tests/conftest.py:124` (`COMPANY_SCOPED_COLLECTIONS`)
- Test: `platform/tests/test_note_model.py` (new); `platform/tests/test_test_data_cleanup_coverage.py` (existing, must pass)

**Interfaces:**
- Produces: `Note`, `NoteParentType`, `NoteAttachment`, `NoteAttachmentKind` exactly as below. Every later platform task imports these.

- [ ] **Step 1: Write the failing test**

Create `platform/tests/test_note_model.py`:

```python
"""models/note.py — one document shape for work-item, property and contact notes."""

from datetime import timezone

from beanie import PydanticObjectId


def test_note_defaults_and_shape():
    from models.note import Note, NoteParentType

    note = Note(
        company=PydanticObjectId(),
        parent_type=NoteParentType.PROPERTY,
        parent_id=PydanticObjectId(),
        body="Gate code **4411**",
        created_by_email="ana@example.com",
        created_by_name="Ana Reyes",
    )
    assert note.work_item_id is None
    assert note.attachments == []
    assert note.created_at.tzinfo is timezone.utc
    assert note.updated_at.tzinfo is timezone.utc
    assert Note.Settings.name == "notes"


def test_note_is_registered_everywhere():
    import models
    from database import init_db  # noqa: F401  # import guards against a missing model import
    from models import Note
    from tests.conftest import COMPANY_SCOPED_COLLECTIONS

    assert models.Note is Note
    assert ("notes", "company") in COMPANY_SCOPED_COLLECTIONS
    # Beanie only binds a collection to a Document that init_db() actually
    # registered, so this fails loudly if `Note` is ever dropped from
    # `document_models` while its import survives — the silent-at-runtime
    # failure mode that a bare import check cannot see.
    assert Note.get_pymongo_collection().name == "notes"


def test_attachment_kinds_and_parent_types():
    from models.note import NoteAttachmentKind, NoteParentType

    assert {k.value for k in NoteAttachmentKind} == {"image", "video", "pdf"}
    assert {p.value for p in NoteParentType} == {"work_item", "estimate", "property", "contact"}
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_note_model.py tests/test_test_data_cleanup_coverage.py -v
```

Expected: `test_note_model.py` fails with `ModuleNotFoundError`; the coverage test passes for now (it will fail after the model exists until conftest is updated, which is the point of the next steps).

- [ ] **Step 3: Create the model**

Create `platform/models/note.py`:

```python
"""Notes: authored, timestamped commentary on a work item, property or contact.

One collection, three parents. A separate document (not an embedded list)
because the creator-only edit rule needs the server to know which note
changed, attachments need a stable id to hang off, and the whole-array
PUT /estimates write must not carry notes with it.

Authorization lives in services/notes.py: editing is creator-only, deleting
is creator-or-Owner (design decision D2). `created_by_email` is the key;
`created_by_name` is a display snapshot taken at write time.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

MAX_NOTE_BODY_CHARS = 20_000
MAX_ATTACHMENTS_PER_NOTE = 10


class NoteParentType(str, Enum):
    WORK_ITEM = "work_item"   # parent_id = Estimate.id, work_item_id = JobItem.id
    ESTIMATE = "estimate"     # parent_id = Estimate.id (the estimate as a whole)
    PROPERTY = "property"     # parent_id = Property.id
    CONTACT = "contact"       # parent_id = Contact.id


class NoteAttachmentKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"


class NoteAttachment(BaseModel):
    file_id: PydanticObjectId                       # GridFS _id in bucket "note_attachments"
    thumb_file_id: Optional[PydanticObjectId] = None  # images only
    kind: NoteAttachmentKind
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Note(Document):
    company: PydanticObjectId
    parent_type: NoteParentType
    parent_id: PydanticObjectId
    # Set only when parent_type == WORK_ITEM. A string, not an ObjectId:
    # JobItem.id is a uuid.
    work_item_id: Optional[str] = None
    body: str = Field(max_length=MAX_NOTE_BODY_CHARS)   # markdown, stored raw
    attachments: List[NoteAttachment] = []
    created_by_email: str      # lowercase; the authorization key
    created_by_name: str       # display snapshot ("Ana Reyes")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Stamped by services/notes.py on every $set — the before_event hook does
    # not fire for .set(), same caveat as every other document here.
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "notes"
        indexes = [
            IndexModel(
                [("company", ASCENDING), ("parent_type", ASCENDING),
                 ("parent_id", ASCENDING), ("created_at", DESCENDING)],
                name="notes_by_parent_newest",
            ),
            # Equality on all four, then the sort key — the shape the work
            # item feed actually queries ("this work item's notes, newest
            # first"). The equality prefix alone still serves the counts
            # aggregation, which groups by work_item_id without sorting.
            IndexModel(
                [("company", ASCENDING), ("parent_type", ASCENDING),
                 ("parent_id", ASCENDING), ("work_item_id", ASCENDING),
                 ("created_at", DESCENDING)],
                name="notes_by_work_item_newest",
            ),
        ]
```

- [ ] **Step 4: Register it**

`platform/models/__init__.py`: add `from .note import Note, NoteAttachment, NoteAttachmentKind, NoteParentType` next to the task import, add the four names to `__all__` if the file declares one, and `Note.model_rebuild()` next to `Task.model_rebuild()`.

`platform/database.py`: add `Note` to the `from models import (...)` list and to `document_models=[...]` after `Task`.

`platform/tests/conftest.py`: add `("notes", "company"),` to `COMPANY_SCOPED_COLLECTIONS` after `("tasks", "company"),`.

- [ ] **Step 5: Run the tests**

```bash
cd platform && ./run_tests.sh tests/test_note_model.py tests/test_test_data_cleanup_coverage.py tests/test_models_layering.py -v
./run_mypy.sh models/note.py models/__init__.py database.py && ./run_ruff.sh models/note.py models/__init__.py database.py tests/conftest.py
```

Expected: all pass, gates clean.

- [ ] **Step 6: Commit (ask first)**

```bash
cd platform && git add models/note.py models/__init__.py database.py tests/conftest.py tests/test_note_model.py
git commit -m "feat: add the Note document

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: `services/notes.py` — authorization, parent validation, CRUD helpers

**Files:**
- Create: `platform/services/notes.py`
- Modify: `platform/services/sparse_update.py:41-49` (nothing to add: `created_by_email` is already in `SERVER_OWNED_FIELDS`; confirm and move on)
- Test: `platform/tests/test_notes_service.py` (new)

**Interfaces:**
- Consumes: `Note`, `NoteParentType` (Task 5); `User`, `UserRole`; `Estimate`, `Property`, `Contact`.
- Produces:
  - `author_display_name(user: User) -> str`
  - `is_note_author(note: Note, user: User) -> bool`
  - `assert_can_edit_note(note, user) -> None` (403), `assert_can_delete_note(note, user) -> None` (403)
  - `async assert_parent_exists(company, parent_type, parent_id, work_item_id) -> None` (404 on a missing/cross-tenant parent, 422 on a missing/unknown `work_item_id`)
  - `async create_note(*, user, parent_type, parent_id, work_item_id, body) -> Note`
  - `async list_notes(company, parent_type, parent_id, work_item_id=None) -> List[Note]` (newest first, cap `MAX_NOTES_LISTED = 500`)
  - `async count_notes_by_work_item(company, estimate_id) -> Dict[str, int]`
  - `async update_note_body(note, body) -> Note`
  - `async delete_note(note) -> None` (document, then blobs via Task 8's `delete_attachment_blobs`; until Task 8 exists it deletes the document only — Task 8 wires the blobs)
  - `async delete_notes_for_parent(parent_type, parent_id) -> int`
  - `async delete_notes_for_work_items(estimate_id, work_item_ids: Iterable[str]) -> int`

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_notes_service.py`:

```python
"""services/notes.py — the rules the router enforces, tested without HTTP."""

import pytest
from beanie import PydanticObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient

from tests.helpers import run_on_portal


def _user(email: str, role: str, first="Ana", last="Reyes"):
    from models import User, UserRole

    return User(email=email, first_name=first, last_name=last, role=UserRole(role),
                company=PydanticObjectId())


def _note(author_email: str):
    from models.note import Note, NoteParentType

    return Note(company=PydanticObjectId(), parent_type=NoteParentType.PROPERTY,
                parent_id=PydanticObjectId(), body="x",
                created_by_email=author_email, created_by_name="Author")


def test_author_display_name_falls_back_to_email():
    from services.notes import author_display_name

    assert author_display_name(_user("a@x.com", "Member")) == "Ana Reyes"
    assert author_display_name(_user("a@x.com", "Member", first="", last="")) == "a@x.com"


def test_edit_is_creator_only_even_for_owner():
    from services.notes import assert_can_edit_note

    note = _note("author@x.com")
    assert_can_edit_note(note, _user("AUTHOR@x.com", "Member"))  # case-insensitive
    with pytest.raises(HTTPException) as exc:
        assert_can_edit_note(note, _user("owner@x.com", "Owner"))
    assert exc.value.status_code == 403


def test_delete_is_creator_or_owner_not_admin():
    from services.notes import assert_can_delete_note

    note = _note("author@x.com")
    assert_can_delete_note(note, _user("author@x.com", "Member"))
    assert_can_delete_note(note, _user("owner@x.com", "Owner"))
    with pytest.raises(HTTPException) as exc:
        assert_can_delete_note(note, _user("admin@x.com", "Admin"))
    assert exc.value.status_code == 403


def test_parent_validation_rejects_missing_and_cross_tenant(client: TestClient, test_company_id: str):
    from models.note import NoteParentType
    from services.notes import assert_parent_exists

    async def _check():
        from models import Property

        prop = Property(street="1 Main", city="Kelowna", prov_state="BC",
                        company=PydanticObjectId(test_company_id))
        await prop.insert()
        try:
            await assert_parent_exists(PydanticObjectId(test_company_id), NoteParentType.PROPERTY, prop.id, None)
            with pytest.raises(HTTPException) as missing:
                await assert_parent_exists(PydanticObjectId(test_company_id), NoteParentType.PROPERTY, PydanticObjectId(), None)
            assert missing.value.status_code == 404
            with pytest.raises(HTTPException) as other_tenant:
                await assert_parent_exists(PydanticObjectId(), NoteParentType.PROPERTY, prop.id, None)
            assert other_tenant.value.status_code == 404
        finally:
            await prop.delete()

    run_on_portal(client, _check)


def test_estimate_parent_is_the_estimate_itself(client: TestClient, test_company_id: str):
    from models.note import NoteParentType
    from services.notes import assert_parent_exists

    async def _check():
        from models.estimate import Estimate, EstimateStatus
        from services.estimate_readable_id import insert_estimate_with_readable_id

        estimate = Estimate(title="t", company=PydanticObjectId(test_company_id), status=EstimateStatus.DRAFT, created_by="tests")
        estimate = await insert_estimate_with_readable_id(estimate)
        try:
            await assert_parent_exists(estimate.company, NoteParentType.ESTIMATE, estimate.id, None)
            with pytest.raises(HTTPException) as with_item:
                await assert_parent_exists(estimate.company, NoteParentType.ESTIMATE, estimate.id, "abcdefgh")
            assert with_item.value.status_code == 422
            with pytest.raises(HTTPException) as other:
                await assert_parent_exists(PydanticObjectId(), NoteParentType.ESTIMATE, estimate.id, None)
            assert other.value.status_code == 404
        finally:
            await estimate.delete()

    run_on_portal(client, _check)


def test_work_item_parent_requires_a_persisted_work_item_id(client: TestClient, test_company_id: str):
    """A transient id (document never backfilled) must not be accepted —
    the note would dangle after the next save."""
    from models.note import NoteParentType
    from services.notes import assert_parent_exists

    async def _check():
        from models.estimate import Estimate, EstimateStatus, JobItem
        from services.estimate_readable_id import insert_estimate_with_readable_id

        estimate = Estimate(title="t", company=PydanticObjectId(test_company_id), status=EstimateStatus.DRAFT, created_by="tests",
                            job_items=[JobItem(description="A")])
        estimate = await insert_estimate_with_readable_id(estimate)
        real_id = estimate.job_items[0].id
        try:
            await assert_parent_exists(estimate.company, NoteParentType.WORK_ITEM, estimate.id, real_id)
            with pytest.raises(HTTPException) as unknown:
                await assert_parent_exists(estimate.company, NoteParentType.WORK_ITEM, estimate.id, "nope-nope-nope")
            assert unknown.value.status_code == 422
            with pytest.raises(HTTPException) as absent:
                await assert_parent_exists(estimate.company, NoteParentType.WORK_ITEM, estimate.id, None)
            assert absent.value.status_code == 422
        finally:
            await estimate.delete()

    run_on_portal(client, _check)


def test_list_is_newest_first_and_counts_group_by_work_item(client: TestClient, test_company_id: str):
    from models.note import NoteParentType
    from services.notes import count_notes_by_work_item, create_note, delete_notes_for_parent, list_notes

    async def _run():
        from models.estimate import Estimate, EstimateStatus, JobItem
        from services.estimate_readable_id import insert_estimate_with_readable_id

        company = PydanticObjectId(test_company_id)
        estimate = Estimate(title="t", company=company, status=EstimateStatus.DRAFT, created_by="tests",
                            job_items=[JobItem(description="A"), JobItem(description="B")])
        estimate = await insert_estimate_with_readable_id(estimate)
        a, b = (ji.id for ji in estimate.job_items)
        user = _user("author@x.com", "Member")
        user.company = company
        try:
            first = await create_note(user=user, parent_type=NoteParentType.WORK_ITEM,
                                      parent_id=estimate.id, work_item_id=a, body="first")
            second = await create_note(user=user, parent_type=NoteParentType.WORK_ITEM,
                                       parent_id=estimate.id, work_item_id=a, body="second")
            await create_note(user=user, parent_type=NoteParentType.WORK_ITEM,
                              parent_id=estimate.id, work_item_id=b, body="other item")

            listed = await list_notes(company, NoteParentType.WORK_ITEM, estimate.id, a)
            assert [n.id for n in listed] == [second.id, first.id]
            assert first.created_by_name == "Ana Reyes"
            assert first.created_by_email == "author@x.com"

            counts = await count_notes_by_work_item(company, estimate.id)
            assert counts == {a: 2, b: 1}

            removed = await delete_notes_for_parent(NoteParentType.WORK_ITEM, estimate.id)
            assert removed == 3
            assert await list_notes(company, NoteParentType.WORK_ITEM, estimate.id) == []
        finally:
            await delete_notes_for_parent(NoteParentType.WORK_ITEM, estimate.id)
            await estimate.delete()

    run_on_portal(client, _run)
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_notes_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.notes'`.

- [ ] **Step 3: Write the service**

Create `platform/services/notes.py`:

```python
"""Notes: authorization rules, parent validation and the CRUD the router calls.

Rules (design decisions D2/D3):
  * anyone in the company can read and create,
  * editing a note is creator-only — an Owner cannot rewrite someone's words,
  * deleting is creator-or-Owner (Admins get no override),
  * the parent's status never matters; an Archived estimate's work items
    still take notes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import HTTPException

from models import Contact, Estimate, Property, User, UserRole
from models.note import Note, NoteParentType

MAX_NOTES_LISTED = 500


def _norm_email(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def author_display_name(user: User) -> str:
    full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return full or user.email


def is_note_author(note: Note, user: User) -> bool:
    return _norm_email(note.created_by_email) == _norm_email(user.email)


def assert_can_edit_note(note: Note, user: User) -> None:
    if not is_note_author(note, user):
        raise HTTPException(status_code=403, detail="Only the person who wrote this note can edit it")


def assert_can_delete_note(note: Note, user: User) -> None:
    if not (is_note_author(note, user) or user.role == UserRole.OWNER):
        raise HTTPException(status_code=403, detail="Only the note's author or a company owner can delete it")


async def assert_parent_exists(
    company: PydanticObjectId,
    parent_type: NoteParentType,
    parent_id: PydanticObjectId,
    work_item_id: Optional[str],
) -> None:
    """404 when the parent is missing or belongs to another company; 422 when
    a work-item note names no work item or one the estimate does not have."""
    if parent_type == NoteParentType.WORK_ITEM:
        if not work_item_id:
            raise HTTPException(status_code=422, detail="work_item_id is required for a work item note")
        # Raw query on purpose: a document that predates JobItem.id would get
        # a transient id through Beanie, and a note keyed on it would dangle.
        # Only an id that is actually stored counts.
        stored = await Estimate.get_pymongo_collection().find_one(
            {"_id": parent_id, "company": company, "job_items.id": work_item_id},
            {"_id": 1},
        )
        if stored is None:
            exists = await Estimate.find_one(Estimate.id == parent_id, Estimate.company == company)
            if exists is None:
                raise HTTPException(status_code=404, detail="Estimate not found")
            raise HTTPException(status_code=422, detail="That work item does not exist on this estimate")
        return
    if work_item_id:
        raise HTTPException(status_code=422, detail="work_item_id only applies to work item notes")
    model = {
        NoteParentType.ESTIMATE: Estimate,
        NoteParentType.PROPERTY: Property,
        NoteParentType.CONTACT: Contact,
    }[parent_type]
    parent = await model.find_one(model.id == parent_id, model.company == company)
    if parent is None:
        raise HTTPException(status_code=404, detail=f"{parent_type.value.capitalize()} not found")


async def create_note(
    *,
    user: User,
    parent_type: NoteParentType,
    parent_id: PydanticObjectId,
    work_item_id: Optional[str],
    body: str,
) -> Note:
    assert user.company is not None
    await assert_parent_exists(user.company, parent_type, parent_id, work_item_id)
    note = Note(
        company=user.company,
        parent_type=parent_type,
        parent_id=parent_id,
        work_item_id=work_item_id if parent_type == NoteParentType.WORK_ITEM else None,
        body=body,
        created_by_email=_norm_email(user.email),
        created_by_name=author_display_name(user),
    )
    await note.insert()
    return note


async def list_notes(
    company: PydanticObjectId,
    parent_type: NoteParentType,
    parent_id: PydanticObjectId,
    work_item_id: Optional[str] = None,
) -> List[Note]:
    query = Note.find(Note.company == company, Note.parent_type == parent_type, Note.parent_id == parent_id)
    if work_item_id is not None:
        query = query.find(Note.work_item_id == work_item_id)
    return await query.sort(-Note.created_at).limit(MAX_NOTES_LISTED).to_list()


async def count_notes_by_work_item(company: PydanticObjectId, estimate_id: PydanticObjectId) -> Dict[str, int]:
    pipeline = [
        {"$match": {"company": company, "parent_type": NoteParentType.WORK_ITEM.value, "parent_id": estimate_id}},
        {"$group": {"_id": "$work_item_id", "count": {"$sum": 1}}},
    ]
    counts: Dict[str, int] = {}
    async for row in Note.get_pymongo_collection().aggregate(pipeline):
        if row["_id"]:
            counts[row["_id"]] = row["count"]
    return counts


async def update_note_body(note: Note, body: str) -> Note:
    await note.set({"body": body, "updated_at": datetime.now(timezone.utc)})
    return note


async def delete_note(note: Note) -> None:
    """Document first, blobs second — a failure between leaves orphaned blobs
    (harmless), never metadata pointing at deleted bytes."""
    attachments = list(note.attachments)
    await note.delete()
    if attachments:
        from services.note_attachments import delete_attachment_blobs  # local: avoids an import cycle at load

        await delete_attachment_blobs(attachments)


async def delete_notes_for_parent(parent_type: NoteParentType, parent_id: PydanticObjectId) -> int:
    notes = await Note.find(Note.parent_type == parent_type, Note.parent_id == parent_id).to_list()
    for note in notes:
        await delete_note(note)
    return len(notes)


async def delete_notes_for_work_items(estimate_id: PydanticObjectId, work_item_ids: Iterable[str]) -> int:
    ids = [i for i in work_item_ids if i]
    if not ids:
        return 0
    notes = await Note.find(
        Note.parent_type == NoteParentType.WORK_ITEM,
        Note.parent_id == estimate_id,
        In(Note.work_item_id, ids),
    ).to_list()
    for note in notes:
        await delete_note(note)
    return len(notes)
```

Until Task 8 creates `services/note_attachments.py`, `delete_note` only reaches the import when a note has attachments, which none do yet, so the tests pass. Task 8 makes the import real.

- [ ] **Step 4: Run the tests**

```bash
cd platform && ./run_tests.sh tests/test_notes_service.py -v
./run_mypy.sh services/notes.py && ./run_ruff.sh services/notes.py
```

Expected: 7 passed. mypy may flag the local import of a module that does not exist yet; if so, create `services/note_attachments.py` now containing only the stub below, which Task 8 fills in:

```python
"""Note attachment storage — filled in by Task 8 of the notes plan."""
from __future__ import annotations

from typing import Iterable

from models.note import NoteAttachment


async def delete_attachment_blobs(attachments: Iterable[NoteAttachment]) -> None:
    raise NotImplementedError
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add services/notes.py services/note_attachments.py tests/test_notes_service.py
git commit -m "feat: notes service with creator-only edit and owner delete

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: `routers/notes.py` — list, counts, create, update, delete

**Files:**
- Create: `platform/routers/notes.py`
- Modify: `platform/routers/__init__.py` (export `notes_router`), `platform/main.py:157` (include after `tasks_router`)
- Test: `platform/tests/test_notes_api.py` (new)

**Interfaces:**
- Consumes: everything from Task 6.
- Produces the HTTP surface Task 10 (portal `api/notes.ts`) calls:
  - `GET /notes?parent_type=&parent_id=[&work_item_id=]` → `List[Note]`
  - `GET /notes/counts?parent_id=<estimate_id>` → `Dict[str, int]`
  - `POST /notes` body `{parent_type, parent_id, work_item_id?, body}` → `Note`
  - `PATCH /notes/{note_id}` body `{body}` → `Note`
  - `DELETE /notes/{note_id}` → `{"message": "Note deleted"}`

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_notes_api.py`:

```python
"""/notes — CRUD, tenancy, and the creator/Owner rules over HTTP."""

from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from tests.helpers import create_company_user, onboard_owner, run_on_portal, unique_email


def _property_id(client: TestClient, company_id: str, email: str) -> str:
    response = client.post("/properties/", json={
        "street": "9 Note St", "city": "Kelowna", "prov_state": "BC", "country": "Canada",
        "contacts": [], "company": company_id,
    }, headers={"X-Test-Email": email})
    assert response.status_code == 200, response.text
    return response.json()["_id"]


def _estimate_with_work_item(client: TestClient, company_id: str) -> tuple[str, str]:
    async def _insert():
        from models.estimate import Estimate, EstimateStatus, JobItem
        from services.estimate_readable_id import insert_estimate_with_readable_id

        estimate = Estimate(title="Notes", company=PydanticObjectId(company_id), status=EstimateStatus.DRAFT, created_by="tests",
                            job_items=[JobItem(description="Sod")])
        estimate = await insert_estimate_with_readable_id(estimate)
        return str(estimate.id), estimate.job_items[0].id

    return run_on_portal(client, _insert)


def _company_with_three_roles(client: TestClient):
    owner = onboard_owner(client, unique_email("notes.owner"), company_name="Notes Co",
                          company_email=unique_email("notes.co"), phone="+15550100200")
    admin = create_company_user(client, manager_email=owner["email"], company_id=owner["company_id"],
                                email=unique_email("notes.admin"), role="Admin")
    member = create_company_user(client, manager_email=owner["email"], company_id=owner["company_id"],
                                 email=unique_email("notes.member"), role="Member")
    return owner, admin, member


def test_create_list_update_delete_on_a_property(client: TestClient, test_company_id: str):
    owner_email = "default.owner@example.com"
    prop = _property_id(client, test_company_id, owner_email)

    created = client.post("/notes", json={
        "parent_type": "property", "parent_id": prop, "body": "Gate code **4411**",
    })
    assert created.status_code == 200, created.text
    note = created.json()
    assert note["created_by_email"] == owner_email
    assert note["created_by_name"] == "Default Owner"
    assert note["attachments"] == []
    # Pydantic v2 renders an aware-UTC datetime with a Z suffix, not "+00:00".
    # The "+00:00" form only appears where a router hand-builds .isoformat().
    assert note["created_at"].endswith("Z")

    listed = client.get(f"/notes?parent_type=property&parent_id={prop}")
    assert listed.status_code == 200
    assert [n["_id"] for n in listed.json()] == [note["_id"]]

    updated = client.patch(f"/notes/{note['_id']}", json={"body": "Gate code 4412"})
    assert updated.status_code == 200
    assert updated.json()["body"] == "Gate code 4412"
    assert updated.json()["updated_at"] > note["updated_at"]

    deleted = client.delete(f"/notes/{note['_id']}")
    assert deleted.status_code == 200
    assert client.get(f"/notes?parent_type=property&parent_id={prop}").json() == []
    client.delete(f"/properties/{prop}")


def test_work_item_notes_need_a_real_work_item(client: TestClient, test_company_id: str):
    estimate_id, work_item_id = _estimate_with_work_item(client, test_company_id)

    missing = client.post("/notes", json={"parent_type": "work_item", "parent_id": estimate_id, "body": "x"})
    assert missing.status_code == 422
    wrong = client.post("/notes", json={"parent_type": "work_item", "parent_id": estimate_id,
                                        "work_item_id": "nope-nope-nope", "body": "x"})
    assert wrong.status_code == 422
    ok = client.post("/notes", json={"parent_type": "work_item", "parent_id": estimate_id,
                                     "work_item_id": work_item_id, "body": "x"})
    assert ok.status_code == 200, ok.text

    counts = client.get(f"/notes/counts?parent_id={estimate_id}")
    assert counts.status_code == 200
    assert counts.json() == {work_item_id: 1}

    client.delete(f"/estimates/{estimate_id}")


def test_estimate_level_notes(client: TestClient, test_company_id: str):
    estimate_id, work_item_id = _estimate_with_work_item(client, test_company_id)
    whole = client.post("/notes", json={"parent_type": "estimate", "parent_id": estimate_id, "body": "overall"})
    assert whole.status_code == 200, whole.text
    item = client.post("/notes", json={"parent_type": "work_item", "parent_id": estimate_id,
                                       "work_item_id": work_item_id, "body": "per item"})
    assert item.status_code == 200
    # The two feeds are separate even though they share a parent_id.
    assert [n["body"] for n in client.get(f"/notes?parent_type=estimate&parent_id={estimate_id}").json()] == ["overall"]
    assert client.get(f"/notes/counts?parent_id={estimate_id}").json() == {work_item_id: 1}
    with_item = client.post("/notes", json={"parent_type": "estimate", "parent_id": estimate_id,
                                            "work_item_id": work_item_id, "body": "x"})
    assert with_item.status_code == 422
    client.delete(f"/estimates/{estimate_id}")


def test_notes_are_writable_on_an_archived_estimate(client: TestClient, test_company_id: str):
    estimate_id, work_item_id = _estimate_with_work_item(client, test_company_id)
    assert client.patch(f"/estimates/{estimate_id}/archive").status_code == 200

    ok = client.post("/notes", json={"parent_type": "work_item", "parent_id": estimate_id,
                                     "work_item_id": work_item_id, "body": "still writable"})
    assert ok.status_code == 200, ok.text
    client.delete(f"/estimates/{estimate_id}")


def test_edit_is_creator_only_and_delete_is_creator_or_owner(client: TestClient):
    owner, admin, member = _company_with_three_roles(client)
    prop = _property_id(client, owner["company_id"], owner["email"])
    note = client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "mine"},
                       headers={"X-Test-Email": member["email"]}).json()

    for actor in (owner, admin):
        r = client.patch(f"/notes/{note['_id']}", json={"body": "theirs"}, headers={"X-Test-Email": actor["email"]})
        assert r.status_code == 403, actor["email"]
    assert client.patch(f"/notes/{note['_id']}", json={"body": "edited"},
                        headers={"X-Test-Email": member["email"]}).status_code == 200

    assert client.delete(f"/notes/{note['_id']}", headers={"X-Test-Email": admin["email"]}).status_code == 403
    assert client.delete(f"/notes/{note['_id']}", headers={"X-Test-Email": owner["email"]}).status_code == 200

    own = client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "mine again"},
                      headers={"X-Test-Email": member["email"]}).json()
    assert client.delete(f"/notes/{own['_id']}", headers={"X-Test-Email": member["email"]}).status_code == 200
    client.delete(f"/properties/{prop}", headers={"X-Test-Email": owner["email"]})


def test_a_closed_account_cannot_edit_or_delete_its_notes(client: TestClient):
    """Archiving a company revokes access everywhere, mutations included."""
    owner = onboard_owner(client, unique_email("notes.closed"), company_name="Closed Notes Co",
                          company_email=unique_email("notes.closed.co"), phone="+15550100400")
    headers = {"X-Test-Email": owner["email"]}
    prop = _property_id(client, owner["company_id"], owner["email"])
    note = client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "before close"},
                       headers=headers).json()

    assert client.delete(f"/companies/{owner['company_id']}", headers=headers).status_code == 200

    for response in (
        client.patch(f"/notes/{note['_id']}", json={"body": "after close"}, headers=headers),
        client.delete(f"/notes/{note['_id']}", headers=headers),
    ):
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "COMPANY_ARCHIVED"


def test_other_company_cannot_see_or_touch_a_note(client: TestClient, test_company_id: str):
    owner, _, _ = _company_with_three_roles(client)
    prop = _property_id(client, test_company_id, "default.owner@example.com")
    note = client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "private"}).json()

    other = {"X-Test-Email": owner["email"]}
    assert client.get(f"/notes?parent_type=property&parent_id={prop}", headers=other).status_code == 404
    assert client.patch(f"/notes/{note['_id']}", json={"body": "x"}, headers=other).status_code == 404
    assert client.delete(f"/notes/{note['_id']}", headers=other).status_code == 404
    assert client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "x"},
                       headers=other).status_code == 404
    client.delete(f"/notes/{note['_id']}")
    client.delete(f"/properties/{prop}")


def test_body_limits(client: TestClient, test_company_id: str):
    prop = _property_id(client, test_company_id, "default.owner@example.com")
    assert client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "   "}).status_code == 422
    assert client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "x" * 20_001}).status_code == 422
    client.delete(f"/properties/{prop}")
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_notes_api.py -v
```

Expected: FAIL with 404s on every `/notes` request (route not registered).

- [ ] **Step 3: Write the router**

Create `platform/routers/notes.py`:

```python
"""Notes on work items, properties and contacts. Rules live in services/notes.py."""
from __future__ import annotations

from typing import Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from dependencies import assert_user_company_access, require_authenticated_user
from models import Estimate, User
from models.note import MAX_NOTE_BODY_CHARS, Note, NoteParentType
from services.notes import (
    assert_can_delete_note,
    assert_can_edit_note,
    assert_parent_exists,
    count_notes_by_work_item,
    create_note,
    delete_note,
    list_notes,
    update_note_body,
)

router = APIRouter(prefix="/notes", tags=["notes"])


def _clean_body(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("A note needs some text")
    return cleaned


class CreateNoteRequest(BaseModel):
    parent_type: NoteParentType
    parent_id: PydanticObjectId
    work_item_id: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9-]{8,64}$")
    body: str = Field(max_length=MAX_NOTE_BODY_CHARS)

    @field_validator("body")
    @classmethod
    def _body_not_blank(cls, value: str) -> str:
        return _clean_body(value)


class UpdateNoteRequest(BaseModel):
    body: str = Field(max_length=MAX_NOTE_BODY_CHARS)

    @field_validator("body")
    @classmethod
    def _body_not_blank(cls, value: str) -> str:
        return _clean_body(value)


async def _get_note_for(user: User, note_id: str) -> Note:
    """404 for a missing note AND for another tenant's — never reveal existence.

    The company-access call is here rather than in each endpoint so that every
    route reaching a note by id inherits the archived-company hard block:
    PATCH, DELETE, and the attachment routes added later. Without it a member
    of a closed account could still edit and delete existing notes while being
    blocked from creating or listing them.
    """
    try:
        wanted = PydanticObjectId(note_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Note not found") from exc
    note = await Note.get(wanted)
    if note is None or note.company != user.company:
        raise HTTPException(status_code=404, detail="Note not found")
    await assert_user_company_access(user, note.company)
    return note


@router.get("", response_model=List[Note])
async def list_notes_endpoint(
    parent_type: NoteParentType = Query(...),
    parent_id: PydanticObjectId = Query(...),
    work_item_id: Optional[str] = Query(None),
    user: User = Depends(require_authenticated_user),
):
    assert user.company is not None
    await assert_user_company_access(user, user.company)
    if parent_type == NoteParentType.WORK_ITEM and not work_item_id:
        # Listing every work item's notes on one estimate is allowed; only
        # confirm the estimate itself is ours.
        if await Estimate.find_one(Estimate.id == parent_id, Estimate.company == user.company) is None:
            raise HTTPException(status_code=404, detail="Estimate not found")
    else:
        await assert_parent_exists(user.company, parent_type, parent_id, work_item_id)
    return await list_notes(user.company, parent_type, parent_id, work_item_id)


@router.get("/counts", response_model=Dict[str, int])
async def note_counts_endpoint(
    parent_id: PydanticObjectId = Query(..., description="The estimate id"),
    user: User = Depends(require_authenticated_user),
):
    assert user.company is not None
    await assert_user_company_access(user, user.company)
    return await count_notes_by_work_item(user.company, parent_id)


@router.post("", response_model=Note)
async def create_note_endpoint(
    payload: CreateNoteRequest,
    user: User = Depends(require_authenticated_user),
):
    assert user.company is not None
    await assert_user_company_access(user, user.company)
    return await create_note(
        user=user,
        parent_type=payload.parent_type,
        parent_id=payload.parent_id,
        work_item_id=payload.work_item_id,
        body=payload.body,
    )


@router.patch("/{note_id}", response_model=Note)
async def update_note_endpoint(
    note_id: str,
    payload: UpdateNoteRequest,
    user: User = Depends(require_authenticated_user),
):
    note = await _get_note_for(user, note_id)
    assert_can_edit_note(note, user)
    return await update_note_body(note, payload.body)


@router.delete("/{note_id}")
async def delete_note_endpoint(
    note_id: str,
    user: User = Depends(require_authenticated_user),
):
    note = await _get_note_for(user, note_id)
    assert_can_delete_note(note, user)
    await delete_note(note)
    return {"message": "Note deleted"}
```

`Estimate` comes from `from models import Estimate, User`.

Register it: in `platform/routers/__init__.py` add `from .notes import router as notes_router` following the existing pattern and add `notes_router` to `__all__`; in `platform/main.py` add `notes_router` to the `from routers import (...)` list and `app.include_router(notes_router, dependencies=protected_route_dependencies)` after the tasks line.

- [ ] **Step 4: Run the tests**

```bash
cd platform && ./run_tests.sh tests/test_notes_api.py -v
./run_mypy.sh routers/notes.py main.py && ./run_ruff.sh routers/notes.py routers/__init__.py main.py
```

Expected: 8 passed, gates clean. If `test_body_limits` sees 422 from the `max_length` on the model rather than the validator, that is fine: both are 422.

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add routers/notes.py routers/__init__.py main.py tests/test_notes_api.py
git commit -m "feat: /notes endpoints for work items, properties and contacts

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Attachments — `services/note_attachments.py` and the three endpoints

**Files:**
- Modify: `platform/services/note_attachments.py` (replace the Task 6 stub)
- Modify: `platform/routers/notes.py` (three endpoints)
- Test: `platform/tests/test_note_attachments_api.py` (new)

**Interfaces:**
- Consumes: `media_blobs` (Task 4), `Note`/`NoteAttachment`/`NoteAttachmentKind` (Task 5), `_get_note_for` + `assert_can_edit_note` (Tasks 6–7).
- Produces:
  - `NOTE_ATTACHMENT_BUCKET = "note_attachments"`
  - `async store_note_attachment(file: UploadFile) -> NoteAttachment` (raises `MediaValidationError`)
  - `async read_note_attachment(attachment, size: Literal["full","thumb"]) -> tuple[bytes | None, str]`
  - `async delete_attachment_blobs(attachments: Iterable[NoteAttachment]) -> None`
  - HTTP: `POST /notes/{id}/attachments` (multipart `file`) → `Note`; `GET /notes/{id}/attachments/{attachment_id}?size=full|thumb` → bytes; `DELETE /notes/{id}/attachments/{attachment_id}` → `Note`.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_note_attachments_api.py`:

```python
"""Note attachments: images (with thumbnail), videos (streamed), PDFs."""

import io

from beanie import PydanticObjectId
from fastapi.testclient import TestClient
from PIL import Image

from tests.helpers import create_company_user, onboard_owner, unique_email


def _jpeg_bytes(width=800, height=600) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (120, 160, 90)).save(buf, format="JPEG")
    return buf.getvalue()


def _mp4_bytes(size=4096) -> bytes:
    header = b"\x00\x00\x00\x18ftypmp42"
    return header + b"\x00" * (size - len(header))


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _property_note(client: TestClient, company_id: str, email: str) -> tuple[str, str]:
    prop = client.post("/properties/", json={
        "street": "9 Note St", "city": "Kelowna", "prov_state": "BC", "country": "Canada",
        "contacts": [], "company": company_id,
    }, headers={"X-Test-Email": email}).json()["_id"]
    note = client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "with files"},
                       headers={"X-Test-Email": email}).json()
    return prop, note["_id"]


def _blob_exists(client: TestClient, file_id: str) -> bool:
    async def _check():
        from models import Note

        db = Note.get_pymongo_collection().database
        return await db["note_attachments.files"].find_one({"_id": PydanticObjectId(file_id)}) is not None

    from tests.helpers import run_on_portal
    return run_on_portal(client, _check)


def test_image_video_and_pdf_upload_and_serve(client: TestClient, test_company_id: str):
    email = "default.owner@example.com"
    prop, note_id = _property_note(client, test_company_id, email)

    img = client.post(f"/notes/{note_id}/attachments", files={"file": ("site.jpg", _jpeg_bytes(), "image/jpeg")})
    assert img.status_code == 200, img.text
    image = img.json()["attachments"][0]
    assert image["kind"] == "image" and image["thumb_file_id"]

    vid = client.post(f"/notes/{note_id}/attachments", files={"file": ("walk.mp4", _mp4_bytes(), "video/mp4")})
    assert vid.status_code == 200, vid.text
    video = vid.json()["attachments"][1]
    assert video["kind"] == "video" and video["thumb_file_id"] is None

    pdf = client.post(f"/notes/{note_id}/attachments", files={"file": ("gate.pdf", _pdf_bytes(), "application/pdf")})
    assert pdf.status_code == 200, pdf.text
    doc = pdf.json()["attachments"][2]
    assert doc["kind"] == "pdf" and doc["thumb_file_id"] is None and doc["size_bytes"] == len(_pdf_bytes())

    thumb = client.get(f"/notes/{note_id}/attachments/{image['file_id']}?size=thumb")
    assert thumb.status_code == 200 and thumb.headers["content-type"] == "image/jpeg"
    assert max(Image.open(io.BytesIO(thumb.content)).size) <= 320

    assert client.get(f"/notes/{note_id}/attachments/{video['file_id']}?size=thumb").status_code == 404
    assert client.get(f"/notes/{note_id}/attachments/{doc['file_id']}?size=thumb").status_code == 404
    served = client.get(f"/notes/{note_id}/attachments/{doc['file_id']}")
    assert served.status_code == 200 and served.headers["content-type"] == "application/pdf"
    assert served.content == _pdf_bytes()

    client.delete(f"/notes/{note_id}")
    assert not _blob_exists(client, image["file_id"])
    assert not _blob_exists(client, video["file_id"])
    client.delete(f"/properties/{prop}")


def test_rejects_wrong_bytes_unknown_types_and_oversize(client: TestClient, test_company_id: str):
    email = "default.owner@example.com"
    prop, note_id = _property_note(client, test_company_id, email)

    bad_bytes = client.post(f"/notes/{note_id}/attachments", files={"file": ("x.png", b"MZ\x90 exe", "image/png")})
    assert bad_bytes.status_code == 400
    exe = client.post(f"/notes/{note_id}/attachments", files={"file": ("x.exe", b"MZ", "application/octet-stream")})
    assert exe.status_code == 400
    fake_pdf = client.post(f"/notes/{note_id}/attachments", files={"file": ("x.pdf", _jpeg_bytes(), "application/pdf")})
    assert fake_pdf.status_code == 400
    big = client.post(f"/notes/{note_id}/attachments",
                      files={"file": ("big.mp4", _mp4_bytes(51 * 1024 * 1024), "video/mp4")})
    assert big.status_code == 400
    assert client.get(f"/notes?parent_type=property&parent_id={prop}").json()[0]["attachments"] == []

    client.delete(f"/notes/{note_id}")
    client.delete(f"/properties/{prop}")


def test_attachment_cap(client: TestClient, test_company_id: str):
    prop, note_id = _property_note(client, test_company_id, "default.owner@example.com")
    for _ in range(10):
        assert client.post(f"/notes/{note_id}/attachments",
                           files={"file": ("p.pdf", _pdf_bytes(), "application/pdf")}).status_code == 200
    assert client.post(f"/notes/{note_id}/attachments",
                       files={"file": ("p.pdf", _pdf_bytes(), "application/pdf")}).status_code == 400
    client.delete(f"/notes/{note_id}")
    client.delete(f"/properties/{prop}")


def test_only_the_author_adds_or_removes_attachments(client: TestClient):
    owner = onboard_owner(client, unique_email("att.owner"), company_name="Att Co",
                          company_email=unique_email("att.co"), phone="+15550100300")
    member = create_company_user(client, manager_email=owner["email"], company_id=owner["company_id"],
                                 email=unique_email("att.member"), role="Member")
    prop, note_id = _property_note(client, owner["company_id"], member["email"])
    as_owner = {"X-Test-Email": owner["email"]}
    as_member = {"X-Test-Email": member["email"]}

    assert client.post(f"/notes/{note_id}/attachments", headers=as_owner,
                       files={"file": ("p.pdf", _pdf_bytes(), "application/pdf")}).status_code == 403
    added = client.post(f"/notes/{note_id}/attachments", headers=as_member,
                        files={"file": ("p.pdf", _pdf_bytes(), "application/pdf")})
    assert added.status_code == 200
    att = added.json()["attachments"][0]
    # Everyone in the company can READ it.
    assert client.get(f"/notes/{note_id}/attachments/{att['file_id']}", headers=as_owner).status_code == 200
    assert client.delete(f"/notes/{note_id}/attachments/{att['file_id']}", headers=as_owner).status_code == 403
    assert client.delete(f"/notes/{note_id}/attachments/{att['file_id']}", headers=as_member).status_code == 200

    client.delete(f"/notes/{note_id}", headers=as_owner)
    client.delete(f"/properties/{prop}", headers=as_owner)
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_note_attachments_api.py -v
```

Expected: FAIL with 404/405 on the attachment routes.

- [ ] **Step 3: Write the attachment service**

Replace `platform/services/note_attachments.py`:

```python
"""Note attachment storage — the "note_attachments" GridFS bucket.

Same pipeline as task photos (services/media_blobs.py): magic-byte checks,
a 320px JPEG thumbnail for images, streamed video with a mid-stream cap, and
now PDFs (no thumbnail). Served back through the API, never a public URL.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Literal, Optional, Tuple

from beanie import PydanticObjectId
from fastapi import UploadFile

from models.note import NoteAttachment, NoteAttachmentKind
from services import media_blobs
from services.media_blobs import (
    MediaValidationError,
    is_pdf_content_type,
    is_video_content_type,
    normalize_content_type,
    validate_image_upload,
    validate_pdf_upload,
)

NOTE_ATTACHMENT_BUCKET = "note_attachments"


async def store_note_attachment(file: UploadFile) -> NoteAttachment:
    """Validate and store one upload; raises MediaValidationError (→ 400)."""
    declared = file.content_type or ""
    thumb_file_id: Optional[PydanticObjectId] = None

    if is_video_content_type(declared):
        filename = file.filename or "video"
        # max_size_bytes is a REQUIRED keyword since ruling R8 made the caps
        # injectable; media_blobs keeps no per-feature constants of its own.
        file_id, size_bytes = await media_blobs.store_video_stream(
            NOTE_ATTACHMENT_BUCKET, file, filename, declared,
            max_size_bytes=media_blobs.MAX_VIDEO_SIZE_BYTES,
        )
        kind, content_type = NoteAttachmentKind.VIDEO, normalize_content_type(declared)
    elif is_pdf_content_type(declared):
        content = await file.read()
        content_type = validate_pdf_upload(content, declared)
        filename = file.filename or "document.pdf"
        file_id = await media_blobs.store_blob(NOTE_ATTACHMENT_BUCKET, content, filename, content_type)
        kind, size_bytes = NoteAttachmentKind.PDF, len(content)
    else:
        content = await file.read()
        content_type = validate_image_upload(content, declared)   # rejects every other type
        filename = file.filename or "photo"
        file_id, thumb_file_id = await media_blobs.store_image_blobs(
            NOTE_ATTACHMENT_BUCKET, content, filename, content_type
        )
        kind, size_bytes = NoteAttachmentKind.IMAGE, len(content)

    return NoteAttachment(
        file_id=file_id,
        thumb_file_id=thumb_file_id,
        kind=kind,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        uploaded_at=datetime.now(timezone.utc),
    )


async def read_note_attachment(
    attachment: NoteAttachment, size: Literal["full", "thumb"]
) -> Tuple[Optional[bytes], str]:
    """(bytes, media_type). bytes is None when the blob is gone."""
    if size == "thumb":
        if attachment.thumb_file_id is None:
            return None, "image/jpeg"
        content = await media_blobs.read_blob(NOTE_ATTACHMENT_BUCKET, attachment.thumb_file_id)
        if content is not None:
            return content, "image/jpeg"
    content = await media_blobs.read_blob(NOTE_ATTACHMENT_BUCKET, attachment.file_id)
    return content, attachment.content_type


async def delete_attachment_blobs(attachments: Iterable[NoteAttachment]) -> None:
    ids: list[PydanticObjectId | None] = []
    for attachment in attachments:
        ids.extend([attachment.file_id, attachment.thumb_file_id])
    if ids:
        await media_blobs.delete_blobs(NOTE_ATTACHMENT_BUCKET, *ids)


__all__ = [
    "MediaValidationError",
    "NOTE_ATTACHMENT_BUCKET",
    "delete_attachment_blobs",
    "read_note_attachment",
    "store_note_attachment",
]
```

- [ ] **Step 4: Add the endpoints**

Append to `platform/routers/notes.py` (add `File`, `UploadFile`, `Response`, `Literal`, `datetime`/`timezone` imports, and the service imports):

```python
from models.note import MAX_ATTACHMENTS_PER_NOTE, NoteAttachment
from services.media_blobs import MediaValidationError, max_media_size_bytes
from services.note_attachments import (
    delete_attachment_blobs,
    read_note_attachment,
    store_note_attachment,
)


def _find_attachment(note: Note, attachment_id: str) -> NoteAttachment:
    try:
        wanted = PydanticObjectId(attachment_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Attachment not found") from exc
    for attachment in note.attachments:
        if attachment.file_id == wanted:
            return attachment
    raise HTTPException(status_code=404, detail="Attachment not found")


@router.post("/{note_id}/attachments", response_model=Note)
async def upload_attachment_endpoint(
    note_id: str,
    file: UploadFile = File(...),
    user: User = Depends(require_authenticated_user),
):
    note = await _get_note_for(user, note_id)
    assert_can_edit_note(note, user)
    if len(note.attachments) >= MAX_ATTACHMENTS_PER_NOTE:
        raise HTTPException(status_code=400, detail=f"A note can carry at most {MAX_ATTACHMENTS_PER_NOTE} attachments.")

    # Reject oversize uploads from the multipart headers before buffering.
    declared = file.content_type or ""
    cap = max_media_size_bytes(declared)
    if file.size is not None and file.size > cap:
        raise HTTPException(status_code=400, detail=f"Files are limited to {cap // (1024 * 1024)}MB.")

    try:
        attachment = await store_note_attachment(file)
    except MediaValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Atomic $push: two uploads from one composer must not clobber each other.
    await Note.get_pymongo_collection().update_one(
        {"_id": note.id},
        {"$push": {"attachments": attachment.model_dump()},
         "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return await _get_note_for(user, note_id)


@router.get("/{note_id}/attachments/{attachment_id}")
async def get_attachment_endpoint(
    note_id: str,
    attachment_id: str,
    size: Literal["full", "thumb"] = Query("full"),
    user: User = Depends(require_authenticated_user),
):
    note = await _get_note_for(user, note_id)
    attachment = _find_attachment(note, attachment_id)
    if size == "thumb" and attachment.thumb_file_id is None:
        raise HTTPException(status_code=404, detail="This attachment has no thumbnail")
    content, media_type = await read_note_attachment(attachment, size)
    if content is None:
        raise HTTPException(status_code=404, detail="Attachment data not found")
    return Response(content=content, media_type=media_type)


@router.delete("/{note_id}/attachments/{attachment_id}", response_model=Note)
async def delete_attachment_endpoint(
    note_id: str,
    attachment_id: str,
    user: User = Depends(require_authenticated_user),
):
    note = await _get_note_for(user, note_id)
    assert_can_edit_note(note, user)
    attachment = _find_attachment(note, attachment_id)
    await Note.get_pymongo_collection().update_one(
        {"_id": note.id},
        {"$pull": {"attachments": {"file_id": attachment.file_id}},
         "$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    await delete_attachment_blobs([attachment])
    return await _get_note_for(user, note_id)
```

- [ ] **Step 5: Run the tests and gates**

```bash
cd platform && ./run_tests.sh tests/test_note_attachments_api.py tests/test_notes_api.py tests/test_notes_service.py -v
./run_mypy.sh services/note_attachments.py routers/notes.py services/notes.py
./run_ruff.sh services/note_attachments.py routers/notes.py services/notes.py
./run_bandit.sh services routers/notes.py
```

Expected: all pass; B110 count unchanged at 13.

- [ ] **Step 6: Commit (ask first)**

```bash
cd platform && git add services/note_attachments.py routers/notes.py tests/test_note_attachments_api.py
git commit -m "feat: image, video and PDF attachments on notes

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Cascades — estimate delete and PUT, property and contact delete, company cleanup

**Files:**
- Modify: `platform/routers/estimates.py` (PUT after `.set()` at `:1303`; DELETE at `:1352`)
- Modify: `platform/routers/properties.py:466-502`, `platform/routers/contacts.py:280-307`
- Modify: `platform/scripts/cleanup/cleanup_company.py:126-166`
- Test: `platform/tests/test_notes_cascade.py` (new)

**Interfaces:**
- Consumes: `delete_notes_for_parent`, `delete_notes_for_work_items` (Task 6).
- Produces: no new names. Behavior only.

- [ ] **Step 1: Write the failing tests**

Create `platform/tests/test_notes_cascade.py`:

```python
"""Notes die with their parent: estimate delete, work item removal via PUT,
property delete, contact delete."""

from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from tests.helpers import run_on_portal


def _count_notes(client: TestClient, parent_id: str) -> int:
    async def _count():
        from models import Note

        return await Note.find(Note.parent_id == PydanticObjectId(parent_id)).count()

    return run_on_portal(client, _count)


def _estimate(client: TestClient, company_id: str, descriptions: list[str]) -> tuple[str, list[str]]:
    async def _insert():
        from models.estimate import Estimate, EstimateStatus, JobItem
        from services.estimate_readable_id import insert_estimate_with_readable_id

        estimate = Estimate(title="cascade", company=PydanticObjectId(company_id), status=EstimateStatus.DRAFT, created_by="tests",
                            created_by_email="default.owner@example.com",
                            job_items=[JobItem(description=d) for d in descriptions])
        estimate = await insert_estimate_with_readable_id(estimate)
        return str(estimate.id), [ji.id for ji in estimate.job_items]

    return run_on_portal(client, _insert)


def _add_note(client: TestClient, estimate_id: str, work_item_id: str) -> None:
    r = client.post("/notes", json={"parent_type": "work_item", "parent_id": estimate_id,
                                    "work_item_id": work_item_id, "body": "n"})
    assert r.status_code == 200, r.text


def test_removing_a_work_item_via_put_deletes_its_notes_only(client: TestClient, test_company_id: str):
    estimate_id, (a, b) = _estimate(client, test_company_id, ["A", "B"])
    _add_note(client, estimate_id, a)
    _add_note(client, estimate_id, b)

    r = client.put(f"/estimates/{estimate_id}", json={"job_items": [{"id": b, "description": "B"}]})
    assert r.status_code == 200, r.text
    assert client.get(f"/notes/counts?parent_id={estimate_id}").json() == {b: 1}
    client.delete(f"/estimates/{estimate_id}")


def test_deleting_the_estimate_deletes_every_note(client: TestClient, test_company_id: str):
    estimate_id, (a,) = _estimate(client, test_company_id, ["A"])
    _add_note(client, estimate_id, a)
    assert client.post("/notes", json={"parent_type": "estimate", "parent_id": estimate_id,
                                       "body": "estimate-level"}).status_code == 200
    assert _count_notes(client, estimate_id) == 2
    assert client.delete(f"/estimates/{estimate_id}").status_code == 200
    assert _count_notes(client, estimate_id) == 0


def test_deleting_a_property_or_contact_deletes_its_notes(client: TestClient, test_company_id: str):
    prop = client.post("/properties/", json={"street": "1 C St", "city": "K", "prov_state": "BC",
                                             "contacts": [], "company": test_company_id}).json()["_id"]
    contact = client.post("/contacts/", json={"first_name": "C", "last_name": "D",
                                              "company": test_company_id}).json()["_id"]
    assert client.post("/notes", json={"parent_type": "property", "parent_id": prop, "body": "p"}).status_code == 200
    assert client.post("/notes", json={"parent_type": "contact", "parent_id": contact, "body": "c"}).status_code == 200

    assert client.delete(f"/properties/{prop}").status_code == 200
    assert client.delete(f"/contacts/{contact}").status_code == 200
    assert _count_notes(client, prop) == 0
    assert _count_notes(client, contact) == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_notes_cascade.py -v
```

Expected: 3 FAIL — notes survive their parents.

- [ ] **Step 3: Wire the cascades**

`platform/routers/estimates.py`, PUT handler, right after `await existing_estimate.set(update_data)`:

```python
    # A work item can only disappear here. Its notes go with it (see below).
```

`existing_estimate.job_items` has already been replaced by `.set()` at this point, so do **not** read it here. Use `stored_ids` — the list Task 1 captured at the top of the `if payload.job_items is not None:` block, before the rebuild — and write the cascade as:

```python
    if payload.job_items is not None:
        removed_ids = set(stored_ids) - {ji.id for ji in update_data["job_items"]}
        if removed_ids:
            background_tasks.add_task(delete_notes_for_work_items, existing_estimate.id, removed_ids)
```

DELETE handler, after `await estimate.delete()` (both feeds share the estimate's id as parent):

```python
    background_tasks.add_task(delete_notes_for_parent, NoteParentType.WORK_ITEM, estimate.id)
    background_tasks.add_task(delete_notes_for_parent, NoteParentType.ESTIMATE, estimate.id)
```

Imports: `from models.note import NoteParentType` and `from services.notes import delete_notes_for_parent, delete_notes_for_work_items`.

`platform/routers/properties.py` `delete_property`, before `await property.delete()`:

```python
    await delete_notes_for_parent(NoteParentType.PROPERTY, property.id)
```

`platform/routers/contacts.py` `delete_contact`, before `await contact.delete()`:

```python
    await delete_notes_for_parent(NoteParentType.CONTACT, contact.id)
```

(both with the same two imports.)

`platform/scripts/cleanup/cleanup_company.py`: add beside `_delete_task_photo_blobs`:

```python
async def _delete_note_attachment_blobs(company_id: PydanticObjectId, dry_run: bool) -> int:
    """GridFS blobs behind this company's note attachments — collected from
    the notes before the note documents are deleted below."""
    from models import Note

    database = Note.get_pymongo_collection().database
    blob_ids = []
    async for note_doc in database["notes"].find({"company": company_id}, {"attachments": 1}):
        for attachment in note_doc.get("attachments") or []:
            for key in ("file_id", "thumb_file_id"):
                if attachment.get(key) is not None:
                    blob_ids.append(attachment[key])
    if not blob_ids:
        return 0
    if not dry_run:
        await database["note_attachments.files"].delete_many({"_id": {"$in": blob_ids}})
        await database["note_attachments.chunks"].delete_many({"files_id": {"$in": blob_ids}})
    _deleted("note attachment blob(s)", len(blob_ids), dry_run)
    return len(blob_ids)
```

and in `cleanup_company_resources`, after the task-photo line: `totals["note_attachment_blobs"] = await _delete_note_attachment_blobs(company_id, dry_run)`. The `notes` collection itself is picked up automatically by `company_scoped_models()`.

- [ ] **Step 4: Run the tests and gates**

```bash
cd platform && ./run_tests.sh tests/test_notes_cascade.py tests/test_estimate_api.py -k "delete_estimate" -v
./run_mypy.sh routers/estimates.py routers/properties.py routers/contacts.py scripts/cleanup/cleanup_company.py
./run_ruff.sh routers/estimates.py routers/properties.py routers/contacts.py scripts/cleanup/cleanup_company.py
```

Expected: all pass, gates clean. (`BackgroundTasks` run inside `TestClient` before the response returns, so the PUT/DELETE assertions see the cascade.)

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add routers/estimates.py routers/properties.py routers/contacts.py scripts/cleanup/cleanup_company.py tests/test_notes_cascade.py
git commit -m "feat: cascade note deletion from estimates, work items, properties and contacts

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Phase 2 deploy note:** after this reaches Dev and prod, run `python scripts/backfill_job_item_ids.py --apply` on each. Portal Phase 4 must not ship before that has happened on prod.

---

# Phase 3 — Shared portal components

### Task 10: Types, API client, media constants, and the pure permission/display helpers

**Files:**
- Modify: `portal/src/types/api.ts` (append), `portal/src/lib/media.ts` (append)
- Create: `portal/src/api/notes.ts`, `portal/src/lib/notesPermissions.ts`, `portal/src/lib/noteDisplay.ts`
- Test: `portal/tests/notesPermissions.test.ts`, `portal/tests/noteDisplay.test.ts`, `portal/tests/media.test.ts` (new)

**Interfaces:**
- Produces (used by every later portal task):
  - types: `NoteParentType = "work_item" | "property" | "contact"`, `NoteAttachmentKind = "image" | "video" | "pdf"`, `NoteAttachment`, `Note`
  - `notesApi.list({ parentType, parentId, workItemId? })`, `notesApi.counts(estimateId)`, `notesApi.create({ parent_type, parent_id, work_item_id?, body })`, `notesApi.update(id, body)`, `notesApi.remove(id)`, `notesApi.uploadAttachment(noteId, file)`, `notesApi.removeAttachment(noteId, attachmentId)`, `notesApi.attachmentBlob(noteId, attachmentId, size)`
  - `canEditNote(note, user)`, `canDeleteNote(note, user)`
  - `formatNoteDate(iso)` → `"Sep 17, 2026"`, `isNoteEdited(note)`
  - media: `MAX_IMAGE_SIZE_BYTES`, `MAX_PDF_SIZE_BYTES`, `PDF_CONTENT_TYPE`, `NOTE_ATTACHMENT_ACCEPT`, `isPdf(type)`, `attachmentSizeError(file): string | null`

- [ ] **Step 1: Write the failing tests**

`portal/tests/notesPermissions.test.ts`:

```ts
import { describe, test, expect } from "vitest";
import { canDeleteNote, canEditNote } from "../src/lib/notesPermissions";
import type { Note } from "../src/types/api";

const note = { created_by_email: "ana@x.com" } as Note;

describe("note permissions (mirror of services/notes.py)", () => {
  test("author can edit and delete, case-insensitively", () => {
    const me = { email: "ANA@x.com", role: "Member" };
    expect(canEditNote(note, me)).toBe(true);
    expect(canDeleteNote(note, me)).toBe(true);
  });
  test("Owner can delete but not edit", () => {
    const owner = { email: "o@x.com", role: "Owner" };
    expect(canEditNote(note, owner)).toBe(false);
    expect(canDeleteNote(note, owner)).toBe(true);
  });
  test("Admin and Member can do neither; no user can do nothing", () => {
    expect(canDeleteNote(note, { email: "a@x.com", role: "Admin" })).toBe(false);
    expect(canEditNote(note, { email: "m@x.com", role: "Member" })).toBe(false);
    expect(canEditNote(note, null)).toBe(false);
    expect(canDeleteNote(note, null)).toBe(false);
  });
});
```

`portal/tests/noteDisplay.test.ts`:

```ts
import { describe, test, expect } from "vitest";
import { formatNoteDate, isNoteEdited } from "../src/lib/noteDisplay";
import type { Note } from "../src/types/api";

describe("noteDisplay", () => {
  test("formatNoteDate renders a short date and dashes bad input", () => {
    expect(formatNoteDate("2026-09-17T12:00:00+00:00")).toMatch(/Sep 1[78], 2026/);
    expect(formatNoteDate("garbage")).toBe("-");
    expect(formatNoteDate(undefined)).toBe("-");
  });
  test("isNoteEdited compares timestamps with a one-second tolerance", () => {
    const base = { created_at: "2026-09-17T12:00:00+00:00" } as Note;
    expect(isNoteEdited({ ...base, updated_at: "2026-09-17T12:00:00.400+00:00" })).toBe(false);
    expect(isNoteEdited({ ...base, updated_at: "2026-09-17T12:05:00+00:00" })).toBe(true);
  });
});
```

`portal/tests/media.test.ts`:

```ts
import { describe, test, expect } from "vitest";
import {
  MAX_IMAGE_SIZE_BYTES, MAX_PDF_SIZE_BYTES, MAX_VIDEO_SIZE_BYTES,
  attachmentSizeError, isPdf,
} from "../src/lib/media";

describe("attachment size guard", () => {
  const file = (type: string, size: number) => ({ name: "f", type, size }) as File;
  test("each kind has its own cap", () => {
    expect(attachmentSizeError(file("image/jpeg", MAX_IMAGE_SIZE_BYTES))).toBeNull();
    expect(attachmentSizeError(file("image/jpeg", MAX_IMAGE_SIZE_BYTES + 1))).toMatch(/10MB/);
    expect(attachmentSizeError(file("video/mp4", MAX_VIDEO_SIZE_BYTES + 1))).toMatch(/50MB/);
    expect(attachmentSizeError(file("application/pdf", MAX_PDF_SIZE_BYTES + 1))).toMatch(/10MB/);
  });
  test("isPdf", () => {
    expect(isPdf("application/pdf")).toBe(true);
    expect(isPdf("image/png")).toBe(false);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd portal && npm test -- tests/notesPermissions.test.ts tests/noteDisplay.test.ts tests/media.test.ts
```

Expected: FAIL, modules not found / exports missing.

- [ ] **Step 3: Write the code**

Append to `portal/src/types/api.ts`:

```ts
export type NoteParentType = "work_item" | "estimate" | "property" | "contact";
export type NoteAttachmentKind = "image" | "video" | "pdf";

export interface NoteAttachment {
  file_id: string;
  thumb_file_id?: string | null;
  kind: NoteAttachmentKind;
  filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_at?: string;
}

/** models/note.py. `created_by_email` is the authorization key; the name is a snapshot. */
export interface Note {
  _id?: string;
  id?: string;
  company?: string;
  parent_type: NoteParentType;
  parent_id: string;
  work_item_id?: string | null;
  body: string;
  attachments: NoteAttachment[];
  created_by_email: string;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}
```

Append to `portal/src/lib/media.ts`:

```ts
/** Client-side mirrors of services/media_blobs.py caps. */
export const MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;
export const MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024;
export const PDF_CONTENT_TYPE = "application/pdf";
export const isPdf = (contentType: string | null | undefined): boolean =>
  contentType === PDF_CONTENT_TYPE;
/** The "Attach" input on a note: videos and PDFs (photos have their own camera input). */
export const NOTE_ATTACHMENT_ACCEPT = `${VIDEO_ACCEPT},${PDF_CONTENT_TYPE}`;

/** Fast local rejection before a doomed upload. Null means the size is fine. */
export function attachmentSizeError(file: Pick<File, "name" | "type" | "size">): string | null {
  const cap = isVideo(file.type)
    ? MAX_VIDEO_SIZE_BYTES
    : isPdf(file.type)
      ? MAX_PDF_SIZE_BYTES
      : MAX_IMAGE_SIZE_BYTES;
  if (file.size <= cap) return null;
  const kind = isVideo(file.type) ? "videos" : isPdf(file.type) ? "PDFs" : "photos";
  return `"${file.name}" is too large — ${kind} are limited to ${cap / (1024 * 1024)}MB.`;
}
```

Create `portal/src/api/notes.ts`:

```ts
import { apiRequest, apiRequestBlob } from "./client";
import type { Note, NoteParentType } from "../types/api";

export interface ListNotesArgs {
  parentType: NoteParentType;
  parentId: string;
  workItemId?: string;
}

export interface CreateNotePayload {
  parent_type: NoteParentType;
  parent_id: string;
  work_item_id?: string;
  body: string;
}

export const notesApi = {
  list: ({ parentType, parentId, workItemId }: ListNotesArgs) => {
    const params = new URLSearchParams({ parent_type: parentType, parent_id: parentId });
    if (workItemId) params.set("work_item_id", workItemId);
    return apiRequest<Note[]>(`/notes?${params}`);
  },
  /** `{ [work_item_id]: count }` for one estimate. */
  counts: (estimateId: string) =>
    apiRequest<Record<string, number>>(`/notes/counts?parent_id=${encodeURIComponent(estimateId)}`),
  create: (payload: CreateNotePayload) =>
    apiRequest<Note>("/notes", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, body: string) =>
    apiRequest<Note>(`/notes/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify({ body }) }),
  remove: (id: string) => apiRequest<{ message: string }>(`/notes/${encodeURIComponent(id)}`, { method: "DELETE" }),
  uploadAttachment: (noteId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiRequest<Note>(`/notes/${encodeURIComponent(noteId)}/attachments`, { method: "POST", body: formData });
  },
  removeAttachment: (noteId: string, attachmentId: string) =>
    apiRequest<Note>(`/notes/${encodeURIComponent(noteId)}/attachments/${encodeURIComponent(attachmentId)}`, {
      method: "DELETE",
    }),
  attachmentBlob: (noteId: string, attachmentId: string, size: "full" | "thumb" = "full") =>
    apiRequestBlob(`/notes/${encodeURIComponent(noteId)}/attachments/${encodeURIComponent(attachmentId)}?size=${size}`),
};
```

Create `portal/src/lib/notesPermissions.ts`:

```ts
import type { Note } from "../types/api";

/** The subset of AuthUser these rules read. */
export interface NoteActor {
  email?: string | null;
  role?: string | null;
}

const norm = (value: string | null | undefined) => (value || "").trim().toLowerCase();

/** Creator-only. Mirrors services/notes.py::assert_can_edit_note; the server enforces it too. */
export function canEditNote(note: Pick<Note, "created_by_email">, user: NoteActor | null | undefined): boolean {
  if (!user?.email) return false;
  return norm(note.created_by_email) === norm(user.email);
}

/** Creator or company Owner (design decision D2). Admins get no override. */
export function canDeleteNote(note: Pick<Note, "created_by_email">, user: NoteActor | null | undefined): boolean {
  if (!user) return false;
  return canEditNote(note, user) || user.role === "Owner";
}
```

Create `portal/src/lib/noteDisplay.ts`:

```ts
import type { Note } from "../types/api";

export function formatNoteDate(value: string | null | undefined): string {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/** True when the body was changed after creation (beyond clock jitter). */
export function isNoteEdited(note: Pick<Note, "created_at" | "updated_at">): boolean {
  const created = new Date(note.created_at).getTime();
  const updated = new Date(note.updated_at).getTime();
  if (Number.isNaN(created) || Number.isNaN(updated)) return false;
  return updated - created > 1000;
}
```

- [ ] **Step 4: Run the tests and typecheck**

```bash
cd portal && npm test -- tests/notesPermissions.test.ts tests/noteDisplay.test.ts tests/media.test.ts && npm run typecheck
```

Expected: pass, clean.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/types/api.ts src/lib/media.ts src/api/notes.ts src/lib/notesPermissions.ts src/lib/noteDisplay.ts tests/notesPermissions.test.ts tests/noteDisplay.test.ts tests/media.test.ts
git commit -m "feat: notes API client, types and permission helpers

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: `NoteMarkdown` — safe light-surface renderer

**Files:**
- Create: `portal/src/components/notes/NoteMarkdown.tsx`
- Test: `portal/tests/NoteMarkdown.test.tsx` (new)

**Interfaces:**
- Produces: `<NoteMarkdown body={string} />`.

- [ ] **Step 1: Write the failing test**

`portal/tests/NoteMarkdown.test.tsx`:

```tsx
/** Notes are the first place one user's markdown renders for another user in
 *  the same company. No raw HTML, no javascript: links, links open in a new tab. */
import { describe, test, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { NoteMarkdown } from "../src/components/notes/NoteMarkdown";

afterEach(cleanup);

describe("NoteMarkdown", () => {
  test("renders gfm markdown", () => {
    render(<NoteMarkdown body={"East bed **first**\n\n- [ ] gate\n- [x] shed"} />);
    expect(screen.getByText("first").tagName).toBe("STRONG");
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  test("raw HTML renders as text, never as elements", () => {
    const { container } = render(<NoteMarkdown body={'<img src=x onerror="alert(1)"> <script>alert(1)</script>'} />);
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    expect(container.textContent).toContain("<script>");
  });

  test("links open in a new tab and javascript: URLs get no href", () => {
    render(<NoteMarkdown body={"[ok](https://example.com) [bad](javascript:alert(1))"} />);
    const ok = screen.getByRole("link", { name: "ok" });
    expect(ok).toHaveAttribute("target", "_blank");
    expect(ok).toHaveAttribute("rel", "noopener noreferrer");
    const bad = screen.getByText("bad").closest("a");
    expect(bad?.getAttribute("href") ?? "").not.toMatch(/^javascript:/i);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- tests/NoteMarkdown.test.tsx
```

Expected: FAIL, module not found.

- [ ] **Step 3: Write the component**

`portal/src/components/notes/NoteMarkdown.tsx`:

```tsx
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Light-surface markdown for note bodies. Deliberately NO rehype-raw: raw
 * HTML in a body is shown as text. react-markdown's default urlTransform
 * already drops javascript: and data: hrefs; links are forced into a new tab.
 * MapleMarkdown and ChangeLogPanel are the dark-on-brand variants and stay
 * separate.
 */
const components: Components = {
  h1: ({ children }) => <h1 className="text-base font-semibold text-gray-900 mt-3 mb-1 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-sm font-semibold text-gray-900 mt-3 mb-1 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-semibold text-gray-900 mt-2 mb-1 first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="text-sm text-gray-800 my-1.5 leading-relaxed first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="list-disc pl-5 my-1.5 text-sm text-gray-800 space-y-0.5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal pl-5 my-1.5 text-sm text-gray-800 space-y-0.5">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-700 hover:underline break-words">
      {children}
    </a>
  ),
  code: ({ children }) => <code className="rounded bg-gray-100 px-1 py-0.5 text-[0.85em]">{children}</code>,
  pre: ({ children }) => <pre className="my-2 overflow-x-auto rounded bg-gray-100 p-2 text-xs">{children}</pre>,
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-gray-300 pl-3 text-gray-600">{children}</blockquote>
  ),
  hr: () => <hr className="my-3 border-gray-200" />,
  input: (props) => <input {...props} disabled className="mr-1 align-middle" />,
};

export function NoteMarkdown({ body }: { body: string }) {
  return (
    <div className="note-markdown break-words">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {body}
      </ReactMarkdown>
    </div>
  );
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/NoteMarkdown.test.tsx && npm run typecheck
```

Expected: 3 passed.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/notes/NoteMarkdown.tsx tests/NoteMarkdown.test.tsx
git commit -m "feat: safe light-surface markdown renderer for notes

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: `ConfirmDialog` (one shared confirm modal)

**Files:**
- Create: `portal/src/components/common/ConfirmDialog.tsx`
- Test: `portal/tests/ConfirmDialog.test.tsx` (new)

**Interfaces:**
- Produces: `<ConfirmDialog open title message confirmLabel? isBusy? onConfirm onCancel />`. The ten existing open-coded delete modals are **not** migrated here (out of scope).

- [ ] **Step 1: Write the failing test**

`portal/tests/ConfirmDialog.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConfirmDialog } from "../src/components/common/ConfirmDialog";

afterEach(cleanup);

describe("ConfirmDialog", () => {
  test("renders nothing when closed, confirms and cancels when open", async () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    const { rerender } = render(
      <ConfirmDialog open={false} title="Delete note" message="Sure?" onConfirm={onConfirm} onCancel={onCancel} />,
    );
    expect(screen.queryByRole("dialog")).toBeNull();

    rerender(<ConfirmDialog open title="Delete note" message="Sure?" onConfirm={onConfirm} onCancel={onCancel} />);
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  test("disables both buttons while busy", () => {
    render(<ConfirmDialog open isBusy title="t" message="m" onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Deleting..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/ConfirmDialog.test.tsx
```

- [ ] **Step 3: Write the component**

`portal/src/components/common/ConfirmDialog.tsx` (mirrors the open-coded pattern in `ContactsPage.tsx:1108-1150`):

```tsx
import type { ReactNode } from "react";
import { Modal } from "./Modal";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  /** Defaults to "Delete" / "Deleting..." — the only use so far is destructive. */
  confirmLabel?: string;
  busyLabel?: string;
  isBusy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open, title, message, confirmLabel = "Delete", busyLabel = "Deleting...", isBusy = false, onConfirm, onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={() => !isBusy && onCancel()}
      maxWidth="max-w-md"
      footer={
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onCancel} disabled={isBusy}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-60">
            Cancel
          </button>
          <button type="button" onClick={onConfirm} disabled={isBusy}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-60">
            {isBusy ? busyLabel : confirmLabel}
          </button>
        </div>
      }
    >
      <p className="text-sm text-gray-600">{message}</p>
    </Modal>
  );
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/ConfirmDialog.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/common/ConfirmDialog.tsx tests/ConfirmDialog.test.tsx
git commit -m "feat: shared ConfirmDialog

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: `useNotes` hook

**Files:**
- Create: `portal/src/hooks/useNotes.ts`
- Test: `portal/tests/useNotes.test.tsx` (new)

**Interfaces:**
- Consumes: `notesApi` (Task 10), `downscaleImage` (`lib/downscaleImage.ts`), `isVideo`/`isPdf` (`lib/media.ts`).
- Produces:

```ts
export interface UseNotesArgs { parentType: NoteParentType; parentId: string; workItemId?: string; enabled?: boolean }
export interface UseNotesResult {
  notes: Note[];
  isLoading: boolean;
  error: string;
  reload: () => Promise<void>;
  /** Creates the note, then uploads each file in order; returns the files that failed. */
  createNote: (body: string, files: File[]) => Promise<{ note: Note; failedFiles: File[] }>;
  updateNote: (id: string, body: string) => Promise<void>;
  deleteNote: (id: string) => Promise<void>;
  addAttachment: (id: string, file: File) => Promise<void>;
  removeAttachment: (id: string, attachmentId: string) => Promise<void>;
}
export function useNotes(args: UseNotesArgs): UseNotesResult
```

- [ ] **Step 1: Write the failing test**

`portal/tests/useNotes.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import type { Note } from "../src/types/api";

const list = vi.fn();
const create = vi.fn();
const update = vi.fn();
const remove = vi.fn();
const uploadAttachment = vi.fn();
const removeAttachment = vi.fn();

vi.mock("../src/api/notes", () => ({
  notesApi: {
    list: (...a: unknown[]) => list(...a),
    create: (...a: unknown[]) => create(...a),
    update: (...a: unknown[]) => update(...a),
    remove: (...a: unknown[]) => remove(...a),
    uploadAttachment: (...a: unknown[]) => uploadAttachment(...a),
    removeAttachment: (...a: unknown[]) => removeAttachment(...a),
  },
}));
vi.mock("../src/lib/downscaleImage", () => ({ downscaleImage: async (f: File) => f }));

import { useNotes } from "../src/hooks/useNotes";

const note = (id: string, body = "b"): Note => ({
  _id: id, parent_type: "property", parent_id: "p1", body, attachments: [],
  created_by_email: "a@x.com", created_by_name: "A",
  created_at: "2026-09-17T00:00:00+00:00", updated_at: "2026-09-17T00:00:00+00:00",
});

beforeEach(() => {
  list.mockReset(); create.mockReset(); update.mockReset(); remove.mockReset();
  uploadAttachment.mockReset(); removeAttachment.mockReset();
});
afterEach(() => vi.clearAllMocks());

describe("useNotes", () => {
  test("loads under StrictMode exactly once per args and exposes the list", async () => {
    list.mockResolvedValue([note("n1")]);
    const { result } = renderHook(() => useNotes({ parentType: "property", parentId: "p1" }), { wrapper: StrictMode });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.notes.map((n) => n._id)).toEqual(["n1"]);
    // StrictMode double-invokes the effect; the second run must be the one that lands.
    expect(result.current.error).toBe("");
  });

  test("does nothing while disabled", async () => {
    const { result } = renderHook(() => useNotes({ parentType: "property", parentId: "p1", enabled: false }));
    await act(async () => {});
    expect(list).not.toHaveBeenCalled();
    expect(result.current.notes).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  test("createNote prepends, uploads files in order, and reports failures", async () => {
    list.mockResolvedValue([note("n1")]);
    create.mockResolvedValue(note("n2", "new"));
    const good = new File(["%PDF-"], "a.pdf", { type: "application/pdf" });
    const bad = new File(["x"], "b.pdf", { type: "application/pdf" });
    uploadAttachment
      .mockResolvedValueOnce({ ...note("n2", "new"), attachments: [{ file_id: "f1", kind: "pdf", filename: "a.pdf", content_type: "application/pdf", size_bytes: 5 }] })
      .mockRejectedValueOnce(new Error("offline"));

    const { result } = renderHook(() => useNotes({ parentType: "property", parentId: "p1" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    let outcome!: { failedFiles: File[] };
    await act(async () => { outcome = await result.current.createNote("new", [good, bad]); });
    expect(create).toHaveBeenCalledWith({ parent_type: "property", parent_id: "p1", body: "new" });
    expect(outcome.failedFiles).toEqual([bad]);
    expect(result.current.notes.map((n) => n._id)).toEqual(["n2", "n1"]);
    expect(result.current.notes[0].attachments).toHaveLength(1);
  });

  test("updateNote and deleteNote patch the list in place", async () => {
    list.mockResolvedValue([note("n1"), note("n2")]);
    update.mockResolvedValue(note("n1", "edited"));
    remove.mockResolvedValue({ message: "ok" });
    const { result } = renderHook(() => useNotes({ parentType: "property", parentId: "p1" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => { await result.current.updateNote("n1", "edited"); });
    expect(result.current.notes[0].body).toBe("edited");
    await act(async () => { await result.current.deleteNote("n2"); });
    expect(result.current.notes.map((n) => n._id)).toEqual(["n1"]);
  });

  test("surfaces a load error", async () => {
    list.mockRejectedValue(new Error("boom"));
    const { result } = renderHook(() => useNotes({ parentType: "property", parentId: "p1" }));
    await waitFor(() => expect(result.current.error).toBe("boom"));
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/useNotes.test.tsx
```

- [ ] **Step 3: Write the hook**

`portal/src/hooks/useNotes.ts`:

```ts
import { useCallback, useEffect, useRef, useState } from "react";
import { notesApi } from "../api/notes";
import { getEntityId } from "../api/client";
import { downscaleImage } from "../lib/downscaleImage";
import { isPdf, isVideo } from "../lib/media";
import type { Note, NoteParentType } from "../types/api";

export interface UseNotesArgs {
  parentType: NoteParentType;
  parentId: string;
  workItemId?: string;
  /** False skips the fetch entirely (unsaved work item, panel collapsed, …). */
  enabled?: boolean;
}

export interface UseNotesResult {
  notes: Note[];
  isLoading: boolean;
  error: string;
  reload: () => Promise<void>;
  createNote: (body: string, files: File[]) => Promise<{ note: Note; failedFiles: File[] }>;
  updateNote: (id: string, body: string) => Promise<void>;
  deleteNote: (id: string) => Promise<void>;
  addAttachment: (id: string, file: File) => Promise<void>;
  removeAttachment: (id: string, attachmentId: string) => Promise<void>;
}

/** Videos and PDFs upload as-is; downscaleImage is an image (canvas) pipeline. */
async function prepareUpload(file: File): Promise<File> {
  return isVideo(file.type) || isPdf(file.type) ? file : downscaleImage(file);
}

export function useNotes({ parentType, parentId, workItemId, enabled = true }: UseNotesArgs): UseNotesResult {
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(enabled);
  const [error, setError] = useState("");
  // Re-armed inside the effect body, not only in cleanup: StrictMode runs
  // cleanup then the body again, and a flag left false would drop the
  // second (real) response. See feedback_strictmode_navigate.
  const aliveRef = useRef(true);

  const load = useCallback(async () => {
    if (!enabled) return;
    setIsLoading(true);
    setError("");
    try {
      const data = await notesApi.list({ parentType, parentId, workItemId });
      // Page tests stub apiRequest to resolve `{}`; never let a non-array reach .map.
      if (aliveRef.current) setNotes(Array.isArray(data) ? data : []);
    } catch (err) {
      if (aliveRef.current) setError((err as Error).message || "Failed to load notes.");
    } finally {
      if (aliveRef.current) setIsLoading(false);
    }
  }, [enabled, parentType, parentId, workItemId]);

  useEffect(() => {
    aliveRef.current = true;
    if (!enabled) {
      setNotes([]);
      setIsLoading(false);
      return;
    }
    void load();
    return () => {
      aliveRef.current = false;
    };
  }, [enabled, load]);

  const replace = (updated: Note | null) => {
    if (!updated) return;
    const id = getEntityId(updated);
    setNotes((previous) => previous.map((n) => (getEntityId(n) === id ? updated : n)));
  };

  const createNote = useCallback(
    async (body: string, files: File[]) => {
      const created = await notesApi.create({
        parent_type: parentType,
        parent_id: parentId,
        ...(parentType === "work_item" && workItemId ? { work_item_id: workItemId } : {}),
        body,
      });
      if (!created) throw new Error("Failed to create the note.");
      let latest: Note = created;
      const failedFiles: File[] = [];
      for (let index = 0; index < files.length; index += 1) {
        try {
          const updated = await notesApi.uploadAttachment(getEntityId(created), await prepareUpload(files[index]));
          if (updated) latest = updated;
        } catch {
          // The connection is likely down; keep the rest for the retry.
          failedFiles.push(...files.slice(index));
          break;
        }
      }
      if (aliveRef.current) setNotes((previous) => [latest, ...previous]);
      return { note: latest, failedFiles };
    },
    [parentType, parentId, workItemId],
  );

  const updateNote = useCallback(async (id: string, body: string) => {
    replace(await notesApi.update(id, body));
  }, []);

  const deleteNote = useCallback(async (id: string) => {
    await notesApi.remove(id);
    if (aliveRef.current) setNotes((previous) => previous.filter((n) => getEntityId(n) !== id));
  }, []);

  const addAttachment = useCallback(async (id: string, file: File) => {
    replace(await notesApi.uploadAttachment(id, await prepareUpload(file)));
  }, []);

  const removeAttachment = useCallback(async (id: string, attachmentId: string) => {
    replace(await notesApi.removeAttachment(id, attachmentId));
  }, []);

  return { notes, isLoading, error, reload: load, createNote, updateNote, deleteNote, addAttachment, removeAttachment };
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/useNotes.test.tsx && npm run typecheck
```

Expected: 5 passed.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/hooks/useNotes.ts tests/useNotes.test.tsx
git commit -m "feat: useNotes hook

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 14: `NoteAttachmentStrip` — tiles, viewer, and the add/remove controls

**Files:**
- Create: `portal/src/components/notes/NoteAttachmentStrip.tsx`
- Test: `portal/tests/NoteAttachmentStrip.test.tsx` (new)

**Interfaces:**
- Consumes: `notesApi.attachmentBlob` (Task 10), `NOTE_ATTACHMENT_ACCEPT`, `isVideo`, `isPdf`.
- Produces:

```ts
interface NoteAttachmentStripProps {
  noteId: string;
  attachments: NoteAttachment[];
  /** Author only: shows the Photo / Attach buttons and per-tile remove. */
  canManage: boolean;
  onAdd: (files: FileList | null) => void;
  onRemove: (attachmentId: string) => void;
  isUploading?: boolean;
  removingId?: string;
  error?: string;
}
export function NoteAttachmentStrip(props: NoteAttachmentStripProps): JSX.Element | null
```

- [ ] **Step 1: Write the failing test**

`portal/tests/NoteAttachmentStrip.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { NoteAttachment } from "../src/types/api";

const attachmentBlob = vi.fn();
vi.mock("../src/api/notes", () => ({ notesApi: { attachmentBlob: (...a: unknown[]) => attachmentBlob(...a) } }));

import { NoteAttachmentStrip } from "../src/components/notes/NoteAttachmentStrip";

const image: NoteAttachment = { file_id: "i1", thumb_file_id: "t1", kind: "image", filename: "site.jpg", content_type: "image/jpeg", size_bytes: 10 };
const video: NoteAttachment = { file_id: "v1", kind: "video", filename: "walk.mp4", content_type: "video/mp4", size_bytes: 10 };
const pdf: NoteAttachment = { file_id: "p1", kind: "pdf", filename: "gate.pdf", content_type: "application/pdf", size_bytes: 2048 };

beforeEach(() => {
  attachmentBlob.mockReset().mockResolvedValue(new Blob(["x"]));
  globalThis.URL.createObjectURL = vi.fn(() => "blob:mock");
  globalThis.URL.revokeObjectURL = vi.fn();
});
afterEach(cleanup);

describe("NoteAttachmentStrip", () => {
  test("renders one tile per attachment, fetching thumbs only for images", async () => {
    render(<NoteAttachmentStrip noteId="n1" attachments={[image, video, pdf]} canManage={false} onAdd={vi.fn()} onRemove={vi.fn()} />);
    expect(screen.getByRole("button", { name: /open photo site\.jpg/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /open video walk\.mp4/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /open pdf gate\.pdf/i })).toBeInTheDocument();
    await waitFor(() => expect(attachmentBlob).toHaveBeenCalledWith("n1", "i1", "thumb"));
    expect(attachmentBlob).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: /remove/i })).toBeNull();
  });

  test("author sees add buttons and can remove a tile", async () => {
    const onRemove = vi.fn();
    const onAdd = vi.fn();
    render(<NoteAttachmentStrip noteId="n1" attachments={[pdf]} canManage onAdd={onAdd} onRemove={onRemove} />);
    await userEvent.click(screen.getByRole("button", { name: /remove gate\.pdf/i }));
    expect(onRemove).toHaveBeenCalledWith("p1");
    expect(screen.getByRole("button", { name: "Photo" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attach" })).toBeInTheDocument();
    const input = screen.getByTestId("note-attach-input") as HTMLInputElement;
    expect(input.accept).toContain("application/pdf");
  });

  test("renders nothing at all for a read-only note with no attachments", () => {
    const { container } = render(<NoteAttachmentStrip noteId="n1" attachments={[]} canManage={false} onAdd={vi.fn()} onRemove={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/NoteAttachmentStrip.test.tsx
```

- [ ] **Step 3: Write the component**

`portal/src/components/notes/NoteAttachmentStrip.tsx`:

```tsx
import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, FileText, Loader2, Paperclip, Trash2, Video, X } from "lucide-react";
import { notesApi } from "../../api/notes";
import { NOTE_ATTACHMENT_ACCEPT, isPdf, isVideo } from "../../lib/media";
import type { NoteAttachment } from "../../types/api";

/** Fetches an attachment blob through the authed API and exposes an object URL. */
function useAttachmentObjectUrl(noteId: string, attachmentId: string | undefined, size: "thumb" | "full") {
  const [objectUrl, setObjectUrl] = useState("");
  useEffect(() => {
    if (!attachmentId) return;
    let alive = true;
    let url = "";
    notesApi
      .attachmentBlob(noteId, attachmentId, size)
      .then((blob) => {
        url = URL.createObjectURL(blob);
        if (alive) setObjectUrl(url);
        else URL.revokeObjectURL(url);
      })
      .catch(() => {
        // Leave the placeholder; the tile is still listed and removable.
      });
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
      setObjectUrl("");
    };
  }, [noteId, attachmentId, size]);
  return objectUrl;
}

function kindLabel(attachment: NoteAttachment): "photo" | "video" | "PDF" {
  if (isVideo(attachment.content_type)) return "video";
  if (isPdf(attachment.content_type)) return "PDF";
  return "photo";
}

function Tile({ noteId, attachment, canManage, isRemoving, onOpen, onRemove }: {
  noteId: string; attachment: NoteAttachment; canManage: boolean; isRemoving: boolean;
  onOpen: () => void; onRemove: () => void;
}) {
  const label = kindLabel(attachment);
  const thumbUrl = useAttachmentObjectUrl(noteId, label === "photo" ? attachment.file_id : undefined, "thumb");
  return (
    <div className="relative group">
      <button type="button" onClick={onOpen} aria-label={`Open ${label} ${attachment.filename}`}
        className="block w-full aspect-square rounded-lg overflow-hidden bg-gray-100 border border-gray-200">
        {label === "video" ? (
          <span className="flex flex-col items-center justify-center gap-1 w-full h-full bg-gray-800 text-white px-1">
            <Video className="w-6 h-6" />
            <span className="text-[10px] leading-tight truncate max-w-full">{attachment.filename}</span>
          </span>
        ) : label === "PDF" ? (
          <span className="flex flex-col items-center justify-center gap-1 w-full h-full bg-red-50 text-red-800 px-1">
            <FileText className="w-6 h-6" />
            <span className="text-[10px] leading-tight truncate max-w-full">{attachment.filename}</span>
          </span>
        ) : thumbUrl ? (
          <img src={thumbUrl} alt={attachment.filename} className="w-full h-full object-cover" />
        ) : (
          <span className="flex items-center justify-center w-full h-full text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </span>
        )}
      </button>
      {canManage && (
        <button type="button" aria-label={`Remove ${attachment.filename}`} onClick={onRemove} disabled={isRemoving}
          className="absolute top-1.5 right-1.5 p-1.5 rounded-full bg-black/55 text-white hover:bg-black/75 disabled:opacity-50">
          {isRemoving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
        </button>
      )}
    </div>
  );
}

function Viewer({ noteId, attachment, onClose }: { noteId: string; attachment: NoteAttachment; onClose: () => void }) {
  const fullUrl = useAttachmentObjectUrl(noteId, attachment.file_id, "full");
  const label = kindLabel(attachment);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);
  // PDFs open in a new tab as soon as their bytes arrive; nothing to render here.
  useEffect(() => {
    if (label === "PDF" && fullUrl) {
      window.open(fullUrl, "_blank", "noopener");
      onClose();
    }
  }, [label, fullUrl, onClose]);
  if (label === "PDF") return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4" onClick={onClose}
      role="dialog" aria-label={`${label} ${attachment.filename}`}>
      <button type="button" aria-label="Close" onClick={onClose}
        className="absolute top-4 left-4 z-10 p-2 rounded-full bg-black/60 text-white ring-1 ring-white/40 hover:bg-black/80">
        <X className="w-5 h-5" />
      </button>
      {!fullUrl ? (
        <Loader2 className="w-8 h-8 text-white animate-spin" />
      ) : label === "video" ? (
        <video src={fullUrl} controls playsInline className="max-w-full max-h-full rounded-lg" onClick={(e) => e.stopPropagation()} />
      ) : (
        <img src={fullUrl} alt={attachment.filename} className="max-w-full max-h-full object-contain rounded-lg" onClick={(e) => e.stopPropagation()} />
      )}
    </div>
  );
}

export interface NoteAttachmentStripProps {
  noteId: string;
  attachments: NoteAttachment[];
  canManage: boolean;
  onAdd: (files: FileList | null) => void;
  onRemove: (attachmentId: string) => void;
  isUploading?: boolean;
  removingId?: string;
  error?: string;
}

export function NoteAttachmentStrip({
  noteId, attachments, canManage, onAdd, onRemove, isUploading = false, removingId = "", error = "",
}: NoteAttachmentStripProps) {
  const [open, setOpen] = useState<NoteAttachment | null>(null);
  const photoInputRef = useRef<HTMLInputElement>(null);
  const attachInputRef = useRef<HTMLInputElement>(null);
  const closeViewer = useCallback(() => setOpen(null), []);

  if (!canManage && attachments.length === 0) return null;

  const handleFiles = (files: FileList | null) => {
    onAdd(files);
    if (photoInputRef.current) photoInputRef.current.value = "";
    if (attachInputRef.current) attachInputRef.current.value = "";
  };

  return (
    <div className="space-y-2">
      {attachments.length > 0 && (
        <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
          {attachments.map((attachment) => (
            <Tile key={attachment.file_id} noteId={noteId} attachment={attachment} canManage={canManage}
              isRemoving={removingId === attachment.file_id} onOpen={() => setOpen(attachment)}
              onRemove={() => onRemove(attachment.file_id)} />
          ))}
        </div>
      )}
      {canManage && (
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => photoInputRef.current?.click()} disabled={isUploading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-60">
            {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5" />}
            {isUploading ? "Uploading..." : "Photo"}
          </button>
          <input ref={photoInputRef} data-testid="note-photo-input" type="file" accept="image/*" capture="environment" multiple
            onChange={(e) => handleFiles(e.target.files)} className="hidden" />
          <button type="button" onClick={() => attachInputRef.current?.click()} disabled={isUploading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-60">
            <Paperclip className="w-3.5 h-3.5" />
            Attach
          </button>
          {/* No `capture`: videos and PDFs come from the library, and iOS
              capture mode would block library picks and ignore `multiple`. */}
          <input ref={attachInputRef} data-testid="note-attach-input" type="file" accept={NOTE_ATTACHMENT_ACCEPT} multiple
            onChange={(e) => handleFiles(e.target.files)} className="hidden" />
          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>
      )}
      {open && <Viewer noteId={noteId} attachment={open} onClose={closeViewer} />}
    </div>
  );
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/NoteAttachmentStrip.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/notes/NoteAttachmentStrip.tsx tests/NoteAttachmentStrip.test.tsx
git commit -m "feat: note attachment tiles, viewer and add/remove controls

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 15: `NoteComposer` — markdown editor with staged files (create) or plain edit

**Files:**
- Create: `portal/src/components/notes/NoteComposer.tsx`
- Test: `portal/tests/NoteComposer.test.tsx` (new)

**Interfaces:**
- Consumes: `MarkdownDescriptionEditor` (`common/MarkdownDescriptionEditor.tsx`), `attachmentSizeError`, `NOTE_ATTACHMENT_ACCEPT`.
- Produces:

```ts
interface NoteComposerProps {
  mode: "create" | "edit";
  initialBody?: string;
  /** Resolves with the files that failed to upload (create mode); [] on full success. */
  onSubmit: (body: string, files: File[]) => Promise<File[]>;
  onCancel: () => void;
  autoFocus?: boolean;
}
export function NoteComposer(props: NoteComposerProps): JSX.Element
```

- [ ] **Step 1: Write the failing test**

`portal/tests/NoteComposer.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// MDXEditor is heavy and contenteditable-based; a textarea stand-in keeps the
// composer's own logic testable. WorkItemInlineContent.test.tsx covers the real editor.
vi.mock("../src/components/common/MarkdownDescriptionEditor", () => ({
  default: ({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) => (
    <textarea aria-label="Note body" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
  ),
}));

import { NoteComposer } from "../src/components/notes/NoteComposer";

beforeEach(() => {
  globalThis.URL.createObjectURL = vi.fn(() => "blob:mock");
  globalThis.URL.revokeObjectURL = vi.fn();
});
afterEach(cleanup);

describe("NoteComposer", () => {
  test("create: Save is disabled until there is text, submits body and staged files, clears on success", async () => {
    const onSubmit = vi.fn().mockResolvedValue([]);
    render(<NoteComposer mode="create" onSubmit={onSubmit} onCancel={vi.fn()} />);
    const save = screen.getByRole("button", { name: "Save note" });
    expect(save).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Note body"), "Gate code 4411");
    const pdf = new File(["%PDF-"], "gate.pdf", { type: "application/pdf" });
    await userEvent.upload(screen.getByTestId("note-composer-attach-input"), pdf);
    expect(screen.getByText("gate.pdf")).toBeInTheDocument();
    await userEvent.click(save);
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("Gate code 4411", [pdf]));
    await waitFor(() => expect((screen.getByLabelText("Note body") as HTMLTextAreaElement).value).toBe(""));
  });

  test("create: failed uploads stay staged with a retry message", async () => {
    const bad = new File(["x"], "walk.mp4", { type: "video/mp4" });
    const onSubmit = vi.fn().mockResolvedValue([bad]);
    render(<NoteComposer mode="create" onSubmit={onSubmit} onCancel={vi.fn()} />);
    await userEvent.type(screen.getByLabelText("Note body"), "text");
    await userEvent.upload(screen.getByTestId("note-composer-attach-input"), bad);
    await userEvent.click(screen.getByRole("button", { name: "Save note" }));
    await waitFor(() => expect(screen.getByText(/failed to upload/i)).toBeInTheDocument());
    expect(screen.getByText("walk.mp4")).toBeInTheDocument();
  });

  test("rejects an oversize file locally", async () => {
    render(<NoteComposer mode="create" onSubmit={vi.fn()} onCancel={vi.fn()} />);
    const huge = new File([new Uint8Array(1)], "huge.pdf", { type: "application/pdf" });
    Object.defineProperty(huge, "size", { value: 11 * 1024 * 1024 });
    await userEvent.upload(screen.getByTestId("note-composer-attach-input"), huge);
    expect(screen.getByText(/limited to 10MB/)).toBeInTheDocument();
    expect(screen.queryByText("huge.pdf")).toBeNull();
  });

  test("edit: starts with the body, has no file controls, cancel restores nothing", async () => {
    const onSubmit = vi.fn().mockResolvedValue([]);
    const onCancel = vi.fn();
    render(<NoteComposer mode="edit" initialBody="old text" onSubmit={onSubmit} onCancel={onCancel} />);
    expect((screen.getByLabelText("Note body") as HTMLTextAreaElement).value).toBe("old text");
    expect(screen.queryByTestId("note-composer-attach-input")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/NoteComposer.test.tsx
```

- [ ] **Step 3: Write the component**

`portal/src/components/notes/NoteComposer.tsx`:

```tsx
import { useEffect, useRef, useState } from "react";
import { Camera, FileText, Loader2, Paperclip, Video, X } from "lucide-react";
import MarkdownDescriptionEditor from "../common/MarkdownDescriptionEditor";
import { NOTE_ATTACHMENT_ACCEPT, attachmentSizeError, isPdf, isVideo } from "../../lib/media";

interface StagedFile {
  file: File;
  previewUrl: string;
}

export interface NoteComposerProps {
  mode: "create" | "edit";
  initialBody?: string;
  onSubmit: (body: string, files: File[]) => Promise<File[]>;
  onCancel: () => void;
  autoFocus?: boolean;
}

/**
 * Write or edit one note. Notes persist on their own endpoints the moment
 * Save is pressed — whatever dialog hosts this composer cannot undo it.
 * Create mode stages files and hands them to onSubmit after the note
 * exists (the Task create-mode pattern); edit mode manages attachments on
 * the card's strip instead, so it has no file controls.
 */
export function NoteComposer({ mode, initialBody = "", onSubmit, onCancel, autoFocus = false }: NoteComposerProps) {
  const [body, setBody] = useState(initialBody);
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const photoInputRef = useRef<HTMLInputElement>(null);
  const attachInputRef = useRef<HTMLInputElement>(null);

  // Cancel/unmount must not leak preview object URLs.
  const stagedRef = useRef<StagedFile[]>([]);
  useEffect(() => {
    stagedRef.current = staged;
  }, [staged]);
  useEffect(() => () => stagedRef.current.forEach((s) => URL.revokeObjectURL(s.previewUrl)), []);

  const stage = (files: FileList | null) => {
    if (!files) return;
    const additions: StagedFile[] = [];
    for (const file of Array.from(files)) {
      const sizeError = attachmentSizeError(file);
      if (sizeError) {
        setError(sizeError);
        continue;
      }
      additions.push({ file, previewUrl: URL.createObjectURL(file) });
    }
    setStaged((previous) => [...previous, ...additions]);
    if (photoInputRef.current) photoInputRef.current.value = "";
    if (attachInputRef.current) attachInputRef.current.value = "";
  };

  const unstage = (target: StagedFile) => {
    URL.revokeObjectURL(target.previewUrl);
    setStaged((previous) => previous.filter((s) => s.previewUrl !== target.previewUrl));
  };

  const canSave = body.trim().length > 0 && !isSubmitting;

  const submit = async () => {
    if (!canSave) return;
    setIsSubmitting(true);
    setError("");
    try {
      const failed = await onSubmit(body.trim(), staged.map((s) => s.file));
      const failedSet = new Set(failed);
      const remaining = staged.filter((s) => failedSet.has(s.file));
      staged.filter((s) => !failedSet.has(s.file)).forEach((s) => URL.revokeObjectURL(s.previewUrl));
      setStaged(remaining);
      if (remaining.length > 0) {
        setError(
          `The note was saved, but ${remaining.length} ${remaining.length === 1 ? "file" : "files"} failed to upload. ` +
            "Check your connection and save again to retry.",
        );
        return;
      }
      if (mode === "create") setBody("");
    } catch (err) {
      setError((err as Error).message || "Failed to save the note.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 space-y-3" data-testid="note-composer">
      <MarkdownDescriptionEditor
        value={body}
        onChange={setBody}
        placeholder="Write a note... markdown is supported"
        minHeight={96}
        autoFocus={autoFocus}
        hideToolbarUntilFocus
      />

      {mode === "create" && (
        <>
          {staged.length > 0 && (
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
              {staged.map((item) => (
                <div key={item.previewUrl} className="relative">
                  {isVideo(item.file.type) ? (
                    <span className="flex flex-col items-center justify-center gap-1 w-full aspect-square rounded-lg bg-gray-800 text-white border border-gray-200 px-1">
                      <Video className="w-6 h-6" />
                      <span className="text-[10px] leading-tight truncate max-w-full">{item.file.name}</span>
                    </span>
                  ) : isPdf(item.file.type) ? (
                    <span className="flex flex-col items-center justify-center gap-1 w-full aspect-square rounded-lg bg-red-50 text-red-800 border border-gray-200 px-1">
                      <FileText className="w-6 h-6" />
                      <span className="text-[10px] leading-tight truncate max-w-full">{item.file.name}</span>
                    </span>
                  ) : (
                    <img src={item.previewUrl} alt={item.file.name} className="w-full aspect-square rounded-lg object-cover border border-gray-200" />
                  )}
                  <button type="button" aria-label={`Remove ${item.file.name}`} onClick={() => unstage(item)} disabled={isSubmitting}
                    className="absolute -top-1.5 -right-1.5 p-1 rounded-full bg-gray-800 text-white hover:bg-gray-900">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => photoInputRef.current?.click()} disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-60">
              <Camera className="w-3.5 h-3.5" /> Photo
            </button>
            <input ref={photoInputRef} data-testid="note-composer-photo-input" type="file" accept="image/*" capture="environment" multiple
              onChange={(e) => stage(e.target.files)} className="hidden" />
            <button type="button" onClick={() => attachInputRef.current?.click()} disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-60">
              <Paperclip className="w-3.5 h-3.5" /> Attach
            </button>
            <input ref={attachInputRef} data-testid="note-composer-attach-input" type="file" accept={NOTE_ATTACHMENT_ACCEPT} multiple
              onChange={(e) => stage(e.target.files)} className="hidden" />
          </div>
        </>
      )}

      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-red-600 min-h-4">{error}</p>
        <div className="flex gap-2 shrink-0">
          <button type="button" onClick={onCancel} disabled={isSubmitting}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-60">
            Cancel
          </button>
          <button type="button" onClick={() => void submit()} disabled={!canSave}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-brand text-white rounded-lg hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed">
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            {mode === "create" ? "Save note" : "Save changes"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/NoteComposer.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/notes/NoteComposer.tsx tests/NoteComposer.test.tsx
git commit -m "feat: note composer with staged attachments

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 16: `NoteCard`

**Files:**
- Create: `portal/src/components/notes/NoteCard.tsx`
- Test: `portal/tests/NoteCard.test.tsx` (new)

**Interfaces:**
- Consumes: `NoteMarkdown`, `NoteComposer`, `NoteAttachmentStrip`, `ConfirmDialog`, `formatNoteDate`, `isNoteEdited`.
- Produces:

```ts
interface NoteCardProps {
  note: Note;
  canEdit: boolean;
  canDelete: boolean;
  onUpdate: (body: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onAddAttachment: (file: File) => Promise<void>;
  onRemoveAttachment: (attachmentId: string) => Promise<void>;
}
export function NoteCard(props: NoteCardProps): JSX.Element
```

- [ ] **Step 1: Write the failing test**

`portal/tests/NoteCard.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Note } from "../src/types/api";

vi.mock("../src/components/common/MarkdownDescriptionEditor", () => ({
  default: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="Note body" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock("../src/api/notes", () => ({ notesApi: { attachmentBlob: vi.fn().mockResolvedValue(new Blob()) } }));

import { NoteCard } from "../src/components/notes/NoteCard";

const note: Note = {
  _id: "n1", parent_type: "property", parent_id: "p1", body: "East bed **first**", attachments: [],
  created_by_email: "ana@x.com", created_by_name: "Ana Reyes",
  created_at: "2026-09-17T12:00:00+00:00", updated_at: "2026-09-17T12:30:00+00:00",
};
const handlers = () => ({
  onUpdate: vi.fn().mockResolvedValue(undefined),
  onDelete: vi.fn().mockResolvedValue(undefined),
  onAddAttachment: vi.fn().mockResolvedValue(undefined),
  onRemoveAttachment: vi.fn().mockResolvedValue(undefined),
});

beforeEach(() => {
  globalThis.URL.createObjectURL = vi.fn(() => "blob:mock");
  globalThis.URL.revokeObjectURL = vi.fn();
});
afterEach(cleanup);

describe("NoteCard", () => {
  test("shows author, date, edited marker and rendered markdown; no actions when not permitted", () => {
    render(<NoteCard note={note} canEdit={false} canDelete={false} {...handlers()} />);
    expect(screen.getByText("Ana Reyes")).toBeInTheDocument();
    expect(screen.getByText(/Sep 1[78], 2026/)).toBeInTheDocument();
    expect(screen.getByText("edited")).toBeInTheDocument();
    expect(screen.getByText("first").tagName).toBe("STRONG");
    expect(screen.queryByRole("button", { name: "Edit note" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete note" })).toBeNull();
  });

  test("edit flow: pencil opens the composer, saving calls onUpdate", async () => {
    const h = handlers();
    render(<NoteCard note={note} canEdit canDelete {...h} />);
    await userEvent.click(screen.getByRole("button", { name: "Edit note" }));
    const box = screen.getByLabelText("Note body");
    await userEvent.clear(box);
    await userEvent.type(box, "West bed first");
    await userEvent.click(screen.getByRole("button", { name: "Save changes" }));
    await waitFor(() => expect(h.onUpdate).toHaveBeenCalledWith("West bed first"));
    await waitFor(() => expect(screen.queryByLabelText("Note body")).toBeNull());
  });

  test("delete flow: trash asks for confirmation, then calls onDelete", async () => {
    const h = handlers();
    render(<NoteCard note={note} canEdit={false} canDelete {...h} />);
    await userEvent.click(screen.getByRole("button", { name: "Delete note" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(h.onDelete).toHaveBeenCalledTimes(1));
  });

  test("Owner who is not the author sees delete but not edit", () => {
    render(<NoteCard note={note} canEdit={false} canDelete {...handlers()} />);
    expect(screen.queryByRole("button", { name: "Edit note" })).toBeNull();
    expect(screen.getByRole("button", { name: "Delete note" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/NoteCard.test.tsx
```

- [ ] **Step 3: Write the component**

`portal/src/components/notes/NoteCard.tsx`:

```tsx
import { useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { getEntityId } from "../../api/client";
import { attachmentSizeError } from "../../lib/media";
import { formatNoteDate, isNoteEdited } from "../../lib/noteDisplay";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { NoteAttachmentStrip } from "./NoteAttachmentStrip";
import { NoteComposer } from "./NoteComposer";
import { NoteMarkdown } from "./NoteMarkdown";
import type { Note } from "../../types/api";

export interface NoteCardProps {
  note: Note;
  canEdit: boolean;
  canDelete: boolean;
  onUpdate: (body: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onAddAttachment: (file: File) => Promise<void>;
  onRemoveAttachment: (attachmentId: string) => Promise<void>;
}

export function NoteCard({ note, canEdit, canDelete, onUpdate, onDelete, onAddAttachment, onRemoveAttachment }: NoteCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [removingId, setRemovingId] = useState("");
  const [attachmentError, setAttachmentError] = useState("");
  const noteId = getEntityId(note);

  const addFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setAttachmentError("");
    setIsUploading(true);
    try {
      for (const file of Array.from(files)) {
        const sizeError = attachmentSizeError(file);
        if (sizeError) {
          setAttachmentError(sizeError);
          continue;
        }
        await onAddAttachment(file);
      }
    } catch (err) {
      setAttachmentError((err as Error).message || "Failed to upload.");
    } finally {
      setIsUploading(false);
    }
  };

  const removeAttachment = async (attachmentId: string) => {
    setRemovingId(attachmentId);
    setAttachmentError("");
    try {
      await onRemoveAttachment(attachmentId);
    } catch (err) {
      setAttachmentError((err as Error).message || "Failed to remove.");
    } finally {
      setRemovingId("");
    }
  };

  const confirmDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete();
    } finally {
      setIsDeleting(false);
      setConfirmingDelete(false);
    }
  };

  return (
    <article className="rounded-lg border border-gray-200 bg-white p-3 sm:p-4 space-y-3" data-testid="note-card">
      <header className="flex items-start justify-between gap-3">
        <p className="text-xs text-gray-500 min-w-0">
          <span className="font-medium text-gray-700">{note.created_by_name}</span>
          <span aria-hidden="true"> · </span>
          <span>{formatNoteDate(note.created_at)}</span>
          {isNoteEdited(note) && (
            <>
              <span aria-hidden="true"> · </span>
              <span className="italic" title={`Edited ${formatNoteDate(note.updated_at)}`}>edited</span>
            </>
          )}
        </p>
        {(canEdit || canDelete) && !isEditing && (
          <div className="flex items-center gap-1 shrink-0">
            {canEdit && (
              <button type="button" aria-label="Edit note" title="Edit note" onClick={() => setIsEditing(true)}
                className="p-2 -m-1 text-gray-500 hover:text-blue-600 transition-colors">
                <Pencil className="w-4 h-4" />
              </button>
            )}
            {canDelete && (
              <button type="button" aria-label="Delete note" title="Delete note" onClick={() => setConfirmingDelete(true)}
                className="p-2 -m-1 text-gray-500 hover:text-red-600 transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </header>

      {isEditing ? (
        <NoteComposer
          mode="edit"
          initialBody={note.body}
          autoFocus
          onSubmit={async (body) => {
            await onUpdate(body);
            setIsEditing(false);
            return [];
          }}
          onCancel={() => setIsEditing(false)}
        />
      ) : (
        <NoteMarkdown body={note.body} />
      )}

      <NoteAttachmentStrip
        noteId={noteId}
        attachments={note.attachments}
        canManage={canEdit}
        onAdd={(files) => void addFiles(files)}
        onRemove={(id) => void removeAttachment(id)}
        isUploading={isUploading}
        removingId={removingId}
        error={attachmentError}
      />

      <ConfirmDialog
        open={confirmingDelete}
        title="Delete note"
        message="Delete this note and its attachments? This cannot be undone."
        isBusy={isDeleting}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setConfirmingDelete(false)}
      />
    </article>
  );
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/NoteCard.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/notes/NoteCard.tsx tests/NoteCard.test.tsx
git commit -m "feat: NoteCard with edit, delete and attachment management

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 17: `NotesPanel`

**Files:**
- Create: `portal/src/components/notes/NotesPanel.tsx`
- Test: `portal/tests/NotesPanel.test.tsx` (new)

**Interfaces:**
- Consumes: `useNotes`, `NoteCard`, `NoteComposer`, `canEditNote`/`canDeleteNote`, `getCurrentUser` (`api/auth.ts`).
- Produces:

```ts
export interface NotesPanelProps {
  parentType: NoteParentType;
  parentId: string;
  workItemId?: string;
  /** Renders the header and hint only; no fetch, no composer. */
  disabled?: boolean;
  disabledHint?: string;
  /** Tailwind max-height class for the scrolling list (e.g. "max-h-80"). Unbounded when omitted. */
  listMaxHeightClassName?: string;
  /** Called with the current count whenever the list changes. */
  onCountChange?: (count: number) => void;
  /** Hide the built-in header (the work-item section supplies its own). */
  hideHeader?: boolean;
  /** Controlled "composer open" for hosts whose header owns the Add button. */
  composerOpen?: boolean;
  onComposerOpenChange?: (open: boolean) => void;
}
export function NotesPanel(props: NotesPanelProps): JSX.Element
```

- [ ] **Step 1: Write the failing test**

`portal/tests/NotesPanel.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Note } from "../src/types/api";

const list = vi.fn();
const create = vi.fn();
const remove = vi.fn();
vi.mock("../src/api/notes", () => ({
  notesApi: {
    list: (...a: unknown[]) => list(...a), create: (...a: unknown[]) => create(...a),
    update: vi.fn(), remove: (...a: unknown[]) => remove(...a),
    uploadAttachment: vi.fn(), removeAttachment: vi.fn(), attachmentBlob: vi.fn().mockResolvedValue(new Blob()),
  },
}));
const currentUser = vi.fn();
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => currentUser() }));
vi.mock("../src/components/common/MarkdownDescriptionEditor", () => ({
  default: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="Note body" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

import { NotesPanel } from "../src/components/notes/NotesPanel";

const mine: Note = { _id: "n1", parent_type: "property", parent_id: "p1", body: "mine", attachments: [],
  created_by_email: "me@x.com", created_by_name: "Me", created_at: "2026-09-17T00:00:00+00:00", updated_at: "2026-09-17T00:00:00+00:00" };
const theirs: Note = { ...mine, _id: "n2", body: "theirs", created_by_email: "ana@x.com", created_by_name: "Ana Reyes" };

beforeEach(() => {
  list.mockReset().mockResolvedValue([mine, theirs]);
  create.mockReset();
  remove.mockReset().mockResolvedValue({ message: "ok" });
  currentUser.mockReset().mockReturnValue({ email: "me@x.com", role: "Member" });
});
afterEach(cleanup);

describe("NotesPanel", () => {
  test("lists notes with the count, and actions only on my own note", async () => {
    render(<NotesPanel parentType="property" parentId="p1" />);
    await waitFor(() => expect(screen.getByText("Notes · 2")).toBeInTheDocument());
    const cards = screen.getAllByTestId("note-card");
    expect(within(cards[0]).getByRole("button", { name: "Edit note" })).toBeInTheDocument();
    expect(within(cards[1]).queryByRole("button", { name: "Edit note" })).toBeNull();
    expect(within(cards[1]).queryByRole("button", { name: "Delete note" })).toBeNull();
  });

  test("Owner gets delete on every card", async () => {
    currentUser.mockReturnValue({ email: "owner@x.com", role: "Owner" });
    render(<NotesPanel parentType="property" parentId="p1" />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Delete note" })).toHaveLength(2));
    expect(screen.queryByRole("button", { name: "Edit note" })).toBeNull();
  });

  test("Add note opens the composer; saving prepends the note and reports the count", async () => {
    const onCountChange = vi.fn();
    create.mockResolvedValue({ ...mine, _id: "n3", body: "new one" });
    render(<NotesPanel parentType="property" parentId="p1" onCountChange={onCountChange} />);
    await waitFor(() => expect(onCountChange).toHaveBeenLastCalledWith(2));
    await userEvent.click(screen.getByRole("button", { name: "Add note" }));
    await userEvent.type(screen.getByLabelText("Note body"), "new one");
    await userEvent.click(screen.getByRole("button", { name: "Save note" }));
    await waitFor(() => expect(screen.getAllByTestId("note-card")).toHaveLength(3));
    expect(onCountChange).toHaveBeenLastCalledWith(3);
    expect(screen.queryByLabelText("Note body")).toBeNull();
  });

  test("empty and disabled states", async () => {
    list.mockResolvedValue([]);
    const { rerender } = render(<NotesPanel parentType="property" parentId="p1" />);
    await waitFor(() => expect(screen.getByText("No notes yet.")).toBeInTheDocument());
    rerender(<NotesPanel parentType="work_item" parentId="e1" workItemId="w1" disabled disabledHint="Save this work item to start adding notes." />);
    expect(screen.getByText("Save this work item to start adding notes.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add note" })).toBeDisabled();
  });

  test("load error is shown", async () => {
    list.mockRejectedValue(new Error("nope"));
    render(<NotesPanel parentType="property" parentId="p1" />);
    await waitFor(() => expect(screen.getByText("nope")).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/NotesPanel.test.tsx
```

- [ ] **Step 3: Write the component**

`portal/src/components/notes/NotesPanel.tsx`:

```tsx
import { useEffect, useState } from "react";
import { FileText, Loader2, Plus } from "lucide-react";
import { getCurrentUser } from "../../api/auth";
import { getEntityId } from "../../api/client";
import { useNotes } from "../../hooks/useNotes";
import { canDeleteNote, canEditNote } from "../../lib/notesPermissions";
import { NoteCard } from "./NoteCard";
import { NoteComposer } from "./NoteComposer";
import type { NoteParentType } from "../../types/api";

export interface NotesPanelProps {
  parentType: NoteParentType;
  parentId: string;
  workItemId?: string;
  disabled?: boolean;
  disabledHint?: string;
  listMaxHeightClassName?: string;
  onCountChange?: (count: number) => void;
  hideHeader?: boolean;
  composerOpen?: boolean;
  onComposerOpenChange?: (open: boolean) => void;
}

/**
 * One parent's notes feed: header with count, Add note, composer, cards.
 * Owns its own fetch so hosts mount it and forget it. Notes persist on their
 * own endpoints; a host dialog's Cancel does not undo them.
 */
export function NotesPanel({
  parentType, parentId, workItemId, disabled = false, disabledHint, listMaxHeightClassName,
  onCountChange, hideHeader = false, composerOpen, onComposerOpenChange,
}: NotesPanelProps) {
  const currentUser = getCurrentUser();
  const { notes, isLoading, error, createNote, updateNote, deleteNote, addAttachment, removeAttachment } = useNotes({
    parentType, parentId, workItemId, enabled: !disabled,
  });
  const [localComposerOpen, setLocalComposerOpen] = useState(false);
  const isComposerOpen = composerOpen ?? localComposerOpen;
  const setComposerOpen = (open: boolean) => {
    setLocalComposerOpen(open);
    onComposerOpenChange?.(open);
  };

  useEffect(() => {
    if (!disabled && !isLoading) onCountChange?.(notes.length);
  }, [disabled, isLoading, notes.length, onCountChange]);

  return (
    <section className="space-y-3" data-testid="notes-panel">
      {!hideHeader && (
        <div className="flex items-center justify-between gap-3">
          <h3 className="inline-flex items-center gap-2 text-sm font-semibold text-gray-800">
            <FileText className="w-4 h-4" />
            {`Notes · ${disabled ? 0 : notes.length}`}
          </h3>
          <button type="button" onClick={() => setComposerOpen(true)} disabled={disabled || isComposerOpen}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed">
            <Plus className="w-4 h-4" /> Add note
          </button>
        </div>
      )}

      {disabled ? (
        <p className="text-sm text-gray-500">{disabledHint}</p>
      ) : (
        <div className={`space-y-3 ${listMaxHeightClassName ? `${listMaxHeightClassName} overflow-y-auto pr-1` : ""}`}>
          {isComposerOpen && (
            <NoteComposer
              mode="create"
              autoFocus
              onSubmit={async (body, files) => {
                const { failedFiles } = await createNote(body, files);
                if (failedFiles.length === 0) setComposerOpen(false);
                return failedFiles;
              }}
              onCancel={() => setComposerOpen(false)}
            />
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {isLoading && (
            <p className="inline-flex items-center gap-2 text-sm text-gray-500"><Loader2 className="w-4 h-4 animate-spin" /> Loading notes…</p>
          )}
          {!isLoading && !error && notes.length === 0 && !isComposerOpen && (
            <p className="text-sm text-gray-500">No notes yet.</p>
          )}
          {notes.map((note) => {
            const id = getEntityId(note);
            return (
              <NoteCard
                key={id}
                note={note}
                canEdit={canEditNote(note, currentUser)}
                canDelete={canDeleteNote(note, currentUser)}
                onUpdate={(body) => updateNote(id, body)}
                onDelete={() => deleteNote(id)}
                onAddAttachment={(file) => addAttachment(id, file)}
                onRemoveAttachment={(attachmentId) => removeAttachment(id, attachmentId)}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 4: Run the test**

```bash
cd portal && npm test -- tests/NotesPanel.test.tsx && npm run typecheck
```

Expected: 5 passed.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/notes/NotesPanel.tsx tests/NotesPanel.test.tsx
git commit -m "feat: NotesPanel feed component

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

# Phase 4 — Mount in the hosts

**Prerequisite:** platform Phases 1–2 deployed and `scripts/backfill_job_item_ids.py --apply` run on the target environment. Until then a work item on an un-backfilled estimate has a transient id and `POST /notes` answers 422 for it.

### Task 18: `WorkItemNotesSection` (collapsible) in the Work Item dialog

**Files:**
- Create: `portal/src/components/estimates/WorkItemNotesSection.tsx`
- Modify: `portal/src/components/estimates/WorkItemInlineContent.tsx` (props + render after the ticket), `portal/src/components/estimates/WorkItemDialog.tsx` (new `estimateId` prop), `portal/src/pages/NewEstimateWithActivityPage.tsx:1814` (pass `estimateId`)
- Test: `portal/tests/WorkItemNotesSection.test.tsx` (new), `portal/tests/WorkItemDialog.test.tsx` (append)

**Interfaces:**
- Consumes: `NotesPanel` with `hideHeader`, `composerOpen`, `onComposerOpenChange`, `onCountChange` (Task 17); `WorkItemV2.id` (Task 3).
- Produces:
  - `<WorkItemNotesSection estimateId={string | undefined} workItemId={string} isPersisted={boolean} />`
  - `WorkItemInlineContentProps.notesHost?: { estimateId?: string; isPersisted: boolean }` — absent means "no notes section" (`TemplateDialog` never passes it).
  - `WorkItemDialogProps.estimateId?: string`.
  - sessionStorage key `notes.workItem.expanded.<estimateId>` holding `"1"` / `"0"`.

- [ ] **Step 1: Write the failing tests**

`portal/tests/WorkItemNotesSection.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const list = vi.fn();
vi.mock("../src/api/notes", () => ({
  notesApi: { list: (...a: unknown[]) => list(...a), create: vi.fn(), update: vi.fn(), remove: vi.fn(),
    uploadAttachment: vi.fn(), removeAttachment: vi.fn(), attachmentBlob: vi.fn() },
}));
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => ({ email: "me@x.com", role: "Member" }) }));
vi.mock("../src/components/common/MarkdownDescriptionEditor", () => ({
  default: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="Note body" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

import { WorkItemNotesSection } from "../src/components/estimates/WorkItemNotesSection";

const note = { _id: "n1", parent_type: "work_item", parent_id: "e1", work_item_id: "w1", body: "hi", attachments: [],
  created_by_email: "me@x.com", created_by_name: "Me", created_at: "2026-09-17T00:00:00+00:00", updated_at: "2026-09-17T00:00:00+00:00" };

beforeEach(() => {
  sessionStorage.clear();
  list.mockReset().mockResolvedValue([note]);
});
afterEach(cleanup);

describe("WorkItemNotesSection", () => {
  test("collapsed by default, header shows the count, click expands", async () => {
    render(<WorkItemNotesSection estimateId="e1" workItemId="w1" isPersisted />);
    const toggle = screen.getByRole("button", { name: /notes/i });
    await waitFor(() => expect(toggle).toHaveTextContent("Notes · 1"));
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByTestId("note-card")).toBeNull();
    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("note-card")).toBeVisible();
    expect(sessionStorage.getItem("notes.workItem.expanded.e1")).toBe("1");
  });

  test("Add note expands the section and opens the composer", async () => {
    render(<WorkItemNotesSection estimateId="e1" workItemId="w1" isPersisted />);
    await userEvent.click(screen.getByRole("button", { name: "Add note" }));
    expect(screen.getByRole("button", { name: /notes/i })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByLabelText("Note body")).toBeInTheDocument();
  });

  test("remembers the expanded state per estimate", async () => {
    sessionStorage.setItem("notes.workItem.expanded.e1", "1");
    render(<WorkItemNotesSection estimateId="e1" workItemId="w1" isPersisted />);
    expect(screen.getByRole("button", { name: /notes/i })).toHaveAttribute("aria-expanded", "true");
  });

  test("unsaved work item: hint, no fetch, Add note disabled", async () => {
    render(<WorkItemNotesSection estimateId="e1" workItemId="w1" isPersisted={false} />);
    expect(screen.getByText("Save this work item to start adding notes.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add note" })).toBeDisabled();
    await new Promise((r) => setTimeout(r, 0));
    expect(list).not.toHaveBeenCalled();
  });
});
```

Append to `portal/tests/WorkItemDialog.test.tsx` (reuse that file's existing mocks/props; add the `notes`/`auth`/editor mocks from the test above if the file lacks them):

```tsx
test("shows the notes section for a saved work item on a saved estimate", async () => {
  render(<WorkItemDialog {...baseProps} estimateId="e1" editIndex={0} draft={{ ...baseProps.draft!, id: "w1" }} />);
  expect(await screen.findByRole("button", { name: /notes/i })).toBeInTheDocument();
});

test("a new work item shows the save-first hint", () => {
  render(<WorkItemDialog {...baseProps} estimateId="e1" editIndex={null} />);
  expect(screen.getByText("Save this work item to start adding notes.")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd portal && npm test -- tests/WorkItemNotesSection.test.tsx tests/WorkItemDialog.test.tsx
```

- [ ] **Step 3: Write the section**

`portal/src/components/estimates/WorkItemNotesSection.tsx`:

```tsx
import { useCallback, useState } from "react";
import { ChevronDown, ChevronRight, FileText, Plus } from "lucide-react";
import { NotesPanel } from "../notes/NotesPanel";

export interface WorkItemNotesSectionProps {
  estimateId?: string;
  workItemId: string;
  /** False for a brand-new item (or the create page): the parent does not exist server-side yet. */
  isPersisted: boolean;
}

const UNSAVED_HINT = "Save this work item to start adding notes.";

function storageKey(estimateId?: string) {
  return `notes.workItem.expanded.${estimateId ?? "new"}`;
}

function readExpanded(estimateId?: string): boolean {
  try {
    return sessionStorage.getItem(storageKey(estimateId)) === "1";
  } catch {
    return false;
  }
}

/**
 * The collapsible Notes block at the foot of the Work Item dialog (design
 * decision D6). Collapsed by default; the header always shows the count, so
 * the panel is mounted (and fetching) even while collapsed — only the body
 * is hidden. The open/closed choice is remembered per estimate for the
 * session, like the activity panel's filter.
 */
export function WorkItemNotesSection({ estimateId, workItemId, isPersisted }: WorkItemNotesSectionProps) {
  const [expanded, setExpanded] = useState(() => readExpanded(estimateId));
  const [count, setCount] = useState(0);
  const [composerOpen, setComposerOpen] = useState(false);
  const enabled = isPersisted && Boolean(estimateId);

  const setExpandedAndRemember = (next: boolean) => {
    setExpanded(next);
    try {
      sessionStorage.setItem(storageKey(estimateId), next ? "1" : "0");
    } catch {
      // Storage unavailable (private mode): the toggle still works for this render.
    }
  };
  const handleCount = useCallback((n: number) => setCount(n), []);

  return (
    <section className="border-t border-gray-200 pt-4" data-testid="work-item-notes-section">
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => setExpandedAndRemember(!expanded)}
          aria-expanded={expanded}
          aria-controls="work-item-notes-body"
          className="inline-flex items-center gap-2 text-sm font-semibold text-gray-800"
        >
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <FileText className="w-4 h-4" />
          {`Notes · ${enabled ? count : 0}`}
        </button>
        <button
          type="button"
          disabled={!enabled || composerOpen}
          onClick={() => {
            setExpandedAndRemember(true);
            setComposerOpen(true);
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-4 h-4" /> Add note
        </button>
      </div>

      {!enabled ? (
        <p className="mt-2 text-sm text-gray-500">{UNSAVED_HINT}</p>
      ) : (
        <div id="work-item-notes-body" className={expanded ? "mt-3" : "hidden"}>
          <NotesPanel
            parentType="work_item"
            parentId={estimateId as string}
            workItemId={workItemId}
            hideHeader
            composerOpen={composerOpen}
            onComposerOpenChange={setComposerOpen}
            onCountChange={handleCount}
          />
        </div>
      )}
    </section>
  );
}
```

`portal/src/components/estimates/WorkItemInlineContent.tsx`: add to the props interface

```tsx
  /** Present only when hosted by the estimate's Work Item dialog. TemplateDialog omits it. */
  notesHost?: { estimateId?: string; isPersisted: boolean };
```

destructure `notesHost`, import `WorkItemNotesSection`, and render it directly after `<WorkItemTotalsTicket ... />` inside the `space-y-4` div:

```tsx
        {notesHost && (
          <WorkItemNotesSection
            estimateId={notesHost.estimateId}
            workItemId={workItemId}
            isPersisted={notesHost.isPersisted}
          />
        )}
```

`portal/src/components/estimates/WorkItemDialog.tsx`: add `estimateId?: string;` to the props, destructure it, and pass

```tsx
        notesHost={{ estimateId, isPersisted: editIndex !== null && Boolean(estimateId) }}
```

to `<WorkItemInlineContent>`.

`portal/src/pages/NewEstimateWithActivityPage.tsx`, at the `<WorkItemDialog` mount: add `estimateId={estimateId}`.

- [ ] **Step 4: Run the tests and typecheck**

```bash
cd portal && npm test -- tests/WorkItemNotesSection.test.tsx tests/WorkItemDialog.test.tsx tests/WorkItemInlineContent.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/estimates/WorkItemNotesSection.tsx src/components/estimates/WorkItemInlineContent.tsx src/components/estimates/WorkItemDialog.tsx src/pages/NewEstimateWithActivityPage.tsx tests/WorkItemNotesSection.test.tsx tests/WorkItemDialog.test.tsx
git commit -m "feat: collapsible notes section in the work item dialog

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 19: Estimate page — estimate-level notes at the bottom (D8) and per-row count badges

**Files:**
- Modify: `portal/src/pages/NewEstimateWithActivityPage.tsx` (state + fetch near `:165-262`; badge in the row at `:1252-1275`; new section after the work-items card at `:1339`)
- Test: `portal/tests/NewEstimateWithActivityPage.notes.test.tsx` (new)

**Interfaces:**
- Consumes: `notesApi.counts` (Task 10), `NotesPanel` (Task 17).
- Produces: nothing new.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/NewEstimateWithActivityPage.notes.test.tsx`. Copy the mock block and the `renderPage()` helper **verbatim** from `tests/NewEstimateWithActivityPage.autosave.test.tsx` (its estimate fixture is at line ~135 and has `job_items`), then add these mocks and tests. Give the fixture's job items ids `"w1"` and `"w2"` and make sure the mocked `estimatesApi.get` returns it.

```tsx
const counts = vi.fn();
const list = vi.fn();
vi.mock("../src/api/notes", () => ({
  notesApi: {
    counts: (...a: unknown[]) => counts(...a),
    list: (...a: unknown[]) => list(...a),
    create: vi.fn(), update: vi.fn(), remove: vi.fn(), uploadAttachment: vi.fn(), removeAttachment: vi.fn(), attachmentBlob: vi.fn(),
  },
}));
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => ({ email: "me@x.com", role: "Member", first_name: "Me", last_name: "" }) }));

beforeEach(() => {
  counts.mockReset().mockResolvedValue({ w1: 2 });
  list.mockReset().mockResolvedValue([]);
});

test("edit mode renders the estimate-level notes section last and note-count badges on rows", async () => {
  renderPage("/estimates/est-1");            // whatever route helper the autosave test uses
  expect(await screen.findByText("Notes · 0")).toBeInTheDocument();
  expect(list).toHaveBeenCalledWith({ parentType: "estimate", parentId: "est-1", workItemId: undefined });
  const badge = await screen.findByLabelText("2 notes");
  expect(badge).toHaveTextContent("2");
  const rows = screen.getAllByRole("row").filter((r) => within(r).queryByText(/^#\d+$/));
  expect(within(rows[0]).getByLabelText("2 notes")).toBeInTheDocument();
  expect(within(rows[1]).queryByLabelText(/notes/)).toBeNull();
  // The notes section is the last section in the page body.
  const sections = document.querySelectorAll("[data-testid='notes-panel']");
  expect(sections).toHaveLength(1);
});

test("create mode has no estimate-level notes section", async () => {
  renderPage("/estimates/new");
  await new Promise((r) => setTimeout(r, 0));
  expect(screen.queryByTestId("notes-panel")).toBeNull();
  expect(counts).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/NewEstimateWithActivityPage.notes.test.tsx
```

- [ ] **Step 3: Implement**

In `NewEstimateWithActivityPage.tsx`:

1. Imports: `import { MessageSquareText } from "lucide-react";` (add to the existing lucide import), `import { notesApi } from "../api/notes";`, `import { NotesPanel } from "../components/notes/NotesPanel";`.
2. State, next to `workItems`: `const [noteCounts, setNoteCounts] = useState<Record<string, number>>({});`
3. A loader and its triggers:

```tsx
  const loadNoteCounts = useCallback(async () => {
    if (!estimateId) return;
    try {
      const data = await notesApi.counts(estimateId);
      setNoteCounts(data && typeof data === "object" ? data : {});
    } catch {
      // Badges are a convenience; a failed count must not disturb the page.
    }
  }, [estimateId]);

  useEffect(() => {
    void loadNoteCounts();
  }, [loadNoteCounts]);
```

and call `void loadNoteCounts();` at the end of `closeWorkItemDialog` and in `saveWorkItemDialog` after `setWorkItemEditIndex(null)` (a note may have been added while the dialog was open).

4. Badge in the row, inside the description `<td>` after the gap pills block:

```tsx
                        {(noteCounts[item.id] ?? 0) > 0 && (
                          <span
                            aria-label={`${noteCounts[item.id]} ${noteCounts[item.id] === 1 ? "note" : "notes"}`}
                            title={`${noteCounts[item.id]} ${noteCounts[item.id] === 1 ? "note" : "notes"}`}
                            className="mt-2 inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700"
                          >
                            <MessageSquareText className="w-3.5 h-3.5" />
                            {noteCounts[item.id]}
                          </span>
                        )}
```

5. The estimate-level section (D8). Place it as a **sibling of the work-items card, inside the page's outer container** (controller ruling R4, pre-flight: the Grand Total block is followed by several closing tags, so read the JSX structure and match the work-items card's own nesting depth rather than counting lines):

```tsx
      {isEditMode && estimateId && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
          <NotesPanel parentType="estimate" parentId={estimateId} />
        </div>
      )}
```

- [ ] **Step 4: Run the tests and typecheck**

```bash
cd portal && npm test -- tests/NewEstimateWithActivityPage.notes.test.tsx tests/NewEstimateWithActivityPage.autosave.test.tsx tests/NewEstimateWithActivityPage.sendGate.test.tsx && npm run typecheck
```

If the two existing page tests fail on `notesApi` being undefined, add the same `vi.mock("../src/api/notes", ...)` block to them (they do not exercise notes; `counts`/`list` resolving `{}`/`[]` is enough).

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/pages/NewEstimateWithActivityPage.tsx tests/NewEstimateWithActivityPage.notes.test.tsx tests/NewEstimateWithActivityPage.autosave.test.tsx tests/NewEstimateWithActivityPage.sendGate.test.tsx
git commit -m "feat: estimate-level notes section and work item note badges

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 20: Properties — detail pane and phone sheet

**Files:**
- Modify: `portal/src/components/properties/PropertyDetailPanel.tsx:76-130`
- Test: `portal/tests/PropertyDetailPanel.test.tsx` (new); `portal/tests/PropertiesPageMobileSheet.test.tsx`, `tests/PropertiesPageEstimates.test.tsx`, `tests/PropertiesPageMobileActivity.test.tsx` (add the notes mock so they keep passing)

**Interfaces:**
- Consumes: `NotesPanel` (Task 17).
- Produces: nothing new. `PropertyDetailPanel` renders notes on every viewport, unlike the activity panel.

- [ ] **Step 1: Write the failing test**

`portal/tests/PropertyDetailPanel.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { Property, TaskStatus } from "../src/types/api";

const list = vi.fn().mockResolvedValue([]);
vi.mock("../src/api/notes", () => ({
  notesApi: { list: (...a: unknown[]) => list(...a), create: vi.fn(), update: vi.fn(), remove: vi.fn(),
    uploadAttachment: vi.fn(), removeAttachment: vi.fn(), attachmentBlob: vi.fn() },
}));
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => ({ email: "me@x.com", role: "Member" }) }));
vi.mock("../src/components/properties/PropertyMapThumbnail", () => ({ PropertyMapThumbnail: () => <div data-testid="map" /> }));
vi.mock("../src/components/properties/PropertyActivityPanel", () => ({ PropertyActivityPanel: () => <div data-testid="activity" /> }));
vi.mock("../src/components/common/MarkdownDescriptionEditor", () => ({ default: () => <textarea aria-label="Note body" /> }));

import { PropertyDetailPanel } from "../src/components/properties/PropertyDetailPanel";

afterEach(cleanup);

const property = { _id: "p1", name: "Maple House", street: "1 Maple St", city: "Toronto", contacts: [] } as unknown as Property;

describe("PropertyDetailPanel notes", () => {
  test("mounts the property notes feed between the address row and the activity panel", async () => {
    render(<MemoryRouter><PropertyDetailPanel property={property} contacts={[]} taskStatuses={[] as TaskStatus[]} showActivity /></MemoryRouter>);
    await waitFor(() => expect(list).toHaveBeenCalledWith({ parentType: "property", parentId: "p1", workItemId: undefined }));
    const notes = screen.getByTestId("notes-panel");
    const activity = screen.getByTestId("activity");
    expect(notes.compareDocumentPosition(activity) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  test("still mounts notes when the activity panel is skipped (phone sheet)", async () => {
    render(<MemoryRouter><PropertyDetailPanel property={property} contacts={[]} taskStatuses={[]} showActivity={false} showName={false} /></MemoryRouter>);
    expect(screen.getByTestId("notes-panel")).toBeInTheDocument();
    expect(screen.queryByTestId("activity")).toBeNull();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/PropertyDetailPanel.test.tsx
```

- [ ] **Step 3: Mount the panel**

In `PropertyDetailPanel.tsx`, import `{ NotesPanel } from "../notes/NotesPanel"` and insert between the address/map row's closing `</div>` and `{showActivity && (`:

```tsx
      {/* Notes on every viewport: photographing a site from a phone is the
          main reason to attach an image to a property note. */}
      <NotesPanel
        parentType="property"
        parentId={getEntityId(property)}
        listMaxHeightClassName="max-h-80"
      />
```

Then add this block to `PropertiesPageMobileSheet.test.tsx`, `PropertiesPageEstimates.test.tsx` and `PropertiesPageMobileActivity.test.tsx` next to their other `vi.mock` calls:

```tsx
vi.mock("../src/api/notes", () => ({
  notesApi: { list: vi.fn(async () => []), counts: vi.fn(async () => ({})), create: vi.fn(), update: vi.fn(),
    remove: vi.fn(), uploadAttachment: vi.fn(), removeAttachment: vi.fn(), attachmentBlob: vi.fn() },
}));
```

- [ ] **Step 4: Run the tests and typecheck**

```bash
cd portal && npm test -- tests/PropertyDetailPanel.test.tsx tests/PropertiesPageMobileSheet.test.tsx tests/PropertiesPageEstimates.test.tsx tests/PropertiesPageMobileActivity.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/properties/PropertyDetailPanel.tsx tests/PropertyDetailPanel.test.tsx tests/PropertiesPageMobileSheet.test.tsx tests/PropertiesPageEstimates.test.tsx tests/PropertiesPageMobileActivity.test.tsx
git commit -m "feat: property notes feed in the detail pane and phone sheet

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 21: Contacts — detail pane and phone sheet

**Files:**
- Modify: `portal/src/components/contacts/ContactDetailPanel.tsx:77`, `:126-128`
- Test: `portal/tests/ContactDetailPanel.test.tsx` (new); every `tests/ContactsPage*.test.tsx` that renders the detail panel gets the notes mock from Task 20

- [ ] **Step 1: Write the failing test**

`portal/tests/ContactDetailPanel.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { Contact } from "../src/types/api";

const list = vi.fn().mockResolvedValue([]);
vi.mock("../src/api/notes", () => ({
  notesApi: { list: (...a: unknown[]) => list(...a), create: vi.fn(), update: vi.fn(), remove: vi.fn(),
    uploadAttachment: vi.fn(), removeAttachment: vi.fn(), attachmentBlob: vi.fn() },
}));
vi.mock("../src/api/auth", () => ({ getCurrentUser: () => ({ email: "me@x.com", role: "Member" }) }));
vi.mock("../src/components/common/MarkdownDescriptionEditor", () => ({ default: () => <textarea aria-label="Note body" /> }));

import { ContactDetailPanel } from "../src/components/contacts/ContactDetailPanel";

afterEach(cleanup);

const contact = { _id: "c1", first_name: "Ana", last_name: "Reyes", role: "Home Owner", notes: "legacy text" } as unknown as Contact;

test("replaces the plain-text Notes field with the notes feed", async () => {
  render(<MemoryRouter><ContactDetailPanel contact={contact} properties={[]} /></MemoryRouter>);
  await waitFor(() => expect(list).toHaveBeenCalledWith({ parentType: "contact", parentId: "c1", workItemId: undefined }));
  expect(screen.getByTestId("notes-panel")).toBeInTheDocument();
  expect(screen.queryByText("legacy text")).toBeNull();
});
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd portal && npm test -- tests/ContactDetailPanel.test.tsx
```

- [ ] **Step 3: Replace the field**

In `ContactDetailPanel.tsx`: delete the `const notes = ...` line (`:77`), import `{ NotesPanel } from "../notes/NotesPanel"`, and replace the `<Field label="Notes">…</Field>` block with

```tsx
      <NotesPanel parentType="contact" parentId={getEntityId(contact)} />
```

Add the Task 20 `vi.mock("../src/api/notes", ...)` block to each `tests/ContactsPage*.test.tsx` (run `ls tests | grep -i contactspage`).

- [ ] **Step 4: Run the tests and typecheck**

```bash
cd portal && npm test -- tests/ContactDetailPanel.test.tsx tests/ContactsPage*.test.tsx && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/contacts/ContactDetailPanel.tsx tests/ContactDetailPanel.test.tsx tests/ContactsPage*.test.tsx
git commit -m "feat: contact notes feed in the detail pane and phone sheet

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

# Phase 5 — Migration, Maple, and retiring the legacy fields

Order matters: 22 (migrate) → 23 (Maple writes notes instead of the scalar) → run the migration on Dev and prod → 24 (remove backend fields) → 25 (remove portal fields) → 26 (docs).

### Task 22: `scripts/migrate_legacy_notes.py` and `create_note_as`

**Files:**
- Modify: `platform/services/notes.py` (add `create_note_as`)
- Create: `platform/scripts/migrate_legacy_notes.py`
- Test: `platform/tests/test_migrate_legacy_notes.py` (new)

**Interfaces:**
- Produces:
  - `services.notes.create_note_as(*, company, parent_type, parent_id, body, author_email, author_name, created_at=None) -> Note` — inserts without parent validation or a `User`; for scripts and Maple.
  - `scripts.migrate_legacy_notes.migrate_legacy_notes(apply: bool) -> dict` with keys `properties_migrated`, `contacts_migrated`, `skipped_no_owner`; CLI `--apply`.
  - `scripts.migrate_legacy_notes.legacy_text_to_markdown(text) -> str`.

- [ ] **Step 1: Write the failing test**

`platform/tests/test_migrate_legacy_notes.py`:

```python
"""Property.notes / Contact.notes (plain strings) → one Note each, authored
by the company's earliest Owner (D7). Idempotent: the scalar is nulled on
migration so a re-run finds nothing."""

from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from tests.helpers import run_on_portal


def test_legacy_text_to_markdown_keeps_line_breaks():
    from scripts.migrate_legacy_notes import legacy_text_to_markdown

    assert legacy_text_to_markdown("gate 4411\nring twice\n\nDog in yard") == "gate 4411  \nring twice\n\nDog in yard"
    assert legacy_text_to_markdown("  plain  ") == "plain"


def test_migrates_property_and_contact_notes_to_the_owner(client: TestClient, test_company_id: str):
    from scripts.migrate_legacy_notes import migrate_legacy_notes

    async def _setup():
        # Raw inserts: the script (and this test) must keep working after
        # Task 24 removes `notes` from the models.
        from models import Contact, Property

        now = datetime.now(timezone.utc)
        prop = await Property.get_pymongo_collection().insert_one({
            "name": "", "street": "7 Legacy St", "city": "K", "prov_state": "BC", "notes": "gate 4411",
            "contacts": [], "company": PydanticObjectId(test_company_id), "created_at": now, "updated_at": now,
        })
        contact = await Contact.get_pymongo_collection().insert_one({
            "first_name": "L", "last_name": "M", "notes": "prefers mornings", "role": "Home Owner",
            "company": PydanticObjectId(test_company_id), "created_at": now, "updated_at": now,
        })
        return str(prop.inserted_id), str(contact.inserted_id)

    prop_id, contact_id = run_on_portal(client, _setup)
    try:
        dry = run_on_portal(client, migrate_legacy_notes, False)
        assert dry["properties_migrated"] >= 1 and dry["contacts_migrated"] >= 1
        assert client.get(f"/notes?parent_type=property&parent_id={prop_id}").json() == []

        applied = run_on_portal(client, migrate_legacy_notes, True)
        assert applied["properties_migrated"] >= 1
        notes = client.get(f"/notes?parent_type=property&parent_id={prop_id}").json()
        assert [n["body"] for n in notes] == ["gate 4411"]
        assert notes[0]["created_by_email"] == "default.owner@example.com"
        assert notes[0]["created_by_name"] == "Default Owner"
        contact_notes = client.get(f"/notes?parent_type=contact&parent_id={contact_id}").json()
        assert [n["body"] for n in contact_notes] == ["prefers mornings"]

        async def _scalars():
            from models import Contact, Property

            p = await Property.get_pymongo_collection().find_one({"_id": PydanticObjectId(prop_id)})
            c = await Contact.get_pymongo_collection().find_one({"_id": PydanticObjectId(contact_id)})
            return p.get("notes"), c.get("notes")

        assert run_on_portal(client, _scalars) == (None, None)

        again = run_on_portal(client, migrate_legacy_notes, True)
        assert len(client.get(f"/notes?parent_type=property&parent_id={prop_id}").json()) == 1
        assert again["properties_migrated"] <= applied["properties_migrated"]
    finally:
        client.delete(f"/properties/{prop_id}")
        client.delete(f"/contacts/{contact_id}")


def test_company_without_an_owner_is_skipped(client: TestClient):
    from scripts.migrate_legacy_notes import migrate_legacy_notes

    async def _setup():
        from models import Company, Contact

        company = Company(
            name="Ownerless Co", street="1 Nowhere", city="K", prov_state="BC", postal_zip="V1V 1V1",
            country="Canada", email="ownerless@example.com", phone="+15550000001", industry="Landscaping",
        )
        await company.insert()
        now = datetime.now(timezone.utc)
        contact = await Contact.get_pymongo_collection().insert_one({
            "first_name": "No", "last_name": "Owner", "notes": "orphan", "role": "Home Owner",
            "company": company.id, "created_at": now, "updated_at": now,
        })
        return str(company.id), str(contact.inserted_id)

    company_id, contact_id = run_on_portal(client, _setup)
    try:
        summary = run_on_portal(client, migrate_legacy_notes, True)
        assert summary["skipped_no_owner"] >= 1

        async def _check():
            from models import Contact, Note

            c = await Contact.get_pymongo_collection().find_one({"_id": PydanticObjectId(contact_id)})
            return c.get("notes"), await Note.find(Note.parent_id == PydanticObjectId(contact_id)).count()

        assert run_on_portal(client, _check) == ("orphan", 0)
    finally:
        async def _cleanup():
            from models import Company, Contact, Note

            await Note.find(Note.parent_id == PydanticObjectId(contact_id)).delete()
            await Contact.get_pymongo_collection().delete_one({"_id": PydanticObjectId(contact_id)})
            company = await Company.get(PydanticObjectId(company_id))
            if company:
                await company.delete()

        run_on_portal(client, _cleanup)
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd platform && ./run_tests.sh tests/test_migrate_legacy_notes.py -v
```

- [ ] **Step 3: Add `create_note_as` and write the script**

Append to `platform/services/notes.py`:

```python
async def create_note_as(
    *,
    company: PydanticObjectId,
    parent_type: NoteParentType,
    parent_id: PydanticObjectId,
    body: str,
    author_email: str,
    author_name: str,
    created_at: Optional[datetime] = None,
) -> Note:
    """Insert a note on behalf of a named author, with no parent validation.

    For the legacy-notes migration and for Maple's property/contact agents,
    which already hold a resolved parent and know the acting user by email.
    The HTTP path must keep using create_note(), which validates the parent.
    """
    stamp = created_at or datetime.now(timezone.utc)
    note = Note(
        company=company,
        parent_type=parent_type,
        parent_id=parent_id,
        work_item_id=None,
        body=body,
        created_by_email=_norm_email(author_email),
        created_by_name=author_name or author_email,
        created_at=stamp,
        updated_at=stamp,
    )
    await note.insert()
    return note
```

Create `platform/scripts/migrate_legacy_notes.py`:

```python
#!/usr/bin/env python3
"""Move Property.notes and Contact.notes (plain strings) into the notes collection.

Each non-empty scalar becomes ONE Note authored by the company's earliest-
created Owner (design decision D7), dated with the parent's updated_at.
Single line breaks become markdown hard breaks so the text reads as it did.
After a successful insert the scalar is set to null, which is what makes a
re-run a no-op. Companies with no Owner are reported and left untouched.

Estimate.notes is deliberately NOT touched (D1).

Usage:
    python scripts/migrate_legacy_notes.py          # dry run (default)
    python scripts/migrate_legacy_notes.py --apply  # persist
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beanie import PydanticObjectId  # noqa: E402

from database import init_db  # noqa: E402
from models import Contact, Property, User, UserRole  # noqa: E402
from models.note import NoteParentType  # noqa: E402
from services.notes import create_note_as  # noqa: E402

_SINGLE_NEWLINE = re.compile(r"(?<!\n)\n(?!\n)")


def legacy_text_to_markdown(text: str) -> str:
    """Plain text → markdown that renders with the same line breaks."""
    return _SINGLE_NEWLINE.sub("  \n", (text or "").strip())


async def _owner_for(company_id: PydanticObjectId, cache: Dict[PydanticObjectId, Optional[Tuple[str, str]]]) -> Optional[Tuple[str, str]]:
    if company_id in cache:
        return cache[company_id]
    owner = await User.find(User.company == company_id, User.role == UserRole.OWNER).sort("+created_at").first_or_none()
    result = None
    if owner is not None:
        name = f"{(owner.first_name or '').strip()} {(owner.last_name or '').strip()}".strip() or owner.email
        result = (owner.email, name)
    cache[company_id] = result
    return result


async def _migrate_collection(model, parent_type: NoteParentType, apply: bool, owners, summary_key: str, summary: dict) -> None:
    # Raw documents on purpose: once the `notes` field leaves the models
    # (plan Task 24) Beanie would drop the key on load and this script — and
    # its tests — must keep working for any company skipped earlier.
    collection = model.get_pymongo_collection()
    async for doc in collection.find({"notes": {"$type": "string", "$ne": ""}}, {"notes": 1, "company": 1, "updated_at": 1}):
        body = legacy_text_to_markdown(doc["notes"])
        if not body:
            continue
        owner = await _owner_for(doc["company"], owners)
        if owner is None:
            summary["skipped_no_owner"] += 1
            print(f"  skip {model.Settings.name}/{doc['_id']}: company {doc['company']} has no Owner")
            continue
        summary[summary_key] += 1
        if not apply:
            continue
        await create_note_as(
            company=doc["company"],
            parent_type=parent_type,
            parent_id=doc["_id"],
            body=body,
            author_email=owner[0],
            author_name=owner[1],
            created_at=doc.get("updated_at") or datetime.now(timezone.utc),
        )
        await collection.update_one({"_id": doc["_id"]}, {"$set": {"notes": None}})


async def migrate_legacy_notes(apply: bool) -> dict:
    summary = {"properties_migrated": 0, "contacts_migrated": 0, "skipped_no_owner": 0}
    owners: Dict[PydanticObjectId, Optional[Tuple[str, str]]] = {}
    await _migrate_collection(Property, NoteParentType.PROPERTY, apply, owners, "properties_migrated", summary)
    await _migrate_collection(Contact, NoteParentType.CONTACT, apply, owners, "contacts_migrated", summary)
    return summary


async def _main(apply: bool) -> int:
    await init_db()
    summary = await migrate_legacy_notes(apply)
    mode = "APPLIED" if apply else "DRY RUN"
    for key, value in summary.items():
        print(f"[{mode}] {key}: {value}")
    if not apply:
        print("Nothing written. Re-run with --apply to persist.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="persist (default is a dry run)")
    sys.exit(asyncio.run(_main(parser.parse_args().apply)))
```

- [ ] **Step 4: Run the tests and gates**

```bash
cd platform && ./run_tests.sh tests/test_migrate_legacy_notes.py tests/test_notes_service.py -v
./run_mypy.sh scripts/migrate_legacy_notes.py services/notes.py && ./run_ruff.sh scripts/migrate_legacy_notes.py services/notes.py
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add services/notes.py scripts/migrate_legacy_notes.py tests/test_migrate_legacy_notes.py
git commit -m "feat: migrate legacy property and contact notes into the notes collection

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 23: Maple's property and contact agents write a Note instead of the scalar

**Files:**
- Modify: `platform/agents/property/service.py:1709` (`_merge_and_update_property`, before `merged_payload.update(fields)`), `:422-470` (`_update_property_via_api`, exclude `notes` from the write set)
- Modify: `platform/agents/contact/service.py:~1244` (before `merged_payload.update(fields)`)
- Test: `platform/tests/test_property_agent.py`, `platform/tests/test_contact_agent.py` (append)

**Interfaces:**
- Consumes: `create_note_as` (Task 22); `working_context["current_user_email"]` / `["current_user_name"]` (set by `routers/agents.py:1044-1052`).
- Produces: behavior only. The phrasing "update the notes on 123 Main St: gate code 4411" still routes to `update_property`; the handler now inserts a note.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_property_agent.py` (reuse that file's `FakePropertyDoc` and the classify/resolve stubs from `test_property_agent_updates_property` at `:302`):

```python
def test_property_notes_phrasing_creates_a_note_instead_of_writing_the_scalar(monkeypatch):
    async def fake_classify(self, _message, context=None):
        return {"intent": "update_property", "probability": 0.9, "fields": {"notes": "gate code 4411"},
                "full_name": "123 Main Street", "confirm_delete": False, "needs_clarification": False,
                "clarifying_question": None}

    stored = {"_id": "507f1f77bcf86cd799439013", "name": "Main Office", "street": "123 Main Street",
              "city": "Vancouver", "prov_state": "BC", "postal_zip": "V1V 2A2", "country": "Canada", "contacts": []}

    async def fake_resolve(self, _company_id, _parsed):
        return (FakePropertyDoc(dict(stored)), None, [], False)

    seen_patches = []

    async def fake_update(self, property_id, company_id, full_payload):
        seen_patches.append(dict(full_payload))
        payload = {**stored, **full_payload, "_id": stored["_id"], "id": property_id, "company": company_id}
        return FakePropertyDoc(payload)

    created = []

    async def fake_create_note_as(**kwargs):
        created.append(kwargs)

    monkeypatch.setattr(PropertyAgent, "_classify_with_llm", fake_classify)
    monkeypatch.setattr(PropertyAgent, "_resolve_target_property", fake_resolve)
    monkeypatch.setattr(PropertyAgent, "_update_property_via_api", fake_update)
    monkeypatch.setattr("agents.property.service.create_note_as", fake_create_note_as)

    agent = PropertyAgent(use_llm=True, llm=object())
    result = asyncio.run(agent.process(
        "update the notes on 123 Main Street: gate code 4411",
        context={"company_id": "507f1f77bcf86cd799439011", "current_user_email": "ana@example.com",
                 "current_user_name": "Ana Reyes"},
    ))

    assert result["success"] is True
    assert created and created[0]["body"] == "gate code 4411"
    assert created[0]["author_email"] == "ana@example.com"
    assert created[0]["author_name"] == "Ana Reyes"
    assert str(created[0]["parent_id"]) == stored["_id"]
    assert all("notes" not in patch for patch in seen_patches)
```

Append the equivalent to `platform/tests/test_contact_agent.py`, following that file's own update-test stubs (`_classify_with_llm`, `_resolve_target_contact`, `_update_contact_via_api`) with `fields={"notes": "prefers mornings"}` and asserting `agents.contact.service.create_note_as` was called with `parent_type == NoteParentType.CONTACT` and no patch carried `notes`.

- [ ] **Step 2: Run to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_property_agent.py tests/test_contact_agent.py -k notes -v
```

Expected: FAIL — `AttributeError: module 'agents.property.service' has no attribute 'create_note_as'`.

- [ ] **Step 3: Implement**

`platform/agents/property/service.py`: add imports `from models.note import NoteParentType` and `from services.notes import create_note_as`. In `_merge_and_update_property`, immediately after `existing_payload = self._property_to_dict(target_property)`:

```python
        # "notes" is no longer a field on the property: a note phrasing
        # inserts a Note authored by the acting user (notes v2, 2026-09).
        note_text = _safe_str(fields.pop("notes", None)).strip()
        if note_text:
            await create_note_as(
                company=PydanticObjectId(company_id),
                parent_type=NoteParentType.PROPERTY,
                parent_id=PydanticObjectId(_safe_str(existing_payload.get("_id") or existing_payload.get("id"))),
                body=note_text,
                author_email=_safe_str(working_context.get("current_user_email")) or "maple@3maples.ai",
                author_name=_safe_str(working_context.get("current_user_name")) or "Maple",
            )
```

and in `_update_property_via_api` change the write set to exclude it as belt-and-braces:

```python
        _safe_update_fields = (PROPERTY_ALLOWED_FIELDS | {"street", "city", "prov_state", "contacts", "updated_at"}) - {"notes"}
```

`platform/agents/contact/service.py`: same two imports; in the update path right after `existing_payload = self._contact_to_dict(target_contact)` (the block ending at `:1244`):

```python
        note_text = _safe_str(fields.pop("notes", None)).strip()
        if note_text:
            await create_note_as(
                company=PydanticObjectId(company_id),
                parent_type=NoteParentType.CONTACT,
                parent_id=PydanticObjectId(_safe_str(existing_payload.get("_id") or existing_payload.get("id"))),
                body=note_text,
                author_email=_safe_str(working_context.get("current_user_email")) or "maple@3maples.ai",
                author_name=_safe_str(working_context.get("current_user_name")) or "Maple",
            )
```

If a phrasing carries **only** a note, `fields` is now empty and the sparse update writes just `updated_at`; the response still reads "I've updated the contact for you" with the details block. Change the response line in that branch to `"I've added a note to the {resource} for you."` when `note_text and not fields`, matching the CRUD tone template in CLAUDE.md.

- [ ] **Step 4: Run the tests and gates**

```bash
cd platform && ./run_tests.sh tests/test_property_agent.py tests/test_contact_agent.py -v
./run_mypy.sh agents/property agents/contact && ./run_ruff.sh agents/property agents/contact
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add agents/property/service.py agents/contact/service.py tests/test_property_agent.py tests/test_contact_agent.py
git commit -m "feat: Maple property and contact note phrasings create notes

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Deploy checkpoint.** After Tasks 22–23 reach an environment: `python scripts/migrate_legacy_notes.py` (dry run), review the skipped-company list, then `--apply`. Do this on Dev, then prod, before Task 24 ships anywhere.

---

### Task 24: Remove `Property.notes` and `Contact.notes` from the backend

**Files:**
- Modify: `platform/models/property.py:16`, `platform/models/contact.py:27`, `platform/routers/properties.py:390`, `platform/routers/contacts.py:47`, `platform/agents/property/service.py:80,966-967`, `platform/agents/contact/service.py:78,819-820`, `platform/agents/contact/utils.py:94`
- Test: `platform/tests/test_property_api.py`, `platform/tests/test_contact_api.py`, `platform/tests/test_property_model.py`/`test_contact_model.py` if they assert on `notes` (grep first)

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_property_api.py` and `platform/tests/test_contact_api.py`:

```python
def test_notes_is_no_longer_a_property_field(client: TestClient, test_company_id: str):
    created = client.post("/properties/", json={"street": "1 Gone St", "city": "K", "prov_state": "BC",
                                                "contacts": [], "company": test_company_id, "notes": "ignored"})
    assert created.status_code == 200
    assert "notes" not in created.json()
    prop_id = created.json()["_id"]
    updated = client.put(f"/properties/{prop_id}", json={"notes": "still ignored", "city": "Kelowna"})
    assert updated.status_code == 200
    assert "notes" not in updated.json() and updated.json()["city"] == "Kelowna"
    client.delete(f"/properties/{prop_id}")
```

(and the contact twin with `first_name`/`last_name`).

- [ ] **Step 2: Run to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_property_api.py tests/test_contact_api.py -k "no_longer" -v
```

- [ ] **Step 3: Remove the field everywhere**

- Delete `notes: Optional[str] = None` from `models/property.py` and `models/contact.py`. Beanie ignores the stale key on documents the migration has already nulled, and on any it skipped (no Owner) — those companies' legacy text stays in the database untouched, readable by a script, never shown.
- Delete `notes: Optional[str] = None` from `UpdatePropertyRequest` and `UpdateContactRequest`. `create_property` binds the `Property` document directly, so the model change covers POST (`extra` is ignored by default).
- **`notes` STAYS in `PROPERTY_ALLOWED_FIELDS` and `CONTACT_ALLOWED_FIELDS`** (controller ruling R2, pre-flight). Those sets gate `_normalize_fields`, which drops any key not in them — so removing `notes` there would silently discard the note text *before* Task 23's `fields.pop("notes")` ever sees it, killing every Maple note phrasing. They are the classifier's field allowlist, not the database write set; the real write set is `_safe_update_fields` in `_update_property_via_api`, which Task 23 already narrows.
- **`"notes"` STAYS in the stopword list at `agents/contact/utils.py:94`** (controller ruling R3, pre-flight). That list stops words being parsed into a contact's *name*; it is not a schema reference. Removing it would let "notes" leak into parsed names from phrasings like "update the notes on John Smith".
- Keep the `notes` aliases in `agents/property/text_helpers.py` (`:53-54`, `:96`) so the phrasing still parses into `fields["notes"]` for Task 23's branch.
- Delete only the accuracy suggestions that read the now-absent field: `agents/property/service.py:966-967` and `agents/contact/service.py:819-820` — both would otherwise fire on every record.
- Run `grep -rn "\"notes\"\|\.notes\b" routers/properties.py routers/contacts.py agents/property agents/contact services/*csv* scripts/` and clean up any remaining reference (CSV column maps included; a legacy `notes` column in an upload is simply ignored from now on).
- Check `tests/test_property_agent.py:322` (`"notes": "legacy"` in a fake doc) — harmless, leave it. `scripts/migrate_legacy_notes.py` and its test read and write raw documents by design, so they keep passing after the field is gone.

- [ ] **Step 4: Run the tests and gates**

```bash
cd platform && ./run_tests.sh tests/test_property_api.py tests/test_contact_api.py tests/test_property_agent.py tests/test_contact_agent.py tests/test_property_upload_api.py tests/test_contact_upload_api.py -q
./run_mypy.sh models routers/properties.py routers/contacts.py agents/property agents/contact
./run_ruff.sh models routers/properties.py routers/contacts.py agents/property agents/contact
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd platform && git add models/property.py models/contact.py routers/properties.py routers/contacts.py agents/property agents/contact tests/
git commit -m "refactor: retire the legacy notes string on properties and contacts

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 25: Remove the Notes textareas from the portal forms

**Files:**
- Modify: `portal/src/components/properties/PropertyDialog.tsx:26,38,191-192,226,521-540`
- Modify: `portal/src/pages/ContactsPage.tsx:50,74,530,552,1060-1075,1089`
- Test: whichever of `tests/PropertyDialog*.test.tsx` / `tests/ContactsPage*.test.tsx` reference "Notes" (grep), plus a new assertion in each that the textarea is gone

- [ ] **Step 1: Write the failing tests**

Append to the PropertyDialog test file (or create `tests/PropertyDialogNotes.test.tsx` using that file's mocks) and to a ContactsPage test:

```tsx
test("the edit form no longer has a Notes textarea (notes live in the detail pane)", async () => {
  // …render the dialog / open the contact form as the neighboring tests do…
  expect(screen.queryByLabelText("Notes")).toBeNull();
});
```

- [ ] **Step 2: Run to verify they fail**

- [ ] **Step 3: Remove the fields**

In both files: delete `notes` from the form-state interface and initial value, from the edit-hydration mapping, from the save payload, and delete the `<textarea>` block with its label. Search each file for `notes` afterwards; zero hits expected.

- [ ] **Step 4: Run the tests and typecheck**

```bash
cd portal && npm test -- tests/PropertyDialog tests/ContactsPage && npm run typecheck
```

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/properties/PropertyDialog.tsx src/pages/ContactsPage.tsx tests/
git commit -m "refactor: drop the legacy notes textareas from the property and contact forms

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 26: Documentation

**Files:**
- Modify: `documentation/development/maple-phrasing-reference.md` (§ Property, § Contact: the notes phrasings now create a note; bump "Last updated"; §12.3 counts unchanged)
- Modify: `CLAUDE.md` (root): add a **Notes** subsection under "Key Implementation Notes"
- Modify: `documentation/development/plans/2026-09-17-notes-design.md`: status → Implemented
- No changelog entry unless asked.

- [ ] **Step 1: Write the CLAUDE.md subsection**

Under "Key Implementation Notes", after the Brevo section:

```markdown
### Notes (work items, estimates, properties, contacts)

One `notes` collection (`models/note.py`) with a polymorphic parent
(`work_item` / `estimate` / `property` / `contact`); `work_item` notes also
carry `work_item_id` = `JobItem.id`. Served by `routers/notes.py` through
`services/notes.py`; attachments (image/video/PDF) live in the
`note_attachments` GridFS bucket via `services/note_attachments.py`, which
shares `services/media_blobs.py` with task photos.

- **Editing is creator-only; deleting is creator-or-Owner.** Admins get no
  override. Reading and creating are open to the company.
- **Estimate status never gates notes**, Archived included.
- **`JobItem.id` is what notes point at.** It is server-generated, preserved
  through `PUT /estimates` (by value, or by position when a legacy client
  sends none), and `scripts/backfill_job_item_ids.py` must have run before
  notes are enabled on an environment. Removing a work item cascades its
  notes; so does deleting an estimate, property or contact.
- **`Estimate.notes` (the plain string printed on the customer document) is
  a different thing** and is untouched by all of this.
- Portal: `components/notes/*`, `hooks/useNotes.ts`, `lib/notesPermissions.ts`.
  `NoteMarkdown` renders bodies with react-markdown and no `rehype-raw`.

Design: `documentation/development/plans/2026-09-17-notes-design.md`.
```

- [ ] **Step 2: Update the phrasing reference and the spec**

In the phrasing reference's Property and Contact sections, find the `notes` update rows and change their description to "creates a Note authored by the acting user (notes v2)"; add a dated entry to the change log at the top of the file describing the switch; bump "Last updated". In the spec: set **Status** to `Implemented <date>`.

- [ ] **Step 3: Commit (ask first)** — two repos:

```bash
cd documentation && git add development/maple-phrasing-reference.md development/plans/2026-09-17-notes-design.md development/plans/2026-09-17-notes-plan.md
git commit -m "docs: notes v2 phrasing, spec status and plan

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

```bash
cd /Users/simon/Development/Tangz/3maples && git add CLAUDE.md
git commit -m "docs: describe the notes system in CLAUDE.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
