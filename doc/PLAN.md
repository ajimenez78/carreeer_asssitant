# High level steps for the firt phase of the project

The first MVP will only afford the job definition step, but ensure that the rest of steps will be supported in the future.

## Part 1: Plan

Enrich this document to plan out each of these parts in detail, with substeps listed out as a checklist to be checked off by the agent, and with tests and success critieria for each. Ensure the user checks and approves the plan.

## Part 2: Clarify

Review the provided documentation and refine the requirements, both functional and non functional to ensure that all of them are perfectly clear. If doubt, make one ore more proposals and ask the user for confirmation. Update the AGENTS.md and PLAN.md accordly keeping them simple.

### User interaction flow
Include in the clarification proposals a more detailed user interaction flow with the system.

## Part 3: Backend scaffold

Set up the infrastructure, the backend in backend/ with the selected technology. Provide a way to start and stop the backend. This should serve example static HTML to confirm that a 'hello world' example works running locally and also make an API call.

## Part 4: Frontend scaffold

Scaffold the NextJS frontend in frontend/. Also provide a way to start and stop

## Part 5:

Propose a database schema for the system, supporting persistence for the job description, job application processes and every stuff that will need to be persisted

## Part 6: AI connectivity

allow the backend to make an AI call via Amazon Bedrock. Test connectivity with a simple "2+2" test and ensure the AI call is working.

## Part 7 Backend

Add API routes to allow the backend to build the ideal job description. Use AI to assist clarification to the user. Test this thoroughly with backend unit tests. The database should be created if it doesn't exist.

## Part 8 Frontend

Build the forntend interacion for the Job definition flow. Do not still connect to backend. Use MOCK request for know. Test the flow thoroughly.

## Part 9: Frontend + Backend

Now have the frontend actually use the backend API, so that the app is a proper Job definition interface board. Test very throughly.

## Part 10:

Add an AI assistan in the form of a Chatbot to help the user provide feedback to the process in the form of opened prompts.
