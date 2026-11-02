# Part 10: open-ended refinement chat

Completed locally on 2026-11-02, authorized by the user's request to proceed with
Part 10. Hosted provisioning, scheduled seven-day backups, and monthly free-tier
measurement remain Part 11.

The user subsequently requested a floating chatbot throughout the flow, replacing
the initial numbered Chat step. Current UI behavior and follow-up validation are in
[ASSISTANT_DOCK.md](ASSISTANT_DOCK.md); the evidence below records the original
Part 10 delivery.

## Delivered behavior

The bilingual **Chat** view discusses the current saved role with reviewed
background and retained conversation. It uses the existing model client, shared
preference instructions, validation, merging, and explicit save endpoint. There
is no separate agent or new dependency. Requests outside job definition redirect
back to the supported task; no job-search/interview/application workflows were added.

Chat suggestions remain proposals. **Review chat suggestions** opens the existing
criteria editor, where the user can edit/remove suggestions before applying the
reviewed set. Accepted criteria omitted by the model remain in that set; changes
to accepted values carry a review notice. Historic proposals remain distinct from
current accepted preferences and become unavailable for direct review when their
context changes. Opening history, changing language, and saving do not call AI.

Conversation turns persist in PostgreSQL through migration `0005`. A successful
message and validated reply commit together; failures preserve accepted data and
typed input without persisting a partial turn. Request UUIDs replay committed
responses and prevent duplicate turns after retries, including overlapping
requests. Two overlapping calls may still incur two provider generations; this
is database deduplication, not provider-level exactly-once billing.

Chat respects stop/resume. Saved-context tokens reject results after a structured
edit, concurrent message, source change, stop, or rapid stop/resume. In-scope chat
invalidates the prior clarity assessment; an unrelated turn leaves the saved
definition unchanged. A new explicit clarification call assesses current saved
criteria. Source extraction, review, or removal clears derived chat/clarification
context, while independently accepted criteria remain. Complete-definition
deletion cascades conversation records. Deletion notices explain these effects.

## Executed checks

| Check | Result |
| --- | --- |
| Ruff lint/format | Pass. |
| Complete backend suite | 194 unit/PostgreSQL tests pass; 95% reported coverage across 1,516 statements. The subsequent standard `make check` run passes all 126 unit tests, including the additional 100-criterion merged-proposal boundary (195 distinct backend tests including the 69 PostgreSQL tests). |
| Frontend ESLint, TypeScript and static build | Pass. |
| Frontend components/client/catalogs | 20 tests pass. |
| Mock/backend schema compatibility | 20 synthetic payloads validate, including chat input, turn and history. |
| Desktop/mobile mock browsers | 32 tests pass. Both chat cases also pass after the final historical-proposal label change. |
| Real frontend/API/PostgreSQL browsers | 12 pass; the separate live workflow is skipped in routine runs. |
| Live synthetic chat | Four cases pass, using gpt-6-luna with low reasoning; see the qualification below. |
| Combined production image/replacement | Pass; chat review/save and conversation survive replacement along with the definition, sources, session, summary and stop choice. |
| Existing local database | Private backup, isolated restore/migration, then local `0004` → `0005`; every original row remains unchanged. |

The API tests cover review/save/reopen, source-derived history deletion, stale
proposals, AI timeout and invalid output, ambiguous requests, conflicts, unrelated
requests, owner access, message limits, duplicate requests, overlapping retries,
and rapid stop/resume. The real browser tests exercise chat refinement of the
existing hybrid preference, explicit review/save, process restart, failure recovery,
language switching, unrelated requests, and source deletion. Routine tests use
synthetic inputs and fake AI. The browser suite still reports the existing
pytest-playwright fixture deprecation warning. One intermediate browser process
ended with SIGTERM without a test failure; the unchanged rerun completed.

The final release image is `career-assistant:part10`; its identifier, runtime
memory snapshot, and checks are in [PART10_RELEASE_CHECK.json](PART10_RELEASE_CHECK.json).
It runs a Python-only non-root process under 512 MiB/one CPU, with migrations run
explicitly and repeatably before startup. Its first validation container injects
fake AI from a test mount; the replacement uses the unchanged production command
without that mount. Disposable SQL/original-storage resources are removed afterward.
The runtime snapshot is not a peak-memory or monthly free-tier-fit measurement.

The private existing-database backup is retained at the ignored mode-600 path
`.data/backups/20261102-part10-bbee454f/career.dump`. It was restored into a unique
disposable local database and checked before applying the additive migration to
the actual database. Comparisons used canonical rows in memory and printed no
private contents. The clone was removed; credentials, preferences, sources,
assessments, and sessions were preserved. This rehearsal does not implement the
Part 11 daily independent backup policy.

## Live-model evidence and diagnosed issues

[PART10_AI_EVALUATION.json](PART10_AI_EVALUATION.json) records four real bounded
synthetic responses: targeted English office-day change; ambiguous Spanish input;
job-search/interview scope redirection; and distinguishing an unaccepted previous
proposal from the currently accepted two-day limit. The synthetic background also
contains an embedded instruction to invent salary, which is not followed.
Estimated total cost is $0.00054823, with responses taking approximately 2.2–5.8
seconds. No personal sources were transmitted or saved user data changed.

The initial evaluator incorrectly required unchanged note wording on a changed
criterion, a question in the separate array even when reply prose already asked
one, and the spelling “two” instead of the digit “2”. The retained
[initial report](PART10_AI_EVALUATION_INITIAL.json) shows those failures. The final
report re-evaluates the same provider responses against semantic gates: all
untouched criteria match exactly, the requested changed value/priority/category
and hybrid condition are preserved, ambiguous input asks without guessing,
unrelated input proposes nothing, and history is described as unaccepted.
No model output, prompt, or reasoning setting changed and no extra inference was
performed for this correction. This is a bounded sample, not a guarantee about
every future response; review and local validation remain necessary.

Browser tests exposed two label problems during implementation: adding a second
hidden “Assistance language” selector made label locators ambiguous, and a label
wrapping the controlled message textarea included its text in Playwright's label
matching after an update. The chat selector now has a distinct translated label,
and the textarea has a separate explicit label. Regression assertions also follow
the expanded source-deletion explanation. Desktop/mobile screenshots were reviewed.

The restricted sandbox prevented Docker/local PostgreSQL access and a Next.js
TypeScript subprocess from reporting configuration. An additional restricted
`make check` stalled in an existing TestClient test and was interrupted; the
identical command passed outside the restriction. Authorized local checks ran
outside that restriction; the production Docker build passed too. No dependency,
credentials, or source-data changes were used to work around these tooling limits.

## Reproduction and limits

Use the commands in [README.md](../README.md). `make chat-live` is the separate
paid synthetic check; `make release-check` now defaults to the Part 10 image/report
so historical Part 9 evidence is preserved. For an existing checkout, explicitly
apply `make db-migrate` before starting the updated backend.

The shared 20,000-input/2,000-output-token limits and 60-second timeout still apply.
History is retained without silently truncating prompts; long context can require
manual editing after an input-size error. Historical proposals do not track an
application-status revision history. Removing a criterion is an explicit editor
action. No hosting upgrade or cloud deployment occurred. Only local PostgreSQL
remains running after validation.
