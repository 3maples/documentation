# Maple multi-turn everywhere — design

**Status:** Approved 2026-09-27 (decisions below). Implementation in progress.
**Scope:** platform (router, orchestrator, every domain agent) and portal (Maple panel, page signals).
**Builds on:** [2026-09-23 multi-turn estimate editing](2026-09-23-maple-estimate-multi-turn-editing.md),
[2026-09-25 routing convergence](2026-09-25-maple-routing-convergence-design.md).

## 1. Why

A read-only review on 2026-09-27 (seven reviewers, then four more probing ~1,500
rules-tier conversations across every page) found that multi-turn conversation
works well for estimate **work items** and poorly everywhere else. The failures
are not missing regexes one at a time; they come from eight mechanisms that the
estimate side has and nothing else shares:

| # | Mechanism | Estimate side today | Everywhere else today |
|---|---|---|---|
| 1 | Questions Maple asks (yes/no, which-one, what-value, follow-ups) | `open_question.decide`: answer / cancel / new message; unanswered drops | seven statement-ordered handlers in `routers/agents.py`; no cancel; nothing expires; stale "yes" deletes |
| 2 | Focus ("it", "this", "him", "there") | one anchor writer, freshness by turn, portal page signal | anchors never go stale; no pronoun→domain mapping; templates/notes don't move focus |
| 3 | A written command list | `command_grammar.py` | keyword regexes per agent |
| 4 | List memory | rows recorded | rows only — no filter, age, total; stale lists answer "the second one"; filters silently dropped |
| 5 | "What about X?" | — | — |
| 6 | Compound requests | edit batches | creates keep the first clause |
| 7 | Conversation turns (cancel, thanks, show more, language) | cancel inside a question only | fall through to a material lookup |
| 8 | Honest boundaries | — | out-of-chat features misroute (a division becomes a contact, "upgrade my plan" a material lookup) |

