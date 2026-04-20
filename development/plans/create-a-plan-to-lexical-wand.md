# Auth Screens Overhaul — Plan

## Context

The portal's authentication today lives in a single ~588-line [Login.tsx](portal/src/Login.tsx) that toggles login/signup via a mode flag and inlines forgot-password and resend-verification handlers. The mock at [AuthScreensV2/](AuthScreensV2/) introduces a polished 7-screen flow with cleaner separation, touched-state validation, dismissible banners, a password strength meter, and dedicated confirmation screens for verification and password reset.

Per user direction:
- **Adopt** the mock's information architecture, screen flow, copy, validation behavior, and password strength meter.
- **Keep** the portal's existing slate theme tokens in [theme.css](portal/src/styles/theme.css) and existing shadcn/ui components ([Button](portal/src/components/ui/button.tsx), [Input](portal/src/components/ui/input.tsx), [Card](portal/src/components/ui/card.tsx), [Alert](portal/src/components/ui/alert.tsx), [Label](portal/src/components/ui/label.tsx)) for primary buttons, inputs, cards, and accents.
- **Use the lavender background** from the mock (`#F3F1F8` / `#ECE8F4`) as the auth-page page background, scoped to auth routes only — not applied globally.
- **Split** into one route per screen so each step has its own URL.

No backend changes. All endpoints in [platform/routers/auth.py](platform/routers/auth.py) are reused as-is.

## Routes & Screens

Add to [App.tsx](portal/src/App.tsx) under the `LoginRoute` guard (so authenticated users redirect to `/dashboard`):

| Route | Page | Replaces / New |
|---|---|---|
| `/login` (and `/`) | `LoginPage` | Replaces Login mode in old file |
| `/signup` | `SignupPage` | Replaces Signup mode in old file |
| `/forgot-password` | `ForgotPasswordPage` | New (was inline button on Login) |
| `/forgot-password/sent` | `ForgotPasswordSentPage` | New |
| `/verify-email/sent` | `VerifyEmailSentPage` | New (was inline message) |
| `/verify-email/success` | `VerifyEmailSuccessPage` | New (handles `?oobCode=…&mode=verifyEmail` from Firebase verify link) |
| `/resend-verification` | `ResendVerificationPage` | New (was inline button) |

Existing `/signup` route already exists — extend the pattern for the other six. Invitation-link flow (`?invite=token&email=address` on `/signup`) must continue to work via [invitationFlow.ts](portal/src/lib/invitationFlow.ts).

## File Layout

```
portal/src/
  pages/auth/
    LoginPage.tsx
    SignupPage.tsx
    ForgotPasswordPage.tsx
    ForgotPasswordSentPage.tsx
    VerifyEmailSentPage.tsx
    VerifyEmailSuccessPage.tsx
    ResendVerificationPage.tsx
  components/auth/
    AuthShell.tsx           # min-h-screen lavender background + flex centered + Card wrapper + logo
    AuthHeader.tsx          # h1 title + optional subtitle
    BackToLoginLink.tsx     # ArrowLeft + "Back to sign in"
    PasswordField.tsx       # Input + Eye/EyeOff toggle button
    PasswordStrengthMeter.tsx
    TermsCheckbox.tsx       # Native styled checkbox + Label
  lib/auth/
    passwordStrength.ts     # ported scorePassword() heuristic from AuthScreensV2/components/Forms.jsx
    validation.ts           # email regex + helpers
```

After all seven pages route correctly, **delete [Login.tsx](portal/src/Login.tsx)** and update [App.tsx](portal/src/App.tsx) imports.

## Component Reuse

Use existing primitives — do not introduce new design language:

