# Preview operational follow-ups

Baseline: the user's working-preview approval on **2026-11-03**. This tracker
extracts the accepted limitations from the
[completed MVP plan](../features/job-definition/PLAN.md). No new provider checks
were executed while reorganizing documentation or planning job finding.

These items remain operational work alongside feature development. They do not
reopen the approved MVP milestone or imply permission for paid resources.

| Follow-up | Recorded status | Completion evidence needed |
| --- | --- | --- |
| Preserve data before Free PostgreSQL expiration | Expires **2 December 2026 at 17:45 Madrid time** | Verified current export and a user-selected continuation or shutdown before expiration; no automatic paid upgrade |
| Observe daily automatic backup delivery | Workflow active and enabled; manual backup/restore passed; no scheduled run observed at the 3 November audit | A successful run whose trigger is the daily schedule, with archive verification and access cleanup; investigate delivery if it remains absent |
| Remaining account-wide usage and allowance checks | R2 usage measured and reported within included allowances; other totals remain incomplete | Render hours/bandwidth/build minutes, PostgreSQL storage/compute/transfer, GitHub Actions usage, and OpenAI usage/budget/alerts recorded against current allowances |
| Notification and alert confirmation | Render failure emails confirmed; Cloudflare lists no notification policies; other confirmations remain open | Cloudflare alert confirmation plus outstanding provider notification/budget settings; record limitations where access is unavailable |

GitHub billing still requires the missing `user` scope in the recorded audit.
Do not treat resource-level metrics as account-wide billing totals. Add the
job-finding workload to usage measurement before enabling its schedules.
Keep search scheduling and backup scheduling independently observable.

Supporting records: [deployment overview](OVERVIEW.md),
[operating runbook](DEPLOYMENT.md),
[preview validation](validation/PART11_VALIDATION.md),
[current recorded audit](evidence/PART11_FINAL_AUDIT.json),
[R2 completion](evidence/PART11_R2_COMPLETION.json), and
[R2 usage](evidence/PART11_R2_USAGE_CHECK.json).
