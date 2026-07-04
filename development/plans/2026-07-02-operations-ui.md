# Operations UI (3Maples Staff Back Office) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give 3Maples staff a separate, root-provisioned class of users who log in through the existing login page but land on an internal Operations Dashboard (companies, users, users-per-company, new/incomplete signups) instead of the customer app.

**Architecture:** A new `StaffUser` Beanie collection (separate from the customer `User` collection) carries staff identity and a staff-only role enum. Firebase remains the single identity provider; `POST /auth` branches on staff membership and returns `user_type: "staff"`. A new `/ops` FastAPI router exposes read endpoints (plus root-only staff management), guarded by a `require_staff_user` dependency that never touches company scoping. The portal adds an `/ops/*` route subtree with its own `OpsLayout` shell and route guards keyed on `user_type`.

**Tech Stack:** FastAPI + Beanie/MongoDB + firebase-admin (backend); React 18 + React Router + Tailwind CSS 4 + existing `src/components/ui/*` primitives (frontend); pytest + Vitest.

## Global Constraints

- **TDD is mandatory** for every functional task: failing test first, then implementation (CLAUDE.md TDD Policy).
- After any `.py` change: `./run_mypy.sh <touched subtree>` and `./run_ruff.sh <touched subtree>` must be clean before the task is complete. Zero-error baseline on both.
- Run **only** the test files named in each task (`./run_tests.sh tests/<file>` / `npm test -- <file>`). Never auto-run the full suite.
- Backend tests need the local test Mongo running: `cd platform && ./scripts/start_test_mongo.sh` (once per session).
- **Every `git commit` requires Simon's fresh, explicit approval** — the commit steps below are checkpoints to *request*, not to execute automatically. `platform/`, `portal/`, and `documentation/` are separate repos; commit in the repo the task touched.
- Datetimes are aware-UTC end-to-end: `datetime.now(timezone.utc)`, never `utcnow()`.
- US spellings everywhere ("canceled", "color", "labor").
- Beanie boolean filters use `beanie.operators.Eq(...)` — a literal `== False` comparison trips ruff E712.
- No behavior change to any customer-facing endpoint other than the two explicitly listed (`POST /auth` gains a staff branch; `POST /auth/signup` gains a staff-email guard).

---

## Part 0 — Design Decisions

### 0.1 How to structure staff users — decision: separate `StaffUser` collection

Three options were considered:

| Option | Verdict |
|---|---|
| **A. Add values to `UserRole`** (e.g. `OPERATIONS`) | ❌ `UserRole` (Owner/Admin/Member) is a *company-scoped* axis. Every existing check (`user.role in {OWNER, ADMIN}` at 9+ sites in `auth.py`, `users.py`, `dependencies.py`, `companies.py`, `estimates.py`, `crud_handlers.py`) assumes a tenant context. Adding a tenant-less role means auditing all of them, forever. |
| **B. `user_type` discriminator field on `User`** | ⚠️ Workable, but staff records would flow through every existing `User` query, serializer, invitation flow, and Maple identity path. `company=None` staff would be indistinguishable (by shape) from customers mid-onboarding — exactly the "New Users" population the dashboard reports on. |
| **C. Separate `StaffUser` collection** ✅ | Hard isolation: company-scoped queries **cannot** return staff; the customer `User` model, its role checks, billing/overage fields, and onboarding logic stay untouched (zero regression surface). Staff get their own role enum that evolves independently. Cost: one extra indexed `find_one` inside `POST /auth`, and a cross-collection uniqueness guard at signup. |

**Decision: Option C.** Firebase email uniqueness guarantees one account is *either* staff or customer; we enforce the same invariant in Mongo (signup refuses emails present in `staff_users`; staff provisioning refuses emails present in `users`).

### 0.2 Staff roles (naming TBD — working proposal)

```python
class StaffRole(str, Enum):
    ROOT = "root"            # The 3Maples Root User. Everything, incl. managing staff.
    OPS_ADMIN = "ops_admin"  # Future write operations (support actions, company fixes).
    OPS_VIEWER = "ops_viewer"# Read-only Operations Dashboard access.
```

V1 permission matrix (all four dashboard features are read-only, so it stays simple):

| Capability | root | ops_admin | ops_viewer |
|---|---|---|---|
| View companies / users / new users | ✅ | ✅ | ✅ |
| Create / disable / re-role staff users | ✅ | ❌ | ❌ |

Renaming later is a one-file enum change + data migration — the plan does not block on final naming.

### 0.3 Provisioning: no self-signup, root bootstrap via script

- Staff users are created **only** through `POST /ops/staff` (root-only). The public `/auth/signup` path can never produce one.
- Chicken-and-egg for the first root: a one-time CLI script `platform/scripts/create_root_user.py` (run manually by Simon) creates the Firebase account (`email_verified=True`), inserts the `StaffUser` with `staff_role=root`, and sends a password-reset email so the root sets their own password. The same provisioning service backs the root-only endpoint afterward.

### 0.4 Login flow: one login page, branch on `user_type`

Staff log in at the normal `/login` with Firebase email+password. `POST /auth` checks `staff_users` **first** (tiny indexed collection); on match it returns a staff payload (`user_type: "staff"`, `staff_role`, `company_id: null`) and the portal routes to `/ops` instead of `/dashboard`. Customers get `user_type: "customer"` added to the existing payload (additive, non-breaking).

Client-side `user_type` is a routing convenience only — **all authorization is server-side** via `require_staff_user`, which re-resolves the staff record from the verified Firebase token on every request.

### 0.5 "New Users" definition

A user appears on the New Users page when any of these holds (first match wins as their `stage`):

1. **`unverified`** — Mongo `User` exists, Firebase `email_verified` is `False` (fetched in batches of 100 via `firebase_admin.auth.get_users`).
2. **`no_company`** — verified but `user.company is None` (signed up, never completed the Create Company step).
3. **`onboarding_incomplete`** — has a company with `onboarding_completed=False`; the row shows the resume step (`contacts` … `plan`).

Firebase lookup failures degrade gracefully (`email_verified: null` → stage falls through to 2/3) so the page never 500s on a Firebase hiccup.

### 0.6 API surface (`/ops` router, staff-only)

| Endpoint | Access | Purpose |
|---|---|---|
| `GET /ops/companies` | any staff | Paginated companies + details (search, status filter, user counts) |
| `GET /ops/companies/{id}` | any staff | Single company detail |
| `GET /ops/companies/{id}/users` | any staff | Users attached to a company |
| `GET /ops/users` | any staff | Paginated all users (search, company filter) |
| `GET /ops/new-users` | any staff | Unverified / no-company / onboarding-incomplete users |
| `GET /ops/staff` | root | List staff users |
| `POST /ops/staff` | root | Provision a staff user |
| `PATCH /ops/staff/{id}` | root | Change role / disable (never self) |

Registered in `main.py` with the standard `protected_route_dependencies` (App Check + verified Firebase token); each route additionally depends on `require_staff_user` / `require_root_staff`. Company-scoping helpers (`assert_company_access` etc.) are **never** called from this router.

---

## Part 1 — Operations UI Layout

### Shell (`OpsLayout`)

Same structural skeleton as `PortalLayout` (fixed left sidebar + content outlet) so it feels like the same product family, but visually unmistakable: **dark slate sidebar** (`bg-slate-900`) instead of brand purple, with a "3Maples **OPERATIONS**" wordmark + badge. No Maple AI panel, no billing dialogs, no company dialog.

```
┌──────────────┬──────────────────────────────────────────────────┐
│ 3MAPLES      │  Companies                                 [◉ SN]│
│ [OPERATIONS] │  ┌ Search…────────────┐ ┌ Status: All ▾┐         │
│              │  ┌──────────────────────────────────────────────┐│
│ ▸ Companies  │  │ Name     Industry  Status  Plan  Users  Est. ││
│   Users      │  │ Acme L.  Landsc.   active  pro     4   12/25 ││
│   New Users  │  │ …rows — click → company detail               ││
│   Staff  ⚿   │  └──────────────────────────────────────────────┘│
│              │  Showing 1–25 of 132        ‹ 1 2 3 ›            │
│ ◉ S. Neal ▾  │                                                  │
│   (logout)   │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
   ⚿ Staff nav item renders only for staff_role === "root"
```

- `/ops` (index) → redirects to `/ops/companies` (no vanity overview page in v1 — YAGNI; count cards can come later).
- All pages are **table-centric**: filter bar on top, `<Table>` from `src/components/ui/table.tsx`, `<Badge>` for statuses, `LoadingState`/`ErrorState` from `PageState.tsx`, simple pagination footer.

### Pages

**Companies** (`/ops/companies`) — search-by-name + status filter; columns: Name, Industry, Status (badge: active/archived), Plan, Users, Estimates used (`12/25`), Created. Row click → detail.

**Company detail** (`/ops/companies/:id`) — two stacked cards:
```
┌ Company ────────────────────────────────────────────┐
│ Acme Landscaping           [active] [pro plan]      │
│ email · phone · city, prov · created 2026-03-14     │
│ Onboarding: completed  |  Estimates: 12 / 25        │
└─────────────────────────────────────────────────────┘
┌ Users (4) ──────────────────────────────────────────┐
│ Name        Email             Role    Joined        │
└─────────────────────────────────────────────────────┘
```

**Users** (`/ops/users`) — search (name/email) + company filter; columns: Name, Email, Role (badge), Company (link → company detail), Phone, Created.

