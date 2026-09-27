# Maple: multi-turn Estimate and Work Item editing

> Execute phase by phase with `superpowers:executing-plans`; TDD, `./run_mypy.sh` + `./run_ruff.sh` scoped after every `.py` edit, `npm test -- <file>` after every portal edit. Every commit/push needs explicit approval. Original plan approved 2026-09-23.

## Context

Maple can already create estimates, list/get/count them, change status, rename, set description, link a property, add estimate notes, and on work items: add, rename, remove (with confirmation), describe, set division, toggle recurring, add/remove/list materials and activities, override the total, and rescale assumptions. What it cannot do reliably is **keep working on the same estimate across turns**, and several manual actions have no chat equivalent.

Root causes found in exploration (all verified in code):

1. **The portal never tells Maple which estimate is open.** `useMapleAgent.ts:88-98` listens for `portal:estimate:loaded`, but nothing dispatches it. The active-estimate anchor is only ever set by Maple's own actions.
2. **The client owns the context.** `routers/agents.py:1032` merges `request.context` *over* the persisted `ConversationContext`, and the portal echoes the entire previous context back every turn. Stale pending/active keys resurface, and a crafted `active_estimate_id` or `pending_estimate_fuzzy_confirmation.estimate_id` is loaded with **no company check** (`estimate_resolver.py:56-63`, `fuzzy_confirmation.py:167`). That is a cross-tenant security bug.
3. **Two resolution orders.** The agent resolves explicit code → named title → positional pick → active → latest (`crud_handlers.py:2003`). The router resolver used by delete/update checks the active anchor *first* (`estimate_resolver.py:144`), and `delegate_get_estimate.py:102` ignores the anchor entirely, so "show this estimate" fails.
4. **`active_estimate_id` goes stale.** `finalize_result.py:65-73` sets only `active_estimate_code` from flat results.
5. **No work-item memory.** No active-work-item anchor; work-item lists are not recorded into `last_listed_items`; "Which work item?" answers are not stored; the estimate agent has no `awaiting_value_for` (only property/contact agents do).
6. **Missing operations.** Update material qty/price and activity role/effort/rate fall through to list handlers (`crud_handlers.py:2380/2386`); markup/overhead/tax are refused by design (`text_helpers.py:901-915`); no work-item notes; no gross margin; the AI add-scope path is unreachable from `/orchestrate` because `orchestrator_intent` is stamped before `run_update_estimate` re-enters the agent.
7. **Set-total is wrong.** `_handle_work_item_set_total` writes `sub_total` directly (`work_item_field_handlers.py:1164`); the next portal save recomputes and discards it. The portal back-calculates markup instead.

**Decisions made with Simon (2026-09-23):** rules first with an LLM edit-planner fallback; markup/overhead/tax applied directly (no confirm step); active estimate = most recent signal wins (page navigation or Maple action, explicit name always overrides); in scope: gross margin %, AI-generated work item into an existing estimate, work-item notes, robust material/activity add/update/remove. **Out of scope:** inventory-gap resolution, reorder/duplicate work items, equipment, labor burden, discount, document generation.

**Precondition:** `platform/` has uncommitted work (untracked `agents/estimate/note_handlers.py`, edits to `crud_handlers.py`, `service.py`, `text_helpers.py`, plus doc-image files). Commit that first (ask) so each phase starts clean. Nothing below conflicts with it.

## Phase overview

| # | Ships | Why here |
|---|---|---|
| 0 | Server-owned context, allowlisted `client_context`, company-scoped estimate loads | Security fix; every later phase reads keys that must be trustworthy |
| 1 | Reliable "this estimate": portal view signal, turn-ordered anchor, one resolution order, get-estimate fix, looser titles, portal refetch | Prerequisite for every follow-up turn |
| 2 | Work-item anchor, work-item lists as positional picks, stored menus, field-then-value pending | Prerequisite for "which work item" and for the planner snapshot |
| 3 | `EditCommand` schema + single executor; migrate existing handlers onto it; port margin math | Foundation so gaps are written once and the planner has a typed target |
| 4 | Fill CRUD gaps on the executor | Feature delivery |
| 5 | Worker-model edit planner as fallback | Replaces the "What would you like to change?" dead end |
| 6 | Phrasing reference, matrix, user guide, CLAUDE.md | Documentation contract |

Each phase is independently shippable and ends with green Tier 1 tests.

---

## Phase 0: Context hardening and company scoping

**Behavior**
- Server is the only writer of `ConversationContext.context`. Client sends a small allowlisted `client_context`. Legacy `context` accepted for one release but filtered through the same allowlist (dropped keys logged at debug).
- Server appends the user turn to `chat_history` itself (dedupe if last entry is identical user text). Portal stops sending history.
- Every estimate load driven by an id from context or a pending record is scoped by the authenticated company.

