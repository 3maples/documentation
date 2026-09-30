# Maple: a name answers the question that asked for it

**Date:** 2026-09-28 · **Revised:** 2026-09-29 (re-checked against `fae429e`;
material-management questions and multi-match "please specify" deferred, §7)
· **Status:** in progress — phases 0–1 done; next phase 3 · **Builds on:**
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

Line numbers as of `fae429e` (2026-09-29). Rows marked *(deferred)* are out
of scope for now (§7).

| Question | Where | Names | Today |
|---|---|---|---|
| "Which estimate? … or its title." | `estimate/crud_handlers.py:2669` (`_stash_estimate_choice` with no `matches`); also :1127, :2737, :2771 | `Estimate.title` | Record stored with no candidates: the gate (`open_question.decide`, :118) and the agent's resume (`work_item_context.py:~540`) both accept only a code, so **every title is dropped** (checked) |
| *(deferred)* "Which category does X go in?" / "What unit is X sold by?" | `conversation/create_questions.py:32-33` | `MaterialCategory` / `MaterialUnit` | Record ✓; verb-led names refused by the gate and by `bare_answer` (:82) |
| *(deferred)* "What's the new category / unit?" (update) | `material/service.py` field flow | same | Record ✓; verb-led names refused by the gate |
| "Which status should I set it to?" | `task/field_flow.py:37` | `TaskStatus.name` (custom per company) | Record ✓; "New Request"-style statuses refused |
| "I don't recognize 'X' as one of your task statuses… Which one?" | `task/operations.py:228` | `TaskStatus.name` | Record ✓ since 2026-09-28 (`_remember_update_question`, `3f343fa`/`1482315`); verb-led statuses refused |
| "Who should I assign it to?" | `task/field_flow.py:38` | `User` names / email | Record ✓; mostly safe |
| "Which contact should I link to this property?" | `property/service.py:1769` | `Contact` full name | Flow record, no awaited field |
| "Okay — which {noun} did you mean?" (after "no" to "Just to check…") | `routers/agents.py:887` | any record kind | **No record**: the original request is lost |
| "Which task did you mean? Tell me its name or ID." / "Which task should I update? Tell me its name or ID." | `task/confirmation.py:244`, `resolver.py:195`, `field_flow.py:169` | `Task.title` | **No record** (`_clarify`); at `field_flow.py:169` the `update_task` record awaiting a value stays open, so the task name is read as the field value (#713) |
| Teammate ambiguity / "Who should I assign the task to?" | `task/operations.py:~290, ~345` | `User` | **No record** |
| *(deferred)* "Multiple … matched. Please specify the exact …" | material :759, equipment :406, labour :477, property :960, contact via property :1875 | the record kind | **No record** (material/equipment updates only have a flow record) |
| *(deferred)* "Which template would you like to see / delete?" | `template/service.py:300, 459` | `Template.name` | **No record** |
| Estimate list filters: "Which property / role / material / contact did you mean?" | `estimate/crud_handlers.py:1237-1389` | Property, Labour, Material, Contact | **No record** |
| "Which property should I link / did you mean?" | `estimate/crud_handlers.py:~3605-3735` | `Property` | **No record** (only the fuzzy path arms `property_link`) |
| "Which material should I use / replace?" | `estimate/assumption_handlers.py:350, 363, 488` | `Material.name` | **No record** |
| "What's the activity / role called?" (new names; the material one is *deferred*) | `crud_handlers.py:3067` (`awaiting_value_for: "activity"`), create flows | a *new* name | Not a lookup. `"activity"` is in neither free-text list, so the gate doesn't see the question as open; verb-led names ("Remove Sod", "Load Truck") are at risk of being read as commands |

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
   the field flows, the `choose_estimate` resume) skips its own "looks like a
   command" rejection when the reply is a known name. Otherwise the gate says
   ANSWER and the agent says no, which is today's category bug.
