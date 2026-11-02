# Persistent assistant alongside the workflow

Requested on 2026-11-02 after the initial Part 10 delivery. This supersedes the
numbered **06 Chat** step. The same assistant entry point is a product requirement
for subsequent phases; current assistant capabilities remain within job definition.

The **Chat with assistant / Hablar con el asistente** launcher stays at the bottom
right of every workspace step. It opens a floating, nonmodal panel without changing
the current step. Minimize it or press Escape to return keyboard focus to the
launcher. Conversation and composer text remain mounted when minimized or navigating;
the panel has its own scrollable transcript and adapts to small screens. New replies
scroll the transcript to the latest turn. English/Spanish switching preserves text.

Chat is available from the initial Describe screen. If no role has been saved,
the first Send explicitly starts a saved draft using that message, then requests
an assistant reply. The panel explains this before sending. Existing description
or criterion edits remain in the editor; they are not implicitly saved. If AI fails
after creating the initial draft, both the draft and typed message remain available
for retry. This reuses the existing save/chat APIs and requires no migration.

Users can send chat messages while editor changes or earlier structured suggestions
are pending. Chat uses saved context. It preserves pending edits and marks earlier
proposals stale when the conversation changes their context. Reviewing a new chat
proposal remains disabled until pending edits/suggestions are saved or discarded,
so a review cannot silently overwrite them. Review opens the existing editor,
minimizes the panel, and focuses its heading; applying changes still requires Save.
Stop/resume and source/definition deletion retain the Part 10 behavior.

The reusable `AssistantDock` component owns only the assistant's presentation and
keyboard behavior. Workspace state supplies the current context and review actions,
independent of its numbered-step selection. Later product phases should retain this
shared presentation and extend its supported tasks as those phases are implemented.
No unused future tools, routes, or agent architecture were introduced.

Validation on 2026-11-02:

- Frontend ESLint, TypeScript, and static production build pass.
- All 20 frontend component/client/catalog tests and 20 backend-schema payload
  checks pass; HTTP shapes are unchanged.
- All 38 desktop/mobile mock browser tests pass. Expanded chat cases cover access
  from each of the five steps, minimizing/Escape and restored focus, composer
  persistence, first-message startup and AI failure recovery, and sending while
  structured proposals/manual changes are pending. The eight chat cases also pass
  after the final transcript/composer layout adjustment, including checks that
  Send remains in the viewport after restoring a conversation.
- All 13 real frontend/API/PostgreSQL browser tests pass; the separately paid live
  workflow is skipped in ordinary runs. The added real test starts a draft through
  chat and verifies conversation across navigation and reload.
- The combined production-image workflow and replacement check pass with the
  floating panel. Conversation, definition, sources, session, summary, and pause
  survive replacement. See [ASSISTANT_DOCK_RELEASE_CHECK.json](ASSISTANT_DOCK_RELEASE_CHECK.json)
  for the final image identifier and measured runtime snapshot.
- Ruff and `git diff --check` pass. Desktop/mobile screenshots were reviewed.

New browser assertions initially counted HTTP requests in mock mode, which performs
no network calls, and used label matching on an existing textarea whose label text
includes its value. The assertions now inspect the persisted mock conversation and
use the control's accessible role. No product behavior was changed to satisfy those
incorrect test assumptions. A separate viewport assertion then exposed that the
composer could scroll below the panel; the layout now reserves its space and
scrolls the transcript independently, with a scrollable fallback for short screens.

Provider prompts/model settings and backend persistence semantics are unchanged,
so no new paid inference calls were needed. Production SQL or personal documents
were not changed. The local database service remains running; test services and
storage are disposable. Hosted deployment remains Part 11. For an existing Docker
application, `make up` rebuilds the combined image with the new UI; development
servers pick up the source change, while static previews use the refreshed export.
