# FAQ Page + Discourse Community Forum

## Context

The marketing site (`website/`) was in stealth mode with no `/forum` route. We want a public help surface that combines:

1. A curated list of top FAQs (accordion).
2. Full-text search across the knowledgebase.
3. A community forum where users can post questions, get answers from other 3Maples customers, and where we can monitor & moderate.
4. Bot protection and a low-ops solution.

### Why we pivoted from a custom-built forum to Discourse

The original plan was to build the forum from scratch on top of Firestore + Cloud Functions + Firebase Auth, reusing the same Firebase project as the portal so 3Maples customer credentials would work seamlessly. We implemented this, but during integration the project's enforced Firebase **App Check** kept colliding with the website's Cloud Functions:

- Browser → platform `/auth` required a debug-token allow-list every time the App Check UUID rotated.
- Cloud Functions → platform `/auth` was a server-to-server call that can't easily mint an App Check token.
- Estimated remaining work: spam protection, moderation queue UI, email digests, badges, threading — all of which Discourse already does well.

**Cost-benefit tipped toward Discourse.** A $6–10/mo self-hosted Discourse instance gives us a battle-tested forum (used by Cloudflare, Figma, DigitalOcean) with built-in mod tools, trust levels, Akismet spam filtering, email digests, mobile apps, and SSO support. We deleted ~2,500 lines of custom forum infra in favor of pointing users at `community.3maples.ai`.

## Final architecture

| Component | Status | Location |
|---|---|---|
| FAQ accordion + content | ✅ Built | `website/src/content/faqs.json`, `website/src/forum/components/FaqAccordion.tsx` |
| Knowledgebase search (Fuse.js) | ✅ Built | `website/src/forum/components/SearchBar.tsx` |
| Forum threads / replies / moderation | 🆕 External | self-hosted Discourse at `community.3maples.ai` |
| Auth | 🆕 External | Discourse email/password (optionally SSO from portal via Discourse Connect) |
| Spam protection | 🆕 External | Discourse trust levels + Akismet |
| Email notifications | 🆕 External | Discourse digests + mention notifications |
| Search across forum threads | 🆕 External | Discourse's built-in search |

## What lives in the website repo

### Page structure (`/forum`)

- **`website/forum.html`** — static entry HTML carrying the same sticky nav and footer chrome as `index.html` / `pricing.html` (so the page feels native to the marketing site).
- **`website/src/forum/main.tsx`** — minimal React mount, no router, renders `<ForumHome />`.
- **`website/src/forum/ForumHome.tsx`** — single-page React component:
  - H1 "Help & Community" + lead text.
  - Search bar (Fuse.js across the FAQs).
  - "Top questions" — featured FAQs accordion (markdown answers via `react-markdown`).
  - **"Join the 3Maples community forum"** card with `target="_blank"` link to `https://community.3maples.ai` (the `COMMUNITY_URL` constant — update when DNS is live).
- **`website/src/forum/components/ForumLayout.tsx`** — thin wrapper providing the centered content column.
- **`website/src/content/faqs.json`** — source of truth for FAQ entries (`{ id, question, answer, tags, featured }`). Featured entries surface on initial load; the rest appear via search.

### Nav links

Both `index.html` and `pricing.html` include a **Forum** link in the desktop nav and mobile hamburger menu.

### Vite + Firebase Hosting wiring

- `vite.config.ts` adds `forum` as a build input (sits alongside `main` and `pricing`).
- Custom Vite dev plugin `forumDevRewrite` rewrites `/forum` → `/forum.html` for `npm run dev` (so it mirrors the production rewrite locally).
- `firebase.json` adds a single `/forum → /forum.html` Hosting rewrite.

### Tests

- `src/forum/__tests__/FaqAccordion.test.tsx` — renders questions, expands answers, empty-state.
- `src/forum/__tests__/SearchBar.test.tsx` — Fuse.js filters, clears.
- All Firebase / platform / forum-API / App Check tests deleted along with the code they covered.

## Discourse provisioning (one-time)

### 1. Server

Minimum spec per Discourse's official requirements:
- 1 GB RAM (2 GB recommended)
- 1 vCPU
- 20 GB SSD
- Ubuntu 22.04 LTS or 24.04 LTS

Recommended: **DigitalOcean $12/mo droplet** (2 GB / 1 vCPU / 50 GB SSD) → comfortable for the first ~1,000 active users.

