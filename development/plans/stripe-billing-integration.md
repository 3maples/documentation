# Stripe Subscription + Usage-Based Billing Integration

**Status:** ✅ FINAL — all decisions locked, ready to start Phase 0/1 implementation
**Last updated:** 2026-05-08
**Owners:** Backend (FastAPI/Beanie), Frontend (React/Vite portal)

**Locked decisions (see §9):**
- D1 ✅ Install Stripe docs Claude Skill
- D2 ✅ No card capture up-front — prompt only when user exceeds the included cap with no card on file
- D3 ✅ Seat aggregation = `last` with backend high-water-mark gating (Stripe doesn't expose `max` natively — see §2.3); estimate aggregation = `count`
- D4 ✅ Migrate every existing Company to Free plan (20 estimates)
- D5 ✅ Base / Pro shown as "Coming Soon" only — disabled / not selectable at launch
- D6 ✅ Embedded Checkout (when paid plans launch)
- D7 ✅ Billing cycle anchor = **anniversary** (user signing up on the 17th bills on the 17th of every month)
- D8 ✅ Free plan: $0 Subscription created in Stripe at end of onboarding
- D9 ✅ No free trial for paid plans (Phase 5 — Base/Pro charge from day one)
- D10 ✅ Default currency = **USD** (single currency at launch)
- D11 ✅ Lookup key naming: `plan_free` / `plan_base` / `plan_pro` for plans; `est_overage_<plan>` and `seat_overage_<plan>` for metered prices

**Onboarding → Stripe (confirmed, see §2.4 / §2.4.1):** at the end of onboarding, the BE creates **both** a Stripe `Customer` and a `Subscription` for every new Company — including Free. The Free subscription is $0 with no payment method attached, but the records exist in Stripe from day one so metering, webhooks, and future plan upgrades all work uniformly.

**$0 invoice webhooks (confirmed, see §4.3.1):** Stripe **does** fire webhooks for $0 invoices. Free-plan cycles end with `invoice.created` → `invoice.finalized` → `invoice.paid` (auto-paid since amount = 0), plus `customer.subscription.updated` for the new period. **`invoice.payment_failed` does NOT fire** for $0 invoices. The BE relies on the `invoice.paid` event to reset `Company.number_of_estimates_created` and refresh period dates — including for Free users — making cycle rollover work uniformly across all plans.

**Seat reporting cadence (confirmed, see §4.4 "Seat snapshot"):** Three paths feed the `seat_count_snapshot` meter — (1) inline roster-change hooks on every invitation-accept / user-reactivate / user-deactivate, (2) a daily defensive cron that re-posts current active-user count for every company, and (3) a cycle-start backstop that re-posts the count immediately when the `customer.subscription.updated` webhook advances the period. Each path goes through `meter_events.report_seat_count`, which gates posts on a per-period high-water mark on the Company doc so the `last` aggregation behaves like `max`. Idempotent under replays.

---

## Pre-flight checklist (Phase 0 status)

| Item | Status | Notes |
|---|---|---|
| Stripe account exists, test-mode keys generated | ✅ Confirmed | User pasted into `.env.local` files |
| `STRIPE_SK` in `platform/.env.local` | ✅ Done | BE config will read this |
| Publishable key in `portal/.env.local` | ⚠️ Needs rename | Currently `STRIPE_PK`; must be renamed to `VITE_STRIPE_PUBLISHABLE_KEY` for Vite to expose it (see §4.6). I'll do this in Phase 1 step 1. |
| `npx skills add -y https://docs.stripe.com` | ⏳ User action | Run before Phase 1 starts. Optional but recommended (D1). |
| Stripe webhook secret | ⏳ Deferred | Local dev uses `stripe listen` CLI which prints a `whsec_…`; deployed environments get one from the Dashboard endpoint config. Not blocking Phase 1. |
| Default currency: USD | ✅ Locked (D10) | Every Stripe Price created uses `currency: "usd"` |
| Billing cycle anchor: anniversary | ✅ Locked (D7) | Subscription created with default `billing_cycle_anchor` (= now) |
| No trial for paid plans | ✅ Locked (D9) | `trial_period_days` not set |
| Lookup-key naming convention | ✅ Locked (D11) | `plan_<tier>` / `est_overage_<tier>` / `seat_overage_<tier>` |
| Stripe business profile (legal name, address, statement descriptor, support email) | ⏳ Pre-launch | Not blocking test-mode work. Required before flipping live mode in Phase 5. |
| Bank account, tax ID, beneficial-owner verification | ⏳ Pre-launch | Same as above — Phase 5 only. Start the activation process early since it can take days. |

**Bottom line:** I'm unblocked to begin Phase 1 work. Action items left for the user are (a) optionally run the `npx skills add` command, and (b) start filling in Stripe business-profile / bank info on the side so it's ready for Phase 5 — neither blocks me today.

---

## 0. TL;DR

Yes, Stripe handles the requested model out of the box. The shape is:

- **One Subscription per Company** containing **two prices**:
  1. A flat recurring price ($0 for Free, $99 Base, $199 Pro).
  2. A **metered price** wired to a **Billing Meter** (`estimates_created`), with **graduated tiers** so the first N units / period are $0 and units N+1 onward cost the per-overage rate.
- Backend reports **every** estimate-create event to Stripe's Meter Events API. Stripe applies the tier math at invoice time. The end-of-cycle invoice is automatically `flat fee + (overage units × per-unit price)`.
- A separate metered price for **additional users** (Free: $10/user/mo, Base/Pro: $5/user/mo) is gated by user-seat count, reported the same way.
- Webhook listener on the FastAPI side links Stripe customer/subscription IDs back to the `Company` document and tracks subscription status.

This document covers: pre-flight question on `npx skills add`, Stripe object model, data-model changes, BE flows (checkout, webhooks, metering), FE flows (plan picker, payment widget, Settings → Billing tab), test plan, env/config, and a phased rollout.

---

## 1. Pre-flight: `npx skills add -y https://docs.stripe.com`

### What it does

This command is part of Anthropic's emerging **Claude Skills** ecosystem (the same surface as the local `Skill` tool — see `~/.claude/skills/`). `npx skills add <url>` fetches a `skill.md` (or skill bundle) hosted at that URL and installs it into the local Claude config so the assistant can load it on demand.

In Stripe's case it installs the `stripe-docs` / `stripe-api` skill, which gives Claude:
- Up-to-date Stripe API docs in a structured, retrievable form
- Code-generation helpers tuned to the current Stripe Node/Python SDKs
- Built-in awareness of recent API changes (e.g., the move from `usage_records` → Meter Events)

### Do we need it?

**Decision (D1): Install it before Phase 1.**

Benefits:

- ✅ Reduces drift — Stripe's API surface changes often (especially around metering), and a skill keeps the LLM grounded in the *current* docs rather than training data.
- ✅ Faster code generation for Stripe-specific patterns we'll be writing repeatedly (Checkout Sessions, webhook handlers, meter events).

Costs (accepted):
- ⚠️ It installs into the local Claude config, so it affects the assistant's behavior across all projects on this machine.
- ⚠️ One more dependency to keep updated.

**Action item:** Run `npx skills add -y https://docs.stripe.com` as the first step of Phase 1.

---

## 2. The Stripe Object Model

### 2.1 Products & Prices (Stripe-side, configured in dashboard or via script)

We'll create **one Product per plan** plus **one shared "Add-on" Product** for metered overages and seat overages. Each Product gets a `lookup_key` so backend code references stable strings, not Stripe IDs.

**All prices in USD (D10).** Subscription `billing_cycle_anchor` defaults to creation time (D7 — anniversary billing). No `trial_period_days` set on any plan (D9).

| Plan | Product `lookup_key` | Flat price (USD) | Estimate overage price | Seat overage price |
|---|---|---|---|---|
| Free | `plan_free` | $0/mo (Subscription still created — see §2.4) | `est_overage_free` @ $5 / unit, free up to 20 | `seat_overage_free` @ $10 / unit, free up to 3 |
| Base (coming soon) | `plan_base` | $99/mo | `est_overage_base` @ $2 / unit, free up to 100 | `seat_overage_base` @ $5 / unit, free up to 20 |
| Pro (coming soon) | `plan_pro` | $199/mo | `est_overage_pro` @ $1 / unit, free up to 200 | `seat_overage_pro` @ $5 / unit, free up to 50 |
| Enterprise | n/a — contact sales | — | — | — |

Each overage price is `recurring + usage_type=metered`, `tiers_mode=graduated`, with two tiers:
- Tier 1: `up_to: <included_count>`, `unit_amount: 0`
- Tier 2: `up_to: inf`, `unit_amount: <overage_cents>`

Both overage prices reference the **same meter** scoped to event names `estimates_created` / `seat_count_snapshot` respectively (see §2.3).

**Why graduated tiers and not "report only the overage"?** Letting Stripe own the tier math means:
- Single source of truth for what's billed.
- Plan changes (Free → Base mid-cycle) automatically re-tier without backend bookkeeping.
- Audit trail: every estimate-create is recorded, so disputes are traceable.

### 2.2 Subscriptions

One Subscription per Company. Items array contains:
1. The flat recurring price for the plan
2. The metered estimate-overage price
3. The metered seat-overage price

Free plan: still create a $0 subscription — gives us a single uniform code path, plus a webhook trail and a place to attach metered prices for any future "Free + paid add-ons" cases.

### 2.3 Billing Meters

Two meters, created once per environment:

```
estimates_created    aggregation: count   customer_mapping: stripe_customer_id
seat_count_snapshot  aggregation: last    customer_mapping: stripe_customer_id
```

**`estimates_created` (aggregation = `count`)** — counts the number of meter events per period. Each estimate creation = one event. We don't need to send `value: 1`; `count` aggregation makes the value irrelevant. Cleaner than `sum` and self-documenting.

**`seat_count_snapshot` (aggregation = `last`)** — Stripe Billing meters expose `count`, `sum`, and `last` only; **`max` is not a supported aggregation**. We get the same effect by combining `last` with backend gating: `meter_events.report_seat_count` only posts an event when the new seat count is HIGHER than the running per-period max we track on the Company doc. Concretely:

- Local field on `Company`: `seat_count_period_high_water` (int, resets at cycle start).
- On every roster-change hook / daily cron / cycle-start backstop: compute current active-user count `n`. If `n > seat_count_period_high_water`, post a meter event with `value=n` AND update the local high-water mark. If `n <= high_water`, do nothing.
- Result: the meter's `last` value within the period is monotonically non-decreasing, so at invoice time it equals the period's max — same revenue-protection guarantee as native `max` would have given. Replays are still idempotent.
- At cycle rollover (`customer.subscription.updated` with new `current_period_start`), reset `seat_count_period_high_water = 0` and immediately re-post the current count as the seed for the new period.

**Cycle reset confirmation (D3):** Stripe meter aggregations are **scoped to the subscription's billing period**. At the start of each new billing cycle, the aggregated value resets to zero. So a company that peaks at 25 users in May and drops to 3 in June starts June with `max = 0`, and June's invoice reflects only June's peak. This is Stripe's documented behavior and applies to both `count` and `max` aggregations — confirmed in the Stripe Billing meters docs. **No backend reset logic required for the Stripe-side counters.**

(Our local mirror in `Company.number_of_estimates_created` still needs the existing month-based lazy-reset logic in `services/estimate_quota.py`, since that's used for fast UI gating without a Stripe round-trip. The two counters can drift slightly during a cycle but converge at cycle start.)

**Reporting cadence:**
- `estimates_created`: one event per estimate, sent inline with `try_claim_estimate_slot`.
- `seat_count_snapshot`: report on every change to the company's user roster (user invited and accepted, user deactivated/removed). Plus a defensive once-daily cron that re-reports the current count, in case any roster-change hooks were missed. Since aggregation is `max`, replays are safe — they only matter if they raise the running max.

### 2.4 Customer

One Stripe `Customer` per `Company`. **Created at the end of onboarding, regardless of which plan is selected — Free included.** This is the design's first principle: Stripe is the system of record for billing identity from day one, even for $0 customers.

Stored as `Company.stripe_customer_id`. The `Customer` object on Stripe's side is populated with:
- `name` ← `Company.name`
- `email` ← Company billing email (a non-null `email` is mandatory for Stripe Customer creation; backfill must guarantee this)
- `phone` ← `Company.phone` (if present)
- `address` ← Company street/city/state/postal/country (if present)
- `metadata.company_id` ← Mongo `Company._id` as a string (so we can reverse-lookup from a Stripe webhook without a join)

Why even for Free:
- The end-of-onboarding flow is the **only** moment we're guaranteed to have valid company data and the user's attention. If a user later goes over the included cap, we don't want to be missing fields like `email` when we try to create the Customer on the fly.
- Webhook handlers are simpler when every Company has a `stripe_customer_id` — no "is this user known to Stripe?" branch.
- It gives us a single uniform code path for all four plans.

### 2.4.1 Subscription created at onboarding (Free) — confirmed

**Yes, even for Free**, the BE also creates a $0 `Subscription` immediately after creating the Customer at end of onboarding (per D2 / D5 design). The Subscription:
- Has `items` = [flat $0 price, metered estimate-overage price, metered seat-overage price].
- Has **no** `default_payment_method` (Stripe accepts this because the recurring amount is $0).
- Triggers the same `customer.subscription.created` webhook used for paid plans, so our state-sync logic is one code path.
- Its `current_period_start` / `current_period_end` are populated by Stripe and mirrored onto the Company doc — these become the source of truth for the billing cycle, replacing the ad-hoc month-based reset for the Stripe-side counters.

So the answer to "do we tell Stripe about Free users at the end of onboarding?" is unambiguously **yes**: both a `Customer` and a `Subscription` are created in Stripe at the end of the onboarding Plan step, even for Free. No payment method, no charge — just the identity and subscription record so everything downstream (metering, webhooks, eventual upgrades) just works.

### 2.5 Free plan handling

**Decision (D2 + D5): Free is the only selectable plan at launch. No card capture up-front. Card is captured the first time the user attempts to exceed the included cap.**

Concretely:
- At onboarding completion, BE creates a Stripe `Customer` for the company plus a **$0 Free Subscription** with all three items attached (flat $0 + metered estimates + metered seats). No `payment_method` is required since the recurring fee is $0.
- The Subscription will fail to charge **only if** an invoice is generated with a non-zero amount (i.e., overages occurred). Stripe's default is to mark the invoice `open` / `uncollectible` and the subscription `past_due`, but it does not retroactively delete the overage events.
- We pre-empt this by **gating estimate creation at the included cap when no payment method is on file**:
  - User has `number_of_estimates_created < 20` → estimate creation proceeds, meter event sent.
  - User has `number_of_estimates_created >= 20` AND no `default_payment_method_*` on Company → block with a "Add a payment method to keep creating estimates" CTA. The CTA opens a Stripe Setup Intent → Payment Element flow that attaches a card to the existing Customer (no new subscription).
  - User has `number_of_estimates_created >= 20` AND a card is on file → estimate creation proceeds, meter event sent, overage will be billed at cycle end.
- Same pattern for seats: roster changes that would push seat count past the included tier are gated identically.

This means **Stripe's invoice never has to chase a missing payment method** — if a user is in "overage mode," they've already attached a card.

---

## 3. Data Model Changes (Beanie / `models/company.py`)

Add to `Company`:

```python
# Stripe linkage
stripe_customer_id: Optional[str] = None
stripe_subscription_id: Optional[str] = None
stripe_subscription_status: Optional[str] = None   # active | past_due | canceled | trialing | incomplete | unpaid
plan_lookup_key: Optional[str] = None              # plan_free | plan_base | plan_pro
plan_selected_at: Optional[datetime] = None
current_period_start: Optional[datetime] = None
current_period_end: Optional[datetime] = None
default_payment_method_last4: Optional[str] = None
default_payment_method_brand: Optional[str] = None
```

The existing `total_estimates_allowed` / `number_of_estimates_created` / `quota_reset_at` fields stay — they're still useful for **fast UI gating** ("you've used 12 of 20 estimates this month") *without* a Stripe round-trip. They remain authoritative for *display* and *soft warnings*; **Stripe is authoritative for billing**.

The plan determines `total_estimates_allowed` going forward:
- Free → 20
- Base → 100
- Pro → 200

Update the `MAX_ESTIMATES` constant in `models/company.py` to a dict keyed by `plan_lookup_key`, or move it to a new `services/billing/plan_config.py` helper. The lazy-reset logic in `services/estimate_quota.py` keeps working — it just reads the limit from the company's plan instead of a global constant.

### Optional but useful: a `BillingEvent` collection

To debug invoice disputes ("user says we overcharged"), persist a denormalized log of every meter event we send: `{company_id, event_name, value, stripe_event_id, idempotency_key, created_at}`. Cheap insurance.

---

## 4. Backend (FastAPI / `platform/`)

### 4.1 New module layout

```
platform/
  routers/
    billing.py                     # /billing/* endpoints
    stripe_webhooks.py             # /stripe/webhook (raw body required — separate router)
  services/
    billing/
      __init__.py
      plan_config.py               # plan_lookup_key → limits/prices map
      stripe_client.py             # Stripe SDK singleton (uses settings.stripe_secret_key)
      checkout.py                  # create_checkout_session, create_billing_portal_session
      meter_events.py              # report_estimate_created, report_seat_snapshot
      webhook_handlers.py          # one handler per event type
  models/
    billing_event.py               # optional audit log
```

### 4.2 New endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `GET` | `/billing/plans` | List configured plans + prices for FE plan-picker (cached) | Authenticated |
| `POST` | `/billing/setup-intent` | **Launch / overage-card-capture path.** Create a Stripe SetupIntent for the company's existing Customer; returns `client_secret` for the Payment Element. | Authenticated |
| `POST` | `/billing/checkout-session` | **Phase 3+.** Create a Stripe Checkout Session for a chosen *paid* plan; returns `client_secret` for Embedded Checkout. Not used at launch since only Free is selectable. | Authenticated |
| `POST` | `/billing/portal-session` | Create a Stripe Billing Portal session for upgrade/downgrade/cancel/payment-method updates | Authenticated |
| `GET` | `/billing/subscription` | Current company's plan, status, period, included/used estimate count, included/used seat count, has-payment-method flag | Authenticated |
| `POST` | `/stripe/webhook` | Receives Stripe events (signed with webhook secret) | **Public** but signature-verified |

### 4.3 Webhook events to handle

| Event | Action |
|---|---|
| `customer.subscription.created` | Set `stripe_subscription_id`, `plan_lookup_key`, `subscription_status`, period dates on Company. |
| `customer.subscription.updated` | Update plan, status, period dates. Recompute `total_estimates_allowed` if plan changed. |
| `customer.subscription.deleted` | Mark subscription canceled; revert `total_estimates_allowed` to Free; mark Company status (NOT archive — see §9). |
| `invoice.created` | Audit-log the invoice into `BillingEvent` (lets us reconcile usage at period close). Fires for both paid and $0 invoices. |
| `invoice.finalized` | No-op for now (kept on the handler whitelist for future use, e.g. emailing a PDF receipt for paid plans). Fires for both paid and $0 invoices. |
| `invoice.paid` | Mark the closed billing period as settled; reset local mirrors `Company.number_of_estimates_created = 0` and refresh `current_period_start` / `current_period_end` from the invoice's parent subscription. **Fires for $0 invoices too** — see §4.3.1. |
| `invoice.payment_failed` | Email user; flag UI banner ("payment failed — update card"); subscription auto-becomes `past_due`. **Does not fire for $0 invoices** since there's no charge attempt. |
| `payment_method.attached` | Update `default_payment_method_last4` / `brand` for Settings UI. |

**Critical:** the webhook router must read the **raw request body** (not parsed JSON) for signature verification. Mount it as a dedicated FastAPI route that uses `request.body()` directly, **before** any middleware that consumes the body.

### 4.3.1 $0 invoice webhook behavior — confirmed

**Yes, Stripe sends webhook events for $0 invoices.** This matters because Free-plan companies that stay within the included caps will close every billing cycle with a $0 invoice, and we still need to know the cycle rolled over.

Concretely, at the end of each Free-plan billing cycle:
1. Stripe assembles the invoice. Line items include the flat $0 plan price plus the metered estimate / seat lines, both of which evaluate to $0 if the user stayed within the included tier.
2. Stripe fires **`invoice.created`** and **`invoice.finalized`** as it would for any invoice.
3. Because the total is $0, Stripe **auto-marks the invoice paid without attempting any charge** and fires **`invoice.paid`**.
4. **`invoice.payment_failed` is NOT fired** for $0 invoices (nothing to fail).
5. Stripe also fires **`customer.subscription.updated`** with the new `current_period_start` / `current_period_end` for the next cycle.

So for Free-plan $0 cycles, the BE receives at minimum: `invoice.created`, `invoice.finalized`, `invoice.paid`, `customer.subscription.updated`. (Plus the corresponding meter snapshots that Stripe takes internally — those do not produce webhooks.)

**BE actions that rely on the $0 webhook chain:**

| Action | Driven by | Why it matters for Free |
|---|---|---|
| Reset `Company.number_of_estimates_created` to 0 at cycle close | `invoice.paid` | The local counter currently uses an ad-hoc month-based reset (`services/estimate_quota.py::ensure_quota_reset`). Once Stripe is wired up, the authoritative reset signal is the cycle-close webhook. We want this firing for Free users too — otherwise their counter never resets, and they'd hit the cap forever. |
| Refresh `current_period_start` / `current_period_end` on Company | `customer.subscription.updated` (and as a fallback, the subscription pointer on `invoice.paid`) | Used by the Settings → Billing tab to render "Resets on May 31". Without this, Free users would see a stale period end. |
| Append a `BillingEvent` audit row | `invoice.created` | Closes the loop on metering — we can prove every estimate that was reported also showed up on an invoice line, even if the invoice was $0. |
| Email user a receipt | `invoice.paid` | **Skipped when `invoice.amount_paid == 0`** — a $0 receipt is just noise. We only email receipts for paid invoices. |

**Migration note:** the current `services/estimate_quota.py::ensure_quota_reset` (lazy month-based reset) can stay as a belt-and-braces fallback for the case where a webhook is dropped/delayed, but the primary reset path becomes the `invoice.paid` handler. Tests in `test_estimate_quota.py` will need to cover both the webhook-driven reset and the lazy-fallback reset paths.

**Risk to watch:** if we ever set `auto_advance: false` on a subscription or use `pause_collection`, the invoice cycle stops generating events. Don't enable those modes for Free without a plan to reset counters another way.

### 4.4 Metering — where we report events

**Estimate creation** — in `services/estimate_quota.py::try_claim_estimate_slot`, after the atomic Mongo increment succeeds. With aggregation = `count`, we don't pass a `value` payload; just emit one event per estimate. Idempotency key uses the post-increment counter so retries don't double-report.

```python
# Pseudocode added to try_claim_estimate_slot after successful claim
await meter_events.report_estimate_created(
    stripe_customer_id=company.stripe_customer_id,
    idempotency_key=f"estimate:{company.id}:{result['number_of_estimates_created']}",
)
```

If the company has no `stripe_customer_id` (legacy data, or onboarding didn't complete), log a warning and skip — don't fail the estimate creation. We'll backfill via a one-shot script during rollout (D4: every existing company → Free plan, see §7 Phase 2).

Before claiming the slot, also enforce the **no-card / over-cap gate** described in §2.5: if `number_of_estimates_created >= included_count(plan)` and `default_payment_method_*` is null, return a 402 with a structured payload telling the FE to surface the "Add a card" flow.

**Seat snapshot — reporting cadence (confirmed)**

The seat meter is fed by **three reporting paths**, each filling a different gap:

| Path | When it fires | What it reports |
|---|---|---|
| **1. Roster-change hook** (event-driven) | Inline in the relevant router whenever the company's active-user count changes | Current active-user count, immediately after the change |
| **2. Daily defensive cron** (scheduled) | Once per day, at a fixed UTC hour | Current active-user count for every company with a `stripe_subscription_id` |
| **3. Cycle-start backstop** (scheduled) | On `customer.subscription.updated` webhook when `current_period_start` advances | Current active-user count, posted into the new cycle |

**Path 1 — Roster-change hook.** The hook fires on every roster mutation that changes the active-user count:

| Trigger | Source | Net change |
|---|---|---|
| Invitation accepted → User created | `routers/auth.py` (invite-accept endpoint) and `routers/invitations.py` | +1 |
| User reactivated (status flips back to active) | `routers/users.py` | +1 |
| User deactivated / archived / removed | `routers/users.py`, `routers/companies.py` (member-removal flow) | −1 |
| Bulk invitation accepts | `routers/invitations.py` | net delta |

Each call posts the **post-change current count** (not a delta) to the `seat_count_snapshot` meter. We post on decrements too, even though under `max` aggregation a decrease doesn't lower the running bill — the reason is (a) keeping the `BillingEvent` audit log complete and (b) the Settings → Billing UI shows live current seat count, which is read from our own DB but cross-referenced against the meter for reconciliation.

Idempotency key per event: `seats:{company_id}:{user_id}:{action}:{timestamp}` — unique per roster mutation so retries from the BE don't double-count, but every distinct mutation produces a distinct event.

**Path 2 — Daily defensive cron.** Runs once per day (UTC) and re-posts the current active-user count for every company that has a `stripe_subscription_id`. Purpose:

- Covers any roster-change hook that silently failed (network blip, deploy in the middle of an invite-accept).
- Covers companies whose seat count hasn't changed in days — without this, a long-running cycle with no roster activity would have *zero* seat events in Stripe for that period, and the meter aggregation would be 0 instead of the actual count.
- Safe under `max`: if the cron posts the same number every day, the running max stays stable; if a hook missed an increment, the cron lifts the max to the correct value within 24 hours.

Implementation: Render Cron Job (`type: cron` in `platform/render.yaml`) running daily at 06:15 UTC, command `python scripts/snapshot_seat_counts.py`. The script calls `services.billing.meter_events.snapshot_all_seat_counts()`. Idempotency key: `seat_snapshot:{company_id}:{YYYY-MM-DD}` — at most one daily snapshot per company per day.

**Path 3 — Cycle-start backstop.** When `customer.subscription.updated` fires with an advanced `current_period_start`, the meter has just rolled over to a new period (running max reset to 0 — see §2.3 D3 reset note). At that exact moment, neither the daily cron nor any roster-change has yet posted into the new cycle, so a brand-new period could read 0 if the user took no action and the daily cron hasn't ticked yet. To prevent that, the cycle-rollover webhook handler immediately re-posts the current active-user count, seeding the new period.

**No payment method gate.** Same over-cap-no-card gate as estimates: if accepting an invitation or reactivating a user would push the company past the included seat count and there's no card on file, the BE returns 402 from the invite-accept / user-activate endpoint, and the FE surfaces the `AddPaymentMethodModal` (§5.3). After the card is attached, the original action is retried.

**What "active user" means** — every User where `User.company == <this company>`. The User model has no `status` / `is_active` field; a user is active by virtue of being attached to the company, and becomes inactive only when their membership is removed. Locked 2026-05-08 (see §8.1).

### 4.5 Idempotency & failure handling

- Every Stripe API call passes an idempotency key.
- Meter event sends are best-effort: failure is logged, but does **not** block the user action (we don't want a Stripe outage to block estimate creation). The local quota counter is still incremented, so we have a record. The optional BillingEvent log lets us replay missed events.
- Webhook handlers must be idempotent — Stripe retries failed deliveries. Use the Stripe `event.id` as a dedup key (insert-or-skip into a `processed_stripe_events` collection).

### 4.6 Config / env vars

**Backend (`platform/.env.local` → `platform/config.py` `Settings`):**

```python
stripe_sk: str                        # already set in .env.local as STRIPE_SK (test mode)
stripe_webhook_secret: str            # added later: from Stripe CLI `stripe listen` output for local dev,
                                      # and from the Dashboard endpoint config for deployed environments
```

Plan lookup keys (`plan_free`, `est_overage_free`, etc.) are hard-coded in `services/billing/plan_config.py` rather than env-driven — they're the same across environments and act as the contract between BE and Stripe.

**Frontend (`portal/.env.local`):**

```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_…
```

⚠️ **Action item Phase 1, day one:** Vite only exposes env vars prefixed with `VITE_` to client bundles. The currently-pasted `STRIPE_PK` won't be readable by React code. **Rename `STRIPE_PK` → `VITE_STRIPE_PUBLISHABLE_KEY`** in `portal/.env.local` (and `portal/.env.example` for documentation) before wiring up the Payment Element.

The publishable key is the only Stripe value the frontend should ever see — never put `STRIPE_SK` or `STRIPE_WEBHOOK_SECRET` anywhere in `portal/`.

---

## 5. Frontend (React / `portal/`)

### 5.1 Onboarding — new "Choose Plan" step

Insert a single new step **before the existing Complete step** in `portal/src/pages/OnboardingPage.tsx`. Update `STEP_LABELS` in `components/onboarding/StepIndicator.tsx`:

```diff
  "Welcome", "Company", "Contacts", "Properties", "Materials", "People",
- "Complete",
+ "Plan", "Complete",
```

Total steps: 7 → 8.

**No Payment step at launch (D2 + D5).** Free is the only selectable plan, and Free does not require a card. Card capture happens later — only if and when a user attempts to exceed the included cap.

**Step 7 — Plan Picker (`components/onboarding/PlanStep.tsx`)**

Layout: 4-card grid:

| Card | State at launch |
|---|---|
| **Free** | $0/mo, primary button **"Select Free Plan"** (only enabled card) |
| **Base** | $99/mo, **"Coming Soon"** pill, button disabled with hover tooltip |
| **Pro** | $199/mo, **"Coming Soon"** pill, button disabled with hover tooltip |
| **Enterprise** | "Custom pricing", **"Contact Sales"** outline button → `mailto:` or contact form |

Each card shows:
- Plan name, monthly price (or "Custom"), "Coming Soon" pill for Base/Pro
- Bulleted feature list (sourced from a typed constant `PLANS_CONFIG` in `lib/billing-plans.ts` — single source of truth, mirrors the BE plan-config map and `subscription-plans.md`)
- Included estimate count + per-overage price ("up to 20 estimates / month, then $5 each")
- Included seat count + per-seat overage price ("up to 3 users, then $10 / user / month")

On Select: call `POST /billing/select-plan` with `plan_lookup_key=plan_free`. BE creates the Stripe `Customer` + $0 Free `Subscription` (idempotent — re-running is safe; see §2.4 / §2.4.1 for the full contract). FE advances to the existing Complete step.

**No card collection in onboarding.** When paid plans launch (Phase 3+), the Plan step will conditionally render an Embedded Checkout panel inline for the selected paid plan. Free continues to skip payment entirely.

### 5.2 Settings → Billing tab

Add to `portal/src/pages/SettingsPage.tsx`:

```diff
 const tabs: TabItem[] = [
   { id: "account", label: "Account" },
   { id: "company", label: "Company" },
   { id: "team-members", label: "Team Members" },
+  { id: "billing", label: "Billing" },
   { id: "material-category", label: "Materials Category" },
   ...
 ];
```

New file: `portal/src/components/settings/BillingTab.tsx`. Fetches `/billing/subscription` and renders:

1. **Current plan card** — plan name, monthly fee, status badge (`active` / `past_due` / `canceled`), period end date.
2. **Usage card** — "Estimates used: 12 / 20 this period" + "Seats: 3 / 3 (no add-on charges)". Show projected overage cost if user is over-included.
3. **Payment method card** — `Visa ending in 4242` + "Update payment method" button → opens Stripe Billing Portal via `POST /billing/portal-session`.
4. **Plan actions** — "Change plan" / "Cancel subscription" (both deep-link to Stripe Billing Portal).
5. **Recent invoices** (Phase 2) — list last 6 invoices with download links from Stripe.

### 5.3 Estimate-create UI — warnings, gate, and card-capture modal

Banner states in the estimates list, driven by `(used, included, hasPaymentMethod)`:

| State | Banner copy |
|---|---|
| `used < included * 0.8` | (no banner) |
| `included * 0.8 <= used < included` | "You've used {used} of {included} included estimates this month. Additional estimates will be billed at ${overage_price} each." |
| `used >= included` AND `hasPaymentMethod` | "You're now creating overage estimates at ${overage_price} each. They'll appear on your next invoice." |
| `used >= included` AND NOT `hasPaymentMethod` | "You've used all {included} included estimates this month. Add a payment method to keep creating estimates." (with primary "Add payment method" button) |

**Gate behavior (D2):** when `used >= included` and no card is on file, the BE returns 402 from `try_claim_estimate_slot`. The FE intercepts the 402 and opens a **card-capture modal** containing Stripe's Payment Element bound to a SetupIntent (fetched from `POST /billing/setup-intent`). On successful card attach, the modal closes and the FE retries the original estimate-create request. Subsequent estimates flow normally as overages.

New components:
- `components/billing/AddPaymentMethodModal.tsx` — wraps Stripe's `<PaymentElement>` for SetupIntent confirmation.
- Hook into the existing estimate-create error path (currently surfaces 429 toasts) to dispatch the modal on 402-with-`code=needs_payment_method`.

Same modal is reusable from the Settings → Billing tab (proactive add-card) and the user-invite flow (when adding a user would push past the seat cap).

---

## 6. Test Plan

### Backend (`platform/tests/`)

- `tests/test_billing_plan_config.py` — plan config map sanity (every plan has price keys, included counts match `subscription-plans.md`).
- `tests/test_billing_checkout.py` — `POST /billing/checkout-session` returns a client_secret for each plan; rejects unauth requests; rejects invalid plan keys.
- `tests/test_billing_subscription.py` — `GET /billing/subscription` returns correct shape; handles companies with no subscription yet.
- `tests/test_stripe_webhooks.py` — signed payload happy path for each event type; reject invalid signature; idempotent on duplicate `event.id`. Use Stripe's signed-payload fixture builder — **do not** mock signature verification.
- `tests/test_meter_events.py` — `report_estimate_created` is called with correct args after `try_claim_estimate_slot` succeeds; not called on failure; idempotency key format is stable. Use `pytest-mock` for the Stripe SDK; integration tests can use Stripe's test-mode meter.
- Update `tests/test_estimate_quota.py` — `total_estimates_allowed` derived from plan, not the global `MAX_ESTIMATES`.

### Frontend (`portal/`)

- `BillingTab.test.tsx` — renders plan/usage/payment-method sections; "Update payment method" calls portal-session endpoint; handles missing-subscription empty state.
- `PlanStep.test.tsx` — clicking Select on Free skips payment step; Base/Pro disabled while `coming_soon`.
- `PaymentStep.test.tsx` — Stripe Embedded Checkout mounts with the correct `client_secret`; success callback advances to completion.

### Manual / E2E (Stripe test mode)

1. Sign up → Free → confirm $0 subscription created in Stripe dashboard, Company has `stripe_customer_id` and `stripe_subscription_id`.
2. Create 25 estimates → verify 25 meter events in Stripe; advance clock to next billing cycle (use Stripe's "Test clocks") → confirm invoice = $0 + 5 × $5 = $25.
3. Sign up → Base → enter test card `4242 4242 4242 4242` → confirm subscription is `active`, period dates populated.
4. Trigger `payment_failed` via Stripe dashboard → verify webhook updates status to `past_due` and Settings → Billing shows the banner.
5. Cancel via Billing Portal → verify Settings reflects canceled state next period.

---

## 7. Phased Rollout

### Phase 0 — Tooling
- Run `npx skills add -y https://docs.stripe.com` (D1)
- Configure Stripe test-mode account; create Products, Prices (`plan_free`, `est_overage_free`, `seat_overage_free`), and the two Meters (`estimates_created` count, `seat_count_snapshot` max)

### Phase 1 — Foundation (BE only, no UI)
- Stripe SDK wired with `stripe_secret_key` from `Settings`
- Stripe Customer creation on Company create
- $0 Free Subscription auto-created when Company onboarding completes (idempotent)
- Webhook handler receiving + persisting state (raw-body verification)
- Plan-config map; `total_estimates_allowed` derived from plan
- Meter event sender wired into estimate creation, behind a `BILLING_METER_ENABLED` feature flag (off by default in production)
- 402 gate in `try_claim_estimate_slot` for over-cap-no-card
- Tests for all of the above

### Phase 2 — Migration of existing companies (D4) ✅ shipped
- ✅ Backfill script: `platform/scripts/backfill_companies_to_free.py` — dry-run default, `--apply` to commit. Verifies existing Stripe IDs against the target account (catches the test→prod transition where docs hold stale test-mode IDs). For each Company: creates Customer (idempotent), creates $0 Free Subscription (idempotent), sets `plan_lookup_key=plan_free`, resets `total_estimates_allowed=20`. Skips companies missing `email`. 7 pytest cases in `tests/test_backfill_companies_to_free.py`.
- ✅ `--prod` flag bypasses `.env.local` to read STRIPE_SK + MONGODB_URL from `.env.production` / `.env`. `--mongo-url` CLI flag for explicit override. `--yes` skips LIVE-mode confirmation for non-interactive use.
- ✅ Production backfill executed: 13 companies all had stale test-mode IDs → all recreated with fresh LIVE Stripe Customers + Subscriptions. Idempotent (re-running shows 13 valid).
- ⏳ Flip `BILLING_METER_ENABLED=on` in production so meter events start reaching Stripe.

### Phase 3 — Onboarding plan picker + Settings → Billing tab (UI launch)
- New `Plan` step in onboarding (Free selectable, Base/Pro Coming Soon, Enterprise contact-sales)
- Free plan onboarding E2E works (no payment widget)
- `Settings → Billing` tab shows plan, usage, payment method (will be empty initially), "Add payment method" button
- `AddPaymentMethodModal` with SetupIntent + Payment Element
- Estimate-list banners (warning / overage-with-card / overage-no-card)
- 402 → modal → retry on estimate-create

### Phase 4 — Polish (✅ shipped)
- ✅ Recent invoices list in Settings → Billing (`GET /billing/invoices/{company_id}`)
- ✅ Stripe Billing Portal deep-link for "Manage subscription" (`POST /billing/portal-session/{company_id}`)
- ✅ Email notifications on `invoice.paid` / `invoice.payment_failed` — handled by **Stripe-native customer emails** (Stripe Dashboard → Settings → Customer emails). Confirm "Successful payments" and "Failed payments" toggles are on. No app-side email plumbing needed.
- ✅ Enterprise "Contact Sales" form (`POST /billing/enterprise-contact`) — replaces the mailto link. Pulls name/email/company from the auth context; only asks for the message + optional phone. Sends via Brevo plain HTML (`services/brevo_email.send_brevo_plain_email`) to support@3maples.ai with `reply-to` set to the requester.

### Phase 5 — Paid plan launch (future, off the critical path)
- Flip Base / Pro from "Coming Soon" → selectable
- Embedded Checkout in Plan step for paid plans (D6)
- Plan-change UX in Settings → Billing (with proration preview)

---

## 8. Risks & Open Items

1. ~~**Seat counting — what's an "active user"?**~~ ✅ **LOCKED 2026-05-08** — every User attached to the company (`User.company == <id>`). The User model has no archived/disabled flag, so this is option (a). Daily snapshot cron implemented as `services.billing.meter_events.snapshot_all_seat_counts()` invoked by `scripts/snapshot_seat_counts.py` from a Render `type: cron` job at 06:15 UTC.
2. **Mid-cycle plan changes (Phase 5 only).** Stripe's `proration_behavior="create_prorations"` creates an immediate prorated invoice when upgrading. We should surface the proration preview in the UI before confirming. Not on the critical path for launch.
3. **Test clocks for QA.** Stripe Test Clocks let us advance subscription time deterministically — required for any E2E test that exercises billing cycles or the `max` seat aggregation reset behavior.
4. **Webhook reliability.** Stripe retries for ~3 days. If our service is down longer, events are lost. Mitigate with a daily reconciliation job that fetches active subscriptions from Stripe and diffs against the Company collection.
5. ~~**CORS / webhook routing.**~~ ✅ **VERIFIED 2026-05-08** — `stripe_webhooks_router` is included in `main.py:203` without `protected_route_dependencies`, with an explicit comment that it MUST NOT be gated. CORS middleware doesn't block it. Signature verification happens inside the router.
6. **Stripe Tax.** Out of scope for this plan. Likely needed before paid-plan launch (Phase 5) for Canadian/US tax. Tracked as a follow-up.
7. **Customer-side data hygiene during migration.** When the Phase 2 backfill creates Stripe Customers for existing companies, double-check that we have a valid `email` on every Company doc; Stripe requires it. Backfill script should report (and skip) any company missing an email, not silently fail.

---

## 9. Decisions (Locked)

| # | Question | Decision |
|---|---|---|
| D1 | Install `npx skills add -y https://docs.stripe.com`? | ✅ **Install** as Phase 0 step. |
| D2 | Free plan: hard-cap at 20 estimates if no card on file, or require card upfront? | ✅ **No card up-front.** When user reaches included cap with no card on file, BE returns 402 and FE prompts for card via SetupIntent + Payment Element modal. Same gate applies to seat overages. |
| D3 | Seat aggregation: `last` vs `max`? Estimate aggregation? | ✅ **Seats = `last` + backend high-water-mark gating** (Stripe doesn't expose native `max`; we approximate it by only posting events when seat count increases — see §2.3 for the full mechanism). **Estimates = `count`**. Stripe meter aggregations are scoped to the subscription's billing period and reset at each cycle start — no app-side reset logic needed for the Stripe-side counters themselves; the local `seat_count_period_high_water` mirror does need a per-cycle reset, handled in the `customer.subscription.updated` webhook. |
| D4 | Existing companies: grandfather at 25, or migrate to Free (20)? | ✅ **Migrate to Free.** Product hasn't launched; one-shot backfill script in Phase 2 sets every existing Company to `plan_lookup_key=plan_free`, `total_estimates_allowed=20`, creates Stripe Customer + $0 Subscription. |
| D5 | Base / Pro selectable at launch? | ✅ **Coming Soon only — disabled / not selectable.** Enabled in Phase 5. |
| D6 | Embedded vs hosted Checkout? | ✅ **Embedded Checkout** (Phase 5+, when paid plans launch). Free plan uses no Checkout at all. |
| D7 | Billing cycle anchor — anniversary or calendar month? | ✅ **Anniversary.** The subscription's `billing_cycle_anchor` is set to creation time; Stripe rolls the period on the same day-of-month each cycle. Avoids day-one prorations. |
| D8 | Free plan in Stripe? | ✅ **Yes — create $0 Subscription** in Stripe at the end of onboarding for Free users. (See §2.4.1 for full contract.) |
| D9 | Trial period for paid plans (Phase 5)? | ✅ **No free trial.** Base/Pro will charge from day one. `trial_period_days` not set on the subscription. |
| D10 | Default currency? | ✅ **USD.** Every Product/Price created in Stripe uses `currency: "usd"`. Adding CAD or other currencies later requires new Price objects per currency. |
| D11 | Lookup-key naming convention? | ✅ Plans: `plan_free`, `plan_base`, `plan_pro`. Metered prices: `est_overage_free`, `est_overage_base`, `est_overage_pro`, `seat_overage_free`, `seat_overage_base`, `seat_overage_pro`. Meters: `estimates_created`, `seat_count_snapshot`. |

---

## 10. Files Touched (Summary)

### New
- `platform/routers/billing.py`
- `platform/routers/stripe_webhooks.py`
- `platform/services/billing/{__init__,plan_config,stripe_client,checkout,setup_intents,meter_events,webhook_handlers}.py`
- `platform/models/billing_event.py` (optional)
- `platform/scripts/backfill_stripe_free_subscriptions.py` — Phase 2 one-shot
- `platform/tests/test_billing_*.py`, `test_stripe_webhooks.py`, `test_meter_events.py`
- `portal/src/components/onboarding/PlanStep.tsx`
- `portal/src/components/billing/AddPaymentMethodModal.tsx`
- `portal/src/components/settings/BillingTab.tsx`
- `portal/src/lib/billing-plans.ts`
- `portal/src/api/billing.ts`

(Note: no separate `PaymentStep.tsx` — onboarding has no payment step at launch; Embedded Checkout will be inlined into `PlanStep.tsx` when paid plans launch in Phase 5.)

### Modified
- `platform/models/company.py` — add Stripe fields
- `platform/main.py` — register billing & webhook routers
- `platform/database.py` — register `BillingEvent` model
- `platform/config.py` — Stripe env vars
- `platform/services/estimate_quota.py` — derive limit from plan; emit meter event
- `platform/routers/companies.py` — create Stripe Customer on Company create
- `portal/src/pages/OnboardingPage.tsx` — insert Plan/Payment steps
- `portal/src/components/onboarding/StepIndicator.tsx` — new labels & step count
- `portal/src/pages/SettingsPage.tsx` — register `billing` tab
- `documentation/development/plans/subscription-plans.md` — link to this doc

### Documentation
- This file, plus a final pass on `subscription-plans.md` and `CLAUDE.md` (a short Maple-style note about how billing is wired).
