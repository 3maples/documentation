# Planner vs. the phrasing reference — gap review (2026-10-11)

What the Maple planner (`platform/agents/planner/`) can't understand, can't run,
or gets wrong, measured against every row of
`documentation/development/maple-phrasing-reference.md`.

## Status — 2026-10-11, after phase 8

Built the same day (switchover plan §7.27). Simon: close what falls back first;
negated commands ("don't add …") are low priority, since users say what to do and
a delete always asks.

- **P0:** relative changes, the same-turn work item, tasks-off on every task op,
  sold beside a status, and Carla linked rather than duplicated are done. Overhead
  on the focus and a line's price on the work item are now prompt rules, checked
  live. Negation is left as is (Simon).
- **P1:** done — stale_days, the estimate's dates and code, line counts, list
  total before tax, dashboard days, catalog `within` (said back), task-list
  refinements, `RedoLast.limit`, compare implying a comparison. Still open: task
  refs by recency or date, `TaskFilter` property-or-person / an unread date /
  all, and `TaskCount` fewest.
- **P2:** done — policy refusals, the three refusal texts, handler questions,
  the router, city/role filters, the customer on create, the contact on an
  estimate, follow-ups, notes, metric shapes, step references, invalid-plan
  retry, and every op covered. Still open: the public widget, two deletes in
  one plan, a city or role beside another filter, lines by category or price,
  and breakdown periods.
- **P3:** the prompt's "More readings" section covers the listed misreads; 43
  phrasings were checked live, all as intended. Template names read as estimate
  titles are still open (the resolver has no cross-kind lookup yet).
- **Owed:** a parity run, and the acceptance corpus on the planner pipeline
  with task statuses in its state.
- **Tracked** in [`code-review-followups.md`](../code-review-followups.md) #840–#847:
  - #840: the public widget;
  - #841: task references;
  - #842: task filters;
  - #843: template names;
  - #844: errors and today's old questions;
  - #845: the smaller fallbacks;
  - #846: the owed verification;
  - #847: negation.

**Evidence**
- The 2026-10-11 00:24 parity run (`tests/reports/planner_parity.json`). It
  planned all 1,035 *checked* ✅/🛑 reference rows. No planner code has changed
  since. Each recorded plan was re-run offline through
  `execute.uncovered_actions` to see whether the executor would run it.
- A static review of all 1,302 reference rows against the schema, policy, said
  rules, resolver and handlers. 267 of those rows are *unchecked*: the parity
  harness can't build them (multi-step, needs a state, ellipsis). About 250 of
  those are supported rows that have never been put to the planner.
- The shadow-conversation run (581 turns, `planner_parity_conversations.md`).
- Dev's unanswered tracker, 2026-10-01 → 10-11 (11 turns, all Sim Co).

**Headline numbers**
- 0 blockers: the planner never refused a phrasing the doc supports.
- About 892 of the 1,035 checked rows plan to something the executor runs.
- About 860 rows look fully right: correct plan and the executor covers it.
- The rest are the items below.

Priorities:
- **P0**: a wrong write or a missing safety gate.
- **P1**: the schema can't express the request, so the planner can't understand it.
- **P2**: the planner understands it but hands the turn to today's pipeline. Every one of these is lost at the switchover.
- **P3**: a misread that a prompt line or a normalizer fixes.

---

## P0 — wrong writes and missing gates

