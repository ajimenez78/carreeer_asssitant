# Job finding: Part 1 specification

Date: **2026-11-03**. Business requirement: **#2**.
Status: **Part 1 requirements baseline approved by the user on 2026-11-03;
application implementation has not started**.
The user requested execution of Part 1 and selected the notification channel,
search cadence and source-fallback policy below. Initial product limits are
reversible specification defaults, not permission to spend or provision services.
Source access, provider selection and measured costs belong to Part 2.

Related documents: [execution plan](PLAN.md),
[acceptance scenarios](ACCEPTANCE_SCENARIOS.md),
[Part 1 review record](validation/PART1_VALIDATION.md), and
[implemented job-definition baseline](../job-definition/MVP_SPEC.md).

## Decisions and scope

| ID | Decision | Basis/status |
| --- | --- | --- |
| D01 | One private owner, one current editable role definition; explicit review/save and no definition revision-history feature | Existing approved baseline |
| D02 | English/Spanish UI and content, persistent language switcher, functional shared floating chat throughout job finding from its first UI delivery | Existing baseline and explicit follow-up requests |
| D03 | Active discovery uses the saved accepted role definition; manual offers/proposals and explainable matching remain available independently of provider access | Requirement #2 and implementation plan |
| D04 | LinkedIn is the primary initial discovery source. Decide any fallback only after Part 2 evidence | User selected on 2026-11-03; no alternative source selected yet |
| D05 | Daily recurring search at **09:00 Europe/Madrid**, disabled until explicitly enabled | User selected on 2026-11-03; timezone follows Madrid daylight-saving changes |
| D06 | In-app notification inbox **plus a daily email digest** | User selected on 2026-11-03; email provider/destination and delivery access remain Part 2 work |
| D07 | Explainable base fit, separate hard-constraint eligibility and evidence coverage; unknowns stay unknown | Requirement #2; initial scoring defaults below, calibration in Part 7 |
| D08 | Explicit interested/not-interested feedback with bounded, visible, reversible personalization; saved preferences change only through review/save | Requirement #2 and existing saving rules |
| D09 | Keep Render/Next.js/FastAPI/PostgreSQL/private R2/direct backend OpenAI; validate locally before cloud release | Existing approved technical decisions |
| D10 | Start with the bounded intake/search/usage/retention defaults below; controls are enforced across retries | Initial Part 1 defaults, adjustable with measured evidence |
| D11 | No new paid source, email, hosting or backup subscription is selected or authorized. Recurring paid inference requires an explicitly saved budget and opt-in | Existing cost boundary; provider prices/access must be verified in Part 2 |
| D12 | Each implemented part builds and maintains meaningful behavior/regression tests. Planning-only work uses reviewed acceptance examples and evidence | Explicit user instruction; no coverage percentage gate |

This feature includes active discovery, manual intake, matching, notifications,
feedback and contextual chat. Skill-development plans, applications/interviews,
recruiter outreach and post-hire support remain later features. Manual import or
a search link alone does not complete active discovery. Email is part of the
selected notification scope; an inbox-only release would require a scope decision.

## Owner flow and navigation

| Action | English / Spanish surface | Required result |
| --- | --- | --- |
| Revisit the template | Job definition / Definir empleo | Existing saved definition remains editable; pending changes stay unsaved |
| Browse vacancies | Job finding / Buscar empleo | Offer list/detail, evidence, availability and score status |
| Add a vacancy/proposal | Add offer / Añadir oferta | Paste text, enter a URL or upload a supported document; explicitly save |
| Search now | Search now / Buscar ahora | Show effective saved template/source; start one bounded discovery run |
| Inspect a match | Match details / Detalles de compatibilidad | Explain score, hard constraints, missing facts and source references |
| Give feedback | Interested / Me interesa; Not interested / No me interesa | Save feedback as an explicit action; explain resulting personalization |
| Review alerts | Notifications / Notificaciones | Persistent inbox, unread/read/dismiss state and daily digest settings |
| Configure recurrence | Search settings / Configuración de búsqueda | Explicit enable/pause, daily 09:00 Madrid schedule and budgets |

Keep the existing chat launcher available beside every view and its empty,
loading/error states, including during searches and alongside dialogs. Navigating,
minimizing or switching language preserves conversation, unsent chat text and
pending definition/intake edits. Existing generated content retains its language.
The shared assistant is never a numbered workflow step.

