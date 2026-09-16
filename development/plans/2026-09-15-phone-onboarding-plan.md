# Phone Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the onboarding wizard usable on a phone by replacing its hard-coded integer step indices with a device-derived sequence of semantic step ids, splitting the overloaded Company screen, and turning the two unusable CSV-import screens into a single information screen.

**Architecture:** `OnboardingPage` stops holding `currentStep: number` and holds an `OnboardingStepId` instead. A new pure module, `src/lib/onboardingSteps.ts`, owns the two sequences (phone: 7 steps, desktop: 8), the label table, the clamping rule for ids absent from the active sequence, and the id ↔ server-enum mapping. Every navigation is `steps[index ± 1]`, so no component knows a step number. The backend change is a single additive enum value.

**Tech Stack:** React 18 + TypeScript + Vite + Tailwind 4; vitest + @testing-library/react (portal). FastAPI + Beanie + pytest (platform).

**Spec:** [2026-09-15-phone-onboarding-design.md](2026-09-15-phone-onboarding-design.md)

## Global Constraints

- **TDD is mandatory** (CLAUDE.md). Failing test first, then implementation. Every task below is ordered that way; do not reorder.
- **US spellings** in all code, comments, copy and test names — `labor`, `behavior`, `color`. Note that the *existing* `CompanyStepEdit.test.tsx` contains "honouring"; leave it, do not mass-rename.
- **Commits need explicit user approval each time** (CLAUDE.md). The `git commit` steps below say what to commit; ask before running them. Never chain a commit off a prior approval.
- Commit message format: `<type>: <description>` where type ∈ `feat|fix|refactor|docs|test|chore|perf|ci`. End every commit message with:
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- **Portal gates:** `npm run typecheck` (tsc) and `npm test` (vitest). `npm run build` is vite-only and does **not** type-check — it is not a substitute.
- **Platform gates:** `./run_mypy.sh <path>` and `./run_ruff.sh <path>` scoped to touched files. Project sits at zero errors for both; fix new ones in the same task.
- **Do not run the full test suite automatically** (CLAUDE.md). Run only the test files named in each task.
- `PHONE_BREAKPOINT_PX` is **768** (Tailwind `md`). Any new phone styling must use `md:` classes so it turns over at the same width `useIsPhone()` does.
- Phones are portrait-only app-wide via `RotateDeviceGate`; do not add orientation handling.
- **Five separate git repos.** `portal/`, `platform/` and `documentation/` are each their own repo. Commit in the repo you changed; never try to stage across them.

### Correction to the spec

Spec §5 states that after a window-widening the user "leaves them on Contacts, since it is the id that moved." That is wrong for the design this plan implements. Clamping is applied as a **render-time derivation** and does not write back to state, so the stored id survives a narrow/widen round trip and the user returns to Properties. This is strictly better. Spec §5 should be amended to say so; Task 10 does it.

---

### Task 1: Backend — add the `percentages` onboarding step

**Files:**
- Modify: `platform/models/company.py:28-48` (the `OnboardingStep` enum and its docstring), and the `onboarding_step` field default at `platform/models/company.py:151`
- Modify: `platform/routers/auth.py:1121`
- Test: `platform/tests/test_onboarding_resume.py` (exists — append to it; do not create a new file)

**Interfaces:**
- Consumes: nothing.
- Produces: the string value `"percentages"` as a valid `OnboardingStep`, accepted by `PATCH /auth/onboarding-progress` and written by `POST /auth/company-onboarding`. Portal Task 3 depends on this value being accepted.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_onboarding_resume.py`:

```python
def test_percentages_is_a_valid_onboarding_step():
    """The wizard's second screen (default percentages) must be resumable."""
    from models.company import OnboardingStep

    assert OnboardingStep("percentages") is OnboardingStep.PERCENTAGES
    assert OnboardingStep.PERCENTAGES.value == "percentages"


def test_company_defaults_to_the_percentages_step():
    """A company created mid-signup resumes at the first step AFTER creation,
    which is now Percentages rather than Contacts."""
    from models.company import Company, OnboardingStep

    company = Company(name="Acme", company_id="acme")
    assert company.onboarding_step is OnboardingStep.PERCENTAGES
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd platform && ./run_tests.sh tests/test_onboarding_resume.py -v
```

Expected: FAIL — `ValueError: 'percentages' is not a valid OnboardingStep`.

- [ ] **Step 3: Add the enum value and update the docstring**

In `platform/models/company.py`, inside `class OnboardingStep`, add `PERCENTAGES` between `WELCOME` and `CONTACTS`:

```python
    WELCOME = "welcome"            # rewind hook — clamps to the first step, never written
    PERCENTAGES = "percentages"    # default company percentages
    CONTACTS = "contacts"
    PROPERTIES = "properties"
    MATERIALS = "materials"
    PEOPLE = "people"
    PLAN = "plan"
```

Replace the trailing two sentences of the class docstring (the ones describing `WELCOME` as "UI step 0" and referring to `uiIndexToOnboardingStep`) with:

```
    Forward progress begins at PERCENTAGES — the first step after the company is
    created, and so the earliest step the portal ever writes: the Company screen
    has no company to store progress on. WELCOME is the exception and only ever
    moves backwards. Set it by hand to rewind a test account; the portal clamps
    it to the first step of whatever sequence is active and never persists it.

    There is deliberately no COMPLETE member: finishing is recorded by
    `onboarding_completed`, and a second representation of the same fact could
    disagree with the boolean. See `SERVER_PERSISTED_STEPS` in
    portal/src/lib/onboardingSteps.ts.
```

Then change the field default at line 151:

```python
    onboarding_step: OnboardingStep = OnboardingStep.PERCENTAGES
```

- [ ] **Step 4: Update the company-creation endpoint**

In `platform/routers/auth.py`, at line 1121, change the assignment and the comment two lines above it:

```python
    # Mark onboarding as in-progress so an interrupted signup resumes at the
    # first post-company step instead of being dropped into the app half-set-up.
    company.onboarding_completed = False
    company.onboarding_step = OnboardingStep.PERCENTAGES
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd platform && ./run_tests.sh tests/test_onboarding_resume.py -v
```

Expected: PASS. Any pre-existing test in that file asserting the old
`OnboardingStep.CONTACTS` default must be updated to `PERCENTAGES` in this same
step — that is the behavior change, not a broken test.

- [ ] **Step 6: Run the gates**

```bash
cd platform && ./run_mypy.sh models/company.py routers/auth.py && ./run_ruff.sh models/company.py routers/auth.py
```

Expected: zero errors from both.

- [ ] **Step 7: Commit (ask first)**

```bash
cd platform && git add models/company.py routers/auth.py tests/test_onboarding_resume.py
git commit -m "feat: add percentages onboarding step

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: The step-sequence module

**Files:**
- Create: `portal/src/lib/onboardingSteps.ts`
- Test: `portal/tests/onboardingStepSequence.test.ts`

**Interfaces:**
- Consumes: nothing (pure module, no React, no imports from the app).
- Produces — every later portal task imports from here:
  - `type OnboardingStepId = "company" | "percentages" | "contacts" | "properties" | "materials" | "people" | "plan" | "complete"`
  - `DESKTOP_STEPS: readonly OnboardingStepId[]` (8 entries, canonical order)
  - `PHONE_STEPS: readonly OnboardingStepId[]` (7 entries, no `properties`)
  - `SERVER_PERSISTED_STEPS: readonly OnboardingStepId[]` (6 entries)
  - `stepsForViewport(isPhone: boolean): readonly OnboardingStepId[]`
  - `stepLabel(step: OnboardingStepId): string`
  - `clampToSequence(step: OnboardingStepId, steps: readonly OnboardingStepId[]): OnboardingStepId`
  - `serverStepToId(step: string | null | undefined): OnboardingStepId`
  - `idToServerStep(step: OnboardingStepId): string | null`
  - `parseStoredStepId(raw: string | null): OnboardingStepId | null`

- [ ] **Step 1: Write the failing test**

Create `portal/tests/onboardingStepSequence.test.ts`:

