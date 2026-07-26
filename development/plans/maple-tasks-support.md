# Maple Tasks Support — Phrasing Reference + Task Agent

> On implementation start, copy this plan to `documentation/development/plans/` (per project convention).

## Context

Tasks shipped as a full platform feature (model, CRUD API, per-company statuses, quota, photos, convert-to-estimate, portal UI) but Maple has zero Task awareness: no `agents/task/` package, no `task` domain in the orchestrator's intent registry, no Task rows in the phrasing reference. Users can't ask Maple to do anything with Tasks.

Confirmed scope (Simon): core CRUD **plus** status changes, assignee operations, convert-to-estimate, archive/unarchive, and **manager-only** single-task delete (bulk delete always refused). Task referencing three ways — relative ("last task", "from yesterday"), by title (fuzzy), by property — with a confirmation question when ambiguous. Once identified, the task becomes Maple's **active task**; follow-ups ("mark it done", "convert it") act on it. Explicit reference in a message must beat active-task context (don't repeat the estimate title-vs-active latent bug).

TDD mandatory (failing tests first); mypy + ruff zero-error gates after every phase; backend + documentation repos only.

## Verified architecture facts

- **Persistence exists — reuse it.** `models/task.py` (title, task_date, description, property ref, due_date, status→`TaskStatus` ref, assigned_to_email, archived, company; photos/convert/created fields server-owned), `models/task_status.py` (defaults To Do/In Progress/Done; `ordered_statuses`, `ensure_default_statuses`), `routers/tasks.py` (CRUD + convert + archive; DELETE manager-only with GridFS cascade; all behind `settings.tasks_enabled`; create enforces `is_task_limit_reached` — free plan cap 50).
- `agents/orchestrator/intents.py:4` — `SUPPORTED_INTENTS_BY_AGENT` is the master registry; `INTENT_TO_AGENT` inverted; intent convention is strictly `{action}_{singular}` / `list_{plural}`; LLM classifier auto-derives allowed intents from `INTENT_TO_AGENT`. Count folds into `list_*`; estimate status transitions fold under `update_estimate` (precedent for tasks).
- `current_user_email` / `current_user_role` are injected into merged_context at `routers/agents.py:971-983`, stripped before persistence (`_PER_REQUEST_IDENTITY_KEYS`). Manager-gate precedent: `agents/template/service.py:283 _assert_manager_role` (context role → `User.firebase_uid` DB fallback, OWNER/ADMIN).
- `is_bulk_delete_request` (`agents/text_utils.py:263`) is domain-agnostic and runs pre-classification — "delete all my tasks" is already refused; just lock with a test.
- **No vocabulary collision**: estimate work items are never called "task" anywhere in `agents/estimate/` (verified by grep); the word is unclaimed in `DOMAIN_HINTS`.
- `routers/agent_helpers/finalize_result.py:42` — entity loop `("contact","property","material","labour","estimate")` writes `active_{type}_id/_name`; `title` already feeds entity_name. Add `"task"`.
- Disambiguation pattern to copy: `routers/agent_helpers/estimate_resolver.py` (context → code → id → fuzzy 0.65/0.80 via `agents/fuzzy_utils.py` → recency fallback gated off for destructive ops) + `fuzzy_confirmation.py` pending-confirmation state machine.
- `create_audit_log` accepts `request=None` + explicit `user_email`/`user_role` (agents already call it that way) — convert logic can move to a service without losing audit.
- Day-boundary date parsing ("yesterday") is net-new; relative windows exist only in `agents/estimate/text_helpers.py::_parse_estimate_date_filter`. All datetimes aware-UTC (never `utcnow()`).
- Coverage matrix: `tests/_maple_coverage_data.py` — `RESOURCE_TOKENS`, `_CRUD_RESOURCES` (adding "task" auto-generates 27 generic cases), `_implicit_relationship` per-resource ladder, `_EXPECTED_AGENT_BY_INTENT_PREFIX`. Test file + gap report generic — no changes.
- Phrasing doc: resources §1–§6; Tasks becomes new **§7**, old §7–§12 renumber to §8–§13 (precedent: Templates addition). Skeleton X.1…X.last per resource, tags ✅/🤖/⚠️/🛑, change-log entry + **Last updated** bump.

## Phases

### Phase A — Phrasing doc, all rows ⚠️ (documentation repo, doc-only commit)

