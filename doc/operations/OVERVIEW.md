# Deployment summary

This is the approved job-definition preview. The planned
[job-finding feature](../features/job-finding/PLAN.md) is not deployed.
Outstanding checks are tracked in [operational follow-ups](FOLLOW_UPS.md).

Verified on 3 November 2026. The private MVP is live at
[career-assistant-jgpm.onrender.com](https://career-assistant-jgpm.onrender.com).
**Part 11 is complete and approved as a working preview on 3 November 2026.**
The user explicitly accepted the operational limitations below. The Cloudflare
permission, lifecycle and credential-isolation gaps have been resolved.

Render builds the tested Git revision
`9ee1e9306ad3a5ce1e4a97e46be5fcb71582b244` with
[`backend/Dockerfile`](../../backend/Dockerfile). The image combines the Next.js static
export with FastAPI; Node.js is used only during the build, and Python/Uvicorn
serves the interface and API from one HTTPS origin. One Free web service runs in
Frankfurt, with automatic deploys disabled. The current Render deployment is
`dep-dbkrhkff3r2c73fnuli0`, redeployed on 3 November to activate scoped storage
credentials while keeping the same tested source.

PostgreSQL 18 runs separately on Render's private network. Migrations ran before
deployment; the existing workspace, owner credentials and two originals were
migrated and verified. Documents remain in a private Cloudflare R2 Standard
bucket. Backend secrets stay outside the image, and the backend calls OpenAI
directly using `gpt-6-luna`.

GitHub Actions is configured for **03:17 UTC daily** (04:17 Madrid during this
preview), writing verified SQL/document archives to a separate private R2 bucket
and pruning archives after seven days. R2 now also enforces seven-day expiry on
the `career-backups/` prefix. Separate keys restrict the web app to document
read/write, the backup reader to document read-only, and backup writes to the
backup bucket. Cross-bucket rejection and read-only enforcement were tested.
The [backup with scoped keys](https://github.com/ajimenez78/carreeer_asssitant/actions/runs/41620465217)
succeeded, including temporary SQL-access cleanup. Previous local and hosted
restoration, restart, rollback and idle-recovery checks passed. Render failure
emails are enabled. The Free web service sleeps when idle; the measured wake-up
took about 33 seconds.

The deployed bilingual browser/API and original-download checks passed after the
credential rollout, preserving saved content and making no AI calls. Backup
archives are downloaded and checksummed; all 28 backup/access-helper unit tests
passed in the earlier audit. Cloudflare account billing reports R2 usage within
the included allowances and $0 in reported charges; provider metrics can lag.

Accepted limitations and operational follow-ups (not approval blockers):

- Remaining account usage, allowances and notification confirmation. GitHub
  billing access still requires the `user` scope; Render resource metrics do not
  establish account billing totals. Cloudflare returns no notification policies;
  its current token has notification read access only. OpenAI account budget and
  alert settings still need confirmation.
- A successful run triggered by the daily schedule. The workflow is active and
  enabled on `main`, but no scheduled run was recorded at this audit; the cause
  has not been established. A successful manual run does not verify scheduling.

The selected Free PostgreSQL preview expires on **2 December 2026 at 17:45 Madrid
time**. Export retained data before then; no paid upgrade is authorized.

See the [operating runbook](DEPLOYMENT.md), [validation record](validation/PART11_VALIDATION.md),
[R2 completion report](evidence/PART11_R2_COMPLETION.json), [R2 usage](evidence/PART11_R2_USAGE_CHECK.json)
and [current audit](evidence/PART11_FINAL_AUDIT.json) for commands and evidence.
