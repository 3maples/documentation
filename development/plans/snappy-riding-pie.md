# Plan: Fix Field Extraction for Contact, Property, and Material Agents

## Context

The evaluation report (2026-03-26) scores **20/33 (61%)**. Labour management was fixed from 0% to 100% by expanding DOMAIN_HINTS, adding natural language regex patterns, and improving LLM prompts. The same approach now needs to be applied to:

- **Contact Management**: 2/5 (40%) — scenarios 2.1, 2.3, 2.4 fail
- **Property Management**: 1/4 (25%) — scenarios 3.1, 3.3, 3.4 fail
- **Material Management**: 1/4 (25%) — scenarios 4.1, 4.3, 4.4 fail

The fixes fall into two categories:
1. **Orchestrator routing** — Missing DOMAIN_HINTS synonyms prevent intent classification
2. **Agent field extraction** — Regex patterns are too rigid for natural language input

Note: Scenarios 2.4, 3.3, 4.4 (list operations returning 0 results) may also have a company scoping issue that is separate from field extraction. The DOMAIN_HINTS fixes will ensure correct routing, but if the underlying query returns 0 results, those tests may still fail.

---

## Changes

### 1. Expand DOMAIN_HINTS for contact, property, material
**File:** `platform/agents/orchestrator/intents.py:102-115`

```python
DOMAIN_HINTS: Dict[str, List[str]] = {
    "property": [
        "property", "properties",
        "job site", "job sites", "job", "jobs",
    ],
    "contact": [
        "contact", "contacts",
        "client", "clients",
    ],
    "estimate": ["estimate", "estimates", "quote", "quotes"],
    "material": [
        "material", "materials",
        "stock", "in stock", "inventory",
    ],
    "labour": [... unchanged ...],
}
```

**Why:** "add a new client" → domain=contact. "new job site" → domain=property. "in stock" → domain=material. Without these, the rule-based classifier returns `None` for domain, forcing fallback to LLM which may misclassify.

**Risk:** "job" is generic. "show me my job" could mean property or something else. Mitigated because it only triggers when paired with a recognized action hint.

---

### 2. Add natural language name extraction to Contact Agent
**File:** `platform/agents/contact/service.py:244-275` (`_extract_name_from_message`)

Add patterns at the end of the existing list (lower priority than explicit patterns):

```python
# Natural language: "add a new client Mike Johnson, ..."
r"\b(?:client|customer)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\b",
# "add a new client Mike Johnson" — after "client" keyword
r"\b(?:new\s+)?(?:client|customer|contact)\s+([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){1,2})\b",
```

**Why:** Test 2.1 sends "add a new client Mike Johnson" — no existing pattern matches because they all require the word "contact" and the name in specific positions. The phone regex `(\+?\d[\d\-\s]{7,}\d)` at line 492 should already extract "604-555-1234", so the main issue is that the agent never gets invoked (routing) or the name isn't found (so it asks for clarification instead of creating).

---

### 3. Add "manger" typo to Contact role aliases
**File:** `platform/agents/contact/service.py:61-67` (`CONTACT_ROLE_ALIASES`)

```python
CONTACT_ROLE_ALIASES = {
    "home owner": ContactRole.HOME_OWNER.value,
    "homeowner": ContactRole.HOME_OWNER.value,
    "owner": ContactRole.HOME_OWNER.value,
    "manager": ContactRole.MANAGER.value,
    "property manager": ContactRole.MANAGER.value,
    "manger": ContactRole.MANAGER.value,          # common typo
    "property manger": ContactRole.MANAGER.value,  # common typo
}
```

**Why:** Test 2.3 "shes the property manger" — "manger" is not matched to "Manager" role.

---

### 4. Add natural language role extraction to Contact Agent
**File:** `platform/agents/contact/service.py:537-545` (role patterns in `_extract_fields_from_message`)

Add patterns to the existing `role` list:

