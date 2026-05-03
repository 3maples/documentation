---
description: Security-focused review of code under platform/ and portal/. Works without a git repo; scope with an optional path arg to narrow to one file or subdirectory.
argument-hint: [optional-path-under-platform-or-portal]
allowed-tools: Bash, Read, Grep, Glob
---

# Security Review

Security-focused review of the Tangz 3maples codebase. This is a **project-local override** of the built-in `/security-review` — the built-in uses `git log` and `git diff` to scope its review, which fails here because this working tree is not a git repository. This version scopes by walking `platform/` and `portal/` directly.

If `$ARGUMENTS` is provided, restrict the review to that path (single file or subdirectory under `platform/` or `portal/`). Otherwise, review both trees in full.

## Step 1 — Discover Files

1. If `$ARGUMENTS` is set, use it as the root. Verify it sits under `platform/` or `portal/` and reject otherwise.
2. Otherwise, walk both roots and bucket files:
   - **Backend (Python)** — `platform/**/*.py` excluding `.venv/`, `__pycache__/`, and `tests/` (tests get a light pass under Step 2 cross-cutting)
   - **Frontend (React)** — `portal/src/**/*.{jsx,tsx,js,ts,css}` excluding `node_modules/` and `dist/`
   - **Config / infra** — `*.json`, `*.yaml`, `*.toml`, `Dockerfile*`, `.env.example` — cross-cutting only
3. Record which buckets have files. Skip Step 3 or Step 4 if their bucket is empty.

Use `Glob` for enumeration, not `git ls-files` — this repo is not a git repo. Do not attempt `git diff`, `git status`, or any `git` command anywhere in this review.

## Step 2 — Cross-Cutting Security Checks (always run)

**CRITICAL**
- Hardcoded credentials or tokens — grep for `sk-`, `AKIA`, `-----BEGIN`, `api_key\s*=\s*["']`, `password\s*=\s*["']`, `token\s*=\s*["']`, `bearer\s+[A-Za-z0-9]`
- Service-account keys on disk inside `platform/` or `portal/` (e.g. `*service-account*.json`, `*.pem`, `*-key.json`)
- `.env` files checked into the tree (should only be `.env.example`)
- Secrets referenced in client-side code (anything matching the above in `portal/`)
- CORS wildcard (`allow_origins=["*"]`) **without** a production fail-fast guard — the repo already has one; flag if it has been weakened or removed
- Prompt-injection surface: user input concatenated directly into LangChain prompts without a sanitization layer

