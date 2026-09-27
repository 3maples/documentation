# Maple routing convergence: design

**Date:** 2026-09-25
**Status:** Draft, awaiting review
**Builds on:** [`2026-09-23-maple-estimate-multi-turn-editing.md`](2026-09-23-maple-estimate-multi-turn-editing.md) (all of it is still uncommitted)
**Decided with Simon:** 2026-09-25, in the brainstorming session after the sixth `/code-review` pass

## 1. Why this exists

Six `/code-review` passes over the multi-turn estimate editing work have not
converged: 36, 31 and 32 findings in passes four to six, with 5–7 of each
pass's findings caused by the previous pass's fixes. The pattern has a cause,
not bad luck:

1. **Ambiguity is being resolved with hand-written regexes over open-ended
   language.** Each fix narrows or widens one pattern for the phrasings in the
   finding and moves the boundary for the phrasings next to them.
2. **Five layers each decide "is this a reply or a new request, and which
   record?"** — the orchestrator (`_answers_estimate_question`,
   `_is_work_item_edit`, the history lane), the router (awaited-value override,
   pending fallback), the agent (`answers_open_question`,
   `_abandons_value_prompt`, `_pick_candidate`) and `fuzzy_confirmation`. Their
   precedence is implicit, so a change in one shows up in another.
3. **Conversation state multiplies the cases.** The same phrasing behaves
   differently with an estimate open, a work item open, another domain last
   touched, or a question pending. The coverage matrix tests only "nothing
   open".
4. **There was no fixed regression corpus.** Tests pinned the phrasings each
   finding quoted; reviewers probed new ones every pass.
5. **Safety came from reading the message right**, not from the write path. A
   misread went straight to a write.

The rules-first design is sound. The rules grew to cover the long tail, which
is the planner's job.

## 2. Goal and definition of done

**Done** means review has **converged**: a `/code-review` round under the
contract in §6 reports **no new findings**. A finding is new when it isn't
already in the latest ledger or in `code-review-followups.md`. In particular,
a fix from the previous round must not cause one.

Fixing every finding is **not** part of done. Each round, Simon picks what to
fix with `/fix-issues`, and the rest is logged as follow-ups. Convergence
comes from three things:
- the rules can't drift, because they're a fixed written list (§4);
- a fix can't quietly break other phrasings without the snapshot showing it
  (§5.5);
- review stops re-finding known issues and stops inventing phrasings (§6).

§8 is the plan's default resolution for the sixth-pass findings. Any of them
can be logged instead of fixed without affecting done.

**Non-goals:** the Property, Contact, Material and People agents' own
routing (their 174-phrasing matrix is stable). They are touched only where
they meet the estimate anchor. Equipment, labor burden, discount,
reorder/duplicate, inventory gaps and document generation stay out of scope,
as in the parent plan.

## 3. Decisions

| # | Decision | Chosen | Rejected |
|---|---|---|---|
| D1 | How much the rules own | A **written list** of exact commands (§4); everything else goes to the edit planner or a question | Planner for every edit (latency on every turn); keeping today's rules plus guards (still open-ended) |
| D2 | Writes whose target was inferred | **Confirm only when not fresh**: apply-and-name for a fresh target; yes/no for a stale one, and for any remove/delete (§5.2) | Always confirm (double the turns); apply + undo (needs an undo command, and the wrong write still happens) |
| D3 | How review judges phrasing | **Against the spec and the snapshot** (§6); unsupported phrasings are gaps, never blocking | Gaps as MEDIUM (brings the open-ended probing back); leaving `/code-review` as is |
| D4 | Protecting the uncommitted work | **Stay uncommitted**; a `git diff` patch of platform, portal and documentation goes to the session scratchpad before each build step | Checkpoint branch; checkpoint on main |
| D5 | What "done" means | **Review converges**: a round reports no new findings (§2); which findings get fixed is chosen per round | Every finding fixed and Approve |

## 4. The written command list

One module, `platform/agents/estimate/command_grammar.py`, holds every
estimate phrasing a rule handles. It is pure: `match_command(text) ->
Optional[ListedCommand]` reads only the text — no database, no conversation
state. **A rule that isn't in this module doesn't exist.** The phrasing
reference's rule table (§1 there) lists the same entries, one-to-one.

