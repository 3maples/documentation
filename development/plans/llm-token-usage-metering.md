# LLM Token Usage Tracking + Stripe Metering

## Context

Today, only the Estimate agent partially captures LLM token counts (in-memory via `TokenUsageAccumulator` in `platform/agents/estimate/service.py:62-91`) and the data is logged to stdout but never persisted. The other 7 agents (Orchestrator, Property, Contact, Material, Labour, Equipment, Maple Guide) capture nothing — 28 LLM call sites in total go unmetered.

We want LLM tokens to become a usage-based billing dimension alongside the existing estimate-count and seat-count meters:

- Capture `prompt_tokens + completion_tokens` for **every** LLM call.
- Attribute each call to the user who triggered it and to that user's company.
- Roll up to a per-company counter that resets at the start of each billing period.
- Report usage to a new Stripe meter (`tokens_used`) so overage flows through normal invoices.
- Plans include a base allocation; overage is billed at $5 / 100,000 tokens ($0.00005/token) via Stripe graduated tiers.
- When a company exhausts included tokens and has no card on file, return **HTTP 402 `needs_payment_method`** (same pattern as estimate quota).
- Surface a usage progress bar on the Billing tab.

User-confirmed design choices:
1. **Metered overage** (no pre-paid bundles).
2. **Combined sum** of prompt + completion tokens is what we meter and display.
3. **Hard 402 block** when over quota with no payment method.
4. **Company-total UI only** for v1 (per-user data persisted but not yet shown).

---

## Architecture summary

```
LLM call sites (28)
       │
       ▼
create_chat_model() factory  ──── per-call callback ────►  TokenTrackingCallback
  (services/llm/factory.py)        (passed via                      │
                                   config={"callbacks":[...]})      │
                                                                    ▼
                                                         record_llm_usage()
                                                         (services/llm/usage.py)
                                                            │       │
                                                            ▼       ▼
                                                  LLMUsageEvent  Company.atomic
                                                   (audit log)   $inc counters
                                                            │
                                                            ▼
                                                Stripe MeterEvent
                                              (services/billing/meter_events.py
                                                report_tokens_used)
```

Three layers:

1. **Capture layer** — a thin LangChain `BaseCallbackHandler` reads `response.llm_output["token_usage"]` (and `usage_metadata` fallback) on `on_llm_end`, then hands the counts to a recorder. The callback is attached **per `ainvoke`**, not per agent, so the existing singleton agents stay singletons.
2. **Persistence layer** — `record_llm_usage()` does two things atomically: insert one `LLMUsageEvent` doc (audit log, per-user attribution) and `$inc` on `Company.tokens_used_this_period` + `User.tokens_used_this_period`.
3. **Metering layer** — after persistence, fire-and-forget `report_tokens_used()` to Stripe with a stable idempotency key. Failures are swallowed and logged, matching the existing `report_estimate_created()` / `report_seat_count()` pattern in `platform/services/billing/meter_events.py`.

---

## Data model changes

### New: `models/llm_usage_event.py`

Per-call audit log. One doc per LLM invocation. Indexed by `(company, created_at)` and `(user, created_at)` for billing-period rollups.

```python
class LLMUsageEvent(Document):
    company: PydanticObjectId
    user: Optional[PydanticObjectId]      # nullable for cron/system calls
    feature: str                          # "estimate.architect" | "orchestrator.classify" | "property.extract" | ...
    model: str                            # "gpt-5.4-mini" etc.
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int                     # denormalized = prompt+completion
    cost_usd: Optional[Decimal]           # computed via MODEL_PRICING; null if model unknown
    stripe_meter_event_id: Optional[str]  # idempotency key we sent to Stripe
    stripe_reported_at: Optional[datetime]
    created_at: datetime

    class Settings:
        name = "llm_usage_events"
        indexes = [
            [("company", 1), ("created_at", -1)],
            [("user", 1), ("created_at", -1)],
        ]
```

Register in `platform/database.py:init_db()` alongside the other 17 models.

### Extend: `models/company.py`

Add two fields next to the existing estimate-quota fields:

```python
tokens_used_this_period: int = 0          # resets to 0 on invoice.paid
tokens_period_high_water: int = 0         # for Stripe meter "max" parity (only needed if we ever need replay)
```

`quota_reset_at` already exists and already drives the period reset — no new field needed there.

### Extend: `models/user.py`

```python
tokens_used_this_period: int = 0          # for future per-user UI; reset on company reset
```

### New: `services/llm/model_pricing.py`

Single source of truth for token → USD conversion (used for the `cost_usd` snapshot in `LLMUsageEvent`; not used for billing — Stripe handles that). Default-zero entry for unknown models so we never crash on a new model name:

The three models actually in use are **gpt-5.5** (architect), **gpt-5.4** (researcher), and **gpt-5.4-mini** (worker / help). Update `config.py` defaults to match — `architect_model="gpt-5.5"`, `researcher_model="gpt-5.4"`, `worker_model="gpt-5.4-mini"`, `maple_help_model="gpt-5.4-mini"`.

```python
MODEL_PRICING_PER_1K = {
    "gpt-5.5":      {"input": Decimal("0.000"), "output": Decimal("0.000")},
    "gpt-5.4":      {"input": Decimal("0.000"), "output": Decimal("0.000")},
    "gpt-5.4-mini": {"input": Decimal("0.000"), "output": Decimal("0.000")},
}
```

(Numbers left as placeholders — user fills in real ones at config time. `cost_usd` on `LLMUsageEvent` is informational only; billing flows through Stripe metering, not this table.)

### Extend: `services/billing/plan_config.py`

Add `included_tokens` and `token_overage_lookup_key` fields to `PlanSpec`:

| Plan | Included tokens | Overage rate |
|---|---|---|
| `plan_free` | 250,000 | $0.05 / 1k |
| `plan_base` | 10,000,000 | $0.05 / 1k |
| `plan_pro` | 10,000,000 | $0.05 / 1k |

---

## Backend implementation

### 1. Centralized chat-model factory — `services/llm/factory.py` (NEW)

Replaces every direct `ChatOpenAI(model=...)` instantiation. Each agent calls `create_chat_model("architect")` or `create_chat_model("worker")` and receives a configured `ChatOpenAI`. Critically, the factory does **not** bake the callback in — agents attach the callback per-invoke so they can pass per-call attribution:

```python
def create_chat_model(role: Literal["architect","researcher","worker","help"], **kwargs) -> ChatOpenAI:
    model_name = {
        "architect":  settings.architect_model,
        "researcher": settings.researcher_model,
        "worker":     settings.worker_model,
        "help":       settings.maple_help_model,
    }[role]
    return ChatOpenAI(model=model_name, **kwargs)
```

Each `ainvoke` call site changes from:

```python
await self.llm.ainvoke(messages)
```

to:

```python
await self.llm.ainvoke(
    messages,
    config={"callbacks": [TokenTrackingCallback(
        company_id=company_id, user_id=user_id, feature="estimate.architect",
    )]},
)
```

The 28 call sites get a small mechanical edit each. To minimize churn, every agent's `process()` already receives company and (in most paths) user identity — we just thread `user_id` to the helper that builds the callback config.

### 2. `services/llm/callback.py` (NEW) — `TokenTrackingCallback`

```python
class TokenTrackingCallback(AsyncCallbackHandler):
    def __init__(self, *, company_id, user_id, feature):
        self.company_id, self.user_id, self.feature = company_id, user_id, feature

    async def on_llm_end(self, response: LLMResult, **kwargs):
        usage = _extract_token_usage(response)   # handles both .llm_output["token_usage"] and .usage_metadata
        if not usage:
            return
        await record_llm_usage(
            company_id=self.company_id, user_id=self.user_id, feature=self.feature,
            model=_extract_model_name(response),
            prompt_tokens=usage["prompt_tokens"], completion_tokens=usage["completion_tokens"],
        )
```

`_extract_token_usage` covers both shapes that `langchain-openai>=0.2.0` emits, with a `0/0` fallback so a metadata-stripped response never breaks the request.

### 3. `services/llm/usage.py` (NEW) — `record_llm_usage()`

```python
async def record_llm_usage(*, company_id, user_id, feature, model, prompt_tokens, completion_tokens):
    total = prompt_tokens + completion_tokens
    cost = _compute_cost(model, prompt_tokens, completion_tokens)  # nullable
    event = LLMUsageEvent(
        company=company_id, user=user_id, feature=feature, model=model,
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        total_tokens=total, cost_usd=cost,
        stripe_meter_event_id=None, stripe_reported_at=None,
        request_id=current_request_id(), created_at=datetime.utcnow(),
    )
    await event.insert()

    # Atomic increments — never read-then-write
    await Company.find_one(Company.id == company_id).inc({Company.tokens_used_this_period: total})
    if user_id:
        await User.find_one(User.id == user_id).inc({User.tokens_used_this_period: total})

    # Fire-and-forget Stripe meter post (does not block the LLM response path)
    asyncio.create_task(_report_to_stripe(event))
```

`_report_to_stripe` calls a new helper in `services/billing/meter_events.py` (next section) and updates the event doc with `stripe_meter_event_id` + `stripe_reported_at` on success.

