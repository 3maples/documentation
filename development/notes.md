# Engineering Notes

Running log of non-obvious decisions and behaviors worth remembering — the kind
of context that isn't self-evident from the code. Append a dated entry per note.

---

## 2026-06-21 — Default template seeding is gated on both standard catalogs

Default estimate templates (`platform/data/default_templates.json`, seeded via
`platform/services/template_bootstrap.py::bootstrap_company_templates`) are wired
into new-company creation through
`platform/services/company_service.py::create_company_with_bootstrap`, which the
live signup endpoint `POST /auth/company-onboarding`
(`platform/routers/auth.py`) calls.

The template step runs **last** and only when **both**
`include_standard_materials` **and** `include_standard_labour_roles` are True.
Both flags default to **False** on `CompanyOnboardingRequest` (auth.py ~271-272),
so a company gets default templates only if onboarding opts into both standard
catalogs. Skip either → no templates seeded (this is intended, not a bug).

**Why:** templates resolve their material/role line items by *name* against the
company's own freshly-seeded catalog; without both catalogs present every item
would fall into `unmatched_*`, so seeding them would just create noise.

**Decision:** keep it gated on both flags — confirmed intentional. If product
later wants every company to get templates regardless, the alternatives are:
always seed (accept `unmatched_*`), or gate on a partial catalog.

---

## 2026-07-03 — Operations UI: StaffUser as a separate collection, not a role extension

Shipped the internal Operations dashboard (staff-only back office: company list,
user list, "new users" funnel, staff management). The core design decision was
**where staff accounts live**, and the answer is a dedicated `staff_users`
Beanie collection (`platform/models/staff_user.py`), deliberately isolated from
the customer `users` collection.

**Alternatives considered:**
- **Extend `UserRole` on the existing `User` model** (add `staff`/`ops_admin`
  style values alongside the current tenant roles). Rejected — `User` is
  structurally company-scoped (every document carries a `company` reference,
  and most CRUD queries filter or assert on it). Roughly **9 routers**
  (`contacts.py`, `billing.py`, `equipments.py`, `material_categories.py`,
  `materials.py`, `estimates.py`, `properties.py`, `labours.py`,
  `divisions.py`, `templates.py`, `rate_cards.py`, `audit_logs.py`,
  `material_units.py`, `companies.py` — company-scoping shows up across more
  than 9 call sites) do explicit `company_id ==` / `assert_company_access`
  checks. Adding a company-less user variant into that model would have meant
  auditing and special-casing every one of those sites to handle a `User` with
  no `company`, for a real regression risk on tenant isolation — the exact
  thing those checks exist to guarantee.
- **`user_type` discriminator field on `User`** (customer vs. staff, single
  collection). Rejected for the same reason as above, plus it blurs a
  collection whose entire purpose is "belongs to a company" with accounts that
  by definition don't.
- **Separate `StaffUser` collection (chosen).** Zero regression surface on the
  company-scoped call sites above — staff accounts simply never appear in any
  `User` query. Trade-off: a few things are duplicated (a second auth check in
  `POST /auth` via `resolve_active_staff`, a second Firebase-backed
  provisioning path), but that duplication is small, explicit, and isolated to
  `dependencies.py` / `services/staff_service.py` / `routers/ops.py`.

**Role names** (`StaffRole` enum in `models/staff_user.py`): `root`,
`ops_admin`, `ops_viewer`. **Naming is provisional** — cheap to rename while
only one staff user (root) exists; the enum values, not just labels, would
need a migration once a second staff user is provisioned, so any rename should
happen soon if at all.

**Root bootstrap procedure** — there is no UI path to create the first root
(by design: `POST /ops/staff` is root-only, so someone has to exist first).
Run once, from `platform/`, venv active, `.env.local` pointed at the target
cluster:

```bash
python scripts/create_root_user.py simon@tangz.com Simon <LastName>
```

`scripts/create_root_user.py` refuses to run if a `root` `StaffUser` already
exists (`StaffUser.find_one(StaffUser.staff_role == StaffRole.ROOT)`), creates
the Firebase account pre-verified, and sends a password-reset email to set the
password — same provisioning path (`services/staff_service.py::provision_staff_user`)
as `POST /ops/staff` uses for subsequent staff.

**New Users stage definitions** (`GET /ops/new-users`, `routers/ops.py`) —
staff-visible funnel over customers who haven't finished onboarding.
Candidates are users with no company or whose company has
`onboarding_completed == False`; email-verification status comes from Firebase
via `services/ops_verification.py` (fails open to `"unknown"` on lookup
failure — an ops dashboard on a Firebase hiccup should degrade to
"can't tell," not crash). Each candidate is bucketed into exactly one stage:

- `unverified` — Firebase reports `email_verified == False`.
- `no_company` — verified (or unknown), but `user.company is None`.
- `onboarding_incomplete` — has a company, but that company's
  `onboarding_completed` is still `False`.
