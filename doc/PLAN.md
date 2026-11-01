# Career assistant MVP plan

Status: draft awaiting user approval. Only Part 1 has started.

## Scope and working rules

The MVP helps a user define, save, revisit, and refine an ideal job using their preferences and optional background documents or profile links. It covers responsibilities, scope, compensation, location, work arrangement, and work–life balance.

Job discovery, offer scoring, notifications, skill development plans, application tracking, interview preparation, and support after starting a job belong to later phases. Consider their relationships in the design without implementing their workflows or unused infrastructure.

- Keep the required Next.js frontend, Python backend, AWS target, Amazon Bedrock endpoint, and relational persistence.
- Resolve hosting, model selection, and other open decisions in Part 2; proposals below are not approved technical decisions.
- Follow the eleven parts in order. Complete each part's checks before marking its tasks done, and record relevant decisions or remaining blockers here.
- Obtain user approval of this plan before Part 2. Resolve requirement and architecture choices with the user before scaffolding.
- Keep planning documents and source examples together in `doc/`: [ideal job](ajimenez/MY_IDEAL_JOB.md), [CV](ajimenez/CV.pdf), and [LinkedIn export](Profile.pdf).
- Verify current stable library versions when adding dependencies, commit lockfiles, and keep the README's setup and test commands current and free of emojis.
- Prefer simple modules and meaningful tests. Aim for approximately 80% code coverage, prioritizing business logic and user workflows without tests written only to raise coverage.
- Use synthetic or redacted test fixtures. Keep credentials and personal document contents out of logs, committed fixtures, and test reports.
- Validate the complete MVP locally before deploying it to AWS in Part 11.

## Proposed user interaction flow

Confirm and refine this flow during Part 2:

1. Start an ideal-job draft with a free-text description, even if it is incomplete.
2. Optionally upload a CV or other background documents and add profile or personal-site links.
3. Review extracted background information and correct mistakes. Keep background facts separate from desired job preferences.
4. Answer focused clarification questions about missing or ambiguous preferences. Allow skipped questions and explicitly unknown values.
5. Review and edit a structured definition covering role, seniority, responsibilities, technical interests, company context, compensation, location, work arrangement, and work–life balance. Distinguish mandatory constraints from preferences.
6. Save the draft or completed definition, reopen it later, and refine it without losing previously accepted information.
7. In Part 10, use open chat to discuss preferences and review proposed changes through the same editing and saving flow.

The supplied ideal-job example is the reference acceptance scenario: preserve Staff scope, architecture and system design, collaboration across teams, learning, international scope, and an AI-engineering preference. Remote is preferred; hybrid is acceptable near Madrid with a two-day on-site limit whose period must be confirmed in Part 2. Clarify “good compensation” rather than inventing a salary, and preserve the constraint against a role focused only on frontend work.

## Part 1: Define and approve the plan

Deliverable: this execution plan, with explicit scope, dependencies, validation, and completion criteria.

- [x] Read `AGENTS.md`, the original plan, and the supplied ideal-job, CV, and LinkedIn examples.
- [x] Expand all eleven parts into actionable checklists with tests and success criteria.
- [x] Record the proposed interaction flow, open decisions, and boundaries for later features and deployment.
- [ ] Obtain user review and approval of this plan; incorporate requested changes before Part 2.

Validation:

- [x] Check that every original part is represented, document links resolve locally, and only planning documentation has changed.
- [x] Check that pending decisions are clearly distinguished from approved requirements.

Success: the user has approved the plan. Approval is pending; no clarification or implementation work is marked complete.

## Part 2: Clarify requirements and choose the architecture

Dependency: Part 1 approved.

