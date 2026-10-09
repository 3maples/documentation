# Maple planner switchover: the executor and the switch — plan

**Date:** 2026-10-07 · **Status:** Approved 2026-10-07 (S1–S5). Build starts at phase 1.
**Builds on:** [`2026-10-02-maple-planner-shadow-design.md`](2026-10-02-maple-planner-shadow-design.md)
§12 (switchover), D20 (Dev first, then production), D21 (the companies in `MAPLE_SHADOW_COMPANIES` run on the planner)

## 1. Goal

Let a company's Maple turns run on the planner — plan, resolve, check, **execute**
— instead of today's pipeline, for the companies in `MAPLE_SHADOW_COMPANIES` (D21). Use it in Dev on Simon's
company until it is clearly better than today's Maple, then every Dev company,
then release with the planner as every company's default (D20, D21).

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

**Revised 2026-10-07 (D21, Simon): no company field.** The switch is the
settings shadow already has:

| `MAPLE_SHADOW_ENABLED` | The company in `MAPLE_SHADOW_COMPANIES` | Its turns |
|---|---|---|
| off | either | today's pipeline only — production until the switchover |
| on | listed | **the planner** (falling back to today's for what it can't run yet) |
| on | not listed | today's pipeline, the planner shadowing it |

- `services/maple_shadow.pipeline_for(company)` decides; `shadows(company)`
  gates the snapshot, so a planner company is never shadowed. Ids only; an
  entry that isn't an id is logged at startup and skipped.
- **Taking effect:** a change to the settings needs a restart (locally, or on
  Render). There is no per-company production rollout: at the switchover the
  planner becomes the default and the list is dropped (§7).
- **Who answers an open question:** the pipeline that asked it. Every question
  the planner pipeline stores carries `"pipeline": "planner"`. On a planner
  company, a turn with an open question **not** tagged planner (a question the
  current pipeline asked before the switch, or in a fallback turn) goes to the
  current pipeline. On a current company, a planner-tagged question (left when
  the company comes off the list) is dropped, with "I've lost track of that question — could you ask
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
   - `clarify` → the planner's question as the reply; not stored as an open
     question — the planner reads it in the history next turn and re-plans
     (S3, as built §7.1).
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
| **1. Switch and skeleton** | `unsupported`, `clarify`, `cancel`, `start_over`, `repeat`, `acknowledge`, `help`, `social`, `calculate` | `maple_shadow.pipeline_for` (D21); the branch; `run_planner_turn` with the coverage gate and fallback; question tagging and the "who answers" rule; shadow off for planner companies; the planner's unanswered outcome; a `fallback` count in the Dev export | Simon's Dev company runs on the planner, every uncovered turn falls back, the endpoint tests for a current company are unchanged |
| **2. Reads** | `get_*` and `list_*` for every domain, `metric`, `dashboard`, `catalog_figure`, `task_count`, `list_work_items`, `get_work_item`, `work_item_field`, `list_work_item_lines`, `list_notes` | Extract each list's query core from its text handler (filters as values: city, role, price range, category, sort, count); `get_*.field` answers; `metric` via `MetricAsk` into the metric internals (mapping as `metric_spec.ask_from_spec` does); `dashboard` via the `_analytics_*` value functions; row recording | Every read in the acceptance corpus runs without fallback |
| **3. Follow-ups** | `show_more`, `redo_last`, `refine_last` | `last_plan_read`; paging for every list (today only tasks and rankings page) | "show more", "and last month?", "just the drafts" run on the stored plan |
| **4. Writes on a record** | `update_*` (catalog), `create_*` (catalog), `edit_estimate`, `set_status`, `unarchive_estimate`, `generate_work_item`, `add_note`, `update_task`, `convert_task`, `link` | Catalog creates/updates on the `_via_api` cores plus today's enrichment and reply templates; `edit_estimate` → `to_edit_command` → `_run_edit_commands` (fanning a `by: all` pick out to one command per work item); task fields through the sub-handlers, several in one action; a contact↔property and estimate→property link core; the tenant fix above | Every write in the corpus runs without fallback; the `after` DB checks pass |
| **5. Confirmations** | every `delete_*`, `delete_note`, stale-target asks, removal confirm | The stash-and-resume record; today's confirmation and decline wording; deletes by id (notes too — today's note delete works by position) | A delete asks, a yes deletes, a no leaves it, on every domain |
| **6. Estimates from scratch** | `create_estimate`, `apply_template`, `adjust_assumption` | `create_estimate` keeps `delegate_create_estimate` (overage, gathering, sufficiency, quota) but takes the resolved property and template as values; the overage yes resumes the stash, not a text replay | Creating from a description, a template and a property all run, overage asks |
| **7. The acceptance run** | — | The 271 acceptance conversations with the company switched and the planner live (`-m llm_e2e`), scored on reply fragments and `after` checks; each failure fixed or added to the parity's explained list | Simon judges the planner clearly better in Dev (§11 of the design) |

