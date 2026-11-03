# Job finding: acceptance examples

Defined and reviewed during **Part 1 on 2026-11-03** against [SPEC.md](SPEC.md).
These are named design scenarios with expected outcomes, not executed application
tests. Implement them at the relevant boundary as each part ships, reusing existing
suites and fixtures. Add cases for demonstrated failures, not coverage percentages.
Execution and provider evidence must be recorded separately during implementation.

## Synthetic templates and offers

`T-REFERENCE` reflects the traits in the private ideal-job example: Staff-level
software/system architecture, business-wide scope, cross-team collaboration,
learning, international work and preferred AI engineering. Remote is preferred;
hybrid requires Madrid/nearby and at most two on-site days with an **unknown period**.
Frontend-only work is excluded. “Good compensation” remains unknown, with no
invented amount. This template is a reference fixture, not a newly saved definition.

`T-CLEAR` is a synthetic variant used only for controlled examples: hybrid means
at most two days **per week** near Madrid; compensation has a mandatory minimum
of **EUR 90,000 gross/year**; work–life preference is a 40-hour week without routine
weekend work. These additions are test inputs, not claims about the owner's preferences.

`T-SCORE` contains exactly four known positive criteria of weight 1: Staff scope
(mandatory), architecture, cross-team collaboration and AI engineering (preferred).
Frontend-only work remains an exclusion. It is used for independently calculated
score examples; it does not replace `T-REFERENCE`.

| Offer | Synthetic evidence |
| --- | --- |
| O-A | Active Staff software role, architecture, cross-team/AI work, international team and learning; explicitly remote from Spain; EUR 100,000 gross/year; 40 hours/week, no routine weekends |
| O-B | Active Staff role with architecture/cross-team work, no AI work; Madrid hybrid, two office days/week; EUR 95,000 gross/year; 40 hours/week |
| O-C | Active Staff role with all four T-SCORE positives, but explicitly frontend-only |
| O-D | Staff role with architecture/cross-team work, Madrid hybrid, “two days in the office” without a period, no salary or hours stated |
| O-E | Staff architecture role, three office days/week in Barcelona, EUR 110,000 gross/year |
| O-F | Staff architecture role with cross-team work; AI involvement, compensation, hours and remote-country eligibility unstated |

Companies, source URLs/IDs, timestamps and documents used in executable fixtures
must be synthetic. Routine tests use fake providers and a controlled clock. No CV,
LinkedIn export, real email address or live vacancy is copied into committed fixtures.

## Template and discovery eligibility

### JF-01: Search the saved definition, preserving pending edits

Given saved `T-CLEAR`, an unsaved editor change excluding AI, and an unaccepted chat
proposal changing location, when Search now starts, it uses only saved `T-CLEAR`.
The effective query/source are visible; pending edits remain unchanged. After a
later explicit save, old matches are marked stale. Boundary: API/integration and
one browser journey in Parts 5, 7–8. Protects accepted-versus-proposed separation.

### JF-02: Incomplete but usable context supports an explicit provisional search

Given saved “Staff software engineering with architecture; compensation unknown,”
unassessed clarity and paused clarification, when the owner selects provisional
search, discovery may run without salary/location guesses or resumed clarification.
The provisional state is visible and readiness stays unchanged. Run the walkthrough
with Spanish input, “Ingeniería de software con alcance Staff y arquitectura;
salario por definir,” and expect the same behavior. Boundary: eligibility unit/API
tests and bilingual browser coverage in Parts 5, 8–9.

### JF-03: No usable query or source access is reported honestly

Given only “not frontend,” or a missing definition, the UI explains the absent
positive search context and offers editing/chat; manual intake is still accessible.
Given a valid template but unproven LinkedIn discovery access, show the access
limitation, not fabricated vacancies or an automatic fallback. An ordinary login
or posting-only API is insufficient evidence. Boundary: eligibility/connector
contracts and source feasibility in Parts 2, 5, 8.

### JF-04: Optional unknowns do not prevent a useful search

Given `T-REFERENCE` with unknown compensation and optional company benefits, when
search runs, keep those fields unknown and query the known role/scope. Do not force
repeated clarification, invent a salary or mark the definition ready. Boundary:
query-generation unit tests and Part 8 integration.

## Intake and provenance

### JF-05: Manual text, public URL and supported documents persist

Given an English vacancy or Spanish recruiter proposal, when text/URL/text-based
PDF/`.doc`/`.docx`/Markdown is submitted and explicitly saved, reopen the same offer
with provenance, source text and corrected fields intact. Source text never changes
the ideal-job preferences. Boundary: parser/intake integration and a representative
bilingual browser journey in Parts 3–6; reuse existing parser tests.

