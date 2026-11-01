# Career assistant MVP plan

Status: Parts 1–6 are implemented and verified locally as of 2026-11-01. Earlier approvals are recorded below; the user explicitly authorized Part 6 only. Requirements/architecture are in [MVP_SPEC.md](MVP_SPEC.md), persistence in [PERSISTENCE.md](PERSISTENCE.md), AI evidence in [AI_EVALUATION.md](AI_EVALUATION.md), and setup commands in [README.md](../README.md). Part 7 is next; Parts 7–11 have not started.

## Scope and working rules

The MVP helps a user define, save, revisit, and refine an ideal job using their preferences and optional background documents or profile links. It covers responsibilities, scope, compensation, location, work arrangement, and work–life balance.

Job discovery, offer scoring, notifications, skill development plans, application tracking, interview preparation, and support after starting a job belong to later phases. Consider their relationships in the design without implementing their workflows or unused infrastructure.

- Keep the required Next.js frontend, Python backend, Railway hosting, Neon PostgreSQL/document storage, direct OpenAI API, and relational persistence.
- Follow the agreed Part 2 decisions in `MVP_SPEC.md`. Evaluate model suitability and live inference in Part 6; provision hosted services in Part 11.
- Follow the eleven parts in order. Complete each part's checks before marking its tasks done, and record relevant decisions or remaining blockers here.
- Part 1 approval and Part 2 requirement/architecture clarification are complete. Keep future changes consistent with the approved MVP scope.
- Keep planning documents and source examples together in `doc/`: [ideal job](ajimenez/MY_IDEAL_JOB.md), [CV](ajimenez/CV.pdf), and [LinkedIn export](ajimenez/Profile.pdf).
- Verify current stable library versions when adding dependencies, commit lockfiles, and keep the README's setup and test commands current and free of emojis.
- Prefer simple modules and meaningful tests. Aim for approximately 80% code coverage, prioritizing business logic and user workflows without tests written only to raise coverage.
- Use synthetic or redacted test fixtures. Keep credentials and personal document contents out of logs, committed fixtures, and test reports.
- Validate the complete MVP locally before deploying it to Railway and Neon in Part 11.

## Agreed user interaction flow

Part 2 defaults approved on 2026-11-01; detailed saving, source, and review behavior is recorded in `MVP_SPEC.md`:

1. Start an ideal-job draft with a free-text description, even if it is incomplete.
2. Optionally upload a CV or other background documents and add profile or personal-site links.
3. Review extracted background information and correct mistakes. Keep background facts separate from desired job preferences.
4. Answer focused clarification questions about missing or ambiguous preferences. Allow skipped questions and explicitly unknown values.
5. Review and edit a structured definition covering role, seniority, responsibilities, technical interests, company context, compensation, location, work arrangement, and work–life balance. Distinguish mandatory constraints from preferences.
6. Save the draft or completed definition, reopen it later, and refine it without losing previously accepted information.
7. In Part 10, use open chat to discuss preferences and review proposed changes through the same editing and saving flow.

The supplied ideal-job example is the reference acceptance scenario: preserve Staff scope, architecture and system design, collaboration across teams, learning, international scope, and an AI-engineering preference. Remote is preferred; hybrid is acceptable near Madrid with a two-day on-site limit whose period the application must clarify. Clarify “good compensation” rather than inventing a salary, and preserve the constraint against a role focused only on frontend work.

## Part 1: Define and approve the plan

Deliverable: this execution plan, with explicit scope, dependencies, validation, and completion criteria.

- [x] Read `AGENTS.md`, the original plan, and the supplied ideal-job, CV, and LinkedIn examples.
- [x] Expand all eleven parts into actionable checklists with tests and success criteria.
- [x] Record the proposed interaction flow, open decisions, and boundaries for later features and deployment.
- [x] Obtain user review and approval of this plan; incorporate requested changes before Part 2. Approved on 2026-11-01, including Part 11 and the `doc/` location.

Validation:

- [x] Check that every original part is represented, document links resolve locally, and only planning documentation has changed.
- [x] Check that pending decisions are clearly distinguished from approved requirements.

