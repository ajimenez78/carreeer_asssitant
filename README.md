# Career assistant

The MVP helps one private user define and refine an ideal job. The backend and
Next.js shell and private job-definition backend are implemented, including owner
login, document/link extraction, reviewed background, AI proposals, saving and
deletion. Requirements and progress live in
[doc/PLAN.md](doc/PLAN.md) and [doc/MVP_SPEC.md](doc/MVP_SPEC.md).

## Prerequisites

- Python 3.14 and [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Docker with Docker Compose v2 for the container stack or local PostgreSQL.
- GNU Make for the convenience commands below.
- Node.js 24 or newer and npm for frontend development/builds.
- `catdoc` for legacy Word extraction when running Python locally
  (`sudo apt-get install catdoc` on Debian/Ubuntu). The Docker image includes it.

## Start and stop locally

Run commands from the repository root. The current health/example routes need no
provider credentials or database; persistence commands use local PostgreSQL.

```bash
make setup
make dev
```

Open <http://127.0.0.1:8000>. The example page calls `/api/health` and displays
`API status: ok`. API documentation is at <http://127.0.0.1:8000/docs>.
Stop the development server with Ctrl+C. To use another port:

```bash
make dev BACKEND_PORT=8001
```

For the backend and PostgreSQL together in Docker:

```bash
make up
```

`make up` builds the locked backend image, starts both services, and waits for
health checks. Ports bind to localhost. The backend container is limited to
512 MiB RAM and one CPU to match the initial Railway Free target.

Check the API from a terminal:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response: `{"status":"ok"}`. Stop the Docker stack with:

```bash
make down
```

To run only PostgreSQL alongside `make dev`:

```bash
make db-up
make db-down
```

PostgreSQL is available at `127.0.0.1:5432`, database/user `career`. Its default
password, `local-development-only`, is for this disposable local setup. Override
it with `CAREER_POSTGRES_PASSWORD` before first database initialization.
`make down` preserves the named database and document volumes. Do not pass
`--volumes` to `docker compose down` unless you intend to delete local data.

## Database and private documents

After `make setup`, initialize the local schema:

```bash
make db-init
```

This starts PostgreSQL, creates the local database if missing, applies Alembic
migrations, and reserves the single owner. Repeating it preserves definitions,
sources, and any configured credentials. The initial owner is named `owner`
with no password hash. Configure login as described below. The schema and storage
contract are in
[doc/PERSISTENCE.md](doc/PERSISTENCE.md).

`DATABASE_URL` optionally overrides the runtime connection. `DATABASE_DIRECT_URL`
overrides the migration connection, falling back to `DATABASE_URL`. PostgreSQL
URLs with or without `+psycopg` are accepted. Keep hosted connections TLS-enabled
and backend-only. Local initialization rejects remote database hosts. For an
already provisioned database, run the separate migration command:

```bash
make db-migrate
```

Migrations never run automatically with the web server. To create a migration
after editing models, use
`uv run --project backend --locked alembic -c backend/alembic.ini revision --autogenerate -m "Describe the change"`
against a local database at the current head, and review the generated operations.

Host-run originals use `.data/documents/`; Docker uses a separate `document_data`
volume at `/data/documents`. Extracted text, reviewed facts, and preferences stay
in PostgreSQL. Source filenames are metadata, not file paths. Local/Neon storage
configuration is listed in [.env.example](.env.example). The Neon adapter needs
explicit Neon credentials and an existing private bucket; no AWS login or cloud
account is needed for local operation.

Removing source metadata queues its original for retryable deletion. Process the
committed queue with:

```bash
make storage-cleanup
```

For Docker-managed originals, use
`docker compose run --rm --no-deps backend python -m career_assistant.db_cli cleanup`
so cleanup uses the same document volume. To apply migrations from the packaged
backend, replace `cleanup` with `migrate`. Host `.data/documents` and the Docker
document volume are separate local stores; keep the same store when reopening a
definition. A failed cleanup leaves its queue entries for retry. API deletions
attempt cleanup after committing and report pending original deletion.

## Private backend workflow

After `make db-init`, configure the owner password interactively:

```bash
make owner
```

Use at least 12 characters. Repeating this command changes the password and
revokes existing sessions. For a different username, run
`uv run --project backend --locked python -m career_assistant.db_cli owner --username your-name`.
For Docker, use `docker compose run --rm --no-deps backend python -m career_assistant.db_cli owner`.

Add `CAREER_SESSION_SECRET` (at least 32 random characters) to the existing ignored
root `.env`, preserving its OpenAI key. Generate the secret locally with
`uv run --project backend --locked python -c 'import secrets; print(secrets.token_urlsafe(48))'`.
Set `CAREER_ALLOWED_ORIGINS` to a JSON array if using other ports/origins. Every
API write, including login, requires a matching `Origin` header. Hosted cookies
must use `CAREER_SESSION_SECURE=true` and an HTTPS origin. Login is disabled
until both the owner password and session secret are configured.

Start `make dev` and use <http://127.0.0.1:8000/docs> to sign in with
`POST /api/session`, save the first draft with `PUT /api/job-definition`, then
add sources, review facts, request clarification, and explicitly save accepted
proposals. The API uses an HttpOnly cookie with twelve-hour sessions; logout
revokes the session on the server. Health remains public.

See [doc/BACKEND_API.md](doc/BACKEND_API.md) for payloads, supported formats,
processing limits, failure/retry behavior, and deletion effects. Editing screens
arrive in Part 8 and real frontend integration in Part 9.

## Frontend development

Install the locked frontend dependencies, then start Next.js:

```bash
make frontend-setup
make frontend-dev
```

Open <http://127.0.0.1:3000>. Stop with Ctrl+C. Override the port with
`make frontend-dev FRONTEND_PORT=3002`. Run `make dev` in another terminal for
the backend at <http://127.0.0.1:8000>; add `make db-up` when a database is needed.
The Part 4 entry page explains the workflow and makes no API requests. Editing,
saving, and uploading arrive in later parts.

The optional public API setting is documented in
[frontend/.env.example](frontend/.env.example). To override it, create
`frontend/.env.local` with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api`.
It defaults to same-origin `/api` for the combined production application.
Next.js embeds `NEXT_PUBLIC_*` values at build time; rebuild after changing them.
Keep the existing root `.env` for backend secrets. Never copy it into `frontend/`,
prefix secrets with `NEXT_PUBLIC_`, or expose secrets through Next.js configuration.
Cross-origin API calls and backend authentication are integrated in Part 9.

Check and test the frontend independently:

```bash
make frontend-check
make frontend-browser-install
make frontend-e2e
```

These run ESLint, TypeScript checks, a production build, and Chromium smoke tests
at desktop/mobile sizes. Browser tests start and stop their own Next.js server
on port 3001; leave that port free. Browser binaries use the same ignored cache
as the backend tests. No provider credentials, database, or backend are needed.

The build generates `frontend/out/`, ready for a static web server. Preview it:

```bash
make frontend-preview
```

Open <http://127.0.0.1:3000> and stop with Ctrl+C. This preview serves static
files only; production will serve them through FastAPI in Part 9. There is no
production Next.js server or `next start` command.

## OpenAI checks

The backend client uses the official SDK and direct Responses API. Keep
`OPENAI_API_KEY` in the existing ignored root `.env`; it is never a frontend
setting. Only explicit facts/clarification requests and the commands below call AI;
uploads, source retrieval, startup, and ordinary saves make no AI calls.

These commands make paid live calls using synthetic data only:

```bash
make ai-smoke
make ai-evaluate
```

The smoke test checks `2+2`; evaluation covers English/Spanish background
extraction, vague preferences, the reference scenario, and a reviewable update.
Results include pass/fail checks, elapsed time, token usage, and estimated cost.
No CV, profile, or other personal source document is sent by these commands.
To save a sanitized report, use
`uv run --project backend --locked python -m career_assistant.ai_cli evaluate --report doc/AI_EVALUATION.json`.

Defaults are `gpt-6-luna`, low reasoning, a 60-second timeout budget, 20,000 input
tokens, and 2,000 output tokens including reasoning. The client counts input
tokens before inference, rejects oversized context, disables automatic retries
and truncation, and requests strict structured output with `store=False`.
Incomplete, refused, or invalid output raises a sanitized error; this client
does not write to the saved definition. Settings can lower those limits but
cannot exceed the agreed caps. See [.env.example](.env.example).

Normal tests use fake transports/clients and never make live OpenAI calls. The
model-selection evidence and its limits are in [doc/AI_EVALUATION.md](doc/AI_EVALUATION.md).

## Configuration

Settings are optional and read from the root `.env` or process environment.
See [.env.example](.env.example). If `.env` already contains your OpenAI key,
keep it and add settings as needed; do not overwrite it with the example file.
`CAREER_APP_NAME` sets the application name in its API documentation.

The Docker scaffold passes only its explicit settings, not the root `.env`
contents. No provider key is embedded in the image. Runtime dependencies and
development tooling are recorded in `backend/pyproject.toml` and `backend/uv.lock`.

## Tests and checks

```bash
make check
make integration
make browser-install
make e2e
```

`make check` runs Ruff and unit tests with coverage; `make test` runs those tests
alone, without a database or external services. `make integration` starts local
PostgreSQL and tests migrations, persistence, constraints, rollback, and deletion
in a uniquely named disposable database. It drops only that database on teardown
and refuses remote connections. The database service stays running; stop it with
`make db-down`. Unit and integration coverage are reported separately. To measure
them together, run
`uv run --project backend --locked pytest backend/tests --ignore=backend/tests/e2e --cov=career_assistant --cov-report=term-missing`
with PostgreSQL running.
`make e2e` launches its own local server and Chromium to test the HTML-to-API
flow and failure/retry behavior; stop commands are not needed for that server.
Tests use synthetic data and stub Neon S3 calls; they need no provider credentials
or cloud access. On Linux, install
Playwright's documented system dependencies if Chromium reports missing shared
libraries. Browser downloads and uv's local cache stay under ignored `.cache/`.

## Local and hosted components

| Local scaffold | Hosted MVP target |
| --- | --- |
| FastAPI/Uvicorn, standalone or in Docker | One Railway Free web service |
| Docker Compose PostgreSQL and named volume | Neon Free PostgreSQL |
| Private host directory or local Docker document volume | Private Neon Object Storage |
| Explicit synthetic AI commands; routine tests use fakes | Backend-only OpenAI API |

The health route checks application liveness, not database or AI readiness.
The private job-definition API, migrations, document storage and AI proposals are
available. The Next.js shell is available separately.
The production image will include its static export when frontend/backend
integration is implemented.
Hosted provisioning and seven-day backup verification belong to Part 11.

## Production packaging

The selected deployment is one application Docker image containing FastAPI and
the Next.js static export. A Node.js build stage compiles the frontend; the final
runtime contains Python and the generated assets, with one Uvicorn process.
Keep the source directories and local development processes separate.

Production PostgreSQL and original documents stay in Neon, outside the application
container. Supply secrets at runtime and run database migrations once as a separate
release step. Local Compose keeps PostgreSQL in its own container and named volume.

The current image contains the backend and packaged migrations. The combined
frontend/backend build will be added and tested in Part 9, before hosted deployment.
