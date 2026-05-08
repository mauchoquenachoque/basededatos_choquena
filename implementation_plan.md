# Enmask - Static Data Masking Platform Implementation Plan

This document outlines the system architecture and implementation steps to build **Enmask**, a Static Data Masking (SDM) platform for hybrid architectures (PostgreSQL and MongoDB).

## User Review Required

> [!CAUTION]
> The backend connects to databases to scan schemas and apply masking. The user must manually set up PostgreSQL and MongoDB local instances and provide the connection credentials in a `.env` file before executing masking jobs, as requested.

## Proposed Changes

We will build the **backend** and **frontend** from scratch following strict SOLID principles, layered architecture, and Clean Code best practices without generating any unit tests or utilizing containers like Docker.

### Backend Overview (FastAPI)

We will use the following specific technologies:
- `FastAPI`, `Uvicorn`, `Pydantic` (Presentation & Application)
- `Motor` (Async MongoDB driver)
- `asyncpg` (Async PostgreSQL driver)
- `Faker` (Realistic data generation)
- `hashlib` (Deterministic masking algorithm)

The backend code will be rigorously divided into layers as per the instructions:

- **1. Presentation**: API REST using FastAPI routers and strict Pydantic schemas.
- **2. Application**: Use Case services like `JobOrchestrator`, `ConnectionService`, and `MaskingService`.
- **3. Domain**: Entities (`MaskingJob`, `MaskingRule`, `ConnectionConfig`), Value Objects, and abstract interfaces for DB and Strategy layers.
- **4. Infrastructure**: Concrete implementation of Repositories (`PostgresConnectionRepo`, `MongoConnectionRepo`, `JobRepo`) and Strategy pattern implementations for Masking (`SubstitutionStrategy`, `HashingStrategy`, etc.).
- **5. Core**: Application configs, centralized logging, exception handling.

### Frontend Overview (React, Vite, TypeScript)

- React JS application constructed using Vite with TypeScript.
- Core logic extracted to custom hooks and an organized `services` folder for REST API calls.
- Routing to manage visually distinct pages: Dashboard/Jobs, Connections, Rules Management.
- CSS best practices for styling (clean, modern interface).

---

### Implementation Progression

#### 1. Setup and Core Configuration
- [NEW] `requirements.txt`
- [NEW] `.env.example`
- [NEW] `backend/app/core/config.py`
- [NEW] `backend/app/core/exceptions.py`
- [NEW] `backend/app/core/logging.py`

#### 2. Domain Layer
- [NEW] `backend/app/domain/entities/...`
- [NEW] `backend/app/domain/value_objects/...`
- [NEW] `backend/app/domain/interfaces/...`

#### 3. Infrastructure Layer
- [NEW] DB Clients: `backend/app/infrastructure/db/postgres_client.py` & `mongodb_client.py`
- [NEW] Masking Strategies: `substitution`, `hashing`, `redaction`, `nullification` strategies.
- [NEW] Repositories: `postgres_connection_repo`, `mongodb_connection_repo`, `job_repo`.

#### 4. Application Layer
- [NEW] DTOs/Schemas: Connection schemas, Rule schemas, Job schemas.
- [NEW] Services: `connection_service.py`, `masking_service.py`, `job_orchestrator.py`

#### 5. Presentation Layer (API Routers)
- [NEW] Endpoints: `connections.py`, `rules.py`, `jobs.py`, `reports.py`
- [NEW] Main Application Initialization: `backend/app/main.py`
- [NEW] FastApi Dependencies: `backend/app/api/deps.py`

#### 6. Frontend Setup and Integration
- Execute `npx create-vite` to scaffold the frontend project.
- Implement types, hooks, API services, components, and application routing to manage connections, define rules, and run jobs.

#### 7. Documentation
- [NEW] `README.md`: Comprehensive setup and execution guide including SQL scripts and commands.

## Open Questions

> [!NOTE]
> Do you have a specific UI framework preference for the frontend (e.g., Material-UI, Tailwind, or completely Vanilla CSS as generally defaulted unless otherwise stated)? Since UI aesthetics are important, I will use a modern, clean design utilizing vanilla CSS unless told otherwise.

## Verification Plan

### Manual Verification
- Launch both FastAPI (`uvicorn`) and React (`vite`) servers successfully.
- Setup a `.env` file manually.
- Perform end-to-end user validations: Register a connection via UI, Create a Masking Rule, Trigger a Job, and observe deterministic masked data outputs crossing both a mock PostgreSQL table and MongoDB collection.
