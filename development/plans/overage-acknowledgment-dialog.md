# Overage Acknowledgment Dialog

## Goal

Replace the current "no card on file" overage warning with a friendlier, broader acknowledgment dialog that:

1. Warns **every** user (with or without card) when an action will go over their plan's limit for Users, Estimates, or Maple Credits.
2. Lets users suppress the warning via a per-user **Show overage notification** preference on their Account page (default: ON).
3. When card is on file → dialog has **Cancel / OK**. OK proceeds; first-ever OK click is audit-logged.
4. When no card is on file → dialog has **Cancel / Add Card** with a merged friendly + add-card message. First-ever Add Card click is audit-logged.
5. Pref is mirrored in-dialog via a "Show this next time" checkbox (omitted in the no-card variant since the no-card path always shows).
6. Dialog is **never shown** from the Maple panel — actions originating there bypass it.

## Design summary

- **Pre-flight is client-side only.** Frontend already has `used_*` / `included_*` / `has_payment_method` from `GET /billing/subscription`. No new "would this overage" endpoint is needed.
- **Backend changes are minimal:** one new pref field on `User`, two new `AuditAction` enum values, one endpoint to record the once-per-user acknowledgment events idempotently, and the existing user-update endpoint takes the new pref.
- **Maple panel exclusion is a frontend choice** — the Maple panel's send path simply doesn't call the dialog. Backend keeps its existing 402 behavior for the no-card-Maple-Credits case so the panel can render its own inline refusal message.

## Phases

### Phase 1 — Backend: schema + audit actions

1. **Add to `User` model** (`platform/models/user.py`):
   - `show_overage_notification: bool = Field(default=True)`
   - `overage_acknowledged_at: Optional[datetime] = None` — set on first OK click; used for once-per-user idempotency of the acknowledgment audit log.
   - *(No `overage_add_card_clicked_at` field.)* The no-card dialog only fires when `default_payment_method_last4 is None`, so the UX itself prevents repeat clicks once a card is added. We log every Add Card click from the dialog and let card state gate it naturally.
2. **Add to `AuditAction` enum** (`platform/models/audit_log.py`):
   - `OVERAGE_ACKNOWLEDGED = "overage.acknowledged"`
   - `OVERAGE_ADD_CARD_CLICKED = "overage.add_card_clicked"`
3. **Tests:** unit-test User defaults, AuditAction enum membership.

### Phase 2 — Backend: endpoints

1. **Update existing user update endpoint** (`platform/routers/users.py`) — accept `show_overage_notification` in the update payload (already audit-logged via existing flow).
2. **New endpoint:** `POST /users/me/overage-event` with body `{ "type": "acknowledged" | "add_card_clicked" }`.
   - For `"acknowledged"`: idempotent — if `User.overage_acknowledged_at` is set, no-op (still 200, no new audit log). Else atomic `find_one_and_update` with guard, then `create_audit_log()` with `OVERAGE_ACKNOWLEDGED`.
   - For `"add_card_clicked"`: always emit the `OVERAGE_ADD_CARD_CLICKED` audit log (no dedupe — natural card-state gate). **Additionally**, if `User.overage_acknowledged_at` is not yet set, stamp it now — clicking Add Card is an implicit acknowledgment, so the user shouldn't get a separate acknowledgment audit log later. This stamp does **not** itself emit an `OVERAGE_ACKNOWLEDGED` audit entry (the Add Card entry already records the user's response).
   - Metadata: include current overage state (which resource, used/included) to make the row useful even though we don't gate on resource type.
