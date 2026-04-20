# Multi-Step Onboarding Flow

## Context

Currently, after email verification, new users see a modal dialog in `Login.tsx` to create their company, then go straight to the Dashboard. This plan replaces that modal with a full-page, 6-step onboarding experience that introduces the user to the app via "Maple" (the AI guide), collects company info, allows optional CSV data imports, and shows free plan details before landing on the Dashboard. The onboarding only shows once during initial account creation.

## Architecture Decisions

- **New route `/onboarding`** instead of inline in Login.tsx -- keeps Login.tsx manageable and enables proper browser navigation
- **Company creation happens at step 2** -- after that, `companyId` is available for CSV uploads in steps 3-5
- **Steps 3-5 are skippable** -- CSV import is optional; users can always do it later from the main app
- **State in React + sessionStorage** -- `currentStep` persists in sessionStorage to survive accidental refresh during the same session. If user refreshes after step 2 (company created), they'll land on Dashboard since `user.company` is now set -- this is acceptable since remaining steps are optional
- **No backend changes needed** -- all endpoints already exist (`/auth/company-onboarding`, `/contacts/upload`, `/properties/upload`, `/materials/upload`)

## Implementation Steps

### Design & Theme Consistency

All onboarding screens use the app's existing theme variables to maintain a cohesive look:
- Background: `bg-background` (`#f8f9fa`)
- Cards: `bg-card` (`#ffffff`) with `border-border` (`#e2e8f0`)
- Primary actions: `bg-primary text-primary-foreground` (slate `#334155` / white)
- Secondary actions ("Setup Later"): `text-muted-foreground` (`#64748b`) styled as text buttons
- Step indicator: `bg-primary` for active/completed dots, `bg-muted` (`#f1f5f9`) for inactive
- Headings: `text-foreground` (`#1e293b`)
- Body text: `text-muted-foreground` (`#64748b`)
- Maple's speech: styled in a subtle card with a `Sparkles` icon accent, using `bg-secondary` background
- Input fields, selects, labels: match existing form styling from the app (same as Login.tsx and SettingsPage)
- Consistent use of `rounded-lg` (`--radius: 0.5rem`) for cards and buttons

### 1. Create `portal/src/pages/OnboardingPage.tsx`

Main orchestrator component with 6 steps:
- Manages `currentStep` state (0-5), persisted to `sessionStorage`
- Full-page layout: `min-h-screen bg-background` with centered content area (`max-w-3xl`)
- Step progress indicator at the top (horizontal dots/bar)
- Renders the active step component
- Shared Next/Back/Skip footer navigation
- After step 2 completes: stores `companyId` in state + calls `setCompanyId()` and `setAuthenticatedSession()` so CSV upload APIs work
- After step 6 "Go to Dashboard": `navigate("/dashboard", { replace: true })`

### 2. Create step components in `portal/src/components/onboarding/`

**`StepIndicator.tsx`** -- Horizontal progress dots showing current step. Uses `bg-primary` for completed/active, `bg-muted` for inactive.

**`WelcomeStep.tsx`** (Screen 1)
- 3maples logo (`3maples-logo-transparent.png`)
- Maple intro with `Sparkles` Lucide icon: "Welcome to 3Maples. I am Maple, your AI guide to using the app."
- Brief overview of what setup covers
- "Get Started" button