The same review found eight destructive or wrong-write defects (§4), three of
them already filed (#671–#673).

## 2. Decisions (owner, 2026-09-27)

1. **Build the shared mechanisms first**, then per-feature phrasings.
2. **New chat capabilities in scope:** (b) read and list notes, delete your own
   note; (c) tasks — link a property, clear the due date, unassign, assign by
   name; (f) dashboard — upcoming, due today, overdue. **Not in scope:** unlink
   contact↔property, duplicate estimate, generating the estimate document,
   calculator re-runs, settings reads.
3. **Out of chat, refused with a redirect** that tells the user where to do it
   (answer drawn from the user guide): company default percentages, team and
   invitations, billing/plan/credits, Load Standard, CSV import, category /
   unit / division management, template create/edit, equipment, and every
   not-in-scope capability above (unlink, duplicate, documents, settings reads).
4. **Every delete asks first**, even with a clearly named target.
5. **A question lives one turn.** Unanswered, it is dropped; "cancel" or any new
   request also drops it.
6. **#667 won't fix:** a note only the edit planner can parse stays refused on a
   locked estimate; users add those notes in the app.
7. **Planner-only estimate phrasings get grammar entries now** (not just a doc tag).
8. **HIGH items may be done together** in this push — the one-HIGH-per-session
   rule is suspended for it — with the churn guards in §3.
9. Material/labour write breakage is confirmed by a test with auth enabled.

## 3. Churn guards (the estimate work took 34 review rounds)

1. **Acceptance corpus first** (§6). Every behaviour change lands with a
   conversation row; a known gap is an `xfail(strict=True)` row naming its
   follow-up number, so a fix flips it and cannot land silently.
2. **The routing snapshot** (`tests/maple_routing/`) is re-recorded only after
   reading its diff (`UPDATE_MAPLE_SNAPSHOT=1`), and every changed row is
   explained in the commit message.
3. **One mechanism per concern.** No new regex outside a command list or a
   shared helper in `agents/text_utils.py` / `agents/conversation/`.
4. **Safety defaults are global, not per agent:** deletes ask; questions last one
   turn; a stale target asks; a refusal ends the turn.
5. **Rules decide what they parse; the LLM decides the rest; a weaker rule never
   overwrites a correct LLM answer** (#690).
6. Each item: failing test first, related test files + snapshot + corpus, mypy
   and ruff scoped, one commit, tracker entry marked RESOLVED in the same commit.

## 4. Safety fixes (Phase A)

| # | Defect | Fix |
|---|---|---|
| 674 | `_is_confirm_text` substring test — "delete it" deletes at once; "no, don't delete it", "Yesler", "Reyes" confirm | delete the helper; the first delete request always asks; confirmation only through the question registry (§5.1) with normalized yes/no |
| 675 | catalog/task/template delete confirmations never expire, no cancel, confirm-time load unscoped | registry expiry + cancel; company-scoped loads |
| 676 | an awaited field value captures every later message | registry `value` kind: commands, codes, questions and cancel release it |
| 677 | stale anchors / pronoun domains / stale lists write to the wrong record | focus model (§5.2) + list memory (§5.4) |
| 678 | material/labour writes call route functions without the user | pass the verified user; keep the manager gate on delete |
| 679 | "remove X from Y", "delete that note" delete the parent | no delete when the message names two records or a note; unlink → redirect; note delete → notes capability |
| 680 | Maple writes a material's price equal to its cost | cost is cost; price derived server-side; ask which size when several |
| 681 | a refusal is overridden by an unfinished create | refusal ends the turn and drops the pending create; unknown category/unit refused, never created |
| 671 | stale estimate yes/no | registry expiry (covers all eight writers of the fuzzy key) |
| 672 | task title with a recency word resolves to the newest task | recency only when the reference is nothing but recency words |
| 673 | address-style estimate names drop the house number (+#334) | strict/loose extractors keep the number; ladder rung 3 digit guards |

## 5. Shared mechanisms (Phase B)

### 5.1 One question registry

`agents/conversation/questions.py` declares every kind of pending state as data:

```
QuestionKind(key, kind, owner, detect(context) -> record|None, drop(context), answer(...))
kind ∈ {"yes_no", "pick", "value", "flow"}
```

It covers the Estimate yes/no and records, every agent's `pending_intents`
record (with its `pending_delete_<domain>_*` companion keys), task
confirmations, status offers, gathering, template size, property link, the two
follow-up machines, and pending calculations. The router's seven
statement-ordered handlers become **answer dispatchers** behind one gate:

1. At turn start, for each open question (newest first) `decide(message)`:
   - `yes_no`: normalized affirmative → ANSWER; negative / cancel → CANCEL
     (unless the kind declares that "no" is an answer); anything else → NEW.
   - `pick`: ordinal, readable code, or a candidate's label → ANSWER.
   - `value` / `flow`: ANSWER unless cancel/negative (CANCEL), a listed or
     unambiguous command, a record code, or a question (NEW).
2. ANSWER → the owner handles it. CANCEL → every open question drops;
   "Okay — I've left it as is." NEW → every open question drops; the message
   is classified normally.
3. **Finalize** stamps `asked_turn` on each open question; a question whose
   stamp is older than this turn and that the router did not dispatch an answer
   to is dropped. One turn, for every kind — no per-path release calls.
4. A turn never ends with a delete confirmation beside another question; the
   delete is dropped and the reply says to ask again on its own.

`open_question.py` becomes the Estimate entries of this registry. The awaited
value override and the pending fallback in `routers/agents.py` are deleted.
Closes #436 (the registry it asked for), #671, #675, #676, and the traps in #683.

### 5.2 Focus

- Every `active_<domain>_id` gets `active_<domain>_set_turn`; templates and
  notes record focus too.
- Pronoun → domain: him/her/his/hers/she → contact; there/that place →
  property; it/this/that/its → the freshest anchor of the command's domain,
  else the freshest overall.
- A **write** through a stale anchor (older than the previous turn and not the
  page the user is on) asks "Did you mean Ana Reyes?" — a `yes_no` question
  that replays the request on "yes" (the estimate `use_active_estimate`
  pattern, generalized).
- A deleted record's anchor is cleared; a dangling anchor asks, never falls
  back to recency.
- Portal: `client_context.viewed_record = {type, id}` for property, contact,
  task, material, labour and template pages, applied the way
  `apply_viewed_estimate_signal` is (a new visit wins).

### 5.3 Command lists per domain

Tasks first (due-date verbs, status verbs, assign/unassign, property link,
readable ids, positional and anchored forms), then catalog "set its price" /
"what's its rate" forms. Same contract as `command_grammar.py`: an entry with
accept/reject tests and a phrasing-reference row.

### 5.4 List memory

`last_listed_items` gains `domain`, `filter` (human-readable), `total`,
`offset`, `recorded_turn`. Every list render records (an empty list clears).
A positional **write** is honoured only when nothing else has taken focus since
the list; otherwise Maple asks. "show more / the rest / next page" re-runs the
list at `offset + page`. Lists say "Showing 20 of 57". A filter phrase the list
cannot apply is named in the reply ("I can't filter tasks by priority yet —
here are all of them"), never silently dropped (#687).

### 5.5 "What about X?"

`last_request = {message, target_text, intent, agent}`. "what about X", "and X?",
"same for X", "and last month?" rewrite the previous message with `target_text`
replaced by X (or its date range replaced) and run it through the normal
pipeline.

### 5.6 Conversation turns and language

A meta layer ahead of classification: cancel / never mind / forget it (drop
questions; "Nothing to cancel" when there are none); thanks / ok / great with
nothing open (short acknowledgement); stray yes/no with nothing open ("I'm not
waiting on an answer — what would you like to do?"); repeat that; show more
(§5.4); start over / clear chat (point to the panel's clear button).
`conversation_lang` is persisted; short replies in a non-English conversation
are translated (#688).

### 5.7 Honest boundaries

`agents/conversation/out_of_chat.py`: one table of capability → detector →
redirect answer (page, tab, user-guide section). Replaces today's misroutes.

## 6. Acceptance corpus

`tests/maple_conversations/` — multi-turn conversations run through the real
`/agents/orchestrate` endpoint (TestClient, local Mongo, a seeded company),
rules tier (`use_llm=False`, planner off, guide LLM stubbed). Each conversation
has a feature, a pattern (M1 follow-up on the shown record, M2 compound, M3
positional, M4 answer a question, M5 correction, M6 cancel/pivot, M7 cross-
feature, M8 read-after-write, M9 "what about X", M10 list refinement, M11
partial create) and per-turn expectations: route, reply fragments, and database
checks (a record still exists, a field's value). Known gaps are
`xfail(strict=True)` with their follow-up number.

## 7. Per-feature work (Phase C, in order)

1. **Tasks** — delete/convert confirmations and menus through the registry;
   value questions (assignee, status, date) resumable; due-date and status verbs
   on the anchored / positional / coded task; create with due, assignee,
   property and status clauses; filters (status, overdue, due window, property,
   assignee by name/email — fix the `.` regex); property link, clear due,
   unassign, assign by crew name; list paging; details show property, estimate,
   photo count; to-do / remind-me creates.
2. **Estimates** — status / link / archive / template with "it" and no reference;
   questions about the estimate in focus (status, total, customer, property,
   markup, margin) ahead of help; several-match question stored and resumable
   (#685); listed rows ahead of the open estimate for delete/update (#686);
   "last month" is a range, not a sort (#687); filters by title / customer /
   property; list refine, sort, page, "total of those"; planner-only phrasings
   promoted to grammar entries; create phrasings ("I need a quote for…").
3. **Properties, contacts, notes** — link phrasings (the guide's own); step-by-
   step create that names missing fields and accepts "skip"; "which property?"
   answers resume the request; filters (property city with counts, contact
   role/city); person-looking property names; post-create follow-ups for every
   field; notes read/list and delete-own (with confirmation).
4. **Materials, people, templates** — "its/it" follow-ups; multi-word sizes;
   several-size reads and "which size?"; category move by name; people list
   ("roles"); "Heavy Equipment Operator" is a role, not equipment; "the X
   template" and bare-name replies.
5. **Dashboard** — upcoming / due today / overdue; pipeline and backlog
   phrasings to the analytics handlers; "and last month?" via §5.5.
6. **Out-of-chat redirects** (§5.7) for everything in §2.3.

## 8. Portal (Phase D)

`viewed_record` signal on every record page; "Waiting for your answer · Cancel"
strip and Yes/No chips on yes/no questions; quiet refresh (no remount) on
catalog pages after Maple writes; refresh events for template-created estimates,
template deletes, the dashboard and the property activity panel; restored
history not wiping a message sent before the restore finished.

## 9. Documentation

- The phrasing reference's change log moves to
  `maple-phrasing-changelog.md`; the reference keeps a short "recent changes"
  list and gets per-section "Open gaps" tables citing follow-up numbers.
- Each phase re-verifies the sections it touches against the corpus.
- CLAUDE.md's Maple section describes the registry, focus model and list memory
  once they land.