`ListedCommand` carries `id` (from the table below), the parsed slots, and the
reference form the message used for its target (`code`, `title`, `ordinal`,
`label`, `pronoun`, `none`). Resolving that reference to a record is §6's job,
not the grammar's.

### 4.1 Shared pieces

- **Estimate reference** `<est>`: an E-code; `this/the/current estimate`
  (also quote/bid/proposal); `the <title> estimate|job|quote`;
  `the estimate (for|called|named) <title or customer>`; or absent.
- **Work-item reference** `<wi>`: `work item <N>`; `the <ordinal> work item`;
  `the <label> work item`; `it` / `that one`; or absent.
- **Lead**: up to two optional openers from a closed list — `hey`, `hi`,
  `ok`/`okay`, `yes`, `great`, `perfect`, `thanks`, `please`, `now`, `also`,
  `and`, `actually`, `never mind`, `one more thing`, `quick`, `can you`,
  `could you` — each followed by a comma or space. Nothing else may precede
  the verb. A trailing `please`/`thanks` is ignored.
- **Command head**: the text before a dictated payload (`: <body>`,
  `saying <body>`, quoted text) and before an assigned value (`to <value>`,
  `called/named <value>`). Policy guards and the open-question decider read
  only the head.

### 4.2 Entries

| id | Shape (after the optional lead) | Accepts | Does not accept (→ planner / classifier) |
|---|---|---|---|
| `list_estimates` | `(list\|show\|see\|view)( me)?( all\| my\| the)? estimates( for <name>)?`, `how many estimates …` | "show me my estimates", "list the estimates for Bob Smith" | "anything open for Bob?" |
| `get_estimate` | `(show\|open\|view\|get)( me)? <est>` with `<est>` present | "open E0042", "show me this estimate", "open the Jones backyard estimate" | "what's going on with Jones?" |
| `list_work_items` | `(list\|show)( me)?( the)? work items( on <est>)?` | "show the work items on E0042" | "what's in there?" |
| `get_work_item` | `(show\|open)( me)? <wi>` with `<wi>` present | "show work item 2", "open the patio work item" | "the patio one" (with no menu open) |
| `create_estimate` | `(create\|start\|make\|build\|new)( a\| an)?( new)? (estimate\|quote\|bid\|proposal) (for\|to) <scope>` | "create an estimate for sod at 12 Oak St" | "hey, add a note to work item 2: …" |
| `rename_estimate` | `rename <est> to <title>` | "rename this estimate to Spring Cleanup" | "call it Spring Cleanup" |
| `add_work_item` | `add( a\| another)? work item (called\|named) <name>( to <est>)?` | "add a work item called Fence to E0042" | "add a fence" |
| `remove_work_item` | `(remove\|delete) <wi>` with `<wi>` present | "delete work item 2", "remove it" | "get rid of the fence stuff" |
| `rename_work_item` | `rename <wi> to <name>` | "rename work item 2 to Back Fence" | "call the second one Back Fence" |
| `set_percentage` | `(set\|change\|make)( the)? (markup\|overhead\|tax)( on <wi>)?( to)? <N>( ?%\| percent)` | "set the markup on work item 2 to 20%" | "bump the markup a bit" |
| `set_gross_margin` | `(set\|make)( the)? gross margin( on <wi>)?( to)? <N>( ?%\| percent)` | "make the gross margin 30%" | "I want 30% profit" |
| `set_total` | `(set\|make)( the)?( work item)? total( on <wi>)?( to)? \$<N>` | "set the total on work item 1 to $1,000" | "make it an even thousand" |
| `add_note` | `(add\|leave\|put)( a)? note (to\|on) <note-target>(:\| saying) <body>` | "hey, add a note to work item 2: check drainage", "add a note to this estimate saying call first" | "jot down a note for John Doe: …" (another record — classifier) |

`<note-target>` is only: an E-code, `this/the estimate`, `<wi>` with a
reference, or `it`. Any other named target is not this command.

### 4.3 Ported entries