**Shapes** (pydantic, `extra="ignore"`)
```
ClientContext:
  source: Optional[str]                        # max 64
  current_path: Optional[str]                  # max 512
  viewed_estimate: Optional[ViewedEstimateSignal]   # consumed in Phase 1
ViewedEstimateSignal:
  id: str     # 24-hex Mongo _id from /estimates/:id/with-activity
  at: int     # client ms nonce (page-load time); ordering is by turn, not clock
```
Transient keys stripped before persistence: extend `_PER_REQUEST_IDENTITY_KEYS` in `finalize_result.py:39` into `_TRANSIENT_KEYS` adding `viewed_estimate`.

**Files**
| File | Change |
|---|---|
| `platform/routers/agents.py` | `OrchestratorAgentRequest.client_context`; replace `merged_context.update(dict(request.context or {}))` (:1032) with `apply_client_context(merged_context, request)`; append user turn to `chat_history` before dispatch |
| `platform/routers/agent_helpers/context_scope.py` | Add `load_company_estimate(estimate_id, context_payload)` = `Estimate.find_one(id == oid, company == company_oid)` using existing `to_object_id` / `company_oid_from_context` |
| `platform/routers/agent_helpers/estimate_resolver.py` | `_from_active_context`, `_from_object_id` use `load_company_estimate` (today: unscoped `Estimate.get`) |
| `platform/routers/agent_helpers/fuzzy_confirmation.py` | :167 scoped load; ignore `pending["company_id"]`/`company_ctx` in favor of the verified `context_payload["company_id"]` |
| `platform/routers/agent_helpers/delegate_get_estimate.py` | Mongo-id rung (:145) scoped |
| `platform/routers/agent_helpers/finalize_result.py` | `_TRANSIENT_KEYS` |
| `portal/src/components/Layout/useMapleAgent.ts` | Drop `aiContext` state and the echo (:176-183); send `client_context: {source, current_path, viewed_estimate}`; keep restore-on-mount |
| `portal/src/api/agents.ts` | Payload type |

Before removing the legacy `context` field, grep `platform/routers/public_maple.py` and every `context_payload.get(` / `working_context.get(` reader for keys that only ever came from the client.

**Tests**
- `tests/test_orchestrator_endpoint.py`: `test_client_context_cannot_set_active_estimate_id`, `test_legacy_context_keys_are_dropped`, `test_server_appends_user_turn_to_chat_history`, `test_user_turn_not_duplicated_on_retry`
- `tests/test_agent_helpers_estimate_resolver.py`: `test_active_context_id_from_other_company_returns_none`
- `tests/test_agent_helpers_fuzzy_confirmation.py`: `test_confirmed_delete_refuses_cross_company_pending_id`
- `tests/test_agent_helpers_context_scope.py`: `test_load_company_estimate_scopes_by_company`
- portal `useMapleAgent.test.ts` (new): sends only allowlisted keys; does not echo previous context

**Risk:** a reader that relied on a client-supplied key silently stops getting it. The one-release deprecation window plus the grep above catches stragglers.

---

## Phase 1: Active-estimate reliability

**Anchor keys** (persisted, server-written only)
```
active_estimate_id, active_estimate_code, active_estimate_name   (existing)
active_estimate_source: "portal_view" | "maple"
active_estimate_set_at: ISO str                                    (observability)
last_viewed_estimate: {id, at} | null    # nonce of the last portal signal processed
```

**Most-recent-signal-wins, ordered by turn**
1. Each turn, if `client_context.viewed_estimate` is present and `(id, at)` differs from `last_viewed_estimate`, the user navigated since the last turn: verify the estimate exists in the company (scoped `find_one`, projection `estimate_id,title,status`), set the anchor with `source="portal_view"`, record the nonce, clear `active_work_item` (Phase 2) if the estimate changed. If the signal is unchanged, the persisted anchor stands, including one Maple set on a later turn.
2. An explicit code or named title in the message wins for that turn.
3. A successful Maple action re-anchors via `finalize_result` (`source="maple"`).
4. `viewed_estimate: null` (user left the page) is recorded as the nonce so revisiting the same estimate is a fresh signal. Leaving does not clear the anchor.
5. New chat (`DELETE /agents/conversation`) drops everything; the next message re-anchors from the page signal.

