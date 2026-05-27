# Maple Template CRUD — Implementation Plan

**Created:** 2026-05-26

## Scope

Add Template support to Maple orchestrator: list, get, delete, count, filter, verbless lookup, and apply-to-estimate. Template creation, update, and duplicate are explicitly refused (§8.5 of phrasing reference).

## Phases

1. **Orchestrator wiring** — `intents.py`: DOMAIN_HINTS, SUPPORTED_INTENTS_BY_AGENT, entity maps, plural tokens
2. **Refusal guard** — `text_utils.py` + `service.py`: `is_template_mutation_request()` + `_detect_policy_short_circuit`
3. **Template Agent** — `agents/template/service.py`: list, get, delete handlers (read + delete only, no LLM needed)
4. **Object link** — `text_utils.py`: add `"template": "/templates"` to OBJECT_LINK_PATHS
5. **Agent dispatch** — `routers/agents.py` + `agents/__init__.py`: wire TemplateAgent into singleton dispatch
6. **Domain knowledge** — `orchestrator/domain_knowledge.py`: add template section
7. **Apply-to-estimate** — `service.py`: specific-phrasing rules for `use/apply template X in/to estimate`
8. **Capability guidance** — `service.py`: mention Templates in the guidance string

## Test strategy

TDD — `tests/test_maple_template_crud.py` written first:
- T1: Orchestrator intent resolution (list/get/delete/count/filter phrasings)
- T2: Refusal tests (create/update/duplicate refused with correct message)
- T3: Template Agent handler tests (list, get, delete, count, bulk-delete belt-and-braces)
- T4: Registry integrity (DOMAIN_HINTS, INTENT_TO_AGENT, etc.)
- T5: Apply-to-estimate cross-resource routing
