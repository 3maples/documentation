# Maple Phrasing Reference

Canonical catalog of user phrasings Maple supports, organized by resource. Add new use cases you want Maple to handle; Claude will update the ✅/⚠️ status after wiring the classifier rule or confirming existing behavior.

**Last updated:** 2026-10-22

### Recent changes

**2026-10-19 (review after the October features):** the reference was read
against the shared material catalog, session history and files on a message,
and each candidate phrasing planned twice on the live planner. New ✅/🛑 rows
for what already works — a misspelt command, "is there a contact named Bob?" /
"do I have Black Mulch?", two contact fields at once, "start a new chat", a
contact updated from a business card, a property made from a work order, a
material's cost from an invoice, one task per line of a photographed list
(§2–§4, §3.9, §7.6.1, §10.10). Twenty-four gaps, G1–G24, are ⚠️ rows in §3,
§4.1, §4.11, §7.13, §10.10 and §10.11 — hiding, showing and resetting standard
materials, Chat history, videos, a task's photos, clearing a field, "added this
month", undo — with the plan to close them, and Simon's four decisions (undo
only when asked and confirmed; a copy offered for a standard material; filed files
listed, not read; one material per message), in
[`plans/2026-10-19-maple-phrasing-gaps-plan.md`](plans/2026-10-19-maple-phrasing-gaps-plan.md).
The full live run that day (§12.4) added G25–G33: four rows the planner now
misses every time (§4.8, §5.11, §5.5, §8.1), an offer to delete a task when
asked to remove its PDF, a stray yes re-planning a stale delete, a task status
not taken as an answer, and two harness gaps — file rows run without a file,
and the conversations run on today's state.

The full dated history lives in
[`maple-phrasing-changelog.md`](maple-phrasing-changelog.md) (split out of this
file 2026-09-27). **2026-09-27:** a multi-turn audit corrected rows found wrong
against the code and added an **Open gaps** line to each resource section
(§1–§7) citing the follow-ups in
[`code-review-followups.md`](code-review-followups.md); the fixes are planned in
[`plans/2026-09-27-maple-multi-turn-everywhere-design.md`](plans/2026-09-27-maple-multi-turn-everywhere-design.md). **Review fixes, same day:** a task edit that names no task and has none in
focus asks "Which task?" instead of changing the newest one, and a stale task
in focus asks "Just to check — do you mean …?"; a status verb is a command
only at the start of the message ("I can't finish the fence task" changes
nothing); "it", "the last" and the like are never read as a line's or
record's name ("remove it from work item 2", "the address for it"); "her city
is Guelph" is the contact's; task days follow the user's time zone (the portal
sends it); a task Maple creates for a teammate notifies them; a material
rename onto a size it already has, or a remove whose label two sizes share,
is refused.

**2026-09-28 (second review):** every task edit — give, unassign, due date,
property, status, assign, archive — is a command only at the start of the
message, after at most a lead ("hey Maple,", "and", "also", "thanks!",
"please", "can you", "I'd like to" — never "I need to", which is work
still to do), so "don't give it to Jordan" changes
nothing; "could you complete it?" is a request. A create's assignee followed
by another sentence stays in the note, unassigned. A material size of "it" /
"the one" / "this material" is the material in focus ("Which material do you
mean?" when there is none; a reply that is one of the company's materials
finishes it however it reads — "Show Stone", "Clear 3/4 Stone" — while a
request such as "change the cost of Topsoil to 20" is taken as a request); "what sizes does
it come in?" lists them. On the portal, stacked (a phone, or a desktop the
Maple panel squeezes), only a contact or property the user picked — a tap, an
`?open=` or `?contactId=` / `?propertyId=` link — is "this one" to Maple, and
it stays so after its sheet closes. Negated renames, field and notes edits
still wrote — follow-up #762, fixed 2026-09-30. A create that describes a size ("a bed that
is 5 feet by 15 feet") and asks for "a separate work item" creates the
estimate: a listed create is no longer read as a question about a work item,
which turned it into a fuzzy update of whichever estimate's title it
resembled (§1.3). A message that mentions a work item is read as a question
about it only when it opens with a question word ("what", "which", "is",
"are", "when", "who" …, after at most a "hey,") — a bare "is" or a relative
"which" further in, or a "?" on a request, doesn't make one. So "remind me to
call Bob about the patio work item, it is urgent" and "create a task for the
fence work item?" are tasks and "add a contact named Ana Reyes, she is the
owner, for the patio work item" a contact, not estimate edits (§1.5.2).
"How many did I sell?" counts Won, Scheduled and Completed — there is no Sold
status — with or without a count before it, and a count that follows a
customer's list keeps the customer. Every estimate count names what it
counted ("You have 2 sold estimates for Bob Lee."), and "for Bob Lee" now
narrows a count or a status list instead of being dropped (§1.1).

**2026-09-29:** the answer to "Which material do you mean?" is looked up
among the company's materials by exact name instead of loading the whole
catalog (#776), and a name that opens with words a reply is cleaned of —
"No. 57 Stone", "The Good Stuff" — now finishes the size change instead of
dead-ending on "Multiple materials matched" (#775, §4.8).

**2026-09-29 (phase 1):** "Which estimate? … or its title." now takes the
title — looked up exactly among the company's estimates, so "Remove Sod and
Reseed" answers instead of being read as "delete contact Sod And Reseed" —
and every "Which estimate?" is remembered, reads included. A title several
estimates share lists them (#615; a delete lists them without remembering),
a named title that matches nothing never shows a different estimate (#616),
and "the last estimate" with none says so (#22) (§1.7).

**2026-09-29 (phase 3):** a task status or teammate the company has answers
Maple's question even when it reads as a request ("New Request", "Create
Estimate"); both assignee questions are remembered, and the teammate lookup
is one indexed, company-scoped query that tidies the reply ("Jordan.") and
logs a failure instead of hiding it. A status column named like a date
moves the card (#711); an ambiguous teammate in a list says so (#752) (§7.7,
§7.8).

**2026-09-29 (phase 4):** after "no" to "Just to check", *"Okay — which
contact did you mean?"* is a real question: a name finishes the request on
the record named — a numbered list when several share it, one more try when
none does (§10.7). Two gaps logged there: a role word ("the homeowner's
phone", #759) and "the city there".

**2026-09-29 (phase 5):** "Which task did you mean?" and the Task agent's
"Which property did you mean?" are remembered too: the name — a task title
that reads as a request included — finishes the request, and a value given
about a task that has gone is kept for the task named next (#713) (§7.11).

**2026-09-29 (phase 7):** an estimate list filter, a property link or a
material swap that names nothing asks which, and the name in reply is
written into the request, which runs again (§1.8). "with the highest total"
and "which estimates have been sent?" are no longer material joins (#722,
#723), and "have been / were sent" filters by the status.

**2026-09-30 (metrics plan, phase 0):** a rename, field edit or notes edit on
a task is a command only at the start of the message, after at most a lead,
like every other task edit — so "don't rename the fence task to Gate", "I won't
change the due date of the fence task to Friday" and "don't add a note to it:
call Bob" change nothing (#762). A note's own words are still its content: "add
a note to it: don't park on the lawn" appends (§7.6, §7.6.1). "Pipeline"
and "backlog" are a metric only in a question ("what's in my backlog?", "how
big is my backlog?") or alone ("pipeline"): "rename work item 2 to the
pipeline trench" and "add a note to this estimate: locate the pipeline" write,
and a reply "check the pipeline under the driveway" answers the question it
was asked (#721, §1.9). With an estimate open, only a question about it —
"what's the total?", "is it sent?" — is answered from it: "what is markup?",
"how much does mulch cost?" and "what's my average markup?" are not (#719),
and "which estimate has the highest total?" is the biggest estimate (#720)
(§1.2). A customer whose surname is a status word counts as the
customer: "how many estimates for Min Won?" counts Min Won's estimates — it
counted Min's won ones, and Jasmine's too (#779); and "how many won estimates
for Bob Lee in review?" asks which status was meant instead of counting won and
ignoring the rest (#780) (§1.1).

**2026-10-01 (metrics plan, Phase 4, lines):** **how much of a material or
role is in your estimates** — "how much Black Mulch is in my open
estimates?", "how many hours of Foreman have I sold this year?" — per unit,
never converted, no dollars (§8.4). The second counted open estimates and
dropped Foreman.

**2026-10-01 (metrics plan, Phase 4, tasks):** **task counts by person and
by property** — "how many overdue tasks does each person have?", "how many
tasks per property?", "who has the most overdue tasks?" — open tasks unless
"overdue" or "all" is said (§7.4.1). They were a flat list or one total;
"each person" was looked up as a teammate.

**2026-10-01 (metrics plan, Phase 4, help):** "what can you calculate?" /
"what numbers can you give me?" answer with the figures Maple gives — the
user guide gained section 6.6, "Asking for a figure" (§11.1).

**2026-10-01 (metrics plan, Phase 4):** **catalog figures** — "how many
materials per category?" lists every category with its count (it gave the
number of categories); "what's my most expensive material?", "what's my
average material price?", "what's my most expensive role?" and "what's the
average wage of my roles?" answer from the catalog (they were guide answers,
the role ones about *contact* roles). Prices and rates are compared within a
unit and never averaged across units (§4.12, §5.11).

**2026-10-01 (metrics plan, Phase 3):** **a win rate counts sold work** —
Won, Scheduled and Completed against Lost (decision 8). "What's my win rate?",
"won-lost ratio", "won vs lost", "how many estimates did I win vs lose?" and
"how am I doing on bids?" counted only estimates still in Won, so a job left
the wins when it was scheduled; they also take a customer, property or
division ("what's the win rate for Bob Lee?") and a calendar period, and
"and last year?" / "what about Ana Reyes?" repeat them. "Won vs Lost status"
and "draft vs approved" are still the literal counts. A win rate ranked, by
month or compared was said back (decision 18) until 2026-10-13, when Simon
reversed it: each row is answered, its own win rate (§1.9, §1.12).
**Gross margin and average markup across estimates** — "what's my gross
margin this year?", "what margin am I making on Bob Lee's jobs?", "what's my
average markup?" were help. They answer for sold work unless a status is said,
summing dollars (markup weighted by cost), and say how many work items an
unpriced activity left out (decisions 15–17) (§1.12).

**2026-09-30 (metrics plan, Phase 2):** Maple **ranks, breaks down by month
and compares periods**. "Who are my top 5 customers by won value?", "which
property has the most estimates?" and "which division earns the most?" list
the ranking — sold value unless a status is said (decision 9), 5 rows unless a
number is, "show more" for the rest, "the second one" opens that customer or
property, "show me the top 10" resizes it. "Value by month this year" gives
every month on your clock and the total. "How does this month compare to last
month?" and "am I up on last year?" compare like with like — the same days of
the earlier period — and give the change in dollars and percent (decisions 10,
11). "And last year?" and "what about Ana Reyes?" repeat each. "Just the won
ones" after a metric answer is not supported yet (decision 13) (§1.12).

**2026-09-30 (review of the metrics work):** a metric question no longer
answers for the wrong record — "what's our revenue excluding Elm House" was
Elm House's revenue, and "over the last year" found a customer called Grover;
a scope the rules can't read now goes to the LLM tier, and a part of a name
matches only whole words. "How much has he spent?" is the customer in focus.
Two customers with one name are counted together instead of a "which one?"
that never ended. Answering "Which one did you mean?" with "Tim Hortons" no
longer rewrites "lifetime". "Whats my pipeline" is the pipeline again, not a
material; "how much is the total?" about the open estimate is answered again;
"how many estimates for Min Won this year?" counts Min Won's. The router's
task-note rule no longer claims "don't add a note to the task" (§1.1, §1.2,
§1.9, §1.12, §7.6).

**2026-09-30 (metrics plan, Phase 1 task 9):** estimate totals are summed by
the new metrics engine. "What's the total of those?" and "the total value of
my open estimates" now add up every matching estimate — they summed the first
20 — and "the total value of my maintenance estimates" adds up only the
Maintenance work, not the whole of each estimate with one Maintenance item.
The pipeline and completed windows start at midnight on the boundary day, as
the dashboard's cards do (§1.1, §1.9). Task 10: the dashboard reads the same
engine, and "Completed" — the card and "what's my completed value?" — now
means marked Completed in the last 30 days, not edited in them (§1.9).
Task 11: **Maple answers metric questions** — lifetime won for a property,
sold to a customer this year, averages, the biggest estimate, a status's total
for a place — each reply naming what it counted (new §1.12). "What's the total
value of sold estimates for Bob Lee?" now reads Bob (§1.1). Task 12: the
biggest estimate named is the one in focus next; "which one?" and "couldn't
find" take a name in reply; "and last year?" and "what about Elm House?"
repeat the question; the public widget refuses. "What's its status?" about the
open estimate works again — the #719 fix had stopped reading "its" as "it"
(§1.2). Task 13: a paraphrase no rule reads — "what has Bob Lee bought from
us over the years?" — is read by the LLM tier into the same fixed choices, and
the engine answers it (§1.12).

**2026-09-30 (phase 8):** a name Maple asks for that doesn't exist yet is
the name, however it reads — an activity ("Remove Sod"), a role ("Load
Truck"). A new task asks *"What should the task say?"* and takes the reply
as its text (#470). The new material's name stays deferred (§4.11).

**2026-09-29 (deferred):** answering a question with a record's name, from
[`plans/2026-09-28-maple-name-answers-plan.md`](plans/2026-09-28-maple-name-answers-plan.md),
leaves material-catalog management and the multi-match "please specify"
questions for later. Each is logged as a ⚠️ gap: a verb-led category, unit or
new material name (§4.9, §4.11), and a bare name in reply to "Multiple …
matched" for properties, contacts, materials and roles, or to "Which
template…?" (§2.9, §3.8, §4.9, §5.9, §6.8).

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

**New rows use the Plan format** (2026-10-12; plan
[`plans/2026-10-12-phrasing-reference-as-test-source-design.md`](plans/2026-10-12-phrasing-reference-as-test-source-design.md)).
The rest of this doc moves to it section by section; `platform/tests/test_phrasing_reference_rows.py`
fails on a new row in the old format, and on any Plan row it can't read.

```
| Phrasing | Plan | Status |
|---|---|---|
| `how many did I win?` / `count my wins` | `list_estimates` filter.sold count | ✅ |
| `make the patio 800 sq ft` [wi] | `resize_work_item` | ✅ |
| `make the patio bigger` [wi] | ask | ✅ |
| `upload a CSV of my properties` | refuse `out_of_chat` `csv_import` | 🛑 |
| `mark {EST} as won` | conversation `<id>` | 🛑 |
| `mow every two weeks` | — | ⚠️ gap — #NNN |
```

- **Phrasing** — whole phrasings in backticks, separated by ` / `; placeholders
  as in the table above. A starting state goes in brackets after them —
  `[est]`, `[wi]`, `[est_then_mat]`, `[<kind>_focus]`. No prose, ellipses or
  arrows: a row that takes several turns names an acceptance conversation
  (`platform/tests/maple_conversations/corpus.py`) as its plan.
- **Plan** — what the planner should do: an op from
  `platform/agents/planner/schema.py` with the fields that are the point of
  the row (a nested field as a dotted path, a bare name for a flag; an
  estimate edit's command by its op, `edit_estimate` commands=set_title). The
  live run scores the op exactly — another op of the same kind is a
  difference. Two ops that make the same write (a task's note as `add_note`
  or `update_task` fields.notes_append) agree only when the row names the
  record's kind (`add_note` parent.domain=task);
  `refuse` with its reason (`out_of_chat` also names the capability); `ask`;
  `conversation` with its id; or `—` for a gap with no plan yet.
- **Status** — ✅ supported, 🛑 refused by design, ⚠️ gap (with its
  follow-up). Notes go after the marker.

`python scripts/phrasing_reference_rows.py` (in `platform/`) lists what's left in
the old format by section and any Plan row's problem.

**Estimates:** a phrasing a rule should handle becomes an entry in
`platform/agents/estimate/command_grammar.py` with accept/reject examples in
`tests/test_command_grammar.py` and a row in §1.0 — never a regex elsewhere
(design 2026-09-25). A phrasing no entry covers is the planner's (🤖) or the
classifier's; mark it ⚠️ gap only if the live suite shows they miss it.

1. Add a Plan row in the right section: the intended op as its plan (or `—` if you don't know it yet) and ⚠️ gap as its status.
2. Ping Claude with "add these phrasings to Maple" — Claude will write failing tests, make the planner handle it, and flip the status to ✅ here.
3. For phrasings that should be refused, add a Plan row with `refuse` and its reason and 🛑 — under §9 or the resource's own section — and note why after the marker.

Tests live in `platform/tests/test_maple_crud_coverage.py` (matrix) and `platform/tests/test_maple_*.py` (targeted). Running the matrix regenerates `platform/tests/reports/maple_crud_gap_report.md` with live pass/fail counts.

---

# 1. Estimates

Estimate has 17 cases in the CRUD coverage matrix (`estimate_work_item_edits` 8, `estimate_outbound` 5, `assumption_adjustment` 4). Most of its surface — multi-turn generation, status transitions, work items, linking — doesn't fit the generic category templates, so it is curated here.

## 1.0 The written command list *(2026-09-25)*

The complete set of estimate phrasings a rule handles
(`agents/estimate/command_grammar.py`). Anything not here goes to the edit planner (edits)
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

| Phrasing | Plan | Status |
|---|---|---|
| `show me my estimates` [est] | `list_estimates` | ✅ grammar entry list_estimates |
| `how many estimates do I have?` [est] | `list_estimates` count | ✅ grammar entry list_estimates |
| `open {EST}` [est] | `get_estimate` | ✅ grammar entry get_estimate |
| `show me the estimate for the Smith property` [est] | `list_estimates` | ✅ the property's estimates — it may have several |
| `show the work items on {EST}` [est] | `list_work_items` | ✅ grammar entry list_work_items |
| `show work item 2` [est] | `get_work_item` | ✅ grammar entry get_work_item |
| `create an estimate for sod at 12 Oak St` [est] | `create_estimate` | ✅ grammar entry create_estimate |
| `rename this estimate to Spring Cleanup` / `update the description to Front yard refresh` [est] | `edit_estimate` | ✅ grammar entries rename_estimate / set_estimate_field — no estimate named: only while it's in focus |
| `add a work item called Fence to {EST}` / `add a work item "Build stone patio" to {EST}` [est] | `edit_estimate` | ✅ grammar entry add_work_item |
| `add a work item to {EST}` / `Add a new work item to it.` [est] | `edit_estimate` | ✅ grammar entry add_work_item — asks the name; "it" is the last record worked with — the estimate or one of its work items; with a material or contact in focus it isn't the estimate's |
| `Add a new work item to it. The client wants to build a patio in their backyard. It will be about 900 sq ft in size.` / `add a work item to {EST}: 200 sq ft paver patio with edging` / `Add a new work item to it for 900 sq ft. The client wants a patio.` / `add a work item for a cedar fence along the back and price it` [est] | `generate_work_item` | ✅ grammar entry add_described_work_item — prices the description as new work; 15+ characters after the separator or "for" |
| `delete work item 2` / `remove the patio work item from {EST}` [est] | `edit_estimate` | ✅ grammar entry remove_work_item |
| `delete it` [est] | `delete_estimate` | ✅ grammar entry remove_pronoun — "it" is the freshest anchor; the estimate itself is a delete of the estimate |
| `delete it` [wi] | `edit_estimate` | ✅ grammar entry remove_pronoun — the work item in focus is the freshest anchor |
| `rename work item 2 to Back Fence` [est] | `edit_estimate` | ✅ grammar entry rename_work_item |
| `rename it to Back Fence` [wi] | `edit_estimate` | ✅ grammar entry rename_pronoun |
| `set the division of work item 1 to Maintenance` [est] | `edit_estimate` | ✅ grammar entry set_work_item_field — the description with no value asks it |
| `update the description on work item 2` [est] | ask | ✅ grammar entry set_work_item_field — the description with no value asks it |
| `change my work item division to Design/Build` [wi] | `edit_estimate` | ✅ grammar entry set_work_item_field |
| `set the markup on work item 2 to 20%` / `set tax rate on the patio work item to 7% on {EST}` [est] | `edit_estimate` | ✅ grammar entry set_percentage |
| `make the gross margin 30%` [wi] | `edit_estimate` | ✅ grammar entry set_gross_margin |
| `set the profit margin on the patio work item to 20%` [est] | `edit_estimate` | ✅ grammar entry set_gross_margin |
| `set the total on work item 1 to $1,000` [est] | `edit_estimate` | ✅ grammar entry set_total |
| `leave a note on this estimate that says: check the gate code` / `add a note: call Bob` / `add a note to that estimate saying check the gate code` / `add a note to our estimate saying check the gate code` / `drop a note on {EST} saying check the gate code` / `new note for this estimate saying check the gate code` [est] | `add_note` | ✅ grammar entry add_note — "add a note: call Bob" is the record in focus; "about drainage" keeps "about …" in the body; "On work item 1, …" names the target first |
| `add a note to work item 2: check drainage` / `add a note to work item 2 about drainage` / `On work item 1, add a note: check drainage` [est] | `edit_estimate` commands=add_work_item_note | ✅ a work-item note (`add_work_item_note`) |
| `add 20 concrete blocks to work item 2` / `add 10 bags of mulch to the front patio work item` / `remove concrete blocks from work item 2` / `change the quantity of mulch in work item 1 to 12` / `update the price of mulch in work item 1 to $5` [est] | `edit_estimate` | ✅ grammar entries add_material / remove_material / update_material *(2026-09-27)* — a plural finds the singular catalog item or line |
| `add activity Grading with role Foreman for 4 hours to work item 2` / `add an activity to work item 2` / `remove the Grading activity from work item 2` [est] | `edit_estimate` | ✅ grammar entries add_activity / add_activity_prompt / remove_activity *(2026-09-27)* — "add an activity to work item 2" asks its name, then adds it |
| `make the excavation activity 8 hours` / `change the role on the Excavation activity to Landscaper` / `assign the Landscaper role to the cleanup activity` / `update the rate for the Planting activity to $45/hr` [wi] | `edit_estimate` | ✅ grammar entry update_activity *(2026-09-27)* |
| `move work item 2 to Tree Care` / `assign work item 2 to Tree Care` / `put work item 2 under Tree Care` / `drop the tax on work item 2` [est] | `edit_estimate` | ✅ grammar entries move_work_item_division / clear_percentage *(2026-09-27)* — dropping the tax sets it to 0% |
| `adjust work item 2 to $1500` / `round work item 2 to $1500` / `bump work item 2 to $1500` / `reduce work item 2 to $1500` / `make work item 2 an even $1500` / `set a flat rate of $1500 on work item 2` [est] | `edit_estimate` | ✅ grammar entry set_total *(2026-09-27 wordings)* |
| `change the margin on work item 2 to 25%` / `I want a 30% margin on work item 2` [est] | `edit_estimate` | ✅ grammar entry set_gross_margin *(2026-09-27 wordings)* |
| `put a 15% markup on it` [wi] | `edit_estimate` | ✅ grammar entry set_percentage *(2026-09-27 wordings)* |
| `change the name of work item 2 to Back Fence` / `delete the Driveway scope from {EST}` [est] | `edit_estimate` | ✅ grammar entries rename_work_item / remove_work_item *(2026-09-27 wordings)* — a work item may be called a "scope" or "job item" |
| `how many work items does {EST} have?` [est] | `list_work_items` count | ✅ grammar entry list_work_items *(2026-09-27 wordings)* |
| `put together an estimate for a cedar fence` / `draw up an estimate for a cedar fence` / `draft an estimate for a cedar fence` / `I need a quote for a cedar fence` / `quote a fence for Bob Lee` [est] | `create_estimate` | ✅ grammar entry create_estimate *(2026-09-27 wordings)* |
| `mark {EST} as sent` [est] | `set_status` status=Sent | ✅ ported entry set_status |
| `retitle {EST} as Fall cleanup` [est] | `edit_estimate` | ✅ ported entry set_estimate_title |
| `Set note on {EST} to "check the gate code"` [est] | `add_note` | ✅ ported entry estimate_note |
| `generate a work item for a cedar fence on {EST}` [est] | `generate_work_item` | ✅ ported entry generate_work_item |
| `apply the {template} template to {EST}` [est] | `apply_template` | ✅ ported entry apply_template |
| `add a Fence work item and set its tax to 13%` [est] | `edit_estimate` | ✅ a plan names the work item it adds by "it" or its exact description *(2026-10-03, #645)* |

**Refused by rule:** bulk delete and equipment (orchestrator, on the command
part only — never on a note body, a new name or a reply to Maple's question);
a note to a material or role. **Refused by the planner:** labor burden
(`labor_burden`) and a stated material cost (`material_cost`). A plan may name the work item it adds by "it" or its exact description — "add a Fence work item and set its tax to 13%" (2026-10-03, #645); a position still numbers the estimate as it was loaded.

## 1.1 Count & status queries

| Phrasing | Plan | Status |
|---|---|---|
| `how many estimates do I have?` / `count my estimates` [est] | `list_estimates` count | ✅ |
| `how many estimates with status draft?` [est] | `list_estimates` count filter.statuses=Draft | ✅ |
| `what's the total estimates with status approved?` [est] | `metric` metric=total | ✅ the approved estimates' value |
| `can you add up the estimates with status approved?` [est] | `list_estimates` total filter.statuses=Approved | ✅ *(closed in Phase A1)* |
| `how many approved estimates do I have?` [est] | `list_estimates` count filter.statuses=Approved | ✅ |
| `count my draft quotes` [est] | `list_estimates` count filter.statuses=Draft | ✅ quotes = synonym |
| `what is the total value of the open estimates` [est] | `metric` status=open | ✅ aggregated across the open estimates *(closed in xfail-wave-3 Workstream C — `_AGGREGATE_VALUE_QUERY_PATTERN` + `_OPEN_ESTIMATE_QUERY_PATTERN` short-circuit `_handle_list_estimates` to a single dollar figure)* |
| `show me draft estimates from last week` [est] | `list_estimates` filter.statuses=Draft filter.period=last_week | ✅ *(closed in xfail-wave-3 Workstream C — `_parse_estimate_date_filter` adds a `$gte/$lte` constraint on `created_at`)* |
| `approved quotes over $10k` [est] | `list_estimates` filter.statuses=Approved filter.amount.over=10000 | ✅ *(closed in xfail-wave-3 Workstream C — verbless plural-domain inference + `_parse_estimate_amount_filter` adds a `$gt`/`$lt` constraint on `grand_total`; `k`/`m` suffixes supported)* |
| `what materials does {EST} use?` [est] | `list_materials` filter.related | ✅ filtered to one estimate's lines *(routes via `_CROSS_RESOURCE_QUERY_PATTERNS` with `filter_by={type=estimate, name=E0042}`; since 2026-09-27 (#682) it reads the materials of every work item — it read a top-level list `Estimate` doesn't have and always said "doesn't list any materials yet")* |
| `which of {EST}'s materials cost over $10?` [est] | `list_materials` filter.related filter.price.over=10 | ✅ the estimate's own lines by unit price — *"Estimate E0001's materials priced over $10.00: Polymeric sand ($20.00)."* *(2026-10-11, #845 — fell back)* · today's pipeline: ⚠️ |
| `the Stone materials on {EST}` [est] | `list_materials` filter.related filter.category=Stone | ✅ the estimate's own lines by catalog category *(2026-10-11, #845 — fell back)* · today's pipeline: ⚠️ |
| `how many materials on {EST} are under $10?` [est] | `list_materials` count filter.related filter.price.under=10 | ✅ the estimate's own lines by unit price *(2026-10-11, #845 — fell back)* · today's pipeline: ⚠️ |
| `what roles are on {EST}?` / `which roles are on {EST}?` [est] | `list_labours` filter.related | ✅ *(symmetric Labour-agent drilldown; since 2026-09-27 (#682) it reads the activities' and labour lines' roles in every work item, and "which roles …" is delegated — it showed "Intent identified: …")* |
| `how many estimates did I win this month?` [est] | `list_estimates` count filter.sold filter.period=month | ✅ *(May expansion — "win" added as a verb-form alias for EstimateStatus.WON in `_estimate_status_from_text`; since #784 "win" is the sold set)* |
| `show only estimates with Won status this month` [est] | `list_estimates` filter.statuses=Won filter.period=month | ✅ *(status + date qualifiers already compose; no new code needed)* |
| `show me all estimates older than 60 days` [est] | `list_estimates` filter.stale_days=60 | ✅ *(`_AGE_FILTER_PATTERN` + age branch in `_parse_estimate_date_filter` returns `(None, cutoff)`; field is `updated_at` as of the 2026-06-02 expansion)* |
| `show me estimates that are 30 days old` [est] | `list_estimates` filter.stale_days=30 | ✅ *(2026-06-02 — `_AGE_DAYS_OLD_PATTERN`; "X days/weeks/months old" → at-least-X-old)* |
| `estimates that are 40 days or older` [est] | `list_estimates` filter.stale_days=40 | ✅ *(2026-07-08 — "N days/weeks/months **or older**" alternation added to `_AGE_DAYS_OLD_PATTERN`; verbless forms route via `_match_estimate_list_filter`)* |
| `which estimates haven't been updated in 30 days?` / `estimates not touched in a month` [est] | `list_estimates` filter.stale_days=30 | ✅ *(2026-06-02 — staleness alternation in `_AGE_DAYS_OLD_PATTERN`; verbless forms routed via `_match_estimate_list_filter`)* |
| `find estimates in draft` / `estimates in review` [est] | `list_estimates` filter.statuses | ✅ *(`in` connector in `_estimate_status_from_text`; only fires when the token after `in` is a known status — "estimates in Toronto" stays a property query)* |
| `show me Draft estimates at property {property}` [est] | `list_estimates` filter.statuses=Draft filter.property | ✅ *(May expansion — "at\s+property" added to the property→estimate cross-resource pattern)* |
| `list estimates for Bob Lee` [est] | `list_estimates` filter.customer | ✅ that customer's (contacts → their properties); a name that is neither a customer nor a property is answered ("I couldn't find a customer or a property called …") *(2026-09-27, #687 — the name was dropped and every estimate listed)* |
| `show estimates for Elm House` [est] | `list_estimates` filter.property | ✅ that property's *(2026-09-27, #687 — the name was dropped and every estimate listed)* |
| `show me estimates from last month` [est] | `list_estimates` filter.period=last_month | ✅ the calendar month, as every figure and the dashboard read it *(Simon, 2026-10-10, switchover phase 7e)*; today's pipeline: the past 30 days *(2026-09-27, #687 — "last" was read as "the latest one" and returned a single row)* |
| `what's the total value of my draft estimates over $1000 before tax?` [est] | `list_estimates` total before_tax filter.amount.over=1000 | ✅ the list's total before tax — *"The combined value of your 2 draft estimates over $1,000 is $1,500.00, before tax."*; every list total says which (*"…, including tax."*) *(2026-10-05 — a list's total was tax-inclusive whatever was asked, and said nothing about tax. `… of my sold estimates before tax` stays the list's too: the metric dates a period differently, so tax said must not change which estimates count — review 2026-10-05 #1)* |
| `how many Lawn Care estimates do I have?` [est] | `list_estimates` count filter.division | ✅ the company's own divisions — *"You have 1 estimate in Lawn Care right now."*; the built-in names still match a company with none of that name *(2026-10-06 — counts and lists knew only the built-in names; the figures read the company's own. `agents/estimate/work_scope.py`)* |
| `list my Maintenance estimates` [est] | `list_estimates` filter.division=Maintenance | ✅ the company's own divisions *(2026-10-06)* |
| `how many Maintenance estimates for Bob Lee?` [est] | `list_estimates` count filter.division=Maintenance filter.customer | ✅ both scopes — *"You have 3 estimates in Maintenance for Bob Lee."* *(review 2026-10-06 #1 — any division said dropped the customer, and a word before "estimates" hid "for Bob Lee" from the list reader)* |
| `how many estimates for Maintenance?` [est] | `list_estimates` count filter.division=Maintenance | ✅ "for Maintenance" is the division alone *(review 2026-10-06 #1)* |
| `how many estimates for Lawn Care Co?` [est] | `list_estimates` count filter.customer | ✅ with a "Lawn Care" division, the customer alone — *"You have 1 estimate for Lawn Care Co."* *(review 2026-10-06 round 2 #1 — a division's words inside the customer's name added that division's filter)* |
| `how many Lawn Care estimates for Lawn Care Co?` [est] | `list_estimates` count filter.division filter.customer | ✅ with the division said outside the name, both *(review 2026-10-06 round 2 #1)* |
| `how many recurring estimates do I have?` [est] | `list_estimates` count filter.recurring=true | ✅ estimates with a work item of that type — a total sums only that work *(2026-10-06, user — "recurring" was no filter)* |
| `how many draft one-time estimates?` [est] | `list_estimates` count filter.statuses=Draft filter.recurring=false | ✅ *(2026-10-06, user)* |
| `how many recurring Maintenance estimates for the last six months?` [est] | `list_estimates` count filter.recurring=true filter.division=Maintenance filter.days=6 filter.window_unit=month | ✅ with the division — *"You have 1 estimate in Maintenance with recurring work in the last 6 months."* *(2026-10-06, user. A counted window — "the last six months", "the last 2 years" — is the figures' rolling window, in digits or words: since the same date, each unit capped (`time_windows._CAPS`), not 30-day months capped at a year (review round 2 #2))* |
| `what's the total value of my maintenance estimates?` [est] | `metric` | ✅ the division's work items only *(2026-09-30, metrics task 9 — it summed each estimate's whole total, and only the first page of 20. Summed by `services/maple_metrics.py`)* |
| `total value of my open estimates` [est] | `metric` status=open | ✅ every matching estimate, more than 20 of them too *(2026-09-30, metrics task 9 — only the first page of 20 was summed)* |
| `how many estimates have been sold?` / `how many sold estimates do I have` / `how many estimates did I sell?` / `how many did I sell?` [est] | `list_estimates` count filter.sold | ✅ over **Won + Scheduled + Completed** — "sold" is no status of its own: everything a customer bought, however far it has since moved *(2026-09-28 — "sold" was no filter, so it counted every estimate. `_SOLD_ESTIMATE_QUERY_PATTERN` needs the estimate noun, so "what unit is River Rock sold by?" is untouched; a named status still wins. **2026-10-03, #784 (user):** "won" alone is this set too — Won + Scheduled + Completed, as in a money question — and the reply says so; only "status won" said outright ("with status won", "won status", "in won status") is the Won status)* |
| `what's the total value of my sold estimates?` [est] | `metric` status=sold | ✅ Won + Scheduled + Completed *(2026-09-28)* |
| `how many did I sell?` / `how many have been sold` / `how many were sold` [est] | `list_estimates` count filter.sold | ✅ with nothing before it *(2026-09-29 — was help: "how many" is a count, never a help question. A `list_estimates` grammar entry built on `SOLD_VERB`, shared with the agent's sold filter)* |
| `how many did we sell this month?` [est] | `list_estimates` count filter.sold filter.period=month | ✅ with nothing before it *(2026-09-29)* |
| `how many estimates for Bob Lee?` [est] | `list_estimates` count filter.customer | ✅ that customer's (or property's), with the status and period *(2026-09-29 — the customer was dropped from every count and every status list, so each counted the whole company. The `list_estimates` entry takes a status before "estimates" and a name after "for"; a trailing period, amount or status — "this year", "over $1000", "with status X", "in draft status", "that are won", in any order — is read off the name, and a status read off it is the one applied: `agents/estimate/list_query.py::read_list_query` reads name, status and status set in one pass. `tests/test_estimate_list_answers.py` checks what was actually counted against a seeded database)* |
| `how many won estimates for Bob Lee?` / `how many estimates for Bob Lee that are won?` [est] | `list_estimates` count filter.customer filter.sold | ✅ *(2026-09-29; "won" is the sold set since #784)* |
| `how many sold estimates for Bob Lee this year?` [est] | `list_estimates` count filter.customer filter.sold filter.period=year | ✅ *(2026-09-29)* |
| `how many estimates for Bob Lee in draft status?` / `how many estimates for Bob Lee in review?` / `how many estimates for Bob Lee on hold?` [est] | `list_estimates` count filter.customer filter.statuses | ✅ *(2026-09-29)* |
| `how many estimates for Bob Lee over $1000?` [est] | `list_estimates` count filter.customer filter.amount.over=1000 | ✅ *(2026-09-29)* |
| `show me draft estimates for Bob Lee` [est] | `list_estimates` filter.customer filter.statuses=Draft | ✅ *(2026-09-29)* |
| `how many estimates for Min Won?` / `how many estimates for Min Won this year?` [est] | `list_estimates` count filter.customer | ✅ a surname (or property name) that ends in a status word is that customer's estimates *(2026-09-30, #779 — "Won" was read off the name as a status and "Min" substring-matched other contacts. The whole name is looked up exactly first; the status is read off it only when the whole name is no one's. Review 2026-09-30 #3: also with a period or status after it, and when the orchestrator's contact rule hands over the whole name)* |
| `show me estimates for Min Won` [est] | `list_estimates` filter.customer | ✅ *(2026-09-30, #779)* |
| `how many draft estimates for Min Won?` / `how many estimates for Min Won in review?` [est] | `list_estimates` count filter.customer filter.statuses | ✅ a status said outside the name still applies *(2026-09-30, #779)* |
| `how many won estimates do I have?` / `how many are won?` [est] | `list_estimates` count filter.sold | ✅ Won + Scheduled + Completed — *"You have 2 won estimates for Bob Lee (Won, Scheduled, Completed)."* *(2026-10-03, #784 — "won" was the Won status in a count or list but the sold set in a money question, so "how much did I win?" covered more estimates than "how many won estimates?". User decision: bare "won"/"win" is the sold set everywhere)* |
| `show me won estimates for Bob Lee` [est] | `list_estimates` filter.sold filter.customer | ✅ Won + Scheduled + Completed *(2026-10-03, #784)* |
| `how many estimates with status won do I have?` [est] | `list_estimates` count filter.statuses=Won | ✅ the Won status only *(2026-10-03, #784 — "status won" said outright; `text_helpers.WON_STATUS_SAID_RE`, shared with metric questions)* |
| `how many estimates for Bob Lee with status won?` [est] | `list_estimates` count filter.statuses=Won filter.customer | ✅ the Won status only — *"You have 1 won estimate for Bob Lee."* *(2026-10-03, #784)* |
| `show me my won status estimates` [est] | `list_estimates` filter.statuses=Won | ✅ the Won status only *(2026-10-03, #784)* |
| `how many won estimates for Bob Lee in review?` / `how many draft estimates for Bob Lee that are sold?` [est] | ask | ✅ *"That asks for two statuses at once — review or won. Which one did you mean? Ask again with just one …"* *(2026-09-30, #780 — the first status read was counted and the other dropped. Not a resumable question: re-ask with one status)* |
| `what's the total value of sold estimates for Bob Lee?` [est] | `metric` status=sold subject | ✅ the customer's total — *"Sold value for Bob Lee, all time: $2,000.00 across 2 estimates (Won, Scheduled, Completed), including tax."* *(2026-09-30 — a metric question, §1.12. It totalled every customer)* |
| `total value of estimates for Bob Lee` [est] | `metric` subject | ✅ the customer's total *(2026-09-30, §1.12)* |
| `how many draft and sent estimates do I have?` / `how many estimates that are draft or sent?` [est] | `list_estimates` count filter.statuses=Draft,Sent | ✅ every status in the list, named back — *"You have 2 draft and sent estimates right now."* A list said together is one set; a status said somewhere else as well is still asked about (#780) *(2026-10-05 — a list counted only the last status named: "draft and sent" counted Sent. `agents/estimate/status_lists.py`; `list_query.statuses_of`. "vs" still compares — only "and", "or" and commas make a list)* |
| `how many Draft, Review, and Sent estimates?` [est] | `list_estimates` count filter.statuses=Draft,Review,Sent | ✅ *(2026-10-05)* |
| `list my draft or review estimates` [est] | `list_estimates` filter.statuses=Draft,Review | ✅ *(2026-10-05)* |
| `show me completed or lost estimates for Bob Lee` [est] | `list_estimates` filter.statuses=Completed,Lost filter.customer | ✅ *(2026-10-05)* |
| `how many won and lost estimates?` [est] | `list_estimates` count filter.statuses | ✅ a set inside the list counts as itself and says so — *"You have 5 won and lost estimates (Won, Scheduled, Completed, Lost) right now."* *(2026-10-05)* |

*Not yet in the Plan format — after a list or a count, or a rule for every reply rather than a phrasing (phase 3):*

| Phrasing                                             | Intent → Agent                                                 | Status                                                                                                                                                                                                                                                              |
| ---------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| after a list: `just the drafts` / `which ones are on hold?` / `only the ones over $1000` / `only the ones from last month` / `only for Bob Lee` | the same list, narrowed | ✅ rule *(2026-09-27 — refinements chain; §10.8)* |
| after a list: `only the won ones` / `which of those are won?` | the same list, narrowed to the sold set — Won, Scheduled, Completed — and the reply names them | ✅ rule *(2026-10-03, #784 — narrowed to the Won status alone)* |
| after a list: `just the draft and sent ones` / `only the draft or review ones` / `which of those are draft, review or sent?` | the same list (and its customer), narrowed to every status in the list | ✅ rule *(2026-10-05 — wasn't a refinement at all: the reader knew one status. `followup.py` rewrites it to "… that are draft and sent", read by the list reader)* |
| after a list: `sort them by total` / `sort them by date` | the same list, highest value / newest first | ✅ rule *(2026-09-27)* |
| after a list: `what's the total of those?` / `add them up` / `how many is that?` | the combined value / the count of that list | ✅ rule *(2026-09-27)* |
| after a list's total: `does that include tax?` | the list's total the other way — every list total says which (*"…, including tax."*) | ✅ rule *(2026-10-05)* · 🤖 planner too *(2026-10-12, #905 — after a list's total it fell back)* |
| after an estimate count or list: `how many have been sold?` / `how many are won?` / `how many are on hold?` / `how many are draft and sent?` *(2026-10-05 — every status in the list; it fell through to help)* | a count by that status that keeps the customer, property, period or amount the last read was narrowed to — after "list my estimates for Bob Lee": *"You have 2 sold estimates for Bob Lee."* | ✅ rule *(2026-09-29 — the first version counted company-wide after a customer's list. `followup.py::_count_by_status`; when the last read had a status AND a scope ("how many estimates did I win this month?") the rule steps aside, since which words to swap is a guess. "how many of those are won?" narrows the list instead and is not this rule)* |
| any estimate count, list, empty list or total | the reply names everything it was narrowed by — *"You have 2 sold estimates for Bob Lee in the last year."*, *"Here are your won estimates for Bob Lee:"*, *"You don't have any sold estimates in the last month."*, *"The combined value of your 2 sold estimates in the last month is $1,500.00."* | ✅ rule *(2026-09-29 — a scoped count read as company-wide, and "show me won estimates for Bob Lee" was headed "Estimates for Bob Lee:". An unfiltered reply reads as before)* |

## 1.2 Value / total queries for a specific estimate

| Phrasing | Plan | Status |
|---|---|---|
| `what is the value of estimate {EST}?` / `what's the grand total for {EST}?` [est] | `get_estimate` field=total | ✅ |
| `what's the total for {EST}?` [est] | `get_estimate` field=total | ✅ *(closed in Phase A2)* |
| `how much is {EST}?` [est] | `get_estimate` field=total | ✅ *(closed in Phase A3)* |
| `worth of {EST}` [est] | `get_estimate` field=total | ✅ |

Handler: `_handle_get_estimate` detects `_GRAND_TOTAL_QUERY_PATTERN` and leads the response with the dollar amount.

**Questions about one estimate** *(2026-09-27, #691)* — answered from the estimate, ahead of the user-guide help that used to take them (`agents/estimate/focus_questions.py`). The estimate is named by code or title, or is the one in focus ("it", or — with no reference — the plainest shape: "what's the total?", "how much is the total?", "who's the customer?"). Plural "estimates", a work item, and how-to questions are not these.

| Phrasing | Plan | Status |
|---|---|---|
| `what's the status of {EST}?` / `is it sent?` [est] | `get_estimate` field=status | ✅ "E0001 'Oak St patio' is Draft." |
| `what's the total on it?` / `how much is {EST}?` [est] | `get_estimate` field=total | ✅ "The total on E0001 … is $1,250.00, including tax." *(2026-10-05 — the reply now says it includes tax)* |
| `what is the total value not including tax?` / `what's the total before tax?` / `how much is it before tax?` / `what's its total pre-tax?` [est] | `get_estimate` field=total before_tax | ✅ with an estimate open: each work item's total ÷ (1 + its tax %), as every "before tax" figure — *"The total on E0001 … is $1,000.00 before tax ($1,130.00 including tax)."* *(2026-10-05, user screenshot — it went to help: "I can't see the estimate figures from here". With nothing open, the same question is every estimate's total, §1.12)* |
| `who's the customer?` / `who is it for?` [est] | `get_estimate` field=customer | ✅ the contacts on its property: "… is for Ana Reyes at 12 Oak St." |
| `what's the address?` / `where is it?` [est] | `get_estimate` field=property | ✅ its property, or how to link one |
| `what's the markup on this estimate?` [est] | `get_estimate` field=markup | ✅ per work item |
| `what's the gross margin on it?` [est] | `get_estimate` field=gross_margin | ✅ per work item |
| `when was it created?` [est] | `get_estimate` field=created | ✅ the date |
| `when was {EST} last updated?` [est] | `get_estimate` field=updated | ✅ the date |
| `what's the code for this estimate?` [est] | `get_estimate` field=code | ✅ the code |
| `show me estimate {EST}` [est] | `get_estimate` | ✅ the details now include "Property: 12 Oak St — Ana Reyes" *(2026-09-27)* |
| `what is markup?` / `what's the difference between markup and gross margin?` [est] | `help` | ✅ with an estimate open, not a question about that estimate *(2026-09-30, #719 — each got the open estimate's figure. With no reference, only "it"/"this" or the plainest "what's the <field>?" is about the open estimate)* |
| `how much does mulch cost?` [est] | `list_materials` filter.text=mulch | ✅ with an estimate open, the catalog — as with nothing open, §4.12 *(2026-09-30, #719)* |
| `what's the address for bob lee?` [est] | `get_contact` field=address | ✅ with an estimate open, the contact *(2026-09-30, #719)* |
| `what's my average markup?` [est] | `metric` metric=markup | ✅ with an estimate open, the company's average markup, §1.12 *(since 2026-10-01; 2026-09-30, #719)* |
| `how much is the total?` / `what's the total including tax?` / `how much is it altogether?` [est] | `get_estimate` field=total | ✅ answered from the open estimate *(review 2026-09-30 #5 — the #719 narrowing had sent them to help. `what's the total before tax?` is too since 2026-10-05, the row above; `what's the total altogether?`, with no "it", is not about one estimate. `how much is the mulch?` / `how much is the foreman?` is a price, not the estimate's total — second review #1. `how much is E0042 in total?` is E0042's total — second review #8)* |
| `what's the status right now?` [est] | `get_estimate` field=status | ✅ answered from the open estimate *(review 2026-09-30 #5)* |
| `what's the customer's name?` [est] | `get_estimate` field=customer | ✅ answered from the open estimate *(review 2026-09-30 #5)* |
| `which estimate has the highest total?` [est] | `metric` metric=largest | ✅ the biggest estimate, not "Which estimate would you like to view?" *(2026-09-30, #720 — a ranking, average or comparison word is never about one estimate)* |
| `what's the lowest total on an estimate?` [est] | `metric` metric=smallest | ✅ *(2026-09-30, #720)* |

**Title-based lookup** *(May expansion)*: when no estimate code is found in the query, `_resolve_estimate_by_title` extracts a title from quoted text (`"Untitled Estimate"`) or `title/called/named X` phrasings and searches by substring match. Single match → returns the estimate. Multiple matches → lists them and asks the user to pick by code.

| Phrasing | Plan | Status |
|---|---|---|
| `tell me about estimate with title "Untitled Estimate"` / `show me the estimate called "Driveway Replacement"` / `pull up estimate named "Foundation Work"` [est] | `get_estimate` | ✅ |
| `show me estimate details for {EST or title}` / `show me estimate details for {title}` [est] | `get_estimate` | ✅ the response includes `created_at`, `updated_at`, the estimate ID/code, description, and notes *(2026-06-06 — `_build_estimate_details_text` now renders Created / Last updated / Description / Notes / ID lines (blank optionals omitted; core fields keep the `—` placeholder). Bare titles resolve via `TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` (`agents/estimate/title_reference.py`). **Caveat:** the linked property NAME is still not rendered — it needs an async lookup from `Estimate.property`; follow-on.)* |
| `show me everything on the {title} quote` [est] | `get_estimate` | ✅ *(2026-06-06 — verified routing; pre-noun bare-title extraction. **2026-06-09:** an explicitly-named title now beats `active_estimate_code` — viewing one estimate then asking for another by name returns the NAMED one, not the viewed one.)* |
| `give me the rundown on the {title} estimate` / `full breakdown on the {title} job` [est] | `get_estimate` | ✅ the planner handles it — was a gap: *(verified 2026-06-06: routes to `unknown` — "rundown"/"breakdown" aren't get-action cues)* |
| `what's the full info on {title}?` / `open up the {title} estimate` [est] | `get_estimate` | ✅ the planner handles it — was a gap: *(verified 2026-06-06: "full info on Spring Cleaning" **misroutes to `get_contact`** via the person-name heuristic; "open up" routes to `unknown`)* |
| `when was the {title} estimate created?` [est] | `get_estimate` field=created | ✅ the planner handles it — was a gap: *(verified 2026-06-06: **misroutes to `create_estimate`** — the word "created" trips the create-action hint. Needs a when-was/question-form guard before the create hint, then a `created_at` lead in the get handler.)* |
| `when did I last touch the {title} quote?` [est] | `get_estimate` field=updated | ✅ the planner handles it — was a gap: *(verified 2026-06-06: routes to `help`. Note the timestamps DO now appear when the user asks for the estimate's details. `when was {EST} last updated?` is answered since 2026-09-27, #691 — the table above)* |
| `what's the ID for the {title} estimate?` [est] | `get_estimate` field=code | ✅ the planner handles it — was a gap: *(verified 2026-06-06: routes to `help`)* |

**Implementation note (updated 2026-06-06):** the response-detail half of this section shipped — `_build_estimate_details_text` carries timestamps/ID/description/notes, and bare-title resolution works wherever `_resolve_estimate_by_title` is consulted. What remains is **routing** for the casual/single-field forms above (rundown / full info / open up / when-was-X / what's-the-ID): they need get-cues or a question-form guard before the create/help classifiers, plus a focused-field lead (mirroring `_GRAND_TOTAL_QUERY_PATTERN`). Both former stretch items have since landed: `bid`/`proposal` are title-extraction nouns (`TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` in `agents/estimate/title_reference.py` accept `estimate|quote|bid|proposal`), and "the Smith job" resolves as an estimate reference (2026-09-24; §1.6).

## 1.3 Generation (multi-turn, LLM-driven)

| Phrasing | Plan | Status |
|---|---|---|
| `create an estimate for {property} — needs 20 yards of concrete and two landscapers` [est] | `create_estimate` | ✅ |
| `draft a quote for a driveway replacement at 456 Oak Ave` [est] | `create_estimate` | ✅ *(2026-09-27)* |
| `I need an estimate for a new cedar fence` / `I need a quote for a new patio at 12 Oak St` [est] | `create_estimate` | ✅ any job description *(2026-09-27)* |
| `can you put together an estimate for a new cedar fence` / `can you draw up an estimate for a new cedar fence` / `can you write up an estimate for a new cedar fence` / `can you work up an estimate for a new cedar fence` / `can you prepare an estimate for a new cedar fence` / `can you price out an estimate for a new cedar fence` [est] | `create_estimate` | ✅ *(2026-09-27 — "put together …" went to get_estimate)* |
| `quote a fence for Bob Lee` [est] | `create_estimate` | ✅ *(2026-09-27 — was unknown)* |
| `create an estimate for a planting bed that is 5 feet by 15 feet with 8 boxwood and mulch. add topsoil to the install. Also as a seperate work item build a 10 by patio using Cambridge pavers.` [est] | `create_estimate` | ✅ several work items in one request, one of them described with "is" *(2026-09-28 — was a fuzzy `update_estimate` of an estimate titled like "Cambridge Paver Patio Installation"; the generation itself remains LLM-driven)* |
| `create a residential estimate` / `new commercial quote` [est] | `create_estimate` | ✅ |
| `create an estimate to plant six hydrangea at the {property} residence` [est] | `create_estimate` property | ✅ property auto-linked at creation; "six" stays a plant quantity, never an area *(2026-07-06 — property link + area grounding guard; the generation itself remains LLM-driven)* |
| `estimate for sod at {street address}` [est] | `create_estimate` property | ✅ address resolved against the Property catalog and linked *(2026-07-06 — unique match required; ambiguous/unknown falls back to the ask-to-link follow-up)* |
| `I'm here at the Smiths, make a new estimate for a cedar fence` / `create a new estimate for a cedar fence on the Johnson job` [est] | ask | ✅ *"A new estimate for the cedar fence, or the estimate you have open?"* — its own words ("start a new estimate", "the open one") and a yes answer it *(round 8)* — with an estimate open and the work planned onto it, an estimate the words may ask for is asked, never made from the words — the answer plans the request again (`as_asked.new_or_open_estimate`); an explicit reference ("on this estimate", "add it to E0042", "work item 2") keeps the work on the one open without asking *(2026-10-13, review round 5 #3; asked since round 7)* |
| `create an estimate` [none] | `create_estimate` | ✅ over the plan's included estimates with a card on file (and the notice on), the charge is asked first — the estimate pages' words — then, on the yes, "What type of work needs to be done?"; the yes carries to that request for 30 minutes and one create, and to any question the planner asks of it ("which customer?") *(2026-10-13, acceptance M4; review rounds 1–2 #2, #37)* |
| `create an estimate from this PDF` / `draft a quote from this photo` [est+quote] | `create_estimate` attach | ✅ with a photo or PDF on the message: the scope is copied from what Maple read in the file — only what the file shows, never invented — and the new estimate carries the file(s) as an estimate-level note *(Simon 2026-10-18; with files on the message, one create and nothing else taking them, the planner sets attach itself)* |
| `create an estimate from this quote and attach it` [est+quote] | `create_estimate` attach | ✅ one create: the estimate from the file's text, carrying the file as a note — a note on the step just made is folded into it, so the file is filed once (Maple attachments, 2026-10-18) |

*Not yet in the Plan format — a plan with two actions, or several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `create an estimate for a front-yard planting and set work item 2's markup to 30%` | the estimate made, then its work item 2 changed; one not on it is said | 🤖 planner *(2026-10-11, #864 — "Something went wrong partway through" after the create)* |
| any create when the company has used its plan's included estimates and has a card on file (and the user hasn't turned the overage notice off) → *"You're creating an estimate beyond the allotted number in your plan. Additional charges will apply at $3/additional estimate. Create it anyway?"* — the estimate pages' dialog, word for word → `yes` / `no` | `yes` goes on with the create (one-shot, gathered or from a template); `no` creates nothing | ✅ rule *(2026-10-03, #279 — Maple created it and billed the overage without a word, where the estimate pages show an acknowledgment dialog. Without a card the create is still refused with the add-card link.)* |

Handled by `agents/estimate/conversation_guide.py` + `agents/estimate/assumption_defaults.py`.

**Assume instead of ask (2026-07-26; sizes became per work item 2026-08-10):** generation no longer blocks on missing details. Only an unknowable **work type** still asks a question ("What type of work needs to be done?"); missing area size, material preferences, etc. are **assumed** and generation runs immediately. The area question is never asked at all.

**Sizes are resolved per work item, after decomposition.** A multi-item request used to get ONE size from a first-keyword-match over the whole message — "build a paver patio and mow the lawn" produced a 5,000 sq ft *patio*. The architect now decomposes first, then each scope missing a size resolves its own (`resolve_scope_area_assumption`), in priority order:
1. **Stated size wins** — a scope whose description carries a size ("a 400 sq ft patio", "24 by 18 ft", "a 24-by-18-foot patio", "24' x 18'", "1,200 sqft") gets **no** assumption; nothing was assumed. *(2026-10-11: sizes said with "by", with feet marks or with a thousands comma were unread — "a 24 by 18 ft. paver patio" stored the 300 sq ft default, and "1,200 sqft" read as 200. A paver's own size, "12x12 inch", is not the job's.)*
2. **Company history** — median job size parsed (`parse_job_size`) from similar past **Won-and-beyond** work items, via the per-company vector search, queried with *that scope's* text rather than the whole message (`infer_area_from_history`; needs ≥2 parseable samples). *(The corpus tightened from Sent/Approved to Won/Scheduled/Completed on 2026-08-10 — a quote nobody bought is not history.)*
3. **Curated defaults table** — `WORK_TYPE_DEFAULTS`, recalibrated 2026-08-10 against typical residential jobs: sod 2,000 sq ft, lawn/mow 5,000 sq ft, patio 300 sq ft, deck 320 sq ft, beds 800 sq ft, driveway 600 sq ft, fence 150 linear ft, wall 40 linear ft, irrigation 5,000 sq ft. Sod split out of the lawn bucket so a mow request no longer suggests sod as its material.
4. **Researcher/architect LLM fallback** — anything still invented is reported in a structured `assumptions` array (never silently guessed).

Per-item jobs (`is_discrete_item_job`) get **no** invented area. That guard now runs per scope, and its locational-phrase handling was widened 2026-08-10 so a job located by an area noun ("replace 3 shrubs **in the mulch bed**", "remove one stump **from the back lawn**") is no longer misread as area-based.

Assumptions persist on `Estimate.assumptions`, each tagged with its work item (`scope`), and the reply appends a block the user can act on — see §1.3.1 for the follow-up adjustments.

**Three important branches before generation runs** (`routers/agent_helpers/delegate_create_estimate.py`):
- **Template named → AI generation is skipped entirely** and the estimate is instantiated from the template (§6.7) — no material/activity questions.
- **Work-type decline → re-ask, not cancel.** A "No"/"skip" to the work-type question re-asks (no sensible assumption exists for *what the job is*); only an explicit cancellation ("cancel", "never mind") aborts. See `routers/agent_helpers/estimate_gathering.py` (`is_cancellation_text`).
- **Property named in the request → linked at creation** (2026-07-06). `extract_property_reference` + `resolve_property_reference` (`agents/estimate/property_reference.py`) resolve "at the {Name} residence/property/house/…" and "at {street address}" against the company's Property catalog before sufficiency assessment. Unique match → the estimate is created already linked (and the post-create follow-up moves on to the description question); ambiguous or unknown → unchanged ask-to-link flow. Explicit mention overrides the `property_id` page context. If the request detours through gathering, the resolved property rides along in the `estimate_gathering_property` context key and `_finalize_gathering` links it — and says so, as the one-shot path does: *"Created estimate 'E0042' and linked it to property 'Primavera Residence'."* (2026-10-03, #406 — the gathering path linked it silently).

**Area grounding guard** (2026-07-06, repurposed 2026-07-26): an extracted `area_measurements` whose units the user never typed is dropped (`is_area_value_grounded`) — guards against item counts becoming acreage ("plant six hydrangea" → ~~"six-acre"~~). With the area back on the missing list, Maple now **assumes** a size (history → table → LLM) instead of asking — except for per-item jobs (`is_discrete_item_job`), which get *no* invented area at all.

### 1.3.1 Assumptions & follow-up adjustments *(2026-07-26)*

When Maple assumes missing info, the creation reply ends with:

> I made a few assumptions — let me know if you'd like to adjust any:
> • Paver Patio — Area: 300 sq ft (average patio)
> • Lawn Mowing — Area: 5000 sq ft (average lawn)
> • Materials: standard pavers

Work-item assumptions are prefixed with their scope (2026-08-10) — with a size assumed per work item, bare "Area:" lines would be indistinguishable. Estimate-wide assumptions (`scope="estimate"`, e.g. materials) stay unprefixed.

Each assumption is stored structured on the estimate (`EstimateAssumption`: `key`, `label`, `assumed_value`, `unit`, `display_text`, `source` = history/table/llm/user). Follow-ups adjust them **deterministically** — no LLM regeneration:

| Phrasing | Plan | Status |
|---|---|---|
| `change the lawn to be 800 sq ft instead` [est] | `resize_work_item` size=800 | ✅ the active estimate *(deterministic routing in `OrchestratorAgent.process`, anchored on `active_estimate_code` or an explicit `{EST}` ref; shared detector `detect_assumption_adjustment` in `agents/estimate/assumption_handlers.py`)* |
| `make it 800 square feet` / `make it 800` [est] | `resize_work_item` size=800 | ✅ a bare number takes the stored size's unit, or asks it *(2026-10-12 — the unit was guessed)* |
| `the area is actually 20x30` [est] | `resize_work_item` size=600 | ✅ |
| `change the lawn to 100 square yards` [est] | `resize_work_item` size=100 size_unit | ✅ unit conversion within family *(cross-family — e.g. sq ft → linear ft — clarifies instead)* |
| `adjust the assumed area to 1000 sq ft on {EST}` [est] | `resize_work_item` size=1000 | ✅ |
| `assume premium pavers instead` [est] | `adjust_assumption` | ✅ *(material swap: re-resolves the catalog match, swaps snapshots + pricing on the lines the old assumption produced, keeps quantities)* |
| `change the lawn to 8000 sq ft` [est] | `resize_work_item` size=8000 | ✅ the estimate has both a patio and a lawn *(2026-08-10 — names the work item; only that item is rescaled)* |
| `change the second one to 8000 sq ft` [est] | `resize_work_item` size=8000 | ✅ *(2026-08-10 — positional reference, `match_positional_reference`)* |

*Several assumed sizes, two matching work items — each conversation seeds the estimate:*

| Phrasing | Plan | Status |
|---|---|---|
| `make it 800 sq ft` | conversation `ref-resize-with-two-sized-items-asks` | ✅ asks which work item — both were priced from a size Maple stored; nothing is changed *(2026-08-10; on the planner 2026-10-13)* |
| `change the lawn to 8000 sq ft` | conversation `ref-resize-two-matching-items-asks` | ✅ asks which, listing both — a Front Lawn and a Back Lawn match *(2026-08-10 — a name matching several items is ambiguous, not positional)* |

**Targeting (2026-08-10):** with a size assumed per work item, an estimate carries several `area_size` records. The one to adjust is resolved by, in order: the **work item the user named** (distinctive-word overlap against each assumption's `scope`), a **positional reference** ("the second one"), or being the **only** candidate. Genuine ambiguity **asks** rather than guessing — a wrong pick silently rewrites the wrong work item's quantities.

**Size mechanics:** factor = new ÷ stored value; **only the targeted work item's** material/labour/equipment quantities and activity effort scale by the factor (`scale_job_item`), sub-totals recompute from the scaled lines, the grand total is recurrence-aware, and the stored assumption updates to the new value (marked "(adjusted)", `source="user"`) so successive adjustments compound (500 → 800 → 1000 = 1.6× then 1.25×). Work items whose total was **manually overridden** (§1.5.8) keep the override semantics — scaled proportionally, not recomputed. Confirmation: *"I've updated the area from 500 sq ft to 800 sq ft and recalculated estimate {EST} — new grand total: $X."*

Legacy estimates created before per-item sizes carry a single `scope="estimate"` assumption that genuinely described the whole estimate — those still rescale every work item, unchanged.

**Guards:** locked statuses refuse via the standard edit loader; absurd factors (×<0.01 or >100), out-of-range positions, and cross-family unit changes clarify without mutating; estimates with **no stored assumptions** (created before this feature, or fully-specified requests) get a graceful "no stored assumptions — use the estimate editor" reply; phrasings owned by other sub-ops (work items, status, financial fields, `{size} of {material}` quantities) are never claimed by this detector.

### 1.3.2 A work item at a new size — the planner *(2026-10-11)*

A converted task, or a request that said its size, stores no assumed size — so "make the patio 1,200 sq ft" had nothing to rescale (*"I don't have any stored assumptions on estimate … to adjust"*). On the planner every new size for priced work is `resize_work_item`, and the work item it names is **repriced** (user decision 2026-10-11; `agents/estimate/work_item_reprice.py`):

- **Priced from a size Maple stored** → rescaled from it, as §1.3.1, nothing asked: *"I've repriced work item 1 for 600 sq ft (it was priced for 300 sq ft) on estimate {EST} — new grand total: $X."*
- **Anything else** (no stored size, a unit it can't convert, a change past ×100) → priced again by the generation pipeline for the new size, **asked first**: *"I'll price work item 1 ("…") on {EST} again from scratch for 1,200 sq ft. That replaces its description, materials and activities, including any changes made to them. Go ahead? (yes/no)"* — naming the estimate, so it is asked the same when the estimate in focus has gone stale. On yes the item keeps its id (its notes), position, markup, overhead, tax and division; its lines are the new pricing (a scope the pipeline split is merged back into one item); the size is stored on the item, so the next change rescales it. "No": *"Okay — I've left the work item as it is."*

| Phrasing | Plan | Status |
|---|---|---|
| `Update the patio size to 1200 sqft.` [est] | `resize_work_item` size=1200 | ✅ the patio named; just after a task convert too |
| `Recalculate the Work Items #1 for 1200 sqft patio` / `redo work item 1 for a 1200 sq ft patio` [est] | `resize_work_item` work_item.n=1 size=1200 | ✅ |
| `the patio is actually 24 by 18 ft` [est] | `resize_work_item` size=432 | ✅ 432 sq ft — no item named: the estimate's only one, or the only one priced from a size |
| `it's 20 by 30` [est] | `resize_work_item` size=600 | ✅ 600 sq ft — no item named: the estimate's only one, or the only one priced from a size |
| `make the patio bigger` [est] | ask | ✅ asks *"What size should the work item be? Say it with its unit, like "1,200 sq ft"."* — a size the message doesn't say is never the model's |
| `assume premium pavers instead` [est] | `adjust_assumption` | ✅ a material — §1.3.1 |

*Several work items, none priced from a size — the conversation seeds the estimate:*

| Phrasing | Plan | Status |
|---|---|---|
| `make it 600 sq ft` | conversation `ref-resize-with-no-sized-item-asks` | ✅ asks which work item, never the unit said with the size *(on the planner 2026-10-13: it had guessed work item 1, and asked the unit of "600 sq ft")* |

Today's pipeline is unchanged: it still rescales only an assumed size and refers the rest to the estimate editor.

## 1.4 Status transitions

EstimateStatus has 13 values (`models/estimate.py:23`): `Generating`, `Failed`, `Draft`, `Sent`, `Review`, `Won`, `Lost`, `On Hold`, `Scheduled`, `Completed`, `Approved` (legacy), `Archived`, `Deleted`. `Generating`, `Failed` and `Deleted` are internal lifecycle states, never a chat target.

**State machine + authorization enforced (2026-06-11):** every phrasing below is additionally subject to `validate_estimate_status_transition` (`models/estimate.py`, mirrors `portal/src/lib/estimateStatus.ts`) and to the HTTP layer's role gates (send/unsend → Owner/Admin; archive/unarchive → Owner/Admin or creator). A recognized phrasing whose edge is illegal for the estimate's *current* status — e.g. `mark {EST} as won` on a Draft — or that the user isn't authorized for, refuses in Maple's persona voice instead of saving. See §9.6.

**Deterministic routing (2026-06-15):** the Orchestrator now routes status-transition phrasings to `update_estimate` via a `process()` fast-path (ahead of the LLM) and a `_classify_with_rules` branch, both gated on an estimate reference + the shared `parse_status_transition` matcher (`agents/estimate/text_helpers.py`). The ✅ rows below were previously LLM-routed and routed inconsistently. **Question forms** (`Can you …?`) are claimed by the help classifier and answered with an offer to proceed — see the last two rows.

| Phrasing | Plan | Status |
|---|---|---|
| `approve {EST}` [est] | `set_status` status=Approved | ✅ the planner handles it — was a gap: *(not parsed — `approve` isn't a status verb and no rule routes it; 2026-09-27 review)* |
| `mark {EST} as approved` [est] | `set_status` status=Approved | ✅ *(2026-06-15 — `as Y` shape via `parse_status_transition`)* |
| `mark {EST} as sent` [est] | `set_status` status=Sent | ✅ *(2026-06-15 — `as Y` shape via `parse_status_transition`)* |
| `set the status for {EST} to Sent` / `set the status of {EST} to Sent` / `set the status on {EST} to Sent` [est] | `set_status` status=Sent | ✅ *(2026-06-15 — `_STATUS_TRANSITION_STATUS_REF_TO_PATTERN`; the estimate code may sit between "status" and "to". The originally-reported failing phrasing.)* |
| `archive {EST}` [est] | `set_status` status=Archived | ✅ *(2026-06-15 routing; archive/unarchive verbs are their own triggers)* |
| `unarchive {EST}` [est] | `unarchive_estimate` | ✅ *(2026-06-15 routing; archive/unarchive verbs are their own triggers)* |
| `reject the estimate` [est] | `set_status` status=Lost | ✅ there is no Rejected status: the customer said no — Lost *(was a gap: not parsed; 2026-09-27 review)* |
| `send {EST} for review` [est] | `set_status` status=Review | ✅ the planner handles it — was a gap: *(not parsed; 2026-09-27 review)* |
| `mark it as sent` / `mark {EST} sent` [est] | `set_status` status=Sent | ✅ the estimate in focus *(2026-09-27 — "it" is the estimate in focus unless a task, contact, material or role is named; "as" is optional after "mark")* |
| `mark it won` [est] | `set_status` status=Won | ✅ the estimate in focus *(2026-09-27)* |
| `archive it` [est] | `set_status` status=Archived | ✅ the estimate in focus *(2026-09-27)* |
| `place it on hold` / `put {EST} on hold` [est] | `set_status` status | ✅ On Hold, the estimate in focus or named by code *(2026-09-27; 2026-06-09 — `_ON_HOLD_PATTERN` maps bare "on hold" (with a status verb incl. `put`/`place`) to ONHOLD; guarded by `_NOTE_OR_DESC_CUE_PATTERN` so a note/description body mentioning "on hold" isn't hijacked)* |
| `send it` / `email the quote to the client` [est] | refuse `out_of_chat` `send` | 🛑 Maple never sends an estimate: create the document with the Documents button, send it, then "mark it as sent" *(2026-09-27; §9.8)* |
| `put the {title} estimate on hold` [est] | `set_status` status | ✅ the planner handles it — was a gap: for a title *(2026-09-27 review: routes to `unknown` on the rules tier; with a code or "it" it works.)* |
| `move this estimate to draft` [est] | `set_status` status=Draft | ✅ the planner handles it — was a gap: *(not parsed — `to draft` has no `status` terminator; 2026-09-27 review)* |
| `Can you set the status for {EST} to Sent?` [est] | `set_status` status=Sent | ✅ question form *(2026-06-15 — answered with "Yes — I can set {EST} to {Y} … Want me to go ahead?" + a `pending_status_transition` record; a following "yes" executes, "no" cancels. Requires an E-code + recognized target.)* |
| `update {EST or title} from Sent to Review status` [est] | `set_status` status=Review | ✅ *(2026-06-08 — `_detect_status_transition` now recognizes the `update` verb and the `from X to Y status` / `to Y status` phrasings via `_STATUS_TRANSITION_TO_STATUS_PATTERN`, anchored on the trailing `status` word so it captures the target Y. Previously fell through to "What would you like to change?". **Same change** switched the status handler to the title-aware resolver `_resolve_estimate_code_or_title`, and made an explicitly-named title override `active_estimate_code` — fixes a data-integrity bug where naming an estimate by title while viewing another updated the WRONG (viewed) estimate. **2026-06-09:** extended title-awareness to ALL estimate UPDATE + READ sub-ops — work items, work-item fields, status — via the shared `_resolve_update_estimate_code` seam and a title-aware `_load_estimate_for_read`.)* |
| `update {EST or title} to Review status` [est] | `set_status` status=Review | ✅ *(2026-06-08 — same `to Y status` pattern; works with `update`/`move`/`change`/`transition`/`switch`/`put`/`place` verbs)* |
| `what's the status of {EST}?` [est] | `get_estimate` field=status | ✅ *(2026-09-27, #691 — answered from the estimate; §1.2)* |

*Not yet in the Plan format — an answer to Maple's offer (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `yes` / `go ahead` (replying to the offer above) | `update_estimate` → Estimate Agent | ✅ rule *(`handle_pending_status_transition`, `routers/agent_helpers/pending_status_transition.py`)* |

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

| Phrasing | Plan | Status |
|---|---|---|
| `add a work item to the estimate` / `add a job item to {EST}` / `add a line item to this estimate` / `create another scope on {EST}` [wi] | `edit_estimate` | ✅ Maple asks for the new work item's name |
| `add a scope to the last estimate` [wi] | `edit_estimate` | ✅ Maple asks for the new work item's name |
| `add a work item called "Foundation Prep" to {EST}` [wi] | `edit_estimate` | ✅ |
| `change work item #1 in {EST}` [wi] | ask | ✅ asks what to change |
| `remove work item 2 from this estimate` [wi] | `edit_estimate` | ✅ |
| `delete the Driveway scope from {EST}` [wi] | `edit_estimate` | ✅ *(2026-09-27 — "scope" is a work item)* |
| `rename the scope to Foundation` [wi] | `edit_estimate` | ✅ the work item in focus; with none, Maple asks which work item ("the scope" names none) |
| `how many work items does {EST} have?` [wi] | `list_work_items` count | ✅ |
| `list the work items in {EST}` / `show me the scopes on this estimate` [wi] | `list_work_items` | ✅ |

### 1.5.2 Division assignment

Division and description are editable via chat. The seeded values come from the `EstimateDivision` enum: Design/Build, Irrigation & Lighting, Maintenance, Snow & Ice, Tree Care, Turf & Plant Care, Unassigned. Each company owns editable `Division` rows bootstrapped from that same seed (`data/default_divisions.csv`).

**How a generated work item gets its division** (2026-07-31): the estimate architect classifies each scope against the company's own divisions — names *and* the coverage description each carries — and reports a `division_confidence` with it; that value rides through research onto the work item. A high-confidence vector match to an approved past estimate donates that estimate's division instead, at full confidence. Whatever arrives is re-anchored to a division the company actually has (`apply_company_divisions`); an unrecognized or low-confidence label falls back to scoring the description against those same divisions (`routers/estimate_helpers/division.py`), then `Unassigned`.

The fallback scorer ranks evidence in tiers: **the company's own description** for a division outranks its **name**, which outranks the built-in keyword vocabulary. So a company whose "Turf & Plant Care" description reads *"fertilization, weed and pest control, aeration"* has said sod installs belong elsewhere, and the built-in `sod` keyword no longer overrules it. Division descriptions are editable in Settings → Divisions and are seeded from `data/default_divisions.csv`.

| Phrasing | Plan | Status |
|---|---|---|
| `set the division of {WI} to Maintenance` / `change the division on {WI} to Snow & Ice` / `assign {WI} to the Design/Build division` / `move {WI} to Tree Care` / `put {WI} under Irrigation & Lighting` [wi] | `edit_estimate` | ✅ |
| `what division is {WI} in?` / `which division does {WI} belong to?` [wi] | `work_item_field` field=division | ✅ |
| `which division is the patio work item in?` / `hey, what division is work item 1 in?` [wi] | `work_item_field` field=division | ✅ a question about a work item: it opens with a question word (what / which / who / whose / when / where / is / are / was / were), after at most a greeting. how / why / can / do don't count — `how do I add a work item?` is help *(2026-09-28 — the lane is `_is_work_item_question` in `agents/orchestrator/service.py`, shared by all three places that used to carry their own copy of the regex. A "?" alone never makes a question.)* |
| `how do I add a work item?` [wi] | `help` | ✅ how / why / can / do don't open a work-item question |
| `is work item 2 taxable?` [wi] | `work_item_field` field=tax | ✅ its tax rate — work items have no taxable flag *(was routes only, 2026-09-28)* |
| `are the patio work item and work item 2 in the same division?` [wi] | `work_item_field` field=division | ✅ the work items with their divisions *(was routes only, 2026-09-28)* |
| `remind me to call Bob about the patio work item, it is urgent` / `create a task: the fence work item is late` / `remind me to ask Bob what the patio work item costs` [wi] | `create_task` | ✅ a statement or request that mentions a work item and uses "is" / "which" / "what" further in routes by its own request *(2026-09-28 — any "is", "what" or "which" beside a work-item word made the message a work-item question, and all of these went to `update_estimate`)* |
| `create a task for the fence work item, which is late` [wi] | ask | ✅ a statement or request that mentions a work item and uses "is" / "which" / "what" further in routes by its own request *(2026-09-28 — any "is", "what" or "which" beside a work-item word made the message a work-item question, and all of these went to `update_estimate`)* |
| `add a contact named Ana Reyes, she is the owner, for the patio work item` [wi] | ask | ✅ routes by its own request *(2026-09-28 — it went to `update_estimate`)* |
| `create a task for the fence work item?` [wi] | ask | ✅ a request with a "?" routes by its own request *(2026-09-28 — a "?" is not a question unless the message opens with a question word)* |
| `create a property for the scope?` [wi] | ask | ✅ a request with a "?" *(2026-09-28)* |
| `create a new estimate with a patio work item?` [wi] | `create_estimate` | ✅ a request with a "?" *(2026-09-28)* |
| `set all work items in {EST} to Maintenance` [wi] | `edit_estimate` | ✅ |
| `set the division of {WI} to Special Projects` [wi] | `edit_estimate` | ✅ a division the company added or renamed *(2026-07-31 — was a ⚠️ gap earlier the same day: the handler validated against the `EstimateDivision` enum only and answered "isn't a recognized division" for a company's own rows. It now validates against the company's live divisions, canonicalizes casing/punctuation to the stored spelling, and lists the company's own divisions when it refuses.)* |
| `set the division of {WI} to Special Project` [wi] | `edit_estimate` | ✅ a near miss (missing plural, typo, leading part of the name like `snow`): asks "Did you mean Special Projects? Say yes and I'll use it."; **yes** applies it *(2026-09-24 — was a flat refusal listing every division. `closest_division_name` (`routers/estimate_helpers/division.py`) proposes the single closest division; the batch is stashed as a `sub_op="edit_commands"` confirmation with the guess substituted, so "no" cancels and nothing is written until "yes". Two about-equally-close divisions (`Care` → Tree Care / Turf & Plant Care) or nothing close keeps the refusal and its list.)* Its yes is the handler's question, answered as today *(2026-10-12 — planner only lost it)* |
| `move {WI} to Special Projects` [wi] | `edit_estimate` | ✅ a company's own division **without** the word "division" *(2026-09-27 — `move_work_item_division` takes any value and the handler checks it against the company's divisions.)* Earlier: ⚠️ gap *(2026-07-31 — the op detector (`work_item_handlers.py::_detect_work_item_field_op`) still gated on a hardcoded alternation of the seven seeded names, so a bare custom name wasn't recognized as a division op at all. Any phrasing that includes the word "division" worked for every value.)* |

### 1.5.3 Description

The rename handler already covers description updates. These phrasings extend the surface with "description"-keyword variants.

| Phrasing | Plan | Status |
|---|---|---|
| `rename {WI} to "Foundation Prep"` / `change the name of {WI} to "Driveway Installation"` / `set the description of {WI} to "Excavation and grading"` / `describe {WI} as "Remove existing pavers and re-lay"` [wi] | `edit_estimate` | ✅ |
| `update the description on {WI}` [wi] | ask | ✅ Maple asks for the new description |
| `what's the description of {WI}?` [wi] | `work_item_field` field=description | ✅ |

### 1.5.4 Recurring schedule (🛑 deferred)

`JobItem.recurring` (bool) + `JobItem.recurrence` (`RecurrenceSchedule`) control repeat billing. `RecurrenceSchedule` supports three end types: `DATE_RANGE` (start/end month+year), `TOTAL_OCCURRENCES` (fixed count), and `SPECIFIC_MONTHS` (named months across years). Currently only `month` period is supported.

| Phrasing | Plan | Status |
|---|---|---|
| `make {WI} recurring` / `set {WI} to recur monthly` / `set {WI} to repeat every month` / `make {WI} recurring from April to October` / `set {WI} to 6 occurrences` / `make {WI} recurring in April, May, June, July, August` / `change the recurrence on {WI} to 12 occurrences` [wi] | refuse `recurring` | 🛑 deferred — set it on the estimate page |
| `turn off recurring on {WI}` / `remove the recurring schedule from {WI}` / `stop {WI} from recurring` [wi] | refuse `recurring` | 🛑 deferred — clear it on the estimate page |
| `is {WI} recurring?` / `how many occurrences does {WI} have?` / `what's the recurring schedule on {WI}?` [wi] | refuse `recurring` | 🛑 deferred — the estimate page shows it |

**🛑 Deferred 2026-09-26 (user decision):** Maple no longer sets, clears or answers a work item's recurring schedule — set it on the estimate page. The `set_recurring` ported entry, its detector (`recurring_enable/disable/query`), the three handlers, their schedule parsing and the orchestrator's recurring routing rule were removed; a recurring request gets the ordinary "What would you like to change?" reply (or the edit planner's, which already treated recurrence as out of scope). The planner (Dev) says so: "I can't set, change or read a work item's recurring schedule from chat — you can see and set it on the estimate page." (`execute.RECURRING_REFUSAL_MESSAGE`). Recurrence itself — the model, templates, grand-total math, the document generator and the portal — is unchanged, and work-item details still show "Recurring: Yes/No".

### 1.5.5 Materials within a work item

`JobItem.materials` is a `List[MaterialItem]` — each entry snapshots a catalog material with quantity and price. These phrasings manage the embedded material list on a specific work item, distinct from the top-level Material catalog CRUD in §4.

| Phrasing | Plan | Status |
|---|---|---|
| `add concrete blocks to {WI}` / `add 50 concrete blocks to {WI}` / `add {material} with quantity 20 and size 12x12 to {WI}` / `remove concrete blocks from {WI}` [wi] | `edit_estimate` | ✅ |
| `add material {material} to {WI} in {EST}` [wi] | `edit_estimate` | ✅ *(2026-09-27)* |
| `add mulch to the front patio work item` [wi] | `edit_estimate` | ✅ *(2026-09-24 — multi-word work-item names before the noun)* |
| `remove all materials from {WI}` [wi] | refuse `bulk_delete` | 🛑 bulk-delete refusal — "remove all …" is a quantifier plus a delete verb (§9.1) |
| `change the quantity of concrete blocks in {WI} to 100` / `change the mulch quantity in {WI} to 8` [wi] | `edit_estimate` | ✅ *(2026-09-24 — now actually edits the line; it used to list the materials)* |
| `update the price of {material} in {WI} to $12` [wi] | `edit_estimate` | ✅ *(2026-09-24 — was misread as a set-total)* |
| `set the price of pavers to $4.25` [wi] | `edit_estimate` | ✅ no work item named: only while a work item is in focus or named; otherwise it is the catalog edit in §4. The work item holding that line is found automatically *(2026-09-24)* |
| `set the cost of {material} in {WI} to $3` [wi] | refuse `material_cost` | 🛑 a line's cost is the catalog snapshot; Maple offers price/quantity or the catalog |
| `how many materials are in {WI}?` [wi] | `list_work_item_lines` count lines=materials | ✅ |
| `what materials does {WI} have?` / `list the materials in {WI}` [wi] | `list_work_item_lines` lines=materials | ✅ |

*After a work item's lines are listed:*

| Phrasing | Plan | Status |
|---|---|---|
| `change the second one to 3 bags` | conversation `ref-a-listed-line-picked-by-position` | ✅ the planner handles it — was a gap: a work item's material and activity lists recorded no rows, so "the second one" had nothing to pick *(2026-10-07; rows recorded 2026-10-13)* |

**Disambiguation note:** `what materials does {EST} use?` (§1.1) queries all materials across all work items via the cross-resource drilldown. The phrasings above scope to a *single* work item within the estimate.

### 1.5.6 Activities within a work item

`JobItem.activities` is a `List[ActivityItem]` — each entry describes a labor task with an optional role (from the Labor catalog), rate, effort hours, and an optional effort-rate-card breakdown. Activities represent the labor component of a work item.

| Phrasing | Plan | Status |
|---|---|---|
| `add activity "Excavation" to {WI}` / `add activity "Planting" with 8 hours of effort to {WI}` / `remove the Excavation activity from {WI}` [wi] | `edit_estimate` | ✅ |
| `add an activity called "Grading" with role Landscaper to {WI}` [wi] | `edit_estimate` | ✅ *(2026-09-27)* |
| `remove all activities from {WI}` [wi] | refuse `bulk_delete` | 🛑 bulk-delete refusal (§9.1) |
| `change the role on the Excavation activity to Foreman` [wi] | `edit_estimate` | ✅ *(2026-09-24 — re-snapshots the rate and, since 2026-10-22, the role snapshot: its wage and the company's unbillable and burden %)* |
| `assign the Landscaper role to the cleanup activity` / `set the effort on the Grading activity in {WI} to 12 hours` / `make the excavation activity 6 hours` [wi] | `edit_estimate` | ✅ *(2026-09-24)* |
| `update the rate for the Planting activity to $45/hr` [wi] | `edit_estimate` | ✅ *(2026-09-24 — a hand-set rate keeps the role snapshot, so the cost basis stays the role's)* |
| `assign an effort rate card to the Excavation activity in {WI}` [wi] | refuse `out_of_chat` `rate_cards` | 🛑 redirected: the effort calculator on the activity; rate cards are in Settings *(was a gap: no chat command for rate cards)* |
| `what activities are in {WI}?` / `list the activities on {WI}` [wi] | `list_work_item_lines` lines=activities | ✅ |
| `how many activities does {WI} have?` [wi] | `list_work_item_lines` count lines=activities | ✅ |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add an activity to {WI}` → *"What's the activity called?"* → `Seeding with role Landscaper for 3 hours` | adds it to that work item | ✅ rule *(2026-09-27)* |
| … → `Remove Sod` — a name that reads as a command | adds the activity "Remove Sod" | ✅ rule *(2026-09-30, name-answers plan phase 8 — the question wasn't seen as open, and "Remove Sod" tried to delete a contact)* |

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

| Phrasing | Plan | Status |
|---|---|---|
| `set the markup on {WI} to 20%` / `put a 15% markup on it` [wi] | `edit_estimate` | ✅ "it" is the work item in focus |
| `set the profit margin on {WI} to 20%` / `change the margin on {WI} to 25%` / `I want a 30% margin on the patio work item` [wi] | `edit_estimate` | ✅ gross margin → markup |
| `set overhead allocation on {WI} to 10%` / `change the overhead on {WI} to 15%` / `set the overhead to 10%` [wi] | `edit_estimate` | ✅ with no work item named, the one in focus |
| `set tax on {WI} to 13%` / `change the tax rate on {WI} to 8.25%` [wi] | `edit_estimate` | ✅ |
| `drop the tax on {WI}` [wi] | `edit_estimate` | ✅ sets 0% |
| `set the labor burden on {WI} to 12%` / `change the labor burden on the Foundation scope to 18%` [wi] | refuse `labor_burden` | 🛑 the estimate page doesn't edit it either |
| `what's the profit margin on {WI}?` / `what's the gross margin on {WI}?` [wi] | `work_item_field` field=gross_margin | ✅ *(2026-09-24 — computed from the lines; explains a missing activity cost basis)* |
| `what's the markup on {WI}?` [wi] | `work_item_field` field=markup | ✅ *(2026-09-24)* |
| `what's the overhead on {WI}?` [wi] | `work_item_field` field=overhead | ✅ *(2026-09-24)* |
| `what's the tax on {WI}?` [wi] | `work_item_field` field=tax | ✅ *(2026-09-24)* |
| `what's the markup on E0042 work item Patio?` [wi] | `work_item_field` field=markup | ✅ the Patio work item on E0042 *(2026-10-03, #725 — the code before "work item" was read as the work item's name)* |
| `what's the subtotal of {WI}?` / `how much is {WI}?` / `what's the total for {WI}?` [wi] | `work_item_field` field=total | ✅ |

**Conceptual questions route to HELP and are answered from the users' guide** (no estimate context needed, no value reported):

| Phrasing | Plan | Status |
|---|---|---|
| `is my 10% markup the same as a 10% margin?` / `what's the difference between markup and margin?` / `what markup do I need for a 20% margin?` / `how is the profit margin calculated?` / `why is my profit margin showing a dash?` [wi] | `help` | ✅ answered from the users' guide |
| `why does labor show no profit?` [wi] | `help` | ✅ the planner handles it — was a gap: today's pipeline sends it to `get_labour` → Labour Agent |

⚠️ **`why does labor show no profit?` misroutes.** "labor" is a domain keyword,
so the classifier sends a conceptual question to the Labour agent, which tries
to look up a role. This is the general keyword-beats-concept routing problem
rather than anything specific to markup/margin, so it was left alone here.
Pinned by a strict `xfail` in `test_maple_help_coverage.py` — when routing is
fixed, that test flips red and this row gets updated.

### 1.5.8 Total amount adjustment

Sets a work item's total to an absolute dollar amount by **back-calculating its markup**, like the portal's Adjust pill (2026-09-24; it used to overwrite `sub_total`, which the next portal save recomputed from the lines and silently undid). The markup before the first adjustment is kept in `original_profit_margin`. Useful for rounding, flat-rate pricing, or manual corrections.

| Phrasing | Plan | Status |
|---|---|---|
| `adjust the total on {WI} to $1600` / `set the total for {WI} to $2500` / `change the amount on {WI} to $3000` / `round up {WI} to $2000` / `round the total on {WI} to $1500` [wi] | `edit_estimate` | ✅ |
| `make {WI} an even $5000` / `bump {WI} up to $1800` / `reduce {WI} to $1200` / `set a flat rate of $750 on {WI}` [wi] | `edit_estimate` | ✅ |

*Not yet in the Plan format — a state the test world can't build (right after an adjustment):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `set the total for {WI} to $440` after an adjustment, $440 being its total at the original markup | the adjustment is reset, as the portal's Adjust dialog does: that markup exactly, and no Adjust pill — *"I've set the total on … back to $440.00 (markup back to 10%)."* | ✅ rule *(2026-10-03, #659 — the back-calculated markup, float residue included, and the adjustment kept)* |

## 1.6 Linking

| Phrasing | Plan | Status |
|---|---|---|
| `link {EST} to {property}` [est] | `link` | ✅ *(2026-06-06 — orchestrator `_link_relationship` arm + `_LINK_VERB_TO_ESTIMATE_PATTERN`)* |
| `attach this estimate to {property}` [est] | `link` | ✅ *(2026-06-06 — "this estimate" resolves via `active_estimate_code` anaphora)* |
| `which property is this estimate for?` [est] | `get_estimate` field=property | ✅ |
| `set the property of estimate {EST} to {property}` [est] | `link` | ✅ *(the link branch `_is_property_link_request` matches `set ... property`; `_handle_update_estimate_property_link` resolves the property by name/address. **2026-07-28** — the property identifier was being extracted as `of this estimate to {property}` (the whole tail after the word "property"), so the lookup always missed; `_PROPERTY_NAME_PATTERN` now skips the estimate-qualifier preamble. **2026-07-28 (b)** — a near-miss ("primavara") now resolves fuzzily and asks for confirmation before linking.)* |
| `set the property of estimate {Estimate Name} to {property}` [est] | `link` | ✅ the estimate referenced by **title** *(2026-06-06 — all update sub-handlers resolve via the shared `_resolve_estimate_code_or_title` (code → anaphora → latest → title); bare titles are extracted by `TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` (`agents/estimate/title_reference.py`) — **first word capitalized, 2+ words** (sentence-case tails OK, bounded by a connector stop-list) adjacent to "estimate"/"quote")* |
| `this quote is for the {property} property` / `the property for this quote is {property}` [est] | `link` | ✅ *(2026-06-06 — `_LINK_RELATIONSHIP_PATTERN`; **2026-07-28** — the `the property for this quote is {X}` variant routed correctly but extracted `for this quote is {X}` as the property name, so it never resolved. Same preamble fix.)* |
| `tie the {title} quote to {property}` / `connect the {title} quote with {property}` / `associate the {title} quote with {property}` [est] | `link` | ✅ *(2026-06-06 — broadened verb set in `_LINK_PROPERTY_PATTERN` + `_LINK_VERB_TO_ESTIMATE_PATTERN` for bare property names)* |
| `assign {EST} to the {property} property` [est] | `link` | ✅ *(2026-06-06 — `assign` in `_LINK_PROPERTY_PATTERN`; deliberately NOT in the bare-name pattern, so "assign" only links when "property" or an address is present)* |
| `change the property on the {title} quote to {property}` [est] | `link` | ✅ *(2026-06-06)* |
| `set the job site for this estimate to {address}` [est] | `link` | ✅ the planner handles it — was a gap: *(routes to `update_estimate` ("job site" is a routing field token), but `_is_property_link_request` has no "job site" cue, so it falls to the generic clarification. Implementation: add a `job\s*site` alternation to `_LINK_PROPERTY_PATTERN`.)* |
| `the {title} job is at {address}` / `this estimate goes with {address}` [est] | `link` | ✅ the planner handles it — was a gap: *("the {X} job" now resolves as an estimate reference (2026-09-24, Task 8 closed), but "goes with"/"is at" aren't link cues yet)* |

**Implementation note (shipped 2026-06-06):** estimate resolution on the linking path is code → `active_estimate_code` anaphora → "latest" → bare/quoted title (shared `_resolve_estimate_code_or_title`). Property resolution is name or bare address (`_extract_property_name` / `_extract_property_address`); possessive nicknames ("Bob's place") remain a softer follow-on gap. Routing note: the orchestrator's bare link-verb arm is deliberately broad — the `_estimate_ref` gate (estimate/quote/bid/proposal/E-code) is the load-bearing guard, and the contact↔property link rules earlier in `_classify_specific_phrasings` still win for contact links.

## 1.7 Anaphora / active estimate

"This estimate" is whichever was touched most recently: the estimate open in the portal (sent every turn as `client_context.viewed_estimate`; a new page visit takes the anchor) or the last one Maple acted on. A code or name in the message always wins (2026-09-24, `routers/agent_helpers/active_estimate.py`).

| Phrasing | Plan | Status |
|---|---|---|
| `add a Landscaper to the estimate` [est] | `edit_estimate` | ✅ |
| `update the estimate` [est] | ask | ✅ Maple asks what to change |
| `show me the estimate` / `show me this estimate` [est] | `get_estimate` | ✅ *(2026-09-24 — the router's get path now reads the anchor)* |
| `add a work item called Fence` [est] | `edit_estimate` | ✅ while viewing an estimate in the portal *(2026-09-24 — the viewed estimate)* |
| `update the henderson job` [est] | ask | ✅ nothing said to change and no estimate of that name: Maple asks — never the open estimate edited. History: no estimate titled that, one is open *(2026-09-27 review: routes to `update_property` on the rules tier.)* Earlier: *(2026-09-24 — "I couldn't find … Did you mean E0042, the estimate you're working on?"; "yes" re-runs the request there)* |
| `this estimate` / `the last estimate` / `that one` [est] | `get_estimate` | ✅ resolves via `active_estimate_code` |
| `the same estimate` / `that estimate` / `the previous estimate` [est] | `get_estimate` | ✅ after a note/description/work-item edit, resolves via `active_estimate_code` *(2026-06-07 — flat-result estimate updates now persist `active_estimate_code` in `finalize_result`, so anaphora anchors on the just-edited estimate; previously these asked "Which estimate?")* |

*Not yet in the Plan format — several turns, a state no test state builds (a list just shown, no estimates at all), a record the test world lacks, a plan with two actions, or a refusal that is a resolver's answer rather than a plan (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `open the second one` (after a list of estimates) | `get_estimate` → Estimate Agent | ✅ rule *(2026-09-24)* |
| `list my estimates` → `delete the first one` (another estimate open) | deletes the first **listed** row, after confirming | ✅ rule *(2026-09-27, #686 — it offered to delete the open estimate)* |
| `mark the patio estimate as sent` → *"I found 2 estimates… which one?"* → `E0001` / `2` / `the backyard one` | the request runs on that estimate | ✅ rule *(2026-09-27, #685 — the reply dead-ended)* |
| `mark the estimate as sent` (nothing open) → *"Which estimate? … or its title."* → `Remove Sod and Reseed` / `the Oak St patio please` | the request runs on the estimate with that title — however it reads | ✅ rule *(2026-09-29, name-answers plan phase 1 — a title was read as a new request: "Remove Sod and Reseed" tried to delete a contact)* |
| … → a title two live estimates share | *"I found 2 estimates matching…"*, then the code or number picks | ✅ rule *(2026-09-29)* |
| `show me the estimate` (nothing open) → *"Which estimate would you like to view?"* → `Oak St patio` | shows it | ✅ rule *(2026-09-29 — the question wasn't remembered; the title went to the Material agent)* |
| `add a work item to the Patio estimate` (two live estimates titled Patio) | lists both, and the code or number picks | ✅ rule *(2026-09-29, #615 — "Which estimate would you like to update?" named neither)* |
| `delete the Patio estimate` (two live estimates titled Patio) | lists both and asks for the code in a new request (`delete E0042`) — a delete is never resumed from a reply | ✅ rule *(2026-09-29, #615)* |
| `delete Ana Reyes and Birch House` | one question naming both — *"Please confirm before I delete these 2:\n- contact 'Ana Reyes'\n- property 'Birch House'\nThis can't be undone."*; yes deletes both, no neither | 🤖 planner *(2026-10-11, #845 — fell back)* · ⚠️ today's |
| `show me the Patio estimate` (no estimate titled that; one titled "Pat") | *"Which estimate would you like to view?"* — never the "Pat" estimate | ✅ rule *(2026-09-29, #616)* |
| `show estimate 66f1c2…` / `delete 66f1c2…` (a database id, e.g. pasted from a portal URL) → `E0012` | *"Which estimate would you like to view? Please provide the estimate code or title."* — the id is never looked up, nor the open estimate used; the code in reply shows it | 🛑 by design *(2026-10-01, #798 — Maple never looks a record up by an id typed into the message; CLAUDE.md "Tenant scope of referenced ids")* |
| `mark task 66f1c2… done` (a database id) | *"I can't look a task up by its database id. Tell me its code (like T0042) or its title."* | 🛑 by design *(2026-10-01, #798)* · 🤖 planner too *(2026-10-12 — it asked for the id again)* |
| `what is the total of the last estimate` / `mark the last estimate as sent` with no estimates | *"You don't have any estimates yet."* | ✅ rule *(2026-09-29, #22 — it asked which estimate)* · 🤖 planner too *(2026-10-12 — it asked which estimate)* |

## 1.8 Estimate ↔ property/contact outbound drilldowns

Closed in xfail-wave-4 + 4.1 (plan: [maple-xfail-wave-4-estimate-outbound.md](plans/maple-xfail-wave-4-estimate-outbound.md)). Routes through `_CROSS_RESOURCE_QUERY_PATTERNS` with three cross-types:
- `cross_type=estimate` (Wave 4 Workstream A) — Property/Contact agents resolve the EST code via `find_estimate_by_code` and follow `Estimate.property` → `Property.contacts`.
- `cross_type=property` (Wave 4 Workstream B) — Estimate agent resolves the property via `find_properties_by_name_or_address` and constrains by `Estimate.property`.
- `cross_type=contact` (Wave 4.1) — Estimate agent resolves the contact via `find_contacts_by_full_name`, walks `Property.contacts` to a property-id set, then constrains `Estimate.property in [...]`.

| Phrasing | Plan | Status |
|---|---|---|
| `which property is this estimate {EST} linked to?` [est] | `get_estimate` field=property | ✅ the estimate's linked property *(Workstream A)* |
| `which contact is this estimate {EST} for?` / `which contact is estimate {EST} for?` [est] | `get_estimate` field=customer | ✅ estimate → property → contacts *(Workstream A)* |
| `who is this estimate {EST} for?` [est] | `get_estimate` field=customer | ✅ the reply leads with the property name as join lead-in *(Workstream A)* |
| `show me estimates for property {property}` / `estimates linked to {property}` / `what estimates are for property {property}` [est] | `list_estimates` filter.property | ✅ the property resolved by name/address, then constrained by `Estimate.property` *(Workstream B)* |
| `show me estimates for {property} property` [est] | `list_estimates` filter.property | ✅ suffix form (e.g. `Bob Residential property`): the suffix `property` strips from the captured name *(Wave 4.1 follow-up)* |
| `show me estimates for {contact}` [est] | `list_estimates` filter.customer | ✅ a capitalized name, transitive: contact → properties → estimates *(Wave 4.1)* |
| `show me estimates with the highest total` / `find estimates with the largest total` [est] | `list_estimates` sort=highest_total | ✅ the sorted list, not a material *(2026-09-29, #722 — "I couldn't find a material or role matching 'highest total'")* |
| `which estimates have been sent?` [est] | `list_estimates` filter.statuses=Sent | ✅ the estimates in that status *(2026-09-29, #723 — a material join, then every estimate)* |
| `which estimates were lost?` [est] | `list_estimates` filter.statuses=Lost | ✅ the estimates in that status *(2026-09-29, #723 — a material join, then every estimate)* |
| `show me estimates for Elm House` [est] | `list_estimates` filter.property | ✅ the planner handles it — was a gap: a property name of two capitalised words: should list its estimates; read as a contact ("I couldn't find a contact matching 'elm house'") — `show estimates for Elm House` works *(found 2026-09-29)* |

*Not yet in the Plan format — several turns, an answer to Maple's question (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| a list filter that names nothing → *"Which role / property / contact / material or role did you mean?"* → a name | the list runs with the name given — `which estimates use the Pea Gravel role?` → `Foreman`; `show me estimates for 99 Pine St` → `12 Oak St`; `show me estimates for Zed Zedson` → `Bob Lee` | ✅ rule *(2026-09-29, name-answers plan phase 7 — the question wasn't remembered, and the name was read as a request of its own)* |
| `link estimate {EST} to property 99 Pine St` → *"Which property did you mean?"* → `9 Maple Ave` | linked to 9 Maple Ave | ✅ rule *(2026-09-29, phase 7)* |
| a material swap naming no catalog material → *"Which material should I use?"* → a name | the swap runs with it | ✅ rule *(2026-09-29, phase 7)* |

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

| Phrasing | Plan | Status |
|---|---|---|
| `what's the value in the pipeline?` [est] | `dashboard` card=pipeline | ✅ |
| `what's my pipeline value in the last 30 days?` [est] | `dashboard` card=pipeline period=last_n_days days=30 | ✅ a custom window |
| `what's the backlog value?` [est] | `dashboard` card=backlog | ✅ |
| `what's my completed value?` / `how much was completed?` [est] | `dashboard` card=completed | ✅ estimates marked Completed in the last 30 days *(2026-09-30 — counts when an estimate was *marked* Completed (`status_changed_at`), with the dashboard's card: it counted Completed estimates *updated* in the window, so editing an old job put it back. Earlier: 2026-06-20 — replaced the retired "won value" headline; see change log)* |
| `what's the value of my estimates?` / `how much are my estimates worth?` [est] | `metric` metric=total | ✅ §1.12's figure over every real estimate (Lost included, as before), with calendar periods, before tax when asked, and the reply naming both *(2026-10-05, user screenshot — the dashboard's total ignored "before tax", gave the tax-inclusive figure, and read "this year" as the last 365 days: "Your estimates are worth $230,775.84 in the last year". `total value of my estimates this year before tax` without the question word is too (review #4); only a tail the metric reader can't hold — `… of the estimates I've done over the last 60 days` — stays the dashboard's below. Before: 2026-07-08 — `_analytics_total_value`: `sum(grand_total)` excluding Archived/Generating/Failed (Lost stays in — a lost bid is still an estimate); plural-only pattern so "value of estimate {EST}" stays §1.2. 2026-07-09 — yields to amount filters: "estimates worth **over $10k**" stays a `list_estimates` amount-threshold query.)* |
| `what's the total value of my estimates this year before tax?` / `total value of my estimates this year before tax` [est] | `metric` metric=total period=year before_tax | ✅ the calendar year, before tax — the reply names both *(2026-10-05, review #4 — see the row above)* |
| `what's the value of the estimates I've done over the last 60 days?` [est] | `metric` metric=total period=last_n_days days=60 | ✅ the total value over a custom window *(2026-07-08 — window bounds `updated_at`; response states the window)* |
| `give me a summary of my estimates from the last 60 days` [est] | `dashboard` card=summary period=last_n_days days=60 | ✅ windowed Pipeline/Backlog/Completed *(2026-07-08 — `_analytics_windowed_summary`: all three buckets recomputed inside the user's window; previously the window was parsed and silently discarded, so every window returned identical numbers)* |
| `what's the breakdown of estimates by statuses this month?` [est] | `metric` shape=by_status period=month | ✅ a status breakdown, §1.12 *(2026-10-06, decision 2 — every status breakdown is the metric engine's, so a division, type of work, customer, period or tax narrows it)* |
| `what's the breakdown of estimates by divisions?` [est] | `dashboard` card=by_division | ✅ |
| `breakdown by divisions last month` [est] | `dashboard` card=by_division period=last_month | ✅ the bounded previous period *(2026-07-08 — previously reported the CURRENT period; "last/previous month, quarter or year" now maps to `last_month`/`last_quarter`/`last_year`)* |
| `by divisions last year` [est] | `dashboard` card=by_division period=last_year | ✅ the bounded previous period *(2026-07-08)* |
| `by statuses last quarter` / `breakdown by statuses for the previous quarter` [est] | `metric` shape=by_status period=last_quarter | ✅ the bounded previous period *(2026-07-08 — "previous …" synonym of "last …")* |
| `breakdown by status this week` [est] | `metric` shape=by_status period=week | ✅ the metric engine's breakdown over that period, saying what it counted *(2026-10-11, #845 — fell back; today's pipeline: ⚠️)* |
| `by status all time` [est] | `metric` shape=by_status period=all_time | ✅ the metric engine's breakdown over that period, saying what it counted *(2026-10-11, #845 — fell back; today's pipeline: ⚠️)* |
| `by division over the last 7 days` [est] | `dashboard` card=by_division period=last_n_days days=7 | ✅ the breakdown over that period, saying what it counted *(2026-10-11, #845 — fell back; today's pipeline: ⚠️)* |
| `what's my pipeline all time?` [est] | `dashboard` card=pipeline period=all_time | ✅ every estimate — *"Your pipeline is worth **$X** across all time, including tax."* *(2026-10-11, #845; today's pipeline: ⚠️)* |
| `completed value all time` [est] | `dashboard` card=completed period=all_time | ✅ every estimate *(2026-10-11, #845; today's pipeline: ⚠️)* |
| `give me a summary for all time` [est] | `dashboard` card=summary period=all_time | ✅ every estimate *(2026-10-11, #845; today's pipeline: ⚠️)* |
| `what's my pipeline over the last few days?` [est] | ask | ✅ no count said: *"Over how many days?"* — never a guessed count *(2026-10-11, #845)* |
| `what is my won-lost ratio?` / `win-loss ratio` / `win/loss ratio` / `won vs lost` / `how many estimates did I win vs lose?` / `what's my win rate?` / `how am I doing on bids?` [est] | `metric` metric=win_rate | ✅ the win rate, sold (Won, Scheduled, Completed) against Lost — §1.12 *(2026-10-01, metrics Phase 3 — they were `analytics_estimates`, counting estimates still in Won, so a job left the wins when it was scheduled or completed; the window was rolling `updated_at`, now a calendar period dated by when each was sold or lost)* |
| `what's my win rate this month?` [est] | `metric` metric=win_rate period=month | ✅ the win rate for the calendar month, §1.12 *(2026-10-01, metrics Phase 3)* |
| `won vs lost status` [est] | `metric` shape=by_status rows=Won,Lost | ✅ a status breakdown (Won alone and Lost, "status" said), §1.12 *(2026-10-06, decision 2 — was the dashboard's literal count with an A:B ratio. 2026-10-01 — "status" keeps the literal statuses)* |
| `draft vs approved estimates` [est] | `metric` shape=by_status rows=Draft,Approved | ✅ a status breakdown, §1.12 *(2026-10-06, decision 2 — was the dashboard's generic pair)* |
| `compare won and lost estimates` / `is my win rate any good?` [est] | `metric` metric=win_rate | ✅ a win-loss phrasing no metric entry lists: the same win rate as §1.12 (sold against Lost); today's pipeline answers it over the dashboard's window *(2026-10-01 — it was the Won-only count)* |
| `what's my pipeline?` / `how's my pipeline looking?` [est] | `dashboard` card=pipeline | ✅ *(2026-09-27, design §7.5 — they went to the user guide)* |
| `what's in my backlog?` [est] | `dashboard` card=backlog | ✅ *(2026-09-27, design §7.5 — it went to the user guide)* |
| `how much have I completed this month?` [est] | `dashboard` card=completed period=month | ✅ *(2026-09-27, design §7.5 — it went to the user guide)* |
| `what's my pipeline before tax?` / `pipeline before tax` [est] | `dashboard` card=pipeline before_tax | ✅ the card's figure before tax; every card, total and summary says which — *"Your pipeline is worth **$X** in the last 90 days, before tax."* A summary before tax counts each card over its own window from the engine. A breakdown by status or division stays tax-inclusive and says so *(2026-10-05 — "before tax" was ignored and no figure said whether it included tax; the anchored summary, dashboard and bare-card forms took no tax phrase at all — review #2. Their results now come back whole, so "does that include tax?" / "what about before tax?" work after them too)* |
| `what's the backlog value not including tax?` [est] | `dashboard` card=backlog before_tax | ✅ the card's figure before tax, and says so *(2026-10-05, review #2)* |
| `give me a summary before tax` / `show me my dashboard before tax` / `how's business before tax?` [est] | `dashboard` card=summary before_tax | ✅ each card over its own window from the engine, before tax, and says so *(2026-10-05, review #2)* |
| `show me my dashboard` / `give me a summary` / `how's business?` [est] | `dashboard` card=summary | ✅ Pipeline / Backlog / Completed *(2026-09-27 — they were unknown or help. A summary of one estimate — "give me a summary of E0042" — is not this.)* |
| `how many estimates are in each status?` [est] | `metric` shape=by_status measure=count | ✅ a status breakdown, §1.12 *(2026-10-06, decision 2. 2026-09-27 — "in each status" counted all estimates)* |
| `pipeline by status` / `estimates by status` [est] | `metric` shape=by_status | ✅ a status breakdown, §1.12 *(2026-10-06, decision 2)* |
| `estimate value by division` [est] | `dashboard` card=by_division | ✅ the breakdown by division *(2026-09-27 — "by division" was unknown)* |
| `what is my pipeline worth` / `hey maple, what's in the pipeline?` / `can I see my pipeline?` / `pipeline` / `whats my pipeline` [est] | `dashboard` card=pipeline | ✅ *(2026-09-30, #721 — a pipeline/backlog question opens with a question or show word after at most a lead, or is the bare noun. Review 2026-09-30 #4: "whats", "which", "is/are my/our" and "I'd like to see" open one too — "whats my pipeline" went to the Material agent. "is the pipeline trench on the estimate?" / "are the pipeline fittings included?" are not metrics — second review #6)* |
| `how big is my backlog?` / `backlog?` / `i'd like to see my backlog` [est] | `dashboard` card=backlog | ✅ *(2026-09-30, #721 — as above)* |
| `which estimates are in my backlog?` [est] | `list_estimates` filter.statuses | ✅ the backlog's estimates — Won and Scheduled, the card's statuses *(2026-10-14, review round 13 #39 — it was the card, which gives a count and a value but not which; the planner listed the pipeline's statuses until the prompt named the backlog's)* |
| `is my pipeline growing?` [est] | `metric` shape=comparison | ✅ this month against the last *(2026-09-30, #721 — as above)* |
| `rename work item 2 to the pipeline trench` / `remove the pipeline flush activity from work item 2` [est] | `edit_estimate` | ✅ the command — never analytics *(2026-09-30, #721 — they routed to `analytics_estimates` and nothing was written. A message the estimate grammar parses is never a metric, and "pipeline"/"backlog" mid-sentence is an ordinary word)* |
| `add a note to this estimate: locate the pipeline before digging` [est] | `add_note` | ✅ the note — never analytics *(as above; an estimate's note is `add_note`, review round 13 #39)* |
| `what are my recent estimates?` / `show me my most recent estimates` [est] | `list_estimates` sort=latest | ✅ the newest 8 — the dashboard's Recent Estimates *(2026-09-27 — help, or one row for a plural ask)* |
| `show me recent draft estimates` [est] | `list_estimates` sort=latest filter.statuses=Draft | ✅ the same, with that status *(2026-10-02, #724 — a word or two between "recent" and the noun cut the list to one row, "Your latest estimate:")* |
| `my latest sent quotes` [est] | `list_estimates` sort=latest filter.statuses=Sent | ✅ the same, with that status *(2026-10-02, #724)* |
| `my recent won estimates` [est] | `list_estimates` sort=latest filter.sold | ✅ the same, sold (Won, Scheduled, Completed) — a bare "won" *(2026-10-02, #724)* |
| `show me the last two estimates` [est] | `list_estimates` sort=latest limit=2 | ✅ that many, newest first *(2026-10-02 — one to ten in words, as digits; "the last few estimates" is the newest 8. "estimates from the last two weeks" stays a date range, never two rows)* |
| `my three most recent estimates` [est] | `list_estimates` sort=latest limit=3 | ✅ that many, newest first *(2026-10-02)* |
| `show me my latest estimate for 153 Ashroken Ave` [est] | `list_estimates` sort=latest limit=1 filter.property | ✅ the sorted list, its lead-in naming everything it was narrowed by — *"Your latest estimate for 'Primavera':"* — a fuzzily matched property above all *(2026-10-03, #437 — "Your latest estimate:" dropped the status, division, customer and the property a fuzzy address resolved to)* |
| `my highest draft estimate for Bob Lee` [est] | `list_estimates` sort=highest_total limit=1 filter.statuses=Draft filter.customer | ✅ the sorted list, its lead-in naming the status and the customer *(2026-10-03, #437)* |
| `my 3 most recent estimates in Hardscape` [est] | `list_estimates` sort=latest limit=3 filter.division=Hardscape | ✅ the sorted list, its lead-in naming the division *(2026-10-03, #437)* |
| `how is the backlog value calculated?` / `what does pipeline value mean?` / `how is the completed value calculated?` [est] | `help` | ✅ *(2026-06-20 — explanatory/definitional phrasing about a metric routes to HELP, not a value lookup. `_match_analytics_query` now redirects a recognized metric phrased with an explanatory cue (`calculated`/`computed`/`defined`/`mean`/…) to help; `calculated`/`computed` also added to `HELP_INSTRUCTIONAL_PATTERNS` for metrics without an analytics keyword.)* |

*Not yet in the Plan format — several turns, an answer to Maple's question (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `check the pipeline under the driveway` / `we cleared our backlog of pavers` as a reply to Maple's question | the answer to the question | ✅ rule *(2026-09-30, #721 — read as a new analytics request, which dropped the question)* |
| `what's my pipeline?` → `and last month?` | the same question for last month | ✅ rule *(2026-09-27 — a read that named no period takes the new one, §10.8; it became a material lookup)* |

**Status comparisons / ratios:** a win rate is a metric question (§1.12, `maple_metrics.run_win_rate`) since 2026-10-01, and every status breakdown — literal pairs included — since 2026-10-06 (decision 2). The rule tier no longer reaches what follows; the LLM classifier still can: `compute_status_comparison` counts each status for a literal pair ("won vs lost status", "draft vs approved") — all-time unless a date window is given, in which case it constrains `updated_at` — and `format_status_comparison` renders a reduced `A:B` ratio (with a win-rate percentage for the literal Won/Lost pair). A win-loss phrasing that reaches this handler without "status" is answered with §1.12's win rate.

**Time windows:** Pipeline/backlog/completed headline queries respect user-specified date ranges via `_parse_estimate_date_filter`, in two shapes: **word qualifiers** ("this month", "last week", "past quarter") via `_DATE_RANGE_FILTER_PATTERN`, and **numeric windows** ("last 90 days", "past 6 months", "last 2 weeks") via `_NUMERIC_DATE_RANGE_PATTERN`. *(2026-06-21 — the numeric form was previously unparsed: "completed value for the last 90 days" silently fell back to the 30-day default and answered "in the last 30 days". `_NUMERIC_DATE_RANGE_PATTERN` (`(last|past) <N> day|week|month|quarter|year`) now resolves it to a real window; `_describe_date_window` reports the exact day count ("in the last 90 days") for any span that isn't a canonical named period. Since 2026-10-06 (review round 2 #2) a counted window is the figures' rolling window — "past 6 months" is since the same date six months ago, "the last 2 years" two years (each unit capped by `time_windows._CAPS`, not one year) — and names itself: "in the last 6 months". Tests: `test_maple_phrasing_expansion.py::TestNumericDateRangeFilter`, `test_dashboard_backlog_parity.py`.)* When no date qualifier is present, the handler falls back to default windows: **pipeline = 90 days, completed = 30 days, backlog = all-time (no recency window)**. An all-time backlog answer reads "… in total" rather than "… in the last N days". *(2026-07-08 — the generic summary and the new total-value metric are window-aware too: `_analytics_windowed_summary` recomputes Pipeline/Backlog/Completed inside an explicit window, and `_analytics_total_value` sums non-archived `grand_total` over the window (all-time when none). Both state the window in the response. Age phrasings now include "N days **or older**".)* Breakdown queries use the `period` parameter passed to `compute_analytics`: the current "month"/"quarter"/"year" or — since 2026-07-08 — the bounded previous "last_month"/"last_quarter"/"last_year" (matched from "last …"/"previous …" phrasings before the bare substring checks, since "last month" contains "month").

**Status sets and dates must mirror the dashboard cards** — both read `services/maple_metrics.py` since 2026-09-30, so they can't drift; Completed is dated by `status_changed_at` (marked Completed in the last 30 days), Pipeline by `updated_at`, Backlog all-time. (`compute_analytics` in `routers/estimates.py`): pipeline = `[DRAFT, SENT, REVIEW, WON]`, **backlog = `[WON, SCHEDULED]` (all-time)**, **completed = `[COMPLETED]` (last 30 days)**. *(2026-06-20 — fixed a parity bug where the chat backlog headline summed only `[WON]`, so Maple reported $0.00 while the dashboard showed the real figure. `_analytics_headline_value` in `crud_handlers.py` now includes SCHEDULED.)* *(2026-06-20 — backlog relaxed from last-30-days to **all-time** in both `compute_analytics` and `_analytics_headline_value`: backlog = every Won/Scheduled estimate regardless of recency; dashboard card now labeled "All time".)*

## 1.10 Estimate-level field edits (title, description & notes)

These edit **top-level `Estimate` fields** (`title`, `description`) — distinct from the work-item (`JobItem`) description edits in §1.5.3. **Notes phrasings no longer write an `Estimate` field**: as of 2026-09-23 they file a real estimate-level `Note` on the Notes feed (section 9.6 of the user guide) via `_handle_add_estimate_note`; `Estimate.notes` itself has no writer left in Maple. Routing is `update_estimate` → Estimate Agent; the dispatcher is `_handle_update_estimate` (`crud_handlers.py:2786`).

| Phrasing | Plan | Status |
|---|---|---|
| `rename {EST} to {new title}` / `retitle this estimate as {new title}` [est] | `edit_estimate` | ✅ *(2026-07-30 — `_detect_estimate_title_update` + `_handle_update_estimate_title`. Before this the chain had NO title branch: `rename` existed only as a **work-item** op, so an estimate-level rename fell through to the capability-list clarification.)* |
| `rename it to {new title}` [est] | `edit_estimate` | ✅ the pronoun target resolves via `active_estimate_code` |
| `change the title of this estimate to {new title}` / `set the title of this estimate to {new title}` / `change the name of this quote to {new title}` [est] | `edit_estimate` | ✅ *(2026-07-30)* |
| `for estimate {EST}, add to the notes the following: "{text}"` [est] | `add_note` | ✅ *(`_detect_note_update` → `_handle_add_estimate_note`; files a real estimate-level `Note` via `create_note_as`, added to the Notes feed (section 9.6) — `Estimate.notes` is never touched, and the note ignores the Draft/Review edit lock. 2026-06-07 — the quoted body is captured in full even with an apostrophe inside (`"Contact me if there's any issues"`); straight + curly, double + single quotes via the shared `QUOTED_VALUE_GROUP` (`agents/estimate/text_helpers.py`). 2026-09-23 — Option C.)* |
| `set the notes on {EST} to "{text}"` / `update notes: {text}` [est] | `add_note` | ✅ the planner handles it — was a gap: *(2026-09-27 review: routes to `unknown` on the rules tier.)* Earlier: *(same handler; 2026-09-23 — "set"/"replace" phrasing is still recognized but now **adds** a note rather than overwriting anything, since a Notes feed only ever grows)* |
| `for estimate {Estimate Name}, add to the notes the following: "{text}"` [est] | `add_note` | ✅ the estimate referenced by **title** *(2026-06-06 — notes handler resolves via the shared `_resolve_estimate_code_or_title`; bare titles extracted by `TITLE_PRE_NOUN_RE`/`TITLE_POST_NOUN_RE` — first word capitalized, 2+ words (sentence-case OK) near "estimate"/"quote". The bare-title patterns run **before** the any-quoted fallback so a quoted note body is never mistaken for the title.)* |
| `add a note to the {title} quote: "{text}"` [est] | `add_note` | ✅ *(2026-06-06)* |
| `update the description of estimate {EST} with the following: "Front and back yard cleanup"` [est] | `edit_estimate` | ✅ *(2026-06-06 — `_detect_estimate_description_update` + `_handle_update_estimate_description` set the top-level `Estimate.description`; quoted, colon, and unquoted `to ...` value forms supported, incl. an E-code sitting between the keyword and the connector)* |
| `set the description of estimate {EST} to "Front and back yard cleanup"` / `change the estimate description to "Front and back yard cleanup"` [est] | `edit_estimate` | ✅ *(2026-06-06)* |
| `change the description on the {title} quote to "Front and back yard cleanup"` / `reword the description on this estimate to "Front and back yard cleanup"` [est] | `edit_estimate` | ✅ *(2026-06-06 — title via bare-title extraction; "this estimate" via anaphora)* |
| `update the write-up for {EST} to "Front and back yard cleanup"` / `update the overview for {EST} to "Front and back yard cleanup"` [est] | `edit_estimate` | ✅ *(2026-06-06 — `write-up`/`overview` are description-cue synonyms)* |
| `put "Front and back yard cleanup" as the overview for the estimate` [est] | `edit_estimate` | ✅ the planner handles it — was a gap: *(value-**before**-cue word order — the extractors expect the cue before the value; needs a `put "X" as the description/overview` pattern)* |
| `describe the {title} estimate as "Front and back yard cleanup"` / `the description for the {title} job should be "Front and back yard cleanup"` [est] | `edit_estimate` | ✅ the planner handles it — was a gap: *(`describe ... as` and `... should be` shapes have no extractor; "the {X} job" also isn't an estimate reference)* |
| `make a note on {EST} that the gate code is 4411` / `leave a note on {EST}: "{text}"` [est] | `add_note` | ✅ *(2026-09-24 — `is_note_add_request` routes them and `_NOTE_TARGETED_LEAD_IN` extracts the `... that X` body.)* *(historical, corrected 2026-06-06: the routing verb list lacked `make`/`leave`/`tack`, so these never reached the agent on a fresh turn; "make a note ... that X" additionally needed a generic `note ... that` tail extractor (only `remember ... that` existed).)* |
| `tack a note onto the {title} quote: "{text}"` [est] | `add_note` | ✅ the planner handles it — was a gap: *(`tack` is still a gap: the routing verb list lacks it, so it never reaches the agent on a fresh turn. Reachable today only when the orchestrator already routed to `update_estimate` for another reason.)* |
| `note on the {title} job: {text}` [est] | `add_note` | ✅ the planner handles it — was a gap: *(verbless + "the {X} job" isn't an estimate reference — Task-8 stretch)* |
| `jot down on the {title} estimate: "{text}"` / `remember on this estimate that the gate code is 4411` / `FYI on the {title} job: "{text}"` [est] | `add_note` | ✅ with an estimate/quote token *(2026-06-06 — informal cues `jot`/`fyi`/`remember`/`write down` in `_NOTE_UPDATE_CUES` + value extractors (`_NOTE_WITH_COLON_SEP` broadened, new `_NOTE_REMEMBER_TAIL`); routed end-to-end by the orchestrator's value-bearing `_informal_note` arm. 2026-09-23 — always **adds** a `Note` to the estimate's Notes feed; `Estimate.notes` is untouched. Note: the phrase still needs an estimate/quote/EST token — "the Smith job" alone doesn't reference an estimate.)* |
| `create a note for this estimate: {text}` / `create a note on {EST}: {text}` / `make a note on this estimate that the gate code is 4411` / `new note for this quote: {text}` [est] | `add_note` | ✅ an estimate-level Note *(2026-09-24 — was `create_estimate`. `create a note for this work item: …` files a work-item Note.)* |
| `Add a note that says: {text}` / `add a note: {text}` / `create a note: {text}` / `leave a note that the gate code is 4411` / `add note - {text}` [est] | `add_note` | ✅ **no target at all**, estimate in play: an estimate-level Note, even with a work item anchored *(2026-09-24 — was `create_estimate`: "add" plus the borrowed estimate domain read as a create)* |
| `write down on the {title} estimate that the gate code is 4411` [est] | `add_note` | ✅ the planner handles it — an estimate's note (review round 13 #39) — was a gap: *(`write down` is a cue, but only `remember` has a `... that ...` tail extractor; needs the tail generalized)* |
| `add this plan to the estimate` / `attach this quote to {EST}` / `put this photo on E0042's notes` [est+quote] | `add_note` attach | ✅ with a photo or PDF on the message (or the previous one): an estimate-level note with the file(s), signed by you, on the Notes feed (Maple attachments, 2026-10-18) |
| `add this photo to work item 2` / `attach this to the patio work item` [est+photo] | `add_note` parent.domain=work_item attach | ✅ with words, the note is added without the file; with none, nothing is written; either way the reply says why — a work item's note takes files on the estimate page (`WORK_ITEM_NOTE_FILES_REFUSAL`) (Maple attachments, 2026-10-18; review 2026-10-19). The model often plans the work item's note as an edit command, with the command copied in as its text ("Add this photo.") or none: `as_asked_files.work_item_files_refused` makes that the refusal, and an edit with words of its own says the file isn't on it *(live run 2026-10-20)* |

*Not yet in the Plan format — a refusal that depends on the estimate's status (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| Renaming a **locked** estimate (Sent / Approved / Archived / Won / Completed …) | Refused | 🛑 refusal *(2026-07-30 — the handler resolves through `_load_estimate_for_update`, so the Draft/Review edit-lock covers the title exactly like description and work-item edits. Locked means locked for every content edit; notes are exempt — since 2026-09-23 they are `Note`s outside the lock.)* |

**Title-vs-target trap (2026-07-30):** the rename handler must resolve its target from the message **head**, never the raw query. `_resolve_estimate_code_or_title` treats the bare word "title" as an explicit name cue (`TITLE_BARE_RE`), so `change the title of this estimate to Patio Rebuild` would otherwise hunt for an estimate literally named *"of this estimate to Patio Rebuild"*, miss, and refuse instead of falling back to the active estimate. `_detect_estimate_title_update` returns `(new_title, target_text)` for exactly this reason. Two exclusions run against that **head**, never the new value (an estimate may legitimately be titled "Scope of Work"): a work-item noun in the head (`rename the patio work item|scope to X`) leaves the message to the work-item op, and a *qualified* name field (`set the name **of the property** on {EST} to X`) leaves it to the property-link branch — without that second guard the value was silently written into `Estimate.title` instead.

**Disambiguation note:** `set the description of {WI} to "..."` (§1.5.3) targets a **work item** and is already ✅ rule. The phrasings here target the **estimate as a whole** — the implementation must detect the absence of a work-item reference (no `work item` / `job item` / `scope` / `line item` token) to route to the estimate-level handler rather than the work-item one.

**Implementation note (shipped 2026-06-06; notes behavior changed 2026-09-23):** all update sub-handlers (description / notes / property-link) resolve the estimate by **code → `active_estimate_code` anaphora → "latest" → quoted-or-bare title** via the shared `_resolve_estimate_code_or_title`. The verb (`set`/`change`/`replace`/`overwrite`/`rewrite` + note vs. everything else, incl. all informal cues) still selects a "mode," but as of 2026-09-23 (Option C) every mode **adds** a `Note` via `_handle_add_estimate_note` → `create_note_as` — nothing ever writes `Estimate.notes` again, and the note ignores the Draft/Review edit lock. Dispatcher order in `_handle_update_estimate`: work-item ops → status → **description** → notes → property link → template (description sits above notes so a "description" cue never lands in the notes branch; work-item ops stay first so `description of {WI}` is untouched). **Remaining ⚠️ in this section:** value-before-cue (`put "X" as the overview`), `describe ... as` / `should be`, routing verbs `make`/`leave`/`tack`, a generalized `note ... that` tail, and "the {X} job" as an estimate reference (Task-8 stretch).

---


## 1.11 Multi-turn work-item conversation *(2026-09-24)*

Work items have no names, only a description and a position, so Maple keeps
three kinds of memory (`agents/estimate/work_item_context.py`): an anchor on
the last work item resolved (by its stable `JobItem.id`), the list it last
showed, and the question it last asked.

| Phrasing | Plan | Status |
|---|---|---|
| `add a note to work item 2: check drainage` / `note on this work item: check drainage` [wi] | `edit_estimate` commands=add_work_item_note | ✅ files a work-item Note (outside the edit lock) |
| `add a note to work item 2 about drainage` / `add a note to work item 2 regarding the gate` [wi] | `edit_estimate` commands=add_work_item_note | ✅ files "about drainage" on work item 2 *(2026-09-27, #684 — it filed "to work item 2 about drainage" on the estimate)* |
| `On work item 1, add a note: check drainage` [wi] | `edit_estimate` commands=add_work_item_note | ✅ files it on work item 1 *(2026-09-27, #665)* |
| `add a note to that estimate saying call the client` / `drop a note on {EST} saying call the client` / `new note for this estimate saying call the client` [wi] | `add_note` | ✅ files the estimate note *(2026-09-27, #664 — these asked where the note should go)* |
| `set the markup on all work items to 20%` / `set the markup for work items 1 and 2 to 20%` [wi] | `edit_estimate` | ✅ not a listed command: the edit planner's. Without it, Maple asks what to change ("… What would you like to change?") and writes nothing *(corrected 2026-09-27 — the "one work item at a time" reply no longer exists)* |
| `remove work item 1 and set the markup on work item 2 to 20%` [wi] | `edit_estimate` | ✅ the edit planner types both; without it, Maple asks what to change and writes nothing *(corrected 2026-09-27 — the "one change at a time" reply no longer exists)* |
| `also raise the markup by 5%` / `change the markup by 5%` [wi] | `edit_estimate` | ✅ a relative change isn't a listed command: the planner's. Without it, Maple asks what to change; a change BY 5 is never applied as the new value *(corrected 2026-09-27 — the "What should the new markup be?" reply no longer exists)* |
| `add a work item Fence and raise its markup by 5%` [wi] | `edit_estimate` | ✅ the new work item at the company's default markup plus 5% *(2026-10-11, #867 — it set 5%)* |
| `create a task to set the markup to 20%` [wi] | `create_task` | ✅ not an estimate edit; nothing is written to the estimate |
| `don't drop the markup on work item 2` [wi] | `acknowledge` | ✅ not an estimate edit; nothing is written — left as it is *(2026-10-11, #847 — it set the markup to 0)* |
| `add 500 sq ft of sod to E0001` [wi] | `generate_work_item` | ✅ prices the scope into E0001 (never a new estimate) |
| `set the tax on the lawn work item on the patio job to 13%` / `remove work item 1 from the patio job` [wi] | `edit_estimate` | ✅ the work item the message names, not the patio one |
| `rename the patio work item on the Smith estimate to Back Patio` [wi] | `edit_estimate` | ✅ renames the work item; never retitles the estimate |
| `add a task to follow up on E0042` [wi] | `create_task` | ✅ creates the task; E0042 is not priced |
| `set the price of mulch to $5` [est_then_mat] | `update_material` fields.price | ✅ the material opened last, not the estimate left earlier |
| `the pavers on the front patio actually cost us $3.50 now` [wi] | refuse `material_cost` | 🛑 the material-cost refusal; a cost is never written as the price |
| `set the overhead lighting work item's markup to 20%` [wi] | `edit_estimate` | ✅ sets the markup on "Overhead lighting" — a field word in a name is never the field |
| `reduce the markup 5%` / `raise the tax 2%` [wi] | `edit_estimate` | ✅ the planner's, as above; without it Maple asks what to change and writes nothing — a change BY 5 is never applied as the new value *(corrected 2026-09-27)* |
| `why is the markup 20%?` [wi] | `work_item_field` field=markup | ✅ not an edit; nothing is written |
| `i think the markup of 20% is too high` [wi] | ask | ✅ not an edit; nothing is written |
| `set the hours on the overhead pruning activity to 6` [wi] | `edit_estimate` | ✅ edits the activity's hours; "overhead" is part of its name |
| `rename the grading activity to Rough Grade` [wi] | `edit_estimate` | ✅ renames the activity — "I've updated activity "Rough Grade" on "Patio": renamed from "Grading"." *(Simon, 2026-10-10)*; today's Maple says "I can't rename an activity from chat yet". Never retitles the estimate |
| `add a work item Patio, add 10 pavers to it` [wi] | `edit_estimate` | ✅ the pavers go on the new Patio work item |
| `generate a work item for installing 200 sq ft of pavers` / `add a scope for installing 200 sq ft of pavers and price it` [wi] | `generate_work_item` | ✅ runs the estimate pipeline for that scope and appends it (15–30 s) |
| `show work item #1` [wi] | `get_work_item` | ✅ description, division, materials, activities, markup/overhead/tax, gross margin, sub-total |
| `we'll need twelve dozen pavers after all and the customer is tax exempt` [wi] | `edit_estimate` | ✅ anything else about an open estimate that no rule recognizes: the edit planner proposes typed commands; validated against the estimate and applied all-or-nothing |

*Not yet in the Plan format — several turns, an answer to Maple's question, a record the test world lacks, the user's role, a plan with two actions, or a plan not yet decided (phase 3):*

| Phrasing (turn by turn) | What happens | Status |
|---|---|---|
| `show work item #2` → `rename it to Patio lights` | the rename lands on #2 (the anchor), even if items were reordered | ✅ rule |
| `list the work items` → `delete the second one` | removes the 2nd row shown (asks to confirm first) | ✅ rule · 🤖 planner: the removal's yes/no is the handler's, answered as today *(2026-10-12 — planner only lost the yes)* |
| `list the work items` → `rename the fifth one to X` (only 3 listed) | "I only listed 3 work items — which one did you mean?" | ✅ rule |
| `rename the patio work item to X` → *(two patios)* → `2` / `the front one` | the menu answer resumes the rename on that item | ✅ rule · 🤖 planner: the work items listed, a number picks one *(2026-10-12 — asked with no list)* |
| `add a work item` → *"what should I call it?"* → `Retaining wall` | creates it and anchors it | ✅ rule · 🤖 planner: asked in today's words *(2026-10-12 — the model made up a name)* |
| `update the description of work item 2` → *"what should it be?"* → `Patio string lights` | sets it | ✅ rule |
| `rename work item 3 to X` → *"which estimate?"* → `E0042` | resumes on E0042 | ✅ rule · 🤖 planner: a code answers its "which estimate?" *(2026-10-12 — read as a new request)* |
| `add a note to the patio work item` → *"What should the note say?"* → `check the grade` | files the reply as a note on the patio work item | ✅ rule · 🤖 planner: asked, never a blank note *(2026-10-12)* |
| `lower the tax on Patio by 15%` (from 13%) | *"That would make the tax on "Patio" -2%, and it has to be between 0% and 100%. I've left it at 13%."* | 🤖 planner *(2026-10-11, #845 — "Something went wrong partway through")* |
| `if we set the markup to 20% …` | not an estimate edit; nothing is written | ✅ rule |
| `delete work item 1 and …` → *question* → `Yes` | a bare yes/no never repeats a delete from the chat history | ✅ rule |
| `list the work items` → `rename the second one to Front Patio Scope` | renames that work item; a work-item word in the new name doesn't stop the pick, and an ordinal rename never retitles the estimate | ✅ rule |
| `list the work items` → `add a note to the second one: check the line item` | files the note on the second work item | ✅ rule |
| `rename the patio work item to X` → *(menu)* → `set the markup on work item 1 to 15%` / `show me the 2nd estimate` | a new request, not a menu pick; only a bare pick answers the menu | ✅ rule |
| `update the description on work item 2` → *"what should it be?"* → `cancel` / `no` / `never mind` | "No problem, I've left it as is." — nothing is written | ✅ rule |
| `update the description on work item 2` → *"what should it be?"* → `list my estimates` / `show me estimate E0004` | the question is dropped and the request runs | ✅ rule |
| `add Bob as the contact on E0042` | creates the contact; E0042 is not priced. The planner (Dev) links Bob to E0042's property — an estimate's customer is its property's contact — or says E0042 has no property yet | ✅ rule · 🤖 planner |
| `rename the patio work item to X` → *(menu "Add mulch beds / Remove stump")* → `Remove stump` | picks that row — a row's own description is always a pick | ✅ rule · 🤖 planner: the menu listed, its name picks *(2026-10-12)* |
| `update the description on work item 2` → `Show homeowner the revised quote before starting` | sets it as the description | ✅ rule · 🤖 planner: asked as text, so a reply that reads like a command is the description *(2026-10-12 — it was lost)* |
| `add a note to the patio work item please` → *"What should the note say?"* → `gate code 1234` | filed on the patio work item | ✅ rule · 🤖 planner: asked, never a blank note *(2026-10-12)* |
| *(menu open)* → `delete all work items` / `add equipment to the patio` | the bulk-delete / equipment refusal — an open question never takes them | 🛑 refused |
| *(material or contact opened last)* → `set the markup to 25%` | goes to that record's agent, not the estimate left earlier | ✅ rule |
| `delete estimate E0042` → `confirm` (Member, not the creator) | "Only the estimate's creator or an Owner can delete …" — the Delete button's rule | 🛑 refused |

*Live run 2026-10-19, G31 ([gap plan](plans/2026-10-19-maple-phrasing-gaps-plan.md)):* in the acceptance conversation `safety-stale-delete-not-replayed`, the stray `yes` on turn 3 was planned as the delete from turn 1 again (asked first, so nothing was deleted) in both conversation runs. Fixed the same day: a bare yes, ok or no with nothing asked never plans a write (`as_asked_reads.stray_yes_writes_nothing`) — Maple says she isn't waiting on an answer.


*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `set the markup on the patio job to 20%` | conversation `ref-markup-on-a-work-item-said-as-a-job` | ✅ the planner handles it — was a gap: "the patio job" names the Front patio pavers work item; today's rules tier routed it to `unknown` *(2026-09-27 review; 2026-10-13)* |

**Edit planner guardrails** (`agents/estimate/edit_planner.py`): runs only
after the estimate is resolved and editable; at most 5 commands; every
work-item target must exist in the snapshot it was shown or the whole plan is
rejected; it cannot name another estimate (it says `different_estimate`);
reads get the capability message; removals still ask for confirmation.
Disabled by `MAPLE_EDIT_PLANNER_ENABLED=false` (the test suite's default).

**Open gaps:** older #23, #354 (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #663, #664, #665, #666, #668, #670, #671, #673, #677, #682, #683, #684, #685, #686, #687, #689, #691, #696, #697, #334, #436; #22, #439, #615, #616 on 2026-09-29; #569, #783, #784, #785, #786, #787, #406, #437, #614, #631, #279, #617, #645, #659 on 2026-10-03.

## 1.12 Metrics — totals, averages, the biggest, rankings, by month, comparisons, win rate, margin and markup *(2026-09-30)*

Plan: [`plans/2026-09-30-maple-metrics-and-next-batch-plan.md`](plans/2026-09-30-maple-metrics-and-next-batch-plan.md).
Grammar entries `analytics_metric` (`command_grammar._METRIC_ENTRIES`), read
by `agents/estimate/metric_query.py`, answered by
`agents/estimate/metric_answers.py` from `services/maple_metrics.py` — the
engine the dashboard reads too. Every number is computed by the database,
never by the LLM, and every reply names what it counted.

**How it reads a question**

- **Won and sold are the same set** — Won + Scheduled + Completed (decision
  8): a job the customer said yes to, whatever came after. "Made", "spent",
  "revenue" and "sales" mean it too, and so does "won" in a count or a list
  (#784). "Status won" said outright — *with status won*, *won status*, *in
  Won status*, *status is won*, *currently won* — is the literal status,
  wherever it sits in the question (it was read only at the end: "total of
  estimates with status won" counted every estimate).
- **Several statuses are one set** (2026-10-05): *on Draft, Review, and Sent
  estimates*, *draft and sent*, *draft or review* — every status in the list,
  in a total, an average, a ranking, by month, a comparison, a margin or
  markup, or a line total, and the reply names each one counted. "Won" in a
  list is still the sold set. Statuses said where a name would stand count as
  statuses — one needs its noun (*for draft estimates*), a list does not. A
  win rate defines its own statuses, so a status said with it is said back as
  unread, and so are two different statuses in two places (*top 3 properties
  by draft value for sent estimates*) — neither is dropped. "Vs" still compares; *the total value of my draft and sent
  estimates* is the list's total, as with one status. It read the list as a
  customer: *"I couldn't find a customer, property or division called Draft,
  Review, and Sent."*
- **Money is tax-inclusive** (the estimates' `grand_total`, as the dashboard);
  *before tax*, *pre-tax*, *excluding*, *not including*, *without*, *ex*,
  *less*, *minus* or *net of tax*, *tax excluded* sums each work item's
  `sub_total ÷ (1 + tax%)`; *including*, *with*, *incl.*, *plus tax*, *tax
  included* is the default said outright. The reply says which. One reading
  for every reader — metrics, the dashboard's cards, a list's total, one
  estimate's total — in `agents/estimate/tax_words.py` (2026-10-05). *After
  tax* is neither, and is said back. A total with tax said and nothing named
  (*what is the total value not including tax?*) is every estimate's — user
  decision 2026-10-05 — unless an estimate is open, when it is that one's.
- **The last figure's tax** (2026-10-05): *does that include tax?* / *is that
  before tax?* re-runs the last money read with tax the other way, after
  *"That included tax. Here it is before tax:"*; *what about before tax?* /
  *and with tax?* re-runs it the way asked
  (`agents/conversation/tax_followup.py`). After a count, a margin or nothing,
  Maple says how tax works instead.
- **Periods are calendar periods on the user's clock**: *this month* is since
  the 1st where they are; *last quarter* is the previous one; *in the last 90
  days* starts at that day's midnight. *The last / past N weeks, months,
  quarters or years*, in digits or words (one to twelve), roll back to the
  same date that many units ago — *the last six months* on Oct 6 is since
  April 6 (user decision 2026-10-06; `agents/estimate/time_windows.py`,
  `metric_periods.last_n`). A time frame Maple can't read (*the last
  fortnight*, *the past few months*) is said back, never looked up as a name. With *won* / *sold* a period reads when
  the estimate was sold (`sold_at`); with another status, when it moved there
  (`status_changed_at`); with none, when it was created. An estimate from
  before those dates existed is placed by `updated_at` — and a sale from then
  is dated once, on its next move within the sold set, so Won → Scheduled →
  Completed can't carry it from month to month.
- **Scopes combine** (user 2026-10-06): a division said with the estimates
  (*my Maintenance estimates*), a status with it (*my won Maintenance
  estimates*), a customer or property after it (*… for Bob Lee*), a time
  frame and a type of work, in one question. The reply names each one; none
  is dropped — a division and a customer was answered for the customer across
  every division. A division that isn't one, or two different divisions, is
  said back.
- **Type of work** (user 2026-10-06): *recurring* or *one-time* work counts
  only those work items, every visit of a recurring one (decision 3), like a
  division and with one (`MetricQuery.recurring`, `maple_metrics.work_clause`).
  Counts and lists give the estimates that have such work.
- **An amount** (reference run 2026-10-14): the model writes it as said —
  *over*, *at least*, *under*, *at most* (`schema_fields.Amount`), *between
  $1k and $5k* as over and under, *five grand* as 5000 — on the action it
  belongs to: a list's total or a material's price, a refinement (*only the
  ones over $1000*), a follow-up (*what about Elm House over 2000?*, which
  replaces the list's amount), a figure or a card. No amount is read from the
  words by a pattern (Simon 2026-10-14). A figure has none, so *the total of
  my draft estimates over $1000* or *how many … under $500* is the estimate
  list's total or count over it, with its status, kind of work, period and
  tax (`as_asked.amount_is_a_lists_total`); on what no list holds — an
  average, a win rate, a card, a customer's, property's or division's
  figure, a year, *since*, *excluding* — it is said back, never summed over:
  *"I can't narrow that figure by an amount yet. …"*
  (`unread_scope.amount_unread`). Beside another request, that request runs
  and the figure is said back above its reply.
- **By status** (user 2026-10-06, decision 2): *Maintenance estimates by
  status for the last six months*, *draft vs sent vs won vs lost for
  Maintenance*, *won vs lost status*, *how many estimates are in each
  status?* — a row per status with its count and value, then the total; only
  the statuses said when they are listed (*Sent: none* for one with none).
  Every status breakdown is the engine's (`run_status_totals`, summed from the
  work items when a division, type or *before tax* narrows it), all time
  unless a period is said, dated by when each estimate was created so the
  rows compare. *Won* is the sold set unless *status* is said with the list.
  *Won vs lost* alone is still the win rate.
- **Who or what it is about**: a customer (every property they are on, each
  once), a property by name or street, a division, or the record in focus —
  *this property*, *them*, *it*. *My* / *our* / nothing is the whole company,
  even with a record open. *He* / *she* / *they* is the customer in focus. A
  part of a name counts only as whole words of it ("Lee" is Bob Lee, "Carl" is
  no one), never a record's name inside what was said. A name that matches
  several asks which; one that matches nothing says so. Two records with one
  name — two customers called Dana Wu — are counted together; a customer and
  a property with one name are offered as *"Birch Hollow (customer)"* /
  *"Birch Hollow (property)"*; the one picked — by its text, its number or
  "the customer" — answers every question shape (#785). A full address ("12
  Oak St, Toronto") names its property, but a city or province alone names
  none (#786); "in total" / "overall" after a name is all
  of it, not part of the name.
- **A scope the choices can't hold is never guessed**: *excluding Elm House*,
  *since January*, *in 2025* are not read as a name — the rules step aside and
  the LLM tier reads the question or declines it; declined (or off, as in
  tests), the reply says what it can't narrow by instead of a wider figure. A
  name with such a word in it ("Between the Pines", "Bob Till") is still a
  name. The LLM tier's subject must be words of the message.
- **Recurring work items** count every occurrence, as the estimate's total
  does.
- **Rankings** *(Phase 2)* rank customers, properties or divisions — by sold
  value unless a status is said, by count for "the most estimates", ties by
  value then name; 5 rows unless a number is said (at most 25). A customer is
  every property they are on, so a shared property counts for each.
- **By month** *(Phase 2)* lists every month of the period on the user's
  clock — this year unless one is said — $0 where nothing counted.
- **Comparisons** *(Phase 2)* put this week, month, quarter or year against
  the last, like with like: on Sept 15, Sept 1–15 against Aug 1–15; "all of
  last month" compares the whole month. Both units must match.
- **Win rate** *(Phase 3)* is sold ÷ (sold + Lost), counting estimates
  (decisions 8, 14): sold is Won + Scheduled + Completed, dated by when it was
  sold; Lost by when it was lost. Open estimates aren't in it, and one won
  then lost counts once, as a loss. A customer, property, division and period
  apply as to a total; a status said doesn't change what a win is. Ranked, by
  month or compared, it is answered — each row its own win rate (Simon
  2026-10-13, reversing decision 18); by value only when asked.
- **Gross margin and average markup** *(Phase 3)* are sold work unless a
  status is said (decision 15) — "on lost estimates", "in Won status". Each
  work item is priced from its lines as the estimate page prices it, every
  occurrence of a recurring one counted, and the dollars are summed: margin =
  profit ÷ pre-tax selling price (overhead deducted, tax left out), markup =
  markup dollars ÷ subtotal (decision 17), so with materials at price and
  labor at its Rate the company's margin is its markup ÷ (1 + markup), as on
  one work item. A work item with an activity that has no cost rate is left
  out and the reply says how many (decision 16). "On Bob Lee's jobs" / "on
  Landscaping work" name whose work it is. Ranked, by month or compared, they
  are answered — each row its own dollars summed, never an average of percents
  (Simon 2026-10-13, reversing decision 18).

| Phrasing | Plan | Status |
|---|---|---|
| `what's the lifetime won amount from 12 Oak St?` [est] | `metric` metric=total status=won subject | ✅ *"Won value for 12 Oak St, all time: $5,000.00 across 2 estimates (Won, Scheduled, Completed), including tax."* |
| `what's the lifetime won amount for this property?` [property_focus] | `metric` metric=total status=won subject | ✅ the property in focus — the same figure for it |
| `how much have I sold to Bob Lee this year?` [est] | `metric` metric=total status=sold subject period=year | ✅ the customer's sold total for the calendar year, across every property they are on |
| `how much have they spent with us?` / `how much has he spent?` / `how much has she spent?` [contact_focus] | `metric` metric=total status=sold subject | ✅ the customer in focus — their sold total, across every property they are on *(review 2026-09-30 #8 — "he" searched every name containing "he")* |
| `how much did I win last quarter?` [est] | `metric` metric=total status=sold period=last_quarter | ✅ the company's sold total for the period |
| `how much have we sold this month?` [est] | `metric` metric=total status=sold period=month | ✅ the company's sold total for the period |
| `what's our revenue this year?` [est] | `metric` metric=total status=sold period=year | ✅ the company's sold total for the period |
| `how much did we sell before tax this year?` [est] | `metric` metric=total status=sold period=year before_tax | ✅ the company's sold total for the period, before tax |
| `how much did we sell over the last year` [est] | `metric` metric=total status=sold period=last_year | ✅ the company's sold total for the period *(the last read "over" as a customer — Grover Smith — review 2026-09-30 #1)* |
| `what's the total value of won estimates for Bob Lee?` [est] | `metric` metric=total status=won subject | ✅ the customer's total |
| `what is the won value for Bob Lee last month?` [est] | `metric` metric=total status=won subject period=last_month | ✅ the customer's total |
| `how much is still in draft for Elm House?` [est] | `metric` metric=total status=draft subject | ✅ that status's total |
| `how much is on hold?` [est] | `metric` metric=total status=on_hold | ✅ that status's total |
| `what's the value of my Landscaping work?` [est] | `metric` metric=total subject=Landscaping | ✅ that division's work items only |
| `what's the average estimate value?` [est] | `metric` metric=average | ✅ |
| `what's the average value of my won estimates?` [est] | `metric` metric=average status=won | ✅ *"The average won estimate is $1,750.00, across 4 estimates (Won, Scheduled, Completed), including tax."* |
| `what's Bob Lee's average job size?` [est] | `metric` metric=average subject | ✅ |
| `what's my biggest estimate?` / `which estimate has the highest total?` [est] | `metric` metric=largest | ✅ *"Your biggest estimate is E0042 'Patio' at $3,000.00 (Completed, including tax)."* *(the last was the sorted list, #720)* |
| `what's my smallest won job?` [est] | `metric` metric=smallest status=won | ✅ |
| `what was the largest estimate for 12 Oak St last year?` [est] | `metric` metric=largest subject period=last_year | ✅ |
| `how much have I sold to Ana?` [est] | `metric` metric=total status=sold subject=Ana | ✅ two Anas — *"Which one did you mean: Ana Lopez or Ana Reyes?"* |
| `how much have I sold to Dana Wu?` [est] | `metric` metric=total status=sold subject | ✅ two customers called Dana Wu — both, each property once *(review 2026-09-30 #9 — "Which one did you mean: Dana Wu?" asked again after every answer)* |
| `what's our revenue excluding Elm House` | conversation `ref-revenue-excluding-a-place` | ✅ the planner handles it — was a gap: the customer's or property's estimates left out, and the reply says so — *"Sold value excluding Elm House, all time: …"*; in a ranking, by month, a comparison, a ratio or a quantity it is said back *(2026-10-13)* |
| `how much have I made since January` | conversation `ref-revenue-since-january` | ✅ the planner handles it — was a gap: from the latest January 1st to now — *"since Jan 1"*; a day still to come is said back *(2026-10-13)* |
| `how much have I made in 2025` | conversation `ref-revenue-in-a-year-by-its-number` | ✅ the planner handles it — was a gap: that calendar year on the user's clock — *"in 2025"*; a year still to come, or one beside a comparison's own periods, is said back *(2026-10-13; before: the LLM tier's; without it, *"I can't narrow a total by "since January" yet. I can narrow it by customer, property or division; …"* — "an average" / "the biggest estimate" / "a win rate" for those questions (#787, 2026-10-03) *(review 2026-09-30 #1 — the first answered FOR Elm House; "since January" and "in 2025" were looked up as names. Second review #2: the fallback was the company-wide dashboard figure)*)* |
| `what's the lifetime won amount for Between the Pines?` / `what's the lifetime won amount from 12 Oak St, Toronto?` [est] | `metric` metric=total status=won subject | ✅ that property's total *(second review 2026-09-30 #3, #4, #7)* |
| `how much have I sold to Elm House in total?` [est] | `metric` metric=total status=sold subject | ✅ that property's total — "in total" is all of it, not part of the name *(second review 2026-09-30 #3, #4, #7)* |
| `how much have I made from Guelph?` / `how much have I made from ON?` [est] | `metric` metric=total status=sold subject | ✅ *"I couldn't find a customer, property or division called Guelph."* — a city or province alone names no property *(2026-10-03, #786 — every property in the city matched, an unbounded "which one?")* |
| `what's the total for Smith?` [est] | `metric` metric=total subject=Smith | ✅ an estimate titled Smith, no customer or property of that name — *"I couldn't find a customer, property or division called Smith, but E0042 'Smith' is an estimate: $1,234.00 including tax (Won)."* *(2026-09-30 gap — it was help, then read as a customer or property named Smith: an estimate title was not a metric subject. 2026-10-03, #783 — said only that no customer was called Smith)* |
| `what's the total for Smith?` [est] | `metric` metric=total subject=Smith | ✅ two estimates titled Smith — *"I couldn't find a customer, property or division called Smith, but 2 estimates are titled Smith."* — a Deleted one is never counted or named *(2026-10-03, #783 review — named whichever came back first)* |
| `how much have I sold to Zed Zedson?` [est] | `metric` metric=total status=sold subject | ✅ *"I couldn't find a customer, property or division called Zed Zedson."* |
| `how much have I sold to Carla Diaz?` [est] | `metric` metric=total status=sold subject | ✅ no property — *"Carla Diaz has no sold estimates (Won, Scheduled, Completed)."* |
| `what has Bob Lee bought from us over the years?` [est] | `metric` metric=total status=sold subject | ✅ a phrasing no grammar entry reads — the classifier picks `analytics_metric`; a worker model fills the same fixed choices (`agents/estimate/metric_spec.py`, fenced, usage-tagged `orchestrator.metric_spec`) and the engine answers *(task 13 — off in tests; "not a metric" falls back to the dashboard answers. Coverage matrix `metrics_paraphrase`. Since Phase 2 task 9 the model also picks a ranking, by month or a comparison, as fixed choices; a ranking of nothing or a comparison with a second period is declined. Since Phase 3 task 8 it also picks a win rate, gross margin or average markup — one asked as a ranking, by month or compared is answered since 2026-10-13, keeping the shape's rows, size and unit; a comparison with nothing or too much to compare is declined)* |
| `which job this year brought in the most money?` [est] | `metric` metric=largest period=year | ✅ a phrasing no grammar entry reads *(task 13)* |
| `who's been my most valuable client over the years?` [est] | `metric` metric=total shape=ranking by=customer limit=1 | ✅ a phrasing no grammar entry reads *(task 13)* |
| `who are my top 5 customers by won value?` [est] | `metric` metric=total shape=ranking by=customer limit=5 status=won | ✅ a numbered ranking — *"Your customers by sold value, all time (Won, Scheduled, Completed), including tax:\n1. Ana Reyes — $5,000.00 across 2 estimates\n2. Bob Lee — $2,000.00 across 2 estimates"*; 5 rows unless a number is said (at most 25), "That's 1–5 of 12 — say "show more" for the next 5." when there are more; a property two customers share counts toward each, and the reply says so *(Phase 2, 2026-09-30 — they were help or unknown. Sold value unless a status is said, decision 9)* |
| `who is my best customer?` [est] | `metric` metric=total shape=ranking by=customer limit=1 | ✅ one row for a singular — "Your top customer by sold value, all time, is Ana Reyes — …" *(Phase 2)* |
| `show me my top 10 customers` [est] | `metric` metric=total shape=ranking by=customer limit=10 | ✅ *(Phase 2)* |
| `which property has the most estimates?` [est] | `metric` metric=total shape=ranking by=property measure=count limit=1 | ✅ "the most estimates" ranks by count, ties by value *(Phase 2)* |
| `which division earns the most?` [est] | `metric` metric=total shape=ranking by=division limit=1 | ✅ *(Phase 2)* |
| `who spent the most this year?` [est] | `metric` metric=total shape=ranking by=customer limit=1 period=year | ✅ *(Phase 2)* |
| `what's my sales by month this year?` / `how much did I sell each month this year?` [est] | `metric` metric=total shape=by_month status=sold period=year | ✅ every month of the period on the user's clock, $0 where nothing sold, and the total — *"Sold value by month this year (Won, Scheduled, Completed), including tax:\n- Jan 2026: $0.00\n…\n- Sept 2026: $7,000.00 across 4 estimates\nTotal: $7,000.00 across 4 estimates."* *(Phase 2 — sold value unless a status is said; this year unless a period is)* |
| `value by month this year` [est] | `metric` metric=total shape=by_month period=year | ✅ sold value, no status said *(Phase 2)* |
| `show me monthly sales for last year` [est] | `metric` metric=total shape=by_month status=sold period=last_year | ✅ *(Phase 2)* |
| `how does this month compare to last month?` / `this month vs last month` [est] | `metric` metric=total compare=month | ✅ both figures, the days each covers, and the change — *"Sold value, Sept 1–15: $12,400.00 across 6 estimates. Aug 1–15: $9,800.00 across 5 estimates. Up $2,600.00 (+27%). Counting Won, Scheduled, Completed, including tax."*; like with like unless "all of last …" (decision 11); no percent from nothing ("Up $7,000.00 from nothing.") *(Phase 2 — sold value unless a status is said, decision 10. Never two statuses — `won vs lost` / `draft vs approved` stay the dashboard's, §1.9 — nor two units: `this month vs last quarter`. A period in the tail as well — `this month vs last month this year` — is said back, not guessed: *"A comparison already names both periods — ask again without "this year"."* On the first day of a period the days read "Sept 1", not "Sept 1–1"; a flat comparison in cents reads "No change.")* |
| `sold this quarter vs last quarter` [est] | `metric` metric=total status=sold compare=quarter | ✅ *(Phase 2)* |
| `am I up on last year?` [est] | `metric` metric=total compare=year | ✅ this year against last year, like with like *(Phase 2)* |
| `how am I doing compared to last year?` [est] | `metric` metric=total compare=year | ✅ this year against last year, like with like *(Phase 2)* |
| `how does this year compare to all of last year?` [est] | `metric` metric=total compare=year whole | ✅ against the whole of last year (decision 11) *(Phase 2)* |
| `top 5 customers in won status` [est] | `metric` metric=total shape=ranking by=customer limit=5 status=literal_won | ✅ Won only, as for a single figure *(Phase 2 review #1 — each counted the whole sold set)* |
| `sales by month in won status` [est] | `metric` metric=total shape=by_month status=literal_won | ✅ Won only, as for a single figure *(Phase 2 review #1 — each counted the whole sold set)* |
| `this month vs last month in won status` [est] | `metric` metric=total compare=month status=literal_won | ✅ Won only, as for a single figure *(Phase 2 review #1 — each counted the whole sold set)* |
| `sales by month for all time` [est] | `metric` metric=total shape=by_month status=sold period=all_time | ✅ the planner handles it — was a gap: every month since the first sale on today's rules *(Phase 2 review #10 — it was refused)*; on the planner a figure per month whose period is all time (the default) is this year (`metric_spec.ask_from_spec`), so "for all time" answers this year |
| `value by month ever` [est] | `metric` metric=total shape=by_month period=all_time | ✅ the planner handles it — was a gap: every month since the first sale on today's rules *(Phase 2 review #10 — it answered this year)*; on the planner it answers this year again, as the row above |
| `what's my win rate?` / `won vs lost` / `how many estimates did I win vs lose?` / `how am I doing on bids?` / `what is my won-lost ratio?` / `how's my win rate looking?` / `what's our close rate?` [est] | `metric` metric=win_rate | ✅ *"Your win rate, all time, is 80%: 4 sold (Won, Scheduled, Completed) against 1 Lost, a 4:1 win-loss ratio. Open estimates aren't counted."* *(Phase 3, 2026-10-01 — they were the dashboard's count of estimates still in Won, §1.9)* |
| `what's my win rate this month?` [est] | `metric` metric=win_rate period=month | ✅ *(Phase 3, 2026-10-01)* |
| `wins vs losses this year` / `win rate this year` [est] | `metric` metric=win_rate period=year | ✅ *(Phase 3, 2026-10-01)* |
| `what's the win rate for Bob Lee?` / `win rate for Elm House` [est] | `metric` metric=win_rate subject | ✅ *"The win rate for Bob Lee, all time, is 67%: 2 sold … against 1 Lost, a 2:1 win-loss ratio. …"* *(Phase 3 — the customer is every property they are on)* |
| `what's Bob Lee's win rate this year?` [est] | `metric` metric=win_rate subject period=year | ✅ *(Phase 3)* |
| `what's my win rate last year?` [est] | `metric` metric=win_rate period=last_year | ✅ nothing sold or lost — *"Nothing was sold or lost last year, so there's no win rate yet."* *(Phase 3 — not 0%)* |
| `which customer has the best win rate?` / `who has the best win rate?` / `what's my win rate by customer?` [est] | `metric` metric=win_rate shape=ranking by=customer | ✅ each customer's own win rate, counting estimates, best first — a tie goes to the one with more decided; open estimates aren't counted *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `win rate by month` [est] | `metric` metric=win_rate shape=by_month | ✅ each month its own win rate — all time from the first month with anything unless a period is said; a month with nothing sold or lost says so *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `how does my win rate this month compare to last month?` / `my win rate this year vs last year` [est] | `metric` metric=win_rate shape=comparison | ✅ both periods' win rates, like with like, and the change in points *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `what's my gross margin?` / `what's my profit margin?` / `what's our overall margin?` / `how much margin am I making?` [est] | `metric` metric=margin | ✅ *"Gross margin on sold work, all time: 31.8% — $700.00 of profit on $2,200.00 of pre-tax selling price, across 4 estimates (Won, Scheduled, Completed). Overhead is deducted; tax is left out. 1 work item is left out: an activity on it has no cost rate."* *(Phase 3, 2026-10-01 — they were help)* |
| `what's my gross margin this year?` [est] | `metric` metric=margin period=year | ✅ *(Phase 3, 2026-10-01 — it was help)* |
| `how's my margin looking this quarter?` [est] | `metric` metric=margin period=quarter | ✅ *(Phase 3, 2026-10-01 — it was help)* |
| `what's the gross margin for Bob Lee?` / `what margin am I making on Bob Lee's jobs?` [est] | `metric` metric=margin subject | ✅ that customer's work *(Phase 3)* |
| `what's my margin on Landscaping work?` [est] | `metric` metric=margin subject=Landscaping | ✅ that division's work *(Phase 3)* |
| `what's my gross margin on lost estimates?` [est] | `metric` metric=margin status=lost | ✅ that status's work *(Phase 3)* |
| `what's my average gross margin on Draft, Review, and Sent estimates?` [est] | `metric` metric=margin statuses=Draft,Review,Sent | ✅ the figure over every status in the list, named back — *"Gross margin on draft, review and sent work, all time: … across 14 estimates (Draft, Review, Sent)."* *(2026-10-05 — the list was looked up as a customer: "I couldn't find a customer, property or division called Draft, Review, and Sent.")* |
| `what's my gross margin on draft or sent estimates?` [est] | `metric` metric=margin statuses=Draft,Sent | ✅ the figure over every status in the list, named back *(2026-10-05)* |
| `what's my average estimate value for draft and sent estimates?` [est] | `metric` metric=average statuses=Draft,Sent | ✅ the figure over every status in the list, named back *(2026-10-05)* |
| `top 3 properties by draft and sent value` [est] | `metric` metric=total shape=ranking by=property limit=3 statuses=Draft,Sent | ✅ the ranking over every status in the list, named back *(2026-10-05)* |
| `draft and sent value by month` [est] | `metric` metric=total shape=by_month statuses=Draft,Sent | ✅ every month over every status in the list, named back *(2026-10-05)* |
| `draft and sent this month vs last month` [est] | `metric` metric=total compare=month statuses=Draft,Sent | ✅ the comparison over every status in the list, named back *(2026-10-05)* |
| `how much Black Mulch is in my draft and sent estimates?` [est] | `metric` metric=line_total line_name statuses=Draft,Sent | ✅ the quantity over every status in the list, named back *(2026-10-05)* |
| `what's my win rate on draft and review estimates?` [est] | `metric` metric=win_rate statuses=Draft,Review | ✅ says back that it can't narrow a win rate by them — a win rate defines its own statuses *(2026-10-05)* |
| `what's my average markup?` [est] | `metric` metric=markup | ✅ *"Average markup on sold work, all time: 29.4% — $500.00 of markup on $1,700.00 of subtotal, across 4 estimates (Won, Scheduled, Completed), weighted by each work item's subtotal."* *(Phase 3 — they were help; weighted by cost, decision 17)* |
| `what's my average markup this year?` [est] | `metric` metric=markup period=year | ✅ *(Phase 3 — it was help)* |
| `what's the average markup for Elm House?` / `what's Bob Lee's average markup?` [est] | `metric` metric=markup subject | ✅ that property's or customer's work *(Phase 3 — they were help)* |
| `what's my gross margin last year?` [est] | `metric` metric=margin period=last_year | ✅ no sold work — *"There's no sold work last year to measure a gross margin on."*; when every work item has an unpriced activity — *"There's no gross margin to give on sold work: every work item in it has an activity with no cost rate (3 work items)."* *(Phase 3 — not 0%)* |
| `which customer has the best margin?` [est] | `metric` metric=margin shape=ranking by=customer | ✅ each customer's gross margin on sold work, dollars summed — never an average of percents *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `what's my gross margin by month?` [est] | `metric` metric=margin shape=by_month | ✅ *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `markup by division` [est] | `metric` metric=markup shape=ranking by=division | ✅ each division's average markup, weighted by subtotal *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `how does my margin this year compare to last year?` [est] | `metric` metric=margin shape=comparison | ✅ *(Simon 2026-10-13: answered — decision 18 had said it back)* |
| `what's my markup?` [est] | `get_estimate` field=markup | ✅ with an estimate open, its markup; with none, the default markup is a setting (Settings) — ask "what's my average markup?" for the figure *(Phase 3 — deliberately not read as the average)* |
| `what's work item 2's margin?` / `what's the patio work item's gross margin?` [est] | `work_item_field` field=gross_margin | ✅ not a metric — the work item's figure (§1.5.7) *(Phase 3 review #1, #3, 2026-10-01 — the possessive was read as a customer: "I couldn't find … called work item 2")* |
| `what's this estimate's gross margin?` / `what's E0042's gross margin?` [est] | `get_estimate` field=gross_margin | ✅ not a metric — the one estimate's *(Phase 3 review #1, #3, 2026-10-01)* |
| `what's this estimate's win rate?` [est] | `get_estimate` | ✅ not a metric — the one estimate's *(Phase 3 review #1, #3, 2026-10-01)* |
| `what's my win rate on bids?` [est] | `metric` metric=win_rate | ✅ the whole company's figure *(Phase 3 review #2 — "bids", "all", "my" were looked up as names; the last since Phase 1)* |
| `what's my gross margin on all estimates?` [est] | `metric` metric=margin | ✅ the whole company's figure *(Phase 3 review #2)* |
| `what's my average markup on my jobs?` [est] | `metric` metric=markup | ✅ the whole company's figure *(Phase 3 review #2)* |
| `how much have I sold on all my estimates?` [est] | `metric` metric=total status=sold | ✅ the whole company's figure *(Phase 3 review #2 — "all my estimates" was looked up as a name since Phase 1)* |
| `what is the total value of my Maintenance Estimates for the last six months?` [est] | `metric` metric=total subject=Maintenance period=last_n_days days=6 window_unit=month | ✅ *"Total value of Maintenance work in the last 6 months: $2,595.00 across 4 estimates, including tax."* *(2026-10-06, user screenshot — "I couldn't find a customer, property or division called the last six months.")* |
| `what's the total value of my won Maintenance estimates for Bob Lee in the last 6 months?` [est] | `metric` metric=total status=won work=Maintenance subject period=last_n_days days=6 window_unit=month | ✅ every scope at once — *"Won value of Maintenance work for Bob Lee in the last 6 months: $1,130.00 across 1 estimate (Won, Scheduled, Completed), including tax."* *(2026-10-06 — the division was dropped beside a customer; "won Maintenance" and "recurring" were looked up as names)* |
| `what's the value of my recurring Maintenance work?` [est] | `metric` metric=total subject=Maintenance recurring | ✅ every scope at once *(2026-10-06)* |
| `how much recurring work did we sell last quarter?` [est] | `metric` metric=total status=sold period=last_quarter recurring | ✅ every scope at once *(2026-10-06)* |
| `Maintenance estimates by status for the last six months` [est] | `metric` metric=total shape=by_status subject=Maintenance period=last_n_days days=6 window_unit=month | ✅ *"Maintenance estimates by status in the last 6 months, including tax:\n- Draft: 1 estimate, $565.00\n- Sent: 1 estimate, $600.00\n- Won: 1 estimate, $1,130.00\n- Lost: 1 estimate, $300.00\nTotal: 4 estimates, $2,595.00."* *(2026-10-06, decision 2 — the dashboard's breakdown ignored the division)* |
| `draft vs sent vs won vs lost for Maintenance` [est] | `metric` metric=total shape=by_status rows subject=Maintenance | ✅ a row per status said; Won is the sold set *(2026-10-06, decision 2)* |
| `won vs lost status for Bob Lee before tax` [est] | `metric` metric=total shape=by_status rows status=literal_won subject before_tax | ✅ Won alone and Lost, "status" said *(2026-10-06, decision 2)* |
| `how much have I sold for the last fortnight?` [est] | `metric` metric=total status=sold period=last_n_days days=14 | ✅ the last 14 days *(2026-10-06 — a time frame was looked up as a name; today's rules said it back: "I can't narrow a total by "the last fortnight" yet. …")* |
| `how much have I sold for the past few months?` [est] | ask | ✅ never a guessed count *(2026-10-06 — a time frame was looked up as a name; today's rules said it back)* |
| `what's the value of my recurring one-time work?` [est] | ask | ✅ never one of the two guessed *(2026-10-06 — today's rules said it back: "I can't narrow a total by "recurring one-time" yet. …")* |
| `what is the total value not including tax?` / `what's the total before tax?` | `metric` metric=total before_tax | ✅ nothing open: every estimate's total — *"Total value, all time: $1,500.00 across 4 estimates, before tax."*; with an estimate open, that one's (§1.2) *(2026-10-05, user decision — it was help: "I can't see the estimate figures from here")* |
| `what's the total value including tax?` | `metric` metric=total | ✅ nothing open: every estimate's total, including tax *(2026-10-05, user decision)* |
| `how much did we sell this year minus tax?` / `what's our revenue this year not including tax?` [est] | `metric` metric=total status=sold period=year before_tax | ✅ that figure before tax *(2026-10-05 — "not including tax" read "including tax" out of it as with tax)* |
| `how much are my open estimates worth?` [est] | `metric` metric=total status=open | ✅ the open estimates' total *(2026-10-05)* |
| `what's the gross margin with tax?` | `metric` metric=margin | ✅ nothing open: the company's margin, always pre-tax *(Phase 3 review #4 — "tax" was looked up as a name. `… after tax` is said back, not read as either: it usually means with the tax taken off — review round 2 #1)* |
| `what's our revenue with tax?` [est] | `metric` metric=total status=sold | ✅ its tax-inclusive total *(Phase 3 review #4 — "tax" was looked up as a name)* |
| `win rate by value` / `what share of my quoted dollars did I win?` [est] | `metric` metric=win_rate_by_value | ✅ sold dollars against Lost dollars, by their totals including tax — only when asked so; a plain win rate still counts estimates *(Simon 2026-10-13; decision 14)* |
| `what's the total value of my draft estimates over $1000?` [est] | `list_estimates` total filter.statuses=Draft filter.amount.over=1000 | ✅ the list's total over the amount — a figure has none *(reference run 2026-10-14; review rounds 20–23)* |
| `total of my open estimates above $2k` [est] | `list_estimates` total filter.open_only filter.amount.over=2000 | ✅ the open estimates' list, "$2k" read as $2,000 *(2026-10-14)* |
| `how many of my sent estimates are under $500?` [est] | `list_estimates` count filter.statuses=Sent filter.amount.under=500 | ✅ the list's count under the amount *(2026-10-14)* |
| `what's the value of my sold estimates over $1,250.50 this month?` [est] | `list_estimates` total filter.sold filter.amount.over=1250.5 filter.period=month | ✅ the sold set's list, its period kept *(2026-10-14)* |
| `total of my estimates between $1k and $5k` / `total of my estimates over $1000 and under $5000` [est] | `list_estimates` total filter.amount.over=1000 filter.amount.under=5000 | ✅ both bounds *(2026-10-14)* |
| `total of my Maintenance estimates over $1000` [est] | `list_estimates` total filter.division filter.amount.over=1000 | ✅ that kind of work's estimates *(2026-10-14)* |
| `what's my average estimate over $1000?` [est] | `metric` metric=average amount.over=1000 | ✅ said back — *"I can't narrow that figure by an amount yet. I can list those estimates with their total instead — for example, "list my estimates over $1,000 with their total"."* — never the average of every estimate *(2026-10-14)* |
| `what's my win rate on jobs over $5,000?` [est] | `metric` metric=win_rate amount.over=5000 | ✅ said back, as above *(2026-10-14)* |
| `what's Bob Lee's total over $1000?` [est] | `metric` metric=total subject amount.over=1000 | ✅ said back: a subject may be a customer, a property or a division, and only the run can tell *(review round 21 #4)* |
| `total of my estimates of at least $1000` [est] | `list_estimates` total filter.amount.at_least=1000 | ✅ "at least" takes an estimate of exactly $1,000 — *"… at least $1,000 …"* *(2026-10-14: the model writes the amount as said — over, at least, under, at most; it was said back while a pattern read the words)* |
| `total of my estimates up to $5000` [est] | `list_estimates` total filter.amount.at_most=5000 | ✅ *(2026-10-14)* |
| `total of my estimates over $1M` [est] | `list_estimates` total filter.amount.over=1000000 | ✅ *(2026-10-14)* |
| `total of my estimates over five grand` [est] | `list_estimates` total filter.amount.over=5000 | ✅ *(2026-10-14)* |
| `my pipeline over $1000` [est] | `dashboard` card=pipeline amount.over=1000 | ✅ said back, as a figure's — a card has no amount *(2026-10-14)* |
| `mark it won, and what's my average estimate over $1000 now?` [est] | `set_status` status=Won | ✅ the status changes; the figure is left out and said back above the reply *(review round 23 #1)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Answer | Status |
|---|---|---|
| `how much has Birch Hollow spent with us?` → *"Which one did you mean: Birch Hollow (customer) or Birch Hollow (property)?"* → `Birch Hollow (customer)` / `1` / `the customer` | that one's figure — *"Sold value for Birch Hollow, all time: $800.00 …"* | ✅ rule *(2026-10-03, #785 — the option's "(customer)" was written into the question, which then matched no shape. The name goes back bare and the kind rides on the turn: `record_names.kind_in_answer`, `forced_metric_subject_kind`)* |
| `what's my biggest estimate?` → `what's its status?` / `open it` | the estimate named is the one in focus, and the one row a pick reads | ✅ rule *(task 12)* |
| `how much have I sold to Ana?` → *"Which one did you mean: Ana Lopez or Ana Reyes?"* → `Ana Reyes` (or `2`) | the question runs again for Ana Reyes | ✅ rule *(task 12 — the name goes into the question, `record_names.ask_to_rewrite`; also after "I couldn't find …" and "Which property do you mean?". The name replaced is the last whole-word one: "the lifetime won amount for Tim" → "Tim Hortons" once made "lifeTim Hortonse", review 2026-09-30 #6)* |
| `how much have I sold to Bob Lee this year?` → `and last year?` / `what's the lifetime won amount from 12 Oak St?` → `what about Elm House?` | the same question for the new period or the new place | ✅ rule *(task 12 — §10.8. The name swapped is the last whole-word one — review 2026-09-30 #7)* |
| `who are my best customers?` → `show me the second one` / `top 2 properties by sold value` → `show more` → `the first one` | the second customer's record; the next page of the ranking (*"More of your properties … 3. 9 Maple Ave — … That's the last of them — 3 in all."*), whose rows are what "the first one" picks | ✅ rule *(Phase 2 task 8 — ranked customers and properties are recorded as records; "show more" pages like any list, `conversation/paging.py`)* |
| `who are my best customers?` → `show me the top 10` / `top 3` / `just the top three instead` | the same ranking with that many rows | ✅ rule *(Phase 2 task 8 — `followup._resized_ranking`; only a ranking that says "top" / "best", not "which property has the most …?")* |
| `who are my best customers?` → `and last year?` / `this month vs last month for Bob Lee` → `what about Ana Reyes?` | the same question for the new period or the new customer | ✅ rule *(Phase 2 task 8 — the `analytics_` replay, as for Phase 1's figures)* |
| `this month vs last month` → `and last year?` / `how does this month compare to last month?` → `what about last quarter?` | the comparison over the new unit — "this year vs last year", "how does this quarter compare to last quarter?" | ✅ rule *(Phase 2 review #8 — the first time phrase alone was swapped: "last year vs last month", which nothing read)* · 🤖 planner: that period's figure, not a comparison — deliberate (`followups._redo`, pinned by `test_a_comparison_for_another_period_is_that_periods_figure`) |
| `what's the win rate for Bob Lee?` → `what about Ana Reyes?` / `what's my win rate this year?` → `and last year?` | the win rate for the new customer or period | ✅ rule *(Phase 3)* |
| `what's my gross margin this year?` → `and last year?` / `what's the gross margin for Bob Lee?` → `what about Ana Reyes?` | the same question for the new period or customer | ✅ rule *(Phase 3)* |
| `what's my win rate?` / `what's our revenue this year?` / `what's my gross margin?` → `what about Bob Lee?` — a company-wide metric question, then a name | the same question for Bob Lee — *"The win rate for Bob Lee, all time, is 67% …"* | ✅ rule *(2026-10-03, #789 — went to help: the question named no one to swap. "for Bob Lee" is added when the metric grammar reads it as the subject; never to a ranking by customer or property)* |
| `What's the total value of my estimates this year before tax?` → `does that include tax?` → `what about before tax?` | *"Total value this year: $1,500.00 across 4 estimates, before tax."* → *"That was before tax. Here it is including tax:\nTotal value this year: $3,745.00 across 4 estimates, including tax."* → the first figure again | ✅ rule *(2026-10-05, user screenshot — the first was the dashboard's tax-inclusive total over the last 365 days; the second was "I'm not able to help with that"; the third swapped "before tax" in as a name)* |

*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `just the won ones` | conversation `ref-ranking-then-just-the-won-ones` | ✅ the planner handles it — was a gap: after a figure or a ranking, a status said is that figure for the status — "Your customers by won value" *(decision 13 left it unsupported, 2026-09-30; 2026-10-13)* |
| `what about Elm House under $1000?` | conversation `ref-list-then-an-amount-for-another-place` | ✅ the planner handles it — was a gap: after a list, the amount said is that list's amount (`redo_last` amount), the old one replaced (`followups._redo`; #1080, 2026-10-14) |

*Not yet in the Plan format — a reply rather than a phrasing, the public widget, or right after a count or a gross margin (no state in the reader fits):*

| Phrasing | Answer | Status |
|---|---|---|
| a total that includes recurring work | *"… including tax. Recurring work is counted for every visit it's scheduled for."* | ✅ rule *(task 12)* |
| `how much have I sold this year?` on the **public** widget | *"I can't see anyone's estimates from here — I'm in read-only demo mode. Sign up …"* | 🛑 refusal *(task 12 — the widget has no company; a figure would be made up)* |
| `does that include tax?` after a count or a gross margin | *"That answer has no tax in it. Totals I give include tax unless you ask for them before tax …"* | ✅ rule *(2026-10-05)* |

**Not metrics** — each keeps its own answer: `how much is E0042?` and `what's
the total on it?` (one estimate, §1.2); `what's the total of those?` (the list
just shown, §1.1); `what is the total value of the open estimates` and
`estimates over $10k` (the list's total and filter, §1.1); `what's my
pipeline?`, `how much have I completed this month?`, `what's my completed value?` and `estimate value
by division` (the dashboard, §1.9); `how is my win rate calculated?` (help);
`what's the gross margin?` / `… on it` / `… on work item 2` / `… on E0042` (one
estimate or work item, §1.2 / §1.5.7); `what's my material markup?` (a
setting); `what's the difference between markup and margin?`, `what markup do
I need for a 20% margin?` (help); `set the margin to 30%` (an edit); `how much mulch do
I need …` (the Calculator, §10.3); `what's the average wage for Foreman?`
(§5.8). Tests: `tests/test_metric_query.py` (accept / reject / reading /
routing / answers), `tests/test_metric_ratios.py` (win rate, margin,
markup), `tests/test_metric_win_rate.py`, `tests/test_metric_margin.py`, `tests/test_maple_metrics.py`,
`tests/test_metric_subject.py`, `tests/test_metric_periods.py`,
`tests/test_metric_spec.py`, `tests/test_tax_words.py`, `tests/test_tax_followup.py`; scopes, windows and
breakdowns: `tests/test_metric_query.py` (BY_STATUS and the combined rows), `tests/test_maple_metrics.py`
(type of work, scoped status totals), `tests/test_metric_periods.py` (`last_n`); multi-turn: the `METRICS` conversations in
`tests/maple_conversations/corpus.py`. #783, #784, #785, #786, #787 and #789
resolved 2026-10-03.


# 2. Properties

## 2.1 Direct imperatives

| Phrasing | Plan | Status |
|---|---|---|
| `add a property called Birch Cottage` | `create_property` fields.name | ✅ *(2026-09-27)* |
| `list all properties` | `list_properties` | ✅ |
| `delete the property {property}` | `delete_property` | ✅ |
| `delet the proprty at 14 Birch Rd` | `delete_property` | ✅ a misspelt command reads as said, then asks first like any delete *(2026-10-19 review — probed live, §13.1)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent |
|---|---|
| `create a new property` → *"What's the property's address? For example: 20 Birch Rd, Toronto, ON."* → `20 Birch Rd, Toronto, ON` | `create_property` → Property Agent *(2026-09-27 — it asked for "the missing property details" without naming any)* |

## 2.2 Casual phrasings

| Phrasing | Plan | Status |
|---|---|---|
| `show me my properties` / `what properties do I have?` | `list_properties` | ✅ |
| `pull up property {property}` | `get_property` | ✅ |

## 2.3 Possessive

| Phrasing | Plan | Status |
|---|---|---|
| `show me {property}'s details` | `get_property` | ✅ |
| `what's {property}'s city?` / `what's the city of {property}?` | `get_property` field=city | ✅ |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `update {property}'s record` → *"which fields?"* → `city` → the value | `update_property` → Property Agent | ✅ rule · 🤖 planner: the field named, its value asked ("What's the new city?") *(2026-10-12 — it looped)* |

These routed but reached no record until 2026-09-27: the agent couldn't read a name followed by "'s". The router now rewrites a possessive or "the <field> of <name>" look — for a property, contact, material, role or template whose exact name it is, and only one kind — into the form its agent reads (`agents/conversation/catalog_names.py::_record_reference`). A name that is nobody's is left alone, and "{name}'s estimates" / "{name}'s notes" are other questions (§8, §3.9).

## 2.4 Count

| Phrasing | Plan | Status |
|---|---|---|
| `how many properties do I have?` / `count my properties` / `total number of properties` | `list_properties` count | ✅ |

## 2.5 Filter / find

| Phrasing | Plan | Status |
|---|---|---|
| `find properties named Toronto` / `search for properties matching Toronto` | `list_properties` filter.text=Toronto | ✅ |
| `how many properties are in Toronto?` | `list_properties` count filter.city=Toronto | ✅ *"You have 2 properties in Toronto."* (2026-09-27, #687: every property was counted) |
| `show me properties in Toronto` | `list_properties` filter.city=Toronto | ✅ *(2026-09-27, #687: every property was listed)* |
| `list properties in Guelph` | `list_properties` filter.city=Guelph | ✅ |
| `properties matching Elm in Toronto` | `list_properties` filter.text=Elm filter.city=Toronto | ✅ *(2026-10-11, #845 — fell back)* |
| `how many properties does Ana Lee own in Toronto?` | `list_properties` count filter.owner filter.city=Toronto | ✅ *(2026-10-11, #845 — fell back)* |
| `do we have a property on Oak St?` | `list_properties` filter.text | ✅ a yes/no about a record is the list it would be in *(2026-10-19 review — probed live, §13.1)* |
| `properties added last week` | `list_properties` filter.added | ✅ the properties added in that period, on the user's clock, newest first; beside another filter the window is said back, never dropped — G22 (gap plan 2026-10-19, closed the same day) |

A city nobody has is said so ("You don't have any properties in Ottawa").

## 2.6 Field-targeted update

| Phrasing | Plan | Status |
|---|---|---|
| `change the city of {property} to Vancouver` / `update the city on {property} to Vancouver` / `set {property}'s city to Vancouver` | `update_property` fields.city=Vancouver | ✅ |
| `update the name of {property} to Oak House` | `update_property` fields.name | ✅ *(2026-09-27 — it wrote the name "12 Oak St to Oak House" and looked the property up by the new name)* |
| `zip M4B 1B3` / `the postal code is M4B 1B3` [property_focus] | `update_property` fields.postal_zip | ✅ the property just created or shown *(2026-09-27, §10.8)* |
| `its city is Guelph` [property_focus] | `update_property` fields.city=Guelph | ✅ the property just created or shown *(2026-09-27, §10.8)* |
| `add a note to {property}: "gate code 4411"` / `set the notes on {property} to "gate code 4411"` | `add_note` | ✅ a real `Note`, authored by the acting user *(2026-09-17 — `notes` is no longer a `Property` field)*. Also on create: `create a property at 123 Main St with notes: gate code 4411`. |

## 2.7 Address formats accepted on create

Each single-line format is read into its parts, so the user can give a complete address in one message.

| Phrasing | Plan | Status |
|---|---|---|
| `create a property at 123 Main Street, Vancouver, BC, V1V 2A2` | `create_property` fields.city=Vancouver fields.postal_zip | ✅ Canadian, comma-separated with postal |
| `create a property at 123 Main Street, Vancouver, BC, Canada, V1V 2A2` | `create_property` fields.city=Vancouver fields.country | ✅ Canadian, with country (or postal-then-country) |
| `create a property at 888 River Road, Richmond, BC` | `create_property` fields.city=Richmond | ✅ Canadian, partial (street + city + province) |
| `create a property at 123 Maple Drive, Surrey BC V3T 4R5` | `create_property` fields.city=Surrey fields.postal_zip | ✅ Canadian, province not comma-separated |
| `create a property at 155 Asharoken Ave, Northport, NY 11768` | `create_property` fields.city=Northport fields.postal_zip | ✅ US, "City, ST ZIP" (no comma before the ZIP) |
| `create a property at 155 Asharoken Ave, Northport, NY 11768-1234` | `create_property` fields.city=Northport fields.postal_zip | ✅ US, ZIP+4 |
| `create a property at 1036 Fort Salonga Rd Northport NY` | `create_property` fields.city=Northport | ✅ no commas at all |

## 2.8 Verbless

| Phrasing | Plan | Status |
|---|---|---|
| `{property}` / `I want the details for {property}` / `tell me about {property}` | `get_property` | ✅ a bare address too (Phase 2a) |

## 2.9 Property gaps

| Phrasing | Plan | Status |
|---|---|---|
| `remove {contact} from {property}` | refuse `out_of_chat` `unlink` | 🛑 nothing is deleted; Maple says the link is removed in the app (§9.8, #679) |
| `60 minutes one way` / `3 days back way` / `20 miles each way` | ask | ✅ not a property — a number then a unit is an amount, never a street number *(2026-10-03, #49 — `_ADDRESS_PATTERN` read them as an address. Only before "way", "court" or "ct": `123 Cedar Way`, `who lives at 12 Elm Court` and streets named after a unit (`2500 4 Mile Rd`, `10 Mile Rd`) still read as addresses)* |

*Not yet in the Plan format — a record the test world lacks, or an answer to a question (phase 3):*

| Phrasing | What happens | Status |
|---|---|---|
| a property whose name looks like a person's (`show me Elm House`) | the property, when that is its exact name and no contact's | ✅ rule *(2026-09-27 — it answered "No contact found with name 'Elm House'")* |

*An answer to a question, on the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `12 Oak St` | conversation `ref-property-picked-by-name-from-a-menu` | ✅ the planner handles it — was a gap: the reply to *"More than one property matches that"*; today's question kept no record, so the request was lost *(deferred 2026-09-29 — name-answers plan §7)* |

Cross-resource phrasings (e.g. `who lives at {property}?`) are tracked under §8.

**Notes, links and follow-ups** for properties and contacts are in §3.9.

**Open gaps:** older #101, #322 (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #679, #682, #683, #687, #697; #49 on 2026-10-03.

---

# 3. Contacts

## 3.1 Direct imperatives

| Phrasing | Plan | Status |
|---|---|---|
| `create a new contact` | `create_contact` | ✅ |
| `list all contacts` | `list_contacts` | ✅ |
| `delete the contact {contact}` | `delete_contact` | ✅ |
| `add a contact named Dan Park` | `create_contact` fields.first_name=Dan fields.last_name=Park | ✅ creates one *(2026-09-27 — it looked for a Dan Park to update)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Status |
|---|---|
| `create a contact` → *"What's the contact's name? First and last, please."* → `Dan Park` | ✅ creates Dan Park *(2026-09-27 — the bare name reply asked the same question again)* |

## 3.2 Casual phrasings

| Phrasing | Plan | Status |
|---|---|---|
| `show me my contacts` / `what contacts do I have?` | `list_contacts` | ✅ |
| `pull up contact {contact}` | `get_contact` | ✅ |

## 3.3 Possessive

| Phrasing | Plan | Status |
|---|---|---|
| `show me {contact}'s details` | `get_contact` | ✅ |
| `what's {contact}'s phone?` / `what's the phone number for {contact}?` | `get_contact` field=phone | ✅ |
| `what's Bob's email?` | `get_contact` field=email | ✅ a first name |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Status |
|---|---|
| `update {contact}'s record` → *"which fields?"* → `phone` → the number | ✅ rule · 🤖 planner: the field named, its value asked *(2026-10-12 — it looped)* |

Routed, but found no one until 2026-09-27 — see §2.3.

## 3.4 Count

| Phrasing | Plan | Status |
|---|---|---|
| `how many contacts do I have?` / `count my contacts` / `total number of contacts` | `list_contacts` count | ✅ |

## 3.5 Filter / find

| Phrasing | Plan | Status |
|---|---|---|
| `find contacts named Smith` / `search for contacts matching Smith` | `list_contacts` filter.name=Smith | ✅ |
| `show contacts in Toronto` | `list_contacts` filter.city=Toronto | ✅ *(2026-09-27, #687: city and role filters; the list came back unfiltered)* |
| `how many contacts are in Guelph?` | `list_contacts` count filter.city=Guelph | ✅ *(2026-09-27, #687)* |
| `list homeowners` | `list_contacts` filter.role | ✅ *(2026-09-27, #687)* |
| `show me the property managers` | `list_contacts` filter.role=Manager | ✅ *(2026-09-27, #687)* |
| `which contacts are administrators?` | `list_contacts` filter.role=Administrator | ✅ *(2026-09-27, #687)* |
| `list homeowners in Guelph` | `list_contacts` filter.role filter.city=Guelph | ✅ *(2026-09-27, #687)* |
| `contacts named Ana in Toronto` | `list_contacts` filter.name=Ana filter.city=Toronto | ✅ a name beside them too *(2026-10-11, #845 — fell back)* |
| `home owners named Di` | `list_contacts` filter.name=Di filter.role | ✅ a name beside them too *(2026-10-11, #845 — fell back)* |
| `is there a contact named Bob?` | `list_contacts` filter.name=Bob | ✅ a yes/no about a record is the list it would be in *(2026-10-19 review — probed live, §13.1)* |
| `shwo my contacs` | `list_contacts` | ✅ misspelt, read as said *(2026-10-19 review — probed live, §13.1)* |
| `which contacts did I add this month?` | `list_contacts` filter.added | ✅ the contacts added in that period, newest first — G22 (gap plan 2026-10-19, closed the same day) |

A filtered list is remembered, so `show me the second one` picks from it.

## 3.6 Field-targeted update

| Phrasing | Plan | Status |
|---|---|---|
| `change the phone of {contact} to 555-1111` / `update the phone on {contact} to 555-1111` / `set {contact}'s phone to 555-1111` | `update_contact` fields.phone=555-1111 | ✅ |
| `his phone is 519-555-1234` / `519-555-1234` [contact_focus] | `update_contact` fields.phone=519-555-1234 | ✅ the contact just created or shown — a bare phone number too *(2026-09-27, §10.8 — these were unknown, or started a second contact)* |
| `her email is ana@new.example.com` / `add her email ana@new.example.com` / `ana@new.example.com` [contact_focus] | `update_contact` fields.email=ana@new.example.com | ✅ the contact just created or shown — a bare email too *(2026-09-27, §10.8 — these were unknown, or started a second contact)* |
| `and her email is ana@new.example.com` [contact_focus] | `update_contact` fields.email=ana@new.example.com | ✅ "and" first: the same update — never "what about X?" *(2026-10-04, #741 — the follow-up rewrite took it as a new target and showed "contact her email is …"; a target that states a value — " is ", " are ", "should be", "=" — is none)* |
| `and the phone should be 519-555-1234` [contact_focus] | `update_contact` fields.phone=519-555-1234 | ✅ "and" first: the same update — never "what about X?" *(2026-10-04, #741)* |
| `set Bob Lee's phone to 519-555-0000 and his email to bob@lee.ca` | `update_contact` fields.phone=519-555-0000 fields.email=bob@lee.ca | ✅ two fields in one write *(2026-10-19 review — probed live, §13.2)* |
| `remove Bob Lee's phone number` / `clear Ana Reyes's email` | `update_contact` fields.clear | ✅ "I've cleared Bob Lee's phone number." — a contact keeps its name; a property clears only its postal code and country — G21 (gap plan 2026-10-19, closed the same day) |
| `add a note to {contact}: "prefers texts"` / `set the notes on {contact} to "prefers texts"` | `add_note` | ✅ *(2026-09-17 — `notes` is no longer a `Contact` field; the phrasing creates a real `Note`, authored by the acting user, instead of writing a scalar. Also handled inline on create.)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Status |
|---|---|
| `change Ana's phone to …` with two Anas → *"More than one contact matches that: 1. Ana Reyes 2. Ana Lopez"* → `Ana Lopez` / `2` / `the second one` | ✅ rule *(2026-09-27 — it said "Multiple contacts matched" and the reply dead-ended)* |

## 3.7 Verbless

| Phrasing | Plan | Status |
|---|---|---|
| `{contact}` / `I want the details for {contact}` / `tell me about {contact}` | `get_contact` | ✅ a bare name too (Phase 2b person-name heuristic) |

## 3.8 Contact gaps

| Phrasing | Plan | Status |
|---|---|---|
| `link {contact} to {property}` | `link` | ✅ the planner handles it — was a gap: (LLM tier) — a correct LLM answer can be demoted to `off_topic` (#690) — the rule tier now handles the guide's phrasings first (§3.9) |

*An answer to a question:*

| Phrasing | Plan | Status |
|---|---|---|
| `link Ana to 9 Maple Ave` | conversation `ref-contact-picked-by-name-while-linking` | ✅ the planner handles it — was a gap: `Ana Reyes` in reply to *"More than one contact matches that"* while linking; today's didn't remember the matches it offered *(deferred 2026-09-29 — name-answers plan §7)* |

Cross-resource phrasings (e.g. `where does {contact} live?`) are tracked under §8.

## 3.9 Notes, links and follow-ups for contacts and properties *(2026-09-27)*

One handler (`agents/conversation/record_notes.py`) keeps the notes feed for contacts, properties and estimates, and one (`agents/conversation/record_links.py`) links a contact and a property in the user guide's words (design 2026-09-27 §7.3; user decision (b)). Adding a note to an estimate or work item stays with the estimate grammar (§1.0).

| Phrasing | Plan | Status |
|---|---|---|
| `add a note to him: call after 5` [contact_focus] | `add_note` | ✅ files the note, authored by you *(it asked "which fields?" on the rules tier)* |
| `add a note to Bob Lee saying call after 5` / `jot down a note for 12 Oak St: gate code 4411` | `add_note` | ✅ files the note, authored by you *(it asked "which fields?" on the rules tier)* |
| `add a note: she wants the gate locked` / `add a note: there is a dog` [task_focus] | `add_note` parent.domain=task | ✅ the note goes to the task in focus, over an older contact or property anchor *(2026-10-03, #726 — a pronoun inside the dictated note picked the contact or property)* |
| `add a note: a dog in the yard` / `add a note: the estimate needs review` / `add a note: check the property line` [contact_focus] | `add_note` parent.domain=contact | ✅ the note goes to the record in focus (an estimate, property, contact or task) — a domain word in the body names nothing *(2026-10-04, #806 — "yard" sent it to a property, "estimate" to the estimate. With nothing in focus, or a material or role in focus (they take no notes), the body is still the only signal: `add a note: the estimate needs review` goes to the estimate)* |
| `Add a note to Elm House. The note should say: remember to buy more trees` / `Add a note to Elm House. It should say: order more mulch` / `Add a note to Elm House, the note should say order more mulch` / `Add a note to Bob Lee. Note: call after 5` | `add_note` body | ✅ the words introduced in a sentence of their own: files the words after "should say" / "Note:" on the record named *(Simon, 2026-10-11 — acceptance rows `note-said-in-its-own-sentence*`; the rules tier reads the second sentence into the record's name and says it couldn't find "Elm House. The note should say")* |
| `note: call after 5` / `Note - bring the trailer` [contact_focus] | `add_note` parent.domain=contact | ✅ the shorthand, said first: files the note on the record in focus |
| `Please note: I want to change the markup to 20%` / `please note - the price changed` | ask | ✅ not a note — "please note" is "be aware"; the request is read as a request (on the rules tier Maple asks what to do) *(2026-10-04, #742 — it was filed as a note and the request wasn't carried out. A lead word before a verbless "note" makes it the idiom; with a verb, `please add a note: …` is still a note)* |
| `show me the notes for 12 Oak St` / `what notes are on Bob Lee?` / `any notes on E0042?` | `list_notes` | ✅ lists them newest first, with author and date |
| `show me his notes` [contact_focus] | `list_notes` | ✅ lists them newest first, with author and date |
| `delete Bob Lee's note` | `delete_note` | ✅ a note delete today's note handler can't parse; there it says *"I couldn't tell which note you meant, so I haven't deleted anything. Say "delete my note on <name>" — or "show me the notes for <name>", then "delete note 2" — and I'll find it."* *(2026-10-03, #743 — said notes couldn't be deleted from chat)* |
| `delete the oldest note for Ana Reyes` | `delete_note` which=oldest | ✅ asks about the record's oldest note (anyone's as its list shows them); someone else's is refused for a Member *(2026-10-11 — it listed the notes and pointed at row 1, the newest; a gap on today's pipeline)* |
| `delete the latest note on 12 Oak St` | `delete_note` which=newest | ✅ asks about the record's newest note (anyone's as its list shows them); someone else's is refused for a Member *(2026-10-11; a gap on today's pipeline)* |
| `delete my newest note on Ana Reyes` | `delete_note` mine which=newest | ✅ "my" — yours only *(2026-10-11; a gap on today's pipeline)* |
| `I want to delete a note on Ana Reyes` | `delete_note` | ✅ lists the record's notes and asks which (*"Which one should I delete? Say "delete note 2"…"*) *(2026-10-11; a gap on today's pipeline)* |
| `show me his contact info` [contact_focus] | `get_contact` | ✅ the contact in focus — a pronoun is never looked up as a name *(2026-10-01, #703 — "his" matched "Chris", which then took the focus)* |
| `delete that one` [contact_focus] | `delete_contact` | ✅ the contact in focus — a pronoun is never looked up as a name *(2026-10-01, #703)* |
| `link John Doe to 123 Main St` / `link 123 Main St to John Doe` / `connect Carla Diaz with the Elm House property` / `add Carla Diaz to 12 Oak St` / `Carla Diaz lives at 12 Oak St` | `link` | ✅ links them (either order); "already linked" when they are *(the guide's own phrasing was unknown on the rules tier)* |
| `link Zed Quill to 12 Oak St` | `link` | ✅ no such contact: "I couldn't find a contact or a property called Zed Quill." |
| `remove Ana Reyes from 12 Oak St` / `unlink Ana Reyes from 12 Oak St` | refuse `out_of_chat` `unlink` | 🛑 done in the app — §9.8 |
| `add this to Elm House's notes` / `add a note to Bob Lee with this PDF` / `put this photo on 12 Oak St` [none+photo] | `add_note` attach | ✅ with a photo or PDF on the message (or the previous one): a note with the file(s), signed by you; the body is whatever else was said, and may be nothing (Maple attachments, 2026-10-18) |
| `add a note to Bob Lee with the gate code from the PDF` [none+quote] | `add_note` body | ✅ the fact is copied out of the file's text into the note — only what was asked for, never the whole file (Maple attachments, 2026-10-18) |
| `attach this to Elm House` / `put this on 12 Oak St` [none+photo] | `add_note` attach | ✅ a note with the file(s) on the property; with no file on the message or the previous one, Maple says to add a photo or PDF with the + button (`NO_FILE_ON_MESSAGE_REFUSAL`) (Maple attachments, 2026-10-18) |
| `add this business card as a contact` / `create a contact from this photo` [none+card] | `create_contact` | ✅ with a photo of a card on the message: the name, phone and email are copied from what Maple read into the contact's fields; the file isn't attached — only an estimate or a task carries the file it was made from (review 2026-10-18 #34) |
| `update Bob Lee's phone from this card` / `use this card to update Bob Lee` [none+card] | `update_contact` fields.phone | ✅ with a photo of a card on the message: the fields asked for (or, said generally, every field the card shows) are copied from what Maple read; the file isn't attached *(2026-10-19 review — probed live with a card on the message)* |
| `create a property from this work order` [none+workorder] | `create_property` fields.street fields.city | ✅ with the PDF on the message: the name and address are copied from what Maple read; the file isn't attached — a property create only copies the facts *(2026-10-19 review — probed live with a work order on the message)* |
| `add this photo to the Foreman role` [none+photo] | refuse `notes_on_catalog` | 🛑 roles and materials take no notes or files *(2026-10-19 review — probed live)* |
| `attach this to Black Mulch` [none+invoice] | refuse `notes_on_catalog` | 🛑 materials and roles take no notes or files — refused in the policy whatever the model planned (it planned a note on the material one run in two) — G19 (gap plan 2026-10-19, closed the same day) |
| `add a note to Elm House: call back Tuesday` [none+prev_photo] | `add_note` | ✅ after `what's in this photo?`, the previous message's photo isn't attached: a file goes on a record a message later only when the message points at it ("it", "this", "that photo") (review 2026-10-18 #33) |

*Not yet in the Plan format — several turns, a state the test world can't build, or a refusal that depends on the user's role (phase 3):*

| Phrasing | Behavior | Status |
|---|---|---|
| `add a note to Bob Lee` → *"What should the note say?"* → the text | files the reply, even if it reads like a command | ✅ rule |
| `delete my note on Bob Lee` / `delete note 2` (after a list) / `delete my last note on Ana Reyes` → *"Delete your note …? This can't be undone."* → `yes` / `no` | deletes it, or keeps it; your own notes, or any as an Owner | ✅ rule *(it was redirected to the app)* |
| `delete the note on Ana Reyes` / `delete note 1` as an Owner, on someone else's note → *"Delete Jordan Lee's note on Ana Reyes: …?"* → `yes` | *"I've deleted Jordan Lee's note on …"* — the author is named, never "your note"; `delete my note on …` offers only your own | ✅ rule *(2026-10-01, #705 / #758 — an Owner was offered an employee's note as "your note")* |
| `delete the first one` / `the second note` after a record's notes were listed (also after `how about for Ana Reyes?`) | *"Delete your note on Ana Reyes: “…”? This can't be undone."* → `yes` deletes that row's note | 🤖 planner *(2026-10-11 — the planner's state didn't show the notes list, so it asked "Which first one?"; on Dev an invalid plan fell to today's, which offered to delete the contact)* · ⚠️ today's reads "first one" as a contact · 🤖 planner: "how about for Ana Reyes?" lists hers *(2026-10-12 — it couldn't)* |

**Open gaps:** #745, #746 (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #679, #682, #683, #687, #690; 2026-10-01: #703, #705, #758; #743 on 2026-10-03; #741 and #742 on 2026-10-04.

---

# 4. Materials

## 4.1 Direct imperatives

| Phrasing | Plan | Status |
|---|---|---|
| `create a new material` | `create_material` | ✅ |
| `list all materials` | `list_materials` | ✅ |
| `delete the material {material}` | `delete_material` | ✅ |

**Standard materials** (shared material catalog, 2026-10-15). Maple sees the
company's own materials and the standard ones it opted into, never a hidden
or category-disabled one. Deleting a standard material **hides** it, after the
usual yes: *"I've hidden the standard material 'Black Mulch' from your
materials."* A company material that an estimate or template uses is not
deleted: *"I can't delete 'Edging' because it's used on estimates or
templates. You can hide it on the Materials page instead."* Creating a
material whose name a visible material already has is refused: *"A material
named 'Black Mulch' already exists."* Asking Maple to hide, show or reset a
material is stage 4 of the catalog plan — done 2026-10-19, below
([gap plan](plans/2026-10-19-maple-phrasing-gaps-plan.md) step 3).

*What the catalog shows (2026-10-19 — the catalog design's §9; each was a gap the review found, probed live):*

| Phrasing | Plan | Status |
|---|---|---|
| `hide Black Mulch` / `hide the Black Mulch material from my list` | `hide_material` | ✅ asked first — *"Hide Black Mulch from your materials? You can show it again any time. (yes/no)"* — then hidden from lists, pickers and Maple; standard or the company's own; Owner/Admin — G1 (gap plan 2026-10-19, closed the same day) |
| `show Black Mulch again` / `unhide Black Mulch` | `show_material` | ✅ found among the hidden materials and shown again, no question; one that isn't hidden is said so; Owner/Admin — G2 (gap plan 2026-10-19, closed the same day) |
| `which materials have I hidden?` / `show my hidden materials` | `list_materials` filter.hidden | ✅ the hidden ones, named so "the second one" picks from them — G3 (gap plan 2026-10-19, closed the same day) |
| `unhide all my materials` | `show_material` all | ✅ asked first, then every hidden material shown again (the Materials page's unhide-all); one whose name the company's own material holds stays hidden and is named — G4 (gap plan 2026-10-19, closed the same day) |
| `reset Black Mulch to the standard price` / `go back to the standard price for Black Mulch` | `reset_material` | ✅ asked first, then the company's own costs, prices and hide dropped; the company's own material is refused — *"… is your own material, so there's no standard to reset it to."* — G5 (gap plan 2026-10-19, closed the same day) |
| `is Black Mulch a standard material?` | `get_material` field=source | ✅ *"Black Mulch is a standard material, from 3Maples' list — you can hide it, or change its cost and price."* / *"… is your own material."* — G6 (gap plan 2026-10-19, closed the same day) |
| `which of my materials are standard?` / `list my custom materials` | `list_materials` filter.source | ✅ standard or the company's own; beside a category, price or estimate it is said back — G7 (gap plan 2026-10-19, closed the same day) |
| `turn on the Irrigation standard materials` / `stop showing standard materials in Soil` | `set_standard_category` | ✅ asked first, then the category's standard materials on or off (per-item hides kept); a category with no standard materials is said so; Load Standard stays the redirect for loading them all — G8 (gap plan 2026-10-19, closed the same day) |
| `add a 2 yd size to Black Mulch` | `update_material` fields.add_size fields.size | ✅ refused with the offer of a copy (D2, Simon 2026-10-19): *"Black Mulch is a standard material, so its sizes can't change. Want me to make you a copy — Black Mulch copy — and add the size there? (yes/no)"*; the yes makes the copy and changes it; Owner/Admin — G9 (gap plan 2026-10-19, closed the same day) |
| `make me a copy of Black Mulch` | `copy_material` | ✅ a standard material copied as the company's own, "Black Mulch copy"; a copy of the company's own material stays the app's (§9.8); Owner/Admin *(gap plan 2026-10-19, D2)* |

## 4.2 Casual phrasings

| Phrasing | Plan | Status |
|---|---|---|
| `show me my materials` / `what materials do I have?` | `list_materials` | ✅ |
| `pull up material {material}` | `get_material` | ✅ |

## 4.3 Possessive

| Phrasing | Plan | Status |
|---|---|---|
| `show me {material}'s details` | `get_material` | ✅ |
| `what's {material}'s price?` | `get_material` field=price | ✅ |
| `update {material}'s record` | `update_material` | ✅ asks which field |

## 4.4 Count

| Phrasing | Plan | Status |
|---|---|---|
| `how many different materials do I have?` / `how many materials do I have?` / `count my materials` | `list_materials` count | ✅ |
| `how many types of materials do I have?` | `list_material_categories` count | ✅ |

The "different" / "types of" modifiers don't change the routing — `how many` already pins the action to ``list`` and the trailing ``materials`` pins the domain. Confirmed via `material_query_variants` coverage category.

## 4.5 Filter / find

| Phrasing | Plan | Status |
|---|---|---|
| `find materials named concrete` / `search for materials matching concrete` | `list_materials` filter.text=concrete | ✅ |
| `show materials in in stock` | ask | ✅ |
| `do I have Black Mulch?` | `list_materials` filter.text | ✅ a yes/no about a record is the list it would be in *(2026-10-19 review — probed live, §13.1)* |

## 4.6 Field-targeted update (material-level)

| Phrasing | Plan | Status |
|---|---|---|
| `change the price of {material} to $5` / `update the price on {material} to $5` / `set {material}'s price to $5` | `update_material` fields.price=5 | ✅ |
| `change the cost of Topsoil to 20` | `update_material` fields.cost=20 | ✅ no "material" said *(2026-09-27 — a material, role or template named exactly is rewritten kind-first, `catalog_names.py`)* |
| `update Topsoil's price to 45` | `update_material` fields.price=45 | ✅ no "material" said *(2026-09-27 — a material, role or template named exactly is rewritten kind-first, `catalog_names.py`)* |
| `update my Black Mulch price from this invoice` [none+invoice] | `update_material` fields.size fields.cost | ✅ with a supplier invoice on the message: what was paid is the size's cost (the price follows from the markup), for the size the invoice names — Owners and Admins only *(2026-10-19 review — probed live with an invoice on the message)* |
| `move Topsoil to the Bulk Materials category` | `update_material` fields.category | ✅ *(2026-09-27, #694 — the category name is resolved to its id, never created; it failed every time)* |
| `rename it to Screened Topsoil` [material_focus] | `update_material` fields.name | ✅ the material in focus |
| `show me the Black Mulch material` / `show me Black Mulch` | `get_material` | ✅ *(it listed every material, or looked for a contact)* |

Closed by Phase 2 of xfail-wave-1 — `_match_possessive_or_field_targeted` resolves the missing material domain via `FIELD_TO_DOMAIN["price"] → material` plus the material-shape residual on the captured entity name.

**Prices and sizes are Owner/Admin** (decision §11.4, 2026-10-15). A cost,
price, unit or size change from a Member is refused before anything is
written — *"Only owners and admins can change material prices and sizes."* —
and so is a create (*"Only owners and admins can add materials."*). A Member
can still rename, describe or re-categorize one of the company's own
materials. On a **standard** material a cost or price becomes the company's
own (a price pins it over the markup); its name, description, category and
sizes — a size's unit included, even one the company has no unit for — are
refused, with nothing written: *"Black Mulch is a standard material, so its
name, description, category and sizes can't change. You can still change its
cost and price."* An Owner or Admin is offered a copy instead, since
2026-10-19 (§4.1, D2). *(2026-10-16 — a unit given for a standard size whose unit
the company doesn't carry was said as updated, with nothing changed.)*

## 4.7 Verbless (Phase 2b material-shape residual)

| Phrasing | Plan | Status |
|---|---|---|
| `{material}` / `I want the details for {material}` / `tell me about {material}` | `get_material` | ✅ |

## 4.8 Size-scoped operations *(shipped in Phase B; any size since 2026-09-27)*

A size is a number with an optional unit and package word (`3 cu ft`, `3 cu ft bag`, `1 cubic yard`, `2x4`) or one word (`large`). Parsed by `agents/material/size_commands.py` (2026-09-27 — a size of more than one word was never recognised) and applied through the ordinary update path, so its guards hold.

| Phrasing | Plan | Status |
|---|---|---|
| `add size {size} to {material} with cost $8 and unit Bag` / `add a 3 cu ft bag size to {material} at $6` / `add a 1 cu yd size to {material} at cost 200 per cu yd` | `update_material` fields.add_size fields.size | ✅ a new size |
| `delete size {size} for {material}` / `remove the {size} size from {material}` | `update_material` fields.remove_size fields.size | ✅ that size removed |
| `update the price for {material} with size {size} to $5` | `update_material` fields.size fields.price=5 | ✅ that size only |
| `change the cost of the {size} size of {material} to 4.50` | `update_material` fields.size fields.cost=4.50 | ✅ that size only |
| `Topsoil 1 yd is $6 per bag` | `update_material` fields.size fields.price=6 fields.unit | ✅ that size's price and unit (with no size said, a one-size material's only size); a standard material's unit can't change — refused, nothing written, but its own unit said beside the price is just the price *(2026-10-17 — the unit was dropped while Maple said it updated; a standard's own unit refused the price)* |
| `Mulch is $6 per bag` | `update_material` fields.price=6 fields.unit | ✅ the price of the material named Mulch, for its size; several matching are asked which — G26 (gap plan 2026-10-19, closed the same day) |
| `rename size {size} of {material} to 1 cubic yard` | `update_material` fields.size fields.rename_size_to | ✅ |
| `delete size 1 cu yd for Topsoil` | `update_material` fields.remove_size fields.size | ✅ Topsoil has no such size: *"Topsoil doesn't come in 1 cu yd — it comes in 1 yd, 2 cu ft, Bag."* — nothing changed *(2026-10-02, #700 — replied "I've updated the material" and changed nothing. Sizes match whatever their case)* |
| `rename size 1 cu yd of Topsoil to 2 cu yd` | `update_material` fields.size fields.rename_size_to | ✅ Topsoil has no such size: the same reply — nothing changed *(2026-10-02, #700)* |
| `how much is {material} in the {size} size?` | `get_material` size field=price | ✅ that size's price and cost |
| `find material {material} with size {size}` | `get_material` size | ✅ that size's price and cost |
| `show all sizes for {material}` / `what sizes does {material} come in?` | `get_material` field=sizes | ✅ *"Black Mulch comes in 2 sizes: 2 cu ft at 4.40, 1 yd at 38.50."* |
| `what sizes do they come in?` [material_focus] | `get_material` field=sizes | ✅ the material in focus (asked about first once stale) *(2026-10-04, #764 — they / these / those and a trailing "please" were read as a material's name: "No material found matching 'They'")* |
| `remove size 1 yd from those` / `remove size 1 yd from these` / `remove size 1 yd from it please` [material_focus] | `update_material` fields.remove_size fields.size | ✅ the material in focus (asked about first once stale) *(2026-10-04, #764)* |
| `what sizes does it come in?` [task_focus] | ask | ✅ *"Only materials have sizes — which material do you mean?"* — the same material question, and its reply finishes the request *(2026-10-04, #763 — it asked "Which material do you mean?" with no reason. Falling through instead reached the task creator, so the question stays)* *(2026-10-12 — the planner said only "Which material do you mean?")* |
| `what sizes does it come in?` [contact_focus] | ask | ✅ the same, with a contact in focus *(2026-10-04, #763)* |
| `what sizes does it come in?` [est] | ask | ✅ the same, with an estimate in focus *(2026-10-04, #763)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `change its price to 5` on a material with several sizes → *"which size?"* → `2 cu ft` | the change, on that size | ✅ rule *(2026-09-27 — the answer didn't resume the edit)* |
| `remove size 1 yd from it` with nothing in focus → *"Which material do you mean?"* → `Show Stone` / `no, Black Mulch please` | the change, on that material — a reply that is one of the company's materials answers however it reads | ✅ rule *(2026-09-28)* |
| … → `No. 57 Stone` / `The Good Stuff` — a name that opens with words a reply is cleaned of, beside materials the cut name also matches | the change, on the material named exactly | ✅ rule *(2026-09-29, #775 — "Multiple materials matched", and nothing changed)* |

**Invariants:**
- **Last-size delete refusal** — cannot remove the only remaining size on a material. Copy: *"I can't remove the last size from this material — it needs at least one size. Add another size first, or delete the material entirely if that's what you mean."*
- **Add-size requires BOTH cost and unit** — `add size {size} to {material} with cost $8` (no unit) refuses and prompts for the unit. Same if cost is missing. A unit is resolved to one of the company's units; a name it doesn't have is answered, never created (#681).
- A message that names an estimate or work item is never a size command — those have their own grammar (§1.5.5).
- **A size is found however its stored label ends** — the user's `60 in` finds `60 in.`, `4` finds `4"` — and the label stays as stored; replies say the stored label. When size words name **more than one** stored label (`4` and `4"`), every size-named op — price, cost, unit, add, a size read (today's and the planner's `get_material` with a size), remove, rename — is refused with nothing written: *"Topsoil has 2 sizes called 4 — change them on the Materials page, so I don't touch the wrong one."* *(2026-10-17, review #11 — a price on `4"` repriced `4`; only remove and rename refused. #12 — the planner's size read needed the exact label)*

## 4.9 Material gaps

| Phrasing | Plan | Status |
|---|---|---|
| `How much does {material} cost?` | `get_material` field=price | ✅ *(closed in xfail-wave-3 Workstream B — non-possessive cost-query rule in orchestrator)* |
| `list materials under $10` | `list_materials` filter.price.under=10 | ✅ *(closed in xfail-wave-3 Workstream B — `_parse_price_range_filter` in `agents/material/text_helpers.py` filters the list response by `under/over/below/above $N`)* |
| `rename size {size} to 1 cubic yard for {material}` | `update_material` fields.size fields.rename_size_to | ✅ *(closed in xfail-wave-3 Workstream B — orchestrator `_match_size_scoped_material_op` rule routes the rename verb)* |
| `show all sizes for {material}` | `get_material` field=sizes | ✅ lists every size *(2026-09-27; see §4.8)* |
| `how much does {size} of {material} cost?` / `what is the price of {size} of {material}?` | `get_material` size field=price | ✅ *(May expansion — "of" form cost query pattern)* |
| `what category is material {material}?` / `what category is {material}?` | `get_material` field=category | ✅ *(May expansion — `_match_field_specific_query` before help classifier)* |

*Answers to a question Maple asked:*

| Phrasing | Plan | Status |
|---|---|---|
| `Clear Coat` | conversation `ref-category-named-like-a-command` | ✅ the planner handles it — was a gap: a category the company has, named in reply to *"What category …?"*, though it opens with a command verb *(deferred 2026-09-29 — name-answers plan §7)* |
| `Black Mulch 2 cu ft` | conversation `ref-material-size-named-in-reply` | ✅ the planner handles it — was a gap: the material and its size in reply to *"which size should I change?"*; today's read it as a new size *(deferred 2026-09-29 — name-answers plan §7)* |

## 4.10 Qualifier list — "what {X} materials do I have?" *(2026-06-02)*

A qualifier `{X}` between the lead-in and the `materials` noun is matched as a
**substring against the material name OR its category name** (case-insensitive).
`_extract_list_qualifier` lifts `{X}` out of the phrasing (rule tier) and
`_find_materials_by_name_or_category` does the OR-match. A bare list with no
qualifier (`what materials do I have?`, §4.2) still lists everything — the
generic-word guard drops a non-qualifier capture.

| Phrasing | Plan | Status |
|---|---|---|
| `what mulch materials do I have?` / `show me my mulch materials` / `list my mulch materials` / `do I have any mulch materials?` / `which mulch materials do I have?` | `list_materials` filter.text=mulch | ✅ name ∪ category substring |
| `how about mulch materials?` / `and mulch materials?` | `list_materials` filter.text=mulch | ✅ *(follow-up phrasings — the "how about" lead-in would otherwise trip `is_help_query`, so the orchestrator `_match_material_list_filter` fast-path routes these before the help classifier. It reuses the agent's `_LIST_QUALIFIER_PATTERN` so routing and qualifier extraction never drift.)* |
| `what about mulch materials?` | `list_materials` filter.text=mulch | ✅ *(follow-up phrasings — the "how about" lead-in would otherwise trip `is_help_query`, so the orchestrator `_match_material_list_filter` fast-path routes these before the help classifier. It reuses the agent's `_LIST_QUALIFIER_PATTERN` so routing and qualifier extraction never drift.)* |
| `how many masonry materials do I have?` | `list_materials` count filter | ✅ *(count-by-category — resolves a whole-word category for count queries; falls back to all when {X} isn't a category)* |

**Disambiguation:** `material units` / `material categories` / `material types` are NOT treated as "{X} materials" lists — a negative lookahead on `_LIST_QUALIFIER_PATTERN` keeps those routing to their help/enum or category handlers.

## 4.11 Create, one question at a time *(2026-09-27)*

A create that is missing details asks for the next one alone, remembers which, and reads a bare reply as its value (`agents/conversation/create_questions.py`, §10.6). It asked for everything at once ("To create a material, I'll need: category, unit, size, price.") and ignored "Bulk Materials". A material is asked for its **cost**: the server prices the size from the company's material markup (see the pricing model in CLAUDE.md), so a create that gives a cost and no price no longer asks for a price.

*Not yet in the Plan format — several turns, each reply answering the question before it (phase 3):*

| Turn | Maple | Status |
|---|---|---|
| `create a new material called River Rock` | *"Which category does River Rock go in? You have: Bulk Materials, Masonry, Soil."* | ✅ rule |
| `Bulk Materials` | *"What unit is River Rock sold by? You have: Bag, Cubic Yard, Each."* | ✅ rule |
| `Bag` | *"What size does River Rock come in? For example: 2 cu ft, or Standard."* | ✅ rule |
| `2 cu ft` | *"What does River Rock cost you? I'll set the price from your material markup."* | ✅ rule |
| `5` | created — cost 5.00, price 5.50 at a 10% markup | ✅ rule |
| `$1,200` / `$2 000 a pallet` / `$2 000 in total` | one number — 1200, 2000, 2000 | ✅ rule *(2026-09-27 #16)* |
| `$20 100lb bag` / `$20 100 lb bag` | cost 20 — a size after the cost is not a thousands group of it | ✅ rule *(2026-10-03, #760 — read as 20100)* |
| a category or unit the company doesn't have | says so and asks again, never creates one (#681) | ✅ rule |

*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `Clear Coat` | conversation `ref-category-named-like-a-command` | ✅ the planner handles it — was a gap: a category the company has whose name opens with a command verb is the answer; today's `bare_answer` refused it *(deferred 2026-09-29 — name-answers plan §7)* |
| `Clear Stone` | conversation `ref-material-named-like-a-command` | ✅ the planner handles it — was a gap: the name in reply to *"What's the material called?"*, then the category is asked *(deferred 2026-09-29 — name-answers plan §7)* |
| `add the materials on this invoice to my catalog` [none+invoice] | `create_material` | ✅ the first two planned as creates (an invoice can have more lines than a plan has actions — review 2026-10-21 #73); several material creates in one plan are refused — *"I add one material at a time — tell me the first one to add."* — never one question for all their details (D4, Simon 2026-10-19: there's no invoice in the app) — G18 (gap plan 2026-10-19, closed the same day). The prompt line once quoted the refusal and the model made it "one task at a time" for a to-do list too; it now says plan the first two creates *(live run 2026-10-20; 2026-10-21, 18/18 re-plans with a 7-line invoice)* |

## 4.12 Catalog figures *(2026-10-01, metrics plan Phase 4)*

Answered by the router pre-handler `agents/conversation/catalog_figures.py`
from `services/catalog_metrics.py` — every number from a function, as for the
estimate metrics (§1.12). Prices are compared **within a unit** and never
averaged across units (decision 23); a size with no price is left out and the
reply says how many.

| Phrasing | Plan | Status |
|---|---|---|
| `how many materials per category?` / `how many materials do I have in each category?` / `materials by category` / `how many materials does each category have?` | `catalog_figure` kind=materials_per_category | ✅ *"Your materials by category:\n- Bulk Materials: 2 materials\n- Masonry: 1 material\n- Soil: 1 material\n4 materials in 3 categories."* — every category, an empty one included *(it answered the number of categories)* |
| `what's my most expensive material?` / `which material is the priciest?` / `which material costs the most?` | `catalog_figure` kind=priciest_material | ✅ *"Your most expensive material by price is Pea Gravel (1 yd) at $49.50 per Cubic Yard."* — the size and its unit; it is "the first one" next *(a guide answer with no figure)* |
| `what's my cheapest material?` | `catalog_figure` kind=cheapest_material | ✅ the same, the cheapest *(a guide answer with no figure)* |
| `what's my average material price?` / `what's the average cost of my materials?` | `catalog_figure` kind=average_material_price | ✅ *"Average material price, by unit:\n- Bag: $4.40 across 1 size\n- Cubic Yard: $40.33 across 3 sizes\n- Each: $2.75 across 1 size\nPrices in different units aren't averaged together."* *(a guide answer)* |
| `what's the price of Topsoil?` | `get_material` field=price | ✅ one material's price — not a catalog figure |
| `how much does mulch cost?` | `list_materials` filter.text=mulch | ✅ the materials called mulch, with their prices — not a catalog figure |
| `how many materials do I have?` | `list_materials` count | ✅ the count — not a catalog figure |
| `list my material categories` | `list_material_categories` | ✅ the categories — not a catalog figure |
| `what's the average price of my mulch?` / `most expensive material in Bulk Materials` | `catalog_figure` within | ✅ the planner handles it — was a gap: a category or material narrowing: not read; the planner (Dev) says the figures are the whole catalog's and offers that one, never passing it off as the narrowed one *(Phase 4 — company-wide figures only)* |

**Open gaps:** #768 (a lead word before a size command) (see [code-review-followups.md](code-review-followups.md)). #775 was resolved 2026-09-29; #763 and #764 on 2026-10-04. Resolved 2026-09-27: #495, #674, #675, #676, #677, #678, #680, #681, #682, #683, #690, #694, #697; #700 on 2026-10-02; #701 on 2026-10-03 (a failed size command says so instead of a server error); #760 on 2026-10-03.

---

# 5. People (roles) — a.k.a. Labor

Labor = catalog of **role definitions** (Landscaper, Foreman, Operator). Individuals go under Contact.

## 5.1 Direct imperatives

| Phrasing | Plan | Status |
|---|---|---|
| `create a new labour role` | `create_labour` | ✅ |
| `create a new role called {role}` | `create_labour` fields.name | ✅ |
| `list all labour roles` / `list my roles` | `list_labours` | ✅ |
| `delete the labour role {role}` / `delete the {role} role` | `delete_labour` | ✅ |

## 5.2 Casual phrasings

| Phrasing | Plan | Status |
|---|---|---|
| `show me my labour roles` / `what labour roles do I have?` | `list_labours` | ✅ |
| `pull up labour role {role}` / `show me the {role} role` | `get_labour` | ✅ |
| `what's the rate for {role}?` | `get_labour` field=rate | ✅ |

Fixed 2026-09-27 (#693): the name extractor read "S" out of `show me my labour roles` and `list all labour roles` ("S Do I Have" from `what labour roles do I have?`) and filtered the list by it.

## 5.3 Possessive

| Phrasing | Plan | Status |
|---|---|---|
| `show me {role}'s details` | `get_labour` | ✅ |
| `tell me {role}'s rate` | `get_labour` field=rate | ✅ |
| `what's {role}'s cost?` | `get_labour` field=wage | ✅ a role's cost is its average wage |
| `update {role}'s record` | `update_labour` | ✅ no field said: Maple asks which field |

## 5.4 Count

| Phrasing | Plan | Status |
|---|---|---|
| `how many labour roles do I have?` / `count my labour roles` / `total number of labour roles` | `list_labours` count | ✅ |

## 5.5 Filter / find

| Phrasing | Plan | Status |
|---|---|---|
| `find labour roles named Foreman` / `search for labour roles matching Foreman` | `list_labours` filter.name=Foreman | ✅ |
| `show labour roles in outdoor` | `list_labours` filter.name=outdoor | ✅ roles have no division or category: the name filter — G27 (gap plan 2026-10-19, closed the same day) |

## 5.6 Field-targeted update

| Phrasing | Plan | Status |
|---|---|---|
| `change the cost of {role} to $50` / `update the cost on {role} to $50` / `set {role}'s cost to $50` | `update_labour` fields.wage=50 | ✅ |
| `change role {role}'s wage to 45` | `update_labour` fields.wage=45 | ✅ *(2026-09-27)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Status |
|---|---|
| `update role {role}` → *"which fields?"* → `wage` → `45` | ✅ rule *(2026-09-27 — it asked "which labor role?")* · 🤖 planner: the field named, its value asked *(2026-10-12 — it looped)* |

## 5.7 Verbless

| Phrasing | Plan | Status |
|---|---|---|
| `{role}` / `I want the details for {role}` / `tell me about {role}` | `get_labour` | ✅ DOMAIN_HINTS include role names |

## 5.8 Role field queries (May expansion)

"What's the X for role Y?" phrasings route to `get_labour` via `_match_field_specific_query` in the orchestrator (runs before `is_help_query`).

| Phrasing | Plan | Status |
|---|---|---|
| `what's the average wage for the role {role}?` | `get_labour` field=wage | ✅ |
| `what's the rate for the role {role}?` | `get_labour` field=rate | ✅ |
| `what's the labor burden for the role {role}?` / `what's the unbillable rate for the role {role}?` | `get_labour` | ✅ |

Note: "labor burden" and "unbillable rate" are company-level settings, not per-role fields. The Labour Agent's get response shows the role's Avg. Wage and computed Rate. The explanation of how rate is computed (wage + unbillable% + labor burden%) is provided when users attempt to edit rate directly.

## 5.8a Standard roles (2026-10-21)

The 3Maples standard roles are each company's own role records tagged with a
standard key: their name, responsibilities and unit are the standard list's,
their wage is the company's. Role names are unique within a company (case and
spacing ignored, hidden roles included). A hidden role is out of Maple's lists
and name lookups; estimate lines keep it.

| Phrasing | Plan | Status |
|---|---|---|
| `set Foreman's wage to 45` / `change the cost of Foreman to $45` | `update_labour` fields.wage=45 | ✅ a standard role's wage is the company's; its Rate follows. Owners and Admins only: a Member is told *"Only owners and admins can set role wages."*, nothing written; a Member's `create a new role called Arborist` likewise gets *"Only owners and admins can add people roles."* before any question (unanswered tracker: `not_permitted` `role`) |
| `rename Foreman to Field Boss` | `update_labour` fields.name | ✅ Foreman being a standard role, nothing is written: *"Foreman is a standard role, so its name, responsibilities and unit can't change. You can still change its wage."* (unanswered tracker: `policy` `standard_role`) |
| `make Foreman daily` | `update_labour` fields.unit | ✅ refused the same way: a standard role's unit is the standard list's |
| `delete the Foreman role` | `delete_labour` | ✅ asked first; for a standard role the yes **hides** it: *"I've hidden the standard role 'Foreman' from your people roles."* |
| `create a new role called Crew Lead` | `create_labour` fields.name | ✅ with a Crew Lead role already there (hidden ones count), nothing is written: *"A role named 'Crew Lead' already exists."* — and, when that role is hidden, *"It's hidden — turn on Show Hidden on the People page to find it."* (`policy` `name_taken`); a rename to a taken name is refused the same way |

A hidden role is not found by name ("show me the Foreman role" with Foreman
hidden answers as for any role the company doesn't list); show it on the
People page.

## 5.9 People gaps

| Phrasing | Plan | Status |
|---|---|---|
| `list my roles` | `list_labours` | ✅ lists every role *(2026-09-27 — both were unknown on the rules tier)* |
| `create a new role called {role}` | `create_labour` fields.name | ✅ creates the role *(2026-09-27 — both were unknown on the rules tier)* |
| `show me the Heavy Equipment Operator` | `get_labour` | ✅ anything about the "Heavy Equipment Operator" role is read, created and edited as a role *(2026-09-27, #693 — the equipment refusal matched the word "equipment"; an equipment operator is a person)* |

*An answer to a question:*

| Phrasing | Plan | Status |
|---|---|---|
| `Lead Hardscape` | conversation `ref-role-picked-by-name-from-a-menu` | ✅ the planner handles it — was a gap: the reply to *"More than one role matches that"*; today's question kept no record, so the reply was read from scratch *(deferred 2026-09-29 — name-answers plan §7)* |

## 5.10 Create, one question at a time *(2026-09-27)*

As for materials (§4.11): `create a new role called Arborist` → *"What's the average wage for Arborist? For example: $30 an hour."* → `30` → *"Is Arborist paid hourly, daily or per job?"* → `hourly` → created. `add a labour role` asks *"What's the role called?"* first — a name that opens with a verb (`Load Truck`) is the name (2026-09-30, phase 8), while a whole request (`list my roles`) is still a request; `$30 an hour` answers the wage and the unit together. It said "To create a role, I'll need: unit, wage." and a bare "30" asked again. ✅

Cross-resource phrasings (e.g. `which properties need a {role}?`) are tracked under §8.

## 5.11 Role figures *(2026-10-01, metrics plan Phase 4)*

As for materials (§4.12): rates and wages are compared within a unit —
an hour against an hour, a day against a day — and a role with no rate is
left out and counted.

| Phrasing | Plan | Status |
|---|---|---|
| `what's my most expensive role?` / `which role has the highest rate?` / `which role costs the most?` | `catalog_figure` kind=highest_role field=price | ✅ *"Your most expensive role by rate is Heavy Equipment Operator at $64.80 an hour."* — one per unit when the roles are in several (*"…, by unit:\n- Hourly: Foreman at $60.00 an hour\n- Daily: Operator at $480.00 a day"*); it is "the first one" next *(help about **contact** roles)* |
| `what's my cheapest role?` | `catalog_figure` kind=lowest_role field=price | ✅ the same, cheapest by rate *(help about **contact** roles)* |
| `who's my highest-paid role?` / `which role gets paid the most?` | `catalog_figure` kind=highest_role field=cost | ✅ the same by average wage *(help about contact roles)* |
| `which role has the lowest wage?` | `catalog_figure` kind=lowest_role field=cost | ✅ the same by average wage — *"Your lowest-paid role by wage is Landscaper at $25.00 an hour."* *(help about contact roles)* |
| `what's the average wage of my roles?` | `catalog_figure` kind=average_role field=cost | ✅ *"Average wage of your roles: $36.67 an hour across 3 roles."* — per unit when there are several *(help about contact roles)* |
| `what's the average rate across my roles?` | `catalog_figure` kind=average_role field=price | ✅ per unit when there are several *(help about contact roles)* |
| `what's my average labour rate?` | `catalog_figure` kind=average_role field=price | ✅ the roles' average rate — set right from the words when the model refuses it as a Rate setting (`as_asked_reads`) — G25 (gap plan 2026-10-19, closed the same day) |
| `what's the average wage for Foreman?` | `get_labour` field=wage | ✅ that role's wage (§5.8) — not a figure across roles |

**Open gaps:** none tracked (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #674, #675, #676, #677, #678, #682, #683, #690, #693.

---

# 6. Templates

Templates are reusable estimate blueprints — a predefined set of materials, activities, and cost parameters that can be applied when creating estimates. Managed via the Templates page in the portal. The API supports full CRUD plus a duplicate operation (`POST /templates/id/{id}/duplicate`).

Key fields: `name` (required, unique per company), `description`, `division`, `recurring` (bool), `profit_margin`, `overhead_allocation`, `labor_burden`, `tax`, `size` + `unit` (baseline dimensions), and embedded `materials` / `activities` lists.

## 6.1 Direct imperatives

| Phrasing | Plan | Status |
|---|---|---|
| `list all templates` | `list_templates` | ✅ |
| `delete the template {template}` | `delete_template` | ✅ |

Template **creation** is refused — see §9.5. Users must create templates through the Templates page in the portal UI.

## 6.2 Casual phrasings

| Phrasing | Plan | Status |
|---|---|---|
| `show me my templates` / `what templates do I have?` | `list_templates` | ✅ |
| `pull up template {template}` | `get_template` | ✅ |

## 6.3 Possessive

| Phrasing | Plan | Status |
|---|---|---|
| `show me {template}'s details` / `what's {template}'s description?` / `what's the description of the {template} template?` | `get_template` | ✅ *(2026-09-27)* |

## 6.4 Count

| Phrasing | Plan | Status |
|---|---|---|
| `how many templates do I have?` / `count my templates` / `total number of templates` | `list_templates` count | ✅ |

## 6.5 Filter / find

| Phrasing | Plan | Status |
|---|---|---|
| `find templates named Driveway` / `search for templates matching Driveway` | `list_templates` filter.name_contains=Driveway | ✅ the list is narrowed to templates whose name contains it (*"Here are your templates matching "Paver":"*), or says none match; `show me the first one` picks from it *(2026-09-27 — every template was listed)* |
| `which templates have patio in the name?` | `list_templates` filter.name_contains=patio | ✅ as above *(2026-09-27 — "which templates …" went to the user guide)* |

Template **update** and **duplicate** are refused — see §9.5. Users must edit and copy templates through the portal UI.

## 6.6 Verbless

| Phrasing | Plan | Status |
|---|---|---|
| `{template}` | `get_template` | ✅ a bare template name, written like a name *(2026-09-27)* |
| `show me the {template} template` | `get_template` | ✅ *(2026-09-27 — it asked "which template?")* |
| `delete the {template} template` | `delete_template` | ✅ *(2026-09-27 — it asked "which template?")* |
| `I want the details for {template}` | `get_template` | ✅ |
| `tell me about {template}` / `tell me about the {template} template` | `get_template` | ✅ *(2026-09-27)* |
| `tell me about Driveway Maintenance` | `get_template` | ✅ a template's name, no "template", that no estimate has: its details *(2026-10-11, #843 — read as an estimate's title)* |
| `delete Driveway Maintenance` | `delete_template` | ✅ a template's name, no "template", that no estimate has: its delete, asked first *(2026-10-11, #843 — read as an estimate's title)* |
| `update Driveway Maintenance's description` | refuse `template_edit` | 🛑 a template's name, no "template", that no estimate has: the template-edit refusal *(2026-10-11, #843 — read as an estimate's title)* |

## 6.7 Apply template to estimate

| Phrasing | Plan | Status |
|---|---|---|
| `use template {template} in the estimate {EST}` / `apply template {template} to {EST}` / `use the {template} template for {EST}` [est] | `apply_template` | ✅ |
| `apply {template} to the estimate` [est] | `apply_template` | ✅ the estimate open |
| `apply template {template} to estimate {title}` | `apply_template` | ✅ *(2026-06-09 — title-aware: targets the named estimate over `active_estimate_code`. A named estimate that **doesn't exist** is REFUSED with a warning — it does NOT silently create a new estimate under that name.)* |
| `create an estimate from template {template}` | `create_estimate` template | ✅ *(creates a new draft estimate and applies the template as a work item — the no-named-target bootstrap path)* |

### Template-driven create (2026-06-02) — skips AI generation

When a **create-estimate** request names a template, `delegate_create_estimate` detects it (`detect_template_in_create_request`) and routes to template instantiation instead of AI generation — no material/activity questions. Linear scaling by job size when the template has a **baseline** (`size` + `unit`).

| Phrasing | Plan | Status |
|---|---|---|
| `create an estimate and use the {template} template` | `create_estimate` template | ✅ a template with no baseline: a draft is created, the template applied as one work item, verbatim (1×); property context linked |
| `create an estimate, 600 sq ft, using the {template} template` | `create_estimate` template template_size=600 template_size_unit | ✅ a template with a baseline and the size in the request: scaled linearly (`factor = job_size ÷ baseline_size`); size taken from the request, not re-asked |
| `create an estimate using the {template} template` | `create_estimate` template | ✅ a template with a baseline and no size: asks "What's the size of this job (in {baseline unit})?" (`pending_template_size`), then scales on reply |
| `create an estimate at {property} from the {template} template` | `create_estimate` property template | ✅ the planner gets it right — today's pipeline: the property named isn't read (only the page's). The planner links it, and keeps it across the size question *(2026-10-09, switchover phase 6b)* |
| `apply the {template} template to {EST} at 400 sq ft` [est] | `apply_template` size=400 size_unit | ✅ the planner gets it right — today's pipeline: added at the baseline, the size unread. The planner scales it (a unit that can't convert adds nothing and says why) *(2026-10-09, switchover phase 6b)* |

*Not yet in the Plan format — answers to the size question (phase 3):*

| Phrasing | Behavior | Status |
|---|---|---|
| reply with size in a **convertible** unit (sq yd↔sq ft, lin yd↔lin ft) | Converted to the baseline unit, then scaled. | ✅ rule |
| reply with an **incompatible** unit (area vs length) | Re-asks for the size in the baseline's unit. | ✅ rule |
| `No` / `skip` to the size question | Instantiate at the baseline (1×) and proceed (no cancel). | ✅ rule · 🤖 planner: left to the template flow, which reads it so *(2026-10-12 — kept as the planner's, "no" cancelled)* |
| `cancel` / `never mind` to the size question | Cancels the estimate request. | 🛑 cancel |

**Scaling** (`agents/estimate/template_scaling.py`): multiplies material/labour/equipment quantities, activity effort, and the work-item `sub_total` by the factor; prices/rates unchanged. Linear across all line items — no per-item fixed-fee exemption. Pre-handler: `handle_pending_template_size` in `routers/agent_helpers/template_estimate.py`.

## 6.8 Template gaps

Orchestrator routing, refusal guard, and Template Agent are implemented. Possessive (§6.3) and most verbless (§6.6) phrasings are rule-tier since 2026-09-27: the router rewrites a template's exact name kind-first (`catalog_names.py`). Template creation, update, and duplicate are explicitly refused (§9.5).

Additional cross-resource phrasings (e.g. `which templates include {material}?`) are future candidates — not tracked here yet.

| Phrasing | Plan | Status |
|---|---|---|
| `show me a template` | conversation `ref-template-named-in-reply` | ✅ the planner handles it — was a gap: `Remove Sod` in reply to *"Which template would you like to see?"*, a name that opens with a command verb *(deferred 2026-09-29 — name-answers plan §7)* |
| `delete a template` | conversation `ref-template-to-delete-named-in-reply` | ✅ the planner handles it — was a gap: `Remove Sod` in reply to *"Which template should I delete?"* is asked to confirm, never shown; today's question kept no record |

**Open gaps:** none tracked (see [code-review-followups.md](code-review-followups.md)). Resolved 2026-09-27: #675, #677, #681, #695; #704 on 2026-10-03 (`delete template Old Patio, it's a duplicate` is Old Patio, not the template in focus — the focus is used only when no template is named, and an aside after a comma is dropped only when the whole name matches no template, so `show template Patio, Large` is still that template); `find templates named X` (§6.5). #807 on 2026-10-04: a courtesy or timing word after the noun is no name — `show me that template now` / `… please` / `… again` is the template in focus, and `show template Old Patio please` is Old Patio.

---

# 7. Tasks

Field-capture to-dos (`models/task.py`) with a title, capture date, optional description / due date / property link / assignee, and a **per-company status** (`TaskStatus` documents — defaults `To Do` | `In Progress` | `Done`; users can rename/add). The Tasks feature is flag-gated (`settings.tasks_enabled`); Maple refuses gracefully when it's off. Free-plan companies have a standing 50-task cap (archived tasks count; only hard delete frees a slot).

Token conventions: `{task}` = a task title (e.g. `fix the fence gate`); `{status}` = a company task-status name; `{email}` = an assignee email.

## 7.1 Direct imperatives

| Phrasing | Plan | Status |
|---|---|---|
| `create a task called {task}` | `create_task` fields.title | ✅ |
| `create a task with title {task}` / `title: {task}` | `create_task` fields.title | ✅ *(2026-07-22 smoke-test fix)* |
| `create a task with title {task}. Add the following notes: {text}` | `create_task` fields.title fields.notes_append | ✅ title and description in one turn *(the notes/description clause is split off before title extraction and stored as the task description)* |
| `add a task to check the retaining wall` / `create a new task to: {text}` / `new task: {text}` | `create_task` | ✅ *(2026-07-25 — **content-is-description rule**: with no title cue, the body becomes the DESCRIPTION and the title is derived from it. Previously the "to …" phrase became the title, and a phrasing like `create a new task to: {text}` put the whole command line in the title.)* |
| `create a task with the notes: {text}` / `Create a task. Add the following notes: {text}` | `create_task` fields.notes_append | ✅ notes, **no** title — creates immediately with a **title derived from the notes** *(2026-07-25 — first sentence of the notes, politeness/reminder preamble stripped ("remind me to call Bob tomorrow" → "Call Bob tomorrow"), truncated to 60 chars on a word boundary; full notes kept as the description. The reply says the title came from the notes so the user can rename it.)* |
| `list my tasks` | `list_tasks` filter.assignee=me | ✅ the user's own tasks (§7.5) |
| `show me the {task} task` | `get_task` | ✅ |
| `create a task to call Bob tomorrow and assign it to me` / `add a task to trim the hedge due Friday and assign it to Jordan` [task_focus] | `create_task` fields.due_date fields.assignee | ✅ *(2026-09-27 — a create's tail sets fields: `assign it to` me / an email / a teammate's name, `mark it` / `status:` a status, a date phrase (`tomorrow`, `due Friday`, `by next week`, `on Oct 3`) as the due date. Instructions come out of the note; the date stays in it. Before, the trailing "assign it to …" routed the whole message to an edit of another task.)* |
| `create a task to fix the side gate at the Elm House property` / `add a task to rake the leaves at 12 Oak St` | `create_task` fields.property | ✅ linked to the property *(2026-09-27 — "at the X property" or an "at …" tail that names one property; the words stay in the note)* |
| `create a task to pick up mulch for Jordan` / `create a task to order gloves for the crew` | `create_task` | ✅ linked to no property — a bare "for …" links only an address (`for 12 Oak St`) or "the … property" *(2026-10-01, #712 — it linked "14 Jordan Rd")* |
| `is it due Friday?` [task_focus] | `get_task` | ✅ not a due-date change — a question never writes; `could you push it to Friday?` still moves it *(2026-10-01, #710 — it set the date)* |
| `due today?` [task_focus] | `list_tasks` filter.due=today | ✅ not a due-date change — a question never writes; `could you push it to Friday?` still moves it *(2026-10-01, #710 — it set the date)* |
| `push the fence task to Friday?` | ask | ✅ not a due-date change — a question never writes *(2026-10-01, #710 — it set the date)* |
| `create a task to call the supplier and assign it to Zed` [task_focus] | `create_task` fields.assignee=Zed | ✅ no such teammate — the task is made, assigned to you, and the reply says Zed wasn't found *(2026-09-27 — a clause Maple can't apply is reported, never dropped)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `create a new task` (no title, **no** notes) → *"What should the task say?"* → bare reply | `create_task` field-then-value flow (§10.1) — the reply is the task's text, and its title derives from it; inline notes from the first turn are kept. A reply that reads as a request (`Create estimate for Bob`) is still the text; only another task create (`create a task to …`) starts over | ✅ rule *(only reached when there are no notes to derive a title from, or the notes yield nothing usable — e.g. `notes: ...`. 2026-09-30, #470 — it asked "What should the task be called?", naming a field the portal no longer has, and re-asked on a request-shaped reply)* |
| `delete the {task} task` → *"…are you sure?"* → `yes` | `delete_task` → Task Agent (manager-only, confirm first) | ✅ rule *(2026-09-27 — the "yes" now deletes; #692)* |

## 7.2 Casual phrasings

| Phrasing | Plan | Status |
|---|---|---|
| `jot down a task to order more mulch` | `create_task` | ✅ *(2026-09-27)* |
| `remind me to call Bob tomorrow` / `set a reminder to call Bob tomorrow` / `don't let me forget to call Bob tomorrow` | `create_task` fields.due_date | ✅ due tomorrow *(2026-09-27 — a reminder is a task, whatever it is about)* |
| `add order more mulch to my to-do list` / `put order more mulch on the to do list` / `new to-do: order more mulch` / `create a reminder to order more mulch` | `create_task` | ✅ *(2026-09-27)* |
| `I need to remember to winterize the irrigation` | `create_task` | ✅ the planner handles it — was a gap: |
| `pull up my tasks` / `what tasks do I have?` | `list_tasks` | ✅ |

## 7.3 Possessive

Bare-title possessives carry no "task" keyword for the rule tier to anchor on, and the 2026-07-22 Tier-2 run showed the LLM doesn't rescue them either (same bare-title gap class as materials/contacts pre-Phase-2b). Adding `the {task} task's …` (with the keyword) routes fine via §7.1/§7.6 shapes.

| Phrasing | Plan | Status |
|---|---|---|
| `what's the {task} task's due date?` | `get_task` | ✅ the planner handles it — was a gap: (bare-title form; keyword form routes ✅) |
| `update {task}'s description` | `update_task` | ✅ the planner handles it — was a gap: |
| `show me {task}'s details` | `get_task` | ✅ the planner handles it — was a gap: |

## 7.4 Count

| Phrasing | Plan | Status |
|---|---|---|
| `how many tasks do I have?` / `count my tasks` / `total number of tasks` | `list_tasks` count | ✅ |
| `how many tasks are overdue?` | `list_tasks` count filter.overdue | ✅ *"You have 1 overdue task."* — every §7.5 filter applies to a count too *(2026-09-27, #687)* |

### 7.4.1 Counts by person and by property *(2026-10-01, metrics plan Phase 4)*

Counted by one `$group` (`services/task_metrics.py`) over the tasks the list's
own filters match (`list_filters.task_group_of`). **Open tasks** unless
"overdue", "all", a status or a due window is said (decision 22); the
"Unassigned" / "No property" row is always last, and never "the most".

| Phrasing | Plan | Status |
|---|---|---|
| `how many tasks does each person have?` / `how many open tasks does everyone have?` / `tasks by person` / `how many tasks are assigned to each person?` | `task_count` group_by=assignee | ✅ *"Your open tasks by assignee:\n1. Jordan Crew — 2 tasks\n2. Sam Owner — 1 task\n3. Unassigned — 1 task\n4 open tasks in all."* *(a flat list or one total; "each person" was looked up as a teammate; "tasks by person" was unknown)* |
| `how many overdue tasks does each person have?` / `overdue tasks by assignee` | `task_count` group_by=assignee filter.overdue | ✅ the same for overdue tasks |
| `all tasks by assignee` | `task_count` group_by=assignee filter.include_done | ✅ every task not archived *(2026-10-11, #842 — "all tasks" is `include_done`; it counted open tasks only)* |
| `how many tasks per property?` / `how many tasks does each property have?` / `count my tasks by property` | `task_count` group_by=property | ✅ *"Your open tasks by property:\n1. Elm House — 2 tasks\n2. 12 Oak St — 1 task\n3. No property — 1 task\n4 open tasks in all."* — properties link to their page and are "the first one", "the second one" next |
| `who has the most tasks?` | `task_count` group_by=assignee most | ✅ a tie names both (*"… have the most open tasks — 2 each."*) |
| `who has the most overdue tasks?` | `task_count` group_by=assignee most filter.overdue | ✅ *"Jordan Crew has the most overdue tasks — 1."* |
| `which property has the most tasks?` | `task_count` group_by=property most | ✅ *(it was help)* |
| `who has the fewest tasks?` | `task_count` group_by=assignee fewest | ✅ the fewest, counting teammates with none — *"Jordan Crew and Sam Owner have no open tasks."* when any have none, else *"Dana Lee and Jordan Crew have the fewest open tasks — 2 each."* *(2026-10-11, #842; 2026-10-13 idle teammates)* |
| `which teammates have no tasks?` | conversation `ref-teammates-with-no-tasks` | ✅ the planner handles it — was a gap: the company's teammates with none of the tasks counted — *"Jordan Crew and Sam Owner have no open tasks."*; "who has the fewest tasks?" counts them too *(2026-10-13)* |
| `rename the fence task to edging by property` / `mark the task sort tools by person as done` | `update_task` | ✅ the edit — a group is read only in a question or list request *(Phase 4 review #1 — they became grouped counts and the edit was lost)* |

## 7.5 Filter / find

| Phrasing | Plan | Status |
|---|---|---|
| `what tasks do we have at {property}?` / `tasks for the {property} property` | `list_tasks` filter.property | ✅ *(2026-09-27; a property that doesn't match is answered — "I couldn't find a property called …")* |
| `tasks at Next Door Landscaping` / `tasks at This Old House` | `list_tasks` filter.property | ✅ at that place — "this" / "next" make a due window only before week / month / year (`tasks for next week`) *(2026-10-04, #804 — a place starting "Next" or "This" was never read, and every task was listed)* |
| `tasks assigned to {email}` / `tasks assigned to me` / `tasks assigned to Jordan` | `list_tasks` filter.assignee | ✅ *(2026-09-27 — the email is read whole (it stopped at the first ".", #687); a teammate by first, last or full name; an unknown name is answered, never dropped)* |
| `Jordan's tasks` / `Elm House's tasks` | `list_tasks` filter.for_name | ✅ a place or a teammate, tried in that order — "Elm House's tasks" are the property's, "Jordan's" the teammate's *(2026-10-13 review #10 — a possessive was moved to the assignee, so a place's tasks found no one)* |
| `tasks assigned to Jordan due today` | `list_tasks` filter.assignee filter.due=today | ✅ *(2026-10-02, #717 — the surname is a capitalised word that opens no other filter; "assigned to Jordan due today" was a teammate called "Jordan due")* |
| `tasks assigned to Jordan Crew at 12 Oak St` | `list_tasks` filter.assignee filter.property | ✅ *(2026-10-02, #717)* |
| `tasks assigned to Jordan marked done` | `list_tasks` filter.assignee filter.status | ✅ *(2026-10-02, #717)* |
| `tasks for Jordan` | `list_tasks` filter.for_name=Jordan | ✅ property first, then teammate *(2026-09-27; 2026-10-11, #842 — filter `for_name`; it always took the assignee)* |
| `unassigned tasks` | `list_tasks` filter.unassigned | ✅ *(2026-09-27)* |
| `list my tasks` | `list_tasks` filter.assignee=me | ✅ "my tasks" is the user's own (Simon, 2026-10-09; `agents/planner/said.py`, 2026-10-10 switchover phase 7d) — before, it was ALL tasks: "my" was no assignee filter, matching every other resource |
| `tasks in progress` / `show done tasks` / `list to do tasks` / `tasks with status {status}` | `list_tasks` filter.status | ✅ *(2026-09-27; "to do" is a status only before "tasks" — "my to-dos" are all tasks)* |
| `show open tasks` / `what's still to do?` | `list_tasks` filter.open_only | ✅ leaving out finished tasks (a status named Done / Completed / Finished / Closed / Cancelled) *(2026-09-27)* |
| `what's overdue?` | `list_tasks` filter.overdue | ✅ due before today and not finished, soonest first with each due date *(2026-09-27)* |
| `show my overdue tasks` | `list_tasks` filter.overdue filter.assignee=me | ✅ the user's own (as above) *(2026-09-27)* |
| `what's due today?` / `today's tasks` | `list_tasks` filter.due=today | ✅ soonest first *(2026-09-27 — no "task" word needed: only tasks have due dates. A week runs Monday to Sunday.)* |
| `tasks due tomorrow` | `list_tasks` filter.due=tomorrow | ✅ *(2026-09-27)* |
| `tasks due this week` | `list_tasks` filter.due=this_week | ✅ *(2026-09-27)* |
| `tasks due next week` / `tasks for next week` | `list_tasks` filter.due=next_week | ✅ *(2026-09-27)* |
| `tasks due by Friday` | `list_tasks` filter.due_before | ✅ *(2026-09-27)* |
| `tasks due on Oct 3` | `list_tasks` filter.due_from filter.due_before | ✅ *(2026-09-27)* |
| `what's due?` / `anything due?` / `what's due next?` | `list_tasks` filter.due=upcoming | ✅ the upcoming list below *(2026-10-02, #718 — no date read meant no filter: every task, finished ones included, under "Here are your tasks", and "for Jordan" was dropped with the unread date)* |
| `anything due already?` | `list_tasks` filter.overdue | ✅ the overdue tasks *(2026-10-02, #718 — no date read meant no filter: every task, finished ones included, under "Here are your tasks", and "for Jordan" was dropped with the unread date)* |
| `what's due now?` | `list_tasks` filter.due | ✅ *(2026-10-02, #718)* |
| `what's due for Jordan?` | `list_tasks` filter.due=upcoming filter.for_name=Jordan | ✅ the upcoming list — for Jordan, property first, then teammate *(2026-10-02, #718)* |
| `what's due for Jordan this week?` | `list_tasks` filter.for_name=Jordan filter.due=this_week | ✅ due this week, for Jordan *(2026-10-02 — "Jordan this week" was read as a place. A bare "this/next week/month" is a window only in a due question)* |
| `what's due in progress?` / `tasks due marked done` | `list_tasks` filter.due=upcoming filter.status | ✅ the status filter, on the upcoming list *(2026-10-02 — a status after "due" isn't a date)* |
| `what's due in the next 3 days?` / `tasks due within the next two weeks` | `list_tasks` filter.due_from filter.due_before | ✅ due from today for that many days or weeks *(2026-10-02 — "in the next 3 days" was read as a status called "next 3 days"; "within the next 3 days" got the 7-day list. "in the …" is a status cue only before a column name)* |
| `what's due in the next week` | `list_tasks` filter.due=next_week | ✅ due from today for that many days or weeks *(2026-10-02 — "in the next 3 days" was read as a status called "next 3 days"; "within the next 3 days" got the 7-day list. "in the …" is a status cue only before a column name)* |
| `what's due 10/3` | `list_tasks` filter.due_unread | ✅ the planner handles it — was a gap: *"I couldn't read '10/3' as a date — …"* *(2026-10-02 — numeric dates aren't read anywhere in tasks: 10/3 is 3 October in the US and 10 March elsewhere, and there is no locale setting. Said back, never swapped for another window. "due Oct 3" works)* · said back *(2026-10-11, #842 — filter `due_unread`; it read 10/3 the US way)* |
| `tasks due whenever` / `what's due on the blue moon?` | `list_tasks` filter.due_unread | ✅ *"I couldn't read 'whenever' as a date — try something like "due Friday", "due Oct 3" or "due this week"."* *(2026-10-02, #718 — a date it can't read is said back, never dropped)* |
| `upcoming tasks` / `what's upcoming?` / `anything due soon?` | `list_tasks` filter.due=upcoming | ✅ overdue or due in the next 7 days and not finished — overdue first, each row saying whether it's overdue *(2026-09-27 — the dashboard's Upcoming Tasks card in words; overdue tasks were left out)* |
| `what's coming up this week?` | `list_tasks` filter.due | ✅ *(2026-09-27)* |
| `what's on my to-do list?` | `list_tasks` filter.due=upcoming filter.assignee=me | ✅ the upcoming list, assigned to you — the card's default view *(2026-09-27 — went to the user guide)* |
| `what's on my plate?` | `list_tasks` filter.due=upcoming filter.assignee=me | ✅ the upcoming list, assigned to you — the card's default view *(2026-09-27 — went to the user guide)* |
| `show archived tasks` | `list_tasks` filter.archived | ✅ archived only |
| `find tasks about fencing` | `list_tasks` filter.search=fencing | ✅ title/description search *(named/matching/about/containing/called all apply the search term)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `list my tasks` (more than 20) → *"That's 1–20 of 24 … say "show more" for the next 4."* → `show more` / `next page` / `the rest` | the same list, from where it stopped — filters included | ✅ rule *(2026-09-27 — good for the next turn only; "show more" with no longer list open says so)* |

## 7.6 Field-targeted update

The `the {task} task` keyword forms are ✅; bare-title forms (`change the due date of {task} to Friday` with no "task" word) are ✅ for the change/update shapes and ⚠️ for the set-possessive shape (2026-07-22 Tier-2 run). Due-date values accept ISO (`2026-08-01`), `today`/`tomorrow`, and weekday names (next occurrence).

| Phrasing | Plan | Status |
|---|---|---|
| `change the due date of the {task} task to Friday` | `update_task` fields.due_date | ✅ |
| `add a description to the last task: {text}` | `update_task` | ✅ recency reference |
| `rename the {task} task to {new title}` | `update_task` fields.title | ✅ *(2026-07-30 — genuinely rule-tier now; `rename` was missing from `ACTION_HINTS` so this row previously described the agent-side handler only, and routing fell through to the LLM)* |
| `retitle the {task} task to {new title}` | `update_task` fields.title | ✅ |
| `rename it to {new title}` [task_focus] | `update_task` fields.title | ✅ pronoun target *(2026-07-30 — resolves through the active-task anchor; see §7.11)* |
| `set the description of the {task} task to {text}` | `update_task` fields.description | ✅ |
| `change the due date of {task} to Friday` | `update_task` fields.due_date | ✅ bare title |
| `set {task}'s due date to next Monday` | `update_task` fields.due_date | ✅ the planner handles it — was a gap: (bare title) |
| `make it due Friday` / `push it to next week` / `it's due in 3 days` / `due Friday` [task_focus] | `update_task` fields.due_date | ✅ task in focus *(2026-09-27 — dates also accept `next week`, `in N days/weeks`, `end of the week/month`, `Oct 3` / `3rd of October`)* |
| `reschedule the {task} task to Oct 3` | `update_task` fields.due_date | ✅ *(2026-09-27)* |
| `set the due date to 2026-10-30` [task_focus] | `update_task` fields.due_date=2026-10-30 | ✅ right after `create a task to …`: the task just made — never a second create *(2026-10-11 — a message with no verb of its own borrowed the create from history and asked "What should the task say?"; a create is never borrowed now, like a delete. A create whose name and notes were the same text also wrote it twice — once now.)* |
| `remove the due date from the {task} task` | `update_task` fields.clear_due_date | ✅ *(2026-09-27)* |
| `clear the due date` [task_focus] | `update_task` fields.clear_due_date | ✅ the task in focus; with none, Maple asks which *(2026-09-27)* |
| `link it to 12 Oak St` [task_focus] | `update_task` fields.property | ✅ *(2026-09-27)* |
| `link the {task} task to the Elm House property` | `update_task` fields.property | ✅ *(2026-09-27)* |
| `set the property of the {task} task to Elm House` | `update_task` fields.property | ✅ *(2026-09-27)* |
| `add to the task description the following: {text}` / `append to its description: {text}` [task_focus] | `update_task` fields.notes_append | ✅ the text added to the task's, never the whole of it *(2026-10-11 — planned as the description, it replaced the task's text and its title, the first line; the planner reads "add"/"append" said before the text as adding (`said._task_text_said`). With no task in focus it asks "Which task should I update?". Today's pipeline created a new task instead, its text written twice)* |
| `set task {TASK} description to {text}` | `update_task` fields.description | ✅ *(2026-09-28 — target before the field (`_TARGET_FIRST_LEAD`); previously asked "What would you like to update on the task?", and the due-date form read its value as "date to …". Description here overwrites, like `set the description of …`)* |
| `set task {TASK} notes to {text}` | `update_task` fields.notes_replace | ✅ *(2026-09-28)* |
| `set task {TASK} due date to Friday` / `change {TASK}'s due date to Friday` | `update_task` fields.due_date | ✅ *(2026-09-28)* |
| `set task {TASK} title to {new title}` | `update_task` fields.title | ✅ *(2026-09-28)* |
| `set task {TASK} property to Elm House` / `set task {TASK} address to Elm House` | `update_task` fields.property | ✅ *(2026-09-28)* |
| `remove the property from the task` | ask | ✅ *(2026-09-27 — unlinking a task is Maple's; unlinking a contact from a property is still done in the app, §9)* |
| `unlink it from the property` [task_focus] | `update_task` fields.clear_property | ✅ *(2026-09-27 — as above)* |
| `hey maple, rename the fence task to Gate` | `update_task` | ✅ *(a lead before the verb — fillers, a polite ask, "I'd like to" — is still a command)* |
| `could you change the due date of it to Friday` / `I'd like to update the description: bring the ladder` [task_focus] | `update_task` | ✅ *(a lead before the verb — fillers, a polite ask, "I'd like to" — is still a command)* |
| `I need you to mark it done` [task_focus] | `update_task` fields.status=Done | ✅ the edit — "I need you to" asks Maple *(2026-10-04, #774 — it showed the task and wrote nothing. Plain `I need to finish it` still notes work to do and is no command, user decision 2026-09-28; the lead is the shared `COMMAND_LEAD`)* |
| `I need you to archive the fence task` | `update_task` fields.archived=true | ✅ the edit — "I need you to" asks Maple *(2026-10-04, #774)* |
| `don't rename the fence task to Gate` / `I won't change the due date of the fence task to Friday` | `acknowledge` | ✅ nothing changes — the verb mid-sentence is not a command *(2026-09-30, #762 — they wrote. Rename, field and add-description shapes are anchored with `_COMMAND_LEAD` like every other task edit; no negation rule)* |
| `we shouldn't update the description of it to foo` / `don't add a description to it: call Bob` [task_focus] | `acknowledge` | ✅ nothing changes *(2026-09-30, #762 — as above)* |

## 7.6.1 Notes on an existing task (append by default)

Adding notes to a task Maple already worked on is an **update**, not a create — the orchestrator's `is_task_notes_update_request` claims these before the generic resolver, because `add` is a CREATE action hint and would otherwise make a *second* task. The rule requires an explicit `task`; a bare `add a note to it` stays on the generic anaphora path, which since 2026-07-30 resolves to whichever domain the user touched **most recently** rather than to a fixed ranking that always preferred an active estimate.

Additive is the default, matching estimate notes (§5.x) — a drive-by note never silently wipes what's there. Existing notes and the new text are blank-line separated; appending onto empty notes collapses to a clean set. Only an explicitly destructive verb (`replace` / `overwrite` / `set … with`) overwrites.

| Phrasing | Plan | Status |
|---|---|---|
| `Add the following notes to the Task: {text}` [task_focus] | `update_task` fields.notes_append | ✅ the task in focus *(2026-07-25)* |
| `Add to the Task: {text}` / `add this to the task: {text}` [task_focus] | `update_task` fields.notes_append | ✅ **no field word at all** *(2026-07-25 smoke-test fix — the colon carries the meaning: everything after it is content, and notes are the only free-text field a task has. A separator is REQUIRED, so `add a photo to the task` isn't claimed.)* |
| `add to the {task} task: {text}` | `update_task` fields.notes_append | ✅ **no field word at all** *(2026-07-25 smoke-test fix)* |
| `Add to the tasks to {text}` / `add to the task to {text}` / `add to the tasks about {text}` / `add to the task that {text}` [task_focus] | `update_task` fields.notes_append | ✅ **plural noun and/or a connector word instead of a colon** *(2026-07-30 — reported: "Add to the tasks to buy more milk." landed on `create_task` and asked "What should the task be called?". Two gaps: `task\b` never matched the plural, and the colon was the only separator. `to` / `about` / `that` now count as separators, and the noun may be plural. `add a photo to the task(s)` still isn't claimed — the verb must be followed immediately by to/on/onto, which was always the real guard.)* |
| `add a note to the task: {text}` [task_focus] | `add_note` parent.domain=task | ✅ the task in focus; with none, Maple asks which |
| `append to the task notes: {text}` | ask | ✅ |
| `add notes to the {task} task: {text}` | `update_task` fields.notes_append | ✅ |
| `add a note to it: {text}` [task_focus] | `add_note` parent.domain=task | ✅ with a task anchor *(2026-09-27 review)* |
| `Add another note: {text}` / `add a note: {text}` [task_focus] | `add_note` parent.domain=task | ✅ **no target at all** — the record in focus, the freshest — never a contact by default *(2026-07-25 smoke-test fix — the active task is implied, same as the pronoun forms. 2026-09-24 — routing is now rule-tier: `is_note_add_request` sends a targetless note to whichever domain was touched most recently; before, the borrowed domain plus `add` resolved to `create_task`. 2026-10-12)* |
| `replace the notes on the task with: {text}` / `set the notes on the task to: {text}` [task_focus] | `update_task` fields.notes_replace | ✅ the task in focus; with none, Maple asks which |
| `add a task with the notes: {text}` | `create_task` fields.notes_append | ✅ *(create shape — the notes-update rule explicitly excludes it)* |
| `don't add a note to it: call Bob` [task_focus] | `acknowledge` | ✅ nothing changes — *"Okay — I'll leave it as it is."* *(2026-09-30, #762 — they appended or replaced the notes. The notes shapes are anchored with `agents.text_utils.COMMAND_LEAD`, and so are the router's copies of them — review 2026-09-30 #13: they still routed to `update_task`, which asked what to change)* *(2026-10-11, #847 — it added the note. Not "don't forget to …", nor with what to do instead)* |
| `we shouldn't set the notes on the fence task to foo` / `please don't add to the task: call Bob` / `don't add to T0042 bring the contract` | `acknowledge` | ✅ nothing changes *(2026-09-30, #762; 2026-10-11, #847 — as above)* |
| `add a note to it: don't park on the lawn` [task_focus] | `add_note` parent.domain=task | ✅ the note's own words are content, never a negated command *(2026-09-30, #762 — the anchor sits before the verb, so the note body is untouched)* |
| `add to the fence task: we shouldn't dig here` | `update_task` fields.notes_append | ✅ the note's own words are content, never a negated command *(2026-09-30, #762)* |
| `attach this to the task` / `add this photo to T0042` / `put this on the fence task` [task_focus+photo] | `update_task` attach | ✅ with a photo or PDF on the message (or the previous one): the file(s) are copied onto the task's media (the Media section in the app); with none, `NO_FILE_ON_MESSAGE_REFUSAL` (Maple attachments, 2026-10-18) |
| `attach these to T0042` / `add this photo to the fence task` [task_focus+photo+quote] | `update_task` attach | ✅ when the files would put the task over 10 (a task holds at most 10 files, any kind): none is attached — `attach` is every file — and Maple says why (`TASK_FILES_FULL_REFUSAL`); a change said beside them is still made (2026-10-19) |
| `add a note to the task with this photo: call first` [task_focus+photo] | `add_note` parent.domain=task attach | ✅ the words go on the description, the file on the task's media (Maple attachments, 2026-10-18) |
| `create a task from this photo: fix the gate latch` / `new task with this PDF: order the pavers` / `make a task from this photo` [none+photo] | `create_task` attach | ✅ the words after the colon (or what the photo shows) are its text; the file(s) go on the new task's Media — a task's notes are its description, so its files are its media (Maple attachments, 2026-10-18) |
| `make a task for each item on this list` [none+list] | `create_task` | ✅ with a photo of a to-do list on the message: one task per line read from it; with several creates nothing claims the file, so none carries it *(2026-10-19 review — probed live with a list on the message)* |
| `remove the photo from T0042` | refuse `out_of_chat` `media` | 🛑 a task's media is removed on the task in the app *(2026-10-19 review — probed live; the refusal's words are a gap, §10.11)* |
| `delete the PDF on the fence task` | refuse `out_of_chat` `media` | 🛑 *"I can't remove a photo or file from chat — open the task or the note in the app and remove it there."* — never the offer to delete the task (`as_asked_files`) — G29 (gap plan 2026-10-19, closed the same day) |

### 7.6.1.1 Dictated payloads — the first intent wins

**In `<command>: <payload>`, the payload is content, not intent.** Classifying the whole string let a domain word inside the user's own prose take over: *"Add to it the following: bring a lawn mower to his place. Need to estimate the lawn size."* routed to `create_estimate` — the trailing "estimate" beat the leading "add to it".

`strip_dictated_payload` (in `intents.py`) returns just the command head when the head carries an add/notes/following cue, and the generic resolvers classify on that head — `_match_unambiguous_command`, `_classify_via_action_domain`, and `_resolve_intent_with_history` (where a payload domain word previously blocked anaphora outright). Task-specific rules still see the full text, because some key off the colon itself. A message that names its domain in the head (`create an estimate for: 123 Main St`) is unaffected.

Paired rule: **an anaphoric target means the entity already exists**, so `is_anaphoric_add_request` rewrites the CREATE reading of "add … to it/this/that" to an update. Which domain it updates still comes from the active-entity anchor (estimate before task, §7.11) — so the same sentence appends to an active estimate when that's what's in play.

| Phrasing | Plan | Status |
|---|---|---|
| `Add to it the following: {text}` / `Add to it the following: bring a lawn mower to his place. Need to estimate the lawn size.` [task_focus] | `update_task` fields.notes_append | ✅ the active task; the payload may mention other domains *(2026-07-25 smoke-test fix)* |
| `add to the task the following: {text}` [task_focus] | `update_task` fields.notes_append | ✅ the planner handles it — was a gap: *(2026-09-27 review: creates a second task instead of appending)* |
| `Add to it the following: {text}` [est] | `add_note` | ✅ an estimate-level note on the active **estimate** *(anchor decides, not the payload)* |

## 7.6.2 Field-then-value flow (§10.1) — "update the task" → "description" → the value

`update the task` alone can't be actioned, so Maple asks which field. That question is only useful if the answer can be resumed: each ask now stashes a `pending_intents` entry naming the Task Agent, which is what the router's pending fallback routes the bare reply back to. **Without it the reply landed wherever the classifier guessed** — in the 2026-07-25 smoke test, three "What would you like to update?" loops followed by create's *"What should the task be called?"*.

Either step can be entered directly: `description` on its own selects the field and asks for the value; `add to the description` works only as a reply to the field question (2026-09-27 review). `match_bare_task_field` maps title/name, description/notes/note/details, due date/due/deadline, status/state, assignee/assigned to/owner — and returns nothing as soon as the message carries a payload, so an answer like "mow the lawn as well" is never mistaken for a field selection. Description values **append**; a fresh command mid-flow (`list my tasks`) is obeyed and the stale ask is dropped.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `update the task` → *"What would you like to update…?"* → `description` → *"What would you like me to add…?"* → `{text}` | `update_task` field-then-value → Task Agent | ✅ rule *(2026-07-25)* · 🤖 planner: the field named, its value asked *(2026-10-12)* |
| bare `title` / `due date` / `status` / `assignee` → value | `update_task` field-then-value → Task Agent | ✅ rule *(status resolves per-company names; assignee takes an email, "me" or a teammate's name; due date takes any §7.6 date phrase, and an unreadable one asks again)* |
| *"Which status…?"* / *"Who should I assign it to?"* → the command restated: `set status to In Progress` / `mark it as done` / `change it to Done` / `assign it to Jordan` | `update_task` field-then-value → Task Agent | ✅ rule *(2026-09-28 — only the value is read (`restated_field_value`); one naming another task (`set T0002 status to Done`) is a new request)* |
| `assign it` / `change the assignee` / `change the status` / `move it` / `set a due date` / `reschedule it` → the value | `update_task` → Task Agent asks for that one value | ✅ rule *(2026-09-27 — no "what would you like to update?" first; #692)* |

*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `add to the description` | conversation `ref-task-description-added-in-reply` | ✅ asks what to add, and the reply is added to the task's description — on its own as well as after the field question *(2026-09-27 review; 2026-10-13)* |

## 7.7 Status changes

`TaskStatus` values are **per-company** (defaults: `To Do`, `In Progress`, `Done`). Status names resolve exact → case-insensitive → fuzzy; an unrecognized name triggers a clarification listing the company's statuses. Status changes fold under `update_task` (same pattern as estimate status transitions under `update_estimate`, §1.4).

*Live run 2026-10-19, G32 ([gap plan](plans/2026-10-19-maple-phrasing-gaps-plan.md)):* in the acceptance conversation `task-status-answered-by-a-request-shaped-status`, `New Request` — a status the company has, in reply to the status question — is not taken as the answer: the planner asks again what to do or which status, in both conversation runs. **Closed:** in the acceptance run of 2026-10-20, on the planner's own state, `New Request` sets the task's status (G33 was why it failed there before: the parity run fed today's state).

| Phrasing | Plan | Status |
|---|---|---|
| `mark it as done` [task_focus] | `update_task` fields.status=Done | ✅ with a task anchor *(2026-09-27 review)* |
| `mark the {task} task as done` | `update_task` fields.status=Done | ✅ |
| `move the {task} task to In Progress` | `update_task` fields.status | ✅ |
| `set the status of the {task} task to {status}` | `update_task` fields.status | ✅ *(unknown names get a clarification listing the company's statuses — since 2026-09-28 a registered question, so the bare reply (`In Progress`) sets it on the same task; done/complete/finished + in-progress/started + to-do/open synonyms map to the default names when present)* |
| `set task {TASK} status to {status}` / `change T0001's status to done` / `set the {task} task status to done` | `update_task` fields.status | ✅ *(2026-09-28 — target before the field; previously asked "What would you like to update on the task?")* |
| `I finished it` / `it's done` / `start it` / `reopen it` [task_focus] | `update_task` fields.status | ✅ *(2026-09-27 — "reopen" moves it back to the company's first status)* |
| `complete the {task} task` | `update_task` fields.status | ✅ *(2026-09-27)* |

*Not yet in the Plan format — an answer to a question, or a status the test world lacks (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| *"Which status should I set it to?"* or *"I don't recognize 'X'… Which one?"* → `New Request` / `Create Estimate` — a custom status that reads as a request | the status is set on that task | ✅ rule *(2026-09-29, name-answers plan phase 3 — read as a new request)* |
| `move it to Next Week` where "Next Week" is one of the company's statuses | the card moves to that status; the due date is untouched | ✅ rule *(2026-09-29, #711 — it set the due date to next Monday)* |

## 7.8 Assignee operations

Assignees are stored as emails (`assigned_to_email`); an email is taken as given (parity with the REST API — no team-membership validation), and since 2026-09-27 a teammate can be named by first, last or full name.

| Phrasing | Plan | Status |
|---|---|---|
| `assign this to {email}` [task_focus] | `update_task` fields.assignee | ✅ with a task anchor *(2026-09-27 review)* |
| `assign the {task} task to me` | `update_task` fields.assignee=me | ✅ |
| `assign the {task} task to {email}` / `reassign the {task} task to {email}` | `update_task` fields.assignee | ✅ an email is taken as given *(2026-10-12 — one outside the team looped)* |
| `give it to Jordan` / `assign it to Jordan` [task_focus] | `update_task` fields.assignee=Jordan | ✅ by teammate name *(2026-09-27 — two teammates with that name get a question listing both)* |
| `hand the {task} task over to Ana` | `update_task` fields.assignee=Ana | ✅ by teammate name *(2026-09-27)* |
| `set task {TASK} assignee to {email}` / `set task {TASK} owner to Jordan` / `change {TASK}'s owner to Jordan` | `update_task` fields.assignee | ✅ *(2026-09-28 — target before the field)* · an email is taken as given *(2026-10-12)* |
| `unassign it` [task_focus] | `update_task` fields.unassign | ✅ *(2026-09-27)* |
| `assign the {task} task to nobody` | `update_task` fields.unassign | ✅ *(2026-09-27)* |
| `remove the assignee` [task_focus] | `update_task` fields.unassign | ✅ the task in focus; with none, Maple asks which *(2026-09-27)* |
| `list tasks for Jordan` | `list_tasks` filter.for_name=Jordan | ✅ with two teammates called Jordan: *"More than one teammate is called Jordan: …"* *(2026-09-29, #752 — "I couldn't find a property or a teammate called Jordan")* |
| `who is the {task} task assigned to?` | `get_task` | ✅ the planner handles it — was a gap: *(details view already shows Assigned to; the who-question routing is unwired)* |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `give it to Jordan` (two Jordans) → *"More than one teammate is called Jordan: … Which one? Their full name or email works."* → `Jordan Park` | assigned to Jordan Park | ✅ rule *(2026-09-29, phase 3 — the question wasn't remembered)* |
| `give it to Zed` (no such teammate) → *"Who should I assign the task to?"* → `Jordan` | assigned to Jordan | ✅ rule *(2026-09-29, phase 3)* |
| `assign it` → *"Who should I assign it to?"* → `Jordan Crew.` | assigned — the reply is tidied first | ✅ rule *(2026-09-29, #751 — "Jordan." never matched)* |

## 7.9 Archive / unarchive

Soft-hide only — archived tasks still count toward the free-plan cap.

| Phrasing | Plan | Status |
|---|---|---|
| `archive that task` [task_focus] | `update_task` fields.archived=true | ✅ the active task |
| `archive the {task} task` | `update_task` fields.archived=true | ✅ |
| `unarchive it` [task_focus] | `update_task` fields.archived=false | ✅ with a task anchor *(2026-09-27 review)* |
| `unarchive the {task} task` / `restore the {task} task` | `update_task` fields.archived=false | ✅ |

## 7.10 Convert to estimate

Converting generates a new estimate from the task's description via the AI pipeline and **consumes one included estimate** — Maple always confirms before running it. Requires a non-empty task description. Billing outcomes surface as friendly refusals (needs payment method / plan blocked / already converting).

Handler: `agents/task/operations.py::_handle_convert_task` → `services/task_convert.py::run_task_conversion` — the SAME claim/billing/generation/re-link core the REST endpoint uses (extracted 2026-07-22 so the two paths can't drift). On success the new estimate becomes the **active estimate** ("add a work item to it" then targets the estimate).

| Phrasing | Plan | Status |
|---|---|---|
| `convert this task to an estimate` [task_focus] | `convert_task` | ✅ the active task; confirms first |
| `convert the {task} task to an estimate` / `turn the {task} task into a quote` | `convert_task` | ✅ confirms first |

## 7.11 Task referencing & anaphora

A task can be referenced three ways; an explicit reference in the message always beats the active-task context. Multiple matches trigger a numbered clarification ("I found 3 tasks matching that — which one did you mean?"); the reply (number, title, or "the first one") dispatches the original request. Once a task is identified (create/get/update/status/assign/archive), it becomes the **active task** — follow-ups ("mark it done", "add a description", "convert it") act on it. Deleting a task clears the active-task context.

Resolver: `agents/task/resolver.py::find_task_from_context_or_message` — order: a database id in the message ends the search and asks for the code or title (2026-10-01, #798 — it was looked up) → positional pick against the last rendered list (§10.5) → recency words → day window (`agents/text_utils.py::parse_relative_day_window`) → property (via `find_properties_by_name_or_address`) → title (exact substring, then fuzzy 0.65/0.80) → active-task context → recency fallback (gated OFF for delete/convert; never used after an unmatched explicit title). Confirmation state: `pending_task_confirmation` (numbered/title/ordinal replies; "no" cancels; a fresh command breaks the pending question). Ordinal replies go through the shared `agents/text_utils.py::match_ordinal_reference` — `first`–`tenth`, `1st`–`10th`, `last`, and digits with an optional leading determiner (`2`, `the 2`, `#2`, `option 2`) (2026-07-30; previously a local `first`–`fifth` table with no `last`).

| Phrasing | Plan | Status |
|---|---|---|
| `show me the last task` / `show me my latest task` | `get_task` | ✅ relative (recency) — "my" = assigned to me *(2026-10-11, #841 — "add a description to the last task" found a task named "last task")* · never a title that starts with "Last" *(2026-10-12)* |
| `show me the task from yesterday` / `show me the task from Tuesday` / `show me the task from 3 days ago` | `get_task` | ✅ relative (date) *(2026-10-11, #841)* |
| `show me the fence gate task` | `get_task` | ✅ by title, fuzzy (typos tolerated) — asked first before a write *(2026-10-11, #841 — "Just to check — do you mean …?")* |
| `show me the task at {property}` | `get_task` | ✅ by property *(2026-10-11, #841)* |
| `mark it as done` [task_focus] | `update_task` fields.status=Done | ✅ anaphora (active task) *(pronoun-only messages route via the LLM tier + active-task context. 2026-07-30 — two routing bugs used to steal these: a stale `active_estimate_code` from earlier in the session out-ranked the just-created task, and a Capitalized new value was mined as a person name and sent to Contact. The anchor is now chosen by recency (`active_entity_domain`), and a pronoun-targeted edit's payload is never read as a domain signal.)* |
| `convert it` [task_focus] | `convert_task` | ✅ anaphora (active task) *(2026-07-30 — as above)* |
| `rename it to {new}` [task_focus] | `update_task` fields.title | ✅ anaphora (active task) *(2026-07-30 — as above)* |
| `mark the task as done` / `assign my task to {email}` / `archive the task` / `rename the task to {new}` [task_focus] | `update_task` | ✅ anaphora (bare determiner) *(2026-07-25 — "the/my task" with no name in between is anaphora: the target hint collapses to empty and resolution goes through the active-task context. Previously the stray determiner leaked into the title matcher and could hit ANY title containing "the".)* |
| `mark the task as done` | ask | ✅ with no task in focus Maple asks "Which task?" rather than editing the most recently updated task; notes appends still fall back to it, #447 *(2026-09-28)* |

*Not yet in the Plan format — several turns, or an answer to a question (phase 3):*

| Reference form | Example | Status |
|---|---|---|
| Ambiguity → confirmation | two similar titles → numbered clarification, reply `1` / `the second one` / `T0004` / words from one title (`the paint one`) / `no` | ✅ *(2026-09-27 — the readable id and title words; the question gate reads a reply naming a choice as the answer, #692)* |
| No match → "Which task did you mean?" | `mark the pool task as done` → *"I couldn't find a task matching 'pool'. Which task did you mean?"* → `Create estimate for Bob` (a title that reads as a request) / its ID | ✅ *(2026-09-29, name-answers plan phase 5 — the question wasn't remembered, and that reply would have started an estimate)* |
| A value for a task that is gone | `status` → `In Progress` → *"Which task should I update?"* → `Fix the fence gate` | ✅ *(2026-09-29, #713 — the task's name was read as the status)* |
| The Task agent's property question | `link it to Pine Ridge` → *"I couldn't find a property called Pine Ridge. Which property did you mean?"* → `Elm House`; `list tasks at St` → *"More than one property matches St: … Which one did you mean?"* → `12 Oak St` | ✅ *(2026-09-29, phase 5, #713 — the reply was read as a new request)* |

## 7.12 Task refusals — 🛑

| Phrasing | Plan | Status |
|---|---|---|
| `delete all my tasks` / `wipe my tasks` | refuse `bulk_delete` | 🛑 bulk-delete refusal (existing domain-agnostic guard) |

*Not yet in the Plan format — the refusal depends on the user's role, the workspace's settings or plan, or the task itself (phase 3):*

| Phrasing / condition | Behavior | Status |
|---|---|---|
| `delete the {task} task` as a non-manager | Refused — owners/admins only (`agents/role_utils.py::assert_manager_role`, shared with the Template agent); Maple offers to archive instead | 🛑 refusal |
| `convert …` with an empty task description | Refused — Maple asks to add a description first | 🛑 refusal |
| Any task request while `tasks_enabled` is off | Friendly "Tasks aren't enabled for your workspace" refusal | 🛑 refusal · 🤖 planner: any action on a task too — a link, its notes *(2026-10-12 — they ran)* |
| `create a task …` at the free-plan 50-task cap | Refused with upgrade pointer (mirrors REST 409) | 🛑 refusal |
| Convert billing outcomes (402 needs-payment / 429 blocked / 409 already-converting) | Friendly first-person refusals mapped from `run_task_conversion`'s HTTP errors | 🛑 refusal |

## 7.13 Task gaps

Shipped 2026-07-22 (plan: [`plans/maple-tasks-support.md`](plans/maple-tasks-support.md)). Remaining ⚠️ rows, confirmed against both tiers where noted:

- **Bare-title references** (possessive §7.3, verbless, set-possessive §7.6) — no "task" keyword to anchor on; both tiers fail (2026-07-22 Tier-2 run). Same gap class as materials/contacts pre-Phase-2b; a catalog-backed title lookup would close it.
- **Informal create cue** — `I need to remember to…` (unverified). `jot down…`, `remind me to…` and the to-do list forms work since 2026-09-27.
- **`who is the {task} task assigned to?`** — unwired; details view covers the need.
- **`who created this task?`** [task_focus] — planned as the task's details, which don't say who created it (`created_by_email` is stored). G24 in the [gap plan](plans/2026-10-19-maple-phrasing-gaps-plan.md) (2026-10-19 review, probed live).
- **`add a task to the estimate`** — routes to the Task Agent (estimate work items are never called "tasks" in code or docs); when the message names an estimate, Maple should offer redirection to the work-item flow ("Did you mean a work item on the estimate?"). Not yet implemented.

Task details (2026-09-27) also show the linked property, the estimate it was converted into, and how many photos and videos it has.

**Open gaps:** #767 ("perfect," / "quick," / "one more thing," before a command); older #447 (see [code-review-followups.md](code-review-followups.md)). #442 and #761 were resolved 2026-10-03; #740, #774 and #804 on 2026-10-04. #672, #675, #676, #683, #687, #689 and #692 were resolved 2026-09-27; #711, #713, #751 and #752 on 2026-09-29; #470 and #762 on 2026-09-30; #710 and #712 on 2026-10-01; #717 and #718 on 2026-10-02.

---

# 8. Cross-resource / implicit relationships

Questions users ask when they think about the domain rather than the database. Routing is via `_match_cross_resource_query` in the orchestrator (Wave 2 Phase 1); the join is performed by the target agent reading a `filter_by` payload off `context` (Wave 2 Phase 2). Direct lookups (Property↔Contact) hit the linked-id list on the Property document. Transitive joins (material/role → property, material/role → estimate, estimate → materials/roles) go through the estimates' lines, which live in their work items: `job_items[].materials[].material` and `job_items[].activities[].role` (plus legacy `job_items[].labours[].labour`). One filter and two readers in `agents/cross_resource.py` (`estimate_line_filter`, `estimate_material_names`, `estimate_role_names`) serve every join. Until 2026-09-27 (#682) the joins queried top-level `materials.material` / `labours.labour`, paths `Estimate` doesn't have, and always came back empty; the estimate list had no material filter.

## 8.1 Property ↔ Contact

| Phrasing | Plan | Status |
|---|---|---|
| `who lives at {property}?` | `get_property` field=contacts | ✅ the contacts linked to the property |
| `what contacts are at {property}?` | `list_contacts` filter.related | ✅ the contacts linked to the property |
| `who owns {property}?` | `get_property` field=owner | ✅ its Home Owners only *(2026-10-11, #845 — it listed every contact linked; none marked: "None of 12 Oak St's contacts is a Home Owner.")* |
| `what properties does {contact} own?` | `list_properties` filter.owner | ✅ the contact's properties — a prompt line — G28 (gap plan 2026-10-19, closed the same day) |
| `where does {contact} live?` | `get_contact` field=properties | ✅ the properties linked to the contact |
| `show me {contact}'s properties` | `get_contact` field=properties | ✅ the possessive flow |
| `which properties does contact {contact} linked to?` | `get_contact` field=properties | ✅ *(May expansion — new "linked to" cross-resource pattern)* |
| `show me properties contact {contact} linked to` / `show me all properties contact {contact} linked to` | `get_contact` field=properties | ✅ *(May expansion)* |

## 8.2 Material → Property / Estimate

| Phrasing | Plan | Status |
|---|---|---|
| `which properties use {material}?` | `list_properties` filter.related | ✅ joined via estimates — *"Properties with an estimate that uses Black Mulch:"* / *"No property has an estimate that uses Topsoil."* *(2026-09-27, #682)* |
| `where is {material} used?` | `list_properties` filter.related | ✅ joined via estimates *(2026-09-27, #682)* |
| `which estimates use {material}?` / `what estimates include {material}?` / `find estimates with {material}` | `list_estimates` filter.material | ✅ *"Estimates that use Black Mulch:"* / *"None of your estimates use Topsoil."* *(2026-09-27, #682 — `find estimates with …` listed every estimate; `with status sent` and other list filters are left to the list)* |

## 8.3 Labour → Property / Estimate

| Phrasing | Plan | Status |
|---|---|---|
| `which properties need a {role}?` | `list_properties` filter.related | ✅ joined via estimates *(2026-09-27, #682)* |
| `what estimates use the {role} role?` / `which estimates use {role}?` | `list_estimates` filter.role | ✅ with or without "role" *(2026-09-27, #682 — it was always empty, and the help pre-check showed "Intent identified: …" instead of delegating)* |
| `show me jobs needing a {role}` / `list properties that need a {role}` | `list_properties` filter.related | ✅ joined via estimates *(2026-09-27, #682 — it listed every property)* |

## 8.4 How much of a material or role is in your estimates *(2026-10-01, metrics plan Phase 4)*

`analytics_metric` grammar entries (`command_grammar._LINE_ENTRIES`, an `l_`
slot), answered by `agents/estimate/metric_lines.py` from
`maple_metrics.run_line_totals`. **Quantities only, no dollars** (decision 19);
**per unit, never converted** (decision 21) — a material line's unit is its
snapshot, or the catalog's unit for its size; a role's is its own. Every
estimate unless a status is said (decision 20); every occurrence of a
recurring item counts; a customer, property, division and period apply as to
any metric (§1.12).

| Phrasing | Plan | Status |
|---|---|---|
| `how much Black Mulch is in my estimates?` | `metric` metric=line_total line_name | ✅ *"Black Mulch in your estimates, all time: 10 bags and 4 cubic yards, across 2 estimates."* *(a guide answer)* |
| `how much Black Mulch is in my open estimates?` | `metric` metric=line_total line_name status=open | ✅ *(a guide answer)* |
| `how much Black Mulch is in my estimates for Bob Lee?` | `metric` metric=line_total line_name subject | ✅ *(a guide answer)* |
| `how much Black Mulch have I quoted this year?` | `metric` metric=line_total line_name period=year | ✅ *(a guide answer)* |
| `how many bags of Black Mulch are in my draft estimates?` | `metric` metric=line_total line_name status=draft | ✅ *(a guide answer)* |
| `how many hours of Foreman are in open estimates?` | `metric` metric=line_total line_name=Foreman status=open | ✅ *(it counted open estimates and dropped Foreman)* |
| `how many hours of Foreman have I sold this year?` / `how much Foreman time did I sell this year?` | `metric` metric=line_total line_name=Foreman status=sold period=year | ✅ *"Foreman in your sold estimates, all time: 8 hours, across 1 estimate (Won, Scheduled, Completed)."* *(it counted open estimates and dropped Foreman)* |
| `how many hours of Operator are in my estimates?` | `metric` metric=line_total line_name=Operator | ✅ a role priced by the day — *"Operator is priced by the day, not the hour: 2 days in your estimates, all time, across 1 estimate."* *(decision 21)* |
| `how much Mulch is in my estimates?` | `metric` metric=line_total line_name=Mulch | ✅ two materials match (Black Mulch and Red Mulch) — *"Which one did you mean: Black Mulch or Red Mulch? Ask again with its full name."* *(not resumable: ask again)* |
| `how much Bluestone is in my estimates?` | `metric` metric=line_total line_name=Bluestone | ✅ no such record — *"I couldn't find a material, role, customer, property or division called Bluestone."* |
| `how much Elm House work did we win?` | `metric` metric=total subject status=sold | ✅ a place where a material would be: that one's total — *"Won value for Elm House, all time: $900.00 across 1 estimate (Won, Scheduled, Completed), including tax."* *(Phase 4 review #2 — it said "couldn't find a material or role")* |
| `how much Landscaping work have we sold this year?` | `metric` metric=total subject=Landscaping status=sold period=year | ✅ a division where a material would be: that one's total *(Phase 4 review #2 — it said "couldn't find a material or role")* |
| `how many hours of Elm House are in my estimates?` | `metric` metric=line_total line_name | ✅ a unit asked of a place — *"I couldn't find a material, role, customer, property or division called Elm House."* — a unit is never a place's total *(Phase 4 review round 2 #2 — it gave Elm House's dollar total)* |
| `how much have I quoted using Black Mulch?` | `metric` metric=line_total line_name | ✅ the quantity in the estimates — never dollars *(decision 19, kept by Simon 2026-10-13: a line's price is a snapshot that markup and repricing move)* |
| `how much mulch is in this estimate?` | ask | ✅ not a line sum — the open estimate's; with none open, Maple asks which estimate |
| `which estimates use Black Mulch?` | `list_estimates` filter.material | ✅ not a line sum — the list |
| `how much does Black Mulch cost?` | `get_material` field=price | ✅ not a line sum — the catalog price |
| `how much mulch do I need for 200 sq ft?` | `calculate` | ✅ not a line sum — the Calculator |

*Not yet in the Plan format — several turns (phase 3):*

| Phrasing | Answer | Status |
|---|---|---|
| `how much Ana work did we win?` (two customers called Ana) → `Ana Reyes` | *"Which one did you mean: Ana Lopez or Ana Reyes?"*; the name in reply runs the question for her | ✅ rule *(Phase 4 review round 2 #3 — it said "couldn't find")* |

*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `what about Topsoil?` | conversation `ref-material-in-estimates-then-another` | ✅ the planner handles it — was a gap: after a material's quantity across estimates, the follow-up swaps the material *(#789's fix added a customer, not a material)* |

---

# 9. Safety refusals

## 9.1 Bulk delete — 🛑 refused

Phrasings with quantifier + delete verb. Enforced at the orchestrator layer AND defensively at each domain agent's `process()`. Verbs: `delete`, `remove`, `drop`, `wipe`, `clear`. **Note:** `clear all {resource}` (e.g. "clear all estimates") **is** treated as a bulk delete and refused — the May 2026 "remove clear" change was reverted (2026-06-02). The one exemption is estimate/quote **creation** requests whose job description mentions clearing/removing work ("create an estimate to clear out all the weeds in my backyard") — these are detected by `is_estimate_creation_request()` and pass through to `create_estimate`, never the refusal guard.

| Phrasing | Plan | Status |
|---|---|---|
| `delete all {plural}` | refuse `bulk_delete` | 🛑 refusal message, `needs_clarification=True` |
| `remove every {singular}` / `wipe my {plural}` / `clear all {plural}` | refuse `bulk_delete` | 🛑 |
| `create an estimate to clear out all the {stuff}` | `create_estimate` scope | ✅ not refused |

Applies to all 4 CRUD resources. Maple-only policy — HTTP routers may still expose bulk delete for UI workflows.

## 9.2 Equipment — 🛑 refused

Equipment isn't a Maple resource. A phrasing that says "equipment", "equipments" or "machinery" (Spanish "equipo(s)", "maquinaria") refuses with `EQUIPMENT_REFUSAL_MESSAGE` (`is_equipment_request`, `agents/text_utils.py:403`). Naming a machine — excavator, skid steer, bobcat — without one of those words does not trigger it. "Equipment operator" is a role, not equipment: since 2026-09-27 (#693) the "Heavy Equipment Operator" role is read, created and edited, and only the rest of the message is checked.

| Phrasing | Plan | Status |
|---|---|---|
| `show all my equipment` / `create a new equipment` / `delete the excavator equipment` | refuse `equipment` | 🛑 |

## 9.3 Material category management — 🛑 refused

Material categories (Hardscape, Masonry, etc.) live in the catalog UI. Maple can list/filter/reassign but not create/rename/delete them.

| Phrasing | Plan | Status |
|---|---|---|
| `create a new category` | refuse `material_category` | 🛑 via `is_material_category_management_request` |
| `rename the Masonry category` / `delete the Hardscape category` | refuse `material_category` | 🛑 |

## 9.4 Partial bulk / small-N destructive — 🛑 refusal

| Phrasing | Plan | Status |
|---|---|---|
| `delete the last 5 contacts` | refuse `bulk_delete` | 🛑 N > 1 but not "all" — extended `_BULK_DELETE_PATTERNS` to catch `last/first/next/previous N` quantifiers (xfail-wave-3 Workstream A) |
| `remove the first 10 properties` / `drop the next 3 materials` | refuse `bulk_delete` | 🛑 |

## 9.5 Template creation / update / duplicate — 🛑 refused

Templates must be created, edited, and duplicated through the Templates page in the portal UI. Maple can list, view, delete, and apply templates to estimates — but not create, update, or copy them.

| Phrasing | Plan | Status |
|---|---|---|
| `create a new template` | refuse `template_edit` | 🛑 directs user to the Templates page |
| `add a template` / `make a new template called Driveway` | refuse `template_edit` | 🛑 |
| `update {template}'s description` / `change the profit margin of {template} to 20` | refuse `template_edit` | 🛑 |
| `duplicate template {template}` / `copy template {template}` | refuse `template_edit` | 🛑 |

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

| Phrasing | Plan | Status |
|---|---|---|
| `set the default markup to 20%` / `change our company tax rate` / `what's the material markup?` | refuse `out_of_chat` `settings_financial` | 🛑 redirected to Settings → Financial tab (Owners and Admins); work-item markup/overhead/tax stay Maple's (§1.5.7) |
| `invite Sam to the team` / `add a new team member` / `remove a user` | refuse `out_of_chat` `team` | 🛑 redirected to Settings → Team Members tab |
| `upgrade my plan` / `how many Maple credits do I have left?` / `change my credit card` / `show my invoices` | refuse `out_of_chat` `billing` | 🛑 redirected to Settings → Billing tab |
| `load the standard materials` / `reload standard people` | refuse `out_of_chat` `load_standard` | 🛑 redirected to the Materials page's Categories tab (standard materials come in by category); the standard roles are always on the People page — Show Hidden or Unhide All in its actions menu shows hidden ones *(2026-10-21)* |
| `import contacts from a CSV` / `upload a spreadsheet of materials` | refuse `out_of_chat` `csv_import` | 🛑 redirected to the CSV upload on the Properties, Contacts or Materials page |
| `add a unit called pallet` / `rename the unit bag` | refuse `out_of_chat` `units` | 🛑 redirected to the Materials page's Units tab (categories: §9.3) |
| `add a division called Snow Removal` | refuse `out_of_chat` `divisions` | 🛑 redirected to Settings → Divisions tab; setting a work item's division stays Maple's (§1.5.2) |
| `unlink Carla Diaz from 12 Oak St` / `detach the contact` | refuse `out_of_chat` `unlink` | 🛑 redirected to the property or contact in the app; unlinking a task's property is Maple's (§7.6) |
| `duplicate the patio estimate` | refuse `out_of_chat` `duplicate` | 🛑 redirected to Duplicate in the row's menu on the Estimates, Materials or People page — a standard material's copy is Maple's since 2026-10-19 (§4.1, D2) |
| `make a copy of {material}` | `copy_material` | ✅ a standard material is copied as the company's own; the company's own material gets the redirect above — the policy decides, from the record (`policy._check_catalog_ops`; gap plan 2026-10-19, D2) |
| `clone this material` [material_focus] | `copy_material` | ✅ the material in focus, decided as above; with none in focus the model either plans the copy (Maple asks which) or gives the Duplicate redirect — both fine *(live run 2026-10-20: it was in the refusal row above until D2)* |
| `generate the document for E0042` / `export a PDF` / `create a Google Doc` | refuse `out_of_chat` `documents` | 🛑 redirected to the estimate's Documents button *(user decision 2026-09-27: no document generation from chat)* |
| `add a photo to the task` / `upload a video` | refuse `out_of_chat` `media` | 🛑 with no file on the message or the previous one: says to attach it with the + button and name the record (`MEDIA_ATTACH_REFUSAL`; a video always goes on the task in the app); while `MAPLE_ATTACHMENTS_ENABLED` is off, today's redirect to Photo or Video on the task (Maple attachments, 2026-10-18) |

Detectors are narrow on purpose — a false positive refuses something Maple can do: "delete the duplicate contact" is a delete, "set the markup on work item 1 to 20%" is Maple's. Tests: `tests/test_out_of_chat_redirects.py`, `tests/test_maple_refusal_is_final.py`.

## 9.9 Deletes — a plain yes, from someone allowed to *(2026-09-27)*

Every Maple delete asks first, and only a plain yes confirms it — "yes", "yes, delete it", "confirm delete". Before, the catalog agents confirmed on any message *containing* "yes", "confirm" or "delete it" (#674): "delete it" deleted at once, "no, don't delete it" confirmed, and so did a name like "Reyes". A delete question lives one turn (§10.6). Deleting a property, contact, material, role, template or task is for Owners and Admins, as in the app (`delete_role_refusal`, `agents/conversation/delete_confirmation.py`); a Member is told so. A standard material is hidden rather than deleted, and a company material an estimate or template uses is refused (§4.1, 2026-10-15); a standard role is hidden rather than deleted too (§5.8a, 2026-10-21). A request about a record's links ("remove Ana from 12 Oak St") never deletes the record — it is redirected (§9.8); a request about its notes deletes the note you name, after asking (§3.9).

---

# 10. Multi-turn patterns

## 10.1 Field-then-value flow (all 4 CRUD resources)

*(2026-07-22: Tasks add a create-side variant — a create request with no
title stashes an awaiting-title `pending_intents` entry, and the bare
reply to "What should the task say?" (until 2026-09-30, "…be called?") becomes the text, keeping any
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

| Phrasing | Plan | Status |
|---|---|---|
| `how many cubic yards of mulch for 2000 sq ft at 3 inches` | `calculate` | ✅ `area_coverage` — needs area_sqft, depth_inches; gives cubic yards |
| `how much concrete for a 10x12 slab 4 inches thick` | `calculate` | ✅ `concrete_volume` — needs length_ft, width_ft, depth_inches; gives cubic yards |
| `how many lbs of grass seed for 5000 sq ft at 4 lbs/1000` | `calculate` | ✅ `seed_coverage` — needs area_sqft, application_rate; gives pounds |
| `how many 8-ft fence panels for 100 linear feet` | `calculate` | ✅ `linear_material` — needs linear_ft (opt. piece_length_ft); gives pieces |
| `how many 12x12 pavers for 200 sq ft` | `calculate` | ✅ `paver_count` — needs area_sqft, paver_length_inches, paver_width_inches; gives pieces |
| `convert 100 sq ft to sq m` | `calculate` | ✅ `unit_conversion` — needs value, from_unit, to_unit; gives the converted value |
| `how many tons of gravel for 100 sq ft 4 inches deep` | `calculate` | ✅ `aggregate_tons` — needs area_sqft, depth_inches (opt. tons_per_cubic_yard, default 1.5); gives tons *(2026-06-15)* |
| `how many bags of mulch for 100 sq ft at 3 inches` | `calculate` | ✅ `mulch_bags` — needs area_sqft, depth_inches (opt. bag_size_cuft, default 2); gives bags *(2026-06-15)* |
| `how many blocks for a 20 ft wall 3 ft high with 12x8 blocks` | `calculate` | ✅ `retaining_wall_blocks` — needs wall_length_ft, wall_height_ft, block_length_inches, block_height_inches; gives blocks *(2026-06-15 — regex doesn't extract block dims; LLM extraction path)* |
| `how many steps for a 42 inch rise` | `calculate` | ✅ `step_count` — needs total_rise_inches (opt. target_riser_inches, default 7); gives steps *(2026-06-15)* |
| `how many plants for 100 sq ft at 12 inch spacing` | `calculate` | ✅ `plant_count` — needs area_sqft, spacing_inches (opt. pattern square/triangular, default square — "triangular spacing"); gives plants *(2026-06-15 — regex defers: "12 inch spacing" is spacing not depth)* |

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

## 10.3.2 Open-math reasoning path (no curated formula) — *behind `CALCULATOR_OPEN_MATH_ENABLED`, default off (2026-06-29)*

When the extraction classifier decides **no curated formula faithfully models**
the request, it returns `open_math` instead of force-fitting the nearest type.
The researcher model then proposes an interpretation, the assumptions it made,
and one or more options — each an arithmetic *expression*, never a final number
— and a sandboxed allow-list evaluator (`safe_eval`) computes them. The reply
states the assumption and shows the working, so every number is auditable.

| Phrasing | Plan | Status |
|---|---|---|
| `how many 3x2 ft stepping stones along a 20 ft path, 3 in apart` | `calculate` | ✅ spaced layout, open_math — no curated formula fits: gaps on a linear run; two possible orientations *(flag)* |
| `how many sq ft can 25 yards of mulch cover` / `how much area does 10 tons of gravel cover at 3 in` | `calculate` | ✅ reverse / inverse coverage, open_math — no curated formula fits: formulas run forward (area + depth → quantity); the reverse has no formula and needs an assumed depth *(2026-06-29 — flag)* |
| `how much mulch for an L-shaped bed, 10x4 plus 6x3` | `calculate` | ✅ composite / irregular shape, open_math — no curated formula fits: multiple sub-shapes *(flag)* |

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
| `not right now` / `nah, leave it` / `Please don't` / `don't` / `not yet` | acknowledge, clear the slot, leave unlinked | ✅ rule *(2026-10-03, #329 — read as a property name, and the lookup re-prompted; "please" was a yes with the value "don't". `replies.declines_offer`, in the generic optional follow-up and the legacy estimate one)* |
| **pivot** — next message is clearly a fresh request (a new CRUD command or question) | drop the slot silently, route normally | ✅ rule *(pre-existing escape hatch in `handle_pending_optional_follow_up`; guard now documented inline. **2026-07-28** — the escape hatch ran at the confirm stage only; it now covers the collect-value stage too, because that stage can keep the slot open across turns. The follow-up field's own domain is exempt, so `the Downtown property` stays a value.)* |
| **unresolved answer** — the named property doesn't match anything (typo, ambiguous, or a property that doesn't exist) | re-ask and keep the slot open so the next reply is still read as the property | ✅ rule *(**2026-07-28** — previously the slot was popped before delegating and never restored, so the retry fell through to intent classification and was answered as a brand-new create request ("Sure, I'll help you create an estimate!"). `_rearm_on_unresolved` restores the record whenever the delegated agent returns `needs_clarification`.)* |
| `{name} - {street}` composite (e.g. `Primavera - 153 Asharoken Ave`) | resolve against the Property catalog | ✅ rule *(**2026-07-28** — `_resolve_property_address` gained a reverse-containment fallback tier, so a label combining both fields matches even though neither field contains the whole string.)* |
| **planner:** `yes` → *"Which property should I link estimate {EST} to?"* → `link it with Primavera - 153 Asharoken Ave` (the property's name misspells its street; its street is `153 Asharoken Avenue`) | `link {a: the estimate in focus, b: property}` — a `{name} - {street}` / `{name}, {street}` name is the one property every part names | 🤖 planner *(2026-10-11 — no name or street is the whole text, and it was "I couldn't find a property matching …" on every retry. `resolve._by_parts`: a part naming nothing, or parts naming different properties, finds none — never a guess. Today's pipeline read "of this estimate to Primavera …" as the name, then took the bare retry for a new estimate)* |
| misspelled or re-worded property (`primavara`, `153 Ashroken Ave`) | fuzzy-resolve, then confirm before linking | ✅ rule *(**2026-07-28 (b)** — tier 3 of `_resolve_property_address` + `pending_property_link_confirmation`. Reads disclose instead of confirming.)* · 🤖 planner: the closest name or street, asked "Just to check" before a write *(2026-10-12 — none found)* |
| **ordinal reply to a near-tie list** — `2` / `(2)` / `option 2` | select that candidate from the list just shown | ✅ rule *(**2026-07-28 (b)** — candidate ids persisted on the pending record; out-of-range and sub-3-character replies re-ask instead of guessing.)* |
| **word-ordinal reply** — `the first one` / `second` / `2nd` / `the last one` / `the 2` | select that candidate from the list just shown | ✅ rule *(**2026-07-30** — reported: Maple offered "(1) Bob Residential; (2) Tang's Resident" and "The first one." was resolved as a property *name*, answering "I couldn't find a property matching 'The first one.'". The matcher was digits-only. Now `agents/text_utils.py::match_ordinal_reference` — `first`–`tenth`, `1st`–`10th`, `last`, and a digit with an optional leading determiner — shared with the Task confirmation flow so two numbered menus can't accept different words. Anchored at both ends, so a property named `First Street` still reaches the correction path.)* |
| **unresolvable reply while a candidate list is on screen** | re-show the numbered list | ✅ rule *(**2026-07-30** — with candidates armed there is no pinned property, so this branch rendered the confirm prompt's placeholder label: "I believe you are looking for 'that property'".)* · 🤖 planner: the menu again *(2026-10-12)* |

*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `I'll do it from the portal` | conversation `ref-link-offer-done-in-the-portal` | ✅ the planner handles it — was a gap: a no to the offer — "Okay, I left … unchanged." — never a property name; also "I'll do it myself", "I'll link it later" |
| `link it to 9 Maple Ave, Toronto` | conversation `ref-link-to-a-street-and-its-city` | ✅ the planner handles it — was a gap: a street and its city name the property at that street in that city; a city alone names none *(2026-10-11; 2026-10-13)* |

**Remaining ⚠️ in this section (§10.4):** none — `I'll do it from the portal` is a decline since 2026-10-13 (`replies.declines_offer`), the other soft negatives since 2026-10-03 (#329). **Note (2026-07-28):** now that an unresolved answer keeps the slot open, these soft negatives re-prompt instead of falling through — the same wrong outcome, but the user is no longer silently dropped out of the flow, and a pivot ("show me my estimates") still releases it. Tests: `tests/test_maple_estimate_field_edits.py::TestEstimateOptionalFollowUp` + `::TestEstimateFollowUpConfirmStage` (incl. the legacy-defers ordering test), `::TestFollowUpSurvivesUnresolvedValue`, and `tests/test_agent_helpers_delegate_create_estimate.py`.

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

**The portal shows the open question** (2026-09-27, #696): while one is open the composer reads "Waiting for your answer · Cancel" (Cancel sends "cancel"), a yes/no question offers Yes/No chips, and a reload restores it.

**Creates ask one field at a time** (2026-09-27): a contact, property, role or material create that is missing details asks for the next one alone and takes a bare reply as its value — "Dan Park" for the name, "30" for a wage, "Bulk Materials" for a category (§3, §2, §5.10, §4.11).

## 10.7 The record in focus *(2026-09-27)*

Each `active_<domain>_id` anchor records the turn it was set on. An anchor set this turn or last — or the record the portal page is showing — is fresh, and "it" acts on it. An edit that would reach an older anchor only through "it" or no name at all asks first: *"Just to check — do you mean Ana Reyes?"* (#677, `agents/conversation/focus.py`). Deletes (their confirmation names the record already) and notes (they overwrite nothing) don't ask. Pronouns pick the domain before recency does: "him"/"her" mean the contact, "there" the property. A record the message names always beats the one in focus ("show me contact Bob Lee" with Ana in focus shows Bob).

**The record open on the page** (2026-09-27, design §8): the Contacts and Properties pages announce their selected record and the Tasks page the task open in its dialog; the Maple panel sends it as `client_context.viewed_record` (`routers/agent_helpers/viewed_record.py`), as the estimate page has always sent its estimate. A new visit makes that record the fresh anchor for its domain — loaded company-scoped, never from another company's id — and the same visit never pulls the focus back from a record the chat moved on to.

| Phrasing | Plan | Status |
|---|---|---|
| `add a note: prefers mornings` [contact_focus] | `add_note` | ✅ with Ana Reyes open on the Contacts page, the note is filed on Ana *(it asked "which fields?", even right after "show me contact Ana Reyes")* |
| `what's her phone?` [contact_focus] | `get_contact` field=phone | ✅ the contact open on the page — that record's details *(it went to the user guide)* |
| `what's the city?` [property_focus] | `get_property` field=city | ✅ a property open on the page — that record's details *(it went to the user guide)* |

**Answering "Just to check"** (2026-09-29, name-answers plan phase 4): "yes" runs the request on the record asked about; "no" asks *"Okay — which contact did you mean?"*, and — since phase 4 — a name in reply finishes the request on the record named (`agents/conversation/record_names.py`, `routers/agents.py::_answer_name_question`).

| Phrasing | Plan | Status |
|---|---|---|
| `change the city there to Hamilton` [property_focus] | `update_property` fields.city=Hamilton | ✅ the planner handles it — was a gap: should change its city; the Property agent parses no field from "the city there" *(found 2026-09-29; "change its city to Hamilton" works)* |

*Not yet in the Plan format — several turns, or a record in focus that Maple asks about first (phase 3):*

| Turns | Behavior | Status |
|---|---|---|
| `change her phone to …` → *"Just to check — do you mean Ana Reyes?"* → `no` → `Bob Lee` | Bob's phone changes; Ana's doesn't | ✅ rule *(2026-09-29 — the name was read as a new request and the change was lost)* |
| … → `no` → `Ana` (two contacts called Ana) | *"I found 2 contacts called Ana: 1. Ana Lopez 2. Ana Reyes"*, and the number or name picks | ✅ rule *(2026-09-29)* |
| … → `no` → `Zed` (no such contact) | *"I couldn't find a contact called Zed. Which contact did you mean?"* — asked once more, then left | ✅ rule *(2026-09-29)* |
| … → `no` → `yes` | a stray yes — Maple says it isn't waiting on an answer; a yes names no one | ✅ rule |
| `change its city to Hamilton` → *"Just to check — do you mean Elm House?"* → `no` → `9 Maple Ave` | the property named by its street (or name) changes | ✅ rule *(2026-09-29)* |
| the same for a material, role or task in focus | the record named — by exact name, then a whole word | ✅ rule *(2026-09-29; a role or template name that reads as a command, e.g. "Remove Crew", has no name source and may still be read as a request — deferred with phase 6)* |

*On the planner:*

| Phrasing | Plan | Status |
|---|---|---|
| `change the homeowner's phone to 416-555-9999` | conversation `contact-stale-anchor-asks` | ✅ the planner handles it — was a gap: "the homeowner" is the contact in focus, and a stale focus asks "Just to check" first *(#759)* |

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

| Phrasing | Plan | Status |
|---|---|---|
| `her phone is 519-555-1234` / `519-555-1234` [contact_focus] | `update_contact` fields.phone=519-555-1234 | ✅ the contact just created or shown *(2026-09-27)* |
| `her email is {email}` / `{email}` [contact_focus] | `update_contact` fields.email | ✅ the contact just created or shown *(2026-09-27)* |
| `zip M4B 1B3` [property_focus] | `update_property` fields.postal_zip | ✅ the property just created or shown *(2026-09-27, §2.6)* |

**Refining the list just shown** (2026-09-27, the same module): after an
estimate or task list, `just the drafts`, `which ones are on hold?`, `only the
ones over $1000`, `sort them by total`, `what's the total of those?`, `just the
overdue ones`, `how many is that?` replay that list with the refinement added
— so refinements chain (§1.1, §7.5). A task-list refinement must read as a
task filter — a status, an assignee, a due window, or a place said with
"at" / "for" / "in" (`which ones are done?`, `just mine`, `just the ones at
Elm House`); `what is the rate for Foreman?` after a task list is its own
question (#740, 2026-10-04).

## 10.9 "Show more" *(2026-09-27)*

A list that stops short of the whole result says how far it got and remembers where it stopped (`agents/conversation/paging.py`). On the next turn, `show more` / `more` / `next page` / `the rest` / `keep going` replays the same request — filters included — from there. Good for one turn; with no longer list open, Maple says so. Tasks page this way today (§7.5); other lists can adopt the same helper.

| Phrasing | Plan | Status |
|---|---|---|
| `show more` / `more` / `next page` / `the rest` / `keep going` | conversation `task-list-show-more` | ✅ the list just shown, from where it stopped; with no longer list open, Maple says so |

## 10.10 Conversation turns *(2026-09-27)*

Turns about the conversation itself are answered after the question gate has had its chance — an open question gets its "yes" first (`agents/conversation/meta.py`). These used to fall through to "I'm not quite sure what you mean" or a material lookup ("go ahead", "never mind" → `get_material`).

| Phrasing | Plan | Status |
|---|---|---|
| `thanks` / `ok thanks` / `great` / `perfect` / `that's all` | `acknowledge` | ✅ no question open: "You're welcome — anything else I can help with?" |
| `cancel` / `never mind` / `stop` | `cancel` | ✅ no question open: "There's nothing to cancel right now — …" |
| `yes` / `no` / `go ahead` | `acknowledge` | ✅ a stray one, no question open: "I'm not waiting on an answer right now — …" |
| `No, set the markup to 25%` / `keep it at 20% markup` / `wait, add a work item called Fence` [est] | `edit_estimate` | ✅ nothing asked: the request runs — only a plain no is a stray no *(2026-10-01, #706 — they were answered "I'm not waiting on an answer")* |
| `don't forget to call Bob Lee tomorrow` | `create_task` | ✅ nothing asked: the request runs — only a plain no is a stray no *(2026-10-01, #706 — they were answered "I'm not waiting on an answer")* |
| `no, don't delete it` / `don't` / `no wait` / `keep it` / `leave it` / `don't delete Ana Reyes` | `acknowledge` | ✅ nothing asked: "I'm not waiting on an answer right now — …" — a decline that asks for nothing stays a stray no *(2026-10-01, #706 review — "no, don't delete it" and "don't delete Ana Reyes" offered the delete; a negated delete is a no whatever it names)*; `don't delete Ana Reyes` is *"Okay — I'll leave it as it is."* *(2026-10-11, #847)* |
| `repeat that` / `say that again` | `repeat` | ✅ Maple's last reply again |
| `start over` / `reset` / `clear the chat` | `start_over` | ✅ points to the clear button; drops anything Maple was waiting on |
| `start a new chat` / `new conversation` | `start_over` | ✅ *(2026-10-19 review — probed live; the reply's words are a gap, §10.10)* |
| `show me my past conversations` / `open my last chat` | refuse `out_of_chat` `history` | 🛑 *"I only see this conversation. Your past conversations are under Chat history at the top of the Maple panel — open one there to pick it up again, or delete it. …"* — G10 (gap plan 2026-10-19, closed the same day) |
| `what did we talk about yesterday?` / `what did I ask you last time?` | refuse `out_of_chat` `history` | 🛑 the same — Maple sees only the conversation open now — G11 (gap plan 2026-10-19, closed the same day) |
| `delete this conversation` / `delete my chat history` | refuse `out_of_chat` `history` | 🛑 the same — the one open now can't be deleted — G12 (gap plan 2026-10-19, closed the same day) |
| `undo that` [est] | `undo_last` | ✅ asked first (D1, Simon 2026-10-19: never on her own) — *"Undo my last change to E0042 — title back to Jones backyard? (yes/no)"*; the yes sets each field back while the record is as Maple left it, never on an estimate that has left Draft/Review since; a create is undone by deleting it while unchanged since, asked as a delete; a note, link, status or delete is said as a change she can't undo — G23 (gap plan 2026-10-19, closed the same day) |
| `take that back` [contact_focus] | `undo_last` | ✅ the same: Maple's own last change, asked first — G23 (gap plan 2026-10-19, closed the same day) |
| `put the price back to what it was` [material_focus] | `undo_last` | ✅ the same — G23 (gap plan 2026-10-19, closed the same day) |

**Start over since session history** (2026-10-19 review, G13 in the
[gap plan](plans/2026-10-19-maple-phrasing-gaps-plan.md)): `start over` and
`start a new chat` plan right; the reply (`meta.START_OVER`) pointed to "the
clear button at the top of the Maple panel" — since 2026-10-16 the panel's
button is *Start a new session*, and the old conversation is kept under *Chat
history*. Fixed the same day: it names both.

**Language** (2026-09-27): the conversation keeps the language the user is writing in. A short reply ("sí", "2", "Cambridge") is answered in that language rather than re-detected from two characters, and a language-neutral message (a code, a number) never switches it (`services/translation.py::conversation_language`).

## 10.11 Files on the message *(2026-10-18)*

A photo or PDF sent with a message (the + button, or dropped on the message box; `POST /agents/attachments`, then `attachment_ids` on the turn) is read once at upload and shown to the planner as a `FILES_ON_MESSAGE` block. The planner puts it on the record the user names (`attach` on `add_note`, `create_task`, `update_task`), reads it back (`describe_files`), or copies facts out of it into a scope, a body or a description. The file is remembered for **one more message** (`last_files`, the state's "Files on the previous message"), so a question about it and then "attach it" works, and so does the answer to "which task?" — when Maple asks something about a request that used the previous message's file, or asks which record was meant, the file is kept for the answer too; a question about anything else lets it lapse, and a new record made from an answer takes the file only when the request it answers used it. Behind `MAPLE_ATTACHMENTS_ENABLED`; the plan is [`plans/2026-10-18-maple-attachments-design.md`](plans/2026-10-18-maple-attachments-design.md).

| Phrasing | Plan | Status |
|---|---|---|
| `what's in this photo?` / `read this` / `what does it say?` [none+photo] | `describe_files` | ✅ with a file on the message (or the previous one): what Maple read from each file — its text, then what it shows, in a plain block (a link in a file is shown, never clickable); a file that couldn't be read says so; with none, `NO_FILE_ON_MESSAGE_REFUSAL` (Maple attachments, 2026-10-18) — the portal never sends a file without words (Simon 2026-10-19); the API reads a files-only message the same way |
| `attach it to T0042` / `now put it on the fence task` [none+prev_photo] | `update_task` attach | ✅ the previous message's file, one turn later — after `what's in this photo?` (Maple attachments, 2026-10-18) |
| `the one at Elm House` [task_focus+prev_photo] | `update_task` attach | ✅ answering "which task?" to `attach this to the fence task`: the file rides along to the answer — the message that carried it is the previous one (Maple attachments, 2026-10-18); and when the question was asked about the previous message's file (`what's in this photo?` → `attach it to the fence task` → "which task?"), the file is kept for the answer too (review round 3 #8) |
| `attach this to T0042` | `update_task` attach | ✅ with the photo two messages back, Maple says there's no file on that message (`NO_FILE_ON_MESSAGE_REFUSAL`) — a file is on its message and the next one only; send it again (Maple attachments, 2026-10-18) |
| `T0042` [none+photo] | `update_task` attach | ✅ a task named with a file on the message and nothing else said: the file goes on the task's media (review 2026-10-19) |
| `Elm House` [none+photo] | `add_note` attach | ✅ a contact, property or estimate named with a file on the message and nothing else said: a note with no words, carrying the file (review 2026-10-19) |
| `what does this quote say, and create a task to call the customer` [none+quote] | `create_task` | ✅ after `describe_files`: the file is read back and the new task is made without it — a plan that reads the files leaves them off the create (review 2026-10-18 #32, 2026-10-19) |
| `attach the photo to T0042 and the PDF to E0042` [none+photo+quote] | ask | ✅ with two or more files on the message, Maple asks first — "Just to check: put all 2 files on each of them? (yes/no)" — since each record would take every file; no leaves it all as it was and says to send each file with its own message (review 2026-10-19 #18) |
| `add a note to it: bring the ladder` [task_focus+prev_photo] | `add_note` parent.domain=task | ✅ just after `create a task from this photo: fix the gate`: the note is added and the photo isn't copied onto the task a second time — "Those files are already on it." (the state says where the previous message's files went; review 2026-10-19 #17) |
| `attach this estimate to Elm House` [est+photo] | `link` | ✅ with a file on the message too: "attach this estimate (or contact) to …" names a record — a link, never the file (review 2026-10-19) |
| `here's a video of the yard, make an estimate` | refuse `out_of_chat` `media` | 🛑 Maple reads photos and PDFs; a video goes on the task in the app — set right when the model refuses it as "other" or equipment (`as_asked_files`) — G14 (gap plan 2026-10-19, closed the same day) |
| `remove the photo from T0042` | refuse `out_of_chat` `media` | 🛑 said as a removal: *"I can't remove a photo or file from chat — …"* (`MEDIA_REMOVE_REFUSAL`) — G15 (gap plan 2026-10-19, closed the same day) |
| `show me the photos on T0042` | `get_task` | ✅ the task's details name its files — *"- Files: 2 — gate_latch.jpg, quote.pdf"* — G16 (gap plan 2026-10-19, closed the same day) |
| `what's in the PDF on Elm House's note?` | `list_notes` | ✅ the notes, each with its files by name, and *"I can only read a file sent with a message — send it here and I'll read it."* — a filed file is never read (D3, Simon 2026-10-19) — G17 (gap plan 2026-10-19, closed the same day) |

**Testing files** (2026-10-19 review, G20): the live run's reference rows
started from a state with no file on the message, so every row above that needs
one was scored without it. The 2026-10-19 rows marked "probed live with … on the
message" were checked by hand with a file in `turn_attachments`; a `[files]`
state for the rows was step 0 of the gap plan, done the same day: a row names its
files after its state — `[est+quote]` on this message, `[task_focus+prev_photo]` on
the one before (`tests/planner_parity/cases.FILES`: photo, quote, card, invoice,
workorder, list). The live run of 2026-10-19 bore it
out: 19 rows needing a file were scored without one — most asked for the file,
two were blockers (`attach this quote to E0042` was redirected as `documents`,
where with no file it should say to attach one; `make a task from this photo`
was the media redirect), and `read this` / `what does it say?` went to help and
small talk.

---

# 11. Help intent

Handled by `agents/orchestrator/help_handler.py` via the `HelpHandler` class. The orchestrator routes to it when `is_help_query()` returns True (`agents/orchestrator/intents.py:487`); the router also short-circuits help before classification (`routers/agents.py:1093`), which is why a question about a record can land here (#691). The agent is always the **Orchestrator Agent** itself — help never dispatches to a downstream domain agent.

**Every answer comes from the user guide** (corrected 2026-09-27). `HelpHandler.build_result` sends the question to the shared LLM responder `answer_from_guide` (`agents/maple_guide/service.py:188`), which answers from `user_guides/users_guide.md`. `HelpHandler.detect_topic()` still classifies the question — personal, cross-domain link, enum, capabilities, how-to, in that order — but the topic is only metadata (`result.topic`): there are no canned enum lists, `valid_values` payloads or `_CONTEXTUAL_EXAMPLES` any more. The topic families below describe classification, not the answer text.

The result payload always has `operation="help"`, `read_only=True`, `topic`, the `SUPPORTED_INTENTS_BY_AGENT` mapping under `result.capabilities`, and `intent="help"` on the envelope. The *classification* is rule-only — it bypasses the LLM classifier even when `use_llm=True` (see `test_orchestrator_help_query_bypasses_llm`) — but the answer is an LLM call.

## 11.1 Capability queries

Direct capability questions. Match via `HELP_DIRECT_HINTS` (`intents.py:299`).

| Phrasing | Plan | Status |
|---|---|---|
| `help` / `help me` / `help please` / `I need help` | `help` | ✅ |
| `what can you help me with?` / `what can you do?` / `how can you help me?` / `what can I ask?` | `help` | ✅ |
| `supported intents` / `capabilities` | `help` | ✅ |
| `what can you calculate?` / `what numbers can you give me?` / `what metrics can you show me?` / `what figures can you tell me?` | `help` | ✅ the guide's §6.6 "Asking for a figure" lists every figure Maple gives (totals, rankings, by month, comparisons, win rate, margin, markup, catalog) and how she reads "sold", tax and periods *(2026-10-01, metrics plan Phase 4 task 6 — the guide had no figures, so the answer couldn't name them. Not the Calculator: no measurement)* |
| `can you tell me my sales?` / `what are my sales?` | `metric` status=sold | ✅ the sold figure itself (§1.12), not a capability answer |

### Feature-definition queries *(2026-07-22)*

A definitional lead-in (`tell me about` / `what is` / `what are` / `explain` / `describe`) followed by a **bare resource noun** routes to HELP (guide-backed answer), not CRUD — previously "tell me about tasks" resolved to `list_tasks` and answered "I couldn't find any matching tasks." Detector: `is_feature_definition_query` (`intents.py`), applied inside `is_help_query` so both tiers share it. Works for every resource noun (tasks, estimates/quotes, properties, contacts, materials, templates, people/labor, to-dos).

| Phrasing | Plan | Status |
|---|---|---|
| `tell me about tasks` / `Tell me about the Tasks feature` | `help` | ✅ guide §7.3 Tasks |
| `what is a task?` / `what are tasks?` | `help` | ✅ |
| `tell me about estimates` / `what are templates?` | `help` | ✅ |
| `tell me about MY tasks` | `list_tasks` filter.assignee=me | ✅ possessive determiner — the user's data, not a definition; "my tasks" are the user's own (Simon, 2026-10-09) |
| `tell me about task {task}` | `get_task` | ✅ named lookups unaffected |
| `tell me about {contact}` | `get_contact` | ✅ named lookups unaffected |

## 11.2 Enum queries

Match via `HELP_ENUM_KEYWORDS` + `HELP_QUESTION_CUES` (`intents.py:309-322`). `HelpHandler.detect_topic()` disambiguates by domain keyword; the answer comes from the user guide.

### Contact roles — topic `contact_roles` (`ContactRole`: Home Owner, Manager, Administrator)

| Phrasing | Plan | Status |
|---|---|---|
| `what are the contact roles?` / `what are the valid contact roles?` / `what are the valid roles for a contact?` | `help` | ✅ |
| `what roles are available?` | `list_labours` | ✅ |
| `available values for role` / `choices for contact role` | `help` | ✅ |

### Estimate statuses — topic `estimate_statuses` (`EstimateStatus` has 13 values, §1.4)

| Phrasing | Plan | Status |
|---|---|---|
| `what are the estimate statuses?` / `what statuses can an estimate have?` / `what are the valid estimate statuses?` | `help` | ✅ |

### Estimate divisions — topic `estimate_divisions`

| Phrasing | Plan | Status |
|---|---|---|
| `what are the estimate divisions?` / `what are the valid estimate divisions?` / `which divisions can an estimate have?` | `help` | ✅ asking which there are is help; only adding, renaming or deleting divisions is done in the app *(2026-10-12 — the model refused it as `out_of_chat` in some runs; `said.asked_which_there_are` answers it as help before anything runs)* |

## 11.3 Procedural how-to queries

Match via `HELP_INSTRUCTIONAL_PATTERNS` (`intents.py:337`): `how do i`, `how can i`, `how to`, `how would i`, `how should i`, `steps to`, `step by step`, `process for`, `process to`, `guide for`, `guide to`, `explain how`, `show me how`, `walk me through`, `what are the steps`, `what's the process`.

When an instructional pattern hits, `detect_topic()` tries to match an action keyword (`create`, `update`, `delete`, `list`, `get`, `find`, `add`, `edit`, `remove`) and a domain keyword (`contact(s)`, `estimate`/`quote(s)`, `property`/`properties`, `material(s)`, `labour`/`labor`). Result is a `how_to_<action>_<domain>` topic; falls back to `how_to_manage_<domain>s` if only domain matched, or `how_to_use_system` if neither.

### Full how-to (action + domain matched)

| Phrasing | Plan | Status |
|---|---|---|
| `how do I create an estimate?` / `explain how to create an estimate` | `help` | ✅ |
| `how do I update a contact?` / `how do I create a contact?` / `how do I create a property?` | `help` | ✅ |
| `steps to add a material` / `how can I update a material price?` | `help` | ✅ |
| `how do I archive an estimate?` | `help` | ✅ *(no action keyword "archive", falls back to manage)* |
| `walk me through making a contact` | `help` | ✅ *("making" isn't an action keyword)* |
| `how do I approve an estimate?` | `help` | ✅ *("approve" not an action keyword)* |

### Domain-only how-to (no action keyword matched)

| Phrasing | Plan | Status |
|---|---|---|
| `guide to setting up a property` | `help` | ✅ (pluralization defect closed by Wave 1 Phase 1) |
| `what's the process for archiving an estimate?` | `help` | ✅ |

### Generic how-to (no action, no domain)

| Phrasing | Plan | Status |
|---|---|---|
| `how do I use this system?` / `show me how to use Maple` / `how to get started` | `help` | ✅ |

## 11.4 Help vs. CRUD precedence

When a message contains **both** a CRUD intent (firm action+domain match) and an enum keyword, CRUD usually wins. Two important carve-outs:

| Phrasing | Plan | Status |
|---|---|---|
| `help me create a contact for Jane` | `create_contact` fields.first_name=Jane | ✅ "help me" is a polite prefix, not an instructional question. CRUD action+domain is firm. |
| `how many labour roles do I have?` | `list_labours` count | ✅ `action == "list"` short-circuit at `intents.py:517` prefers CRUD over help even though "roles" is an enum keyword. |
| `what are the material categories?` | `list_material_categories` | ✅ Rule-level CRUD match fires before help classifier. See §9.3 refusal for create/delete variants. |
| `how do I create a contact?` | `help` | ✅ Instructional pattern ("how do i") always wins over CRUD — `intents.py:506`. |

## 11.5 Help gaps

Phase 1 of the xfail backlog (plan: `documentation/development/plans/maple-xfail-wave-1.md`) closed most §11.5 entries on 2026-05-02. Remaining gaps below are awaiting Wave 2 design work.

| Phrasing | Plan | Status |
|---|---|---|
| `tutorial` / `getting started` / `docs` / `documentation` | `help` | ✅ (Phase 1). |
| `examples` / `give me some examples` / `what kinds of things can I ask?` | `help` | ✅ (Phase 1). |
| `what can't you do?` / `what are your limitations?` | `help` | ✅ (already covered before Phase 1). |
| `does Maple support templates?` / `is there a way to add a note to a property?` | `help` | ✅ (Phase 1) — equipment refusal now gated by `_looks_interrogative`; `is there a way` and `does maple support` added to `HELP_INSTRUCTIONAL_PATTERNS`. |
| `what is a work item?` / `what's a property?` | `help` | ✅ glossary / terminology help (already covered). |
| `what fields does a contact have?` | `help` | ✅ schema help (already covered via fallback). |
| `what happens when I approve an estimate?` / `what does archive do?` | `help` | ✅ action-semantics help (already covered via fallback). |
| `how does Maple work?` / `explain Maple to me` / `what do you do?` | `help` | ✅ (Phase 1). |
| `what are the labour units?` / `what are the material units?` | `help` | ✅ (Phase 1) — `unit`/`units` added to `HELP_ENUM_KEYWORDS`; §5.12 + §5.13 in `users_guide.md` provide source content. Asking which there are is help, never `out_of_chat` `units` — only adding, renaming or deleting a unit is done in the app *(2026-10-12 — the model refused the labour units as `out_of_chat` in some runs; `said.asked_which_there_are` answers it as help before anything runs)* |
| `I am lost` / `I am stuck` | `help` | ✅ (Phase 1). |
| `what should I ask?` / `what can I do?` | `help` | ✅ (Phase 1). |
| `list your features` | `help` | ✅ (Phase 1). |
| `how do I add a work item?` | `help` | ✅ (Phase 1) — `work item`/`job item`/`line item` detected and routed to estimate scope. |
| `how do I link a contact to a property?` | `help` | ✅ (Phase 1) — cross-domain detection runs before single-domain loop; §5.11 in `users_guide.md`. |

### Pluralization defect — `how_to_manage_propertys` (closed Phase 1)

`HelpHandler.detect_topic` previously returned `f"how_to_manage_{domain_name}s"`, which produced `how_to_manage_propertys` for the property domain. Phase 1 introduced an inline `plural_topic` map (`property → properties`, others append `s`) so the topic key round-trips correctly to `how_to_manage_properties`.

## 11.6 Social & personality

Maple handles greetings and personal/anthropomorphized questions in **two tiers**:

1. **Bare greetings** (`hey`, `hi maple`, `good morning`) are caught in the **orchestrator** (`agents/orchestrator/service.py`, `_detect_policy_short_circuit` via `is_greeting`) and answered with an instant canned reply from `GREETING_RESPONSES` in `agents/text_utils.py`. This is a **new `social` intent** (operation `social`, `read_only`) — **not** a help topic — so there is **no LLM call**. Suggestion chips come from `_SOCIAL_SUGGESTIONS`.
2. **Personal questions** (`how are you?`, `what do you look like?`, `are we friends?`) are detected by `is_personal_question` in `agents/text_utils.py` and routed through the **existing help path** — `HelpHandler.detect_topic` returns the **new `personal` topic** — and answered by the LLM guide responder (`agents/maple_guide/service.py`) **from Maple's persona** (`agents/maple_persona.py`), via a rule-1 exemption in the guide prompt.

The personal-question detector is deliberately **topic-keyed** so product-capability phrasings stay in the product lane (see the Negatives table below).

### Greetings — `social` intent (canned, no LLM)

| Phrasing | Plan | Status |
|---|---|---|
| `hey` / `hi` / `hi maple` / `hello` / `howdy` | `social` | ✅ canned |
| `good morning` / `good afternoon` / `good evening` | `social` | ✅ canned |
| `hola` / `buenos días` | `social` | ✅ canned — Spanish, defense-in-depth |

### Personal questions — `personal` help topic (LLM, persona-answered)

| Phrasing | Plan | Status |
|---|---|---|
| `how are you?` / `how's it going?` | `social` | ✅ feelings |
| `what do you look like?` | `social` | ✅ appearance |
| `are you hot?` | `social` | ✅ appearance — *playful deflect* |
| `are we friends?` | `social` | ✅ friendship |
| `are you married?` / `do you have a partner?` | `social` | ✅ relationships — *playful deflect* |
| `i love you` | `social` | ✅ flirty — *playful deflect, no reciprocation* |
| `are you an AI?` | `social` | ✅ identity — *honest yes* |
| `how old are you?` / `where do you live?` / `what's your sign?` | `social` | ✅ biography |

### Negatives (stay in the product lane)

These read like questions *about* Maple but are really **capability / CRUD** requests — the detector deliberately excludes them so they route to normal help/CRUD, **not** `personal`.

| Phrasing | Plan | Status |
|---|---|---|
| `are you able to add contacts?` | `help` | ✅ (correctly excluded) |
| `can you create an estimate?` | `create_estimate` | ✅ (correctly excluded) |
| `how are you estimating this job?` | `help` | ✅ (correctly excluded) |
| `how are you able to help me?` | `help` | ✅ (correctly excluded) |

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
| metrics *(2026-09-30)* | 6/6 | not yet run | covered (the `analytics_metric` grammar entries, §1.12) |
| metrics_paraphrase *(2026-09-30)* | 0/3 (known gap) | not yet run | LLM tier's by design: classifier + metric spec (§1.12) |
| metrics_ranking *(2026-09-30, Phase 2)* | 4/4 | not yet run | covered (rankings and by month, §1.12) |
| metrics_compare *(2026-09-30, Phase 2)* | 3/3 | not yet run | covered (period comparisons, §1.12) |
| metrics_ratio *(2026-10-01, Phase 3)* | 4/4 | not yet run | covered (win rate, gross margin, average markup, §1.12) |
| metrics_lines *(2026-10-01, Phase 4)* | 2/2 | not yet run | covered (a material's quantity, a role's hours, §8.4) |
| task_counts *(2026-10-01, Phase 4)* | 2/2 | not yet run | covered (by person and by property, §7.4.1); catalog figures are a router pre-handler's — the corpus covers them (§4.12, §5.11) |

**Totals: Tier 1 192/206 · Tier 2 173/182 + 24 not yet run** *(Tier 1 2026-10-01 — the seven metrics categories added 24 cases, 21 passing and 3 known rule-tier gaps; Tier 2 last live run 2026-09-24, the other rows are the 2026-07-29 counts, unchanged)*.

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

## 12.4 Live run 2026-10-19

`tests/test_planner_parity_live.py` (`-m llm_e2e`), after the review in
[`plans/2026-10-19-maple-phrasing-gaps-plan.md`](plans/2026-10-19-maple-phrasing-gaps-plan.md);
compared with the run of 2026-10-14 (corpora) and 2026-10-12 (conversations).

| Source | Cases | Agree | Differ | Blockers | Refusals ok | Refusals missed |
|---|---|---|---|---|---|---|
| routing | 3549 | 2330 | 682 | 0 | — | 0 |
| expected | 107 | 81 | 25 | 0 | — | 0 |
| crud | 206 | 178 | 10 | 0 | 18 | 0 |
| reference | 1476 | 1339 | 48 | 4 | 75 | 2 |
| conversations (turns) | 648 | 586 / 590 on a re-run | 60 / 56 | — | — | — |

- **Blockers and missed refusals:** two are rows that need a file (G20);
  `delete Driveway Maintenance` is explained (a code guard turns the refusal
  into the delete); `what's my average labour rate?` is G25; `delete the PDF on
  the fence task` is G29; `add a template` was missed on 2026-10-14 too —
  asked for a name instead of refused (G30).
- **Rows that drift run to run** (G30) — right one or two times in three
  re-plans: `add a work item to {EST}` [est] and `add mulch to the front patio
  work item` [wi] / `add a Landscaper to the estimate` [est] (ask instead), `show
  me the task from 3 days ago` (a list), `how much does Black Mulch cost?` (a
  list), `what roles are available?` (help), `what are the estimate divisions?`
  (the divisions redirect), `don't drop the markup on work item 2` [wi] (once an
  estimate edit — `said.told_not_to` sets the turn right). `update {task}'s
  description` asks for the text, the field-then-value question the row means.
- **Conversations:** most new differences are the `ref-*` conversations added
  since 2026-10-12, where the planner is right and today's pipeline isn't.
  G31 and G32 repeat in both runs. `Clear Coat` and `Remove Sod` read as
  requests because the run feeds the planner today's state — today's pipeline
  never asked the question the planner would have — so a conversation where the
  two part ways on turn 1 tests nothing after it (G33). Two planner calls failed
  on a dropped TLS connection; the four `RuntimeError` turns were in the 10-12 run
  too.

**After the gap plan (2026-10-20)** — the reference source again
(`PARITY_SOURCES=reference`), with the 29 file rows on their files: 1,511 cases,
1,392 agree, 30 differ, **0 blockers** (4 before), 4 missed refusals — each read:
`attach this to Black Mulch` and `add a template` are set right before anything
runs (`explained.py`), `make a copy of {material}` is now `copy_material` (its own
row), and `remove Ana Reyes from 14 Birch Rd` refused 2 of 3 re-plans (G30's
drift). 36 rows came right; of the 15 that went the other way, re-planned three
times, two were the gap plan's own prompt lines — "what's the price of Topsoil?"
and "Ana Reyes's properties" — narrowed the same day (3/3 and 2/3 since); the
rest drift as before (`pipeline by status` and `what are the material units?`
missed on 2026-10-14 too). The routing, expected and CRUD sources and the
parity run's conversations are owed, on Simon's word (the acceptance run is below).

**The new rows alone (2026-10-20)** — the 78 rows the gap plan added or moved
onto file states, three plans each (95 cases): 262 of 285 right at first. Read
row by row:
- **Fixed.** "add this photo to work item 2" was planned as the work item's note,
  written as "Add this photo." without the photo or left blank (which would ask
  for its text). `as_asked_files.work_item_files_refused` now gives the work-item
  refusal, and an edit with words of its own says the file isn't on it.
- **Fixed, the gap plan's own prompt lines.** The several-materials line quoted
  its "one at a time" question, and the model asked it of "make a task for each
  item on this list" too (3/3). The line now says to plan one create per material,
  and the policy refuses (15/15 re-plans). The material-source line had pulled
  "do I have Black Mulch?" to `get_material` (now `list_materials`, 3/3).
- **Rows reworded to the plan they mean.** `parent.domain=work_item` and
  `parent.domain=task` on two note rows, so a task's note planned as
  `update_task {notes_append}` (the same write) agrees. `create_task` on the
  read-then-create row. `create_material` on the invoice row. "clone this
  material" moved from the Duplicate refusal row to its own `copy_material` row
  ([material_focus]), since D2.
- **Explained** (`explained.py`). "T0042" and "Elm House" with a photo are set
  right by `named_with_files`. "the one at Elm House" answers a question, so it
  is never planned alone (the run can't build the open question).

The re-run after these changes: 272 of 288 right, 0 blockers. Of the 16 left,
11 are explained. 3 are the clone phrasing before its row moved; with a material
in focus it plans `copy_material` 2 of 2. The other 2 are drift: "what's in the
PDF on Elm House's note?" planned `describe_files` once in three, and the model
wrote an empty note body twice for one plan, failing validation after the
retry, so that turn fell back.

**Acceptance run, 2026-10-20** (`test_planner_acceptance_live.py`, every
conversation on the planner's own state): 294 of 312 passed, and 627 of 632
turns were answered by the planner. The 5 handed back are by design ("never
mind", "hi maple", a yes to a question the old pipeline asked).
- **G32 is closed**: `task-status-answered-by-a-request-shaped-status` passes.
- **30 gaps of the old pipeline** pass on the planner.
- **17 failures** are explained, each one explained before this branch.
- **1 failure counted**: `metrics-best-customers-then-last-year` once asked what
  "best customers" means. Alone it passed 3 of 3, and "who are my
  best/top/biggest customers?" planned the ranking 15 of 15: drift.

The corpus had no conversation for the gap plan's multi-turn flows, so four were
added (`corpus.GAP_PLAN_2026_10_19`): undo after a yes, undo declined, a stray yes
after a declined delete, and hide asked first. All four passed in each of three
runs (12 of 12). The copy offer (D2) needs a standard material the world doesn't
seed; its unit tests pin it.

**Live runs, 2026-10-22** — after the review rounds and the sync with main. The
full parity run (all four sources) had 0 blockers:

| Source | Cases | Agree | Differ | Blockers | Refusals missed |
|---|---|---|---|---|---|
| routing | 3549 | 2366 | 645 | 0 | 0 |
| expected | 107 | 84 | 22 | 0 | 0 |
| crud | 206 | 178 | 9 | 0 | 0 |
| reference | 1517 | 1397 | 34 | 0 | 2 |

Both missed refusals were already explained ("attach this to Black Mulch", "add a
template"). The reference rows that newly differed were checked: the systematic
ones are set right before the policy runs (a total over an amount is the list's,
"my margin" the company's, the cedar fence asks which estimate). Parity scores
the model's plan before those corrections.

The acceptance run had 291 of 316 passing, with 8 counting. Each was rerun three
times. Three failed every time and were fixed:
- "due Thursday", said on a Thursday, was set to today. The prompt now says a due
  date set by a day's name alone is the first such day after today.
- "what's the total value of my Maintenance estimates for Bob Lee before tax?"
  after a recurring-work figure was planned as that figure again. A lone
  `redo_last` whose message is a whole figure question is now asked for once more.
- "add a labour role" got the planner's own name question. A name question for a
  create with nothing else said is now asked for once more, so the role create
  asks in its usual words.

One wrong copy of an email ("jordan.6d3f65c0@…" planned without "jordan.") is set
back to the email the message says (`said_tasks._email_said`). Three
conversations were added to `explained.py`: two where the model carries "Bob Lee"
onto a count and Maple asks rather than widen it, and the excavation activity
looked for on the wrong work item (follow-up #1434).

The first weekday wording ("'due Thursday' said on a Thursday is a week away")
made the model push "Friday" a week out too. The line now gives both cases.
After it, the fixed conversations passed 15 of 15, and the weekday ones three
reruns with none counting.

The reference rows rerun on the final prompt: 1404 agree, 27 differ, 0 blockers,
1 missed refusal (explained). The 5 newly differing rows are reads or questions
asked before anything runs.

## 12.5 Related docs

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
