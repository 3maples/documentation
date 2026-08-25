# Concurrent updates: stop full-object writes from clobbering

> **Status:** approved 2026-08-24, ready to implement.
> Detecting *same-field* conflicts is deliberately out of scope and lives in its
> own, unscheduled plan:
> [2026-08-24-concurrent-update-conflict-detection.md](2026-08-24-concurrent-update-conflict-detection.md).

## Context

Two writers touching the same record today lose data, and not only in the
two-humans case that prompted this.

Six of the seven resources bind the **full Beanie `Document` as the request
body** and write `existing.set(payload.model_dump(exclude={"id","created_at"}))`.
An omitted field does not mean "leave it" — it resolves to the model default and
overwrites the stored value. The portal compounds this by sending the whole
object on every save, usually rebuilt from a snapshot loaded minutes earlier.

The scar tissue is already in the tree. [routers/tasks.py:277](platform/routers/tasks.py:277)
carries a hand-maintained 13-field exclusion list plus a `model_fields_set`
probe, and its comments name the bugs it was built to stop ("the portal's kanban
drag sends exactly that payload, which would wipe the id on every column move";
a single omission "used to lose both fields and rename the task to 'Untitled
task'"). [routers/properties.py:391](platform/routers/properties.py:391) has an
equivalent block preserving geocoded coordinates. Both are point fixes for one
structural problem, and the pattern will keep recurring per-field until the
write shape changes.

**The dominant risk is human-vs-Maple, not human-vs-human.** The median tenant
is 1–3 users on the Free plan, but *every* tenant has a second writer: the chat
agent. ~15 estimate agent call sites do whole-document `.save()` from a
possibly-stale in-memory copy. [agents/task/base.py:283](platform/agents/task/base.py:283)
explicitly refuses to do this and documents why — "a whole-document save from
this (possibly stale) copy would clobber concurrent photo uploads, converting
claims, or archived state" — but the estimate agents never got that treatment.
A user editing an estimate in the builder while asking Maple to change it is a
single-user data-loss path.

**Intended outcome:** concurrent edits to *different* fields both survive, on
every resource, from every writer (portal, Maple, direct API). That removes the
large majority of real-world loss without introducing locks, version tokens, or
any conflict UI.

### Consequence accepted in this plan

Two writers changing the **same** field still resolve silently to whoever saves
last, undetected. Fixing that is the separate conflict-detection plan, which is
not scheduled by this one.

### Rejected

- **Pessimistic locking.** Needs heartbeats and TTLs, strands on crash (the
  `Task.converting` claim already had to grow one for exactly this), and
  penalizes the solo user who is the median tenant. The one legitimate use —
  a genuinely exclusive long operation — already exists and is correct.
- **Do nothing.** Not tenable: Maple writes to every tenant's estimates, so this
  is not an edge case gated on team size.

## Approach

One recipe, applied uniformly. For each resource: accept a sparse DTO, merge the
patch onto the loaded document, run existing derivation/normalization against
the merged result, then `$set` only the patched keys plus whatever those
derivations changed.

```python
patch = payload.model_dump(exclude_unset=True, exclude=SERVER_OWNED)
merged = existing.model_copy(update=patch)      # normalize/derive against this
...                                              # geocode / markup / title, etc.
update = {**patch, **derived}
update["updated_at"] = datetime.now(timezone.utc)
await existing.set(update)
```

Two properties make this safe to land incrementally:

- **Backward compatible.** Every DTO field is `Optional` with `extra: "ignore"`,
  so a client still sending the whole object behaves exactly as today. The
  backend can ship before the portal.
- **`exclude_unset=True` is new here.** It appears nowhere in the codebase today;
  `model_fields_set` is used manually at 12 sites. Prefer `exclude_unset=True`
  for the dump and reserve `model_fields_set` for the absent-vs-empty checks that
  already exist.

Estimates already do this ([routers/estimates.py:982](platform/routers/estimates.py:982)
via `UpdateEstimateRequest`) and are the model to copy — including its one
inconsistency worth *not* copying: `title`/`approved_by`/`grand_total` use
`is not None` (so they can never be cleared) while `description`/`notes`/
`property` use `model_fields_set`. New DTOs should use set-ness uniformly.

## Work

TDD is mandatory (CLAUDE.md): write the failing test first for every step.

### 1. Fix `updated_at` — it is currently client-supplied

`@before_event([Replace, Insert])` does **not** fire for `.set()`; Beanie routes
`.set()` through `Document.update()`. Tasks and Estimates compensate by hand;
Contacts, Properties, Materials and Labour do not, so their `updated_at` is
whatever the client sent. A client echoing back a stale GET freezes it.

Server-stamp `updated_at` inside every `.set()` payload, and add it to the
server-owned exclusion set so a client value is always ignored. Do this first —
later steps depend on the timestamp being trustworthy.

Files: `routers/{contacts,properties,materials,labours}.py`.

### 2. Sparse update DTOs

Add an `Update<X>Request` per resource, all fields `Optional`,
`model_config = {"extra": "ignore"}`, retaining existing field validators so a
patch can't write an empty `first_name`. Apply the recipe above.

| Resource | File | Preserve |
|---|---|---|
| Contact | [routers/contacts.py:199](platform/routers/contacts.py:199) | — (barest case) |
| Material | [routers/materials.py:464](platform/routers/materials.py:464) | `_normalize_material_payload` against `merged` |
| Labour | [routers/labours.py:301](platform/routers/labours.py:301) | `_normalize_labour` against `merged`; also fix the bare `return None` on 404, which violates `response_model` |
| Property | [routers/properties.py:372](platform/routers/properties.py:372) | re-geocode only when an address field is *in the patch* and changed; drop the coordinate-preservation block, which becomes unnecessary |
| Task | [routers/tasks.py:250](platform/routers/tasks.py:250) | title derivation when `description` is patched; the exclusion list collapses into `SERVER_OWNED` |

Server-owned everywhere: `id`, `created_at`, `updated_at`, `company`,
`created_by_email`. Plus for Task: `readable_id`, `title`, `task_date`,
`photos`, `estimate`, `converting`, `converting_since`, `archived`.

The Task handler's `model_fields_set` description probe and the Property
coordinate block are the two point fixes this step retires — delete them rather
than leaving both mechanisms in place.

### 3. Maple estimate agents: whole-document `.save()` → targeted `.set()`

Generalize [agents/task/base.py:283](platform/agents/task/base.py:283)
(`_apply_task_update`) into a shared helper and route every estimate agent write
through it, so `job_items`/`grand_total`/`status` changes stop replacing the
whole document from a stale copy.

Sites: `agents/estimate/work_item_field_handlers.py` (7), `work_item_handlers.py`
(5), `crud_handlers.py` (lines 677, 795, 2835, 2910, 2949, 2996, 3217),
`assumption_handlers.py:229`, `routers/agent_helpers/template_estimate.py:152`.

### 4. Maple material/labour/contact agents: stop rebuilding whole documents

[agents/material/service.py:632](platform/agents/material/service.py:632) and
[agents/labour/service.py:383](platform/agents/labour/service.py:383) construct a
**brand-new** `Material`/`Labour` from LLM-extracted fields and hand it to the
router function — so any field the LLM didn't extract is written back as a model
default. [agents/contact/service.py:698](platform/agents/contact/service.py:698)
does the same inline. Pass the new sparse DTO carrying only extracted fields;
Step 2 then makes the omissions harmless.

### 5. Portal: send only what changed

Add `portal/src/lib/diffPayload.ts` — shallow diff of current form state against
the originally-loaded object, deep-equal for arrays/objects, returning only
changed keys. Every dialog already retains the loaded object (`editingContact`,
`currentTask`, …) to diff against.

Wire into the save handlers: `TaskDialog.saveTask` ([TaskDialog.tsx:400](portal/src/components/tasks/TaskDialog.tsx:400)),
`ContactsPage:513`, `PropertyDialog:184`, `MaterialsPage:339`, `PeoplePage:162`.
`EquipmentsPage:166` shares the pattern — include it for consistency.

The API client needs no change: [client.ts:231](portal/src/api/client.ts:231)
already carries arbitrary bodies, and `ApiError` already exposes `.status`.

### 6. Two stale-snapshot quick wins

- [TasksPage.tsx:371](portal/src/pages/TasksPage.tsx:371) `handleMoveTask`
  re-PUTs a whole stale row to change one column. Send `{ status: newStatusId }`.
  This is the single highest-value line in the plan — the shared kanban is the
  one place two humans genuinely collide, and the payload is built from whatever
  `loadTasks()` last returned. It also currently swallows the error object.
- [NewEstimateWithActivityPage.tsx:937](portal/src/pages/NewEstimateWithActivityPage.tsx:937)
  `handleSaveEstimate` always sends `job_items`, so a title-only save rewrites
  every work item from the local snapshot. Send `job_items` only when work items
  actually changed.

### 7. Log the deferred items

Append to `documentation/development/code-review-followups.md`: stable `JobItem`
ids, and the `Company`/Stripe-webhook race (6 whole-document `company.save()`
calls in `services/billing/webhook_handlers.py` racing with Settings edits).
Cross-reference existing item #59, which already proposes optimistic concurrency
keyed on `estimate.updated_at`, and point it at the conflict-detection plan.

## Residual risk (accepted in this scope)

- **Same-field concurrent edits** still resolve silently to the last writer, with
  no detection.
- **Work items remain whole-array replace.** `JobItem` has no id — items are
  addressed positionally, and both `WorkItemSummary` (keyed `(estimate_id,
  job_item_index)`) and the `unmatched_*` carry-forward in
  [workItemV2.ts:162](portal/src/lib/workItemV2.ts:162) depend on that ordering.
  Step 6 narrows the window (title-only saves stop touching work items) but two
  people editing *different work items in the same estimate* still lose one set.
- **The estimate builder never refetches.** Its load effect depends only on
  `[estimateId]`, and it ignores the existing `portal:estimates:changed` bus that
  every list page listens to — so Maple can rewrite an estimate the builder has
  open and the builder will PUT its stale snapshot over the top. A ~10-line
  follow-up if it bites.

## Verification

Backend, per CLAUDE.md gates:

```bash
cd platform && ./run_tests.sh tests/test_task_api.py tests/test_contacts_api.py tests/test_properties_api.py tests/test_materials_api.py tests/test_labours_api.py tests/test_estimate_api.py
```

```bash
cd platform && ./run_mypy.sh routers && ./run_ruff.sh routers agents
```

Tests to write first, per resource:
- a partial PUT leaves unsent fields untouched (the core regression);
- a two-writer sequence — load, writer A patches field X, writer B patches
  field Y from the *original* snapshot — leaves both X and Y set;
- a client-supplied `updated_at` is ignored and the server value advances;
- Maple agent writes touch only the intended fields (assert on the resulting
  `$set`, mirroring the existing task-agent tests).

Frontend:

```bash
cd portal && npm test -- diffPayload TaskDialog TasksPage && npm run typecheck
```

End-to-end sanity, which is what the whole plan is for: open a task in the
portal, ask Maple to change its status in the chat panel, then save an unrelated
description edit from the still-open dialog — both changes should survive.

Do not run the full suite or add a changelog entry; both are user-triggered.
