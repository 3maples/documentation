# Estimate readable IDs — `E0042`

## Context

Tasks gained a short, human-quotable identifier in August 2026: `T` plus four
Crockford Base32 characters, sequential per company off an atomic counter,
server-owned, searchable, and resolvable by Maple. Estimates never got the same
treatment. They carry an `estimate_id` of the form `EST-4E73F7BB` — the literal
`f"EST-{uuid.uuid4().hex[:8].upper()}"`, copy-pasted at five creation sites,
with no allocator, no format constraint, and **no unique index**.

That code is worse than the one Tasks replaced in three specific ways:

- **It can't be spoken.** Eight random hex characters is unusable by voice, and
  voice is the point: a user in a truck should be able to say "show me estimate
  forty-two" and land on the right document.
- **Every lookup is an unindexed scan.** The four Beanie queries in the estimate
  agent scan the collection; `agents/cross_resource.py::find_estimate_by_code`
  loads *every estimate in the company* and compares in Python.
- **Nothing guarantees uniqueness.** The field is a plain required `str` with no
  index, and the API lets clients supply their own value.

**Outcome:** estimates get `E0001`, `E0002` … `E0042` … `E9999` — the prefix
plus a zero-padded **decimal** counter. Server-owned, unique per company,
indexed, backfilled over the existing data, searchable from a new
`GET /estimates?search=`, and resolvable by Maple from the ID alone.

### Decisions confirmed with the user

| Question | Decision |
|---|---|
| Format | **`E` + 4 decimal digits**, widening to 5 past `E9999`. Not Crockford Base32. |
| Why decimal | **Voice.** The number a user counts and the code they read are the same object. |
| Existing estimates | **Renumber them all** in `created_at` order. No legacy alias field. |
| Client-supplied codes | **Removed.** `estimate_id` drops off `CreateEstimateRequest`; the server owns it, as with Tasks. |
| Model field name | **Stays `estimate_id`.** No data migration, no portal type churn. |
| Server-side search | **Yes** — add `GET /estimates?search=`, matching `GET /tasks?search=`. |
| Phase ordering | Dual recognition (accepting `EST-` and `E####` simultaneously) is **skipped**; the regex switch rides along with the generation flip. |
| Spoken form | **Digit by digit** — "E zero zero four two". A bare "estimate 42" is deliberately NOT supported. |
| Tasks stay Crockford | Accepted inconsistency, tracked as follow-up **#504**. |

### Why not Crockford, given Tasks use it

The counter is what gets encoded, so under Crockford the displayed code diverges
from the count almost immediately: estimate #10 renders as `E000A`, #42 as
`E001A`. A user who has written ten estimates and says "estimate ten" is naming
nothing. With a decimal body the two are the same object — #42 *is* `E0042` —
which is exactly the property the short prefix was chosen to enable.

Crockford's benefit is also the wrong one here. It drops I, L, O and U because
they **look** confusable with 1, 1 and 0 on a screen. It does nothing about the
letters that **sound** alike — B, D, E, G, P, T, V and Z are the standard
speech-recognition confusion set — so a letter-bearing body pays Crockford's
cost without collecting its benefit for a user speaking into a phone in a noisy
cab. Digits are the most reliably transcribed token class there is.

Capacity is the trade, and it is comfortable. Four digits is 9,999 per company.
The plan tiers allow 20 estimates per billing period on Free and 100 on the paid
tier (`services/billing/plan_config.py:68-103`; the top tier's `1_000_000` is a
sentinel for unlimited, not an expectation), so the heaviest realistic account
runs ~1,200/year — roughly eight years of headroom. Past that the encoder
**widens rather than fails**: #10,000 becomes `E10000`, the same policy
`encode_crockford_base32` already applies for Tasks.

### What this deliberately does not do

**No legacy alias.** Renumbering without keeping the old code means the
`EST-4E73F7BB` strings already printed into generated Google Docs, into
`audit.metadata.duplicated_from`, and into persisted `chat_history` stop
resolving. Accepted knowingly: an alias field plus its index is real permanent
weight to carry for references that are read by humans, not by the app.

**Existing Drive files are not renamed.** `routers/estimates.py:1578` names each
generated doc `Estimate-{estimate_id}-V{n}`. New versions will be named
`Estimate-E0042-V3`; the `Estimate-EST-4E73F7BB-V1` files already sitting in
Drive keep their names forever. Renaming them would mean a Drive write per
historical version for a cosmetic gain.

