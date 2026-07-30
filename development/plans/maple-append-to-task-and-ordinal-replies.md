# Maple: "add to the task(s) …" appends, and ordinal replies to numbered lists

**Status**: design approved 2026-07-30
**Scope**: `platform/` only. Two independent user-reported defects, plus one
wording bug found while tracing the second.

---

## 1. Background

Two failures reported from a live Maple session (mobile, `maples-dev.web.app`).

### 1.1 "Add to the tasks to buy more milk." created nothing

Maple had just created a task *Take out the trash*. The user then sent:

> Add to the tasks to buy more milk.

intending to append "buy more milk" to that task's notes. Maple answered
*"What should the task be called?"* — create's missing-title question.

**Root cause (by inspection; the red tests in §4 confirm it).** The message
resolved to `create_task` and then failed content extraction, so create had
neither a title nor a description and had to ask.

Two independent gaps, in a *mirrored pair* of detectors that the codebase
already treats as one contract:

| Layer | Detector | Gap |
|---|---|---|
| Classifier | `is_task_notes_update_request` — `agents/orchestrator/intents.py` | 4th `_TASK_NOTES_UPDATE_RES` pattern requires `task` + a **colon**. |
| Task agent | `detect_notes_update` → `_ADD_BARE_NOTES_RE` — `agents/task/text_helpers.py` | Same two gaps. |

1. **`task\b` does not match `tasks`.** The plural breaks every pattern.
2. **No slot for the `add **to the** task …` shape.** The colon is currently
   the only thing that can mark the trailing content.

Because the classifier never returned `update_task`, the Task agent's notes
path was never reached; `create_task`'s `_CREATE_CONTENT_RE` then also failed
(its preamble only admits `add [me] [a|an|another|the] [new] task`), which is
why the user saw create's question rather than a notes append.

### 1.2 "The first one." did not pick from a numbered list

Maple offered a numbered property list:

> I found a few properties that look close to "Bob's residence": (1) Bob
> Residential; (2) Tang's Resident. Which one did you mean?

The user replied *"The first one."* and got
*"I couldn't find a property matching 'The first one.'"*.

**Root cause.** `_ORDINAL_PATTERN` in
`routers/agent_helpers/pending_property_link.py` matches **digits only**
(`2`, `#2`, `(2)`, `option 2`). Word ordinals fall through to the free-text
correction path, which tries to resolve "The first one." as a property name,
finds nothing, and re-prompts.

### 1.3 Placeholder label leaks into the re-prompt (found while tracing 1.2)

The same failure produced:

> I believe you are looking for 'that property'.

When candidates are armed there is **no pinned property**, so `property_label`
is `""` and the `"that property"` fallback string is rendered into a confirm
prompt that has nothing to confirm. That branch must re-render the numbered
list instead.

---

## 2. Goals

- `add to the task(s) …` (singular or plural, with or without a colon)
  **appends** to the current task's notes rather than creating a new task.
- A reply of `the first one` / `second` / `3rd` / `the last one` selects from
  any numbered list Maple offers.
- Word-ordinal handling lives in **one** helper, not three divergent copies.
- The armed-candidates failure branch re-shows the list instead of the
  `"that property"` placeholder.

## 3. Non-goals (explicitly deferred)

- **`add to my task list: buy milk`** — this is genuinely *create*-shaped (a
  new task on the list, not a note on a task). Neither the notes patterns nor
  `_CREATE_CONTENT_RE` handle it today. Deliberately out of scope; log as a
  follow-up.
- The exact-multi-match property branches in
  `agents/estimate/crud_handlers.py` (~lines 1075, 3082) arm **no** pending
  record at all, so no ordinal reply of any kind can work there. Untouched —
  a separate defect with a different fix.
- No LLM involvement in ordinal resolution. The menu is already numbered;
  a model call here adds latency and a hallucination risk to a hot path.

---

## 4. Design

### 4.1 Task notes-append widening

Both detectors get the same two widenings, applied symmetrically:

- `tasks?` in place of `task\b`.
- The content separator becomes **either** the existing `[:\-]` **or** a
  connector word `to` / `about` / `that`, followed by the content.

Sketch (Task agent side; the classifier pattern mirrors it without the
capture group):

```
\b(?:add|append|attach|put)\s+(?:this\s+|that\s+|the\s+following\s+)?
(?:to|on|onto)\s+{TARGET_OR_PRONOUN_tasks?}
(?:\s*[:\-]\s*|\s+(?:to|about|that)\s+)
(?P<value>.+)$
```

**Why `add a photo to the task` stays safe.** The pattern requires the verb
to be followed immediately by `to`/`on`/`onto` (only `this` / `that` /
`the following` may intervene). `add **a photo** to the task` never enters the
pattern at all — the colon was never what protected it.

