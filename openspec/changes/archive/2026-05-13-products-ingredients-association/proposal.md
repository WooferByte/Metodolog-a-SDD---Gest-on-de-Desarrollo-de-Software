## Why

Products in the food store need to expose their ingredient composition so that customers can make informed decisions (allergens, dietary restrictions) and customize orders by removing specific ingredients. The `ProductoIngrediente` pivot table already exists in the schema but has no API surface yet. This change wires up the association management endpoints and adds the `?excluirAlergenos` filter to the product listing so downstream features (catalog UI, checkout personalization) have the data they need.

## What Changes

- New sub-resource endpoints under `/api/v1/productos/{id}/ingredientes`:
  - `GET` — list ingredients associated with a product (public)
  - `PUT` — atomically replace the full ingredient set (STOCK or ADMIN) — includes `es_removible` per association
  - `DELETE /{ing_id}` — remove a single ingredient association (STOCK or ADMIN)
- `GET /api/v1/productos/{id}` enriched with `ingredientes: list[IngredienteCompacto]` (including `es_removible`)
- `GET /api/v1/productos/` gains `?excluirAlergenos=1,3,7` query parameter — comma-separated list of allergen ingredient IDs; products containing ANY of those allergens are excluded from the listing
- New `ProductoIngredienteRepository` (dedicated pivot repo, mirrors `ProductoCategoriaRepository`)
- UoW wired with `producto_ingredientes` using the new dedicated repository

## Capabilities

### New Capabilities

- `products-ingredients-association`: Management of the `ProductoIngrediente` N:M pivot — CRUD endpoints for product-ingredient associations, `es_removible` flag per link, and `?excluirAlergenos` filter on the product catalog.

### Modified Capabilities

- `products-crud`: `GET /api/v1/productos/{id}` response shape gains `ingredientes` field; `GET /api/v1/productos/` gains `?excluirAlergenos` query parameter.

## Impact

- **Backend — new files**: `productos/repository.py` (add `ProductoIngredienteRepository` class), `backend/tests/test_productos_ingredientes.py`
- **Backend — modified files**: `productos/schemas.py` (add `IngredienteCompacto`, `ProductoIngredienteSetRequest`, update `ProductoResponse`), `productos/service.py` (new service functions), `productos/router.py` (new sub-resource routes), `infrastructure/uow.py` (upgrade `producto_ingredientes` property to use `ProductoIngredienteRepository`)
- **No model changes**: `ProductoIngrediente` already exists in `core/models.py`
- **No migration needed**: table `producto_ingrediente` already created by prior migration
- **API contract**: Adding new fields to `ProductoResponse` is non-breaking; new endpoints and query param are additive
- **Dependencies satisfied**: `products-crud-core` ✅, `ingredients-crud-allergens` ✅
