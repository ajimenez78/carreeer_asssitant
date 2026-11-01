# Part 7 validation

Verified locally on 2026-11-01. The private backend workflow is implemented;
frontend editing, integrated browser journeys, chat, hosting and backups remain
the subsequent planned parts. The contract is in [BACKEND_API.md](BACKEND_API.md).

## Automated checks

- Ruff lint/format checks pass.
- 167 deterministic unit/PostgreSQL tests pass, with 94% statement coverage of
  1,371 backend statements at this validation point. Two Chromium scaffold
  regression tests also pass. Browser tooling retains its existing upstream
  pytest fixture deprecation warning.
- API/database checks cover initial save, optional context, unreviewed-source
  exclusion, fact correction/provenance, clarification, unknown/skipped answers,
  reviewed apply, stable identity, restart/reload and later refinement. They also
  cover rollback after failed commit, unavailable/invalid AI output, stale AI
  results, file slots, extraction failure/retry, and removal of deleted source
  content from future prompts while preserving accepted preferences.
- Access tests cover unauthenticated reads/writes/originals, exact Origin checks,
  HttpOnly/SameSite cookies, server-side logout revocation, expiry, persisted login
  throttling, and owner reconfiguration. Routine tests use fake AI and synthetic
  documents, without credentials or paid inference.
- Parsers are exercised in real child processes. PDF/DOCX/Markdown fixtures are
  generated; the committed short binary DOC is synthetic. Checks include corrupt,
  unsupported, empty and oversized files, image-only/encrypted/overlong PDFs,
  expanded DOCX limits/XML entities, resource timeout/termination, and absence of
  provider credentials in the worker environment. Child-process executed lines
  are not collected by the normal coverage run; the low worker-module percentage
  does not mean those parser paths were skipped.
- URL checks cover private/metadata/loopback/multicast/reserved/IPv6 transition
  addresses, mixed DNS answers, IP pinning, redirects into internal networks,
  compression, excessive bodies and inaccessible pages. A real public HTTPS
  retrieval of `https://example.com` succeeded through the worker (175 characters).
- Repeated `make db-init`, packaged `db_cli migrate`, old-schema-to-head migration
  data/credential preservation, and Alembic drift checks pass. Existing local
  credentials were preserved. No hosted services were provisioned.

Final `make check` passes (124 tests without a database); the combined 167-test
run includes PostgreSQL integration. Coverage totals are from that combined run.
The latest image also passed a real HTTP/PostgreSQL smoke test in a disposable
database/container: login, save/reload, a full 10 MiB binary DOC upload, original
download, fact review, complete deletion, original cleanup, and logout. It used
512 MiB/one CPU, peaked at 176.11 MiB, and processed the upload in 0.2814 s. Three
warm GET-plus-save pairs each completed within 0.0403 s. This check made no AI
calls. See [result](PART7_CONTAINER_CHECK.json). Reproduce after `make db-up` and
`docker compose build backend` with
`uv run --project backend --locked python backend/scripts/check_container_api.py`.
The script refuses remote database creation and removes only its generated test
database/container; it leaves the normal local database and credentials alone.

The environment's previously documented TestClient/network restrictions require
tests and Docker checks outside its execution sandbox. Local catdoc was extracted
from the built runtime image into an ignored project cache rather than installed
into the host system. Normal local development requires catdoc on PATH, as in the
README; the image already includes it.

## Parser measurements

Eight fresh containers used `--memory=512m --cpus=1 --network=none`. Each loaded
the actual application and executed the production extraction worker. The full
runtime libraries were present; no development server or parser suite was loaded.
See [raw measurements](PART7_RESOURCES.json).

| Format | Small input / container peak | Near-10 MiB input / container peak | Large-input extraction CPU |
| --- | --- | --- | --- |
| PDF | 705 B / 145.32 MiB | 10,484,392 B / 222.64 MiB | 0.1414 s |
| DOCX | 445 B / 123.49 MiB | 10,485,256 B / 144.50 MiB | 0.0642 s |
| DOC | 9,216 B / 124.26 MiB | 10,485,760 B / 155.31 MiB | 0.0659 s |
| Markdown | 45 B / 124.28 MiB | 10,485,760 B / 154.25 MiB | 0.0705 s |

