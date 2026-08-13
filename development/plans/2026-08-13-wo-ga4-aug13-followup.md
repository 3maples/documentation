# WO-GA4-AUG13 follow-up — net-new items only

**Status: complete.** Scope was cut during review — see "Deliberately not done" below.

## Context

Ron issued a second work order (`3maples-wo-ga4-measurement_2.md`, Aug 13) that partly re-specifies work already completed earlier the same day and partly opens new ground. This covers **only the net-new, non-conflicting items**. Everything already built stands, and the same governing rule applies: **where the WO conflicts with the codebase, the repo wins.**

### Triage of the new WO

| WO item | Verdict |
|---|---|
| §1 GA4 tag on the app | Already done (build-time env-gated Vite plugin). Hostname guard **not adopted** — see below. |
| §1 SPA route tracking | No code needed; Ron enabled the history-events toggle on the Portal stream. |
| §2 conversion in the success path | Already done. Ron's `localStorage`-keyed variant **not adopted**. |
| §2 "confirm fbq PageView fires on /signup" | Already answered from the production bundle; no code change. |
| §3 UTM passthrough | Already done. **Click-ID forwarding adopted.** |
| §4 kill cross-hostname pollution | **Pixel guard adopted.** GA guard not adopted. |
| §5 app `robots.txt` | Already fixed in code (`30d6bb8`, Aug 12), unreleased. |
| §5 app `noindex` meta | Not adopted — inert. |

---

## Done

### 1. Click-ID forwarding — `website/src/analytics/utm-passthrough.ts`

`utm_*` alone is not enough: Google Ads and Meta attribute on `gclid` / `fbclid`, so forwarding only the campaign params gives GA4 a source while leaving the ad platforms unable to tie a signup back to the click that paid for it. Since the driver is an ad relaunch, this matters at least as much as the UTMs.

- `extractUtmParams` → **`extractAttributionParams`** (the old name became a lie once it returned click IDs).
- New `isAttributionParam(key)`: `utm_` **prefix** (case-insensitive) **or** exact match against `['gclid','fbclid','msclkid']`.
- The prefix match is kept rather than swapped for the WO's fixed five-name list, which omits `utm_id` and `utm_source_platform`. The result is a superset of both.
- The same predicate now guards `decorateUrl`'s "already attributed" check, so a link carrying its own `gclid` is left alone exactly as one carrying its own `utm_source` is.
- **All-or-nothing decoration kept** over the WO's per-param `if (!has(k)) set(k)`: merging per-param would blend a link's hardcoded campaign with the session's into attribution belonging to neither.

Tests: 8 new cases in `utm-passthrough.test.ts` (35 total), including a click ID arriving with no UTMs, case-insensitivity, rejection of near-miss names like `my_gclid`, and the full landing → `/pricing` → click acceptance path extended to carry a `gclid`.

### 2. Meta Pixel hostname guard — all 5 pages

One line inside the pixel snippet's existing IIFE guard:

```js
var PIXEL_HOSTS = ['3maples.com', 'www.3maples.com'];
if (PIXEL_HOSTS.indexOf(location.hostname) === -1) return;
```

Rationale: the production build is also served at `maples-website.web.app`. Nobody browses it — it carries `<link rel="canonical" href="https://3maples.com/">`, so search never sends anyone there — but we open it ourselves from the Firebase console, and Ron's runsheet logged 16 pixel events from it. Those internal visits land in Meta retargeting audiences and lookalike seeds, which is the one place a handful of junk events has outsized effect.

Verified at runtime against the built `dist/index.html` in jsdom, with a numeric pixel ID baked in:

| Host | Result |
|---|---|
| `3maples.com` | fires |
| `www.3maples.com` | fires |
| `maples-website.web.app` | blocked |
| `maples-website-dev.web.app` | blocked |
| `localhost` | blocked |

Tests: 2 new cases per page in `meta-pixel-presence.test.ts`, including one asserting the guard precedes `fbq('init')` — a guard placed after init would stop nothing.

---

## Deliberately not done

**GA4 hostname guard, website and portal.** Dropped after weighing cost against value. Cost: rewriting a static `<script async src>` into a dynamic loader across 5 pages, moving `gtag` into an IIFE (which would silently break `section-tracking.ts`, since it reads `win.gtag` and only works today because `function gtag(){}` at page scope happens to be global), plus rewriting two existing test files. Value: filtering out our own clicks. If GA4 noise ever becomes visible, the conventional remedy is an internal-traffic filter in GA4 admin — Ron's side, zero code. The env-var gate already covers the risk that actually mattered, which is dev *builds* carrying a production tag.

**`noindex` meta on the portal.** `firebase.json` already sends `X-Robots-Tag: noindex, nofollow`, and `robots.txt`'s `Disallow: /` means a compliant crawler never fetches the page to read either one. Pure checklist; changes nothing.

**§2's `localStorage`-keyed once-guard.** The conversion fires inside the resolved promise of account creation, after which the app signs out and navigates — refreshing the success screen cannot re-run it, so the WO's acceptance test #6 already passes. Ron's version would add a permanent `3m_signup_tracked_<accountId>` key per account ever created in that browser and require plumbing an account ID to the call site, for no behavior change.

**§2's OAuth branch.** Still no `signInWithPopup` / `GoogleAuthProvider` anywhere in the portal.

---

## Findings to pass to Ron

1. **`maples-website.web.app` is not a dev domain.** `maples-website` is the *production* Firebase site (`maples-website-dev` is dev). The pollution was the prod build reporting from a second hostname, not a dev deploy — which is why an env gate could never have fixed it, and why the guard is a hostname check.
2. **`app.3maples.ai/robots.txt` currently returns the app shell — the fix is already committed but unreleased.** `portal/public/robots.txt` landed 2026-08-12 (`30d6bb8`) and is correct. There are **6 unreleased commits on `portal/main`**; acceptance test #9 passes automatically on the next `/release portal`.
3. **Acceptance test #8 is still unsatisfiable as written.** Meta's Test Events tab only shows events carrying a `test_event_code`, which this integration never sends. Use Events Manager → Overview / Diagnostics, or the Meta Pixel Helper extension.
4. **Correction accepted.** My earlier report said the site and app were separate GA4 properties that could not stitch sessions. That came from Ron's superseded doc and was wrong: one property, cross-domain linking now configured. No code consequence — the linker appends `_gl` at click time and our decorator round-trips the URL through `new URL()`, preserving it.

## Still parked

- **Query-string PII** — the `page_location` sanitizer is in the portal GA tag. Ron still needs "Exclude URL query parameters" on the data stream for enhanced-measurement pageviews. The Meta pixel remains unmitigated.

## Verification run

- `npm test` (website): **562 passing**, 27 files.
- `npm run build` + `verify-bundles.mjs`: clean.
- Runtime jsdom checks against built `dist/`: pixel guard table above; UTMs + `gclid` + `fbclid` all survive landing → untagged `/pricing` → click.
- `dist/` left in its normal state (pixel sentinel `disabled`, no real ID baked in).