**One resolution order (router and agent)**
1. Explicit E-code in message (ends the search; unknown code → "couldn't find E0099").
2. Raw Mongo id in message (router only, scoped).
3. Named title candidate confirmed against the company's estimates: 1 match → target; 2+ → clarification listing codes; 0 → **refuse and offer the active estimate** as a yes/no ("I couldn't find an estimate named 'Henderson'. Did you mean E0042 'Spring Cleaning', the one you have open?"). Never silently use the active estimate for a named-but-unmatched title. (This preserves the 2026-06-08 integrity fix.)
4. Positional pick against `last_listed_items` (resource `estimate`).
5. Active anchor (company-scoped).
6. "latest / last / most recent" → most recently created.
7. Router update/delete only: fuzzy title flagged for confirmation; most-recent fallback only for non-destructive.
8. Otherwise "Which estimate?" and stash `awaiting_value_for="estimate"` (Phase 2 makes the answer resume the original message).

**Title loosening** (in `crud_handlers.py` next to `_TITLE_PRE_NOUN_RE` / `_TITLE_POST_NOUN_RE`, currently 2+ words + capitalized first word at :1873-1881)
- Allow lowercase and single-word candidates when adjacent to an estimate noun: `(?:the\s+)?(?P<title>[\w&'-]+(?:\s+[\w&'-]+){0,4})\s+(?:estimate|quote|bid|proposal|job(?!\s*item))\b` and the post-noun form `(?:estimate|quote|bid|proposal)\s+(?:for\s+|called\s+|named\s+)?(?P<title>…)`.
- Stop-list rejects: this/that/the same/current/active/open/previous/last/latest/new/first/whole/entire/my/our, status words, `_TITLE_TAIL_STOP`.
- Matching ladder: exact case-insensitive → whole-word prefix → substring (2+ word candidates only) → **customer resolution**: `find_properties_by_name_or_address` / contacts by name → estimates linked to those properties (closes Task 8 in `maple-estimate-field-edits.md:975-993`). Multiple → existing multi-match envelope.
- Bare quoted strings stay excluded from candidacy (they may be note bodies).
- Synonyms `bid`/`proposal`: `DOMAIN_HINTS["estimate"]` and `PLURAL_DOMAIN_TOKENS` in `agents/orchestrator/intents.py`; `_ESTIMATE_NOUN_PATTERN` in `orchestrator/service.py`; `_ESTIMATE_SEARCH_STOP_WORDS` (`estimate_resolver.py`); `_GET_ESTIMATE_STOP_WORDS` (`delegate_get_estimate.py`).

