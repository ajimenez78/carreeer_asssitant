# Career assistant

The MVP helps one private user define and refine an ideal job. Part 3 provides
the Python backend scaffold and local PostgreSQL infrastructure. Requirements
and progress live in [doc/PLAN.md](doc/PLAN.md) and [doc/MVP_SPEC.md](doc/MVP_SPEC.md).

## Prerequisites

- Python 3.14 and [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Docker with Docker Compose v2 for the container stack or local PostgreSQL.
- GNU Make for the convenience commands below.

## Start and stop locally

Run commands from the repository root. The backend needs no provider credentials
and runs independently of PostgreSQL at this stage.

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
`make down` preserves the named database volume. Do not pass `--volumes` to
`docker compose down` unless you intend to delete local database data.

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
make browser-install
make e2e
```

`make check` runs Ruff and in-process API/configuration tests with coverage.
Run `make test` for just the API/configuration tests.
`make e2e` launches its own local server and Chromium to test the HTML-to-API
flow and failure/retry behavior; stop commands are not needed for that server.
Neither test suite needs provider credentials or cloud access. On Linux, install
Playwright's documented system dependencies if Chromium reports missing shared
libraries. Browser downloads and uv's local cache stay under ignored `.cache/`.

## Local and hosted components

| Local scaffold | Hosted MVP target |
| --- | --- |
| FastAPI/Uvicorn, standalone or in Docker | One Railway Free web service |
| Docker Compose PostgreSQL and named volume | Neon Free PostgreSQL |
| Private local files in the later upload module | Private Neon Object Storage |
| No AI calls in this scaffold | Backend-only OpenAI API integration in Part 6 |

The health route checks application liveness, not database or AI readiness.
Database schema/migrations are Part 5, AI connectivity is Part 6, and the job
definition API starts in Part 7. Next.js begins in Part 4. The production image
will include its static export when frontend/backend integration is implemented.
Hosted provisioning and seven-day backup verification belong to Part 11.

## Production packaging

The selected deployment is one application Docker image containing FastAPI and
the Next.js static export. A Node.js build stage compiles the frontend; the final
runtime contains Python and the generated assets, with one Uvicorn process.
Keep the source directories and local development processes separate.

Production PostgreSQL and original documents stay in Neon, outside the application
container. Supply secrets at runtime and run database migrations once as a separate
release step. Local Compose keeps PostgreSQL in its own container and named volume.

The current image is the Part 3 backend scaffold. The combined frontend/backend
build will be added and tested in Part 9, before hosted deployment.
