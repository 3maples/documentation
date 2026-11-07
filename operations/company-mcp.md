# Customer MCP server (`/mcp`)

Customers connect their own AI agents (Claude Code, claude.ai, Cursor …) to
their company's data in 3Maples. Built 2026-11-04 (part three of the MCP
enhancements; parts one and two, the API keys and the staff server's move to
`/mcp/internal`, shipped 2026-10-30). Rules for anyone changing it:
`.claude/rules/mcp-company.md`. The staff analytics server is a different
server: [analytics-mcp.md](analytics-mcp.md).

Endpoint: `https://api.3maples.ai/mcp` (Dev: `https://api-dev.3maples.ai/mcp`).
Transport: streamable HTTP, stateless, JSON responses. Auth: **signing in**
(OAuth 2.1 — the app opens 3Maples, the person approves it) or a user API key
(`3m_app_…`) as a bearer token, for scripts and apps that can't sign in.

## Turning it on

`MCP_SERVER_ENABLED=true` on the platform service starts both MCP servers; with
it off, `/mcp` and `/mcp/internal` answer 404 (Simon 2026-11-04: one switch,
live with the release).

| Setting | Default | What |
|---|---|---|
| `MCP_RATE_LIMIT_PER_MINUTE` | 120 | requests per API key |
| `MCP_COMPANY_RATE_LIMIT_PER_MINUTE` | 600 | requests per company, across all its keys |
| `MCP_COMPANY_AI_DAILY_LIMIT` | 50 | paid AI calls per company per UTC day (see below) |
| `MCP_IP_RATE_LIMIT_PER_MINUTE` | 600 | requests per address, before the key lookup |
| `MCP_MAX_PAGE_SIZE` | 200 | rows per list call |
| `MCP_ACCESS_LOG_RETENTION_DAYS` | 395 | how long the per-call access log is kept |
| `API_PUBLIC_URL` | unset | the API's own address (`https://api.3maples.ai`, no trailing slash); unset, sign-in is off |
| `OAUTH_IP_RATE_LIMIT_PER_MINUTE` | 60 | requests per address to the sign-in routes |

Sign-in also needs `APP_BASE_URL` to be this environment's portal:
`/authorize` sends the person to `<APP_BASE_URL>/connect`.

## Signing in (OAuth)

