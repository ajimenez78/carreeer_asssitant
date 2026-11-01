# MVP requirements and architecture

Status: Part 2 complete, 2026-11-01. The user selected Railway Free + Neon Free + direct OpenAI API calls and approved the product/source defaults. This is the implementation baseline; live inference/model evaluation and cloud provisioning remain in Parts 6 and 11.

## Confirmed baseline

- Deliver the job-definition MVP first, including later refinement through chat. Keep job discovery and the other career workflows for later phases.
- Use Next.js, Python/FastAPI, Railway hosting, Neon PostgreSQL/document storage, and the direct OpenAI API. Test the complete application locally before the Part 11 deployment.
- Support incomplete descriptions, optional background documents and links, clarification, compensation/work–life preferences, saving, and later refinement.
- Initially serve one private user. Public registration and multiple-user product flows are outside this initial scope.
- Keep planning and source examples in `doc/`. The execution checklist is [PLAN.md](PLAN.md).

## Approved product defaults

| Area | Agreed behavior |
| --- | --- |
| Access | One configured owner login over HTTPS on Railway; no public registration. Use a maintained authentication/session library and protect API and source-file access. Local development defaults to localhost. |
| Definitions | One current definition, updated in place. Incomplete drafts can be saved; no revision-history UI. Use a stable identifier so later phases can reference it. |
| Completion | A nonempty initial description is enough to save. Other fields may remain unknown; the owner chooses when the definition is ready and can revisit it. |
| Clarification | Ask at most three focused questions per round. Allow skip and “not sure.” Explain conflicts and ask before replacing accepted information. |
| Preferences | Separate mandatory constraints, preferences, and exclusions. Do not infer desired future responsibilities from every historical CV skill. |
| Compensation | Record currency, range or target, payment period, and gross/net basis when known. Ask what vague terms mean; never invent amounts. |
| Documents | Support text-based PDF, legacy `.doc`, `.docx`, and Markdown. Allow five documents per definition and 10 MB per document. Use bounded extraction/conversion; explain unsupported scanned PDFs and request a text-based alternative. OCR is deferred. |
| Links | Save provenance and attempt extraction from public HTTP(S) pages. For inaccessible LinkedIn or other restricted pages, offer document upload or pasted text. No authenticated scraping or LinkedIn account connection in this MVP. |
| Sources and deletion | Retain sources and extracted text until removed by the owner. Source deletion removes the original, extracted text, and source-derived background facts, and clears derived clarification/chat context so old snippets cannot re-enter AI prompts. Explain that effect before deletion; independently accepted job preferences remain. Allow deletion of the complete definition with its sources, answers, and conversation. Backup copies expire under the agreed retention policy. |
| Languages | English UI; accept English and Spanish descriptions/documents and clarify in the user's chosen language. |
| Saving | Explicit save/apply actions with visible unsaved state for definition edits. Create/save the initial draft before adding sources or requesting AI assistance. Source actions and submitted clarification answers/chat messages persist when the user performs those actions, independently of saving definition edits. AI suggestions are proposals until reviewed and applied; an AI or network failure preserves the existing draft and typed input. |

The salary target and the period of the example's two-day office limit are data the application should clarify. They are not hard-coded assumptions about future users or prerequisites for scaffolding.

## User interaction flow

1. Sign in and reopen the current definition, or start with a free-text description. Save an incomplete draft at any point after entering a description; save the initial draft before proceeding to sources or AI assistance.
2. Optionally attach documents and public URLs. Show each source's extraction status and a clear recovery action on failure.
3. Review extracted background facts and correct them before using them to clarify the ideal job. Keep source references with extracted facts.
4. Answer a small batch of targeted questions. A skipped answer remains unknown; a conflicting answer produces a reviewable correction.
5. Review an editable definition covering role/seniority, responsibilities and scope, technical interests, business/team context, compensation, location, remote/hybrid arrangement, hours/travel, and learning/work–life preferences.
6. Save accepted edits and supporting context. Reopen and refine the same definition later, including after application restarts.
7. In Part 10, discuss changes in chat. Display proposed changes to the definition, apply only reviewed changes, and keep structured editing and chat consistent.

