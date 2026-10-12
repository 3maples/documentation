# Code Review Follow-ups

Punch-list of issues surfaced by `/code-review` and deferred by `/fix-issues`.
Started 2026-04-19. Closed items live in
[`code-review-followups-archive.md`](code-review-followups-archive.md).

Pick what's valuable when you're already in the affected area — this is not a
sprint plan.

## How to use this file

**Consolidated 2026-09-20** — 408 entries down to 370, by archiving what was
already resolved, folding every file/length finding into #4, and regrouping the
remainder by theme instead of by review date. The chronological
"deferred from /code-review on <date>" session headers are gone; every entry
kept its number and its body.

**Maple pass 2026-10-11** — 133 resolved Maple entries moved to the archive, and 33
entries about code only today's pipeline runs dropped there too (the planner never
runs it, and it goes at the switchover). The archive's 2026-10-11 section lists both.

- **Entries are numbered and permanent.** Next free number: **929**. Never
  reuse or reassign one — the archive keeps them resolvable. `/fix-issues`
  selects by number.
- **File and function length goes in #4.** Update its table; do not file a new
  entry, and do not file a second entry for a file already listed.
- **Recurring themes have a home section.** Before filing, check whether one of
  these already covers it:
  [File and function size](#file-and-function-size),
  [Query efficiency](#query-efficiency--scans-n1-and-missing-indexes),
  [Silently swallowed errors](#silently-swallowed-errors),
  [Duplicated code and twin files](#duplicated-code-and-twin-files),
  [Accessibility](#accessibility),
  [Responsive and breakpoint drift](#responsive-and-breakpoint-drift),
  [LLM prompt hygiene](#llm-prompt-hygiene-and-injection-surface),
  [Codebase hygiene](#codebase-hygiene-batchable).
- **A length finding that also names a distinct defect stays separate** — the
  defect outlives the line count.
- **Tooling gaps are not findings.** A missing local tool is a setup problem.
- **When you close an item:** mark it RESOLVED in place, then move it to the
  archive in the next cleanup pass. Don't let resolved entries accumulate here.

Working rules: one HIGH item per session, failing test first (TDD per
`CLAUDE.md`), run the related test file only, one commit per item, mark it
RESOLVED in the same commit.

## Priority queue — next seven

Ranked by severity × value, originally derived 2026-09-20. Two items have been
worked off and one declined since, so the order below is **maintained, not
re-derived** — treat it as a to-do list, not a fresh ranking. A full re-derive
is due.

**2026-09-27:** the multi-turn push
([design](plans/2026-09-27-maple-multi-turn-everywhere-design.md)) takes the
Maple HIGH items #671–#681 as a batch — the one-HIGH-per-session rule is
suspended for it (design decision 8); see its §4. The ranking below is
unchanged.

| # | Item | Why it's here |
|---|------|---------------|
| 1 | [#490](#490-medium-same-field-conflicts-are-still-silent--the-conflict-detection-phase) | Concurrent edits to the same field resolve silently, last-write-wins. **In progress 2026-09-22:** the server mechanism and the TaskDialog are built; the estimate builder is the remaining surface — see the entry for what it still needs. |
| 2 | [#546](#546-medium-platformscriptsmigrate_landscaping_industrypy73--no-way-to-target-prod-and-no-confirmation-before---apply) | A migration script with `--apply`, no environment guard and no confirmation prompt. Latent, but one wrong shell is production data. |
| 3 | [#4](#4-high-file-and-function-size) | `routers/auth.py` — the one oversized file with a clean seam. Extract the invitation lifecycle into `routers/invitations.py` (~400 lines) and the backlog's biggest theme finally moves. |
| 4 | [Query efficiency](#query-efficiency--scans-n1-and-missing-indexes) | Eighteen full-collection scans, N+1 loops and unindexed sorts — several on Maple's hot paths ([#25](#25-medium-regex-email-lookup-in-_resolve_user), [#328](#328-medium-_resolve_estimate_by_title-full-collection-scan-now-on-three-more-paths), [#443](#443-medium-platformroutersopspy200--task-counts-aggregate-the-whole-collection), [#506](#506-medium-platformroutersestimatespy444--search-runs-an-unindexed-regex-over-titledescription)). Cost and latency grow with every customer added. |
| 5 | [Silently swallowed errors](#silently-swallowed-errors) | Fifteen paths that discard the real failure, including the 11 bare `except Exception: pass` blocks that are the standing bandit baseline ([#64](#64-medium-workitem-divisions-fetch-swallows-errors-silently), [#430](#430-low-platformagents--11-bare-except-exception-pass-blocks-bandit-b110), [#290](#290-medium-dashboard-analytics-fetch-error-is-silent), [#461](#461-medium-portalsrcpagesauthloginpagetsx201--terminal-invitation-failure-silently-dropped-for-unverified-users)). |
| 6 | [Accessibility](#accessibility) | Twenty-seven findings, several of them keyboard traps or controls with no accessible name at all ([#43](#43-medium-trash-icon-only-buttons-have-no-accessible-name), [#469](#469-low-portalsrccomponentscommonsearchableselecttsx--no-keyboard-navigation), [#476](#476-low-portalsrccomponentscommonstatusfilterdropdowntsx196--trigger-has-no-accessible-name-beyond-its-summary), [#552](#552-medium-portalsrccomponentsnotesnotebodytsx90--the-note-text-is-unreachable-by-keyboard)). |
| 7 | [#60](#60-medium-no-unique-compound-index-on-material--contact) | No unique compound index on Material / Contact — duplicate rows can be created concurrently. Was "just off the list"; promoted 2026-09-22 into the slot #326 vacated. |

**Closed from this queue:** #566 (local dev holds production credentials),
closed 2026-09-22 as an owner decision — accepted risk, the laptop is not a leak
path. #350 left the queue with it but stays open: its `SecretStr` half guards a
future call site, which is a different question. #451 and #363, the two prompt-injection entries,
both resolved 2026-09-22. Division and role catalogs are now fenced as data
through one shared helper (`prompts/fencing.py`); the instruction-prefix
blocklist both entries suggested was rejected, and they record why. The
material catalog and unit list in the same prompts remain unfenced and
unfiled — see the tail of #363. #557 and #563 (work-item summaries standalone
corpus + the erasure its §4 left behind), resolved 2026-09-21. **#326**
(duplicated delegation block) resolved 2026-09-22, taking #335 with it.
**#535** (AI-accuracy disclaimer) closed 2026-09-22 as an owner decision —
will not fix; the notice stays removed.

**Demoted 2026-09-21:** #350 fell from slot 1 and from HIGH to MEDIUM. It held
slot 1 because the 2026-07-27 credential exposure was unrotated; the owner
confirmed the output never left the laptop, so rotation is withdrawn and both
leak paths were already closed. What survives is #566 — the reason a laptop had
production keys at all — plus #350's latent `SecretStr` gap.

## File and function size

### 4. [HIGH] File and function size

**The single tracker for every file-length and function-length finding.** Line
counts below re-measured on `main`, 2026-09-20; the Maple rows (Maple agents,
`routers/agents.py` and the Maple test files) re-measured 2026-09-27.
Forty-four entries were folded in here on 2026-08-25 and a further twenty on
2026-09-20; their bodies —
including the suggested split for each — are preserved under
[`## 4 — folded file/function-size entries`](code-review-followups-archive.md)
in the archive.

**When a review flags a long file or function, update the row below — do not
file a new entry.** The 2026-09-20 pass found the same three files logged
independently three times over (`PortalLayout.tsx` ×3, `ContactsPage.tsx` ×2,
`NewEstimateWithActivityPage.tsx` ×2), each with a stale line count. A row
cannot go stale that way.

A new entry is warranted only for a length finding that *also* names a distinct
defect (duplication, dead code) — see #326 and #445.

Guideline is 800 lines per file and 50 per function (CLAUDE.md).

#### Source files over 800 lines

| Lines | File | Note |
|------:|------|------|
| 3,797 | [platform/agents/estimate/crud_handlers.py](../../platform/agents/estimate/crud_handlers.py) | +27 on 2026-09-29 (sold estimates; the question reader went to its own `list_query.py`); no clean seam; −176 on 2026-09-23 when the notes sub-op moved to `note_handlers.py`; +60 on 2026-09-24 (multi-turn estimate editing: title offer, open-work-item check), +63 over the review passes; +78 on 2026-09-25 routing convergence (the listed-command dispatcher `_dispatch_listed_command` replaced the cascade) ; +354 by 2026-09-27 over the routing-convergence review rounds — **next step:** move `_dispatch_listed_command` into its own `listed_dispatch.py` mixin; +112 on 2026-09-27 (multi-turn push); 4,022 on 2026-10-05 (+5 that day: `_create_estimate_from_template(audit=)`); 4,089 on 2026-10-06 (+67: tax in the dashboard's figures and a list's total); 4,144 on 2026-10-08 (+55, switchover phase 4d: the property link's write and reply split out as `_apply_estimate_property` for the planner); 4,163 on 2026-10-09 (+19, switchover phase 6b: today's template apply's tail split out as `_add_template_work_item`); +4 on 2026-10-10 (phase 7d: the dashboard's summary card in `dashboard_reply`) |
| 3,577 | [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py) | no clean seam; `process()` is a 282-line god-method. +120 on 2026-09-24 for the estimate conversation lanes; 2026-09-25 routing convergence deleted `_is_work_item_edit`, `_answers_estimate_question` and the inferred-material lane but added `_route_listed_command`, `_route_note_to_a_named_record` and the fenced context (+42 net); +70 by 2026-09-27 — **next step:** move those two routes and `_names_an_anchored_line` into `agents/orchestrator/estimate_rules.py`; +155 on 2026-09-27 (multi-turn push: cross-record joins, dashboard, named creates) |
| 3,483 | [platform/agents/material/service.py](../../platform/agents/material/service.py) | 3,483 on 2026-10-10 (+27 over 3,456, switchover phase 7d: `material_sizes_reply` shared with today's size command, `materials_on_estimate_reply` and `_estimate_materials_reply`); +366 on 2026-09-27 (multi-turn push: size commands, one-question creates); +123 in the 2026-09-27/28 review fixes (3,087 at `main` then) — the material in focus, size-label refusals, "which material?". `_handle_size_command` is 105 lines — split into `_resolve_size_target(...)`, `_render_size_read(...)` and `_size_command_fields(...)` (review 2026-09-27 #29) |
| 2,823 | [platform/agents/property/service.py](../../platform/agents/property/service.py) | +170 since Aug; +70 on 2026-09-27; 2,823 on 2026-10-10 (switchover phase 7d part 2: `properties_using_reply`, the cross list's words split out as `_cross_response`, and `_estimate_linked_reply` and `_joined_properties_reply` split out of `_list_properties_by_cross_resource`, which is now under 50 lines) |
| 2,561 | [portal/src/pages/SettingsPage.tsx](../../portal/src/pages/SettingsPage.tsx) | **next step: extract `CompanyTab`** to finish the split already begun |
| 2,498 | [platform/agents/contact/service.py](../../platform/agents/contact/service.py) | +123 on 2026-09-27 |
| 2,282 | [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) | logged twice at stale counts (1,861 / 1,927); +133 on 2026-09-24 for Maple sync (announce, reload guard, deferred reload), more over the review passes for the estimate-switch guards, the load-error state and the autosave rollback; +56 on 2026-09-25 (merge-by-id work-item saves, delete-on-screen, Retry focus) — a `useMapleEstimateSync` hook is the natural seam |
| 2,227 | [platform/routers/agents.py](../../platform/routers/agents.py) | +26 on 2026-09-24 (open-question short-cuts; fourth pass #18); −36 on 2026-09-25 (the release heuristic and the Estimate branches of the awaited-value override and pending fallback moved into `open_question.py`); +11 by 2026-09-27. was `orchestrate_agent_endpoint` at 607 lines; +221 on 2026-09-27 (open question, conversation store, page signals); the endpoint body is now `_orchestrate_turn` (#689), 729 lines (functions table); re-measured 2,227 on 2026-10-07 (+63 that day, from 2,164: the turn id and the unanswered tracker's hooks on the finalize closure, the early exits and the 500 path — review 2026-10-07 #4, deferred) |
| 1,720 | [platform/agents/text_utils.py](../../platform/agents/text_utils.py) | +78 on 2026-09-24, +156 by 2026-09-27. **Next step:** move the command-head helpers (`strip_dictated_payload`, `strip_assigned_value`, `is_pronoun_targeted_edit`) into `agents/command_head.py`, re-exported from here (review 2026-09-24 #73); +89 on 2026-09-27 |
| 1,644 | [platform/routers/estimates.py](../../platform/routers/estimates.py) | −122 on 2026-09-23 (doc endpoints moved to `routers/estimate_documents.py`); +20 on 2026-09-22 for #490's conditional write; −35 on 2026-09-25 (delete rule and cascade moved to `services/estimate_delete.py`); `update_estimate` is most of the file's weight (see below) |
| 1,712 | [platform/agents/labour/service.py](../../platform/agents/labour/service.py) | +42 on 2026-09-27; 1,712 on 2026-10-10 (+27, switchover phase 7d: `roles_on_estimate_reply`, the per-estimate list's reply split out as `_estimate_labours_reply` so the planner passes its own estimate) |
| 1,565 | [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx) | |
| 1,284 | [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) | |
| 1,274 | [portal/src/pages/ContactsPage.tsx](../../portal/src/pages/ContactsPage.tsx) | logged twice; two shared-component extractions already landed |
| 1,246 | [platform/agents/estimate/llm_pipeline.py](../../platform/agents/estimate/llm_pipeline.py) | −153 by 2026-09-27 |
| 1,210 | [platform/routers/auth.py](../../platform/routers/auth.py) | **highest-value split** — see below |
| 1,206 | [platform/agents/estimate/text_helpers.py](../../platform/agents/estimate/text_helpers.py) | +11 on 2026-09-27 |
| 1,201 | [portal/src/pages/PeoplePage.tsx](../../portal/src/pages/PeoplePage.tsx) | |
| 1,177 | [platform/agents/equipment/service.py](../../platform/agents/equipment/service.py) | +22 on 2026-09-27 |
| 1,163 | [platform/agents/estimate/work_item_handlers.py](../../platform/agents/estimate/work_item_handlers.py) | +48 over the 2026-09-24 review passes; +15 by 2026-09-27 |
| 1,195 | [platform/agents/task/text_helpers.py](../../platform/agents/task/text_helpers.py) | **crossed the line 2026-09-27** (was 745): the multi-turn push added task verbs, create clauses and due phrases; +65 on 2026-09-28 for the target-first field shapes and `restated_field_value`. **Next step:** `agents/task/due_dates.py` (`parse_due_date_value`, the month/relative-date regexes, `parse_due_phrase`), `agents/task/verbs.py` (the `_DUE_CHANGE` / `_STATUS_VERB` / `_GIVE` / `_UNASSIGN` / `_PROPERTY_*` patterns and the `detect_*` functions) and `agents/task/create_parsing.py` (`_CREATE_LEAD`, `is_task_create_request`, `split_create_clauses`), re-exported from here (review 2026-09-27 #46) |
| 1,072 | [platform/agents/estimate/edit_executor.py](../../platform/agents/estimate/edit_executor.py) | new 2026-09-24, over the line after three review passes (third pass #29); +83 on 2026-09-25 (`_command`, stale-target confirmation); +39 by 2026-09-27. **Next step:** move the confirmations (`_confirm_removal`, `_confirm_division_guess`, `_confirm_target`, `_stash_edit_confirmation`) and target resolution (`_pin_targets`, `_resolve_target`) into `edit_targets.py`; +7 on 2026-09-27; 1,102 on 2026-10-05 (+14 for the save failure's outage/bug split, #619) |
| 1,060 | [platform/agents/estimate/command_grammar.py](../../platform/agents/estimate/command_grammar.py) | the written command list (design 2026-09-25), first measured 2026-10-06; +23 that day (tax: `_M_TAX`, the "of my estimates" and bare-total lookaheads, the "how much are my estimates worth" and headless total-value entries). **Next step:** move each family of entries (metric, line, ranking / by month / comparison, ratio) into `grammar_metrics.py` and keep `_CORE` here as their concatenation |
| 1,005 | [platform/agents/task/service.py](../../platform/agents/task/service.py) | **crossed the line 2026-09-27** (was 688); 1,048 by 2026-10-08, then −43 when `_handle_task_due_change` moved into operations.py (switchover phase 4b, done). **Next step:** a `TaskListBase` layer in `agents/task/listing.py` holding `_handle_list_tasks`, `_due_note`, `_resolve_list_ask` and `_FINISHED_STATUS_NAMES`; split `_handle_update_subop` into a detector table plus a named-target helper — about 600 lines left (review 2026-09-27 #47) |
| 818 | [platform/agents/task/operations.py](../../platform/agents/task/operations.py) | **crossed the line 2026-10-08** (was 774): `_handle_task_due_change` moved in beside the other sub-handlers (switchover phase 4b). **Next step:** the convert flow (`_handle_convert_task`, `_perform_conversion`, `_convert_error_copy`, about 175 lines) into `agents/task/convert.py` as a `TaskConvertBase` layer (review 2026-10-08 (4b) #22, deferred) |
| 903 | [platform/agents/orchestrator/intents.py](../../platform/agents/orchestrator/intents.py) | +36 on 2026-09-27 |
| 883 | [portal/src/components/tasks/TaskDialog.tsx](../../portal/src/components/tasks/TaskDialog.tsx) | **crossed the line** — was on Watch at 793; +73 on 2026-09-22 for #490's conflict handling. **Next step:** extract that state machine (`PendingConflict`, `saveThen`, `reportSaveFailure`, the Reload handler) into a `useConflictResolution` hook beside `ConflictNotice` — deliberately deferred until the estimate builder is wired, so a second caller shapes its API |
| 860 | [portal/src/components/Layout/PortalLayout.tsx](../../portal/src/components/Layout/PortalLayout.tsx) | logged **three** times (894 / 878 / 838). Next: extract `PortalSidebar.tsx` (lines 398-580) with one `{company, user, unreadCount, isCollapsed, ...handlers}` prop object, then `MobileNavDrawer.tsx` |
| 860 | [platform/services/maple_metrics.py](../../platform/services/maple_metrics.py) | the metrics engine, first measured 2026-10-06; +7 that day (`pre_tax_total`). **Next step:** the Phase 3 ratios (`run_win_rate`, `run_margin` and their helpers) into `maple_ratios.py` |
| 837 | [platform/services/google_drive_service.py](../../platform/services/google_drive_service.py) | 2026-09-23: image placement moved to `services/google_doc_images.py` (was 910 at peak); `create_estimate_from_template` split into helpers. Still 37 over |
| ~~1,027~~ 322 | [platform/agents/planner/execute.py](../../platform/agents/planner/execute.py) | **RESOLVED 2026-10-08** — split before switchover phase 5, no behavior change: the handlers moved to `execute_records.py` (contacts, properties, materials, roles, templates, tasks; 404), `execute_estimates.py` (estimate reads joined its writes; 309), `execute_links.py` (the notes feed joined links and notes; 142) and `execute_figures.py` (catalog figures, dashboard, metric; 94). `execute.py` keeps the meta replies, the gate and the run, and builds `COVERED` from each module's `HANDLERS`; `test_each_op_has_one_handler_across_the_executors_modules` fails on an op two modules register. Move to the archive in the next cleanup |
| 817 | [platform/agents/planner/schema.py](../../platform/agents/planner/schema.py) | **crossed the line 2026-10-11** (was 785): phase 8 added fields (stale_days, before_tax, days, within, limit, the task refinements). **Next step:** the follow-up and answer actions (RedoLast, RefineLast, ShowMore, Answer) or the figures (Metric, Dashboard, CatalogFigure) into `schema_reads.py`, as schema_edits/schema_fields already are (review 2026-10-11 #73, deferred) |

**Highest-value split, unchanged:** `routers/auth.py` → extract the invitation
lifecycle into `routers/invitations.py` (~400 lines, a clean seam, leaves
`auth.py` near the threshold).

#### Test files over 800 lines

**Stale since 2026-09-28** (review 2026-09-28 #11, deferred): the source table
above was re-measured that day, this one was not. Thirteen counts are out of
date (e.g. test_material_agent.py is 2,193, test_orchestrator_intents.py
2,580, test_property_agent.py 2,278, test_maple_task_operations.py 2,023), and
three files over 800 lines are missing: `tests/maple_conversations/corpus.py`
(1,354), `test_command_grammar.py` (957), `test_address_service.py` (855).
Re-measure with `wc -l`, add the three rows, re-sort.

Softer guideline — inline-explicit setup is a deliberate trade against hidden
fixtures — but these are past the point of scanning.

| Lines | File |
|------:|------|
| 6,194 | platform/tests/test_estimate_agent.py |
| 5,565 | platform/tests/test_estimate_api.py |
| 4,329 | platform/tests/test_orchestrator_endpoint.py |
| 2,655 | platform/tests/test_contact_agent.py |
| 2,493 | platform/tests/test_orchestrator_intents.py |
| 2,431 | platform/tests/test_maple_estimate_field_edits.py |
| 2,218 | platform/tests/test_property_agent.py |
| 2,020 | platform/tests/test_material_agent.py |
| 1,984 | platform/tests/test_maple_task_operations.py |
| 1,501 | platform/tests/test_auth_api.py |
| 1,371 | platform/tests/test_text_utils.py |
| 1,367 | platform/tests/test_maple_task_crud.py |
| 1,325 | platform/tests/test_tasks_api.py |
| 1,219 | portal/tests/TaskDialog.test.tsx |
| 1,174 | platform/tests/test_cross_resource_joins.py |
| 1,138 | platform/tests/test_maple_work_item_context.py |
| 957 | platform/tests/test_user_api.py |
| 926 | portal/tests/TasksPage.test.tsx |
| 925 | platform/tests/test_task_convert_api.py |
| 923 | platform/tests/test_labour_agent.py |
| 922 | platform/tests/test_maple_estimate_targeting.py |
| 907 | platform/tests/test_maple_work_item_edits.py |
| 890 | platform/tests/test_estimate_edit_executor.py |
| 883 | platform/tests/test_maple_listed_positional_reference.py |
| 862 | platform/tests/test_company_api.py |
| 823 | platform/tests/test_estimate_gathering.py |
| 822 | platform/tests/conftest.py |
| 818 | platform/tests/test_agents_api.py |
| 808 | platform/tests/test_llm_usage_tracking.py |

`test_llm_usage_tracking.py` (added 2026-10-07, review #4, deferred) crossed 800 with the
prompt-caching and credits tests; its seam is `TestCachedTokenPricing` + `TestCredits` →
`tests/test_llm_credits.py`.

`test_maple_task_operations.py` has the only pre-planned split:
`test_maple_task_notes.py` / `_ops.py` / `_text_helpers.py` / `_perf.py`, on
seams that already exist as separate classes.

#### Functions over the 50-line guideline

| Lines | Function |
|------:|----------|
| 822 | `_orchestrate_turn` — routers/agents.py:1057 (the endpoint body since #689 moved the double-send claim into `orchestrate_agent_endpoint`; was `orchestrate_agent_endpoint` at 607 on 2026-09-27's first measure, +122 over the multi-turn push. The multi-turn design (2026-09-27 §5.1) made its pending handlers answer dispatchers behind one gate — the natural first cut is those dispatchers and the router pre-handlers into `routers/agent_helpers/`) Re-measured 822 on 2026-10-07; +28 that day (794 → 822) for the unanswered tracker's `_track_unanswered` closure and the crash-record hand-off. |
| 381 | `update_estimate` — routers/estimates.py:959 (grew ~18 lines on 2026-09-22 for #490's conditional write + 409 translation, +5 on 2026-10-01 for the tenant checks; the next thing added here should come out as a helper, e.g. `_write_estimate_update(existing, update_data, base_version)`, rather than grow the body) |
| 124 | `create_estimate` — routers/estimates.py:299 (first measured 2026-10-01: 118 before, +6 for the property and line checks before the slot claim. Extract `_assert_create_refs(company_obj_id, payload)` — tenant batch 1 review #2) |
| 99 | `duplicate_estimate` — routers/estimates.py:790 (first measured 2026-10-01: 93 before, +6 to drop another company's property from the copy; extract the clone into `_clone_estimate(source, user_email)`) |
| 195 | `run_task_conversion` — services/task_convert.py:45 (first measured 2026-10-01: 191 before, +4 for the property check before the slot claim; split into claim / generate-and-save / file-photos / link-or-delete helpers) |
| 62 | `update_task` — routers/tasks.py:308 (first measured 2026-10-01: 59 before, +3 for the property check. Add `_assert_property_belongs_to_company(property_id, company)` beside `_assert_status_belongs_to_company` and use it in both task routes — tenant batch 1 review #3) |
| 57 | `create_task` — routers/tasks.py:98 (first measured 2026-10-01: 56 before, +1; the same helper — tenant batch 1 review #4) |
| 76 | `archive_estimate` — routers/estimates.py:1394 (first measured 2026-10-01, ~+1 for moving the tenant 404 ahead of the status answer — tenant batch 2 review #1. Extract `_archive_actor(decoded_token, estimate) -> User` — the email/user lookup, the tenant 404 and the creator-or-Owner/Admin check — shared with `unarchive_estimate`) |
| 76 | `unarchive_estimate` — routers/estimates.py:1473 (first measured 2026-10-01; a near-copy of `archive_estimate`'s authorization block — the same `_archive_actor` helper — tenant batch 2 review #2) |
| 67 | `sync_payment_method` — routers/billing.py:443 (61 before 2026-10-01, +6 for the card-ownership 404 — tenant batch 2 review #3. Move the Stripe calls into `_make_default_card(stripe, company, payment_method_id) -> (brand, last4)`) |
| 277 | `handle_pending_property_link_confirmation` — routers/agent_helpers/pending_property_link.py:141 |
| ~270 | `OnboardingPage` component body — portal/src/pages/OnboardingPage.tsx:84 |
| ~264 | `TourRunner` — portal/src/components/tours/TourManager.tsx:83 |
| 282 | `OrchestratorAgent.process()` — agents/orchestrator/service.py:1883 (god-method; +19 on 2026-09-24 — move the two new early exits into one `_match_estimate_conversation_lane()`, review #67) |
| 196 | `handle_pending_optional_follow_up` — routers/agent_helpers/optional_follow_up.py:462 (down from ~281 by #326; #326 claimed this was already tracked here — it was not) |
| 69 | `_delegate_synthetic` — routers/agent_helpers/optional_follow_up.py:393 (was 95; the 2026-09-22 review split `_envelope_confidence`, `_chain_next_follow_up` and `_propagate_result_extras` out of it. The remainder is ~22 lines of docstring, an early-return guard and one dict literal — no non-arbitrary seam left, so treat this row as recorded, not actionable) |
| 64 | `get_optional_follow_up_spec` — routers/agent_helpers/optional_follow_up.py:216 (pre-existing; it is a single allowlist dict literal, so the length is data, not logic) |
| 176 | `_handle_update_estimate_work_item_update_field` — agents/estimate/work_item_handlers.py:851 |
| 396 | `EstimateAgent.process` — agents/estimate/service.py:821 (+13 on 2026-09-24, +14 on 2026-09-25 for the bulk-delete/equipment guard; move the CRUD short-circuit block into `_process_crud_intent(...)`, review #71) |
| 126 | `delegate_get_estimate` — routers/agent_helpers/delegate_get_estimate.py:252 (+35 on 2026-09-24; one helper per rung plus `_render_estimate_summary`, review #62; was 182 — its reply tail moved to `estimate_details_reply` 2026-10-08) |
| 94 | `estimate_details_reply` — routers/agent_helpers/delegate_get_estimate.py:380 (new 2026-10-08, switchover phase 2b: the tail of `delegate_get_estimate`, moved whole as the reply the planner's executor shares; split into `_field_answer_envelope(...)` (the `if field:` branch) and `_details_text(est_payload, property_label, customers)` — review 2026-10-08 (2b) #4, deferred) |
| 157 | `_run_edit_commands` — agents/estimate/edit_executor.py:257 (new 2026-09-24, +18 in the third review pass for the dry-run confirmation and the transient/bug error split, +7 in the fourth for the pin snapshot, +12 on 2026-10-05 splitting the save failure the same way, #619; extract `_persist_batch`, `_success_envelope` and the exception branches, review #57) |
| 114 | `run_update_estimate` — routers/agent_helpers/estimate_update.py:163 (+44 on 2026-09-24; extract `_dispatch_to_planner` and `_build_dispatch_context`, review #63) |
| 123 | `_dispatch_confirmed_intent` — routers/agent_helpers/fuzzy_confirmation.py:65 (+25 on 2026-09-24, +30 on 2026-09-25 for the delete permission check and audit — move that branch into `_confirm_delete(...)`; a `sub_op` → handler dict, review #64) |
| 484 | `_handle_list_estimates` — agents/estimate/crud_handlers.py:1180 (first measured 2026-09-29; 489 at that day's HEAD, 484 after the sold-estimates work. Reads the question, resolves the address/property/contact/material-line constraints, builds the filter, queries, and builds four replies. **Next step:** move the reply building — count / total / empty / list, all from one `described` — into a `_list_reply(...)` helper, and the filter building into `_list_filters(list_query, …)`; the question is already read by `agents/estimate/list_query.py`) |
| 91 | `_resolve_estimate_code_or_title` — agents/estimate/crud_handlers.py:1948 (+21 on 2026-09-24; move the forced-code, open-work-item and offer steps into helpers, review #69) |
| 87 | `finalize_orchestrate_result` — routers/agent_helpers/finalize_result.py:173 |
| 68 | `_handle_analytics_query` — agents/estimate/crud_handlers.py:1843 (first measured 2026-10-06; +2 that day for tax, the breakdown's note kept in `_analytics_breakdown`). **Next step:** a table of matched card → handler in place of the if/elif chain |
| 56 | `dashboard_breakdown` — agents/estimate/crud_handlers.py:2144 (new 2026-10-08, switchover phase 2c: `_analytics_breakdown`'s body moved whole as the reply the planner shares; extract `_division_lines(analytics, label)` and `_status_lines(analytics, label)` — review 2026-10-08 (2c) #3, deferred) |
| 54 | `work_item_field_reply` — agents/estimate/work_item_field_handlers.py:633 (was `_handle_query_work_item_field`, 85 lines, +24 on 2026-09-24; its tail moved here 2026-10-08 as the reply the planner's executor shares, the handler now ~40. Extract `_describe_work_item_field` — the per-field `if/elif` returning `resp` — review #65; review 2026-10-08 (2b) #5, deferred) |
| 62 | `answer` — agents/estimate/focus_questions.py:136 (47 → 62 on 2026-10-08, switchover phase 2b: title, description and division answers for the planner. Move those three into `_answer_text_field(field, estimate, label, items)`, called before the work-item branches; no reply change — review 2026-10-08 (2b) #6, deferred) |
| 80 | `_classify_via_action_domain` — agents/orchestrator/service.py:2682 (+16 on 2026-09-24; extract `_apply_note_add_target`, review #66) |
| 66 | `build_edit_snapshot` — agents/estimate/edit_planner.py:66 (new 2026-09-24; extract `_snapshot_work_item`, `_active_entry`, `_chat_slice`, review #58) |
| 62 | `find_estimate_from_context_or_message` — routers/agent_helpers/estimate_resolver.py:144 (+12 on 2026-09-24; extract `_from_named_or_listed`, review #70) |
| 53 | `_update_estimate_anchor` — routers/agent_helpers/finalize_result.py:118 (new 2026-09-24; extract `_estimate_from_flat_result`, review #61) |
| 66 | `_resolve_target` — agents/estimate/edit_executor.py:530 (new 2026-09-24; extract `_resolve_active`, review #59) |
| 131 | `_handle_update_estimate_work_item_remove` — agents/estimate/work_item_handlers.py:749 (126 before 2026-09-24; next step: route the removal through the executor's `RemoveWorkItem`, which already confirms and persists — third pass #31) |
| 68 | `_prepare_estimate_turn` — agents/estimate/work_item_context.py:452 (new 2026-09-24, +8 in the fourth pass for the cancel reply; one resume helper per pending op, e.g. `_resume_choice` / `_resume_value` — third pass #30) |
| 51 | `_plan_and_apply_edits` — agents/estimate/edit_planner.py:236 (crossed 50 on 2026-09-25 with the material-cost refusal; extract the `unsupported_reason` dispatch into `_answer_unsupported(plan, ...)`) |
| 51 | `_confirm_division_guess` — agents/estimate/edit_executor.py:426 (new 2026-09-24, crossed 50 in the fourth pass naming removals from the loaded list; extract `_removal_labels(target, commands, pins)`) |
| 51 | `_match_work_items` — agents/estimate/work_item_handlers.py:576 (crossed 50 in the fourth pass; extract the forced-pick block into `_forced_pick_matches(...)`) |
| 53 | `_match_listed_positional_follow_up` — agents/orchestrator/service.py:1058 (47 at HEAD; extract the scope check into `_list_pick_scope_matches` — fourth pass #33) |
| 61 | `_resolve_intent_with_history` — agents/orchestrator/service.py:3230 (55 at HEAD, grew with the bare-reply and no-inferred-delete guards; extract `_history_action_allowed(message, action)` — fourth pass #34) |
| 84 | `handle_estimate_fuzzy_confirmation` — routers/agent_helpers/fuzzy_confirmation.py:167 (79 at HEAD — fourth pass #35) |
| 316 | `delegate_create_estimate` — routers/agent_helpers/delegate_create_estimate.py:102 (309 at HEAD, grew with the anchor write; extract the follow-up stash block — fourth pass #36) |
| ~167 | `MarkdownDescriptionEditor` component body — portal/src/components/common/MarkdownDescriptionEditor.tsx:252 |
| 153 | `_handle_update_estimate` — agents/estimate/crud_handlers.py:2378 (+14 on 2026-09-24; extract the work-item dispatch into `_dispatch_work_item_op(...)`, review #68) |
| ~120 | `install()` — website/contact-modal/install.js |
| ~115 | `compute_analytics` — routers/estimates.py:507 |
| 112 | `MaterialGapsTable` — portal/src/components/estimates/InventoryGapsPanel.tsx:106 |
| 105 | `RoleGapsTable` — portal/src/components/estimates/InventoryGapsPanel.tsx:219 |
| 97 | `_handle_update_estimate_apply_template` — agents/estimate/crud_handlers.py |
| 94 | `DocumentsDialog` component body — portal/src/components/estimates/DocumentsDialog.tsx:48 (was 107; `DocumentsDialogFooter` extracted 2026-09-23. About 38 of it is JSX. The next seam is a `useDocumentForm(versions)` hook owning `info` / `kept` / `ready`, the `syncedVersions` reconciliation and `submit`) |
| ~85 | `_send_flow` — routers/support.py |
| ~77 | `assert_token_quota` — services/llm/quota.py |
| 72 | `reinstate_company_account` — routers/companies.py:111 |
| ~70 | `_handle_resolve` — routers/slack_events.py |
| 70 | `_parse_estimate_date_filter` — agents/estimate/text_helpers.py:613 |
| ~69 | `translate_response_bundle` — services/translation.py:661 |
| ~67 | `bootstrap_company_materials` — services/material_bootstrap.py |
| 64 | `_resolve_domain_from_history` — agents/estimate/crud_handlers.py |
| 60 | `detach_non_owner_members` — services/company_service.py:25 |
| 60 | `_reuse_past_work_item` — agents/estimate/llm_pipeline.py:680 (was 93; loops extracted 2026-09-20. Slated for deletion by #557 — drop this row with it) |
| 55 | `sync_user_stage` — services/brevo_contacts.py:361 |
| ~54 | `formatOrchestratorReply` — portal/src/lib/orchestratorReply.ts:39 |
| 53 | `_run` — scripts/backfill_task_readable_ids.py:70 |
| 171 | `_handle_update_subop` — agents/task/service.py:605 (new 2026-09-27; a detector table plus a named-target helper — review 2026-09-27 #47) |
| 129 | `list_tasks_reply` — agents/task/service.py:345 (was `_handle_list_tasks`, 104 lines; its body moved here 2026-10-08 as the reply the planner's executor shares, +25 for the signature and docstring; `_handle_list_tasks` is now 14 lines. Moves with `TaskListBase`, #47) |
| 67 | `_create_task_core` — agents/task/create.py:145 (new 2026-10-08: the body of `_handle_create_task`, about 110 lines, split into its reading and this core both pipelines call — switchover phase 4b. Split into the insert and a `_task_created_reply(task, resolved, unapplied, …)` for the lead and details — review 2026-10-08 (4b) #23, deferred) |
| 89 | `_resolve_list_ask` — agents/task/service.py:399 (new 2026-09-27; make its `teammate()` closure a method, #47) |
| 105 | `_handle_size_command` — agents/material/service.py:1693 (new 2026-09-27; +30 on 2026-09-28 for the material in focus and its "which material?" question; split into `_resolve_size_target(...)`, `_render_size_read(...)` and `_size_command_fields(...)` — review 2026-09-27 #29) |
| 70 | `parse_task_list_ask` — agents/task/list_filters.py:139 (new 2026-09-27; one reader per filter phrase) |
| 63 | `open_questions` — routers/agent_helpers/open_question.py:235 (new 2026-09-27; one small reader per question kind — pending intents, delete records, router flows — concatenated — review 2026-09-27 #56) |
| 132 | `_handle_awaited_field_value` — agents/task/field_flow.py:117 (about 120 before 2026-09-28; +6 then for replies that restate the command. Extract `_read_awaited_value(field, message)` for the cancel check and restated value, and turn the per-field if-chain into a dispatch dict of `_apply_awaited_<field>` coroutines — review 2026-09-28 #4) |
| 676 | `TasksPage` component body — portal/src/pages/TasksPage.tsx:64 (637 before 2026-09-28; +39 then for Maple's `?open=` task links — the fetch-by-id fallback, its ref guard and the dialog shared with the error state. **Next step:** move the deep-link handling into `portal/src/hooks/useTaskDeepLink.ts` taking `{ tasks, isLoading, onOpen: setEditingTask }` and returning `requestedTaskId` for the two initializers; `tests/TasksPageDeepLink.test.tsx` covers it unchanged — review 2026-09-28 #1) |
| — | seven functions in `platform/agents/task/` (see archive for the list) |
| — | four functions in `agents/estimate/assumption_handlers.py` (measured 2026-10-09, after the detector moved to `assumption_detect.py` in switchover phase 6c): `_handle_assumption_material_swap` :400 (92), `_handle_assumption_size_adjustment` :680 (63), `_find_size_assumption` :497 (62), `_resolve_swap_material` :280 (58; +7 in 6c for the planner's "Which material?" — extract the two `ask_to_rewrite` clarifies into `_ask_material(...)`) |
| — | functions in `agents/estimate/llm_pipeline.py:677` (per-scope assumptions) |
| 125 | `_finalize_template_estimate` — routers/agent_helpers/template_estimate.py:102 (first measured 2026-10-05, +16 that day logging the failure, splitting the outage/bug reply and removing an estimate inserted before the failure, #318; extract the create/scale/save block into `_instantiate(processor, company_oid, template, factor, context_payload)`, leaving the gate, audit and envelope here — review 2026-10-05 #4) |
| 51 | `_compare` — services/maple_compare.py:240 (first measured 2026-10-07, review of the planner parity run #1, deferred: the decline check, the both-answered branch and the item matching in one body. Extract the matching loop — from `unsure: List[str] = []` to the leftover-items loop — into `_match(current, current_items, planner_items) -> Tuple[List[str], List[str]]` returning `(why, unsure)`; `_compare` keeps the readings and the verdict. No behaviour change; tests/test_maple_compare.py must pass unchanged.) |
| 62 | `list_contacts_reply` — agents/contact/service.py:2034 (new 2026-10-08, switchover phase 2a: the body of `_handle_list_contacts`, which shrank by as much, as the reply the planner's executor shares; split the row rendering into `_contact_list_items(serialized)` — review 2026-10-08 #10, deferred) |
| 64 | `list_properties_reply` — agents/property/service.py:2458 (new 2026-10-08, phase 2a: moved out of the list fall-through; extract `_property_list_items(serialized)` — review 2026-10-08 #11, deferred) |
| 63 | `list_labours_reply` — agents/labour/service.py:1253 (new 2026-10-08, phase 2a: moved out of the list fall-through; extract `_labour_list_items(serialized)` — review 2026-10-08 #12, deferred) |
| 63 | `list_templates_reply` — agents/template/service.py:282 (new 2026-10-08, phase 2a: moved out of `_handle_list_templates`; extract the envelope into `_templates_envelope(...)` — review 2026-10-08 #13, deferred) |
| 59 | `execute` — platform/agents/planner/execute.py:447 (was 46; phase 8 added step pointing and the policy refusal. Move the per-action loop body into `_run_action` — review 2026-10-11 #43) |
| 60 | `_redo` — platform/agents/planner/followups.py:136 (was 44; a dispatch table of `_redo_metric` / `_redo_dashboard` / `_redo_estimates` / `_redo_get`, as `_redo_list` is — review 2026-10-11 #74) |
| 52 | `_refine` — platform/agents/planner/followups.py:198 (was 41; split the guards into `_refine_refusal(op, change)` — review 2026-10-11 #75) |
| 54 | `resolve_work_item` — platform/agents/planner/resolve.py:386 (was 49; move the `by == "name"` arm and its retry into `_work_item_by_name` — review 2026-10-11 #76) |
| 74 | `_reply_rules` — platform/services/maple_outcomes.py:80 (was 60; themed rule tuples — refusals, limits, errors, rewrites — concatenated — review 2026-10-11 #77) |

#### Watch

`platform/agents/estimate/catalog_matching.py` is at 793 — seven lines under.
The next change to it crosses the line.

`portal/src/pages/TasksPage.tsx` is at 739 — 61 under, after +39 on
2026-09-28. The `useTaskDeepLink` extraction in the functions table above takes
it back under 720.

## Query efficiency — scans, N+1 and missing indexes

Full-collection loads, Python-side filtering, N+1 round-trips and unindexed
sorts. #25 and #26 are the long-standing anchors; everything below is the same
shape of problem in a different collection.

### 25. [MEDIUM] Regex email lookup in `_resolve_user()`
**File**: `dependencies.py:17-26`
**Severity**: MEDIUM

Email is `.lower()`'d at line 17, then looked up with
`User.find_one({"email": {"$regex": f"^{escaped_email}$", "$options": "i"}})`
at line 25-26. The case-insensitive regex defeats index usage on the
`email` field and runs on every authenticated request. `User.email` in
`models/user.py` is stored without normalization, so the regex is defending
against historical mixed-case data rather than the current write path.

Fix: two-step. (a) Add a one-shot backfill script under
`scripts/` that lowercases `User.email` for all existing rows. (b) Normalize
on write (override `__init__` / validator so any create or update lowercases
the field). (c) Replace the regex with `User.find_one(User.email == email)`.
Don't do (c) before (a) — a stray capitalized row would silently fail auth.

### 33. [MEDIUM] `$in` × `$in` bulk-fetch over-fetches the cross-product
**Files**: `routers/equipments.py:138-144`, `routers/labours.py:195-201`
**Severity**: MEDIUM (theoretical) / LOW (in practice)

For a CSV with N distinct names and M distinct units, the query
`{"name": {"$in": names}, "unit": {"$in": units}}` matches every name ×
unit combination in Mongo — up to N×M rows — even though only exact-tuple
matches are used. The Python-side filter `existing_by_key.get((name, unit))`
discards the extras. Harmless for typical CSVs (one unit type, many
names), grows quadratically with mixed CSVs.

Fix (when it bites): switch to `{"$or": [{"name": n, "unit": u} for ...]}`
— exact tuples, no bloat. Not worth doing until we see a CSV where this
matters.

### 60. [MEDIUM] No unique compound index on Material / Contact
**Files**: [platform/models/material.py:32](../../platform/models/material.py),
[platform/models/contact.py:45](../../platform/models/contact.py)
**Severity**: LOW–MEDIUM (data integrity, not an active bug)

Both models declare only `IndexModel([("company", ASCENDING)])`. Concurrent
inserts can produce duplicates for the same `(company, name)`.

The reviewer's proposed fix — "compound unique index on (company, name)
for all inventory models" — is correct for Material but **wrong for
Contact**. Two contacts can legitimately share a full name (two different
"John Smith" homeowners). A Contact uniqueness constraint would need to
include email/phone, and even that is debatable.

Fix: for Material, add `IndexModel([("company", ASCENDING), ("name",
ASCENDING)], unique=True)` — but only after auditing prod data for
existing duplicates; index creation fails if violations exist. For
Contact, no unique index (reviewer was wrong on this one); if
deduplication is a real concern, surface it in the UI on create/update
instead.

**Absorbed:** #66.

### 71. [MEDIUM] Sequential `material.replace()` per remap is slow at scale
**File**: [platform/scripts/db/backfill_material_units.py:60](../../platform/scripts/db/backfill_material_units.py)
**Severity**: MEDIUM (performance, fine for current scale)

`remap_materials_for_unit` iterates materials and calls
`await material.replace()` one at a time, so the cost is roughly
`O(companies × renamed_units × materials_per_company)`. The 2026-04-25
production run touched 191 materials in seconds; at 10k+ materials per
company this would hurt.

Fix (if reused): batch via
```python
Material.find_many({"company": company_id, "sizes.unit": old_unit_id}).update_many(
    {"$set": {"sizes.$[el].unit": new_unit_id, "updated_at": now}},
    array_filters=[{"el.unit": old_unit_id}],
)
```
Skips the `before_event` hook, so set `updated_at` explicitly.

### 73. [MEDIUM] N+1 `find_one` inside bootstrap loops
**File**: [platform/services/rate_card_bootstrap.py:48-54](../../platform/services/rate_card_bootstrap.py)
**Severity**: MEDIUM
**Why it's MEDIUM, not HIGH**: matches the existing pattern in
`division_bootstrap.py`, `material_category_bootstrap.py`, and
`material_unit_bootstrap.py`. Volume is small today (6 templates × 12
companies = 72 queries during backfill), but the cost compounds as more
bootstrappers join the chain.

Fix: pre-load existing names with one query and check membership in the
loop, e.g.
```python
existing_names = {
    rc.name for rc in await RateCard.find({
        "company": normalized_company_id,
        "name": {"$in": [t["name"] for t in templates]},
    }).to_list()
}
```
Apply consistently across all `*_bootstrap.py` modules in one pass to keep
them aligned.

### 157. [MEDIUM] Cross-resource transitive join uses two round-trips instead of $lookup
**File**: [platform/agents/property/service.py:1071](../../platform/agents/property/service.py)
**Severity**: MEDIUM (perf hook)

`_properties_with_estimates_referencing` does TWO Beanie queries —
`Estimate.find` to collect property IDs, then `Property.find` with
those IDs. For tenants with thousands of estimates the first query
loads full estimate documents just to read the `.property` field.

Fix: replace with a single Mongo aggregation pipeline:
```python
Estimate.aggregate([
    {"$match": {"company": ..., "<field>": {"$in": ids}}},
    {"$group": {"_id": "$property"}},
    {"$lookup": {"from": "properties", "localField": "_id",
                 "foreignField": "_id", "as": "property"}},
])
```

Defer until perf measurements demand it; current shape is correct
and clear. Worth coupling with a fixture-based perf test.

### 328. ~~[MEDIUM] `_resolve_estimate_by_title` full-collection scan now on three more paths~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** with #669 — `_match_estimates_by_title` calls `title_reference.find_named_estimates`, which matches on titles alone and loads only the matches. No cap was added: a capped list matched the wrong estimate as an exact target (round 32 #2).

The (pre-existing) resolver does `Estimate.find(company == oid).to_list()` and
substring-matches titles in Python. The new `_resolve_estimate_code_or_title`
wires it into notes/description/link updates, so every code-less update turn
loads ALL of a tenant's estimates. Single company-scoped query (not N+1) and
fine at typical tenant sizes, but unbounded. Fix: add a `.limit(...)` bound or
a server-side case-insensitive regex match on `title`; `company` is already the
indexed filter per the `Settings.indexes` convention.

### 443. [MEDIUM] platform/routers/ops.py:200 — task counts aggregate the whole collection
`_counts_by_company` runs `$group` with no `$match`, and is now called on `tasks`
as well as `users` for the ops Companies list. The page needs counts for at most
100 company ids, but the pipeline scans every task in the database on every load.
Tasks are the highest-volume company-scoped collection (50 per company on Free
alone), so the cost grows without bound while the page's needs stay fixed.
Harmless at present data size; the shape is the problem.
**Suggested fix:** pass the page's company ids and prepend
`{"$match": {"company": {"$in": ids}}}` — the existing
`IndexModel([("company", 1), ...])` prefixes on Task serve it. Applies equally to
the pre-existing users call.

### 506. [MEDIUM] platform/routers/estimates.py:444 — search runs an unindexed regex over title/description
`_search_condition` builds `{"$regex": ..., "$options": "i"}` clauses on `title`
and `description`. A case-insensitive unanchored regex cannot use a B-tree
index, so each search scans the company's estimates. The `company` equality lets
Mongo enter through `company_updated_at_status` first, which bounds the scan to
one tenant — acceptable at current volumes (62 estimates on Dev, a 100-per-period
plan cap) but it degrades linearly with tenant size.

**Selected for fixing but deliberately not fixed:** the finding's own remediation
is "no code change today", and the real fix — an Atlas Search index on
(title, description) — is substantially larger than the finding describes and
premature at these volumes. The repo already runs `mongodb-atlas-local` for
`$vectorSearch` parity, so the capability exists when it is needed.

**Suggested fix:** revisit when a tenant's estimate count makes search latency
visible; add an Atlas Search index rather than a B-tree one. The same reasoning
applies to `GET /tasks?search=`, which has the identical shape.

### 27. [LOW] Inefficient merge pattern in bulk work-item endpoint

**Update 2026-09-29:** the call moved to `platform/routers/agent_helpers/estimate_update.py:116` and is **not** a no-op — each parsed item goes through `_build_extra_parsed_item`, which stamps the company markup/overhead defaults. Dropping the call would regress; only a clarifying comment or rename is safe.
**File**: `routers/agents.py:1621-1632`
**Severity**: LOW (code clarity)

The code calls
`merge_job_items_with_original_descriptions([], new_job_items_raw, ...)`
with an empty first argument, which turns the helper into a no-op, then
manually appends the parsed items to `target_estimate.job_items`. The
helper at `routers/estimates.py:404-415` is designed for reconciliation
between an existing request list and newly parsed items — passing `[]`
bypasses that contract. Canonical usage is in `prepare_generated_estimate`.

Fix: either call the helper with the real existing items (if reconciliation
is wanted) or drop the call entirely and just build items from
`new_job_items_raw` via `build_job_items_from_parsed`. Works fine today; the
concern is that the next reader will assume reconciliation is happening.

### 28. [LOW] Unbounded `ChangeLogEntry.find_all()`
**File**: `routers/change_logs.py:23-26`
**Severity**: LOW

`ChangeLogEntry.find_all().sort(...).to_list()` with no `.limit()`. Current
volume is small (curated changelog), so this is an anti-pattern waiting to
bite rather than an active problem.

Fix: add `.limit(100)` and accept an optional `?limit=` / `?offset=` query
param. Cheap to do; reviewer should have filed as LOW, not WARNING.

### 62. [LOW] Python-side sort in `get_material_categories` / `get_material_units`
**Files**: [platform/routers/material_categories.py:48](../../platform/routers/material_categories.py),
[platform/routers/material_units.py:49](../../platform/routers/material_units.py)
**Severity**: LOW (cleanliness, not performance)

Both handlers call `sorted(items, key=lambda x: x.name.lower())` after
`.to_list()`. Reviewer framed this as "unscalable" — overstated, since
category/unit counts per company are dozens, not millions. Real reason
to fix is consistency, not throughput.

Caveat on the fix: the reviewer's proposed
`.sort(+MaterialCategory.name)` is byte-order (case-sensitive) unless a
collation is attached. The current Python sort is case-insensitive via
`.name.lower()`. A straight DB-side sort would change ordering for
mixed-case names (e.g., "apple" vs "Banana").

Fix (when next touching these files): switch to
`await MaterialCategory.find(...).sort(+MaterialCategory.name).to_list()`
**with a collation** `{locale: "en", strength: 2}` so case-insensitive
order is preserved. Same shape for `MaterialUnit`. If attaching a
collation is awkward via Beanie, leave the Python sort — clarity beats
a half-done DB push-down.

### 410. [LOW] platform/routers/tasks.py — sort=due_date sorts in memory, unindexed
The $sort runs on computed fields, so no index can serve it; Mongo sorts the company's matched tasks in memory (100MB stage cap). Fine at current volumes, and the dashboard passes limit=5, but it's O(company task count) per dashboard visit.
**Suggested fix:** None needed now; if task volumes grow, maintain a stored "due-or-updated" sort field on write, indexed under the existing Settings.indexes convention.

### 415. [LOW] platform/models/llm_usage_event.py:46 — no index for feature-filtered usage queries
Public usage events all carry `company=None`. They're reachable efficiently via
the existing `(company, created_at)` index (querying `company == None` uses it),
but the natural ops query — filter by `feature == "maple_public"` over a date
range — has no supporting index and will collection-scan as `llm_usage_events`
grows.
**Suggested fix:** Add `IndexModel([("feature", 1), ("created_at", -1)])` to
`Settings.indexes` when/if per-feature dashboards materialize; harmless to add
now.

### 715. ~~[MEDIUM] No `company` index, so `_teammate_email` scans users across tenants on the chat path~~ — RESOLVED 2026-09-29

**Resolved 2026-09-29** (name-answers plan phase 3): `User.Settings.indexes` has `company`.

`platform/models/user.py:89` — `User.find(User.company == …)` in `_teammate_email` (operations.py:302) runs on every assignment or teammate filter, but `users` indexes only `email`, so each lookup scans the whole collection. (review 2026-09-27 #42)

**Suggested fix:** Add `IndexModel([("company", ASCENDING)])` to `User.Settings.indexes`.

### 716. ~~[MEDIUM] `due_date` is filtered and sorted with no index, and the docstring says otherwise~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** `Task.Settings.indexes` has `(company, due_date, updated_at desc, _id)` — the due-date lists' filter and their whole sort (`+due_date, -updated_at, +_id`), so the sort and its limit stay index-served and `_list_conditions`' "all fields indexed" is true. Beanie builds it on boot; nothing to drop. Tests: `tests/test_task_due_index.py` (the index exists; the overdue query's winning plan uses it with no SORT stage).

`platform/models/task.py:74` — The new `extra` conditions filter on `due_date` and sort by `+due_date` (agents/task/base.py:216-217, :259), but no index covers `(company, due_date)`, while `_list_conditions` says "All fields used here are indexed". MEDIUM rather than HIGH: the company-prefixed indexes keep the scan to one tenant. (review 2026-09-27 #43)

**Suggested fix:** Add `IndexModel([("company", 1), ("due_date", 1)])`, or correct the docstring.

### 812. ~~[MEDIUM] `find_properties_by_name_or_address` loads every property to match a name~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** the finder reads only the address fields of the company's properties, matches in Python exactly as before, and loads the matches in full — the #669 pattern. The match stays in Python on purpose: the reverse direction (a stored name inside the query, user option a) has no indexed form, and Mongo's `$toLower` would not fold "Île" / "École" the way `str.lower` does. It still reads every property's address row, but no longer every document. `PropertyAgent._find_properties_by_name_or_address` (its twin, over `_list_properties_via_api`) is unchanged. Tests: `tests/test_property_name_lookup.py`.

`platform/agents/cross_resource.py:34` — The finder loads all the company's properties and matches in Python: the query inside the name, street or full address, or a stored name or street inside the query. It serves the estimate customer fallback (`title_reference.resolve_named_estimates`, after a title matches nothing) and the property agent's twin (`PropertyAgent._find_properties_by_name_or_address`). Left out of the slow-lookups batch (#709, #669, #328, #26) because the reverse containment ("Elm House" inside "the elm house job") has no indexed form, and Mongo's `$toLower` lowercases ASCII only, so moving it to `$expr` could miss accented names the Python match finds. (logged 2026-10-04)

**Suggested fix:** Run the forward containment in Mongo (`$regexMatch` on name, street and the composed address, escaped, case-insensitive) and keep the reverse check, or drop it if no phrasing needs it — the customer fallback already re-checks whole words in `_names_whole`. Then project only the fields matched, and share one finder between `cross_resource` and the property agent.

### 819. [LOW] `export_unanswered.py` loads the whole period into memory
`platform/scripts/export_unanswered.py:112` — `collect()` reads every `MapleUnanswered` row between `--since` and `--until` with `.to_list()`. With the 180-day TTL and an early `--since`, that is every unanswered turn for six months held in memory at once. LOW: a manual review script; two weeks of traffic is small. (review 2026-10-07 #9)

**Suggested fix:** Accept it for now; if the collection grows, render per reason with an aggregation (`$group` by reason/detail for the counts) and iterate the rows with an async cursor instead of `.to_list()`.

## Silently swallowed errors

Paths that discard the real failure. #64 is the anchor; #430 is the standing
bandit `B110` baseline (11 bare `except Exception: pass` blocks — a count above
11 means a change added one).

### 64. [MEDIUM] WorkItem divisions fetch swallows errors silently
**File**: [portal/src/components/estimates/WorkItemInlineContent.tsx:73](../../portal/src/components/estimates/WorkItemInlineContent.tsx)
**Severity**: MEDIUM

`.catch(() => setDivisions([]))` hides API failures. If the divisions
endpoint is down, users see an empty dropdown with no signal whether
it's a transient failure or just a freshly-created company. Mirrors the
pre-existing rate-cards pattern, so consistent — but support has no
breadcrumb when this fires.

Fix: log via `console.error` (or a shared error reporter if one exists
later) before the empty fallback. Apply the same change to the
rate-cards `.catch` for consistency.

### 76. [MEDIUM] Backfill swallows per-company exceptions
**File**: [documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py:32](../../documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py)
**Severity**: MEDIUM
The backfill catches every `Exception` per company and prints a one-liner.
A misconfigured DB (auth failure, etc.) scrolls past silently as N
identical errors. Pre-existing convention across migration scripts.

Fix: differentiate infrastructure errors (`ServerSelectionTimeoutError`,
`OperationFailure`) from per-document validation errors and let the former
propagate. Apply the same shape to other migration scripts in one pass.

### 184. [MEDIUM] `response.json()` decode errors no longer caught in `address_service.py`
**File**: [platform/services/address_service.py:366, :409, :468](../../platform/services/address_service.py)
**Severity**: MEDIUM (behaviour change)

Narrowing `except Exception` → `except (httpx.HTTPError,
httpx.TimeoutException)` (the [#41](code-review-followups-archive.md)
fix) achieved the followup's stated goal: any `HTTPException(429)`
raised from inside the `try` propagates instead of being silently
swallowed. The narrower side effect is that `response.json()` —
which raises `json.JSONDecodeError` (subclass of `ValueError`) on
malformed payloads — used to fall into the `[]`/`{}` empty result and
now propagates as a 500 to the caller.

In practice Google Maps returns well-formed JSON, so this is
theoretical. Arguably an improvement (loud failure beats silent empty),
but it's a behaviour change beyond what the followup wording implied.

Fix: if you want the previous soft-fail on malformed payloads, expand
to `except (httpx.HTTPError, httpx.TimeoutException, ValueError):`.
Otherwise leave as-is and accept the loud-fail behaviour.

### 269. [MEDIUM] Overage-dialog audit-event failures swallowed without Sentry capture
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/pages/EstimatesPage.tsx` (the `handleOverageConfirm` and
`handleOverageAddCard` paths) and `portal/src/pages/SettingsPage.tsx`
(`handleConfirmSeatsOverage`, `handleOpenAddCardFromWarning`) wrap
`usersApi.recordOverageEvent(...)` in bare `try { ... } catch {}`.
Failures are silent, so a regression in the `/users/me/overage-event`
endpoint or the audit-log pipeline would go unnoticed.

`portal/src/components/billing/AddPaymentMethodModal.tsx:197` already
establishes the pattern of `Sentry.captureException(e, { tags: ... })`
for non-blocking failures. Apply the same pattern to all four sites so
silent regressions surface in Sentry.

Fix: replace each `catch {}` with
`catch (e) { Sentry.captureException(e, { tags: { feature: "overage_dialog", action: "<acknowledged|add_card_clicked|pref_persist>" } }); }`.

### 290. [MEDIUM] Dashboard analytics fetch error is silent
**Where:** `portal/src/pages/DashboardPage.tsx` — the `estimatesApi.analytics(...).catch(() => setAnalytics(null))` branch.

**Issue:** Network/server errors are swallowed and the page silently shows `$0` cards. A user can't distinguish "no estimates yet" from "the API is down".

**Fix:** Track an `analyticsError` state and render a small inline note ("Couldn't load analytics — retry") when set.

### 318. ~~[MEDIUM] Broad `except Exception` in template instantiation swallows the real failure~~ — RESOLVED 2026-10-05

**Resolved 2026-10-05:** the create/scale/save block logs `Template estimate instantiation failed for company <id>: <type>` before releasing the slot: a `TRANSIENT_WRITE_ERRORS` hiccup (`services/sparse_update.py`, shared with the edit executor) at WARNING with "try again", anything else at ERROR with "Something went wrong on my side … You can create it on the Estimates page", since a retry would fail the same way. An estimate already inserted when the failure struck is deleted first (`_discard_unfinished`), so the reply's "couldn't create" is true and the released slot leaves no unbilled empty draft per attempt (review 2026-10-05 round 3). The router passes `_create_estimate_from_template(audit=False)` and keeps its own create audit, written only after a successful save, so a template estimate is audited as created once and a failed attempt leaves no audit trace (rounds 4–5). The design that makes the cleanup necessary is #818. The type only, no traceback: Sentry captures frame locals, and this frame holds the user's token claims and message (see #817). Pinned by `test_a_failed_instantiation_is_logged_and_frees_the_slot`.

**Where:** `platform/routers/agent_helpers/template_estimate.py:156`

**Issue:** The create/scale/save block catches bare `Exception`, releases the quota slot, and returns a generic "try again" with no logging. A genuine bug (scaling math, model validation) is invisible in logs and indistinguishable from a transient DB blip.

**Fix:** `logger.exception("template instantiation failed for company %s", company_ctx)` before returning the friendly message, matching the pattern in `material/service.py:_load_categories`.

### 330. [MEDIUM] `target.save()` unwrapped in `_handle_update_estimate_description`
The new description handler follows the notes handler's bare-save precedent,
but the property-link handler in the same file wraps its save in try/except
with a friendly "couldn't reach the database" envelope — the file has two
precedents and the new code picked the weaker one. A Mongo hiccup surfaces as a
generic 500 instead of the retry prompt. Fix: wrap like the link path, or
extract a `_save_or_error` helper and use it in all three field-edit handlers.

### 461. [MEDIUM] portal/src/pages/auth/LoginPage.tsx:201 — terminal invitation failure silently dropped for unverified users
When the sign-in is unverified AND the invitation accept failed, `inviteError` is discarded so
the verify banner wins — deliberate, and commented in the code. But on a terminal status
(403/404/409) the pending invitation is ALSO cleared, so the token is gone and the user was
never told. They verify, sign back in, and land in `/onboarding` with no company and no
indication an invitation ever existed, let alone lapsed. This is the exact path for an invitee
whose invitation hits the 7-day expiry while they work through verification — the scenario the
change was written to unblock.

**Suggested fix:** when `inviteError` had a terminal status, append a second line to the verify
banner ("Your invitation has expired — ask them to send a new one."). Turns a silent dead end
into an actionable one. Needs a test in `tests/LoginPageInvitationOrdering.test.tsx`.

### 68. [LOW] `backfill_divisions.py` uses broad `except Exception`
**File**: [platform/scripts/db/backfill_divisions.py:54](../../platform/scripts/db/backfill_divisions.py)
**Severity**: LOW (script context, not a service handler)

The script intentionally swallows per-company exceptions to keep going
through the company list, then reports failures and exits non-zero.
Acceptable for a one-off backfill — flagging only because spec calls
broad excepts CRITICAL by default. No action expected unless the script
gets reused for repeated migrations.

### 312. [LOW] `try_claim_estimate_slot` override path doesn't warn on missing document
**Where:** `platform/services/estimate_quota.py:76`

**Issue:** When `company.overage_billing_disabled` is true, `find_one_and_update` returning `None` (document gone mid-request) is silently ignored — the in-memory counter is stale but `True` is returned. No log entry makes this invisible in operational monitoring.

**Fix:** Add `logger.warning("overage_billing_disabled slot claimed but company %s not found in DB", company.id)` inside the `if result is None` branch.

### 314. [LOW] Filter-driven estimate refetch swallows errors silently
**Where:** `portal/src/pages/EstimatesPage.tsx` — `loadData` (~line 180) + the initial-load effect (~line 305)

**Issue:** Toggling the Archived / All Status filter changes `includeArchived`, which re-runs the load effect via `loadData({ showLoading: false })` (the deliberate fix so the page doesn't unmount the open dropdown). But `loadData`'s `catch` only sets `error` when `showLoading` is true, so a failed archived refetch shows no error and no archived rows — a silent partial failure. This matches the existing `loadData({ showLoading: false })` background-refresh convention (polling, `performDuplicate`), so it's intentional, not a regression.

**Fix:** If feedback on filter-refetch failures is wanted, surface a non-blocking inline toast/banner rather than the full-page `ErrorState` (which would re-introduce the unmount-the-dropdown bug this change fixed).

### 387. [LOW] portal/src/lib/supportFirestore.ts — console.error in listener error paths
Error-path logging only (rules/App Check misconfiguration surfaces here) — arguably desirable during the dev-only rollout.
**Suggested fix:** Keep for Phase 1; route to a proper client logger if one is adopted.

### 430. [LOW] platform/agents/** — 11 bare `except Exception: pass` blocks (bandit B110)
Surfaced by the first bandit scan (2026-07-27) and left unfixed deliberately —
all pre-existing, and each needs its intent understood rather than a blanket
edit. Sites, re-counted 2026-09-20: `agents/contact/service.py` (2),
`agents/equipment/service.py` (2), `agents/labour/service.py` (2),
`agents/material/service.py` (2), `agents/property/service.py` (2),
`agents/estimate/service.py` (1). The two in
`routers/agent_helpers/estimate_resolver.py` have since been fixed, which is
what took the baseline from 13 to 11.

All follow one shape: *try an enhancement or resolution strategy; on any
failure fall through to a safe default.* The swallow is intentional — but a
bare `except Exception` with `pass` and no logging makes a genuine defect (a
`TypeError` in a suggestion builder, an `AttributeError` in the resolver)
indistinguishable from the expected miss, and nothing reaches the logs. This is
the same class the `/code-review` cross-cutting checklist rates CRITICAL
("bare `except:` or `except Exception: pass` hiding errors").

**Do not silence these with `# nosec`** — that would suppress a real finding
rather than resolve it. Until they're fixed, `./run_bandit.sh` reports exactly these 11;
a count above 11 means the change under review added one. CLAUDE.md carries the
same number — update both together.
**Suggested fix:** per site, narrow the exception to what's actually expected
and add `logger.debug(...)` (or `logger.exception(...)` where a failure is not
routine) before falling through. Best done as one focused sweep, since the
pattern is near-identical across the six files.

## Duplicated code and twin files

Copy-paste that has to be changed in two or more places and can drift. Includes
the three twin-file pairs (Materials/Activities tables, Categories/Units tabs,
the settings tabs).

### 144. [MEDIUM] Alternating row color computed inline twice
**Files**:
- [portal/src/components/estimates/MaterialsTable.tsx](../../portal/src/components/estimates/MaterialsTable.tsx)
- [portal/src/components/estimates/WorkItemInlineContent.tsx](../../portal/src/components/estimates/WorkItemInlineContent.tsx) (Activities table)

**Severity**: MEDIUM

`const rowBg = idx % 2 === 1 ? "bg-emerald-50" : "bg-white"` is
duplicated across two `map()` bodies. Logic is correct (works around
the activities table's sub-row Fragment shifting `:nth-child(even)`
parity) but the rule is in two places.

Fix: extract a shared `getRowBg(idx: number)` helper into a small
utility module or co-locate it where both tables can import it.

### 219. [MEDIUM] `VALID_PLAN_KEYS` duplicates `PLAN_LOOKUP_KEYS` from `billing-plans.ts`
**File**: [portal/src/pages/OnboardingPage.tsx:21-25](../../portal/src/pages/OnboardingPage.tsx)
**Severity**: MEDIUM

The new `VALID_PLAN_KEYS` set added by [#205](code-review-followups-archive.md)
hardcodes the three plan lookup keys, but
`portal/src/lib/billing-plans.ts:136-140` already exports
`PLAN_LOOKUP_KEYS: PlanLookupKey[]`. Two lists to keep in sync — adding
a fourth plan in `billing-plans.ts` would silently reject the new key
during localStorage hydration without a single line in this file
indicating why.

Fix: `import { PLAN_LOOKUP_KEYS } from "../lib/billing-plans"` and
derive `const VALID_PLAN_KEYS: ReadonlySet<string> = new Set(PLAN_LOOKUP_KEYS)`.
Roll into the next OnboardingPage edit.

### 302. [MEDIUM] TYPE_CHECKING stub blocks duplicate signatures from sibling mixins
**Where:** `agents/estimate/crud_handlers.py:95-179` (19 stubs) and `agents/estimate/work_item_handlers.py:65-91` (4 stubs).

**Issue:** Each stub block lifts method signatures from sibling mixins (`CrudParsingMixin`, `WorkItemHandlersMixin`, etc.) and re-declares them inside `if TYPE_CHECKING:` so mypy stops flagging attr-defined on the cross-mixin calls. If a signature in the real implementation drifts (e.g. `_crud_envelope` adds a new keyword param), the stub won't catch it — mypy silently uses the stub.

**Fix:** define an `EstimateAgentHostProtocol(Protocol)` in `agents/estimate/host_protocol.py` (or a shared types module) that captures the cross-mixin contract once. Each mixin can reference the Protocol via `Self` bound or via inheritance from a shared base. Short-term mitigation: per-method docstring pointers (`# See agents/estimate/crud_helpers.py:381 — keep in sync`). Worth doing if the stubs grow further; for now the 23 stubs are stable enough.

### 317. [MEDIUM] `recentEstimates.ts` reinvents archived-status normalization
**Where:** `portal/src/lib/recentEstimates.ts:18`

**Issue:** `(e.status ?? "").trim().toLowerCase() !== "archived"` open-codes a partial status normalization when the canonical `normalizeEstimateStatus` in `lib/estimateStatus.ts` is already used in ~6 other modules. Risks drift if status values gain spacing/casing variants.

**Fix:** `import { normalizeEstimateStatus } from "./estimateStatus"` and compare `normalizeEstimateStatus(e.status) !== "archived"`. (Same single-source-of-truth concern as #315.)

### 331. [MEDIUM] Twin datetime formatters duplicate the label format
`_fmt_dt` (`agents/estimate/crud_helpers.py`, datetime objects) and
`_fmt_iso_dt` (`routers/agent_helpers/delegate_get_estimate.py`, ISO strings)
are deliberate and cross-referenced in comments, but the format string
`"%Y-%m-%d %H:%M UTC"` is duplicated and will drift. Fix: share the constant
(or one helper accepting both input types) from a neutral module.

### 336. [MEDIUM] `load-standard` endpoints duplicate the audit-log loop (~55 lines each)
`routers/material_categories.py::load_standard_material_categories` and
`routers/material_units.py::load_standard_material_units` are verbatim twins
apart from the enum values, and each is marginally over the 50-line guideline
(complexity is low — linear, max 2-level nesting). Fix: extract the
removed-states audit-log loop into a small shared helper (e.g. in
`routers/agent_helpers` or a `routers/_audit_helpers.py`), which also pulls
both handlers under the line guideline.

### 337. [MEDIUM] Materials Categories/Units tabs are twin files, worsened by this change
`portal/src/components/settings/MaterialCategoriesTab.tsx` and
`MaterialUnitsTab.tsx` were already near-identical; the reload state, handler,
and modal added ~110 more duplicated lines each (differing only in wording and
API object). Divergence bugs get likelier each time. Fix: extract a shared
`ResourceCatalogTab` parameterized by labels + API object, the same move that
extracted `ActionsMenu` from `RowActionsMenu`.

### 456. [MEDIUM] website/index.html:698 — footer icon block duplicated five ways
The social row adds ~13 lines of CSS and ~20 lines of SVG markup, copy-pasted verbatim into
all five static pages (`index`, `pricing`, `faq`, `privacy`, `terms` — ~165 duplicated lines
total). A future edit — one URL change, one glyph swap — has to land in five files or the
pages silently diverge. This follows the existing convention (the whole footer is already
duplicated) and `src/content/__tests__/social-footer-links.test.ts` does assert all five stay
in sync, so the risk is contained rather than open-ended.

**Suggested fix:** no action needed if the duplicated-footer convention is intentional. If it
is being outgrown, the fix is a shared partial injected at build time rather than a per-change
workaround — that is a separate refactor covering the whole footer, not just the icons.

### 542. [MEDIUM] portal/tests/InventoryGapsAccordion.test.tsx:96 — `spanOf` test helper duplicated across two files

An identical `spanOf(row, label)` helper (parse `col-span-N` off the cell carrying a field label)
now exists in both `InventoryGapsAccordion.test.tsx` and `LineItemAccordion.test.tsx`, as does a
near-identical `stubViewport` matchMedia stub. Both encode the same grid contract, so a change to
the span convention has to be found and fixed in two places. Violates the DRY rule in CLAUDE.md §2.

**Suggested fix:** move `spanOf` and `stubViewport` into a shared `tests/helpers/grid.ts` (or
extend an existing test-utils module) and import from both files. Note `tests/useIsBelowSm.test.tsx`
and `tests/useIsPhone.test.tsx` now carry a third and fourth copy of a richer `stubMatchMedia`, so
the consolidation is worth doing across all four at once.

### 553. [MEDIUM] portal/tests/PropertiesPageNarrowContent.test.tsx:1 — ~70 lines of mock setup duplicated from the phone suite

The first 80 lines are byte-identical to `PropertiesPageMobileSheet.test.tsx` apart from the
docblock and one import — the same eight `vi.mock` factories, the same fixtures, the same
`stubViewport` and `findRow` helpers. The two files test the same component through the same seams,
so any change to a mocked API forces two edits, and the pair will drift the first time only one is
updated.

**Suggested fix:** extract the fixtures and helpers to `tests/helpers/propertiesPageHarness.tsx` and
import from both. `vi.mock` factories are hoisted per-file and cannot move, so either keep those two
copies, or merge the squeezed-desktop describe into `PropertiesPageMobileSheet.test.tsx` and rename
the file for the wider subject. Merging is preferable — both describes are about the same stacked
layout, arrived at by different routes.

### 83. [LOW] Inconsistent ID extraction across settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx),
[portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx),
[portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
**Severity**: LOW (style)

The new tab components use the non-null assertion operator
(`editingDivision.id!`, `categoryToDelete!.id!`) when calling the API.
The sibling `RateCardsTab.tsx` instead uses `extractEntityId(rc)` from
`lib/entityId`, which handles the union shape from the API response
without requiring a non-null assertion. Pattern was preserved verbatim
during the 2026-04-26 #63 extraction — pre-existing, not introduced.

Fix: switch to `extractEntityId(...)` for consistency with `RateCardsTab`.
~6 call sites across the three files.

### 148. [LOW] Three near-identical settings tabs
**Files**:
- [portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
- [portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx)
- [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx)

**Severity**: LOW

~95% identical markup and state machinery. Each round of UI work
(icon buttons, Actions column width, Name column width) had to be
applied three times. Divergence risk grows.

Fix: extract a generic `<NameDescriptionResourceTab>` component
parameterised by `api`, singular/plural labels, and any tab-specific
extras.

> Note: the seventh portal item ("`NewEstimateWithActivityPage.tsx` is
> 1,990+ lines") duplicates existing finding [#137](code-review-followups-archive.md)
> and is tracked there.

### 189. [LOW] `estimate_update.py` could mirror `fuzzy_confirmation._envelope`
**File**: [platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py)
**Severity**: LOW (DRY / symmetry)

`fuzzy_confirmation.py` introduced a `_envelope(...)` helper during the
#95 split that deduplicates the standard 11-key result dict across 4
call sites. `estimate_update.py` still has three near-identical
envelope shapes:
- `_modify_items_refusal` refusal dict (~14 lines)
- `run_update_estimate` empty-result dict (~13 lines)
- `_persist_added_job_items` success dict (~14 lines)

These differ in `success`, `result`, `needs_clarification`, and
`error` but otherwise share the same key set. Extracting an
`_envelope` helper local to this file would shave ~20 total lines and
nudge `_persist_added_job_items` (49-line body) and `_modify_items_refusal`
(41-line body) closer to the 50-line ceiling measured incl. signature.

Why LOW, not MEDIUM: the envelope-builder pattern is also flagged as
the higher-leverage fix in [#94](code-review-followups-archive.md)
for `agents/material/service.py`. Worth considering whether to factor
a single shared `_envelope` into `routers/agent_helpers/responses.py`
that both modules can import — but that's #94-scope work, not a
standalone cleanup.

### 216. [LOW] Extract `<PlanSummaryBlock>` component
**File**: `portal/src/components/onboarding/CompletionStep.tsx:36-58`, `portal/src/components/settings/BillingTab.tsx`, `portal/src/components/billing/PlanPickerGrid.tsx`
**Severity**: LOW

Three places render `included_seats` / `included_estimates` summary blocks. Minor DRY concern — adding a fourth field to the Free-plan summary card would mean updating three spots.

Fix: optional refactor — extract `<PlanSummaryBlock plan={plan} variant="onboarding" | "billing-tab" | "card" />` if a fourth field gets added or another surface needs the block.

### 251. [LOW] Consolidate `ensure_*_price` helpers in `scripts/seed_stripe_products.py`
`ensure_flat_price`, `ensure_metered_overage_price`, and
`ensure_metered_token_overage_price` share ~70% of their logic
(lookup-key search, tier-drift comparator, archive-and-recreate flow).

Fix: refactor to a single `ensure_price(...)` driver that takes the
Price-create kwargs plus a per-shape `drift_check(existing_full)` callable.
Low risk, but defer until we add a fourth Price shape — premature otherwise.

### 292. [LOW] `RowActionsMenu` has two near-identical menu-item buttons
**Where:** `portal/src/components/common/RowActionsMenu.tsx` — the Move up and Move down `<button>` blocks differ only in icon, label, and onClick.

**Issue:** Minor duplication. Refactor only worthwhile if a fourth/fifth menu item lands.

**Fix:** Extract a small `<MenuItem icon={…} label={…} disabled={…} onClick={…} />` helper if the menu grows.

### 315. [LOW] Duplicate `normalizeEstimateStatus` definition (pre-existing)
**Where:** `portal/src/pages/EstimatesPage.tsx:33` vs `portal/src/lib/estimateStatus.ts`

**Issue:** The local `normalizeEstimateStatus` in `EstimatesPage.tsx` (still used by `getSortableValue`) is byte-identical to the exported one in `lib/estimateStatus.ts`. The new `estimateStatusFilter.ts` already imports the canonical version, so the page now has both in play. Pre-existing duplication — not introduced by this change.

**Fix:** Import `normalizeEstimateStatus` from `../lib/estimateStatus` and delete the local copy so there's a single definition.

### 367. [LOW] portal/src/components/settings/FinancialTab.tsx:44 — field descriptions duplicated from users_guide.md
The six tooltip description strings are copied from the platform glossary
(`platform/user_guides/users_guide.md` lines 718-725). Two sources of truth can drift — a guide
edit won't propagate to the UI. The frontend can't import the backend markdown, so this is a
conscious tradeoff, not a bug.
**Suggested fix:** No action needed now. If these multiply, consider a shared copy module or
surfacing them from an API. Note kept so a future guide edit remembers to update the UI strings too.

### 398. [LOW] portal — duplicated staff-session persistence block in App.tsx + LoginPage.tsx
Both `onIdTokenChanged` (App.tsx) and `handleLogin` (LoginPage.tsx) build the same staff `AuthUser` object and call `setCurrentUser` / session helpers inline. Extract a shared `persistStaffSession(authData)` helper (mirroring `resolvePostLoginRoute` in `src/lib/staffAuth.ts`) and wire both call sites through it.

### 463. [LOW] portal/src/pages/auth/LoginPage.tsx:330 — the two banner action blocks are duplicated markup
The `resendToken` and `linkExpired` blocks are near-identical (`div.mt-1.5` wrapping an
underlined action with the same utility classes) and are mutually exclusive by construction —
`handleSubmit` clears `linkExpired`, and `resendToken` is only ever set inside it. Two copies
will drift.

**Suggested fix:** render one action slot whose content is chosen by whichever state is set, or
extract a small `BannerAction` wrapper carrying the shared classes.

### 479. [LOW] portal/src/components/estimates/AddMaterialGapDialog.tsx:435, portal/src/pages/MaterialsPage.tsx:923 — unit-column width is now a magic literal in three places
The same conceptual column is sized `w-[240px]`, `w-[180px]`, and `w-[160px]` across three
tables, each tuned by hand to a different font size. Nothing ties them together, so the
next unit added to the catalog requires finding and re-deriving all three independently —
which is how the original 160px went stale.
**Suggested fix:** extract a shared constant (e.g. `UNIT_COLUMN_WIDTH_CLASS` in `src/lib/`
or alongside the other estimate constants) and reference it from all three headers so they
move together.

### 498. [LOW] portal — empty-patch behavior is inconsistent across the five edit surfaces
MaterialsPage, PeoplePage, and PropertyDialog skip the API call when the diff is empty;
ContactsPage and TaskDialog still send `{}` (a server round-trip that only bumps
`updated_at`). Both are safe; the inconsistency is the issue.
**Suggested fix:** pick one convention (skipping is better — no spurious `updated_at` bump for
a no-op save) and apply it to ContactsPage and TaskDialog.

### 525. [LOW] portal/src/components/estimates/ActivitiesTable.tsx:199 — the add-row button markup is duplicated across the twin tables
`MaterialsTable` and `ActivitiesTable` were already near-identical siblings; the blank-row
guard added ~14 more duplicated lines to each — the wrapping flex div, the conditional
"Finish the empty row" hint span, the `disabled` attribute, and the four `disabled:` utility
classes. The two copies differ only in the button label, so any future change to the disabled
treatment has to be made twice and can silently drift.

**Suggested fix:** extract an `AddRowButton` component (`label`, `disabled`, `disabledHint`,
`onClick`) into `src/components/estimates/` or `src/components/common/`, and render it from
both tables' headers.

### 744. [LOW] `_UNLINK_REDIRECT` duplicates `out_of_chat._UNLINK`
`platform/agents/conversation/delete_confirmation.py:59` — The same user-facing unlink redirect text lives in two modules and will drift. (review 2026-09-27 #74)

**Suggested fix:** Export one constant from out_of_chat.py and import it here.

### 750. [LOW] Private `_EMAIL_RE` imported across modules, and two email regexes disagree
`platform/agents/task/create.py:24` — create.py imports operations' private `_EMAIL_RE` (operations.py:45), which disagrees with the bounded one in list_filters.py:55. (review 2026-09-27 #80)

**Suggested fix:** Share one public `EMAIL_RE` and use `email_in()` everywhere.

### 767. [LOW] The task command lead is a third lead-word list, drifted from the shared one
`platform/agents/task/text_helpers.py:109` — `agents/estimate/lead_words.py` exists so the lead words are written once ("so the two can't drift apart"), but `_LEAD_FILLER` is a separate list. "perfect, mark it done", "one more thing, archive it" and "quick, archive it" return None, though the shared list has perfect / one more thing / quick. (review 2026-09-28 third round #6)

**Suggested fix:** Build `_LEAD_FILLER` from `lead_words.LEADS` (move the module to `agents/lead_words.py` if a task import from `agents/estimate` is unwanted), add task-only words there, and add the three cases to `test_a_polite_edit_still_counts`. Keep "I need to" out (user decision 2026-09-28).

### 803. [LOW] A third copy of the small-number words
`platform/agents/task/list_filters.py:175` — The "wrong answers that look right" batch (#717/#718/#724) added `_SMALL_COUNTS` (list_filters.py:175, one…ten) and `_COUNT_WORDS` (estimate/crud_helpers.py:188, one…ten) beside the existing `_SMALL_NUMBERS` (task/text_helpers.py:992, a/an/one…three). Three maps for one idea drift apart: "in four days" works in a task list but not in a task edit, and the next person to add "eleven" adds it to one of three. LOW: no wrong answer today — each map covers what its parser accepts. (review 2026-10-02 round 3 #1)

**Suggested fix:** Put one `SMALL_NUMBER_WORDS = {"one": 1, … "ten": 10}` in `agents/text_utils.py`, and have all three import it (text_helpers keeps its "a"/"an" → 1 as `{**SMALL_NUMBER_WORDS, "a": 1, "an": 1}` and widens `_IN_N_RE` to the shared words). Rerun test_task_list_filters.py, test_estimate_list_sort_words.py and the due-date tests in test_maple_task_operations.py.

### 816. [LOW] `PropertyAgent._find_properties_by_name_or_address` is a second copy of the property finder, still loading every property
`platform/agents/property/service.py:534` — The agent's twin of `cross_resource.find_properties_by_name_or_address` loads every property document through `_list_properties_via_api` to match a name or address, and serves the property agent's own get/update/delete lookups (:926, :2435). #812 (resolved 2026-10-04) changed only the shared finder — a projected read with the matches reloaded — so the two copies of the predicate can now drift, and the agent's copy keeps the full load. LOW: pre-existing and correct. Related: #815 (the same agents' id lookups). (review 2026-10-04, slow-queries batch #2)

**Suggested fix:** Make the agent's method delegate to `cross_resource.find_properties_by_name_or_address` (same predicate, projected read, matches reloaded), moving its tests from stubbing `_list_properties_via_api` to stubbing the shared finder. Could be done together with #815.

## Accessibility

Missing accessible names, keyboard traps, ARIA relationships and contrast.
Several of these are controls with no accessible name at all, not polish.

### 43. [MEDIUM] Trash-icon-only buttons have no accessible name
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — Preview version-row delete (~line 1017) and work-item row delete (~line 1147)
**Severity**: MEDIUM (a11y)

Both buttons render only `<Trash2 />` inside. Each is wrapped in a
`<Tooltip content="Delete this version">` (or similar), but tooltip
content is typically not announced by screen readers — the button has
no accessible name. Same pattern appears on other icon-only trash
buttons across the portal (EquipmentsPage, ContactsPage, PropertiesPage,
RateCardsTab, etc.) — this is a portal-wide gap, not specific to this
change.

Fix: add `aria-label={`Delete version ${v.version}`}` (or equivalent
row-specific label) on every icon-only trash button. Sweep-style PR;
grep for `<Trash2 ` and audit each site.

**Absorbed:** #258, #191 — duplicate findings on the same a11y gap (icon-only / decorative-icon accessible names) from later review passes. See `## Closed` for their original bodies.

### 106. [MEDIUM] `autoFocus` on dialog open may interrupt screen-reader announcements
File: `portal/src/components/estimates/UseTemplateDialog.tsx:84`
**Severity**: MEDIUM

`autoFocus` on the search input pulls focus immediately when the dialog
opens. On some assistive tech this races with the modal's open
announcement, so the user hears a partial label. Same pattern is used in
several other dialogs (e.g. `TemplateDialog.tsx`), so it's a codebase-wide
concern, not specific to this dialog.

The standard fix is to focus the modal container (or first heading) on
open and let the user Tab into the search field. That requires changes
inside `components/common/Modal.tsx` and ripples to every dialog. Not
worth a one-dialog fix — defer until an a11y pass that addresses Modal
focus management as a single change.

Fix: address as part of a future Modal a11y refactor; do not patch
per-dialog.

### 135. [MEDIUM] Description "button" wraps multi-line content
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (accessibility)

The read-only description div has `role="button"` and `tabIndex={0}`,
so screen readers announce the entire description as the button's
accessible name. Fine for short text, awkward for long ones.

Fix: add `aria-label="Edit description"` so the announced label is
concise; the visible text remains content.

### 136. [MEDIUM] Docs menu items missing `role="menuitem"`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (accessibility)

The status dropdown items use `role="menuitem"`; the docs dropdown's
`<a>` / `<button>` items inside `role="menu"` do not. Inconsistent
ARIA.

Fix: add `role="menuitem"` to each item inside the docs `<li>`.

### 270. [MEDIUM] `OverageWarningDialog` `aria-labelledby` points at a `<span>` inside the heading
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/components/billing/OverageWarningDialog.tsx:60-62` —
`DialogContent ariaLabelledBy="overage-warning-title"` resolves to an
`id` placed on a `<span>` inside the `<h2>` rendered by `DialogTitle`.
Screen readers still find the label text, but the convention is for
`aria-labelledby` to point at the heading element itself, not a child
of it.

Fix: either drop the inner `<span id>` and let `DialogContent` derive a
default label, or extend `DialogTitle` to accept an `id` prop that lands
on the underlying `<h2>` (preferred — minor `ui/dialog.tsx` change).

### 338. [MEDIUM] `ActionsMenu` has `role="menu"` but no arrow-key navigation
`portal/src/components/common/ActionsMenu.tsx` has correct roles,
`aria-expanded`, and Escape handling, but no ArrowUp/ArrowDown focus movement,
which the ARIA menu pattern implies. Inherited verbatim from `RowActionsMenu`
(not a regression), but `ActionsMenu` is now the shared primitive, so the gap
propagates to every consumer. Fix: one `onKeyDown` handler on the menu div that
cycles focus across `menuitem` buttons.

### 462. [MEDIUM] portal/src/pages/auth/LoginPage.tsx:330 — resend button unmounts from a live region, dropping focus
The Resend button renders inside `AuthBanner` (`role="status"` or `role="alert"`). On a
successful resend — and on the 409 already-verified path — `resendToken` is cleared, so the
button the user just activated unmounts while the banner swaps message. Focus falls to
`<body>`, so keyboard and screen-reader users lose their place immediately after acting. The
expired-link `<Link>` does not share this problem: activating it navigates away.

**Suggested fix:** move focus deliberately once the resend resolves — to the email input, or to
the banner container given `tabIndex={-1}` and `.focus()`, which also anchors the announcement
of the new message.

### 539. [MEDIUM] portal/src/components/estimates/CollapsedLineHeader.tsx:39 — `aria-expanded` with no `aria-controls`

The collapsed-row toggle announces its expanded state but never identifies what it expands. The
revealed fields are sibling `<td>`s, not descendants, so a screen-reader user hears "expanded" with
no way to navigate to the content that appeared. Pre-existing, but this change widened its reach
from 2 tables to 4 and made the bar the permanent home of the row menu and the line amount, so the
bar is now the primary control for each line.

**Suggested fix:** give the detail cells a container id per row (e.g. `gap-${gap.id}-details`) and
add the matching `aria-controls` to the toggle; needs a small prop addition to CollapsedLineHeader.
Deferred because it touches all four call sites and wants its own a11y-focused pass rather than
riding along with a layout change.

### 552. [MEDIUM] portal/src/components/notes/NoteBody.tsx:90 — the note text is unreachable by keyboard

The body is an `overflow-y-auto` region with no `tabIndex` and no role, so it never receives focus.
In Chrome and Safari a non-focusable scroll container cannot be scrolled with the arrow keys or
Page Down, which means a keyboard-only or screen-reader user can read the first ~8 rows of a note
and has no way to reach the rest. The chevrons that announce the hidden text are `aria-hidden`, so
assistive tech is not told it exists either. WCAG 2.1.1.

Deferred: the fix needs a call on tab-stop density. Every overflowing note becoming a tab stop is
a real cost on a feed of twenty, and the alternative (a single "expand" control per card) is the
affordance that was just deliberately removed.

**Suggested fix:** when the body actually overflows, make it a focusable labelled region —
`tabIndex={0} role="region" aria-label={`Note by ${author}`}` on the scroller. Gate it on the
overflow state already tracked (`edges.above || edges.below`, plus a `hasOverflow` flag) so short
notes do not each add a tab stop.

### 110. [LOW] `FeedbackPanel` error message has no live-region announcement
**File**: [portal/src/components/common/FeedbackPanel.tsx:169](../../portal/src/components/common/FeedbackPanel.tsx)
**Severity**: LOW (accessibility)

The submission-error div is a plain `<div className="text-xs text-red-600">{error}</div>`.
Screen readers don't announce it when it appears, so a visually impaired
user gets no audible signal that submission failed — they have to walk the
DOM to find out why nothing happened.

Fix: add `role="alert"` (or `aria-live="polite"`) to the error div. The
same applies to `ChangeLogPanel.tsx:166`, which uses the identical
pattern.

### 173. [LOW] `<input>` in `AdjustTotalDialog` uses `aria-label`, not a real `<label>`
**Severity**: LOW
`AdjustTotalDialog.tsx:65–73` — the visible "Adjust Amount" text comes
from the modal title (`<h3>`), not from a `<label htmlFor=…>` on the
input. The input has `aria-label="Adjust Amount"`, so screen readers do
announce the field correctly, but there's no clickable visual association
between the heading and the input.

Fix: render an explicit `<label htmlFor="adjust-amount-input">Adjust
Amount</label>` inside the modal body and drop the `aria-label`. Keep
the modal's `<h3>` title as-is for the dialog heading. Minor a11y polish.

### 174. [LOW] Reset button doesn't refocus the input
**Severity**: LOW
`AdjustTotalDialog.tsx:77` — clicking Reset replaces the input value but
leaves keyboard focus on the Reset button. Users frequently want to
glance at or tweak the field before clicking Set.

Fix: hold a `useRef` on the input and call `inputRef.current?.focus()`
inside the Reset handler. Tiny UX polish.

### 177. [LOW] Grand Total contrast borderline at small text sizes
**Severity**: LOW
`portal/src/pages/NewEstimateWithActivityPage.tsx:1273` — the new
`bg-total-bg` (`#38A776`) with `text-white` measures ~3.03:1. Passes WCAG
AA only via the large-bold exemption (text is `text-lg font-bold`).
Acceptable here, but if the same token is reused for normal-weight or
smaller text it will fail AA.

Fix: if reuse is needed, define a darker variant (e.g.
`--total-bg-strong: #2E8A60`) for normal-weight text. Or document on the
token in `theme.css` that it's only safe for large-bold copy.

### 192. [LOW] Plan-name `<h3>` visually outsizes the dialog `<h2>`
**File**: [portal/src/components/billing/PlanPickerGrid.tsx](../../portal/src/components/billing/PlanPickerGrid.tsx) line 219
**Severity**: LOW (visual hierarchy)

Plan names are now `text-3xl uppercase` while the parent dialog
heading "Choose Your Plan" is `text-2xl` (in both
`PlanStep.tsx:38` and `ManagePlanModal.tsx:60`). Semantic hierarchy is
still correct (h2 > h3), but visually the cards now hero over the
section title.

Fix (pick one): bump dialog `<h2>` to `text-3xl`, drop card `<h3>` to
`text-2xl`, or accept as-is if the design intentionally hero's the
plan name.

### 264. [LOW] Description label not programmatically associated with the editor
`portal/src/pages/NewEstimateWithActivityPage.tsx:1036` and
`portal/src/components/estimates/WorkItemInlineContent.tsx:371` — the
"Description" label renders as a plain `<span>` / `<h3>` with no `id`
referenced by the editor's accessible name. Screen readers don't
announce "Description" when the contenteditable receives focus.
Matches the pre-mdxeditor textarea (also unlabeled), so it's a
continuation, not a regression. Fix: add `id="..."` to the heading
and pass `aria-labelledby="..."` through `MarkdownDescriptionEditor`
to the underlying `MDXEditor` (props pass-through prop, or accept it
on the wrapper).

### 288. [LOW] Spot-check rotated chart labels with a screen reader

`portal/src/components/dashboard/PipelineStatusChart.tsx` — the bar chart
already wraps the data inside `role="img" aria-label={ariaLabel}`, so the
rotated visual labels are decorative for assistive tech. Worth a one-time
VoiceOver pass to confirm no regression.

Fix: manual check, no code change unless something reads wrong.

### 362. [LOW] portal/src/components/onboarding/CompletionStep.tsx:16 — decorative sparkle icon lacks aria-hidden
The `<Sparkles>` icon is purely decorative but has no `aria-hidden="true"`. Lucide renders a
bare `<svg>` with no accessible name, so screen readers already skip it (hence LOW), and it
matches the existing inline-icon pattern across the codebase.
**Suggested fix:** Optionally add `aria-hidden="true"` for explicitness. Skip if you'd rather
stay consistent with the rest of the codebase, which omits it on decorative icons.

### 368. [LOW] portal/src/components/ui/InfoTooltip.tsx:92 — info button tap target is 16x16px
The trigger is `h-4 w-4` (16px), below the ~44px recommended touch target. Fine for a secondary
info affordance, but slightly fiddly on touch.
**Suggested fix:** Optional — add padding (e.g. `p-1` with `-m-1` to preserve visual size) to
enlarge the hit area without changing the icon's appearance.

### 376. [LOW] portal/src/pages/SettingsPage.tsx:1208 — tablist orientation / keyboard semantics
This change removed `aria-orientation="vertical"`; on the desktop vertical layout that now defaults to `horizontal` (minor SR regression), and it cannot be statically correct for both responsive layouts. Separately and pre-existing (unchanged by this diff): the roving `tabIndex={isActive ? 0 : -1}` follows the ARIA tabs pattern but there is no Arrow-key keydown handler, so keyboard users can't move between tabs — only the active tab is reachable via Tab.
**Suggested fix:** If full correctness is wanted, drive `aria-orientation` from a `matchMedia('(min-width:768px)')` state and add an ArrowLeft/Right (and Up/Down) handler that moves focus + selection across `tabs`. Low practical impact today (orientation has no keyboard effect without arrow handling), so acceptable to defer.

### 414. [LOW] portal/src/components/Layout/PortalLayout.tsx:509 — mobile drawer close button has no accessible name (pre-existing)
The drawer's X close button renders only an aria-hidden lucide icon, so screen readers announce an unnamed button. Pre-existing (not introduced by the swipe change), but adjacent to the reviewed code; the sibling collapse/expand buttons do have aria-labels.
**Suggested fix:** Add `aria-label="Close menu"` to the button.

### 431. [LOW] portal/src/components/properties/EstimatesPicker.tsx:83 — the locked-row reason is conveyed only by a title attribute
Locked rows set `title={LOCKED_HINT}` on the `<label>`, but the checkbox is
`disabled` and therefore not focusable, so keyboard and screen-reader users may
never surface the tooltip and just see an unexplained un-toggleable row. Partly
mitigated: the same sentence was appended to the always-visible helper text
below the list.
**Suggested fix:** Render the reason as visible per-row text, or
`aria-describedby` pointing at the helper paragraph, rather than relying on
`title`. Same family as the icon-only-button a11y sweep in
[#43](#43-medium-trash-icon-only-buttons-have-no-accessible-name).

### 457. [LOW] website/index.html:1248 — `title` and `aria-label` carry different text on each icon link
Each anchor has `aria-label="3Maples on LinkedIn"` and `title="LinkedIn"`. `aria-label` wins
as the accessible name; some screen readers additionally announce `title` as the description,
producing "3Maples on LinkedIn, LinkedIn". Harmless but redundant. Applies to all five pages.

**Suggested fix:** keep `title` for the sighted-user tooltip and accept the duplication, or
drop `title` and rely on the accessible name alone.

### 458. [LOW] website/index.html:701 — icon links rely on the UA default focus ring
The new anchors style `:hover` but not `:focus-visible`. There is no global outline reset, so
keyboard focus is still visible via the browser default — not a WCAG 2.4.7 failure. It is
however inconsistent with `.m3s-dot:focus-visible` (index.html:299), which defines an explicit
2px accent ring with offset. Applies to all five pages.

**Suggested fix:** add `.foot-col .foot-social a:focus-visible { outline: 2px solid
var(--social-accent); outline-offset: 2px; }` to match the established treatment.

### 459. [LOW] website/index.html:700 — 34px touch targets
The icon tiles are 34x34 CSS px with an 8px gap. This clears WCAG 2.2 SC 2.5.8 Target Size
(Minimum, AA = 24px) but sits under the 44px commonly recommended for comfortable thumb use,
and these are the only touch targets in the mobile footer.

**Suggested fix:** optional. Bumping to 40-44px would need the `repeat(3, 34px)` track and the
`svg` sizing adjusted together; verify the 2-column mobile footer still fits at 320px.

### 469. [LOW] portal/src/components/common/SearchableSelect.tsx — no keyboard navigation
The component gained combobox/listbox/option roles and Escape-to-close in this change, but
still has no arrow-key navigation or type-ahead focus movement: a keyboard user can open it
and tab through the option buttons, which works but does not match the combobox pattern
screen readers announce.

**Suggested fix:** add ArrowUp/ArrowDown/Home/End over the filtered rows with
`aria-activedescendant`. Deferred because it touches all six consumers' focus behaviour and
was out of scope for the Tasks work.

### 476. [LOW] portal/src/components/common/StatusFilterDropdown.tsx:196 — trigger has no accessible name beyond its summary
The button's accessible name is just the current summary ("8 statuses", "No statuses"),
which does not say what it filters. `aria-haspopup="true"` also implies a menu rather
than the checkbox group actually rendered. Pre-existing, but the control now appears in
more places.
**Suggested fix:** give the trigger an `aria-label` such as "Filter by status, 8
selected", and set `aria-haspopup` to match the rendered role.

### 530. [LOW] portal/src/pages/TasksPage.tsx:104 — `md:order-first` makes DOM order disagree with visual order
The task card's thumbnail now renders after the text block and is pulled back to the left with
`md:order-first`. Above 768px the visual sequence is photo→text while the DOM sequence is
text→photo, so a screen reader hears the task title and metadata before the photo it sits beside
(WCAG 1.3.2 Meaningful Sequence). Impact is small: the element is an `<img>` with descriptive alt
text, or an aria-hidden placeholder, and nothing in the card is focusable except the actions menu,
so tab order is unchanged.

**Suggested fix:** acceptable as-is given the low impact, and reordering the DOM per breakpoint
would mean duplicating the subtree — worse. If it is worth cleaning up, drop `md:order-first` and
instead keep the thumbnail first in the DOM with `order-last md:order-none`, so the visual reorder
happens on the phone (where the image is genuinely secondary) rather than on desktop.

### 601. [LOW] Doc-image loading placeholder's aria-label is ignored
`portal/src/components/estimates/DocImagePicker.tsx:18` — A `div` with `aria-label` and no role is not announced, so screen readers get nothing while a kept image loads or after it fails. The remove badge still names the file, hence LOW.

**Suggested fix:** Add `role="img"` to the placeholder.

### 602. [LOW] Keyboard focus is lost after deleting a doc version
`portal/src/components/estimates/DocVersionList.tsx:43` — The delete-confirm modal returns focus to the trash button, whose row no longer exists, so focus lands on `<body>`.

**Suggested fix:** When `versions` shrinks, move focus to the next row's trash button or to the "Generated versions" heading (`tabIndex={-1}`).

### 757. [LOW] The `role="status"` live region is added to the page already containing its text
`portal/src/components/Layout/AiPanel.tsx:432` — `{openQuestion && <div role="status">…}` mounts the region with its text in one render; NVDA/JAWS generally don't announce a region that appears already filled. (review 2026-09-27 #87)

**Suggested fix:** Always render an empty `<div role="status" aria-live="polite">` and toggle only its contents.

## Responsive and breakpoint drift

Phone/tablet layout issues, plus the `sm` (640px) vs documented `md` (768px)
breakpoint inconsistency — now at four call sites and best fixed in one pass.

### 285. [MEDIUM] Proliferating `@[Xrem]` container-query thresholds in DashboardPage

`portal/src/pages/DashboardPage.tsx` — the responsive pass introduced
breakpoints at 14rem, 18rem, 20rem, 24rem, 26rem, 32rem, and 48rem with no
shared rationale. Future tuning means hunting through the file. Surfaced
during `/code-review` on the responsive-dashboard change; not a regression,
just a maintainability watch-item.

Fix: when the next container-query pass lands, introduce a tiny
`dashboardBreakpoints.ts` (or a one-line comment at each call site
documenting *why* that threshold — icon-fit, table-row, etc.). Don't refactor
purely for this — wait for the next responsive change in this area.

### 286. [MEDIUM] `overflow-x-hidden` on the root PortalLayout flex container

`portal/src/components/Layout/PortalLayout.tsx:262` — added as a belt-and-
braces guard against any future child blowing out the viewport on mobile.
Acceptable today (every wide table in the portal already uses its own
`overflow-x-auto` scroll container), but worth noting so a contributor adding
e.g. a fluid horizontal-scroll admin view doesn't fight the parent.

Fix: no action. Drop a comment at the class site if it ever causes
confusion.

### 416. [MEDIUM] portal/src/components/Layout/PortalLayout.tsx:345 — setState per touchmove re-renders the whole layout tree
`onSwipeMove` calls `setDrawerDragPx` on every touchmove (~60Hz), re-rendering
all of `PortalLayout` including the routed page (`Outlet`), desktop sidebar,
and AiPanel on each drag frame. On low-end phones with heavy pages (dashboard
charts, task board) the drag can jank — the exact scenario the reveal
animation is meant to smooth out.
**Suggested fix:** Only if jank is observed on real devices: move drag progress
out of React state — write transform/opacity directly to drawer/backdrop refs
inside `onSwipeMove` (optionally rAF-throttled) and keep state only for the
settled open/closed transitions.

### 548. [MEDIUM] portal/src/lib/onboardingSteps.ts:79 — the desktop progress row may now wrap

The two longest labels in the set replaced two of the shortest: `percentages` went "Defaults" →
"Percentages" and `plan` went "Plan" → "Choose Plan". The desktop `StepIndicator` renders all eight
labels in one `flex` row with seven 24px connector rules and `gap-2`, inside a `max-w-3xl` (768px)
container that itself sits inside `px-4`. Estimated to land within a few pixels of the available
736px. It will not overflow horizontally — the label `<span>`s have no `whitespace-nowrap`, so they
wrap — but one or two labels going to two lines would make the dot row ragged. jsdom does no layout,
so no test can catch this, and `/onboarding` is behind `firebaseAuth.currentUser` so it was not
visually verified.

**Suggested fix:** needs a look at ≥1024px width first. If it wraps: either shorten `plan` back
toward "Plan" in `STEP_LABELS` (the card title stays "Choose Your Plan" — they are already
independent), or widen `containerWidthClass` in `OnboardingPage.tsx` from `max-w-3xl` to `max-w-4xl`
for the non-plan steps.

### 147. [LOW] `MaterialsPage` mobile card popup-clip fix is scoped
**File**: [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx)

**Severity**: LOW

The previous `overflow-hidden` clip was fixed by removing
`overflow-hidden` from the card and adding `rounded-b-xl
overflow-hidden` to the expanded sizes section. This works for the
current popup but if a future popup is added inside the expanded sizes
section it'll be clipped again.

Fix: if/when that case appears, switch popups to render via React
portal so they aren't subject to ancestor clipping.

### 287. [LOW] `min-h-[60px]` on vertical status labels may clip long words

`portal/src/components/dashboard/PipelineStatusChart.tsx:140` — `Completed`
rotated to `writing-mode: vertical-rl` is ~54-58px tall, so 60px is tight.
A future status name like `Cancelled` (~60px) could touch the limit.

Fix: bump to `min-h-[72px]`, or drop the `min-h` entirely and rely on
`flex-row items-start` to size itself naturally. Defer until a new status
label is added.

### 378. [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1211-1279 — narrow two-row layout relies on inline-block flow; needs an eyes-on check
The "Description row 1, meta row 2" result depends on the Description inline-block filling row 1 so the meta cells wrap below. When a description is very short, the meta cells may sit beside it on row 1 (still readable, just not strictly two rows). No correctness impact; purely visual.
**Suggested fix:** Verify across short/long descriptions at a narrow container width. If strict two-row behavior is required, force a break (e.g. `basis-full` on the Description cell under a flex `tr`, or a wrapper element for the meta trio).

### 400. [LOW] portal/src/components/Layout/OpsLayout.tsx — mobile nav not addressed
The ops layout's navigation hasn't been evaluated for small-viewport/mobile use; revisit if ops staff need mobile access.

### 412. [LOW] portal/src/components/Layout/useSwipeGesture.ts:72 — no touchcancel handling
A gesture interrupted by the system (incoming call, browser takeover) fires touchcancel, not touchend, leaving startPoint set. Harmless today because every new sequence begins with touchstart (which recomputes it), but it is one browser quirk away from a phantom swipe.
**Suggested fix:** Return an `onTouchCancel` handler that clears startPoint, and spread it with the others.

### 413. [LOW] portal/src/index.css:39 — overscroll-behavior-x: none is global, not mobile-only
Besides suppressing Chrome-on-Android overscroll navigation (the intent), this also disables two-finger trackpad back/forward swipe on desktop Chrome/Edge app-wide. Usually desirable in an SPA (prevents accidental back-nav losing form state), but it should be a deliberate UX decision, not a side effect.
**Suggested fix:** Keep if intended (recommended); otherwise scope it inside an `@media (pointer: coarse)` block.

### 521. [LOW] portal/src/components/common/EstimatesTable.tsx:279 — Duplicate is now unreachable on a phone
Removing `RowActionMenu` from the mobile card removed the only mobile entry point to
Duplicate (the menu's sole item). A phone user who wants to copy an estimate has no path
to it — the estimates list is the only surface that offers it. This was an explicit product
request, so it is recorded as an accepted trade-off rather than a defect.

**Suggested fix:** none if the trade-off stands. If mobile duplication should stay reachable,
the cheapest option is a Duplicate button inside the estimate editor (where there is room for
a label) rather than restoring the dot-menu to the card.

### 528. [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1659 — a fourth site collapses a label at `sm` (640px) while the documented phone breakpoint is `md` (768px)
**Absorbs #524** (2026-09-20 consolidation): the `ContactsPicker`-only entry
logged the same day, which this one already superseded in its own text.

The `sm:hidden` / `hidden sm:inline` pair on the checklist's Create PDF button switches at 640px,
but `src/lib/breakpoints.ts` documents `PHONE_BREAKPOINT_PX = 768` as the width where the portal
changes shape. This is now the fourth such site — `TasksPage.tsx`, `TaskDialog.tsx` and
`ContactsPicker.tsx` are the others — so it is consistent with practice but not with the
documented constant. No visible defect in the 640-768px band; the rows have room there.

**Suggested fix:** leave as-is for consistency, or switch all four to `md:` in one deliberate pass.
Do not change a single site — a lone `md:` would be a third convention. This supersedes the
`ContactsPicker`-only entry logged earlier the same day: treat the four together whenever this is
picked up.

### 529. [LOW] portal/src/lib/viewport.ts:57 — MediaQueryList.addEventListener with no legacy fallback
`query.addEventListener("change", ...)` is guarded only by `typeof window.matchMedia ===
"function"`, not by whether the returned MediaQueryList supports the modern listener API. On a
host that only implements the deprecated `addListener` the call throws during mount, and because
`useIsPhone` now runs in TaskDialog, TasksPage, PropertiesPage and NewEstimateWithActivityPage,
that is a hard crash of those screens rather than a degraded layout. LOW rather than MEDIUM
because the modern API has been in Safari since 14 (2020) and every current target supports it —
the realistic victim is a future test that stubs matchMedia minimally and gets a confusing
TypeError.

**Suggested fix:** feature-detect before subscribing: use `addEventListener` /
`removeEventListener` when present and fall back to `addListener` / `removeListener` otherwise,
or wrap the subscribe/unsubscribe pair in a small helper so both call sites stay in step.

### 544. [LOW] portal/src/components/estimates/InventoryGapsPanel.tsx:121 — two matchMedia subscriptions per panel

`MaterialGapsTable` and `RoleGapsTable` each call `useIsBelowSm()`, so one panel registers two
listeners for the same query and re-renders both subtrees on every resize across 640px. Harmless at
this scale; noted only because the two values must never disagree.

**Suggested fix:** call `useIsBelowSm()` once in `InventoryGapsPanel` and pass `collapsible` down as
a prop. This requires moving the call above the `return null` early exit to satisfy the Rules of
Hooks. Best folded into the `MaterialGapRow` / `RoleGapRow` extraction above, which already reshapes
these props.

## LLM prompt hygiene and injection surface

Company-authored text reaching agent prompts unsanitized, and prompts that are
accumulating routing rules past what they can reliably carry.

### 15. [MEDIUM] Split Example block may anchor LLM back to terse descriptions
**File**: `prompts/estimate_generation.py`, ~lines 99-109
**Severity**: MEDIUM (prompt quality)

Rule 4d now requires 1-2 sentence (~15-40 word) descriptions with materials,
sizes, and method. The Split Example block still shows short labels like
`Paver patio installation`, `Low-voltage landscape lighting installation`,
`Lawn refresh and grading`. LLMs latch onto examples as implicit targets, so
these short labels may be undermining rule 4d's guidance.

Fix: rewrite each Split Example entry to the richer 4d shape, e.g.
`Paver patio installation — 400 sq ft porcelain pavers on compacted base
with edge restraints and polymeric sand joints`. Low effort, likely
meaningful impact on what Maple actually emits.

### 452. [MEDIUM] platform/prompts/estimate_generation.py:82 — an over-long division description is silently dropped, not truncated
`_MAX_DIVISION_DESCRIPTION_LEN = 300`; `_safe_prompt_text` returns `""` above
that, so the coverage text a user wrote vanishes from the prompt entirely and
the division either inherits the seeded description (if it kept a seeded name)
or renders as a bare label. Nothing is logged and the Settings → Divisions form
gives no hint that the field is capped. The longest seeded description is 249
characters, so a user elaborating on one crosses the cap easily — and the
symptom is invisible: classification just quietly gets worse.

**Suggested fix:** truncate at the cap instead of dropping
(`text[:_MAX_DIVISION_DESCRIPTION_LEN]`), or log at WARNING when a description
is rejected for length. Consider surfacing the limit as a `maxLength` on the
description input in `portal/src/components/settings/DivisionsTab.tsx`.

### 17. [LOW] Architect prompt rule 5 still mentions "quantities" ambiguously
**File**: `prompts/estimate_architect.py`, rule 5
**Severity**: LOW (prompt quality)

Rule 5 now says "DO NOT include prices, labour rates, or inventory IDs/SKUs.
Sizes and quantities … ARE allowed." A stricter LLM may read the word
"quantities" as still-discouraged overall, because this rule used to ban all
quantities.

Fix: tighten to "DO NOT include prices, labour rates, inventory IDs, or
**purchase quantities** (how many to buy). Scope-describing sizes,
dimensions, coverage area, linear feet, and spacing ARE allowed."

### 385. [LOW] platform/agents/calculator/service.py:88 + open_math.py:43 — classifier + reasoner prompts still growing
Both prompts gained another rule (reverse + now labor-time). Still clear, but the trend warrants a periodic clarity/token pass.
**Suggested fix:** Periodically run /agent-prompt-review on the extraction + reasoning prompts.

**Update 2026-09-27:** #382 (the extraction prompt at `agents/calculator/service.py:88` accumulating routing rules) was merged into this entry — same file, same watch-point, same periodic /agent-prompt-review.

### 621. [LOW] `client_context.current_path` only has a length limit and reaches the classifier prompt unfenced
`platform/routers/agent_helpers/client_context.py:52` — It is saved and injected unfenced into the orchestrator LLM context ("Current page: …", orchestrator/service.py:1176). The client can only affect its own session.

**Suggested fix:** Validate it against a URL-path pattern such as `^/[\w\-/]*$`. Also add `source` and `current_path` to `TRANSIENT_KEYS` (`routers/agent_helpers/finalize_result.py`), so they are not saved with the conversation as stale state (review 2026-09-25 fifth pass #26, a duplicate of this entry).

### 898. [MEDIUM] Prompt entanglement: "More readings" restates rules from other sections
`platform/prompts/maple_planner.py:129` — The new section repeats rules that live elsewhere: acknowledge, help, redo_last/refine_last, edit targeting, links, empty creates and focus. The next edit to one copy will leave the other stale. No injection issue: the text is static and the fences are unchanged. (review 2026-10-11 #78, deferred)

**Suggested fix:** Fold each bullet into its home section and delete the duplicates. This owes a parity run (#846).

### 899. [MEDIUM] "while a work item is in play" is undefined
`platform/prompts/maple_planner.py:131` — Line 111 says a catalog price is settable (update_material); line 131 sends "set the price of pavers to $4.25" to the estimate line when a work item is "in play". A user with an estimate open who means the catalog price gets the line changed. (review 2026-10-11 #79, deferred)

**Suggested fix:** Define it: "a work item in focus in the state, or named in the message". Add one contrasting catalog example, and cover both in the parity run.

## Platform — Maple agents

### 325. [LOW] `sacá …todos` can false-positive the fail-open bulk-delete net
`_BULK_DELETE_PATTERNS` in `agents/text_utils.py` now matches `saca/sacá`
(remove/take-out) + an all/every quantifier, so a phrasing like "sacá una foto
de todos" (take a photo of everyone) would trip the bulk-delete refusal. Only
reachable on the rare translation-fail-open path (the happy path translates to
English first), and the guard is conservative (quantifier required), so impact
is minimal. Drop `saca/sacá` if real-world noise appears, or tighten to require
a record-noun nearby.

> Not logged (duplicate): the `orchestrate_agent_endpoint` / `routers/agents.py`
> God-handler + file-size concern is already tracked by #238, #257, and the #4
> file-size cluster. This change added ~20 lines to that pre-existing handler.

**Update 2026-09-27:** inbound translation now fails **closed** (`detect_and_translate_to_english` raises and the canned message is returned), so this is no longer a fail-open path. Untranslated Spanish reaches the guard only on a **prefilter miss** — `prefilter_language` (`services/translation.py:269`) judging the message English. The pattern is `agents/text_utils.py:241, :247`.

### 565. [MEDIUM] The reuse removal's cost to estimate generation is unmeasured

`platform/agents/estimate/llm_pipeline.py:595` — `_step2_and_3_for_scope` no
longer returns early on a >= 0.85 vector match, so scopes that used to skip
step 3 entirely now make a web-search research call. A multi-scope estimate
that previously reused three items makes three extra researcher calls, and
prices that were copied verbatim from a past job are now re-researched.

That is the intended behaviour change (#557 §3), not a defect. What is missing
is the check the plan itself asked for: a side-by-side on a few real scopes
before this reaches production. Nothing in the test suite can stand in for it —
it needs live generation against a real company's corpus.

**Suggested fix:** run the side-by-side on a handful of representative scopes
and record what changed: whether re-researched prices land near the ones that
used to be copied, and what the added latency per scope actually is.

**Ruled out — do not add a config flag to restore the short-circuit.** It would
switch between "infer from history" and "copy a past price verbatim", which
re-introduces the stale-price path #557 removed, and a flag like that gets
turned on the first time generation feels slow. If the side-by-side shows the
research path is worse, that is a reason to improve the prompt context, not to
bring back copying.

### 746. [LOW] Linking rewrites the whole `contacts` array
`platform/agents/conversation/record_links.py:141` — `fresh.set({"contacts": [*fresh.contacts, id]})` reads, modifies and writes, so a concurrent link (another turn or a portal edit) is overwritten. The docstring (13-14) says the write goes through the property agent; it doesn't. (review 2026-09-27 #76)

**Suggested fix:** Use `{"$addToSet": {"contacts": contact.id}}` with an `updated_at` `$set`, and correct the docstring.

### 818. [LOW] The template router saves the estimate before its work item exists, so every later failure needs cleanup
`platform/agents/estimate/crud_handlers.py:768` — `_create_estimate_from_template` inserts an empty Draft, and the callers then build, scale and price the template's work item and save it with a second write. Any failure between the two writes leaves an empty estimate behind. The template router (`routers/agent_helpers/template_estimate.py::_finalize_template_estimate`) now copes: it deletes the estimate (`_discard_unfinished`), releases the quota slot, and skips the processor's audit (`audit=False`) so the record and the reply agree. That took four review rounds of #318 to get right (2026-10-05), and Maple's own template path (`crud_handlers.py:925`) has the same insert-then-fill shape without that cleanup. LOW: the router path is correct today; the agent path's exposure is the same rare failure window.

**Suggested fix:** Build and price the work item first, then insert the estimate once with its job items and total, and audit that single insert. A failure before the insert leaves nothing, which removes `_discard_unfinished`, the second write and the `audit` flag. It touches both callers, so do it as its own change with the template routing and estimate agent tests.

### 821. [MEDIUM] Shadow planner calls take global LLM slots with no cap of their own — WON'T FIX for the window
`platform/services/maple_shadow.py:246` — The planner runs under a tenant-less context, so `services/llm/concurrency.llm_slot` gives it no per-company semaphore. It takes only a global slot (`OPENAI_MAX_CONCURRENCY`, 24). With shadow on for every company, each Maple turn adds a 3–20 s call that competes for the same 24 slots as users' live calls. Under a burst, users' estimate generations and Maple turns would queue behind shadow calls. That breaks the "never affects the user" guarantee (design 2026-10-02 §7.2) for latency, though not for errors. MEDIUM rather than HIGH: at today's traffic the queue is unlikely to form. (review 2026-10-07 #3)

**Decision (Simon, 2026-10-07):** not an issue — shadow runs only for the limited two-week review window, then is turned off. Revisit only if shadow is kept on longer, or if the window shows LLM queueing.

**Suggested fix (if revisited):** give shadow its own bound: a module-level `asyncio.Semaphore` (default 4) in `maple_shadow`, tried without waiting in `_plan_and_check`. When it's taken, skip planning and record `planner.error = "shadow_busy"` instead of queueing.

### 822. [LOW] The planner's estimate list core reaches the Estimate agent's private helpers through a duck-typed argument
`platform/agents/estimate/list_core.py:137` — `list_estimates_reply(..., helpers: Any)` calls `helpers._estimate_summary_payload` and `helpers._format_estimate_list_entry`. Neither uses agent state (they read the estimate and call `object_link`), so passing the agent in only to reach two private methods is the coupling switchover phase 2a's review removed from the executor. LOW: same package, works, but the signature hides what it needs. (review 2026-10-08 (2b) #7)

**Suggested fix:** Make them module functions in `agents/estimate/crud_helpers.py` (`estimate_summary(estimate)`, `estimate_list_entry(summary)`), keep the mixin methods as one-line wrappers for today's callers, and drop the `helpers` parameter and the executor's `_estimate_agent` lookup for the list.

### 840. [HIGH] Public Maple widget never runs the planner — a decision before the switchover

**File**: [routers/public_maple.py](../../platform/routers/public_maple.py)
**Severity**: HIGH
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md) (P2h)

`/public/maple/ask` answers on today's pipeline only. When today's pipeline is
retired (switchover plan §10), the public widget has nothing to run on. Decide:
move it onto the planner (with its own narrower op set — public Maple refuses
metrics and every write), or keep a small public-only reader. Needs Simon's call
before the switchover.

### 841. [MEDIUM] Planner: tasks referred to by recency, date or place

**File**: [agents/planner/refs.py:13](../../platform/agents/planner/refs.py), [agents/conversation/record_names.py:98](../../platform/agents/conversation/record_names.py)
**Severity**: MEDIUM
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md) (P1, reference §7.11 rows 1963–1966)

"the last task", "my latest task", "the task from yesterday / 3 days ago",
"the task at Elm House", and fuzzy titles: `RefBy` has no recency, date or
property kind, and name lookup is exact or word-start only. "add a description
to the last task" was planned as a task named "last task" and found nothing. Fix:
a `recent` (and date) ref for tasks, or route task names through today's
`find_task_from_context_or_message`.

### 842. [MEDIUM] Planner: task list and count filters it can't say

**File**: [agents/planner/schema_fields.py:185](../../platform/agents/planner/schema_fields.py), [agents/planner/execute_records.py](../../platform/agents/planner/execute_records.py) (`_task_ask`, `_task_count`)
**Severity**: MEDIUM
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md) (P1, reference §7.4–§7.5)

- "tasks for Jordan": today tries a property, then a teammate
  (`TaskListAsk.property_or_person`); the planner always picks the assignee.
  Add `TaskFilter.for_name`.
- "tasks due whenever", "what's due 10/3": no unread-date slot, so the planner
  guesses (10/3 read the US way) where today says the date back. Add `due_unread`.
- "all tasks by assignee": `_task_count` forces open tasks unless a status, due
  window or archived is said. Add `TaskFilter.all`.
- "who has the fewest tasks?": `TaskCount` has only `most`.

Each adds schema characters (budget 58,000, at ~57,100): batch them, and check live.

### 843. [MEDIUM] Planner: template names read as estimate titles

**File**: [agents/planner/resolve.py:352](../../platform/agents/planner/resolve.py)
**Severity**: MEDIUM
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md) (P3; parity `explained.py`)

"tell me about Driveway Maintenance" was planned as `list_estimates
{title_contains}`. "update Driveway Maintenance's description" was planned as an
estimate edit, where it should be the `template_edit` refusal. The planner can't
know a bare name's kind, and the resolver looks in one kind only. Fix: when a
bare-name reference finds nothing in its kind, try the other named kinds by exact
name (as today's `catalog_names.py` does). If a template matches an estimate
edit, refuse `template_edit`. Then drop the two `EXPLAINED` rows.

### 844. [MEDIUM] Planner: turns that still fall back whole — errors, and today's old questions

**File**: [agents/planner/turn.py](../../platform/agents/planner/turn.py) (`run_planner_turn`, `_kept_turn`)
**Severity**: MEDIUM
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md)

After phase 8 (switchover plan §7.27), two kinds of turn still go to today's
pipeline, and both need an answer before it is retired:
- **A planner failure:** a timeout, the LLM down, a second invalid plan, or a
  check or execute error before a write. It needs the planner's own "something
  went wrong, try again" reply.
- **A question today's pipeline asked in an earlier fallback turn**
  (`open_question`). These shrink as fallbacks go. At the switchover, drop them
  with `LOST_TRACK`, or convert them as `kept_questions` does.

### 845. [LOW] Planner: smaller shapes that still fall back

**File**: [agents/planner/confirm.py](../../platform/agents/planner/confirm.py), [agents/planner/execute.py](../../platform/agents/planner/execute.py), [agents/planner/execute_figures.py](../../platform/agents/planner/execute_figures.py)
**Severity**: LOW
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md)

- Two deletes in one plan (`confirm:several_deletes`). Ask about the first and
  keep the second for the next turn, or refuse as a bulk delete.
- A city or role beside another list filter ("contacts named Ana in Toronto"):
  `record_lists.list_reply` takes city and role alone.
- An estimate's lines by category or price ("which of E0001's materials cost
  over $10?"): `_lines_beyond`.
- A dashboard breakdown over a period it doesn't take, or "all time" on a
  windowed card (`_dashboard_uncovered`).
- A kept handler question in a multi-action plan where another action wrote
  (`kept_questions._wrote_beside`).
- A relative percentage that lands out of bounds raises before the write
  (`execute_estimates._changed_by`; `edit_estimate` is a write, so the reply is WRITE_FAILED — "part of the change may already be saved" — though nothing was written). It should be said
  ("that would make the markup −3%").
- "who owns 12 Oak St?": `get_property {field: owner}` lists every contact
  there, not the owners.

### 846. [HIGH] Planner: owed verification after phase 8

**File**: [tests/test_planner_parity_live.py:66](../../platform/tests/test_planner_parity_live.py), [tests/maple_conversations/](../../platform/tests/maple_conversations/)
**Severity**: HIGH
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md)

Phase 8 changed the prompt and the schema. They were checked live on 43
phrasings, all as intended, but that's not the parity run. Owed:
- **The parity run** (on request, ~$1.50). Diff it against
  `planner_parity.json` from 2026-10-11 00:24.
- **Task statuses in the parity state.** `plan_turn` is called without
  `planner_task_statuses`, so every task-status row is planned blind.
- **The acceptance corpus on the planner pipeline.** It was last run on 4
  conversations.
- **Acceptance conversations for the ~250 reference rows never put to the
  planner.** These are multi-step rows, rows that need a state, and rows with an
  ellipsis (`scripts/phrasing_reference_rows.py` lists them as not checked):
  §1.1 list refinements, §1.11, §4.8, §7.11, and §10.4–10.9.

### 847. [LOW] Planner: negated commands write

**File**: [prompts/maple_planner.py](../../platform/prompts/maple_planner.py), [agents/planner/said.py](../../platform/agents/planner/said.py)
**Severity**: LOW *(Simon 2026-10-11: users say what to do; a delete always asks)*
**Filed**: 2026-10-11, from the planner [gap review](plans/2026-10-11-planner-phrasing-gap-review.md) (P0, deprioritised)

"don't drop the markup on work item 2" was planned as markup 0, and "don't add a
note to it: call Bob" appended the note. Nothing on the planner path reads
negation. Recorded only, not to be worked unless it shows up in use.

### 848. [MEDIUM] An unknown stored status gives a blank refusal
`platform/agents/planner/policy.py:593` — Edge case. `_locked()` refuses any status outside Draft/Review, but `locked_edit_text` returns None for an unknown one, so the refusal text is `""` and the reply is empty. Today's handler fails open and allows the edit. (review 2026-10-11 #22, deferred)

**Suggested fix:** Refuse only when `locked_edit_text(...)` returns text. Test: an estimate stored with status "Pending" → the edit runs.

### 849. [MEDIUM] "tasks are off" is checked after the role and convert refusals
`platform/agents/planner/policy.py:605` — Edge case. The first refusal is the one said. With tasks off, a Member's task delete gets the archive offer (kept as a question), and a convert gets "Want to add one first?". Today's Task agent checks tasks-off first. (review 2026-10-11 #23, deferred)

**Suggested fix:** Move the tasks-off check to the top of `_check_rules`. Test: tasks off + Member `delete_task` → TASKS_DISABLED_MESSAGE, no question kept.

### 850. [MEDIUM] The archive/unarchive role refusal wording is untested
`platform/agents/planner/policy.py:304` — Edge case. The `who == "archive"` text is never asserted. (review 2026-10-11 #24, deferred)

**Suggested fix:** A non-creator Member archiving → `response == status_role_refusal_text("archive", code, DRAFT, ARCHIVED)`.

### 851. [MEDIUM] The missing-items send block, and the new refusal order, are untested
`platform/agents/planner/policy.py:355` — Edge case. Neither MISSING_ITEMS_SEND_BLOCK_MESSAGE as the reply, nor role-before-send-gate for a Member, is asserted. (review 2026-10-11 #25, deferred)

**Suggested fix:** An Owner sends the "gaps" estimate → MISSING_ITEMS_SEND_BLOCK_MESSAGE. A Member → the "only an Owner or Admin can send" text.

### 852. [MEDIUM] A status jump from a status with nowhere to go (`asks=False`) is untested
`platform/agents/planner/policy.py:295` — Edge case. The "there's nowhere I can move it from chat" arm, and that no question is kept, are untested. (It's unreachable with today's transition table; see #31.) (review 2026-10-11 #26, deferred)

**Suggested fix:** Monkeypatch `ESTIMATE_STATUS_TRANSITIONS` so the current status has no targets → assert the text and `_asks_again(done)` false.

### 853. [MEDIUM] `_from_step` when the earlier step found no single record is untested
`platform/agents/planner/policy.py:379` — Edge case. A step pointing at a list action becomes "unresolved", which should give would_ask; no test covers it. (review 2026-10-11 #27, deferred)

**Suggested fix:** `[list_contacts, update_contact {target: step 1}]` → the second ref status is "unresolved" and the decision is "ask".

### 854. [MEDIUM] A work item's label in the several-stale-records question is untested
`platform/agents/planner/confirm.py:226` — Edge case. The `work_item` arm of `_stale_label` isn't reached. (review 2026-10-11 #28, deferred)

**Suggested fix:** Two stale refs, one a work item → the question contains `the "Patio" work item on E00xx 'Birch Patio'`.

### 855. [MEDIUM] The `confirm:overage_with_others` / `convert_with_others` fallbacks are untested
`platform/agents/planner/confirm.py:200` — Edge cases. An overage beside a stale ref, and a convert beside a stale ref or a second convert, reach no test. (review 2026-10-11 #29, deferred)

**Suggested fix:** `confirm.ask` with OVERAGE_REASON + a stale ref → "confirm:overage_with_others"; the same for CONVERT_REASON.

### 856. [MEDIUM] An empty list total is untested
`platform/agents/estimate/list_core.py:118` — Edge case. The "You don't have any matching {plural} to total up." arm isn't reached. (review 2026-10-11 #30, deferred)

**Suggested fix:** `{list_estimates, filter:{statuses:[Lost]}, total}` with no Lost estimates → that text and count 0.

### 859. [MEDIUM] A city/role count with no results is untested
`platform/agents/conversation/record_lists.py:119` — Edge case. The `ask.count` arm with no rows isn't reached on either pipeline. (review 2026-10-11 #33, deferred)

**Suggested fix:** `{list_properties, filter:{city:"Ottawa"}, count}` → "You don't have any properties in Ottawa."

### 860. [MEDIUM] A count of exactly one is untested
`platform/agents/conversation/record_lists.py:121` — Edge case. The singular-noun arm isn't reached. (review 2026-10-11 #34, deferred)

**Suggested fix:** Guelph count → "You have 1 property in Guelph."; Administrator count → "You have 1 administrator."

### 861. [MEDIUM] The comparison said-back for average/largest/smallest, and "smallest", are untested
`platform/agents/estimate/metric_ratios.py:58` — Edge case. The fall-through arm, and every "smallest" entry, are never used by a test. (review 2026-10-11 #35, deferred)

**Suggested fix:** `said_back(_metric(metric="average", compare="quarter", status="sold", period="quarter"))` == the "I can't compare average estimates yet…" text, and smallest ranking → "I can't rank by smallest estimate yet.".

### 862. [MEDIUM] The task-delete archive offer's words are never asserted
`platform/agents/role_utils.py:25` — Edge case. The arm is driven, but only "owners and admins" is asserted, never "You can archive it instead — want me to do that?". MEDIUM, not HIGH, because the arm is driven. (review 2026-10-11 #36, deferred)

**Suggested fix:** Unit test: `manager_denial("delete tasks", DELETE_TASK_DENIAL_SUFFIX)` == the full sentence; tighten `test_delete_non_manager_refused`.

### 863. [MEDIUM] The role-rate refusal exists as two copies
`platform/agents/planner/execute.py:60` — `LABOUR_RATE_REFUSAL` is a hand copy of today's text at agents/labour/service.py:1016, which breaks the "one source" rule. The two can drift with no test failing. (review 2026-10-11 #37, deferred)

**Suggested fix:** Make it one constant in agents/labour/ (used at service.py:1016), imported by planner/execute.py and maple_outcomes.

### 864. [MEDIUM] A create followed by a work-item edit of the new estimate reports "Something went wrong"
`platform/agents/planner/execute.py:355` — `_made_by_a_step` lets `edit_estimate{estimate: step(create_estimate)}` through. But the policy skips work-item picks unless the estimate resolved to one, so `_commands` raises RecordNotLoaded after the create wrote, and the reply is WRITE_FAILED. MEDIUM, not HIGH: an unusual combination, and the create itself is saved and reported. (review 2026-10-11 #38, deferred)

**Suggested fix:** In `uncovered`, return `ref:…step` when a step-made estimate is the `estimate` of an op that needs work-item refs. Test: `[create_estimate, edit_estimate{estimate: step 1, commands:[… target position 1]}]` → uncovered is not None.

### 865. [MEDIUM] When a create makes nothing, the later steps are dropped without a word
`platform/agents/planner/execute.py:477` — Edge case. `_pointed` returns None and the loop breaks, so "create Mark Liu and link him to Birch House" answers only the create's reply and never says the link wasn't made. Untested. (review 2026-10-11 #39, deferred)

**Suggested fix:** When breaking with results, append "I didn't do the rest of that, since the first step didn't finish." Test: `create_contact_reply` monkeypatched to return a clarify with no contact → no link, and that sentence in the reply.

### 866. [MEDIUM] A policy refusal keeps the first refusal's text as the question, even when another one asks
`platform/agents/planner/execute.py:417` — `ask_again(..., first.refusal)` fires when any refusal asks. If action 1's refusal doesn't ask and action 2's does, the kept question is action 1's statement. (review 2026-10-11 #40, deferred)

**Suggested fix:** `asking = next(c for c in refused if c.refusal_asks); ask_again(context, message_en, asking.refusal)`. Test: a two-action refusal where only the second asks → the kept question equals the second.

### 867. [MEDIUM] A relative change on the work item this edit adds writes the amount as the value
`platform/agents/planner/execute_estimates.py:297` — The "added" target is converted before `_changed_by`, so "add a work item Fence and raise its markup by 5%" sets 5%. A negative value raises ValidationError, giving WRITE_FAILED. (review 2026-10-11 #41, deferred)

**Suggested fix:** For an added target with `relative=True`, ask or refuse ("set it to what?"), or add the company's default markup as the base. I'd refuse/ask: there's no current value yet. Test: `[add_work_item Fence, set_work_item_percentage{target: added, value:5, relative:true}]` → not written as 5.

### 868. [MEDIUM] The "kept the task" sentence is appended after a question
`platform/agents/planner/execute_records.py:414` — It fires on a clarify too (e.g. `convert_needs_description`), so the question is no longer last and `kept_questions._last_paragraph` could keep the wrong text. Untested. (review 2026-10-11 #42, deferred)

**Suggested fix:** Also require `not result.get("needs_clarification")`. Tests: `delete_task:true` on a convertible task → ends with KEPT_AFTER_CONVERT; on a blank task → ends with "Want to add one first?".

### 869. [MEDIUM] A policy refusal with no words falling back (`decision:refuse`) is untested
`platform/agents/planner/execute.py:334` — Edge case. The `all(c.refusal …)` False arm isn't reached by a test. (review 2026-10-11 #44, deferred)

**Suggested fix:** `PlanCheck("refuse", [ActionCheck(1, "edit_estimate", verdict="would_refuse", refusal="")])` → `uncovered == "decision:refuse"`.

### 870. [MEDIUM] Several refusals joined and de-duplicated is untested
`platform/agents/planner/execute.py:415` — Edge case. The two-action join is never driven. (review 2026-10-11 #45, deferred)

**Suggested fix:** Two refused actions, the same text twice plus one different → the response holds two paragraphs.

### 871. [MEDIUM] An estimate's lines by category or price falling back is untested
`platform/agents/planner/execute.py:313` — Edge case. The `_lines_beyond` True arm for an estimate isn't reached (the existing test uses a contact). (review 2026-10-11 #46, deferred)

**Suggested fix:** `list_materials{filter:{related: estimate, category:"Mulch"}}` with an estimate ref → "filter:list_materials.related".

### 873. [MEDIUM] `_metric`'s said-back reply is untested
`platform/agents/planner/execute_figures.py:102` — Edge case. Only `said_back()` and the gate are tested, not the handler arm. (review 2026-10-11 #48, deferred)

**Suggested fix:** `asyncio.run(_metric(metric{average, by_month}, …))` → the response equals the `said_back` text and the operation is "refusal".

### 874. [MEDIUM] Notes on a work item or a catalog record are only reached through the gate
`platform/agents/planner/execute_links.py:199` — Edge case. The `said_reply(no_notes_feed(domain))` arm isn't driven. (review 2026-10-11 #49, deferred)

**Suggested fix:** `list_notes` with a material parent → NOTES_NOT_ON_CATALOG_MESSAGE; with a work_item parent → WORK_ITEM_NOTES_IN_APP.

### 875. [MEDIUM] The estimate-first contact link, and an estimate whose property isn't the company's, are untested
`platform/agents/planner/execute_links.py:85` — Edge case. The second case is also misleading: it says the estimate "isn't linked to a property yet". (review 2026-10-11 #50, deferred)

**Suggested fix:** `_link(world, ("draft","estimate"), ("ana","contact"))` → Ana is on Birch. For a foreign property id, say "I couldn't find that estimate's property" and test it.

### 876. [MEDIUM] The guard for an estimate's property outside the company is untested
`platform/agents/planner/execute_records.py:108` — Edge case. (review 2026-10-11 #51, deferred)

**Suggested fix:** The estimate's property points at another company's property → `pytest.raises(execute.RecordNotLoaded)`.

### 877. [MEDIUM] A customer with several properties, and a property plus a customer, are untested
`platform/agents/planner/execute_estimates.py:374` — Edge case. (review 2026-10-11 #52, deferred)

**Suggested fix:** Ana on two properties → `made.property is None`. With both `property: Birch` and `customer: Ana` → `made.property == birch`.

### 878. [MEDIUM] `catalog_within`'s role wording is untested
`platform/agents/planner/execute_figures.py:23` — Edge case. Only the material arm is tested. (review 2026-10-11 #53, deferred)

**Suggested fix:** `catalog_within("foremen", "labour")` contains "all your roles".

### 879. [MEDIUM] The singular "uses 1 material" is untested
`platform/agents/planner/execute_records.py:261` — Edge case. (review 2026-10-11 #54, deferred)

**Suggested fix:** Count on an estimate with one material → "Estimate X uses 1 material."

### 880. [MEDIUM] A follow-up with nothing before it and only a limit or "last N days" gets the tax message
`platform/agents/planner/followups.py:300` — Edge case. `_nothing_before` falls through to NO_FIGURE for `redo_last {limit}` or `{period: last_n_days}`. (review 2026-10-11 #55, deferred)

**Suggested fix:** Return NO_FIGURE only when `before_tax` is set; otherwise ask "Which list or figure would you like …?". Tests for both shapes.

### 881. [MEDIUM] A ranking by count is treated as money
`platform/agents/planner/followups.py:112` — Edge case. `metric {shape: ranking, measure: count}` re-runs on a tax question instead of answering NO_FIGURE. (review 2026-10-11 #56, deferred)

**Suggested fix:** `_money` returns False when `last.get("measure") == "count"`. Test: a count ranking + before_tax → `Reply(NO_FIGURE)`.

### 882. [MEDIUM] `_redo_list`'s period fallback is untested
`platform/agents/planner/followups.py:123` — Edge case. (review 2026-10-11 #57, deferred)

**Suggested fix:** `_expand(_stored({"op":"list_tasks"}), {"op":"redo_last","period":"last_month"}) == "followup:redo_last.list_tasks.period"`.

### 883. [MEDIUM] A link side by listed or viewed with no kind is resolved as the focus kind
`platform/agents/planner/schema.py:386` — The validator now allows any non-name side without a domain. `resolve_ref` then uses `active_entity_domain`, which a list doesn't set. So "link the second one to Elm House" after a contact list asks the wrong question. Only focus (and step) were meant. (review 2026-10-11 #58, deferred)

**Suggested fix:** Allow a missing domain only for `focus` and `step`, or resolve `listed` from `last_listed_items.resource`. Test: `a={"by":"listed","n":2}` with no domain → raises, or resolves to the contact row.

### 884. [MEDIUM] The validator arm rejecting a name side with no kind is untested
`platform/agents/planner/schema.py:386` — Edge case. (review 2026-10-11 #59, deferred)

**Suggested fix:** `pytest.raises(ValidationError)` for a link `{"a":{"by":"name","text":"Ana"}, …}`.

### 885. [MEDIUM] `_the_note_itself` drops the record the user named
`platform/agents/planner/schema.py:416` — Edge case. "delete the first note on Bob Lee" while the notes listed are Ana's proposes Ana's first note. The confirmation names the record, which limits the harm. (review 2026-10-11 #60, deferred)

**Suggested fix:** Drop `parent` only when the listed notes' parent matches it; otherwise keep both and let the policy check the note belongs to the parent (ask on a mismatch). Test: Ana's list + parent Bob → asks.

### 886. [MEDIUM] `Dashboard.days` was added, but the unsaid guard skips dashboards
`platform/agents/planner/said.py:31` — Edge case. A card window carried from history is never dropped. "last 6 months" can only be planned as days (there's no `window_unit`). (review 2026-10-11 #61, deferred)

**Suggested fix:** Add `window_unit` to `Dashboard`, pass it to `_card_window`, and add "dashboard" to `_WINDOWED`. Tests for the dropped window and (6, "month").

### 887. [MEDIUM] The "sold or Review" question isn't in today's words and can repeat
`platform/agents/planner/said.py:277` — Today's says "That asks for two statuses at once — won or review. Which one did you mean? Ask again with just one…", using the user's own word. The planner says "sold". The appended answer still contains both words, so the same question can come back. (review 2026-10-11 #62, deferred)

**Suggested fix:** Word it from the user's word ("won"/"sold") as today does. On the answer, rewrite deterministically (keep the plan, drop `sold` or `statuses` per the reply). Test: "won" → the question says "won"; answer "Review" → statuses [Review], sold false.

### 888. [MEDIUM] Policy reason strings matched by literal copies
`platform/agents/planner/asks.py:316` — `_CONFIRMING` and `_other_question` copy six policy.py reason strings. Rewording one in policy.py silently turns those turns into the `ask:other` fallback. (review 2026-10-11 #63, deferred)

**Suggested fix:** Export them as constants from policy.py (STALE_WRITE_ASKS, DELETE_ASKS, NOTHING_ASKED, BARE_YES_NOTHING_ASKED, QUESTION_EXPIRED_PREFIX, DATE_AS_STATUS_PREFIX) and import them in both files.

### 889. [MEDIUM] A create's missing field in a multi-action plan is untested
`platform/agents/planner/asks.py:338` — Edge case. The "What's the name of the new contact?" arm isn't reached. (review 2026-10-11 #64, deferred)

**Suggested fix:** `[create_contact {}, link step 1 → property]` with `create_need("create_contact","name")` → that text, `label == "name"`, domain PLANNER_TEXT; plus a labour case ("wage").

### 890. [MEDIUM] LOST_TRACK through asks is untested
`platform/agents/planner/asks.py:329` — Edge case. (review 2026-10-11 #65, deferred)

**Suggested fix:** Reasons `["the question expired (asked over an hour ago)"]` → `found.text == confirm.LOST_TRACK and found.ask is False`.

### 891. [MEDIUM] The fallback text for a subject that matches nothing is untested
`platform/agents/planner/asks.py:293` — Edge case. When `found.reason` is empty, "Which customer or property did you mean by {said}?" is never tested. (review 2026-10-11 #66, deferred)

**Suggested fix:** `Resolved("name","subject","none")` with no reason → that text and `replace_text == said`.

### 892. [MEDIUM] The singular "I only listed 1 …" is untested
`platform/agents/planner/asks.py:271` — Edge case. (review 2026-10-11 #67, deferred)

**Suggested fix:** Reason "row 2 of a list of 1" for a task → "I only listed 1 task — which one did you mean?".

### 893. [MEDIUM] The note question's "that record" fallback is untested
`platform/agents/planner/asks.py:305` — Edge case. (review 2026-10-11 #68, deferred)

**Suggested fix:** A note ref resolved `via="parent"` with no `parent` ref → "You don't have any notes on that record to delete."

### 894. [MEDIUM] Ranking-of-nothing turning into "smallest" is untested
`platform/agents/planner/metric_ask.py:94` — Edge case. (review 2026-10-11 #69, deferred)

**Suggested fix:** `metric_ask(_metric(metric="smallest", shape="ranking"))` → ("figure", "smallest").

### 895. [MEDIUM] The `by == "added"` branch is unreachable and untested
`platform/agents/planner/resolve.py:412` — Edge case. A defensive guard: the policy handles "added" before calling the resolver. (review 2026-10-11 #70, deferred)

**Suggested fix:** `_pick(world, {"by":"added"}).status == "unresolved"`, or remove the branch with a comment.

### 896. [MEDIUM] The override's absolute out-of-bounds arm is untested
`platform/agents/planner/schema_edits.py:112` — The override replaces the base validator, and nothing asserts that a value of 600 (markup) still raises. (review 2026-10-11 #71, deferred)

**Suggested fix:** `pytest.raises(ValidationError)` for `{set_work_item_percentage, field: markup, value: 600}`.

### 897. [MEDIUM] The retry's failure arms are untested, and the first error is lost
`platform/agents/planner/planner.py:132` — Edge cases: the retry timing out or hitting an LLM error, and `_tool_error`'s missing-id fallback. A failed retry also drops the first invalid plan's raw args and error, which the shadow log exists to show. (review 2026-10-11 #72, deferred)

**Suggested fix:** When the retry yields no plan, keep the first `raw` and combine the errors (`f"{second} after {first}"`). Tests: invalid then a timeout → the error starts with "timeout" and raw is the first args; a tool call with no id → `tool_call_id == "plan"`.

### 900. [MEDIUM] The unsaid question at turn level is untested
`platform/agents/planner/turn.py:283` — Edge case. `said.without_unsaid` returning text, which becomes a kept question through `run_planner_turn`, is only tested at the `said` level. (review 2026-10-11 #80, deferred)

**Suggested fix:** Wire `list_estimates {sold, statuses:[Review]}` with "how many won estimates in review?" → the response is the question, and an open question carries REPLAN_KEY.

### 901. [MEDIUM] A question asked on a confirmed yes being kept is untested
`platform/agents/planner/turn.py:123` — Edge case. The overage-yes test asserts only the response prefix. (review 2026-10-11 #81, deferred)

**Suggested fix:** After "yes" to an overage create with no property, assert the open question is REWRITE_OP with `original_message == "link estimate E00xx to a property"` and OFFER_LABEL_KEY set.

### 902. [MEDIUM] The older estimate follow-up is untested, and its "no" isn't today's words
`platform/agents/planner/kept_questions.py:79` — Edge case. The `"estimate_code" in stored` arm is untested, and its decline says "Okay, I left E0042 unchanged." where today's (pending_estimate_follow_up.py:197) says "Okay, I left estimate '<title>' unlinked.". (review 2026-10-11 #82, deferred)

**Suggested fix:** Store the decline text per offer (today's sentence for the legacy record). Test the request and the decline.

### 903. [MEDIUM] Several handler questions in one turn is untested
`platform/agents/planner/kept_questions.py:122` — Edge case. All are dropped and only the newest is kept; nothing asserts this. (review 2026-10-11 #83, deferred)

**Suggested fix:** Two non-yes/no handler questions in `ran["context"]` → exactly one open question, with the newest text.

### 904. [MEDIUM] An estimate with no contacts is logged as an unanswered refusal
`platform/agents/planner/execute_records.py:104` — `said_reply` marks "…has no contacts yet" as `operation: refusal`, so the tracker records `policy/refusal` for what is an empty answer (CLAUDE.md: "nor is an empty list"). The same phrasing also exists in execute_links.py:93. MEDIUM rather than LOW: it skews the switchover gap list. (review 2026-10-11 #84, deferred)

**Suggested fix:** Return a non-refusal envelope (`operation: "list_contacts", count: 0`), and share one "isn't linked to a property" phrase.

### 905. [LOW] A tax follow-up on a list's total still falls back
`platform/agents/planner/followups.py:175` — `ListEstimates.before_tax` now exists, but "does that include tax?" after a planner list total returns `followup:redo_last.list_estimates.before_tax`, which test_planner_followups.py:255 pins. Today's pipeline answers it correctly, so this is LOW. (review 2026-10-11 #85, deferred)

**Suggested fix:** When `last.get("total")`, set `last["before_tax"] = change.before_tax` and return `last`; keep the fallback for a list or count. Update the test.

### 906. [LOW] With nothing before it, the follow-up's reply drops the plan's other actions
`platform/agents/planner/followups.py:321` — "thanks — and last month?" never runs the acknowledge. Only a pleasantry is lost. (review 2026-10-11 #86, deferred)

**Suggested fix:** Return the Reply only when the follow-up is the plan's only action; otherwise note it in the docstring.

### 907. [LOW] `unsaid_period` is dead code and its new arm breaks its contract
`platform/agents/planner/said.py:216` — Only tests call it. The `_sold_beside` arm returns a sentence, not `unsaid:<op>.<what>`. (review 2026-10-11 #87, deferred)

**Suggested fix:** Delete it, port its tests to `without_unsaid`, and update the module docstring.

### 908. [LOW] The guard against a carried customer passes after the question is answered
`platform/agents/planner/said.py:313` — The answered request contains "Bob Lee" in the question text, so `_named` passes even after a "no". It depends on the model keeping the filter. (review 2026-10-11 #88, deferred)

**Suggested fix:** Check only the user's text before the "— asked" suffix, or rewrite deterministically on "no".

### 911. [LOW] A note whose record is gone gets the work-item message
`platform/agents/planner/confirm.py:150` — `note_feed_of` returns None for a deleted parent too, which now says WORK_ITEM_NOTES_IN_APP. (review 2026-10-11 #91, deferred)

**Suggested fix:** Use that sentence only when `note.parent_type == WORK_ITEM`; otherwise "confirm:delete_unresolved".

### 912. [LOW] The docstring claims a plain no gets today's words
`platform/agents/planner/kept_questions.py:17` — A bare "no" is cancelled at the gate ("No problem, I've left it as is."); only longer declines reach `offer_declined`. (review 2026-10-11 #92, deferred)

**Suggested fix:** Correct the docstring.

### 913. [LOW] Four `_OFFERS` entries can't be reached from a planner turn
`platform/agents/planner/kept_questions.py:41` — Only `delegate_create_estimate` and calculate's `delegate_generic` arm offers. The contact, property, labour and material entries are dead. (review 2026-10-11 #93, deferred)

**Suggested fix:** Drop them, or arm the offers on the planner's creates and cover them.

### 914. [LOW] Branches that can't run
`platform/agents/planner/turn.py:238` — The LOST_TRACK arm of `_ask_back`, `_user_now`'s `now is None` arm, and `confirm:{op}` after all the delete kinds are unreachable. (review 2026-10-11 #94, deferred)

**Suggested fix:** Remove them, or comment why they're kept.

### 916. [LOW] Private names imported across modules
`platform/agents/planner/kept_questions.py:55` — `_router_flow_keys` here, and `_PARENT_TYPES` in note_pick.py:25, which also rebuilds `_remember_list`'s shape by hand. (review 2026-10-11 #96, deferred)

**Suggested fix:** Make them public accessors and reuse `_remember_list`.

### 917. [LOW] The `_answer` handler is effectively unreachable, and its docstring overstates it
`platform/agents/planner/execute.py:132` — An answer with nothing open goes through `_ask_back`. `_answer` runs only when a question was open, where "not waiting" would be wrong. (review 2026-10-11 #97, deferred)

**Suggested fix:** Say in the docstring that it only marks `answer` covered, or raise there.

### 919. [LOW] Public `narrowed()` has no docstring
`platform/agents/planner/execute_records.py:41` — A public helper is missing its docstring. (review 2026-10-11 #99, deferred)

**Suggested fix:** Add a one-line docstring.

### 920. [LOW] "other" refusals are filed as `guide_no_answer`
`platform/agents/planner/execute.py:84` — The planner's own unsupported verdict is mixed into the guide's misses in the report. (review 2026-10-11 #100, deferred)

**Suggested fix:** Give it its own constant (or a `result.reason == "other"` check classified first).

### 924. [LOW] The `confirmed=False` default has no caller
`platform/agents/task/planned.py:61` — The only caller always passes True. A future caller that leaves it out gets a question the planner can't answer. (review 2026-10-11 #104, deferred)

**Suggested fix:** Make `confirmed` a required keyword.

### 926. [LOW] The `company_id` guard didn't move into `list_reply`
`platform/agents/conversation/record_lists.py:95` — An empty id raises `InvalidId` in the now-public `list_reply`. (review 2026-10-11 #106, deferred)

**Suggested fix:** Move the guard into `list_reply`.

### 928. [LOW] "isn't linked to a property" phrasing duplicated across the executors
`platform/agents/planner/execute.py:433` — execute_records.py:104 and execute_links.py:93 build near-identical sentences by hand, so they will drift. (review 2026-10-11 #108, deferred)

**Suggested fix:** One helper in execute_links (`no_property_text(code, …)`) used by both.

## Platform — API, models and data

**Resolved 2026-09-27** (platform `2c2e5d0`): `agents/conversation/out_of_chat.py` answers company default percentages, team/invitations, billing/plan/credits, Load Standard, CSV import, units, divisions, unlink, duplicate, the estimate document and photos with the place in the app where each is done (user-guide wording), as a policy refusal read on the command head only. Pinned by `tests/test_out_of_chat_redirects.py` (including false-positive guards: work-item markup, "the duplicate contact", "the invoice task", note bodies) and corpus rows `boundary-*`. Snapshot: "duplicate it" and "set the company's default markup for work items to 20%" now redirect.

### 31. [MEDIUM] Intra-CSV duplicate rows now upsert silently instead of erroring
**Files**: `routers/equipments.py:148-170`, `routers/labours.py:204-229`
**Severity**: MEDIUM

Before the #24 fix, a CSV with two rows sharing the same `(name, unit)`
would insert the first and crash the second (captured into `errors[]`).
After the fix, the handler registers each newly-inserted row back into
`existing_by_key`, so the second occurrence upserts the first. The behavior
is arguably friendlier, but (a) it's undocumented, (b) no test exercises
it, and (c) the response payload reports N `created` IDs for an N-row
upload even when the user effectively paid for duplicate rows.

Fix: pick one of — (i) add a test pinning the new upsert-on-duplicate
behavior; (ii) or revert to the pre-fix error behavior by omitting the
`existing_by_key[(name, unit)] = row` registration line. If staying with
(i), consider splitting the response into `created` vs `updated` lists so
the caller can see what actually happened (materials.py already does this).

### 75. [MEDIUM] `CardItem.easy/standard/hard` unbounded
**File**: [platform/models/rate_card.py:26-28](../../platform/models/rate_card.py)
**Severity**: MEDIUM
**Why it's MEDIUM**: pre-existing — predates the unit-Literal change. But
the dropdown work tightened `unit` validation, and the same rigour should
apply to the rate fields: today negative, zero, NaN, and Infinity all pass
Pydantic. Frontend rejects negatives (`min="0"`); a direct API client or
malformed `default_rate_cards.json` can poison data and break effort
calculations (division by zero on a row's chosen difficulty).

Fix: `easy: float = Field(..., gt=0)` (and same for `standard`/`hard`).
Will require touching test fixtures that pass `0` and updating the frontend
helper text. Coordinate with whoever owns the Effort Calculator's
zero-handling so we don't change semantics underneath.

### 103. [MEDIUM] `delete_template` returns 200 on non-existent id
File: `platform/routers/templates.py:158-160`
**Severity**: MEDIUM

```python
if not template:
    return {"message": "Template not found"}
```

200 with a body that says "not found" is misleading. Mirrors
`routers/labours.py:336-338`, so it's a project convention rather than a
regression. If we ever standardize, fix all four (labours, templates, etc.)
together.

Fix: change to `raise HTTPException(404, "Template not found")` and update
the parallel routers in the same PR.

### 490. [MEDIUM] Same-field conflicts are still silent — the conflict-detection phase
Two writers changing the **same** field still resolve to whoever saves last,
with no detection and no signal to either user. Sparse writes shrink the
exposure to genuinely overlapping edits; they do not remove it.

**Suggested fix:** the designed, unscheduled follow-on plan is
[`plans/2026-08-24-concurrent-update-conflict-detection.md`](plans/2026-08-24-concurrent-update-conflict-detection.md)
— a `version` field on Estimate and Task, an atomic conditional write using the
`find_one_and_update` idiom already in `services/task_convert.py:77`, auto-merge
when the changed-field sets do not overlap, and a 409 naming the conflicting
fields when they do. **Supersedes #59**, which proposed optimistic concurrency
keyed on `estimate.updated_at` for the Drive-filename race.

**Status 2026-09-22 — in progress.** Built:

- `services/conflict_detection.py` — `conditional_update` (precondition,
  bounded auto-merge, 409 via `ConflictError`) and `versioned_set` for writers
  that hold no loaded version. `version: int = 0` on `Estimate` and `Task`.
- Both PUT routes take an optional `base_version` and put
  `audit_metadata(document, patch)` — `version` plus the `fields` actually
  written — on their audit entry. `changed_fields_since` reads those, falling
  back to the `changes` diff only for older entries (the diff over-reports:
  it also picks up whatever another writer landed mid-request). It requires
  the entries to be **contiguous** over `(base, current]`; any gap degrades
  to a document-level conflict rather than an auto-merge. The returned
  document is built from the write's own `ReturnDocument.AFTER` snapshot, so
  the audited version is always this write's.
- Every other writer bumps `version`: Maple's Task agent
  (`_apply_task_update`, audited with the version), and Maple's estimate
  writes via `persist_fields` plus the three direct `.set()` sites that used
  to bypass it (`estimate_update.py`, `pending_property_link.py`,
  `pending_estimate_follow_up.py`). The cost backfill no longer does a
  whole-document `.save()`, which could move `version` backwards.
- Raw pymongo skips Beanie's event actions, so `conditional_update` re-runs
  the model's `after_event(Update)` hooks itself — the estimate PUT route is
  the load-bearing caller of `Estimate.note_brevo_lifecycle`.
- Portal: the TaskDialog sends `base_version` and renders `ConflictNotice`
  (Reload / Save anyway) from Save, Archive and Create Estimate; Save anyway
  resumes whichever of the three the conflict interrupted. The builder's
  whole-save sends only changed header fields (`lib/estimateHeaderPatch.ts`),
  a prerequisite for versioning it.

**Remaining — the estimate builder:**

1. **Maple's estimate writes bump `version` but most record no audited
   version.** `persist_fields` has no user and writes no audit entry, so once
   the builder sends `base_version`, any conflict spanning a Maple edit
   degrades to document level — a false conflict whenever the fields were in
   fact disjoint, which is the failure the whole design exists to avoid. Give
   `persist_fields` (or its callers) an audit entry carrying
   `audit_metadata(written, update)` **before** wiring the builder. No
   before-state is needed: the recorded fields are what the lookup reads.
2. Wire `base_version` into the builder's field auto-save and whole-save, and
   render `ConflictNotice` there.

**Deploy:** `scripts/backfill_document_versions.py --apply` is no longer a
hard prerequisite — the precondition matches a missing `version` for base 0 —
but run it once per environment so stored data carries the number the API
reports.

### 29. [LOW] `update_estimate` recalculates totals on any `job_items`-present edit
**File**: `routers/estimates.py:1868-2016`
**Severity**: LOW (likely won't fix)

When `payload.job_items is not None`, the handler recalculates the entire
estimate's totals — even if the client sent back unchanged items alongside a
notes/title edit. Overhead is real but CPU-bound and negligible at normal
estimate sizes.

The reviewer framed this as waste, but the *safer* reading is that
gating recalculation on change-detection would risk stale totals if the
change-detector missed a case. Leave alone unless profiling shows latency.
Filed so we don't re-litigate.

### 35. [LOW] `names` list in materials bulk-fetch may contain casing duplicates
**File**: `routers/materials.py:295`
**Severity**: LOW

`names = [md["name"] for md in grouped.values()]` — `grouped` is keyed by
`name.lower()`, so names are unique by casefold but not by original
casing. A CSV with both `"Patio Stone"` and `"patio stone"` would produce
two `$in` entries that both resolve to the same Mongo row.

Fix: `list({md["name"] for md in grouped.values()})`. Micro-optimization;
skip unless already editing the file.

### 67. [LOW] `PydanticObjectId(company)` returns 500 on garbage input
**File**: [platform/routers/divisions.py:44](../../platform/routers/divisions.py)
**Severity**: LOW

A malformed `?company=xyz` query raises `bson.errors.InvalidId` →
unhandled → 500 instead of a clean 422. Mirrors `material_categories`
and `material_units`. Pre-existing pattern; defer.

Also surfaced 2026-05-13 in the hodgepodge `/code-review` pass against
`platform/routers/estimates.py` — the new `get_analytics` route and the
adjacent list endpoint both call `PydanticObjectId(company)` and share
the same 500-on-garbage-input gap. Fold both into the cross-router fix
below.

Fix: wrap in try/except → `HTTPException(422, "Invalid company id")`,
or factor a Pydantic dependency that validates ObjectIds and use it
across all `?company=` query routers (divisions, material_categories,
material_units, estimates list, estimates analytics).

### 78. [LOW] Validation error message doesn't list allowed units
**File**: [portal/src/lib/rateCards.ts:28](../../portal/src/lib/rateCards.ts)
**Severity**: LOW
`"Item ${i+1}: Unit must be one of the allowed values."` is unactionable
for any user who hits it (which shouldn't happen via the UI, but could from
a stale tab or a copy-paste).

Fix: include the list:
```ts
` Item ${i + 1}: Unit must be one of: ${RATE_CARD_UNITS.join(", ")}.`
```

### 102. [LOW] `duplicate` insert lacks 409 fallback
File: `platform/routers/templates.py:120-136`
**Severity**: LOW

`_next_copy_name` does a `find_one` for the candidate name, then
`copy.insert()`. Between those two awaits, another caller could insert the
same name, and the unique `(company, name)` index would surface a
`DuplicateKeyError` to the client as a 500 instead of a clean 409.

Fix: wrap the insert in `try/except DuplicateKeyError` and either retry
once with the next `(copy N)` suffix or raise 409. Low likelihood — the
window is sub-millisecond and same-user duplicate spam is the only realistic
trigger.

### 201. [LOW] Use `Query(..., ge=1, le=50)` for `list_invoices` limit
**File**: `platform/routers/billing.py:282`
**Severity**: LOW

Inline `max(1, min(limit, 50))` clamping silently coerces bad input. `Query(12, ge=1, le=50)` returns a clean 422 instead.

### 202. [LOW] Validate Stripe `brand` against an allow-list before persisting
**File**: `platform/services/billing/webhook_handlers.handle_payment_method_attached`, `platform/routers/billing.py:111`
**Severity**: LOW

The brand string flows from Stripe → DB → FE rendering. Not a security issue today (Stripe controls the value), but if it's ever rendered un-escaped, an unexpected brand value breaks the UI.

Fix: lowercase and check membership in `{"visa", "mastercard", "amex", "discover", "diners", "jcb", "unionpay", "unknown"}` before persisting.

### 321. [LOW] `begin_template_estimate` divides by `template.size` without the zero-guard its sibling has
**Where:** `platform/routers/agent_helpers/template_estimate.py:200-201,258-261`

**Issue:** `_has_baseline` accepts `size == 0.0` (`is not None`), then `begin_template_estimate` computes `converted / template.size` → `ZeroDivisionError`. The pending-turn handler guards this (`not baseline_size`), so the two paths are inconsistent. A zero-size template is nonsensical/unlikely but the asymmetry is a latent trap.

**Fix:** Make `_has_baseline` require `template.size` truthy, or guard the division and fall through to `_ask_size_envelope`.

### 339. [LOW] `load-standard` POSTs have no `response_model`
Both routes return plain summary dicts (`{loaded, removed, skipped_in_use}`),
not documents — no leakage risk, and this matches the `/materials/load-standard`
precedent. Logged only because the repo convention declares `response_model` on
most routes. Fix (optional): a small shared `ReloadResult` Pydantic model;
natural to do together with #336.

### 342. [LOW] Auto-create of missing categories/units has a find-then-insert race
Added 2026-06-07 with the load-standard auto-create change.
`services/material_bootstrap.py::_ensure_referenced_categories_and_units`
checks the pre-loaded name→doc dict, then `await .insert()`s any missing
`MaterialCategory` / `MaterialUnit`. `MaterialCategory`/`MaterialUnit` have a
`(company, ASCENDING)` index but it is **not unique** and not on
`(company, name)`, so two concurrent `load-standard` calls for the same company
could each create the same category/unit → duplicates. This mirrors the
identical race in `routers/materials.py::_find_or_create_category` /
`_find_or_create_unit` (the upload path) — an accepted pattern, and bootstrap is
effectively single-shot (onboarding / one button click), so practical risk is
low. Fix (closes both call sites at once if ever wanted): add a unique
`(company, name)` index to both models and catch `DuplicateKeyError` in the
create helpers.

### 386. [LOW] platform/routers/support.py — clear/seen/current endpoints lack per-user rate limits
Only the send endpoints are rate-limited. `clear` posts to Slack per call; abuse is bounded (requires an open conversation, archived after one call) but the guard is one line.
**Suggested fix:** Apply `auth_rate_limiter` with modest limits (e.g. 10/min) to the three remaining endpoints.

### 401. [LOW] platform staff provisioning — email-format validation + DuplicateKeyError hardening
`staff_service.py` / `routers/ops.py` don't validate email format before provisioning, and don't translate a Mongo `DuplicateKeyError` (race between the existence check and insert) into a clean 409 — it would currently surface as an unhandled 500.

### 402. [LOW] platform/routers/auth.py — invitation staff-email 403 could name the offending email
The staff-email guard on `POST /auth/company-invitations` fails the whole batch with a generic "This email cannot be invited". For multi-email batches, include the offending email in the 403 detail (it is the inviter's own input, so no information leak). Keep the atomic-403 semantics — do not half-process the batch.

### 409. [LOW] platform/routers/tasks.py — sort=due_date aggregation helper fields ride along on documents
`_undated` and `_sort_time` are computed by the pipeline and only dropped implicitly by pydantic at `Task.model_validate`; a future `extra="allow"` config change (or raw-dict return) would leak them to clients.
**Suggested fix:** Append `{"$unset": ["_undated", "_sort_time"]}` (or a $project) as the final pipeline stage in `_find_tasks_by_due_date`.

### 419. [LOW] platform/services/task_quota.py:46 — accepted check-then-insert race (informational)
Two concurrent creates at limit−1 can both pass `is_task_limit_reached` and land
one over the cap. Deliberate and documented in the module docstring: overshoot
is bounded by in-flight concurrency, nothing is billed, and the next create is
blocked.
**Suggested fix:** None required. If ever needed, an atomic claim would require
a denormalized counter (estimate-quota pattern) with decrements on both
hard-delete paths.

### 423. [LOW] platform/routers/properties.py:295 — malformed property_id produces a 500 instead of 404
`Property.get(property_id)` raises on a string that is not a valid ObjectId
(e.g. `GET /properties/abc/map.png`), surfacing as a 500. Inherited verbatim
from the existing `get_property` / `update_property` pattern in this router —
the new map-image route is consistent with its siblings, but it adds one more
instance of the pattern.
**Suggested fix:** A shared parse-or-404 helper applied router-wide (fixing
only the new route would make it inconsistent with siblings).

### 453. [LOW] platform/routers/ops.py:417 — company-detail payload carries stale membership fields
Reviewed and **accepted as-is** rather than deferred by omission. `list_company_users`
calls `_serialize_user_summary(u, company.name)` with defaults, so the payload reports
`membership_status="active"` and `company_archived=False` even for an archived company.

This was originally raised as HIGH ("the two ops pages contradict each other") and that
was wrong about impact: `OpsCompanyDetailPage` renders Name / Email / Role / Joined and
never reads either field, so no operator-visible inconsistency exists. The page is also a
*roster* view — "who is attached to this company" — and its header already shows the
company as archived, so per-row orphan labelling would be redundant. The product decision
is that the roster should keep listing attached users exactly as it does now.

What remains is dead data that could mislead later: whoever next adds a Status column to
that table would get wrong values with no hint why.

**Suggested fix:** if that table ever grows a Status column, pass the real values at the
same time — `company` is already loaded on line 410, so it costs no extra query:
`membership_status(u.company, ..., company_archived=_is_archived(company))` and
`company_archived=_is_archived(company)`. Until then, no change.

### 468. [LOW] platform/routers/tasks.py — `POST`/`PUT /tasks/` still bind the raw `Task` Document
There is no `TaskCreate`/`TaskUpdate` Pydantic schema, so PUT is a full-replace bind: every
field a client omits resets to its model default. The exclude set at `routers/tasks.py`
is now eight entries long (`readable_id`, `title`, `task_date`, `photos`, `estimate`,
`converting`, `converting_since`, `archived`) and each one is load-bearing — the
`readable_id` entry exists purely because the portal's kanban drag would otherwise blank
the id on every column move. That is a list you have to remember to extend every time a
server-owned field is added, and forgetting is silent data loss.

**Suggested fix:** introduce explicit `TaskCreate` / `TaskUpdate` request models listing
only the client-writable fields. Then a forgotten field is inert rather than destructive.

### 492. [LOW] Stripe webhooks replace the whole Company document
`services/billing/webhook_handlers.py` calls `await company.save()` at six sites
(lines 75, 87, 102, 122, 142) on `customer.subscription.*`, `invoice.paid`,
`invoice.payment_failed` and `payment_method.attached`. Each is a
read-modify-write of the entire company record, racing with anyone editing
Settings — and `portal/src/components/settings/FinancialTab.tsx:213` spreads a
possibly-stale `companyDetails` into its own save, so the collision runs both
ways. No seat count required; this is reachable on a one-person account.

Deliberately out of scope: the sparse-writes work was scoped to the seven
resources the request named, and Company was not one of them.

**Suggested fix:** the same treatment — an `UpdateCompanyRequest` DTO on
`routers/companies.py:220` plus `services/sparse_update.build_patch`/`finalize`,
and targeted `.set()` calls in the webhook handlers instead of `.save()`.

### 496. [LOW] platform/routers/properties.py:418 — `changed()` gate lost the old whitespace/None normalization
The old comparison normalized with `str(x or "").strip()`; the new `changed()` compares raw
values, so `"Toronto "` vs `"Toronto"`, or `""` sent for a stored `None`, counts as an address
change and spends a geocode round-trip (fail-open, so cost only).
**Suggested fix:** normalize in the property handler before calling `changed()` (strip
strings, coerce `""`/`None` equivalence) — three lines — or accept the occasional spurious
geocode and note it in the comment.

### 567. [LOW] Every storage error on the doc-image GET becomes a 404
`platform/routers/estimate_documents.py:264` — `except Exception` → 404 "Image not found". A transient Firebase outage looks like a deleted image, so the Documents dialog may render it as gone and the user may drop it from the form.

**Suggested fix:** Map `google.api_core.exceptions.NotFound` → 404 and everything else → 503.

### 570. [LOW] `logger.exception` in doc creation sends customer PII and signed URLs to Sentry
`platform/routers/estimate_helpers/doc_versions.py:164` — The frame's locals hold `replacements` (customer name, property address, free-text NOTES) and `images` (10-minute signed URLs). The line predates the Documents dialog and is router code, hence LOW.

**Suggested fix:** `logger.error("Failed to create Google Doc for estimate %s (%s)", estimate.estimate_id, type(err).__name__)`, with no `exc_info`.

### 607. [MEDIUM] Deleting a doc version can still remove a blob a concurrent generate is keeping
`platform/routers/estimate_documents.py (delete_docs_version)` — Partly fixed 2026-09-23 (code review #7): the version is now removed with an atomic `$pull` and orphans are computed from the returned document, which narrows the window. It does not close it: a generate that has already resolved its kept images can still have one deleted underneath it, and then either 502s or records a version pointing at a missing blob. Needs two tabs or two users within the generate window.

**Suggested fix:** Decided 2026-09-23: option (b), a delayed sweep, was chosen as the real fix but deferred because it needs a scheduled job. Mark candidate paths on version delete instead of deleting them, and have a sweep delete ones still unreferenced by any version after ~15 minutes.

### 631. ~~[MEDIUM] The estimates PUT still recomputes with the old formula~~ — RESOLVED 2026-10-03

**Resolved 2026-10-03 (user: one formula):** The PUT prices each work item with `work_item_breakdown`, the server port of the portal's math, so the stored total is the one the estimate page and Maple show: 5 × 2.5 × $3.99 at 15% markup and 13% tax is $64.85, not $64.81. Legacy `labours` lines no longer price a work item (the portal never sends them); the two API tests that priced one now use an activity. A stored labor burden still prices, as before. Review rounds of that batch: AI generation, Maple's add-work-items path and the manual (`skip_generation`) create price the same way once an item has material or activity lines (`job_item_builders._price_as_the_page`) — an item with neither keeps its own figure — and a sized template stores its scaled lines' price, not its total times the factor. Tests: `test_estimate_api.py::test_update_estimate_prices_work_items_as_the_portal_does`, `test_build_job_items_from_parsed_prices_lines_as_the_portal_does`, `test_manual_create_prices_work_items_as_the_portal_does`, `test_template_create_routing.py::…test_a_sized_template_stores_the_price_of_its_scaled_lines`.

`platform/routers/estimates.py:1296` — The PUT rounds once, half-even; Maple now rounds each line, half-up. Verified: 5 lines of 2.5 × $3.99 with 15% markup and 13% tax → PUT $64.81, Maple $64.85. A portal save restates a total Maple stored to the cent, and the assumption rescale's exact `line_derived` check (< 0.01) now flags portal-saved items as manual overrides.

**Suggested fix:** Have the PUT use `work_item_breakdown` (the portal sends burden 0), or loosen `line_derived` to accept either formula. Needs your call because it changes the HTTP API's stored totals; I'd pick the former for one formula everywhere. **Awaiting Simon's decision** (changes the totals the HTTP API stores).

*(Review 2026-09-24 fourth pass #17.)*

### 790. ~~[LOW] An estimate's activity role and rate card are saved unchecked~~ — RESOLVED 2026-10-01

**Resolved 2026-10-01** (tenant batch 2): `snapshots.assert_own_line_refs` now covers activity roles (Labour) and `effort_rate_card_id` (RateCard) on estimate create/update; ids already stored aren't re-checked.
`platform/routers/estimates.py:1169` — `activities[].role` and `activities[].effort_rate_card_id` (and the create path in `job_item_builders.py` ~176) are stored with no company check, so an estimate can link another company's role or rate card. Nothing is shown from them unless the same id is also a labours line, which batch 1 now checks. (tenant audit 2026-10-01, A3)

**Suggested fix:** Check new ids with `dependencies.assert_company_refs` (Labour, RateCard), skipping ids already on the estimate, as `snapshots.assert_own_line_refs` does for lines (CLAUDE.md "Tenant scope of referenced ids").

### 792. ~~[LOW] Category and unit "in use" counts look across every company~~ — RESOLVED 2026-10-01

**Resolved 2026-10-01** (tenant batch 2): Both deletes and both load-standard bootstraps count only the company's own materials.
`platform/routers/material_categories.py` delete, `routers/material_units.py` delete, `services/material_category_bootstrap.py` ~63, `services/material_unit_bootstrap.py` ~66 — `Material.find(category == id)` / `{"sizes.unit": id}` have no company filter, so another company's materials pointing at X's category block X's delete and reveal a count. New links are refused since #702; old ones remain. (tenant audit 2026-10-01, A6)

**Suggested fix:** Add `company` to each count query.

### 793. ~~[LOW] Deleting a property clears the property on estimates of any company~~ — RESOLVED 2026-10-01

**Resolved 2026-10-01** (tenant batch 2): The cascade filters on `Estimate.company == property.company`.
`platform/routers/properties.py:539` — `Estimate.find(Estimate.property == property.id).update(property=None)` has no company filter, so a cross-company link written before batch 1 lets X's delete edit Z's estimate. (tenant audit 2026-10-01, A9)

**Suggested fix:** Filter the cascade on `Estimate.company == property.company`.

### 794. ~~[LOW] Setting the default card doesn't check the card is the company's~~ — RESOLVED 2026-10-01

**Resolved 2026-10-01** (tenant batch 2): `sync-payment-method` refuses (404) a payment method whose `customer` isn't the company's Stripe customer, before setting it as default.
`platform/routers/billing.py:440` — `sync-payment-method` retrieves `body.payment_method_id` and sets it as the default without checking `pm.customer == company.stripe_customer_id`. Stripe should refuse a card not attached to the customer, so likely not exploitable. (tenant audit 2026-10-01, A10)

**Suggested fix:** Refuse (404) when `pm.customer` isn't the company's Stripe customer, before the update call.

## Platform — services, scripts and integrations

### 350. [MEDIUM] Credential fields are plain `str`, not `SecretStr` — both known leak paths closed 2026-07-27
**Severity**: MEDIUM (was HIGH until 2026-09-21 — see "Incident closed" below)
`platform/config.py` holds every credential as a plain `str` — `openai_api_key`,
`stripe_sk`, `stripe_webhook_secret`, `slack_bot_token`, `slack_signing_secret`,
`slack_webhook_url`, `brevo_api_key`, the three `trello_*` values,
`google_maps_api_key`, `mongodb_url` (password embedded in the URI),
`sentry_dsn`, `recaptcha_v3_secret`, and `firebase_credentials_json` /
`google_drive_credentials_json` (whole service-account blobs, RSA private key
included). Zero `SecretStr` usage.

**The 2026-07-27 incident — CLOSED 2026-09-21, no rotation required.** A backend
test run surfaced Settings content in plain text, putting the live Stripe
`sk_live_` key, OpenAI key, Brevo key, Slack signing secret and the Firebase
private key into test output. Scope verified at the time: **not** in any commit
(`.env` / `.env.local` are gitignored — re-confirmed 2026-09-21 that no env file
other than `.env.example` has ever been committed on any branch), **not** in CI
logs (`platform/` has no GitHub Actions workflows and the pre-push hook
deliberately skips pytest).

The one question rotation depended on was whether that output ever left the
machine. **Owner confirmed 2026-09-21: it did not** — never pasted into a bug
report, a Slack thread, or Sentry. No credential is known to have reached a
third party, so **rotation is not required and the recommendation is
withdrawn.** Earlier revisions of this entry carried "the exposed keys have not
been rotated" as its most urgent open item and ranked it #1 in the priority
queue on that basis; both are superseded. What remains is defense-in-depth.

*On the exact mechanism:* an earlier draft of this entry said pytest printed the
frame's locals. That is **not** verified and is probably wrong — `--showlocals`
is not in this repo's `pytest.ini` `addopts`, so locals are not rendered by
default. The producing path could not be reconstructed after the fact. The
likelier candidate is the `ValidationError` path described below, which formats
`input_value=<the value>` and was directly observed echoing (fake) secrets while
this very fix was being written. Recorded this way deliberately: a follow-up
entry that misstates *how* a credential leak happened will misdirect whoever
investigates the next one.

**Both leak paths closed 2026-07-27**, two different ways — neither covers the
other:

1. **Rendering an existing object.** `Settings.__repr_args__` masks anything
   `_is_secret_field()` classifies as a credential. pydantic v2 routes
   `__repr__`, `__str__` and `__pretty__` through that hook, so reprs,
   f-strings, `print()`, and any log line or traceback frame that displays the
   object are covered by one override with **no call-site changes**. Verified
   against a real `--showlocals` traceback, which renders
   `Settings(mongodb_url='********', openai_api_key='********', …)`.
2. **Failing to construct one.** pydantic raises before an object exists to
   repr and formats the error as `input_value=<the value>` — a path
   `__repr_args__` cannot reach. `hide_input_in_errors = True` on the `Config`
   class closes it for *every* construction path, not just the module-level
   singleton. Errors still name the offending field, so a malformed `.env`
   remains debuggable at startup.

Classification is name-based (`key`, `secret`, `token`, `password`, `credential`, `dsn`) plus an
explicit `_EXTRA_SECRET_FIELDS` set for the three that carry no marker —
`mongodb_url`, `stripe_sk`, `slack_webhook_url`. Name-based on purpose: a
credential added later is masked by default rather than exposed by default.
Unset values render honestly as `None` / `''`, because masking those would hide
whether a credential is configured at all and an empty value leaks nothing.

Tests: `tests/test_settings_repr_masking.py` (76 cases, covering both leak
paths). Note the deliberate
assertion style — every check computes a bool *before* asserting, because
`assert settings.openai_api_key not in text` would make pytest print both
operands on failure and leak the exact value under test. There is also a
guard test that fails when a new field starts matching the classifier, forcing
a deliberate decision instead of a silent default.

**Still open — but latent, not live (re-verified 2026-09-21):**
- A call site that reads one field and logs it (`logger.info(settings.stripe_sk)`)
  still handles a plain `str`. **No such call site exists today** — the only
  print of a credential field is `scripts/db/drop_db.py:121`, which routes
  `mongodb_url` through `_redact_mongo_uri()` first.
- `model_dump()` / `model_dump_json()` are unmasked. **No non-test call site
  invokes `settings.model_dump()`.**

Both are guards against a *future* call site rather than a current leak, which
is why this dropped to MEDIUM: nothing in the codebase exposes a credential
today.

**Read this before working on it — local *is* production (verified 2026-09-21).**
`.env.local` and `.env.production` hold byte-identical values for `stripe_sk`
(prefix `sk_live_`), `stripe_webhook_secret`, `openai_api_key`, `brevo_api_key`,
`firebase_credentials_json`, `google_maps_api_key` and `sentry_dsn`; only
`mongodb_url` differs (Dev vs Prod cluster). `config.py:289` loads `.env.local`
**last**, so it wins, and `tests/conftest.py:23` overrides **only**
`MONGODB_URL`. Every `./run_tests.sh` run therefore holds the real production
Stripe live key in `settings`. That is the structural reason a local test run
could put production credentials on screen at all, and no fix above changes it.
Tracked separately as [#566](code-review-followups-archive.md#566-medium-local-dev-and-test-runs-load-real-production-credentials--closed-2026-09-22-accepted-risk).

**Suggested fix (the remaining work):** convert the credential fields to
`SecretStr` and update the ~98 read sites to `.get_secret_value()`. Counted
2026-07-27: `openai_api_key` 22, `stripe_sk` 19, `mongodb_url` 17, `sentry_dsn`
6, `google_maps_api_key` / `google_drive_credentials_json` / `brevo_api_key` 5
each, `slack_webhook_url` / `slack_bot_token` 4 each, `trello_api_key` /
`trello_api_token` 3 each, `stripe_webhook_secret` / `firebase_credentials_json`
2 each, `slack_signing_secret` 1. Tedious but low-risk: `SecretStr` is not a
`str`, so every missed site becomes a mypy error and the project's zero-error
gate catches them all before runtime.

### 74. [MEDIUM] JSON re-parsed on every `bootstrap_company_rate_cards` call
**File**: [platform/services/rate_card_bootstrap.py:20](../../platform/services/rate_card_bootstrap.py)
**Severity**: MEDIUM
The loader reads + parses `default_rate_cards.json` on every call. Cheap
individually, wasteful in the backfill loop (12× during the recent
backfill, more whenever a new bootstrapper is added).

Fix: `@functools.lru_cache(maxsize=1)` on `load_default_rate_card_templates`,
or assign at module import. Tests already monkey-patch
`DEFAULT_RATE_CARDS_PATH`, so any cache must be invalidated in those tests
(via `cache_clear()` in a fixture).

### 77. [MEDIUM] `SEED_COMPANY_ID` is a magic constant tied to live data
**File**: [documentation/development/migration_scripts/export_default_rate_cards.py:26](../../documentation/development/migration_scripts/export_default_rate_cards.py)
**Severity**: MEDIUM
The hard-coded ObjectId is documented in the module docstring but not
guarded. If this script is re-run after the seed company evolves, it
silently overwrites `default_rate_cards.json`.

Fix: either accept the company id as a CLI arg with no default, or refuse
to overwrite an existing `default_rate_cards.json` without a `--force`
flag. Low priority since the script is clearly labeled "one-shot".

### 195. [MEDIUM] Reconciliation cron for "soft-failed" plan selection
**File**: `platform/routers/billing.py:186` (select-plan), `platform/routers/billing.py:492` (enterprise-contact)
**Severity**: MEDIUM

Both endpoints catch `Exception` broadly with the comment "reconciliation cron retries" — but the cron doesn't exist yet. A user whose plan-selection Stripe call silently failed thinks they're on Pro/Base; the BE has the local plan set but no Stripe subscription. There's nothing to find their orphaned record later.

Fix: either (a) build the planned reconciliation job that scans companies with a non-Free local plan but no `stripe_subscription_id` and replays the missing call, or (b) persist a `BillingReconciliationQueue` row at the catch site so the future cron has explicit work to find. At minimum, fire a Sentry capture inside the except block and surface a soft-warning flag in the response so the FE can show "Your plan is saved; we'll finish setup shortly."

### 196. [MEDIUM] Implement `payment_failed` user notification
**File**: `platform/services/billing/webhook_handlers.py:114` (TODO)
**Severity**: MEDIUM

Customers in `past_due` after a card decline are not notified by the platform. Stripe's "Smart Retries" Dashboard emails partially cover this, but the codebase shouldn't rely on that implicitly — and we lose the chance to brand the message.

Fix: send via `services/brevo_email.send_brevo_plain_email` from the `invoice.payment_failed` handler. Subject: "Payment failed — update your card." Link target: customer-portal session URL.

### 259. [MEDIUM] Migration script uses Beanie field descriptors as `.set()` keys
`platform/scripts/db/migrate_approved_to_sent.py:60` calls
`estimate.set({Estimate.status: ..., Estimate.updated_at: ...})`. The
rest of `routers/estimates.py` (3 call sites at 910, 993, 1071) uses
string keys: `estimate.set({"status": ..., "updated_at": ...})`. Beanie
tolerates both forms but the inconsistency is surprising. Low-effort
fix — swap the keys to string literals to match the codebase.

### 294. [MEDIUM] Make `RECAPTCHA_MIN_SCORE` configurable
**Where:** `website/functions/index.js:13`.

**Why:** The 0.5 threshold is hardcoded. Fresh keys with no traffic history routinely score below it (we hit this in dev). Tuning currently requires a code change + redeploy.

**Suggested fix:** Use `defineString('RECAPTCHA_V3_MIN_SCORE', { default: '0.5' })` from `firebase-functions/params`, parse to float at handler start, fall back to 0.5 on `NaN`. Set per-environment via `firebase functions:config` or a runtime param.

### 546. [MEDIUM] platform/scripts/migrate_landscaping_industry.py:73 — no way to target prod, and no confirmation before --apply

The script takes only `--apply`. `config.py` loads `.env.local` with precedence, so on a developer
machine an unqualified `--apply` writes to the **Dev cluster** — with no prompt and no echo of which
database it just modified. Its sibling `backfill_companies_to_free.py` grew `--prod`, `--mongo-url`,
and a LIVE confirmation prompt for exactly this reason. An operator can work around it with an inline
`MONGODB_URL=...`, which is why this is MEDIUM rather than HIGH, but that path is undocumented and the
docstring doesn't mention it. Less urgent since `CompanyIndustry._missing_` landed (finding #2) — the
migration is now a cleanup pass rather than a deploy gate — but the script will still be run against
production eventually.

**Suggested fix:** mirror the `backfill_companies_to_free.py` interface: add `--prod` (read
`MONGODB_URL` from `.env.production`/`.env`, bypassing `.env.local`), `--mongo-url`, and a
`--yes`-skippable confirmation before `--apply`. At minimum, print the target host before writing and
document the `MONGODB_URL=` inline override in the module docstring.

### 59. [LOW] Drive-filename filename-collision policy still implicit
**Severity**: LOW
The 2026-04-23 fix put the estimate_id back into the Drive filename
(`Estimate-{estimate_id}-V{n}`), which resolves traceability. However,
Drive still permits duplicate filenames within a folder — there is no
enforcement that `(estimate_id, version)` is globally unique *as a
filename*. If two concurrent generate-doc requests race, they could
produce two Drive files with the same name. The version-number
computation in `routers/estimates.py:2376-2379` is also read-modify-
write without a lock.

Fix: add a unique index on `(estimate_id, version)` inside the
`GoogleDocsVersion` embedded array, or wrap the version-bump + create
in an optimistic-concurrency retry keyed on `estimate.updated_at`.
Low priority — the user would need to double-click "New Version" within
the Drive latency window to trigger the race.

**Superseded 2026-08-24** by the conflict-detection plan
(`plans/2026-08-24-concurrent-update-conflict-detection.md`), which puts a real
`version` field on Estimate rather than keying on `updated_at`. See the
2026-08-24 section at the end of this file.

### 61. [LOW] Trello httpx client rebuilt per request
**File**: [platform/services/trello_service.py:40](../../platform/services/trello_service.py)
**Severity**: TRIVIAL (don't fix unless path becomes hot)

`async with httpx.AsyncClient(timeout=15.0) as client:` inside
`create_trello_card` tears down the connection pool on every call.
Reviewer correctly flagged that a module-scoped client would enable
connection pooling.

In practice: this endpoint fires once per estimate → card creation. The
pool-churn cost is microseconds on a call that already takes hundreds of
ms over the network. Premature optimization at current volume.

Fix (if it ever matters): promote to a module-level
`_client = httpx.AsyncClient(timeout=15.0)` and swap the `async with`
for `await _client.post(...)`. Add a FastAPI lifespan hook to close it
on shutdown.

### 69. [LOW] Bootstrap services log nothing on success
**Files**: [platform/services/division_bootstrap.py](../../platform/services/division_bootstrap.py),
[platform/services/material_category_bootstrap.py](../../platform/services/material_category_bootstrap.py),
[platform/services/material_unit_bootstrap.py](../../platform/services/material_unit_bootstrap.py)
**Severity**: LOW

All three bootstrap helpers run silently on success. The wrapper in
`company_service.py` does `logger.exception(...)` on failure, so
failures are observable, but successful seeding leaves no audit trail.
Useful diagnostic when investigating "why does this company not have X"
questions.

Fix (low value, low effort): emit `logger.info("Seeded N {resource}
templates for company %s", company_id)` from each bootstrap function.

### 204. [LOW] Don't write Stripe webhook signing secret to repo working tree
**File**: `platform/scripts/setup_stripe_webhook.py:140-157`
**Severity**: LOW

The script writes the signing secret to `secrets/webhook_signing_secret.<id>.txt` with `chmod 0600`. Reasonable, but the file persists until manually removed and an operator who misses the print-message reminder leaves a real `whsec_…` in the working tree.

Fix: use `tempfile.NamedTemporaryFile(delete=False, dir="/tmp")` outside the repo, or print the secret to stderr and have the operator pipe to `.env` directly. Alternatively, register an `atexit` handler that clears the file unless `--keep-secret` was passed.

### 223. [LOW] SetupIntent idempotency window not configurable
**File**: [platform/routers/billing.py:271](../../platform/routers/billing.py)
**Severity**: LOW

`int(time.time() // 60)` hardcodes a 60-second bucket. Fine in
practice — Stripe SetupIntent.create returns in under 2s — but if the
network ever degrades to >60s round-trips, a retry would mint a new
key and create the duplicate intent the key was meant to prevent.

Fix: optional. Either accept a client-supplied `idempotency_key` from
the request body, or expose the bucket size as a `Settings` field
(`stripe_idempotency_window_seconds: int = 60`). Don't fix in
isolation; roll into the next billing router touch.

### 224. [LOW] Sentry extras include Stripe PaymentMethod ID
**File**: [portal/src/components/billing/AddPaymentMethodModal.tsx:194-197](../../portal/src/components/billing/AddPaymentMethodModal.tsx)
**Severity**: LOW

The capture added by [#209](code-review-followups-archive.md)
attaches `paymentMethodId` (a Stripe PM ID like `pm_…`) to Sentry
under `extra`. PM IDs aren't PII per Stripe's classification, but
they're correlation keys someone with both Sentry and Stripe access
could use to look up the underlying card brand/last4.

Fix: optional, depends on Sentry retention policy. Either add an
inline `// Stripe PM IDs aren't PII; safe to attach for debugging`
comment to document the stance, or move `paymentMethodId` from
`extra` (indexed) to `contexts` (free-form attached metadata, less
prominent in alert UIs).

### 225. [LOW] `APP_BASE_URL` has a localhost default that ships to production
**File**: [platform/config.py:80](../../platform/config.py)
**Severity**: LOW

The `app_base_url: str = Field(default="http://localhost:5173", ...)`
default added by [#197](code-review-followups-archive.md)
is correct for dev, but a production deploy that forgets to set
`APP_BASE_URL` bounces customers from the Stripe Customer Portal back
to `http://localhost:5173/settings` — "site can't be reached" from
their browser. Better than the prior hardcoded prod URL (the previous
state guaranteed dev/staging users got bounced), but still relies on
ops remembering to set it per environment.

Fix: optional safety net at app startup — if
`sentry_environment == "production"` and
`app_base_url.startswith("http://localhost")`, log a CRITICAL warning
or abort. Or change the Settings field to `str | None = None` and
assert non-None at the use site for prod environments.

### 359. [LOW] platform/services/company_bootstrap.py:68 — (name, unit) lookup key assumes canonical unit casing
`existing_by_key` is keyed by `(doc.name, doc.unit)` where `doc.unit` is the LabourUnit
str-enum, and looked up with the template's raw `unit` string. It works today only because
default_labours.csv uses exactly "Hourly" (verified). If a future seed row used an
alias/lowercase unit ("hour"), the key would miss on rerun and insert a DUPLICATE role
instead of overwriting. The legacy find_one had the same latent gap, so this is not a
regression — but the in-memory key makes the casing assumption implicit.
**Suggested fix:** Normalize the template unit when building/looking up the key, e.g. key
on `LabourUnit.from_string(template["unit"])` on both sides, so alias/case variants resolve
to the same enum. (Or assert the seed CSV uses canonical unit values.)

### 360. [LOW] platform/services/material_bootstrap.py — insert_many is non-atomic on partial failure
`Material.insert_many(to_insert)` (and the labour equivalent) isn't transactional. A
mid-batch failure (e.g. a duplicate-key race, validation) leaves some rows inserted, then
raises up to the load-standard router as a 502 with `created` never set. The pre-existing
one-insert-per-row loop had the same partial-state shape, so this isn't a regression, just
worth being aware of now that it's a single bulk call.
**Suggested fix:** Optional. If atomicity matters, wrap the bulk writes in a Motor
transaction (the atlas-local replica set supports them), or pass `ordered=False` and
surface a partial "imported N of M" result instead of a bare 502.

### 372. [LOW] platform/services/translation.py:712 — unbounded concurrency in `asyncio.gather`
One LLM call is fired per segment with no concurrency cap. In practice `suggestions` is a small fixed UI set (~3-4 chips) so fan-out is caller-bounded, but there is no structural guard; a future caller passing a large `suggestions` list would launch that many simultaneous LLM calls (rate-limit / burst-cost risk).
**Suggested fix:** Optional — bound it with a `Semaphore` or cap the number of translated chips if suggestion counts could ever grow. Not needed at current call sites.

### 374. [LOW] platform/services/template_bootstrap.py:241 — duplicate catalog names collapse silently (last-wins)
`materials_by_name` / `labours_by_name` are dict comprehensions keyed by name. Material has a non-unique (company, name) index, so two same-name rows silently keep only the last — resolution could bind to an unexpected size/price with no signal.
**Suggested fix:** Optional — log a warning when a name maps to >1 catalog doc.

### 375. [LOW] platform/services/template_bootstrap.py:152 — size label kept when requested size doesn't match
When `size_str` is provided but matches no `MaterialSizeCost`, `_resolve_material_size` falls back to the first size for price/unit, yet the item stores the original `size_str`. Result: a line item whose size label and price/unit can disagree. (No current template hits this — all sizes match.)
**Suggested fix:** Store `size.size` (the resolved label), or route a non-matching size to `unmatched_materials`. Document the chosen behavior in the helper docstring.

### 405. [LOW] platform/services/transcription.py — language/duration always None without verbose_json
`transcriptions.create()` is called without `response_format`. `gpt-4o-mini-transcribe` never returns language/duration, and `whisper-1` only does with `response_format="verbose_json"`. Fields are nullable and unused by the planned frontend, so behavior is correct today.
**Suggested fix:** Either request verbose_json when the model is whisper-1, or document that language/duration are best-effort and typically None.

### 434. [LOW] platform/config.py — falsy non-string values render unmasked
`Settings.__repr_args__` guards on truthiness (`if ... and value`), so a
secret-classified field holding `0` or `False` renders as-is rather than
masked. No current field is affected — every field the classifier matches is
`str` or `str | None`, and the truthiness check is deliberate there so unset
credentials show honestly as `None` / `''` instead of a misleading `********`.
The gap is latent: a future field such as `api_key_rotation_count: int = 0`
would match the `key` token and print unmasked while zero.
**Suggested fix:** test `value not in (None, "")` instead of truthiness, which
preserves the honest rendering of unset string credentials while covering
numeric and boolean fields.

### 486. [LOW] platform/services/brevo_lifecycle.py:361 — a new httpx client per event
`emit` opens `httpx.AsyncClient()` per call, so the reconcile sweep builds and tears down a
connection pool for every event of every user. Harmless in a request handler firing one
event; wasteful in a sweep that may fire thousands.
**Suggested fix:** either accept it (it matches `services/brevo_contacts.py`, and the sweep
has no deadline) or let `emit` take an optional client the sweep creates once and passes in.
Leaning accept — consistency with the sibling module is worth more here than the connections
saved on a nightly job. Logged so the choice is deliberate rather than inherited.

### 511. [LOW] platform/services/readable_id.py — the spoken pattern can emit a spurious longer candidate
`TASK_CODE_SPOKEN` spans separators, so `"T0042 5"` yields both `T0042` (typed)
and `T00425` (spoken, swallowing the trailing number). The typed candidate now
sorts first by position, so the resolver reaches the right task; a wrong
candidate costs one database miss on a message shaped like "T0042 5 hours".
**Suggested fix:** low priority. If tightened, require a spoken match to contain
at least one internal separator, so it cannot re-read a contiguous typed code
plus a following number. `ESTIMATE_CODE_SPOKEN` carries the identical behavior —
fix both or neither.

### 515. [LOW] platform/services/brevo_lifecycle_reconcile.py:70 — `EstimateFacts` can represent an incoherent state
`started=True` with `started_at=None` is representable, and does occur for a legacy estimate
whose `created_at` is missing. It is handled correctly (`replay_attributes` falls back to the
default), but the dataclass also lets a caller construct `built=False, built_at=<date>`,
which is meaningless.
**Suggested fix:** low value and not worth much churn. If tightening: add a `__post_init__`
assertion that each `*_at` is None whenever its boolean is False. The leaning is to leave it —
the type is internal to this module and the aggregation is its only real producer.

### 564. [LOW] The `job_item_index` half of the work-item-summary index is vestigial

`platform/models/work_item_summary.py` — the compound index is
`(estimate_id, job_item_index)`, but since #563 made indexing append-only no
query filters or sorts on `job_item_index`. Both remaining queries (the
"already indexed?" probe and the manual `delete_work_item_summaries`) use the
`estimate_id` prefix alone, so the second key is dead weight on every write.

Left alone deliberately: changing it means Beanie creates the new single-key
index while the old compound one lingers until someone drops it by hand, which
is an operational step for no functional gain.

**Suggested fix:** narrow to `IndexModel([("estimate_id", ASCENDING)])` and drop
the old index, whenever this collection next needs a migration for another
reason. Not worth its own deploy.

### 562. [LOW] The work-item corpus now only grows, and nothing bounds it

`platform/models/work_item_summary.py` — §6 of #557's plan, explicitly out of
scope for that change and now a live question. Every row carries a 1536-float
embedding, nothing deletes a row automatically any more, and the status join
that used to keep the working set small by accident is gone.

Not urgent: it becomes real the first time one company's corpus outgrows the
`$vectorSearch` candidate window (`numCandidates = limit * 10`), at which point
retrieval quality degrades quietly rather than failing.

**Suggested fix:** a per-company row cap or an age cutoff, decided before a
large customer hits it rather than after. Worth measuring the largest tenant's
row count first — this may be years away.

### 576. [LOW] `_image_object_size` divides by width and height unguarded
`platform/services/google_doc_images.py:31` — A 0 dimension raises `ZeroDivisionError`, surfacing as an unexplained 502. Stored dimensions come only from server processing and are ≥1 today.

**Suggested fix:** `max(width_px, 1) * PX_TO_PT`, and the same for height.

### 577. [LOW] The no-marker fallback insert point assumes a non-empty doc body
`platform/services/google_doc_images.py:94` — `content[-1]` raises `IndexError` on an empty body, which ends in a 502 and a trashed doc instead of appended images.

**Suggested fix:** `insert_at = content[-1]['endIndex'] - 1 if content else 1`.

### 610. [LOW] A 16-bit color PNG's transparency key never matches, so the "transparent" color prints
`platform/services/estimate_doc_images.py` — Found while fixing the 16-bit grayscale case (code review 2026-09-23 #2). For a 16-bit RGB PNG, Pillow reduces the pixels to 8-bit but leaves the tRNS key in 16-bit, so no pixel ever equals the key. The keyed color (often magenta or green) prints on the customer's doc instead of flattening to white. Rare: it needs a 16-bit RGB PNG that uses a color key rather than an alpha channel.

**Suggested fix:** When `image.mode == "RGB"` and `image.info["transparency"]` has any component above 255, scale the key down to 8-bit (`>> 8`) before the convert to RGBA. Test: a 16-bit RGB PNG with a magenta key comes out with no magenta pixels.

### 817. [MEDIUM] Sentry ships frame locals — token claims and chat messages — with every `logger.exception`
`platform/main.py:59` — `sentry_sdk.init` leaves `include_local_variables` at its default (True; SDK 2.70), and `send_default_pii=False` does not strip frame variables. The default scrubber denylists exact keys such as `token`, not `decoded_token`, `message` or `context_payload`. So each of the ~29 `logger.exception` calls on Maple paths (`routers/agents.py:1828` among them) can send the user's Firebase claims (uid, email), their chat message and conversation state to Sentry. The estimate edit executor and the template instantiation (#318) log the exception type only for this reason, but that costs the stack. Found reviewing #318 (review 2026-10-05 #1).

**Suggested fix:** Needs your decision. Either set `include_local_variables=False` in `sentry_sdk.init`, which keeps every stack and drops locals everywhere (my pick: one line, covers all sites, and the type-only logs could go back to full tracebacks); or keep locals and add an `EventScrubber` denylist for `decoded_token`, `message`, `context_payload`, `chat_history` and the user/email names — narrower, but every new local name is a new leak.

### 857. [MEDIUM] Public `or_join`'s empty and two-item arms are untested
`platform/services/estimate_status.py:98` — Edge case, unreachable today (every status allows 1 or 3 targets), but the helper is now public. (review 2026-10-11 #31, deferred)

**Suggested fix:** Unit test: `or_join([])==""`, `["A"]`→"A", `["A","B"]`→"A or B", `["A","B","C"]`→"A, B, or C".

### 858. [MEDIUM] `locked_edit_text` failing open on an unknown status is untested
`platform/services/estimate_status.py:140` — Edge case. It's now the planner's lock as well as today's. (review 2026-10-11 #32, deferred)

**Suggested fix:** Assert `locked_edit_text("E1", None) is None`, and None for Draft and Review.

### 922. [LOW] `who` accepts any string
`platform/services/estimate_status.py:127` — Any `who` other than "sent" gets the archive wording. (review 2026-10-11 #102, deferred)

**Suggested fix:** Type it as `Literal["sent", "archive"]` (and `status_change_role_refusal`'s return), with an explicit archive arm.

## Portal — estimate builder

**Update 2026-09-27** (platform `a612723`, `3526a08`): the server half is fixed — the conversation remembers its language (`conversation_lang`), a short reply in a non-English conversation is detected and translated, a code/email/number reply is answered in the conversation's language, and "No."/"No, thanks." read as a no. Still open (portal, design §8): the restored transcript shows the English history.

**Resolved 2026-09-27** (platform `9f657b4`, portal `97c87f4`): a non-English turn's chat lines carry `display_text` — the user's own words and the reply as sent — written by a second, conditional save after the reply is translated; the restored transcript shows `display_text` over the English `text` the pipeline keeps. Pinned by `tests/test_conversation_display_text.py` and `useMapleAgent.test.tsx`.

### 131. [MEDIUM] `saveError` displayed far from origin
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM

`saveError` (description / property auto-save failures) is rendered in
the Work Items header; users blurring the description at the top of
the page won't see the message if scrolled. Work item dialog now uses
its own `workItemDialogError` so this affects only description and
property.

Fix: render `saveError` adjacent to the field that failed, or use a
toast. Simplest: append a small inline error under the description /
property when their auto-save fails.

### 146. [MEDIUM] EffortCalculator mobile dropdown initial-render flicker
**File**: [portal/src/components/estimates/EffortCalculatorDialog.tsx](../../portal/src/components/estimates/EffortCalculatorDialog.tsx)

**Severity**: MEDIUM

When the modal opens with `selectedCardId === null` and
`rateCards.length > 0`, the mobile `<select>` shows the first card's
name while the right panel still reads "Select a rate card to begin"
until the parent useEffect fires. Brief visual mismatch.

Fix: initialise `selectedCardId` synchronously via `useState(() => …)`
reading the first rate card so there's no null window. Keep the
existing useEffect for the open/close transitions.

### 16. [LOW] Delete-button propagation on touch devices
**File**: `portal/src/pages/NewEstimateWithActivityPage.tsx` (trash button
per work item row)
**Severity**: LOW (needs manual verification)

The row has an `onClick` that opens the work-item editor, and the trash
button inside the row calls `e.stopPropagation()`. On some touch devices a
long-press can fire both `pointerdown`/`click` paths and both handlers run.
Not verifiable from source — needs a mobile-browser test.

Fix (if the test shows leakage): add
`onPointerDown={(e) => e.stopPropagation()}` alongside the existing
`onClick` on the trash button.

### 57. [LOW] Stale closure of `estimate` in `handleGenerateGoogleDoc`
**Severity**: LOW
In `portal/src/pages/NewEstimateWithActivityPage.tsx`, after
`await handleSaveEstimate()` resolves, the local `estimate` identifier
still refers to the pre-save snapshot — only `getEntityId(estimate)` is
read afterward, and the ID doesn't change, so no current bug. But anyone
extending this path to read a field that can change mid-save (e.g.,
`estimate.status`, `estimate.updated_at`) will silently use stale data.

Fix: widen `handleSaveEstimate` to return
`Promise<EstimateWithExtras | null>` and use the resolved value instead
of the closure reference.

### 104. [LOW] `TemplateDialog` captures `initialName` only on mount
File: `portal/src/components/estimates/TemplateDialog.tsx:36`
**Severity**: LOW

`useState(initialName ?? "")` reads `initialName` only on first render.
Switching from create-mode to edit-mode without remount would leave `name`
empty. Currently safe because `TemplatesPage.tsx` passes `key={dialogKey}`
and gates with `{isFormOpen && <TemplateDialog ... />}`, forcing a fresh
mount each time.

Fix: only required if either the key or the gate is removed. If so, sync
`name` via a `useEffect` on `initialName` change.

### 105. [LOW] Templates page re-fetches `/companies/{id}` on every mount
File: `portal/src/pages/TemplatesPage.tsx:60-74`
**Severity**: LOW

Every visit to `/templates` re-fetches the company doc just to read profit
margin / overhead / labor burden / tax. Other pages
(`NewEstimateWithActivityPage`, `PeoplePage`) do the same, so it's a
codebase-wide convention.

Fix: hoist company defaults to a context provider or React Query cache in
a follow-up that addresses all the consumers at once. Not worth a one-page
change.

### 107. [LOW] Inventory-gaps panel does not reflect template-inserted work items until save
File: `portal/src/pages/NewEstimateWithActivityPage.tsx:418-424`
**Severity**: LOW

`inventoryGaps` is memoized off `estimate` (the server snapshot), not
`workItems` (the editor state). When a user inserts a template, any
unmatched materials/activities the template carries don't surface in the
gaps panel until the estimate is saved and reloaded. Same behavior as
`handleAddWorkItem` — pre-existing limitation, not a regression — but
worth knowing because templates are more likely to carry unmatched items
than from-scratch work items.

Fix: rebuild gaps from `workItems` rather than `estimate.job_items` so
in-progress edits surface immediately. Out of scope for the Templates
feature; revisit if the gaps panel becomes a primary editing surface.

### 108. [LOW] `templates.find()` could return undefined on stale state
**Severity**: LOW
File: `portal/src/components/estimates/UseTemplateDialog.tsx:51`

If templates were re-fetched mid-confirm and the list shrank,
`templates.find((t) => getEntityId(t) === selectedId)` returns undefined.
The `if (chosen)` guard handles it correctly (the OK click silently does
nothing), so the path is safe. Could improve UX by clearing `selectedId`
when it disappears from the list — but with the dialog gated by
conditional mount, the templates list never refreshes mid-session.

Fix: none required while the dialog is mounted-on-open. If we ever switch
to keep-mounted-with-refresh, add `useEffect` to clear `selectedId` when
it disappears from `templates`.

### 139. [LOW] Pre-existing `printWindow.document.write` deprecation hint
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW

TS `6387` hint at line ~545 in `handleChecklistPdfDownload`. Predates
this session. Replace with `printWindow.document.body.innerHTML = …`
or build the document via DOM APIs.

### 149. [LOW] `lastSavedDescriptionRef` / `lastSavedTitleRef` initial-value window
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW

The two refs added by #133 (and the title fix that landed alongside)
are initialized to `""` and only seeded to the canonical server value
inside the estimate-load `useEffect`. There is a brief window between
mount and load where the ref is stale.

In practice no save can fire during that window — `autoSaveField`
returns early when `!estimateId`, and the title/description fields
are not interactive until the page renders post-load — so this is
theoretical only. Worth noting for future maintainers who might
introduce a save path that bypasses those guards.

Fix: optional. Either fold the seeding into the `useState` initializer
(reading from a route loader), or leave a stronger inline contract
comment near the ref declarations.

### 179. [LOW] Inline `reduce` on `activityRows` recomputed every render
**Severity**: LOW
`portal/src/components/estimates/WorkItemInlineContent.tsx:701` —
the "N.NN hours total" pill walks `activityRows` on every render via
inline `.reduce(...)`. Cheap (<50 rows), but inconsistent with the
surrounding `breakdown` value which is properly memoized via the
`computeBreakdown(...)` hook.

Fix: hoist into a `useMemo(() => activityRows.reduce(...), [activityRows])`
to match the file's existing pattern. Defer until a perf complaint or
the next time someone is in this code path.

### 261. [LOW] Session-stored estimate filter can be the now-removed "Approved" value
`portal/src/pages/EstimatesPage.tsx:96` —
`sessionStorage.getItem("estimatesStatusFilter") ?? "Draft"` is read
verbatim. Users who had `Approved` selected before the swap will see
the `<select>` render an orphan value (not in `statusOptions`), which
shows as a blank option in the dropdown. Defensive coerce:

```tsx
const saved = sessionStorage.getItem("estimatesStatusFilter");
return saved && statusOptions.includes(saved) ? saved : "Draft";
```

Self-heals within a few days as users click a real option and overwrite
the stale value, so LOW priority.

### 266. [LOW] `onBlur` prop fires on every contenteditable blur, not just true wrapper-exit
`portal/src/components/common/MarkdownDescriptionEditor.tsx:132` —
mdxeditor's `onBlur` is forwarded raw, so the parent's `onBlur` runs
whenever focus leaves the contenteditable (e.g. when the user clicks
a toolbar button, even though they're still editing). The estimate
page dedupes via `lastSavedDescriptionRef`, so this is harmless in
practice. Fix: gate the forwarded `onBlur` on `relatedTarget` not
being inside `wrapperRef`, mirroring the focus-tracking logic for
`handleBlurCapture`. Then `onBlur` only fires when focus truly leaves
the editor surface — safer for any future consumer that doesn't
dedupe.

### 271. [LOW] Clear-all toolbar button bypasses `handleMarkdownChange`
`portal/src/components/common/MarkdownDescriptionEditor.tsx:97` —
the toolbar Clear button calls `onChangeRef.current("")`
directly, skipping `handleMarkdownChange`, so `lastEmittedRef`
isn't updated. The visible behavior is correct (sync effect
re-runs and calls `setMarkdown("")`), but the asymmetry breaks
the invariant "lastEmittedRef equals the most recent value we
emitted" that the sync guard relies on. Fix: route Clear through
`handleMarkdownChange("")` so every emit path updates the ref.

### 272. [LOW] `lastEmittedRef` is never re-synced from external updates
`portal/src/components/common/MarkdownDescriptionEditor.tsx:57` —
when the sync effect calls `setMarkdown(value)` for an external
update, it doesn't write `lastEmittedRef.current = value`. We get
away with it today because mdxeditor fires `onChange` after
`setMarkdown` and the ref catches up via that path, but the
invariant is implicit. If a future mdxeditor version stops
emitting onChange on setMarkdown, the next external sync could
falsely short-circuit. Fix: set `lastEmittedRef.current = value`
inside the sync effect right after the `setMarkdown` call.

### 274. [LOW] `encodeBlankParagraphs` runs on every keystroke
`portal/src/components/common/MarkdownDescriptionEditor.tsx:90-96` —
`handleMarkdownChange` runs the regex scan on every onChange,
which scales linearly with description length. Not a real perf
concern at human typing speed, but worth profiling if estimate
descriptions ever grow into the multi-thousand-character range
(e.g. AI-generated long-form descriptions). Fix: only revisit if
profiling surfaces it.

### 377. [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1213 — `key={idx}` on a deletable work-item list (pre-existing)
Work items can be deleted, so index keys can cause React to mis-associate row state on removal. Not introduced by this change — the line was only shifted — but it sits in the edited map.
**Suggested fix:** Use a stable id if available (e.g. the work item's own id). Out of scope for the styling change; fold into a follow-up if desired.

### 450. [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1083 — read-only property field can render a raw ObjectId
The fallback chain ends `... || property || "-"`, where `property` is the raw
property id string. If both the fetched property and the list lookup miss
(deleted property, failed fetch), a locked estimate shows the user a Mongo
ObjectId. Pre-existing — the property-label fix neither introduced nor worsened
it — but the line was touched.
**Suggested fix:** replace the `property` term with `UNASSIGNED_PROPERTY_LABEL`
from `lib/propertyDisplay`, matching how `getEstimateProperty` handles a
missing property.

### 478. [LOW] portal/src/components/estimates/AddMaterialGapDialog.tsx:315 — the read-only sizes table in the same dialog keeps a 160px Unit column
When the resolve dialog shows an *existing* material, the Unit cell renders plain
`text-sm` text (line 355) in a `w-[160px]` column with no `whitespace-nowrap`. At 14px,
"Cubic yards (cu yd)" needs ~157px including the `px-3` padding, so the longest names wrap
onto two lines and the row heights jump. Not a truncation, so lower severity than the
editable select — but it is the same dialog the user was looking at, and it now disagrees
with the editable table's 240px.
**Suggested fix:** widen this header to match the editable table (`w-[240px]`) so unit
names stay on one line and both tables in the dialog line up.

### 545. [LOW] portal/src/components/estimates/InventoryGapsPanel.tsx:147 — key fallback contradicts the accordion id

The material row key is `gap.id || i`, implying `id` may be absent, while the accordion uses bare
`gap.id` for both `toggle()` and the open comparison. If an id were ever empty, every empty-id row
would share `openId === ""` and open together. Not live today — ids are generated as
`material-gap-${index}-${gapIndex}` in `estimateInventoryGaps.ts` and are always truthy — so this is
an inconsistency rather than a bug. (The role-group equivalent was fixed as #2 in this pass.)

**Suggested fix:** drop the fallback to `key={gap.id}`, matching what the accordion already assumes.

### 559. [LOW] Redundant cast before the `instanceof` guard it duplicates
`portal/src/components/common/MarkdownDescriptionEditor.tsx:360` —
`const target = e.target as Element | null;` is followed immediately by
`if (!(target instanceof Element)) return;`. The cast asserts exactly what the next line checks,
and the `| null` it adds is a case the guard rejects anyway, so it reads as though it were
load-bearing.

**Suggested fix:** `const target = e.target;` — `instanceof Element` narrows `EventTarget` on its
own and the rest of the handler is unchanged.

### 560. [LOW] The editor's click-target fill hangs off an unclassed Lexical div
`portal/src/styles/index.css:53` — `.mdxeditor-root-contenteditable > div:first-child` targets a
wrapper Lexical renders with no class of its own. An MDXEditor version that inserts another
element there breaks the flex chain silently: the dead strip under the last line comes back, with
no error and no failing test. `handleChromeMouseDown` still focuses the editor in that case, so
the feature degrades to "caret jumps to the end" rather than failing outright.

**Suggested fix:** decision needed. Leave it and rely on the documented fallback (preferred —
MDXEditor exposes no public class for that element, and the fallback is tested), or add a render
test asserting the contenteditable's parent chain, which pins the assumption at the cost of a
test that breaks on every MDXEditor upgrade.

### 592. [LOW] The Documents dialog's friendly fallback message never shows for API or network errors
`portal/src/components/estimates/DocumentsDialog.tsx:102` — The fallback shows only for an empty message, but `performApiRequest` always sets `Request failed (N)` and fetch sets "Failed to fetch", so users see raw text such as "Request failed (413)".

**Suggested fix:** Show the fallback for an `ApiError` with no parsed detail (`/^Request failed \(\d+\)$/`) and for a `TypeError`; otherwise keep `err.message`.

### 593. [LOW] The save-failure reason is hidden behind the Documents dialog
`portal/src/pages/NewEstimateWithActivityPage.tsx:563` — When the save before generation fails, the dialog shows a generic message and the real reason goes to `saveError`, rendered on the page behind the modal.

**Suggested fix:** Have `handleSaveEstimate` return or throw the reason, and include it: `Your changes couldn't be saved (${reason}), so no document was generated.`

### 594. [LOW] A comment claims an ordering requirement the Documents dialog doesn't need
`portal/src/pages/NewEstimateWithActivityPage.tsx:571` — "setDocVersions must run before this resolves" — the dialog re-prefills from the resolved value and its reconciliation is correct in either order, so a maintainer could protect or rely on a requirement that doesn't exist.

**Suggested fix:** Reword: "The dialog re-prefills from the returned versions; the setDocVersions order here is not load-bearing."

### 595. [LOW] The portal still sends a `created_by` the server now ignores
`portal/src/pages/NewEstimateWithActivityPage.tsx:567` — Superseded in part on 2026-09-23: the platform now takes a version's author from the authenticated user and ignores the form field (it is still accepted so old tabs don't 422). The portal keeps sending `currentUserDisplayName || "portal-user"`, which is dead weight and misleading to read.

**Suggested fix:** Drop `createdBy` from `GenerateDocInput` and the page call; keep the server accepting-and-ignoring the field for a release, then remove it.

### 596. [LOW] `getEntityId(estimate) ?? ""` is dead code on the Documents button
`portal/src/pages/NewEstimateWithActivityPage.tsx:1037` — `getEntityId` returns `string`, so `?? ""` never applies; an empty id would silently break every thumbnail URL. Nothing tests this or the `isEditMode` gate.

**Suggested fix:** Pass the route `estimateId` (or `getEntityId(estimate)` without the `??`), and render `EstimateDocuments` only when the id is non-empty.

### 597. [LOW] Over-cap image picks don't say which files were skipped
`portal/src/components/estimates/useStagedImages.ts:40` — The loop `break`s on a generic "at most 10 images" message: dropped files aren't named, and later wrong-type or oversize files are never checked or reported.

**Suggested fix:** Don't break; collect the overflow names and report once: `Only 10 images fit; skipped a.jpg, b.jpg.`

### 598. [LOW] Image pick errors stay on screen after they stop being true
`portal/src/components/estimates/useStagedImages.ts:45` — The error is cleared only on the next add or submit, so "at most 10 images" stays up after the user frees a slot.

**Suggested fix:** Clear the error in unstage and in the kept-image remove handler.

### 635. ~~[MEDIUM] A notes refresh wipes a note the user just created~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** `useNotes` tracks the fetch in flight; a local create, delete, edit or attachment change while one is pending starts a fresh fetch that supersedes it (`supersedeInFlight`), so the older answer can't undo the change and the feed still picks up what Maple filed. The fresh fetch keeps the kind of the one it supersedes, so a superseded parent-switch load still clears on failure (review round 1), and it always runs the newest `load` (`loadRef`): a change that finishes after a record switch fetches the record on screen, never the one it was clicked on (review round 2). Tests: `tests/useNotes.test.tsx` › local changes during a refresh (create; delete), "a superseded parent-switch load still clears on failure", and "a note change that finishes after a parent switch never reloads the old parent".

`portal/src/hooks/useNotes.ts:84` — When Maple files a note, `refreshKey` bumps and a fetch starts. If the user creates their own note before it lands, `createNote` prepends it and then the older fetch replaces the list without it. A probe went from ['created'] to []; in the partial-upload retry path `notes.find(pendingId)` then finds nothing.

**Suggested fix:** After any local change to the list (create, delete, replace), start a fresh `load` (or bump the sequence), so the stale response is superseded. Add a test.

*(Review 2026-09-24 fourth pass #22.)*

### 638. [LOW] The note-only badge refresh isn't actually note-only, and `loadNoteCounts` is unguarded
`portal/src/pages/NewEstimateWithActivityPage.tsx:562` — A note event calls `loadNoteCounts` twice (lines 564 and 571); a non-note event still calls it once via line 571 or the deferred flush. `loadNoteCounts` has no sequence or estimate guard, so A's counts can land on B.

**Suggested fix:** Call it once and only for note operations (skip at 571 when 564 ran); add a sequence and estimateId guard.

*(Review 2026-09-24 fourth pass #25.)*

### 639. [LOW] Enabling the hook with a changed refresh key fetches twice
`portal/src/hooks/useNotes.ts:136` — A `refreshKey` change while disabled isn't recorded as seen, so enabling fetches from both effects. It can't happen today (NotesPanel never passes `enabled`).

**Suggested fix:** Record `seenRefreshKeyRef.current = refreshKey` in the main load effect too.

*(Review 2026-09-24 fourth pass #26.)*

### 640. [LOW] A Maple change during the first load is dropped
`portal/src/pages/NewEstimateWithActivityPage.tsx:557` — While `loadedIdRef` is null, a matching event is ignored outright rather than deferred. If the first GET was answered before Maple's write was saved, the page shows stale data until something else reloads it.

**Suggested fix:** When the event matches by `_id`/`id` during the first load, set `pendingMapleReloadRef`, and flush once the first load applies.

*(Review 2026-09-24 fourth pass #27.)*

### 641. [LOW] A write finishing after the page closed still fires a reload
`portal/src/pages/NewEstimateWithActivityPage.tsx:514` — `trackWrite`'s `finally` calls `flushRef.current()`, and the flush has no `aliveRef` check, so a pending reload fires a wasted GET plus `loadNoteCounts` (setState after unmount).

**Suggested fix:** Add `if (!aliveRef.current) return;` at the top of `flushDeferredMapleReload`.

*(Review 2026-09-24 fourth pass #28.)*

### 651. [MEDIUM] The Delete Document Version dialog survives a switch to another estimate
`portal/src/pages/NewEstimateWithActivityPage.tsx:486` — The estimateId reset clears `deletingWorkItemIndex` but not `isDeleteDocOpen`, `docVersionToDelete` or `isDeleteOpen`. If the dialog "Delete Estimate V{n}" is open when the user goes Back/Forward to another estimate and confirms, `handleDeleteDocVersion` deletes version n of the NEW estimate (`getEntityId(estimate)` is B, the version is A's). Suspected from code reading. Graded MEDIUM rather than HIGH because it needs in-page navigation while a modal is open.

**Suggested fix:** In the reset effect, also call `setIsDeleteDocOpen(false)`, `setDocVersionToDelete(null)`, `setIsDeleteOpen(false)`, `setStatusAlert(null)`, `setMaterialGap(null)` and `setRoleGaps(null)`. Better still, store the estimate id with `docVersionToDelete` and refuse when it differs. Add a test.

*(Review 2026-09-25 fifth pass #20.)*

### 655. ~~[MEDIUM] A failed refresh empties the feed and loses a note edit in progress~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** `load` takes a `refresh` flag (the refresh key and the manual reload set it). A failed refresh keeps the list and shows the error; only a failed load after a parent switch clears it, as before. A card being edited stays mounted and the badge keeps its count. Tests: `tests/useNotes.test.tsx` › refresh failure (refresh key; manual reload); the parent-switch clearing test is unchanged.

`portal/src/hooks/useNotes.ts:103` — The `catch` clears notes on every failure. That was meant for a parent switch, but it now also runs on a Maple-triggered refetch of the same parent. Verified: `['n1']` → `[]` with the error "offline". Each `NoteCard` holds its edit composer in local state (NoteCard.tsx:61), so a card being edited unmounts and the typed text is lost. `onCountChange(0)` also resets the badge.

**Suggested fix:** Pass a `refresh` flag to `load` and only `setNotes([])` when the parent changed. On a refresh failure keep the list and set `error` (or a light "couldn't refresh" message). Add a test.

*(Review 2026-09-25 fifth pass #24.)*

### 660. [LOW] Every Maple reload refetches the company's full property and contact lists
`portal/src/pages/NewEstimateWithActivityPage.tsx:410` — `loadEstimate(true)` reuses the first-load `Promise.all`, so each Maple change to the estimate costs three GETs plus `notesApi.counts`, and two of them are lists that didn't change.

**Suggested fix:** When `fromMaple` is true, call only `estimatesApi.get`.

*(Review 2026-09-25 fifth pass #30.)*

### 811. [LOW] A note created on one record can be prepended to the next record's list
`portal/src/hooks/useNotes.ts:189` — `createNote` awaits `notesApi.create`, then always prepends the created note. Switch from property A to B while the create is saving: if B's load has already landed, A's new note is added to the top of B's list, and nothing replaces it until B is next fetched (a Maple refresh, a reload or a revisit). If B's load is still in flight, `supersedeInFlight` fetches B and the stray note is replaced. LOW: it predates the notes-feed batch (#635/#654/#655), it's display only and same-company, and it needs a switch during the create's round trip. (review 2026-10-04, notes-feed batch round 3 #1)

**Suggested fix (decided 2026-10-04, user):** fix the cause, not this one race. The hook survives a record switch (the detail panes are reconciled in place), so every async step can land on the wrong record; three review rounds in a row found narrower versions of that. Key the notes panel by its parent — `<NotesPanel key={`${parentType}:${parentId}:${workItemId ?? ""}`} …/>` wherever it renders — so a switch mounts a fresh hook and the old one's late responses are dropped by its own unmounted guard. That closes this finding and the whole class, and lets the defensive code (the parent-switch clearing in `load`, `loadRef`) be simplified afterwards. Cost: an open note draft is discarded on a switch. Test: create on A with `create` pending, switch to B, resolve → B's list unchanged. (The narrower alternative — compare the parent in `createNote` before prepending — was considered and not chosen.)

## Portal — layout, navigation and Maple panel

### 118. [MEDIUM] Hand-rolled `import.meta` cast in widget API client

**Deferred 2026-10-04 (user):** left for a website session — the repo had no `node_modules`, and the user chose not to install them in this batch.
**File**: [website/widget/api.ts:25-27](../../website/widget/api.ts)
**Severity**: MEDIUM (DX)

`(import.meta as { env?: ... }).env?.VITE_PUBLIC_API_URL` works but
exists because the website project doesn't pull in Vite's client
types. Every future env-var lookup in the widget will repeat the cast.

Fix: add a one-line `website/widget/vite-env.d.ts` containing
`/// <reference types="vite/client" />`. Drop the cast and read
`import.meta.env.VITE_PUBLIC_API_URL` directly.

### 289. [MEDIUM] `useEffect` references function declared later in the same component
**Where:** `portal/src/pages/MaterialsPage.tsx` and `portal/src/pages/PeoplePage.tsx` — the `?open=<id>` effect calls `openEditMaterial` / `openEditLabour` declared further down. (Note: this was originally flagged when those effects opened the edit modal; the modal logic has since been removed, so the *symptom* is gone — but the pattern of effect-before-declaration may still apply if either page picks up a similar handler later.)

**Issue:** Works at runtime because effects fire after the component body finishes evaluating, but it's brittle, future-hostile, and would silently fail eslint's `react-hooks/exhaustive-deps` rule.

**Fix:** When adding any new effect in those files, declare its dependencies above the effect, or wrap helpers in `useCallback`.

### 388. [MEDIUM] portal/src/components/common/SupportPanel.tsx — errored Firestore listeners stay dead until panel reopen
Found during 2026-07-01 manual dev testing: `onSnapshot` terminates permanently on `permission-denied` (no retry). A listener that errors during a transient misconfiguration leaves the panel empty — with no visible error — until the user switches tabs or refreshes. Reopening the panel re-attaches (effect on `[open, conversationId]`), so the blast radius is one stale view, but users won't know to do it.
**Suggested fix:** Surface an error state in the panel when a listener errors ("Couldn't load messages — Retry") whose retry re-runs the subscribe effect; same for the layout-level badge listener.

### 408. [MEDIUM] portal/src/components/dashboard/UpcomingTasksCard.tsx:38 — completed tasks surface in "Upcoming Tasks"
The card lists tasks from every status column, including the terminal "Done" status. A finished task whose due date has passed will sit at the top of the card in red indefinitely, crowding out genuinely actionable tasks (the card only shows 5). Deferred pending a product decision on whether "Done" tasks belong in the card.
**Suggested fix:** Fetch task statuses (taskStatusesApi.list), identify the final status column, and exclude tasks in it — or filter in selectDashboardTasks via a passed-in "done" status id.

### 112. [LOW] Replace `isMountedRef`/`fetchTokenRef` race-guards with `AbortController`
**Files**: [portal/src/components/common/ChangeLogPanel.tsx](../../portal/src/components/common/ChangeLogPanel.tsx), [portal/src/components/common/FeedbackPanel.tsx](../../portal/src/components/common/FeedbackPanel.tsx), [portal/src/api/client.ts](../../portal/src/api/client.ts)
**Severity**: LOW (refactor)

Both panels copy a manual race-guard pattern (`isMountedRef`,
`submitTokenRef` / `fetchTokenRef`, post-await staleness checks) to drop
results from superseded fetches. The cleaner shape is `AbortController`
+ `signal`, but it requires changing the shared API client.

Fix:
1. Teach `apiRequest` in `portal/src/api/client.ts` to accept an
   `AbortSignal` and pass it through to `fetch`.
2. Migrate `ChangeLogPanel` and `FeedbackPanel` together — abort the
   in-flight request on unmount or on a new submit/fetch, then drop the
   ref-based guards.

Migrate both call sites in the same PR so the pattern is consistent.

### 119. [LOW] URL build via string concatenation in widget API client
**File**: [website/widget/api.ts:36](../../website/widget/api.ts)
**Severity**: LOW (robustness)

`resolveApiUrl().replace(/\/+$/, "") + "/public/maple/ask"` hand-rolls
the join. A misconfigured env (e.g. trailing whitespace, missing
scheme, accidental query string) builds a broken URL silently.

Fix: use `new URL("/public/maple/ask", base)`. Surface a clear error
if the base is malformed.

### 121. [LOW] Implicit "welcome bubble has id 0" coupling
**Files**: [website/widget/MapleWidget.tsx:31, 69, 108](../../website/widget/MapleWidget.tsx)
**Severity**: LOW (style)

The widget treats the welcome bubble specially in two unrelated places:
- Line 69: `bubbles.filter((b) => b.id !== 0)` — strip the welcome
  before building the API history.
- Line 108: `showStarterChips = bubbles.length === 1 && !pending` —
  show starter chips only on initial state.

Both rely on the convention that the welcome bubble has id 0 and is
the only bubble at start. A rename / re-numbering would have to touch
both spots.

Fix: tag the welcome bubble with a flag (`isWelcome: true`) on the
`Bubble` type, or move the welcome state into a separate variable
outside the `bubbles` array.

### 356. [LOW] portal/src/lib/orchestratorReply.ts:80 — combine can stack two questions on distinct question-bearing refusals
When `response` and `clarifying_question` are distinct and neither contains the
other, the result is `${response}\n\n${question}`. For the illegal-status-transition
refusal — whose `response` already ends in its own question ("…want me to do one of
those instead?") and whose `clarifying_question` is "Which status would you like
instead?" — the reply shows two stacked questions. Cosmetic; context is preserved
(the point of the change), and it's a deliberate, documented tradeoff.
**Suggested fix:** Acceptable as-is. If the doubling reads poorly in practice,
refine backend-side (drop the redundant clarifying_question on flows whose
`response` is already self-contained) rather than adding heuristics in the portal.

### 357. [LOW] portal/src/lib/orchestratorReply.ts:74 — substring dedup could over-collapse a degenerate short question
`context.includes(question)` / `question.includes(context)` dedup on raw substring.
If a `clarifying_question` were a short fragment that happens to appear mid-sentence
in `response` (e.g. question "name" inside "Add a name."), the shorter field is
dropped. In practice clarifying_question is always a full prompt sentence, so the
risk is negligible.
**Suggested fix:** Acceptable as-is. If hardening is wanted, compare on a
sentence/boundary basis or only dedup when one string fully equals a trimmed line
of the other. Not worth the complexity now.

### 369. [LOW] portal/src/components/ui/InfoTooltip.tsx:78 — position clamped horizontally but not vertically
The portaled bubble always opens below the trigger (`top = triggerRect.bottom + 6`) and clamps only
`left` to the viewport width. A field near the bottom of a short viewport can push the tooltip off
the bottom edge — there is no flip-to-above or bottom clamp. Low impact: the Financial fields sit
high in the card and the bubble is short, so it's unlikely in practice.
**Suggested fix:** Optional — if the bubble would exceed `innerHeight - margin`, flip above the
trigger (`top = triggerRect.top - bubbleHeight - gap`), or accept it (closing on scroll already
limits the stale-position window).

### 389. [LOW] portal/src/components/Layout/AiPanel.tsx — confirm dialog backdrop is full-viewport, unlike Support's panel-scoped one
The Maple confirm uses `fixed inset-0` so its dark backdrop dims the entire app, whereas the Support confirm uses `absolute inset-0` and dims only the panel. Functionally identical; rendering once at the fragment level was a deliberate choice to avoid duplicating it across the mobile+desktop asides.
**Suggested fix:** Accept the full-screen backdrop (common modal pattern), or scope it to the panel by rendering the dialog inside each aside's relative container like SupportPanel does.

### 390. [LOW] portal/src/components/common/SupportPanel.tsx — draft/attachment cleared on message-type dropdown switch, not only tab switch
The resolve-conversation effect (deps `[open, activeTab, activeType]`) clears draft + pendingFile on every `activeType` change, so switching the Feedback/Support dropdown mid-compose discards a half-typed message. Reasonable (separate conversation per type) but recorded as a behavior.
**Suggested fix:** Accept, or preserve the draft across dropdown switches by keying the draft-clear on `activeTab` only.

### 391. [LOW] portal/src/components/Layout/PortalLayout.tsx:147 — flag-off environments now have NO in-app feedback entry point
The Support tab is still gated on `supportEnabled` (VITE_SUPPORT_PANEL_ENABLED), and the Trello Feedback tab — which was unconditional — is gone. In any build without the flag, the footer is just Maple | What's New: no way to contact support in-app at all. Prod has the flag on today, so no current impact — but the documented way to "turn the panel off" (empty the GitHub var + rebuild) now has a much bigger blast radius than before: it silently removes the only contact channel, not just a beta feature. The flag has effectively changed meaning from rollout gate to kill switch.
**Suggested fix:** Either accept (flag stays permanently on) and note the kill-switch semantics in the workflow comment next to VITE_SUPPORT_PANEL_ENABLED — or drop the flag gating entirely now that Support is the production channel (remove isSupportPanelEnabled and render unconditionally).

### 393. [LOW] portal/src/components/common/SupportPanel.tsx:156 — App Check gate covers only the message/doc listener
The `waitForAppCheckReady()` gate is applied to `subscribeToMessages` + `subscribeToConversationDoc` (the important one), but the panel's `subscribeToLiveAvailability` (SupportPanel.tsx:156) and the layout badge's `subscribeToUserConversations` (useSupportUnread.ts:37, gated on `waitForAuthReady` but NOT `waitForAppCheckReady`) attach without an App Check token primed. With enforcement on, a permission-denied on their first onSnapshot kills them permanently too (no auto-retry) — the same bug class the gate was added to fix. Impact is lower for these two: both have a REST fallback (getLiveAvailability seed for the pill; getUnread seed for the badge), so a dead listener degrades to "stale until refresh" rather than an empty transcript. That's why targeting the message listener first is reasonable — but the fix is incomplete for consistency.
**Suggested fix:** Gate the availability effect's `subscribeToLiveAvailability` and the `subscribeToUserConversations` call in useSupportUnread on `waitForAppCheckReady` too (await it before attaching, same cancelled-flag pattern). Or, if the REST fallbacks are deemed sufficient for those two, add a one-line comment on each noting the deliberate choice so the asymmetry reads as intentional.

### 417. [LOW] portal/src/components/dashboard/UpcomingTasksCard.tsx:53 — "Current User" filter silently shows all tasks when no stored email
`loadTasks` falls back to an unfiltered fetch when `getCurrentUser()?.email` is
missing, while the select still displays "Current User" — the UI then
misrepresents what the list contains. The fallback is deliberate (commented)
and the no-email state should be rare, so impact is minimal.
**Suggested fix:** If the stored user has no email, hide the filter select or
force the value to "all" so the label matches the data.

### 464. [LOW] portal/src/pages/auth/LoginPage.tsx:303 — dismissBanner discards a still-valid resend token
`dismissBanner` clears `resendToken` along with the banner, so a user who closes it to re-read
the form cannot get the resend back without submitting the whole login again, though the
captured token is good for the best part of an hour.

**Suggested fix:** either leave `resendToken` alone (it is already cleared at the top of
`handleSubmit` and on the success/409 paths), or — better — surface the affordance outside the
banner so dismissing the message does not dismiss the remedy.

### 520. [LOW] portal/src/components/tours/TourCallout.tsx:159 — outside-click handlers bound to mousedown/pointerdown still fire through the overlay
The tour's blocking overlay only handles `click`. At least six components dismiss themselves
from `document.addEventListener("mousedown", ...)` or `"pointerdown"` — `TaskFilterButton.tsx:55`,
`TaskActionsMenu.tsx:43`, `EstimateTitleBar.tsx:94` and `:110`, `TemplatesTab.tsx:425`,
`InfoTooltip.tsx:106` — and those events fire before `click` and are a different event type, so
the overlay's `stopPropagation` on the click never sees them. Clicking the overlay while one of
those menus is open closes it. LOW because the only observable effect is a dropdown dismissing,
which is harmless and arguably what a user expects; nothing destructive is bound to those events.

**Suggested fix:** if the block should be airtight, add matching `onMouseDownCapture` and
`onPointerDownCapture` handlers to the overlay that also call `stopPropagation`. The reviewing
recommendation was to leave it as-is — the behavior is benign, and three handlers where one
reads clearly is the worse trade. Recorded so the gap stays a known choice rather than an
oversight.

### 661. [LOW] A confirmation question fires `estimates:changed`
`portal/src/components/Layout/agentMutationEvents.ts:103` — Results such as `{"operation": "update_estimate", "missing_fields": ["confirmation"]}` (edit_executor.py:419/471) change nothing but still reload the page. If the page is blocked, they leave a reload waiting.

**Suggested fix:** Skip the dispatch when `agentResult.needs_clarification` is true or `result.missing_fields` is non-empty. Add a test.

*(Review 2026-09-25 fifth pass #31.)*

### 733. ~~[MEDIUM] A successful quiet reload never clears an earlier load error~~ — RESOLVED 2026-10-03

**Resolved 2026-10-03:** `DashboardPage`'s loader clears the error after every successful load, quiet or not, as TasksPage does; a Maple-triggered reload now lifts the error screen. Test: `tests/DashboardPage.test.tsx` — "a successful reload after a failed first load leaves the error screen". The shared quiet-load helper this entry suggested was not extracted: the five loaders differ (one is an effect keyed on a reload token), and the fix is one line each.

`portal/src/pages/DashboardPage.tsx:84` — Same defect as #728 in the dashboard list loader (81-108); the page stays on the error state (235). (review 2026-09-27 #63)

**Suggested fix:** Clear the error after a successful load regardless of `quiet`. Consider one shared quiet-load helper, since the pattern is now pasted six times.

### 734. ~~[MEDIUM] The question-strip Cancel button takes focus off the composer~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** The question strip's Cancel has `onMouseDown={keepComposerFocus}`, like the composer's other controls. Test: `tests/AiPanel.test.tsx` › "pressing Cancel keeps focus in the composer".

`portal/src/components/Layout/AiPanel.tsx:435` — The button has no `onMouseDown={keepComposerFocus}`, against the file's own rule (336-347). On a phone, blur brings the tab bar back (PortalLayout 426), lifting the composer about 64px between press and click, so the tap misses. The strip appears right after a reply, when the textarea has just been refocused. (review 2026-09-27 #64)

**Suggested fix:** Add `onMouseDown={keepComposerFocus}`, as the other composer controls do.

### 735. ~~[MEDIUM] Cancel doesn't stop a pending voice auto-send~~ — RESOLVED 2026-10-04

**Resolved 2026-10-04:** Cancel calls `cancelAutoSend()` before `onCancelQuestion`, so a counting-down voice transcript no longer sends itself after the cancel turn. Test: `tests/AiPanelVoice.test.tsx` › "cancelling the open question aborts the auto-send".

`portal/src/components/Layout/AiPanel.tsx:437` — `onClick={() => onCancelQuestion?.()}` bypasses `cancelAutoSend()`. If a voice transcript is counting down ("Sending in 3…"), it can still fire after the "cancel" turn — the double-send `submitDirectMessageCancellingAutoSend` (187-190) exists to prevent. (review 2026-09-27 #65)

**Suggested fix:** `onClick={() => { cancelAutoSend(); onCancelQuestion?.(); }}`.

### 753. [LOW] A failed analytics refetch after a Maple write shows $0
`portal/src/pages/DashboardPage.tsx:145` — The analytics effects now re-run on `reloadToken`, and on failure they `setDivisionAnalytics(null)` / `setStatusAnalytics(null)` (145, 160), so the headline cards read 0, contradicting the "every card reload quietly" comment. (review 2026-09-27 #83)

**Suggested fix:** On a reload (`reloadToken > 0`), keep the previous analytics when the fetch fails.

### 754. [LOW] A reload can return the numbers from before the write
`portal/src/pages/DashboardPage.tsx:117` — `fetchAnalytics` reuses an in-flight promise for the same period, so a `reloadToken` bump that lands while the mount fetch is still in flight gets pre-write data. (review 2026-09-27 #84)

**Suggested fix:** Bypass the in-flight map when the fetch is triggered by a reload.

### 755. [LOW] The list reload has no `cancelled` guard
`portal/src/pages/DashboardPage.tsx:81` — Unlike its neighbours (139, 154), the main list effect doesn't cancel on re-run, so an older response can land after a newer one. (review 2026-09-27 #85)

**Suggested fix:** Add the same `let cancelled = false` / cleanup guard.

### 756. [LOW] A restored `open_question` can overwrite the result of a turn that already finished
`portal/src/components/Layout/useMapleAgent.ts:307` — `setOpenQuestion((current) => current ?? waiting)` can't tell "never set" from "the last reply closed it". Answer "yes" before a slow restore lands: the POST reply sets null, then the older GET sets `{kind:"yes_no"}`, and the strip shows "Waiting for your answer" with nothing open. (review 2026-09-27 #86)

**Suggested fix:** Set a ref when any local turn completes, and skip the restored `open_question` once it is set.

## Portal — settings, billing, onboarding and ops

### 206. [MEDIUM] Generalize `PlanPickerGrid` button label
**File**: `portal/src/components/billing/PlanPickerGrid.tsx:140-145`
**Severity**: MEDIUM

`buttonLabel` is hardcoded to "Select Free Plan" for any selectable plan. The day Base or Pro flips `selectableAtLaunch: true`, every button reads "Select Free Plan."

Fix: ``Select ${plan.displayLabel} Plan`` — or just "Select plan" if displayLabel feels redundant.

### 210. [MEDIUM] `PlanStep` should disable the grid when `companyId` is null
**File**: `portal/src/components/onboarding/PlanStep.tsx:18-33`
**Severity**: MEDIUM

If `companyId` is null when the user clicks Select, they see "Missing company context. Please reload and try again." But by step 6, the company was created in step 1 — a missing companyId here is a code-flow bug, not a user-recoverable state. Telling the user to reload is unhelpful.

Fix: pass a `disabled` prop down to `PlanPickerGrid` when `!companyId`. Render an inline "Initializing your account…" notice instead of letting the user click and fail.

### 82. [LOW] `alert(...)` for save errors in 3 settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx) (`handleSaveDivision`),
[portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx) (`handleSaveUnit`),
[portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx) (`handleSaveCategory`)
**Severity**: LOW (UX inconsistency)

The save handlers surface API errors via browser `alert(...)`. The delete
flows in the same files render an inline error inside the modal instead.
Pattern was preserved verbatim from the pre-extraction `SettingsPage.tsx`
during the 2026-04-26 #63 fix — pre-existing, not introduced.

Fix: lift the error into a `formError` state inside the dialog, displayed
above the action buttons. Consistent with the delete-modal pattern in the
same files. Theme-adjacent to entry #44.

### 213. [LOW] Pluralize plan summary copy
**File**: `portal/src/components/onboarding/CompletionStep.tsx:23`
**Severity**: LOW

"Up to 3 team members" / "Up to 20 new estimates per month" hardcodes plural. A future plan with `includedSeats: 1` would read "Up to 1 team members."

Fix: `${n === 1 ? "team member" : "team members"}` — same for estimates.

### 214. [LOW] Map raw Stripe `subscription_status` to friendly labels in BillingTab
**File**: `portal/src/components/settings/BillingTab.tsx:104-107`
**Severity**: LOW

`state.stripe_subscription_status` is rendered as-is. Values like `incomplete_expired`, `past_due`, `trialing` show literally with underscores — cosmetic but user-facing.

Fix: small `STATUS_LABELS` map: `active → "Active"`, `past_due → "Past Due"`, `trialing → "Trialing"`, `incomplete → "Incomplete"`, `incomplete_expired → "Setup Expired"`, `canceled → "Canceled"`, `unpaid → "Unpaid"`.

### 399. [LOW] portal/src/pages/ops/OpsStaffPage.tsx — no per-row pending map
Row actions share a single pending/loading flag; if parallel edits across rows ever matter, switch to a per-row pending map so one in-flight action doesn't disable controls on unrelated rows.

### 421. [LOW] portal/src/components/settings/BillingTab.tsx:133 — "0 / 0" Tasks row during mixed-version deploys
If the portal deploys before the platform, subscription responses lack
`used_tasks`/`included_tasks`; strict `=== null` (correctly) refuses to treat
`undefined` as unlimited, so the Tasks row renders "0 / 0" until the backend
ships. Transient and flag-gated.
**Suggested fix:** Optionally skip the row when `state.included_tasks ===
undefined`, or deploy platform before (or together with) portal.

### 538. [LOW] portal/src/components/onboarding/CompanyStep.tsx:549 — the same setting has two names

Onboarding collects this field as "Standard Unbillable (%)" while Settings → Financial now labels
it "Unbillable Time". A user sets one during setup and later hunts for it under a different name.
The mismatch predates the rename but the rename widened it, and the glossary in
`platform/user_guides/users_guide.md` still says "Standard Unbillable %" — so Maple will name the
field differently again if asked.

**Suggested fix:** align the onboarding label and the guide glossary entry to "Unbillable Time".
Deferred deliberately: it touches onboarding wizard copy outside the scope of the Markup change,
and will be resolved as part of the planned onboarding-flow overhaul.

### 732. [MEDIUM] A successful quiet reload never clears an earlier load error
`portal/src/components/settings/TemplatesTab.tsx:50` — Same defect as #728 in the templates loader (49-62); the tab stays on `<ErrorState>` (183). (review 2026-09-27 #62)

**Suggested fix:** Clear the error after a successful load regardless of `quiet`.

## Portal — tasks, properties, contacts and materials

### 494. [MEDIUM] portal/src/pages/EquipmentsPage.tsx:166 — plan committed to including EquipmentsPage; it was skipped, and naive inclusion would break saves
The approved sparse-writes plan's Step 5 lists EquipmentsPage "for consistency", but it still
sends the whole object. Note the trap: the equipments *router* still binds the full
`Equipment` document (it was outside the 7-resource backend scope), so wiring `diffPayload`
into the page alone would 422 on missing required fields. The skip was correct in effect but
is an undocumented deviation from the approved plan.
**Suggested fix:** either (a) extend the backend treatment to `routers/equipments.py` (an
`UpdateEquipmentRequest` DTO + `build_patch`/`finalize`, same recipe) and then wire the page —
consistent, ~30 min; or (b) drop EquipmentsPage from the plan doc explicitly. Option (a)
preferred: Equipment is a catalog resource identical in shape to Material/Labour, and leaving
one full-bind PUT invites the old bug class back.

### 72. [LOW] `getCategoryName` / `getUnitName` re-allocated each render
**File**: [portal/src/pages/MaterialsPage.tsx:183-193](../../portal/src/pages/MaterialsPage.tsx)
**Severity**: LOW (pre-existing pattern; not introduced by the
configurable-units change)

Both helpers are defined in the component body, so they're new function
references on every render. No memoized child currently depends on
referential equality, so this is purely cosmetic — flagging only because
the same lookup pattern shows up across `MaterialsPage`,
`AddMaterialGapDialog`, and the (eventual) inventory drawer. A shared
`useMemo`-wrapped lookup hook would centralise the cache.

### 188. [LOW] Contact deep-link still renders when contact name is empty
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx:1094-1101](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW (UX)

When `selectedPropertyContact` resolves but both `first_name` and
`last_name` are empty/whitespace, `.trim() || "-"` falls back to
literal `"-"`, but the surrounding `<Link>` still renders. Users see a
clickable hyphen with no context. Accessibility is fine
(`title="View contact details"` provides hover text), but the
affordance is weak.

Fix options:
- Gate the `<Link>` on a non-empty trimmed name, falling back to the
  plain `<span>"-"</span>` branch.
- Substitute a descriptive fallback like `"Unnamed contact"` so the
  link target is meaningful.

Same pattern likely worth checking in any other card that renders
contact-name-or-dash next to a deep link.

### 340. [LOW] `alert()` used for the skipped-in-use report after reload
`MaterialCategoriesTab.tsx` / `MaterialUnitsTab.tsx` surface skipped in-use
items via browser `alert()` — consistent with the tabs' existing error
handling, but the weakest UX in the flow. Fix: inline banner or toast; natural
to do together with #337.

### 407. [LOW] portal/src/pages/PropertiesPage.tsx:714 — uploading the unmodified template creates real sample contacts
The property upload endpoint resolves contact1–contact5 by name and creates a contact when no match exists (platform/routers/properties.py:189). A user who uploads the sample template as-is gets a real "John Smith" / "Jane Doe" contact in their tenant. Pre-existing behavior for the onboarding sample; informational — sample files are meant to be edited before upload.
**Suggested fix:** Optional: use obviously-placeholder contact names in sample rows (e.g. "Contact Name 1"), or leave as-is.

### 411. [LOW] portal/src/pages/TasksPage.tsx — moveError now carries archive failures too
handleArchive reports through the moveError state; the name no longer describes its role as the page's generic inline action alert, which invites misuse or confusion on the next edit.
**Suggested fix:** Rename to actionError (state + setter + alert usage) on the next touch of this file.

### 420. [LOW] portal/src/pages/TasksPage.tsx:296 — gate not refreshed after convert-with-delete
`refreshSubscription()` runs after create and delete, but a convert-to-estimate
that deletes the source task also frees a slot. Until the page remounts, the
client-side gate can over-block (shows the limit dialog one click too long).
The backend 409 remains authoritative either way.
**Suggested fix:** Call `refreshSubscription()` from the ConvertTaskDialog
success/close path, same as `handleDelete`.

### 473. [LOW] portal/src/components/properties/PropertyActivityPanel.tsx:152 — panel cache grows unbounded for the session
Entries accumulate per property x tab x filter combination and are only ever cleared
wholesale by the mutation event. A long session across many properties retains every
result set.
**Suggested fix:** cap it (a small LRU, or evict entries for other properties when
`propertyId` changes).

### 474. [LOW] portal/src/components/common/StatusFilterDropdown.tsx:186 — reposition runs setState on every scroll event
The scroll listener is registered with `capture: true` and calls `setPosition` on each
event, re-rendering the menu for every scroll frame while it is open.
**Suggested fix:** throttle with `requestAnimationFrame`, or close the menu on scroll.

### 475. ~~[LOW] portal/src/pages/TasksPage.tsx:199 — taskId param never clears when the list is empty~~ — RESOLVED 2026-09-28
Resolved: the deep-link effect now waits on `isLoading` rather than the row count, and clears
`open`/`taskId` whatever the list holds (a task it lacks is fetched by id). Pinned by
`tests/TasksPageDeepLink.test.tsx` ("the param clears even when the filtered list is empty").

The effect returns early when `tasks.length === 0`, so `?taskId=` stays in the URL when
the filtered list has no rows. A later filter change that produces rows can then open a
dialog the user did not ask for.
**Suggested fix:** clear the param whenever `requestedTaskId` is set and loading has
completed, independent of the row count.

### 556. [LOW] portal/src/components/notes/NoteBody.tsx:56 — scroll handler reads layout on every event

`sync` reads `scrollHeight`, `clientHeight` and `scrollTop` on every scroll event. In practice this
is cheap — scroll events already fire about once per frame, nothing is dirtying style at that
moment, and the functional `setEdges` bails when the answer is unchanged — which is why it is LOW
rather than a performance defect. It is still an unguarded forced-layout read in a hot path.

**Suggested fix:** coalesce with `requestAnimationFrame` — keep the pending frame id in a ref, skip
if one is already scheduled, clear it in the callback, and cancel it in the existing effect cleanup.

### 728. ~~[MEDIUM] A successful quiet reload never clears an earlier load error~~ — RESOLVED 2026-10-03

**Resolved 2026-10-03:** `ContactsPage`'s loader clears the error after every successful load, quiet or not, as TasksPage does; a Maple-triggered reload now lifts the error screen. Test: `tests/ContactsPageDiffSave.test.tsx` — "a successful reload after a failed first load leaves the error screen".

`portal/src/pages/ContactsPage.tsx:251` — `setError("")` now runs only when `!quiet`. If the first load failed, the page shows `<ErrorState>` (671). A later Maple write triggers a quiet reload that succeeds, but the error stays and the page stays on the error screen. Before this diff, a Maple write reset the error and the page recovered. (review 2026-09-27 #58)

**Suggested fix:** Call `setError("")` after the successful `set*` calls in `try`, as TasksPage.tsx:151 does.

### 729. ~~[MEDIUM] A successful quiet reload never clears an earlier load error~~ — RESOLVED 2026-10-03

**Resolved 2026-10-03:** `MaterialsPage`'s loader clears the error after every successful load, quiet or not, as TasksPage does; a Maple-triggered reload now lifts the error screen. Test: `tests/MaterialsPageDiffSave.test.tsx` — "a successful reload after a failed first load leaves the error screen".

`portal/src/pages/MaterialsPage.tsx:121` — Same defect as #728 in the materials loader (120-134); the page stays on `<ErrorState>` (551) after a successful Maple-triggered reload. (review 2026-09-27 #59)

**Suggested fix:** Clear the error after a successful load regardless of `quiet`.

### 730. ~~[MEDIUM] A successful quiet reload never clears an earlier load error~~ — RESOLVED 2026-10-03

**Resolved 2026-10-03:** `PeoplePage`'s loader clears the error after every successful load, quiet or not, as TasksPage does; a Maple-triggered reload now lifts the error screen. Test: `tests/PeoplePageDiffSave.test.tsx` — "a successful reload after a failed first load leaves the error screen".

`portal/src/pages/PeoplePage.tsx:101` — Same defect as #728 in the roles loader (100-114); the page stays on `<ErrorState>` (335). (review 2026-09-27 #60)

**Suggested fix:** Clear the error after a successful load regardless of `quiet`.

### 731. ~~[MEDIUM] A successful quiet reload never clears an earlier load error~~ — RESOLVED 2026-10-03

**Resolved 2026-10-03:** `PropertiesPage`'s loader clears the error after every successful load, quiet or not, as TasksPage does; a Maple-triggered reload now lifts the error screen. Test: `tests/PropertiesPageMobileSheet.test.tsx` — "a successful reload after a failed first load leaves the error screen".

`portal/src/pages/PropertiesPage.tsx:125` — Same defect as #728 in the properties loader (122-156); the page stays on `<ErrorState>` (394). (review 2026-09-27 #61)

**Suggested fix:** Clear the error after a successful load regardless of `quiet`.

### 771. [LOW] A `?contactId=` link on a phone-sized screen lands on the list with no sheet
`portal/src/pages/ContactsPage.tsx:527` — following a contact link (from a property's sheet or an estimate) while stacked (a phone, or a desktop the Maple panel squeezes) selects and announces the contact to Maple, but shows the list, not its detail; `?open=` opens the sheet. Removing the param with `replace` also means Back from the next page lands on `/contacts` with the first row, as `?open=` already does. (review 2026-09-28 third round #11)

**Decision (user, 2026-09-28):** "when do we have link to a phone number? I don't think we need this case." — deferred. Note: the case is a contact link followed *on a phone-sized screen*, not a link to a phone number; confirm before closing.

**Suggested fix (if wanted):** open the sheet when stacked, as the `?open=` effect does (`if (isStacked) setIsDetailSheetOpen(true)`, gated on `isMeasured`).

### 772. [LOW] A `?propertyId=` link on a phone-sized screen lands on the list with no sheet
`portal/src/pages/PropertiesPage.tsx:307` — same as #771 for a property linked from a contact's sheet or an estimate. (review 2026-09-28 third round #12)

**Decision (user, 2026-09-28):** deferred with #771 (same note).

**Suggested fix (if wanted):** as #771.

## Website

### 226. [MEDIUM] `cm-waitlist` is used as both a CSS class and an element id
**File**: [website/public/contact-modal.js:138, 252](../../website/public/contact-modal.js)
**Severity**: MEDIUM

The wrapper `<div class="cm-waitlist">` shares the literal string
`cm-waitlist` with the `<input id="cm-waitlist">` it contains. CSS is
unaffected (class vs id selectors don't collide), and
`<label for="cm-waitlist">` correctly resolves to the input. But
anyone who later writes `document.getElementById('cm-waitlist')`
expecting the wrapper will instead get the checkbox — a quiet
footgun, not a current bug.

Fix: rename the wrapper class to `.cm-waitlist-block` (or rename the
id to `cm-join-waitlist`), update the matching CSS selectors, and
update the `<label for=…>` accordingly. ~5 line change. Roll into the
next contact-modal touch.

### 425. [MEDIUM] website/index.html — carousel CSS still inline (remainder of finding #8)
The carousel JS was extracted to `src/hero/hero-carousel.ts` in this pass, taking
index.html from 1486 back down to 1355 lines. The ~175 lines of `m3s-*` CSS are
still inline, so the file remains above the 800-line guideline. Extraction was
deliberately not attempted: the hero is the LCP element, and moving its CSS into
the Vite module graph means the stylesheet arrives via the JS chunk in dev,
producing a flash of unstyled hero on every dev reload. Production is unaffected
(Vite extracts a `<link>` at build time), so this is a dev-ergonomics trade-off
rather than a shipping problem.
**Suggested fix:** If the file length becomes a real maintenance problem, move
the `m3s-*` block to `src/styles/hero-carousel.css` and link it from `<head>`
directly (a plain `<link>`, not a JS-graph import) so there is no FOUC in either
environment.

### 454. [MEDIUM] website/contact-modal/install.js:297 — optional-field validation machinery is now inert
Removing the pre-launch waitlist checkbox removed the only code path that could ever mark an
optional field invalid. `optionalFieldWrappers` survives and is still iterated by
`clearAllFieldErrors()` (line 316) and the input-listener loop (line 319), but both are now
guaranteed no-ops — nothing can put a `cm-invalid` class on those controls. The five
`<div class="cm-field-error">Field is required</div>` nodes under each `data-optional-field`
wrapper are likewise unreachable markup. Line 370's
`const wrappersToValidate = baseRequiredWrappers` is a redundant alias left from the
conditional it replaced. None of this is a defect today; it is dead weight that will read as
intentional to the next person touching the form.

**Suggested fix:** either drop `optionalFieldWrappers`, the `data-optional-field` attributes
and the dead error divs; or keep them deliberately and add a one-line comment saying the
wrappers exist only so optional fields share the "clear error as you type" wiring. Inline
`wrappersToValidate` into the `forEach` either way.

### 455. [MEDIUM] website/functions/index.js:170 — server-side joinWaitlist path is now permanently dormant
The frontend no longer sends `joinWaitlist`, so `wantsWaitlist` is always false. Three
consequences, none breaking but all misleading: (a) the 400 branch at line 170 ("A message is
required when joining the pre-launch waitlist") is unreachable from the UI; (b) every ops
notification email now carries a constant `Pre-launch waitlist: No` row (line 265) — pure
noise on every submission; (c) `BREVO_PRELAUNCH_LIST_ID` is referenced at line 74 but can
never be appended to `listIds`, so the env var is dead config. Deliberately left in place
during the UI change because this is a deployed cloud function wired to live Brevo lists.

**Suggested fix:** decide whether the pre-launch list is retired for good. If so, remove the
field from the handler, drop the email row and the unreachable 400, and retire
`BREVO_PRELAUNCH_LIST_ID` from config and docs. Tests in `functions/joinWaitlist.test.js` and
`functions/brevoContactSync.test.js` cover this field and must move with it. If the list may
return, leave the backend alone and note it in the changelog.

### 480. [MEDIUM] website/src/seo/pageMeta.ts:30 — comment points at a build script that does not exist
The `OG_IMAGE` docstring says the card is "generated by `scripts/build-og-image.mjs`". That
file was never created — `scripts/` contains only `og-image-template.html` and
`verify-bundles.mjs`. The image was produced by driving the template through a browser by
hand at 1200x630 and exporting JPEG, so the one instruction pointing at how to regenerate it
is a dead reference and the asset is effectively unreproducible.
**Suggested fix:** write the script the comment promises (a short Playwright/Puppeteer
capture: load `scripts/og-image-template.html`, viewport 1200x630, screenshot to
`public/og/3maples-og-home.jpg` at quality ~90). The card will be regenerated whenever the
tagline or brand changes, and an undocumented manual step is one nobody repeats correctly.
Correcting the comment to describe the manual procedure is the cheaper alternative.

### 228. [LOW] `form.joinWaitlist.checked` relies on the named-elements collection
**File**: [website/public/contact-modal.js:331](../../website/public/contact-modal.js)
**Severity**: LOW

Works because HTML form elements are exposed by `name` on the form
object. If another element were ever added to this form with
`name="joinWaitlist"`, the lookup would return a `RadioNodeList` and
`.checked` would be `undefined`. The pattern matches the rest of the
file (`form.firstName.value` etc.), so this is consistent — just
inherited fragility.

Fix: optional. Switch to
`form.querySelector('#cm-waitlist').checked` (or use a captured
reference like the other inputs at module scope) for clarity. Skip if
you prefer to stay consistent with the existing style.

### 426. [LOW] website/public/screens/app-tasks.webp — placeholder copy visible in the capture
The tasks board screenshot shows "Test Task for scale" and "Task #10 / #11 / #13"
as task names. This is open item 1 on the supplied DEVELOPER-HANDOFF.md launch
checklist and reads as unfinished on a public landing page. Not fixable in code —
it needs a fresh capture of the Tasks board.
**Suggested fix:** Re-capture the Tasks board with realistic task names and drop
the new file in at the same path. The CSS crop is resolution-independent, so no
`--z` / `--cx` / `--cy` values need to change.

### 481. [LOW] website/404.html:8 — two conflicting robots metas in non-prod builds
The page hardcodes `<meta name="robots" content="noindex, follow">`, and in a non-production
build `seoSiteEnvPlugin` prepends `noindex, nofollow`. The built 404 page then carries two
robots directives. Crawlers resolve this by taking the most restrictive union, so behavior is
correct, but the output is confusing to read and the `follow` intent is silently overridden.
**Suggested fix:** skip the injection for `404.html` in
`seoSiteEnvPlugin.transformIndexHtml` — it is already `noindex` by its own tag on every
environment — keeping the page's declared `follow` semantics intact.

### 483. [LOW] website/src/seo/siteEnv.ts:95 — `renderSitemap` does not XML-escape `<loc>` values
Paths are interpolated straight into `<loc>`. Today every value comes from the hardcoded
`PAGE_META` list and contains no `&`, `<` or `>`, so the output is valid. It is a latent trap
rather than a live bug: the first page path with a query string or ampersand produces
malformed XML, and a malformed sitemap fails silently at Google rather than at build time.
**Suggested fix:** escape `&`, `<` and `>` when building the `<loc>` value, and add a case to
`robots-sitemap.test.ts` covering a path containing `&`.

### 485. [LOW] website/package.json:6 — no type gate covers the `src/seo/` modules
**Absorbs #433** (2026-09-20 consolidation): the same gap, first logged for
`widget/api.ts` / `MapleWidget.tsx` importing the untyped `lib/recaptchaClient.js`.
One decision covers both — add `typescript` + `tsconfig.json` + a `typecheck`
script wired into a pre-push hook, mirroring `portal/`, or accept the status quo.

The SEO work added three TypeScript source modules under `src/seo/` and five TypeScript test
files. The website project has no `tsconfig.json`, no `typecheck` script, and does not have
`typescript` installed — vite and vitest transpile `.ts` via esbuild, which strips types
without checking them, so type errors in these modules cannot be caught by anything in the
pipeline. Pre-existing (the widget, hero and analytics modules are already TS under the same
conditions), but the SEO change meaningfully increases the unchecked surface.
**Suggested fix:** needs a project-wide decision, not a fix to one change. Option A: add
`typescript` + a minimal `tsconfig.json` + a `typecheck` script wired into the pre-push hook,
matching `portal/` (which already runs `tsc --noEmit`); costs one dependency plus whatever
pre-existing errors it surfaces. Option B: accept the status quo. A is the better end state —
`portal/` proves the pattern and the website now carries real logic in TS rather than a
couple of DOM helpers — but it is scope beyond an SEO change.

## Tests and tooling

### 220. [MEDIUM] Onboarding plan-persistence test reimplements `readPersistedPlanKey`
**File**: [portal/tests/onboardingPlanPersistence.test.tsx:11-17](../../portal/tests/onboardingPlanPersistence.test.tsx)
**Severity**: MEDIUM

The new test landed alongside [#205](code-review-followups-archive.md)
defines its own copy of `readPersistedPlanKey` and `VALID_PLAN_KEYS`
rather than importing from `OnboardingPage.tsx`. If the production
validation changes (e.g., adds `plan_enterprise` or tightens
acceptance), the test still passes against the old logic and gives
false confidence.

Fix: extract `readPersistedPlanKey` (and `VALID_PLAN_KEYS`) into a
small `portal/src/lib/onboardingPlanStorage.ts` helper, export it, and
have both `OnboardingPage.tsx` and the test import from there. Drives
both sides from one source.

### 291. [MEDIUM] `test_estimates_analytics.py` exclusion assertion is brittle
**Where:** `platform/tests/test_estimates_analytics.py:163-164` (`test_analytics_excludes_lost_and_archived_from_pipeline`)

**Issue:** The assertion is `777.0 not in (pipeline, pipeline - 4000.0, pipeline - 3500.0)` against hand-computed offsets. A subtle inclusion-bug could pass the assertion. The test also relies on the test runner's wall-clock to align with the seeded `now`, which has caused at least one false alarm during development.

**Fix:** Either (a) plumb `now` through `compute_analytics` as a hook for testing and pin it via the route, then assert exact totals, or (b) use `freezegun` to pin time. Simplest near-term: rebuild the assertion as `assert pipeline == <explicit_in_window_sum>` with no clock dependency.

### 300. [MEDIUM] 17 near-identical `assert client.portal is not None` lines across 10 test files
**Where:** `tests/test_audit_integration.py`, `test_change_logs_api.py`, `test_company_api.py`, `test_divisions_api.py`, `test_feedback_anonymous.py`, `test_feedback_api.py`, `test_property_api.py`, `test_rate_card_bootstrap.py`, `test_resources_rbac.py`, `test_template_api.py`.

**Issue:** The #93 fix added 17 sites of `assert client.portal is not None  # TestClient context manager guarantees a portal (mypy hygiene)`. Comment string is identical at each site. DRY violation flagged in the code review of that batch — the original #93 entry mentioned "a thin `_get_portal()` helper" as the alternative but it was rejected as larger touch (touching every `.call` site in 10 files).

**Fix:** add a session-scoped `portal` fixture in `tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def portal(client: TestClient):
    assert client.portal is not None  # TestClient context manager guarantees a portal
    return client.portal
```

Tests then take `portal: BlockingPortal` and call `portal.call(_fn)` instead of `client.portal.call(_fn)`. Defer until another test-suite touch in any of the 10 files — refactoring purely for DRY is churn.

### 395. [MEDIUM] platform/routers/ops.py — missing 409-path + status/pagination-edge tests
No test coverage for the 409 conflict path, or for status-filter/pagination edge cases (empty page, out-of-range offset, invalid status value).

### 507. [MEDIUM] portal/src/lib/estimateCode.ts + platform/services/readable_id.py — a cross-language contract test was not added
`normalizeEstimateCode` reimplements `normalize_estimate_readable_id` in a second
language. The drift-detection half of the review finding **was** applied: both
files now carry a comment naming the other's test file, and the two suites
(`portal/tests/estimateCode.test.ts`, `platform/tests/test_readable_id.py`)
deliberately mirror each other's cases.

The other half needs a product call that was not made: whether to add a single
API contract test that posts each decorated form (`e0042`, `#E0042`, `E-0042`,
`E 0 0 4 2`) to `GET /estimates?search=` and asserts the same row comes back —
so that one test fails when *either* side moves, instead of relying on a human
noticing the paired comments.

**Suggested fix:** decide whether that test is worth an API round-trip in CI. It
is the only mechanism that makes the duplication self-policing; the argument
against is that it couples a portal unit suite to a running backend. If the
answer is no, close this entry — the mirrored suites plus the comments are a
reasonable resting place.

### 53. [LOW] `_CONFIRMED_WORKING_CASE_IDS` has no entry-validation
**File**: [tests/_maple_coverage_data.py](../../platform/tests/_maple_coverage_data.py)
**Severity**: LOW

The override set grows monotonically and is manually curated. A
mistyped case ID silently does nothing — the override never applies,
and the phrasing stays marked as an XFAIL without the reviewer
realizing.

Fix: at module load, assert that every entry in
`_CONFIRMED_WORKING_CASE_IDS` corresponds to a real `case_id` in the
matrix; raise `ValueError` on mismatch. ~5 lines.

### 113. [LOW] Test bypass `FIREBASE_AUTH_DISABLED=true` hides unauthenticated paths
**File**: [platform/tests/conftest.py:7](../../platform/tests/conftest.py)
**Severity**: LOW (testing infra)

The whole suite runs with `os.environ.setdefault("FIREBASE_AUTH_DISABLED", "true")`,
so a test that hits a router without `X-Test-Email` doesn't actually
exercise the Firebase verification path — it just routes through the
test bypass. Endpoints that *should* 401 for missing auth are not
verifying that behavior.

Fix: add a fixture that temporarily clears (or sets to `"false"`) the
flag for the duration of one test, so router-level auth dependencies are
genuinely exercised. Apply it to at least one endpoint per router family
(feedback, change-logs, companies). Treat as shared testing-infra work
rather than per-PR add-ons.

### 218. [LOW] Mark the price placeholder div for testability and clarity
**File**: `portal/src/components/billing/PlanPickerGrid.tsx:209`
**Severity**: LOW

`<div aria-hidden="true" />` is correct ARIA usage but appears in DevTools as an unexplained empty div. The intent is documented in the comment block above the JSX, but the markup itself is opaque to a future reader scanning the rendered tree.

Fix: optional — add `data-testid="price-placeholder"` (also lets #217's tests target the slot directly), or wrap it in a self-explanatory inline comment at the JSX site.

### 263. [LOW] Remaining `vite` / `vitest` / `esbuild` advisories require a semver-major bump
`portal/package.json` — 5 moderate-severity advisories left after
`npm audit fix`: vite path-traversal in optimized-deps `.map` handling,
vite `server.fs` HTML-bypass, `@vitest/mocker`, `vite-node`, `vitest`.
All dev-only (test runner / dev server), all require the semver-major
fix path (`vite` 4.5 → 8.x, `vitest` 2.1 → 4.x). Bundle this with a
broader tooling refresh — don't tack it onto a feature branch, since
the Vite 8 / Vitest 4 migrations may surface config and plugin changes
across the portal.

### 277. [LOW] Pydantic 2.11 deprecation warning surfaces in async tests
Six warnings per test run from
`lazy_model/parser/new.py:110` — "Accessing the 'model_fields' attribute on
the instance is deprecated. Instead, you should access this attribute from
the model class. Deprecated in Pydantic V2.11 to be removed in V3.0."

Not introduced by these tests; it's a third-party (`lazy_model`)
compatibility gap with Pydantic 2.11. Surfaced because the new async tests
exercise Beanie model loading paths. Will break when Pydantic V3 lands
(currently slated for a 2026-Q3+ release).

Fix: bump `lazy_model` when an upstream release addresses the deprecation,
or pin Pydantic to <2.11 until then. Track upstream
[BAMR-team/lazy-model](https://github.com/roman-right/lazy-model).

### 341. [LOW] New reload API tests don't wrap cleanup in `try/finally`
The reload tests in `tests/test_material_categories_api.py` /
`test_material_units_api.py` follow the file's existing trailing-`# Cleanup`
convention, so a mid-test assertion failure skips the API cleanup calls.
`conftest`'s by-company teardown backstops it, so this is cosmetic. Fix only if
these files grow: fixture-based cleanup.

### 351. [LOW] `React.ReactNode` referenced without explicit React import in MapleMarkdown.test.tsx
`portal/tests/MapleMarkdown.test.tsx:13` — `renderInRouter` types
its `node` param as `React.ReactNode` but the file doesn't
`import React` or `import type { ReactNode } from "react"`. Resolves
today via the global `React` namespace from `@types/react`, but
breaks if the project ever tightens `tsconfig.compilerOptions.types`
or removes the global declaration. Fix: `import type { ReactNode }
from "react"` and reference `ReactNode` directly.

### 361. [LOW] portal/src/pages/OnboardingPage.tsx:140 — back-nav wiring isn't covered by a test
The new `onBack={() => goToStep(1)}` on the Contacts step and the
`companyId`/`onCompanyUpdated` props are untested at the page level. The meaningful logic
(create-vs-update, prefill) is covered in `CompanyStepEdit.test.tsx`; this is just one-line
glue, but the navigation contract has no regression guard.
**Suggested fix:** Optional — `OnboardingPage` needs firebase mocking to render (no existing
pattern), so low-value to test directly. Acceptable to leave given the branch logic is
covered.

### 396. [LOW] platform/services/ops_verification.py — no Firebase-failure unit test
No test simulates a Firebase Admin SDK failure (e.g. `firebase_admin_auth.get_user_by_email` raising something other than `UserNotFoundError`) to verify the verification flow degrades safely.

### 397. [LOW] platform/services/staff_service.py — no email-failure provisioning branch test
`provision_staff_user` swallows `send_password_reset_email` failures (logs a warning, continues) but no test exercises that branch to confirm the staff record is still created.

### 403. [LOW] portal/tests/onboardingResumeApply.test.ts — test name overstates
The test named "clears a stale in-progress flag and its saved step" only asserts the in-progress flag; `clearOnboardingInProgress()` leaves `portal.onboardingStep` behind (harmless — routing gates on the flag alone). Rename the test, or extend the helper to clear the step key too.

### 422. [LOW] platform/tests/test_billing_plan_config.py:220 — duplicated TS block-parsing regex
`test_fe_included_tasks_matches_be` re-implements the plan-block regex parse
instead of sharing it with the class fixture (necessary because the fixture is
int-only, but the block-carving regex is now written twice).
**Suggested fix:** Extract a shared "parse plan blocks from billing-plans.ts"
helper used by both the fixture and the nullable-field test.

### 432. [LOW] CLAUDE.md — the bandit baseline is a hardcoded "13" and will drift
Logged 2026-07-27 from the second `/code-review` pass. The bandit section added
to CLAUDE.md states "Known baseline: 13 B110 findings" and tells the reader a
count above 13 means their change added one. As the B110 sweep (entry above)
lands, that number goes stale and the guidance silently inverts — a reader
seeing 9 can't tell whether that's progress or a miscount.
**Suggested fix:** Either drop the number and point at the followups entry as
the source of truth, or adopt `bandit -b baseline.json` so the tool tracks the
delta itself instead of a human-maintained integer in prose. The second is
better if the B110 sweep is going to be gradual.

### 440. [LOW] platform — untested branches and one simulated test premise
Three small gaps, none behavioral: (a) the `resolution["error"]` path and the
estimate-deleted branch of `_write_link` have no covering test — both are simple
early returns with no state mutation; (b) there is no router-level end-to-end
test for arm-near-tie → reply `"2"` — both halves are unit-tested with a fake on
the other side, and the record shape was verified by inspection; (c) the Critical
ordinal test simulates the substring trap with a fake resolver rather than
exercising real tier-1 matching, so nothing in the suite pins
`"2" in "12 oak rd"` as the mechanism. (c) is now largely moot — the short-query
floor in `_resolve_property_address` closes that trap at its source.
**Suggested fix:** add the covering tests opportunistically when these files are
next touched.

### 444. [LOW] portal/tests/opsUsage.test.ts — assertions depend on the runtime locale
`formatUsage` / `formatCreditsBalance` use `toLocaleString()`, and the tests
assert `"1,200 / 100,000"` and `"49,876"`. Under a non-en ICU locale those become
`"1.200"` / `"49 876"` and the suite fails for reasons unrelated to the code. Dev
and CI are en-US today, so it is latent.
**Suggested fix:** pin the locale in the formatter (`toLocaleString("en-US")`) if
ops output should be stable regardless of operator locale, or assert with a
locale-independent matcher.

### 460. [LOW] website/contact-modal/__tests__/install.test.js:135 — regex assertion spans the entire document body
`expect(document.body.innerHTML).not.toMatch(/pre-launch/i)` guards the whole body rather than
the modal. In jsdom the body only holds the modal, so it passes today, but any unrelated
fixture that ever mentions "pre-launch" would fail this test in a way that points at the wrong
code.

**Suggested fix:** scope it —
`expect(document.querySelector('.cm-dialog').innerHTML).not.toMatch(/pre-launch/i)`.

### 466. [LOW] portal/tests/TaskDialog.test.tsx:105 — raised timeouts slow the failure of genuine hangs
A real infinite-await in a 20s-tier file now takes 20s to surface instead of 5s — up to
43 tests in TaskDialog. This is the inherent cost of the fix and was a deliberate call:
the rest of the suite was left at the 5s default specifically to confine the cost to nine
files rather than all ~176.

**Suggested fix:** none — accept. Revisit only if the 20s tier grows, at which point the
right move is probably to make the slow files faster rather than to widen the margin.

### 467. [LOW] portal/tests/ — tiers derive from a one-off measurement with no drift check
The tier assignment reflects timings taken once, on one idle machine. Nothing re-verifies
that TaskDialog is still >= 2.0s, and nothing flags a newly-slow file that has no override.
The tiering will go stale silently — which is exactly how the 5s default became wrong in
the first place.

**Suggested fix:** no action now. If it recurs, a CI step that fails when an un-overridden
file exceeds the tier threshold would catch drift without manual re-measurement.

### 482. [LOW] website/src/content/__tests__/image-perf.test.ts:31 — the lazy-loading assertion skips both logos
`ABOVE_THE_FOLD` excludes by `src`, and the header and footer logos share the same `src`
(`/3Maples-logo-horizontal-black.png`). The exclusion intended for the header logo therefore
also exempts the footer one, so the `loading="lazy"` added to the footer image is not covered
by any test and could be removed without failing anything.
**Suggested fix:** key the exemption on something that distinguishes them — simplest is to
exempt only the first occurrence of that src in document order (the header logo) and require
lazy on the rest.

### 489. [LOW] platform/scripts/prime_brevo_events.py — no test coverage
The one file in the change with no tests. It is an operational script in the same mould as
`scripts/create_brevo_attributes.py`, which is also untested, so this is consistent rather
than novel — but it posts to a live Brevo account.
**Suggested fix:** a test is optional given the sibling precedent; if one is wanted, the
meaningful assertion is that a dry run performs zero HTTP calls, which is the property that
makes the script safe to hand to someone else.

### 503. [LOW] platform/tests/ — `asyncio.run` in unit tests runs on a different loop than Beanie's client
`tests/conftest.py` initializes Beanie through the session-scoped TestClient, so
the Motor client is bound to that client's portal loop. Any test that drives an
endpoint with `asyncio.run(...)` creates a fresh loop, and every DB call from it
fails with "Future attached to a different loop". Two files were affected
(`test_orchestrator_endpoint.py`, `test_agents_api.py`) and both are now stubbed
at the persistence boundary, which is the right answer for *those* tests — they
are unit tests of routing, and real coverage lives in `test_conversation_api.py`.

The general trap remains: any future test that reaches for the DB through
`asyncio.run` will fail silently or noisily depending on whether the caller logs,
and the failure looks like a product bug rather than a harness one. Note that
tests using `portal_call(client, ...)` are fine — they run on the right loop, and
`TestReadableIdEndToEnd` genuinely exercises persistence that way.

**Suggested fix:** either a conftest guard that fails loudly when a Beanie call
is made from a loop other than the client's, or a documented `portal_call`
convention for any test that needs the DB. The guard is more work but catches it
at the point of the mistake; a note in `CLAUDE.md`'s testing section is the cheap
version.

### 514. [LOW] platform/tests/test_brevo_lifecycle_reconcile.py — function-level imports break the file's convention
The DB-backed replay-date tests import `datetime`, `GoogleDocsVersion` and
`collect_estimate_facts` inside the test body, while every other test in the file relies on
module-level imports at the top. Nothing is circular, so the local imports have no reason
beyond how they were written. (`GoogleDocsVersion` is in fact already imported at module
level, so that one is redundant as well as inconsistent.)
**Suggested fix:** move them to the module header alongside the existing imports.

### 517. [LOW] platform/tests/test_auth_email.py:158 — module constant declared mid-file
`FIREBASE_VERIFY_LINK` is defined at line 158, below seven existing tests, because the
verification-link tests were appended to the end of the file. It resolves fine at import time,
so there is no behavioral consequence; it just makes a shared fixture value harder to find than
the top-of-module placement a reader expects.

**Suggested fix:** move the `FIREBASE_VERIFY_LINK` assignment up to just under the imports at
the top of the file, leaving the tests where they are.

### 519. [LOW] portal/tests/TourManager.test.tsx:37 — the viewport mock hard-codes the module's current shape
`vi.mock("../src/tours/viewport", () => ({ isPhoneViewport: vi.fn(() => false) }))` replaces
the whole module with a single-export factory. If `viewport.ts` later gains a second export
and `TourManager` imports it, this file fails with an undefined-is-not-a-function error at
render time rather than anything that names the real cause. The same pattern was since
copied into `tests/PreferencesCard.test.tsx`, so a fix should cover both.

**Suggested fix:** use
`vi.mock("../src/tours/viewport", async (importOriginal) => ({ ...(await importOriginal<typeof import("../src/tours/viewport")>()), isPhoneViewport: vi.fn(() => false) }))`
so future exports pass through unmocked. Low value on its own — fold it in when either test
file is next touched.

### 522. [LOW] portal/tests/RecurrenceDialog.test.tsx:50 — brittle substring assertion over a `<select>`'s full option text
`expect(rowOf(startMonth).textContent).not.toContain("to")` reads the whole row, and a
`<select>`'s `textContent` includes all twelve `MONTH_LABELS`. It passes today only because no
abbreviation happens to contain "to". Localizing or renaming a month label (e.g. a full-name
variant with "October") would fail this test for a reason unrelated to what it guards.

**Suggested fix:** assert on the row's label span instead of the whole row — query the
`Start`/`End` label element and check its text — or scope the negative assertion to the row's
direct `<span>` children rather than `textContent`.

### 526. [LOW] portal/tests/WorkItemBlankRowGuard.test.tsx:97 — blank rows are counted by `textContent` prefix rather than by role name
`countPlaceholders` filters all comboboxes by `textContent.startsWith("Select material")`. It
works, but couples the test to the placeholder copy and to the fact that the size select's text
happens to begin differently ("Select size1 yd"). Renaming a placeholder — a pure copy change —
silently breaks the guard tests. This existed because the selects had no accessible name; that
blocker is now gone (they carry `ariaLabel="Material"` / `"Role"` as of the same pass), so the
cleanup is unblocked.

**Suggested fix:** replace the helper with `screen.queryAllByRole("combobox", { name: "Material" })`
/ `{ name: "Role" }` and delete `countPlaceholders`. Note the counts change meaning — those
queries match every row, not only blank ones — so the assertions need rewriting in terms of
total row count rather than blank-row count.

### 578. [LOW] No test that `discard_doc_image_paths` swallows errors
`platform/routers/estimate_helpers/doc_versions.py:376` — Every API test swaps in a `delete_doc_images` that never raises, so the "never fails the request" branch the delete route relies on is untested.

**Suggested fix:** A unit test with a raising `delete_doc_images`: assert no exception and one warning.

### 579. [LOW] No test for the doc-image GET when the blob is missing from storage
`platform/routers/estimate_documents.py:264` — Only an unknown image id is tested, not a known id whose blob is gone (for example after a race).

**Suggested fix:** Pop the blob from `fake_store.blobs`, then assert 404.

### 582. [LOW] Stale docstring says notes inherit the estimate edit lock
`platform/tests/test_estimate_agent.py:3818` — `test_locked_estimate_refuses_title_rename` still lists "notes" among the sub-ops that inherit the lock; notes bypass it since 2026-09-23.

**Suggested fix:** Remove "notes /" from the docstring.

### 583. [LOW] Lost the agent-level check that Review status is editable
`platform/tests/test_estimate_agent.py:3842` — The old notes test covered Draft and Review; `test_editable_estimate_allows_title_rename` covers only Draft, so a regression that locked Review would pass every Maple lock test.

**Suggested fix:** `@pytest.mark.parametrize("status", ["Draft", "Review"])`.

### 603. [LOW] No test re-renders the Documents dialog with the post-success versions
`portal/tests/DocumentsDialog.test.tsx:97` — The kept-image reconciliation never runs against a freshly kept image — the path the adjust-during-render design was accepted for. It is believed correct; nothing pins it.

**Suggested fix:** After the `waitFor`, `rerender(<DocumentsDialog {...props} versions={[v3, v2, v1]} />)` and assert "Remove c.jpg" is present and the counter reads "1 / 10".

### 604. [LOW] Documents dialog test name says "oversize files" but uploads none
`portal/tests/DocumentsDialog.test.tsx:86` — The size branch is covered only by the `docImagePickError` unit test.

**Suggested fix:** Upload `jpeg("big.jpg", 10 * 1024 * 1024 + 1)` and assert `/big\.jpg.*10MB/`, or rename the test.

### 605. [LOW] `useBlobObjectUrl`'s leak guards aren't tested
`portal/tests/useBlobObjectUrl.test.tsx:27` — No test for a late resolution after unmount (URL revoked, never returned) or a key change (old URL revoked) — the branches `NoteAttachmentStrip` now relies on.

**Suggested fix:** Add a deferred-load-resolves-after-unmount test and a key-change rerender test asserting the first URL is revoked and `load` is called twice.

### 606. [LOW] The estimate page's own generate-doc rejection paths aren't tested
`portal/tests/NewEstimateWithActivityPage.documents.test.tsx:194` — The dirty-save failure (must reject without calling `generateGoogleDoc`) and the `!estimate` guard have no test.

**Suggested fix:** Make the page dirty and make `estimatesApi.update` reject, call onGenerate, and assert it rejects with /couldn't be saved/ and `generateMock` was not called.

### 644. [LOW] The fake patches the wrong `get_company_defaults`
`platform/tests/_estimate_fakes.py:92` — It patches `work_item_handlers.get_company_defaults`, but the executor imports its own name, so executor add tests never use the fake's 20/10/13 defaults (they hit the real lookup, which fails and falls back to 0).

**Suggested fix:** Also patch `agents.estimate.edit_executor.get_company_defaults` in `wire_estimate_agent`.

*(Review 2026-09-24 fourth pass #31.)*

### 662. [LOW] /code-review's bandit command bypasses the pinned config
`.claude/commands/code-review.md:69` — Step 3 runs `bandit -r . -x tests/`, which doesn't load `platform/bandit.yaml` (bandit reads it only with `-c`; `run_bandit.sh` passes it). A literal run therefore reports every B101 `assert … is not None` from the mypy playbook and scans `.claude` worktrees, while Step 3 says to number every hit and compare against the 11-B110 baseline — a comparison that can't hold on that output. CLAUDE.md says to run bandit via `./run_bandit.sh` and not to pass flags ad hoc. Predates the 2026-09-25/26 Maple routing work; review tooling, not user-facing.

**Suggested fix:** Replace the code block with `cd platform && ./run_bandit.sh` (the script activates the venv and pins `-c bandit.yaml`).

*(Review 2026-09-26 round 20 #2.)*

### 736. [MEDIUM] The "without the loading screen" assertion cannot fail
`portal/tests/DashboardPage.test.tsx:262` — `window.dispatchEvent(...)` runs outside `act`, so the re-render hasn't happened when `queryByText("Loading dashboard...")` is checked; the assertion passes trivially. The `waitFor` on the analytics call count would pass for a non-quiet reload too. (review 2026-09-27 #66)

**Suggested fix:** Make `estimatesApi.list` return a pending promise, dispatch inside `await act(async () => …)`, then assert no spinner, as the Contacts, Materials and Templates tests do.

### 769. [LOW] The `?contactId=` announce test never checks the link is consumed
`portal/tests/ContactsPageDiffSave.test.tsx:194` — with no sheet the `if (close)` branch is skipped, so the test only checks "announced c2, never unannounced"; deleting `setSearchParams(... delete("contactId"))` (the snap-back fix) leaves it green, and the `?open=` case never asserts the sheet opened. (review 2026-09-28 third round #9)

**Suggested fix:** Put the expected sheet state in the `each` table and assert it (a dialog for `?open=`, none for `?contactId=`); for `?contactId=`, tap c1, fire the contacts-changed event (a quiet reload), and assert the last announced id is c1.

### 770. [LOW] The `?propertyId=` announce test never checks the link is consumed
`portal/tests/PropertiesPageMobileSheet.test.tsx:365` — same gap as #769: deleting `delete("propertyId")` leaves it green, and the `?open=` case never asserts the sheet. (review 2026-09-28 third round #10)

**Suggested fix:** As #769: assert the sheet state per case, tap prop-1, trigger a quiet reload, assert prop-1 stays announced.

### 800. [LOW] The CSV upload test leaves a "Hardscape" category in use
`platform/tests/test_material_upload_api.py:11` — its "Patio Stone" material stays in the test company, so `test_material_categories_api.py::test_load_standard_categories_removes_non_standard_when_requested` fails when it runs after the upload tests (`skipped_in_use == ['Hardscape']`). Fails on a clean checkout too; order-dependent.

**Suggested fix:** Delete the uploaded materials (and their created categories/units) in the upload tests' teardown.

### 805. [LOW] Two of the three guards are pinned only by a 0.1 s wall clock
`platform/tests/test_record_lists.py:1` — `test_a_long_message_never_reaches_the_bare_name_pattern` and `test_catalog_names.py::test_a_long_message_is_no_focus_question` assert `elapsed < 0.1`. What #707 and #708 fixed is an ORDER: the length check runs before the pattern. That is directly testable, but the tests check it through timing instead. The fixed path is microseconds, so they pass by a wide margin today. But the neighbouring test (`test_a_long_what_about_stays_linear`) deliberately uses 1.0 s because "a wall-clock bound must not flake on a GC pause", and these two are the only 0.1 s bounds in the conversation suites. LOW: no flake observed; it's suite hygiene. (review 2026-10-02, guards batch #1)

**Suggested fix:** Assert the order rather than the clock: `monkeypatch.setattr(record_lists, "_BARE_GET_RE", _Exploding())` (and `catalog_names._FOCUS_QUESTION_RE`), where `_Exploding.match` raises, then call each rewrite with the 2,000-character message and assert None. Keep the #788 test (`test_conversation_followup.py::test_a_long_comparison_stays_linear`) on the clock (bounded search; 1.6 ms against 0.1 s) and add the same exploding stand-in for its "Bob Lee" path, which should never search at all.

### 823. [MEDIUM] The catalog figure's database-down reply is untested
`platform/agents/conversation/catalog_figures.py:298` — (Edge case — an infrastructure failure.) `catalog_figure_reply` catches a failed query and replies `_DB_DOWN` under a list intent with an empty result, so no 500 reaches the user. No test makes the query fail, so a regression that re-raises or uses the wrong intent would pass. (review 2026-10-08 (2c) branch audit #2, deferred)

**Suggested fix:** Monkeypatch `catalog_figures.material_price_extreme` to raise, run `{op: "catalog_figure", kind: "priciest_material"}` through the executor, and assert `response == _DB_DOWN`, `intent == "list_materials"`, `result == {"operation": "list_materials", "read_only": True, "figure": "highest", "field": "price"}`.

### 824. [MEDIUM] The metric's database-down reply is untested
`platform/agents/estimate/metric_answers.py:334` — (Edge case — an infrastructure failure.) `answer_metric_ask` catches a failed resolve or fetch and replies `_DB_DOWN` as a question ("Would you like to try again?"). Only the string's outcome classification is tested (test_maple_outcomes.py:84), not the path. (review 2026-10-08 (2c) branch audit #3, deferred)

**Suggested fix:** Monkeypatch `metric_answers.run_metric` to raise, run `{op: "metric", status: "sold"}` through the executor, and assert `response == _DB_DOWN`, `needs_clarification is True`, `clarifying_question == "Would you like to try again?"`.

### 825. [MEDIUM] A status breakdown with no data is untested
`platform/agents/estimate/crud_handlers.py:2188` — (Edge case — analytics with no entries at all, a data shape #4/#5 don't reach.) When `compute_analytics` returns no status entries, the reply is "No status data available for this period." No test reaches it. (review 2026-10-08 (2c) branch audit #6, deferred)

**Suggested fix:** Monkeypatch `routers.estimates.compute_analytics` to return an object with empty `by_status` and `by_division`, run `{card: "by_status"}`, and assert the reply. Pair with #5, so each arm has its own case.

### 826. [MEDIUM] A `count: false` inside a filter beside `count: true` is untested
`platform/agents/planner/schema.py:67` — (Edge case — an unusual combination of inputs.) `_count_in_filter` keeps the action's own `count` when the filter's is false (`bool(data.get("count")) or bool(counted)`). Only `filter.count: true` is tested, so a change that lets the filter's false override the action's true would pass. (review 2026-10-08 (2c) branch audit #10, deferred)

**Suggested fix:** Add a schema test: `{"op": "list_properties", "count": True, "filter": {"owner": "x", "count": False}}` validates to `count is True` and a filter without `count`.

### 827. [MEDIUM] `_metric`'s no-ask guard is untested
`platform/agents/planner/execute.py:681` — (Edge case — a defensive guard no caller reaches.) `_metric` raises `ValueError` when `metric_ask` returns None — unreachable through `execute` because the gate stops such a plan, but it is the executor's guard if `_metric` is ever reached another way. No test. (review 2026-10-08 (2c) branch audit #12, deferred)

**Suggested fix:** Call `execute._metric(schema.Metric(shape="ranking"), context={}, message_en="m", get_processor=lambda _l: None)` under `pytest.raises(ValueError)`.

### 828. [MEDIUM] A notes parent property with no name is untested
`platform/agents/conversation/record_notes.py:115` — (Edge case — optional data missing.) `note_parent("property", doc)` names a property by its street when it has no name (`Property.name` is optional, default ""). The reply's label and the focus name both use it. Every test property has a name. (review 2026-10-08 (2c) branch audit #13, deferred)

**Suggested fix:** In the notes test, add a property with `name=""` and a note, run `list_notes` on it, and assert the reply names its street ("Here are the notes on [3 Oak Ave]…").

### 829. [MEDIUM] A notes parent estimate with no code is untested
`platform/agents/conversation/record_notes.py:119` — (Edge case — optional data missing.) `note_parent("estimate", doc)` labels the estimate by its title when `estimate_id` is blank. No test has an estimate without a code. (review 2026-10-08 (2c) branch audit #14, deferred)

**Suggested fix:** Call `note_parent("estimate", SimpleNamespace(id=PydanticObjectId(), estimate_id="", title="Birch Patio"))` and assert `"Birch Patio" in parent.label` and `parent.name == ""`.

### 830. [MEDIUM] A property's contacts named by its street, or "That property", is untested
`platform/agents/contact/service.py:2039` — (Edge case — optional data missing.) `contacts_of_property_reply` labels the property by name, else street, else "That property". Only the name arm is tested. (review 2026-10-08 (2c) branch audit #15, deferred)

**Suggested fix:** Add stored properties with `name=""` (assert "3 Oak Ave has 1 contact:") and with `name=""` and `street=""` — `street` is required but an empty string passes — (assert "That property has no contacts linked to it yet.").

### 831. [MEDIUM] A contact's property row named by its street, or "Unnamed Property", is untested
`platform/agents/property/service.py:2553` — (Edge case — optional data missing.) `properties_of_contact_reply` labels each row by name, else street, else "Unnamed Property". Only named properties are tested, so a nameless property's row label is unpinned. (review 2026-10-08 (2c) branch audit #16, deferred)

**Suggested fix:** Link Ana to a property with `name=""` (assert its row shows the street) and to one with `name=""` and `street=""` — `street` is required but an empty string passes validation — (assert its row shows "Unnamed Property").

### 832. [MEDIUM] Adding notes to a task that has none, among several changes, is untested
`platform/agents/task/planned.py:95` — (Edge case: optional data missing.) `_planned_note`'s `else added` arm, notes added to an empty note among several changes, has no test. A wrong join would leave a stray blank first line, which becomes an empty title. (review 2026-10-08 (4b) #16, deferred)

**Suggested fix:** With the blank task, test `{"notes_append": "Call Bob", "status": "Done"}`: `description == "Call Bob"` and `title == "Call Bob"`.

### 833. [MEDIUM] A task status that doesn't resolve among several changes is untested
`platform/agents/task/planned.py:107` — (Edge case: a guard the policy screens out.) The policy asks first about a status the company doesn't have (`_check_details`), so `_planned_change` returning None for one is reachable only if the policy and `_resolve_status_by_name` disagree. It is untested. (review 2026-10-08 (4b) #17, deferred)

**Suggested fix:** Test `TaskAgent.update_task_reply(task, {"status": "Blocked", "assignee": "Jordan"}, …)` directly: it asks today's "I don't recognize 'Blocked' …" question, and nothing is written.

### 834. [MEDIUM] A teammate that doesn't resolve among several task changes is untested
`platform/agents/task/planned.py:110` — (Edge case: a guard the policy screens out.) The policy asks first about a teammate who isn't exactly one (`_check_details`), so `_planned_assignee` returning None for a name is unreachable through a real turn. It is untested. (review 2026-10-08 (4b) #18, deferred)

**Suggested fix:** Call `update_task_reply` directly with `{"assignee": "Nobody", "status": "Done"}`: today's "Who should I assign the task to?" is asked, and nothing is written.

### 835. [MEDIUM] "Me" with no known email among several task changes is untested
`platform/agents/task/planned.py:129` — (Edge case: missing data.) With no `current_user_email`, `_planned_assignee` returns None and the change goes to `_handle_task_assign`, which says "I couldn't confirm your email…". There is no test. (review 2026-10-08 (4b) #19, deferred)

**Suggested fix:** Use a context without `current_user_email` and `{"assignee": "me", "status": "Done"}`: that reply, with `success=False`, and nothing written (`_run(..., me=None)` in test_planner_execute_tasks.py already supports it).

### 836. [MEDIUM] Archiving among several task changes is untested
`platform/agents/task/planned.py:115` — (Edge case: an unusual combination.) `_planned_change`'s `archived` arm ("mark it done and archive it") has no test. (review 2026-10-08 (4b) #20, deferred)

**Suggested fix:** Test `{"status": "Done", "archived": True}`: both are written in one update.

### 837. [MEDIUM] The planner's unknown-task-field raise can't be reached
`platform/agents/task/planned.py:122` — (Edge case: a defensive guard no caller reaches.) Every key comes from `TaskFields`, so `raise ValueError(f"no task field {name}")` can't run. It is untested. (review 2026-10-08 (4b) #21, deferred)

**Suggested fix:** Keep it as the explicit guard and add a direct test: `_planned_change("colour", "red", …)` raises ValueError. Or fold `due_date` into the `cleared` table's style and drop the raise.

### 838. [LOW] A failing planner-only acceptance row is listed twice in the report
`platform/tests/planner_parity/acceptance.py:148` — `render` builds "Gaps of today's still open" from `r["gap"] and not r["passed"]`. A failing `Conversation.planner=True` row also has `counts_against=True`, so it appears under both "Failures that count" and "Gaps of today's still open". The second listing makes a planner regression look expected, and inflates the "still open" count. LOW, not MEDIUM: the run's assertion and the header counts are right; only the report's sections mislead. (review 2026-10-11 #1, deferred)

**Suggested fix:** Exclude counted rows from that section: `[r for r in results if r["gap"] and not r["passed"] and not r["counts_against"]]`. Add a `test_planner_acceptance_report.py` test that renders a failing `planner=True` row and asserts it appears under "Failures that count (1)" and that the report has "Gaps of today's still open (0)".

### 839. [LOW] An explained planner-only acceptance row is reported as a still-open gap
`platform/tests/planner_parity/acceptance.py:146` — "Explained failures" filters `not r["gap"]`, so a failing `planner=True` row that is in `EXPLAINED_CONVERSATIONS` (counts_against False) lands only in "Gaps of today's still open". The report never shows its explanation where a reader looks for it. LOW: it only matters once a planner row is explained, and none is today. (review 2026-10-11 #2, deferred)

**Suggested fix:** Filter by whether the planner owns the row: `[r for r in results if not r["passed"] and r["explained"] and (not r["gap"] or r["planner"])]`. Carry `"planner": conv.planner` in `conversation_result`'s dict, and drop explained planner rows from "still open". Add a render test with an explained failing `planner=True` row that asserts "Explained failures (1)".

### 872. [MEDIUM] "a breakdown over N days falls back" is never really tested
`platform/tests/test_planner_execute_figures.py:323` — The test strips `days`, so the new arm at execute_figures.py:50 (days given + a breakdown → fallback) isn't reached. (review 2026-10-11 #47, deferred)

**Suggested fix:** Keep `days` for that case, or add one: `{card:"by_division", period:"last_n_days", days:7}` → "filter:dashboard.period".

### 910. [LOW] The test asserts only what the reply isn't
`platform/tests/test_planner_adjust_assumption.py:182` — It never checks that the change was applied. (review 2026-10-11 #90, deferred)

**Suggested fix:** Assert the saved quantity changed, or today's adjustment wording.

## Codebase hygiene (batchable)

Small, low-risk cleanups. Safe to batch into a single `chore: code hygiene`
commit, or clear opportunistically when already editing the file. #8-#13 are
standing sweeps; the rest are individual instances.

### 8. [MEDIUM] `print()` → `logging`
Any `print()` left in `services/`, `routers/`, `agents/`, or `models/`. Keep
`print()` in `scripts/` (operator-facing CLIs) — that's appropriate there.

### 9. [MEDIUM] Magic numbers → named constants
Examples found: timeout values, quota limits, retry counts, score thresholds.
Give each a module-level constant with a short comment explaining its source.

Specific instances:
- #162 — `_parse_estimate_date_filter` fixed day counts per unit
- #171 — `lg:right-[26rem]` AI panel width duplicated across 3 sites
- #194 — `1_000_000` "effectively unlimited estimates" across 3 sites
- #262 — `Math.max(heightPct, 4)` unnamed minimum bar floor
- #267 — `1023px` mobile breakpoint coupled to Tailwind `lg`

**Absorbed:** #162, #171, #194, #262, #267.

### 10. [MEDIUM] Missing docstrings on public APIs
Focus only on functions exported across package boundaries. Don't docstring
private helpers — named variables beat comments.

**Absorbed:** #52.

### 11. [MEDIUM] TODO / FIXME triage
Grep for `TODO` and `FIXME` added in recent changes. Each should either:
- be resolved, or
- be converted into a GitHub issue with a link back to the code.
Comments that just say "TODO" with no owner / date / issue will rot.

Specific instances:
- #253 — Remove deprecated `TokenUsageAccumulator` after one billing cycle
- #254 — Reintroduce `request_id` on `LLMUsageEvent` when middleware lands

**Absorbed:** #253, #254.

### 13. [MEDIUM] Mutation where immutable return would be clearer
Case-by-case judgment. Only refactor if it actually simplifies the reader's
job; don't chase stylistic purity.

### 32. [MEDIUM] `hasattr(l.unit, "value")` defensive check with unclear motivation
**File**: `routers/labours.py:202`
**Severity**: MEDIUM

`existing_by_key = {(l.name, l.unit.value if hasattr(l.unit, "value") else l.unit): l for l in candidates}` —
the `Labour.unit` field is typed as `LabourUnit` enum in the model, so
`.value` should always work. The `hasattr` fallback either (a) defends
against legacy string-valued rows in prod, or (b) is defensive coding
without cause. If (a), document it; if (b), drop it.

Fix: grep production data once to check whether any `Labour` rows have
`unit` stored as a raw string. If none, simplify to `l.unit.value`. If
some, add a one-line comment and file a data-migration task.

### 44. [MEDIUM] `(err as Error).message` fallback in catch blocks can render `undefined`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — three catch blocks: `handleDelete` (~L427), `handleStatusChange` (~L458), `handleGenerateGoogleDoc` (~L481)
**Severity**: MEDIUM

If the rejected value isn't an `Error` instance (plain string from
`ApiError`, JSON object, aborted fetch signal), `(err as Error).message`
evaluates to `undefined` and `setFormError(undefined)` clears the banner
instead of showing a useful message. Pre-existing pattern carried through
the refactor; third catch (`handleGenerateGoogleDoc`) already has an
OR-fallback, the first two do not.

Fix: unify to `setFormError(err instanceof Error ? err.message :
"Failed to update status")` (pick appropriate fallback copy per handler).
One-line change per catch.

### 70. [MEDIUM] Missing type hints in `backfill_material_units.py` helpers
**File**: [platform/scripts/db/backfill_material_units.py:50, 68](../../platform/scripts/db/backfill_material_units.py)
**Severity**: MEDIUM (script context, not production code)

`remap_materials_for_unit(company_id, old_unit_id, new_unit_id)` and
`migrate_company(company)` lack annotations. The divisions backfill set
the same precedent, but for consistency with the model APIs these would
be more self-documenting as
`remap_materials_for_unit(company_id: PydanticObjectId, old_unit_id: PydanticObjectId, new_unit_id: PydanticObjectId) -> int`
and `migrate_company(company: Company) -> dict`.

### 115. [MEDIUM] Mixed string-vs-regex tuples in `refusal.py`
**File**: [platform/agents/maple_public/refusal.py:27-55](../../platform/agents/maple_public/refusal.py)
**Severity**: MEDIUM (maintainability)

`_ACTION_VERBS` and `_DOMAIN_NOUNS` mostly hold plain strings, but a few
entries embed raw regex fragments (`"set\\s*up"`, `"job\\s*site"`,
`"team\\s*member"`, `"work\\s*item"`, `"rate\\s*card"`). The values are
joined into a `|` alternation and never `re.escape`d. A maintainer
adding a literal noun with a regex metacharacter (e.g. a hyphen, parens,
or a dot) would silently get the wrong match.

Fix: either (a) add a one-line comment near the tuples saying "values
are raw regex fragments — do NOT pre-escape", or (b) split into two
tuples (literal vs regex), `re.escape` the literal one before joining.

### 132. [MEDIUM] Description read-only color is dead CSS
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM

`className={'... ${canEdit ? "..." : "bg-gray-50 ... text-gray-500"} ${!description ? "text-gray-400" : "text-gray-900"}'}`.
The trailing ternary always wins over the `!canEdit` `text-gray-500`
because Tailwind utilities at the same specificity resolve by
stylesheet source order, not className order. Read-only state ends up
visually identical to editable.

Fix: collapse to one expression:
`canEdit ? (description ? "text-gray-900" : "text-gray-400") : "text-gray-500"`.

### 190. [MEDIUM] Typo "iintegrations" in Pro plan feature copy
**File**: [portal/src/lib/billing-plans.ts](../../portal/src/lib/billing-plans.ts) line 111
**Severity**: MEDIUM (user-visible copy)

`PLAN_DETAILS.plan_pro.features` ships `"All systems iintegrations"` —
double `i`. Visible in onboarding's PlanStep and the Manage Plan modal.
Pre-existing in the uncommitted diff (not introduced this session) but
flagged so it gets fixed before the next plan-cards commit lands.

Fix: `"All systems integrations"` (or revisit phrasing entirely — the
prior copy was `"Integrate with top accounting packages"`).

### 222. [MEDIUM] `ESTIMATE_STATUS_TRANSITIONS` two-step construction in `models/estimate.py`
**File**: [platform/models/estimate.py:36-92](../../platform/models/estimate.py)
**Severity**: MEDIUM

The map is declared empty (`ESTIMATE_STATUS_TRANSITIONS: dict[...] = {}`),
then `.update(...)` populates it after `validate_estimate_status_transition`
is defined. The forward-reference dance (`dict["EstimateStatus", set["EstimateStatus"]]`)
implies a circular dependency that doesn't actually exist —
`EstimateStatus` is fully defined at line 8, well before line 36.

Fix: collapse to a single literal assignment with concrete type
annotations (no string forward refs), placed once before
`validate_estimate_status_transition`. Identical behavior, cleaner
ordering, easier to read.

### 301. [MEDIUM] `messages: List[Any]` in `agents/estimate/service.py:1811` weakens type info
**Where:** `agents/estimate/service.py:1811` — `messages: List[Any] = [SystemMessage(content=formatted_prompt)]`.

**Issue:** Annotated as `List[Any]` to allow appending `HumanMessage` to a list initialized with `SystemMessage`. Loses type safety on all subsequent `.append()` calls (4 sites in this function plus several elsewhere).

**Fix:** use `List[BaseMessage]` from `langchain_core.messages` (or `langchain.schema.BaseMessage`) — that's the actual base class for `SystemMessage` / `HumanMessage` / `AIMessage`. Tighter and more honest. Same pattern likely needed at other langchain message-list sites in `service.py` that escaped this pass.

### 352. [MEDIUM] `EstimatesTable.tsx` layout comment references `min-w-0` but cells use `min-w-[8rem]`
`portal/src/components/common/EstimatesTable.tsx:137-140` — the
new layout-rationale comment claims Title/Property "can shrink to
a small floor (`min-w-0` lets a long word break instead of forcing
the column wide)", but the `<th>` cells actually use
`min-w-[8rem]` (128px). `min-w-0` is nowhere on either cell. A
reader trusting the comment will misjudge how narrow the columns
can get. Fix: update the comment to match the 8rem floor, or add
`min-w-0` to the inner content div if word-break behavior is
actually wanted alongside the cell floor.

### 34. [LOW] Missing type hint on `existing_by_key` dict
**Files**: `routers/equipments.py:136`, `routers/labours.py:193`
**Severity**: LOW

Materials.py added the annotation (`existing_by_key: Dict[str, Material] = {}`);
equipments.py and labours.py did not. Consistency gap introduced by the
same commit.

Fix: `existing_by_key: Dict[Tuple[str, str], Equipment] = {}` (and
similarly for Labour). Import `Dict, Tuple` from typing.

### 39. [LOW] `_RATE_LIMIT_DETAIL` constant is misplaced in `address_service.py`
**File**: `services/address_service.py:15`
**Severity**: LOW (code layout)

The `_RATE_LIMIT_DETAIL` module-level constant sits between the import
block and the unrelated `SUPPORTED_COUNTRY_CODES` set, separated from
its only caller (`_enforce_maps_rate_limit`) by one line. Cohesion with
the helper would read better.

Fix: either inline the literal as `detail=` inside
`_enforce_maps_rate_limit`, or move the constant to sit directly above
the helper. Cosmetic; do when next touching the file.

### 45. [LOW] `.gitignore` widened from filename to directory without comment
**File**: [platform/.gitignore](../../platform/.gitignore):145
**Severity**: LOW

`service-account-key.json` → `secrets/` is functionally fine (the
`service-account-key*.json` and `*-key.json` sibling patterns still
catch loose keys), but the diff reads as "why did a specific-file rule
become a directory rule?" without context.

Fix: add a one-line comment above the `secrets/` entry — e.g.
`# local secrets directory (service-account keys, tokens, etc.)` — so
the next reader understands the broadening.

### 79. [LOW] `load_default_rate_card_templates` returns loose `list[dict]`
**File**: [platform/services/rate_card_bootstrap.py:13](../../platform/services/rate_card_bootstrap.py)
**Severity**: LOW
Returning `list[dict]` loses the schema; callers can't tell what keys
exist without reading the validator.

Fix: define `RateCardTemplate` and `CardItemTemplate` as `TypedDict`s in
the same module and return `list[RateCardTemplate]`. Pure ergonomics — no
runtime change.

### 100. [LOW] Defensive `|| canEdit` clause in estimate-page row visibility is dead today
File: `portal/src/pages/NewEstimateWithActivityPage.tsx:879`
**Severity**: LOW

```tsx
{isEditMode && estimate && (allowedTransitions.length > 0 || canEdit) && (
```

`canEdit` is true only for `draft`/`review`. Both statuses have ≥2
transitions even after the non-admin Approve filter, so
`allowedTransitions.length > 0` is always true when `canEdit` is true.
The `|| canEdit` clause is dead today.

Keeping it is defensible — it documents intent ("show the row when we have
either buttons or a Save to render") and the cost is one boolean OR. But
if `isEditableStatus` or `TRANSITIONS_BY_STATUS` ever changes such that
the implication breaks, the clause would silently start mattering, which
is the kind of thing that surfaces only via a runtime regression.

Fix: either drop `|| canEdit` or add a one-line comment noting the
defensive intent. No runtime impact today.

### 117. [LOW] `_LLMHolder` class is more scaffolding than the use needs
**File**: [platform/agents/maple_public/service.py:99-127](../../platform/agents/maple_public/service.py)
**Severity**: LOW (style)

The lazy-init holder class plus `set_llm_for_tests` is more structure
than the single-LLM use needs. A module-level
`_llm: Optional[ChatOpenAI] = None` plus a getter and a test-only
setter would be flatter.

Fix: optional refactor; not blocking. Keeps the test injection path
clean either way.

### 120. [LOW] Unused CSS variable in widget palette
**File**: [website/widget/widget.css:6](../../website/widget/widget.css)
**Severity**: LOW (hygiene)

`--mw-bg-alt: #3b3f5c;` is declared but never referenced.

Fix: remove the line.

### 142. [LOW] Table heading weight drift (`font-medium` → `font-semibold`)
**Files**:
- [portal/src/components/common/EstimatesTable.tsx](../../portal/src/components/common/EstimatesTable.tsx)
- [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx)
- [portal/src/pages/PeoplePage.tsx](../../portal/src/pages/PeoplePage.tsx)

**Severity**: LOW

The 2026-05-01 "apply emerald-100 heading color" change also bumped
`<th>` font weight from `font-medium` to `font-semibold` while
recoloring. The user only asked for a color change. Other tables in
the app still use `font-medium` headers, so this is now inconsistent.

Fix: pick one and apply globally. Either revert these three files to
`font-medium`, or sweep the rest of the codebase up to `font-semibold`.

### 153. [LOW] `_PolicyShortCircuit.response` field name overloaded
**File**: [platform/agents/orchestrator/service.py:188](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (naming clarity)

Found by `/code-review` 2026-05-02 after the #12 extraction landed. The
`response` field on `_PolicyShortCircuit` carries either a refusal
message (negative case — bulk-delete / equipment / category-management)
or `None` (positive `list_material_categories` case, where
`_build_short_circuit_response` hardcodes `"I can help you with that."`).
The polymorphic meaning isn't obvious from the field name and the class
docstring doesn't mention it.

Fix: either rename to `clarification` to match the legacy 5-tuple's
last-position semantics in `_classify_with_rules`, or add a one-line
note in the docstring: "None for positive routings; refusal copy for
negative routings." Cosmetic only — behavior is correct and tested.

### 154. [LOW] `_TopicFlags.property` field name shadows Python builtin
**File**: [platform/agents/orchestrator/help_handler.py:38](../../platform/agents/orchestrator/help_handler.py)
**Severity**: LOW (naming clarity)

Found by `/code-review` 2026-05-02 after the #150 split landed. The
`_TopicFlags` dataclass field `property` shadows the `property` builtin
within the dataclass scope. Attribute access (`flags.property`) is
safe, but if anyone later writes a bare `property` reference inside
`help_handler.py` they'll get the boolean instead of the decorator.

Fix: optional. Either accept the shadowing trade-off (current state
keeps symmetry with the other domain flags), or rename every flag to
`is_*` for consistency (`is_property`, `is_contact`, etc.).

### 185. [LOW] Redundant `httpx.TimeoutException` in narrowed except tuple
**File**: [platform/services/address_service.py:366, :409, :468](../../platform/services/address_service.py)
**Severity**: LOW (style)

`httpx.TimeoutException` is a subclass of `httpx.HTTPError` (via
`RequestError`), so the tuple `(httpx.HTTPError, httpx.TimeoutException)`
is redundant — the second arm never matches. Harmless and explicit;
matches the [#41](code-review-followups-archive.md)
followup wording exactly.

Fix: optional simplification to `except httpx.HTTPError:`. Keeping the
explicit tuple is documentary, so this is style-only. Don't fix in
isolation; roll into any future address-service edit.

### 186. [LOW] Non-null assertion on `call.payload` in `handleStatusChange`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx:478](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW (type safety)

`await estimatesApi.update(id, call.payload!)` uses `!` to assert
`payload` is defined inside the `kind === "update"` branch. Type-safe
in practice because `resolveStatusChangeApi` always returns a payload
when `kind === "update"`, but a future change that returns
`{ kind: "update" }` without a payload would break the invariant
silently.

Fix: tighten `StatusChangeApiCall` into a discriminated union so the
relationship between `kind` and `payload` is encoded in the type:

```ts
export type StatusChangeApiCall =
  | { kind: "archive" }
  | { kind: "unarchive" }
  | { kind: "update"; payload: { status?: string; approved_by?: string } };
```

`call.payload` is then provably defined inside the `else` branch, the
`!` goes away, and `StatusChangeApiKind` becomes the narrowable
discriminator. ~10 lines in `lib/estimateStatus.ts` plus one cleanup at
the call site.

### 187. [LOW] Redundant `&& property` truthy check in property-info card
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx:1080](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW (dead code)

The address-link branch reads
`{selectedPropertyData?.street && property ? (...) : (...)}`, but the
entire block is already gated on `{property && (...)}` at line 1076,
so `&& property` inside the inner ternary is unreachable-to-falsify.
Harmless, but it implies a guard that doesn't exist.

Fix: simplify to `selectedPropertyData?.street ? (...) : (...)`. One-line
edit — roll into any future Property card edit.

### 193. [LOW] Trailing whitespace in `ENTERPRISE_DISPLAY.features`
**File**: [portal/src/lib/billing-plans.ts](../../portal/src/lib/billing-plans.ts) line 128
**Severity**: LOW (cosmetic)

`"Custom configuration"    ` has 4 trailing spaces. Linters and diff
tools flag this; harmless at runtime.

Fix: trim to `"Custom configuration"`.

### 203. [LOW] Drop the `event_type or "unknown"` defensive branch
**File**: `platform/routers/stripe_webhooks.py:65`
**Severity**: LOW

Signature verification has already passed, so the event is well-formed. A missing `type` would be a Stripe SDK bug, not a runtime expectation. The defensive `or "unknown"` lets a malformed event get persisted with a placeholder label.

Fix: `event_type = event_dict["type"]` and let the KeyError bubble.

### 211. [LOW] Remove or use `publishable_key_hint`
**File**: `portal/src/api/billing.ts:38-41`
**Severity**: LOW

`SetupIntentResponse.publishable_key_hint` is declared but never read. Publishable key comes from `VITE_STRIPE_PUBLISHABLE_KEY` only. Dead field.

Fix: either remove from the type, or use it as a runtime sanity check ("BE hint disagrees with FE env" → log warning) inside `getStripePromise`.

### 212. [LOW] Drop `opacity-95` on coming-soon plans
**File**: `portal/src/components/billing/PlanPickerGrid.tsx:152`
**Severity**: LOW

A 5% reduction is visually indistinguishable from full opacity. The intent is clearly to dim Coming-Soon plans. Either drop the prop or strengthen.

Fix: `opacity-70` or remove `dimWhenComingSoon` if the "Coming Soon" badge is enough.

### 215. [LOW] Drop redundant 5000-char client check in EnterpriseContactModal
**File**: `portal/src/components/billing/EnterpriseContactModal.tsx:56-58`
**Severity**: LOW

`MESSAGE_MAX_LEN` is already enforced via `maxLength` on the textarea, making the explicit length check redundant defense.

Fix: remove the duplicate check, or add a comment confirming it matches the BE `enterprise-contact` endpoint validation.

### 233. [LOW] `_LABEL_PATTERNS` is a mutable class-level dict
**File**: [platform/agents/property/service.py:375](../../platform/agents/property/service.py)
**Severity**: LOW

Class-level `Dict[str, List[str]]` is allocated once and is technically
mutable. Today nothing mutates it, but a future `_extract_label_fields`
edit that did `self._LABEL_PATTERNS[field].append(...)` would silently
corrupt subsequent calls (and other instances).

Fix: either annotate as
`_LABEL_PATTERNS: Final[Mapping[str, Sequence[str]]] = ...` (importing
`Final` and `Mapping` / `Sequence` from `typing`) or convert the
inner `List[str]` values to tuples. Cosmetic; safe today.

### 252. [LOW] In-function imports in `services/billing/webhook_handlers.py`
`handle_invoice_paid` does `from models import User` inside the function
for the per-user token-counter reset path. The rest of the module imports
models at the top. Mixed style.

Fix: move to module-top imports for consistency. Trivial cleanup; bundle
with the next functional change to this file.

### 255. [LOW] Redundant `hover:bg-emerald-600` on current-plan button
`portal/src/components/billing/PlanPickerGrid.tsx:134` — the
`buttonClass` for the current plan includes both `bg-emerald-600` and
`hover:bg-emerald-600`. The hover variant matches the base, and the
shared `Button` component already sets `disabled:pointer-events-none`,
so hover can never fire on the disabled current-plan button anyway.

Fix: drop `hover:bg-emerald-600` from the `isCurrent` branch of
`buttonClass`. Keep `bg-emerald-600 text-white border-transparent
disabled:opacity-100 w-full`.

### 265. [LOW] Generic `data-toolbar-visible` attribute could collide
`portal/src/styles/index.css:6` and
`portal/src/components/common/MarkdownDescriptionEditor.tsx:124` —
the CSS rule keys off a non-namespaced `data-toolbar-visible`
attribute. Low collision risk today, but the name is generic enough
that another component could reuse it. Rename to
`data-mdx-toolbar-visible` in both the CSS rule and the wrapper so
the contract is explicit.

### 268. [LOW] `<AiPanelProvider>` top-level wrap not re-indented in PortalLayout
`portal/src/components/Layout/PortalLayout.tsx:966` and `:1925` —
when `AiPanelProvider` was hoisted to wrap the whole layout return,
the inner `<div className="flex h-screen …">` was left at the same
indentation as the new provider tag. Functionally fine, just
inconsistent. Fix: Prettier pass over the file.

### 273. [LOW] NBSP literal in `markdownBlankParagraphs.ts` is invisible in source, no test imports the constant
`portal/src/components/common/markdownBlankParagraphs.ts:7` —
`NBSP_PARAGRAPH = " "` contains a literal U+00A0 byte-different
from regular space but visually identical. The test file
reconstructs its own `NBSP = " "` constant rather than importing
this one, so a slip on either side passes silently. Fix: either
export `NBSP_PARAGRAPH` and import it in the test for a single
source of truth, or write the constant as
`String.fromCharCode(0xA0)` so it's unambiguous in source.

### 276. [LOW] Unused `_showNextTime` parameter in `handleConfirmSeatsOverage`

`portal/src/pages/SettingsPage.tsx:handleConfirmSeatsOverage` accepts a
`_showNextTime: boolean` parameter that's intentionally unused — the
user-invite dialog has no "Show this next time" checkbox, so the value is
always `true` and irrelevant. The underscore prefix signals intent but the
`OverageWarningDialog.onConfirm` interface forces the awkward signature.

Fix: narrow `OverageWarningDialog`'s `onConfirm` to `() => void` when
`resource !== "estimates"`. Two cleanest options: (a) make `onConfirm`'s
arg optional, (b) split into two prop callbacks (`onConfirm` for non-checkbox
variants, `onConfirmWithPref` for estimates). Either path touches all three
call sites — defer until the dialog API is touched for another reason.

### 280. [LOW] Redundant `readOnly` on disabled overage-notification checkbox

`portal/src/pages/SettingsPage.tsx` (~line 1452, inside the Account-tab
read-only view) renders the "Show estimate overage notification" checkbox
with both `disabled` and `readOnly`. `disabled` already prevents interaction
and excludes the input from form submission; `readOnly` has no defined effect
on `<input type="checkbox">` per the HTML spec — it's a no-op there.

Fix: drop `readOnly`. Cosmetic only; the rendered behavior is identical
either way. Worth doing the next time anyone touches this block to keep
the JSX honest about what the attributes actually do.

### 282. [LOW] `"hard_cap_reached"` string literal repeated in `routers/agents.py`

The literal appears at two sites in `orchestrate_agent_endpoint` — once in
the `code == "hard_cap_reached"` guard and once as the `intent=` kwarg passed
to `_maple_credits_refusal_payload`. A typo on one side silently breaks the
wiring.

Fix: promote to a module-level constant near the existing refusal helpers
(`HARD_CAP_INTENT = "hard_cap_reached"`). The existing `needs_payment_method`
/ `needs_acknowledgment` codes have the same duplication so apply the same
treatment if you ever pull this thread.

### 297. [LOW] Hoist `optionalString` to module scope
**Where:** `website/functions/index.js:77`.

**Why:** Pure helper recreated on every request. Negligible perf cost but belongs at module scope alongside `escapeHtml`.

### 299. [LOW] Drop `escapeHtml(label)` on hardcoded labels
**Where:** `website/functions/index.js:183`.

**Why:** `htmlDetails` escapes label values that are all string literals defined two lines above. Defensive but unnecessary; misleads a reader into thinking labels could be untrusted.

**Suggested fix:** Drop the `escapeHtml(label)` call (keep `escapeHtml(value)`). Or move labels to a top-level constant to make their hardcoded nature explicit.

### 313. [LOW] Inconsistent null-check style across overage sentinel (`=== null` vs `!= null`)
**Where:** `portal/src/utils/overage.ts:58` vs `portal/src/components/settings/BillingTab.tsx`

**Issue:** `overage.ts` uses loose `!= null` (catches `undefined` too); `BillingTab.tsx` uses strict `=== null`. Both are correct for their context, but the inconsistency across files sharing the same sentinel contract is a readability trap.

**Fix:** Standardise on `=== null` / `!== null` across both files when the intent is to test for the unlimited sentinel specifically.

### 324. [LOW] Language codes `"en"` / `"es"` are bare string literals
`services/translation.py` and the two endpoint handlers (`routers/agents.py`,
`routers/public_maple.py`) compare against `"en"` / `"es"` inline in several
branches. `SUPPORTED_TARGET_LANGS` already centralizes the supported set; a
small `LANG_EN = "en"` constant (or an enum) would remove the remaining magic
strings and make adding a language a touch safer. Cosmetic — no behavior change.

### 333. [LOW] `_residual_is_field_restatement` filler-word heuristic is undocumented at the call site
The filler list (`add|set|update|link|the|a|an|it|to|with|please|me|my`) is a
heuristic; values that reduce oddly (a property literally named "My Place"
reduces to "place" and still passes — correct today) deserve a pointer to the
§9.4 soft-negative follow-up so the two heuristics evolve together.

### 348. [LOW] Defensive `'Sent'` fallback in `_authorize_status_transition` is logically unreachable
Added 2026-06-11. `agents/estimate/crud_handlers.py::_authorize_status_transition`:
in the `involves_sent and not is_owner_or_admin` refusal, the
`current_status.value if current_status else 'Sent'` else-branch can't be hit —
when `target_status` isn't Sent-like, `involves_sent` can only be True via
`current_status`, so it can't be `None` there. Kept deliberately because
`current_status` is typed `Optional[EstimateStatus]` and mypy requires the
guard (an inline comment marks it typing-only). Fix (optional): narrow the
parameter type instead, e.g. split the gate so the unsend branch receives a
non-Optional `EstimateStatus`. Not worth doing on its own — fold into #347's
split if that happens.

### 353. [LOW] Plan file line references drift after implementation

`documentation/development/plans/overage-acknowledgment-dialog.md` references
specific line numbers (e.g. "SettingsPage.tsx:1042-1062") that shifted during
implementation. Plan files are point-in-time snapshots, so post-merge readers
will hit off-by-a-few-lines mismatches when navigating to the cited code.

Fix: optional housekeeping. Either refresh the line refs once after merge or
add a "post-implementation: line refs may be stale, search by function name"
disclaimer to the plan template. Low priority since plans aren't authoritative
documentation.

### 392. [LOW] platform/routers/feedback.py — backend /feedback route + Trello service are now dead code
With portal/src/api/feedback.ts deleted, nothing calls POST /feedback anymore. The feedback router, trello_service, and the TRELLO_* config keys (trello_api_key/secret/api_token + three list IDs in config.py) are dead code in platform — an unused authenticated route that still writes to Trello if hit, plus live Trello credentials in prod env for a retired feature.
**Suggested fix:** Separate platform change: remove routers/feedback.py (+ main.py registration), trello_service, the TRELLO_* Settings fields (or keep them declared-but-unused like trello_secret if .env files still carry them), and their tests; then revoke the Trello API token. Also retire the golden-sprouting-adleman plan doc as superseded.

### 394. [LOW] platform/dependencies.py — `resolve_active_staff` return annotation
Return type isn't precisely annotated for the staff/None resolution path. Tighten to the honest `StaffUser | None` per the mypy-playbook pattern.

### 472. [LOW] portal/src/components/properties/PropertyActivityPanel.tsx:233 — redundant effect dependencies
The fetch effect lists `activeFilter.length`, `estimateFilter` and `taskFilter`
alongside `cacheKey`, which already encodes the active filter. Changing the inactive
tab's filter re-runs the effect for no reason; it is harmless only because the cache
absorbs it.
**Suggested fix:** depend on `cacheKey` alone (plus `propertyId`, `activeTab` and
`reloadToken`), and read the filters through a ref or recompute them inside the effect.

### 487. [LOW] platform/services/brevo_lifecycle_reconcile.py:184 — `dict[Any, Company]` where the key type is known
`_collect_companies` returns `dict[Any, Company]`. The key is `Company.id`, a
`PydanticObjectId`. `Any` silently disables checking at every call site that indexes into it.
**Suggested fix:** annotate `dict[PydanticObjectId, Company]` and import the type from
beanie. If mypy then objects that `company.id` is `Optional`, the existing
`if company.id is not None` filter already narrows it.

### 488. [LOW] platform/services/brevo_lifecycle.py:194 — `reset_cache` docstring claims a caller it does not have
The docstring says "For tests and for the backfill", but the only callers are
`tests/conftest.py` and `tests/test_brevo_estimate_hook.py`. The backfill never calls it. A
future reader may preserve behaviour for a caller that isn't there.
**Suggested fix:** either drop "and for the backfill" from the docstring, or have the backfill
actually call it — it arguably should, since it rewrites claims out from under a warm cache.
Since the backfill only ever runs as a standalone script, the cache is cold anyway and the
docstring is simply the thing to correct.

### 497. [LOW] platform/services/sparse_update.py:68 — `merge_onto` is unused by production code
The routers use `existing.model_copy(update=...)` directly; `merge_onto` exists only in the
module docstring and its unit tests. Dead public API invites drift between the documented
recipe and the real one.
**Suggested fix:** use `merge_onto` at the three call sites that inline `model_copy`
(materials, labours, properties), or delete the helper and update the docstring example.

### 508. [LOW] platform/services/readable_id.py — `ESTIMATE_CODE_CAPTURE` has no callers
Defined but never imported anywhere in the codebase. Pre-existing, not
introduced by the task-id work, but the `TASK_CODE_CAPTURE` added alongside it
**is** used (by `_TASK_CODE_PATTERNS`), so the dead one is now conspicuous
sitting next to a live twin.
**Suggested fix:** delete it, or annotate it as an intentional public constant.
Deleting is safer — it is trivially re-addable, and the estimate half of the
file otherwise mirrors the task half exactly.

### 510. [LOW] platform/services/readable_id.py — sibling readers have different shapes
`estimate_code_in_text` returns the first match via `.search`, while
`task_codes_in_text` returns every match (ordered by position) and
`task_code_in_text` wraps it. Two readers with the same job and different
contracts is a milder form of the drift #505 was about — and the task side now
carries a positional-ordering fix the estimate side does not.
**Suggested fix:** add `estimate_codes_in_text` and define
`estimate_code_in_text` on top of it, mirroring the task pair. Cheap, and it
keeps the two halves of the file symmetrical. Worth doing next time the estimate
half of that file is touched.

### 531. [LOW] portal/src/pages/MaterialsPage.tsx:60 — `onDuplicate` is optional with no caller that omits it
Removing the mobile card's `<MaterialsActionsMenu>` (phones are now a read-only catalog) left
exactly one call site, at line 678, which always passes `onDuplicate`. The `onDuplicate?: () =>
void` optionality and the `action?.()` no-op it enables are now unreachable. Worth noting that the
same change silently FIXED a latent bug: the removed mobile instance omitted `onDuplicate`, so its
always-rendered "Duplicate" menu item did nothing when tapped.

**Suggested fix:** tighten the prop to `onDuplicate: () => void` so a future caller that forgets it
is a type error rather than a dead menu item.

### 532. [LOW] portal/src/pages/MaterialsPage.tsx:774 — `justify-between` row left with a single child
With the actions menu removed from the mobile card, this row holds only the "Show Sizes" toggle,
so `justify-between` no longer distributes anything. Renders correctly (the button sits left) but
the class now misdescribes the layout.

**Suggested fix:** drop `justify-between` from that div, leaving `flex items-center pt-3 border-t
border-gray-200`.

### 543. [LOW] portal/src/lib/viewport.ts:1 — module docstring still describes a single gate

The header reads "The shared phone-viewport gate" and explains only `PHONE_BREAKPOINT_PX` / `md`.
The module now exports two gates at two breakpoints, and the `md` explanation reads as though it
governs everything in the file — misleading for the next reader choosing between them.

**Suggested fix:** extend the header to name both gates and say when to reach for each —
`useIsPhone` for `md:`-stacked layouts, `useIsBelowSm` for `sm:`-stacked ones — with the rule that
the JS gate must match the breakpoint in the component's Tailwind classes.

### 549. [LOW] portal/src/components/onboarding/CsvUploadStep.tsx:29 — required props that two of the three modes ignore

`sampleCsvUrl` and `onUpload` are non-optional, but `infoOnly` and `standardOnly` never read either —
the sample link and the file input are both inside the `infoOnly || standardOnly ? null :` branch. So
`OnboardingPage` passes `sampleCsvUrl={MATERIALS_SAMPLE_CSV_URL}` and a live `onUpload` to screens
that cannot upload, which reads as though they can.

**Suggested fix:** make both optional and have the normal-mode branch require them (a discriminated
union on the mode would be most honest, but optional props plus the existing branch guard is enough).
Then drop the dead `sampleCsvUrl`/`onUpload` props from the three phone call sites in
`OnboardingPage.tsx`.

### 571. [LOW] "5,000" hard-coded in the additional-info 422 message
`platform/routers/estimate_documents.py:117` — The message duplicates `MAX_ADDITIONAL_INFO_CHARS`, so the two can drift.

**Suggested fix:** `detail=f"Additional information can be at most {MAX_ADDITIONAL_INFO_CHARS:,} characters."`

### 572. [LOW] "10 MB" hard-coded in the doc-image size message
`platform/services/estimate_doc_images.py:60` — Not derived from `MAX_DOC_IMAGE_FILE_SIZE_BYTES`; the test patches the cap to 10 bytes and still asserts "10 MB".

**Suggested fix:** `f'"{name}" is larger than {MAX_DOC_IMAGE_FILE_SIZE_BYTES // (1024 * 1024)} MB.'`

### 573. [LOW] Doc-image file-name limit `200` is an unnamed literal
`platform/services/estimate_doc_images.py:66` — `name[:200]` is a magic number.

**Suggested fix:** `MAX_DOC_IMAGE_FILE_NAME_CHARS = 200`.

### 574. [LOW] `max-age=3600` literal on the doc-image response
`platform/routers/estimate_documents.py:267` — A magic number inside the header string.

**Suggested fix:** `DOC_IMAGE_CACHE_SECONDS = 3600` and build the header from it.

### 575. [LOW] `_normalized_bucket_name` is imported privately across modules
`platform/services/estimate_doc_images.py:33` — The private helper from `services.company_logo` now has a third caller outside that module (after `support_attachments.py`).

**Suggested fix:** Rename it to the public `normalized_bucket_name` (or move it to `services/firebase_storage.py`) and update the callers.

### 580. [LOW] `prepare_doc_template` docstring doesn't mention `additional_info`
`platform/routers/estimate_helpers/doc_versions.py:222` — It doesn't say that `additional_info` fills `{{NOTES}}` or that `Estimate.notes` is no longer read.

**Suggested fix:** Add one sentence saying so.

### 585. [LOW] `Form([])` / `File([])` mutable list defaults on generate-doc
`platform/routers/estimate_documents.py:195` — Matches the mutable-default pattern. Safe in practice because pydantic copies field defaults.

**Suggested fix:** `Form(default_factory=list)` / `File(default_factory=list)`.

### 586. [LOW] `get_doc_image` has no return annotation
`platform/routers/estimate_documents.py:247` — A new public route without `-> Response` (its sibling `generate_google_doc` now has one).

**Suggested fix:** Add `-> Response`.

### 587. [LOW] `find_doc_image` has no docstring
`platform/routers/estimate_helpers/doc_versions.py:321` — Undocumented that it searches every version and returns the first match.

**Suggested fix:** Add a one-line docstring.

### 588. [LOW] `doc_image_storage_path` has no docstring
`platform/services/estimate_doc_images.py:152` — The path layout is load-bearing for company scoping and cleanup, and isn't documented.

**Suggested fix:** Add a one-line docstring.

### 589. [LOW] `store_doc_image` has no docstring
`platform/services/estimate_doc_images.py:163` — Undocumented that the blob gets no public download token and the content type is always JPEG.

**Suggested fix:** Add a one-line docstring.

### 590. [LOW] `read_doc_image` has no docstring
`platform/services/estimate_doc_images.py:176` — Undocumented that it raises on a missing blob, which the router relies on.

**Suggested fix:** Add a one-line docstring.

### 591. [LOW] `ProcessedDocImage` has no docstring
`platform/services/estimate_doc_images.py:47` — Undocumented that width and height are post-resize pixels.

**Suggested fix:** Add a one-line docstring.

### 599. [LOW] "10MB" hard-coded in the Documents dialog helper text
`portal/src/components/estimates/DocImagePicker.tsx:70` — Duplicates `MAX_DOC_IMAGE_BYTES`, so copy and check can drift.

**Suggested fix:** Export `MAX_DOC_IMAGE_MB = MAX_DOC_IMAGE_BYTES / (1024 * 1024)` from `docVersions.ts` and build the text from it.

### 600. [LOW] "10MB" hard-coded in the image rejection message
`portal/src/components/estimates/docVersions.ts:39` — Same drift risk as #599.

**Suggested fix:** Use `MAX_DOC_IMAGE_MB` in the message.

### 609. [LOW] Estimate Brevo hook docstring names only one of the two raw writes that bypass it
`platform/models/estimate.py:617` — It says one hook catches every write path and names `append_doc_version_to_estimate`'s raw `$push` as the only write no event sees (which now runs the after-Update actions itself via `as_written`). `remove_doc_version_from_estimate` also writes a raw `$pull` that fires nothing. Harmless, since removing a version can't cross a lifecycle line, but unstated.

**Suggested fix:** Add: "`remove_doc_version_from_estimate`'s raw `$pull` fires nothing either; removing a version cannot cross a lifecycle line."

### 622. [LOW] `ClientContext` has no docstring
`platform/routers/agent_helpers/client_context.py:48` — The allowlist contract isn't stated on the model.

**Suggested fix:** Add a one-line docstring naming the allowlist contract.

### 623. [LOW] `context_scope` module docstring is out of date
`platform/routers/agent_helpers/context_scope.py:3` — It still says `context_payload` is populated from the client's request context.

**Suggested fix:** Say state is server-owned and the client supplies only the allowlisted `client_context`.

### 624. [LOW] `create_note_as` points work-item callers to the wrong function
`platform/services/notes.py:169` — Its docstring and `ValueError` say to use `create_note()` for work-item notes, but server-side callers should now use `create_work_item_note_as`.

**Suggested fix:** Update the message and the docstring.

### 739. [LOW] `load_conversation` is used only by tests
`platform/routers/agent_helpers/conversation_store.py:75` — Production re-implements it in `routers/agents.py:_load_conversation_context` (`find_one` + `loaded_from`), so the tests cover a path production never calls. (review 2026-09-27 #69)

**Suggested fix:** Have `_load_conversation_context` call `load_conversation`, keeping its try/except and ContextVar set.

### 749. [LOW] The `assigned_to` parameter is now unused
`platform/agents/task/base.py:204` — No caller passes `assigned_to` to `_list_conditions`, `_list_tasks_db` (:243) or `_count_tasks_db` (:275) any more; `extra` replaced it. (review 2026-09-27 #79)

**Suggested fix:** Remove the parameter from all three.

### 810. [LOW] The router imports an agent module's private `_recalculate_sub_total`
`platform/routers/agent_helpers/template_estimate.py:26` — The sized-template fix (#631 review) imports `agents.estimate.work_item_field_handlers._recalculate_sub_total`, a leading-underscore helper, into `routers/agent_helpers`. That is the cross-module private import #575 and #750 flag elsewhere. It ties the router to one agent mixin's internals, for a one-line wrapper around `work_item_breakdown(unburdened(item)).total`, which already lives in the routers' own `routers/estimate_helpers/calculations.py`. LOW: no behavioral effect. (review 2026-10-03, wrong-answers batch 4 round 3 #1)

**Suggested fix:** In `template_estimate.py`, import `unburdened` and `work_item_breakdown` from `routers.estimate_helpers.calculations` and write `job_item.sub_total = work_item_breakdown(unburdened(job_item)).total`. Drop the `_recalculate_sub_total` import. The test needs no change.

### 814. [LOW] `title_reference.py` ends with a blank line
`platform/agents/estimate/title_reference.py:536` — `find_named_estimates` was appended with an extra trailing newline, so the file ends "\n\n". pycodestyle's W391; the project's ruff rules don't include W, so no gate catches it. Style only. (review 2026-10-04, slow-lookups batch #2)

**Suggested fix:** Remove the final empty line so the file ends with a single newline after `return [by_id[i] for i in ids if i in by_id]`.

### 820. [LOW] The planner design's §5.1 still treats langchain's cache support as unknown
`documentation/development/plans/2026-10-02-maple-planner-shadow-design.md:445` — "Getting it onto the wire" says it is not known whether langchain-openai 1.6.6 keeps a content-block breakpoint, and plans a raw `AsyncOpenAI` fallback (step 6a). Step 0 established it does: `ChatOpenAI` has a `prompt_cache_options` field and `_format_message_content` keeps `prompt_cache_breakpoint`, pinned by `platform/tests/test_llm_prompt_cache.py`. The plan describes a fallback that will never be needed. (review 2026-10-07 #8)

**Suggested fix:** Replace the two "Getting it onto the wire" bullets with: "langchain-openai 1.6.6 supports both natively (`ChatOpenAI.prompt_cache_options`; `prompt_cache_breakpoint` on a text block), pinned by `tests/test_llm_prompt_cache.py`", and reduce step 6a to the live `cached_tokens > 0` check.

### 909. [LOW] Redundant local import of `create_needs`
`platform/agents/planner/asks.py:324` — It repeats the module-level import. (review 2026-10-11 #89, deferred)

**Suggested fix:** Remove the local import.

### 915. [LOW] `_question_text` never uses its `question` parameter
`platform/agents/planner/kept_questions.py:65` — Dead parameter. (review 2026-10-11 #95, deferred)

**Suggested fix:** Remove it from the signature and the call.

### 918. [LOW] `_WRITE_FIELDS = {}` leaves dead code in `_uncovered_write`
`platform/agents/planner/execute.py:212` — The allowed/unread tail can't fire. (review 2026-10-11 #98, deferred)

**Suggested fix:** Remove `_WRITE_FIELDS` and that tail.

### 921. [LOW] A dead copy of `_or_join`
`platform/agents/estimate/crud_handlers.py:173` — Nothing references it after the move to `estimate_status.or_join`. (review 2026-10-11 #101, deferred)

**Suggested fix:** Delete it.

### 925. [LOW] A stray third blank line
`platform/agents/task/operations.py:64` — Extra blank line before `class TaskOperationsBase`. (review 2026-10-11 #105, deferred)

**Suggested fix:** Remove it.

### 927. [LOW] A comment points to where the lock's words used to live
`platform/services/maple_outcomes.py:137` — It names `crud_handlers._locked_status_edit_refusal`. (review 2026-10-11 #107, deferred)

**Suggested fix:** Point it at `estimate_status.locked_edit_text`.
