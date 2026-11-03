# Part 6: OpenAI connectivity and model evaluation

Verified on 2026-11-01. Select `gpt-6-luna` with `reasoning.effort=low` for the
initial extraction, clarification/suggestions, and future refinement-chat tasks.
It passed this bounded synthetic corpus after correcting the prompt ambiguity
described below. No stronger model was needed for these checks. This is an
initial suitability decision, not an exhaustive comparison of every model.

## Client contract

The backend uses official OpenAI Python SDK 3.42.0, the fixed direct
`https://api.openai.com/v1` endpoint, and backend-only `OPENAI_API_KEY` from the
ignored root `.env`. SDK/base-URL environment overrides cannot reroute the key.
There are no tools, external document URLs, or stored conversation IDs in these
requests. API credentials never appear in frontend configuration or reports.

`AIClient` is a small injectable protocol. `OpenAIClient` sends strict JSON Schema
output requests and validates the returned JSON with Pydantic. The evaluation
schemas are deliberately small probes; Part 7 still defines the application
payloads and connects suggestions to explicit user review. The client has no
database writes and cannot apply a suggestion to a saved definition.

Before inference, the Responses input-token endpoint counts the same model,
instructions, JSON input, reasoning configuration, and output schema. Requests
over 20,000 input tokens are rejected. Inference uses a maximum of 2,000 output
tokens, including reasoning, with automatic truncation and retries disabled.
The configured timeout is 60 seconds; time spent in preflight is deducted from
the generation timeout. `store=False` disables persisted Response state.
See [official token counting](https://developers.openai.com/api/docs/guides/token-counting)
and [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

Sanitized `AIError` codes distinguish missing configuration, access denial,
unavailable model, exhausted quota, rate limiting, connection failure, timeout,
rejected request configuration, incomplete output, refusal, and invalid JSON.
Output-limit exhaustion is an error even if partial text looks parseable. Usage
is retained when a returned paid response is rejected; a transport failure may
leave final usage unknown. No raw provider diagnostic or personal text is logged.

## Live checks

The arithmetic smoke test returned structured `answer=4` for `2+2` in 3.875 s,
with 56 input tokens and 12 output tokens. The SDK's token-count and generation
endpoints both succeeded with the configured account/model.

Final quality run, elapsed times including token preflight:

| Synthetic case | Result | Seconds | Input / output tokens |
| --- | --- | ---: | ---: |
| English background, provenance, embedded instruction attack | Pass | 3.960 | 323 / 139 |
| Spanish background and unknown education | Pass | 1.973 | 318 / 108 |
| Vague job description and compensation clarification | Pass | 2.300 | 578 / 105 |
| Reference job preferences and conditional hybrid constraints | Pass | 4.456 | 643 / 409 |
| Change AI engineering priority while retaining accepted values | Pass | 2.092 | 734 / 126 |

The reference case checks Staff scope, architecture, cross-team collaboration,
learning, international scope, AI preference, remote preference, mandatory Madrid
hybrid location and two-day cap, frontend-only exclusion, and questions about
salary and the unknown office-day period. Salary remains explicitly unknown;
historical frontend experience does not override the desired exclusion.

Initial evaluation failed the two hybrid-priority checks. A separate reproduction
showed that the model retained both limits in the text but classified them as
`preferred`. The prompt had named the priorities without specifying how a hard
condition on a preferred alternative should be classified. The correction
explicitly treats “only”/“at most” conditions as mandatory, keeps them conditional
on hybrid work, and leaves the period unknown. The same five-case suite then
passed without increasing reasoning effort or changing the model. A deterministic
regression test rejects the originally observed softening of those limits.

Evidence:

- [Arithmetic smoke](evidence/AI_SMOKE.json)
- [Initial quality run](evidence/AI_EVALUATION_INITIAL.json)
- [Synthetic diagnostic proposal](evidence/AI_REFERENCE_DIAGNOSTIC.json)
- [Final quality run](evidence/AI_EVALUATION.json)

These are small synthetic examples, with no real CV/profile input. They show
inference access and representative behavior, not a production SLA, exhaustive
hallucination resistance, or performance on maximum-size documents/conversations.
Low reasoning was accepted by the API; reported reasoning usage varied and was
sometimes zero. All final cases meet the 20-second target on these inputs.
Broader workflow and document-size measurements remain in Parts 7 and 9.

## Usage and cost

Verified Standard short-context text rates for `gpt-6-luna` are $0.10 per million
input tokens, $0.01 cached input, and $0.50 output; reasoning is included in output
usage. See [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [pricing](https://developers.openai.com/api/docs/pricing).

The final five-case run used 2,596 input and 887 output tokens, estimated at
$0.0007031. Across the smoke, initial suite, diagnostic reproduction, and final
suite, 12 generations used 5,599 input and 2,113 output tokens, estimated at
$0.0016164. These are inference-usage estimates, not an invoice or a measurement
of remaining account credit. No authentication/quota errors occurred in the
live checks; those failure paths were exercised with fake responses.

The existing monthly assumption of one million input and 200,000 output tokens
still estimates $0.20. At the maximum uncached per-generation caps, the text
estimate is $0.003. Other model identifiers return an unknown cost estimate until
their rates are verified. Pricing changes, taxes, and account-specific charges
are outside these estimates.

## Local validation

Ruff and 78 combined unit/PostgreSQL tests pass with 99% statement coverage of
the current 568 backend statements. Tests use fake SDK transports or the
`AIClient` protocol and require no OpenAI credentials or inference calls. They
cover request serialization, preflight limits, timeout budgeting, access/quota/
throttling errors, malformed and incomplete output, refusals, cost accounting,
the synthetic quality gates, and existing persistence behavior.

The backend image builds with the locked SDK/native dependencies. Hosted
inference remains a Part 11 check. Part 7 subsequently implemented the API and
application schemas; its two synthetic schema/quality calls and broader backend
tests are recorded separately in [PART7_VALIDATION.md](validation/PART7_VALIDATION.md).
