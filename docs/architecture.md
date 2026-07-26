# Architecture Overview

## System Overview

Sidewalk Surveying and Management Dashboard (CURBO) is planned as a geospatial web platform for viewing city infrastructure layers, collecting annotations, and evaluating corridors.

## Component Diagram

```text
Users
  -> Frontend (React + TypeScript dashboard)
    -> Backend API (FastAPI)
      -> PostgreSQL + PostGIS

External GeoJSON / city datasets
  -> Data ingestion scripts and backend import workflows
    -> PostgreSQL + PostGIS

Backend
  -> Report generation pipeline (future HTML/PDF outputs)
```

## Frontend Responsibilities

- Render the map dashboard and layer toggles
- Display GeoJSON layers and corridor summaries
- Support annotation creation and editing workflows
- Surface backend results to planners

## Backend Responsibilities

- Expose REST endpoints for health, layers, annotations, and reporting
- Validate request payloads and shape GeoJSON responses
- Coordinate spatial queries and corridor analysis
- Manage authentication/authorization later if added

## Database Responsibilities

- Store infrastructure geometry and related metadata
- Support PostGIS spatial indexing and queries
- Persist user annotations and generated report metadata
- Serve as the source of truth for corridor analysis inputs

## Data Ingestion Responsibilities

- Normalize source datasets into a shared GeoJSON-oriented pipeline
- Load infrastructure layers into PostGIS tables
- Preserve source lineage and refresh workflows for updated city data

## Report Generation Responsibilities

- Assemble corridor summaries from spatial query results
- Produce HTML first and PDF later
- Capture key counts, findings, and map/context snapshots

## MVP Boundaries

- Include only the map dashboard, layer viewing, basic spatial queries, annotations, and corridor summary planning
- Exclude full production auth, advanced analytics, and polished report rendering for now
