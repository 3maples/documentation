# Analytics MCP server: connect an agent

For 3Maples staff. The platform serves a read-only [MCP](https://modelcontextprotocol.io)
server at `/mcp` that lets an AI agent (Claude Code, Claude Desktop, Cursor, your
own) answer usage questions from the same data as the ops portal, plus the audit
log and usage history. Design and decisions:
[`development/plans/analytics-mcp-server.md`](../development/plans/analytics-mcp-server.md).
Rules for anyone changing it: `.claude/rules/mcp-analytics.md`.

Endpoint: `https://api.3maples.ai/mcp`

---

## 1. Get an API key

Only the **root** staff account can issue keys.

1. Sign in to the portal as root and open **Ops → Staff**.
2. On the row of the staff member the key is for (yourself included), click
   **API keys**.
3. Name the key after where it will live ("Simon – Claude Code laptop"), pick how
   long it lasts (30, 90, 180 or 365 days; 90 by default), and **Create key**.
4. Copy the key (`3m_mcp_…`) straight away. **It is shown once.** Close the dialog
   and it's gone; only its first characters stay in the list.

What a key can do is decided by its staff member's role **at the moment it is
used**:

| Role | Can read |
|---|---|
| `ops_viewer` | everything below except the details |
| `ops_admin`, `root` | also `include_details`: changed values and before/after snapshots in audit rows, IPs, user agents, phone numbers, and what users typed to Maple |

Disabling the staff member stops all their keys at once; re-enabling brings back
the ones that haven't expired. A staff member can hold at most 10 active keys.
Revoke a key from the same dialog the moment a laptop is lost or a key is pasted
somewhere it shouldn't be — it stops working on the next request.

Treat a key like a password with read access to every customer: keep it in an
environment variable or a secrets manager, never in a repository or a chat.

---

## 2. Connect a client

The server speaks Streamable HTTP and takes the key as a bearer token:
`Authorization: Bearer 3m_mcp_…`. It has no OAuth sign-in.

**Smoke test first** (any shell; a 200 with a list of tools means the key and
the endpoint both work):

```bash
curl -s https://api.3maples.ai/mcp \
  -H "Authorization: Bearer $MAPLES_MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Claude Code

One command ([docs](https://code.claude.com/docs/en/mcp.md)); `--scope user`
makes it available in every project:

```bash
claude mcp add --transport http 3maples-operations https://api.3maples.ai/mcp --header "Authorization: Bearer 3m_mcp_…" --scope user
```

To keep the key out of the config, use a `.mcp.json` (project scope) that reads
it from your environment. Don't name the variable `ANTHROPIC_API_KEY` or the like:
Claude Code blanks those inside remote-server headers.

```json
{
  "mcpServers": {
    "3maples-operations": {
      "type": "http",
      "url": "https://api.3maples.ai/mcp",
      "headers": { "Authorization": "Bearer ${MAPLES_MCP_TOKEN}" }
    }
  }
}
```

### claude.ai and Claude Desktop (custom connector)

Setting up the MCP connection in Claude Desktop:

1. **Settings → Connectors → Add custom connector.**
2. **Name:** `3maples-operations`. **URL:** `https://api.3maples.ai/mcp`
3. **Authentication:** choose **No sign-in**. Don't choose a sign-in option: this
   server has no OAuth, so a sign-in attempt would just fail.
4. **Request headers:** add
   - name `Authorization`
   - value `Bearer 3m_mcp_…` (the word `Bearer`, a space, then your key)
5. Save, then turn the connector on in a chat's tools menu.

Depending on the account, the authentication and header settings may be on a
second screen after the URL; Anthropic's [custom connector guide](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
describes both layouts. On a Team or Enterprise plan an owner may have to add
the connector for the organisation. The same connector works in claude.ai on
the web.

### Claude Desktop config file

For an account whose custom connector screen has no **Request headers**
option. `claude_desktop_config.json` runs only local servers, so a remote server
with a header needs a bridge. The usual one is
[`mcp-remote`](https://github.com/geelen/mcp-remote) (community tooling, not
Anthropic's). Open **Settings → Developer → Edit Config** and add `mcpServers`
as a top-level entry if the file has none. Quit Claude Desktop with ⌘Q and
reopen it after saving.

```json
{
  "mcpServers": {
    "3maples-operations": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://api.3maples.ai/mcp", "--header", "Authorization:${AUTH_HEADER}"],
      "env": { "AUTH_HEADER": "Bearer 3m_mcp_…" }
    }
  }
}
```

Keep the key in `env`, not in `args`: Claude Desktop splits arguments that contain spaces. If the server doesn't appear, read `~/Library/Logs/Claude/mcp-server-<name>.log`.

### Cursor and other clients

Any client that can send a header to a Streamable HTTP server works: give it the
endpoint URL and the `Authorization: Bearer 3m_mcp_…` header. In Cursor that is
an `mcp.json` entry with `url` and `headers`, shaped like the `.mcp.json` above.

---

## 3. What you can ask

Twelve tools, all read-only. You rarely name them — ask the question and the
agent picks. A good first call is `platform_overview`.

| Tool | Answers |
|---|---|
| `platform_overview` | Signups, onboarding, sign-ins, active users and companies, estimates, Maple turns, credits and cost, for a range and per day/week/month |
| `list_companies`, `get_company` | The ops Companies page: plan, status, usage against what the plan includes, members |
| `list_users`, `list_new_users` | The ops Users and New Users pages, with role, membership, signup and last-login filters |
| `search_audit_logs`, `audit_log_stats`, `resource_history` | What users changed, cross-company, as rows or counts grouped by action, user, company, day/week/month |
| `audit_vocabulary` | The action and resource names the audit tools take |
| `llm_usage` | Calls, tokens, credits and OpenAI cost by company, user, feature, model or time |
| `maple_activity` | Maple turns, who sent them, what Maple couldn't answer and why |
| `billing_events` | Stripe webhooks as they landed, and the ones our handler failed on |

Example questions:

- "How did signups and active companies trend week by week over the last quarter?"
- "Which ten companies used the most Maple credits last month, and what did that cost us?"
- "Show me Acme Landscaping's audit trail for the past two weeks."
- "What does Maple fail to answer most often this month? Show examples." (examples need an ops_admin or root key)
- "Which paying companies haven't had anyone sign in for 30 days?"
- "Did any Stripe webhooks fail this week?"

---

## 4. What the data can't tell you

- **Only changes are audited**, plus one sign-in row per user per UTC day. Page
  views, reads and time spent in the app are not recorded anywhere.
- **Sign-ins are recorded from the release that added them** (October 2026).
  `platform_overview` reports `logins_recorded_since`; earlier ranges show none.
- **Audit rows are kept 395 days**, then deleted. Every audit and usage read
  covers at most 400 days (the last 30 by default).
- **When a company finished onboarding isn't stored**, only whether it has.
- **Users join across tools by email.** Audit rows carry the Firebase UID as
  `user_id`; the user tools return database ids.
- Unanswered Maple turns are kept 180 days; Maple turns and credits are kept
  with the LLM calls.

Every tool call is logged against your key (`mcp_access_logs`, kept 395 days):
who asked, which tool, with what arguments, how many rows came back.

---

## 5. When it doesn't work

| You see | Why | Fix |
|---|---|---|
| HTTP 404 | The server is off in this environment | Set `MCP_SERVER_ENABLED=true` on that environment's platform service |
| HTTP 401 | Missing, mistyped, revoked or expired key, or the staff account is disabled | Check the header is `Authorization: Bearer 3m_mcp_…`; issue a new key |
| HTTP 429 | More than 120 requests a minute on this key, or 600 from one address | Wait a minute; ask fewer, broader questions |
| "include_details needs an ops_admin or root key" | Your role can't see details | Ask without details, or use a senior key |
| "a range is at most 400 days" | The question spans more than 400 days | Ask per year |
