# In-App Customer Support System

**Status:** Phase 1 SHIPPED (2026-07-01, committed + pushed; verified end-to-end in dev). **Phase 2 (Live Chat) code COMPLETE (2026-07-01, backend + portal, 10 new backend tests + 2 new portal tests green, uncommitted).** Remaining for Phase 2: commit/push, deploy the `supportMeta/liveChat` mirror doc (created automatically on first `/livechat` toggle), end-to-end verification (verification step 8). Phase 3 (cutover) not started.

### Implementation notes (Phase 2 — Live Chat)

- **`StaffAvailability`** ([platform/models/staff_availability.py](../../../platform/models/staff_availability.py)) — one doc per staff Slack user (`slack_user_id` unique). Available ⇔ `online == True and expires_at > now`; the `/livechat on` command sets `expires_at = now + AUTO_EXPIRY` (4h safeguard). Registered in `models/__init__.py` + `database.py`.
- **`services/live_chat_availability.py`** — `set_online` / `set_offline` / `is_available` / `status`; `_online_count` uses a raw `{"online": True, "expires_at": {"$gt": now}}` filter (avoids ruff E712 on `== True`). Every toggle calls `_mirror_to_firestore` → `firestore_service.set_live_availability(bool)` → `supportMeta/liveChat`.
- **`/livechat on|off|status`** handled in [platform/routers/slack_events.py](../../../platform/routers/slack_events.py) `_handle_livechat`. Allowlist = `settings.slack_livechat_staff_ids` (comma-separated); non-allowlisted users get an ephemeral refusal with **no** state change. (Unlike `/resolve`, `/livechat` can be run from any channel, so it needs its own authorization.)
- **Live send gate:** `_send_flow` in [platform/routers/support.py](../../../platform/routers/support.py) now refuses `type=live` (409) only when `live_chat_availability.is_available()` is false — server-authoritative. `GET /support/live-availability` returns `{available, staff_online}`.
- **Portal:** `subscribeToLiveAvailability` (supportFirestore) + `getLiveAvailability` (api/support) drive a `liveAvailable` state in `SupportPanel`; the Live Chat composer enables only when staff are online and disables in real time (transcript retained) if they go offline mid-chat. The Phase 1 "always offline" constant is gone.

### Implementation notes (Phase 1 deviations from the plan)

