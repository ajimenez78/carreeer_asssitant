# Job finding implementation plan

Business requirement: **#2, Job finding**. Created: **2026-11-03**.
Status: **proposed plan; implementation has not started**. The request authorizes
planning and documentation reorganization. Defaults below need agreement in
Part 1; external capabilities need evidence in Part 2. No provider access,
subscription, LinkedIn connection, schedule or deployment is authorized by this file.

This feature extends the approved [job-definition MVP](../job-definition/PLAN.md).
The [project roadmap](../../PLAN.md), [documentation index](../../README.md),
[existing API](../../architecture/BACKEND_API.md), and
[persistence contract](../../architecture/PERSISTENCE.md) describe the starting point.
The MVP's eleven part numbers remain historical; the parts below belong to job finding.

Each part separates implementation tasks from a validation checklist. Check off
validation items only after recording the executed check and its result in the
feature's validation notes, with sanitized evidence where useful. Leave blocked
or unexecuted checks unchecked; explain conditional checks that do not apply.

## Testing approach for every part

Build and maintain tests alongside each implemented behavior in its own part;
Part 13 integrates these tests rather than postponing their creation. Select
cases from business rules, realistic failures, data-loss risks and observed bugs.
Every test should identify the behavior it protects and assert an observable
outcome using expectations independent of the implementation.

Use focused unit tests for decision logic, real disposable PostgreSQL integration
tests for persistence/concurrency, and browser tests for user-visible journeys.
Extend existing suites and reuse synthetic fixtures instead of duplicating the
same assertions at every layer. Fake external services in routine tests; keep
bounded live capability checks separate. Avoid assertions tied to private helper
calls, exact AI wording or incidental markup. When fixing a bug, reproduce its
cause with a regression test at the relevant boundary.

Coverage is a diagnostic for finding untested meaningful behavior, not a numerical
target or release gate. Do not add tests for trivial accessors, framework behavior,
document existence or implementation details solely to increase coverage. Maintain
useful tests as behavior changes, and remove redundant or obsolete cases. Parts
that only make planning/access decisions use acceptance walkthroughs and recorded
evidence; runnable tests are added when there is actual behavior to protect.

## Outcome and boundaries

The owner can find relevant vacancies using the current saved ideal-job definition,
add a vacancy or recruiter proposal manually, understand each match score, receive
notifications of interesting new offers, and improve ranking through feedback.
LinkedIn is the intended primary initial discovery source. The feature must be
honest about unavailable sources, incomplete listing details and uncertain matches.

Preserve one private owner and one current editable definition, with explicit
review/save actions and no definition revision-history feature. Keep English and
Spanish interfaces/content, the persistent language switcher and the floating
assistant throughout definition and discovery. Preserve conversations, unsent chat
input and pending editor/intake changes when navigating or minimizing. Changes
proposed to the saved definition still require review and explicit saving.

Confirmed on 2026-11-03: **the chat-interface assistant is required throughout
job finding, starting with its first UI delivery in Part 5**. Keep the same
floating chatbot available on the offer list/detail, manual-intake, search/results,
notification, feedback and search-settings views, including empty, loading and
error states. It remains available while a search runs and clarification is paused.
Keep its launcher accessible alongside dialogs without obscuring their controls.
Chat is a shared interface alongside the workflow, never a numbered step.

As each capability ships, the assistant can help with that capability using saved
context: preparing searches or manual offers, explaining matches and missing
details, reviewing interesting offers and proposing feedback. Keep proposed
actions separate from execution; saving changes or starting/configuring a search
requires an explicit user action. Part 12 completes the contextual integration;
assistant availability and support for delivered capabilities must not wait for it.

Use the existing Next.js static export and FastAPI application, PostgreSQL/Alembic,
private R2 and direct backend OpenAI client. Reuse authentication, public-URL
protections, parsers, usage reporting and backup/recovery tooling where appropriate.
Keep search connectors behind a small Python interface; introduce extra services
only if a demonstrated requirement needs them. Check current stable compatible
dependency versions when implementation adds packages.

Skill-development plans, application pipelines, interview preparation, automatic
applications, recruiter messaging and support after joining a company are later
features. This plan adds no workflows or empty tables for those phases.

## Requirement coverage and delivery slices

| Requirement #2 capability | Parts | Acceptance evidence |
| --- | --- | --- |
| Agent actively finds jobs from the saved definition | 2, 8, 9 | Real permitted source returns traceable vacancies; bounded runs survive retries and scheduled execution |
| LinkedIn first; request account connection if needed | 1, 2, 8 | Supported LinkedIn discovery route demonstrated, or an explicitly agreed scope change; connection only when it grants required capabilities |
| Manually add positions and proposals | 3–6 | Bilingual manual text/URL/document workflow persists an editable, deduplicated offer |
| Score offers against the ideal job | 6–7 | Evidence-based score, hard-constraint checks, unknowns and stale-result handling |
| Notify about the most interesting offers | 9–10 | New qualifying matches delivered through the agreed channel without duplicate alerts |
| Learn from feedback | 11 | Saved feedback changes later ordering predictably and can be corrected/reset |
| Shared assistant and safe release | 5, 12–14 | Navigation/input preservation, reviewed proposals, full local regression and recovery checks |

