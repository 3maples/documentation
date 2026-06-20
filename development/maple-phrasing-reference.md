# Maple Phrasing Reference

Canonical catalog of user phrasings Maple supports, organized by resource. Add new use cases you want Maple to handle; Claude will update the ✅/⚠️ status after wiring the classifier rule or confirming existing behavior.

**Last updated:** 2026-06-20

### Change log

**2026-06-20 — Headline metrics: explanatory routing, dashboard parity, all-time backlog, Won→Completed (§1.9)**
- "How is the Backlog Value calculated?" (and other definitional metric questions) now route to **HELP** instead of returning a dollar figure. `_match_analytics_query` redirects a recognized metric phrased with an explanatory cue to help; `calculated`/`computed` added to `HELP_INSTRUCTIONAL_PATTERNS`.
- Fixed a parity bug: Maple's backlog headline summed only `[WON]` while the dashboard card sums `[WON, SCHEDULED]`, so chat reported $0.00 against a real dashboard figure. `_analytics_headline_value` now includes SCHEDULED. Tests: `tests/test_dashboard_backlog_parity.py`.
- **Backlog relaxed to all-time:** removed the last-30-days recency window from backlog in both `compute_analytics` (dashboard) and `_analytics_headline_value` (Maple). Backlog now sums **every** Won/Scheduled estimate for the company regardless of when it closed; pipeline (90d) is unchanged. Maple's all-time backlog answer reads "… in total"; the dashboard card is relabeled "All time". Guide updated (`users_guide.md` §7.1).
- **Won Value → Completed Value:** retired the "Won Value" headline (Won+Scheduled+Completed, 30d) and replaced it with **Completed Value = `[COMPLETED]` only, last 30 days** across the dashboard card (API field `won_value` → `completed_value`; label "Completed Value"), Maple (`_analytics_headline_value` "completed" metric, answer "Your completed value is … in the last 30 days"; the analytics router recognizes `completed value` / `how much was completed`), and the guide (`users_guide.md` §7.1). The legacy "how much was won?" headline question is retired (parity invariant: chat must mirror the dashboard cards).

**2026-06-15 — Calculator registry refactor + 4 new landscaping calculations (§9.3.1)**
- The Calculator Agent now derives its dispatch table, required-params, type→label map, and the extraction prompt's type list from a single declarative `CalcSpec` registry (`agents/calculator/registry.py`). Adding a calculation is now one formula in `formulas.py` plus one registry entry — the old parallel dicts and `_dispatch()` if-ladder are gone. A drift-guard test (`test_calculator_registry.py`) makes any schema-Literal ↔ registry mismatch a test failure.
- **Five new calculation types, all deterministic:** `aggregate_tons` (gravel/crushed-stone base by weight, cu yd × density), `mulch_bags` (bagged-material count, ÷ bag volume), `retaining_wall_blocks` (courses × blocks-per-course), `step_count` (total rise ÷ riser height), `plant_count` (groundcover grid spacing — square `area ÷ spacing²` or triangular `÷ (spacing² × 0.866)`). All math stays in pure `formulas.py`; the LLM only extracts parameters.
- **Regex fast-path now reads the output-unit signal:** "how many **tons**/**bags** … N sq ft … N inches" routes to `aggregate_tons`/`mulch_bags` instead of silently collapsing to cubic-yard coverage. `steps?` added to the orchestrator pre-classifier's measurement-unit set.
- Tests: `tests/test_calculator_formulas.py` (4 new formula classes), `tests/test_calculator_agent.py::TestAggregateTons`, `tests/test_calculator_registry.py`.

**2026-06-15 — Status transitions route deterministically; status *questions* offer to proceed (§1.4)**
- **Routing fix (the reported bug):** the Orchestrator never routed estimate status changes to `update_estimate` — the rule classifier's estimate field-edit detector only knew description/notes/property, and there was no status branch. So `set the status for {EST} to Sent`, `mark {EST} as Sent`, `archive {EST}`, etc. fell through to `unknown` and (in prod, where the LLM is the primary classifier) routed inconsistently — sometimes a help answer, sometimes "that's not something I can do." Added a **deterministic status-transition lane** in `OrchestratorAgent.process()` (runs before the LLM) plus a branch in `_classify_with_rules`, both gated on an estimate reference and the shared `parse_status_transition` matcher.
- **Word-order gap:** `_detect_status_transition` only matched `status to Y` (adjacent), `to Y status`, or `as Y`, so `set the status for|of|on {EST} to Y` (the estimate code interposed between "status" and "to") was missed. Detection logic moved to a single-source module function `parse_status_transition` in `agents/estimate/text_helpers.py` (shared by the agent and the orchestrator so routable ≡ actionable), and broadened with `_STATUS_TRANSITION_STATUS_REF_TO_PATTERN`.
- **Status *questions* now offer to act (issue #2):** a status request phrased as a question (`Can you set {EST} to Sent?`) is still claimed by the help classifier, but Maple now answers **and offers** to do it (`Yes — I can set {EST} to Sent … Want me to go ahead?`), stashing a `pending_status_transition` record. A following "yes" executes it via `routers/agent_helpers/pending_status_transition.py`; "no" cancels. Only fires when an EST-code and a recognized target status are present.
- **Send-gate message made self-contained:** when a confirmed send is blocked by unresolved missing items, the refusal (`_refuse_send_with_missing_items`) now returns a self-contained statement (`needs_clarification=False`, no `clarifying_question`) instead of the bare, unanswerable question "Would you like to add them to your catalog or dismiss them?" — chat can't resolve missing items (that's a portal-editor action), and the portal renders only `clarifying_question` on clarification turns, so the question previously showed with no antecedent for "them". (The general portal issue — clarification turns dropping the `response` context, which also affects illegal-transition refusals — is tracked separately.)
- Tests: `test_estimates_status_transition_status_ref_to_phrasing`, `test_chat_blocks_sent_while_missing_items_unresolved` (`tests/test_estimate_agent.py`); `test_orchestrator_routes_estimate_status_transition`, `..._is_deterministic_not_llm`, `..._status_question_form_stays_help`, `test_help_status_question_offers_to_proceed_and_sets_pending` (`tests/test_orchestrator_intents.py`); `tests/test_pending_status_transition.py`.

