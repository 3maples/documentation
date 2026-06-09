# Generalize Maple's Translation Sandwich to Any Input Language

> On approval, copy this plan to `documentation/development/plans/` per project convention.

## Context

Maple currently supports English and Spanish. Spanish works via a "translation sandwich" in [platform/services/translation.py](platform/services/translation.py): a heuristic detector flags Spanish, the message is LLM-translated to English, the entire English pipeline (intent routing, slot extraction, filters) runs unchanged, and the response is translated back to Spanish on the way out. Simon wants this generalized: accept **any** language, detect it, translate to English, process, and translate the reply back to the original language.

Decisions made with Simon (2026-06-09):
1. **Detection = combined LLM detect+translate.** A cheap dependency-free pre-filter flags "probably not English"; flagged messages get ONE worker-model LLM call that returns `{"lang": "<ISO 639-1>", "english": "<translation>"}`. English turns stay at 0 extra LLM calls; non-English turns stay at +2 (combined inbound + outbound bundle), same as today.
2. **Fail closed inbound.** If the pre-filter flagged non-English and the inbound LLM call errors, return a canned "I'm having trouble understanding right now" message instead of pushing raw foreign text through the English pipeline (English-only safety guards can't catch e.g. a Japanese bulk-delete). This **reverses** today's inbound fail-open. Outbound translation failure still fails open (English reply beats no reply). Existing Spanish keyword guards in `agents/text_utils.py` / `crud_helpers.py` stay as defense-in-depth for pre-filter false negatives.
3. **Open language set.** No curated allowlist — whatever language is detected gets translated back. Spanish keeps its curated extras (pan-Hispanic register, glossary, voseo guidance) via an extensible per-language dict; all other languages get a generic quality prompt.

Invariants preserved: all internal processing is English-only; persisted `chat_history` stays English; temperature 0, worker model; both entry points covered ([routers/agents.py](platform/routers/agents.py) `/agents/orchestrate` and [routers/public_maple.py](platform/routers/public_maple.py) `/public/maple/ask`); mocked-LLM tests via the existing `set_llm_for_tests` seam.

## Changes — all in `platform/`

### 1. Pre-filter (replaces `detect_language`) — `services/translation.py`

```python
@dataclass(frozen=True)
class LanguagePrefilter:
    maybe_non_english: bool
    hint: Optional[str]  # coarse guess, used ONLY to pick canned error copy

def prefilter_language(text: str) -> LanguagePrefilter: ...
```

Heuristic only, no LLM, no new dependencies. Signals in order:
1. Empty / no letters (emoji-only, numbers-only, `EST-0042`) → not flagged.
2. **Non-Latin script** → flag immediately, hint from dominant script: Hiragana/Katakana→`ja`, Hangul→`ko`, Han (no kana)→`zh`, Cyrillic→`ru`, Arabic→`ar`, Hebrew→`he`, Thai→`th`, Devanagari→`hi`, Greek→`el`. Hints are deliberately coarse (Cyrillic might be Ukrainian) — the LLM does real detection.
3. **Latin-script scoring**, generalizing today's `_ES_MARKER_WORDS` design:
   - `_LATIN_MARKERS: dict[str, frozenset[str]]` — migrate the es set verbatim; add fr/pt/de/it marker sets.
   - `_LATIN_STRONG: dict[str, frozenset[str]]` — single-word flips (existing es strong set + `merci`, `danke`, `obrigado`, `grazie`, `bonjour`…).
   - `¿¡` punctuation → flag with hint `es`. Broaden the diacritic regex from `[ñáéíóúü]` to general Latin-1 Supplement / Extended-A letters (+1 point).
   - **English counter-score** (new — this preserves the English bias): small English stopword set; flag only when `max_lang_score >= 2 AND max_lang_score > english_score`. Keeps "show me los angeles properties", "add a café table material", "delete Hormigón H-30" at 0 LLM cost.

`detect_language` stays alive during the commit sequence and is deleted in the final cleanup commit.

### 2. Combined detect+translate call — `services/translation.py`

```python
class InboundTranslationError(Exception): ...

@dataclass(frozen=True)
class InboundTranslation:
    lang: str           # normalized ISO 639-1; "en" when already English
    english_text: str   # == original text verbatim when lang == "en"

async def detect_and_translate_to_english(text: str) -> InboundTranslation: ...
```

- Reuses `_llm_holder` / `set_llm_for_tests` (translation.py:132-156) unchanged. Plain `ainvoke` + JSON output contract (NOT `with_structured_output`, so the existing fake-LLM test seam keeps working — same precedent as `agents/estimate/service.py`).
- Prompt: refactor the preservation rules (markdown links, quoted/backticked values, identifiers, numbers, URLs — currently inside `_SYSTEM_PROMPT_BASE`) into a shared `_PRESERVATION_RULES` constant used by both directions. Include `_INPUT_EXTRA` generalized to any language, the Spanish voseo/varieties guidance, and `_GLOSSARY_TO_EN` unconditionally. Output contract: `Return ONLY a JSON object: {"lang": "...", "english": "..."}`, with an explicit rule: English with embedded foreign names ("delete Hormigón H-30") → `lang: "en"`.
- Parsing (`_parse_inbound_payload`): strip code fences → `json.loads` → fallback `re.search(r"\{.*\}", raw, re.DOTALL)` once → normalize lang (lowercase, first subtag of `pt-BR`, must match `^[a-z]{2,3}$`) → validate non-empty `english`. Any failure or LLM exception → `InboundTranslationError` (chained, `logger.exception`). No retry — fail-closed handles it.
- **False positive handling:** `lang == "en"` → return `InboundTranslation("en", original)` using the ORIGINAL user text, not the model's echo (protects rule-based matchers from paraphrase drift); router then treats the turn as plain English, no outbound translation.

Canned unavailable copy: `_TRANSLATION_UNAVAILABLE_EN` + a static `dict` of ~12 pre-written translations keyed by pre-filter hint (`es fr pt de it ja zh ko ru ar hi th`), exposed via `translation_unavailable_message(hint)` with English fallback. Zero LLM cost, written once.

### 3. Outbound generalization — `services/translation.py`

- Delete `SUPPORTED_TARGET_LANGS` (line 36). `_should_skip` (line 228) becomes `not target_lang or target_lang == "en"`.
- Extend `_LANG_NAMES` to ~20 common languages; add `_lang_label(code)` with fallback `f"the language with ISO 639-1 code '{code}'"` so unknown codes still work.
- Per-language extras seam: `_OUTBOUND_EXTRAS: dict[str, tuple[str, ...]] = {"es": (_OUTPUT_ES_REGISTER, _GLOSSARY_TO_ES)}` + `_OUTPUT_GENERIC_REGISTER` ("write naturally in {target_name}, neutral business register, polite forms where the language distinguishes formality") as the fallback.
- `_build_system_prompt` (line 233): drop the inbound `target_lang == "en"` branch (subsumed by the combined call); `es` branch becomes `_OUTBOUND_EXTRAS.get(target_lang, (generic,))`. Rename to `_build_outbound_system_prompt`.
- `translate_text` / `translate_response_bundle`: signatures and batching delimiter unchanged; still **fail open**; now translate to any non-`en` target.
- Rewrite the module docstring (currently says "Everything here fails open" — now inbound fails closed, outbound fails open).

### 4. Router rewiring — `routers/agents.py` + `routers/public_maple.py`

`routers/agents.py` `orchestrate_agent_endpoint`:
- Line 698: `target_lang = detect_language(message)` → `prefilter = prefilter_language(message)`; `target_lang` starts `"en"`, resolved at the inbound seam.
- Quota-refusal 402 branches (lines 757-783) need a `target_lang` before the main seam: add helper `_detect_lang_for_refusal(message, prefilter)` — returns `"en"` unflagged, otherwise the combined call's lang, falling back to `"en"` on error (refusal copy in English is fine; don't fail-close a quota refusal).
- Main inbound seam (lines 799-800), still after the quota gate and `set_llm_context` (token attribution preserved):
  ```python
  if prefilter.maybe_non_english:
      try:
          inbound = await detect_and_translate_to_english(message)
      except InboundTranslationError:
          return OrchestratorAgentResponse(
              **_translation_unavailable_payload(original_message, prefilter.hint),
              supported_intents=SUPPORTED_INTENTS_BY_AGENT,
          )
      target_lang = inbound.lang
      message = inbound.english_text
  ```
