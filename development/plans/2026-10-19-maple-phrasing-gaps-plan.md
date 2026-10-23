# Maple phrasing gaps after the October features — plan (2026-10-19)

**Status:** built 2026-10-19/20 on `claude/maple-phrasing-review-0af5ac` (platform, documentation, workspace), not committed — §6. Simon decided D1–D4 on 2026-10-19 (§4). Open: G32 (to be confirmed by the acceptance run) and the full live runs, on Simon's word.
**Source:** a review of [`maple-phrasing-reference.md`](../maple-phrasing-reference.md)
against what shipped since the last parity run (2026-10-14): the shared
material catalog (stages 1–2, 2026-10-15/17), Maple session history and its
delete (2026-10-16/17), files on a Maple message (2026-10-18/19), task titles
from markdown notes and the planner's bare task title (2026-10-17/18).

## 1. How the gaps were found

Each candidate phrasing was planned twice by the live planner (gpt-6-luna,
`plan_turn`, no database — a few cents in all). Files were put on the message
by hand (`turn_attachments` with read text: a business card, a supplier
invoice, a work order, a photo of a to-do list), since the live run can't do
that yet (G20).

- **Already right** — added to the reference as ✅/🛑 rows, so the run scores
  them from now on: a misspelt delete or list, "is there a contact named Bob?",
  "do I have Black Mulch?", "do we have a property on Oak St?", two contact
  fields in one message, "start a new chat", a contact updated from a card, a
  property made from a work order, a material's cost from an invoice, one task
  per line of a photographed list, a file put on a role (refused), removing a
  task photo (redirected).
- **Wrong or missing** — G1–G24 below, each a ⚠️ row (or a paragraph, where
  the plan is right and only the words are wrong) in the reference.

## 2. The gaps

| # | Phrasing (reference §) | What the planner did | What it should do |
|---|---|---|---|
| G1 | `hide Black Mulch` (§4.1) | refused "other", or asked what to do | hide the standard material after a yes; Owner/Admin |
| G2 | `show Black Mulch again` / `unhide Black Mulch` (§4.1) | showed its details / refused | unhide it; Owner/Admin |
| G3 | `which materials have I hidden?` (§4.1) | refused / "can't look up hidden materials" | list the hidden ones |
| G4 | `unhide all my materials` (§4.1) | refused | the Materials page's unhide-all, after a yes |
| G5 | `reset Black Mulch to the standard price` (§4.1) | asked what price / read the price | drop the company's override |
| G6 | `is Black Mulch a standard material?` (§4.1) | read the description | say standard or the company's own |
| G7 | `which of my materials are standard?` / `list my custom materials` (§4.1) | asked what "standard" means / listed all, "custom" dropped | list by source |
| G8 | `turn on the Irrigation standard materials` (§4.1) | Load Standard redirect or "other", run to run | toggle the category (Owner/Admin), or one consistent redirect — design §9 says toggle |
| G9 | `add a 2 yd size to Black Mulch` (§4.1) | planned right; handler refuses, no offer | offer the copy — **D2: yes** |
| G10 | `show me my past conversations` (§10.10) | "other", or the `documents` redirect | point to *Chat history* |
| G11 | `what did we talk about yesterday?` (§10.10) | help or small talk | "I only see this conversation" + *Chat history* |
| G12 | `delete this conversation` (§10.10) | "other"; once an invalid capability | point to the delete in *Chat history*; the open one can't be deleted |
| G13 | `start over` (§10.10) | plan right; `meta.START_OVER` names "the clear button" | name *Start a new session* and say the chat is kept in *Chat history* |
| G14 | `here's a video of the yard, make an estimate` (§10.11) | "other" or **equipment** | the `media` redirect (videos go on the task) |
| G15 | `remove the photo from T0042` (§10.11) | `media` redirect, but the flag-on words say "attach it with the + button" | words for a removal |
| G16 | `show me the photos on T0042` (§10.11) | the task's notes, or a redirect | the task's media by name |
| G17 | `what's in the PDF on Elm House's note?` (§10.11) | the notes listed; a filed file is never read | list the files by name; Maple reads only files sent to her — **D3** |
| G18 | `add the materials on this invoice to my catalog` (§4.11) | one question for every material at once | refuse several materials at once — one per message — **D4** |
| G19 | `attach this to Black Mulch` (§3.9) | a note on the material one run in two | always `notes_on_catalog` |
| G20 | the live run itself (§10.11) | file rows run with no file | a `[files]` state |
| G21 | `remove Bob Lee's phone number` (§3.6) | asks for a new value | clear the field |
| G22 | `which contacts did I add this month?` (§3.5, §2.5) | every record, the window dropped silently | a created-in window, or say it back |
| G23 | `undo that` / `take that back` (§10.10) | refused / showed the contact / empty update | undo Maple's last change only when asked, after a yes — **D1** |
| G24 | `who created this task?` (§7.13) | the details, which don't name the creator | name `created_by_email`'s teammate |