4. **Every name question stores a record — and something reads it.** Which
   mechanism depends on who answers the question:
   - **Agent-owned "which record?" questions** (phases 4 and 5) use one new
     helper, `ask_for_name(context, agent, intent, domain, original_message,
     question)`. It writes a `pending_intents` record
     `{agent, intent, op: "name_answer", domain, awaiting_value_for: domain,
     original_message}`, so `open_questions` sees a `_VALUE` question. The
     router reads the answer in a branch beside `_answer_anchor_check`, and
     replays the same way: it looks the reply up in `domain`, and with
     exactly one match sets `active_<domain>_id`, calls `stamp_anchor` and
     re-runs `original_message` through the owner (`delegate_generic`).
     Several matches → a numbered menu stored as `choices`, answered through
     the existing `menu_pick` path. No exact match (a partial such as
     "mulch") → the domain's own finder, with the same one / several
     outcomes; still nothing → "I couldn't find X. Which {noun} did you
     mean?", asked once more.
   - **Task value questions** (phase 3) already have records
     (`_remember_update_question`); they carry the value to
     `_handle_task_assign` / `_handle_task_status_change`, so they need name
     sources, not `ask_for_name`.
   - **Estimate questions** (phases 1 and 7) are answered by the Estimate
     agent: the router hands it the reply, and its own resume
     (`work_item_context.py`) reads the record. They extend
     `_stash_estimate_pending` with new ops, and each op must be registered
     in `open_question._estimate_question_for` / `current_question`, or the
     gate never sees the question.
   Every record lives one turn, as every question does.
5. **New-name questions are free text.** "What's the activity / role /
   material called?" asks for a name that doesn't exist yet, so there is
   nothing to look up. Mark those fields free text so only a cancel backs out:
   agent questions in `_FREE_TEXT_VALUE_FIELDS`, and estimate questions
   (`"activity"`) in `_FREE_TEXT_FIELDS` — whose `decide()` branch still
   runs `is_command`, so it must skip that check for new-name fields. Let
   `bare_answer` stop rejecting verb-led names for them.

## 4. Phases

Each phase is a separate commit and follows the same checklist:

- failing tests first (TDD): a gate unit test in `tests/test_open_question.py`
  (a verb-led name answers; a request naming it is still a request) and the
  agent-side test for the resume;
- one row in `tests/maple_conversations/corpus.py` whose `setup=` seeds a
  verb-led name;
- a clean `tests/test_maple_routing_snapshot.py` (re-record with
  `UPDATE_MAPLE_SNAPSHOT=1` only after reviewing the diff);
- `./run_mypy.sh` and `./run_ruff.sh` scoped to the touched subtrees;
- the phrasing reference updated (rows, "Recent changes", "Last updated");
- the §8.1 follow-ups the phase fixes marked RESOLVED in
  `code-review-followups.md` in the same commit.

They are ordered by how likely users are to hit them, after the groundwork
in phase 0. **Phases 2 and 6 are deferred (§7)**; their numbers are kept so
references to the other phases stay valid.

**Dependencies:** 0 before everything (the `(owner, field)` keys and the
lookup). 1 before 7 (`decide()` takes `known_names`). 4 before 5
(`ask_for_name` and its router branch). #722/#723 before 7. 3 and 8 need only
phase 0.

**Phase 0: lookup, not load** (§3.1, §3.2). ✅ *Done 2026-09-29.* Re-key `NAME_SOURCES` by
`(owner, field)` and replace the material loader with a per-reply lookup:
one `find_one({"company": …, "name": <anchored, escaped,
case-insensitive regex>}, {"_id": 0, "name": 1})` per open name question, trying the
reply as typed and then `name_in_reply(message)` (#775). With that projection the
query is covered by the `(company, name)` index: the regex scans the
company's index keys and reads no documents. `NAME_VALUE_FIELDS` and its tie-in test follow the
new key. The existing `test_named_answers.py` cases are the check that
nothing else changes. Closes #776, #775. *Small.*
Follow-ups (§8.1): #776, #775 (the reply cleaner also cuts real names —
"No. 57 Stone", "The Good Stuff" — so the gate answers but the agent looks
up the cut name and dead-ends; the lookup should try the whole reply first);
#709 (`catalog_names._catalog`) is the same load-everything pattern and can
reuse the lookup, but is optional here.

