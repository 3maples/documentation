# Phone Onboarding — Design Spec

**Date:** 2026-09-15
**Status:** Approved design — ready for implementation planning

## Problem

The onboarding wizard was built for a laptop and is close to unusable on a
handset. Three distinct failures, which need distinct fixes:

1. **The progress indicator does not fit.** `StepIndicator` lays eight labelled
   dots with connector rules in a single centered row. At 375px the labels
   collide and the row overflows.
2. **Individual screens are too heavy.** `CompanyStep` puts sixteen fields on
   one screen — ten company details plus six default percentages. On a phone
   that is a very long scroll before the first Save.
3. **Four of the eight screens ask for something a phone cannot do.** Contacts,
   Properties, Materials and People Roles are all CSV-upload screens. Picking a
   CSV file out of a phone's file system, having produced it somewhere else
   first, is not a thing a new user will do mid-signup. They will skip — which
   for Materials and People means landing in the app with an empty catalog and
   an estimate builder that cannot build anything.

The underlying constraint: the wizard has exactly one sequence, hard-coded as
integer indices, so there is nowhere for a phone variant to live.

### Current flow (verified 2026-09-15)

- Eight UI steps held as `currentStep: number` in
  [OnboardingPage.tsx](../../../portal/src/pages/OnboardingPage.tsx) —
  0 Welcome, 1 Company, 2 Contacts, 3 Properties, 4 Materials, 5 People,
  6 Plan, 7 Completion.
- Every step hard-wires its neighbors: `onNext={() => goToStep(3)}`,
  `onBack={() => goToStep(2)}`, and so on through the whole if-chain.
- The company is created at step 1 via `POST /auth/company-onboarding`
  (`completeCompanyOnboarding`). Returning to step 1 later takes a different
  path — `updateCompany` (PUT) — so the create-then-update shape already exists
  and is already exercised.
- Resume is semantic, not positional: the server stores an `OnboardingStep`
  enum ([platform/models/company.py:28](../../../platform/models/company.py))
  and [onboarding.ts](../../../portal/src/lib/onboarding.ts) maps it to and
  from UI indices with two hand-maintained tables.
- `useIsPhone()` already exists in
  [viewport.ts](../../../portal/src/lib/viewport.ts), keyed to Tailwind's `md:`
  breakpoint (768px).
- Phones are portrait-only app-wide:
  [RotateDeviceGate](../../../portal/src/components/common/RotateDeviceGate.tsx)
  is mounted outside `<Routes>` in
  [App.tsx](../../../portal/src/App.tsx) and explicitly covers onboarding.
- Skipping plan selection is already safe — `Company.plan_lookup_key` is
  `Optional[str]` and reads fall back to `plan_free`
  ([routers/billing.py](../../../platform/routers/billing.py)).

## Decisions taken

Recorded here because several were live questions during design and the
rejected options are not obviously wrong.

| Decision | Chosen | Rejected |
|---|---|---|
| How much the phone flow skips | Contacts and Properties become information-only; Materials, People and Plan stay interactive | Skipping all five and loading defaults silently |
| Welcome screen | Removed on **both** phone and desktop | Phone-only removal |
| Default percentages | Own screen on **both** phone and desktop | Phone-only split |
| Progress indicator on phone | `Step 3 of 7` plus a thin bar | Removing it; unlabelled dots |
| Contacts + Properties on phone | Merged into one screen | Two consecutive prose screens |
| Plan card collapsing | Inside `PlanPickerGrid`, so Manage Plan benefits too | Forking a phone-only variant for onboarding |
| Phone detection | Reactive `useIsPhone()` | One-shot sample at mount |

**Why Materials and People stay interactive.** The suggested copy for this
work proposed skipping them along with Contacts and Properties, loading
standards silently. Rejected: an empty materials catalog makes the estimate
builder — the entire point of the product — unable to produce anything, and
the standard people roles carry starting wages, which is a pricing decision a
user should see rather than inherit. One tap on "Use Standard" is a small ask
next to that.

**Why the Welcome removal is not, by itself, a screen-count win.** Dropping
Welcome and adding the percentages screen is net zero. The reduction on phone
comes from merging Contacts and Properties, which is only defensible *because*
they have become information-only: two consecutive screens of prose with
nothing but a Next button are one screen.

## Design

### 1. The step model

