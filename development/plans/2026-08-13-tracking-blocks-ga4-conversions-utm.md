# Tracking Blocks 1–3: GA4 on the app, signup conversions, UTM passthrough

## Context

Ron's work order ([website/seo/3maples-wo-tracking-blocks-1-2.md](website/seo/3maples-wo-tracking-blocks-1-2.md), Aug 11) reports that paid ads restart with no measurement in place: the portal app at `app.3maples.ai` has **no GA4 tag at all**, no signup conversion event reaches either Google or Meta, and campaign parameters that land on `3maples.com` **die at the click** through to the app because every CTA is a hardcoded `href`.

Three fixes, two repos:

- **Block 1** — GA4 (`G-11QBML6KHK`, the existing Portal stream on `maples-ai-prod`) loads on `app.3maples.ai`, and never in a dev deploy.
- **Block 2** — a `sign_up` (GA4) + `CompleteRegistration` (Meta) conversion fires exactly once, at the moment account creation actually succeeds.
- **Block 3** — `utm_*` params captured on landing at `3maples.com` ride through to the app on every Get Started / Login button.

Outcome: Ron can mark `sign_up` as a key event in GA4, Meta Events Manager shows registrations, and both are attributable to the campaign that produced them.

### Governing rule: the repo wins

**The WO is a statement of intent, not a specification.** It was written without repo access, so wherever its literal instructions conflict with what the code actually does, **the existing codebase takes precedence** — in both `portal/` and `website/`. Established patterns (the `metaPixel.ts` loader shape, the `%VITE_*%`/env-var dev gate, `replaceOrThrow` HTML injection, the `describe.each(PAGES)` fs-read tests, the rollback-aware signup path) are the source of truth; the WO supplies the *goal*, which is: GA4 reporting on the app, one conversion event per real signup in both dashboards, and campaign attribution surviving the click to the app.

Every divergence below is recorded so Ron can be told what changed and why — none of them are silent.

### Where the WO conflicts with this codebase

Six instructions need adjusting, and one is a trap:

1. **Block 2c is already implemented.** [portal/src/lib/metaPixel.ts:67](portal/src/lib/metaPixel.ts:67) already calls `fbq('track','PageView')` immediately after `init`, on the same code path. Adding the line again would be a literal no-op that *hides* whatever is actually wrong. Phase 0 diagnoses instead.
2. **Block 2's OAuth branch is dead code.** The portal has no `signInWithPopup` / `GoogleAuthProvider` / `signInWithRedirect` anywhere — email/password only. Skip it entirely.
3. **Block 1's two rules contradict each other.** "Paste into `index.html`'s `<head>`" and "don't let it ship in any dev deploy" cannot both hold: [portal/index.html](portal/index.html) is a plain static file with no env templating. The env-gated Vite plugin (your call) resolves this.
4. **Block 2b's call site is wrong for us.** Firing right after `createUserWithEmailAndPassword` would report conversions for accounts that [rollbackOrphanedFirebaseUser](portal/src/lib/auth/rollbackOrphanedFirebaseUser.ts) then deletes — phantom signups in both dashboards. Keep the existing placement at [SignupPage.tsx:218](portal/src/pages/auth/SignupPage.tsx:218), after the portal user and verification email both succeed.
5. **Block 3's snippet has two real bugs.** `href += '?' + tail` appends *after* a fragment (`/signup#top?utm_source=fb` — not a query string at all), and the `indexOf('utm_')` double-append guard also matches a *path* containing `utm_`. Both fixed by parsing with `URL`.
6. **Block 1's CSP bullet is a no-op today** — the portal sets no CSP ([firebase.json](portal/firebase.json) has only HSTS / nosniff / X-Frame-Options / Referrer-Policy / X-Robots-Tag). Nothing to do; noted for whenever a CSP does land.

### Decisions taken

| Decision | Choice |
|---|---|
| GA4 scope in the portal | **App-wide** — GA4 is first-party product analytics, and Enhanced Measurement history-change pageviews only exist if gtag loads on every route |
| GA4 injection | **Env-gated `transformIndexHtml` Vite plugin** — `<head>`-level load, zero footprint in dev builds |
| UTM decoration | **Load pass + delegated click listener**, scoped to the Get Started / Login buttons. Maple widget CTA explicitly out of scope |

---

## Phase 0 — Diagnose the pixel before writing code (~10 min, no commits)

