# Agent Responsibilities

## Initial Repository Agent

- Create the monorepo structure
- Add shared documentation, sample data, and bootstrap scripts
- Define contracts and boundaries for specialized agents
- Do not deeply implement frontend, backend, database, or ML business logic

## Frontend Agent

- Build the React + TypeScript dashboard
- Implement map rendering, layer toggles, uploads, and annotation UX
- Follow the documented API contracts and environment conventions

## Backend Agent

- Implement the FastAPI service
- Add persistence, spatial querying, upload handling, and report orchestration
- Keep the API aligned with the contract documents or update them deliberately

## ML Agent

- Implement the curb-cut detection service and its mockable boundary
- Define model input/output expectations and inference workflow
- Keep early integration simple enough for local development

## Supervisor/Integration Agent

- Coordinate shared assumptions across teams
- Resolve integration gaps between frontend, backend, database, and ML
- Add end-to-end checks, compose workflows, and update documentation when contracts shift
