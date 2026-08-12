# SEO for the 3Maples marketing site

_Planned 2026-08-12. Source audit: `website/seo/3maples-seo.md` (Ron, 2026-08-07)._

## Context

`website/` (the 3maples.com marketing site) has essentially no SEO. It is a five-page
static Vite multi-page build (`index/pricing/faq/privacy/terms` .html) deployed to
Firebase Hosting. Today:

- **Every unmatched URL returns HTTP 200 with the homepage.** `firebase.json` ends with
  a catch-all `{ "source": "**", "destination": "/index.html" }`. `/pricing`, `/blog`,
  `/sitemap.xml` and any nonsense string all serve the homepage — Google will index
  homepage duplicates at arbitrary URLs.
- **The only meta tag on the homepage is `viewport`.** No description, no canonical, no
  Open Graph, no Twitter card, no structured data. Titles are brand-first
  (`3Maples — The Landscaper's Operating System`) and the legal/pricing/FAQ titles are
  `3Maples - Pricing`-style.
- **The FAQ page is invisible to crawlers.** All 49 Q&As live in
  `src/content/faqs.json` and are injected client-side by React into `#forum-root`
  (`src/forum/main.tsx` → `ForumHome` → `FaqAccordion`). Googlebot sees ~228 words.
- **`robots.txt` is 23 bytes** (`User-agent: * / Allow: /`) with no sitemap line, and
  there is no `sitemap.xml`.
- **The homepage ships ~19 MB of images.** `TT-v1.png` is 13.5 MB and `ED-v1.png` is
  5.7 MB, neither with `loading` or dimensions. This is a severe Core Web Vitals
  problem not covered in Ron's audit.
- **The dev site writes into production analytics.** `_deploy.yml` reads
  `vars.VITE_GA_MEASUREMENT_ID` per GitHub environment; the `dev` environment appears to
  carry the production ID. `maples-website-dev.web.app` is also fully indexable.

Source of truth for the work: `website/seo/3maples-seo.md` (Ron, 2026-08-07). This plan
follows it, with four deliberate deviations flagged inline (FAQ count, OG images, hero
H1 mechanics, image weight).

Intended outcome: real 404s, one canonical URL per page, complete head tags, crawlable
FAQ content, valid structured data, and a homepage that is not 19 MB.

---

## Approach

Seven phases, each independently shippable. Phases 1–5 are the website repo; 6–7 are
outside it. **TDD throughout** (CLAUDE.md mandates it for `.html`/`.ts` behavior
changes) — the site already has the right test idiom: `src/content/__tests__/*.test.ts`
read the raw HTML files off disk with `fs.readFileSync` and assert on their contents.
See `src/content/__tests__/favicon-links.test.ts` and `legal-footer-links.test.ts` for
the established pattern; new SEO tests copy it exactly.

---

### Phase 1 — Clean URLs, real 404s

**`website/firebase.json`**

- Delete the `{ "source": "**", "destination": "/index.html" }` catch-all.
- Delete the now-redundant `{ "source": "/faq", "destination": "/faq.html" }` rewrite —
  `cleanUrls` supersedes it.
- **Keep** the `/api/contact` function rewrite. It must stay first in the array.
- Add `"cleanUrls": true` and `"trailingSlash": false` to the `hosting` block.

`cleanUrls` serves `/pricing` from `pricing.html` **and** 301s `/pricing.html` → `/pricing`,
which kills the `/faq` vs `/faq.html` duplicate (currently both 200 with identical bytes)
in the same setting.

**`website/404.html`** (new) — minimal page from §1 of the audit, with
`<meta name="robots" content="noindex, follow">`. Firebase serves it with a real 404
status automatically. Register it as a build input in `vite.config.ts`
(`rollupOptions.input.notFound`) so it lands in `dist/`.

**Internal links** — mechanical rewrite across all five pages. The pattern is uniform
(verified): per page 3× `/pricing.html`, 1× `/privacy.html` (2× in terms.html), 1×
`/terms.html`, 3× `/faq` (already extensionless). Rewrite `.html` → extensionless in
nav, mobile menu, and footer.