`documentation/development/maple-phrasing-reference.md`:
1. Insert **§7 Tasks** after §6; renumber old §7–§12 → §8–§13 and fix every intra-doc `§` cross-reference (grep for `§7`–`§12`, `## 7.`–`## 12.`).
2. §7 sub-sections (each row initially ⚠️ gap; flipped in Phase E):
   - **7.1 Direct imperatives** — create a task called {title} / list my tasks / show me the {title} task / delete the {title} task
   - **7.2 Casual** — jot down a task… / I need to remember to… / pull up my tasks / what tasks do I have
   - **7.3 Possessive** — the {title} task's due date / update {title}'s description
   - **7.4 Count** — how many tasks do I have / how many open tasks (status-filtered)
   - **7.5 Filter / find** — tasks at {address} (property) / tasks assigned to {email} / my tasks / tasks in progress / archived tasks / tasks due this week
   - **7.6 Field-targeted update** — change the due date of {title} to Friday / add a description to the last task / rename the task to {new}
   - **7.7 Status changes** — mark it as done / move {title} to In Progress / set status to {custom}; per-company `TaskStatus` name resolution + clarification listing statuses on no-match
   - **7.8 Assignee** — assign this to {email} / reassign to me / who is the {title} task assigned to
   - **7.9 Archive/unarchive** — archive that task / unarchive it / show archived tasks
   - **7.10 Convert to estimate** — convert this task to an estimate / turn the {title} task into a quote; documents the confirm step (consumes an estimate credit) and 402/429 refusal copy
   - **7.11 Referencing & anaphora** — last/latest task, the task from yesterday, {title} fuzzy, the task at {address}, disambiguation flow, active-task follow-ups
   - **7.12 Refusals 🛑** — bulk delete, non-manager delete, convert with empty description, feature flag off, 50-task free-plan cap
   - **7.13 Gaps** — residuals
3. Change-log entry, **Last updated** bump, note in renumbered §12.1/§12.3 that matrix counts are stale pending Phase E.

Commit: `docs: add §7 Tasks phrasing matrix (all rows ⚠️ pending implementation)`

### Phase B — Orchestrator routing + core CRUD Task Agent

**Tests first**: new `tests/test_maple_task_routing.py` (rule classification: create/list/count/get/delete routing, bulk-delete refusal lock, plural-flip "find tasks about fencing" → `list_tasks`) and new `tests/test_maple_task_crud.py` (mirror `test_maple_template_crud.py`: create happy-path + quota-cap refusal + flag-off refusal, get, list, update title/description/due-date, delete manager-allowed vs non-manager 🛑, photo-cascade parity).

1. `agents/orchestrator/intents.py` —
   `SUPPORTED_INTENTS_BY_AGENT["Task Agent"] = ["create_task", "update_task", "delete_task", "list_tasks", "get_task", "convert_task"]`.
   Status/assignee/archive fold under `update_task` (mirrors estimate-status precedent); `convert_task` is its own intent (distinct confirm + billing semantics). Entity dicts: singular/plural "task"/"tasks"; `PLURAL_DOMAIN_TOKENS["task"] = ("tasks", "to-dos", "todos", "to dos")`; `DOMAIN_HINTS["task"]` narrow: task/tasks/to-do/todo (leave "reminder"/"chore" to the LLM). Add `is_task_convert_request(text)` detector (regex `\b(convert|turn)\b…\btask\b…\b(estimate|quote)\b`, plus "convert it/this to an estimate" when active-task context exists).
2. `agents/orchestrator/service.py` — wire the convert detector into `_classify_with_rules` before generic action/domain resolution; the rest (fast-path, ≥0.9 override, bulk-delete guard) keys off the registries — verify via routing tests, no task-specific code expected.
3. `agents/orchestrator/domain_knowledge.py` — new Tasks block: intents, trigger words, required-for-create (title; task_date defaults now), optional (description, due date, property, assignee), per-company statuses, "mark done/assign/archive ⇒ update_task", "convert ⇒ convert_task", follow-up suggestions.
4. **New `agents/task/` package** — `__init__.py` (exports `TaskAgent`), `service.py` (structure like `agents/template/service.py` with the `agents/property/service.py` dispatch shape: defensive bulk-delete check → `settings.tasks_enabled` gate with friendly refusal → pending-confirmation gate (Phase C) → intent resolution → dispatch), `text_helpers.py` (title extraction incl. quoted, bare-field matcher for title/description/due date/status/assignee, due-date phrase parse). Handlers: `_handle_create_task` (quota check first, friendly 50-cap copy), `_handle_get_task`, `_handle_list_tasks` (count phrasing → `format_count_response`; regex search parity with `routers/tasks.py::get_tasks`), `_handle_update_task` (field-then-value stash via `pending_intents` + `awaiting_value_for`), `_handle_delete_task`. All queries company-scoped; friendly first-person templates per CLAUDE.md.
5. **Shared manager gate** — extract template agent's `_assert_manager_role` into `agents/role_utils.py::assert_manager_role(working_context)` (context `current_user_role` first, `user_id`→`User.firebase_uid` DB fallback); template agent switches to it; Task delete uses it. Non-manager copy: "Only owners and admins can delete tasks. You can archive it instead — want me to do that?" Delete parity with REST: cascade `services/task_photos.py::delete_photo_blobs`, audit `TASK_DELETE` via `create_audit_log(request=None, …)`.
6. Wiring — `agents/__init__.py` export; `routers/agents.py`: singleton `get_task_agent()`, `"Task Agent"` in `IMPLEMENTED_CHAT_AGENTS`, `_get_processor` branch (generic delegation via `delegate_generic` unchanged).

