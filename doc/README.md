# Project documentation

Start with the [project roadmap](PLAN.md). **Job finding** is the current feature;
the job-definition MVP is the implemented baseline.

## Current feature: job finding

- [Implementation plan](features/job-finding/PLAN.md): 14 small parts, dependencies,
  proposed defaults, outstanding decisions and acceptance criteria for requirement #2.
- Implementation has not started. This plan proposes future behavior; it does not
  claim that search, scoring, notifications or learning are already available.

## Implemented feature: job definition

- [Completed MVP plan](features/job-definition/PLAN.md): original Parts 1–11,
  approval history and completion evidence.
- [Requirements and architecture baseline](features/job-definition/MVP_SPEC.md).
- [Clarity and natural-language summary](features/job-definition/CLARITY_SUMMARY.md).
- [Persistent floating assistant](features/job-definition/ASSISTANT_DOCK.md).
- [Initial AI evaluation](features/job-definition/AI_EVALUATION.md).
- Validation records: [backend](features/job-definition/validation/PART7_VALIDATION.md),
  [frontend](features/job-definition/validation/PART8_VALIDATION.md),
  [integration](features/job-definition/validation/PART9_VALIDATION.md), and
  [chat](features/job-definition/validation/PART10_VALIDATION.md).
- Sanitized machine-readable results live in
  [the feature's evidence directory](features/job-definition/evidence/).

## Shared architecture and operations

- [Backend API](architecture/BACKEND_API.md) and
  [persistence and deletion](architecture/PERSISTENCE.md): implemented contracts;
  update them when new feature behavior is implemented.
- [Deployment overview](operations/OVERVIEW.md): approved Render/R2 preview.
- [Deployment and recovery runbook](operations/DEPLOYMENT.md).
- [Operational follow-ups](operations/FOLLOW_UPS.md): accepted limitations and
  the database-expiration deadline.
- [Preview validation](operations/validation/PART11_VALIDATION.md) and
  [cloud evidence](operations/evidence/).
- [Repository README](../README.md): local setup, commands and validation entry points.

## Historical and private material

- [Superseded Neon setup](archive/NEON_SETUP.md) is retained for historical context;
  Render is the current database provider.
- Personal reference files keep their existing ignored locations:
  `doc/ajimenez/MY_IDEAL_JOB.md`, `doc/ajimenez/CV.pdf` and
  `doc/ajimenez/Profile.pdf`. They are not public fixtures or routine test inputs.

## Conventions for feature work

Each feature owns `doc/features/<feature>/PLAN.md`. Add its agreed specification
when decisions are settled, validation notes in `validation/`, and sanitized
reports in `evidence/` as work is executed. Do not create placeholder reports or
label proposed decisions as approved. Qualify part numbers by feature; historical
MVP Part 2 and job-finding Part 2 are different milestones.

Keep shared API/persistence contracts under `architecture/` and deployment,
backup and usage documentation under `operations/`. New features extend the same
application and operational runbooks. Preserve dated evidence and approval
records; old validation counts describe the revision checked at that time.

The reorganization on 2026-11-03 moved the former flat documentation into these
folders and updated links and report writers. Original JSON report contents were
preserved, including any historical paths recorded inside them. The former
MVP plan is now `features/job-definition/PLAN.md`; `doc/PLAN.md` remains the
stable entry point for the project's current roadmap. The former `deployment.md`
is now `operations/OVERVIEW.md`, avoiding filenames distinguished only by case.
