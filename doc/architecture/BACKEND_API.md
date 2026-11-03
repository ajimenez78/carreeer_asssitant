# Job-definition backend

Implemented API baseline. The [job-finding plan](../features/job-finding/PLAN.md)
proposes additional contracts; discovery APIs are not implemented yet. Extend
this document as those endpoints are delivered.

Part 7 implements the private API for one owner and one current definition.
The generated request/response schemas are at `/openapi.json` and `/docs`.
Part 9 connects the bilingual frontend to this API and serves its static export from the same Python service. Mocks are an explicit development/test option; Part 10 adds persistent refinement chat.
The subsequent clarity/summary extension adds system readiness, a persisted
assessment, and independent clarification stop/resume control. Its validation
record is [CLARITY_SUMMARY.md](../features/job-definition/CLARITY_SUMMARY.md).

## Access and initialization

Run `make db-init` explicitly before using private routes. It creates only a local
database, migrates it, and reserves the owner without enabling login. Repeating
initialization preserves data and credentials. Hosted migrations remain a
separate release command; web startup performs no migrations or provider calls.

Migration `0004` adds the assessment and clarification-control fields. Existing
manual readiness is reset to unassessed `draft`; accepted preferences, sources,
answers, and owner credentials are retained. New assessments determine readiness
under the system-controlled workflow.

Run `make owner` to configure a password interactively, then configure a stable
`CAREER_SESSION_SECRET` of at least 32 random characters in the ignored `.env`.
Passwords use pwdlib's recommended Argon2 settings. There is no registration or
HTTP password-reset endpoint. Reconfiguration through the CLI revokes all sessions.

`POST /api/session` accepts `{"username":"owner","password":"..."}`. It sets
a signed HttpOnly, SameSite=Strict cookie referencing a revocable database session.
Sessions expire after twelve hours. `GET /api/session` checks the session;
`DELETE /api/session` revokes it. Five failed attempts lock login for fifteen
minutes, with counters persisted across restarts. Cookie contents contain no
passwords, documents, or job preferences.

Every write, including login and multipart uploads, requires an `Origin` header
matching `CAREER_ALLOWED_ORIGINS` exactly. Requests without it are rejected.
This applies to curl and other API clients too. Configure only trusted origins;
use HTTPS origins and `CAREER_SESSION_SECURE=true` for hosted operation. Credentialed CORS allows only the configured exact origins and supported methods/headers, including preflights and API errors. Private responses disable caching; originals
are attachment downloads. `/api/health` remains a public liveness check.

## Saved definitions and proposals

`PUT /api/job-definition` explicitly creates or replaces the accepted description
and complete preference list. A description of 1–20,000 characters is enough
to save an incomplete draft. Example:

```json
{
  "description": "Staff scope, architecture and cross-team work. Good compensation.",
  "state": "draft",
  "preferences": [
    {"key":"seniority","category":"seniority","priority":"mandatory","value":"Staff","note":null},
    {"key":"remote","category":"work_arrangement","priority":"preferred","value":true,"note":null},
    {"key":"hybrid_location","category":"location","priority":"mandatory","value":"Madrid or nearby","note":"If hybrid"},
    {"key":"onsite_limit","category":"work_arrangement","priority":"mandatory","value":{"days":2,"period":null},"note":"If hybrid"},
    {"key":"salary","category":"compensation","priority":"preferred","value":null,"note":null}
  ]
}
```

The request's `state` remains accepted for compatibility but does not set
readiness. The system sets `ready` only after a sufficient-clarity assessment;
changed saved criteria clear the assessment and return to `draft`. An unchanged
save preserves the current assessment/readiness. `GET /api/job-definition`
returns the stable UUID, timestamps, accepted preferences, source metadata,
clarification questions/answers, `assessment` (or null), and
`clarification_paused`. No current definition returns 404. Omitted
preferences in an explicit save are removed; source and answer records are
independent of this action. There is no revision history.

Preference keys must be unique (up to 100). Categories are `role`, `seniority`,
`responsibilities`, `technical_interests`, `company_context`, `compensation`,
`location`, `work_arrangement`, and `work_life_balance`. Priorities are
`mandatory`, `preferred`, or `excluded`. Values may be text, numbers, booleans,
text lists, or null. Structured compensation uses all six nullable members
`minimum`, `maximum`, `target`, `currency` (three uppercase letters), `period`
(`hour/day/week/month/year`), and `basis` (`gross/net`). Ranges cannot be negative
or reversed. Structured on-site limits use `days` and `period`
(`week/month/year` or null). Each serialized value is limited to 4,000 characters.
Keep unknown values null instead of inventing amounts or periods.

`POST /api/job-definition/clarifications` accepts
`{"language":"English"}` or `{"language":"Spanish"}` (English by default).
It reads the saved description, accepted preferences, reviewed source facts and
previous answer states. It returns:

- `proposal.preferences`: the complete editable proposed preference set, merging
  AI changes with accepted criteria so omitted accepted values are preserved;