- **Module name:** the Slack bridge lives at `services/slack_support.py` — `services/slack_service.py` was already taken by the ops-notification webhook module.
- **No `slack_sdk`:** implemented with plain `httpx` against the Slack Web API (house style; the SDK's async client would add an `aiohttp` dep and its sync client blocks the event loop). Zero new Python dependencies. Web API calls are form-encoded (only a subset of methods accept JSON).
- **Multipart send is its own route:** `POST /support/conversations/message-with-file` (FastAPI can't accept JSON-or-multipart on one route). `api/support.ts` maps `sendMessageWithFile` to it.
- **DEV marker flag:** driven by the existing `settings.sentry_environment` (no new env flag needed).
- **`firestore_conversation_id`** is a computed property on `SupportConversation` (== Mongo id hex), not a stored field — can't drift.
- **Staff sender names** resolve via cached `users.info` (`users:read` scope — already in the manifest); fallback label "Support staff".
- **`/livechat`** replies with an honest "coming in Phase 2" ephemeral (it's registered in the Slack app already).
- **Test infra:** local-Mongo test suite gained `support_slack_env` / `fake_slack_support` / `fake_firestore_support` conftest fixtures; SlackEventDedupe test rows are cleaned per-test (they persist 7 days via TTL and would otherwise dedupe re-runs).
**Supersedes (at cutover):** [golden-sprouting-adleman.md](golden-sprouting-adleman.md) (Trello feedback → retired only after the new system is production-ready)
**Date:** 2026-06-24 (updated 2026-07-01: two-tab panel UI + Feedback/Support type dropdown, one dedicated Slack channel per type — `#feedback` / `#support` / `#live-chats` — real-time unread badge, staff `/resolve` command, late-reply-to-closed handling)

---

## Context

Today the "Maple Feedback" panel ([portal/src/components/common/FeedbackPanel.tsx](../../../portal/src/components/common/FeedbackPanel.tsx)) is a one-way form that POSTs to `/feedback` ([platform/routers/feedback.py](../../../platform/routers/feedback.py)) and creates a Trello card. There is no reply path — users can send but never hear back in-app.

We are replacing it with a **two-way customer support system** so users can hold an actual conversation with 3Maples support staff, who work entirely from **Slack**. The panel has **two tabs**:

1. **Send Messages** tab (Phase 1) — asynchronous, 48h SLA. A **message-type dropdown with two options — "Feedback" and "Support"** (mirrors the category `<select>` already in `FeedbackPanel`) selects which conversation the user is in. Each type is its **own conversation with its own Slack thread in its own dedicated private channel** — Feedback → **`#feedback`**, Support → **`#support`** — so **no message prefixes are needed**; the channel itself is the triage signal. Because the panel natively carries a Feedback type, it fully absorbs the Trello feedback use case at cutover — with the upgrade that staff can now *reply* to feedback.
2. **Live Chat** tab (Phase 2) — real-time, available **only when a staff member has marked themselves online** via a Slack slash command (`/livechat on|off`). Routed to a dedicated private channel **`#live-chats`**. (No dropdown on this tab — live is its own type.)

Internally the three are one enum: `type: Literal["feedback","support","live"]` — the type alone determines the Slack channel, replacing the earlier `mode` + per-message tag design.

Both tabs: users can attach **PDF / PNG / JPEG**, and **clear the conversation** to start fresh.

### Rollout strategy (dev-first, no production impact)

The existing **Trello "Feedback" panel stays untouched and live in production** throughout development. The new support system ships behind a build flag:

- Keep [FeedbackPanel.tsx](../../../portal/src/components/common/FeedbackPanel.tsx) + its "Feedback" footer tab exactly as-is.
- Add the new `SupportPanel` as a **separate** entry point, rendered only when `VITE_SUPPORT_PANEL_ENABLED` is truthy (set in dev/`.env.development`, **unset in `.env.production`** → never shown in prod).
- **Cutover (later, explicit phase):** flip `VITE_SUPPORT_PANEL_ENABLED` on in prod, validate, then remove `FeedbackPanel` / `feedback.py` / `trello_service.py` and the Trello config keys. Trello retirement is deferred to that phase — **not** Phase 1.

### Confirmed decisions

| Decision | Choice |
|---|---|
| Panel UI | **Two tabs: "Send Messages" + "Live Chat".** Send Messages carries a **message-type dropdown ("Feedback" / "Support")** that switches between two per-type conversations; Live Chat is the third type. |
| Slack channels | **One dedicated private channel per type: `#feedback`, `#support`, `#live-chats`.** Conversation type ⇒ channel; **no `[Feedback]`/`[Support]` message prefixes** — the channel is the triage signal. One Slack thread per user per type. **Channels are created (2026-07-01) and shared by Dev and Prod**: non-production backends prefix the thread-opener with a **`DEV`** marker (e.g. `DEV — …`) so test threads are unmistakable next to real ones. Channel IDs + staff IDs are captured in `platform/.env.local`. |
| Transport | **Firestore for both phases.** Backend is the *sole* Firestore writer (Admin SDK, bypasses rules); portal *only reads* via real-time `onSnapshot`. Replaces 5-min polling with instant push for all three conversation types. |
| Clear conversation | **User side:** a "Start new conversation" action in the panel header (confirmation dialog — it archives history) closes the current Slack thread (posts a note for staff), archives history server-side; next message opens a **fresh** thread + fresh Firestore conversation doc. **Staff side:** `/resolve <customer-email>` in the conversation's channel archives it the same way; the user's panel flips to a "closed by our team" state in real time. |
| Late replies to a closed thread | Archived conversations **keep** `slack_thread_ts`, so a staff reply in a closed thread still resolves. It is **not delivered**; the bot posts an in-thread warning ("closed — the user won't see replies here") so nothing is silently lost. |
| Reply notifications | **Unread badge** on the support entry button **+ email** (via existing Brevo) when staff reply while the user is away. Badge is **real-time**: backend mirrors `unreadForUser` onto the Firestore conversation doc and the portal keeps a lightweight conversation-doc listener even while the panel is closed (REST `GET /support/unread` is the initial/fallback value only). |
| Live-chat availability | **Staff-controlled, not clock-based.** Staff toggle online/offline via a Slack slash command (`/livechat on\|off\|status`); live chat is "available" whenever ≥1 staff is online. Auto-expiry safeguard prevents a forgotten "on". |
| Trello feedback | **Kept live in prod during dev; retired only at cutover.** New `SupportPanel` is dev-only behind `VITE_SUPPORT_PANEL_ENABLED`. |

### Why Firestore (not MongoDB polling)

The portal is already a Firebase-authenticated client with App Check ([portal/src/firebase.ts](../../../portal/src/firebase.ts)). A Firestore `onSnapshot` listener is push-based, charges only on change, and gives instant updates with no polling infra — strictly better than a 5-min poll, and it makes Phase 2 (live chat) almost free since the real-time channel already exists. The backend writes via the Admin SDK (bypasses security rules), so the client never needs write access.

---

## Architecture

```
USER MESSAGE:
  Portal ──REST(auth+AppCheck)──► POST /support/conversations/message
                                    {type: feedback|support|live, text}
                                      │
                                      ├─► slack_service.post → channel by type (#feedback | #support | #live-chats), open/reply in thread
                                      ├─► firestore_service.write_message  ──onSnapshot──► Portal UI
                                      └─► MongoDB SupportConversation (routing source of truth)

STAFF REPLY (in Slack thread):
  Slack Events API ──HMAC-signed──► POST /slack/events  (public, no Firebase auth)
                                      │ (ack <3s, process async, dedupe by event_id)
                                      ├─► lookup conversation by (channel, thread_ts)
                                      ├─► firestore_service.write_message  ──onSnapshot──► Portal UI
                                      └─► support_notifications (unread++ / Brevo away-email)

STAFF CLOSE (Phase 1):
  Slack /resolve <email> ──signed──► POST /slack/commands
                                      ├─► archive SupportConversation (Mongo, thread_ts kept)
                                      ├─► firestore: conversation status → "archived" ──onSnapshot──► panel shows "closed by our team"
                                      └─► post "Closed by <staff>" note in the Slack thread + ephemeral confirmation

STAFF AVAILABILITY (Phase 2):
  Slack /livechat on|off ──signed──► POST /slack/commands
                                      ├─► upsert StaffAvailability (MongoDB)
                                      └─► mirror flag → supportMeta/liveChat ──onSnapshot──► Live Chat tab on/off
```

- **MongoDB** = source of truth for routing, auth/tenant scoping, unread counts, archival. The Slack webhook has no Firebase identity, so the `thread_ts → conversation → company/user` lookup *must* live server-side.
- **Firestore** = client real-time read surface only. Backend-written, client-read.
- Patterns reused: the **Stripe webhook** ([platform/routers/stripe_webhooks.py](../../../platform/routers/stripe_webhooks.py)) for raw-body + HMAC + public mount + idempotency; **company logo** ([platform/services/company_logo.py](../../../platform/services/company_logo.py)) for Firebase Storage upload + tokenized download URL.

---

## Data model

### MongoDB — `SupportConversation` (new Beanie `Document`)

Register in [platform/database.py](../../../platform/database.py) `init_db()` and [platform/models/__init__.py](../../../platform/models/__init__.py) (follow the existing model-registration pattern). Use the `@before_event([Replace, Insert])` timestamp pattern from [platform/models/user.py](../../../platform/models/user.py).

Fields: `company: PydanticObjectId`, `user_id: PydanticObjectId`, `user_firebase_uid: str`, `user_email: str`, `type: Literal["feedback","support","live"]` (determines the Slack channel; `feedback`/`support` are async-48h-SLA, `live` is real-time), `slack_channel_id: str`, `slack_thread_ts: str | None`, `status: Literal["open","archived"]`, `firestore_conversation_id: str` (deterministic = Mongo `_id` hex), `last_message_at`, `last_message_preview`, `last_sender`, `unread_for_user: int`, `user_last_seen_at`, timestamps.

Indexes:
- Unique compound **`(slack_channel_id, slack_thread_ts)`** (partial — only where `slack_thread_ts` set) → inbound reply routing.
- `(company, user_id, type, status)` → "current open conversation" lookup (one open conversation per user per type).
- `(user_id, status)` → archive listing.

### MongoDB — `SlackEventDedupe` (new) — idempotency

`event_id: str` unique index. Slack retries on >3s ack; dedupe like `BillingEvent.stripe_event_id`.

### MongoDB — `StaffAvailability` (new) — live-chat online state

One doc per staff Slack user: `slack_user_id: str` (unique), `display_name: str`, `online: bool`, `since: datetime`, `expires_at: datetime`. **Live chat is available ⇔ at least one doc has `online == true and expires_at > now`.** `/livechat on` upserts `online=true` with `expires_at = now + AUTO_EXPIRY` (e.g. 4h safeguard); `/livechat off` sets `online=false`. This per-staff set means one person stepping away doesn't close live chat if another is still online.

### Firestore — read surface

```
supportConversations/{conversationId}        # doc id == firestore_conversation_id
  companyId, userId (Firebase UID), type ("feedback"|"support"|"live"), status, updatedAt
  unreadForUser: int                          # mirrored from Mongo on every staff write / seen — real-time badge source
  messages/{messageId}                        # immutable append log subcollection
    sender: "user"|"staff", senderName, text, createdAt (server ts), slackTs
    attachments: [{ storagePath, downloadUrl, contentType, fileName, sizeBytes }]

supportMeta/liveChat                          # single shared doc — live-chat availability mirror
  available: bool                             # ⇔ ≥1 StaffAvailability online & unexpired
  updatedAt: timestamp
```

The `supportMeta/liveChat` doc lets every open Live Chat tab flip on/off **in real time** via the same `onSnapshot` mechanism. It's globally readable (no PII) and changes only a handful of times a day, so the "many listeners on one doc" fan-out is safe (the hot-doc concern only bites at >~1 write/sec).

`userId` on the conversation doc is the **Firebase UID** (so security rules match `request.auth.uid` directly). On "clear": flip old doc `status:"archived"` (history stays readable) + create a fresh conversation doc.

---

## Firestore security rules + App Check

Read-only client, scoped per Firebase UID (writes are backend-only):

```
match /supportConversations/{cid} {
  allow read:  if request.auth != null && resource.data.userId == request.auth.uid;
  allow write: if false;
  match /messages/{mid} {
    allow read:  if request.auth != null &&
                 get(/databases/$(db)/documents/supportConversations/$(cid)).data.userId == request.auth.uid;
    allow write: if false;
  }
}
match /supportMeta/{doc} {        // live-chat availability mirror — no PII
  allow read:  if request.auth != null;
  allow write: if false;
}
```

- **Enable Firestore (Native mode)** in the `fieldservice-portal-tangz` project — not yet used anywhere. `firebase-admin` already bundles `google-cloud-firestore`, so no new Python dep for Firestore.
- **Enable App Check enforcement for Cloud Firestore** in the console. Reuse the existing `firebaseApp` + `firebaseAppCheck` from [portal/src/firebase.ts](../../../portal/src/firebase.ts) (do **not** init a second app) so the Firestore Web SDK auto-attaches App Check tokens. Gate the first `onSnapshot` on auth + App Check readiness (`waitForAuthReady`) to avoid a silent listener failure — the team previously hit App Check pain (Discourse/Cloud Functions); staged-rollout the rules in dev first.
- Indexes: the `orderBy(createdAt, desc).limit(10)` + `startAfter` pagination needs only the auto single-field index. No composite index (no `where` alongside the `orderBy`) — document this so none is added needlessly.
- **Badge listener query:** the always-on unread listener is `query(supportConversations, where("userId","==",uid))`. The `resource.data.userId == request.auth.uid` rule above already admits exactly this query (Firestore proves every possible result satisfies the rule), and it needs only the auto single-field index on `userId`. No rule or index change required — noted here so nobody "fixes" it.

---

## Slack app setup (one app, three channels: `#feedback`, `#support`, `#live-chats`)

- **Bot scopes:** `chat:write`, `chat:write.customize` (post per-customer username), `files:write`, `files:read`, `groups:history`, `groups:read`, `users:read`, `commands` (auto-added with the slash command). Channels are **private** (customer PII) → use `groups:*` + subscribe to `message.groups`; the bot must be invited to each channel.
- **Event Subscriptions:** request URL `https://api.3maples.ai/slack/events` (Render host). Echo the `url_verification` challenge **before** any auth. Subscribe to `message.groups` (carries text replies *and* file shares via `subtype:"file_share"` + `files[]`).
- **Slash commands:** register `/resolve` (Phase 1) and `/livechat` (Phase 2), both with request URL `https://api.3maples.ai/slack/commands`. Slack POSTs `application/x-www-form-urlencoded` (`command`, `text`, `user_id`, `user_name`, `channel_id`), signed with the **same signing secret** (same HMAC verification).
  - **`/resolve` needs an argument** — slash-command payloads carry `channel_id` but **no `thread_ts`** (even when typed inside a thread), so a bare command can't identify the conversation. `/resolve <customer-email>` closes that user's open conversation **in the channel it's invoked from** (channel ⇒ type); bare `/resolve` replies with an ephemeral list of the channel's open conversations (email + last-message preview) to copy from. Invoking it outside the three configured channels gets an ephemeral "run this in a support channel". Channel membership *is* the staff authorization — the channels are private.
  - `/livechat` handles `on` / `off` / `status` (see the live-availability section).
- **Signature verification** (mirror Stripe, shared by both `/slack/events` and `/slack/commands`): raw `await request.body()`; reject timestamp >5 min old (replay guard); HMAC-SHA256 of `v0:{ts}:{body}` vs `X-Slack-Signature`, constant-time compare.
- **Channel routing:** config holds `SLACK_FEEDBACK_CHANNEL_ID` + `SLACK_SUPPORT_CHANNEL_ID` + `SLACK_LIVE_CHAT_CHANNEL_ID` (a `type → channel_id` map in one place); outbound posts pick the channel from the conversation `type`, inbound webhook resolves `event.channel` back to the type. Channel names carry no PII requirement — the **private** setting does; all three are private and the bot is invited to each.
- **Bot-echo filter (critical — prevents loops):** drop events with `bot_id`, `user == bot_user_id` (cache from `auth.test` at startup), drop-subtypes (`bot_message`, `message_changed`, `message_deleted`, joins…), missing `thread_ts`, or a `thread_ts` that doesn't resolve to a known conversation. Backend-posted user messages echo back as events — this filter is what stops double-writes.
- **Dev marker (shared channels):** Dev and Prod share the three channels. When the backend runs in a non-production environment, `slack_service` prefixes the **thread-opener** with `DEV — ` (opener only; the thread groups everything under it). Driven by an environment flag in `config.py` (add one if none exists).

### App creation runbook

**Stage A — create + install (no code required) — ✅ COMPLETED 2026-07-01** (app created + installed, bot token + signing secret in `platform/.env.local`, bot invited to all three channels):
1. <https://api.slack.com/apps> → **Create New App** → **From an app manifest** → pick the staff workspace → paste the manifest below **without the `event_subscriptions` block** (Slack refuses to save an events URL it can't verify, and `/slack/events` doesn't exist yet).
2. Create, then **Install App → Install to Workspace → Allow** (needs workspace app-install approval if restricted).
3. **Basic Information → Signing Secret** → `SLACK_SIGNING_SECRET` in `platform/.env.local`.
4. **OAuth & Permissions → Bot User OAuth Token** (`xoxb-…`) → `SLACK_BOT_TOKEN` in `platform/.env.local`.
5. In each of the three private channels: `/invite @3maples-support` — private channels are invisible to the bot until invited.

**Stage B — after `/slack/events` + `/slack/commands` are implemented and publicly reachable** (ngrok → local, or the Render dev host):
6. **Event Subscriptions → Enable** → Request URL `https://<host>/slack/events` → must flip to **Verified** (the endpoint echoes the `url_verification` challenge) → **Subscribe to bot events → `message.groups`** → Save.
7. Slash-command URLs were registered by the manifest; if using ngrok, update both commands' URLs to the current tunnel host (command URLs are *not* challenge-verified — they just need to respond when used).
8. If any scope changed since install, Slack banners a **reinstall** prompt — accept it.

**Stage C — in-thread Resolve message shortcut** (Slack blocks *slash commands* inside threads with "/resolve is not supported in threads", so `/resolve` must be typed in the channel's main box; the message shortcut is the thread-friendly alternative and needs no email argument):
9. **Interactivity & Shortcuts → Interactivity → On** → **Request URL** `https://<host>/slack/interactions` (same HMAC gate; not challenge-verified).
10. **Create New Shortcut → On messages** → Name "Resolve conversation", short description, **Callback ID `resolve_conversation`** (must match `RESOLVE_SHORTCUT_CALLBACK_ID` in `routers/slack_events.py`) → Save.
11. Staff then use it from any message in a customer's thread via the message `⋯` menu → "Resolve conversation": the handler resolves `(channel, thread_ts)` → conversation → the same atomic archive + "closed by" note + Firestore flip as `/resolve`, and confirms back via the interaction's `response_url`. `/resolve <email>` stays as the main-channel fallback.

```yaml
display_information:
  name: "3Maples Support"
  description: "Two-way customer support bridge (portal <-> Slack)"
features:
  bot_user:
    display_name: "3maples-support"
    always_online: true
  slash_commands:
    - command: /resolve
      # Command URLs are format-validated at save but NOT reachability-checked,
      # so register the prod URL now; repoint to the dev host/tunnel in Stage B.
      url: "https://api.3maples.ai/slack/commands"
      description: "Close a customer's open conversation in this channel"
      usage_hint: "customer@email.com"
      should_escape: false
    - command: /livechat
      url: "https://api.3maples.ai/slack/commands"
      description: "Toggle your live-chat availability"
      usage_hint: "on | off | status"
      should_escape: false
oauth_config:
  scopes:
    bot:
      - chat:write
      - chat:write.customize
      - files:write
      - files:read
      - groups:history
      - groups:read
      - users:read
      - commands
settings:
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

**Single-app URL constraint:** a Slack app has **one** events URL and one URL per command — so only one environment receives events at a time. That's fine while the feature is dev-only (URLs point at dev). At Phase 3 cutover, repoint the URLs to `https://api.3maples.ai`; if active development continues past cutover, create a second app ("3Maples Support DEV") with its own token/secret for the dev backend — the unknown-thread + bot-echo filters already make the two apps ignore each other's threads in the shared channels.

---

## Backend — endpoints & services

**New router [platform/routers/support.py](../../../platform/routers/support.py)** (authenticated; mount in [platform/main.py](../../../platform/main.py) with `protected_route_dependencies` like `feedback_router`; resolve user/company via `require_authenticated_user` from [platform/dependencies.py](../../../platform/dependencies.py); rate-limit via `auth_rate_limiter` from [platform/services/request_protection.py](../../../platform/services/request_protection.py), key `support:send:{uid}`):

- `POST /support/conversations/message` — JSON `{type, text}` or multipart with file. `type` ∈ `feedback|support|live` (422 otherwise). Resolve/create the open conversation for that type, open a Slack thread in the **type's channel** if none, post to Slack (no prefix — the channel is the signal), write the user message to Firestore. (Message surfaces via the listener.)
- `POST /support/conversations/clear` — `{type}`. Post "closed by user" note to Slack thread, set Mongo `status=archived` (**keep `slack_thread_ts`** — it's what lets a late staff reply still resolve for the in-thread warning), flip Firestore doc to `archived`.
- `GET /support/conversations/current?type=` — returns `{firestore_conversation_id, type, status}` so the portal knows which Firestore doc to attach to. (Messages are read from Firestore, **not** REST.)
- `GET /support/unread` — `{unread: {feedback: int, support: int, live: int}}` per open conversation (badge **initial/fallback** value; live updates come from the Firestore conversation-doc `unreadForUser` mirror).
- `POST /support/conversations/seen` — `{type}`. Zero `unread_for_user`, stamp `user_last_seen_at`.
- `GET /support/live-availability` — returns `{available: bool, staff_online: int}` derived from the `StaffAvailability` store (Phase 2). Server-authoritative; the portal also gets real-time updates via the `supportMeta/liveChat` listener.

**Public Slack endpoints [platform/routers/slack_events.py](../../../platform/routers/slack_events.py)** (mounted bare, no auth deps, like `stripe_webhooks_router`):
- `POST /slack/events` — signature + timestamp verify, `url_verification` echo, **ack within 3s then process async** (`BackgroundTasks`), dedupe on `event_id`, bot-echo filter, route by `(channel, thread_ts)`, write staff message to Firestore, trigger notifications. **If the resolved conversation is `archived`** (user cleared it or staff `/resolve`d it): do **not** deliver — post an in-thread bot note instead ("⚠️ This conversation was closed — the user won't see replies here. They'll reach you in a new thread if they write again."), throttled to once per thread per hour so a multi-message reply doesn't stack warnings.
- `POST /slack/commands` — signature-verify (shared helper), dispatch on `command`, respond ephemerally within 3s:
  - **`/resolve` (Phase 1):** validate the invoking channel is one of the three configured ids (⇒ type); parse `text` as the customer email; find that user's **open** conversation of that type → archive Mongo (keep `thread_ts`) + Firestore, post "Closed by <staff display name>" in the thread, ephemeral confirmation to the invoker. Bare `/resolve` → ephemeral list of the channel's open conversations. No match → ephemeral "no open conversation for that email".
  - **`/livechat` (Phase 2):** parse `text` (`on`/`off`/`status`), restrict to the staff allowlist (`user_id`). Upsert `StaffAvailability` for `user_id`, recompute global availability, mirror to `supportMeta/liveChat` in Firestore, and return an **ephemeral** confirmation (`{"response_type":"ephemeral","text":"✅ Live chat is now ONLINE (you + N others)"}`).

**New services:**
- `services/slack_service.py` — wraps `slack_sdk` (new `requirements.txt` dep): `open_thread`, `post_message`, `upload_file` (`files.uploadV2`), `download_file` (bot-token `Authorization` header — **required**, else Slack returns an HTML login page), `verify_signature`, cached `bot_user_id`.
- `services/firestore_service.py` — lazy singleton `firebase_admin.firestore.client()` (guard with `initialize_firebase_admin()` like `company_logo.py`): `write_message`, `upsert_conversation`, `archive_conversation`, `set_unread(conversation_id, n)` (mirrors Mongo `unread_for_user` onto the conversation doc — called on staff write and on `seen`). All Admin-SDK writes centralized here.
- `services/support_attachments.py` — validate (allow-list `image/png`, `image/jpeg`, `application/pdf`; size cap; image path reuses Pillow validation from `company_logo.py`; PDF = magic-byte `%PDF-` + size), store to Firebase Storage at `companies/{company_id}/support/{conversation_id}/{ts}-{uuid}.{ext}` reusing the tokenized-URL helpers from `company_logo.py`. Validate **both** directions (staff can attach anything in Slack).
- `services/support_notifications.py` — `notify_staff_reply`: increment unread; if user away (`now - user_last_seen_at > threshold`) send a Brevo email via [platform/services/brevo_email.py](../../../platform/services/brevo_email.py) with an app deep-link; throttle to one email per conversation per quiet window.
- `services/live_chat_availability.py` — `set_online(slack_user_id, name)` / `set_offline(...)` / `is_available() -> bool` / `status()` over the `StaffAvailability` collection (treating `expires_at <= now` as offline), and `_mirror_to_firestore()` to keep `supportMeta/liveChat.available` in sync after every change.

**Config** ([platform/config.py](../../../platform/config.py)): add `slack_bot_token`, `slack_signing_secret`, `slack_feedback_channel_id`, `slack_support_channel_id`, `slack_live_chat_channel_id`, `slack_livechat_staff_ids` (comma-separated allowlist), plus `.env`/`.env.example` entries. *(Channel IDs and staff IDs are already captured in `platform/.env.local` — 2026-07-01; bot token + signing secret land there at app creation, Stage A of the runbook.)* Frontend: add `VITE_SUPPORT_PANEL_ENABLED` (dev-on / prod-unset) to `.env.example`, `.env.development`; leave it out of `.env.production`.

### Attachment round-trip

- **User → :** validate → store to Storage → `files.uploadV2` into the thread (upload bytes directly, don't make Slack fetch the token URL) → write Firestore message with `attachments[]`. Order for resilience: Storage before Slack; if Slack fails, still write Firestore + log.
- **Staff → :** Events `files[]` → download via `httpx` with bot-token header → validate bytes → store to Storage → write Firestore. Portal renders images via `<img>`, PDFs via a `target="_blank" rel="noopener"` link.

---

## Frontend

- **`portal/src/firebase.ts`** — add `getFirestore(firebaseApp)`, export `firestoreDb` (reuse existing app so Auth + App Check carry over).
- **`portal/src/api/support.ts`** (new) — `apiRequest` wrappers: `sendMessage({type, text})`, `sendMessageWithFile` (FormData, same fields + file), `clearConversation(type)`, `getCurrentConversation(type)`, `getUnread`, `markSeen(type)`, `getLiveAvailability`. Export `type SupportConversationType = "feedback" | "support" | "live"`. Same shape as [portal/src/api/feedback.ts](../../../portal/src/api/feedback.ts).
- **`SupportPanel` component** (new) added as a **separate, dev-only** entry point — **does not touch `FeedbackPanel`**. In [portal/src/components/Layout/AiPanel.tsx](../../../portal/src/components/Layout/AiPanel.tsx) / [portal/src/components/Layout/PortalLayout.tsx](../../../portal/src/components/Layout/PortalLayout.tsx), keep the existing "Feedback" tab + `FeedbackPanel` untouched, and add a **new "Support (beta)" footer tab** that renders only when `import.meta.env.VITE_SUPPORT_PANEL_ENABLED` is truthy. The new tab carries the unread badge. (At cutover, the Feedback tab/panel are removed and Support becomes the sole entry.) `SupportPanel` keeps the same `open`/`onClose` contract.
  - **Two in-panel tabs** — **"Send Messages"** (types `feedback`/`support`) and **"Live Chat"** (type `live`), styled like the existing footer-tab pattern in `PortalLayout.tsx` (`mapleNavFooter`). Each tab shows its own unread dot (Send Messages = feedback + support summed; Live Chat = live) — per-conversation `unread_for_user` exists in Mongo and mirrors to Firestore.
  - **Send Messages tab** — a **message-type dropdown ("Feedback" / "Support")** sits above the message list, reusing the labeled-`<select>` pattern from `FeedbackPanel.tsx`'s category picker. The selection **switches the active conversation**: each type has its own thread/history, so changing the dropdown detaches the current `messages` listener, calls `getCurrentConversation(newType)` + `markSeen(newType)`, and attaches the new listener — same mechanics as a tab switch. Default selection: "Support". Show the type's unread count next to each dropdown option so a pending Feedback reply isn't invisible while viewing Support.
  - **Live Chat tab** — no dropdown. Tab disabled + "Support staff are offline right now — send us a message instead" note when no staff are online; availability comes from a `supportMeta/liveChat` `onSnapshot` listener (flips in real time when staff `/livechat on|off`), with `getLiveAvailability()` as the initial/fallback value. If availability flips off **mid-conversation**, keep the transcript visible but disable the composer with the same note (and the backend 409 on a raced send is surfaced as that note, not a generic error).
  - **Message list** — `getCurrentConversation(type)` → attach `onSnapshot` on `messages` `orderBy(createdAt desc).limit(10)`, reversed for display; detach on unmount, tab switch, dropdown switch, or panel close.
  - **Lazy load older** — one-shot `getDocs(startAfter(oldestDoc).limit(10))` on scroll-to-top, prepend (separate from the live listener).
  - **Composer** — textarea + attach (reuse hidden-input + chip UX from [portal/src/components/onboarding/CsvUploadStep.tsx](../../../portal/src/components/onboarding/CsvUploadStep.tsx), `accept="image/png,image/jpeg,application/pdf"`). Optional optimistic append de-duped by `slackTs`.
  - **Clear** — an explicit **"Start new conversation" button in the panel header** (e.g. a labeled icon button, visible whenever the active conversation has messages) opens a **confirmation dialog** ("This closes the current conversation and starts fresh — your history won't be shown again. Continue?"); on confirm, `clearConversation(type)` for the active conversation (active tab + dropdown selection), detach listener, refetch current.
  - **Closed by staff** — the conversation-doc `onSnapshot` also watches `status`; if it flips to `archived` while the user is viewing (staff ran `/resolve`), keep the transcript visible, disable the composer, and show a banner: "This conversation was closed by our support team — send a new message to start a fresh one." The next send creates a fresh conversation via the normal open-conversation resolution.
  - **Unread badge** — real-time: an always-mounted `onSnapshot` on `query(supportConversations, where("userId","==",uid))` (attached at layout level while `VITE_SUPPORT_PANEL_ENABLED`, not just while the panel is open) sums `unreadForUser` across types for the footer-tab badge (and provides the per-type counts for the in-panel dots); `getUnread()` is the pre-listener initial value. `markSeen(type)` on viewing a conversation zeroes it (server zeroes Mongo + mirrors 0 to Firestore).
- Reuse chat-message rendering patterns already in `AiPanel.tsx`.

---

## Live-chat availability — staff-controlled via Slack (Phase 2)

Availability is driven by **staff explicitly going online/offline**, not by a clock.

- **Control surface:** `/livechat on` / `/livechat off` / `/livechat status` slash command → `POST /slack/commands` (signed). Each staff toggles their *own* `StaffAvailability` entry; **live chat is available ⇔ ≥1 entry is `online` and unexpired** — so a single staff doing `/livechat on` enables the feature, and it only goes offline once *all* online staff are `off`/expired. (Currently 2 staff, but the set-based design needs no change as the team grows.)
- **Staff allowlist (locked):** `/livechat` is restricted to a configured `SLACK_LIVECHAT_STAFF_IDS` allowlist (the 2 staff Slack user IDs initially) — anyone else gets an ephemeral "not authorized" reply and no state change. Add/remove IDs in config as the team changes.
- **Auto-expiry safeguard:** `on` sets `expires_at = now + AUTO_EXPIRY` (e.g. 4h). A forgotten `on` silently lapses to offline rather than leaving live chat falsely open overnight. (Optional refinement: tie to Slack `presence_change` events to auto-offline on Slack logout — defer.)
- **Real-time to the portal:** every toggle mirrors the global flag into the Firestore `supportMeta/liveChat` doc; the Live Chat tab listens via `onSnapshot` and flips instantly. `GET /support/live-availability` is the REST fallback / initial value.
- **Server-authoritative:** the backend **refuses** `type=live` sends when no staff are online (409/422) — the client availability flag is advisory UX, never the gate.

---

## Phasing

**Phase 1 (Async) — builds the entire shared foundation, dev-only:**
- `SupportConversation` + `SlackEventDedupe` models + indexes; Firestore enablement + rules + App Check.
- Services: `slack_service`, `firestore_service`, `support_attachments`, `support_notifications`.
- Slack app + the `#feedback` and `#support` channels + `/slack/events` webhook (signature, challenge, 3s ack, dedupe, echo filter, channel→type routing, archived-thread reply warning).
- `/slack/commands` endpoint with the **`/resolve` staff command** (close-by-email, open-conversation listing, "Closed by <staff>" thread note).
- Authenticated REST: message / clear / current / unread / seen.
- Portal `SupportPanel` with the **Send Messages tab** (message-type dropdown Feedback/Support), `onSnapshot` listener (real-time even in async), lazy load, attachments, real-time unread badge (conversation-doc listener), Brevo away-email — **rendered only behind `VITE_SUPPORT_PANEL_ENABLED`; Trello "Feedback" panel left fully intact and live in prod.** The Live Chat tab is present but shows the offline state in Phase 1 (availability is always false until Phase 2 ships the toggle).

**Phase 2 (Live) adds only:**
- The third Slack channel `#live-chats` + its config id (webhook already resolves `event.channel` → type).
- `type="live"` through the already type-driven model/endpoints.
- `StaffAvailability` model + the `/livechat` command (the `/slack/commands` endpoint already exists from Phase 1's `/resolve`) + `live_chat_availability` service + `supportMeta/liveChat` mirror + `GET /support/live-availability`.
- The Live Chat tab goes live: real-time availability listener enables it, plus the server-side live-send refusal and the mid-chat "staff went offline" composer-disable state.
- Optional presence ("agent typing") — defer unless needed.

**Phase 3 (Cutover) — only once the above is validated in prod:**
- Flip `VITE_SUPPORT_PANEL_ENABLED` on in production; soak.
- Remove `FeedbackPanel`, `feedback.py`, `trello_service.py`, `api/feedback.ts`, the "Feedback" footer tab, and the Trello config keys. Promote "Support" to the sole entry point — the Send Messages tab's **"Feedback" type is the direct replacement** for the Trello form (its three Trello categories — general feedback / report issue / feature request — collapse into the single "Feedback" type; the distinction lives in the message text, and "report issue" traffic naturally belongs under "Support" anyway).

---

## Files to create / modify

**Create (backend):** `routers/support.py`, `routers/slack_events.py` (events **+** `/slack/commands`), `services/slack_service.py`, `services/firestore_service.py`, `services/support_attachments.py`, `services/support_notifications.py`, `services/live_chat_availability.py` (P2), `models/support_conversation.py`, `models/slack_event_dedupe.py`, `models/staff_availability.py` (P2).
**Modify (backend):** `config.py`, `database.py`, `models/__init__.py`, `main.py`, `requirements.txt` (+`slack_sdk`), `.env` / `.env.example`. **Leave `routers/feedback.py` + `services/trello_service.py` untouched** (retired in Phase 3).
**Create (frontend):** `src/api/support.ts`, `src/components/common/SupportPanel.tsx`.
**Modify (frontend):** `src/firebase.ts`, `src/components/Layout/AiPanel.tsx`, `src/components/Layout/PortalLayout.tsx` (add the dev-only "Support (beta)" tab), `.env.example` / `.env.development` (+`VITE_SUPPORT_PANEL_ENABLED`). **Keep `FeedbackPanel.tsx` + `api/feedback.ts`** (removed in Phase 3).
**Infra:** `firestore.rules` + `firestore.indexes.json` (portal Firebase project), Firestore enablement, App Check enforcement, Slack app (+ `/resolve` and `/livechat` slash commands), Render env vars.

---

## Risks / gotchas

- **3s ack** — verify signature + dedupe synchronously, return 200, then process in a background task; Slack disables endpoints that ack slowly and retries with the same `event_id` (dedupe via Mongo unique index, **not** the in-process rate limiter, which doesn't span Render instances).
- **Bot-echo loops** — the backend posts user messages to Slack; without the bot-id/subtype/own-user filter every user message double-writes and can loop. Single most important webhook guard.
- **Slack private-file download** needs `Authorization: Bearer {bot_token}` or you get an HTML login page; validate downloaded bytes before storing.
- **App Check + Firestore** — enforce in console; reuse the existing app + debug-token wiring; gate first listener on readiness; stage rules in dev before prod (team hit App Check pain before).
- **Forgotten `/livechat on`** — without the auto-expiry safeguard, live chat stays falsely "available" and users get silence. The `expires_at` lapse is the backstop; the slash command also needs the same <3s ack as events.
- **File validation** both directions; PNG/JPEG/PDF allow-list + size cap.
- **Webhook auth = signature only** (no Firebase token); 5-min replay window is the gate. Must NOT sit behind App Check/Firebase, like the Stripe webhook.
- **Two "Feedback" surfaces during dev** — while `VITE_SUPPORT_PANEL_ENABLED` is on in dev, both the legacy "Feedback" footer tab (Trello) and the Support panel's "Feedback" dropdown type exist. That's dev-only and resolves at Phase 3 cutover, but keep the dev footer label "Support (beta)" (not "Messages") so testers don't conflate the two.
- **Badge listener lifetime** — the unread `onSnapshot` lives at layout level (mounts with the portal, not the panel), so remember to tear it down on logout with the rest of the Firebase listeners.
- **Thread opener must carry the customer email** — `/resolve <email>` is keyed on email, so the bot's thread-opening message must include it (along with company/user context staff need anyway). Otherwise staff have nothing to copy into the command.
- **`/resolve` races a user send** — if the user sends at the same moment staff close, the send may recreate/reuse state mid-archive. Archive should be a single atomic Mongo update on the open doc (`find_one_and_update(status="open" → "archived")`); a user send that loses the race simply finds no open conversation and starts a fresh one, which is the desired outcome anyway.

---

## Testing (TDD — write tests first)

**Backend (pytest, `FIREBASE_AUTH_DISABLED=true` + `X-Test-Email` per [platform/tests/conftest.py](../../../platform/tests/conftest.py); monkeypatch `slack_service`/`firestore_service`/`brevo_email`, mock `httpx`):**
- `test_support_send_message.py` — opens/reuses conversation per type; thread_ts persisted then reused; Slack + Firestore called; **`type=feedback` posts to the feedback channel id and `type=support` to the support channel id (no prefix on the text)**; invalid/missing `type` → 422; feedback and support conversations for the same user stay separate (distinct threads).
- `test_slack_webhook_signature.py` — valid HMAC accepted; bad/expired rejected; `url_verification` echoes challenge.
- `test_slack_webhook_routing.py` — threaded reply routes to right company **and right conversation type per source channel (feedback vs support vs live-chats)**; bot/own-user/subtype/unknown-thread/unknown-channel dropped; duplicate `event_id` deduped.
- `test_slack_file_roundtrip.py` — staff file → download → validate → Storage → Firestore attachment ref.
- `test_support_clear.py` — archives Mongo + Firestore (**`slack_thread_ts` kept on the archived doc**), posts note, next message opens fresh thread.
- `test_support_closed_thread_replies.py` — staff reply to an archived conversation's thread is **not** written to Firestore and does **not** increment unread; the bot posts the in-thread warning instead; warning throttled (second reply within the window → no second warning).
- `test_resolve_command.py` — `/resolve <email>` from the support channel archives that user's open support conversation (Mongo + Firestore), posts the "Closed by" thread note, returns ephemeral confirmation; bare `/resolve` lists open conversations; unknown email → ephemeral error, no state change; invoked from a non-support channel → refused; bad signature rejected; the user's next send opens a fresh conversation.
- `test_support_unread_and_seen.py` — staff write increments unread **and mirrors the count to the Firestore conversation doc** (mock); `seen` zeroes both; away → one Brevo email.
- `test_livechat_command.py` (Phase 2) — `/livechat on` marks staff online + flips global availability + mirrors to Firestore (mock); `off` clears; an expired `StaffAvailability` counts as offline; bad signature rejected; **non-allowlisted user rejected with no state change**; **2-staff case: either one `on` → available; available stays true until both are `off`**; `type=live` send refused (409/422) when no staff online.

**Frontend (vitest + RTL; mock `firebase/firestore` `onSnapshot` + `api/support.ts`):**
- `SupportPanel.test.tsx` — renders messages; **tab switch (Send Messages ↔ Live Chat) swaps listeners**; **message-type dropdown defaults to "Support" and switching it swaps to the other type's conversation (listener detached/re-attached, correct `type` passed on send)**; composer sends; **"Start new conversation" button shows the confirmation dialog and only clears the active conversation on confirm**; **a conversation-doc snapshot flipping `status` to `archived` shows the "closed by our support team" banner and disables the composer**; lazy-load fetches older; Live Chat tab disabled when unavailable, and composer disables (transcript stays) when availability flips off mid-chat.
- Unread badge seeds from `getUnread`, updates when a conversation-doc snapshot's `unreadForUser` changes; per-type dots (tab + dropdown options) reflect their own type; viewing a conversation calls `markSeen(type)` and clears its dot.
- Attachment picker per `CsvUploadStep.test.tsx`.

## Verification (end-to-end)

1. **Local backend gates:** `cd platform && ./run_mypy.sh && ./run_ruff.sh && ./run_tests.sh tests/test_support_*.py tests/test_slack_*.py`.
2. **Slack handshake:** point a Slack app dev event-URL (or ngrok → local) at `/slack/events`; confirm the `url_verification` challenge succeeds and a signed test event 200s.
3. **Round-trip (dev):** from the Send Messages tab send one message as type "Support" and one as "Feedback" → confirm they land as **separate threads in the correct channels** (`#support` / `#feedback`, no prefixes) → reply in each thread from Slack → confirm each reply appears in the matching dropdown conversation via the listener with no refresh. Repeat with a PNG and a PDF both directions.
4. **Clear (user):** use the "Start new conversation" button (confirm the dialog appears) → confirm the Slack thread gets the "closed" note and the next message starts a new thread. Then **reply from Slack in the old (closed) thread** → confirm the reply does *not* appear in the panel and the bot posts the "closed — user won't see this" warning in-thread.
4b. **Close (staff):** run `/resolve <that user's email>` in `#support` → confirm the ephemeral confirmation, the "Closed by" thread note, and that the open panel flips to the "closed by our support team" banner in real time; the user's next message starts a fresh thread. Also confirm bare `/resolve` lists open conversations.
5. **Unread + email:** with the panel closed (app still open), staff-reply and confirm the footer-tab badge increments **in real time without a reload** (conversation-doc listener) and (after the away threshold) a Brevo email arrives.
6. **Frontend gates:** `cd portal && npm run typecheck && npm test -- SupportPanel`.
7. **Dev-only gate:** confirm the "Support (beta)" tab appears with `VITE_SUPPORT_PANEL_ENABLED` set and is **absent** in a production build (`npm run build` with prod env), while the existing Trello "Feedback" tab still works unchanged.
8. **Phase 2 only:** run `/livechat on` in Slack → confirm the portal Live Chat tab enables in real time (via the `supportMeta/liveChat` listener) and a live message round-trips through `#live-chats`; run `/livechat off` **while a live conversation is open** → confirm the tab shows the offline note, the composer disables with the transcript still visible, and the backend refuses `type=live` sends; let an `on` entry expire and confirm it auto-flips offline.