```ts
/**
 * The onboarding wizard has two sequences — 8 steps on a laptop, 7 on a phone
 * (Contacts and Properties merge into one information screen). Integer indices
 * cannot identify a step across both, so the wizard's state is a semantic id
 * and the index is derived. This module owns that mapping.
 */
import { describe, test, expect } from "vitest";
import {
  DESKTOP_STEPS,
  PHONE_STEPS,
  SERVER_PERSISTED_STEPS,
  stepsForViewport,
  stepLabel,
  clampToSequence,
  serverStepToId,
  idToServerStep,
  parseStoredStepId,
} from "../src/lib/onboardingSteps";

describe("the two sequences", () => {
  test("desktop keeps all eight screens in order", () => {
    expect(DESKTOP_STEPS).toEqual([
      "company", "percentages", "contacts", "properties",
      "materials", "people", "plan", "complete",
    ]);
  });

  test("phone drops Properties, which merges into the Contacts screen", () => {
    expect(PHONE_STEPS).toEqual([
      "company", "percentages", "contacts",
      "materials", "people", "plan", "complete",
    ]);
    expect(PHONE_STEPS).not.toContain("properties");
  });

  test("phone is a subsequence of desktop, so desktop is the canonical order", () => {
    const desktopOrder = PHONE_STEPS.map((s) => DESKTOP_STEPS.indexOf(s));
    expect(desktopOrder).toEqual([...desktopOrder].sort((a, b) => a - b));
    expect(desktopOrder).not.toContain(-1);
  });

  test("stepsForViewport picks by viewport", () => {
    expect(stepsForViewport(true)).toBe(PHONE_STEPS);
    expect(stepsForViewport(false)).toBe(DESKTOP_STEPS);
  });

  test("every step has a label", () => {
    for (const step of DESKTOP_STEPS) {
      expect(stepLabel(step)).toBeTruthy();
    }
    expect(stepLabel("percentages")).toBe("Defaults");
  });
});

describe("clampToSequence", () => {
  test("leaves a step the sequence contains alone", () => {
    expect(clampToSequence("materials", PHONE_STEPS)).toBe("materials");
    expect(clampToSequence("properties", DESKTOP_STEPS)).toBe("properties");
  });

  test("clamps a desktop-only step back to the merged phone screen", () => {
    // A desktop user stored at Properties who reopens on a phone must land on
    // Contacts — the screen that absorbed Properties — not skip past it.
    expect(clampToSequence("properties", PHONE_STEPS)).toBe("contacts");
  });

  test("never clamps forward", () => {
    // Every clamp result must sit at or before the requested step in the
    // canonical order; moving forward would skip a screen never seen.
    for (const step of DESKTOP_STEPS) {
      const landed = clampToSequence(step, PHONE_STEPS);
      expect(DESKTOP_STEPS.indexOf(landed)).toBeLessThanOrEqual(
        DESKTOP_STEPS.indexOf(step),
      );
    }
  });

  test("falls back to the first step when nothing precedes", () => {
    expect(clampToSequence("company", PHONE_STEPS)).toBe("company");
  });
});

describe("serverStepToId", () => {
  test("passes through the steps the server persists", () => {
    for (const step of SERVER_PERSISTED_STEPS) {
      expect(serverStepToId(step)).toBe(step);
    }
  });

  test("resolves the welcome rewind hook to the first step", () => {
    expect(serverStepToId("welcome")).toBe("company");
  });

  test("falls back to the first post-company step for unknown or empty values", () => {
    expect(serverStepToId("bogus")).toBe("percentages");
    expect(serverStepToId(null)).toBe("percentages");
    expect(serverStepToId(undefined)).toBe("percentages");
    // `complete` is not a server step — finishing is recorded by the
    // onboarding_completed boolean, so it must not round-trip as one.
    expect(serverStepToId("complete")).toBe("percentages");
  });
});

describe("idToServerStep", () => {
  test("returns the id for steps the portal persists", () => {
    expect(idToServerStep("percentages")).toBe("percentages");
    expect(idToServerStep("plan")).toBe("plan");
  });

  test("returns null for steps with nothing to PATCH", () => {
    // Company: the company row does not exist yet. Complete: recorded by the
    // onboarding_completed flag instead.
    expect(idToServerStep("company")).toBeNull();
    expect(idToServerStep("complete")).toBeNull();
  });
});

describe("parseStoredStepId", () => {
  test("accepts a known id", () => {
    expect(parseStoredStepId("materials")).toBe("materials");
  });

  test("discards a legacy numeric index left by the old wizard", () => {
    // The old wizard stored an integer under the same localStorage key. An
    // index cannot be reinterpreted as an id, so it is dropped and the
    // server-provided resume step wins.
    expect(parseStoredStepId("4")).toBeNull();
    expect(parseStoredStepId("0")).toBeNull();
  });

  test("discards junk and absent values", () => {
    expect(parseStoredStepId("bogus")).toBeNull();
    expect(parseStoredStepId(null)).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- onboardingStepSequence
```

Expected: FAIL — cannot resolve `../src/lib/onboardingSteps`.

- [ ] **Step 3: Write the implementation**

Create `portal/src/lib/onboardingSteps.ts`:

```ts
/**
 * The onboarding wizard's step model.
 *
 * The wizard has two sequences — eight screens on a laptop, seven on a phone,
 * where Contacts and Properties merge into a single information screen. An
 * integer index cannot identify a step across both (index 3 is Properties on
 * one and Materials on the other), so the wizard's state is a semantic id and
 * the index is derived from whichever sequence is active.
 *
 * That also makes a live sequence swap safe: a browser window dragged across
 * the 768px breakpoint recomputes the index, and `clampToSequence` handles the
 * one id that exists on only one side.
 *
 * DESKTOP_STEPS is the canonical order — it is a superset of PHONE_STEPS, and
 * everything that needs to compare two steps orders them by it.
 */

export type OnboardingStepId =
  | "company"
  | "percentages"
  | "contacts"
  | "properties"
  | "materials"
  | "people"
  | "plan"
  | "complete";

export const DESKTOP_STEPS: readonly OnboardingStepId[] = [
  "company",
  "percentages",
  "contacts",
  "properties",
  "materials",
  "people",
  "plan",
  "complete",
] as const;

/**
 * `properties` is absent, not reordered: on a phone both import screens become
 * prose, and two consecutive screens of prose with nothing but a Next button
 * are one screen. The merged screen keeps the id `contacts` — the earlier of
 * the two — so a phone user resuming on a laptop lands before the split rather
 * than past it.
 */
export const PHONE_STEPS: readonly OnboardingStepId[] = [
  "company",
  "percentages",
  "contacts",
  "materials",
  "people",
  "plan",
  "complete",
] as const;

/**
 * The steps the portal persists server-side, mirroring the backend
 * `OnboardingStep` enum minus two deliberate absences.
 *
 * `company` is absent because a user on that screen has no company row to
 * PATCH. `complete` is absent because finishing is recorded by
 * `onboarding_completed`, and a second representation of the same fact could
 * disagree with the boolean. `welcome` is read-only — see `serverStepToId`.
 */
export const SERVER_PERSISTED_STEPS: readonly OnboardingStepId[] = [
  "percentages",
  "contacts",
  "properties",
  "materials",
  "people",
  "plan",
] as const;

/** Where resume lands when the stored value is missing or unrecognized. */
const DEFAULT_RESUME_STEP: OnboardingStepId = "percentages";

const STEP_LABELS: Record<OnboardingStepId, string> = {
  company: "Company",
  percentages: "Defaults",
  contacts: "Contacts",
  properties: "Properties",
  materials: "Materials",
  people: "People",
  plan: "Plan",
  complete: "Complete",
};

export function stepsForViewport(isPhone: boolean): readonly OnboardingStepId[] {
  return isPhone ? PHONE_STEPS : DESKTOP_STEPS;
}

export function stepLabel(step: OnboardingStepId): string {
  return STEP_LABELS[step];
}

/**
 * Resolve a step against the active sequence, walking BACKWARDS through the
 * canonical order to the nearest step the sequence contains.
 *
 * Backwards is the whole point: clamping forward would drop the user past a
 * screen they never saw. Reached by a desktop user stored at Properties who
 * reopens on a phone, and by the `welcome` rewind hook.
 */
export function clampToSequence(
  step: OnboardingStepId,
  steps: readonly OnboardingStepId[],
): OnboardingStepId {
  if (steps.includes(step)) return step;
  for (let i = DESKTOP_STEPS.indexOf(step) - 1; i >= 0; i -= 1) {
    const candidate = DESKTOP_STEPS[i];
    if (steps.includes(candidate)) return candidate;
  }
  return steps[0];
}

/**
 * Server enum value -> UI step id.
 *
 * `welcome` resolves to the first step: it predates the wizard's current shape
 * and exists only so a test account can be rewound by hand.
 */
export function serverStepToId(step: string | null | undefined): OnboardingStepId {
  if (step === "welcome") return "company";
  if (step && (SERVER_PERSISTED_STEPS as readonly string[]).includes(step)) {
    return step as OnboardingStepId;
  }
  return DEFAULT_RESUME_STEP;
}

/** UI step id -> server enum value, or null where there is nothing to persist. */
export function idToServerStep(step: OnboardingStepId): string | null {
  return (SERVER_PERSISTED_STEPS as readonly string[]).includes(step) ? step : null;
}

/**
 * Read a step id out of localStorage.
 *
 * Returns null for anything unrecognized, which deliberately includes the
 * integer index the previous wizard wrote under the same key: an index cannot
 * be reinterpreted as an id, so it is dropped and the server-provided resume
 * step wins.
 */
export function parseStoredStepId(raw: string | null): OnboardingStepId | null {
  if (!raw) return null;
  return (DESKTOP_STEPS as readonly string[]).includes(raw)
    ? (raw as OnboardingStepId)
    : null;
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- onboardingStepSequence && npm run typecheck
```

Expected: all tests PASS, tsc clean.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/lib/onboardingSteps.ts tests/onboardingStepSequence.test.ts
git commit -m "feat: add onboarding step-sequence module

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Move resume from indices to step ids

