# ADR-004: LLM explanations are grounded-only, no free-form access

## Context
We want a plain-language explanation of why a specific store/SKU was flagged as at-risk. This is the only place an LLM touches the system.

## Options Considered
- **Chatbot-style**: let users ask free-form questions against the data via an LLM with tool/DB access.
- **Templated text only**: no LLM, just string templates filled with computed values.
- **Grounded single-purpose call**: LLM receives only the already-computed numeric facts for one flagged item and returns a short natural-language explanation; no tool access, no database access, no user-supplied free text in the prompt.

## Decision
Grounded single-purpose call.

## Rationale
A chatbot isn't a stated goal of this project (explicit non-goal) and introduces open-ended prompt-injection surface for no clear benefit. Pure templating is safe but produces stiff, low-value text and skips any real AI/ML engineering learning. The grounded approach gets genuine LLM-integration experience (prompting, output validation, evaluating usefulness) while keeping the attack surface bounded: the model has no tools, no untrusted input, and only ever restates numbers we've already computed and trust.

## Tradeoffs
- Less impressive/flexible than a chatbot.
- Still need to validate the LLM doesn't fabricate numbers not present in its input (output validation step required).

## Consequences
- The explanation service's prompt is built entirely from our own metric outputs — never raw user input, never arbitrary table contents.
- Output is checked (at minimum spot-checked, ideally with a simple validation rule) against the source numbers before being shown in the UI.