**`website/vite.config.ts`** — generalize the existing `faqDevRewrite()` plugin into
`cleanUrlsDevRewrite()`: map `/pricing`, `/faq`, `/privacy`, `/terms` (and `/x/*`
subpaths, as the current FAQ rule does) to their `.html` files, so `npm run dev` matches
production. Keep the explanatory comment block — it documents why the plugin exists.

**Tests**
- New `src/content/__tests__/clean-urls.test.ts`: no page contains `href="/pricing.html"`,
  `/privacy.html`, `/terms.html`, or `/faq.html`; `firebase.json` has `cleanUrls: true`,
  `trailingSlash: false`, no `**` rewrite, and still has the `/api/contact` function
  rewrite; `404.html` exists and carries the noindex robots meta.
- **Update `src/content/__tests__/legal-footer-links.test.ts`** — it currently asserts
  `<a href="/privacy.html">Privacy Policy</a>` and will fail. Change both assertions to
  the extensionless hrefs.

---

### Phase 2 — robots.txt, sitemap.xml, and non-prod de-indexing

All three are produced by one build-time Vite plugin keyed off a new `VITE_SITE_ENV`,
**failing safe**: only `VITE_SITE_ENV === 'production'` gets the indexable output;
anything else (local dev, the `dev` GitHub environment, an unset var) gets the blocked
version. Add `VITE_SITE_ENV: ${{ vars.VITE_SITE_ENV }}` to the Build step env in
`.github/workflows/_deploy.yml` and set it to `production` on the `production` GitHub
environment only (Phase 6).

**robots.txt** — production gets `Allow: /` plus the `Sitemap:` line; non-prod gets
`Disallow: /`. Delete `public/robots.txt`; the plugin owns it via `emitFile`.

**Non-prod `noindex`.** *Amendment:* `Disallow: /` blocks crawling but does not remove
already-indexed URLs — a blocked page can sit in the index indefinitely as a stale entry.
`maples-website-dev.web.app` needs a real `noindex`. An `X-Robots-Tag` header won't work
here: `firebase.json` has a single `hosting` block shared by the dev and prod targets, so
a header can't differ between them. Instead the same plugin injects
`<meta name="robots" content="noindex, nofollow">` into every page's `<head>` via
`transformIndexHtml` when `VITE_SITE_ENV !== 'production'` — per-build, so the prod
artifact never carries it. (The portal's own `firebase.json` is app-only, so Phase 7 uses
the header approach there.)

**sitemap.xml** — *amendment:* generate it at build time from the same page list the
tests use, rather than a hand-edited static file. `priority` is omitted — Google ignores
it. `lastmod` comes from each source HTML file's git commit date, so it stays honest
instead of decaying to a stale hard-coded string. Emitted only in the production build.

**Tests** — new `src/content/__tests__/robots-sitemap.test.ts`, against the pure helpers:
- `renderRobotsTxt(siteEnv)` → `Disallow: /` for `undefined` / `'dev'`, and `Allow: /`
  plus the `Sitemap:` line for `'production'`.
- `renderSitemap(pages)` → valid XML, exactly the five expected `<loc>` values, all
  `https://3maples.com`, none ending in `.html`, no `<priority>`, every `<lastmod>` a
  valid ISO date.
- `shouldNoindex(siteEnv)` → true for everything except `'production'`.

---

### Phase 3 — Head tags on all five pages

Paste the §4 blocks from the audit into each `<head>`, after the existing `<title>`:
new titles, meta descriptions, `<link rel="canonical">`, Open Graph (`og:type`,
`og:site_name`, `og:url`, `og:title`, `og:description`) and `twitter:card` /
`twitter:site`. `/privacy` and `/terms` already have descriptions — they get canonicals,
OG and Twitter tags only.

**OG image — produced in this change.** *Amendment:* rather than defer to Ron and ship
with no social preview, generate `public/og/3maples-og-home.jpg` here. Build a small
1200×630 HTML template using the site's own tokens (Plus Jakarta Sans, `--ink #2a2546`,
`--accent #2f9e6b`) and `public/3Maples-logo-horizontal-black.png`, then screenshot it
with the Playwright MCP at exactly 1200×630 and export under 300 KB. Keep all type inside
the centre 80% — LinkedIn and X crop the edges. Wire it into every page's head as
`og:image` / `og:image:width` / `og:image:height` / `og:image:alt` and `twitter:image`.
If Ron later delivers a designed version, it drops in at the same path with no code
change.

