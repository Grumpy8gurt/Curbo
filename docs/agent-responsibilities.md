# Agent Responsibilities

## Initial Repository Agent

- Create the monorepo structure
- Add shared documentation, sample data, and bootstrap scripts
- Define contracts and boundaries for specialized agents
- Do not deeply implement frontend, backend, or database business logic

## Frontend Agent

- Build the React + TypeScript dashboard
- Implement map rendering, layer toggles, and annotation UX
- Follow the documented API contracts and environment conventions

## Backend Agent

- Implement the FastAPI service
- Add persistence, spatial querying, and report orchestration
- Keep the API aligned with the contract documents or update them deliberately

## Supervisor/Integration Agent

- Coordinate shared assumptions across teams
- Resolve integration gaps between frontend, backend, and database
- Add end-to-end checks, compose workflows, and update documentation when contracts shift