### JF-06: Restricted or unusable sources preserve recovery paths

Given a login-walled/removed URL, unsafe redirect/internal destination, scanned
PDF or oversized file, when intake fails, preserve entered text/URL and show the
appropriate paste/upload/edit path. A reference-only URL is not a scored listing.
Storage/commit failure leaves retryable state without falsely reporting a durable
upload; deletion failure leaves queued cleanup. Boundary: existing URL protections
plus new intake/storage integration and targeted browser failure in Parts 4–5.

### JF-07: Deduplicate reliable identities and preserve ambiguous proposals

Given the same source vacancy via two tracking URLs, reimport resolves to one
record and keeps manual corrections. Given similar title/company without matching
source identity, retain both and show a possible duplicate. A different location/
requisition is not silently merged. Boundary: deduplication unit and persistence
integration tests in Parts 3–4, extended by discovery in Part 8.

## Fit, hard constraints and uncertainty

### JF-08: Staff architecture/AI offers outrank narrower relevant work

Given `T-REFERENCE`, compare O-A and a version of O-B with every other applicable
positive criterion equal. O-A scores higher because AI and remote preferences are
met more strongly; show the per-criterion evidence. Historical frontend CV experience
does not weaken the frontend-only exclusion. Boundary: labeled ranking fixtures in
Part 7 and grounded chat explanation in Part 12.

### JF-09: A high numeric score cannot override exclusion or mandatory failure

Given `T-SCORE`, O-C has four met positive criteria: base fit **100**, coverage
**100%**, but it is ineligible because frontend-only work is excluded. Given
`T-CLEAR`, O-E violates the hybrid city and attendance constraints despite high
compensation. Neither offer creates an interesting-match notification. Boundary:
deterministic matching tests in Part 7 and notification eligibility in Part 10.

### JF-10: Conditional hybrid restrictions keep unknown periods unknown

Given `T-REFERENCE`, O-D needs review because the office-day period is unresolved;
O-B also cannot prove the owner's unknown intended period. Do not assume weekly.
Given `T-CLEAR`, O-B meets Madrid/two-days-per-week constraints. O-A's explicit
Spain-remote arrangement makes hybrid-only constraints not applicable. Boundary:
criterion-comparison fixtures in Part 7.

### JF-11: Compensation and work–life balance need compatible evidence

Given `T-CLEAR`, O-A meets the stated salary and hours/weekend criteria; O-D has
unknown salary/hours and cannot satisfy the mandatory salary minimum. A salary
stated only as “100k,” USD/year or EUR/month net does not prove EUR 90,000 gross/year.
Do not invent exchange rates, tax conversion or work–life claims. Given
`T-REFERENCE`, “good compensation” stays unknown instead of borrowing the test
minimum. Boundary: extraction/comparison corpus in Parts 6–7.

### JF-12: Partial evidence, stale matches and hand-calculated scores

Given `T-SCORE`, an offer with Staff/architecture/cross-team met and AI not met has
base fit **75**, coverage **100%**. If AI is unknown instead, fit is **100** over
known criteria with coverage **75%**; missing evidence stays visible. No known
positive criteria means unscored. These are hand-calculated expectations independent
of production code. A changed criterion/offer/policy marks results stale and rejects
late results; viewing/saving alone does not recalculate or invoke AI. Boundary:
score unit tests and real persistence/concurrency tests in Part 7.

### JF-13: Eligibility thresholds include uncertainty and availability

Given initial thresholds, base fit 75 and coverage 75% with all hard constraints
satisfied and source-confirmed active availability within 24 hours qualifies.
Fit 74, coverage 74%, unknown salary under `T-CLEAR`, an exclusion, closed status,
expired availability check, dismissal or a stale match does not qualify. O-F's
unstated remote-country eligibility is not proof of Spain eligibility. Boundary:
notification eligibility tests in Parts 7, 10; use a fixed clock for boundaries.

## Durable discovery and recurrence

### JF-14: Failures, duplicates and cancellation retain bounded progress

Given a multi-page run with duplicates and 401/403/429/transient failures, retain
successful offers, show partial/failure separately from zero matches, and respect
retry/time/page/candidate/AI/budget caps across restarts. Repeated triggers do not
overlap runs. Cancel or delete context before completion and reject late current
matches/alerts. Boundary: fake-connector contracts and real PostgreSQL run-state
integration in Parts 2, 8–9.

### JF-15: Prove real discovery and necessary account connection separately

Given the selected permitted source route, a bounded live probe must return actual
vacancy IDs/URLs and measured usage. If connection is required, verify appropriate
scopes and revoke/disconnect behavior with backend-only credentials. If access is
unavailable, record evidence and request the user's fallback choice. Fake adapters
only prove local behavior. Boundary: explicit source evidence in Parts 2, 8.

