# Part 9: local frontend/backend integration

Completed locally on 2026-11-02 after the user's explicit Part 8 approval and
request for Part 9. Chat and hosted deployment remain Parts 10 and 11.

## Delivered implementation

- Real credentialed HTTP is the default. API configuration uses the public build-time
  base URL; backend secrets remain server-only. Multipart uploads let the browser
  set the boundary. Network, proxy/non-JSON, and API errors preserve input.
- Owner sign-in, failed-login feedback, sign-out, initial session checking and
  expiry recovery use the existing database-backed, signed HttpOnly session cookie.
  Expiry hides the workspace while keeping pending edits mounted; reauthentication
  does not replay a failed write automatically. Sign-out unmounts private content.
- Existing English/Spanish catalogs cover the new authentication and real-service
  error/recovery messages. UI switching preserves input and API enum values.
- FastAPI serves the Next.js static export and API in one process. API routes take
  precedence over static files; unknown API paths return JSON 404, not HTML. Private
  data/originals remain behind the API, outside the public asset directory.
- Credentialed CORS permits only configured exact origins and methods/headers.
  Browser preflights and API error responses work without relaxing origin checks
  or SameSite=Strict cookies. Local cross-origin requests must use matching hostnames
  and schemes; production uses one HTTPS origin.
- Original-upload failures expose the durable reserved source while retaining the
  selected file. The UI explains remove/re-upload when no original was stored.
  Deletion outcomes show pending original cleanup and provide explicit retry.
- `NEXT_PUBLIC_API_MODE=mock` is an explicit build-time development/test choice.
  There is no query-string/storage switch or fallback to mocked success. The image
  fixes real mode and same-origin `/api`. Existing browser-local preview data stays
  separate from PostgreSQL and is not transmitted/imported automatically.
- `backend/Dockerfile` uses the repository-root context: Node.js 26 LTS builds the
  frontend; a non-root Python/Uvicorn image contains only its export and backend.
  No Node runtime, frontend dev server or test launcher is installed in the final
  runtime. Local Compose retains separate PostgreSQL/document named volumes and
  512 MiB/one-CPU application limits. No migration or inference runs at startup.
- README gives clean-checkout setup, owner/secret configuration, one-origin and
  hot-reload workflows, image operation, test commands and safe stop/replacement.
  [DEPLOYMENT.md](../../../operations/DEPLOYMENT.md) records the future Railway/Neon procedure with
  separate migrations, access controls, smoke checks and distinct rollback/recovery.

No new application dependency was required. Current lockfiles are retained.
Node.js 26 LTS is used only by the new build stage. The backend's existing Python
3.14 constraint and parser/runtime limits remain in place.

## Local checks

| Check | Observed result |
| --- | --- |
| Ruff | All checks pass; 50 Python files formatted. |
| Combined backend unit/PostgreSQL suite | 168 pass; 94% statement coverage of 1,373 statements. Parser-child coverage is not fully collected by the parent. |
| Frontend ESLint, route types, TypeScript and production build | Pass. |
| Frontend unit/component/client/catalog tests | 15 pass, including real HTTP configuration, cookie/cache options, multipart and empty-204/proxy-error handling. |
| Pydantic contract check | 15 synthetic mock request/response payloads validate against existing backend schemas. |
| Mock-mode Chromium regressions | 22 pass across desktop/Pixel 7 sizes in an isolated Next.js output directory. |
| Real-backend Chromium | 7 pass; the explicit paid live test is skipped in ordinary runs. |
| Explicit live synthetic workflow | Passes with two `gpt-6-luna` generations. See [PART9_AI_WORKFLOW.json](../evidence/PART9_AI_WORKFLOW.json). |
| Combined image and replacement | Passes. See [PART9_RELEASE_CHECK.json](../evidence/PART9_RELEASE_CHECK.json). |
| Docker context audit | 53 allowed source/lock/config files, approximately 444 KB; no .env, personal documents, credentials, dependencies, tests or caches. |

The real browser suite uses a newly migrated disposable PostgreSQL database,
temporary private originals, the actual static export and real document parser.
AI and public-URL outcomes are deterministic injected test adapters, not production
configuration switches. It covers PDF upload → evidence/fact correction → link →
clarification → explicit application → all answer states → save/reload/refine,
application reconstruction and authenticated original download. Other cases cover
AI unavailability, invalid uploads, restricted-link paste fallback, expiry and
reauthentication without losing edits, sign-out, source/context deletion, original
write/delete failures and recovery, Spanish login/upload errors, and real browser
cross-origin cookies/preflights/writes with untrusted-origin rejection.

