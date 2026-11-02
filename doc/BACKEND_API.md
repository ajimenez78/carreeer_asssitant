# Job-definition backend

Part 7 implements the private API for one owner and one current definition.
The generated request/response schemas are at `/openapi.json` and `/docs`.
Frontend editing uses mocks in Part 8; real integration remains Part 9 and chat Part 10.

## Access and initialization

Run `make db-init` explicitly before using private routes. It creates only a local
database, migrates it, and reserves the owner without enabling login. Repeating
initialization preserves data and credentials. Hosted migrations remain a
separate release command; web startup performs no migrations or provider calls.

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
use HTTPS origins and `CAREER_SESSION_SECURE=true` for hosted operation. CORS
browser integration is Part 9. Private responses disable caching; originals
are attachment downloads. `/api/health` remains a public liveness check.

## Saved definitions and proposals

`PUT /api/job-definition` explicitly creates or replaces the accepted description,
state, and complete preference list. A description of 1–20,000 characters is enough
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

Use `draft` or `ready`; the owner decides readiness. `GET /api/job-definition`
returns the stable UUID, timestamps, accepted preferences, source metadata and
clarification questions/answers. No current definition returns 404. Omitted
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
- `proposal_context`: a context fingerprint, and `usage`: tokens/model/cost estimate.

Preferences are not applied by this call. After review, send the edited complete
preference set through `PUT`, including `proposal_context` when applying the AI
proposal. A changed context returns 409 instead of applying stale suggestions.
An in-flight AI result is also rejected if its context changes. Ordinary manual
saves need no fingerprint. Failed AI calls and failed save transactions preserve
the previous definition and accepted preferences.

`PATCH /api/job-definition/clarifications/{question_id}` persists one answer:

```json
{"state":"answered","answer":"EUR 100,000–120,000 gross per year"}
```

Alternatively send `{"state":"skipped"}` or `{"state":"unknown"}`. Only an
answered question accepts text. Answers persist independently of definition saves
and do not apply preferences automatically; request another proposal when ready.

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
Retried extraction invalidates previous review, source facts and derived questions.

`POST /sources/{id}/facts` with an optional language requests AI background-fact
proposals from that source's raw extracted text. Each proposed fact must include
an exact evidence quote found in the source. These proposals are not saved or
sent to job clarification until the owner reviews them.
`PATCH /sources/{id}` with `{"facts":["Corrected historical fact", "…"]}`
explicitly replaces and accepts the source's facts (up to 100, 2,000 characters
each). An empty list accepts no facts. Provenance stays attached to the source.
Reviewing or correcting facts clears derived clarification context. Historical
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
job preferences remain independent. `DELETE /api/job-definition` deletes the
definition, all sources/facts/preferences/answers, and queues its originals;
the configured owner and login remain. Part 10 will apply this invalidation rule
to chat records when they exist.

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
