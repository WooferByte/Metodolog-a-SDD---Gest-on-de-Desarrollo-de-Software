# feature-first-backend Specification

## Purpose
TBD - created by archiving change infrastructure-repo-setup. Update Purpose after archive.
## Requirements
### Requirement: Feature-first backend directory structure

The system SHALL organize backend features as top-level directories under `/backend`, where each feature directory contains its own routers, models, services, and repositories. Features include: auth, usuarios, productos, categorias, ingredientes, pedidos, pagos, direcciones, admin, and refresh_tokens.

#### Scenario: Feature directories exist
- **WHEN** a developer navigates to `/backend`
- **THEN** they find exactly these feature directories: auth/, usuarios/, productos/, categorias/, ingredientes/, pedidos/, pagos/, direcciones/, admin/, refresh_tokens/

#### Scenario: Each feature is self-contained
- **WHEN** a developer opens a feature directory (e.g., `/backend/productos`)
- **THEN** they find subdirectories for models.py, router.py, service.py, and repository.py (or similar structure based on DDD patterns)

#### Scenario: Core infrastructure is separate
- **WHEN** a developer looks for shared utilities and configuration
- **THEN** they find `/backend/core` containing database.py, config.py, security.py, and dependencies.py

#### Scenario: Main entry point is clear
- **WHEN** a developer wants to run the backend
- **THEN** they find `/backend/main.py` as the FastAPI application entry point

### Requirement: No cyclic feature dependencies

The system SHALL enforce that feature A cannot import from feature B if feature B is not explicitly listed as a dependency in feature A's documentation. A developer working on one feature should understand its dependencies without hunting through imports.

#### Scenario: Dependencies are documented
- **WHEN** feature `pedidos` (orders) needs data from `productos` (products)
- **THEN** the dependency is documented in the change proposal or design, not buried in code imports

#### Scenario: Shared utilities are in /core
- **WHEN** a feature needs a utility that multiple features use (e.g., JWT validation, database session management)
- **THEN** the utility is placed in `/backend/core` and imported from there, not from another feature