**Phase 1: estimate titles.** ✅ *Done 2026-09-29* — also remembers "Which estimate?" at the six sites that stored nothing (reads, the router's update, assumptions); a delete is listed but never remembered. "Which estimate? … or its title." invites a
title and drops every one. Source `Estimate.title` (company-scoped,
non-archived first), keyed `(ESTIMATE_AGENT_LABEL, "estimate")`. `estimates`
has no `(company, title)` index — add one (the existing indexes are all
company-prefixed, but a title regex would still fetch every document). Three
places change:

- `known_names_for_open_questions` also looks up a `choose_estimate` record,
  which is a `pick` question, not a `_VALUE` one;
- `open_question.decide()` takes `known_names` (today only `_decide_any`
  does) and answers a candidate-less `choose_estimate` whose reply matches a
  title;
- the agent's resume (`work_item_context.py:~540`) resolves the title to its
  code and sets `FORCED_ESTIMATE_CODE_KEY`, asking with the numbered menu
  when several estimates share it (§5.3).

The corpus row asks "add a note to the estimate", then answers "Front Yard
Refresh". *Small–medium.*
Follow-ups (§8.1): don't build the title lookup on `_match_estimates_by_title`
or `resolve_named_estimates` — both load every estimate (#669); use the
phase-0 indexed lookup. Fix together: #615 (several live estimates share
the title → the generic prompt, with no candidates listed) and #616 (the get path's
loose substring match isn't gated on a named title), which are one resolver
gap from two sides; #22 (no "you don't have any estimates yet" branch
before "Which estimate?"); #346 (`names_target` resolves the title twice).

**Phase 2: material category and unit.** *Deferred — see §7.*

**Phase 3: task status and teammates.** First add a `company` index to `User`
(#715). Sources `TaskStatus.name` and `User`
(email, first, last, full name). Both status questions already store records;
the teammate-ambiguity and "Who should I assign the task to?" asks get
one through `_remember_update_question(field="assigned_to_email")`. For the
ambiguity ask, extend that helper to also store the teammates offered as
`choices` (it takes none today), so "2" or "Mark Lee" answers it through
`menu_pick` (§3.4). `task_statuses` already has a unique
`(company, name)` index. Rows: a custom status "New Request" set by name, both from
"Which status?" and from the "I don't recognize…" re-ask; "Mark Lee" as the
assignee. *Small–medium.*
Follow-ups (§8.1): #715 (the index), #714 (`_teammate_email` swallows
database errors and loads every user — the indexed lookup replaces it),
#751 (the assignee reply isn't tidied, so "Jordan." never matches — use
`name_in_reply`), #752 (the property-or-person path replaces the teammate
ambiguity question with "I couldn't find…"), #711 (a status column named like
a date — "Next Week", "Today" — is read as a due date: "move it to Next
Week" sets the due date instead of moving the card). Adjacent, not required: #750, #777, #717.

**Phase 4: "Okay — which {noun} did you mean?"** Introduces `ask_for_name`
and its router branch (§3.4); document both in CLAUDE.md's "Multi-turn,
every feature" section. After a "no" to the anchor check, store a record
carrying the original request. The named record then gets the original
edit, asking first if the name matches several. Name sources: contacts
(first + last) and properties (name, street), with `(company, …)` indexes
for the fields looked up — `contacts` indexes only `company` and
`properties` only `(company, updated_at)`. Materials already have one
(phase 0). Roles and templates get no source here, because their sources
belonged to deferred phase 6. So an ordinary role or template name still
answers through the shape checks, but a verb-led one ("Remove Sod") stays
a gap.
Row: "change her phone to …" → "Just to check — do you mean Ana?" → "no" →
"Bob Lee" → Bob's phone changes. *Medium.*
Follow-ups (§8.1): #759 — corpus row `contact-stale-anchor-asks` passes
without checking for "Just to check"; tighten it here, since this phase's
row starts from the same question.