Some rule-only abilities have no planner command, so deleting their detector
would delete the ability. These are registered in `command_grammar.py` as
**ported** entries: the entry wraps the existing detector unchanged, and its
grammar is that detector's pattern, documented in the entry. They were not a
source of routing churn; tightening them is out of scope unless a review
finding under §6 asks for it.

| id | Wraps | Example |
|---|---|---|
| `set_status` | `_detect_status_transition` (agent) / `parse_status_transition` (orchestrator) | "mark E0042 as sent", "archive the patio job" |
| `set_estimate_description` | `_detect_estimate_description_update` | "set the description of E0042 to …" |
| `generate_work_item` | `_detect_generate` | "generate a scope for a patio and price it" |
| `set_recurring` | `_detect_work_item_op` → `recurring_enable/_disable/_query` | "make work item 2 recurring monthly" |
| `list_work_item_lines` | `_detect_work_item_op` → `list_materials` / `list_activities` | "what materials are on work item 2?" |
| `query_work_item_field` | `_detect_work_item_op` → `query` | "what's the markup on work item 2?" |
| `adjust_assumption` | `_detect_assumption_adjustment` | "use premium pavers instead", "make it 300 sq ft" |
| `apply_template` | `_detect_template_application` | "apply the Driveway Maintenance template to E0042" |
| `link_property` | `_is_property_link_request` | "link this estimate to 123 Main St" |

Every other branch of today's `_handle_update_estimate` cascade (material
and activity add/remove/update, work-item description/division/rename by
loose phrasing, set-total by loose phrasing, the `WorkItemEdit` kinds
`relative_percentage`, `compound`, `multi_target`) is deleted; the planner
has a command for each.

**Policy refusals** are not commands; they run once in the orchestrator on the
command head (§5.3): bulk delete and equipment. **Labor burden** and a
**material's catalog cost** are refused inside the estimate edit path only —
by the planner's schema (it has no field for either) and its `unsupported_reason`
values (`material_cost`, and a new `labor_burden` that keeps today's burden
refusal copy) — never by a routing regex.

Line-level edits (add/update/remove a material or activity, quantities,
prices, effort, roles), description changes, property links, recurring,
division, AI-generated scope and every multi-edit turn go to the planner.

### 4.4 Added during implementation

Found necessary by the migration (each with accept/reject tests in
`tests/test_command_grammar.py` and routing-snapshot rows); the phrasing
reference §1.0 is the current full table.

- **Core:** `set_work_item_field` (a work item's description or division,
  with a value-less prompt form), `set_estimate_field` ("update the
  description/title to …" — routed to the estimate only while it is in
  focus), `rename_pronoun` ("rename it to …", freshest anchor), the bare
  `add_note` form ("add a note: …"), add_work_item's quoted-name and
  value-less prompt forms, more reference forms ("this/my work item", "the
  Work Item #1", "work item <label>", "work-item"), an optional estimate
  suffix on work-item commands ("… on E0043"), "tax/overhead rate", "profit
  margin", three openers.
- **Ported:** `set_estimate_title` (`_detect_estimate_title_update`) and
  `estimate_note` (`_detect_note_update`).
- **Routing-only helpers:** `names_work_item` (a work item named outright is
  the estimate's domain), `addressed_phrase` (the router's data check that
  "… to the front yard" names an existing work item before pricing new work),
  `line_edit_target` (a line edit goes to the estimate when the open work
  item has that line — the anchor records its activity and material names),
  `foreign_note_target` (a note for another record never lands on the
  estimate).
- **From the final review:** `set_estimate_field` takes the estimate suffix
  too ("set the title to X on E0042") and its value is lazy; every dictated
  value passes through `clean_value()` (curly quotes, one trailing
  please/thanks, wrapping quotes — linear, no regex). A "yes" followed by a
  closed list of confirming tails ("Yes, go ahead", "yes, delete it") is a
  yes (`is_affirmative_text`); "yes, link it to Bob" still carries a value.
  "… in the catalog" is never a line on the open work item.
- **From user testing (2026-09-25):** `add_work_item` takes "to it / this /
  that" (a pronoun reference, routed to the estimate only while no other
  record is in focus); `add_described_work_item` — "add a work item[ to <ref>].
  <what the job is>" — prices the description as new work. A command's
  domain comes from its first sentence (`command_sentence`); later sentences
  are the job's description.

