# New Machine Setup

_Last updated: 2026-09-27_

How to take a brand-new Mac from nothing to a running backend (`platform/`) and
frontend (`portal/`). Written after setting up a new Mac Mini (Apple Silicon),
and ordered around the things that actually went wrong there.

For the workspace layout and the development process itself, see
[`development-process.md`](development-process.md). For the per-command
reference (tests, mypy, ruff, bandit), see the root `CLAUDE.md`.

---

## 0. Checklist

1. Install toolchain: Homebrew, Python **3.11**, Node, Docker (§1)
2. Clone `claude-config` and run `./bootstrap.sh` — **don't** clone the product repos by hand (§2)
3. Copy the secrets over from an existing machine (§3)
4. Build the backend venv and install portal packages (§4)
5. Allowlist the machine's IP on the Dev Atlas cluster (§5)
6. Start both apps and verify (§6)

---

## 1. Toolchain

```bash
# Homebrew (if not installed) — https://brew.sh
brew install python@3.11 node git
```

- **Python must be 3.10+; use 3.11** to match production (`render.yaml` pins
  `PYTHON_VERSION` 3.11.5). macOS ships `/usr/bin/python3` as **3.9** — a venv
  built from it installs every package fine and then crashes at import:
  ```
  config.py: google_maps_api_key: str | None = None
  TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
  ```
  Always create the venv with `/opt/homebrew/bin/python3.11` explicitly.
- **Node**: no version is pinned; current Homebrew Node works (verified on
  Node 26).
- **Docker Desktop** — only needed for the backend test suite (local
  MongoDB). Running the apps does not need it. Install from docker.com.

## 2. Clone the workspace

```bash
mkdir -p ~/Development && cd ~/Development
git clone https://github.com/3maples/claude-config.git 3Maples
cd 3Maples
./bootstrap.sh
```

`bootstrap.sh` clones the four product repos into **`platform/`, `portal/`,
`website/`, `documentation/`** and activates the pre-push hooks.

Do **not** `git clone` the product repos yourself. GitHub's default folder
names (`fieldservice-platform/`, `fieldservice-portal/`) break the setup
quietly:
- the `claude-config` `.gitignore` only covers `/platform/` and `/portal/`,
  so the repos show up as untracked there (one `git add .` from committing
  them);
- `CLAUDE.md` and the skills all address `platform/` / `portal/`;
- the pre-push hooks (ruff + mypy gate) are never activated.

If that has already happened: `mv fieldservice-platform platform && mv
fieldservice-portal portal`, then re-run `./bootstrap.sh` (idempotent — it
skips existing repos and just activates the hooks). Verify with
`git -C platform config core.hooksPath` → `.githooks`.

## 3. Secrets — copy from an existing machine

None of these are in git. Copy them from a working machine (AirDrop / USB /
password manager), never through chat or a commit.

| File | Holds |
|---|---|
| `platform/.env` | Non-secret defaults: app name, Brevo template IDs, Firebase project, Google Drive IDs, model overrides, Trello |
| `platform/.env.local` | Secrets + local overrides: `MONGODB_URL` (Dev cluster), `OPENAI_API_KEY`, `FIREBASE_CREDENTIALS_JSON`, Brevo, Stripe, Sentry, Slack, Google Maps, `CORS_ORIGINS`. Loaded with precedence over `.env` |
| `platform/secrets/service-account-key.json` | Google Drive service account, referenced by `GOOGLE_DRIVE_CREDENTIALS_PATH` in `.env.local` |
| `portal/.env` | Firebase web config, reCAPTCHA site key, Sentry DSN |
| `portal/.env.local` | `VITE_API_URL=http://localhost:8000`, Stripe publishable key, App Check debug token, feature flags |
| `portal/.env.development`, `portal/.env.production` | Used by `npm run dev:remote` / builds, not by plain `npm run dev` |
| `.claude/settings.local.json` (workspace root) | Optional — machine-local Claude permissions |

Two failure modes to know:
- **`MONGODB_URL` and `OPENAI_API_KEY` have no default** — without
  `platform/.env.local` the backend won't start at all.
- **The Drive service-account file is easy to miss.** The backend starts and
  looks healthy without it; only estimate document generation fails. Check
  that the path in `GOOGLE_DRIVE_CREDENTIALS_PATH` exists. A relative path
  resolves from the directory uvicorn is started in, so always start it from
  `platform/`. Lock the key down with `chmod 600` — the Drive service warns
  when it is group- or world-readable.

`platform/.env.example` and `portal/.env.example` list the optional keys if
you ever need to rebuild these from scratch.

## 4. Install dependencies

```bash
cd platform
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ../portal
npm install
```

A venv hardcodes its absolute path, so if you rename or move `platform/`
after creating it, delete `.venv` and recreate it.

## 5. Atlas IP allowlist

`platform/.env.local` points at the **Dev** Atlas cluster. Add the new
machine's public IP to the cluster's Network Access list in Atlas, or the
backend hangs on its first database call. (Tests don't need this — they use
local MongoDB, §7.)

## 6. Start and verify

```bash
# Terminal 1 — backend on :8000
cd platform && .venv/bin/uvicorn main:app --reload

# Terminal 2 — portal on :5173 (vite --mode local-dev)
cd portal && npm run dev
```

In Claude Code, both are configured in the workspace's
`.claude/launch.json` (`platform`, `portal`), so the assistant can start them
itself.

Verify:
- [ ] Backend log ends with `Application startup complete.`;
      `curl localhost:8000/` returns `"hello"`
- [ ] Database is reachable (not just configured — motor connects lazily):
      ```bash
      cd platform && .venv/bin/python - <<'EOF'
      import asyncio
      from motor.motor_asyncio import AsyncIOMotorClient
      from config import settings
      async def ping():
          client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=8000)
          return await client.admin.command("ping")
      print(asyncio.run(ping()))
      EOF
      ```
      → `{'ok': 1}`
- [ ] Firebase admin loads:
      `.venv/bin/python -c "import firebase_auth, firebase_admin; firebase_auth.initialize_firebase_admin(); print(firebase_admin.get_app().project_id)"`
- [ ] http://localhost:5173 shows the login page with no console errors
- [ ] Sign in with a real account (proves Firebase web config, App Check,
      CORS and the API together)
- [ ] Generate a document on an estimate (proves the Drive service account)

Harmless noise from Vite: a Node `DEP0205` deprecation warning and
"Browserslist: caniuse-lite is old" (`npx update-browserslist-db@latest`
clears it).

## 7. Running the tests (optional)

The backend suite runs against a local MongoDB container, not Dev:

```bash
cd platform
./scripts/start_test_mongo.sh   # needs Docker Desktop running
./run_tests.sh tests/test_<module>.py
cd ../portal && npm test
```

See the root `CLAUDE.md` → "Backend Testing" for how the test database
override works.
