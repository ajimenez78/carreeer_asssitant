# MVP persistence

Part 5 design review, 2026-11-01. This implements the approved single-owner,
single-current-definition lifecycle. Parts 6–7 subsequently implemented AI,
authentication, extraction and API handlers; see [BACKEND_API.md](BACKEND_API.md).
Part 10 adds persistent conversation storage through migration `0005`.

## Schema and workflow review

| Table | Purpose and constraints |
| --- | --- |
| `owners` | One configured owner, enforced by primary key/check `id = 1`. Unique login name; nullable password hash means login is not configured. No plaintext password or public registration. |
| `job_definitions` | Stable UUID, unique owner foreign key, nonempty original description, system-assessed draft/ready state, creation/update times. Nullable JSONB assessment stores summary/clarity and language/time/context metadata. A separate clarification-paused flag and nonnegative monotonic control version persist stop/resume and reject obsolete in-flight results. Updates replace the current accepted state; no revisions. |
| `preferences` | Definition foreign key, unique criterion key per definition, category, mandatory/preferred/excluded priority, nullable JSONB value, optional explanatory text. SQL NULL represents unknown. JSONB holds a single structured value, not an entire definition. |
| `sources` | Definition foreign key, UUID, kind (file/URL/text), display name, original URL or object key as appropriate, media type/size, extraction state/text, review timestamp. File slots 1–5, unique per definition, enforce five files; each is at most 10 MiB. |
| `background_facts` | Source foreign key, editable fact text, timestamps. Facts are reviewed through their source and never automatically become preferences. |
| `clarifications` | Definition foreign key, round UUID, position 1–3, question, answer state (unanswered/answered/skipped/unknown), nullable answer, timestamps. Unique round/position limits each round to three questions. |
| `chat_turns` | Request UUID, definition foreign key, 1–4,000 character message, assistance language, UTC timestamp, and validated response JSONB including reply, reviewable proposal, context token, and usage. Message/response commit together; UUID retries reuse the saved result. |
| `document_deletions` | Durable queue of object UUIDs to remove after the metadata transaction commits. No foreign key to a deleted source or definition. |

All foreign keys cascade on parent deletion. UUIDs identify domain records;
UTC-aware timestamps use PostgreSQL `timestamptz`. Check constraints enforce
states, nonempty text, and source-kind/answer consistency. Referencing columns
are indexed. Schema changes use Alembic, never application-startup `create_all`.

Criterion keys distinguish independent constraints in the same category. For
example, `remote` can be preferred while `hybrid_location` and
`onsite_limit` are mandatory. A compensation value can retain separate
`currency`, `minimum`, `maximum`, `period`, and `basis` members as unknown until
clarified. Part 7 validates detailed domain payloads; Part 5 validates
the persistence envelope and does not infer missing values.

| Approved interaction | Persistence behavior |
| --- | --- |
| Save an incomplete description | Create the current definition; empty optional context is allowed. |
| Review and explicitly save edits | Update the same UUID and replace only the supplied preference set within one transaction. Source/answer actions use their own transactions. |
| Assess clarity and summarize | Store the validated assessment and post-question context in the explicit clarification transaction; only sufficient clarity sets ready. Unaccepted preference proposals remain separate. |
| Change saved criteria or answer/source context | Invalidate derived assessment/summary and return to draft. An unchanged definition save preserves the current assessment. |
| Stop or resume clarification | Persist the separate paused flag and increment control version when changed; keep accepted data and current assessment. Stop/resume changes prevent an older in-flight result from applying. |
| Add context and review facts | Sources and facts have their own records; only reviewed sources supply accepted background. |
| Skip or answer a clarification | Store an explicit answer state; skipped/unknown answers remain NULL. Unreviewed proposals do not update preferences. |
| Remove a source | Delete original-source metadata and facts, clear all derived clarification context, and queue its original file for removal. Accepted preferences remain. |
| Delete the definition | Cascade all associated records and queue every original file. Keep the configured owner. |
| Failed save | Roll back the transaction; previously accepted data remains. |

The walkthrough preserves Staff scope, broad architecture, AI preference, and
the frontend-only exclusion without turning historical CV skills into goals.
Unknown salary and the office-day period remain unknown. This review establishes
the schema before implementation; it does not assert that later AI/API behavior
is already implemented.

## Storage and deletion boundary

`DocumentStore` exposes put/get/delete by an opaque UUID. User filenames never
become paths. Local originals live in `.data/documents/` in a private directory;
Private R2 originals use `documents/<UUID>` in a preconfigured private bucket. Raw
extracted text, corrected facts, provenance, and preferences live in PostgreSQL.
Neither originals nor personal text belong in the image or logs.

The S3 adapter uses its HTTPS endpoint and explicit bucket-scoped R2 credentials,
SigV4, path-style addressing, and bounded timeouts. It neither provisions a
bucket nor uses an AWS account. Tests use a stubbed S3 client. Real account,
endpoint, bucket privacy, and provider behavior are verified in Part 11.
See [R2 S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/).

