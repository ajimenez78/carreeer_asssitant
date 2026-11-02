# Railway + Neon release procedure

Prepared in Part 9; not executed. Deploy only after Parts 9–10 pass and the user
requests Part 11. Preserve the single combined-image architecture and private owner.

## Before provisioning

Confirm Railway/Neon accounts, an available EU location, Neon PostgreSQL and private
object-storage availability, and the ongoing Free allowances. Include web runtime,
backup jobs, seven-day independent backup storage and transfer in the budget;
introductory credits do not prove ongoing fit. Obtain an explicit user decision
before a paid upgrade. Actual bucket privacy, backup scheduling/restoration and
hosting configuration are Part 11 acceptance checks, not claims of this procedure.

Record the tested Git revision and built image identifier. Require a clean release
checkout and successful `make check`, `make integration`, `make frontend-check`,
`make frontend-contract`, `make frontend-e2e`, `make e2e`, and `make release-check`.
The live synthetic workflow is an explicit separate check, not a build/start hook.

## Build and runtime configuration

Keep the Railway service root at the repository root. Use `backend/Dockerfile`
with the root `.dockerignore`; do not change the service root to `backend/`.
The Dockerfile fixes frontend API configuration to same-origin `/api` and real mode.
Runtime secrets are never declared as Docker build arguments or frontend variables.
[Railway supports a custom Dockerfile path](https://docs.railway.com/builds/dockerfiles)
through `RAILWAY_DOCKERFILE_PATH=backend/Dockerfile`; version-controlled Railway
hosting configuration will be added in Part 11.

Use one Railway web service, one Uvicorn process, and the default image command.
It binds `0.0.0.0` and the runtime `PORT`. Set `/api/health` as the deployment
healthcheck. It is a public liveness check and does not establish database/provider
readiness; separately test authenticated persistence and inference.
[Railway healthchecks](https://docs.railway.com/deployments/healthchecks) gate rollout
but do not continuously monitor the service after activation.

Configure these backend runtime variables privately:

| Variable | Production value |
| --- | --- |
| `DATABASE_URL` | Neon PostgreSQL runtime URL with verified TLS; pooled URL if appropriate. |
| `DATABASE_DIRECT_URL` | Direct Neon URL for separate migrations/backups. |
| `CAREER_SESSION_SECRET` | Stable random secret of at least 32 characters, shared across image replacement. |
| `CAREER_SESSION_SECURE` | `true`. |
| `CAREER_ALLOWED_ORIGINS` | JSON array containing only the actual trusted HTTPS application origin. |
| `OPENAI_API_KEY` | Backend-only key for the selected account. |
| `CAREER_AI_MODEL` | Evaluated `gpt-6-luna`, unless a separately evaluated choice is approved. |
| `CAREER_AI_REASONING_EFFORT` | `low`. |
| `CAREER_AI_TIMEOUT_SECONDS` | At most 60. |
| `CAREER_AI_MAX_INPUT_TOKENS` / `CAREER_AI_MAX_OUTPUT_TOKENS` | At most 20,000 / 2,000. |
| `CAREER_DOCUMENT_BACKEND` | `neon`. |
| `CAREER_NEON_STORAGE_ENDPOINT`, `CAREER_NEON_STORAGE_REGION`, `CAREER_NEON_STORAGE_BUCKET` | Verified private bucket configuration. |
| `CAREER_NEON_STORAGE_ACCESS_KEY`, `CAREER_NEON_STORAGE_SECRET_KEY` | Backend-only bucket credentials. |

`CAREER_FRONTEND_DIRECTORY=/app/frontend` is supplied by the image. Do not store
production documents inside it or inside any application layer. The browser
contains public code and locale choice; private data and file operations require
an authenticated API session. Keep secure, HttpOnly, SameSite=Strict cookies and
exact-origin write enforcement. Do not solve CORS issues with wildcard credentials.

## Migration, owner initialization and rollout

1. Back up the current database and document manifest/originals to independent
   private storage before schema changes. Confirm recoverability and the target
   environment before executing a release command.
2. Run `python -m career_assistant.db_cli migrate` once as a separate release step,
   using the direct database URL where configured. It does not run on web startup.
   Repeating it preserves data and existing credentials.
3. On first installation only, configure the owner with
   `python -m career_assistant.db_cli owner` through a protected interactive command
   connected to the intended database. Do not put passwords in command arguments,
   deployment logs, or HTTP registration endpoints. Credential changes revoke sessions.
4. Deploy the exact locally tested revision/image. Record Git revision, image
   digest, deployment identifier and HTTPS URL. Keep the previous known-good image.
5. Check health, assets, private-route rejection without a cookie, correct/wrong
   login behavior, and a complete synthetic save → background → review → clarification
   → save → reload → refinement flow. Check a live bounded inference separately.
6. Replace/restart the application and verify the same saved identity, accepted
   preferences, source provenance and authenticated original downloads survive.
   Confirm files and SQL are external to the application.
7. Configure the seven-day daily independent backup/cleanup job, verify restoration
   against disposable data, and measure combined recurring usage. Verify sleeping
   and first-request recovery without duplicate writes. These remain Part 11 work.

A Railway [pre-deploy command](https://docs.railway.com/deployments/pre-deploy-command)
can provide the separate migration step if available on the chosen account. It runs
in a separate container with runtime variables, and a nonzero exit stops rollout.
It cannot rely on web-process startup or local volume state. Otherwise use a
protected one-off release command; never run migrations independently per replica.

## Rollback and recovery

If the new image fails smoke checks, select/redeploy the previous recorded image
with the same external database/document storage and stable session secret.
Application rollback does not undo schema changes. Prefer backward-compatible
migrations and prove compatibility before rolling an older image onto a newer schema.
If incompatible, stop writes and follow a separately tested database/document
recovery procedure instead of blindly running a downgrade.

Restore database and originals together from the verified manifest into isolated
replacement resources first. Verify identity, references, original checksums and
privacy before switching the application. Retain the old resources until recovery
is confirmed. Document backup retention, restore evidence and rollback outcomes in
Part 11; do not delete persistent resources as routine application cleanup.