Success: achieved. The user approved Part 1 and explicitly requested Part 2 on 2026-11-01.

## Part 2: Clarify requirements and choose the architecture

Dependency: Part 1 approved.

- [x] Present concise proposals for the open decisions below, using the supplied examples; ask only questions that materially affect the MVP. See [MVP_SPEC.md](MVP_SPEC.md).
- [x] Confirm the interaction flow, required definition fields, draft/completion rules, and treatment of unknown or conflicting answers. The user approved the proposed product/source defaults on 2026-11-01.
- [x] Define functional and nonfunctional acceptance criteria, including upload limits, response-time targets, bounded AI usage, supported languages, and the approved backup retention.
- [x] Compare AWS Lambda and container hosting for the frontend, API, AI calls, and document processing. Include request duration, relational connections, operational effort, expected usage, and cost. Distinguish a Docker-based local setup from the cloud compute decision.
- [x] Select the Python framework, relational database, migration tool, local setup, and deployment/storage approach: FastAPI, SQLAlchemy/Psycopg, Alembic, local PostgreSQL via Compose, Railway, and Neon.
- [x] Resolve the AI provider requirement: the user explicitly selected the direct OpenAI API. A read-only authenticated model-catalog request returned HTTP 200 and listed `gpt-6-luna`; live inference, billing/quota behavior, and quality checks remain for Part 6.
- [x] Establish the initial API contract and error conventions for drafts, sources, clarification, and saving, consistent with the approved flow; refine payload and schema details in Parts 5 and 7.
- [x] Update `AGENTS.md` and this plan with approved requirements and decisions, keeping both concise.

| Decision | Agreed baseline |
| --- | --- |
| Users and access | One private user, one configured owner login, no public registration. |
| Definition lifecycle | One current definition; explicit saving/review; incomplete drafts allowed; no revision history. |
| Preferences | Mandatory/preferred/excluded criteria; structured compensation and work arrangement; unknown values stay unknown. The application clarifies sample-specific salary and office-day periods. |
| Documents | Text-based PDF, legacy `.doc`, `.docx`, and Markdown; five files at 10 MB each; no scanned-PDF OCR initially. |
| Links | Read public pages; provide upload/paste fallback; no authenticated scraping or LinkedIn account connection. |
| Data handling | Retain sources until removed; review extracted background before AI use; direct OpenAI calls receive the necessary reviewed text; daily backups retained for seven days. |
| Usability | English UI, English/Spanish content, small clarification rounds with skips and explicit unknowns. |
| Operations | Start on Railway Free and Neon Free; target $0 hosting within ongoing allowances, with metered OpenAI calls billed separately. Measure the web service, backups, storage, and transfer together. Paid upgrades require an explicit user decision. |

Validation:

- [x] Walk through the reference scenario and one incomplete-input scenario with the proposed flow. Expected outcomes are recorded in [MVP_SPEC.md](MVP_SPEC.md); these are design walkthroughs, not executed application tests.
- [x] Check that agreed requirements map to testable outcomes and that no unresolved design decision blocks scaffolding. Provider account setup and production credentials are deployment prerequisites, not local scaffold requirements.
- [x] Review hosting/model alternatives with the user and record their Railway + Neon + OpenAI selection.

Success: achieved. Requirements, user flow, architecture, acceptance criteria, and the initial API baseline are recorded; later-phase features remain outside implementation scope.

The user explicitly approved Part 2 and requested Part 3 on 2026-11-01.

Validation recorded on 2026-11-01: `.env` contains the correctly named `OPENAI_API_KEY`, has no Bedrock base-URL override, and is ignored by Git. Direct OpenAI model discovery returned HTTP 200 and listed `gpt-6-luna`. This proves read-only authentication/catalog access, not inference access, available credit, or model quality. No inference calls or cloud provisioning have been performed. The previous AWS authentication issue is superseded by the approved provider change.

## Part 3: Scaffold the backend and local infrastructure

Dependency: Part 2 decisions recorded.