Database and object storage do not share a transaction. Deletion therefore
removes live context and records a cleanup entry atomically; a separate cleanup
operation removes private bytes and acknowledges the entry. Missing objects
count as success; failures leave the queue available for retry. Never run cleanup
before the metadata transaction commits. Part 7 must report pending cleanup
accurately and trigger retries; Part 11 adds scheduled operational retries.
Provider lifecycle and retained backup copies must also be checked during deployment.

Upload coordination in Part 7 must avoid orphan objects: reserve the source/key
in a committed transaction, write the object, then update extraction state;
retain a failed source for retry or explicit removal. Do not acknowledge a
successful upload before both metadata and bytes are durable.

## Initialization, migration, and recovery contract

Keep PostgreSQL 18 for local/Render parity; Render supports this major
([Render Postgres](https://render.com/docs/postgresql-creating-connecting)).
Local initialization creates a missing database through the local `postgres`
maintenance database and applies Alembic to head. Repeating it preserves data.
Hosted migrations use an already provisioned database and the direct TLS URL;
they never try to create a hosted database. Migrations run as a separate release
step, not with each web process. Integration tests create a unique disposable
local database, migrate it, and drop only that generated database on teardown.

The 2026-11-02 clarity/summary extension uses migration `0004` to add assessment
and pause/control-version columns. Legacy manually selected ready state becomes
unassessed draft; accepted preferences, sources, answers, and credentials remain.
The next explicit assessment determines readiness. Validation for this extension
is recorded separately in [CLARITY_SUMMARY.md](CLARITY_SUMMARY.md).

The Part 11 backup implementation pairs a custom-format `pg_dump` with a UTF-8 JSON
manifest and originals under `documents/<UUID>`. The manifest records format
version, UTC capture time, database identity hash, Alembic revision, database-dump
SHA-256, and each confirmed original's object UUID, relative path, size, and SHA-256.
Source IDs and provenance remain in the SQL dump. A consistent PostgreSQL snapshot
and coordinated row locks keep writes/cleanup from changing the captured context;
every referenced original is copied and verified before publication. The deletion
queue stays in the dump; loose files do not resurrect deleted sources.

Restore into a disposable empty database/private directory: verify hashes and
manifest paths, copy originals, restore the dump transactionally, check foreign
keys and reviewed context, then drain pending deletions. Validate before swapping
runtime configuration. Retain successful daily copies for seven days; prune older copies
only after a successful backup. Source deletions are immediate in live context;
backup copies expire under this policy. Local tests, daily GitHub scheduling and
real Render/R2 backup/restoration drills pass. The hosted drill used a disposable
database and temporary originals in the private backup bucket, then removed both.
The additional R2 lifecycle expiry backstop remains pending. Evidence
and setup are in [PART11_VALIDATION.md](PART11_VALIDATION.md) and
[DEPLOYMENT.md](DEPLOYMENT.md).

## Later phases

Future offers and matches can reference the stable definition UUID; skill plans,
applications, interviews, and career progress can reference that owner and their
relevant offer/process. No tables for those workflows are created now. Conversation
records belong to the current definition, with the same source-context invalidation
rule; they are not definition revision history.

## Part 7 additions

Revision `0003` adds revocable `owner_sessions`, persistent login-throttle fields,
and source `original_stored`/`extraction_error` status. Original writes coordinate
with deletion using the definition lock after reserving metadata. Extraction or
storage failure clears review/facts/derived clarification context. The API
reports pending cleanup and supplies a retry endpoint. Owner reconfiguration
revokes sessions without replacing the definition.

The backup manifest must include confirmed originals (`original_stored=true`);
unconfirmed/failed source metadata stays in the database dump without promising
missing original bytes. Restore preserves those recoverable source states.
The consistent write/cleanup pause and seven-day retention contract still apply;
the implementation and its local restoration evidence are recorded in Part 11.

## Part 10 additions

Migration `0005` only adds `chat_turns` and its foreign-key index. Existing accepted
criteria, sources, assessments, credentials and sessions remain unchanged. A source
extraction/review/deletion clears derived chat and clarifications in the same
transaction. Whole-definition deletion cascades chat. Successful in-scope messages
invalidate the saved assessment/control version, and conversation identity/content
participates in proposal tokens. This prevents stale chat or structured proposals
from applying after changes. The request UUID prevents duplicate committed turns.

The existing local `0004` database was privately backed up, restored into an isolated
clone, migrated and compared before applying `0005` locally. Every original table's
rows were compared canonically in memory and remained unchanged; the new chat table
was empty. The private dump is retained under ignored `.data/backups/`; it is not
a replacement for Part 11's scheduled independent backups. See
[Part 10 validation](PART10_VALIDATION.md).
