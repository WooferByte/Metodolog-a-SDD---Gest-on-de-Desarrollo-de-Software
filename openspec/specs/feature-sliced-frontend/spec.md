# feature-sliced-frontend Specification

## Purpose
TBD - created by archiving change infrastructure-repo-setup. Update Purpose after archive.
## Requirements
### Requirement: Feature-Sliced Design directory structure for React

The system SHALL organize frontend code following Feature-Sliced Design (FSD) architecture with the following layers: app/, pages/, widgets/, features/, entities/, shared/. This structure ensures scalability and maintainability as the frontend grows.

#### Scenario: Core layers exist
- **WHEN** a developer navigates to `/frontend/src`
- **THEN** they find exactly these directories: app/, pages/, widgets/, features/, entities/, shared/

#### Scenario: Each layer has clear responsibilities
- **WHEN** a developer opens `/frontend/src/features`
- **THEN** they find feature directories (UserAuth/, ProductCatalog/, ShoppingCart/, PaymentCheckout/, etc.) each containing components, hooks, types, and styles related to that feature

#### Scenario: Shared utilities are centralized
- **WHEN** a developer needs a utility used across multiple features (e.g., axios instance, constants, types)
- **THEN** they find it in `/frontend/src/shared` with subdirectories for api/, hooks/, types/, utils/, components/

#### Scenario: Entity models are consistent
- **WHEN** a developer needs to model a Product, User, or Order
- **THEN** they find TypeScript interfaces and constants in `/frontend/src/entities` to ensure consistency across the app

#### Scenario: Pages route to features
- **WHEN** a developer opens a page component (e.g., `/frontend/src/pages/ProductCatalogPage.tsx`)
- **THEN** it imports and composes feature components from `/frontend/src/features`, not implementing business logic directly

### Requirement: No direct imports across feature boundaries

The system SHALL NOT allow a feature to import from another feature's internal files (e.g., ProductCatalog feature should not import ProductCard directly from ShoppingCart). Features communicate through entities and shared utilities only.

#### Scenario: Features use public interfaces
- **WHEN** feature `ShoppingCart` needs data from feature `ProductCatalog`
- **THEN** it uses the public entity models from `/frontend/src/entities/Product`, not internal components from ProductCatalog

#### Scenario: Components are properly exported
- **WHEN** a feature exposes a component for reuse
- **THEN** it is exported from a public `index.ts` file, not imported directly from internal subdirectories