- [x] Create `backend/` with FastAPI, `uv.lock`, environment-backed settings, Ruff, pytest/coverage, and Playwright tooling. Resolve current stable libraries when adding dependencies.
- [x] Separate settings, application construction, and HTTP routing; leave business logic for the job-definition implementation without adding empty layers.
- [x] Add `/api/health` and a packaged static “hello world” page that fetches the real API, displays the result, and supports retry after an error.
- [x] Provide development and Docker start/stop commands in the Makefile/README and a credential-free `.env.example`. Preserve the existing ignored `.env`.
- [x] Set up Docker Compose PostgreSQL with a named volume and localhost-only ports. Document local-to-Railway/Neon mapping; do not provision hosted services.
- [x] Measure the production scaffold container at approximately 48 MiB after smoke checks, with a 512 MiB memory limit and one CPU enforced. This excludes build tooling, development reload processes, and the separate local database; later document processing/full-MVP usage remains to be measured.
- [x] Create a concise README with prerequisites, configuration, setup, start/stop commands, tests, and scope boundaries.

Validation:

- [x] Run `make setup`, start `make dev BACKEND_PORT=8001`, check HTTP health, and verify graceful Ctrl+C shutdown. Build/start `make up`, verify packaged HTML and browser-to-API behavior, run SQL against PostgreSQL 18.6, exercise `make db-down`/`make db-up`, and finish with `make down` while retaining the database volume.
- [x] Run `make check`: Ruff passes and four in-process API/configuration tests pass with 100% coverage of the current 28 backend statements. Tests use no provider calls or external network services.
- [x] Run `make browser-install` and `make e2e`: two Chromium tests pass, covering a successful real API call and failure/retry recovery. Also check the built production container with Chromium.

Success: achieved. The documented setup starts/stops the local backend and database, and both development and packaged-container HTML-to-API checks pass. The test containers and development server were stopped after verification.

The user explicitly approved Part 3 on 2026-11-01.

Verification notes: local Python 3.14.8 and container Python 3.14.10; FastAPI 0.162.0 and Uvicorn 0.54.0 locked. This environment's sandbox stalls Starlette's TestClient thread portal, while the same tests pass unchanged outside it. Browser tests pass with one upstream pytest/Playwright fixture deprecation warning. No application changes were made to bypass these environment/tooling conditions. No inference calls or hosted deployment occurred.

## Part 4: Scaffold the frontend

Dependency: Parts 2–3 complete.

- [x] Create `frontend/` with current stable compatible Next.js, TypeScript, dependency lockfile, linting, and Playwright browser tooling.
- [x] Configure static export for the selected combined application image. Keep frontend development separate and avoid dependencies on a runtime Next.js server.
- [x] Add the application shell and a minimal entry page for the ideal-job workflow.
- [x] Set up environment-based API configuration without exposing backend, OpenAI, or Neon secrets to the browser.
- [x] Document frontend start/stop commands and how to run it alongside the backend.

Validation:

- [x] Run `make frontend-setup` from the lockfile and `make frontend-check`: ESLint, route-type generation, TypeScript checks, and the static production build pass.
- [x] Run `make frontend-browser-install` and `make frontend-e2e`: two Chromium smoke tests pass at desktop/mobile sizes, including keyboard skip navigation and horizontal-overflow/browser-error checks.
- [x] Run the existing `make check` regression checks: backend Ruff checks and all four API/configuration tests pass, retaining 100% coverage of the scaffold's 28 statements.
- [x] Open the entry page locally and verify that the development server stops cleanly. `make frontend-dev FRONTEND_PORT=3002` returns HTTP 200 and exits on Ctrl+C; the generated export also returns HTTP 200 and renders correctly in desktop/mobile Chromium through `make frontend-preview FRONTEND_PORT=3003`, with no browser errors or horizontal overflow. Both servers were stopped.

Success: achieved. The frontend runs locally and builds successfully; the job-definition UI remains for Part 8. The user authorized Part 4 on 2026-11-01; no later part or hosted deployment was started.