**Files:**
- Modify: `portal/src/lib/onboarding.ts` (replace the two index maps and the return shape)
- Modify: `portal/src/api/auth.ts:159-185` (`setOnboardingResumeStep`, `applyOnboardingResume`)
- Test: `portal/tests/onboardingResume.test.ts` (rewrite), `portal/tests/onboardingResumeApply.test.ts` (update)

**Interfaces:**
- Consumes: everything from `src/lib/onboardingSteps.ts` (Task 2).
- Produces:
  - `resolveOnboardingResume(authData): { shouldResume: boolean; stepId: OnboardingStepId }` — note `stepId`, replacing `stepIndex`.
  - `setOnboardingResumeStep(step: OnboardingStepId): void` — writes the id string under the existing `ONBOARDING_STEP_KEY`.
  - `onboardingStepToUiIndex` and `uiIndexToOnboardingStep` are **deleted**.

- [ ] **Step 1: Rewrite the failing test**

Replace the whole of `portal/tests/onboardingResume.test.ts`:

```ts
/**
 * Resume routing. The server stores a semantic step; the wizard's state is a
 * step id; neither is an index any more.
 */
import { describe, test, expect } from "vitest";
import { resolveOnboardingResume } from "../src/lib/onboarding";

describe("resolveOnboardingResume", () => {
  test("resumes when a company exists but onboarding is incomplete", () => {
    const decision = resolveOnboardingResume({
      company_id: "abc123",
      onboarding_completed: false,
      onboarding_step: "materials",
    });
    expect(decision.shouldResume).toBe(true);
    expect(decision.stepId).toBe("materials");
  });

  test("does not resume once onboarding is completed", () => {
    const decision = resolveOnboardingResume({
      company_id: "abc123",
      onboarding_completed: true,
      onboarding_step: "materials",
    });
    expect(decision.shouldResume).toBe(false);
  });

  test("does not resume without a company", () => {
    const decision = resolveOnboardingResume({
      company_id: null,
      onboarding_completed: false,
    });
    expect(decision.shouldResume).toBe(false);
  });

  test("treats a legacy company with no flag as completed", () => {
    // Absent (undefined) is not false: companies predating the field finished
    // onboarding and must never be dragged back into the wizard.
    const decision = resolveOnboardingResume({ company_id: "abc123" });
    expect(decision.shouldResume).toBe(false);
  });

  test("falls back to the first post-company step for an unknown stored step", () => {
    const decision = resolveOnboardingResume({
      company_id: "abc123",
      onboarding_completed: false,
      onboarding_step: "bogus",
    });
    expect(decision.stepId).toBe("percentages");
  });

  test("resolves the welcome rewind hook to the first step", () => {
    const decision = resolveOnboardingResume({
      company_id: "abc123",
      onboarding_completed: false,
      onboarding_step: "welcome",
    });
    expect(decision.stepId).toBe("company");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- onboardingResume
```

Expected: FAIL — `decision.stepId` is `undefined` (the module still returns `stepIndex`).

- [ ] **Step 3: Rewrite `onboarding.ts`**

Replace the entire contents of `portal/src/lib/onboarding.ts`:

```ts
// Onboarding resume helpers.
//
// The server stores onboarding progress as a semantic step (see the backend
// `OnboardingStep` enum) so reordering the wizard cannot corrupt stored
// progress. The wizard's own state is a step id too — see
// ./onboardingSteps.ts, which owns the sequences and the id/enum mapping.

import { serverStepToId, type OnboardingStepId } from "./onboardingSteps";

export interface OnboardingAuthData {
  company_id?: string | null;
  onboarding_completed?: boolean;
  onboarding_step?: string | null;
}

export interface OnboardingResumeDecision {
  shouldResume: boolean;
  stepId: OnboardingStepId;
}

// Decide whether a returning user should be routed back into onboarding.
// Resume only when a company exists (so there is progress to resume) AND the
// server explicitly says onboarding is not completed. Legacy companies (field
// absent -> undefined) are treated as completed and never resumed.
export function resolveOnboardingResume(
  authData: OnboardingAuthData | null | undefined,
): OnboardingResumeDecision {
  const hasCompany = Boolean(authData?.company_id);
  const incomplete = authData?.onboarding_completed === false;
  return {
    shouldResume: hasCompany && incomplete,
    stepId: serverStepToId(authData?.onboarding_step),
  };
}
```

- [ ] **Step 4: Update `api/auth.ts`**

In `portal/src/api/auth.ts`, add the import at the top alongside the existing `./lib/onboarding` import:

```ts
import type { OnboardingStepId } from "../lib/onboardingSteps";
```

Then change `setOnboardingResumeStep` (line ~161) and the call inside `applyOnboardingResume` (line ~179):

```ts
// Seed the resume step that OnboardingPage reads on mount. Used when a returning
// user with incomplete onboarding is routed back into the wizard at login.
export function setOnboardingResumeStep(step: OnboardingStepId): void {
  localStorage.setItem(ONBOARDING_STEP_KEY, step);
}
```

```ts
  if (resume.shouldResume) {
    setOnboardingResumeStep(resume.stepId);
    setOnboardingInProgress();
  } else {
```

- [ ] **Step 5: Update the apply test**

In `portal/tests/onboardingResumeApply.test.ts`, every assertion reading `ONBOARDING_STEP_KEY` now expects an id string rather than a stringified index. Find each `localStorage.getItem(ONBOARDING_STEP_KEY)` assertion and change the expected value from the numeral to the matching id, using this mapping: `2 → "contacts"`, `3 → "properties"`, `4 → "materials"`, `5 → "people"`, `6 → "plan"`, `0 → "company"`. Update the `onboarding_step` values passed into the fixtures to match what each test is asserting.

- [ ] **Step 6: Run both tests to verify they pass**

```bash
cd portal && npm test -- onboardingResume && npm run typecheck
```

Expected: PASS, tsc clean. If tsc reports errors in `OnboardingPage.tsx` about `stepIndex`, that is expected — it is rewired in Task 8. Leave it and note it; do not patch it here.

- [ ] **Step 7: Commit (ask first)**

```bash
cd portal && git add src/lib/onboarding.ts src/api/auth.ts tests/onboardingResume.test.ts tests/onboardingResumeApply.test.ts
git commit -m "refactor: resume onboarding by step id instead of index

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: StepIndicator — sequence-driven, with a phone variant

**Files:**
- Modify: `portal/src/components/onboarding/StepIndicator.tsx` (full rewrite, 55 lines)
- Test: `portal/tests/StepIndicator.test.tsx` (create)

**Interfaces:**
- Consumes: `OnboardingStepId`, `stepLabel` from Task 2.
- Produces: `<StepIndicator steps={readonly OnboardingStepId[]} currentStep={OnboardingStepId} isPhone={boolean} />`. The old `currentStep: number` / `totalSteps?: number` props are gone.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/StepIndicator.test.tsx`:

```tsx
/**
 * Eight labelled dots do not fit at 375px. On a phone the indicator collapses
 * to a counter plus a bar; on a laptop it keeps the dots. Both read their
 * length from the active sequence, so neither hard-codes a step count.
 */
import { describe, test, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";

import { StepIndicator } from "../src/components/onboarding/StepIndicator";
import { DESKTOP_STEPS, PHONE_STEPS } from "../src/lib/onboardingSteps";

afterEach(cleanup);

describe("StepIndicator on a phone", () => {
  test("renders a counter sized to the phone sequence", () => {
    render(
      <StepIndicator steps={PHONE_STEPS} currentStep="contacts" isPhone />,
    );
    // Contacts is the 3rd of the phone sequence's 7 steps.
    expect(screen.getByText("Step 3 of 7")).toBeTruthy();
  });

  test("names the current step alongside the counter", () => {
    render(
      <StepIndicator steps={PHONE_STEPS} currentStep="materials" isPhone />,
    );
    expect(screen.getByText("Materials")).toBeTruthy();
    expect(screen.getByText("Step 4 of 7")).toBeTruthy();
  });

  test("does not render the full label list", () => {
    render(
      <StepIndicator steps={PHONE_STEPS} currentStep="company" isPhone />,
    );
    // Only the current step's label is present — the others would overflow.
    expect(screen.queryByText("Plan")).toBeNull();
    expect(screen.queryByText("People")).toBeNull();
  });

  test("reports progress to assistive tech", () => {
    render(<StepIndicator steps={PHONE_STEPS} currentStep="plan" isPhone />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("6");
    expect(bar.getAttribute("aria-valuemax")).toBe("7");
  });
});

describe("StepIndicator on a laptop", () => {
  test("renders every label in the desktop sequence", () => {
    render(
      <StepIndicator
        steps={DESKTOP_STEPS}
        currentStep="properties"
        isPhone={false}
      />,
    );
    for (const label of ["Company", "Defaults", "Contacts", "Properties", "Plan"]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
  });

  test("marks the current step for assistive tech", () => {
    const { container } = render(
      <StepIndicator
        steps={DESKTOP_STEPS}
        currentStep="materials"
        isPhone={false}
      />,
    );
    const current = container.querySelectorAll('[aria-current="step"]');
    expect(current.length).toBe(1);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- StepIndicator
```

Expected: FAIL — the component does not accept a `steps` prop.

