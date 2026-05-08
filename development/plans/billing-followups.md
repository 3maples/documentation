# Stripe Billing — Follow-ups

Source: `/code-review` of the Stripe billing integration (platform + portal), May 2026.

The five HIGH-severity blockers shipped with the original change:

- platform: `current_period_*` field relocation under pinned API version `2026-04-22.dahlia`
- platform: webhook dedupe-before-success retry gap in `routers/stripe_webhooks.py`
- platform: synchronous Stripe SDK calls inside `async def` handlers (event-loop blocking)
- portal: `AddPaymentMethodModal.onSuccess` retry path that didn't actually retry the create-draft effect
- portal: `ManagePlanModal` rendering bare `<div>` outside `<DialogContent>` (lost dialog semantics)

The items below are deferred housekeeping. Pick them up in order of severity, repo-by-repo.

---

## platform/

### MEDIUM — Hoist the `1_000_000` "effectively unlimited estimates" magic number

**Where:** `routers/billing.py:417`, `services/billing/webhook_handlers.py:132`, `services/billing/plan_config.py:68`.

**Why:** Three call sites use the same literal to disable the local quota cap once a payment method is attached. Drift between any two of them produces inconsistent gating.

**Fix:** Define `EFFECTIVE_UNLIMITED_ESTIMATES = 1_000_000` (or similar) as a module-level constant in `services/billing/plan_config.py` and import from the other two locations.

---

### MEDIUM — Reconciliation cron for "soft-failed" plan selection

**Where:** `routers/billing.py:186` (select-plan), `routers/billing.py:492` (enterprise-contact).

**Why:** Both endpoints catch `Exception` broadly with the comment "reconciliation cron retries" — but the cron doesn't exist yet. A user whose plan-selection Stripe call silently failed thinks they're on Pro/Base; the BE has the local plan set but no Stripe subscription. There's nothing to find their orphaned record later.

**Fix:** Either (a) build the planned reconciliation job that scans companies with a non-Free local plan but no `stripe_subscription_id` and replays the missing call, or (b) persist a `BillingReconciliationQueue` row at the catch site so the future cron has explicit work to find. At minimum, fire a Sentry capture inside the except block and surface a soft-warning flag in the response so the FE can show "Your plan is saved; we'll finish setup shortly."

---

### MEDIUM — Implement `payment_failed` user notification

**Where:** `services/billing/webhook_handlers.py:114` (TODO).

**Why:** Customers in `past_due` after a card decline are not notified by the platform. Stripe's "Smart Retries" Dashboard emails partially cover this, but the codebase shouldn't rely on that implicitly — and we lose the chance to brand the message.

**Fix:** Send via `services/brevo_email.send_brevo_plain_email` from the `invoice.payment_failed` handler. Subject: "Payment failed — update your card." Link target: customer-portal session URL.

---

### MEDIUM — Customer-portal `return_url` should not hardcode prod

**Where:** `routers/billing.py:355`.

**Why:** The fallback `"https://app.3maples.ai/settings"` kicks dev/staging users into prod if the FE forgets to pass `return_url`.

**Fix:** Add `app_base_url: str` to `Settings` in `config.py` and use `f"{settings.app_base_url}/settings"` as the fallback. Default to `http://localhost:5173` in `.env.example`.

---

### MEDIUM — Add `idempotency_key` to SetupIntent creation

**Where:** `routers/billing.py:267-275`.

**Why:** Other Stripe calls in this codebase pass an `idempotency_key` (e.g. `services/billing/customer.py:69`, `services/billing/subscriptions.py:107`). SetupIntent creation doesn't, so a double-click or a network-blip retry produces duplicate SetupIntents in the Stripe Dashboard.

**Fix:** `idempotency_key=f"setup_intent:{company.id}:{int(time.time() // 60)}"` (1-minute window) or accept a client-supplied key from the request body.

---

### MEDIUM — Narrow the `except` in `customer.py:67`

**Where:** `services/billing/customer.py:67`.

**Why:** Bare `except Exception` on the Customer-retrieve path falls through to "create fresh" on any transient error (network, rate limit, 5xx). The Stripe-side idempotency key prevents true dupes within 24h, but the company doc's `stripe_customer_id` is then orphaned.

**Fix:** Catch only `stripe.error.InvalidRequestError` (which is what `resource_missing` raises). Re-raise `APIConnectionError` / `RateLimitError` so the request returns 5xx and the FE retries cleanly.

---

### MEDIUM — Atomic high-water update in `meter_events.py`

**Where:** `services/billing/meter_events.py:96-98`.