- `_translation_unavailable_payload(message, hint)`: mirror `_maple_credits_refusal_payload` (the proven inline-bubble contract): `success=True, intent="translation_unavailable", needs_clarification=True, response=clarifying_question=translation_unavailable_message(hint), query=original_message`. Do **not** call `_save_conversation_context` — the failed turn must not pollute the English chat_history.
- `_localize_response_payload` / `_finalize_result` unchanged — they already accept any `target_lang`.

`routers/public_maple.py` (lines 69-91): same pattern; fail-closed return is `MapleAskResponse(response=translation_unavailable_message(prefilter.hint), suggestions=[], requires_signup=False)` + a `logger.warning` (no message contents).

Defense-in-depth Spanish keywords (`agents/text_utils.py` ~192-209/331-343, `agents/estimate/crud_helpers.py` `_SPANISH_STATUS_ALIASES`): **no behavior change**; update comments — their role shifts from "translation fail-open path" to "pre-filter false-negative path".

## Test plan (TDD — failing tests first per commit)

| File | Action |
|---|---|
| `tests/test_language_prefilter.py` | **New.** Parametrized per script family (ja/zh/ko/ru/ar/th/hi/el/he → flagged + right hint); Latin fr/pt/de/it + strong single words; English-bias regressions (plain English, "add a café table material", "delete Hormigón H-30", "show me los angeles properties", emoji/numbers/empty → not flagged); mixed-script "delete 北京 office" → flagged (LLM returns en). |
| `tests/test_inbound_detect_translate.py` | **New.** Happy path fr; fenced/prose-wrapped JSON; lang normalization (`PT-BR`→`pt`); `lang=="en"` returns ORIGINAL text; malformed JSON / missing keys / bad lang → `InboundTranslationError`; LLM raise → error (fail-closed unit proof); prompt contains preservation rules + voseo + glossary; `translation_unavailable_message` hit/miss. |
| `tests/test_translation.py` | Re-target detect tests to `prefilter_language`; delete `test_es_is_the_only_supported_target` and `translate_to_english` tests (incl. its fail-open test — superseded); invert `test_translate_text_unsupported_target_is_noop` (fr now invokes); keep outbound `test_translate_text_fails_open_on_error`; re-target the voseo-prompt test to the combined-call prompt. |
| `tests/test_orchestrator_endpoint_es.py` → `test_orchestrator_endpoint_i18n.py` | Rename. Swap monkeypatches (`detect_language`→`prefilter_language`, `translate_to_english`→fake `detect_and_translate_to_english`); keep the 3 existing assertions. New: fail-closed (canned response, `intent=="translation_unavailable"`, domain agent never called, context not saved); false positive (`("en", original)` → plain English, no outbound call); French round trip (bundle gets `target_lang=="fr"`). |
| `tests/test_public_maple_api.py` | Update Spanish fake LLM to answer call #1 with combined JSON, later calls with the bundle transform. New: fail-closed (200, canned copy, empty suggestions); Japanese round trip. |