## Saved template and search eligibility

A usable template has a saved, affirmative role/title/technical-domain term in
the accepted description or criteria, sufficient to construct at least one query.
Salary, location, company type and optional benefits may remain unknown. An
exclusion by itself, such as “not frontend,” is not a usable positive query.

A sufficiently clear saved definition can start a normal search. If an otherwise
usable definition is unassessed/incomplete, show the gaps and effective query and
let the owner explicitly choose a **provisional search**. This does not mark the
definition ready, resume clarification or fill optional unknowns. Recurring search
requires explicit acceptance of that provisional template before opt-in. If there
is no usable positive term, explain the missing search context and offer editing
or chat; manual intake remains available.

Unsaved editor text and unaccepted chat suggestions never become search criteria.
Use reviewed background only when necessary for an explained comparison; CV skills
do not become desired responsibilities. Do not send the CV, chat transcript or
compensation details to a search provider merely to construct public queries.

Every run records its effective query summary and a saved-context fingerprint.
Definition/context changes make existing matches stale and prevent late results
from becoming current. New runs use the latest accepted usable context. Store
the context needed to explain the current comparison, without adding definition
revision history. Clarification pause is independent of search and job-finding chat.

## Manual intake, sources and offer lifecycle

An offer is a vacancy or recruiter proposal with retained text and provenance,
plus known title/company, URL/source identity, source/check timestamps, language
and availability (`active`, `closed`, `unknown`). Missing fields remain unknown.
A URL can be saved as a reference when retrieval fails; it cannot receive an
evidence-based score until sufficient listing text is supplied.

Manual text/file/URL submission, editing and deletion are explicit owner actions.
Use existing public-URL network/redirect protections and document parsers. Support
text-based PDF, legacy `.doc`, `.docx` and Markdown; scanned-document OCR remains
deferred. Restricted pages offer paste/upload fallback. An ordinary LinkedIn login
does not establish vacancy-search access; Part 2 must prove the supported route.

Known source IDs/canonical URLs identify duplicates. Tracking-only URL differences
do not create new vacancies. Similar company/title/location without reliable
identity produces a reviewable possible duplicate, preserving separate records.
Reimports and refreshed extraction preserve manual corrections and surface conflicts.

Discovered offers are automatically retained as source-linked candidates within
the agreed run limits. Their extracted facts are labeled derived and correctable;
they do not require manual review before every tentative match can be calculated.
Notification eligibility still requires sufficient evidence and resolved hard
constraints. Failed processing preserves the source and visible retry status.

The owner can delete an offer, its feedback and derived match/notifications.
Whole-definition deletion removes its associated discovery records and stops runs.
Queue original-file cleanup durably. Remove deleted source/offer content from
future assistant context; clear retained conversation context where required by
the existing source-deletion policy. Source-derived hard constraints are not
silently copied into accepted preferences.

## Matching and uncertainty

Compare accepted criteria against evidence as **met**, **partial**, **not met**
or **unknown**, with source references. Mark conditional criteria **not applicable**
when their condition is false. For example, hybrid city/attendance limits do not
apply to a role explicitly remote from Spain. “Remote” without country eligibility
does not establish permission to work from Spain.

Initial scoring default: equal weights across applicable, known positive criteria;
met = 1, partial = 0.5, not met = 0. Base fit is
`100 × sum(weight × match) / sum(known applicable weights)`. Separately show known
weight divided by all applicable positive-criterion weight as evidence coverage.
No known criteria means **unscored**, not zero or a perfect match. Unknown ideal
preferences are omitted rather than invented. Confirm the partial-match rules
and calibrate weights in Part 7 using independently labeled examples.
Partly specified mandatory constraints remain unresolved checks; omission from
numeric scoring never means the constraint is satisfied.

A proven mandatory violation or matched exclusion makes the offer **ineligible**
regardless of fit. An unresolved applicable hard constraint means **needs review**.
Mandatory uncertainty cannot be averaged away. A two-day hybrid limit with no
known period stays unresolved for hybrid offers; never assume “per week.”
Compensation requires compatible currency, period and gross/net basis; the first
version does not invent exchange rates or convert incomparable salaries.
Work–life claims require evidence about hours, on-call/travel or stated benefits.

