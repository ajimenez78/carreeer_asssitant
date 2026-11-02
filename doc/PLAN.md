# Career assistant MVP plan

Status: Parts 1–10 are implemented and verified locally; Parts 8–9 were completed on 2026-11-02. The user explicitly approved Part 7 on 2026-11-01 and Parts 8–9 on 2026-11-02; earlier approvals are recorded below. The user subsequently requested system-assessed clarity, stoppable iteration, and a natural-language summary; this structured-workflow extension is tracked below and in [CLARITY_SUMMARY.md](CLARITY_SUMMARY.md), separately from historical Part 9 evidence. Requirements/architecture are in [MVP_SPEC.md](MVP_SPEC.md), persistence in [PERSISTENCE.md](PERSISTENCE.md), AI evidence in [AI_EVALUATION.md](AI_EVALUATION.md), and setup commands in [README.md](../README.md). Part 7 evidence and payloads are in [PART7_VALIDATION.md](PART7_VALIDATION.md) and [BACKEND_API.md](BACKEND_API.md). Part 8 evidence and mock limitations are in [PART8_VALIDATION.md](PART8_VALIDATION.md). Part 9 evidence is in [PART9_VALIDATION.md](PART9_VALIDATION.md); the release procedure is in [DEPLOYMENT.md](DEPLOYMENT.md). Part 10 chat was authorized and completed on 2026-11-02; see [PART10_VALIDATION.md](PART10_VALIDATION.md). Part 10 is approved; Part 11 is authorized and in progress. Local deployment/recovery preparation is recorded in [PART11_VALIDATION.md](PART11_VALIDATION.md); the Free Render preview is live, the approved workspace is migrated, and daily cloud backup/restoration is verified. Remaining acceptance/provider items are recorded below.

On 2026-11-02, the user replaced Railway with Render and subsequently replaced Neon with Render PostgreSQL. Use private R2 buckets for originals and separate backups, with external GitHub Actions scheduling. The user explicitly selected the Free 30-day PostgreSQL preview on 2026-11-02, accepting its expiration. No paid resources are authorized. Earlier Railway/Neon decisions below are historical; the current Part 11 checklist supersedes them.

Current preview scope update, 2026-11-02: the user re-enabled Cloudflare backups, superseding the temporary deferral. Daily GitHub Actions backups are active, and a real archive has passed restoration and row/file comparison. Separate buckets work with the supplied shared key; credential isolation and the additional R2 lifecycle backstop remain pending.

The abandoned Neon CLI setup remains a historical record in [NEON_SETUP.md](NEON_SETUP.md). No Neon sign-in is needed. Current Render configuration and remaining access requirements are in [PART11_VALIDATION.md](PART11_VALIDATION.md).

## Scope and working rules

The MVP helps a user clarify, save, revisit, and refine the role they are looking for using their preferences and optional background documents or profile links. It covers responsibilities, scope, compensation, location, work arrangement, and work–life balance.

Frontend wording, updated at the user's request on 2026-11-02, frames this as clarifying the role the user is looking for. English and Spanish headings, navigation, description labels, and page metadata follow that framing; the existing workflow and API terminology remain unchanged.

Job discovery, offer scoring, notifications, skill development plans, application tracking, interview preparation, and support after starting a job belong to later phases. Consider their relationships in the design without implementing their workflows or unused infrastructure.

- Keep the required Next.js frontend, Python backend, Render hosting/PostgreSQL and private R2 document storage, direct OpenAI API, and relational persistence.
- Follow the agreed Part 2 decisions in `MVP_SPEC.md`. Evaluate model suitability and live inference in Part 6; provision hosted services in Part 11.
- Follow the eleven parts in order. Complete each part's checks before marking its tasks done, and record relevant decisions or remaining blockers here.
- Part 1 approval and Part 2 requirement/architecture clarification are complete. Keep future changes consistent with the approved MVP scope.
- Keep planning documents and source examples together in `doc/`: [ideal job](ajimenez/MY_IDEAL_JOB.md), [CV](ajimenez/CV.pdf), and [LinkedIn export](ajimenez/Profile.pdf).
- Verify current stable library versions when adding dependencies, commit lockfiles, and keep the README's setup and test commands current and free of emojis.
- Prefer simple modules and meaningful tests. Aim for approximately 80% code coverage, prioritizing business logic and user workflows without tests written only to raise coverage.
- Use synthetic or redacted test fixtures. Keep credentials and personal document contents out of logs, committed fixtures, and test reports.
- Validate the complete MVP locally before deploying it to Render in Part 11.