**Routes stay on the Mongo `_id`.** `getEstimateDetailsPath` and every
`/estimates/:id/with-activity` link keep using the ObjectId, exactly as Tasks
kept `?taskId=`. The readable ID is for humans and for Maple, not for URLs.

**Tasks are not migrated.** They keep `T4K7Q`. Tracked as follow-up #504 with
the case for eventually aligning them; not worth a second renumber on its own.

---

## Design decisions

### Format: `E` + 4 decimal digits

`ESTIMATE_READABLE_ID_PREFIX = "E"`, `ESTIMATE_READABLE_ID_WIDTH = 4`.
Formatting is `f"E{seq:04d}"` — `str.zfill` past the width, so #10,000 yields
`E10000` rather than raising.

**Digits eliminate the prose false-positive problem outright.** No English word
contains a digit, so `E[0-9]{4,7}` cannot match running text. This is a
substantive simplification over the Task scheme, which needs
`(?-i:T[0-9A-HJKMNP-TV-Z]{4,7})` precisely because lowercase `tasks` parses as
`T`+`ASKS` and `trees` as `T`+`REES`. Three consequences:

1. **Matching is case-insensitive.** `e0042` is safe to accept bare. This
   matters because speech-to-text output is usually lowercased.
2. **No cue word is required** for the canonical form. Tasks permit lowercase
   only behind a `task`/`#` lead-in; estimates need no such hedge.
3. **A well-formed ID that misses should stop, not fall through** — see
   "Miss behavior" below. This is a deliberate divergence from Tasks.

### Normalization: the spoken and typed forms

`normalize_estimate_readable_id(raw)` canonicalizes to the stored form and
returns `""` (never raises) for anything that isn't ID-shaped, so callers can
use it as a cheap "is this an ID?" test — the same contract as
`normalize_task_readable_id`. It must accept, at minimum:

| Input | Why | Result |
|---|---|---|
| `E0042`, `e0042` | canonical, either case | `E0042` |
| `#E0042`, `E-0042` | typed decorations | `E0042` |
| `E 0 0 4 2` | **speech-to-text spacing every digit** | `E0042` |
| `E42` | user drops the padding | `E0042` |

Internal spaces and hyphens are collapsed *within* a digit run only, bounded to
seven digits, so the pattern can't stitch across a sentence boundary.

**Detection and normalization deliberately differ in strictness.** The free-text
pattern below requires a full 4-7 digit body, so scanning a chat message never
treats `E5` as an ID. `normalize_estimate_readable_id` is the looser of the two
and accepts an unpadded `E42`, because its other callers hand it a value the user
*meant* as an ID — the search box, an explicit field — where there is no
surrounding prose to be confused by. Keep the two contracts separate;
widening the free-text pattern to short bodies is how model numbers and
quantities start resolving as estimates.

**A bare "estimate 42" is deliberately not supported.** Users say the digits
individually — "E zero zero four two" — which the spaced-digit row above already
covers. Supporting the bare number would mean matching `(?:estimate|quote)\s+#?\d+`,
and that reads a quantity as an identifier: "estimate 3 hours of labor" would
offer `E0003` as a candidate. Requiring the prefix keeps every candidate an
unambiguous statement of intent, which is what makes the miss behavior below
safe to tighten.

### Counter: `Company.next_estimate_seq: int = 0`

The same atomic idiom as `next_task_seq` and
`services/estimate_quota.py::try_claim_estimate_slot` —
`find_one_and_update({"_id": cid}, {"$inc": {...}}, return_document=AFTER)`. No
new collection, no `database.py` registration; `$inc` creates a missing field at
0, so existing companies need no migration.

Comment on the field that **it is not an estimate count** — deletes leave
permanent gaps, and the plan cap in `services/estimate_quota.py` counts
documents. The identical warning on `next_task_seq` exists because that
optimization is tempting and wrong.

**Allocation goes after the quota check.** `routers/tasks.py:131` deliberately
allocates only once the plan cap has passed, so a rejected create doesn't burn a
sequence number — which matters more here, because a gap in a decimal sequence
is visible to users in a way a gap in Crockford is not. The estimate create path
claims its slot through `try_claim_estimate_slot` /
`claim_estimate_slot_with_status`; allocation must sit after that, and before
insert.

### Modules

