# Maple planner, shadow comparison and unanswered tracking: design

**Date:** 2026-10-02 · **Revised:** 2026-10-07 (Maple changes of 2026-10-02 → 10-06; decisions D6–D19; the unanswered tracker, §9; prompt caching, §5.1; parity with today's phrasings, §4.5 and Appendix A; gap review, §15)
**Status:** Approved 2026-10-07 (D1–D19). Steps 0–11 built 2026-10-07. **Revised the same day (D20): the comparison runs in Dev only; switchover in Dev, then production** — the switchover plan is [`2026-10-07-maple-planner-switchover-plan.md`](2026-10-07-maple-planner-switchover-plan.md).
**Builds on:** [`2026-09-25-maple-routing-convergence-design.md`](2026-09-25-maple-routing-convergence-design.md),
[`2026-09-27-maple-multi-turn-everywhere-design.md`](2026-09-27-maple-multi-turn-everywhere-design.md)
**Decided with Simon:** 2026-10-02 (D1–D5) and 2026-10-06 (D6–D17) and 2026-10-07 (D18–D20), in the architecture-review session

## 1. Why this exists

Today a Maple turn is read by about twenty components in turn: the question
gate, a growing set of router pre-handlers, ten pending-flow handlers, fourteen
orchestrator rule matchers, the LLM classifier, `_prefer_explicit_rule_match`,
the history lane, the low-confidence fallback — and then each domain agent
classifies the message again. The first one to claim the message wins. This
has three costs that more rules cannot remove:

1. **Precedence is implicit.** A fix in one reader moves the boundary of
   another. The routing convergence work took 34 review rounds; the multi-turn
   work needed a 1,216-phrasing snapshot to stay still.
2. **Several intents in one message cannot work.** An intent is a label, not a
   parse. `_match_unambiguous_command` claims the first clause; with several
   LLM matches, each agent receives the whole message and parses it again.
3. **The rules don't save LLM calls.** A routine Property/Contact/Material/
   People turn already makes 2–3 calls (the agent's own classify, extract,
   accuracy suggestions), and 3–4 when the rules miss. The regex layer is
   English-only, so non-English turns also pay for the translation sandwich.

**The week this draft sat in review shows the pattern.** Between 2026-10-02 and
10-06, sixteen Maple commits added a tax follow-up pre-handler
(`tax_followup.py`, a new reader ahead of "what about X?"), a status-list
grammar (`status_lists.py`), tax words (`tax_words.py`), rolling windows
(`time_windows.py`), division and type-of-work scopes (`work_scope.py`) and an
overage question. Regex call sites went from 877 to 900 and the Maple code from
60.2k to 61.9k lines. And the two parsers of one question drifted:
`MetricAsk` (what the grammar reads) gained status sets, `work`, `recurring`,
status-breakdown `rows` and line totals, while `MetricSpec` (what the LLM tier
fills) has none of them — so a metric question the grammar misses can no
longer be answered as fully by the fallback.

Meanwhile the LLM is not the weak reader: on the coverage matrix the live tier
scores 173/182 against the rules tier's 192/206, and it wins on implicit and
field-targeted phrasings — the ones the rules keep growing for. And one corner
of Maple already works the way this design proposes: the estimate edit planner
emits typed `EditCommand`s (`edit_commands.py`) that one executor validates
and applies all-or-nothing (`edit_executor.py`).

This design generalizes that pattern to every Maple turn — **the LLM plans,
the code decides** — proves it against the current pipeline on real traffic
before any customer is switched, and, alongside, records every turn Maple
could not answer (§9).

## 2. Decisions

| # | Decision | Chosen | Rejected |
|---|---|---|---|
| D1 | How to compare | **Shadow comparison only**: the current pipeline answers every turn; the planner runs beside it, dry-run, and both are logged | A/B split of users (needs traffic we don't have, and exposes users to the unproven path) |
| D2 | What is logged | **Every session, one md file per session**, for review | Automated scoring, an LLM judge |
| D3 | How long | ~~**Two weeks** with shadow on, then review~~ — superseded by D20: until the planner is clearly better in Dev | Open-ended |
| D4 | How it's judged | **Manual review** of the session files by Simon; no conversation replay | Replaying the corpus conversations end to end |
| D5 | Switchover | **Company by company**, behind a per-company setting, and only if the review finds the planner much better; otherwise the current pipeline stays and the planner keeps improving | Big-bang cutover |
| D6 | What shadow builds | **The real planner, resolver and policy**; only the executor is missing (was P3) | A throwaway prototype |
| D7 | Privacy | **No privacy constraints on the logs**: full emails, verbatim messages; exports go wherever Simon chooses | First names only, refusing in-repo output paths |
| D8 | Which companies | ~~**All companies**, including 3Maples' own and demo companies~~ — superseded by D20: Dev's companies only, narrowed by `MAPLE_SHADOW_COMPANIES` when wanted | Customers only |
| D9 | Unanswered turns | **Recorded, with the message and the reason** (§9); each is reviewed as a valid response or a gap | Not tracked |
| D10 | What a session is (was P1) | **One whole conversation**: from a user's first message until they press Clear (which deletes the conversation) or it expires after 30 idle days — never split by time, so the file shows everything the conversation carried. Each turn's file entry shows its tokens, cached tokens and credits (§10.2). The 30-day expiry is Mongo's TTL on `ConversationContext.updated_at`: it deletes the whole document — history, anchors, open questions — so the panel comes back empty. Kept as is: the planner's cost doesn't grow with history (§5), so nothing argues for clearing sooner, and a user back after a month is better served by a clean panel than by month-old context | Splitting after 30 minutes idle; a shorter expiry |
| D11 | The per-company switch (was P5) | **A `Company` field, optional: missing means the current pipeline**, so no migration and no default write (§12) | An env list of company ids |
| D12 | The unanswered tracker after the window (was P6) | **Stays on**, as a standing product signal (§9.5) | On for the window only |
| D13 | Prompt caching | **Cache only the fixed part of the prompt** — one explicit breakpoint after the static block, nothing per-turn before it (§5.1); every LLM call's cached and cache-write tokens are recorded, so caching is visible across Maple | The default mode, which caches the whole prompt and pays the write premium on the part that never repeats |
| D14 | Today's Maple during the window (was P2) | *Revised by D20: today's Maple is being replaced, so phrasing work goes to the planner from now on, window or not.* **Don't change how today's Maple reads messages during the two weeks**: no new phrasings, regex or rule entries — they wait, or go into the planner. Fixes that stop data loss or a wrong write are still fine, and all other work carries on (features outside Maple's language reading, portal work, the unanswered tracker, prompt-caching changes). Otherwise the first week compares the planner with one version of Maple and the second week with another | Keep changing both during the window |
| D15 | Before the window (was P4) | **A check before turning shadow on**: run the planner once, locally, over sentences whose right answers are already written down, and read the misses. Widened by D18 | Turn shadow on without the check |
| D16 | Questions Maple asks | **A clarifying question is not an unanswered turn.** Maple asking which record, what value, or yes/no is mid-request, not a failure (§9.1) | Counting every turn that didn't act |
| D17 | Credits for cached tokens | **A cached token costs the customer less**: credits count it at the cached rate, and the Stripe meter reports the same number (§5.1) | Counting every prompt token alike |
| D18 | The parity run (was P7) | **Every corpus that pins today's behaviour, and the phrasing reference itself** (§4.5, step 11): the 1,216-phrase routing corpus in each state, the 206 CRUD-coverage phrasings, the 256 acceptance conversations replayed with the planner live, and every ✅ reference row — about 2,700 calls, under $5. No ✅ phrasing may come back `unsupported` or `not_understood`; every difference is read. Kept as the planner's regression suite, run before every prompt, schema or model change | The 125 `expected.json` rows only |
| D19 | Staleness by time (was P8) | **An anchor or remembered list older than 24 hours is stale** however few turns ago it was set, so a write through "it" asks first; **an open question older than 1 hour is dropped** — a question lives one turn, or one hour. The snapshot shows each age in turns and in time (§6). For today's Maple the same rule is a separate follow-up | Turns only, as today |
| D20 | Where the comparison runs (2026-10-07) | **Dev only, then switch over in Dev, then production.** Shadow runs in Dev on Simon's own traffic; the parity suite is the measure, and every phrasing worth keeping becomes a reference row. When the planner works clearly better than today's Maple in Dev, the switchover (§12) is built and used in Dev first; production follows company by company. Phrasing refinements go into the planner only — today's Maple gets fixes for data loss, wrong writes and production bugs. Supersedes D3, D8, §11's window and step 12 | The two-week production window (D3, D8) |

## 3. The new pipeline

```
message + state snapshot + last turns
        │
        ▼
   Planner   one structured-output call ──►  Plan
        │
        ▼
   Resolver  every reference → a record of the caller's company, or a question
        │
        ▼
   Policy    permission · Draft/Review lock · deletes ask · stale targets ask · overage asks
        │
        ▼
   Executor  today's handlers, one write path per domain     (not in shadow)
        │
        ▼
   Reply     templates that name every target               (not in shadow)
```

New code lives in `platform/agents/planner/` (`schema.py`, `snapshot.py`,
`planner.py`, `resolve.py`, `policy.py`, later `execute.py`). The shadow
recorder is `platform/services/maple_shadow.py`; the unanswered tracker is
`platform/services/maple_outcomes.py` (§9).

**Kept as they are, and reused:** server-owned `ConversationContext`; focus
anchors and their turn stamps (`agents/conversation/focus.py`); list memory;
the "a question lives one turn" rule; delete confirmation; the overage
question (`overage_confirmation.py`, `services/estimate_quota.estimate_bills_overage`);
company-scoped name lookups — since 2026-10-04 indexed queries rather than
catalog loads (`catalog_names`' five-collection exact-name lookup,
`title_reference.find_named_estimates`, `contact/utils.find_contacts_by_name`,
`named_answers.NAME_SOURCES`, `dependencies.assert_company_refs`); the metrics
engine and its readers' value types (`MetricAsk`, `metric_periods`,
`tax_words`, `status_lists`); the edit executor; the estimate generation
pipeline (it becomes the executor of `create_estimate`); `DataFence`; the
corpora.

**Replaced at switchover, not before:** the router pre-handlers'
language-reading (including `tax_followup`'s and `followup`'s detectors),
`decide_turn`'s heuristics, the orchestrator ladder and classifier, each
agent's own classify/extract calls, `command_grammar.py`, and `metric_spec.py`. *The translation sandwich stays, both ways (Simon,
2026-10-07): the planner reads any language, but its stray-reply check, the
history and the reports are English, and the replies are English templates.*

## 4. The plan

### 4.1 Shape

```
Plan
  actions:     list[Action]          at most 5, run in order
  clarify:     str | None            a question to ask instead of acting
  unsupported: Unsupported | None    what Maple won't do, and why
  answers_open_question: bool        this message answers the question Maple asked
  reply_language: str                ISO code of the user's language
```

Exactly one of `actions` (non-empty), `clarify` or `unsupported` is set.

This is the whole of what the model returns — one function call whose
arguments are a `Plan`. Everything the executor needs to act must be inside
an `Action`; nothing is re-read from the message afterwards. So every action
carries three things:

```
Action
  op:      Literal[...]           what to do        — the discriminator
  domain:  Literal[...]           what kind of record (where the op isn't domain-specific)
  target:  RecordRef              which record       (§4.3; absent on create and list)
  …        the op's own fields    the details        — typed, enumerated, bounded
```

The details are never a free `Dict[str, Any]`, as today's per-agent
`LLMClassification.fields` is. Each domain's `update` and `create` carry a
`fields` model whose keys are that domain's allowlist as `Literal`s — today's
`CONTACT_ALLOWED_FIELDS` (`phone`, `email`, `street`, `city`, `prov_state`,
`postal_zip`, `country`, `role`, `middle_name`…), `PROPERTY_ALLOWED_FIELDS`,
and so on — with `extra="forbid"`, so a value can only land on a field that
exists. An `update` must set at least one field (as `UpdateMaterial` already
requires). Money, quantities and percentages are numbers with bounds; a date
is an ISO date — the snapshot states today's date in the user's timezone
(`client_context.timezone`, `agents/local_time.py`) so "next Friday" is
resolved by the model from a known today, not by a date regex in code.

**Worked examples.** The user's own case first:

> *update the phone number for Bob Jones to 555-123-4567*

```json
{"actions": [
  {"op": "update", "domain": "contact",
   "target": {"by": "name", "text": "Bob Jones"},
   "fields": {"phone": "555-123-4567"}}
 ],
 "answers_open_question": false, "reply_language": "en"}
```

The resolver finds the company's contact named Bob Jones (asks if there are
two, says so if none); the policy marks it `would run` (a named target, no
confirmation needed); the executor calls today's contact update with
`{"phone": "555-123-4567"}` and replies with the existing template.