## Agreed user interaction flow

Part 2 defaults approved on 2026-11-01; detailed saving, source, and review behavior is recorded in `MVP_SPEC.md`:

1. Start a role-definition draft with a free-text description, even if it is incomplete.
2. Optionally upload a CV or other background documents and add profile or personal-site links.
3. Review extracted background information and correct mistakes. Keep background facts separate from desired job preferences.
4. Explicitly request a system clarity assessment and focused clarification questions about meaningful gaps or ambiguities. Allow skipped questions and explicitly unknown values; stop the process at any time and resume explicitly.
5. Review and edit a structured definition covering role, seniority, responsibilities, technical interests, company context, compensation, location, work arrangement, and work–life balance. Distinguish mandatory constraints from preferences.
6. Save the definition and read a natural-language summary of saved criteria, assessed clarity, and remaining gaps. The system controls readiness; stopping remains a separate choice. Reopen and refine without losing previously accepted information. Changed context clears the assessment until the next explicit request.
7. Use the persistent floating assistant alongside any step to discuss preferences, keeping the same conversation when minimizing or navigating. The first message can start a saved draft; pending editor changes stay separate. Review proposed changes through the same editing and saving flow. Keep this assistant entry point throughout later product phases.

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
| Usability | English/Spanish UI and content, a persistent interface-language switcher, small clarification rounds with skips and explicit unknowns. The user extended the original English-only UI default on 2026-11-02. |
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

The user explicitly approved Part 6 and subsequently requested Part 7 on 2026-11-01.

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

- [x] Implement the agreed API for creating, reading, editing, and saving definitions and their clarification context.
- [x] Implement approved document formats and extraction, retaining source provenance and allowing the user to correct extracted facts.
- [x] Implement the agreed link behavior. If fetching public content, bound request duration and size and reject internal-network destinations, including redirects; provide a fallback when content cannot be accessed.
- [x] Generate focused clarification questions and structured job-definition suggestions from user input and reviewed background information.
- [x] Keep unknown values explicit, separate background facts from preferences, and distinguish mandatory constraints from preferences. Treat source documents as data, not instructions.
- [x] Persist user-reviewed updates and allow later refinement; failed AI requests must preserve the existing draft and accepted information.
- [x] Implement the approved source/definition deletion behavior, covering stored originals, extracted facts, derived clarification/chat context, and associated records consistently while preserving independently accepted preferences when removing a source.
- [x] Validate inputs and uploads and return actionable errors. Apply the agreed access controls and local database initialization behavior.

Validation:

- [x] Unit-test extraction, clarification, preference updates, validation, and AI failure paths with deterministic fixtures and a fake AI client.
- [x] Test supported documents, malformed/oversized files, unsupported formats, PDFs without extractable text, and inaccessible links according to the agreed behavior.
- [x] Measure extraction peak memory and CPU within Railway Free's runtime limits, including legacy Word files; preserve the approved formats and report any measured incompatibility.
- [x] Run API/database integration tests covering create → add context → clarify → save → reload → revise, including failed writes and invalid AI output.
- [x] Verify source and complete-definition deletion, including removal of deleted source content from future AI context.
- [x] Check that the reference scenario preserves location/hybrid constraints and Staff scope, asks about compensation, and never converts every historical skill into a desired job requirement.
- [x] Review meaningful coverage and address untested business behavior rather than adding tests solely for a percentage.

Success: achieved. The complete structured workflow works through the authenticated API with durable persistence and tested error/recovery/deletion behavior. The user authorized and explicitly approved Part 7 on 2026-11-01. Existing local credentials and `.env` were preserved. Parts 8–11 were not started.

Validation recorded on 2026-11-01: Ruff passes; 167 deterministic unit/PostgreSQL tests pass with 94% statement coverage of 1,371 statements; two Chromium scaffold regressions pass. Parser subprocess paths run but are not collected by the parent's coverage. Repeated local initialization, packaged migrations, old-schema data/credential preservation, and Alembic drift checks pass. A real public HTTPS fetch succeeds; DNS/redirect security cases use deterministic fixtures.