**Found by the live run** (§5 below; each re-planned three times before it counted):

| # | Phrasing (reference §) | What the planner did | What it should do |
|---|---|---|---|
| G25 | `what's my average labour rate?` (§5.11) | refused 3/3 — `labour_rate`, "other", Settings | `catalog_figure` average role rate — a read, not the rate setting |
| G26 | `Mulch is $6 per bag` (§4.8) | asked which mulch / whether a price, 3/3 | the price of the one-size material named exactly |
| G27 | `show labour roles in outdoor` (§5.5) | asked division or category, 3/3 | `list_labours` filter.name |
| G28 | `what properties does {contact} own?` (§8.1) | the contact's details, 3/3 | `list_properties` filter.owner (row moved 2026-10-13) |
| G29 | `delete the PDF on the fence task` (§7.6.1) | 2/3 offered to delete the whole task | the `media` redirect — never offer a bigger delete |
| G30 | rows that drift (§12.4) and `add a template` (§9.5) | right 1–2 times in 3; "add a template" asks for a name | a prompt line or correction each, after re-plans show which hold |
| G31 | stray `yes` after a stale delete (§1.11, conversation) | planned the old delete again (asked first) | "I'm not waiting on an answer" |
| G32 | `New Request` answering the task-status question (§7.7, conversation) | asked again | the status, as a company status always answers it |
| G33 | the conversations run itself | the planner is fed today's state, so turns after a turn-1 split test nothing (`Clear Coat`, `Remove Sod`) | a planner-only conversations run on the planner's own state |

## 3. Plan

Planner-first, TDD per CLAUDE.md; each correction as narrow as its case with
nearby phrasings pinned as left alone; each step flips its reference rows to ✅
in the same change. A prompt or `agents/planner/` change is checked with a few
live messages (cents) and owes the parity run, which runs only when Simon asks.

**Step 0 — the run can carry files (G20).** `scripts/phrasing_reference_rows.py`
and `tests/planner_parity/cases.py` gain a `[files]` state (a photo and a PDF
with read text in `turn_attachments`), and the file rows of §3.9, §4.6, §7.6.1,
§1.3, §1.10 and §10.11 move onto it. Test: `test_phrasing_reference_rows.py`
reads the state; a parity-harness test builds its context.