> *add a contact Mark Liu, 555-0142, and link him to 14 Birch Rd*

```json
{"actions": [
  {"op": "create", "domain": "contact",
   "fields": {"first_name": "Mark", "last_name": "Liu", "phone": "555-0142"}},
  {"op": "link", "from": {"by": "step", "n": 1},
   "to": {"domain": "property", "by": "name", "text": "14 Birch Rd"}}
 ], …}
```

> *what did we sell to Ridgeline last quarter, before tax?*

```json
{"actions": [
  {"op": "metric", "metric": "total", "statuses": "sold",
   "subject": "Ridgeline", "period": {"kind": "last_quarter"},
   "before_tax": true}
 ], …}
```

> *(Maple asked "Which work item — 1 Patio, 2 Fence?")* — *the fence one*

```json
{"actions": [{"op": "answer", "pick": 2}],
 "answers_open_question": true, …}
```

### 4.2 Actions

A union discriminated on `op`, every model `extra="forbid"`, with length and
range limits as in `edit_commands.py`. Grouped by what they touch:

| Group | Ops |
|---|---|
| Records — property, contact, material, people (labour), task, template, **estimate** | `create`, `update` (field → value, with `append` for a task's notes), `delete`, `get` (optionally one `field`: "what's its status?", "what's the total of E0042?"), `list` (filters), `count` — each carries `domain`; a domain gets only the ops it supports today (`SUPPORTED_INTENTS_BY_AGENT`); a material op takes a `size`; `list material_category` is the category list |
| Links | `link` / `unlink` between two records (contact↔property, estimate→property, task→property) — `unlink` maps to today's out-of-chat redirect |
| Notes | `add_note`, `list_notes`, `delete_note` on a property, contact, estimate or work item |
| Estimates | `create_estimate` (scope text → generation pipeline; or a `template` ref with a `size`), `set_status` (archive included), `apply_template`, `generate_work_item`, `adjust_assumption` ("use premium pavers instead", "make it 300 sq ft"), `set_recurring`, `edit_estimate` — which carries **today's `EditCommand` list unchanged**; estimate `list`/`count` filters take a status **set**, a division, recurring/one-time, a time window, and a cross-record filter (a material, a role, a contact or a property the estimates use — `cross_resource.estimate_line_filter`), as the grammar now does |
| Work items (reads) | `list_work_items`, `get_work_item`, `work_item_field` (markup, division, total…), `list_work_item_lines` (its materials or activities) |
| Tasks | `set_due`, `clear_due`, `assign`, `unassign`, `set_status`, `archive` / `unarchive`, `convert_task` |
| Figures | `metric` — the fields of **`MetricAsk`**, not `MetricSpec`: status set, `before_tax`, subject, period (calendar or last-N), shape, `by`, `measure`, `limit`, `compare`, `work`, `recurring`, breakdown `rows`, `line_name`/`line_unit`; `dashboard` (the pipeline / backlog / completed cards and the dashboard's status counts — today's `analytics_estimates`); `catalog_figure`; `task_count` (by person or property); `calculate` (hands the text to the Calculator Agent, open math included) |
| Help | `help` (a question for the user guide) |
| Conversation | `answer` (a choice, a value, yes, no, or the fields a create or gathering flow asked for), `cancel`, `show_more`, `repeat`, `acknowledge`, `social` (a question about Maple itself — `maple_persona`), `redo_last` (the last read again with one change: another subject, another period, or tax the other way — today's `followup.py` and `tax_followup.py`), `refine_last` (narrow the list just shown: "just the drafts") |

### 4.2.1 As built (step 4, 2026-10-07)

Decisions the code forced, in `platform/agents/planner/schema.py`:

- **Each op is today's intent name** where one exists (`update_contact`,
  `list_tasks` …; `INTENT_OF_OP` maps the rest — `set_status` → `update_estimate`,
  `metric` → `analytics_metric`, notes and conversation turns to their feature).
  The shadow comparison (§8) reads it, and a test fails if a supported intent
  has no op.
- **Task edits are one `update_task`** with typed fields (due date, clear due,
  status, assignee, unassign, property, clear property, notes append/replace,
  archived) — how the Task agent already works — not six ops.
- **Inventory corrections:** tasks have no priority; templates are only listed,
  read and deleted; a role's Rate is derived, so `labour_rate` is a refusal
  reason and `LabourFields` has `wage` only; contact roles and labour units are
  enums, task statuses and divisions are the company's names.
- **`edit_estimate` does not carry `EditCommand` unchanged.** Today's
  `WorkItemRef` has `job_item_id`, which would let the model pass an id. The
  planner's edit commands subclass today's — every bound and validator kept —
  with a symbolic `WorkItemPick` (position, name, focus, listed) and, for a
  line edit, a `line` that may be a listed row. `to_edit_command` turns one
  back into today's `EditCommand` once the resolver has the work item.
- **The tool is sent prebuilt** (`plan_tool()`): langchain's conversion inlines
  every `$ref` and made the schema ~34k tokens. Kept as `$defs`, titles
  stripped, it is ~13k tokens — cached at a tenth after the first call. A test
  caps it (56,000 characters) so it grows only on purpose.

Step 5 (`snapshot.py`) needed the state to carry time as well as turns (D19):
anchors now stamp `active_<domain>_set_at` (`focus.stamp_anchor`), lists
`recorded_at`, and every turn `last_turn_at` (`finalize_orchestrate_result`) —
bookkeeping, not message reading, so D14 doesn't hold it back. The viewed
estimate signal carries an id, never a code; the snapshot names it through the
estimate anchor the signal sets.

**Step 6a, measured 2026-10-07** (gpt-6-luna, three live calls):

| Call | Latency | Input | Cache | Plan |
|---|---|---|---|---|
| "update the phone number for Bob Jones to 555-123-4567" | 2.8 s | 25,815 | wrote 25,466 | valid, as §4.1 |
| "add a contact Mark Liu, 555-0142, and link him to 14 Birch Rd" | 5.2 s | 25,820 | read 25,466 | valid: create + link via `step` |
| "change her email to ana@reyes.ca" (Ana in focus) | 2.8 s | 25,809 | read 25,466 | valid: `focus`, domain contact |

- **Caching works as designed:** everything up to the breakpoint (prompt + tool
  schema) is written once and read after; only ~350 tokens per turn are
  uncached. langchain-openai 1.6.6 carries `prompt_cache_options` and the
  content-block breakpoint natively — no raw-client fallback (#820 is moot).
- **The cached prefix is ~25,500 tokens, not ~15,000:** OpenAI counts the tool
  schema at about twice the characters-÷-4 estimate. Per turn on Luna: ~$0.0003
  (cached read + ~350 fresh + ~70 out); the first write ~$0.0032.
- **Latency is 2.8–5.2 s with the prefix cached** — fine for shadow (it runs
  after the reply); a question for switchover, where it is the user's wait. The
  parity run (step 11) records it per call; trimming the schema is the lever.

### 4.3 References are symbolic, never ids

Every target is a `RecordRef`:

| `by` | Meaning | Example |
|---|---|---|
| `name` | a name, title or readable code the user said | "Ana Reyes", "the patio job", "E0042" |
| `focus` | the record in focus for a domain (or the freshest) | "it", "him", "there" |
| `viewed` | the record open on the portal page | "this estimate" on the estimate page |
| `listed` | a row of the last list | "the second one" |
| `step` | the record an earlier action of this plan made or found | "create John and link **him** to 12 Oak St" |

The schema has no id field. A model that copies an id out of the message has
nowhere to put it, so the tenant rule ("Maple never looks a record up by an id
typed into the message") holds by construction. `step` is what makes several
intents in one message composable.

### 4.4 Policy is in the schema

What Maple refuses today by regex becomes the absence of an op or an
`Unsupported.reason`: `bulk_delete` (no op takes "all"), `equipment`,
`labor_burden`, `material_cost`, `material_category`, `template_edit`,
`notes_on_catalog`, `out_of_chat` (with the capability, so the reply can use
`out_of_chat.py`'s redirect), `other`. These reasons are also the planner's
side of the unanswered tracker (§9.3).

### 4.5 Parity: every phrasing Maple handles today

The planner replaces about twenty readers, and "the same set of phrases" is
not guaranteed by writing a good prompt. It is guaranteed by three things:

1. **A map from today's catalog to the schema, written before the schema.**
   Appendix A maps every section of the phrasing reference (the human truth,
   731 ✅ rows), every intent in `SUPPORTED_INTENTS_BY_AGENT`, every
   `command_grammar` entry (core and ported), every router pre-handler and
   every open-question kind to the action, reference form or policy that
   carries it. A row with nothing to map to is a schema gap, found at the
   desk rather than in the window. Building the map against the reference's
   headings already added eleven ops to §4.2 that the first draft lacked
   (work-item reads, assumption adjustment, recurring, template-with-size
   creates, size-scoped material ops, cross-record estimate filters, the
   dashboard cards, task counts, archive, `social`, `refine_last`).
2. **Every multi-step flow is readable from the snapshot.** Today nine router
   flows and every agent's `pending_intents` record hold a question in
   progress: estimate gathering (details Maple still needs to generate),
   template size, property-link confirmation, the estimate follow-up and the
   optional follow-up, a pending calculation, note body and note delete, the
   status offer after generation, overage, the fuzzy-match "did you mean",
   task confirmations and menus, a create's next field, a field-then-value
   update. The planner cannot answer a question it cannot see, so
   `snapshot.py` renders **each kind in words** — what was asked, what an
   answer looks like, the choices if any — and the `answer` action carries
   the reply. A test renders every kind in `open_question.open_questions`
   (the router flows and the agent records) and fails on one it has no words
   for, so a new question kind can't be added without the planner learning to
   read it.
3. **An offline parity run before the window** (§11, step 11), over every
   corpus that pins today's behaviour — not just the 125 `expected.json`
   rows — **and over the phrasing reference itself** (D18). The test corpora
   overlap the reference but are not it: the reference is the human truth
   (741 ✅ rows on 2026-10-07) and holds phrasings no test runs. Its tables
   are regular enough to read by script — a backticked `Phrasing` first
   column, an `Intent → Agent` or `Status` column, and section headings that
   mark whole tables ✅ — so step 11 reads every ✅ row out of it, fills its
   placeholders (`{property}`, `{contact}`, `{estimate}`) from the seeded test
   world, runs it under its section's state, and scores the plan against the
   row's intent and agent. Rows the script cannot read (prose, multi-step
   sequences written with arrows) are listed in the report as *not checked*,
   so an unchecked phrasing is visible rather than assumed. See step 11 for
   the bar it has to clear.

Two kinds of phrasing need no map entry because the planner is better at them
by construction: the verbless and possessive forms the rules handle with
address and person-name heuristics (§2.8, §3.7, §4.7, §5.7), and anything
in another language.

### 4.5.1 As built: the parity run (step 11, 2026-10-07)

**The harness.**
- `tests/test_planner_parity_live.py` is opt-in: `-m llm_e2e` with
  `OPENAI_API_KEY`. Its knobs are `PARITY_SOURCES`, `PARITY_LIMIT` and
  `PARITY_CONCURRENCY`.
- Helpers live in `tests/planner_parity/`: cases, scoring, the runner, the
  report, and the explained rows.
- `scripts/phrasing_reference_rows.py` reads the reference.
- Reports go to `tests/reports/planner_parity.md` and
  `planner_parity_conversations.md`, with `.json` copies for diffing two runs.

**Four corpora, with no database (only the plan is scored):**
- *routing*: every phrasing of the routing corpus in each of its four anchor
  states, against `snapshot_routing.json`. Rows the rules left `unknown`
  aren't scored.
- *expected*: the routing rows of `expected.json`.
- *crud*: the 206-row coverage matrix, refusals included.
- *reference*: every ✅/🛑 row the reader can check.
  - 1,035 rows are checked, 67 of them refusals; 267 are listed as not checked,
    each with its reason (several steps, a state it can't build, an ellipsis,
    an identifier, an unknown placeholder).
  - A row that says "it" runs with its section's record in focus.

**Scoring** uses the window's own comparison (`services/maple_compare`). On top
of it:
- *blocker*: a supported phrasing the planner refuses — the bar. Counted only
  on expected, crud and reference: the routing corpus records where the rules
  routed, not what the agent then did ("set the labor burden …" routes to the
  Estimate Agent, which refuses).
- *ran*: a supported row with no recorded intent (or the rules tier's help
  fallback); it only has to not refuse.
- *refusal_ok* / *refusal_missed*.
- *intent match*: the stricter `INTENT_OF_OP` equality.

**The acceptance conversations** run through the real endpoint against the
seeded world, with shadow on, the current pipeline at the rules tier and the
planner live. The turn's background tasks run, so each turn is scored by its
stored `comparison`: a dry run of the window.

**Results.** First run, then final run, same code paths. Each run was about
5,000 corpus calls (29 minutes at 8 at a time) plus 581 conversation turns.
Five rounds came to roughly 20,000 calls, about $6 at step 6a's measured
cost.

| Corpus | Cases | Agree | Differ | Blockers | Refusals missed | Errors |
|---|---|---|---|---|---|---|
| routing (first → final) | 3,549 | 2,010 → 2,149 | 1,268 → 803 | (34) → 0 | — | 237 → 54 |
| expected | 107 | 65 → 78 | 32 → 28 | 1 → 0 | — | 8 → 0 |
| crud | 206 | 155 → 165 | 27 → 23 | 0 → 0 | 0 | 6 → 0 |
| reference | 1,223 → 1,035 | 356 → 382 | 155 → 73 | 6 → 0 | 31 → 3 (explained) | 55 → 3 |
| conversations (turns) | 581 | 487 → 551 (95%) | 94 → 30 | — | — | — |

**The bar is met:** no blocker, and the three remaining flags are explained
(`tests/planner_parity/explained.py`):
- renaming an activity: the reference refuses it, but the shared edit command
  can do it, so a decision is needed;
- two template edits named without saying "template": the policy finds no
  estimate by that name and asks, so nothing runs.

**What the runs changed.**
- Prompt:
  - estimate edits go only inside `edit_estimate`;
  - never ask which record (point with focus, or name it);
  - refusal scope:
    - only *setting* labor burden is refused;
    - a role's cost is its wage;
    - moving a material to a category is an update;
    - a task's property is cleared, not unlinked;
    - equipment only when said;
    - templates and partial bulk deletes are refused;
  - an activity's rate on an estimate is settable;
  - a bare name, address or code shows the record;
  - empty creates and updates;
  - a bare yes with nothing open answers nothing;
  - replies to a text question, a menu (by code) or a "which one?";
  - start over;
  - personal questions are `social`.
- Schema:
  - creates and updates may name nothing yet;
  - `archived=false` is a value;
  - "every work item" (`by: all`) for markup, overhead, tax, gross margin and
    division, never for a removal;
  - the `recurring` refusal — set_recurring removed, decision 2026-10-07;
  - `start_over`;
  - `refine_last` sort and count;
  - role figures take rate and wage;
  - `put_back` moves the model's common misplacements to where they belong
    and never invents a value.
- Policy:
  - today's status gates: transitions, the missing-items send gate, and the
    role rule — now one function,
    `services/estimate_status.status_change_role_refusal`, used by the
    Estimate Agent too;
  - a create's needed fields (a material's cost, a role's wage);
  - an empty update asks what to change;
  - which size, which teammate, an unknown task status;
  - a figure's subject, by `metric_subject.resolve_subject`;
  - a bare yes, ok or no with nothing open never writes.
- Resolver:
  - estimate list rows recorded by E-code;
  - a name copied with "the" and its kind word.
- Comparison:
  - "couldn't find" and "asked which" are one outcome;
  - a create that then offers a follow-up wrote.
- Current pipeline: the overage "no" and the note-delete "no" mark themselves
  `cancelled`.
- Planner call: one retry on a dropped connection.

**What remains, read.**
- The routing corpus's 803 differences are mostly the planner asking for a
  record the message doesn't name, where the rules routed to an agent that
  asks the same, plus the corpus's deliberate fragments ("due date",
  "check grade"). In a real turn both sides ask, and the window's comparison
  scores that as agreement.
- In the scored sources the differences are mostly labelling:
  - work-item reads that today files under `update_estimate`;
  - answers reached by another route ("which contact is E0042 for?" as an
    estimate field);
  - a few real ones, such as "which properties use Black Mulch?", which the
    planner answers with estimates.
- The 30 conversation differences are edge readings:
  - "show more" with nothing listed;
  - a stale list;
  - "Show Stone" answering "which material?";
  - unknown teammates in a filter.
  
  Each is in the conversation report.

**From here** the suite is the planner's live regression suite. Run it before
every prompt, schema or model change and diff the `.json` against the last run.

### 4.6 A multi-turn drill-down, turn by turn

The plan is per turn; what carries a conversation is the server-owned state
the previous turns left, rendered into the snapshot. A drill-down from an
estimate to a work item to a material to its size looks like this. The
snapshot column is what the planner reads (abridged); the state column is
what the turn writes back — the same keys today's Maple writes
(`active_estimate_id`, `active_work_item` keyed on `JobItem.id`,
`last_listed_items`, `pending_intents`), so nothing new is persisted.

| # | User says | Snapshot shows | Plan | State after |
|---|---|---|---|---|
| 1 | *open the Jones backyard estimate* | focus: none · page: /estimates | `get` estimate, target `name:"Jones backyard"` | estimate anchor E0042, set turn 1 |
| 2 | *show me the patio work item* | focus: estimate E0042 "Jones backyard" — 1 turn ago, 1 min ago | `get_work_item`, target `name:"patio"` (scoped to the estimate in focus) | work-item anchor Patio (`JobItem.id`), set turn 2; its line names recorded |
| 3 | *what materials are on it?* | focus: work item "Patio" on E0042 — 1 turn ago; estimate — 2 turns ago | `list_work_item_lines`, target `focus`, `lines:"materials"` | last list: 3 rows — 1 Pavers 24×24 (120 ea) · 2 Polymeric sand (8 bags) · 3 Gravel base (2 yd) |
| 4 | *make the second one 10 bags* | last list: materials on "Patio" (3 rows, numbered) · focus: work item | `edit_estimate` → `update_material`, target work item `use_active`, line `listed:2`, `quantity: 10` | the resolver turns row 2 into the line's identity (name + size) before the `EditCommand` is built; executor applies; list rows kept |
| 5 | *switch the pavers to the bigger size* | same list; catalog has Pavers in 12×12 and 24×24 (the resolver, not the snapshot, knows this) | `edit_estimate` → `update_material`, line `listed:1`, `size: "bigger"` → the resolver can't read "bigger" as a size → the policy makes it a `pick` question: "Which size — 1 12×12, 2 24×24?" | `pending_intents`: a pick, choices recorded, the original plan stashed |
| 6 | *the 24* | open question: pick, "Which size…", choices 1 12×12 · 2 24×24 | `answer`, `pick: 2`, `answers_open_question: true` | the stashed plan runs with size 24×24; question dropped |
| 7 | *and its price?* | focus: work item (turn 2); last list: lines; last request: an edit of row 1 | `get` with `field: price` on the material just edited (`listed:1`) — "its" reads as the line, the freshest thing touched | — |

Four things this relies on, all already in today's Maple and kept (§3):

- **One focus per domain, each stamped with its turn**, and a pronoun reads
  the freshest (turn 7). A work item's focus is scoped to its estimate, so
  "the patio work item" after turn 1 is looked up on E0042 only.
- **List memory records rows** (`format_and_record_list_response`), which is
  what makes "the second one" a `listed` reference rather than a guess
  (turn 4). A list of lines records the line's name and size, not just a
  label, so the resolver can build the `EditCommand` locator from it.
- **A question lives one turn** (or one hour, D19), and its answer re-runs
  the stashed plan (turns 5–6) — the `sub_op="edit_commands"` stash that
  `run_confirmed_edits` already re-validates from JSON.
- **`EditCommand` stays unchanged**: `listed` is resolved to today's
  `material_query` + `size` locators by the resolver, so the executor's
  validation (`invalid_targets`, exact unique match) is the same code path.

**In shadow this is subtler than it looks.** The state the planner reads at
turn N is the state *today's* pipeline wrote at turn N−1. If the current
pipeline misread turn 3 and recorded no list, the planner's turn 4 has no
rows to point at and asks "which material?" — a `differ` caused by the other
side's earlier turn, not by the planner. The session file marks these
("state from current: no list recorded") so the reviewer doesn't score them
against the planner. At switchover the planner writes its own state, so the
chain is its own.

## 5. The planner call

- **Model:** the worker role (`create_chat_model("worker")`, today gpt-6-luna,
  reasoning effort `none`), `with_structured_output(Plan,
  method="function_calling")`, temperature 0, 20 s timeout. The model name is
  logged with every turn, so a later Sol comparison is possible but out of
  scope.
- **Input**, in this order (static first, for prompt caching):
  1. Static: what Maple can do, the domains and their fields
     (`domain_knowledge.py`), the reference rules (§4.3), the refusal reasons,
     and the reading rules the grammar encodes as data rather than regex —
     "won"/"sold" is the sold set unless "status won" is said; a list of
     statuses is one set; money includes tax unless "before tax".
  2. The state snapshot (`snapshot.py`), fenced: focus anchors with their age
     in turns and in time ("contact Ana Reyes — 1 turn ago, 19 days ago"),
     the page being viewed, the
     open question in words — its kind, what it asked, its choices (§4.5,
     point 2) — the last list's rows with their numbers and the filter that
     made it, the last request (including whether its figure was before tax).
  3. The last 10 entries of `chat_history`, each cut to 500 characters, fenced.
  4. The message, **in the user's own words** (pre-translation), fenced with
     `DataFence("USER_MESSAGE")`.
- **Not the full history.** Old turns cost tokens — and credits — and carry
  stale references; how old an anchor is reaches the model as data, but
  whether it is too old to write through stays the policy's decision (§6).
  The window is fixed at 10 entries, so a turn costs the same on the
  fortieth message of a long conversation as on the third; a session's length
  (D10) changes what the log file shows, never what the planner is sent.
  (Today's classifier sends 20 entries.)
- **Prompt review:** `/agent-prompt-review` before the switchover (§12).

### 5.1 Prompt caching

How OpenAI caches the GPT-5.6-and-later models (prompt-caching guide, read
2026-10-06):
- A prompt is cached only once it has at least 1,024 input tokens.
- A cache *write* costs 1.25× the normal input price. A cache *read* costs
  about 0.1×.
- A cached prefix stays reusable for 30 minutes after its last write or read.
- The default ("implicit") mode puts a cache breakpoint at the end of the
  latest message. That means every call writes its **whole** prompt into the
  cache at 1.25×.

The planner's prompt ends in a different message, history and state on every
turn, so implicit mode would pay the write premium on the part that never
repeats. The planner therefore uses **explicit-only mode with one
breakpoint**:

- `prompt_cache_options={"mode": "explicit"}` on the request.
- `prompt_cache_breakpoint: {"mode": "explicit"}` on the last content block of
  the static developer message. The guide says top-level `instructions` can't
  hold a breakpoint, so the static text goes in a developer message.
- Everything after the breakpoint (snapshot, history, message) is billed at
  the normal input rate with no write charge.
- The static part is the same for every company and user. It is written once
  and then read at about a tenth of the price for as long as Maple traffic
  keeps it warm. The 30-minute idle window is long, so a quiet night costs one
  re-write in the morning.

**Worked example**, in units of one normal input token. Take a planner call
with 3,000 static tokens and 1,500 that change every turn:

| | Static 3,000 | Changing 1,500 | Input cost |
|---|---|---|---|
| No caching | 3,000 × 1 | 1,500 × 1 | 4,500 |
| Implicit mode (today's default), static part already cached | 3,000 × 0.1 | 1,500 × 1.25 (written, never reused) | 2,175 |
| **Explicit, one breakpoint after the static part** | 3,000 × 0.1 | 1,500 × 1 | **1,800** |

Caching is worth it either way. What explicit mode adds is not paying the
write premium on the 1,500 tokens that will never be read again. Outputs are
never cached; caching only discounts input. The multipliers above are the
guide's general ones; the exact gpt-6-luna and gpt-6-sol rates are checked on
OpenAI's pricing page when `model_pricing.py` gains them (step 0).

**Later, if the numbers justify it:** within a conversation the history is
partly repeated from one turn to the next. A second breakpoint after the
history could cache that too. But the 10-entry window slides, and the state
snapshot changes every turn, so whether this would hit often is unclear.
Step 0's per-turn numbers decide it; it isn't built until they do.

Rules that keep the prefix stable:
- **Nothing per-turn in the static block.** No date, no company name, no user,
  no current page. All of that belongs in the snapshot, after the breakpoint.
  A test asserts the static block is byte-identical across two different
  companies' turns.
- **The tool schema never changes per call.** The `Plan` schema is
  `with_structured_output`'s function definition; changing tools or their
  order invalidates the cached prefix. A domain never gets a narrowed schema
  per turn; restrictions go in the policy.
- **Prompt and schema changes are deploys.** Each one costs one cold write,
  which is fine.
- **The static block must be over 1,024 tokens.** It will be (domain knowledge
  plus reference and reading rules), and a test asserts it, so a trimmed
  prompt doesn't silently drop out of caching.
- **No `prompt_cache_key`.** On these models it isn't needed for hit rate, and
  calls with different keys don't share entries. A per-user key would stop
  every user sharing the one static prefix. The static block holds no customer
  data, so there is nothing to probe.

**Getting it onto the wire:**
- langchain-openai 1.6.6 passes top-level request fields through
  `model_kwargs`/`extra_body`. Whether it keeps an unknown key on a message
  content block is not known, and is checked in step 7 against a real request.
- If it drops the key, the planner calls the raw `AsyncOpenAI` client, as the
  estimate researcher's `responses.parse` calls already do. The CLAUDE.md rule
  for raw calls applies: no `temperature` or other sampling parameters to a
  reasoning model.

**Measuring it, for every LLM call (not just the planner):**
- Today `services/llm/callback.py::_extract_token_usage` reads only prompt and
  completion tokens, and `model_pricing.py` has one input price per model. A
  cached token is therefore costed, and counted, as a full one, and a cache
  write as a normal one.
- `LLMUsageEvent` gains `cached_tokens` and `cache_write_tokens`, read from the
  usage details (`input_tokens_details.cached_tokens` /
  `cache_write_tokens`, and their Chat Completions equivalent).
- `compute_cost_usd` prices those tokens at the cached and write rates.
- This covers every Maple feature at once, so each feature's hit rate is one
  query on `llm_usage_events`.

**Existing calls:**
- Every other Maple call uses implicit mode today, so it already pays the
  write premium on prompts whose tails never repeat. Once the usage fields
  show per-feature numbers, the calls with a large fixed prompt move to the
  same explicit-mode helper: the classifier, the domain agents' classify and
  extract calls, the guide, the edit planner and the metric spec.
- That helper is `services/llm/factory.py`: one function that marks a static
  developer message's breakpoint and sets the mode, so no caller builds it by
  hand.
- This is a cost change, not a change to how Maple reads messages, so D14 does
  not hold it back.

**Credits (D17):** today `record_llm_usage` adds the raw token total to
`Company.tokens_used_this_period` and `User.tokens_used_this_period` (what the
quota reads) and posts the same number to the Stripe `tokens_used` meter. A
cached token therefore costs the customer as much as an uncached one. From
step 0 the number added and reported is the **credit-weighted total**:

```
credits = (prompt_tokens − cached_tokens) + cached_tokens × cached_rate + completion_tokens
```

rounded to the nearest token, with `cached_rate` a config value
(`LLM_CACHED_TOKEN_CREDIT_RATE`, default 0.1 — the price ratio). Cache writes
are **not** charged above the normal rate: a write happens once per deploy or
quiet spell and serves every customer, so whichever customer happens to
trigger it shouldn't pay 1.25× for it. `LLMUsageEvent` stores `credits` beside
the raw counts, so the audit trail shows both. `total_tokens` keeps meaning raw
tokens. The quota's `included_tokens` is unchanged — a customer simply gets
more turns out of it once caching lands. A test pins the formula and that the
meter event carries `credits`, not `total_tokens`.

## 6. Resolver and policy

The resolver turns each `RecordRef` into a record of the caller's company,
using the existing lookups (§3) — exact name first, then the same fuzzy
fallbacks today's agents use (`fuzzy_utils`, the address matching in
`address_service`, `find_contacts_by_name`'s fuzzy pass), so "123 Main" still
finds "123 Main St" — never a bare `Model.get(id)`:

| Outcome | Shadow log shows |
|---|---|
| one record | `→ Ana Reyes (contact)` |
| several | `would ask: which of 3?` |
| none | `would say: not found` |
| `step` | `→ (made by step 1)` |

The policy then marks each action as today's rules would treat it:

- `would confirm` — any delete; a write through a stale anchor; a `listed`
  write after focus moved; a `create_estimate` that bills overage
  (`estimate_bills_overage`, unless the user turned the notice off).
  **Stale means by turn or by time.** Today freshness is counted in turns
  only (`focus.py`: an anchor set this turn or the previous one is fresh), so
  a user back after three weeks finds their last anchor "one turn ago" and
  "update its phone" would write to it unasked. The planner's policy adds a
  clock: an anchor or a recorded list older than **24 hours** is stale however
  few turns ago it was set, and an open question older than **1 hour** is
  dropped as if unanswered — "a question lives one turn, or one hour" (D19).
  The snapshot shows each anchor's age in both ("1 turn ago, 19 days ago").
  The same rule in today's Maple would be a change to the frozen pipeline; it
  prevents a wrong write, so D14 allows it, but it is logged as a follow-up
  and decided on its own, not slipped in with this work.
- `would refuse` — role lacks permission; Draft/Review lock; estimate or task
  limit reached; no card for an overage create.
- `would run` — otherwise.

In shadow nothing runs; at switchover the same code gates the executor.

**Several actions:** resolve and check all of them first. If any would ask or
confirm, the whole plan asks once, with a summary. Otherwise run in order and
stop at the first failure, saying what was done. (Shadow logs the decision.)

### 6.1 As built (step 7, 2026-10-07)

`agents/planner/resolve.py` and `agents/planner/policy.py`, read-only.

- **Names** go through the existing company-scoped finders:
  `record_names.find_records_named` (contacts, properties, materials, roles,
  tasks — exact, then word-start), `find_estimate_by_code` /
  `find_named_estimates` for estimates, readable-code lookups for `T0042` /
  `E0042`, and an exact-then-word-start name match for templates.
- **Focus, page and listed rows** load by `{"_id", "company"}` — an anchor or
  a row pointing at another company's record resolves to *none*. Work items
  resolve on the resolved estimate by position, name, focus (only an anchor on
  that estimate) or a listed work-item row scoped to it. A listed line gives
  the line's name, which today's `EditCommand` takes as its query. It counts
  only a list of that work item's lines (`material_line` / `activity_line`,
  scoped to its `JobItem.id`). Today's line lists record no rows, so a listed
  line asks rather than reading an older list (review 2026-10-07 #1; ⚠️ gap in
  the phrasing reference).
- **Stale** (§5.2, D19): a focus not fresh by turn (`focus.anchor_is_fresh`,
  the viewed page counts as fresh) or set more than 24 hours ago; a list shown,
  or a work item put in focus, before the previous turn or more than 24 hours
  ago.
- **The policy reuses today's rules, never copies them:** `may_delete_estimate`,
  `services/notes.may_delete_note` (a note's author or an Owner; Maple's note
  delete and the HTTP route read the same rule), the Owner/Admin rule for catalog deletes, `EDITABLE_ESTIMATE_STATUSES` with
  `CONTENT_OPS` (notes exempt), `estimate_bills_overage` with
  `check_quota_exceeded`, `settings.tasks_enabled` with `is_task_limit_reached`.
  An answer is *would ask* when no question is open or it was asked more than
  an hour ago (D19).
- **A plan's decision is its strictest action's** — refuse, ask, confirm, run —
  so a plan with one doubtful action asks once, before anything runs.

## 7. Shadow recording

### 7.1 Where it hooks in

`_orchestrate_turn` (`routers/agents.py`) returns every result through its
`_finalize_result` closure — still true after the 2026-10-03/05 additions (the
overage question, the tax follow-up), which return through it like everything
else. Shadow adds two things:

1. After the page signals are applied (`viewed_estimate`, `viewed_record`)
   and before `decide_turn`: a deep copy of `merged_context` and both message
   forms (original and English). Taken earlier, the planner's `viewed`
   reference would have nothing to read.
   `decide_turn`'s verdict (answer / cancel / new message) is kept for the
   comparison (§8).
2. In `_finalize_result`, after the response is built:
   `background_tasks.add_task(maple_shadow.record_turn, …)` with the snapshot
   and the finished response.

Turns that end before orchestration — the turn lock, the rate limiter's 429,
the credit refusals, and `translation_unavailable` — return before
`_finalize_result` exists and are not shadowed (the unanswered tracker still
records them, §9.2). Public Maple (`/public/maple/ask`) is not shadowed. Every
company is (D8).

### 7.2 Guarantees

- **Never affects the user.** It runs after the response is sent; every
  exception is logged (no `logger.exception`) and swallowed; a 20 s timeout
  bounds it.
- **Never writes customer data.** No executor; reads only, company-scoped. It
  never saves `ConversationContext` — it works on its own deep copy.
- **Never bills the customer.** Maple's LLM calls today bump the company's and
  user's token counters and post a Stripe meter event (`services/llm/usage.py`).
  Shadow calls run under a tenant-less attribution, `feature="maple.shadow.plan"`
  — `record_llm_usage` with `company_id=None` records the event for ops spend
  and skips both counters and metering. **The background task inherits the
  request's LLM context** (Starlette runs it in the same task, so the
  `ContextVar` set for the user's turn is still there); `record_turn` must
  therefore set the tenant-less context itself before its first call, keeping
  only the `turn_id`. A test pins that a shadow call bumps no counter.
- **Off by default:** `MAPLE_SHADOW_ENABLED` (config, default false; forced
  false in tests like the planner flags).

### 7.3 Storage: `maple_shadow_turns`

The Render web service's disk is wiped on every deploy and restart, so md
files are never written on the server. Each turn is one document:

| Field | |
|---|---|
| `company`, `user`, `user_email` | |
| `at`, `turn_index` | |
| `message`, `message_en` | original and English |
| `state` | the snapshot text the planner saw |
| `current` | the current pipeline: `intent`, `agent`, operation, records touched, `open_question`, `response`, `wrote`, latency, **outcome** (§9.2), and its **tokens** — the sum of the turn's `llm_usage_events` (prompt, cached, cache-write, completion) and the credits they used |
| `planner` | the plan, the resolver and policy outcomes, model, tokens (prompt, cached, cache-write, completion), latency or the error, **outcome** (§9.3) |
| `comparison` | `agree` / `differ` / `unsure`, and why (§8) |
| `conversation_id`, `turn_id` | the conversation the file groups by (§10.1); the turn's id (below) |

To sum a turn's usage exactly, each turn gets a `turn_id` (a UUID made at the
start of `_orchestrate_turn`), carried in the LLM request context
(`LLMRequestContext.turn_id`, `services/llm/context.py`) and stored on every
`LLMUsageEvent` written during that turn — the current pipeline's calls and
the shadow call alike. That one field is what makes "this turn cost N
credits" a lookup instead of a time-window guess.

Indexed on `(company, user, at)` and `(conversation_id, at)`. A TTL index
expires documents 45 days after insert — housekeeping, so the collection
doesn't outlive its review.

### 7.4 As built (step 8, 2026-10-07)

- `services/maple_shadow.py`: `take_snapshot` (a deep copy of `merged_context`,
  taken right after `apply_viewed_record_signal`; it drops the history's last
  user entry when it is this turn's message, so the planner sees the message
  once, in its own fence) and `record_turn` (the background task).
- The question gate's reading goes onto the capture after `decide_turn`:
  `decision` is `answer` / `cancel` / `new_message`, or `none` when nothing was
  open, and `question_open` says which.
- `_finalize_result` schedules `record_turn` right after `_track_unanswered`,
  with the English payload and the turn's latency. The current pipeline's
  `maple_unanswered` row carries `shadow_turn` too: the capture's id is made at
  snapshot time and becomes the `maple_shadow_turns` document's `_id`.
- Attribution: `services/llm/context.tenantless_llm_context(feature, turn_id)`
  wraps the plan and the check and resets on exit, so the tasks after it keep
  the request's attribution. The planner's calls are `maple.shadow.plan`, with
  no company and no user.
- Tokens per side come from the turn's `llm_usage_events` (indexed on
  `turn_id`), split on that feature. Each side records `prompt`, `cached`,
  `cache_write`, `completion`, `credits` and `calls`.
- The bound is 30 s, not 20 s: the planner call keeps its own 20 s, and the
  resolver's reads get 10 s more. It runs after the reply, so the user never
  waits for it.
- The planner's outcome (§9.3) is `planner_outcome`:
  - Unsupported gives its reason. `out_of_chat` carries the capability, and
    `other` is `not_understood`.
  - An action that would be refused is `ActionCheck.refused_for`, which is
    `not_permitted` or `limit`. The policy now sets it with each refusal.
  - A reference that matches nothing is `not_found`.
  - A failed call is `error`.
  - A clarify plan or a "which one?" is not a miss.
  A miss is written to `maple_unanswered` with `pipeline="planner"`.
- `current.wrote` is a heuristic: an intent or operation that starts with a
  write verb, no question was saved, and the turn wasn't cancelled. A declined
  delete comes back as `delete_<x>` with `cancelled`, and wrote nothing. `current.anchors` lists the
  `active_<domain>_id`s that moved this turn. Step 9's comparison reads the
  delegations themselves. `comparison` stays empty until step 9.
- Flag: `MAPLE_SHADOW_ENABLED` (config, default false; forced false in
  `tests/conftest.py`). Set in `platform/.env.local` for the Dev comparison
  (D20) — never on Render.
- **Which companies** (2026-10-07, Simon): `MAPLE_SHADOW_COMPANIES`, a
  comma-separated list of company ids, narrows the flag to those companies —
  for a trial on one company before the whole window. Empty is every company,
  so D8 is unchanged. Ids, not names: names repeat and change, and the turn
  already carries the id. An entry that isn't a 24-hex id is logged (at
  startup, when the flag is on) and skipped; a list with no valid id records
  no one, never everyone. `maple_shadow.records_company` is the one check,
  in `take_snapshot`.
