---
description: Review LangChain agents in platform/agents/ and prompts in platform/prompts/ for prompt injection risk, instruction clarity, token efficiency, and temperature/model appropriateness.
argument-hint: [optional-file-path]
allowed-tools: Bash, Read, Grep, Glob
---

# Agent & Prompt Review

Dedicated review for your production LangChain agents and their system prompts. This covers concerns that `/code-review` doesn't drill into because they're specific to prompt engineering: injection surface, instruction clarity, token economy, and configuration choices.

`$ARGUMENTS` (optional) scopes the review to one file under `platform/agents/` or `platform/prompts/`. Otherwise, reviews all files in both directories.

## Step 1: Discover Agents and Prompts

```bash
# Agent definitions
find platform/agents -name "*.py" -not -name "__init__.py"

# Prompt definitions
find platform/prompts -name "*.py" -not -name "__init__.py"
```

Read each file identified. For each agent, note:

- Which prompt module(s) it imports
- Which LLM and temperature it uses (usually visible as `ChatOpenAI(model=..., temperature=...)`)
- Which tools / external functions it can call
- How user input flows into the prompt

## Step 2: Prompt Injection and Security

**CRITICAL**

- User input concatenated directly into a system or human message string (e.g. `f"User said: {user_text}"`) without delimiters or escaping
- User input used to control tool selection or agent routing decisions
- Prompts that explicitly tell the model to treat incoming text as trusted instructions
- Secrets, API keys, or internal URLs embedded in prompt text (they should come from `config.py` / env)
- System prompts that reveal internal implementation details (database names, route paths, column names) which could aid an attacker who sees the output

**HIGH**

- User input used inside instruction phrasing (e.g. `"Summarise the following user request: <user_text>"`) without a clear delimiter like triple-backticks or XML tags
- Tools that take free-form user strings and pass them to `subprocess`, shell, file I/O, or database queries
- Missing output validation — LLM output used directly in business logic without schema validation

## Step 3: Instruction Clarity

**HIGH**

- Contradictory instructions (e.g. "always return JSON" and "return a polite apology if you can't")
- Ambiguous priority between rules — when rules conflict, which wins?
- Missing or unclear output format specification (if the caller parses output, the format must be unambiguous)
- Examples in the prompt that don't match the stated format
- Placeholder text left in prompts (`TODO`, `FIXME`, `XXX`, `...`)

**MEDIUM**

- Prompts longer than ~800 tokens where a shorter version would work (see Step 4)
- Overuse of absolutes ("always", "never", "must") without explicit examples of edge cases
- Instructions that duplicate what the model already does by default (e.g. "be helpful and polite")
- Named entities without definitions — if the prompt mentions "the estimate workflow", is that defined anywhere reachable?

## Step 4: Token and Cost Efficiency

**MEDIUM**

- Prompts that embed the full schema when a reference to a few field names would do
- Few-shot examples longer than the expected output — trim to the minimum that conveys the pattern
- Repeating the same instruction in both system and human messages
- Verbose instructions where a concise version preserves meaning

**LOW**

- System prompts not extracted to `platform/prompts/` — per your `CLAUDE.md` pattern, prompts should live in that module, not inline in agent code

For any file flagged under this step, also report the approximate token count — a rough guide is 1 token per ~4 characters of English text.

## Step 5: Configuration Appropriateness

Per `CLAUDE.md`, the `EstimateAgent` uses `temperature=0.7`. For each agent:

- **Temperature too high (>0.7) for structured output** — if the agent returns JSON or a strict schema, temperature should usually be ≤0.3
- **Temperature too low (<0.3) for creative work** — if the agent writes copy, descriptions, or suggestions, very low temperature produces robotic output
- **Model mismatch** — `gpt-4o-mini` is fine for routine extraction; for complex reasoning or safety-critical steps consider a larger model
- **Missing timeout or retry configuration** — agents should have bounded wait times and retry behaviour on transient failures
- **Non-async usage in a FastAPI route** — use `ainvoke`, not `invoke`, per the `CLAUDE.md` AI Agent Pattern note

## Step 6: Test Coverage for Agents

**HIGH**

- Agents without any test file — every agent should have `platform/tests/test_agents_<name>.py` or similar
- Tests that hit the real OpenAI API instead of mocking (`AsyncMock` per `CLAUDE.md`)
- Tests that only cover the happy path — error paths (OpenAI down, invalid LLM response, rate limit) should also be tested

## Step 7: Severity-Tiered Report

Use the same format as `/code-review`:

```
[SEVERITY] <file>:<line> — <short title>
  Issue: <what's wrong and why it matters>
  Fix:   <suggested remediation>
```

Sort by severity. Include a count summary at the top.

## Step 8: Recommendation

| Status       | Condition                     | Meaning                                |
|--------------|-------------------------------|----------------------------------------|
| Approve      | Zero CRITICAL, zero HIGH      | Safe to deploy                         |
| Warning      | MEDIUM issues only            | Safe to deploy; improve in follow-up   |
| Block (rec.) | Any CRITICAL or any HIGH      | **Recommend revising before deploy**   |

Prompt-injection CRITICAL issues are especially high-priority because they can expose data or escalate agent capability in production. Do not wave these through.

## Integration with Other Commands

- Run this command whenever you edit any file under `platform/agents/` or `platform/prompts/`
- Per `CLAUDE.md`, prompt text edits are **TDD-exempt** — but they still need this review
- `/code-review` does a lighter pass that catches the CRITICAL prompt-injection issue; use `/agent-prompt-review` for the full pass
