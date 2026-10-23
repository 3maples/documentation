# Analytics MCP server (staff-only, read-only)

_Plan drafted 2026-10-22. Decisions D1–D5 approved by Simon 2026-10-22 (all as recommended). Phases 1–5 built 2026-10-22, uncommitted, worktree `claude/analytics-mcp-b44714` (root, platform, portal, documentation). Left for Simon: merge, the production retention count, `MCP_SERVER_ENABLED` on Render, `/release`._

## 1. Goal

Let other AI agents (Claude Desktop / Claude Code / claude.ai connectors,
Cursor, in-house agents) read the same data the admin portal (`/ops`) shows,
plus the `audit_logs` collection and the usage collections the portal does not
surface yet, with filters on company, user, action, resource and time range.

Non-goals for v1: writes of any kind, customer-facing access, OAuth.

## 2. Decisions (approved 2026-10-22: every recommendation taken)

| # | Decision | Recommendation (approved) |
|---|---|---|
| D1 | **Auth for MCP clients.** Firebase ID tokens don't fit (hourly expiry, no sign-in flow in MCP clients, App Check impossible). | Per-staff **API keys**: created by root in `/ops/staff`, shown once, stored hashed, revocable, optional expiry, inherit the staff user's role. OAuth 2.1 is a later phase if claude.ai's connector flow needs it. |
| D2 | **PII and customer data exposure.** Agents keep tool output in third-party LLM context. Audit `before_state`/`after_state` carry estimate contents, contacts, prices; `ip_address` / `user_agent` are personal data. | Default responses carry names, emails, ids, counts and `changes` keys. `before_state`, `after_state`, `ip_address`, `user_agent`, phone numbers only with `include_details=true` **and** an `ops_admin`/`root` key. Dollar amounts (estimate totals, revenue) stay out of v1 unless you want them. |
| D3 | **Audit retention.** `audit_log_retention_days = 90` is in `config.py`, and two Brevo services are written as if rows are pruned after it, but **nothing prunes**: no TTL index, no script. Rows are kept forever today. | Decide explicitly. For analytics, keep raw rows for 13 months (TTL index via `database.align_ttl_indexes`) and add monthly rollups later if trends beyond that matter. Fix the config comment either way. |
| D4 | **Where it runs.** | Same codebase, mounted in the platform app at `/mcp` behind `MCP_SERVER_ENABLED` (default false). Split to its own Render service later if agent load ever competes with customers; the module is written so `mcp_main.py` is a two-line entrypoint. |
| D5 | **Engagement data that doesn't exist yet** (see §6). | Add a `USER_LOGIN` audit action now (cheap) so the MCP can answer "who was active when". Page-view analytics are a product-analytics tool, not this server. |

## 3. Architecture

```
platform/
  mcp_server/
    __init__.py
    server.py        # FastMCP instance, tool registration, lifespan hook
    auth.py          # bearer key -> StaffUser (role, key id); 401/403 mapping
    access_log.py    # one McpAccessLog row per tool call
    tools_ops.py     # admin-portal parity tools
    tools_audit.py   # audit log search / stats / history / vocabulary
    tools_usage.py   # llm usage, maple activity, billing events, overview
    pagination.py    # cursor encode/decode (timestamp,_id), caps
  services/
    ops_queries.py   # NEW: query + serialization logic lifted out of routers/ops.py
    audit_queries.py # NEW: filter builder + $group pipelines shared by /audit-logs and MCP
  models/
    staff_api_key.py # NEW
    mcp_access_log.py# NEW
```

**Transport**: official `mcp` SDK (2.3.0 is compatible with the pinned
starlette 1.7 / pydantic 2.13 / anyio 4.15 / httpx2; adds `mcp-types`,
`jsonschema`, `sse-starlette`, `opentelemetry-api`). Streamable HTTP, mounted
with `app.mount("/mcp", mcp.streamable_http_app())` **without**
`protected_route_dependencies` (App Check cannot be satisfied by MCP clients;
auth is the API key, see below). Stateless mode so Render can run more than one
instance.