### JF-16: Daily Madrid recurrence survives time and execution changes

Given explicit opt-in, daily search is due at 09:00 Europe/Madrid in both standard
and daylight-saving time. With a controlled clock, duplicate/missed ticks, sleep/
restart, expired credentials and pause/budget exhaustion cannot cause overlapping
or unbounded catch-up. Record real schedule-triggered delivery separately; a
manual dispatch is insufficient. Chat remains usable with clarification paused.
Boundary: scheduler unit/integration and observed execution in Parts 9, 14.

## Inbox and daily email

### JF-17: One qualifying event, useful digest and explicit setup

Given new eligible offers and completed email setup/opt-in, save one inbox event
per offer and send one daily digest with up to ten newly qualifying offers. Links
open the authenticated workspace; email contains no CV/chat/preference excerpts.
If no new offers qualify, send no digest. Repeat runs/refreshes without duplicate
events; read/dismiss persists. Email off leaves inbox usable. Boundary: fake notifier
and inbox browser tests in Part 10; explicit selected-channel proof in Parts 2, 14.
If more than ten offers qualify, unsent eligible offers remain pending for later
digests rather than being falsely marked emailed or silently discarded.

### JF-18: Delivery retries, digest timing and independent controls

Given a partial daily run or transient/ambiguous email response, retain truthful
pending/sent/failed state and bounded retries without resetting daily limits.
New matches after the digest wait until the next day. With search disabled but
email enabled, daily processing only considers saved qualifying matches. No
provider/destination is assumed from selecting email in Part 1. Boundary:
notification/runner integration in Parts 9–10, real delivery observation in Part 14.

## Feedback and learning

### JF-19: Relevant feedback changes later ordering without rewriting preferences

Given otherwise comparable eligible offers and an explicit work-arrangement reason,
subsequent ordering reflects that reason within bounded adjustments and explains
the difference from base fit. A closed/duplicate/temporary reason does not create
a lasting exclusion. Missing hard-constraint evidence stays unresolved. Boundary:
before/after ranking fixtures and feedback integration in Part 11.

### JF-20: Correcting/removing feedback and reset restores the expected baseline

Given saved interested/not-interested feedback, edit/remove it and recompute using
the current policy. Reset removes its ranking effect; accepted criteria remain
unchanged. Contradictory/sparse feedback cannot dominate ordering. A proposed
permanent preference still needs review/save and changed ranking does not create
duplicate alerts. Boundary: persistence/ranking tests and one UI journey in Part 11.

## Shared chat, privacy and recovery

### JF-21: Functional shared chat preserves input on every job-finding view

Given sent conversation, an unsent chat message and unsaved definition/intake edits,
navigate offer list/detail, intake, search/results, inbox, feedback and settings;
minimize/reopen, switch English/Spanish and use keyboard/mobile controls. Preserve
all input, keep the launcher reachable beside dialogs, and send a contextual reply
even during loading/error/search states. Reuse/extend one shared navigation journey
as views ship; a visible launcher alone is insufficient. Boundary: Parts 5–12.

### JF-22: Chat is grounded and proposed actions remain explicit

Given a saved current match, ask why it fits and get its evidence/unknowns, not
invented vacancies. Chat can propose intake, search or feedback but cannot silently
save them, enable recurrence or change preferences. A reviewed preference proposal
only changes saved context after explicit save. Deleted/stale offer references,
listing prompt injection and AI failure leave accepted data and typed input safe.
Boundary: assistant API and shared browser tests in Parts 6–8, 11–12.

### JF-23: Limits, privacy and deletion protect retained data

Given an unauthenticated request, no offer, private source or attachment is readable/
writable. At offer/file/budget capacity, show the limit and preserve existing records;
no automatic eviction or budget-reset retry. Delete an offer/source/whole definition
and remove its agreed data/future AI context, cancel work and queue original cleanup.
Retained backups expire after seven days. Boundary: API, storage and persistence
integration in Parts 3–4, 8–11, 14; no real personal documents in routine tests.

### JF-24: New feature data survives deployment and isolated recovery

Given populated synthetic definition/chat/offers/matches/runs/feedback/inbox and
attachments, replace the application image and restore SQL/original backups into
isolated resources. Compare business records, relationships, original bytes and
credentials, excluding explicitly transient session/diagnostic comparisons where
appropriate. Measure actual resource usage and observe scheduled backup delivery
separately. Existing live workspace is preserved. Boundary: release/recovery checks
in Parts 13–14, with provider limitations recorded rather than inferred to pass.
