# Customer MCP server (`/mcp`)

Customers connect their own AI agents (Claude Code, claude.ai, Cursor …) to
their company's data in 3Maples. Built 2026-11-04 (part three of the MCP
enhancements; parts one and two, the API keys and the staff server's move to
`/mcp/internal`, shipped 2026-10-30). Rules for anyone changing it:
`.claude/rules/mcp-company.md`. The staff analytics server is a different
server: [analytics-mcp.md](analytics-mcp.md).

Endpoint: `https://api.3maples.ai/mcp` (Dev: `https://api-dev.3maples.ai/mcp`).
Transport: streamable HTTP, stateless, JSON responses. Auth: a user API key
(`3m_app_…`) as a bearer token — no OAuth sign-in.

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

## Keys

Each user makes their own in **Settings → Account → API keys**: scope `read`
(default) or `read_write`, a year at most, ten active per user. Owners and
Admins see and revoke every key in the company. A key acts as its user with
their role at the moment of each call; it stops when the user leaves the
company or the company closes. The same page shows the connection snippets
below with the new key filled in.

## Connecting

Claude Code:

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
change, with the key's user as the actor and `source: mcp`. Every call (reads
too) also writes an `mcp_access_logs` row with `kind: "company"`, the user, the
company, the key, the tool, its arguments (free text, search terms, estimate
titles, a property's name, and people's names, emails, phones and street
addresses recorded as `<text>`, nested ones too; empty arguments left out),
rows returned, duration and any error. Customers can't read the access log;
staff can in the database.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 404 | The servers are off in this environment | `MCP_SERVER_ENABLED=true` |
| 401 "A valid 3Maples API key is required" | Unknown, revoked or expired key; the user left the company; the company is closed | Make a new key in Settings → Account |
| Tool error "… used its 50 AI calls through the API for today" | The daily AI cap | Wait for midnight UTC, or raise `MCP_COMPANY_AI_DAILY_LIMIT` |
| Tool error "… Maple credits …" | The company is out of credits (no card), the user hasn't accepted overage, or the company hit the Maple hard cap | Add a card, or accept in 3Maples; for the hard cap, contact 3Maples support |
| 401 "Staff keys are accepted at /mcp/internal" | A staff `3m_mcp_` key | Use the staff server |
| 429 "Too many requests for this API key / company" | A limit above | Wait a minute |
| Tool error "… this API key is read-only" | A `read` key on a write tool | Make a `read_write` key |
| Tool error "Tasks isn't turned on for this account" | `TASKS_ENABLED` is off on this environment (platform-wide) | `TASKS_ENABLED=true` on the platform service |
