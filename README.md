# Career assistant

A private workspace for clarifying the role you are looking for. Describe your
preferences, add background documents or public links, review extracted facts,
answer focused questions, and explicitly save or refine your current definition.
The interface supports English and Spanish with a remembered language switcher.
The system assesses clarity and provides a natural-language summary; clarification
can be stopped at any time and resumed explicitly. Chat refines the same definition
through proposals that you review and save.

The Free Render preview is live at [career-assistant-jgpm.onrender.com](https://career-assistant-jgpm.onrender.com),
with Render PostgreSQL, R2 originals and verified daily backups. Final Part 11
acceptance items are recorded in the deployment status. See [the plan](doc/PLAN.md),
[requirements](doc/MVP_SPEC.md), and [Part 9 validation](doc/PART9_VALIDATION.md).
The subsequent clarity/summary extension is tracked in
[CLARITY_SUMMARY.md](doc/CLARITY_SUMMARY.md). Chat evidence is in
[Part 10 validation](doc/PART10_VALIDATION.md).

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

Migration `0005` adds conversation storage without changing existing records.
Run `make db-migrate` before starting the updated backend.

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

Use **Chat with assistant / Hablar con el asistente** at the bottom right from any
step. The floating panel can be minimized without losing conversation or typed
input; Escape minimizes it and returns keyboard focus to its launcher. The first
message can start a saved role draft. Existing description/criteria edits stay in
the editor until you save them. You can keep chatting with pending edits or
suggestions; chat uses saved context, and those edits must be saved/discarded before
reviewing a new chat proposal. Messages and replies persist together after a
successful request; failures retain typed input.
Use **Review chat suggestions** to open the same **Review & save** editor, edit
or remove suggestions, and explicitly apply them. Reopening Chat restores the
conversation without calling AI. The assistant is independent of the numbered
steps and remains the common entry point for later product phases. Old proposals
remain historical after context
changes. Chat stays within job definition and respects the stop/resume control.
The assistant uses the saved criteria, reviewed background, and retained conversation;
unaccepted proposals remain separate from accepted preferences.

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

Removing a source removes its text/facts and clears derived questions/answers,
conversation, and the clarity assessment/summary;
accepted job criteria remain. Whole-definition deletion removes its associated
live records. Original-file deletion is queued durably; the UI reports pending
cleanup and can retry. A failed original upload leaves a visible reserved source
that can be removed and uploaded again. Retry queued originals from the CLI with:

```bash
make storage-cleanup
```

The hosted workspace has daily independent backups with seven-day pruning;
the local application does not schedule backups. Detailed payloads and limits are in
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
CAREER_RELEASE_CPUS=0.1 make release-check
```

This builds `career-assistant:part11`, uses a disposable database and Docker volume,
and records [the release check](doc/PART11_LOCAL_RELEASE_CHECK.json). Its first container
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

Run the separate paid synthetic chat quality check with `make chat-live`. It uses
four bounded calls through the existing model client and writes
[PART10_AI_EVALUATION.json](doc/PART10_AI_EVALUATION.json). It does not load personal
sources or change saved data. Chat keeps the existing 20,000 input/2,000 output
token caps and 60-second timeout. Oversized context is rejected without truncation;
manual editing remains available.

## Deployment

Use **Render for the app and PostgreSQL**, with private Cloudflare R2 Standard
storage for uploaded documents and a separate private R2 bucket for daily backups
retained seven days. You re-enabled backups on 2026-11-02.
Neon is no longer used. The root commands `npm run build` and `npm start` build
and start the combined frontend/API locally. Settings load `.env`, then `.env.local`.

`render.yaml` declares a Free web service and Free PostgreSQL 18 database in
Frankfurt. **The Free database expires after 30 days.** This configuration is a
preview, not an ongoing free hosting solution. You explicitly selected this free
30-day preview on 2026-11-02. No paid upgrade is authorized.
[Render database limits](https://render.com/docs/free).

The blueprint supplies the internal database URL automatically. Runtime database
traffic requires TLS on Render's private network; external operations use the
full public hostname with certificate verification. Uploaded files use the
backend-only `CAREER_S3_*` settings for the private R2 bucket.

Migrations and owner setup run separately before deployment:

```bash
make operations-image
# Use a private ignored operations file with the external Render database URL.
docker run --rm --env-file .env.operations.local career-assistant-operations:part11 python -m career_assistant.operations release
docker run -it --rm --env-file .env.operations.local career-assistant-operations:part11 python -m career_assistant.db_cli owner
```

For a schema upgrade, create a verified backup first and pass its key to
`release --backup-key`. Render startup validates security, migration head and
owner configuration. It does not migrate the database.

The [deployment runbook](doc/DEPLOYMENT.md) explains private storage, network access,
release/recovery commands and quotas. [Part 11 status](doc/PART11_VALIDATION.md)
records local and deployed checks. The preview is live; use your existing local
login. The free database expires on **2 December 2026 at 17:45 Madrid time**; see
[resource details](doc/PART11_RENDER_PREVIEW.json).
The Free web service sleeps when idle. Its first authenticated request after
17 idle minutes took 32.9 seconds and preserved the workspace/session.

Daily backups are enabled at 03:17 UTC (04:17 Madrid during this preview), with
seven-day pruning. The [first GitHub-hosted run](https://github.com/ajimenez78/carreeer_asssitant/actions/runs/41488898644)
and a real restoration drill passed. Public SQL access stays blocked between
maintenance runs; the workflow temporarily admits only its own runner.

R2 dashboard setup remains: add seven-day expiry for the `career-backups/` prefix
and separate bucket-scoped credentials. The supplied key works for both buckets
but cannot configure lifecycle rules.