### 4. `services/billing/meter_events.py` — extend with `report_tokens_used()`

Mirrors the existing `report_estimate_created()` shape:

```python
async def report_tokens_used(*, stripe_customer_id: str, tokens: int, event_id: str):
    if not settings.billing_meter_enabled or not stripe_customer_id or tokens <= 0:
        return None
    identifier = f"tok:{event_id}"   # event_id is the LLMUsageEvent _id; guarantees idempotency on retry
    payload = {"stripe_customer_id": stripe_customer_id, "value": str(tokens)}
    return await asyncio.to_thread(
        stripe.billing.MeterEvent.create,
        event_name="tokens_used",
        payload=payload,
        identifier=identifier,
    )
```

Failures are caught + logged + swallowed (matches `report_estimate_created`). The `LLMUsageEvent` row is the durable record — if Stripe is down, a daily reconciliation job (deferred, out of scope for v1) can replay events whose `stripe_reported_at IS NULL`.

### 5. Quota gate — `services/llm/quota.py` (NEW) + dependency

A FastAPI dependency `assert_token_quota(company)` runs on every router that triggers an LLM call:

```python
async def assert_token_quota(company: Company):
    plan = get_plan_spec(company.plan_lookup_key)
    if company.tokens_used_this_period < plan.included_tokens:
        return                                      # within quota
    if company.default_payment_method_last4:
        return                                      # over quota but card on file → overage
    raise HTTPException(
        status_code=402,
        detail={"code": "needs_payment_method", "resource": "tokens"},
    )
```

Mount on the LLM-bearing endpoints in `routers/agents.py` (`/agents/orchestrate`, `/agents/estimate`) and any future LLM-using endpoints. The check is at-request-start, so a single big request can still tip over the limit — deliberate, matches existing estimate-quota behavior.

### 6. Cycle reset

Already wired: `webhook_handlers.py` resets `Company.number_of_estimates_created = 0` on `invoice.paid`. Extend the same handler to also zero `Company.tokens_used_this_period`, `Company.tokens_period_high_water`, and `User.tokens_used_this_period` for every user in the company. One-line MongoDB `update_many`. Existing test for the handler gets one extra assertion.

### 7. Stripe seed — `scripts/seed_stripe_products.py`

Add to the existing seeder:
- One `stripe.billing.Meter.create()` call for `event_name="tokens_used"`, aggregation `sum`, `customer_mapping.event_payload_key="stripe_customer_id"`, `value_settings.event_payload_key="value"`.
- One metered `Price` per plan with `usage_type="metered"`, `tiers_mode="graduated"`, tier 0 = `up_to=<included_tokens>` flat $0, tier 1 = `up_to=inf` at `unit_amount=0.05` per 1000 tokens. Lookup keys: `plan_<name>_token_overage`.
- Wire each plan's subscription creation in `services/billing/stripe_client.py` to attach the new metered price as an additional subscription item.

---

## Frontend (Portal)

### `portal/src/components/settings/BillingTab.tsx`

Add a second progress bar block beneath the existing "Estimates this period" block. Reuse the same `<UsageBar />` styling so the two stack consistently. New copy: "Tokens this period — `{used.toLocaleString()} / {included.toLocaleString()}`". Show overage warning (already pattern-matched in the file) when `used > included`.

### `portal/src/api/billing.ts`

Extend the `getSubscription()` response type with:

```ts
tokens: {
  used: number;
  included: number;
  overage: number;          // max(used - included, 0)
}
```

The backend's `GET /billing/subscription/{company_id}` (in `routers/billing.py`) populates this from `company.tokens_used_this_period` + `plan_spec.included_tokens`. No new endpoint needed.

---

## Files to modify

**New:**
- `platform/models/llm_usage_event.py`
- `platform/services/llm/__init__.py`
- `platform/services/llm/factory.py`
- `platform/services/llm/callback.py`
- `platform/services/llm/usage.py`
- `platform/services/llm/quota.py`
- `platform/services/llm/model_pricing.py`
- `platform/tests/test_llm_usage_tracking.py`
- `platform/tests/test_token_quota_gate.py`