**Why:** Two concurrent estimate creations both observing `high_water=5` and trying to bump to 6 and 7 will race — last writer wins, and the high-water mark could end up at 6 (lower than the meter's actual `last`). The next snapshot is then considered ≤ high-water and silently dropped.

**Fix:** Use the same conditional-update pattern as `services/estimate_quota.try_claim_estimate_slot`:
```python
await Company.find_one(
    {"_id": company.id, "seat_count_period_high_water": {"$lt": seat_count}}
).update({"$set": {"seat_count_period_high_water": seat_count}})
```

---

### LOW — Use `Query(..., ge=1, le=50)` for `list_invoices` limit

**Where:** `routers/billing.py:282`.

**Why:** Inline `max(1, min(limit, 50))` clamping silently coerces bad input. `Query(12, ge=1, le=50)` returns a clean 422 instead.

---

### LOW — Validate Stripe `brand` against an allow-list before persisting

**Where:** `services/billing/webhook_handlers.handle_payment_method_attached` and `routers/billing.py:111`.

**Why:** The brand string flows from Stripe → DB → FE rendering. Not a security issue today (Stripe controls the value), but if it's ever rendered un-escaped, an unexpected brand value breaks the UI.

**Fix:** Lowercase and check membership in `{"visa", "mastercard", "amex", "discover", "diners", "jcb", "unionpay", "unknown"}` before persisting.

---

### LOW — Drop the `event_type or "unknown"` defensive branch

**Where:** `routers/stripe_webhooks.py:65`.

**Why:** Signature verification has already passed, so the event is well-formed. A missing `type` would be a Stripe SDK bug, not a runtime expectation. The defensive `or "unknown"` lets a malformed event get persisted with a placeholder label.

**Fix:** `event_type = event_dict["type"]` and let the KeyError bubble.

---

### LOW — Don't write Stripe webhook signing secret to repo working tree

**Where:** `scripts/setup_stripe_webhook.py:140-157`.

**Why:** The script writes the signing secret to `secrets/webhook_signing_secret.<id>.txt` with `chmod 0600`. Reasonable, but the file persists until manually removed and an operator who misses the print-message reminder leaves a real `whsec_…` in the working tree.

**Fix:** Use `tempfile.NamedTemporaryFile(delete=False, dir="/tmp")` outside the repo, or print the secret to stderr and have the operator pipe to `.env` directly. Alternatively, register an `atexit` handler that clears the file unless `--keep-secret` was passed.

---

## portal/

### MEDIUM — Persist `selectedPlan` to localStorage during onboarding

**Where:** `src/pages/OnboardingPage.tsx:35,70`.

**Why:** `currentStep` is persisted but `selectedPlan` is not. A refresh on step 7 (CompletionStep) lands the user with `selectedPlan === null`, falling back to `PLAN_DETAILS.plan_free` in `CompletionStep` — telling them they're on Free even when they picked Pro/Base in step 6.

**Fix:** Persist `selectedPlan` alongside the step counter, OR call `billingApi.getSubscription(companyId)` in CompletionStep when `planLookupKey` is null and use the live plan.

---

### MEDIUM — Generalize `PlanPickerGrid` button label

**Where:** `src/components/billing/PlanPickerGrid.tsx:140-145`.

**Why:** `buttonLabel` is hardcoded to "Select Free Plan" for any selectable plan. The day Base or Pro flips `selectableAtLaunch: true`, every button reads "Select Free Plan."

**Fix:** ``Select ${plan.displayLabel} Plan`` — or just "Select plan" if displayLabel feels redundant.

---

### MEDIUM — Re-fetch SetupIntent on `companyId` change in AddPaymentMethodModal

**Where:** `src/components/billing/AddPaymentMethodModal.tsx:48-76`.

**Why:** The effect early-returns on `!open` and only re-fetches when `open` toggles. If `companyId` changes while the modal stays open (parent swaps companies), the modal keeps the stale `clientSecret` for the previous customer — and attaches the card to the wrong Stripe Customer.

**Fix:** Don't early-return on `!open`. Use `let cancelled = false` and only short-circuit the network fetch on `!open`, but let the effect re-run on `companyId` change. Or, if companyId is documented to be stable per session, accept that and add a comment.

---

### MEDIUM — Drive `billing-plans` constants from the BE `listPlans()` API

**Where:** `src/lib/billing-plans.ts:45-119`.

**Why:** The file's docstring acknowledges this is a hand-maintained mirror of `plan_config.py`. Billing fields (`includedEstimates`, `estimateOverageCents`, `flatPriceCents`, `includedSeats`, `seatOverageCents`) are duplicated. Drift here means the customer sees the wrong included counts or overage rates.

**Fix:** `billingApi.listPlans()` already exists. Drive the card grid from BE data. Keep only the **display-only** fields (tagline, features, supportLines, bottomInfoLines) hardcoded in the frontend. As a stopgap: add a unit test that compares the BE `listPlans` response shape against the FE constants and fails on drift.

---

### MEDIUM — Don't silently warn on `syncPaymentMethod` failure

**Where:** `src/components/billing/AddPaymentMethodModal.tsx:181-186`.

**Why:** If `syncPaymentMethod` fails post-attach, only `console.warn` runs. The user sees "Saved" UX but the BE reflects no card. The comment says the webhook backfills, but in dev with no `stripe listen` running, or with webhook delivery delays in prod, the BillingTab keeps showing "No card on file" and the user re-attaches.

**Fix:** Fire a Sentry capture (Sentry is already in deps). Optionally surface a non-blocking toast like "Card saved — refreshing details…" and trigger a BillingTab reload regardless of whether sync succeeded.

---

### MEDIUM — `PlanStep` should disable the grid when `companyId` is null

**Where:** `src/components/onboarding/PlanStep.tsx:18-33`.

**Why:** If `companyId` is null when the user clicks Select, they see "Missing company context. Please reload and try again." But by step 6, the company was created in step 1 — a missing companyId here is a code-flow bug, not a user-recoverable state. Telling the user to reload is unhelpful.

**Fix:** Pass a `disabled` prop down to `PlanPickerGrid` when `!companyId`. Render an inline "Initializing your account…" notice instead of letting the user click and fail.

---

### LOW — Remove or use `publishable_key_hint`

**Where:** `src/api/billing.ts:38-41`.

**Why:** `SetupIntentResponse.publishable_key_hint` is declared but never read. Publishable key comes from `VITE_STRIPE_PUBLISHABLE_KEY` only. Dead field.

**Fix:** Either remove from the type, or use it as a runtime sanity check ("BE hint disagrees with FE env" → log warning) inside `getStripePromise`.

---

### LOW — Drop `opacity-95` on coming-soon plans

**Where:** `src/components/billing/PlanPickerGrid.tsx:152`.

**Why:** A 5% reduction is visually indistinguishable from full opacity. The intent is clearly to dim Coming-Soon plans. Either drop the prop or strengthen.

**Fix:** `opacity-70` or remove `dimWhenComingSoon` if the "Coming Soon" badge is enough.

---

### LOW — Pluralize plan summary copy

**Where:** `src/components/onboarding/CompletionStep.tsx:23`.

**Why:** "Up to 3 team members" / "Up to 20 new estimates per month" hardcodes plural. A future plan with `includedSeats: 1` would read "Up to 1 team members."

**Fix:** `${n === 1 ? "team member" : "team members"}` — same for estimates.

---

### LOW — Map raw Stripe `subscription_status` to friendly labels in BillingTab

**Where:** `src/components/settings/BillingTab.tsx:104-107`.

**Why:** `state.stripe_subscription_status` is rendered as-is. Values like `incomplete_expired`, `past_due`, `trialing` show literally with underscores — cosmetic but user-facing.

**Fix:** Small `STATUS_LABELS` map: `active → "Active"`, `past_due → "Past Due"`, `trialing → "Trialing"`, `incomplete → "Incomplete"`, `incomplete_expired → "Setup Expired"`, `canceled → "Canceled"`, `unpaid → "Unpaid"`.

---

### LOW — Drop redundant 5000-char client check in EnterpriseContactModal

**Where:** `src/components/billing/EnterpriseContactModal.tsx:56-58`.

**Why:** `MESSAGE_MAX_LEN` is already enforced via `maxLength` on the textarea, making the explicit length check redundant defense.

**Fix:** Remove the duplicate check, or add a comment confirming it matches the BE `enterprise-contact` endpoint validation.

---

### LOW — Extract `<PlanSummaryBlock>` component

**Where:** `CompletionStep.tsx:36-58`, `BillingTab.tsx`, `PlanPickerGrid.tsx`.

**Why:** Three places render `included_seats` / `included_estimates` summary blocks. Minor DRY concern — adding a fourth field to the Free-plan summary card would mean updating three spots.

**Fix:** Optional refactor — extract `<PlanSummaryBlock plan={plan} variant="onboarding" | "billing-tab" | "card" />` if a fourth field gets added or another surface needs the block.