All eight extractions succeeded without OOM kills. Large PDF/DOCX/Markdown
samples returned 44,999 characters; large DOC padded the real short OLE fixture.
Padding exercises upload-sized bytes, not every possible complex document.
Application RSS high-water marks can exceed cgroup memory accounting because
they include shared mappings; the container peak is the measured runtime budget.
Parser processes independently enforce 256 MiB address space, eight CPU seconds,
and fifteen seconds wall time. Other content exceeding those bounds is rejected
with an upload/paste recovery path rather than silently truncated.

These checks demonstrate compatibility of the approved formats with the local
512 MiB / one-CPU cap on this corpus. They do not establish Railway's monthly
free-allowance fit, full frontend/backend peak, maximum simultaneous requests,
hosted cold starts, or backup costs; those measurements remain Parts 9/11.

Reproduce one case after `docker compose build backend`:

```bash
docker run --rm --memory=512m --cpus=1 --network=none \
  --mount type=bind,src="$PWD/backend/scripts",dst=/checks/scripts,readonly \
  --mount type=bind,src="$PWD/backend/tests/fixtures",dst=/checks/tests/fixtures,readonly \
  --entrypoint python career-assistant-local-backend \
  /checks/scripts/measure_extraction.py doc --large
```

Replace `doc` with `pdf`, `docx` or `md`; omit `--large` for the small case.

## Application AI schema check

Two explicit paid calls exercised the actual Part 7 schemas with `gpt-6-luna`, low
reasoning: the synthetic reference definition and Spanish background containing
an embedded instruction to invent a doctorate. All acceptance gates passed.
The reference preserves Staff/architecture/cross-team/learning/international
scope, AI/remote preferences, mandatory conditional Madrid and two-day hybrid
constraints, frontend-only exclusion, null salary members and null office period.
It asks about compensation and the office period and adds no SQL requirement
from historical background. Spanish facts retain exact evidence and omit the
invented doctorate. Proposals remain unaccepted until an explicit save/review.

See [sanitized result](PART7_AI_CHECK.json): 908 + 329 input tokens, 763 + 81 output
tokens, 8.587 s and 3.300 s including preflight. Estimated total inference cost:
$0.0005457 using the Part 6 verified rates. This is a small schema/quality check,
not a production SLA or a substitute for the Part 9 integrated live workflow.

To rerun explicitly (paid, synthetic only):

```bash
uv run --project backend --locked python backend/scripts/check_workflow_ai.py \
  --report doc/PART7_AI_CHECK.json
```

## Issues diagnosed and resolved

Antiword 0.37-17 rejected the valid short LibreOffice-exported DOC with “text
stream … too small” in both the host and runtime container. Its implementation
rejects WordDocument streams below the OLE big-block threshold
([Debian source](https://sources.debian.org/src/antiword/0.37-17/wordole.c)).
Catdoc 1:0.95-6 reads the same fixture correctly and stays within the measured
runtime budget, so the runtime uses catdoc. This preserves legacy DOC support.

A regression test reproduced a 409 when retrying a reviewed file during storage
failure: setting extraction to failed while retaining `reviewed_at` violated the
schema's review/extraction invariant. The failure path now uses the repository's
invalidation operation, atomically clearing source facts and clarification
context while retaining accepted preferences. The regression passes.

The preexisting old-schema migration test initially queried the new owner columns
after downgrading to revision 0001. Its fixture now seeds the old schema with SQL,
then verifies the current ORM after upgrade, preserving the original migration
and credential checks instead of querying an incompatible schema.

A chunked-upload regression reproduced 3,854,415 bytes of Python buffer allocation
for only 20,000 input bytes because each tiny network message was retained as a
separate object. The request boundary now buffers the bounded bytes directly,
passing the same test below 1 MiB. Chunked requests still enforce the same total
byte cap as declared-length requests.