```python
"role": [
    # ... existing label-based patterns ...
    r"\b(?:he|she|they)\s+is\s+an?\s+([a-zA-Z][a-zA-Z .'\-]{1,60})",  # existing
    # Natural language: "shes the property manager", "she's a manager"
    r"\b(?:he'?s|she'?s|they'?re)\s+(?:the|a|an)\s+([a-zA-Z][a-zA-Z .'\-]{1,60})",
],
```

**Why:** Test 2.3 "shes the property manger" — the existing pattern `(?:he|she|they)\s+is\s+an?\s+` requires "is" but the message uses "shes" (contraction without apostrophe).

---

### 5. Improve Contact LLM entity extraction prompt
**File:** `platform/agents/contact/service.py:858-870` (`_extract_entities_with_llm`)

Add extraction rules to the system prompt:

```python
"Extract structured contact entities from user input.\n"
"Use conversation history for references, but prioritize the latest user message.\n"
"Return only entity data, no prose.\n"
"Extract person name into full_name when present.\n"
"Do not include trailing connector words (e.g., and/that/who/owns) in names.\n"
"Include any detected contact fields in fields.\n"
"EXTRACTION RULES:\n"
"- 'client' and 'customer' are synonyms for 'contact'\n"
"- Extract phone numbers into fields.phone (e.g., '604-555-1234')\n"
"- Extract email addresses into fields.email\n"
"- Extract role from context (e.g., 'property manager', 'home owner') into fields.role\n"
"- Correct common typos: 'manger' means 'Manager'\n"
"- Extract address components: fields.address, fields.city, fields.prov_state, fields.postal_zip\n"
"- 'his number is 604-555-1234' means phone=604-555-1234\n"
"{intent_hint_instruction}"
```

---

### 6. Add natural language address extraction to Property Agent
**File:** `platform/agents/property/service.py:376-521` (`_extract_fields_from_message`)

The current address parser requires commas between all parts: `address, city, prov_state, postal_zip`. Test 3.1 sends "123 Maple Drive, Surrey BC V3T 4R5" — no comma between city and province, province and postal run together.

Add a more flexible address pattern **after** the existing strict ones (around line 520, before `return extracted`):

```python
# Flexible Canadian address: "123 Maple Drive, Surrey BC V3T 4R5"
# (city and province separated by space, not comma)
flexible_address_match = re.search(
    r"\bat\s+"
    r"(\d{1,6}\s+[^,\n;]{3,80}?)"        # street address
    r"\s*,\s*"                              # comma separator
    r"([A-Za-z][A-Za-z ]{1,40}?)"          # city
    r"\s+"                                  # space (not comma)
    r"([A-Z]{2})"                           # province code (BC, ON, etc.)
    r"(?:\s+"
    r"([A-Z]\d[A-Z]\s?\d[A-Z]\d)"          # postal code (V3T 4R5)
    r")?"
    r"(?:\s*$|\s*,|\s*\.)",
    normalized,
    flags=re.IGNORECASE,
)
if flexible_address_match:
    extracted.setdefault("address", _safe_str(flexible_address_match.group(1)))
    extracted.setdefault("city", _safe_str(flexible_address_match.group(2)))
    prov = self._normalize_prov_state_token(flexible_address_match.group(3))
    if prov:
        extracted.setdefault("prov_state", prov)
    if flexible_address_match.group(4):
        postal = self._normalize_postal_zip_token(flexible_address_match.group(4))
        if postal:
            extracted.setdefault("postal_zip", postal)
```

**Why:** "I got a new job site at 123 Maple Drive, Surrey BC V3T 4R5" — only one comma, province is "BC" (2-letter code after city), postal code is space-separated.

---

### 7. Improve Property LLM entity extraction prompt
**File:** `platform/agents/property/service.py:692-709` (`_extract_entities_with_llm`)