The WO says the pixel "initializes on /signup but has never fired an event." That contradicts [metaPixel.ts:66-67](portal/src/lib/metaPixel.ts:66). Both cannot be true, so find out which:

```bash
curl -s https://app.3maples.ai/ | grep -o 'assets/index-[^"]*\.js' | head -1
```

Then fetch that bundle and grep for `1027059673405942` and `fbevents`.

- **Not present** → the production build has no pixel ID. Either `vars.VITE_META_PIXEL_ID` was never created on the portal repo's `Production` environment, or the deployed `release` build predates the metaPixel commit. This is the most likely cause and it explains the whole symptom.
- **Present** → hard-reload `app.3maples.ai/signup` in a clean Chrome profile, Network filtered to `facebook`. No `fbevents.js` at all ⇒ blocked client (uBlock / Brave / Safari ITP). Request present but no `/tr?…&ev=PageView` ⇒ read the `id=` param, it's the wrong pixel.

Also check `gh variable list --env Production` on the portal repo, and `git log -1 --format=%ci release -- src/lib/metaPixel.ts` against the deploy history.

> **Also tell Ron:** acceptance test #5 as written is unsatisfiable. Meta's **Test Events** tab only shows events carrying a `test_event_code`, which this integration never sends. Verify in Events Manager → Overview / Diagnostics instead, or use the Meta Pixel Helper extension.

**No code change for Block 2c.** Record the finding in the Phase 2 commit message.

---

## Phase 1 — GA4 loader in the portal (Block 1)

Two pieces: a build plugin that injects the tag, and a tiny runtime module that Block 2 can fire events through.

### 1a. The plugin

**New file `portal/vite/gtagPlugin.js`** — a plain-JS module (matching `vite.config.js`, which is also JS) exporting:

- `resolveGaMeasurementId(env)` — pure; returns the ID only if it matches `/^G-[A-Z0-9]+$/`, else `""`. Rejects `""`, `undefined`, and an accidental `%VITE_GA_MEASUREMENT_ID%` placeholder.
- `buildGtagSnippet(measurementId)` — pure; returns the `<script>` markup.
- `gtagPlugin(env)` — the Vite plugin; `transformIndexHtml` injects the snippet immediately after `<head>`, and **throws if the `<head>` anchor is missing** (borrowing the `replaceOrThrow` discipline from [website/vite.config.ts:130](website/vite.config.ts:130) — a silent no-op here means shipping an untagged app and not noticing).

Snippet shape — Ron's exact code, plus PII stripping (see risk 1 below):

```html
<!-- Google tag (gtag.js) — GA4 Portal stream, property maples-ai-prod.
     Injected at build time by vite/gtagPlugin.js, ONLY when
     VITE_GA_MEASUREMENT_ID is set — so dev deploys ship no tag at all. -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  // Strip invitation/auth params out of the reported URL: /signup carries
  // ?invite=<token>&email=<address> and the Firebase action links carry
  // ?oobCode=<single-use token>. Those must not reach Google.
  gtag('config', 'G-XXXX', { page_location: (function () {
    try {
      var u = new URL(window.location.href);
      ['invite','email','oobCode','apiKey','token'].forEach(function (k) { u.searchParams.delete(k); });
      return u.toString();
    } catch (e) { return window.location.origin + window.location.pathname; }
  })() });
</script>
```

> `dataLayer.push(arguments)` must stay the `arguments` object — gtag.js identifies commands by `[object Arguments]`. A tidier `push([...args])` looks equivalent and silently records nothing.

**Modify `portal/vite.config.js`**: switch to the function form so the plugin can read env files as well as CI env vars, since Vite does *not* put `.env` values into `process.env`:

```js
import { defineConfig, loadEnv } from "vite";
import { gtagPlugin } from "./vite/gtagPlugin.js";

export default defineConfig(({ mode }) => ({
  plugins: [react(), gtagPlugin(loadEnv(mode, process.cwd(), "VITE_"))],
  // …existing resolve / test blocks unchanged
}));
```

### 1b. The event seam

**New file `portal/src/lib/googleAnalytics.ts`** — no loader (the plugin owns loading), just the typed window declaration and:

```ts
export function trackGaEvent(eventName: string, params?: Record<string, unknown>): void
```

