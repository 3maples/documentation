# Maple planner switchover: the executor and the per-company switch — plan

**Date:** 2026-10-07 · **Status:** Approved 2026-10-07 (S1–S5). Build starts at phase 1.
**Builds on:** [`2026-10-02-maple-planner-shadow-design.md`](2026-10-02-maple-planner-shadow-design.md)
§12 (switchover), D11 (the per-company field), D20 (Dev first, then production)

## 1. Goal

Let a company's Maple turns run on the planner — plan, resolve, check, **execute**
— instead of today's pipeline, chosen per company. Use it in Dev on Simon's
company until it is clearly better than today's Maple, then every Dev company,
then release, then production company by company (D20).

What it is not: a rewrite of what Maple *does*. Every write still goes through
today's write path, every reply still names its target in today's words, and
every policy (deletes ask, overage asks, Draft/Review lock, roles, tenant scope)
is the one already enforced.

## 2. What the code looks like today

Two read-only surveys of the code (2026-10-07) found:

- **The branch has one clean place:** `routers/agents.py::_orchestrate_turn`,
  after the `_finalize_result` closure (:1348) and before `decide_turn`
  (:1356). Everything the planner needs is built by then: the English and
  original message, `merged_context` with page signals applied and
  `turn_index` bumped, the loaded `company_doc`, the LLM context (billing to the
  company), and the version-safe save. Both branches end in the same
  `_finalize_result` → `finalize_orchestrate_result`, which owns anchors,
  `last_request`, chat history, `open_question`/chips and the save.
- **Few of today's handlers take resolved values.** Most agent handlers re-read
  the message — positional picks, `is_count_query`, field-then-value replies,
  `confirms(message)` for deletes, list filters that exist only as text
  (city, role, price range, sort), and creates that parse their own clauses.
  The catalog agents also resolve their own targets (with fuzzy matching).
  Calling them with the planner's resolved record would mean passing text back
  in, which re-introduces the reading the planner replaces.
- **Some are already callable with values:** `_run_edit_commands` (edit
  executor, by code + `EditCommand`s), `_handle_update_estimate_status_transition`
  (status tuple + forced code), `_handle_generate_work_item`, the task
  sub-handlers (`resolved_task` + value), `_handle_get_task`,
  `_handle_convert_task`, `record_notes._add` / `._list` (a `NoteParent`),
  `catalog_figures._answer` (a `CatalogAsk`), `focus_questions.answer`, the
  metric internals (`_resolve` / `_fetch` / `_word` with a `MetricAsk`),
  `run_task_counts` + `group_counts_text`, `_finalize_template_estimate`, the
  material `_handle_size_command(SizeCommand)`, the `_via_api` write cores of
  the catalog agents, and the meta replies.
- **Some plan fields have no handler at all** (§8).

## 3. Decisions (Simon, 2026-10-07)

| # | Question | Chosen | Rejected |
|---|---|---|---|
| S1 | A plan with an op the executor doesn't cover yet | **Fall back to today's pipeline for that turn**, decided on the whole plan *before anything runs*. The switch is usable from phase 1 and coverage grows op by op; every fallback is logged, so the Dev export shows what's left | Build every op before anyone can switch |
| S2 | How the executor reaches a write | **Extract value-taking cores from today's handlers** (`parse → core(values) → reply`), called by both pipelines — one write path, identical replies, and at retirement only the text-parsing wrappers are deleted | A new planner-only handler per op (two write paths until retirement) |
| S3 | What happens after the planner asks something | **Confirmations resume a stashed plan** (delete, overage, stale target, removal — the action is already decided, only the yes is missing). **Everything else is re-planned**: after a "which one?", a missing value or a `clarify`, the next turn's planner reads the question and the history and plans the whole request again | Stash and resume every question |
| S4 | Translation | **Decided (Simon, 2026-10-07): kept, both ways, for planner companies too.** Inbound: the policy's stray-reply check (`policy._stray_reply`: a bare yes/no with nothing open) reads English, as do `chat_history`, the unanswered tracker and the session files; and it costs nothing for English (the prefilter skips the call). Outbound: the executor's replies are today's English templates | Drop inbound translation for planner companies |
| S5 | Multi-action plans (up to five actions) | **Run them in order, all-or-nothing on checks, one reply per action joined in order**; each action moves its own anchor | Refuse compound plans at first |

S1, S2, S3 and S5 as recommended; S4 kept translation (above).

## 4. The switch

- **Field:** `Company.maple_pipeline: Optional[str] = None`. A plain string,
  not a `Literal`: a bad stored value must never fail validation of the whole
  Company document (that would break `/auth`). It is read by
  `maple_pipeline_of(company) -> Literal["current", "planner"]`: anything other
  than `"planner"` — missing, `None`, unknown, unreadable, or no `company_doc`
  (it is `None` in `asyncio.run` tests) — means current. No migration, no
  backfill (D11).
