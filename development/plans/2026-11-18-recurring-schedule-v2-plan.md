# Recurring Schedule V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the work item's "N times per month" recurring setting with real-calendar patterns between two dates, a live preview, and a visit count that is correct for the calendar, on desktop and phone.

**Architecture:** `RecurrenceSchedule` gains optional fields; a schedule with `pattern` set is new-form, one without is old-form and counts exactly as today (no migration). The platform counts in a new pure module `services/recurrence.py`; the portal counts in `src/lib/recurrenceFormat.ts`. One shared cases file, byte-identical in both repos, pins dates, counts, summaries, validation and roll-forward for both.

**Tech Stack:** Platform: FastAPI, Pydantic 2, Beanie 2.0, pytest. Portal: React 18, TypeScript, Tailwind 4, Vitest + Testing Library.

**Spec:** the approved plan page "Recurring Schedule V2 Plan", https://claude.ai/artifact/NRtKkWrjx9RoZiGwpuQKRW (approved by Simon 2026-11-18; read it with the Artifact tool). Its "Design" sections are the UI spec; its storage table, counting rules and security review are binding. Cases: [`2026-11-18-recurring-schedule-v2-cases.json`](2026-11-18-recurring-schedule-v2-cases.json) (generated from the spec's reference rules, checked by a second, independent implementation).

## Global Constraints

- **Where to work:** fresh worktrees off `main` for `platform/`, `portal/`, `website/` and the workspace root (for `.claude/rules/` and `CLAUDE.md`), nested in this session's worktree. Setup per memory: copy portal `.env`, `.env.local`, `.env.development` from the main checkout; symlink `platform/.venv`.
- **No commits by the implementer.** Each task ends at a checkpoint (its scoped tests and gates pass). Simon moves the work with `/mothership` and commits with `/commit`. Never push.
- **TDD:** every task writes its failing tests first. Run only the tests named in the task (`./run_tests.sh <file>`, `npm test -- <file>`). Platform: `./run_ruff.sh` and `./run_mypy.sh` scoped to touched paths must be clean.
- **Pattern values:** `weekly`, `every_n_days`, `monthly_date`, `monthly_position`, `visit_count`.
- **Limits** (both repos, identical): `interval` weekly 1–52, every_n_days 1–365, monthly 1–12, and absent for `visit_count`; `weekdays` 1–7 distinct of 0–6 (Mon = 0); `month_days` 1–32 distinct of 1–31 and −1 (last day); `positions` 1–5 distinct of 1, 2, 3, 4, −1 (last); `position_weekday` 0–6; `visits` 1 to the number of days in the season; `max_visits` 1–1,828, not with `visit_count`; dates `YYYY-MM-DD` strings, real dates, years 2000–2100, end ≥ start, end ≤ start + 5 years (29 Feb + 5 years = 28 Feb); at least one visit.
- **Shape:** with `pattern` set, every old field (`end_type`, `start_month`, `start_year`, `end_month`, `end_year`, `total_occurrences`, `specific_months`) and every field the pattern doesn't use is absent; `frequency`/`period` keep their defaults (1, `"month"`) and are ignored. Lists are stored ascending with −1 last.
- **Old-form validation is not changed at all.** No limit on an old schedule is tightened.
- **Saved totals come from the platform's own count.** The portal's count is display only.
- **Wording people read:** "visits" (not "occurrences"/"times") in the portal, documents and the guide. API and MCP key names (`occurrences`, `total_all_occurrences`, `calculate_occurrences`) do not change. The switch stays labelled "Recurring"; the dialog title is "Recurring Schedule".
- **Summary format** (both repos, from the cases file): `<rhythm>, <season>[, up to N visits]`. Rhythm examples: `Weekly on Tue`, `Every 2 weeks on Mon and Fri`, `Every day`, `Every 10 days`, `Monthly on the 1st and 15th`, `Monthly on the 31st (or last day)` (appended when a day 29–31 is chosen and "last day" is not), `Every 2 months on the 2nd and 4th Tue`, `Monthly on the last Fri`, `3 visits`, `1 visit`. Season: `Apr 5 – Nov 20, 2027`, `Nov 1, 2027 – Mar 31, 2028`, one day `Jun 1, 2027` (spaced en dash). Old-form summaries are today's strings, unchanged.
- **Dialog error copy** (exact): `Enter the season's start and end dates.` · `The season ends before it starts.` · `A season can be at most 5 years long.` · `No visits fall inside this season.` · `A season cannot hold more visits than it has days.` · `Repeat every 1 to 52 weeks.` / `… 1 to 365 days.` / `… 1 to 12 months.` · `Enter at least 1 visit.` · `Stop after 1 to 1,828 visits.`
- **Dialog notes** (exact): over 150 visits `That is N visits. Check this is what you intend.` · cap reached `Stops after N visits on Mon D, before the season ends.` · cap not reached `The season ends first, after N visits.` · day 29–31 `In shorter months the visit falls on the last day.` · visit_count `Dates are approximate. Only the number of visits affects the price.`
- **Presets** (label → schedule; season dates kept): Weekly → weekly, 1, [weekday of start]; Every 2 weeks → weekly, 2, [weekday of start]; Twice a month → monthly_date, 1, [1, 15]; Monthly → monthly_date, 1, [day of start]; Every 10 days → every_n_days, 10. Weekday presets keep the chosen weekdays once the user has changed them.
- **Phone:** below 768 px (`md`) one column, preview under the settings; dialog `fullScreenOnMobile`; count and total in the `Modal` footer; every control ≥ 44 px tall on a phone; weekdays one row of seven, month days seven across; native date and number inputs; fields covered by the iOS focus-zoom floor in `portal/src/styles/index.css`; nothing wider than a 320 px screen except the chart, which scrolls inside its panel.