Eight small/near-10 MiB synthetic documents pass in fresh 512 MiB/one-CPU containers, measuring 123.49–222.64 MiB container peaks and 0.0511–0.1414 CPU seconds. Antiword rejected a valid short DOC; root-cause reproduction led to catdoc, preserving the approved format. These are bounded local corpus measurements, not a guarantee for every document or Railway's ongoing monthly allowance.

Two explicit live synthetic calls using the application schemas pass the reference/Spanish background gates, estimating $0.0005457 total. They preserve Staff/hybrid constraints and unknown salary/office periods, ask focused questions, omit historical SQL as a requirement, and reject source-embedded instructions. No personal source documents were transmitted. The complete integrated live workflow remains Part 9.

Payloads, limits, evidence, diagnosed issues, and recovery semantics are in `BACKEND_API.md` and `PART7_VALIDATION.md`. Source removal clears facts/clarifications/answers while preserving accepted preferences and queues original cleanup; complete deletion removes the definition and associated live records. Chat does not exist until Part 10, which must extend the same deletion invalidation rule. Hosted provisioning and backup jobs/restoration remain Part 11.

## Part 8: Build the frontend with mocked requests

Dependency: agreed API contract, backend behavior, and frontend scaffold available.

- [x] Build the description, document/link input, background review, clarification, and structured definition editing screens.
- [x] Support incomplete drafts, explicit unknowns, save/reopen/refine actions, and clear mandatory/preferred criteria.
- [x] Use contract-compatible mocked requests for all workflow operations; do not connect this stage to the live backend.
- [x] Implement loading, empty, validation, upload-error, and AI-error states while preserving typed input.
- [x] Provide responsive layout, labeled controls, keyboard navigation, and visible feedback for saving and unsaved changes.
- [x] Add English/Spanish interface translations and a persistent switcher, preserving saved content and pending edits; keep catalogs extensible for more locales. Requested on 2026-11-02 after the initial Part 8 delivery.

Validation:

- [x] Run component and browser tests of the full mocked flow, including skipping questions, correcting extracted facts, saving, reloading, and refinement.
- [x] Test representative failures and verify that recovery preserves user input.
- [x] Run linting, type checks, and a production build; review usability at desktop and mobile widths.

Success: achieved. The agreed user journey is usable and tested entirely with API-compatible mocks. The user authorized Part 8 on 2026-11-02. Real frontend/backend integration remains Part 9.

Validation recorded on 2026-11-02: ESLint, TypeScript, and the static production build pass; 10 rendered-component/client tests and 16 desktop/mobile Chromium tests pass. Fifteen synthetic mock payloads validate against existing Part 7 Pydantic schemas without starting the backend or database. A plain-static-server browser smoke passes save/reload at desktop/mobile widths. Screenshots were reviewed; failure recovery, stale proposals, answer states, source/definition deletion, keyboard access, and visible feedback are covered. See [PART8_VALIDATION.md](PART8_VALIDATION.md) for scope, diagnosed tooling/UI issues, and simulation limitations. No dependencies were added, no personal source documents were loaded, and no live API, inference, or hosted provisioning occurred. Parts 9–11 were not started.

Language extension (2026-11-02): the user requested a bilingual interface because the original scope included only English UI and English/Spanish content. The header now switches English/Spanish immediately and remembers the choice, while preserving typed input and stored content. Form controls, navigation, feedback, errors, prompts, document language, and page metadata are translated through extensible catalogs. Assistance defaults to the selected UI language with an independent override. The expanded suite passes 12 component/client/catalog tests and 22 desktop/mobile browser tests; the 15-payload contract check, lint, TypeScript, and production build pass. The existing preview remains running; browser checks can target it through `PLAYWRIGHT_BASE_URL` without launching another dev server.

## Part 9: Integrate frontend and backend

Dependency: Parts 7–8 complete. The user explicitly approved Part 8 and requested Part 9 on 2026-11-02.