**`platform/services/readable_id.py`** gains the estimate constants, formatter
and normalizer alongside the existing Crockford ones. The Crockford codec itself
is **not** parameterized — estimates don't use it, so the generic
`format_readable_id(seq, *, prefix, width)` refactor considered earlier is
dropped as speculative. `encode_crockford_base32`, `decode_crockford_base32` and
the two `*_task_*` wrappers are untouched; no Task behavior changes and no Task
call site moves.

Update the module docstring: it currently frames the file as a Crockford codec.
It now holds two schemes, and the docstring should say why they differ —
estimates are spoken aloud, tasks are read off a screen — so the next person
doesn't "fix" the inconsistency without reading follow-up #504.

**`platform/services/estimate_readable_id.py`** — a sibling of
`task_readable_id.py`. Exports:

- `allocate_estimate_readable_id(company_id) -> str`
- `reserve_estimate_readable_id_block(company_id, count) -> Tuple[int, int]`
- `insert_estimate_with_readable_id(estimate, *, attempts=3) -> Estimate`,
  retrying a `DuplicateKeyError` **only** when `keyPattern` names
  `estimate_id`, and re-raising any other unique violation rather than
  swallowing it in the loop.

### Model changes

```python
# platform/models/estimate.py
estimate_id: str = ""   # server-owned; assigned by services/estimate_readable_id.py
```

The field stays a non-`Optional` `str`. Task's `readable_id` had to be
`Optional[str] = None` only because pre-backfill tasks genuinely had no value;
every estimate already carries a code, so the portal needs no null handling and
`portal/src/types/api.ts:314` is unchanged. The `""` default exists solely so
the document can be constructed before the allocator assigns — it is never a
persisted state on any path that goes through `insert_estimate_with_readable_id`,
and the unique index below will reject a second `""` in a company, which is the
correct loud failure if some path ever bypasses the helper.

Index, added to `Estimate.Settings.indexes`:

```python
pymongo.IndexModel(
    [
        ("company", pymongo.ASCENDING),
        ("estimate_id", pymongo.ASCENDING),
    ],
    unique=True,
    partialFilterExpression={"estimate_id": {"$type": "string"}},
    name="company_estimate_id_unique",
),
```

Note the house style in this file: indexes are declared namespaced
(`pymongo.IndexModel` / `pymongo.ASCENDING`) and **every one carries an explicit
`name=`**, both existing indexes included. Follow it.

`sparse=True` does **not** substitute — on a compound index a document is
included if *any* keyed field exists, and `company` always does.

This index is also the performance fix. It converts the four direct Beanie
lookups in `agents/estimate/crud_handlers.py` (`:890`, `:1001`, `:2315`,
`:2776`), the two Python substring scans in
`routers/agent_helpers/estimate_resolver.py:77-80` and
`delegate_get_estimate.py:118-122`, and the full-collection scan in
`agents/cross_resource.py:97-116` from scans into indexed point lookups.

### Generation: five sites collapse to one helper

| Site | Current |
|---|---|
| `routers/estimates.py:323` | `payload.estimate_id or f"EST-{uuid…}"` |
| `routers/estimates.py:326` | same, `skip_generation` branch |
| `routers/estimates.py:871` | duplicate endpoint |
| `routers/estimate_helpers/ai_generation.py:415` | `request.estimate_id or f"EST-{uuid…}"` |
| `agents/estimate/crud_handlers.py:645` | create-from-template |

All five build an `Estimate` and insert it, so all five become
`insert_estimate_with_readable_id(estimate)`. Drop `import uuid` from
`routers/estimates.py:3` — verified: those three f-strings are its only
consumers in the file.

`CreateEstimateRequest.estimate_id` (`routers/estimates.py:225`) and
`CreateEstimatePayload.estimate_id` (`portal/src/api/estimates.ts:27`) are
removed. Because `CreateEstimateRequest` sets `model_config = {"extra":
"ignore"}`, an old client still sending the field gets it silently dropped
rather than a 422 — the desired behavior during a rolling deploy.

**Test churn:** roughly 17 call sites across `tests/test_estimate_api.py` inject
codes like `"test-001"` through this override and must switch to reading the
server-assigned value off the create response. This is the largest mechanical
piece of the change.

### Update path — already safe, needs a test

