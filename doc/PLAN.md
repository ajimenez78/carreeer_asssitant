# Career assistant roadmap

Updated: 2026-11-03. The current feature is **business requirement #2: job finding**.
This planning request does not start implementation or authorize new services.

| Feature | Status | Execution plan |
| --- | --- | --- |
| 1. Job definition | Implemented; working cloud preview approved on 2026-11-03 with accepted operational limitations | [Completed MVP plan](features/job-definition/PLAN.md) |
| 2. Job finding | Planned; product and source-access decisions remain open | [Job-finding implementation plan](features/job-finding/PLAN.md) |
| 3. Closing the gap | Future feature | Plan when this feature starts |
| 4. Application tracking and interview preparation | Future feature | Plan when this feature starts |
| 5. Starting a job and further growth | Future feature | Plan when this feature starts |

Start new feature work with the job-finding plan. Its 14 small parts cover
requirements, source feasibility, offer intake, scoring, active search,
notifications, feedback, assistant integration, local validation and release.
Parts 1–2 settle the decisions needed before implementing external discovery.
The manual-intake path can progress while provider access is being resolved;
it does not by itself complete requirement #2.

Build and maintain meaningful behavior and regression tests within each
implementation part. Planning-only parts use acceptance walkthroughs and evidence.
Use coverage to identify relevant gaps; a percentage target does not determine
completion. The final validation part integrates tests already built along the way.

The existing floating assistant, saved role definition, explicit review/save flow,
and English/Spanish support remain product-wide requirements. The same functional
chat assistant must be available throughout job finding from its first UI slice,
preserving conversation and typed input across views and minimizing. Add relevant
chat capabilities as each slice ships; Part 12 completes their integration.
Keep the current
Next.js static export, FastAPI/Python runtime, Render PostgreSQL, private R2
storage and direct backend OpenAI integration. Validate locally before cloud
deployment. No paid upgrade is authorized.

The approved preview's database expires on **2 December 2026 at 17:45 Madrid
time**. Preserve the workspace before that deadline. Outstanding usage,
notification and automatic-backup-delivery checks remain visible in
[operational follow-ups](operations/FOLLOW_UPS.md); starting a feature does not
establish that those checks passed.

See the [documentation index](README.md) for specifications, architecture,
operations, historical validation and the documentation conventions used for
each feature.