- **shadcn/ui**: `Button`, `Input`, `Label`, `Card` + `CardHeader/Title/Description/Content`, `Alert` (variant `destructive` for errors, default for info; if no info variant exists, use the default styling — confirm in [alert.tsx](portal/src/components/ui/alert.tsx) before relying on it).
- **lucide-react** (already installed): `Eye`, `EyeOff`, `ArrowLeft`, `CheckCircle2`, `Mail`, `AlertCircle`, `X`.
- **Logo**: continue using [3maples-logo-bottom.png](portal/src/assets/3maples-logo-bottom.png) — do **not** port the mock's custom SVG mark.
- **Inter font**: already loaded via [fonts.css](portal/src/styles/fonts.css).
- **Checkbox**: `@radix-ui/react-checkbox` is **not** installed. Use a styled native `<input type="checkbox">` inside `TermsCheckbox.tsx` with Tailwind classes (matches the rest of the portal's "no extra deps unless needed" stance). Add the radix package only if a future PR needs it elsewhere.

## What to Port from the Mock

From [AuthScreensV2/components/](AuthScreensV2/components/):

| From mock | Port how |
|---|---|
| Screen copy (titles, subtitles, button labels, banner messages) | Verbatim |
| Touched-state validation pattern (errors only after blur or submit) | As-is |
| Email regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` | Into `lib/auth/validation.ts` |
| `scorePassword()` heuristic (length 8/12, upper, lower, digit, symbol → 0–4 + label + hints) | Into `lib/auth/passwordStrength.ts` |
| 4-bar `StrengthMeter` visual | Into `PasswordStrengthMeter.tsx`, color the bars using existing theme tokens (`bg-destructive`, `bg-amber-500`, `bg-green-600`, `bg-muted`) — **not** the mock's custom hex colors |
| Password show/hide eye toggle | Into `PasswordField.tsx` |
| Dismissible banner pattern | Use shadcn/ui `Alert` + a close button |
| Resend-verification separate screen | New `ResendVerificationPage` |
| Screen-to-screen navigation links ("Back to sign in", "Sign in instead", "try a different email") | Use `<Link>` from `react-router-dom` |

**Skip from the mock**: maple-green accent, animated wave SVG backdrop, custom SVG logo, inline-style theming, the Tweaks dev panel.

**Lavender background implementation**: Add two CSS variables — `--auth-bg: #F3F1F8` and `--auth-bg-2: #ECE8F4` — to [theme.css](portal/src/styles/theme.css). `AuthShell.tsx` applies `background: var(--auth-bg)` (or a subtle radial gradient between the two values to mirror the mock). Keep the white shadcn/ui `Card` on top so the inner form still uses the existing slate-themed primitives. The lavender appears only behind auth pages because `AuthShell` is the only consumer.

## API Wiring (Reuse Existing)

All from [api/auth.ts](portal/src/api/auth.ts) and [firebase.ts](portal/src/firebase.ts):

- **Login**: `signInWithEmailAndPassword` → `authenticate(idToken)` → `setCurrentUser` + `setAuthenticatedSession` → `Navigate("/dashboard")`. Honor existing pending-invitation handling.
- **Signup**: `createUserWithEmailAndPassword` → `createPortalUser` → `sendVerificationEmailRequest` → `Navigate("/verify-email/sent", { state: { email } })`.
- **Forgot password**: `requestPasswordResetEmail(email)` → `Navigate("/forgot-password/sent", { state: { email } })`. Endpoint already returns a generic message (does not reveal if email exists).
- **Resend verification**: requires a signed-in Firebase user. Match the existing pattern in Login.tsx — `signInWithEmailAndPassword` with provided email+password, then `sendVerificationEmailRequest`, show success banner. (Tag the call with [transientAuthFlow.ts](portal/src/lib/transientAuthFlow.ts) so `App.tsx`'s `onIdTokenChanged` does not treat this as a real login.)
- **Verify email success**: read `oobCode` from query string → `applyActionCode(firebaseAuth, oobCode)` → render success state with "Go to sign in" button. Show error state if the code is invalid/expired.
- **Toast & error semantics**: keep the existing `pendingToastMessage` sessionStorage handoff used by Login.tsx so messages survive redirects.

## Routing Updates in App.tsx

Inside the existing `LoginRoute`-wrapped block in [App.tsx:151-168](portal/src/App.tsx#L151-L168), replace the single `<Login />` element with a nested `<Routes>` switch over the seven new pages, or — simpler — add seven sibling `<Route>` elements each rendered through `LoginRoute` so they all share the "redirect-to-/dashboard-if-authenticated" guard. Keep `/`, `/login`, `/signup` working as today.

## Testing

Vitest is currently configured with `environment: "node"` ([vite.config.js](portal/vite.config.js)) — no DOM. Per CLAUDE.md, run only related tests and let the user trigger the full suite.

- **Add unit tests** (run in node, no infra change):
  - `portal/tests/passwordStrength.test.ts` — score boundaries, hint output, label thresholds
  - `portal/tests/validation.test.ts` — email regex valid/invalid cases
- **Page-level component tests**: skipped for this PR. The existing repo has zero Login.tsx component tests, so this matches precedent. Note in the PR description that adding `jsdom` + `@testing-library/react` would unlock these and is a worthwhile follow-up.

Run after changes:
```bash
cd portal && npm test -- passwordStrength validation
cd portal && npm run lint
cd portal && npm run typecheck
```

## Verification (Manual)

```bash
cd portal && npm run dev
```

Walk every flow in a browser:

1. **Login happy path**: `/login` → valid creds → `/dashboard`.
2. **Login bad password**: dismissible error banner shown, no navigation.
3. **Signup happy path**: `/signup` → fill all fields → strength meter reaches ≥ 2 bars → terms checked → submit → `/verify-email/sent` shows the email entered.
4. **Signup duplicate email**: backend returns existing-email error → banner with "Sign in instead" link to `/login`.
5. **Forgot password**: `/login` → "Forgot password?" → `/forgot-password` → enter email → `/forgot-password/sent` showing the email.
6. **Verify email link**: open Firebase verification email, click link → lands on `/verify-email/success` with `oobCode` in URL → success state shown → "Go to sign in" → `/login`.
7. **Resend verification**: `/login` → "Didn't get verification email? Resend it" → `/resend-verification` → enter creds → success banner.
8. **Invitation flow**: visit `/signup?invite=TOKEN&email=foo@bar.com` → email pre-filled → signup completes → invitation acceptance still fires.
9. **Authenticated user visiting `/login`**: redirects to `/dashboard` (existing `LoginRoute` guard).
10. **Toast handoff**: trigger a flow that sets `pendingToastMessage` in sessionStorage (e.g., signup → redirected to verify-sent) and confirm the message renders on the destination page.

## Out of Scope

- Backend endpoint changes
- Theme/global color changes outside auth pages
- Adding `jsdom` + React Testing Library (recommended follow-up)
- Porting the mock's wave background, custom logo SVG, or Tweaks panel
- Replacing existing shadcn/ui primitives