- [ ] Present concise proposals for the open decisions below, using the supplied examples; ask only questions that materially affect the MVP.
- [ ] Confirm the interaction flow, required definition fields, draft/completion rules, and treatment of unknown or conflicting answers.
- [ ] Define functional and nonfunctional acceptance criteria, including upload limits, expected response times, AI spending limits, and supported languages.
- [ ] Compare AWS Lambda and container hosting for the frontend, API, AI calls, and document processing. Include request duration, relational connections, operational effort, expected usage, and cost. Distinguish a Docker-based local setup from the cloud compute decision.
- [ ] Select the Python web framework, relational database, migration tool, local development setup, and AWS compute/storage approach; document a short rationale and local-to-cloud differences.
- [ ] Verify how the OpenAI-model requirement can be met through the configured Bedrock endpoint, region, and account. Resolve any incompatibility with the user before selecting models or changing providers. Do not disclose credentials.
- [ ] Agree the initial API contract and error conventions for drafts, sources, clarification, and saving; refine details in Parts 5 and 7.
- [ ] Update `AGENTS.md` and this plan with approved requirements and decisions, keeping both concise.

| Decision | Points to resolve |
| --- | --- |
| Users and access | Personal single-user tool or accounts; authentication, ownership, and access required for deployment. |
| Definition lifecycle | One or several definitions per user; required fields; save incomplete drafts; update the current definition or retain history. |
| Preferences | Mandatory versus preferred criteria; salary currency, range, gross/net basis and period; working hours, travel, location, and hybrid limits. |
| Documents | Exact support for PDF, legacy `.doc`, `.docx`, and Markdown; text-only versus scanned PDFs; file size/count limits and failure messages. Do not silently replace `.doc` with `.docx`. |
| Links | Store references only or retrieve public content; fallback for inaccessible LinkedIn pages; no assumption of authenticated scraping or LinkedIn account integration. |
| Data handling | Storage of originals and extracted text, retention/deletion expectations, and what background information is sent to Bedrock. |
| Usability | Interface and input languages, question cadence, skipped questions, and review of AI suggestions. |
| Operations | AWS region, expected usage and budget, AI response-time targets, credentials, and the eventual deployment environment. |

Validation:

- [ ] Walk through the reference scenario and one incomplete-input scenario with the proposed flow.
- [ ] Check that agreed requirements map to testable outcomes and that no unresolved decision blocks scaffolding.
- [ ] Review the architecture rationale and model-access constraints with the user.

Success: the MVP requirements, user flow, architecture, and acceptance criteria are agreed and recorded; later-phase features remain outside implementation scope.

## Part 3: Scaffold the backend and local infrastructure

Dependency: Part 2 decisions recorded.

- [ ] Create `backend/` with the selected Python framework, dependency lockfile, basic configuration, and test tooling.
- [ ] Separate configuration, HTTP handlers, and application logic without introducing unused abstractions.
- [ ] Add a health API route and a small static “hello world” HTML page that calls the API and displays its result.
- [ ] Provide documented backend start/stop commands and a credential-free configuration template. Read secrets from local configuration or the environment.
- [ ] Set up the agreed local infrastructure and document the AWS resource mapping. Keep actual cloud provisioning outside this scaffold step.
- [ ] Create a simple README with prerequisites, configuration, and reproducible start/stop/test instructions.

Validation:

- [ ] Run the backend from the documented setup; verify the HTML page, successful API call, health response, and shutdown.
- [ ] Run basic API tests without AWS credentials or network access.

Success: another developer can start and stop the local backend and demonstrate the HTML-to-API call using the README.

## Part 4: Scaffold the frontend

Dependency: Parts 2–3 complete.

- [ ] Create `frontend/` with current stable Next.js, TypeScript, dependency lockfile, linting, and the agreed test tooling.
- [ ] Add the application shell and a minimal entry page for the ideal-job workflow.
- [ ] Set up environment-based API configuration without exposing backend or AWS secrets to the browser.
- [ ] Document frontend start/stop commands and how to run it alongside the backend.

Validation:

- [ ] Run linting, type checks, and a production build.
- [ ] Open the entry page locally and verify that the development server stops cleanly.