**2026-06-12 — Edit lock tightened to Draft/Review only (§8.7)**
- The locked-status edit guard now mirrors the portal's `isEditableStatus` (`portal/src/lib/estimateStatus.ts`) instead of the PUT route's narrower lock: estimate contents are editable in chat **only in Draft or Review**. Won / On Hold / Lost / Scheduled / Completed (and internal statuses) now refuse edits too, closing the gap where chat could edit a Won estimate's notes while the UI showed it read-only. Allowlist constant: `_EDITABLE_ESTIMATE_STATUSES` in `agents/estimate/crud_handlers.py`.
- Refusals stay persona-voiced; when the state machine offers a one-hop path back (On Hold → Review, Lost → Review) the refusal suggests it ("Ask me to move it to Review first"). Archived and Sent/Approved keep their specific copy.
- Note: the HTTP PUT route still only locks Sent/Approved/Archived — tracked as a follow-up (#349 in code-review-followups.md).
- Tests: `test_locked_estimate_other_statuses_refuse_notes_edit` (Won/Scheduled/Completed), `..._review_reachable_statuses_suggest_review` (On Hold/Lost), `..._won_refuses_work_item_edit`, `test_editable_estimate_notes_edit_still_works` (Draft + Review).

**2026-06-11 (follow-up 2) — Locked-status edit guard (new §8.7)**
- Edits to an **Archived** estimate (any sub-op) and to a **Sent**/legacy **Approved** estimate (any sub-op except the unsend status change) are now refused in chat, mirroring the PUT route's locks ("Cannot update an archived estimate" / "Cannot update a sent estimate"). Enforced once in `_load_estimate_for_update` (`agents/estimate/crud_handlers.py`) — the shared loader behind every edit sub-op: notes, description, property linking, template application, and all work-item operations. Reads are unaffected; the status-transition path has its own rules (state machine + role gates) and is not blocked by this guard.
- Refusals are persona-voiced with the next step: "Ask me to unarchive it first…" / "Ask me to move it back to Draft or Review first…".
- Tests: `test_locked_estimate_archived_refuses_notes_edit`, `..._sent_refuses_notes_edit` (Sent + Approved), `..._sent_refuses_work_item_edit`, `test_draft_estimate_notes_edit_still_works` (`tests/test_estimate_agent.py`).

**2026-06-11 (follow-up) — Status-transition authorization + persona refusals (§1.4, §8.6)**
- The status handler now also enforces the HTTP layer's **role gates**: any transition touching `Sent`/legacy `Approved` (send or unsend) is **Owner/Admin only** (mirrors the PUT role gate); **archive/unarchive** is **Owner/Admin or the estimate's creator** (mirrors the dedicated endpoints' check against `created_by_email`, case-insensitive).
- Identity reaches agents via two new context keys set by the authenticated `/agents/orchestrate` endpoint from the verified user (never the client payload): `current_user_email` (normalized lowercase) and `current_user_role`. Gated operations **fail closed** when identity is missing from context.
- All status-transition refusals (illegal edge, role, creator, missing identity) were rewritten in Maple's persona voice — warm, first-person, apologetic, and always offering the next step ("From Draft I can take it to Archived, On Hold, or Sent — want me to do one of those instead?" / "If you ask an Owner or Admin on your team, they can take care of it for you.").
- Tests: `test_estimates_status_transition_send_unsend_requires_owner_or_admin`, `..._archive_member_non_creator_refused`, `..._archive_member_creator_allowed`, `..._unarchive_member_non_creator_refused`, `..._gated_op_missing_identity_fails_closed`, `..._ungated_op_member_allowed` (`tests/test_estimate_agent.py`); `test_orchestrate_endpoint_passes_user_identity_to_agents` (`tests/test_orchestrator_endpoint.py`).

**2026-06-11 — Status-transition state machine enforced in chat (§1.4, new §8.6)**
- Maple's status handler (`_handle_update_estimate_status_transition` in `agents/estimate/crud_handlers.py`) now calls `validate_estimate_status_transition` from `models/estimate.py` — the same single-source-of-truth state machine the PUT route enforces (#46) and the FE renders (`portal/src/lib/estimateStatus.ts`). Previously chat wrote `status` directly to the DB, so e.g. `mark {EST} as won` succeeded on a Draft estimate.
- Legal edges are unchanged and still save (Draft → Sent/On Hold/Archived; Review → Sent/On Hold/Archived; On Hold → Review; Won → Scheduled/On Hold/Lost; Lost → Review; Scheduled → Completed; Sent/Approved → anything = "unsend"). Illegal edges now refuse with the current status, the rejected target, and the allowed next statuses (🛑 rows in §8.6).
- Tests: `test_estimates_status_transition_blocked_by_state_machine` / `..._allowed_by_state_machine` in `tests/test_estimate_agent.py`.

**2026-06-09 — Social & personality handling (greetings + anthropomorphized questions)**
- **Greetings → new `social` intent (canned, no LLM).** Bare greetings ("hey", "hi maple", "good morning") are caught in the orchestrator (`_detect_policy_short_circuit` via `is_greeting`) and answered instantly from `GREETING_RESPONSES`; suggestion chips come from `_SOCIAL_SUGGESTIONS`. The `social` intent is operation `social`, `read_only` — a separate intent, not a help topic.
- **Personal questions → new `personal` help topic (persona-answered).** Anthropomorphized questions ("how are you?", "what do you look like?", "are we friends?", "are you married?", "are you an AI?") are detected by `is_personal_question` and routed through the existing help path (`HelpHandler.detect_topic` returns `personal`), then answered by the LLM guide responder from Maple's persona thanks to a rule-1 exemption in the guide prompt.
- **New detectors** `is_greeting` / `is_personal_question` in `agents/text_utils.py`; **new persona** `agents/maple_persona.py` (playful deflection for flirty messages, no romantic reciprocation, honest about being an AI, short replies that pivot back to work).
- **Topic-keyed by design** so product-capability phrasings stay in the product lane: "are you able to add contacts?", "can you create an estimate?", "how are you estimating this job?" are explicit negatives → normal help/CRUD, not `personal`.
- New §10.6 (Social & personality) catalogs the greeting and personal-question phrasings.

**2026-06-07 — Note-body quote fix + estimate anaphora persistence (user report: truncated note + "the same estimate" not recognized)**
- **Quoted note/description bodies no longer truncate at an apostrophe.** `_NOTE_WITH_QUOTED_VALUE` and `_ESTIMATE_DESC_QUOTED` used `[^"']+?`, which treated the `'` in `"Contact me if there's any issues"` as the closing quote and captured only `Contact me if there`. Both now share `_QUOTED_VALUE_GROUP` — a matched-quote capture (straight + curly, double + single) whose close-quote is a negated class, so an apostrophe or the other quote type can appear inside the value. Callers coalesce the four branches via `_first_quoted_group`.
- **"the same / that / previous estimate" now resolves after a note edit.** Root cause: estimate note/description/work-item updates return a **flat** result (`{"operation": "update_estimate_notes", "estimate_id": ...}`) with no nested `"estimate"` dict, so `finalize_result._resolve_entity_reference` never set `active_estimate_code` — the next turn had no anaphora anchor and asked "Which estimate?". The resolver now recognizes a flat `estimate_id` (skipping delete ops). Resolution itself already supported anaphora via `active_estimate_code`; the gap was purely that it was never persisted.
- **`previous`/`prior` added to `_LAST_ESTIMATE_PATTERN`** as cold-start fallbacks (mid-conversation they resolve via active context first).
- Tests: `TestNoteQuoteExtraction` + `TestEstimateAnaphora` (field-edits suite); flat-`estimate_id` cases in `test_agent_helpers_finalize_result.py`.

**2026-06-06 (follow-up) — Production router path fixed (user report: "estimate detail is not shown")**
- The morning wave landed in the **agent** handlers, but the production endpoint routes through `routers/agents.py` delegation helpers that were bypassing them in three places, now fixed:
  - `delegate_get_estimate` rendered its own thin summary (code/status/work-items/grand-total only) — it now also carries **Created / Last updated / Description / Notes / ID**, mirroring the agent renderer.
  - `_should_delegate_update_estimate_to_agent` didn't recognize the new description/notes sub-ops and held a **stale copy** of the link patterns — it now defers to the new `EstimateAgent.owns_update_sub_op` (description + notes + link detectors as the single source of truth), so those phrasings reach the agent instead of the add/modify-items flow.
  - Bare-title extraction now accepts **sentence-case titles** ("Spring cleaning") — first word capitalized, 2+ words, tail bounded by a connector stop-list; single trailing capitalized words ("estimate Won") still never capture.
- Lesson encoded in tests: `TestRouterDelegationPredicate` + `TestRouterDelegationIntegration` pin the router→agent delegation for every new sub-op, and the `delegate_get_estimate` tests pin the enriched render using the exact reported phrasing ("show details for the Spring cleaning estimate").

**2026-06-06 — Estimate field edits & follow-up SHIPPED (plan: [plans/maple-estimate-field-edits.md](plans/maple-estimate-field-edits.md))**
- All five 2026-06-05 user-reported items implemented and the corresponding rows flipped ✅ (each remaining ⚠️ was re-verified against the live rule tier on 2026-06-06):
  - **§1.10 description** — new `_detect_estimate_description_update` + `_handle_update_estimate_description` (estimate-level `description`; quoted/colon/unquoted forms; `write-up`/`overview` synonyms). Dispatcher order: work-item → status → description → notes → link → template.
  - **§1.10 notes** — title/anaphora resolution; informal cues `jot`/`FYI`/`remember`/`write down` detected AND routed (orchestrator `_informal_note` value-bearing arm).
  - **§1.6 linking** — relationship phrasings (`tie`/`connect`/`associate`, "is for", "property for this quote"), bare-property-name targets, `link {EST} to {property}` now rule-tier (was 🤖 LLM).
  - **§1.2 details** — `_build_estimate_details_text` renders Created / Last updated / Description / Notes / ID; "show me everything on the {title} quote" works (linked-property NAME still pending an async lookup).
  - **§9.4 follow-up** — Estimate registered in the generic `optional_follow_up` machine; **one-turn** "Yes, link it to Bob Residential"; bare-property answers; legacy `pending_estimate_follow_up` no longer dual-writes and defers to the generic key (the legacy handler swallowing the reply was the root cause of the original report).
- **Cross-cutting:** shared `_resolve_estimate_code_or_title` (code → anaphora → latest → title) used by all update sub-handlers; bare-title extraction `_TITLE_PRE/POST_NOUN_RE` (case-sensitive first word, 2+ words incl. sentence-case tails, ordered before the any-quoted fallback so note bodies aren't mistaken for titles); orchestrator estimate field-edit fast-path in `_classify_specific_phrasings`.
- Tests: `tests/test_maple_estimate_field_edits.py` (57) + additions to `tests/test_agent_helpers_delegate_create_estimate.py`; ~500-test regression sweep green; mypy + ruff project-wide zero.
- Still ⚠️ after this wave (verified, with misroute notes where found): casual detail forms ("rundown", "full info" → misroutes to `get_contact`, "open up"), "when was X created/updated" (the created form misroutes to `create_estimate`), value-before-cue description ("put X as the overview"), `describe … as`, note verbs `make`/`leave`/`tack`, generalized `note … that` tail, "job site" link cue, soft negatives ("not right now", "I'll do it from the portal"), `bid`/`proposal` as title-extraction nouns, and job-name → estimate resolution (Task-8 stretch).

**2026-06-05 — Estimate-level field-edit & details gaps logged (⚠️ for implementation)**
- Five user-reported estimate phrasings reviewed against the live code; new ⚠️ gap rows added for the ones not correctly handled. Root cause shared by three of them: **title-based estimate reference (`_resolve_estimate_by_title`) is wired only into the `get_estimate` path** (`crud_handlers.py:1535`); every *update* sub-handler (`notes` @1891, property `link` @1943, and the not-yet-built description handler) resolves the estimate by **EST-code only** (`_resolve_estimate_code`), so a title like "Spring Cleaning" prompts for a code on the update path.
- **§1.10 (new)** — estimate-level `description` edit is unhandled (model field exists, no dispatcher sub-op → falls through to the `_handle_update_estimate` refusal); estimate-level `notes` append **is** handled rule-side (newly documented) but code-only.
- **§1.2** — title-based details response is too thin: `_build_estimate_details_text` (`crud_helpers.py:446`) emits only Code/Title/Status/Grand total. Missing `created_at`, `updated_at`, linked property, description, notes (all present on the model and in the full result payload, just not rendered).
- **§1.6** — title-referenced property linking ("set the property of estimate {Name} to {property}") is a gap; the link handler fires but can't resolve a titled estimate.
- **§9.4 (new)** — the post-creation "link this to a property now?" follow-up (`extraction_helpers.build_optional_follow_up`) has no pending-intent state, so an affirmative reply ("Yes, link it to Bob Residential") isn't carried back into the linking handler.
- Each of the five sections now carries **landscaper-style variant rows** in its catalog table (informal verbs, customer/job-name references, bare-address properties, value-only notes, confirmation-word-plus-property replies) plus a concise **Implementation note**, so coverage targets the real input distribution, not just the canonical phrasing. Recurring sub-gaps surfaced by the variants: estimate synonyms `bid`/`proposal`, job-name → estimate resolution, possessive property nicknames ("Bob's place"), informal note cues (`jot down`/`FYI`/`remember`), and bare-property affirmatives in the link follow-up.
- Implementation plan written: [`plans/maple-estimate-field-edits.md`](plans/maple-estimate-field-edits.md).

**2026-06-02 — Template-driven estimate creation (skips AI generation) + gathering decline fix**
- A **create-estimate request that names a template** now skips AI generation entirely and instantiates from the template (§1.3, §6.7). No-baseline → template applied as one work item verbatim; baseline (`size`+`unit`) → linear scaling to the job size (`factor = job_size ÷ baseline_size`), taking the size from the request or asking once (`pending_template_size`). Convertible units (sq yd↔sq ft, lin yd↔lin ft) are converted; incompatible (area vs length) re-asks. Property context is linked.
- New: `agents/estimate/template_scaling.py` (`convert_size`, `parse_job_size`, `scale_job_item`), `agents/estimate/text_helpers.detect_template_in_create_request`, `routers/agent_helpers/template_estimate.py` (`begin_template_estimate`, `handle_pending_template_size`).
- **Gathering decline no longer cancels** (§1.3): "No"/"skip" to a gathering question (e.g. "Any material preferences?") records an assumption and continues; only explicit cancel phrases abort. New `is_cancellation_text`, `get_assumption_value`.
- Tests: `test_template_scaling.py`, `test_template_create_routing.py`, plus gathering/predicate additions.

**2026-06-02 — Phrasing expansion: ratios, age/staleness, status-`in`, material qualifiers**
- **Status comparisons / ratios** (§1.9) — "what's my won-lost ratio?", "won vs lost", generic "draft vs approved", "win rate", "how am I doing on bids?". New `parse_status_comparison()` + `format_status_comparison()` in `agents/estimate/text_helpers.py`; counts via `compute_status_comparison()` in `routers/estimates.py`; handled by `_analytics_comparison` in `crud_handlers.py`. Routed through the existing `analytics_estimates` path (`_match_analytics_query` now also calls `parse_status_comparison`). A win-loss family cue defaults to WON-vs-LOST; an explicit "X vs Y" names both statuses in order. Count-based, with a win-rate % for the WON/LOST pair.
- **Age / staleness filter** (§1.1) — "estimates that are 30 days old", "not touched in a month", "haven't been updated in 30 days" via new `_AGE_DAYS_OLD_PATTERN`. **Both** age phrasings (`older than X days` and `X days old`/stale) now constrain **`updated_at`** (was `created_at` for older-than) via `_estimate_date_filter_field()`; relative date-range phrasings ("from last week") keep `created_at`. Verbless age phrasings route to `list_estimates` via the orchestrator `_match_estimate_list_filter` fast-path.
- **Status filter via `in`** (§1.1) — "find estimates in draft", "estimates in review" already resolved via the existing `in` connector in `_estimate_status_from_text`; coverage rows added.
- **Material qualifier list** (§4.5/§4.9) — "what {X} materials do I have?" matches {X} as a substring against material **name OR category** (`_find_materials_by_name_or_category` + `_extract_list_qualifier`). Count-by-category ("how many hardscape materials do I have?") now resolves the category for count queries too.
- New tests: `tests/test_maple_phrasing_expansion.py` (routing + pure parsers/formatter), plus additions to `test_material_agent.py` and `test_estimates_analytics.py`.

**2026-06-02 — `clear` restored as a bulk-delete verb (with estimate-creation exemption)**
- Reverted the May 2026 removal of `clear` from the bulk-delete verb list: `clear all {resource}` ("clear all estimates", "clear every material") is again refused as a bulk delete, matching the `delete`/`remove`/`drop`/`wipe` policy (§8.1).
- Added `is_estimate_creation_request()` in `agents/text_utils.py`, applied at the **orchestrator routing layer** (`_detect_policy_short_circuit`) so estimate/quote creation requests whose job description mentions clearing/removing work ("create an estimate to clear out all the weeds in my backyard") route to `create_estimate` instead of being refused. The exemption is deliberately NOT inside `is_bulk_delete_request()` — that guard stays strict so each domain agent's defensive delete-path check keeps full force. A `_ESTIMATE_AS_DELETE_TARGET` veto ensures "delete every estimate" (estimate as the delete target) is never read as creation.
- Reconciled contradictory tests: `test_text_utils.py` and `test_maple_new_phrasings.py` now agree that `clear all {resource}` is bulk delete and estimate-creation-with-clearing is allowed (verified end-to-end through the orchestrator).

**2026-05-27 — Work-item field operations (implemented)**
- Expanded §1.5 from a flat table into eight sub-sections (§1.5.1–§1.5.8) covering all CRUD operations on work items inside an estimate.
- Added `{WI}` placeholder convention for work-item references (positional, by description, contextual).
- §1.5.1 Work-item CRUD: added list/count/show work items (3 → ✅ rule).
- §1.5.2 Division: assign/move/put/query phrasings (6 → ✅ rule, 1 bulk ⚠️ gap).
- §1.5.3 Description: "set description"/"update description"/"what's description" (3 → ✅ rule, 1 "describe as" ⚠️ gap).
- §1.5.4 Recurring schedule: all 13 phrasings implemented (✅ rule). `recurring`/`recurrence` removed from `_WORK_ITEM_REFUSED_FIELDS`. Handlers parse 3 schedule shapes: total occurrences, date range, specific months.
- §1.5.5 Materials in work item: all 11 phrasings implemented (✅ rule). Add material from catalog, remove by name, list/count. Sub-total auto-recalculated.
- §1.5.6 Activities in work item: 9/13 implemented (✅ rule). Add with optional role/effort, remove by name, list/count. 4 update-in-place phrasings (change role/effort/rate, assign rate card) remain ⚠️ gap.
- §1.5.7 Cost adjustments: subtotal/total read queries (2 → ✅ rule, 1 "how much" ⚠️ gap). Percentage fields remain 🛑 refused.
- §1.5.8 Total amount adjustment: all 9 phrasings implemented (✅ rule). Direct sub_total override with grand_total recalculation.
- New file: `agents/estimate/work_item_field_handlers.py` (WorkItemFieldHandlersMixin).
- New test file: `tests/test_maple_work_item_ops.py` (79 tests — routing, op detection, regression, param parsing).
- Orchestrator routing: extended verb list with make/assign/move/put/adjust/round/bump/reduce/turn/stop/disable; added sub-resource, list, query, and recurring patterns; work-item field queries bypass `is_help_query` (excludes definitional "what is a work item?").

**2026-05-26 — Template CRUD phrasings**
- Template resource added to terminology table and phrasing catalog (§6). All phrasings are ⚠️ gap — no Template Agent or orchestrator routing exists yet.
- Phrasings cover: list, get, delete, verbless, and apply-template-to-estimate (§6.7).
- Template **creation, update, and duplicate are refused** (§8.5) — users must manage these through the portal UI.
- Sections renumbered: old §6–§11 → §7–§12 to accommodate the new §6.

**2026-05-26 — May expansion**
- Dashboard analytics intent (`analytics_estimates`) with pipeline value, backlog, completed value, and breakdown-by-status/division phrasings (§1.9). Custom time windows respected — "pipeline value in the last 30 days" queries the DB with the user's window, not the default 90-day headline.
- Title-based estimate lookup — `_handle_get_estimate` now resolves estimates by quoted title or `title/called/named X` phrases when no EST-code is present (§1.2)
- "win" added as a verb-form alias for EstimateStatus.WON so "how many estimates did I win this month?" routes correctly
- "older than X days" age-based date filter via `_AGE_FILTER_PATTERN`
- "at property" cross-resource variant for estimate→property queries
- Contact→property "linked to" cross-resource patterns (§7.1)
- Material size "of" form (`how much does 12x12 of concrete blocks cost?`) and category query (`what category is material X?`) (§4.9)
- Role field queries via "what's the X for role Y?" routing to `get_labour` (§5.8)
- "clear" removed from bulk-delete verb patterns — ambiguous in this domain (§8.1)
- US English: user-facing "labour" → "labor" in response strings, accuracy suggestions, and guide content
- User guide updated: contacts can be linked to multiple properties (no limit)

**2026-05-13 — Object links in CRUD responses**
- `object_link()` helper in `agents/text_utils.py` renders `[Name](/properties?open=<id>)` for Property/Contact/Material/Labor Get/Create/Update/List responses and `[Name](/estimates/<id>)` for Estimate Get/List. Frontend list pages read `?open=<id>` on mount and auto-open the edit modal.

**2026-05-02 — Waves 1-4.1**
- Wave 4.1: Contact-anchored estimate list, EST-code regex broadened to alphanumeric, suffix "property" form
- Wave 4: Estimate ↔ property/contact outbound drilldowns (§1.8)
- Wave 3: Estimate filters (status + date + amount), cross-resource drilldowns (materials/roles on EST-code), material query variants, partial-bulk delete refusal
- Wave 2: Cross-resource routing + agent-side join for all four CRUD resources (§7)
- Wave 1: Possessive/field-targeted phrasings, help gaps (§10.5), coverage blind spots consolidated into §12

## How to read this doc

Each phrasing shows expected routing — the **intent** the orchestrator picks and the **agent** that handles it — plus its status:

- ✅ **rule** — handled deterministically by the rule-based classifier (`use_llm=False`). Works without an OpenAI key.
- 🤖 **LLM** — works on the live-LLM tier only (`use_llm=True`). Robust to paraphrase but slower and requires an OpenAI key.
- ⚠️ **gap** — not handled today. Use cases here are candidates for new classifier rules or handler work.
- 🛑 **refusal** — Maple is explicitly designed to refuse this phrasing (e.g., bulk delete, equipment management).

Token conventions used throughout:

| Placeholder | Example |
|---|---|
| `{property}` | `123 Main St` |
| `{contact}` | `John Doe` |
| `{material}` | `concrete blocks` |
| `{role}` | `Landscaper` |
| `{template}` | `Driveway Maintenance` |
| `{EST}` | `EST-0042`, `EST-4E73F7BB`, `EST-2026-001` (alphanumeric — anything matching `EST[-_][A-Za-z0-9\-_]*`) |
| `{size}` | `12x12` |
| `{unit}` | `each`, `sq ft`, `linear ft` |

## Terminology note — the 5 + 1 Maple resources

| User-facing | Code domain | What it represents |
|---|---|---|
| **Property** | `property` | Job sites / addresses |
| **Contact** | `contact` | **Individuals** at a property (homeowner, manager, etc.) |
| **Material** | `material` | Catalog of physical products with sizes/prices |
| **People** | `labour` | Catalog of **role definitions** (Landscaper, Foreman). NOT individuals — that's Contact. |
| **Template** | `template` | Reusable estimate blueprints with predefined materials, activities, and cost parameters. |
| **Estimate** | `estimate` | Quotes / job costings. Generated by an AI agent from a job description. |

Equipment is **explicitly blocked** via `is_equipment_request()` at the orchestrator layer — see §8.

## How to add new use cases

1. Add the phrasing under the appropriate resource section with status ⚠️ gap. Include the intended intent/agent if you have one.
2. Ping Claude with "add these phrasings to Maple" — Claude will write failing tests, implement the rule, and flip the status to ✅ here.
3. For phrasings that should be refused, add under §8 with status 🛑 and note why.

Tests live in `platform/tests/test_maple_crud_coverage.py` (matrix) and `platform/tests/test_maple_*.py` (targeted). Running the matrix regenerates `platform/tests/reports/maple_crud_gap_report.md` with live pass/fail counts.

---

# 1. Estimates

Estimate is not in the CRUD coverage matrix — its generation is multi-turn and its operations (status transitions, work items, linking) don't fit the generic category templates. These are curated.

## 1.1 Count & status queries

| Phrasing                                             | Intent → Agent                                                 | Status                                                                                                                                                                                                                                                              |
| ---------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `how many estimates do I have?`                      | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `count my estimates`                                 | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `how many estimates with status draft?`              | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `what's the total estimates with status approved?`   | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `can you add up the estimates with status approved?` | `list_estimates` → Estimate Agent                              | ✅ rule *(closed in Phase A1)*                                                                                                                                                                                                                                       |
| `how many approved estimates do I have?`             | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `count my draft quotes` (quotes = synonym)           | `list_estimates` → Estimate Agent                              | ✅ rule                                                                                                                                                                                                                                                              |
| `what is the total value of the open estimates`      | aggregated `sum(grand_total)` across DRAFT/APPROVED/REVIEW/WON | ✅ rule *(closed in xfail-wave-3 Workstream C — `_AGGREGATE_VALUE_QUERY_PATTERN` + `_OPEN_ESTIMATE_QUERY_PATTERN` short-circuit `_handle_list_estimates` to a single dollar figure)*                                                                                 |
| `show me draft estimates from last week`             | `list_estimates` with `created_at` window                      | ✅ rule *(closed in xfail-wave-3 Workstream C — `_parse_estimate_date_filter` adds a `$gte/$lte` constraint on `created_at`)*                                                                                                                                        |
| `approved quotes over $10k`                          | `list_estimates` with status + `grand_total` range             | ✅ rule *(closed in xfail-wave-3 Workstream C — verbless plural-domain inference + `_parse_estimate_amount_filter` adds a `$gt`/`$lt` constraint on `grand_total`; `k`/`m` suffixes supported)*                                                                      |
| `what materials does {EST} use?`                     | `list_materials` filtered to one estimate's snapshot           | ✅ rule *(closed in xfail-wave-3 Workstream C — orchestrator routes via `_CROSS_RESOURCE_QUERY_PATTERNS` with `filter_by={type=estimate, name=EST-…}`; Material agent's `_handle_list_materials_for_estimate` resolves and projects the embedded `materials` array)* |
| `what roles are on {EST}?`                           | `list_labours` filtered to one estimate's snapshot             | ✅ rule *(closed in xfail-wave-3 Workstream C — symmetric Labour-agent drilldown via `_handle_list_labours_for_estimate`)*                                                                                                                                           |
| `how many estimates did I win this month?`           | `list_estimates` with status=WON + date filter                 | ✅ rule *(May expansion — "win" added as a verb-form alias for EstimateStatus.WON in `_estimate_status_from_text`)*                                                                                                                                                  |
| `show only estimates with Won status this month`     | `list_estimates` with status=WON + date filter                 | ✅ rule *(status + date qualifiers already compose; no new code needed)*                                                                                                                                                                                              |
| `show me all estimates older than 60 days`           | `list_estimates` with `updated_at <= cutoff`                   | ✅ rule *(`_AGE_FILTER_PATTERN` + age branch in `_parse_estimate_date_filter` returns `(None, cutoff)`; field is `updated_at` as of the 2026-06-02 expansion)*                                                                                                       |
| `show me estimates that are 30 days old`             | `list_estimates` with `updated_at <= cutoff`                   | ✅ rule *(2026-06-02 — `_AGE_DAYS_OLD_PATTERN`; "X days/weeks/months old" → at-least-X-old)*                                                                                                                                                                          |
| `which estimates haven't been updated in 30 days?` / `estimates not touched in a month` | `list_estimates` with `updated_at <= cutoff` | ✅ rule *(2026-06-02 — staleness alternation in `_AGE_DAYS_OLD_PATTERN`; verbless forms routed via `_match_estimate_list_filter`)*                                                                                                                                   |
| `find estimates in draft` / `estimates in review`    | `list_estimates` with status filter                            | ✅ rule *(`in` connector in `_estimate_status_from_text`; only fires when the token after `in` is a known status — "estimates in Toronto" stays a property query)*                                                                                                   |
| `show me Draft estimates at property {property}`     | `list_estimates` with status + property cross-resource filter  | ✅ rule *(May expansion — "at\s+property" added to the property→estimate cross-resource pattern)*                                                                                                                                                                    |

## 1.2 Value / total queries for a specific estimate

| Phrasing                               | Intent → Agent                  | Status                        |
| -------------------------------------- | ------------------------------- | ----------------------------- |
| `what is the value of estimate {EST}?` | `get_estimate` → Estimate Agent | ✅ rule                        |
| `what's the total for {EST}?`          | `get_estimate` → Estimate Agent | ✅ rule *(closed in Phase A2)* |
| `how much is {EST}?`                   | `get_estimate` → Estimate Agent | ✅ rule *(closed in Phase A3)* |
| `what's the grand total for {EST}?`    | `get_estimate` → Estimate Agent | ✅ rule                        |
| `worth of {EST}`                       | `get_estimate` → Estimate Agent | ✅ rule                        |

Handler: `_handle_get_estimate` detects `_GRAND_TOTAL_QUERY_PATTERN` and leads the response with the dollar amount.

**Title-based lookup** *(May expansion)*: when no EST-code is found in the query, `_resolve_estimate_by_title` extracts a title from quoted text (`"Untitled Estimate"`) or `title/called/named X` phrasings and searches by substring match. Single match → returns the estimate. Multiple matches → lists them and asks the user to pick by code.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `tell me about estimate with title "Untitled Estimate"` | `get_estimate` → Estimate Agent | ✅ rule |
| `show me the estimate called "Driveway Replacement"` | `get_estimate` → Estimate Agent | ✅ rule |
| `pull up estimate named "Foundation Work"` | `get_estimate` → Estimate Agent | ✅ rule |
| `show me estimate details for {EST or title}` (e.g. `Spring Cleaning`) — response includes `created_at`, `updated_at`, the estimate ID/code, description, and notes | `get_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `_build_estimate_details_text` now renders Created / Last updated / Description / Notes / ID lines (blank optionals omitted; core fields keep the `—` placeholder). Bare titles resolve via `_TITLE_PRE/POST_NOUN_RE`. **Caveat:** the linked property NAME is still not rendered — it needs an async lookup from `Estimate.property`; follow-on.)* |
| `show me everything on the {title} quote` | `get_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — verified routing; pre-noun bare-title extraction. **2026-06-09:** an explicitly-named title now beats `active_estimate_code` — viewing one estimate then asking for another by name returns the NAMED one, not the viewed one.)* |
| `give me the rundown on the {title} estimate` / `full breakdown on the {title} job` | `get_estimate` → Estimate Agent | ⚠️ gap *(verified 2026-06-06: routes to `unknown` — "rundown"/"breakdown" aren't get-action cues)* |
| `what's the full info on {title}?` / `open up the {title} estimate` | `get_estimate` → Estimate Agent | ⚠️ gap *(verified 2026-06-06: "full info on Spring Cleaning" **misroutes to `get_contact`** via the person-name heuristic; "open up" routes to `unknown`)* |
| `when was the {title} estimate created?` | `get_estimate` → Estimate Agent (lead with `created_at`) | ⚠️ gap *(verified 2026-06-06: **misroutes to `create_estimate`** — the word "created" trips the create-action hint. Needs a when-was/question-form guard before the create hint, then a `created_at` lead in the get handler.)* |
| `when was {EST} last updated?` / `when did I last touch the {title} quote?` | `get_estimate` → Estimate Agent (lead with `updated_at`) | ⚠️ gap *(verified 2026-06-06: routes to `help`. Note the timestamps DO now appear when the user asks for the estimate's details.)* |
| `what's the ID for the {title} estimate?` | `get_estimate` → Estimate Agent (lead with `estimate_id`) | ⚠️ gap *(verified 2026-06-06: routes to `help`)* |

**Implementation note (updated 2026-06-06):** the response-detail half of this section shipped — `_build_estimate_details_text` carries timestamps/ID/description/notes, and bare-title resolution works wherever `_resolve_estimate_by_title` is consulted. What remains is **routing** for the casual/single-field forms above (rundown / full info / open up / when-was-X / what's-the-ID): they need get-cues or a question-form guard before the create/help classifiers, plus a focused-field lead (mirroring `_GRAND_TOTAL_QUERY_PATTERN`). Separately, **estimate synonyms** `bid`/`proposal` route (they're in the orchestrator's `_estimate_ref`) but are NOT yet title-extraction nouns (`_TITLE_PRE/POST_NOUN_RE` accept only `estimate|quote`), and **job-name reference** ("the Smith job") remains open — both are Task-8 stretch items in [plans/maple-estimate-field-edits.md](plans/maple-estimate-field-edits.md).

## 1.3 Generation (multi-turn, LLM-driven)

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `create an estimate for {property} — needs 20 yards of concrete and two landscapers` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `draft a quote for a driveway replacement at 456 Oak Ave` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `I need an estimate for [job description]` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `create a residential estimate` | `create_estimate` → Estimate Agent | 🤖 LLM |
| `new commercial quote` | `create_estimate` → Estimate Agent | 🤖 LLM |

Handled by `agents/estimate/conversation_guide.py`. The EstimateAgent walks the user through job description → material/equipment/labour recommendations → estimate creation.

**Two important branches before generation runs** (`routers/agent_helpers/delegate_create_estimate.py`):
- **Template named → AI generation is skipped entirely** and the estimate is instantiated from the template (§6.7) — no material/activity questions.
- **Gathering decline → assumption, not cancel.** A "No"/"skip" to a gathering question (e.g. "Any material preferences?") records an assumption and continues; only an explicit cancellation ("cancel", "never mind") aborts. See `routers/agent_helpers/estimate_gathering.py` (`is_cancellation_text`, `get_assumption_value`).

## 1.4 Status transitions

EstimateStatus values: `DRAFT`, `APPROVED`, `WON`, `LOST`, `ONHOLD`, `SCHEDULED`, `COMPLETED`, `SUBMITTED`, `REVIEW`, `ARCHIVED`.

**State machine + authorization enforced (2026-06-11):** every phrasing below is additionally subject to `validate_estimate_status_transition` (`models/estimate.py`, mirrors `portal/src/lib/estimateStatus.ts`) and to the HTTP layer's role gates (send/unsend → Owner/Admin; archive/unarchive → Owner/Admin or creator). A recognized phrasing whose edge is illegal for the estimate's *current* status — e.g. `mark {EST} as won` on a Draft — or that the user isn't authorized for, refuses in Maple's persona voice instead of saving. See §8.6.

**Deterministic routing (2026-06-15):** the Orchestrator now routes status-transition phrasings to `update_estimate` via a `process()` fast-path (ahead of the LLM) and a `_classify_with_rules` branch, both gated on an estimate reference + the shared `parse_status_transition` matcher (`agents/estimate/text_helpers.py`). The ✅-rule rows below were previously 🤖 LLM and routed inconsistently. **Question forms** (`Can you …?`) are claimed by the help classifier and answered with an offer to proceed — see the last two rows.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `approve {EST}` | `update_estimate` → Estimate Agent | 🤖 LLM *(`approve` isn't in the status-verb set; LLM-routed)* |
| `mark {EST} as approved` / `mark {EST} as sent` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-15 — `as Y` shape via `parse_status_transition`)* |
| `set the status for\|of\|on {EST} to {Y}` (e.g. `set the status for EST-… to Sent`) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-15 — `_STATUS_TRANSITION_STATUS_REF_TO_PATTERN`; the estimate code may sit between "status" and "to". The originally-reported failing phrasing.)* |
| `archive {EST}` / `unarchive {EST}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-15 routing; archive/unarchive verbs are their own triggers)* |
| `reject the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `send {EST} for review` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `put {EST or title} on hold` / `place it on hold` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-09 — `_ON_HOLD_PATTERN` maps bare "on hold" (with a status verb incl. `put`/`place`) to ONHOLD; guarded by `_NOTE_OR_DESC_CUE_PATTERN` so a note/description body mentioning "on hold" isn't hijacked)* |
| `move this estimate to draft` | `update_estimate` → Estimate Agent | 🤖 LLM *(`to draft` has no `status` terminator; LLM-routed)* |
| `Can you set the status for {EST} to {Y}?` (question form) | `help` → Orchestrator, then **offer** | ✅ rule *(2026-06-15 — answered with "Yes — I can set {EST} to {Y} … Want me to go ahead?" + a `pending_status_transition` record; a following "yes" executes, "no" cancels. Requires an EST-code + recognized target.)* |
| `yes` / `go ahead` (replying to the offer above) | `update_estimate` → Estimate Agent | ✅ rule *(`handle_pending_status_transition`, `routers/agent_helpers/pending_status_transition.py`)* |
| `update {EST or title} from {X} to {Y} status` (e.g. `from Sent to Review status`) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-08 — `_detect_status_transition` now recognizes the `update` verb and the `from X to Y status` / `to Y status` phrasings via `_STATUS_TRANSITION_TO_STATUS_PATTERN`, anchored on the trailing `status` word so it captures the target Y. Previously fell through to "What would you like to change?". **Same change** switched the status handler to the title-aware resolver `_resolve_estimate_code_or_title`, and made an explicitly-named title override `active_estimate_code` — fixes a data-integrity bug where naming an estimate by title while viewing another updated the WRONG (viewed) estimate. **2026-06-09:** extended title-awareness to ALL estimate UPDATE + READ sub-ops — work items, work-item fields, status — via the shared `_resolve_update_estimate_code` seam and a title-aware `_load_estimate_for_read`.)* |
| `update {EST or title} to {Y} status` (e.g. `to Review status`) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-08 — same `to Y status` pattern; works with `update`/`move`/`change`/`transition`/`switch`/`put`/`place` verbs)* |
| `what's the status of {EST}?` | `get_estimate` → Estimate Agent | 🤖 LLM |

## 1.5 Work-item / line-item management

All work-item operations route to `update_estimate` → Estimate Agent. Orchestrator regex rules at `agents/orchestrator/service.py:230-248` detect the work-item / job-item / scope / line-item token and route accordingly; the Estimate Agent's `WorkItemHandlersMixin` dispatches to the specific sub-operation.

**Work-item reference conventions** — users can identify a work item by:

| Placeholder | Examples |
|---|---|
| `{WI}` (positional) | `work item 1`, `work item #2`, `the first scope`, `the last line item` |
| `{WI}` (by description) | `the Driveway work item`, `the Foundation scope` |
| `{WI}` (contextual) | `this work item`, `the work item` (when only one, or most recently discussed) |

Synonyms: `work item`, `job item`, `scope`, `line item` are interchangeable in all phrasings below.

### 1.5.1 Work-item CRUD (add / remove / rename)

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add a work item to the estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a job item to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a scope to the last estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a line item to this estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `create another scope on {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add a work item called "Foundation Prep" to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `change work item #1 in {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove work item 2 from this estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `delete the Driveway scope from {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `rename the scope to Foundation` | `update_estimate` → Estimate Agent | ✅ rule |
| `how many work items does {EST} have?` | `update_estimate` → Estimate Agent | ✅ rule |
| `list the work items in {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `show me the scopes on this estimate` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.2 Division assignment

Division and description are editable via chat. Values come from `EstimateDivision` enum: Design/Build, Irrigation & Lighting, Maintenance, Snow & Ice, Tree Care, Turf & Plant Care, Unassigned — plus custom `Division` documents per company.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `set the division of {WI} to Maintenance` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the division on {WI} to Snow & Ice` | `update_estimate` → Estimate Agent | ✅ rule |
| `assign {WI} to the Design/Build division` | `update_estimate` → Estimate Agent | ✅ rule |
| `move {WI} to Tree Care` | `update_estimate` → Estimate Agent | ✅ rule |
| `put {WI} under Irrigation & Lighting` | `update_estimate` → Estimate Agent | ✅ rule |
| `what division is {WI} in?` | `update_estimate` → Estimate Agent | ✅ rule |
| `which division does {WI} belong to?` | `update_estimate` → Estimate Agent | ✅ rule |
| `set all work items in {EST} to Maintenance` | `update_estimate` → Estimate Agent | 🤖 LLM |

### 1.5.3 Description

The rename handler already covers description updates. These phrasings extend the surface with "description"-keyword variants.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `rename {WI} to "Foundation Prep"` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the name of {WI} to "Driveway Installation"` | `update_estimate` → Estimate Agent | ✅ rule |
| `set the description of {WI} to "Excavation and grading"` | `update_estimate` → Estimate Agent | ✅ rule |
| `update the description on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `describe {WI} as "Remove existing pavers and re-lay"` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `what's the description of {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.4 Recurring schedule

`JobItem.recurring` (bool) + `JobItem.recurrence` (`RecurrenceSchedule`) control repeat billing. `RecurrenceSchedule` supports three end types: `DATE_RANGE` (start/end month+year), `TOTAL_OCCURRENCES` (fixed count), and `SPECIFIC_MONTHS` (named months across years). Currently only `month` period is supported.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `make {WI} recurring` | `update_estimate` → Estimate Agent | ✅ rule |
| `set {WI} to recur monthly` | `update_estimate` → Estimate Agent | ✅ rule |
| `set {WI} to repeat every month` | `update_estimate` → Estimate Agent | ✅ rule |
| `make {WI} recurring from April to October` | `update_estimate` → Estimate Agent | ✅ rule |
| `set {WI} to 6 occurrences` | `update_estimate` → Estimate Agent | ✅ rule |
| `make {WI} recurring in April, May, June, July, August` | `update_estimate` → Estimate Agent | ✅ rule |
| `turn off recurring on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove the recurring schedule from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `stop {WI} from recurring` | `update_estimate` → Estimate Agent | ✅ rule |
| `is {WI} recurring?` | `update_estimate` → Estimate Agent | ✅ rule |
| `how many occurrences does {WI} have?` | `update_estimate` → Estimate Agent | ✅ rule |
| `what's the recurring schedule on {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the recurrence on {WI} to 12 occurrences` | `update_estimate` → Estimate Agent | ✅ rule |

`recurring` and `recurrence` removed from `_WORK_ITEM_REFUSED_FIELDS` in `text_helpers.py`. Handlers parse three `RecurrenceSchedule` shapes: total occurrences, date range (month-to-month), and specific months.

### 1.5.5 Materials within a work item

`JobItem.materials` is a `List[MaterialItem]` — each entry snapshots a catalog material with quantity and price. These phrasings manage the embedded material list on a specific work item, distinct from the top-level Material catalog CRUD in §4.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add concrete blocks to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add material {material} to {WI} in {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add 50 concrete blocks to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add {material} with quantity 20 and size 12x12 to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove concrete blocks from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove all materials from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the quantity of concrete blocks in {WI} to 100` | `update_estimate` → Estimate Agent | ✅ rule |
| `update the price of {material} in {WI} to $12` | `update_estimate` → Estimate Agent | ✅ rule |
| `how many materials are in {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `what materials does {WI} have?` | `update_estimate` → Estimate Agent | ✅ rule |
| `list the materials in {WI}` | `update_estimate` → Estimate Agent | ✅ rule |

**Disambiguation note:** `what materials does {EST} use?` (§1.1) queries all materials across all work items via the cross-resource drilldown. The phrasings above scope to a *single* work item within the estimate.

### 1.5.6 Activities within a work item

`JobItem.activities` is a `List[ActivityItem]` — each entry describes a labor task with an optional role (from the Labor catalog), rate, effort hours, and an optional effort-rate-card breakdown. Activities represent the labor component of a work item.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add an activity to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add activity "Excavation" to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add an activity called "Grading" with role Landscaper to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `add activity "Planting" with 8 hours of effort to {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove the Excavation activity from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `remove all activities from {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the role on the Excavation activity to Foreman` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `set the effort on the Grading activity in {WI} to 12 hours` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `update the rate for the Planting activity to $45/hr` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `assign an effort rate card to the Excavation activity in {WI}` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `what activities are in {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `list the activities on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |
| `how many activities does {WI} have?` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.7 Cost adjustments (profit margin, overhead, labor burden, tax)

`JobItem` carries four cost parameters: `profit_margin` (default 15%), `overhead_allocation` (default 0%), `labor_burden` (default 0%), and `tax` (default 0%). These multiplicatively affect the work item's `sub_total` and roll up into `Estimate.grand_total`.

**Current policy:** these fields are in `_WORK_ITEM_REFUSED_FIELDS` — the agent directs users to the UI because financial changes have dollar-impact visibility concerns. The phrasings below are defined for review; implementation would require lifting the refusal.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `set the profit margin on {WI} to 20%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `change the margin on {WI} to 25%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `set overhead allocation on {WI} to 10%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `change the overhead on {WI} to 15%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `set the labor burden on {WI} to 12%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `change the labor burden on the Foundation scope to 18%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `set tax on {WI} to 13%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `change the tax rate on {WI} to 8.25%` | `update_estimate` → Estimate Agent | 🛑 refused |
| `what's the profit margin on {WI}?` | `update_estimate` → Estimate Agent | 🛑 refused |
| `what's the subtotal of {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |
| `how much is {WI}?` | `update_estimate` → Estimate Agent | 🤖 LLM |
| `what's the total for {WI}?` | `update_estimate` → Estimate Agent | ✅ rule |

### 1.5.8 Total amount adjustment

Direct override of a work item's `sub_total`. Unlike the percentage-based cost parameters in §1.5.7, this sets an absolute dollar amount on the work item, which then rolls up into `Estimate.grand_total`. Useful for rounding, flat-rate pricing, or manual corrections.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `adjust the total on {WI} to $1600` | `update_estimate` → Estimate Agent | ✅ rule |
| `set the total for {WI} to $2500` | `update_estimate` → Estimate Agent | ✅ rule |
| `change the amount on {WI} to $3000` | `update_estimate` → Estimate Agent | ✅ rule |
| `round up {WI} to $2000` | `update_estimate` → Estimate Agent | ✅ rule |
| `round the total on {WI} to $1500` | `update_estimate` → Estimate Agent | ✅ rule |
| `make {WI} an even $5000` | `update_estimate` → Estimate Agent | ✅ rule |
| `bump {WI} up to $1800` | `update_estimate` → Estimate Agent | ✅ rule |
| `reduce {WI} to $1200` | `update_estimate` → Estimate Agent | ✅ rule |
| `set a flat rate of $750 on {WI}` | `update_estimate` → Estimate Agent | ✅ rule |

## 1.6 Linking

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `link {EST} to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — orchestrator `_link_relationship` arm + `_LINK_VERB_TO_ESTIMATE_PATTERN`; was 🤖 LLM)* |
| `attach this estimate to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — "this estimate" resolves via `active_estimate_code` anaphora)* |
| `which property is this estimate for?` | `get_estimate` → Estimate Agent | 🤖 LLM |
| `set the property of estimate {EST} to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(the link branch `_is_property_link_request` matches `set ... property`; `_handle_update_estimate_property_link` resolves the property by name/address)* |
| `set the property of estimate {Estimate Name} to {property}` (estimate referenced by **title**) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — all update sub-handlers resolve via the shared `_resolve_estimate_code_or_title` (code → anaphora → latest → title); bare titles are extracted by `_TITLE_PRE_NOUN_RE`/`_TITLE_POST_NOUN_RE` — **first word capitalized, 2+ words** (sentence-case tails OK, bounded by a connector stop-list) adjacent to "estimate"/"quote")* |
| `this quote is for the {property} property` / `the property for this quote is {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `_LINK_RELATIONSHIP_PATTERN`)* |
| `tie / connect / associate the {title} quote to/with {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — broadened verb set in `_LINK_PROPERTY_PATTERN` + `_LINK_VERB_TO_ESTIMATE_PATTERN` for bare property names)* |
| `assign {EST} to the {property} property` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `assign` in `_LINK_PROPERTY_PATTERN`; deliberately NOT in the bare-name pattern, so "assign" only links when "property" or an address is present)* |
| `change the property on the {title} quote to {property}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06)* |
| `set the job site for this estimate to {address}` | `update_estimate` → Estimate Agent | ⚠️ gap *(routes to `update_estimate` ("job site" is a routing field token), but `_is_property_link_request` has no "job site" cue, so it falls to the generic clarification. Implementation: add a `job\s*site` alternation to `_LINK_PROPERTY_PATTERN`.)* |
| `the {title} job is at {address}` / `this estimate goes with {address}` | `update_estimate` → Estimate Agent | ⚠️ gap *("the {X} job" isn't an estimate reference (job-name resolution is the Task-8 stretch) and "goes with"/"is at" aren't link cues yet)* |

**Implementation note (shipped 2026-06-06):** estimate resolution on the linking path is code → `active_estimate_code` anaphora → "latest" → bare/quoted title (shared `_resolve_estimate_code_or_title`). Property resolution is name or bare address (`_extract_property_name` / `_extract_property_address`); possessive nicknames ("Bob's place") remain a softer follow-on gap. Routing note: the orchestrator's bare link-verb arm is deliberately broad — the `_estimate_ref` gate (estimate/quote/bid/proposal/EST-code) is the load-bearing guard, and the contact↔property link rules earlier in `_classify_specific_phrasings` still win for contact links.

## 1.7 Anaphora / active estimate

When session context carries `active_estimate_code` (user recently worked on an estimate):

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `add a Landscaper to the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM + context |
| `update the estimate` | `update_estimate` → Estimate Agent | 🤖 LLM + context |
| `show me the estimate` | `get_estimate` → Estimate Agent | 🤖 LLM + context |
| `this estimate` / `the last estimate` / `that one` | resolves via `active_estimate_code` | 🤖 LLM + context |
| `the same estimate` / `that estimate` / `the previous estimate` (after a note/description/work-item edit) | resolves via `active_estimate_code` | ✅ rule *(2026-06-07 — flat-result estimate updates now persist `active_estimate_code` in `finalize_result`, so anaphora anchors on the just-edited estimate; previously these asked "Which estimate?")* |

## 1.8 Estimate ↔ property/contact outbound drilldowns

Closed in xfail-wave-4 + 4.1 (plan: [maple-xfail-wave-4-estimate-outbound.md](plans/maple-xfail-wave-4-estimate-outbound.md)). Routes through `_CROSS_RESOURCE_QUERY_PATTERNS` with three cross-types:
- `cross_type=estimate` (Wave 4 Workstream A) — Property/Contact agents resolve the EST code via `find_estimate_by_code` and follow `Estimate.property` → `Property.contacts`.
- `cross_type=property` (Wave 4 Workstream B) — Estimate agent resolves the property via `find_properties_by_name_or_address` and constrains by `Estimate.property`.
- `cross_type=contact` (Wave 4.1) — Estimate agent resolves the contact via `find_contacts_by_full_name`, walks `Property.contacts` to a property-id set, then constrains `Estimate.property in [...]`.

| Phrasing                                           | Intent → Agent                                                                       | Status |
| -------------------------------------------------- | ------------------------------------------------------------------------------------ | ------ |
| `which property is this estimate {EST} linked to?` | `list_properties` → Property Agent (resolve estimate → return its linked property)   | ✅ rule *(Workstream A)* |
| `which contact is this estimate {EST} for?` (also without the `this`, e.g. `which contact is estimate EST-4E73F7BB for?`) | `list_contacts` → Contact Agent (resolve estimate → property → contacts) | ✅ rule *(Workstream A)* |
| `who is this estimate {EST} for?`                  | `list_contacts` → Contact Agent (response leads with the property name as join lead-in) | ✅ rule *(Workstream A)* |
| `show me estimates for property {property}`        | `list_estimates` → Estimate Agent (resolve property by name/address → constrain by `Estimate.property`) | ✅ rule *(Workstream B)* |
| `estimates linked to {property}` / `what estimates are for property {property}` | same as above | ✅ rule *(Workstream B)* |
| `show me estimates for {property} property` (suffix form, e.g. `Bob Residential property`) | `list_estimates` → Estimate Agent (suffix `property` strips from captured name) | ✅ rule *(Wave 4.1 follow-up)* |
| `show me estimates for {contact}` (capitalized name) | `list_estimates` → Estimate Agent (transitive: resolve contact → properties → estimates) | ✅ rule *(Wave 4.1)* |

**Empty-result copy** (so the user sees why nothing matched, instead of an empty list):
- Estimate not found → *"I couldn't find an estimate with code '{EST}'."*
- Estimate exists but `property` is `None` → *"Estimate {EST} isn't linked to a property yet."*
- Property linked but missing contacts → *"Estimate {EST} is linked to {property}, but that property has no contacts yet."*
- No property matches the constraint name → *"I couldn't find a property matching '{name}'."*
- No contact matches the constraint name → *"I couldn't find a contact matching '{name}'."*
- Contact resolves but isn't linked to any property → *"{Name} isn't linked to any properties yet, so there are no estimates to show."*

**Anchoring rules:**
- Property-anchored Workstream B fires on either the prefix form (`for property X` / `linked to (property)? X`) OR the suffix form (`for X property` / `for X properties`). Status phrasings like `estimates for approval` / `estimates for review` don't match (no `property` or `linked to` token).
- Contact-anchored Wave 4.1 uses a broad `estimates? for X` shape gated by a `fullmatch` on the captured slice in original case: it must be exactly a 2+ word capitalized name. `Bob Residential property` (trailing noun), `John Doe at 123 Main St` (locator suffix), and `bob jones` (lowercase) all fail the gate and fall through. Property-anchored patterns are checked first inside the same matcher, so `estimates for property Bob Jones` and `estimates for Bob Residential property` both win as `cross_type=property` before the contact gate runs.

## 1.9 Dashboard / analytics queries

Added in the May 2026 expansion. Routed via `_match_analytics_query` in the orchestrator to a new `analytics_estimates` intent handled by the Estimate Agent. Runs before `is_help_query` so question-word phrasings aren't swallowed by the help classifier.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what's the value in the pipeline?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what's my pipeline value in the last 30 days?` | `analytics_estimates` → Estimate Agent (custom window) | ✅ rule |
| `what's the backlog value?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what's my completed value?` / `how much was completed?` | `analytics_estimates` → Estimate Agent (COMPLETED only, last 30 days) | ✅ rule *(2026-06-20 — replaced the retired "won value" headline; see change log)* |
| `what's the breakdown of estimates by statuses this month?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what's the breakdown of estimates by divisions?` | `analytics_estimates` → Estimate Agent | ✅ rule |
| `what is my won-lost ratio?` / `win-loss ratio` / `win/loss ratio` | `analytics_estimates` → Estimate Agent (WON vs LOST) | ✅ rule *(2026-06-02 — `parse_status_comparison`; count ratio + win-rate %)* |
| `won vs lost` / `how many estimates did I win vs lose?` | `analytics_estimates` → Estimate Agent (WON vs LOST) | ✅ rule *(2026-06-02)* |
| `draft vs approved estimates` / `compare won and lost estimates` | `analytics_estimates` → Estimate Agent (generic pair) | ✅ rule *(2026-06-02 — explicit "X vs Y" / "compare X and Y"; no win-rate framing for non-WON/LOST pairs)* |
| `what's my win rate?` / `what's my win rate this month?` | `analytics_estimates` → Estimate Agent (WON vs LOST, window-aware) | ✅ rule *(2026-06-02)* |
| `how am I doing on bids?` | `analytics_estimates` → Estimate Agent (WON vs LOST) | ✅ rule *(2026-06-02 — landscaper-friendly win-rate cue)* |
| `how is the backlog value calculated?` / `what does pipeline value mean?` / `how is the completed value calculated?` | `help` → Orchestrator Agent | ✅ rule *(2026-06-20 — explanatory/definitional phrasing about a metric routes to HELP, not a value lookup. `_match_analytics_query` now redirects a recognized metric phrased with an explanatory cue (`calculated`/`computed`/`defined`/`mean`/…) to help; `calculated`/`computed` also added to `HELP_INSTRUCTIONAL_PATTERNS` for metrics without an analytics keyword.)* |

**Status comparisons / ratios:** `compute_status_comparison` counts each status (all-time unless a date window is given, in which case it constrains `updated_at`). `format_status_comparison` renders a reduced `A:B` ratio; the WON-vs-LOST pair additionally reports a win-rate percentage (`won / (won + lost)`). Generic pairs ("draft vs approved") report counts + ratio only.

**Time windows:** Pipeline/backlog/won headline queries respect user-specified date ranges ("last 30 days", "this month", "last week") via `_parse_estimate_date_filter`. When no date qualifier is present, the handler falls back to default windows: **pipeline = 90 days, completed = 30 days, backlog = all-time (no recency window)**. An all-time backlog answer reads "… in total" rather than "… in the last N days". Breakdown queries use the `period` parameter ("month"/"quarter"/"year") passed to `compute_analytics`.

**Status sets must mirror the dashboard cards** (`compute_analytics` in `routers/estimates.py`): pipeline = `[DRAFT, SENT, REVIEW, WON]`, **backlog = `[WON, SCHEDULED]` (all-time)**, **completed = `[COMPLETED]` (last 30 days)**. *(2026-06-20 — fixed a parity bug where the chat backlog headline summed only `[WON]`, so Maple reported $0.00 while the dashboard showed the real figure. `_analytics_headline_value` in `crud_handlers.py` now includes SCHEDULED.)* *(2026-06-20 — backlog relaxed from last-30-days to **all-time** in both `compute_analytics` and `_analytics_headline_value`: backlog = every Won/Scheduled estimate regardless of recency; dashboard card now labeled "All time".)*

## 1.10 Estimate-level field edits (description & notes)

These edit **top-level `Estimate` fields** — distinct from the work-item (`JobItem`) description edits in §1.5.3. Both `description` and `notes` exist on the `Estimate` model (`models/estimate.py`). Routing is `update_estimate` → Estimate Agent; the dispatcher is `_handle_update_estimate` (`crud_handlers.py:1632`).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `for estimate {EST}, add to the notes the following: "..."` | `update_estimate` → Estimate Agent | ✅ rule *(`_detect_note_update` → `_handle_update_estimate_notes`, append-mode; preserves existing notes. 2026-06-07 — the quoted body is captured in full even with an apostrophe inside (`"Contact me if there's any issues"`); straight + curly, double + single quotes via the shared `_QUOTED_VALUE_GROUP`)* |
| `set the notes on {EST} to "..."` / `update notes: ...` | `update_estimate` → Estimate Agent | ✅ rule *(same handler; set-mode vs append-mode chosen by verb)* |
| `for estimate {Estimate Name}, add to the notes the following: "..."` (estimate referenced by **title**) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — notes handler resolves via the shared `_resolve_estimate_code_or_title`; bare titles extracted by `_TITLE_PRE/POST_NOUN_RE` — first word capitalized, 2+ words (sentence-case OK) near "estimate"/"quote". The bare-title patterns run **before** the any-quoted fallback so a quoted note body is never mistaken for the title.)* |
| `add a note to the {title} quote: "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06)* |
| `update the description of estimate {EST} with the following: "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `_detect_estimate_description_update` + `_handle_update_estimate_description` set the top-level `Estimate.description`; quoted, colon, and unquoted `to ...` value forms supported, incl. an EST-code sitting between the keyword and the connector)* |
| `set the description of estimate {EST} to "..."` / `change the estimate description to "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06)* |
| `change the description on the {title} quote to "..."` / `reword the description on this estimate to "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — title via bare-title extraction; "this estimate" via anaphora)* |
| `update the write-up/overview for {EST} to "..."` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — `write-up`/`overview` are description-cue synonyms)* |
| `put "..." as the overview for the estimate` | `update_estimate` → Estimate Agent | ⚠️ gap *(value-**before**-cue word order — the extractors expect the cue before the value; needs a `put "X" as the description/overview` pattern)* |
| `describe the {title} estimate as "..."` / `the description for the {title} job should be "..."` | `update_estimate` → Estimate Agent | ⚠️ gap *(`describe ... as` and `... should be` shapes have no extractor; "the {X} job" also isn't an estimate reference)* |
| `make a note on {EST} that ...` / `leave a note on {EST}: "..."` / `tack a note onto the {title} quote: "..."` | `update_estimate` → Estimate Agent | ⚠️ gap *(corrected 2026-06-06: the routing verb list lacks `make`/`leave`/`tack`, so these never reach the agent on a fresh turn; "make a note ... that X" additionally needs a generic `note ... that` tail extractor (only `remember ... that` exists). Reachable today only when the orchestrator already routed to `update_estimate` for another reason.)* |
| `note on the {title} job: ...` | `update_estimate` → Estimate Agent | ⚠️ gap *(verbless + "the {X} job" isn't an estimate reference — Task-8 stretch)* |
| `jot down on the {title} estimate: "..."` / `remember on this estimate that ...` / `FYI on the {title} job: "..."` (with an estimate/quote token) | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-06 — informal cues `jot`/`fyi`/`remember`/`write down` in `_NOTE_UPDATE_CUES` + value extractors (`_NOTE_WITH_COLON_SEP` broadened, new `_NOTE_REMEMBER_TAIL`); routed end-to-end by the orchestrator's value-bearing `_informal_note` arm. Always **append**-mode. Note: the phrase still needs an estimate/quote/EST token — "the Smith job" alone doesn't reference an estimate.)* |
| `write down on the {title} estimate that ...` | `update_estimate` → Estimate Agent | ⚠️ gap *(`write down` is a cue, but only `remember` has a `... that ...` tail extractor; needs the tail generalized)* |

**Disambiguation note:** `set the description of {WI} to "..."` (§1.5.3) targets a **work item** and is already ✅ rule. The phrasings here target the **estimate as a whole** — the implementation must detect the absence of a work-item reference (no `work item` / `job item` / `scope` / `line item` token) to route to the estimate-level handler rather than the work-item one.

**Implementation note (shipped 2026-06-06):** all update sub-handlers (description / notes / property-link) resolve the estimate by **code → `active_estimate_code` anaphora → "latest" → quoted-or-bare title** via the shared `_resolve_estimate_code_or_title`. Set-vs-append for notes follows the verb (`set`/`change`/`replace`/`overwrite`/`rewrite` + note → set; everything else, incl. all informal cues, → **append**, the non-destructive default). Dispatcher order in `_handle_update_estimate`: work-item ops → status → **description** → notes → property link → template (description sits above notes so a "description" cue never lands in the notes branch; work-item ops stay first so `description of {WI}` is untouched). **Remaining ⚠️ in this section:** value-before-cue (`put "X" as the overview`), `describe ... as` / `should be`, routing verbs `make`/`leave`/`tack`, a generalized `note ... that` tail, and "the {X} job" as an estimate reference (Task-8 stretch).

---

# 2. Properties

## 2.1 Direct imperatives (all ✅ rule)

| Phrasing | Intent → Agent |
|---|---|
| `create a new property` | `create_property` → Property Agent |
| `list all properties` | `list_properties` → Property Agent |
| `delete the property {property}` | `delete_property` → Property Agent |

## 2.2 Casual phrasings (all ✅ rule)

| Phrasing | Intent → Agent |
|---|---|
| `show me my properties` | `list_properties` → Property Agent |
| `what properties do I have?` | `list_properties` → Property Agent |
| `pull up property {property}` | `get_property` → Property Agent |

## 2.3 Possessive

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me {property}'s details` | `get_property` → Property Agent | ✅ rule |
| `what's {property}'s city?` | `get_property` → Property Agent | ✅ rule |
| `update {property}'s record` | `update_property` → Property Agent | ✅ rule |

## 2.4 Count (all ✅ rule)

`how many properties do I have?` · `count my properties` · `total number of properties`

## 2.5 Filter / find (all ✅ rule)

`find properties named Toronto` · `show properties in Toronto` · `search for properties matching Toronto`

## 2.6 Field-targeted update

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `change the city of {property} to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `update the city on {property} to Vancouver` | `update_property` → Property Agent | ✅ rule |
| `set {property}'s city to Vancouver` | `update_property` → Property Agent | ✅ rule |

## 2.7 Address formats accepted on create (all ✅ rule)

The regex fallback in `_extract_fields_from_message` parses these single-line formats so the user can supply a complete address in one message:

| Format | Example |
|---|---|
| Canadian, comma-separated with postal | `123 Main Street, Vancouver, BC, V1V 2A2` |
| Canadian, comma-separated with country | `123 Main Street, Vancouver, BC, Canada, V1V 2A2` (or postal-then-country) |
| Canadian, partial (street + city + state) | `888 River Road, Richmond, BC` |
| Canadian, "at" prefix space-separated state | `at 123 Maple Drive, Surrey BC V3T 4R5` |
| **US, "City, ST ZIP"** (no comma between state and ZIP) | `155 Asharoken Ave, Northport, NY 11768` |
| **US, ZIP+4** | `155 Asharoken Ave, Northport, NY 11768-1234` |

Comma-less unformatted addresses (`1036 Fort Salonga Rd Northport NY`) are intentionally **not** parsed by regex — the LLM entity extractor handles them.

## 2.8 Verbless (all ✅ rule — Phase 2a address-pattern resolver)

| Phrasing | Intent → Agent |
|---|---|
| `{property}` (bare address) | `get_property` → Property Agent |
| `I want the details for {property}` | `get_property` → Property Agent |
| `tell me about {property}` | `get_property` → Property Agent |

## 2.9 Property gaps

No outstanding property-specific gaps in scope for the current backlog. Cross-resource phrasings (e.g. `who lives at {property}?`) are tracked under §7.

---

# 3. Contacts

## 3.1 Direct imperatives (all ✅ rule)

`create a new contact` · `list all contacts` · `delete the contact {contact}`

## 3.2 Casual phrasings (all ✅ rule)

`show me my contacts` · `what contacts do I have?` · `pull up contact {contact}`

## 3.3 Possessive

| Phrasing | Status |
|---|---|
| `show me {contact}'s details` | ✅ rule |
| `what's {contact}'s phone?` | ✅ rule |
| `update {contact}'s record` | ✅ rule |

## 3.4 Count (all ✅ rule)

`how many contacts do I have?` · `count my contacts` · `total number of contacts`

## 3.5 Filter / find (all ✅ rule)

`find contacts named Smith` · `show contacts in Toronto` · `search for contacts matching Smith`

## 3.6 Field-targeted update

| Phrasing | Status |
|---|---|
| `change the phone of {contact} to 555-1111` | ✅ rule |
| `update the phone on {contact} to 555-1111` | ✅ rule |
| `set {contact}'s phone to 555-1111` | ✅ rule |

## 3.7 Verbless (all ✅ rule — Phase 2b person-name heuristic)

`{contact}` (bare name) · `I want the details for {contact}` · `tell me about {contact}`

## 3.8 Contact gaps

No outstanding contact-specific gaps in scope for the current backlog. Cross-resource phrasings (e.g. `where does {contact} live?`) are tracked under §7.

---

# 4. Materials

## 4.1 Direct imperatives (all ✅ rule)

`create a new material` · `list all materials` · `delete the material {material}`

## 4.2 Casual phrasings (all ✅ rule)

`show me my materials` · `what materials do I have?` · `pull up material {material}`

## 4.3 Possessive

| Phrasing                         | Intended behavior          | Status |
| -------------------------------- | -------------------------- | ------ |
| `show me {material}'s details`   | `get_material`             | ✅ rule |
| `what's {material}'s price?`     | `get_material` field focus | ✅ rule |
| `update {material}'s record`     | `update_material`          | ✅ rule |

## 4.4 Count

| Phrasing                                  | Intended behavior | Status |
| ----------------------------------------- | ----------------- | ------ |
| `how many different materials do I have?` | count materials   | ✅ rule |
| `how many types of materials do I have?`  | count materials   | ✅ rule |
| `how many materials do I have?`           | count materials   | ✅ rule |
| `count my materials`                      | count materials   | ✅ rule |

The "different" / "types of" modifiers don't change the routing — `how many` already pins the action to ``list`` and the trailing ``materials`` pins the domain. Confirmed via `material_query_variants` coverage category.

## 4.5 Filter / find (all ✅ rule)

`find materials named concrete` · `show materials in in stock` · `search for materials matching concrete`

## 4.6 Field-targeted update (material-level)

| Phrasing | Status |
|---|---|
| `change the price of {material} to $5` | ✅ rule |
| `update the price on {material} to $5` | ✅ rule |
| `set {material}'s price to $5` | ✅ rule |

Closed by Phase 2 of xfail-wave-1 — `_match_possessive_or_field_targeted` resolves the missing material domain via `FIELD_TO_DOMAIN["price"] → material` plus the material-shape residual on the captured entity name.

## 4.7 Verbless (all ✅ rule — Phase 2b material-shape residual)

`{material}` · `I want the details for {material}` · `tell me about {material}`

## 4.8 Size-scoped operations *(shipped in Phase B — all ✅ rule)*

All size-scoped phrasings require an explicit `size <X>` token to fire. Material Agent's `_build_sizes_from_fields` handles the payload; `_handle_update_material` enforces the last-size refusal and add-size missing-field refusal.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `find material {material} with size {size}` | `get_material` (size-scoped) | ✅ rule |
| `how much is {material} with size {size}?` | `get_material` (size-scoped) | ✅ rule |
| `update the cost for {material} with size {size} to $5` | `update_material` (size-scoped cost) | ✅ rule |
| `update the price for {material} with size {size} to $5` | `update_material` (size-scoped price) | ✅ rule |
| `delete size {size} for {material}` | `update_material` (size_op=remove) | ✅ rule |
| `add size {size} to {material} with cost $8 and unit each` | `update_material` (append) | ✅ rule |

**Invariants:**
- **Last-size delete refusal** — cannot remove the only remaining size on a material. Copy: *"I can't remove the last size from this material — it needs at least one size. Add another size first, or delete the material entirely if that's what you mean."*
- **Add-size requires BOTH cost and unit** — `add size {size} to {material} with cost $8` (no unit) refuses and prompts for the unit. Same if cost is missing.

## 4.9 Material gaps

| Phrasing | Intended behavior | Status |
|---|---|---|
| `How much does {material} cost?` | `get_material` field focus | ✅ rule *(closed in xfail-wave-3 Workstream B — non-possessive cost-query rule in orchestrator)* |
| `list materials under $10` | `list_materials` with price range | ✅ rule *(closed in xfail-wave-3 Workstream B — `_parse_price_range_filter` in `agents/material/service.py` filters the list response by `under/over/below/above $N`)* |
| `rename size {old} to {new} for {material}` | `update_material` (size_op=rename) | ✅ rule *(closed in xfail-wave-3 Workstream B — orchestrator `_match_size_scoped_material_op` rule routes the rename verb)* |
| `show all sizes for {material}` | `get_material` | 🤖 LLM |
| `how much does {size} of {material} cost?` | `get_material` (size-scoped) | ✅ rule *(May expansion — "of" form cost query pattern)* |
| `what is the price of {size} of {material}?` | `get_material` (size-scoped) | ✅ rule *(May expansion)* |
| `what category is material {material}?` | `get_material` (category focus) | ✅ rule *(May expansion — `_match_field_specific_query` before help classifier)* |
| `what category is {material}?` | `get_material` (category focus) | ✅ rule *(May expansion)* |

## 4.10 Qualifier list — "what {X} materials do I have?" *(2026-06-02)*

A qualifier `{X}` between the lead-in and the `materials` noun is matched as a
**substring against the material name OR its category name** (case-insensitive).
`_extract_list_qualifier` lifts `{X}` out of the phrasing (rule tier) and
`_find_materials_by_name_or_category` does the OR-match. A bare list with no
qualifier (`what materials do I have?`, §4.2) still lists everything — the
generic-word guard drops a non-qualifier capture.

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what {X} materials do I have?` | `list_materials` (name ∪ category substring) | ✅ rule |
| `show me my {X} materials` | `list_materials` | ✅ rule |
| `list my {X} materials` | `list_materials` | ✅ rule |
| `do I have any {X} materials?` | `list_materials` | ✅ rule |
| `which {X} materials do I have?` | `list_materials` | ✅ rule |
| `how about {X} materials?` / `what about {X} materials?` / `and {X} materials?` | `list_materials` | ✅ rule *(follow-up phrasings — the "how about" lead-in would otherwise trip `is_help_query`, so the orchestrator `_match_material_list_filter` fast-path routes these before the help classifier. It reuses the agent's `_LIST_QUALIFIER_PATTERN` so routing and qualifier extraction never drift.)* |
| `how many {X} materials do I have?` | `list_materials` (count of category {X}) | ✅ rule *(count-by-category — resolves a whole-word category for count queries; falls back to all when {X} isn't a category)* |

**Disambiguation:** `material units` / `material categories` / `material types` are NOT treated as "{X} materials" lists — a negative lookahead on `_LIST_QUALIFIER_PATTERN` keeps those routing to their help/enum or category handlers.

---

# 5. People (roles) — a.k.a. Labor

Labor = catalog of **role definitions** (Landscaper, Foreman, Operator). Individuals go under Contact.

## 5.1 Direct imperatives (all ✅ rule)

`create a new labour role` · `list all labour roles` · `delete the labour role {role}`

## 5.2 Casual phrasings (all ✅ rule)

`show me my labour roles` · `what labour roles do I have?` · `pull up labour role {role}`

## 5.3 Possessive

| Phrasing | Status |
|---|---|
| `show me {role}'s details` | ✅ rule |
| `what's {role}'s cost?` | ✅ rule |
| `update {role}'s record` | ✅ rule |

## 5.4 Count (all ✅ rule)

`how many labour roles do I have?` · `count my labour roles` · `total number of labour roles`

## 5.5 Filter / find (all ✅ rule)

`find labour roles named Foreman` · `show labour roles in outdoor` · `search for labour roles matching Foreman`

## 5.6 Field-targeted update

| Phrasing | Status |
|---|---|
| `change the cost of {role} to $50` | ✅ rule |
| `update the cost on {role} to $50` | ✅ rule |
| `set {role}'s cost to $50` | ✅ rule |

## 5.7 Verbless (all ✅ rule — DOMAIN_HINTS include role names)

`{role}` · `I want the details for {role}` · `tell me about {role}`

## 5.8 Role field queries (all ✅ rule — May expansion)

"What's the X for role Y?" phrasings route to `get_labour` via `_match_field_specific_query` in the orchestrator (runs before `is_help_query`).

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `what's the average wage for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |
| `what's the rate for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |
| `what's the labor burden for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |
| `what's the unbillable rate for the role {role}?` | `get_labour` → Labour Agent | ✅ rule |

Note: "labor burden" and "unbillable rate" are company-level settings, not per-role fields. The Labour Agent's get response shows the role's Avg. Wage and computed Rate. The explanation of how rate is computed (wage + unbillable% + labor burden%) is provided when users attempt to edit rate directly.

## 5.9 People gaps

No outstanding people-specific gaps in scope for the current backlog. Cross-resource phrasings (e.g. `which properties need a {role}?`) are tracked under §7.

---

# 6. Templates

Templates are reusable estimate blueprints — a predefined set of materials, activities, and cost parameters that can be applied when creating estimates. Managed via the Templates page in the portal. The API supports full CRUD plus a duplicate operation (`POST /templates/id/{id}/duplicate`).

Key fields: `name` (required, unique per company), `description`, `division`, `recurring` (bool), `profit_margin`, `overhead_allocation`, `labor_burden`, `tax`, `size` + `unit` (baseline dimensions), and embedded `materials` / `activities` lists.

## 6.1 Direct imperatives

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `list all templates` | `list_templates` → Template Agent | ✅ rule |
| `delete the template {template}` | `delete_template` → Template Agent | ✅ rule |

Template **creation** is refused — see §8.5. Users must create templates through the Templates page in the portal UI.

## 6.2 Casual phrasings

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me my templates` | `list_templates` → Template Agent | ✅ rule |
| `what templates do I have?` | `list_templates` → Template Agent | ✅ rule |
| `pull up template {template}` | `get_template` → Template Agent | ✅ rule |

## 6.3 Possessive

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `show me {template}'s details` | `get_template` → Template Agent | 🤖 LLM |
| `what's {template}'s description?` | `get_template` → Template Agent | 🤖 LLM |

## 6.4 Count

`how many templates do I have?` · `count my templates` · `total number of templates`

All ✅ rule — routes to `list_templates` → Template Agent with count response.

## 6.5 Filter / find

`find templates named Driveway` · `search for templates matching Driveway`

All ✅ rule — routes to `list_templates` → Template Agent.

Template **update** and **duplicate** are refused — see §8.5. Users must edit and copy templates through the portal UI.

## 6.6 Verbless

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `{template}` (bare template name) | `get_template` → Template Agent | 🤖 LLM |
| `I want the details for {template}` | `get_template` → Template Agent | 🤖 LLM |
| `tell me about {template}` | `get_template` → Template Agent | 🤖 LLM |

## 6.7 Apply template to estimate

| Phrasing | Intent → Agent | Status |
|---|---|---|
| `use template {template} in the estimate {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `apply template {template} to {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `apply {template} to the estimate` | `update_estimate` → Estimate Agent | ✅ rule |
| `apply template {template} to estimate {title}` | `update_estimate` → Estimate Agent | ✅ rule *(2026-06-09 — title-aware: targets the named estimate over `active_estimate_code`. A named estimate that **doesn't exist** is REFUSED with a warning — it does NOT silently create a new estimate under that name.)* |
| `use the {template} template for {EST}` | `update_estimate` → Estimate Agent | ✅ rule |
| `create an estimate from template {template}` | `update_estimate` → Estimate Agent | ✅ rule *(creates a new draft estimate and applies the template as a work item — the no-named-target bootstrap path)* |

### Template-driven create (2026-06-02) — skips AI generation

When a **create-estimate** request names a template, `delegate_create_estimate` detects it (`detect_template_in_create_request`) and routes to template instantiation instead of AI generation — no material/activity questions. Linear scaling by job size when the template has a **baseline** (`size` + `unit`).

| Phrasing | Behavior | Status |
|---|---|---|
| `create an estimate ... use the {template} template` (no baseline) | Create a draft, template applied as one work item, verbatim (1×). Property context linked. | ✅ rule |
| `create an estimate, 600 sq ft, using the {template} template` (baseline + size in request) | Scale the template linearly (`factor = job_size ÷ baseline_size`); size taken from the request, not re-asked. | ✅ rule |
| `create an estimate using the {template} template` (baseline, no size) | Ask "What's the size of this job (in {baseline unit})?" (`pending_template_size`), then scale on reply. | ✅ rule |
| reply with size in a **convertible** unit (sq yd↔sq ft, lin yd↔lin ft) | Converted to the baseline unit, then scaled. | ✅ rule |
| reply with an **incompatible** unit (area vs length) | Re-asks for the size in the baseline's unit. | ✅ rule |
| `No` / `skip` to the size question | Instantiate at the baseline (1×) and proceed (no cancel). | ✅ rule |
| `cancel` / `never mind` to the size question | Cancels the estimate request. | 🛑 cancel |

**Scaling** (`agents/estimate/template_scaling.py`): multiplies material/labour/equipment quantities, activity effort, and the work-item `sub_total` by the factor; prices/rates unchanged. Linear across all line items — no per-item fixed-fee exemption. Pre-handler: `handle_pending_template_size` in `routers/agent_helpers/template_estimate.py`.

## 6.8 Template gaps

Orchestrator routing, refusal guard, and Template Agent are implemented. Possessive (§6.3) and verbless (§6.6) phrasings are 🤖 LLM — they rely on the LLM classifier since template names lack a rule-tier entity-shape heuristic. Template creation, update, and duplicate are explicitly refused (§8.5).

Additional cross-resource phrasings (e.g. `which templates include {material}?`) are future candidates — not tracked here yet.

---

# 7. Cross-resource / implicit relationships

Questions users ask when they think about the domain rather than the database. Routing is via `_match_cross_resource_query` in the orchestrator (Wave 2 Phase 1); the join is performed by the target agent reading a `filter_by` payload off `context` (Wave 2 Phase 2). Direct lookups (Property↔Contact) hit the linked-id list on the Property document; transitive joins (material/labour → property) go through the Estimate collection's embedded `materials.material` / `labours.labour` lists.

## 7.1 Property ↔ Contact

| Phrasing | Intended behavior | Status |
|---|---|---|
| `who lives at {property}?` | `list_contacts` filtered by property | ✅ rule |
| `what contacts are at {property}?` | `list_contacts` filtered by property | ✅ rule |
| `who owns {property}?` | `list_contacts` filtered by property + role=owner | ✅ rule |
| `what properties does {contact} own?` | `list_properties` filtered by contact | ✅ rule |
| `where does {contact} live?` | `list_properties` filtered by contact | ✅ rule |
| `show me {contact}'s properties` | `list_properties` filtered by contact | ✅ rule (possessive flow) |
| `which properties does contact {contact} linked to?` | `list_properties` filtered by contact | ✅ rule *(May expansion — new "linked to" cross-resource pattern)* |
| `show me (all) properties contact {contact} linked to` | `list_properties` filtered by contact | ✅ rule *(May expansion)* |

## 7.2 Material → Property / Estimate

| Phrasing | Intended behavior | Status |
|---|---|---|
| `which properties use {material}?` | `list_properties` joined via estimates | ✅ rule |
| `where is {material} used?` | `list_properties` joined via estimates | ✅ rule |
| `find estimates with {material}` | `list_estimates` filtered by material | ✅ rule (plural-aware list flip) |

## 7.3 Labour → Property / Estimate

| Phrasing | Intended behavior | Status |
|---|---|---|
| `which properties need a {role}?` | `list_properties` joined via estimates | ✅ rule |
| `what estimates use the {role} role?` | `list_estimates` filtered by labour | ✅ rule |
| `show me jobs needing a {role}` | `list_properties` joined via estimates | ✅ rule (plural-aware list flip) |

---

# 8. Safety refusals

## 8.1 Bulk delete — 🛑 refused

Phrasings with quantifier + delete verb. Enforced at the orchestrator layer AND defensively at each domain agent's `process()`. Verbs: `delete`, `remove`, `drop`, `wipe`, `clear`. **Note:** `clear all {resource}` (e.g. "clear all estimates") **is** treated as a bulk delete and refused — the May 2026 "remove clear" change was reverted (2026-06-02). The one exemption is estimate/quote **creation** requests whose job description mentions clearing/removing work ("create an estimate to clear out all the weeds in my backyard") — these are detected by `is_estimate_creation_request()` and pass through to `create_estimate`, never the refusal guard.

| Phrasing | Behavior |
|---|---|
| `delete all {plural}` | 🛑 refusal message, `needs_clarification=True` |
| `remove every {singular}` | 🛑 refusal |
| `wipe my {plural}` | 🛑 refusal |
| `clear all {plural}` | 🛑 refusal |
| `create an estimate to clear out all the {stuff}` | ✅ `create_estimate` (not refused) |

Applies to all 4 CRUD resources. Maple-only policy — HTTP routers may still expose bulk delete for UI workflows.

## 8.2 Equipment — 🛑 refused

Equipment isn't a Maple resource. Any phrasing mentioning equipment (excavator, skid steer, bobcat, etc.) refuses with `EQUIPMENT_REFUSAL_MESSAGE`.

| Phrasing | Behavior |
|---|---|
| `show all my equipment` | 🛑 refusal |
| `create a new equipment` | 🛑 refusal |
| `delete the excavator equipment` | 🛑 refusal |

## 8.3 Material category management — 🛑 refused

Material categories (Hardscape, Masonry, etc.) live in the catalog UI. Maple can list/filter/reassign but not create/rename/delete them.

| Phrasing | Behavior |
|---|---|
| `create a new category` | 🛑 refusal via `is_material_category_management_request` |
| `rename the Masonry category` | 🛑 refusal |
| `delete the Hardscape category` | 🛑 refusal |

## 8.4 Partial bulk / small-N destructive — 🛑 refusal

| Phrasing | Intended behavior | Status |
|---|---|---|
| `delete the last 5 contacts` | Refuse (N > 1 but not "all") | 🛑 refusal — extended `_BULK_DELETE_PATTERNS` to catch `last/first/next/previous N` quantifiers (xfail-wave-3 Workstream A) |
| `remove the first 10 properties` | Refuse | 🛑 refusal |
| `drop the next 3 materials` | Refuse | 🛑 refusal |

## 8.5 Template creation / update / duplicate — 🛑 refused

Templates must be created, edited, and duplicated through the Templates page in the portal UI. Maple can list, view, delete, and apply templates to estimates — but not create, update, or copy them.

| Phrasing | Behavior |
|---|---|
| `create a new template` | 🛑 refusal — directs user to the Templates page |
| `add a template` | 🛑 refusal |
| `make a new template called Driveway` | 🛑 refusal |
| `update {template}'s description` | 🛑 refusal |
| `change the profit margin of {template} to 20` | 🛑 refusal |
| `duplicate template {template}` | 🛑 refusal |
| `copy template {template}` | 🛑 refusal |

## 8.6 Illegal status transitions — 🛑 refused *(2026-06-11)*

The estimate status state machine (`ESTIMATE_STATUS_TRANSITIONS` in `models/estimate.py`) is enforced in chat, matching the PUT route and the FE. The refusal names the current status and lists the legal next statuses. Whether a phrasing is refused depends on the estimate's **current** status, not the wording.

| Phrasing (example) | Current status | Behavior |
|---|---|---|
| `mark {EST} as won` | Draft | 🛑 refusal — Draft can only go to Sent, On Hold, Archived |
| `update {EST} to Review status` | Draft | 🛑 refusal — same rule |
| `archive {EST}` | Won | 🛑 refusal — Won can only go to Scheduled, On Hold, Lost |
| `mark {EST} as draft` | Scheduled | 🛑 refusal — Scheduled can only go to Completed |
| `mark {EST} as won` | Sent | ✅ allowed — Sent/Approved → anything (the "unsend" rule), **Owner/Admin only** |

Internal lifecycle states (`Generating`, `Failed`, `Deleted`) were already refused as targets regardless of current status; legacy/unknown stored statuses are not blocked (fail-open so old data isn't stranded).

**Authorization (2026-06-11 follow-up)** — legal edges are additionally role-gated, mirroring the HTTP layer:

| Operation | Who can do it | Refusal behavior |
|---|---|---|
| Send (→ Sent) / unsend (Sent/Approved → anything) | Owner or Admin | 🛑 warm refusal pointing the user to an Owner/Admin |
| Archive / unarchive | Owner, Admin, or the estimate's creator (`created_by_email`, case-insensitive) | 🛑 warm refusal naming who can do it |
| All other legal edges (e.g. Won → Scheduled) | Any authenticated user | ✅ |
| Any gated op with no identity in context | — | 🛑 fail closed ("I wasn't able to confirm your permissions…") |

All refusal copy follows Maple's persona (`agents/maple_persona.py`): first-person, apologetic, plain words, and always a next step — never a bare "permission denied".

## 8.7 Edits to locked-status estimates — 🛑 refused *(2026-06-11, tightened 2026-06-12)*

Mirrors the portal's `isEditableStatus`: estimate contents are editable **only in Draft or Review**. Enforced once in `_load_estimate_for_update` (allowlist `_EDITABLE_ESTIMATE_STATUSES`), the shared loader for every estimate edit sub-op (notes, description, link property, apply template, all work-item operations). Reads (`get_estimate`, work-item queries) are unaffected; status changes go through the §8.6 transition path instead.

| Current status | Edit attempt (any sub-op) | Behavior |
|---|---|---|
| Draft / Review | `add a note to {EST}: "…"`, `remove work item 1 from {EST}`, … | ✅ normal flow |
| Archived | same | 🛑 refusal — "…is archived… ask me to unarchive it first" |
| Sent / legacy Approved | same | 🛑 refusal — "…locked for edits… move it back to Draft or Review first" |
| On Hold / Lost | same | 🛑 refusal — Draft-or-Review rule + "ask me to move it to Review first" (one-hop path exists) |
| Won / Scheduled / Completed (and internal statuses) | same | 🛑 refusal — Draft-or-Review rule, no one-hop path offered |
| Sent / Approved | unsend status change (e.g. `move {EST} back to Review`) | ✅ allowed via the status-transition path (Owner/Admin only, §8.6) |
| Archived | `unarchive {EST}` | ✅ allowed via the status-transition path (Owner/Admin or creator, §8.6) |

Legacy/unknown stored statuses fail open so old data isn't stranded. The HTTP PUT route still locks only Sent/Approved/Archived — the UI/chat-vs-API gap is tracked as follow-up #349.

---

# 9. Multi-turn patterns

## 9.1 Field-then-value flow (all 4 CRUD resources)

User responds to "What fields should I update?" with a bare field name:

```
User: update Landscaper
Maple: What fields should I update? (options: cost, description, ...)
User: cost
Maple: What's the new cost?
User: $50
Maple: I've updated the cost for Landscaper for you.
```

Pending-intent slot: `awaiting_value_for`. Canonical implementation: `agents/property/service.py`.

## 9.2 Add-size missing-field flow (materials)

When user says "add size {size} to {material}" without providing cost or unit:

```
User: add size 24x24 to concrete blocks with cost $8
Maple: I need a unit for size '24x24' on concrete blocks. Try again with cost and unit — for example: "add size 24x24 to concrete blocks with cost $10 and unit each".
```

Currently refuses and requests a retry with complete info (pending-intent persistence is a future UX refinement).

## 9.3 Calculation continuation flow (Calculator Agent) ✅

When the Calculator Agent asks for a missing parameter (area, depth, etc.), it
stores a `pending_calculation` record in the conversation context. On the next
turn the router pre-handler `handle_pending_calculation`
(`routers/agent_helpers/pending_calculation.py`) merges the user's reply into
the pending calculation **before** orchestrator classification — so a bare or
units-only answer is no longer misrouted to the Property Agent.

```
User: how many square feet, at 3-inches, will a yard of mulch cover
Maple: I can help with mulch coverage calculation! I just need a couple more details:
       - the area (in square feet)?
User: 750 square feet          ← absorbed as area_sqft, no longer "I couldn't find any matching properties"
Maple: Here's your mulch calculation: … Total needed: 6.94 cubic yards
```

- A bare number ("750") fills the single outstanding field.
- A reply that supplies only some of the missing fields re-asks for the rest,
  keeping the pending state.
- **Pivot drops silently:** a value-less reply that clearly matches a different
  intent (a CRUD command, or a fresh full calculation query) abandons the
  pending calculation and falls through to normal routing.

Pending-state slot: `pending_calculation`. Continuation logic:
`CalculatorAgent.continue_pending()` +
`text_helpers.extract_continuation_values()`. Tests:
`tests/test_agent_helpers_pending_calculation.py`,
`tests/test_calculator_agent.py::TestContinuePending`,
`tests/test_calculator_text_helpers.py::TestExtractContinuationValues`.

> Note: re-engagement phrasings ("can you help with mulch coverage?") and
> inverse-coverage math ("how many sq ft will a yard cover" → solve for area)
> remain unsupported by design (out of scope for the continuation fix).

## 9.3.1 Calculation catalog (Calculator Agent) ✅

Each type is one `CalcSpec` in `agents/calculator/registry.py` → one pure
function in `formulas.py`. The LLM only extracts parameters; all arithmetic is
deterministic. Adding a type is a single registry entry + formula.

| Calculation type | Example phrasing | Required inputs | Output | Status |
|---|---|---|---|---|
| `area_coverage` | "how many cubic yards of mulch for 2000 sq ft at 3 inches" | area_sqft, depth_inches | cubic yards | ✅ rule |
| `concrete_volume` | "how much concrete for a 10x12 slab 4 inches thick" | length_ft, width_ft, depth_inches | cubic yards | ✅ rule |
| `seed_coverage` | "how many lbs of grass seed for 5000 sq ft at 4 lbs/1000" | area_sqft, application_rate | pounds | ✅ rule |
| `linear_material` | "how many 8-ft fence panels for 100 linear feet" | linear_ft (opt. piece_length_ft) | pieces | ✅ rule |
| `paver_count` | "how many 12x12 pavers for 200 sq ft" | area_sqft, paver_length_inches, paver_width_inches | pieces | ✅ rule |
| `unit_conversion` | "convert 100 sq ft to sq m" | value, from_unit, to_unit | converted value | ✅ rule |
| `aggregate_tons` | "how many **tons** of gravel for 100 sq ft 4 inches deep" | area_sqft, depth_inches (opt. tons_per_cubic_yard, default 1.5) | tons | ✅ rule *(2026-06-15)* |
| `mulch_bags` | "how many **bags** of mulch for 100 sq ft at 3 inches" | area_sqft, depth_inches (opt. bag_size_cuft, default 2) | bags | ✅ rule *(2026-06-15)* |
| `retaining_wall_blocks` | "how many blocks for a 20 ft wall 3 ft high with 12x8 blocks" | wall_length_ft, wall_height_ft, block_length_inches, block_height_inches | blocks | 🤖 LLM *(2026-06-15 — regex doesn't extract block dims; LLM extraction path)* |
| `step_count` | "how many steps for a 42 inch rise" | total_rise_inches (opt. target_riser_inches, default 7) | steps | 🤖 LLM *(2026-06-15)* |
| `plant_count` | "how many plants for 100 sq ft at 12 inch spacing" (opt. "triangular spacing") | area_sqft, spacing_inches (opt. pattern square/triangular, default square) | plants | 🤖 LLM *(2026-06-15 — regex defers: "12 inch spacing" is spacing not depth)* |

All accept an optional `waste_factor_pct` ("with 10% waste") except
`step_count` and `unit_conversion`. The missing-parameter continuation flow in
§9.3 applies to every type: a bare number fills a single outstanding field, and
natural-language replies are matched for the common dimension phrasings
("20 feet long", "3 feet high", "8 inch spacing", "42 inch rise").

For area-based calculations, `area_sqft` is **derived from length × width** when
the user gives dimensions instead of an area (e.g. "the bed is 45 feet long and
6 feet wide" → 270 sq ft) — Maple won't re-ask for area it can compute. The
multiplication is done in code (`_derive_implied_params`), never by the LLM.

> **Deferred by design:** grading pitch (2% / quarter-inch-per-foot) and
> irrigation/drainage hydraulics (TDH, GPM, runoff, pipe sizing). The hydraulics
> set carries install/liability risk and needs reviewed engineering formulas —
> tracked for a separate phase.

## 9.4 Post-creation "link to a property?" follow-up ✅ implemented *(2026-06-06)*

After an estimate is created **without** a linked property, Maple appends an optional follow-up question to the response: *"Would you like me to link this estimate to a property now?"* (`extraction_helpers.build_optional_follow_up`, surfaced in `agents/estimate/service.py:907`). The reply is now handled by the **generic pending-optional-follow-up state machine** (`routers/agent_helpers/optional_follow_up.py`):

- `("Estimate Agent", "create_estimate", "property")` is registered in the `get_optional_follow_up_spec` allowlist; `delegate_create_estimate.py` persists the pending record and seeds `active_estimate_code` on the create turn.
- **The legacy `pending_estimate_follow_up` flow is superseded** for this combo: the create path no longer dual-writes the legacy key (it remains only as a fallback when the generic spec isn't registered), and the legacy handler defers (`return None`) whenever the generic key is present. This handler-priority conflict — the legacy handler swallowing the reply — was the root cause of the original "Maple could not handle it" report.
- **One-turn affirmative+value**: a confirm-stage reply carrying residual content after the affirmation ("Yes, link it to Bob Residential") strips the affirmation + any link-verb preamble and delegates a synthetic `set the property of this estimate to Bob Residential` to the Estimate Agent (resolved via `active_estimate_code` anaphora). This residual shortcut is generic — contact-email/material-size follow-ups also gain one-turn completion.

```
Maple: I've created the estimate for you. … Would you like me to link this estimate to a property now?
User:  Yes, link it to Bob Residential
Maple: I've linked estimate EST-… to Bob Residential for you.   ← one turn (2026-06-06)
```

| Phrasing (turn 2, after the offer) | Intended behavior | Status |
|---|---|---|
| `Yes, link it to {property}` | one-turn: strip affirmation + link-verb preamble → `set the property of this estimate to {property}` → Estimate Agent | ✅ rule *(2026-06-06 — confirm-stage residual shortcut)* |
| `yeah, it's for {address}` / `sure, the {property} property` / `yep, tie it to the {property} property` / `yes please, link to {property}` / `go ahead — {property}` | one-turn: same residual shortcut (`_AFFIRMATION_PREFIX` covers yeah/yep/yup/sure/ok/please/go ahead/…) | ✅ rule *(2026-06-06 — the residual is re-parsed by the link handler's name/address extraction, so "it's for …" phrasings resolve via the address/name in the text)* |
| **bare property answer** — `{property}` / `{address}` / `link it to {address}` (no yes/no word) | the answer *is* the value while the slot is open → link | ✅ rule *(2026-06-06 — verified: a non-affirmative, non-negative, non-pivot reply at the confirm stage is treated as the collect-value answer)* |
| `Yes` (no property named) | re-ask: "Which property should I link estimate '{EST}' to?" | ✅ rule *(2026-06-06)* |
| `No` / `not now` / `no thanks` / `maybe later` | acknowledge, clear the slot, leave unlinked | ✅ rule *(2026-06-06 — these are in the `_NEGATIVE_VALUES` lexicon)* |
| `not right now` / `I'll do it from the portal` / `nah, leave it` | acknowledge, clear the slot, leave unlinked | ⚠️ gap *(NOT in the exact-match `_NEGATIVE_VALUES` lexicon (`routers/agent_helpers/text_helpers.py`) — currently treated as a property-name answer; the link lookup fails and re-prompts. Fix: extend the lexicon or add a soft-negative prefix check.)* |
| **pivot** — next message is clearly a fresh request (a new CRUD command or question) | drop the slot silently, route normally | ✅ rule *(pre-existing escape hatch in `handle_pending_optional_follow_up`; guard now documented inline)* |

**Remaining ⚠️ in this section:** soft-negative phrasings not in the exact-match lexicon (`not right now`, `I'll do it from the portal`, `nah, leave it`) are treated as a property-name answer — extend `_NEGATIVE_VALUES` or add a soft-negative prefix check in `routers/agent_helpers/text_helpers.py`. Tests: `tests/test_maple_estimate_field_edits.py::TestEstimateOptionalFollowUp` + `::TestEstimateFollowUpConfirmStage` (incl. the legacy-defers ordering test) and `tests/test_agent_helpers_delegate_create_estimate.py`.

---

# 10. Help intent

Handled by `agents/orchestrator/help_handler.py` via the `HelpHandler` class. The orchestrator routes to it when `is_help_query()` returns True (see `agents/orchestrator/intents.py:296`). The agent is always the **Orchestrator Agent** itself — help never dispatches to a downstream domain agent.

Three topic families, in order of priority inside `HelpHandler.detect_topic()`:

1. **Enum queries** — contact roles, estimate statuses, estimate divisions. Returns the enum's valid values plus a `valid_values` list in the result payload.
2. **Capabilities** — "what can you do?". Returns the `SUPPORTED_INTENTS_BY_AGENT` mapping under `result.capabilities`.
3. **Procedural (how-to)** — instructional patterns like "how do I", "steps to", "walk me through". Attempts to load a user guide from `user_guides/content.py`; falls back to a contextual example from `_CONTEXTUAL_EXAMPLES` if no guide exists.

The result payload always has `operation="help"`, `read_only=True`, and an `intent="help"` on the envelope. Help queries are rule-only — they bypass the LLM even when `use_llm=True` (see `test_orchestrator_help_query_bypasses_llm`).

## 10.1 Capability queries

Direct capability questions. Match via `HELP_DIRECT_HINTS` (`intents.py:184`).

| Phrasing | Topic | Status |
|---|---|---|
| `help` | `capabilities` | ✅ rule |
| `help me` | `capabilities` | ✅ rule |
| `help please` | `capabilities` | ✅ rule |
| `I need help` | `capabilities` | ✅ rule |
| `what can you help me with?` | `capabilities` | ✅ rule |
| `what can you do?` | `capabilities` | ✅ rule |
| `how can you help me?` | `capabilities` | ✅ rule |
| `what can I ask?` | `capabilities` | ✅ rule |
| `supported intents` | `capabilities` | ✅ rule |
| `capabilities` | `capabilities` | ✅ rule |

## 10.2 Enum queries

Match via `HELP_ENUM_KEYWORDS` + `HELP_QUESTION_CUES` (`intents.py:194-218`). `HelpHandler.detect_topic()` disambiguates by domain keyword.

### Contact roles — returns `["Home Owner", "Manager", "Administrator"]`

| Phrasing | Status |
|---|---|
| `what are the contact roles?` | ✅ rule |
| `what are the valid contact roles?` | ✅ rule |
| `what roles are available?` | ✅ rule |
| `what are the valid roles for a contact?` | ✅ rule |
| `available values for role` | ✅ rule |
| `choices for contact role` | ✅ rule |

### Estimate statuses — returns the 10 EstimateStatus enum values

| Phrasing | Status |
|---|---|
| `what are the estimate statuses?` | ✅ rule |
| `what statuses can an estimate have?` | ✅ rule |
| `what are the valid estimate statuses?` | ✅ rule |

### Estimate divisions — returns EstimateDivision enum values

| Phrasing | Status |
|---|---|
| `what are the estimate divisions?` | ✅ rule |
| `what are the valid estimate divisions?` | ✅ rule |
| `which divisions can an estimate have?` | ✅ rule |

## 10.3 Procedural how-to queries

Match via `HELP_INSTRUCTIONAL_PATTERNS` (`intents.py:220-237`): `how do i`, `how can i`, `how to`, `how would i`, `how should i`, `steps to`, `step by step`, `process for`, `process to`, `guide for`, `guide to`, `explain how`, `show me how`, `walk me through`, `what are the steps`, `what's the process`.

When an instructional pattern hits, `detect_topic()` tries to match an action keyword (`create`, `update`, `delete`, `list`, `get`, `find`, `add`, `edit`, `remove`) and a domain keyword (`contact(s)`, `estimate`/`quote(s)`, `property`/`properties`, `material(s)`, `labour`/`labor`). Result is a `how_to_<action>_<domain>` topic; falls back to `how_to_manage_<domain>s` if only domain matched, or `how_to_use_system` if neither.

### Full how-to (action + domain matched)

| Phrasing                             | Topic                     | Status                                                       |
| ------------------------------------ | ------------------------- | ------------------------------------------------------------ |
| `how do I create an estimate?`       | `how_to_create_estimate`  | ✅ rule (guide loaded from `user_guides/content.py`)          |
| `how do I update a contact?`         | `how_to_update_contact`   | ✅ rule (guide loaded)                                        |
| `how do I create a contact?`         | `how_to_create_contact`   | ✅ rule (guide loaded)                                        |
| `how do I create a property?`        | `how_to_create_property`  | ✅ rule (guide loaded)                                        |
| `how do I archive an estimate?`      | `how_to_manage_estimates` | ✅ rule *(no action keyword "archive", falls back to manage)* |
| `steps to add a material`            | `how_to_add_material`     | ✅ rule (no guide; contextual example)                        |
| `explain how to create an estimate`  | `how_to_create_estimate`  | ✅ rule                                                       |
| `walk me through making a contact`   | `how_to_manage_contacts`  | ✅ rule *("making" isn't an action keyword)*                  |
| `how can I update a material price?` | `how_to_update_material`  | ✅ rule                                                       |
| `how do I approve an estimate?`      | `how_to_manage_estimates` | ✅ rule *("approve" not an action keyword)*                   |

### Domain-only how-to (no action keyword matched)

| Phrasing | Topic | Status |
|---|---|---|
| `guide to setting up a property` | `how_to_manage_properties` | ✅ rule (pluralization defect closed by Wave 1 Phase 1) |
| `what's the process for archiving an estimate?` | `how_to_manage_estimates` | ✅ rule |

### Generic how-to (no action, no domain)

| Phrasing | Topic | Status |
|---|---|---|
| `how do I use this system?` | `how_to_use_system` | ✅ rule |
| `show me how to use Maple` | `how_to_use_system` | ✅ rule |
| `how to get started` | `how_to_use_system` | ✅ rule |

## 10.4 Help vs. CRUD precedence

When a message contains **both** a CRUD intent (firm action+domain match) and an enum keyword, CRUD usually wins. Two important carve-outs:

| Phrasing | Result | Why |
|---|---|---|
| `help me create a contact for Jane` | `create_contact` → Contact Agent | "help me" is a polite prefix, not an instructional question. CRUD action+domain is firm. |
| `how many labour roles do I have?` | `list_labours` → Labour Agent | `action == "list"` short-circuit at `intents.py:321` prefers CRUD over help even though "roles" is an enum keyword. |
| `what are the material categories?` | `list_material_categories` → Orchestrator Agent | Rule-level CRUD match fires before help classifier. See §8.3 refusal for create/delete variants. |
| `how do I create a contact?` | `help` → Orchestrator Agent | Instructional pattern ("how do i") always wins over CRUD — `intents.py:310-311`. |

## 10.5 Help gaps

Phase 1 of the xfail backlog (plan: `documentation/development/plans/maple-xfail-wave-1.md`) closed most §10.5 entries on 2026-05-02. Remaining gaps below are awaiting Wave 2 design work.

| Phrasing | Intended behavior | Status |
|---|---|---|
| `tutorial` / `getting started` / `docs` / `documentation` | `capabilities` topic via `HELP_DIRECT_HINTS` | ✅ rule (Phase 1). |
| `examples` / `give me some examples` / `what kinds of things can I ask?` | `capabilities` topic | ✅ rule (Phase 1). |
| `what can't you do?` / `what are your limitations?` | `general_question` via interrogative guide-fallback | ✅ rule (already covered before Phase 1). |
| `does Maple support X?` / `is there a way to do X?` | `capabilities` / `general_question` via help routing | ✅ rule (Phase 1) — equipment refusal now gated by `_looks_interrogative`; `is there a way` and `does maple support` added to `HELP_INSTRUCTIONAL_PATTERNS`. |
| `what is a work item?` / `what's a property?` | Glossary / terminology help via guide-fallback | ✅ rule (already covered). |
| `what fields does a contact have?` | Schema help — return Pydantic model fields | ✅ rule (already covered via fallback). |
| `what happens when I approve an estimate?` / `what does archive do?` | Action-semantics help | ✅ rule (already covered via fallback). |
| `how does Maple work?` / `explain Maple to me` / `what do you do?` | `capabilities` topic | ✅ rule (Phase 1). |
| `what are the labour units?` / `what are the material units?` | `labour_units` / `material_units` topics | ✅ rule (Phase 1) — `unit`/`units` added to `HELP_ENUM_KEYWORDS`; new §3.13 + §3.14 in `users_guide.md` provide source content. |
| `I am lost` / `I am stuck` | `capabilities` topic | ✅ rule (Phase 1). |
| `what should I ask?` / `what can I do?` | `capabilities` topic | ✅ rule (Phase 1). |
| `list your features` | `capabilities` topic | ✅ rule (Phase 1). |
| `how do I add a work item?` | `how_to_manage_estimates` (estimate line-item alias) | ✅ rule (Phase 1) — `work item`/`job item`/`line item` detected and routed to estimate scope. |
| `how do I link a contact to a property?` | `how_to_link_contact_property` topic | ✅ rule (Phase 1) — cross-domain detection runs before single-domain loop; new §3.12 in `users_guide.md`. |

### Pluralization defect — `how_to_manage_propertys` (closed Phase 1)

`HelpHandler.detect_topic` previously returned `f"how_to_manage_{domain_name}s"`, which produced `how_to_manage_propertys` for the property domain. Phase 1 introduced an inline `plural_topic` map (`property → properties`, others append `s`) so the topic key round-trips correctly to `how_to_manage_properties`.

## 10.6 Social & personality

Maple handles greetings and personal/anthropomorphized questions in **two tiers**:

1. **Bare greetings** (`hey`, `hi maple`, `good morning`) are caught in the **orchestrator** (`agents/orchestrator/service.py`, `_detect_policy_short_circuit` via `is_greeting`) and answered with an instant canned reply from `GREETING_RESPONSES` in `agents/text_utils.py`. This is a **new `social` intent** (operation `social`, `read_only`) — **not** a help topic — so there is **no LLM call**. Suggestion chips come from `_SOCIAL_SUGGESTIONS`.
2. **Personal questions** (`how are you?`, `what do you look like?`, `are we friends?`) are detected by `is_personal_question` in `agents/text_utils.py` and routed through the **existing help path** — `HelpHandler.detect_topic` returns the **new `personal` topic** — and answered by the LLM guide responder (`agents/maple_guide/service.py`) **from Maple's persona** (`agents/maple_persona.py`), via a rule-1 exemption in the guide prompt.

The personal-question detector is deliberately **topic-keyed** so product-capability phrasings stay in the product lane (see the Negatives table below).

### Greetings — `social` intent (canned, no LLM)

| Phrasing | Intent | Status |
|---|---|---|
| `hey` | `social` | ✅ rule (canned) |
| `hi` / `hi maple` | `social` | ✅ rule (canned) |
| `hello` | `social` | ✅ rule (canned) |
| `good morning` / `good afternoon` / `good evening` | `social` | ✅ rule (canned) |
| `howdy` | `social` | ✅ rule (canned) |
| `hola` / `buenos días` (Spanish, defense-in-depth) | `social` | ✅ rule (canned) |

### Personal questions — `personal` help topic (LLM, persona-answered)

| Phrasing | Topic | Status |
|---|---|---|
| `how are you?` / `how's it going?` (feelings) | `personal` | ✅ (LLM/persona) |
| `what do you look like?` (appearance) | `personal` | ✅ (LLM/persona) |
| `are you hot?` (appearance) | `personal` | ✅ (LLM/persona — *playful deflect*) |
| `are we friends?` (friendship) | `personal` | ✅ (LLM/persona) |
| `are you married?` / `do you have a partner?` (relationships) | `personal` | ✅ (LLM/persona — *playful deflect*) |
| `i love you` (flirty) | `personal` | ✅ (LLM/persona — *playful deflect, no reciprocation*) |
| `are you an AI?` (identity) | `personal` | ✅ (LLM/persona — *honest yes*) |
| `how old are you?` (biography) | `personal` | ✅ (LLM/persona) |
| `where do you live?` (biography) | `personal` | ✅ (LLM/persona) |
| `what's your sign?` (biography) | `personal` | ✅ (LLM/persona) |

### Negatives (stay in the product lane)

These read like questions *about* Maple but are really **capability / CRUD** requests — the detector deliberately excludes them so they route to normal help/CRUD, **not** `personal`.

| Phrasing | Routes to | Status |
|---|---|---|
| `are you able to add contacts?` | `capabilities` / CRUD (not `personal`) | ✅ (correctly excluded) |
| `can you create an estimate?` | `capabilities` / `create_estimate` (not `personal`) | ✅ (correctly excluded) |
| `how are you estimating this job?` | help / estimate flow (not `personal`) | ✅ (correctly excluded) |
| `how are you able to help me?` | `capabilities` (not `personal`) | ✅ (correctly excluded) |

**Persona boundaries** (`agents/maple_persona.py`): flirty messages get a **playful deflection** with **no romantic reciprocation**; explicit or persistent advances drop the humor and redirect to work; AI-identity questions are answered **honestly** (she is an AI); replies stay short and pivot back to the task; she **never** reveals other users' data.

---

# 11. Appendix

## 11.1 Where tests live

| Path | Purpose |
|---|---|
| `platform/tests/test_maple_crud_coverage.py` | Matrix — 117 phrasings × Tier 1 + Tier 2 |
| `platform/tests/_maple_coverage_data.py` | Matrix data (10 categories × 5 resources) |
| `platform/tests/test_maple_estimate_status_queries.py` | Estimate count + value queries (Phase A) |
| `platform/tests/test_maple_material_size_operations.py` | Material size ops (Phase B) |
| `platform/tests/test_maple_help_coverage.py` | HELP intent — supported phrasings + xfail gaps (§10) |
| `platform/tests/test_material_agent.py` | Material Agent handler integration |
| `platform/tests/test_estimate_agent.py` | Estimate Agent handler integration |
| `platform/tests/test_orchestrator_intents.py` | Orchestrator intent resolution |
| `platform/tests/test_maple_template_crud.py` | Template CRUD — routing, refusals, apply-to-estimate (§6) |
| `platform/tests/test_maple_work_item_ops.py` | Work-item field operations — routing, op detection, regression, recurring param parsing (§1.5) |
| `platform/tests/test_maple_new_phrasings.py` | May 2026 expansion — clear bug, win alias, age filter, analytics, material/role field queries, cross-resource "linked to" |
| `platform/tests/test_maple_phrasing_expansion.py` | June 2026 expansion — status ratios/comparisons, age/staleness (`updated_at`), status-`in`, material name∪category qualifier (routing + pure parsers/formatter) |
| `platform/tests/reports/maple_crud_gap_report.md` | Auto-generated gap report (regenerates each test run) |

## 11.2 How to run

```bash
cd platform
./run_tests.sh tests/test_maple_crud_coverage.py                     # Tier 1 only (~8s)
./run_tests.sh tests/test_maple_crud_coverage.py -m ""               # Tier 1 + Tier 2 (~3min, ~$0.05, needs OPENAI_API_KEY)
./run_tests.sh tests/test_maple_estimate_status_queries.py tests/test_maple_material_size_operations.py
./run_tests.sh tests/test_maple_help_coverage.py                     # HELP intent (74 passing, 0 xfail after Phase 1)
./run_tests.sh tests/test_maple_new_phrasings.py                     # May 2026 expansion (31 tests)
```

## 11.3 Current matrix score (Tier 1 / Tier 2)

Snapshot as of 2026-05-02 — regenerate with the coverage test.

| Category | Tier 1 | Tier 2 | Verdict |
|---|---|---|---|
| direct_imperative | 12/12 | 9/12 | covered (LLM flubs "create a new X") |
| casual | 12/12 | 12/12 | covered |
| possessive | 12/12 | 6/12 | covered (Wave 1 Phase 2) |
| count | 12/12 | 12/12 | covered |
| filter_find | 12/12 | 12/12 | covered |
| field_targeted_update | 12/12 | 8/12 | covered (Wave 1 Phase 2) |
| implicit_relationship | 12/12 | 4/12 | covered (Wave 2 — orchestrator routing + agent-side join) |
| bulk | 12/12 | 12/12 | refused correctly |
| verbless | 12/12 | 11/12 | covered |
| material_size | 6/6 | 6/6 | covered |
| material_query_variants | 5/5 | n/a | covered (Wave 3 Workstream B) |
| estimate_outbound | 5/5 | n/a | covered (Wave 4 + 4.1 — orchestrator routing + Property/Contact/Estimate agent cross-resource branches; contact-anchored variant gated on person-name shape) |
| equipment_blocked | 3/3 | 3/3 | refused correctly |

**Totals: Tier 1 127/127 · Tier 2 95/117** (Tier 2 is unchanged — Wave 4/4.1 hasn't been re-run on the LLM tier; new categories aren't included in the Tier 2 coverage column above). All Tier 1 categories pass and cross-resource list responses are correctly filtered. The `cross_resource` join layer lives in `agents/cross_resource.py`; per-agent join handlers in Contact / Property / Estimate read `context.filter_by` to apply the constraint, including the Wave 4/4.1 `estimate`, `property`, and `contact` cross-types.

*Note (2026-06-09): the new Social & personality surface (§10.6) — greetings via the `social` intent and personal questions via the `personal` help topic — is not yet represented in the auto-generated matrix above; see §10.6 for its phrasing catalog.*

## 11.4 Related docs

- `CLAUDE.md` > "Maple (Orchestrator) — CRUD assistant policies" — architectural overview
- `documentation/development/plans/maple-xfail-wave-1.md` — active plan for closing the remaining xfail backlog

---

# 12. Coverage blind spots & extension ideas

The matrix is shape-complete for the nine CRUD categories but never exercises several phrasing families real users will type. This section is the gap-hunting backlog — entries here aren't tracked as ⚠️ gaps in §1–§8 because they're conceptual classes, not specific phrasings ready to wire. Promote an entry to a per-resource ⚠️ gap row once you've picked a concrete phrasing and a target intent.

## 12.1 Language / phrasing variation

- **Negations:** `I don't need the Landscaper role anymore`, `remove John Doe — he moved`
- **Conjunctions / multi-action:** `create a contact and link it to {property}`, `delete the Foreman role and add Operator instead`
- **Typos / stemming:** `delet the proprty at 123 Main`, `contacs`, `labours` vs `labour roles` — partly mitigated by `agents/fuzzy_utils.py`
- **Pronouns / anaphora across turns:** `update it`, `that one`, `the last one I created` (estimate-scoped anaphora exists in §1.7; cross-resource anaphora is the gap)
- **Questions that imply get vs list:** `is there a contact named John?`, `do I have concrete blocks?`

## 12.2 Value / field shapes not exercised

- **Dates / date ranges:** `contacts added this month`, `estimates from last week`
- **Numeric ranges / comparisons:** `materials under $10` (already in §4.9), `labour roles costing more than $40/hr`
- **Multi-field update:** `set John Doe's phone to X and email to Y`
- **Nullable / clearing:** `remove John Doe's phone number`, `clear the description on {material}`

## 12.3 Domain overlap ambiguity

The matrix uses disjoint tokens by design — real users won't:

- Same name across domains: a contact and a property both called "John's Place"
- Role-name collisions: a contact named "Foreman Smith"
- Addresses that look like material names

A small `ambiguity` test category would assert the classifier's tiebreak behavior.

## 12.4 Refusal surface beyond bulk + equipment

- **Destructive at smaller scale:** `delete the last 5 contacts` (N>1 but not "all") — listed as a §8.4 ⚠️ gap
- **Cross-tenant / out-of-scope:** `show me other companies' estimates`
- **Non-CRUD slipping through:** `email John Doe`, `schedule a visit`

## 12.5 Highest-value extensions (ranked by ROI)

If we want to expand coverage, here's the order:

1. **`status_transition` matrix category for estimates** — fixed verb set × 5 EstimateStatus values × 2-3 subjects. ~30 new cases. Cleanest starter; status transitions already exist in §1.4.
2. **Active-entity anaphora** — exercises the `active_estimate_code` session path beyond what §1.7 currently asserts.
3. **Filter by status / date** — `show me draft estimates from last week`, `approved quotes over $10k`. Needs date-range parsing.
4. **Direct coverage of the add-work-item regex path** — `agents/orchestrator/service.py` work-item rules; today only hit by orchestrator unit tests.
5. **Cross-resource outbound from estimate** — mirrors §7.2 / §7.3 inbound pattern (e.g. `which property is {EST} for?`, `what materials does {EST} use?`).
6. **Ambiguity fixtures** — see §12.3.
7. **Typo / stemming fixtures** — 5–10 common misspellings per resource to catch fuzzy-match regressions.