Added 2026-11-06 so that setting up is "paste the address, sign in". Code:
`platform/services/oauth.py` (the rules), `services/oauth_provider.py` (the
MCP SDK's provider interface), `mcp_server/oauth_app.py` (the routes),
`routers/oauth.py` (the consent page's API and connected-apps lists), portal
`src/pages/auth/ConnectPage.tsx`.

1. The app calls `/mcp` with no token. The 401's `WWW-Authenticate` names
   `resource_metadata="<api>/.well-known/oauth-protected-resource/mcp"`
   (RFC 9728), which names this API as the authorization server.
2. The app reads `/.well-known/oauth-authorization-server` and registers
   itself at `/register` (RFC 7591). **Every client is public**: whatever it
   asks for, it is stored with `token_endpoint_auth_method: none` and no
   secret — anyone can register, so a secret would prove nothing. PKCE (S256)
   and an exact redirect match do. Redirects may be https, plain http only to
   `localhost` / `127.0.0.1` / `[::1]`, or an app's own scheme (`cursor://`);
   never `javascript:`, `data:`, `file:` or with a fragment. A client nobody
   approves is deleted after 30 days.
3. `/authorize` saves the request (10 minutes) and sends the browser to
   `<APP_BASE_URL>/connect?request=…`. Signed out, the portal sends them to
   sign in first and back (`/login?next=`).
4. The page shows the app's name, where it gets access (a website's host, or
   an app's own scheme written as `myapp://host` so it can't pass for that
   website), and who it will act as. **"Allow it to make changes" starts
   ticked** (Simon 2026-11-06) unless the app asked only for the `read`
   scope; unticked, the connection is read-only. One person has at most one
   live connection per app and server (a unique index). Approve or Deny
   sends the browser back to the app with a code or `access_denied` (and
   `iss`, RFC 9207).
5. The app swaps the code (5 minutes, once) at `/token` for an access token
   (`3m_oat_…`, an hour) and a refresh token (`3m_ort_…`, 30 days, rotated on
   every use). **A spent code or refresh token presented again by its app
   revokes the connection** — it was copied. `/revoke` with either token disconnects it.

A **connection** acts as its person *now*, like a key: every call re-reads the
user and company; leaving the company, being removed, moving company or the
company closing stops it, and leaving revokes it for good (the five places
that revoke keys revoke connections too). The person's role limits every write
as usual. One person and one app make one connection — signing in again
updates it.

People see and disconnect their apps in **Settings → AI Apps → Your connected
apps** (its own tab since 2026-11-06); Owners and Admins also see every app in the company. Only hashes of
codes and tokens are stored (`oauth_tokens`), with the requests
(`oauth_requests`), clients (`oauth_clients`) and connections (`oauth_grants`).

## Keys

**Hidden in the portal since 2026-11-06**: signing in is the one way Settings
→ AI Apps shows. The key routes (`/api-keys`) and keys made before still
work; `ApiKeysSection` is kept and comes back by rendering it in
`AiAppsTab` again. Until then nobody can make, see or revoke a customer key
in the portal, so a key made before runs until it expires (a year at most) or
its user leaves.

When shown, each user makes their own in the **API keys** section:
scope `read` (default) or `read_write`, a year at most, ten active per user.
Owners and Admins see and revoke every key in the company. A key acts as its
user with their role at the moment of each call; it stops when the user
leaves the company or the company closes. The same page shows the connection
snippets below with the new key filled in.

## Connecting

**By signing in** (most apps): add the server address, then sign in to 3Maples
and approve when the app asks. Settings → AI Apps shows the same steps.

- claude.ai and Claude Desktop: **Settings → Connectors → Add custom
  connector**, URL `https://api.3maples.ai/mcp`, no headers.
- Claude Code: `claude mcp add --transport http 3maples https://api.3maples.ai/mcp`,
  then `/mcp` → 3maples → authenticate.
- Cursor or `.mcp.json`: `{ "mcpServers": { "3maples": { "type": "http", "url": "https://api.3maples.ai/mcp" } } }`.
- ChatGPT and others: add it as a custom connector / MCP server with that URL.

**With a key** (scripts, CI, apps that only send a header) — Claude Code:

```bash
claude mcp add --transport http 3maples https://api.3maples.ai/mcp --header "Authorization: Bearer 3m_app_…"
```

Cursor or a project's `.mcp.json`:

```json
{ "mcpServers": { "3maples": { "type": "http", "url": "https://api.3maples.ai/mcp",
  "headers": { "Authorization": "Bearer 3m_app_…" } } } }
```

claude.ai and Claude Desktop (custom connector):

1. **Settings → Connectors → Add custom connector.**
2. **Name:** `3maples`. **URL:** `https://api.3maples.ai/mcp`
3. **Authentication:** **No sign-in** (the server has no OAuth).
4. **Request headers:** name `Authorization`, value `Bearer 3m_app_…`.
5. Save, then turn the connector on in a chat's tools menu.

The screens differ a little between accounts, and a Team or Enterprise owner
may have to add the connector; [analytics-mcp.md](analytics-mcp.md#claudeai-and-claude-desktop-custom-connector)
has the details and the `mcp-remote` fallback for the Desktop config file.

Check a key by hand:

```bash
curl -s https://api.3maples.ai/mcp \
  -H "Authorization: Bearer 3m_app_…" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"whoami","arguments":{}}}'
```

## What an agent can do (92 tools)

Everything goes through the same rules as the portal: Owner/Admin only where
the portal is, estimates editable only in Draft or Review, the status machine
and send gate, the plan's estimate quota. A `read` key can only read. Rate
cards, divisions, material categories and material units are Owner/Admin to
create, change and delete, as in the portal (Simon 2026-11-04), although their
routes would let any member.

| Area | Tools |
|---|---|
| You and your company | `whoami`, `get_company`, `update_company`, `list_users` (no phone numbers) |
| Contacts and properties | `list_/get_/create_/update_/delete_contact`, `list_/get_/create_/update_/delete_property`, `get_property_activity`, `link_contact_to_property`, `unlink_contact_from_property` |
| Notes | `list_notes`, `create_note`, `update_note`, `delete_note` (property, contact, estimate, work item) |
| Tasks (when Tasks is on) | `list_/get_/create_/update_/archive_/delete_task`, `convert_task_to_estimate`, `list_/create_/update_/delete_task_status` |
| Estimates | `list_estimates`, `get_estimate`, `get_estimate_analytics`, `create_estimate`, `duplicate_estimate`, `update_estimate`, `set_estimate_status`, `archive_estimate`, `unarchive_estimate`, `delete_estimate`, `edit_estimate` (Maple's edit commands, all-or-nothing; lines named by `line_id` or by name) |
| Estimates with AI | `generate_estimate` (from a description), `generate_work_item` (a priced scope added to an estimate), `resize_work_item` (rescaled from a stored size, else priced again by AI), `adjust_assumption` (a size or material Maple assumed; no AI) |
| Materials catalog | `list_/get_/create_/update_/delete_material`, `set_material_pricing`, `reset_material`, `hide_material`, `show_material`, `unhide_all_materials`, `duplicate_material`, categories and units (list; create/update/delete Owner/Admin), `set_standard_category_included` |
| People roles | `list_/get_/create_/update_/delete_people_role`, `hide_/show_/reset_/duplicate_people_role`, `unhide_all_people_roles` |
| Templates, rate cards, divisions | `list_/get_/create_/update_/duplicate_/delete_template`, `list_/get_/create_/update_/delete_rate_card`, `list_/create_/update_/delete_division` |

**Asks first** (`confirm: true`; without it the tool says what it would do and
changes nothing): every delete, moving an estimate into Sent, changing a company
percentage, resetting a standard material or role, removing a work item through
`edit_estimate`, a create, copy or convert that bills an extra estimate, a convert
that deletes the task, and a resize that prices a work item again with AI. As in
the portal, a create, copy or AI create doesn't ask about the extra estimate
when the key's user has turned off **Show estimate overage notification**; a
convert always asks. A
work-item removal's answer lists the items' `job_item_ids`; the agent confirms
with those, so items moving in between can't remove the wrong one.

**Not available** (Simon 2026-10-29 and 2026-11-04): user management,
invitations, equipment, the audit log, applying a template (v2), estimate
documents, file attachments and task photos.

## AI calls

`generate_estimate`, `generate_work_item`, `convert_task_to_estimate` and a
`resize_work_item` that prices again are paid model calls. Each one:

- uses the company's **Maple credits**, billed like Maple's own (usage feature
  `mcp.<tool>`). A company out of credits with no card is refused, and so is a
  user who hasn't accepted overage charges yet: they accept them in 3Maples
  (Maple's refusal links to it), not through the API;
- counts against **`MCP_COMPANY_AI_DAILY_LIMIT`** (50) for the company, across
  all its keys, per UTC day. An attempt counts once it starts, even if it then
  fails. The count is in the `mcp_ai_usage` collection (one row per company per
  day, dropped after a week);
- can take a minute.

A refusal (an unknown id, a locked estimate, an unconfirmed resize, a company
out of estimates, a task with no description, already converting or on another
company's property) happens
before the call and costs nothing. A resize that needed no AI stops and asks
the agent to call again if the work item's size changed in the meantime; it
never prices again without asking.

## Line ids

Every material and activity line has an id (`line_id` in `get_estimate`), so an
agent can name the one line it means when two share a name. Run once per
environment, after the release that ships them is live there (older code drops
the ids when it saves; running it again is safe):

```bash
python scripts/backfill_line_ids.py          # dry run
python scripts/backfill_line_ids.py --apply
```

Until it has run, a line saved before 2026-11-04 loads with an id worked out
from its work item and its place, the same on every load, and the backfill
stores that same id, so an id an agent already read keeps working. The portal keeps and sends the ids from the same
release; an older portal tab saves its lines with new ids (an agent just reads
the estimate again).

## Contacts left on properties

Deleting a contact now takes it off every property it was linked to (in the
portal, through Maple and through `delete_contact`). Contacts deleted before
2026-11-04 left their ids behind. Run once per environment after the release:

```bash
python scripts/pull_dangling_property_contacts.py          # dry run
python scripts/pull_dangling_property_contacts.py --apply
```

Until it has run, `update_property` still works (it checks only contacts it
adds), and reads skip the missing contacts.

## Auditing

Every change an agent makes is on the company's audit trail like a portal
change, with the key's or connection's user as the actor and `source: mcp`.
Connecting, connecting again and disconnecting an app write
`OAUTH_CONNECTION_CREATE` / `_UPDATE` / `_REVOKE` on the company (app name and
scope, never a token). Every call (reads
too) also writes an `mcp_access_logs` row with `kind: "company"`, the user, the
company, the key (`api_key`) or connection (`oauth_grant`), the tool, its arguments (free text, search terms, estimate
titles, a property's name, and people's names, emails, phones and street
addresses recorded as `<text>`, nested ones too; empty arguments left out),
rows returned, duration and any error. Customers can't read the access log;
staff can in the database.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 404 | The servers are off in this environment | `MCP_SERVER_ENABLED=true` |
| 401 "A valid 3Maples API key is required" | Unknown, revoked or expired key or sign-in; the user left the company; the company is closed | Sign in again from the app (the portal no longer makes keys; see Keys) |
| The app never offers to sign in; `/.well-known/oauth-authorization-server` is 404 | `API_PUBLIC_URL` unset on this environment | Set it (no trailing slash) |
| `/connect` says "This sign-in link has expired" | More than 10 minutes passed, or it was already used | Start again from the app |
| `/connect` says to sign in with a staff account / not a staff account | The app asked for the other server (`resource`) | Sign in with the right account, or fix the app's URL |
| Tool error "… this connection is read-only" | "Allow it to make changes" was unticked, or the app asked only for `read` and the box was left unticked | Reconnect the app and tick it |
| A browser-based tool (e.g. MCP Inspector) can't finish signing in; the browser console shows a CORS error on `/token` or `/register` | The app's CORS allow-list (`CORS_ORIGINS`) covers the portal only, and it answers those preflights before the OAuth routes do (accepted 2026-11-06: supported apps — Claude, Claude Code, Cursor, ChatGPT — sign in from their servers or desktop, not a web page) | Use a desktop or server-side client, or an API key |
| Tool error "… used its 50 AI calls through the API for today" | The daily AI cap | Wait for midnight UTC, or raise `MCP_COMPANY_AI_DAILY_LIMIT` |
| Tool error "… Maple credits …" | The company is out of credits (no card), the user hasn't accepted overage, or the company hit the Maple hard cap | Add a card, or accept in 3Maples; for the hard cap, contact 3Maples support |
| 401 "Staff keys are accepted at /mcp/internal" | A staff `3m_mcp_` key | Use the staff server |
| 429 "Too many requests for this API key / company" | A limit above | Wait a minute |
| 429 on `/token`, `/authorize` or `/register` for many users at once | A hosted connector (claude.ai, ChatGPT) calls the sign-in routes from the provider's own servers, so all its users share a few addresses and one `OAUTH_IP_RATE_LIMIT_PER_MINUTE` allowance. At 60, that's roughly 12 sign-ins in the same minute, or about 3,600 connections refreshing hourly per provider address (accepted 2026-11-06: far above today's usage) | Raise `OAUTH_IP_RATE_LIMIT_PER_MINUTE` on Render (no release needed) |
| Tool error "… this API key is read-only" | A `read` key on a write tool | Make a `read_write` key |
| Tool error "Tasks isn't turned on for this account" | `TASKS_ENABLED` is off on this environment (platform-wide) | `TASKS_ENABLED=true` on the platform service |