- Tests: `tests/test_maple_shadow.py` (24).
  - The snapshot, including the viewed record.
  - The planner's outcomes.
  - Tenant-less attribution with the turn id kept. A real `record_llm_usage`
    under it bumps no counter and posts no meter.
  - Both sides' tokens.
  - The planner's miss row.
  - A failure never raises.
  - The reply is identical with shadow on (except the turn's clock).
  - Shadow saves no conversation.

## 8. Comparing with the current pipeline

An adapter reads what the current pipeline did from the finished response and
the context: `intent` and `agent`, each of `delegations`, the anchors written
this turn (an `active_<domain>_id` that changed is the record touched),
`open_question` (it asked rather than acted), and the outcome (§9.2). It
reduces both sides to a list of `(domain, kind, target)`, where kind is
`read`, `write`, `delete`, `ask`, `couldnt` (with the §9.1 reason), `help` or
`chat`. When a question was open at the start of the turn, both sides also
say how they read the message — `decide_turn`'s verdict against the plan's
`answers_open_question` — so "the current pipeline took it as an answer, the
planner as a new request" is a `differ` of its own.

- **agree:** the same list.
- **differ:** a different domain, kind or target, or a different count — that
  includes every compound message one side split and the other didn't, and
  every turn where one side couldn't and the other would have.
- **unsure:** the adapter can't tell what the current pipeline touched.

Known skew: the planner's resolver reads the database *after* the current
pipeline wrote. When `current.wrote` is true the log says so, because the
planner may see the record the current pipeline just made.

### 8.1 As built (step 9, 2026-10-07)

- `services/maple_compare.compare(current, planner)` is a pure function of the
  two stored records. `record_turn` stores its result as `comparison`:
  `verdict`, `why`, both sides' items as `[domain, kind, detail]`, and `skew`
  (the current pipeline wrote). Because it reads only what's stored, a
  window's turns can be compared again after the comparison changes. It never
  raises; a failure is `unsure`.
- **The current side.** An outcome (§9.2) is `couldnt` with its reason; so
  is an `off_topic` turn with none (recorded before the tracker classified
  the off-topic reply, 2026-10-07), as `not_understood`. A saved question is
  `ask`, a cancel is `chat`. Otherwise each op becomes one
  item: the turn's own op, or each delegation of a multi-intent turn.
  - The kind comes from the operation, else the intent, by name prefix.
  - The domain comes from the agent, else the intent.
  - The record acted on is the anchor the turn moved, else the one still in
    focus after it. So an edit to the contact already in focus still names
    its contact. Each turn now stores `anchors_after` and `cancelled` for this.
- **The planner side.** A failed call — or a plan whose check failed
  (`check_error`), which is stored with its plan — is `couldnt` with `error`,
  and is also the planner's `error` outcome in `maple_unanswered`; unsupported
  is `couldnt` with its reason; clarify is `ask`. Otherwise, per action:
  - A reference that matched nothing is `couldnt not_found`, and a refused
    action is `couldnt` with its `refused_for`.
  - *would ask* and *would confirm* are both `ask` — a delete asks first on
    both sides.
  - A plan that asks or refuses runs nothing else, so its other actions don't
    count.
  - A note takes its parent's domain, as today's note replies do; a link and
    a note delete match any domain, as today's link answers as a property
    update.
  - Stored references are now structured: `describe`, `status`, `domain`,
    `label`, `record_id`, `stale`.
- **The verdict.**
  - With a question open, a different reading of the message (answer, cancel,
    new message) is `differ` — unless the planner failed, which read nothing,
    or both declined. The gate cancels on "never mind" before it reads the
    question's kind, while the planner answers a yes/no with `yes=false`, so
    a cancel and a no (or an answer that ended cancelled and a planner
    `cancel`) count as one decline and `agree`.
    When both take it as the answer, a yes/no is compared with what the
    current pipeline did: a no against a write, or a yes against a cancel, is
    `differ`. A pick or a value is `agree`, saying the choice isn't compared,
    since the current side doesn't record which it took.
  - Otherwise items are matched in any order (an empty domain matches any).
    A leftover on either side, or a different record where both name one, is
    `differ`. Records are compared by id but named in the reason, by the
    current pipeline's anchor name and the planner's resolved label. When one side couldn't and the other would, the first reason
    says so.
  - **Two couldn'ts agree**, whatever reason or record each names — neither
    side did anything, and the reply's wording is the unanswered report's
    concern, not the comparison's (first Dev export, 2026-10-07: "how's the
    weather tomorrow?" was `guide_no_answer` against `not_understood`, and
    read as a difference). The `why` keeps both reasons, and the session file
    prints it under the collapsed turn.
  - An intent the adapter doesn't know, or a record the current pipeline
    didn't show, is `unsure`.