**Files**
| File | Change |
|---|---|
| `platform/routers/agent_helpers/active_estimate.py` (new) | `apply_viewed_estimate_signal(merged_context, client_context)`; `anchor_estimate(final_context, *, estimate, source)` as the single writer of anchor keys |
| `platform/routers/agents.py` | Call `apply_viewed_estimate_signal` after the merge |
| `platform/routers/agent_helpers/finalize_result.py` | Flat results: resolve `active_estimate_id` via `agents/cross_resource.py::find_estimate_by_code` when only a code is present; use `anchor_estimate` |
| `platform/routers/agent_helpers/estimate_resolver.py` | Reorder rungs (:144); add named-title rung delegating to the agent's title resolver via `get_estimate_agent()` |
| `platform/routers/agent_helpers/delegate_get_estimate.py` | After the code rung: `resolve_listed_reference(msg, ctx, resource="estimate")`, then the anchor when the message is anaphoric or names no title |
| `platform/routers/agent_helpers/estimate_update.py` | `run_update_estimate`: pass a context copy with `orchestrator_intent` removed so `agent.process` can reach generation (formalized in Phase 4) |
| `platform/agents/estimate/crud_handlers.py` | Candidate patterns, stop-list, ladder, customer fallback, active-estimate offer (stash `pending_estimate_fuzzy_confirmation` with `sub_op="use_active_estimate"`, `original_message`) |
| `platform/routers/agent_helpers/fuzzy_confirmation.py` | `sub_op == "use_active_estimate"` → re-dispatch `original_message` with `forced_estimate_code` |
| `portal/src/pages/NewEstimateWithActivityPage.tsx` | After `setEstimate(est)` in `loadEstimate` (~:358) dispatch `portal:estimate:loaded` `{id, estimate_id, title, status, at: Date.now()}`; dispatch `portal:estimate:unloaded` on unmount / id change; extract `loadEstimate` to `useCallback` and listen for `ESTIMATES_CHANGED_EVENT` (`agentMutationEvents.ts:19`) → reload when `detail.estimate?._id === estimateId` or `detail.estimate_id === estimate.estimate_id` and no save in flight and page not dirty; also `loadNoteCounts()` (closes followup #493) |
| `portal/src/components/Layout/useMapleAgent.ts` | Handle `portal:estimate:unloaded`; build `viewed_estimate` from the loaded detail |
| `portal/src/components/Layout/agentMutationEvents.ts` | Include `estimate_id` (code) in the event detail; add `add_estimate_note`, `add_work_item_note` to Estimate Agent operations |

**Tests**
- `tests/test_agent_helpers_active_estimate.py` (new): `test_new_view_signal_overrides_maple_anchor`, `test_unchanged_signal_keeps_later_maple_anchor`, `test_signal_for_other_company_estimate_is_ignored`, `test_null_signal_records_nonce_so_revisit_is_fresh`, `test_estimate_change_clears_work_item_anchor`
- `tests/test_agent_helpers_estimate_resolver.py`: `test_explicit_code_beats_active_context`, `test_named_title_beats_active_context`, `test_named_title_no_match_does_not_fall_to_active` (existing `:49` active-first assertion flips)
- `tests/test_agent_helpers_delegate_get_estimate.py`: `test_show_this_estimate_uses_active_anchor`, `test_positional_pick_after_list`
- `tests/test_agent_helpers_finalize_result.py`: `test_flat_result_sets_active_estimate_id_by_code`
- `tests/test_maple_estimate_field_edits.py`: `TestTitleCandidates` (lowercase single word, "the Smith job", "the Henderson proposal", stop-list words rejected, zero-match offers active)
- `tests/test_agent_helpers_estimate_update.py`: `test_run_update_estimate_reaches_generation_when_no_sub_op`
- portal `NewEstimateWithActivityPage.test.tsx`: dispatches loaded event; reloads on estimates-changed for its own id only; skips when dirty

**Risks:** refetch can clobber unsaved edits (mitigated by the dirty/in-flight guard, else a "Updated by Maple, reload?" affordance). Customer-name resolution may match many estimates: always return the multi-match envelope.

---

## Phase 2: Work-item context and multi-turn

**Keys**
```
active_work_item: {estimate_id, estimate_code, job_item_id, position, description, set_at}
last_listed_items: {resource: "work_item", ids: [job_item_id…], labels: […], scope: "E0042"}   # `scope` new optional field
pending_intents[]: {id, agent: "Estimate Agent", intent: "update_estimate"|"get_estimate",
                    awaiting_value_for: "work_item"|"estimate"|"description"|"material"|"activity"|"amount"|"division",
                    original_message, estimate_code, op, candidates: [{job_item_id, position, description}]}
```

**Behavior**
- Anchor set by: get work item; any sub-op that resolved exactly one work item; add work item (the new one); a resolved "Which work item?" answer. Cleared by: estimate anchor change, work item removed, estimate deleted.
- `_find_work_item_matches` (`work_item_handlers.py:418`) gains `context`; empty or anaphoric hints ("it", "that one", "this work item", "the same one") resolve to the anchor by `job_item_id` (position fallback). Centralize the repeated `if not name_hint and len(job_items) == 1` block (e.g. `work_item_field_handlers.py:1136`) into `_resolve_work_item_target(query, job_items, code, context, *, name_hint) -> (idx, item) | clarification`. Phase 3's executor reuses it.
- `_handle_list_work_items`, agent `_handle_get_estimate`, and `delegate_get_estimate` record rendered rows with `record_listed_items(resource="work_item", scope=code)` (`agents/text_utils.py:1062`). `resolve_listed_reference` (:1171) skips its work-item bail when `resource == "work_item"`; a pick is honored only when `scope` equals the target estimate's code. Orchestrator `_match_listed_positional_follow_up` maps `recorded_list_resource() == "work_item"` to the Estimate Agent (`get_estimate` for read verbs, else `update_estimate`).
- Clarifications stash a pending record. New `_resume_estimate_pending(query, context)` runs at the top of `EstimateAgent.process` (before the CRUD short-circuit at `service.py:813`): position/ordinal/number or single candidate match → set anchor, re-dispatch `original_message`; `estimate` → resolve reply as code/title, re-dispatch with `forced_estimate_code`; value fields → re-dispatch with `pending_value` in context (handlers read it before their own extraction). A reply that is itself a full command (E-code, `_detect_work_item_op`, `owns_update_sub_op`, read verb) drops the pending. Router `_get_awaiting_value_match` (`agents.py:418`) already forces the agent when `awaiting_value_for` is set.

**Files**
| File | Change |
|---|---|
| `platform/agents/estimate/pending_handlers.py` (new `EstimatePendingMixin`) | `_stash_estimate_pending`, `_resume_estimate_pending`, `_set_active_work_item`, `_clear_active_work_item`; normalization mirrors `agents/property/service.py:126-176` |
| `platform/agents/estimate/service.py` | Add mixin; call resume at top of `process` |
| `platform/agents/estimate/work_item_handlers.py` | `_find_work_item_matches(context=…)`, `_resolve_work_item_target`, `_ambiguous_work_item_response` stashes candidates, anchor writes |
| `platform/agents/estimate/work_item_field_handlers.py` | Replace inline "Which work item?" blocks with `_resolve_work_item_target`; record list rows |
| `platform/agents/text_utils.py` | `record_listed_items(..., scope=None)`; work-item branch in `resolve_listed_reference` |
| `platform/agents/orchestrator/service.py` | `_match_listed_positional_follow_up` work-item mapping |
| `platform/routers/agent_helpers/delegate_get_estimate.py` | Record listed work items |
| `platform/routers/agent_helpers/active_estimate.py` | Clear `active_work_item` on estimate change |

**Tests**
- `tests/test_maple_work_item_context.py` (new): `test_get_work_item_sets_anchor`, `test_it_resolves_to_anchor_on_same_estimate`, `test_anchor_ignored_when_estimate_differs`, `test_which_work_item_answer_by_number_resumes_original`, `test_which_work_item_answer_by_description_resumes_original`, `test_new_command_releases_pending`, `test_description_value_reply_resumes`, `test_which_estimate_answer_with_code_resumes`
- `tests/test_maple_listed_positional_reference.py`: `test_second_one_after_work_item_list_targets_work_item`, `test_work_item_pick_rejected_for_other_estimate_scope`
- `tests/test_orchestrator_intents.py`: referenceless positional follow-ups after a work-item list

**Risk:** stale pending records. One pending per agent (upsert by id), released on any full command, cleared when the anchor estimate changes.

---

## Phase 3: `EditCommand` schema and executor

**Command catalog** (pydantic discriminated union on `op`; `WorkItemRef` = exactly one of `job_item_id | position | description_hint | use_active=True`)

| `op` | Fields | Notes |
|---|---|---|
| `set_title` | `title` | estimate-level |
| `set_description` | `description` | estimate-level |
| `set_status` | `status` | `validate_estimate_status_transition` + role gates extracted from `_handle_update_estimate_status_transition` into `_apply_status_transition` |
| `set_property` | `property_id` (rules) / `property_query` (planner) / `null` to unlink | executor resolves query to exactly one company property |
| `add_estimate_note` | `body` | lock-exempt; `NoteHandlersMixin` |
| `add_work_item` | `description`, `division?` | company defaults via `get_company_defaults` |
| `remove_work_item` | `target` | confirmation unless `confirmed=True` |
| `set_work_item_description` | `target`, `description` | rename is the same command |
| `set_work_item_division` | `target`, `division` | `canonical_division_name` against company `Division` docs |
| `add_material` | `target`, `material_query`, `quantity=1`, `size?` | `_find_catalog_materials` + `build_work_item_material_line` |
| `update_material` | `target`, `material_query`, `quantity?`, `price?` | at least one; writes `price` only, never `cost` |
| `remove_material` | `target`, `material_query` | |
| `add_activity` | `target`, `name`, `role_query?`, `effort_hours?` | `build_work_item_activity_line` |
| `update_activity` | `target`, `activity_query`, `name?`, `role_query?`, `effort_hours?`, `rate?` | role change re-snapshots `rate` and `cost_rate` from the catalog; bare `rate` change leaves `cost_rate` alone |
| `remove_activity` | `target`, `activity_query` | |
| `set_work_item_percentage` | `target`, `field: markup\|overhead\|tax`, `value` | writes `profit_margin` / `overhead_allocation` / `tax`; bounds markup −100..500, overhead/tax 0..100 |
| `set_work_item_gross_margin` | `target`, `margin_pct` | `back_calculate_markup_from_gross_margin` → `profit_margin`; refuse ≥100 or missing activity cost basis |
| `set_work_item_total` | `target`, `amount` | `back_calculate_markup` → `profit_margin`; set `original_profit_margin` once when `None` (mirrors the portal Adjust pill); **replaces today's direct `sub_total` write** |
| `set_work_item_recurring` | `target`, `enabled`, `schedule?` | keeps existing parsing |
| `add_work_item_note` | `target`, `body` | lock-exempt; Phase 4 note service |
| `generate_work_item` | `scope_text`, `division?` | Phase 4 |

Reads (get/list/query) stay rule handlers; they are not commands.

**Executor contract** (`EditExecutorMixin._execute_edit_commands(*, target, commands, company_id, context, confirmed=False) -> ExecutionReport`)
- Validate all commands first (targets resolve to exactly one work item; catalog queries to exactly one row; bounds), then mutate in memory, recompute `sub_total` for touched items with the shared breakdown, recompute `grand_total`, persist **once** via `services/sparse_update.py::persist_fields(target, "job_items", "grand_total", …)`. Any validation failure → nothing persisted, one clarification (candidates stashed per Phase 2).
- Edit lock: content commands reuse `_locked_status_edit_refusal` (`crud_handlers.py:828`); notes exempt; `set_status` follows the transition table.
- `remove_work_item` without `confirmed` → `needs_confirmation` with the pending shape `fuzzy_confirmation.py` already dispatches (`sub_op="edit_commands"`, serialized commands, `estimate_id`, `original_message`); router re-executes on "yes".
- `ExecutionReport`: `applied[]` (op, work item position/id/description, new sub_total, summary line), `estimate_doc_id`, `estimate_code`, `grand_total`, `needs_confirmation`, `clarification`. `render_report()` echoes each change plus work-item total(s) and grand total. `result` carries `operation: "update_estimate"`, `estimate_id` (code), and a slim `estimate: {_id, estimate_id, title, status, grand_total}` so `finalize_result` anchors by id and the portal event fires.

**Ported math** (`platform/routers/estimate_helpers/calculations.py`, beside `apply_overhead_to_labour_and_profit_to_total` :90): `work_item_breakdown(item)`, `work_item_gross_margin(item) -> Optional`, `back_calculate_markup(subtotal, tax_pct, new_total)`, `back_calculate_markup_from_gross_margin(item, target_pct)`, `count_activities_missing_cost(item)`. Semantics pinned to `portal/src/utils/__tests__/estimateCalculations.test.ts` (material markup is cost; only activities billed off `cost_rate` contribute profit; overhead deducted; tax excluded; negative not clamped; `None` when an activity lacks `cost_rate`). `_recalculate_sub_total` (`work_item_field_handlers.py:79`) becomes `work_item_breakdown(item).total`.

**Migration order** (one commit each, existing tests green): set_total → add/remove material → add/remove activity → division/description → rename → add work item → remove (confirmation) → recurring → title/description/property/note → status. Each handler becomes parse → command → execute → render.

**Files**
| File | Change |
|---|---|
| `platform/agents/estimate/edit_commands.py` (new) | Schema |
| `platform/agents/estimate/edit_executor.py` (new) | Mixin: validation, persistence, rendering |
| `platform/routers/estimate_helpers/calculations.py` | Ported math |
| `platform/agents/estimate/service.py` | Add mixin |
| `work_item_handlers.py`, `work_item_field_handlers.py`, `crud_handlers.py`, `note_handlers.py` | Handlers build commands |
| `platform/routers/agent_helpers/fuzzy_confirmation.py` | `sub_op == "edit_commands"` |
| `platform/routers/agent_helpers/estimate_update.py` | `_persist_added_job_items` becomes an executor call |

**Tests**
- `tests/test_estimate_edit_commands.py`: `test_work_item_ref_requires_exactly_one_locator`, `test_update_material_requires_quantity_or_price`, `test_percentage_bounds`
- `tests/test_estimate_edit_executor.py`: `test_persists_once_for_multi_command_batch`, `test_any_invalid_command_persists_nothing`, `test_remove_requires_confirmation`, `test_locked_status_refuses_content_but_allows_note`, `test_set_total_back_calculates_markup_and_sets_original_once`, `test_update_material_never_writes_cost`, `test_role_change_resnapshots_rate_and_cost_rate`
- `tests/test_estimate_calculations_gross_margin.py`: port portal cases one-to-one (`margin_is_markup_over_one_plus_markup_when_no_activity_spread`, `back_calc_round_trips_readout`, `returns_none_when_activity_missing_cost`, `negative_markup_not_clamped`, `refuses_100_percent`)
- Existing `test_maple_work_item_ops.py`, `test_maple_work_item_division_update.py`, `test_estimate_agent.py` stay green through migration

**Risk:** fixtures using `MagicMock` job items won't survive a real breakdown; executor reads fields via `getattr(..., default)` as `_recalculate_sub_total` does today.

---

## Phase 4: Fill the CRUD gaps (rules layer, on the executor)

| Gap | Detector (rules) | Command |
|---|---|---|
| Update material qty/price | `_detect_catalog_sub_op` returns `update_material` with `material_query`, `quantity?`, `price?` ("change the mulch quantity in work item 2 to 8", "set the price of pavers on the patio work item to $4.25") | `update_material` |
| Update activity effort/rate/role | `update_activity` slots ("make the excavation activity 6 hours", "change the rate on grading to $80", "assign the Landscaper role to the cleanup activity") | `update_activity` |
| Percentages | New `_detect_work_item_percentage_op` ("set the markup on work item 2 to 20%", "tax 13% on the patio work item", "overhead to 10%"); delete `_WORK_ITEM_REFUSED_FIELDS` and the refusal branch at `work_item_handlers.py:931`; **labor burden stays refused** with a UI pointer | `set_work_item_percentage` |
| Gross margin | `_detect_gross_margin_op` ("set the gross margin on work item 1 to 35%") | `set_work_item_gross_margin` |
| Set total | existing detector | `set_work_item_total` (back-calculation) |
| Work-item notes | `_detect_note_update` + work-item noun → new `services/notes.py::create_work_item_note_as(company, estimate_id, work_item_id, body, author_email, author_name)` that calls `assert_parent_exists` then inserts with `work_item_id`. `create_note` stays the HTTP path; `create_note_as` keeps its WORK_ITEM rejection | `add_work_item_note` |
| AI-generated work item | `_detect_generate_work_item` ("generate/price/build a work item for <scope> on E0042", "add a scope for installing 200 sq ft of pavers and price it"); executor runs `LlmPipelineMixin._run_pipeline` for the single scope, builds via `merge_job_items_with_original_descriptions` + `build_job_items_from_parsed` + `enrich_job_items_in_place`, appends, anchors the new work item | `generate_work_item` |
| View work item | `_build_work_item_details_text` lists materials/activities with qty/price/effort/rate plus markup/overhead/tax/gross margin | read, no command |

Also remove `_modify_items_refusal` in `estimate_update.py` (the agent owns those phrasings; `_should_delegate_update_estimate_to_agent` at `agents.py:226` picks up new detectors through `owns_update_sub_op`). Extend the portal's `pendingVariantFor` regex so generate-work-item phrasings show the long-running indicator.

**Tests**
- `tests/test_maple_work_item_ops.py`: `test_update_material_quantity_detected`, `test_update_activity_effort_detected`, `test_markup_percentage_detected`, `test_gross_margin_detected`, `test_work_item_note_detected`, `test_generate_work_item_detected`
- `tests/test_maple_work_item_edits.py` (new, handler-level with fake estimates): `test_update_material_quantity_recomputes_totals`, `test_set_markup_echoes_new_work_item_total`, `test_gross_margin_sets_markup_and_readout_matches`, `test_labor_burden_still_refused`, `test_work_item_note_files_with_work_item_id`, `test_generate_work_item_appends_and_anchors`
- `tests/test_notes_service.py`: `test_create_work_item_note_as_validates_parent`

---

## Phase 5: LLM edit-planner fallback

**Invocation:** only from the end of `_handle_update_estimate` (`crud_handlers.py:2454`) and the refusal path in `run_update_estimate`, when `self.use_llm`, the estimate resolved per Phase 1 order, and no rule matched. Never for reads; never when no estimate is resolvable ("Which estimate?" stays). One call per turn, no retries, 12s timeout; on error → existing capability message.

**Prompt inputs** (`platform/prompts/estimate_edit_planner.py`; all snapshot text framed as data, not instructions)
```
estimate: {id, code, title, status, description (≤300 chars), property_label|null, grand_total}
work_items[]: {n, job_item_id, description, division, markup_pct, overhead_pct, tax_pct, sub_total, recurring,
               materials[≤12]: {i, name, qty, unit, price}, activities[≤12]: {i, name, role, effort_hours, rate}}  (+ "N more")
active_work_item: {n, job_item_id} | null
last_assistant_question: str | null
recent_chat: last 6 turns, ≤300 chars each
message: the user's English text
```
**Output contract**
```
EditPlan: commands: List[EditCommand] (0..5); needs_clarification: bool; clarifying_question: Optional[str];
          unsupported_reason: Optional[Literal["read_only","different_estimate","out_of_scope","unclear"]]
```
`create_chat_model("worker", temperature=0).with_structured_output(EditPlan, method="function_calling")` (same shape as `agents/property/service.py:258`).

**Guardrails:** schema has no estimate field, so a command cannot name another estimate (prompt returns `different_estimate`); `job_item_id` must be in the snapshot, `position` in range, else the whole plan is rejected; max 5 commands; `remove_work_item` still gates on confirmation; reads refused (`read_only`); whole-plan rejection on any invalid command with one clarification; log op names and estimate code only, never bodies. Run the `agent-prompt-review` skill on the prompt before merge.

**Files:** `platform/agents/estimate/edit_planner.py` (new: snapshot builder, `plan_edits()`), `platform/prompts/estimate_edit_planner.py` (new), `crud_handlers.py` (fallback call), `estimate_update.py`, `service.py` (planner model beside the existing worker LLM).

**Tests**
- Tier 1 with a fake LLM exposing `with_structured_output` (pattern in `agents/contact/service.py:887`): `tests/test_maple_edit_planner.py`: `test_planner_not_called_when_rule_matches`, `test_planner_not_called_without_resolved_estimate`, `test_plan_with_unknown_job_item_id_rejected_whole`, `test_plan_over_max_commands_rejected`, `test_read_only_reason_returns_capability_message`, `test_remove_from_plan_still_requires_confirmation`, `test_snapshot_caps_lines_and_truncates_description`
- Tier 2 `@pytest.mark.llm_e2e`: `tests/test_maple_edit_planner_llm.py`: paraphrases of each Phase 4 op, a two-command turn, a different-estimate message, an ambiguous work item

---

## Phase 6: Docs and matrix

- `documentation/development/maple-phrasing-reference.md` §1 (lines 648-1103): new §1.5 rows for every phrasing above (✅ rule / 🤖 planner / 🛑 labor burden); flip the "financial fields refused" rows in §1.5.7; §12.3 counts; "Last updated".
- `platform/tests/_maple_coverage_data.py`: curated `_estimate_work_item_edits` category (E0042-anchored phrasings, `resources=("estimate",)`) so `tests/reports/maple_crud_gap_report.md` regenerates.
- `platform/user_guides/users_guide.md` §5.6 / §7.2: markup, tax, gross margin, work-item notes, "keep talking about this estimate"; fix the contradiction at :169-170 and :1099-1102 about estimate notes.
- `CLAUDE.md`: one pointer under the pricing section to the ported math and to `edit_commands.py` as the single write path for Maple estimate edits; note `client_context` allowlist under the Maple section.
- `documentation/development/plans/maple-estimate-field-edits.md`: mark Task 8 closed. `code-review-followups.md`: close #493.

---

## What NOT to do

- Do not write `Estimate.notes`; all notes go to the Notes feed (estimate or work item).
- Do not bypass the Draft/Review lock except for notes; status changes use the transition table and role gates.
- Do not write `price` into `MaterialItem.cost`; `update_material` touches `price`/`quantity` only. Never coerce a missing `cost`/`cost_rate` to 0 or to the price.
- `JobItem.profit_margin` is a markup. Gross margin is derived, never stored; `set_work_item_gross_margin` writes a markup.
- Do not overwrite `sub_total` directly; back-calculate markup as the portal does.
- Do not `.save()` whole documents; `persist_fields` only (version bump, #490).
- Do not let the client set `active_*`, `pending_*`, `last_listed_items`, or `chat_history`; do not trust `company_id` stored in pending records.
- Do not call the planner for reads, let it pick the estimate, or apply a partial plan.
- Do not touch labor burden, equipment, discount, reorder/duplicate, inventory-gap resolution, or document generation.
- After Phase 3, no new handler gets its own persistence.

## Verification (end to end)

1. Backend per phase: `cd platform && ./run_tests.sh tests/<files above>`; `./run_mypy.sh agents/estimate routers/agent_helpers`; `./run_ruff.sh agents/estimate routers/agent_helpers`. Local Mongo via `./scripts/start_test_mongo.sh`.
2. Portal per phase: `cd portal && npm test -- useMapleAgent NewEstimateWithActivityPage`; `npm run typecheck` before any push.
3. Matrix: `./run_tests.sh tests/test_maple_crud_coverage.py` (Tier 1) and once after Phase 5 `-m ""` (Tier 2, ~3 min, needs `OPENAI_API_KEY`).
4. Manual walk-through in the browser preview (`preview_start` on the portal dev server against Dev):
   - "Create an estimate for sod at 12 Oak St" → "add a work item called Patio" → "add 10 bags of mulch to it" → "set the markup to 20%" → "set the gross margin to 35%" → "add a note to the patio work item: check drainage" → all apply to the new estimate; the page refetches after each.
   - Open E0042 in the portal, say "add a work item called Fence" → applies to E0042 not the estimate created above. Then "update estimate Spring Cleaning status to Sent" → applies to Spring Cleaning, not E0042.
   - "show the work items" → "the second one" → "make it 6 hours of Landscaper" → resolves against the stored list and anchors the work item.
   - Craft a request with `context.active_estimate_id` of another company's estimate → ignored (Phase 0).
   - Long-tail phrasing with no rule ("bump the patio's pavers to a dozen and drop the tax") → planner produces two commands; reply echoes both and the new totals.