Implementation notes (2026-11-01): Next.js 16.4.3, React 19.3.1, ESLint 10.14.0, Playwright 1.64.1, and TypeScript 6.0.3 are locked. TypeScript 7.0.2 is newer but the current `typescript-eslint` explicitly rejects it (supported range `<6.1.0`). Use the current native Next.js and TypeScript ESLint plugins directly to avoid the incompatible legacy plugins in `eslint-config-next`. Frontend tooling requires Node.js 24 or newer. The optional `NEXT_PUBLIC_API_BASE_URL` is public and fixed at build time, defaults to `/api`, and is reserved for later API integration; the entry page makes no API calls and does not read the root backend `.env`.

Validation limitations: this sandbox suppresses stdout from Next.js's spawned TypeScript process, causing configuration parsing to fail; the unchanged checks pass outside the sandbox. Browser tooling emits harmless `NO_COLOR`/`FORCE_COLOR` environment warnings. `npm audit` reports 12 moderate development-tool findings derived from the transitive `minimatch` glob-amplification advisory (GHSA-g3hv-75wg-m249); current lint-tool dependencies do not provide a compatible fix. `npm audit --omit=dev` reports zero findings. No forced dependency upgrades or major-version overrides were applied. Recheck when updating lint tooling; frontend build tools are excluded from the eventual production runtime.

## Part 5: Design and implement MVP persistence

Dependency: approved requirements and working scaffolds.

The user explicitly approved Part 4 and requested Part 5 on 2026-11-01.

- [x] Propose the schema for one owner/current definition, sources, preferences, facts, and clarification questions/answers. See [PERSISTENCE.md](PERSISTENCE.md); conversation persistence remains Part 10.
- [x] Define stable UUIDs, keys, relationships, constraints, timestamps, and updates without revision history. Keep reviewed background separate and unknown values explicit.
- [x] Sketch relationships to later workflows without creating unused tables.
- [x] Review the schema against the approved interaction flow before adding migrations and persistence operations. Record the walkthrough and deletion effects in `PERSISTENCE.md`.
- [x] Provide repeatable local database creation/migration and unique disposable PostgreSQL test databases. Separate local initialization from migrations against an already provisioned hosted database.
- [x] Document private original-file storage versus SQL extracted/reviewed context and the retention/deletion rules.
- [x] Implement local/Neon document-store adapters and retryable original-file deletion. Define the backup manifest and restore contract; actual backup/restore verification remains Part 11.

Validation:

- [x] Create fresh disposable PostgreSQL databases, apply migrations, and verify repeated initialization preserves data and configured credentials. Run `make db-init` twice and `make db-migrate` against the development database.
- [x] Run Ruff and the combined unit/PostgreSQL suite: 41 tests pass with 99% statement coverage of the current 390 backend statements. `make check` and `make integration` also pass independently. Tests cover save/reload/refine, unknowns, reviewed facts, answer states, file limits, constraints, rollback, and deletion with cleanup failure/retry.
- [x] Verify a real `0001` → `0002` migration preserves the definition, preferences, and owner credentials; Alembic detects no schema drift. Enforce one owner/current definition in PostgreSQL. Authentication/session handling remains Part 7; no private HTTP routes are added here.
- [x] Build the backend image, run its packaged migrations, verify private document-volume read/write/delete and API health. Stop test services while retaining database/document volumes.

Success: achieved. The schema supports saved and revisable definitions and context through tested persistence operations and repeatable Alembic migrations.

Implementation notes (2026-11-01): SQLAlchemy 2.1.6, Psycopg 3.3.6, Alembic 1.20.1, and boto3/botocore 1.43.123 are locked; PostgreSQL 18.6 matches a Neon-supported major. Connections use bounded timeouts, hidden SQL parameters, and no idle application pool. Runtime and direct migration URLs remain backend-only. Imports do not open provider connections.

The two migration revisions establish the core schema and durable file-deletion queue. Source deletion removes source facts and derived clarification context transactionally while preserving accepted preferences. Original deletion runs after commit and remains queued after failure. Neon calls are tested with botocore stubs, including missing objects/provider errors; actual bucket privacy, deletion retention, hosted credentials, and backup/restore remain Part 11. No AI inference or cloud provisioning occurred. Database/container checks ran outside the sandbox's documented process/network restrictions; application code does not work around those tooling limits.

## Part 6: Verify OpenAI API connectivity and select models

Dependency: the direct OpenAI API is selected in Part 2; the backend and persistence are available. The user authorized completion of Part 6 only on 2026-11-01.