- **Set by** `scripts/set_maple_pipeline.py <company-id> planner|current`,
  `--dry-run` by default, `--apply` to write; it prints the company's name.
- **Taking effect:** the branch reads it each turn, so a switch or a rollback
  takes effect on the next turn.
- **Who answers an open question:** the pipeline that asked it. Every question
  the planner pipeline stores carries `"pipeline": "planner"`. On a planner
  company, a turn with an open question **not** tagged planner (a question the
  current pipeline asked before the switch, or in a fallback turn) goes to the
  current pipeline. On a current company, a planner-tagged question (left by a
  rollback) is dropped, with "I've lost track of that question — could you ask
  again?".
- **Shadow:** off for a planner company (`take_snapshot` already skips by
  company; it gains a pipeline check). Planner-vs-planner turns would be noise
  and would bill no one.

## 5. The planner turn

`agents/planner/turn.py::run_planner_turn(...) -> Optional[dict]` — called at the
branch; returns a result dict for `_finalize_result`, or `None` to fall back.

1. `plan_turn(original_message, context_without_this_turns_user_line)` — under
   the request's LLM context (billed to the company, feature
   `maple.planner.plan`), never `tenantless_llm_context`.
2. On a planner error (timeout, invalid plan): **fall back** (S1), logged as
   `fallback: planner_error`.
3. `check_plan(...)`.
4. **Questions are dropped here, as `decide_turn` would:** if the plan doesn't
   answer an open question, `drop_all_questions`; if it does, the answered
   question is consumed. `question_keys_after_gate` is filled so
   `settle_after_turn` sees what was asked this turn.
5. **Coverage gate (S1):** every action's op (and the fields it sets) must be in
   the executor's `COVERED` table; otherwise fall back, logged with the op.
   Decided before anything runs, so a fallback never follows a partial write.
6. By the check's decision:
   - `refuse` → the refusal reply (the existing constants; §8 lists the
     reasons without one).
   - `clarify` → the planner's question as the reply, stored as a planner-tagged
     `value` question (re-planned next turn, S3).
   - `ask` (a name nothing matched, several matched, a missing value) → the
     question the policy names, stored as a planner-tagged `pick` (with
     `choices` + `candidate_ids`) or `value` record — shapes `open_questions()`
     already reads, so the panel's "Waiting for your answer" and chips work
     unchanged.
   - `confirm` (delete, stale target, removal, overage) → today's confirmation
     wording; the plan is stashed on a planner-tagged destructive `yes_no`
     record; a yes next turn executes the stash with `confirmed=True`, a no
     declines with today's words and `cancelled=True`.
   - `run` → execute (§6).
7. **The unanswered tracker** records the planner's own outcome
   (`maple_shadow.planner_outcome`, `pipeline="planner"`) instead of
   classifying the reply.

## 6. The executor

`agents/planner/execute.py`: `COVERED: Dict[str, Callable]`, one entry per op.
Each entry takes the action, its `ActionCheck` (resolved records) and the
context, calls a core, and returns `ActionResult(reply, result, listed, anchor)`.

- **Result dicts** use today's intent names (`schema.INTENT_OF_OP`) and agent
  labels, and today's `result` shape (`operation`, the entity sub-dict with
  `_id`/`name`), so `finalize_orchestrate_result`, `remember_request`,
  suggestions, the outcome classifier and the corpus asserts read them
  unchanged.
