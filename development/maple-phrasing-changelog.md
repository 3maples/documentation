# Maple Phrasing Reference — Change Log

The dated history of [`maple-phrasing-reference.md`](maple-phrasing-reference.md),
newest first. It was split out of the reference on 2026-09-27, when it had grown
to over a third of that file; the entries below are moved verbatim and were not
re-verified against the code after the 2026-09-25 routing convergence, so read
them as what was true on their date. The reference itself keeps only a short
"Recent changes" list and is the current truth. Two bullets that still read as
current behaviour — work-item recurring schedules, deferred from chat on
2026-09-26 — carry a bracketed 2026-09-27 note; nothing else was changed.
New entries go at the top of this file.

### Change log

**2026-09-27 — multi-turn everywhere** (design
[`plans/2026-09-27-maple-multi-turn-everywhere-design.md`](plans/2026-09-27-maple-multi-turn-everywhere-design.md);
platform `3526a08` … `67892ec`)

- Deletes: every Maple delete asks first; only a plain yes confirms (#674);
  Owners and Admins only, as in the app; "delete the note on Bob" / "remove
  Ana from 12 Oak St" never delete the record (§9.9).
- Catalog writes run as the signed-in user (they crashed with auth on); a
  material cost edit keeps the markup (the server derives the price); Maple
  never creates a category or unit as a side effect of a material create —
  an unknown one is named in the reply.
- A refusal ends the turn; out-of-chat requests (Settings, team, billing,
  Load Standard, CSV, units, divisions, unlinking records, duplicate,
  documents, photos) are answered with where to do them (§9.8, #697).
- One gate for every question; a question lives one turn (§10.6; #671,
  #675, #676). An edit that reaches a stale anchor only through "it" asks
  first; a named contact or property beats the one in focus (§10.7, #677).
  "the second one" answers only from a list that is still current (§10.5).
- "thanks", stray yes/no, cancel, repeat, start over (§10.10); the
  conversation keeps its language across short replies.
- "what about X?" / "and last month?" repeat the last read (§10.8).
- A named estimate keeps its house number and connectors ("4 Elm St",
  "Edge of the Garden"; #334). A task title containing "last" is a title.
- Tasks (§7): due-date verbs ("make it due Friday", "push it to next week",
  "clear the due date"), status verbs ("I finished it", "reopen it"), give /
  unassign by teammate name, property link / unlink; creates that carry a due
  date, assignee, status and property; "remind me to …", "add … to my to-do
  list", "new to-do: …"; list filters (overdue, due windows, upcoming,
  status, open, assignee, unassigned, property) and "what's due today?"
  (#687, task half); value questions and "which task?" menus that resume by
  number, readable id or title words (#692); "show more" (§10.9). A field
  answer never lands on the newest task instead of the one being edited
  (#698).
- Estimates (§1): with an estimate in focus, "mark it as sent" / "mark it
  won" / "archive it" / "link it to 12 Oak St" act on it; questions about one
  estimate (status, total, customer, property, markup, margin, dates) are
  answered from it, not the user guide (#691), and its details show the
  property and customer; "which estimate?" menus resume by code, number or
  name (#685); "delete the first one" after a list deletes that row (#686);
  "list estimates for Bob Lee" and "from last month" filter (#687); the list
  just shown can be narrowed, sorted and totalled; "put together / draw up
  an estimate for …", "I need a quote for …" and "quote a fence for …"
  create one; "send it" says how. About 46 work-item phrasings that only the
  LLM planner understood got grammar entries — material and activity lines,
  division and total verbs, margin/markup wordings, "scope" as a work item —
  and notes land where they were addressed (#664, #665, #666, #684). Routing
  notes are never shown to the user.
- Contacts, properties and notes (§2, §3, §3.9): notes are added ("add a
  note to him: …", or the text on the next turn), read back and deleted
  (your own, after a yes); "link John Doe to 123 Main St" in either order;
  creates ask for what's missing in plain words and take a bare name;
  "his phone is …" / "zip …" after a create or a view update that record;
  "which contact?" lists names and resumes; lists filter by city and role;
  "add a contact named …" creates; "show me Elm House" finds the property;
  "update the name of 12 Oak St to Oak House" renames it correctly. A
  greeting during estimate gathering and an estimate edit during "link a
  property?" are never taken as answers (#683, #687).
- Materials, people and templates (§4, §5, §6; platform `00110ed` …
  `948e255`): a material, role or template named without its kind ("the
  Paver Patio template", "Topsoil's price", a bare "Black Mulch") is found;
  "move Topsoil to the Bulk Materials category" works (#694); "list my
  roles" lists every role and "Heavy Equipment Operator" is a role, not
  equipment (#693); sizes of more than one word, and add / remove /
  reprice / rename / list a size, by rule; "which size?" resumes the edit;
  a new role or material is asked for one field at a time, and a material
  for its cost, priced by the server from the markup; "find templates named
  Paver" and "which templates have … in the name?" filter. Possessive looks
  ("show me Bob Lee's details", "what's the phone number for Bob Lee?",
  "update Bob Lee's record") reach the record — they routed but found no one.
- Dashboard (§1.9, §7.5; platform `6fcdff9`): "what's my pipeline?",
  "what's in my backlog?", "how much have I completed this month?", "show me
  my dashboard", "give me a summary", "how's business?", status and division
  breakdowns reach the analytics handler; "and last month?" repeats a period-
  less read for that period; "what are my recent estimates?" lists the newest
  eight. "what's upcoming?" includes overdue tasks, overdue first, and "what's
  on my plate?" is that list for you.
- The portal (§10.6, §10.7; platform `c478a53`, `9f657b4`, `d608e74`; portal
  `97c87f4`, `19257da`, `dd54cd3`): "Waiting for your answer · Cancel" while
  a question is open, Yes/No chips on a yes/no question; the contact,
  property or task open on the page is "this one" ("add a note: …", "what's
  her phone?"); catalog pages refresh quietly after a Maple write, and
  template, link and note writes refresh what they change; a restored chat
  reads in the language it was held in; two overlapping turns keep each
  other's state, and a double-sent message isn't run twice.
- Across records (§8; platform `634703f`, `695e0f8`): "which properties use
  Black Mulch?", "which properties need a Foreman?", "what estimates use the
  Foreman role?", "what materials does E0042 use?" and "which roles are on
  E0042?" read the estimates' work items — they queried fields `Estimate`
  doesn't have and were always empty (#682). "which estimates use Black
  Mulch?" / "find estimates with …" and "show me jobs needing a Foreman"
  filter instead of listing everything; the replies say it in plain words.

**2026-09-26 — routing convergence: rounds 12–24**

- Thirty-third review: tasks follow the estimate rule — a task reference
  that counts from the end ("mark the second to last task as done") asks
  which task, and is never matched to a task by its title; "the second task"
  with no list shown asks too. A list pick is the first reference in the
  message: "rename the last one to Lot #2" renames the last one, and "the
  last one, not the first one" / "…instead of the first one" mean the last
  one. A title shared with an archived estimate ("Patio" live, last year's
  "Patio" archived) resolves to the live one; a list of matching estimates
  shows the newest first, with each status. "the Smith residence" finds the
  property named "Smith" (whole words, either direction).
- ⚠️ Gap (follow-up #670): a customer name ending in punctuation ("Acme
  Inc.") isn't matched.
- Thirty-second review: an estimate named by its customer matches the
  customer's name, street or property name as a whole word — "the lee job"
  is Dan Lee's, never Kathleen Moore's; "park" is not "45 Parkside Dr". A
  named estimate is looked up among all the company's estimates (archived
  too), not only the newest 100, so "the Patio estimate" finds the one titled
  "Patio" however old it is.
- Thirty-first review: work-item recurring schedules are deferred from chat
  (user decision) — "make work item 2 recurring", "turn off recurring on …",
  "is … recurring?" are no longer handled (§1.5.4 🛑); use the estimate page.
  This also retires a misread where "make the patio work item recurring"
  switched on a work item whose name contained "recurring". The "the patio
  job" work-item menu now names an estimate Maple guessed from a while back,
  like the other menus. "Great, archive …" / "Perfect, archive …" archive —
  the archive check shares the grammar's lead words.
- Thirtieth review: with a note or description in the message, "archive"
  is an archive command only when the message starts with it ("archive the
  Site Overview estimate", "please unarchive the Notes estimate"); anywhere
  else it is the text ("add archive photos to the notes on this estimate").
  When a "which work item?" menu or a "what should the new description be?"
  prompt is about an estimate Maple guessed from a while back, it now names
  it ("On E0042 'Spring Cleaning': …"), and answering it is the
  confirmation.
- Twenty-ninth review: changing an assumed size or material "on the patio
  job" no longer asks "Which work item?" (the answer was ignored); it
  targets the assumption by name as before. "archive the Site Overview
  estimate" / "archive the Notes estimate" archive again — a note or
  description word only stops an archive when it comes before it. "on the
  other / new / whole / entire job" is not a work-item name; Maple asks which
  estimate. A plan that both guesses the open work item and names another
  now asks about the guessed one, and a removal question also names a
  guessed work item the same batch would change.
- ⚠️ Gap (follow-up #667): on a locked (Sent/Won/…) estimate, a note phrased
  in a way no rule parses is refused instead of filed.
- ⚠️ Gap: "mark the Site Overview estimate as sent" — a title holding
  notes/description/overview blocks a "mark … as" status change; use the
  code ("mark E0042 as sent").
- Twenty-eighth review: a "… job" name that matches two or more work items
  on the open estimate ("set the tax to 13% on the patio job" with "Front
  patio pavers" and "Back patio lights") asks which one — it used to change
  whichever work item was open. Adding a work item "to the patio job" still
  goes on the open estimate. A note or description whose text says
  "archive" ("note on this estimate: archive photos go in the shared drive")
  is no longer read as archiving the estimate; say "archive E0042" or
  mention "status" to change it.
- ⚠️ Gaps (follow-ups #664–#666): an estimate note by code or "that estimate"
  with "saying"/"that says"/"about" instead of a colon asks where it goes; a
  work item named before the verb ("On work item 2, add a note: …") goes on
  the estimate; "note: on Friday - bring the trailer" asks where it goes.
- Twenty-seventh review: a note that says where it goes in a shape Maple
  doesn't parse — a quoted body before its target (`add a note "check
  drainage" to work item 2`), a " - " after it ("add a note to the work item
  on E0042 - check drainage"), or any target other than an estimate code or
  "this/that/our estimate" ("drop a note on the Johnson Residence estimate:
  …", "leave a note for the crew: …") — asks "Which estimate or work item
  should the note go on?" instead of going on the open estimate. Untargeted
  notes ("add a note to call the client", "note: …") and ones addressed to an
  estimate by code ("Set note on E0059 to \"…\"") file as before. "add a
  note to the patio job: …" asks whether you mean the estimate titled Patio
  or the open estimate's patio work item when both exist. A task note whose
  title holds "about" or "from" ("add a note to the call Bob about pricing
  task: …") goes to the task instead of being refused as a material.
- Twenty-fourth review (supersedes the "the work item" parts of the 22nd and
  23rd): "the work item" with no number or name is not read as the one you
  have open — say "this work item", "work item 2" or its name. It never
  changes a guessed work item either. A note to a work item Maple can't
  pick out ("add a note to work item 2, 3 and 4: …", "…to the work item: …")
  asks which work item instead of going on the estimate; a note to someone
  that mentions the work item ("add a note to John Doe about the work item:
  …") goes to that person.
- ⚠️ Gap: a bare "the work item" ("set the markup on the work item to 20%",
  "add mulch to the work item") — use "this work item", its number or name.
- Twenty-third review: "rename the work item for the patio job to …" no
  longer renames the estimate itself, and "set the markup on the work item
  for the patio job to 20%" no longer changes the open work item — "the work
  item" followed by for/on/in/of/from names which one. "set the work item
  description to …" changes the open work item (it looked for one called
  "description"). "add a note to the work item: …" files a work-item note.
  A note to a contact or property whose text mentions "the work item" ("add
  a note to John Doe saying he approved the work item") goes to that record.
- Twenty-second review: "the work item" on its own means the one you have
  open, like "this work item". "set the markup on the work item to 20%" /
  "set the total on the work item to $500" / "set the gross margin for the
  work item at 30%" change the open work item — "to"/"at" was read as a
  work item's name and could change one called "Topsoil…". "add mulch to
  the work item" goes to the open work item (it was not understood, or
  created a material). "set the work item total to $1,600" sets the open
  work item's total (it looked for a work item called "total").
- Eighteenth review: a change whose message counts from the end — "archive
  the second to last estimate", "now rename the second to last one to …",
  "mark the second to last draft estimate as sent" — and doesn't name the
  estimate by code or title asks first: "Just to check: apply this to E0042
  'Spring Cleaning'? (yes/no)". No writes, nothing renamed, until you say
  yes. The same question comes up when a message merely mentions it ("set
  the description to install a light next to the last step"); yes applies
  it. Name the estimate (E0042, or its title) and there is no question.
- Sixteenth review (supersedes the fourteenth and fifteenth bullets' special
  question): counting from the end is simply not supported. Maple has no
  special "Which one did you mean?" for it any more; it only makes sure the
  phrase is never misread. "the second to last …" never picks row 2, the
  last row, the newest record or the estimate you have open — however it is
  worded ("that second to last estimate", "the estimate next to last",
  "Make sure to archive the second to last estimate"). What you get instead
  is the ordinary answer ("Which estimate…?", "Which one did you mean?").
  "Make sure to add … to our equipment list" is refused again, like any
  equipment request.
- Fifteenth review: a message is read left to right — the first thing it
  names is its target, and a position counted from the end after it is
  content. "add a note to E0042 saying the second to last bed needs mulch",
  "add a work item called Regrade the second to last bed", "rename it to
  Install next to the last row", "change the description of task T0042 to
  mulch the second to last bed…" and "create a task to fix the second to
  last sprinkler head" all do what they say; "Add to it the following: …
  next to the last step" keeps the estimate you have open. "apply the …
  template to the estimate next to last" asks which estimate (it created a
  new one).
- Fourteenth review: Maple asks "Which one did you mean?" once, before
  anything else runs, whenever the command counts from the end — so
  "archive the second to last estimate" no longer archives the estimate
  you have open, and "apply the … template to the second to last estimate"
  no longer applies it there. "the second last one", "2nd-last" and "the
  one before the last one" are the same kind of phrase (they were read as
  the last row). In a new value it is content: "…the second one to install
  next to the last row" picks row 2, and "change the description to Install
  the gate next to the last fence post" sets the description.
- Thirteenth review: a position counted from the end — "the second to last
  one", "the next-to-last task", "the third from last row" — is never read as
  a row on any list; Maple asks which one. It is never "the newest" either
  ("mark the second to last task done" no longer marks the newest task).
  "…the second one to install next to the last row" still picks row 2. A
  colon inside a note's body stays in the body ("…for Smith saying call at
  3:30", "…that says gate code: 4412", "…that the gate code is: 1234").
- ⚠️ Gap (not supported): counting from the end ("rename the second to last
  estimate to …", "delete the next-to-last task", "the second last one",
  "the one before the last one") — say the row's number, code or name
  instead. "first" and "last" work.
- ⚠️ Gap: a note to an estimate whose title contains "that", "says" or
  "saying" by its "for/called" form ("add a note to the estimate called Walk
  That Way: …") — the title stops before "that"; use its code, or "the Walk
  That Way estimate: …".
- Twelfth review: "add a work item for the estimate for Smith" / "…to the
  estimate for John Smith Patio" adds a work item to Smith's estimate — it
  was priced as a scope on the open one. "add a note to the estimate called
  Oak Street - Phase 2: …" keeps the whole title (a colon ends it). With no
  list shown, "the second estimate" asks which estimate rather than taking
  the newest.

**2026-09-25 — routing convergence: final review fixes**

- "Yes, go ahead", "Sure, go ahead", "yes, delete it" answer a yes/no
  question (they were read as new requests).
- A title no longer keeps "thanks", curly quotes or a trailing "on E0042";
  "set the title to Spring Cleanup on E0042" targets E0042.
- Adding a work item, renaming, a note, a status change and the other direct
  writes ask "Just to check: apply this to E0042?" when the estimate came from
  an anchor the user hasn't touched this turn or last — as line edits
  already did.
- "add a note to this work-item: …" (hyphen) goes on the work item.
- "set the price of mulch in the catalog to $5" edits the catalog even when
  the open work item has mulch.
- "add a task: lower the markup to 10% on work item 2" creates a task.
- "Add a new work item to it. The client wants to build a patio in their
  backyard. It will be about 900 sq ft in size." prices the described patio
  as a new work item on the estimate "it" refers to — it was read as "add a
  client" and asked for a contact's name. A command's target comes from the
  sentence holding its verb; later sentences describe the job
  (`command_sentence()` in `agents/text_utils.py`). "it" is the last record
  worked with: after a material or contact, it isn't the estimate.
- "set description on this estimate: Same scope as E0017" / "change the
  write-up to …" are no longer read as a status change (the text after "as" /
  "to" was taken as a status and refused with the status list): a message
  naming the description, notes, write-up or overview is a status change
  only when it says "status".
- Tenth review: "the current / the same / the estimate" is the open estimate
  and "the latest / the second estimate" is found by recency or Maple's last
  list — never looked up as a title; "…on estimate E 0 0 4 2" / "#E0042" is a
  code; "set the description of this estimate to … on E0017" keeps "on E0017"
  in the description; "add a work item called Fence for E0042" goes on E0042;
  "add a note to the Smith estimate: …" and "…to work item 2 on E0042: …" are
  filed, not refused; "add a work item for the Smith estimate please" is not a
  scope; "Add a new work item called Spring Cleanup" is a work item, not a
  contact; "Add a new contact named Mary Jones. Set the email to …" creates
  the contact.
- Eleventh review: after a list, "the last estimate" is its last row, not
  the newest estimate. "the sixth estimate" / "the 6th estimate" is a
  list pick, never a title. "rename the Back to Basics estimate to Spring
  Cleanup" writes "Spring Cleanup" (a title holding "to" or "as" was cut in
  the wrong place). "…on estimate Smith Residence." / "…please", "…on the
  estimate for Smith to 20%" and "add a note to the estimate for Smith that
  says …" find Smith (the period, "please", "for" or "to" was read as part
  of the title).
- Ninth review (structural): a listed command's estimate is the one the
  grammar parsed — a code or title inside a note, new value or scope never
  moves the write; "change the title to Spring Cleanup" renames the open
  estimate (the leftover "to" was read as a title); `Add a note "…" to E0042`
  keeps its target after a quoted body; "add a work item for a cedar fence on
  E0042" prices it on E0042; "add a work item for the Johnson Residence
  estimate" is not a scope; "the current / the same work item" asks like
  "this work item" when stale; "Add a new work item to it. Mary Johnson
  wants …" is not a contact; "Add St. Mary's Church as a property" is a
  property.
- ⚠️ Gap: "mark the Garden Overview estimate as won" — a message naming
  notes/description/write-up/overview is a status change only when it says
  "status"; a title containing one of those words needs "set the status of …
  to won".
- Seventh review: a delete or "Just to check" question left unanswered across
  a help question no longer waits for a later "ok"; an estimate code inside a
  note or new value ("…: same fix as E0017") no longer moves the write to
  that estimate; "apply the Driveway template to the estimate", "set this
  work item to recur monthly" and "Add to it the following: …" ask first when
  the estimate or work item came from an anchor the user hasn't touched
  lately; an estimate picked from Maple's list is never questioned. *[2026-09-27: superseded — work-item recurring was deferred from chat on 2026-09-26; see the reference's §1.5.4 🛑.]*

**2026-09-25 — routing convergence: rules are a written list**

Six review passes kept finding new phrasings because the rules were
open-ended regexes spread over five layers. Now every estimate phrasing a rule
handles is an entry in `platform/agents/estimate/command_grammar.py` (§1.0
below); everything else goes to the edit planner (🤖) or the classifier. What
changes for a user:
- Material and activity line edits ("add 10 mulch to work item 2", "make the
  excavation activity 6 hours", "set the price of pavers to $4.25") are the
  planner's; the router still sends a line edit to the estimate when the open
  work item has that line.
- A reply to Maple's question is decided in one place: "list my contacts"
  typed at a yes/no or a description prompt is a new request, "no" or "not
  now" cancels, a reply after switching estimate pages never confirms the old
  question.
- A guessed target that isn't fresh asks first ("Just to check: apply this to
  the "Front patio" work item on E0042?"); "delete it" / "rename it" follow
  whichever anchor was touched last.
- "jot down a note for John Doe: …" goes to John Doe; a note for a material or
  role gets "Materials and roles don't take notes."
- "set the markup to 20%" after touching a contact still sets the estimate's
  markup (only estimates have one).
Routing snapshot: `platform/tests/test_maple_routing_snapshot.py` (1,145
phrasings × 4 states, plus decisions for 3 question kinds).

**2026-09-25 — fifth review of multi-turn estimate editing**

From the fifth `/code-review` (fixed #1–#13 and #15; the rest are follow-ups
#646–#661). "delete estimate E0042" → "confirm" now follows the same rule as
the Delete button: only the estimate's creator or an Owner, and the estimate's
notes go with it. With a Maple question open, "delete all work items" or "add
equipment to the patio" is still refused, and small talk is no longer taken as
an estimate edit. After opening a material or a contact, "set the price of
mulch to $5" or "set the markup to 25%" no longer lands on the last estimate.
"rename the patio work item within/inside/under the Smith estimate to X" and
"…work item E0042 estimate…" rename the work item. A menu reply that is a
row's own description ("Add mulch beds", "Remove stump") picks it. A
description that mentions a quote, a count or a code ("Show homeowner the
revised quote before starting") is kept. "set the overhead on the lawn job to
12%, same as the first one" edits the lawn. "add a note to the patio work item
please" → the reply is filed on the patio work item. A work-item note
mentioned inside another request is part of that request. "the pavers cost us
$3.50 now" gets the cost refusal instead of a price change. "set the overhead
lighting work item's markup to 20%" sets the markup. Tests sit beside each fix
(`test_agent_helpers_fuzzy_confirmation.py`, `test_orchestrator_endpoint.py`,
`test_maple_estimate_targeting.py`, `test_maple_work_item_context.py`,
`test_maple_work_item_edits.py`, `test_work_item_edit_detectors.py`,
`test_maple_edit_planner.py`).

**2026-09-25 — fourth review of multi-turn estimate editing**

From the fourth `/code-review` (fixed #1–#6, #10, #12–#16, #18; the rest are
follow-ups #627–#645). "rename the patio work item on the Smith estimate to
Back Patio" renames the work item, never the estimate. With "which work item?"
open, only a bare pick answers it ("2", "work item 2", "the back one"); "set
the markup on work item 1 to 15%" or "show me the 2nd estimate" is a new
request. "What should the description be?" can be left: "cancel" / "no" /
"never mind" answer "No problem, I've left it as is", and "list my estimates",
"how many estimates do I have" or "show me estimate E0004" go where they
would have gone. "set the tax on the lawn work item on the patio job to 13%" edits
the lawn. "add a task to follow up on E0042" creates a task and "add Bob as
the contact on E0042" a contact. Estimates named "Final Grading", "Far Hills"
or "Full Service" are found by name. A rename or division change no longer
re-prices a work item. Tests sit beside each fix
(`test_maple_work_item_context.py`, `test_maple_estimate_targeting.py`,
`test_estimate_edit_executor.py`, `test_estimate_title_reference.py`,
`test_orchestrator_endpoint.py`).

**2026-09-24 — third review of multi-turn estimate editing**

From the third `/code-review` (findings #1–#40). "yes" to a removal removes
the item Maple named even if the list changed in between, and nothing if that
item is gone. Work-item edit phrasings only count when they ARE the request:
"create a task to set the markup to 20%", "don't drop the markup", "remind me
to drop the tax", "if we set the markup to 20% …" and "Hey Maple, add a note:
drop the tax" no longer change the estimate. "raise the markup by 5%" (with or
without "also"/"ok") asks for the new value; "change the markup by 5%" too.
"set the markup on all work items to 20%" and two edits in one message
("remove work item 1 and set the markup on work item 2 to 20%") are asked
about instead of half-applied. A target after the value is kept ("change the
markup to 20% on estimate E0042", "change the name to Front Yard for property
Oak Villa"). "add 500 sq ft of sod to E0001" adds to E0001 instead of creating
an estimate. A bare "Yes" never repeats a delete from earlier in the chat.
"add a note to work item 2 about drainage" files a work-item note. Estimates
titled "Back Yard Materials" or "Activity Center" can be renamed again. "show
me the estimate again" / "the full estimate" show the open estimate. "I'd like
a 20% markup", "give me a 10% markup on the patio work item", "set markup =
20" and material names like `3/4" gravel` or "1.5 inch pipe" work. "generate
a scope for …" with nothing open starts a new estimate. Tests sit beside each
fix (`test_work_item_edit_detectors.py`, `test_maple_estimate_targeting.py`,
`test_maple_assigned_value_routing.py`, `test_maple_work_item_context.py`,
`test_estimate_edit_executor.py`, `test_maple_work_item_edits.py`).

**2026-09-24 — second review of multi-turn estimate editing**

From the second `/code-review` (findings #1–#42). Adding a catalog material
through Maple works again: a real catalog size carries a unit id, and the line
now gets the unit's label. "yes" to a work-item removal removes exactly the
item it named, on the estimate it named, even if you opened another estimate
in between. "set the hours on the overhead pruning activity to 6" edits the
activity, not the overhead; questions and remarks ("why is the markup 20%?",
"i think the markup of 20% is too high") write nothing; "reduce the markup 5%"
asks for the new value instead of setting 5%. "bid" matches whole words only
(Rabideau, Bidwell stay contacts). Catalog and company edits ("the hourly rate
of the Foreman role", "the cost of the mulch material", "my company tax rate")
stay with their agents while an estimate is open. After a work-item list,
"rename the second one to Front Patio Scope" renames that work item, and an
ordinal rename never retitles the estimate. "rename the grading activity to …"
says Maple can't rename a line from chat, rather than retitling the estimate.
"add a note to the patio work item" with no text asks "What should the note
say?" and files the reply. "the patio job" also picks the patio work item, and
matches whole words only. "show me the smith job" with no Smith estimate
offers the open one instead of showing it. "hey maple, add a note: …", "just
add a note: …" and "add a reminder note: …" go to the open estimate; "add a
note task" creates a task. A value containing "to" ("update the title to Send
estimate to Bob") stays the value. Tests sit beside each fix
(`test_work_item_edit_detectors.py`, `test_maple_estimate_targeting.py`,
`test_maple_work_item_context.py`, `test_estimate_edit_executor.py`,
`test_maple_work_item_edits.py`, `test_agent_helpers_finalize_result.py`,
`test_maple_assigned_value_routing.py`).

**2026-09-24 — review fixes to multi-turn estimate editing**

From the `/code-review` of the multi-turn work (findings #1–#56):
note, title and description text is never read as a pricing edit ("add a
note: drop the tax" files the note); a name containing "to" keeps its target
("rename the Back to Basics estimate to …", "update the Walk to Work contact
phone to …"); "create a note task" / "note estimate" are creates again;
"add X to the estimate as a new work item" is no longer a material add;
"the patio job" means the open estimate's patio work item when it has one; a
list pick ("the second one") only applies to the estimate it was listed for,
never over a named work item or estimate; "which estimate?" is answered only
by a bare code; a "yes" names exactly the work items it removes; out-of-range
percentages are explained ("Markup can be set between -100% and 500%").
Tests sit beside each fix (`test_work_item_edit_detectors.py`,
`test_maple_work_item_context.py`, `test_estimate_edit_executor.py`,
`test_maple_assigned_value_routing.py`, `test_maple_estimate_targeting.py`).

**2026-09-24 — a near-miss division gets a best guess**

`Change the division for Work Item #1 to Special Project` was refused with the
whole division list for one missing letter. Maple now proposes the closest
division and applies it on "yes" (§1.5 division rows). Found on the way: a
work-item edit the Estimate agent recognizes (division, markup, a line's
quantity) was sent to the "do it in the estimate editor" refusal before the
agent was asked — only the edit planner's hand-back rescued it, so with the
planner off every such edit was refused. `run_update_estimate` now asks the
agent first. Tests: `tests/test_division_best_guess.py`, the endpoint replay
in `tests/test_maple_description_after_remove.py`.

**2026-09-24 — a field's new value never picks the resource; stray replies are never priced**

Reported: after removing a work item, `Update the description to "A job for
Mr. X"` went to the Property agent ("What property fields should I
update?"), and the reply `The description` then appended an AI-generated
mowing work item to the estimate. Three fixes:

- **The new value is content.** `strip_assigned_value`
  (`agents/text_utils.py`) drops everything after the first `to`/`as` of a
  `set/change/update/edit/rename … to …` before the orchestrator looks for a
  domain — "job" in the value is a property hint, and "Mr. X" read as a
  person. A target named before the value (`the description of the 12 Oak St
  property to …`, `the status of E0042 to …`) still routes. Same rule
  `strip_dictated_payload` applies after a colon.
- **Only new work is priced.** An `update_estimate` message that no edit rule
  claims reaches AI generation only when `describes_new_work`
  (`agents/estimate/text_helpers.py`) says it asks for work — a leading
  add/price/include/"we need" verb with a scope. Anything else gets "what
  would you like to change?" (or the edit planner).
- **A "yes" confirms one removal, not the next.** `confirmed`,
  `orchestrator_intent` and `orchestrator_confidence` are per-turn and are no
  longer saved into the conversation; a saved `confirmed` let the next
  "remove work item …" skip its confirmation.

Gap noted: `set the description to …` (verb `set`, no estimate noun) is still
unrouted on the rule tier, as it was before; `update`/`change` work.
Tests: `tests/test_maple_description_after_remove.py` (endpoint replay of the
reported conversation), `tests/test_maple_assigned_value_routing.py`.

**2026-09-24 — a note with no target annotates the entity in play**

`Add a note that says: …` / `add a note: …` / `leave a note that …` name no
resource, so the orchestrator borrows the domain from the active anchor — and
read `add` as CREATE. With an estimate open, Maple started a brand-new
estimate instead of filing the note (same for property, contact and task). A
note always hangs off something that exists, so `is_note_add_request`
(`agents/orchestrator/intents.py`) now makes it an update of the anchored
entity, on both the rule and the LLM path. The same goes when the resource
IS named: `create a note for this estimate: …`, `make a note on E0053 that …`,
`new note for this quote: …` used to resolve to `create_estimate` (with any
anchor or none), and the equivalents to `create_property` / `create_contact`
/ `create_task`. The note must be the object of the leading verb, so
`create a new estimate with a note: …` stays a create. The estimate note
extractor drops the lead-in (`saying`, `that says`, `- `, `that`) and the
target (`for this estimate that says …`), and the work-item note detector
accepts `create`/`make`/`drop` and `… that …`. Tests:
`tests/test_maple_bare_note_routing.py`, `tests/test_maple_work_item_edits.py`.

**2026-09-24 — multi-turn estimate & work-item editing**

Maple keeps track of "this estimate" and "this work item" across turns, and
edits everything on a work item a user can edit by hand
(plan: `plans/2026-09-23-maple-estimate-multi-turn-editing.md`).

- **Which estimate:** opening an estimate in the portal makes it "this
  estimate" (most recent signal wins against Maple's own last action). A named
  code or title still beats it; names may now be lowercase or one word ("the
  smith job", "the Henderson proposal"), including a customer or property name.
  A name that matches nothing offers the open estimate as a yes/no.
  `bid`/`proposal` are estimate synonyms.
- **Which work item:** "this work item" / "it" follow the last work item
  resolved (by its stable id); "the second one" follows the list Maple just
  showed; "which work item?" menus and "what should I call it?" prompts resume
  the original request.
- **New edits (§1.5.5–§1.5.8, §1.11):** material quantity/price, activity
  effort/rate/role, markup/overhead/tax, gross margin (writes the markup that
  delivers it), work-item notes, pricing a new scope with AI. Set-total now
  back-calculates the markup like the Adjust pill. Labor burden and a
  material's cost stay refused.
- **Edit planner (🤖 planner):** requests no rule recognizes go to a
  worker-model planner that emits the same typed commands; see §1.11.
- Coverage matrix: new `estimate_work_item_edits` category (8/8 both tiers).

**2026-09-23 — estimate notes → Notes feed (Option C)**

Every estimate note phrasing (add / append / jot / FYI / remember / set /
replace) now files an estimate-level `Note` via `_handle_add_estimate_note`;
nothing writes `Estimate.notes`. Set/replace phrasings add rather than
overwrite. Notes ignore the Draft/Review lock; the lock tests now probe with
a description edit. Tests: `TestEstimateNotesGoToFeed`,
`test_estimate_notes_ignore_the_edit_lock`.

**No routing changed** — no phrasing was added, closed or reclassified, only
what a supported phrasing *does* server-side. §12.3's counts are unaffected.

**2026-09-17 — property and contact notes phrasings now create a real Note**

`notes` stays a supported field on both the Property and Contact agents
(§2.6, §3.6), but writing to it no longer sets a scalar — `Property.notes` and
`Contact.notes` were removed from the models. A note phrasing (on update, and
inline on create — `create a property at 123 Main St with notes: gate code
4411`) now inserts a real `Note` document via `services/notes.create_note_as`,
authored by the acting user and visible in the property/contact detail
panel's Notes feed. Legacy scalar text was migrated into the new collection
by `scripts/migrate_legacy_notes.py`.

**No routing changed** — no phrasing was added, closed or reclassified, only
what a supported phrasing *does* server-side. §12.3's counts are unaffected.

**2026-09-15 — the material markup is now COST, not profit**

Gross Margin no longer counts the spread between a material's catalog cost and
its price: a price *is* the material's cost basis. The consequence for
guide-answered questions is that Markup and Gross Margin now **are** a fixed
conversion of one another (`markup / (1 + markup)`) on any job where labor is
billed at its role's Rate — which corrects the 2026-09-14 entry below, and the
users' guide passages Maple answers from. Only a hand-raised activity rate
makes them differ. The dash now means an **activity** has no cost basis;
a material without one no longer suppresses the figure.

**No routing or refusal changed** — no phrasing was added, closed or
reclassified, and §12.3's counts are unaffected. Reporting a specific work
item's margin value stays refused for the same reason as before (the figure is
computed in the frontend and never stored).

**2026-09-14 — "Profit Margin" readout renamed to Gross Margin**

The figure formerly labeled "Profit Margin" is now **Gross Margin**, and shares
a row with **Markup %** — the same dollars stated against cost and against the
Selling Price. A new **Selling Price** row (subtotal + markup, pre-tax) sits
directly below, so the margin's denominator is on screen; it previously looked
miscalculated because the only total nearby included tax.

**Gross Margin % is now editable.** Only `profit_margin` is stored: typing a
target margin solves backwards for the markup that delivers it. (As shipped it
was *not* a unit conversion of the markup, because the solver counted the
profit inside material prices — superseded by the 2026-09-15 entry above.) The
margin dashes and goes un-editable when there is no cost basis to solve
against.

The maths is otherwise unchanged: tax was always excluded from both sides, and
overhead is still deducted (a deliberate departure from the textbook "gross").

**What this changes for Maple.** Two things, both in `text_helpers.py`:

- `"gross margin"` already reached the financial-field refusal, because the
  refused set is matched by substring and `"margin"` is inside it.
- `"markup"` did **not** — it shares no substring with `"margin"`, so
  "set the markup on the patio work item to 20%" fell through to the generic
  unknown-field fallback instead of the deliberate UI-pointer refusal. That is
  the label the UI actually shows on the editable field, so it was the likeliest
  phrasing of all. `"markup"` is now in `_WORK_ITEM_REFUSED_FIELDS`, and the
  refusal copy names markup rather than "profit margin".

Users still say "profit margin" — the old label remains in their vocabulary and
in the refused set. Guide-answered conceptual questions now cover both spellings
(`test_maple_help_coverage.py` §1.5.7).

**2026-09-13 — "profit margin" split into Markup and Profit Margin**

The work item's editable percentage is a **markup**, not a margin: it is
applied to the subtotal and added on top, so 10% yields a 9.09% margin. It is
now labeled **Markup %** everywhere in the UI. A separate read-only **Profit
Margin** appears under each Work Item Total, computed from stored line costs.

**What this changes for Maple.** Nothing routes differently and no refusal was
lifted — §1.5.7's write phrasings stay refused. What changed is the *answer*:
the users' guide previously defined the markup field as a margin, so Maple
would confidently give the wrong answer to "is my 10% markup the same as a 10%
margin?". The guide now carries a "Markup vs. Gross Margin" section (renamed
2026-09-14), and
conceptual questions about either are answered from it.

**Still refused: reporting a specific work item's margin value.** Maple cannot
read the computed figure; the value lives in the frontend calculation. A user
asking "what's the margin on the Patio work item?" is pointed at the work item
screen. Lifting this needs the formula ported to Python — tracked as a
follow-up, not done here.

**2026-08-27 — task ids became `T0042`: decimal, not Crockford (#504)**

Tasks and estimates carried two different readable-id schemes. Estimates use
`E` + a decimal counter; tasks used `T` + four Crockford Base32 characters
(`T4K7Q`). Tasks now match estimates.

**The displayed code is the count again.** Task ten used to display as `T000A`,
so "task ten" named nothing. It is `T0010` now.

**What this deleted.** Three pieces of machinery existed only because the body
carried letters:

- the **uppercase-only rule** on the bare form (lowercased, `tasks` is
  `T`+`ASKS`);
- the **"must contain a digit" rule** #505 added the day before to make bare
  lowercase safe;
- the **338,250-task edge**, past which an all-letter body would still have
  needed uppercase.

No English word contains a digit, so a decimal body cannot collide with prose
in either case, and all three are gone. `agents/task/text_helpers.py` went from
two target branches back to one.

**The spoken form now resolves** (`archive T 0 0 4 2`), for the first time.
Crockford drops I/L/O/U because they are *visually* confusable and does nothing
about B/D/E/G/P/T/V/Z, which is the speech-recognition set — so spoken ids were
never worth supporting on a letter-bearing body. `T-0042` rides the same
pattern.

**Existing ids were re-rendered, not renumbered.** `Company.next_task_seq` was
already a per-company counter and a Crockford body decodes straight back to it,
so every task kept its sequence number — `T000A` became `T0010`, the tenth task
either way. Gaps left by deleted tasks survive, the job is re-runnable, and the
counter was never written. `scripts/migrate_task_readable_ids_to_decimal.py`.

**No grace period:** `T4K7Q` no longer resolves at all.

**The id must be quoted in full**, everywhere it is read — the bare-id
shortcut, `GET /tasks?search=`, Maple's task list, and the portal search box.
**Estimates adopted the identical rule the same day**, so `E42` is refused too.
`T42` is refused rather than padded to `T0042`, because padding guesses between
`T0042`, `T0420` and `T4200`, and the id is the one field someone types when
they already know exactly which task they want. Decorations are still forgiven,
since `#T0042` and `T-0042` change presentation, not which task is named.

**Portal:** `portal/src/lib/taskCode.ts` mirrors the backend normalizer, and
task search matches the id **in full** rather than as a substring — with a
decimal body, "42" would otherwise hit `T0042`, `T0421` and `T1042` alike. The
server half is `services/task_search.py`, shared by the REST route and Maple's
task list so the two cannot drift.

Tests: `tests/test_readable_id.py`, `tests/test_task_code_pattern.py` (30
cases), `tests/test_migrate_task_readable_ids_to_decimal.py` (13),
`portal/tests/taskCode.test.ts` (11), plus the TasksPage search cases.

**2026-08-27 — every layer that reads a task id now shares one reader (#505)**

Task ids had four independent readers — the orchestrator's routing gate, the
intent grammar's `TASK_REFERENCE`, the update grammar's target, and the
resolver's own pair of regexes — and they had drifted. The consequences were
the kind that look like a product bug rather than a parser one:

- **`T-0042` was a silent dead end.** `normalize_task_readable_id` stripped the
  hyphen and would have resolved it, but no pattern accepted the form, so the
  message never reached the reader that could have handled it. It routed to
  `None` — no domain at all. Now ✅ at every layer.
- **The gate disagreed with the resolver on cued lowercase.** The resolver
  accepted `task t0042`; the gate did not, and neither did the update grammar,
  so `rename task t0042 to X` parsed its way to "What would you like to
  update?". Now ✅.

All five sites call `task_code_in_text` / `task_codes_in_text`
(`services/readable_id.py`), the same shape estimates use. The plural form
exists because the cue word can front an ordinary word that is also a valid id
(`task tasks` reads as `T`+`ASKS`), so the resolver must be able to walk past a
false positive to a real id later in the message.

**Bare lowercase now works too** (`archive t0042`). It had been refused
wholesale, but the real constraint is narrower than "lowercase": 728 words in
the system dictionary are structurally valid lowercase ids — `tasks` is
`T`+`ASKS`, `trees` is `T`+`REES`, and so are `tabby` and `tacca` — and **not
one of them contains a digit**. No task id lacks one either until sequence
338,250 renders as `TAAAA`. So the digit, not the capital letter, is what
separates an id from a word, and `t0042` reads while `trims` does not. An
all-letter body still resolves in uppercase.

**Superseded the next day:** the spoken form was refused here because a
Crockford body read aloud is unreliable regardless of the parser. #504 moved
the body to decimal, and `T 0 0 4 2` now resolves — see the entry above.

Tests: `tests/test_task_code_pattern.py` (22 cases across gate, both grammars
and the shared reader).

**2026-08-26 — estimate codes became `E0042`, and the id must be given in full (§1.2)**

`EST-4E73F7BB` was a uuid4 hex slice: unreadable aloud, unindexed, and not
unique. Estimates now carry `E` plus a per-company decimal counter, server-owned
and backfilled over the whole back catalogue. Decimal rather than the Crockford
Base32 behind task ids, because it is the *sequence number* that gets encoded —
Crockford would render the tenth estimate `E000A`, so "estimate ten" would name
nothing.

- **Every pattern that reads a code moved to `E[0-9]{4,7}`** — the two
  previously divergent `_ESTIMATE_CODE_PATTERN` definitions (the estimate
  agent's was case-sensitive, the orchestrator's was not) now derive from one
  shared fragment, along with `_ESTIMATE_REF_PATTERN` and ~25 inline
  alternatives. A decimal body cannot collide with prose, so none of the
  uppercase-only guarding the task patterns need is required here.
- **The spoken form is supported**: `archive E 0 0 4 2`, which is how
  speech-to-text renders a user reading the digits out one at a time. All four
  readers share `estimate_code_in_text`.
- **A bare "estimate 42" is deliberately NOT supported** 🛑 — matching
  `(?:estimate|quote)\s+#?\d+` would read a quantity as an identifier, so
  "estimate 3 hours of labor" would offer `E0003`. Requiring the prefix keeps
  every candidate an unambiguous statement of intent.
- **A well-formed code that doesn't exist now stops** rather than falling
  through to the fuzzy title match and the most-recent fallback. Tasks must
  fall through because `TRIMS` parses as a task id; an `E`-code cannot come
  from prose, so guessing a *different* estimate is worse than saying so. This
  is a deliberate divergence from the task resolver.
- **Search requires the full id.** `GET /estimates?search=` matches title and
  description as substrings, but the id as an anchored equality: over a decimal
  space "42" would hit E0042, E0421, E4200 and E1042 alike.
- Lookup by code is now an indexed point lookup on `(company, estimate_id)`.
  The estimate agent, the orchestrator's resolver and `cross_resource` all used
  to scan; `find_estimate_by_code` loaded the company's entire estimate
  collection and compared in Python.

Net effect on §12.3's counts: **none** — the code *format* changed, not the
coverage matrix, and `tests/test_maple_crud_coverage.py` is untouched at
163/174. Design: [`plans/2026-08-26-estimate-readable-ids.md`](plans/2026-08-26-estimate-readable-ids.md).
Tests: `test_estimate_code_pattern.py`, `test_estimate_readable_id.py`,
`test_backfill_estimate_readable_ids.py`, `test_readable_id.py`.


**2026-08-10 — assumed sizes became per work item, and adjustments target one of them (§1.3, §1.3.1)**

Generated totals were landing low. The activities Maple picks were fine; their *sizes and hours* were not.

- **One size no longer covers the whole request.** `resolve_assumptions` ran before the architect and did a single first-keyword-match over the raw message, so "build a paver patio **and** mow the lawn" stamped one size on both — a 5,000 sq ft patio. The architect now decomposes **first**, then each scope resolves its own size (`resolve_scope_area_assumption`): a stated size wins outright, else that scope's own history (queried with the scope text, not the whole message), else its own row in the curated table. Assumptions are tagged with their work item via the long-dormant `EstimateAssumption.scope` field.
- **The area question is gone.** `area_measurements` is no longer a required gathering detail — a single answer cannot size a multi-item request. Volunteered sizes are still extracted and honored; only the question disappeared.
- **The reply names each work item** — `• Paver Patio — Area: 300 sq ft` — because bare "Area:" lines are indistinguishable once there are several.
- **Adjustments target one work item.** "change the lawn to 8000 sq ft" resolves by name, then by position ("the second one"), then by being the only candidate, and **asks** when genuinely ambiguous. Only the targeted item rescales; previously *every* work item did, which was right for one estimate-wide assumption and wrong the moment sizes became per-item. Legacy `scope="estimate"` estimates keep whole-estimate rescaling.
- **Curated sizes recalibrated** against typical residential jobs (lawn 500 → 5,000 sq ft, patio 200 → 300, deck 150 → 320, beds 300 → 800, fence 100 → 150 ln ft, irrigation 500 → 5,000), with **sod split out of the lawn bucket** — a mow request no longer suggests sod as its material, and a sod job is sized as a section (2,000 sq ft) rather than the whole property. The old 500 sq ft lawn was a 22×22 patch; at a seeded mower rate it implied a three-minute mowing visit.
- **`is_discrete_item_job` widened.** Its locational-phrase pattern only stripped an area noun sitting immediately after the preposition, and did not recognize `in`/`from`/`within`/`at` — so "replace 3 shrubs **in the mulch bed**" read as area-based and was sized as an 800 sq ft bed. Pre-existing; it now costs more because effort is derived from size.
- **History means won work.** Work-item summaries index on **Won/Scheduled/Completed** instead of Sent/Approved (`embed_won_estimate`), are removed when an estimate leaves that lane, and are filtered on the estimate's *current* status at read time. Retrieval also prefers the most **recent** qualifying match rather than the highest similarity score.

Tests: `test_scope_assumptions.py`, `test_assumption_adjustment_targeting.py`, `test_assumed_job_sizes.py`, `test_history_eligibility.py`, `test_history_recency.py`, plus updates across the gathering/applicability/grounding suites.

**2026-08-07 — tasks gained a readable ID, and their title became a derived mirror of the note (§7)**

Two changes to how a task is referred to, both driven by the portal's task dialog losing its Title field.

- **New: `show me task T0042`.** Every task now carries a short, human-quotable id — `T` plus four Crockford Base32 characters, sequential per company (`services/readable_id.py`). It resolves as **step 1a** of `agents/task/resolver.py`, ahead of the positional step, because an explicit id should beat "the second one". ~~Two shapes are accepted: the bare form is **uppercase-only** (every capitalized T-word is valid Crockford — `TRIMS` parses as `T`+`RIMS`), while a lowercase id needs a `task`/`#` lead-in.~~ **Superseded 2026-08-27 (#504):** the body is decimal, so one case-insensitive shape covers everything. A **DB miss falls through** to the title/fuzzy steps rather than swallowing the turn. The id also joins the search `$or` in both `GET /tasks?search=` and the agent's task list, and leads the `- ID:` line of the task-details block.
- **Removed: rename-by-title as a direct title write.** A task's title is now derived from the first line of its description on every save, so `changes = {"title": …}` would be silently reverted by the user's next portal edit. `rename the {task} task to {new}` **still works** and is still supported — it now rewrites the note's first line (`services/task_title.py::retitle_note`), which is the thing the title is read from. Chat-created tasks fold a nominated title into the note the same way, so `create a task called Fix the fence gate` stores that text as the note and derives the same title back out.

- **New: acting on a task by id, not just finding one.** Resolution alone wasn't enough — the update phrasings parse their target with `_TARGET_OR_PRONOUN`, which accepted only `"{title} task"`, a positional, or a pronoun. So `rename task T0042 to X` resolved the id and then still asked "What would you like to update?". A readable-id branch now leads that alternation, covering `T0042`, `task T0042` and `#T0042` across **every** sub-op that shares it: rename, set-description, add-notes, mark/move/set status, assign, and archive. `the T0042 task` already worked (the id matched as a title fragment) and still does. ~~The id branch is deliberately **case-sensitive** via `(?-i:…)`: lowercased, `tasks` is itself a valid Crockford id (`T`+`ASKS`), so a case-insensitive target would hijack `archive the tasks` and every other plural phrasing.~~ **Superseded 2026-08-27 (#504):** a decimal body can't collide with prose, so the branch is case-insensitive and the two-branch target collapsed back to one.

- **New: the ORCHESTRATOR now routes an id-only message.** Making the agent act on an id wasn't enough — an id-only message ("archive T0042") carried no domain signal at all, so the rule tier scored `unknown` and never reached the Task agent. Three places assumed the literal word: the entity-signal domain supplement, the status/assign/archive sub-op block, and the notes-update + convert detectors. All now accept a readable id, plus a bare id on its own (`T0042`, `#T0042`) resolves to `get_task` — unlike a bare title, an id names exactly one thing, so it needs no verb. **23 id-only phrasings** now route at the rule tier that previously did not. The worst of them was `add to T0042: …`, which resolved to **`create_task`** and would have silently made a second task — "add" is a create hint, and the notes-update detector that exists to prevent exactly that required `\btask\b`.

- **New: a follow-up that names only the FIELD.** Right after a create, "Update the description to say: …" is the natural next turn — the user has just been shown the task and won't name it again. Every field-update shape required an explicit target (`… of the {title} task`, or a pronoun), so a target-less one fell through to "What would you like to update on the task?" *even though the active-task anchor was sitting right there*. A new target-less shape covers `set|change|update|edit|modify the {description|notes|due date|title|name} to [say|read|be] {value}`, with an empty target hint — the same thing a pronoun normalizes to, which routes the resolver through the active task and still asks when there is no anchor. `notes` is now a `description` alias in `_FIELD_CANONICAL`.

- **Fixed: "create a task for me to X" named the task "me to X".** The create-content extractor treats `for` as command preamble, stranding the first-person object at the front of the note — and since the title now mirrors the note's first line verbatim, that text became the task's visible name. A leading `me|myself|us|ourselves + to` is now stripped. Deliberately first-person only: `for John to call the supplier` names WHO, and dropping that would discard information the note is carrying.

- **New: "Add to the Task T0042 - {content}" appends instead of asking.** Two things blocked it. The id target accepted `task T0042` but not `the task T0042`, so the determiner people actually type broke the match; and the bare-notes shape required a separator (`:` / `-` / `to|about|that`) to mark where content begins. With an explicit id there is nothing to disambiguate — notes are the only free-text field a task has — so a by-id sibling of the bare-notes pattern drops the separator requirement. The separator guard stays for every other target shape, so `add a photo to the task` is still not claimed. **Mirrored on both sides** (`_ADD_BARE_NOTES_BY_CODE_RE` in `agents/task/text_helpers.py` and the matching entry in `_TASK_NOTES_UPDATE_RES`): without the orchestrator half, the message keeps "add"'s CREATE hint and makes a *second* task.

- **Copy: Maple no longer offers to change the "title".** The update clarify question read *"I can change the title, description, due date, status, or assignee"* — but there is no Title field to change, so it pointed the user at a control that does not exist. It now lists description / due date / status / assignee / archive. Renaming still works and still rewrites the note's first line; it just isn't advertised as a field, because it isn't one. Two more places carried the same wrong model and were corrected: the task-details block listed a `- Title:` line that rendered *identically* to the `- Description:` line below it (removed), and the disambiguation prompt said "Reply with the number or the title" (now "the task's name").

- **Fixed: a multi-line note broke the details bullet list.** The details block is markdown, one field per bullet, and a note is routinely multi-line now that it is the task's whole content. The second line landed at column 0, which markdown reads as the end of the list item — so every field below the description fell out of the list. Continuation lines are now indented two spaces to stay inside the bullet.

- **Fixed: "update the task description: {value}".** Three separate things blocked the most ordinary phrasing there is. The target-less field shape required the word **"to"** before the value, so a `:` or `-` separator never matched; it allowed no **domain word** between the determiner and the field, so "the **task** description" broke it; and — the subtle one — with an empty target the resolver falls back to `extract_reference_hint`, which reads `task <X>` as *"the task named X"*, so the hint became `"description: Buy mowers"` and Maple answered *"I couldn't find a task matching that"*. The shape now accepts `to say/read/be`, plain `to`, or a bare `:` / `-`, with an optional `task` before the field name; and `extract_reference_hint` returns "" for a target-less field update, because everything after the field name is the VALUE, not a title. The targeted shape (`… of the fence task to X`) does not match the target-less pattern, so it keeps its priority and still resolves by title.

- **Systematic sweep of the Task update surface (2026-08-08).** After three rounds of single-shape bug reports, the whole grid was enumerated instead: **2,475 target-less phrasings** (verb x determiner x domain word x field x separator) and **111 operation x target-form** routing cases (bare id / `task <id>` / `the task <id>` / `#<id>` / by title / pronoun). Both now live as a permanent regression matrix, `tests/test_maple_task_phrasing_matrix.py`. Findings:
  - **825 of 2,475 target-less phrasings failed, and every one was `status` or `assignee`** — exactly the two fields the clarify question offers, neither of which could be set without naming the task again. Now routed through the status/assign detectors (not the field shape: `_FIELD_CANONICAL` has no `status` key and the update handler treats an unrecognized field as a *description* edit, so widening the field shape would have written "Done" into the note). **0 of 2,475 fail now.**
  - **`due date` was in no orchestrator field-keyword list at all**, so `set the due date of {anything} to {date}` matched no update shape for *any* domain or target form. Added as `ORCHESTRATOR_ROUTING_FIELD_KEYWORDS` — separate from `ORCHESTRATOR_EXTRA_FIELD_KEYWORDS` because that tuple holds *raw* regex fragments and the builder escapes what it is given (folding them together produced a pattern matching the literal text `due\s*date`).

- **Fixed: "archive it" (and every sub-op verb with a pronoun).** The sub-op verbs — mark / move / assign / archive / convert — are deliberately not ACTION_HINTS, and the sub-op block required the message to NAME a task: the literal word or a readable id. A pronoun is neither, so `archive it` one turn after Maple showed you a task did not merely miss — it fell through to the bare-entity residual heuristic and resolved to the **Material agent**. The block now also accepts a pronoun **when a task is the active entity**. The gate matters: `_anchored_domain` reads the `active_entity_domain` recency marker *only*, never the static priority fallback, because anchors are not cleared when the user moves on — the fallback would let a task from twenty turns ago claim `archive it` after the user had switched to an estimate. Closing this meant threading the anchor domain through `_classify_with_rules` → `_match_unambiguous_command` → `_classify_specific_phrasings`, which previously took only the message. Tests cover the anchor deciding correctly (an estimate anchor must NOT route to task), no anchor at all, and an explicitly named task still winning over the anchor.

- **Fixed: the last three pronoun shapes.** Two different causes. `set the description of it to X` / `set the due date of it to X` reached the SHARED field-of pattern, which matched fine with `name="it"` — but `_domain_from_field_or_name` had no rung for a pronoun, so no domain resolved. It now returns the anchored domain for a pronoun name (gated on the anchor: a pronoun alone carries no domain, and the shape heuristics below it would have picked one out of the air). Separately, `append to it: X` failed because **`append` was not an ACTION_HINT at all** — which is why `add to it` worked (`add` is a CREATE hint, then redirected by the anaphoric-add guard) and `append to it` did not. Both fixes are domain-agnostic by construction: the same phrasings now resolve against an active *estimate* or *material* too, which is the correct behavior and is covered by tests asserting a different anchor is respected. **Every pronoun shape in the matrix now routes.**

**Known rule-tier gaps** (tracked as strict entries in `tests/test_maple_task_phrasing_matrix.py::KNOWN_ROUTING_GAPS`, so the suite fails if one silently changes in either direction): `open {task}` and `give {task} to {person}` (need global action hints — `open` collides with the estimate *status* word); `what's on {task}`; and a `#`-prefixed id in the field-of shape (`set the description of #T0042 to X`) — the shared pattern's `<name>` group must start with `\w`, and widening it reaches every domain, while the bare and `task `-prefixed forms both work and `#` IS accepted by the sub-op shapes. These score `unknown` on the rule tier and fall through to the LLM tier, which generally classifies them correctly; they are a pre-existing Task-phrasing gap rather than a regression, and closing them means adding action hints (`open`, `give`) or a due-date sub-op shape that would affect every domain.

Net effect on §12.3's counts: none — neither is a coverage-matrix category. Tests: `tests/test_task_resolver.py` (id resolution, fall-through, company scoping), `tests/test_maple_task_crud.py` (rename preserves the rest of the note; details block carries the id), `tests/test_readable_id.py` / `tests/test_task_title.py` (pure helpers).

**2026-07-31 (later) — divisions are matched against the company's own list, description-first (§1.5.2)**

Follow-up to the entry below, after the seeded division descriptions were rewritten from terse tag-lists into real coverage prose. Divisions are per-company rows a user can rename, add, and describe, so "which division does this work item belong to?" is a match against *their* list — and what a custom division covers is only knowable from the description they wrote. One phrasing closes (`set the division of {WI} to {custom division}`), one new gap opens (the same request without the word "division"); §12.3's auto-generated counts are unaffected — none of these are coverage-matrix cases.

- **Both LLM stages now classify against the company's divisions with their descriptions**, and return a `division_confidence` alongside the label. Below a floor the label is dropped and the work-item text decides — a bare label gives the model no way to say "none of these fit", so it picks one anyway.
- **The lexical fallback scores the company's own divisions**, in tiers: their description beats the division name, which beats the built-in vocabulary. Before this, that vocabulary was hardcoded to the seven seeded divisions — a company running its own set could only ever be scored against names it had deleted, so *every* fallback returned `Unassigned`.
- **Two regressions were caught by scoring against the real seed rather than test fixtures.** The built-in `sod`/`shrub` keywords out-voted a description that explicitly handed installs to Design/Build; and the boilerplate every seeded description ends with ("Usually sold as per-event, per-push, or seasonal contracts…") scored as domain vocabulary, so "seasonal service contract" landed on Snow & Ice. Both now covered by `tests/test_estimate_division_seed_catalog.py`, which scores `data/default_divisions.csv` as shipped.
- **Chat-side division updates validate against the company's live divisions** instead of the `EstimateDivision` enum, canonicalize casing and punctuation to the stored spelling, and list the company's own divisions when refusing.
- **The prompt's fallback description list is read from the seed CSV**, not restated in the prompt module — a hand-maintained copy had already drifted from it on all seven entries.
- Tests: `test_estimate_division_seed_catalog.py`, `test_estimate_division_inference.py`, `test_estimate_division_classification.py`, `test_maple_work_item_division_update.py`.

**2026-07-31 — a paver patio was filed under Turf & Plant Care (§1.5.2)**

Reported live: a generated work item reading "Assumes a 500 sq ft standard concrete-paver patio with a compacted 4-inch aggregate base and 1-inch bedding sand." carried the **Turf & Plant Care** division. It should have been Design/Build. No phrasing changed here — this is how divisions get assigned when Maple *generates* an estimate, so the §12.3 counts are untouched.

- **Rule 4g was dead prompt text.** The generation prompt has always listed the seven divisions and told the model to classify each job item — but `ExtractedJobItem` had no `division` field, so `with_structured_output(..., method="function_calling")` never offered the property and `model_dump()` discarded any answer. Same for `ArchitectScope`, which is the stage that actually decides the work-item split in the research pipeline. Every division on every Maple-generated estimate came from the keyword table alone.
- **That table had no hardscape vocabulary at all.** `patio`, `paver`, `walkway`, `driveway`, `retaining wall`, `deck` — none of them were keywords, so hardscape scopes fell through to `Unassigned`. It also matched whole words only (`shrub` matched, `shrubs` didn't) and returned the **first** division whose keyword appeared in dict order, so "Seasonal cleanup and tree pruning" scored Maintenance before Tree Care ever got a look.
- **The architect now classifies each scope**, and the division rides scope → research deliverable → job item. A high-confidence vector match to an approved past estimate donates *that* estimate's division instead — the strongest signal available, since a human reviewed it. New rule 4h/9 tells both models to classify on the primary scope, not incidental mentions ("a paver patio bordering a lawn is a build scope, not lawn care"), and the JSON example no longer hardcodes `Turf & Plant Care` as the sole worked example.
- **Both prompts now render the company's own division names**, not the seeded seven — divisions are per-company editable rows, so a company that renamed one could never be matched against it. Labels that still match a seeded division keep that division's scope examples; renamed ones render bare. Names are sanitized and brace-escaped like the unit allow-list.
- **Whatever the model returns is re-anchored** (`apply_division_names`): a match is canonicalized to the company's stored spelling, and a hallucinated or deleted division falls back to keyword inference rather than persisting.
- **The keyword fallback was rebuilt** — hardscape vocabulary, light stemming for plurals/gerunds, and weighted scoring (strong domain nouns vs. supporting terms) instead of first-match-wins.
- Tests: `tests/test_estimate_division_inference.py`, `tests/test_estimate_division_classification.py`.

**2026-07-30 — "show me the fourth one" answered with the first (§10.5)**

Reported live: Maple listed eight tasks, and every positional follow-up came back with row one. Nothing recorded which rows had been rendered, so "the fourth one" wasn't a reference at all — the message carried no title, id, or date, and resolution fell through to the recency fallback, which *is* row one (lists are sorted most-recently-updated first). §10.4's ordinal matcher didn't help: it is anchored at both ends because it reads replies to a numbered *menu*, and this pick arrives inside a sentence.

- **Lists now remember what they rendered.** `record_listed_items` / `format_and_record_list_response` (`agents/text_utils.py`) store the `(id, label)` rows under `last_listed_items`; one slice feeds both the renderer and the record, so a truncated page can't leave positions pointing at rows the user never saw. Wired into all seven list-producing resources (Task, Property, Contact, Material, People, Template, Estimate); estimates record their E-codes.
- **`match_positional_reference`** extends the menu matcher to embedded ordinals, tail-anchored with a small clause-boundary set so `rename the second one to X` resolves while `put on the first coat of paint` doesn't.
- **Routing was the other half.** A positional follow-up names no domain: the rule classifier read `show me the fourth one` as a *material* lookup and bare `the second one` as `unknown`. `_match_listed_positional_follow_up` routes it to the resource that was listed (verb picks read/update/delete) and stands down for domain-naming messages and armed `pending_*` flows, which §10.4 already owns.
- **Out-of-range re-asks** ("I only listed 3 tasks — which one did you mean?") instead of falling through — falling through is what produced the wrong row. A row deleted between turns re-asks in the user's words rather than quoting back the internal id it picked.
- **Estimate line items are carved out.** `#2` names a work item as readily as a listed row, so with an estimate list on screen `delete work item #2` retargeted a *different* estimate. `resolve_listed_reference` stands down for work item / job item / scope / line item — caught in review, not in the field.
- **Sub-op targets had to learn the shape too.** Routing `mark the first one as done` to `update_task` only helped once `agents/task/text_helpers.py::_TARGET_OR_PRONOUN` accepted a positional target; until then the detectors knew "the {title} task" and pronouns only, and these phrasings asked "what would you like to update?".
- Found in passing and fixed: the Task list page claimed "the 20 most recently updated" while the renderer's 10-row default silently cut the list at 10.
- Tests: `tests/test_maple_listed_positional_reference.py`, `tests/test_text_utils.py::TestMatchPositionalReference` / `::TestListedItemsContext`.

**2026-07-30 — "add to the tasks to …" made nothing, and "the first one" picked nothing (§7.6.1, §10.4)**

Two reports from one live session, unrelated in cause:

- **`Add to the tasks to buy more milk.` asked "What should the task be called?"** It resolved to `create_task`, and create then found neither a title nor content, so it had to ask. Two gaps, present in the classifier detector (`is_task_notes_update_request`) *and* its Task-agent twin (`_ADD_BARE_NOTES_RE`) — these are one contract and both were missing the same things: `task\b` never matched the **plural**, and a **colon was the only separator** that could mark the trailing content. `to` / `about` / `that` now count as separators and the noun may be plural. The colon was never what protected `add a photo to the task` — the verb must be followed immediately by to/on/onto, and that guard is untouched. Deliberately still unclaimed: `add to my task **list**: buy milk`, which is create-shaped, not note-shaped.
- **`The first one.` against a numbered property list** was handed to free-text resolution and answered "I couldn't find a property matching 'The first one.'". `_ORDINAL_PATTERN` accepted digits only. Word ordinals now live in one shared helper (`agents/text_utils.py::match_ordinal_reference`: `first`–`tenth`, `1st`–`10th`, `last`), used by both the property-link and Task confirmation flows — the latter previously stopped at `fifth` and had no `last`. Anchored at both ends, so `First Street` is still an address. The same report also exposed a **placeholder leak**: with candidates armed there is no pinned property, so the failure branch rendered "I believe you are looking for 'that property'" — it now re-shows the list.
- Tests: `tests/test_maple_task_operations.py::TestAddToTheTasksAppends` (both layers pinned together), `tests/test_maple_task_routing.py` (intent lands on `update_task`), `tests/test_maple_task_context.py` (full create→append round trip), `tests/test_agent_helpers_pending_property_link.py::TestWordOrdinalReply` / `::TestUnresolvableReplyAgainstArmedCandidates`, `tests/test_text_utils.py::TestMatchOrdinalReference`.

**2026-07-30 — "rename it to …" created an estimate (§7.6, §7.11)**
- **`rename` was never an action hint.** `ACTION_HINTS["update"]` listed update/edit/change/modify only, so every rename phrasing scored `unknown` on the rule tier. The LLM classified it correctly (verified live at 0.99), but the demotion guard in `_prefer_explicit_rule_match` reads an action-less, domain-less message as a *follow-up answer*: it discarded the LLM's `update_task` and rebuilt an intent from history — action from the previous turn (`create`) plus the highest-priority active anchor. Reproduced end to end: with a stale `active_estimate_code`, "rename it to {title}" **created an estimate**; with only task anchors it created a **duplicate task**. `rename` and `retitle` are now update hints, which also makes `rename the {task} task to {new}` resolve deterministically at the rule tier.
- **Anaphora anchors are now chosen by recency, not by a fixed ranking.** `_resolve_domain_from_history` walked a static list where `task` trailed `estimate`, and anchors are never cleared when the user moves on — so an estimate opened twenty turns earlier captured every later pronoun follow-up on a task. `finalize_orchestrate_result` now also writes `active_entity_domain` naming the freshest anchor, and that wins whenever its own anchor is still present (a delete pops the anchor but not the marker, so the static list remains the fallback — and still applies to conversations persisted before the marker existed).
- **A pronoun-targeted edit's payload is a value, not a domain signal.** `_supplement_domain_from_entity_signals` mined the text after "rename it to …" for entity shapes, so a Capitalized new title tripped the person-name heuristic and produced `update_contact` — "update it to Prune the Hinoki by the Putting Green" edited a contact. New `is_pronoun_targeted_edit` guard suppresses the guess for these messages (same rule `is_anaphoric_add_request` already enforced for "add … to it"); with no anchor they now ask instead of guessing.
- Tests: `tests/test_maple_task_routing.py` (T5 rename routing, T6 pronoun-edit detector), `tests/test_maple_task_context.py` (anchor recency + marker write). Existing task-rename tests injected `orchestrator_intent="update_task"` and so never exercised routing — that hole is what let all three bugs ship.

**2026-07-30 — where "rename it to …" actually LANDS, per resource (§1.10, §7.6)**

Routing the pronoun rename correctly only mattered if the receiving agent could complete it. Audited all five; two could not, and one had no handler at all:

| Resource | Before | Now |
|---|---|---|
| Task | ✅ renamed via the active-task anchor | unchanged |
| **Estimate** | ❌ no title handler anywhere — fell through to the capability-list clarification | ✅ `_handle_update_estimate_title`, edit-lock enforced (§1.10) |
| **Contact** | ❌ classifier puts the new name in `full_name`, the same slot used as the lookup key — searched for a contact that doesn't exist, and **fuzzy-matched a different real contact** ("Robert Smith" → "Bob Smith"), i.e. it could edit the wrong person | ✅ anchor wins |
| **Property** | ❌ new name landed in `fields`, which fed the lookup query; the fuzzy fallback could return an unrelated property | ✅ anchor wins |
| Material / People | ✅ already worked — the pre-dispatch guard promotes the active id because their classifiers leave `full_name` empty | hardened + pinned by tests |

The shared signal is `is_pronoun_targeted_edit` (`agents/text_utils.py`, alongside the other cross-agent Maple detectors), surfaced to each domain agent as `parsed["target_is_anaphoric"]`: when a pronoun names the target, anything name-shaped in the payload is the NEW value and must never be used as a lookup key. It reuses `strip_dictated_payload`, so a dictated body (`add a note to it: please update it to reflect …`) does not trip it.

**2026-07-28 — Property linking after estimate creation actually resolves (§1.6, §10.4)**
- **The identifier handed to the property lookup was mangled.** `_PROPERTY_NAME_PATTERN` captured *everything* after the word "property", so the follow-up's synthetic message `set the property of this estimate to Primavera - 153 Asharoken Ave` searched for the literal string *"of this estimate to Primavera - 153 Asharoken Ave"* and reported `I couldn't find a property matching "of this estimate to …"`. The pattern now skips an `of|on|for [this|that|the|my] estimate|quote|bid|proposal … to|with|is` preamble before capturing. This also fixes the directly-typed `set the property of estimate {Name} to {property}` and `the property for this quote is {property}` phrasings, whose ✅ rows were only ever verified at the *routing* tier — the extraction underneath them was broken.
- **A failed lookup no longer ends the flow.** The collect-value stage popped the pending record *before* delegating and never restored it, so an unresolved property answer dropped the user out of the follow-up entirely: the next message (usually just the property name again) went to intent classification and came back as *"Sure, I'll help you create an estimate!"* mid-link. `handle_pending_optional_follow_up` now re-arms the record whenever the delegated agent asks a clarifying question, matching the legacy `pending_estimate_follow_up` behavior. Because the slot can now stay open, the collect-value stage gained the pivot escape hatch the confirm stage already had (with the field's own domain exempted, so "the Downtown property" stays a *value*, not a pivot).
- **Composite "{name} - {street}" answers resolve.** `_resolve_property_address` only matched when the typed text was a substring of `street`/`name`; it now falls back to the reverse direction when the strict tier finds nothing — parity with `find_property_by_name_or_address`. Tiered, so every existing single-match resolution is unchanged.
- Tests: `tests/test_maple_estimate_field_edits.py::TestPropertyIdentifierExtraction`, `::TestPropertyResolutionCompositeLabel`, `::TestFollowUpSurvivesUnresolvedValue`.

**2026-07-28 (b) — Fuzzy property matching on the estimate link (§1.6, §10.4)**
- **Near-misses now resolve.** `_resolve_property_address` gained a third, fallback-only tier using the repo's shared difflib matcher (`agents/fuzzy_utils.fuzzy_best_matches`, threshold 0.65) scoring name / street / **name+street** / full address. Typos (`primavara`, `153 Ashroken Ave`), re-wordings (`Primavera, 153 Asharoken Avenue`) and composite labels resolve; noise (`Bogus Place`, `the property`) still doesn't. The tier fires only where the two substring tiers found nothing, so no existing resolution changed.
- **A fuzzy match on a WRITE confirms first**, per the house rule for fuzzy + mutation. New `pending_property_link_confirmation` record pins the resolved property id so the confirming turn links directly rather than re-running the ambiguous lookup. A corrected name ("no, I meant Maple Ridge") is re-resolved *inside* the handler — handing a bare property name back to the classifier is what produced the "Sure, I'll help you create an estimate!" bug.
- **A fuzzy match on a READ discloses instead of gating** — "Estimates for 'Primavera':".
- **Two defects the review loop caught before this shipped:** the confirmation handler passed a raw `str` where Beanie needed a `PydanticObjectId` for the company-scoped lookup, so corrections silently matched nothing (fixed — the handler now converts to `PydanticObjectId` before calling `_resolve_property_address`, mirroring `agents/estimate/crud_handlers.py`); and `"estimates for {address} property"` satisfies both the address extractor and the cross-resource `filter_by`, and the latter used to re-resolve and clobber the former's already-correct property label (fixed — the cross-resource lookup is now skipped once the address block has already resolved the property).
- **Numbered disambiguation can now be answered by number.** When a fuzzy near-tie offers `(1) … (2) …`, replying `2` / `(2)` / `#2` / `option 2` / `number 2` selects that candidate. The candidate ids are persisted on the pending record, so the choice is resolved against the list actually shown rather than re-parsed as free text — previously `"2"` substring-matched the street `12 Oak Rd` and silently linked the wrong property. Ordinals are capped at two digits so a bare street number (`153`) still resolves as an address, and a reply under three characters is never treated as a property identifier.
- Tests: `tests/test_agent_helpers_pending_property_link.py`, and `TestPropertyFuzzyResolution` / `TestFuzzyLinkConfirmation` / `TestFuzzyConfirmNotEatenByFollowUp` / `TestFuzzyLinkEndToEnd` in `tests/test_maple_estimate_field_edits.py`.

**2026-07-26 — Assume instead of ask: estimates complete on partial info + adjustable assumptions (new §1.3.1)**
- **Generation no longer blocks on missing area/materials.** Only an unknowable *work type* still asks a question; every other missing detail is assumed and generation runs immediately. Assumed values come from, in priority order: **company history** (median size parsed from similar past work items via the same vector search the pipeline reuses — `infer_area_from_history`), the **curated per-work-type defaults table** (`agents/estimate/assumption_defaults.py` — lawn 500 sq ft, patio 200 sq ft, driveway 600 sq ft, …), then the **architect LLM** (which now reports any value it invents in a structured `assumptions` array instead of silently guessing).
- **Assumptions are structured + surfaced.** New `Estimate.assumptions` field (`EstimateAssumption`: key/label/value/unit/display/source). The creation reply appends: *"I made a few assumptions — let me know if you'd like to adjust any: • Area: 500 sq ft (average lawn) • Materials: standard sod"*.
- **Follow-up adjustments rescale deterministically.** "change the lawn to be 800 sq ft instead" resolves the estimate (active context or explicit code/title), computes factor = 800/500, scales every work item's quantities + activity effort (`scale_job_item`), recomputes sub/grand totals, updates the stored assumption (so later adjustments compound), and confirms with the new total. Manual work-item total overrides are preserved proportionally. "assume premium pavers instead" swaps the assumed material's catalog match on the matching lines and re-prices — no LLM regeneration in either path. See §1.3.1.
- The multi-question gathering loop degenerates to at most the work-type question; the mid-gathering per-item recheck (`_maybe_skip_area_question`) and its extra `assess_sufficiency` LLM call are gone — the deterministic `is_discrete_item_job` guard alone decides per-item vs area-based (per-item jobs get **no** invented area). Tests: +75 across `test_assumption_defaults`, `test_estimate_assumption_adjustment`, delegate/gathering suites; coverage matrix +4 phrasings (`assumption_adjustment` category).

**2026-07-26 — Task Agent code-review fixes (9 of 12; 3 deferred)**
- **ReDoS in the notes detectors (HIGH).** Every scanning segment in `agents/task/text_helpers.py` and the orchestrator's task detectors is now length-bounded (`[^.?!]{0,80}?`, an 80-char target body). "add to it " ×600 took **5.5s** before — nested unbounded lazy quantifiers, on an unbounded input field, holding the GIL and stalling the whole worker. Now ~1ms, pinned by a timing suite. `OrchestratorAgentRequest.message` also gained `max_length=2000` (matching the public Maple ask limit) as defence in depth.
- **An awaited value is content, not intent (HIGH).** A note typed at the "what should the new description be?" prompt was **silently discarded** when its text parsed as a command, and the classifier ran that command instead (verified: "create a new estimate for Bob next week" → note lost, estimate created). Root cause was in the ROUTER, not the agent: `pending_intents` was only consulted when classification returned `unknown`. New `_get_awaiting_value_match` now **outranks** classification whenever a pending intent carries `awaiting_value_for`. The agent-side escape narrowed from any fresh intent to explicit cancel/no, and now acknowledges ("No problem — I've left the task as it is.") instead of silently re-asking.
- **Filters pushed into Mongo (HIGH).** The resolver and list handler loaded the company's ENTIRE task collection and filtered in Python — fine under the free plan's 50-task cap, unbounded on paid plans. Search/assignee/date-window/property filters are now query conditions (all indexed), counts use `count()` instead of materializing rows, lists cap at 20 and report the true total ("that's the 20 most recently updated of 137"), and the one un-queryable step (fuzzy title) caps candidates at 200, most-recently-updated first.
- **§7.6.1.1 fallback:** stripping the dictated payload could leave a message with no domain at all, so `notes: the estimate needs review` became unroutable. The full text is now reconsidered as a last resort — **except** for anaphoric adds, where "it" already names the target (without that gate the fallback re-broke the "Add to it … estimate" fix).
- Also: `except Exception` around task fetches narrowed to a shared `to_object_id` helper so a DB outage no longer reads as "I couldn't find that task"; candidate matching does one `$in` query instead of up to five sequential fetches; `WEEKDAY_NAMES` de-duplicated into `agents/text_utils.py`; `_resolve_create_title` no longer mutates the context it's handed; a comment re-attached to the dict it documents.
- Deferred by Simon (logged in [`code-review-followups.md`](code-review-followups.md)): long functions, the 1,560-line ops test file, and a direct unit test for `is_anaphoric_add_request`.

**2026-07-25 — "Add the following notes to the Task" appends to the remembered task (new §7.6.1)**
- **Routing fix (was a silent duplicate-create):** `Add the following notes to the Task: …` classified as `create_task` — `add` is a CREATE action hint — so it made a *second* task instead of annotating the active one. New `is_task_notes_update_request` in `intents.py`, wired into `_classify_specific_phrasings` ahead of the generic resolver, with an explicit create-shape exclusion so `add a task with the notes: …` still creates.
- **Append semantics** (`detect_notes_update` → `_handle_task_notes_update`): existing notes are preserved and blank-line separated, matching the estimate-notes precedent; appending onto empty notes is a clean set; only `replace`/`overwrite`/`set … with` overwrites. `add a description to …` now appends too (previously overwrote).
- **Resolver fix:** `extract_reference_hint` checked the `{name} task` shape before the bare-anaphora guard, so "add the following notes to **the task**" yielded the title hint *"following notes to the"* and resolved to nothing. The anaphora guard now runs first.
- **Field-word-free form** (smoke test): `Add to the Task: {text}` carries no "notes"/"description" word, so the first pass still fell through to `create_task`. Now recognized on the strength of the colon — required, so `add a photo to the task` stays unclaimed.
- Active-task memory itself already worked (`finalize_result` writes `active_task_id/_name` for every create/get/update); it's now covered end-to-end by a create → "add the following notes to the Task" round-trip test. Tests: +33.

**2026-07-25 — Dictated payloads no longer hijack routing (new §7.6.1.1) — cross-cutting**
- *"Add to it the following: bring a lawn mower to his place. Need to estimate the lawn size."* routed to **create_estimate**: the classifier scanned the whole message, so "estimate" in the user's dictated content outvoted the leading "add to it". Worse, `_resolve_intent_with_history` bails whenever *any* domain word is present, so the payload also blocked anaphora from rescuing it.
- **The first intent wins.** New `strip_dictated_payload` returns the command head for `<command>: <payload>` shapes whose head carries an add/notes/following cue; the three generic resolvers (`_match_unambiguous_command`, `_classify_via_action_domain`, `_resolve_intent_with_history`) now classify on that head. Task-specific rules still see the full text (some key off the colon), and a head that names its own domain (`create an estimate for: …`) is untouched. **This is cross-cutting — it applies to every domain, not just tasks.**
- **Anaphoric adds are updates**: `is_anaphoric_add_request` rewrites "add … to it/this/that" away from the CREATE reading of "add" — you can't create something you're pointing at. Domain still comes from the active-entity anchor, so the same sentence appends to an active estimate when that's the anchor.
- Agent-side: `add to it the following: {text}` (field cue trailing the target) now parses as a notes append. Tests: +11.

**2026-07-25 — Task update was a dead end: field-then-value flow added (new §7.6.2) + target-less notes**
- **The loop in the smoke test:** `update the task` → "What would you like to update?" → `add to the description` → the same question → `description` → **create's "What should the task be called?"**. Root cause: the update clarify stashed no pending state, so every reply was re-classified from scratch and eventually guessed `create_task`. Each ask now stashes a `pending_intents` entry for the Task Agent (the router's pending fallback then routes the reply back here), and `match_bare_task_field` turns a bare field name — or `add to the description` — into a field selection. New `agents/task/field_flow.py`.
- **`Add another note: {text}`** (no "task", no target) now appends to the active task; it previously fell through to the generic clarify.
- Structure: create split into `agents/task/create.py` — `service.py` had grown back to 874 lines, over the 800 ceiling; now 644. Tests: +34.

**2026-07-25 — Task create: content is the description, title is derived (§7.1)**

**The rule: unless the user nominates a title, what they type is the description.** Only `called / named / titled X`, `with title X`, or a quoted string count as naming a title; everything else is content. `extract_create_content` strips the `create a (new) task [to|for|about|:]` preamble, the remainder is stored as the **description**, and `derive_title_from_description` builds the title from it (first sentence, politeness/reminder preamble stripped, truncated to 60 chars on a word boundary, first letter capitalized). The reply says the title came from the content so the user can rename it.

- `Create a task with the notes: remind me to call Bob tomorrow.` → title `Call Bob tomorrow`, description = the notes. Previously asked "What should the task be called?".
- `create a new task to: get back to john with the estimate tomorrow.` → title `Get back to john with the estimate tomorrow`, description = the sentence. **Previously the entire command line — "create a new task to: get back to…" — became the title with an empty description** (smoke test).
- `add a task to check the retaining wall` → the "to …" phrase is now the description (title derived from it), where it used to become the title with no description.
- **Stale-pending fix:** a fresh create command arriving while "What should the task be called?" was pending got swallowed whole as the title. The bare-reply branch now defers to `message_starts_fresh_intent`, so a new command is processed as one and the stale pending entry is dropped.
- The awaiting-title flow is now the fallback only — no title cue AND no usable content. Tests: +29 (`test_maple_task_crud.py`, `test_maple_task_operations.py`).

**2026-07-25 — Task Agent review fixes: bare-determiner anaphora + targeted-`$set` persistence (+ module split)**
- **"mark/assign/archive/rename the task …" now resolves via the active-task context** (new §7.11 row). Bare determiners ("the", "my") leaking out of the target regex previously became a title hint — `mark the task as done` could substring-match any title containing "the", or extract garbage hints like "as done". `_normalize_target` collapses determiners to empty and `extract_reference_hint` treats a nameless "the task" as anaphora.
- **Chat-driven task updates persist via targeted `$set`** (REST parity) instead of whole-document `save()` — a concurrent photo upload, convert claim, or archive can no longer be clobbered by a stale agent copy; `updated_at` is server-stamped.
- Structure: `agents/task/service.py` split into `base.py` / `confirmation.py` / `operations.py` / `service.py` (all under the 800-line ceiling); no behavior change beyond the two fixes above. Tests: +12 in `test_maple_task_operations.py` (determiner unit+behavioral, concurrent-write safety).

**2026-07-22 — Tasks SHIPPED: Task Agent + routing + coverage matrix (§7 flipped)**
- New **Task Agent** (`agents/task/`): core CRUD, per-company status changes, assignee ops, archive/unarchive, and convert-to-estimate (via the new shared `services/task_convert.py` core — the REST endpoint now calls the same code). Registered in `intents.py` (`create/update/delete/list/get_task` + dedicated `convert_task`), `domain_knowledge.py`, and `routers/agents.py`.
- **Reference resolution** (`agents/task/resolver.py`): explicit reference beats active-task context beats recency fallback; relative ("last task", "from yesterday" via the new shared `parse_relative_day_window`), by fuzzy title, by property. Ambiguity → numbered `pending_task_confirmation` flow. `active_task_id/name` persisted by `finalize_result.py`; delete clears the anchor; convert hands the anchor to the new estimate.
- **Policies**: manager-only single delete (shared `agents/role_utils.py::assert_manager_role`, Template agent migrated), convert always confirms (billing slot), feature-flag + 50-task-cap refusals, bulk delete locked by the existing guard.
- **Coverage matrix**: `task` added to `_CRUD_RESOURCES` (+27 generic cases) + new `task_operations` category (8) → Tier 1 159/170 (11 known-gap xfails, all bare-title class); Tier 2 task slice 28/35.
- Tests: `test_maple_task_routing.py` (44), `test_maple_task_crud.py` (14), `test_task_resolver.py` (19), `test_maple_task_context.py` (10), `test_maple_task_operations.py` (24); `test_task_convert_api.py` green post-extraction.
- Post-smoke-test polish (same day): **feature-definition queries** ("tell me about tasks", "what is a task?") now route to HELP for every resource instead of an empty list (`is_feature_definition_query`, see §11.1); **task details render as markdown bullets** (one field per line) in create/get/update responses.
- Create-flow fixes (same day, user report): `with title {task}` / `title: {task}` cues recognized; an inline `notes:`/`description:` clause is captured as the task description; a missing title now stashes a `pending_intents` awaiting-title entry so the bare reply to *"What should the task be called?"* becomes the title (previously looped the same question) — inline notes survive the turn.

**2026-07-22 — Tasks phrasing matrix added (new §7, all rows ⚠️ pending implementation)**
- New: **§7 Tasks** catalogs the full planned Maple surface for the Tasks feature — CRUD (§7.1–§7.6), per-company status changes (§7.7), assignee operations (§7.8), archive/unarchive (§7.9), convert-to-estimate with confirm + billing-refusal copy (§7.10), the three task-referencing forms plus active-task anaphora and ambiguity confirmation (§7.11), and refusals incl. manager-only delete and the flag/quota gates (§7.12). Every row is ⚠️ — no Task Agent or orchestrator routing exists yet. Implementation plan: [`plans/maple-tasks-support.md`](plans/maple-tasks-support.md).
- Sections renumbered: old §7–§12 → §8–§13 to accommodate the new §7. Terminology table is now "6 + 1" resources with a Task row; `{task}` added to the token conventions.

**2026-07-09 — Total-value patterns yield to amount filters; Generating/Failed excluded from total value (§1.1, §1.9)**
- Fixed (regression from 2026-07-08, caught in code review before commit): the new `estimates worth` / `value of … estimates` analytics patterns hijacked amount-threshold LIST phrasings — "show me estimates worth **more than $5000**", "list estimates worth **over 10k**", "what is the total value of estimates **over $10k**?" routed to the company-wide total (dropping the $ threshold) instead of `list_estimates`. The total-value patterns now live in a separate `_TOTAL_VALUE_PATTERNS` tuple that only claims a phrasing when `_parse_estimate_amount_filter` finds **no** over/under-$N filter.
- Changed: `_analytics_total_value` excludes `Generating` and `Failed` (transient AI-generation shells) alongside `Archived`; `Lost` stays in by design — a lost bid is still an estimate the user made.
- Refactor: the pipeline/backlog/completed status sets are now shared class constants (`_PIPELINE/_BACKLOG/_COMPLETED_STATUS_VALUES`) used by the headline, windowed-summary, and total-value handlers, so the buckets can't drift from the dashboard definitions.

**2026-07-08 — Analytics honor the user's date window; "value of my estimates" metric; "N days or older" filter (§1.1, §1.9)**
- Fixed: "What's the value of the estimates I've done over the last **60** days?" and the same question for **30** days returned byte-identical Pipeline/Backlog/Completed numbers — the parsed window reached `_analytics_summary` (`crud_handlers.py`) and was **ignored** (it always called `compute_analytics(period="year")`, whose headline uses fixed windows). A windowed summary now recomputes all three buckets inside the user's window (on `updated_at`) and says which window it used ("Here's a quick summary of your estimates in the last 60 days: …"). The no-window summary is unchanged.
- New: **total estimate value** metric — "what's the value of my estimates?" / "value of the estimates I've done over the last N days" / "how much are my estimates worth?" now answers with `sum(grand_total)` across all non-archived estimates (window-aware, all-time when no window), instead of falling into the generic dashboard summary. Rule-tier routing added to `_ANALYTICS_PATTERNS` (plural `estimates` only — "value of estimate EST-001" stays a single-estimate get, §1.2). Handler: `_analytics_total_value`.
- New: "**N days or older**" age phrasing ("Estimates that are 40 days or older") — added to `_AGE_DAYS_OLD_PATTERN`, so it parses to the `(None, cutoff)` window, targets `updated_at`, and verbless forms route to `list_estimates` via the existing `_match_estimate_list_filter` fast-path. Previously unrecognized: the phrase fell to the LLM tier, landed in analytics, and returned the same static summary as above.
- Tests: `test_maple_analytics_date_windows.py` (28 tests: parsing, routing, dispatch, window-difference regression).

**2026-07-08 — Breakdown queries honor previous-calendar periods (§1.9)**
- Fixed: "what's the breakdown of estimates by divisions **last month**?" silently reported **this** month — `_analytics_breakdown` (`crud_handlers.py`) matched `"month" in lowered` before any last-period check. "last …" / "previous …" (month/quarter/year) now map to the new bounded `last_month` / `last_quarter` / `last_year` periods that `compute_analytics` gained in the dashboard previous-periods change (inclusive start, exclusive end = start of the current period). Current-period phrasings are unchanged. Tests: `test_maple_phrasing_expansion.py::TestAnalyticsBreakdownPeriods`.

**2026-07-06 — Item-count ≠ area guard + property auto-link in create requests (§1.3)**
- Fixed: "Create an estimate to plant **six hydrangea** at the Primavera residence" — the sufficiency extractor hallucinated `area_measurements: "six-acre"` from the plant count, skipped the area question, and generated a six-acre job. Two layers: (1) `SUFFICIENCY_ASSESSMENT_PROMPT` / `DETAIL_EXTRACTION_PROMPT` now state that item counts are material QUANTITIES (kept with the material, e.g. "6 hydrangea"), never area; (2) a deterministic grounding guard (`is_area_value_grounded`, `agents/estimate/conversation_guide.py`) drops any extracted area whose units (acre/ft/sq/yd/m, or NxM dimensions) don't appear in the user's own text — the area question is then asked instead. Volunteered areas in gathering replies get the same guard; the directly-asked area answer is trusted. Tests: `test_estimate_area_grounding.py`.
- New: a property named in the create request ("at the **Primavera residence**", "at **123 Main St**") is now resolved against the Property catalog up front (`agents/estimate/property_reference.py`) and linked at creation — no more "Would you like me to link this estimate to a property now?" when the property was already named. Unique match required; ambiguous/unknown references keep the ask-to-link flow. An explicitly-named property overrides the `property_id` page context (same rule as explicit estimate titles vs `active_estimate_code`). Survives the gathering detour via the `estimate_gathering_property` context stash. Tests: `test_estimate_property_reference.py`, `test_agent_helpers_delegate_create_estimate.py`, `test_estimate_gathering.py`.

**2026-07-05 — Word-number follow-up replies in calculation continuation (§10.3)**
- Fixed: "How much topsoil do I need to fill a 1,000 square feet of lawn?" → Maple asks for the depth → **"Three inches deep."** looped the same depth question forever. The continuation path is regex-only (no LLM fallback) and every extraction pattern required digits, so spelled-out numbers yielded no value and weren't a pivot, re-asking indefinitely. `extract_continuation_values` now normalizes number words to digits first (`_normalize_number_words`: units/teens/tens, hyphenated compounds, `hundred`/`thousand` scales, optional "and" — "three" → 3, "twenty-five" → 25, "seven hundred and fifty" → 750, "two thousand" → 2000, colloquial "twenty five hundred" → 2500). Ungrammatical runs ("nineteen ninety", "five five") are rejected and left as words rather than summed into a wrong value. Applies to every missing-field type and the bare-value fallback. Tests: `test_calculator_text_helpers.py::TestExtractContinuationNumberWords`, `test_calculator_agent.py::TestContinuePending::test_word_number_depth_reply_completes_calculation`.
- Pivot hardening (same change): an interrogative fresh calculation ("**how much** concrete for a 10x12 slab **4 inches** thick") asked while another calculation is pending now pivots to the new calculation even though it mentions the pending missing field — previously its "4 inches" was mined into the stale calc. New `is_fresh_calculation_query()` (interrogative subset: how many/much, how long, calculate, convert) is checked *before* value mining; declarative follow-up answers ("I need it 3 inches deep", "750 sq ft at 3") still continue the pending calculation. Tests: `test_agent_helpers_pending_calculation.py::TestPivotDropsSilently`.

**2026-06-29 — Open-math reasoning path + reverse/inverse coverage (§10.3.2)**
- New **open-math fallback tier** (`agents/calculator/open_math.py`): when no curated formula faithfully models a calculation, the extraction classifier returns `open_math` and a researcher-model call proposes assumptions + one or more options, each carrying an arithmetic *expression* that a sandboxed `safe_eval` computes (the LLM never returns the final number). Handles spaced layouts, multi-orientation counts, composite shapes, and — newly — **reverse/inverse coverage** ("how many sq ft can 25 yards of mulch cover", "how much area does 10 tons of gravel cover"). Behind `CALCULATOR_OPEN_MATH_ENABLED` (default **off**); not yet promoted to production. The old §10.3 "inverse-coverage remains unsupported" note is retired.
- **Known gap (documented, not fixed):** labor-time-from-production-rate questions ("how long to edge 800 linear feet of beds") — they depend on a crew role + rate-card production rate, not a material formula, and don't reach the Calculator's "how many / how much" query gate. Maple declines gracefully and points to the rate-card / estimate workflow. See §10.3.2.
- Tests: `tests/test_calculator_safe_eval.py`, `tests/test_calculator_open_math.py`, `tests/test_calculator_open_math_live.py` (opt-in `llm_e2e`).

**2026-06-21 — Numeric time windows for headline metrics (§1.9)**
- Fixed: "What is my completed value for the **last 90 days**?" answered "in the last 30 days" — the numeric window never parsed, so the handler used its 30-day default for both the computation and the label. Added `_NUMERIC_DATE_RANGE_PATTERN` (`(last|past) <N> day|week|month|quarter|year`) to `_parse_estimate_date_filter`, so "last 90 days" / "past 6 months" / "last 2 weeks" resolve to a real `(start, end)` window. `_describe_date_window` now reports the exact day count ("in the last 90 days") for any span that isn't a canonical named period (week/month/quarter/year), so the label never contradicts what the user asked. Word-form windows ("last week", "this month") are unchanged. Tests: `test_maple_phrasing_expansion.py::TestNumericDateRangeFilter`, `test_dashboard_backlog_parity.py`.

**2026-06-20 — Headline metrics: explanatory routing, dashboard parity, all-time backlog, Won→Completed (§1.9)**
- "How is the Backlog Value calculated?" (and other definitional metric questions) now route to **HELP** instead of returning a dollar figure. `_match_analytics_query` redirects a recognized metric phrased with an explanatory cue to help; `calculated`/`computed` added to `HELP_INSTRUCTIONAL_PATTERNS`.
- Fixed a parity bug: Maple's backlog headline summed only `[WON]` while the dashboard card sums `[WON, SCHEDULED]`, so chat reported $0.00 against a real dashboard figure. `_analytics_headline_value` now includes SCHEDULED. Tests: `tests/test_dashboard_backlog_parity.py`.
- **Backlog relaxed to all-time:** removed the last-30-days recency window from backlog in both `compute_analytics` (dashboard) and `_analytics_headline_value` (Maple). Backlog now sums **every** Won/Scheduled estimate for the company regardless of when it closed; pipeline (90d) is unchanged. Maple's all-time backlog answer reads "… in total"; the dashboard card is relabeled "All time". Guide updated (`users_guide.md` §7.1).
- **Won Value → Completed Value:** retired the "Won Value" headline (Won+Scheduled+Completed, 30d) and replaced it with **Completed Value = `[COMPLETED]` only, last 30 days** across the dashboard card (API field `won_value` → `completed_value`; label "Completed Value"), Maple (`_analytics_headline_value` "completed" metric, answer "Your completed value is … in the last 30 days"; the analytics router recognizes `completed value` / `how much was completed`), and the guide (`users_guide.md` §7.1). The legacy "how much was won?" headline question is retired (parity invariant: chat must mirror the dashboard cards).

**2026-06-15 — Calculator registry refactor + 4 new landscaping calculations (§10.3.1)**
- The Calculator Agent now derives its dispatch table, required-params, type→label map, and the extraction prompt's type list from a single declarative `CalcSpec` registry (`agents/calculator/registry.py`). Adding a calculation is now one formula in `formulas.py` plus one registry entry — the old parallel dicts and `_dispatch()` if-ladder are gone. A drift-guard test (`test_calculator_registry.py`) makes any schema-Literal ↔ registry mismatch a test failure.
- **Five new calculation types, all deterministic:** `aggregate_tons` (gravel/crushed-stone base by weight, cu yd × density), `mulch_bags` (bagged-material count, ÷ bag volume), `retaining_wall_blocks` (courses × blocks-per-course), `step_count` (total rise ÷ riser height), `plant_count` (groundcover grid spacing — square `area ÷ spacing²` or triangular `÷ (spacing² × 0.866)`). All math stays in pure `formulas.py`; the LLM only extracts parameters.
- **Regex fast-path now reads the output-unit signal:** "how many **tons**/**bags** … N sq ft … N inches" routes to `aggregate_tons`/`mulch_bags` instead of silently collapsing to cubic-yard coverage. `steps?` added to the orchestrator pre-classifier's measurement-unit set.
- Tests: `tests/test_calculator_formulas.py` (4 new formula classes), `tests/test_calculator_agent.py::TestAggregateTons`, `tests/test_calculator_registry.py`.

**2026-06-15 — Status transitions route deterministically; status *questions* offer to proceed (§1.4)**
- **Routing fix (the reported bug):** the Orchestrator never routed estimate status changes to `update_estimate` — the rule classifier's estimate field-edit detector only knew description/notes/property, and there was no status branch. So `set the status for {EST} to Sent`, `mark {EST} as Sent`, `archive {EST}`, etc. fell through to `unknown` and (in prod, where the LLM is the primary classifier) routed inconsistently — sometimes a help answer, sometimes "that's not something I can do." Added a **deterministic status-transition lane** in `OrchestratorAgent.process()` (runs before the LLM) plus a branch in `_classify_with_rules`, both gated on an estimate reference and the shared `parse_status_transition` matcher.
- **Word-order gap:** `_detect_status_transition` only matched `status to Y` (adjacent), `to Y status`, or `as Y`, so `set the status for|of|on {EST} to Y` (the estimate code interposed between "status" and "to") was missed. Detection logic moved to a single-source module function `parse_status_transition` in `agents/estimate/text_helpers.py` (shared by the agent and the orchestrator so routable ≡ actionable), and broadened with `_STATUS_TRANSITION_STATUS_REF_TO_PATTERN`.
- **Status *questions* now offer to act (issue #2):** a status request phrased as a question (`Can you set {EST} to Sent?`) is still claimed by the help classifier, but Maple now answers **and offers** to do it (`Yes — I can set {EST} to Sent … Want me to go ahead?`), stashing a `pending_status_transition` record. A following "yes" executes it via `routers/agent_helpers/pending_status_transition.py`; "no" cancels. Only fires when an EST-code and a recognized target status are present.
- **Send-gate message made self-contained:** when a confirmed send is blocked by unresolved missing items, the refusal (`_refuse_send_with_missing_items`) now returns a self-contained statement (`needs_clarification=False`, no `clarifying_question`) instead of the bare, unanswerable question "Would you like to add them to your catalog or dismiss them?" — chat can't resolve missing items (that's a portal-editor action), and the portal renders only `clarifying_question` on clarification turns, so the question previously showed with no antecedent for "them". (The general portal issue — clarification turns dropping the `response` context, which also affects illegal-transition refusals — is tracked separately.)
- Tests: `test_estimates_status_transition_status_ref_to_phrasing`, `test_chat_blocks_sent_while_missing_items_unresolved` (`tests/test_estimate_agent.py`); `test_orchestrator_routes_estimate_status_transition`, `..._is_deterministic_not_llm`, `..._status_question_form_stays_help`, `test_help_status_question_offers_to_proceed_and_sets_pending` (`tests/test_orchestrator_intents.py`); `tests/test_pending_status_transition.py`.

**2026-06-12 — Edit lock tightened to Draft/Review only (§9.7)**
- The locked-status edit guard now mirrors the portal's `isEditableStatus` (`portal/src/lib/estimateStatus.ts`) instead of the PUT route's narrower lock: estimate contents are editable in chat **only in Draft or Review**. Won / On Hold / Lost / Scheduled / Completed (and internal statuses) now refuse edits too, closing the gap where chat could edit a Won estimate's notes while the UI showed it read-only. Allowlist constant: `_EDITABLE_ESTIMATE_STATUSES` in `agents/estimate/crud_handlers.py`.
- Refusals stay persona-voiced; when the state machine offers a one-hop path back (On Hold → Review, Lost → Review) the refusal suggests it ("Ask me to move it to Review first"). Archived and Sent/Approved keep their specific copy.
- Note: the HTTP PUT route still only locks Sent/Approved/Archived — tracked as a follow-up (#349 in code-review-followups.md).
- Tests: `test_locked_estimate_other_statuses_refuse_notes_edit` (Won/Scheduled/Completed), `..._review_reachable_statuses_suggest_review` (On Hold/Lost), `..._won_refuses_work_item_edit`, `test_editable_estimate_notes_edit_still_works` (Draft + Review).

**2026-06-11 (follow-up 2) — Locked-status edit guard (new §9.7)**
- Edits to an **Archived** estimate (any sub-op) and to a **Sent**/legacy **Approved** estimate (any sub-op except the unsend status change) are now refused in chat, mirroring the PUT route's locks ("Cannot update an archived estimate" / "Cannot update a sent estimate"). Enforced once in `_load_estimate_for_update` (`agents/estimate/crud_handlers.py`) — the shared loader behind every edit sub-op: notes, description, property linking, template application, and all work-item operations. Reads are unaffected; the status-transition path has its own rules (state machine + role gates) and is not blocked by this guard.
- Refusals are persona-voiced with the next step: "Ask me to unarchive it first…" / "Ask me to move it back to Draft or Review first…".
- Tests: `test_locked_estimate_archived_refuses_notes_edit`, `..._sent_refuses_notes_edit` (Sent + Approved), `..._sent_refuses_work_item_edit`, `test_draft_estimate_notes_edit_still_works` (`tests/test_estimate_agent.py`).

**2026-06-11 (follow-up) — Status-transition authorization + persona refusals (§1.4, §9.6)**
- The status handler now also enforces the HTTP layer's **role gates**: any transition touching `Sent`/legacy `Approved` (send or unsend) is **Owner/Admin only** (mirrors the PUT role gate); **archive/unarchive** is **Owner/Admin or the estimate's creator** (mirrors the dedicated endpoints' check against `created_by_email`, case-insensitive).
- Identity reaches agents via two new context keys set by the authenticated `/agents/orchestrate` endpoint from the verified user (never the client payload): `current_user_email` (normalized lowercase) and `current_user_role`. Gated operations **fail closed** when identity is missing from context.
- All status-transition refusals (illegal edge, role, creator, missing identity) were rewritten in Maple's persona voice — warm, first-person, apologetic, and always offering the next step ("From Draft I can take it to Archived, On Hold, or Sent — want me to do one of those instead?" / "If you ask an Owner or Admin on your team, they can take care of it for you.").
- Tests: `test_estimates_status_transition_send_unsend_requires_owner_or_admin`, `..._archive_member_non_creator_refused`, `..._archive_member_creator_allowed`, `..._unarchive_member_non_creator_refused`, `..._gated_op_missing_identity_fails_closed`, `..._ungated_op_member_allowed` (`tests/test_estimate_agent.py`); `test_orchestrate_endpoint_passes_user_identity_to_agents` (`tests/test_orchestrator_endpoint.py`).

**2026-06-11 — Status-transition state machine enforced in chat (§1.4, new §9.6)**
- Maple's status handler (`_handle_update_estimate_status_transition` in `agents/estimate/crud_handlers.py`) now calls `validate_estimate_status_transition` from `models/estimate.py` — the same single-source-of-truth state machine the PUT route enforces (#46) and the FE renders (`portal/src/lib/estimateStatus.ts`). Previously chat wrote `status` directly to the DB, so e.g. `mark {EST} as won` succeeded on a Draft estimate.
- Legal edges are unchanged and still save (Draft → Sent/On Hold/Archived; Review → Sent/On Hold/Archived; On Hold → Review; Won → Scheduled/On Hold/Lost; Lost → Review; Scheduled → Completed; Sent/Approved → anything = "unsend"). Illegal edges now refuse with the current status, the rejected target, and the allowed next statuses (🛑 rows in §9.6).
- Tests: `test_estimates_status_transition_blocked_by_state_machine` / `..._allowed_by_state_machine` in `tests/test_estimate_agent.py`.

**2026-06-09 — Social & personality handling (greetings + anthropomorphized questions)**
- **Greetings → new `social` intent (canned, no LLM).** Bare greetings ("hey", "hi maple", "good morning") are caught in the orchestrator (`_detect_policy_short_circuit` via `is_greeting`) and answered instantly from `GREETING_RESPONSES`; suggestion chips come from `_SOCIAL_SUGGESTIONS`. The `social` intent is operation `social`, `read_only` — a separate intent, not a help topic.
- **Personal questions → new `personal` help topic (persona-answered).** Anthropomorphized questions ("how are you?", "what do you look like?", "are we friends?", "are you married?", "are you an AI?") are detected by `is_personal_question` and routed through the existing help path (`HelpHandler.detect_topic` returns `personal`), then answered by the LLM guide responder from Maple's persona thanks to a rule-1 exemption in the guide prompt.
- **New detectors** `is_greeting` / `is_personal_question` in `agents/text_utils.py`; **new persona** `agents/maple_persona.py` (playful deflection for flirty messages, no romantic reciprocation, honest about being an AI, short replies that pivot back to work).
- **Topic-keyed by design** so product-capability phrasings stay in the product lane: "are you able to add contacts?", "can you create an estimate?", "how are you estimating this job?" are explicit negatives → normal help/CRUD, not `personal`.
- New §11.6 (Social & personality) catalogs the greeting and personal-question phrasings.

**2026-06-07 — Note-body quote fix + estimate anaphora persistence (user report: truncated note + "the same estimate" not recognized)**
- **Quoted note/description bodies no longer truncate at an apostrophe.** `_NOTE_WITH_QUOTED_VALUE` and `_ESTIMATE_DESC_QUOTED` used `[^"']+?`, which treated the `'` in `"Contact me if there's any issues"` as the closing quote and captured only `Contact me if there`. Both now share `_QUOTED_VALUE_GROUP` — a matched-quote capture (straight + curly, double + single) whose close-quote is a negated class, so an apostrophe or the other quote type can appear inside the value. Callers coalesce the four branches via `_first_quoted_group`.
- **"the same / that / previous estimate" now resolves after a note edit.** Root cause: estimate note/description/work-item updates return a **flat** result (`{"operation": "update_estimate_notes", "estimate_id": ...}`) with no nested `"estimate"` dict, so `finalize_result._resolve_entity_reference` never set `active_estimate_code` — the next turn had no anaphora anchor and asked "Which estimate?". The resolver now recognizes a flat `estimate_id` (skipping delete ops). Resolution itself already supported anaphora via `active_estimate_code`; the gap was purely that it was never persisted.
- **`previous`/`prior` added to `_LAST_ESTIMATE_PATTERN`** as cold-start fallbacks (mid-conversation they resolve via active context first).
- Tests: `TestNoteQuoteExtraction` + `TestEstimateAnaphora` (field-edits suite); flat-`estimate_id` cases in `test_agent_helpers_finalize_result.py`.

**2026-06-06 (follow-up) — Production router path fixed (user report: "estimate detail is not shown")**
- The morning wave landed in the **agent** handlers, but the production endpoint routes through `routers/agents.py` delegation helpers that were bypassing them in three places, now fixed:
  - `delegate_get_estimate` rendered its own thin summary (code/status/work-items/grand-total only) — it now also carries **Created / Last updated / Description / Notes / ID**, mirroring the agent renderer.
  - `_should_delegate_update_estimate_to_agent` didn't recognize the new description/notes sub-ops and held a **stale copy** of the link patterns — it now defers to the new `EstimateAgent.owns_update_sub_op` (description + notes + link detectors as the single source of truth), so those phrasings reach the agent instead of the add/modify-items flow.
  - Bare-title extraction now accepts **sentence-case titles** ("Spring cleaning") — first word capitalized, 2+ words, tail bounded by a connector stop-list; single trailing capitalized words ("estimate Won") still never capture.
- Lesson encoded in tests: `TestRouterDelegationPredicate` + `TestRouterDelegationIntegration` pin the router→agent delegation for every new sub-op, and the `delegate_get_estimate` tests pin the enriched render using the exact reported phrasing ("show details for the Spring cleaning estimate").

**2026-06-06 — Estimate field edits & follow-up SHIPPED (plan: [plans/maple-estimate-field-edits.md](plans/maple-estimate-field-edits.md))**
- All five 2026-06-05 user-reported items implemented and the corresponding rows flipped ✅ (each remaining ⚠️ was re-verified against the live rule tier on 2026-06-06):
  - **§1.10 description** — new `_detect_estimate_description_update` + `_handle_update_estimate_description` (estimate-level `description`; quoted/colon/unquoted forms; `write-up`/`overview` synonyms). Dispatcher order: work-item → status → description → notes → link → template.
  - **§1.10 notes** — title/anaphora resolution; informal cues `jot`/`FYI`/`remember`/`write down` detected AND routed (orchestrator `_informal_note` value-bearing arm).
  - **§1.6 linking** — relationship phrasings (`tie`/`connect`/`associate`, "is for", "property for this quote"), bare-property-name targets, `link {EST} to {property}` now rule-tier (was 🤖 LLM).
  - **§1.2 details** — `_build_estimate_details_text` renders Created / Last updated / Description / Notes / ID; "show me everything on the {title} quote" works (linked-property NAME still pending an async lookup).
  - **§10.4 follow-up** — Estimate registered in the generic `optional_follow_up` machine; **one-turn** "Yes, link it to Bob Residential"; bare-property answers; legacy `pending_estimate_follow_up` no longer dual-writes and defers to the generic key (the legacy handler swallowing the reply was the root cause of the original report).
- **Cross-cutting:** shared `_resolve_estimate_code_or_title` (code → anaphora → latest → title) used by all update sub-handlers; bare-title extraction `_TITLE_PRE/POST_NOUN_RE` (case-sensitive first word, 2+ words incl. sentence-case tails, ordered before the any-quoted fallback so note bodies aren't mistaken for titles); orchestrator estimate field-edit fast-path in `_classify_specific_phrasings`.
- Tests: `tests/test_maple_estimate_field_edits.py` (57) + additions to `tests/test_agent_helpers_delegate_create_estimate.py`; ~500-test regression sweep green; mypy + ruff project-wide zero.
- Still ⚠️ after this wave (verified, with misroute notes where found): casual detail forms ("rundown", "full info" → misroutes to `get_contact`, "open up"), "when was X created/updated" (the created form misroutes to `create_estimate`), value-before-cue description ("put X as the overview"), `describe … as`, note verbs `make`/`leave`/`tack`, generalized `note … that` tail, "job site" link cue, soft negatives ("not right now", "I'll do it from the portal"), `bid`/`proposal` as title-extraction nouns, and job-name → estimate resolution (Task-8 stretch).

**2026-06-05 — Estimate-level field-edit & details gaps logged (⚠️ for implementation)**
- Five user-reported estimate phrasings reviewed against the live code; new ⚠️ gap rows added for the ones not correctly handled. Root cause shared by three of them: **title-based estimate reference (`_resolve_estimate_by_title`) is wired only into the `get_estimate` path** (`crud_handlers.py:1535`); every *update* sub-handler (`notes` @1891, property `link` @1943, and the not-yet-built description handler) resolves the estimate by **EST-code only** (`_resolve_estimate_code`), so a title like "Spring Cleaning" prompts for a code on the update path.
- **§1.10 (new)** — estimate-level `description` edit is unhandled (model field exists, no dispatcher sub-op → falls through to the `_handle_update_estimate` refusal); estimate-level `notes` append **is** handled rule-side (newly documented) but code-only.
- **§1.2** — title-based details response is too thin: `_build_estimate_details_text` (`crud_helpers.py:446`) emits only Code/Title/Status/Grand total. Missing `created_at`, `updated_at`, linked property, description, notes (all present on the model and in the full result payload, just not rendered).
- **§1.6** — title-referenced property linking ("set the property of estimate {Name} to {property}") is a gap; the link handler fires but can't resolve a titled estimate.
- **§10.4 (new)** — the post-creation "link this to a property now?" follow-up (`extraction_helpers.build_optional_follow_up`) has no pending-intent state, so an affirmative reply ("Yes, link it to Bob Residential") isn't carried back into the linking handler.
- Each of the five sections now carries **landscaper-style variant rows** in its catalog table (informal verbs, customer/job-name references, bare-address properties, value-only notes, confirmation-word-plus-property replies) plus a concise **Implementation note**, so coverage targets the real input distribution, not just the canonical phrasing. Recurring sub-gaps surfaced by the variants: estimate synonyms `bid`/`proposal`, job-name → estimate resolution, possessive property nicknames ("Bob's place"), informal note cues (`jot down`/`FYI`/`remember`), and bare-property affirmatives in the link follow-up.
- Implementation plan written: [`plans/maple-estimate-field-edits.md`](plans/maple-estimate-field-edits.md).

**2026-06-02 — Template-driven estimate creation (skips AI generation) + gathering decline fix**
- A **create-estimate request that names a template** now skips AI generation entirely and instantiates from the template (§1.3, §6.7). No-baseline → template applied as one work item verbatim; baseline (`size`+`unit`) → linear scaling to the job size (`factor = job_size ÷ baseline_size`), taking the size from the request or asking once (`pending_template_size`). Convertible units (sq yd↔sq ft, lin yd↔lin ft) are converted; incompatible (area vs length) re-asks. Property context is linked.
- New: `agents/estimate/template_scaling.py` (`convert_size`, `parse_job_size`, `scale_job_item`), `agents/estimate/text_helpers.detect_template_in_create_request`, `routers/agent_helpers/template_estimate.py` (`begin_template_estimate`, `handle_pending_template_size`).
- **Gathering decline no longer cancels** (§1.3): "No"/"skip" to a gathering question (e.g. "Any material preferences?") records an assumption and continues; only explicit cancel phrases abort. New `is_cancellation_text`, `get_assumption_value`.
- Tests: `test_template_scaling.py`, `test_template_create_routing.py`, plus gathering/predicate additions.

**2026-06-02 — Phrasing expansion: ratios, age/staleness, status-`in`, material qualifiers**
- **Status comparisons / ratios** (§1.9) — "what's my won-lost ratio?", "won vs lost", generic "draft vs approved", "win rate", "how am I doing on bids?". New `parse_status_comparison()` + `format_status_comparison()` in `agents/estimate/text_helpers.py`; counts via `compute_status_comparison()` in `routers/estimates.py`; handled by `_analytics_comparison` in `crud_handlers.py`. Routed through the existing `analytics_estimates` path (`_match_analytics_query` now also calls `parse_status_comparison`). A win-loss family cue defaults to WON-vs-LOST; an explicit "X vs Y" names both statuses in order. Count-based, with a win-rate % for the WON/LOST pair.
- **Age / staleness filter** (§1.1) — "estimates that are 30 days old", "not touched in a month", "haven't been updated in 30 days" via new `_AGE_DAYS_OLD_PATTERN`. **Both** age phrasings (`older than X days` and `X days old`/stale) now constrain **`updated_at`** (was `created_at` for older-than) via `_estimate_date_filter_field()`; relative date-range phrasings ("from last week") keep `created_at`. Verbless age phrasings route to `list_estimates` via the orchestrator `_match_estimate_list_filter` fast-path.
- **Status filter via `in`** (§1.1) — "find estimates in draft", "estimates in review" already resolved via the existing `in` connector in `_estimate_status_from_text`; coverage rows added.
- **Material qualifier list** (§4.5/§4.9) — "what {X} materials do I have?" matches {X} as a substring against material **name OR category** (`_find_materials_by_name_or_category` + `_extract_list_qualifier`). Count-by-category ("how many hardscape materials do I have?") now resolves the category for count queries too.
- New tests: `tests/test_maple_phrasing_expansion.py` (routing + pure parsers/formatter), plus additions to `test_material_agent.py` and `test_estimates_analytics.py`.

**2026-06-02 — `clear` restored as a bulk-delete verb (with estimate-creation exemption)**
- Reverted the May 2026 removal of `clear` from the bulk-delete verb list: `clear all {resource}` ("clear all estimates", "clear every material") is again refused as a bulk delete, matching the `delete`/`remove`/`drop`/`wipe` policy (§9.1).
- Added `is_estimate_creation_request()` in `agents/text_utils.py`, applied at the **orchestrator routing layer** (`_detect_policy_short_circuit`) so estimate/quote creation requests whose job description mentions clearing/removing work ("create an estimate to clear out all the weeds in my backyard") route to `create_estimate` instead of being refused. The exemption is deliberately NOT inside `is_bulk_delete_request()` — that guard stays strict so each domain agent's defensive delete-path check keeps full force. A `_ESTIMATE_AS_DELETE_TARGET` veto ensures "delete every estimate" (estimate as the delete target) is never read as creation.
- Reconciled contradictory tests: `test_text_utils.py` and `test_maple_new_phrasings.py` now agree that `clear all {resource}` is bulk delete and estimate-creation-with-clearing is allowed (verified end-to-end through the orchestrator).

**2026-05-27 — Work-item field operations (implemented)**
- Expanded §1.5 from a flat table into eight sub-sections (§1.5.1–§1.5.8) covering all CRUD operations on work items inside an estimate.
- Added `{WI}` placeholder convention for work-item references (positional, by description, contextual).
- §1.5.1 Work-item CRUD: added list/count/show work items (3 → ✅ rule).
- §1.5.2 Division: assign/move/put/query phrasings (6 → ✅ rule, 1 bulk ⚠️ gap).
- §1.5.3 Description: "set description"/"update description"/"what's description" (3 → ✅ rule, 1 "describe as" ⚠️ gap).
- §1.5.4 Recurring schedule: all 13 phrasings implemented (✅ rule). `recurring`/`recurrence` removed from `_WORK_ITEM_REFUSED_FIELDS`. Handlers parse 3 schedule shapes: total occurrences, date range, specific months. *[2026-09-27: superseded — work-item recurring was deferred from chat on 2026-09-26; see the reference's §1.5.4 🛑.]*
- §1.5.5 Materials in work item: all 11 phrasings implemented (✅ rule). Add material from catalog, remove by name, list/count. Sub-total auto-recalculated.
- §1.5.6 Activities in work item: 9/13 implemented (✅ rule). Add with optional role/effort, remove by name, list/count. 4 update-in-place phrasings (change role/effort/rate, assign rate card) remain ⚠️ gap.
- §1.5.7 Cost adjustments: subtotal/total read queries (2 → ✅ rule, 1 "how much" ⚠️ gap). Percentage fields remain 🛑 refused.
- §1.5.8 Total amount adjustment: all 9 phrasings implemented (✅ rule). Direct sub_total override with grand_total recalculation.
- New file: `agents/estimate/work_item_field_handlers.py` (WorkItemFieldHandlersMixin).
- New test file: `tests/test_maple_work_item_ops.py` (79 tests — routing, op detection, regression, param parsing).
- Orchestrator routing: extended verb list with make/assign/move/put/adjust/round/bump/reduce/turn/stop/disable; added sub-resource, list, query, and recurring patterns; work-item field queries bypass `is_help_query` (excludes definitional "what is a work item?").

**2026-05-26 — Template CRUD phrasings**
- Template resource added to terminology table and phrasing catalog (§6). All phrasings are ⚠️ gap — no Template Agent or orchestrator routing exists yet.
- Phrasings cover: list, get, delete, verbless, and apply-template-to-estimate (§6.7).
- Template **creation, update, and duplicate are refused** (§9.5) — users must manage these through the portal UI.
- Sections renumbered: old §6–§11 → §7–§12 to accommodate the new §6.

**2026-05-26 — May expansion**
- Dashboard analytics intent (`analytics_estimates`) with pipeline value, backlog, completed value, and breakdown-by-status/division phrasings (§1.9). Custom time windows respected — "pipeline value in the last 30 days" queries the DB with the user's window, not the default 90-day headline.
- Title-based estimate lookup — `_handle_get_estimate` now resolves estimates by quoted title or `title/called/named X` phrases when no EST-code is present (§1.2)
- "win" added as a verb-form alias for EstimateStatus.WON so "how many estimates did I win this month?" routes correctly
- "older than X days" age-based date filter via `_AGE_FILTER_PATTERN`
- "at property" cross-resource variant for estimate→property queries
- Contact→property "linked to" cross-resource patterns (§8.1)
- Material size "of" form (`how much does 12x12 of concrete blocks cost?`) and category query (`what category is material X?`) (§4.9)
- Role field queries via "what's the X for role Y?" routing to `get_labour` (§5.8)
- "clear" removed from bulk-delete verb patterns — ambiguous in this domain (§9.1)
- US English: user-facing "labour" → "labor" in response strings, accuracy suggestions, and guide content
- User guide updated: contacts can be linked to multiple properties (no limit)

**2026-05-13 — Object links in CRUD responses**
- `object_link()` helper in `agents/text_utils.py` renders `[Name](/properties?open=<id>)` for Property/Contact/Material/Labor Get/Create/Update/List responses and `[Name](/estimates/<id>)` for Estimate Get/List. Frontend list pages read `?open=<id>` on mount and auto-open the edit modal.

**2026-05-02 — Waves 1-4.1**
- Wave 4.1: Contact-anchored estimate list, EST-code regex broadened to alphanumeric, suffix "property" form
- Wave 4: Estimate ↔ property/contact outbound drilldowns (§1.8)
- Wave 3: Estimate filters (status + date + amount), cross-resource drilldowns (materials/roles on EST-code), material query variants, partial-bulk delete refusal
- Wave 2: Cross-resource routing + agent-side join for all four CRUD resources (§8)
- Wave 1: Possessive/field-targeted phrasings, help gaps (§11.5), coverage blind spots consolidated into §13