**HIGH**
- Missing input validation on any external-facing path (router bodies, query params, webhook handlers)
- Tenant-scope leaks: `Estimate.find_one`, `Property.find`, `Contact.find`, `Material.find`, etc. without a `company ==` / `company_id ==` filter in the same query
- Unauthenticated endpoints that access paid or sensitive external APIs (Google Maps, OpenAI, Brevo, Firebase Admin, Trello)
- Rate limiting absent on external-API-fanout endpoints
- `eval`, `exec`, `subprocess.run(..., shell=True)`, `os.system` — report every occurrence with context
- SQL / NoSQL injection: f-strings or `%`-formatting inside `.find(...)`, `.aggregate(...)`, or `subprocess.run(...)`
- Known-vulnerable dependency versions (suggest `pip-audit` / `npm audit` for a deeper scan but don't run them here — no network)

**MEDIUM**
- Bare `except:` or `except Exception: pass` that would swallow security-relevant failures
- Weak cryptographic primitives (`md5`, `sha1` for anything security-bearing, `random` for secrets instead of `secrets`)
- HTTP instead of HTTPS in hardcoded URLs pointing at production services
- Overly permissive file / directory permissions set via `chmod`

## Step 3 — Backend (Python) Security Checks

**Run only if Python files are in scope.**

If tooling exists in the venv, run first:

```bash
cd platform
source .venv/bin/activate
# Only run tools that are actually installed; do NOT pip install.
command -v bandit >/dev/null 2>&1 && bandit -q -r <scope> -x tests/
command -v pip-audit >/dev/null 2>&1 && pip-audit --progress-spinner off || true
```

Surface output under the appropriate severity. If a tool is not installed, skip it silently — do not attempt to install.

Then check manually:

**CRITICAL**
- LangChain `.ainvoke(user_message)` called without a system-prompt layer constraining the model (prompt-injection)
- Pydantic models accepting `dict` / `Any` for fields that should be typed (allows arbitrary payloads)

**HIGH**
- Beanie queries missing tenant scoping — for each `Model.find_one`, `Model.find`, `Model.get`, confirm a `company` / `company_id` equality is present in the same expression or before the `.to_list()`. Known pattern: [agents/estimate/service.py](platform/agents/estimate/service.py) `_resolve_latest_estimate` was fixed for this — look for regressions.
- Blocking calls (`requests.get`, `time.sleep`, `pymongo`) inside `async def` route handlers
- Firebase Admin SDK initialization without `FIREBASE_AUTH_DISABLED` fail-fast in production (pattern used in [main.py](platform/main.py))
- Audit-log write omitted on mutations to `Estimate`, `Property`, `Contact`, `Material`, `Labour`, `Equipment`, `Company`, `User`
- JWT / Firebase token verification skipped or weakened

**MEDIUM**
- `fetch_link()` called inside a loop (N+1) — performance but also DoS surface
- Missing `limit=` on unbounded `.to_list()` queries returning user-visible data

## Step 4 — Frontend (React) Security Checks

**Run only if frontend files are in scope.**

**CRITICAL**
- `dangerouslySetInnerHTML` without a DOMPurify / sanitizer wrapper (XSS)
- User input rendered via `innerHTML` / `document.write`
- API keys, OAuth secrets, service-account material anywhere in `portal/src/**`
- Firebase config with secret keys (should only contain public `apiKey`, `authDomain`, etc.)

**HIGH**
- `localStorage` / `sessionStorage` storing auth tokens or PII
- `fetch` / `axios` to external (non-platform) origins with credentials attached
- React-Router routes exposing admin / internal routes without a role gate
- `eval()`, `new Function()`, `setTimeout` with string arg

**MEDIUM**
- Hard-coded URLs pointing at production API — should be env-driven via `import.meta.env`
- Missing CSP / Permissions-Policy / HSTS headers in Firebase Hosting config

## Step 5 — Severity Report

Format each finding as:

```
[SEVERITY] <file>:<line> — <short title>
  Issue: <what's wrong and why it matters>
  Fix:   <suggested remediation>
```

Sort CRITICAL → HIGH → MEDIUM → LOW, with a count summary at the top:

```
CRITICAL: N
HIGH:     N
MEDIUM:   N
LOW:      N
```

## Step 6 — Recommendation

| Status       | Condition                  | Meaning                            |
|--------------|----------------------------|------------------------------------|
| Approve      | Zero CRITICAL, zero HIGH   | Safe to ship                       |
| Warning      | MEDIUM only                | Safe to ship; address in follow-up |
| Block (rec.) | Any CRITICAL or any HIGH   | Recommend blocking the release     |

**Note:** Claude cannot block a commit. "Block (rec.)" is advisory.

## Rules

- Do **not** run any `git` command. This repo is not a git repository in this working tree.
- Do **not** install linters or security tools. If bandit / pip-audit aren't present, skip them and note it.
- Do **not** attempt remediation during the review — report only. Fixes go through the normal `/ultrareview` or direct-edit flow.
- Keep findings specific: every finding must have a file path and line number or a concrete grep pattern that found it.
- Differentiate pre-existing findings from newly-introduced ones where possible (read [documentation/development/code-review-followups.md](documentation/development/code-review-followups.md) to recognise already-tracked items).
