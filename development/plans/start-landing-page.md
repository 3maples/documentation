# `/start` Paid-Traffic Landing Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a standalone, `noindex` landing page at `https://3maples.com/start` that captures an email address, fires the Meta `Lead` and GA4 `generate_lead` conversions, records the lead in Brevo, and hands the visitor to `app.3maples.ai/signup` with the email prefilled.

**Architecture:** Three independent deliverables across three repos, in dependency order. (1) **Portal** gains a pure `landingPrefill` module so `/signup?email=` actually prefills — today that param is silently dropped. (2) **Website functions** gains a `lead` Cloud Function behind an `/api/lead` Hosting rewrite, reusing the existing Brevo contact-sync pattern. (3) **Website** gains `start.html`, a self-contained page (spec Option B) wired into the Vite multi-page build as a standalone entry — deliberately *not* in `PAGE_META`, so it stays out of the sitemap and out of the `seo-head` assertions, exactly like `404.html`.

**Tech Stack:** Static HTML + hand-written CSS (Vite 6 multi-page build, Firebase Hosting `cleanUrls`); Firebase Functions v2 (Node 20, ESM); React 19 + react-router (portal); vitest everywhere.

**Spec:** [`start-landing-page-spec.md`](start-landing-page-spec.md) — Ron St.Pierre, 2026-09-02. Copy and design are final; do not rewrite them.

---

## Global Constraints

- **URL is `/start`.** It is *not* the target of any device-based redirect. Ads link to it directly. Wiring a mobile redirect at this URL would send Googlebot Smartphone to a `noindex` page and de-index the homepage under mobile-first indexing.
- **The repo is the source of truth for design values.** Where the spec and the live site disagree, the site wins. Do **not** modify `index.html`, `pricing.html`, `faq.html`, `privacy.html`, or `terms.html`.
- **Option B (standalone) only.** Option A is not buildable — the site has no shared stylesheet; every page carries its own inline `<style>` with its own `:root`.
- **The redirect to signup must fail open.** If `/api/lead` errors or is slow, the visitor still reaches signup. Never trade a signup for a lead record.
- **Copy is final and verbatim.** Free-plan facts, everywhere they appear: **3 users, 20 estimates a month, 50 tasks, no credit card, no contract.**
- **Banned from the page** (spec §10): margin or markup claims (bug `3M-EST-001`), any claim that estimates send from the app, Spanish exclusivity claims, ROI or "make more money" claims, stock photography, redrawn or AI-generated logos, cookie banner, chat widget, video embed, carousel, animation library.
- **No images above the fold.** Hero is type and color only.
- **Analytics IDs are never hardcoded.** Use the repo's build-time templating (`%VITE_GA_MEASUREMENT_ID%`, `%VITE_META_PIXEL_ID%`) *and* the hostname allowlists from `index.html`. Hardcoding makes the dev deploy fire the production pixel — the exact bug those allowlists were added to fix.
- **TDD is mandatory** (CLAUDE.md). Failing test first, then implementation.
- **Gates:** portal — `npm test` + `npm run typecheck`; website — `npm test` + `npm run build`. Commit and push each need fresh explicit approval.

## Open configuration items (block deploy, not build)

These do not block writing code. They block pointing ad spend at the page.

1. ~~**Brevo list `Leads - Not Signed Up` must exist, and its numeric ID must be set** as the `BREVO_LEADS_LIST_ID` param.~~ — **RESOLVED 2026-09-04.** The list is **20**, now a plain constant in `functions/index.js` beside `BREVO_CONTACT_LIST_ID = 6` / `BREVO_PRELAUNCH_LIST_ID = 7`.

   The `defineString` param this originally used was **wrong for this pipeline** and was removed: GitHub Actions deploys the functions (`--only hosting:website,functions`), and `.gitignore`'s `.env` / `.env.*` patterns match at any depth, so `functions/.env` never reaches CI. The param would have resolved to empty there and skipped every lead in silence. A list ID is not a secret — the file's own comment says so — so a constant is both simpler and visible in review.

   (The value also sits in `platform/.env.local:54`, where it is inert: that is a different service, and `platform/config.py` declares no `brevo_leads_list_id` setting, so Pydantic drops it. Safe to delete that line.)
2. ~~**Confirm the GitHub Actions variable `VITE_META_PIXEL_ID` equals `1027059673405942`**~~ — **RESOLVED 2026-09-04.** Verified via `gh variable list --repo 3maples/website --env production`: it is environment-scoped (repo-level vars are empty) and reads `1027059673405942`, matching spec §8. Note it is deliberately **unset on the `dev` environment**, so the dev deploy bakes an empty value and the `/^\d+$/` guard suppresses the pixel — which is why acceptance test #7 can only run against `3maples.com`.

   reCAPTCHA domains need no action: `VITE_RECAPTCHA_V3_SITE_KEY` is the same key in both environments and is already serving the contact modal and Maple widget on `3maples.com`, so the allowed-domains list already covers this origin.
