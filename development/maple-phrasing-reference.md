# Maple Phrasing Reference

Canonical catalog of user phrasings Maple supports, organized by resource. Add new use cases you want Maple to handle; Claude will update the ✅/⚠️ status after wiring the classifier rule or confirming existing behavior.

**Last updated:** 2026-09-27

### Recent changes

The full dated history lives in
[`maple-phrasing-changelog.md`](maple-phrasing-changelog.md) (split out of this
file 2026-09-27). **2026-09-27:** a multi-turn audit corrected rows found wrong
against the code and added an **Open gaps** line to each resource section
(§1–§7) citing the follow-ups in
[`code-review-followups.md`](code-review-followups.md); the fixes are planned in
[`plans/2026-09-27-maple-multi-turn-everywhere-design.md`](plans/2026-09-27-maple-multi-turn-everywhere-design.md).

Headlines, 2026-09-27 (multi-turn everywhere — design
[`plans/2026-09-27-maple-multi-turn-everywhere-design.md`](plans/2026-09-27-maple-multi-turn-everywhere-design.md)):

- **Safety** — every delete asks first and only a plain yes confirms it; Owners
  and Admins only; a request about notes or links never deletes the record
  (§9.9). Catalog writes run as the signed-in user; a cost edit keeps the
  material markup; Maple never creates a category or unit as a side effect.
- **One question at a time** (§10.6), **the record in focus** (§10.7), **"what
  about X?"** (§10.8), **"show more"** (§10.9), **thanks / cancel / repeat /
  start over** and language continuity (§10.10).
- **Done in the app** — Settings, team, billing, Load Standard, CSV import,
  units, divisions, unlinking records, duplicating, documents and photos are
  refused with where to do them (§9.8).
- **Tasks** (§7) — due dates, status verbs, give/unassign by teammate name,
  property links; creates that carry due date, assignee, status and property;
  "remind me to …" and to-do lists; list filters and "what's due today?";
  resumable value questions and menus; paging.
- **Estimates** (§1) — "it" means the estimate in focus for status, archive
  and link; questions about an estimate are answered from it (§1.2); menus
  and listed rows resume; lists filter by customer, property and date and can
  be refined; more create wordings; ~46 planner-only work-item phrasings
  promoted to grammar entries (§1.0).
- **Contacts, properties, notes** (§2, §3, §3.9) — notes added, read back and
  deleted; guide-worded links; creates that ask for what's missing; follow-up
  fields; "which contact?" menus; city and role filters; possessive looks
  ("show me Bob Lee's details", "what's Elm House's city?").
- **Materials, people, templates** (§4, §5, §6) — records found however
  they're named ("the Paver Patio template", "Topsoil's price", a bare
  "Black Mulch"); sizes of more than one word, and add / remove / reprice /
  rename / list a size; category moves; a new role or material asked for one
  field at a time; "list my roles" and the Heavy Equipment Operator role;
  templates filtered by name.
- **Dashboard** (§1.9, §7.5) — pipeline, backlog, completed, a summary,
  status and division breakdowns, recent estimates, "what's upcoming?"
  (overdue first) and "what's on my plate?", each in the dashboard's own
  terms; "and last month?" repeats the question for that period.
- **Across records** (§8) — "which properties use Black Mulch?", "which
  estimates use the Foreman role?", "what materials does E0042 use?" read the
  estimates' work items and answer (they were always empty, #682).

Headlines, 2026-09-24 → 2026-09-26:

- **2026-09-26** — work-item recurring schedules deferred from chat (user
  decision, §1.5.4 🛑); set them on the estimate page.
- **2026-09-26** — a position counted from the end ("the second to last …") is
  never read as a list row, the newest record or the open estimate — Maple
  asks. Tasks follow the same rule.
- **2026-09-26** — a list pick is the first reference in the message; a live
  estimate beats an archived one with the same title; a named estimate is
  looked up among all the company's estimates, and a customer name matches
  whole words only.
- **2026-09-26** — a note whose target Maple can't parse asks "Which estimate
  or work item should the note go on?" instead of landing on the open
  estimate; a bare "the work item" is not a reference.
- **2026-09-26** — with a note or description in the message, "archive" is an
  archive command only when the message starts with it.
- **2026-09-25** — routing convergence: every estimate phrasing a rule handles
  is an entry in `command_grammar.py` (§1.0); everything else goes to the edit
  planner (🤖) or the classifier. Routing snapshot test added.
- **2026-09-25** — whether a message answers Maple's open estimate question is
  decided in one place (`open_question.py`): a new request drops the question,
  "no" / "not now" cancels.
- **2026-09-25** — a write whose estimate or work item came from an anchor the
  user hasn't touched lately asks "Just to check: apply this to …?" first.
- **2026-09-24** — multi-turn estimate and work-item editing (§1.11): "this
  estimate" follows the portal page or Maple's last action, "this work item"
  follows its stable id, lists and menus are remembered, questions resume.
- **2026-09-24** — markup, overhead, tax and gross margin settable from chat
  (§1.5.7); material quantity/price and activity hours/rate/role editable
  (§1.5.5–§1.5.6); one all-or-nothing write path through the edit executor.
- **2026-09-24** — a note with no target annotates the record in play instead
  of creating a new one; a field's new value never picks the resource; a
  near-miss division gets a best-guess yes/no.

## How to read this doc

Each phrasing shows expected routing — the **intent** the orchestrator picks and the **agent** that handles it — plus its status:

- ✅ **rule** — handled deterministically by the rule-based classifier (`use_llm=False`). Works without an OpenAI key.
- 🤖 **LLM** — works on the live-LLM tier only (`use_llm=True`). Robust to paraphrase but slower and requires an OpenAI key.
- 🤖 **planner** — an estimate edit no grammar entry parses; only the LLM edit planner handles it (`MAPLE_EDIT_PLANNER_ENABLED`, off in tests). See §1.0 and §1.11.
- ⚠️ **gap** — not handled today. Use cases here are candidates for new classifier rules or handler work.
- 🛑 **refusal** — Maple is explicitly designed to refuse this phrasing (e.g., bulk delete, equipment management).

Token conventions used throughout:

| Placeholder | Example |
|---|---|
| `{property}` | `123 Main St` |
| `{contact}` | `John Doe` |
| `{material}` | `concrete blocks` |
| `{role}` | `Landscaper` |
| `{template}` | `Driveway Maintenance` |
| `{task}` | `fix the fence gate` (a task title) |
| `{EST}` | `E0042` — the prefix plus 4-7 digits (`E[0-9]{4,7}`). Case-insensitive; `#E0042`, `E-0042` and the spoken `E 0 0 4 2` all resolve. The id must be given **in full**: a partial body (`E42`) is refused rather than padded, and a bare number is not an id. Same rule as `{TASK}`. |
| `{TASK}` | `T0042` — the prefix plus 4-7 **digits** (`T[0-9]{4,7}`). Case-insensitive; `#T0042`, `T-0042`, `task t0042` and the spoken `T 0 0 4 2` all resolve. The id must be given **in full**: a partial body (`T42`) is refused rather than padded, and a bare number is not an id at all. |
| `{size}` | `12x12` |
| `{unit}` | `each`, `sq ft`, `linear ft` |

## Terminology note — the 6 + 1 Maple resources

| User-facing | Code domain | What it represents |
|---|---|---|
| **Property** | `property` | Job sites / addresses |
| **Contact** | `contact` | **Individuals** at a property (homeowner, manager, etc.) |
| **Material** | `material` | Catalog of physical products with sizes/prices |
| **People** | `labour` | Catalog of **role definitions** (Landscaper, Foreman). NOT individuals — that's Contact. |
| **Template** | `template` | Reusable estimate blueprints with predefined materials, activities, and cost parameters. |
| **Task** | `task` | Field-capture to-dos with statuses, assignees, property links, and convert-to-estimate. |
| **Estimate** | `estimate` | Quotes / job costings. Generated by an AI agent from a job description. |

Equipment is **explicitly blocked** via `is_equipment_request()` at the orchestrator layer — see §9.

## How to add new use cases

**Estimates:** a phrasing a rule should handle becomes an entry in
`platform/agents/estimate/command_grammar.py` with accept/reject examples in
`tests/test_command_grammar.py` and a row in §1.0 — never a regex elsewhere
(design 2026-09-25). A phrasing no entry covers is the planner's (🤖) or the
classifier's; mark it ⚠️ gap only if the live suite shows they miss it.

1. Add the phrasing under the appropriate resource section with status ⚠️ gap. Include the intended intent/agent if you have one.
2. Ping Claude with "add these phrasings to Maple" — Claude will write failing tests, implement the rule, and flip the status to ✅ here.
3. For phrasings that should be refused, add under §9 with status 🛑 and note why.

Tests live in `platform/tests/test_maple_crud_coverage.py` (matrix) and `platform/tests/test_maple_*.py` (targeted). Running the matrix regenerates `platform/tests/reports/maple_crud_gap_report.md` with live pass/fail counts.

---

# 1. Estimates

Estimate has 17 cases in the CRUD coverage matrix (`estimate_work_item_edits` 8, `estimate_outbound` 5, `assumption_adjustment` 4). Most of its surface — multi-turn generation, status transitions, work items, linking — doesn't fit the generic category templates, so it is curated here.

## 1.0 The written command list *(2026-09-25)*

The complete set of estimate phrasings a rule handles
(`agents/estimate/command_grammar.py`). Anything not here is 🤖 planner (edits)
or the classifier (routing). **2026-09-27:** the rows in §1.5–§1.11 that were
marked ✅ but reached only the LLM edit planner (off in tests) — about 46:
material and activity lines, division and total verbs, margin and markup
wordings, "scope" as a work item — now have entries below (design 2026-09-27
§7.2, decision 7), each checked end to end in the multi-turn corpus.

**Shared pieces:** up to three openers (hey, hi, maple, ok, yes, great,
perfect, thanks, please, now, also, and, actually, just, never mind, one more
thing, quick, can you, could you); a trailing please/thanks. An estimate is
named by an E-code, "this/the estimate", "the <title> estimate|job|quote" or
"the estimate for <name>". A work item is "work item N" / "the Work Item #N",
"the second work item", "the <label> work item", "work item <label>", "this/my
work item"; a work-item command may end "… on/from E0042" or "… on the Smith
estimate".

