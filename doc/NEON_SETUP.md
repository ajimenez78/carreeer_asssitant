# Neon setup

Historical record, superseded on 2026-11-02: the user selected Render PostgreSQL
instead of Neon. Neon is no longer an application dependency; `neon.ts` and the
root Neon packages were removed, and the local link was archived privately.
No Neon cloud resources were provisioned or deleted. The sign-in request below
is obsolete. Current setup is in [DEPLOYMENT.md](DEPLOYMENT.md).

## Initialization

The first sandboxed install attempt also failed DNS resolution (`ENOTFOUND`);
normal network access resolved that limitation before the global permission error.
The requested global installation failed with `EACCES` creating
`/usr/local/lib/node_modules/neon`. The requested fallback succeeded:

```text
$ npx --yes neon@latest --version
8.16.0
```

The requested initialization ran from the project root:

```bash
npx --yes neon@latest init -y --org-id org-patient-cake-83718400 --project-id wild-dew-59977193 --branch production --services postgres,object-storage
```

It installed Neon agent tooling, created the ignored `.neon` link and `neon.ts`,
and installed locked root configuration dependencies. Its account result was:

```text
Linked .neon
  Project         wild-dew-59977193
  Branch          production
  Org             org-patient-cake-83718400

Written offline (--no-checks): nothing was verified.
```

`neon.ts` declares the private `assets` bucket; PostgreSQL is built into the
project. The generated `auth: false` declaration was removed so this setup does
not request changes to an unrelated Neon Auth service. The app keeps its existing
owner login. Existing branch tuning is unchanged.

The original `.env` was preserved in an ignored, mode-600 private backup before
initialization. Its existing API key and settings remain unchanged. Raw CLI logs
are private and ignored because future environment output may contain secrets.

## Environment and drivers

The installed `neon`, `neon-postgres`, and `neon-object-storage` skills were read.
They recommend preserving established drivers/ORMs and using direct connections
for migrations and dumps. This app keeps Python SQLAlchemy/Psycopg and boto3 in
the FastAPI backend; no database or storage credentials enter the frontend.

| Neon CLI variable | App use |
| --- | --- |
| `DATABASE_URL` | Runtime PostgreSQL, including pooled connections. |
| `DATABASE_URL_UNPOOLED` | Direct migration/backup connection; explicit legacy `DATABASE_DIRECT_URL` takes precedence. |
| `AWS_ENDPOINT_URL_S3` | Private Neon storage endpoint. |
| `AWS_REGION` | Storage signing region. |
| `AWS_ACCESS_KEY_ID` | Backend-only storage access key. |
| `AWS_SECRET_ACCESS_KEY` | Backend-only storage secret. |

Existing `CAREER_NEON_STORAGE_*` overrides remain supported. Settings load `.env`
and then `.env.local`, preserving unrelated values. Neon database connections use
certificate/hostname verification with system trust roots. The S3 client retains
required path-style addressing and SigV4.

After a successful deploy/pull, select `CAREER_DOCUMENT_BACKEND=neon` and
`CAREER_NEON_STORAGE_BUCKET=assets` privately in the app environment. These two
app-specific values are not emitted by Neon. They have not been activated yet,
because no storage credentials have been pulled and existing local use is preserved.

References: [connection choices](https://neon.com/docs/connect/choose-connection),
[pooling](https://neon.com/docs/connect/connection-pooling),
[Object Storage setup](https://neon.com/docs/storage/get-started).

## Executed checks

`npm run build` from the project root succeeded after running outside the sandbox:

```text
> career-assistant@0.1.0 build
> npm --prefix frontend run build
✓ Compiled successfully in 76ms
  Finished TypeScript in 1470ms ...
✓ Generating static pages using 4 workers (3/3) in 240ms
Route (app)
┌ ○ /
└ ○ /_not-found
○  (Static)  prerendered as static content
```

The first sandboxed attempt failed with `Could not parse output from TypeScript's
--showConfig`. An isolated reproduction returned zero stdout bytes in the sandbox;
the same helper returned 2,743 valid JSON bytes outside it. No TypeScript checks
were disabled. Setting the frontend's explicit Turbopack root also removes the
new root-lockfile ambiguity while preserving the separate frontend build.

Starting the built app with `npm start -- --port 8011` succeeded:

```text
Application startup complete.
Uvicorn running on http://127.0.0.1:8011
GET /: HTTP 200
GET /api/health: HTTP 200
{'status': 'ok'}
GET /api/session: HTTP 401
```

These checks prove local frontend/API startup and unauthenticated rejection. They
do not exercise cloud persistence: the app still has its pre-existing local settings.
The focused configuration/database/storage/backup suite passed 38 tests; Python
lint/format and frontend ESLint passed. `neon.ts` also loads successfully.
The final unit suite passed: `151 passed in 2.00s`. The local PostgreSQL integration
suite passed: `75 passed in 28.93s`. An earlier sandboxed unit
run stalled and was stopped; the normal rerun completed successfully.
The operations image was rebuilt with the new mappings. A regression test confirms
recovery uses explicitly configured replacement credentials and cannot fall back
to the live `AWS_*` settings.

## Authentication failure and remaining work

The requested `npx --yes neon@latest deploy` attempted browser authentication:

```text
Awaiting authentication in web browser.
ERROR: Authentication timed out after 60 seconds
```

No deployment or environment pull completed, and no PostgreSQL/Object Storage
end-to-end cloud check has passed. The CLI's active profile still reports no
account and a missing credentials file. The user was asked to run:

```bash
npx neon@latest login
```

After sign-in, retry deployment against the pinned project/branch, confirm the
project's storage-supported region and free-plan allowances, and verify pulled
environment keys without displaying values. Inspect existing database contents
before migrations or data transfer; preserve existing owner credentials and data.
Initialize/migrate via the existing release command, activate the two app-specific
storage settings, restart the app, and exercise authenticated save/reload and
document upload/download/delete against the real services. Use disposable test
resources to protect production user content and remove only the generated test
data. Record actual cloud evidence here before marking Neon setup complete.