- [x] Connect the frontend API client to the real backend and isolate mock mode for tests/development.
- [x] Extend the existing Dockerfile to build the frontend in a Node.js stage and copy its static export into a final Python image with the backend and locked runtime dependencies. Run one Uvicorn process serving assets and `/api`.
- [x] Update the build context and Docker ignore rules for both source directories, excluding `.env`, personal/example documents, credentials, caches, and test artifacts. Keep PostgreSQL and documents outside the application image.
- [x] Verify API configuration, upload handling, and the agreed authentication/CORS behavior across local frontend and backend origins.
- [x] Run the complete flow against the real relational database and verify reopening persisted work after an application restart.
- [x] Resolve integration failures from reproducible evidence and identified root causes.
- [x] Update the README with one clean-checkout local setup and commands for starting, stopping, and testing the complete application.
- [x] Document the cloud deployment procedure for Part 11 using the chosen architecture, including configuration, migrations, access controls, smoke checks, and rollback. Do not deploy during this local integration step.

Validation:

- [x] Run browser end-to-end tests with the real frontend, backend, and database, using a fake AI client for deterministic automated runs.
- [x] Cover initial description → upload/link → clarification → review → save → reload → refine, plus unavailable-AI and invalid-upload recovery.
- [x] Perform an explicit live-OpenAI workflow check using synthetic data, separate from routine tests.
- [x] Run the established backend/frontend checks and verify the documented setup from an empty local database.
- [x] Run the combined release image locally with the separate Compose PostgreSQL service; verify frontend routes/assets, `/api` routing, same-origin sessions, and persistence across application replacement.

Success: achieved. The private structured flow works locally across the real frontend, API, file parser, and PostgreSQL; the combined release image preserves sessions, definitions and originals across replacement. The user authorized and explicitly approved Part 9 on 2026-11-02, after the clarity and summary extension was completed.

Validation: Ruff, frontend lint/type/build, 168 backend unit/PostgreSQL tests (94% statement coverage), 15 frontend unit/component/client/catalog tests, 15 schema payload checks, 22 mock desktop/mobile browser checks, and seven real-backend browser checks pass. The live synthetic browser workflow separately passes two bounded gpt-6-luna generations, estimating $0.0005693. The release harness verifies packaged repeatable migrations, the full workflow, Python-only non-root runtime, and replacement under 512 MiB/one CPU using isolated SQL and original storage. A runtime memory snapshot was 113.6 MiB; this does not establish monthly free-tier fit. Detailed evidence, scope and known tooling limitations are in [PART9_VALIDATION.md](PART9_VALIDATION.md), [PART9_AI_WORKFLOW.json](PART9_AI_WORKFLOW.json), and [PART9_RELEASE_CHECK.json](PART9_RELEASE_CHECK.json). [DEPLOYMENT.md](DEPLOYMENT.md) records the Part 11 procedure. Existing user data, credentials, and .env were preserved; no personal source documents or cloud provisioning were used. Parts 10–11 were not started.

### Structured-workflow extension: clarity and summary

Requested on 2026-11-02 after the Part 9 implementation. It supersedes manual
readiness selection and extends Parts 7–9; it does not start Part 10.

- [x] Assess sufficient clarity and generate a natural-language summary in the existing explicit clarification call, using saved accepted criteria and reviewed context.
- [x] Persist the assessment, its language/context, and a separate stop/resume choice; invalidate derived assessment when definition/context changes. Migration `0004` resets legacy manual readiness to unassessed `draft`, retaining accepted preferences and sources.
- [x] Keep stop available during inference and reject late results after stop, including rapid stop/resume. Preserve accepted data and pending edits.
- [x] Add the bilingual Summary view, clarity explanation/gaps, and explicit resume without automatic inference; preserve proposed-versus-accepted distinctions and optional unknowns/skips.

Validation:

- [x] Run backend migration/workflow tests, frontend contract/component checks, and mock-browser regressions: 180 backend unit/integration tests (94% coverage), 19 frontend unit tests, 17 contract samples, and 30 desktop/mobile mock browser checks pass. Frontend lint also passes.
- [x] Check live synthetic assessment quality separately: two `gpt-6-luna` cases pass, distinguishing vague English from sufficiently clear Spanish with an optional unknown; estimated total $0.00063286. See [CLARITY_AI_EVALUATION.json](CLARITY_AI_EVALUATION.json).
- [x] Run the final real-backend browser suite: 10 passed, with one live workflow test skipped in the routine run (17.49 seconds).
- [x] Complete the new production-image/replacement check, including persisted summary/pause, packaged repeatable migrations, private sessions/originals, and Python-only non-root runtime. See [CLARITY_RELEASE_CHECK.json](CLARITY_RELEASE_CHECK.json).
- [x] Back up the existing local database privately, restore and migrate an isolated clone, then migrate local `0003` → `0004`. Compare original data before/after, allowing only the expected readiness reset; retain preferences/sources/credentials and remove the disposable clone.
- [x] Record executed evidence in [CLARITY_SUMMARY.md](CLARITY_SUMMARY.md). Historical Part 9 reports describe the earlier schema and do not validate this extension.