## 5. Components

### 5.1 One decider for open questions

`platform/routers/agent_helpers/open_question.py` is the only code that
decides whether a message answers Maple's pending question. Every pending
record stores its expected answer type:

| Type | Used by | Counts as an answer | Anything else |
|---|---|---|---|
| `yes_no` | delete/update confirmations, removals, `use_active_estimate`, stale-target confirmations | yes / no / cancel as the whole message (a trailing courtesy word allowed) | drop the question; handle as a new message ("yes, add a note to work item 2: …" is a new message) |
| `pick` | "which work item?", "which estimate?" menus | an ordinal or number in range, an exact row label, a phrase of at most five words whose content words all appear in exactly one row's label ("the patio one"), an E-code among the candidates, cancel | drop; new message |
| `value` (typed) | `awaiting_value_for` with a numeric/percent/money/status/division field | a value that parses as the type, cancel | drop; new message |
| `value` (free text) | description, note body, work-item name | any text, **unless** it matches a §4 command, contains an E-code, ends in `?`, or is an unambiguous command for another domain by the orchestrator's existing rule (`is_unambiguous_command`: a leading imperative verb naming one domain) | drop; new message |

One call, `decide(message, pending) -> Answer | NewMessage | Cancel`, runs in
the router before orchestration. It owns every **Estimate Agent** pending
record and the `pending_estimate_fuzzy_confirmation` yes/no. It replaces,
for those: the router's awaited-value override and pending fallback, the
agent's `answers_open_question` / `_abandons_value_prompt`, the
orchestrator's `_answers_estimate_question`, and `fuzzy_confirmation`'s
repeat-the-question branch. The `policy_refusal` flag is deleted outright.
No question traps later messages; an unanswered question is dropped.

Other agents' pending records (Task/Contact awaited values, Property missing
details) keep today's path — the awaited-value override and the pending
fallback — because their routing is out of scope (§2). Only the
`policy_refusal` suppression is removed from that path (#15).

For a value prompt or a menu, a plain "no" / "not now" / "maybe later"
cancels, like "cancel". The router answers every cancel itself ("No
problem, I've left it as is."), so no agent's own cancel pattern can
disagree. Only the newest pending record is open: an Estimate question
behind a newer question from another agent is not.

A free-text answer's reply always names where it went ("I've set the
description of Patio (E0042) to '…'").

### 5.2 Target resolution and freshness

Each request increments `turn_index` in the conversation context. Anchors
record the turn they were set: `active_estimate_set_turn`,
`active_work_item.set_turn`.

Every write batch the executor receives carries `target_source`:

| `target_source` | When |
|---|---|
| `named` | The message named the record: E-code, title, row label, ordinal against a recorded list |
| `fresh_anchor` | The target is an anchor set on this turn or the previous one, **or** the estimate the portal page currently shows (`viewed_estimate` equals the anchor) |
| `stale_anchor` | Any other anchor |

The executor applies `named` and `fresh_anchor` batches and names the target
in the reply. Listed commands whose handlers write without the executor
(add a work item, title, description, notes, status, recurring, assumptions,
property link) get the same estimate check in the shared resolver seam
(`_stale_anchor_question`, final review I1); "yes" re-runs the message with
the estimate forced. An answer to Maple's own optional follow-up is pinned to
the estimate Maple asked about. It turns a `stale_anchor` batch — and any `remove_work_item` or
delete, whatever its source — into a `yes_no` question through the existing
`edit_commands` confirmation path. A pronoun (`it`, `that one`) resolves to
the anchor with the higher `set_turn`, work item or estimate.

Resolution order for a reference is the parent plan's (code → title →
recorded-list pick → anchor → "which?"), with one change: estimate-level
commands (`set_status`, `rename_estimate`, `get_estimate`) resolve a name as
an estimate title first; a work-item reading of a name applies only to
work-item commands. When both readings match, Maple asks.

**A listed command's target is its parsed reference** (amended after review
round 9). The grammar records how each core entry named its estimate —
`ListedCommand.estimate_ref`: `code`, `title` (with `job` for "the <x> job"),
`this`, `pronoun` or `none` — and `_resolve_listed_estimate` resolves from
that alone: a code is that estimate; a title is matched as a title ("the
patio job" may be the open estimate's work item, a title matching nothing
offers the open one); `this` / `pronoun` / `none` are the anchor, labeled for
the freshness step. The message text is never re-read for a core entry's
target, so an estimate code or title inside a dictated value, a leftover
"to", or a suffix can no longer move a write. Only the ported entries, which
have no slots, still read text — with their value blanked, never cut. "the
current/same work item" parses as "this work item".

