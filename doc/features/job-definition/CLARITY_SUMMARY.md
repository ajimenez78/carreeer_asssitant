# System clarity and role summary

Requested on 2026-11-02 after Part 9: let the system decide whether the role
definition is sufficiently clear, help the owner iterate, allow stopping at any
time, and show the current definition in natural language. This extends the
structured workflow. Part 10 chat and later job discovery remain outside scope.

## Agreed behavior

- Reuse the existing explicit clarification request to produce questions,
  reviewable preference proposals, a clarity explanation/gaps, and a saved
  natural-language summary. No AI calls on page load or save, and no separate
  summary call.
- Assess the saved definition and reviewed context. Explain genuine ambiguity;
  allow optional unknowns and skipped questions. System-controlled `ready` means
  sufficiently clear, not every possible field filled.
- Summarize saved accepted requirements without presenting proposed preferences
  as accepted. Keep the generated language when switching the bilingual UI.
- Persist the assessment and its language, timestamp, and context. Changed saved
  criteria, answers, or source context invalidate the old assessment and return
  to `draft`; an unchanged save preserves it.
- Persist stop/resume separately from readiness. Stop remains available during
  inference; in-flight responses after a control/context change cannot apply,
  including stop followed immediately by resume. Preserve accepted data and
  local edits; resume requires a separate explicit assessment request.
- Add a fifth Summary view with prose, clarity explanation/gaps, and clear
  feedback when saved context is unassessed or differs from local edits.

Payloads and limits are documented in [BACKEND_API.md](../../architecture/BACKEND_API.md). The
requirements are in [MVP_SPEC.md](MVP_SPEC.md) and execution in [PLAN.md](PLAN.md).

Migration `0004` adds assessment/pause persistence and a monotonic control version
for in-flight context checks. Legacy manual `ready` status is reset to unassessed
`draft`. Existing preferences, sources, answers, and owner credentials remain;
the next explicit assessment establishes readiness under the new workflow.

## Acceptance checks

- [x] A vague saved description gets an insufficient assessment and focused
  questions; a sufficiently clear saved role gets `ready` without new questions.
- [x] Optional unknowns/skips do not cause endless repeated questioning; manual
  request `state` cannot override the assessment.
- [x] Assessment and prose persist on reload. Unsaved edits and pending proposals
  stay separate from accepted criteria; UI language changes preserve content.
- [x] Changed criteria/answers/reviewed facts/retried or deleted sources clear
  assessment and readiness; unchanged saves preserve them. Whole deletion
  removes associated assessment/control data with the definition.
- [x] Stop works during a pending request, persists after reload, and prevents
  late application, including rapid stop/resume. Failed control writes are shown
  honestly. Resume makes no automatic AI call.
- [x] AI, validation, and network failures preserve accepted data and local input.
  Background facts remain separate from job requirements.
- [x] Backend, frontend, and mock-browser checks pass with synthetic data;
  migrations are exercised against disposable PostgreSQL.
- [x] Final real-backend browser checks pass.
- [x] Final production-image/replacement check passes.

## Validation evidence

Recorded on 2026-11-02:

| Check | Result |
| --- | --- |
| Combined backend unit/PostgreSQL integration suite | 180 passed; 94% statement coverage |
| Frontend unit/component/client tests | 19 passed; frontend lint passed |
| API contract samples | 17 passed |
| Desktop/mobile mock Chromium suite | 30 passed |
| Explicit live synthetic model assessment | 2/2 passed; estimated total $0.00063286 |
| Final real-backend browser suite | 10 passed, 1 explicit-live workflow skipped; 17.49 seconds |
| New production image and replacement check | Passed; summary and pause persist across replacement |

The backend checks cover saved assessment/readiness, invalidation, unchanged
saves, pause/resume and late-result rejection, strict output failures, and
migration/persistence behavior. Frontend checks cover saved prose versus pending
edits, bilingual content preservation, source/answer invalidation, stopping during
a pending request, a mock stop/resume race, and truthful failure/retry feedback
for stop persistence.

The explicit `gpt-6-luna` check used synthetic data only. A vague English case was
assessed insufficient without inventing a Staff role; a detailed Spanish case
was assessed sufficiently clear while retaining an optional unknown. Both
produced prose, kept historical background separate from requirements, and
passed the focused-question/clear-stop gates. Calls took approximately 8.0 and
4.5 seconds. Full results are in
[CLARITY_AI_EVALUATION.json](evidence/CLARITY_AI_EVALUATION.json). This is bounded quality
evidence for those two cases, not a general guarantee or deployed check.

The combined production image passes packaged repeatable migrations, the full
browser workflow with test-only AI injection, HttpOnly same-origin sessions,
real Markdown extraction, save/reload/refine, and replacement preserving SQL,
session, originals, summary, and pause. The runtime contains Python only, runs
without root, excludes private files, and was checked under 512 MiB/one CPU.
Its memory snapshot was 113.5 MiB; this is not a peak or monthly free-tier fit
measurement. The image ID and checks are in
[CLARITY_RELEASE_CHECK.json](evidence/CLARITY_RELEASE_CHECK.json).

Local migration `0003` → `0004` also passed against the existing owner database.
Before changing it, a mode-600 backup was written to the ignored private path
`.data/backups/20261102T083649Z-pre-clarity/career.dump`. It was restored into a
unique isolated database, migrated there, and checked using canonical row
fingerprints compared in memory. The same migration was then applied to the
main local database; original rows and columns were unchanged except for the
expected readiness reset to `draft`. Sources, preferences, and credentials were
retained. The disposable restore database was dropped; no source documents were
changed and no private contents were printed.

Only the local database service was running after these checks. No cloud or
application deployment occurred. This one-off private backup/restore rehearsal
does not implement the scheduled seven-day backup policy planned for Part 11.
For another existing database, apply `make db-migrate` explicitly before running
the updated application.

The Part 9 counts, live-model report, and release-image report remain historical
evidence for the preceding schema and must not be interpreted as validation of
this extension. Part 10 and hosted deployment have not started.
