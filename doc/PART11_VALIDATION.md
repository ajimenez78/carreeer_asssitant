# Part 11: Render preview and daily backups

Status on 2026-11-02: the Free preview is live at
[career-assistant-jgpm.onrender.com](https://career-assistant-jgpm.onrender.com).
Daily backups are enabled and the first GitHub-hosted run succeeded. Final
acceptance gaps are listed below; Part 11 is not marked fully complete.

## Deployed resources

The app and PostgreSQL 18 use Render Free in Frankfurt. The database expires on
**2 December 2026 at 17:45 Madrid time**, as explicitly accepted by the user.
Original documents and backups use separate private R2 buckets. No paid Render
resource was created. The deployed source is `9ee1e9306ad3a5ce1e4a97e46be5fcb71582b244`,
with deployment `dep-dbkc9lks728c73cohtng`. Automatic web deploys are off.
[Resource IDs, URL, usage and configuration](PART11_RENDER_PREVIEW.json).

The user explicitly approved transferring the existing local workspace, owner
password hash and two uploaded documents to Render/R2. The source workspace was
preserved. All database rows and all 184,269 document bytes matched after transfer.
Existing login credentials remain valid; no owner password was reset.

## Verification

| Check | Evidence |
| --- | --- |
| Complete unit/integration regression | 232 passed in 26.81 seconds; 90% statement/branch coverage. |
| Required root build | `npm run build` exited 0: TypeScript finished, static pages generated (3/3), `/` and `/_not-found` prerendered. |
| Combined production image and browser/replacement flow | Passed at 0.1 CPU / 512 MiB. Starts: 19.737 and 19.037 seconds; measured memory 114.1 MiB. [Local release report](PART11_LOCAL_RELEASE_CHECK.json). |
| Deployed protected API and originals | Authenticated reads and both original downloads passed; unauthenticated reads rejected. |
| Deployed security | Untrusted Origin rejected; Secure/HttpOnly/SameSite=Strict cookies and session revocation verified. |
| Deployed bilingual UI and assistant | Language switch persists after reload; floating assistant is available at every step; unsent input survives minimizing and navigation. No automatic AI requests; saved content unchanged. [Deployed report](PART11_DEPLOYED_CHECK.json). |
| Hosted live AI workflow | Synthetic upload/extraction, fact review, proposal/save, explicit reassessment and Spanish chat passed through a temporary Free service and isolated database schema. Four real model calls; idempotent retry reused the result. Temporary service/schema/originals removed; real workspace unchanged. [Live AI report](PART11_LIVE_AI_CHECK.json). |
| Real SQL/original backup and recovery | Downloaded the cloud archive, restored into disposable local PostgreSQL/files, and compared every row/file and owner hash. Temporary recovery resources removed. [Recovery report](PART11_CLOUD_BACKUP_CHECK.json). |
| GitHub-hosted backup | [Run 41488898644](https://github.com/ajimenez78/carreeer_asssitant/actions/runs/41488898644) passed export, upload/readback, pruning and temporary-access cleanup. 216,255-byte archive with two originals; 21.525-second backup operation. |
| Database network boundary | GitHub removes its own temporary rule. With public access closed, the app still reads SQL through Render's private network. Operator verification sessions were revoked. |
| Hosted restart persistence | Render restart returned 200; health, identical saved workspace and the existing signed session passed afterward. Verification session revoked and maintenance access closed. [Restart report](PART11_RESTART_CHECK.json). |

The deployed read check uses a short-lived operator-created session, not a reset
owner password. It performs reads, one invalid-origin request and logout; it does
not save changes or call AI. Reproduce it using
`CAREER_DEPLOYED_URL=https://career-assistant-jgpm.onrender.com uv run --project backend --locked python backend/tests/deployed_read_check.py`
with browser dependencies, private operator settings and temporary SQL access.

Two initial smoke-check assertions were corrected in the harness: await saved-data
hydration, and use the existing browser suite's language-switch selector. No
product workaround was needed.

The root build initially failed inside the execution sandbox: Node emitted
`Failed to create stream fd: Operation not permitted` before TypeScript's
`--showConfig` JSON, which Next.js could not parse. Running the same build outside
that restriction passed without code changes. The Docker production build passed
as well.

The synthetic hosted AI check also initially expected an assessment to survive a
changed criteria save. The application correctly invalidated it. The harness
explicitly requested reassessment and verified the saved criteria separately.
Usage was recorded for the final two calls only; their estimated $0.00037386 is
not the total cost of all four calls.

## Backup operations

`BACKUPS_ENABLED=true` and encrypted GitHub secrets are configured. The schedule
is **03:17 UTC daily**, which is **04:17 Madrid time during this preview**. No SQL
or original files are published as GitHub artifacts. Archives are private and
checksummed, downloaded for verification before pruning, and retained seven days.
The workflow opens only its runner's IPv4 /32 and closes that rule in an always-run
cleanup step; other operator rules are preserved. State files contain no API key.

The operations image contains Python 3.14 and PostgreSQL 18 tools. Both the access
helper and backup worker run in that image, avoiding runner Python-version drift.
The first live checks diagnosed two infrastructure differences before fixing them:
Psycopg's bundled OpenSSL trust path differed from Python's valid system trust
store, and dual-stack IP discovery returned IPv6 while Postgres traffic used IPv4.
The backend now chooses an explicit available CA bundle while keeping
`sslmode=verify-full`, and maintenance IP discovery selects IPv4.

Measured application usage: PostgreSQL 8,599,231 bytes, originals 184,269 bytes,
and two backup archives totaling 432,510 bytes. These application measurements fit
the intended allowances; other workloads in the user's accounts were not audited.

## Remaining acceptance and provider setup

- R2 rejected lifecycle configuration with `403 AccessDenied` for the supplied
  S3 keys. The running backup job performs seven-day pruning. Configure an
  additional seven-day expiry rule for `career-backups/` in the backup bucket's
  dashboard so expiry also works if the job stops.
- The supplied document and backup access keys are identical. Functional checks
  passed; create separate bucket-scoped credentials and a read-only originals
  credential for CI to finish the intended credential isolation.
- Finish actual sleep/wake observation, redeploy/rollback checks and account-wide
  quota/notification verification. SQL/original recovery was proven from the real
  cloud archive into disposable local resources; a hosted recovery drill remains.
- Record Render's built image digest if exposed; the local tested image digest
  is in the local release report and is not claimed to be Render's image digest.

The operational procedure is [DEPLOYMENT.md](DEPLOYMENT.md). The original abandoned
Neon setup remains historical in [NEON_SETUP.md](NEON_SETUP.md).