### 2. DNS

- Create an A record: `community.3maples.ai` → droplet IP.
- Discourse handles its own Let's Encrypt certificate during install.

### 3. Install

```bash
ssh root@<droplet-ip>
wget -qO- https://get.docker.com/ | sh
mkdir /var/discourse
git clone https://github.com/discourse/discourse_docker.git /var/discourse
cd /var/discourse
./discourse-setup
```

The setup script prompts for: domain, admin email, SMTP credentials (reuse the same Brevo `BREVO_SMTP_USER` / `BREVO_SMTP_PASS` we use for the contact form). Build takes ~10 minutes.

### 4. Brand customization

- **Admin → Customize → Themes → Install** the default Discourse "Air" or "Graceful" theme as a base, or use the Discourse stock theme.
- Override the brand colors to match the website: edit the theme's color palette to use `--accent: #2f9e6b` and `--ink: #2a2546` so the forum's accent green matches `pricing.html` / `forum.html`.
- Replace the favicon and logo with `/favicon.png` from `website/public/`.
- Set the homepage banner copy to match the website's "Community Forum" CTA.

### 5. Categories (initial seed)

- **Announcements** (read-only for users, staff post-only)
- **Questions & Help** (default for new threads)
- **Tips & Tricks** (customer-to-customer)
- **Feature Requests** (link this to a "How we prioritize" pinned post)
- **Bugs & Issues**

### 6. SSO (optional, recommended)

Discourse Connect lets users sign in with their **3Maples portal credentials** instead of registering a separate Discourse account:

- Admin → Settings → **Login** → enable `enable discourse connect`.
- `discourse connect url` → an endpoint on the platform (e.g. `https://api.3maples.ai/auth/discourse-sso`) that:
  1. Verifies the user's Firebase ID token (reuse `firebase_auth.py`).
  2. Returns the SSO payload (signed with the shared secret) per [Discourse Connect spec](https://meta.discourse.org/t/discourse-sso-provider/32974).
- This is a new endpoint we'd need to add to `platform/routers/auth.py`. **Out of scope for v1** — start with native Discourse email/password registration. Add SSO once we have meaningful forum traffic.

### 7. Moderation

- Promote yourself and one or two trusted users to **TL3 (trust level 3) → moderator** in Admin → Users.
- Configure auto-flag thresholds in Admin → Settings → Spam.
- Enable Akismet (free for non-commercial communities, $10/mo otherwise) via the official Discourse plugin.

## Env / secret cleanup vs the original plan

The Discourse pivot **removed all of these env requirements**:

| Removed | Why |
|---|---|
| `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_APP_ID` | Website no longer uses Firebase Auth / Firestore |
| `VITE_PUBLIC_API_URL` | Website no longer calls platform `/auth` |
| `VITE_FIREBASE_APPCHECK_DEBUG_TOKEN` | No App Check needed on website |
| `PLATFORM_API_URL` Cloud Functions secret | No forum endpoints in Functions |

**Still required (unchanged from before this plan):**
- `VITE_RECAPTCHA_V3_SITE_KEY` — contact form
- `BREVO_SMTP_USER`, `BREVO_SMTP_PASS`, `RECAPTCHA_V3_SECRET` — contact form Cloud Function

## Verification

1. `cd website && npm install && npm run build` — confirm Vite build succeeds and emits `dist/forum.html`. Bundle is ~47 KB gzip (down from 568 KB when Firebase was bundled).
2. `npm test` — confirm FaqAccordion and SearchBar tests pass.
3. `npm run dev` → open `http://localhost:5173/forum`:
   - See header + footer matching the marketing pages.
   - See FAQ accordion with top 5 featured questions.
   - Type in the search box → results filter live.
   - Click the "Join the 3Maples community forum" card → opens `community.3maples.ai` in a new tab.
4. After Discourse is provisioned: clicking the card lands on the live forum; register an account; post a test thread; flag it; confirm it ends up in the mod queue.

## Out of scope (deferred)

- Discourse SSO via Discourse Connect (use email/password registration for v1).
- Embedded preview of recent threads on the `/forum` page (Discourse exposes a JSON feed at `community.3maples.ai/latest.json` — we could pull the top 5 threads and render them next to the FAQ, but it adds CORS complexity).
- Backup/restore automation for Discourse (use Discourse's built-in scheduled backups → S3).
- Multi-language / i18n.