**Step 1 — words and guards, no new ops (G13, G14, G15, G19).**
- G13: `meta.START_OVER` names *Start a new session* and *Chat history*
  (`test_maple_meta*`, the planner's start-over test).
- G14: a video asked of Maple is the `media` refusal — a prompt line plus an
  `as_asked` correction from "other"/`equipment` when the message says
  video/clip/footage; `is_equipment_request` must not claim "video".
- G15: a `MEDIA_REMOVE_REFUSAL` for removing or deleting a file, chosen when the
  refused request removes; entry in `maple_outcomes._reply_rules` and
  `test_maple_outcomes.py`.
- G19: `add_note` with a material or role parent is refused `notes_on_catalog`
  in the policy, whatever the model planned.

**Step 2 — session history redirect (G10, G11, G12).** A new out-of-chat
capability `history` (schema `OutOfChatCapability`,
`out_of_chat.REDIRECT_CAPABILITIES`, a redirect in the user guide's words, a
prompt line): open or list past conversations → *Chat history*; "what did we
talk about yesterday?" → Maple sees only the conversation open now, and past
ones are under *Chat history*; delete a conversation → the delete in *Chat
history* (the open one can't be). The planner still never sees history.

**Step 3 — standard catalog ops (G1–G8; catalog design §9 = its stage 4).**
`WRITE_OPS` gain `hide_material` (a list of names, or `all` for unhide),
`show_material`, `reset_material` and `toggle_standard_category`;
`list_materials` gains `filter.source` (standard / custom) and
`filter.hidden`; `get_material` gains `field=source`. All through
`services/material_catalog`, Owner/Admin per decision §11.4, writes asked
first like deletes, replies in the portal's words. G8 replaces the
`load_standard` redirect for a named category (Load Standard for People stays).
G9 (D2): a size, name, description or category change refused on a standard
material ends with the copy offer — *"Black Mulch is a standard material, so
its sizes can't change. Want me to make you a copy — Black Mulch copy — and add
the size there?"* — and the yes makes the copy (named per catalog decision 8)
and applies the change to it, Owner/Admin. §9.8's duplicate redirect stays for
everything else (estimates, custom materials, roles, templates).

**Step 4 — fields and filters (G21, G22, G24).**
- G21: `ContactFields` / `PropertyFields` gain `clear` (a list of field names),
  clashing with a value for the same field like the task clears; the update
  handlers write the field empty (check each takes it before relying on it).
- G22: `created` (a `PeriodName` or `since`) on the contact, property and
  material filters, read by their list handlers; until then a window the
  message says is said back, never dropped (the `unread_scope` rule).
- G24: task details name who created the task (the teammate's name for
  `created_by_email`), in `task_details_reply` so both pipelines say it.

**Step 4b — regressions from the run (G25–G32).** One narrow fix each, with
neighbours pinned: G25 a prompt line (an average rate is a figure) plus an
`as_asked` correction from a `labour_rate` refusal on a question; G26 and G27
prompt lines; G28 the prompt's owner wording; G29 a policy guard — a refused file
removal never becomes a delete question about its record; G31 the planner's
stray-yes rule reads the open questions, never the chat history; G32 a company
status named in reply to the planner's status question is the answer. G30's
drifting rows are re-planned five times after each fix and fixed only where they
miss most of the time; `add a template` gets the template-create refusal.
G33: `test_conversations_parity` gains a planner-only mode (the planner's own
state carried turn to turn, as `MAPLE_PLANNER_ONLY` runs it).

**Step 5 — files already on records (G16, G17) and several creates (G18).**
G16: `get_task` field=media lists the task's photos and PDFs by name. G17 (D3):
a question about a file already on a record lists that record's files by name
and says Maple reads only files sent to her — "send it here and I'll read it";
no vision call. G18 (D4): a plan with more than one `create_material` is
refused in the policy, whatever the model planned — Maple adds one material per
message and says so; one material from a file still works.

**Step 6 — undo (G23, D1).** Maple never undoes anything unless asked. Her
last write in this conversation is kept on the conversation (the record, the
fields it changed and their values before — one entry, replaced by the next
write, dropped by a new session). "undo that", "take that back", "put the price
back to what it was" is a new `undo_last` op: Maple names what she would set back
and asks first (*"Undo my last change — Black Mulch 2 cu ft price back from
$5.00 to $4.40? (yes/no)"*), through the planner's confirmation
(`confirm.py`); the yes writes the old values through the record's update
handler, with every rule checked again (role, standard material, locked status).
With nothing kept, or when the record has changed since, Maple says so and
writes nothing. To settle when building it: what undoing a create or a delete
means (proposed: a create is undone by deleting what was made, asked as any
delete; a delete is never undone — the record is gone).

Then the parity run, on Simon's word, before the push.

## 4. Decisions (Simon, 2026-10-19)

- **D1 — undo (G23).** Maple should not undo on her own. If the user asks to
  undo the last action, Maple confirms first before taking it (step 6).
- **D2 — a copy of a standard material (G9).** Yes: the catalog design's offer,
  for standard materials only, Owner/Admin (step 3).
- **D3 — a file already filed on a record (G17).** Yes: list the files by name
  and say Maple reads only what is sent to her (step 5).
- **D4 — several materials at once (G18).** There's no invoice in the app;
  creating several materials at once is not supported (step 5).

## 5. The live run, 2026-10-19

The full parity run (`tests/test_planner_parity_live.py -m llm_e2e`, 42 min;
conversations re-run once, 9 min) after the new rows went in. Reference: 1,476
cases, 1,339 agree, 48 differ, 4 blockers, 2 refusals missed (2026-10-14: 1,422,
1,312, 33, 0, 1). Routing, expected and CRUD are within a few rows of 10-14.
Every row added in this review that needs no file agreed. The 19 rows that need
a file all ran without one (G20). The rest is G25–G33; the record is
§12.4 of the reference.

## 6. As built (2026-10-19/20)

Every step, TDD, each phrasing checked live three times (cents) with nearby
phrasings pinned as left alone. Platform files new: `agents/planner/as_asked_files.py`,
`as_asked_reads.py`, `execute_catalog.py`, `undo.py`; tests
`test_planner_as_asked_files.py`, `test_planner_as_asked_reads.py`,
`test_planner_material_catalog_ops.py`, `test_planner_undo.py`, and new cases in
the schema, policy, execute, reads, writes, files, outcomes and meta suites.

| Step | Gaps | What closed them |
|---|---|---|
| 0 | G20 | `[base+file]` states (`tests/planner_parity/cases.FILES`, `scripts/phrasing_reference_rows._STATE_NAME`); 29 file rows moved onto them. Their first live check found G34 (a record named with a file read, not filed) and G35 ("add this plan to the estimate" priced) |
| 1 | G13, G14, G15, G19, G29, G34, G35 | `meta.START_OVER` names *Start a new session* and *Chat history*; `as_asked_files` (video → media; a file removed → media with `MEDIA_REMOVE_REFUSAL`; a name alone with a file → its attach; a file note's text that is the command dropped); `policy._check_catalog_notes`; prompt lines |
| 2 | G10–G12 | out-of-chat `history` capability and its redirect; a prompt line |
| 3 | G1–G9 | `hide_material`, `show_material`, `reset_material`, `copy_material`, `set_standard_category`; `filter.source` / `filter.hidden`; `field=source`; `resolve.hidden_material_named`; `policy._check_catalog_ops`; `confirm._ask_catalog` with `Asked.kept` for the copy offer (D2); `material_catalog.find_by_name(visibility=…)` and `next_copy_name`; the tool budget to 62,300 |
| 4 | G21, G22, G24 | `ContactFields` / `PropertyFields` `clear` (a contact keeps its name; a property its street, city and province) through `clear_contact_fields_reply` / `clear_property_fields_reply`; `filter.added` / `added_days`, said back beside another filter; task details "Created by" |
| 4b | G25–G31 | `as_asked_reads` (average rate → `catalog_figure`; "add a template" → `template_edit`; a stray yes never writes); prompt lines for G26–G28; G30's drifting rows left to re-plans |
| 5 | G16–G18 | task details name their files; a notes list names each note's files and, asked what one says, `FILED_FILES_NOT_READ` (D3); several `create_material` refused (`MULTI_MATERIAL_CREATE_REFUSAL`, D4) and a prompt line planning one create per material (it first quoted the refusal, which the model applied to a to-do list's tasks too) |
| 6 | G23 | `undo.py` (D1): every write kept as `maple_last_write`; `undo_last` asked first, fields set back only while unchanged since, a create undone by its delete; the tool budget to 63,400 |

The user guide (`platform/user_guides/users_guide.md`) gained the catalog,
file, history and undo lines Maple's help answers from; the workspace rules
(`.claude/rules/maple.md`, `materials.md`) name the new modules.

**Live check, 2026-10-20**: the reference source alone (§12.4 of the reference) —
0 blockers (4 before), 30 differences (48 before); two prompt lines narrowed after it.
**Acceptance run, 2026-10-20:** 294 of 312 conversations passed, with 17
explained (all explained before this branch). The 1 that counted, a "best
customers" clarify, was drift: it passed 3 of 3 alone. **G32 is closed** there. Four
conversations for this plan's multi-turn flows were added to the corpus (undo yes
and no, a stray yes, hide asked first): 12 of 12 passed over three runs. Owed, on
Simon's word: the full parity run, before the push.

**The new rows alone, 2026-10-20** (78 rows, three plans each; reference §12.4):
the run found one more gap and two of this plan's own prompt lines overreaching.
- **The gap:** a photo put on a work item was planned as the work item's note,
  written without the photo. It is set right by
  `as_asked_files.work_item_files_refused`, and an edit with words of its own
  says the file isn't on it.
- **The prompt lines:** the several-materials line made a to-do list "one task at
  a time", and the material-source line took "do I have Black Mulch?". Both are
  narrowed.
- **The rows:** five reference rows reworded to the plan they mean, and three
  messages explained.

After the changes: 272 of 288 right, 0 blockers.

**G33** needed no new mode: `tests/test_planner_acceptance_live.py` already runs
every conversation on the planner's own state. A full live run is it and the
parity run together (noted in the Maple rules).
