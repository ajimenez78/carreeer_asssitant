# Part 11: Render deployment preparation

Status on 2026-11-02: authorized and prepared locally; cloud release pending.
The user re-enabled Cloudflare backups on 2026-11-02, superseding the temporary
deferral. The daily schedule and `BACKUPS_ENABLED` guard are restored. Private
backup credentials, database access and a hosted backup/restore drill are again
required. The restored workflow is published on GitHub (`4719c55`), and its
syntax/schema validation passes. `BACKUPS_ENABLED=false` is configured until real
R2 credentials and a successful backup/restore check are available. No backup
has run.
The user subsequently replaced Neon with Render PostgreSQL. The abandoned CLI
setup is historical in [NEON_SETUP.md](NEON_SETUP.md); no Neon sign-in is needed.
The user replaced Railway with Render and selected free external backup scheduling
and private storage. The Free PostgreSQL 18 database is now provisioned in Frankfurt
(resource `dpg-dbkbsfc9v7es73cafmag-a`). It was created on 2 November 2026 at
17:45 Madrid time and expires on 2 December 2026 at 17:45 Madrid time. Its latest
provider status is `available`. No paid
plan or web service has been provisioned; no cloud backup has run. Details are in
[PART11_RENDER_PREVIEW.json](PART11_RENDER_PREVIEW.json).

## Prepared configuration and operations