- Tests: `tests/test_maple_compare.py` (39) covers agree, differ and unsure,
  compound messages, couldn't against would, the open-question reading, notes
  and links. `tests/test_maple_shadow.py` checks the stored comparison.

## 9. Tracking what Maple couldn't do

### 9.1 What counts, and the reasons

A turn is **unanswered** when Maple did not do what was asked. Every such turn
is recorded — including the ones where not doing it was right (an equipment
refusal, a Member trying to delete): the review decides which are valid
responses and which are gaps.

| Reason | Covers | Usually |
|---|---|---|
| `policy` | bulk delete, equipment, material categories, template edits, notes on a catalog item, labor burden, material cost | valid |
| `out_of_chat` | the 12 redirects in `out_of_chat.py` (settings, team, billing, CSV, units, divisions, unlink, duplicate, documents, media, send, Load Standard) | valid — but each one is demand for a chat feature |
| `not_permitted` | role refusals (catalog and estimate deletes, send/archive), Draft/Review lock | valid |
| `limit` | token quota, hard cap, estimate limit / add a card, tasks disabled, task limit | valid |
| `not_understood` | intent `unknown`, the low-confidence capability guidance, "could you rephrase it?", the router's "I'm not sure — did you want me to …?", the edit planner's capability message | gap |
| `cant_narrow` | a metric scope said back (`unread_scope`, "can't narrow / can't rank") | gap |
| `not_found` | "I couldn't find …" with nothing offered, `template_not_found` | either — a typo or a real miss |
| `guide_no_answer` | the user guide's fallback sentence or response | gap |
| `error` | an agent's `success=False`, the edit and template "something went wrong" replies, the database-unavailable reply, `translation_unavailable`, the endpoint's 500 | bug |