Show base fit, coverage, eligibility, missing facts, last check and stale/current
state separately. Scores describe preference fit, not hiring probability. Recompute
only explicitly or within an opted-in run, never on opening a page or ordinary
save. Extend the existing AI client with bounded structured output and validate
every claimed field against source text. Listing instructions are untrusted data.

## Discovery, cadence and notifications

On-demand discovery builds bounded queries from the saved template, retrieves
real source-linked offers and reuses deduplication, extraction and matching.
Persist progress and separate completed/partial/failed/canceled runs from zero
matches. Cancellation, repeated triggers, sleep/restart and retries cannot create
overlapping runs or reset consumed budgets. No browser must stay open for recurrence.

Recurring discovery is off until the owner explicitly enables it with source,
template, schedule and budgets visible. The selected local start time is 09:00
Europe/Madrid daily. Provider/scheduler delivery is best effort and measured;
missed/late runs are visible, not silently represented as successful searches.
Part 2 chooses the supported runner and authentication approach. Revoked access,
deleted/unusable templates or exhausted budgets stop further external work.

Initial “interesting” rule: current base fit **at least 75**, evidence coverage
**at least 75%**, all applicable hard constraints resolved and satisfied, no
exclusion/dismissal, and active availability checked within the last **24 hours**.
Thresholds are initial product defaults to calibrate in Part 7. Personalization
orders otherwise eligible matches; it cannot bypass eligibility or base thresholds.

Persist qualifying events in the inbox, including read/dismiss state. A daily
email digest contains up to **10** highest-ranked new qualifying offers, linking
back to the private workspace. It contains no CV excerpts, salary preferences or
chat transcript. No qualifying new offers means no empty digest. Duplicate imports,
unchanged refreshes and repeated runs do not create a second alert. The first
version does not re-alert the same offer automatically after dismissal/read.
Offers omitted from a full digest remain pending for a later digest while still
eligible; only included offers are marked delivered by email.

Assemble the digest after that day's search completes; if recurring search is
disabled but email is enabled, a daily 09:00 tick considers saved matches only.
New matches after that day's digest wait for the next digest. Delivery failures
retain pending/failed state and bounded retries; ambiguous transport outcomes are
not claimed to provide exactly-once delivery. Turning off search and turning off
email are independent controls; existing inbox records remain readable.

Part 2 must select a suitable email provider and prove the sending capability,
destination verification, costs/quotas and failure handling. The owner supplies
and verifies the destination during setup; no address or provider is assumed.
Daily email remains disabled until that setup and explicit opt-in are complete.
Selecting the channel here does not authorize messages from this Part 1 task.

## Feedback and assistant behavior

Interested/not-interested feedback can include role/scope, company, compensation,
work arrangement or work–life reasons. Closed/duplicate/temporary reasons do not
become enduring preferences. Feedback can be edited, removed or reset.

Start with small deterministic bounded adjustments to ordering, showing base fit
and the personalization reason separately. Feedback cannot rewrite the definition,
invent an exclusion or promote missing evidence into a satisfied hard constraint.
Part 11 calibrates adjustment magnitudes on before/after fixtures. Any suggested
permanent preference change uses the existing review/save flow.

As each capability ships, chat can prepare a manual offer/search, explain saved
matches and missing details, review interesting offers and propose feedback.
Chat proposals need explicit save/submit/start actions before modifying records
or executing a run. Chat cannot enable a schedule or silently apply a preference.
Stopped role clarification still permits independent authorized job-finding read/
search assistance. Pending definition edits remain separate from saved context.

## Initial operating limits and retention

These limits define a bounded first implementation. They can be adjusted with
measured evidence; they are not statements about provider allowances or pricing.

