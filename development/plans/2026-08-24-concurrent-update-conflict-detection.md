# Conflict detection for Estimates and Tasks (409)

## Context

Depends on the sparse-writes plan
(`2026-08-24-concurrent-update-sparse-writes.md`) having landed. That plan makes
concurrent edits to *different* fields survive; this one detects the remainder —
two writers changing the *same* field — and surfaces it instead of losing one
silently.

Scope is **Estimates and Tasks only**. Estimates because Maple writes to them
for every tenant and the builder holds edits open for minutes; Tasks because the
shared kanban is where two humans actually collide. The catalogs (Contacts,
Materials, Labour, Properties) stay on sparse-writes-only.

## The trap to avoid

A naive strict version precondition would 409 on exactly the non-overlapping
edits the sparse-writes plan just made safe — a visible regression. The
precondition failing is **not** the conflict; it only means "someone wrote since
you loaded." The write must auto-merge when the two writers touched different
fields, and escalate only on genuine overlap.

## Work

### 1. Version field + backfill

Add `version: int = 0` to `Task` and `Estimate`. A one-shot
`scripts/backfill_document_versions.py` sets `version: 0` where the field is
missing, following the existing `scripts/backfill_*.py` precedent — needed
because a `{"version": 0}` filter does not match a document that lacks the field.

### 2. Conditional write with no-overlap auto-merge

Replace `existing.set(update)` with the house conditional-write idiom from
[services/task_convert.py:77](platform/services/task_convert.py:77):

```python
result = await Model.get_pymongo_collection().find_one_and_update(
    {"_id": oid, "version": base_version},
    {"$set": update, "$inc": {"version": 1}},
    return_document=ReturnDocument.AFTER,
)
```

On `None`, resolve rather than reject:

1. Determine which fields changed since `base_version` (§3).
2. **No overlap with the patch keys** → re-read and retry against the current
   version. The user sees nothing; both edits survive. Bound the loop at 3
   attempts to avoid livelock, then fall through to (3).
3. **Overlap** → `409` with the conflicting field names.

`base_version` travels as an optional body field, not an `If-Match` header:
the codebase has no header conventions, and making it optional keeps
unversioned callers (Maple, scripts, any direct API client) working unchanged.
Those callers skip the precondition — acceptable because after the sparse-writes
plan they write targeted `$set`s and re-read immediately before writing, so their
window is tiny. Note this in the module docstring so it is a decision, not an
oversight.

### 3. Determining what changed since `base_version`

Reuse the audit trail rather than adding per-field version columns. Record the
resulting `version` in the audit entry's `metadata` at write time, then union
the `changes` keys of entries for this resource with `metadata.version >
base_version`. [services/audit_service.py:88](platform/services/audit_service.py:88)
already computes that field-level diff, and `AuditLog` already indexes
`(resource_type, resource_id)`.

**Degrade honestly.** Audit logging is fail-open and can be disabled
(`settings.audit_logging_enabled`), and `audit_log_level = "minimal"` records no
`changes` at all. When the changed-field set cannot be determined, do **not**
auto-merge — report a document-level conflict. Cover both configurations in
tests so the degraded path is pinned.

### 4. The 409 payload

Return a structured detail the portal can render: the conflicting field names,
who made the competing change and when (`user_email` / `timestamp` from the same
audit entries), and the current server version so a deliberate overwrite can
re-submit. Extend `parseErrorPayload` in [client.ts:263](portal/src/api/client.ts:263)
to carry it through; `ApiError` already exposes `.status` and `.code`.

### 5. Portal conflict UX — keep the user's edits

Never discard in-progress work. On 409, keep local state intact and show:
*"Maple changed the description while you were editing."* with **Reload** (refetch
and lose local edits, on explicit click) and **Save anyway** (re-submit with the
current server version).

Wire the rich path into the surfaces where edits are long-lived and losing them
hurts: the estimate builder's whole-save, work-item dialog, notes dialog and
field auto-save, plus `TaskDialog`. The other ~15 `catch { setXError(msg) }`
blocks need no change — they surface the 409 message inline as they would any
other error. Two are worth fixing in passing: `TasksPage.tsx:387` and
`RateCardsTab.tsx:123` currently discard the error object entirely, so a conflict
message would be lost.

Send `version` from the loaded object as `base_version` in each save payload — a
natural extension of the `diffPayload` helper.

## Residual risk

Work items remain a whole-array replace, so two people editing *different work
items in the same estimate* both patch the `job_items` key and register as a
genuine conflict. Coarse but honest — a visible conflict instead of silent loss —
and the strongest argument for giving `JobItem` stable ids.

## Verification

- stale `base_version` + non-overlapping fields → succeeds silently, both edits
  present, `version` incremented twice;
- stale `base_version` + overlapping field → 409 naming that field and the
  competing editor;
- `Save anyway` with the current version succeeds;
- audit logging disabled and `audit_log_level="minimal"` → document-level
  conflict, never a silent auto-merge;
- the retry loop terminates under sustained contention.

End-to-end: open an estimate in the builder, have Maple edit the description,
then edit the description locally and save — expect the conflict notice with the
user's text still in the box.
