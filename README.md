# Career assistant

A private workspace for clarifying the role you are looking for. Describe your
preferences, add background documents or public links, review extracted facts,
answer focused questions, and explicitly save or refine your current definition.
The interface supports English and Spanish with a remembered language switcher.
The system assesses clarity and provides a natural-language summary; clarification
can be stopped at any time and resumed explicitly.

Parts 1–9 work locally. Chat remains Part 10; Railway/Neon deployment, scheduled
backups and restoration remain Part 11. See [the plan](doc/PLAN.md),
[requirements](doc/MVP_SPEC.md), and [Part 9 validation](doc/PART9_VALIDATION.md).
The subsequent clarity/summary extension is tracked in
[CLARITY_SUMMARY.md](doc/CLARITY_SUMMARY.md).

## Prerequisites

- Docker with Compose for local PostgreSQL and the combined application image.
- Python 3.14 and [uv](https://docs.astral.sh/uv/) for local backend development.
- Node.js 24 or newer and npm; the image builds with Node.js 26 LTS.
- Chromium for browser tests, installed with the commands below.

Run commands from the repository root. Keep an existing ignored `.env`; do not
replace its credentials. For a new checkout, create `.env` from `.env.example`.
Configure a stable `CAREER_SESSION_SECRET` of at least 32 random characters before
signing in. Generate one locally with:

```bash
uv run --project backend --locked python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Save it in the backend `.env`. Add `OPENAI_API_KEY` there to enable explicit
background-fact and clarification requests. The application uses the approved
`gpt-6-luna` model with low reasoning and bounded input/output. Ordinary startup,
uploads, document extraction and saves make no AI calls. Never put secrets in
`frontend/`, `NEXT_PUBLIC_*` variables, build arguments, or tracked files.

## Start locally from a clean checkout

Install the locked dependencies, create/migrate the local database, and configure
the owner on first setup:

```bash
make setup
make frontend-setup
make db-init
make owner
make frontend-check
make dev
```

Open <http://127.0.0.1:8000> and sign in. `make dev` serves the built frontend and
API through one Uvicorn process. Stop it with Ctrl+C. Use `BACKEND_PORT=8001` to
choose another port and add that exact origin to `CAREER_ALLOWED_ORIGINS`.

`make owner` prompts for a password of 12–1,024 characters. It is an explicit
credential change: repeating it revokes existing sessions. Repeated `make db-init`
and `make db-migrate` preserve saved data and configured credentials. Startup does
not migrate databases or configure accounts automatically.

For frontend hot reload, keep `make dev` running and start another terminal:

```bash
make frontend-dev
```

Open <http://127.0.0.1:3000>. This command targets the backend at port 8000 by
default; use `FRONTEND_API_BASE_URL=http://127.0.0.1:8001/api` when needed.
`FRONTEND_PORT` changes the frontend port. Add nondefault origins to the backend's
`CAREER_ALLOWED_ORIGINS` JSON array. Use the same hostname and scheme for both
processes (`127.0.0.1` on both); mixing `localhost` and `127.0.0.1` crosses the
site boundary of the Strict session cookie. Cookies and CORS require exact origins.

Direct `npm --prefix frontend run dev` uses `frontend/.env.local` or the default
same-origin `/api`; see [the public example](frontend/.env.example). Public API
configuration is compiled into the frontend, so rebuild/restart after changing it.

## Run the combined application image

After the initial database/owner/secret setup above:

```bash
make up
```

Open <http://127.0.0.1:8000>. The root-context Docker build compiles the Next.js
static export in a Node.js stage and copies it into a non-root Python image.
One Uvicorn process serves the frontend and `/api`; no Node.js server runs in the
final image. Compose enforces 512 MiB RAM and one CPU for this application.
PostgreSQL and original documents use separate named volumes.

Stop/start with `make down` / `make up`. Those commands retain the volumes. Stop
only PostgreSQL with `make db-down`, and start it with `make db-up`. Do not use
`docker compose down --volumes` for saved work.

Apply migrations explicitly before replacing an application image:

```bash
make db-up
make db-migrate
make up
```

The packaged migration command is
`docker compose run --rm --no-deps backend python -m career_assistant.db_cli migrate`.
It can be used instead of the local migration command after building the image.
The packaged owner command is the same with `owner`, run interactively only when
initializing or deliberately changing credentials.

Migration `0004` adds saved assessments and clarification control. Existing
manually selected `ready` definitions become unassessed `draft` definitions;
their accepted preferences and sources remain. Request an assessment to have
the system determine clarity under the new workflow.

## Workspace and data handling

Save an initial description before adding sources or requesting suggestions.
Incomplete drafts and explicit unknowns are valid. Source reviews and answers
save independently. Suggested criteria stay unapplied until you review and save
them; changing context marks pending suggestions stale. Errors retain typed input,
and an expired session lets you sign in again without discarding pending edits.
Sign-out removes the current workspace from the page.

Request clarification to assess the current saved definition and generate a
natural-language summary in **Summary / Resumen**. The system decides whether
more clarification is useful and explains remaining gaps. Optional unknowns and
skipped questions are allowed. Readiness is not selected manually. Summary text
describes saved criteria; pending suggestions and unsaved edits require review
and saving before they can appear as accepted requirements. Changes to the
definition or its context clear the previous assessment until the next explicit
request. Assessments and summaries reuse the clarification call; opening the
workspace and saving do not trigger AI.

Use **Stop clarification / Detener aclaración** even while a request is running.
The stopped state persists after reopening and does not mark the definition
ready or discard edits. Resume explicitly before requesting another round.

Use **Interface language / Idioma de la interfaz** in the header. Switching keeps
user content and unsaved edits intact. Assistance defaults to the selected UI
language, with an independent selector for new requests. Existing documents,
answers, and previously generated content keep their original language.

Supported uploads are text-based PDF, `.doc`, `.docx`, `.md`, and `.markdown`:
up to five files of 10 MiB each. Scanned-document OCR is deferred. Public URLs are
retrieved with bounded processing and internal-network/redirect protection;
restricted pages offer upload/paste fallback. Only explicitly accepted facts
become background context. Historical skills do not become desired job criteria
automatically. No personal example files are used by routine tests.

Removing a source removes its text/facts and clears derived questions/answers
and the clarity assessment/summary;
accepted job criteria remain. Whole-definition deletion removes its associated
live records. Original-file deletion is queued durably; the UI reports pending
cleanup and can retry. A failed original upload leaves a visible reserved source
that can be removed and uploaded again. Retry queued originals from the CLI with:

```bash
make storage-cleanup
```

Backups with seven-day retention are an agreed Part 11 requirement and are not
scheduled by the local application. Keep appropriate independent copies until
that operational work is implemented. Detailed payloads and limits are in
[the backend API](doc/BACKEND_API.md) and [persistence notes](doc/PERSISTENCE.md).

## Mock preview

The real backend is the default. For the isolated Part 8 browser-local preview:

```bash
NEXT_PUBLIC_API_MODE=mock make frontend-dev
```

The visible mock notice distinguishes it from the private workspace. Mock data is
stored only in that browser and is never imported into PostgreSQL automatically.
The preview simulates binary extraction, public retrieval and AI; it provides no
real authentication, original storage or backups. Use synthetic data. This setting
is build-time only; a URL or browser-storage value cannot enable mocks in a real
build. The combined Docker image always builds in real-backend mode.

## Tests and validation

```bash
make check
make integration
make frontend-check
make frontend-contract
make browser-install
make frontend-browser-install
make frontend-e2e
make e2e
```

`make check` runs Ruff and backend unit tests; `make integration` starts local
PostgreSQL and uses disposable migrated databases. `make frontend-contract` runs
component/client/catalog tests and validates synthetic payloads against the backend
schemas without a server. `make frontend-e2e` runs desktop/mobile mock workflows
on port 3001 in an isolated Next.js output directory. If using `PLAYWRIGHT_BASE_URL`,
point it only at an explicitly mock-enabled preview.

`make e2e` builds/checks the real-mode frontend and starts local PostgreSQL.
It serves that export with the real backend, sessions,
PostgreSQL and file parser. Fake AI and deterministic URL retrieval are injected
only by the test harness. Each run creates/removes its own database and temporary
originals. No existing owner, definitions or documents are changed. The live test
is skipped in ordinary runs.

Validate the combined image, packaged migrations, browser workflow and application
replacement with external persistence:

```bash
make release-check
```

This builds `career-assistant:part9`, uses a disposable database and Docker volume,
and records [the release check](doc/PART9_RELEASE_CHECK.json). Its first container
mounts a read-only test launcher with fake AI; the replacement runs the unchanged
production command without that mount. All test resources are removed afterward.

The explicitly paid live workflow uses two bounded generations and synthetic
content only, against its own temporary database:

```bash
make workflow-live
```

Results are in [the live workflow report](doc/PART9_AI_WORKFLOW.json). Additional
provider-only diagnostics remain available as `make ai-smoke` and `make ai-evaluate`.
They require the backend key and incur inference charges; ordinary tests do not.

## Deployment

No cloud resources have been provisioned. [The Part 11 deployment procedure](doc/DEPLOYMENT.md)
records configuration, separate migrations, authentication, smoke checks and
rollback. Railway/Neon account availability, ongoing free allowances, private
object storage, independent backups and restoration must be verified in Part 11.
Any paid hosting upgrade requires your explicit choice.