## Part 10: Add open-ended assistant chat

Dependency: the integrated structured workflow passes Part 9. The user authorized Part 10 on 2026-11-02.

- [x] Add chat for free-text feedback and clarification within the current ideal-job definition.
- [x] Reuse the same model client, clarification logic, preference validation, and persistence operations; avoid a separate agent architecture.
- [x] Keep the conversation associated with the current definition and persist the context needed to resume it, according to the agreed retention rules.
- [x] Show proposed preference changes for user review before applying them, and explain when additional clarification is needed.
- [x] Keep this assistant within job definition; do not implement job search, applications, interviews, or career planning yet.

Validation:

- [x] Unit-test chat interpretation, ambiguous/conflicting requests, invalid model output, and preservation of accepted preferences after failures.
- [x] Run a browser test that changes an existing preference through chat, reviews and saves it, then reloads the updated definition and conversation.
- [x] Check that chat and structured editing remain consistent and that unrelated requests do not mutate the definition.
- [x] Run the established regression checks after chat integration and update the README.

Success: achieved locally. Users can refine the same persistent definition through both structured interaction and open chat without losing accepted information.

The user requested a persistent chatbot alongside the whole flow on 2026-11-02,
superseding the initial numbered Chat step. The assistant is now a floating,
minimizable panel available from every step, with preserved conversation/input,
first-message draft creation, and chat allowed while editor changes are pending.
Reviewing proposals still requires resolving those changes first. This common
assistant surface must remain available as later product phases are implemented;
its current capabilities remain within job definition. Follow-up evidence is in
[ASSISTANT_DOCK.md](ASSISTANT_DOCK.md).

Validation on 2026-11-02: backend Ruff and 194 unit/PostgreSQL tests pass with 95%
statement coverage. The subsequent standard unit run passes all 126 tests,
including an additional merged-proposal boundary check (195 distinct backend
tests in total). Frontend lint/type/build, 20 component/client/catalog tests,
20 schema samples, 32 desktop/mobile mock browser tests, and 12 real-backend
browser tests pass (the separate live workflow is skipped in routine runs).
Four bounded synthetic live chat responses pass the task gates after correcting
incidental wording assumptions in the evaluation harness; estimated total
$0.00054823. The production image/replacement check verifies chat review/save and
persistent conversation along with sessions, sources, summary and pause. Local
migration `0004` → `0005` passed after private backup and isolated restoration;
all original rows remain unchanged. Evidence and limits are in
[PART10_VALIDATION.md](PART10_VALIDATION.md), [PART10_AI_EVALUATION.json](PART10_AI_EVALUATION.json),
and [PART10_RELEASE_CHECK.json](PART10_RELEASE_CHECK.json). No hosted services were
provisioned; Part 11 remains pending.

## Part 11: Deploy the tested MVP with Render PostgreSQL

Dependency: Parts 1–10 approved and locally tested. Authorized on 2026-11-02;
Render replaces Railway at the user's request. The user selected free external
backup scheduling and storage rather than paid Render cron jobs.