**One service layer, two front doors.** The ops router and the MCP tools both
call `services/ops_queries.py` / `services/audit_queries.py`. A parity test
asserts the MCP `list_companies` row equals the `/ops/companies` row for the
same company, so the portal and the agents can never disagree on `ops_status`,
entitlements or membership status. Do **not** build the MCP as an HTTP proxy
over `/ops`: that would need Firebase + App Check tokens and double the
serialization.

**Auth flow**: `Authorization: Bearer 3m_mcp_<key>` → sha256 → `StaffApiKey`
(active, not expired) → `StaffUser` (active). Same `resolve_active_staff`
semantics as `require_staff_user`; disabled staff lose all keys at once. Key
prefix + `last_used_at` updated per call. Keys never scope to a company: staff
are not tenants (`.claude/rules/staff-users.md`).

**Access log**: every tool call writes `McpAccessLog {staff_id, key_id, tool,
args (no details payloads), rows_returned, duration_ms, ok, error, at}`. It is
a separate collection, **not** `audit_logs`: customers read their own
`audit_logs` via `/audit-logs`, and staff reads must never show up there.
Also the place to answer "which agent pulled what".

**Limits**: page size ≤ 200 for row tools, ≤ 2000 buckets for stats, date
range required for raw audit reads (default last 30 days, max 400 days), per-key
sliding-window rate limit reusing `services/request_protection.py`
(`InMemorySlidingWindowRateLimiter`), 25 s query timeout (`maxTimeMS`).

## 4. Tool set

Kept small (12 tools) and well described: agents pick correctly among a dozen,
badly among forty. Every list tool takes `since` / `until` (ISO 8601, UTC) and
returns `{items, next_cursor, total?}`; stats tools return `{buckets, range}`.

### 4a. Admin-portal parity (`tools_ops.py`)

| Tool | Filters | Source today |
|---|---|---|
| `list_companies` | search, ops_status (new/active/archived), plan, stripe_status, created since/until, cursor | `GET /ops/companies` |
| `get_company` | company_id → summary + members | `GET /ops/companies/{id}` + `/users` |
| `list_users` | search, company_id, role, membership_status, email_verified, created / last_login since/until, cursor | `GET /ops/users` |
| `list_new_users` | stage | `GET /ops/new-users` (skips the Firebase live lookup; reads the mirrored flag and says so) |

Staff list (`/ops/staff`) is deliberately not exposed.

### 4b. Audit logs (`tools_audit.py`)

| Tool | Notes |
|---|---|
| `search_audit_logs` | company_id, user_email, user_id, action / actions[], resource_type, resource_id, success, source (`metadata.source`: maple / portal), since, until, include_details, cursor. Cross-company, unlike `/audit-logs`. Cursor on `(timestamp, _id)`. |
| `audit_log_stats` | same filters + `group_by`: action, resource_type, user_email, company_id, source, day, week, month (one or two keys). `$group` pipeline, never the load-everything loop `/audit-logs/stats` uses today. |
| `resource_history` | resource_type + resource_id, full trail. |
| `audit_vocabulary` | the `AuditAction` and `ResourceType` enums with one-line meanings, so agents never guess strings. Also published as an MCP resource `audit://vocabulary`. |

### 4c. Usage analytics the portal doesn't show yet (`tools_usage.py`)

| Tool | Collection | Why |
|---|---|---|
| `llm_usage` | `llm_usage_events` | tokens, credits, cost_usd by company / user / feature / model / day. The real "how much Maple does each customer use" answer. |
| `maple_activity` | `maple_sessions`, `maple_unanswered` | sessions and turns per company/user, unanswered reasons (note: `maple_unanswered` has a TTL; say so in the tool description). |
| `billing_events` | `billing_events` | Stripe lifecycle per company, errors. |
| `platform_overview` | companies, users, audit_logs, llm_usage_events | one call: signups, onboarding completions, active companies, users seen (needs D5), estimates created, credits burned, for a range with day/week buckets. |

Estimate money figures (`services/maple_metrics.py`) are **not** wired in v1
(D2). If wanted, they go through that engine, never a new `$sum` of
`grand_total`.

## 5. Phases

Each phase is TDD, scoped `./run_mypy.sh` / `./run_ruff.sh`, bandit at review,
tests against the local Mongo.