- `proposal.conflicts`: explanations/requests to review changes to accepted values;
- `clarifications`: at most three newly persisted questions, with UUIDs and round;
- `assessment`: persisted natural-language `summary`, boolean `sufficient`,
  `explanation`, and `gaps`, plus `language`, `assessed_at`, and `context` metadata;
- `state`: `ready` when sufficiently clear, otherwise `draft`;
- `proposal_context`: a context fingerprint, and `usage`: tokens/model/cost estimate.

The model's strict proposal includes `assessment` with a 1–4,000 character summary,
1–2,000 character explanation, and at most nine gaps. The saved summary describes
the current accepted definition; proposed preferences are not accepted facts.
Assess meaningful clarity rather than field completion: optional unknowns and
skipped questions are allowed. No new questions are added when sufficiently
clear. Assessment and summary share this existing explicit AI call; loading and
saving do not call AI. Generated prose retains its requested language when the
interface language changes.

Preferences are not applied by this call. After review, send the edited complete
preference set through `PUT`, including `proposal_context` when applying the AI
proposal. A changed context returns 409 instead of applying stale suggestions.
An in-flight AI result is also rejected if its context changes. Ordinary manual
saves need no fingerprint. Failed AI calls and failed save transactions preserve
the previous definition and accepted preferences.

`PATCH /api/job-definition/clarification-control` accepts `{"paused":true}` to
stop or `{"paused":false}` to resume, returning the full current definition.
Pause persists independently of `state`; it neither marks ready nor removes
accepted preferences, questions, or an otherwise-current assessment. New
clarification calls are rejected while paused. Control changes invalidate
in-flight AI context, including stop followed immediately by resume, so a late
response cannot apply. The frontend keeps stop available during requests and
discards aborted results. Resume alone makes no AI call.

`PATCH /api/job-definition/clarifications/{question_id}` persists one answer:

```json
{"state":"answered","answer":"EUR 100,000–120,000 gross per year"}
```

Alternatively send `{"state":"skipped"}` or `{"state":"unknown"}`. Only an
answered question accepts text. Answers persist independently of definition saves
and do not apply preferences automatically. Changed answer state/text clears the
assessment and returns the definition to `draft`; request another assessment
when ready.

## Sources, correction, and processing limits

Save a definition before adding sources. `POST /api/job-definition/sources`
accepts one multipart `file` or a JSON source:

```json
{"kind":"text","display_name":"Pasted profile","text":"Historical experience…"}
```

```json
{"kind":"url","display_name":"Public profile","url":"https://example.com/profile"}
```

Files support text-based PDF, binary Word `.doc`, `.docx`, `.md` and `.markdown`.
The extension selects the parser; supplied MIME headers are not trusted. Filenames
are metadata, never storage paths. Each definition can retain five files, each
up to 10 MiB. Validation rejects unsupported, empty or oversized files before
reserving a source. A reserved source/key is committed before writing its original;
original writes coordinate with deletion through the definition lock.

Uploads/extraction never call AI automatically. A created source returns 201 with
`extraction_state` (`pending/ready/failed`), `extraction_error`, `original_stored`,
`reviewed_at`, provenance, extracted text and reviewed facts. A durable original
with unusable text returns a created **failed** source and recovery message,
not an extracted success. Storage failures return 503 with `error.fields.source_id`;
the reserved key remains visible for recovery or deletion. Interrupted processing
may leave a pending source, which can be retried or removed.

`GET /sources/{id}` reads authenticated extracted text and facts.
`GET /sources/{id}/original` downloads an authenticated stored file.
`POST /sources/{id}/retry` re-reads the stored original or retrieves the URL again.
If no original bytes were stored, remove the failed source and upload it again.
Retried extraction invalidates previous review, source facts, derived questions,
and the clarity assessment/summary.

`POST /sources/{id}/facts` with an optional language requests AI background-fact
proposals from that source's raw extracted text. Each proposed fact must include
an exact evidence quote found in the source. These proposals are not saved or
sent to job clarification until the owner reviews them.
`PATCH /sources/{id}` with `{"facts":["Corrected historical fact", "…"]}`
explicitly replaces and accepts the source's facts (up to 100, 2,000 characters
each). An empty list accepts no facts. Provenance stays attached to the source.
Reviewing or correcting facts clears derived clarification context and the
clarity assessment/summary, returning the definition to `draft`. Historical
facts remain separate from desired job criteria. Conflicting source facts can be
compared/corrected before review; they are never automatically reconciled as truth.

Processing bounds:

| Boundary | Limit |
| --- | --- |
| JSON bodies / multipart bodies | 256 KiB / 10 MiB + 64 KiB overhead, including chunked requests |
| Retained extracted source text | 60,000 characters; excessive text is rejected, never truncated |
| Parser/fetcher process | One at a time; 256 MiB address space, 8 CPU seconds, 15 seconds wall time |
| PDF | 200 pages; encrypted PDFs rejected; scanned/image-only PDFs require a text alternative; no OCR |
| DOCX | 2,000 ZIP entries; 20 MiB total expanded size; document paragraphs/table cells |
| Legacy DOC | Debian `catdoc`, UTF-8 output; subprocess inherits resource limits |
| Public URLs | HTTP(S), standard ports, no credentials; 2 MiB text/HTML; up to three redirects; five-second socket timeout within overall worker deadline |
| AI | Exact token preflight, maximum 20,000 input / 2,000 output tokens; 60-second total budget; no automatic retries |