```python
"Extract structured property entities from user input.\n"
"Use conversation history for references, but prioritize the latest user message.\n"
"Return only entity data.\n"
"Extract target property name/address into full_name when present.\n"
"Extract property owner person into owner_name when asked for properties someone owns.\n"
"Extract assigned contact person name into contact_name when present.\n"
"Do not include connector words (e.g., and/that/which/owns) in extracted names.\n"
"EXTRACTION RULES:\n"
"- 'job site', 'job', 'site', 'yard' are synonyms for 'property'\n"
"- Extract street address into fields.address (e.g., '123 Maple Drive')\n"
"- Extract city into fields.city (e.g., 'Surrey')\n"
"- Extract province/state code into fields.prov_state (e.g., 'BC')\n"
"- Extract postal/zip code into fields.postal_zip (e.g., 'V3T 4R5')\n"
"- Parse addresses even without labels: 'at 123 Main St, Vancouver BC' -> address='123 Main St', city='Vancouver', prov_state='BC'\n"
"{intent_hint_instruction}"
```

---

### 8. Add natural language material name extraction
**File:** `platform/agents/material/service.py:200-256` (`_extract_name_from_message`)

Add patterns at the end of the existing list:

```python
# Natural language: "add river rock, ..." — name is first noun phrase after add
r"\badd\s+([a-zA-Z][a-zA-Z ]{1,60}?)\s*(?:,|\bit(?:'|\s)s\b|\babout\b|\bcost\b|\bprice\b|$)",
# "add paver stones, hardscape category" — name before comma + category
r"\badd\s+([a-zA-Z][a-zA-Z ]{1,60}?)\s*,\s*(?:[a-zA-Z]+ )?(?:category|type|material)\b",
```

**Why:** Test 4.1 "add river rock, its a landscaping material" — no existing pattern matches because they all require "name:", "material called", "material named" labels.

---

### 9. Extend material per-unit patterns for landscaping units
**File:** `platform/agents/material/service.py:462-469` (per_unit_match)

Current pattern only handles: `hour|hr|hrs|day|week|month|job|project`. Landscaping materials use: cubic yard, square foot, bag, etc.

```python
per_unit_match = re.search(
    r"\$?\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:\/|per)\s*"
    r"(hour|hr|hrs|day|week|month|job|project"
    r"|cubic\s*yard|cubic\s*yd|cu\s*yd|cy"
    r"|square\s*foot|square\s*ft|sq\s*ft|sf"
    r"|bag|roll|sheet|piece|each|unit"
    r"|ton|tonne|yard|yd|foot|ft|meter|metre)\b",
    normalized,
    flags=re.IGNORECASE,
)
```

Also add a pattern for "about $45 per cubic yard" (with "about" before the dollar amount):

```python
# "about $45 per cubic yard"
about_cost_match = re.search(
    r"\babout\s+\$?\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:\/|per)\s*"
    r"(cubic\s*yard|cubic\s*yd|cu\s*yd|cy"
    r"|square\s*foot|square\s*ft|sq\s*ft|sf"
    r"|bag|roll|sheet|piece|each|unit"
    r"|ton|tonne|yard|yd|foot|ft|meter|metre"
    r"|hour|hr|day|week|month)\b",
    normalized,
    flags=re.IGNORECASE,
)
if about_cost_match:
    extracted.setdefault("price", _safe_str(about_cost_match.group(1)))
    extracted.setdefault("unit", _safe_str(about_cost_match.group(2)))
```

And add "bucks"/"dollars" support like the labour agent:

```python
if "price" not in extracted:
    bucks_match = re.search(
        r"\b([0-9]+(?:\.[0-9]{1,2})?)\s*(?:bucks?|dollars?)\b",
        normalized, flags=re.IGNORECASE,
    )
    if bucks_match:
        extracted["price"] = _safe_str(bucks_match.group(1))
```

---

### 10. Add category extraction from natural language for materials
**File:** `platform/agents/material/service.py:406-516` (`_extract_fields_from_message`)