`make e2e` and `make workflow-live` build/check the real frontend and start local
PostgreSQL before testing, so the browser cannot silently use an outdated export.
`make frontend-e2e` uses an explicit mock-mode Next.js server and a separate output
folder, preserving an existing development preview. Test databases and originals
are disposable; existing owner credentials, saved work and .env are preserved.

## Live synthetic check

The explicit `make workflow-live` browser check signs into the temporary application,
saves the synthetic reference description, uploads a synthetic Markdown CV, requests
background facts, accepts reviewed facts, requests clarification, reviews/applies
criteria, reloads and manually refines the same definition. No personal example
files or real user data are loaded or transmitted.

Both generations succeed and pass the recorded gates for Staff scope, architecture,
Madrid hybrid location, a two-day cap with unknown period, no invented compensation,
clarification questions and save/reload/refine preservation. The two SDK boundary
latencies are 4.473 s and 9.748 s. Usage is 1,243 input / 890 output tokens including
reasoning; estimated inference cost is $0.0005693 using the existing Part 6 rate
assumptions. This is a small end-to-end check, not a latency percentile, account
balance/rate-limit measurement, or broader model-quality evaluation. Provider
errors and token/input/output limits remain covered by deterministic backend tests.

The existing client keeps strict structured-output validation consistent with the
[official Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).
No model upgrade, API endpoint change, automatic retries or additional live checks
were needed for Part 9.

## Packaged release check

`make release-check` builds the combined image, creates an isolated SQL database
and named document volume, and runs the image's packaged migration command twice.
It configures only a synthetic owner. The first container mounts a read-only test
launcher/provider to exercise the full browser flow without paid calls. The
replacement uses the unchanged production CMD with no test mount or provider key.
The same cookie, definition identity, preferences, sources and original Markdown
bytes survive replacement; missing API/private-file requests return 404.

The check confirms UID 10001, no Node executable, no `/app/.env`, and no test mount
in the replacement. A runtime memory snapshot during the workflow is 113.6 MiB
under the imposed 512 MiB limit; one CPU is imposed too. This is not a peak-memory
or monthly Railway allowance guarantee. The image identifier is recorded in the
JSON report. This is a working-tree candidate, not a committed or deployed release.
All temporary containers, volumes, runtime env files and the release database are
removed by the harness; existing Compose data volumes remain.

## Diagnosed issues and remaining limits

- Initial Docker negation rules re-admitted dependency directories (a 474.82 MB
  context). Explicit parent/child deny-and-allow rules reduce the exported context
  to about 444 KB; a separate context export verified the exclusions before the
  final candidate was built. The final image copies only approved source/export.
- Docker Desktop does not bind this host's `/tmp` files. A harmless mount probe
  reproduced `bind source path does not exist`; release-test temp files now live
  under the ignored shared checkout cache and are removed afterward.
- The new isolated mock build output initially fell outside ESLint's generated-file
  ignores. That produced generated-bundle lint errors; the ignore now includes
  exactly that generated directory. A Spanish error test then exposed an older
  export left by the failed build. Explicit build prerequisites fix test ordering;
  the rebuilt real frontend passes that case without a runtime translation workaround.
- The existing upstream pytest/Playwright fixture deprecation warning and Node
  `NO_COLOR`/`FORCE_COLOR` warnings remain; they do not fail the checks.
- `npm audit` reports one moderate minimatch glob-pattern denial-of-service advisory
  propagated through 12 lint-tool dependency entries. The affected package is absent
  from `npm ls minimatch --omit=dev` and from the Python-only runtime. No high/critical
  findings were reported. Audit fix suggestions downgrade/break the established lint
  stack, so no blind force update was applied. Track the upstream tooling fix; this
  check does not claim the development dependency tree is vulnerability-free.

The standalone original-download endpoint is authenticated and tested; no public
file directory is mounted. Scheduled backup/cleanup jobs, seven-day independent
retention, restoration, hosted privacy, ongoing free-tier fit, HTTPS and deployed
smoke tests remain Part 11. Chat remains Part 10. No cloud provisioning, deployment,
paid hosting upgrade, or unrelated later-phase workflow was performed.