Delivery slices: Parts 3–7 provide useful manual intake and matching; Part 8 adds
on-demand active discovery; Parts 9–12 add recurring discovery, notifications,
learning and expanded assistant support; Parts 13–14 verify and release the whole
feature. The assistant is already required in the first UI slice and remains
available throughout subsequent slices.
Manual import, a LinkedIn search link or a fake connector alone does not satisfy
active discovery. If LinkedIn access cannot be obtained, report that limitation
and obtain a concrete source/scope decision before claiming full completion.

## Proposed defaults and decisions to settle

| Topic | Proposal for Part 1 | Open decision or evidence |
| --- | --- | --- |
| Search context | Use only saved accepted criteria; show their summary before starting. Reviewed background may support matching, without becoming desired preferences. | Define the minimum usable search template; a provisional search from an incomplete definition must be explicitly chosen and labeled. Clarification pause is independent of search. |
| Discovery sources | Prioritize a supported LinkedIn route; accept LinkedIn links/pasted offers immediately. Add a permitted employer/feed/API source only when agreed. | Actual read/search access, available fields, freshness, storage permissions, quotas and price. |
| Cadence and budgets | Start with explicit on-demand runs; recurring search disabled until configured. | Choose daily/weekly cadence, timezone, maximum pages/results/calls/run and monetary limits before activation. Include wake-up and retry costs. |
| Notifications | Persist an in-app inbox with unread state; suggest a daily digest of new eligible matches. | Confirm whether an external channel is required, then select provider, destination, delivery cadence and price. No email integration is assumed. |
| Matching | Explain a 0–100 fit score alongside constraint eligibility, evidence coverage and missing details. | Agree criterion weights, partial-match rules, notification threshold and calibration examples in Part 7. A score is not a hiring probability. |
| Feedback | Interested/not interested plus optional reasons; bounded transparent personalization of ordering. | Agree reasons, adjustment limits and reset behavior. Feedback never silently edits saved criteria. |
| Retention and limits | Retain saved offers until deleted; retain backups for seven days under the existing policy. Reuse supported document formats and parser limits. | Agree offer attachment quota, discovered-result/run retention and list limits separately from the existing five background-document slots. |
| Operating cost | Remain within agreed hosting/backup allowances; meter every search, extraction, match and notification operation. | Verify source/notification/AI prices and account allowances; paid additions require explicit choice. |

Part 1 records agreed choices in `SPEC.md` beside this plan. Part 2 records source
and execution evidence in `SOURCE_ACCESS.md`. Create those files when the work is
done; neither document exists as an agreed contract yet.

## LinkedIn feasibility evidence

