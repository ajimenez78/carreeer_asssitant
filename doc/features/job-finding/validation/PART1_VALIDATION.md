# Job finding Part 1: requirements and acceptance review

Date: **2026-11-03**. Scope: execute Part 1 of the
[job-finding plan](../PLAN.md). This is a **design review**, not application-test,
source-access, AI-inference, notification-delivery or deployment evidence.

## Inputs and decisions reviewed

- Read the project instructions, current roadmap, job-finding plan and implemented
  job-definition requirements, API, persistence and assistant behavior.
- Reviewed the private ideal-job Markdown to retain Staff/software architecture,
  cross-team/learning/international scope, AI preference, Madrid hybrid conditions,
  frontend-only exclusion and genuinely unknown compensation/office-day period.
  No CV/profile contents were copied into fixtures or reports.
- The user explicitly requested functional chat throughout the feature,
  per-part validation and meaningful maintained tests without a coverage target.
- During Part 1, the user selected **in-app inbox plus daily email digest**, **daily
  09:00 Europe/Madrid search after opt-in**, and **LinkedIn first, with any fallback
  decided after Part 2 evidence**. These are recorded as user decisions in the spec.
- Initial numeric limits/retention/thresholds are specification defaults, not claims
  of user-selected spending, provider capacity or measured application performance.

Deliverables: [SPEC.md](../SPEC.md) and
[ACCEPTANCE_SCENARIOS.md](../ACCEPTANCE_SCENARIOS.md), with 24 named synthetic
scenarios and later implementation/test ownership.

## Walkthrough results

The following outcomes were checked for consistency against the written rules.
“Consistent” means the design gives an explicit answer; it does not mean a running
application has passed the scenario.

| Design walkthrough | Result | Reviewed conclusion |
| --- | --- | --- |
| Saved template → search → inspect → feedback → notification | Consistent | Only saved accepted criteria drive discovery; evidence and eligibility control inbox/email; feedback alters ordering rather than saved preferences |
| Clear English template, O-A | Consistent | Staff/architecture/AI work and explicit Spain-remote evidence fit; controlled salary/hours examples remain test data |
| Incomplete English/Spanish templates | Consistent | A usable positive term permits an explicit provisional search; optional unknowns and paused clarification do not imply readiness or block all discovery |
| Unknown hybrid attendance period | Consistent | Reference period remains unknown; hybrid matches require review, while explicit Spain-remote offers make hybrid-only restrictions inapplicable |
| Compensation/work–life evidence | Consistent | Missing salary/hours remain unknown; incompatible units/basis are not invented or converted |
| Hand-calculated scoring | Consistent | Three met plus one failed criterion = 75/100% coverage; three met plus one unknown = 100/75%; a matched exclusion still makes a 100/100% offer ineligible |
| Unsaved edits/chat suggestions during search | Consistent | Pending data remains separate; context changes make old matches stale and prevent late alerts |
| Manual restricted URL/proposal and duplicate intake | Consistent | Paste/upload fallback, retained provenance/corrections and reliable-identity deduplication preserve distinct vacancies |
| Daily 09:00 Madrid search and email digest | Consistent | Independent explicit opt-ins; digest after daily search or a saved-match-only tick; current provider/runner capability is still unproven |
| Shared chat, switching views/languages, clarification paused | Consistent | Functional chat remains available from the first UI slice, preserving typed input and requiring explicit actions/review/save |
| Feedback/reset, limits and deletion | Consistent | Bounded ordering changes are reversible; no silent preference edits, data eviction or budget-reset retries |
| Requirement #2 traceability | Complete design mapping | All six business bullets map to spec sections, named scenarios and delivery parts; cross-feature privacy/chat/recovery are also mapped |

## Part 1 checks

- [x] Define the bilingual owner flow and navigation alongside job definition.
- [x] Resolve notification channel, cadence and source-fallback policy with the user;
  specify search eligibility, feedback, retention, operating limits and cost controls.
- [x] Define reference acceptance examples using synthetic vacancies and clearly
  separate added test constraints from actual user preferences.
- [x] Record scope, decision provenance, measurable targets and provider-dependent
  follow-ups in the specification.
- [x] Define named input/outcome scenarios and review business risks; use design
  walkthroughs rather than artificial automated documentation tests.
- [x] Trace every requirement #2 bullet and review complete/incomplete bilingual
  inputs, hybrid/salary/work–life ambiguity and shared chat/review boundaries.

Documentation maintenance checks also passed: local links resolve, all 14 parts
retain separate test-maintenance/validation sections, only Part 1 is marked
complete, and the 24 scenario IDs are unique and sequential. `git diff --check`
passes. These checks do not substitute for future application tests; no automated
documentation-presence tests were added to the repository.

## Remaining work belongs to later parts

Part 2 must prove supported LinkedIn discovery/connection, runner/schedule behavior,
email provider/destination setup and actual costs/quotas. An unavailable LinkedIn
route requires the user's fallback decision after that evidence. Explicit budget
configuration is required before recurring paid inference. Part 7 calibrates
matching thresholds and Part 11 feedback adjustments using meaningful fixtures.

No application code, schema, dependencies, credentials, live workspace, external
service or schedule was changed. No model calls, messages or cloud operations were
performed. Runtime tests remain to be built within their implementation parts;
Part 1 does not report application or provider behavior as tested.

Status: **Part 1 complete and explicitly approved by the user on 2026-11-03;
Part 2 not started**. Approval covers the requirements/specification deliverables,
acceptance scenarios and design review.
The user's specific selections are distinguished from revisable specification
defaults and future capability evidence. This does not claim acceptance of a
working job-finding feature or authorize later implementation/deployment work.