Commit: `feat: Task Agent core CRUD + orchestrator routing`

### Phase C — Reference resolution, disambiguation, active-task context

**Tests first**: new `tests/test_task_resolver.py` (resolution-order unit tests incl. explicit-beats-context precedence, recency, yesterday-window, property lookup, fuzzy single/multi, recent-fallback gated off for delete/convert, company isolation) and new `tests/test_maple_task_context.py` (multi-turn E2E: create → "add a description to it" → "mark it done"; `active_task_*` written by finalize; delete clears them; ambiguity → numbered candidates → affirmative/negative/unrelated handling). Extend `test_maple_task_crud.py` update/delete to use references.

1. **Day-window helper (net-new, shared)** — `agents/text_utils.py::parse_relative_day_window(text, *, now=None) -> Optional[Tuple[datetime, datetime]]`: "yesterday", "today", weekday names, "N days ago" → aware-UTC `[start, end)` bounds. Docstring notes estimate `_parse_estimate_date_filter` can delegate later — no estimate refactor now.
2. **Resolver — new `agents/task/resolver.py`** — `find_task_from_context_or_message(message, company_id, context, *, allow_recent_fallback=True) -> TaskResolution` (dataclass: task, is_fuzzy, candidates). Order:
   1. Explicit reference in message wins (quoted/bare title, ObjectId, property phrase, date phrase) → skip context
   2. `active_task_id` from context (exact)
   3. 24-hex ObjectId in message
   4. "last/latest/most recent task" (+"my" also filters `assigned_to_email == current_user_email`) → `updated_at` desc limit 1
   5. Day window via `parse_relative_day_window` on `task_date` (fallback `created_at`); 1 hit resolves, N → candidates
   6. Property phrase → `agents/cross_resource.py::find_properties_by_name_or_address` → tasks with that property id; 1/N as above
   7. Fuzzy title via `agents/fuzzy_utils.py::fuzzy_best_matches` (0.65/0.80, stop-word list incl. task verbs: mark/done/assign/archive/convert)
   8. Recency fallback only when `allow_recent_fallback=True` (delete/convert pass `False`)
3. **Pending confirmation** — context key `pending_task_confirmation` `{task_id|candidate_ids, intent, sub_op, original_message, title}`, handled agent-level at top of `process()` (template-agent style): affirmative → re-fetch + dispatch; numbered/name reply picks a candidate; negative → clear + acknowledge; unrelated message → clear + fall through. Used for fuzzy confirms on mutating ops, multi-candidate disambiguation, delete confirm, convert confirm (Phase D). Clear after dispatch (avoid double-fire).
4. **Active-task plumbing** — `finalize_result.py:42`: add `"task"` to the entity tuple (title feeds name already); `_handle_delete_task` returns flat result (no nested `task` dict) and pops `active_task_id`/`active_task_name` from returned context. `agents/orchestrator/service.py`: add `("active_task_name", "Active task")` to `_build_entity_context_summary` and task entries to `_resolve_domain_from_history` (ordered **after** estimate to preserve existing anaphora precedence). Create/get/update handlers return nested `task` dict so finalize sets the keys automatically.

Commit: `feat: task reference resolution, disambiguation, active-task context`

### Phase D — Status, assignee, archive, convert-to-estimate

**Tests first**: new `tests/test_maple_task_operations.py` (status resolution exact/case-insensitive/fuzzy + unknown-status clarification listing `ordered_statuses` + first-status/None equivalence; "my tasks" filter, assign to email/"me"; archive/unarchive + archived-tasks listing; convert confirm-then-convert, empty-description/402/429/409 friendly copy, estimate re-link, `active_estimate_code` handoff). Existing `tests/test_task_convert_api.py` must pass **unmodified** — the regression gate for the extraction.