**`CompanyStep.tsx`** (Screen 2)
- Extract the company form from [Login.tsx:853-1150](portal/src/Login.tsx#L853-L1150) (the current modal dialog)
- Fields: Company Name, Industry, Email, Phone, Website, Street (with address autocomplete), City, Province/State, Postal/Zip, Country
- Company percentages with updated defaults per requirements:
  - Profile Margin: `15.0` (was `0.0`)
  - Overhead Allocation: `20.0` (was `0.0`)
  - Material Markup: `10.0` (new field)
  - Labor Burden: `20.0` (new field)
- Bootstrap checkboxes (standard materials, standard labour roles)
- Calls existing `completeCompanyOnboarding()` from [api/auth.ts](portal/src/api/auth.ts)
- On success: passes `companyId` back to parent via `onCompanyCreated` callback

**`CsvUploadStep.tsx`** -- Reusable for screens 3, 4, 5
- Props: `title`, `description`, `introText`, `sampleCsvUrl`, `onUpload(file) => Promise`, `showSiteOneConnect?`
- Each screen has a proper introduction explaining what the resource is and how it's used in the app:
  - **Contacts (Screen 3)**: Explains that contacts are the people/companies you work with -- clients, vendors, subcontractors. Import existing contacts to quickly associate them with estimates and properties.
  - **Properties (Screen 4)**: Explains that properties are the job sites or locations where work is performed. Import your property list to streamline estimate creation.
  - **Materials (Screen 5)**: Explains that materials are the products and supplies used in your jobs. Import your material catalog to build estimates faster with accurate pricing.
- Download sample CSV link
- File picker + upload button (reuse pattern from [ContactsPage.tsx:1010-1030](portal/src/pages/ContactsPage.tsx#L1010-L1030))
- Upload result display (created/updated/errors counts)
- For Materials step: "Connect with SiteOne" button (disabled, "Coming Soon" badge)
- "Setup Later" button (instead of "Skip") and "Next" button (after successful upload)

**`CompletionStep.tsx`** (Screen 6)
- Maple message with `Sparkles` icon: "Your setup is complete! You're ready to start using 3Maples."
- Explain they are on the **Free Forever Plan** with two limitations:
  - Up to 5 team members
  - Up to 25 new estimates per month
- "Go to Dashboard" button

### 3. Create sample CSV templates in `portal/public/templates/`

Based on existing backend upload endpoint requirements:

**`contacts-sample.csv`**: `first_name,last_name,phone,email,street,city,prov_state,postal_zip,country,role,notes`

**`properties-sample.csv`**: `name,street,city,prov_state,postal_zip,country,notes`

**`materials-sample.csv`**: `name,description,category,units,size,cost,price`

### 4. Extract shared constants to `portal/src/constants/addressOptions.ts`

Move `countryOptions`, `canadaProvinceOptions`, `usStateOptions` from Login.tsx to a shared file (also used by property forms).

### 5. Modify `portal/src/App.tsx`

- Import `OnboardingPage`
- Add `OnboardingRoute` guard component: requires Firebase auth but no company; redirects to `/dashboard` if already onboarded, to `/` if not logged in
- Add route: `<Route path="/onboarding" element={<OnboardingRoute authReady={authReady} />} />`

### 6. Modify `portal/src/Login.tsx`

- At [line 340-348](portal/src/Login.tsx#L340-L348): replace `setShowCompanyDialog(true)` with `navigate("/onboarding", { replace: true, state: { email } })`
- Remove all company dialog state, handlers, and JSX (~300 lines):
  - `showCompanyDialog`, `companyForm`, `companyErrorMessage`, `isCompanySubmitting` states
  - `handleCompanySubmit`, `handleCompanyFieldChange` functions
  - Address autocomplete effect for company dialog
  - Company dialog JSX block (lines 853-1150)
  - `getEmptyCompanyForm`, `CompanyFormData` type
  - Move country/province/state arrays to shared constants

## Files Summary

| File | Action |
|------|--------|
| `portal/src/pages/OnboardingPage.tsx` | Create |
| `portal/src/components/onboarding/StepIndicator.tsx` | Create |
| `portal/src/components/onboarding/WelcomeStep.tsx` | Create |
| `portal/src/components/onboarding/CompanyStep.tsx` | Create |
| `portal/src/components/onboarding/CsvUploadStep.tsx` | Create |
| `portal/src/components/onboarding/CompletionStep.tsx` | Create |
| `portal/src/constants/addressOptions.ts` | Create |
| `portal/public/templates/contacts-sample.csv` | Create |
| `portal/public/templates/properties-sample.csv` | Create |
| `portal/public/templates/materials-sample.csv` | Create |
| `portal/src/App.tsx` | Modify |
| `portal/src/Login.tsx` | Modify |

## Verification

1. Sign up with a new account, verify email, log in -- should redirect to `/onboarding` (not show the old modal)
2. Step 1: Welcome screen renders with Maple intro, click "Get Started"
3. Step 2: Fill company form, submit -- company created via API, step advances
4. Steps 3-5: Can download sample CSVs, upload CSVs, or skip each step
5. Step 6: See free plan details, click "Go to Dashboard" -- lands on Dashboard
6. Refresh at any point: before step 2, returns to onboarding; after step 2, lands on Dashboard
7. Subsequent logins: go directly to Dashboard (never see onboarding again)
8. Invitation flow: still works as before (bypasses onboarding entirely)
9. Run `cd portal && npm test` for related test files