| Area | Initial specification default |
| --- | --- |
| Stored offers | 500 retained offers per workspace; at capacity show a clear limit and pause new intake, with no automatic deletion of retained offers |
| Listing text | Reuse the existing 60,000 extracted-character limit; reject oversized input with an edit/upload recovery path |
| Offer attachments | Five files total across job-finding offers, at most 10 MiB each; separate from the existing five background-document slots |
| Lists | 20 entries per page, maximum requested page size 100 |
| Discovery | One active run; up to five provider pages and 50 returned candidates total across queries, whichever limit is reached first |
| New/changed processing | At most 20 offers and 40 AI generations per run; reuse unchanged offers/results and expose unprocessed candidates in a partial-run summary |
| Run duration/retries | A 10-minute total execution budget; unfinished work is reported as partial. At most two transient retries per failed external operation within the original run/time/budget limits |
| AI call limits | Preserve existing backend limits of 20,000 input tokens, 2,000 output tokens and 60-second timeout; ordinary saves/page loads make no AI calls |
| Monetary guardrails | Proposed initial job-finding AI caps of US$0.10/run and US$1/month, subject to explicit budget configuration before recurring inference; no new paid subscriptions |
| Budget accounting | Reserve a conservative cost before a billable call, reconcile known usage, retain uncertain usage/reservations after failure, and stop on unknown prices or exhausted limits |
| Offer retention | Retain offers, saved corrections, feedback and source text/attachments until deleted; provider-specific retention capability must be established in Part 2 |
| Operational records | Keep completed run/delivery diagnostics 30 days; unread notifications remain until acted on, read/dismissed records may expire after 30 days; retain the latest current match per offer |
| Backups | Daily SQL/original backups with seven-day retention and verified restore, including all new data; live deletion does not erase already retained backups immediately |

Part 2 must resolve any source limit/retention incompatibility and confirm source,
email, scheduler and account-wide usage before enabling automation. Overall account
monitoring includes the existing MVP workload, not only job-finding totals. If a
source/provider requires a paid resource, present evidence and choices before use.

## Measurable acceptance targets

- Immediate visible loading/error feedback; warm non-AI list/read/save target
  under one second on a 500-offer synthetic workspace, excluding network latency.
- Representative single-offer AI extraction/comparison target under 20 seconds;
  the existing 60-second request timeout preserves input on failure. Measure each
  new task rather than treating the old MVP evaluation as proof.
- Persist bounded-run progress between batches and survive interruption/restart;
  canceled/deleted-context results never become current matches or alerts.
- Scheduled-start target within 60 minutes of 09:00 Madrid and digest assembly
  after the completed/partial daily search. Record actual delivery and lateness;
  Part 2 must prove whether the selected scheduler can meet this target.
- Every eligible alert is traceable to an offer/source, current saved context,
  score/coverage evidence and a stable notification event; no duplicate event
  from repeating a completed run.
- English/Spanish desktop/mobile workflows preserve all pending forms and chat
  input across navigation/minimizing/language changes. Every new private endpoint
  and original download requires authenticated owner access.
- New data survives image replacement and isolated backup/restore. Preserve the
  existing one-day recovery-point/one-working-day recovery targets, subject to
  provider availability; actual scheduled backup delivery remains an operational check.

The Free PostgreSQL preview expires on **2 December 2026 at 17:45 Madrid time**
in the recorded baseline. Continuation, remaining account usage/alerts and automatic
backup observations remain in [operational follow-ups](../../operations/FOLLOW_UPS.md).
Part 1 changes no deployed resources and grants no automatic paid upgrade.

## Requirement traceability and remaining decisions

| Requirement #2 | Specification coverage | Named acceptance scenarios | Delivery parts |
| --- | --- | --- | --- |
| Actively find positions from the ideal-job template | Saved template, discovery, bounded runs | JF-01–04, JF-14–16 | 2, 8–9 |
| LinkedIn first; connect if required | D04, source capability and conditional connection | JF-03, JF-15 | 2, 8 |
| Manually add positions/proposals | Intake, provenance, supported files and duplicates | JF-05–07 | 3–6 |
| Score against the ideal job | Explainable matching, uncertainty and constraints | JF-08–12 | 6–7 |
| Notify about interesting offers | D06, inbox, daily email and delivery state | JF-13, JF-17–18 | 9–10 |
| Learn from feedback | Explicit feedback, bounded ordering and reset | JF-19–20 | 11 |
| Preserve cross-feature product requirements | D01–02/D09/D12, chat, privacy, testing and recovery | JF-21–24 | 3–5, 12–14 |

Part 2 must establish the actual LinkedIn discovery route, necessary connection
scopes, runner choice, email provider/destination setup, current quotas/prices and
whether the operating targets are feasible. An unavailable LinkedIn route needs
the user's fallback decision supported by that evidence. No fallback is presumed.
Part 7 calibrates matching/thresholds; Part 11 calibrates feedback adjustments.
These later decisions do not prevent manual-intake design from proceeding, but
unproven discovery/email/schedules cannot be reported as implemented or verified.
