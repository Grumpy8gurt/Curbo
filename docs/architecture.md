# Architecture Overview

## System Overview

Sidewalk Surveying and Management Dashboard (Curbo) is planned as a geospatial web platform for viewing city infrastructure layers, collecting annotations, evaluating corridors, and eventually assisting curb-cut review from imagery.

## Component Diagram

```text
Users
  -> Frontend (React + TypeScript dashboard)
    -> Backend API (FastAPI)
      -> PostgreSQL + PostGIS
      -> File/object storage for uploads (future)
      -> ML service for curb-cut detection (mockable at first)

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
- Upload images for future detection workflows
- Surface backend and ML results to planners

## Backend Responsibilities

- Expose REST endpoints for health, layers, annotations, uploads, and reporting
- Validate request payloads and shape GeoJSON responses
- Coordinate spatial queries and corridor analysis
- Manage authentication/authorization later if added
- Provide an integration boundary to the ML service

## Database Responsibilities

- Store infrastructure geometry and related metadata
- Support PostGIS spatial indexing and queries
- Persist user annotations, uploads, detections, and generated report metadata
- Serve as the source of truth for corridor analysis inputs

## ML Responsibilities

- Accept uploaded or referenced street-level imagery
- Return curb-cut detection results and confidence metadata
- Stay mockable during MVP so UI and backend work can proceed independently

## Data Ingestion Responsibilities

- Normalize source datasets into a shared GeoJSON-oriented pipeline
- Load infrastructure layers into PostGIS tables
- Preserve source lineage and refresh workflows for updated city data

## Report Generation Responsibilities

- Assemble corridor summaries from spatial query results
- Produce HTML first and PDF later
- Capture key counts, findings, and map/context snapshots

## MVP Boundaries

- Include only the map dashboard, layer viewing, basic spatial queries, annotations, mocked image upload/detection, and corridor summary planning
- Exclude full production auth, advanced analytics, live model operations, and polished report rendering for now
