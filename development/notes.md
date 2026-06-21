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