`UpdateEstimateRequest` (`routers/estimates.py:920`) sets `model_config =
{"extra": "ignore"}` and simply **omits** `estimate_id` — verified against the
current source. That is the same omission-not-exclusion pattern protecting
Task's `readable_id`, so no change is needed. It does need an explicit **"PUT
omitting the field preserves it"** test, not merely "PUT can't change it". That
distinction is what caught the sparse-write regression on Tasks.

### Maple: regexes and resolution

Canonical pattern, replacing the two divergent `_ESTIMATE_CODE_PATTERN`
definitions that exist today (`agents/estimate/text_helpers.py:64` is
case-sensitive, `agents/orchestrator/service.py:119-121` is not — the
inconsistency is itself a latent bug):

```python
_ESTIMATE_CODE_REF = r"(?<![0-9A-Za-z])[Ee][0-9]{4,7}(?![0-9A-Za-z])"
```

No `(?-i:…)` wrapper and no cue-word variant are needed for this form; digits
carry the disambiguation that case-sensitivity had to carry for Tasks.

Change sites: the two `_ESTIMATE_CODE_PATTERN` definitions above,
`_ESTIMATE_REF_PATTERN` (`agents/orchestrator/service.py:71-73`),
`_PENDING_RELEASE_ESTIMATE_CODE_PATTERN` (`routers/agents.py:256-257`), and
roughly 25 inline `est[-_]` alternatives embedded in other phrase patterns —
`agents/orchestrator/service.py:427, 506, 516, 528, 542, 2286, 2352, 2369, 2435,
2441, 2742`; `agents/estimate/text_helpers.py:811, 817, 834, 843, 865, 875,
882`; `agents/estimate/crud_handlers.py:299, 590, 595`;
`agents/estimate/crud_helpers.py:205`; `routers/agents.py:208`.

**`_ESTIMATE_REF_PATTERN` is the one that breaks ID-only routing if missed.** It
gates estimate routing on `est[-_]…|estimate|quote|bid|proposal`; a message like
"archive E0042" matches none of those, so the orchestrator never reaches the
estimate agent. Tasks needed the equivalent fix
(`agents/orchestrator/intents.py:550-552`) and it was found late.

Resolution changes:

- `agents/estimate/crud_helpers.py:253-258` — `_estimate_code_from_text` runs
  candidates through `normalize_estimate_readable_id`.
- `routers/agent_helpers/estimate_resolver.py:77-80` and
  `delegate_get_estimate.py:118-122` — replace the load-100-then-substring-scan
  with an indexed `find_one`. See "Miss behavior" for what happens on a miss.
- `agents/cross_resource.py:97-116` — `find_estimate_by_code` becomes an indexed
  `find_one` instead of loading the company's whole estimate collection.

User-facing copy naming the old format needs updating: `crud_handlers.py:906`,
`:2336`, `:2800` ("I couldn't find an estimate with code …") and `:996`
("Please share the estimate code (e.g. EST-2026-001)"), which should now offer
the spoken form as the example.

### Miss behavior: a well-formed ID that doesn't exist

**Recommended change, and a deliberate divergence from Tasks.** Today step 2 of
`find_estimate_from_context_or_message` falls through on a code miss, so
"archive E0042" for a non-existent `E0042` continues to the fuzzy title match
(step 4) and then to the most-recent fallback (step 5), returning
`is_fuzzy_match=True`. That is not a safety bug — mutating callers treat the
flag as a cue to confirm, and delete already passes
`allow_recent_fallback=False` — but it produces a confusing prompt: a user who
typed an exact identifier gets asked "did you mean <most recent estimate>?".

Tasks need that fall-through because `TRIMS` and `TREES` parse as task IDs, so a
miss is often not an ID at all. **Digits remove that reason.** An `E` followed by
four to seven digits is an unambiguous statement of intent, so the better
behavior is to short-circuit: return "I couldn't find estimate E0042" and stop,
rather than guessing a different target.

Scope it narrowly — only when the message contains a well-formed `E####`. Every
other path down the ladder is unchanged, and `_estimate_code_from_text`'s callers
in `agents/estimate/` already surface a not-found message of their own
(`crud_handlers.py:906`), so this mainly aligns the orchestrator's resolver with
what the agent layer already does.

### Search: `GET /estimates?search=`

Modeled on `routers/tasks.py:174, 201` and folded into the existing
`_estimate_conditions` (`routers/estimates.py:438-457`) alongside the company /
status / property filters — but with one deliberate difference from Tasks.