| Entry | Example | Routes to |
|---|---|---|
| list_estimates | "show me my estimates", "how many estimates do I have?" | list_estimates |
| get_estimate | "open E0042", "show me the estimate for the Smith property" | get_estimate |
| list_work_items / get_work_item | "show the work items on E0042", "show work item 2" | update_estimate (renders them) |
| create_estimate | "create an estimate for sod at 12 Oak St" | create_estimate |
| rename_estimate / set_estimate_field | "rename this estimate to Spring Cleanup", "update the description to Front yard refresh" | update_estimate (no estimate named: only while it's in focus) |
| add_work_item | "add a work item called Fence to E0042", 'add a work item "Build stone patio" to E0043', "add a work item to E0042" (asks the name), "Add a new work item to it." (asks the name; "it" = the last record worked with — the estimate or one of its work items; with a material or contact in focus it isn't the estimate's) | update_estimate |
| add_described_work_item | "Add a new work item to it. The client wants to build a patio in their backyard. It will be about 900 sq ft in size.", "add a work item to E0042: 200 sq ft paver patio with edging", "Add a new work item to it for 900 sq ft. The client wants a patio.", "add a work item for a cedar fence along the back and price it" (prices the description as new work; 15+ characters after the separator or "for") | update_estimate |
| remove_work_item / remove_pronoun | "delete work item 2", "remove the patio work item from E0043", "delete it" | update_estimate — "it" is the freshest anchor; the estimate itself → delete_estimate |
| rename_work_item / rename_pronoun | "rename work item 2 to Back Fence", "rename it to Back Fence" | update_estimate |
| set_work_item_field | "set the division of work item 1 to Maintenance", "update the description on work item 2" (asks the value), "change my work item division to Design/Build" | update_estimate |
| set_percentage | "set the markup on work item 2 to 20%", "set tax rate on the patio work item to 7% on E0043" | update_estimate |
| set_gross_margin | "make the gross margin 30%", "set the profit margin on the patio work item to 20%" | update_estimate |
| set_total | "set the total on work item 1 to $1,000" | update_estimate |
| add_note | "add a note to work item 2: check drainage", "leave a note on this estimate that says: …", "add a note: call Bob" (the record in focus), "add a note to work item 2 about drainage" (the body keeps "about …"), "add a note to that / our estimate saying …", "drop a note on E0042 saying …", "new note for this estimate saying …", "On work item 1, add a note: …" (target first) | update_estimate |
| add_material / remove_material / update_material *(2026-09-27)* | "add 20 concrete blocks to work item 2", "add 10 bags of mulch to the front patio work item", "remove concrete blocks from work item 2", "change the quantity of mulch in work item 1 to 12", "update the price of mulch in work item 1 to $5" — a plural finds the singular catalog item or line | update_estimate |
| add_activity / add_activity_prompt / remove_activity / update_activity *(2026-09-27)* | "add activity Grading with role Foreman for 4 hours to work item 2", "add an activity to work item 2" (asks its name, then adds it), "remove the Grading activity from work item 2", "make the excavation activity 8 hours", "change the role on the Excavation activity to Landscaper", "assign the Landscaper role to the cleanup activity", "update the rate for the Planting activity to $45/hr" | update_estimate |
| move_work_item_division / clear_percentage *(2026-09-27)* | "move / assign / put work item 2 to / under Tree Care", "drop the tax on work item 2" (to 0%) | update_estimate |
| *(2026-09-27 wordings on existing entries)* | set_total: "adjust / round / bump / reduce work item 2 to $X", "make work item 2 an even $X", "set a flat rate of $X on work item 2"; set_gross_margin: "change the margin on …", "I want a 30% margin on …"; set_percentage: "put a 15% markup on it"; rename_work_item: "change the name of work item 2 to …"; list_work_items: "how many work items does E0042 have?"; create_estimate: "put together / draw up / draft an estimate for …", "I need a quote for …", "quote a fence for Bob Lee". A work item may be called a "scope" or "job item" ("delete the Driveway scope from E0042"). | as the entry |
| *(ported)* set_status, set_estimate_description, set_estimate_title, estimate_note, generate_work_item, list_work_item_lines, query_work_item_field, adjust_assumption, apply_template, link_property | the older detectors, unchanged: "mark E0042 as sent", "retitle E0042 as …", 'Set note on E0059 to "…"', "generate a work item for …", "apply the Driveway Maintenance template to E0042" | the Estimate Agent (the orchestrator's own rules route these) |

**Refused by rule:** bulk delete and equipment (orchestrator, on the command
part only — never on a note body, a new name or a reply to Maple's question);
a note to a material or role. **Refused by the planner:** labor burden
(`labor_burden`) and a stated material cost (`material_cost`).

## 1.1 Count & status queries

| Phrasing                                             | Intent → Agent                                                 | Status                                                                                                                                                                                                                                                              |
| ---------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `how many estimates do I have?`                      | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `count my estimates`                                 | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `how many estimates with status draft?`              | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `what's the total estimates with status approved?`   | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `can you add up the estimates with status approved?` | `list_estimates` → Estimate Agent                              | ✅ rule *(closed in Phase A1)*                                                                                                                                                                                                                                       |
| `how many approved estimates do I have?`             | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `count my draft quotes` (quotes = synonym)           | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `what is the total value of the open estimates`      | aggregated `sum(grand_total)` across DRAFT/APPROVED/REVIEW/WON | ✅ rule *(closed in xfail-wave-3 Workstream C — `_AGGREGATE_VALUE_QUERY_PATTERN` + `_OPEN_ESTIMATE_QUERY_PATTERN` short-circuit `_handle_list_estimates` to a single dollar figure)*                                                                                 |
| `show me draft estimates from last week`             | `list_estimates` with `created_at` window                      | ✅ rule *(closed in xfail-wave-3 Workstream C — `_parse_estimate_date_filter` adds a `$gte/$lte` constraint on `created_at`)*                                                                                                                                        |
| `approved quotes over $10k`                          | `list_estimates` with status + `grand_total` range             | ✅ rule *(closed in xfail-wave-3 Workstream C — verbless plural-domain inference + `_parse_estimate_amount_filter` adds a `$gt`/`$lt` constraint on `grand_total`; `k`/`m` suffixes supported)*                                                                      |
| `what materials does {EST} use?`                     | `list_materials` filtered to one estimate's snapshot           | ✅ rule *(routes via `_CROSS_RESOURCE_QUERY_PATTERNS` with `filter_by={type=estimate, name=E0042}`; since 2026-09-27 (#682) it reads the materials of every work item — it read a top-level list `Estimate` doesn't have and always said "doesn't list any materials yet")* |
| `what roles are on {EST}?` / `which roles are on {EST}?` | `list_labours` filtered to one estimate's snapshot             | ✅ rule *(symmetric Labour-agent drilldown; since 2026-09-27 (#682) it reads the activities' and labour lines' roles in every work item, and "which roles …" is delegated — it showed "Intent identified: …")* |
| `how many estimates did I win this month?`           | `list_estimates` with status=WON + date filter                 | ✅ rule *(May expansion — "win" added as a verb-form alias for EstimateStatus.WON in `_estimate_status_from_text`)*                                                                                                                                                  |
| `show only estimates with Won status this month`     | `list_estimates` with status=WON + date filter                 | ✅ rule *(status + date qualifiers already compose; no new code needed)*                                                                                                                                                                                              |
| `show me all estimates older than 60 days`           | `list_estimates` with `updated_at <= cutoff`                   | ✅ rule *(`_AGE_FILTER_PATTERN` + age branch in `_parse_estimate_date_filter` returns `(None, cutoff)`; field is `updated_at` as of the 2026-06-02 expansion)*                                                                                                       |
| `show me estimates that are 30 days old`             | `list_estimates` with `updated_at <= cutoff`                   | ✅ rule *(2026-06-02 — `_AGE_DAYS_OLD_PATTERN`; "X days/weeks/months old" → at-least-X-old)*                                                                                                                                                                          |
| `estimates that are 40 days or older`                | `list_estimates` with `updated_at <= cutoff`                   | ✅ rule *(2026-07-08 — "N days/weeks/months **or older**" alternation added to `_AGE_DAYS_OLD_PATTERN`; verbless forms route via `_match_estimate_list_filter`)*                                                                                                      |
| `which estimates haven't been updated in 30 days?` / `estimates not touched in a month` | `list_estimates` with `updated_at <= cutoff` | ✅ rule *(2026-06-02 — staleness alternation in `_AGE_DAYS_OLD_PATTERN`; verbless forms routed via `_match_estimate_list_filter`)*                                                                                                                                   |
| `find estimates in draft` / `estimates in review`    | `list_estimates` with status filter                            | ✅ rule *(`in` connector in `_estimate_status_from_text`; only fires when the token after `in` is a known status — "estimates in Toronto" stays a property query)*                                                                                                   |
| `show me Draft estimates at property {property}`     | `list_estimates` with status + property cross-resource filter  | ✅ rule *(May expansion — "at\s+property" added to the property→estimate cross-resource pattern)*                                                                                                                                                                    |
| `list estimates for Bob Lee` / `show estimates for Elm House` | `list_estimates` for that customer (contacts → their properties) or property; a name that is neither is answered ("I couldn't find a customer or a property called …") | ✅ rule *(2026-09-27, #687 — the name was dropped and every estimate listed)* |
| `show me estimates from last month` | `list_estimates` over the past 30 days (a rolling window, like "from last week") | ✅ rule *(2026-09-27, #687 — "last" was read as "the latest one" and returned a single row)* |
| after a list: `just the drafts` / `which ones are on hold?` / `only the ones over $1000` / `only the ones from last month` / `only for Bob Lee` | the same list, narrowed | ✅ rule *(2026-09-27 — refinements chain; §10.8)* |
| after a list: `sort them by total` / `sort them by date` | the same list, highest value / newest first | ✅ rule *(2026-09-27)* |
| after a list: `what's the total of those?` / `add them up` / `how many is that?` | the combined value / the count of that list | ✅ rule *(2026-09-27)* |

## 1.2 Value / total queries for a specific estimate

| Phrasing                               | Intent → Agent                  | Status                        |
| -------------------------------------- | ------------------------------- | ----------------------------- |
| `what is the value of estimate {EST}?` | `get_estimate` → Estimate Agent | ✅ rule                        |
| `what's the total for {EST}?`          | `get_estimate` → Estimate Agent | ✅ rule *(closed in Phase A2)* |
| `how much is {EST}?`                   | `get_estimate` → Estimate Agent | ✅ rule *(closed in Phase A3)* |
| `what's the grand total for {EST}?`    | `get_estimate` → Estimate Agent | ✅ rule                        |
| `worth of {EST}`                       | `get_estimate` → Estimate Agent | ✅ rule                        |

Handler: `_handle_get_estimate` detects `_GRAND_TOTAL_QUERY_PATTERN` and leads the response with the dollar amount.

**Questions about one estimate** *(2026-09-27, #691)* — answered from the estimate, ahead of the user-guide help that used to take them (`agents/estimate/focus_questions.py`). The estimate is named by code or title, or is the one in focus ("it", or no reference at all). Plural "estimates", a work item, and how-to questions are not these.

| Phrasing | Answer | Status |
|---|---|---|
| `what's the status of {EST}?` / `is it sent?` | "E0001 'Oak St patio' is Draft." | ✅ rule |
| `what's the total on it?` / `how much is {EST}?` | "The total on E0001 … is $1,250.00." | ✅ rule |
| `who's the customer?` / `who is it for?` | the contacts on its property: "… is for Ana Reyes at 12 Oak St." | ✅ rule |
| `what's the address?` / `where is it?` | its property, or how to link one | ✅ rule |
| `what's the markup on this estimate?` / `what's the gross margin on it?` | per work item | ✅ rule |
| `when was it created?` / `when was {EST} last updated?` / `what's the code for this estimate?` | the date / the code | ✅ rule |
| `show me estimate {EST}` | the details now include "Property: 12 Oak St — Ana Reyes" | ✅ rule *(2026-09-27)* |

**Title-based lookup** *(May expansion)*: when no estimate code is found in the query, `_resolve_estimate_by_title` extracts a title from quoted text (`"Untitled Estimate"`) or `title/called/named X` phrasings and searches by substring match. Single match → returns the estimate. Multiple matches → lists them and asks the user to pick by code.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `tell me about estimate with title "Untitled Estimate"` | `get_estimate` → Estimate Agent | ✅ rule |
| `show me the estimate called "Driveway Replacement"` | `get_estimate` → Estimate Agent | ✅ rule |
| `pull up estimate named "Foundation Work"` | `get_estimate` → Estimate Agent | ✅ rule |
| `show me estimate details for {EST or title}` (e.g. `Spring Cleaning`) — response includes `created_at`, `updated_at`, the estimate ID/code, description, and notes | `get_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `_build_estimate_details_text` now renders Created / Last updated / Description / Notes / ID lines (blank optionals omitted; core fields keep the `—` placeholder). Bare titles resolve via `TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` (`agents/estimate/title_reference.py`). **Caveat:** the linked property NAME is still not rendered — it needs an async lookup from `Estimate.property`; follow-on.)* |
| `show me everything on the {title} quote` | `get_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — verified routing; pre-noun bare-title extraction. **2026-06-09:** an explicitly-named title now beats `active_estimate_code` — viewing one estimate then asking for another by name returns the NAMED one, not the viewed one.)* |
| `give me the rundown on the {title} estimate` / `full breakdown on the {title} job` | `get_estimate` → Estimate Agent | ⚠️ gap *(verified 2026-06-06: routes to `unknown` — "rundown"/"breakdown" aren't get-action cues)* |
| `what's the full info on {title}?` / `open up the {title} estimate` | `get_estimate` → Estimate Agent | ⚠️ gap *(verified 2026-06-06: "full info on Spring Cleaning" **misroutes to `get_contact`** via the person-name heuristic; "open up" routes to `unknown`)* |
| `when was the {title} estimate created?` | `get_estimate` → Estimate Agent (lead with `created_at`) | ⚠️ gap *(verified 2026-06-06: **misroutes to `create_estimate`** — the word "created" trips the create-action hint. Needs a when-was/question-form guard before the create hint, then a `created_at` lead in the get handler.)* |
| `when was {EST} last updated?` / `when did I last touch the {title} quote?` | `get_estimate` → Estimate Agent (lead with `updated_at`) | ⚠️ gap *(verified 2026-06-06: routes to `help`. Note the timestamps DO now appear when the user asks for the estimate's details.)* |
| `what's the ID for the {title} estimate?` | `get_estimate` → Estimate Agent (lead with `estimate_id`) | ⚠️ gap *(verified 2026-06-06: routes to `help`)* |

**Implementation note (updated 2026-06-06):** the response-detail half of this section shipped — `_build_estimate_details_text` carries timestamps/ID/description/notes, and bare-title resolution works wherever `_resolve_estimate_by_title` is consulted. What remains is **routing** for the casual/single-field forms above (rundown / full info / open up / when-was-X / what's-the-ID): they need get-cues or a question-form guard before the create/help classifiers, plus a focused-field lead (mirroring `_GRAND_TOTAL_QUERY_PATTERN`). Both former stretch items have since landed: `bid`/`proposal` are title-extraction nouns (`TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` in `agents/estimate/title_reference.py` accept `estimate|quote|bid|proposal`), and "the Smith job" resolves as an estimate reference (2026-09-24; §1.6).

## 1.3 Generation (multi-turn, LLM-driven)

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `create an estimate for {property} — needs 20 yards of concrete and two landscapers` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `draft a quote for a driveway replacement at 456 Oak Ave` | `create_estimate` → Estimate Agent | ✅ rule *(2026-09-27)* |
| `I need an estimate for [job description]` / `I need a quote for a new patio at 12 Oak St` | `create_estimate` → Estimate Agent | ✅ rule *(2026-09-27)* |
| `can you put together / draw up / write up / work up / prepare / price out an estimate for …` | `create_estimate` → Estimate Agent | ✅ rule *(2026-09-27 — "put together …" went to get_estimate)* |
| `quote a fence for Bob Lee` | `create_estimate` → Estimate Agent | ✅ rule *(2026-09-27 — was unknown)* |
| `create a residential estimate` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `new commercial quote` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `create an estimate to plant six hydrangea at the {property} residence` — property auto-linked at creation; "six" stays a plant quantity, never an area | `create_estimate` → Estimate Agent | ✅ rule *(2026-07-06 — property link + area grounding guard; the generation itself remains 🤖 LLM)* |
| `estimate for sod at {street address}` — address resolved against the Property catalog and linked | `create_estimate` → Estimate Agent | ✅ rule *(2026-07-06 — unique match required; ambiguous/unknown falls back to the ask-to-link follow-up)* |

Handled by `agents/estimate/conversation_guide.py` + `agents/estimate/assumption_defaults.py`.

**Assume instead of ask (2026-07-26; sizes became per work item 2026-08-10):** generation no longer blocks on missing details. Only an unknowable **work type** still asks a question ("What type of work needs to be done?"); missing area size, material preferences, etc. are **assumed** and generation runs immediately. The area question is never asked at all.

**Sizes are resolved per work item, after decomposition.** A multi-item request used to get ONE size from a first-keyword-match over the whole message — "build a paver patio and mow the lawn" produced a 5,000 sq ft *patio*. The architect now decomposes first, then each scope missing a size resolves its own (`resolve_scope_area_assumption`), in priority order:
1. **Stated size wins** — a scope whose description carries a size ("a 400 sq ft patio") gets **no** assumption; nothing was assumed.
2. **Company history** — median job size parsed (`parse_job_size`) from similar past **Won-and-beyond** work items, via the per-company vector search, queried with *that scope's* text rather than the whole message (`infer_area_from_history`; needs ≥2 parseable samples). *(The corpus tightened from Sent/Approved to Won/Scheduled/Completed on 2026-08-10 — a quote nobody bought is not history.)*
3. **Curated defaults table** — `WORK_TYPE_DEFAULTS`, recalibrated 2026-08-10 against typical residential jobs: sod 2,000 sq ft, lawn/mow 5,000 sq ft, patio 300 sq ft, deck 320 sq ft, beds 800 sq ft, driveway 600 sq ft, fence 150 linear ft, wall 40 linear ft, irrigation 5,000 sq ft. Sod split out of the lawn bucket so a mow request no longer suggests sod as its material.
4. **Researcher/architect LLM fallback** — anything still invented is reported in a structured `assumptions` array (never silently guessed).

Per-item jobs (`is_discrete_item_job`) get **no** invented area. That guard now runs per scope, and its locational-phrase handling was widened 2026-08-10 so a job located by an area noun ("replace 3 shrubs **in the mulch bed**", "remove one stump **from the back lawn**") is no longer misread as area-based.

Assumptions persist on `Estimate.assumptions`, each tagged with its work item (`scope`), and the reply appends a block the user can act on — see §1.3.1 for the follow-up adjustments.

**Three important branches before generation runs** (`routers/agent_helpers/delegate_create_estimate.py`):
- **Template named → AI generation is skipped entirely** and the estimate is instantiated from the template (§6.7) — no material/activity questions.
- **Work-type decline → re-ask, not cancel.** A "No"/"skip" to the work-type question re-asks (no sensible assumption exists for *what the job is*); only an explicit cancellation ("cancel", "never mind") aborts. See `routers/agent_helpers/estimate_gathering.py` (`is_cancellation_text`).
- **Property named in the request → linked at creation** (2026-07-06). `extract_property_reference` + `resolve_property_reference` (`agents/estimate/property_reference.py`) resolve "at the {Name} residence/property/house/…" and "at {street address}" against the company's Property catalog before sufficiency assessment. Unique match → the estimate is created already linked (and the post-create follow-up moves on to the description question); ambiguous or unknown → unchanged ask-to-link flow. Explicit mention overrides the `property_id` page context. If the request detours through gathering, the resolved property rides along in the `estimate_gathering_property` context key and `_finalize_gathering` links it.

**Area grounding guard** (2026-07-06, repurposed 2026-07-26): an extracted `area_measurements` whose units the user never typed is dropped (`is_area_value_grounded`) — guards against item counts becoming acreage ("plant six hydrangea" → ~~"six-acre"~~). With the area back on the missing list, Maple now **assumes** a size (history → table → LLM) instead of asking — except for per-item jobs (`is_discrete_item_job`), which get *no* invented area at all.

### 1.3.1 Assumptions & follow-up adjustments *(2026-07-26)*

When Maple assumes missing info, the creation reply ends with:

> I made a few assumptions — let me know if you'd like to adjust any:
> • Paver Patio — Area: 300 sq ft (average patio)
> • Lawn Mowing — Area: 5000 sq ft (average lawn)
> • Materials: standard pavers

Work-item assumptions are prefixed with their scope (2026-08-10) — with a size assumed per work item, bare "Area:" lines would be indistinguishable. Estimate-wide assumptions (`scope="estimate"`, e.g. materials) stay unprefixed.

Each assumption is stored structured on the estimate (`EstimateAssumption`: `key`, `label`, `assumed_value`, `unit`, `display_text`, `source` = history/table/llm/user). Follow-ups adjust them **deterministically** — no LLM regeneration:

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `change the lawn to be 800 sq ft instead` (active estimate in context) | `update_estimate` → Estimate Agent | ✅ rule *(deterministic routing in `OrchestratorAgent.process`, anchored on `active_estimate_code` or an explicit `{EST}` ref; shared detector `detect_assumption_adjustment` in `agents/estimate/assumption_handlers.py`)* |
| `make it 800 square feet` / `make it 800` (bare number → stored unit) | `update_estimate` → Estimate Agent | ✅ rule |
| `the area is actually 20x30` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the lawn to 100 square yards` (unit conversion within family) | `update_estimate` → Estimate Agent | ✅ rule *(cross-family — e.g. sq ft → linear ft — clarifies instead)* |
| `adjust the assumed area to 1000 sq ft on {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `assume premium pavers instead` | `update_estimate` → Estimate Agent | ✅ rule *(material swap: re-resolves the catalog match, swaps snapshots + pricing on the lines the old assumption produced, keeps quantities)* |
| `change the lawn to 8000 sq ft` (estimate has both a patio and a lawn) | `update_estimate` → Estimate Agent | ✅ rule *(2026-08-10 — names the work item; only that item is rescaled)* |
| `change the second one to 8000 sq ft` | `update_estimate` → Estimate Agent | ✅ rule *(2026-08-10 — positional reference, `match_positional_reference`)* |
| `make it 800 sq ft` with several assumed sizes | clarifies — *"Estimate {EST} has more than one assumed size — Paver Patio, Lawn Mowing. Which one should I change?"* | ⚠️ asks *(2026-08-10 — ambiguous; nothing is mutated)* |
| `change the lawn to 8000 sq ft` where a **Front Lawn** and **Back Lawn** both match | clarifies, listing both | ⚠️ asks *(2026-08-10 — a name matching several items is ambiguous, not positional)* |

**Targeting (2026-08-10):** with a size assumed per work item, an estimate carries several `area_size` records. The one to adjust is resolved by, in order: the **work item the user named** (distinctive-word overlap against each assumption's `scope`), a **positional reference** ("the second one"), or being the **only** candidate. Genuine ambiguity **asks** rather than guessing — a wrong pick silently rewrites the wrong work item's quantities.

**Size mechanics:** factor = new ÷ stored value; **only the targeted work item's** material/labour/equipment quantities and activity effort scale by the factor (`scale_job_item`), sub-totals recompute from the scaled lines, the grand total is recurrence-aware, and the stored assumption updates to the new value (marked "(adjusted)", `source="user"`) so successive adjustments compound (500 → 800 → 1000 = 1.6× then 1.25×). Work items whose total was **manually overridden** (§1.5.8) keep the override semantics — scaled proportionally, not recomputed. Confirmation: *"I've updated the area from 500 sq ft to 800 sq ft and recalculated estimate {EST} — new grand total: $X."*

Legacy estimates created before per-item sizes carry a single `scope="estimate"` assumption that genuinely described the whole estimate — those still rescale every work item, unchanged.

**Guards:** locked statuses refuse via the standard edit loader; absurd factors (×<0.01 or >100), out-of-range positions, and cross-family unit changes clarify without mutating; estimates with **no stored assumptions** (created before this feature, or fully-specified requests) get a graceful "no stored assumptions — use the estimate editor" reply; phrasings owned by other sub-ops (work items, status, financial fields, `{size} of {material}` quantities) are never claimed by this detector.

## 1.4 Status transitions

EstimateStatus has 13 values (`models/estimate.py:23`): `Generating`, `Failed`, `Draft`, `Sent`, `Review`, `Won`, `Lost`, `On Hold`, `Scheduled`, `Completed`, `Approved` (legacy), `Archived`, `Deleted`. `Generating`, `Failed` and `Deleted` are internal lifecycle states, never a chat target.

**State machine + authorization enforced (2026-06-11):** every phrasing below is additionally subject to `validate_estimate_status_transition` (`models/estimate.py`, mirrors `portal/src/lib/estimateStatus.ts`) and to the HTTP layer's role gates (send/unsend → Owner/Admin; archive/unarchive → Owner/Admin or creator). A recognized phrasing whose edge is illegal for the estimate's *current* status — e.g. `mark {EST} as won` on a Draft — or that the user isn't authorized for, refuses in Maple's persona voice instead of saving. See §9.6.

**Deterministic routing (2026-06-15):** the Orchestrator now routes status-transition phrasings to `update_estimate` via a `process()` fast-path (ahead of the LLM) and a `_classify_with_rules` branch, both gated on an estimate reference + the shared `parse_status_transition` matcher (`agents/estimate/text_helpers.py`). The ✅-rule rows below were previously 🤖 LLM and routed inconsistently. **Question forms** (`Can you …?`) are claimed by the help classifier and answered with an offer to proceed — see the last two rows.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `approve {EST}` | `update_estimate` → Estimate Agent | ⚠️ gap *(not parsed — `approve` isn't a status verb and no rule routes it; 2026-09-27 review)* |
| `mark {EST} as approved` / `mark {EST} as sent` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-15 — `as Y` shape via `parse_status_transition`)* |
| `set the status for\|of\|on {EST} to {Y}` (e.g. `set the status for E0042 to Sent`) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-15 — `_STATUS_TRANSITION_STATUS_REF_TO_PATTERN`; the estimate code may sit between "status" and "to". The originally-reported failing phrasing.)* |
| `archive {EST}` / `unarchive {EST}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-15 routing; archive/unarchive verbs are their own triggers)* |
| `reject the estimate` | `update_estimate` → Estimate Agent | ⚠️ gap *(not parsed; 2026-09-27 review)* |
| `send {EST} for review` | `update_estimate` → Estimate Agent | ⚠️ gap *(not parsed; 2026-09-27 review)* |
| `mark it as sent` / `mark it won` / `mark {EST} sent` / `archive it` / `place it on hold` (estimate in focus) | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-27 — "it" is the estimate in focus unless a task, contact, material or role is named; "as" is optional after "mark")* |
| `send it` / `email the quote to the client` | — | 🛑 redirect *(2026-09-27 — Maple never sends an estimate: create the document with the Documents button, send it, then "mark it as sent"; §9.8)* |
| `put {EST or title} on hold` | `update_estimate` → Estimate Agent | ⚠️ gap for a title *(2026-09-27 review: routes to `unknown` on the rules tier; with a code or "it" it works.)* Earlier: *(2026-06-09 — `_ON_HOLD_PATTERN` maps bare "on hold" (with a status verb incl. `put`/`place`) to ONHOLD; guarded by `_NOTE_OR_DESC_CUE_PATTERN` so a note/description body mentioning "on hold" isn't hijacked)* |
| `move this estimate to draft` | `update_estimate` → Estimate Agent | ⚠️ gap *(not parsed — `to draft` has no `status` terminator; 2026-09-27 review)* |
| `Can you set the status for {EST} to {Y}?` (question form) | `help` → Orchestrator, then **offer** | ✅ rule *(2026-06-15 — answered with "Yes — I can set {EST} to {Y} … Want me to go ahead?" + a `pending_status_transition` record; a following "yes" executes, "no" cancels. Requires an E-code + recognized target.)* |
| `yes` / `go ahead` (replying to the offer above) | `update_estimate` → Estimate Agent | ✅ rule *(`handle_pending_status_transition`, `routers/agent_helpers/pending_status_transition.py`)* |
| `update {EST or title} from {X} to {Y} status` (e.g. `from Sent to Review status`) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-08 — `_detect_status_transition` now recognizes the `update` verb and the `from X to Y status` / `to Y status` phrasings via `_STATUS_TRANSITION_TO_STATUS_PATTERN`, anchored on the trailing `status` word so it captures the target Y. Previously fell through to "What would you like to change?". **Same change** switched the status handler to the title-aware resolver `_resolve_estimate_code_or_title`, and made an explicitly-named title override `active_estimate_code` — fixes a data-integrity bug where naming an estimate by title while viewing another updated the WRONG (viewed) estimate. **2026-06-09:** extended title-awareness to ALL estimate UPDATE + READ sub-ops — work items, work-item fields, status — via the shared `_resolve_update_estimate_code` seam and a title-aware `_load_estimate_for_read`.)* |
| `update {EST or title} to {Y} status` (e.g. `to Review status`) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-08 — same `to Y status` pattern; works with `update`/`move`/`change`/`transition`/`switch`/`put`/`place` verbs)* |
| `what's the status of {EST}?` | `get_estimate` → Estimate Agent | ✅ rule *(2026-09-27, #691 — answered from the estimate; §1.2)* |

## 1.5 Work-item / line-item management

All work-item operations route to `update_estimate` → Estimate Agent. The phrasings a rule handles are entries in the written command list (§1.0, `agents/estimate/command_grammar.py`); anything else goes to the edit planner. The Estimate Agent's `WorkItemHandlersMixin` dispatches to the specific sub-operation.

**Work-item reference conventions** — users can identify a work item by:

| Placeholder | Examples |
|---|---|
| `{WI}` (positional) | `work item 1`, `work item #2`, `the first scope`, `the last line item` |
| `{WI}` (by description) | `the Driveway work item`, `the Foundation scope` |
| `{WI}` (contextual) | `this work item`, `my work item` (the anchored one). A bare `the work item` is **not** a reference — the grammar rejects it; say "this work item", its number or its name. |

The written command list (§1.0) names a work item as "work item …", "scope …" or "job item …" (2026-09-27); `line item` is **not** interchangeable with it. A bare "the scope" is no more a reference than "the work item" — Maple asks which.

### 1.5.1 Work-item CRUD (add / remove / rename)

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add a work item to the estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a job item to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a scope to the last estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a line item to this estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `create another scope on {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a work item called "Foundation Prep" to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `change work item #1 in {EST}` | `update_estimate` → Estimate Agent — asks what to change | ✅ rule |
| `remove work item 2 from this estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `delete the Driveway scope from {EST}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-27 — "scope" is a work item)* |
| `rename the scope to Foundation` | `update_estimate` → Estimate Agent — asks which work item ("the scope" names none) | ✅ rule |
| `how many work items does {EST} have?` | `update_estimate` → Estimate Agent | ✅ rule |
| `list the work items in {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `show me the scopes on this estimate` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.2 Division assignment

Division and description are editable via chat. The seeded values come from the `EstimateDivision` enum: Design/Build, Irrigation & Lighting, Maintenance, Snow & Ice, Tree Care, Turf & Plant Care, Unassigned. Each company owns editable `Division` rows bootstrapped from that same seed (`data/default_divisions.csv`).

**How a generated work item gets its division** (2026-07-31): the estimate architect classifies each scope against the company's own divisions — names *and* the coverage description each carries — and reports a `division_confidence` with it; that value rides through research onto the work item. A high-confidence vector match to an approved past estimate donates that estimate's division instead, at full confidence. Whatever arrives is re-anchored to a division the company actually has (`apply_company_divisions`); an unrecognized or low-confidence label falls back to scoring the description against those same divisions (`routers/estimate_helpers/division.py`), then `Unassigned`.

The fallback scorer ranks evidence in tiers: **the company's own description** for a division outranks its **name**, which outranks the built-in keyword vocabulary. So a company whose "Turf & Plant Care" description reads *"fertilization, weed and pest control, aeration"* has said sod installs belong elsewhere, and the built-in `sod` keyword no longer overrules it. Division descriptions are editable in Settings → Divisions and are seeded from `data/default_divisions.csv`.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `set the division of {WI} to Maintenance` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the division on {WI} to Snow & Ice` | `update_estimate` → Estimate Agent | ✅ rule |
| `assign {WI} to the Design/Build division` | `update_estimate` → Estimate Agent | ✅ rule |
| `move {WI} to Tree Care` | `update_estimate` → Estimate Agent | ✅ rule |
| `put {WI} under Irrigation & Lighting` | `update_estimate` → Estimate Agent | ✅ rule |
| `what division is {WI} in?` | `update_estimate` → Estimate Agent | ✅ rule |
| `which division does {WI} belong to?` | `update_estimate` → Estimate Agent | ✅ rule |
| `set all work items in {EST} to Maintenance` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `set the division of {WI} to {custom division}` (a division the company added or renamed) | `update_estimate` → Estimate Agent | ✅ rule *(2026-07-31 — was a ⚠️ gap earlier the same day: the handler validated against the `EstimateDivision` enum only and answered "isn't a recognized division" for a company's own rows. It now validates against the company's live divisions, canonicalizes casing/punctuation to the stored spelling, and lists the company's own divisions when it refuses.)* |
| `set the division of {WI} to Special Project` — a near miss (missing plural, typo, leading part of the name like `snow`) | asks "Did you mean Special Projects? Say yes and I'll use it."; **yes** applies it | ✅ rule *(2026-09-24 — was a flat refusal listing every division. `closest_division_name` (`routers/estimate_helpers/division.py`) proposes the single closest division; the batch is stashed as a `sub_op="edit_commands"` confirmation with the guess substituted, so "no" cancels and nothing is written until "yes". Two about-equally-close divisions (`Care` → Tree Care / Turf & Plant Care) or nothing close keeps the refusal and its list.)* |
| `move {WI} to {custom division}` — **without** the word "division" | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-27 — `move_work_item_division` takes any value and the handler checks it against the company's divisions.)* Earlier: ⚠️ gap *(2026-07-31 — the op detector (`work_item_handlers.py::_detect_work_item_field_op`) still gates on a hardcoded alternation of the seven seeded names, so a bare custom name isn't recognized as a division op at all. Any phrasing that includes the word "division" works for every value.)* |

### 1.5.3 Description

The rename handler already covers description updates. These phrasings extend the surface with "description"-keyword variants.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `rename {WI} to "Foundation Prep"` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the name of {WI} to "Driveway Installation"` | `update_estimate` → Estimate Agent | ✅ rule |
| `set the description of {WI} to "Excavation and grading"` | `update_estimate` → Estimate Agent | ✅ rule |
| `update the description on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `describe {WI} as "Remove existing pavers and re-lay"` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `what's the description of {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.4 Recurring schedule (🛑 deferred)

`JobItem.recurring` (bool) + `JobItem.recurrence` (`RecurrenceSchedule`) control repeat billing. `RecurrenceSchedule` supports three end types: `DATE_RANGE` (start/end month+year), `TOTAL_OCCURRENCES` (fixed count), and `SPECIFIC_MONTHS` (named months across years). Currently only `month` period is supported.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `make {WI} recurring` | — | 🛑 deferred |
| `set {WI} to recur monthly` | — | 🛑 deferred |
| `set {WI} to repeat every month` | — | 🛑 deferred |
| `make {WI} recurring from April to October` | — | 🛑 deferred |
| `set {WI} to 6 occurrences` | — | 🛑 deferred |
| `make {WI} recurring in April, May, June, July, August` | — | 🛑 deferred |
| `turn off recurring on {WI}` | — | 🛑 deferred |
| `remove the recurring schedule from {WI}` | — | 🛑 deferred |
| `stop {WI} from recurring` | — | 🛑 deferred |
| `is {WI} recurring?` | — | 🛑 deferred |
| `how many occurrences does {WI} have?` | — | 🛑 deferred |
| `what's the recurring schedule on {WI}?` | — | 🛑 deferred |
| `change the recurrence on {WI} to 12 occurrences` | — | 🛑 deferred |

**🛑 Deferred 2026-09-26 (user decision):** Maple no longer sets, clears or answers a work item's recurring schedule — set it on the estimate page. The `set_recurring` ported entry, its detector (`recurring_enable/disable/query`), the three handlers, their schedule parsing and the orchestrator's recurring routing rule were removed; a recurring request gets the ordinary "What would you like to change?" reply (or the edit planner's, which already treated recurrence as out of scope). Recurrence itself — the model, templates, grand-total math, the document generator and the portal — is unchanged, and work-item details still show "Recurring: Yes/No".

### 1.5.5 Materials within a work item

`JobItem.materials` is a `List[MaterialItem]` — each entry snapshots a catalog material with quantity and price. These phrasings manage the embedded material list on a specific work item, distinct from the top-level Material catalog CRUD in §4.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add concrete blocks to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add material {material} to {WI} in {EST}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-27)* |
| `add 50 concrete blocks to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add {material} with quantity 20 and size 12x12 to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove concrete blocks from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove all materials from {WI}` | — | 🛑 refused *(bulk-delete refusal — "remove all …" is a quantifier plus a delete verb, §9.1)* |
| `change the quantity of concrete blocks in {WI} to 100` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24 — now actually edits the line; it used to list the materials)* |
| `update the price of {material} in {WI} to $12` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24 — was misread as a set-total)* |
| `change the mulch quantity in {WI} to 8` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `set the price of pavers to $4.25` (no work item named) | `update_estimate` → Estimate Agent | ✅ rule + context *(2026-09-24 — only while a work item is in play; otherwise it is the catalog edit in §4. The work item holding that line is found automatically)* |
| `add mulch to the front patio work item` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24 — multi-word work-item names before the noun)* |
| `set the cost of {material} in {WI} to $3` | `update_estimate` → Estimate Agent | 🛑 refused *(a line's cost is the catalog snapshot; Maple offers price/quantity or the catalog)* |
| `how many materials are in {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `what materials does {WI} have?` | `update_estimate` → Estimate Agent | ✅ rule |
| `list the materials in {WI}` | `update_estimate` → Estimate Agent | ✅ rule |

**Disambiguation note:** `what materials does {EST} use?` (§1.1) queries all materials across all work items via the cross-resource drilldown. The phrasings above scope to a *single* work item within the estimate.

### 1.5.6 Activities within a work item

`JobItem.activities` is a `List[ActivityItem]` — each entry describes a labor task with an optional role (from the Labor catalog), rate, effort hours, and an optional effort-rate-card breakdown. Activities represent the labor component of a work item.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add an activity to {WI}` → *"What's the activity called?"* → `Seeding with role Landscaper for 3 hours` | adds it to that work item | ✅ rule *(2026-09-27)* |
| `add activity "Excavation" to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add an activity called "Grading" with role Landscaper to {WI}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-27)* |
| `add activity "Planting" with 8 hours of effort to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove the Excavation activity from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove all activities from {WI}` | — | 🛑 refused *(bulk-delete refusal, §9.1)* |
| `change the role on the Excavation activity to Foreman` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24 — re-snapshots rate and cost basis from the role's Rate)* |
| `assign the Landscaper role to the cleanup activity` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `set the effort on the Grading activity in {WI} to 12 hours` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `make the excavation activity 6 hours` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `update the rate for the Planting activity to $45/hr` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24 — a hand-set rate keeps the role's cost basis)* |
| `assign an effort rate card to the Excavation activity in {WI}` | `update_estimate` → Estimate Agent | ⚠️ gap *(no chat command for rate cards; the planner answers out-of-scope)* |
| `what activities are in {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `list the activities on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `how many activities does {WI} have?` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.7 Cost adjustments (markup, overhead, labor burden, tax)

`JobItem` carries four cost parameters: `profit_margin` (default 15%), `overhead_allocation` (default 0%), `labor_burden` (default 0%), and `tax` (default 0%). These multiplicatively affect the work item's `sub_total` and roll up into `Estimate.grand_total`.

**Naming:** the persisted field is still `profit_margin`, but it is a **markup** — applied to the subtotal and added on top — and the UI labels it **Markup %**. The field was not renamed (a migration across estimates, templates and company defaults for no user benefit). The **Gross Margin** shown beside it is computed, never stored — in the portal (`portal/src/utils/estimateCalculations.ts`) and, since 2026-09-24, server-side for Maple (`routers/estimate_helpers/calculations.py`: `work_item_gross_margin`), so Maple can report it (row below). Editing it in the UI or from chat writes back to `profit_margin`, so there is still exactly one stored number.

**Current policy (2026-09-24, reversing the 2026-04-21 UI-only decision):**
markup, overhead and tax are set directly and the reply echoes the new
work-item total. A **gross margin** ("margin", "gross margin", "profit
margin") writes the markup that delivers it — the margin itself is never
stored (server port of the portal math in
`routers/estimate_helpers/calculations.py`). Labor burden stays refused: the
estimate page doesn't edit it either.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `set the markup on {WI} to 20%` | `update_estimate` → Estimate Agent | ✅ rule |
| `put a 15% markup on it` | `update_estimate` → Estimate Agent | ✅ rule + context |
| `set the profit margin on {WI} to 20%` | `update_estimate` → Estimate Agent | ✅ rule *(gross margin → markup)* |
| `change the margin on {WI} to 25%` | `update_estimate` → Estimate Agent | ✅ rule *(gross margin → markup)* |
| `I want a 30% margin on the patio work item` | `update_estimate` → Estimate Agent | ✅ rule |
| `set overhead allocation on {WI} to 10%` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the overhead on {WI} to 15%` | `update_estimate` → Estimate Agent | ✅ rule |
| `set the overhead to 10%` (work item in play) | `update_estimate` → Estimate Agent | ✅ rule + context |
| `set tax on {WI} to 13%` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the tax rate on {WI} to 8.25%` | `update_estimate` → Estimate Agent | ✅ rule |
| `drop the tax on {WI}` | `update_estimate` → Estimate Agent | ✅ rule *(sets 0%)* |
| `set the labor burden on {WI} to 12%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `change the labor burden on the Foundation scope to 18%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `what's the profit margin on {WI}?` / `what's the gross margin on {WI}?` | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24 — computed from the lines; explains a missing activity cost basis)* |
| `what's the markup on {WI}?` / overhead / tax | `update_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `what's the subtotal of {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `how much is {WI}?` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `what's the total for {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |

**Conceptual questions route to HELP and are answered from the users' guide** (no estimate context needed, no value reported):

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `is my 10% markup the same as a 10% margin?` | `help` → Maple Guide | ✅ guide |
| `what's the difference between markup and margin?` | `help` → Maple Guide | ✅ guide |
| `what markup do I need for a 20% margin?` | `help` → Maple Guide | ✅ guide |
| `how is the profit margin calculated?` | `help` → Maple Guide | ✅ guide |
| `why does labor show no profit?` | `get_labour` → Labour Agent | ⚠️ gap |
| `why is my profit margin showing a dash?` | `help` → Maple Guide | ✅ guide |

⚠️ **`why does labor show no profit?` misroutes.** "labor" is a domain keyword,
so the classifier sends a conceptual question to the Labour agent, which tries
to look up a role. This is the general keyword-beats-concept routing problem
rather than anything specific to markup/margin, so it was left alone here.
Pinned by a strict `xfail` in `test_maple_help_coverage.py` — when routing is
fixed, that test flips red and this row gets updated.

### 1.5.8 Total amount adjustment

Sets a work item's total to an absolute dollar amount by **back-calculating its markup**, like the portal's Adjust pill (2026-09-24; it used to overwrite `sub_total`, which the next portal save recomputed from the lines and silently undid). The markup before the first adjustment is kept in `original_profit_margin`. Useful for rounding, flat-rate pricing, or manual corrections.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `adjust the total on {WI} to $1600` | `update_estimate` → Estimate Agent | ✅ rule |
| `set the total for {WI} to $2500` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the amount on {WI} to $3000` | `update_estimate` → Estimate Agent | ✅ rule |
| `round up {WI} to $2000` | `update_estimate` → Estimate Agent | ✅ rule |
| `round the total on {WI} to $1500` | `update_estimate` → Estimate Agent | ✅ rule |
| `make {WI} an even $5000` | `update_estimate` → Estimate Agent | ✅ rule |
| `bump {WI} up to $1800` | `update_estimate` → Estimate Agent | ✅ rule |
| `reduce {WI} to $1200` | `update_estimate` → Estimate Agent | ✅ rule |
| `set a flat rate of $750 on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |

## 1.6 Linking

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `link {EST} to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — orchestrator `_link_relationship` arm + `_LINK_VERB_TO_ESTIMATE_PATTERN`; was 🤖 LLM)* |
| `attach this estimate to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — "this estimate" resolves via `active_estimate_code` anaphora)* |
| `which property is this estimate for?` | `get_estimate` → Estimate Agent | 🤖 LLM |
| `set the property of estimate {EST} to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(the link branch `_is_property_link_request` matches `set ... property`; `_handle_update_estimate_property_link` resolves the property by name/address. **2026-07-28** — the property identifier was being extracted as `of this estimate to {property}` (the whole tail after the word "property"), so the lookup always missed; `_PROPERTY_NAME_PATTERN` now skips the estimate-qualifier preamble. **2026-07-28 (b)** — a near-miss ("primavara") now resolves fuzzily and asks for confirmation before linking.)* |
| `set the property of estimate {Estimate Name} to {property}` (estimate referenced by **title**) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — all update sub-handlers resolve via the shared `_resolve_estimate_code_or_title` (code → anaphora → latest → title); bare titles are extracted by `TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` (`agents/estimate/title_reference.py`) — **first word capitalized, 2+ words** (sentence-case tails OK, bounded by a connector stop-list) adjacent to "estimate"/"quote")* |
| `this quote is for the {property} property` / `the property for this quote is {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `_LINK_RELATIONSHIP_PATTERN`; **2026-07-28** — the `the property for this quote is {X}` variant routed correctly but extracted `for this quote is {X}` as the property name, so it never resolved. Same preamble fix.)* |
| `tie / connect / associate the {title} quote to/with {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — broadened verb set in `_LINK_PROPERTY_PATTERN` + `_LINK_VERB_TO_ESTIMATE_PATTERN` for bare property names)* |
| `assign {EST} to the {property} property` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `assign` in `_LINK_PROPERTY_PATTERN`; deliberately NOT in the bare-name pattern, so "assign" only links when "property" or an address is present)* |
| `change the property on the {title} quote to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06)* |
| `set the job site for this estimate to {address}` | `update_estimate` → Estimate Agent | ⚠️ gap *(routes to `update_estimate` ("job site" is a routing field token), but `_is_property_link_request` has no "job site" cue, so it falls to the generic clarification. Implementation: add a `job\s*site` alternation to `_LINK_PROPERTY_PATTERN`.)* |
| `the {title} job is at {address}` / `this estimate goes with {address}` | `update_estimate` → Estimate Agent | ⚠️ gap *("the {X} job" now resolves as an estimate reference (2026-09-24, Task 8 closed), but "goes with"/"is at" aren't link cues yet)* |

**Implementation note (shipped 2026-06-06):** estimate resolution on the linking path is code → `active_estimate_code` anaphora → "latest" → bare/quoted title (shared `_resolve_estimate_code_or_title`). Property resolution is name or bare address (`_extract_property_name` / `_extract_property_address`); possessive nicknames ("Bob's place") remain a softer follow-on gap. Routing note: the orchestrator's bare link-verb arm is deliberately broad — the `_estimate_ref` gate (estimate/quote/bid/proposal/E-code) is the load-bearing guard, and the contact↔property link rules earlier in `_classify_specific_phrasings` still win for contact links.

## 1.7 Anaphora / active estimate

"This estimate" is whichever was touched most recently: the estimate open in the portal (sent every turn as `client_context.viewed_estimate`; a new page visit takes the anchor) or the last one Maple acted on. A code or name in the message always wins (2026-09-24, `routers/agent_helpers/active_estimate.py`).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add a Landscaper to the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM + context |
| `update the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM + context |
| `show me the estimate` / `show me this estimate` | `get_estimate` → Estimate Agent | ✅ rule + context *(2026-09-24 — the router's get path now reads the anchor)* |
| `open the second one` (after a list of estimates) | `get_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `list my estimates` → `delete the first one` (another estimate open) | deletes the first **listed** row, after confirming | ✅ rule *(2026-09-27, #686 — it offered to delete the open estimate)* |
| `mark the patio estimate as sent` → *"I found 2 estimates… which one?"* → `E0001` / `2` / `the backyard one` | the request runs on that estimate | ✅ rule *(2026-09-27, #685 — the reply dead-ended)* |
| `add a work item called Fence` while viewing an estimate in the portal | `update_estimate` → Estimate Agent | ✅ rule + context *(2026-09-24 — the viewed estimate)* |
| `update the henderson job` (no estimate titled that, one is open) | `update_estimate` → Estimate Agent | ⚠️ gap *(2026-09-27 review: routes to `update_property` on the rules tier.)* Earlier: *(2026-09-24 — "I couldn't find … Did you mean E0042, the estimate you're working on?"; "yes" re-runs the request there)* |
| `this estimate` / `the last estimate` / `that one` | resolves via `active_estimate_code` | 🤖 LLM + context |
| `the same estimate` / `that estimate` / `the previous estimate` (after a note/description/work-item edit) | resolves via `active_estimate_code` | ✅ rule *(2026-06-07 — flat-result estimate updates now persist `active_estimate_code` in `finalize_result`, so anaphora anchors on the just-edited estimate; previously these asked "Which estimate?")* |

## 1.8 Estimate ↔ property/contact outbound drilldowns

Closed in xfail-wave-4 + 4.1 (plan: [maple-xfail-wave-4-estimate-outbound.md](plans/maple-xfail-wave-4-estimate-outbound.md)). Routes through `_CROSS_RESOURCE_QUERY_PATTERNS` with three cross-types:
- `cross_type=estimate` (Wave 4 Workstream A) — Property/Contact agents resolve the EST code via `find_estimate_by_code` and follow `Estimate.property` → `Property.contacts`.
- `cross_type=property` (Wave 4 Workstream B) — Estimate agent resolves the property via `find_properties_by_name_or_address` and constrains by `Estimate.property`.
- `cross_type=contact` (Wave 4.1) — Estimate agent resolves the contact via `find_contacts_by_full_name`, walks `Property.contacts` to a property-id set, then constrains `Estimate.property in [...]`.

| Phrasing                                           | Intent → Agent                                                                       | Status |
| -------------------------------------------------- | ------------------------------------------------------------------------------------ | ------ |
| `which property is this estimate {EST} linked to?` | `list_properties` → Property Agent (resolve estimate → return its linked property)   | ✅ rule *(Workstream A)* |
| `which contact is this estimate {EST} for?` (also without the `this`, e.g. `which contact is estimate E0042 for?`) | `list_contacts` → Contact Agent (resolve estimate → property → contacts) | ✅ rule *(Workstream A)* |
| `who is this estimate {EST} for?`                  | `list_contacts` → Contact Agent (response leads with the property name as join lead-in) | ✅ rule *(Workstream A)* |
| `show me estimates for property {property}`        | `list_estimates` → Estimate Agent (resolve property by name/address → constrain by `Estimate.property`) | ✅ rule *(Workstream B)* |
| `estimates linked to {property}` / `what estimates are for property {property}` | same as above | ✅ rule *(Workstream B)* |
| `show me estimates for {property} property` (suffix form, e.g. `Bob Residential property`) | `list_estimates` → Estimate Agent (suffix `property` strips from captured name) | ✅ rule *(Wave 4.1 follow-up)* |
| `show me estimates for {contact}` (capitalized name) | `list_estimates` → Estimate Agent (transitive: resolve contact → properties → estimates) | ✅ rule *(Wave 4.1)* |

**Empty-result copy** (so the user sees why nothing matched, instead of an empty list):
- Estimate not found → *"I couldn't find an estimate with code '{EST}'."*
- Estimate exists but `property` is `None` → *"Estimate {EST} isn't linked to a property yet."*
- Property linked but missing contacts → *"Estimate {EST} is linked to {property}, but that property has no contacts yet."*
- No property matches the constraint name → *"I couldn't find a property matching '{name}'."*
- No contact matches the constraint name → *"I couldn't find a contact matching '{name}'."*
- Contact resolves but isn't linked to any property → *"{Name} isn't linked to any properties yet, so there are no estimates to show."*

**Anchoring rules:**
- Property-anchored Workstream B fires on either the prefix form (`for property X` / `linked to (property)? X`) OR the suffix form (`for X property` / `for X properties`). Status phrasings like `estimates for approval` / `estimates for review` don't match (no `property` or `linked to` token).
- Contact-anchored Wave 4.1 uses a broad `estimates? for X` shape gated by a `fullmatch` on the captured slice in original case: it must be exactly a 2+ word capitalized name. `Bob Residential property` (trailing noun), `John Doe at 123 Main St` (locator suffix), and `bob jones` (lowercase) all fail the gate and fall through. Property-anchored patterns are checked first inside the same matcher, so `estimates for property Bob Jones` and `estimates for Bob Residential property` both win as `cross_type=property` before the contact gate runs.

## 1.9 Dashboard / analytics queries

Added in the May 2026 expansion. Routed via `_match_analytics_query` in the orchestrator to a new `analytics_estimates` intent handled by the Estimate Agent. Runs before `is_help_query` so question-word phrasings aren't swallowed by the help classifier — and since 2026-09-27 the router delegates a help-shaped message the orchestrator routed to an agent, rather than answering it from the help pre-check (#682). The chat answers are the dashboard's own cards: Pipeline, Backlog and Completed values, value by division, the pipeline-status chart, Recent Estimates, and Upcoming Tasks (§7.5).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what's the value in the pipeline?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what's my pipeline value in the last 30 days?` | `analytics_estimates` → Estimate Agent (custom window) | ✅ rule |
| `what's the backlog value?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what's my completed value?` / `how much was completed?` | `analytics_estimates` → Estimate Agent (COMPLETED only, last 30 days) | ✅ rule *(2026-06-20 — replaced the retired "won value" headline; see change log)* |
| `what's the value of my estimates?` / `how much are my estimates worth?` | `analytics_estimates` → Estimate Agent (total value, all-time) | ✅ rule *(2026-07-08 — `_analytics_total_value`: `sum(grand_total)` excluding Archived/Generating/Failed (Lost stays in — a lost bid is still an estimate); plural-only pattern so "value of estimate {EST}" stays §1.2. 2026-07-09 — yields to amount filters: "estimates worth **over $10k**" stays a `list_estimates` amount-threshold query.)* |
| `what's the value of the estimates I've done over the last 60 days?` | `analytics_estimates` → Estimate Agent (total value, custom window) | ✅ rule *(2026-07-08 — window bounds `updated_at`; response states the window)* |
| `give me a summary of my estimates from the last 60 days` | `analytics_estimates` → Estimate Agent (windowed Pipeline/Backlog/Completed) | 🤖 LLM *(2026-07-08 — `_analytics_windowed_summary`: all three buckets recomputed inside the user's window; previously the window was parsed and silently discarded, so every window returned identical numbers)* |
| `what's the breakdown of estimates by statuses this month?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what's the breakdown of estimates by divisions?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `breakdown by divisions last month` / `by statuses last quarter` / `by divisions last year` | `analytics_estimates` → Estimate Agent (bounded previous period) | ✅ rule *(2026-07-08 — previously reported the CURRENT period; "last/previous month|quarter|year" now maps to `last_month`/`last_quarter`/`last_year`)* |
| `breakdown by statuses for the previous quarter` | `analytics_estimates` → Estimate Agent (bounded previous period) | ✅ rule *(2026-07-08 — "previous …" synonym of "last …")* |
| `what is my won-lost ratio?` / `win-loss ratio` / `win/loss ratio` | `analytics_estimates` → Estimate Agent (WON vs LOST) | ✅ rule *(2026-06-02 — `parse_status_comparison`; count ratio + win-rate %)* |
| `won vs lost` / `how many estimates did I win vs lose?` | `analytics_estimates` → Estimate Agent (WON vs LOST) | ✅ rule *(2026-06-02)* |
| `draft vs approved estimates` / `compare won and lost estimates` | `analytics_estimates` → Estimate Agent (generic pair) | ✅ rule *(2026-06-02 — explicit "X vs Y" / "compare X and Y"; no win-rate framing for non-WON/LOST pairs)* |
| `what's my win rate?` / `what's my win rate this month?` | `analytics_estimates` → Estimate Agent (WON vs LOST, window-aware) | ✅ rule *(2026-06-02)* |
| `how am I doing on bids?` | `analytics_estimates` → Estimate Agent (WON vs LOST) | ✅ rule *(2026-06-02 — landscaper-friendly win-rate cue)* |
| `what's my pipeline?` / `how's my pipeline looking?` / `what's in my backlog?` / `how much have I completed this month?` | `analytics_estimates` → Estimate Agent | ✅ rule *(2026-09-27, design §7.5 — they went to the user guide)* |
| `show me my dashboard` / `give me a summary` / `how's business?` | `analytics_estimates` → Estimate Agent (Pipeline / Backlog / Completed) | ✅ rule *(2026-09-27 — they were unknown or help. A summary of one estimate — "give me a summary of E0042" — is not this.)* |
| `how many estimates are in each status?` / `pipeline by status` / `estimates by status` / `estimate value by division` | `analytics_estimates` → Estimate Agent (breakdown) | ✅ rule *(2026-09-27 — "in each status" counted all estimates; "by division" was unknown)* |
| `what's my pipeline?` → `and last month?` | the same question for last month | ✅ rule *(2026-09-27 — a read that named no period takes the new one, §10.8; it became a material lookup)* |
| `what are my recent estimates?` / `show me my most recent estimates` | `list_estimates`, the newest 8 — the dashboard's Recent Estimates | ✅ rule *(2026-09-27 — help, or one row for a plural ask)* |
| `how is the backlog value calculated?` / `what does pipeline value mean?` / `how is the completed value calculated?` | `help` → Orchestrator Agent | ✅ rule *(2026-06-20 — explanatory/definitional phrasing about a metric routes to HELP, not a value lookup. `_match_analytics_query` now redirects a recognized metric phrased with an explanatory cue (`calculated`/`computed`/`defined`/`mean`/…) to help; `calculated`/`computed` also added to `HELP_INSTRUCTIONAL_PATTERNS` for metrics without an analytics keyword.)* |

**Status comparisons / ratios:** `compute_status_comparison` counts each status (all-time unless a date window is given, in which case it constrains `updated_at`). `format_status_comparison` renders a reduced `A:B` ratio; the WON-vs-LOST pair additionally reports a win-rate percentage (`won / (won + lost)`). Generic pairs ("draft vs approved") report counts + ratio only.

**Time windows:** Pipeline/backlog/completed headline queries respect user-specified date ranges via `_parse_estimate_date_filter`, in two shapes: **word qualifiers** ("this month", "last week", "past quarter") via `_DATE_RANGE_FILTER_PATTERN`, and **numeric windows** ("last 90 days", "past 6 months", "last 2 weeks") via `_NUMERIC_DATE_RANGE_PATTERN`. *(2026-06-21 — the numeric form was previously unparsed: "completed value for the last 90 days" silently fell back to the 30-day default and answered "in the last 30 days". `_NUMERIC_DATE_RANGE_PATTERN` (`(last|past) <N> day|week|month|quarter|year`) now resolves it to a real window; `_describe_date_window` reports the exact day count ("in the last 90 days") for any span that isn't a canonical named period. Tests: `test_maple_phrasing_expansion.py::TestNumericDateRangeFilter`, `test_dashboard_backlog_parity.py`.)* When no date qualifier is present, the handler falls back to default windows: **pipeline = 90 days, completed = 30 days, backlog = all-time (no recency window)**. An all-time backlog answer reads "… in total" rather than "… in the last N days". *(2026-07-08 — the generic summary and the new total-value metric are window-aware too: `_analytics_windowed_summary` recomputes Pipeline/Backlog/Completed inside an explicit window, and `_analytics_total_value` sums non-archived `grand_total` over the window (all-time when none). Both state the window in the response. Age phrasings now include "N days **or older**".)* Breakdown queries use the `period` parameter passed to `compute_analytics`: the current "month"/"quarter"/"year" or — since 2026-07-08 — the bounded previous "last_month"/"last_quarter"/"last_year" (matched from "last …"/"previous …" phrasings before the bare substring checks, since "last month" contains "month").

**Status sets must mirror the dashboard cards** (`compute_analytics` in `routers/estimates.py`): pipeline = `[DRAFT, SENT, REVIEW, WON]`, **backlog = `[WON, SCHEDULED]` (all-time)**, **completed = `[COMPLETED]` (last 30 days)**. *(2026-06-20 — fixed a parity bug where the chat backlog headline summed only `[WON]`, so Maple reported $0.00 while the dashboard showed the real figure. `_analytics_headline_value` in `crud_handlers.py` now includes SCHEDULED.)* *(2026-06-20 — backlog relaxed from last-30-days to **all-time** in both `compute_analytics` and `_analytics_headline_value`: backlog = every Won/Scheduled estimate regardless of recency; dashboard card now labeled "All time".)*

## 1.10 Estimate-level field edits (title, description & notes)

These edit **top-level `Estimate` fields** (`title`, `description`) — distinct from the work-item (`JobItem`) description edits in §1.5.3. **Notes phrasings no longer write an `Estimate` field**: as of 2026-09-23 they file a real estimate-level `Note` on the Notes feed (section 9.6 of the user guide) via `_handle_add_estimate_note`; `Estimate.notes` itself has no writer left in Maple. Routing is `update_estimate` → Estimate Agent; the dispatcher is `_handle_update_estimate` (`crud_handlers.py:2786`).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `rename {EST} to {new title}` / `retitle this estimate as {new title}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-07-30 — `_detect_estimate_title_update` + `_handle_update_estimate_title`. Before this the chain had NO title branch: `rename` existed only as a **work-item** op, so an estimate-level rename fell through to the capability-list clarification.)* |
| `rename it to {new title}` (pronoun target) | `update_estimate` → Estimate Agent | ✅ rule *(resolves via `active_estimate_code`)* |
| `change/set the title of this estimate to {new title}` / `change the name of this quote to {new title}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-07-30)* |
| Renaming a **locked** estimate (Sent / Approved / Archived / Won / Completed …) | Refused | 🛑 refusal *(2026-07-30 — the handler resolves through `_load_estimate_for_update`, so the Draft/Review edit-lock covers the title exactly like description and work-item edits. Locked means locked for every content edit; notes are exempt — since 2026-09-23 they are `Note`s outside the lock.)* |
| `for estimate {EST}, add to the notes the following: "..."` | `update_estimate` → Estimate Agent | ✅ rule *(`_detect_note_update` → `_handle_add_estimate_note`; files a real estimate-level `Note` via `create_note_as`, added to the Notes feed (section 9.6) — `Estimate.notes` is never touched, and the note ignores the Draft/Review edit lock. 2026-06-07 — the quoted body is captured in full even with an apostrophe inside (`"Contact me if there's any issues"`); straight + curly, double + single quotes via the shared `QUOTED_VALUE_GROUP` (`agents/estimate/text_helpers.py`). 2026-09-23 — Option C.)* |
| `set the notes on {EST} to "..."` / `update notes: ...` | `update_estimate` → Estimate Agent | ⚠️ gap *(2026-09-27 review: routes to `unknown` on the rules tier.)* Earlier: *(same handler; 2026-09-23 — "set"/"replace" phrasing is still recognized but now **adds** a note rather than overwriting anything, since a Notes feed only ever grows)* |
| `for estimate {Estimate Name}, add to the notes the following: "..."` (estimate referenced by **title**) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — notes handler resolves via the shared `_resolve_estimate_code_or_title`; bare titles extracted by `TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` — first word capitalized, 2+ words (sentence-case OK) near "estimate"/"quote". The bare-title patterns run **before** the any-quoted fallback so a quoted note body is never mistaken for the title.)* |
| `add a note to the {title} quote: "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06)* |
| `update the description of estimate {EST} with the following: "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `_detect_estimate_description_update` + `_handle_update_estimate_description` set the top-level `Estimate.description`; quoted, colon, and unquoted `to ...` value forms supported, incl. an E-code sitting between the keyword and the connector)* |
| `set the description of estimate {EST} to "..."` / `change the estimate description to "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06)* |
| `change the description on the {title} quote to "..."` / `reword the description on this estimate to "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — title via bare-title extraction; "this estimate" via anaphora)* |
| `update the write-up/overview for {EST} to "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `write-up`/`overview` are description-cue synonyms)* |
| `put "..." as the overview for the estimate` | `update_estimate` → Estimate Agent | ⚠️ gap *(value-**before**-cue word order — the extractors expect the cue before the value; needs a `put "X" as the description/overview` pattern)* |
| `describe the {title} estimate as "..."` / `the description for the {title} job should be "..."` | `update_estimate` → Estimate Agent | ⚠️ gap *(`describe ... as` and `... should be` shapes have no extractor; "the {X} job" also isn't an estimate reference)* |
| `make a note on {EST} that ...` / `leave a note on {EST}: "..."` / `tack a note onto the {title} quote: "..."` | `update_estimate` → Estimate Agent | ✅ rule for `make`/`leave` *(2026-09-24 — `is_note_add_request` routes them and `_NOTE_TARGETED_LEAD_IN` extracts the `... that X` body; `tack` is still a gap.)* ⚠️ *(historical, corrected 2026-06-06: the routing verb list lacks `make`/`leave`/`tack`, so these never reach the agent on a fresh turn; "make a note ... that X" additionally needs a generic `note ... that` tail extractor (only `remember ... that` exists). Reachable today only when the orchestrator already routed to `update_estimate` for another reason.)* |
| `note on the {title} job: ...` | `update_estimate` → Estimate Agent | ⚠️ gap *(verbless + "the {X} job" isn't an estimate reference — Task-8 stretch)* |
| `jot down on the {title} estimate: "..."` / `remember on this estimate that ...` / `FYI on the {title} job: "..."` (with an estimate/quote token) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — informal cues `jot`/`fyi`/`remember`/`write down` in `_NOTE_UPDATE_CUES` + value extractors (`_NOTE_WITH_COLON_SEP` broadened, new `_NOTE_REMEMBER_TAIL`); routed end-to-end by the orchestrator's value-bearing `_informal_note` arm. 2026-09-23 — always **adds** a `Note` to the estimate's Notes feed; `Estimate.notes` is untouched. Note: the phrase still needs an estimate/quote/EST token — "the Smith job" alone doesn't reference an estimate.)* |
| `create a note for this estimate: …` / `create a note on E0053: …` / `make a note on this estimate that …` / `new note for this quote: …` | `update_estimate` → Estimate Agent (estimate-level Note) | ✅ rule *(2026-09-24 — was `create_estimate`. `create a note for this work item: …` files a work-item Note.)* |
| `Add a note that says: …` / `add a note: …` / `create a note: …` / `leave a note that …` / `add note - …` — **no target at all**, estimate in play | `update_estimate` → Estimate Agent (estimate-level Note, even with a work item anchored) | ✅ rule *(2026-09-24 — was `create_estimate`: "add" plus the borrowed estimate domain read as a create)* |
| `write down on the {title} estimate that ...` | `update_estimate` → Estimate Agent | ⚠️ gap *(`write down` is a cue, but only `remember` has a `... that ...` tail extractor; needs the tail generalized)* |

**Title-vs-target trap (2026-07-30):** the rename handler must resolve its target from the message **head**, never the raw query. `_resolve_estimate_code_or_title` treats the bare word "title" as an explicit name cue (`TITLE_BARE_RE`), so `change the title of this estimate to Patio Rebuild` would otherwise hunt for an estimate literally named *"of this estimate to Patio Rebuild"*, miss, and refuse instead of falling back to the active estimate. `_detect_estimate_title_update` returns `(new_title, target_text)` for exactly this reason. Two exclusions run against that **head**, never the new value (an estimate may legitimately be titled "Scope of Work"): a work-item noun in the head (`rename the patio work item|scope to X`) leaves the message to the work-item op, and a *qualified* name field (`set the name **of the property** on {EST} to X`) leaves it to the property-link branch — without that second guard the value was silently written into `Estimate.title` instead.

**Disambiguation note:** `set the description of {WI} to "..."` (§1.5.3) targets a **work item** and is already ✅ rule. The phrasings here target the **estimate as a whole** — the implementation must detect the absence of a work-item reference (no `work item` / `job item` / `scope` / `line item` token) to route to the estimate-level handler rather than the work-item one.

**Implementation note (shipped 2026-06-06; notes behavior changed 2026-09-23):** all update sub-handlers (description / notes / property-link) resolve the estimate by **code → `active_estimate_code` anaphora → "latest" → quoted-or-bare title** via the shared `_resolve_estimate_code_or_title`. The verb (`set`/`change`/`replace`/`overwrite`/`rewrite` + note vs. everything else, incl. all informal cues) still selects a "mode," but as of 2026-09-23 (Option C) every mode **adds** a `Note` via `_handle_add_estimate_note` → `create_note_as` — nothing ever writes `Estimate.notes` again, and the note ignores the Draft/Review edit lock. Dispatcher order in `_handle_update_estimate`: work-item ops → status → **description** → notes → property link → template (description sits above notes so a "description" cue never lands in the notes branch; work-item ops stay first so `description of {WI}` is untouched). **Remaining ⚠️ in this section:** value-before-cue (`put "X" as the overview`), `describe ... as` / `should be`, routing verbs `make`/`leave`/`tack`, a generalized `note ... that` tail, and "the {X} job" as an estimate reference (Task-8 stretch).

---


## 1.11 Multi-turn work-item conversation *(2026-09-24)*

Work items have no names, only a description and a position, so Maple keeps
three kinds of memory (`agents/estimate/work_item_context.py`): an anchor on
the last work item resolved (by its stable `JobItem.id`), the list it last
showed, and the question it last asked.

| Phrasing (turn by turn) | What happens | Status |
|---|---|---|
| `show work item #2` → `rename it to Patio lights` | the rename lands on #2 (the anchor), even if items were reordered | ✅ rule |
| `list the work items` → `delete the second one` | removes the 2nd row shown (asks to confirm first) | ✅ rule |
| `list the work items` → `rename the fifth one to X` (only 3 listed) | "I only listed 3 work items — which one did you mean?" | ✅ rule |
| `rename the patio work item to X` → *(two patios)* → `2` / `the front one` | the menu answer resumes the rename on that item | ✅ rule |
| `add a work item` → *"what should I call it?"* → `Retaining wall` | creates it and anchors it | ✅ rule |
| `update the description of work item 2` → *"what should it be?"* → `Patio string lights` | sets it | ✅ rule |
| `rename work item 3 to X` → *"which estimate?"* → `E0042` | resumes on E0042 | ✅ rule |
| `add a note to work item 2: check drainage` / `note on this work item: …` | files a work-item Note (outside the edit lock) | ✅ rule |
| `add a note to the patio work item` → *"What should the note say?"* → `check the grade` | files the reply as a note on the patio work item | ✅ rule |
| `add a note to work item 2 about drainage` / `… regarding the gate` | files "about drainage" on work item 2 | ✅ rule *(2026-09-27, #684 — it filed "to work item 2 about drainage" on the estimate)* |
| `On work item 1, add a note: check drainage` | files it on work item 1 | ✅ rule *(2026-09-27, #665)* |
| `add a note to that estimate saying call the client` / `drop a note on {EST} saying …` / `new note for this estimate saying …` | files the estimate note | ✅ rule *(2026-09-27, #664 — these asked where the note should go)* |
| `set the markup on all work items to 20%` / `… for work items 1 and 2 …` | not a listed command: the edit planner's. Without it, Maple asks what to change ("… What would you like to change?") and writes nothing | 🤖 planner *(corrected 2026-09-27 — the "one work item at a time" reply no longer exists)* |
| `remove work item 1 and set the markup on work item 2 to 20%` | the edit planner types both; without it, Maple asks what to change and writes nothing | 🤖 planner *(corrected 2026-09-27 — the "one change at a time" reply no longer exists)* |
| `also raise the markup by 5%` / `change the markup by 5%` | a relative change isn't a listed command: the planner's. Without it, Maple asks what to change; a change BY 5 is never applied as the new value | 🤖 planner *(corrected 2026-09-27 — the "What should the new markup be?" reply no longer exists)* |
| `create a task to set the markup to 20%` / `don't drop the markup on work item 2` / `if we set the markup to 20% …` | not an estimate edit; nothing is written | ✅ rule |
| `add 500 sq ft of sod to E0001` | prices the scope into E0001 (never a new estimate) | ✅ rule |
| `delete work item 1 and …` → *question* → `Yes` | a bare yes/no never repeats a delete from the chat history | ✅ rule |
| `list the work items` → `rename the second one to Front Patio Scope` | renames that work item; a work-item word in the new name doesn't stop the pick, and an ordinal rename never retitles the estimate | ✅ rule |
| `list the work items` → `add a note to the second one: check the line item` | files the note on the second work item | ✅ rule |
| `set the markup on the patio job to 20%` (open estimate has one "patio" work item) | intended: sets it on that work item, not the anchored one; today the rules tier routes it to `unknown` | ⚠️ gap *(2026-09-27 review)* |
| `set the tax on the lawn work item on the patio job to 13%` / `remove work item 1 from the patio job` | the work item the message names, not the patio one | ✅ rule |
| `rename the patio work item to X` → *(menu)* → `set the markup on work item 1 to 15%` / `show me the 2nd estimate` | a new request, not a menu pick; only a bare pick answers the menu | ✅ rule |
| `update the description on work item 2` → *"what should it be?"* → `cancel` / `no` / `never mind` | "No problem, I've left it as is." — nothing is written | ✅ rule |
| `update the description on work item 2` → *"what should it be?"* → `list my estimates` / `show me estimate E0004` | the question is dropped and the request runs | ✅ rule |
| `rename the patio work item on the Smith estimate to Back Patio` | renames the work item; never retitles the estimate | ✅ rule |
| `add a task to follow up on E0042` / `add Bob as the contact on E0042` | creates the task / contact; E0042 is not priced | ✅ rule |
| `rename the patio work item to X` → *(menu "Add mulch beds / Remove stump")* → `Remove stump` | picks that row — a row's own description is always a pick | ✅ rule |
| `update the description on work item 2` → `Show homeowner the revised quote before starting` | sets it as the description | ✅ rule |
| `add a note to the patio work item please` → *"What should the note say?"* → `gate code 1234` | filed on the patio work item | ✅ rule |
| *(menu open)* → `delete all work items` / `add equipment to the patio` | the bulk-delete / equipment refusal — an open question never takes them | 🛑 refused |
| *(material or contact opened last)* → `set the price of mulch to $5` / `set the markup to 25%` | goes to that record's agent, not the estimate left earlier | ✅ rule |
| `the pavers on the front patio actually cost us $3.50 now` (planner) | the material-cost refusal; a cost is never written as the price | 🛑 refused |
| `set the overhead lighting work item's markup to 20%` | sets the markup on "Overhead lighting" — a field word in a name is never the field | ✅ rule |
| `delete estimate E0042` → `confirm` (Member, not the creator) | "Only the estimate's creator or an Owner can delete …" — the Delete button's rule | 🛑 refused |
| `reduce the markup 5%` / `raise the tax 2%` | the planner's, as above; without it Maple asks what to change and writes nothing — a change BY 5 is never applied as the new value | 🤖 planner *(corrected 2026-09-27)* |
| `why is the markup 20%?` / `i think the markup of 20% is too high` | not an edit; nothing is written | ✅ rule |
| `set the hours on the overhead pruning activity to 6` | edits the activity's hours; "overhead" is part of its name | ✅ rule |
| `rename the grading activity to Rough Grade` | "I can't rename an activity from chat yet" — never retitles the estimate | 🛑 refused |
| `add a work item Patio, add 10 pavers to it` (planner) | the pavers go on the new Patio work item | 🤖 planner |
| `generate a work item for installing 200 sq ft of pavers` / `add a scope for … and price it` | runs the estimate pipeline for that scope and appends it (15–30 s) | ✅ rule |
| `show work item #1` | description, division, materials, activities, markup/overhead/tax, gross margin, sub-total | ✅ rule |
| anything else about an open estimate that no rule recognizes (`we'll need twelve dozen pavers after all and the customer is tax exempt`) | the edit planner proposes typed commands; validated against the estimate and applied all-or-nothing | 🤖 planner |

**Edit planner guardrails** (`agents/estimate/edit_planner.py`): runs only
after the estimate is resolved and editable; at most 5 commands; every
work-item target must exist in the snapshot it was shown or the whole plan is
rejected; it cannot name another estimate (it says `different_estimate`);
reads get the capability message; removals still ask for confirmation.
Disabled by `MAPLE_EDIT_PLANNER_ENABLED=false` (the test suite's default).

**Open gaps:** #683, #689, #696, and older #22, #23, #279, #329, #354, #406, #437, #439, #569, #614, #615, #616, #617, #645, #659, #663, #668, #670 (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #664, #665, #666, #671, #673, #677, #682, #684, #685, #686, #687, #691, #697, #334, #436.

# 2. Properties

## 2.1 Direct imperatives (all ✅ rule)

| Phrasing | Intent → Agent |
|---|---|
| `create a new property` → *"What's the property's address? For example: 20 Birch Rd, Toronto, ON."* → `20 Birch Rd, Toronto, ON` | `create_property` → Property Agent *(2026-09-27 — it asked for "the missing property details" without naming any)* |
| `add a property called Birch Cottage` | `create_property` → Property Agent *(2026-09-27)* |
| `list all properties` | `list_properties` → Property Agent |
| `delete the property {property}` | `delete_property` → Property Agent |

## 2.2 Casual phrasings (all ✅ rule)

| Phrasing | Intent → Agent |
|---|---|
| `show me my properties` | `list_properties` → Property Agent |
| `what properties do I have?` | `list_properties` → Property Agent |
| `pull up property {property}` | `get_property` → Property Agent |

## 2.3 Possessive

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me {property}'s details` | `get_property` → Property Agent | ✅ rule |
| `what's {property}'s city?` / `what's the city of {property}?` | `get_property` → Property Agent | ✅ rule |
| `update {property}'s record` → *"which fields?"* → `city` → the value | `update_property` → Property Agent | ✅ rule |

These routed but reached no record until 2026-09-27: the agent couldn't read a name followed by "'s". The router now rewrites a possessive or "the <field> of <name>" look — for a property, contact, material, role or template whose exact name it is, and only one kind — into the form its agent reads (`agents/conversation/catalog_names.py::_record_reference`). A name that is nobody's is left alone, and "{name}'s estimates" / "{name}'s notes" are other questions (§8, §3.9).

## 2.4 Count (all ✅ rule)

`how many properties do I have?` · `count my properties` · `total number of properties`

## 2.5 Filter / find (all ✅ rule)

`find properties named Toronto` · `search for properties matching Toronto`

`how many properties are in Toronto?` → "You have 2 properties in Toronto." · `list properties in Guelph` · `show me properties in Toronto` — the city filters (2026-09-27, #687: every property was listed or counted); a city nobody has is said so ("You don't have any properties in Ottawa").

## 2.6 Field-targeted update

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `change the city of {property} to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `update the city on {property} to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `set {property}'s city to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `update the name of {property} to Oak House` | `update_property` → Property Agent | ✅ rule *(2026-09-27 — it wrote the name "12 Oak St to Oak House" and looked the property up by the new name)* |
| right after a property is created or shown: `zip M4B 1B3` / `the postal code is M4B 1B3` / `its city is Guelph` | `update_property` on that property | ✅ rule *(2026-09-27, §10.8)* |
| `add a note to {property}: "gate code 4411"` / `set the notes on {property} to "..."` | `update_property` → Property Agent | ✅ rule *(2026-09-17 — `notes` is no longer a `Property` field; the phrasing creates a real `Note`, authored by the acting user, instead of writing a scalar. Also handled inline on create: `create a property at 123 Main St with notes: gate code 4411`.)* |

## 2.7 Address formats accepted on create (all ✅ rule)

The regex fallback in `_extract_fields_from_message` parses these single-line formats so the user can supply a complete address in one message:

| Format | Example |
|---|---|
| Canadian, comma-separated with postal | `123 Main Street, Vancouver, BC, V1V 2A2` |
| Canadian, comma-separated with country | `123 Main Street, Vancouver, BC, Canada, V1V 2A2` (or postal-then-country) |
| Canadian, partial (street + city + state) | `888 River Road, Richmond, BC` |
| Canadian, "at" prefix space-separated state | `at 123 Maple Drive, Surrey BC V3T 4R5` |
| **US, "City, ST ZIP"** (no comma between state and ZIP) | `155 Asharoken Ave, Northport, NY 11768` |
| **US, ZIP+4** | `155 Asharoken Ave, Northport, NY 11768-1234` |

Comma-less unformatted addresses (`1036 Fort Salonga Rd Northport NY`) are intentionally **not** parsed by regex — the LLM entity extractor handles them.

## 2.8 Verbless (all ✅ rule — Phase 2a address-pattern resolver)

| Phrasing | Intent → Agent |
|---|---|
| `{property}` (bare address) | `get_property` → Property Agent |
| `I want the details for {property}` | `get_property` → Property Agent |
| `tell me about {property}` | `get_property` → Property Agent |

## 2.9 Property gaps

| Phrasing | What happens | Status |
|---|---|---|
| `remove {contact} from {property}` | nothing is deleted; Maple says the link is removed in the app (§9.8, #679) | 🛑 redirect |
| a property whose name looks like a person's (`show me Elm House`) | the property, when that is its exact name and no contact's | ✅ rule *(2026-09-27 — it answered "No contact found with name 'Elm House'")* |
| `N <words> way` / `court` / `ct` phrasings (`60 minutes one way`) | `_ADDRESS_PATTERN` false-matches them as a property lookup (#49) | ⚠️ gap |

Cross-resource phrasings (e.g. `who lives at {property}?`) are tracked under §8.

**Notes, links and follow-ups** for properties and contacts are in §3.9.

**Open gaps:** older #49, #101, #322 (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #679, #682, #683, #687, #697.

---

# 3. Contacts

## 3.1 Direct imperatives (all ✅ rule)

`create a new contact` · `list all contacts` · `delete the contact {contact}`

`create a contact` → *"What's the contact's name? First and last, please."* → `Dan Park` creates Dan Park *(2026-09-27 — the bare name reply asked the same question again)*; `add a contact named Dan Park` creates one *(2026-09-27 — it looked for a Dan Park to update)*.

## 3.2 Casual phrasings (all ✅ rule)

`show me my contacts` · `what contacts do I have?` · `pull up contact {contact}`

## 3.3 Possessive

| Phrasing | Status |
|---|---|
| `show me {contact}'s details` | ✅ rule |
| `what's {contact}'s phone?` / `what's the phone number for {contact}?` / `what's Bob's email?` (first name) | ✅ rule |
| `update {contact}'s record` → *"which fields?"* → `phone` → the number | ✅ rule |

Routed, but found no one until 2026-09-27 — see §2.3.

## 3.4 Count (all ✅ rule)

`how many contacts do I have?` · `count my contacts` · `total number of contacts`

## 3.5 Filter / find

`find contacts named Smith` · `search for contacts matching Smith` — ✅ rule.

`show contacts in Toronto` · `how many contacts are in Guelph?` · `list homeowners` · `show me the property managers` · `which contacts are administrators?` · `list homeowners in Guelph` — ✅ rule *(2026-09-27, #687: city and role filters; the list came back unfiltered)*. A filtered list is remembered, so `show me the second one` picks from it.

## 3.6 Field-targeted update

| Phrasing | Status |
|---|---|
| `change the phone of {contact} to 555-1111` | ✅ rule |
| `change Ana's phone to …` with two Anas → *"More than one contact matches that: 1. Ana Reyes 2. Ana Lopez"* → `Ana Lopez` / `2` / `the second one` | ✅ rule *(2026-09-27 — it said "Multiple contacts matched" and the reply dead-ended)* |
| right after a contact is created or shown: `his phone is 519-555-1234` / `her email is …` / `add his email …` / a bare email or phone number | ✅ rule *(2026-09-27, §10.8 — these were unknown, or started a second contact)* |
| `update the phone on {contact} to 555-1111` | ✅ rule |
| `set {contact}'s phone to 555-1111` | ✅ rule |
| `add a note to {contact}: "..."` / `set the notes on {contact} to "..."` | ✅ rule *(2026-09-17 — `notes` is no longer a `Contact` field; the phrasing creates a real `Note`, authored by the acting user, instead of writing a scalar. Also handled inline on create.)* |

## 3.7 Verbless (all ✅ rule — Phase 2b person-name heuristic)

`{contact}` (bare name) · `I want the details for {contact}` · `tell me about {contact}`

## 3.8 Contact gaps

| Phrasing | What happens | Status |
|---|---|---|
| `link {contact} to {property}` on the LLM tier | a correct LLM answer can be demoted to `off_topic` (#690) — the rule tier now handles the guide's phrasings first (§3.9) | ⚠️ gap (LLM tier) |

Cross-resource phrasings (e.g. `where does {contact} live?`) are tracked under §8.

## 3.9 Notes, links and follow-ups for contacts and properties *(2026-09-27)*

One handler (`agents/conversation/record_notes.py`) keeps the notes feed for contacts, properties and estimates, and one (`agents/conversation/record_links.py`) links a contact and a property in the user guide's words (design 2026-09-27 §7.3; user decision (b)). Adding a note to an estimate or work item stays with the estimate grammar (§1.0).

| Phrasing | Behavior | Status |
|---|---|---|
| `add a note to him: call after 5` (contact in focus) / `add a note to Bob Lee saying …` / `jot down a note for 12 Oak St: …` | files the note, authored by you | ✅ rule *(it asked "which fields?" on the rules tier)* |
| `add a note to Bob Lee` → *"What should the note say?"* → the text | files the reply, even if it reads like a command | ✅ rule |
| `show me the notes for 12 Oak St` / `what notes are on Bob Lee?` / `any notes on E0042?` / `show me his notes` | lists them newest first, with author and date | ✅ rule |
| `delete my note on Bob Lee` / `delete note 2` (after a list) / `delete my last note on Ana Reyes` → *"Delete your note …? This can't be undone."* → `yes` / `no` | deletes it, or keeps it; your own notes, or any as an Owner | ✅ rule *(it was redirected to the app)* |
| `link John Doe to 123 Main St` / `link 123 Main St to John Doe` / `connect Carla Diaz with the Elm House property` / `add Carla Diaz to 12 Oak St` / `Carla Diaz lives at 12 Oak St` | links them (either order); "already linked" when they are | ✅ rule *(the guide's own phrasing was unknown on the rules tier)* |
| `link Zed Quill to 12 Oak St` (no such contact) | "I couldn't find a contact or a property called Zed Quill." | ✅ rule |
| `remove Ana Reyes from 12 Oak St` / `unlink …` | done in the app — §9.8 | 🛑 redirect |

**Open gaps:** #690 (LLM tier) (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #679, #682, #683, #687.

---

# 4. Materials

## 4.1 Direct imperatives (all ✅ rule)

`create a new material` · `list all materials` · `delete the material {material}`

## 4.2 Casual phrasings (all ✅ rule)

`show me my materials` · `what materials do I have?` · `pull up material {material}`

## 4.3 Possessive

| Phrasing                         | Intended behavior          | Status |
| -------------------------------- | -------------------------- | ------ |
| `show me {material}'s details`   | `get_material`             | ✅ rule |
| `what's {material}'s price?`     | `get_material` field focus | ✅ rule |
| `update {material}'s record`     | `update_material` — asks which field | ✅ rule |

## 4.4 Count

| Phrasing                                  | Intended behavior | Status |
| ----------------------------------------- | ----------------- | ------ |
| `how many different materials do I have?` | count materials   | ✅ rule |
| `how many types of materials do I have?`  | count materials   | ✅ rule |
| `how many materials do I have?`           | count materials   | ✅ rule |
| `count my materials`                      | count materials   | ✅ rule |

The "different" / "types of" modifiers don't change the routing — `how many` already pins the action to ``list`` and the trailing ``materials`` pins the domain. Confirmed via `material_query_variants` coverage category.

## 4.5 Filter / find (all ✅ rule)

`find materials named concrete` · `show materials in in stock` · `search for materials matching concrete`

## 4.6 Field-targeted update (material-level)

| Phrasing | Status |
|---|---|
| `change the price of {material} to $5` | ✅ rule |
| `update the price on {material} to $5` | ✅ rule |
| `set {material}'s price to $5` | ✅ rule |
| `change the cost of Topsoil to 20` / `update Topsoil's price to 45` (no "material") | ✅ rule *(2026-09-27 — a material, role or template named exactly is rewritten kind-first, `catalog_names.py`)* |
| `move Topsoil to the Bulk Materials category` | ✅ rule *(2026-09-27, #694 — the category name is resolved to its id, never created; it failed every time)* |
| `rename it to Screened Topsoil` (material in focus) | ✅ rule |
| `show me the Black Mulch material` / `show me Black Mulch` | ✅ rule *(it listed every material, or looked for a contact)* |

Closed by Phase 2 of xfail-wave-1 — `_match_possessive_or_field_targeted` resolves the missing material domain via `FIELD_TO_DOMAIN["price"] → material` plus the material-shape residual on the captured entity name.

## 4.7 Verbless (all ✅ rule — Phase 2b material-shape residual)

`{material}` · `I want the details for {material}` · `tell me about {material}`

## 4.8 Size-scoped operations *(shipped in Phase B; any size since 2026-09-27)*

A size is a number with an optional unit and package word (`3 cu ft`, `3 cu ft bag`, `1 cubic yard`, `2x4`) or one word (`large`). Parsed by `agents/material/size_commands.py` (2026-09-27 — a size of more than one word was never recognised) and applied through the ordinary update path, so its guards hold.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add size {size} to {material} with cost $8 and unit Bag` / `add a 3 cu ft bag size to {material} at $6` / `… at cost 200 per cu yd` | `update_material` (append) | ✅ rule |
| `delete size {size} for {material}` / `remove the {size} size from {material}` | `update_material` (remove) | ✅ rule |
| `update the price for {material} with size {size} to $5` / `change the cost of the {size} size of {material} to 4.50` | `update_material` (one size) | ✅ rule |
| `rename size {size} of {material} to 1 cubic yard` | `update_material` (rename) | ✅ rule |
| `how much is {material} in the {size} size?` / `find material {material} with size {size}` | `get_material` — that size's price and cost | ✅ rule |
| `show all sizes for {material}` / `what sizes does {material} come in?` | `get_material` — *"Black Mulch comes in 2 sizes: 2 cu ft at 4.40, 1 yd at 38.50."* | ✅ rule |
| `change its price to 5` on a material with several sizes → *"which size?"* → `2 cu ft` | the change, on that size | ✅ rule *(2026-09-27 — the answer didn't resume the edit)* |

**Invariants:**
- **Last-size delete refusal** — cannot remove the only remaining size on a material. Copy: *"I can't remove the last size from this material — it needs at least one size. Add another size first, or delete the material entirely if that's what you mean."*
- **Add-size requires BOTH cost and unit** — `add size {size} to {material} with cost $8` (no unit) refuses and prompts for the unit. Same if cost is missing. A unit is resolved to one of the company's units; a name it doesn't have is answered, never created (#681).
- A message that names an estimate or work item is never a size command — those have their own grammar (§1.5.5).

## 4.9 Material gaps

| Phrasing | Intended behavior | Status |
|---|---|---|
| `How much does {material} cost?` | `get_material` field focus | ✅ rule *(closed in xfail-wave-3 Workstream B — non-possessive cost-query rule in orchestrator)* |
| `list materials under $10` | `list_materials` with price range | ✅ rule *(closed in xfail-wave-3 Workstream B — `_parse_price_range_filter` in `agents/material/text_helpers.py` filters the list response by `under/over/below/above $N`)* |
| `rename size {old} to {new} for {material}` | `update_material` (size_op=rename) | ✅ rule *(closed in xfail-wave-3 Workstream B — orchestrator `_match_size_scoped_material_op` rule routes the rename verb)* |
| `show all sizes for {material}` | `get_material` — lists every size | ✅ rule *(2026-09-27; see §4.8)* |
| `how much does {size} of {material} cost?` | `get_material` (size-scoped) | ✅ rule *(May expansion — "of" form cost query pattern)* |
| `what is the price of {size} of {material}?` | `get_material` (size-scoped) | ✅ rule *(May expansion)* |
| `what category is material {material}?` | `get_material` (category focus) | ✅ rule *(May expansion — `_match_field_specific_query` before help classifier)* |
| `what category is {material}?` | `get_material` (category focus) | ✅ rule *(May expansion)* |

## 4.10 Qualifier list — "what {X} materials do I have?" *(2026-06-02)*

A qualifier `{X}` between the lead-in and the `materials` noun is matched as a
**substring against the material name OR its category name** (case-insensitive).
`_extract_list_qualifier` lifts `{X}` out of the phrasing (rule tier) and
`_find_materials_by_name_or_category` does the OR-match. A bare list with no
qualifier (`what materials do I have?`, §4.2) still lists everything — the
generic-word guard drops a non-qualifier capture.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what {X} materials do I have?` | `list_materials` (name ∪ category substring) | ✅ rule |
| `show me my {X} materials` | `list_materials` | ✅ rule |
| `list my {X} materials` | `list_materials` | ✅ rule |
| `do I have any {X} materials?` | `list_materials` | ✅ rule |
| `which {X} materials do I have?` | `list_materials` | ✅ rule |
| `how about {X} materials?` / `what about {X} materials?` / `and {X} materials?` | `list_materials` | ✅ rule *(follow-up phrasings — the "how about" lead-in would otherwise trip `is_help_query`, so the orchestrator `_match_material_list_filter` fast-path routes these before the help classifier. It reuses the agent's `_LIST_QUALIFIER_PATTERN` so routing and qualifier extraction never drift.)* |
| `how many {X} materials do I have?` | `list_materials` (count of category {X}) | ✅ rule *(count-by-category — resolves a whole-word category for count queries; falls back to all when {X} isn't a category)* |

**Disambiguation:** `material units` / `material categories` / `material types` are NOT treated as "{X} materials" lists — a negative lookahead on `_LIST_QUALIFIER_PATTERN` keeps those routing to their help/enum or category handlers.

## 4.11 Create, one question at a time *(2026-09-27)*

A create that is missing details asks for the next one alone, remembers which, and reads a bare reply as its value (`agents/conversation/create_questions.py`, §10.6). It asked for everything at once ("To create a material, I'll need: category, unit, size, price.") and ignored "Bulk Materials". A material is asked for its **cost**: the server prices the size from the company's material markup (see the pricing model in CLAUDE.md), so a create that gives a cost and no price no longer asks for a price.

| Turn | Maple | Status |
|---|---|---|
| `create a new material called River Rock` | *"Which category does River Rock go in? You have: Bulk Materials, Masonry, Soil."* | ✅ rule |
| `Bulk Materials` | *"What unit is River Rock sold by? You have: Bag, Cubic Yard, Each."* | ✅ rule |
| `Bag` | *"What size does River Rock come in? For example: 2 cu ft, or Standard."* | ✅ rule |
| `2 cu ft` | *"What does River Rock cost you? I'll set the price from your material markup."* | ✅ rule |
| `5` | created — cost 5.00, price 5.50 at a 10% markup | ✅ rule |
| a category or unit the company doesn't have | says so and asks again, never creates one (#681) | ✅ rule |

**Open gaps:** #690 (LLM tier), and older #495 (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #678, #680, #681, #682, #683, #694, #697.

---

# 5. People (roles) — a.k.a. Labor

Labor = catalog of **role definitions** (Landscaper, Foreman, Operator). Individuals go under Contact.

## 5.1 Direct imperatives (✅ rule except as noted)

`create a new labour role` · `list all labour roles` · `delete the labour role {role}` · `create a new role called {role}` · `delete the {role} role` · `list my roles`

## 5.2 Casual phrasings (✅ rule except as noted)

`show me my labour roles` · `what labour roles do I have?` · `pull up labour role {role}` · `show me the {role} role` · `what's the rate for {role}?`

Fixed 2026-09-27 (#693): the name extractor read "S" out of `show me my labour roles` and `list all labour roles` ("S Do I Have" from `what labour roles do I have?`) and filtered the list by it.

## 5.3 Possessive

| Phrasing | Status |
|---|---|
| `show me {role}'s details` / `tell me {role}'s rate` | ✅ rule |
| `what's {role}'s cost?` | ✅ rule |
| `update {role}'s record` — asks which field | ✅ rule |

## 5.4 Count (all ✅ rule)

`how many labour roles do I have?` · `count my labour roles` · `total number of labour roles`

## 5.5 Filter / find (all ✅ rule)

`find labour roles named Foreman` · `show labour roles in outdoor` · `search for labour roles matching Foreman`

## 5.6 Field-targeted update

| Phrasing | Status |
|---|---|
| `change the cost of {role} to $50` | ✅ rule |
| `update the cost on {role} to $50` | ✅ rule |
| `set {role}'s cost to $50` | ✅ rule |
| `change role {role}'s wage to 45` | ✅ rule *(2026-09-27)* |
| `update role {role}` → *"which fields?"* → `wage` → `45` | ✅ rule *(2026-09-27 — it asked "which labor role?")* |

## 5.7 Verbless (all ✅ rule — DOMAIN_HINTS include role names)

`{role}` · `I want the details for {role}` · `tell me about {role}`

## 5.8 Role field queries (all ✅ rule — May expansion)

"What's the X for role Y?" phrasings route to `get_labour` via `_match_field_specific_query` in the orchestrator (runs before `is_help_query`).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what's the average wage for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |
| `what's the rate for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |
| `what's the labor burden for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |
| `what's the unbillable rate for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |

Note: "labor burden" and "unbillable rate" are company-level settings, not per-role fields. The Labour Agent's get response shows the role's Avg. Wage and computed Rate. The explanation of how rate is computed (wage + unbillable% + labor burden%) is provided when users attempt to edit rate directly.

## 5.9 People gaps

| Phrasing | What happens | Status |
|---|---|---|
| `list my roles` / `create a new role called {role}` | lists every role / creates the role | ✅ rule *(2026-09-27 — both were unknown on the rules tier)* |
| anything about the "Heavy Equipment Operator" role | read, created and edited as a role | ✅ rule *(2026-09-27, #693 — the equipment refusal matched the word "equipment"; an equipment operator is a person)* |

## 5.10 Create, one question at a time *(2026-09-27)*

As for materials (§4.11): `create a new role called Arborist` → *"What's the average wage for Arborist? For example: $30 an hour."* → `30` → *"Is Arborist paid hourly, daily or per job?"* → `hourly` → created. `add a labour role` asks *"What's the role called?"* first; `$30 an hour` answers the wage and the unit together. It said "To create a role, I'll need: unit, wage." and a bare "30" asked again. ✅ rule.

Cross-resource phrasings (e.g. `which properties need a {role}?`) are tracked under §8.

**Open gaps:** #690 (LLM tier) (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #678, #682, #683, #693.

---

# 6. Templates

Templates are reusable estimate blueprints — a predefined set of materials, activities, and cost parameters that can be applied when creating estimates. Managed via the Templates page in the portal. The API supports full CRUD plus a duplicate operation (`POST /templates/id/{id}/duplicate`).

Key fields: `name` (required, unique per company), `description`, `division`, `recurring` (bool), `profit_margin`, `overhead_allocation`, `labor_burden`, `tax`, `size` + `unit` (baseline dimensions), and embedded `materials` / `activities` lists.

## 6.1 Direct imperatives

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `list all templates` | `list_templates` → Template Agent | ✅ rule |
| `delete the template {template}` | `delete_template` → Template Agent | ✅ rule |

Template **creation** is refused — see §9.5. Users must create templates through the Templates page in the portal UI.

## 6.2 Casual phrasings

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me my templates` | `list_templates` → Template Agent | ✅ rule |
| `what templates do I have?` | `list_templates` → Template Agent | ✅ rule |
| `pull up template {template}` | `get_template` → Template Agent | ✅ rule |

## 6.3 Possessive

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me {template}'s details` | `get_template` → Template Agent | ✅ rule *(2026-09-27)* |
| `what's {template}'s description?` / `what's the description of the {template} template?` | `get_template` → Template Agent | ✅ rule *(2026-09-27)* |

## 6.4 Count

`how many templates do I have?` · `count my templates` · `total number of templates`

All ✅ rule — routes to `list_templates` → Template Agent with count response.

## 6.5 Filter / find

`find templates named Driveway` · `search for templates matching Driveway` · `which templates have patio in the name?` — ✅ rule. The list is narrowed to templates whose name contains it (*"Here are your templates matching "Paver":"*), or says none match; `show me the first one` picks from it. *(2026-09-27 — every template was listed, and "which templates …" went to the user guide.)*

Template **update** and **duplicate** are refused — see §9.5. Users must edit and copy templates through the portal UI.

## 6.6 Verbless

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `{template}` (bare template name, written like a name) | `get_template` → Template Agent | ✅ rule *(2026-09-27)* |
| `show me the {template} template` / `delete the {template} template` | `get_template` / `delete_template` | ✅ rule *(2026-09-27 — it asked "which template?")* |
| `I want the details for {template}` | `get_template` → Template Agent | 🤖 LLM |
| `tell me about {template}` / `tell me about the {template} template` | `get_template` → Template Agent | ✅ rule *(2026-09-27)* |

## 6.7 Apply template to estimate

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `use template {template} in the estimate {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `apply template {template} to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `apply {template} to the estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `apply template {template} to estimate {title}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-09 — title-aware: targets the named estimate over `active_estimate_code`. A named estimate that **doesn't exist** is REFUSED with a warning — it does NOT silently create a new estimate under that name.)* |
| `use the {template} template for {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `create an estimate from template {template}` | `update_estimate` → Estimate Agent | ✅ rule *(creates a new draft estimate and applies the template as a work item — the no-named-target bootstrap path)* |

### Template-driven create (2026-06-02) — skips AI generation

When a **create-estimate** request names a template, `delegate_create_estimate` detects it (`detect_template_in_create_request`) and routes to template instantiation instead of AI generation — no material/activity questions. Linear scaling by job size when the template has a **baseline** (`size` + `unit`).

| Phrasing | Behavior | Status |
|---|---|---|
| `create an estimate ... use the {template} template` (no baseline) | Create a draft, template applied as one work item, verbatim (1×). Property context linked. | ✅ rule |
| `create an estimate, 600 sq ft, using the {template} template` (baseline + size in request) | Scale the template linearly (`factor = job_size ÷ baseline_size`); size taken from the request, not re-asked. | ✅ rule |
| `create an estimate using the {template} template` (baseline, no size) | Ask "What's the size of this job (in {baseline unit})?" (`pending_template_size`), then scale on reply. | ✅ rule |
| reply with size in a **convertible** unit (sq yd↔sq ft, lin yd↔lin ft) | Converted to the baseline unit, then scaled. | ✅ rule |
| reply with an **incompatible** unit (area vs length) | Re-asks for the size in the baseline's unit. | ✅ rule |
| `No` / `skip` to the size question | Instantiate at the baseline (1×) and proceed (no cancel). | ✅ rule |
| `cancel` / `never mind` to the size question | Cancels the estimate request. | 🛑 cancel |

**Scaling** (`agents/estimate/template_scaling.py`): multiplies material/labour/equipment quantities, activity effort, and the work-item `sub_total` by the factor; prices/rates unchanged. Linear across all line items — no per-item fixed-fee exemption. Pre-handler: `handle_pending_template_size` in `routers/agent_helpers/template_estimate.py`.

## 6.8 Template gaps

Orchestrator routing, refusal guard, and Template Agent are implemented. Possessive (§6.3) and most verbless (§6.6) phrasings are rule-tier since 2026-09-27: the router rewrites a template's exact name kind-first (`catalog_names.py`). Template creation, update, and duplicate are explicitly refused (§9.5).

Additional cross-resource phrasings (e.g. `which templates include {material}?`) are future candidates — not tracked here yet.

**Open gaps:** #695 (portal) (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #675, #677, #681; `find templates named X` (§6.5).

---

# 7. Tasks

Field-capture to-dos (`models/task.py`) with a title, capture date, optional description / due date / property link / assignee, and a **per-company status** (`TaskStatus` documents — defaults `To Do` | `In Progress` | `Done`; users can rename/add). The Tasks feature is flag-gated (`settings.tasks_enabled`); Maple refuses gracefully when it's off. Free-plan companies have a standing 50-task cap (archived tasks count; only hard delete frees a slot).

Token conventions: `{task}` = a task title (e.g. `fix the fence gate`); `{status}` = a company task-status name; `{email}` = an assignee email.

## 7.1 Direct imperatives (all ✅ rule)

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `create a task called {task}` | `create_task` → Task Agent | ✅ rule |
| `create a task with title {task}` / `title: {task}` | `create_task` → Task Agent | ✅ rule *(2026-07-22 smoke-test fix)* |
| `create a task with title {task}. Add the following notes: {text}` | `create_task` → Task Agent (title + description in one turn) | ✅ rule *(the notes/description clause is split off before title extraction and stored as the task description)* |
| `add a task to check the retaining wall` / `create a new task to: {text}` / `new task: {text}` | `create_task` → Task Agent | ✅ rule *(2026-07-25 — **content-is-description rule**: with no title cue, the body becomes the DESCRIPTION and the title is derived from it. Previously the "to …" phrase became the title, and a phrasing like `create a new task to: {text}` put the whole command line in the title.)* |
| `create a task with the notes: {text}` / `Create a task. Add the following notes: {text}` (notes, **no** title) | `create_task` → Task Agent — creates immediately with a **title derived from the notes** | ✅ rule *(2026-07-25 — first sentence of the notes, politeness/reminder preamble stripped ("remind me to call Bob tomorrow" → "Call Bob tomorrow"), truncated to 60 chars on a word boundary; full notes kept as the description. The reply says the title came from the notes so the user can rename it.)* |
| `create a new task` (no title, **no** notes) → *"What should the task be called?"* → bare reply | `create_task` field-then-value flow (§10.1) — the reply becomes the title; inline notes from the first turn are kept | ✅ rule *(only reached when there are no notes to derive a title from, or the notes yield nothing usable — e.g. `notes: ...`)* |
| `list my tasks` | `list_tasks` → Task Agent | ✅ rule |
| `show me the {task} task` | `get_task` → Task Agent | ✅ rule |
| `delete the {task} task` → *"…are you sure?"* → `yes` | `delete_task` → Task Agent (manager-only, confirm first) | ✅ rule *(2026-09-27 — the "yes" now deletes; #692)* |
| `create a task to call Bob tomorrow and assign it to me` / `add a task to trim the hedge due Friday and assign it to Jordan` | `create_task` → Task Agent with due date / assignee | ✅ rule *(2026-09-27 — a create's tail sets fields: `assign it to` me / an email / a teammate's name, `mark it` / `status:` a status, a date phrase (`tomorrow`, `due Friday`, `by next week`, `on Oct 3`) as the due date. Instructions come out of the note; the date stays in it. Before, the trailing "assign it to …" routed the whole message to an edit of another task.)* |
| `create a task to fix the side gate at the Elm House property` / `add a task to rake the leaves at 12 Oak St` | `create_task` → Task Agent, linked to the property | ✅ rule *(2026-09-27 — "at the X property" or an "at …" tail that names one property; the words stay in the note)* |
| `create a task to call the supplier and assign it to Zed` (no such teammate) | `create_task` — the task is made, assigned to you, and the reply says Zed wasn't found | ✅ rule *(2026-09-27 — a clause Maple can't apply is reported, never dropped)* |

## 7.2 Casual phrasings

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `jot down a task to order more mulch` | `create_task` → Task Agent | ✅ rule *(2026-09-27)* |
| `remind me to call Bob tomorrow` / `set a reminder to …` / `don't let me forget to …` | `create_task` → Task Agent (due tomorrow) | ✅ rule *(2026-09-27 — a reminder is a task, whatever it is about)* |
| `add order more mulch to my to-do list` / `put … on the to do list` / `new to-do: …` / `create a reminder to …` | `create_task` → Task Agent | ✅ rule *(2026-09-27)* |
| `I need to remember to winterize the irrigation` | `create_task` → Task Agent | ⚠️ gap |
| `pull up my tasks` | `list_tasks` → Task Agent | ✅ rule |
| `what tasks do I have?` | `list_tasks` → Task Agent | ✅ rule |

## 7.3 Possessive

Bare-title possessives carry no "task" keyword for the rule tier to anchor on, and the 2026-07-22 Tier-2 run showed the LLM doesn't rescue them either (same bare-title gap class as materials/contacts pre-Phase-2b). Adding `the {task} task's …` (with the keyword) routes fine via §7.1/§7.6 shapes.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what's the {task} task's due date?` | `get_task` → Task Agent | ⚠️ gap (bare-title form; keyword form routes ✅) |
| `update {task}'s description` | `update_task` → Task Agent | ⚠️ gap |
| `show me {task}'s details` | `get_task` → Task Agent | ⚠️ gap |

## 7.4 Count (all ✅ rule)

`how many tasks do I have?` · `count my tasks` · `total number of tasks` — `list_tasks` count path → `format_count_response`. Every §7.5 filter applies to a count too: `how many tasks are overdue?` → "You have 1 overdue task." *(2026-09-27, #687)*

## 7.5 Filter / find

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what tasks do we have at {property}?` / `tasks for the {property} property` | `list_tasks` filtered by property | ✅ rule *(2026-09-27; a property that doesn't match is answered — "I couldn't find a property called …")* |
| `tasks assigned to {email}` / `tasks assigned to me` / `tasks assigned to Jordan` / `Jordan's tasks` | `list_tasks` filtered by assignee | ✅ rule *(2026-09-27 — the email is read whole (it stopped at the first ".", #687); a teammate by first, last or full name; an unknown name is answered, never dropped)* |
| `tasks for Jordan` | property first, then teammate | ✅ rule *(2026-09-27)* |
| `unassigned tasks` | `list_tasks` with no assignee | ✅ rule *(2026-09-27)* |
| `list my tasks` | `list_tasks` (ALL tasks — "my" is not an assignee filter, matching every other resource; use "assigned to me" to filter) | ✅ rule |
| `tasks in progress` / `show done tasks` / `list to do tasks` / `tasks with status {status}` | `list_tasks` filtered by status | ✅ rule *(2026-09-27; "to do" is a status only before "tasks" — "my to-dos" are all tasks)* |
| `show open tasks` / `what's still to do?` | `list_tasks` leaving out finished tasks (a status named Done / Completed / Finished / Closed / Cancelled) | ✅ rule *(2026-09-27)* |
| `show my overdue tasks` / `what's overdue?` | `list_tasks`, due before today and not finished, soonest first with each due date | ✅ rule *(2026-09-27)* |
| `what's due today?` / `tasks due tomorrow` / `tasks due this week` / `tasks due next week` / `tasks due by Friday` / `tasks due on Oct 3` / `today's tasks` / `tasks for next week` | `list_tasks` with a `due_date` window, soonest first | ✅ rule *(2026-09-27 — no "task" word needed: only tasks have due dates. A week runs Monday to Sunday.)* |
| `upcoming tasks` / `what's upcoming?` / `what's coming up this week?` / `anything due soon?` | `list_tasks`, overdue or due in the next 7 days and not finished — overdue first, each row saying whether it's overdue | ✅ rule *(2026-09-27 — the dashboard's Upcoming Tasks card in words; overdue tasks were left out)* |
| `what's on my plate?` / `what's on my to-do list?` | the same, assigned to you — the card's default view | ✅ rule *(2026-09-27 — went to the user guide)* |
| `show archived tasks` | `list_tasks` with archived-only filter | ✅ rule |
| `find tasks about fencing` | `list_tasks` with title/description search | ✅ rule *(named/matching/about/containing/called all apply the search term)* |
| `list my tasks` (more than 20) → *"That's 1–20 of 24 … say "show more" for the next 4."* → `show more` / `next page` / `the rest` | the same list, from where it stopped — filters included | ✅ rule *(2026-09-27 — good for the next turn only; "show more" with no longer list open says so)* |

## 7.6 Field-targeted update

The `the {task} task` keyword forms are ✅ rule; bare-title forms (`change the due date of {task} to Friday` with no "task" word) are 🤖 LLM for the change/update shapes and ⚠️ for the set-possessive shape (2026-07-22 Tier-2 run). Due-date values accept ISO (`2026-08-01`), `today`/`tomorrow`, and weekday names (next occurrence).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `change the due date of the {task} task to Friday` | `update_task` → Task Agent | ✅ rule |
| `add a description to the last task: {text}` | `update_task` → Task Agent (recency reference) | ✅ rule |
| `rename the {task} task to {new title}` | `update_task` → Task Agent | ✅ rule *(2026-07-30 — genuinely rule-tier now; `rename` was missing from `ACTION_HINTS` so this row previously described the agent-side handler only, and routing fell through to the LLM)* |
| `retitle the {task} task to {new title}` | `update_task` → Task Agent | ✅ rule |
| `rename it to {new title}` (pronoun target) | `update_task` → Task Agent | ✅ agent-side *(2026-07-30 — resolves through the active-task anchor; see §7.11)* |
| `set the description of the {task} task to {text}` | `update_task` → Task Agent | ✅ rule |
| `change the due date of {task} to Friday` (bare title) | `update_task` → Task Agent | 🤖 LLM |
| `set {task}'s due date to next Monday` (bare title) | `update_task` → Task Agent | ⚠️ gap |
| `make it due Friday` / `push it to next week` / `reschedule the {task} task to Oct 3` / `it's due in 3 days` / `due Friday` (task in focus) | `update_task` (due date) → Task Agent | ✅ rule *(2026-09-27 — dates also accept `next week`, `in N days/weeks`, `end of the week/month`, `Oct 3` / `3rd of October`)* |
| `clear the due date` / `remove the due date from the {task} task` | `update_task` (due date cleared) → Task Agent | ✅ rule *(2026-09-27)* |
| `link it to 12 Oak St` / `link the {task} task to the Elm House property` / `set the property of the {task} task to Elm House` | `update_task` (property) → Task Agent | ✅ rule *(2026-09-27)* |
| `remove the property from the task` / `unlink it from the property` | `update_task` (property cleared) → Task Agent | ✅ rule *(2026-09-27 — unlinking a task is Maple's; unlinking a contact from a property is still done in the app, §9)* |

## 7.6.1 Notes on an existing task (append by default)

Adding notes to a task Maple already worked on is an **update**, not a create — the orchestrator's `is_task_notes_update_request` claims these before the generic resolver, because `add` is a CREATE action hint and would otherwise make a *second* task. The rule requires an explicit `task`; a bare `add a note to it` stays on the generic anaphora path, which since 2026-07-30 resolves to whichever domain the user touched **most recently** rather than to a fixed ranking that always preferred an active estimate.

Additive is the default, matching estimate notes (§5.x) — a drive-by note never silently wipes what's there. Existing notes and the new text are blank-line separated; appending onto empty notes collapses to a clean set. Only an explicitly destructive verb (`replace` / `overwrite` / `set … with`) overwrites.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `Add the following notes to the Task: {text}` (active task) | `update_task` (notes append) → Task Agent | ✅ rule *(2026-07-25)* |
| `Add to the Task: {text}` / `add this to the task: {text}` / `add to the {task} task: {text}` — **no field word at all** | `update_task` (notes append) → Task Agent | ✅ rule *(2026-07-25 smoke-test fix — the colon carries the meaning: everything after it is content, and notes are the only free-text field a task has. A separator is REQUIRED, so `add a photo to the task` isn't claimed.)* |
| `Add to the tasks to {text}` / `add to the task to {text}` / `add to the tasks about {text}` / `add to the task that {text}` — **plural noun and/or a connector word instead of a colon** | `update_task` (notes append) → Task Agent | ✅ rule *(2026-07-30 — reported: "Add to the tasks to buy more milk." landed on `create_task` and asked "What should the task be called?". Two gaps: `task\b` never matched the plural, and the colon was the only separator. `to` / `about` / `that` now count as separators, and the noun may be plural. `add a photo to the task(s)` still isn't claimed — the verb must be followed immediately by to/on/onto, which was always the real guard.)* |
| `add a note to the task: {text}` / `append to the task notes: {text}` | `update_task` (notes append) → Task Agent | ✅ rule |
| `add notes to the {task} task: {text}` | `update_task` (notes append) → Task Agent | ✅ rule |
| `add a note to it: {text}` (pronoun only) | `update_task` (notes append) → Task Agent | ✅ rule with a task anchor *(2026-09-27 review)* |
| `Add another note: {text}` / `add a note: {text}` — **no target at all** | `update_task` (notes append) → Task Agent | ✅ rule *(2026-07-25 smoke-test fix — the active task is implied, same as the pronoun forms. 2026-09-24 — routing is now rule-tier: `is_note_add_request` sends a targetless note to whichever domain was touched most recently; before, the borrowed domain plus `add` resolved to `create_task`.)* |
| `replace the notes on the task with: {text}` / `set the notes on the task to: {text}` | `update_task` (notes **set**) → Task Agent | ✅ rule |
| `add a task with the notes: {text}` | `create_task` → Task Agent | ✅ rule *(create shape — the notes-update rule explicitly excludes it)* |

### 7.6.1.1 Dictated payloads — the first intent wins

**In `<command>: <payload>`, the payload is content, not intent.** Classifying the whole string let a domain word inside the user's own prose take over: *"Add to it the following: bring a lawn mower to his place. Need to estimate the lawn size."* routed to `create_estimate` — the trailing "estimate" beat the leading "add to it".

`strip_dictated_payload` (in `intents.py`) returns just the command head when the head carries an add/notes/following cue, and the generic resolvers classify on that head — `_match_unambiguous_command`, `_classify_via_action_domain`, and `_resolve_intent_with_history` (where a payload domain word previously blocked anaphora outright). Task-specific rules still see the full text, because some key off the colon itself. A message that names its domain in the head (`create an estimate for: 123 Main St`) is unaffected.

Paired rule: **an anaphoric target means the entity already exists**, so `is_anaphoric_add_request` rewrites the CREATE reading of "add … to it/this/that" to an update. Which domain it updates still comes from the active-entity anchor (estimate before task, §7.11) — so the same sentence appends to an active estimate when that's what's in play.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `Add to it the following: {text}` (active task; payload mentions other domains) | `update_task` (notes append) → Task Agent | ✅ rule *(2026-07-25 smoke-test fix)* |
| `add to the task the following: {text}` | `update_task` (notes append) → Task Agent | ⚠️ gap *(2026-09-27 review: creates a second task instead of appending)* |
| `Add to it the following: {text}` (active **estimate**) | `update_estimate` → Estimate Agent | ✅ rule *(anchor decides, not the payload)* |

## 7.6.2 Field-then-value flow (§10.1) — "update the task" → "description" → the value

`update the task` alone can't be actioned, so Maple asks which field. That question is only useful if the answer can be resumed: each ask now stashes a `pending_intents` entry naming the Task Agent, which is what the router's pending fallback routes the bare reply back to. **Without it the reply landed wherever the classifier guessed** — in the 2026-07-25 smoke test, three "What would you like to update?" loops followed by create's *"What should the task be called?"*.

Either step can be entered directly: `description` on its own selects the field and asks for the value; `add to the description` works only as a reply to the field question (2026-09-27 review). `match_bare_task_field` maps title/name, description/notes/note/details, due date/due/deadline, status/state, assignee/assigned to/owner — and returns nothing as soon as the message carries a payload, so an answer like "mow the lawn as well" is never mistaken for a field selection. Description values **append**; a fresh command mid-flow (`list my tasks`) is obeyed and the stale ask is dropped.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `update the task` → *"What would you like to update…?"* → `description` → *"What would you like me to add…?"* → `{text}` | `update_task` field-then-value → Task Agent | ✅ rule *(2026-07-25)* |
| `add to the description` → *"What would you like me to add…?"* → `{text}` | `update_task` (notes append) → Task Agent | ⚠️ only as a reply to the field question *(2026-09-27 review)* |
| bare `title` / `due date` / `status` / `assignee` → value | `update_task` field-then-value → Task Agent | ✅ rule *(status resolves per-company names; assignee takes an email, "me" or a teammate's name; due date takes any §7.6 date phrase, and an unreadable one asks again)* |
| `assign it` / `change the assignee` / `change the status` / `move it` / `set a due date` / `reschedule it` → the value | `update_task` → Task Agent asks for that one value | ✅ rule *(2026-09-27 — no "what would you like to update?" first; #692)* |

## 7.7 Status changes

`TaskStatus` values are **per-company** (defaults: `To Do`, `In Progress`, `Done`). Status names resolve exact → case-insensitive → fuzzy; an unrecognized name triggers a clarification listing the company's statuses. Status changes fold under `update_task` (same pattern as estimate status transitions under `update_estimate`, §1.4).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `mark it as done` (active task) | `update_task` (status) → Task Agent | ✅ rule with a task anchor *(2026-09-27 review)* |
| `mark the {task} task as done` | `update_task` (status) → Task Agent | ✅ rule |
| `move the {task} task to In Progress` | `update_task` (status) → Task Agent | ✅ rule |
| `set the status of the {task} task to {status}` | `update_task` (status) → Task Agent | ✅ rule *(unknown names get a clarification listing the company's statuses; done/complete/finished + in-progress/started + to-do/open synonyms map to the default names when present)* |
| `I finished it` / `it's done` / `complete the {task} task` / `start it` / `reopen it` | `update_task` (status) → Task Agent | ✅ rule *(2026-09-27 — "reopen" moves it back to the company's first status)* |

## 7.8 Assignee operations

Assignees are stored as emails (`assigned_to_email`); an email is taken as given (parity with the REST API — no team-membership validation), and since 2026-09-27 a teammate can be named by first, last or full name.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `assign this to {email}` (active task) | `update_task` (assign) → Task Agent | ✅ rule with a task anchor *(2026-09-27 review)* |
| `assign the {task} task to me` | `update_task` (assign, current user) → Task Agent | ✅ rule |
| `assign the {task} task to {email}` / `reassign …` | `update_task` (assign) → Task Agent | ✅ rule |
| `give it to Jordan` / `hand the {task} task over to Ana` / `assign it to Jordan` | `update_task` (assign by teammate name) → Task Agent | ✅ rule *(2026-09-27 — two teammates with that name get a question listing both)* |
| `unassign it` / `assign the {task} task to nobody` / `remove the assignee` | `update_task` (assignee cleared) → Task Agent | ✅ rule *(2026-09-27)* |
| `who is the {task} task assigned to?` | `get_task` → Task Agent | ⚠️ gap *(details view already shows Assigned to; the who-question routing is unwired)* |

## 7.9 Archive / unarchive

Soft-hide only — archived tasks still count toward the free-plan cap.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `archive that task` (active task) | `update_task` (archive) → Task Agent | ✅ rule |
| `archive the {task} task` | `update_task` (archive) → Task Agent | ✅ rule |
| `unarchive it` (active task) | `update_task` (unarchive) → Task Agent | ✅ rule with a task anchor *(2026-09-27 review)* |
| `unarchive the {task} task` / `restore the {task} task` | `update_task` (unarchive) → Task Agent | ✅ rule |

## 7.10 Convert to estimate

Converting generates a new estimate from the task's description via the AI pipeline and **consumes one included estimate** — Maple always confirms before running it. Requires a non-empty task description. Billing outcomes surface as friendly refusals (needs payment method / plan blocked / already converting).

Handler: `agents/task/operations.py::_handle_convert_task` → `services/task_convert.py::run_task_conversion` — the SAME claim/billing/generation/re-link core the REST endpoint uses (extracted 2026-07-22 so the two paths can't drift). On success the new estimate becomes the **active estimate** ("add a work item to it" then targets the estimate).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `convert this task to an estimate` (active task) | `convert_task` → Task Agent (confirm first) | ✅ rule |
| `convert the {task} task to an estimate` | `convert_task` → Task Agent (confirm first) | ✅ rule |
| `turn the {task} task into a quote` | `convert_task` → Task Agent (confirm first) | ✅ rule |

## 7.11 Task referencing & anaphora

A task can be referenced three ways; an explicit reference in the message always beats the active-task context. Multiple matches trigger a numbered clarification ("I found 3 tasks matching that — which one did you mean?"); the reply (number, title, or "the first one") dispatches the original request. Once a task is identified (create/get/update/status/assign/archive), it becomes the **active task** — follow-ups ("mark it done", "add a description", "convert it") act on it. Deleting a task clears the active-task context.

Resolver: `agents/task/resolver.py::find_task_from_context_or_message` — order: ObjectId → positional pick against the last rendered list (§10.5) → recency words → day window (`agents/text_utils.py::parse_relative_day_window`) → property (via `find_properties_by_name_or_address`) → title (exact substring, then fuzzy 0.65/0.80) → active-task context → recency fallback (gated OFF for delete/convert; never used after an unmatched explicit title). Confirmation state: `pending_task_confirmation` (numbered/title/ordinal replies; "no" cancels; a fresh command breaks the pending question). Ordinal replies go through the shared `agents/text_utils.py::match_ordinal_reference` — `first`–`tenth`, `1st`–`10th`, `last`, and digits with an optional leading determiner (`2`, `the 2`, `#2`, `option 2`) (2026-07-30; previously a local `first`–`fifth` table with no `last`).

| Reference form | Example | Status |
|---|---|---|
| Relative (recency) | `the last task` / `my latest task` (my = assigned to me) | ✅ |
| Relative (date) | `the task from yesterday` / `from Tuesday` / `3 days ago` | ✅ |
| By title (fuzzy) | `the fence gate task` (typos tolerated) | ✅ |
| By property | `the task at {property}` | ✅ |
| Anaphora (active task) | `mark it as done` / `convert it` / `rename it to {new}` | ✅ agent-side *(pronoun-only messages route via the LLM tier + active-task context. 2026-07-30 — two routing bugs used to steal these: a stale `active_estimate_code` from earlier in the session out-ranked the just-created task, and a Capitalized new value was mined as a person name and sent to Contact. The anchor is now chosen by recency (`active_entity_domain`), and a pronoun-targeted edit's payload is never read as a domain signal.)* |
| Anaphora (bare determiner) | `mark the task as done` / `assign my task to {email}` / `archive the task` / `rename the task to {new}` | ✅ agent-side *(2026-07-25 — "the/my task" with no name in between is anaphora: the target hint collapses to empty and resolution goes through the active-task context. Previously the stray determiner leaked into the title matcher and could hit ANY title containing "the".)* |
| Ambiguity → confirmation | two similar titles → numbered clarification, reply `1` / `the second one` / `T0004` / words from one title (`the paint one`) / `no` | ✅ *(2026-09-27 — the readable id and title words; the question gate reads a reply naming a choice as the answer, #692)* |

## 7.12 Task refusals — 🛑

| Phrasing / condition | Behavior | Status |
|---|---|---|
| `delete all my tasks` / `wipe my tasks` | Bulk-delete refusal (existing domain-agnostic guard) | 🛑 refusal |
| `delete the {task} task` as a non-manager | Refused — owners/admins only (`agents/role_utils.py::assert_manager_role`, shared with the Template agent); Maple offers to archive instead | 🛑 refusal |
| `convert …` with an empty task description | Refused — Maple asks to add a description first | 🛑 refusal |
| Any task request while `tasks_enabled` is off | Friendly "Tasks aren't enabled for your workspace" refusal | 🛑 refusal |
| `create a task …` at the free-plan 50-task cap | Refused with upgrade pointer (mirrors REST 409) | 🛑 refusal |
| Convert billing outcomes (402 needs-payment / 429 blocked / 409 already-converting) | Friendly first-person refusals mapped from `run_task_conversion`'s HTTP errors | 🛑 refusal |

## 7.13 Task gaps

Shipped 2026-07-22 (plan: [`plans/maple-tasks-support.md`](plans/maple-tasks-support.md)). Remaining ⚠️ rows, confirmed against both tiers where noted:

- **Bare-title references** (possessive §7.3, verbless, set-possessive §7.6) — no "task" keyword to anchor on; both tiers fail (2026-07-22 Tier-2 run). Same gap class as materials/contacts pre-Phase-2b; a catalog-backed title lookup would close it.
- **Informal create cue** — `I need to remember to…` (LLM tier, unverified). `jot down…`, `remind me to…` and the to-do list forms are rule-tier since 2026-09-27.
- **`who is the {task} task assigned to?`** — unwired; details view covers the need.
- **`add a task to the estimate`** — routes to the Task Agent (estimate work items are never called "tasks" in code or docs); when the message names an estimate, Maple should offer redirection to the work-item flow ("Did you mean a work item on the estimate?"). Not yet implemented.

Task details (2026-09-27) also show the linked property, the estimate it was converted into, and how many photos and videos it has.

**Open gaps:** #683, and older #442, #447, #470 (see [code-review-followups.md](code-review-followups.md)). #672, #675, #676 and #692 were resolved 2026-09-27; #687's task half is done.

---

# 8. Cross-resource / implicit relationships

Questions users ask when they think about the domain rather than the database. Routing is via `_match_cross_resource_query` in the orchestrator (Wave 2 Phase 1); the join is performed by the target agent reading a `filter_by` payload off `context` (Wave 2 Phase 2). Direct lookups (Property↔Contact) hit the linked-id list on the Property document. Transitive joins (material/role → property, material/role → estimate, estimate → materials/roles) go through the estimates' lines, which live in their work items: `job_items[].materials[].material` and `job_items[].activities[].role` (plus legacy `job_items[].labours[].labour`). One filter and two readers in `agents/cross_resource.py` (`estimate_line_filter`, `estimate_material_names`, `estimate_role_names`) serve every join. Until 2026-09-27 (#682) the joins queried top-level `materials.material` / `labours.labour`, paths `Estimate` doesn't have, and always came back empty; the estimate list had no material filter.

## 8.1 Property ↔ Contact

| Phrasing | Intended behavior | Status |
|---|---|---|
| `who lives at {property}?` | `list_contacts` filtered by property | ✅ rule |
| `what contacts are at {property}?` | `list_contacts` filtered by property | ✅ rule |
| `who owns {property}?` | `list_contacts` filtered by property + role=owner | ✅ rule |
| `what properties does {contact} own?` | `list_properties` filtered by contact | ✅ rule |
| `where does {contact} live?` | `list_properties` filtered by contact | ✅ rule |
| `show me {contact}'s properties` | `list_properties` filtered by contact | ✅ rule (possessive flow) |
| `which properties does contact {contact} linked to?` | `list_properties` filtered by contact | ✅ rule *(May expansion — new "linked to" cross-resource pattern)* |
| `show me (all) properties contact {contact} linked to` | `list_properties` filtered by contact | ✅ rule *(May expansion)* |

## 8.2 Material → Property / Estimate

| Phrasing | Intended behavior | Status |
|---|---|---|
| `which properties use {material}?` | `list_properties` joined via estimates — *"Properties with an estimate that uses Black Mulch:"* / *"No property has an estimate that uses Topsoil."* | ✅ rule *(2026-09-27, #682)* |
| `where is {material} used?` | `list_properties` joined via estimates | ✅ rule *(2026-09-27, #682)* |
| `which estimates use {material}?` / `what estimates include {material}?` / `find estimates with {material}` | `list_estimates` filtered by material — *"Estimates that use Black Mulch:"* / *"None of your estimates use Topsoil."* | ✅ rule *(2026-09-27, #682 — `find estimates with …` listed every estimate; `with status sent` and other list filters are left to the list)* |

## 8.3 Labour → Property / Estimate

| Phrasing | Intended behavior | Status |
|---|---|---|
| `which properties need a {role}?` | `list_properties` joined via estimates | ✅ rule *(2026-09-27, #682)* |
| `what estimates use the {role} role?` / `which estimates use {role}?` (no "role") | `list_estimates` filtered by role | ✅ rule *(2026-09-27, #682 — it was always empty, and the help pre-check showed "Intent identified: …" instead of delegating)* |
| `show me jobs needing a {role}` / `list properties that need a {role}` | `list_properties` joined via estimates | ✅ rule *(2026-09-27, #682 — it listed every property)* |

---

# 9. Safety refusals

## 9.1 Bulk delete — 🛑 refused

Phrasings with quantifier + delete verb. Enforced at the orchestrator layer AND defensively at each domain agent's `process()`. Verbs: `delete`, `remove`, `drop`, `wipe`, `clear`. **Note:** `clear all {resource}` (e.g. "clear all estimates") **is** treated as a bulk delete and refused — the May 2026 "remove clear" change was reverted (2026-06-02). The one exemption is estimate/quote **creation** requests whose job description mentions clearing/removing work ("create an estimate to clear out all the weeds in my backyard") — these are detected by `is_estimate_creation_request()` and pass through to `create_estimate`, never the refusal guard.

| Phrasing | Behavior |
|---|---|
| `delete all {plural}` | 🛑 refusal message, `needs_clarification=True` |
| `remove every {singular}` | 🛑 refusal |
| `wipe my {plural}` | 🛑 refusal |
| `clear all {plural}` | 🛑 refusal |
| `create an estimate to clear out all the {stuff}` | ✅ `create_estimate` (not refused) |

Applies to all 4 CRUD resources. Maple-only policy — HTTP routers may still expose bulk delete for UI workflows.

## 9.2 Equipment — 🛑 refused

Equipment isn't a Maple resource. A phrasing that says "equipment", "equipments" or "machinery" (Spanish "equipo(s)", "maquinaria") refuses with `EQUIPMENT_REFUSAL_MESSAGE` (`is_equipment_request`, `agents/text_utils.py:403`). Naming a machine — excavator, skid steer, bobcat — without one of those words does not trigger it. "Equipment operator" is a role, not equipment: since 2026-09-27 (#693) the "Heavy Equipment Operator" role is read, created and edited, and only the rest of the message is checked.

| Phrasing | Behavior |
|---|---|
| `show all my equipment` | 🛑 refusal |
| `create a new equipment` | 🛑 refusal |
| `delete the excavator equipment` | 🛑 refusal |

## 9.3 Material category management — 🛑 refused

Material categories (Hardscape, Masonry, etc.) live in the catalog UI. Maple can list/filter/reassign but not create/rename/delete them.

| Phrasing | Behavior |
|---|---|
| `create a new category` | 🛑 refusal via `is_material_category_management_request` |
| `rename the Masonry category` | 🛑 refusal |
| `delete the Hardscape category` | 🛑 refusal |

## 9.4 Partial bulk / small-N destructive — 🛑 refusal

| Phrasing | Intended behavior | Status |
|---|---|---|
| `delete the last 5 contacts` | Refuse (N > 1 but not "all") | 🛑 refusal — extended `_BULK_DELETE_PATTERNS` to catch `last/first/next/previous N` quantifiers (xfail-wave-3 Workstream A) |
| `remove the first 10 properties` | Refuse | 🛑 refusal |
| `drop the next 3 materials` | Refuse | 🛑 refusal |

## 9.5 Template creation / update / duplicate — 🛑 refused

Templates must be created, edited, and duplicated through the Templates page in the portal UI. Maple can list, view, delete, and apply templates to estimates — but not create, update, or copy them.

| Phrasing | Behavior |
|---|---|
| `create a new template` | 🛑 refusal — directs user to the Templates page |
| `add a template` | 🛑 refusal |
| `make a new template called Driveway` | 🛑 refusal |
| `update {template}'s description` | 🛑 refusal |
| `change the profit margin of {template} to 20` | 🛑 refusal |
| `duplicate template {template}` | 🛑 refusal |
| `copy template {template}` | 🛑 refusal |

## 9.6 Illegal status transitions — 🛑 refused *(2026-06-11)*

The estimate status state machine (`ESTIMATE_STATUS_TRANSITIONS` in `models/estimate.py`) is enforced in chat, matching the PUT route and the FE. The refusal names the current status and lists the legal next statuses. Whether a phrasing is refused depends on the estimate's **current** status, not the wording.

| Phrasing (example) | Current status | Behavior |
|---|---|---|
| `mark {EST} as won` | Draft | 🛑 refusal — Draft can only go to Sent, On Hold, Archived |
| `update {EST} to Review status` | Draft | 🛑 refusal — same rule |
| `archive {EST}` | Won | 🛑 refusal — Won can only go to Scheduled, On Hold, Lost |
| `mark {EST} as draft` | Scheduled | 🛑 refusal — Scheduled can only go to Completed |
| `mark {EST} as won` | Sent | ✅ allowed — Sent/Approved → anything (the "unsend" rule), **Owner/Admin only** |

Internal lifecycle states (`Generating`, `Failed`, `Deleted`) were already refused as targets regardless of current status; legacy/unknown stored statuses are not blocked (fail-open so old data isn't stranded).

**Authorization (2026-06-11 follow-up)** — legal edges are additionally role-gated, mirroring the HTTP layer:

| Operation | Who can do it | Refusal behavior |
|---|---|---|
| Send (→ Sent) / unsend (Sent/Approved → anything) | Owner or Admin | 🛑 warm refusal pointing the user to an Owner/Admin |
| Archive / unarchive | Owner, Admin, or the estimate's creator (`created_by_email`, case-insensitive) | 🛑 warm refusal naming who can do it |
| All other legal edges (e.g. Won → Scheduled) | Any authenticated user | ✅ |
| Any gated op with no identity in context | — | 🛑 fail closed ("I wasn't able to confirm your permissions…") |

All refusal copy follows Maple's persona (`agents/maple_persona.py`): first-person, apologetic, plain words, and always a next step — never a bare "permission denied".

## 9.7 Edits to locked-status estimates — 🛑 refused *(2026-06-11, tightened 2026-06-12)*

Mirrors the portal's `isEditableStatus`: estimate contents are editable **only in Draft or Review**. Enforced once in `_load_estimate_for_update` (allowlist `_EDITABLE_ESTIMATE_STATUSES`), the shared loader for every estimate content edit (description, link property, apply template, all work-item operations). Notes are exempt: since 2026-09-23 every note is a `Note` on the Notes feed and ignores the lock. Reads (`get_estimate`, work-item queries) are unaffected; status changes go through the §9.6 transition path instead.

| Current status | Edit attempt (any sub-op) | Behavior |
|---|---|---|
| Draft / Review | `set the description of {EST} to "…"`, `remove work item 1 from {EST}`, … | ✅ normal flow |
| Archived | same | 🛑 refusal — "…is archived… ask me to unarchive it first" |
| Sent / legacy Approved | same | 🛑 refusal — "…locked for edits… move it back to Draft or Review first" |
| On Hold / Lost | same | 🛑 refusal — Draft-or-Review rule + "ask me to move it to Review first" (one-hop path exists) |
| Won / Scheduled / Completed (and internal statuses) | same | 🛑 refusal — Draft-or-Review rule, no one-hop path offered |
| Sent / Approved | unsend status change (e.g. `move {EST} back to Review`) | ✅ allowed via the status-transition path (Owner/Admin only, §9.6) |
| Archived | `unarchive {EST}` | ✅ allowed via the status-transition path (Owner/Admin or creator, §9.6) |

Legacy/unknown stored statuses fail open so old data isn't stranded. The HTTP PUT route enforces the same Draft/Review content lock (`estimate_status_allows_content_edit`, `models/estimate.py`).

## 9.8 Done in the app, not in chat — 🛑 redirected *(2026-09-27)*

Requests Maple doesn't do from chat are refused with where to do them, in the user guide's words (`agents/conversation/out_of_chat.py`, #697). The orchestrator checks the table with its other policy refusals on the command head, so a refusal ends the turn — and a refusal is final: the router never sends it on to an agent afterwards. These used to misroute ("add a division called Snow Removal" became a contact action, "upgrade my plan" a material lookup, "create a document for E0042" a new estimate).

| Phrasing | Redirected to | Status |
|---|---|---|
| `set the default markup to 20%` / `change our company tax rate` / `what's the material markup?` | Settings → Financial tab (Owners and Admins); work-item markup/overhead/tax stay Maple's (§1.5.7) | 🛑 redirect |
| `invite Sam to the team` / `add a new team member` / `remove a user` | Settings → Team Members tab | 🛑 redirect |
| `upgrade my plan` / `how many Maple credits do I have left?` / `change my credit card` / `show my invoices` | Settings → Billing tab | 🛑 redirect |
| `load the standard materials` / `reload standard people` | Load Standard in the Materials or People page's actions menu, or the matching Settings tab | 🛑 redirect |
| `import contacts from a CSV` / `upload a spreadsheet of materials` | the CSV upload on the Properties, Contacts or Materials page | 🛑 redirect |
| `add a unit called pallet` / `rename the unit bag` | Settings → Materials Unit tab (categories: §9.3) | 🛑 redirect |
| `add a division called Snow Removal` | Settings → Divisions tab; setting a work item's division stays Maple's (§1.5.2) | 🛑 redirect |
| `unlink Carla Diaz from 12 Oak St` / `detach the contact` | the property or contact in the app; unlinking a task's property is Maple's (§7.6) | 🛑 redirect |
| `duplicate the patio estimate` / `clone this material` / `make a copy of …` | Duplicate in the row's menu on the Estimates, Materials or People page | 🛑 redirect |
| `generate the document for E0042` / `export a PDF` / `create a Google Doc` | the estimate's Documents button | 🛑 redirect *(user decision 2026-09-27: no document generation from chat)* |
| `add a photo to the task` / `upload a video` | Photo or Video on the task in the app | 🛑 redirect |

Detectors are narrow on purpose — a false positive refuses something Maple can do: "delete the duplicate contact" is a delete, "set the markup on work item 1 to 20%" is Maple's. Tests: `tests/test_out_of_chat_redirects.py`, `tests/test_maple_refusal_is_final.py`.

## 9.9 Deletes — a plain yes, from someone allowed to *(2026-09-27)*

Every Maple delete asks first, and only a plain yes confirms it — "yes", "yes, delete it", "confirm delete". Before, the catalog agents confirmed on any message *containing* "yes", "confirm" or "delete it" (#674): "delete it" deleted at once, "no, don't delete it" confirmed, and so did a name like "Reyes". A delete question lives one turn (§10.6). Deleting a property, contact, material, role, template or task is for Owners and Admins, as in the app (`delete_role_refusal`, `agents/conversation/delete_confirmation.py`); a Member is told so. A request about a record's links ("remove Ana from 12 Oak St") never deletes the record — it is redirected (§9.8); a request about its notes deletes the note you name, after asking (§3.9).

---

# 10. Multi-turn patterns

## 10.1 Field-then-value flow (all 4 CRUD resources)

*(2026-07-22: Tasks add a create-side variant — a create request with no
title stashes an awaiting-title `pending_intents` entry, and the bare
reply to "What should the task be called?" becomes the title, keeping any
inline notes from the first turn. See §7.1.)*

User responds to "What fields should I update?" with a bare field name:

```
User: update Landscaper
Maple: What fields should I update? (options: cost, description, ...)
User: cost
Maple: What's the new cost?
User: $50
Maple: I've updated the cost for Landscaper for you.
```

Pending-intent slot: `awaiting_value_for`. Canonical implementation: `agents/property/service.py`.

## 10.2 Add-size missing-field flow (materials)

When user says "add size {size} to {material}" without providing cost or unit:

```
User: add size 24x24 to concrete blocks with cost $8
Maple: I need a unit for size '24x24' on concrete blocks. Try again with cost and unit — for example: "add size 24x24 to concrete blocks with cost $10 and unit each".
```

Currently refuses and requests a retry with complete info (pending-intent persistence is a future UX refinement).

## 10.3 Calculation continuation flow (Calculator Agent) ✅

When the Calculator Agent asks for a missing parameter (area, depth, etc.), it
stores a `pending_calculation` record in the conversation context. On the next
turn the router pre-handler `handle_pending_calculation`
(`routers/agent_helpers/pending_calculation.py`) merges the user's reply into
the pending calculation **before** orchestrator classification — so a bare or
units-only answer is no longer misrouted to the Property Agent.

```
User: how many square feet, at 3-inches, will a yard of mulch cover
Maple: I can help with mulch coverage calculation! I just need a couple more details:
       - the area (in square feet)?
User: 750 square feet          ← absorbed as area_sqft, no longer "I couldn't find any matching properties"
Maple: Here's your mulch calculation: … Total needed: 6.94 cubic yards
```

- A bare number ("750") fills the single outstanding field.
- **Spelled-out numbers work too** *(2026-07-05)*: "Three inches deep.",
  "three inches of depth.", bare "three", "twenty-five square feet", "seven
  hundred and fifty", "two thousand square feet" — number words are normalized
  to digits before extraction (`_normalize_number_words`).
- A reply that supplies only some of the missing fields re-asks for the rest,
  keeping the pending state.
- **Pivot drops silently:** a value-less reply that clearly matches a different
  intent (a CRUD command, or a fresh full calculation query) abandons the
  pending calculation and falls through to normal routing.
- **Interrogative queries always pivot** *(2026-07-05)*: a "how much / how
  many / how long / calculate / convert" query pivots to a new calculation
  *before* value mining, so "how much concrete … 4 inches thick" never has its
  numbers merged into a stale pending calc (`is_fresh_calculation_query`).

Pending-state slot: `pending_calculation`. Continuation logic:
`CalculatorAgent.continue_pending()` +
`text_helpers.extract_continuation_values()`. Tests:
`tests/test_agent_helpers_pending_calculation.py`,
`tests/test_calculator_agent.py::TestContinuePending`,
`tests/test_calculator_text_helpers.py::TestExtractContinuationValues`.

> Note: re-engagement phrasings ("can you help with mulch coverage?") remain
> unsupported by the continuation fix. **Inverse-coverage math** ("how many sq
> ft will a yard cover" → solve for area) is now handled by the open-math path
> (§10.3.2) when `CALCULATOR_OPEN_MATH_ENABLED` is on.

## 10.3.1 Calculation catalog (Calculator Agent) ✅

Each type is one `CalcSpec` in `agents/calculator/registry.py` → one pure
function in `formulas.py`. The LLM only extracts parameters; all arithmetic is
deterministic. Adding a type is a single registry entry + formula.

| Calculation type | Example phrasing | Required inputs | Output | Status |
|---|---|---|---|---|
| `area_coverage` | "how many cubic yards of mulch for 2000 sq ft at 3 inches" | area_sqft, depth_inches | cubic yards | ✅ rule |
| `concrete_volume` | "how much concrete for a 10x12 slab 4 inches thick" | length_ft, width_ft, depth_inches | cubic yards | ✅ rule |
| `seed_coverage` | "how many lbs of grass seed for 5000 sq ft at 4 lbs/1000" | area_sqft, application_rate | pounds | ✅ rule |
| `linear_material` | "how many 8-ft fence panels for 100 linear feet" | linear_ft (opt. piece_length_ft) | pieces | ✅ rule |
| `paver_count` | "how many 12x12 pavers for 200 sq ft" | area_sqft, paver_length_inches, paver_width_inches | pieces | ✅ rule |
| `unit_conversion` | "convert 100 sq ft to sq m" | value, from_unit, to_unit | converted value | ✅ rule |
| `aggregate_tons` | "how many **tons** of gravel for 100 sq ft 4 inches deep" | area_sqft, depth_inches (opt. tons_per_cubic_yard, default 1.5) | tons | ✅ rule *(2026-06-15)* |
| `mulch_bags` | "how many **bags** of mulch for 100 sq ft at 3 inches" | area_sqft, depth_inches (opt. bag_size_cuft, default 2) | bags | ✅ rule *(2026-06-15)* |
| `retaining_wall_blocks` | "how many blocks for a 20 ft wall 3 ft high with 12x8 blocks" | wall_length_ft, wall_height_ft, block_length_inches, block_height_inches | blocks | 🤖 LLM *(2026-06-15 — regex doesn't extract block dims; LLM extraction path)* |
| `step_count` | "how many steps for a 42 inch rise" | total_rise_inches (opt. target_riser_inches, default 7) | steps | 🤖 LLM *(2026-06-15)* |
| `plant_count` | "how many plants for 100 sq ft at 12 inch spacing" (opt. "triangular spacing") | area_sqft, spacing_inches (opt. pattern square/triangular, default square) | plants | 🤖 LLM *(2026-06-15 — regex defers: "12 inch spacing" is spacing not depth)* |

All accept an optional `waste_factor_pct` ("with 10% waste") except
`step_count` and `unit_conversion`. The missing-parameter continuation flow in
§10.3 applies to every type: a bare number fills a single outstanding field, and
natural-language replies are matched for the common dimension phrasings
("20 feet long", "3 feet high", "8 inch spacing", "42 inch rise").

For area-based calculations, `area_sqft` is **derived from length × width** when
the user gives dimensions instead of an area (e.g. "the bed is 45 feet long and
6 feet wide" → 270 sq ft) — Maple won't re-ask for area it can compute. The
multiplication is done in code (`_derive_implied_params`), never by the LLM.

> **Deferred by design:** grading pitch (2% / quarter-inch-per-foot) and
> irrigation/drainage hydraulics (TDH, GPM, runoff, pipe sizing). The hydraulics
> set carries install/liability risk and needs reviewed engineering formulas —
> tracked for a separate phase.

## 10.3.2 Open-math reasoning path (no curated formula) 🤖 — *behind `CALCULATOR_OPEN_MATH_ENABLED`, default off (2026-06-29)*

When the extraction classifier decides **no curated formula faithfully models**
the request, it returns `open_math` instead of force-fitting the nearest type.
The researcher model then proposes an interpretation, the assumptions it made,
and one or more options — each an arithmetic *expression*, never a final number
— and a sandboxed allow-list evaluator (`safe_eval`) computes them. The reply
states the assumption and shows the working, so every number is auditable.

| Pattern | Example phrasing | Why no curated formula fits | Status |
|---|---|---|---|
| Spaced layout | "how many 3x2 ft stepping stones along a 20 ft path, 3 in apart" | gaps on a linear run; two possible orientations | 🤖 open_math *(flag)* |
| Reverse / inverse coverage | "how many sq ft can 25 yards of mulch cover", "how much area does 10 tons of gravel cover at 3 in" | formulas run forward (area + depth → quantity); the reverse has no formula and needs an assumed depth | 🤖 open_math *(2026-06-29 — flag)* |
| Composite / irregular shape | "how much mulch for an L-shaped bed, 10x4 plus 6x3" | multiple sub-shapes | 🤖 open_math *(flag)* |

Forward calculations (e.g. "how much mulch for 200 sq ft at 3 inches") stay on
their curated formula — the classifier only diverts genuine misfits. With the
flag **off**, an `open_math` query returns a short clarification instead of a
wrong number (it is never force-fit to a curated formula). Not yet promoted to
production. Tests: `tests/test_calculator_safe_eval.py`,
`tests/test_calculator_open_math.py`, `tests/test_calculator_open_math_live.py`
(opt-in `llm_e2e` — reverse + forward-sanity classification).

**⚠️ gap — labor-time from a production rate:** "how long does it take to edge
800 linear feet of beds?" is **not** handled. It is a labor/time question whose
answer depends on a crew role and a rate-card production rate (linear ft per
hour), not a material formula — and it doesn't even reach the Calculator: the
"how long" phrasing isn't in the calculation-query gate (which keys on "how
many" / "how much"). Maple currently declines gracefully and points to the
rate-card / estimate workflow (crew role → production rate → effort). A real
answer would need a production-rate lookup, or an assumed rate surfaced as an
assumption — a candidate for the open-math path once it can reach labor-time
questions.

## 10.4 Post-creation "link to a property?" follow-up ✅ implemented *(2026-06-06)*

After an estimate is created **without** a linked property, Maple appends an optional follow-up question to the response: *"Would you like me to link this estimate to a property now?"* (`extraction_helpers.build_optional_follow_up`, surfaced in `agents/estimate/service.py:1148`). The reply is now handled by the **generic pending-optional-follow-up state machine** (`routers/agent_helpers/optional_follow_up.py`):

- `("Estimate Agent", "create_estimate", "property")` is registered in the `get_optional_follow_up_spec` allowlist; `delegate_create_estimate.py` persists the pending record and seeds `active_estimate_code` on the create turn.
- **The legacy `pending_estimate_follow_up` flow is superseded** for this combo: the create path no longer dual-writes the legacy key (it remains only as a fallback when the generic spec isn't registered), and the legacy handler defers (`return None`) whenever the generic key is present. This handler-priority conflict — the legacy handler swallowing the reply — was the root cause of the original "Maple could not handle it" report.
- **One-turn affirmative+value**: a confirm-stage reply carrying residual content after the affirmation ("Yes, link it to Bob Residential") strips the affirmation + any link-verb preamble and delegates a synthetic `set the property of this estimate to Bob Residential` to the Estimate Agent (resolved via `active_estimate_code` anaphora). This residual shortcut is generic — contact-email/material-size follow-ups also gain one-turn completion.

```
Maple: I've created the estimate for you. … Would you like me to link this estimate to a property now?
User:  Yes, link it to Bob Residential
Maple: I've linked estimate E0042 to Bob Residential for you.   ← one turn (2026-06-06)
```

| Phrasing (turn 2, after the offer) | Intended behavior | Status |
|---|---|---|
| `Yes, link it to {property}` | one-turn: strip affirmation + link-verb preamble → `set the property of this estimate to {property}` → Estimate Agent | ✅ rule *(2026-06-06 — confirm-stage residual shortcut)* |
| `yeah, it's for {address}` / `sure, the {property} property` / `yep, tie it to the {property} property` / `yes please, link to {property}` / `go ahead — {property}` | one-turn: same residual shortcut (`_AFFIRMATION_PREFIX` covers yeah/yep/yup/sure/ok/please/go ahead/…) | ✅ rule *(2026-06-06 — the residual is re-parsed by the link handler's name/address extraction, so "it's for …" phrasings resolve via the address/name in the text)* |
| **bare property answer** — `{property}` / `{address}` / `link it to {address}` (no yes/no word) | the answer *is* the value while the slot is open → link | ✅ rule *(2026-06-06 — verified: a non-affirmative, non-negative, non-pivot reply at the confirm stage is treated as the collect-value answer)* |
| `Yes` (no property named) | re-ask: "Which property should I link estimate '{EST}' to?" | ✅ rule *(2026-06-06)* |
| `No` / `not now` / `no thanks` / `maybe later` | acknowledge, clear the slot, leave unlinked | ✅ rule *(2026-06-06 — these are in the `_NEGATIVE_VALUES` lexicon)* |
| `not right now` / `I'll do it from the portal` / `nah, leave it` | acknowledge, clear the slot, leave unlinked | ⚠️ gap *(NOT in the exact-match `_NEGATIVE_VALUES` lexicon (`routers/agent_helpers/text_helpers.py`) — currently treated as a property-name answer; the link lookup fails and re-prompts. Fix: extend the lexicon or add a soft-negative prefix check.)* |
| **pivot** — next message is clearly a fresh request (a new CRUD command or question) | drop the slot silently, route normally | ✅ rule *(pre-existing escape hatch in `handle_pending_optional_follow_up`; guard now documented inline. **2026-07-28** — the escape hatch ran at the confirm stage only; it now covers the collect-value stage too, because that stage can keep the slot open across turns. The follow-up field's own domain is exempt, so `the Downtown property` stays a value.)* |
| **unresolved answer** — the named property doesn't match anything (typo, ambiguous, or a property that doesn't exist) | re-ask and keep the slot open so the next reply is still read as the property | ✅ rule *(**2026-07-28** — previously the slot was popped before delegating and never restored, so the retry fell through to intent classification and was answered as a brand-new create request ("Sure, I'll help you create an estimate!"). `_rearm_on_unresolved` restores the record whenever the delegated agent returns `needs_clarification`.)* |
| `{name} - {street}` composite (e.g. `Primavera - 153 Asharoken Ave`) | resolve against the Property catalog | ✅ rule *(**2026-07-28** — `_resolve_property_address` gained a reverse-containment fallback tier, so a label combining both fields matches even though neither field contains the whole string.)* |
| misspelled or re-worded property (`primavara`, `153 Ashroken Ave`) | fuzzy-resolve, then confirm before linking | ✅ rule *(**2026-07-28 (b)** — tier 3 of `_resolve_property_address` + `pending_property_link_confirmation`. Reads disclose instead of confirming.)* |
| **ordinal reply to a near-tie list** — `2` / `(2)` / `option 2` | select that candidate from the list just shown | ✅ rule *(**2026-07-28 (b)** — candidate ids persisted on the pending record; out-of-range and sub-3-character replies re-ask instead of guessing.)* |
| **word-ordinal reply** — `the first one` / `second` / `2nd` / `the last one` / `the 2` | select that candidate from the list just shown | ✅ rule *(**2026-07-30** — reported: Maple offered "(1) Bob Residential; (2) Tang's Resident" and "The first one." was resolved as a property *name*, answering "I couldn't find a property matching 'The first one.'". The matcher was digits-only. Now `agents/text_utils.py::match_ordinal_reference` — `first`–`tenth`, `1st`–`10th`, `last`, and a digit with an optional leading determiner — shared with the Task confirmation flow so two numbered menus can't accept different words. Anchored at both ends, so a property named `First Street` still reaches the correction path.)* |
| **unresolvable reply while a candidate list is on screen** | re-show the numbered list | ✅ rule *(**2026-07-30** — with candidates armed there is no pinned property, so this branch rendered the confirm prompt's placeholder label: "I believe you are looking for 'that property'".)* |

**Remaining ⚠️ in this section (§10.4):** soft-negative phrasings not in the exact-match lexicon (`not right now`, `I'll do it from the portal`, `nah, leave it`) are treated as a property-name answer — extend `_NEGATIVE_VALUES` or add a soft-negative prefix check in `routers/agent_helpers/text_helpers.py`. **Note (2026-07-28):** now that an unresolved answer keeps the slot open, these soft negatives re-prompt instead of falling through — the same wrong outcome, but the user is no longer silently dropped out of the flow, and a pivot ("show me my estimates") still releases it. Tests: `tests/test_maple_estimate_field_edits.py::TestEstimateOptionalFollowUp` + `::TestEstimateFollowUpConfirmStage` (incl. the legacy-defers ordering test), `::TestFollowUpSurvivesUnresolvedValue`, and `tests/test_agent_helpers_delegate_create_estimate.py`.

---

## 10.5 Positional follow-up to a result list ("the fourth one") ✅ implemented *(2026-07-30)*

A **result list** ("Here are your tasks:\n- …") invites the same pick a numbered *menu* does, but phrased inside a sentence: `show me the fourth one`. §10.4's `match_ordinal_reference` is anchored at both ends because it reads menu *replies*, so it saw no ordinal here — and nothing recorded which rows had been shown anyway. The message carried no title, no id and no date, so resolution fell through to the recency fallback, which is row one by construction. Reported live: eight tasks listed, "show me the fourth one" answered with the first.

Both halves are now shared (`agents/text_utils.py`):

- **`record_listed_items` / `format_and_record_list_response`** — every list handler records the `(id, label)` rows it *renders* under `last_listed_items` (resource + ids + labels). One slice feeds the renderer and the record, so a truncated page can't leave positions pointing at rows the user never saw. Wired into Task, Property (incl. cross-resource), Contact (incl. contacts-at-property / estimate drilldown), Material, People, Template, and Estimate list responses. Estimates record their **E-codes**, the handle every estimate path resolves by.
- **`match_positional_reference` / `resolve_listed_reference`** — a superset of `match_ordinal_reference`: bare menu replies still resolve, plus the ordinal embedded in a request. Tail-anchored, with a small clause-boundary set (`to` / `and` / `with` / `as` / `into` / `'s` / punctuation) so an edit that names the row and then the new value still resolves while ordinals inside content don't. `resolve_listed_reference` also stands down for **estimate line-item numbering** — `#2` names a work item as readily as a listed row, and reading one as the other retargets the op at an estimate the user never opened.

Routing is part of the fix: a positional follow-up names no domain, so the rule classifier read `show me the fourth one` as a **material** lookup and bare `the second one` as `unknown`. `OrchestratorAgent._match_listed_positional_follow_up` now routes it to the resource that was listed, picking read / update / delete from the verb. It stands down when the message names a domain of its own or when any `pending_*` flow is armed — a numbered confirmation (§10.4) already owns "the second one".

| Phrasing (turn 2, after a list) | Intended behavior | Status |
|---|---|---|
| `show me the fourth one` / `the second one` / `open the first one` | read the Nth row that was listed | ✅ rule *(**2026-07-30** — the reported bug; previously answered with row one)* |
| `show me the last one` | the last row **listed**, not the newest record — resolved ahead of the "last / latest" recency step | ✅ rule *(2026-07-30)* |
| `delete the second one` / `archive the third one` | delete/archive that row (delete still confirms first) | ✅ rule *(2026-07-30)* |
| `rename the second one to {new}` / `change the third one's due date` / `mark the first one as done` / `add a note to the second one: {text}` | update that row — the clause boundary closes the reference before the new value | ✅ rule *(2026-07-30 — needed BOTH halves: the ordinal reaching the classifier, and `_TARGET_OR_PRONOUN` in `agents/task/text_helpers.py` accepting a positional target. Until the second one landed these routed to `update_task` and then asked "what would you like to update?", because the sub-op detectors only knew "the {title} task" and pronouns.)* |
| `archive the second one` | archive that row | ✅ rule *(2026-07-30 — archive is an UPDATE sub-op, not a delete; it was briefly mapped to the delete lane, which offered to delete a row the user asked to archive.)* |
| `show me #3` / `open number 3` / `option 2` | same pick by marked digit; a **bare** trailing digit stays a value (`set the price to 5`) | ✅ rule *(2026-07-30)* |
| **position past the end** — `the fourth one` against 3 rows | re-ask ("I only listed 3 tasks — which one did you mean?") | ✅ rule *(2026-07-30 — never falls through; falling through is what answered with the wrong row)* |
| **pick against a different resource's list** | ignored — the recorded resource must match the agent handling the message | ✅ rule *(2026-07-30)* |
| `rename the second one to {new}` **against a template list** | still refused — templates have no update intent, so that verb never routes to a read | 🛑 refusal *(2026-07-30 — §9 template-mutation policy is unchanged by positional routing)* |
| ordinal inside content — `put on the first coat of paint`, `add 2x4 lumber first`, `the second coat needs to dry` | not a pick; reaches free-text resolution unchanged | ✅ rule *(2026-07-30)* |
| **estimate line-item numbering** — `delete work item #2`, `show work item 2`, `remove line item #1` | NOT a row pick — these keep targeting the estimate the user has open (§1.5) | ✅ rule *(2026-07-30 — caught in review: `#2` is how a line item AND a listed row are named, so with an estimate list on screen a work-item op silently retargeted a different estimate. `resolve_listed_reference` now stands down whenever the message names a work item / job item / scope / line item.)* |

**Known limits:** the word table stops at `tenth` (`the eleventh one` is not a pick — marked digits cover the rest); and a row deleted between turns re-asks rather than guessing. *(2026-09-27: a list is current only while nothing but its own rows has taken focus since — "list my contacts" → open an estimate → "change the email of the second one" now asks "which one?" instead of editing the old list's second contact; #677.)* Tests: `tests/test_maple_listed_positional_reference.py` (per-resource round trips + orchestrator routing + estimate code resolution), `tests/test_text_utils.py::TestMatchPositionalReference` / `::TestListedItemsContext`.

## 10.6 One question at a time *(2026-09-27)*

Every question Maple asks — a yes/no, a numbered menu, a value ("What's the new city?"), a multi-step flow — goes through one gate (`routers/agent_helpers/open_question.py::decide_turn`). The next message either **answers** the newest open question, **cancels** ("never mind", "cancel", "forget it"), or is a **new request** — and then every open question is dropped before the message is classified. A question lives one turn. Before, a delete question survived turns that didn't answer it and a later "ok thanks" confirmed it (#671, #675), and an awaited field value captured every later message (#676).

| Turn 2, after a question | Behavior | Status |
|---|---|---|
| the answer (`yes`, `2`, `T0004`, `Cambridge`) | the question's owner applies it | ✅ rule |
| `never mind` / `cancel` | "No problem — …", every question dropped | ✅ rule |
| a new request (`list my properties`, `show me E0042`, `how do I add a property?`) | the question is dropped and the request runs | ✅ rule |
| a note or description asked for, and the reply reads like a command | stored as the text — only a cancel backs out | ✅ rule |
| a delete question left open beside another question | set aside, so a stray "yes" can't confirm it | ✅ rule |
| a question asked under another company | dropped unread | ✅ rule |

**Creates ask one field at a time** (2026-09-27): a contact, property, role or material create that is missing details asks for the next one alone and takes a bare reply as its value — "Dan Park" for the name, "30" for a wage, "Bulk Materials" for a category (§3, §2, §5.10, §4.11).

## 10.7 The record in focus *(2026-09-27)*

Each `active_<domain>_id` anchor records the turn it was set on. An anchor set this turn or last — or the record the portal page is showing — is fresh, and "it" acts on it. An edit that would reach an older anchor only through "it" or no name at all asks first: *"Just to check — do you mean Ana Reyes?"* (#677, `agents/conversation/focus.py`). Deletes (their confirmation names the record already) and notes (they overwrite nothing) don't ask. Pronouns pick the domain before recency does: "him"/"her" mean the contact, "there" the property. A record the message names always beats the one in focus ("show me contact Bob Lee" with Ana in focus shows Bob).

## 10.8 "What about X?" *(2026-09-27)*

Maple remembers the last **read** — its message and the records it was about — and rewrites an elliptical follow-up into that request with the new target (`agents/conversation/followup.py`). A write is never replayed: "what about Bob?" after changing Ana's phone does not change Bob's.

| Turn 1 → turn 2 | Behavior | Status |
|---|---|---|
| `who lives at 12 Oak St?` → `and 9 Maple Ave?` | the same question for 9 Maple Ave | ✅ rule |
| `show me contact Bob Lee` → `what about Ana Reyes?` | Ana's details | ✅ rule |
| `what's my pipeline this month?` → `and last month?` | the same question for last month | ✅ rule |
| `change Bob Lee's phone to …` → `what about Carla Diaz?` | not replayed — Carla's phone is left alone | ✅ rule |
| `… ` → `and then delete it` | a new request, not a new target | ✅ rule |

**A field said about the record just shown** (2026-09-27, the same module): right after a contact or property is created or shown, `his phone is 519-555-1234`, `her email is …`, `zip M4B 1B3` or a bare email or phone number is rewritten to `update {name}'s {field} to {value}` for that record (`rewrite_field_statement`; §2.6, §3.6). A post-create "link a …?" question doesn't claim them.

**Refining the list just shown** (2026-09-27, the same module): after an
estimate or task list, `just the drafts`, `which ones are on hold?`, `only the
ones over $1000`, `sort them by total`, `what's the total of those?`, `just the
overdue ones`, `how many is that?` replay that list with the refinement added
— so refinements chain (§1.1, §7.5).

## 10.9 "Show more" *(2026-09-27)*

A list that stops short of the whole result says how far it got and remembers where it stopped (`agents/conversation/paging.py`). On the next turn, `show more` / `more` / `next page` / `the rest` / `keep going` replays the same request — filters included — from there. Good for one turn; with no longer list open, Maple says so. Tasks page this way today (§7.5); other lists can adopt the same helper.

## 10.10 Conversation turns *(2026-09-27)*

Turns about the conversation itself are answered after the question gate has had its chance — an open question gets its "yes" first (`agents/conversation/meta.py`). These used to fall through to "I'm not quite sure what you mean" or a material lookup ("go ahead", "never mind" → `get_material`).

| Phrasing (no question open) | Reply | Status |
|---|---|---|
| `thanks` / `ok thanks` / `great` / `perfect` / `that's all` | "You're welcome — anything else I can help with?" | ✅ rule |
| `cancel` / `never mind` / `stop` | "There's nothing to cancel right now — …" | ✅ rule |
| a stray `yes` / `no` / `go ahead` | "I'm not waiting on an answer right now — …" | ✅ rule |
| `repeat that` / `say that again` | Maple's last reply again | ✅ rule |
| `start over` / `reset` / `clear the chat` | points to the clear button; drops anything Maple was waiting on | ✅ rule |

**Language** (2026-09-27): the conversation keeps the language the user is writing in. A short reply ("sí", "2", "Cambridge") is answered in that language rather than re-detected from two characters, and a language-neutral message (a code, a number) never switches it (`services/translation.py::conversation_language`).

---

# 11. Help intent

Handled by `agents/orchestrator/help_handler.py` via the `HelpHandler` class. The orchestrator routes to it when `is_help_query()` returns True (`agents/orchestrator/intents.py:487`); the router also short-circuits help before classification (`routers/agents.py:1093`), which is why a question about a record can land here (#691). The agent is always the **Orchestrator Agent** itself — help never dispatches to a downstream domain agent.

**Every answer comes from the user guide** (corrected 2026-09-27). `HelpHandler.build_result` sends the question to the shared LLM responder `answer_from_guide` (`agents/maple_guide/service.py:188`), which answers from `user_guides/users_guide.md`. `HelpHandler.detect_topic()` still classifies the question — personal, cross-domain link, enum, capabilities, how-to, in that order — but the topic is only metadata (`result.topic`): there are no canned enum lists, `valid_values` payloads or `_CONTEXTUAL_EXAMPLES` any more. The topic families below describe classification, not the answer text.

The result payload always has `operation="help"`, `read_only=True`, `topic`, the `SUPPORTED_INTENTS_BY_AGENT` mapping under `result.capabilities`, and `intent="help"` on the envelope. The *classification* is rule-only — it bypasses the LLM classifier even when `use_llm=True` (see `test_orchestrator_help_query_bypasses_llm`) — but the answer is an LLM call.

## 11.1 Capability queries

Direct capability questions. Match via `HELP_DIRECT_HINTS` (`intents.py:299`).

| Phrasing | Topic | Status |
|---|---|---|
| `help` | `capabilities` | ✅ rule |
| `help me` | `capabilities` | ✅ rule |
| `help please` | `capabilities` | ✅ rule |
| `I need help` | `capabilities` | ✅ rule |
| `what can you help me with?` | `capabilities` | ✅ rule |
| `what can you do?` | `capabilities` | ✅ rule |
| `how can you help me?` | `capabilities` | ✅ rule |
| `what can I ask?` | `capabilities` | ✅ rule |
| `supported intents` | `capabilities` | ✅ rule |
| `capabilities` | `capabilities` | ✅ rule |

### Feature-definition queries *(2026-07-22)*

A definitional lead-in (`tell me about` / `what is` / `what are` / `explain` / `describe`) followed by a **bare resource noun** routes to HELP (guide-backed answer), not CRUD — previously "tell me about tasks" resolved to `list_tasks` and answered "I couldn't find any matching tasks." Detector: `is_feature_definition_query` (`intents.py`), applied inside `is_help_query` so both tiers share it. Works for every resource noun (tasks, estimates/quotes, properties, contacts, materials, templates, people/labor, to-dos).

| Phrasing | Routing | Status |
|---|---|---|
| `tell me about tasks` / `Tell me about the Tasks feature` | `help` (guide §7.3 Tasks) | ✅ rule |
| `what is a task?` / `what are tasks?` | `help` | ✅ rule |
| `tell me about estimates` / `what are templates?` | `help` | ✅ rule |
| `tell me about MY tasks` (possessive determiner) | `list_tasks` — the user's data, not a definition | ✅ rule |
| `tell me about task {task}` / `tell me about {contact}` | `get_task` / `get_contact` — named lookups unaffected | ✅ rule |

## 11.2 Enum queries

Match via `HELP_ENUM_KEYWORDS` + `HELP_QUESTION_CUES` (`intents.py:309-322`). `HelpHandler.detect_topic()` disambiguates by domain keyword; the answer comes from the user guide.

### Contact roles — topic `contact_roles` (`ContactRole`: Home Owner, Manager, Administrator)

| Phrasing | Status |
|---|---|
| `what are the contact roles?` | ✅ rule |
| `what are the valid contact roles?` | ✅ rule |
| `what roles are available?` | ✅ rule |
| `what are the valid roles for a contact?` | ✅ rule |
| `available values for role` | ✅ rule |
| `choices for contact role` | ✅ rule |

### Estimate statuses — topic `estimate_statuses` (`EstimateStatus` has 13 values, §1.4)

| Phrasing | Status |
|---|---|
| `what are the estimate statuses?` | ✅ rule |
| `what statuses can an estimate have?` | ✅ rule |
| `what are the valid estimate statuses?` | ✅ rule |

### Estimate divisions — topic `estimate_divisions`

| Phrasing | Status |
|---|---|
| `what are the estimate divisions?` | ✅ rule |
| `what are the valid estimate divisions?` | ✅ rule |
| `which divisions can an estimate have?` | ✅ rule |

## 11.3 Procedural how-to queries

Match via `HELP_INSTRUCTIONAL_PATTERNS` (`intents.py:337`): `how do i`, `how can i`, `how to`, `how would i`, `how should i`, `steps to`, `step by step`, `process for`, `process to`, `guide for`, `guide to`, `explain how`, `show me how`, `walk me through`, `what are the steps`, `what's the process`.

When an instructional pattern hits, `detect_topic()` tries to match an action keyword (`create`, `update`, `delete`, `list`, `get`, `find`, `add`, `edit`, `remove`) and a domain keyword (`contact(s)`, `estimate`/`quote(s)`, `property`/`properties`, `material(s)`, `labour`/`labor`). Result is a `how_to_<action>_<domain>` topic; falls back to `how_to_manage_<domain>s` if only domain matched, or `how_to_use_system` if neither.

### Full how-to (action + domain matched)

| Phrasing                             | Topic                     | Status                                                       |
| ------------------------------------ | ------------------------- | ------------------------------------------------------------ |
| `how do I create an estimate?`       | `how_to_create_estimate`  | ✅ rule          |
| `how do I update a contact?`         | `how_to_update_contact`   | ✅ rule                                        |
| `how do I create a contact?`         | `how_to_create_contact`   | ✅ rule                                        |
| `how do I create a property?`        | `how_to_create_property`  | ✅ rule                                        |
| `how do I archive an estimate?`      | `how_to_manage_estimates` | ✅ rule *(no action keyword "archive", falls back to manage)* |
| `steps to add a material`            | `how_to_add_material`     | ✅ rule                        |
| `explain how to create an estimate`  | `how_to_create_estimate`  | ✅ rule                                                       |
| `walk me through making a contact`   | `how_to_manage_contacts`  | ✅ rule *("making" isn't an action keyword)*                  |
| `how can I update a material price?` | `how_to_update_material`  | ✅ rule                                                       |
| `how do I approve an estimate?`      | `how_to_manage_estimates` | ✅ rule *("approve" not an action keyword)*                   |

### Domain-only how-to (no action keyword matched)

| Phrasing | Topic | Status |
|---|---|---|
| `guide to setting up a property` | `how_to_manage_properties` | ✅ rule (pluralization defect closed by Wave 1 Phase 1) |
| `what's the process for archiving an estimate?` | `how_to_manage_estimates` | ✅ rule |

### Generic how-to (no action, no domain)

| Phrasing | Topic | Status |
|---|---|---|
| `how do I use this system?` | `how_to_use_system` | ✅ rule |
| `show me how to use Maple` | `how_to_use_system` | ✅ rule |
| `how to get started` | `how_to_use_system` | ✅ rule |

## 11.4 Help vs. CRUD precedence

When a message contains **both** a CRUD intent (firm action+domain match) and an enum keyword, CRUD usually wins. Two important carve-outs:

| Phrasing | Result | Why |
|---|---|---|
| `help me create a contact for Jane` | `create_contact` → Contact Agent | "help me" is a polite prefix, not an instructional question. CRUD action+domain is firm. |
| `how many labour roles do I have?` | `list_labours` → Labour Agent | `action == "list"` short-circuit at `intents.py:517` prefers CRUD over help even though "roles" is an enum keyword. |
| `what are the material categories?` | `list_material_categories` → Orchestrator Agent | Rule-level CRUD match fires before help classifier. See §9.3 refusal for create/delete variants. |
| `how do I create a contact?` | `help` → Orchestrator Agent | Instructional pattern ("how do i") always wins over CRUD — `intents.py:506`. |

## 11.5 Help gaps

Phase 1 of the xfail backlog (plan: `documentation/development/plans/maple-xfail-wave-1.md`) closed most §11.5 entries on 2026-05-02. Remaining gaps below are awaiting Wave 2 design work.

| Phrasing | Intended behavior | Status |
|---|---|---|
| `tutorial` / `getting started` / `docs` / `documentation` | `capabilities` topic via `HELP_DIRECT_HINTS` | ✅ rule (Phase 1). |
| `examples` / `give me some examples` / `what kinds of things can I ask?` | `capabilities` topic | ✅ rule (Phase 1). |
| `what can't you do?` / `what are your limitations?` | `general_question` via interrogative guide-fallback | ✅ rule (already covered before Phase 1). |
| `does Maple support X?` / `is there a way to do X?` | `capabilities` / `general_question` via help routing | ✅ rule (Phase 1) — equipment refusal now gated by `_looks_interrogative`; `is there a way` and `does maple support` added to `HELP_INSTRUCTIONAL_PATTERNS`. |
| `what is a work item?` / `what's a property?` | Glossary / terminology help via guide-fallback | ✅ rule (already covered). |
| `what fields does a contact have?` | Schema help — return Pydantic model fields | ✅ rule (already covered via fallback). |
| `what happens when I approve an estimate?` / `what does archive do?` | Action-semantics help | ✅ rule (already covered via fallback). |
| `how does Maple work?` / `explain Maple to me` / `what do you do?` | `capabilities` topic | ✅ rule (Phase 1). |
| `what are the labour units?` / `what are the material units?` | `labour_units` / `material_units` topics | ✅ rule (Phase 1) — `unit`/`units` added to `HELP_ENUM_KEYWORDS`; §5.12 + §5.13 in `users_guide.md` provide source content. |
| `I am lost` / `I am stuck` | `capabilities` topic | ✅ rule (Phase 1). |
| `what should I ask?` / `what can I do?` | `capabilities` topic | ✅ rule (Phase 1). |
| `list your features` | `capabilities` topic | ✅ rule (Phase 1). |
| `how do I add a work item?` | `how_to_manage_estimates` (estimate line-item alias) | ✅ rule (Phase 1) — `work item`/`job item`/`line item` detected and routed to estimate scope. |
| `how do I link a contact to a property?` | `how_to_link_contact_property` topic | ✅ rule (Phase 1) — cross-domain detection runs before single-domain loop; §5.11 in `users_guide.md`. |

### Pluralization defect — `how_to_manage_propertys` (closed Phase 1)

`HelpHandler.detect_topic` previously returned `f"how_to_manage_{domain_name}s"`, which produced `how_to_manage_propertys` for the property domain. Phase 1 introduced an inline `plural_topic` map (`property → properties`, others append `s`) so the topic key round-trips correctly to `how_to_manage_properties`.

## 11.6 Social & personality

Maple handles greetings and personal/anthropomorphized questions in **two tiers**:

1. **Bare greetings** (`hey`, `hi maple`, `good morning`) are caught in the **orchestrator** (`agents/orchestrator/service.py`, `_detect_policy_short_circuit` via `is_greeting`) and answered with an instant canned reply from `GREETING_RESPONSES` in `agents/text_utils.py`. This is a **new `social` intent** (operation `social`, `read_only`) — **not** a help topic — so there is **no LLM call**. Suggestion chips come from `_SOCIAL_SUGGESTIONS`.
2. **Personal questions** (`how are you?`, `what do you look like?`, `are we friends?`) are detected by `is_personal_question` in `agents/text_utils.py` and routed through the **existing help path** — `HelpHandler.detect_topic` returns the **new `personal` topic** — and answered by the LLM guide responder (`agents/maple_guide/service.py`) **from Maple's persona** (`agents/maple_persona.py`), via a rule-1 exemption in the guide prompt.

The personal-question detector is deliberately **topic-keyed** so product-capability phrasings stay in the product lane (see the Negatives table below).

### Greetings — `social` intent (canned, no LLM)

| Phrasing | Intent | Status |
|---|---|---|
| `hey` | `social` | ✅ rule (canned) |
| `hi` / `hi maple` | `social` | ✅ rule (canned) |
| `hello` | `social` | ✅ rule (canned) |
| `good morning` / `good afternoon` / `good evening` | `social` | ✅ rule (canned) |
| `howdy` | `social` | ✅ rule (canned) |
| `hola` / `buenos días` (Spanish, defense-in-depth) | `social` | ✅ rule (canned) |

### Personal questions — `personal` help topic (LLM, persona-answered)

| Phrasing | Topic | Status |
|---|---|---|
| `how are you?` / `how's it going?` (feelings) | `personal` | ✅ (LLM/persona) |
| `what do you look like?` (appearance) | `personal` | ✅ (LLM/persona) |
| `are you hot?` (appearance) | `personal` | ✅ (LLM/persona — *playful deflect*) |
| `are we friends?` (friendship) | `personal` | ✅ (LLM/persona) |
| `are you married?` / `do you have a partner?` (relationships) | `personal` | ✅ (LLM/persona — *playful deflect*) |
| `i love you` (flirty) | `personal` | ✅ (LLM/persona — *playful deflect, no reciprocation*) |
| `are you an AI?` (identity) | `personal` | ✅ (LLM/persona — *honest yes*) |
| `how old are you?` (biography) | `personal` | ✅ (LLM/persona) |
| `where do you live?` (biography) | `personal` | ✅ (LLM/persona) |
| `what's your sign?` (biography) | `personal` | ✅ (LLM/persona) |

### Negatives (stay in the product lane)

These read like questions *about* Maple but are really **capability / CRUD** requests — the detector deliberately excludes them so they route to normal help/CRUD, **not** `personal`.

| Phrasing | Routes to | Status |
|---|---|---|
| `are you able to add contacts?` | `capabilities` / CRUD (not `personal`) | ✅ (correctly excluded) |
| `can you create an estimate?` | `capabilities` / `create_estimate` (not `personal`) | ✅ (correctly excluded) |
| `how are you estimating this job?` | help / estimate flow (not `personal`) | ✅ (correctly excluded) |
| `how are you able to help me?` | `capabilities` (not `personal`) | ✅ (correctly excluded) |

**Persona boundaries** (`agents/maple_persona.py`): flirty messages get a **playful deflection** with **no romantic reciprocation**; explicit or persistent advances drop the humor and redirect to work; AI-identity questions are answered **honestly** (she is an AI); replies stay short and pivot back to the task; she **never** reveals other users' data.

---

# 12. Appendix

## 12.1 Where tests live

| Path | Purpose |
|---|---|
| `platform/tests/test_maple_crud_coverage.py` | Matrix — 182 cases (17 categories, 11 known gaps) × Tier 1 + Tier 2 |
| `platform/tests/_maple_coverage_data.py` | Matrix data (17 categories; 5 CRUD resources incl. Tasks + estimate/equipment/calculator extras) |
| `platform/tests/test_maple_routing_snapshot.py` + `platform/tests/maple_routing/` | Routing snapshot — a 1,159-phrasing corpus × conversation states; re-record with `UPDATE_MAPLE_SNAPSHOT=1` only after reviewing the diff |
| `platform/tests/test_maple_estimate_status_queries.py` | Estimate count + value queries (Phase A) |
| `platform/tests/test_maple_material_size_operations.py` | Material size ops (Phase B) |
| `platform/tests/test_maple_help_coverage.py` | HELP intent — supported phrasings + xfail gaps (§11) |
| `platform/tests/test_material_agent.py` | Material Agent handler integration |
| `platform/tests/test_estimate_agent.py` | Estimate Agent handler integration |
| `platform/tests/test_orchestrator_intents.py` | Orchestrator intent resolution |
| `platform/tests/test_maple_template_crud.py` | Template CRUD — routing, refusals, apply-to-estimate (§6) |
| `platform/tests/test_maple_work_item_ops.py` | Work-item field operations — routing, op detection, regression (§1.5; recurring deferred) |
| `platform/tests/test_maple_new_phrasings.py` | May 2026 expansion — clear bug, win alias, age filter, analytics, material/role field queries, cross-resource "linked to" |
| `platform/tests/test_maple_phrasing_expansion.py` | June 2026 expansion — status ratios/comparisons, age/staleness (`updated_at`), status-`in`, material name∪category qualifier (routing + pure parsers/formatter) |
| `platform/tests/test_maple_listed_positional_reference.py` | Positional follow-ups to a result list — "show me the fourth one" (§10.5): per-resource round trips, orchestrator routing, estimate-code resolution |
| `platform/tests/reports/maple_crud_gap_report.md` | Auto-generated gap report (regenerates each test run) |

## 12.2 How to run

```bash
cd platform
./run_tests.sh tests/test_maple_crud_coverage.py                     # Tier 1 only (~8s)
./run_tests.sh tests/test_maple_crud_coverage.py -m ""               # Tier 1 + Tier 2 (~3min, ~$0.05, needs OPENAI_API_KEY)
./run_tests.sh tests/test_maple_estimate_status_queries.py tests/test_maple_material_size_operations.py
./run_tests.sh tests/test_maple_help_coverage.py                     # HELP intent (one strict xfail: "why does labor show no profit?", §1.5.7)
./run_tests.sh tests/test_maple_new_phrasings.py                     # May 2026 expansion (31 tests)
```

## 12.3 Current matrix score (Tier 1 / Tier 2)

**Both tiers re-counted 2026-07-29**, straight from a full `./run_tests.sh tests/test_maple_crud_coverage.py -m ""` run against the live gpt-5.6 models — not adjusted by hand. This is the first Tier 2 run since the 2026-07-14 model upgrade; the previous figures (95/117) were measured on the retired gpt-5.5/5.4 family and are superseded.

| Category | Tier 1 *(2026-07-29)* | Tier 2 *(2026-07-29)* | Verdict |
|---|---|---|---|
| direct_imperative | 15/15 | 15/15 | covered |
| casual | 15/15 | 15/15 | covered |
| possessive | 12/15 | 11/15 | rule gap (Task slice) + 1 LLM miss |
| count | 15/15 | 15/15 | covered |
| filter_find | 15/15 | 15/15 | covered |
| field_targeted_update | 12/15 | 14/15 | rule gap (Task slice) |
| implicit_relationship | 13/15 | 15/15 | rule gap (Task slice); LLM covers it |
| bulk | 15/15 | 15/15 | refused correctly |
| verbless | 12/15 | 12/15 | rule gap (Task slice) |
| material_size | 6/6 | 6/6 | covered |
| material_query_variants | 5/5 | 5/5 | covered (Wave 3 Workstream B) |
| estimate_outbound | 5/5 | 5/5 | covered (Wave 4 + 4.1 — orchestrator routing + Property/Contact/Estimate agent cross-resource branches; contact-anchored variant gated on person-name shape) |
| assumption_adjustment | 4/4 | 4/4 | covered (2026-07-26) |
| estimate_work_item_edits | 8/8 *(2026-09-24)* | 8/8 *(2026-09-24)* | covered (the written command list, `agents/estimate/command_grammar.py`) |
| task_operations | 8/8 | 8/8 | covered |
| equipment_blocked | 3/3 | 3/3 | refused correctly |
| calculator | 8/8 | 7/8 | 1 LLM miss ("how much topsoil do I need for 1000 sq ft") |

**Totals: Tier 1 171/182 · Tier 2 173/182** *(2026-09-24, live; the other rows are the 2026-07-29 counts, unchanged)*.

*2026-09-24 run: Tier 2's 9 misses are the same classes as below, with one
swap — `verbless/property` "tell me about 123 Main St" missed once (the model
call returned no intent; it passed 3/3 on rerun) while `possessive/property`
"what's 123 Main St's city" passed. Both are standing LLM-tier variance.*

*Unchanged by the 2026-09-13 Markup/Margin split or the 2026-09-14 Gross
Margin rename: neither change was
documentation-only for Maple — no classifier rule was added, no refusal lifted,
and `test_maple_crud_coverage.py` exercised the same 174 phrasings (182 since the
2026-09-24 `estimate_work_item_edits` category). The six new
§1.5.7 conceptual phrasings route to HELP through existing rules and are
covered by `test_maple_help_coverage.py`, which is not part of this matrix.*

*Tier 2's 9 misses: seven are the same known Task bare-title class as Tier 1's ("Fix the Fence Gate" without a verb). The other two — `possessive/property` "what's 123 Main St's city" and `calculator` "how much topsoil do I need for 1000 sq ft" — were verified to fail identically on `main`, so they are standing LLM-tier gaps, not regressions. The 2026-07-29 model upgrade moved Tier 2 from 81% (95/117) to 95% (165/174, the matrix size then); `implicit_relationship` improved most (4/12 → 15/15).*

The 11 Tier 1 misses are the known-gap `xfail(strict=False)` Task bare-title class — the Task resource slice is 24/35; every other resource is at 100% (property 27/27, contact 27/27, material 38/38, labour 27/27, estimate 17/17, equipment 3/3, calculator 8/8). The `cross_resource` join layer lives in `agents/cross_resource.py`; per-agent join handlers in Contact / Property / Estimate read `context.filter_by` to apply the constraint, including the Wave 4/4.1 `estimate`, `property`, and `contact` cross-types.

*Count-provenance note (2026-07-29): the two numbers this table previously carried were **both already stale before the fuzzy-property-matching work** — the totals line read `Tier 1 127/127` (a 2026-05-02 snapshot) while a 2026-07-22 parenthetical above it read `Tier 1 159/170`; neither matched the generator. They have been replaced by a single re-count rather than patched. Note also that this table counts **coverage-matrix cases** from `tests/test_maple_crud_coverage.py`, not the hand-curated ✅/⚠️/🛑 rows elsewhere in this document — so §10.4's fuzzy-property rows do not appear in it, and the 159/170 → 163/174 delta comes from other work, not from that feature.*

*Note (2026-06-09): the new Social & personality surface (§11.6) — greetings via the `social` intent and personal questions via the `personal` help topic — is not yet represented in the auto-generated matrix above; see §11.6 for its phrasing catalog.*

## 12.4 Related docs

- `CLAUDE.md` > "Maple (Orchestrator) — CRUD assistant policies" — architectural overview
- `documentation/development/plans/maple-xfail-wave-1.md` — active plan for closing the remaining xfail backlog

---

# 13. Coverage blind spots & extension ideas

The matrix is shape-complete for the nine CRUD categories but never exercises several phrasing families real users will type. This section is the gap-hunting backlog — entries here aren't tracked as ⚠️ gaps in §1–§9 because they're conceptual classes, not specific phrasings ready to wire. Promote an entry to a per-resource ⚠️ gap row once you've picked a concrete phrasing and a target intent.

## 13.1 Language / phrasing variation

- **Negations:** `I don't need the Landscaper role anymore`, `remove John Doe — he moved`
- **Conjunctions / multi-action:** `create a contact and link it to {property}`, `delete the Foreman role and add Operator instead`
- **Typos / stemming:** `delet the proprty at 123 Main`, `contacs`, `labours` vs `labour roles` — partly mitigated by `agents/fuzzy_utils.py`
- **Pronouns / anaphora across turns:** `update it`, `that one`, `the last one I created` (estimate-scoped anaphora exists in §1.7; cross-resource anaphora is the gap)
- **Questions that imply get vs list:** `is there a contact named John?`, `do I have concrete blocks?`

## 13.2 Value / field shapes not exercised

- **Dates / date ranges:** `contacts added this month`, `estimates from last week`
- **Numeric ranges / comparisons:** `materials under $10` (already in §4.9), `labour roles costing more than $40/hr`
- **Multi-field update:** `set John Doe's phone to X and email to Y`
- **Nullable / clearing:** `remove John Doe's phone number`, `clear the description on {material}`

## 13.3 Domain overlap ambiguity

The matrix uses disjoint tokens by design — real users won't:

- Same name across domains: a contact and a property both called "John's Place"
- Role-name collisions: a contact named "Foreman Smith"
- Addresses that look like material names

A small `ambiguity` test category would assert the classifier's tiebreak behavior.

## 13.4 Refusal surface beyond bulk + equipment

- **Destructive at smaller scale:** `delete the last 5 contacts` (N>1 but not "all") — listed as a §9.4 ⚠️ gap
- **Cross-tenant / out-of-scope:** `show me other companies' estimates`
- **Non-CRUD slipping through:** `email John Doe`, `schedule a visit`

## 13.5 Highest-value extensions (ranked by ROI)

If we want to expand coverage, here's the order:

1. **`status_transition` matrix category for estimates** — fixed verb set × 5 EstimateStatus values × 2-3 subjects. ~30 new cases. Cleanest starter; status transitions already exist in §1.4.
2. **Active-entity anaphora** — exercises the `active_estimate_code` session path beyond what §1.7 currently asserts.
3. **Filter by status / date** — `show me draft estimates from last week`, `approved quotes over $10k`. Needs date-range parsing.
4. **Direct coverage of the add-work-item regex path** — `agents/orchestrator/service.py` work-item rules; today only hit by orchestrator unit tests.
5. **Cross-resource outbound from estimate** — mirrors §8.2 / §8.3 inbound pattern (e.g. `which property is {EST} for?`, `what materials does {EST} use?`).
6. **Ambiguity fixtures** — see §13.3.
7. **Typo / stemming fixtures** — 5–10 common misspellings per resource to catch fuzzy-match regressions.
