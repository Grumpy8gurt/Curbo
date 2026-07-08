# Sprint 2 AI Implementation And Review Note

## How AI Helped Implementation

AI helped accelerate the repository setup, frontend scaffolding, backend route integration, ML mock service wiring, and engineering review of contract mismatches across the stack. It was especially useful for:

- organizing the frontend into components and API modules
- drafting mock-first FastAPI routes and response schemas
- identifying integration mismatches between frontend expectations and backend responses
- drafting supporting documentation after the implementation was stabilized

## How AI Helped Review

AI was also used as a review assistant to inspect the current repository state, compare the frontend API layer to backend routes, verify the ML handoff shape, and summarize what was working versus what remained risky.

## One Suggestion I Accepted

I accepted the suggestion to add compatibility handling between frontend and backend request/response shapes instead of trying to rewrite the whole frontend or backend. This kept the Sprint 2 scope focused while making the prototype coherent enough to run and explain.

## One Suggestion I Rejected Or Postponed

I postponed replacing the mock-first data flow with full Postgres/PostGIS persistence. That would be valuable later, but it was too large for the current Sprint 2 feature slice and would have distracted from demonstrating one working client/server interaction.

I also decided against building out a more fleshed-out ML layer at this stage. The current mock ML boundary is enough to demonstrate how the system would connect to detection logic later, and expanding that part further now would likely push the project beyond a realistic Sprint 2 scope.

## One Verification Step After Review

After the AI-assisted review surfaced integration drift, I verified the result by running:

- `cd frontend && npm run build`
- `cd backend && pytest`
- `cd ml && pytest`

I also confirmed that both backend and ML services could start with `uvicorn`, and I used targeted smoke checks for key backend and ML routes.

Running the prototype with docker showed that the service doesn't really work at the current moment, the map doesn't render, a lot of the text is redundant, and the back  

## Final Responsibility

AI assisted with implementation speed, issue discovery, and documentation drafting, but final engineering decisions remained my responsibility. I chose which suggestions to keep, which to postpone, and whether the results were acceptable based on build output, test results, startup behavior, and the actual state of the repository.