- [ ] **Step 3: Rewrite the component**

Replace the entire contents of `portal/src/components/onboarding/StepIndicator.tsx`:

```tsx
/**
 * Onboarding progress.
 *
 * Eight labelled dots with connector rules do not fit at 375px — the labels
 * collide and the row overflows. So the phone gets a counter and a bar, which
 * costs no horizontal space and still says how much is left; losing that is
 * exactly when people abandon a signup.
 *
 * Neither variant hard-codes a step count: both read the active sequence, so
 * the phone's 7 and the laptop's 8 are correct without either knowing which
 * sequence it was handed.
 */
import { stepLabel, type OnboardingStepId } from "../../lib/onboardingSteps";

interface StepIndicatorProps {
  steps: readonly OnboardingStepId[];
  currentStep: OnboardingStepId;
  isPhone: boolean;
}

export function StepIndicator({ steps, currentStep, isPhone }: StepIndicatorProps) {
  const index = steps.indexOf(currentStep);
  // A step absent from the sequence is clamped by the caller before it reaches
  // here; guard anyway so a bad index can never render a negative-width bar.
  const position = index < 0 ? 0 : index;
  const humanPosition = position + 1;

  if (isPhone) {
    return (
      <nav aria-label="Onboarding progress" className="space-y-1.5">
        <div className="flex items-baseline justify-between">
          <span className="text-sm font-medium text-foreground">
            {stepLabel(currentStep)}
          </span>
          <span className="text-xs text-muted-foreground">
            Step {humanPosition} of {steps.length}
          </span>
        </div>
        <div
          role="progressbar"
          aria-valuenow={humanPosition}
          aria-valuemin={1}
          aria-valuemax={steps.length}
          className="h-1 w-full rounded-full bg-muted overflow-hidden"
        >
          <div
            className="h-full bg-primary transition-[width]"
            style={{ width: `${(humanPosition / steps.length) * 100}%` }}
          />
        </div>
      </nav>
    );
  }

  return (
    <nav aria-label="Onboarding progress">
      <ol className="flex items-center justify-center gap-2">
        {steps.map((step, i) => {
          const isCompleted = i < position;
          const isActive = i === position;

          return (
            <li key={step} className="flex items-center gap-2">
              {i > 0 && (
                <div
                  className={`h-px w-6 transition-colors ${
                    isCompleted ? "bg-primary" : "bg-border"
                  }`}
                />
              )}
              <div className="flex flex-col items-center gap-1">
                <div
                  aria-current={isActive ? "step" : undefined}
                  className={`h-2.5 w-2.5 rounded-full transition-colors ${
                    isCompleted || isActive ? "bg-primary" : "bg-muted"
                  }`}
                />
                <span
                  className={`text-xs transition-colors ${
                    isActive
                      ? "text-foreground font-medium"
                      : isCompleted
                        ? "text-muted-foreground"
                        : "text-muted-foreground/60"
                  }`}
                >
                  {stepLabel(step)}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- StepIndicator
```

Expected: PASS.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/onboarding/StepIndicator.tsx tests/StepIndicator.test.tsx
git commit -m "feat: give the onboarding progress indicator a phone variant

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Extract the default percentages into their own step

**Files:**
- Create: `portal/src/components/onboarding/CompanyDefaultsStep.tsx`
- Modify: `portal/src/components/onboarding/CompanyStep.tsx` — remove the six percentage fields from the form JSX (lines ~503-570) and from the submit payload (lines ~274-283); make `onBack` optional
- Test: `portal/tests/CompanyDefaultsStep.test.tsx` (create); `portal/tests/CompanyStepEdit.test.tsx` (update)

**Interfaces:**
- Consumes: `updateCompany`, `getCompany` from `../../api/companies`; `parsePercentInput` from `../../lib/format`.
- Produces: `<CompanyDefaultsStep companyId={string | null} onSaved={() => void} onBack={() => void} />`.
- `CompanyStep`'s `onBack` prop becomes `onBack?: () => void`; the Back button is hidden when it is absent (Company is now the first screen).

**Note on `PERCENT_KEYS`:** `CompanyStep.tsx` declares this const at lines 20-27 and uses it only to prefill percentages. It moves wholesale to `CompanyDefaultsStep.tsx`; delete it from `CompanyStep.tsx` along with the percentage entries in `CompanyFormData`, `getEmptyCompanyForm` and `companyToFormData`.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/CompanyDefaultsStep.test.tsx`:

```tsx
/**
 * The six default percentages, lifted off the Company screen so neither screen
 * is a sixteen-field scroll on a phone. The company already exists by the time
 * this renders, so this screen always PUTs — it never creates.
 */
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const getCompanyMock = vi.fn();
const updateCompanyMock = vi.fn();

vi.mock("../src/api/companies", () => ({
  getCompany: (...a: unknown[]) => getCompanyMock(...a),
  updateCompany: (...a: unknown[]) => updateCompanyMock(...a),
}));

import { CompanyDefaultsStep } from "../src/components/onboarding/CompanyDefaultsStep";

const existingCompany = {
  id: "company-123",
  name: "Existing Co",
  material_markup: 14,
  labor_burden: 33,
};

beforeEach(() => {
  getCompanyMock.mockReset().mockResolvedValue(existingCompany);
  updateCompanyMock.mockReset().mockResolvedValue(existingCompany);
});

afterEach(cleanup);

function renderStep(overrides: Record<string, unknown> = {}) {
  return render(
    <CompanyDefaultsStep
      companyId="company-123"
      onSaved={vi.fn()}
      onBack={vi.fn()}
      {...overrides}
    />,
  );
}