**Phase 5: "Which task did you mean?"** `ask_for_name(domain="task")` at
all three call sites, with a `Task.title` source (add `(company, title)`;
the resolver already queries `title` by regex). At `field_flow.py:169`
the value was already given, so the ask replaces the open value record with
one that keeps `awaiting_value_for` and the value; once the task is named,
the field flow applies the value instead of reading the task name as the
value (#713). Widened
2026-09-29: the Task agent's own "Which property did you mean?" /
"More than one property matches…" asks (`task/operations.py:~457, ~466`,
`task/service.py`) go through the same `_clarify` and store nothing either
(#713); give them records here, since no other phase reaches them. *Medium.*

**Phase 6: multi-match "please specify".** *Deferred — see §7.*

**Phase 7: estimate-side lookups**: list filters, property linking,
assumption materials. These are Estimate-agent questions (§3.4): new
`_stash_estimate_pending` ops, registered in `_estimate_question_for`. A
list-filter answer re-runs the original request with the unmatched name
replaced by the one given ("estimates using mulch" → "Black Mulch" →
"estimates using Black Mulch"). *Medium.*
Follow-ups (§8.1): fix #722 and #723 **first** — "show me estimates with
the highest total" and "which estimates have been sent?" are misread as
material filters and
end in "Which material or role did you mean?"; once that question stores a
record, the user's next message would be taken as its answer. Also #322
(a property with a blank street matches any reply in the post-create
link follow-up, so the estimate can be linked to it silently) and #439 (the property-link flow exempts every property message, so
"create a new property at 42 Elm St" doesn't back out). Adjacent: #159
(the list-filter finders load whole collections), #779.

**Phase 8: new-name questions** (§3.5) — the estimate activity and the role
create; the material create's "What's the material called?" is deferred
(§7). Start by pinning today's behaviour for "Remove Sod" as an activity
name, since the gate does not see that question as open. *Small.*
Follow-ups (§8.1): #470 — "What should the task be called?" names a field
the portal no longer shows; reword it ("What should the task say?") and
read the bare reply as free text into the description, like the other
new-name questions.

## 5. Decisions (settled 2026-09-29)

1. **Exact match only.** The whole reply, after tidying, case-insensitive. A
   partial ("mulch") still answers through the agent's own lookup, as it does
   today; a fuzzy match at the gate would let a request that mentions a name
   become an answer.
2. **Dead-end questions become real questions (phases 4, 5 and 7).** This
   changes behaviour: today the next message starts fresh; afterwards a bare
   name finishes the original request, which is what the question already
   promises.
3. **Several records with the same name** (two contacts called "Mark Lee"):
   the gate still answers, and Maple asks with a numbered menu, as for any
   ambiguous name.

## 6. Risks

- **A real request that is exactly a record's name** ("Invoices", if a
  template is called that) is taken as the answer. Only while the question is
  open, and only for one turn. Accepted: it is what the user just named.
- **Query cost:** one indexed lookup per turn while a name question is open,
  and none otherwise. `company` is indexed on the catalog models, but not on
  `User`, which indexes only `email` (`models/user.py:89`, #715): add that
  index first in phase 3, and `(company, name)` wherever a phase needs it.
- **Tracked follow-ups:** §8.1 lists every one each phase closes. #700/#701
  (size commands) are not touched and stay in the backlog. #766 ("Black
  Mulch?" as the reply) is already resolved: a known name ending in "?"
  answers since 2026-09-28, and an unknown "X?" is still a new request.

## 7. Deferred (2026-09-29)

Material-catalog management and the multi-match "please specify" questions
are out of scope for now. Each case below is logged as a ⚠️ gap in
[`maple-phrasing-reference.md`](../maple-phrasing-reference.md) (§2.9, §3.8,
§4.9, §4.11, §5.9, §6.8) so it stays visible until it is picked up.

- **Phase 2 — material category and unit** (create and update). Would add
  `MaterialCategory.name` / `MaterialUnit.name` sources and the `bare_answer`
  / `_take_awaited_create_answer` bypass for known names (§3.3). Unsupported
  today: "Clear Coat" in answer to "Which category does River Rock go in?",
  "Set" in answer to "What unit is Paver Base sold by?" or to a unit update.
- **Material create's new name** (the material part of phase 8): a verb-led
  name ("Clear Stone") in answer to "What's the material called?".
- **Phase 6 — multi-match "please specify"** for material, labour, property,
  contact (through property) and template, including "Which template would
  you like to see / delete?". Would give each ask a record via
  `ask_for_name` (§3.4) and a name source per kind. Unsupported today: the
  bare name in reply is classified from scratch and the original request is
  lost. (Equipment is refused outright, §9.2 of the phrasing reference, so it
  needs nothing here.)

Not deferred, although they involve materials: the existing "Which material
do you mean?" lookup (re-keyed in phase 0) and the estimate-side "Which
material should I use / replace?" (phase 7), which pick a catalog material
for an estimate rather than manage the catalog.

When picking these up, the phase checklist in §4 applies unchanged.

Not deferred with them: **#702** (hex category/unit ids are taken without a
company check, and `_with_catalog_names` reads them unscoped). It sits in the
material code but is a tenant-isolation fix, not a feature, so it stays in
the backlog (§8.3) to be done on its own.

## 8. Maple follow-ups (reviewed 2026-09-29)

Every open entry in
[`code-review-followups.md`](../code-review-followups.md) that touches Maple
— its agents, `routers/agents.py`, `routers/agent_helpers/`, translation, the
Maple panel and the public widget — was re-checked against the code at
platform `fae429e` (143 entries). The numbers are the follow-up numbers; the
entries themselves stay in that file.

### 8.1 Taken up by a phase

| Phase | Entries | Verified |
|---|---|---|
| 0 | #776, #775; #709 optional | #776, #775 resolved 2026-09-29; #709 left in the backlog |
| 1 | #669, #615, #616, #22, #346 | #615, #616, #22 resolved 2026-09-29; #669 avoided, not fixed (no new full load); #346 left as is — the pre-check carries a distinction the resolver doesn't return |
| 3 | #715, #714, #751, #752, #711 (adjacent: #750, #777, #717) | all still apply |
| 4 | #759 | still applies |
| 5 | #713 (task questions, and the Task agent's property questions) | still applies |
| 7 | #722, #723 (prerequisites), #322, #439 (adjacent: #159, #779) | all still apply |
| 8 | #470 | still applies |

Close each entry in the follow-ups file in the phase's own commit.

### 8.2 No longer valid

- **#308** — fixed: the work-item question guard is one predicate,
  `_is_work_item_question` (`agents/orchestrator/service.py:286`), used at
  all three call sites (`6cc41e8`).
- **#445** — fixed: `_resolve_update_estimate_code`
  (`agents/estimate/crud_handlers.py:2626`) is the shared resolve-or-ask
  preamble for the title, description and property-link handlers
  (`7213840`).
- **#27** — still open, but its suggested fix is now wrong: the call is not
  a no-op (`_build_extra_parsed_item` stamps the company's markup and
  overhead defaults), so only a clarifying comment or rename is safe.

#308 and #445 are marked RESOLVED in the follow-ups file, and #27 carries the
correction.

Partly fixed or moved entries are noted inline below.

### 8.3 Not in this plan — the rest of the Maple backlog

These are still open and verified, but no phase depends on them. Grouped by
their section in the follow-ups file.

**Query efficiency — scans, N+1 and missing indexes** (7)

- #26 MEDIUM — `find_contacts_by_name` fetches whole company, filters in Python
- #157 MEDIUM — Cross-resource transitive join uses two round-trips instead of $lookup
- #27 LOW — Inefficient merge pattern in bulk work-item endpoint — *partly: the call moved to `estimate_update.py:116` and is not a no-op — `_build_extra_parsed_item` stamps the company's markup/overhead defaults, so the suggested "drop the call" would regress; only a clarifying comment or rename is safe*
- #159 LOW — `agents/cross_resource.py` filters in-Python on full collections
- #448 LOW — platform/agents/template/service.py:161 — full-collection load to resolve one id
- #618 LOW — The estimate is loaded twice per planned edit
- #716 MEDIUM — `due_date` is filtered and sorted with no index, and the docstring says otherwise

**Silently swallowed errors** (6)

- #20 MEDIUM — Narrow `except Exception` around `PydanticObjectId(company_id)` cast in `_resolve_latest_estimate` — *moved to `agents/estimate/crud_helpers.py:318-349`*
- #318 MEDIUM — Broad `except Exception` in template instantiation swallows the real failure
- #430 LOW — platform/agents/** — 11 bare `except Exception: pass` blocks (bandit B110)
- #619 LOW — A failed estimate-edit persist logs nothing about the cause
- #747 LOW — `except Exception: return None` hides errors without logging
- #748 LOW — `except Exception: return None` hides errors without logging

**Duplicated code and twin files** (10)

- #302 MEDIUM — TYPE_CHECKING stub blocks duplicate signatures from sibling mixins — *grown: ~37 stubs in `crud_handlers.py`, ~16 in `work_item_handlers.py`*
- #316 MEDIUM — Company-context resolution duplicated across both template-estimate entry points — *partly: `_envelope` is shared now; the company resolve-or-refuse block is in three places*
- #331 MEDIUM — Twin datetime formatters duplicate the label format
- #189 LOW — `estimate_update.py` could mirror `fuzzy_confirmation._envelope`
- #370 LOW — platform/agents/estimate/crud_handlers.py:1635 — canonical-span constants duplicated across two files
- #744 LOW — `_UNLINK_REDIRECT` duplicates `out_of_chat._UNLINK`
- #750 LOW — Private `_EMAIL_RE` imported across modules, and two email regexes disagree
- #767 LOW — The task command lead is a third lead-word list, drifted from the shared one
- #768 LOW — The size-command `_LEAD` is a fourth lead-word list
- #777 LOW — `_SET_TARGET_STATUS_RE` repeats `_TARGET_FIRST_LEAD` inline

**LLM prompt hygiene and injection surface** (4)

- #15 MEDIUM — Split Example block may anchor LLM back to terse descriptions
- #385 LOW — platform/agents/calculator/service.py:88 + open_math.py:43 — classifier + reasoner prompts still growing — *accepted / watch item*
- #620 LOW — The edit planner's `clarifying_question` is shown to the user verbatim — *partly: the question is shown only when the plan needs clarification or is unclear, but still verbatim*
- #621 LOW — `client_context.current_path` only has a length limit and reaches the classifier prompt unfenced

**Platform — Maple agents** (59)

- #49 MEDIUM — `_ADDRESS_PATTERN` can false-match "N <word>+ way/court"
- #279 MEDIUM — Maple-chat estimate-creation refusal still uses the legacy direct add-card link
- #329 MEDIUM — "Please don't" is consumed as a property value by the one-turn shortcut
- #23 LOW — `_NOTE_WITH_IMPLICIT_TAIL` can false-positive on descriptive phrasings
- #101 LOW — US-address regex could match noisy mid-message text — *moved to `agents/property/text_helpers.py:444`*
- #325 LOW — `sacá …todos` can false-positive the fail-open bulk-delete net
- #354 LOW — platform/agents/orchestrator/service.py:~1858 — status offer made without pre-validating legality/role
- #366 LOW — platform/agents/orchestrator/service.py:2657 — `_classify_specific_phrasings` evaluated twice on the LLM-reconciliation path
- #383 LOW — platform/agents/calculator/text_helpers.py:54 — "how long" is a broad gate trigger — *accepted / watch item*
- #406 LOW — platform/routers/agent_helpers/estimate_gathering.py:238 — gathering-path response never mentions the auto-linked property
- #437 LOW — platform/agents/estimate/crud_handlers.py — fuzzy disclosure dropped on sorted and aggregate list responses — *partly: since `729eede` counts, aggregates, empty and unsorted lists name the property; the sorted replies ("Your highest estimate:") still don't*
- #442 LOW — agents/task/resolver.py:94 — `-updated_at` recency sort has no tiebreaker
- #447 LOW — platform/agents/task/text_helpers.py:117 — "add to the tasks: X" with no active task appends to an unrelated task — *accepted / watch item*
- #565 MEDIUM — The reuse removal's cost to estimate generation is unmeasured — *accepted / watch item*
- #569 LOW — `or target.company` fallback can file a Maple note under another tenant
- #581 LOW — `_detect_note_update` keeps a dead `mode` with a false rationale
- #614 LOW — `run_confirmed_edits` acts on the stashed code, not the verified target
- #617 LOW — `intent` and `existing_estimate_id` aren't treated as per-turn keys
- #645 LOW — The planner rejects references to a work item added in the same plan
- #659 LOW — Setting a work item back to its original total doesn't reset the adjustment the way the portal does
- #699 MEDIUM — The display-text save for non-English turns can erase another turn's chat lines
- #700 MEDIUM — Removing or renaming a size the material doesn't have replies "I've updated the material"
- #701 MEDIUM — The size-command branch skips `process()`'s error handling
- #702 MEDIUM — A category id typed into the message skips the company check, and the details lookup reads it unscoped
- #703 MEDIUM — "show me his contact info" / "delete it" look up a contact named by the pronoun
- #704 MEDIUM — "it/this/that" anywhere in a message picks the focused template over one the user named
- #705 MEDIUM — "delete my note" offers an Owner someone else's note and calls it "your note"
- #706 MEDIUM — Requests starting with no / don't / keep it / wait are answered "I'm not waiting on an answer"
- #707 MEDIUM — `_BARE_GET_RE` runs before the 80-character guard
- #708 MEDIUM — `rewrite_focus_question` has no length cap
- #710 MEDIUM — A due-date question becomes a write
- #712 MEDIUM — "for X" at the end of a create silently links a property
- #717 MEDIUM — "assigned to <name>" swallows the next word
- #718 MEDIUM — Due questions without a parseable date list every task
- #719 MEDIUM — With an estimate in focus, help and catalog questions get that estimate's figures
- #720 MEDIUM — "which estimate has the highest total?" now asks "Which estimate would you like to view?"
- #721 MEDIUM — The pipeline/backlog analytics patterns catch estimate writes and value replies
- #724 MEDIUM — "show me recent draft estimates" is cut to one row
- #725 MEDIUM — An estimate code before "work item" is taken as the work item's name
- #726 MEDIUM — `pronoun_domain` reads the dictated note body
- #737 LOW — A turn's chat lines are lost on merge when its last line repeats the previous last line
- #738 LOW — A turn that overlaps Clear brings the cleared conversation back
- #740 LOW — After a task list, any "what is/are …" question becomes a task filter
- #741 LOW — "and her email is …" is swallowed by the "what about X?" rewrite
- #742 LOW — "Please note: …" is filed as a note
- #743 LOW — `NOTE_DELETE_REDIRECT` still says notes can't be deleted from chat
- #745 LOW — The saved `note_ids` are never read
- #746 LOW — Linking rewrites the whole `contacts` array
- #758 LOW — The positional note delete also says "your note" for someone else's note
- #760 LOW — Space grouping merges two numbers into one cost
- #761 LOW — The overdue midnight keeps `fold` and disagrees with the other midnight helpers
- #762 HIGH — Negated rename, field and notes edits still write
- #763 LOW — "what sizes does it come in?" is claimed for materials whatever is in focus
- #764 LOW — The size-command pronoun set misses they / these / those and "it please"
- #765 LOW — A material literally named "One", "Material" or "It" can't be named in a size command — *accepted / watch item*
- #774 LOW — "I need you to mark it done" no longer counts as a command
- #778 LOW — The work-item question lane routes by regex outside `command_grammar.py`
- #779 MEDIUM — A bare status word is stripped even when it's the customer's surname, and the shortened name substring-matches other contacts
- #780 LOW — When a question names two statuses, one wins silently

**Platform — services, scripts and integrations** (2)

- #30 LOW — `[A-Z]{2}` with `re.IGNORECASE` for state-code parsing — *moved to `agents/property/text_helpers.py:548`*
- #372 LOW — platform/services/translation.py:712 — unbounded concurrency in `asyncio.gather`

**Portal — estimate builder** (2)

- #640 LOW — A Maple change during the first load is dropped
- #660 LOW — Every Maple reload refetches the company's full property and contact lists

**Portal — layout, navigation and Maple panel** (8)

- #123 MEDIUM — `formatOrchestratorReply` mutates input parameter
- #119 LOW — URL build via string concatenation in widget API client
- #121 LOW — Implicit "welcome bubble has id 0" coupling
- #356 LOW — portal/src/lib/orchestratorReply.ts:80 — combine can stack two questions on distinct question-bearing refusals — *accepted / watch item*
- #357 LOW — portal/src/lib/orchestratorReply.ts:74 — substring dedup could over-collapse a degenerate short question — *accepted / watch item*
- #727 MEDIUM — `mergeRestored` can wipe the restored transcript when the pending message repeats an earlier one
- #753 LOW — A failed analytics refetch after a Maple write shows $0
- #756 LOW — A restored `open_question` can overwrite the result of a turn that already finished

**Tests and tooling** (6)

- #304 MEDIUM — Dual-mock pattern in `test_orchestrator_endpoint.py` after helper extractions — *partly — now actionable: the aliases are dead imports (`routers/agents.py:135-142`); drop them and the stale patches*
- #53 LOW — `_CONFIRMED_WORKING_CASE_IDS` has no entry-validation
- #351 LOW — `React.ReactNode` referenced without explicit React import in MapleMarkdown.test.tsx
- #427 LOW — platform/agents/orchestrator/intents.py — `is_anaphoric_add_request` has no direct unit test (finding #12)
- #583 LOW — Lost the agent-level check that Review status is editable
- #584 LOW — Rewritten Maple note tests don't check `success` or the response copy

**Codebase hygiene (batchable)** (17)

- #115 MEDIUM — Mixed string-vs-regex tuples in `refusal.py`
- #301 MEDIUM — `messages: List[Any]` in `agents/estimate/service.py:1811` weakens type info — *moved to `agents/estimate/llm_pipeline.py:1094`*
- #117 LOW — `_LLMHolder` class is more scaffolding than the use needs — *partly: the public service no longer has it; the class remains in `agents/maple_guide/service.py:119`*
- #153 LOW — `_PolicyShortCircuit.response` field name overloaded
- #154 LOW — `_TopicFlags.property` field name shadows Python builtin
- #233 LOW — `_LABEL_PATTERNS` is a mutable class-level dict — *partly: module-level now (`agents/property/text_helpers.py:62`), still mutable*
- #282 LOW — `"hard_cap_reached"` string literal repeated in `routers/agents.py`
- #324 LOW — Language codes `"en"` / `"es"` are bare string literals
- #348 LOW — Defensive `'Sent'` fallback in `_authorize_status_transition` is logically unreachable
- #371 LOW — platform/agents/estimate/text_helpers.py:589 — `_parse_estimate_date_filter` docstring not updated for numeric windows
- #608 LOW — `QUOTED_VALUE_GROUP` comment names a caller that doesn't use it, and the constant splits a block
- #622 LOW — `ClientContext` has no docstring
- #623 LOW — `context_scope` module docstring is out of date
- #625 LOW — `WorkItemEdit` has no docstring
- #626 LOW — `_handle_work_item_edit` has no docstring
- #739 LOW — `load_conversation` is used only by tests
- #749 LOW — The `assigned_to` parameter is now unused