- [x] Add backend-only `OPENAI_API_KEY` settings and the fixed direct OpenAI endpoint. Preserve the ignored `.env`; never print or embed its key.
- [x] Implement an injectable `AIClient` protocol and official SDK boundary; normal tests use fake clients/transports.
- [x] Run the explicit live `2+2` test: validated structured answer 4, 3.875 s including preflight. See [AI_SMOKE.json](AI_SMOKE.json).
- [x] Evaluate the initial `gpt-6-luna` candidate at low reasoning on English/Spanish extraction, vague preferences, the reference scenario, and a targeted reviewable update. The final five cases pass; no stronger model was needed for this corpus.
- [x] Record model/endpoint/account prerequisites, limits, latency, usage, cost assumptions, and limitations in [AI_EVALUATION.md](AI_EVALUATION.md). Keep one configurable model for the evaluated tasks.
- [x] Validate strict structured output, count input before inference, cap input/output, and map access, quota, timeout, throttling, invalid/incomplete/refused output, and unavailable-model failures to sanitized errors.

Validation:

- [x] Ruff and the final combined unit/PostgreSQL suite pass: 78 tests, 99% statement coverage of 568 current backend statements. SDK transport tests verify strict JSON requests, token preflight, bounded output, no retries, timeout budgeting, error mapping, and usage/cost accounting without live AI.
- [x] Run and record the live arithmetic test separately. The final quality run has latencies of 1.973–4.456 s, 2,596 input/887 output tokens, and estimated inference cost $0.0007031. All 12 development generations together estimate $0.0016164; reports contain synthetic/sanitized data only.
- [x] Verify preservation of Staff scope, architecture, cross-team work, Madrid hybrid constraints, the two-day cap, remote/AI preferences, and the frontend-only exclusion; leave salary and the office-day period unknown and ask for clarification. Reject source-embedded commands in the extraction examples and retain source evidence.
- [x] Build the backend image and verify SDK/native imports and key-free application construction. No live AI calls are made during builds, startup, or routine tests. Stop local test services while retaining volumes.

Success: achieved for the bounded Part 6 evaluation. Direct OpenAI inference and token preflight work with the configured account; the initial model satisfies these synthetic quality/latency checks. Routine tests require neither credentials nor paid calls. Account balance/rate ceilings, maximum-document performance, and production reliability are not established by this small corpus.

An initial quality run and diagnostic reproduction showed that conditional hybrid limits were retained as text but incorrectly labelled preferred. The prompt now explicitly distinguishes hard conditions on a preferred alternative; the unchanged acceptance gates pass after this correction. Initial/final reports and the synthetic diagnostic are retained in `doc/`; no model or reasoning upgrade was needed. OpenAI SDK 3.42.0 is locked. API integration/document extraction/authentication remain Part 7, and hosted inference remains Part 11.

## Part 7: Implement the job-definition backend

Dependency: persistence and AI connectivity verified in Parts 5–6.

- [ ] Implement the agreed API for creating, reading, editing, and saving definitions and their clarification context.
- [ ] Implement approved document formats and extraction, retaining source provenance and allowing the user to correct extracted facts.
- [ ] Implement the agreed link behavior. If fetching public content, bound request duration and size and reject internal-network destinations, including redirects; provide a fallback when content cannot be accessed.
- [ ] Generate focused clarification questions and structured job-definition suggestions from user input and reviewed background information.
- [ ] Keep unknown values explicit, separate background facts from preferences, and distinguish mandatory constraints from preferences. Treat source documents as data, not instructions.
- [ ] Persist user-reviewed updates and allow later refinement; failed AI requests must preserve the existing draft and accepted information.
- [ ] Implement the approved source/definition deletion behavior, covering stored originals, extracted facts, derived clarification/chat context, and associated records consistently while preserving independently accepted preferences when removing a source.
- [ ] Validate inputs and uploads and return actionable errors. Apply the agreed access controls and local database initialization behavior.

Validation:

- [ ] Unit-test extraction, clarification, preference updates, validation, and AI failure paths with deterministic fixtures and a fake AI client.
- [ ] Test supported documents, malformed/oversized files, unsupported formats, PDFs without extractable text, and inaccessible links according to the agreed behavior.
- [ ] Measure extraction peak memory and CPU within Railway Free's runtime limits, including legacy Word files; preserve the approved formats and report any measured incompatibility.
- [ ] Run API/database integration tests covering create → add context → clarify → save → reload → revise, including failed writes and invalid AI output.
- [ ] Verify source and complete-definition deletion, including removal of deleted source content from future AI context.
- [ ] Check that the reference scenario preserves location/hybrid constraints and Staff scope, asks about compensation, and never converts every historical skill into a desired job requirement.
- [ ] Review meaningful coverage and address untested business behavior rather than adding tests solely for a percentage.

Success: the complete job-definition workflow works through the API with durable persistence and useful unit/integration coverage.

## Part 8: Build the frontend with mocked requests

Dependency: agreed API contract, backend behavior, and frontend scaffold available.

- [ ] Build the description, document/link input, background review, clarification, and structured definition editing screens.
- [ ] Support incomplete drafts, explicit unknowns, save/reopen/refine actions, and clear mandatory/preferred criteria.
- [ ] Use contract-compatible mocked requests for all workflow operations; do not connect this stage to the live backend.
- [ ] Implement loading, empty, validation, upload-error, and AI-error states while preserving typed input.
- [ ] Provide responsive layout, labeled controls, keyboard navigation, and visible feedback for saving and unsaved changes.

Validation:

- [ ] Run component and browser tests of the full mocked flow, including skipping questions, correcting extracted facts, saving, reloading, and refinement.
- [ ] Test representative failures and verify that recovery preserves user input.
- [ ] Run linting, type checks, and a production build; review usability at desktop and mobile widths.

Success: the agreed user journey is usable and tested entirely with API-compatible mocks.

## Part 9: Integrate frontend and backend

Dependency: Parts 7–8 complete.

- [ ] Connect the frontend API client to the real backend and isolate mock mode for tests/development.
- [ ] Extend the existing Dockerfile to build the frontend in a Node.js stage and copy its static export into a final Python image with the backend and locked runtime dependencies. Run one Uvicorn process serving assets and `/api`.
- [ ] Update the build context and Docker ignore rules for both source directories, excluding `.env`, personal/example documents, credentials, caches, and test artifacts. Keep PostgreSQL and documents outside the application image.
- [ ] Verify API configuration, upload handling, and the agreed authentication/CORS behavior across local frontend and backend origins.
- [ ] Run the complete flow against the real relational database and verify reopening persisted work after an application restart.
- [ ] Resolve integration failures from reproducible evidence and identified root causes.
- [ ] Update the README with one clean-checkout local setup and commands for starting, stopping, and testing the complete application.
- [ ] Document the cloud deployment procedure for Part 11 using the chosen architecture, including configuration, migrations, access controls, smoke checks, and rollback. Do not deploy during this local integration step.

Validation:

- [ ] Run browser end-to-end tests with the real frontend, backend, and database, using a fake AI client for deterministic automated runs.
- [ ] Cover initial description → upload/link → clarification → review → save → reload → refine, plus unavailable-AI and invalid-upload recovery.
- [ ] Perform an explicit live-OpenAI workflow check using synthetic data, separate from routine tests.
- [ ] Run the established backend/frontend checks and verify the documented setup from an empty local database.
- [ ] Run the combined release image locally with the separate Compose PostgreSQL service; verify frontend routes/assets, `/api` routing, same-origin sessions, and persistence across application replacement.

Success: the structured job-definition flow works locally across all layers and survives restarts; local validation evidence and deployment instructions are recorded.

## Part 10: Add open-ended assistant chat

Dependency: the integrated structured workflow passes Part 9.

- [ ] Add chat for free-text feedback and clarification within the current ideal-job definition.
- [ ] Reuse the same model client, clarification logic, preference validation, and persistence operations; avoid a separate agent architecture.
- [ ] Keep the conversation associated with the current definition and persist the context needed to resume it, according to the agreed retention rules.
- [ ] Show proposed preference changes for user review before applying them, and explain when additional clarification is needed.
- [ ] Keep this assistant within job definition; do not implement job search, applications, interviews, or career planning yet.

