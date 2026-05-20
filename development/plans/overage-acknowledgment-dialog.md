# Overage Acknowledgment Dialog

## Context

We currently show a generic "no card on file" warning in only some overage situations, and Maple credit exhaustion already surfaces inline in the Maple panel via the orchestrator's refusal payload. Product wants each of the three overage surfaces — **Team Members invites**, **Estimate creation**, and **Maple credits** — to have its own clearly-worded acknowledgment dialog with specific copy, specific gating rules, and specific post-OK behavior. Goal: ensure every paying user explicitly acknowledges overage charges before they accrue, while keeping repeat friction down for Estimates (user-controlled pref) and Maple credits (first-time only).

## Per-resource behavior matrix

| Surface | When dialog shows | Pref / checkbox | OK (card on file) | OK (no card) |
|---|---|---|---|---|
| **User invite** (Team Members) | **Always**, when the invitation would push seats over the included count | None | Continue with invitation | Open Add Card dialog |
| **Estimate create** | When over included estimates AND user pref `show_overage_notification` is ON (or no card) | Existing pref + in-dialog "Show this next time" checkbox | Continue with estimate creation | Open Add Card dialog |
| **Maple credits** | **First time only** the user is over credits (or every time if no card on file) — surfaced as a link inside the Maple panel chat bubble | None | Dismiss dialog, return user to Maple panel (subsequent overages proceed silently) | Open Add Card dialog |

### Exact dialog copy

**User invite**
- Has card: *"You are going over the number of users included in the plan. Additional charges will apply at $10/user/month. To proceed, please acknowledge this charge."*
- No card: *"You are going over the number of users included in the plan. Additional charges will apply at $10/user/month. To proceed, please acknowledge this charge and add a payment method."*

**Estimate create**
- Has card: *"You are going over the number of estimates included in the plan. Additional charges will apply at $3/estimate. To proceed, please acknowledge this charge."*
- No card: *"You are going over the number of estimates included in the plan. Additional charges will apply at $3/estimate. To proceed, please acknowledge this charge and add a payment method."*

**Maple credits** (link text in panel: *"You have run out of Maple credits, please click to proceed."*)
- Has card (first time): *"You have used up all the Maple credits included in the plan. Additional charges will apply at $0.05/1K Maple credits. To proceed, please acknowledge this charge."*
- No card: *"You have used up all the Maple credits included in the plan. Additional charges will apply at $0.05/1K Maple credits. To proceed, please acknowledge this charge and add a payment method."*

## Design summary

- **One reusable dialog component**, three resource configs. The dialog accepts `resource`, `hasPaymentMethod`, optional `showPrefCheckbox` (only `true` for Estimates), and renders the matching copy.
- **Pre-flight is client-side** for User invite and Estimate create (frontend already has `used_*` / `included_*` / `has_payment_method` from `GET /billing/subscription`).
- **Maple credits is server-driven**: backend orchestrator already returns a refusal chat bubble (`platform/routers/agents.py:_maple_credits_refusal_payload()` lines 380–397). We change that payload's link text and target so the frontend opens the dialog instead of navigating to `/settings`. The backend gate (`assert_token_quota()`) is relaxed so that **has-card + already-acknowledged-Maple-overage** users pass through (overage billed silently).
- **Per-resource "acknowledged at" timestamps** replace the existing single global `overage_acknowledged_at`. We need to know specifically whether the user has acknowledged Maple-credit overage (for the "first time only" rule). User and Estimate flows don't need first-time logic but a per-resource timestamp keeps audit trail and idempotency clean.

## Phases

### Phase 1 — Backend: schema + audit + acknowledgment endpoint

1. **`platform/models/user.py`** — replace the single `overage_acknowledged_at` with three nullable timestamps:
   - `users_overage_acknowledged_at: Optional[datetime] = None`
   - `estimates_overage_acknowledged_at: Optional[datetime] = None`
   - `maple_credits_overage_acknowledged_at: Optional[datetime] = None`
   - Keep `show_overage_notification: bool = True` (now scoped to Estimates only in UX, but keeping field name avoids a migration).
2. **`platform/models/audit_log.py`** — keep existing `OVERAGE_ACKNOWLEDGED` and `OVERAGE_ADD_CARD_CLICKED`; add a `resource` key in metadata (`"users" | "estimates" | "maple_credits"`).
3. **`platform/routers/users.py`** — `POST /users/me/overage-event` body becomes `{ "type": "acknowledged" | "add_card_clicked", "resource": "users" | "estimates" | "maple_credits" }`.
   - `"acknowledged"`: atomic `find_one_and_update` stamping the resource-specific field if unset; emit audit log; idempotent per resource.
   - `"add_card_clicked"`: always emit audit log; additionally stamp the resource-specific `*_overage_acknowledged_at` if unset (clicking Add Card implicitly acknowledges).