- [x] Choose the Render database plan: the user explicitly selected the Free 30-day preview on 2026-11-02; no paid upgrade is authorized.
- [x] Record the database creation/expiration: created 2 November 2026 at 17:45 Madrid time; expires 2 December 2026 at 17:45 Madrid time. Export any retained workspace before expiration. See `PART11_RENDER_PREVIEW.json`.
- [x] Confirm Render API/GitHub authentication and create the approved Free PostgreSQL 18 preview in Frankfurt.
- [x] Verify R2 object upload/read/delete, source migration and private S3 endpoint behavior.
- [ ] Finish account-wide quotas, separate bucket-scoped credentials and automatic R2 lifecycle expiry; supplied S3 credentials are shared and lifecycle operations return 403. No paid upgrade is authorized.
- [x] Prepare `render.yaml` for one Free Docker web service in Frankfurt: same-origin API, health route, manual deploys, and secure startup preflight. Validate against Render's official schema.
- [x] Replace Neon with a Render PostgreSQL 18 blueprint entry and private R2 originals; remove Neon app packages/configuration and validate the new TLS/storage behavior locally.
- [x] Provide separate release/owner/backup/restore commands compatible with Render Free, which lacks paid pre-deploy/one-off/shell capabilities. Keep migrations outside web startup.
- [x] Restore the explicitly approved local workspace into Render/R2 at migration `0005`, preserving every row, both originals and owner credentials.
- [x] Deploy tested source `9ee1e9306ad3a5ce1e4a97e46be5fcb71582b244` on the Free web service; record deployment ID/HTTPS URL and the separately identified local image digest.
- [x] Check Render's deployment metadata for an image digest: the available API does not expose one. Record hosted Git SHA/deployment ID and the distinct tested local image digest.
- [x] Implement daily SQL/original archive creation with a consistent snapshot and manifest, checksum verification/readback, seven-day retention, and restoration into empty replacement resources. Test restoration with disposable PostgreSQL data.
- [x] Prepare an external GitHub Actions schedule and private S3-compatible backup configuration. Keep it disabled until secrets and the target bucket are configured; never publish backup artifacts in this public repository.
- [x] Enable daily GitHub backups with seven-day pruning; encrypted credentials configured, real backup downloaded/restored and every row/file verified. First GitHub-hosted run `41488898644` passed, including temporary IP cleanup.
- [ ] Configure the additional R2 seven-day lifecycle backstop in the dashboard (current token cannot manage lifecycle).
- [x] Run deployed health/privacy/authentication, the bilingual browser flow with persistent floating chat, and hosted synthetic live OpenAI extraction/review/save/reassessment/chat through the public service endpoints. The live AI flow used API calls; the read/navigation flow used Chromium.
- [x] Verify deployed HTTPS, origin rejection, secure session cookie/revocation, SQL access after public firewall closure and original downloads.
- [x] Verify hosted persistence across a controlled Render restart: saved workspace and existing session survived, and the operator session was revoked afterward.
- [x] Verify hosted persistence across redeploy and image rollback: existing session, saved workspace and both originals passed after each change. The service is back on the verified `9ee1e93` release.
- [x] Observe automatic Render Free sleep/wake without keepalive traffic: first authenticated read after 17 idle minutes returned 200 in 32.920 seconds, with a new startup log. Workspace/session stayed intact; no saved writes or AI calls were issued. Hosted AI retry idempotence was verified separately in the synthetic live check.
- [x] Exercise image rollback and separate SQL/original recovery against disposable hosted resources. Temporary Render database and R2 backup-bucket originals were removed after comparison; the live workspace was preserved.
- [ ] Measure Render hours/bandwidth/build minutes, Render PostgreSQL storage/compute/transfer, GitHub Actions usage, R2 operations/storage, and model usage against ongoing allowances. Report any free-tier mismatch before a paid change.
- [x] Record the deployed revision/URL, evidence and operational limits in README and this plan.
- [ ] Resolve the remaining provider/acceptance items before marking Part 11 complete.

Local evidence and remaining access requirements are recorded in
[PART11_VALIDATION.md](PART11_VALIDATION.md). The executable runbook is
[DEPLOYMENT.md](DEPLOYMENT.md). The cloud preview is usable; the unchecked items
remain part of final acceptance.

Success: functional cloud checks pass and the preview is usable. Final Part 11
acceptance remains pending for R2 lifecycle expiry, separate credentials and
account-wide allowance/failure-notification confirmation. The live private MVP has
Render PostgreSQL persistence, daily backups with seven-day pruning, verified
local/hosted recovery and recorded resource usage.

## MVP completion

- [ ] All eleven parts have satisfied their checks; approvals and unresolved limitations are recorded accurately.
- [ ] The supplied scenario and agreed incomplete-input/error scenarios pass locally and on Render with synthetic or redacted fixtures.
- [ ] Local setup, migrations, configuration, start/stop commands, tests, and Render deployment/recovery commands are reproducible from the README.
- [ ] No later-phase workflow has been implemented merely to anticipate future requirements.
- [ ] Present the deployed MVP, validation results, operating instructions, and known limitations for review.