1. Sub-handlers under `update_task` in `agents/task/service.py`: `_handle_task_status_change` (`ensure_default_statuses` then `ordered_statuses` name match), `_handle_task_assign` (email or me/myself → `current_user_email`; REST parity — no team-membership validation, matches API), `_handle_task_archive` (archive/unarchive verbs; `list_tasks` gains archived filters).
2. **Convert extraction — new `services/task_convert.py`**: move the core of `routers/tasks.py::convert_task_to_estimate` into `run_task_conversion(task, company_doc, *, created_by_email, delete_task=False, request=None, decoded_token=None, source="api") -> Estimate` (atomic converting claim, `claim_estimate_slot_with_status` 402/429, estimate generation, slot/claim release on failure, re-link, both audit logs). Router becomes a thin wrapper. Keep raising `HTTPException` (lowest churn).
3. `_handle_convert_task`: resolve with `allow_recent_fallback=False` → refuse if description empty ("I need a description on the task before I can generate an estimate — want to add one?") → **always confirm** ("Converting '{title}' will generate a new estimate and uses one of your included estimates — go ahead?") → on yes call `run_task_conversion`, map 402/429/409/422 to friendly first-person copy → response includes new estimate code; return nested `estimate` dict so finalize sets `active_estimate_code` (natural handoff to estimate follow-ups).

Commit: `feat: task status/assignee/archive ops + convert-to-estimate via Maple`

### Phase E — Coverage matrix + doc flip

1. `tests/_maple_coverage_data.py`: `RESOURCE_TOKENS["task"]` (name "fix the fence gate", filter "fence", location "123 Main St", field "due date", field_value "Friday"); add `"task"` to `_CRUD_RESOURCES` (+27 generic cases); `task` branch in `_implicit_relationship`; `"task"/"tasks" → "Task Agent"` in `_EXPECTED_AGENT_BY_INTENT_PREFIX`; new `task_operations` category (status/assign/archive/convert phrasings) scoped `("task",)`. Run Tier 1 + Tier 2; promote passing known-gap cases into `_CONFIRMED_WORKING_CASE_IDS`.
2. Doc flip: §7 rows → ✅/🤖 per actual gap-report results; residuals stay ⚠️ in §7.13; update matrix score in renumbered §12.1/§12.3; change-log entry + **Last updated** bump.

Commits: platform `test: add tasks to Maple CRUD coverage matrix`; documentation `docs: flip §7 Tasks rows to shipped status`.

## Test plan summary

| File | Phase | Kind |
|---|---|---|
| `tests/test_maple_task_routing.py` (new) | B | Tier-1 rule classification |
| `tests/test_maple_task_crud.py` (new) | B/C | Agent behavior |
| `tests/test_task_resolver.py` (new) | C | Resolver units (DB fixtures) |
| `tests/test_maple_task_context.py` (new) | C | Multi-turn E2E |
| `tests/test_maple_task_operations.py` (new) | D | Status/assign/archive/convert |
| `tests/test_task_convert_api.py` (existing) | D | Must pass unmodified (extraction gate) |
| `tests/_maple_coverage_data.py` (extend) | E | Coverage matrix |

After each phase: `./run_mypy.sh` + `./run_ruff.sh` scoped to touched subtrees, related tests via `./run_tests.sh tests/<file>` (local test Mongo via `./scripts/start_test_mongo.sh`). Commit/push per phase only with explicit approval.

## Decisions encoded / residual risks

- **"Add a task to the estimate"** — routes to Task Agent (verified no estimate work-item vocabulary collision); Task Agent's create handler will notice "to/for the estimate {ref}" and, since Task has no estimate-create link, offer redirection ("Did you mean a work item on the estimate?"). Documented in §7.13.
- **Assignee email validation** — REST parity (no team-membership check) now; soft warning is a possible follow-up.
- **Status-name collision with estimate statuses** ("mark it as approved" with both active estimate and active task) — `_resolve_domain_from_history` priority (task after estimate) decides; locked with a test in `test_maple_task_context.py`.
- **Translation sandwich** — no changes needed; status resolution matches per-company DB names, inherently language-agnostic.
- **Double "convert it"** — 409 converting-claim path gets friendly "already being converted" copy; pending confirmation cleared after dispatch.

## Verification (end-to-end)

1. `./run_tests.sh` on all new/extended test files per phase (Tier 1 default; Tier 2 via `-m ""` with `OPENAI_API_KEY` for the coverage matrix, ~$0.05).
2. Manual smoke via portal chat (Dev cluster): create a task → "add a description to it" → "mark it done" → "assign it to me" → "convert it to an estimate" (confirm flow) → verify estimate link + `active_estimate_code` handoff; ambiguity case with two similar titles → numbered clarification; "delete all tasks" → refusal; non-manager delete → refusal.
3. Regenerated `tests/reports/maple_crud_gap_report.md` shows task rows; phrasing doc §7 statuses match it.