**Modified:**
- `platform/models/company.py` — two new fields
- `platform/models/user.py` — one new field
- `platform/database.py:init_db()` — register `LLMUsageEvent`
- `platform/services/billing/plan_config.py` — `included_tokens`, `token_overage_lookup_key`
- `platform/services/billing/meter_events.py` — `report_tokens_used()`
- `platform/services/billing/webhook_handlers.py` — extend `invoice.paid` reset
- `platform/scripts/seed_stripe_products.py` — meter + metered prices
- `platform/routers/agents.py` — mount `assert_token_quota` dependency
- `platform/routers/billing.py` — add tokens block to `GET /billing/subscription`
- `platform/agents/estimate/service.py` — switch to factory; attach callback per `ainvoke`. **Mark `TokenUsageAccumulator` and its stdout logging as deprecated** with a `# DEPRECATED:` banner comment + removal note pointing at the new `record_llm_usage` flow. Leave it functioning for now; remove in a follow-up once the new path is verified in production for one full billing cycle.
- `platform/agents/orchestrator/service.py` — factory + callback (1 site)
- `platform/agents/{property,contact,material,labour,equipment}/service.py` — factory + callback (3 sites each)
- `platform/agents/maple_guide/service.py` — factory + callback (1 site)
- `portal/src/components/settings/BillingTab.tsx` — second progress bar
- `portal/src/api/billing.ts` — type extension

---

## Reused existing utilities

- `services/billing/meter_events.py` pattern (`report_estimate_created`, `report_seat_count`) — copy for `report_tokens_used`.
- `services/billing/stripe_client.py` — already pinned to API `2026-04-22.dahlia` and exposes a configured SDK; nothing new to add for the SDK itself.
- `services/billing/webhook_handlers.py` — existing `invoice.paid` handler resets the estimate counter; extend, don't duplicate.
- `Company.quota_reset_at` and `current_period_start/end` — already populated on subscription updates; reuse.
- `assert_company_access` / `require_authenticated_user` (`platform/dependencies.py`) — already give every router a typed `current_user` with `.company`.
- `BillingEvent` model — already provides idempotent webhook audit; we mirror its idempotency-key shape (`tok:{event_id}`) for meter posts.
- The estimate agent's `TokenUsageAccumulator` (`platform/agents/estimate/service.py:62`) — **deprecated, scheduled for removal.** The callback-based flow is now the source of truth for token data. We keep the accumulator wired up only so the existing HTTP response shape doesn't change underneath any clients in this release; it gets a `# DEPRECATED:` banner and is deleted in a follow-up PR once the new path has run cleanly through one billing cycle.

---

## Verification

**Backend unit tests (TDD-first):**
1. `test_llm_usage_tracking.py`
   - `TokenTrackingCallback.on_llm_end` parses both `llm_output["token_usage"]` and `usage_metadata` shapes.
   - `record_llm_usage` writes one `LLMUsageEvent`, `$inc`s Company and User counters atomically.
   - When `user_id` is None, only Company increments.
   - Cost computation uses `MODEL_PRICING_PER_1K`; unknown model → `cost_usd=None`, no exception.
2. `test_token_quota_gate.py`
   - Under quota → request passes.
   - Over quota + card on file → request passes (overage will bill).
   - Over quota + no card → 402 with `code: "needs_payment_method"`, `resource: "tokens"`.
3. Extend `test_billing_meter_events.py` — `report_tokens_used` passes the right `event_name`, `value` (string), and `identifier`; swallows API errors; skipped when meter disabled.
4. Extend `test_billing_webhook_handlers.py` — `invoice.paid` zeroes `tokens_used_this_period` for the company and all its users.
5. Extend `test_agents_api.py` — orchestrate endpoint produces an `LLMUsageEvent` row with the requesting user's id and the correct feature tag.

**Frontend test:**
- `portal/src/components/settings/BillingTab.test.tsx` — token bar renders included/used; overage warning appears when used > included.

**Manual end-to-end:**
1. Run `./run_tests.sh tests/test_llm_usage_tracking.py tests/test_token_quota_gate.py tests/test_billing_meter_events.py tests/test_billing_webhook_handlers.py`.
2. With `BILLING_METER_ENABLED=true` against Stripe test mode: trigger one orchestrate request, then `stripe meter-events list --event-name tokens_used` — confirm one event with the right customer + value.
3. Visit Settings → Billing in the portal — verify both the estimates bar and the new tokens bar render with live values.
4. Force quota with a Free-plan company that has no card → expect 402 with `needs_payment_method` and a friendly portal toast.

**Out of scope for v1 (call out so we don't forget):**
- Per-user breakdown table in the UI (data is already captured; only the view is deferred).
- Replay job for `LLMUsageEvent.stripe_reported_at IS NULL` rows.
- Pre-paid token bundles.
- Per-feature pricing tiers (we may want different rates for `architect` vs `worker` later — schema already supports it via the `feature` column).

---

## Follow-ups

LOW-severity items from `/code-review` are tracked in
[`code-review-followups.md`](../code-review-followups.md) under the
"2026-05-10 `/code-review` pass" section (#251–#254).
