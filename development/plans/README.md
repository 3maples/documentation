# Plans

This folder contains implementation plans for the 3maples project. Each file is a markdown document describing the context, approach, status, and follow-ups for a discrete piece of work.

Plans are versioned alongside the code so they stay discoverable, shareable, and editable as the work evolves. New plans should be saved here directly (not to the global `~/.claude/plans/` folder).

## Index

| File | Topic |
|---|---|
| [create-a-plan-to-velvet-eclipse.md](create-a-plan-to-velvet-eclipse.md) | Maple CRUD coverage test suite + gap report |
| [create-a-plan-to-lexical-wand.md](create-a-plan-to-lexical-wand.md) | Auth screens overhaul |
| [reflective-wiggling-charm.md](reflective-wiggling-charm.md) | Portal UI v2 facelift |
| [cheerful-cuddling-bengio.md](cheerful-cuddling-bengio.md) | Maple AI estimate creation with activities |
| [cryptic-chasing-gizmo.md](cryptic-chasing-gizmo.md) | Work item template feature |
| [recursive-questing-abelson.md](recursive-questing-abelson.md) | Change log feature |
| [golden-sprouting-adleman.md](golden-sprouting-adleman.md) | Customer feedback & support |
| [ticklish-herding-orbit.md](ticklish-herding-orbit.md) | Featurebase feedback widget integration |
| [binary-pondering-seal.md](binary-pondering-seal.md) | Sentry integration (frontend & backend) |
| [snuggly-sauteeing-rossum.md](snuggly-sauteeing-rossum.md) | Multi-step onboarding flow |
| [harmonic-strolling-anchor.md](harmonic-strolling-anchor.md) | Monthly estimate quota per company |
| [snappy-riding-pie.md](snappy-riding-pie.md) | Field extraction fixes (Contact, Property, Material agents) |
| [2026-06-24-in-app-customer-support.md](2026-06-24-in-app-customer-support.md) | In-app customer support (async + live chat via Slack/Firestore) |

## Naming convention

New plans **must** use `YYYY-MM-DD-short-topic.md` (e.g.
`2026-06-13-auth-screens-overhaul.md`). The date prefix keeps the folder
chronologically sortable and the topic slug keeps it scannable.

Do **not** use the random-word slugs that plan-mode generates
(`binary-pondering-seal.md`); rename them to the dated form on save. The legacy
random-word files above are grandfathered in — leave them as-is and let them age
out; only the index table needs to stay accurate.

## When adding a new plan

1. Save the file directly to this folder, named `YYYY-MM-DD-short-topic.md`.
2. Add a new row to the index table above.
