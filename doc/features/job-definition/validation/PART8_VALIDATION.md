# Part 8: mocked frontend

Implemented and verified locally on 2026-11-02. Real frontend/backend integration
remains Part 9. No hosted resources or OpenAI inference were used in this part.

## Delivered behavior

- Four responsive steps: description, optional background, clarification, and
  structured review/save. English and Spanish UI accepts English and Spanish content.
  A persistent header switcher updates labels, navigation, status/error feedback,
  prompts, document language, title, and metadata without changing user content.
- Explicit saving of incomplete drafts or ready definitions; saved mock work
  reopens after a browser reload. Definition edits show unsaved status and warn
  before discarding. Step navigation preserves unfinished source/answer input.
- Document, public-link, and pasted-text inputs; extraction status, retry, and
  upload/paste fallback. Background review includes extracted text, provenance,
  evidence, editable facts, and explicit acceptance independent of definition saves.
- Up to three clarification questions per round, answer/skip/unknown actions,
  and independently saved answer states. Suggested criteria remain proposals.
- Editable criteria across all nine contract categories, with mandatory,
  preferred, and excluded priorities; text, boolean, number, text-list, unknown,
  structured compensation, and on-site limit values. Nullable pay details and
  office-day periods remain unknown until explicitly supplied.
- Pending proposals become stale when answers or source context change. Edited
  criteria remain available for review; applying stale suggestions is blocked.
  Users can discard them or explicitly retain them as unsaved manual edits.
- Source deletion explains context invalidation and preserves accepted criteria.
  Whole-definition deletion requires confirmation. Both use the API cleanup shape.
- Loading, empty, validation, upload, assistant, storage, and request-error states
  preserve input. Status/error feedback stays visible while scrolling long forms.
  Controls have labels, visible focus, keyboard access, and responsive layouts.

## Request boundary and simulation limits

`frontend/src/lib/contracts.ts` mirrors the Part 7 shapes; `client.ts` sends the
documented paths, methods, JSON bodies, multipart uploads, and error envelopes
through an injected transport. The workspace uses only `mock-transport.ts`.
There is no fetch transport or live-backend mode in Part 8.

The mock persists one current definition and sources in browser local storage
under `career-assistant:mock:v1`. No real authentication, durable original-file
storage, original downloads, backups, PDF/Word parser, public-page fetch, or AI
inference is provided by this preview. Markdown and pasted text are read locally;
binary documents/public pages use synthetic extraction text. Background proposals
quote fixture/source lines. Job suggestions are deterministic fixtures and do not
evaluate language understanding or interpret answers as an actual model would.
A visible notice identifies the simulation. Use synthetic content for previewing.

Mock file limits match the agreed five files/10 MiB each; validation covers
unsupported and empty files, text bounds, criteria, salary ordering/currency,
and nullable on-site periods. A LinkedIn/restricted URL simulates retrieval
failure; a filename containing `scanned` simulates missing extractable text.
Retrying an inaccessible fixture retains its failed state and fallback message.

The opaque proposal fingerprint follows the API's 64-hex-character contract and
models stale-context rejection; it is not the backend's fingerprint algorithm.
Part 9 must consume the server's actual fingerprints and authentication behavior.

For deterministic failure tests, session storage key
`career-assistant:mock-failure` accepts one next-operation failure: `save`, `ai`,
`upload`, `source-review`, `answer`, or `read`. The control is internal to the
mock adapter and is not exposed as a product setting.

## Validation evidence

| Check | Result |
| --- | --- |
| `make frontend-check` | ESLint, route types, TypeScript, and static production export pass. |
| `make frontend-test` | 12 rendered-component, validation, request-boundary, mock-workflow, and translation-catalog tests pass. |
| `make frontend-contract` | The same 12 tests pass; 15 synthetic request/response payloads validate against the existing backend Pydantic models without HTTP, database access, or inference. |
| `make frontend-e2e` | 22 Chromium tests pass: eleven journeys/checks at desktop and Pixel 7 sizes. When a preview is already running, use `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3000 make frontend-e2e`. |
| Static-export browser smoke | Desktop/mobile draft save → reload passes against a plain static server, with no backend requests or browser errors. |
| Visual review | Desktop/mobile screenshots reviewed; no horizontal overflow, clipped form controls, or hidden save/error feedback in the tested workflows. |

Browser coverage includes document upload, evidence review and fact correction,
clarification, all answer states, unapplied/stale proposals, explicit application,
save/reload/refinement, every editor value type, ready status, source/definition
deletion, keyboard navigation, and unfinished input across steps. Failure checks
cover saves, AI, upload, inaccessible URL/retry/paste fallback, source review,
answers, invalid compensation, empty description, and unavailable browser storage.
The full journey asserts zero `/api/`/OpenAI requests; workflow tests reject
browser exceptions and console errors. Unit tests also cover the five-file limit,
oversized/unsupported/empty uploads, stale rejection, and failed storage writes.

No new libraries were added. Component checks use React server rendering and the
existing Playwright runner; interactive behavior is exercised in browser tests.
These results establish bounded workflow coverage, not an 80% frontend statement
coverage measurement or real-service acceptance. Backend logic is unchanged;
the backend suite was not rerun for this frontend-only part.

## Diagnosed issues

The sandbox rejected the localhost test server with `listen EPERM`; a sandboxed
Next.js build also failed while reading its TypeScript-config subprocess output.
The same checks/build and browser tooling pass outside that sandbox. No application
workaround was introduced. Existing `NO_COLOR`/`FORCE_COLOR` tooling warnings remain.

Initial browser checks exposed two locator mismatches: Next.js adds its own
route-announcer alert, and an implicit select label includes option text when
looked up by label text. Tests now scope alerts to the workspace and locate the
boolean selector by its accessible role/name. A genuine React warning came from
reusing the file input's DOM node as a controlled source-name input when switching
source types; keyed input groups fix it. Console-error checks cover that path.

The bilingual extension was requested on 2026-11-02. Its browser cases switch
languages during description, fact, answer, and structured-criterion editing;
check Spanish validation, assistant/source errors and deletion prompts; verify
language persistence after reload; preserve literal user text even when it matches
an English UI message; and cover invalid stored locales and unavailable preference
storage. Spanish assistance requests retain the API's `Spanish` enum value even
though the visible option reads `Español`. Previously generated/source text remains
in its original language. Desktop/mobile Spanish screenshots were reviewed.

## Adding another interface language

Messages live in `frontend/src/lib/i18n/catalogs.ts`. English source messages act
as catalog keys. Add a complete translated `Messages` dictionary and a locale
entry with its native name and supported default assistance language. The switcher
and runtime locale validation derive their options from this registry. Type checks
and catalog tests enforce completeness and matching interpolation placeholders.
The React provider owns locale state; individual screens keep their current state
when it changes. No routing changes, backend calls, or new libraries are required.
The static export initially renders English and restores a remembered locale after
hydration; English is the default when no supported preference is available.

README setup/test commands and the Part 8 checklist are updated. Authentication,
real processing/inference, combined-image integration, and cloud operations remain
in their planned later parts.