**Target resolution is unchanged.** An empty target hint flows through the
existing order in `agents/task/resolver.py`: `active_task_id`, then the
recency fallback. In the reported transcript that lands on *Take out the
trash*.

**Accepted risk.** With no active task, the recency fallback picks the
most-recently-updated task in the company, which may be unrelated. This is
pre-existing behavior for *every* notes phrasing and is not changed here. It
is mitigated by the append being non-destructive (`mode="append"`) and by
Maple echoing the updated task back to the user.

**Length-bounding.** Every new scanning segment stays length-bounded, per the
existing ReDoS note in `agents/task/text_helpers.py` (`_SCAN`, `_TARGET_BODY`).
No new nested unbounded lazy quantifiers.

### 4.2 Shared ordinal helper

New in `agents/text_utils.py` (the shared-helper home; consistent with the
2026-07-30 relocation of the pronoun/rename helpers):

```python
def match_ordinal_reference(text: str, *, count: int) -> Optional[int]:
    """1-based index into a numbered list, or None."""
```

Accepts, anchored `^…$` on the whole reply:

- digits — `2`, `#2`, `(2)`, `[2]`, `option 2`, `number 2`, `no. 2`, `choice 2`
- word ordinals — `first` … `tenth`, `1st` … `10th`
- optional leading `the`, optional trailing `one`
- `last` / `the last one` → `count`

Returns `None` for anything else, and for an in-range check failure the caller
keeps its existing out-of-range re-ask.

**Anchoring is the safety property.** A property named "First Street" is not
`^(the )?first( one)?$`, so it still reaches the correction path. A bare reply
of exactly `first` is read as a menu pick — the same trade the digit matcher
already makes (`2` wins over the street "12 Oak Rd").

**Call sites:**

1. `routers/agent_helpers/pending_property_link.py::_match_ordinal` — becomes
   a thin wrapper over the shared helper. **This is the reported fix.**
2. `agents/task/confirmation.py::_pick_candidate` — refactored onto the shared
   helper, replacing its local `_ORDINAL_WORDS`. Extends that agent from
   `first`–`fifth` to `first`–`tenth` plus `last`.

`agents/estimate/text_helpers.py::_ORDINAL_POSITION_MAP` is **left alone**:
it is 0-based and serves work-item row targeting, not menu replies. Folding it
in would be a semantic change to a different feature.

### 4.3 Placeholder-label fix

In `handle_pending_property_link_confirmation`, the "no matches" branch after
free-text resolution currently always calls `_confirm_prompt(property_label,
…)`. When the pending record carries `candidates` and no pinned
`property_id`, re-render the numbered list and stay armed instead.

---

## 5. Testing

TDD, per CLAUDE.md — every item below is written **failing first**.

**Red tests that reproduce the reports (these also serve as the empirical
confirmation of the §1 regex analysis):**

- `"Add to the tasks to buy more milk."` → classifier returns `update_task`;
  Task agent appends to the active task; no second task is created.
- `"The first one."` against an armed 2-candidate property record → links
  candidate 1.

**Extending:**

- Notes append: singular/plural × `to` / `about` / `that` / `:` / `-`.
- Regression: `"Add a photo to the task"` is **not** claimed as a note;
  `"Add a task to buy more milk."` still creates.
- Ordinal helper: unit table over digits, words, `1st`–`10th`, `last`,
  out-of-range, and non-ordinal text ("First Street", "12 Oak Rd").
- Task confirmation: `"the last one"` now resolves (new capability).
- Placeholder bug: unresolvable free text against an armed record re-renders
  the list and does **not** emit `"that property"`.

**Files**: `tests/test_maple_task_operations.py`,
`tests/test_maple_task_crud.py`, `tests/test_pending_property_link.py`
(or nearest existing), plus a new unit test for the shared helper.

**Gates**: `./run_tests.sh` on the touched files, `./run_mypy.sh` and
`./run_ruff.sh` scoped to `agents/` and `routers/agent_helpers/`.

**Docs**: `documentation/development/maple-phrasing-reference.md` must be
updated in the same change — new supported phrasings, the §12.3 snapshot
counts, and the "Last updated" date. Required by CLAUDE.md.

---

## 6. Risk

| Risk | Mitigation |
|---|---|
| `add to the tasks …` now appends where a user meant a new task | Append is additive, never overwrites; Maple echoes the updated task back |
| Bare `first` shadows a property literally named "First" | Anchored match only; same trade the existing digit matcher makes |
| Regex widening re-opens the ReDoS class documented in `text_helpers.py` | All new segments length-bounded; no nested unbounded lazy quantifiers |
| Classifier and Task-agent patterns drift apart | Both edited in one change, with paired tests at each layer |