3. ~~**Pre-existing drift, flagged not fixed:** `functions/index.js` `ALLOWED_ORIGINS` names `3maples.ai`, not `3maples.com`.~~ — **FIXED 2026-09-04** as code-review finding #11: `https://3maples.com` and `https://www.3maples.com` were added alongside the `.ai` pair, which is kept so anything still pointing there keeps working.
4. **NEW — reCAPTCHA gate on `/api/lead`** (code-review finding #1). The Brevo *write* now requires a v3 verdict; the visitor is never blocked. Nothing to configure — `VITE_RECAPTCHA_V3_SITE_KEY` and the `RECAPTCHA_V3_SECRET` Functions secret are already set in both environments. Leads arriving without a usable token are still recorded, tagged `SOURCE: website-start-landing-unverified`, so watch that segment after launch: a large share means the token supply is failing, not that traffic is fraudulent.

---

## File Structure

| File | Repo | Responsibility |
|---|---|---|
| `src/lib/landingPrefill.ts` | portal | Pure: read + validate `?email=`, and strip it from the query string. No React, no window. |
| `tests/landingPrefill.test.ts` | portal | Unit tests for the above (node env). |
| `src/pages/auth/SignupPage.tsx` | portal | Wire the prefill effect in, declared *before* the Meta Pixel effect. |
| `functions/index.js` | website | Add `syncLeadToBrevo()` + the `lead` onRequest export. |
| `functions/lead.test.js` | website | Unit tests for the handler (vitest, module-mocked). |
| `functions/{brevoContactSync,joinWaitlist,corsConfig}.test.js` | website | Refactor: capture handlers by export, not by last registration. Required before a second `onRequest` can exist. |
| `firebase.json` | website | `/api/lead` → `lead` function rewrite. |
| `start.html` | website | The page. Self-contained: tokens, CSS, markup, form script. |
| `vite.config.ts` | website | Standalone rollup entry + dev clean-URL mapping. |
| `src/content/__tests__/start-page.test.ts` | website | Pin the page's contracts: noindex, real asset paths, guarded analytics, token parity with `index.html`, sitemap exclusion. |

---

## Deviations from spec §9, and why

Every one of these is a repo-verified mismatch or a defect. Apply all of them.

| # | Spec says | Change to | Why |
|---|---|---|---|
| D1 | `<img src="/assets/3maples-logo-horizontal.png" width="26" height="26">` | `<img src="/3Maples-logo-horizontal-black.png" alt="3Maples" width="1174" height="170" style="height:20px;width:auto;display:block">` | The `/assets/` path does not exist. The real file is in `public/`, served at root, and is 1174×170 — `index.html:858` renders it at `height:20px;width:auto`. Spec's dimensions would squash it. Acceptance test #3 fails as written. |
| D2 | `h2{letter-spacing:-.025em}` | `-0.03em` | `index.html:119`. Acceptance test #6 compares side by side with the homepage. |
| D3 | Hardcoded `G-XXXXXXX` (×2) and `fbq('init','1027059673405942')`, pixel at end of `<body>` | The two guarded snippets copied verbatim from `index.html:6-50`, in `<head>` | Repo pattern: build-time templating plus `GA_HOSTS` / `PIXEL_HOSTS` allowlists. Prevents the dev deploy at `maples-website-dev.web.app` firing the production pixel. Prod GA4 is `G-G6JJ1W36JH` via `.env.production`; do not inline it. |
| D4 | `<form class="signup" id="f" novalidate>` | add `action="https://app.3maples.ai/signup" method="get"` | With JS disabled the submit handler never binds and `novalidate` kills native validation, so submitting silently reloads the page and loses the visitor. With `action`/`method=get` the no-JS path degrades to a real navigation carrying `?email=`. The JS handler still calls `preventDefault()`, so behavior with JS is unchanged. |
| D5 | Footer is `&copy; 2026 3Maples` | add a `/privacy` link | The page collects PII and runs the Meta Pixel. §10 does not ban a footer link. |
| D6 | `btn.disabled=true` is never reversed | leave `disabled`, but re-enable in the `finish` guard's failure path — see Task 3 Step 3 | If the redirect is blocked the visitor is left with a dead "One second" button. |
| D7 | No favicon or manifest links | add the four links from `index.html:71-74` | Consistency; costs nothing. |
| D8 | Fonts: "self-host as woff2 if the site already does" | keep the Google Fonts link | `src/styles/fonts.css` is 0 bytes; `index.html:77` uses the Google Fonts `<link>`. Answers spec §13 Q1: **not self-hosted**. Keep spec §9's non-blocking `media="print" onload` form — it is better for the LCP gate than `index.html`'s render-blocking version. |

**Not changed, deliberately:** the `.hero-grid` breakpoint stays at `960px` even though §3 lists the site's breakpoints as 560/720/820/900/1100. It is the spec's design intent and changing it would alter the layout the CMO signed off on.

**Not needed under Option B:** the `--font` undefined bug, the `.btn` transparent-background bug, and the `.eyebrow::before` favicon image were all Option A hazards. Option B declares its own `--font`, its own `.btn` with `background:var(--accent)`, and an `.eyebrow` with no `::before`. Verify each survives into `start.html` rather than assuming.

---

## Task 1: Portal — `?email=` prefill on `/signup`

Today `SignupPage` reads email only via `parseInvitationLink()`, which returns `null` unless `?invite=` is present (`src/lib/invitationFlow.ts:24`). A bare `?email=` is dropped, so spec acceptance test #9 cannot pass. This task lands independently of the rest.

**Files:**
- Create: `portal/src/lib/landingPrefill.ts`
- Create: `portal/tests/landingPrefill.test.ts`
- Modify: `portal/src/pages/auth/SignupPage.tsx:29-33` (imports), `:72-77` (effect order)

**Interfaces:**
- Consumes: `isValidEmail`, `normalizeEmail` from `@/lib/auth/validation`
- Produces: `parseLandingEmail(search: string | null | undefined): string | null`, `stripLandingEmail(search: string | null | undefined): string`

- [x] **Step 1: Write the failing test**

Create `portal/tests/landingPrefill.test.ts`:

```ts
/**
 * The /start landing page hands off to /signup?email=<address>&utm_*=...
 *
 * Two jobs, both pure so they can be tested without rendering the page:
 * read the address, and get it back out of the URL. The second matters as
 * much as the first — SignupPage initialises the Meta Pixel, whose PageView
 * beacon carries `page_location`. An email left in the query string is PII
 * shipped to Meta.
 */
import { describe, test, expect } from "vitest";

import { parseLandingEmail, stripLandingEmail } from "../src/lib/landingPrefill";

describe("parseLandingEmail", () => {
  test("returns the normalized address", () => {
    expect(parseLandingEmail("?email=Foo%40Bar.COM")).toBe("foo@bar.com");
  });

  test("returns null when there is no email param", () => {
    expect(parseLandingEmail("?utm_source=meta")).toBeNull();
  });

  test("returns null for an empty or malformed address", () => {
    expect(parseLandingEmail("?email=")).toBeNull();
    expect(parseLandingEmail("?email=nope")).toBeNull();
  });

  test("defers to the invitation flow when invite is present", () => {
    // parseInvitationLink already owns that URL shape, including its own
    // banner and its own history rewrite. Two handlers on one param races.
    expect(parseLandingEmail("?invite=tok&email=foo@bar.com")).toBeNull();
  });

  test("tolerates null and undefined", () => {
    expect(parseLandingEmail(null)).toBeNull();
    expect(parseLandingEmail(undefined)).toBeNull();
  });
});

describe("stripLandingEmail", () => {
  test("removes email and keeps every other param", () => {
    expect(stripLandingEmail("?utm_source=meta&email=foo@bar.com&utm_content=you-talk")).toBe(
      "?utm_source=meta&utm_content=you-talk",
    );
  });

  test("returns an empty string when email was the only param", () => {
    expect(stripLandingEmail("?email=foo@bar.com")).toBe("");
  });

  test("is a no-op when there is no email param", () => {
    expect(stripLandingEmail("?utm_source=meta")).toBe("?utm_source=meta");
  });
});
```

- [x] **Step 2: Run test to verify it fails**

```bash
cd portal && npm test -- landingPrefill
```

Expected: FAIL — `Failed to resolve import "../src/lib/landingPrefill"`.

- [x] **Step 3: Write minimal implementation**

Create `portal/src/lib/landingPrefill.ts`:

```ts
/**
 * Email prefill for visitors arriving from the /start landing page.
 *
 * /start captures the address on 3maples.com (where the Meta pixel works) and
 * hands off to /signup?email=<address> with the campaign's UTMs intact. Without
 * this module that param is dropped: `parseInvitationLink` only reads `email`
 * when `invite` is also present, so a plain landing-page handoff prefilled
 * nothing and the visitor retyped their address.
 *
 * `stripLandingEmail` is not housekeeping. SignupPage initialises the Meta
 * Pixel, and its PageView beacon reports `page_location` — an address left in
 * the query string is PII sent to Meta. Strip before the pixel loads.
 */
import { isValidEmail, normalizeEmail } from "@/lib/auth/validation";

/** The address from `?email=`, normalized — or null if absent, invalid, or an invitation. */
export function parseLandingEmail(search: string | null | undefined): string | null {
  const params = new URLSearchParams(String(search || ""));
  // The invitation flow owns any URL carrying `invite`, banner and all.
  if (params.get("invite")) return null;
  const email = normalizeEmail(params.get("email") || "");
  if (!email || !isValidEmail(email)) return null;
  return email;
}

/** The same query string with `email` removed, `?`-prefixed, or "" if nothing is left. */
export function stripLandingEmail(search: string | null | undefined): string {
  const params = new URLSearchParams(String(search || ""));
  params.delete("email");
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}
```

- [x] **Step 4: Run test to verify it passes**

```bash
cd portal && npm test -- landingPrefill
```

Expected: PASS, 8 tests.

- [x] **Step 5: Wire into SignupPage**

In `portal/src/pages/auth/SignupPage.tsx`, add to the import block that currently pulls from `@/lib/invitationFlow` (line 29):

```ts
import { parseLandingEmail, stripLandingEmail } from "@/lib/landingPrefill";
```

Then replace the Meta Pixel effect at lines 72-76 with the prefill effect *followed by* the pixel effect. Order is load-bearing — effects run in declaration order, so the strip must be declared first:

```tsx
  // Landing-page handoff: /start sends the visitor here as
  // /signup?email=<address>&utm_*=... Prefill the field, then take the address
  // back out of the URL.
  //
  // Declared BEFORE the Meta Pixel effect on purpose: effects run in
  // declaration order, and the pixel's PageView beacon reports
  // `page_location`. Reorder these and the address ships to Meta.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const landingEmail = parseLandingEmail(window.location.search);
    if (!landingEmail) return;
    setEmail((current) => current || landingEmail);
    const nextSearch = stripLandingEmail(window.location.search);
    window.history.replaceState(
      {},
      document.title,
      `${window.location.pathname}${nextSearch}${window.location.hash || ""}`,
    );
  }, []);

  // Meta Pixel loads only on the signup flow (ad-conversion tracking) — see
  // src/lib/metaPixel.ts. No-op unless VITE_META_PIXEL_ID is baked in.
  useEffect(() => {
    initMetaPixel();
  }, []);
```

- [x] **Step 6: Verify the gates**

```bash
cd portal && npm test -- landingPrefill && npm run typecheck
```

Expected: tests PASS, `tsc --noEmit` clean.

- [x] **Step 7: Manual check**

```bash
cd portal && npm run dev
```

Open `/signup?email=Foo%40Bar.com&utm_source=meta`. Expected: email field shows `foo@bar.com`; the address bar reads `/signup?utm_source=meta`; no invitation banner.

- [x] **Step 8: Commit** (ask for approval first)

```bash
cd portal && git add src/lib/landingPrefill.ts tests/landingPrefill.test.ts src/pages/auth/SignupPage.tsx
git commit -m "$(cat <<'EOF'
feat: prefill signup email from the /start landing page handoff

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Website functions — `POST /api/lead`

**Files:**
- Modify: `website/functions/brevoContactSync.test.js`, `joinWaitlist.test.js`, `corsConfig.test.js` (Step 1 — required refactor, see below)
- Modify: `website/functions/index.js` (add a param, a sync helper, and the `lead` export)
- Create: `website/functions/lead.test.js`
- Modify: `website/firebase.json` (rewrite)

**Blocking prerequisite — the existing tests break the moment a second function exists.** All three current test files mock `onRequest` into a *singleton*:

```js
let capturedHandler = null;
vi.mock('firebase-functions/v2/https', () => ({
  onRequest: vi.fn((_config, handler) => { capturedHandler = handler; return {...}; }),
}));
```

`index.js` registers `contact` today, so the singleton happens to hold the right handler. Add `export const lead = onRequest(...)` and the last registration wins: `brevoContactSync.test.js` and `joinWaitlist.test.js` would run all of their cases against the *lead* handler, and `corsConfig.test.js` would assert against lead's config while claiming to test contact. Separately, all three mock `firebase-functions/params` with `defineSecret` only — the moment `index.js` calls `defineString`, every one of them throws `defineString is not a function` at import.

Step 1 fixes this first, as a pure refactor with no behavior change: the mock returns the handler, so each export *is* its own handler and registration order stops mattering.

**Interfaces:**
- Consumes: existing module constants `BREVO_API_KEY`, `ALLOWED_ORIGINS`, `BREVO_CONTACTS_URL`, `BREVO_FETCH_TIMEOUT_MS`, `EMAIL_RE`
- Produces: `export const lead` — an `onRequest` handler accepting `{ email: string, query: string, page: string }` and returning `204` on any well-formed request

**Design notes:**
- **Always 2xx for a well-formed POST**, and never await Brevo before responding. The client redirects after 1200ms regardless (spec §8); a slow Brevo call must not eat that budget.
- **Fail open on an unset list ID.** `defineString('BREVO_LEADS_LIST_ID')` with no default: unset logs a warning and skips the sync. A wrong default would silently write leads into the contact list.
- **Malformed input still gets 204.** The spec forbids validation that blocks the response. Drop the record, keep the status.
- **Rate limiting is deliberately not in this task.** It is an unauthenticated write into the marketing CRM and should be capped, but Firebase Functions v2 has no built-in limiter and the right fix (Firestore counter, or App Check) is its own decision. Logged as a follow-up below rather than half-built here.

- [x] **Step 1: Make the existing function tests registration-order-independent**

In **each** of `brevoContactSync.test.js`, `joinWaitlist.test.js`, and `corsConfig.test.js`, replace the `firebase-functions/v2/https` mock with one that returns the handler and hangs the config off it:

```js
// Return the handler itself, so `index.js`'s exports ARE the handlers and it
// no longer matters how many functions the module registers or in what order.
// The config rides along on the function object for corsConfig.test.js.
vi.mock('firebase-functions/v2/https', () => ({
  onRequest: vi.fn((config, handler) => {
    handler.__config = config;
    return handler;
  }),
}));
```

Add `defineString` to the `firebase-functions/params` mock in **all three** files, alongside the existing `defineSecret`:

```js
  defineString: vi.fn((name) => ({
    __stringName: name,
    value: vi.fn(() => stringValues[name] ?? ''),
  })),
```

…backed by a `const stringValues = {};` declared next to the existing `secretValues` map in each file.

Then in `brevoContactSync.test.js` and `joinWaitlist.test.js`: change `await import('./index.js');` to `const { contact } = await import('./index.js');` (hoisting it to module scope or a `beforeEach` as each file already does for `capturedHandler`), delete the `let capturedHandler = null;` declaration, and replace every `capturedHandler(` call with `contact(`.

In `corsConfig.test.js`: delete `let capturedConfig = null;` and its reset, change the import line to `const { contact } = await import('./index.js');`, and replace every `capturedConfig.` with `contact.__config.`.

- [x] **Step 2: Run the existing tests to confirm the refactor changed nothing**

```bash
cd website && npm test -- functions/
```

Expected: PASS, same count as before the edit. This is a pure refactor — a failure here means the rewrite is wrong, not that behavior changed.

- [x] **Step 3: Write the failing test**

Create `website/functions/lead.test.js`:

```js
/**
 * POST /api/lead — the /start landing page's capture endpoint.
 *
 * The contract that matters is the one the page depends on: respond fast and
 * always, and never let Brevo hold up the response. The page redirects to
 * signup 1200ms after submit no matter what comes back, so a handler that
 * awaits a slow CRM is a handler that costs signups.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('firebase-functions/v2/https', () => ({
  onRequest: vi.fn((config, handler) => {
    handler.__config = config;
    return handler;
  }),
}));

const secretValues = { BREVO_API_KEY: 'test-brevo-key' };
const stringValues = { BREVO_LEADS_LIST_ID: '8' };
vi.mock('firebase-functions/params', () => ({
  defineSecret: vi.fn((name) => ({
    __secretName: name,
    value: vi.fn(() => secretValues[name] ?? ''),
  })),
  defineString: vi.fn((name) => ({
    __stringName: name,
    value: vi.fn(() => stringValues[name] ?? ''),
  })),
}));

vi.mock('nodemailer', () => ({
  default: { createTransport: vi.fn(() => ({ sendMail: vi.fn(async () => ({})) })) },
}));

function mockRes() {
  return {
    statusCode: null,
    body: undefined,
    status(code) { this.statusCode = code; return this; },
    json(payload) { this.body = payload; return this; },
    send(payload) { this.body = payload; return this; },
    end() { return this; },
  };
}

async function loadLead() {
  vi.resetModules();
  const { lead } = await import('./index.js');
  return lead;
}

describe('POST /api/lead', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stringValues.BREVO_LEADS_LIST_ID = '8';
    global.fetch = vi.fn(async () => ({ ok: true, text: async () => '' }));
  });

  it('rejects anything that is not a POST', async () => {
    const lead = await loadLead();
    const res = mockRes();
    await lead({ method: 'GET', body: {} }, res);
    expect(res.statusCode).toBe(405);
  });

  it('returns 204 and upserts the contact onto the leads list', async () => {
    const lead = await loadLead();
    const res = mockRes();
    await lead(
      { method: 'POST', body: { email: 'Foo@Bar.com', query: 'utm_source=meta', page: '/start' } },
      res,
    );
    expect(res.statusCode).toBe(204);
    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = global.fetch.mock.calls[0];
    expect(url).toBe('https://api.brevo.com/v3/contacts');
    const sent = JSON.parse(init.body);
    expect(sent.email).toBe('foo@bar.com');
    expect(sent.listIds).toEqual([8]);
    expect(sent.updateEnabled).toBe(true);
    expect(sent.attributes.SOURCE).toBe('website-start-landing');
    // Pins the attribute set exactly. Brevo 4xx's on an unknown attribute name
    // and this sync is fail-open, so an attribute added here without being
    // created in Brevo first would drop every lead in silence.
    expect(Object.keys(sent.attributes).sort()).toEqual(['SOURCE', 'SUBMITTED_AT']);
  });

  it('still returns 204 when the address is malformed, and writes nothing', async () => {
    // The spec forbids validation that blocks the response — the page redirects
    // regardless. Drop the record, keep the status.
    const lead = await loadLead();
    const res = mockRes();
    await lead({ method: 'POST', body: { email: 'nope', query: '', page: '/start' } }, res);
    expect(res.statusCode).toBe(204);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('still returns 204 when the list ID is unconfigured, and writes nothing', async () => {
    // Failing open beats writing leads into the wrong Brevo list.
    stringValues.BREVO_LEADS_LIST_ID = '';
    const lead = await loadLead();
    const res = mockRes();
    await lead(
      { method: 'POST', body: { email: 'foo@bar.com', query: '', page: '/start' } },
      res,
    );
    expect(res.statusCode).toBe(204);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('still returns 204 when Brevo throws', async () => {
    global.fetch = vi.fn(async () => { throw new Error('brevo down'); });
    const lead = await loadLead();
    const res = mockRes();
    await lead(
      { method: 'POST', body: { email: 'foo@bar.com', query: '', page: '/start' } },
      res,
    );
    expect(res.statusCode).toBe(204);
  });
});
```

- [x] **Step 4: Run test to verify it fails**

```bash
cd website && npm test -- functions/lead.test.js
```

Expected: FAIL — `lead` is not exported from `index.js`.

- [x] **Step 5: Write minimal implementation**

In `website/functions/index.js`, extend the params import (line 2):

```js
import { defineSecret, defineString } from 'firebase-functions/params';
```

Add below the existing Brevo list constants (after `const BREVO_PRELAUNCH_LIST_ID = 7;`):

```js
// The /start landing page's list ("Leads - Not Signed Up"). Unlike the two
// above this is NOT hardcoded: it did not exist when this file was written, and
// a wrong guess writes paid-campaign leads into the contact list. Unset means
// skip the sync — see syncLeadToBrevo.
const BREVO_LEADS_LIST_ID = defineString('BREVO_LEADS_LIST_ID');
```

Add the sync helper next to `syncContactToBrevo`:

```js
/**
 * Upsert a /start landing-page lead onto the leads list.
 *
 * Never awaited by the request path. The page redirects to signup 1200ms after
 * submit whatever happens here, so every failure is logged and swallowed —
 * we never trade a signup for a lead record.
 */
async function syncLeadToBrevo({ apiKey, listId, email }) {
  if (!apiKey) {
    console.warn('BREVO_API_KEY not configured — skipping lead sync.');
    return;
  }
  if (!listId) {
    console.warn('BREVO_LEADS_LIST_ID not configured — skipping lead sync.');
    return;
  }

  const body = JSON.stringify({
    email,
    // ONLY attributes this Brevo account already knows about. Brevo rejects an
    // upsert carrying an unknown attribute name, and this sync is fail-open —
    // so inventing one here drops every lead silently, with nothing to see but
    // a line in the Functions log. SOURCE and SUBMITTED_AT are already written
    // by the contact form, so both exist. Adding a new attribute means creating
    // it in Brevo FIRST.
    //
    // Campaign attribution deliberately lives in GA4 and Meta, which attribute
    // the generate_lead / Lead conversion to the ad themselves. Brevo does not
    // need a second copy, and the `query` the page posts is not persisted.
    attributes: {
      SOURCE: 'website-start-landing',
      SUBMITTED_AT: new Date().toISOString(),
    },
    listIds: [listId],
    updateEnabled: true,
  });

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), BREVO_FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(BREVO_CONTACTS_URL, {
      method: 'POST',
      headers: {
        'api-key': apiKey,
        'content-type': 'application/json',
        'accept': 'application/json',
      },
      body,
      signal: controller.signal,
    });
    if (!response.ok) {
      const errBody = await response.text().catch(() => '');
      console.warn('Brevo lead sync non-2xx response', {
        status: response.status,
        body: errBody.slice(0, 500),
      });
    }
  } catch (err) {
    if (err?.name === 'AbortError') {
      console.warn('Brevo lead sync timed out', { timeoutMs: BREVO_FETCH_TIMEOUT_MS });
    } else {
      console.warn('Brevo lead sync threw', { message: err?.message });
    }
  } finally {
    clearTimeout(timeoutId);
  }
}
```

Add the export at the end of the file:

```js
/**
 * POST /api/lead — email capture for the /start landing page.
 *
 * No reCAPTCHA, unlike `contact`: the spec forbids anything that could block or
 * slow the response, because the page redirects to signup on a 1200ms timer and
 * a blocked response is a lost signup. Malformed input therefore still gets a
 * 204 — we drop the record, not the visitor.
 */
export const lead = onRequest(
  {
    secrets: [BREVO_API_KEY],
    cors: ALLOWED_ORIGINS,
    region: 'us-central1',
    memory: '256MiB',
    timeoutSeconds: 15,
  },
  async (req, res) => {
    if (req.method !== 'POST') {
      res.status(405).json({ error: 'Method not allowed' });
      return;
    }

    // The page posts { email, query, page } per spec §8. Only `email` is
    // persisted — see the attribute note in syncLeadToBrevo.
    const { email } = req.body || {};
    const normalized = String(email || '').trim().toLowerCase();
    const listId = Number.parseInt(BREVO_LEADS_LIST_ID.value(), 10);

    if (EMAIL_RE.test(normalized)) {
      await syncLeadToBrevo({
        apiKey: BREVO_API_KEY.value(),
        listId: Number.isFinite(listId) && listId > 0 ? listId : null,
        email: normalized,
      });
    } else {
      console.warn('Lead capture received a malformed address — dropping the record.');
    }

    res.status(204).end();
  },
);
```

- [x] **Step 6: Run test to verify it passes**

```bash
cd website && npm test -- functions/lead.test.js
```

Expected: PASS, 5 tests.

- [x] **Step 7: Add the Hosting rewrite**

In `website/firebase.json`, add to `hosting.rewrites` after the `/api/contact` entry:

```json
      {
        "source": "/api/lead",
        "function": {
          "functionId": "lead",
          "region": "us-central1",
          "pinTag": true
        }
      }
```

- [x] **Step 8: Run the full website suite**

```bash
cd website && npm test
```

Expected: PASS, including the three files refactored in Step 1. If `brevoContactSync.test.js` or `joinWaitlist.test.js` now fail, the Step 1 rewrite missed a `capturedHandler(` call site.

- [x] **Step 9: Commit** (ask for approval first)

```bash
cd website && git add functions/index.js functions/lead.test.js functions/brevoContactSync.test.js functions/joinWaitlist.test.js functions/corsConfig.test.js firebase.json
git commit -m "$(cat <<'EOF'
feat: add POST /api/lead for the /start landing page

Also makes the function tests capture handlers by export rather than by
last-registration, which silently broke the moment index.js registered a
second onRequest.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Website — the `/start` page

**Files:**
- Create: `website/start.html`
- Modify: `website/vite.config.ts` (rollup input + dev clean-URL list)
- Create: `website/src/content/__tests__/start-page.test.ts`

**Interfaces:**
- Consumes: `/api/lead` (Task 2), `/signup?email=` prefill (Task 1), `public/3Maples-logo-horizontal-black.png`
- Produces: `dist/start.html`, served at `/start` by Firebase `cleanUrls`

- [x] **Step 1: Write the failing test**

Create `website/src/content/__tests__/start-page.test.ts`:

```ts
/**
 * Contracts for the /start paid-traffic landing page.
 *
 * /start is not part of the marketing site's crawlable surface — it is the
 * destination for ad clicks, it is noindex, and it is deliberately absent from
 * PAGE_META so it stays out of the sitemap and out of seo-head.test.ts. That
 * absence means nothing else in the suite watches this file, so everything the
 * page depends on is pinned here.
 */
import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

import { SITE_PAGES } from '../../seo/siteEnv'

const ROOT = path.resolve(__dirname, '..', '..', '..')
const html = fs.readFileSync(path.join(ROOT, 'start.html'), 'utf8')
const indexHtml = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8')

describe('/start crawl posture', () => {
  it('is noindex — it is an ad destination, not a search result', () => {
    expect(html).toMatch(/<meta name="robots" content="noindex">/)
  })

  it('is absent from SITE_PAGES, so it never reaches the sitemap', () => {
    expect(SITE_PAGES.some((p) => p.path === '/start')).toBe(false)
    expect(SITE_PAGES.some((p) => p.file === 'start.html')).toBe(false)
  })
})

describe('/start assets', () => {
  it('references a logo file that actually exists', () => {
    const match = html.match(/<img[^>]+src="(\/[^"]+\.png)"/)
    expect(match).not.toBeNull()
    const src = match![1]
    // The spec shipped /assets/3maples-logo-horizontal.png, which has never
    // existed. The real file lives in public/ and is served from the root.
    expect(fs.existsSync(path.join(ROOT, 'public', src.slice(1)))).toBe(true)
  })

  it('keeps the hero type-and-colour only — no image on the LCP path', () => {
    // The nav logo above it is expected (acceptance test #3); what the
    // non-negotiable forbids is an image in the hero itself.
    const hero = html.slice(html.indexOf('<section class="hero"'), html.indexOf('HOW IT WORKS'))
    expect(hero).not.toMatch(/<img/)
    expect(hero).not.toMatch(/background:\s*url\(/)
  })
})

describe('/start analytics', () => {
  it('templates the measurement and pixel IDs rather than hardcoding them', () => {
    expect(html).toContain('%VITE_GA_MEASUREMENT_ID%')
    expect(html).toContain('%VITE_META_PIXEL_ID%')
    expect(html).not.toMatch(/G-[A-Z0-9]{7,}/)
    expect(html).not.toMatch(/fbq\('init',\s*'\d/)
  })

  it('carries the same hostname allowlists as the homepage', () => {
    // Without these the dev deploy at maples-website-dev.web.app fires the
    // production pixel — the bug the allowlists were added to fix.
    for (const guard of ["var GA_HOSTS = ", "var PIXEL_HOSTS = "]) {
      const line = indexHtml.split('\n').find((l) => l.includes(guard))
      expect(line, `${guard} missing from index.html`).toBeDefined()
      expect(html).toContain(line!.trim())
    }
  })
})

describe('/start form', () => {
  it('degrades to a real navigation when JavaScript is off', () => {
    // Without action/method the no-JS submit silently reloads the page and the
    // visitor is lost; novalidate means they do not even get native validation.
    const forms = html.match(/<form[^>]*class="signup"[^>]*>/g) ?? []
    expect(forms).toHaveLength(2)
    for (const form of forms) {
      expect(form).toContain('action="https://app.3maples.ai/signup"')
      expect(form).toContain('method="get"')
    }
  })

  it('posts to the lead endpoint and hands off to signup', () => {
    expect(html).toContain("var ENDPOINT='/api/lead'")
    expect(html).toContain("var SIGNUP='https://app.3maples.ai/signup'")
  })

  it('links to the privacy policy — the page collects PII and runs a pixel', () => {
    expect(html).toContain('href="/privacy"')
  })
})

describe('/start visual parity with the site', () => {
  const TOKENS = [
    ['--bg-2', '#f0eef7'],
    ['--surface-2', '#f5f4fa'],
    ['--surface-3', '#e7e8ef'],
    ['--ink', '#2a2546'],
    ['--ink-2', '#4a4570'],
    ['--ink-soft', '#7a7696'],
    ['--muted', '#a7a5bd'],
    ['--line', '#e8e7ef'],
    ['--line-2', '#d6d8e3'],
    ['--accent', '#2f9e6b'],
    ['--danger', '#dc4b4b'],
  ] as const

  it.each(TOKENS)('%s matches the homepage value %s', (token, value) => {
    expect(indexHtml).toContain(`${token}: ${value}`)
    expect(html).toMatch(new RegExp(`${token}\\s*:\\s*${value}`))
  })

  it('uses the homepage h2 letter-spacing, not the spec table value', () => {
    // index.html:119 is -0.03em; the spec's table said -.025em.
    expect(html).toMatch(/h2\{[^}]*letter-spacing:-0?\.03em/)
  })
})

describe('/start build wiring', () => {
  const viteConfig = fs.readFileSync(path.join(ROOT, 'vite.config.ts'), 'utf8')

  it('is a standalone rollup entry, like 404.html', () => {
    expect(viteConfig).toContain("start: path.resolve(__dirname, 'start.html')")
  })

  it('is mapped for the dev server, or npm run dev serves index.html at /start', () => {
    expect(viteConfig).toContain("EXTRA_CLEAN_URL_PAGES = ['start']")
  })
})
```

- [x] **Step 2: Run test to verify it fails**

```bash
cd website && npm test -- start-page
```

Expected: FAIL — `ENOENT: no such file or directory, open '.../start.html'`.

- [x] **Step 3: Create `start.html`**

Take spec §9's complete file as the base, then apply **every** deviation D1-D8 from the table above. The `<head>` is rewritten enough to be worth spelling out in full — replace spec §9's head (its lines 403-522) with:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
```

…then the two guarded analytics snippets **copied verbatim from `index.html` lines 6-50** (the `GA_HOSTS` IIFE and the Meta Pixel IIFE, including their comments), then:

```html
<title>Landscaping estimates, built while you talk | 3Maples</title>
<meta name="description" content="Talk through the job. Maple builds the estimate. Free to start: 3 users, 20 estimates a month, 50 tasks. No credit card, no contract.">
<!-- Ad destination, not a search result. The build injects a second robots tag
     off production; both say noindex, which is harmless. robots.txt stays
     Allow: / on purpose — a Disallow would stop Google seeing this tag. -->
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- Loaded non-blocking, unlike index.html's render-blocking link: this page is
     gated on an LCP budget (spec acceptance test #1) and the homepage is not. -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"></noscript>
<style>
/* Tokens copied from index.html's :root — the homepage is the source of truth,
   not the spec's table. See the token parity test in
   src/content/__tests__/start-page.test.ts. */
```

The remainder of the `<style>` block is spec §9 verbatim **except** `h2{...letter-spacing:-.025em...}` → `-0.03em` (D2).

Body changes from spec §9:

- **Nav logo** (D1) — replace the `<img>` in `.brand`:
  ```html
  <a class="brand" href="/"><img src="/3Maples-logo-horizontal-black.png" alt="3Maples" width="1174" height="170" style="height:20px;width:auto;display:block"></a>
  ```
  The literal text "3Maples" after the image goes — the logo already says it, and the spec's `alt=""` plus adjacent text was the workaround for a 26×26 icon that does not exist.
- **Both forms** (D4) — `<form class="signup" id="f" novalidate>` → `<form class="signup" id="f" action="https://app.3maples.ai/signup" method="get" novalidate>`, and the same for `id="f2"`.
- **Footer** (D5):
  ```html
  <footer><div class="wrap">&copy; 2026 3Maples &middot; <a href="/privacy" style="color:inherit;text-decoration:underline">Privacy</a></div></footer>
  ```
- **Delete** spec §9's trailing Meta Pixel block and GA4 block (lines 688-705) — D3 moved both into `<head>`.

In the form script, apply D6 — replace the `finish` declaration:

```js
      var done=false, finish=function(){ if(!done){done=true;go(email);} };
```

with:

```js
      // If the handoff is ever blocked, give the visitor their button back
      // rather than leaving a dead "One second" control on screen.
      var done=false, finish=function(){
        if(done) return;
        done=true;
        go(email);
        setTimeout(function(){ btn.disabled=false; btn.textContent='Start free'; },2000);
      };
```

Everything else in spec §9 — the headline-swap script and its nine `utm_content` variants, all section markup, all copy — is verbatim. Do not regenerate it.

- [x] **Step 4: Wire the build**

In `website/vite.config.ts`, add below the `CLEAN_URL_PAGES` definition:

```ts
// Pages served at a clean URL but deliberately outside PAGE_META, so they stay
// out of the sitemap and out of seo-head.test.ts. `/start` is the paid-traffic
// landing page: noindex, ad-linked, not part of the crawlable site.
const EXTRA_CLEAN_URL_PAGES = ['start']
```

and change the dev-rewrite lookup to search both lists:

```ts
        const page = [...CLEAN_URL_PAGES, ...EXTRA_CLEAN_URL_PAGES].find(
          (p) => pathname === `/${p}` || pathname.startsWith(`/${p}/`),
        )
```

Then add the rollup entry in `build.rollupOptions.input`, next to `notFound`:

```ts
        // Paid-traffic landing page. A standalone entry rather than a PAGE_META
        // page: it is noindex and must not reach the sitemap.
        start: path.resolve(__dirname, 'start.html'),
```

- [x] **Step 5: Run test to verify it passes**

```bash
cd website && npm test -- start-page
```

Expected: PASS.

- [x] **Step 6: Build and verify the artifact**

```bash
cd website && npm run build && ls -la dist/start.html
```

Expected: build succeeds (`verify-bundles.mjs` included — `start.html` references neither `contact-modal.js` nor `maple-widget.js`, so it adds no constraints), and `dist/start.html` exists with the GA/pixel placeholders substituted.

- [x] **Step 7: Run the full website suite**

```bash
cd website && npm test
```

Expected: PASS, including `robots-sitemap.test.ts` — confirm `/start` is absent from the generated sitemap.

- [x] **Step 8: Manual check**

```bash
cd website && npm run dev
```

Visit `/start`, `/start?utm_content=you-talk`, and `/start?utm_content=garbage`. Expected: page renders at the clean URL; headline swaps for the known value; falls back to "Stop building estimates at midnight." for the unknown one.

- [x] **Step 9: Commit** (ask for approval first)

```bash
cd website && git add start.html vite.config.ts src/content/__tests__/start-page.test.ts
git commit -m "$(cat <<'EOF'
feat: add the /start paid-traffic landing page

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Deploy-gated acceptance run

Not code. Run spec §12 against the deployed page **before** any ad spend points at it. Tests 7-9 cannot pass until the open configuration items at the top of this plan are resolved and all three commits are deployed.

- [ ] Confirm `VITE_META_PIXEL_ID` matches `1027059673405942`
- [ ] Create the Brevo list `Leads - Not Signed Up`; set `BREVO_LEADS_LIST_ID` for the prod Functions environment
- [ ] Deploy website (page + function) and portal
- [ ] §12 #1 — PageSpeed Insights mobile against `https://3maples.com/start`: LCP < 2.5s, TBT < 200ms. **This is the gate.**
- [ ] §12 #2 — real phone on cellular: headline and email field visible without scrolling
- [ ] §12 #3 — logo renders, no broken image box
- [ ] §12 #4 — all nine `utm_content` values swap correctly, no flash, no layout shift
- [ ] §12 #5 — JavaScript disabled: default headline stands, page readable, and (beyond the spec) submitting navigates to signup rather than reloading
- [ ] §12 #6 — side by side with the homepage: same green, same ink, same Plus Jakarta Sans, same button radius, same container width
- [ ] §12 #7 — submit, watch Meta Events Manager Test Events for `Lead` on `1027059673405942`. **Must be run on `3maples.com`** — `PIXEL_HOSTS` blocks the pixel on `*.web.app` by design
- [ ] §12 #8 — submit, confirm the contact appears on `Leads - Not Signed Up`
- [ ] §12 #9 — inspect the redirect: lands on `app.3maples.ai/signup` carrying `email` and every `utm_` param, and the email field is prefilled
- [ ] §12 #10 — force `/api/lead` to 500; the redirect still happens
- [ ] §12 #11 — keyboard tab-through: focus ring visible on both inputs and both buttons

## Follow-ups (log, do not build here)

- `/api/lead` is an unauthenticated write into the marketing CRM with no rate limit. Cap it (Firestore counter keyed on IP, or App Check) before it is discovered. Without this, lead counts are attacker-controlled.
- `functions/index.js` `ALLOWED_ORIGINS` names `3maples.ai`; the marketing site is `3maples.com`. Harmless today (same-origin rewrite), wrong if anything ever calls these functions cross-origin.
- The spec diagnoses the funnel's failure as "four fields and a five-rule password." Prefilling one field does not change the other three or the password policy. Worth revisiting with Ron.
- `/start` has no Open Graph tags. Fine for ad clicks; a shared link will render bare.
- The Brevo contact carries no campaign attribution — decided 2026-09-04, because Brevo rejects unknown attribute names and a fail-open sync turns that into silently dropped leads. If per-campaign segmentation is ever wanted *inside Brevo*, the order is: create `UTM_SOURCE` / `UTM_MEDIUM` / `UTM_CAMPAIGN` / `UTM_CONTENT` as text attributes in the account first, then add them to the payload. Never the other way round.
- Nothing removes a contact from `Leads - Not Signed Up` once they actually sign up, so the list name describes a state no code maintains. Worth a Brevo automation keyed on the `account_created` lifecycle event, or accept it as "submitted an email on /start" and rename.
- Spec §8's events table lists a **Google Ads conversion** on form submit, deferred there to "when the Ads account exists". Not built here. When the account is live, add the tag to `start.html` behind the same `GA_HOSTS`-style hostname guard as the other two.