| Phase | Work | Tests |
|---|---|---|
| 0 Prep | Decisions D1–D5 (done 2026-10-22). The `mcp==2.3.0` pin and the `mcp_*` settings move to phase 3, where they are first used. | — |
| 1 Service layer ✅ | Lift query/serialize logic from `routers/ops.py` into `services/ops_queries.py`; add `services/audit_queries.py` (filter builder + pipelines). Router behaviour unchanged. **Done:** `AuditFilter` (company optional = cross-tenant), `audit_find`, `audit_page` (cursor), `audit_counts` (1–2 group keys, UTC day/week-from-Monday/month), `audit_summary` (one `$facet`), `serialize_audit_log(include_details=)` with `changed_fields`; `/audit-logs` and `/audit-logs/stats` use them. `ops_queries.list_new_users(live_verification=False)` for agents; company counts now `$match` the page's ids. | existing `test_ops_*_api.py`, `test_audit_logs_api.py` stay green; new unit tests for the pipelines (group_by, cursor). |
| 2 API keys ✅ | `models/staff_api_key.py` (hash, prefix, expires_at, revoked_at, last_used_at; register in `database.py`). No role snapshot after all: a key acts as its staff member's *current* role and status, read on every call. 90-day default expiry, 365 max, 10 active per staff, `last_used_at` written at most once a minute, issue/revoke audited as `STAFF_API_KEY_*`. Root-only `POST/GET/DELETE /ops/staff/{id}/api-keys`. Portal: key panel on `OpsStaffPage.tsx` (create shows the key once, revoke). **Done:** an API keys button on every row (own row included) opens `components/ops/StaffApiKeysDialog.tsx`: list by name and prefix, create with 30/90/180/365-day expiry, the key shown once with Copy, revoke with an inline confirm. | `test_staff_api_keys_api.py`, portal Vitest for the panel. |
| 3 MCP core | `mcp_server/` with auth, access log, limits, the 4a and 4b tools; mount at `/mcp` when enabled. Indexes: `[action, timestamp]`, `[user_email, timestamp]`, `[timestamp, _id]` on `audit_logs`. D3: TTL index on `audit_logs.timestamp` at 395 days through `database._ttl_indexes`, `audit_log_retention_days` set to 395 and actually wired. **The first index build deletes every older row**: before `/release platform`, run a read-only count of prod rows older than 395 days and tell Simon. **Done:** `mcp_server/` (`endpoint.py` key gate + per-key rate limit + 404 when off; `server.py`; `tools_ops.py` list_companies / get_company / list_users / list_new_users; `tools_audit.py` search_audit_logs / audit_log_stats / resource_history / audit_vocabulary; `access_log.py` → `mcp_access_logs`, 395-day TTL). `mcp==2.3.0` pinned; seven new transitive pins in `constraints.txt`, no existing pin moved. New `ops_queries` filters: plan, stripe status, signup range for companies; role, membership, signup and last-login ranges for users. Audit reads carry `maxTimeMS` (`MCP_QUERY_TIMEOUT_MS`). Found on the way: the ops orphan detection read only the audit log, so the TTL would have turned old orphans into never-joined signups — `ops_membership.fetch_ever_joined_user_ids` now also counts company-less users with `has_ever_joined_company`. SDK notes: one session manager per app start (a second `TestClient` restarts the app), its DNS-rebinding guard turned off (it accepts only localhost Host headers), its `logging.basicConfig` suppressed, tools return builtin `dict[str, Any]` so structured content isn't wrapped. | `test_mcp_server.py` (key gate, rate limit, every tool, D2 details, access log, parity with `/ops`, the SDK client end to end over ASGI), `test_mcp_indexes.py`, new cases in `test_ops_queries.py` / `test_audit_queries.py`. |
| 4 Usage tools ✅ | 4c tools; `USER_LOGIN` audit action in `POST /auth` (D5). **Done:** `services/usage_queries.py` (`llm_usage`, `maple_activity`, `unanswered_examples`, `billing_events_report`, `platform_overview`) and `mcp_server/tools_usage.py` (llm_usage, maple_activity, billing_events, platform_overview; 12 tools in all). Credits count a pre-credits row's total_tokens, as billing does; Maple turns are distinct `turn_id`s among the LLM calls; what users typed to Maple only with details. `USER_LOGIN` is written on the first sign-in of each UTC day. To make that an exact daily-active signal, `last_login_at` (and the Brevo LAST_LOGIN push) now moves once per UTC calendar day instead of per rolling 24h, which skipped every other day for someone signing in a little earlier each morning. Day/week/month buckets moved to `services/date_buckets.py`, raw aggregates to `services/mongo_aggregate.py`. | `test_usage_queries.py`, usage cases in `test_mcp_server.py`, login cases in `test_login_last_seen.py`. |
| 5 Ship (docs ✅, release Simon's) | `.claude/rules/mcp-analytics.md` (tenancy and PII rules for anyone touching the tools), user guide "Connect an agent to 3Maples analytics" (Claude Desktop / claude.ai connector / Claude Code config snippets), Render env (`MCP_SERVER_ENABLED=true`), `/release platform`. **Done:** the rule file (and its row in `CLAUDE.md`, plus the tenant-scope exception named there); the staff guide at `documentation/operations/analytics-mcp.md` (keys, clients, tools, limits, troubleshooting, turning it on) — not in `platform/user_guides/`, which Maple's help answers read; `scripts/audit_retention_check.py`, a read-only count of what the TTL would delete, which never calls `init_db` (that would build the index). Dev checked 2026-10-22: 6,069 rows, oldest 2026-03-20, none deleted. **Simon's:** merge, `pip install -r requirements.txt` in the main venv, the production count, `MCP_SERVER_ENABLED=true` on Render (Dev first), `/release platform` (or `app`, for the portal key panel). Client setups other than Claude Code are not yet tried against the server. | `test_audit_retention_check.py` |
| 6 Later | OAuth 2.1 if a client demands it; separate Render service with a read-only Mongo user and secondary read preference; monthly audit rollups once D3 retention bites. | — |

Rough size: phases 1–3 are the bulk (about two to three working sessions);
4 and 5 one session each.

## 6. Gaps the MCP cannot paper over

The server only serves what is recorded. Today that means:

1. ~~**Logins are not audited.**~~ Phase 4: one `USER_LOGIN` row per user per
   UTC day, from 2026-10-22 on (earlier ranges have none; `platform_overview`
   says when recording began). Still no session length or page data.
2. **Reads are not audited.** Only mutations write `audit_logs`, so "which
   pages or features do people use" is not in the database at all. That is
   product analytics (PostHog or similar), not this server.
3. **Maple conversations are not in `audit_logs`.** Cost is in
   `llm_usage_events`; question text lives only in `maple_unanswered` and
   `maple_shadow_turns`, both with TTLs. If "what do customers ask Maple" is a
   question you want answered, a retained, redacted turn log is a separate
   feature.
4. ~~**Retention is undefined** (D3): config says 90 days, reality is forever.~~
   Phase 3: 395 days, enforced by a TTL index.
5. **Join key is email.** `audit_logs.user_id` is the Firebase UID, ops user ids
   are Mongo ids; `user_email` is the only common key, and an email change
   splits a user's history. Document it; a UID→user map tool is cheap if it
   bites.
6. ~~**`/audit-logs/stats` loads every row into memory.**~~ Fixed in phase 1 (one `$facet`). Fine per-company for
   30 days; the MCP version uses pipelines and the router should adopt the
   same helper in phase 1.
7. ~~**Cross-company audit indexes are missing** for action/time and user/time
   queries~~ — added in phase 3.

## 7. Alternative considered: MongoDB's official MCP server

Point `mongodb-mcp-server` at a read-only database user with a collection
allow-list and every collection is queryable in an afternoon, no code.
Rejected as the primary path because it exposes raw schemas and raw PII, has
no notion of `ops_status` / entitlements / membership (the portal derives
these), can't rate-limit or log per staff user, and lets an agent write
arbitrary aggregations against production. It is a reasonable **stopgap for
you personally** while phases 1–3 land, on the Dev cluster only.