Integer indices stop being a stable identity the moment there are two
sequences. A phone user at index 2 who resumes on a laptop would land wherever
index 2 happens to fall in the other sequence — correct today only by
coincidence.

Make the semantic step id the state, and derive the sequence from the device:

```ts
type OnboardingStepId =
  | "company" | "percentages" | "contacts" | "properties"
  | "materials" | "people" | "plan" | "complete";

const isPhone = useIsPhone();
const steps: OnboardingStepId[] = isPhone ? PHONE_STEPS : DESKTOP_STEPS;

const index = steps.indexOf(currentStep);   // derived; only the indicator reads it
const next  = steps[index + 1];             // no hard-wired numbers anywhere
```

Four things fall out of this rather than needing separate solutions:

- The progress indicator gets `Step {index + 1} of {steps.length}` for free,
  correct in both sequences without knowing which one it is in.
- Cross-device resume already stores a semantic id, so it keeps working
  unchanged.
- The `goToStep(N)` arithmetic threaded through every step's props disappears.
- A sequence swap mid-flow cannot corrupt state, because the state is an id and
  not a position. This is what makes reactive phone detection safe (§5).

**Clamping rule (new, and load-bearing).** When the current or stored step is
not present in the active sequence, clamp to the **nearest preceding step that
is**. Never forward — that would skip a screen the user never saw. Three cases
reach this:

- A desktop user stored at `properties` resuming on a phone → `contacts`.
- The `welcome` rewind hook, now that Welcome is gone → `company`, the first
  step, which is exactly what that hook was always for.
- A desktop window dragged below 768px while on `properties` → `contacts`.

The clamp is a **derived guard**, computed during render from
`steps.indexOf(currentStep)`, not a `useEffect` that corrects state afterwards.
This keeps it clear of the StrictMode re-arm trap that has bitten this codebase
twice, and means there is never a frame rendering a step the sequence does not
contain.

### 2. The two sequences

| # | Desktop (8) | Phone (7) |
|---|---|---|
| 1 | Company details | Company details |
| 2 | Default percentages | Default percentages |
| 3 | Contacts — CSV import | **Contacts & Properties — information only** |
| 4 | Properties — CSV import | Materials — Use Standard / Later |
| 5 | Materials — CSV + standard | People — Use Standard / Later |
| 6 | People — CSV + standard | Plan — collapsed cards |
| 7 | Plan | You're All Set |
| 8 | You're All Set | |

**The merged phone screen's id is `contacts`.** `properties` is simply absent
from the phone sequence. This is what makes the clamping cases in §1 resolve
the way they do, and it means a phone user who gets that far and resumes on a
laptop lands on the desktop Contacts screen — the earlier of the two, so
nothing is skipped.

**`complete` is a UI-only step id.** It is deliberately *not* added to the
server `OnboardingStep` enum: reaching it is recorded by
`onboarding_completed: true`, and a `complete` enum value would be a second
representation of the same fact that could disagree with the boolean.

Phone copy for the merged screen, keeping each resource's existing overview
prose above it:

> Since you're on your phone, I'll skip asking you to import your Contacts and
> Properties so we can get you up and running. Both are easy to add later from
> a computer — or just ask me and I'll add them one at a time.

Materials and People keep their existing skip-confirmation dialog when the user
takes "Later" with nothing selected. That warning matters more on phone than
desktop, not less, because "Later" is the path of least resistance there.

> **Revised 2026-09-16.** The phone screens dropped the dialog. Their prose now
> states up front what skipping costs and that Maple still recommends the
> items, so the modal was asking a question already answered on screen — and on
> a phone a modal is the whole screen. The laptop screens keep theirs: there the
> user was offered a file picker and a checkbox, so reaching Next with neither
> is worth one question. Skip labels became "Skip Materials" / "Skip People
> Roles".

### 3. Component changes

**New — `CompanyDefaultsStep.tsx`.** The six percentage fields lifted out of
`CompanyStep`: tax rate, overall markup, overhead allocation, materials markup,
standard unbillable, labor burden. Single column on phone, two on desktop.

Sequencing note: the company is created (POST) at step 1 and the percentages
land via PUT at step 2. `CompanyStep` already takes the PUT path whenever
`companyId` is set, so this is an existing code path reached in a new order, not
a new backend contract. The suggested starting values and the "a blank field
means the user cleared it deliberately, so 0" reading move across unchanged —
including the one field that does not follow it, `standard_unbillable_percent`,
whose `parsePercentInput` fallback is 20 rather than 0.