**The ID clause is an anchored full-ID match, not a substring.** Title and
description stay case-insensitive `re.escape`d substring regexes; `estimate_id`
does not. Run the search term through `normalize_estimate_readable_id` first: if
it yields a well-formed ID, match `estimate_id` exactly; if it returns `""`, omit
the `estimate_id` clause entirely and search title and description only.

Substring matching on a decimal ID is too noisy to be useful — `42` would match
`E0042`, `E0421`, `E4200` and `E1042` alike — and the ID is the one field a user
searches precisely when they already know exactly what they want. Requiring the
prefix is what makes it precise: bare `42` searches titles, `E0042` finds one
estimate. This is also why the Task substring behavior isn't copied; a Crockford
body collides far less often than a decimal one.

Normalization still absorbs the decorations, so `e0042`, `#E0042`, `E-0042` and
the spaced-digit `E 0 0 4 2` all reach the same query. `E42` works too — that is
the normalizer's documented padding convenience for direct input, and it stays
prefix-anchored, so it names exactly one estimate rather than a family of them.

Property name stays out of the server-side query: it lives on a linked
`Property` document, not on the estimate, and joining it would mean an
aggregation. `EstimatesPage`'s client-side filter keeps matching on the
already-resolved property label, so property search is unchanged in behavior —
it is simply still limited to loaded rows, as it is today.

### Backfill

`platform/scripts/backfill_estimate_readable_ids.py`, modeled on
`backfill_task_readable_ids.py`: dry run by default, `--apply` to write, exit 1
if any document failed.

One difference that matters. The Task backfill selects `{"readable_id": None}` —
documents with no ID at all. Ours renumbers documents that *already have* a
value, so the selector is "not already in the new format":

```python
{"estimate_id": {"$not": {"$regex": r"^E[0-9]{4,}$"}}}
```

That keeps the script idempotent and re-runnable: a second run finds nothing.
Order by `created_at` ascending, group by company, one
`reserve_estimate_readable_id_block(company_id, len(docs))` per company, and
guard each write with the old value so a concurrent edit isn't clobbered:

```python
update_one({"_id": doc["_id"], "estimate_id": old_code}, {"$set": {"estimate_id": new_code}})
```

`modified_count == 0` prints "skipped (already assigned)" and is not an error.

`scripts/db/seed_db.py:338` upserts by `estimate_id` and must be updated, or
re-seeding a dev database will create duplicates rather than upserting.

### Portal

- `EstimatesPage.tsx:365-374` — the search box moves to the server param
  (debounced), matching `TasksPage.tsx:294`. The client-side filter stays for
  the property label only.
- `api/estimates.ts` — drop `estimate_id` from `CreateEstimatePayload`; add
  `search` to the list query.
- `EstimatesTable.tsx:221`, `NewEstimateWithActivityPage.tsx:1342`,
  `DashboardPage.tsx:410, 467`, `EstimatesPicker.tsx:77`,
  `PropertyActivityPanel.tsx:372` — these already render `estimate.estimate_id`
  and need no logic change. Give them `font-mono text-xs` for parity with the
  Task chips (`TasksPage.tsx:622-626`).
- `types/api.ts:314` — unchanged; add a doc comment marking the field
  server-owned and read-only.

### Documentation

- `documentation/development/maple-phrasing-reference.md:388` — the canonical
  `{EST}` format row, currently `EST-0042`, `EST-4E73F7BB`, `EST-2026-001`
  matching `EST[-_][A-Za-z0-9\-_]*`. Also `:363`, `:457`, `:553`, `:559`,
  `:1736`, the affected phrasing-status tags, the §12.3 snapshot counts, and the
  "Last updated" date. Record the spaced-digit form (`E 0 0 4 2`) as supported
  and a bare "estimate 42" as an explicit 🛑 non-goal, so the exclusion survives
  the next person reading the matrix. CLAUDE.md requires this in the same change.
- `platform/user_guides/users_guide.md:156, 313` — both say "its EST- code".
  This file is loaded at runtime by the `maple_guide` responder, so stale text
  here becomes a wrong answer from Maple.

---

## The two ordering landmines

**The unique index cannot ship before the backfill.** Beanie builds indexes
during `init_db`, at app boot. `estimate_id` is a non-null string on every
existing document and has no unique index today, so a partial unique index
deployed before the renumber would be built against the old random-hex data — and
if any two estimates in one company happen to share a code, the build fails and
takes the service down at boot. The index lands only once the backfill has
guaranteed uniqueness.