- `render.yaml`: one Free Docker web service and one Free PostgreSQL 18 database
  in Frankfurt. The database URL is supplied through `fromDatabase`, with private
  network TLS required. Public database access starts blocked. Free Postgres
  expires after 30 days; the user explicitly selected this preview on 2026-11-02. The web
  service uses manual deploys, health checks and backend-only secrets. Validated against Render's current
  [official JSON schema](https://render.com/schema/render.yaml.json).
- Separate production preflight, migration, owner setup, backup and restoration
  commands. Startup requires the packaged migration head and an initialized owner;
  it does not migrate the database. Existing schema upgrades require a verified
  archive of the same database from the preceding 24 hours.
- Independent private backup storage with GitHub Actions scheduling at 03:17 UTC.
  The workflow requires `BACKUPS_ENABLED=true` and protected repository secrets;
  it publishes no private backup artifacts in this public repository.
- Snapshot-consistent SQL/original archives, checksums, bounded private temporary
  files, upload/readback verification and seven-day pruning. Failed publication
  leaves existing archives untouched. Configure storage lifecycle expiry as an
  additional backstop when creating the private bucket.
- Recovery requires an empty replacement database, refuses existing matching
  originals, restores SQL transactionally and removes newly copied originals if
  restoration fails. Remote recovery requires explicit selection and verified TLS.

The executable setup and recovery procedure is in [DEPLOYMENT.md](DEPLOYMENT.md).
The provider choice is Render web hosting + Render PostgreSQL, with GitHub Actions
and separate private R2 Standard buckets for originals and backups. The Neon
config/packages and local link were removed; existing secrets and remote projects
were not changed. The user explicitly selected the Free 30-day preview on
2026-11-02, accepting expiration. The reviewed alternative is `0.1c-256mb` at $6/month compute plus
$0.30/GB/month storage (about $6.30/month with 1 GB before tax/other usage). No paid
choice has been made. Actual account usage and eligibility remain to be checked.
[Render Free](https://render.com/docs/free),
[Render pricing](https://render.com/pricing),
[R2 pricing](https://developers.cloudflare.com/r2/pricing/).

## Local evidence

The post-switch unit/integration run passed **228 tests** in 29.56 seconds, with
**91% combined statement/branch coverage**. The focused configuration/storage/backup
suite passed **40 tests**. `npm run build` passed after Neon package removal.
Ruff lint/format and Git whitespace checks pass. Tests cover internal Render TLS
without weakening external TLS, R2-compatible storage settings, separate backup
buckets and recovery credential isolation. These are local tests and stubbed S3
transport; they do not prove a hosted service.
The rebuilt operations image also passed all six real PostgreSQL backup/recovery
integration tests in 2.94 seconds using its packaged PostgreSQL 18 client.

Before the latest provider switch, the combined application image passed the browser workflow and container replacement
check with 512 MiB memory and a 0.1 CPU cap. It preserved SQL, original documents,
owner/session data, accepted preferences, clarity summary/pause, and reviewed chat
refinement across replacement. The runtime remained Python-only and non-root;
private build inputs were excluded. See
[PART11_LOCAL_RELEASE_CHECK.json](PART11_LOCAL_RELEASE_CHECK.json).

Measured starts were 19.927 and 18.332 seconds; observed steady memory was
113.7 MiB of 512 MiB. The previous harness's approximately ten-second readiness
window was insufficient at the lower CPU cap: an isolated import took 16.501
seconds. The harness now permits 120 seconds and records actual startup times.
These are local container measurements, not hosted cold-start evidence.

The release browser harness uses injected synthetic AI in its first container;
its replacement uses the production runtime without the injection mount. Real
PostgreSQL and document parsing are exercised. This does not claim a live OpenAI
call, actual Render startup, or deployed authentication/security acceptance.

Backup/recovery tests exercise real disposable PostgreSQL databases and synthetic
originals. Checks cover snapshot restoration of application records, original
hashes, deletion/cleanup coordination, missing-original failure, owner preservation,
migration backup requirements, empty-target recovery and failure cleanup. S3
transport/retention tests use the SDK stubber; they do not access real Render/R2 services.

Reproduce the checks from the repository root:

```bash
make db-up
UV_CACHE_DIR=$PWD/.cache/uv uv run --project backend --locked pytest backend/tests --ignore=backend/tests/e2e --cov=career_assistant --cov-report=term -q
make operations-image
CAREER_BACKUP_TOOLS_IMAGE=career-assistant-operations:part11 UV_CACHE_DIR=$PWD/.cache/uv uv run --project backend --locked pytest backend/tests/test_backup.py backend/tests/integration/test_backup_recovery.py -q
CAREER_RELEASE_CPUS=0.1 make release-check
make lint
git diff --check
```

Browser tests run separately from unit/integration collection, as in the Makefile.
The unit chat test file was renamed to avoid its prior basename collision with
the integration chat tests; its behavior is unchanged.

## Remaining deployment work

Render API authentication is verified (HTTP 200), and GitHub CLI authentication
works. The Render plugin remains unconnected; the provided API key is the active
access method. The R2 endpoint and access-key fields in the private operations
file remain placeholders; actual storage authentication cannot be tested yet. The Free 30-day preview database plan
is already selected; no paid plan has been authorized. Configure private R2
originals and backup buckets with separate credentials. The current database deny-all external allowlist must
be reconciled with the trusted external migration/backup runner before activating
GitHub Actions; normal GitHub runner IPs vary. These are explicit deployment gaps.

After the R2 values are ready, finish provisioning only on the authorized plans,
initialize or migrate the intended private workspace, configure the owner without
overwriting existing data, deploy the exact tested revision and record its digest,
deployment ID and HTTPS URL. Then verify the deployed bilingual structured/chat
workflow, live synthetic inference, authentication/privacy, persistence, real
sleep/wake behavior, rollback and a hosted backup/restoration drill.

GitHub had no repository variables or secrets at inspection. Configure GitHub
secrets, the separate private backup bucket, lifecycle, failure
notifications and usage monitoring. Verify a manual backup/restore before setting
`BACKUPS_ENABLED=true` for the restored schedule. Measure actual
Render/PostgreSQL, GitHub, R2 and model usage against ongoing allowances. Any required
paid change must be presented to the user before proceeding. Part 11 remains open
until these hosted checks pass; [PLAN.md](PLAN.md) retains the unchecked tasks.