**Not unanswered (D16):** a question Maple asks — which record, what value,
yes/no, a menu — is mid-request, not a failure. The test is `open_question`
set on the response: Maple saved a question it can take an answer to. A reply
that *reads* as a question but saved nothing ("I'm not sure — did you want me
to …?" with no pending state) is not one the user can answer, so it stays
`not_understood`; a "did you mean Ana Reyes?" that saved its yes/no is a
question. Also not unanswered: a cancel (`result.cancelled`), social turns,
`duplicate_message`, an empty list (a real answer), and the rate limiter's 429
(no turn ran).

### 9.2 Detecting it in the current pipeline

The current response has **no outcome field.** `success` is true on almost
every refusal; `needs_clarification` is set on refusals and real questions
alike; most reasons are distinguishable only by reply text. Adding a marker at
each of the ~100 sites (79 "I couldn't find …" strings across 27 files alone)
would be a large change to the pipeline D14 freezes, and the planner makes it
unnecessary (§9.3). So detection happens in **one place**,
`services/maple_outcomes.py::classify(payload) -> Outcome | None`, run on the
finished response in `_finalize_result`, in this order:

1. **Structured markers that exist today:** `result.operation == "refusal"`;
   intent `needs_payment_method` / `hard_cap_reached` /
   `translation_unavailable`; `result.refused` (catalog delete); 
   `template_not_found`; `update_estimate_unsupported_modify`; `success is
   False`; intent `unknown` with no `open_question`; intent `off_topic`
   (`not_understood off_topic`, 2026-10-07 — its reply had been an inline
   string, so neither rule saw it; it is now
   `orchestrator.OFF_TOPIC_REFUSAL_MESSAGE`); an `analytics_metric` result
   with no value.
2. **The reply against the existing constants, imported by name** —
   `BULK_DELETE_REFUSAL_MESSAGE`, `EQUIPMENT_REFUSAL_MESSAGE`,
   `BURDEN_REFUSAL`, `MATERIAL_COST_REFUSAL`, `ESTIMATE_LIMIT_REFUSAL_MESSAGE`,
   `TASKS_DISABLED_MESSAGE`, `TASK_LIMIT_MESSAGE`, `NOTES_NOT_ON_CATALOG_MESSAGE`,
   the `out_of_chat` redirects (which also name the capability), the guide
   fallbacks, `_EDIT_BUG_REPLY`, `_TEMPLATE_BUG_REPLY`, `maple_delete_refusal()`
   — plus a short list of reply prefixes ("I couldn't find", "I'm not quite
   sure how to do that", "I couldn't reach the estimates database"). Exact or
   prefix comparison against the constants, never a new regex.
3. **Otherwise not unanswered.** A turn the classifier misses is therefore
   *under*-reported, never invented — and the shadow comparison still shows it
   when the planner would have done something.

Four exits never reach `_finalize_result` and record their outcome at the
exit itself, through the same `maple_outcomes.record` call: the two credit
refusals (`limit`: `needs_payment_method`, `hard_cap_reached`),
`translation_unavailable` (`error`), and the endpoint's 500 catch-all
(`error`, with the exception type as `detail`). Each is a `return
OrchestratorAgentResponse(...)` in `_orchestrate_turn` before the closure is
defined, which is why the tracker can't rely on the closure alone.

**Keeping it honest:** a table-driven test imports every constant above and
asserts its reason, so renaming or rewording a constant fails a test instead
of silently dropping a reason; and one endpoint test per reason drives a real
turn through `/agents/orchestrate` and checks the record.

### 9.3 The planner's side

The planner needs no classifier: its outcome is in the plan. `unsupported`
gives the reason directly (§4.4); a resolver `none` is `not_found`; a policy
`would refuse` is `not_permitted` or `limit`; a timeout or malformed output is
`error`. A `clarify` plan is a question, not unanswered (D16) — the shadow log
still shows it as `ask`, so a planner that hides misreadings behind questions
would show up in the review as "asks too much", not vanish. In
shadow these sit beside the current pipeline's outcome, so the review sees
"current couldn't, planner would" (and the reverse) on the same turn. After
switchover the tracker reads the planner's outcome only, and §9.2's
string-matching is deleted with the pipeline it reads.

### 9.4 Storage: `maple_unanswered`

One document per unanswered turn, written from the same background task as
shadow (or on its own when shadow is off):

| Field | |
|---|---|
| `company`, `user`, `user_email`, `at` | |
| `message`, `message_en` | |
| `reason`, `detail` | §9.1 reason; detail is the constant's name, the capability, or the not-found phrase |
| `response` | what Maple said |
| `intent`, `agent`, `pipeline` | `current` or `planner` |
| `state` | a one-line state summary (focus, open question) |
| `shadow_turn` | the `maple_shadow_turns` id, when shadow was on |

Indexed on `(reason, at)` and `(company, at)`. TTL 180 days. Flag
`MAPLE_UNANSWERED_LOG_ENABLED` (default true; forced false in tests other than
its own). No LLM call — it costs one insert per unanswered turn.

### 9.5 The report

`python scripts/export_unanswered.py --since <date> --out <dir>` writes one
`unanswered.md`: a table of counts by reason (and by company), then each reason
as a section, its turns grouped by `detail` with the most frequent first:

```markdown
## not_understood — 23 turns

### "I'm not quite sure how to do that" — 9

- 2026-10-14 09:14 · Ridgeline · dana@ridgeline.com
  > move all of Bob's open tasks to next Friday
  Maple: I'm not quite sure how to do that — could you rephrase it?
  [ ] valid response  [ ] gap — Maple should handle this  [ ] bug
```

During the window it is reviewed with the session files; afterwards (D12) it is
a standing list of what to build next — `out_of_chat` counts in particular say
which out-of-chat features users ask Maple for.

## 10. The session files

### 10.1 Export

`python scripts/export_shadow_sessions.py --since <date> --out <dir>` reads
`maple_shadow_turns` (read-only), groups the turns by conversation (D10), and
writes one file per conversation plus an `index.md`. Run against production
with its `MONGODB_URL` set explicitly for that run.

A conversation is one `ConversationContext.conversation_id`, which each shadow
turn records. A user has one at a time. Pressing Clear deletes it
(`DELETE /agents/conversation`), and it also expires after 30 idle days; the
next message starts a new one. A file is never split by time, so a long
conversation is one long file with a heading for each day. A conversation that
began before the window starts at the first turn recorded in it, and its file
says so.

File name: `<first-turn date>_<company-slug>_<user-email-local-part>_<conversation-id prefix>.md`.

### 10.2 Format

```markdown
# Ridgeline Landscaping · dana@ridgeline.com · conversation 3f9c… · 2026-10-14 → 10-16

31 turns · 26 agree · 5 differ · 0 unsure · current couldn't: 2 · planner couldn't: 1
Tokens — current: 412,300 (cached 18%) · credits 412,300 · planner: 121,800 (cached 64%)

## 2026-10-14

## Turn 3 — DIFFER

> add a contact Mark Liu, 555-0142, and link him to 14 Birch Rd

State: property 14 Birch Rd in focus (1 turn ago) · no open question

**Current** (Contact Agent · create_contact · 1.4 s · 3 calls · 11,200 tokens, 1,900 cached · 11,200 credits)
Wrote: contact Mark Liu. Did not link.
> I've created the contact for you. Here are the details: …

**Planner** (gpt-6-luna · 1.1 s · 1 call · 3,950 tokens, 2,600 cached)
1. create contact {name: Mark Liu, phone: 555-0142} → would run
2. link contact (step 1) ↔ property "14 Birch Rd" → 14 Birch Rd · would run

Verdict: [ ] current  [ ] planner  [ ] both fine  [ ] both wrong
Note:

## Turn 5 — DIFFER · current couldn't (not_understood)

> move all of Bob's open tasks to next Friday

**Current** (unknown · 0.9 s)
> I'm not quite sure how to do that — could you rephrase it?

**Planner** …
```

Agreeing turns print collapsed (message, one line each side, each with its
tokens). The header's totals show how a conversation's cost grows with its
length — the current pipeline's credits per turn rise as its 20-entry history
fills, the planner's stay flat (§5). `index.md` lists every conversation with
its counts and tokens, differing conversations first.

### 10.3 As built (step 10, 2026-10-07)

- `scripts/export_shadow_sessions.py --since <date> [--until <date>] --out <dir>`
  is read-only. It reads `maple_shadow_turns` in the window, groups them by
  `conversation_id` (or by user, for a turn without one), and writes one file
  per conversation plus `index.md`.
- **The header:** the company, the user, the conversation prefix and the
  dates. Below it, the counts:
  - agree, differ and unsure;
  - how many turns each side couldn't do;
  - each side's tokens with the cached share;
  - the current pipeline's credits, and the planner's credits "if billed",
    since the planner bills no one.
  
  A conversation whose first recorded turn isn't turn 1 says it began before
  the window.
- **Dates are the user's days** (2026-10-07): each turn stores the
  browser's zone (`MapleShadowTurn.timezone`, from `client_context`), and
  the file name, the header's dates and each `## <date>` heading use it —
  else the zone the state's `Today:` line names, else UTC. `--since` and
  `--until` stay UTC days. Without this, an evening turn on the US west
  coast was filed under tomorrow.
- **The turns:** a `## <date>` heading each day.
  - An agreeing turn is collapsed: the message, then one line a side with its
    tokens, and any note the comparison left (two couldn'ts' reasons).
  - Any other turn is shown in full:
    - a heading with the verdict, and which side couldn't;
    - the message, and its English when that differs — each quoted line by
      line. A value spanning several lines in a planner action is printed on
      one line with `⏎` marking the breaks.
    - the state the planner saw;
    - the current pipeline: agent, intent, latency, calls, tokens and
      credits; how it read an open question; what it touched; any question
      it asked; its outcome; its reply;
    - the planner: each action with its values, its references and its
      verdict — or its refusal, question or failure;
    - the comparison's reasons, and the skew note;
    - a verdict to tick and a note line.
- `index.md` puts the most differing conversations first, then the most
  unsure, then the earliest. It gives each conversation's counts, the current
  pipeline's credits and the planner's tokens, plus totals for the window.
- Tests: `tests/test_export_shadow_sessions.py` (22), including the script
  imported cold — it imports `routers` first, past the agents ↔ routers
  cycle the suite never sees.

## 11. The window and the review

**Revised 2026-10-07 (D20): the comparison runs in Dev, not production.** The
two-week production window below the line was the original plan and is kept
for the record; nothing of it runs.

- **Where:** Dev only — `MAPLE_SHADOW_ENABLED=true` in `platform/.env.local`,
  narrowed with `MAPLE_SHADOW_COMPANIES` when wanted. The flag is never set on
  Render. Production runs today's Maple, unchanged, until the switchover.
- **The traffic is Simon's own.** The comparison only shows what someone
  tried, so the measure is the parity suite (step 11): every phrasing tried by
  hand that matters becomes a phrasing-reference row (or a corpus row), and
  from then on every run checks it.
- **The loop:** use Maple in Dev → export (`scripts/export_shadow_sessions.py`)
  → read the differences and the unanswered turns → fix the planner (prompt,
  schema, policy, resolver) → parity run → again. Gaps go to the planner only
  (D14 as revised by D20); today's Maple gets fixes for data loss, a wrong
  write, or a bug customers hit in production.
- **Blockers regardless:** any planner turn that *would run* a write on the
  wrong record, a delete without asking, or an overage create without asking.
- **Decision (Simon):** when the planner works clearly better than today's
  Maple in Dev, build the switchover (§12, its own plan) and switch in Dev
  first. Production follows only after that, company by company.

---

*Original plan (superseded by D20):*

- **Before:** D15's pre-flight; deploy with `MAPLE_SHADOW_ENABLED=true`
  (promotion by Simon with `/release platform`). After day one, check
  `llm_usage_events` for `maple.shadow.plan` spend and the error rate, and
  `maple_unanswered` for a plausible mix of reasons.
- **Two weeks** of traffic, every company (D8).
- **Review:** export both reports; read `index.md`, tick a verdict on each
  differing turn; tick each unanswered turn. Tally per kind (read / write /
  compound / question answers / refusals / couldn't).
- **Blockers regardless of the tally:** any planner turn that *would run* a
  write on the wrong record, a delete without asking, or an overage create
  without asking. A blocker is fixed and the window extended, not waved
  through.
- **Decision (Simon):** switch over (§12), or keep the current pipeline and
  keep improving the planner, then run another window. Gaps the unanswered
  report finds go to the planner in either case (D14).
- **After:** turn the shadow flag off; the shadow collection expires on its
  TTL. The unanswered tracker stays on (D12).

## 12. Switchover (only if the review says so)

**Planned in [`2026-10-07-maple-planner-switchover-plan.md`](2026-10-07-maple-planner-switchover-plan.md)** (D20: Dev first, then production). The outline below is what that plan builds on.

1. **Executor** (`agents/planner/execute.py`): each action calls today's
   handler for it — the domain agents' handler tables, `edit_executor` for
   `edit_estimate`, `delegate_create_estimate` (with its overage question) for
   `create_estimate`, `maple_metrics` for `metric`. Replies come from the
   existing templates (CLAUDE.md "Friendly first-person tone"), so every reply
   still names its target. Its own TDD plan, written then.
2. **Per-company switch (D11):** `Company.maple_pipeline:
   Optional[Literal["current", "planner"]] = None`, set by
   `scripts/set_maple_pipeline.py`. **Missing or `None` means the current
   pipeline**, so no migration and no backfill: only a company someone switched
   has the field. Anything unreadable also means current.
   `_orchestrate_turn` branches after the shared turn prelude (lock, limits,
   context load) and before `decide_turn`; both branches end in
   `finalize_orchestrate_result`. A conversation's open question is answered by
   the pipeline that asked it — the switch takes effect at a turn with no open
   question.
3. **Rollout (D20):** Simon's company in Dev → every Dev company → release →
   3Maples' own company in production → two or three customers → everyone.
   Shadow stays on in Dev for the companies not yet switched.
4. **Rollback:** setting the field back to `current` takes effect next turn.
5. **Retirement:** four weeks after the last company switches, with no rollback
   used, the current pipeline's language-reading code is deleted: the router
   pre-handlers' detectors, `decide_turn`'s heuristics, the orchestrator ladder
   and classifier, the agents' classify/extract calls, `command_grammar.py`,
   `metric_spec.py`, §9.2's reply matching, and the routing snapshot (its
   corpus becomes planner eval data). CLAUDE.md's Maple section and the
   phrasing reference are rewritten in the same change.

## 13. Build order

Each step: failing test first; scoped `./run_mypy.sh` and `./run_ruff.sh`;
related tests only; one commit. Steps 1–3 of the tracker don't depend on the
planner and can ship first — it is useful on its own.

| Step | Work | Tests |
|---|---|---|
| 0 | Usage capture for every LLM call (§5.1): `cached_tokens`, `cache_write_tokens`, `credits` and `turn_id` on `LLMUsageEvent`; `_extract_token_usage` reads them; `compute_cost_usd` prices them; the counters and the Stripe meter take `credits` (D17); `LLM_CACHED_TOKEN_CREDIT_RATE`; the explicit-mode cache helper in `services/llm/factory.py` | a response with cached/write details records them; cost at the cached and write rates; the credit formula; the `$inc` and the meter event carry `credits`; a turn's events share its `turn_id`; the helper's request carries the mode and one breakpoint |
| 1 | `services/maple_outcomes.py` — `Outcome`, `classify` (§9.2) | the constants table; each structured marker; questions, cancels and empty lists are not unanswered |
| 2 | `maple_unanswered` model (registered in `database.py`), TTL; recorded from `_finalize_result` and the four early exits as a background task; flag in `config.py` and `.env.example` | one endpoint test per reason, including a credit refusal and `translation_unavailable`; a recording failure doesn't reach the user |
| 3 | `scripts/export_unanswered.py` | grouping and counts; file format |
| 4 | `agents/planner/schema.py` — `Plan`, actions, `RecordRef`, `Unsupported`; reuse `EditCommand` and `MetricAsk`'s fields | valid and invalid plans; no id field anywhere; one-of rule |
| 5 | `snapshot.py` — context → fenced state text | anchors with age, open question, list rows, last request's tax; nothing outside the allowlist |
| 6 | `planner.py` + prompt through the cache helper; `/agent-prompt-review` | fake LLM: parse, timeout, malformed output → error recorded; the static block is identical for two companies and over 1,024 tokens; the request is explicit-mode with one breakpoint at the end of the static block |
| 6a | One live call twice in a row: the second reports `cached_tokens` > 0. If langchain drops the content-block breakpoint, switch the planner to the raw `AsyncOpenAI` client (§5.1) | a report, not a gate |
| 7 | `resolve.py`, `policy.py` (dry-run) on the existing lookups | company scoping (another company's name never resolves); ambiguity; `step`; every policy outcome including overage |
| 8 | `services/maple_shadow.py` + `maple_shadow_turns`, TTL; hook in `_orchestrate_turn` after the page signals; `decide_turn`'s verdict passed through; tenant-less LLM attribution set inside the task; flag in `config.py`, `.env.example` and the Render dashboard; the planner's outcome into `maple_unanswered` | endpoint test: response unchanged with shadow on; a shadow exception doesn't reach the user; no counter bump, no meter post; context not saved; the snapshot carries the viewed record |
| 9 | Adapter and comparison | agree / differ / unsure, compound messages, couldn't-vs-would |
| 10 | `scripts/export_shadow_sessions.py` | one file per conversation, never split by time; day headings; a conversation begun before the window; tokens and credits per turn and in total; file format |
| 11 | **Parity run** (D18): the planner, live, over every corpus that pins today's behaviour, scored against the answer each already records: (a) the 1,216-phrase routing corpus in each of its states, against `snapshot_routing.json` (domain and kind); (b) the 206 CRUD-coverage phrasings, against their expected intent; (c) the 256 acceptance conversations, run through the endpoint with shadow on and the planner live, against the seeded test world — 539 turns in every conversation state, through the exact §8 comparison, a dry run of the window itself; (d) **every ✅ row of the phrasing reference**, read by `scripts/phrasing_reference_rows.py` (§4.5 point 3), against the row's intent and agent, with unreadable rows listed as not checked. About 2,700 worker-model calls; under $5 | **The bar:** no ✅ phrasing (reference) or `expected` row (corpus) comes back from the planner as `unsupported` or `not_understood`, and every `differ` is read and either fixed or explained in the report. Blockers (§11) apply here too. The run is kept as the planner's live-tier regression suite (`llm_e2e`, like `test_maple_routing_live.py`), run before every prompt, schema or model change from here on — not only at retirement |
| 11a | Existing calls onto the cache helper (§5.1), largest fixed prompts first, by the per-feature numbers from step 0 | each moved call's request is explicit-mode; its feature's cached share rises in `llm_usage_events` |
| 12 | ~~Deploy, two-week window, review~~ — D20: the Dev loop (§11), until the planner is clearly better | the parity suite, run after every planner change |
| 13+ | Switchover (§12), only after Simon's decision — Dev first, then production | [`2026-10-07-maple-planner-switchover-plan.md`](2026-10-07-maple-planner-switchover-plan.md) |

## 14. Risks

| Risk | Mitigation |
|---|---|
| Shadow spend is higher than expected | One worker call per turn, its static part cached; spend visible on day one under `maple.shadow.plan`; the flag turns it off |
| Caching silently doesn't happen (a field dropped on the wire, a per-turn value in the static block, a prompt under 1,024 tokens) | Step 6a's live check; the static-block tests; day one's cached share in `llm_usage_events` |
| Shadow slows the server | Runs after the response; 20 s timeout; Maple's LLM concurrency limiter still applies |
| Dev traffic is only what Simon tries (D20) | The parity suite is the measure; each phrasing worth keeping becomes a reference row, so later runs check it |
| Production's phrasings were never shadowed before the switch (D20) | The parity suite pins every phrasing today's Maple handles; production rolls out with 3Maples' own company first; rollback is one field. Optionally, shadow 3Maples' own production company (`MAPLE_SHADOW_COMPANIES`) for a few days before switching it |
| The comparison flags too much as `unsure` | Reviewer reads `unsure` like `differ`; tighten the adapter after the first export, not during the window |
| The unanswered classifier misses a reason (a reply worded outside the constants) | It under-reports, never invents; the constants test fails on a rename; the shadow comparison still surfaces the turn when the planner would have acted |
| The current pipeline keeps changing (as it did 10-02 → 10-06) | D14's freeze; the doc's §3 and §4.2 are re-checked against the code before step 4 starts |
| The planner reads a phrasing today's rules handle as something else, or not at all | Appendix A's map before the schema; the snapshot test for every question kind; the parity run (step 11) before the window, kept as the regression suite |
| The planner looks good in shadow but executes worse | The executor reuses today's handlers; rollout starts with our own company; rollback is one field |

## 15. Gap review (2026-10-06)

Checked against the code before this draft was closed. Each found gap is fixed
in the section named.

| Checked | Found | Fixed in |
|---|---|---|
| Does every turn pass through `_finalize_result`? | No — the two credit refusals, `translation_unavailable` and the 500 catch-all return before the closure exists | §7.1 (not shadowed), §9.2 (recorded at the exit) |
| Does a background task carry the user's LLM attribution? | Yes — Starlette runs it in the request's context, so a shadow call would have billed the company | §7.2 |
| When is the context copy taken? | "At load" was before the page signals; the planner's `viewed` reference needs them | §7.1 |
| Can the comparison see how each side read an open question? | Not from the response alone | §8 |
| What is a conversation for the file? | `ConversationContext.conversation_id`, made per document (`conversation_store._new_conversation_id`); Clear deletes the document, so the next message makes a new id | §10.1 — confirmed |
| Where do credits come from? | `record_llm_usage` `$inc`s the raw total and posts it to the Stripe meter; both must take the weighted number | §5.1 (D17), step 0 |
| Does a planner `clarify` hide a misread? | It could; it is logged as `ask` in shadow either way | §9.3 |
| Does the schema cover every phrasing the reference marks ✅? | Not in the first draft — eleven ops were missing (listed in §4.5), and nine multi-step question kinds had no way to reach the planner | §4.2, §4.5, §5 (snapshot), Appendix A |
| Is parity measured before the window? | D15 covered 125 of ~2,000 pinned phrasings | Step 11 (D18) |
| Is the phrasing reference itself checked, not only the test corpora? | Not in the first draft; the reference holds ✅ phrasings no test runs | §4.5 point 3, step 11 (d) — and kept as a regression suite, so the reference becomes a living test |
| Does freshness survive a long absence? | No — it is counted in turns, so a three-week-old anchor is "fresh" on return | §6 (D19: 24 h for anchors and lists, 1 h for open questions) |
| Is any decision still open? | None — P7 and P8 were decided 2026-10-07 as D18 and D19. The cached-token credit rate follows the price ratio (D17: a discounted token is a discounted credit), 0.1 today, kept in config so a price change is a setting, not a code change | §5.1 |

Nothing else is open. The things this design deliberately leaves to later
plans: the executor (§12.1), caching a second breakpoint after the history
(§5.1), moving existing calls onto the cache helper (step 11a), and the
retirement change (§12.5).

## 16. What not to do

- Don't give the plan an id field, or resolve a reference outside the caller's
  company.
- Don't let shadow save `ConversationContext`, write a record, or bill a
  company.
- Don't write session files or reports on the server.
- Don't add outcome markers across the current pipeline's handlers — classify
  in `maple_outcomes.py`; the planner carries them natively.
- Don't add phrasings to the current pipeline (D14, revised by D20) — they go to the planner.
- Don't switch a company over without Simon's decision from the review.

## Appendix A. Parity map — today's catalog → the plan

One row per section of the phrasing reference (`maple-phrasing-reference.md`),
plus the intents, grammar entries, pre-handlers and question kinds that aren't
sections of their own. This table is the *design* check — every section has
a carrier; step 11 (d) is the *runtime* check — every ✅ row produces the
right plan. "Carrier" is the action, reference form, snapshot item
or policy that handles it. This table is finished before step 4 starts and is
the checklist the schema is built from; a row whose carrier is blank is a gap.

| Today | Carrier in the plan |
|---|---|
| §1.0 core grammar entries: list/get estimates, list/get work items, create/rename estimate, add/remove/rename work item, set percentage / gross margin / total, add note, set work-item field, set estimate field, rename pronoun, add described work item | `list`/`get` (estimate), `list_work_items`/`get_work_item`, `create_estimate`, `edit_estimate` (`EditCommand`s: set_title, add/remove_work_item, set_work_item_description/division, set_work_item_percentage/gross_margin/total, add_*_note), `generate_work_item`; references by `name`/`focus`/`listed` |
| §1.0 ported entries: set_status, set_estimate_description/title, generate_work_item, set_recurring, list_work_item_lines, query_work_item_field, adjust_assumption, apply_template, link_property, estimate_note | `set_status`, `edit_estimate` (set_description/set_title), `generate_work_item`, `set_recurring`, `list_work_item_lines`, `work_item_field`, `adjust_assumption`, `apply_template`, `link` (estimate→property), `add_note` |
| §1.1 count and status queries | `count` (estimate) with a status set; `get` with `field: status` |
| §1.2 one estimate's value / total | `get` (estimate) with `field: total`, `before_tax` |
| §1.3 generation, gathering, sufficiency questions | `create_estimate`; the gathering flow in the snapshot (§4.5 point 2) + `answer` |
| §1.3.1 assumptions and adjustments | `adjust_assumption` |
| §1.4 status transitions, status offer after generation | `set_status`; the `status_offer` question + `answer` |
| §1.5.1–1.5.3, 1.5.5–1.5.8 work-item and line edits | `edit_estimate` (`EditCommand`s, unchanged) |
| §1.5.4 recurring | `set_recurring` |
| §1.6 linking | `link` / `unlink` (unlink → `unsupported: out_of_chat`) |
| §1.7 anaphora / active estimate | `focus`, `viewed`; freshness in policy |
| §1.8 outbound drilldowns (estimates using a material / role / for a contact or property) | `list` (estimate) with a cross-record filter |
| §1.9 dashboard queries | `dashboard` |
| §1.10 estimate title / description / notes | `edit_estimate` (set_title, set_description, add_estimate_note) |
| §1.11 multi-turn work-item conversation (which work item?, value prompts, resume) | `pick`/`value` questions in the snapshot + `answer`; `step` for compound turns |
| §1.12 metrics, rankings, by month, comparisons, ratios, line totals; "what about X?", "and last month?", "does that include tax?" | `metric` (`MetricAsk` fields); `redo_last` |
| §2–§5 ×.1–×.2 direct and casual CRUD | `create` / `update` / `delete` / `get` / `list` per domain |
| §2–§5 ×.3 possessive, ×.7 verbless | the planner (no carrier needed) |
| §2–§5 ×.4 count, ×.5 filter / find | `count`, `list` with filters (city, role, category, unit, qualifier) |
| §2–§5 ×.6 field-targeted update; field-then-value flow | `update` (field → value); the `value` question + `answer` |
| §2.7 address formats on create | `create` (property); address normalisation stays in the executor |
| §3.9 notes, links and follow-ups for contacts and properties | `add_note` / `list_notes` / `delete_note`; `link`; `redo_last`; `focus` by pronoun domain |
| §4.8 size-scoped material operations | material `get`/`update`/`delete` with `size`; "which size?" as a `pick` question |
| §4.10 qualifier lists | `list` (material) with a qualifier filter |
| §4.11, §5.10 create one question at a time | `create` with the fields given; the policy asks the next field; `answer` |
| §4.12, §5.11 catalog and role figures | `catalog_figure` |
| §6.1–6.6 templates | `get` / `list` / `count` / `delete` (template); edits → `unsupported: template_edit` |
| §6.7 apply template, template-driven create with size | `apply_template`; `create_estimate` with `template` + `size`; the `template_size` question + `answer` |
| §7.1–7.6 tasks CRUD, filters (status, overdue, due window, property, assignee) | task `create` / `update` / `get` / `list` / `count`; `set_due` / `clear_due` |
| §7.4.1 task counts by person / property | `task_count` |
| §7.6.1 notes on a task (append) | `update` (task, `notes`, `append`) |
| §7.7 status, §7.8 assignee, §7.9 archive, §7.10 convert | `set_status`; `assign` / `unassign`; `archive` / `unarchive`; `convert_task` |
| Calculator (incl. open math, missing-parameter questions) | `calculate`; the `calculation` question + `answer` |
| Help / user-guide questions | `help` |
| Personal and social questions about Maple | `social` |
| Meta turns: thanks, cancel, repeat, start over, show more | `acknowledge`, `cancel`, `repeat`, `unsupported: out_of_chat` (clear chat → the panel's button), `show_more` |
| List refinement ("just the drafts"), positional picks ("the second one") | `refine_last`; `listed` |
| Out-of-chat redirects (12 capabilities) | `unsupported: out_of_chat` + capability |
| Policy refusals: bulk delete, equipment, material categories, template edits, notes on catalog items, labor burden, material cost | `unsupported` reasons (§4.4) |
| Deletes always ask; Owners/Admins only | policy `would confirm` / `would refuse` |
| Overage question on a create | policy `would confirm`; the `overage` question + `answer` |
| Property-link confirmation, optional follow-up, estimate follow-up, note body / note delete, fuzzy "did you mean", task confirmations and menus | each a question kind in the snapshot + `answer` |
| Any language | the planner reads the original; `reply_language` |

