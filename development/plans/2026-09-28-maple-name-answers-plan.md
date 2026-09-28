# Maple: a name answers the question that asked for it

**Date:** 2026-09-28 · **Status:** proposed · **Builds on:**
[`2026-09-27-maple-multi-turn-everywhere-design.md`](2026-09-27-maple-multi-turn-everywhere-design.md)
(one question gate, `routers/agent_helpers/open_question.py`)

## 1. The idea

When Maple has just asked for the name of something the company has ("Which
material do you mean?", "Which category does River Rock go in?", "Which
estimate?"), the next message is most likely that name. The reply is checked
against the company's real names first. A reply that *is* one of them is the
answer, however it reads: "Clear Stone", "Set Up", "Remove Sod", "New
Construction". Only a reply that names nothing the company has goes through
the "does this look like a new request?" checks.

The first case shipped on 2026-09-28 (review round 5 #1):

- `routers/agent_helpers/named_answers.py`: `NAME_SOURCES` maps the field
  a value question waits for to a loader of the company's names.
  `known_names_for_open_questions` runs once per turn in the router, and only
  while such a question is open.
- `decide_turn(..., known_names=...)`: an exact whole-reply match answers
  before any command check.
- `agents/conversation/replies.py`: `name_in_reply` / `name_key` strip "no,",
  "the", "now", "please" … the same way in the gate and in the agent.

## 2. What the survey found

About 25 questions ask for an existing name. Only "Which material do you
mean?" matches names today; numbered menus already match through
`menu_pick` / `_pick_candidate`. Two problems stand in the way everywhere else.

1. **Names that read as commands are treated as new requests.** In the gate,
   a capitalised verb-led reply ("New Construction", "Remove Sod", "Add Ons",
   "Update Crew") passes `is_unambiguous_command` and becomes a new message.
   In the material create flow, `create_questions.bare_answer` also rejects
   any reply that opens with a command verb, so "Clear Coat" and "Set Up" are
   refused as a category even when the gate answers (checked).
2. **Many questions store no pending record.** Nothing marks them as open, so
   the reply can never be an answer: it is classified from scratch, and the
   original request is lost. Name matching cannot help until they do.

| Question | Where | Names | Today |
|---|---|---|---|
| "Which estimate? … or its title." | `estimate/crud_handlers.py:2642` (and :2494) | `Estimate.title` | Record stored with no candidates: only a code answers; **every title is dropped** (checked) |
| "Which category does X go in?" / "What unit is X sold by?" | `conversation/create_questions.py:32-33` | `MaterialCategory` / `MaterialUnit` | Record ✓; verb-led names refused by the gate and by `bare_answer` |
| "What's the new category / unit?" (update) | `material/service.py` field flow | same | Record ✓; verb-led names refused by the gate |
| "Which status should I set it to?" | `task/field_flow.py:37` | `TaskStatus.name` (custom per company) | Record ✓; "New Request"-style statuses refused |
| "Who should I assign it to?" | `task/field_flow.py:38` | `User` names / email | Record ✓; mostly safe |
| "Which contact should I link to this property?" | `property/service.py:1769` | `Contact` full name | Flow record, no awaited field |
| "Okay — which {noun} did you mean?" (after "no" to "Just to check…") | `routers/agents.py:887` | any record kind | **No record**: the original request is lost |
| "Which task did you mean? Tell me its name or ID." / "Which task should I update? Tell me its name or ID." | `task/confirmation.py:244`, `resolver.py:195`, `field_flow.py:240` | `Task.title` | **No record**; at `field_flow.py:240` the task name is stored as the field value (#713) |
| "I don't recognize 'X' as one of your task statuses… Which one?" | `task/operations.py:~226` | `TaskStatus.name` | **No record** |
| Teammate ambiguity / "Who should I assign the task to?" | `task/operations.py:291, 340` | `User` | **No record** |
| "Multiple … matched. Please specify the exact …" | material :759, equipment :406, labour :477, property :960, contact via property :1855/:1875 | the record kind | **No record** (material/equipment updates only have a flow record) |
| "Which template would you like to see / delete?" | `template/service.py:300, 459` | `Template.name` | **No record** |
| Estimate list filters: "Which property / role / material / contact did you mean?" | `estimate/crud_handlers.py:1202-1354` | Property, Labour, Material, Contact | **No record** |
| "Which property should I link / did you mean?" | `estimate/crud_handlers.py:~3578-3628` | `Property` | **No record** (only the fuzzy path arms `property_link`) |
| "Which material should I use / replace?" | `estimate/assumption_handlers.py:350, 363, 488` | `Material.name` | **No record** |
| "What's the activity / role / material called?" (new names) | `work_item_context.py:443`, create flows | a *new* name | Not a lookup: verb-led names ("Remove Sod", "Load Truck") are refused as commands |

Already safe: the router flows `property_link`, `optional_follow_up` and
`estimate_follow_up` exempt their own domain; numbered menus; "which size?".

## 3. Design

1. **Key sources by owner and field.** `NAME_SOURCES[(agent, field)]`:
   "status" means a `TaskStatus` for the Task agent but an enum for estimates,
   and "category" is a material category only for the Material agent.
2. **Look up the reply, don't load the catalog.** Contacts, users and
   estimates can run to thousands. Replace "load every name" with one indexed
   query per open name question: company plus a case-insensitive exact match
   on the name (or on first + last for people), for that one reply. The
   router passes `{(owner, field): {name_key(reply)}}` when it matches, so the
   gate stays synchronous and database-free.
3. **The agent accepts what the gate accepted.** Every agent-side reader of
   an answered name question (`bare_answer`, `_take_awaited_create_answer`,
   the field flows) skips its own "looks like a command" rejection when the
   reply is a known name. Otherwise the gate says ANSWER and the agent says
   no, which is today's category bug.
4. **Every name question stores a record.** One helper,
   `ask_for_name(context, agent, intent, field, original_message, question)`,
   writes `{agent, intent, awaiting_value_for: field, original_message}`.
   The answer re-runs `original_message` with the name filled in, the way the
   size command already does (`_resume_size_command`). Dead-end questions
   switch to it, and the record lives one turn as every question does.
5. **New-name questions are free text.** "What's the activity / role /
   material called?" asks for a name that doesn't exist yet, so there is
   nothing to look up. Add those fields to `_FREE_TEXT_VALUE_FIELDS` (only a
   cancel backs out), and let `bare_answer` stop rejecting verb-led names for
   them.

## 4. Phases

Each phase is a separate commit and follows the same checklist: a gate
unit test (a verb-led name answers; a request naming it is still a request),
one corpus row whose `setup=` seeds a verb-led name, a clean routing
snapshot, and the phrasing reference updated. They are ordered by how
likely users are to hit them.

**Phase 1: estimate titles.** "Which estimate? … or its title." invites a
title and drops every one. Source `Estimate.title` (company-scoped,
non-archived first). When a `choose_estimate` record has no candidates,
`decide()` accepts a reply that matches a title. The corpus row asks
"add a note to the estimate", then answers "Front Yard Refresh". *Small.*

**Phase 2: material category and unit** (create and update). Sources
`MaterialCategory.name` / `MaterialUnit.name`; the `bare_answer` and
`_take_awaited_create_answer` bypass for known names (§3.3). The rows are a
create that answers "Clear Coat" as the category, and an update of a unit to
"Set" (seeded). *Small.*

**Phase 3: task status and teammates.** First add a `company` index to `User`
(#715). Sources `TaskStatus.name` and `User`
(email, first, last, full name). The status re-ask
(`task/operations.py:~226`) and the teammate-ambiguity asks get records
(§3.4). Rows: a custom status "New Request" set by name; "Mark Lee" as the
assignee. *Medium.*

**Phase 4: "Okay — which {noun} did you mean?"** After a "no" to the anchor
check, store a record carrying the original request. The named record then
gets the original edit, asking first if the name matches several.
Row: "change her phone to …" → "Just to check — do you mean Ana?" → "no" →
"Bob Lee" → Bob's phone changes. *Medium.*

**Phase 5: "Which task did you mean?"** Records at all three call sites;
fixes the field-flow bug where the task name becomes the value (#713). *Medium.*

**Phase 6: multi-match "please specify"** for material, equipment, labour,
property, contact (through property) and template. One record per ask via
`ask_for_name`, with the name sources for each kind. *Medium; mostly
mechanical once §3.4 exists.*

**Phase 7: estimate-side lookups**: list filters, property linking,
assumption materials. *Medium.*

**Phase 8: new-name questions** (§3.5). *Small.*

## 5. Decisions needed

1. **Exact match only?** Recommended: yes, whole reply after tidying,
   case-insensitive. A partial ("mulch") still answers through the agent's own
   lookup, as it does today; a fuzzy match at the gate would let a request
   that mentions a name become an answer.
2. **Should dead-end questions become real questions (phases 4–7)?** This
   changes behavior: today the next message starts fresh; afterwards a bare
   name finishes the original request. Recommended: yes. It is what the
   question already promises.
3. **Several records with the same name** (two contacts called "Mark Lee").
   Recommended: the gate still answers, and the agent asks with its numbered
   menu, as for any ambiguous name.

## 6. Risks

- **A real request that is exactly a record's name** ("Invoices", if a
  template is called that) is taken as the answer. Only while the question is
  open, and only for one turn. Accepted: it is what the user just named.
- **Query cost:** one indexed lookup per turn while a name question is open,
  and none otherwise. `company` is indexed on the catalog models, but not on
  `User`, which indexes only `email` (`models/user.py:89`, #715): add that
  index first in phase 3, and `(company, name)` wherever a phase needs it.
- **Tracked follow-ups this closes or touches:** #713 (which-one questions
  store no record), #700/#701 (size commands), #776 (the material loader's
  silent 5000-name cap, which §3.2 replaces). #766 ("Black Mulch?" as the
  reply) is already resolved: a known name ending in "?" answers since
  2026-09-28, and an unknown "X?" is still a new request.
