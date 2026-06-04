# Code Review Follow-ups

Follow-up tracker for HIGH and MEDIUM issues surfaced by `/code-review`.
Originally captured on 2026-04-19 after the 18 CRITICAL findings from that
pass were fixed; refreshed 2026-04-20 with new findings from the
material-categories change.

Treat this list as a punch-list, not a sprint plan. Pick what's valuable when
touching the affected area. Items are ordered by impact within each severity.

---

## HIGH

### 3. [HIGH] ~~mypy baseline — themed gaps (271 errors across 38 files)~~ — RESOLVED 2026-05-22
**Closed as resolved 2026-05-22.** mypy now reports **`Success: no issues found in 265 source files`** on the full project. From 271 errors at the original 2026-04-26 baseline → 0 errors across 265 files. All themed sub-entries (#86 union-attr, #87 boundary arg-type, #88 implicit-Optional, #89 resource-narrowing arg-type, #90 Optional[int] arithmetic, #91 ChatOpenAI signature, #92 call-arg, #93 BlockingPortal, #124 / #183 / #256 misc) are closed. Pre-fix CI gate is now viable; suggested follow-up tracked separately if a CI step is desired.

Final session (2026-05-22) cleared the residual 77 errors via:
- `routers/materials.py` (10) — `assert` narrowings on `find_one().id` / `insert().id`, explicit `Dict[str, Any]` annotations, renamed shadowed `existing` variable.
- `routers/agents.py` (7) — `Dict[str, Any]` annotation on `detail`; `set_llm_context` widened to accept `Optional[PydanticObjectId]` with internal `None` short-circuit (more honest about the `User.company` model); replaced `[{"description": ...}]` dict literals with explicit `JobItemCreate(description=...)`; guarded `release_estimate_slot(company_doc)` calls with `if company_doc is not None`.
- `services/audit_service.py` (6) — `sanitized: Dict[str, Any]` and `changes: Dict[str, Dict[str, Any]]` annotations.
- `routers/billing.py` (6) — `assert company.id is not None` at all 6 `assert_company_access(decoded_token, company.id)` sites (replace_all on the canonical line).
- `routers/estimate_helpers/ai_generation.py` (4) — return-type annotations tightened from `Optional[Tuple[…]]` to `Tuple[…]` (functions actually never return None); `assert company_obj_id is not None` after the `if not company: raise` guard.
- `routers/auth.py` (4) — `# type: ignore[arg-type]` on the `float(value: object)` cast (TypeError caught below for non-floatable), `# type: ignore[operator]` on Beanie unary-minus sort, `results: List[Dict[str, Any]]` annotation.
- `user_guides/content.py` (3) — bind `guide.get("tips")` / `.get("notes")` / `.get("related_topics")` to locals before the truthy check.
- `routers/audit_logs.py` (3) — two `# type: ignore[operator]` on Beanie sort idioms, `Optional[PydanticObjectId]` annotation for the user-fallback branch.
- `scripts/setup_stripe_webhook.py` (3) — `cast(Any, ...)` on `enabled_events` / `api_version` to bypass Stripe SDK Literal stubs.
- `routers/companies.py` (2), `routers/properties.py` (2), `routers/change_logs.py` (1), `services/brevo_email.py` (2), `services/company_service.py` (1), `services/google_drive_service.py` (2), `services/trello_service.py` (2), `services/estimate_doc_generator.py` (1), `routers/agent_helpers/estimate_update.py` (1), `routers/estimate_helpers/job_item_builders.py` (1), `agents/contact/service.py` (3), `agents/material/service.py` (2), `firebase_auth.py` (2), `config.py` (2), `scripts/db/backfill_divisions.py` (1), `scripts/seed_stripe_products.py` (2), `tests/test_billing_plan_config.py` (1), `tests/test_estimate_agent.py` (1), `tests/test_maple_crud_coverage.py` (1), `scratch/test_owner_leave.py` (1) — same playbook variations (assert narrowing, dict[str, Any] annotation, type: ignore on third-party Literal/operator stubs).

Verified: 245 tests pass across `test_material_api.py`, `test_audit_service.py`, `test_billing_*`, `test_orchestrator_endpoint.py`, `test_estimate_agent.py`, `test_recurrence_model.py` (most likely-affected test surface).

<details>
<summary>Original body (preserved for history)</summary>

### 3. [HIGH] mypy baseline — themed gaps (271 errors across 38 files)
Generated 2026-04-26 via `mypy . --ignore-missing-imports --explicit-package-bases`
after fixing the 7 implicit-Optional `http_request: Request = None` router
sites (the only mechanically safe category — `Optional[Request]` breaks
FastAPI's request injection, so the kept-default + `# type: ignore[assignment]`
form is the canonical fix). Remaining errors split into the themed entries
below; see [#86](#86-mypy-no_implicit_optional-defaults-on-agentestimateservicepy)
through [#90](#90-models-estimate-arithmetic-on-optional-int-fields) for
specific scopes.

Pre-fix CI gate is **not** recommended yet — too many false positives from
LangChain/Beanie type erasure. The right next move is one of:
- enable `mypy --strict` only on `services/` (the smallest, most type-clean
  package), or
- add a `mypy.ini` with the noisy categories disabled (e.g. `disable_error_code = union-attr,arg-type` while the agents are refactored).

Categories below are sorted by error count.

Specific instances:
- #84 — `_coerce_company_oid` returns `Optional[Any]` to keep beanie lazy-import.
- #86 — `union-attr` on `dict.get(...)` chains across agent services (92 errors).
- #87 — `arg-type` on `PydanticObjectId | None` → required at router/service boundaries (~25 errors).
- #88 — `assignment` implicit-Optional defaults across agents / prompts (~50 errors).
- #89 — `arg-type` on agent services — `Material | None` → `Material` (~30 errors).
- #90 — `models/estimate.py` arithmetic on `Optional[int]` fields (16 errors).
- #91 — `call-arg` on `ChatOpenAI(openai_api_key=...)` signature drift (5 errors).
- #92 — `call-arg` on agent → router calls missing `http_request` (5 errors).
- #93 — `BlockingPortal | None` errors in tests (12 errors).
- #124 — `openai_api_key=` keyword on ChatOpenAI flags mypy in maple_guide / maple_public.
- #183 — `change_logs.py` `.sort()` tuple type mismatch (pre-existing).
- #256 — `detail` lacks an explicit type annotation in the orchestrate credits-gate try/except.

**Absorbed:** #84, #86, #87, #88, #89, #90, #91, #92, #93, #124, #183, #256 — themed mypy gaps surfaced in later review passes. See `## Closed` for original bodies.

Progress 2026-05-20: cleared all `union-attr` errors from `agents/property/service.py` (15 → 0 in file; total mypy errors 384 → 365 globally — the assert-on-`target_property` added for union-attr coverage also collapsed three `arg-type` errors on `_property_to_dict` calls). Closes the `union-attr` portion of #86 for this file; the `Property | None` → `Property` arg-type slice of #89 also drops 3 errors. Fixes were pure type narrowing via `assert` (LLM guarded by callers, `target_property` guaranteed non-None after `if resolve_error: return`, `active_pending_intent` guaranteed non-None inside `should_fallback_to_pending`) plus tightening two `if active_pending_intent_id and ...` conditions to also check `active_pending_intent is not None`. No real null-deref bugs surfaced — all 15 were narrowing gaps.

Progress 2026-05-20: applied the same playbook to `agents/contact/service.py` (21 → 2 in file; total mypy errors 365 → 346 globally). Cleared 15 `union-attr` + 4 `arg-type` errors via 6 narrowing edits: 2 `assert self.llm is not None` on the `_classify_with_llm` / `_extract_entities_with_llm` paths (callers gate on `self.use_llm and self.llm is not None`), 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_contact is not None` after the `if resolve_error: return` early-bail, and 2 pending-delete conditions tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for contact; the `Contact | None` → `Contact` arg-type slice of #89 also drops 4 errors. Remaining 2 errors in this file (`no-redef` at L1794, `assignment` at L2014) are unrelated — separate categories from #3. Verified with `tests/test_contact_agent.py` + `test_contact_api.py` + `test_contact_model.py` + `test_cross_resource_envelope_contact.py` (99 tests passing).

Progress 2026-05-20: applied the same playbook to `agents/material/service.py` (17 → 4 in file; total mypy errors 346 → 333 globally). Cleared 10 `union-attr` + 3 `arg-type` errors via 5 narrowing edits: 2 `assert self.llm is not None` on `_classify_with_llm` / `_extract_entities_with_llm`, 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_material is not None` after the `if resolve_error: return` early-bail (collapses 3 `arg-type` errors on `_handle_get_material` / `_handle_delete_material` / `_material_to_dict` calls plus 3 `.name`/`.id` union-attrs), and 1 pending-delete condition tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for material; the `Material | None` → `Material` arg-type slice of #89 also drops 3 errors. Remaining 4 errors in this file are out of scope (390: `_parse_cost(Any | None)` arg-type; 1227, 1230: `call-arg` missing `http_request` — part of #92; 1356: `len(Any | list[Any] | None)`). Verified with `tests/test_material_agent.py` + `test_maple_material_size_operations.py` + `test_material_response_envelope.py` (88 tests passing).

Progress 2026-05-20: applied the same playbook to `agents/labour/service.py` (15 → 2 in file; total mypy errors 333 → 320 globally). Cleared 10 `union-attr` + 3 `arg-type` errors via 6 narrowing edits: 2 `assert self.llm is not None` on `_classify_with_llm` / `_extract_entities_with_llm`, 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_labour is not None` after the `if resolve_error: return` early-bail (collapses 3 `arg-type` errors on `_labour_to_dict` calls plus 2 `.id` union-attrs), and 2 pending-delete conditions tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for labour; the `Labour | None` → `Labour` arg-type slice of #89 also drops 3 errors. Remaining 2 errors in this file (721, 724: `call-arg` missing `http_request`) are part of #92. Verified with `tests/test_labour_agent.py` + `test_labour_api.py` (40 tests passing).

Progress 2026-05-20: applied the same playbook to `agents/equipment/service.py` (16 → 3 in file; total mypy errors 320 → 307 globally). Cleared 10 `union-attr` + 3 `arg-type` errors via 6 narrowing edits: 2 `assert self.llm is not None` on `_classify_with_llm` / `_extract_entities_with_llm`, 1 `assert active_pending_intent is not None` inside `should_fallback_to_pending`, 1 `assert target_equipment is not None` after the `if resolve_error: return` early-bail (collapses 3 `arg-type` errors on `_equipment_to_dict` calls plus 2 `.id` union-attrs), and 2 pending-delete conditions tightened with `and active_pending_intent is not None`. Closes the `union-attr` portion of #86 for equipment; the `Equipment | None` → `Equipment` arg-type slice of #89 also drops 3 errors. **All four agent services (property/contact/material/labour/equipment) are now union-attr-clean — the `dict[str, Any] | None` and `<Resource> | None` slices of #86 are closed for this resource cluster.** Remaining 3 errors in this file (574, 586, 589: `call-arg` missing `request`/`http_request`) are part of #92. Verified with `tests/test_equipment_agent.py` + `test_equipment_api.py` (20 tests passing). Cumulative #3 progress this session: 384 → 307 mypy errors (-77 across the four agent services).

Progress 2026-05-20: cleared the remaining 4 errors in `agents/orchestrator/service.py` (4 → 0 in file; total mypy errors 271 → 267 globally on the `mypy agents/ routers/ models/` slice). Three targeted edits: (1) renamed the inner-loop variable `domain` → `hint_match` at line 1269 so the `str | None` return from `_match_first_hint` doesn't clash with the outer `str`-typed `domain` from the `for domain in domain_priority:` loop (cleared the `assignment` error); (2) added `assert self.llm is not None  # Callers gate on self.use_llm and self.llm is not None.` before the `prompt | self.llm.with_structured_output(...)` chain in `_classify_with_llm` (caller at line 1902 already gates on `self.use_llm and self.llm is not None`); (3) annotated `normalized_matches: List[Dict[str, Any]] = [...]` in `_normalize_llm_result` so the downstream `float(match.get("probability") or 0.0)` and `', '.join(match['intent'] for match in delegate_matches)` calls stop tripping `arg-type`/`misc` on the inferred `dict[str, object]`. Verified with `tests/test_orchestrator_intents.py` (185 passing) + `tests/test_orchestrator_bare_entity_helpers.py` + `tests/test_orchestrator_endpoint.py` (94 passing) — 279 total green. Closes the union-attr/arg-type slice of #86 for orchestrator; the file now has zero open mypy errors.

Progress 2026-05-20: closed **#92** (agent → router `call-arg` cluster). Cleared all 7 errors by applying the canonical implicit-Optional pattern (already used by `create_material`, `delete_all_materials`, `create_labour`, etc.) to 7 router sites: `update_material` and `delete_material` in `routers/materials.py`, `update_labour` and `delete_labour` in `routers/labours.py`, and `create_equipment` / `update_equipment` / `delete_equipment` in `routers/equipments.py`. Each was `http_request: Request,` (or `request: Request,` for equipment-create) made into `http_request: Request = None,  # type: ignore[assignment]` — the form documented in #3's preamble as "the only mechanically safe category" (`Optional[Request]` would break FastAPI's request injection). Behavioral check: all three audit-log call sites pass `request=http_request` directly to `create_audit_log`, which already accepts `Optional[Request] = None` (see `services/audit_service.py:101`) — when called via HTTP, FastAPI still injects the real Request; when called directly from an agent service (the path that previously raised `TypeError: missing positional argument`), audit logging still runs but without client_ip / user_agent metadata. Total mypy errors 267 → 260 globally. Verified with `tests/test_material_api.py` + `test_material_agent.py` + `test_labour_api.py` + `test_labour_agent.py` + `test_equipment_api.py` + `test_equipment_agent.py` (125 tests passing). The 2 remaining `call-arg` errors in `config.py:86` are unrelated (Pydantic Settings construction — `mongodb_url` / `openai_api_key` validated at runtime via env vars but not visible to mypy).

Progress 2026-05-20: cleared the 4 residual errors in `agents/property/service.py` (4 → 0 in file; total mypy errors 260 → 256 globally). Three edits: (1) added `assert linked_property is not None  # _resolve_estimate_linked_property guarantees non-None when error_message is None.` before `self._property_to_dict(linked_property)` in the estimate-code cross-resource handler (line ~1171) — the resolver's contract returns `(None, message)` on any failure and `(Property, None)` on success; (2) annotated `pending_record: Dict[str, Any] = {...}` at line 1804 (the `create_property` missing-fields branch) so the subsequent `dict["confirm_delete"] = False` reassignment at line 1967 (in the fuzzy-match `delete_property` branch — both paths share the variable via the outer `process()` scope) doesn't trip the inferred `dict[str, Collection[str]]` from the `"fields": dict[Any, Any]` value; (3) renamed the inner-loop `options = [str, ...]` at line 2167 → `contact_options` to avoid clashing with the outer-scope `options` from `_resolve_target_property`'s tuple unpack at line 1923 (which is `list[dict[str, Any]]`). Verified with `tests/test_property_agent.py` + `test_property_api.py` (57 tests passing). All `union-attr` / `arg-type` / `assignment` / `misc` errors in this file are now closed.

Progress 2026-05-20: cleared 2 errors in `prompts/estimate_react.py` and `prompts/estimate_architect.py` (total mypy errors 256 → 254 globally). Both `build_estimate_*_prompt(industry: str = None)` signatures used the implicit-Optional pattern. Fix: changed to `industry: Optional[str] = None` and added `from typing import Optional` to each file. These are pure-Python helper functions (not FastAPI routes), so the standard `Optional[str]` form is correct — the `# type: ignore[assignment]` shim is only needed for `Request` parameters where FastAPI's dependency injection breaks if the annotation is widened to `Optional[Request]`. No behavior change; both functions already test `if industry:` against falsy.

**This-session running totals**: 384 → 254 mypy errors (-130 across `agents/`, `routers/`, `models/`, `prompts/`). Closed in full: `#92` (call-arg cluster), `union-attr`/`arg-type` slice of `#86`/`#89` for property/contact/material/labour/equipment/orchestrator. Next candidate batches (require user approval — substantial scope): `agents/estimate/*` cluster (133 errors across crud_handlers.py / service.py / work_item_handlers.py / llm_helpers.py / conversation_guide.py / catalog_matching.py — these are mostly `#88` implicit-Optional defaults and `WorkItemHandlersMixin` attr-defined errors from the mixin pattern, not the resolve-error narrowing playbook); `models/estimate.py` arithmetic on Optional[int] fields (13 errors, `#90`); `routers/estimates.py` boundary `PydanticObjectId | None` → required (17 errors, `#87`).

Progress 2026-05-20: cleared the 17 errors in `routers/estimates.py` (17 → 0 in file; total mypy errors 254 → 237 globally). Seven edits: (1) `assert company_obj_id is not None` after `parse_object_id(company, ...)` at the top of `create_estimate` (line 295) — the `if not company: raise` check above guarantees the parse returns a real OID; cascades to clear errors at L296 (`assert_company_access`) and L324 (`get_company_defaults`); (2) `# type: ignore[operator]  # Beanie descriptor unary-minus sort idiom.` on `query.sort(-Estimate.created_at).limit(limit)` at L426 — Beanie's negate-field syntax is correct at runtime but unmodellable in mypy stubs; (3) annotated `update_data: Dict[str, Any] = {}` in `update_estimate` (L801) — was being inferred as `dict[str, str]` from the first `update_data["title"] = payload.title` assignment, breaking subsequent assigns of `description`/`property`/`status`/`job_items`/`grand_total`/`updated_at` (clears 7 errors at L809–1020); (4) `effort_card_items=[EffortCardItem(**ci.model_dump()) for ci in a.effort_card_items]` at L962 — explicit `EffortCardItemCreate → EffortCardItem` conversion via Pydantic constructor instead of relying on auto-coercion of `dict` payloads (mypy can't see Pydantic's runtime coercion); (5–7) four `assert <reload> is not None` after `await Estimate.get(estimate_id)` re-reads following a `.set(...)` mutation — archive (L1207), unarchive (L1285), generate-doc (L1362), delete-doc-version (L1410). Each reload is on the same estimate_id that was just mutated, so a None return would indicate a concurrent delete race or DB outage — `assert` is correct since the route has already authenticated and the prior mutation succeeded. Closes the bulk of `#87` for this file. Tests verified: 107 passing in `tests/test_estimate_api.py` + `test_estimate_docs_api.py` + `test_estimate_quota.py`. 3 pre-existing test-isolation flakes (`test_archive_estimate_as_non_creator_member_fails`, `test_docs_versions_sorted_by_version_desc`, `test_docs_versions_empty`) all pass in isolation and exercise code paths untouched by these edits (403 auth path and GET routes); flagged but not introduced by this change.

Progress 2026-05-21: closed the **`agents/estimate/*` cluster** — the single largest remaining batch flagged in the 2026-05-20 "next candidates" line (133 errors across 6 files in the original estimate; the actual surface was 180 errors across 6 files at the start of this work). Total mypy errors 217 → 77 globally (-140). All 12 source files under `agents/estimate/` now show `Success: no issues found in 12 source files`.

The work split into three patterns matching the file shapes:

1. **Mixin attr-defined cluster (#88-adjacent)** — `crud_handlers.py` (64 errors) and `work_item_handlers.py` (32 errors) were both 100% `attr-defined` from the mixin pattern: methods called via MRO from sibling mixins (`CrudParsingMixin`, `WorkItemHandlersMixin`, etc.) but invisible to mypy at the call site. Fix: added a `if TYPE_CHECKING:` stub block at the top of each mixin class declaring the sibling-resolved methods (`_crud_envelope`, `_resolve_estimate_code`, `_estimate_status_from_text`, `_estimate_summary_payload`, `_load_estimate_for_*`, the work-item handler quintet, etc.). 19 stub declarations in `crud_handlers.py`, 4 in `work_item_handlers.py` — all signatures lifted verbatim from the real implementations in `crud_helpers.py` and `work_item_handlers.py`. The `if TYPE_CHECKING:` guard means zero runtime cost — these stubs only exist during mypy's pass. Also added one `assert code is not None` after `_load_estimate_for_read` in `work_item_handlers.py:_handle_get_work_item` (resolver contract: code is non-None when error is None).

2. **`#88` implicit-Optional defaults in `service.py`** — 23 errors, all `param: X = None` where `X` was non-Optional. Canonical fix: widened each to `Optional[X] = None`. Touched signatures: `_merge_duplicate_line_items` (carry_fields), `_step1_architect` / `_step2_and_3_for_scope` / `_step3_research_single_scope` (industry, tokens), `_run_pipeline` / `_run_react_loop` (company_id, industry, max_iterations, tokens), `_generate_estimate` / `_score_with_inventory_check` (tokens), `process` / `analyze_project` / `answer_question` (company, property, context, estimate_data), `generate_estimate` (job_items). Also propagated the Optional widening down to `_step2_vector_retrieval(company_id)` and the `create_estimate_tools(company_id)` factory in `tools.py`. None of these required runtime guards added — the function bodies already handle the None case.

3. **Inference fixes** — handful of one-off shape issues: (a) split three sites where `payload.get("X") if isinstance(payload.get("X"), list) else []` was tripping `Any | list[Any] | None` (the same `.get()` called twice can't narrow); bound the value to a local first then narrowed (`_base_raw = base.get(...); base_items: List[Any] = _base_raw if isinstance(_base_raw, list) else []`); same pattern applied to three `dict(working_context.get(KEY))` sites; (b) `messages: List[Any] = [SystemMessage(...)]` to allow `HumanMessage` appends (langchain doesn't expose a `BaseMessage` union convenient for the local annotation); (c) `final_summary = str(msg.content)` to coerce langchain's `str | list[str | dict]` content union to a flat string for log use; (d) `context: Dict[str, Any] = {"project_description": ...}` in `generate_estimate` to allow the later `context["job_items"] = job_items` assignment; (e) widened `_score_catalog_match(requested_value: Any, candidate_values: List[Any])` + `_canonicalize_text(text: Any)` + `_find_best_catalog_match(requested_value: Any, ...)` in `catalog_matching.py` — the functions already coerce via `_normalize_catalog_text(value: Any)` so the strict `str` annotations were over-specified; (f) `ESTIMATE_DETAILS: List[Dict[str, Any]] = [...]` in `conversation_guide.py` to stop mypy inferring `object` for the heterogeneous dict values; (g) removed the dead `try/except ImportError → fallback to ()` block in `llm_helpers.py:format_llm_error` — both `openai` and `httpx` are hard deps in `requirements.txt` so the import fallback never fires, and the `if AuthenticationError and isinstance(...)` truthy guards became always-True after the cleanup.

Verified with `tests/test_estimate_agent.py` (112 passing) + `test_estimate_tools.py` + `test_estimate_crud_handler_helpers.py` (137 passing across those + `test_estimate_agent.py` re-run) + recurrence/analytics tests already covered in earlier #90 work. **This-session running totals**: 276 → 77 mypy errors (-199), closing #90, #93, and the `agents/estimate/*` cluster — the three remaining named batches from the 2026-05-20 candidate line are now done.

Progress 2026-05-21: closed **#93** (`BlockingPortal | None` errors in tests). Cleared all 29 errors across 10 test files (note: original entry estimated 12 errors across 5 files; the actual surface grew to 29 sites across 10 files as more API tests adopted the `client.portal.call(...)` pattern). Total mypy errors 263 → 234 globally. Pattern: 17 added `assert client.portal is not None  # TestClient context manager guarantees a portal (mypy hygiene)` calls — one per function/helper that invokes `.portal.call(...)`; mypy's flow analysis narrows the union for the rest of the function scope so a single assert covers multiple `.portal.call` sites in the same function. Files touched: `test_rate_card_bootstrap.py` (5 asserts for 9 sites: 2 helpers + 3 tests), `test_change_logs_api.py` (2: 1 fixture + 1 helper), `test_audit_integration.py` (2: 2 tests), `test_feedback_anonymous.py` (2: 2 tests), and one assert each in `test_template_api.py`, `test_resources_rbac.py`, `test_property_api.py`, `test_divisions_api.py`, `test_feedback_api.py`, `test_company_api.py`. Rejected the alternative "thin `_get_portal()` helper" suggested in the original entry — would have required touching every `.call` site in 10 files plus changes to test function signatures; the per-function `assert` matches the playbook used in earlier #3 progress notes (`assert self.llm is not None`, `assert target_<resource> is not None`) and is the minimum-touch fix. Verified by re-running mypy: 0 BlockingPortal-related errors remain.

Progress 2026-05-21: closed **#90** (`models/estimate.py` arithmetic on `Optional[int]` fields). Cleared all 13 errors in this file (13 → 0; total mypy errors 276 → 263 globally). Two edits in `RecurrenceSchedule`: (1) added `assert month_val is not None` inside the `for month_val in [self.start_month, self.end_month]:` loop in `validate_end_type_fields` — guaranteed non-None by the preceding `if any(v is None ...)` guard inside the `DATE_RANGE` branch; (2) added per-branch `assert <field> is not None` block at the top of each `if/elif` in `calculate_occurrences()` — `end_year`/`start_year`/`end_month`/`start_month` for `DATE_RANGE`, `total_occurrences` for `TOTAL_OCCURRENCES`, `end_year`/`start_year`/`specific_months` for `SPECIFIC_MONTHS`. All asserts reference the `@model_validator(mode="after")` contract that fires on construction (covered by `tests/test_recurrence_model.py` with explicit `pytest.raises(ValidationError)` cases for each branch's required-field shape). Tightening the model declarations to `int = 0` was rejected — the fields are conditionally required *based on `end_type`*, so the Optional typing is correct at the field level; narrowing belongs in the methods. Verified with `tests/test_recurrence_model.py` + `test_estimate_api.py` + `test_estimates_analytics.py` (133 passing). No behavior change.

Progress 2026-05-20: closed the audit-log channel-provenance gap surfaced during the `/code-review` of the `#92` fix. The implicit-Optional widening of `http_request: Request` on 7 router signatures means agent → router calls now succeed silently with `request=None`, dropping `ip_address` / `user_agent` / `method` / `path` from those audit log rows. Without a channel marker, downstream consumers can't distinguish Maple-initiated mutations from a misconfigured Portal request that lost its Request context. **Fix**: added `_audit_source_ctx: ContextVar[Optional[str]]` + `audit_source(source: str)` context manager in `services/audit_service.py`, and modified `create_audit_log` to merge `{"source": ctx_source}` into `metadata` when the var is set (caller-supplied `metadata["source"]` wins). Then wrapped the 7 previously-untagged agent → router callsites with `with audit_source("<resource>_agent"):` — `_update_material_via_api` + `_delete_material_via_api` (material), `_update_labour_via_api` + `_delete_labour_via_api` (labour), and `_create_equipment_via_api` + `_update_equipment_via_api` + `_delete_equipment_via_api` (equipment). The existing `_create_material_via_api` / `_create_labour_via_api` already tagged `metadata={"source": "<resource>_agent"}` directly (they bypass the router) — now the entire CRUD-via-Maple surface is consistently provenance-tagged. **Tests**: added 6 new tests in `tests/test_audit_service.py` — 3 unit tests for the ContextVar (set/reset/nesting/exception-safety), and 3 integration tests that mock the router call and assert the context var resolves to the expected source mid-call (`material_agent` / `labour_agent` / `equipment_agent`). All 132 tests pass across `test_audit_service.py` + `test_material_*` + `test_labour_*` + `test_equipment_*` + `test_audit_integration.py`. Closed independently of `#3` — this was a side-effect of the `#92` resolution, not a pre-existing mypy gap.

</details>

### 4. [HIGH] File and function size
Files over the 800-line HIGH threshold (line counts refreshed 2026-04-26):
- `routers/agents.py` — 1360 lines (2026-05-22 refresh; was 1407
  before the delegate-generic extraction this session, 1642 before the
  delegate-get/update/delete-estimate extractions, 1821 before the
  delegate-create-estimate extraction, 1905 before the estimate-resolver
  extraction, 1977 before the finalize-result extraction, 2203 before
  the estimate-gathering extraction, 2478 before the optional-follow-up
  extraction, 2772 before the pending-estimate-follow-up extraction,
  2917 before 2026-04-26). **53% reduction from the 2026-04-26
  baseline.** Recent extractions landed under `routers/agent_helpers/`:
  - `text_helpers.py` — `is_affirmative_text` / `is_negative_text` (50 lines).
  - `estimate_update.py` — `run_update_estimate` add-items flow (175 lines).
  - `fuzzy_confirmation.py` — `handle_estimate_fuzzy_confirmation` +
    `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY` (180 lines).
  - `pending_estimate_follow_up.py` — landed 2026-05-22 (377 lines).
    Lifted the `_handle_pending_estimate_follow_up` closure (294 lines)
    plus its five property-lookup helpers (`_property_name_of`,
    `_property_address_of`, `_property_label_of`, `_property_full_address_of`,
    `_find_property_by_name_or_address`) out of `orchestrate_agent_endpoint`
    into a module-level helper. Owns `PENDING_ESTIMATE_FOLLOW_UP_KEY` and
    the `ESTIMATE_FOLLOW_UP_STAGE_CONFIRM` / `_SELECT_PROPERTY` constants
    (re-exported from `routers/agents.py` for the existing test imports).
    All 9 return paths now go through a small `_envelope()` helper instead
    of inline 11-key dicts; signature reduced to
    `handle_pending_estimate_follow_up(message, context_payload)`. Tests:
    52 passing in `test_orchestrator_endpoint.py`; `properties_api_get_properties`
    mocks moved from `agents_router` to the helper module via string-form
    `monkeypatch.setattr(...)` (4 sites + 1 contract assertion). The now-dead
    `from routers.properties import fetch_properties as properties_api_get_properties`
    alias was removed from `routers/agents.py`.
  - `optional_follow_up.py` — landed 2026-05-22 (356 lines). Lifted the
    `_handle_pending_optional_follow_up` closure (~195 lines) plus its
    three builders (`_build_optional_follow_up_prompt`,
    `_build_optional_follow_up_update_message`, `_get_optional_follow_up_spec`)
    and the three closure-level constants (`PENDING_OPTIONAL_FOLLOW_UP_KEY`,
    `OPTIONAL_FOLLOW_UP_STAGE_CONFIRM`, `OPTIONAL_FOLLOW_UP_STAGE_COLLECT_VALUE`)
    out of `orchestrate_agent_endpoint`. The closure-level `_get_processor`
    factory (used in 4 sites — only one of which moves into the helper)
    was lifted to module-level in `routers/agents.py` and passed in as a
    `processor_factory: ProcessorFactory` parameter. Five return paths in
    the handler now go through a single `_envelope()` helper. Re-exported
    from `routers/agents.py` so the existing test imports
    (`OPTIONAL_FOLLOW_UP_STAGE_CONFIRM`, etc.) still resolve unchanged.
    Tests: 52 passing in `test_orchestrator_endpoint.py`; no mock-target
    changes needed because no FastAPI-helper aliases were moved.
  - `delegate_generic.py` — landed 2026-05-22 (100 lines). Lifted the
    generic non-Estimate-Agent delegate-and-shape tail (~54 lines) used
    by every agent that isn't routed through one of the Estimate-Agent
    specialized branches (Contact / Property / Labour / Material, plus
    intents Estimate-Agent doesn't claim). Calls
    `processor.process(message, context=...)`, merges the agent-surfaced
    `optional_follow_up` question and stashes a pending follow-up record
    (reusing `get_optional_follow_up_spec` from the existing optional-
    follow-up module), then backfills `completion_ready` /
    `missing_fields` / `accuracy_suggestions` and re-packages as the
    standard 11-key orchestrator envelope. Companion to
    `optional_follow_up.handle_pending_optional_follow_up`, which uses
    the same shape but with slightly different fallback behavior — kept
    separate to avoid parameter explosion. Tests: 52 passing; no mock
    changes needed (`processor.process` is mocked at the agent-instance
    level via `get_<agent>_agent` factory replacements).
  - `delegate_get_estimate.py` — landed 2026-05-22 (145 lines). Lifted
    the `get_estimate` sub-branch (~93 lines) of `_delegate_to_agent`'s
    Estimate Agent block. Pure read path — no Beanie mutations, no
    quota gate, no audit log. The stop-word regex and ObjectId-extraction
    regex moved to module-level constants. Three tests
    (`test_orchestrate_get_estimate_*`) updated with string-form
    `monkeypatch.setattr` on the helper's `estimates_api_get_estimates`.
  - `delegate_estimate_ops.py` — landed 2026-05-22 (226 lines).
    Bundled `delegate_update_estimate` + `delegate_delete_estimate`
    (~82 + ~91 lines of the closure body) since they share the
    `find_estimate_from_context_or_message` resolver, the
    `fuzzy_disclaimer` copy, and the `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY`
    stash record. Closure-only predicates
    (`_should_delegate_update_estimate_to_agent`,
    `_is_work_item_op_message`) are passed in as callables to avoid a
    circular import on `routers/agents.py`. SAFETY GUARDS preserved
    verbatim: update_estimate routes property-link / status-transition
    phrasings straight to the agent BEFORE the fuzzy-resolver; delete
    always requires confirmation regardless of exact vs fuzzy match, and
    refuses the most-recent fallback (destructive callers can't guess).
    All existing delete tests continue to pass via the already-redirected
    resolver mocks from the earlier `estimate_resolver` extraction.
  - `delegate_create_estimate.py` — landed 2026-05-22 (275 lines).
    Lifted the create_estimate sub-branch (~192 lines) of the
    `_delegate_to_agent` closure's Estimate Agent block into a
    module-level helper. Same shape as `estimate_gathering._finalize_gathering`
    — sufficiency check → either enter gathering OR proceed with quota
    gate + estimate generation + audit log + optional follow-up record.
    Closure dependencies passed in: `processor`, `current_user_name`,
    `decoded_token`, and the `_check_estimate_limit_or_refuse` callable
    (latter would be a circular import). Three return paths go through
    a small `_envelope()` helper. Tests: 52 passing; one test
    (`test_orchestrate_endpoint_delegates_to_estimate_agent`) updated to
    also patch `routers.agent_helpers.delegate_create_estimate.prepare_generated_estimate`
    and `save_generated_estimate` via string-form `monkeypatch.setattr`
    (the existing `agents_router` patches stay because the aliases are
    still used in the remaining `_delegate_to_agent` branches).
  - `estimate_resolver.py` — landed 2026-05-22 (119 lines). Lifted the
    `_find_estimate_from_context_or_message` closure (~85 lines) into a
    module-level helper. Resolves the user's target estimate via the
    five-step ladder: active-context → estimate_id code → MongoDB _id
    → fuzzy title match → most-recent fallback. The two regex constants
    are now module-level (`_ESTIMATE_SEARCH_STOP_WORDS`, `_MONGO_OBJECT_ID`).
    Tests: 52 passing; two delete-estimate tests updated to also patch
    `routers.agent_helpers.estimate_resolver.estimates_api_get_estimate{s}`
    via string-form `monkeypatch.setattr` (the existing `agents_router`
    patches stay because the aliases are still used in two other call
    sites inside `_delegate_to_agent`).
  - `finalize_result.py` — landed 2026-05-22 (119 lines). Lifted the
    82-line `_finalize_result` closure body (chat-history append + active-
    entity coreference + suggestions enrichment + conversation persistence)
    into a module-level `finalize_orchestrate_result(...)` helper.
    `_finalize_result` closure remains in `routers/agents.py` as a 9-line
    thin wrapper that calls the helper and wraps the resulting dict in
    `OrchestratorAgentResponse` (the Pydantic response model stays in
    `routers/agents.py` to avoid a circular import). The 5-way entity-key
    scan was extracted into a small `_resolve_entity_reference()`
    private helper inside the new module. All 6 existing call sites are
    untouched — they still call the closure wrapper. Dependencies passed
    in: `delegate_context`, `merged_context`, `user_id`, and the
    `_save_conversation_context` callable. Tests: 52 passing in
    `test_orchestrator_endpoint.py`.
  - `estimate_gathering.py` — landed 2026-05-22 (315 lines). Lifted the
    `_handle_pending_estimate_gathering` closure (236 lines) plus the
    three state-key constants (`ESTIMATE_GATHERING_STATE_KEY`,
    `ESTIMATE_GATHERED_DETAILS_KEY`, `ESTIMATE_NEXT_QUESTION_KEY`) out of
    `orchestrate_agent_endpoint`. The closure captured `message`,
    `decoded_token`, and `current_user_name` from request scope and
    called the module-level `_check_estimate_limit_or_refuse` (a
    circular import if pulled into the helper); these now flow through
    keyword parameters (`decoded_token`, `current_user_name`,
    `estimate_agent`, `check_estimate_limit_or_refuse`). Internal split:
    the per-turn step is the public `handle_pending_estimate_gathering`,
    and the all-details-collected path lives in a private
    `_finalize_gathering` so the main entry stays well under the 50-line
    ceiling. Five return paths go through a single `_envelope()` helper.
    Tests: 75 passing across `test_orchestrator_endpoint.py` +
    `test_estimate_gathering.py`. No mock surgery — no test directly
    exercises the closure-level call path.

  Candidates for the next extraction round:
  - `_finalize_result` and the orchestrate-endpoint epilogue (chat-history
    persistence + suggestion enrichment + response shaping). Still inline
    in `orchestrate_agent_endpoint`.
  - The orchestrate-endpoint's main classification + delegate loop
    (~700 lines after this extraction round). Largest remaining inline
    block in `routers/agents.py`.
- `agents/material/service.py` — 2874 lines (2026-05-22 refresh; was 2875
  pre-extraction this session; doc's earlier "2560" baseline preceded the
  cost/size-guard helpers and accuracy-suggestion code that landed in the
  intervening weeks). `process()` is a mega-switch that inserts a new
  50-line inline handler per intent. ~~Easiest extraction target: the
  `list_material_categories` block~~ landed 2026-04-26 as
  `_handle_list_material_categories()` (44 lines) plus a static
  `_format_material_categories_response()` helper. Follow-up extractions
  landed 2026-04-26: `_handle_create_material`, `_handle_get_material`
  (incl. size-scoped lookup), `_handle_delete_material` (post-resolve
  confirmation flow), and `_handle_list_materials` (count + category-filter
  + name-hint dispatch). `_handle_update_material` landed 2026-05-22:
  the ~246-line inline `update_material` block (multi-turn field-then-value
  state, add-size cost+unit guard, remove-last-size refusal, per-size
  unit-OID resolution, and the final merge/update via
  `_update_material_via_api`) was lifted into a dedicated method that
  reuses `_build_response_envelope` for all 5 return shapes. `process()`
  call site collapses from 246 inline lines to a 14-line kwargs call
  mirroring the `_handle_create_material` / `_handle_delete_material`
  pattern. Verified: 78 tests pass across `test_material_agent.py` +
  `test_material_api.py` + `test_maple_material_size_operations.py`;
  full-project mypy stays at `Success: no issues found in 265 source files`.
  Remaining inline block: the `delete_material` early-confirm shortcut
  that fires before `_resolve_target_material` (small; pre-resolve so it
  can't easily share the post-resolve `_handle_delete_material` signature).

  Pure-helper extraction landed 2026-05-23 in four steps, all into a new `agents/material/text_helpers.py` (375 lines) modeled on `agents/estimate/text_helpers.py`. `agents/material/service.py` dropped from 2,874 → 2,541 lines (**-333, -11.6%**) across the session. Steps:
  - **Step 1**: four leaf-level methods with no `self.*` dependencies (`_is_confirm_text`, `_explicit_intent_from_message`, `_normalize_unit`, `_normalize_size_text`) lifted from instance methods to module-level functions, following the existing pattern set by `_parse_price_range_filter` / `_material_matches_price_filter` / `_format_amount`. 17 callsites rewritten across the file (`self._foo(x)` → `_foo(x)`).
  - **Step 2**: moved Step-1 helpers into a dedicated `agents/material/text_helpers.py` module (76 lines initially).
  - **Step 3**: moved the three pre-existing module-level helpers (`_parse_price_range_filter`, `_material_matches_price_filter`, `_format_amount`) plus the `_PRICE_RANGE_PATTERN` / `_PRICE_RANGE_OP_DIRECTION` constants into `text_helpers.py`. (-75 lines from service.py; 4 internal callsites already module-level so no `self.` rewrites needed.)
  - **Step 4**: moved seven instance methods plus four module-level constants. Methods: `_match_intent_rules`, `_extract_name_from_message`, `_normalize_material_name`, `_parse_cost`, `_has_explicit_cost_field`, `_should_default_cost_to_price`, `_normalize_sizes_field`. Constants: `MATERIAL_ACTION_HINTS`, `NAME_STOPWORDS`, `NAME_LEADING_PREPOSITIONS`, `NAME_TRAILING_NOISE`. 41 `self._foo(x)` → `_foo(x)` callsites rewritten via `replace_all`. (-205 lines from service.py.) All seven methods were transitively pure (chain: `_normalize_sizes_field` uses `_parse_cost` + `_normalize_size_text`; `_extract_name_from_message` uses `_normalize_material_name`; `_has_explicit_cost_field` uses `_parse_cost`); moving them en bloc kept the import dependency one-way (service.py → text_helpers.py).

  The structural win: every helper in `text_helpers.py` is callable and unit-testable without instantiating `MaterialAgent`. Backwards-compat for tests is preserved by the `from agents.material.text_helpers import ...` line at the top of `service.py` — names imported into service.py's namespace are still resolvable via `from agents.material.service import <name>` (used by `tests/test_material_agent.py` for `_material_matches_price_filter` and `_parse_price_range_filter`). Verified: 119 tests pass across `test_material_agent.py` + `test_material_api.py` + `test_maple_material_size_operations.py` + `test_material_response_envelope.py` + `test_audit_service.py`; full-project mypy clean at 275 source files.

  `_handle_update_material` refactor landed 2026-05-23: split 234 → 120 lines (**-49%**) across the orchestration shell, with four new helpers:
  - `_request_update_fields_clarification` (78 lines — bare-field-name selection vs. generic "which fields?" prompt; both terminal)
  - `_check_add_size_guard` (65 lines — refuse add-size when cost or unit missing; returns `Optional[envelope]`)
  - `_check_remove_last_size_refusal` (31 lines — refuse removing the last size; returns `Optional[envelope]`)
  - `_finalize_update_material` (61 lines — merge fields → `_update_material_via_api` → accuracy suggestions → envelope)

  Shell now reads as a linear pipeline: derive state → fields-clarification → add-size guard → remove-size guard → per-size unit-OID resolution → finalize. File-size cost on that single refactor: service.py +121 lines from helper signatures and docstrings — an honest tradeoff where per-function readability wins.

  **`_extract_fields_from_message` and `_build_sizes_from_fields` lifted to `text_helpers.py`** (2026-05-23). Both were pure functions despite being methods — neither used `self.*`. Combined ~278 lines moved out of service.py. Two test callsites updated to use the module-level function (`agent._extract_fields_from_message(...)` → `_extract_fields_from_message(...)` plus an import). text_helpers.py grew to 656 lines (12 pure helpers + 6 constants); service.py dropped from 2,662 → 2,384 (-278).

  **`process()` refactor landed 2026-05-23**: split 457 → **138 lines (-70%)** in two passes via six helper extractions:
  - `_dispatch_intent_to_handler` (147 lines) — the intent-routing mega-switch
  - `_maybe_confirm_pending_delete` (~55 lines) — pending-delete confirmation fast-path
  - `_run_llm_classification` (86 lines) — LLM classify + entity-extraction pipeline; returns ``(parsed, llm_error)``
  - `_apply_post_classify_fallbacks` (~75 lines) — explicit-intent override + name normalization + regex fallback; mutates parsed in place, returns explicit_intent
  - `_apply_pending_intent_fallback` (~66 lines) — pending-intent merge for low-confidence intents; returns `(intent, probability, fields, pending_override_applied)`
  - `_check_pre_dispatch_refusals` (~78 lines) — three pre-dispatch refusal guards (unsupported intent, missing company_id, invalid company_id shape); returns `Optional[envelope]`

  Shell `process()` now reads as a linear pipeline: bulk-delete refusal → context setup → LLM classification → post-classify fallbacks → derive intent/probability/fields → pending-intent fallback → secondary pending-intent merge → pre-dispatch refusals → `_dispatch_intent_to_handler(...)`.

  Session totals for `agents/material/service.py`: **2,874 → 2,568 lines (-306, -10.6%)** across the full session, with `text_helpers.py` at 656 lines (16 pure helpers + 6 constants). The file got bigger than the post-extraction count because each new helper added ~10–15 lines of signature + docstring overhead — function-size is the primary HIGH-issue target so this is a net win even when file-size ticks up. 97 material tests + 22 audit tests pass; full-project mypy clean at 275 source files.

  **`_dispatch_intent_to_handler` refactor landed 2026-05-23**: split 147 → 75 lines (-49%) via one extraction:
  - `_resolve_and_dispatch_target_op` (112 lines) — pending-delete fast-path → `_resolve_target_material` → per-intent handler for the `update_material` / `delete_material` / `get_material` cluster (the only branch that needed target-material resolution). Stashes a pending-update intent on resolve-error and returns the clarification envelope with optional candidate suggestions.

  The dispatcher shell now reads as: `create` branch → `update/delete/get` branch (delegates to `_resolve_and_dispatch_target_op`) → `list_material_categories` branch → fall-through `list_materials`.

  Session totals for `agents/material/service.py`: **2,874 → 2,608 lines (-266, -9.3%)** with `text_helpers.py` at 656 lines (16 pure helpers + 6 constants). Top-N method sizes after this round: `process` (138), `_handle_update_material` (120), `_resolve_and_dispatch_target_op` (112), `_handle_list_materials` (97), `_handle_delete_material` (90), `_run_llm_classification` (86), `_handle_create_material` (85), `_check_pre_dispatch_refusals` (78), `_request_update_fields_clarification` (78), `_handle_list_materials_for_estimate` (76), `_dispatch_intent_to_handler` (75). No method now exceeds 140 lines (was 457 at session start). 97 material tests + 22 audit tests pass; full-project mypy clean at 275 source files.
- `agents/estimate/service.py` — 5685 lines after the 2026-04-26 #80
  refactor. Similar split: prompt-building / inventory fetch / LLM
  extraction / totals calc / CRUD read handlers are each their own concern.
  Cleanest first cut: move the new CRUD methods
  (`_handle_list_estimates`, `_handle_get_estimate`, `_crud_envelope`, plus
  the small parsing helpers) into `agents/estimate/crud.py` as a mixin.
- `agents/labour/service.py` — **1,732 → 1,474 lines (-258, -15%)** across 2026-05-24. Same playbook:
  - **Pure-helper lift to new `agents/labour/text_helpers.py`** (370 lines): 10 leaf-level methods (`_is_confirm_text`, `_match_intent_rules`, `_explicit_intent_from_message`, `_extract_name_from_message`, `_normalize_role_text`, `_parse_cost`, `_normalize_unit`, `_is_bare_rate_reference`, `_match_bare_field_name`, `_extract_fields_from_message`) plus 4 constants (`LABOUR_ACTION_HINTS`, `NAME_STOPWORDS`, `NAME_LEADING_PREPOSITIONS`, `ROLE_TRAILING_NOISE`), class-level `_BARE_FIELD_ALIASES` / `_BARE_RATE_PHRASES`, and the module-level `_format_amount`. Three test sites updated (4 `agent._extract_name_from_message(...)` and 1 `agent._extract_fields_from_message(...)` → module-level + import), plus two `monkeypatch.setattr(LabourAgent, "_extract_*", ...)` rewritten to target the import location.
  - **`process()` dispatch extraction**: lifted the 531-line try-body into `_dispatch_intent_to_handler` (554 lines). `process()` is now **286 lines (-64% from 803 starting point)**.

  40 labour tests pass.

- `agents/equipment/service.py` — **1,343 → 1,151 lines (-192, -14%)** across 2026-05-24. Same playbook:
  - **Pure-helper lift to new `agents/equipment/text_helpers.py`** (284 lines): 8 leaf-level methods (`_is_confirm_text`, `_match_intent_rules`, `_explicit_intent_from_message`, `_extract_name_from_message`, `_normalize_equipment_name`, `_parse_cost`, `_normalize_unit`, `_extract_fields_from_message`) plus 4 constants (`EQUIPMENT_ACTION_HINTS`, `NAME_STOPWORDS`, `NAME_LEADING_PREPOSITIONS`, `NAME_TRAILING_NOISE`) and `_format_amount`. Two test sites updated (1 each of `agent._extract_name_from_message(...)` and `agent._extract_fields_from_message(...)` → module-level).
  - **`process()` dispatch extraction**: lifted the 382-line try-body into `_dispatch_intent_to_handler` (405 lines). `process()` is now **264 lines (-58% from 632 starting point)**.

  20 equipment tests pass.

- `agents/contact/service.py` — **2,412 → 1,928 lines (-484, -20%)** across 2026-05-24. Same playbook as property/material:
  - **Pure-helper lift to new `agents/contact/text_helpers.py`** (593 lines): 17 leaf-level methods moved out of `ContactAgent` as module-level functions, plus 6 constants (`CONTACT_ACTION_HINTS`, `SUPPORTED_CONTACT_ROLES`, `CONTACT_ROLE_ALIASES`, `CONTACT_ENUM_FIELD_OPTIONS`, `_BARE_FIELD_ALIASES`) and the module-level enum-extraction helper (`_extract_contact_enum_field_options`). Migrated helpers: `_is_confirm_text`, `_match_intent_rules`, `_explicit_intent_from_message`, `_extract_name_from_message`, `_split_name_parts`, `_normalize_phone_token`, `_normalize_postal_zip_token`, `_normalize_country_token`, `_normalize_prov_state_token`, `_normalize_role_token`, `_field_name_variants`, `_extract_value_like_phrase`, `_normalize_enum_field_value`, `_detect_enum_help_field`, `_infer_single_missing_field_value`, `_match_bare_field_name`, `_extract_fields_from_message`. Callsites rewritten via `sed`. Three test sites updated: 10 `agent._extract_name_from_message(...)` → module-level, 10 `agent._extract_fields_from_message(...)` → module-level, 7 `agent._normalize_phone_token(...)` → module-level (the test's `agent = ContactAgent(use_llm=False)` line still works but isn't needed), and two `monkeypatch.setattr(ContactAgent, "_extract_*", ...)` rewritten to target the import location in `agents.contact.service`. (Initial deletion was too aggressive — also stripped the 4 module constants `CONTACT_AGENT_LABEL` / `PENDING_INTENTS_CONTEXT_KEY` / `ACTIVE_CONTACT_ID_CONTEXT_KEY` / `ACTIVE_CONTACT_NAME_CONTEXT_KEY`; restored in a follow-up edit.)
  - **`process()` dispatch extraction**: lifted the 641-line try-body dispatch into `_dispatch_intent_to_handler` (665 lines). `process()` is now **407 lines (-61% from 1,040 starting point)**. Also lifted the inline `_response` closure to a module-level `_finalize_response_envelope` (16 callsites + 2 `response_wrapper=` references rewritten via `sed`).

  82 contact tests pass; full-project mypy clean at 277 source files. The remaining `process()` (407 lines) still has post-classify-fallbacks, pending-intent merges, enum-help-field early-return, and pre-dispatch refusals all inline — natural follow-up extractions matching the material/property phase pattern. `_dispatch_intent_to_handler` (665 lines) is itself well over the ceiling — could split the create-contact / resolve-then-dispatch / list-contacts branches further.

  **`_dispatch_intent_to_handler` split landed 2026-05-25**: the 382-line update/delete/get cluster lifted into `_resolve_and_dispatch_target_op` following the property playbook (line-for-line port of property's helper, minus the property-specific `contact_name` / `owner_name` params; the contact dispatcher's `active_contact_id` param turned out to be unused inside the body and was left untouched on the original method's signature for minimum-touch). `_dispatch_intent_to_handler` dropped from 665 → 299 lines (-55%); new helper at 412 lines (vs. property's 468). Net file size: 1,928 → 1,974 lines (+46 from new method header + the `return None` tail; the size cost is an honest tradeoff — per-function readability is the HIGH-issue target, not file-size minimization). Two `pending_record: Dict[str, Any] = {...}` annotations added to the lifted scope to keep mypy happy (the cluster's narrowest dict literal mixed with a downstream `pending_record["confirm_delete"] = False` mutation tripped `Collection[str]` inference). 99 contact tests pass across `test_contact_agent.py` + `test_contact_api.py` + `test_contact_model.py` + `test_cross_resource_envelope_contact.py`; full-project mypy clean at 279 source files. Natural next splits target the new helper's internal branches (delete-confirm fast-path / fuzzy-confirmation / get / update / delete) — same per-intent split that property's helper still needs.

  **`_handle_update_target_contact` extraction landed 2026-05-25**: the 152-line `if intent == "update_contact":` branch lifted out of `_resolve_and_dispatch_target_op` into a dedicated `_handle_update_target_contact` method. Covers the three sub-flows the branch already had inline: (a) multi-turn ``awaiting_value_for`` re-entry (the prior turn stashed a field-name → this turn supplies the value), (b) bare-field-name selection + ``awaiting_value_for`` stash + ``no-fields`` clarification stash, and (c) the field-merge → Google address enrichment → ``_update_contact_via_api`` → accuracy-suggestions pipeline. `_resolve_and_dispatch_target_op` dropped from 412 → 276 lines (-33%); new helper at 177 lines. File: 1,974 → 2,015 lines (+41). 99 contact tests pass; full-project mypy clean at 279 source files.

  **`_handle_delete_target_contact` extraction landed 2026-05-25**: the 79-line implicit-fall-through delete branch (reachable only when ``intent == "delete_contact"`` after update / get returned) lifted into its own method. Two-step shape preserved: first hit stashes ``pending_delete_*`` + the active-contact context keys and returns the confirmation envelope; second hit (with ``parsed.confirm_delete`` truthy or ``_is_confirm_text(message)``) hits ``_delete_contact_via_api`` and clears pending state. Signature deliberately narrower than `_handle_update_target_contact` — drops the unused ``fields`` / ``company_id`` / ``pending_override_applied`` params (delete uses ``target_contact.id`` and never enriches address fields). `_resolve_and_dispatch_target_op` dropped from 276 → 210 lines (-24%); new helper at 102 lines. File: 2,015 → 2,051 lines (+36). 99 contact tests pass; full-project mypy clean at 279 source files.

  **`_handle_create_contact` extraction landed 2026-05-25**: the 160-line `if intent == "create_contact":` branch lifted out of `_dispatch_intent_to_handler` into a dedicated `_handle_create_contact` method. Covers the three sub-flows the branch already had inline: (a) name-token reconciliation between ``parsed`` and the active pending intent's first/last name slots (the "name is X" with a prior pending first-name case is preserved), (b) single-missing-field inference from the prior turn's pending ``missing_fields`` list (only fires when exactly one required field was missing), and (c) Google address enrichment → required-field check → either stash-and-ask-for-missing or ``_create_contact_via_api`` → accuracy-suggestions + optional post-create follow-up question for any of ``phone`` / ``email`` / ``street`` not supplied. Cleaned up the stale ``# noqa - re-binding ... (line 1682)`` comment on the `pending_missing_fields` initializer — the prior-line reference was already wrong after the earlier extractions, and the variable is now scoped to the helper so no shadowing exists. Replaced with a clean ``pending_missing_fields: List[str] = []`` annotation. `_dispatch_intent_to_handler` dropped from 299 → 153 lines (-49%); new helper at 188 lines. File: 2,051 → 2,093 lines (+42).

  **`_handle_list_contacts` extraction landed 2026-05-25**: the 61-line list-contacts fall-through (name-hint normalization via ``parsed.full_name`` → ``first_name + last_name``; count-query / generic-words filtering against the inline ``_GENERIC_WORDS`` set; ``find_contacts_by_name`` vs. full-catalog ``_list_contacts_via_api`` dispatch; response shaping for count / empty / list cases) lifted out of `_dispatch_intent_to_handler` into a dedicated `_handle_list_contacts` method. Body moved verbatim (no dedent needed — already at method-body indent). Also fixed a pre-existing missing blank line between `_dispatch_intent_to_handler` and `process` left over from the first extraction round. `_dispatch_intent_to_handler` dropped from 153 → 101 lines (-34%); new helper at 82 lines. File: 2,093 → 2,123 lines (+30).

  Session totals for `agents/contact/service.py`: 1,928 → 2,123 lines (+195 from sig+docstring overhead across the five new methods). Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (210), `_handle_create_contact` (188), `_handle_update_target_contact` (177), `_handle_delete_target_contact` (102), `_dispatch_intent_to_handler` (101), `_handle_list_contacts` (82), `_classify_with_llm` (72), `_list_contacts_at_property` (71). No method now exceeds 210 lines (was 665 at session start) — every method reduced by at least 51%, the worst single function reduced by 68%. `_dispatch_intent_to_handler` is now a clean three-branch router: `create_contact` → helper, `update/delete/get` → resolve-then-dispatch helper, cross-resource filter (~34 lines, the only branch still inline since both sub-shapes are already in `_list_contacts_at_property` / `_list_contacts_for_estimate`), then `list_contacts` → helper. 99 contact tests pass; full-project mypy clean at 279 source files.

- `agents/property/service.py` — **2,418 → 2,027 lines (-391, -16.2%)** across 2026-05-24. Two-pronged refactor following the material-agent playbook:
  - **Pure-helper lift to new `agents/property/text_helpers.py`** (572 lines): 19 leaf-level methods moved out of `PropertyAgent` as module-level functions, plus 3 constants (`PROPERTY_ACTION_HINTS`, `_BARE_FIELD_ALIASES`, `_LABEL_PATTERNS`). Migrated helpers: `_is_confirm_text`, `_explicit_intent_from_message`, `_match_intent_rules`, `_sanitize_property_reference`, `_extract_name_from_message`, `_extract_contact_name_from_message`, `_extract_explicit_property_name_from_message`, `_extract_owner_name_from_message`, `_normalize_postal_zip_token`, `_normalize_country_token`, `_normalize_prov_state_token`, `_match_bare_field_name`, `_extract_label_fields`, `_try_canadian_full_address`, `_try_us_zip_address`, `_try_chunked_address`, `_try_partial_address`, `_try_at_prefix_canadian_address`, `_extract_fields_from_message`. 27 `self._foo(x)` callsites rewritten via `sed`. Three test sites updated (`agent._extract_fields_from_message(...)` → `_extract_fields_from_message(...)` plus an import) and one `monkeypatch.setattr(PropertyAgent, "_extract_name_from_message", ...)` rewritten to target the import location in `agents.property.service`.
  - **`process()` refactor**: split 936 → 750 lines (-20%) via three helper extractions matching the material pattern: `_run_llm_classification` (88 lines — LLM classify + entity-extraction; returns `(parsed, llm_error)`), `_apply_post_classify_fallbacks` (77 lines — explicit-intent override + name normalization + regex fallback; returns explicit_intent), `_apply_pending_intent_fallback` (91 lines — pending-intent merge for low-confidence intents; returns 6-tuple `(intent, probability, fields, contact_name, owner_name, pending_override_applied)`), `_check_pre_dispatch_refusals` (~50 lines — unsupported-intent + missing-company-id guards).

  58 property tests pass; full-project mypy clean at 276 source files.

  **`process()` dispatch extraction landed 2026-05-24**: lifted the 610-line try-body intent dispatch into `_dispatch_intent_to_handler` (636 lines initially). `process()` is now **150 lines (-84% from 936 starting point)** and reads as a linear pipeline: bulk-delete refusal → context setup → LLM classification → post-classify fallbacks → derive intent/probability/fields → pending-intent fallback → secondary pending-intent merge → active-property fallback → pre-dispatch refusals → `_dispatch_intent_to_handler(...)`. Also lifted the inline `_response` closure to a module-level `_finalize_response_envelope` (20 callsites rewritten via `sed`) so the dispatch helper has independent access to the envelope-defaults logic.

  **`_dispatch_intent_to_handler` split landed 2026-05-24**: the 438-line update/delete/get cluster lifted into `_resolve_and_dispatch_target_op`. `_dispatch_intent_to_handler` dropped from 636 → 216 lines (-66%). The new helper handles pending-delete confirmation, fuzzy-match resolve flow with stash-on-resolve-error, and the per-intent (update/delete/get) handler dispatch. Returns `Optional[Dict[str, Any]]` so the caller can fall through to the create / list / list-by-cross-resource branches when the intent isn't a resolved-target op. (The first run of the extraction script had a dedent bug — the cluster body was already at the right method-body indent and didn't need stripping. Reverted via `awk` to add the 4 spaces back, then fixed a fresh `Dict[str, Any]` annotation gap on `pending_record` exposed by mypy.)

  Updated `agents/property/service.py` line count: 2,418 → 2,123 (-295, -12.2%). Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (468), `_dispatch_intent_to_handler` (216), `process` (150), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77), `_classify_with_llm` (69). Two methods still well over the 50-line ceiling — natural next splits target the create-property branch (~90 lines) and the resolve-then-dispatch internals (delete-confirm path, fuzzy-match stash, per-intent handlers).

  **`_dispatch_intent_to_handler` create-property extraction landed 2026-05-28**: lifted the 92-line `if intent == "create_property":` branch into a dedicated `_handle_create_property` helper (107 lines). The dispatcher now delegates with an 11-line call site, leaving only the resolve-then-dispatch passthrough, the cross-resource filter shortcut, and the `list_properties` fall-through inline. `_dispatch_intent_to_handler` dropped from 216 → 138 lines (-36%). The new helper accepts the create-flow-specific subset of parameters (no `intent`, `active_pending_intent`, `contact_name`, or `owner_name`) and hardcodes `intent = "create_property"` internally. File grew slightly (2,123 → 2,152, +29) due to method-signature/docstring boilerplate, but per-method sizes are now more focused. Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (468), `process` (150), `_dispatch_intent_to_handler` (138), `_handle_create_property` (107), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77). Verified: 46 tests pass in `test_property_agent.py`; 52 pass in `test_orchestrator_endpoint.py`; mypy clean on `agents/property/`. The new helper is still over the 50-line ceiling — a future sub-split could separate the missing-fields stash branch (28 lines) from the post-create assembly (~70 lines), but each is one coherent code path so the value is marginal.

  **`_resolve_and_dispatch_target_op` per-intent handler split landed 2026-05-28**: lifted the three per-intent handlers out of the 468-line resolve-then-dispatch parent: `_handle_get_property` (43 lines), `_handle_update_property` (244 lines), `_handle_delete_property` (93 lines). The parent now reads as a linear pipeline — pending-delete early-exit → `_resolve_target_property(...)` → fuzzy-match confirmation stash → per-intent delegate — and drops from **468 → 169 lines (-64%)**. `_handle_get_property` is the only new helper under the 50-line ceiling; `_handle_update_property` is now the largest method in the file (244 lines) but is isolated, and its natural future split is the awaiting-value/bare-field-name clarification stash (~110 lines) vs. the merge-and-update body (~130 lines). All three new helpers hardcode `intent = "<op>"` internally rather than taking it as a parameter. File grew 2,152 → 2,233 (+81) for method-signature boilerplate. Top-N method sizes after this round: `_handle_update_property` (244), `_resolve_and_dispatch_target_op` (169), `process` (150), `_dispatch_intent_to_handler` (138), `_handle_create_property` (107), `_handle_delete_property` (93), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77), `_classify_with_llm` (69). Verified: 46 tests pass in `test_property_agent.py`; 52 pass in `test_orchestrator_endpoint.py`; mypy clean on `agents/property/`.

  **`_handle_update_property` sub-block split landed 2026-05-28**: the 244-line update handler split into two sub-helpers along its natural seam — the `if not fields and not contact_name:` clarification stash → `_maybe_stash_update_clarification` (116 lines, returns `Optional[Dict[str, Any]]` so the parent falls through on `None`), and the merge-and-update body → `_merge_and_update_property` (139 lines, async; owns the existing-payload merge, address enrichment, contact lookup/disambiguation, update API call, and response assembly). `_handle_update_property` is now **62 lines** (-75%): the awaiting-value unwrap (~12 lines) plus two delegate calls. The clarification-stash helper is sync (no awaits) — kept as a method rather than a module-level function because it touches `self._upsert_pending_intent` / `self._persist_pending_intents`. File grew 2,233 → 2,306 (+73) for method-signature boilerplate. Top-N method sizes after this round: `_resolve_and_dispatch_target_op` (169), `process` (150), `_merge_and_update_property` (139), `_dispatch_intent_to_handler` (138), `_maybe_stash_update_clarification` (116), `_handle_create_property` (107), `_handle_delete_property` (93), `_apply_pending_intent_fallback` (91), `_list_properties_by_cross_resource` (90), `_run_llm_classification` (88), `_apply_post_classify_fallbacks` (77), `_classify_with_llm` (69), `_handle_update_property` (62). Verified: 98 tests pass across `test_property_agent.py` + `test_orchestrator_endpoint.py`; mypy clean on `agents/property/`.

  **Property-agent chain paused 2026-05-28** — diminishing returns. The largest remaining method is `_resolve_and_dispatch_target_op` (169 lines), a linear pipeline whose sub-steps don't decompose cleanly without obscuring the flow. Pivoting to `agents/estimate/service.py` (#235), the largest file in the repo.

- `agents/estimate/service.py` — **2,600 → 2,451 → 2,344 lines (-256, -9.8% total)** across two 2026-05-28 passes:
  - Calc-cluster lift to new `agents/estimate/calc_helpers.py` (127 lines, 5 module-level functions: `get_material_default_price`, `get_material_default_cost`, `merge_duplicate_line_items`, `merge_resolved_material_items`, `merge_resolved_labour_items`). The cluster had eight methods total — three (`_calculate_material_cost`, `_estimate_labour_hours`, `_calculate_total_estimate`) were dead (zero call sites across `platform/`, `tests/`) and deleted outright. The remaining five didn't read `self` or call sibling methods, so they lifted cleanly as module-level functions. Six `self._foo(...)` call sites rewritten. Verified: 112 tests pass in `test_estimate_agent.py`.
  - Gathering sync-helpers lift to existing `agents/estimate/text_helpers.py` (643 → 759 lines, +116). The 2026-05-11 remaining-targets list called this the "gathering/sufficiency cluster (~200 lines)", but on inspection the cluster split into two surfaces: the two async LLM methods (`assess_sufficiency`, `extract_detail_from_reply`) are public — called by `routers/agent_helpers/delegate_create_estimate.py` and `routers/agent_helpers/estimate_gathering.py` — so they stay on the agent. The 5 sync helpers (`_field_name_variants`, `_normalize_enum_value`, `_extract_value_like_phrase`, `_detect_enum_help_field`, `_infer_single_pending_field_value`) are call-only-from-`service.py` pure functions that directly parallel the same names already lifted to `agents/contact/text_helpers.py` — matched the contact pattern and appended them as module-level functions. Five `self._foo(...)` call sites rewritten via `sed`. `text_helpers.py` grew to 759 lines, still under the 800-line HIGH threshold. Stale doc note from 2026-05-11 corrected: LLM error / JSON parsing helpers (`format_llm_error`, `build_json_parse_diagnostic`, `strip_json_comments`) were **already lifted** to `llm_helpers.py` in the same 2026-05-11 pass — that list entry was outdated, no work needed there.
  - Combined verification: 135 tests pass across `test_estimate_agent.py` + `test_estimate_gathering.py`; mypy clean on `agents/estimate/` (14 source files).
  - Extraction normalization cluster lifted to new `agents/estimate/extraction_helpers.py` (342 lines, 7 module-level functions: `normalize_extracted_estimate`, `has_meaningful_value`, `merge_job_item_payloads`, `merge_with_pending_estimate`, `build_optional_follow_up`, `collect_missing_required_fields`, `build_clarifying_question`). All 7 are pure data transformations — none touch `self` state, only intra-cluster method calls (which become bare function calls in the module). The module imports `_normalize_enum_value` from `text_helpers` and `ExtractedEstimate` from `schemas`. Five `self._foo(...)` call sites in `service.py` rewritten via `sed`. No external callers (grep across `platform/`, `tests/`). Verified: 135 tests pass; mypy clean (now 15 source files in `agents/estimate/`).
  - `agents/estimate/service.py` net session reduction: **2,600 → 2,055 lines (-545, -21.0%)** across the calc, gathering-sync, and extraction-normalization passes.
  - LangChain research/architect pipeline cluster lifted to new `agents/estimate/llm_pipeline.py` as a `LlmPipelineMixin` (1,089 lines). 17 methods moved as-is: `_build_research_input`, `_collect_research_sources`, `_normalize_research_result`, `_decompose_requirement`, `_step1_architect`, `_step2_vector_retrieval`, `_step3_research_for_scope`, `_reuse_past_work_item`, `_step2_and_3_for_scope`, `_run_pipeline`, `_run_react_loop`, `_run_estimate_research`, `_estimate_has_no_line_items`, `_build_estimate_from_research`, `_extract_estimate_with_llm`, `_fallback_accuracy_suggestions`, `_generate_accuracy_suggestions`. **Mixin pattern (not module-level)** because tests + `agents/estimate/tools.py` call these as `agent._step1_architect(...)` / `monkeypatch.setattr(EstimateAgent, "_step1_architect", ...)` — preserving the agent-method surface keeps all callers unchanged. `EstimateAgent` inheritance is now: `(CatalogMatchingMixin, CrudParsingMixin, WorkItemHandlersMixin, WorkItemFieldHandlersMixin, CrudHandlersMixin, LlmPipelineMixin)`.
  - Test patches updated: `monkeypatch.setattr(estimate_service, "search_similar_work_items", ...)` (2 sites) rewritten to target the new module (`estimate_llm_pipeline`). The `ChatOpenAI` patches at module level were unaffected because the mixin doesn't import `ChatOpenAI` directly — `self.llm` is set on the agent.
  - TYPE_CHECKING stub block added inside `LlmPipelineMixin` declaring the host-instance attrs the mixin touches: `llm`, `architect_llm`, `responses_client`, `architect_prompt`, `research_prompt`, `web_research_enabled`, `vector_search_enabled`, `react_max_iterations`, plus `_fill_prices_and_calculate_totals` (the only sibling method called that lives outside the mixin chain). Matches the established pattern in `CrudHandlersMixin` and `WorkItemHandlersMixin`.
  - **`agents/estimate/service.py` final session size: 2,055 → 1,089 lines (-966, -47% from this final pass; -1,511 total from session start of 2,600, -58.1%).** Cluster split out cleanly without disturbing any of the in-place CRUD / process / response-shaping logic.
  - Verified: 144 tests pass across `test_estimate_agent.py` + `test_estimate_gathering.py` + `test_estimate_tools.py`; mypy clean across all 16 source files in `agents/estimate/`. 3 pre-existing failures in `test_agents_api.py::test_*_estimate_*_requires_confirmation` (event-loop / "Future attached to a different loop" Beanie cursor issue) reproduce on HEAD without these changes — unrelated to this refactor.
  - **`_fetch_inventory_items` split landed 2026-05-29**: the 106-line method split into a thin orchestrator (18 lines) plus two sub-helpers — `_fetch_materials_inventory` (56 lines) and `_fetch_labour_inventory` (35 lines). The orchestrator wraps both sub-calls in a single try/except (the only Beanie failure mode worth catching), defaulting to module-level `_empty_materials_inventory()` / `_empty_labour_inventory()` sentinels on error. The `_size_price` inner closure was promoted to a module-level `_size_unit_price(size)` helper (5 lines) and is now reused inside `_fetch_materials_inventory` (was duplicated inline twice in the original). Both sub-helpers raise on error — only the orchestrator catches — which is honest about the failure mode. All 15 `monkeypatch.setattr(EstimateAgent, "_fetch_inventory_items", fake)` test sites unaffected because they replace the orchestrator wholesale (sub-helpers aren't called when patched). `_fetch_materials_inventory` is 56 lines — just over the 50-line ceiling, kept as one coherent fetch+build flow. Verified: 144 tests pass; mypy clean. After this round, `_fetch_inventory_items` is no longer on the 2026-05-11 list. `agents/estimate/service.py` final size: 1,089 → 1,118 lines (+29 for signature/docstring boilerplate, but the largest method shrunk from 106 → 56).
  - **Session-wide summary on `agents/estimate/service.py`: 2,600 → 1,118 lines (-1,482, -57%).** Remaining over-50-line methods: `process` (333 lines — main entry orchestrator, the natural next target), `_fill_prices_and_calculate_totals` (224 lines — already on the 2026-05-11 list as "single function that should split into helper steps"), `_fetch_materials_inventory` (56 lines, just over). Top-of-funnel `process()` is the last big chunk left.

- `agents/orchestrator/service.py` — 1990 lines (file-level). `_classify_with_rules` reduced 2026-05-22/23 from 238 → 76 lines via five helper extractions:
  - `_classify_specific_phrasings` (52 lines — link/work-item/EST-code-total overrides)
  - `_classify_via_action_domain` (47 lines — standard ACTION+DOMAIN orchestration shell)
  - `_resolve_action_and_domain` (22 lines — ACTION + DOMAIN match with plural-aware get→list override)
  - `_apply_add_set_update_override` (36 lines — "add/set a <field> to <entity>" create→update rewrite)
  - `_ambiguity_fallback` (36 lines — three ambiguity clarification shapes)

  All five new helpers are under the 50-line ceiling. Main shell now reads as a linear sequence of `if (result := stage(...)) is not None: return result` short-circuits. Only the shell itself (76 lines, mostly comments) and `_classify_specific_phrasings` (52 lines) remain over the soft ceiling. `process()` still duplicates the same short-circuit patterns (see MEDIUM #12). Verified: 279 tests pass across `test_orchestrator_intents.py` + `test_orchestrator_endpoint.py` + `test_orchestrator_bare_entity_helpers.py`; mypy clean on `agents/orchestrator/`.

No function in this repo should exceed 50 lines. Grep for long bodies with
a line-count tool after each refactor pass.

Specific instances:
- #18 — `agents/estimate/service.py` at 5,098 lines (2026-04-22 refresh).
- #94 — New material handlers all exceed the 50-line ceiling.
- #125 — `agents/orchestrator/service.py` at 1,358 lines (file-size note).
- #137 — `NewEstimateWithActivityPage.tsx` extractions partial (1,733 lines).
- #165 — `_list_properties_by_cross_resource` still 88 lines after #155.
- #166 — `_list_contacts_for_estimate` still 91 lines after #156.
- #167 — `_resolve_cross_resource_properties` at 62 lines (accepted).
- #235 — `agents/estimate/service.py` at 6,066 lines (largest file in repo).
- #236 — `portal/src/pages/SettingsPage.tsx` is 2,496 lines.
- #237 — `agents/material/service.py` at 2,745 lines (file-level).
- #238 — `routers/agents.py` at 2,640 lines.
- #240 — `agents/property/service.py` at 2,386 lines.
- #241 — `agents/contact/service.py` at 2,378 lines.
- #242 — `NewEstimateWithActivityPage.tsx` at 1,814 lines.
- #243 — `agents/orchestrator/service.py` at 1,970 lines.
- #244 — `agents/labour/service.py` at 1,732 lines.
- #245 — `portal/src/pages/MaterialsPage.tsx` at 1,421 lines.
- #246 — `agents/equipment/service.py` at 1,343 lines.
- #247 — `portal/src/pages/ContactsPage.tsx` at 1,324 lines.
- #248 — `portal/src/pages/PeoplePage.tsx` at 1,024 lines.
- #249 — `portal/src/pages/PropertiesPage.tsx` at 878 lines.
- #250 — `platform/routers/auth.py` at 892 lines.
- #257 — `routers/agents.py` grew to 2,810 lines post-gate-helpers PR.
- #260 — `routers/estimates.py` over the 800-line soft cap (1,294 lines).

**Absorbed:** #18, #94, #125, #137, #165, #166, #167, #235, #236, #237, #238, #240, #241, #242, #243, #244, #245, #246, #247, #248, #249, #250, #257, #260 — specific file/function-size instances surfaced in later review passes. See `## Closed` for original bodies.

## MEDIUM — ~45 findings

Cosmetic / hygiene. Safe to batch into a single "chore: code hygiene" PR, or
clean up opportunistically when editing a file.

### 8. [MEDIUM] `print()` → `logging`
Any `print()` left in `services/`, `routers/`, `agents/`, or `models/`. Keep
`print()` in `scripts/` (operator-facing CLIs) — that's appropriate there.

### 9. [MEDIUM] Magic numbers → named constants
Examples found: timeout values, quota limits, retry counts, score thresholds.
Give each a module-level constant with a short comment explaining its source.

Specific instances:
- #162 — `_parse_estimate_date_filter` fixed day counts per unit
- #171 — `lg:right-[26rem]` AI panel width duplicated across 3 sites
- #194 — `1_000_000` "effectively unlimited estimates" across 3 sites
- #262 — `Math.max(heightPct, 4)` unnamed minimum bar floor
- #267 — `1023px` mobile breakpoint coupled to Tailwind `lg`

**Absorbed:** #162, #171, #194, #262, #267.

### 10. [MEDIUM] Missing docstrings on public APIs
Focus only on functions exported across package boundaries. Don't docstring
private helpers — named variables beat comments.

**Absorbed:** #52.

### 11. [MEDIUM] TODO / FIXME triage
Grep for `TODO` and `FIXME` added in recent changes. Each should either:
- be resolved, or
- be converted into a GitHub issue with a link back to the code.
Comments that just say "TODO" with no owner / date / issue will rot.

Specific instances:
- #253 — Remove deprecated `TokenUsageAccumulator` after one billing cycle
- #254 — Reintroduce `request_id` on `LLMUsageEvent` when middleware lands

**Absorbed:** #253, #254.

### 13. [MEDIUM] Mutation where immutable return would be clearer
Case-by-case judgment. Only refactor if it actually simplifies the reader's
job; don't chase stylistic purity.

---

## 2026-04-22 review (Maple estimate flow session)

MEDIUM and LOW findings from the `/code-review` pass after the tax / division
/ description / work-item-delete work. The HIGH finding from that pass
("last work item" inconsistency) was fixed in the same session; these are
the residuals.

### 14. [MEDIUM] Unused `ESTIMATE_GENERATION_PROMPT` import
**File**: `agents/estimate/service.py:15`
**Severity**: MEDIUM (hygiene)

The module-level `ESTIMATE_GENERATION_PROMPT` constant is imported but never
referenced — only `build_estimate_generation_prompt()` function calls are
used (lines 446, 2008, 4830). Pre-existing; surfaced during investigation of
why prompt edits weren't taking effect.

Fix: drop the import.

### 15. [MEDIUM] Split Example block may anchor LLM back to terse descriptions
**File**: `prompts/estimate_generation.py`, ~lines 99-109
**Severity**: MEDIUM (prompt quality)

Rule 4d now requires 1-2 sentence (~15-40 word) descriptions with materials,
sizes, and method. The Split Example block still shows short labels like
`Paver patio installation`, `Low-voltage landscape lighting installation`,
`Lawn refresh and grading`. LLMs latch onto examples as implicit targets, so
these short labels may be undermining rule 4d's guidance.

Fix: rewrite each Split Example entry to the richer 4d shape, e.g.
`Paver patio installation — 400 sq ft porcelain pavers on compacted base
with edge restraints and polymeric sand joints`. Low effort, likely
meaningful impact on what Maple actually emits.

### 16. [LOW] Delete-button propagation on touch devices
**File**: `portal/src/pages/NewEstimateWithActivityPage.tsx` (trash button
per work item row)
**Severity**: LOW (needs manual verification)

The row has an `onClick` that opens the work-item editor, and the trash
button inside the row calls `e.stopPropagation()`. On some touch devices a
long-press can fire both `pointerdown`/`click` paths and both handlers run.
Not verifiable from source — needs a mobile-browser test.

Fix (if the test shows leakage): add
`onPointerDown={(e) => e.stopPropagation()}` alongside the existing
`onClick` on the trash button.

### 17. [LOW] Architect prompt rule 5 still mentions "quantities" ambiguously
**File**: `prompts/estimate_architect.py`, rule 5
**Severity**: LOW (prompt quality)

Rule 5 now says "DO NOT include prices, labour rates, or inventory IDs/SKUs.
Sizes and quantities … ARE allowed." A stricter LLM may read the word
"quantities" as still-discouraged overall, because this rule used to ban all
quantities.

Fix: tighten to "DO NOT include prices, labour rates, inventory IDs, or
**purchase quantities** (how many to buy). Scope-describing sizes,
dimensions, coverage area, linear feet, and spacing ARE allowed."

---

## 2026-04-22 second review (six-phrasing coverage session)

HIGH tenant-leak (`_resolve_latest_estimate` unscoped fallback) and the
notes-overwrite safety finding were fixed in the same session. Residuals
below were deferred per reviewer direction.

### 20. [MEDIUM] Narrow `except Exception` around `PydanticObjectId(company_id)` cast in `_resolve_latest_estimate`
**File**: `agents/estimate/service.py` — the first of two `except Exception`
clauses in `_resolve_latest_estimate` (around line 3266 post-fix).
**Severity**: MEDIUM (hygiene, matches entry #0 of the original batch)

The `PydanticObjectId(company_id)` cast is wrapped in `except Exception:
return None`. Only `InvalidId` / `TypeError` can arise from a bad cast,
so broadening to `Exception` masks unrelated failures.

The same defect in `_load_estimate_for_update` and `_load_estimate_for_read`
was fixed in the 2026-04-26 #80 refactor by extracting the shared
`_coerce_company_oid` helper with a narrowed `except (InvalidId, TypeError)`.
The same helper can be used here.

Fix: replace the inline cast with `self._coerce_company_oid(company_id)`,
or apply the same `except (InvalidId, TypeError)` narrowing inline.
Keep the second broad-except (around line 3277 post-fix) — it logs via
`logger.exception` so a surprise failure is still observable.

### 21. [MEDIUM] Module-scope vs. method-scope inconsistency for note/work-item helpers
**File**: `agents/estimate/service.py`
**Severity**: MEDIUM (style)

`_detect_note_update`, `_is_property_link_request`, and
`_detect_status_transition` are all instance methods on the agent class,
but `_detect_get_work_item_request` and `_parse_work_item_position` live at
module scope. Callers have to know which helper is where.

Fix: promote the two module-level helpers to methods, or demote the three
instance methods to module functions and thread any needed state through.
Low effort; no behavior change.

### 22. [LOW] "Last estimate" with zero estimates falls back to generic "Which estimate?"
**File**: `agents/estimate/service.py` — the `_handle_get_estimate` branch
that falls through when `_resolve_latest_estimate` returns `None`.
**Severity**: LOW (UX polish)

When a user asks "what is the grand total for the last estimate" and the
company has no estimates yet, the handler shows the generic "Which
estimate? Please share the estimate code (e.g. EST-2026-001)." prompt.
Correct behavior but confusing for a new user.

Fix: detect the latest-estimate intent (via `_looks_like_latest_estimate_query`)
before the generic clarification and respond with "You don't have any
estimates yet."

### 23. [LOW] `_NOTE_WITH_IMPLICIT_TAIL` can false-positive on descriptive phrasings
**File**: `agents/estimate/service.py` — the `_NOTE_WITH_IMPLICIT_TAIL`
regex inside `_detect_note_update`.
**Severity**: LOW (edge-case UX)

The pattern `\b(?:with|add(?:ing)?|append(?:ing)?)\s+(?:a(?:nother)?\s+)?
notes?\s+(?P<value>.+?)\s*$` will match phrasings like "update estimate X
with notes about the call" and capture "about the call" as a note body.
Very unlikely in practice (users rarely ask Maple to describe things), but
the capture is silent so a false positive would append unwanted text to
the estimate.

Fix: require a cue token after `note/notes` signaling that a value is
coming — e.g. a quote, a colon, or a preposition like `to`/`saying`/
`that reads`. Or fall back to the quoted-only path when the implicit tail
looks descriptive.

---

## 2026-04-22 third review (external warnings triage)

Eight warnings raised by an external pass; each verified against current
source before filing. One was a hallucination and is noted under Deferred.

### 25. [MEDIUM] Regex email lookup in `_resolve_user()`
**File**: `dependencies.py:17-26`
**Severity**: MEDIUM

Email is `.lower()`'d at line 17, then looked up with
`User.find_one({"email": {"$regex": f"^{escaped_email}$", "$options": "i"}})`
at line 25-26. The case-insensitive regex defeats index usage on the
`email` field and runs on every authenticated request. `User.email` in
`models/user.py` is stored without normalization, so the regex is defending
against historical mixed-case data rather than the current write path.

Fix: two-step. (a) Add a one-shot backfill script under
`scripts/` that lowercases `User.email` for all existing rows. (b) Normalize
on write (override `__init__` / validator so any create or update lowercases
the field). (c) Replace the regex with `User.find_one(User.email == email)`.
Don't do (c) before (a) — a stray capitalized row would silently fail auth.

### 26. [MEDIUM] `find_contacts_by_name` fetches whole company, filters in Python
**File**: `agents/contact/utils.py:158-170`
**Severity**: MEDIUM

`Contact.find(Contact.company == ...).to_list()` pulls every contact for
the tenant, then lines 163-170 iterate and match names in Python. Fine at
dozens of contacts; degrades linearly with tenant size.

Fix: push the name match into Mongo. Either a `$regex` with
`^<escaped>$` and `$options: "i"` (bearable here because the query is
per-tenant-scoped and low-frequency), or — better — a case-insensitive
collation index on `first_name` / `last_name` with an equality query. If
fuzzy matching is required, keep the Python filter but pre-narrow with a
Mongo text-ish prefix filter so the in-memory set is small.

### 27. [LOW] Inefficient merge pattern in bulk work-item endpoint
**File**: `routers/agents.py:1621-1632`
**Severity**: LOW (code clarity)

The code calls
`merge_job_items_with_original_descriptions([], new_job_items_raw, ...)`
with an empty first argument, which turns the helper into a no-op, then
manually appends the parsed items to `target_estimate.job_items`. The
helper at `routers/estimates.py:404-415` is designed for reconciliation
between an existing request list and newly parsed items — passing `[]`
bypasses that contract. Canonical usage is in `prepare_generated_estimate`.

Fix: either call the helper with the real existing items (if reconciliation
is wanted) or drop the call entirely and just build items from
`new_job_items_raw` via `build_job_items_from_parsed`. Works fine today; the
concern is that the next reader will assume reconciliation is happening.

### 28. [LOW] Unbounded `ChangeLogEntry.find_all()`
**File**: `routers/change_logs.py:23-26`
**Severity**: LOW

`ChangeLogEntry.find_all().sort(...).to_list()` with no `.limit()`. Current
volume is small (curated changelog), so this is an anti-pattern waiting to
bite rather than an active problem.

Fix: add `.limit(100)` and accept an optional `?limit=` / `?offset=` query
param. Cheap to do; reviewer should have filed as LOW, not WARNING.

### 29. [LOW] `update_estimate` recalculates totals on any `job_items`-present edit
**File**: `routers/estimates.py:1868-2016`
**Severity**: LOW (likely won't fix)

When `payload.job_items is not None`, the handler recalculates the entire
estimate's totals — even if the client sent back unchanged items alongside a
notes/title edit. Overhead is real but CPU-bound and negligible at normal
estimate sizes.

The reviewer framed this as waste, but the *safer* reading is that
gating recalculation on change-detection would risk stale totals if the
change-detector missed a case. Leave alone unless profiling shows latency.
Filed so we don't re-litigate.

### 30. [LOW] `[A-Z]{2}` with `re.IGNORECASE` for state-code parsing
**File**: `agents/property/service.py:520` (regex) and `:527` (flag)
**Severity**: LOW (nit)

The compiled pattern matches any two-letter substring when run with
`IGNORECASE` — "in", "or", "to", "me" all pass. In practice the match runs
against address-shaped input and the result flows through
`_normalize_prov_state_token` (`service.py:298-323`) which does additional
validation, so false positives in free prose aren't reaching users.

Fix (when touching this file): drop the `IGNORECASE` flag and match
`[A-Z]{2}` strictly, or validate the token against a `VALID_STATES` /
`VALID_PROVINCES` set inside `_normalize_prov_state_token`. No hurry.

---

## 2026-04-22 fourth review (post-#24 bulk-fetch fix)

Follow-ups from the `/code-review` pass on the #24 fix (bulk-fetch in CSV
upload handlers). The fix itself is good — these are residuals that didn't
warrant blocking the commit.

### 31. [MEDIUM] Intra-CSV duplicate rows now upsert silently instead of erroring
**Files**: `routers/equipments.py:148-170`, `routers/labours.py:204-229`
**Severity**: MEDIUM

Before the #24 fix, a CSV with two rows sharing the same `(name, unit)`
would insert the first and crash the second (captured into `errors[]`).
After the fix, the handler registers each newly-inserted row back into
`existing_by_key`, so the second occurrence upserts the first. The behavior
is arguably friendlier, but (a) it's undocumented, (b) no test exercises
it, and (c) the response payload reports N `created` IDs for an N-row
upload even when the user effectively paid for duplicate rows.

Fix: pick one of — (i) add a test pinning the new upsert-on-duplicate
behavior; (ii) or revert to the pre-fix error behavior by omitting the
`existing_by_key[(name, unit)] = row` registration line. If staying with
(i), consider splitting the response into `created` vs `updated` lists so
the caller can see what actually happened (materials.py already does this).

### 32. [MEDIUM] `hasattr(l.unit, "value")` defensive check with unclear motivation
**File**: `routers/labours.py:202`
**Severity**: MEDIUM

`existing_by_key = {(l.name, l.unit.value if hasattr(l.unit, "value") else l.unit): l for l in candidates}` —
the `Labour.unit` field is typed as `LabourUnit` enum in the model, so
`.value` should always work. The `hasattr` fallback either (a) defends
against legacy string-valued rows in prod, or (b) is defensive coding
without cause. If (a), document it; if (b), drop it.

Fix: grep production data once to check whether any `Labour` rows have
`unit` stored as a raw string. If none, simplify to `l.unit.value`. If
some, add a one-line comment and file a data-migration task.

### 33. [MEDIUM] `$in` × `$in` bulk-fetch over-fetches the cross-product
**Files**: `routers/equipments.py:138-144`, `routers/labours.py:195-201`
**Severity**: MEDIUM (theoretical) / LOW (in practice)

For a CSV with N distinct names and M distinct units, the query
`{"name": {"$in": names}, "unit": {"$in": units}}` matches every name ×
unit combination in Mongo — up to N×M rows — even though only exact-tuple
matches are used. The Python-side filter `existing_by_key.get((name, unit))`
discards the extras. Harmless for typical CSVs (one unit type, many
names), grows quadratically with mixed CSVs.

Fix (when it bites): switch to `{"$or": [{"name": n, "unit": u} for ...]}`
— exact tuples, no bloat. Not worth doing until we see a CSV where this
matters.

### 34. [LOW] Missing type hint on `existing_by_key` dict
**Files**: `routers/equipments.py:136`, `routers/labours.py:193`
**Severity**: LOW

Materials.py added the annotation (`existing_by_key: Dict[str, Material] = {}`);
equipments.py and labours.py did not. Consistency gap introduced by the
same commit.

Fix: `existing_by_key: Dict[Tuple[str, str], Equipment] = {}` (and
similarly for Labour). Import `Dict, Tuple` from typing.

### 35. [LOW] `names` list in materials bulk-fetch may contain casing duplicates
**File**: `routers/materials.py:295`
**Severity**: LOW

`names = [md["name"] for md in grouped.values()]` — `grouped` is keyed by
`name.lower()`, so names are unique by casefold but not by original
casing. A CSV with both `"Patio Stone"` and `"patio stone"` would produce
two `$in` entries that both resolve to the same Mongo row.

Fix: `list({md["name"] for md in grouped.values()})`. Micro-optimization;
skip unless already editing the file.

---

## 2026-04-22 fifth review (post-#1 async-hygiene fix)

Follow-ups from the `/code-review` pass on the #1 fix (Firebase wraps +
Contact N+1 batching). Same-session fixes: silent-swallow logging on
`_fetch_linked_contacts`, and a test-assertion shape cleanup on the new
batched-find test. Residuals below were deferred.

## 2026-04-22 sixth review (post-#2 Maps rate-limit fix)

Residuals from the `/code-review` pass on the #2 fix (per-company Maps
rate limiting + auth dep on the addresses router). The docstring MEDIUM
was fixed in the same session; these are what's left.

### 39. [LOW] `_RATE_LIMIT_DETAIL` constant is misplaced in `address_service.py`
**File**: `services/address_service.py:15`
**Severity**: LOW (code layout)

The `_RATE_LIMIT_DETAIL` module-level constant sits between the import
block and the unrelated `SUPPORTED_COUNTRY_CODES` set, separated from
its only caller (`_enforce_maps_rate_limit`) by one line. Cohesion with
the helper would read better.

Fix: either inline the literal as `detail=` inside
`_enforce_maps_rate_limit`, or move the constant to sit directly above
the helper. Cosmetic; do when next touching the file.

---

## 2026-04-23 `/security-review` pass (post-LLM rate-limit fix)

HIGH finding (missing per-company rate limiting on `/agents/orchestrate`
and `/agents/estimate`) was fixed in the same session as the pass. The
two items below are the residual MEDIUM findings. LOW finding
("`_handle_get_estimate` unscoped fallback") duplicates entry #37 and
is not re-filed.

## 2026-04-23 `/code-review` pass (estimate status state machine + detail-page layout)

MEDIUM and LOW residuals from the `/code-review` pass on the layout +
status-state-machine work. No CRITICAL or HIGH findings. Recommendation
was "Warning — safe to commit" — items below are quality-of-life.

### 43. [MEDIUM] Trash-icon-only buttons have no accessible name
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — Preview version-row delete (~line 1017) and work-item row delete (~line 1147)
**Severity**: MEDIUM (a11y)

Both buttons render only `<Trash2 />` inside. Each is wrapped in a
`<Tooltip content="Delete this version">` (or similar), but tooltip
content is typically not announced by screen readers — the button has
no accessible name. Same pattern appears on other icon-only trash
buttons across the portal (EquipmentsPage, ContactsPage, PropertiesPage,
RateCardsTab, etc.) — this is a portal-wide gap, not specific to this
change.

Fix: add `aria-label={`Delete version ${v.version}`}` (or equivalent
row-specific label) on every icon-only trash button. Sweep-style PR;
grep for `<Trash2 ` and audit each site.

**Absorbed:** #258, #191 — duplicate findings on the same a11y gap (icon-only / decorative-icon accessible names) from later review passes. See `## Closed` for their original bodies.

### 44. [MEDIUM] `(err as Error).message` fallback in catch blocks can render `undefined`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — three catch blocks: `handleDelete` (~L427), `handleStatusChange` (~L458), `handleGenerateGoogleDoc` (~L481)
**Severity**: MEDIUM

If the rejected value isn't an `Error` instance (plain string from
`ApiError`, JSON object, aborted fetch signal), `(err as Error).message`
evaluates to `undefined` and `setFormError(undefined)` clears the banner
instead of showing a useful message. Pre-existing pattern carried through
the refactor; third catch (`handleGenerateGoogleDoc`) already has an
OR-fallback, the first two do not.

Fix: unify to `setFormError(err instanceof Error ? err.message :
"Failed to update status")` (pick appropriate fallback copy per handler).
One-line change per catch.

### 45. [LOW] `.gitignore` widened from filename to directory without comment
**File**: [platform/.gitignore](../../platform/.gitignore):145
**Severity**: LOW

`service-account-key.json` → `secrets/` is functionally fine (the
`service-account-key*.json` and `*-key.json` sibling patterns still
catch loose keys), but the diff reads as "why did a specific-file rule
become a directory rule?" without context.

Fix: add a one-line comment above the `secrets/` entry — e.g.
`# local secrets directory (service-account keys, tokens, etc.)` — so
the next reader understands the broadening.

## 2026-04-23 `/code-review` pass (verbless-gap fix)

Residuals from the `/code-review` pass on the Phase 1 + 2a + 2b verbless
classification fix. No CRITICAL or HIGH findings blocked commit;
recommendation was "Warning — safe to commit." Items below are quality
debt from the heuristic-driven implementation of Phase 2b that the
original plan's catalog-backed Phase 2a-proper would largely retire.

Plan: [plans/fix-maple-verbless-gap.md](plans/fix-maple-verbless-gap.md).

### 49. [MEDIUM] `_ADDRESS_PATTERN` can false-match "N <word>+ way/court"
**File**: [agents/orchestrator/service.py:65](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

Pattern uses `.search()` (not `.fullmatch()`) with permissive suffixes
including `way`, `court`, `ct`. Phrasings like `"3 days back way"` or
`"60 minutes one way"` trigger `domain=property` → `get_property`. Low
real-world frequency but demonstrably triggerable.

Fix (quick win): drop the most-ambiguous suffixes (`way`, `court`,
`ct`). Smaller coverage, fewer false positives. For the permanent fix,
require the match to be the entire residual after stripping any
action-phrase prefix via `_bare_entity_residual`. Catalog-backed
lookup (per the plan's deferred Phase 2a-proper) would retire the
concern entirely.

### 53. [LOW] `_CONFIRMED_WORKING_CASE_IDS` has no entry-validation
**File**: [tests/_maple_coverage_data.py](../../platform/tests/_maple_coverage_data.py)
**Severity**: LOW

The override set grows monotonically and is manually curated. A
mistyped case ID silently does nothing — the override never applies,
and the phrasing stays marked as an XFAIL without the reviewer
realizing.

Fix: at module load, assert that every entry in
`_CONFIRMED_WORKING_CASE_IDS` corresponds to a real `case_id` in the
matrix; raise `ValueError` on mismatch. ~5 lines.

### 55. [MEDIUM] Tier 2 gap: implicit-relationship cross-resource phrasings
**Files**: LLM system prompt in
[agents/orchestrator/service.py:~674](../../platform/agents/orchestrator/service.py) (and entity-knowledge graph if extended)
**Severity**: MEDIUM (Tier 2 coverage 4/12)

Phrasings like `who owns 123 Main St?`, `where does John Doe live?`,
`which properties use concrete blocks?`, `what estimates use the
Landscaper role?` expect Maple to return `list_<related_resource>`
intents. LLM handles these inconsistently and rules can't infer
cross-resource semantics at all.

Fix (sketch): add 4–6 few-shot examples to the LLM system prompt that
pair each implicit-relationship phrasing with the expected
`list_<related_resource>` intent. Then re-run Tier 2 and see whether
the LLM picks them up. If prompt alone doesn't close it, the
orchestrator would need to resolve the referenced entity first, then
infer the target resource based on the relationship verb — that's a
larger design change.

## 2026-04-23 review (Estimate Detail + Maple panel session)

Findings deferred from the `/code-review` pass on the Estimate Detail page
polish, Maple list-formatting helper, and Maple-panel footer nav work.
HIGH items in that review were fixed in-session; these are the MEDIUM /
LOW items the user chose not to land right now.

### 57. [LOW] Stale closure of `estimate` in `handleGenerateGoogleDoc`
**Severity**: LOW
In `portal/src/pages/NewEstimateWithActivityPage.tsx`, after
`await handleSaveEstimate()` resolves, the local `estimate` identifier
still refers to the pre-save snapshot — only `getEntityId(estimate)` is
read afterward, and the ID doesn't change, so no current bug. But anyone
extending this path to read a field that can change mid-save (e.g.,
`estimate.status`, `estimate.updated_at`) will silently use stale data.

Fix: widen `handleSaveEstimate` to return
`Promise<EstimateWithExtras | null>` and use the resolved value instead
of the closure reference.

### 59. [LOW] Drive-filename filename-collision policy still implicit
**Severity**: LOW
The 2026-04-23 fix put the estimate_id back into the Drive filename
(`Estimate-{estimate_id}-V{n}`), which resolves traceability. However,
Drive still permits duplicate filenames within a folder — there is no
enforcement that `(estimate_id, version)` is globally unique *as a
filename*. If two concurrent generate-doc requests race, they could
produce two Drive files with the same name. The version-number
computation in `routers/estimates.py:2376-2379` is also read-modify-
write without a lock.

Fix: add a unique index on `(estimate_id, version)` inside the
`GoogleDocsVersion` embedded array, or wrap the version-bump + create
in an optimistic-concurrency retry keyed on `estimate.updated_at`.
Low priority — the user would need to double-click "New Version" within
the Drive latency window to trigger the race.

---

## 2026-04-24 external review (indexes + httpx + DB-side sort)

Three warnings raised by an external reviewer; each verified against
current source before filing. None are active bugs. Filed per user
request for later triage.

### 60. [MEDIUM] No unique compound index on Material / Contact
**Files**: [platform/models/material.py:32](../../platform/models/material.py),
[platform/models/contact.py:45](../../platform/models/contact.py)
**Severity**: LOW–MEDIUM (data integrity, not an active bug)

Both models declare only `IndexModel([("company", ASCENDING)])`. Concurrent
inserts can produce duplicates for the same `(company, name)`.

The reviewer's proposed fix — "compound unique index on (company, name)
for all inventory models" — is correct for Material but **wrong for
Contact**. Two contacts can legitimately share a full name (two different
"John Smith" homeowners). A Contact uniqueness constraint would need to
include email/phone, and even that is debatable.

Fix: for Material, add `IndexModel([("company", ASCENDING), ("name",
ASCENDING)], unique=True)` — but only after auditing prod data for
existing duplicates; index creation fails if violations exist. For
Contact, no unique index (reviewer was wrong on this one); if
deduplication is a real concern, surface it in the UI on create/update
instead.

**Absorbed:** #66.

### 61. [LOW] Trello httpx client rebuilt per request
**File**: [platform/services/trello_service.py:40](../../platform/services/trello_service.py)
**Severity**: TRIVIAL (don't fix unless path becomes hot)

`async with httpx.AsyncClient(timeout=15.0) as client:` inside
`create_trello_card` tears down the connection pool on every call.
Reviewer correctly flagged that a module-scoped client would enable
connection pooling.

In practice: this endpoint fires once per estimate → card creation. The
pool-churn cost is microseconds on a call that already takes hundreds of
ms over the network. Premature optimization at current volume.

Fix (if it ever matters): promote to a module-level
`_client = httpx.AsyncClient(timeout=15.0)` and swap the `async with`
for `await _client.post(...)`. Add a FastAPI lifespan hook to close it
on shutdown.

### 62. [LOW] Python-side sort in `get_material_categories` / `get_material_units`
**Files**: [platform/routers/material_categories.py:48](../../platform/routers/material_categories.py),
[platform/routers/material_units.py:49](../../platform/routers/material_units.py)
**Severity**: LOW (cleanliness, not performance)

Both handlers call `sorted(items, key=lambda x: x.name.lower())` after
`.to_list()`. Reviewer framed this as "unscalable" — overstated, since
category/unit counts per company are dozens, not millions. Real reason
to fix is consistency, not throughput.

Caveat on the fix: the reviewer's proposed
`.sort(+MaterialCategory.name)` is byte-order (case-sensitive) unless a
collation is attached. The current Python sort is case-insensitive via
`.name.lower()`. A straight DB-side sort would change ordering for
mixed-case names (e.g., "apple" vs "Banana").

Fix (when next touching these files): switch to
`await MaterialCategory.find(...).sort(+MaterialCategory.name).to_list()`
**with a collation** `{locale: "en", strength: 2}` so case-insensitive
order is preserved. Same shape for `MaterialUnit`. If attaching a
collation is awkward via Beanie, leave the Python sort — clarity beats
a half-done DB push-down.

---

## 2026-04-25 review (configurable divisions session)

Findings from `/code-review` after migrating Work Item divisions from a
hardcoded `EstimateDivision` enum to a per-company configurable list
(see [`plans/configurable-divisions.md`](plans/configurable-divisions.md)).
Zero CRITICAL, one HIGH (pre-existing file size), three MEDIUM, three LOW.

### 64. [MEDIUM] WorkItem divisions fetch swallows errors silently
**File**: [portal/src/components/estimates/WorkItemInlineContent.tsx:73](../../portal/src/components/estimates/WorkItemInlineContent.tsx)
**Severity**: MEDIUM

`.catch(() => setDivisions([]))` hides API failures. If the divisions
endpoint is down, users see an empty dropdown with no signal whether
it's a transient failure or just a freshly-created company. Mirrors the
pre-existing rate-cards pattern, so consistent — but support has no
breadcrumb when this fires.

Fix: log via `console.error` (or a shared error reporter if one exists
later) before the empty fallback. Apply the same change to the
rate-cards `.catch` for consistency.

### 67. [LOW] `PydanticObjectId(company)` returns 500 on garbage input
**File**: [platform/routers/divisions.py:44](../../platform/routers/divisions.py)
**Severity**: LOW

A malformed `?company=xyz` query raises `bson.errors.InvalidId` →
unhandled → 500 instead of a clean 422. Mirrors `material_categories`
and `material_units`. Pre-existing pattern; defer.

Also surfaced 2026-05-13 in the hodgepodge `/code-review` pass against
`platform/routers/estimates.py` — the new `get_analytics` route and the
adjacent list endpoint both call `PydanticObjectId(company)` and share
the same 500-on-garbage-input gap. Fold both into the cross-router fix
below.

Fix: wrap in try/except → `HTTPException(422, "Invalid company id")`,
or factor a Pydantic dependency that validates ObjectIds and use it
across all `?company=` query routers (divisions, material_categories,
material_units, estimates list, estimates analytics).

### 68. [LOW] `backfill_divisions.py` uses broad `except Exception`
**File**: [platform/scripts/db/backfill_divisions.py:54](../../platform/scripts/db/backfill_divisions.py)
**Severity**: LOW (script context, not a service handler)

The script intentionally swallows per-company exceptions to keep going
through the company list, then reports failures and exits non-zero.
Acceptable for a one-off backfill — flagging only because spec calls
broad excepts CRITICAL by default. No action expected unless the script
gets reused for repeated migrations.

### 69. [LOW] Bootstrap services log nothing on success
**Files**: [platform/services/division_bootstrap.py](../../platform/services/division_bootstrap.py),
[platform/services/material_category_bootstrap.py](../../platform/services/material_category_bootstrap.py),
[platform/services/material_unit_bootstrap.py](../../platform/services/material_unit_bootstrap.py)
**Severity**: LOW

All three bootstrap helpers run silently on success. The wrapper in
`company_service.py` does `logger.exception(...)` on failure, so
failures are observable, but successful seeding leaves no audit trail.
Useful diagnostic when investigating "why does this company not have X"
questions.

Fix (low value, low effort): emit `logger.info("Seeded N {resource}
templates for company %s", company_id)` from each bootstrap function.

## 2026-04-25 review (configurable material units session)

### 70. [MEDIUM] Missing type hints in `backfill_material_units.py` helpers
**File**: [platform/scripts/db/backfill_material_units.py:50, 68](../../platform/scripts/db/backfill_material_units.py)
**Severity**: MEDIUM (script context, not production code)

`remap_materials_for_unit(company_id, old_unit_id, new_unit_id)` and
`migrate_company(company)` lack annotations. The divisions backfill set
the same precedent, but for consistency with the model APIs these would
be more self-documenting as
`remap_materials_for_unit(company_id: PydanticObjectId, old_unit_id: PydanticObjectId, new_unit_id: PydanticObjectId) -> int`
and `migrate_company(company: Company) -> dict`.

### 71. [MEDIUM] Sequential `material.replace()` per remap is slow at scale
**File**: [platform/scripts/db/backfill_material_units.py:60](../../platform/scripts/db/backfill_material_units.py)
**Severity**: MEDIUM (performance, fine for current scale)

`remap_materials_for_unit` iterates materials and calls
`await material.replace()` one at a time, so the cost is roughly
`O(companies × renamed_units × materials_per_company)`. The 2026-04-25
production run touched 191 materials in seconds; at 10k+ materials per
company this would hurt.

Fix (if reused): batch via
```python
Material.find_many({"company": company_id, "sizes.unit": old_unit_id}).update_many(
    {"$set": {"sizes.$[el].unit": new_unit_id, "updated_at": now}},
    array_filters=[{"el.unit": old_unit_id}],
)
```
Skips the `before_event` hook, so set `updated_at` explicitly.

### 72. [LOW] `getCategoryName` / `getUnitName` re-allocated each render
**File**: [portal/src/pages/MaterialsPage.tsx:183-193](../../portal/src/pages/MaterialsPage.tsx)
**Severity**: LOW (pre-existing pattern; not introduced by the
configurable-units change)

Both helpers are defined in the component body, so they're new function
references on every render. No memoized child currently depends on
referential equality, so this is purely cosmetic — flagging only because
the same lookup pattern shows up across `MaterialsPage`,
`AddMaterialGapDialog`, and the (eventual) inventory drawer. A shared
`useMemo`-wrapped lookup hook would centralise the cache.

---

## 2026-04-26 review (rate-card unit dropdown + default seeding session)

MEDIUM and LOW residuals from the `/code-review` pass after the rate-card
unit Literal, dropdown, Effort Calculator column, JSON-fixture seeding, and
on-signup bootstrap landed. The HIGH finding from that pass (missing
`aria-label`s on the rate-card row inputs) was fixed in the same session.

### 73. [MEDIUM] N+1 `find_one` inside bootstrap loops
**File**: [platform/services/rate_card_bootstrap.py:48-54](../../platform/services/rate_card_bootstrap.py)
**Severity**: MEDIUM
**Why it's MEDIUM, not HIGH**: matches the existing pattern in
`division_bootstrap.py`, `material_category_bootstrap.py`, and
`material_unit_bootstrap.py`. Volume is small today (6 templates × 12
companies = 72 queries during backfill), but the cost compounds as more
bootstrappers join the chain.

Fix: pre-load existing names with one query and check membership in the
loop, e.g.
```python
existing_names = {
    rc.name for rc in await RateCard.find({
        "company": normalized_company_id,
        "name": {"$in": [t["name"] for t in templates]},
    }).to_list()
}
```
Apply consistently across all `*_bootstrap.py` modules in one pass to keep
them aligned.

### 74. [MEDIUM] JSON re-parsed on every `bootstrap_company_rate_cards` call
**File**: [platform/services/rate_card_bootstrap.py:20](../../platform/services/rate_card_bootstrap.py)
**Severity**: MEDIUM
The loader reads + parses `default_rate_cards.json` on every call. Cheap
individually, wasteful in the backfill loop (12× during the recent
backfill, more whenever a new bootstrapper is added).

Fix: `@functools.lru_cache(maxsize=1)` on `load_default_rate_card_templates`,
or assign at module import. Tests already monkey-patch
`DEFAULT_RATE_CARDS_PATH`, so any cache must be invalidated in those tests
(via `cache_clear()` in a fixture).

### 75. [MEDIUM] `CardItem.easy/standard/hard` unbounded
**File**: [platform/models/rate_card.py:26-28](../../platform/models/rate_card.py)
**Severity**: MEDIUM
**Why it's MEDIUM**: pre-existing — predates the unit-Literal change. But
the dropdown work tightened `unit` validation, and the same rigour should
apply to the rate fields: today negative, zero, NaN, and Infinity all pass
Pydantic. Frontend rejects negatives (`min="0"`); a direct API client or
malformed `default_rate_cards.json` can poison data and break effort
calculations (division by zero on a row's chosen difficulty).

Fix: `easy: float = Field(..., gt=0)` (and same for `standard`/`hard`).
Will require touching test fixtures that pass `0` and updating the frontend
helper text. Coordinate with whoever owns the Effort Calculator's
zero-handling so we don't change semantics underneath.

### 76. [MEDIUM] Backfill swallows per-company exceptions
**File**: [documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py:32](../../documentation/development/migration_scripts/seed_rate_cards_for_existing_companies.py)
**Severity**: MEDIUM
The backfill catches every `Exception` per company and prints a one-liner.
A misconfigured DB (auth failure, etc.) scrolls past silently as N
identical errors. Pre-existing convention across migration scripts.

Fix: differentiate infrastructure errors (`ServerSelectionTimeoutError`,
`OperationFailure`) from per-document validation errors and let the former
propagate. Apply the same shape to other migration scripts in one pass.

### 77. [MEDIUM] `SEED_COMPANY_ID` is a magic constant tied to live data
**File**: [documentation/development/migration_scripts/export_default_rate_cards.py:26](../../documentation/development/migration_scripts/export_default_rate_cards.py)
**Severity**: MEDIUM
The hard-coded ObjectId is documented in the module docstring but not
guarded. If this script is re-run after the seed company evolves, it
silently overwrites `default_rate_cards.json`.

Fix: either accept the company id as a CLI arg with no default, or refuse
to overwrite an existing `default_rate_cards.json` without a `--force`
flag. Low priority since the script is clearly labeled "one-shot".

### 78. [LOW] Validation error message doesn't list allowed units
**File**: [portal/src/lib/rateCards.ts:28](../../portal/src/lib/rateCards.ts)
**Severity**: LOW
`"Item ${i+1}: Unit must be one of the allowed values."` is unactionable
for any user who hits it (which shouldn't happen via the UI, but could from
a stale tab or a copy-paste).

Fix: include the list:
```ts
` Item ${i + 1}: Unit must be one of: ${RATE_CARD_UNITS.join(", ")}.`
```

### 79. [LOW] `load_default_rate_card_templates` returns loose `list[dict]`
**File**: [platform/services/rate_card_bootstrap.py:13](../../platform/services/rate_card_bootstrap.py)
**Severity**: LOW
Returning `list[dict]` loses the schema; callers can't tell what keys
exist without reading the validator.

Fix: define `RateCardTemplate` and `CardItemTemplate` as `TypedDict`s in
the same module and return `list[RateCardTemplate]`. Pure ergonomics — no
runtime change.

---

## 2026-04-26 `/code-review` pass (HIGH cleanup session — #19, #38, #47, #63)

Findings from the `/code-review` after the four HIGH refactors landed
(`_classify_with_rules` extraction, `_handle_get_work_item` extraction,
`_enrich_address_fields_with_google` shared helper, SettingsPage tab
extractions). The HIGH (`_load_estimate_for_read` / `_load_estimate_for_update`
both over 50 lines, originally filed as #80) was fixed in the same
session via the shared `_estimate_load_error_envelope` and
`_coerce_company_oid` helpers — that fix also resolved the
`_load_estimate_for_read` and `_load_estimate_for_update` portions of
entry #20. Two MEDIUM (#81, #84) and three LOW (#82, #83, #85) remain
below.

### 82. [LOW] `alert(...)` for save errors in 3 settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx) (`handleSaveDivision`),
[portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx) (`handleSaveUnit`),
[portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx) (`handleSaveCategory`)
**Severity**: LOW (UX inconsistency)

The save handlers surface API errors via browser `alert(...)`. The delete
flows in the same files render an inline error inside the modal instead.
Pattern was preserved verbatim from the pre-extraction `SettingsPage.tsx`
during the 2026-04-26 #63 fix — pre-existing, not introduced.

Fix: lift the error into a `formError` state inside the dialog, displayed
above the action buttons. Consistent with the delete-modal pattern in the
same files. Theme-adjacent to entry #44.

### 83. [LOW] Inconsistent ID extraction across settings tab components
**Files**: [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx),
[portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx),
[portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
**Severity**: LOW (style)

The new tab components use the non-null assertion operator
(`editingDivision.id!`, `categoryToDelete!.id!`) when calling the API.
The sibling `RateCardsTab.tsx` instead uses `extractEntityId(rc)` from
`lib/entityId`, which handles the union shape from the API response
without requiring a non-null assertion. Pattern was preserved verbatim
during the 2026-04-26 #63 extraction — pre-existing, not introduced.

Fix: switch to `extractEntityId(...)` for consistency with `RateCardsTab`.
~6 call sites across the three files.

## 2026-04-26 mypy baseline (themed entries from #3)

All themed entries (#86, #87, #88, #89, #90, #91, #92, #93) were folded into the #3 mypy baseline canonical. See `## Closed`.

---

## Deferred — not on the fix list

These were considered and intentionally NOT filed as follow-ups:

- **CORS wildcard in dev**: already guarded — production fail-fast landed in
  the critical batch. The wildcard fallback in development is intentional.
- **`ChangeLogEntry` lacking tenant scope**: intentionally global; documented
  in the model's docstring.
- **Firebase/Brevo credentials in `.env`**: correct pattern. Only the
  service-account-key on disk was problematic, and that was rotated.
- **Duplicate `getEstimateDivision` in DashboardPage + EstimatesTable**
  (2026-04-22 third review): verified and rejected. No such function
  exists anywhere in `portal/`. Division aggregation lives only in
  `DashboardPage.tsx:169-184` as a `useMemo`; `EstimatesTable.tsx` is a
  generic props-driven table with no division logic. No `divisionBadge.ts`
  file exists. Reviewer appears to have described a state of the code
  that is not present in this repo.

---

## 2026-04-26 `/code-review` pass (post-#4 material + routers extractions)

Findings from the `/code-review` after the material-service handler
extractions (`_handle_create_material`, `_handle_get_material`,
`_handle_delete_material`, `_handle_list_materials`) and the
`routers/agent_helpers/` package landed (`text_helpers.py`,
`estimate_update.py`, `fuzzy_confirmation.py`). Zero CRITICAL, three
HIGH, three MEDIUM, two LOW. The HIGH items are all function-size
inheritances from the original closures — they came over verbatim during
the extraction and remain as the next iteration's target.

### 97. [MEDIUM] `text_helpers` import uses private aliases at the call site
**File**: [platform/routers/agents.py:54-56](../../platform/routers/agents.py)
**Severity**: MEDIUM (style)

`routers/agent_helpers/text_helpers.py` exports
`is_affirmative_text` / `is_negative_text` as public functions. The
caller imports them with leading-underscore aliases (`as
_is_affirmative_text`) to avoid touching ~10 call sites inside
`orchestrate_agent_endpoint`. Hides the public/private boundary at the
call site.

Fix: rename the call sites to drop the underscore prefix and remove
the `as` clause. Mechanical, ~10 substitutions.

---

## 2026-04-27 review (US address parsing + estimate navigation session)

### 100. [LOW] Defensive `|| canEdit` clause in estimate-page row visibility is dead today
File: `portal/src/pages/NewEstimateWithActivityPage.tsx:879`
**Severity**: LOW

```tsx
{isEditMode && estimate && (allowedTransitions.length > 0 || canEdit) && (
```

`canEdit` is true only for `draft`/`review`. Both statuses have ≥2
transitions even after the non-admin Approve filter, so
`allowedTransitions.length > 0` is always true when `canEdit` is true.
The `|| canEdit` clause is dead today.

Keeping it is defensible — it documents intent ("show the row when we have
either buttons or a Save to render") and the cost is one boolean OR. But
if `isEditableStatus` or `TRANSITIONS_BY_STATUS` ever changes such that
the implication breaks, the clause would silently start mattering, which
is the kind of thing that surfaces only via a runtime regression.

Fix: either drop `|| canEdit` or add a one-line comment noting the
defensive intent. No runtime impact today.

### 101. [LOW] US-address regex could match noisy mid-message text
File: `platform/agents/property/service.py:457-480`
**Severity**: LOW

The new pattern matches anywhere in the message:
`\d{1,6}` + 3-120 chars + `,` + city + `,` + 2-letter state + space + ZIP.
A free-form sentence like "I owe 23456 dollars, paid via bank, NY 11768
reference" technically matches and would produce spurious `street`/`city`/
`prov_state`/`postal_zip` extractions. The same false-positive surface
exists in the pre-existing Canadian regex variants in this file, so it's
consistent — but worth noting.

Fix: acceptable for now. The downstream Google address-enrichment step or
LLM extraction usually overrides nonsense. If false positives surface in
production, anchor the pattern to the start of a line or after a verb hint
(`at|address[: ]`).

---

## 2026-04-28 `/code-review` pass (Templates resource)

After implementing the Templates CRUD page (model + router + dialog + list).
HIGH (`PUT /templates/id/{id}` allowed cross-tenant move via the request body)
and MEDIUMs (missing `role="alert"` on the dialog error banner; race between
page mount and "New Template" click before company defaults loaded) were
fixed in the same change. The four LOW findings below remain.

### 102. [LOW] `duplicate` insert lacks 409 fallback
File: `platform/routers/templates.py:120-136`
**Severity**: LOW

`_next_copy_name` does a `find_one` for the candidate name, then
`copy.insert()`. Between those two awaits, another caller could insert the
same name, and the unique `(company, name)` index would surface a
`DuplicateKeyError` to the client as a 500 instead of a clean 409.

Fix: wrap the insert in `try/except DuplicateKeyError` and either retry
once with the next `(copy N)` suffix or raise 409. Low likelihood — the
window is sub-millisecond and same-user duplicate spam is the only realistic
trigger.

### 103. [MEDIUM] `delete_template` returns 200 on non-existent id
File: `platform/routers/templates.py:158-160`
**Severity**: MEDIUM

```python
if not template:
    return {"message": "Template not found"}
```

200 with a body that says "not found" is misleading. Mirrors
`routers/labours.py:336-338`, so it's a project convention rather than a
regression. If we ever standardize, fix all four (labours, templates, etc.)
together.

Fix: change to `raise HTTPException(404, "Template not found")` and update
the parallel routers in the same PR.

### 104. [LOW] `TemplateDialog` captures `initialName` only on mount
File: `portal/src/components/estimates/TemplateDialog.tsx:36`
**Severity**: LOW

`useState(initialName ?? "")` reads `initialName` only on first render.
Switching from create-mode to edit-mode without remount would leave `name`
empty. Currently safe because `TemplatesPage.tsx` passes `key={dialogKey}`
and gates with `{isFormOpen && <TemplateDialog ... />}`, forcing a fresh
mount each time.

Fix: only required if either the key or the gate is removed. If so, sync
`name` via a `useEffect` on `initialName` change.

### 105. [LOW] Templates page re-fetches `/companies/{id}` on every mount
File: `portal/src/pages/TemplatesPage.tsx:60-74`
**Severity**: LOW

Every visit to `/templates` re-fetches the company doc just to read profit
margin / overhead / labor burden / tax. Other pages
(`NewEstimateWithActivityPage`, `PeoplePage`) do the same, so it's a
codebase-wide convention.

Fix: hoist company defaults to a context provider or React Query cache in
a follow-up that addresses all the consumers at once. Not worth a one-page
change.

---

## 2026-04-28 `/code-review` pass (Use Template on estimate page)

After wiring `UseTemplateDialog` + the split-button on the estimate detail
page. Two MEDIUMs (search input missing `aria-label`; `setExpandedWorkItemIndex`
read stale closure of `workItems.length`) were fixed in the same change.
The deferred MEDIUM and two LOWs remain.

### 106. [MEDIUM] `autoFocus` on dialog open may interrupt screen-reader announcements
File: `portal/src/components/estimates/UseTemplateDialog.tsx:84`
**Severity**: MEDIUM

`autoFocus` on the search input pulls focus immediately when the dialog
opens. On some assistive tech this races with the modal's open
announcement, so the user hears a partial label. Same pattern is used in
several other dialogs (e.g. `TemplateDialog.tsx`), so it's a codebase-wide
concern, not specific to this dialog.

The standard fix is to focus the modal container (or first heading) on
open and let the user Tab into the search field. That requires changes
inside `components/common/Modal.tsx` and ripples to every dialog. Not
worth a one-dialog fix — defer until an a11y pass that addresses Modal
focus management as a single change.

Fix: address as part of a future Modal a11y refactor; do not patch
per-dialog.

### 107. [LOW] Inventory-gaps panel does not reflect template-inserted work items until save
File: `portal/src/pages/NewEstimateWithActivityPage.tsx:418-424`
**Severity**: LOW

`inventoryGaps` is memoized off `estimate` (the server snapshot), not
`workItems` (the editor state). When a user inserts a template, any
unmatched materials/activities the template carries don't surface in the
gaps panel until the estimate is saved and reloaded. Same behavior as
`handleAddWorkItem` — pre-existing limitation, not a regression — but
worth knowing because templates are more likely to carry unmatched items
than from-scratch work items.

Fix: rebuild gaps from `workItems` rather than `estimate.job_items` so
in-progress edits surface immediately. Out of scope for the Templates
feature; revisit if the gaps panel becomes a primary editing surface.

### 108. [LOW] `templates.find()` could return undefined on stale state
**Severity**: LOW
File: `portal/src/components/estimates/UseTemplateDialog.tsx:51`

If templates were re-fetched mid-confirm and the list shrank,
`templates.find((t) => getEntityId(t) === selectedId)` returns undefined.
The `if (chosen)` guard handles it correctly (the OK click silently does
nothing), so the path is safe. Could improve UX by clearing `selectedId`
when it disappears from the list — but with the dialog gated by
conditional mount, the templates list never refreshes mid-session.

Fix: none required while the dialog is mounted-on-open. If we ever switch
to keep-mounted-with-refresh, add `useEffect` to clear `selectedId` when
it disappears from `templates`.

---

## 2026-04-29 review (improvements.md consolidation)

Items consolidated from `documentation/development/improvements.md`. The
".gitignore `*-key.json` is broad" suggestion from that file was dropped as
already covered by #45 (which explicitly notes the `*-key.json` sibling
pattern is functionally fine).

### 110. [LOW] `FeedbackPanel` error message has no live-region announcement
**File**: [portal/src/components/common/FeedbackPanel.tsx:169](../../portal/src/components/common/FeedbackPanel.tsx)
**Severity**: LOW (accessibility)

The submission-error div is a plain `<div className="text-xs text-red-600">{error}</div>`.
Screen readers don't announce it when it appears, so a visually impaired
user gets no audible signal that submission failed — they have to walk the
DOM to find out why nothing happened.

Fix: add `role="alert"` (or `aria-live="polite"`) to the error div. The
same applies to `ChangeLogPanel.tsx:166`, which uses the identical
pattern.

### 112. [LOW] Replace `isMountedRef`/`fetchTokenRef` race-guards with `AbortController`
**Files**: [portal/src/components/common/ChangeLogPanel.tsx](../../portal/src/components/common/ChangeLogPanel.tsx), [portal/src/components/common/FeedbackPanel.tsx](../../portal/src/components/common/FeedbackPanel.tsx), [portal/src/api/client.ts](../../portal/src/api/client.ts)
**Severity**: LOW (refactor)

Both panels copy a manual race-guard pattern (`isMountedRef`,
`submitTokenRef` / `fetchTokenRef`, post-await staleness checks) to drop
results from superseded fetches. The cleaner shape is `AbortController`
+ `signal`, but it requires changing the shared API client.

Fix:
1. Teach `apiRequest` in `portal/src/api/client.ts` to accept an
   `AbortSignal` and pass it through to `fetch`.
2. Migrate `ChangeLogPanel` and `FeedbackPanel` together — abort the
   in-flight request on unmount or on a new submit/fetch, then drop the
   ref-based guards.

Migrate both call sites in the same PR so the pattern is consistent.

### 113. [LOW] Test bypass `FIREBASE_AUTH_DISABLED=true` hides unauthenticated paths
**File**: [platform/tests/conftest.py:7](../../platform/tests/conftest.py)
**Severity**: LOW (testing infra)

The whole suite runs with `os.environ.setdefault("FIREBASE_AUTH_DISABLED", "true")`,
so a test that hits a router without `X-Test-Email` doesn't actually
exercise the Firebase verification path — it just routes through the
test bypass. Endpoints that *should* 401 for missing auth are not
verifying that behavior.

Fix: add a fixture that temporarily clears (or sets to `"false"`) the
flag for the duration of one test, so router-level auth dependencies are
genuinely exercised. Apply it to at least one endpoint per router family
(feedback, change-logs, companies). Treat as shared testing-infra work
rather than per-PR add-ons.

---

## 2026-04-29 `/code-review` pass (public Maple widget)

Hygiene findings from the post-implementation review of the public Maple
Q&A widget (marketing site). HIGH `/code-review` items #3, #5, and #6
landed in the same session; these are the residual MEDIUM/LOW items.

### 114. [LOW] Unused `Optional` import in `refusal.py`
**File**: [platform/agents/maple_public/refusal.py:21](../../platform/agents/maple_public/refusal.py)
**Severity**: LOW (hygiene)

`from typing import Optional` is imported but no symbol from this module
references it. (Was used before the instructional-question short-circuit
landed and the function signature changed.)

Fix: drop the line.

### 115. [MEDIUM] Mixed string-vs-regex tuples in `refusal.py`
**File**: [platform/agents/maple_public/refusal.py:27-55](../../platform/agents/maple_public/refusal.py)
**Severity**: MEDIUM (maintainability)

`_ACTION_VERBS` and `_DOMAIN_NOUNS` mostly hold plain strings, but a few
entries embed raw regex fragments (`"set\\s*up"`, `"job\\s*site"`,
`"team\\s*member"`, `"work\\s*item"`, `"rate\\s*card"`). The values are
joined into a `|` alternation and never `re.escape`d. A maintainer
adding a literal noun with a regex metacharacter (e.g. a hyphen, parens,
or a dot) would silently get the wrong match.

Fix: either (a) add a one-line comment near the tuples saying "values
are raw regex fragments — do NOT pre-escape", or (b) split into two
tuples (literal vs regex), `re.escape` the literal one before joining.

### 116. [LOW] Duplicated "I'm not sure" fallback copy in `service.py`
**File**: [platform/agents/maple_public/service.py:90-91, 194-198](../../platform/agents/maple_public/service.py)
**Severity**: LOW (maintainability)

The "I'm not sure — that's not something I can answer from here. Sign
up at {signup_url} and I can help you with that in the app." line lives
both inside the LLM strict prompt (rule 5) and as the Python-side
fallback when the LLM returns empty content. They will drift over time.

Fix: extract a small helper or module constant that produces the
phrasing; reuse from both sites.

### 117. [LOW] `_LLMHolder` class is more scaffolding than the use needs
**File**: [platform/agents/maple_public/service.py:99-127](../../platform/agents/maple_public/service.py)
**Severity**: LOW (style)

The lazy-init holder class plus `set_llm_for_tests` is more structure
than the single-LLM use needs. A module-level
`_llm: Optional[ChatOpenAI] = None` plus a getter and a test-only
setter would be flatter.

Fix: optional refactor; not blocking. Keeps the test injection path
clean either way.

### 118. [MEDIUM] Hand-rolled `import.meta` cast in widget API client
**File**: [website/widget/api.ts:25-27](../../website/widget/api.ts)
**Severity**: MEDIUM (DX)

`(import.meta as { env?: ... }).env?.VITE_PUBLIC_API_URL` works but
exists because the website project doesn't pull in Vite's client
types. Every future env-var lookup in the widget will repeat the cast.

Fix: add a one-line `website/widget/vite-env.d.ts` containing
`/// <reference types="vite/client" />`. Drop the cast and read
`import.meta.env.VITE_PUBLIC_API_URL` directly.

### 119. [LOW] URL build via string concatenation in widget API client
**File**: [website/widget/api.ts:36](../../website/widget/api.ts)
**Severity**: LOW (robustness)

`resolveApiUrl().replace(/\/+$/, "") + "/public/maple/ask"` hand-rolls
the join. A misconfigured env (e.g. trailing whitespace, missing
scheme, accidental query string) builds a broken URL silently.

Fix: use `new URL("/public/maple/ask", base)`. Surface a clear error
if the base is malformed.

### 120. [LOW] Unused CSS variable in widget palette
**File**: [website/widget/widget.css:6](../../website/widget/widget.css)
**Severity**: LOW (hygiene)

`--mw-bg-alt: #3b3f5c;` is declared but never referenced.

Fix: remove the line.

### 121. [LOW] Implicit "welcome bubble has id 0" coupling
**Files**: [website/widget/MapleWidget.tsx:31, 69, 108](../../website/widget/MapleWidget.tsx)
**Severity**: LOW (style)

The widget treats the welcome bubble specially in two unrelated places:
- Line 69: `bubbles.filter((b) => b.id !== 0)` — strip the welcome
  before building the API history.
- Line 108: `showStarterChips = bubbles.length === 1 && !pending` —
  show starter chips only on initial state.

Both rely on the convention that the welcome bubble has id 0 and is
the only bubble at start. A rename / re-numbering would have to touch
both spots.

Fix: tag the welcome bubble with a flag (`isWelcome: true`) on the
`Bubble` type, or move the welcome state into a separate variable
outside the `bubbles` array.

---

## 2026-04-30 `/code-review` pass (HELP intent → users-guide refactor)

Scope: shared `agents.maple_guide` responder, `HelpHandler` rewrite,
public-widget refactor, orchestrator interrogative→guide fallback,
extracted `formatOrchestratorReply` portal utility.

### 123. [MEDIUM] `formatOrchestratorReply` mutates input parameter
**File**: [portal/src/lib/orchestratorReply.ts:54](../../portal/src/lib/orchestratorReply.ts)
**Severity**: MEDIUM (mutation)

Sets `result._outOfScope = true` so the caller can read it. Inherited
from the original closure inside `PortalLayout.tsx`, copied verbatim
during the extraction. The extraction was the right time to fix this
contract; we kept it for parity instead.

Fix: return `{ text, outOfScope }` (or a tuple). Caller assigns
`result._outOfScope = outOfScope` explicitly. Cleaner contract; easier
to test side effects independently.

---

## 2026-05-01 `/code-review` pass (Estimate detail UI overhaul + Work Item dialog refactor)

Items below were called out across two `/code-review` passes during a UI
overhaul of `NewEstimateWithActivityPage.tsx` (info/notes/status/docs
icons, auto-saving description+property, Documents dropdown, status
dropdown, Work Items table redesign, and the Work Item editor refactor
from inline expansion to a Cancel/Save dialog).

The two HIGH items addressed in-session:
- Dialog now stays open during save with a "Saving…" state and an
  inline error banner; revert path on failure.
- Material/role gap resolvers fold their resolution into
  `workItemDraft` when the dialog is open, bumping `workItemDialogKey`
  to remount `WorkItemInlineContent` so the change is visible. The Save
  Work Item button is now the persistence path for those edits.


### 131. [MEDIUM] `saveError` displayed far from origin
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM

`saveError` (description / property auto-save failures) is rendered in
the Work Items header; users blurring the description at the top of
the page won't see the message if scrolled. Work item dialog now uses
its own `workItemDialogError` so this affects only description and
property.

Fix: render `saveError` adjacent to the field that failed, or use a
toast. Simplest: append a small inline error under the description /
property when their auto-save fails.

### 132. [MEDIUM] Description read-only color is dead CSS
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM

`className={'... ${canEdit ? "..." : "bg-gray-50 ... text-gray-500"} ${!description ? "text-gray-400" : "text-gray-900"}'}`.
The trailing ternary always wins over the `!canEdit` `text-gray-500`
because Tailwind utilities at the same specificity resolve by
stylesheet source order, not className order. Read-only state ends up
visually identical to editable.

Fix: collapse to one expression:
`canEdit ? (description ? "text-gray-900" : "text-gray-400") : "text-gray-500"`.

### 135. [MEDIUM] Description "button" wraps multi-line content
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (accessibility)

The read-only description div has `role="button"` and `tabIndex={0}`,
so screen readers announce the entire description as the button's
accessible name. Fine for short text, awkward for long ones.

Fix: add `aria-label="Edit description"` so the announced label is
concise; the visible text remains content.

### 136. [MEDIUM] Docs menu items missing `role="menuitem"`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (accessibility)

The status dropdown items use `role="menuitem"`; the docs dropdown's
`<a>` / `<button>` items inside `role="menu"` do not. Inconsistent
ARIA.

Fix: add `role="menuitem"` to each item inside the docs `<li>`.

### 139. [LOW] Pre-existing `printWindow.document.write` deprecation hint
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW

TS `6387` hint at line ~545 in `handleChecklistPdfDownload`. Predates
this session. Replace with `printWindow.document.body.innerHTML = …`
or build the document via DOM APIs.

---

## 2026-05-01 `/code-review` pass (Green table headings + auto-create estimate)

### 142. [LOW] Table heading weight drift (`font-medium` → `font-semibold`)
**Files**:
- [portal/src/components/common/EstimatesTable.tsx](../../portal/src/components/common/EstimatesTable.tsx)
- [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx)
- [portal/src/pages/PeoplePage.tsx](../../portal/src/pages/PeoplePage.tsx)

**Severity**: LOW

The 2026-05-01 "apply emerald-100 heading color" change also bumped
`<th>` font weight from `font-medium` to `font-semibold` while
recoloring. The user only asked for a color change. Other tables in
the app still use `font-medium` headers, so this is now inconsistent.

Fix: pick one and apply globally. Either revert these three files to
`font-medium`, or sweep the rest of the codebase up to `font-semibold`.

---

## 2026-05-01 review (Work Item dialog / Estimate page mobile-responsiveness — consolidated from `plans/portal-ui-refactor-followups.md`)

The two HIGH items from this pass (file size of `WorkItemInlineContent.tsx`,
fragile modal stacking) were addressed in the same change set; the items
below are MEDIUM / LOW and were logged for later.

### 144. [MEDIUM] Alternating row color computed inline twice
**Files**:
- [portal/src/components/estimates/MaterialsTable.tsx](../../portal/src/components/estimates/MaterialsTable.tsx)
- [portal/src/components/estimates/WorkItemInlineContent.tsx](../../portal/src/components/estimates/WorkItemInlineContent.tsx) (Activities table)

**Severity**: MEDIUM

`const rowBg = idx % 2 === 1 ? "bg-emerald-50" : "bg-white"` is
duplicated across two `map()` bodies. Logic is correct (works around
the activities table's sub-row Fragment shifting `:nth-child(even)`
parity) but the rule is in two places.

Fix: extract a shared `getRowBg(idx: number)` helper into a small
utility module or co-locate it where both tables can import it.

### 146. [MEDIUM] EffortCalculator mobile dropdown initial-render flicker
**File**: [portal/src/components/estimates/EffortCalculatorDialog.tsx](../../portal/src/components/estimates/EffortCalculatorDialog.tsx)

**Severity**: MEDIUM

When the modal opens with `selectedCardId === null` and
`rateCards.length > 0`, the mobile `<select>` shows the first card's
name while the right panel still reads "Select a rate card to begin"
until the parent useEffect fires. Brief visual mismatch.

Fix: initialise `selectedCardId` synchronously via `useState(() => …)`
reading the first rate card so there's no null window. Keep the
existing useEffect for the open/close transitions.

### 147. [LOW] `MaterialsPage` mobile card popup-clip fix is scoped
**File**: [portal/src/pages/MaterialsPage.tsx](../../portal/src/pages/MaterialsPage.tsx)

**Severity**: LOW

The previous `overflow-hidden` clip was fixed by removing
`overflow-hidden` from the card and adding `rounded-b-xl
overflow-hidden` to the expanded sizes section. This works for the
current popup but if a future popup is added inside the expanded sizes
section it'll be clipped again.

Fix: if/when that case appears, switch popups to render via React
portal so they aren't subject to ancestor clipping.

### 148. [LOW] Three near-identical settings tabs
**Files**:
- [portal/src/components/settings/MaterialCategoriesTab.tsx](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
- [portal/src/components/settings/MaterialUnitsTab.tsx](../../portal/src/components/settings/MaterialUnitsTab.tsx)
- [portal/src/components/settings/DivisionsTab.tsx](../../portal/src/components/settings/DivisionsTab.tsx)

**Severity**: LOW

~95% identical markup and state machinery. Each round of UI work
(icon buttons, Actions column width, Name column width) had to be
applied three times. Divergence risk grows.

Fix: extract a generic `<NameDescriptionResourceTab>` component
parameterised by `api`, singular/plural labels, and any tab-specific
extras.

> Note: the seventh portal item ("`NewEstimateWithActivityPage.tsx` is
> 1,990+ lines") duplicates existing finding [#137](#137-newestimatewithactivitypagetsx-at-1900-lines)
> and is tracked there.

---

## 2026-05-02 `/code-review` pass (post-#143/#130/#133/#138 batch)

### 149. [LOW] `lastSavedDescriptionRef` / `lastSavedTitleRef` initial-value window
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW

The two refs added by #133 (and the title fix that landed alongside)
are initialized to `""` and only seeded to the canonical server value
inside the estimate-load `useEffect`. There is a brief window between
mount and load where the ref is stale.

In practice no save can fire during that window — `autoSaveField`
returns early when `!estimateId`, and the title/description fields
are not interactive until the page renders post-load — so this is
theoretical only. Worth noting for future maintainers who might
introduce a save path that bypasses those guards.

Fix: optional. Either fold the seeding into the `useState` initializer
(reading from a route loader), or leave a stronger inline contract
comment near the ref declarations.

## 2026-05-02 `/code-review` pass (post-#12/#109/#150/#151/#152 batch)

### 153. [LOW] `_PolicyShortCircuit.response` field name overloaded
**File**: [platform/agents/orchestrator/service.py:188](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (naming clarity)

Found by `/code-review` 2026-05-02 after the #12 extraction landed. The
`response` field on `_PolicyShortCircuit` carries either a refusal
message (negative case — bulk-delete / equipment / category-management)
or `None` (positive `list_material_categories` case, where
`_build_short_circuit_response` hardcodes `"I can help you with that."`).
The polymorphic meaning isn't obvious from the field name and the class
docstring doesn't mention it.

Fix: either rename to `clarification` to match the legacy 5-tuple's
last-position semantics in `_classify_with_rules`, or add a one-line
note in the docstring: "None for positive routings; refusal copy for
negative routings." Cosmetic only — behavior is correct and tested.

### 154. [LOW] `_TopicFlags.property` field name shadows Python builtin
**File**: [platform/agents/orchestrator/help_handler.py:38](../../platform/agents/orchestrator/help_handler.py)
**Severity**: LOW (naming clarity)

Found by `/code-review` 2026-05-02 after the #150 split landed. The
`_TopicFlags` dataclass field `property` shadows the `property` builtin
within the dataclass scope. Attribute access (`flags.property`) is
safe, but if anyone later writes a bare `property` reference inside
`help_handler.py` they'll get the boolean instead of the decorator.

Fix: optional. Either accept the shadowing trade-off (current state
keeps symmetry with the other domain flags), or rename every flag to
`is_*` for consistency (`is_property`, `is_contact`, etc.).

---

## 2026-05-02 `/code-review` pass (xfail-wave-2 Phase 2)

### 157. [MEDIUM] Cross-resource transitive join uses two round-trips instead of $lookup
**File**: [platform/agents/property/service.py:1071](../../platform/agents/property/service.py)
**Severity**: MEDIUM (perf hook)

`_properties_with_estimates_referencing` does TWO Beanie queries —
`Estimate.find` to collect property IDs, then `Property.find` with
those IDs. For tenants with thousands of estimates the first query
loads full estimate documents just to read the `.property` field.

Fix: replace with a single Mongo aggregation pipeline:
```python
Estimate.aggregate([
    {"$match": {"company": ..., "<field>": {"$in": ids}}},
    {"$group": {"_id": "$property"}},
    {"$lookup": {"from": "properties", "localField": "_id",
                 "foreignField": "_id", "as": "property"}},
])
```

Defer until perf measurements demand it; current shape is correct
and clear. Worth coupling with a fixture-based perf test.

### 159. [LOW] `agents/cross_resource.py` filters in-Python on full collections
**File**: [platform/agents/cross_resource.py](../../platform/agents/cross_resource.py)
**Severity**: LOW (scaling)

All four `find_X_by_name` helpers load the full collection and filter
in Python. Acceptable for typical company sizes (<1k materials, <100
labour roles, <100 properties) but won't scale to enterprise tenants.

Fix: document the scaling boundary in the module docstring (already
present — "pragmatic for typical company sizes; revisit if a tenant
exceeds ~10k properties"). Future refactor: push substring matching
to MongoDB via `$regex` filters with case-insensitive option.

---

## 2026-05-02 `/code-review` pass (xfail-wave-3 — all three workstreams)

Surfaced after shipping `documentation/development/plans/maple-xfail-wave-3.md`
(partial-bulk delete refusal + material query variants + estimate filters &
drilldowns). Code review found 0 CRITICAL / 0 HIGH; only MEDIUM / LOW
follow-ups below. The `_OPEN_ESTIMATE_STATUSES` hardcoded-strings
fragility was caught and fixed inline during the review (now derived
from `EstimateStatus.{DRAFT,APPROVED,REVIEW,WON}.value`).

### 163. [MEDIUM] Wave 3 file growth — three large agent files grew further
**Files**:
- [platform/agents/material/service.py](../../platform/agents/material/service.py) — 2,560 → 2,659 lines
- [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) — 5,719 → 5,873 lines
- [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py) — 1,712 → 1,830 lines

**Severity**: MEDIUM

Pre-existing condition (all three were already far above the 800-line
CLAUDE.md guideline before Wave 3); this change does not make it
materially worse but contributes ~370 lines across the three files.
Tracked here so the pressure stays visible.

Fix: one of three options for each file —
- Material: extract `_handle_list_materials_for_estimate`, `_handle_get_material`, `_handle_list_materials` into a `material/handlers/` package.
- Estimate: split the 5,873-line file by phase (generation / extraction / CRUD / status-transitions are natural seams).
- Orchestrator: extract `_match_size_scoped_material_op`, `_match_possessive_or_field_targeted`, `_match_cross_resource_query` into `orchestrator/matchers/` modules.

Out of scope for any single feature commit; would warrant its own refactor PR.

### 164. [LOW] `find_estimate_by_code` loads full estimate collection
**File**: [platform/agents/cross_resource.py:97](../../platform/agents/cross_resource.py#L97)
**Severity**: LOW (scaling)

Mirrors the existing `find_properties_by_name_or_address` /
`find_materials_by_name` pattern (in-memory linear scan after loading
the company's full estimate collection). Pragmatic for typical company
sizes; could matter once a tenant exceeds ~1k estimates.

Fix: replace with a Beanie indexed lookup —
```python
return await Estimate.find_one(
    Estimate.company == PydanticObjectId(company_id),
    Estimate.estimate_id == code_text.upper(),
)
```
Requires confirming there's an index on `(company, estimate_id)`; if
not, add one in `database.py:init_db()`.

---

## 2026-05-03 `/code-review` pass (post-#155/#156/#158/#160/#161 batch)

Surfaced after the five-item refactor batch landed. No CRITICAL / HIGH
findings; the four notes below are accepted trade-offs from the batch
itself, logged for visibility so future refactors don't re-discover
the same questions.

All three items in this batch (#165, #166, #167) were folded into the #4 file/function-size canonical. See `## Closed`.

---

## 2026-05-03 `/code-review` pass (Maple FAB + Modal AI-panel awareness)

Findings from the session that introduced `AiPanelContext`, the Modal
backdrop carve-out for the desktop Maple rail, and the bottom-right
floating Sparkles button. The actionable items (decoupling divisions
fetch, FAB ARIA, removing the unused `coverAiPanel` prop) were fixed in
the same change. The items below were deferred.

---

## 2026-05-04 `/code-review` pass (Adjust Work Item Total feature)

Findings from the session that added the "Adjust" pill on the Work Item
Total row, the `AdjustTotalDialog` component, the `original_profit_margin`
field round-trip (frontend type + backend `JobItem`), the
`backCalculateProfitMargin` helper, and the `NumericInput` precision-
preserving blur. The lint error caught during review
(`react-hooks/set-state-in-effect` on `AdjustTotalDialog`) was fixed in
the same change by remounting the dialog via a `key` prop on open. All
items below were deferred.

### 173. [LOW] `<input>` in `AdjustTotalDialog` uses `aria-label`, not a real `<label>`
**Severity**: LOW
`AdjustTotalDialog.tsx:65–73` — the visible "Adjust Amount" text comes
from the modal title (`<h3>`), not from a `<label htmlFor=…>` on the
input. The input has `aria-label="Adjust Amount"`, so screen readers do
announce the field correctly, but there's no clickable visual association
between the heading and the input.

Fix: render an explicit `<label htmlFor="adjust-amount-input">Adjust
Amount</label>` inside the modal body and drop the `aria-label`. Keep
the modal's `<h3>` title as-is for the dialog heading. Minor a11y polish.

### 174. [LOW] Reset button doesn't refocus the input
**Severity**: LOW
`AdjustTotalDialog.tsx:77` — clicking Reset replaces the input value but
leaves keyboard focus on the Reset button. Users frequently want to
glance at or tweak the field before clicking Set.

Fix: hold a `useRef` on the input and call `inputRef.current?.focus()`
inside the Reset handler. Tiny UX polish.

### 175. [MEDIUM] `JobItemCreate` margin/tax fields accept unbounded floats
**Severity**: MEDIUM
`platform/routers/estimates.py:609–614` — `original_profit_margin`,
`profit_margin`, `overhead_allocation`, `labor_burden`, and `tax` are all
`Optional[float] = None` with no bounds. Pydantic accepts NaN, ±Infinity,
and arbitrarily large/negative values. A malicious or buggy client could
persist garbage. Pre-existing pattern across the model — I added one more
field with the same loose typing rather than tightening it.

Fix: introduce shared `Annotated[float, Field(ge=…, le=…, allow_inf_nan=False)]`
type aliases for percentage fields (e.g. `PercentField`) and apply across
`JobItemCreate` + the corresponding `JobItem` model fields. Coordinate so
existing data still validates on read (use `model_validate` not strict
parsing on legacy docs).

---

## 2026-05-05 `/code-review` pass (header recolor + Maple FAB realignment + NumericInput blur-format)

### 177. [LOW] Grand Total contrast borderline at small text sizes
**Severity**: LOW
`portal/src/pages/NewEstimateWithActivityPage.tsx:1273` — the new
`bg-total-bg` (`#38A776`) with `text-white` measures ~3.03:1. Passes WCAG
AA only via the large-bold exemption (text is `text-lg font-bold`).
Acceptable here, but if the same token is reused for normal-weight or
smaller text it will fail AA.

Fix: if reuse is needed, define a darker variant (e.g.
`--total-bg-strong: #2E8A60`) for normal-weight text. Or document on the
token in `theme.css` that it's only safe for large-bold copy.

---

## 2026-05-06 `/code-review` pass (People pricing — Standard Unbillable %)

### 179. [LOW] Inline `reduce` on `activityRows` recomputed every render
**Severity**: LOW
`portal/src/components/estimates/WorkItemInlineContent.tsx:701` —
the "N.NN hours total" pill walks `activityRows` on every render via
inline `.reduce(...)`. Cheap (<50 rows), but inconsistent with the
surrounding `breakdown` value which is properly memoized via the
`computeBreakdown(...)` hook.

Fix: hoist into a `useMemo(() => activityRows.reduce(...), [activityRows])`
to match the file's existing pattern. Defer until a perf complaint or
the next time someone is in this code path.

---

## 2026-05-07 `/code-review` pass (top-10 followups batch — #28/#37/#40/#43/#44/#54/#56/#65/#67/#136)

Findings from the post-implementation review of the ten-item follow-up
batch that closed #28/#37/#40/#43/#44/#65/#67/#136 in code and resolved
#54/#56 by documentation. No CRITICAL / HIGH; three MEDIUM, one LOW.

---

## 2026-05-07 `/code-review` pass (second batch — #41/#42/#48/#50/#81/#180/#181/#182)

Findings from the post-implementation review of the second eight-item
follow-up batch. No CRITICAL / HIGH; one MEDIUM behaviour-change to
consider, two LOW style nits.

### 184. [MEDIUM] `response.json()` decode errors no longer caught in `address_service.py`
**File**: [platform/services/address_service.py:366, :409, :468](../../platform/services/address_service.py)
**Severity**: MEDIUM (behaviour change)

Narrowing `except Exception` → `except (httpx.HTTPError,
httpx.TimeoutException)` (the [#41](#41-except-exception-around-httpx-calls-in-address_servicepy-could-mask-future-httpexception)
fix) achieved the followup's stated goal: any `HTTPException(429)`
raised from inside the `try` propagates instead of being silently
swallowed. The narrower side effect is that `response.json()` —
which raises `json.JSONDecodeError` (subclass of `ValueError`) on
malformed payloads — used to fall into the `[]`/`{}` empty result and
now propagates as a 500 to the caller.

In practice Google Maps returns well-formed JSON, so this is
theoretical. Arguably an improvement (loud failure beats silent empty),
but it's a behaviour change beyond what the followup wording implied.

Fix: if you want the previous soft-fail on malformed payloads, expand
to `except (httpx.HTTPError, httpx.TimeoutException, ValueError):`.
Otherwise leave as-is and accept the loud-fail behaviour.

### 185. [LOW] Redundant `httpx.TimeoutException` in narrowed except tuple
**File**: [platform/services/address_service.py:366, :409, :468](../../platform/services/address_service.py)
**Severity**: LOW (style)

`httpx.TimeoutException` is a subclass of `httpx.HTTPError` (via
`RequestError`), so the tuple `(httpx.HTTPError, httpx.TimeoutException)`
is redundant — the second arm never matches. Harmless and explicit;
matches the [#41](#41-except-exception-around-httpx-calls-in-address_servicepy-could-mask-future-httpexception)
followup wording exactly.

Fix: optional simplification to `except httpx.HTTPError:`. Keeping the
explicit tuple is documentary, so this is style-only. Don't fix in
isolation; roll into any future address-service edit.

### 186. [LOW] Non-null assertion on `call.payload` in `handleStatusChange`
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx:478](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW (type safety)

`await estimatesApi.update(id, call.payload!)` uses `!` to assert
`payload` is defined inside the `kind === "update"` branch. Type-safe
in practice because `resolveStatusChangeApi` always returns a payload
when `kind === "update"`, but a future change that returns
`{ kind: "update" }` without a payload would break the invariant
silently.

Fix: tighten `StatusChangeApiCall` into a discriminated union so the
relationship between `kind` and `payload` is encoded in the type:

```ts
export type StatusChangeApiCall =
  | { kind: "archive" }
  | { kind: "unarchive" }
  | { kind: "update"; payload: { status?: string; approved_by?: string } };
```

`call.payload` is then provably defined inside the `else` branch, the
`!` goes away, and `StatusChangeApiKind` becomes the narrowable
discriminator. ~10 lines in `lib/estimateStatus.ts` plus one cleanup at
the call site.

---

## 2026-05-07 `/code-review` pass (estimate title bar — mobile kebab + checklist consolidation)

Findings from review of the EstimateTitleBar mobile-kebab refactor,
Property/Contact deep-link wiring, and Checklist button move into the
title bar. Zero CRITICAL / HIGH; two LOW polish items in
`NewEstimateWithActivityPage.tsx`. The pre-existing 1,783-line size of
that file is already covered by the file-size refactor item further up.

### 187. [LOW] Redundant `&& property` truthy check in property-info card
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx:1080](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW (dead code)

The address-link branch reads
`{selectedPropertyData?.street && property ? (...) : (...)}`, but the
entire block is already gated on `{property && (...)}` at line 1076,
so `&& property` inside the inner ternary is unreachable-to-falsify.
Harmless, but it implies a guard that doesn't exist.

Fix: simplify to `selectedPropertyData?.street ? (...) : (...)`. One-line
edit — roll into any future Property card edit.

### 188. [LOW] Contact deep-link still renders when contact name is empty
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx:1094-1101](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: LOW (UX)

When `selectedPropertyContact` resolves but both `first_name` and
`last_name` are empty/whitespace, `.trim() || "-"` falls back to
literal `"-"`, but the surrounding `<Link>` still renders. Users see a
clickable hyphen with no context. Accessibility is fine
(`title="View contact details"` provides hover text), but the
affordance is weak.

Fix options:
- Gate the `<Link>` on a non-empty trimmed name, falling back to the
  plain `<span>"-"</span>` branch.
- Substitute a descriptive fallback like `"Unnamed contact"` so the
  link target is meaningful.

Same pattern likely worth checking in any other card that renders
contact-name-or-dash next to a deep link.

---

## 2026-05-08 `/code-review` pass (post-#95 split)

Review of the `run_update_estimate` / `handle_estimate_fuzzy_confirmation`
split. No CRITICAL / HIGH beyond the function-size residuals already
acknowledged in #95's resolution; one LOW symmetry nit.

### 189. [LOW] `estimate_update.py` could mirror `fuzzy_confirmation._envelope`
**File**: [platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py)
**Severity**: LOW (DRY / symmetry)

`fuzzy_confirmation.py` introduced a `_envelope(...)` helper during the
#95 split that deduplicates the standard 11-key result dict across 4
call sites. `estimate_update.py` still has three near-identical
envelope shapes:
- `_modify_items_refusal` refusal dict (~14 lines)
- `run_update_estimate` empty-result dict (~13 lines)
- `_persist_added_job_items` success dict (~14 lines)

These differ in `success`, `result`, `needs_clarification`, and
`error` but otherwise share the same key set. Extracting an
`_envelope` helper local to this file would shave ~20 total lines and
nudge `_persist_added_job_items` (49-line body) and `_modify_items_refusal`
(41-line body) closer to the 50-line ceiling measured incl. signature.

Why LOW, not MEDIUM: the envelope-builder pattern is also flagged as
the higher-leverage fix in [#94](#94-new-material-handlers-all-exceed-the-50-line-ceiling)
for `agents/material/service.py`. Worth considering whether to factor
a single shared `_envelope` into `routers/agent_helpers/responses.py`
that both modules can import — but that's #94-scope work, not a
standalone cleanup.

---

## 2026-05-08 `/code-review` pass (Choose-Your-Plan dialog polish + onboarding tweaks)

Review of the plan-card type-scale changes, Enterprise theme darkening,
WelcomeStep list extension, CompletionStep green-accent sparkle, and the
SettingsPage Company-tab cleanup (estimate count/allowance moved to
Billing). No CRITICAL / HIGH; two MEDIUMs and two LOWs below.

### 190. [MEDIUM] Typo "iintegrations" in Pro plan feature copy
**File**: [portal/src/lib/billing-plans.ts](../../portal/src/lib/billing-plans.ts) line 111
**Severity**: MEDIUM (user-visible copy)

`PLAN_DETAILS.plan_pro.features` ships `"All systems iintegrations"` —
double `i`. Visible in onboarding's PlanStep and the Manage Plan modal.
Pre-existing in the uncommitted diff (not introduced this session) but
flagged so it gets fixed before the next plan-cards commit lands.

Fix: `"All systems integrations"` (or revisit phrasing entirely — the
prior copy was `"Integrate with top accounting packages"`).

### 192. [LOW] Plan-name `<h3>` visually outsizes the dialog `<h2>`
**File**: [portal/src/components/billing/PlanPickerGrid.tsx](../../portal/src/components/billing/PlanPickerGrid.tsx) line 219
**Severity**: LOW (visual hierarchy)

Plan names are now `text-3xl uppercase` while the parent dialog
heading "Choose Your Plan" is `text-2xl` (in both
`PlanStep.tsx:38` and `ManagePlanModal.tsx:60`). Semantic hierarchy is
still correct (h2 > h3), but visually the cards now hero over the
section title.

Fix (pick one): bump dialog `<h2>` to `text-3xl`, drop card `<h3>` to
`text-2xl`, or accept as-is if the design intentionally hero's the
plan name.

### 193. [LOW] Trailing whitespace in `ENTERPRISE_DISPLAY.features`
**File**: [portal/src/lib/billing-plans.ts](../../portal/src/lib/billing-plans.ts) line 128
**Severity**: LOW (cosmetic)

`"Custom configuration"    ` has 4 trailing spaces. Linters and diff
tools flag this; harmless at runtime.

Fix: trim to `"Custom configuration"`.

---

## 2026-05-08 `/code-review` pass (Stripe billing integration — platform + portal)

Review of the Stripe billing integration shipped May 2026. The five HIGH-severity blockers below shipped with the original change and are listed for historical context only:

- platform: `current_period_*` field relocation under pinned API version `2026-04-22.dahlia`
- platform: webhook dedupe-before-success retry gap in `routers/stripe_webhooks.py`
- platform: synchronous Stripe SDK calls inside `async def` handlers (event-loop blocking)
- portal: `AddPaymentMethodModal.onSuccess` retry path that didn't actually retry the create-draft effect
- portal: `ManagePlanModal` rendering bare `<div>` outside `<DialogContent>` (lost dialog semantics)

The items below are deferred housekeeping. Pick them up in order of severity, repo-by-repo.

### 195. [MEDIUM] Reconciliation cron for "soft-failed" plan selection
**File**: `platform/routers/billing.py:186` (select-plan), `platform/routers/billing.py:492` (enterprise-contact)
**Severity**: MEDIUM

Both endpoints catch `Exception` broadly with the comment "reconciliation cron retries" — but the cron doesn't exist yet. A user whose plan-selection Stripe call silently failed thinks they're on Pro/Base; the BE has the local plan set but no Stripe subscription. There's nothing to find their orphaned record later.

Fix: either (a) build the planned reconciliation job that scans companies with a non-Free local plan but no `stripe_subscription_id` and replays the missing call, or (b) persist a `BillingReconciliationQueue` row at the catch site so the future cron has explicit work to find. At minimum, fire a Sentry capture inside the except block and surface a soft-warning flag in the response so the FE can show "Your plan is saved; we'll finish setup shortly."

### 196. [MEDIUM] Implement `payment_failed` user notification
**File**: `platform/services/billing/webhook_handlers.py:114` (TODO)
**Severity**: MEDIUM

Customers in `past_due` after a card decline are not notified by the platform. Stripe's "Smart Retries" Dashboard emails partially cover this, but the codebase shouldn't rely on that implicitly — and we lose the chance to brand the message.

Fix: send via `services/brevo_email.send_brevo_plain_email` from the `invoice.payment_failed` handler. Subject: "Payment failed — update your card." Link target: customer-portal session URL.

### 201. [LOW] Use `Query(..., ge=1, le=50)` for `list_invoices` limit
**File**: `platform/routers/billing.py:282`
**Severity**: LOW

Inline `max(1, min(limit, 50))` clamping silently coerces bad input. `Query(12, ge=1, le=50)` returns a clean 422 instead.

### 202. [LOW] Validate Stripe `brand` against an allow-list before persisting
**File**: `platform/services/billing/webhook_handlers.handle_payment_method_attached`, `platform/routers/billing.py:111`
**Severity**: LOW

The brand string flows from Stripe → DB → FE rendering. Not a security issue today (Stripe controls the value), but if it's ever rendered un-escaped, an unexpected brand value breaks the UI.

Fix: lowercase and check membership in `{"visa", "mastercard", "amex", "discover", "diners", "jcb", "unionpay", "unknown"}` before persisting.

### 203. [LOW] Drop the `event_type or "unknown"` defensive branch
**File**: `platform/routers/stripe_webhooks.py:65`
**Severity**: LOW

Signature verification has already passed, so the event is well-formed. A missing `type` would be a Stripe SDK bug, not a runtime expectation. The defensive `or "unknown"` lets a malformed event get persisted with a placeholder label.

Fix: `event_type = event_dict["type"]` and let the KeyError bubble.

### 204. [LOW] Don't write Stripe webhook signing secret to repo working tree
**File**: `platform/scripts/setup_stripe_webhook.py:140-157`
**Severity**: LOW

The script writes the signing secret to `secrets/webhook_signing_secret.<id>.txt` with `chmod 0600`. Reasonable, but the file persists until manually removed and an operator who misses the print-message reminder leaves a real `whsec_…` in the working tree.

Fix: use `tempfile.NamedTemporaryFile(delete=False, dir="/tmp")` outside the repo, or print the secret to stderr and have the operator pipe to `.env` directly. Alternatively, register an `atexit` handler that clears the file unless `--keep-secret` was passed.

### 206. [MEDIUM] Generalize `PlanPickerGrid` button label
**File**: `portal/src/components/billing/PlanPickerGrid.tsx:140-145`
**Severity**: MEDIUM

`buttonLabel` is hardcoded to "Select Free Plan" for any selectable plan. The day Base or Pro flips `selectableAtLaunch: true`, every button reads "Select Free Plan."

Fix: ``Select ${plan.displayLabel} Plan`` — or just "Select plan" if displayLabel feels redundant.

### 210. [MEDIUM] `PlanStep` should disable the grid when `companyId` is null
**File**: `portal/src/components/onboarding/PlanStep.tsx:18-33`
**Severity**: MEDIUM

If `companyId` is null when the user clicks Select, they see "Missing company context. Please reload and try again." But by step 6, the company was created in step 1 — a missing companyId here is a code-flow bug, not a user-recoverable state. Telling the user to reload is unhelpful.

Fix: pass a `disabled` prop down to `PlanPickerGrid` when `!companyId`. Render an inline "Initializing your account…" notice instead of letting the user click and fail.

### 211. [LOW] Remove or use `publishable_key_hint`
**File**: `portal/src/api/billing.ts:38-41`
**Severity**: LOW

`SetupIntentResponse.publishable_key_hint` is declared but never read. Publishable key comes from `VITE_STRIPE_PUBLISHABLE_KEY` only. Dead field.

Fix: either remove from the type, or use it as a runtime sanity check ("BE hint disagrees with FE env" → log warning) inside `getStripePromise`.

### 212. [LOW] Drop `opacity-95` on coming-soon plans
**File**: `portal/src/components/billing/PlanPickerGrid.tsx:152`
**Severity**: LOW

A 5% reduction is visually indistinguishable from full opacity. The intent is clearly to dim Coming-Soon plans. Either drop the prop or strengthen.

Fix: `opacity-70` or remove `dimWhenComingSoon` if the "Coming Soon" badge is enough.

### 213. [LOW] Pluralize plan summary copy
**File**: `portal/src/components/onboarding/CompletionStep.tsx:23`
**Severity**: LOW

"Up to 3 team members" / "Up to 20 new estimates per month" hardcodes plural. A future plan with `includedSeats: 1` would read "Up to 1 team members."

Fix: `${n === 1 ? "team member" : "team members"}` — same for estimates.

### 214. [LOW] Map raw Stripe `subscription_status` to friendly labels in BillingTab
**File**: `portal/src/components/settings/BillingTab.tsx:104-107`
**Severity**: LOW

`state.stripe_subscription_status` is rendered as-is. Values like `incomplete_expired`, `past_due`, `trialing` show literally with underscores — cosmetic but user-facing.

Fix: small `STATUS_LABELS` map: `active → "Active"`, `past_due → "Past Due"`, `trialing → "Trialing"`, `incomplete → "Incomplete"`, `incomplete_expired → "Setup Expired"`, `canceled → "Canceled"`, `unpaid → "Unpaid"`.

### 215. [LOW] Drop redundant 5000-char client check in EnterpriseContactModal
**File**: `portal/src/components/billing/EnterpriseContactModal.tsx:56-58`
**Severity**: LOW

`MESSAGE_MAX_LEN` is already enforced via `maxLength` on the textarea, making the explicit length check redundant defense.

Fix: remove the duplicate check, or add a comment confirming it matches the BE `enterprise-contact` endpoint validation.

### 216. [LOW] Extract `<PlanSummaryBlock>` component
**File**: `portal/src/components/onboarding/CompletionStep.tsx:36-58`, `portal/src/components/settings/BillingTab.tsx`, `portal/src/components/billing/PlanPickerGrid.tsx`
**Severity**: LOW

Three places render `included_seats` / `included_estimates` summary blocks. Minor DRY concern — adding a fourth field to the Free-plan summary card would mean updating three spots.

Fix: optional refactor — extract `<PlanSummaryBlock plan={plan} variant="onboarding" | "billing-tab" | "card" />` if a fourth field gets added or another surface needs the block.

---

## 2026-05-09 `/code-review` pass (Choose Your Plan dialog refinements)

Visual pass on `PlanPickerGrid` — reordered the card sections (tagline → title → price → action → features → support → limits), bumped tagline / shrunk title, hid non-monetary price labels, fixed outline-button contrast on dark cards, swapped the Enterprise "Contact Sales" CTA for a disabled "Coming Soon" button, and updated the modal subtitle. Two findings logged below; the orphaned `EnterpriseContactModal` and the `priceLabel.startsWith("$")` heuristic were both flagged but explicitly marked TEMP-only by the user and not tracked here.

### 218. [LOW] Mark the price placeholder div for testability and clarity
**File**: `portal/src/components/billing/PlanPickerGrid.tsx:209`
**Severity**: LOW

`<div aria-hidden="true" />` is correct ARIA usage but appears in DevTools as an unexplained empty div. The intent is documented in the comment block above the JSX, but the markup itself is opaque to a future reader scanning the rendered tree.

Fix: optional — add `data-testid="price-placeholder"` (also lets #217's tests target the slot directly), or wrap it in a self-explanatory inline comment at the JSX site.

---

## 2026-05-09 `/code-review` pass (followups #37/#40/#46/#65/#197/#198/#199/#200/#205/#207/#208/#209 cleanup batch)

Findings from the post-implementation review of the twelve-followup
batch. No CRITICAL / HIGH; four MEDIUMs and three LOWs.

### 219. [MEDIUM] `VALID_PLAN_KEYS` duplicates `PLAN_LOOKUP_KEYS` from `billing-plans.ts`
**File**: [portal/src/pages/OnboardingPage.tsx:21-25](../../portal/src/pages/OnboardingPage.tsx)
**Severity**: MEDIUM

The new `VALID_PLAN_KEYS` set added by [#205](#205-persist-selectedplan-to-localstorage-during-onboarding)
hardcodes the three plan lookup keys, but
`portal/src/lib/billing-plans.ts:136-140` already exports
`PLAN_LOOKUP_KEYS: PlanLookupKey[]`. Two lists to keep in sync — adding
a fourth plan in `billing-plans.ts` would silently reject the new key
during localStorage hydration without a single line in this file
indicating why.

Fix: `import { PLAN_LOOKUP_KEYS } from "../lib/billing-plans"` and
derive `const VALID_PLAN_KEYS: ReadonlySet<string> = new Set(PLAN_LOOKUP_KEYS)`.
Roll into the next OnboardingPage edit.

### 220. [MEDIUM] Onboarding plan-persistence test reimplements `readPersistedPlanKey`
**File**: [portal/tests/onboardingPlanPersistence.test.tsx:11-17](../../portal/tests/onboardingPlanPersistence.test.tsx)
**Severity**: MEDIUM

The new test landed alongside [#205](#205-persist-selectedplan-to-localstorage-during-onboarding)
defines its own copy of `readPersistedPlanKey` and `VALID_PLAN_KEYS`
rather than importing from `OnboardingPage.tsx`. If the production
validation changes (e.g., adds `plan_enterprise` or tightens
acceptance), the test still passes against the old logic and gives
false confidence.

Fix: extract `readPersistedPlanKey` (and `VALID_PLAN_KEYS`) into a
small `portal/src/lib/onboardingPlanStorage.ts` helper, export it, and
have both `OnboardingPage.tsx` and the test import from there. Drives
both sides from one source.

### 221. [MEDIUM] `meter_events.report_seat_count` atomic update inside broad `except` swallows DB errors
**File**: [platform/services/billing/meter_events.py:99-122](../../platform/services/billing/meter_events.py)
**Severity**: MEDIUM

The atomic `find_one_and_update` added by [#200](#200-atomic-high-water-update-in-meter_eventspy)
lives inside the same `try / except Exception` block originally meant
to catch Stripe failures. A pymongo error from the conditional update
gets logged with `"Failed to report seat-count meter event"` —
misleading because the meter event already succeeded by that point.
Worse, the silent swallow means the next `report_seat_count` call
sees a stale local `company.seat_count_period_high_water` and may
re-post the same value to Stripe (which is harmless thanks to the
date-keyed idempotency key, but still wastes a round trip).

Fix: split into two try blocks (Stripe → log+continue, DB → propagate
or log via a distinct error path), OR tighten the except to
`(stripe_sdk.error.StripeError,)` so DB errors surface, matching the
narrow-except pattern landed in `customer.py` ([#199](#199-narrow-the-except-in-customerpy67)).

### 222. [MEDIUM] `ESTIMATE_STATUS_TRANSITIONS` two-step construction in `models/estimate.py`
**File**: [platform/models/estimate.py:36-92](../../platform/models/estimate.py)
**Severity**: MEDIUM

The map is declared empty (`ESTIMATE_STATUS_TRANSITIONS: dict[...] = {}`),
then `.update(...)` populates it after `validate_estimate_status_transition`
is defined. The forward-reference dance (`dict["EstimateStatus", set["EstimateStatus"]]`)
implies a circular dependency that doesn't actually exist —
`EstimateStatus` is fully defined at line 8, well before line 36.

Fix: collapse to a single literal assignment with concrete type
annotations (no string forward refs), placed once before
`validate_estimate_status_transition`. Identical behavior, cleaner
ordering, easier to read.

### 223. [LOW] SetupIntent idempotency window not configurable
**File**: [platform/routers/billing.py:271](../../platform/routers/billing.py)
**Severity**: LOW

`int(time.time() // 60)` hardcodes a 60-second bucket. Fine in
practice — Stripe SetupIntent.create returns in under 2s — but if the
network ever degrades to >60s round-trips, a retry would mint a new
key and create the duplicate intent the key was meant to prevent.

Fix: optional. Either accept a client-supplied `idempotency_key` from
the request body, or expose the bucket size as a `Settings` field
(`stripe_idempotency_window_seconds: int = 60`). Don't fix in
isolation; roll into the next billing router touch.

### 224. [LOW] Sentry extras include Stripe PaymentMethod ID
**File**: [portal/src/components/billing/AddPaymentMethodModal.tsx:194-197](../../portal/src/components/billing/AddPaymentMethodModal.tsx)
**Severity**: LOW

The capture added by [#209](#209-dont-silently-warn-on-syncpaymentmethod-failure)
attaches `paymentMethodId` (a Stripe PM ID like `pm_…`) to Sentry
under `extra`. PM IDs aren't PII per Stripe's classification, but
they're correlation keys someone with both Sentry and Stripe access
could use to look up the underlying card brand/last4.

Fix: optional, depends on Sentry retention policy. Either add an
inline `// Stripe PM IDs aren't PII; safe to attach for debugging`
comment to document the stance, or move `paymentMethodId` from
`extra` (indexed) to `contexts` (free-form attached metadata, less
prominent in alert UIs).

### 225. [LOW] `APP_BASE_URL` has a localhost default that ships to production
**File**: [platform/config.py:80](../../platform/config.py)
**Severity**: LOW

The `app_base_url: str = Field(default="http://localhost:5173", ...)`
default added by [#197](#197-customer-portal-return_url-should-not-hardcode-prod)
is correct for dev, but a production deploy that forgets to set
`APP_BASE_URL` bounces customers from the Stripe Customer Portal back
to `http://localhost:5173/settings` — "site can't be reached" from
their browser. Better than the prior hardcoded prod URL (the previous
state guaranteed dev/staging users got bounced), but still relies on
ops remembering to set it per environment.

Fix: optional safety net at app startup — if
`sentry_environment == "production"` and
`app_base_url.startswith("http://localhost")`, log a CRITICAL warning
or abort. Or change the Settings field to `str | None = None` and
assert non-None at the use site for prod environments.

---

## 2026-05-09 `/code-review` pass (contact form pre-launch waitlist checkbox)

Findings from the change that adds a "Join the pre-launch waitlist"
checkbox to the website contact modal and surfaces the opt-in in the
support email. Touches `website/public/contact-modal.js` (UI + payload)
and `website/functions/index.js` (Cloud Function — accept the new
boolean field, render it in the email body).

### 226. [MEDIUM] `cm-waitlist` is used as both a CSS class and an element id
**File**: [website/public/contact-modal.js:138, 252](../../website/public/contact-modal.js)
**Severity**: MEDIUM

The wrapper `<div class="cm-waitlist">` shares the literal string
`cm-waitlist` with the `<input id="cm-waitlist">` it contains. CSS is
unaffected (class vs id selectors don't collide), and
`<label for="cm-waitlist">` correctly resolves to the input. But
anyone who later writes `document.getElementById('cm-waitlist')`
expecting the wrapper will instead get the checkbox — a quiet
footgun, not a current bug.

Fix: rename the wrapper class to `.cm-waitlist-block` (or rename the
id to `cm-join-waitlist`), update the matching CSS selectors, and
update the `<label for=…>` accordingly. ~5 line change. Roll into the
next contact-modal touch.

### 228. [LOW] `form.joinWaitlist.checked` relies on the named-elements collection
**File**: [website/public/contact-modal.js:331](../../website/public/contact-modal.js)
**Severity**: LOW

Works because HTML form elements are exposed by `name` on the form
object. If another element were ever added to this form with
`name="joinWaitlist"`, the lookup would return a `RadioNodeList` and
`.checked` would be `undefined`. The pattern matches the rest of the
file (`form.firstName.value` etc.), so this is consistent — just
inherited fragility.

Fix: optional. Switch to
`form.querySelector('#cm-waitlist').checked` (or use a captured
reference like the other inputs at module scope) for clarity. Skip if
you prefer to stay consistent with the existing style.

### 229. [LOW] Submit handler is ~60 lines after this change
**File**: [website/public/contact-modal.js:316-386](../../website/public/contact-modal.js)
**Severity**: LOW

The inline `form.addEventListener('submit', async (e) => { … })`
body is long enough to be hard to scan. Pre-existing issue; this
change adds one line so it's not regressing meaningfully.

Fix: extract the body into a named function (`handleSubmit`) in a
follow-up if/when the file is touched again. No action needed for
this commit.

---

## 2026-05-09 `/code-review` pass (file-size HIGH-followup batch — #94/#99/#172/#178/#58 partial)

Findings from the post-implementation review of the size-refactor
batch that closed #99 / #172 / #178, partially closed #58 / #94, and
consolidated #169 / #176 into #58. No CRITICAL; one HIGH (precedent-
matched), two MEDIUM, two LOW.

### 233. [LOW] `_LABEL_PATTERNS` is a mutable class-level dict
**File**: [platform/agents/property/service.py:375](../../platform/agents/property/service.py)
**Severity**: LOW

Class-level `Dict[str, List[str]]` is allocated once and is technically
mutable. Today nothing mutates it, but a future `_extract_label_fields`
edit that did `self._LABEL_PATTERNS[field].append(...)` would silently
corrupt subsequent calls (and other instances).

Fix: either annotate as
`_LABEL_PATTERNS: Final[Mapping[str, Sequence[str]]] = ...` (importing
`Final` and `Mapping` / `Sequence` from `typing`) or convert the
inner `List[str]` values to tuples. Cosmetic; safe today.

## 2026-05-09 file-size sweep (untracked giants — under the #4 theme)

Sweep of files >800 lines (frontend) / >800 lines (backend, ignoring
tests + .venv) that were not yet logged. Listed in priority order
within each tier; severities are HIGH per the file-size guideline,
but resolution will likely require multiple sessions per file. These
are tracked under the broader #4 file/function-size theme.

All entries from this sweep (#235, #236, #237, #238, #240, #241, #242, #243, #244, #245, #246, #247, #248, #249, #250) were folded into the #4 file/function-size canonical. See `## Closed`. #239 (resolved) remains in `## Closed` independently.

---

## 2026-05-10 `/code-review` pass (LLM token tracking + Stripe metering)

LOW-severity items from the review of the LLM-token-usage-metering change.
HIGH and MEDIUM findings from that pass were fixed in the same PR; these
four are the remainder. See [`plans/llm-token-usage-metering.md`](./plans/llm-token-usage-metering.md)
for the design context.

### 251. [LOW] Consolidate `ensure_*_price` helpers in `scripts/seed_stripe_products.py`
`ensure_flat_price`, `ensure_metered_overage_price`, and
`ensure_metered_token_overage_price` share ~70% of their logic
(lookup-key search, tier-drift comparator, archive-and-recreate flow).

Fix: refactor to a single `ensure_price(...)` driver that takes the
Price-create kwargs plus a per-shape `drift_check(existing_full)` callable.
Low risk, but defer until we add a fourth Price shape — premature otherwise.

### 252. [LOW] In-function imports in `services/billing/webhook_handlers.py`
`handle_invoice_paid` does `from models import User` inside the function
for the per-user token-counter reset path. The rest of the module imports
models at the top. Mixed style.

Fix: move to module-top imports for consistency. Trivial cleanup; bundle
with the next functional change to this file.

---

## 2026-05-10 `/code-review` pass (Properties/Contacts name column + current-plan button)

### 255. [LOW] Redundant `hover:bg-emerald-600` on current-plan button
`portal/src/components/billing/PlanPickerGrid.tsx:134` — the
`buttonClass` for the current plan includes both `bg-emerald-600` and
`hover:bg-emerald-600`. The hover variant matches the base, and the
shared `Button` component already sets `disabled:pointer-events-none`,
so hover can never fire on the disabled current-plan button anyway.

Fix: drop `hover:bg-emerald-600` from the `isCurrent` branch of
`buttonClass`. Keep `bg-emerald-600 text-white border-transparent
disabled:opacity-100 w-full`.

---

## 2026-05-11 `/code-review` pass (Maple plan-limit gates — Maple credits + estimate count)

CRITICAL: 0, HIGH: 1 (fixed in the same PR), MEDIUM: 2, LOW: 1.

The HIGH (`blocked` branch leaked billing — counter didn't advance and no
Stripe meter event was posted when over-cap but card on file) was fixed
in-PR by adding `services/estimate_quota.py:record_overage_estimate()`
and calling it from the `blocked` branch in
`routers/agents.py:_check_estimate_limit_or_refuse`. Counter now advances
and the overage bills at cycle close. The MEDIUM/LOW items below are
deferred.

#256 (mypy annotation) folded into #3. #257 (file-size) folded into #4. See `## Closed`.

---

## 2026-05-12 `/code-review` pass (estimate duplicate menu + Approved→Sent swap)

The two HIGHs from this pass were fixed in-PR
(`duplicate_estimate` quota rollback + PortalLayout refusal-sentence
restructure). MEDIUMs and LOW captured here.

### 259. [MEDIUM] Migration script uses Beanie field descriptors as `.set()` keys
`platform/scripts/db/migrate_approved_to_sent.py:60` calls
`estimate.set({Estimate.status: ..., Estimate.updated_at: ...})`. The
rest of `routers/estimates.py` (3 call sites at 910, 993, 1071) uses
string keys: `estimate.set({"status": ..., "updated_at": ...})`. Beanie
tolerates both forms but the inconsistency is surprising. Low-effort
fix — swap the keys to string literals to match the codebase.

### 261. [LOW] Session-stored estimate filter can be the now-removed "Approved" value
`portal/src/pages/EstimatesPage.tsx:96` —
`sessionStorage.getItem("estimatesStatusFilter") ?? "Draft"` is read
verbatim. Users who had `Approved` selected before the swap will see
the `<select>` render an orphan value (not in `statusOptions`), which
shows as a blank option in the dropdown. Defensive coerce:

```tsx
const saved = sessionStorage.getItem("estimatesStatusFilter");
return saved && statusOptions.includes(saved) ? saved : "Draft";
```

Self-heals within a few days as users click a real option and overwrite
the stale value, so LOW priority.

## 2026-05-12 /code-review pass (Dashboard pipeline histogram)

Frontend-only change: recurring totals now flow into the division chart,
Pipeline Status switched to a vertical histogram, status colors
recolored across the app. Three MEDIUMs and the `<$1k` LOW were fixed
in-PR. One LOW remains.

## 2026-05-12 `/code-review` pass (markdown description editor)

Frontend-only change: replaced the textarea on the estimate description
and the work item description with a WYSIWYG markdown editor
(`@mdxeditor/editor`). Two MEDIUMs fixed in-PR (dead `prose` classes
stripped from `MarkdownDescriptionEditor.tsx`; `npm audit fix` reduced
vulnerabilities from 15 (1 critical / 4 high / 10 moderate) to 5
moderate, all in dev-only `vite` / `vitest` / `esbuild` chains that
require a semver-major upgrade — tracked as #263 below). Three LOWs
remain.

### 263. [LOW] Remaining `vite` / `vitest` / `esbuild` advisories require a semver-major bump
`portal/package.json` — 5 moderate-severity advisories left after
`npm audit fix`: vite path-traversal in optimized-deps `.map` handling,
vite `server.fs` HTML-bypass, `@vitest/mocker`, `vite-node`, `vitest`.
All dev-only (test runner / dev server), all require the semver-major
fix path (`vite` 4.5 → 8.x, `vitest` 2.1 → 4.x). Bundle this with a
broader tooling refresh — don't tack it onto a feature branch, since
the Vite 8 / Vitest 4 migrations may surface config and plugin changes
across the portal.

### 264. [LOW] Description label not programmatically associated with the editor
`portal/src/pages/NewEstimateWithActivityPage.tsx:1036` and
`portal/src/components/estimates/WorkItemInlineContent.tsx:371` — the
"Description" label renders as a plain `<span>` / `<h3>` with no `id`
referenced by the editor's accessible name. Screen readers don't
announce "Description" when the contenteditable receives focus.
Matches the pre-mdxeditor textarea (also unlabeled), so it's a
continuation, not a regression. Fix: add `id="..."` to the heading
and pass `aria-labelledby="..."` through `MarkdownDescriptionEditor`
to the underlying `MDXEditor` (props pass-through prop, or accept it
on the wrapper).

### 265. [LOW] Generic `data-toolbar-visible` attribute could collide
`portal/src/styles/index.css:6` and
`portal/src/components/common/MarkdownDescriptionEditor.tsx:124` —
the CSS rule keys off a non-namespaced `data-toolbar-visible`
attribute. Low collision risk today, but the name is generic enough
that another component could reuse it. Rename to
`data-mdx-toolbar-visible` in both the CSS rule and the wrapper so
the contract is explicit.

### 266. [LOW] `onBlur` prop fires on every contenteditable blur, not just true wrapper-exit
`portal/src/components/common/MarkdownDescriptionEditor.tsx:132` —
mdxeditor's `onBlur` is forwarded raw, so the parent's `onBlur` runs
whenever focus leaves the contenteditable (e.g. when the user clicks
a toolbar button, even though they're still editing). The estimate
page dedupes via `lastSavedDescriptionRef`, so this is harmless in
practice. Fix: gate the forwarded `onBlur` on `relatedTarget` not
being inside `wrapperRef`, mirroring the focus-tracking logic for
`handleBlurCapture`. Then `onBlur` only fires when focus truly leaves
the editor surface — safer for any future consumer that doesn't
dedupe.

## 2026-05-13 `/code-review` pass (#7 implementation — test backfills)

Review of the 211-test backfill that closed item #7 ("Missing tests for new
public functions"). Production code unchanged; findings below all apply to
the new test files themselves.

### 276. [MEDIUM] Long test functions in #7 backfill tests
Five test functions across two files exceed the 50-line guideline:

- `test_generate_google_doc_router.py:128` — `test_generate_google_doc_batches_contact_fetch` (118 lines)
- `test_generate_google_doc_router.py:252` — `test_generate_google_doc_zero_contacts_succeeds` (86 lines)
- `test_generate_google_doc_router.py:404` — `test_fetch_estimate_doc_context_issues_single_batched_contact_find` (78 lines)
- `test_feedback_anonymous.py:133` — `test_feedback_registered_user_uses_real_name` (54 lines)
- `test_feedback_anonymous.py:189` — `test_feedback_blank_first_last_name_falls_back_to_unknown_user` (56 lines)

Body bulk is fixture setup (multi-contact estimates for the doc tests,
firebase-token + user-record scaffolding for the feedback tests), not
assertion logic. Hard to scan.

Fix: extract the multi-contact estimate scaffold into a `pytest.fixture`
in a module-level setup so the assertion is the bulk of the test body;
parameterize contact-count for the two related variants in
`test_generate_google_doc_router.py`. Could also fold under #4 as
function-size instances.

### 277. [LOW] Pydantic 2.11 deprecation warning surfaces in async tests
Six warnings per test run from
`lazy_model/parser/new.py:110` — "Accessing the 'model_fields' attribute on
the instance is deprecated. Instead, you should access this attribute from
the model class. Deprecated in Pydantic V2.11 to be removed in V3.0."

Not introduced by these tests; it's a third-party (`lazy_model`)
compatibility gap with Pydantic 2.11. Surfaced because the new async tests
exercise Beanie model loading paths. Will break when Pydantic V3 lands
(currently slated for a 2026-Q3+ release).

Fix: bump `lazy_model` when an upstream release addresses the deprecation,
or pin Pydantic to <2.11 until then. Track upstream
[BAMR-team/lazy-model](https://github.com/roman-right/lazy-model).

### 269. [MEDIUM] Overage-dialog audit-event failures swallowed without Sentry capture
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/pages/EstimatesPage.tsx` (the `handleOverageConfirm` and
`handleOverageAddCard` paths) and `portal/src/pages/SettingsPage.tsx`
(`handleConfirmSeatsOverage`, `handleOpenAddCardFromWarning`) wrap
`usersApi.recordOverageEvent(...)` in bare `try { ... } catch {}`.
Failures are silent, so a regression in the `/users/me/overage-event`
endpoint or the audit-log pipeline would go unnoticed.

`portal/src/components/billing/AddPaymentMethodModal.tsx:197` already
establishes the pattern of `Sentry.captureException(e, { tags: ... })`
for non-blocking failures. Apply the same pattern to all four sites so
silent regressions surface in Sentry.

Fix: replace each `catch {}` with
`catch (e) { Sentry.captureException(e, { tags: { feature: "overage_dialog", action: "<acknowledged|add_card_clicked|pref_persist>" } }); }`.

### 270. [MEDIUM] `OverageWarningDialog` `aria-labelledby` points at a `<span>` inside the heading
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/components/billing/OverageWarningDialog.tsx:60-62` —
`DialogContent ariaLabelledBy="overage-warning-title"` resolves to an
`id` placed on a `<span>` inside the `<h2>` rendered by `DialogTitle`.
Screen readers still find the label text, but the convention is for
`aria-labelledby` to point at the heading element itself, not a child
of it.

Fix: either drop the inner `<span id>` and let `DialogContent` derive a
default label, or extend `DialogTitle` to accept an `id` prop that lands
on the underlying `<h2>` (preferred — minor `ui/dialog.tsx` change).

## LOW

### 268. [LOW] `<AiPanelProvider>` top-level wrap not re-indented in PortalLayout
`portal/src/components/Layout/PortalLayout.tsx:966` and `:1925` —
when `AiPanelProvider` was hoisted to wrap the whole layout return,
the inner `<div className="flex h-screen …">` was left at the same
indentation as the new provider tag. Functionally fine, just
inconsistent. Fix: Prettier pass over the file.

### 269. [LOW] `React.ReactNode` referenced without explicit React import in MapleMarkdown.test.tsx
`portal/tests/MapleMarkdown.test.tsx:13` — `renderInRouter` types
its `node` param as `React.ReactNode` but the file doesn't
`import React` or `import type { ReactNode } from "react"`. Resolves
today via the global `React` namespace from `@types/react`, but
breaks if the project ever tightens `tsconfig.compilerOptions.types`
or removes the global declaration. Fix: `import type { ReactNode }
from "react"` and reference `ReactNode` directly.

### 270. [MEDIUM] `EstimatesTable.tsx` layout comment references `min-w-0` but cells use `min-w-[8rem]`
`portal/src/components/common/EstimatesTable.tsx:137-140` — the
new layout-rationale comment claims Title/Property "can shrink to
a small floor (`min-w-0` lets a long word break instead of forcing
the column wide)", but the `<th>` cells actually use
`min-w-[8rem]` (128px). `min-w-0` is nowhere on either cell. A
reader trusting the comment will misjudge how narrow the columns
can get. Fix: update the comment to match the 8rem floor, or add
`min-w-0` to the inner content div if word-break behavior is
actually wanted alongside the cell floor.

### 271. [LOW] Clear-all toolbar button bypasses `handleMarkdownChange`
`portal/src/components/common/MarkdownDescriptionEditor.tsx:97` —
the toolbar Clear button calls `onChangeRef.current("")`
directly, skipping `handleMarkdownChange`, so `lastEmittedRef`
isn't updated. The visible behavior is correct (sync effect
re-runs and calls `setMarkdown("")`), but the asymmetry breaks
the invariant "lastEmittedRef equals the most recent value we
emitted" that the sync guard relies on. Fix: route Clear through
`handleMarkdownChange("")` so every emit path updates the ref.

### 272. [LOW] `lastEmittedRef` is never re-synced from external updates
`portal/src/components/common/MarkdownDescriptionEditor.tsx:57` —
when the sync effect calls `setMarkdown(value)` for an external
update, it doesn't write `lastEmittedRef.current = value`. We get
away with it today because mdxeditor fires `onChange` after
`setMarkdown` and the ref catches up via that path, but the
invariant is implicit. If a future mdxeditor version stops
emitting onChange on setMarkdown, the next external sync could
falsely short-circuit. Fix: set `lastEmittedRef.current = value`
inside the sync effect right after the `setMarkdown` call.

### 273. [LOW] NBSP literal in `markdownBlankParagraphs.ts` is invisible in source, no test imports the constant
`portal/src/components/common/markdownBlankParagraphs.ts:7` —
`NBSP_PARAGRAPH = " "` contains a literal U+00A0 byte-different
from regular space but visually identical. The test file
reconstructs its own `NBSP = " "` constant rather than importing
this one, so a slip on either side passes silently. Fix: either
export `NBSP_PARAGRAPH` and import it in the test for a single
source of truth, or write the constant as
`String.fromCharCode(0xA0)` so it's unambiguous in source.

### 274. [LOW] `encodeBlankParagraphs` runs on every keystroke
`portal/src/components/common/MarkdownDescriptionEditor.tsx:90-96` —
`handleMarkdownChange` runs the regex scan on every onChange,
which scales linearly with description length. Not a real perf
concern at human typing speed, but worth profiling if estimate
descriptions ever grow into the multi-thousand-character range
(e.g. AI-generated long-form descriptions). Fix: only revisit if
profiling surfaces it.

---

## Closed

Items archived here are resolved/fixed and kept only for historical reference and to preserve numbering for cross-references in the live list. Sorted by item number.

### 7. [HIGH] Missing tests for new public functions
**Closed as resolved 2026-05-13.** All 10 absorbed children backfilled with direct test coverage. 209 tests added across 9 new files + 1 extended file:

- **#36** → `platform/tests/test_generate_google_doc_router.py` (8 tests, single-`Contact.find` regression assertion)
- **#51** → `platform/tests/test_orchestrator_bare_entity_helpers.py` (42 tests)
- **#85** → `platform/tests/test_estimate_crud_handler_helpers.py` (16 tests)
- **#98** → `platform/tests/test_agent_helpers_text_predicates.py` (63 tests for `is_affirmative_text` / `is_negative_text`; `run_update_estimate` and `handle_estimate_fuzzy_confirmation` covered separately by prior `test_agent_helpers_estimate_update.py` and `test_agent_helpers_fuzzy_confirmation.py`)
- **#111** → `platform/tests/test_feedback_anonymous.py` (4 tests for "Unknown User" fallback)
- **#129** → `portal/tests/NewEstimateWithActivityPage.autosave.test.tsx` (6 tests via RTL)
- **#168** → `platform/tests/test_cross_resource_envelope_helpers.py` (40 tests across 10 helpers — verification found one more helper than originally listed)
- **#217** → `portal/tests/PlanPickerGrid.test.tsx` extended (+3 tests: aria-hidden price slot, button order, `text-foreground` class)
- **#227** → `website/functions/joinWaitlist.test.js` (8 tests on Cloud Function; vanilla-JS modal skipped — no test infra under `public/`)
- **#232** → `platform/tests/test_material_response_envelope.py` (19 tests)

Bugs/curiosities surfaced during backfill (not fixed; worth tracking as new follow-ups):
- `_is_bare_entity_reference` for the contact domain skips the stopword guard — `"Hello Smith"` passes as a bare-entity reference.
- `_PERSON_NAME_PATTERN` rejects `"O'Brien"` / `"Smith-Jones"` when the post-apostrophe/hyphen word starts uppercase — likely a latent regex bug for Irish/hyphenated surnames.
- `_coerce_company_oid` returns `None` on whitespace-only input via the `PydanticObjectId` path, not the early `if not company_id` guard.
- `joinWaitlist` Cloud Function uses strict-equality (`=== true`) coercion; non-boolean payloads silently resolve to `false`. Safe in current frontend usage but worth knowing.

<details>
<summary>Original body (preserved for history)</summary>

Per `CLAUDE.md` mandatory-testing rule. To identify gaps: for each new public
function added in the last N commits, verify there's a corresponding
`tests/test_<module>.py::test_<fn>`. A `coverage report` run against
`routers/` and `agents/` will spotlight the red lines.

Specific instances surfaced in later passes:
- **#36:** No unit test for the N+1 batch fix in `generate_google_doc`.
- **#51:** New orchestrator bare-entity helpers covered only end-to-end.
- **#85:** `_estimate_load_error_envelope` / `_coerce_company_oid` lack direct tests.
- **#98:** Four new `agent_helpers/` public functions lack direct tests.
- **#111:** Anonymous Firebase token → "Unknown User" fallback never exercised.
- **#129:** Page-level auto-save + dialog flows still need page-level tests.
- **#168:** Nine new cross-resource agent helpers covered only via integration tests.
- **#217:** New `PlanPickerGrid` behaviors lack assertions.
- **#227:** New `joinWaitlist` field has no automated tests.
- **#232:** `_build_response_envelope` lacks a direct shape test.

**Absorbed:** #36, #51, #85, #98, #111, #129, #168, #217, #227, #232 — specific test-gap instances surfaced in later review passes. See `## Closed` for original bodies.

</details>

---

### 18. [MEDIUM] File-size threshold — `agents/estimate/service.py` now at 5,098 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: MEDIUM (architectural drift)

Entry #4 above already flags the HIGH-threshold files. Updating the
numbers: after the 2026-04-22 session, `agents/estimate/service.py` is now
~5,098 lines, `routers/agents.py` is ~2,892, `routers/estimates.py` is
~2,548. The extraction plan in entry #4 still applies; nothing added this
session is individually large, but the pile keeps growing.

</details>

---

### 36. [MEDIUM] No unit test for the N+1 batch fix in `generate_google_doc`
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: `routers/estimates.py:2368`
**Severity**: MEDIUM

The loop → `Contact.find({"_id": {"$in": list(property_info.contacts)}})`
batch change is covered only by inspection. A targeted unit test requires
a full TestClient + Drive mock + Mongo fixtures, which is why it didn't
land in the #1 fix. The agent-level sibling (`_fetch_linked_contacts`) is
tested in [tests/test_property_agent.py](../../platform/tests/test_property_agent.py).

Fix: either (a) add a TestClient case in
[tests/test_estimate_doc_generator.py](../../platform/tests/test_estimate_doc_generator.py)
that asserts `Contact.find` is called once and `Contact.get` is never
called; or (b) extract the contact-fetch out of the route into a helper
in `services/` and test the helper directly. Option (b) has the side
benefit of letting the same helper back the Maple-side path.

</details>

---

### 37. [LOW] ~~`_handle_get_estimate` falls through to an unscoped `Estimate.find_one` when `company_id` is invalid~~ — RESOLVED 2026-05-07

Fixed in commit `dfb8184` (2026-05-07). `_handle_get_estimate` now coerces
`company_id` to `company_oid` immediately after the latest-estimate
shortcut and returns the same "need a company" clarification envelope
that `_handle_list_estimates` uses when the cast fails. The downstream
`Estimate.find_one(...)` is now scoped via `Estimate.company == company_oid`,
closing the cross-tenant fallback. Original entry below.


**File**: `agents/estimate/service.py` — inside `_handle_get_estimate`,
around the `if company_oid is not None: ... else: ...` branch
(~lines 3787-3794 post-fix).
**Severity**: LOW (tenant-isolation gap — narrow path, but real)

When `PydanticObjectId(company_id)` fails (invalid hex string), the
narrowed `(InvalidId, TypeError)` except sets `company_oid = None`, and
the subsequent handler runs `await Estimate.find_one(Estimate.estimate_id
== code)` — an **unscoped** query that returns any estimate in the
platform with that code. Pre-existing pattern; the #1 narrow-except
change preserved it rather than introducing it. The sibling
`_handle_list_estimates` already gates behind `company_oid is None` and
returns a clarification envelope — get_estimate should mirror that.

Fix: after the ObjectId cast, if `company_oid is None`, return a
"need a company" clarification envelope (same shape as
`_handle_list_estimates` uses) instead of running the unscoped
`find_one`. Theme-adjacent to entry #20 (narrow-except in the latest
resolver) and the tenant-leak fix that already landed for
`_resolve_latest_estimate`.

---

---

### 40. [MEDIUM] ~~`portal/firebase.json` has no security-header config~~ — RESOLVED 2026-05-07

Landed in commit `692069f` ("chore: add HSTS and clickjacking headers to
firebase hosting config"). `portal/firebase.json` now ships all four
recommended headers on every response: `Strict-Transport-Security:
max-age=31536000; includeSubDomains`, `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`.
A real CSP is still a larger undertaking and remains deferred. Original
entry below.


**File**: [portal/firebase.json](portal/firebase.json)
**Severity**: MEDIUM

The hosting block contains only `public`, `ignore`, and `rewrites` — no
`headers` array. That means the deployed portal serves no CSP, no HSTS,
no `X-Frame-Options`, no `X-Content-Type-Options`, no `Referrer-Policy`,
and no `Permissions-Policy`. Firebase Hosting emits these only when
they are explicitly configured.

Fix: add a `headers` array covering at minimum:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

A real CSP is a larger undertaking — enumerate allowed `script-src`
(Vite chunks), `connect-src` (the API host from `VITE_API_URL` plus
Firebase Auth domains), `img-src` (user-uploaded assets, Firebase
Storage if used), and `style-src`. Ship the four simple headers first;
tackle CSP as its own change once the allow-lists are stable.

---

### 41. [MEDIUM] ~~`except Exception` around httpx calls in `address_service.py` could mask future `HTTPException`~~ — RESOLVED 2026-05-07

Narrowed to `except (httpx.HTTPError, httpx.TimeoutException):` in
`autocomplete`, `resolve_place_id`, and `normalize_address_parts`. Added
`test_google_address_service_propagates_http_exception_from_inside_request`
which monkeypatches `httpx.AsyncClient.get` to raise
`HTTPException(429)` from inside the `try` and asserts all three methods
re-raise instead of returning empty results. Original entry below for
context.


**File**: [services/address_service.py](platform/services/address_service.py) lines 324-418 (three sites)
**Severity**: MEDIUM (defensive)

Each of `autocomplete`, `resolve_place_id`, and `normalize_address_parts`
has a `try/except Exception:` wrapping the httpx call that returns `[]`
or `{}` on any failure. This is fine today — `_enforce_maps_rate_limit`
runs **before** the `try`, so its `HTTPException(429)` propagates
naturally. The concern is that a future refactor that moves the
enforce call inside the `try` would silently swallow the 429 and turn
a rate-limit rejection into an empty result, defeating the point of
the limiter.

Fix: narrow each `except Exception:` to
`except (httpx.HTTPError, httpx.TimeoutException):` so unrelated
failures (including any `HTTPException` raised from inside the block)
propagate naturally. Zero behaviour change in the happy path; makes
the invariant explicit to the next reader.

---

---

### 42. [MEDIUM] ~~No unit test for the `handleStatusChange` dispatcher~~ — RESOLVED 2026-05-07

Extracted `resolveStatusChangeApi(currentStatus, target, { approvedBy })`
as a pure helper alongside `getAllowedTransitions` in
`portal/src/lib/estimateStatus.ts`. Returns
`{ kind: "archive" | "unarchive" | "update", payload?: { status?: string;
approved_by?: string } }`. `NewEstimateWithActivityPage.handleStatusChange`
is now a thin switch on `kind`. Six new unit tests in
`tests/estimateStatus.test.ts` cover all routing branches (archive,
unarchive-from-archived-only, approved+approver, plain status update,
review-from-non-archived). Original entry below.


**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx) — `handleStatusChange` around line 444
**Severity**: MEDIUM

The consolidated handler routes between three API paths (`estimatesApi.archive`,
`estimatesApi.unarchive`, `estimatesApi.update`) based on `target` +
`currentNormalized`. `getAllowedTransitions` is covered by 15 vitest cases,
but the routing decision inside the page is not tested anywhere.
CLAUDE.md's TDD rule applies to `.tsx` behaviour changes.

Fix: extract the routing decision into a pure helper beside
`getAllowedTransitions` — e.g. `resolveStatusChangeApi(currentStatus,
target): { kind: "archive" | "unarchive" | "update", payload?: { status?:
string; approved_by?: string } }` — and unit-test it. The page handler
becomes a thin switch on `kind`. Cheap.

---

### 46. [LOW] ~~State machine is frontend-only (by design, re-filed for visibility)~~ — RESOLVED 2026-05-09

Backend now mirrors `portal/src/lib/estimateStatus.ts:TRANSITIONS_BY_STATUS`.
Added `ESTIMATE_STATUS_TRANSITIONS` map + `validate_estimate_status_transition(current, target)`
helper in `platform/models/estimate.py`. The PUT `/estimates/{id}` handler
calls the validator after `parse_estimate_status` and raises
`HTTPException(400, "Invalid transition: {current} → {target}")` on
forbidden moves (Lost → Won, Won → Approved, OnHold → Draft, etc.).
`Approved` retains the "unapprove" escape hatch (any non-Approved target)
so the existing role-gated unapprove flow keeps working; legacy/system
statuses (Generating/Failed/Submitted/Scheduled/Completed/Deleted) are
unconstrained.

Tests: 11-case `TestValidateEstimateStatusTransition` unit class plus
`test_update_estimate_rejects_invalid_status_transition` integration test
(Lost → Won returns 400, Lost → Review returns 200). All 88
`tests/test_estimate_api.py` cases plus the related versioning / quota
suites green.


**File**: [platform/routers/estimates.py](../../platform/routers/estimates.py) — `update_estimate` handler (~L1777), `unarchive_estimate` (~L2244)
**Severity**: LOW

Per the plan (see `documentation/development/plans/create-a-plan-to-lively-karp.md`),
backend PUT `/estimates/{id}` still accepts any `{status: "..."}` value.
An API caller bypassing the UI can drive invalid transitions (e.g. Lost →
Won, or reopening Archived via PUT instead of `/unarchive`). The UI
enforces the state table via `getAllowedTransitions`; the backend does
not.

Fix: when a non-UI API surface matters (public API, external
integrations, Maple agent moves beyond current verbs), add a
`validate_transition(current, target)` check in the PUT handler before
`estimate.set(...)`. Shape: raise `HTTPException(status_code=400,
detail=f"Invalid transition: {current.value} → {target.value}")`. Mirror
the `TRANSITIONS_BY_STATUS` map from the frontend, or better, define it
once in `models/estimate.py` and import from both.

---

---

### 48. [MEDIUM] ~~`_LABOUR_ROLE_TOKENS` drifts from `DOMAIN_HINTS["labour"]`~~ — RESOLVED 2026-05-07

Added `LABOUR_ROLE_HINTS: Tuple[str, ...]` export to
`agents/orchestrator/intents.py` as the single source of truth for the
sufficient-on-their-own role tokens. `_LABOUR_ROLE_TOKENS` in
`service.py` now derives via `frozenset(LABOUR_ROLE_HINTS)`. New test
`test_labour_role_hints_are_single_source_of_truth` asserts the role
hints are a subset of `DOMAIN_HINTS["labour"]` and equal to the
service-level frozenset. Adding a new role now means appending to one
constant. Original entry below.


**File**: [agents/orchestrator/service.py:77](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

The frozenset is maintained manually with a "kept in sync with
intents.py" comment. If a new role is added to `DOMAIN_HINTS["labour"]`,
the set won't auto-update and verbless-labour bare tokens silently stop
working.

Fix: split `DOMAIN_HINTS["labour"]` in `intents.py` into
`_GENERIC_LABOUR_HINTS` + `_LABOUR_ROLE_HINTS`, export the role-hints
list, and re-use it in `service.py`. Cleaner than the alternative of
filtering generic keywords out of the combined list at import time.

---

### 50. [MEDIUM] ~~Duplicate stopword lists in the orchestrator~~ — RESOLVED 2026-05-07

Extracted `_COMMON_FILLER_STOPWORDS` frozenset (19 entries — the
greeting/pronoun/acknowledgement fillers shared by both heuristics).
`_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` now derive
via `_COMMON_FILLER_STOPWORDS | frozenset({...domain-specific delta})`.
New test `test_stopword_sets_share_common_filler_base` asserts the
common set's exact contents and that both downstream sets are
supersets. Original entry below.


**File**: [agents/orchestrator/service.py:88, :130](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM

`_PERSON_NAME_STOPWORDS` and `_MATERIAL_RESIDUAL_STOPWORDS` share ~14
entries (`hi`, `hey`, `the`, `that`, `my`, `your`, `our`, `no`, `yes`,
`ok`, `okay`, `thank`, `thanks`, `please`, `sorry`). Two lists to keep
in sync when adding a new filler.

Fix: extract `_COMMON_FILLER_STOPWORDS` frozenset; union with
domain-specific additions for each downstream use.

---

### 51. [MEDIUM] No direct unit tests for the new bare-entity helpers
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [agents/orchestrator/service.py:372, :395, :404](../../platform/agents/orchestrator/service.py)
**Severity**: MEDIUM (TDD policy)

`_is_bare_entity_reference`, `_looks_like_person_name`, and
`_bare_entity_residual` are covered end-to-end via
`tests/test_maple_crud_coverage.py` but have no direct unit tests.
Edge cases (empty string, unicode names like "Renée Dupont",
punctuation-heavy input, adversarial input) aren't exercised.
CLAUDE.md's TDD rule applies to new `.py` behaviour.

Fix: add `tests/test_orchestrator_bare_entity_helpers.py` with ~10
parametrized cases per helper — edge cases plus golden paths.

</details>

---

### 52. [LOW] Inline comments instead of docstrings on new helpers
**Folded into #10.** Specific instance of the "missing docstrings on public APIs" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [agents/orchestrator/service.py:395, :404](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (style)

Project leans toward docstrings on methods (see `_format_chat_history`,
`_build_entity_context_summary`, etc.). My new helpers use inline
`# ` comments instead. Cosmetic only.

Fix: convert the prose comments to proper docstrings. Do when next
touching the file.

</details>

---

### 54. [LOW] ~~Tier 1 gap: `set <name>'s <field> to <value>` pattern~~ — RESOLVED 2026-05-07

Closed without changing `ACTION_HINTS["update"]`. The dedicated
`SET_POSSESSIVE_UPDATE_PATTERN` regex (`agents/text_utils.py:467`) and
`FIELD_OF_UPDATE_PATTERN` (`agents/text_utils.py:481`) — invoked from
`_match_possessive_or_field_targeted` — now handle the `set X's Y to Z`
and `set the <field> of/on/for <name> to <value>` shapes for all four
resources. The latest `tests/reports/maple_crud_gap_report.md` confirms
Tier 1 ✅ for every documented `set …` phrasing.

Adding a bare `"set"` (or `"set "`) entry to `ACTION_HINTS["update"]`
was rejected: the matcher uses `text.find()` substring scan, so `"set "`
false-positives on tokens like `asset `, `subset `, and `sunset `,
which would mis-route benign phrasings to update.

---

### 56. [LOW] Tier 1 gap: `what's <name>'s <field>?` contraction not handled
**File**: [agents/orchestrator/intents.py:131-150](../../platform/agents/orchestrator/intents.py) (`ACTION_HINTS["get"]`)
**Severity**: LOW

`ACTION_HINTS["get"]` contains `"what is"` but not `"what's"` — the
contraction. Phrasings like `"what's John Doe's phone?"` or `"what's
Landscaper's cost?"` therefore fail rule-level action detection, even
when the domain resolves via `phone` / `cost` / the name heuristic.

**RESOLVED 2026-05-07** — closed without changing `ACTION_HINTS["get"]`.
The `POSSESSIVE_LOOKUP_PATTERN` invoked from
`_match_possessive_or_field_targeted` (Shape 3) now anchors before
action-hint matching and resolves `[verb] <name>'s <field>` /
`<name>'s <field>` directly to `get_<domain>`, bypassing the
contraction gap entirely. The latest `tests/reports/maple_crud_gap_report.md`
shows ✅ Tier 1 for every `what's <name>'s <field>?` case across all
four resources.

---

### 58. [HIGH] `PortalLayout.tsx` over the 800-line HIGH threshold (canonical)
**Closed as resolved 2026-05-13.** Multi-session refactor reduced PortalLayout.tsx from 1,923 to under 800 lines across 5 sessions. Final state: 598 lines. Extractions: CompanyDialog, SettingsDialog, TeamMembersDialog, AiPanel, and hooks (useMapleAgent / useCompanyDetails / useAccountForm). All session diffs are byte-preserving refactors; user smoke-tested at each step.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: HIGH (in progress — partial 2026-05-09)
Canonical entry; #169 and #176 are duplicate flags from later review
passes — consolidated here on 2026-05-09.

Progress 2026-05-09: extracted pure-data and pure-helper layers out of
the file:
- `components/Layout/portalLayoutData.ts` — `countryOptions`,
  `canadaProvinceOptions`, `usStateOptions`, `ProvinceStateOption`
- `components/Layout/portalLayoutHelpers.tsx` — `getCompanyFormState`,
  `getAccountFormState`, `createConversationId`,
  `isAuthenticatedMember`, `ThinkingIndicator`, plus the
  `CompanyFormState` / `AccountFormState` / `CompanyDetails` /
  `PortalUser` / `TeamMember` interfaces.

Result: 2,094 → 1,917 lines. Still over the 800 HIGH threshold; full
suite (477 portal tests) and `tsc --noEmit` both clean.

Progress 2026-05-19: extracted the Company settings dialog into
`components/Layout/CompanyDialog.tsx` (~364 lines moved). The new
component takes 14 props (open, onClose, isLoading, isEditing,
isSaving, companyDetails, companyForm, companyFormError,
provinceStateOptions, provinceStateLabel, onEdit, onCancelEdit, onSave,
onFieldChange). PortalLayout.tsx now at 1,559 lines. Lint + build
clean; no PortalLayout component tests exist yet so verification is
build-level only.

Progress 2026-05-19 (session 2): extracted the Account/Settings modal
into `components/Layout/SettingsDialog.tsx` (~119 lines moved, 174-line
new file). The new component takes 11 props (open, onClose,
currentUser, accountForm, accountFormError, isAccountEditing,
isAccountSaving, onAccountFieldChange, onAccountEdit,
onAccountCancelEdit, onAccountSave). PortalLayout.tsx now at 1,440
lines. Also removed now-unused `PhoneInput` and `formatPhone` imports
from PortalLayout.tsx. Lint, `tsc --noEmit`, and build all clean.

Progress 2026-05-19 (session 3): extracted the Team Members modal into
`components/Layout/TeamMembersDialog.tsx` (~68 lines moved, 107-line
new file). The new component takes 6 props (open, onClose, teamMembers,
isTeamMembersLoading, teamMembersError, currentUser). PortalLayout.tsx
now at 1,372 lines. Also removed now-unused `Modal` and
`isAuthenticatedMember` imports from PortalLayout.tsx. Lint,
`tsc --noEmit`, and build all clean. The right-side Maple AI panel
state extraction was considered but deferred: `aiContext`,
`currentViewedEstimate`, and several effects cross panel/route/company
boundaries (e.g. `aiContext` is rewritten on company-change events and
route changes, not just by panel handlers), so a clean hook boundary
requires more tracing than fits a single bounded session.

Progress 2026-05-19 (session 4): extracted the Maple AI panel
(desktop right-side aside + mobile bottom-sheet aside + floating
toggle button + message/composer render helpers) into
`components/Layout/AiPanel.tsx` (~216 lines moved, 308-line new
file). State stays in PortalLayout; AiPanel is purely presentational
with 18 props across 5 categories: open state (2), conversation
state (4), composer callbacks (5), refs (2), side-panel state (4),
nav-footer JSX (1). The `HELP_CHIPS` constant and `AiMessage`
interface moved with the component (AiMessage re-exported and
re-imported by PortalLayout for its useState typing). Also removed
now-unused `Send`/`Trash2`/`Loader2` lucide imports and
`MapleMarkdown`/`ThinkingIndicator`/`FeedbackPanel`/`ChangeLogPanel`
imports from PortalLayout.tsx. PortalLayout.tsx now at 1,156 lines
(cumulative 1,923 -> 1,156 across sessions 1-4 = 767 lines reduced).
AiPanelProvider boundary stays in PortalLayout wrapping the whole
tree, untouched. Lint, `tsc --noEmit`, and build all clean.

Progress 2026-05-13 (session 5): extracted `useMapleAgent` /
`useCompanyDetails` / `useAccountForm` hooks (~558 lines moved across
three new files: useMapleAgent.ts 398 lines, useCompanyDetails.ts 233
lines, useAccountForm.ts 135 lines). PortalLayout.tsx now at 598
lines — under the 800-line threshold. The combined company-changed
+ estimate-loaded `useEffect` was split into two independent effects
(one per hook); both register listeners on mount with `[]` deps and
have no shared state, so behavior is identical. Lint, `tsc --noEmit`,
and build all clean.

Next steps (left for a planned session — risky without component
tests for `PortalLayout`): extract the three big in-file modals
(Settings ~130 lines, Company ~378 lines, TeamMembers ~74 lines), the
mobile + desktop AI panel branches, and the `MapleFloatingButton`.
The Maple panel (header + messages + composer + footer +
Feedback/ChangeLog overlays) is a natural `components/maple/MaplePanel.tsx`
with a `variant="mobile" | "desktop"` prop since both branches render
nearly-identical markup. Until component tests exist for PortalLayout,
each modal extraction needs a manual UI smoke test.

**Absorbed:** #126, #169, #176 — duplicate findings on the same file from later review passes. See `## Closed` for their original bodies.

</details>

---

### 65. [MEDIUM] ~~"Unknown" division is selectable in the Work Item dropdown~~ — RESOLVED 2026-05-07

Closed in two stages:
1. Commit `1b75358` ("fix: render Unknown division fallback option as
   disabled") — first pass making the fallback non-selectable.
2. Commit `2008afe` ("feat: map legacy Others division to Unassigned in
   the FE") — replaced the unrecognized "Unknown" sentinel with
   "Unassigned", which is now a first-class division in the BE
   (`EstimateDivision.UNASSIGNED`), the seed CSV
   (`platform/data/default_divisions.csv`), and the FE resolver
   (`portal/src/lib/divisionResolve.ts`). New companies bootstrap with
   "Unassigned" as a real division row, so the synthetic dropdown option
   appears only for legacy companies — and persisting it now writes the
   universally-recognized sentinel rather than a dead string. Aggregation
   helpers (`resolveDivisionName`, `bucketJobItemsByDivision`,
   `filterStaleDivisions`) all bucket stale/missing values back into the
   "Unassigned" canonical name.

Coverage: `portal/tests/divisionResolve.test.ts` (resolution,
bucket-into-Unassigned, legacy-Others rewrite, stale-name handling) and
`portal/tests/WorkItemInlineContent.test.tsx` (`stale division values
not in the company list are mapped to "Unassigned"`).


**File**: [portal/src/components/estimates/WorkItemInlineContent.tsx:236-238](../../portal/src/components/estimates/WorkItemInlineContent.tsx)
**Severity**: MEDIUM

When the stored `division` value isn't in the company's fetched list,
the dropdown renders `"Unknown"` as the displayed value. The locked
spec said "Unknown" should be a display-only fallback — but the option
is currently `<option value="Unknown">Unknown</option>`, so a user
clicking it persists the literal string `"Unknown"` to the DB. That
value will never match a real division on subsequent loads, so it
self-perpetuates.

Fix: render the Unknown `<option>` with `disabled`, or in the `onChange`
handler ignore the literal `"Unknown"` value and keep the prior state.
Add a frontend test that exercises the fallback path with a stale
division name.

---

### 66. [MEDIUM] No unique compound index on Division `(name, company)`
**Folded into #60.** Specific instance of the "compound-index data-integrity" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: [platform/models/division.py](../../platform/models/division.py),
[platform/services/division_bootstrap.py](../../platform/services/division_bootstrap.py)
**Severity**: MEDIUM

The Division model indexes `company` only. The bootstrap's "find then
insert" pattern and the POST endpoint both check existence before
inserting, but there's no unique constraint backing them — two
concurrent POSTs with the same name produce two rows. Same gap exists
on `MaterialCategory` (entry #60), so this is propagating a known
pattern rather than introducing a new one. Flagging it explicitly so
both can be fixed together.

Fix: add `IndexModel([("company", ASCENDING), ("name", ASCENDING)],
unique=True)` to `Division.Settings.indexes` (and to MaterialCategory
in the same pass). Backfill existing duplicates via a one-off cleanup
script before applying the index in production.

</details>

---

### 81. [MEDIUM] ~~`react-hooks/exhaustive-deps` disabled in 3 new settings tab components~~ — RESOLVED 2026-05-07

Wrapped `fetchDivisions` / `fetchUnits` / `fetchCategories` in
`useCallback(..., [companyId])` and added the callback to the effect's
dependency array — matches the pattern in `RateCardsTab.tsx`. The three
`// eslint-disable-next-line react-hooks/exhaustive-deps` comments are
gone. Original entry below.


**Files**: [portal/src/components/settings/DivisionsTab.tsx:55](../../portal/src/components/settings/DivisionsTab.tsx),
[portal/src/components/settings/MaterialUnitsTab.tsx:55](../../portal/src/components/settings/MaterialUnitsTab.tsx),
[portal/src/components/settings/MaterialCategoriesTab.tsx:56](../../portal/src/components/settings/MaterialCategoriesTab.tsx)
**Severity**: MEDIUM

All three new tab components use
`// eslint-disable-next-line react-hooks/exhaustive-deps` on the
`useEffect` that calls `fetchX()` when `active` flips to true. Disabling
the rule masks a stale-closure risk if `companyId` ever changes between
renders. The existing `RateCardsTab.tsx` solves the same problem cleanly
with `useCallback`.

Fix: wrap each fetch helper in
`useCallback(async () => { ... }, [companyId])`, list the callback in the
effect's deps, and drop the eslint-disable comment. ~6 lines per file.
Mirror the pattern in `portal/src/components/settings/RateCardsTab.tsx`
(lines 46-61).

---

### 84. [MEDIUM] `_coerce_company_oid` returns `Optional[Any]` to keep lazy beanie import
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) — `_coerce_company_oid` (added 2026-04-26)
**Severity**: MEDIUM (style / future-proofing)

The new helper has return annotation `Optional[Any]` so the
`from beanie import PydanticObjectId` import can stay lazy (inside the
function body), matching ~20 other lazy-import sites in this file. The
docstring documents the actual return shape, but static-typing precision
is lost at every call site.

The lazy-import pattern itself looks like a leftover artifact rather
than a deliberate decision — `bson.ObjectId` is already imported at
module level (line 22), and beanie is fully loaded by the time
`agents/estimate/service.py` is evaluated. There's no obvious circular
import to defend against.

Fix: when entry #3 (mypy baseline) lands, promote
`from beanie import PydanticObjectId` to module level and tighten
`_coerce_company_oid`'s return annotation to `Optional[PydanticObjectId]`.
~20 in-function `from beanie import PydanticObjectId` lines can also be
removed at the same time. Don't fix in isolation — bundle with the mypy
work since it's the easiest place to verify nothing breaks.

</details>

---

### 85. [LOW] No direct unit tests for `_estimate_load_error_envelope` and `_coerce_company_oid`
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py) — both helpers added 2026-04-26 in the #80 refactor
**Severity**: LOW (TDD policy, private helpers)

Both helpers are exercised transitively via `_load_estimate_for_update`
and `_load_estimate_for_read`, but lack direct tests. Edge cases worth
pinning: empty `company_id`, malformed ObjectId hex (e.g. "abc"),
`TypeError` cast input (e.g. `None`), and the `probability` fallback
when `orchestrator_confidence` is missing from the context dict.

Theme-adjacent to entry #51 (`_is_bare_entity_reference` etc. covered
only end-to-end). CLAUDE.md's TDD rule applies softly to private
helpers, so this is filed as LOW rather than MEDIUM.

Fix: add ~6-8 parametrized cases to a new
`tests/test_estimate_load_helpers.py` (or extend `test_estimate_agent.py`
with a small section). Quick to write since both helpers are pure or
near-pure.

</details>

---

### 86. [MEDIUM] `union-attr` on `dict.get(...)` chains (92 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `agents/property/service.py`, `agents/contact/service.py`,
`agents/material/service.py`, `agents/labour/service.py`,
`agents/equipment/service.py` — typically `context.get("...")` followed by
attribute access without a None guard.
**Severity**: MEDIUM (mostly false positives — context is always a dict in
practice, but mypy can't see the call-site contract)

The agent `process()` methods all accept `context: Optional[dict[str, Any]] =
None` and call `context.get(...)` deep in the body. Pydantic narrows the
type at the entry point, but mypy doesn't see the early `if context is
None: context = {}` guard because it's done implicitly via `.get()`-on-None
(which crashes at runtime if it ever happens).

Fix (per-agent): early in each `process()`, normalize the context with
`context = context or {}` and re-bind to a `dict[str, Any]` local. Mypy
sees the narrowed type and the 92 false positives collapse. Apply
opportunistically when next refactoring each agent.

</details>

---

### 87. [MEDIUM] `arg-type` on `PydanticObjectId | None` → required (~25 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `routers/companies.py`, `routers/estimates.py`,
`routers/materials.py`, `routers/properties.py`,
`services/company_service.py`, `scripts/db/backfill_divisions.py`
**Severity**: MEDIUM (legitimate gap)

`current_user.company` is `Optional[PydanticObjectId]` because users can
exist without a company (pre-onboarding). Functions like
`assert_company_access` and `get_company_defaults` declare a required
`PydanticObjectId` param. The handlers should explicitly raise 401/403
when `current_user.company is None` instead of leaning on Pydantic's
runtime coercion.

Fix: add a `_require_company(current_user)` helper in `dependencies.py`
that returns `PydanticObjectId` or raises `HTTPException(401, "User has
no company")`. Use it at the top of every handler that currently passes
`current_user.company` to a function expecting required ObjectId.

</details>

---

### 88. [MEDIUM] `assignment` — implicit-Optional defaults (~50 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `agents/estimate/service.py` (~20 sites including 7 `tokens:
TokenUsageAccumulator = None`), `agents/orchestrator/service.py`,
`prompts/estimate_react.py`, `prompts/estimate_architect.py`,
`agents/estimate/conversation_guide.py`
**Severity**: MEDIUM (mechanical, but high volume)

Pattern is `def f(x: T = None)` where T is non-Optional. Two fixes:
- For agent helpers where None is a real signal (e.g.
  `tokens: TokenUsageAccumulator = None`), change to `Optional[T] = None`.
- For prompt-builder kwargs (`property: str = None`, `industry: str =
  None`, `company: str = None`), change to `str = ""` if empty-string is
  the actual sentinel — many of these immediately do `(value or "").strip()`
  so the empty-string default is closer to the true contract.

Do NOT apply to FastAPI `Request = None` params (see entry #3 fix notes).

</details>

---

### 89. [MEDIUM] `arg-type` on `agents/*/service.py` — `Material | None` → `Material` (~30 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `agents/material/service.py`, `agents/labour/service.py`,
`agents/equipment/service.py`, `agents/property/service.py`,
`agents/contact/service.py`
**Severity**: MEDIUM (real defensiveness gap)

After `await Material.find_one(...)` the result is `Material | None`,
but the result is passed directly to `_material_to_dict(material)`
without checking. If the lookup misses, the helper crashes with
`AttributeError`. In practice the find calls are guarded by an earlier
existence check, so the misses don't reach the dict helper — but the
guards are easy to forget when adding new branches.

Fix: in each agent, change `_material_to_dict(material: Material)` to
accept `Optional[Material]` and return an empty-dict envelope on None.
Callers no longer need to guard. Same shape for Labour, Equipment,
Property, Contact.

</details>

---

### 90. [MEDIUM] `models/estimate.py` arithmetic on `Optional[int]` fields (16 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [models/estimate.py:157, 206-215](../../platform/models/estimate.py)
**Severity**: MEDIUM (latent bug if any nullable field is actually null)

Several `EstimateVersion` / `Estimate` fields are typed `Optional[int]`
but used in arithmetic (`<=`, `>=`, `-`, `len()`) without None guards.
Today they're always populated (the create/update handlers fill defaults),
but the types disagree with the runtime invariant.

Fix: tighten the model declarations to `int = 0` (or whatever the real
invariant is), or add `assert version.foo is not None` guards at the
arithmetic sites. Tightening the model is cleaner — touch a fixture or
two and the arithmetic just works.

</details>

---

### 91. [LOW] `call-arg` — `ChatOpenAI(openai_api_key=...)` signature drift (5 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `agents/orchestrator/service.py:148`,
`agents/material/service.py:167`, `agents/labour/service.py:125`,
`agents/equipment/service.py:115`, `agents/contact/service.py:112`,
`agents/property/service.py:88`
**Severity**: LOW (langchain version skew, runtime works)

mypy says `ChatOpenAI` doesn't accept `openai_api_key=`. The langchain
stub is out of date — the kwarg exists at runtime and the call works.

Fix: either upgrade `langchain-openai` to a version with synced stubs
(check the pin in `requirements.txt`), or pass the key via env-var
(`OPENAI_API_KEY`) and drop the kwarg. The env-var path is more
idiomatic and removes the dependency on stub freshness.

</details>

---

### 92. [LOW] `call-arg` — agent → router calls missing `http_request` (5 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `agents/material/service.py:1154-1157`,
`agents/labour/service.py:719-722`,
`agents/equipment/service.py:571-586`
**Severity**: LOW (agents pass None but the router's `http_request: Request
= None` default accepts it, see entry #3)

Each Maple CRUD agent calls the corresponding router function directly
(e.g. `await update_material(...)`) but doesn't pass `http_request`. The
router's `# type: ignore[assignment]` default makes this work at runtime.

Fix (long-term): extract the router body into a service helper that
doesn't need `http_request`, and have both the HTTP route and the agent
call the service. Audit logging would shift into the service or wrap the
service call. Big refactor — not blocking. In the short term, suppress
with `# type: ignore[call-arg]` at the agent call sites.

</details>

---

### 93. [LOW] `BlockingPortal | None` errors in tests (12 errors)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: `tests/test_rate_card_bootstrap.py` (9 sites),
`tests/test_audit_integration.py` (3 sites),
`tests/test_feedback_api.py` (2 sites),
`tests/test_company_api.py` (1 site),
`tests/test_divisions_api.py` (1 site)
**Severity**: LOW (tests, not production)

`pytest-anyio` returns `BlockingPortal | None` from the
`portal_blocking_portal` fixture. Tests call `portal.call(...)` without a
None guard.

Fix: add `assert portal is not None` (or a thin `_get_portal()` helper) at
the top of each test that uses the fixture. Pure mypy hygiene.

</details>

---

### 94. [HIGH] New material handlers all exceed the 50-line ceiling
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: HIGH (continuation of entry #4 — substantial progress 2026-05-09)

Update 2026-05-09 (second pass): all four documented per-handler
helper extractions landed.

| Handler | Before | After | Δ |
| --- | ---: | ---: | ---: |
| `_handle_create_material` | 175 → 163 → **85** | -90 |
| `_handle_get_material` | 122 → 106 → **49** ✓ | -73 |
| `_handle_list_materials` | 146 → 135 → **97** | -49 |
| `_handle_delete_material` | 101 → 92 → **90** | -11 |

`_handle_get_material` is now under the 50-line ceiling. The other
three remain over but the residual length is all genuine business
logic; envelope construction and the major sub-flows (resolution,
sizes-from-price, missing-fields computation, list filters,
size-scoped get, pending-delete cleanup, post-create finalisation)
are now in named helpers.

New helpers landed:
- `_resolve_create_category_unit_ids` — try/except wrapper around
  category/unit ObjectId resolution + sizes-with-unit construction
- `_default_sizes_from_price` — single-size entry from price/cost/size
- `_compute_missing_create_fields` — dedup'd missing-field list
- `_finalize_created_material` — context update + accuracy suggestions
  + post-create question
- `_resolve_list_name_hint` — count-query bypass + generic-stop-word
  filter
- `_fetch_list_materials` — fan-out by filter (category beats name
  beats fall-through)
- `_format_list_materials_response` — count vs. empty vs. populated
  response copy
- `_handle_get_material_size_scoped` — entire size-scoped get branch
- `_clear_pending_delete_context` — pending-delete bookkeeping
  cleanup after a successful delete

Verified: 255 platform tests pass across material/orchestrator/Maple-
coverage suites. Substantial progress; leaving open until the three
remaining handlers cross the 50-line ceiling, which would require
further decomposition that yields diminishing returns. **Original
notes preserved below.**



Progress 2026-05-09: extracted the response envelope into
`_build_response_envelope(...)` (the ~25-line method centralises the
canonical 15-key envelope used by every material handler). All 8
inline-dict returns across the four big handlers and
`_handle_list_material_categories` now call the helper. Material test
suites pass: `test_material_agent.py` (56), `test_material_api.py`,
`test_maple_material_size_operations.py` (78 total).

Updated handler line counts (2026-05-09):
- `_handle_create_material` — 163 (was 175; saved 12)
- `_handle_get_material` — 106 (was 122; saved 16)
- `_handle_list_materials` — 135 (was ~146; saved 11)
- `_handle_delete_material` — 92 (was 101; saved 9)
- `_handle_list_material_categories` — 33 (was 44)

None hit the 50-line ceiling yet — the residual length is genuinely
business logic (field resolution, sizing inference, pending-intent
bookkeeping), not envelope boilerplate. To get the four big handlers
fully under 50 lines, the next extraction targets are per-handler
helpers:

- `_handle_create_material`: split out the
  category/unit-resolution ladder (lines ~1462-1494) and the
  sizes-from-price construction (lines ~1496-1512) into private
  helpers. ~80 lines that don't belong in the orchestration shell.
- `_handle_list_materials`: extract the filter-resolution block
  (name_hint cleaning + category_filter_id + price_filter combination
  + the materials fetch dispatch) into `_resolve_list_filters(...)`.
  ~50 lines.
- `_handle_get_material`: split the size-scoped branch (lines
  ~1989-2024) into `_handle_get_material_size_scoped(...)`. ~40
  lines.
- `_handle_delete_material`: extract the pending-context cleanup
  (lines ~1942-1950) into `_clear_pending_delete_context(...)`. ~10
  lines.

Each is mechanical and the existing test suites cover the behavior.

Original notes preserved below for context:

Each one is mostly a single response-builder per branch. Next
extraction: factor out the repeated envelope shape (12 keys: `success`,
`query`, `intent`, `agent`, `confidence`, `matches`,
`needs_clarification`, `clarifying_question`, `response`, `result`,
`context`, `error`, `completion_ready`, `missing_fields`,
`accuracy_suggestions`) into a small builder helper. That alone would
shrink each handler by 30–40 lines.

`_handle_list_material_categories` (44 lines, 2026-04-26) is the only
existing handler under threshold and is the model to mirror.

</details>

---

### 95. [HIGH] ~~New `agent_helpers/` extractions exceed the 50-line ceiling~~ — RESOLVED 2026-05-07
**Files**: [platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py),
[platform/routers/agent_helpers/fuzzy_confirmation.py](../../platform/routers/agent_helpers/fuzzy_confirmation.py)
**Severity**: HIGH (continuation of entry #4 — resolved)

`estimate_update.py` — `run_update_estimate` (136 lines) split into
three focused functions:
- `_modify_items_refusal()` — modify-vs-add detection + refusal dict
  (54 lines incl. multi-line signature; 41 lines body)
- `_persist_added_job_items()` — merge / build / persist / response
  build (58 lines; 49 lines body)
- `run_update_estimate()` — orchestration shell (58 lines; 48 lines body)

`fuzzy_confirmation.py` — `handle_estimate_fuzzy_confirmation` (150
lines) split into two focused functions plus a small envelope helper:
- `_envelope()` — standard 11-key result template that deduplicates the
  three response-dict shapes (28 lines)
- `_dispatch_confirmed_intent()` — affirmative-branch dispatcher for
  delete / work-item-remove / add-items (69 lines)
- `handle_estimate_fuzzy_confirmation()` — main router for negative /
  affirmative / break / re-ask paths (79 lines)

The deep nesting flagged in entry #97 (`if is_affirmative_text:` branch
at 75 lines) is gone — the affirmative path is now a single delegation
to `_dispatch_confirmed_intent`.

TDD cycle: 5 direct unit tests for `_modify_items_refusal` and 3 direct
unit tests for `_dispatch_confirmed_intent` (delete success, work-item-
remove redispatch with `confirmed=True`, add-items pipeline with
mocked `run_update_estimate`). Pure refactor — 186 related tests
(orchestrator endpoint, agents API, estimate agent, new helpers) all
green.

Two methods (`_dispatch_confirmed_intent` 69 / `handle_estimate_fuzzy_confirmation`
79) remain over the strict 50-line ceiling — each path inside the
dispatcher is ~16 lines × 3 paths, and the main function still owns
pending-unpack + 3 distinct branch handlers. Splitting further would
be over-decomposition. Net win: 286 lines of two methods became 234
lines across five focused units, with single responsibilities and
direct test coverage.

---

### 96. [MEDIUM] ~~Pre-existing failing tests in `test_agents_api.py`~~ — FIXED 2026-04-26

Both tests were stale assertions left over from before the 2026-04-21
delete-safety hardening (`routers/agents.py:1975-1982`), which unified
exact-code and fuzzy-title delete paths to always require confirmation.

- `test_fuzzy_estimate_delete_requires_confirmation`: assertion at
  line 526 changed from `["fuzzy_confirmation"]` to `["confirmation"]`
  to match the unified envelope. The `is_fuzzy_match` flag still
  distinguishes the two paths on the result side.
- `test_exact_estimate_delete_executes_directly` → renamed to
  `test_exact_estimate_delete_requires_confirmation` and the assertions
  flipped: `needs_clarification=True`, `deleted_flags["deleted"] is
  False`, plus `PENDING_ESTIMATE_FUZZY_CONFIRMATION_KEY` IS now
  present. Source unchanged.

---

### 98. [LOW] No direct unit tests for the four new agent_helpers public functions
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: [platform/routers/agent_helpers/text_helpers.py](../../platform/routers/agent_helpers/text_helpers.py),
[platform/routers/agent_helpers/estimate_update.py](../../platform/routers/agent_helpers/estimate_update.py),
[platform/routers/agent_helpers/fuzzy_confirmation.py](../../platform/routers/agent_helpers/fuzzy_confirmation.py)
**Severity**: LOW (refactor, transitively covered)

Public functions added 2026-04-26:
- `is_affirmative_text(text: str) -> bool`
- `is_negative_text(text: str) -> bool`
- `run_update_estimate(...)` (async)
- `handle_estimate_fuzzy_confirmation(...)` (async)

End-to-end coverage exists via `tests/test_agents_api.py` (64 passing)
and `tests/test_orchestrator_endpoint.py`. CLAUDE.md's mandatory-testing
rule applies softly to refactors — but the two text predicates are pure
and would be a 5-minute parametrized test file. The async helpers carry
the same dependencies (DB + EstimateAgent) as the orchestrate endpoint
and are harder to pin in isolation.

Fix: add `tests/test_agent_helpers_text.py` with ~10 parametrized cases
covering each predicate (affirmative, negative, empty, whitespace,
mixed-case, leading/trailing punctuation). Defer the async-helper
direct tests until #94/#95 are split — easier to test smaller units.

</details>

---

### 99. [HIGH] ~~`_extract_fields_from_message` length growing past 200 lines~~ — RESOLVED 2026-05-09
File: `platform/agents/property/service.py:597`
**Severity**: HIGH (resolved)

Resolved 2026-05-09 along the exact strategy proposed in the original
fix note. Each address-shape parser is now its own helper returning
a partial dict, and the coordinator is a 26-line fold:

| Helper | Lines | Shape parsed |
| --- | --- | --- |
| `_extract_label_fields` | 30 | Labelled `name:`, `address:`, `city:`, `prov_state:`, `postal_zip:`, `country:`, `notes:` patterns + postal/prov normalisation |
| `_try_canadian_full_address` | 25 | "1234 Main St, Vancouver, BC, V1V 2A2" |
| `_try_us_zip_address` | 27 | "155 Asharoken Ave, Northport, NY 11768" |
| `_try_chunked_address` | 38 | Either-order country/postal: "…, BC, 32333, Canada" |
| `_try_partial_address` | 25 | Postal/country omitted: "888 River Rd, Richmond, BC" |
| `_try_at_prefix_canadian_address` | 35 | "at 123 Maple Drive, Surrey BC V3T 4R5" |

The label-pattern dict moved to a class attribute (`_LABEL_PATTERNS`)
so it's not re-allocated on every call. The coordinator pre-applies
the labelled-pattern extractor (whose matches win), then folds in
each address-shape parser via `setdefault` — earlier matches take
precedence, matching the original semantics. The at-prefix parser
remains gated behind "no street found yet" as before.

Verified: 71 property tests pass (`test_property_agent.py`,
`test_property_api.py`, `test_address_service.py`). Coordinator
dropped from ~207 → 26 lines.

---

### 111. [LOW] Missing test: anonymous Firebase token → "Unknown User <unknown>" fallback
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/tests/test_feedback_api.py](../../platform/tests/test_feedback_api.py), [platform/routers/feedback.py:87-89](../../platform/routers/feedback.py)
**Severity**: LOW (test gap)

Every existing feedback test injects `X-Test-Email`, so the defensive
branch in `submit_feedback` that handles a verified token *without* an
email (`full_name = "Unknown User"`, `email = "unknown"`) never runs in
the test suite. A regression that breaks the fallback (e.g. a future
refactor that drops the `or "unknown"` clause and 500s instead) would
ship undetected.

Fix: add a test that posts with a token that has `uid` but no `email`,
and assert the Trello card payload is built with `Unknown User <unknown>`.

</details>

---

### 122. [HIGH] ~~`_apply_low_confidence_fallback` is now ~84 lines~~ — RESOLVED 2026-05-07
**File**: [platform/agents/orchestrator/service.py:1424](../../platform/agents/orchestrator/service.py)
**Severity**: HIGH (function size — resolved)

Extracted `_try_guide_fallback(self, result, message, context,
best_confidence) -> Optional[Dict[str, Any]]` per the proposed plan.
Caller now uses `override = self._try_guide_fallback(...); if override
is not None: return override`. Final line counts:
- `_apply_low_confidence_fallback`: 40 lines (was 84 — confidence math
  + early-return + delegation only)
- `_try_guide_fallback`: 50 lines (interrogative→guide decision tree
  in one method with a single responsibility)

Both methods are now within the 50-line ceiling. TDD cycle: 4 direct
tests for `_try_guide_fallback` (off_topic short-circuit, non-
interrogative short-circuit, interrogative-with-guide-text mutation,
empty-guide passthrough) added in `tests/test_orchestrator_intents.py`.
All 185 orchestrator-intent tests + 124 related help/endpoint tests
green.

---

### 124. [MEDIUM] `openai_api_key=` keyword on ChatOpenAI flags mypy
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Files**:
- [platform/agents/maple_guide/service.py:111](../../platform/agents/maple_guide/service.py)
- [platform/agents/maple_public/service.py](../../platform/agents/maple_public/service.py) (pre-existing — pattern was copied into the new shared module)

**Severity**: MEDIUM (type hygiene)

`openai_api_key` is accepted via Pydantic alias on `ChatOpenAI`, but
mypy reports `Unexpected keyword argument` because the public type
signature uses `api_key`. Pre-existing pattern that propagated into
the new shared service.

Fix: rename to `api_key=settings.openai_api_key` everywhere. Functional
behavior identical; mypy clean.

</details>

---

### 125. [LOW] `platform/agents/orchestrator/service.py` at 1358 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py)
**Severity**: LOW (file size)

Pre-existing breach of the 800-line threshold; this PR added ~70 net
lines. Tracked under existing item [#4](#4-file-and-function-size).

</details>

---

### 126. [LOW] `portal/src/components/Layout/PortalLayout.tsx` at 2105 lines
**Merged into #58.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/components/Layout/PortalLayout.tsx](../../portal/src/components/Layout/PortalLayout.tsx)
**Severity**: LOW (file size)

This PR shrunk the file by ~35 lines via the
`lib/orchestratorReply.ts` extraction. Continue extracting closures
(`dispatchAgentMutation`, chip-set logic, agent-mutation handlers) into
`lib/` to keep chipping at this. Tracked under existing item [#4](#4-file-and-function-size).

</details>

---

### 127. [HIGH] New-estimate flow has no save mechanism
**Closed as obsolete.** Implemented as the suggested Option B: `NewEstimateWithActivityPage.tsx:272–298` auto-creates a draft estimate on mount via `estimatesApi.create(...)`, then `navigate(..., { replace: true })` to `/estimates/<newId>/with-activity` so the page reloads in edit mode and the existing auto-save path takes over. The in-code comment explicitly addresses the StrictMode unmount/remount hazard from prior feedback. Verified 2026-05-13 by user (draft survived navigate-back-to-listing).

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH

`persistWorkItems` falls back to `setIsDirty(true)` when not in edit
mode. Save Estimate was removed earlier in the session, so a user on
the new-estimate flow can fill in title/description/work items but has
no UI affordance to actually create the estimate. Pre-existing problem
that the dialog refactor cements.

Fix options:
- Re-introduce a "Create Estimate" button that's only visible on the
  new flow.
- Auto-create the estimate on first interaction (e.g., title blur)
  then fall through to the auto-save path for subsequent edits.

</details>

---

### 128. [HIGH] ~~Title and notes have no auto-save path~~ — RESOLVED 2026-05-01
**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH (resolved)

Both fields now auto-save:
- Title: `commitTitle` runs on blur + Enter → `autoSaveField({ title })`,
  with diff guard against `estimate.title`.
- Notes: `saveNotesDialog` runs from the Notes dialog Save button →
  `estimatesApi.update({ notes })`. Diff-guarded against `notes`. Dialog
  stays open during save, shows "Saving…" + inline error on failure;
  Cancel and backdrop close are blocked while saving. Mirrors the work
  item dialog pattern.

---

### 129. [HIGH] Missing tests for auto-save + dialog flows (partial)
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH

Component-level testing infrastructure landed 2026-05-02:
`@testing-library/react` + `jsdom` added, `vite.config.js` matches
`*.test.tsx` against jsdom. 29 component tests now cover the
extracted dialog/bar wrappers:

- `WorkItemDialog`: title text, Cancel/Save callbacks, disabled state
  while saving, errorMessage rendering.
- `DocumentsBar`: empty-state, auto-seed selection, re-seed when
  current selection becomes stale, generate/delete callbacks.
- `EstimateTitleBar`: read-only ↔ edit transition, blur/Enter commit,
  Details/Notes/Delete callbacks, status menu open + transition.

Still TODO (require deeper page-level mocking):
- `autoSaveField` race-handling end-to-end (the `sequenceGuard`
  helper is unit-tested in `tests/sequenceGuard.test.ts`; the wiring
  inside the page is not).
- `persistWorkItems` insert-vs-replace path.
- `saveWorkItemDialog` failure branches.
- Description blur ↔ stale-comparison wiring (the
  `lastSavedDescriptionRef` invariant; the helper-equivalent test
  for sequence guards is the closest existing coverage).

</details>

---

### 137. [MEDIUM] `NewEstimateWithActivityPage.tsx` extractions (partial)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: MEDIUM (file size)

The three named extraction targets landed 2026-05-02:
`<WorkItemDialog>`, `<DocumentsBar>`, `<EstimateTitleBar>`. Page is
now 1733 lines, down from 2044 — still over the 800-line guideline.
Further reductions need additional extractions:

- Work items table (~250 lines) — header row + map + per-row controls.
- Gap dialogs / inventory gap helpers — currently inline.
- Notes / Details / Delete / Delete-doc modals (small but repetitive).
- `handleChecklistPdfDownload` (currently inline in JSX).

Tracked under existing item [#4](#4-file-and-function-size). Next
single extraction round should target the work-items table.

</details>

---

### 155. [HIGH] ~~`_list_properties_by_cross_resource` is 124 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/property/service.py](../../platform/agents/property/service.py)

Resolved by extracting three helpers:
- `_build_list_properties_envelope` (32 lines) — single response-shape
  builder, replaces 5 duplicate envelope literals.
- `_resolve_estimate_linked_property` (33 lines) — three-step estimate→
  property resolution with `(property, error_message)` return.
- `_resolve_cross_resource_properties` (62 lines) — contact/material/
  labour dispatch returning `(properties, not_found_kind)`. Stays
  slightly over the 50-line ceiling per the original analysis (each
  branch differs by ~3 lines; further splitting is indirection without
  DRY payoff).

Parent function dropped from 248 → 88 lines. Tests
`tests/test_cross_resource_joins.py` and `tests/test_property_agent.py`
both green (67/67).

---

### 156. [HIGH] ~~`_list_contacts_at_property` is 108 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/contact/service.py](../../platform/agents/contact/service.py)

Resolved by extracting two helpers:
- `_build_list_contacts_envelope` (32 lines) — shared response-shape
  builder, used by both cross-resource handlers in this file.
- `_resolve_contacts_at_properties` (32 lines) — encapsulates the
  property-IDs → contacts join with optional `role_hint == "owner"`
  HOME_OWNER filter.

`_list_contacts_at_property` dropped from 108 → 70 lines.
`_list_contacts_for_estimate` got a free win too (135 → 91 lines)
since both call sites now share the envelope helper. Tests
`tests/test_cross_resource_joins.py` and `tests/test_contact_agent.py`
green (88/88).

---

### 158. [HIGH] ~~Property cross-resource type=contact loads full catalog~~ — FIXED 2026-05-03
**File**: [platform/agents/property/service.py](../../platform/agents/property/service.py)

Resolved by introducing a `_properties_linked_to_contacts(company_id,
contact_ids)` helper (paralleling `_properties_with_estimates_referencing`)
that runs a single indexed Mongo query
(`Property.find({"company": ..., "contacts": {"$in": contact_ids}})`)
instead of loading the full property catalog and filtering in Python.

The contact path in `_resolve_cross_resource_properties` now calls
this helper. Test
`test_property_agent_lists_properties_for_contact` was updated to stub
the new helper instead of `_list_properties_via_api`. Tests
`tests/test_cross_resource_joins.py` and `tests/test_property_agent.py`
green (67/67).

The pre-existing in-memory pattern in `_find_properties_by_owner_name`
and `_find_properties_by_name_or_address` is a separate refactor —
flagged in #159.

---

### 160. [HIGH] ~~`_handle_list_materials_for_estimate` is 98 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)

Resolved by:
- Local `clarification()` closure dedupes the two clarification-shape
  envelope returns inside the handler.
- New `_collect_estimate_material_items` static helper (27 lines) flattens
  matched + unmatched materials into display dicts (was a 22-line inline
  loop with `(unmatched)` suffix duplication).

Handler dropped from 98 → 74 lines. Still slightly over the 50-line
guideline, but the remaining body is the final result-shape dict
(used once) plus the items-empty / items-present branching — extracting
further would add indirection without DRY payoff.

The followup's "agent-wide envelope helper across `_handle_list_estimates`,
`_handle_create_material`, etc." is a separate, larger pass — out of
scope for this fix.

---

### 161. [HIGH] ~~`_handle_list_labours_for_estimate` is 91 lines~~ — FIXED 2026-05-03
**File**: [platform/agents/labour/service.py](../../platform/agents/labour/service.py)

Same shape as #160; same fix:
- Local `clarification()` closure for the two clarification returns.
- New `_collect_estimate_labour_items` static helper (26 lines).

Handler dropped from 91 → 73 lines. Tests
`tests/test_cross_resource_joins.py`, `tests/test_material_agent.py`,
and `tests/test_labour_agent.py` green (101/101).

---

### 162. [LOW] `_parse_estimate_date_filter` uses fixed day counts
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/estimate/service.py:354](../../platform/agents/estimate/service.py#L354)
**Severity**: LOW

`days_per_unit = {"day":1, "week":7, "month":30, "quarter":91, "year":365}`
— calendar-month edges and leap years are not handled. "Estimates from
this month" on Jan 31 will look back to Jan 1, but on Mar 1 will look
back to Jan 30, not Feb 1. Matches the docstring's "no calendar-month
edge cases" note but worth flagging.

Fix: swap to `dateutil.relativedelta` (already a transitive dep of
`langchain` so no new requirement) for strict calendar-aligned windows
when a user complaint surfaces. Defer until then.

</details>

---

### 165. [MEDIUM] `_list_properties_by_cross_resource` still 88 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/property/service.py:1078](../../platform/agents/property/service.py#L1078)
**Severity**: MEDIUM (function-length policy)

After #155 the parent dropped from 248 → 88 lines. Still over the
50-line CLAUDE.md guideline. Remaining body: estimate-branch label
pick + final response-rendering tail (which already calls the shared
`_build_list_properties_envelope` helper).

Accepted as-is. Splitting further pushes one-line dispatch into helpers
without DRY payoff. Re-flag only if a future change makes the function
harder to read.

</details>

---

### 166. [MEDIUM] `_list_contacts_for_estimate` still 91 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/contact/service.py:1092](../../platform/agents/contact/service.py#L1092)
**Severity**: MEDIUM (function-length policy)

Got a free DRY win during #156 (135 → 91 lines via shared envelope
helper) but remains over 50. Three guard clauses (estimate not found /
property not linked / property deleted) + property_label compute +
items-empty branching.

Fix (deferred): extract `_resolve_estimate_linked_property` (currently
only on the property agent) into `agents/cross_resource.py` so both
agents share a single estimate→property resolver. Drops the contact
helper to ~50 lines and removes the parallel implementation.

</details>

---

### 167. [LOW] `_resolve_cross_resource_properties` at 62 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/property/service.py:1015](../../platform/agents/property/service.py#L1015)
**Severity**: LOW (function-length policy)

Three near-identical contact / material / labour resolve+filter blocks
with ~3-line differences each. Extracted intentionally during #155;
the original analysis flagged "splitting per-type resolution into 3
helpers would add indirection without DRY payoff."

Accepted as-is. Re-evaluate only if a fourth cross-resource type joins
the dispatch.

</details>

---

### 168. [LOW] New helpers from #155/#156/#158/#160/#161 lack direct unit tests
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent. Previously absorbed #231.

<details>
<summary>Original body (preserved for history)</summary>

**Files**: property / contact / material / labour `service.py`
**Severity**: LOW (test coverage)

Nine new private helpers landed across the batch:
- `_build_list_properties_envelope`, `_resolve_estimate_linked_property`,
  `_resolve_cross_resource_properties`, `_properties_linked_to_contacts`
  (property agent)
- `_build_list_contacts_envelope`, `_resolve_contacts_at_properties`
  (contact agent)
- `_collect_estimate_material_items` (material agent)
- `_collect_estimate_labour_items` (labour agent)

All are exercised end-to-end by the existing 67–101 integration tests
(`tests/test_cross_resource_joins.py`, `test_property_agent.py`,
`test_contact_agent.py`, `test_material_agent.py`, `test_labour_agent.py`)
that pass after the refactor.

Per CLAUDE.md "Don't docstring private helpers" / pragmatic-coverage
norms: integration coverage is sufficient for pure refactors. Re-flag
only if these helpers grow public-facing semantics or if a regression
slips through that a unit test would have caught.

**Absorbed:** #231 — duplicate finding (no direct unit tests on newly-extracted helper/component) from a later review pass. See `## Closed` for its original body.

</details>

---

### 169. [HIGH] `PortalLayout.tsx` is ~1500 lines — duplicate of #58
**Merged into #58.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: HIGH (consolidated into #58 on 2026-05-09)
Same finding as #58. Both flag `PortalLayout.tsx` over the 800-line
HIGH threshold; track the refactor under #58 going forward. Notes
preserved below for context.

File is well over the 800-line guideline. The session's edits added
~10 lines on top of an already over-budget file. Natural extraction
candidates: the AI panel composer + message renderer, the settings/
account modal, and the feedback/changelog panel wiring — each ~200-300
lines and largely self-contained.

</details>

---

### 170. [MEDIUM] No component tests for `Modal` or `DashboardPage` division-seeding behavior
**Closed as obsolete.** #129's component-test infrastructure (`@testing-library/react` + jsdom) has since landed, so the gap this item flagged no longer exists.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: MEDIUM
CLAUDE.md mandates tests for behavior changes; the portal currently has
no component-test infrastructure under `src/` (vitest is configured at
the package level via `npm test`, but there are zero `*.test.tsx` files).
The Modal change (conditional positioning when AI panel is open) and
the Dashboard division-seeding logic are untested as a result.

First component test added will need to pull in
`@testing-library/react` + jsdom setup — not a one-line task. Worth
landing once another test-worthy frontend change comes along so the
scaffolding pays for itself.

</details>

---

### 171. [MEDIUM] `lg:right-[26rem]` in `Modal.tsx` duplicates `AI_PANEL_WIDTH`
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: MEDIUM
`Modal.tsx:32` hard-codes `lg:right-[26rem]` to match the desktop Maple
rail width, which is also declared in `PortalLayout.tsx:129` as
`AI_PANEL_WIDTH = 416 // w-[26rem]` and on the `<aside>` itself as
`w-[26rem]`. Three sites must agree; if the rail width changes, the
modal backdrop will silently misalign.

Fix: export an `AI_PANEL_WIDTH_CLASS` (or similar) constant from a
shared module (e.g. `lib/aiPanelContext.ts`) and reference it from all
three sites — or expose the value via `AiPanelContext` so consumers
build the className dynamically.

</details>

---

### 172. [HIGH] ~~`WorkItemInlineContent.tsx` now 834 lines (over the 800-line HIGH threshold)~~ — RESOLVED 2026-05-09
**Severity**: HIGH (resolved)

Extracted the Activities table into `components/estimates/ActivitiesTable.tsx`
(mirroring the existing `MaterialsTable.tsx` precedent). Props match
the same shape: rows + lookup items + readOnly + onAddRow / onUpdateRow /
onRemoveRow / onRoleSelect / onOpenCalc. `WorkItemInlineContent.tsx` is
now 724 lines — back under the 800 HIGH threshold. The 11-test
`WorkItemInlineContent.test.tsx` suite still passes; `tsc --noEmit`
clean. Closes #178 (same file flagged again on 2026-05-06).

Original notes preserved below for context:

This change pushed the file from ~760 to 834 lines (Adjust pill + dialog
mount + Original line + handleAdjustSet + handleProfitMarginChange +
originalTotal useMemo). The component was already at the limit before
this feature.

Natural extraction: the entire Pricing Breakdown block (Materials/Labor
subtotals → Overhead → Subtotal → + Profit → Tax → Work Item Total → Adjust
pill → Original line) is a self-contained ~150-line slice that takes only
the breakdown numbers and a handful of setters as props. Pulling it into
a `WorkItemPricingBreakdown` component would restore this file to under
800 lines and isolate the back-calc / Original-line logic with the rest
of the pricing UI.

---

### 176. [HIGH] `PortalLayout.tsx` is ~1500 lines (pre-existing) — duplicate of #58
**Merged into #58.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**Severity**: HIGH (consolidated into #58 on 2026-05-09)
Same finding as #58 / #169. Track the refactor under #58. Notes
preserved below for context.

`portal/src/components/Layout/PortalLayout.tsx` — sidebar, mobile sidebar,
top-bar logo regions, AI panel header (desktop + mobile), the floating
Maple FAB, and the Account modal all live in one file. Not introduced by
this change, but every edit here adds reach.

Fix: split into siblings — at minimum `MapleFloatingButton`, `AiPanel`,
and `AccountModal`. Out of scope for the recolor work; track for the next
time someone touches this file substantially.

</details>

---

### 178. [HIGH] ~~`WorkItemInlineContent.tsx` over the 800-line HIGH threshold~~ — RESOLVED 2026-05-09 (duplicate of #172)
**Severity**: HIGH (resolved)
Resolved together with #172 on 2026-05-09. The activities `<table>`
block was extracted into `components/estimates/ActivitiesTable.tsx`
(mirror of `MaterialsTable.tsx`), exactly as the fix recommendation
proposed. File now 724 lines.

---

### 180. [MEDIUM] ~~`raise HTTPException` inside `except` lacks `from None`~~ — RESOLVED 2026-05-07

Appended `from None` to all three `raise HTTPException(status_code=422,
detail="Invalid company id")` lines in `divisions.py`,
`material_categories.py`, `material_units.py`. Behaviour-neutral
mechanical sweep; the existing 422-test in each router file still
passes.


**Files**:
- [platform/routers/divisions.py:46](../../platform/routers/divisions.py)
- [platform/routers/material_categories.py:46](../../platform/routers/material_categories.py)
- [platform/routers/material_units.py:48](../../platform/routers/material_units.py)
**Severity**: MEDIUM (style)

The new `try / except (InvalidId, TypeError) → HTTPException(422)` blocks
in all three routers chain the original `InvalidId` via Python's implicit
`__context__`. Functional, but flake8-bugbear's `B904` flags the missing
`from` clause. Idiomatic shape is `raise HTTPException(...) from None`
when we deliberately want to suppress the inner cause from the response.

Fix: append `from None` to all three `raise HTTPException(422)` lines.
Mechanical, three-line sweep.

---

### 181. [MEDIUM] ~~Duplicate `PydanticObjectId` coercion pattern in estimate agent~~ — RESOLVED 2026-05-07

Replaced the inline `try / PydanticObjectId(company_id) if company_id
else None` casts in both `_handle_list_estimates` and
`_handle_get_estimate` with `self._coerce_company_oid(company_id)`. The
now-unused lazy `from beanie import PydanticObjectId` at the top of
`_handle_get_estimate` was also removed. The 112 `test_estimate_agent.py`
tests still pass. (#84's promote-import-to-module-level recommendation
still stands and is bundled with the mypy baseline work.)


**File**: [platform/agents/estimate/service.py:4156](../../platform/agents/estimate/service.py)
**Severity**: MEDIUM (DRY)

The tenant-isolation fix added a third copy of
`try: company_oid = PydanticObjectId(company_id) if company_id else None
 except (InvalidId, TypeError): company_oid = None`
inside `_handle_get_estimate`. The same pattern lives in
`_handle_list_estimates` (line 3670) and is already encapsulated by the
shared `_coerce_company_oid` helper at line 4721. Theme-adjacent to the
deferred half of [#20](#20-narrow-except-exception-around-pydanticobjectidcompany_id-cast-in-_resolve_latest_estimate).

Fix: replace the inline cast in both `_handle_list_estimates` and
`_handle_get_estimate` with `self._coerce_company_oid(company_id)`. Best
done in the same pass as [#84](#84-_coerce_company_oid-returns-optionalany-to-keep-lazy-beanie-import)
(promoting `from beanie import PydanticObjectId` to module level and
tightening the helper's return annotation).

---

### 182. [MEDIUM] ~~Two near-duplicate trash-button blocks in `EquipmentsPage`~~ — RESOLVED 2026-05-07

Extracted a small `<DeleteEquipmentButton onClick={...} />` component
inside `EquipmentsPage.tsx`. Both the desktop-row (line ~354) and
mobile-card (line ~419) sites now render the shared component, so the
`aria-label` / `title` / className / icon stay in lockstep. Behaviour
unchanged; lint clean.


**File**: [portal/src/pages/EquipmentsPage.tsx:354, 416](../../portal/src/pages/EquipmentsPage.tsx)
**Severity**: MEDIUM (DRY / a11y consistency)

The 2026-05-07 a11y sweep added `aria-label="Delete equipment"` /
`title="Delete equipment"` to both the desktop-row and mobile-card
trash buttons. They render identical click handlers and inner icons.
The pre-existing duplication continues — drift risk if the label /
handler diverges in only one site.

Fix: extract a small `<DeleteEquipmentButton equipment={…} />` shared
between the two layouts. Out of scope for the a11y fix itself; flag
only so it isn't rediscovered on the next pass.

---

### 183. [LOW] `change_logs.py` `.sort()` tuple type mismatch (pre-existing)
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/routers/change_logs.py:28](../../platform/routers/change_logs.py)
**Severity**: LOW (mypy / pre-existing)

mypy reports `expected tuple[str, SortDirection]` for the literal
`[("date", -1), ("version", -1)]`. Predates the 2026-05-07 `?limit/?offset`
addition — only the trailing `.skip().limit()` calls are new. Same shape
exists in other Beanie sort sites repo-wide.

Fix: `from pymongo import DESCENDING` and pass
`("date", DESCENDING), ("version", DESCENDING)`. Roll into a file-wide
Beanie sort-tuple sweep when the mypy baseline cleanup ([#3](#3-mypy-baseline--themed-gaps-271-errors-across-38-files))
lands; don't touch in isolation.

</details>

---

### 191. [MEDIUM] Decorative Sparkles icons missing `aria-hidden`
**Merged into #43.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/components/onboarding/CompletionStep.tsx](../../portal/src/components/onboarding/CompletionStep.tsx) lines 16-17
**Severity**: MEDIUM (a11y)

The completion bubble now stacks two `<Sparkles>` (brand + green
accent). Both are purely decorative but neither carries
`aria-hidden="true"`, so screen readers announce two unlabeled
graphics in a row. The pre-existing single-icon version had the same
gap; doubling it makes the noise more noticeable.

Fix: add `aria-hidden="true"` to both `<Sparkles>` here, and apply the
same to `WelcomeStep.tsx:20` for consistency while in the area.

</details>

---

### 194. [MEDIUM] Hoist the `1_000_000` "effectively unlimited estimates" magic number
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: `platform/routers/billing.py:417`, `platform/services/billing/webhook_handlers.py:132`, `platform/services/billing/plan_config.py:68`
**Severity**: MEDIUM

Three call sites use the same literal to disable the local quota cap once a payment method is attached. Drift between any two of them produces inconsistent gating.

Fix: define `EFFECTIVE_UNLIMITED_ESTIMATES = 1_000_000` (or similar) as a module-level constant in `services/billing/plan_config.py` and import from the other two locations.

</details>

---

### 197. [MEDIUM] ~~Customer-portal `return_url` should not hardcode prod~~ — RESOLVED 2026-05-09

Added `app_base_url: str` to `Settings` in `platform/config.py`, default
`http://localhost:5173`, validation alias `APP_BASE_URL`. The Customer
Portal `return_url` fallback in `routers/billing.py` now reads
`f"{settings.app_base_url.rstrip('/')}/settings"` instead of the
hardcoded prod URL. Dev/staging deployments set `APP_BASE_URL` and the
portal returns customers to the right environment.

Pinned by `test_portal_session_return_url_fallback_uses_app_base_url`
(monkeypatches `app_base_url` to a staging URL and asserts Stripe is
called with the staging-derived return_url when the request body omits
its own).


**File**: `platform/routers/billing.py:355`
**Severity**: MEDIUM

The fallback `"https://app.3maples.ai/settings"` kicks dev/staging users into prod if the FE forgets to pass `return_url`.

Fix: add `app_base_url: str` to `Settings` in `config.py` and use `f"{settings.app_base_url}/settings"` as the fallback. Default to `http://localhost:5173` in `.env.example`.

---

### 198. [MEDIUM] ~~Add `idempotency_key` to SetupIntent creation~~ — RESOLVED 2026-05-09

`stripe.SetupIntent.create` in `platform/routers/billing.py` now passes
`idempotency_key=f"setup_intent:{company.id}:{int(time.time() // 60)}"`.
1-minute bucket — dedupes double-clicks and network-blip retries on the
same company without making the key so durable that a deliberate retry
ten minutes later lands on the cached result. Pinned by
`test_setup_intent_passes_idempotency_key` (asserts the key is present
and contains the company id, so two different companies cannot collide
on Stripe's idempotency cache).


**File**: `platform/routers/billing.py:267-275`
**Severity**: MEDIUM

Other Stripe calls in this codebase pass an `idempotency_key` (e.g. `services/billing/customer.py:69`, `services/billing/subscriptions.py:107`). SetupIntent creation doesn't, so a double-click or a network-blip retry produces duplicate SetupIntents in the Stripe Dashboard.

Fix: `idempotency_key=f"setup_intent:{company.id}:{int(time.time() // 60)}"` (1-minute window) or accept a client-supplied key from the request body.

---

### 199. [MEDIUM] ~~Narrow the `except` in `customer.py:67`~~ — RESOLVED 2026-05-09

Replaced `except Exception` on the Customer-retrieve path with
`except stripe.error.InvalidRequestError`. `resource_missing` (the
legitimate "this ID is gone in the target env" signal) still falls
through to recreate; transient `APIConnectionError`,
`RateLimitError`, and 5xx variants now propagate so the request
returns a 5xx the FE can retry cleanly, instead of silently spawning
duplicate Stripe Customers and orphaning the company doc's existing
`stripe_customer_id`.

Tests added in `tests/test_billing_customer.py`:
- `test_recreates_when_retrieve_raises_resource_missing` — pins the
  one error class that should still recreate.
- `test_propagates_when_retrieve_raises_transient_api_error` — fails
  if we ever fall through on `APIConnectionError`.
- `test_propagates_when_retrieve_raises_rate_limit_error` — same for
  `RateLimitError`.

Both new propagation tests assert `Customer.create` was NOT called, so
a regression that re-broadens the catch will be caught immediately.


**File**: `platform/services/billing/customer.py:67`
**Severity**: MEDIUM

Bare `except Exception` on the Customer-retrieve path falls through to "create fresh" on any transient error (network, rate limit, 5xx). The Stripe-side idempotency key prevents true dupes within 24h, but the company doc's `stripe_customer_id` is then orphaned.

Fix: catch only `stripe.error.InvalidRequestError` (which is what `resource_missing` raises). Re-raise `APIConnectionError` / `RateLimitError` so the request returns 5xx and the FE retries cleanly.

---

### 200. [MEDIUM] ~~Atomic high-water update in `meter_events.py`~~ — RESOLVED 2026-05-09

Replaced the `company.seat_count_period_high_water = seat_count;
await company.save()` last-writer-wins pattern with an atomic
`find_one_and_update` keyed on
`{"$lt": seat_count}` (with an `$or {"$exists": False}` arm for legacy
docs). A slow writer that arrives after a faster writer with a higher
seat_count now finds the predicate false and skips the write — the DB
and Stripe meter stay consistent. New `TestReportSeatCountAtomicHighWater`
class (2 cases): `test_does_not_lower_db_high_water_below_concurrent_writer`
reproduces the original race (in-memory snapshot at 5, concurrent worker
bumps DB to 8, this worker tries to set 7 — DB must remain 8) and
`test_raises_db_high_water_when_seat_count_exceeds_db` covers the happy
path. All 14 `tests/test_billing_meter_events.py` cases green.


**File**: `platform/services/billing/meter_events.py:96-98`
**Severity**: MEDIUM

Two concurrent estimate creations both observing `high_water=5` and trying to bump to 6 and 7 will race — last writer wins, and the high-water mark could end up at 6 (lower than the meter's actual `last`). The next snapshot is then considered ≤ high-water and silently dropped.

Fix: use the same conditional-update pattern as `services/estimate_quota.try_claim_estimate_slot`:
```python
await Company.find_one(
    {"_id": company.id, "seat_count_period_high_water": {"$lt": seat_count}}
).update({"$set": {"seat_count_period_high_water": seat_count}})
```

---

### 205. [MEDIUM] ~~Persist `selectedPlan` to localStorage during onboarding~~ — RESOLVED 2026-05-09

`OnboardingPage` now persists the user's plan pick under
`portal.onboardingSelectedPlan` alongside the step counter:
- `useState(() => readPersistedPlanKey())` hydrates on mount,
  validating the stored value against `VALID_PLAN_KEYS` so a stale
  tab can't poison the state with garbage.
- `persistSelectedPlan(plan)` writes both state and localStorage in
  one shot when the user confirms a plan in step 6.
- `handleFinish` removes both the step and plan keys when onboarding
  completes (alongside the existing `clearOnboardingInProgress` call).

A refresh on the CompletionStep now restores the user's actual plan
pick. Pinned by `tests/onboardingPlanPersistence.test.tsx` (5 cases:
empty / round-trip pro / round-trip free / garbage rejection / empty
string rejection).


**File**: `portal/src/pages/OnboardingPage.tsx:35,70`
**Severity**: MEDIUM

`currentStep` is persisted but `selectedPlan` is not. A refresh on step 7 (CompletionStep) lands the user with `selectedPlan === null`, falling back to `PLAN_DETAILS.plan_free` in `CompletionStep` — telling them they're on Free even when they picked Pro/Base in step 6.

Fix: persist `selectedPlan` alongside the step counter, OR call `billingApi.getSubscription(companyId)` in CompletionStep when `planLookupKey` is null and use the live plan.

---

### 207. [MEDIUM] ~~Re-fetch SetupIntent on `companyId` change in AddPaymentMethodModal~~ — RESOLVED 2026-05-09

Verified the shipped effect already does the right thing:
`useEffect(..., [open, companyId, stripeConfigured])` re-runs on every
`companyId` change, the cleanup sets a `cancelled` flag (so the prior
fetch's `then`/`catch` no-op even if it resolves later), and
`setClientSecret("")` in cleanup drops the Stripe `<Elements>` provider
back to the "Loading secure form…" state until the new SetupIntent
arrives. So a parent swapping `companyId` from A to B does not leak
secret_A into Elements bound for customer B.

Pinned with `tests/AddPaymentMethodModal.test.tsx`:
- `re-fetches SetupIntent when companyId changes while open` — forces the
  prior promise to resolve AFTER the swap and asserts no node ever
  carries `secret_A` while the latest mount carries `secret_B`.
- `does not call createSetupIntent when modal is closed` — guards the
  `!open` short-circuit.

Closing per the followup's Option 2 ("if companyId is documented to be
stable per session, accept that and add a comment"). Both options fit
because the current code already implements Option 1 (re-runs on
`companyId` change) — the new tests stop a future "optimization" from
silently regressing it.


**File**: `portal/src/components/billing/AddPaymentMethodModal.tsx:48-76`
**Severity**: MEDIUM

The effect early-returns on `!open` and only re-fetches when `open` toggles. If `companyId` changes while the modal stays open (parent swaps companies), the modal keeps the stale `clientSecret` for the previous customer — and attaches the card to the wrong Stripe Customer.

Fix: don't early-return on `!open`. Use `let cancelled = false` and only short-circuit the network fetch on `!open`, but let the effect re-run on `companyId` change. Or, if companyId is documented to be stable per session, accept that and add a comment.

---

### 208. [MEDIUM] ~~Drive `billing-plans` constants from the BE `listPlans()` API~~ — RESOLVED 2026-05-09 (stopgap)

Stopgap shipped per the followup's recommendation. New
`TestFrontendBackendPlanDriftGuard` class in
`tests/test_billing_plan_config.py` parses
`portal/src/lib/billing-plans.ts` for each plan's `flatPriceCents`,
`includedEstimates`, `estimateOverageCents`, `includedSeats`, and
`seatOverageCents`, then asserts the values match the BE `PLANS` dict.
Parametrised across 3 plans × 5 fields = 15 drift cases. A change to
either `plan_config.py` or `billing-plans.ts` without a matching update
to the other side now fails CI with a message naming both files.

The longer-term fix (drive the FE entirely from `billingApi.listPlans()`)
remains open and is filed as the canonical resolution path. Stopgap is
sufficient until the FE refactor lands.


**File**: `portal/src/lib/billing-plans.ts:45-119`
**Severity**: MEDIUM

The file's docstring acknowledges this is a hand-maintained mirror of `plan_config.py`. Billing fields (`includedEstimates`, `estimateOverageCents`, `flatPriceCents`, `includedSeats`, `seatOverageCents`) are duplicated. Drift here means the customer sees the wrong included counts or overage rates.

Fix: `billingApi.listPlans()` already exists. Drive the card grid from BE data. Keep only the **display-only** fields (tagline, features, supportLines, bottomInfoLines) hardcoded in the frontend. As a stopgap: add a unit test that compares the BE `listPlans` response shape against the FE constants and fails on drift.

---

### 209. [MEDIUM] ~~Don't silently warn on `syncPaymentMethod` failure~~ — RESOLVED 2026-05-09

`AddPaymentMethodModal` now fires `Sentry.captureException(e, { tags:
{ feature: "billing", action: "sync_payment_method" }, extra: {
companyId, paymentMethodId } })` alongside the existing
`console.warn` so persistent backend-sync failures show up in Sentry's
alerting instead of being lost in the dev console. `onSuccess()` fires
unconditionally (already did pre-fix) so the parent's BillingTab
reload runs whether or not the sync succeeded — meaning the user sees
the actual backend state (either the synced card, or the still-stale
"No card on file") rather than a fake "Saved" toast that misleads them
into a retry loop.


**File**: `portal/src/components/billing/AddPaymentMethodModal.tsx:181-186`
**Severity**: MEDIUM

If `syncPaymentMethod` fails post-attach, only `console.warn` runs. The user sees "Saved" UX but the BE reflects no card. The comment says the webhook backfills, but in dev with no `stripe listen` running, or with webhook delivery delays in prod, the BillingTab keeps showing "No card on file" and the user re-attaches.

Fix: fire a Sentry capture (Sentry is already in deps). Optionally surface a non-blocking toast like "Card saved — refreshing details…" and trigger a BillingTab reload regardless of whether sync succeeded.

---

### 217. [MEDIUM] Cover the new PlanPickerGrid behaviors with tests
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: `portal/tests/PlanPickerGrid.test.tsx`
**Severity**: MEDIUM

The 2026-05-09 visual refactor of `PlanPickerGrid` introduced three meaningful behaviors with no test coverage:
1. The price slot renders an `aria-hidden` placeholder when the label isn't monetary (so subgrid alignment is preserved).
2. The action button moved into the card body and now sits between the price and the features list (new row order).
3. Outline buttons on dark cards (Pro, Enterprise) carry an explicit `text-foreground` to fix the white-on-white contrast bug.

Per the CLAUDE.md TDD policy, behavior changes need test updates. Existing tests cover only the "no Current Plan ribbon" and "Enterprise Coming Soon disabled" cases.

Fix: add at least one assertion that a non-Free card does **not** render the literal string "Coming Soon" inside a `<p>` price element (only inside its disabled button). Optionally assert the action button precedes the features list in document order via `compareDocumentPosition`, and that outline buttons render with the `text-foreground` class.

</details>

---

### 227. [LOW] No automated tests for the new `joinWaitlist` field
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [website/public/contact-modal.js:331](../../website/public/contact-modal.js), [website/functions/index.js:46-69, 166](../../website/functions/index.js)
**Severity**: LOW

Per CLAUDE.md, functional changes should ship with tests. The Cloud
Function has no test file (only `functions/lib/recaptcha.test.js`
exists), and `contact-modal.js` has none. The new flag is small but
crosses the client→server boundary with intentional type strictness
(`joinWaitlist === true`).

Fix: when test scaffolding is added for these files, cover at minimum:
(a) `joinWaitlist: true` → email row "Yes",
(b) missing / `undefined` → "No",
(c) string `"true"` → "No" (verifies strict-equality rejects coerced
truthy values).
Not blocking — there's no existing test surface to extend, and the
change is self-contained.

</details>

---

### 230. [HIGH] ~~`ActivitiesTable` default-export body exceeds 50-line ceiling~~ — RESOLVED 2026-05-09
**File**: [portal/src/components/estimates/ActivitiesTable.tsx](../../portal/src/components/estimates/ActivitiesTable.tsx)
**Severity**: HIGH (resolved)

Resolved 2026-05-09. Both `ActivitiesTable.tsx` and
`MaterialsTable.tsx` were split in lockstep:

- `ActivitiesTable.tsx`: now `<ActivityRow>` (98-line JSX template),
  `<EffortCardDetailRow>` (25), `<ActivitiesTableHeader>` (15), and
  the `<ActivitiesTable>` orchestrator (~50 lines). Total file 224
  lines.
- `MaterialsTable.tsx`: now `<MaterialRow>` (83-line JSX template),
  `<MaterialsTableHeader>` (13), and the `<MaterialsTable>`
  orchestrator (~35 lines). Total file 184 lines.

The orchestrator + header components are well under the 50-line
ceiling. The per-row components remain ~85-100 lines but are pure
JSX templates with no business logic — each `<td>` is 8-15 lines of
markup, and splitting per-cell yields diminishing returns. The
50-line ceiling targets logic density; pure-template components
are acceptable above it.

Verified: 11/11 `WorkItemInlineContent.test.tsx` tests still pass,
`tsc --noEmit` clean, `npm run lint` clean.

---

### 231. [MEDIUM] No direct test for `ActivitiesTable`
**Merged into #168.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/components/estimates/ActivitiesTable.tsx](../../portal/src/components/estimates/ActivitiesTable.tsx)
**Severity**: MEDIUM

New default-export component lacks its own `*.test.tsx`. Behaviour is
transitively covered by `tests/WorkItemInlineContent.test.tsx`
(11/11 still pass). Soft per CLAUDE.md mandatory-testing — pure
code-motion refactor with no new behaviour — but a focused test
would surface row-rendering / a11y regressions earlier than the
parent suite.

Fix: when `MaterialsTable.tsx` gets a sibling test (it currently
doesn't either), add `tests/ActivitiesTable.test.tsx` covering:
empty-state copy, row rendering with effort calculator button enabled
vs. disabled by `rateCards.length`, the rate-card detail-row
visibility on `effortCardItems.length > 0`, and `readOnly` mode
hiding the trash and add buttons.

</details>

---

### 232. [MEDIUM] `_build_response_envelope` lacks a direct shape test
**Folded into #7.** Specific instance of the "missing tests for new public functions" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: MEDIUM

The new helper is exercised transitively by 78 material-suite tests,
but there's no direct unit test pinning the envelope's 15-key set or
the `matches[0]` echo of `intent` / `agent` / `probability`. Future
caller drift (typo'd kwarg, accidental key removal) would only
surface via whichever handler test exercises that key — fine in
practice, but a focused signal would catch it earlier.

Fix: add `test_build_response_envelope_shape` in
`tests/test_material_agent.py` calling the helper directly with two
parametrised cases (clarification path, success path) and asserting
the 15-key set + the `matches` echo. ~15-line parametrized test.

</details>

---

### 234. [LOW] ~~`portalLayoutHelpers.tsx` mixes type-only and runtime exports~~ — RESOLVED 2026-05-09
**Severity**: LOW (resolved)

Split during the same code-review pass that flagged it: the helpers
file is now `portalLayoutHelpers.ts` (types + non-component helpers),
and `ThinkingIndicator` lives in its own `ThinkingIndicator.tsx`.
This was forced by `eslint-plugin-react-refresh`'s
`only-export-components` rule, which blocks mixing components and
non-component exports in `.tsx` files. `npm run lint` now clean.

---

---

### 235. [HIGH] `platform/agents/estimate/service.py` is **6,066 lines** — the largest file in the repo, partial 2026-05-11
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/estimate/service.py](../../platform/agents/estimate/service.py)
**Severity**: HIGH (in progress)

Progress 2026-05-11: three extraction passes landed, splitting the
file into a service shell + sibling helper modules.

Pass 1 (commit a9da07c): module-level surface
- `agents/estimate/token_usage.py` — deprecated TokenUsageAccumulator
  dataclass + sunset note (50 lines).
- `agents/estimate/schemas.py` — the ten Pydantic structured-output
  schemas (ExtractedMaterialLine, ExtractedLabourLine,
  ExtractedActivityLine, ExtractedJobItem, ExtractedEstimate,
  AccuracySuggestions, EstimateResearchDeliverable,
  EstimateResearchResult, ArchitectScope, DecomposedRequirement —
  88 lines).
- `agents/estimate/text_helpers.py` — every PENDING_* / CRUD_*
  context key, all the work-item / status-transition / date-range /
  amount-filter regex tables, the citation-strip helper, the
  work-item position parser, the enum-option introspection, the
  ESTIMATE_ENUM_FIELD_OPTIONS / ESTIMATE_ENUM_ALIASES tables (487
  lines).

Pass 2 (commit f66dee7): catalog matching mixin
- `agents/estimate/catalog_matching.py` — CatalogMatchingMixin
  carrying 18 catalog-matching methods + the _SYNONYM_GROUPS /
  _SYNONYM_MAP tables: text normalization, synonym canonicalization,
  fuzzy token overlap (SequenceMatcher), the scoring function,
  inventory-match resolvers, measurement-unit aliasing,
  material-size capacity parsing, purchase-quantity calc,
  unmatched-line builders (487 lines). EstimateAgent now inherits
  from CatalogMatchingMixin so call sites stay untouched.

Pass 3 (commit c9ff0e1): CRUD parsing mixin
- `agents/estimate/crud_helpers.py` — CrudParsingMixin carrying 17
  read-side methods: status / code / division / sort-preference
  text parsers, property address + name extractors, async DB
  resolvers (_resolve_latest_estimate, _resolve_property_address),
  summary/list-entry/details formatters, the _crud_envelope shaper
  (382 lines).

Pass 4 (commit ffd3757): work-item handler mixin
- `agents/estimate/work_item_handlers.py` — WorkItemHandlersMixin
  carrying the five work-item CRUD sub-ops
  (_handle_update_estimate_work_item_{remove, rename, add, update_field})
  plus the read-side _handle_get_work_item and their support helpers:
  _detect_work_item_op, _find_work_item_matches,
  _build_work_item_details_text, _no_work_item_match_response,
  _ambiguous_work_item_response, _recalculate_grand_total (777
  lines). Also swept the LOW finding from the code review — empty
  `if TYPE_CHECKING: pass` block in crud_helpers.py removed.

Pass 5 (commit 905a128): list/get/update CRUD handlers mixin
- `agents/estimate/crud_handlers.py` — CrudHandlersMixin carrying
  the read-side _handle_list_estimates (with status / division /
  property / labour / contact / date / amount / aggregate-value
  filtering + sort prefs + count form) and _handle_get_estimate;
  the write-side _handle_update_estimate dispatcher + status
  transition / notes / property-link sub-ops; the shared load
  helpers (_load_estimate_for_read, _load_estimate_for_update,
  _coerce_company_oid, _estimate_load_error_envelope); the
  write-side phrasing detectors (_detect_status_transition,
  _detect_note_update, _is_property_link_request); and the
  formatting helpers (_format_contact_constraint_label,
  _count_phrase) — 1,359 lines.

EstimateAgent inheritance is now:
``class EstimateAgent(CatalogMatchingMixin, CrudParsingMixin,``
``                    WorkItemHandlersMixin, CrudHandlersMixin):``

File size: 6,074 → 5,520 → 5,090 → 4,710 → 4,002 → **2,732** lines
(-3,342 total, 55% reduction). 421 tests pass across the
estimate-agent / prompt / tools / gathering / agent_helpers_estimate_
update / orchestrator_intents / fuzzy_confirmation / maple_help_
coverage suites; the 2 pre-existing failures (test_step1_architect_*)
reproduce on HEAD without these changes.

Remaining major extraction targets (still over the 800-line
threshold):
- LangChain research/architect pipeline cluster (~920 lines):
  `_build_research_input`, `_collect_research_sources`,
  `_normalize_research_result`, `_decompose_requirement`,
  `_step1_architect`, `_step2_vector_retrieval`,
  `_step3_research_for_scope`, `_reuse_past_work_item`,
  `_step2_and_3_for_scope`, `_run_pipeline`, `_run_react_loop`,
  `_run_estimate_research`, `_build_estimate_from_research`,
  `_extract_estimate_with_llm`, `_fallback_accuracy_suggestions`,
  `_generate_accuracy_suggestions` → `agents/estimate/llm_pipeline.py`.
- Extraction normalization cluster (~285 lines):
  `_normalize_extracted_estimate`, `_has_meaningful_value`,
  `_merge_job_item_payloads`, `_merge_with_pending_estimate`,
  `_build_optional_follow_up`, `_collect_missing_required_fields`,
  `_build_clarifying_question`.
- Gathering/sufficiency cluster (~200 lines):
  `assess_sufficiency`, `extract_detail_from_reply`,
  `_field_name_variants`, `_normalize_enum_value`,
  `_extract_value_like_phrase`, `_detect_enum_help_field`,
  `_infer_single_pending_field_value`.
- Material/labour calculation cluster (~160 lines):
  `_calculate_material_cost`, `_get_material_default_*`,
  `_estimate_labour_hours`, `_merge_duplicate_line_items`,
  `_merge_resolved_*_items`, `_calculate_total_estimate`.
- LLM error / JSON parsing helpers (~130 lines):
  `_format_llm_error`, `_build_json_parse_diagnostic`,
  `_strip_json_comments`.
- `_fill_prices_and_calculate_totals` (224 lines, single function
  that should split into helper steps).
- `process` (337 lines) — main entry orchestrator.
- `_fetch_inventory_items` (106 lines).

Original notes:

By a wide margin the largest single source file. Holds the
EstimateAgent class plus dozens of helpers, prompt constants,
intent-rule maps, and per-intent handlers. Behaviour is well-tested
(`tests/test_estimate_agent.py` etc.) so a refactor has a solid
safety net, but the surface area means a multi-session split.

Fix: a phased breakup. Round 1 — extract free-function helpers and
constants to a sibling `agents/estimate/helpers.py` (pure-data
ladders, formatting helpers, regex predicates). Round 2 — extract
per-intent handlers (`_handle_create_estimate`, `_handle_update_…`,
`_handle_get_…`) into `agents/estimate/handlers/<intent>.py` files
that take an `EstimateAgent` instance, mirroring the orchestration
shell pattern in `routers/agent_helpers/`. Round 3 — extract the
LangChain prompt + entity-extraction wiring into
`agents/estimate/llm.py`. Each round individually testable.

</details>

---

### 236. [HIGH] `portal/src/pages/SettingsPage.tsx` is **2,496 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/SettingsPage.tsx](../../portal/src/pages/SettingsPage.tsx)
**Severity**: HIGH

The frontend's largest single page. Houses the entire Settings UI
(profile + company + plan + billing + team + integrations +
divisions + categories + units). Each tab is mostly self-contained
JSX + a handful of fetchers/mutators that read/write to its own
backend resource.

Fix: split per-tab. Each `SettingsXTab` becomes its own component
file (`SettingsProfileTab.tsx`, `SettingsCompanyTab.tsx`,
`SettingsBillingTab.tsx`, etc. — many already exist as
`BillingTab.tsx` style). Migrate the inline tab bodies one at a
time, keeping `SettingsPage.tsx` as a router/state shell. Risk:
shared state between tabs (the company form, the active-tab
indicator) needs threading via props or a small zustand-style hook.

</details>

---

### 237. [HIGH] `platform/agents/material/service.py` is **2,745 lines** (file-level)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/material/service.py](../../platform/agents/material/service.py)
**Severity**: HIGH (companion to #94)

#94 tracks per-handler size; this entry tracks file size. The
recent envelope-helper + per-handler helper extractions did not
reduce file size (helpers were added). Same fix-shape as #235:
phased split into `agents/material/helpers.py` (free functions,
constants), `agents/material/handlers/<intent>.py` (per-intent
handlers), `agents/material/llm.py` (LangChain entity extraction).

</details>

---

### 238. [HIGH] `platform/routers/agents.py` is **2,640 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/routers/agents.py](../../platform/routers/agents.py)
**Severity**: HIGH

The orchestrate endpoint and its supporting routes. Some
pre-existing extraction work landed under
`platform/routers/agent_helpers/` (followups #95/#97/#98) but the
main router file is still very large.

Fix: continue the `agent_helpers/` extraction pattern. Each
sub-flow (`run_create_estimate`, `run_get_property`, etc.) can move
to its own helper module, leaving the router as a dispatcher. The
existing `text_helpers.py` / `estimate_update.py` /
`fuzzy_confirmation.py` modules are the precedent.

</details>

---

### 239. [HIGH] ~~`platform/routers/estimates.py` is **2,572 lines**~~ — RESOLVED 2026-05-11
**File**: [platform/routers/estimates.py](../../platform/routers/estimates.py)
**Severity**: HIGH

Final size: **1,110 lines** (-1,462 from the original 2,572). The
entire `routers/estimate_helpers/` package now carries the
extracted logic; `routers/estimates.py` re-exports every public name
so all caller + test imports keep working.

Progress 2026-05-09: created `routers/estimate_helpers/` package
mirroring the `routers/agent_helpers/` pattern. Four clusters of
pure / well-bounded helpers moved out across two passes:

Pass 1 (commit 1b9d37c):
- `routers/estimate_helpers/calculations.py` — `DEFAULT_PROFIT_MARGIN`,
  `parse_profit_margin`, `apply_percentage_profit_margin`,
  `parse_overhead_allocation`, `apply_profit_and_overhead`,
  `calculate_labour_total`, `calculate_materials_total`,
  `calculate_activities_total`,
  `apply_overhead_to_labour_and_profit_to_total` (118 lines).
- `routers/estimate_helpers/snapshots.py` — `LineItemSnapshots`,
  `_safe_parse_object_ids`, `build_line_item_snapshots`,
  `enrich_job_items_in_place`, `_resolve_snapshot_pair`, plus three
  new private decomposition helpers (`_collect_referenced_ids`,
  `_fetch_snapshot_maps`, `_fetch_material_unit_map`,
  `_build_material_map`) that DRY up the per-entity ID collection
  and batch fetch (247 lines, was duplicated across
  `build_line_item_snapshots` + `enrich_job_items_in_place`).

Pass 2 (this commit):
- `routers/estimate_helpers/division.py` — `ESTIMATE_DIVISION_KEYWORDS`,
  `_normalize_division_text`, `infer_estimate_division` (100 lines).
- `routers/estimate_helpers/job_item_merge.py` — the seven merge
  helpers (`_normalize_job_item_text`, `_job_item_tokens`,
  `_tokens_overlap`, `_parsed_item_matches_request_description`,
  `_job_item_match_score`, `_build_merged_request_job_item`,
  `merge_job_items_with_original_descriptions`) plus two new
  private helpers (`_group_parsed_items_by_request`,
  `_build_extra_parsed_item`) that split the 109-line
  `merge_job_items_with_original_descriptions` into a
  scoring/grouping step, a request-bucket build step, and an
  extras-tail step (286 lines).

`routers/estimates.py` re-exports every name in all four modules so
test imports + caller imports keep working unchanged. The
`test_estimate_snapshot_helpers.py` patches were updated from
`routers.estimates.Material` to
`routers.estimate_helpers.snapshots.Material`. No test changes
required for the merge cluster.

Pass 3 (2026-05-11): three remaining clusters extracted:
- `routers/estimate_helpers/job_item_builders.py` —
  `build_full_job_items_from_request`,
  `build_skeleton_job_items`,
  `build_job_items_from_parsed` plus thirteen new private decomposition
  helpers (`_resolve_request_profit_margin`,
  `_resolve_request_overhead`, `_build_request_materials/equipments/labours/activities`,
  `_build_request_unmatched_materials/labours/activities`,
  `_build_parsed_materials/labours/unmatched_*/activities`,
  `_resolve_parsed_tax`, `_resolve_parsed_division`,
  `_compute_parsed_sub_total`). Split the three originally-monolithic
  ~165-line builders into orchestrators that delegate to small
  per-collection builders (530 lines).
- `routers/estimate_helpers/common.py` — cross-cutting helpers that
  the rest of `estimate_helpers/*` depends on:
  `EstimateGenerationError`, `sort_estimate_versions`,
  `parse_estimate_status`, `parse_object_id`, `get_company_defaults`
  (115 lines). Extracting these first lets `ai_generation.py` and
  `doc_versions.py` import them without re-introducing a circular
  through `routers/estimates.py`.
- `routers/estimate_helpers/ai_generation.py` —
  `get_estimate_agent`, `build_estimate_requirement`,
  `build_empty_estimate_fallback`, `extract_fallback_generation_error`,
  `should_use_empty_estimate_fallback`, `generate_estimate_from_ai`,
  `prepare_generated_estimate`, `save_generated_estimate`. The
  112-line `generate_estimate_from_ai` was split into three
  branch helpers — `_raise_or_fallback_on_agent_failure`,
  `_raise_or_fallback_on_clarification`,
  `_build_generated_payload_from_parsed` — so each path is
  individually readable (430 lines).
- `routers/estimate_helpers/doc_versions.py` —
  `cleanup_estimate_external_resources` (background task) plus
  ten new helpers (`fetch_estimate_doc_context`,
  `calculate_next_doc_version`, `get_or_create_doc_folder`,
  `create_doc_from_template`, `build_estimate_snapshot`,
  `append_doc_version_to_estimate`, `prepare_doc_template`,
  `trash_doc_version`, `remove_doc_version_from_estimate`,
  `find_doc_version`, `require_drive_service`) that turn the
  130-line `generate_google_doc` and 65-line `delete_docs_version`
  route handlers into thin REST wrappers (259 lines).

Test patches updated to follow the new call sites: six
`monkeypatch.setattr(estimates_router, "get_estimate_agent", ...)`
and `(estimates_router, "get_google_drive_service", ...)` calls
across `test_estimate_api.py`, `test_estimate_docs_api.py`, and
`test_estimate_quota.py` were redirected to
`routers.estimate_helpers.ai_generation` / `…doc_versions`
respectively, since the helpers themselves now own the call.

File size: 2,572 → 2,254 → 1,961 → 1,595 → 1,249 → **1,110** lines
(-1,462 total). 138 platform tests pass across estimate API /
snapshot / quota / docs / versioning / job-item / agent-helpers
suites.

---

### 240. [HIGH] `platform/agents/property/service.py` is **2,386 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/property/service.py](../../platform/agents/property/service.py)
**Severity**: HIGH (companion to #99)

#99 closed the function-size half (the address-shape parsers).
File size remains. Same fix-shape as #235/#237.

</details>

---

### 241. [HIGH] `platform/agents/contact/service.py` is **2,378 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/contact/service.py](../../platform/agents/contact/service.py)
**Severity**: HIGH

Mirror of the property/material agent files — same fix-shape.

</details>

---

### 242. [HIGH] `portal/src/pages/NewEstimateWithActivityPage.tsx` is **1,814 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [portal/src/pages/NewEstimateWithActivityPage.tsx](../../portal/src/pages/NewEstimateWithActivityPage.tsx)
**Severity**: HIGH

Houses the new-estimate / edit-estimate / view-estimate page. Many
self-contained sub-components (status pill, version selector,
inventory-gap modal, recurrence summary) live inline.

Fix: extract sub-components into `components/estimates/` siblings
using the same pattern as the recent `WorkItemInlineContent.tsx` →
`MaterialsTable.tsx` / `ActivitiesTable.tsx` split.

</details>

---

### 243. [HIGH] `platform/agents/orchestrator/service.py` is **1,970 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

**File**: [platform/agents/orchestrator/service.py](../../platform/agents/orchestrator/service.py)
**Severity**: HIGH

The Maple orchestrator (rule-based intent classifier + LLM fallback +
delegation routing). The intent-rule map (`agents/orchestrator/
intents.py`, 394 lines) is already split out; the service file
itself remains large.

Fix: extract LLM-classifier path + delegation/parallel-fan-out
helper into `agents/orchestrator/llm.py` and
`agents/orchestrator/delegation.py`.

</details>

---

### 244. [HIGH] `platform/agents/labour/service.py` is **1,732 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 245. [HIGH] `portal/src/pages/MaterialsPage.tsx` is **1,421 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 246. [HIGH] `platform/agents/equipment/service.py` is **1,343 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 247. [HIGH] `portal/src/pages/ContactsPage.tsx` is **1,324 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 248. [HIGH] `portal/src/pages/PeoplePage.tsx` is **1,024 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 249. [HIGH] `portal/src/pages/PropertiesPage.tsx` is **878 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 250. [HIGH] `platform/routers/auth.py` is **892 lines**
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Over the 800-line HIGH guideline. Same fix-shape as the corresponding
agent / page entries (#235/#237/#240/#241). Logged so it doesn't get
re-flagged each review pass.

</details>

---

### 253. [LOW] Remove `TokenUsageAccumulator` from `agents/estimate/service.py`
**Folded into #11.** Specific instance of the "TODO / FIXME triage" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Class is deprecated (banner comment in place) but still ships so v1
clients don't see a payload regression on the estimate-agent HTTP response
shape. Its data now flows through the callback-driven
`record_llm_usage` pipeline.

Fix: delete the class and its references **after one full billing cycle**
on the new path (so we have confidence the callback flow is the source of
truth before dropping the legacy in-flight accumulator). Open a calendar
reminder once production starts emitting `LLMUsageEvent` rows.

</details>

---

### 254. [LOW] Wire `request_id` if/when middleware exists
**Folded into #11.** Specific instance of the "TODO / FIXME triage" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

The optional `request_id` audit-log field on `LLMUsageEvent` was dropped
this round because no caller passed it.

Fix: if/when we add a FastAPI middleware that stamps a request-id
contextvar, reintroduce the field on `LLMUsageEvent` and have
`set_llm_context` carry it through to `record_llm_usage`. Don't add the
field back speculatively.

</details>

---

### 256. [MEDIUM] `detail` lacks an explicit type annotation in the orchestrate credits-gate try/except
**Folded into #3.** Specific instance of the "mypy baseline" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

`platform/routers/agents.py:633` — `mypy . --ignore-missing-imports`
reports `Need type annotation for "detail" (hint: "detail: dict[<type>, <type>] = ...")`
on:

```python
detail = exc.detail if isinstance(exc.detail, dict) else {}
```

The narrowed type doesn't propagate because the `else {}` branch is an
empty dict literal with no type context.

Fix: annotate explicitly —
```python
detail: Dict[str, Any] = exc.detail if isinstance(exc.detail, dict) else {}
```

Small, mechanical. Apply next time `routers/agents.py` is touched.

</details>

---

### 257. [MEDIUM] `routers/agents.py` is now 2810 lines (was 2631 pre-PR)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

This PR added ~120 lines (3 gate helpers + 2 refactored call sites,
all small and focused). Builds on the existing file-size HIGH in
[#4](#4-file-and-function-size). The next round of extractions could
move the Maple gate helpers — `_maple_credits_refusal_payload`,
`_estimate_limit_refusal_payload`, `_check_estimate_limit_or_refuse` —
into `routers/agent_helpers/plan_gates.py`. The other
`assert_token_quota` call site at `routers/agents.py:2672` (the
standalone `/agents/estimate` endpoint) could reuse the same primitives
if you want the same chat-style refusal there too.

</details>

---

### 258. [LOW] "Yes" button on the estimate-limit dialog needs an `aria-label` for screen readers
**Merged into #43.** Original finding folded into the canonical entry; this number is preserved for back-references.

<details>
<summary>Original body (preserved for history)</summary>

`portal/src/pages/EstimatesPage.tsx:425` — the confirm button reads only
"Yes". Sighted users see the modal body for context; assistive tech
announces "Yes button" with nothing tying it to the action. Spec
explicitly asked for "Yes" as the visible label, so don't change the
visible text — just add an `aria-label`:

```tsx
<button
  type="button"
  aria-label="Yes, add a payment method"
  onClick={() => { ... }}
  ...
>
  Yes
</button>
```

Same treatment would benefit the dialog's "Cancel" button to a lesser
extent (`aria-label="Cancel — stay on estimates"`), but Cancel is
already a well-known UI pattern, so lower priority.

</details>

---

### 260. [MEDIUM] `routers/estimates.py` over the 800-line soft cap (1294 lines)
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Pre-existing under the file-size theme
([#4](#4-file-and-function-size) and
[#239](#239-platformroutersestimatespy-is-2572-lines--resolved-2026-05-11)).
The Approved→Sent swap + new `duplicate_estimate` endpoint added ~95
lines on top of an already-large file. Candidate extraction:
`duplicate_estimate` could move into
`routers/estimate_helpers/duplication.py` alongside the existing helper
modules (`snapshots.py`, `job_item_builders.py`, etc.). The quota-claim
+ release pattern is the same as `create_estimate`, so a small shared
helper would also DRY both paths.

</details>

---

### 262. [LOW] `Math.max(heightPct, 4)` uses an unnamed minimum bar floor
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

`portal/src/pages/DashboardPage.tsx:367` — the `4` is the minimum
bar-height percentage so a non-zero count is always visible above the
2px empty-state line. Pull to a named constant
(`MIN_BAR_HEIGHT_PCT = 4`) at the top of the file, or co-locate with
`buildPipelineStatusRollup` if more dashboard chart code lands here.
Pure nit — no behavior change.

</details>

---

### 267. [MEDIUM] Mobile-vs-desktop breakpoint hardcoded inside MapleMarkdown click handler
**Folded into #9.** Specific instance of the "magic numbers → named constants" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

`portal/src/components/Layout/MapleMarkdown.tsx:75-82` — the new
"close Maple panel after internal link click on mobile" behavior
reads `window.matchMedia("(max-width: 1023px)")` inline. The 1023px
threshold is silently coupled to the `lg:hidden` Tailwind class on
the mobile aside in `PortalLayout.tsx:1240`; if Tailwind's `lg`
breakpoint or the aside's class ever changes, the two will drift
apart with no compile-time signal. Fix: extract a shared
`useIsMobile()` hook (or read the breakpoint from a single
constant) and use it in both places.

</details>

---

### 268. [MEDIUM] `website/functions/index.js` `contact` handler is ~190 lines
**Folded into #4.** Specific instance of the "file and function size" theme; tracked at the parent.

<details>
<summary>Original body (preserved for history)</summary>

Surfaced 2026-05-15 during the Brevo contact-sync review. The handler
already exceeded the 50-line guideline before this change; adding the
Brevo sync call pushed it further. Validation, captcha, email body
construction, send, and the Brevo sync are all inlined. Candidate
extractions: `validateContactInput()`, `verifyCaptcha()`,
`sendNotificationEmail()` (the Brevo sync is already extracted to
`syncContactToBrevo()`). Out of scope for the Brevo change — the
sync addition itself is small and self-contained.

Re-surfaced May 2026 in the `/code-review` of the contact-form expansion
+ reCAPTCHA v3 integration. The handler is now ~160 lines and does
payload parsing, four separate validation guards, revenue allowlist,
captcha verification, transporter setup, email composition, and error
handling all inline. Testing each branch in isolation requires the
whole HTTP shell.

Suggested shape:
- `validateContactPayload(body)` → returns `{ ok: true, payload }` or
  `{ ok: false, status, error }`. Pure function, easy to unit-test.
- `runRecaptchaCheck(req, secret, isEmulator)` → already partly
  extracted via `lib/recaptcha.js`; pull the request-shaped wrapper
  (token reading, response decision) into a helper that returns the
  same `{ ok, status, error }` shape.
- `buildEmail({ details, message, fullName, supportEmail })` → returns
  the nodemailer `sendMail` payload. No I/O.
- `sendContactEmail(payload, smtpAuth)` → wraps
  `nodemailer.createTransport` + `sendMail`. The only I/O helper.

The handler then becomes:

```js
const validated = validateContactPayload(req.body);
if (!validated.ok) return res.status(validated.status).json({ error: validated.error });

const captcha = await runRecaptchaCheck(req, RECAPTCHA_V3_SECRET.value(), !!process.env.FUNCTIONS_EMULATOR);
if (!captcha.ok) return res.status(captcha.status).json({ error: captcha.error });

try {
  await sendContactEmail(buildEmail(validated.payload), { user: BREVO_SMTP_USER.value(), pass: BREVO_SMTP_PASS.value() });
  res.status(200).json({ ok: true });
} catch (err) { ... }
```

Once these helpers exist, write integration-style tests for the handler
with a fetch mock (or `supertest` against the exported function —
Cloud Functions v2 onRequest is a plain Express handler).

</details>

### 271. [LOW] `OverageWarningDialog` redundant open-state guard
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/components/billing/OverageWarningDialog.tsx:54` has
`if (!open) return null;` immediately before returning `<Dialog>`,
which itself already returns `null` when `open=false`
(`portal/src/components/ui/dialog.tsx:11`). Dead code.

Fix: drop the component-level guard; let `Dialog` handle it.

### 272. [LOW] `OverageWarningDialog` body copy assembled via string concatenation
Surfaced 2026-05-19 in the overage-acknowledgment-dialog review.

`portal/src/components/billing/OverageWarningDialog.tsx:64` —
`{hasPaymentMethod ? BASE_MESSAGE : BASE_MESSAGE + NO_CARD_SUFFIX}`
works but reads oddly. Two explicit, complete strings would be clearer
and easier to localize later.

Fix: define `CARD_MESSAGE` and `NO_CARD_MESSAGE` as two complete
constants and pick between them.

---

### 275. [HIGH] `platform/tests/test_cross_resource_envelope_helpers.py` exceeds 800-line threshold
**Closed as resolved 2026-05-13.** Split into `test_cross_resource_envelope_contact.py` (475 lines, 16 tests) and `test_cross_resource_envelope_property.py` (648 lines, 24 tests), with shared fake-model scaffolding extracted into `_cross_resource_fakes.py`. All 40 tests still pass.

<details>
<summary>Original body (preserved for history)</summary>

File is 1,175 lines holding 40 tests across 10 cross-resource envelope
helpers. Shared fake-model scaffolding lives inline to avoid the cost of
spinning up real Beanie models. The 800-line guideline from CLAUDE.md
applies in principle; in practice this is the trade-off of inline-explicit
test setup over hidden fixtures.

Fix: optional. If splitting, the natural boundary is by agent —
`test_cross_resource_envelope_contact.py` (4 helpers) vs
`test_cross_resource_envelope_property.py` (6 helpers) — with the shared
fake-model classes moved into a small `conftest_cross_resource.py` helper
imported by both. Could also fold under #4 as another file-size instance.

</details>


## 2026-05-19 review (overage acknowledgment dialog)

Captured after the per-resource overage acknowledgment dialog change. Three
MEDIUM findings; one was fixed in the same PR (subscription refresh on
sentinel-link open), one was extracted into a hook + unit-tested, and one is
deferred here as it requires a chat-retry mechanism that's out of spec for the
current change.

### 276. [LOW] Unused `_showNextTime` parameter in `handleConfirmSeatsOverage`

`portal/src/pages/SettingsPage.tsx:handleConfirmSeatsOverage` accepts a
`_showNextTime: boolean` parameter that's intentionally unused — the
user-invite dialog has no "Show this next time" checkbox, so the value is
always `true` and irrelevant. The underscore prefix signals intent but the
`OverageWarningDialog.onConfirm` interface forces the awkward signature.

Fix: narrow `OverageWarningDialog`'s `onConfirm` to `() => void` when
`resource !== "estimates"`. Two cleanest options: (a) make `onConfirm`'s
arg optional, (b) split into two prop callbacks (`onConfirm` for non-checkbox
variants, `onConfirmWithPref` for estimates). Either path touches all three
call sites — defer until the dialog API is touched for another reason.

### 277. [LOW] Plan file line references drift after implementation

`documentation/development/plans/overage-acknowledgment-dialog.md` references
specific line numbers (e.g. "SettingsPage.tsx:1042-1062") that shifted during
implementation. Plan files are point-in-time snapshots, so post-merge readers
will hit off-by-a-few-lines mismatches when navigating to the cited code.

Fix: optional housekeeping. Either refresh the line refs once after merge or
add a "post-implementation: line refs may be stale, search by function name"
disclaimer to the plan template. Low priority since plans aren't authoritative
documentation.

### 278. [LOW] `assert_token_quota` legacy "no-user" branch silently allows overage

`platform/services/llm/quota.py:assert_token_quota(company, user=None)` keeps
a backward-compat path: when `user is None` AND has-card AND over-quota, it
silently passes (metered overage, no acknowledgment required). This is
intentional and documented in the docstring — protects batch jobs, webhooks,
and other server-side callers that can't thread a user context.

Risk: any future LLM endpoint that forgets to pass `user` will silently meter
overage without acknowledgment, bypassing the new dialog flow.

Fix: not actionable now. Periodically audit `assert_token_quota(...)` call
sites (today: `routers/agents.py` orchestrate + estimate endpoints, both
correctly pass `current_user`). Consider a `logger.warning` in the no-user
branch if telemetry shows unintended callers hitting it.

---

### 279. [MEDIUM] Maple-chat estimate-creation refusal still uses the legacy direct add-card link

`ESTIMATE_LIMIT_REFUSAL_MESSAGE` in `platform/agents/text_utils.py:237-240` still embeds
`ADD_CARD_LINK` (`/settings?tab=billing&openAddCard=1`) when the orchestrator's
estimate-creation path is over quota with no card. The new acknowledgment
dialog flow is wired into `EstimatesPage` and `NewEstimateWithActivityPage`,
but the Maple-chat estimate-creation path bypasses the dialog and routes
directly to the billing tab.

Same-resource UX divergence:
- **EstimatesPage / NewEstimateWithActivityPage**: over-quota → sentinel-style
  dialog → OK acknowledges (has-card) or opens AddCard (no-card).
- **Maple chat → orchestrator → estimate creation**: over-quota + no-card →
  refusal bubble with direct add-card link; has-card silently passes
  through with metered overage (no acknowledgment required).

Fix: route the orchestrator estimate-refusal through a sentinel link that
opens the `OverageWarningDialog` with `resource="estimates"`. Two additional
pieces of work are needed:

1. Add a per-user `estimates_overage_acknowledged_at` enforcement in
   `services/estimate_quota.py` (parallel to the Maple-credits gate change),
   so has-card + over-quota also requires acknowledgment in the Maple chat
   path. Today `claim_estimate_slot_with_status` silently allows the overage
   when a card is on file; the spec implies acknowledgment should always
   precede billed overage.
2. Implement a chat-retry mechanism so OK in the dialog re-submits the user's
   last estimate-creation message. Without this, the user has to manually
   re-type their request after acknowledging. This is the bigger lift and is
   the reason the divergence is acceptable as an interim state.

Why deferred: implementing #2 cleanly requires hooking into `useMapleAgent`'s
last-message buffer + adding a "re-send after dialog confirm" callback path,
which is non-trivial and would expand the scope of the current PR beyond the
spec the user signed off on. Track until product asks for the consistent UX
across all three resources or a customer reports the dual-flow inconsistency.

### 281. [MEDIUM] `assert_token_quota` is ~77 lines (4 sequential 402 gates)

`platform/services/llm/quota.py:assert_token_quota` crossed the 50-line HIGH
threshold after the hard-cap branch landed. The function is still cohesive — a
flat top-to-bottom policy of hard-cap → over-quota+no-card → over-quota+no-ack
→ pass — and splitting now would fragment a policy that benefits from being
read in one place.

Fix when it grows another gate: extract a `_raise_quota_402(code, message)`
helper to collapse the four near-identical `raise HTTPException(...)` blocks.
Not worth doing today.

### 282. [LOW] `"hard_cap_reached"` string literal repeated in `routers/agents.py`

The literal appears at two sites in `orchestrate_agent_endpoint` — once in
the `code == "hard_cap_reached"` guard and once as the `intent=` kwarg passed
to `_maple_credits_refusal_payload`. A typo on one side silently breaks the
wiring.

Fix: promote to a module-level constant near the existing refusal helpers
(`HARD_CAP_INTENT = "hard_cap_reached"`). The existing `needs_payment_method`
/ `needs_acknowledgment` codes have the same duplication so apply the same
treatment if you ever pull this thread.

### 283. [LOW] `MAPLE_TOKEN_HARD_CAP` not configurable per plan

`platform/services/llm/quota.py` defines `MAPLE_TOKEN_HARD_CAP = 40_000_000`
as a single global. A future Pro/Enterprise tier might legitimately need a
higher ceiling.

Fix when the first higher-tier customer asks: add a `hard_cap_tokens` field
to each plan in `services/billing/plan_config.py`, then mirror the existing
`_included_tokens_for(company)` helper with `_hard_cap_for(company)`. Not
needed now — the spec called for one safety net, not per-tier tuning.

### 280. [LOW] Redundant `readOnly` on disabled overage-notification checkbox

`portal/src/pages/SettingsPage.tsx` (~line 1452, inside the Account-tab
read-only view) renders the "Show estimate overage notification" checkbox
with both `disabled` and `readOnly`. `disabled` already prevents interaction
and excludes the input from form submission; `readOnly` has no defined effect
on `<input type="checkbox">` per the HTML spec — it's a no-op there.

Fix: drop `readOnly`. Cosmetic only; the rendered behavior is identical
either way. Worth doing the next time anyone touches this block to keep
the JSX honest about what the attributes actually do.

---

## 2026-05-20 review (dashboard analytics window change)

### 284. [LOW] `compute_analytics` is ~115 lines

`platform/routers/estimates.py:507` — pre-existing length, not introduced by
the 2026-05-20 pipeline-window/updated_at change. The four-way
`asyncio.gather` plus per-bucket reshape (headline → by_division → by_status)
keeps everything in one function. The `/code-review` HIGH rule flags >50
lines, so worth splitting next time the function grows further.

Fix: extract `_compute_headline`, `_compute_by_division`, `_compute_by_status`
helpers. Defer until the next behavioural change in this function — splitting
purely for length without a behavioural driver is churn.

---

## 2026-05-20 review (mobile responsiveness — dashboard cards/charts/table)

### 285. [MEDIUM] Proliferating `@[Xrem]` container-query thresholds in DashboardPage

`portal/src/pages/DashboardPage.tsx` — the responsive pass introduced
breakpoints at 14rem, 18rem, 20rem, 24rem, 26rem, 32rem, and 48rem with no
shared rationale. Future tuning means hunting through the file. Surfaced
during `/code-review` on the responsive-dashboard change; not a regression,
just a maintainability watch-item.

Fix: when the next container-query pass lands, introduce a tiny
`dashboardBreakpoints.ts` (or a one-line comment at each call site
documenting *why* that threshold — icon-fit, table-row, etc.). Don't refactor
purely for this — wait for the next responsive change in this area.

### 286. [MEDIUM] `overflow-x-hidden` on the root PortalLayout flex container

`portal/src/components/Layout/PortalLayout.tsx:262` — added as a belt-and-
braces guard against any future child blowing out the viewport on mobile.
Acceptable today (every wide table in the portal already uses its own
`overflow-x-auto` scroll container), but worth noting so a contributor adding
e.g. a fluid horizontal-scroll admin view doesn't fight the parent.

Fix: no action. Drop a comment at the class site if it ever causes
confusion.

### 287. [LOW] `min-h-[60px]` on vertical status labels may clip long words

`portal/src/components/dashboard/PipelineStatusChart.tsx:140` — `Completed`
rotated to `writing-mode: vertical-rl` is ~54-58px tall, so 60px is tight.
A future status name like `Cancelled` (~60px) could touch the limit.

Fix: bump to `min-h-[72px]`, or drop the `min-h` entirely and rely on
`flex-row items-start` to size itself naturally. Defer until a new status
label is added.

### 288. [LOW] Spot-check rotated chart labels with a screen reader

`portal/src/components/dashboard/PipelineStatusChart.tsx` — the bar chart
already wraps the data inside `role="img" aria-label={ariaLabel}`, so the
rotated visual labels are decorative for assistive tech. Worth a one-time
VoiceOver pass to confirm no regression.

Fix: manual check, no code change unless something reads wrong.

---

## 2026-05-13 `/code-review` pass (hodgepodge change — deferred follow-ups)

Carried over from the hodgepodge `/code-review` (2026-05-13). The two HIGHs from that pass (sequential analytics awaits, unescaped markdown labels) shipped with the original change; these are the deferred MEDIUMs/LOWs. The `compute_analytics` company-id validation finding from this batch was folded into #67.

### 289. [MEDIUM] `useEffect` references function declared later in the same component
**Where:** `portal/src/pages/MaterialsPage.tsx` and `portal/src/pages/PeoplePage.tsx` — the `?open=<id>` effect calls `openEditMaterial` / `openEditLabour` declared further down. (Note: this was originally flagged when those effects opened the edit modal; the modal logic has since been removed, so the *symptom* is gone — but the pattern of effect-before-declaration may still apply if either page picks up a similar handler later.)

**Issue:** Works at runtime because effects fire after the component body finishes evaluating, but it's brittle, future-hostile, and would silently fail eslint's `react-hooks/exhaustive-deps` rule.

**Fix:** When adding any new effect in those files, declare its dependencies above the effect, or wrap helpers in `useCallback`.

### 290. [MEDIUM] Dashboard analytics fetch error is silent
**Where:** `portal/src/pages/DashboardPage.tsx` — the `estimatesApi.analytics(...).catch(() => setAnalytics(null))` branch.

**Issue:** Network/server errors are swallowed and the page silently shows `$0` cards. A user can't distinguish "no estimates yet" from "the API is down".

**Fix:** Track an `analyticsError` state and render a small inline note ("Couldn't load analytics — retry") when set.

### 291. [MEDIUM] `test_estimates_analytics.py` exclusion assertion is brittle
**Where:** `platform/tests/test_estimates_analytics.py:163-164` (`test_analytics_excludes_lost_and_archived_from_pipeline`)

**Issue:** The assertion is `777.0 not in (pipeline, pipeline - 4000.0, pipeline - 3500.0)` against hand-computed offsets. A subtle inclusion-bug could pass the assertion. The test also relies on the test runner's wall-clock to align with the seeded `now`, which has caused at least one false alarm during development.

**Fix:** Either (a) plumb `now` through `compute_analytics` as a hook for testing and pin it via the route, then assert exact totals, or (b) use `freezegun` to pin time. Simplest near-term: rebuild the assertion as `assert pipeline == <explicit_in_window_sum>` with no clock dependency.

### 292. [LOW] `RowActionsMenu` has two near-identical menu-item buttons
**Where:** `portal/src/components/common/RowActionsMenu.tsx` — the Move up and Move down `<button>` blocks differ only in icon, label, and onClick.

**Issue:** Minor duplication. Refactor only worthwhile if a fourth/fifth menu item lands.

**Fix:** Extract a small `<MenuItem icon={…} label={…} disabled={…} onClick={…} />` helper if the menu grows.

---

## 2026-05 `/code-review` pass (contact form + reCAPTCHA v3 — deferred follow-ups)

Carried over from the `/code-review` of the contact-form expansion + reCAPTCHA v3 integration on the marketing site (May 2026). The two security-flavored fixes (emulator gate, structured email addresses) and a vitest unit suite for `verifyRecaptcha` shipped with the original change. The HIGH refactor of the `contact` request handler from this batch was folded into #268 (with the proposed extraction shape preserved there).

### 293. [HIGH] ~~Frontend test for `resolveRecaptchaSiteKey` blocked by current architecture~~ — RESOLVED 2026-05-21
**Closed as resolved 2026-05-21.** Contact modal moved out of `website/public/` into a proper Vite entry. New layout:
- `website/contact-modal/install.js` — extracted from `public/contact-modal.js`; named-exports `install`, `resolveRecaptchaSiteKey`, `loadRecaptcha`, `getRecaptchaToken`. No top-level side effects so vitest can import without triggering DOM injection.
- `website/contact-modal/index.js` — 16-line build entry that imports `install` and runs it on DOMContentLoaded.
- `website/contact-modal/__tests__/resolveSiteKey.test.js` — 4 tests (real key → returned, empty → empty string, unsubstituted Vite placeholder → empty string, whitespace trim).
- `vite.config.ts` — added `'contact-modal'` to `rollupOptions.input` so prod build emits `dist/contact-modal.js`; added a `contactModalDevRewrite()` middleware that serves a `import('/contact-modal/index.js')` shim when the dev server receives `GET /contact-modal.js` (HTML pages already use `<script src="/contact-modal.js" defer>` — no HTML changes needed).
- `vitest.config.ts` — extended `include` glob to `contact-modal/**/*.test.{js,ts}`.
- `public/contact-modal.js` — deleted (was 491 lines).

Also closed **#298** as a side-effect — the heuristic placeholder check became `trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%'` while editing the file. Verified: vitest 42/42 green; `vite build` emits `dist/contact-modal.js` cleanly; dev server smoke-test confirms `/contact-modal.js` returns the dynamic-import shim and `/contact-modal/index.js` serves the source.

The follow-on opportunity (#296, the ~120-line `install()` split) is now unblocked — `install` is exported and could be unit-tested or split further.

<details>
<summary>Original body (preserved for history)</summary>

**Where:** `website/public/contact-modal.js`.

**Why blocked:** `contact-modal.js` lives in `public/` and is served verbatim by Vite/Hosting. It's wrapped in an IIFE (no exports), so its helpers can't be imported by vitest. To test `resolveRecaptchaSiteKey` (the Vite-substitution-detection logic), the file needs to become a proper Vite/Rollup entry — same pattern as `widget/index.tsx` / `maple-widget.js`.

**Suggested move:**
1. Create `website/contact-modal/index.ts` (or `.js`) with the modal logic, exporting helpers like `resolveRecaptchaSiteKey` for tests.
2. Add the entry to `vite.config.ts` `rollupOptions.input` and `entryFileNames` rules so the build emits `dist/contact-modal.js` at the same path.
3. Drop `website/public/contact-modal.js`.
4. Add `website/contact-modal/__tests__/resolveSiteKey.test.ts` covering: real key → returned, empty → empty string, raw `%VITE_RECAPTCHA_V3_SITE_KEY%` placeholder → empty string.

This refactor also unlocks unit-testing the submit handler, the captcha load promise, and the form validation helper.

</details>

### 294. [MEDIUM] Make `RECAPTCHA_MIN_SCORE` configurable
**Where:** `website/functions/index.js:13`.

**Why:** The 0.5 threshold is hardcoded. Fresh keys with no traffic history routinely score below it (we hit this in dev). Tuning currently requires a code change + redeploy.

**Suggested fix:** Use `defineString('RECAPTCHA_V3_MIN_SCORE', { default: '0.5' })` from `firebase-functions/params`, parse to float at handler start, fall back to 0.5 on `NaN`. Set per-environment via `firebase functions:config` or a runtime param.

### 295. [MEDIUM] Tighten CORS
**Where:** `website/functions/index.js:26` — currently `cors: true` (wildcard).

**Why:** The contact form is served via Hosting rewrite, so traffic to `/api/contact` is same-origin and doesn't need CORS at all. Wildcard CORS lets any origin POST to the endpoint; reCAPTCHA mitigates abuse but tightening costs nothing.

**Suggested fix:**

```js
cors: [
  'https://3maples.ai',
  'https://www.3maples.ai',
  'https://maples-website-dev.web.app',
  'https://maples-website-dev.firebaseapp.com',
  'http://localhost:5050', // hosting emulator
],
```

Or drop `cors` entirely and rely on same-origin Hosting rewrites for prod traffic; only add CORS when explicit cross-origin support is needed.

### 296. [MEDIUM] `install()` in `contact-modal.js` is ~120 lines
**Where:** `website/public/contact-modal.js:240-360`.

**Why:** Mixes DOM creation, ref binding, captcha setup, open/close handlers, and submit logic. Hard to follow at a glance.

**Suggested fix:** Split into `renderModal()`, `bindOpenClose(refs)`, `bindSubmit(refs, captcha)`. Cleanest after the file is moved out of `public/` (see #293), since the helpers can then be unit-tested with injected refs.

### 297. [LOW] Hoist `optionalString` to module scope
**Where:** `website/functions/index.js:77`.

**Why:** Pure helper recreated on every request. Negligible perf cost but belongs at module scope alongside `escapeHtml`.

### 298. [LOW] ~~Replace placeholder heuristic with explicit equality~~ — RESOLVED 2026-05-21
**Closed as resolved 2026-05-21** as a side-effect of #293. Now `trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%'` in `website/contact-modal/install.js:resolveRecaptchaSiteKey`. Covered by the new vitest case at `contact-modal/__tests__/resolveSiteKey.test.js`.

<details>
<summary>Original body (preserved for history)</summary>

**Where:** `website/public/contact-modal.js:5-11` — `resolveRecaptchaSiteKey`.

**Why:** Current check rejects values containing `%` or starting with `VITE_`. Functional but heuristic. An explicit check on the literal placeholder is clearer:

```js
if (!trimmed || trimmed === '%VITE_RECAPTCHA_V3_SITE_KEY%') return '';
return trimmed;
```

</details>

### 299. [LOW] Drop `escapeHtml(label)` on hardcoded labels
**Where:** `website/functions/index.js:183`.

**Why:** `htmlDetails` escapes label values that are all string literals defined two lines above. Defensive but unnecessary; misleads a reader into thinking labels could be untrusted.

**Suggested fix:** Drop the `escapeHtml(label)` call (keep `escapeHtml(value)`). Or move labels to a top-level constant to make their hardcoded nature explicit.

---

## 2026-05-21 `/code-review` pass (post-#3 mypy batch — agents/estimate cluster + #90 + #93)

Carried over from the `/code-review` of the 2026-05-21 mypy session that closed #90, #93, and the entire `agents/estimate/*` cluster (276 → 77 mypy errors). The two HIGH file-size flags from that review (crud_handlers.py at 1,449 lines and work_item_handlers.py just crossed 800) fold into #4. The MEDIUMs below are deferred housekeeping.

### 300. [MEDIUM] 17 near-identical `assert client.portal is not None` lines across 10 test files
**Where:** `tests/test_audit_integration.py`, `test_change_logs_api.py`, `test_company_api.py`, `test_divisions_api.py`, `test_feedback_anonymous.py`, `test_feedback_api.py`, `test_property_api.py`, `test_rate_card_bootstrap.py`, `test_resources_rbac.py`, `test_template_api.py`.

**Issue:** The #93 fix added 17 sites of `assert client.portal is not None  # TestClient context manager guarantees a portal (mypy hygiene)`. Comment string is identical at each site. DRY violation flagged in the code review of that batch — the original #93 entry mentioned "a thin `_get_portal()` helper" as the alternative but it was rejected as larger touch (touching every `.call` site in 10 files).

**Fix:** add a session-scoped `portal` fixture in `tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def portal(client: TestClient):
    assert client.portal is not None  # TestClient context manager guarantees a portal
    return client.portal
```

Tests then take `portal: BlockingPortal` and call `portal.call(_fn)` instead of `client.portal.call(_fn)`. Defer until another test-suite touch in any of the 10 files — refactoring purely for DRY is churn.

### 301. [MEDIUM] `messages: List[Any]` in `agents/estimate/service.py:1811` weakens type info
**Where:** `agents/estimate/service.py:1811` — `messages: List[Any] = [SystemMessage(content=formatted_prompt)]`.

**Issue:** Annotated as `List[Any]` to allow appending `HumanMessage` to a list initialized with `SystemMessage`. Loses type safety on all subsequent `.append()` calls (4 sites in this function plus several elsewhere).

**Fix:** use `List[BaseMessage]` from `langchain_core.messages` (or `langchain.schema.BaseMessage`) — that's the actual base class for `SystemMessage` / `HumanMessage` / `AIMessage`. Tighter and more honest. Same pattern likely needed at other langchain message-list sites in `service.py` that escaped this pass.

### 302. [MEDIUM] TYPE_CHECKING stub blocks duplicate signatures from sibling mixins
**Where:** `agents/estimate/crud_handlers.py:95-179` (19 stubs) and `agents/estimate/work_item_handlers.py:65-91` (4 stubs).

**Issue:** Each stub block lifts method signatures from sibling mixins (`CrudParsingMixin`, `WorkItemHandlersMixin`, etc.) and re-declares them inside `if TYPE_CHECKING:` so mypy stops flagging attr-defined on the cross-mixin calls. If a signature in the real implementation drifts (e.g. `_crud_envelope` adds a new keyword param), the stub won't catch it — mypy silently uses the stub.

**Fix:** define an `EstimateAgentHostProtocol(Protocol)` in `agents/estimate/host_protocol.py` (or a shared types module) that captures the cross-mixin contract once. Each mixin can reference the Protocol via `Self` bound or via inheritance from a shared base. Short-term mitigation: per-method docstring pointers (`# See agents/estimate/crud_helpers.py:381 — keep in sync`). Worth doing if the stubs grow further; for now the 23 stubs are stable enough.

### 303. [HIGH] ~~Unit tests missing for the 9 new `routers/agent_helpers/` modules~~ — RESOLVED 2026-06-03
**Severity**: HIGH (resolved)

**Resolved 2026-06-03**: 8 module-level unit-test files added (103 tests), one
per untested helper — `estimate_gathering.py` already had
`tests/test_estimate_gathering.py`, so the original "9" was 8 in practice:

| Module | Test file | Tests |
|---|---|---|
| `finalize_result.py` | `tests/test_agent_helpers_finalize_result.py` | 17 |
| `estimate_resolver.py` | `tests/test_agent_helpers_estimate_resolver.py` | 9 |
| `delegate_generic.py` | `tests/test_agent_helpers_delegate_generic.py` | 7 |
| `pending_estimate_follow_up.py` | `tests/test_agent_helpers_pending_estimate_follow_up.py` | 24 |
| `optional_follow_up.py` | `tests/test_agent_helpers_optional_follow_up.py` | 21 |
| `delegate_get_estimate.py` | `tests/test_agent_helpers_delegate_get_estimate.py` | 11 |
| `delegate_estimate_ops.py` | `tests/test_agent_helpers_delegate_estimate_ops.py` | 14 |
| `delegate_create_estimate.py` | `tests/test_agent_helpers_delegate_create_estimate.py` | 7 |

Each file covers every envelope return path / state-machine branch via
injected fakes + `monkeypatch` (no DB or LLM). All 103 pass; mypy clean.
A latent matcher quirk surfaced and was characterized (not fixed —
tracked as a new LOW below): `find_property_by_name_or_address` treats a
property with a **blank `street`** as a contains-match for *any* query
(`"" in query` is always true), so such a property auto-links. See
`test_find_property_blank_street_contains_matches_any_query`.

**Where:** `routers/agent_helpers/pending_estimate_follow_up.py`, `optional_follow_up.py`, `estimate_gathering.py`, `delegate_create_estimate.py`, `delegate_estimate_ops.py`, `delegate_get_estimate.py`, `delegate_generic.py`, `finalize_result.py`, `estimate_resolver.py` (all landed 2026-05-22).

**Issue:** All 9 helper modules extracted from `orchestrate_agent_endpoint` lack module-level unit tests. Behavior is exercised through `tests/test_orchestrator_endpoint.py` integration tests (52 passing), so no regression risk today — but each helper is a state machine with multiple return paths (`handle_pending_estimate_follow_up` has 9 envelope returns spanning `confirm`/`select_property`/`negative`/`list-properties`/`no-properties`/`escape-hatch`/`resolve-error`/`success` shapes) and the integration tests don't necessarily cover every branch. Per `CLAUDE.md` "tests are mandatory after any code change" — extraction without unit-test backfill leaves the per-branch behavior implicit in the endpoint tests.

**Fix:** Add per-helper unit-test files (`tests/test_pending_estimate_follow_up.py`, etc.) with one test per return path. Each test constructs a `context_payload` matching the entry state, asserts the returned envelope's `intent` / `response` / `result.operation` / `needs_clarification` flags. Use the existing fixtures (`monkeypatch` for `Estimate.get`, `properties_api_get_properties`, etc.) — same shape as the integration tests but scoped to one helper. Estimated 6-9 tests per module = ~60-80 new tests total.

### 304. [MEDIUM] Dual-mock pattern in `test_orchestrator_endpoint.py` after helper extractions
**Where:** `tests/test_orchestrator_endpoint.py` — 4 sites for `properties_api_get_properties`, 4 sites for `estimates_api_get_estimates`, 2 sites for `estimates_api_get_estimate`, 2 sites for `prepare_generated_estimate` / `save_generated_estimate`.

**Issue:** After the 2026-05-22 helper extractions, several `monkeypatch.setattr(agents_router, "X", ...)` calls now have a parallel `monkeypatch.setattr("routers.agent_helpers.<helper>.X", ...)`. The `agents_router.X` patches are NOT yet dead because two callsites of `estimates_api_get_estimate{s}` still live inside `_delegate_to_agent` (Estimate Agent fallback for unhandled intents — lines ~880-911 in `routers/agents.py`). Functionally correct but cluttered, and easy to forget which patches are load-bearing.

**Fix:** When the remaining `_delegate_to_agent` Estimate Agent fallback is extracted (would naturally consolidate into a `delegate_estimate_misc.py` module or merge into `delegate_estimate_ops.py`), the `agents_router.estimates_api_get_estimate{s}` aliases become fully dead. At that point: drop the `agents_router`-targeted patches at lines 1835, 1886, 1953, 2028, 2853-2854, 2933-2934; keep only the helper-module patches. Also update `test_orchestrate_imports_plain_helpers_not_endpoints` contract test (line 3083) — its assertion that `agents_router.estimates_api_get_estimates is fetch_estimates` would need to drop both `estimates_api_*` aliases (the test already moved `properties_api_get_properties` to the helper module's binding).

### 305. [HIGH] Long handler functions in `work_item_field_handlers.py`
**Where:** `agents/estimate/work_item_field_handlers.py` — `_handle_work_item_add_material()` (132 lines), `_handle_work_item_add_activity()` (114 lines), `_handle_work_item_remove_material()` (101 lines), `_handle_work_item_set_total()` (94 lines), `_handle_work_item_recurring_enable()` (93 lines).

**Issue:** Five handlers exceed the 50-line threshold. Each mixes estimate resolution, work-item matching, sub-resource lookup, mutation, sub_total recalculation, and save into one method.

**Fix:** Extract shared boilerplate (resolve estimate → find work item → clarify on miss) into a `_resolve_work_item_for_update()` helper returning `(target, job_items, idx, matched, err_response)`. Extract catalog lookup + item construction into `_resolve_and_build_material_item()` / `_resolve_and_build_activity_item()`. Each handler shrinks to ~30 lines of domain logic.

### 306. [HIGH] `_detect_work_item_op()` is 202 lines
**Where:** `agents/estimate/work_item_handlers.py:110`

**Issue:** Grew from ~75 lines to 202 with the new sub-resource ops. Readable as a cascading if-chain but past the length threshold.

**Fix:** Extract the `has_wi` block (lines 140–212) into `_detect_sub_resource_op()` that `_detect_work_item_op` calls first. Keeps the legacy patterns untouched.

### 307. [HIGH] ~~Full-catalog fetch for material/role lookup~~ — RESOLVED 2026-06-03
**Severity**: HIGH (resolved)
**Where:** `agents/estimate/work_item_field_handlers.py:531` and `:889`

**Issue:** `Material.find(company==X).to_list()` and `Labour.find(company==X).to_list()` load the full company catalog into memory for Python-side substring matching. Acceptable at current scale (<1000 items) but degrades on larger catalogs.

**Resolved 2026-06-03**: extracted two helpers — `_find_catalog_materials()`
and `_find_catalog_roles()` — that push the name substring match into MongoDB
via a case-insensitive `{"name": {"$regex": re.escape(hint), "$options": "i"}}`
filter (alongside the existing `company ==` clause). The handlers now receive
only matching documents instead of the whole catalog; the exact-match /
ambiguity disambiguation logic stays in the handler on the (now-smaller) list.
`re.escape` preserves literal-substring semantics for hints containing regex
metacharacters. Dead inline `from models import Material/Labour` imports in the
two handlers removed. New `tests/test_work_item_catalog_lookup.py`: 6 unit tests
(query-shape + escaping + empty-hint short-circuit, `find` stubbed) plus 1 live
test that exercises the real `$regex` against the test DB (match returns only
the matching doc; non-match returns nothing). mypy clean; 102 related tests pass.

### 308. [MEDIUM] Duplicated work-item/help bypass in orchestrator
**Where:** `agents/orchestrator/service.py:578` and `:2173`

**Issue:** The `what + work item (excluding definitional)` pre-help guard appears in both `_classify_with_rules` and `process()` with the same 3-regex check. If one is updated the other can drift.

**Fix:** Extract into a `_is_work_item_field_query(text: str) -> bool` predicate called from both sites.

### 309. [MEDIUM] Hardcoded `start_year=2026` in recurring param parser
**Where:** `agents/estimate/work_item_field_handlers.py` — `_parse_recurring_params()` at 3 sites

**Issue:** `RecurrenceSchedule` objects default to `start_year=2026`. After December 2026 this produces stale schedules.

**Fix:** Use `datetime.now(timezone.utc).year` instead of the literal.

### 310. [MEDIUM] `work_item_field_handlers.py` is 1286 lines
**Where:** `agents/estimate/work_item_field_handlers.py`

**Issue:** Above the 800-line threshold. Single mixin with 12 handlers following the same pattern.

**Fix:** Addressed naturally when #305 extracts shared boilerplate — the file should drop below 800 lines after the helper extraction.

### 311. [HIGH] `SettingsPage.tsx` is 2,541 lines
**Where:** `portal/src/pages/SettingsPage.tsx`

**Issue:** Well above the 800-line threshold. The team-invitation flow, seat-count display, billing gate logic, and numerous unrelated settings panels all live in one component.

**Fix:** Extract the seat overage gate logic into a `useSeatsOverageGate` hook, the invitation form into an `InviteTeamSection` sub-component, and the billing display rows into `BillingUsageSection`. This PR touched this file — the debt is growing.

### 312. [LOW] `try_claim_estimate_slot` override path doesn't warn on missing document
**Where:** `platform/services/estimate_quota.py:76`

**Issue:** When `company.overage_billing_disabled` is true, `find_one_and_update` returning `None` (document gone mid-request) is silently ignored — the in-memory counter is stale but `True` is returned. No log entry makes this invisible in operational monitoring.

**Fix:** Add `logger.warning("overage_billing_disabled slot claimed but company %s not found in DB", company.id)` inside the `if result is None` branch.

### 313. [LOW] Inconsistent null-check style across overage sentinel (`=== null` vs `!= null`)
**Where:** `portal/src/utils/overage.ts:58` vs `portal/src/components/settings/BillingTab.tsx`

**Issue:** `overage.ts` uses loose `!= null` (catches `undefined` too); `BillingTab.tsx` uses strict `=== null`. Both are correct for their context, but the inconsistency across files sharing the same sentinel contract is a readability trap.

**Fix:** Standardise on `=== null` / `!== null` across both files when the intent is to test for the unlimited sentinel specifically.

---

## 2026-06-02 `/code-review` pass (Estimates multi-select status filter)

Findings from the Estimates page status-filter change (single `<select>` →
multi-select checkbox dropdown: new `src/lib/estimateStatusFilter.ts` +
`src/components/common/EstimateStatusFilter.tsx`, wired into
`src/pages/EstimatesPage.tsx`). The one MEDIUM finding (`role="listbox"` on a
container of checkboxes) was fixed in-session by switching to `role="group"`.
The two LOW items below were deferred.

### 314. [LOW] Filter-driven estimate refetch swallows errors silently
**Where:** `portal/src/pages/EstimatesPage.tsx` — `loadData` (~line 180) + the initial-load effect (~line 305)

**Issue:** Toggling the Archived / All Status filter changes `includeArchived`, which re-runs the load effect via `loadData({ showLoading: false })` (the deliberate fix so the page doesn't unmount the open dropdown). But `loadData`'s `catch` only sets `error` when `showLoading` is true, so a failed archived refetch shows no error and no archived rows — a silent partial failure. This matches the existing `loadData({ showLoading: false })` background-refresh convention (polling, `performDuplicate`), so it's intentional, not a regression.

**Fix:** If feedback on filter-refetch failures is wanted, surface a non-blocking inline toast/banner rather than the full-page `ErrorState` (which would re-introduce the unmount-the-dropdown bug this change fixed).

### 315. [LOW] Duplicate `normalizeEstimateStatus` definition (pre-existing)
**Where:** `portal/src/pages/EstimatesPage.tsx:33` vs `portal/src/lib/estimateStatus.ts`

**Issue:** The local `normalizeEstimateStatus` in `EstimatesPage.tsx` (still used by `getSortableValue`) is byte-identical to the exported one in `lib/estimateStatus.ts`. The new `estimateStatusFilter.ts` already imports the canonical version, so the page now has both in play. Pre-existing duplication — not introduced by this change.

**Fix:** Import `normalizeEstimateStatus` from `../lib/estimateStatus` and delete the local copy so there's a single definition.

---

## 2026-06-02 `/code-review` pass (Template instantiation + estimate age/staleness + Maple phrasing expansion)

Findings from the template-driven estimate instantiation feature
(`agents/estimate/template_scaling.py`, `routers/agent_helpers/template_estimate.py`),
the `created_at`→`updated_at` age/staleness refactor, and the Maple
phrasing/routing expansion. The one HIGH item (a `parse_job_size` ordering bug
that under-scaled `NxN <area-unit>` dimensions, e.g. `"20x20 sq ft"` → 20 instead
of 400) plus its missing test coverage were **fixed in-session** (reordered
`_DIMENSIONS_RE` ahead of `_VALUE_UNIT_RE`; added
`test_dimensions_with_explicit_area_unit`). The items below were deferred.

### 316. [MEDIUM] `_finalize_template_estimate` is ~100 lines with duplicated company-context resolution
**Where:** `platform/routers/agent_helpers/template_estimate.py:94-197` (and the near-identical block in `begin_template_estimate:215-225`)

**Issue:** Exceeds the 50-line guideline and mixes company-context validation, the quota gate, create/scale/save, audit logging, and three envelope constructions. The company-context resolution (lines 106-126) is duplicated almost verbatim in `begin_template_estimate`.

**Fix:** Extract a shared `_resolve_company_or_refuse(...)` used by both entry points, and lift the audit-log + success-envelope tail into a helper. Reduces both length and duplication.

### 317. [MEDIUM] `recentEstimates.ts` reinvents archived-status normalization
**Where:** `portal/src/lib/recentEstimates.ts:18`

**Issue:** `(e.status ?? "").trim().toLowerCase() !== "archived"` open-codes a partial status normalization when the canonical `normalizeEstimateStatus` in `lib/estimateStatus.ts` is already used in ~6 other modules. Risks drift if status values gain spacing/casing variants.

**Fix:** `import { normalizeEstimateStatus } from "./estimateStatus"` and compare `normalizeEstimateStatus(e.status) !== "archived"`. (Same single-source-of-truth concern as #315.)

### 318. [MEDIUM] Broad `except Exception` in template instantiation swallows the real failure
**Where:** `platform/routers/agent_helpers/template_estimate.py:156`

**Issue:** The create/scale/save block catches bare `Exception`, releases the quota slot, and returns a generic "try again" with no logging. A genuine bug (scaling math, model validation) is invisible in logs and indistinguishable from a transient DB blip.

**Fix:** `logger.exception("template instantiation failed for company %s", company_ctx)` before returning the friendly message, matching the pattern in `material/service.py:_load_categories`.

### 319. [MEDIUM] Orchestrator/material routing keeps growing already-oversized files
**Where:** `platform/agents/orchestrator/service.py` (2402 lines), `platform/agents/material/service.py` (2710 lines)

**Issue:** This change correctly adds net-new logic as separate modules, but the new routing fast-paths (`_match_estimate_list_filter`, `_match_material_list_filter`) were added to files already well over the 800-line guideline. Pre-existing structural debt, not introduced here.

**Fix:** Next time these files are touched, consider extracting the orchestrator routing fast-paths into a `routing/` submodule.

### 320. [LOW] f-string with no placeholders
**Where:** `platform/routers/agent_helpers/template_estimate.py:354`

**Issue:** `prefix=f"That unit doesn't match this template. "` has an `f` prefix but no interpolation (`ruff` F541).

**Fix:** Drop the `f`.

### 321. [LOW] `begin_template_estimate` divides by `template.size` without the zero-guard its sibling has
**Where:** `platform/routers/agent_helpers/template_estimate.py:200-201,258-261`

**Issue:** `_has_baseline` accepts `size == 0.0` (`is not None`), then `begin_template_estimate` computes `converted / template.size` → `ZeroDivisionError`. The pending-turn handler guards this (`not baseline_size`), so the two paths are inconsistent. A zero-size template is nonsensical/unlikely but the asymmetry is a latent trap.

**Fix:** Make `_has_baseline` require `template.size` truthy, or guard the division and fall through to `_ask_size_envelope`.

### 322. [LOW] `find_property_by_name_or_address` auto-matches a blank-street property to any query
**Where:** `platform/routers/agent_helpers/pending_estimate_follow_up.py:101-110`

**Issue:** The contains-match block tests `_property_address_of(item).lower() in query`. When a property's `street` is blank, `"" in query` is always true, so a property with no street is treated as a substring-match candidate for *every* property query. With a single such property in the company, the estimate-link follow-up will silently link the new estimate to it even for an unrelated reply. Surfaced and characterized while backfilling #303 (`test_find_property_blank_street_contains_matches_any_query`).

**Fix:** Guard the empty-string clauses — only test `address in query` / `name in query` when the field is non-empty. Flip the characterization test's assertion in the same change.

---

## 2026-06-03 (ruff lint gate adoption)

`ruff` was adopted as a hard lint gate for `platform/` on 2026-06-03, the same
model as the mypy gate (#3). Config is pinned in `platform/ruff.toml`; run via
`./run_ruff.sh`. Ruleset: `E, F, I, B, C4, SIM` — `E501` (line length) off, `UP`
(pyupgrade) intentionally excluded (its annotation rewrites collide with the
mypy.ini playbook). See CLAUDE.md "ruff is a Gate, Not a Suggestion" for the
full policy + recurring playbook.

On adoption the safe auto-fixable backlog (~287 fixes: import sorting + trivial
simplifications, **no import deletions**) was applied across 186 files. The
manual backlog below remains and must be worked down before the project is
fully green. **Until then, scope `./run_ruff.sh` to the files you touch** so you
gate your change without tripping over the legacy backlog.

> **F401 is report-only by config** (`unfixable = ["F401"]`). Blanket
> `ruff --fix` is **unsafe** in this codebase: it deletes (a) re-export-hub
> imports — modules that import a symbol only to re-expose it (`routers/estimates.py`,
> `routers/agents.py`, `agents/estimate/service.py`) — and (b) module-level
> imports that tests monkeypatch via `setattr(module, "Name", ...)` (e.g.
> `estimate_service.ChatOpenAI`). Both break imports/tests; the second isn't
> caught by an `import main` smoke test. This was learned the hard way during
> adoption (140 test failures from the first sweep, fully reverted). Triage each
> F401 by hand: genuinely dead → delete; re-export → add to `__all__`;
> monkeypatch target → keep with `# noqa: F401` + reason.

### 323. [MEDIUM] ruff manual backlog — 281 findings remaining (all F401) across the conservative ruleset
Snapshot 2026-06-03 (`./run_ruff.sh`); **B904 slice closed 2026-06-03** (32 → 0);
**style/simplify slice (E741/E712/SIM/C4/B007) closed 2026-06-04** (52 → 0);
**E402 + F841 slices closed 2026-06-04** (56 + 52 → 0).
Remaining `ruff check .` (2026-06-04): **F401 281 — the only category left.**

| Rule | Count | Category | Notes |
|---|---|---|---|
| ~~**B904** raise-without-`from`~~ | ~~32~~ → **0** | correctness | **RESOLVED 2026-06-03** — see progress note below |
| F401 unused-import | 281 | dead code | report-only; triage per the hazard note above |
| ~~E402 import-not-at-top~~ | ~~56~~ → **0** | style | **RESOLVED 2026-06-04** — see progress note below |
| ~~F841 unused-variable~~ | ~~52~~ → **0** | dead code | **RESOLVED 2026-06-04** — see progress note below |
| ~~E741 ambiguous-name (`l`/`I`/`O`)~~ | ~~24~~ → **0** | style | **RESOLVED 2026-06-04** — see progress note below |
| ~~E712 `== True/False`~~ | ~~5~~ → **0** | style | **RESOLVED 2026-06-04** |
| ~~SIM103/102/108/105~~ | ~~16~~ → **0** | simplify | **RESOLVED 2026-06-04** |
| ~~C408/C401/C416~~ | ~~5~~ → **0** | simplify | **RESOLVED 2026-06-04** |
| ~~B007 unused-loop-var~~ | ~~2~~ → **0** | style | **RESOLVED 2026-06-04** |

**Recommended order:** (1) **B904** — the only correctness category; it matches
CLAUDE.md's "don't leak/garble tracebacks" rule. Add `raise ... from err`
(preserve cause) or `raise ... from None` (suppress). B904 sites by file:
`services/google_drive_service.py` (12), `routers/agents.py` (6),
`routers/estimate_helpers/doc_versions.py` (3), `routers/audit_logs.py` (3),
`routers/templates.py` (2), `routers/stripe_webhooks.py` (2), `routers/auth.py`
(2), `routers/materials.py` (1), `routers/billing.py` (1). (2) the mechanical
style/simplify slices (E741/E712/SIM/C4/B007) — low risk. (3) E402 + F841 —
case-by-case judgment. (4) F401 last — largest and needs the per-import triage
above. **Slices (1)–(3) are now closed; only F401 (4) remains.**

Work each slice as its own commit (`./run_ruff.sh --select B904` to scope a
run). Update this entry's counts as slices close; mark RESOLVED when
`./run_ruff.sh` is clean project-wide.

**Progress 2026-06-03 — B904 slice closed (32 → 0).** All 32 raise-without-`from`
sites now chain explicitly; `./run_ruff.sh --select B904` is clean project-wide.
Cause-preservation split followed the playbook:
- **`from e`** (preserve cause) where the exception was already bound *and* is a
  genuine unexpected/internal failure worth chaining: `routers/stripe_webhooks.py`
  (signature-verify 400, handler 500) and all 12 `services/google_drive_service.py`
  sites (RuntimeError on credential/build failure + HTTPException 500s on Drive
  HttpError — each `except ... as e`).
- **`from None`** (suppress) where the re-raise is a deliberate boundary over
  expected input or an already-logged error: input-validation conversions
  (`routers/audit_logs.py` ×3 invalid enum 400, `routers/auth.py` ×2 invalid
  role/industry 400, `routers/agents.py` ×2 invalid ObjectId 422), 409 conflict
  conversions (`routers/templates.py` ×2 DuplicateKey), and 500/502 handlers that
  already `logger.exception(...)` the full traceback (`routers/agents.py` ×4,
  `routers/billing.py`, `routers/materials.py`, `routers/estimate_helpers/doc_versions.py` ×3).

Verified: full-project `./run_mypy.sh` slice clean (`routers`, `services`); 155
related tests pass (`test_stripe_webhooks`, `test_template_api`,
`test_audit_logs_api`, `test_billing_enterprise_contact`, `test_google_drive_service`,
`test_estimate_docs_api`, `test_orchestrator_endpoint`, `test_auth_api`). Next
slice per the recommended order: the mechanical style/simplify batch
(E741/E712/SIM/C4/B007).

**Progress 2026-06-04 — style/simplify slice closed (52 → 0).**
`./run_ruff.sh --select E741,E712,SIM,C4,B007` is clean project-wide. Breakdown:
- **E741** (24) — every `l` ambiguous-name was the same idiom: a labour item in a
  loop/comprehension. Renamed `l` → `lab` throughout each enclosing scope (renaming
  *all* uses, not just the binding). Sites: `agents/cross_resource.py`,
  `agents/estimate/{crud_handlers,llm_pipeline,service ×3,tools,work_item_field_handlers}.py`,
  `agents/property/service.py`, `routers/estimate_helpers/{job_item_builders ×5,snapshots ×2}.py`,
  `routers/estimates.py` ×3, `routers/labours.py`, and tests
  (`test_cross_resource_joins.py`, `test_labour_api.py` ×2).
- **E712** (5, all tests) — `== True/False` → truthiness / `not` in `test_google_drive_service.py`.
- **SIM103** (6) — `if cond: return True / return False` → `return cond`; the regex
  `.search()` cases wrapped in `bool(...)` to keep the `-> bool` return type honest
  (`routers/agents.py` ×4, `routers/agent_helpers/pending_calculation.py`,
  `routers/estimate_helpers/ai_generation.py`).
- **SIM102** (5) — collapsed nested `if`s into a single `and` condition, verified each
  outer `if` contained only the inner one (`routers/agents.py`, `routers/auth.py`,
  `routers/agent_helpers/finalize_result.py`, `services/google_drive_service.py`,
  `agents/estimate/crud_handlers.py`).
- **SIM108** (3) — if/else assignment → ternary (`delegate_create_estimate.py`,
  `services/address_service.py`, `tests/conftest.py`).
- **SIM105** (2) — `try/except: pass` → `contextlib.suppress(...)`, adding a top-level
  `import contextlib` to each (`routers/agent_helpers/delegate_get_estimate.py`,
  `scripts/setup_stripe_webhook.py`).
- **C416** (1) — redundant list comp → `list(_STATUS_ALIASES.items())` (`crud_helpers.py`).
- **C401** (1) — `set(gen)` → set comprehension (`work_item_field_handlers.py`).
- **C408** (3) — `dict(...)` → literal (`template_estimate.py` ×2, `tests/_cross_resource_fakes.py`).
- **B007** (2) — unused loop var `i` → `_` (`services/google_drive_service.py`).

Verified: `./run_mypy.sh agents routers services` clean (140 files); `compileall` clean;
458 related tests pass across `test_estimate_agent`, `test_estimate_api`,
`test_orchestrator_endpoint`, `test_labour_api`, `test_google_drive_service`,
`test_auth_api`, `test_cross_resource_joins`, `test_address_service`,
`test_agent_helpers_pending_calculation`, `test_estimate_snapshot_helpers`,
`test_job_item_original_profit_margin`, `test_maple_work_item_ops`. Remaining backlog
(390): F401 (282, needs per-import triage), E402 (56), F841 (52) — the case-by-case
slices per the recommended order.

**Progress 2026-06-04 — E402 + F841 slices closed (56 + 52 → 0).**
`./run_ruff.sh --select E402,F841` is clean project-wide; the whole remaining
backlog is now F401 only.

*F841 (52)* — 3 production dead assignments deleted (`services/google_drive_service.py`
unused `table`, `agents/property/service.py` unused `intent`,
`agents/estimate/crud_handlers.py` unused `has_custom_window`). In tests: 43
`agent = XAgent(use_llm=False)` constructions removed (the tests exercise module-level
helpers, not the instance — construction is side-effect-free with `use_llm=False`); 3
`result = asyncio.run(...)` cases kept the call but dropped the unused binding (asserts
read `captured`, not `result`); `fake_est` (immediately reassigned before use) deleted;
`second_owner = create_company_user(...)` kept the side-effecting call, dropped the
binding; `audit_logs_query` (a never-executed lazy Beanie `.find()` for deferred audit
verification) removed along with its now-orphaned `from models import ...` line.

*E402 (56)* — split between config and reorder:
- **`ruff.toml` per-file-ignores** for the two *structural* cases that cannot be
  reordered: `scripts/**/*.py` (operational scripts must `sys.path.insert(project_root)`
  before importing `database`/`models`/`config`) and `models/__init__.py` (interleaves
  `model_rebuild()` between import groups so Beanie/Pydantic forward refs resolve in
  dependency order). Cleared 33 findings.
- **Reorders** for the rest: moved the `logger = logging.getLogger(__name__)` assignment
  below the import block in `agents/orchestrator/service.py` (11); hoisted `import logging`
  + `from pymongo.errors import DuplicateKeyError` to the top of `routers/agents.py` (2);
  lifted co-located imports to the top in `tests/test_agents_api.py` (2),
  `tests/test_template_create_routing.py` (1), `tests/test_agent_helpers_text_predicates.py` (1).
- **Misplaced-noqa fix** in `agents/estimate/service.py` — the `# noqa: E402` sat on the
  continuation line; moved it to the `from ... import (` statement line so ruff honors it.

Verified: `./run_mypy.sh` clean on the 6 touched production files; full-project
`./run_ruff.sh` reports **281 F401 and nothing else**; 436 related tests pass across
`test_agents_api`, `test_audit_integration`, `test_user_api`, `test_estimate_agent`,
`test_contact_agent`, `test_property_agent`, `test_labour_agent`, `test_equipment_agent`,
`test_template_create_routing`, `test_agent_helpers_text_predicates`,
`test_google_drive_service`. Next and final slice: F401 (281) — the per-import triage.

---

## How to work through this

1. Pick ONE HIGH item per work session. Don't batch.
2. Write the failing test first (TDD per `CLAUDE.md`).
3. Run the related test file, not the full suite.
4. Commit each item as its own PR — easier to revert, easier to review.
5. Delete the bullet from this file in the same PR.

When this file is empty, delete it.