Success: the frontend runs locally and builds successfully; the job-definition UI remains for Part 8.

## Part 5: Design and implement MVP persistence

Dependency: approved requirements and working scaffolds.

- [ ] Propose a relational schema for the agreed user/ownership model, background sources, ideal-job drafts, preferences, and clarification questions/answers. Add conversation persistence when required by Part 10.
- [ ] Define keys, relationships, constraints, timestamps, and how accepted changes are saved. Implement revision history only if agreed in Part 2.
- [ ] Sketch how future offers, matches, development plans, application processes, interviews, and career progress relate to the MVP entities; do not create unused later-phase tables.
- [ ] Review the schema against the interaction flow before adding migrations and the necessary persistence operations.
- [ ] Provide reproducible local database initialization and an isolated test database. Create the local database when absent and apply migrations; document managed-database provisioning separately.
- [ ] Document where original files and extracted content are stored, consistent with the approved retention requirements.

Validation:

- [ ] Initialize an empty local environment, apply migrations, and repeat initialization without losing data.
- [ ] Test create, save, reload, and update operations against the selected relational engine; verify relevant constraints and transaction rollback.
- [ ] Verify ownership boundaries if multiple users are supported and verify schema upgrades preserve existing data.

Success: the MVP schema supports saved and revisable definitions and their context, with repeatable migrations and persistence tests.

## Part 6: Verify Bedrock connectivity and select models

Dependency: Part 2 resolves provider, endpoint, and account compatibility; backend scaffold available.

- [ ] Add backend-only Bedrock configuration using the provided environment settings without printing credentials or committing secrets.
- [ ] Implement a small AI client boundary that supports a fake client for routine tests.
- [ ] Run an explicit live smoke test asking “2+2” and verify that the response represents 4.
- [ ] Evaluate accessible candidate OpenAI models on representative background extraction, ambiguous-preference clarification, and structured definition updates. Prefer the lowest-cost model that meets the agreed quality and latency criteria for each task.
- [ ] Record selected model identifiers, region/endpoint requirements, evaluation results, token limits, and a usage/cost estimate based on verified pricing. Reuse a model across tasks when sufficient.
- [ ] Define structured-output validation and useful behavior for access errors, unavailable models, timeouts, throttling, and invalid responses.

Validation:

- [ ] Unit-test request construction, response validation, and error handling with fake responses.
- [ ] Run the live arithmetic test separately from routine tests; record a sanitized result.
- [ ] Use synthetic examples to check that the selected models preserve constraints, ask about missing salary information, and avoid inventing background facts.

Success: the configured Bedrock endpoint works, task-level model choices have evidence, and routine tests need neither credentials nor paid AI calls. Arithmetic alone does not establish model suitability.

## Part 7: Implement the job-definition backend

Dependency: persistence and AI connectivity verified in Parts 5–6.

- [ ] Implement the agreed API for creating, reading, editing, and saving definitions and their clarification context.
- [ ] Implement approved document formats and extraction, retaining source provenance and allowing the user to correct extracted facts.
- [ ] Implement the agreed link behavior. If fetching public content, bound request duration and size and reject internal-network destinations, including redirects; provide a fallback when content cannot be accessed.
- [ ] Generate focused clarification questions and structured job-definition suggestions from user input and reviewed background information.
- [ ] Keep unknown values explicit, separate background facts from preferences, and distinguish mandatory constraints from preferences. Treat source documents as data, not instructions.
- [ ] Persist user-reviewed updates and allow later refinement; failed AI requests must preserve the existing draft and accepted information.
- [ ] Implement source deletion or cleanup if required by the Part 2 retention decisions, covering stored originals, extracted content, and associated records consistently.
- [ ] Validate inputs and uploads and return actionable errors. Apply the agreed access controls and local database initialization behavior.

Validation:

- [ ] Unit-test extraction, clarification, preference updates, validation, and AI failure paths with deterministic fixtures and a fake AI client.
- [ ] Test supported documents, malformed/oversized files, unsupported formats, PDFs without extractable text, and inaccessible links according to the agreed behavior.
- [ ] Run API/database integration tests covering create → add context → clarify → save → reload → revise, including failed writes and invalid AI output.
- [ ] Verify deletion/cleanup behavior if included in the approved requirements.
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
- [ ] Verify API configuration, upload handling, and the agreed authentication/CORS behavior across local frontend and backend origins.
- [ ] Run the complete flow against the real relational database and verify reopening persisted work after an application restart.
- [ ] Resolve integration failures from reproducible evidence and identified root causes.
- [ ] Update the README with one clean-checkout local setup and commands for starting, stopping, and testing the complete application.
- [ ] Document the cloud deployment procedure for Part 11 using the chosen architecture, including configuration, migrations, access controls, smoke checks, and rollback. Do not deploy during this local integration step.

Validation:

- [ ] Run browser end-to-end tests with the real frontend, backend, and database, using a fake AI client for deterministic automated runs.
- [ ] Cover initial description → upload/link → clarification → review → save → reload → refine, plus unavailable-AI and invalid-upload recovery.
- [ ] Perform an explicit live-Bedrock workflow check using synthetic data, separate from routine tests.
- [ ] Run the established backend/frontend checks and verify the documented setup from an empty local database.

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

## Part 11: Deploy the tested MVP to AWS

Dependency: Parts 1–10 complete, local acceptance checks passing, and the deployment procedure from Part 9 reviewed. Use the architecture selected in Part 2.

- [ ] Confirm the target AWS account, region, environment, planned resource changes, and estimated recurring cost against the agreed budget.
- [ ] Add version-controlled infrastructure definitions and repeatable deployment commands for the selected frontend hosting, Python backend, relational database, document storage, networking, and access controls.
- [ ] Configure HTTPS, the agreed application access model, runtime IAM roles, and backend-only secrets; keep credentials out of browser assets and deployment output.
- [ ] Verify Bedrock model access in the deployment region and configure the selected model identifiers and usage limits.
- [ ] Build versioned release artifacts from the locally tested revision and validate the infrastructure changes before applying them.
- [ ] Provision the required resources, initialize the cloud database, apply migrations, and deploy the backend and frontend with the correct API configuration. Back up existing data before schema changes.
- [ ] Configure useful logs, health/error monitoring, cost alerts, and the agreed backup and retention settings.
- [ ] Document redeployment, application rollback, database recovery, and resource cleanup, distinguishing disposable resources from persistent user data.
- [ ] Update the README with the deployed URL, release identifier, operational commands, and known limitations.

Validation:

- [ ] Run deployed frontend/API health checks and a live Bedrock smoke test.
- [ ] Run the deployed browser workflow using synthetic data: description → upload/link → clarification → review → save → reload → structured refinement → chat refinement.
- [ ] Verify HTTPS, authentication/access boundaries, production API/CORS configuration, and restricted database/document-storage access according to the approved design.
- [ ] Verify that saved definitions, background sources, and conversation context survive an application restart or redeployment.
- [ ] Check useful error reporting and exercise application rollback and database backup/recovery against disposable test data without affecting user data.
- [ ] Record the deployed revision, URLs, validation results, and any remaining operational limitations.

Success: the MVP is accessible to its intended users on AWS, its deployed workflow passes acceptance checks, data persists across releases, and deployment and recovery are reproducible.

## MVP completion

- [ ] All eleven parts have satisfied their checks; approvals and unresolved limitations are recorded accurately.
- [ ] The supplied scenario and agreed incomplete-input/error scenarios pass locally and on AWS with synthetic or redacted fixtures.
- [ ] Local setup, migrations, configuration, start/stop commands, tests, and AWS deployment/recovery commands are reproducible from the README.
- [ ] No later-phase workflow has been implemented merely to anticipate future requirements.
- [ ] Present the deployed MVP, validation results, operating instructions, and known limitations for review.