Gates after every commit: `./run_mypy.sh` + `./run_ruff.sh` (scoped, then full before commit-prep) + `./run_tests.sh <touched test files only>`. Never the full suite.

## Ordered commits

1. **feat: open outbound target set** — extras dict, `_lang_label`, generic register, `_PRESERVATION_RULES` refactor, delete `SUPPORTED_TARGET_LANGS` (temporary inline guard keeps `translate_to_english` compiling).
2. **feat: language pre-filter** — `prefilter_language` + `tests/test_language_prefilter.py` (old `detect_language` still present).
3. **feat: combined detect+translate + canned copy** — `detect_and_translate_to_english`, parser, error type, `translation_unavailable_message` + `tests/test_inbound_detect_translate.py`.
4. **feat: rewire /agents/orchestrate** — prefilter wiring, fail-closed seam, `_translation_unavailable_payload`, `_detect_lang_for_refusal` + renamed i18n endpoint tests.
5. **feat: rewire /public/maple/ask** — same pattern + test updates.
6. **refactor: remove detect_language/translate_to_english** — dead code + stale tests + module docstring rewrite; full mypy/ruff sweep.
7. **docs/memory (flag, separate repos):** rewrite the auto-memory `project_maple_translation_sandwich.md` (now wrong on `SUPPORTED_TARGET_LANGS`, `detect_language`, "everything fails open"); add a dated entry to `documentation/development/code-review-followups.md`; optional short language-support note in CLAUDE.md's Maple section. `maple-phrasing-reference.md` doesn't mention translation — no change.

## Risks / accepted edge cases

- **Mixed language / code-switching**: pre-filter flags, combined call decides; "English + foreign names → en" prompt rule is the safety valve (costs one extra worker call on such turns).
- **Multi-turn**: detection stays per-message (as today). Turn 1 Spanish + turn 2 bare "phone" → turn 2 answered in English; a turn-2 "teléfono" (1 point) goes through raw with the Spanish alias maps as backstop — both match today's behavior. Detection flapping is harmless: history is always English; `target_lang` only shapes the same turn's outbound bubble.
- **Wrong/exotic lang code from the LLM**: `_lang_label` fallback keeps outbound functional; outbound still fails open to English.
- **Fail-closed UX**: a flagged message during an LLM outage gets the canned reply instead of degraded English processing — accepted per decision 2; pre-filter English bias makes false-positive cases rare, and the payload mirrors the credits-refusal bubble so the portal needs zero changes.
- **Quota-refusal lang detection runs before `set_llm_context`** (unattributed tokens) — same as today's refusal-branch translation; documented, not fixed here.

## Verification

1. Per-commit: scoped `./run_tests.sh` on the five test files above; `./run_mypy.sh` + `./run_ruff.sh` scoped then full.
2. End-to-end smoke (mocked LLM, via TestClient tests): Spanish round trip unchanged; French and Japanese round trips localize outbound; fail-closed path returns canned copy without invoking domain agents; English messages never touch the translator.
3. Optional live check (Simon-triggered, needs `OPENAI_API_KEY`): run the Tier-2 Maple coverage suite and manually send `「見積もりはいくつありますか？」` / `"combien de contacts j'ai ?"` through `/agents/orchestrate` in dev.