**Skipping dual recognition opens a window.** Because the `EST-` regexes are
retired in the same phase that generation flips, there is an interval between
that deploy and the backfill run in which existing estimates still carry `EST-`
codes that Maple no longer recognizes. Title-based, positional and
active-estimate-context resolution all still work, so the degradation is
narrow — but Phases 2 and 3 should ship back-to-back, with the backfill run
immediately after the deploy, not scheduled for later.

---

## Phases

Each phase is independently testable. TDD throughout — failing test first. Gate
each with `./run_tests.sh <touched test files>`, `./run_mypy.sh <subtree>` and
`./run_ruff.sh <subtree>`.

**Phase 1 — formatter, counter, allocator.** Add the estimate constants,
`format_estimate_readable_id` and `normalize_estimate_readable_id` to
`services/readable_id.py`; add `services/estimate_readable_id.py` and
`Company.next_estimate_seq`. No behavior change anywhere; nothing calls the
allocator yet. Tests: `test_readable_id.py` extended for the estimate formatter
and every normalization row in the table above (including the spaced-digit and
unpadded forms), plus a new `test_estimate_readable_id.py` mirroring
`test_task_readable_id.py` (first is `E0001`, sequential per company, companies
independent, block reservation contiguous and non-overlapping, insert retries
past an occupied ID, foreign duplicate re-raised, widening at 10,000).

**Phase 2 — generation, server ownership, and the regex switch.** Flip all five
creation sites to `insert_estimate_with_readable_id`; remove the client
override from `CreateEstimateRequest` and `CreateEstimatePayload`; switch every
regex and resolver listed above from `EST-` to `E####`; apply the miss-behavior
short-circuit; update the user-facing copy. Rewrite the ~17 injecting tests. Add
the "PUT omitting `estimate_id` preserves it" regression test, an "archive
E0042" end-to-end orchestrator test, a spaced-digit test ("archive E 0 0 4 2"),
and a test that a well-formed but non-existent `E0042` reports not-found instead
of resolving to the most recent estimate.

**Phase 3 — backfill.** Add `scripts/backfill_estimate_readable_ids.py` and
`test_backfill_estimate_readable_ids.py` (dry run writes nothing; apply
renumbers in `created_at` order; counter advances; idempotent on re-run;
companies numbered independently; clean exit with nothing to do). Update
`scripts/db/seed_db.py:338`. **Run the backfill on each environment before
Phase 4.**

**Phase 4 — the unique index.** Add the partial unique `IndexModel` to
`Estimate.Settings.indexes`. Verify boot against backfilled data first.

**Phase 5 — search, portal, docs.** `GET /estimates?search=` with the anchored
full-ID clause; wire `EstimatesPage` to it; `font-mono` styling on the ID chips;
drop `estimate_id` from the create payload type; update the phrasing reference
and the user guide. Tests: `E0042` returns exactly that estimate; a bare `42`
returns title matches only and **not** `E0042`, `E0421` or `E4200`; the
decorated forms (`e0042`, `#E0042`, `E 0 0 4 2`) all reach the same result.

---

## Risks

| Risk | Mitigation |
|---|---|
| Index build fails at boot on duplicate pre-backfill codes | Phase 4 is strictly after Phase 3; verify boot on backfilled data |
| Maple can't resolve `EST-` codes between the Phase 2 deploy and the backfill | Ship Phases 2 and 3 back-to-back; run the backfill immediately after deploy |
| Estimate resolution diverges from Task resolution (short-circuit vs fall-through) | Deliberate; justified by digits removing prose collisions. Documented in "Miss behavior" |
| A missed inline `est[-_]` regex silently drops a phrasing | The full change list is enumerated above; the Maple CRUD coverage matrix is the backstop |
| `_ESTIMATE_REF_PATTERN` missed → ID-only messages never route to the estimate agent | Called out explicitly; add an "archive E0042" end-to-end orchestrator test |
| Old `EST-` codes in generated Google Docs stop resolving | Accepted; documented above under "What this deliberately does not do" |
| A create path bypassing the helper persists `estimate_id: ""` | The unique partial index rejects the second one in a company — a loud failure |
| Two ID schemes in one app (`T4K7Q` vs `E0042`) | Accepted; rationale and the case for eventually aligning Tasks tracked as follow-up #504 |
| 9,999 estimates exhausted in one company | Widens to `E10000`; ~8 years of headroom at the heaviest plan tier |