Validation:

- [ ] Unit-test chat interpretation, ambiguous/conflicting requests, invalid model output, and preservation of accepted preferences after failures.
- [ ] Run a browser test that changes an existing preference through chat, reviews and saves it, then reloads the updated definition and conversation.
- [ ] Check that chat and structured editing remain consistent and that unrelated requests do not mutate the definition.
- [ ] Run the established regression checks after chat integration and update the README.

Success: users can refine the same persistent definition through both structured interaction and open chat without losing accepted information.

## Part 11: Deploy the tested MVP to Railway and Neon

Dependency: Parts 1–10 complete, local acceptance checks passing, and the deployment procedure from Part 9 reviewed. Use the architecture selected in Part 2.

- [ ] Confirm Railway/Neon accounts, EU deployment locations, environment, resource changes, and estimated recurring usage. Start with Railway Free and Neon Free; verify available features and the ongoing $1/month Railway resource allowance separately from temporary trial credits.
- [ ] Add version-controlled Railway build/start/health configuration and repeatable deployment commands. Provision Neon PostgreSQL and private document storage with backend-only credentials.
- [ ] Configure HTTPS and the single-owner access model; keep OpenAI, database, storage, and session secrets out of browser assets, release images, and deployment output.
- [ ] Verify direct OpenAI inference from Railway and configure the Part 6 model identifiers and usage limits.
- [ ] Deploy the combined application image from the locally tested revision to one Railway web service. Record its Git revision and deployed image digest; Node.js is used only during the frontend build.
- [ ] Initialize Neon PostgreSQL independently of the web service and configure private Neon document storage and backend-only runtime connections. Back up existing data before schema changes, then apply Alembic migrations once in a separate pre-deployment/release step before rolling out the web process.
- [ ] Configure useful logs, health/error monitoring, usage alerts, and the daily database/document backup job with seven-day retention in independent private storage. Do not rely on Neon's free restore window to satisfy this policy.
- [ ] Enable and verify Railway's sleeping/serverless behavior to reduce idle usage. Avoid background traffic and unnecessary open connections that prevent sleep; verify first-request recovery without duplicate writes.
- [ ] Document redeployment, application rollback, database recovery, and resource cleanup, distinguishing disposable resources from persistent user data.
- [ ] Update the README with the deployed URL, release identifier, operational commands, and known limitations.

Validation:

- [ ] Run deployed frontend/API health checks and a live OpenAI smoke test.
- [ ] Run the deployed browser workflow using synthetic data: description → upload/link → clarification → review → save → reload → structured refinement → chat refinement.
- [ ] Verify HTTPS, authentication/access boundaries, production API/CORS configuration, and restricted database/document-storage access according to the approved design.
- [ ] Verify that saved definitions, background sources, and conversation context survive an application restart or redeployment.
- [ ] Verify that application image replacement and rollback preserve external database/document data; document database recovery separately from application rollback.
- [ ] Measure web-service, backup-job, storage, and egress usage against ongoing free limits, including the 0.5 GB RAM/1 vCPU runtime cap. Record projected monthly usage; if the complete MVP cannot fit, report the limitation and options before any paid upgrade.
- [ ] Check useful error reporting and exercise application rollback and database backup/recovery against disposable test data without affecting user data.
- [ ] Record the deployed revision, URLs, validation results, and any remaining operational limitations.

Success: the private MVP is accessible through Railway, persists data and documents in Neon, passes deployed acceptance checks, and has reproducible deployment and recovery.

## MVP completion

- [ ] All eleven parts have satisfied their checks; approvals and unresolved limitations are recorded accurately.
- [ ] The supplied scenario and agreed incomplete-input/error scenarios pass locally and on Railway/Neon with synthetic or redacted fixtures.
- [ ] Local setup, migrations, configuration, start/stop commands, tests, and Railway/Neon deployment/recovery commands are reproducible from the README.
- [ ] No later-phase workflow has been implemented merely to anticipate future requirements.
- [ ] Present the deployed MVP, validation results, operating instructions, and known limitations for review.