The grammar's reference contract is pinned as a matrix
(`test_every_placement_parses_every_estimate_reference_exactly` in
`tests/test_command_grammar.py`): every placement (main reference, mid and
trailing suffix, note target) × every way of naming an estimate (code, spoken
or `#` code, title, "the <x> job", this / the current / the same / the
estimate, the latest / second). A parse either misses (the planner or
classifier takes it) or yields exactly that reference, and the dictated value
never carries it. One reference is folded whole — main, else suffix a, else
suffix b — and a later suffix is given back to the value it follows. A new
reference form or placement is added to the matrix, not tested one phrasing
at a time.

### 5.3 Routing

- **Orchestrator**: a §4 command routes to the Estimate Agent by rule. A
  message naming another domain routes as today. Everything else goes to the
  LLM classifier, whose input now includes a short summary of what is open
  (estimate code/title, work item label, pending question type). Removed:
  `_is_work_item_edit`'s anchor-only branches, `_answers_estimate_question`,
  the last-touched gate, and — in the history lane
  (`_resolve_intent_with_history`), which serves every domain — only the
  estimate domain: when history resolves to `estimate`, the lane defers to
  the classifier. Other domains keep the lane.
- **Policy guards** (`is_bulk_delete_request`, `is_equipment_request`) run
  once, in the orchestrator, on the command head only, and never on a message
  the open-question decider accepted as an answer. The Estimate Agent's
  duplicate guard is deleted.
- **Estimate Agent**: `match_command` first; an unmatched update goes to the
  planner once an estimate is resolved, or to "Which estimate?". The loose
  detectors in `work_item_edit_detectors.py` and the legacy cascade branches
  that overlap §4 are deleted; the detectors that remain are only the ones §4
  names.
- **Planner prompt** gains: effort in hours only (ask when the user gives
  days/weeks), a stated cost is `material_cost`, and each command must carry
  the target it resolved. The regex cost backstop in `edit_planner.py` is
  deleted.

### 5.4 Safety at the write

- The Draft/Review lock is checked in the executor and in every router write
  path, including `run_update_estimate`'s add-items path, before generation
  and again before persisting.
- Delete permission (`may_delete_estimate`) is checked before Maple asks to
  confirm, and again after; a refusal returns `success=False`.
- Per-turn keys never persist: `filter_by` and `property_id` join
  `TRANSIENT_KEYS`; `property_id` is set only from `request.property`.

### 5.5 The routing snapshot