Add after the label-based patterns (around line 460):

```python
# Natural language category: "hardscape category", "landscaping material"
if "category" not in extracted:
    cat_match = re.search(
        r"\b([a-zA-Z][a-zA-Z ]{1,40}?)\s+(?:category|type)\b",
        normalized, flags=re.IGNORECASE,
    )
    if cat_match:
        extracted["category"] = _safe_str(cat_match.group(1)).strip()

# "its a landscaping material" → category = "landscaping"
if "category" not in extracted:
    its_a_match = re.search(
        r"\b(?:it(?:'|\s)?s\s+a(?:n)?|it\s+is\s+a(?:n)?)\s+([a-zA-Z][a-zA-Z ]{1,40}?)\s+material\b",
        normalized, flags=re.IGNORECASE,
    )
    if its_a_match:
        extracted["category"] = _safe_str(its_a_match.group(1)).strip()
```

---

### 11. Improve Material LLM entity extraction prompt
**File:** `platform/agents/material/service.py:683-698` (`_extract_entities_with_llm`)

```python
"Extract structured material entities from user input.\n"
"Use conversation history for references, but prioritize the latest user message.\n"
"Return only entity data.\n"
"Extract material name into full_name when present.\n"
"Extract fields: name, description, category, unit, size, price, cost.\n"
"For rename requests, extract current name into source_name and target name into fields.name.\n"
"Do not include trailing connector words in names.\n"
"EXTRACTION RULES:\n"
"- Extract the material name from natural language: 'add river rock' -> full_name='River Rock'\n"
"- 'landscaping material' or 'hardscape' can indicate category\n"
"- '$45 per cubic yard' -> price=45, unit='cubic yard'\n"
"- '$3.50 per square foot' -> price=3.50, unit='sq ft'\n"
"- '6 bucks per bag' -> price=6, unit='bag'\n"
"- 'about $45' means price=45 (ignore 'about')\n"
"- 'in stock' and 'inventory' refer to materials, not a specific material name\n"
"{intent_hint_instruction}"
```

---

### 12. Add `full_name` → `fields["name"]` population for materials
**File:** `platform/agents/material/service.py:1115-1119`

Ensure material name from `full_name` is used when `fields["name"]` is empty (similar to what was done for labour):

```python
if intent == "create_material" and _safe_str(fields.get("name")) == "":
    inferred_name = self._normalize_material_name(parsed.get("full_name"))
    if inferred_name:
        fields["name"] = inferred_name
```

This already exists at line 1115-1119, so verify it's working correctly. The issue may be that `full_name` itself isn't being extracted.

---

## Files to Modify

| File | Changes |
|------|---------|
| `platform/agents/orchestrator/intents.py` | Expand DOMAIN_HINTS for contact ("client"), property ("job site", "job"), material ("stock", "in stock") |
| `platform/agents/contact/service.py` | Add "manger" typo aliases; natural language name extraction; "shes the" role pattern; improve LLM prompt |
| `platform/agents/property/service.py` | Flexible Canadian address regex (space-separated city/prov); improve LLM prompt |
| `platform/agents/material/service.py` | Natural language name extraction; landscaping unit patterns (cubic yard, sq ft, bag); "bucks" support; category from context; improve LLM prompt |

---

## Verification

1. Run the evaluation suite:
```bash
cd platform
./run_tests.sh tests/test_landscaper_e2e.py -v -s -m evaluation
```

2. Run the full test suite for regressions:
```bash
cd platform
./run_tests.sh
```

**Expected Improvement:**
- Contact: 40% → 60-80% (2.1, 2.3 should pass; 2.4 depends on company scoping)
- Property: 25% → 50-75% (3.1 should pass; 3.3, 3.4 depend on scoping/context)
- Material: 25% → 50-75% (4.1, 4.3 should pass; 4.4 depends on scoping)
- Overall: 61% → ~73-82% (24-27 of 33)
