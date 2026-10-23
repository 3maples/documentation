# Analytics MCP server: connect an agent

For 3Maples staff. The platform serves a read-only [MCP](https://modelcontextprotocol.io)
server at `/mcp` that lets an AI agent (Claude Code, Claude Desktop, Cursor, your
own) answer usage questions from the same data as the ops portal, plus the audit
log and usage history. Design and decisions:
[`development/plans/analytics-mcp-server.md`](../development/plans/analytics-mcp-server.md).
Rules for anyone changing it: `.claude/rules/mcp-analytics.md`.

| Environment | Endpoint |
|---|---|
| Dev | `https://api-dev.3maples.ai/mcp` |
| Production | `https://<production API host>/mcp` |

It answers 404 until `MCP_SERVER_ENABLED=true` is set on that environment's
platform service (see [Turning it on](#turning-it-on)).

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
curl -s https://api-dev.3maples.ai/mcp \
  -H "Authorization: Bearer $MAPLES_MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Claude Code

One command ([docs](https://code.claude.com/docs/en/mcp.md)); `--scope user`
makes it available in every project:

```bash
claude mcp add --transport http maples https://api-dev.3maples.ai/mcp --header "Authorization: Bearer 3m_mcp_…" --scope user
```

To keep the key out of the config, use a `.mcp.json` (project scope) that reads
it from your environment. Don't name the variable `ANTHROPIC_API_KEY` or the like:
Claude Code blanks those inside remote-server headers.

```json
{
  "mcpServers": {
    "maples": {
      "type": "http",
      "url": "https://api-dev.3maples.ai/mcp",
      "headers": { "Authorization": "Bearer ${MAPLES_MCP_TOKEN}" }
    }
  }
}
```

### claude.ai and Claude Desktop (custom connector)

**Settings → Connectors → Add custom connector**: the endpoint URL, and the key
as a fixed request header (`Authorization` = `Bearer 3m_mcp_…`). Anthropic's
[custom connector guide](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
covers servers that use "an API key, bearer token, or other fixed credential
instead of OAuth". Not yet tried against this server (2026-10-22): check the
field accepts an `Authorization` header before relying on it. On a Team or
Enterprise plan an owner may have to add the connector for the organisation.

### Claude Desktop config file

`claude_desktop_config.json` runs only local servers, so a remote server with a
header needs a bridge. The usual one is [`mcp-remote`](https://github.com/geelen/mcp-remote)
(community tooling, not Anthropic's; not yet tried against this server):

```json
{
  "mcpServers": {
    "maples": {
      "command": "npx",
      "args": ["mcp-remote", "https://api-dev.3maples.ai/mcp", "--header", "Authorization:${AUTH_HEADER}"],
      "env": { "AUTH_HEADER": "Bearer 3m_mcp_…" }
    }
  }
}
```

Prefer the custom connector above where it works.

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
| HTTP 404 | The server is off in this environment | Set `MCP_SERVER_ENABLED=true` ([Turning it on](#turning-it-on)) |
| HTTP 401 | Missing, mistyped, revoked or expired key, or the staff account is disabled | Check the header is `Authorization: Bearer 3m_mcp_…`; issue a new key |
| HTTP 429 | More than 120 requests a minute on this key, or 600 from one address | Wait a minute; ask fewer, broader questions |
| "include_details needs an ops_admin or root key" | Your role can't see details | Ask without details, or use a senior key |
| "a range is at most 400 days" | The question spans more than 400 days | Ask per year |

---

## Turning it on

Per environment, on the platform web service in the Render dashboard
(`fastapi-app`), **Environment**:

1. Add `MCP_SERVER_ENABLED` = `true`. The limits have working defaults
   (`MCP_RATE_LIMIT_PER_MINUTE`, `MCP_MAX_PAGE_SIZE`, `MCP_MAX_BUCKETS`,
   `MCP_QUERY_TIMEOUT_MS`; see `platform/.env.example`).
2. Save; Render redeploys. `/mcp` now answers 401 to a request without a key.

### Before the release that first ships it

The same release adds the 395-day audit retention. **Its first startup in an
environment deletes every audit row older than 395 days.** Before promoting it,
count what would go, read-only:

```bash
cd platform
MONGODB_URL='<that environment's connection string>' .venv/bin/python scripts/audit_retention_check.py
```

If that environment sets its own `AUDIT_LOG_RETENTION_DAYS`, pass it with
`--days <n>`; otherwise the script uses this machine's setting (395).

It prints the total, the oldest row and the rows that would be deleted, by
action. It writes nothing and never builds indexes. Dev, checked 2026-10-22:
6,069 rows, oldest 2026-03-20, **none** would be deleted. Production is the one
to check.

After merging into the main checkout, its `platform/.venv` needs the new
dependency (`mcp`) before the pre-push hook can import the app:

```bash
cd platform && .venv/bin/pip install -r requirements.txt
```