4. **`platform/routers/agents.py`** — relax `assert_token_quota()` / orchestrator gate so that:
   - over-limit + has-card + `maple_credits_overage_acknowledged_at` is set → proceed (overage billed).
   - over-limit + has-card + not acknowledged → return refusal bubble (new copy below).
   - over-limit + no-card → return refusal bubble regardless of acknowledgment state.
5. **`_maple_credits_refusal_payload()`** — change link text to *"You have run out of Maple credits, please click to proceed."* and change link target to a sentinel route the frontend MapleMarkdown layer intercepts (e.g. `/portal/maple-credits-overage`) — clicking it opens the dialog rather than navigating.
6. **Tests:**
   - User defaults for new timestamp fields.
   - `POST /users/me/overage-event` per-resource idempotency + add-card stamping.
   - Orchestrator gate: blocks no-card / unacknowledged-has-card; allows acknowledged-has-card.

### Phase 2 — Frontend: shared dialog + helpers

1. **`portal/src/components/billing/OverageAcknowledgmentDialog.tsx`** (new) — props:
   - `open: boolean`
   - `resource: "users" | "estimates" | "maple_credits"`
   - `hasPaymentMethod: boolean`
   - `showPrefCheckbox?: boolean` (Estimates only; default `false`)
   - `prefDefault?: boolean` (Estimates only)
   - `onConfirm(showNextTime?: boolean): void`
   - `onAddCard(): void`
   - `onCancel(): void`
   - Renders the exact copy from the matrix above based on `resource` + `hasPaymentMethod`.
   - Cancel / OK buttons when `hasPaymentMethod`; Cancel / Add Card when not. (No "OK" + Add Card combination — OK in the no-card variant **is** the Add Card action per spec.)
2. **`portal/src/lib/teamSeats.ts`** — `evaluateSeatsOverageGate()` becomes "always prompt when over included seats" (drop the pref check; remove the `shouldPrompt: false when has-card && pref-off` branch).
3. **`portal/src/lib/estimateOverage.ts`** (existing `evaluateEstimateGate()`) — keep current behavior (pref-driven + always-prompt-no-card).
4. **`portal/src/lib/mapleCreditsOverage.ts`** (new) — small helper: given user state + subscription, returns `{ shouldShowDialog, hasPaymentMethod }`. Used by the Maple panel link click handler. Frontend doesn't pre-empt the chat — the backend tells the frontend when to show the link; this helper just decides which dialog variant to render once the user clicks.
5. **`portal/src/api/users.ts`** — `recordOverageEvent({ type, resource })` (extend existing function to accept `resource`).
6. **Tests:** dialog renders correct copy per (resource × hasPaymentMethod) combo; checkbox only present for Estimates; OK fires correct callback per variant.

### Phase 3 — Frontend: wire into call sites

1. **User invite — `portal/src/pages/SettingsPage.tsx:1042-1062`**:
   - Replace existing seats gate consumption with the new "always prompt" gate.
   - Remove the legacy paid-seat modal at lines 2545–2593 (now replaced by `OverageAcknowledgmentDialog` with `resource="users"`).
   - OK + has-card → fire `recordOverageEvent({type: "acknowledged", resource: "users"})` then proceed with invitation API call.
   - OK + no-card → fire `recordOverageEvent({type: "add_card_clicked", resource: "users"})` then open existing `AddPaymentMethodModal`. Do **not** auto-proceed with the invitation after card is added — user re-submits.
2. **Estimate create — `portal/src/pages/EstimatesPage.tsx:113-208`** (covers duplicate path) **and `portal/src/pages/NewEstimateWithActivityPage.tsx:302-313`**:
   - Replace `isAtPlanLimitWithoutCard()` (and existing `evaluateEstimateGate`) consumption with the new dialog component.
   - `showPrefCheckbox={true}`, `prefDefault={user.show_overage_notification}`.
   - OK + has-card → fire `recordOverageEvent({type:"acknowledged", resource:"estimates"})`; if checkbox toggled, also persist pref via existing user-update endpoint; then proceed.
   - OK + no-card → fire `recordOverageEvent({type:"add_card_clicked", resource:"estimates"})`; open `AddPaymentMethodModal`.
   - **Keep** the existing 402 `needs_payment_method` catch in both files as a server-driven fallback (covers race conditions / multi-tab).
