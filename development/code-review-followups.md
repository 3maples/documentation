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

## Closed — archived

The 106 resolved/closed items previously tracked inline here were moved to
[`code-review-followups-archive.md`](code-review-followups-archive.md) on
2026-06-13 to keep this tracker scannable (it had grown past 400 KB). Numbering
is preserved there for cross-references.

**When you close an item:** mark it RESOLVED in place in the live list above,
then relocate it to the archive in the next cleanup pass.

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

### 323. [RESOLVED 2026-06-04] ruff manual backlog — fully cleared; `platform/` is at zero ruff errors
Snapshot 2026-06-03 (`./run_ruff.sh`); **B904 slice closed 2026-06-03** (32 → 0);
**style/simplify slice (E741/E712/SIM/C4/B007) closed 2026-06-04** (52 → 0);
**E402 + F841 slices closed 2026-06-04** (56 + 52 → 0);
**F401 slice closed 2026-06-04** (281 → 0). `./run_ruff.sh` is now clean
project-wide — ruff is a fully-enforced zero-error gate, same as mypy.

| Rule | Count | Category | Notes |
|---|---|---|---|
| ~~**B904** raise-without-`from`~~ | ~~32~~ → **0** | correctness | **RESOLVED 2026-06-03** — see progress note below |
| ~~F401 unused-import~~ | ~~281~~ → **0** | dead code | **RESOLVED 2026-06-04** — see progress note below |
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

**Progress 2026-06-04 — F401 slice closed (281 → 0). Backlog fully cleared.**
`./run_ruff.sh` is now clean project-wide across all 317 files. The per-import
triage was done with a classifier (built ad-hoc) that scans the whole repo for
each unused name and labels it **DEAD** (referenced nowhere outside its own
module), **REEXPORT** (another module does `from <mod> import <name>` or
`<alias>.<name>`), or **MONKEYPATCH** (a test does `setattr(<mod-alias>, "<name>", …)`).

