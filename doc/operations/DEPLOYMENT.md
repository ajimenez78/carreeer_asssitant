# Render PostgreSQL deployment and recovery

For a short description of the running system and current acceptance status, see
[deployment overview](OVERVIEW.md). The user approved Part 11 as a working preview
on 3 November 2026, explicitly accepting the remaining account usage/notification
and automatic-schedule verification limitations as operational follow-ups.
The [3 November audit](evidence/PART11_FINAL_AUDIT.json)
confirms Render failure emails and live service health. The subsequent
[R2 completion check](evidence/PART11_R2_COMPLETION.json) verifies lifecycle expiry,
three scoped credentials and their deployment. [R2 account usage](evidence/PART11_R2_USAGE_CHECK.json)
fits the reported free allowances. Other provider usage/notification checks and
an observed scheduled backup remain outstanding. The schedule is configured,
but only manual runs have been observed. The instructions below remain the
operating procedure.

Track remaining checks and the preview-expiration deadline in
[operational follow-ups](FOLLOW_UPS.md). The [job-finding plan](../features/job-finding/PLAN.md)
does not change the deployed feature set or enable new schedules.

Part 11 was authorized on 2026-11-02. Render replaces Railway at the user's request.
The user re-enabled Cloudflare backups on 2026-11-02, superseding the temporary
deferral. Provision separate private original-document and backup buckets. The
workflow daily schedule is active, with `BACKUPS_ENABLED=true`, configured
credentials, temporary runner access and a verified backup/restoration.
The user selected a free external backup scheduler/storage option. Current setup:
Render Free web service, Render PostgreSQL, private R2 original storage, GitHub Actions
scheduling, and a separate private R2 backup bucket. Neon is no longer used.
The user explicitly selected the Free 30-day PostgreSQL preview on 2026-11-02,
accepting its expiration. Keep the declared Free plan; no paid upgrade is authorized.
The free database was created on 2 November 2026 at 17:45 Madrid time and expires
on 2 December 2026 at 17:45 Madrid time. The app is live at
https://career-assistant-jgpm.onrender.com and daily GitHub backups are enabled. Export
any workspace to retain before expiration. See [PART11_VALIDATION.md](validation/PART11_VALIDATION.md)
and [resource details](evidence/PART11_RENDER_PREVIEW.json).

## Accounts and release prerequisites

Add the Render integration or configure authenticated Render tooling privately.
A Cloudflare R2 account/bucket and scoped storage credentials are also needed.
No Cloudflare integration was found in the available plugin search; use private
local settings or the provider dashboard for those credentials. Do not paste them
into chat, source files, build arguments, workflow YAML, or committed artifacts.