After phase 7: every Dev company → release with the planner as the default
for every company (design §12, D20, D21). Retirement of today's
language reading is its own change, four weeks after the last switch.

### 7.1 As built: phase 1 (2026-10-07)

- **The switch (D21):** `maple_shadow.pipeline_for` — the planner for a
  company listed in `MAPLE_SHADOW_COMPANIES` while `MAPLE_SHADOW_ENABLED` is
  on, today's for every other turn; `shadows` gates the snapshot. (Built first
  as a `Company.maple_pipeline` field and a script, then replaced the same
  day.)
- **The branch** (`routers/agents.py::_orchestrate_turn`): the pipeline is read
  after the page signals; shadow's snapshot is skipped for a planner company;
  after the `_finalize_result` closure, `run_planner_turn` runs, and a result
  goes straight to `_finalize_result`. Any exception there is a fallback
  (`turn_error:<Type>`), never a 500.
- **`run_planner_turn`** (`agents/planner/turn.py`) falls back on:
  - `open_question`: any open question at all. In phase 1 the planner asks
    nothing it would answer itself, so every open question is the current
    pipeline's (a calculator's follow-up included). The planner isn't called.
    The pipeline tag and the rollback rule in §4 come with the first planner
    question (phase 2's "which one?").
  - `planner_error:<e>`, `check_error:<Type>`;
  - `op:<op>`, `decision:<d>` (ask / confirm), `unsupported:<reason>` from
    `execute.uncovered`;
  - `execute_error:<Type>` — safe in phase 1, which covers no write.
- **A `clarify` is not stored as an open question.** The planner reads its own
  question in the history next turn and re-plans the whole request (S3), so
  there is nothing to resume; the reply has `needs_clarification`, and the
  panel shows no chips for it.
- **The executor** (`agents/planner/execute.py`) covers, through today's code:
  refusals with today's words (bulk delete, equipment, material categories,
  template edits, notes on catalog, labor burden, material cost, every
  out-of-chat redirect) — `other`, `recurring` and `labour_rate` fall back;
  `clarify`; `acknowledge`, `start_over`, `cancel` (nothing open),
  `repeat` (the `meta` constants); `help` (the guide, asked the planner's
  `question`); `social` (today's canned greeting for a bare greeting, else
  the guide's persona); `calculate` (today's Calculator Agent through
  `delegate_generic`). Several actions run in order, one reply each (S5).
  Processors come from the router's `_get_processor`, passed in.
- **Billing:** the planner's call runs under the request's LLM context — the
  company, the turn id, feature `maple.planner.plan` (pinned by a test).
- **Recorded for the Dev review:** every planner-company turn is a
  `maple_shadow_turns` row with `pipeline="planner"` and `fallback` (why, or
  ""), from the plan already made — no second planner call
  (`maple_shadow.record_planner_turn`). A turn the planner ran has verdict
  `planner`; a fallback is compared like a shadow turn; one the planner
  wasn't asked about is `skipped`. A turn the planner ran records the
  planner's own outcome in `maple_unanswered` (pipeline `planner`) instead of
  classifying the reply. The session export shows a ran turn on one line, a
  fallback in full under `FELL BACK (<why>)`, and counts "planner ran / fell
  back" in each header and the index.
- **Tests:** `test_planner_execute.py` (14), `test_planner_turn.py` (8),
  `test_planner_pipeline_endpoint.py` (4), plus the shadow and export tests. `tests/conftest.py` now also clears
  `MAPLE_SHADOW_COMPANIES`, which a developer's `.env.local` may set. A live
  check over eight phase-1 messages against Dev gave today's replies, and
  "list my contacts" fell back.

### 7.2 As built: phase 2a — reading records (2026-10-08)