Guards on `typeof window.gtag !== "function"`, so it is a clean no-op in dev and local builds where the plugin injected nothing. Header comment documents the app-wide-vs-signup-only split versus [metaPixel.ts](portal/src/lib/metaPixel.ts): GA4 is first-party analytics on our own property, not an ad network building cross-site audiences.

### Tests first

**`portal/tests/gtagPlugin.test.ts`** (`.test.ts` — node env is fine, no DOM):
1. `resolveGaMeasurementId` accepts `G-11QBML6KHK`.
2. Returns `""` for unset, `""`, `"%VITE_GA_MEASUREMENT_ID%"`, `"UA-1234-5"`, `"G6JJ1W36JH"`.
3. `buildGtagSnippet` embeds the ID in both the `src` and the `config` call.
4. Plugin's `transformIndexHtml` returns the HTML **unchanged** when the ID is unset — the dev-deploy guarantee.
5. Injects exactly one gtag script when set.
6. **Throws** when `<head>` is absent.

**`portal/tests/googleAnalytics.test.tsx`** (`.tsx` is **mandatory** — `environmentMatchGlobs` in `vite.config.js` only routes `.test.tsx` to jsdom). Copy the `vi.resetModules()` + dynamic-`import()` + `vi.stubEnv` scaffolding from [tests/metaPixel.test.tsx](portal/tests/metaPixel.test.tsx):
7. `trackGaEvent("sign_up", {method:"email"})` forwards all three args to `window.gtag`.
8. Two-arg form when `params` is omitted.
9. Does not throw when `window.gtag` is absent.

---

## Phase 2 — Signup conversion (Block 2a / 2b)

**New file `portal/src/lib/signupConversion.ts`** — its own module so each vendor loader stays single-purpose and the "fires both, exactly once, never throws" behavior has one testable seam:

```ts
import { trackGaEvent } from "./googleAnalytics";
import { trackMetaEvent } from "./metaPixel";

export type SignupMethod = "email";

// Module-level rather than the WO's `window.__3m_signup_tracked`: both reset on
// reload, but this one is resettable in tests via vi.resetModules and keeps the
// app off the global namespace. Matches metaPixel.ts's `initialized`.
let reported = false;

export function trackSignupComplete(method: SignupMethod = "email"): void {
  if (reported) return;
  reported = true; // set BEFORE the vendor calls, so a throw can't allow a re-fire
  try {
    trackGaEvent("sign_up", { method });
    trackMetaEvent("CompleteRegistration", { content_name: "app_signup" });
  } catch (error) {
    console.warn("Signup conversion tracking failed", error);
  }
}
```

**Modify [portal/src/lib/metaPixel.ts:71](portal/src/lib/metaPixel.ts:71)** — widen to `trackMetaEvent(eventName: string, params?: Record<string, unknown>)`. Forward the third argument **conditionally**: always passing `undefined` would queue `["track","CompleteRegistration",undefined]`, breaking the existing `toContainEqual(["track","CompleteRegistration"])` assertion and putting an empty custom-data payload on the wire.

**Modify [portal/src/pages/auth/SignupPage.tsx](portal/src/pages/auth/SignupPage.tsx)** — swap the import at L33 (`trackMetaEvent` → `trackSignupComplete`, keep `initMetaPixel`), and replace L218-220 in place, extending the existing comment to record why the call site is where it is:

```ts
      // Account fully created (portal user + verification email) — report the
      // conversion to GA4 and Meta regardless of how the post-signup redirect
      // goes. Deliberately NOT fired right after createUserWithEmailAndPassword:
      // the rollback path above deletes orphaned Firebase users, and a
      // conversion for an account that no longer exists is a phantom signup.
      trackSignupComplete("email");
```

### Tests first

**`portal/tests/signupConversion.test.tsx`** — `vi.hoisted` spies + top-level `vi.mock` of both vendor modules; `vi.resetModules()` per test to clear the once-flag:
1. Fires `trackGaEvent("sign_up", { method: "email" })`.
2. Fires `trackMetaEvent("CompleteRegistration", { content_name: "app_signup" })`.
3. Defaults `method` to `"email"`.
4. A second call fires neither vendor.
5. A throwing vendor call is swallowed — `expect(() => …).not.toThrow()`.
6. After a vendor throw, a second call still does not re-fire.

**Append to [portal/tests/metaPixel.test.tsx](portal/tests/metaPixel.test.tsx)**:
7. Three-element queue form when `params` is passed. Leave the existing two-arg test untouched — it now pins the no-trailing-`undefined` behavior.

