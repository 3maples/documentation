# Backoffice Overrides

Operational runbook for backoffice-only flags that are set **directly in
MongoDB** — never via the API or UI. These are levers a human at 3Maples pulls
to onboard beta customers or handle special cases.

> ⚠️ These flags bypass normal billing safeguards. Always run the `find` query
> first to confirm you're editing the right company before any write.

---

## `overage_billing_disabled` — unlimited beta accounts

**Collection:** `companies`
**Field:** `overage_billing_disabled` (boolean, defaults to `false`)
**Defined in:** `platform/models/company.py`

Set `true` when a beta customer is brought on to test the app and should not be
billed for any overage. The flag name is **never exposed to the client** — the
subscription endpoint serializes the included limits as `null`, which the UI
renders as ∞, indistinguishable from a normal unlimited plan.

### What it changes when `true`

- **Estimates** — unlimited; counter still increments (shown as `N / ∞`), but
  the cap predicate and Stripe metering are skipped.
- **Seats** — unlimited; no seat-overage prompts.
- **Maple credits (tokens)** — unlimited; no payment-method / acknowledgment
  prompts, no per-token Stripe metering.
- **UI** — all limits render as ∞; overage popups and overage copy suppressed.
- **Stripe** — no overage usage is reported for this company.

### What it does NOT change

- The `MAPLE_TOKEN_HARD_CAP` runaway-cost safety in
  `platform/services/llm/quota.py` still fires. The override is deliberately
  checked **after** the hard cap, so a runaway loop or malicious automation is
  still stopped.

### Step 1 — Find the company (confirm before writing)

```js
db.companies.find({}, { name: 1, plan_lookup_key: 1, overage_billing_disabled: 1 })
```

### Step 2 — Enable the override

By name:

```js
db.companies.updateOne(
  { name: "Acme Landscaping" },
  { $set: { overage_billing_disabled: true } }
)
```

By `_id`:

```js
db.companies.updateOne(
  { _id: ObjectId("507f1f77bcf86cd799439011") },
  { $set: { overage_billing_disabled: true } }
)
```

### Step 3 — Revert (back to normal metered billing)

```js
db.companies.updateOne(
  { name: "Acme Landscaping" },
  { $set: { overage_billing_disabled: false } }
)
```

### From the MongoDB UI (Compass / Atlas Data Explorer)

Prefer the UI? You find the document with a filter, then edit the field inline
— no `updateOne` needed.

1. **Find the company.** Open the `companies` collection and paste into the
   **filter** bar:

   ```js
   { name: "Acme Landscaping" }
   ```

   By `_id` (the `ObjectId(...)` wrapper is required):

   ```js
   { _id: ObjectId("507f1f77bcf86cd799439011") }
   ```

   Optional — limit the columns shown via Options ▸ **Project**:

   ```js
   { name: 1, plan_lookup_key: 1, overage_billing_disabled: 1 }
   ```

2. **Edit the document.** Hover the returned document → click the **pencil
   (Edit)** icon, then:
   - If `overage_billing_disabled` is present, toggle its value `false` → `true`.
   - If it's **missing** (companies created before the field existed), click `+`
     to add a field — name `overage_billing_disabled`, type `Boolean`,
     value `true`.

3. Click **Update** to commit. Revert is the same flow, setting it back to
   `false`.

You can also use Compass's embedded `mongosh` shell at the bottom of the
window — the shell commands above work there verbatim.

> Inline edit only works on a document the filter actually returned. If the
> filter comes back empty, check the `name` spelling (case- and
> whitespace-sensitive) or use the `_id` filter instead.

### Notes

- The change takes effect on the company's next request — no restart or cache
  bust needed (the flag is read fresh from the `Company` document each time).
- If the company already accrued overage in Stripe before the flag was set,
  this flag does not retroactively credit it — handle any existing Stripe
  usage separately.