## Acceptance criteria and design walkthroughs

These define future tests; no application tests have run during clarification.

| Scenario | Expected result |
| --- | --- |
| Supplied ideal-job description | Preserve Staff scope, system-wide architecture/design, cross-team work, continuous learning, international scope, and AI-engineering preference. Retain the exclusion of frontend-only roles. |
| Remote/hybrid preference | Preserve remote as preferred and Madrid or nearby as the constraint for hybrid work. Ask which period the two-day on-site limit covers before normalizing it. |
| “Good compensation” | Ask for the desired range, currency, period, and gross/net basis. Leave unanswered values unknown. |
| Description only: “I want a better software job” | Save a draft without demanding documents; ask about responsibilities/seniority, compensation, and work arrangement in manageable rounds. |
| Background documents | Extract supported files, show source provenance, allow corrections, and distinguish career facts from job requirements. Conflicting CV/profile facts are surfaced for review. |
| Unusable source | Corrupt/oversized/unsupported files, PDFs without text, or inaccessible links produce a useful message and upload/paste/retry path without clearing the draft. |
| AI failure or invented information | Reject invalid model output, preserve the accepted draft, and show a retry/edit path. Unprovided background facts must not become accepted claims. |
| Save → stop → restart → reopen → refine | Definition, accepted background, source references, and clarification answers survive; Part 10 conversation context also survives. |
| Source/definition deletion | Remove the agreed data consistently; ensure deleted source text is absent from subsequent AI context and that backup expiry matches the documented policy. |
| Chat refinement | A request such as changing hybrid availability produces a reviewable proposal; applying it updates the same definition used by the structured editor. |
| Private access | Unauthenticated requests cannot read or change the definition or retrieve uploaded documents. |

Nonfunctional targets and implementation limits:

- Show loading/error states immediately. Aim for non-AI reads/saves below one second when warm, excluding network latency; measure on the selected local/cloud setup.
- Target AI answers within 20 seconds for representative inputs, with a 60-second request timeout and preserved drafts on failure. Confirm feasibility in Part 6 rather than promise an unmeasured SLA.
- Bound document extraction and AI input/output sizes; reject excessive content with an actionable message rather than silently discard it. Set final extracted-text limits from parser/model measurements before accepting arbitrary uploads.
- Initially cap each AI call at 20,000 input tokens and 2,000 billable output tokens, including reasoning where applicable. Use low reasoning effort initially and evaluate quality in Part 6. Display incomplete/truncated output as an error or clarification need, not a completed definition.
- Run daily database/document backups with seven-day retention and a tested restore procedure. The application recovery target is one working day, with at most one day of lost writes; managed-provider outages can affect recovery availability. Implement the independent backup job in Part 11.
- Keep secrets and personal content out of logs and browser configuration. Normal automated tests use synthetic data and a fake AI client; live OpenAI checks are separate.

## Selected architecture

The user selected Railway + Neon + OpenAI on 2026-11-01. FastAPI, SQLAlchemy/Psycopg, Alembic, and the initial API below are the technical baseline for the approved flow. Earlier AWS/Lightsail/Lambda and Bedrock proposals are superseded; AWS credentials are no longer an MVP prerequisite.