**Amend [portal/tests/SignupPage.test.tsx](portal/tests/SignupPage.test.tsx)** — add `vi.mock("../src/lib/signupConversion", …)`. Do **not** leave the real helper unmocked here: its module-level once-flag is shared across every test in the file, so the second test to complete a signup would silently observe nothing.
8. Rewrite "fires CompleteRegistration on success" → asserts `trackSignupComplete` called once with `"email"`.
9. Rewrite "does not fire when creation fails" → asserts not called.
10. **New:** "does not report a conversion when the portal user is rolled back" — `createUserWithEmailAndPassword` resolves, `createPortalUser` rejects, rollback mocked to a non-`failed` result; assert not called. This is the regression guard for divergence #4 above. Check the exact `kind` union in [rollbackOrphanedFirebaseUser.ts](portal/src/lib/auth/rollbackOrphanedFirebaseUser.ts) first.

Keep the existing `../src/lib/metaPixel` mock for the `initMetaPixel`-on-mount test.

---

## Phase 3 — Portal CI wiring

**Modify [portal/.github/workflows/firebase-hosting-merge.yml](portal/.github/workflows/firebase-hosting-merge.yml)** — add to the `build_and_deploy` (Production) job's `env:` block **only**, matching the surrounding comment style used for `VITE_META_PIXEL_ID` at L42-45:

```yaml
          # GA4 — Portal stream G-11QBML6KHK on property maples-ai-prod. Set
          # only on the Production environment so dev deploys ship no tag at
          # all; unset ⇒ vite/gtagPlugin.js injects nothing. Same CAUTION as
          # above: baked in at build time, so a change needs a rebuild.
          VITE_GA_MEASUREMENT_ID: ${{ vars.VITE_GA_MEASUREMENT_ID }}
```

The `build_and_deploy_dev` job is left alone — omission *is* the dev-safety mechanism.

**Set the GitHub variable directly** (portal is its own repo; use the `3maples` gh account):

```bash
gh variable set VITE_GA_MEASUREMENT_ID --env Production --body G-11QBML6KHK --repo <portal-remote-slug>
```