- **Anchors:** finalize moves one entity anchor per turn and, for
  `multi_intent`, only the estimate's. The executor moves each action's anchor
  itself (with finalize's own helpers — `anchor_estimate`, `stamp_anchor`) and
  hands finalize the last action's result.
- **Lists record their rows** with `format_and_record_list_response`, as every
  list handler must.
- **Follow-ups read the last plan, not the last text:** each read stores its
  action as `last_plan_read` (alongside today's `last_request`). `redo_last`
  and `refine_last` change that action's fields and run it again; `show_more`
  runs it with the next offset. No text rewrite.
- **Tenant scope:** the executor only receives ids the resolver found in the
  caller's company; the cores it calls must still scope by company. One today
  doesn't — `_delete_contact_via_api` uses a bare `Contact.get(id)`
  (`agents/contact/service.py:776`) — and is fixed in phase 4.

## 7. Phases

Each step: failing test first, scoped mypy and ruff, related tests, one commit.
Executor tests drive `run_planner_turn` with a **fixed plan** (a stub
`plan_turn`), so they are deterministic and need no LLM.

| Phase | Covers | Core work | Done when |
|---|---|---|---|
| **1. Switch and skeleton** | `unsupported`, `clarify`, `cancel`, `start_over`, `repeat`, `acknowledge`, `help`, `social`, `calculate` | `Company.maple_pipeline`, `maple_pipeline_of`, the script; the branch; `run_planner_turn` with the coverage gate and fallback; question tagging and the "who answers" rule; shadow off for planner companies; the planner's unanswered outcome; a `fallback` count in the Dev export | Simon's Dev company runs on the planner, every uncovered turn falls back, the endpoint tests for a current company are unchanged |
| **2. Reads** | `get_*` and `list_*` for every domain, `metric`, `dashboard`, `catalog_figure`, `task_count`, `list_work_items`, `get_work_item`, `work_item_field`, `list_work_item_lines`, `list_notes` | Extract each list's query core from its text handler (filters as values: city, role, price range, category, sort, count); `get_*.field` answers; `metric` via `MetricAsk` into the metric internals (mapping as `metric_spec.ask_from_spec` does); `dashboard` via the `_analytics_*` value functions; row recording | Every read in the acceptance corpus runs without fallback |
| **3. Follow-ups** | `show_more`, `redo_last`, `refine_last` | `last_plan_read`; paging for every list (today only tasks and rankings page) | "show more", "and last month?", "just the drafts" run on the stored plan |
| **4. Writes on a record** | `update_*` (catalog), `create_*` (catalog), `edit_estimate`, `set_status`, `unarchive_estimate`, `generate_work_item`, `add_note`, `update_task`, `convert_task`, `link` | Catalog creates/updates on the `_via_api` cores plus today's enrichment and reply templates; `edit_estimate` → `to_edit_command` → `_run_edit_commands` (fanning a `by: all` pick out to one command per work item); task fields through the sub-handlers, several in one action; a contact↔property and estimate→property link core; the tenant fix above | Every write in the corpus runs without fallback; the `after` DB checks pass |
| **5. Confirmations** | every `delete_*`, `delete_note`, stale-target asks, removal confirm | The stash-and-resume record; today's confirmation and decline wording; deletes by id (notes too — today's note delete works by position) | A delete asks, a yes deletes, a no leaves it, on every domain |
| **6. Estimates from scratch** | `create_estimate`, `apply_template`, `adjust_assumption` | `create_estimate` keeps `delegate_create_estimate` (overage, gathering, sufficiency, quota) but takes the resolved property and template as values; the overage yes resumes the stash, not a text replay | Creating from a description, a template and a property all run, overage asks |
| **7. The acceptance run** | — | The 271 acceptance conversations with the company switched and the planner live (`-m llm_e2e`), scored on reply fragments and `after` checks; each failure fixed or added to the parity's explained list | Simon judges the planner clearly better in Dev (§11 of the design) |

After phase 7: every Dev company → release → 3Maples' own production company →
two or three customers → everyone (design §12, D20). Retirement of today's
language reading is its own change, four weeks after the last switch.

## 8. Plan fields with no handler today

Each gets a core in the phase that covers its op, or the planner stops offering
it (a schema change, with a parity run):

- `convert_task.delete_task` — no delete-after-convert anywhere.
- `create_estimate.customer` — only a property is linked today.
- `apply_template.size` — scaling exists only when creating from a template.
- `edit_estimate` on **every** work item — `WorkItemRef` has no "all".
- Several task fields in one update — today one sub-op per message.
- `get_<record>.field` — the agents always return full details (material size
  aside); `get_estimate.field` lacks division, title and description.
- `list_notes` / `delete_note` on a work item or task, and a note by reference.
- A listed material or activity line — no line list records rows, so
  `resolve_line` always asks.
- `refine_last.sort` oldest / lowest total.
- Refusal copy for `notes_on_catalog`, `recurring` and `other`; `labour_rate`'s
  is inline (`agents/labour/service.py:959`) and becomes a constant.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Extracting cores changes today's behaviour | Today's handler calls the same core; its existing tests (and the routing snapshot) must stay green in the same commit |
| A fallback after a partial write | The coverage gate decides on the whole plan before anything runs |
| A question asked by one pipeline answered by the other | The `pipeline` tag and the routing rule in §4; a rollback drops planner-tagged questions with a sentence |
| A multi-action plan half fails | Checks run on every action first (all-or-nothing); a core that raises stops the rest, and the reply says which actions ran |
| Dev data is real Dev data | Writes go through today's cores and checks; Simon's company first |
| The planner's cost per turn | ~26k prompt tokens, ~25k cached (~3k credits); now billed to the company like any Maple call — watch `maple.planner.plan` in `llm_usage_events` |

## 10. Not in this plan

- Retiring today's pipeline (design §12 point 5).
- Moving other calls onto the cache helper (design step 11a).
- Any new capability: the executor does what today's Maple does, through
  today's write paths.