No second asset is needed: the Organization schema's `logo` points at the existing
square `public/favicon-512.png` instead of a new `/og/3maples-logo-512.png`.

**Tests** — new `src/content/__tests__/seo-head.test.ts`, table-driven over the five
pages like `favicon-links.test.ts`: exactly one `<title>` and it matches the expected
string; `name="description"` present with length in 120–165 chars; canonical present and
equal to the expected absolute URL; `og:type`/`og:site_name`/`og:url`/`og:title`/
`og:description` and `twitter:card` present; `og:url` equals the canonical.

---

### Phase 4 — Structured data + crawlable FAQ content

**Homepage JSON-LD** — the §5 `@graph` (Organization + SoftwareApplication) pasted before
`</head>` in `index.html`, with two corrections:

- **Confirm the `offers` block before shipping.** The Free plan must genuinely require no
  credit card. `faqs.json` (`credit-card-required`) says it does and the pricing page
  shows Free at $0, so the block stands — but re-read the live pricing page at
  implementation time. If there is any caveat, drop `offers` entirely rather than soften
  it (schema that overstates an offer is a manual-action risk).
- **Drop `"es"` from `inLanguage`.** *Amendment:* the audit claims `["en", "es"]`, but
  every page on the site is English-only. Maple supports Spanish; the marketing site does
  not. Ship `["en"]` and add `"es"` when a Spanish page exists.
- `logo` points at the existing `https://3maples.com/favicon-512.png`.
- Verify `alternateName: "3Maples, Inc."` matches the legal entity named in
  `terms.html` before shipping it as structured data.

**FAQ page — build-time pre-render + FAQPage schema.**

*Deviation from §6:* the audit assumes 8 questions; `src/content/faqs.json` actually has
**49**, and its static-fallback list is stale. Generate from the data file — never
hand-write it.

*Calibrate the expectation:* the audit calls FAQPage "the highest-value single item
here." Google restricted FAQ rich results in August 2023 to authoritative government and
health sites, so this will **not** produce FAQ snippets for 3Maples. It is still worth
shipping — AI crawlers and AI Overviews consume it, and it costs nothing once the data
plumbing exists — but the real win in this phase is the pre-rendered HTML: 228 crawlable
words becoming 49 full answers.

- New `website/src/seo/faqSchema.ts` — pure, unit-testable:
  - `mdToPlainText(md)` — strips the markdown used in the answers (`**bold**`,
    `[label](href)`) for the schema `text` values.
  - `mdToHtml(md)` — same two constructs → `<strong>` / `<a>` for the pre-rendered block.
  - `buildFaqPageSchema(faqs)` → the `FAQPage` JSON-LD object.
  - `renderFaqStaticHtml(faqs)` → `<h2>question</h2><div>answer</div>` markup.
- New Vite plugin (alongside the existing ones in `vite.config.ts`) using
  `transformIndexHtml`, scoped to the `faq.html` entry only. It injects the JSON-LD into
  `<head>` and the static Q&A markup **inside `#forum-root`**. `createRoot(container).render()`
  in `src/forum/main.tsx` clears the container's children on first render, so React
  replaces the pre-rendered block with the live accordion — crawlers get 49 full answers,
  users get the unchanged interactive page. No change to `ForumHome`/`FaqAccordion`.
  `transformIndexHtml` runs in dev too, so `npm run dev` gets the same output for free.

**Tests** — new `src/content/__tests__/faq-seo.test.ts`:
- `buildFaqPageSchema(faqs)` emits one `Question` per entry in `faqs.json` (count derived
  from the file, not hard-coded), every `acceptedAnswer.text` non-empty, no residual
  `**` or `[...](...)` markdown.
- `renderFaqStaticHtml` output contains every `question` string.
- `mdToHtml`/`mdToPlainText` round-trip the tricky live answers (`how-do-i-sign-up`
  has bold; `pricing` and `get-help` have links).
- Homepage JSON-LD: extract the `<script type="application/ld+json">` from `index.html`,
  `JSON.parse` it, assert `@graph` contains `Organization` and `SoftwareApplication` with
  the expected `@id`s and that `publisher.@id` resolves within the graph.