**Test first — `portal/tests/deployWorkflowAnalytics.test.ts`** (node env, reads the workflow as text, splits on `build_and_deploy_dev:`). This is the only automated guard possible for a deploy-time property, and Block 1's "must not ship in any dev deploy" rule earns it:
1. Production job passes `VITE_GA_MEASUREMENT_ID`.
2. Development job does **not** mention it.
3. Production job passes `VITE_META_PIXEL_ID` (pins today's state).
4. Development job does **not** mention it.

---

## Phase 4 — UTM passthrough module (Block 3)

**New file `website/src/analytics/utm-passthrough.ts`**, following the DI + auto-init pattern of [section-tracking.ts](website/src/analytics/section-tracking.ts) (pure exports, `initUtmPassthrough(doc, win)`, bottom-of-file auto-init guarded by `typeof document !== "undefined"`).

Exports:

- `extractUtmParams(search)` — keeps `utm_*` keys (case-insensitive prefix), URL-encodes values, returns a `&`-joined tail or `""`.
- `captureUtms(search, storage)` — writes to `sessionStorage['3m_utms']`. **An untagged page must never clear an earlier capture** — that is the whole point of surviving the detour to `/pricing`. Keeps an in-memory fallback, because reading `win.sessionStorage` can itself throw when cookies are blocked (Safari private mode).
- `readStoredUtms(storage)` — storage, falling back to memory.
- `decorateUrl(href, tail)` — returns the decorated URL or `null`. **Parses with `new URL()`** rather than concatenating: fixes the fragment bug, matches on `url.host === "app.3maples.ai"` (so `https://evil.example/?r=app.3maples.ai` is rejected), and checks `searchParams` keys for an existing `utm_` prefix rather than a substring test on the whole href.
- `decorateAll(doc, tail)` — one pass over `a[href*="app.3maples.ai"]`.
- `initUtmPassthrough(doc, win)` — capture, then:
  1. **Load pass** on `DOMContentLoaded` (or immediately if already parsed) — decorates the 23 static nav / mobile-menu / CTA hrefs, so hover previews, "copy link address" and middle-click all carry the campaign.
  2. **Delegated capture-phase listener** on `document` for `click` and `auxclick` — rewrites the href before the browser resolves the default action, which covers `target="_blank"` and middle-click with no special handling, and makes the buttons robust to any re-render.

Per your call, the Maple widget CTA is not a requirement. The delegated listener happens to cover it anyway (the widget renders a plain light-DOM `<a href>`), and `data-signup-url` at [index.html:1223](website/index.html:1223) needs no separate handling. No `MutationObserver`.

### Tests first — `website/src/analytics/__tests__/utm-passthrough.test.ts`

(Vitest 4, jsdom, globals on — mirrors [section-tracking.test.ts](website/src/analytics/__tests__/section-tracking.test.ts).)

1. `extractUtmParams` keeps only `utm_*`, encoding spaces and `&`.
2. Returns `""` with no utm params.
3. Case-insensitive key prefix (`UTM_Source`).
4. `captureUtms` writes under `3m_utms`.
5. A later untagged page leaves the earlier capture intact.
6. Throwing storage still decorates, via the memory fallback.
7. `decorateUrl` appends to an app URL with no query.
8. Appends with `&` when a query exists (`/signup?invite=x`).
9. **Params land before the fragment** — the WO's concat bug.
10. `null` for a non-app host, including `https://evil.example/?r=app.3maples.ai`.
11. `null` when the URL already carries any `utm_` param.
12. `null` for an unparseable href (`mailto:`, `#anchor`).
13. `initUtmPassthrough` decorates static app links present at init.
14. Leaves non-app links untouched.
15. A link appended **after** init is decorated on click (dispatch a bubbling click from a child node).
16. Decorates on `auxclick`.
17. Clicking twice does not double-append.
18. No stored params ⇒ hrefs untouched.

---

## Phase 5 — Wire the module into the pages (Block 3)

Insert immediately before `</body>` in **`index.html`, `pricing.html`, `faq.html`, `privacy.html`, `terms.html`** — matching the existing [index.html:1511](website/index.html:1511) precedent for `section-tracking.ts`:

```html
<!-- UTM passthrough: campaign params captured on landing are appended to every
     app.3maples.ai link. See src/analytics/utm-passthrough.ts. -->
<script type="module" src="/src/analytics/utm-passthrough.ts"></script>
```

A static tag rather than a third `transformIndexHtml` plugin: it works in dev, is visible when reading page source, and its only downside ("you could forget a page") is exactly what the repo's `describe.each(PAGES)` fs-read tests already catch — earlier, since CI runs `npm test` before `npm run build`.

**No change** to the 23 hardcoded hrefs (decoration is runtime — [hero-carousel.test.ts:66](website/src/content/__tests__/hero-carousel.test.ts:66) asserts the bare URL in source), to `data-signup-url`, or to `vite.config.ts`.

### Tests first — `website/src/analytics/__tests__/utm-passthrough-presence.test.ts`

Modeled on [meta-pixel-presence.test.ts](website/src/analytics/__tests__/meta-pixel-presence.test.ts) — same `ROOT`, same `PAGES` array, same `describe.each`:
1. Each of the 5 pages loads the module exactly once.
2. The tag sits before `</body>`.
3. Every `app.3maples.ai` href in source is still bare, with no `utm_` — pins the runtime-decoration approach.
4. Separate `describe` for **404.html**: it does *not* load the module **and** contains no `app.3maples.ai` link, with a comment noting the second assertion justifies the first. The day someone adds a CTA there, the test fails and forces the decision.

---

## Verification

**Portal** (from `portal/`):

```bash
npm test -- tests/gtagPlugin.test.ts tests/googleAnalytics.test.tsx tests/signupConversion.test.tsx tests/metaPixel.test.tsx tests/SignupPage.test.tsx tests/deployWorkflowAnalytics.test.ts && npm run typecheck && npm run lint
```

Then prove the build gate both ways, without sending local traffic to the live property:

```bash
npm run build && grep -c googletagmanager dist/index.html
```

Expect `0` (no GA var locally). Then `VITE_GA_MEASUREMENT_ID=G-11QBML6KHK npm run build && grep -c googletagmanager dist/index.html` → expect `1`, and eyeball the injected snippet in `dist/index.html`. Also confirm `npm run build:dev` produces `0`.

**Website** (from `website/`):

```bash
npm test && npm run build
```

Then `npm run preview` and walk Ron's acceptance path: load `/?utm_source=fb&utm_medium=paid&utm_campaign=test`, browse to `/pricing`, click **Get started** — the app URL must carry all three params. Repeat with middle-click and with "copy link address".

**Production acceptance** (Ron, after `/release`): `/signup` with Network filtered to `collect` shows `tid=G-11QBML6KHK`; a test signup produces `en=sign_up` and `ev=CompleteRegistration`; a refresh produces no duplicate; log out / log in produces none.

> Every Block 1 and 2 acceptance criterion is **only observable on production** — the measurement ID is a Production-environment build variable, which is precisely the mechanism that satisfies "must not ship in dev deploys". `maples-dev` will show nothing, by design. The `gh variable set` in Phase 3 must land **before** the release deploy or the whole thing ships as a no-op.

---

## Risks to flag

1. **Query-string PII reaches Google and Meta.** [SignupPage.tsx:79-96](portal/src/pages/auth/SignupPage.tsx:79) reads `?invite=<token>&email=<address>` and only strips it via `replaceState` in a `useEffect` — *after* the initial `page_view` has already fired. Firebase action links carry `?oobCode=<single-use token>`. The `page_location` sanitizer in the Phase 1 snippet covers the initial pageview (which is where all these landing URLs are). **Ask Ron to also set "Exclude URL query parameters" on the GA4 data stream** for Enhanced Measurement's history-change pageviews. Sending PII to GA4 also breaches Google's own terms. The Meta pixel is already doing this today, unmitigated.
2. **`gclid` / `fbclid` are not forwarded** — Block 3 only moves `utm_*`. But Google Ads and Meta attribute on those click IDs, not on UTMs. Given the driver here is "ads restart tomorrow", forwarding them alongside the UTMs is a one-line extension to `extractUtmParams` and arguably matters more than the UTMs do. **Not in the plan — the WO doesn't ask for it. Say the word and I'll fold it into Phase 4.**
3. **High-cardinality page paths.** App-wide GA4 turns `/estimates/:id`, `/tasks/:id`, `/ops/companies/:id` into thousands of distinct `page_path` values, which makes the Pages report hard to read. Not sensitive; a normalization follow-up if it becomes annoying.
4. **No cross-domain measurement.** The site is `G-G6JJ1W36JH` and the app is `G-11QBML6KHK` — two properties, so a click from `3maples.com` starts a fresh session on the app. UTM passthrough gives that session campaign attribution (exactly Block 3's job) but the two cannot stitch a single user journey. Worth telling Ron.
5. **`import.meta.env.PROD` is `true` in `npm run build:dev`** — `vite build --mode development` still resolves `NODE_ENV=production`. This is why the GA gate is env-var presence, not `PROD`. Side observation: the Sentry init at [main.tsx:12](portal/src/main.tsx:12) is therefore active in the dev deploy too. Probably intentional; worth a separate look.
6. **No consent banner on either property.** GA4 + Meta Pixel with no consent mechanism is live exposure for EEA/UK traffic, and Consent Mode v2 is a hard requirement for Google/Meta *ads* audiences from the EEA. [privacy.html](website/privacy.html) describes cookies and pixels generically and names reCAPTCHA, but names neither Google Analytics nor Meta. Predates this work; app-wide GA4 widens it. Flag to legal, don't block.
7. **Ad-blocker attrition.** `googletagmanager.com` is blocked harder than `fbevents.js` — expect 20–40% of real signups missing from GA4. Set that expectation before "both dashboards saw the same signup" becomes the definition of done.

## Delivery notes

- **TDD throughout** per CLAUDE.md — every phase writes its tests first.
- If any further WO instruction turns out to contradict the code once implementation starts, the repo wins and the divergence gets recorded here and in the commit message — I won't re-litigate it mid-flight.
- This plan should be copied to `documentation/development/plans/` as its permanent home once implementation begins (plan mode restricted writes to the scratch path).
- Portal and website are **separate repos**; each needs its own commit, and each commit and push needs fresh explicit approval.
- The portal pre-push hook runs `lint` + `typecheck` + `npm test`; the website CI runs `npm test` before `npm run build`.
- Blocks 1 and 2 **must ship in the same portal release** — `sign_up` has nowhere to go without gtag loaded. Block 3 is fully independent and can go first.
- Promotion to production is `/release portal` and `/release website`, on your explicit say-so only.