URL retrieval validates **all** resolved addresses and rejects internal, private,
loopback, link-local, multicast, reserved and IPv6 transition destinations.
It pins the socket to a checked IP while retaining the original HTTP Host and
TLS hostname/certificate check, and repeats validation after redirects. No proxy
environment, cookies, credentials, browser scripts, page subresources, or
authenticated LinkedIn scraping are used. Restricted pages and unsupported
responses retain provenance and offer upload/paste fallback.

The extraction worker receives no database, storage or OpenAI credentials.
Source commands are treated as data in both fact and clarification prompts.
Only explicit AI requests transmit the necessary source/reviewed text to OpenAI.
Strict structured output and local domain/evidence validation reject invalid
results. These checks reduce errors; user review remains required for factual
correctness. See [official structured-output guidance](https://developers.openai.com/api/docs/guides/structured-outputs).

## Deletion and errors

Before deleting a source, the UI must explain that `DELETE /sources/{id}` removes
its live text/facts and clears all derived clarification/answer context. Accepted
job preferences remain independent; the assessment/summary is invalidated and
readiness returns to `draft`. `DELETE /api/job-definition` deletes the
definition, all sources/facts/preferences/answers, and queues its originals;
the configured owner and login remain. Conversation records are also removed
on source-context invalidation or complete-definition deletion.

Metadata deletion and the original-deletion queue commit together. The API then
attempts original cleanup and returns `cleanup_pending` and `pending_originals`.
Storage failure cannot restore deleted text to future AI context. Retry using
`POST /api/job-definition/cleanup` or `make storage-cleanup`, including after the
whole definition is gone. Daily scheduled retry/backup operations remain Part 11.
Backup copies expire under the agreed seven-day retention policy.

Errors use `{"error":{"code":"...","message":"...","fields":{}}}`. Statuses
include 401 (sign-in required), 403 (origin), 404 (absent record), 409 (state/stale
proposal/conflict), 413 (size), 415 (format), 422 (validation), 429 (login throttle),
502/503 (AI/availability), and 504 (timeout). Validation diagnostics contain field
paths/types, not rejected passwords or personal source text. No provider response,
SQL parameters, or credentials are exposed in errors. Source extraction failures
are also retained in the source's safe `extraction_error` for reload and recovery.

## Part 10 chat

Migration `0005` adds `chat_turns`, attached to the current definition with cascading
deletion. No existing rows are rewritten. All routes below require the owner
session and the existing origin controls; responses are private/no-store.

- `GET /api/job-definition/chat` returns `{turns, context}`. Each turn includes
  `id`, `message`, `language`, `created_at`, `reply`, `in_scope`, `questions`,
  `proposal: {preferences, conflicts}`, `has_changes`, `proposal_context`, and `usage`.
  `context` is the current SHA-256 saved-context token, for distinguishing historical
  proposals. Loading history does not call AI.
- `POST /api/job-definition/chat` takes `{request_id: UUID, message, language}`;
  trimmed message length is 1–4,000 characters, language is English or Spanish.
  It returns the persisted turn. The same UUID/message/language replays the saved
  response without another model generation; reusing a UUID for different input
  returns `409 chat_request_conflict`. Overlapping retries can both generate, but
  commit only one turn; this does not promise provider-level exactly-once billing.
- Review chat proposals through the existing `PUT /api/job-definition`, sending
  `description`, the complete reviewed `preferences`, and `proposal_context`.
  Omitted accepted criteria are merged back before the proposal reaches the UI.
  No chat call writes accepted preferences. Removing a criterion remains an
  explicit operation in the shared editor.

Both structured clarification and chat reuse preference instructions, the model
client, local domain validation, and proposal merging. The retained conversation
is included in AI context with earlier changes labelled as unaccepted proposals.
Only reviewed background is included. In-scope chat invalidates the old clarity
assessment; readiness is reassessed only through the explicit clarification call.
Unrelated requests return a scope explanation and cannot carry preference changes.

Messages and validated replies commit atomically after generation; a failed or
obsolete call commits neither and preserves accepted data. A persisted stop,
rapid stop/resume, concurrent message, structured edit, or source-context change
invalidates in-flight context. Paused chat returns `409 clarification_paused`;
obsolete results and saves return `409 stale_proposal`. Source extraction/review/
deletion clears conversation and derived clarifications, preventing removed source
snippets from returning through history. Accepted preferences remain independent.
Complete-definition deletion cascades chat records. Backups expire under Part 11's
seven-day policy. History is retained without silent truncation; existing provider
input/output/timeout caps apply and oversized context remains a recoverable error.