The official [Job Posting API overview](https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/overview)
describes restricted posting integrations, not general vacancy discovery for job
seekers. This does not establish access to job search. LinkedIn's
[automated activity guidance](https://www.linkedin.com/help/linkedin/answer/a1340567/prohibited-software-and-extensions)
also restricts third-party website automation. These sources were checked during
planning on 2026-11-03; recheck capabilities and terms during Part 2.

Planning inference: an ordinary LinkedIn sign-in or access to a posting API must
not be treated as permission or capability to search all vacancies. Validate an
authorized API/partner/data-provider route before implementation. Only request a
connection if that route actually needs it and supports this use. Do not build
around passwords, copied session cookies, private endpoints or login automation.
Manual paste/upload remains available when a URL cannot be retrieved. A permitted
alternative source can unblock development but changes the LinkedIn-first scope
only with an explicit decision.

## Part 1: Agree the smallest complete job-finding scope

Dependency: this plan is reviewed before implementation starts.
Deliverable: an agreed feature specification and reference acceptance examples.

- [ ] Walk through saved definition → search/manual add → inspect score → feedback
  → notification, in English and Spanish; define navigation alongside job definition.
- [ ] Resolve the table above, including provisional searches, recurring-run opt-in,
  notification channel, limits, deletion and any paid-source decision.
- [ ] Specify acceptance examples derived from the reference ideal job using
  synthetic offers: Staff architecture scope, Madrid hybrid constraints,
  AI-engineering preference, compensation and work–life balance.
- [ ] Record scope, decisions and measurable targets in `SPEC.md`; distinguish
  accepted behavior from provider-dependent work and later features.

### Tests and test maintenance

- [ ] Define named acceptance scenarios with inputs and expected user outcomes for
  the reference job, incomplete criteria and explicit review/save boundaries; reuse
  them as implementation fixtures in later parts.
- [ ] Review these scenarios against business requirements and risks. Validate
  planning decisions through walkthroughs rather than artificial document tests.

### Validation checklist

- [ ] Trace every requirement #2 bullet to an observable acceptance outcome and
  implementation part; record any unresolved source-access decision and next step.
- [ ] Walk through complete and incomplete saved definitions in both languages;
  optional unknowns/skips do not force clarification or block a usable template.
- [ ] Review the synthetic reference scenarios, including Staff scope, conditional
  Madrid hybrid limits, compensation and work–life balance, against the specification.
- [ ] Confirm the agreed scope includes functional shared chat from the first UI
  delivery, explicit save/review, notification delivery and feedback-based ranking.
- [ ] Record agreed defaults, measurable targets and remaining provider-dependent
  decisions in `SPEC.md` without presenting proposals as approved choices.

## Part 2: Prove source access and background execution

Dependency: Part 1 defines the intended sources and limits.
Deliverable: a small feasibility spike and a recorded connector/execution decision.

- [ ] Verify LinkedIn discovery options using current primary documentation and
  actual permitted access. Record fields, pagination, location filters, freshness,
  attribution, retention, quotas, account scopes and total cost. Distinguish
  indexed snippets, full listings and posting-only APIs.
- [ ] Demonstrate one bounded real discovery request. If no supported LinkedIn
  route exists for this owner, document the evidence and obtain a specific
  alternative/access decision; manual import remains an independent workstream.
- [ ] Test bounded Python execution with persisted PostgreSQL run state. Compare
  an external GitHub Actions runner using the existing operations approach with
  authenticated bounded API batches; select one that survives Render sleep/restart.
  Keep the single web service and avoid relying on in-process timers/tasks.
- [ ] Confirm present hosting, database, scheduler, source and notification
  allowances. Record authentication, secrets, budget enforcement, recovery and
  scheduling approach in `SOURCE_ACCESS.md` before enabling external automation.

### Tests and test maintenance

- [ ] For connector/runner code retained from the spike, build focused contract
  tests for response identity, retry limits and persisted restart recovery using
  synthetic responses; carry those tests into Parts 8–9.
- [ ] Keep the permitted live discovery probe reproducible with sanitized output
  and measured usage. Record access-only findings as evidence rather than tests
  that merely assert provider configuration values.

### Validation checklist

- [ ] Demonstrate permitted retrieval of real vacancies with source IDs/URLs,
  available fields, freshness and measured latency/usage; posting-only access
  does not count as discovery access.
- [ ] Record evidence for the supported LinkedIn route or the explicit alternative/
  access decision; distinguish unknown access or pricing from verified availability.
- [ ] Interrupt and retry the selected runner approach; persisted progress survives
  sleep/restart, with no duplicate run or budget overrun.
- [ ] If account connection is needed, verify required scopes, backend-only secret
  handling, revocation/disconnection and truthful failure after access is revoked.
- [ ] Record source/runner quotas, measured costs, operating constraints and the
  execution decision in `SOURCE_ACCESS.md` before external automation is enabled.

## Part 3: Add the minimal offer schema and API contract

Dependency: Part 1; source-specific fields follow the Part 2 decision.
Deliverable: migration and private API contracts for the manual-intake slice.

- [ ] Model an offer with stable identity, title/company, description, source kind,
  original/canonical URL, external ID, source timestamps, language and active/
  closed/unknown availability. Preserve provenance and manual corrections.
- [ ] Define normalized fields for role/scope, skills, compensation, geography,
  work arrangement and work–life balance with explicit unknowns. Keep offers
  separate from definition background documents and preferences.
- [ ] Add only the tables needed now, indexes/uniqueness for source identity,
  owner-scoped CRUD/list/filter payloads, bounded pagination and deletion behavior.
  Specify how whole-definition deletion removes associated discovery data.
- [ ] Update shared API/persistence docs with implemented contracts. Define result
  shapes for later scores/runs without creating unused workflow infrastructure.

### Tests and test maintenance

- [ ] Extend real PostgreSQL migration/integration tests to protect existing data,
  source-identity uniqueness and deletion behavior, including failed transactions.
- [ ] Add API boundary tests for private access, invalid payloads and stable
  pagination; reuse existing authentication tests and shared synthetic fixtures.

### Validation checklist

- [ ] Migrate a disposable restored copy from existing head `0005` and repeat the
  migration; existing definitions, credentials, sources and conversation stay unchanged.
- [ ] Verify valid offer/proposal records round-trip with provenance, explicit
  unknowns and manual corrections; invalid payloads fail without partial writes.
- [ ] Reject unauthenticated access to every new offer endpoint and attachment.
- [ ] Exercise source-identity uniqueness, foreign keys, bounded pagination and
  stable list/filter results with synthetic PostgreSQL fixtures.
- [ ] Verify offer and whole-definition deletion follow the agreed association,
  attachment-cleanup and retention rules; shared contract docs match actual payloads.

## Part 4: Implement manual text, URL and document intake

Dependency: Part 3.
Deliverable: persistent manual offers and recruiter proposals through the backend.

- [ ] Accept a pasted listing/proposal or public URL; preserve submitted content
  and its provenance. Reuse bounded URL retrieval and upload/paste fallback for
  login walls, removed pages or insufficient snippets.
- [ ] Accept offer documents using existing PDF, `.doc`, `.docx` and Markdown
  parsing/storage, the agreed offer quota and 10 MiB file limit. OCR stays deferred.
- [ ] Canonicalize tracking URLs; use source IDs and normalized URLs for reliable
  deduplication. Flag ambiguous company/title/location similarities for review;
  do not merge distinct vacancies automatically or discard manual edits.
- [ ] Support edit, explicit save, deletion and safe retry after partial failures.
  Clarify when a supplied URL is stored as a reference without retrieved text.

### Tests and test maintenance

- [ ] Add focused deduplication tests for tracking URLs, distinct source IDs and
  ambiguous same-title vacancies; reuse parser/URL-security tests, extending them
  only for new offer-specific behavior.
- [ ] Add intake integration tests for text/URL/document round trips and failures
  between storage and database writes; assert retained input, safe retries and cleanup.

### Validation checklist

- [ ] Add, save, reload, edit and delete synthetic offers/proposals through text,
  URL and each supported document format, preserving content and provenance.
- [ ] Reimport a known source ID/canonical URL without creating a second offer;
  ambiguous company/title/location matches remain separate and preserve manual edits.
- [ ] Exercise inaccessible/removed/login-required URLs and upload/paste fallback;
  reference-only URLs are clearly distinguished from retrieved descriptions.
- [ ] Reject internal-network destinations, unsafe redirects, unsupported/scanned
  documents and uploads exceeding the agreed size/quota limits.
- [ ] Inject retrieval, storage and cleanup failures; retries preserve submitted
  content, avoid duplicate records and expose pending cleanup accurately.

## Part 5: Add bilingual offer browsing and manual-entry UI

Dependency: Part 4.
Deliverable: an end-to-end manual-intake workflow alongside job definition.

- [ ] Add Job finding / Buscar empleo navigation, offer list/detail and Add offer
  form with loading, empty, validation, retry and expired-session states.
- [ ] Show provenance, missing fields, last source check and explicit edit/save/
  delete controls. Preserve drafts during navigation and failed requests.
- [ ] Add bounded filtering/sorting using fields available so far; avoid implying
  a scored or searched result before those capabilities exist.
- [ ] Keep the existing floating chat assistant mounted above feature navigation
  and available on every job-finding view/state from this first UI delivery.
  Preserve its conversation/composer and unsaved definition/intake input across
  both features, mobile layouts and language changes. Add contextual help for
  manual intake now and extend it as later capabilities ship.

### Tests and test maintenance

- [ ] Extend existing desktop/mobile browser suites with manual offer save/edit/
  delete, failure/session recovery and keyboard navigation in both languages.
- [ ] Extend shared assistant/navigation tests to protect sent conversation,
  unsent composer and pending form input across feature/language changes and
  minimizing; assert visible behavior rather than incidental component structure.

### Validation checklist

- [ ] Complete add → save → reload → edit → delete in English and Spanish on
  desktop/mobile, using keyboard navigation and accessible form controls.
- [ ] Exercise empty/loading/error and expired-session states; retry or sign-in
  recovery retains typed intake and definition edits without implicit saving.
- [ ] Switch feature views and interface language; offer content, pending forms,
  conversation and unsent chat input remain intact.
- [ ] Open the floating assistant, send a message, minimize/reopen and navigate
  from every delivered job-finding view; the launcher remains reachable alongside
  dialogs and the assistant provides contextual help for delivered capabilities.
- [ ] Repeat chat-preservation checks in each later UI slice, including during
  active search and provider failures when those capabilities become available.
- [ ] Run existing job-definition browser regressions; reviewed proposals still
  require explicit saving and no numbered Chat step is introduced.

## Part 6: Extract trustworthy structured offer facts

Dependency: Parts 4–5.
Deliverable: bounded extraction with field-level provenance and correction.

- [ ] Reuse deterministic parsing first and the backend AI client when needed.
  Separate listing instructions from system instructions; validate structured
  output and evidence against the retained source text.
- [ ] Extract listed requirements and benefits without inventing salary, currency,
  pay period, office frequency, seniority or geography. Keep vague/contradictory
  data unresolved. Mark extracted values and support explicitly saved corrections.
- [ ] Preserve user corrections when listings refresh; present conflicting updates
  for review. Keep offer requirements separate from the user's actual background
  and desired criteria; never apply listing text to the definition.
- [ ] Add an explicit extraction action for manual offers. Automated runs may
  extract within their agreed limits after opt-in. Reuse unchanged source results;
  capture token/cost/latency and failures without logging private content.

### Tests and test maintenance

- [ ] Use the injectable AI client to test unsupported facts, contradictory values,
  prompt injection, invalid/refused responses and preservation of manual corrections.
  Assert accepted fields/provenance and unchanged saved criteria, not exact prose.
- [ ] Maintain a small labeled English/Spanish offer corpus for explicit extraction
  evaluations; add cases for observed failures and reuse it in matching evaluations.

### Validation checklist

- [ ] Evaluate a bilingual synthetic corpus of complete/vague listings and recruiter
  proposals; extracted fields cite source evidence and missing values stay unknown.
- [ ] Check salary currency/pay period, office frequency, seniority and geography
  against source text; contradictory details remain visibly unresolved.
- [ ] Exercise embedded prompt injection, malformed/refused output, timeout and
  quota failures; no listing instructions change saved criteria or system behavior.
- [ ] Refresh corrected offers and retry failed extraction; raw content and saved
  corrections survive, conflicting changes require review and unchanged text is reused.
- [ ] Verify page loads and ordinary saves make no AI calls; explicit/opted-in
  extraction enforces limits and records sanitized usage, cost and latency.

## Part 7: Score and explain offer fit

Dependency: Part 6 and agreed saved-definition semantics from Part 1.
Deliverable: versioned, explainable comparisons against the saved ideal job.

- [ ] Compare each accepted criterion to supported offer evidence as met, partial,
  not met or unknown. Apply conditional constraints correctly: a Madrid hybrid
  rule applies to hybrid offers; an unknown office-day period remains unknown.
- [ ] Propose a deterministic score: `100 × sum(weight × match) / sum(weight)`
  over known positive criteria, with met = 1, partial = 0.5, not met = 0.
  Report known-weight coverage against all evaluable positive criteria; return
  unscored when no criterion is known. Agree weights and partial rules using
  reference examples before release. Unknown ideal values are not requirements.
- [ ] Show mandatory/excluded checks separately. A proven mandatory violation or
  excluded characteristic makes an offer ineligible for recommendation regardless
  of score; an unknown hard constraint requires review. Missing salary or location
  cannot become a satisfied constraint or a confident high-match notification.
- [ ] Store definition/context, offer-content and scoring-policy fingerprints,
  timestamp, per-criterion evidence and model/usage metadata. Saved criteria or
  offer changes mark results stale; late results cannot overwrite newer context.
  Recompute explicitly or in an opted-in run, never on page load/save.

### Tests and test maintenance

- [ ] Build independently hand-calculated ranking fixtures for hard constraints,
  conditional hybrid work, unknowns and evidence coverage; assert expected ordering
  and eligibility instead of copying production scoring logic into the tests.
- [ ] Add persistence/concurrency tests for stale fingerprints and late results;
  extend the shared browser/chat suite to verify visible score explanations.

### Validation checklist

- [ ] Verify deterministic scores and ordering against labeled reference offers:
  Staff/AI scope, frontend-only exclusion, remote/conditional Madrid hybrid,
  salary currencies/pay periods, missing benefits and vague listings.
- [ ] Recalculate score/coverage from recorded weights and evidence; missing values
  do not count as satisfied criteria and an entirely unknown match is unscored.
- [ ] Verify proven mandatory/excluded violations block recommendation regardless
  of numeric score; unknown hard constraints remain review-required.
- [ ] Change saved criteria, offer content or scoring policy during a calculation;
  late results cannot replace newer context and stale matches cannot trigger alerts.
- [ ] Confirm recomputation requires an explicit action or opted-in run; page loads
  and saves do not invoke AI. Chat explanations use the same saved score/evidence.
- [ ] Evaluate the cheapest suitable model on the new bilingual comparison corpus
  and record quality, latency and cost separately from historical MVP evaluations.

## Part 8: Deliver on-demand active discovery

Dependency: Parts 2 and 7; the selected source must have demonstrated access.
Deliverable: Search now finds, persists and ranks real source-linked vacancies.

- [ ] Build queries from the accepted saved template, including role synonyms,
  location/work arrangement and negative constraints without overfiltering
  unknown listing fields. Show the effective template and source selection.
- [ ] Implement the selected connector behind a small search/detail interface.
  Keep a stable run ID, source cursor, effective-template fingerprint and durable
  queued/running/completed/partial/failed/canceled state with bounded work batches.
- [ ] Ingest through existing deduplication/extraction/scoring. Record source
  failures separately from zero matches, rate-limit backoff and partial results;
  allow cancel/retry without repeating successful paid work unnecessarily.
- [ ] Enforce one active run per owner and total limits across retries. Discard
  late writes after cancellation/context deletion; mark results from an older
  template stale after definition changes. Treat raw provider content as untrusted.

### Tests and test maintenance

- [ ] Extend the Part 2 connector contract tests with realistic pagination,
  duplicate IDs, rate limits and partial responses; verify persisted offers and
  run outcomes instead of asserting internal connector call sequences.
- [ ] Add real PostgreSQL run-state/concurrency tests for interruption, cancellation,
  duplicate starts and changed context, plus a browser search/results/chat journey.

### Validation checklist

- [ ] Verify generated queries use saved accepted criteria and preserve relevant
  synonyms/conditional constraints without filtering out unknown listing fields.
- [ ] Use a fake provider to exercise pagination, 401/403/429, empty results,
  duplicate/expired listings and partial failures; show failures separately from zero matches.
- [ ] Interrupt, resume, cancel and retry runs; persisted progress and completed
  work are reused, concurrent starts do not overlap and total limits span retries.
- [ ] Change/delete the definition during a run; reject invalid late writes and
  visibly mark results produced from an older template as stale.
- [ ] Execute a bounded permitted live search with traceable source URLs and
  measured usage/cost; generated offers or a fake adapter are not live evidence.
- [ ] Verify chat remains usable during search and failures, explains delivered
  results from saved evidence, and starts a proposed run only after explicit action.

## Part 9: Add opted-in recurring discovery

Dependency: Part 8 and the Part 2 execution decision.
Deliverable: scheduled discovery that works without an open browser.

- [ ] Persist enable/pause, cadence, timezone, last/next run and cumulative budgets.
  Keep recurring discovery disabled until explicitly configured by the owner.
- [ ] Implement the chosen external runner/batch trigger with scoped backend-only
  credentials. Use idempotent run identity, persisted progress and bounded retry
  after Render wake-up; recover abandoned work without overlapping runs.
- [ ] Use the latest usable saved template at run start. Pause/ask for review when
  deletion, revoked source access or unusable criteria prevent a valid run.
  Do not start automatic clarification or silently change accepted preferences.
- [ ] Display last success, partial/failure status, skipped budget-limited runs and
  missed schedules. Keep discovery scheduling independent from daily backups.

### Tests and test maintenance

- [ ] Use an injectable clock to test timezone/DST, missed schedules, budgets and
  pause/cancel behavior deterministically, without wall-clock sleeps.
- [ ] Extend runner integration tests with duplicate triggers, expired claims and
  wake-up/restart failures; assert one bounded run and accurate persisted status.
  Keep actual schedule delivery as a separate observed operational check.

### Validation checklist

- [ ] Verify schedules stay disabled until configured, and enable/pause, cadence,
  timezone and last/next run persist across reload and restart.
- [ ] Exercise duplicate triggers, Render sleep/wake, interrupted batches, missed
  slots and timezone/DST boundaries without overlapping or unbounded catch-up runs.
- [ ] Test expired/revoked credentials, exhausted budgets and pause/cancel races;
  truthful run status explains failures/skips and prevents unauthorized continuation.
- [ ] Verify each run uses the latest usable saved template; deletion or unusable
  criteria pauses execution without automatic clarification or preference changes.
- [ ] Observe and record a real schedule-triggered run with bounded usage;
  manual dispatch or a configured cron expression alone is insufficient evidence.
- [ ] Confirm search scheduling/status and credentials remain independent from
  backups, with chat accessible on scheduling views and during background runs.

## Part 10: Notify about new interesting offers

Dependency: Parts 7–9; channel and threshold agreed in Part 1.
Deliverable: useful, deduplicated notifications with visible delivery state.

- [ ] Define interesting as a fresh non-stale result above the agreed score and
  coverage thresholds, with satisfied hard constraints, active/verified availability
  and no dismissal. Explain when an offer needs review instead of qualifying.
- [ ] Persist a notification inbox with read/dismiss actions and stable offer/event
  identity. Avoid alerts for duplicate imports, repeated runs, unchanged refreshes
  or already dismissed offers; agree what material improvement permits re-alerting.
- [ ] Implement the agreed digest/instant policy. If an external channel is chosen,
  configure only that channel, keep credentials backend-only, and make its content
  useful without exposing private definition details. Support disable/pause.
- [ ] Persist pending/sent/failed delivery and bounded retry. Enforce provider limits
  and handle ambiguous delivery responses without claiming exactly-once transport.

### Tests and test maintenance

- [ ] Add eligibility/event tests at meaningful threshold boundaries and integration
  tests for deduplication, ambiguous delivery, retries and opt-out with a fake notifier.
- [ ] Add an inbox read/dismiss browser journey with chat preservation; reuse shared
  navigation/language tests and keep real-channel delivery outside routine runs.

### Validation checklist

- [ ] Test score/coverage threshold boundaries, missing salary, unknown constraints,
  stale scores and closed/ineligible offers; only qualifying matches generate alerts.
- [ ] Repeat imports/runs/refreshes and dismiss offers; event identity prevents
  duplicate alerts and re-alerting follows the agreed material-improvement policy.
- [ ] Verify inbox persistence and read/dismiss state, digest/instant timing,
  disable/pause and channel opt-out through API and bilingual browser tests.
- [ ] Inject delivery failure, rate limiting and ambiguous responses using a fake
  notifier; pending/sent/failed state and bounded retries remain accurate.
- [ ] During feature validation, verify the agreed channel with a bounded
  owner-directed delivery test; configuration alone does not establish delivery.
  External-channel checks apply only when that channel is selected and authorized.
- [ ] Check notification content exposes no private definition details and chat
  remains functional on inbox/detail views, using saved offer evidence.

## Part 11: Learn from explicit offer feedback

Dependency: Parts 7–8; notification integration follows Part 10.
Deliverable: saved feedback and a transparent, reversible ranking adjustment.

- [ ] Save interested/not interested and optional reasons such as role, compensation,
  company or work arrangement; allow editing/removing feedback. Separate explicit
  preferences from temporary reasons such as a closed or duplicate vacancy.
- [ ] Implement small deterministic bounded adjustments from agreed feedback reasons
  as a baseline. Store the applied policy/weights so the same inputs reproduce
  ordering; no fine-tuning or opaque recommender service is required.
- [ ] Show base fit and personalized ordering separately with explanations. Honor
  hard constraints and missing evidence; one dismissal cannot invent a permanent
  exclusion or automatically promote an uncertain match to a notification.
- [ ] Support correction/reset and explicit reranking in future runs. A suggested
  lasting preference change goes through the existing review/save flow. Invalidate
  affected derived ranking/alerts without sending duplicate notifications.

### Tests and test maintenance

- [ ] Extend the labeled ranking fixtures with before/after feedback, unrelated
  reasons, contradictory feedback and reset; assert explainable later ordering
  while hard constraints and accepted criteria remain unchanged.
- [ ] Add persistence tests for feedback edits/removal and browser tests for
  visible base/personalized results; reuse notification tests for changed eligibility.

### Validation checklist

- [ ] Save, reload, edit and remove feedback with/without reasons; offer identity
  and feedback provenance remain intact in English and Spanish.
- [ ] Compare before/after fixtures: relevant feedback changes later offer ordering
  predictably, while unrelated/temporary reasons do not create lasting preferences.
- [ ] Reproduce ordering from stored policy/weights; adjustments stay bounded,
  contradictory/sparse feedback is handled and reset restores baseline behavior.
- [ ] Verify personalization never overrides hard constraints, hides missing
  evidence, silently edits saved criteria or promotes uncertain offers into alerts.
- [ ] Exercise reranking and notification integration after feedback changes;
  derived results invalidate correctly without duplicate alerts.
- [ ] Verify chat explains feedback effects from saved data and any lasting
  preference proposal still requires review and explicit saving.

## Part 12: Extend the shared assistant to job finding

Dependency: Parts 5, 7–8 and 11.
Deliverable: contextual assistance through the existing floating chatbot.

The shared chat is already available from Part 5. This part completes and checks
the integration across all delivered job-finding capabilities.

- [ ] Let chat explain an offer's evidence, score, uncertainty and feedback effects
  using saved permitted context and stable offer IDs; avoid invented vacancies.
- [ ] Support proposing a search/manual offer or definition refinement. Require an
  explicit action before a new run or opted-in schedule; review/save preference
  changes through the current editor. Ordinary chat must not enable automation.
- [ ] Keep job-finding context separate from role-clarification state. Respect
  stopped clarification while allowing independent authorized search/read actions;
  definition proposals remain subject to existing controls.
- [ ] Preserve existing conversation/source-deletion rules and composer behavior.
  Specify retention of offer references in chat when an offer is deleted. Extend
  existing backend logic with small explicit actions rather than a second agent stack.

### Tests and test maintenance

- [ ] Extend existing assistant API tests with grounded offer explanations, deleted/
  stale references and proposed actions; assert saved state changes only after the
  required explicit action/review/save, using fake AI replies rather than exact wording.
- [ ] Maintain one shared cross-feature browser journey for conversation/composer
  preservation and paused clarification, adding new contextual interactions without
  duplicating the navigation tests created in Part 5.

### Validation checklist

- [ ] Ask chat to explain a saved offer's score, evidence, unknowns and feedback
  effects; answers match persisted data and cite the correct offer context.
- [ ] Exercise search/manual-offer proposals and definition refinement through
  chat; starting/configuring a run needs an explicit action and preference changes
  remain unapplied until reviewed and saved.
- [ ] Navigate every delivered job-finding view and job-definition step in both
  languages on desktop/mobile; conversation, composer and pending forms survive
  minimizing, dialogs, active runs and error states.
- [ ] Pause clarification and verify independent authorized search/read actions
  remain usable while definition proposals respect existing clarification controls.
- [ ] Delete referenced sources/offers and verify agreed context-retention rules;
  chat does not reuse deleted content or apply stale proposals.
- [ ] Reject unsupported actions, prompt injection and invalid/stale offer IDs
  without mutating saved data; run existing assistant regressions.

## Part 13: Validate the complete feature locally

Dependency: Parts 1–12 implemented within the agreed source/channel scope.
Deliverable: reproducible validation report and sanitized evidence in this feature.

- [ ] Run relevant unit/PostgreSQL integration, frontend lint/type/build/contract
  and desktop/mobile browser tests, including all job-definition regressions.
  Inspect coverage for missed business behavior; no percentage determines acceptance.
- [ ] Exercise definition → manual/discovered offer → extraction → explained score
  → feedback → rerun → notification, including bilingual content, unknown values,
  stale templates, session expiry, source outages and interrupted work.
- [ ] Evaluate new extraction/comparison tasks on a synthetic labeled corpus and
  record ranking quality, unsupported claims, latency, tokens and cost. Routine
  tests use fakes; execute paid live checks only within the agreed bounded budget.
- [ ] Build the combined image and operations runner; verify migrations, restart/
  replacement, real batch resumption and SQL/original backup/restore for new data.
  Measure memory/CPU/database/transfer and worst-case run budgets on local fixtures.

### Tests and test maintenance

- [ ] Run and maintain the tests built in Parts 2–12; add only missing cross-feature
  scenarios exposed by integration, preserving deterministic routine runs and
  separately labeled live evaluations.
- [ ] Review failures, flaky/redundant cases and coverage gaps for actual product
  risk. Fix causes and add regressions for demonstrated bugs; do not manufacture
  tests or duplicate assertions to reach a coverage number.

### Validation checklist

- [ ] Record passing relevant backend unit/PostgreSQL integration, frontend
  lint/type/build/contract and desktop/mobile browser checks, including existing
  job-definition and floating-chat regressions.
- [ ] Complete the agreed definition → intake/discovery → extraction → score →
  feedback → rerun → notification journeys in both languages, including unknowns,
  stale context, expired sessions, provider outages and interrupted work.
- [ ] Record bounded live source/model/channel evidence separately from mocks,
  with synthetic labeled-corpus quality, unsupported claims, latency, tokens and cost;
  simulated search or delivery alone cannot complete the feature.
- [ ] Verify the combined image and operations runner support repeatable migrations,
  restart/replacement, persisted batch resumption and restore of all new data/files.
- [ ] Compare resource/usage measurements and worst-case budgets with agreed limits;
  verify original user data, credentials and private source contents remain protected.
- [ ] Record remaining issues and evidence in feature validation notes; complete
  required local checks before proceeding to cloud release.

## Part 14: Release and verify operations

Dependency: Part 13 passes; source access, channel, costs and deployment are settled.
Deliverable: tested feature rollout, updated runbooks and observed operational checks.

- [ ] Review existing [operational follow-ups](../../operations/FOLLOW_UPS.md),
  particularly the **2 December 2026, 17:45 Madrid** database expiry. Agree resource
  continuation if the feature will outlive the preview; no automatic paid upgrade.
- [ ] Create/verify a backup, rehearse migration on an isolated restored copy, and
  prepare rollback compatible with the new schema before updating the live app.
  Preserve definition, sources, conversation, credentials and original files.
- [ ] Configure selected source/runner/notifier secrets and roll out tested images.
  Keep recurring search disabled until its opt-in and limits are confirmed. Verify
  hosted authentication, bilingual UI, manual entry, live discovery and recovery.
- [ ] Observe actual recurring search and notification delivery, plus backup/restore
  including all new tables and offer attachments. Meter total account usage and
  update API/persistence docs, operations runbook, README and the project roadmap.

### Tests and test maintenance

- [ ] Extend existing release/recovery checks to include new offer/run/feedback/
  notification data and attachments; verify restored business state and compatible
  rollback rather than hard-coding provider resource IDs or snapshot timestamps.
- [ ] Maintain a bounded reproducible hosted smoke journey for private access,
  real discovery and chat continuity. Record actual scheduler/delivery observations
  separately from automated tests and preserve live user data during checks.

### Validation checklist

- [ ] Record the deployed revision/schema, selected source route, configured channel
  and runner settings; secrets stay backend-only and recurring search respects opt-in.
- [ ] Verify hosted authentication, bilingual manual intake, real discovery/scoring,
  notifications and feedback, with functional persistent chat throughout the feature.
- [ ] Observe a real schedule-triggered search and agreed-channel delivery; record
  traceable run/delivery evidence separately from manual dispatches and mocks.
- [ ] Restore a current SQL/original backup into isolated resources and verify all
  new tables/attachments plus existing definition, conversation, sources and credentials.
  Rehearse schema-compatible rollback/recovery without changing the live workspace.
- [ ] Record account-wide usage against allowances, backup scheduling status and
  the database-expiration/continuation decision; retain unresolved checks in the
  operational tracker without implying a paid upgrade is authorized.
- [ ] Confirm README, API/persistence contracts, runbooks and roadmap match the
  deployed feature; present the result for review with verified behavior and any
  accepted provider restrictions/operational limitations clearly distinguished.

## Dependencies and completion rules

Execution order is 1 → 2, then 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14.
Parts 3–7 may proceed after Part 1 while Part 2 access is unresolved; Part 8
requires a proven source. Part 11 can proceed after Part 8 while delivery work is
under way, but its notification effects need Part 10 before integration validation.
Every part should remain independently reviewable and end with its stated checks.
Behavior-changing parts include maintained tests when delivered; Part 13 does not
substitute for them. Coverage percentages do not determine part completion.

- [ ] All six requirement #2 capabilities have agreed, executed acceptance evidence.
- [ ] Each implemented part includes relevant maintained tests for its business
  behavior and meaningful failure/regression risks; planning-only parts have
  reviewed acceptance scenarios/evidence, with no coverage-driven filler tests.
- [ ] LinkedIn-first discovery is proven or the user explicitly accepts a documented
  source/scope change. No capability is inferred from login or manual import.
- [ ] The same functional floating chat is available throughout every job-finding
  view/state from the first UI delivery. Conversation, typed input and pending
  edits survive navigation/minimizing/language changes; relevant delivered
  capabilities work through chat with explicit action/review/save boundaries.
- [ ] Job definition, explicit saving, bilingual content and shared chat regressions pass.
- [ ] Runs, notifications and learning are bounded, explainable and recoverable;
  missing facts, stale results and provider failures are visible.
- [ ] New data survives replacement and verified backup/restore; deletion/retention
  and credentials follow the shared operational policy.
- [ ] Local and hosted evidence, costs, operating commands and limitations are
  recorded without private document contents or credentials.