**`CsvUploadStep.tsx`** — add an `infoOnly` mode that drops the sample-CSV
link, the file picker and the standard-list checkbox, leaving the prose and a
Next button. The merged phone screen renders two prose blocks in this mode.

**`StepIndicator.tsx`** — take labels from the active sequence rather than a
module-level constant. Dots on desktop as today; on phone, `Step 3 of 7` plus a
thin filled bar.

**`PlanPickerGrid.tsx`** — collapse the features, supports and limits sections
behind a "See what's included" toggle below `md`, leaving tagline, name, price
and action visible. Applied inside the shared component, so the in-app Manage
Plan modal gets the same fix; it has the same problem on a phone. The `lg:`
subgrid alignment is untouched, since it only engages at ≥1024px where nothing
is collapsed.

**`CompletionStep.tsx`** — unchanged except for one phone-only line noting that
contacts, properties and the plan can all be set up from a computer whenever
they are ready.

**Deleted — `WelcomeStep.tsx`.**

### 4. Backend

Small and additive.

- `OnboardingStep` gains `PERCENTAGES = "percentages"`
  ([models/company.py](../../../platform/models/company.py)).
- [routers/auth.py](../../../platform/routers/auth.py) stores `PERCENTAGES`
  rather than `CONTACTS` immediately after company creation, and the model's
  `onboarding_step` default follows.
- `welcome` stays in the enum. Its meaning becomes "clamp to the first step,"
  which is what the rewind hook always used it for; the docstring needs
  updating to say so, since it currently describes it as "UI step 0."

**No migration.** A user mid-flight at `contacts` gave their percentages in the
old combined form, so resuming past the new Percentages screen is the correct
behavior for them, not a gap.

### 5. Phone detection

Reactive `useIsPhone()`, matching the idiom
[viewport.ts](../../../portal/src/lib/viewport.ts) exists to provide.

A one-shot sample at mount was considered and rejected. The case for it was
rotation — an iPhone in landscape is 844px and crosses the breakpoint — but
phones are portrait-only app-wide via `RotateDeviceGate`, so rotation never
reaches the wizard. That left only a local divergence from the house pattern,
bought with a case that cannot occur.

The one real trigger is a desktop browser window dragged across 768px. A user
on Properties who narrows their window clamps back to the merged Contacts
screen and presses Next once more; widening again returns them to Properties,
because the clamp is a render-time derivation and never writes back, so the
stored id survives the round trip. Better than freezing the layout at whatever
width the window happened to have at mount.

## Testing

TDD per CLAUDE.md — failing test first for each behavior below.

**New**

- `onboardingStepSequence.test.ts` — both sequences; index derivation; and each
  clamping case by name: phone-at-`properties`, the `welcome` rewind, and the
  live resize.
- `CompanyDefaultsStep.test.tsx` — prefill from an existing company, the
  cleared-field-means-zero reading, the `standard_unbillable_percent` fallback
  of 20, and PUT-on-submit.
- `StepIndicator` phone variant — `Step N of M` and the count tracking the
  active sequence rather than a constant.

**Updated**

- `onboardingResume.test.ts`, `onboardingResumeApply.test.ts` — step ids in
  place of indices.
- `CompanyStepEdit.test.tsx` — percentages no longer on this screen.
- `CsvUploadStep.test.tsx` — `infoOnly` hides picker, sample link and checkbox.
- `PlanPickerGrid.test.tsx`, `ManagePlanModal.test.tsx` — collapse behavior.
- `onboardingPlanPersistence.test.tsx` — plan persistence across the new
  sequence.
- Platform auth tests — the new post-creation default step.

Gates: `npm run typecheck` and `npm test` in `portal/`; `./run_mypy.sh` and
`./run_ruff.sh` scoped to the touched files in `platform/`. `npm run build` is
vite-only and does not type-check, so it is not a substitute for `typecheck`.

## Out of scope

- Merging Materials and People into a single phone screen with two toggles.
  Would reach six screens, but each carries a real decision and folding them
  together makes both easier to dismiss with one tap.
- Any change to CSV parsing, the upload endpoints, or the standard materials
  and roles content.
- Native file-picker or camera-based import on phone.
- The desktop screen count, which stays at eight.