3. **Tests:** acknowledgment idempotency (second call doesn't double-log), add_card always logs, add_card stamps `overage_acknowledged_at` if unset, add_card does NOT re-stamp `overage_acknowledged_at` if already set, auth required.

### Phase 3 — Frontend: shared dialog + helpers

1. **New component:** `portal/src/components/billing/OverageWarningDialog.tsx`
   - Props: `open`, `hasPaymentMethod`, `showPrefDefault`, `onConfirm(showNextTime: boolean)`, `onAddCard()`, `onCancel()`.
   - Card-on-file variant: friendly message + "Show this next time" checkbox (pre-checked from pref) + Cancel / OK.
   - No-card variant: merged friendly + add-card message + Cancel / Add Card. No prefs checkbox.
2. **New helper:** `portal/src/hooks/useOverageGate.ts` (or a plain function in `src/utils/overage.ts`)
   - Takes the resource ("user" | "estimate" | "maple_credit"), the subscription state, the current user prefs.
   - Returns `{ shouldPrompt, hasPaymentMethod }`.
   - Encapsulates the "card on file + pref OFF → skip" rule.
3. **New API client functions:**
   - `recordOverageAcknowledged()` / `recordOverageAddCardClicked()` in `portal/src/api/billing.ts` (or `users.ts`).
   - `updateAccountPreferences({ show_overage_notification })` — likely extend the existing account-save call.
4. **Tests:** dialog renders correct variant, fires correct callbacks, pref toggle in dialog reflects to `onConfirm`.

### Phase 4 — Frontend: wire into call sites

For each call site below: compute overage state from subscription data, call `useOverageGate`, render `OverageWarningDialog` when `shouldPrompt`, and only proceed with the action on confirm. On OK click, fire `recordOverageAcknowledged` and (if pref toggled) save updated pref. On Add Card click, fire `recordOverageAddCardClicked` then open the existing Stripe card flow.

1. **Estimates create — list page** (`portal/src/pages/EstimatesPage.tsx:113-208`): replace existing `isAtPlanLimitWithoutCard()` gate with the new gate. Also covers the duplicate-estimate path.
2. **Estimates create — activity page** (`portal/src/pages/NewEstimateWithActivityPage.tsx:302-307`).
3. **User invitation** (`portal/src/pages/SettingsPage.tsx:1047-1060`): replace the existing "paid seat" modal with the new dialog (the modal at lines 2552-2586 can be deleted).
4. **Maple Credits — out of scope for this pass.** Dialog + gate helper accept `"maple_credit"` as a resource so the wiring slot exists, but no call sites are wired now. To be done when a non-Maple-panel credit-consuming surface ships.
5. **Maple panel:** explicit no-op. The orchestrator chat in `PortalLayout.tsx` does **not** call the gate; backend 402 path keeps current behavior for no-card credit exhaustion.

### Phase 5 — Frontend: Account page checkbox

1. **Account tab in `SettingsPage.tsx` (lines 1228-1355):** add "Show overage notification" checkbox under the existing name/email/phone block, default checked, wired into the existing edit/save form pattern (NOT live onChange — this form has explicit Save).
2. **Tests:** checkbox renders, default state honors `User.show_overage_notification`, save round-trip updates the user.

## Files I'll touch

**Backend (platform/):**
- `models/user.py` — new fields
- `models/audit_log.py` — new enum values
- `routers/users.py` — accept new field; new `/users/me/overage-event` endpoint
- `tests/test_users_api.py` (or equivalent) — endpoint + idempotency tests

**Frontend (portal/):**
- `src/components/billing/OverageWarningDialog.tsx` — new
- `src/utils/overage.ts` (or `src/hooks/useOverageGate.ts`) — new
- `src/api/billing.ts` and/or `src/api/users.ts` — new functions
- `src/pages/EstimatesPage.tsx` — replace gate
- `src/pages/NewEstimateWithActivityPage.tsx` — replace gate
- `src/pages/SettingsPage.tsx` — replace seat modal; add Account checkbox
- Any AI-credit-consuming page outside Maple panel — TBD during Phase 4 audit
- Corresponding test files

## Open / deferred

- **Audit log "once per user" is global, not per resource** — confirmed. So once a user OK's any overage warning, no subsequent OKs are audit-logged even if they later overage on a different resource. The dialog still **shows** every time (per option c).
- **No analytics event** is part of scope. If product wants funnel data later, add a separate event emitter without coupling to audit log.
- **Changelog entry:** not adding per project policy — user triggers changelog entries explicitly.

## Risks

- **Maple panel boundary** is purely a frontend convention. If a future code path consumes Maple credits from the Maple panel via a non-Maple-panel-aware helper, it might trigger the dialog. Mitigate by routing all Maple-panel-originated agent calls through a single function that skips the gate.
- **Idempotency under race** — two parallel OK clicks. The `POST /users/me/overage-event` endpoint must use an atomic `find_one_and_update` with `$exists: false` guard on the timestamp, not a read-then-write, to avoid double-logging.
- **Existing `AddPaymentMethodModal` flows** (estimate duplication 402 catch, activity-page 402 catch) — these still need to keep working as a **server-driven fallback** if a request slips past the frontend gate (e.g., concurrent overage from another tab). Don't delete them.