1. **Negated commands write.** Nothing on the planner path checks negation:
   there's no prompt rule, nothing in `said.py`, and the planner runs before
   today's `COMMAND_LEAD` (`routers/agents.py:1323`).
   - `don't drop the markup on work item 2` (estimate in focus) → markup set to **0** on work item 2.
   - `don't add a note to it: call Bob` → note appended.
   - `don't add a description to it: call Bob` → task **renamed** "Call Bob".
   - `we shouldn't set the notes on the fence task to foo` → note appended.
   - `push the fence task to Friday?` → written. A question must never write (#710).
   - *Fix:* a deterministic guard before execution that turns a negated write into `acknowledge`, reusing today's negation detection. Add a prompt rule as well.
2. **Relative changes written as absolute values.** `PSetWorkItemPercentage` only takes `value` (`schema_edits.py:104`).
   - `raise the markup by 5%` → markup = 5.
   - `reduce the markup 5%` → markup = −5.
   - `raise the tax 2%` → tax = 2 on **every** work item.
   - *Fix:* add `change_by`, resolved against the current value, or ask.
3. **Same-turn added work item.** `add a work item Patio, add 10 pavers to it` targets `position 2`. On an estimate that already has 2 or more items, the pavers go on the **existing** #2.
   - *Fix:* a `WorkItemPick by:"added"` that maps to `WorkItemRef(description_hint=…)`, which `edit_executor._pin_targets` already resolves (`edit_executor.py:617-625`).
4. **Tasks-off is gated only on create** (`policy.py:485`). The executor calls the `*_reply` methods directly, skipping `TaskAgent._entry_guards` (`agents/task/service.py:196`). With tasks off, the planner can still list, update, convert and delete tasks.
   - *Fix:* refuse every task op in `_check_rules`.
5. **Wrong target or field, written:**
   - `add Carla Diaz to 12 Oak St` / `Carla Diaz lives at 12 Oak St` → create_contact (+ link), so a **duplicate** contact.
   - `set the overhead to 10%` with a work item in play → `target: all`, every work item.
   - `set the price of pavers to $4.25` inside a work item → edits the **catalog** material.
   - `add a description to the last task: X` → overwrites the description; it should append.
   - `rename the scope to Foundation` → guesses `position 1`.
   - *Fix:* prompt rules — with no work item named use the focus; "add … description/notes" → `notes_append`; "add/lives at" with an existing person → `link`.
6. **`won estimates for Bob Lee in review`** → `statuses:[Review] + sold:true`, counted as the union (`execute_estimates.py:131-135`). Today asks (#780).
   - *Fix:* ask, or refuse, when `sold` and `statuses` conflict.

## P1 — the schema can't express it

| Doc rows | Phrasing | Missing | Where |
|---|---|---|---|
| 412–415 | `older than 60 days`, `40 days or older`, `not touched in a month` | No age/stale filter. The model writes `last_n_days` (the opposite), and `window_unit:"day"` is an invalid plan. | `EstimateFilter`, `WindowUnit` (schema_fields.py:36, 204) |
| 465, 482–484 | `when was E0042 last updated/created?`, `what's the code…` | `GetEstimate.field` has no created/updated/code | schema.py:275 + `_DETAIL_FIELDS` |
| 696, 724 | `how many materials/activities are in work item 1?` | `ListWorkItemLines.count`; invalid plan today | schema.py:352 |
| 425, 82 | `total of my drafts … before tax`, then `does that include tax?` | `ListEstimates.before_tax` | schema.py:282, list_core.py:105 |
| 883, 888 | `pipeline value in the last 30 days` | `Dashboard.days/window_unit` (it substitutes a metric) | schema.py:448, execute_figures.py:35 |
| 1547 | `average price of my mulch`, `most expensive in Bulk Materials` | `CatalogFigure` has no category/text, so it **silently answers company-wide** | schema.py:458 |
| 2456–2459 | after a task list: `which ones are done?`, `just mine`, `just the ones at Elm House` | `RefineLast` has estimate statuses only, and no assignee/property | schema.py:558, followups.py:137 |
| 1963–1966 | `the last task`, `the task from yesterday`, `the task at Elm House`, fuzzy titles | `RefBy` has no recency/date/property; name match is exact/word-start | refs.py:13 |
| 1809, 1816, 1929 | `tasks for Jordan` (property-or-person) | `TaskFilter.for_name` → `property_or_person` | schema_fields.py:185 |
| 1821, 1830 | `tasks due whenever`, `what's due 10/3` | No `due_unread`. Today says the unread date back; the planner guesses. | execute_records.py:339 |
| 1795, 1798 | `all tasks by assignee`, `who has the fewest tasks?` | `TaskFilter.all`; `TaskCount` has only `most` | schema.py:474 |
| 1176 | `show me the top 10` after a ranking | `RedoLast.limit` | schema.py:542 |
| 1174, 1179, 1188 | `sold this quarter vs last quarter` | `compare` without `shape=comparison` **silently answers one period** | schema.py:431. *Fix:* a validator. |

## P2 — understood, but handed to today's pipeline

**a. Policy refusals.** `uncovered()` returns `decision:refuse` (`execute.py:300`) for every policy refusal, so today's pipeline words them. Affected:
- §9.6 illegal transitions;
- §9.7 locked estimates;
- §9.9 and member deletes for catalog, notes and estimates;
- §7.12 task limits;
- tasks off.

*Fix (one change):* answer `PlanCheck("refuse")` from `refused_for`, using today's copy.

**b. Refusal reasons with no planner copy:** `other`, `recurring`, `labour_rate` (`execute._refusal_copy`). They cover the 13 recurring rows (662–674), the rate card (721) and the role Rate (1608). Dev saw `make work item #1 recurring monthly…` on 10-08.

**c. Questions owned by today's handlers that the planner calls.** The answer turn falls back on `open_question` (`turn.py:156`); only record creates are kept (`asks.keep_create_question`). This is the biggest switchover risk:
- estimate gathering and the post-create "link a property?" follow-up (§10.4; `delegate_create_estimate.py:246, 410-444`);
- calculator continuation (§10.3; `delegate_generic.py:70`);
- the template baseline-size question (1711–1715; `open_question.py:324`);
- the division near-miss "yes" (640) and the assumption "which one?" (548, 549, 859);
- the convert-task confirmation, plus the 402/429/409 outcomes (1951–1953, 1980, 1983). This should be a `confirm.py` record, like deletes.
- the metric "Which one did you mean…?" — `ask_to_rewrite` is called without `replan=True` (`metric_answers.py:110`), at 1155, 1160, 1164 and 2052;
- a single-field task "link it to Pine Ridge" — `ask_for_name` without replan (`agents/task/operations.py:488`).

**d. Router:**
- A new request while today's question is open only re-enters the planner for REPLAN questions (`routers/agents.py:1374`).
- A question asked under another company is seen by `_kept_turn` before `decide_turn` drops it.

**e. Filters the schema has but the executor rejects:**
- `list_properties.city`, `list_contacts.city/role` (1269, 1352 — `how many properties are in Toronto?`, `list homeowners`). `_LIST_FILTERS` allows only text/owner/related (execute.py:166).
- `list_contacts.role` for `who owns 14 Birch Rd?`.
- `create_estimate.customer` (`quote a fence for Bob Lee`, 496).
- A contact–estimate link (`add Bob as the contact on E0042`, 989).

**f. Follow-ups:**
- `redo_last` ("what about X?") only handles metric, dashboard, estimate list and gets. A contact, property, task, material or template list falls back (followups.py:127): 1511, 2440.
- A comparison plus `and last year?` keeps `compare=month` → `filter:metric.shape` (1178).
- `does that include tax?` after a count or a ratio (1204).
- `show more` with nothing listed, a follow-up after a write, and a position past the end of the list (2443, 2460, 2385).

**g. Notes:**
- `delete the first one` after listing a contact's notes gives an **invalid plan** (`delete_note names its note or the record it is on, not both`). Seen twice on Dev today.
- `delete my note on X` with zero or several notes (note_pick.py:40).
- `add a note: …` with nothing in focus, or a material/role in focus (`RecordNotLoaded`).

**h. Public widget:** `routers/public_maple.py` never runs the planner. This needs a decision before the switchover.

## P3 — misreads (prompt line or normalizer)

- **Metrics wording** (maple_planner.py:81-88):
  - `won vs lost` / `how am I doing on bids?` → `win_rate`. Today the prompt's own example sends "win vs lose" to a count.
  - `X vs Y (status)` → `by_status`.
  - `breakdown by divisions` → `by_division`.
  - `backlog` → Won + Scheduled.
  - `how much was completed?` → the Completed card.
  - `recent drafts` (no invented period).
  - `done` ≠ sold.
  - `my/our gross margin` = the company, even with an estimate open.
  - `by month for all time` keeps all time.
  - `which division earns the most?` → limit 1.
  - `which estimate has the highest total?` → a metric.
- **Work-item names:** `the patio work item`, `Driveway scope` → strip "work item / scope / line item / the" in `resolve_work_item` (resolve.py:399), as `_bare_name` does.
- **Focus words:** `the last estimate`, `the same estimate`, `apply X to the estimate` (uses focus).
- **Cross-kind bare names:**
  - `tell me about Driveway Maintenance` → it's a template, but planned as `list_estimates`.
  - `update Driveway Maintenance's description` should be the `template_edit` refusal.
  - *Fix:* when a bare name finds none in its kind, try the other kinds by exact name (today's `catalog_names.py`).
- **Catalog figures:** "costs the most" → price/rate; "highest-paid" → wage. `how much does 50 lb of X cost?` → `get_material {size}`, not `calculate`.
- **Relations:** `where is Polymeric sand used?` → properties related; `where does Ana live?` → her properties.
- **Tasks:**
  - `unarchive it` (task in focus) → `unarchive_estimate` (wrong domain).
  - `reopen it` → first status.
  - `push it to next week` → a due date.
  - `within the next two weeks` → today + 14.
  - `rename the fence task to …` asks which task.
- **Asks when it shouldn't:**
  - `update X's record` → the empty update (field-then-value);
  - `worth of E0042`;
  - `change the second one to 8000 sq ft` → adjust_assumption;
  - `add a work item to the estimate` → invents a name (make `description` optional and ask);
  - `I am stuck` → help;
  - `don't` / `please don't` / `no wait` / `leave it` → the not-waiting reply, not a clarify or "nothing to cancel".
- **Invalid plans:** `link it to X` with a focus ref and no domain (schema.py:379) — infer the domain from the freshest linkable anchor, or retry once on a validation error. There is no retry today (planner.py:148).
- **Dev 10-08:** `how many properties does Bob Residential has?` read Bob Residential as a contact (`filter.related` not found).

## Test coverage gaps

- About 250 supported reference rows have never been put to the planner, because the harness can't build them: §1.1 list refinements, §1.11, §10.4–10.9, §4.8, §7.11 and others. Most need a 2–3-turn conversation in the acceptance corpus.
- The parity run's state has no `planner_task_statuses` (`test_planner_parity_live.py:66`), so every task-status row was planned blind. Also, policy's status check is exact-name only: "Completed" against a company whose status is "Done" asks.
- Several rows were scored in the wrong state: task rows without `task_focus`, row 1883 in `task_focus` instead of `est`.
- `planner_acceptance.md` was last run on 4 conversations only. The full corpus hasn't been executed on the planner pipeline since.

## Suggested order

1. **P0** — safety first. Several are small: the negation guard, the tasks-off gate, the sold+status conflict.
2. **P2a + P2b** — the policy-refusal reply and the three missing refusal texts. One mechanical change, and it removes a whole class of fallbacks.
3. **P2c/d** — question ownership: make today's handler questions planner questions. This is the largest piece and the real switchover blocker.
4. **P1** — schema additions, each with its handler mapping.
5. **P2e–h** — executor filters, follow-ups and notes.
6. **P3** — batch the prompt lines with a few live checks. Then a parity run (on request), plus the acceptance corpus on the planner pipeline with task statuses in state.