**New Users** (`/ops/new-users`) — stage filter chips `[All] [Unverified] [No company] [Onboarding incomplete]`; columns: Name, Email, Stage (badge: amber/blue/violet), Onboarding step (when applicable), Company, Signed up. Sorted newest first.

**Staff** (`/ops/staff`, root only) — table of staff (Name, Email, Role, Status, Created) + "Add staff user" dialog (email, first/last name, role) + per-row disable/re-role actions.

---

## Part 2 — Backend Tasks

### Task 1: `StaffUser` model

**Files:**
- Create: `platform/models/staff_user.py`
- Modify: `platform/models/__init__.py` (export), `platform/database.py` (register in `document_models`)
- Test: `platform/tests/test_staff_user_model.py`

**Interfaces:**
- Produces: `StaffUser` document (`email: str` lowercase-unique, `first_name`, `last_name`, `staff_role: StaffRole`, `status: StaffUserStatus`, `created_by: Optional[PydanticObjectId]`, timestamps), enums `StaffRole {ROOT="root", OPS_ADMIN="ops_admin", OPS_VIEWER="ops_viewer"}`, `StaffUserStatus {ACTIVE="active", DISABLED="disabled"}`. Collection `staff_users`.

- [ ] **Step 1: Write the failing test**

```python
# platform/tests/test_staff_user_model.py
import pytest
from models.staff_user import StaffRole, StaffUser, StaffUserStatus


@pytest.fixture()
def staff_email():
    return "ops.model.test@3maples.ai"


def _cleanup(client, email):
    async def _run():
        await StaffUser.find(StaffUser.email == email).delete()
    client.portal.call(_run)


def test_staff_user_insert_and_defaults(client, staff_email):
    _cleanup(client, staff_email)

    async def _run():
        staff = StaffUser(
            email=staff_email.upper(),  # must normalize to lowercase
            first_name="Ops",
            last_name="Tester",
            staff_role=StaffRole.OPS_VIEWER,
        )
        await staff.insert()
        return await StaffUser.find_one(StaffUser.email == staff_email)

    found = client.portal.call(_run)
    assert found is not None
    assert found.email == staff_email  # lowercased
    assert found.status == StaffUserStatus.ACTIVE
    assert found.created_at is not None
    _cleanup(client, staff_email)


def test_staff_role_values():
    assert {r.value for r in StaffRole} == {"root", "ops_admin", "ops_viewer"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform && ./run_tests.sh tests/test_staff_user_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'models.staff_user'`

- [ ] **Step 3: Write the model**

```python
# platform/models/staff_user.py
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Insert, PydanticObjectId, Replace, before_event
from pydantic import Field, field_validator
from pymongo import ASCENDING, IndexModel


class StaffRole(str, Enum):
    ROOT = "root"
    OPS_ADMIN = "ops_admin"
    OPS_VIEWER = "ops_viewer"


class StaffUserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class StaffUser(Document):
    """Internal 3Maples staff account. Deliberately separate from the customer
    ``User`` collection: staff have no company, no billing state, and must never
    surface in tenant-scoped queries."""

    email: str
    first_name: str
    last_name: str
    staff_role: StaffRole
    status: StaffUserStatus = StaffUserStatus.ACTIVE
    created_by: Optional[PydanticObjectId] = None  # StaffUser id of the provisioning root
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @before_event([Replace, Insert])
    async def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "staff_users"
        indexes = [IndexModel([("email", ASCENDING)], unique=True)]
```

Add to `platform/models/__init__.py` (follow the existing export style in that file):

```python
from models.staff_user import StaffRole, StaffUser, StaffUserStatus  # noqa: E402  (if the file's E402 carve-out applies)
```

and extend its `__all__` with `"StaffRole", "StaffUser", "StaffUserStatus"`.

Register in `platform/database.py` `document_models` list (after `User`):

```python
            StaffUser,
```

with the matching import at the top of `database.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform && ./run_tests.sh tests/test_staff_user_model.py -v`
Expected: 2 passed

- [ ] **Step 5: Gates**

Run: `./run_mypy.sh models/staff_user.py database.py && ./run_ruff.sh models/staff_user.py models/__init__.py database.py`
Expected: zero errors

- [ ] **Step 6: Commit checkpoint** — request Simon's approval for `feat: add StaffUser model for 3Maples staff accounts` in `platform/`.

---

### Task 2: Staff auth dependencies + `/auth` staff branch + signup guard

**Files:**
- Modify: `platform/dependencies.py` (add `require_staff_user`, `require_root_staff`)
- Modify: `platform/routers/auth.py` (staff branch in `POST /auth` at line ~338; guard in `POST /auth/signup` at line ~379; new `_serialize_staff_user`; add `"user_type": "customer"` to `_serialize_user` at line ~78)
- Test: `platform/tests/test_ops_auth.py`

**Interfaces:**
- Consumes: `StaffUser`, `StaffRole`, `StaffUserStatus` (Task 1); existing `verify_verified_firebase_token`.
- Produces: `async def require_staff_user(decoded_token=Depends(verify_verified_firebase_token)) -> StaffUser` (403 for non-staff/disabled); `async def require_root_staff(staff=Depends(require_staff_user)) -> StaffUser` (403 unless `staff_role == ROOT`); `POST /auth` returns `{"user_type": "staff", "staff_role": "<role>", "user_id", "email", "first_name", "last_name", "company_id": None, ...}` for staff and adds `"user_type": "customer"` for customers.

- [ ] **Step 1: Write the failing tests**

```python
# platform/tests/test_ops_auth.py
import pytest
from models.staff_user import StaffRole, StaffUser, StaffUserStatus

STAFF_EMAIL = "ops.auth.test@3maples.ai"
DISABLED_EMAIL = "ops.disabled.test@3maples.ai"


@pytest.fixture()
def staff_user(client):
    async def _create():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
        staff = StaffUser(
            email=STAFF_EMAIL, first_name="Ops", last_name="Auth",
            staff_role=StaffRole.OPS_VIEWER,
        )
        await staff.insert()
        return staff

    staff = client.portal.call(_create)
    yield staff

    async def _cleanup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
    client.portal.call(_cleanup)


def test_auth_returns_staff_payload(client, staff_user):
    resp = client.post("/auth", headers={"X-Test-Email": STAFF_EMAIL})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_type"] == "staff"
    assert data["staff_role"] == "ops_viewer"
    assert data["company_id"] is None


def test_auth_customer_payload_tagged(client, test_company_id):
    # default conftest owner header is already set
    resp = client.post("/auth")
    assert resp.status_code == 200
    assert resp.json()["user_type"] == "customer"


def test_auth_disabled_staff_rejected(client):
    async def _create():
        await StaffUser.find(StaffUser.email == DISABLED_EMAIL).delete()
        await StaffUser(
            email=DISABLED_EMAIL, first_name="Ops", last_name="Disabled",
            staff_role=StaffRole.OPS_VIEWER, status=StaffUserStatus.DISABLED,
        ).insert()
    client.portal.call(_create)

    resp = client.post("/auth", headers={"X-Test-Email": DISABLED_EMAIL})
    assert resp.status_code == 403

    async def _cleanup():
        await StaffUser.find(StaffUser.email == DISABLED_EMAIL).delete()
    client.portal.call(_cleanup)


def test_signup_rejects_staff_email(client, staff_user):
    resp = client.post(
        "/auth/signup",
        json={"email": STAFF_EMAIL, "first_name": "X", "last_name": "Y"},
        headers={"X-Test-Email": STAFF_EMAIL},
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_ops_auth.py -v`
Expected: FAIL — `user_type` KeyError on the staff test; signup test returns 200/creates a user.

- [ ] **Step 3: Implement**

In `platform/dependencies.py` (append; mirrors `assert_is_manager` style):

```python
async def require_staff_user(
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    """FastAPI dependency: resolve an ACTIVE 3Maples staff account.

    Staff live in the separate ``staff_users`` collection and are never
    company-scoped; this dependency must not be combined with the
    company-access helpers above.
    """
    from models import StaffUser
    from models.staff_user import StaffUserStatus

    email = (decoded_token.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing email claim in token",
        )
    staff = await StaffUser.find_one(StaffUser.email == email)
    if not staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    if staff.status != StaffUserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff account is disabled")
    return staff


async def require_root_staff(staff=Depends(require_staff_user)):
    """FastAPI dependency: require the root staff role."""
    from models.staff_user import StaffRole

    if staff.staff_role != StaffRole.ROOT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the root user can perform this action",
        )
    return staff
```

In `platform/routers/auth.py`:

1. Import `StaffUser` and `StaffUserStatus` alongside the existing `models` imports.
2. Add `"user_type": "customer",` to the dict returned by `_serialize_user` (line ~78).
3. Add below `_serialize_user`:

```python
def _serialize_staff_user(staff: "StaffUser") -> dict:
    return {
        "message": "Authentication successful",
        "user_id": str(staff.id),
        "user_type": "staff",
        "staff_role": staff.staff_role.value,
        "company_id": None,
        "email": staff.email,
        "first_name": staff.first_name,
        "last_name": staff.last_name,
        "role": None,
        "phone": None,
        "onboarding_completed": True,
        "onboarding_step": None,
    }
```

4. In `authenticate` (`POST /auth`, line ~338), before the customer lookup:

```python
@router.post("/auth")
async def authenticate(decoded_token: dict = Depends(verify_verified_firebase_token)):
    """Authenticate a Firebase user against a platform user record."""
    email = (decoded_token.get("email") or "").strip().lower()
    if email:
        staff = await StaffUser.find_one(StaffUser.email == email)
        if staff:
            if staff.status != StaffUserStatus.ACTIVE:
                raise HTTPException(status_code=403, detail="Staff account is disabled")
            return _serialize_staff_user(staff)
    user, _email = await _require_authenticated_user(decoded_token)
    # ... existing company/archived logic unchanged
```

5. In `signup` (`POST /auth/signup`), right before `existing_user = await _find_user_by_email(request_email)`:

```python
    if await StaffUser.find_one(StaffUser.email == request_email):
        raise HTTPException(status_code=403, detail="This email cannot be used for signup")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_ops_auth.py tests/test_auth_api.py -v` (the second file guards against regression in the customer path)
Expected: all pass

- [ ] **Step 5: Gates**

Run: `./run_mypy.sh dependencies.py routers/auth.py && ./run_ruff.sh dependencies.py routers/auth.py`
Expected: zero errors

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: staff auth dependencies + staff branch in /auth` in `platform/`.

---

### Task 3: Staff provisioning service + root bootstrap script

**Files:**
- Create: `platform/services/staff_service.py`
- Create: `platform/scripts/create_root_user.py`
- Test: `platform/tests/test_staff_service.py`

**Interfaces:**
- Consumes: `StaffUser`, `StaffRole` (Task 1); `firebase_admin.auth`; `services.auth_email.send_password_reset_email`; `config.settings.firebase_auth_disabled`.
- Produces: `async def provision_staff_user(*, email: str, first_name: str, last_name: str, staff_role: StaffRole, created_by: PydanticObjectId | None = None) -> StaffUser`, raising `StaffProvisioningError(str)` on conflicts. Used by Task 4's endpoint and the bootstrap script.

- [ ] **Step 1: Write the failing tests**

```python
# platform/tests/test_staff_service.py
import pytest
from models import User, UserRole
from models.staff_user import StaffRole, StaffUser
from services.staff_service import StaffProvisioningError, provision_staff_user

NEW_STAFF = "ops.provision.test@3maples.ai"
TAKEN_BY_CUSTOMER = "ops.customer.clash@3maples.ai"


@pytest.fixture(autouse=True)
def _cleanup(client):
    async def _run():
        await StaffUser.find({"email": {"$in": [NEW_STAFF, TAKEN_BY_CUSTOMER]}}).delete()
        await User.find(User.email == TAKEN_BY_CUSTOMER).delete()
    client.portal.call(_run)
    yield
    client.portal.call(_run)


def test_provision_creates_active_staff(client):
    async def _run():
        return await provision_staff_user(
            email=NEW_STAFF.upper(), first_name="New", last_name="Staff",
            staff_role=StaffRole.OPS_VIEWER,
        )
    staff = client.portal.call(_run)
    assert staff.email == NEW_STAFF
    assert staff.staff_role == StaffRole.OPS_VIEWER


def test_provision_rejects_existing_customer_email(client):
    async def _run():
        await User(
            email=TAKEN_BY_CUSTOMER, first_name="C", last_name="U",
            role=UserRole.MEMBER, company=None,
        ).insert()
        with pytest.raises(StaffProvisioningError):
            await provision_staff_user(
                email=TAKEN_BY_CUSTOMER, first_name="X", last_name="Y",
                staff_role=StaffRole.OPS_VIEWER,
            )
    client.portal.call(_run)


def test_provision_rejects_duplicate_staff(client):
    async def _run():
        await provision_staff_user(
            email=NEW_STAFF, first_name="A", last_name="B",
            staff_role=StaffRole.OPS_VIEWER,
        )
        with pytest.raises(StaffProvisioningError):
            await provision_staff_user(
                email=NEW_STAFF, first_name="A", last_name="B",
                staff_role=StaffRole.ROOT,
            )
    client.portal.call(_run)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_staff_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.staff_service'`

- [ ] **Step 3: Implement the service**

```python
# platform/services/staff_service.py
"""Provisioning for 3Maples staff accounts.

Staff cannot self-signup: accounts are created only by the root user (via the
/ops/staff endpoint) or the one-time bootstrap script. Provisioning ensures a
Firebase account exists (created verified — root vouches for staff emails) and
sends a password-reset email so the new staff member sets their own password.
"""
import asyncio
import logging

from beanie import PydanticObjectId
from firebase_admin import auth as firebase_admin_auth

from config import settings
from models import StaffUser, User
from models.staff_user import StaffRole
from services.auth_email import send_password_reset_email

logger = logging.getLogger(__name__)


class StaffProvisioningError(Exception):
    """Raised when a staff account cannot be provisioned (caller maps to 4xx)."""


def _ensure_firebase_account(email: str) -> None:
    try:
        firebase_admin_auth.get_user_by_email(email)
    except firebase_admin_auth.UserNotFoundError:
        firebase_admin_auth.create_user(email=email, email_verified=True)


async def provision_staff_user(
    *,
    email: str,
    first_name: str,
    last_name: str,
    staff_role: StaffRole,
    created_by: PydanticObjectId | None = None,
) -> StaffUser:
    normalized = email.strip().lower()
    if not normalized:
        raise StaffProvisioningError("Email is required")

    if await User.find_one(User.email == normalized):
        raise StaffProvisioningError("Email already belongs to a portal user")
    if await StaffUser.find_one(StaffUser.email == normalized):
        raise StaffProvisioningError("A staff user with this email already exists")

    if not settings.firebase_auth_disabled:
        await asyncio.to_thread(_ensure_firebase_account, normalized)
        try:
            await send_password_reset_email(normalized)
        except Exception:  # noqa: BLE001 — provisioning must not fail on email delivery
            logger.warning("Password-reset email failed for new staff %s", normalized)

    staff = StaffUser(
        email=normalized,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        staff_role=staff_role,
        created_by=created_by,
    )
    await staff.insert()
    return staff
```