3. **Maple credits — `portal/src/components/Layout/MapleMarkdown.tsx:49-85`**:
   - Detect the sentinel link target (e.g. `/portal/maple-credits-overage`) and open `OverageAcknowledgmentDialog` with `resource="maple_credits"` instead of navigating.
   - OK + has-card → fire `recordOverageEvent({type:"acknowledged", resource:"maple_credits"})`; dismiss dialog. User remains in Maple panel; subsequent overage messages from the orchestrator will now succeed (server-side gate sees the timestamp).
   - OK + no-card → fire `recordOverageEvent({type:"add_card_clicked", resource:"maple_credits"})`; open `AddPaymentMethodModal`.

### Phase 4 — Frontend: Account page

1. **`portal/src/pages/SettingsPage.tsx` Account tab (lines 1228-1355)** — keep the existing "Show overage notification" checkbox (now labelled *"Show estimate overage notification"* to clarify scope), default `true`, bound to `user.show_overage_notification`. Save via existing form pattern.
2. Remove any UI / copy that implies the pref applies to user invites or Maple credits.

## Files to modify

**Backend (platform/):**
- `models/user.py` — three new `*_overage_acknowledged_at` fields; drop the legacy single field (or rename to `estimates_overage_acknowledged_at` for cheap migration).
- `routers/users.py` — `POST /users/me/overage-event` accepts `resource`.
- `routers/agents.py` — relax token-quota gate; update refusal payload link.
- `tests/test_users_api.py` and `tests/test_agents_api.py` — per-resource idempotency + relaxed-gate tests.

**Frontend (portal/):**
- `src/components/billing/OverageAcknowledgmentDialog.tsx` — new
- `src/lib/teamSeats.ts` — drop pref branch
- `src/lib/mapleCreditsOverage.ts` — new
- `src/components/Layout/MapleMarkdown.tsx` — sentinel link interception
- `src/pages/SettingsPage.tsx` — invite wiring + delete legacy modal + Account-tab label tweak
- `src/pages/EstimatesPage.tsx` and `src/pages/NewEstimateWithActivityPage.tsx` — wire dialog
- `src/api/users.ts` — `recordOverageEvent({type, resource})`
- Matching test files

## Verification

- **Backend tests** (`cd platform && ./run_tests.sh tests/test_users_api.py tests/test_agents_api.py`):
  - Per-resource acknowledgment idempotency.
  - Orchestrator gate allows has-card + acknowledged users, blocks the other two cases.
- **Frontend tests** (`cd portal && npm test -- OverageAcknowledgmentDialog SettingsPage EstimatesPage NewEstimateWithActivityPage MapleMarkdown`):
  - Dialog renders the exact copy from the matrix per (resource × hasPaymentMethod).
  - User-invite dialog always opens when over seats (independent of pref).
  - Estimate dialog opens per pref; pref toggle round-trips.
  - Maple-credits sentinel link click opens dialog; OK fires correct event.
- **Manual E2E**:
  1. Seed a company at seats = included; invite a user → dialog shows (has-card variant); OK invites.
  2. Toggle pref off; create estimate at limit → dialog still shows (no card OR pref-on); flip pref on/off via Account tab and confirm.
  3. Burn through Maple credits in chat → orchestrator returns refusal bubble with new link text; click → dialog; OK + has-card → next message succeeds and no link appears.
  4. Repeat (3) with no card on file → every overage attempt re-prompts the dialog with the "add payment method" variant.

## Open items

- **Migration of existing `overage_acknowledged_at` field**: pick one — (a) rename to `estimates_overage_acknowledged_at` in a single migration step (simplest, but assumes existing acks were for estimates), or (b) leave the old field unused and add three new fields. Recommend (a).
- **Audit log retention**: per-resource metadata makes the audit row useful even after the global "once per user" semantics are gone. No retention policy change needed.
- **Changelog entry**: not in scope per project policy — user triggers changelog entries explicitly.

## Risks

- **Server-side gate relaxation for Maple credits** is the biggest behavior change: a user who has-card and previously acknowledged will now silently incur overage charges every time they hit credits. Make sure the acknowledgment dialog copy is unambiguous about ongoing charges, and that the Account page surfaces current credit usage so users can monitor.
- **Sentinel-link convention**: relying on a magic URL string for the Maple panel dialog is fragile. Mitigate by defining the constant in one shared module (`portal/src/lib/mapleCreditsOverage.ts`) and importing it on both the markdown interceptor and any test that exercises the orchestrator refusal payload.
- **Race conditions**: existing 402 fallbacks in estimate paths still need to keep working (already covered above). For invites, the backend invite endpoint should also enforce the seat limit so a frontend bypass doesn't silently add a paid user without acknowledgment.
