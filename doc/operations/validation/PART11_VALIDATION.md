# Part 11: Render preview and daily backups

## Preview approval on 2026-11-03

The user explicitly approved the working preview with the remaining limitations
accepted. **Part 11 is complete for this approved preview scope.** Remaining
account usage/allowance and notification checks, including Cloudflare budget/alert
confirmation, and proof of a successful automatic scheduled backup are operational
follow-ups rather than approval blockers. Manual backups and restoration are
verified; approval does not establish that automatic scheduling has run.

The Free PostgreSQL expiration remains 2 December 2026 at 17:45 Madrid time.
No paid upgrade or broader credential access is authorized by this approval.
The audit sections below retain the evidence and status at the time of each check.
See [deployment.md](../OVERVIEW.md) for the approved deployment description.

## R2 setup completed on 2026-11-03 after the permission update

The updated `CARREER_CLOUDFARE_TOKEN` now permits the required account operations.
This section supersedes the initial Cloudflare blockers recorded below.

- Configured and read back a seven-day (`604800` seconds) object-deletion rule
  for `career-backups/` in the backup bucket. Existing multipart-cleanup rules
  were preserved; originals have no new expiry rule.
- Created three distinct account-owned, bucket-scoped credentials: document
  read/write for the web app, document read-only for the backup runner, and
  backup-bucket read/write for archive creation/pruning. All permitted operations
  passed; each credential rejects the other bucket, and the reader rejects
  uploads. Synthetic probe objects were removed. Newly created credentials
  initially returned `Unauthorized` until propagation completed; the same
  unchanged policies and keys then passed.
- Installed the scoped credentials in Render, encrypted GitHub secrets and the
  private ignored operations settings. The original shared token remains only
  for operator account management; it was not revoked because it is also the
  user's configured management credential. No token values are recorded here.
- Redeployed tested source `9ee1e9306ad3a5ce1e4a97e46be5fcb71582b244` as
  `dep-dbkrhkff3r2c73fnuli0`. It became live at 10:35:48 UTC on 3 November.
  Deployed browser/API, bilingual UI, floating-chat preservation, original
  downloads, origin protection and session revocation all passed afterward.
  Saved content was unchanged, no AI was called, and the operator session and
  temporary network rule were removed.