*(Check `send_password_reset_email`'s actual signature in `services/auth_email.py` — if it is sync, drop the `await`.)*

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_staff_service.py -v`
Expected: 3 passed (Firebase calls skipped because `FIREBASE_AUTH_DISABLED=true` in tests)

- [ ] **Step 5: Write the bootstrap script** (config/docs change — no TDD per policy)

```python
# platform/scripts/create_root_user.py
"""One-time bootstrap: create the initial 3Maples ROOT staff user.

Usage (from platform/, venv active, .env/.env.local configured):
    python scripts/create_root_user.py simon@tangz.com Simon Neal
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import init_db  # noqa: E402  (sys.path bootstrap must run first)
from models.staff_user import StaffRole, StaffUser  # noqa: E402
from services.staff_service import StaffProvisioningError, provision_staff_user  # noqa: E402


async def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 1
    email, first_name, last_name = sys.argv[1], sys.argv[2], sys.argv[3]

    await init_db()
    existing_root = await StaffUser.find_one(StaffUser.staff_role == StaffRole.ROOT)
    if existing_root:
        print(f"A root user already exists: {existing_root.email}. Aborting.")
        return 1
    try:
        staff = await provision_staff_user(
            email=email, first_name=first_name, last_name=last_name,
            staff_role=StaffRole.ROOT,
        )
    except StaffProvisioningError as err:
        print(f"Failed: {err}")
        return 1
    print(f"Root staff user created: {staff.email} (id={staff.id}).")
    print("A password-reset email was sent — use it to set the password.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

*(Confirm `init_db()`'s import path/name against an existing script in `platform/scripts/` and mirror its bootstrap idiom exactly — `ruff.toml` already carves out E402 for `scripts/**`.)*

- [ ] **Step 6: Gates**

Run: `./run_mypy.sh services/staff_service.py scripts/create_root_user.py && ./run_ruff.sh services/staff_service.py scripts/create_root_user.py`
Expected: zero errors

- [ ] **Step 7: Commit checkpoint** — request approval for `feat: staff provisioning service + root bootstrap script` in `platform/`.

---

### Task 4: `/ops` router — staff management endpoints (root-only) + registration

**Files:**
- Create: `platform/routers/ops.py`
- Modify: `platform/routers/__init__.py` (export `ops_router`), `platform/main.py` (include with `protected_route_dependencies`)
- Test: `platform/tests/test_ops_staff_api.py`

**Interfaces:**
- Consumes: `require_staff_user`, `require_root_staff` (Task 2); `provision_staff_user`, `StaffProvisioningError` (Task 3).
- Produces: `GET/POST /ops/staff`, `PATCH /ops/staff/{staff_id}`; router object `router = APIRouter(prefix="/ops", tags=["ops"])` that Tasks 5–7 extend. Staff JSON shape: `{"id", "email", "first_name", "last_name", "staff_role", "status", "created_at"}`.

- [ ] **Step 1: Write the failing tests**

```python
# platform/tests/test_ops_staff_api.py
import pytest
from models.staff_user import StaffRole, StaffUser

ROOT_EMAIL = "ops.root.test@3maples.ai"
VIEWER_EMAIL = "ops.viewer.test@3maples.ai"
CREATED_EMAIL = "ops.created.test@3maples.ai"


@pytest.fixture()
def root_and_viewer(client):
    async def _setup():
        await StaffUser.find(
            {"email": {"$in": [ROOT_EMAIL, VIEWER_EMAIL, CREATED_EMAIL]}}
        ).delete()
        root = StaffUser(email=ROOT_EMAIL, first_name="Root", last_name="User",
                         staff_role=StaffRole.ROOT)
        viewer = StaffUser(email=VIEWER_EMAIL, first_name="View", last_name="Only",
                           staff_role=StaffRole.OPS_VIEWER)
        await root.insert()
        await viewer.insert()
        return root, viewer

    root, viewer = client.portal.call(_setup)
    yield root, viewer

    async def _cleanup():
        await StaffUser.find(
            {"email": {"$in": [ROOT_EMAIL, VIEWER_EMAIL, CREATED_EMAIL]}}
        ).delete()
    client.portal.call(_cleanup)


def test_root_can_create_staff(client, root_and_viewer):
    resp = client.post(
        "/ops/staff",
        json={"email": CREATED_EMAIL, "first_name": "New", "last_name": "Hire",
              "staff_role": "ops_viewer"},
        headers={"X-Test-Email": ROOT_EMAIL},
    )
    assert resp.status_code == 201
    assert resp.json()["staff_role"] == "ops_viewer"


def test_viewer_cannot_create_staff(client, root_and_viewer):
    resp = client.post(
        "/ops/staff",
        json={"email": CREATED_EMAIL, "first_name": "N", "last_name": "H",
              "staff_role": "ops_viewer"},
        headers={"X-Test-Email": VIEWER_EMAIL},
    )
    assert resp.status_code == 403


def test_customer_cannot_access_ops(client, root_and_viewer):
    # default conftest header is the test company owner — a customer
    resp = client.get("/ops/staff")
    assert resp.status_code == 403


def test_root_cannot_modify_self(client, root_and_viewer):
    root, _viewer = root_and_viewer
    resp = client.patch(
        f"/ops/staff/{root.id}",
        json={"status": "disabled"},
        headers={"X-Test-Email": ROOT_EMAIL},
    )
    assert resp.status_code == 400


def test_root_can_disable_viewer(client, root_and_viewer):
    _root, viewer = root_and_viewer
    resp = client.patch(
        f"/ops/staff/{viewer.id}",
        json={"status": "disabled"},
        headers={"X-Test-Email": ROOT_EMAIL},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disabled"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_ops_staff_api.py -v`
Expected: FAIL — 404s (router not registered)

- [ ] **Step 3: Implement the router**

```python
# platform/routers/ops.py
"""Operations (staff-only) endpoints for the 3Maples back office.

Every route depends on require_staff_user (or require_root_staff) and is
deliberately outside company scoping — never call assert_company_access here.
"""
import logging
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies import require_root_staff, require_staff_user
from models import StaffUser
from models.staff_user import StaffRole, StaffUserStatus
from services.staff_service import StaffProvisioningError, provision_staff_user

router = APIRouter(prefix="/ops", tags=["ops"])
logger = logging.getLogger(__name__)


def _serialize_staff(staff: StaffUser) -> dict:
    return {
        "id": str(staff.id),
        "email": staff.email,
        "first_name": staff.first_name,
        "last_name": staff.last_name,
        "staff_role": staff.staff_role.value,
        "status": staff.status.value,
        "created_at": staff.created_at.isoformat(),
    }


class CreateStaffRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    staff_role: StaffRole


class UpdateStaffRequest(BaseModel):
    staff_role: Optional[StaffRole] = None
    status: Optional[StaffUserStatus] = None


@router.get("/staff")
async def list_staff(root: StaffUser = Depends(require_root_staff)):
    staff = await StaffUser.find_all().sort(-StaffUser.created_at).to_list()
    return {"items": [_serialize_staff(s) for s in staff], "total": len(staff)}


@router.post("/staff", status_code=201)
async def create_staff(
    body: CreateStaffRequest,
    root: StaffUser = Depends(require_root_staff),
):
    try:
        staff = await provision_staff_user(
            email=body.email,
            first_name=body.first_name,
            last_name=body.last_name,
            staff_role=body.staff_role,
            created_by=root.id,
        )
    except StaffProvisioningError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
    return _serialize_staff(staff)


@router.patch("/staff/{staff_id}")
async def update_staff(
    staff_id: PydanticObjectId,
    body: UpdateStaffRequest,
    root: StaffUser = Depends(require_root_staff),
):
    staff = await StaffUser.get(staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff user not found")
    if staff.id == root.id:
        raise HTTPException(status_code=400, detail="You cannot modify your own staff account")
    if body.staff_role is not None:
        staff.staff_role = body.staff_role
    if body.status is not None:
        staff.status = body.status
    await staff.save()
    return _serialize_staff(staff)
```

Register: export `ops_router` from `platform/routers/__init__.py` following the existing pattern (add to its `__all__` if the module is a re-export hub), and in `platform/main.py` alongside the other protected routers:

```python
app.include_router(ops_router, dependencies=protected_route_dependencies)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_ops_staff_api.py -v`
Expected: 5 passed

- [ ] **Step 5: Gates**

Run: `./run_mypy.sh routers/ops.py main.py && ./run_ruff.sh routers/ops.py routers/__init__.py main.py`
Expected: zero errors

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: /ops router with root-only staff management` in `platform/`.

---

### Task 5: `/ops/companies` list + detail

**Files:**
- Modify: `platform/routers/ops.py`
- Test: `platform/tests/test_ops_companies_api.py`

**Interfaces:**
- Consumes: `require_staff_user`; `Company`, `User` models; router from Task 4.
- Produces: `GET /ops/companies?search=&status=&page=&page_size=` → `{"items": [CompanySummary], "total", "page", "page_size"}`; `GET /ops/companies/{company_id}` → CompanySummary. Shape: `{"id", "name", "industry", "email", "phone", "city", "prov_state", "country", "status", "plan_lookup_key", "stripe_subscription_status", "onboarding_completed", "onboarding_step", "user_count", "estimates_created", "estimates_allowed", "created_at"}`.

- [ ] **Step 1: Write the failing tests**

```python
# platform/tests/test_ops_companies_api.py
import pytest
from models.staff_user import StaffRole, StaffUser

STAFF_EMAIL = "ops.companies.test@3maples.ai"


@pytest.fixture()
def staff_headers(client):
    async def _setup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
        await StaffUser(email=STAFF_EMAIL, first_name="Ops", last_name="C",
                        staff_role=StaffRole.OPS_VIEWER).insert()
    client.portal.call(_setup)
    yield {"X-Test-Email": STAFF_EMAIL}

    async def _cleanup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
    client.portal.call(_cleanup)


def test_list_companies_includes_test_company(client, staff_headers, test_company_id):
    resp = client.get("/ops/companies", params={"search": "Test Company"},
                      headers=staff_headers)
    assert resp.status_code == 200
    data = resp.json()
    ids = [item["id"] for item in data["items"]]
    assert test_company_id in ids
    row = next(item for item in data["items"] if item["id"] == test_company_id)
    assert row["user_count"] >= 1  # the conftest default owner
    assert {"status", "plan_lookup_key", "estimates_created", "created_at"} <= row.keys()


def test_company_detail(client, staff_headers, test_company_id):
    resp = client.get(f"/ops/companies/{test_company_id}", headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == test_company_id


def test_company_detail_404(client, staff_headers):
    resp = client.get("/ops/companies/000000000000000000000000", headers=staff_headers)
    assert resp.status_code == 404


def test_customer_forbidden(client, test_company_id):
    resp = client.get("/ops/companies")  # default owner header
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_ops_companies_api.py -v`
Expected: FAIL — 404 (routes missing)

- [ ] **Step 3: Implement** (append to `routers/ops.py`; extend imports with `re`, `Query`, `Company`, `User`)

```python
def _serialize_company_summary(company: "Company", user_count: int) -> dict:
    return {
        "id": str(company.id),
        "name": company.name,
        "industry": company.industry.value if company.industry else None,
        "email": company.email,
        "phone": company.phone,
        "city": company.city,
        "prov_state": company.prov_state,
        "country": company.country,
        "status": company.status.value,
        "plan_lookup_key": company.plan_lookup_key,
        "stripe_subscription_status": company.stripe_subscription_status,
        "onboarding_completed": company.onboarding_completed,
        "onboarding_step": company.onboarding_step.value,
        "user_count": user_count,
        "estimates_created": company.number_of_estimates_created,
        "estimates_allowed": company.total_estimates_allowed,
        "created_at": company.created_at.isoformat(),
    }


async def _user_counts_by_company() -> dict:
    rows = await User.aggregate(
        [{"$group": {"_id": "$company", "count": {"$sum": 1}}}]
    ).to_list()
    return {row["_id"]: row["count"] for row in rows if row["_id"] is not None}


@router.get("/companies")
async def list_companies(
    staff: StaffUser = Depends(require_staff_user),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    query: dict = {}
    if search and search.strip():
        query["name"] = {"$regex": re.escape(search.strip()), "$options": "i"}
    if status_filter:
        query["status"] = status_filter

    total = await Company.find(query).count()
    companies = (
        await Company.find(query)
        .sort(-Company.created_at)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    counts = await _user_counts_by_company()
    return {
        "items": [_serialize_company_summary(c, counts.get(c.id, 0)) for c in companies],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/companies/{company_id}")
async def get_company(
    company_id: PydanticObjectId,
    staff: StaffUser = Depends(require_staff_user),
):
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    user_count = await User.find(User.company == company_id).count()
    return _serialize_company_summary(company, user_count)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_ops_companies_api.py -v`
Expected: 4 passed

- [ ] **Step 5: Gates** — `./run_mypy.sh routers/ops.py && ./run_ruff.sh routers/ops.py` → zero errors

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: ops companies list + detail endpoints` in `platform/`.

---

### Task 6: `/ops/users` + `/ops/companies/{id}/users`

**Files:**
- Modify: `platform/routers/ops.py`
- Test: `platform/tests/test_ops_users_api.py`

**Interfaces:**
- Consumes: router + serializers from Tasks 4–5.
- Produces: `GET /ops/users?search=&company_id=&page=&page_size=` → paginated `{"items": [UserSummary], ...}`; `GET /ops/companies/{company_id}/users` → `{"items": [...], "total"}`. UserSummary: `{"id", "email", "first_name", "last_name", "phone", "role", "company_id", "company_name", "created_at"}`.

- [ ] **Step 1: Write the failing tests**

```python
# platform/tests/test_ops_users_api.py
import pytest
from models.staff_user import StaffRole, StaffUser

STAFF_EMAIL = "ops.users.test@3maples.ai"


@pytest.fixture()
def staff_headers(client):
    async def _setup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
        await StaffUser(email=STAFF_EMAIL, first_name="Ops", last_name="U",
                        staff_role=StaffRole.OPS_VIEWER).insert()
    client.portal.call(_setup)
    yield {"X-Test-Email": STAFF_EMAIL}

    async def _cleanup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
    client.portal.call(_cleanup)


def test_list_users_search_finds_default_owner(client, staff_headers, test_company_id):
    resp = client.get("/ops/users", params={"search": "default.owner"},
                      headers=staff_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    row = data["items"][0]
    assert row["company_id"] == test_company_id
    assert row["company_name"] == "Test Company"


def test_list_users_filtered_by_company(client, staff_headers, test_company_id):
    resp = client.get("/ops/users", params={"company_id": test_company_id},
                      headers=staff_headers)
    assert resp.status_code == 200
    assert all(item["company_id"] == test_company_id for item in resp.json()["items"])


def test_company_users_endpoint(client, staff_headers, test_company_id):
    resp = client.get(f"/ops/companies/{test_company_id}/users", headers=staff_headers)
    assert resp.status_code == 200
    emails = [item["email"] for item in resp.json()["items"]]
    assert "default.owner@example.com" in emails


def test_company_users_404(client, staff_headers):
    resp = client.get("/ops/companies/000000000000000000000000/users",
                      headers=staff_headers)
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_ops_users_api.py -v`
Expected: FAIL — 404s

- [ ] **Step 3: Implement** (append to `routers/ops.py`; add `In` to a `beanie.operators` import)

```python
def _serialize_user_summary(user: "User", company_name: Optional[str]) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "role": user.role.value,
        "company_id": str(user.company) if user.company else None,
        "company_name": company_name,
        "created_at": user.created_at.isoformat(),
    }


async def _company_names_for(users: list) -> dict:
    from beanie.operators import In

    company_ids = {u.company for u in users if u.company}
    if not company_ids:
        return {}
    companies = await Company.find(In(Company.id, list(company_ids))).to_list()
    return {c.id: c.name for c in companies}


@router.get("/users")
async def list_users(
    staff: StaffUser = Depends(require_staff_user),
    search: Optional[str] = None,
    company_id: Optional[PydanticObjectId] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    query: dict = {}
    if search and search.strip():
        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [
            {"email": pattern},
            {"first_name": pattern},
            {"last_name": pattern},
        ]
    if company_id:
        query["company"] = company_id

    total = await User.find(query).count()
    users = (
        await User.find(query)
        .sort(-User.created_at)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    names = await _company_names_for(users)
    return {
        "items": [_serialize_user_summary(u, names.get(u.company)) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/companies/{company_id}/users")
async def list_company_users(
    company_id: PydanticObjectId,
    staff: StaffUser = Depends(require_staff_user),
):
    company = await Company.get(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    users = await User.find(User.company == company_id).sort(-User.created_at).to_list()
    return {
        "items": [_serialize_user_summary(u, company.name) for u in users],
        "total": len(users),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_ops_users_api.py -v`
Expected: 4 passed

- [ ] **Step 5: Gates** — `./run_mypy.sh routers/ops.py && ./run_ruff.sh routers/ops.py` → zero errors

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: ops users + company-users endpoints` in `platform/`.

---

### Task 7: `/ops/new-users` + Firebase verification service

**Files:**
- Create: `platform/services/ops_verification.py`
- Modify: `platform/routers/ops.py`
- Test: `platform/tests/test_ops_new_users_api.py`

**Interfaces:**
- Consumes: `User`, `Company`; `firebase_admin.auth.get_users`; `settings.firebase_auth_disabled`.
- Produces: `async def fetch_email_verified_map(emails: list[str]) -> dict[str, bool | None]` (None = unknown/lookup failed/disabled); `GET /ops/new-users` → `{"items": [{"id", "email", "first_name", "last_name", "email_verified", "stage", "company_id", "company_name", "onboarding_step", "created_at"}], "total"}` where `stage ∈ {"unverified", "no_company", "onboarding_incomplete"}`.

- [ ] **Step 1: Write the failing tests**

```python
# platform/tests/test_ops_new_users_api.py
import pytest
from models import Company, User, UserRole
from models.company import OnboardingStep
from models.staff_user import StaffRole, StaffUser

STAFF_EMAIL = "ops.newusers.test@3maples.ai"
NO_COMPANY_EMAIL = "newuser.nocompany.test@example.com"
INCOMPLETE_EMAIL = "newuser.incomplete.test@example.com"


@pytest.fixture()
def seeded(client):
    created: dict = {}

    async def _setup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
        await User.find({"email": {"$in": [NO_COMPANY_EMAIL, INCOMPLETE_EMAIL]}}).delete()
        await StaffUser(email=STAFF_EMAIL, first_name="Ops", last_name="N",
                        staff_role=StaffRole.OPS_VIEWER).insert()

        await User(email=NO_COMPANY_EMAIL, first_name="No", last_name="Company",
                   role=UserRole.MEMBER, company=None).insert()

        company = Company(
            name="Ops Incomplete Test Co", email="opsco@example.com",
            phone="+15550000000", onboarding_completed=False,
            onboarding_step=OnboardingStep.MATERIALS,
        )
        await company.insert()
        created["company_id"] = company.id
        await User(email=INCOMPLETE_EMAIL, first_name="Half", last_name="Way",
                   role=UserRole.OWNER, company=company.id).insert()

    client.portal.call(_setup)
    yield created

    async def _cleanup():
        await StaffUser.find(StaffUser.email == STAFF_EMAIL).delete()
        await User.find({"email": {"$in": [NO_COMPANY_EMAIL, INCOMPLETE_EMAIL]}}).delete()
        await Company.find(Company.name == "Ops Incomplete Test Co").delete()
    client.portal.call(_cleanup)


def test_new_users_lists_both_stages(client, seeded):
    resp = client.get("/ops/new-users", headers={"X-Test-Email": STAFF_EMAIL})
    assert resp.status_code == 200
    by_email = {item["email"]: item for item in resp.json()["items"]}

    assert by_email[NO_COMPANY_EMAIL]["stage"] == "no_company"
    incomplete = by_email[INCOMPLETE_EMAIL]
    assert incomplete["stage"] == "onboarding_incomplete"
    assert incomplete["onboarding_step"] == "materials"
    assert incomplete["company_name"] == "Ops Incomplete Test Co"


def test_new_users_excludes_fully_onboarded(client, seeded, test_company_id):
    resp = client.get("/ops/new-users", headers={"X-Test-Email": STAFF_EMAIL})
    emails = [item["email"] for item in resp.json()["items"]]
    assert "default.owner@example.com" not in emails  # completed company


def test_unverified_stage_takes_precedence(client, seeded, monkeypatch):
    import routers.ops as ops_module

    async def fake_map(emails):
        return {e: (False if e == NO_COMPANY_EMAIL else None) for e in emails}

    monkeypatch.setattr(ops_module, "fetch_email_verified_map", fake_map)
    resp = client.get("/ops/new-users", headers={"X-Test-Email": STAFF_EMAIL})
    by_email = {item["email"]: item for item in resp.json()["items"]}
    assert by_email[NO_COMPANY_EMAIL]["stage"] == "unverified"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_ops_new_users_api.py -v`
Expected: FAIL — 404s

- [ ] **Step 3: Implement the verification service**

```python
# platform/services/ops_verification.py
"""Batch email-verification lookups against Firebase for the ops dashboard.

Values in the returned map: True/False = Firebase's email_verified flag,
None = unknown (Firebase disabled, account missing, or lookup failed). The
new-users endpoint degrades gracefully on None rather than erroring.
"""
import asyncio
import logging

from firebase_admin import auth as firebase_admin_auth

from config import settings

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100  # firebase get_users hard limit


def _lookup_batch(emails: list[str]) -> dict[str, bool]:
    identifiers = [firebase_admin_auth.EmailIdentifier(e) for e in emails]
    result = firebase_admin_auth.get_users(identifiers)
    return {u.email.lower(): bool(u.email_verified) for u in result.users if u.email}


async def fetch_email_verified_map(emails: list[str]) -> dict[str, bool | None]:
    normalized = [e.strip().lower() for e in emails if e and e.strip()]
    verified: dict[str, bool | None] = {e: None for e in normalized}
    if not normalized or settings.firebase_auth_disabled:
        return verified

    for start in range(0, len(normalized), _BATCH_SIZE):
        batch = normalized[start : start + _BATCH_SIZE]
        try:
            verified.update(await asyncio.to_thread(_lookup_batch, batch))
        except Exception:  # noqa: BLE001 — degrade to "unknown", never 500 the page
            logger.warning("Firebase verification lookup failed for %d emails", len(batch))
    return verified
```

- [ ] **Step 4: Implement the endpoint** (append to `routers/ops.py`; import `Eq` from `beanie.operators` and `fetch_email_verified_map` at module level — the test monkeypatches `routers.ops.fetch_email_verified_map`)

```python
@router.get("/new-users")
async def list_new_users(staff: StaffUser = Depends(require_staff_user)):
    from beanie.operators import Eq

    incomplete_companies = await Company.find(
        Eq(Company.onboarding_completed, False)
    ).to_list()
    incomplete_by_id = {c.id: c for c in incomplete_companies}

    users = (
        await User.find(
            {"$or": [
                {"company": None},
                {"company": {"$in": list(incomplete_by_id)}},
            ]}
        )
        .sort(-User.created_at)
        .to_list()
    )
    verified_map = await fetch_email_verified_map([u.email for u in users])

    items = []
    for user in users:
        verified = verified_map.get(user.email.strip().lower())
        company = incomplete_by_id.get(user.company) if user.company else None
        if verified is False:
            stage = "unverified"
        elif user.company is None:
            stage = "no_company"
        else:
            stage = "onboarding_incomplete"
        items.append({
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_verified": verified,
            "stage": stage,
            "company_id": str(user.company) if user.company else None,
            "company_name": company.name if company else None,
            "onboarding_step": company.onboarding_step.value if company else None,
            "created_at": user.created_at.isoformat(),
        })
    return {"items": items, "total": len(items)}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_ops_new_users_api.py -v`
Expected: 3 passed

- [ ] **Step 6: Gates** — `./run_mypy.sh routers/ops.py services/ops_verification.py && ./run_ruff.sh routers/ops.py services/ops_verification.py` → zero errors

- [ ] **Step 7: Commit checkpoint** — request approval for `feat: ops new-users endpoint with Firebase verification enrichment` in `platform/`.

---

## Part 3 — Frontend Tasks

### Task 8: Auth plumbing — `user_type` through login and session

**Files:**
- Modify: `portal/src/types/api.ts` (extend `AuthUser`)
- Create: `portal/src/lib/staffAuth.ts`
- Modify: `portal/src/App.tsx` (staff branch in `onIdTokenChanged` handler, lines ~90-116)
- Modify: `portal/src/pages/auth/LoginPage.tsx` (staff branch before `company_id` check, lines ~167-215)
- Test: `portal/tests/staffAuth.test.ts`

**Interfaces:**
- Produces: `AuthUser` gains `user_type?: "customer" | "staff"` and `staff_role?: string | null`; `resolvePostLoginRoute(authData): "/ops" | "/onboarding" | "/dashboard"`; `isStaffUser(user): boolean`. Tasks 9–13 rely on `isStaffUser(getCurrentUser())`.

- [ ] **Step 1: Write the failing test**

```typescript
// portal/tests/staffAuth.test.ts
import { describe, expect, test } from "vitest";
import { isStaffUser, resolvePostLoginRoute } from "../src/lib/staffAuth";

describe("resolvePostLoginRoute", () => {
  test("staff users route to /ops", () => {
    expect(resolvePostLoginRoute({ user_type: "staff", company_id: null })).toBe("/ops");
  });
  test("customers without a company route to /onboarding", () => {
    expect(resolvePostLoginRoute({ user_type: "customer", company_id: null })).toBe("/onboarding");
    expect(resolvePostLoginRoute({ company_id: "" })).toBe("/onboarding");
  });
  test("customers with a company route to /dashboard", () => {
    expect(resolvePostLoginRoute({ user_type: "customer", company_id: "abc" })).toBe("/dashboard");
    expect(resolvePostLoginRoute({ company_id: "abc" })).toBe("/dashboard");
  });
});

describe("isStaffUser", () => {
  test("true only for user_type staff", () => {
    expect(isStaffUser({ user_type: "staff" })).toBe(true);
    expect(isStaffUser({ user_type: "customer" })).toBe(false);
    expect(isStaffUser(null)).toBe(false);
    expect(isStaffUser(undefined)).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd portal && npm test -- staffAuth`
Expected: FAIL — module not found

- [ ] **Step 3: Implement**

```typescript
// portal/src/lib/staffAuth.ts
interface PostLoginAuthData {
  user_type?: string | null;
  company_id?: string | null;
}

export function isStaffUser(user: PostLoginAuthData | null | undefined): boolean {
  return user?.user_type === "staff";
}

export function resolvePostLoginRoute(
  authData: PostLoginAuthData | null | undefined,
): "/ops" | "/onboarding" | "/dashboard" {
  if (isStaffUser(authData)) return "/ops";
  if (!String(authData?.company_id || "").trim()) return "/onboarding";
  return "/dashboard";
}
```

Extend `AuthUser` in `portal/src/types/api.ts`:

```typescript
  user_type?: "customer" | "staff";
  staff_role?: string | null;
```

In `portal/src/App.tsx` `onIdTokenChanged` handler, insert the staff branch immediately after `const authData = await authenticate(idToken);` (before the `company_id` bail-out):

```typescript
        if ((authData as Record<string, unknown>)?.user_type === "staff") {
          setCurrentUser({
            id: (authData as Record<string, unknown>).user_id as string,
            email: authData?.email,
            first_name: authData?.first_name,
            last_name: authData?.last_name,
            role: (authData as Record<string, unknown>).staff_role as string,
            user_type: "staff",
            staff_role: (authData as Record<string, unknown>).staff_role as string,
            phone: "",
          });
          setAuthenticatedSession();
          setIsAuthenticated(true);
          return; // staff have no company_id; skip customer plumbing
        }
```

In `portal/src/pages/auth/LoginPage.tsx`, insert the same-shaped branch immediately after `const authData = await authenticate(idToken);` (before the `!authData?.company_id → /onboarding` check), ending with `navigate("/ops", { replace: true }); return;`. Add `user_type: "customer"` to the customer `setCurrentUser` call in `persistSessionAndRedirect` so both paths tag the session.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd portal && npm test -- staffAuth && npm test -- authState`
Expected: all pass

- [ ] **Step 5: Typecheck + lint** — `npm run typecheck && npm run lint` → clean (typecheck is mandatory before pushing; the pre-push hook enforces it)

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: user_type-aware login routing for staff accounts` in `portal/`.

---

### Task 9: Ops routes, guards, `OpsLayout`, and API client

**Files:**
- Create: `portal/src/components/Layout/OpsLayout.tsx`
- Create: `portal/src/api/ops.ts`
- Modify: `portal/src/App.tsx` (add `OpsProtectedLayout` guard + `/ops/*` routes; staff redirect in `ProtectedLayout` and `LoginRoute`)
- Test: `portal/tests/OpsLayout.test.tsx`

**Interfaces:**
- Consumes: `isStaffUser`, `getCurrentUser` (Task 8); `apiRequest` from `src/api/client.ts` (mirror the exact call pattern used in `src/api/resources.ts` — same helper the customer APIs use).
- Produces: `opsApi` with `listCompanies(params)`, `getCompany(id)`, `listCompanyUsers(id)`, `listUsers(params)`, `listNewUsers()`, `listStaff()`, `createStaff(body)`, `updateStaff(id, body)`; routes `/ops` (index → `/ops/companies`), `/ops/companies`, `/ops/companies/:id`, `/ops/users`, `/ops/new-users`, `/ops/staff`; `<OpsLayout />` renders sidebar + `<Outlet />`.

- [ ] **Step 1: Write the failing test**

```tsx
// portal/tests/OpsLayout.test.tsx
import { describe, expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import OpsLayout from "../src/components/Layout/OpsLayout";

afterEach(cleanup);

vi.mock("../src/api/auth", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../src/api/auth")>();
  return { ...mod, getCurrentUser: vi.fn(() => currentUser) };
});

let currentUser: Record<string, unknown> = {
  first_name: "Ops", last_name: "Viewer",
  user_type: "staff", staff_role: "ops_viewer",
};

describe("OpsLayout", () => {
  test("renders operations nav for a viewer, without Staff item", () => {
    render(<MemoryRouter initialEntries={["/ops/companies"]}><OpsLayout /></MemoryRouter>);
    expect(screen.getByText("Operations")).toBeTruthy();
    expect(screen.getByText("Companies")).toBeTruthy();
    expect(screen.getByText("Users")).toBeTruthy();
    expect(screen.getByText("New Users")).toBeTruthy();
    expect(screen.queryByText("Staff")).toBeNull();
  });

  test("root sees the Staff nav item", () => {
    currentUser = { ...currentUser, staff_role: "root" };
    render(<MemoryRouter initialEntries={["/ops/companies"]}><OpsLayout /></MemoryRouter>);
    expect(screen.getByText("Staff")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd portal && npm test -- OpsLayout`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `OpsLayout`**

```tsx
// portal/src/components/Layout/OpsLayout.tsx
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Building2, ShieldCheck, UserPlus, Users } from "lucide-react";
import { clearSessionAndCache, getCurrentUser } from "../../api/auth";

const NAV_ITEMS = [
  { path: "/ops/companies", label: "Companies", icon: Building2 },
  { path: "/ops/users", label: "Users", icon: Users },
  { path: "/ops/new-users", label: "New Users", icon: UserPlus },
];

export default function OpsLayout() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const isRoot = currentUser?.staff_role === "root";
  const items = isRoot
    ? [...NAV_ITEMS, { path: "/ops/staff", label: "Staff", icon: ShieldCheck }]
    : NAV_ITEMS;

  const handleLogout = async () => {
    await clearSessionAndCache();
    navigate("/", { replace: true });
  };

  return (
    <div className="flex h-screen bg-[#EEEDF5] overflow-x-hidden">
      <aside className="hidden lg:flex w-52 flex-col bg-slate-900 text-white">
        <div className="px-4 py-5 border-b border-slate-700">
          <div className="text-lg font-semibold">3Maples</div>
          <span className="inline-block mt-1 text-[10px] font-bold tracking-widest uppercase bg-amber-500 text-slate-900 rounded px-1.5 py-0.5">
            Operations
          </span>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1">
          {items.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-800"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-slate-700 text-sm">
          <div className="font-medium truncate">
            {currentUser?.first_name} {currentUser?.last_name}
          </div>
          <div className="text-slate-400 text-xs mb-2">{currentUser?.staff_role}</div>
          <button
            type="button"
            onClick={handleLogout}
            className="text-slate-300 hover:text-white text-sm underline-offset-2 hover:underline"
          >
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 flex flex-col overflow-y-auto min-w-0 p-6">
        <Outlet />
      </main>
    </div>
  );
}
```

*(Verify `clearSessionAndCache` is the logout helper `PortalLayout.tsx` uses at lines ~274-282 and import it from the same module.)*

- [ ] **Step 4: Implement the API client**

```typescript
// portal/src/api/ops.ts
import { apiRequest } from "./client"; // mirror the exact import/signature used by src/api/resources.ts

function toQuery(params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") qs.set(key, String(value));
  });
  const s = qs.toString();
  return s ? `?${s}` : "";
}

export interface OpsListParams {
  search?: string;
  status?: string;
  company_id?: string;
  page?: number;
  page_size?: number;
}

export const opsApi = {
  listCompanies: (params: OpsListParams = {}) =>
    apiRequest(`/ops/companies${toQuery(params)}`),
  getCompany: (id: string) => apiRequest(`/ops/companies/${id}`),
  listCompanyUsers: (id: string) => apiRequest(`/ops/companies/${id}/users`),
  listUsers: (params: OpsListParams = {}) =>
    apiRequest(`/ops/users${toQuery(params)}`),
  listNewUsers: () => apiRequest(`/ops/new-users`),
  listStaff: () => apiRequest(`/ops/staff`),
  createStaff: (body: {
    email: string; first_name: string; last_name: string; staff_role: string;
  }) => apiRequest(`/ops/staff`, { method: "POST", body: JSON.stringify(body) }),
  updateStaff: (id: string, body: { staff_role?: string; status?: string }) =>
    apiRequest(`/ops/staff/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
};
```

- [ ] **Step 5: Wire routes and guards in `App.tsx`**

```tsx
function OpsProtectedLayout({ authReady, isAuthenticated }: AuthGateProps) {
  if (!authReady) return <AuthLoading />;
  if (!isAuthenticated) return <Navigate to="/" replace />;
  return isStaffUser(getCurrentUser()) ? <OpsLayout /> : <Navigate to="/dashboard" replace />;
}
```

- In `ProtectedLayout`, before the onboarding redirect: `if (isAuthenticated && isStaffUser(getCurrentUser())) return <Navigate to="/ops" replace />;`
- In `LoginRoute`: redirect authenticated users to `isStaffUser(getCurrentUser()) ? "/ops" : "/dashboard"`.
- Route registration (lazy pages arrive in Tasks 10-13; register each route in the task that creates its page, or create all four page files as minimal stubs here and fill them in per task — prefer the former to keep tasks independent):

```tsx
<Route path="/ops" element={<OpsProtectedLayout authReady={authReady} isAuthenticated={isAuthenticated} />}>
  <Route index element={<Navigate to="/ops/companies" replace />} />
  {/* child routes added by Tasks 10–13 */}
</Route>
```

- [ ] **Step 6: Run tests** — `npm test -- OpsLayout` → 2 passed; `npm run typecheck && npm run lint` → clean

- [ ] **Step 7: Commit checkpoint** — request approval for `feat: ops route guards, OpsLayout shell, and ops API client` in `portal/`.

---

### Task 10: Companies pages

**Files:**
- Create: `portal/src/pages/ops/OpsCompaniesPage.tsx`, `portal/src/pages/ops/OpsCompanyDetailPage.tsx`
- Modify: `portal/src/App.tsx` (register `companies` + `companies/:id` child routes)
- Test: `portal/tests/OpsCompaniesPage.test.tsx`

**Interfaces:**
- Consumes: `opsApi.listCompanies`, `opsApi.getCompany`, `opsApi.listCompanyUsers` (Task 9); `Table/Badge/Card/Input/Select` from `src/components/ui/*`; `LoadingState`/`ErrorState` from `src/components/common/PageState.tsx`.

- [ ] **Step 1: Write the failing test**

```tsx
// portal/tests/OpsCompaniesPage.test.tsx
import { describe, expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../src/api/ops", () => ({
  opsApi: {
    listCompanies: vi.fn().mockResolvedValue({
      items: [{
        id: "c1", name: "Acme Landscaping", industry: "Landscaping & Hardscape",
        status: "active", plan_lookup_key: "pro", user_count: 4,
        estimates_created: 12, estimates_allowed: 25,
        created_at: "2026-03-14T00:00:00+00:00",
      }],
      total: 1, page: 1, page_size: 25,
    }),
  },
}));

import OpsCompaniesPage from "../src/pages/ops/OpsCompaniesPage";

afterEach(cleanup);

describe("OpsCompaniesPage", () => {
  test("renders company rows from the API", async () => {
    render(<MemoryRouter><OpsCompaniesPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText("Acme Landscaping")).toBeTruthy();
    });
    expect(screen.getByText("active")).toBeTruthy();
    expect(screen.getByText("12 / 25")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd portal && npm test -- OpsCompaniesPage`
Expected: FAIL — module not found

- [ ] **Step 3: Implement the list page**

```tsx
// portal/src/pages/ops/OpsCompaniesPage.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { opsApi } from "../../api/ops";
import { LoadingState, ErrorState } from "../../components/common/PageState";
import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";

interface CompanyRow {
  id: string; name: string; industry: string | null; status: string;
  plan_lookup_key: string | null; user_count: number;
  estimates_created: number; estimates_allowed: number; created_at: string;
}

export default function OpsCompaniesPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{ items: CompanyRow[]; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    opsApi
      .listCompanies({ search, status: statusFilter, page, page_size: 25 })
      .then((res) => { if (!cancelled) setData(res as { items: CompanyRow[]; total: number }); })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load companies"); });
    return () => { cancelled = true; };
  }, [search, statusFilter, page]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Companies</h1>
      <div className="flex gap-2 mb-4">
        <Input
          placeholder="Search by name…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="max-w-xs bg-white"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="rounded-md border border-gray-200 bg-white px-3 text-sm"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </select>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Industry</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Plan</TableHead>
              <TableHead>Users</TableHead>
              <TableHead>Estimates</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((row) => (
              <TableRow
                key={row.id}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => navigate(`/ops/companies/${row.id}`)}
              >
                <TableCell className="font-medium">{row.name}</TableCell>
                <TableCell>{row.industry || "—"}</TableCell>
                <TableCell>
                  <Badge variant={row.status === "active" ? "default" : "secondary"}>
                    {row.status}
                  </Badge>
                </TableCell>
                <TableCell>{row.plan_lookup_key || "—"}</TableCell>
                <TableCell>{row.user_count}</TableCell>
                <TableCell>{`${row.estimates_created} / ${row.estimates_allowed}`}</TableCell>
                <TableCell>{new Date(row.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
        <span>{data.total} companies</span>
        <div className="flex gap-2">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}
                  className="px-2 py-1 rounded border border-gray-200 bg-white disabled:opacity-40">‹</button>
          <button type="button" disabled={page * 25 >= data.total} onClick={() => setPage(page + 1)}
                  className="px-2 py-1 rounded border border-gray-200 bg-white disabled:opacity-40">›</button>
        </div>
      </div>
    </div>
  );
}
```

*(Check `<Badge>`'s actual variant names in `src/components/ui/badge.tsx` and `LoadingState`/`ErrorState` props in `PageState.tsx`; adjust to the real signatures. Debounce the search input with the codebase's existing debounce idiom if one exists — otherwise a 300 ms `setTimeout` in the effect.)*

- [ ] **Step 4: Implement the detail page** — same fetch/state pattern with `opsApi.getCompany(id)` + `opsApi.listCompanyUsers(id)` via `Promise.all`, `useParams()` for the id; render the two stacked cards from the Part 1 wireframe (`Card`/`CardHeader`/`CardTitle`/`CardContent` + a users `Table` with Name/Email/Role/Joined columns; onboarding line shows `onboarding_completed ? "completed" : \`in progress — ${onboarding_step}\``). Back link to `/ops/companies`.

- [ ] **Step 5: Register routes** in `App.tsx` under the `/ops` parent:

```tsx
  <Route path="companies" element={<OpsCompaniesPage />} />
  <Route path="companies/:id" element={<OpsCompanyDetailPage />} />
```

- [ ] **Step 6: Run tests** — `npm test -- OpsCompaniesPage` → passed; `npm run typecheck && npm run lint` → clean

- [ ] **Step 7: Commit checkpoint** — request approval for `feat: ops companies list and detail pages` in `portal/`.

---

### Task 11: Users page

**Files:**
- Create: `portal/src/pages/ops/OpsUsersPage.tsx`
- Modify: `portal/src/App.tsx` (register `users` child route)
- Test: `portal/tests/OpsUsersPage.test.tsx`

**Interfaces:**
- Consumes: `opsApi.listUsers` (Task 9).

- [ ] **Step 1: Write the failing test** — mirror `OpsCompaniesPage.test.tsx` exactly: mock `opsApi.listUsers` to resolve `{ items: [{ id: "u1", email: "jane@acme.com", first_name: "Jane", last_name: "Doe", phone: null, role: "Owner", company_id: "c1", company_name: "Acme Landscaping", created_at: "2026-04-01T00:00:00+00:00" }], total: 1, page: 1, page_size: 25 }`, render `<OpsUsersPage />` in a `MemoryRouter`, and assert `jane@acme.com`, `Owner`, and `Acme Landscaping` appear.

- [ ] **Step 2: Run test to verify it fails** — `npm test -- OpsUsersPage` → module not found

- [ ] **Step 3: Implement** — same structure as `OpsCompaniesPage` (search input + paginated table). Columns: Name (`first_name last_name`), Email, Role (`<Badge>`), Company (a `<Link to={`/ops/companies/${row.company_id}`}>` when `company_id` is set, otherwise "—"), Phone, Created. The `search` param feeds `opsApi.listUsers({ search, page, page_size: 25 })`.

- [ ] **Step 4: Register route** — `<Route path="users" element={<OpsUsersPage />} />`

- [ ] **Step 5: Run tests** — `npm test -- OpsUsersPage` → passed; `npm run typecheck && npm run lint` → clean

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: ops users page` in `portal/`.

---

### Task 12: New Users page

**Files:**
- Create: `portal/src/pages/ops/OpsNewUsersPage.tsx`
- Modify: `portal/src/App.tsx` (register `new-users` child route)
- Test: `portal/tests/OpsNewUsersPage.test.tsx`

**Interfaces:**
- Consumes: `opsApi.listNewUsers` (Task 9). Row shape from Task 7 (`stage`, `email_verified`, `onboarding_step`, `company_name`).

- [ ] **Step 1: Write the failing test**

```tsx
// portal/tests/OpsNewUsersPage.test.tsx
import { describe, expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../src/api/ops", () => ({
  opsApi: {
    listNewUsers: vi.fn().mockResolvedValue({
      items: [
        { id: "u1", email: "unv@x.com", first_name: "Un", last_name: "Verified",
          email_verified: false, stage: "unverified", company_id: null,
          company_name: null, onboarding_step: null,
          created_at: "2026-06-30T00:00:00+00:00" },
        { id: "u2", email: "half@x.com", first_name: "Half", last_name: "Way",
          email_verified: true, stage: "onboarding_incomplete", company_id: "c9",
          company_name: "Halfway Co", onboarding_step: "materials",
          created_at: "2026-06-29T00:00:00+00:00" },
      ],
      total: 2,
    }),
  },
}));

import OpsNewUsersPage from "../src/pages/ops/OpsNewUsersPage";

afterEach(cleanup);

describe("OpsNewUsersPage", () => {
  test("renders stage badges and onboarding step", async () => {
    render(<MemoryRouter><OpsNewUsersPage /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText("unv@x.com")).toBeTruthy());
    expect(screen.getByText("Unverified")).toBeTruthy();
    expect(screen.getByText("Onboarding incomplete")).toBeTruthy();
    expect(screen.getByText("materials")).toBeTruthy();
  });

  test("stage filter chips narrow the list", async () => {
    render(<MemoryRouter><OpsNewUsersPage /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText("unv@x.com")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /^Unverified/ }));
    expect(screen.queryByText("half@x.com")).toBeNull();
    expect(screen.getByText("unv@x.com")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails** — `npm test -- OpsNewUsersPage` → module not found

- [ ] **Step 3: Implement** — fetch once with `opsApi.listNewUsers()`; client-side stage filtering via chip buttons `[All] [Unverified] [No company] [Onboarding incomplete]` (each a `<button>` styled as a pill, active chip in `bg-slate-900 text-white`). Table columns: Name, Email, Stage (badge — amber `unverified`, blue `no_company` → label "No company", violet `onboarding_incomplete` → label "Onboarding incomplete"), Step (`onboarding_step` or "—"), Company (`company_name` or "—"), Signed up (`created_at` date). Stage label mapping lives in a `const STAGE_LABELS: Record<string, string>` so tests and UI can't drift.

- [ ] **Step 4: Register route** — `<Route path="new-users" element={<OpsNewUsersPage />} />`

- [ ] **Step 5: Run tests** — `npm test -- OpsNewUsersPage` → 2 passed; `npm run typecheck && npm run lint` → clean

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: ops new-users page` in `portal/`.

---

### Task 13: Staff page (root only)

**Files:**
- Create: `portal/src/pages/ops/OpsStaffPage.tsx`
- Modify: `portal/src/App.tsx` (register `staff` child route)
- Test: `portal/tests/OpsStaffPage.test.tsx`

**Interfaces:**
- Consumes: `opsApi.listStaff/createStaff/updateStaff` (Task 9); `Dialog` primitives from `src/components/ui/dialog.tsx`.

- [ ] **Step 1: Write the failing test** — mock `opsApi.listStaff` to resolve two staff rows (one `root`, one `ops_viewer` with `status: "active"`); assert both emails render with role badges and that an "Add staff user" button is present. Second test: mock `opsApi.createStaff` to resolve a new row, open the dialog, fill email/first/last/role via `fireEvent.change`, submit, and assert `opsApi.createStaff` was called with `{ email, first_name, last_name, staff_role }`.

- [ ] **Step 2: Run test to verify it fails** — `npm test -- OpsStaffPage` → module not found

- [ ] **Step 3: Implement** — table (Name, Email, Role badge, Status badge, Created) with a per-row actions: "Disable"/"Enable" (`updateStaff(id, { status })`) and a role `<select>` (`updateStaff(id, { staff_role })`), both disabled for the current user's own row (compare email with `getCurrentUser()?.email`). "Add staff user" opens a `<Dialog>` with Email, First name, Last name, Role select (`ops_viewer`/`ops_admin`/`root`); on submit call `opsApi.createStaff`, append the returned row, close the dialog, and show the returned email in the table. Surface API errors (409 duplicate etc.) in an inline `<Alert>` inside the dialog. This page is already root-gated by nav visibility + the server; no extra client gate needed beyond hiding the nav item (Task 9).

- [ ] **Step 4: Register route** — `<Route path="staff" element={<OpsStaffPage />} />`

- [ ] **Step 5: Run tests** — `npm test -- OpsStaffPage` → passed; `npm run typecheck && npm run lint` → clean

- [ ] **Step 6: Commit checkpoint** — request approval for `feat: ops staff management page (root only)` in `portal/`.

---

### Task 14: Documentation sync

**Files:**
- Modify: `CLAUDE.md` (root repo — add StaffUser/ops router to the Architecture section, one short paragraph)
- Modify: `documentation/development/notes.md` (decision record: separate StaffUser collection, staff role names, root bootstrap procedure)

No TDD (docs-only). Content: a "Staff / Operations users" subsection under Backend Architecture stating: staff live in `staff_users` (never company-scoped), roles `root/ops_admin/ops_viewer`, provisioning root-only via `/ops/staff` + `scripts/create_root_user.py`, `/ops/*` endpoints guarded by `require_staff_user`, portal routes staff to `/ops` on `user_type: "staff"`.

- [ ] **Step 1: Write both doc updates**
- [ ] **Step 2: Commit checkpoint** — request approval for `docs: document staff users + operations dashboard` in the root repo and `documentation/` repo respectively.

---

## Rollout / Verification

1. After all tasks land: Simon runs `python scripts/create_root_user.py simon@tangz.com Simon <LastName>` against the Dev cluster (venv active, `.env.local` in place), sets the password via the reset email.
2. Manual smoke: log in as root → land on `/ops/companies`; verify the four features; create an `ops_viewer` staff user; log in as viewer → no Staff nav; log in as a customer → normal `/dashboard`, `/ops/*` URLs bounce to `/dashboard` and `/ops` API calls return 403.
3. Full gates run at push via the pre-push hooks (platform: ruff + mypy; portal: typecheck). Full pytest/vitest suites: Simon triggers manually.
4. Production promotion only via `/release` on Simon's explicit request — never chained.

## Out of Scope (deliberate)

- Write operations on companies/users from the ops dashboard (archive company, resend verification, impersonation) — natural v2 once `ops_admin` earns real permissions.
- Ops overview/analytics cards, CSV export, audit-logging of staff reads.
- Final staff role naming — enum values are cheap to rename before any second staff user exists.