- **Mechanized the safe deletion.** Protected every REEXPORT/MONKEYPATCH name
  with an inline `# noqa: F401  # <reason>`, then ran
  `ruff check --select F401 --fix --extend-fixable F401` (the `--extend-fixable`
  overrides `ruff.toml`'s `unfixable = ["F401"]` *for that one run*). ruff then
  removed only the genuinely-unused imports — including the multi-line paren-block
  surgery — and left the noqa-protected names untouched. Followed by
  `--select I --fix` to re-sort the import blocks. **174 dead imports removed.**
- **Biggest hubs:** `agents/estimate/service.py` (90: 87 dead leftovers from the
  service-split, +`ChatOpenAI` monkeypatch, +`ArchitectScope`/`DecomposedRequirement`
  re-exports kept), `routers/agents.py` (42), `routers/estimates.py` (27 — a
  documented re-export facade; kept the 8 consumed re-exports/monkeypatch targets,
  deleted the 19 nothing consumes). `__init__.py` files were already F401-exempt,
  so package re-exports were never at risk.
- **Caught a classifier gap with the test suite.** Two monkeypatch targets on
  `routers.agents` (`estimates_api_get_estimate`, `estimates_api_get_estimates`,
  aliased imports patched via `setattr(agents_router, …)`) were mis-labeled DEAD and
  removed; the orchestrator endpoint tests failed with `AttributeError: module
  routers.agents has no attribute …`. Restored both with `# noqa: F401`. An
  AST-based re-scan of every modified module then confirmed **0** remaining
  test-accessed attributes were missing.

Verified: full-project `./run_ruff.sh` clean (0 findings); `./run_mypy.sh` clean
(317 files); `pytest --collect-only` clean (no import errors across 2874 tests);
**full suite 2874 passed, 0 failures**.

> **#323 is RESOLVED.** With B904 + style/simplify + E402 + F841 + F401 all closed,
> `platform/` sits at zero ruff errors. ruff is now a fully-enforced gate (like
> mypy): any new `./run_ruff.sh` finding in a PR is a regression to fix in-place,
> not backlog. The legacy-backlog scoping caveat in CLAUDE.md's baseline note is no
> longer needed — `./run_ruff.sh` can be run project-wide without tripping over
> pre-existing findings.

---

## 2026-06-05 `/code-review` pass (Maple Spanish translation sandwich)

Backend-only change: input→English / output→Spanish translation boundary
(`services/translation.py`), dialect-aware prompts, and defense-in-depth Spanish
keywords in the guards/helpers. HIGH (`_estimate_status_from_text` length) and
all MEDIUMs were fixed in the same change. These two LOWs were deferred.

### 324. [LOW] Language codes `"en"` / `"es"` are bare string literals
`services/translation.py` and the two endpoint handlers (`routers/agents.py`,
`routers/public_maple.py`) compare against `"en"` / `"es"` inline in several
branches. `SUPPORTED_TARGET_LANGS` already centralizes the supported set; a
small `LANG_EN = "en"` constant (or an enum) would remove the remaining magic
strings and make adding a language a touch safer. Cosmetic — no behavior change.

### 325. [LOW] `sacá …todos` can false-positive the fail-open bulk-delete net
`_BULK_DELETE_PATTERNS` in `agents/text_utils.py` now matches `saca/sacá`
(remove/take-out) + an all/every quantifier, so a phrasing like "sacá una foto
de todos" (take a photo of everyone) would trip the bulk-delete refusal. Only
reachable on the rare translation-fail-open path (the happy path translates to
English first), and the guard is conservative (quantifier required), so impact
is minimal. Drop `saca/sacá` if real-world noise appears, or tighten to require
a record-noun nearby.

> Not logged (duplicate): the `orchestrate_agent_endpoint` / `routers/agents.py`
> God-handler + file-size concern is already tracked by #238, #257, and the #4
> file-size cluster. This change added ~20 lines to that pre-existing handler.

---

## 2026-06-06 `/code-review` pass (Maple estimate field edits + router-path fix)

Reviewed the session range `11b22ef..5bace30` (8 commits, 13 files): estimate-level
description/notes/link sub-ops, shared title-or-code resolver, enriched details
(agent + `delegate_get_estimate`), the generic optional-follow-up one-turn
shortcut, and the router delegation predicate fix. Gates were zero (ruff, mypy)
and ~700 related tests green at review time; both HIGHs are structural, not
correctness/security. CRITICAL: 0.

### 326. [HIGH] `handle_pending_optional_follow_up` is 259 lines with a duplicated delegation block
`routers/agent_helpers/optional_follow_up.py` — the new one-turn confirm+value
shortcut hand-rolls a ~40-line processor-delegation + envelope that near-copies
the two-turn path at the bottom of the same function. The shortcut deliberately
omits `accuracy_suggestions` / `missing_fields` propagation (commented), but two
envelope assemblies in one 259-line function WILL drift, and this is the shared
state machine for ALL agents' follow-ups. Fix: extract a
`_delegate_synthetic(pending, synthetic_message, processor_factory, context, *,
propagate_extras)` helper used by both paths; behavior is pinned by the existing
`test_agent_helpers_optional_follow_up.py` + `TestEstimateFollowUpConfirmStage`
tests, so this is a pure refactor. Fold #335 into the same pass.

### 327. [HIGH] `agents/estimate/crud_handlers.py` grew ~250 lines to 2,309
Pre-existing giant (under the #4 file-size theme) but this change materially
worsened it: the mixin now holds link/notes/description detectors + handlers,
bare-title extraction, the shared resolver, and the get/update dispatchers.
Next touch, split the estimate-level field-edit sub-ops (description / notes /
property-link detectors + handlers) into an `estimate_field_handlers.py` mixin,
mirroring the existing `work_item_field_handlers.py` precedent from §1.5.

### 328. [MEDIUM] `_resolve_estimate_by_title` full-collection scan now on three more paths
The (pre-existing) resolver does `Estimate.find(company == oid).to_list()` and
substring-matches titles in Python. The new `_resolve_estimate_code_or_title`
wires it into notes/description/link updates, so every code-less update turn
loads ALL of a tenant's estimates. Single company-scoped query (not N+1) and
fine at typical tenant sizes, but unbounded. Fix: add a `.limit(...)` bound or
a server-side case-insensitive regex match on `title`; `company` is already the
indexed filter per the `Settings.indexes` convention.

### 329. [MEDIUM] "Please don't" is consumed as a property value by the one-turn shortcut
`optional_follow_up.py` — `please` is in `_AFFIRMATION_PREFIX` and `don't` is
not in the exact-match `_NEGATIVE_VALUES`, so a "Please don't" reply at the
confirm stage delegates a property lookup for the literal value "don't" (fails
gracefully → re-prompt, but reads badly). Same family as the §9.4-documented
soft-negative gap (`not right now`, `I'll do it from the portal`, `nah, leave
it`). Fix once for both: check the post-affirmation residual against a
soft-negative list (`don't`, `do not`, `never mind`, `not right now`, …) before
treating it as a value, or extend `_NEGATIVE_VALUES` prefix-matching.

### 330. [MEDIUM] `target.save()` unwrapped in `_handle_update_estimate_description`
The new description handler follows the notes handler's bare-save precedent,
but the property-link handler in the same file wraps its save in try/except
with a friendly "couldn't reach the database" envelope — the file has two
precedents and the new code picked the weaker one. A Mongo hiccup surfaces as a
generic 500 instead of the retry prompt. Fix: wrap like the link path, or
extract a `_save_or_error` helper and use it in all three field-edit handlers.

### 331. [MEDIUM] Twin datetime formatters duplicate the label format
`_fmt_dt` (`agents/estimate/crud_helpers.py`, datetime objects) and
`_fmt_iso_dt` (`routers/agent_helpers/delegate_get_estimate.py`, ISO strings)
are deliberate and cross-referenced in comments, but the format string
`"%Y-%m-%d %H:%M UTC"` is duplicated and will drift. Fix: share the constant
(or one helper accepting both input types) from a neutral module.

### 332. [MEDIUM] Router delegation predicate constructs the EstimateAgent singleton
`routers/agents.py::_should_delegate_update_estimate_to_agent` now calls
`get_estimate_agent().owns_update_sub_op(text)` — first call lazily builds
`ChatOpenAI` (sync constructor, no network; fine in practice). The predicate is
also reached from `_message_breaks_pending_confirmation`, so agent construction
can happen earlier in the request lifecycle than before. No action required;
logged for awareness — if it ever matters, pass the agent in the way
`delegate_update_estimate` already receives it.

### 333. [LOW] `_residual_is_field_restatement` filler-word heuristic is undocumented at the call site
The filler list (`add|set|update|link|the|a|an|it|to|with|please|me|my`) is a
heuristic; values that reduce oddly (a property literally named "My Place"
reduces to "place" and still passes — correct today) deserve a pointer to the
§9.4 soft-negative follow-up so the two heuristics evolve together.

### 334. [LOW] `_TITLE_TAIL_STOP` excludes mid-title connector words
A real title like "Edge of the Garden" won't bare-extract (the tail stops at
"of"); quoted and `called X` forms still work, and the failure mode is the
standard ask-for-code clarification. Documented tradeoff in the phrasing
reference — revisit only if real titles hit it.

### 335. [LOW] One-turn shortcut envelope omits `accuracy_suggestions` / `missing_fields`
Intentional and commented, but it makes the one-turn and two-turn paths return
structurally different envelopes. Resolved automatically by the #326 refactor —
tracked separately so it isn't forgotten if #326 is deferred.

---

## 2026-06-06 `/code-review` pass (Settings materials actions menus + load-standard endpoints)

The HIGH finding from this pass (per-item `count()` loop on unindexed fields in
`remove_non_standard_material_categories/_units`) was fixed in the same session:
batched `get_pymongo_collection().distinct()` + `category` / `sizes.unit`
entries in `models/material.py` `Settings.indexes`. The rest is deferred here.

### 336. [MEDIUM] `load-standard` endpoints duplicate the audit-log loop (~55 lines each)
`routers/material_categories.py::load_standard_material_categories` and
`routers/material_units.py::load_standard_material_units` are verbatim twins
apart from the enum values, and each is marginally over the 50-line guideline
(complexity is low — linear, max 2-level nesting). Fix: extract the
removed-states audit-log loop into a small shared helper (e.g. in
`routers/agent_helpers` or a `routers/_audit_helpers.py`), which also pulls
both handlers under the line guideline.

### 337. [MEDIUM] Materials Categories/Units tabs are twin files, worsened by this change
`portal/src/components/settings/MaterialCategoriesTab.tsx` and
`MaterialUnitsTab.tsx` were already near-identical; the reload state, handler,
and modal added ~110 more duplicated lines each (differing only in wording and
API object). Divergence bugs get likelier each time. Fix: extract a shared
`ResourceCatalogTab` parameterized by labels + API object, the same move that
extracted `ActionsMenu` from `RowActionsMenu`.

### 338. [MEDIUM] `ActionsMenu` has `role="menu"` but no arrow-key navigation
`portal/src/components/common/ActionsMenu.tsx` has correct roles,
`aria-expanded`, and Escape handling, but no ArrowUp/ArrowDown focus movement,
which the ARIA menu pattern implies. Inherited verbatim from `RowActionsMenu`
(not a regression), but `ActionsMenu` is now the shared primitive, so the gap
propagates to every consumer. Fix: one `onKeyDown` handler on the menu div that
cycles focus across `menuitem` buttons.

### 339. [LOW] `load-standard` POSTs have no `response_model`
Both routes return plain summary dicts (`{loaded, removed, skipped_in_use}`),
not documents — no leakage risk, and this matches the `/materials/load-standard`
precedent. Logged only because the repo convention declares `response_model` on
most routes. Fix (optional): a small shared `ReloadResult` Pydantic model;
natural to do together with #336.

### 340. [LOW] `alert()` used for the skipped-in-use report after reload
`MaterialCategoriesTab.tsx` / `MaterialUnitsTab.tsx` surface skipped in-use
items via browser `alert()` — consistent with the tabs' existing error
handling, but the weakest UX in the flow. Fix: inline banner or toast; natural
to do together with #337.

### 341. [LOW] New reload API tests don't wrap cleanup in `try/finally`
The reload tests in `tests/test_material_categories_api.py` /
`test_material_units_api.py` follow the file's existing trailing-`# Cleanup`
convention, so a mid-test assertion failure skips the API cleanup calls.
`conftest`'s by-company teardown backstops it, so this is cosmetic. Fix only if
these files grow: fixture-based cleanup.

### 342. [LOW] Auto-create of missing categories/units has a find-then-insert race
Added 2026-06-07 with the load-standard auto-create change.
`services/material_bootstrap.py::_ensure_referenced_categories_and_units`
checks the pre-loaded name→doc dict, then `await .insert()`s any missing
`MaterialCategory` / `MaterialUnit`. `MaterialCategory`/`MaterialUnit` have a
`(company, ASCENDING)` index but it is **not unique** and not on
`(company, name)`, so two concurrent `load-standard` calls for the same company
could each create the same category/unit → duplicates. This mirrors the
identical race in `routers/materials.py::_find_or_create_category` /
`_find_or_create_unit` (the upload path) — an accepted pattern, and bootstrap is
effectively single-shot (onboarding / one button click), so practical risk is
low. Fix (closes both call sites at once if ever wanted): add a unique
`(company, name)` index to both models and catch `DuplicateKeyError` in the
create helpers.

### 343. [LOW] `bootstrap_company_materials` body is ~67 lines (over the 50-line heuristic)
Added 2026-06-07. The 8-line auto-create wiring pushed
`services/material_bootstrap.py::bootstrap_company_materials` past the 50-line
guideline, though the bulk is docstring + comments and the new logic was already
extracted into `_ensure_referenced_categories_and_units`. Cosmetic only. Fix if
the function grows further: extract the category/unit pre-load and the
group-and-insert loop into named helpers.

## 2026-06-09 `/code-review` pass (estimate title-vs-active-context refactor + status phrasing)

Context: the `_resolve_update_estimate_code` seam refactor — all 7 estimate
UPDATE-path handlers (status, work items, work-item fields, apply-template)
now route through one title-aware resolver so an explicitly-named title
overrides `active_estimate_code`, closing the long-standing latent bug. Plus
expanded status-transition phrasing (`update/transition/switch/put/place` +
bare "on hold"). Gates clean (ruff + mypy), 13 new tests, phrasing-reference
doc synced. No CRITICAL/HIGH defects — all findings are maintainability.

### 344. [MEDIUM] `_handle_update_estimate_apply_template` grew to 97 lines
Added 2026-06-09. `agents/estimate/crud_handlers.py::_handle_update_estimate_apply_template`
(L598) gained ~30 lines for the named-target-vs-bootstrap branching, pushing it
to 97 lines (well over the 50-line heuristic). The three-way branch
(named → resolve-or-refuse / unnamed-no-code → bootstrap from template /
unnamed-with-code → load) is the kind of logic that reads and tests better
extracted. Fix: pull the named-target resolution+refuse block into a small
helper (mirrors the `_resolve_update_estimate_code` seam this change
introduced), leaving the handler to orchestrate the three branches.

### 345. [MEDIUM] `crud_handlers.py` (2,495) and `work_item_field_handlers.py` (1,270) exceed the 800-line guideline
Added 2026-06-09. Extends [#327](#327-agentsestimatecrud_handlerspy-grew-250-lines-to-2309)
— `crud_handlers.py` was 2,309 there and is now 2,495 after this change. The
estimate CRUD mixin keeps accreting; `work_item_field_handlers.py` is also over
at 1,270. Pre-existing, not introduced by this refactor (the change is net
behavior-neutral plumbing), but worsened. Fix (large, defer until the area is
actively reworked): split the estimate handler mixins by sub-domain —
list/analytics vs. get/update vs. work-items — into separate modules.

### 346. [LOW] Redundant double resolution in `apply_template`
Added 2026-06-09. `agents/estimate/crud_handlers.py` (~L631): computing
`names_target` calls `_resolve_estimate_code(query, None)` and
`_query_names_estimate_title(query)`, then the subsequent
`_resolve_estimate_code_or_title(...)` re-runs both internally. Regex-only
cost, so negligible, but it duplicates the precedence intent. Fix (optional):
`_resolve_estimate_code_or_title` already encodes the full precedence, so the
`names_target` pre-check could be folded into how its `(code, clarify)` return
is interpreted rather than pre-resolving.

## 2026-06-09 Any-language translation sandwich (note — supersedes earlier Spanish-only references)

Context: Maple's translation sandwich was generalized from Spanish-only to an
open language set. `services/translation.py` now exposes `prefilter_language`
(heuristic, any script) + `detect_and_translate_to_english` (one combined
worker-model call returning `{lang, english}`); `SUPPORTED_TARGET_LANGS`,
`detect_language`, and `translate_to_english` were removed. **Failure policy
changed: inbound translation now FAILS CLOSED** (canned
`translation_unavailable_message` instead of processing raw foreign text);
outbound still fails open. Any earlier entry describing inbound translation as
"fails open" is superseded. The Spanish keyword guards in
`agents/text_utils.py` / `crud_helpers.py` remain as the safety net for
pre-filter misses. Plan:
`documentation/development/plans/2026-06-09-maple-any-language-translation.md`.

## 2026-06-11 `/code-review` pass (Maple status transitions: state machine + authorization + locked-status edits)

Context: chat-side enforcement of the estimate status state machine
(`validate_estimate_status_transition`), the HTTP layer's role gates
(send/unsend → Owner/Admin; archive/unarchive → Owner/Admin or creator,
identity via `current_user_email`/`current_user_role` context keys set by the
orchestrate endpoint, fail-closed), and the locked-status edit guard in
`_load_estimate_for_update` (Archived / Sent / legacy Approved). Gates clean
(ruff + mypy), 492 tests passing across the related suites. The pass's HIGH
(handler length) and two MEDIUMs (role magic strings; identity keys persisted
to `conversation_contexts`) were fixed in the same change — handler is back to
153 lines via `_refuse_illegal_status_transition` /
`_authorize_status_transition` extraction, roles compare against
`_ELEVATED_ROLES` derived from `UserRole`, and `finalize_result.py` strips the
per-request identity keys before persisting. The two remaining findings:

### 347. [MEDIUM] `crud_handlers.py` now 2,724 lines — extends #345
Added 2026-06-11. Extends [#345](#345-medium-crud_handlerspy-2495-and-work_item_field_handlerspy-1270-exceed-the-800-line-guideline)
— 2,495 there, 2,724 after the status-transition enforcement work (+229 across
the two 2026-06-11 changes). Same fix, same deferral: split the estimate
handler mixins by sub-domain when the area is next actively reworked. The new
`_refuse_illegal_status_transition` / `_authorize_status_transition` /
`_load_estimate_for_update`-guard cluster is a ready-made seed for a
`status_policy.py` (or similar) module in that split.

### 348. [LOW] Defensive `'Sent'` fallback in `_authorize_status_transition` is logically unreachable
Added 2026-06-11. `agents/estimate/crud_handlers.py::_authorize_status_transition`:
in the `involves_sent and not is_owner_or_admin` refusal, the
`current_status.value if current_status else 'Sent'` else-branch can't be hit —
when `target_status` isn't Sent-like, `involves_sent` can only be True via
`current_status`, so it can't be `None` there. Kept deliberately because
`current_status` is typed `Optional[EstimateStatus]` and mypy requires the
guard (an inline comment marks it typing-only). Fix (optional): narrow the
parameter type instead, e.g. split the gate so the unsend branch receives a
non-Optional `EstimateStatus`. Not worth doing on its own — fold into #347's
split if that happens.

## 2026-06-12 (UI/Maple edit-lock alignment)

Context: Maple's chat edit guard was tightened from the PUT route's lock
(Sent/Approved/Archived) to the portal's `isEditableStatus` rule — contents
editable only in Draft or Review (`_EDITABLE_ESTIMATE_STATUSES` allowlist in
`agents/estimate/crud_handlers.py`). UI and chat now agree; the API does not:

### 349. [MEDIUM] PUT `/estimates/{id}` allows content edits in statuses the UI and Maple treat as read-only
Added 2026-06-12. `routers/estimates.py` (PUT handler, ~L820): the route locks
Archived and Sent/legacy-Approved, but still accepts content updates (notes,
job_items, property, …) for Won / On Hold / Lost / Scheduled / Completed —
statuses the portal renders read-only (`isEditableStatus`: Draft/Review only)
and Maple now refuses to edit. Any direct API caller (integration, script,
future mobile client) can bypass the editing rule the product presents as
truth. Fix: add the same Draft/Review allowlist to the PUT route's lock block
(keeping the existing unsend exception for status-only changes), mirroring the
`_EDITABLE_ESTIMATE_STATUSES` constant — or, better, move the allowlist next to
`ESTIMATE_STATUS_TRANSITIONS` in `models/estimate.py` so model, route, and
agent share one definition. Coordinate with the FE before shipping: confirm no
portal flow PUTs content for non-Draft/Review estimates (e.g. auto-save firing
on a just-transitioned estimate).

---

## 2026-06-15 deferred from /code-review

Logged by `/fix-issues` — findings from the latest review (Maple status-transition
routing + help answer-then-offer) not fixed in that pass. Selection fixed #1, #2,
#3, #5; #4 deferred here because the fix is much larger than the finding describes.

### [LOW] platform/agents/orchestrator/service.py:~1858 — status offer made without pre-validating legality/role
`_maybe_attach_status_offer` offers "Yes — I can set {EST} to {Y}…" whenever an
EST-code + recognized target status is present, without checking the estimate's
current status or the user's role. A Member, or a request for an illegal edge, is
still offered the action and only refused after they say "yes". The copy is hedged
("as long as that's an allowed next step from its current status"), so this is a UX
nuance, not a correctness bug — the execution path enforces the state machine and
role gate correctly on confirmation.
**Suggested fix:** Pre-validate at offer time: load the estimate, run
`validate_estimate_status_transition` + the role/creator gates, and if the
transition would be refused, return that refusal as the help answer instead of an
offer. NOTE this is deliberately deferred — it requires making the (currently
sync) help-lane offer path async and duplicating the state-machine/role checks the
agent already performs on "yes". Only worth doing if the optimistic offer proves
confusing in practice.

### [INFO] tooling / regex — not actionable now
- `bandit` is not installed in `platform/.venv`, so the Step-3 security scan was
  skipped during review. `pip install bandit` (or add to dev requirements) to
  enable `bandit -r . -x tests/`. Manual review found no injection/secrets in the
  change.
- `_STATUS_TRANSITION_STATUS_REF_TO_PATTERN` (`agents/estimate/text_helpers.py`)
  was checked for ReDoS: single lazy span on short chat input → ~O(n²) worst case,
  not exponential; consistent with the existing `_STATUS_TRANSITION_*` patterns. No
  action needed — recorded because this repo has a history of ReDoS findings.

---

## 2026-06-15 deferred from /code-review (portal orchestratorReply clarification merge)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass
(selection: none). All LOW / optional polish on the clarification-merge change.

### [LOW] portal/src/lib/orchestratorReply.ts:39 — formatOrchestratorReply is now ~54 lines (just over the 50-line guideline)
The added clarification-merge block pushes the function just past the 50-line
guideline. It's still linear guard-clauses + a doc comment, so it reads fine, but
the merge logic is a self-contained unit.
**Suggested fix:** Optional — extract the needs_clarification block into a small
pure helper, e.g. `mergeClarification(response, question): string`, and call it
from formatOrchestratorReply. Improves readability and lets the merge/dedup be
unit-tested directly.

### [LOW] portal/src/lib/orchestratorReply.ts:80 — combine can stack two questions on distinct question-bearing refusals
When `response` and `clarifying_question` are distinct and neither contains the
other, the result is `${response}\n\n${question}`. For the illegal-status-transition
refusal — whose `response` already ends in its own question ("…want me to do one of
those instead?") and whose `clarifying_question` is "Which status would you like
instead?" — the reply shows two stacked questions. Cosmetic; context is preserved
(the point of the change), and it's a deliberate, documented tradeoff.
**Suggested fix:** Acceptable as-is. If the doubling reads poorly in practice,
refine backend-side (drop the redundant clarifying_question on flows whose
`response` is already self-contained) rather than adding heuristics in the portal.

### [LOW] portal/src/lib/orchestratorReply.ts:74 — substring dedup could over-collapse a degenerate short question
`context.includes(question)` / `question.includes(context)` dedup on raw substring.
If a `clarifying_question` were a short fragment that happens to appear mid-sentence
in `response` (e.g. question "name" inside "Add a name."), the shorter field is
dropped. In practice clarifying_question is always a full prompt sentence, so the
risk is negligible.
**Suggested fix:** Acceptable as-is. If hardening is wanted, compare on a
sentence/boundary basis or only dedup when one string fully equals a trimmed line
of the other. Not worth the complexity now.

---

## 2026-06-16 deferred from /code-review (calculator registry refactor + new calcs)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [LOW] platform/agents/calculator/text_helpers.py:195 — calculation_type string literals spread into a third location
"aggregate_tons"/"mulch_bags" are now hardcoded in `text_helpers` in addition to the
schema `Literal` and the registry keys (the Magic Strings smell). Risk is low — the
`Literal` type makes a typo a mypy error and the registry drift test guards
schema↔registry — but the values now live in three files.
**Suggested fix:** Acceptable as-is given the tooling guards. If the set keeps
growing, promote `calculation_type` to a shared `StrEnum` referenced by the schema,
the registry, and `text_helpers` so there is one source of truth.

---

## 2026-06-17 deferred from /code-review (batch materials/labour load-standard bootstrap)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [MEDIUM] platform/services/material_bootstrap.py:179 — bootstrap_company_materials exceeds the 50-line guideline
After adding the preload + partition + insert_many, the function is ~63 code lines and
now juggles several responsibilities (resolve company id, load templates, preload
categories, preload units, auto-create missing cats/units, group rows, preload existing
materials, partition into update/insert, batched write). It's cohesive and readable, but
crosses the review rubric's 50-line threshold and is getting hard to scan.
**Suggested fix:** Extract the per-material partition loop (resolve → update-existing vs
collect-to-insert) into a small private helper, e.g. `_partition_materials(grouped,
existing_by_name, categories, units, company_id, result) -> list[Material]`. Pure
mechanical extraction, no behavior change.

### [LOW] platform/services/company_bootstrap.py:68 — (name, unit) lookup key assumes canonical unit casing
`existing_by_key` is keyed by `(doc.name, doc.unit)` where `doc.unit` is the LabourUnit
str-enum, and looked up with the template's raw `unit` string. It works today only because
default_labours.csv uses exactly "Hourly" (verified). If a future seed row used an
alias/lowercase unit ("hour"), the key would miss on rerun and insert a DUPLICATE role
instead of overwriting. The legacy find_one had the same latent gap, so this is not a
regression — but the in-memory key makes the casing assumption implicit.
**Suggested fix:** Normalize the template unit when building/looking up the key, e.g. key
on `LabourUnit.from_string(template["unit"])` on both sides, so alias/case variants resolve
to the same enum. (Or assert the seed CSV uses canonical unit values.)

### [LOW] platform/services/material_bootstrap.py — insert_many is non-atomic on partial failure
`Material.insert_many(to_insert)` (and the labour equivalent) isn't transactional. A
mid-batch failure (e.g. a duplicate-key race, validation) leaves some rows inserted, then
raises up to the load-standard router as a 502 with `created` never set. The pre-existing
one-insert-per-row loop had the same partial-state shape, so this isn't a regression, just
worth being aware of now that it's a single bulk call.
**Suggested fix:** Optional. If atomicity matters, wrap the bulk writes in a Motor
transaction (the atlas-local replica set supports them), or pass `ordered=False` and
surface a partial "imported N of M" result instead of a bare 502.

---

## 2026-06-19 deferred from /code-review (onboarding back-to-Company edit)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [LOW] portal/src/pages/OnboardingPage.tsx:140 — back-nav wiring isn't covered by a test
The new `onBack={() => goToStep(1)}` on the Contacts step and the
`companyId`/`onCompanyUpdated` props are untested at the page level. The meaningful logic
(create-vs-update, prefill) is covered in `CompanyStepEdit.test.tsx`; this is just one-line
glue, but the navigation contract has no regression guard.
**Suggested fix:** Optional — `OnboardingPage` needs firebase mocking to render (no existing
pattern), so low-value to test directly. Acceptable to leave given the branch logic is
covered.

---

## 2026-06-19 deferred from /code-review (onboarding CompletionStep restyle)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [LOW] portal/src/components/onboarding/CompletionStep.tsx:16 — decorative sparkle icon lacks aria-hidden
The `<Sparkles>` icon is purely decorative but has no `aria-hidden="true"`. Lucide renders a
bare `<svg>` with no accessible name, so screen readers already skip it (hence LOW), and it
matches the existing inline-icon pattern across the codebase.
**Suggested fix:** Optionally add `aria-hidden="true"` for explicitness. Skip if you'd rather
stay consistent with the rest of the codebase, which omits it on decorative icons.

---

## 2026-06-20 deferred from /code-review (estimate role-catalog injection)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [MEDIUM] platform/prompts/role_catalog.py:55 — company-editable role text reaches the LLM prompt unsanitized for instruction-injection
`render_labour_role_catalog` renders Labour `name` + `description` (company-editable) into both
estimate prompts. Names are hardened (control-char/length drop) and descriptions are
whitespace-collapsed + truncated, but description content is not scrubbed for injection text. A
company user could embed "ignore previous instructions…" in a role description. Bounded:
same-tenant only, and parity with the pre-existing injection of `available_labour` /
`available_materials` / `unit_names` into the same prompts (this widens an existing surface, not
a new trust boundary).
**Suggested fix:** Acceptable to ship given tenant ownership + parity. For defense-in-depth, add
a light injection scrub in the renderer or a system-prompt reminder that catalog text is data,
not instructions. Not a blocker.

### [LOW] platform/agents/estimate/llm_pipeline.py:951 — pre-existing print(formatted_prompt) now dumps role descriptions to stdout
`_extract_estimate_with_llm` prints the full prompt (pre-existing debug code, not in this diff).
This change enlarges what it dumps (role responsibility text). Not PII, but noisy debug output
in a production path.
**Suggested fix:** Out of scope here; downgrade `print(...)` → `logger.debug(...)` when next
touching this file.

### [LOW] platform/prompts/role_catalog.py — role resolution now leans on LLM prompt-adherence (conscious tradeoff)
Activity-role correctness now depends on the model honoring "pick from the catalog." Intended
design (live smokes confirm it works); deterministic `_resolve_labour_inventory_match` remains
as fallback, so not Prompt Entanglement. Flagged only for record: prompt drift could regress
role matching, which the prompt tests (wiring-only) won't catch.
**Suggested fix:** None required. Consider a periodic live role-matching smoke if this path
becomes critical.

---

## 2026-06-20 deferred from /code-review

Logged by `/fix-issues` — findings from the orchestrator intent-first review not fixed in that
pass (selection was `1, 3, 4`).

### [HIGH] platform/agents/orchestrator/service.py:2508 — process() is a ~245-line god-method
process() already exceeded the 50-line threshold; the intent-first change adds another inline
fast-path block, worsening it. Pre-existing structural smell — not a defect in the new logic
(the block mirrors the existing inline pre-checks). The DRY extraction in review-#3 (now applied,
`_build_rule_match_result`) trims the duplicated dicts but does not shorten the method's branch
count materially.
**Suggested fix:** Decompose process()'s deterministic pre-check sequence into a table-driven
dispatch (ordered list of `(matcher, builder)` pairs iterated in one loop) so each new pre-check
is data, not another inline `if` block. Not a blocker on its own.

### [LOW] platform/agents/orchestrator/service.py:2657 — `_classify_specific_phrasings` evaluated twice on the LLM-reconciliation path
When the pre-LLM fast-path returns None, the LLM runs, then `_prefer_explicit_rule_match` →
`_classify_with_rules` → `_match_unambiguous_command` re-invokes `_classify_specific_phrasings`.
Same regexes run twice per ambiguous message. Cheap (regex only), no correctness impact.
**Suggested fix:** If optimizing, reuse the pre-LLM rule classification in reconciliation instead
of recomputing it.

---

## 2026-06-20 deferred from /code-review (Finance-page InfoTooltip)

Logged by `/fix-issues` — findings from the Finance-page tooltip review not fixed in that pass
(selection was `1`; #1 viewport-edge clipping was fixed).

### [LOW] portal/src/components/settings/FinancialTab.tsx:44 — field descriptions duplicated from users_guide.md
The six tooltip description strings are copied from the platform glossary
(`platform/user_guides/users_guide.md` lines 718-725). Two sources of truth can drift — a guide
edit won't propagate to the UI. The frontend can't import the backend markdown, so this is a
conscious tradeoff, not a bug.
**Suggested fix:** No action needed now. If these multiply, consider a shared copy module or
surfacing them from an API. Note kept so a future guide edit remembers to update the UI strings too.

### [LOW] portal/src/components/ui/InfoTooltip.tsx:92 — info button tap target is 16x16px
The trigger is `h-4 w-4` (16px), below the ~44px recommended touch target. Fine for a secondary
info affordance, but slightly fiddly on touch.
**Suggested fix:** Optional — add padding (e.g. `p-1` with `-m-1` to preserve visual size) to
enlarge the hit area without changing the icon's appearance.

---

## 2026-06-20 deferred from /code-review (InfoTooltip portal rewrite)

Logged by `/fix-issues` — findings from the InfoTooltip portal/clamp/fade review (selection was
`none`). The 16px tap-target finding from this review is the same one already tracked above
(2026-06-20 Finance-page InfoTooltip) — not re-logged to avoid a duplicate.

### [LOW] portal/src/components/ui/InfoTooltip.tsx:78 — position clamped horizontally but not vertically
The portaled bubble always opens below the trigger (`top = triggerRect.bottom + 6`) and clamps only
`left` to the viewport width. A field near the bottom of a short viewport can push the tooltip off
the bottom edge — there is no flip-to-above or bottom clamp. Low impact: the Financial fields sit
high in the card and the bubble is short, so it's unlikely in practice.
**Suggested fix:** Optional — if the bubble would exceed `innerHeight - margin`, flip above the
trigger (`top = triggerRect.top - bubbleHeight - gap`), or accept it (closing on scroll already
limits the stale-position window).

---

## 2026-06-21 deferred from /code-review

Logged by `/fix-issues` — findings from the latest review (numeric time windows for Maple headline metrics) not fixed in that pass. #1 (OverflowError → 500) was fixed in the same pass via a 1-year clamp.

### [LOW] platform/agents/estimate/crud_handlers.py:1635 — canonical-span constants duplicated across two files
The `named` dict keys {7, 30, 91, 365} in `_describe_date_window` mirror `days_per_unit` in `text_helpers.py` and must stay in lockstep. If `quarter` were ever retuned to 90 in the parser, the label would silently stop matching and fall back to "in the last 90 days". Latent drift coupling, not a current bug.
**Suggested fix:** Acceptable as-is given the small surface; optionally derive both from one shared constant if these spans are touched again.

### [LOW] platform/agents/estimate/text_helpers.py:589 — `_parse_estimate_date_filter` docstring not updated for numeric windows
The docstring still enumerates only word-form phrasings ("from last week" / "this month" / "in the past year") and says it returns `None` "when no recognized qualifier appears" — it now also handles numeric windows ("last 90 days", "past 6 months"). The inline comment above the new regex documents it, but the function-level docstring is the public contract.
**Suggested fix:** Add one line noting numeric windows are also recognized (and capped at one year).

---

## 2026-06-21 deferred from /code-review (PYTHON-J per-segment outbound translation)

Logged by `/fix-issues` — findings from the review of the PYTHON-J fix (per-segment outbound translation in `services/translation.py`) not fixed in that pass. #2 (distinct clarifying_question test gap) was fixed in the same pass.

### [LOW] platform/services/translation.py:712 — unbounded concurrency in `asyncio.gather`
One LLM call is fired per segment with no concurrency cap. In practice `suggestions` is a small fixed UI set (~3-4 chips) so fan-out is caller-bounded, but there is no structural guard; a future caller passing a large `suggestions` list would launch that many simultaneous LLM calls (rate-limit / burst-cost risk).
**Suggested fix:** Optional — bound it with a `Semaphore` or cap the number of translated chips if suggestion counts could ever grow. Not needed at current call sites.

### [LOW] platform/services/translation.py:661 — `translate_response_bundle` length (~69 lines incl. docstring)
By the mechanical >50-line rule the function is long. Mitigating context: the executable body is ~30 linear, branch-light lines, and this change reduced the function from ~90 lines (removed the batch/fallback block). Readability is fine.
**Suggested fix:** None required. The segment-build block could be extracted to a helper if it grows.

---

## 2026-06-21 deferred from /code-review (default-templates bootstrap + Settings responsiveness)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass. #1 (`_build_template` length) and #2 (date_range recurrence test) were fixed in the same pass.

### [LOW] platform/services/template_bootstrap.py:241 — duplicate catalog names collapse silently (last-wins)
`materials_by_name` / `labours_by_name` are dict comprehensions keyed by name. Material has a non-unique (company, name) index, so two same-name rows silently keep only the last — resolution could bind to an unexpected size/price with no signal.
**Suggested fix:** Optional — log a warning when a name maps to >1 catalog doc.

### [LOW] platform/services/template_bootstrap.py:152 — size label kept when requested size doesn't match
When `size_str` is provided but matches no `MaterialSizeCost`, `_resolve_material_size` falls back to the first size for price/unit, yet the item stores the original `size_str`. Result: a line item whose size label and price/unit can disagree. (No current template hits this — all sizes match.)
**Suggested fix:** Store `size.size` (the resolved label), or route a non-matching size to `unmatched_materials`. Document the chosen behavior in the helper docstring.

### [LOW] portal/src/pages/SettingsPage.tsx:1208 — tablist orientation / keyboard semantics
This change removed `aria-orientation="vertical"`; on the desktop vertical layout that now defaults to `horizontal` (minor SR regression), and it cannot be statically correct for both responsive layouts. Separately and pre-existing (unchanged by this diff): the roving `tabIndex={isActive ? 0 : -1}` follows the ARIA tabs pattern but there is no Arrow-key keydown handler, so keyboard users can't move between tabs — only the active tab is reachable via Tab.
**Suggested fix:** If full correctness is wanted, drive `aria-orientation` from a `matchMedia('(min-width:768px)')` state and add an ArrowLeft/Right (and Up/Down) handler that moves focus + selection across `tabs`. Low practical impact today (orientation has no keyboard effect without arrow handling), so acceptable to defer.

---

## 2026-06-22 deferred from /code-review (Settings/Dashboard intros + Work Items two-row layout)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass. #1 (`break-words` on the Work Items description cell) was fixed in the same pass.

### [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1213 — `key={idx}` on a deletable work-item list (pre-existing)
Work items can be deleted, so index keys can cause React to mis-associate row state on removal. Not introduced by this change — the line was only shifted — but it sits in the edited map.
**Suggested fix:** Use a stable id if available (e.g. the work item's own id). Out of scope for the styling change; fold into a follow-up if desired.

### [LOW] portal/src/pages/NewEstimateWithActivityPage.tsx:1211-1279 — narrow two-row layout relies on inline-block flow; needs an eyes-on check
The "Description row 1, meta row 2" result depends on the Description inline-block filling row 1 so the meta cells wrap below. When a description is very short, the meta cells may sit beside it on row 1 (still readable, just not strictly two rows). No correctness impact; purely visual.
**Suggested fix:** Verify across short/long descriptions at a narrow container width. If strict two-row behavior is required, force a break (e.g. `basis-full` on the Description cell under a flex `tr`, or a wrapper element for the meta trio).

---

## 2026-06-23 deferred from /code-review (People page container-query + Unit column removal)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [LOW] portal/src/pages/PeoplePage.tsx:1 — file exceeds 800-line guideline (1128 lines)
The file is over the 800-line HIGH threshold. PRE-EXISTING; this change does not worsen it (net -6 lines). Reported for awareness only.
**Suggested fix:** Out of scope for this change. If addressed later, extract the create/edit Modal form, the CSV-upload Modal, and the card/table row renderers into child components.

---

## 2026-06-23 deferred from /code-review (Role form rename + breakdown tooltips)

Logged by `/fix-issues` — findings from the latest review not fixed in that pass.

### [LOW] portal/src/pages/PeoplePage.tsx:1 — file exceeds 800 lines (1168 lines)
PeoplePage.tsx is 1168 lines. PRE-EXISTING; the Role-form rename/tooltip change added ~30 lines but did not create the size problem. Reported for awareness only (per the size heuristic).
**Suggested fix:** No action needed for this change. If the page grows further, extract the Role form Modal and the list table into sub-components.

## 2026-06-28 deferred from /code-review (calculator open-math path)

Logged by `/fix-issues` — `/fix-issues all` was requested, but these three were deliberately NOT force-applied because their correct fix would work against the approved design (#2, #3) or is tooling rather than a source change (#4). #1 (raw user message in the open-math exception log → PII risk) WAS fixed in the same pass.

### [LOW] platform/agents/calculator/open_math.py:38 — whole-number rounding enforced only in the prompt
"counts must be whole — wrap in floor/ceil" lives only in `_REASONING_SYSTEM_PROMPT`; neither `safe_eval` nor `format_open_math` enforces it, so a model slip can reproduce the fractional-count bug the feature targets (`_fmt_value` would render "6.67"). This is the residual modeling risk the design spec explicitly accepted (mitigated by the auditable `Working:` line + temperature 0).
**Suggested fix:** A blanket floor is wrong — not every open-math result is a count (areas/weights are legitimately fractional). A correct guard needs count-vs-measurement unit classification or a re-prompt, i.e. a mini-feature, not a one-liner. Accept as documented residual risk unless it recurs in practice.

### [LOW] platform/agents/calculator/service.py:236 — broad `except Exception` can mask genuine bugs
The fail-soft catch is intentional for LLM/parse failures but also swallows programming errors (e.g. a future KeyError) into a silent fallback. Mitigated by `logger.exception` preserving the trace.
**Suggested fix:** Narrowing to specific LLM/validation exception types would let unanticipated error types (OpenAI timeouts, new LangChain exceptions) propagate and 500 the request — contradicting the spec's mandated fail-soft guarantee. Keep the broad catch; the existing `logger.exception` already surfaces masked bugs in logs. No change recommended.

### [LOW] platform/.venv — bandit not installed; automated security scan skipped
The `/code-review` bandit step could not run; only the manual security pass covered the diff. There is no dev-requirements split — adding `bandit` to the single runtime `requirements.txt` would ship a dev-only scanner to production.
**Suggested fix:** Introduce a `requirements-dev.txt` (or a `[project.optional-dependencies] dev` group) and pin `bandit` there, then wire it into the review tooling. Tooling/process task, not a source fix.

---

## How to work through this

1. Pick ONE HIGH item per work session. Don't batch.
2. Write the failing test first (TDD per `CLAUDE.md`).
3. Run the related test file, not the full suite.
4. Commit each item as its own PR — easier to revert, easier to review.
5. Delete the bullet from this file in the same PR.

When this file is empty, delete it.