describe("CompanyDefaultsStep", () => {
  test("renders all six percentage fields", async () => {
    renderStep();
    await waitFor(() => expect(getCompanyMock).toHaveBeenCalled());
    for (const label of [
      /Tax Rate/i,
      /Overall Markup/i,
      /Overhead Allocation/i,
      /Materials Markup/i,
      /Standard Unbillable/i,
      /Labor Burden/i,
    ]) {
      expect(screen.getByLabelText(label)).toBeTruthy();
    }
  });

  test("prefills saved values and suggests defaults for the rest", async () => {
    renderStep();
    await waitFor(() => {
      expect(
        (screen.getByLabelText(/Materials Markup/i) as HTMLInputElement).value,
      ).toBe("14");
    });
    expect((screen.getByLabelText(/Labor Burden/i) as HTMLInputElement).value).toBe("33");
    // Not saved on the company -> the suggested starting value, visible and
    // editable rather than applied silently.
    expect((screen.getByLabelText(/Overall Markup/i) as HTMLInputElement).value).toBe("15");
  });

  test("saves with PUT and advances", async () => {
    const onSaved = vi.fn();
    renderStep({ onSaved });
    await waitFor(() => expect(getCompanyMock).toHaveBeenCalled());

    await userEvent.click(screen.getByRole("button", { name: /Save & Continue/i }));

    await waitFor(() => expect(updateCompanyMock).toHaveBeenCalled());
    expect(updateCompanyMock.mock.calls[0][0]).toBe("company-123");
    expect(onSaved).toHaveBeenCalled();
  });

  test("a cleared field saves 0, honoring the explicit clear", async () => {
    renderStep();
    await waitFor(() => expect(getCompanyMock).toHaveBeenCalled());

    await userEvent.clear(screen.getByLabelText(/Materials Markup/i));
    await userEvent.clear(screen.getByLabelText(/Labor Burden/i));
    await userEvent.click(screen.getByRole("button", { name: /Save & Continue/i }));

    await waitFor(() => expect(updateCompanyMock).toHaveBeenCalled());
    const payload = updateCompanyMock.mock.calls[0][1];
    expect(payload.material_markup).toBe(0);
    expect(payload.labor_burden).toBe(0);
  });

  test("a cleared Standard Unbillable saves 20, not 0", async () => {
    // The one field whose parsePercentInput fallback is not 0. It is a payroll
    // reality rather than a preference, and zeroing it would silently report
    // unbillable time as billable. Pinned so lifting these fields into a new
    // component cannot flatten it.
    renderStep();
    await waitFor(() => expect(getCompanyMock).toHaveBeenCalled());

    await userEvent.clear(screen.getByLabelText(/Standard Unbillable/i));
    await userEvent.click(screen.getByRole("button", { name: /Save & Continue/i }));

    await waitFor(() => expect(updateCompanyMock).toHaveBeenCalled());
    expect(updateCompanyMock.mock.calls[0][1].standard_unbillable_percent).toBe(20);
  });

  test("surfaces a save failure instead of advancing", async () => {
    updateCompanyMock.mockRejectedValue(new Error("Network down"));
    const onSaved = vi.fn();
    renderStep({ onSaved });
    await waitFor(() => expect(getCompanyMock).toHaveBeenCalled());

    await userEvent.click(screen.getByRole("button", { name: /Save & Continue/i }));

    await waitFor(() => expect(screen.getByRole("alert").textContent).toMatch(/Network down/));
    expect(onSaved).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- CompanyDefaultsStep
```

Expected: FAIL — cannot resolve `CompanyDefaultsStep`.

- [ ] **Step 3: Write the component**

Create `portal/src/components/onboarding/CompanyDefaultsStep.tsx`:

```tsx
/**
 * The company's default percentages, lifted off the Company screen.
 *
 * Sixteen fields on one screen is a long scroll before the first Save on a
 * phone, and a lot to take in on a laptop. Splitting them costs a screen and
 * buys two that fit.
 *
 * The company always exists by the time this renders — it was created by the
 * previous screen — so this only ever PUTs.
 */
import { useEffect, useState } from "react";
import { getCompany, updateCompany } from "../../api/companies";
import { parsePercentInput } from "../../lib/format";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

const PERCENT_KEYS = [
  "tax_rate",
  "default_profit_margin",
  "default_overhead_allocation",
  "material_markup",
  "standard_unbillable_percent",
  "labor_burden",
] as const;

type PercentKey = (typeof PERCENT_KEYS)[number];
type PercentForm = Record<PercentKey, string>;

// Suggested starting values, not silent defaults — the user sees every one of
// these and can override any of them before saving.
const SUGGESTED: PercentForm = {
  tax_rate: "0",
  default_profit_margin: "15",
  default_overhead_allocation: "20",
  material_markup: "10",
  standard_unbillable_percent: "20",
  labor_burden: "20",
};

// Every percentage is pre-filled above, so a blank field means the user
// deliberately cleared it — 0 is the honest reading, and the platform does not
// substitute a house value over an explicit choice. Standard Unbillable is the
// exception: it is a payroll reality rather than a preference, and zeroing it
// would report unbillable time as billable.
const CLEARED_FALLBACK: Record<PercentKey, number> = {
  tax_rate: 0,
  default_profit_margin: 0,
  default_overhead_allocation: 0,
  material_markup: 0,
  standard_unbillable_percent: 20,
  labor_burden: 0,
};

const FIELDS: { key: PercentKey; id: string; label: string; step: string }[] = [
  { key: "tax_rate", id: "ob_tax_rate", label: "Tax Rate (%)", step: "0.01" },
  { key: "default_profit_margin", id: "ob_profit_margin", label: "Overall Markup (%)", step: "0.1" },
  { key: "default_overhead_allocation", id: "ob_overhead", label: "Overhead Allocation (%)", step: "0.1" },
  { key: "material_markup", id: "ob_material_markup", label: "Materials Markup (%)", step: "0.1" },
  { key: "standard_unbillable_percent", id: "ob_standard_unbillable_percent", label: "Standard Unbillable (%)", step: "0.1" },
  { key: "labor_burden", id: "ob_labor_burden", label: "Labor Burden (%)", step: "0.1" },
];

interface CompanyDefaultsStepProps {
  companyId: string | null;
  onSaved: () => void;
  onBack: () => void;
}

export function CompanyDefaultsStep({
  companyId,
  onSaved,
  onBack,
}: CompanyDefaultsStepProps) {
  const [form, setForm] = useState<PercentForm>(() => ({ ...SUGGESTED }));
  const [isPrefilling, setIsPrefilling] = useState<boolean>(Boolean(companyId));
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!companyId) {
      setIsPrefilling(false);
      return;
    }
    // Re-armed in the effect body, not only in cleanup: StrictMode runs the
    // cleanup of the first pass before the second, and a flag left false there
    // would discard the second pass's result.
    let alive = true;
    setIsPrefilling(true);
    void (async () => {
      try {
        const company = await getCompany(companyId);
        if (!alive || !company) return;
        setForm((previous) => {
          const next = { ...previous };
          for (const key of PERCENT_KEYS) {
            const value = (company as Record<string, unknown>)[key];
            if (typeof value === "number") next[key] = String(value);
          }
          return next;
        });
      } catch {
        // A failed prefill leaves the suggested values in place, which the user
        // can still edit and save — better than blocking the wizard.
      } finally {
        if (alive) setIsPrefilling(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [companyId]);

  const handleChange = (key: PercentKey, value: string) => {
    setForm((previous) => ({ ...previous, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyId) {
      setErrorMessage("Missing company context. Please reload and try again.");
      return;
    }
    setErrorMessage("");
    setIsSubmitting(true);
    try {
      const payload: Record<string, number> = {};
      for (const key of PERCENT_KEYS) {
        payload[key] = parsePercentInput(form[key], CLEARED_FALLBACK[key]);
      }
      await updateCompany(companyId, payload);
      onSaved();
    } catch (error: unknown) {
      const err = error as { message?: string };
      setErrorMessage(err?.message || "Failed to save your defaults. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isPrefilling) {
    return (
      <div className="py-12 text-center text-sm text-muted-foreground" role="status">
        Loading your company...
      </div>
    );
  }

  return (
    <div className="py-4">
      <div className="text-center mb-6">
        <h2 className="text-xl font-medium text-foreground">Your Default Percentages</h2>
        <p className="text-sm text-muted-foreground mt-1">
          These seed every new estimate. You can change any of them later in Settings.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FIELDS.map((field) => (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={field.id}>{field.label}</Label>
              <Input
                type="number"
                step={field.step}
                id={field.id}
                value={form[field.key]}
                onChange={(e) => handleChange(field.key, e.target.value)}
              />
            </div>
          ))}
        </div>

        {errorMessage ? (
          <p className="text-sm text-red-600" role="alert">
            {errorMessage}
          </p>
        ) : null}

        <div className="flex gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onBack} className="flex-1">
            Back
          </Button>
          <Button type="submit" disabled={isSubmitting} variant="brand" className="flex-1">
            {isSubmitting ? "Saving..." : "Save & Continue"}
          </Button>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 4: Run the new test to verify it passes**

```bash
cd portal && npm test -- CompanyDefaultsStep
```

Expected: PASS.

- [ ] **Step 5: Strip the percentages out of `CompanyStep.tsx`**

Four edits, all deletions plus one prop change:

1. Delete the `PERCENT_KEYS` const (lines 18-27, including its comment).
2. In `CompanyFormData`, delete the six percentage members (`tax_rate` through `labor_burden`).
3. In `getEmptyCompanyForm`, delete the six percentage entries and the two-line comment above them.
4. In `companyToFormData`, delete the `for (const key of PERCENT_KEYS)` loop.
5. In `handleSubmit`'s `payload`, delete the six `parsePercentInput(...)` lines and the four-line comment above them.
6. Delete the entire `<div className="border-t border-border pt-4 mt-4">` block containing "Default Company Percentages" (lines ~503-570).
7. Remove the now-unused `parsePercentInput` import.
8. Make Back optional, since Company is now the first screen:

```tsx
  onBack?: () => void;
```

and in the JSX:

```tsx
        <div className="flex gap-3 pt-2">
          {onBack ? (
            <Button type="button" variant="outline" onClick={onBack} className="flex-1">
              Back
            </Button>
          ) : null}
```

- [ ] **Step 6: Update `CompanyStepEdit.test.tsx`**

Delete the whole `describe("CompanyStep — cleared percentage fields")` block (lines ~178-217) — that behavior now lives in `CompanyDefaultsStep.test.tsx`. Remove `material_markup: 14` and `labor_burden: 33` from the `existingCompany` fixture. Then add one test pinning the split:

```tsx
test("no longer renders the percentage fields", async () => {
  render(
    <CompanyStep
      companyId="company-123"
      onCompanyCreated={vi.fn()}
      onCompanyUpdated={vi.fn()}
      onBack={vi.fn()}
    />,
  );
  await waitFor(() => expect(getCompanyMock).toHaveBeenCalled());
  // They moved to CompanyDefaultsStep; sixteen fields on one screen was the
  // reason this screen did not fit a phone.
  expect(screen.queryByLabelText(/Materials Markup/i)).toBeNull();
  expect(screen.queryByLabelText(/Labor Burden/i)).toBeNull();
  expect(screen.queryByText(/Default Company Percentages/i)).toBeNull();
});
```

- [ ] **Step 7: Run both tests and typecheck**

```bash
cd portal && npm test -- CompanyDefaultsStep CompanyStepEdit && npm run typecheck
```

Expected: PASS. `OnboardingPage.tsx` may still have tsc errors from Task 3 — that is expected until Task 8.

- [ ] **Step 8: Commit (ask first)**

```bash
cd portal && git add src/components/onboarding/CompanyDefaultsStep.tsx src/components/onboarding/CompanyStep.tsx tests/CompanyDefaultsStep.test.tsx tests/CompanyStepEdit.test.tsx
git commit -m "feat: split company default percentages onto their own step

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: `CsvUploadStep` information-only mode

**Files:**
- Modify: `portal/src/components/onboarding/CsvUploadStep.tsx`
- Test: `portal/tests/CsvUploadStep.test.tsx` (append a describe block)

**Interfaces:**
- Consumes: nothing new.
- Produces: two new optional props on `CsvUploadStep`:
  - `infoOnly?: boolean` — hides the sample-CSV link, the file picker and the standard-list checkbox, leaving the prose and a Next button. When set, `onUpload` and `onLoadStandard` are never called.
  - `secondaryOverviewText?: string` — a third paragraph rendered between `overviewText` and `importText`, used only by the merged phone screen.
  - `nextLabel?: string` — the primary button's label when there is nothing to upload. Defaults to the existing `skipLabel` behavior.

- [ ] **Step 1: Write the failing test**

Append to `portal/tests/CsvUploadStep.test.tsx`:

```tsx
describe("CsvUploadStep information-only mode", () => {
  const infoProps = {
    ...baseProps,
    title: "Contacts & Properties",
    infoOnly: true,
    secondaryOverviewText: "Properties are the job sites where work is performed.",
    nextLabel: "Got it — continue",
  };

  test("hides the file picker, sample link and standard checkbox", () => {
    const { container } = render(<CsvUploadStep {...infoProps} />);
    // Picking a CSV out of a phone's file system mid-signup is not a thing a
    // new user will do, so the screen stops asking.
    expect(container.querySelector('input[type="file"]')).toBeNull();
    expect(screen.queryByText(/Download Sample CSV/i)).toBeNull();
    expect(screen.queryByText(/Use 3Maples Standard Materials List/i)).toBeNull();
  });

  test("still shows all the explanatory prose", () => {
    render(<CsvUploadStep {...infoProps} />);
    expect(screen.getByText("overview")).toBeTruthy();
    expect(screen.getByText(/Properties are the job sites/i)).toBeTruthy();
    expect(screen.getByText("import")).toBeTruthy();
  });

  test("advances without ever uploading", async () => {
    render(<CsvUploadStep {...infoProps} />);
    fireEvent.click(screen.getByRole("button", { name: /Got it — continue/i }));
    await waitFor(() => expect(onNext).toHaveBeenCalled());
    expect(onUpload).not.toHaveBeenCalled();
    expect(onLoadStandard).not.toHaveBeenCalled();
  });

  test("never opens the skip-confirm dialog", async () => {
    // There is nothing to skip — the screen asked for nothing.
    render(
      <CsvUploadStep
        {...infoProps}
        skipConfirmTitle="No materials added yet"
        skipConfirmMessage="You haven't uploaded anything."
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Got it — continue/i }));
    await waitFor(() => expect(onNext).toHaveBeenCalled());
    expect(screen.queryByText(/No materials added yet/i)).toBeNull();
  });
});

describe("CsvUploadStep normal mode is unchanged by the info-only prop", () => {
  test("still renders the picker when infoOnly is absent", () => {
    const { container } = render(<CsvUploadStep {...baseProps} onLoadStandard={onLoadStandard} />);
    expect(container.querySelector('input[type="file"]')).not.toBeNull();
    expect(screen.getByText(/Download Sample CSV/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- CsvUploadStep
```

Expected: FAIL — the file input is still rendered.

- [ ] **Step 3: Implement the mode**

In `portal/src/components/onboarding/CsvUploadStep.tsx`:

Add to the props interface, after `skipConfirmTitle`:

```tsx
  /**
   * Strips the screen down to its explanatory prose and a Next button: no
   * sample-CSV link, no file picker, no standard-list checkbox. Used on a
   * phone, where picking a CSV out of the file system mid-signup is not
   * something a new user will do. `onUpload` and `onLoadStandard` are never
   * called in this mode, and the skip-confirm never opens — there is nothing
   * to skip, because the screen asked for nothing.
   */
  infoOnly?: boolean;
  /** A third paragraph between overview and import — the merged phone screen. */
  secondaryOverviewText?: string;
  /** Primary button label when there is nothing staged. Falls back to skipLabel. */
  nextLabel?: string;
```

Add them to the destructured parameter list.

Replace `handlePrimaryClick` with:

```tsx
  const handlePrimaryClick = () => {
    // Nothing was asked for, so there is nothing to warn about and nothing to
    // upload — go straight on.
    if (infoOnly) {
      onNext();
      return;
    }
    if (!hasWork && !importedAny && skipConfirmMessage) {
      setShowSkipConfirm(true);
      return;
    }
    void handleNext();
  };
```

Add the secondary paragraph inside the `bg-secondary` block, between the two existing `<p>` elements:

```tsx
        {secondaryOverviewText ? (
          <p className="text-sm text-muted-foreground leading-relaxed">
            {secondaryOverviewText}
          </p>
        ) : null}
```

Wrap the interactive region — the `<div className="space-y-6">` containing the sample link, picker, errors and checkbox — so it renders only outside info-only mode:

```tsx
      {infoOnly ? null : (
        <div className="space-y-6">
          {/* ...unchanged contents... */}
        </div>
      )}
```

Change the primary button's label expression:

```tsx
          {isUploading
            ? "Uploading..."
            : isLoadingStandard
              ? "Loading..."
              : hasWork
                ? "Next"
                : (nextLabel ?? skipLabel ?? "Setup Later")}
```

Finally, guard the dialog so it cannot render in info-only mode:

```tsx
      {skipConfirmMessage && !infoOnly ? (
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- CsvUploadStep && npm run typecheck
```

Expected: PASS, including every pre-existing test in that file.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/onboarding/CsvUploadStep.tsx tests/CsvUploadStep.test.tsx
git commit -m "feat: add an information-only mode to the CSV import step

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Collapse the plan cards on a phone

**Files:**
- Modify: `portal/src/components/billing/PlanPickerGrid.tsx` (the `PlanCardBody` function)
- Test: `portal/tests/PlanPickerGrid.test.tsx` (append), `portal/tests/ManagePlanModal.test.tsx` (check and update if it asserts on feature text)

**Interfaces:**
- Consumes: `useIsPhone` from `../../lib/viewport`.
- Produces: no prop changes. `PlanPickerGrid`'s public surface is unchanged; the collapse is internal and viewport-driven, so the in-app Manage Plan modal gets it too.

**Note:** the `lg:` subgrid alignment is untouched — it engages at ≥1024px, where nothing is collapsed.

- [ ] **Step 1: Write the failing test**

Append to `portal/tests/PlanPickerGrid.test.tsx` (reuse the `stubMatchMedia` helper from `tests/useIsPhone.test.tsx` — copy it into this file; it is 30 lines and duplicating it keeps the two files independent):

```tsx
describe("PlanPickerGrid on a phone", () => {
  test("collapses the feature list behind a toggle", () => {
    stubMatchMedia(true);
    render(<PlanPickerGrid pendingKey={null} onSelect={vi.fn()} />);
    // Four cards (Free, Base, Pro, Enterprise), each with its own toggle.
    expect(screen.getAllByRole("button", { name: /See what's included/i }).length).toBe(4);
    expect(screen.queryByText(/Everything to get started:/i)).toBeNull();
  });

  test("keeps name, price and action visible while collapsed", () => {
    stubMatchMedia(true);
    render(<PlanPickerGrid pendingKey={null} onSelect={vi.fn()} />);
    expect(screen.getByText(/^Free$/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Select Free Plan/i })).toBeTruthy();
  });

  test("expands on click", async () => {
    stubMatchMedia(true);
    render(<PlanPickerGrid pendingKey={null} onSelect={vi.fn()} />);
    const toggles = screen.getAllByRole("button", { name: /See what's included/i });
    await userEvent.click(toggles[0]);
    expect(screen.getByText(/Everything to get started:/i)).toBeTruthy();
  });

  test("does not collapse above the breakpoint", () => {
    stubMatchMedia(false);
    render(<PlanPickerGrid pendingKey={null} onSelect={vi.fn()} />);
    expect(screen.queryByRole("button", { name: /See what's included/i })).toBeNull();
    expect(screen.getByText(/Everything to get started:/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- PlanPickerGrid
```

Expected: FAIL — no toggle button exists.

- [ ] **Step 3: Implement the collapse**

In `portal/src/components/billing/PlanPickerGrid.tsx`, add the imports:

```tsx
import { useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { useIsPhone } from "../../lib/viewport";
```

Inside `PlanCardBody`, above the `cardClass` const:

```tsx
  // Four full-height cards stacked on a phone is a very long scroll before the
  // user can compare anything. Collapsed, the four decisions fit on one screen
  // and the detail is one tap away. Shared with the in-app Manage Plan modal,
  // which has the same problem.
  const isPhone = useIsPhone();
  const [isExpanded, setIsExpanded] = useState(false);
  const showDetail = !isPhone || isExpanded;
```

Immediately after the action-button div (section 4), add the toggle:

```tsx
      {/* 4b — Phone-only detail toggle */}
      {isPhone ? (
        <button
          type="button"
          onClick={() => setIsExpanded((previous) => !previous)}
          aria-expanded={isExpanded}
          className={`flex items-center justify-center gap-1 text-sm ${theme.mutedClass}`}
        >
          {isExpanded ? "Hide details" : "See what's included"}
          <ChevronDown
            aria-hidden="true"
            className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-180" : ""}`}
          />
        </button>
      ) : null}
```

Then wrap sections 5, 6 and 7 (features, supports, limits) in `{showDetail ? ( ... ) : null}` as a single fragment, so one toggle governs all three:

```tsx
      {showDetail ? (
        <>
          {/* 5 — Features ... 6 — Available supports ... 7 — Plan limitations */}
        </>
      ) : null}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- PlanPickerGrid ManagePlanModal PlanStep PlanLimitsCopy && npm run typecheck
```

Expected: PASS. If `ManagePlanModal.test.tsx` or `PlanLimitsCopy.test.tsx` assert on feature text and fail, they are running without a `matchMedia` stub — `matchesMediaQuery` returns `false` there, so `isPhone` is `false` and nothing collapses. A failure therefore means a genuine regression; investigate rather than stubbing it away.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/billing/PlanPickerGrid.tsx tests/PlanPickerGrid.test.tsx
git commit -m "feat: collapse plan card details on a phone

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Rewire `OnboardingPage` to the sequence

**Files:**
- Modify: `portal/src/pages/OnboardingPage.tsx` (substantial rewrite)
- Delete: `portal/src/components/onboarding/WelcomeStep.tsx`
- Test: `portal/tests/OnboardingPageSequence.test.tsx` (create)

**Interfaces:**
- Consumes: everything from Tasks 2-7.
- Produces: the finished wizard. No exported surface changes — `OnboardingPage` is still the default export.

- [ ] **Step 1: Write the failing test**

Create `portal/tests/OnboardingPageSequence.test.tsx`:

```tsx
/**
 * The wizard drives off a device-derived sequence rather than integer indices.
 * These tests pin the sequence-level behavior — which screens appear, in what
 * order, and what happens when the stored step is not in the active sequence.
 */
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

vi.mock("firebase/auth", () => ({ signOut: vi.fn(async () => undefined) }));
vi.mock("../src/firebase", () => ({ firebaseAuth: { currentUser: null } }));
vi.mock("../src/api/companies", () => ({
  getCompany: vi.fn(async () => ({ id: "company-123", name: "Acme" })),
  updateCompany: vi.fn(async () => ({ id: "company-123" })),
}));
vi.mock("../src/api/addresses", () => ({
  addressesApi: {
    autocomplete: vi.fn(async () => ({ predictions: [] })),
    resolve: vi.fn(async () => ({ matched: false })),
  },
}));
vi.mock("../src/api/billing", () => ({
  billingApi: { selectPlan: vi.fn(async () => ({ ok: true })) },
}));
vi.mock("../src/api/resources", () => ({
  contactsApi: { uploadCsv: vi.fn() },
  propertiesApi: { uploadCsv: vi.fn() },
  materialsApi: { uploadCsv: vi.fn(), loadStandard: vi.fn(async () => ({})) },
  peopleApi: { uploadCsv: vi.fn(), loadStandard: vi.fn(async () => ({})) },
}));

import OnboardingPage from "../src/pages/OnboardingPage";
import { ONBOARDING_STEP_KEY } from "../src/api/auth";

type Listener = () => void;

function stubMatchMedia(isPhone: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: isPhone,
    media: query,
    addEventListener: (_e: string, _l: Listener) => undefined,
    removeEventListener: (_e: string, _l: Listener) => undefined,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onchange: null,
  })) as unknown as typeof window.matchMedia;
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  delete (window as { matchMedia?: unknown }).matchMedia;
});

function renderWizard() {
  return render(
    <MemoryRouter>
      <OnboardingPage />
    </MemoryRouter>,
  );
}

describe("the wizard's first screen", () => {
  test("opens on Create Your Company, not a welcome screen", () => {
    stubMatchMedia(false);
    renderWizard();
    expect(screen.getByText(/Create Your Company/i)).toBeTruthy();
    expect(screen.queryByText(/I am Maple, your AI Assistant/i)).toBeNull();
    expect(screen.queryByRole("button", { name: /Get Started/i })).toBeNull();
  });

  test("has no Back button, being the first screen", () => {
    stubMatchMedia(false);
    renderWizard();
    expect(screen.queryByRole("button", { name: /^Back$/i })).toBeNull();
  });
});

describe("progress indicator", () => {
  test("counts seven steps on a phone", () => {
    stubMatchMedia(true);
    localStorage.setItem(ONBOARDING_STEP_KEY, "contacts");
    renderWizard();
    expect(screen.getByText("Step 3 of 7")).toBeTruthy();
  });

  test("shows the full label row on a laptop", () => {
    stubMatchMedia(false);
    localStorage.setItem(ONBOARDING_STEP_KEY, "contacts");
    renderWizard();
    expect(screen.getByText("Properties")).toBeTruthy();
    expect(screen.queryByText(/Step 3 of/)).toBeNull();
  });
});

describe("the merged phone screen", () => {
  test("covers both Contacts and Properties, and asks for neither", async () => {
    stubMatchMedia(true);
    localStorage.setItem(ONBOARDING_STEP_KEY, "contacts");
    const { container } = renderWizard();

    expect(screen.getByText(/Contacts & Properties/i)).toBeTruthy();
    expect(screen.getByText(/Since you're on your phone/i)).toBeTruthy();
    expect(container.querySelector('input[type="file"]')).toBeNull();
  });

  test("advances straight to Materials, skipping the Properties screen", async () => {
    stubMatchMedia(true);
    localStorage.setItem(ONBOARDING_STEP_KEY, "contacts");
    renderWizard();

    await userEvent.click(screen.getByRole("button", { name: /continue/i }));
    await waitFor(() => expect(screen.getByText(/Load Materials/i)).toBeTruthy());
  });
});

describe("clamping a step absent from the active sequence", () => {
  test("a desktop user stored at Properties lands on the merged phone screen", () => {
    stubMatchMedia(true);
    localStorage.setItem(ONBOARDING_STEP_KEY, "properties");
    renderWizard();
    // Clamped backwards to Contacts, which absorbed Properties. Never forwards
    // — that would skip a screen this user has not seen.
    expect(screen.getByText(/Contacts & Properties/i)).toBeTruthy();
  });

  test("clamping does not overwrite the stored step", () => {
    stubMatchMedia(true);
    localStorage.setItem(ONBOARDING_STEP_KEY, "properties");
    renderWizard();
    // Render-time derivation, not a write-back: widening the window later must
    // return the user to Properties rather than stranding them on Contacts.
    expect(localStorage.getItem(ONBOARDING_STEP_KEY)).toBe("properties");
  });

  test("a legacy numeric index falls back to the first post-company step", () => {
    stubMatchMedia(false);
    localStorage.setItem(ONBOARDING_STEP_KEY, "4");
    renderWizard();
    expect(screen.getByText(/Your Default Percentages/i)).toBeTruthy();
  });
});

describe("the desktop sequence", () => {
  test("still shows Properties as its own importable screen", () => {
    stubMatchMedia(false);
    localStorage.setItem(ONBOARDING_STEP_KEY, "properties");
    const { container } = renderWizard();
    expect(screen.getByText(/Add Properties/i)).toBeTruthy();
    expect(container.querySelector('input[type="file"]')).not.toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- OnboardingPageSequence
```

Expected: FAIL — the wizard still opens on the Welcome screen.

- [ ] **Step 3: Rewrite the page**

Replace `portal/src/pages/OnboardingPage.tsx`. The parts that change:

Replace the `WelcomeStep` import with the new modules:

```tsx
import { CompanyDefaultsStep } from "../components/onboarding/CompanyDefaultsStep";
import { useIsPhone } from "../lib/viewport";
import {
  stepsForViewport,
  clampToSequence,
  parseStoredStepId,
  idToServerStep,
  type OnboardingStepId,
} from "../lib/onboardingSteps";
```

Replace the `currentStep` state and `goToStep` with:

```tsx
  const isPhone = useIsPhone();
  const steps = stepsForViewport(isPhone);

  // The STORED step, which is not necessarily the one on screen: a step absent
  // from the active sequence is clamped for rendering only (below), never
  // written back. That is what lets a window narrowed across the breakpoint and
  // widened again return the user to where they were.
  const [storedStep, setStoredStep] = useState<OnboardingStepId>(
    () => parseStoredStepId(localStorage.getItem(ONBOARDING_STEP_KEY)) ?? "company",
  );

  // Derived, not an effect: an effect correcting state afterwards would render
  // one frame of a step the sequence does not contain, and would need the
  // StrictMode re-arm dance to boot.
  const currentStep = clampToSequence(storedStep, steps);
  const stepIndex = steps.indexOf(currentStep);

  const goToStep = (step: OnboardingStepId) => {
    setStoredStep(step);
    localStorage.setItem(ONBOARDING_STEP_KEY, step);
    // Persist resumable steps server-side so an interrupted signup picks up
    // here on next login (even on another device). localStorage stays the fast
    // local mirror; a failed PATCH is non-fatal — the server reconciles on the
    // next successful advance.
    const serverStep = idToServerStep(step);
    if (serverStep) {
      void updateOnboardingProgress({ step: serverStep }).catch((e) => {
        Sentry.captureException(e);
      });
    }
  };

  const goNext = () => {
    const next = steps[stepIndex + 1];
    if (next) goToStep(next);
  };

  const goBack = () => {
    const previous = steps[stepIndex - 1];
    if (previous) goToStep(previous);
  };

  // Company is the first screen now, so it has nowhere to go back to.
  const backHandler = stepIndex > 0 ? goBack : undefined;
```

Change `handleCompanyCreated`'s last line from `goToStep(2)` to `goToStep("percentages")`.

Change the container width rule:

```tsx
  // Plan step needs more horizontal room for the 4-card layout.
  const containerWidthClass = currentStep === "plan" ? "max-w-6xl" : "max-w-3xl";
```

Replace the indicator:

```tsx
          <StepIndicator steps={steps} currentStep={currentStep} isPhone={isPhone} />
```

Replace the whole if-chain of `{currentStep === N && ...}` blocks with id comparisons. The Welcome block is deleted. The Contacts block becomes conditional on `isPhone`:

```tsx
          {currentStep === "company" && (
            <CompanyStep
              initialEmail={initialEmail}
              companyId={companyId}
              onCompanyCreated={handleCompanyCreated}
              onCompanyUpdated={() => goToStep("percentages")}
              onBack={backHandler}
            />
          )}

          {currentStep === "percentages" && (
            <CompanyDefaultsStep
              companyId={companyId}
              onSaved={goNext}
              onBack={goBack}
            />
          )}

          {currentStep === "contacts" && (
            isPhone ? (
              <CsvUploadStep
                title="Contacts & Properties"
                infoOnly
                overviewText="Contacts are the people, or companies, associated with a Property — typically the homeowners or site managers. Keeping your Contacts organized streamlines communication and ties every job back to the right people."
                secondaryOverviewText="Properties are the job sites or locations where work is performed. Each property can be linked to one or more contacts and used across multiple estimates."
                importText="Since you're on your phone, I'll skip asking you to import your Contacts and Properties so we can get you up and running. Both are easy to add later from a computer — or just ask me and I'll add them one at a time."
                sampleCsvUrl={CONTACTS_SAMPLE_CSV_URL}
                onUpload={(file) => contactsApi.uploadCsv(companyId, file)}
                nextLabel="Got it — continue"
                onNext={goNext}
                onBack={goBack}
              />
            ) : (
              <CsvUploadStep
                title="Import Contacts"
                overviewText="Contacts are the people, or companies, associated with a Property — typically the homeowners or site managers. Keeping your Contacts organized streamlines communication and ties every job back to the right people."
                importText="Import your existing contacts now so I can automatically link them to your Properties in the next step. If you'd prefer, you can do this later from the Contacts section."
                sampleCsvUrl={CONTACTS_SAMPLE_CSV_URL}
                onUpload={(file) => contactsApi.uploadCsv(companyId, file)}
                uploadLabel="Upload your Contacts CSV file:"
                skipLabel="Import Contacts Later"
                onNext={goNext}
                onBack={goBack}
              />
            )
          )}
```

The `properties`, `materials`, `people` and `plan` blocks keep their existing props verbatim; only the guard and the navigation callbacks change — `currentStep === "properties"` etc., with `onNext={goNext}` and `onBack={goBack}`. The `plan` block's `onSelected` becomes:

```tsx
              onSelected={(planKey) => {
                persistSelectedPlan(planKey);
                goNext();
              }}
```

And `complete`:

```tsx
          {currentStep === "complete" && (
            <CompletionStep onFinish={handleFinish} planLookupKey={selectedPlan} isPhone={isPhone} />
          )}
```

- [ ] **Step 4: Delete the Welcome step**

```bash
cd portal && git rm src/components/onboarding/WelcomeStep.tsx
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
cd portal && npm test -- OnboardingPageSequence onboardingPlanPersistence && npm run typecheck
```

Expected: PASS, tsc clean across the whole project now.

- [ ] **Step 6: Commit (ask first)**

```bash
cd portal && git add src/pages/OnboardingPage.tsx tests/OnboardingPageSequence.test.tsx
git commit -m "feat: drive onboarding off a device-derived step sequence

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: CompletionStep phone note

**Files:**
- Modify: `portal/src/components/onboarding/CompletionStep.tsx`
- Test: `portal/tests/CompletionStep.test.tsx` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: `CompletionStep` gains `isPhone?: boolean`. Passed by `OnboardingPage` in Task 8.

- [ ] **Step 1: Write the failing test**

Append to `portal/tests/CompletionStep.test.tsx`:

```tsx
describe("CompletionStep on a phone", () => {
  test("says what was skipped and where to finish it", () => {
    render(<CompletionStep onFinish={vi.fn()} planLookupKey="plan_free" isPhone />);
    expect(screen.getByText(/from a computer/i)).toBeTruthy();
  });

  test("says nothing of the sort on a laptop", () => {
    render(<CompletionStep onFinish={vi.fn()} planLookupKey="plan_free" />);
    expect(screen.queryByText(/from a computer/i)).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd portal && npm test -- CompletionStep
```

Expected: FAIL — the text is absent.

- [ ] **Step 3: Add the note**

In `portal/src/components/onboarding/CompletionStep.tsx`, add `isPhone?: boolean` to the props interface and the destructured list, then insert after the first `<p>` in the prose block:

```tsx
          {isPhone ? (
            <p>
              I skipped importing your Contacts and Properties to keep this
              short. Whenever you&apos;re at a computer you can bring them in,
              swap the standard lists for your own, and change your plan — or
              just ask me and I&apos;ll add things one at a time.
            </p>
          ) : null}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd portal && npm test -- CompletionStep && npm run typecheck
```

Expected: PASS.

- [ ] **Step 5: Commit (ask first)**

```bash
cd portal && git add src/components/onboarding/CompletionStep.tsx tests/CompletionStep.test.tsx
git commit -m "feat: tell phone users where to finish setup

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Documentation and full verification

**Files:**
- Modify: `documentation/development/plans/2026-09-15-phone-onboarding-design.md` (§5 correction)
- Modify: `CLAUDE.md` if it describes the onboarding step count — check with `grep -n "onboarding" CLAUDE.md`

- [ ] **Step 1: Correct spec §5**

In §5 of the design doc, replace this sentence:

> widening again leaves them on Contacts, since it is the id that moved.

with:

> widening again returns them to Properties: the clamp is a render-time
> derivation and never writes back, so the stored id survives the round trip.

- [ ] **Step 2: Check CLAUDE.md**

```bash
cd /Users/simon/Development/Tangz/3maples && grep -n "onboarding\|Onboarding" CLAUDE.md
```

Expected matches are all in the Brevo section (lines ~396-432) and concern
lifecycle events, not the wizard's shape. One of them cites
`portal/src/lib/onboarding.ts::resolveOnboardingResume` — that function and its
path both survive this work, so the reference stays correct and needs no edit.
CLAUDE.md does not document the wizard's step count, and this plan does not add
a reason to start. Confirm that is still true and make no change.

- [ ] **Step 3: Run every touched test file**

```bash
cd portal && npm test -- onboardingStepSequence onboardingResume onboardingResumeApply StepIndicator CompanyDefaultsStep CompanyStepEdit CsvUploadStep PlanPickerGrid PlanStep ManagePlanModal PlanLimitsCopy OnboardingPageSequence onboardingPlanPersistence CompletionStep useIsPhone
```

Expected: all PASS.

- [ ] **Step 4: Run the type and lint gates**

```bash
cd portal && npm run typecheck && npm run lint
```

```bash
cd platform && ./run_mypy.sh models/company.py routers/auth.py && ./run_ruff.sh models/company.py routers/auth.py
```

Expected: zero errors from all four.

- [ ] **Step 5: Manual check at 375px**

Run `npm run dev`, open the wizard in a browser at a 375×812 viewport, and walk all seven phone screens. Confirm: no horizontal scroll on any screen; the progress line reads `Step N of 7`; the merged Contacts & Properties screen shows no file picker; Materials and People still open the skip-confirm dialog when you take "Later" with nothing selected; the plan cards are collapsed with a working toggle.

- [ ] **Step 6: Commit the doc change (ask first)**

```bash
cd documentation && git add development/plans/2026-09-15-phone-onboarding-design.md
git commit -m "docs: correct the clamping round-trip in the phone onboarding spec

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review

**Spec coverage** — every section maps to a task: §1 step model → Tasks 2, 3, 8; §2 sequences → Tasks 2, 8; §3 components → Tasks 4 (indicator), 5 (defaults split), 6 (info-only), 7 (plan collapse), 8 (Welcome deletion), 9 (completion note); §4 backend → Task 1; §5 phone detection → Task 8, with the correction in Task 10. The testing section maps to the test files named in each task. No gaps.

**Type consistency** — `OnboardingStepId` is defined once in Task 2 and imported everywhere after. `resolveOnboardingResume` returns `stepId` (Task 3) and nothing later reads `stepIndex`. `setOnboardingResumeStep` takes `OnboardingStepId` in Task 3 and is called with `resume.stepId`. `StepIndicator`'s props (Task 4) match the call site in Task 8. `CompanyDefaultsStep`'s `onSaved`/`onBack` (Task 5) match Task 8. `CsvUploadStep`'s three new props (Task 6) match the merged-screen call in Task 8. `CompletionStep`'s `isPhone` (Task 9) matches Task 8.

**Known cross-task breakage** — Task 3 leaves `OnboardingPage.tsx` failing tsc until Task 8 rewires it. This is called out in both tasks' verification steps so an executor does not treat it as a regression and patch around it.