| Component | Decision and rationale |
| --- | --- |
| Frontend | Next.js with TypeScript and static export. Keep `frontend/` separate for development; compile it in a Node.js Docker build stage and copy the generated assets into the Python runtime image. FastAPI serves them alongside `/api` on one production origin. Use a fixed editor route and avoid features requiring a runtime Next.js server. [Next.js static export](https://nextjs.org/docs/app/guides/static-exports). |
| API | FastAPI with Pydantic validation and generated OpenAPI schemas. Keep handlers, job-definition logic, and provider/storage adapters in one small backend. [Railway FastAPI deployment](https://railway.com/guides/fastapi), [FastAPI](https://fastapi.tiangolo.com/). |
| Database | PostgreSQL with SQLAlchemy, Psycopg, and Alembic migrations. Use local PostgreSQL via Docker Compose and managed Neon PostgreSQL in deployment. Select a current stable PostgreSQL major supported by Neon when implementing persistence. |
| Connections | Configure backend-only `DATABASE_URL` with TLS for Neon runtime access and a separate direct connection for migrations/backups where required. Keep connection counts bounded for this one-user application. [Neon connections](https://neon.com/docs/connect/connection-pooling). |
| Documents | Local private file storage for development and private Neon Object Storage for deployment, behind one small storage adapter. Keep metadata/extracted facts in PostgreSQL. Production filesystem contents are disposable; uploads must survive deployments. [Neon Object Storage](https://neon.com/docs/storage/overview). |
| Owner access | One configured owner, no public registration. Use a password hash and a maintained session mechanism; validate access on every private API/file operation. Keep session secrets backend-only, secure cookies in production, and origin/CSRF protection on cookie-authenticated writes. |
| AI | Official OpenAI Python SDK and Responses API, authenticated with backend-only `OPENAI_API_KEY`. Use the standard `https://api.openai.com/v1` endpoint and a fake client for routine tests. [Official Python SDK](https://developers.openai.com/api/reference/python). |
| Local workflow | Run PostgreSQL via Docker Compose, Python locally or in the backend container, and Next.js development tooling. Test the production image/static export locally before cloud deployment. Use isolated local databases and file directories for tests. |
| Railway deployment | Start with Free and one web service using the combined application image. Run one Python/Uvicorn process; Node.js is a build dependency, not a second production server. Use a version-controlled multi-stage Docker build, health route, and documented release commands; bind the server to the platform-provided port. Target 0.5 GB RAM and 1 vCPU per service. Enable sleeping/serverless mode, measure wake-up behavior, and choose an available EU region close to Neon. |
| Neon deployment | Start with Free while measured storage/compute/transfer fit the plan. Prefer Frankfurt because Neon Object Storage is supported there. Verify account availability and limits before provisioning; credentials are not needed for the local scaffold. |
| Backups | A daily Railway cron job exports PostgreSQL and copies source documents into a separate private Railway storage bucket, retaining seven daily copies. This separates backups from the Neon project and supports the approved seven-day policy. Test restoration of both database and files. |

Use the latest stable compatible library versions and lockfiles when each part is implemented. No scaffolding, dependency installation, or cloud provisioning is included in Part 2.

### Production packaging and release

The user explicitly selected the combined application option on 2026-11-01: separate frontend/backend source directories, one deployable application image, and externally managed persistence.

- Build the frontend with its Node.js toolchain and lockfile; copy only the static export into the final image containing locked Python runtime dependencies and the backend. Include neither development servers nor a runtime Node.js server.
- Extend the existing backend Dockerfile to use the repository-root build context during Part 9. Exclude `.env`, credentials, personal/example documents, Git data, caches, and test artifacts from the build context and final image.
- Keep production PostgreSQL in Neon and original uploads in private Neon Object Storage. Locally, PostgreSQL remains a separate Compose service with a named volume. Replacing the application image must not replace or delete persistent data.
- Supply database, storage, session, and OpenAI configuration at runtime. Run Alembic migrations once in a pre-deployment/release step, using the direct database connection where needed; do not run migrations independently in every web-server startup.
- Test the combined production image locally before release. Identify releases by Git revision and record the deployed image digest. Verify health and the real browser workflow after deployment.
- Keep application rollback and database recovery distinct. Prefer backward-compatible schema changes; rolling back an image does not undo a migration. Retain the approved daily database/document backups for seven days.

Current implementation: Part 3 supplies a backend-only image and the separate local PostgreSQL service. The Next.js scaffold is Part 4; building and testing the combined image is Part 9; hosted deployment is Part 11.

### Persistence and recovery details

- Neon Free currently includes 1 GB PostgreSQL storage, 100 CU-hours/project/month, and 5 GB object storage. These are quotas, not a guarantee that every future workload is free. Monitor compute, data transfer, and stored backups. [Neon pricing](https://neon.com/pricing).
- Do not equate the free database's instant-restore allowance with seven-day backups. The scheduled logical export and document-copy job explicitly implements that requirement. Storage credentials stay private and the backup job prunes copies older than seven days after a successful backup.
- Include a consistent source manifest with each database/document backup and verify restoration against disposable test data. Source deletion takes effect in the live application immediately; backup copies expire under the seven-day policy.
- Railway supports scheduled services and private object-storage buckets. Budget their usage along with the web service; the cron job exits after exporting and does not run as another always-on server. [Railway cron jobs](https://docs.railway.com/cron-jobs), [bucket billing](https://docs.railway.com/storage-buckets/billing).
- Keep local operation independent of Railway/Neon accounts. Validate adapters locally; exercise the real hosted database, storage, and backup path in Part 11.
- Include backup-job and bucket usage in the Railway Free budget, and verify those features are available to the actual account before deployment. If the approved seven-day backup policy cannot fit the free setup, report the evidence and options rather than silently omit backups or upgrade the plan.

### Railway Free operating constraints

- The ongoing Free plan includes $1/month of resource credit, up to 0.5 GB RAM and 1 vCPU per service. A new account's introductory $5 trial is temporary and must not be used to conclude that steady-state usage fits. [Railway pricing](https://railway.com/pricing), [plan details](https://docs.railway.com/pricing/plans).
- Use the single combined frontend/API service and Neon for durable data. Measure the complete monthly resource footprint, including scheduled backups, storage, and egress; free hosting is a target conditional on measured usage.
- Enable Railway's sleeping/serverless mode. It sleeps after roughly 5–10 minutes without outbound traffic; database connections, telemetry, or background requests can prevent sleep. Test cold-start recovery and preserve accepted data and submitted actions. [Railway serverless behavior](https://docs.railway.com/deployments/serverless).
- Measure document-conversion peak memory, especially legacy Word support, within the runtime limits. Keep the approved document formats; report a demonstrated resource mismatch before changing scope.
- If usage exceeds the ongoing allowance, report the measured bottleneck and alternatives. A paid upgrade is a separate user decision and must not happen automatically.

## Monthly cost estimate

Estimate date: 2026-11-01. USD before tax, one private user, light traffic, no separate always-on staging service. AI assumption: one million input tokens plus 200,000 billable output/reasoning tokens per month; this is not measured usage.

| Item | Monthly estimate or allowance |
| --- | ---: |
| Railway Free web service, backup jobs, and bucket usage within the ongoing $1 resource credit | $0 target |
| Neon Free PostgreSQL and private documents within included quotas | $0 |
| OpenAI `gpt-6-luna`, 1M input + 0.2M output at Standard rates | $0.20 |
| Working total if both hosting free tiers fit | $0.20 in metered AI usage |

Railway Free is the selected starting plan. Its ongoing $1/month resource allowance must cover the service, jobs, and storage together; it is not an unlimited always-on server. Neon must also remain within its free compute, storage, and transfer quotas. [Railway pricing](https://railway.com/pricing), [Neon pricing](https://neon.com/pricing).

This is a conditional free-hosting target, not a measured result or a guarantee. OpenAI API usage is billed separately; the $0.20 figure uses the token assumption above. Domain registration, taxes, higher usage, and any later paid provider plan are excluded. Configure usage monitoring and per-call token limits. Optimize and measure first; obtain the user's explicit choice before moving to paid hosting.

## OpenAI configuration, access, and model selection

Local checks on 2026-11-01 confirmed:

- `.env` has the correctly spelled `OPENAI_API_KEY`; `OPEAI_API_KEY` is not present. The key is never printed or copied into documentation.
- No `OPENAI_BASE_URL` override or Bedrock token remains in the file. Use the standard direct OpenAI endpoint.
- `.env` is ignored by Git.
- An authenticated read-only `GET https://api.openai.com/v1/models` returned HTTP 200 and listed `gpt-6-luna`.
- This establishes authentication/catalog access only. No inference request has been made; available credit, inference permissions, rate limits, output behavior, and task quality still need the Part 6 checks.

| AI task | Initial candidate | Part 6 selection check |
| --- | --- | --- |
| Background extraction from locally parsed text | `gpt-6-luna` | Preserve facts and source provenance without inventing employment or skills. |
| Clarification and structured definition suggestions | `gpt-6-luna` | Ask useful questions, preserve constraints, and leave unknowns unknown. |
| Open-ended refinement chat | `gpt-6-luna` | Return consistent, reviewable preference changes. |

Start with one configurable model. Increase reasoning effort or evaluate a stronger model only if representative quality tests show the need, recording the cost/latency tradeoff. Final task-level selection belongs to Part 6. GPT-6 Luna currently supports structured outputs and has Standard text rates of $0.10/1M input tokens and $0.50/1M output tokens. The example cost is $0.10 + 0.2 × $0.50 = $0.20. [Official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).

Billable output includes reasoning where applicable. Larger prompts, repeated documents, retries, and longer conversations increase usage. Track per-request tokens and cost estimates; do not expose keys to the frontend. Preserve the existing draft on authentication, quota, provider, or output-validation errors.

## Initial API contract

Use JSON for structured data and multipart form uploads for files. The API returns the server's validated saved representation after writes. Source text and chat context are authenticated backend data, never embedded in the static frontend build.

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Sanitized service health; no configuration details. |
| `POST /api/session`, `DELETE /api/session` | Owner sign-in/sign-out using the selected maintained session mechanism. |
| `GET /api/job-definition` | Read the current draft, structured preferences, clarification state, and source metadata. |
| `PUT /api/job-definition` | Create or save the current draft and user-reviewed edits; allow unknown optional fields. |
| `DELETE /api/job-definition` | Delete the definition and its agreed associated data. |
| `POST /api/job-definition/sources` | Add an uploaded document, public URL, or pasted source text; retain provenance and extraction status. |
| `GET`, `PATCH`, `DELETE /api/job-definition/sources/{source_id}` | Review/correct extracted background or remove a source. |
| `POST /api/job-definition/clarifications` | Return focused questions and proposed definition changes from the supplied description, reviewed context, and answers. Persist clarification context without applying unreviewed preferences. |
| `GET`, `POST /api/job-definition/chat` | Part 10 conversation retrieval and messages; return reviewable preference proposals. |

Definition fields follow the user-flow categories above; detailed relational columns and payload schemas are Part 5/7 work. Store background facts separately from preferences and represent unknown values explicitly. Manual and chat-approved updates use the same saving operation.

Errors follow `{"error": {"code": "...", "message": "...", "fields": {}}}` with appropriate HTTP status: validation (400/422), unauthenticated (401), absent data (404), excessive/unsupported uploads (413/415), unavailable/invalid AI responses (502/503), and timeout (504). Normalize framework errors to this contract; do not return secrets, raw provider errors, or document contents in diagnostics.

## Decision and completion record

- 2026-11-01: Part 1 approved; one private initial user confirmed.
- 2026-11-01: Railway + Neon + direct OpenAI selected, replacing AWS and Bedrock.
- 2026-11-01: The user explicitly selected Railway Free as the starting plan, with Neon Free and separately metered OpenAI calls. This supersedes the earlier Hobby estimate; paid hosting upgrades require a separate user decision.
- 2026-11-01: The user approved one combined application Docker image containing FastAPI and the static Next.js export, with PostgreSQL and documents managed separately in Neon.
- 2026-11-01: Product defaults approved: one current editable definition, explicit save/review, no revision history, English UI with English/Spanish content.
- 2026-11-01: Source defaults approved: text-based PDF, legacy Word, DOCX, Markdown; five files at 10 MB each; public-page retrieval with upload/paste fallback; no OCR initially; retain sources until removal; daily backups retained seven days.
- Part 2 is complete. No unresolved product or architecture question blocks Part 3. Exact salary/office-day periods are inputs for the application's clarification flow.
- Live model evaluation remains in Part 6. Railway/Neon account setup, hosted credentials, region availability, measured costs, and deployed backup verification remain in Part 11. These checks are not marked complete here.