Confirm the actual free plans, existing account usage, and EU placement before
provisioning. Use Frankfurt for Render web and PostgreSQL; choose an EU jurisdiction for R2
if available to the account, and use its corresponding S3 endpoint. Keep R2
Standard storage private: no public development URL or custom public domain.
[Render compute](https://render.com/docs/compute-plans),
[Render Postgres](https://render.com/docs/postgresql-creating-connecting),
[R2 bucket creation/privacy](https://developers.cloudflare.com/r2/buckets/create-buckets/).

Prepare a clean tested release commit. Record its full Git SHA, built image digest,
Render deployment ID and HTTPS URL. The database is provisioned, but local test
images are not hosted web release identifiers. Record the exact Git revision
when deploying the web service.

## Backend-only configuration

`render.yaml` declares exactly one `plan: free` Docker web service in Frankfurt,
using `backend/Dockerfile` with repository-root build context. Render serves the
static frontend and FastAPI from one origin; Node.js remains build-only. Automatic
deploys are off to preserve the external migration → rollout sequence. A Free
PostgreSQL 18 instance is declared and connected via `fromDatabase`. No
disk, cron job, or paid resource is declared. Database public access starts blocked
with `ipAllowList: []`. Do not apply this preview blueprint expecting permanent
free storage. For an explicitly approved paid database, change its plan to
`0.1c-256mb` and set `diskSizeGB: 1` before applying; estimated database cost is
$6/month compute plus $0.30/GB/month storage, before taxes and other usage.
[Compute plans](https://render.com/docs/compute-plans),
[storage pricing](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).

Provide the prompted runtime secrets through Render's protected environment UI:

| Setting | Value |
| --- | --- |
| `DATABASE_URL` | Automatically supplied by the blueprint from Render Postgres over the same-region private network. The backend requires TLS (`sslmode=require`) internally because Render uses self-signed internal certificates. For external operations use the public hostname and `sslmode=verify-full` with trusted roots. |
| `CAREER_SESSION_SECRET` | Blueprint-generated stable secret, retained across restarts/rollbacks. Do not regenerate it on routine deploys. |
| `CAREER_SESSION_SECURE` | `true`. |
| `CAREER_ALLOWED_ORIGINS` | Normally omit: `operations serve` derives the exact HTTPS origin from Render's `RENDER_EXTERNAL_URL`. For custom domains, explicitly set a JSON array containing only trusted HTTPS origins without paths. |
| `OPENAI_API_KEY` | Existing direct OpenAI backend key, kept private. |
| `CAREER_DOCUMENT_BACKEND` | `s3`. |
| `CAREER_S3_ENDPOINT`, `CAREER_S3_REGION`, `CAREER_S3_BUCKET` | Private R2 originals bucket; signing region `auto`. Use the actual jurisdiction endpoint. |
| `CAREER_S3_ACCESS_KEY`, `CAREER_S3_SECRET_KEY` | Bucket-scoped R2 credentials. Web uploads need read/write/delete access to originals only; use a separate read-only originals credential for backups. |
| AI settings | Existing `gpt-6-luna`, low reasoning, 60-second timeout, 20,000 input/2,000 output caps. |

The image supplies `CAREER_FRONTEND_DIRECTORY=/app/frontend`. It contains no `.env`,
private originals, keys, or database files. Database and source credentials are not
frontend settings. Render's startup command is `python -m career_assistant.operations serve`.
It checks security configuration, migration head and configured owner before serving;
it never runs migrations. The public health route remains sanitized `/api/health`.
[Blueprint reference](https://render.com/docs/blueprint-spec),
[Render TLS modes](https://render.com/docs/postgresql-creating-connecting),
[R2 S3 credentials](https://developers.cloudflare.com/r2/api/s3/api/).

If the existing local workspace should become the hosted workspace, export its
actual SQL/originals, verify the archive, and restore it into empty replacement
resources first. Preserve the existing owner hash and accepted data; do not run
`owner` again unless intentionally changing credentials. Confirm the source document
store (development directory or Compose volume) before exporting. A missing original
aborts the backup rather than publishing an incomplete migration artifact.

## Separate release and owner initialization

Render Free does not support the paid pre-deploy command, shell, or one-off jobs.
Run release/owner commands from a protected local or CI operations runner before
triggering the web deployment. Keep migration credentials out of the Render build.
[Render deploy phases](https://render.com/docs/deploys), [Free limitations](https://render.com/docs/free).

Create ignored mode-600 `.env.operations.local` with a **direct** `DATABASE_URL`
and `DATABASE_DIRECT_URL` pointing to the intended Render PostgreSQL database, verified TLS,
read-scoped R2 original-storage settings, and backup settings below. An empty
new database needs no prior backup. For an existing schema change, first make a
completed verified backup of this same database; release rejects missing, foreign,
older-than-24-hour, or invalid selected backup archives.

```bash
make operations-image
# Open access from this runner and retain its private cleanup state.
mkdir -p .cache/render-maintenance
docker run --rm --user "$(id -u):$(id -g)" --env-file .env.operations.local --mount "type=bind,source=$PWD/.cache/render-maintenance,target=/maintenance" career-assistant-operations:part11 python -m career_assistant.render_access open /maintenance/access.json
# Empty database initialization, or repeatable migration check at current head:
docker run --rm --env-file .env.operations.local career-assistant-operations:part11 python -m career_assistant.operations release
# Before a schema change on an existing database:
docker run --rm --env-file .env.operations.local career-assistant-operations:part11 python -m career_assistant.operations backup
# Use the completed key printed in the safe completion record:
docker run --rm --env-file .env.operations.local career-assistant-operations:part11 python -m career_assistant.operations release --backup-key career-backups/TIMESTAMP-ID.zip
# First installation only: enter the owner password interactively.
docker run -it --rm --env-file .env.operations.local career-assistant-operations:part11 python -m career_assistant.db_cli owner
# Always close runner access, including after a failed operation.
docker run --rm --user "$(id -u):$(id -g)" --env-file .env.operations.local --mount "type=bind,source=$PWD/.cache/render-maintenance,target=/maintenance" career-assistant-operations:part11 python -m career_assistant.render_access close /maintenance/access.json
```

External maintenance uses `career_assistant.render_access` to add only the runner's
IPv4 /32, preserving other entries. The GitHub workflow supplies encrypted
`RENDER_API_KEY` and repository variable `RENDER_POSTGRES_ID`; its always-run cleanup
removes only its own rule. The database returns to an empty public allowlist while
the app keeps using Render's private network. Force-cancelled runners may need
operator cleanup of their uniquely labeled `career-maintenance-*` entry.

For local maintenance, use the operations image with a writable private state mount
and the host UID, just as the workflow does. Open access before release/backup;
close it after the operation. The private operations file includes the database ID.
Keep the state file for cleanup if an API call times out. Database TLS remains
`verify-full`; the backend resolves `system` trust to an explicit available CA
bundle because binary Psycopg can use a different OpenSSL trust location.

Passwords never appear in command arguments. Repeating `release` preserves existing
owner credentials and data. Deliberately rerunning `owner` changes credentials and
revokes sessions. Do not overwrite an existing private environment file.

Create the Render service from `render.yaml` and configure the prompted secrets.
The existing preview was created through the Render API and is not Blueprint-managed.
Deploy updates on the existing service ID recorded in `PART11_RENDER_PREVIEW.json`.
Trigger a manual deployment of the tested commit after release/owner setup.
For subsequent releases: back up → migrate separately → deploy that commit → smoke
test. Keep the previous compatible commit/image available for rollback. Initial
Blueprint creation can trigger a deployment; startup will fail safely if schema
or owner prerequisites are not ready yet.

## Daily independent backups

Current state: `BACKUPS_ENABLED=true`; GitHub-hosted backups and real restoration
passed. On 3 November, three distinct bucket-scoped keys were installed and
verified: web document read/write, CI document read-only, and backup archive
read/write. The backup prefix has a verified seven-day lifecycle rule in addition
to worker pruning. The operator `CARREER_CLOUDFARE_TOKEN` manages bucket settings;
the application/CI object keys intentionally lack management access. The setup
instructions below describe how to reproduce or replace this configuration.

In Cloudflare, open **R2 → backup bucket → Settings → Object Lifecycle Rules →
Add rule**. Enable object deletion after seven days for prefix `career-backups/`
and save. Apply this to the backup bucket; originals remain until explicitly
deleted. Cloudflare's default seven-day multipart-upload cleanup is a different
rule and does not expire completed backup archives.
[Cloudflare lifecycle setup](https://developers.cloudflare.com/r2/buckets/object-lifecycles/).

Create bucket-scoped R2 tokens with these permissions, keeping the existing token
valid until the replacements have been verified:

| Use | Permission and bucket | Private destination |
| --- | --- | --- |
| Web documents | Object Read & Write; originals bucket only | Operations `CAREER_S3_ACCESS_KEY` / `CAREER_S3_SECRET_KEY`, then the web service's matching settings. |
| Backup document reads | Object Read only; originals bucket only | GitHub `DOCUMENT_BACKUP_ACCESS_KEY` / `DOCUMENT_BACKUP_SECRET_KEY`. |
| Backup archive writes/pruning | Object Read & Write; backup bucket only | Operations `CAREER_BACKUP_ACCESS_KEY` / `CAREER_BACKUP_SECRET_KEY`, then GitHub `BACKUP_ACCESS_KEY` / `BACKUP_SECRET_KEY`. |

R2 tokens are created under **R2 → Account Details → API Tokens → Manage**.
Select the intended bucket when assigning object permissions. Lifecycle management
belongs in the dashboard; application credentials need only object access.
[Cloudflare R2 token setup](https://developers.cloudflare.com/r2/api/tokens/).

Create a dedicated private R2 Standard bucket. Configure a seven-day object lifecycle
expiry on the dedicated `career-backups/` prefix as a backstop if the scheduler stops.
Use bucket-scoped write/list/delete credentials on the backup runner, separate from
the web service credentials. Supply originals-only credentials to the web app;
keep backup bucket credentials on the operations runner. The former shared-key
limitation was resolved on 3 November; preserve the same separation when rotating
credentials.

External operations settings:

```text
CAREER_BACKUP_ENDPOINT=https://ACCOUNT_ID.r2.cloudflarestorage.com
CAREER_BACKUP_REGION=auto
CAREER_BACKUP_BUCKET=career-assistant-backups
CAREER_BACKUP_ACCESS_KEY=<private bucket-scoped access key>
CAREER_BACKUP_SECRET_KEY=<private secret>
CAREER_BACKUP_PREFIX=career-backups/
```

For an EU-jurisdiction bucket, use its actual EU endpoint rather than the example.
The account's ongoing free allowance is shared with other workloads; verify remaining
capacity and notification settings. [R2 pricing](https://developers.cloudflare.com/r2/pricing/).

`.github/workflows/daily-backup.yml` schedules the job at 03:17 UTC and also supports
manual dispatch. It retains read-only repository permissions, pinned checkout,
a 15-minute timeout and no pull-request trigger. The job executes only when the
repository variable `BACKUPS_ENABLED=true` is set. Before activation, configure
these Actions secrets and validate the database network access:

- `RENDER_API_KEY` and repository variable `RENDER_POSTGRES_ID` (temporary runner access).
- `BACKUP_DATABASE_DIRECT_URL` (external Render URL with verified TLS).
- `DOCUMENT_STORAGE_ENDPOINT`, `DOCUMENT_STORAGE_BUCKET`, `DOCUMENT_BACKUP_ACCESS_KEY`,
  `DOCUMENT_BACKUP_SECRET_KEY` (separate R2 read-only original access).
- `BACKUP_ENDPOINT`, `BACKUP_BUCKET`, `BACKUP_ACCESS_KEY`, `BACKUP_SECRET_KEY`.

The public repository contains only code. The job does not upload SQL/originals
as GitHub artifacts or log their contents; archives go directly to the private bucket.
The runner builds the operations image without secrets, then passes credentials
by environment names only. Enable normal GitHub workflow-failure notifications;
verify a manual run and its private object before enabling the daily schedule.
Public repositories' schedules can stop after prolonged inactivity and can be
delayed: monitor successful completion independently and keep an operator reminder
to check daily recovery points. Do not use the sleeping web service as a scheduler.
[GitHub scheduling](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule).

Each archive contains a custom-format SQL dump, manifest, and confirmed originals.
The worker locks the owner/definition/cleanup rows, exports one PostgreSQL snapshot,
and captures original bytes before releasing locks; existing app mutations coordinate
through those same rows. Cleanup cannot remove a required original during capture.
The archive uses private temporary files, bounded streaming and a 512 MiB archive cap.
It verifies every checksum locally, uploads with a transport checksum, downloads
and verifies it again, then prunes recovery points seven days old or older.
Failed exports/uploads/readback do not prune old backups. Job records include only
completion/failure, bytes, count, elapsed time and an object key.

## Restore into replacement resources

Use trusted archives only: SQL backups are executable database input. Retrieve the
chosen archive privately from the R2 dashboard or `BackupBucket.download` through
the protected operations environment. Never publish a backup link or its contents.

Create an empty replacement database and a separate empty originals destination.
Use a distinct `CAREER_RESTORE_DATABASE_URL` variable. For hosted originals configure
`CAREER_RESTORE_S3_ENDPOINT`, `_REGION`, `_BUCKET`, `_ACCESS_KEY`, and
`_SECRET_KEY`; the `_S3_` prefix here expands as normal environment names,
for example `CAREER_RESTORE_S3_SECRET_KEY`. These must reference the
replacement database/bucket, not the live source.

```bash
# Mount a private backup directory as /recovery; the archive itself stays private.
docker run --rm --env-file .env.recovery.local --mount type=bind,source=/ABS/PRIVATE/BACKUPS,target=/recovery,readonly career-assistant-operations:part11 python -m career_assistant.operations restore /recovery/backup.zip --allow-remote
```

Remote recovery requires explicit `--allow-remote` and verified TLS. Local rehearsals
can use `--documents-directory /path/to/empty-originals`. Restoration validates all
entries and checksums before writing, rejects an occupied database or matching
originals, restores SQL transactionally and cleans newly copied originals if restore
fails. Validate accepted preferences, source hashes/provenance, owner/session data,
summary/pause, and conversation before changing the web app's connection settings.
Keep old resources until recovery is confirmed. Perform this drill against disposable
resources, not the owner's live data.

## Rollback, smoke checks and quotas

An image rollback uses the previous recorded compatible commit with unchanged
external Render PostgreSQL/R2 resources and stable session secret. It does not reverse migrations.
For an incompatible schema, stop writes and restore SQL/originals into replacement
resources first. Never blindly downgrade or delete persistent resources during cleanup.

Run hosted acceptance for each release: health/assets; unauthenticated rejection;
secure HttpOnly session; exact-origin writes; bilingual saved-draft → document/link
→ reviewed background → clarification/summary → reviewed save → reload → structured
refinement → floating chat → reviewed chat save; bounded live synthetic inference;
restart/redeploy and rollback persistence; private original retrieval; backup/restore;
and real sleep/wake behavior. Use synthetic data in disposable branches/environments.
Do not replace existing user work with a smoke-test definition. Completed checks
for this preview are in [PART11_VALIDATION.md](validation/PART11_VALIDATION.md).

Render Free supplies 512 MB / 0.1 CPU and 750 workspace instance-hours/month, sleeps
after 15 idle minutes, and may take about a minute to wake. It has no durable local
disk. Measure cold recovery without keepalive pings. Render's included bandwidth/build
quotas and external-traffic policies also apply. Monitor actual workspace usage;
no paid upgrade is authorized. Render PostgreSQL storage/compute/transfer, GitHub runner usage,
and R2 storage/operations must remain within their ongoing allowances as well.
[R2 Standard](https://developers.cloudflare.com/r2/pricing/) includes 10 GB-month;
seven maximum 512 MiB archives require roughly 3.5 GiB before other account usage.
Daily external database transfer still depends on actual SQL/original bytes and is not proven
free solely by that storage calculation.