`platform/tests/maple_routing/` holds the corpus (the 935 phrasings of the
sixth-pass sweep, plus every phrasing quoted in the sixth-pass ledger and in
follow-ups #627–661), the states, a runner, and `snapshot.json`.

**States (7):** nothing open; estimate open; work item open; another domain
last touched; value prompt pending; pick menu pending; yes/no pending.

**Two layers**, both rules-only, with the classifier and planner replaced by
a `DEFERRED(classifier|planner)` marker:

1. **Routing** — `OrchestratorAgent(use_llm=False).process` over the four
   anchor states (the sweep harness's method): intent and agent.
2. **Grammar** — core `match_command` over the corpus: command id.
3. **Decisions** — `open_question.decide` over the corpus for each of the
   three question kinds: answer / new message / cancel.

Layer 1 is recorded from step 0. Layers 2 and 3 are recorded from the step
that creates their module (2 and 3): today's reply-or-new decision is spread
over five components and is only observable end to end, so step 0 covers the
pending states with `expected` rows instead of a recording.

**Row kinds:** `expected` rows assert behavior this spec requires (every
finding's phrasing is one); `recorded` rows capture current behavior and
change only with `--update-snapshot`, whose diff is reviewed. Target: under a
minute on the local Mongo.

## 6. What review checks (the `/code-review` contract)

Added to `.claude/commands/code-review.md` as a Maple section:

> A Maple phrasing issue is a finding only when one of these holds:
> 1. A rule accepts input outside its entry in `command_grammar.py` (or the
>    open-question table in `open_question.py`).
> 2. `snapshot.json` changed without an intentional `--update-snapshot`, or an
>    `expected` row fails.
> 3. A misread can reach a write without the §5.2 step — a stale or guessed
>    target written without confirmation, or a write that doesn't name its
>    target.
>
> A phrasing Maple doesn't support is a **gap**: record it in the phrasing
> reference (⚠️), never as a finding. Do not invent phrasings to probe the
> planner or classifier; the Tier 2 live suite covers them.
>
> **Known findings are not new.** Before reporting, check
> `documentation/development/code-review-followups.md`. A finding already
> logged there, at the same place and for the same cause, goes under an
> unnumbered "Already tracked" list with its follow-up number, not in the
> numbered findings. The same applies to a finding in the previous ledger
> that `/fix-issues` logged.

Every other part of `/code-review` (security, data integrity, portal,
tests, size) is unchanged.

## 7. Build order

Before each step: patch backup of platform, portal and documentation to the
session scratchpad. Each step: TDD; scoped `./run_mypy.sh` and `./run_ruff.sh`;
related tests; the snapshot diff shows only intended rows.

| Step | Work | Closes |
|---|---|---|
| 0 | Build `tests/maple_routing/` from the sweep harness; record layer 1 for today's tree as the baseline; mark finding phrasings `expected` (failing ones marked xfail with the finding number) | — |
| 1 | Fixes that don't depend on the redesign (§8.2, §8.3). Snapshot must not move | #1, 6, 7, 9–12, 18, 23–32, #653 |
| 2 | `command_grammar.py`, not yet wired; accept/reject tests per entry | — |
| 3 | `open_question.py`; wire into the router; delete the five replaced deciders | #4, 15, 19 |
| 4 | `turn_index`, `set_turn`, `target_source`; executor confirmation for stale targets and removals; pronoun resolution | #20 |
| 5 | Estimate Agent on `match_command`; delete loose detectors and overlapping cascade branches; tests pinning removed phrasings become "goes to the planner" (fake planner) plus snapshot rows | #3 (agent), 5, 17, 22; #2, 21 (handler) |
| 6 | Orchestrator routing (§5.3); guards on the head, once; delete the agent's guard; classifier prompt state summary; `/agent-prompt-review` | #2, 3, 8, 13, 14, 16, 21 |
| 7 | Planner prompt (§5.3); `/agent-prompt-review`; one Tier 2 live run of the finding phrasings plus a corpus sample through the real classifier and planner (a few minutes, under $1) | confirms 5–6 |
| 8 | Phrasing reference (rule table = §4, gaps), `CLAUDE.md` Maple section, the `/code-review` contract (§6), follow-up closures (§8.4), #4 size rows | — |
| 9 | Simon runs the full suite; `/code-review`; `/fix-issues <Simon's selection>`; repeat until a round reports no new findings (§2) | done |

## 8. Planned resolution of the sixth-pass findings

### 8.1 Removed by the redesign (14)

| # | Resolution |
|---|---|
| 2 | `add_note`'s target list excludes other named records → classifier; the estimate note handler refuses a head naming another record |
| 3 | `add_note` accepts the closed lead list; `create_estimate` requires its own grammar |
| 4 | Free-text value rule in §5.1 (command, E-code or `?` releases); reply names the target |
| 5 | Estimate-level commands resolve names as titles first (§5.2) |
| 8 | Anchor-only claim deleted; catalog names route to their domain or the classifier |
| 13 | Agent guard deleted; the orchestrator guard skips answers |
| 14 | Guards read the command head only |
| 15 | `policy_refusal` flag deleted with the pending fallback |
| 16 | Last-touched gate deleted; `set_percentage` / `set_gross_margin` are listed commands |
| 17 | Regex cost backstop deleted; the planner's schema and prompt handle cost |
| 19 | No question traps later messages (§5.1) |
| 20 | Pronoun → most recent anchor; removals always confirm (§5.2) |
| 21 | `add_note` only reaches note-capable records; materials and roles get "Materials and roles don't take notes." |
| 22 | Effort by rule is hours only; other units and unit-mismatched quantities go to the planner, which asks |

### 8.2 Server fixes (10)

| # | Fix |
|---|---|
| 6 | Swap only the best-scoring line (≥85 or exact head noun) within the assumption's work item; ask when several are close |
| 7 | Lock check on the router's add-items path, before generation and before persisting |
| 9 | `filter_by` in `TRANSIENT_KEYS`, popped at load |
| 10 | `property_id` in `TRANSIENT_KEYS`, set only from `request.property`; the follow-up link writes `active_property_id` |
| 18 | `may_delete_estimate` before the confirmation; `success=False` on refusal |
| 23 | `work_item_breakdown` excludes legacy `labours`; readouts computed at burden 0; parity tests on both sides |
| 26 | Delete cleanup deferred through `BackgroundTasks` from the orchestrate endpoint |
| 27 | Owner compared case-insensitively; user id threaded into the audit entry |
| 29 | Reply line when company defaults couldn't be read |
| 30 | `exc_info=True` on both log calls |

### 8.3 Portal fixes (8)

| # | Fix |
|---|---|
| 1 | A work-item save or delete fetches the latest estimate, changes only its own item by `JobItem.id`, and sends `base_version`; a 409 re-fetches and re-applies |
| 11 | `setIsDirty(false)` after `persistWorkItems` succeeds |
| 12 | Raw items matched by id in `persistWorkItems` and `handleSaveEstimate` |
| 24 | try/catch: restore rows, show the error, no unhandled rejection |
| 25 | Match the deleted estimate; if it is this one, unload and navigate to `/estimates` |
| 28 | Rollback only while `guard.isLatest(seq)` |
| 31 | Clear `saveError`, `formError`, `workItemDialogError` on switch |
| 32 | Focus Retry; add "Back to Estimates" |

### 8.4 Earlier follow-ups

- **Closed by the redesign and replaced with snapshot rows (20):** #627,
  628, 629, 630, 632, 633, 634, 636, 637, 642, 643, 646, 647, 648, 649, 650,
  652, 656, 657, 658.
- **Fixed in Step 1:** #653.
- **Not touched:** #631 (the PUT's old rounding) — its entry awaits Simon's
  decision because it changes the totals the HTTP API stores.
- **Stay logged, non-blocking:** the remaining LOW/MEDIUM entries from
  #611–661.

## 9. Risks

| Risk | Mitigation |
|---|---|
| More behavior depends on the LLM, which Tier 1 doesn't exercise | Step 7 live run; stale targets become questions; every write names its target |
| Latency and cost on long-tail turns | ~one worker-model call on turns the rules don't handle; answers and listed commands stay rules-only |
| Common line edits (materials, activities) now always use the planner | Accepted in D1; revisit by adding a §4 entry (with snapshot rows) if Tier 2 shows the planner is slow or wrong on them |
| A large rewrite on an uncommitted tree | Patch backup per step; the snapshot shows each step's effect |
| Rewritten tests lose their intent | Each becomes an `expected` snapshot row |
| `turn_index` freshness is wrong for a long page session | The page's `viewed_estimate` counts as fresh while it equals the anchor |

## 10. What not to do

- Don't add a regex outside `command_grammar.py` to fix a routing finding.
  Either add a §4 entry (with snapshot rows and a phrasing-reference row) or
  leave the phrasing to the classifier/planner.
- Don't let a component other than `open_question.py` decide reply vs new
  message.
- Don't write to a stale or guessed target without the §5.2 question.
- Don't update `snapshot.json` without reviewing the diff.
- Everything in the parent plan's "What NOT to do" still holds.