- [Backup run 41620465217](https://github.com/ajimenez78/carreeer_asssitant/actions/runs/41620465217)
  succeeded with the scoped credentials, including temporary SQL-access cleanup.
- Account-wide R2 metrics, GraphQL operations and billing are now accessible.
  Billing reports 36 Class A and 56 Class B operations and
  `0.000020577866666666668` GB-months for the reported 2 November period, each
  with $0 charges. The month-to-date analytics query returned 132 requests.
  These reported totals fit the ongoing Standard allowances; provider metrics
  lag recent operations and do not establish other providers' allowance usage.
- Cloudflare notification-policy listing now works and returns no policies.
  The token has `Notifications Read`; alert setup/dashboard confirmation remains
  open. GitHub billing still requires the missing `user` scope. No scheduled
  backup run has been observed; all successful runs so far were manual.

Evidence: [R2 configuration/rollout](../evidence/PART11_R2_COMPLETION.json),
[R2 account usage](../evidence/PART11_R2_USAGE_CHECK.json),
[current audit](../evidence/PART11_FINAL_AUDIT.json) and
[short deployment description](../OVERVIEW.md). The remaining account
usage/notification and scheduled-delivery checks were subsequently accepted as
preview limitations in the approval recorded above.

## Initial completion audit on 2026-11-03, before the permission update

At this initial audit, Part 11 remained open: the outstanding provider permissions
were checked again. The later permission update and preview approval are recorded
above. A short description of the deployed system is in
[deployment.md](../OVERVIEW.md); the detailed operating runbook remains
[DEPLOYMENT.md](../DEPLOYMENT.md).

- The Free web service is live on the same verified `9ee1e93` release. HTTPS
  health and interface requests return 200; unauthenticated workspace reads
  return 401. PostgreSQL is available and its public IP allowlist is empty.
- The deployed browser/API check passed again: authenticated workspace/original
  reads, bilingual UI, persistent floating assistant and typed input, origin
  rejection, secure cookies and session revocation. No saved content changed and
  no AI call was made. The verification session and temporary network rule were
  removed. See [deployed report](../evidence/PART11_DEPLOYED_CHECK.json).
- All 28 existing backup and temporary-access unit tests pass.
- A fresh manually dispatched
  [backup run 41615710497](https://github.com/ajimenez78/carreeer_asssitant/actions/runs/41615710497)
  passed, including its always-run temporary database-access cleanup.
  Its 216,220-byte archive passed all checksums after download; both originals
  matched live R2 storage, and the temporary downloaded copy was removed. Three
  archives now total 648,730 bytes; originals remain 184,269 bytes. This verifies
  current application storage, not account-wide storage or operation totals.
- Render workspace failure emails are enabled; the web service inherits that
  setting. GitHub/Cloudflare notification and account-wide allowance confirmation
  remain outstanding.
- Cloudflare account-token verification succeeds, but token-detail, bucket-list,
  lifecycle and notification-policy requests return 403. S3 lifecycle access also
  returns `403 AccessDenied`. Originals and backup credentials are still shared.
  Account-level access or dashboard changes are needed to complete isolation and
  the lifecycle backstop; current object access is sufficient for backups only.
- The current GitHub billing-usage endpoint returns 404 and explicitly requires
  the missing `user` scope. No credentials or scopes were changed.
- The backup workflow is active on the default `main` branch, repository Actions
  are enabled, and `BACKUPS_ENABLED=true`. However, GitHub reports **zero runs
  triggered by `schedule`**. The schedule is configured, but automated delivery
  is not verified. No scheduler-delivery diagnostic is available in these checks;
  its cause remains unresolved. The fresh manual run establishes backup-worker
  functionality only.

[Current provider/backup audit](../evidence/PART11_FINAL_AUDIT.json). The previously verified
recovery, rollout and live-AI reports below remain evidence for those checks;
this audit did not repeat inference or replace the deployed application.

## Previous deployment evidence

Status on 2026-11-02: the Free preview is live at
[career-assistant-jgpm.onrender.com](https://career-assistant-jgpm.onrender.com).
Daily backups are enabled and the first GitHub-hosted run succeeded. Final
acceptance gaps were still open at that time. The later preview approval and its
accepted limitations are recorded at the top of this document.

## Deployed resources

The app and PostgreSQL 18 use Render Free in Frankfurt. The database expires on
**2 December 2026 at 17:45 Madrid time**, as explicitly accepted by the user.
Original documents and backups use separate private R2 buckets. No paid Render
resource was created. The deployed source is `9ee1e9306ad3a5ce1e4a97e46be5fcb71582b244`,
with current deployment `dep-dbkcr8d9fdbs73c20he0` after the verified rollback.
Automatic web deploys are off.
[Resource IDs, URL, usage and configuration](../evidence/PART11_RENDER_PREVIEW.json).

The user explicitly approved transferring the existing local workspace, owner
password hash and two uploaded documents to Render/R2. The source workspace was
preserved. All database rows and all 184,269 document bytes matched after transfer.
Existing login credentials remain valid; no owner password was reset.

## Verification

| Check | Evidence |
| --- | --- |
| Complete unit/integration regression | 232 passed in 26.81 seconds; 90% statement/branch coverage. |
| Required root build | `npm run build` exited 0: TypeScript finished, static pages generated (3/3), `/` and `/_not-found` prerendered. |
| Combined production image and browser/replacement flow | Passed at 0.1 CPU / 512 MiB. Starts: 19.737 and 19.037 seconds; measured memory 114.1 MiB. [Local release report](../evidence/PART11_LOCAL_RELEASE_CHECK.json). |
| Deployed protected API and originals | Authenticated reads and both original downloads passed; unauthenticated reads rejected. |
| Deployed security | Untrusted Origin rejected; Secure/HttpOnly/SameSite=Strict cookies and session revocation verified. |
| Deployed bilingual UI and assistant | Language switch persists after reload; floating assistant is available at every step; unsent input survives minimizing and navigation. No automatic AI requests; saved content unchanged. [Deployed report](../evidence/PART11_DEPLOYED_CHECK.json). |
| Hosted live AI workflow | Synthetic upload/extraction, fact review, proposal/save, explicit reassessment and Spanish chat passed through a temporary Free service and isolated database schema. Four real model calls; idempotent retry reused the result. Temporary service/schema/originals removed; real workspace unchanged. [Live AI report](../evidence/PART11_LIVE_AI_CHECK.json). |
| Real SQL/original backup and recovery | Downloaded the cloud archive, restored into disposable local PostgreSQL/files, and compared every row/file and owner hash. Temporary recovery resources removed. [Recovery report](../evidence/PART11_CLOUD_BACKUP_CHECK.json). |
| GitHub-hosted backup | [Run 41488898644](https://github.com/ajimenez78/carreeer_asssitant/actions/runs/41488898644) passed export, upload/readback, pruning and temporary-access cleanup. 216,255-byte archive with two originals; 21.525-second backup operation. |
| Database network boundary | GitHub removes its own temporary rule. With public access closed, the app still reads SQL through Render's private network. Operator verification sessions were revoked. |
| Hosted restart persistence | Render restart returned 200; health, identical saved workspace and the existing signed session passed afterward. Verification session revoked and maintenance access closed. [Restart report](../evidence/PART11_RESTART_CHECK.json). |
| Hosted redeploy and rollback | Deployed documentation/test commit `a72b01d`, then rolled back to release `9ee1e93`. Existing session, saved workspace and both original downloads stayed identical after each operation. [Rollout report](../evidence/PART11_ROLLOUT_CHECK.json). |
| Hosted SQL/original recovery | Restored the verified archive into a disposable database on the existing Free Render instance and temporary originals in the private backup R2 bucket. All nine business/owner tables and both originals matched; transient sessions excluded from live comparison. Recovery database and objects removed. [Hosted recovery report](../evidence/PART11_HOSTED_RECOVERY_CHECK.json). |
| Automatic Free idle recovery | After 17 minutes without application requests, the first authenticated read returned 200 in 32.920 seconds. Startup-complete log at 18:11:38 UTC confirms the wake-up. Saved workspace and session survived; no saved writes or AI calls issued. [Idle recovery report](../evidence/PART11_IDLE_RECOVERY_CHECK.json). |

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
Render resource samples recorded a maximum 140,034,050 bytes of web memory and
67,227,650 bytes of database disk usage, including provider/system overhead.
The reported bandwidth sample is 1.2003765 MB. These are sampled resource metrics,
not a monthly account billing total. GitHub billing usage returned 404 and reported
that the existing token lacks the `user` scope. R2 S3 keys do not grant account
metadata access. No credentials were broadened. [Usage report](../evidence/PART11_USAGE_CHECK.json).
The first GitHub backup run lasted 65 seconds and its timing endpoint reported
zero billable Ubuntu milliseconds; this does not audit other account usage.

## Accepted operational follow-ups, updated 2026-11-03

- R2 lifecycle expiry, separate scoped credentials and R2 account usage are now
  verified, as recorded in the update at the top of this document. Object-only
  keys intentionally cannot manage lifecycle rules; use the operator API token.
- Finish the remaining account-wide quota/notification verification. Render
  resource metrics do not establish billing totals; GitHub billing requires
  `user` scope, Cloudflare returns no notification policies, and OpenAI account
  budget/alert settings need confirmation.
- Observe a successful scheduled backup. The default-branch workflow is active
  and enabled; manual runs succeed, but the schedule has not produced an
  observed run. The cause is not established.

Render's public deployment response does not expose an image digest. The tested
local image digest is recorded separately; the hosted release is identified by its
full Git SHA and Render deployment ID.

The operational procedure is [DEPLOYMENT.md](../DEPLOYMENT.md). The original abandoned
Neon setup remains historical in [NEON_SETUP.md](../../archive/NEON_SETUP.md).