- **Shared replies (S2).** Each agent's details and list replies became a
  method that takes values; today's handler reads the message and calls it,
  the executor calls it with the plan's:
  `ContactAgent.contact_details_reply` / `list_contacts_reply`,
  `PropertyAgent.property_details_reply` / `list_properties_reply`,
  `MaterialAgent.material_details_reply` / `list_materials_reply` (it matches
  a category by name itself) / `list_material_categories_reply`,
  `LabourAgent.labour_details_reply` / `list_labours_reply`,
  `TemplateAgent.template_details_reply` / `list_templates_reply`,
  `TaskAgent.task_details_reply` / `list_tasks_reply`. The executor calls
  only these public methods (review 2026-10-08 #3–#7). Today's tests for
  each agent, the CRUD coverage matrix, the routing snapshot and the 275
  acceptance conversations pass unchanged.
- **Covered:** `get_*` and `list_*` for contacts, properties, materials, roles,
  tasks and templates, and `list_material_categories`. Records load by the
  resolver's id **within the caller's company** (`execute._load`; anything
  else is a `LookupError`, so a fallback).
- **The turn's state is copied** for the executor (`run_planner_turn`): a
  fallback part way through a plan hands today's pipeline the state the turn
  started with, never the planner's half-written lists and anchors; a run's
  result carries the copy, which finalize saves (review #1). A reference
  that isn't one record (a `step`) falls back at the gate, `ref:<name>.<status>`
  (review #2).
- **Per-field coverage** (`execute._uncovered_read`): a list filter or a get
  `field` the executor doesn't read yet falls back (`filter:<op>.<name>`,
  `field:<op>.<field>`). Not yet: contacts by role, city or related record;
  properties by city or related; materials or roles on an estimate; a
  property's contacts / owner / estimates / notes, a contact's properties /
  notes. A get's other fields answer with the full details, as today.
- **A filtered property count is the planner's own answer** (user decision
  2026-10-08, review round 2 #2): today drops the owner / name filter and
  counts every property; the planner counts what it filtered and says so —
  "You have 2 properties owned by Ana Reyes." (`format_count_response`'s
  `qualifier`). Today's reply is unchanged: its handler still drops the
  filters before calling `list_properties_reply`. Where today's Maple gives a
  wrong answer, the planner gives the right one rather than copying it.
- **Values, not text:** a material category is matched by name (one the
  company doesn't have lists nothing); `price_below` / `price_above` both
  apply; task filters map onto today's `TaskListAsk`, named due windows
  through `list_filters.apply_due_window` (the same dates and words as
  "due this week"), explicit dates on the user's clock, worded "due by Oct 16".
  `due_before` is the last day included — "due by Friday" is Friday, "due
  before Friday" Thursday — said in the schema and the prompt's "Reading the
  words" (review round 2 #1; a live check of four phrasings gave those days).
- **Focus for several actions:** finalize's entity anchoring is now
  `finalize_result.anchor_entity`; the executor calls it for each action of a
  multi-action plan (finalize moves only the estimate's), the last newest.
- **Tests:** `test_planner_execute_reads.py` (30, each branch of the task
  filter mapping included), `test_task_list_filters.py` (every `DueWindow`
  against today's parser), `test_planner_turn.py` (the copy on fallback). A live check over eight
  reads against Simon's Dev company gave today's replies.

### 7.3 As built: phase 2b — reading estimates (2026-10-08)

- **One estimate** (`get_estimate`): `delegate_get_estimate.estimate_details_reply`
  holds today's full reply and field answers; the router calls it after
  resolving from the text, the executor with the resolved estimate (loaded
  within the company). Fields map onto `focus_questions.answer`
  (`gross_margin` → margin; `work_items` → the full details, which record the
  work-item rows). Title, description and divisions are new answers there —
  today's reader never asks for them, so today is unchanged. `notes` falls
  back (`field:get_estimate.notes`) until `list_notes` (2c).
- **Work items** (`list_work_items`, `get_work_item`, `work_item_field`,
  `list_work_item_lines`): today's handlers split into
  `work_items_reply`, `work_item_details_reply`, `work_item_field_reply` and
  `work_item_lines_reply`, each called after today's text matching. The
  executor finds the work item by the resolver's `JobItem.id` — never a
  position — and a work item the estimate no longer has is a `LookupError`
  (fallback). Each puts the work item in focus. `lines: "all"` is both lists.
- **The estimate list is the planner's own core** (user decision 2026-10-08):
  today's `_handle_list_estimates` reads every filter from the text in one
  611-line handler and is left alone. `agents/estimate/list_core.py`
  (`EstimateListAsk`; `list_estimates_reply`, `count_estimates_reply`,
  `total_estimates_reply`) reads through the metric engine's filter
  (`maple_metrics.estimate_match`), so a list, its count and its total read
  the same estimates as every figure and the dashboard, and words its replies
  as today's do (each names everything it was narrowed by). Where today is
  wrong, the planner is right:
  - a property, customer, material or role said in any words narrows a count
    ("how many estimates have I done at Bob Residential?" was 56, the
    company's);
  - no status said is every real estimate (`DEFAULT_STATUSES`) — today counts
    archived, generating and deleted ones too (Sim Co: 55 against today's 56);
  - a period dates estimates as the engine does (`date_field_for`: sold ones
    by `sold_at`), where today's list always reads `created_at`;
  - sorts today lacks: oldest, lowest total; a title filter.
  - the reply names exactly the statuses it counted: "open draft and lost
    estimates (Draft)", "open sold estimates (Won)"; "open" over statuses none
    of which is open counts no estimate — a filter, never the Deleted status a
    delete leaves for a moment (user, review 2026-10-08 (2b) #1–#2); a customer
    and a property are both named ("for Ana Reyes at 'Elm House'", #3).
- **A customer named by a property's name** ("at Bob Residential", planned as
  a customer): when no contact matches but one property does, the policy
  resolves it as the property (`policy._resolve_all`), and the list counts
  that property's estimates.
- **Live check on Sim Co** (read-only): "show me my 3 oldest estimates", "how
  many estimates do I have?" and "list my won estimates" ran on the planner.
  "how many estimates have I done at Bob Residential?" and "what's the total
  value of my draft estimates?" were planned as `metric` and fell back — 2c.
  Seen in one run: "list my won estimates" planned `statuses: ["Won"]`
  rather than `sold` (#784: a bare "won" is the sold set) — the prompt already
  says so; a parity-run item, not an executor rule.
- **Tests:** `test_planner_execute_estimates.py` (27: details and fields
  against today's own replies, work items against today's handlers),
  `test_planner_execute_estimate_list.py` (22), a policy test for the
  customer-as-property reading. A stale assertion in
  `test_agent_helpers_delegate_get_estimate.py` (it predates `recorded_at`,
  27ecc77) was fixed in passing.

### 7.4 As built: phase 2c — figures and notes (2026-10-08)

- **`metric`**: `metric_answers.answer_metric_ask(agent, ask, …)` is today's
  answer from the ask on (subject resolved within the company, fetch, word);
  `answer_metric` reads the text and calls it. `agents/planner/metric_ask.py`
  maps the plan to today's `MetricAsk` through `metric_spec.ask_from_spec`
  (the plan's status, period and shape choices are the spec's), so both LLM
  tiers keep one set of rules, and adds what the spec can't say: a status
  list, `work`, `recurring`, `by_status` rows, `line_total`. A division said
  as `work` with no customer or property is the subject, as today. Pinned by
  ask equality: each plan maps to the very ask today's grammar reads from the
  words (18 phrasings). A plan no ask describes falls back
  (`filter:metric.shape`).
- **`dashboard`**: `EstimateAgent.dashboard_reply(card, …)` over today's card
  functions; the breakdown became `dashboard_breakdown(by, period, …)`, which
  today's text router calls. A card's period is the **calendar** one
  ("pipeline this month" is the month, as every figure reads it — today's text
  reader rolls back 30 days). A breakdown over a week, any card over "the
  last N days" (a card has no day count), and "all time" on pipeline or
  completed have no answer today and fall back at the gate
  (`filter:dashboard.period`; review 2026-10-08 (2c) #2).
- **`catalog_figure`**: `catalog_figures.catalog_figure_reply(CatalogAsk, …)`,
  which today's pre-handler calls after reading the words.
- **`task_count`**: today's `list_tasks_reply` with the group set, open tasks
  unless a status, a due window or "archived" is said (decision 22). "All
  tasks by person" can't be told from the plan yet; it counts open ones.
- **`list_notes`**: `record_notes.note_parent(domain, doc)` and
  `notes_reply(parent, …)`, shared with today's reader, for a contact,
  property or estimate. A work item's or a task's notes fall back
  (`ref:parent.<domain>`): tasks have none, and a work item's have no chat
  reader yet.
- **A record's linked records** ("how many properties does John Smith
  have?" — today: "You have 6 properties", every property): the 2a fields
  left over are covered. A contact's `properties` and a property list
  `related` to a contact are `PropertyAgent.properties_of_contact_reply` (one
  query on the contact's id, new index `company_contacts`; "John Smith has 3
  properties:"; a name filter beside it still narrows, review (2c) #5). A
  property's `contacts` / `owner` are `ContactAgent.contacts_of_property_reply`,
  in the property's own order (#4). Its `estimates` are the 2b list
  core, and a contact's or property's `notes` are `notes_reply`. A property list
  related to an estimate, material or role still falls back.
- **A `count` written inside a list's filter** is the list's count
  (`schema._Listing`): in the live check the planner wrote
  `filter: {owner, count}` for that question three times in five, which
  failed validation and fell back to today's wrong answer. Anything else
  stray in a filter is still refused. Four runs after both fixes: 3 every time.
- **Contact or property, either way**: the 2b rule now covers a notes
  parent too — a name planned as one kind that matches none of it but one
  record of the other resolves as that record (`policy._EITHER_KIND`), as
  today's note reader tries contacts, then properties.
- **Live check on Sim Co** (read-only): "how many estimates have I done at
  Bob Residential?" ran on the planner — "You have 7 estimates for Bob
  Residential, worth $35,790.52, including tax." (today: "You have 56
  estimates"). A total figure planned with `measure: count` leads with the
  count (user 2026-10-08; `MetricAsk.measure` on a figure, which today's
  reader never sets). Also on the planner: the total of draft estimates, top 3
  customers, this year's win rate, the pipeline, the backlog this year, the
  priciest material, open tasks by person, and Bob Residential's notes.
- **Tests:** `test_planner_execute_figures.py` (81: task counts, catalog
  figures, notes and dashboard cards against today's replies; the metric
  ask-equality table and end-to-end figures), a policy test for the either-
  kind parent.

### 7.5 As built: phase 3 — follow-ups on the plan (2026-10-08)

- **The stored read** (`agents/planner/followups.py`): each read the executor
  runs is stored as its action in `last_plan_read`, stamped with the turn; any
  other action forgets it, so a follow-up never replays a write.
- **A follow-up is the read it follows up, changed** (`followups.expand`, run
  in `run_planner_turn` before the check): `redo_last` changes the subject,
  period or tax of a figure, a card, an estimate list or one record;
  `refine_last` narrows, sorts or counts the list just shown; `show_more` is
  the list again from where it stopped. The expanded plan is checked and run
  like any other — its references resolved again within the company, the
  gate deciding. Only the read **just before** counts (today's "show more"
  rule): if that turn was today's pipeline, or the read can't take the change
  (`followup:<why>`), the turn falls back and today's answers from its own
  memory (`last_request`, `list_page`).
- **Every list pages on the planner** (user decision 2026-10-08):
  `paging.format_and_record_page` shows ten rows (an estimate list twenty, as
  today's; tasks and rankings already page), says "That's 1–10 of 34 — say
  "show more" for the next 10." and remembers where it stopped; the last page
  says "That's the last of them — 34 in all." The list replies take
  `paged` / `offset`, which only the executor passes — today's lists still
  stop at ten without a word. The offset of a "show more" goes on the
  planner's copy of the state only, so a fallback never inherits it, and a
  planner list's page is kept under its own key (`paging.PLANNER_PAGE_KEY`)
  — today's "show more" after a failed planner turn would otherwise replay it
  and show the first rows again (review 2026-10-08 (phase 3) #7); tasks and
  rankings keep today's `list_page`, which both pipelines honour. An
  explicit limit ("my top 3") is the whole answer.
- **"Does that include tax?"** gives the figure the other way, as today does
  (user decision; a prompt line: `before_tax` opposite the one just shown).
- **Live check on Sim Co** (read-only): sold this year → "and last month?" →
  "what about Bob Residential?"; open estimates → "just the drafts" → "how
  many is that?" (39); the pipeline → "does that include tax?" ($475,843.21
  before tax); 55 estimates paged 20, 20, 15 — all on the planner.
- **Tests:** `test_planner_followups.py` (30, every follow-up and fallback),
  `test_paging_pages.py` (3), `test_planner_show_more.py` (9: contacts,
  properties, materials, roles, templates, estimates and tasks paged end to end, a limit, today's list unchanged), two
  turn tests and an estimate-list conversation through the real check.

### 7.6 As built: phase 4a — catalog creates and updates (2026-10-08)

- **Today's handlers write** (the plan's design: the planner reads the
  request, today's code does the work). Each agent has a public
  `create_*_reply` / `update_*_reply` that hands the plan's fields to today's
  private handler, as the material size commands already did:
  `ContactAgent`, `PropertyAgent`, `MaterialAgent` (`_handle_create_material`
  / `_handle_update_material`), `LabourAgent` (its dispatcher, the role named
  by id). Enrichment (address lookup, geocoding, the material markup, the
  Rate from the wage), validation, the one-field-at-a-time questions — whose
  answers are today's to take, through the open-question gate — the audit
  log and the reply are all today's. The executor maps the plan's names
  onto today's: a role's `wage` is `cost`; a material's `rename_size_to` /
  `remove_size` are `size_op` / `new_size`; a size's unit is the company's
  own by name, one it lacks said back with today's note and nothing written.
- **A write never falls back** (`execute.WRITES`): once a write has begun,
  a failure is answered — "Something went wrong partway through that, so I
  stopped. Please check the record before trying again — part of the change
  may already be saved." — never handed to today's pipeline, which could make
  the write twice. A record that doesn't load within the company
  (`execute.RecordNotLoaded`) is raised before any write, so with nothing
  written before it the turn still falls back.
- **Tenant scope** (CLAUDE.md): today's `_update_contact_via_api` and
  `_update_property_via_api` loaded by a bare id and never checked the
  company; both now refuse another company's record (safe today only because
  today's resolver supplies the company's own ids).
- Checked and not a defect: changing a role's unit ("make the Foreman daily")
  writes, through the planner and today's update.
- **Sizes** (review 2026-10-08 (4a)): adding a size the material already has
  is said back ("Pavers already comes in 12x12 — I've left it as it is.") —
  it overwrote that size's cost, on the planner and on today's add command
  alike, and both now share `MaterialAgent._size_already_there`. A cost for
  a size the material lacks still adds it, as today (user decision, option
  B). A size renamed and removed at once is refused by the schema, so the
  turn falls back. A failed write is the unanswered tracker's
  `error/write_failed`.
- **Live check on Sim Co** (planned and gated only — nothing written to Dev):
  a contact, a contact's email, a property, a role's wage, a material and a
  role all plan cleanly, pass the policy and would run.
- **Tests:** `test_planner_execute_writes.py` (19: each create and update
  through today's handler against the database, each missing-field question
  with nothing written, sizes renamed, added and removed, an unknown unit,
  another company's record, the two update cores' company checks, adding a
  size it has, a cost for one it lacks), the write rule in
  `test_planner_execute.py` (4), today's add command on a size it has
  (`test_material_agent.py`), the schema's rename-and-remove refusal and the
  outcome row.

### 7.7 As built: phase 4b — task writes (2026-10-08)

- **Create** (`create_task`): today's `_handle_create_task` is split into its
  reading (the clauses, the title, the awaiting-title question) and
  `_create_task_core`, which both pipelines call; the planner's entry is
  `TaskAgent.create_task_reply`. So the note and its derived title, "I named
  it from your notes", the teammate, status and property resolved as today
  (one that can't be is told and the task still made), the notification, the
  audit and the task limit are all today's. A due date is midnight of the
  user's day (`execute._due_at`), as today's dates. Today's create has no
  unassigned, archived or replaced-notes task, so those fields fall back
  (`execute._WRITE_FIELDS`).
- **Update** (`update_task`, `agents/task/planned.py`): one field runs today's
  own sub-handler with the task resolved — status, assignee, unassign,
  property, due date, archive, notes added or replaced — so its reply and any
  question are today's. Several fields (§8's "one sub-op per message") are
  resolved first and written once (`_finish_task_update`: one version, one
  audit, today's "I've updated the task … Here are the updated details"). A
  property that can't be found, or that several share, is asked with
  `record_names.ask_to_rewrite(replan=True)`: the answer is written into the
  request and, for a planner company, the router plans that whole request
  again (`REPLAN_KEY`, user decision 2026-10-08 — today's one-change reading
  would drop the rest). Any other field that can't be resolved goes to its
  sub-handler, which asks. Nothing is written either way. The note fields fold into one note: set or replaced, added to,
  then renamed (the title is its first line). A field with its clearing, or
  two whole notes, is refused by the schema (`TaskFields`), so the turn falls
  back. `_handle_task_due_change` moved to `operations.py` beside the other
  sub-handlers.
- **One record, one update** (Dev, 2026-10-08): "Mark T0001 as done and link
  to Bob Residential" was planned as an update and a second update on "the
  task of step 1"; the executor can't load a step reference, so the turn fell
  back and today's pipeline read "done and link to Bob Residential" as a
  status. `agents/planner/merge.py::merge_step_updates` folds such a second
  update into the first before the check (same op, no field given two values,
  the merged fields still valid; later step references renumbered), and the
  prompt now says several changes to one record are one update. Owes the
  parity run.
- **Convert** (`convert_task`): today's flow with the task resolved — it asks
  first (an estimate uses a billing slot) and today's pipeline takes the yes,
  through the open-question gate. `delete_task` falls back (§8).
- **Live check on Sim Co** (planned and gated only): a create with a due
  date, "me" and a property; a status; status, assignee and due date at once;
  a rename; a convert — all would run. "Add a note to T0002" plans as
  `add_note` on the task (phase 4d: it becomes `notes_append`), and convert
  with delete falls back.
- **Tests:** `test_planner_execute_tasks.py` (44), the re-plan at the endpoint
  (`test_planner_pipeline_endpoint.py`, both ways) and the flag
  (`test_record_names.py`).

### 7.8 As built: phase 4c — estimate writes (2026-10-08)

- **Today's estimate code writes**, through the Estimate agent's value entry
  points (`agents/estimate/planned.py`: `status_reply`, `edit_reply`,
  `generate_work_item_reply`), called by `agents/planner/execute_estimates.py`
  on the estimate the planner resolved within the company. The executor's
  shared helpers (`RecordNotLoaded`, the company-scoped load, the agent
  lookup) moved to `agents/planner/execute_base.py` so the per-area modules
  don't import `execute.py`.
- **Status** (`set_status`, `unarchive_estimate`):
  `_handle_update_estimate_status_transition` with the estimate forced
  (`FORCED_ESTIMATE_CODE_KEY`, for the one call, never saved), so today's
  resolver neither re-reads the message nor guesses from a stale anchor.
  The workflow's transitions, who may move it, the send gate, the audit and
  "I've marked estimate E0001 as Sent." / "I've archived …" / "I've
  unarchived … (now Review)." are today's.
- **Edits** (`edit_estimate`): each planner command becomes today's
  `EditCommand` (`to_edit_command`), its work item named by id, and the batch
  runs through `_run_edit_commands`: all or nothing, the edit lock, the
  removal question (today's pipeline takes its yes), one reply line per
  command. "Every work item" is one command per work item (§8, done); the
  gate lets an edit command's `all` through.
- **New work** (`generate_work_item`): `_handle_generate_work_item` — the
  lock checked before the paid generation, "I couldn't price … as a work
  item" when nothing comes back, the new item in focus.
- **Live check on Sim Co** (planned and gated only): mark as sent, the markup
  on every work item, a rename, new work, removing a work item and an
  unarchive all would run.
- **Tests:** `test_planner_execute_estimate_writes.py` (22: each write through
  today's code with its reply pinned, plus the review's — a work item gone
  since the check falls back, the missing agent, and the forced code cleared
  on a raise and never carried in a copied reply).

### 7.9 As built: phase 4d — links and notes (2026-10-08)

- **Links** (`link`, `agents/planner/execute_links.py`), each side loaded
  within the company: a contact and a property through
  `record_links.link_contact_reply` (today's write, split out of
  `handle_link_request`: the property read again within the company — it was
  a bare get — "already linked", the audit); an estimate and its property
  through the Estimate agent's `link_property_reply` (today's load with its
  edit lock, and `_apply_estimate_property`, split out of
  `_handle_update_estimate_property_link`); a task and a property through the
  Task agent's `link_property_reply` (today's handler, the property forced for
  the one call). Any other pair falls back (`link:<a>-<b>`).
- **Notes** (`add_note`): a contact's, property's or estimate's feed through
  `record_notes.add_note_reply` (today's, signed by the user, "I've added a
  note to …"); a task's notes through today's append ("add a note to T0002"
  plans as `add_note`, and a task's notes are its description); a work item's
  through today's `add_work_item_note` edit command, its estimate found within
  the company.
- **Tenant fix** (§2, CLAUDE.md): `_delete_contact_via_api` and
  `_delete_property_via_api` took a bare id; both now take the caller's
  company and read within it.
- **Live check on Sim Co** (planned and gated only): a task's link, and notes
  on a contact, a task, an estimate and a property, would run. "Link John
  Smith to Bob Residential" is asked back (Sim Co has a contact and a property
  of that name). **Follow-up:** "link E0059 to Bob Residential" planned the
  property as a contact, so the pair is uncovered and today's pipeline links
  it — the policy could try a link side as the other of contact and property
  (as `_EITHER_KIND` does for a customer filter); owes a parity look.
- **Tests:** `test_planner_execute_links_notes.py` (21).

### 7.10 As built: phase 5a — the confirmation (2026-10-08)

Phase 5 is split like phase 4: **5a** the confirmation itself, **5b** the
catalog deletes, **5c** the estimate delete and a note's delete by id.
**Removal stays today's** (Simon, 2026-10-08): "remove the patio from E0042"
already asks first inside today's edit executor (the dry run names the items
and the new total), and today's pipeline answers its yes from the commands it
kept, by work-item id — so the planner doesn't ask it again.

- **Asking** (`agents/planner/confirm.py`, `turn._ask`): the gate lets a
  `confirm` decision through (`execute.uncovered`); the turn asks today's
  question and keeps the plan and the records it resolved on a
  `pending_intents` record tagged `"pipeline": "planner"`
  (`op: planner_confirm`), which `open_questions` reads as a yes/no — so the
  panel's "Waiting for your answer" and Yes/No chips work unchanged. 5a asks
  one thing: a write through a record the user has moved on from (a stale
  focus or list, D19), in today's words — "Just to check — do you mean Ana
  Reyes?", "Just to check: apply this to E0042 'Spring Cleaning'? (yes/no)"
  (any stale estimate, a link's side too), or a work item's. **A note doesn't
  ask** (Simon, 2026-10-09): it overwrites nothing and its reply names the
  record, as today (`focus.stale_anchor_confirmation`); a link still asks, since
  an estimate's or a task's replaces its property. Two stale records in one plan, or a confirm 5a doesn't ask
  yet, fall back (`confirm:several`, `confirm:<op>`).
- **The next turn** (`turn._answer_kept`), before any planner call: **yes**
  runs the kept plan on the kept records, the rules checked again
  (`policy.recheck`: a role, the Draft/Review lock, an author found now still
  stops it; the stale check doesn't ask twice). Anything that stops it — a
  refusal, a record gone — is `confirm.CHANGED_SINCE`, never today's pipeline,
  whose reading of "yes" isn't the plan. **No** is today's "Okay — which
  contact did you mean?", not kept as a question: the name in reply is planned
  again whole (S3) — today's replays the text. **A cancel** is today's
  `LEFT_AS_IS`. **Anything else** drops the question (it lives one turn) and is
  planned as a new request; the planner's copy loses it too. A question asked
  under another company is dropped (#675). The reply is read by the gate's own
  rule (`open_question.decide_question`), so a yes/no reads the same for both
  pipelines; a kept plan this build can't read is answered `LOST_TRACK`
  (`confirm:unreadable`).
- **Off the planner** (§4): today's pipeline meeting a planner-tagged question
  answers it with `confirm.LOST_TRACK` ("I've lost track of that question —
  could you ask again?") — a company taken off the list between the question
  and the answer. A question today's pipeline asked still falls back
  (`open_question`).
- `CHANGED_SINCE` and `LOST_TRACK` are classified for the unanswered tracker
  (`error/changed_since`, `error/lost_track`).
- **Tests:** `test_planner_confirm.py` (31, real records and the real policy),
  two endpoint tests in `test_planner_pipeline_endpoint.py`, the gate's in
  `test_planner_execute.py`.

## 8. Plan fields with no handler today

Each gets a core in the phase that covers its op, or the planner stops offering
it (a schema change, with a parity run):

- `convert_task.delete_task` — no delete-after-convert anywhere.
- `create_estimate.customer` — only a property is linked today.
- `apply_template.size` — scaling exists only when creating from a template.
- ~~`edit_estimate` on **every** work item~~ — done in phase 4c (§7.8): one
  command per work item.
- ~~Several task fields in one update~~ — done in phase 4b (§7.7).
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
| A question asked by one pipeline answered by the other | The `pipeline` tag and the routing rule in §4; taking a company off the list drops planner-tagged questions with a sentence |
| A multi-action plan half fails | Checks run on every action first (all-or-nothing); a core that raises stops the rest, and the reply says which actions ran |
| Dev data is real Dev data | Writes go through today's cores and checks; Simon's company first |
| The planner's cost per turn | ~26k prompt tokens, ~25k cached (~3k credits); now billed to the company like any Maple call — watch `maple.planner.plan` in `llm_usage_events` |

## 10. Not in this plan

- Retiring today's pipeline (design §12 point 5).
- Moving other calls onto the cache helper (design step 11a).
- Any new capability: the executor does what today's Maple does, through
  today's write paths.