---

### Phase 5 — Hero H1, keyword copy, image weight

**H1 swap (§7).** *Deviation:* the H1 is not a standalone block — it lives in frame 1 of
the 7-frame animated hero carousel at `index.html:793-801`, as
`<h1 class="m3s-display">` with three `<span class="m3s-line m3s-up">` children carrying
staggered `animation-delay` values, under an `<span class="eyebrow m3s-up">`. Restructure
rather than paste:

- Promote the eyebrow text (`The Landscaper's Operating System`) to `<h1 class="m3s-display">`.
- Demote `Easy to implement. / Easy to use. / Smart.` to a subhead element that keeps the
  `.m3s-line` / `.m3s-up` classes and the `.25s / .75s / 1.25s` delays, so the stagger
  animation is byte-for-byte unchanged.
- Add `<span class="eyebrow m3s-up">Just ask</span>` above.
- Verify visually at `npm run dev` — `m3s-display` sizing was tuned for three short lines
  and one long line will wrap differently.

**Keyword sentence.** Add to the opening copy (the `.m3s-sub` in frame 1, or the section
below the hero): *"3Maples is landscaping estimating software you run by talking.
Describe the job and Maple builds the estimate: materials, labor, overhead, profit.
Nothing missed."* The exact phrase "landscaping estimating software" appears nowhere on
the site today.

**Image weight** (not in the audit — found during exploration):

| File | Current | Action |
|---|---|---|
| `public/TT-v1.png` | 13.5 MB | downscale to ~1600px wide, convert to WebP |
| `public/ED-v1.png` | 5.7 MB | same |
| `public/DE-v1.png` | 427 KB | same |

Check tooling availability first (`cwebp`, then `sips`, then `npx sharp-cli` as fallback);
do not add a permanent dependency for a one-off conversion. Update the three `<img>` tags
at `index.html:1023/1035/1047` to the `.webp` sources and add `loading="lazy"`,
`decoding="async"`, and explicit `width`/`height` — matching the pattern already used
correctly at `index.html:957`. Leave the hero carousel images (`data-shot`, populated by
`src/hero/hero-carousel.ts`) eager.

**Tests** — new `src/content/__tests__/image-perf.test.ts`: every `<img>` in `index.html`
outside the hero carousel has `loading="lazy"` and explicit `width`/`height`; no file in
`public/` exceeds 500 KB. Add a case to the existing hero-carousel test only if the
restructure touches its selectors. Extend `src/content/__tests__/seo-head.test.ts` (or a
small sibling) with: `index.html` has exactly one `<h1>`, it contains "Landscaper", and
the page body contains the exact phrase "landscaping estimating software".

---

### Phase 6 — GitHub Actions variables (this repo, no code)

Set directly with `gh` on the `3maples` account (never hand these off as manual UI steps):

```bash
gh variable list --env dev && gh variable list --env production
```

Then, in the website repo:
- `production` environment: `VITE_SITE_ENV=production` (Phase 2). Deliberately **not** set
  on `dev`, so the fail-safe `Disallow: /` applies there. **Set this before the code
  ships** — in the other order, a production deploy would briefly serve `Disallow: /`
  plus a `noindex` meta on 3maples.com.

**The GA variable needed no change.** The audit's item 2 ("the dev domain is writing into
production analytics") does not reproduce: the `dev` environment has carried
`VITE_GA_MEASUREMENT_ID=G-JMT249S2CS` — the correct dev property — since 2026-05-24, and
`production` carries `G-G6JJ1W36JH`. The host GA4 diagnostics flagged,
`maples-website.web.app`, is **production's** own Firebase domain (the dev target is
`maples-website-dev`), so it is the production site firing the production ID — correct
behavior, not a leak. What remains is that production is reachable on two hostnames,
which inflates prod analytics with anyone testing via the `.web.app` URL. The SEO half of
that is now handled by the canonical tags in Phase 3; the analytics half is a GA4 hostname
filter, which sits with Ron.

---

### Phase 7 — De-index the app subdomain (portal repo)

`app.3maples.ai` serves the login shell at every path today. Login screens competing with
the marketing site in search helps nobody. Two changes, both needed for the same reason as
Phase 2 — robots.txt stops the crawl, `noindex` removes existing entries:

- `portal/public/robots.txt` (new): `User-agent: * / Disallow: /`.
- `portal/firebase.json`: add `{ "key": "X-Robots-Tag", "value": "noindex, nofollow" }` to
  the existing `headers` block (which already carries HSTS, `X-Frame-Options`, etc.).
  Unlike the website, the portal's `firebase.json` is app-only, so a header is safe here —
  and noindex is wanted on both the dev and prod app targets. Leave the SPA catch-all
  rewrite alone.

Separate repo, separate deploy, separate approval.

---

## Files touched

| Path | Change |
|---|---|
| `website/firebase.json` | drop catch-all + `/faq` rewrite, add `cleanUrls`/`trailingSlash` |
| `website/404.html` | new |
| `website/vite.config.ts` | `cleanUrlsDevRewrite`, FAQ SEO plugin, site-env plugin, `notFound` input |
| `website/index.html` | head tags, JSON-LD, H1 restructure, keyword copy, image srcs + lazy |
| `website/{pricing,faq,privacy,terms}.html` | head tags, extensionless internal links |
| `website/src/seo/faqSchema.ts` | new — pure FAQ helpers |
| `website/src/seo/siteEnv.ts` | new — `renderRobotsTxt` / `renderSitemap` / `shouldNoindex` |
| `website/public/og/3maples-og-home.jpg` | new — generated 1200×630 |
| `website/public/robots.txt` | deleted (plugin-generated) |
| `website/src/content/__tests__/*.test.ts` | 5 new files + 1 updated |
| `website/.github/workflows/_deploy.yml` | pass `VITE_SITE_ENV` |
| `portal/public/robots.txt`, `portal/firebase.json` | new / `X-Robots-Tag` (Phase 7) |

---

## Verification

**Local (per phase):**

```bash
cd website && npm test
```

```bash
cd website && npm run build && npx serve dist -p 5055
```

Then check `/pricing`, `/faq`, `/privacy`, `/terms` render, `/nonsense` serves 404.html,
and view-source on `/faq` shows all 49 answers plus the FAQPage script. Run
`npm run dev` and confirm the extensionless routes and the restructured hero.

**Post-deploy** — the audit's acceptance table, adjusted for the OG-image deferral:

| # | Test | Expected |
|---|---|---|
| 1 | `curl -I https://3maples.com/nonexistent-test-99999` | 404, not 200 |
| 2 | `https://3maples.com/sitemap.xml` | valid XML, 5 URLs |
| 3 | `https://3maples.com/robots.txt` | contains the `Sitemap:` line |
| 4 | view-source `/`, `name="description"` | present, 150–160 chars |
| 5 | `curl -I https://3maples.com/faq.html` | 301 → `/faq` |
| 6 | `curl -I https://3maples.com/pricing.html` | 301 → `/pricing` |
| 7 | paste `https://3maples.com` into Slack/LinkedIn | image, title and description all render |
| 8 | Rich Results Test on `/` | Organization + SoftwareApplication, no errors |
| 9 | Rich Results Test on `/faq` | FAQPage, 49 questions, no errors |
| 10 | view-source `/`, `<h1>` | "The Landscaper's Operating System", exactly one |
| 11 | `curl -I https://app.3maples.ai/` + `/robots.txt` | `X-Robots-Tag: noindex`, `Disallow: /` |
| 12 | `https://maples-website-dev.web.app/` | `Disallow: /` **and** a `noindex` meta in source |
| 13 | view-source production `/` | **no** `noindex` meta (fail-safe didn't misfire) |
| 14 | PageSpeed Insights on `/` | homepage transfer well under 19 MB |

---

## What this plan does not solve

This is technical hygiene across the five existing pages — it makes the site correctly
indexable, which is the prerequisite for anything else. The ranking surface stays at those
five pages plus brand searches. Adding more pages later is a separate decision; nothing
here blocks it, and the sitemap and head-tag work are generated from a page list, so a new
page picks both up automatically.

Also out of scope: Google Search Console verification needs registrar/DNS access — the
separate message to Bradford at the end of the audit doc. GA4 conversion events
(`signup_click`) are Ron's workstream and already done.