## Review Focus

1. **An old schedule nobody edits stays old.** Opening a work item with an old schedule and changing only its description must save the schedule byte-for-byte unchanged; only Save in the dialog converts it. Test in Task 8.
2. **Cancel on an old schedule.** Opening the new dialog on an old schedule and pressing Cancel leaves the old schedule and the switch as they were. Test in Task 7.
3. **Switch off, then save.** With the schedule remembered for switch-back, a save while the switch is off must send `recurring: false` and no `recurrence`. Test in Task 8.
4. **Time zones.** Visit dates must not move in a time zone far from UTC; date strings are never parsed with local-time `Date`. Verification run under `TZ=Pacific/Auckland` and `TZ=America/Los_Angeles` in Task 6.
5. **A cleared number field.** `NumericInput` emits 0 when cleared; the dialog must show the interval/visits error and disable Save, never save 0. Test in Task 7.

---

## Platform

### Task 1: Shared cases and the counting module

**Files:**
- Create: `platform/tests/fixtures/recurrence_cases.json` (byte copy of the plan's cases file)
- Create: `platform/services/recurrence.py`
- Test: `platform/tests/test_recurrence_rules.py`

**Interfaces:**
- Produces, in `services/recurrence.py` (no import of `models` at load; type hints via `TYPE_CHECKING` only — `models/estimate.py` imports this module in Task 2):
  - `iter_visits(schedule: RecurrenceSchedule) -> Iterator[date]` — new-form only, applies `max_visits`; raises `ValueError` on an old-form schedule.
  - `visit_dates(schedule) -> List[date]` — `list(iter_visits(...))`.
  - `count_visits(schedule) -> int` — consumes `iter_visits` without building a list.
  - `first_visit(schedule) -> Optional[date]` — ignores `max_visits`.
  - `summary(schedule) -> str` — both forms; old form returns exactly what `format_recurrence_summary` returns today.
  - `season_text(start: date, end: date) -> str`.

- [ ] **Step 1: Copy the cases file**

Run: `cp ../documentation/development/plans/2026-11-18-recurring-schedule-v2-cases.json tests/fixtures/recurrence_cases.json`

- [ ] **Step 2: Write the failing tests** — load the file once at module level and parametrize by case `name`.

```python
@pytest.mark.parametrize("case", CASES["valid"], ids=lambda c: c["name"])
def test_visit_dates_count_and_summary(case):
    s = RecurrenceSchedule.model_validate(case["schedule"])
    assert [d.isoformat() for d in visit_dates(s)] == case["dates"]
    assert count_visits(s) == case["count"]
    assert summary(s) == case["summary"]

@pytest.mark.parametrize("case", CASES["old"], ids=lambda c: c["name"])
def test_old_schedules_keep_todays_summary(case):
    assert summary(RecurrenceSchedule.model_validate(case["schedule"])) == case["summary"]

def test_first_visit_ignores_the_cap(): ...   # "stop after 20 visits" case → date(2027, 4, 6)
def test_iter_visits_refuses_an_old_schedule(): ...  # ValueError
```

Until Task 2 adds the fields, build the schedule with a minimal stand-in (`types.SimpleNamespace(**case["schedule"])` with absent keys as `None`); switch to `RecurrenceSchedule.model_validate` in Task 2.

- [ ] **Step 3: Run to see them fail** — `./run_tests.sh tests/test_recurrence_rules.py` → FAIL, `ModuleNotFoundError: services.recurrence`.

- [ ] **Step 4: Implement `services/recurrence.py`.** The counting rules are the spec's "Counting rules" panel; the reference is the `visitDates` function in the spec page's script. Use `date` arithmetic only (`date.toordinal()`, `calendar.monthrange`). Weekly: first visit is the first chosen weekday in the 7 days from the start; a date counts when `((monday(d) - monday(first)).days // 7) % interval == 0`. Monthly: walk months from the start's month; the cycle anchor is the first month with a matching date inside the season; day 29–31 clamps to the month's last day, duplicates in a month collapse. Visit count: `start + floor((k + 0.5) * season_days / visits)` days for `k` in `0..visits-1`.

- [ ] **Step 5: Run to see them pass** — `./run_tests.sh tests/test_recurrence_rules.py` → PASS. Then `./run_ruff.sh services/recurrence.py tests/test_recurrence_rules.py` and `./run_mypy.sh services/recurrence.py` → clean.

### Task 2: The model

**Files:**
- Modify: `platform/models/estimate.py` (`RecurrenceSchedule`, around lines 391–500)
- Test: `platform/tests/test_recurrence_model.py`, `platform/tests/test_recurrence_rules.py`, `platform/tests/test_estimate_api.py`, `platform/tests/test_template_api.py`, `platform/tests/mcp_company/test_mcp_company_setup.py`

**Interfaces:**
- Consumes: `services.recurrence.count_visits`, `first_visit` (Task 1).
- Produces: `RecurrencePattern` (str Enum, the five values); new optional fields on `RecurrenceSchedule`: `pattern: Optional[RecurrencePattern]`, `interval: Optional[int]`, `weekdays: Optional[List[int]]`, `month_days: Optional[List[int]]`, `positions: Optional[List[int]]`, `position_weekday: Optional[int]`, `visits: Optional[int]`, `start_date: Optional[str]`, `end_date: Optional[str]`, `max_visits: Optional[int]`; `end_type` becomes `Optional[RecurrenceEndType] = None`. Each new field gets a `Field(description=...)` — the MCP template tools publish this schema. `calculate_occurrences()` returns `count_visits(self)` for new-form, today's maths for old-form. Module-level constants `MAX_SEASON_YEARS = 5`, `MAX_VISITS = 1828`.

- [ ] **Step 1: Write the failing tests** in `test_recurrence_model.py` (the 31 existing tests stay as they are and must still pass):

```python
@pytest.mark.parametrize("case", CASES["invalid"], ids=lambda c: c["name"])
def test_invalid_new_schedules_are_refused(case):
    with pytest.raises(ValidationError):
        RecurrenceSchedule.model_validate(case["schedule"])

@pytest.mark.parametrize("case", CASES["normalised"], ids=lambda c: c["name"])
def test_lists_are_stored_sorted(case):
    dumped = RecurrenceSchedule.model_validate(case["schedule"]).model_dump()
    for key, value in case["stored"].items():
        assert dumped[key] == value

def test_old_schedule_without_end_type_is_refused(): ...   # {"frequency": 1} → ValidationError
def test_calculate_occurrences_counts_new_schedules(): ...  # "weekly on Tue" case → 33
def test_job_item_total_uses_the_visit_count(): ...          # JobItem(sub_total=85, recurring=True, recurrence=<weekly Tue>).effective_sub_total() == 2805
```

In `test_recurrence_rules.py`, replace the stand-in with `RecurrenceSchedule.model_validate`.

Route tests (one out-of-range schedule each, e.g. the "weekly interval 53" case): `test_estimate_api.py::test_put_refuses_an_out_of_range_schedule` → 422; `test_template_api.py::test_create_refuses_an_out_of_range_schedule` → 422; `mcp_company/test_mcp_company_setup.py::test_template_tool_refuses_an_out_of_range_schedule` → tool error. Plus `test_estimate_api.py::test_schedule_change_on_a_sent_estimate_is_refused` — same response as any other content change on a Sent estimate.

- [ ] **Step 2: Run to see them fail** — `./run_tests.sh tests/test_recurrence_model.py tests/test_recurrence_rules.py` → FAIL on the new tests.

- [ ] **Step 3: Implement.** In the existing `model_validator(mode="after")`: if `pattern is None`, require `end_type` (`ValueError("end_type is required")`) and run today's checks unchanged; otherwise apply the Global Constraints limits and shape rules, sort the lists, and require `first_visit(self) is not None`. Parse dates with `date.fromisoformat` after checking `^\d{4}-\d{2}-\d{2}$`. Keep validation free of `count_visits` (the model is validated on every estimate read).

- [ ] **Step 4: Run to see them pass** — `./run_tests.sh tests/test_recurrence_model.py tests/test_recurrence_rules.py tests/test_estimate_api.py tests/test_template_api.py tests/mcp_company/test_mcp_company_setup.py` → PASS. Ruff and mypy on `models/estimate.py` → clean.

### Task 3: Everything that reads a schedule

**Files:**
- Modify: `platform/services/estimate_doc_generator.py:24-53` (remove `format_recurrence_summary`; `_work_item_display` uses `services.recurrence.summary`)
- Modify: `platform/services/document_templates/sample_estimate.py:44`
- Modify: `platform/mcp_server/company/tools_setup.py:149` (`Recurrence` description)
- Test: `platform/tests/test_estimate_doc_generator.py`, `platform/tests/test_maple_metrics.py`, `platform/tests/mcp_company/test_mcp_company_estimates.py`

**Interfaces:**
- Consumes: `services.recurrence.summary` (Task 1), `RecurrenceSchedule` new form (Task 2).
- Produces: nothing new. Both document paths (`work_item_rows` and the document-template context's `_work_items_and_tax`) go through `_work_item_display`, so one change covers both.

- [ ] **Step 1: Write the failing tests**

```python
# test_estimate_doc_generator.py
def test_new_schedule_reads_as_visits_on_the_document():
    desc, amount = _work_item_display(JobItem(description="Mowing", sub_total=85, recurring=True, recurrence=WEEKLY_TUE))
    assert desc == "Mowing (Weekly on Tue, Apr 5 – Nov 20, 2027)"
    assert amount == 2805

# test_maple_metrics.py
def test_occurrences_counts_a_stored_new_schedule():
    assert _occurrences({"recurring": True, "recurrence": WEEKLY_TUE.model_dump()}) == 33

# test_mcp_company_estimates.py
def test_get_estimate_counts_a_new_schedule(): ...   # occurrences == 33, total_all_occurrences == round(85 * 33, 2)
```

Existing doc-generator tests that import `format_recurrence_summary` switch to `services.recurrence.summary`; their expected strings do not change.

- [ ] **Step 2: Run to see them fail** — the three files → FAIL on the new tests.

- [ ] **Step 3: Implement.** Sample row text becomes `Seasonal maintenance (Every 2 weeks on Wed, May 6 – Sep 30, 2026)`; amounts stay. `Recurrence` description: `Schedule for a recurring template: pattern, interval, the days that pattern uses, start_date and end_date (YYYY-MM-DD), optional max_visits.`

- [ ] **Step 4: Run to see them pass**, plus `./run_tests.sh tests/document_templates` (sample and composer). Ruff and mypy on touched files → clean.

### Task 4: Templates move their season forward

**Files:**
- Modify: `platform/services/recurrence.py` (add `roll_season_forward`)
- Modify: `platform/data/default_templates.json:24-39`
- Modify: `platform/services/template_bootstrap.py:88-118`
- Modify: `platform/agents/estimate/crud_handlers.py:831-852` (`_build_job_item_from_template`)
- Test: `platform/tests/test_recurrence_rules.py`, `platform/tests/test_template_bootstrap.py`, the template-estimate tests (`grep -l _build_job_item_from_template tests`)

**Interfaces:**
- Produces: `roll_season_forward(schedule: RecurrenceSchedule, today: date) -> RecurrenceSchedule` in `services/recurrence.py`. Old form → returned unchanged. New form: while `end_date < today`, add one year to both dates (29 Feb → 28 Feb); if no year was added, or the moved season would hold no visits, or a year passes 2100, or the result fails validation, return the input unchanged. Builds the result with `type(schedule).model_validate({**schedule.model_dump(), "start_date": …, "end_date": …})`, catching `ValidationError` — no model import at load.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("case", CASES["roll"], ids=lambda c: c["name"])
def test_roll_season_forward(case):
    s = roll_season_forward(RecurrenceSchedule.model_validate(case["schedule"]), date.fromisoformat(case["today"]))
    assert (s.start_date, s.end_date) == (case["expected"]["start_date"], case["expected"]["end_date"])

def test_roll_leaves_an_old_schedule_alone(): ...
# test_template_bootstrap.py
def test_seeded_mow_template_has_a_new_form_schedule(): ...   # weekly, [0], 2026-04-06..2026-11-28 in the JSON
def test_bootstrap_moves_a_past_season_forward(): ...         # freeze today to 2027-01-10 → 2027-04-06..2027-11-28
# template-estimate tests
def test_using_a_template_moves_its_past_season_forward(): ...
```

The existing `test_anchor_recurrence_to_now_*` tests keep passing for old-form schedules.

- [ ] **Step 2: Run to see them fail.**

- [ ] **Step 3: Implement.** Seed schedule: `{"pattern": "weekly", "interval": 1, "weekdays": [0], "start_date": "2026-04-06", "end_date": "2026-11-28"}` (34 visits, as the old seed). `_anchor_recurrence_to_now` keeps its month logic for old form and calls `roll_season_forward(schedule, datetime.now(timezone.utc).date())` for new form. `_build_job_item_from_template` passes `template.recurrence` through `roll_season_forward` with the same UTC date (one builder serves "use template" and a new estimate from a template).

- [ ] **Step 4: Run to see them pass.** Ruff and mypy on touched files → clean.

### Task 5: Stored-schedule check script

**Files:**
- Create: `platform/scripts/recurrence_schedule_check.py`
- Test: `platform/tests/test_recurrence_schedule_check.py`

**Interfaces:**
- Produces: `async def schedule_report(estimates: Any, templates: Any) -> Dict[str, Any]` returning `{"estimates_checked", "templates_checked", "invalid": [{"collection", "id", "error"}], "max_frequency", "max_total_occurrences", "max_year_span"}`. Read-only; opens its own client and never calls `init_db`, following `scripts/audit_retention_check.py`. Prints the report; exit code 1 when `invalid` is non-empty.

- [ ] **Step 1: Write the failing test** — insert into the local test Mongo one estimate with a valid old schedule, one with `{"frequency": 2}` (no end_type), one template with a new-form schedule; assert counts, that exactly the broken one is listed, and the maxima. Clean up the inserted documents.
- [ ] **Step 2: Run to see it fail.**
- [ ] **Step 3: Implement** with `$unwind`-free iteration over `job_items` in Python (projection `{"job_items.recurring": 1, "job_items.recurrence": 1}`).
- [ ] **Step 4: Run to see it pass.** Ruff and mypy → clean.

---

## Portal

### Task 6: Types and counting

**Files:**
- Modify: `portal/src/types/api.ts:328-341`
- Modify: `portal/src/lib/recurrenceFormat.ts` (rewrite)
- Create: `portal/tests/fixtures/recurrence_cases.json` (byte copy)
- Test: `portal/tests/recurrenceFormat.test.ts`, `portal/tests/workItemV2.test.ts`, `portal/tests/divisionResolve.test.ts`

**Interfaces:**
- Produces in `api.ts`: `RecurrencePattern` union; `RecurrenceSchedule` with every old field optional (`frequency?`, `period?`, `end_type?` …) plus the new fields, dates as `string`.
- Produces in `recurrenceFormat.ts` (all date maths on UTC day numbers; never `new Date("YYYY-MM-DD")` in local time):
  - `isNewSchedule(r: RecurrenceSchedule): boolean`
  - `visitDates(r: RecurrenceSchedule): string[]` (ISO dates, `max_visits` applied)
  - `calculateOccurrences(r: RecurrenceSchedule): number` (both forms; old form unchanged)
  - `formatRecurrenceSummary(r): string` (cases `summary`; old form unchanged)
  - `formatRecurrenceShort(r): string` (cases `short`; old form → `"N time(s) per month"`)
  - `formatSeason(r): string` (new form only; `""` for old)
  - `validateSchedule(r): string | null` (the Global Constraints error copy, checked in that order)
  - `PRESETS: ReadonlyArray<{ id: PresetId; label: string }>`, `applyPreset(id: PresetId, r: RecurrenceSchedule, weekdaysTouched: boolean): RecurrenceSchedule`, `activePreset(r): PresetId | null`
  - `seasonFromOldSchedule(r: RecurrenceSchedule): RecurrenceSchedule`
  - `rollSeasonForward(r: RecurrenceSchedule, today: string): RecurrenceSchedule` (same rules as Task 4)
  - `todayIso(): string` (the user's local date)

- [ ] **Step 1: Copy the cases file** and **write the failing tests**: one `describe.each` per cases section (`valid` → dates, count, short, summary; `invalid` → `validateSchedule` not null; `old` → count and summary; `roll` → dates), plus:

```ts
test("an old date range opens as the 1st of its first month to the last day of its last", () => {
  expect(seasonFromOldSchedule(OLD_RANGE_05_09_2026)).toMatchObject({ pattern: "weekly", interval: 1, start_date: "2026-05-01", end_date: "2026-09-30", weekdays: [4] });
});
test("old total occurrences opens as 12 months with stop after", () => {
  expect(seasonFromOldSchedule(OLD_TOTAL_34_FROM_05_2026)).toMatchObject({ start_date: "2026-05-01", end_date: "2027-04-30", max_visits: 34 });
});
test("old specific months open as first to last chosen month of the start year", () => {
  expect(seasonFromOldSchedule(OLD_SPECIFIC_APR_JUN_2026_2027)).toMatchObject({ start_date: "2026-04-01", end_date: "2026-06-30" });
});
test("an old range longer than 5 years is cut to 5", ...);           // end_date = start + 5 years
test("Weekly preset takes the start date's weekday", ...);           // start 2027-04-07 → weekdays [2]
test("weekday presets keep weekdays the user chose", ...);
```

`workItemV2.test.ts` and `divisionResolve.test.ts`: one test each that a work item with the "weekly on Tue" schedule and an $85 total gives $2,805.

- [ ] **Step 2: Run to see them fail** — `npm test -- tests/recurrenceFormat.test.ts tests/workItemV2.test.ts tests/divisionResolve.test.ts`.
- [ ] **Step 3: Implement** to the same rules as Task 1 (the spec page's script is the reference). `seasonFromOldSchedule` gives weekly, interval 1, weekdays `[weekday of start_date]`.
- [ ] **Step 4: Run to see them pass**, then the time-zone check: `TZ=Pacific/Auckland npm test -- tests/recurrenceFormat.test.ts` and `TZ=America/Los_Angeles npm test -- tests/recurrenceFormat.test.ts` → PASS. `npx tsc --noEmit` and `npm run lint` → clean (old-form callers now read optional fields).

### Task 7: The schedule dialog

**Files:**
- Modify: `portal/src/components/estimates/RecurrenceDialog.tsx` (rewrite)
- Create: `portal/src/components/estimates/RecurrencePreview.tsx`
- Test: `portal/tests/RecurrenceDialog.test.tsx` (rewrite)

**Interfaces:**
- Consumes: everything Task 6 produces.
- Produces: `RecurrenceDialog` props `{ open: boolean; onClose: () => void; onSave: (schedule: RecurrenceSchedule) => void; initialData?: RecurrenceSchedule; pricePerVisit: number }`. `RecurrencePreview` props `{ schedule: RecurrenceSchedule; pricePerVisit: number }` — summary, count, first/last (`Around … to …` for visit_count), notes, visits-per-month bars (one per month of the season, `overflow-x-auto`), price per visit, "Total for all visits".

Layout per the spec's "Design: the schedule dialog" and "Design: on a phone": shared `Modal`, `maxWidth="max-w-3xl"`, `fullScreenOnMobile`, body `grid md:grid-cols-[1.25fr_1fr]`; footer shows `N visits · $X` (or the error) left, Cancel / Save right, and on a phone stacks the line over two equal buttons. Chips reuse today's pill classes (`px-3 py-1.5 text-sm rounded-full border`), pressed = `bg-brand text-white`, `aria-pressed`; on a phone `min-h-11`. Weekday chips: `grid grid-cols-7` on a phone. Month-day squares: `grid grid-cols-7`, "Last" spans 4. Number fields: `NumericInput` with `inputMode="numeric"`. Dates: `<input type="date">` bound to the ISO string. "Stop after" is a checkbox plus number, hidden for visit_count. Toggling off the last selected chip in a list is ignored.

- [ ] **Step 1: Write the failing tests**

```ts
test("Weekly preset, then Save, saves weekly on the start date's weekday", ...);   // onSave called with { pattern: "weekly", interval: 1, weekdays: [...], start_date, end_date }
test("the preview shows 33 visits and $2,805.00 for weekly Tue, Apr 5 – Nov 20, 2027 at $85", ...);
test("only the chosen pattern's controls are shown", ...);   // choose "Monthly, on a weekday" → position chips visible, weekday chips absent
test("Save is disabled with the reason when the season ends before it starts", ...);
test("a cleared interval disables Save with 'Repeat every 1 to 52 weeks.'", ...);   // Review Focus 5
test("an old schedule opens converted, with a line showing the old wording and count", ...);   // "Was: 1 time per month, from 05/2026 until 09/2026 · 5 visits"
test("Cancel on an old schedule calls onClose and never onSave", ...);              // Review Focus 2
test("stop after 20 says the cap comes first", ...);                              // "Stops after 20 visits on Aug 17, before the season ends."
test("over 150 visits shows the check note but still allows Save", ...);          // every day, Apr 5 – Nov 20, 2027 → "That is 230 visits. Check this is what you intend."
test("the 31st shows the shorter-months note", ...);
test("on a phone the count and total are in the footer", ...);                      // matchMedia mocked to the phone query, as in WorkItemsMobileColumns.test.tsx
```

- [ ] **Step 2: Run to see them fail** — `npm test -- tests/RecurrenceDialog.test.tsx`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run to see them pass**; `npm run lint` → clean.

### Task 8: Around the dialog

**Files:**
- Modify: `portal/src/components/estimates/WorkItemInlineContent.tsx:72-74, 150-167, 348-400, 533-545`
- Modify: `portal/src/components/estimates/WorkItemTotalsTicket.tsx:440-475`
- Modify: `portal/src/pages/NewEstimateWithActivityPage.tsx:1678-1745`
- Test: `portal/tests/WorkItemInlineContent.test.tsx`, `portal/tests/WorkItemBreakdownTooltips.test.tsx` (or the ticket's own test), `portal/tests/WorkItemsMobileColumns.test.tsx`, `portal/tests/NewEstimateWithActivityPage.workItemSave.test.tsx`

**Interfaces:**
- Consumes: `formatRecurrenceShort`, `formatSeason`, `calculateOccurrences` (Task 6); `RecurrenceDialog` with `pricePerVisit={breakdown.total}` (Task 7).

Editor: the Division/Recurring row keeps its shape; the blue text link is replaced by a strip under it (spec "Work item editor"): rhythm (`formatRecurrenceShort`) over season (`formatSeason`), a `N visits` pill, an Edit button; on a phone the strip stacks (rhythm and season, then pill and a full-height Edit). Switching off keeps `recurrence` in state; switching on with a kept schedule restores it without opening the dialog; switching on with none opens the dialog. The `onChange` payload sends `recurrence: recurring ? recurrence : undefined`. Totals ticket: "Work Item Total" gains a muted `per visit` label when recurring; rows become `Visits` → `N` and `Total for all visits`. List: the desktop Recurring cell shows short form over `N visits` (blue `Yes` pill and `No` replaced; one-time stays `No`); on a phone, a recurring item shows a blue pill `<short> · N visits` under its description (the column stays dropped).

- [ ] **Step 1: Write the failing tests**

```ts
test("an untouched old schedule saves unchanged", ...);          // Review Focus 1: edit description only → onChange payload recurrence deep-equals the initial old schedule
test("switching off sends no schedule; switching back on restores it", ...);   // Review Focus 3
test("the strip shows Weekly on Tue, Apr 5 – Nov 20, 2027 and 33 visits", ...);
test("the totals ticket reads Visits 33 and Total for all visits $2,805.00", ...);
test("the list shows the rhythm and count instead of Yes", ...);
test("on a phone a recurring item shows its schedule under the description", ...);   // WorkItemsMobileColumns.test.tsx; a one-time item shows nothing extra
```

Existing tests asserting `Number of Occurrences`, `times`, `Work Item Total with Recurring Dates` or the `Yes` pill are updated to the new copy.

- [ ] **Step 2: Run to see them fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run to see them pass** (the four files plus `tests/WorkItemDialog.test.tsx` and `tests/TemplateDialog.test.tsx`, which share the editor); `npm run lint` → clean.

### Task 9: Applying a template moves its season

**Files:**
- Modify: `portal/src/lib/templates.ts` (add `templateToEstimateWorkItem`)
- Modify: `portal/src/pages/NewEstimateWithActivityPage.tsx:1246`
- Test: `portal/tests/templates.test.ts`

**Interfaces:**
- Produces: `templateToEstimateWorkItem(template: Template, today: string): WorkItemV2` = `templateToWorkItem` with `recurrence` passed through `rollSeasonForward(…, today)`. `TemplatesTab` keeps `templateToWorkItem` (editing a template never moves its dates); the estimate page calls the new function with `todayIso()`.

- [ ] **Step 1: Write the failing tests** — a template with the seeded schedule and `today = "2027-01-10"` gives `2027-04-06`..`2027-11-28`; `templateToWorkItem` on the same template leaves the 2026 dates.
- [ ] **Step 2: Run to see them fail** — `npm test -- tests/templates.test.ts`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run to see them pass**; `npm run lint` → clean.

---

## Docs

### Task 10: User guide, FAQ and rules

**Files:**
- Modify: `platform/user_guides/users_guide.md` — §7.2 "Recurring work items" (~line 1024), §7.2 Templates paragraph (~line 968), the estimate steps "Set up Recurring" (~line 1259) and totals explanation (~line 1296), Glossary "Recurrence" (~line 1806), the Documents passages in §7.2 and §9.8
- Modify: `website/src/content/faqs.json` (`recurring-work-items`)
- Create: `.claude/rules/recurrence.md` (workspace root, with `paths:` globs for `platform/services/recurrence.py`, `platform/models/estimate.py`, `portal/src/lib/recurrenceFormat.ts`, `portal/src/components/estimates/Recurrence*.tsx`)
- Modify: `CLAUDE.md` (rules table row)
- Test: `platform/tests/test_maple_help_coverage.py`, `platform/tests/test_public_maple_api.py`

The §7.2 rewrite covers: the presets; the five ways to repeat; the season's start and end dates (can cross the new year, at most 5 years); "Stop after"; the preview (count, first and last visit, visits per month, price per visit, total); that the work item total is the price per visit, multiplied by the visits; that a schedule made before this change keeps its count until it is edited, and editing it shows the old wording and count before Save; how it looks on a phone. Templates: a template's season moves to the current year when the template is used. Glossary: "Recurrence — a schedule that makes a work item repeat between two dates: weekly on chosen days, every few days, monthly on dates or on a weekday, or a set number of visits." Leave unchanged (still true): the "Recurring schedules" line in what Maple doesn't do, and the metrics line "every scheduled visit". FAQ: "…choose how it repeats (weekly, every few weeks, monthly, or a set number of visits) and the season it runs in. The total is the price per visit times the number of visits." The rule file records the shape, the limits, the counting rules, the shared cases file and that both copies must stay byte-identical.

- [ ] **Step 1: Make the edits.** `grep -n -i "occurrence\|times per month\|number of months" platform/user_guides/users_guide.md` → no passage that describes the old dialog remains (the Pricing "Each — flat fee per occurrence" line is unrelated and stays).
- [ ] **Step 2: Run** `./run_tests.sh tests/test_maple_help_coverage.py tests/test_public_maple_api.py` → PASS.
- [ ] **Step 3: Check the copies match:** `cmp platform/tests/fixtures/recurrence_cases.json portal/tests/fixtures/recurrence_cases.json` → no output.

---

## After the tasks (Simon's steps, listed so nothing is missed)

1. `/code-review` on the branch; `/fix-issues` as chosen.
2. Manual check on Dev at phone size and on a real iPhone and Android phone: nothing wider than the screen, controls ≥ 44 px, count visible while editing. Ask Maple "how do I make a work item repeat every 2 weeks?" and compare with the dialog.
3. Run `python scripts/recurrence_schedule_check.py` against Dev and prod; release only if `invalid` is empty. Its maxima decide whether the follow-up limits on old schedules are safe.
4. `/mothership`, `/commit`, push, then `/release app` (platform and portal together: the old platform refuses a new-form schedule and the old portal cannot total one).
