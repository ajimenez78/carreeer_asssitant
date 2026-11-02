# Carreer assistant system

## General description
This career assistant helps the user clarify the role they are looking for, select interesting offers, close skill gaps, prepare for interviews, and continue growing after starting a job.

The assistant must remain available as a standard floating chatbot throughout all workflow steps and future product phases, rather than as a numbered step. Preserve conversation and typed input when minimizing or changing steps. Chat proposals still require review and explicit saving.

## Business requierements

### 1. Job definition
- The user can clarify the role they are looking for.
- The system assesses whether the saved definition is sufficiently clear and asks focused questions to help the user iterate. The user can stop clarification at any time and resume explicitly; stopping is separate from clarity/readiness.
- Provide a natural-language summary of the current saved definition, its clarity assessment, and remaining gaps. Keep unaccepted suggestions separate from accepted preferences.
- Include not only job responsabilities. Also compensations like salary and life/work balance.
- An example of an initial, partially vague description is referenced in doc/ajimenez/MY_IDEAL_JOB.md
- In the job definition, the user can be able to provide it's background, uploading it's CV in PDF, doc or even markdonw format and additional documents like the LinkedIn profile.
- Also external links like Linkedin profile or personal websites are allowed
- Once the position is defined, it can be re-visited and refined latelly

### 2. Job finding
- The system provides an Agent that can actively  find for job positions across Internet. The defined job position is used as template for this search.
- In an initial phase, The main source for finding positions will be LinkedIn. If needed, the system will ask to connect to the user LinkedIn account for more accurate finding.
- You can also manually add positions and proposals.
- An score of position vs ideal job descriptions will be provided
- The system will notify to the user with the most interesting offers
- The user can provide feedback to the system about the found offers. The system will learn of this feedback.

### 3. Closing the gap
- If there is a Gap between the User skills and the skills demanded for the job offers, the system could provide a skill development plan to the user
- The plan shouldn't be specific to a particular offer, but suitable for most of the offers that match more the ideal job definition.

### 4. Application tracking and interview preparation
- The system will provide a module for tracking the opened job application processes
- The system will provide an assistant for preparing the different job interviews in the process
- If a process ends without a real offer, the user could provide feedback to the system to enhance the career plan

### 5. Getting into the real job and further
- Once a job position is reached, the system will guide the user to be proficient in doing the real daily job
- The system will provide with a further develpment carrer plan for the user, in the current company or outside it, based on his goals, preferences and the market status

## Limitations
The business requiremens implementation will be incremental. We will start with a MVP that will only match with the first step, Job definition. But the initial design will take into account that the system will grouth with the rest of provided requirements

The MVP is for one private user with one current editable job definition, explicit save/review actions, and no revision history. Provide English and Spanish interfaces with a persistent language switcher and catalogs that can support additional languages; preserve user content when switching. Accept English and Spanish content. Support text-based PDF, legacy .doc, .docx, and Markdown, up to five files of 10 MB each; scanned-document OCR is deferred. Retrieve public URLs with an upload/paste fallback. Retain sources until deleted, with daily backups retained for seven days. The Part 2 defaults were approved on 2026-11-01; bilingual UI support was requested on 2026-11-02.

The system-assessed clarity and summary extension was requested on 2026-11-02. Reuse explicit clarification requests to assess and summarize saved context; do not call AI on page load or save. Changed definition/context invalidates the saved assessment. Optional unknowns or skipped questions do not by themselves prevent sufficient clarity.

## Technical decisions
- Start on Railway Free, with Neon Free for managed PostgreSQL and private document storage. Measure usage against the ongoing free allowances, including backup jobs/storage; do not rely on introductory trial credits to prove the app fits. Any paid hosting upgrade requires the user's explicit choice. This replaces the earlier AWS deployment requirement.
- Use Next.js with TypeScript. Package its static export and FastAPI together in one application Docker image and one Railway web service. Use Node.js only in the frontend build stage and Python/Uvicorn in the final runtime image; keep frontend/ and backend/ separate for local development. PostgreSQL and uploaded documents stay outside the application container in Neon.
- Use Python with FastAPI, SQLAlchemy, Psycopg, and Alembic migrations. Use local PostgreSQL through Docker Compose for development and integration tests.
- Test the complete solution locally before the real cloud deployment.
- Call the OpenAI API directly using the backend-only OPENAI_API_KEY in .env. This replaces Amazon Bedrock; AWS authentication is no longer an MVP prerequisite.
- Select the lowest-cost OpenAI model that meets each task's quality and latency requirements. Evaluate gpt-6-luna initially; confirm inference behavior and model suitability in Part 6.
- Retain daily database/document backups for seven days and verify restoration. Use independent private backup storage; do not assume the free database tier provides the agreed backup retention.

## Coding standards
1. For external libraries, use the most recent versions. Keep them updated.
2. Keep the code simple. Use good practices and proved design pattenrs, but do not overengineer. Simplfy and refactor when needed. No unnecessary defensive programming. No extra features. Follow SOLID principles and at the same time focus on simplicity.
3. Make and maintain useful unit and end-to-end tests. Try to ensure 80% of code coverage but do not force silly tests only to reach this goal. Keep them relevant and priorize useful test to coverage.
4. Keep README updated, simple and free of emojis.
5. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.

## Working documentation
All documents for planning and executing this project will be in the doc/ directory. Please review the doc/PLAN.md document before proceeding. Agreed Part 2 requirements, architecture, API baseline, and validation status are recorded in doc/MVP_SPEC.md. Example source documents remain in doc/: doc/ajimenez/MY_IDEAL_JOB.md, doc/ajimenez/CV.pdf, and doc/ajimenez/Profile.pdf (LinkedIn export).
