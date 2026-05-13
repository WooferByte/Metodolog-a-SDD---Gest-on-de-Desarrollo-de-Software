## MODIFIED Requirements

### Requirement: Get single product by ID
The system SHALL return a single active product by its primary key. The response SHALL include the product's `categorias` list (list of CategoriaCompacta with id, nombre, padre_id) and the product's `ingredientes` list (list of IngredienteCompacto with id, nombre, es_alergeno, es_removible). If the product does not exist or is soft-deleted, the system SHALL return 404. No authentication is required.

#### Scenario: Existing product returns 200 with categories and ingredients
- **WHEN** GET /api/v1/productos/{id} is called with a valid product ID
- **THEN** response is 200 with a ProductoResponse that includes both the categorias list and the ingredientes list populated from their respective pivot tables

#### Scenario: Product with no categories and no ingredients returns empty lists
- **WHEN** GET /api/v1/productos/{id} is called with a valid product ID that has no category or ingredient associations
- **THEN** response is 200 with categorias: [] and ingredientes: []

#### Scenario: Non-existent product returns 404
- **WHEN** GET /api/v1/productos/{id} is called with a product ID that does not exist
- **THEN** response is 404 Not Found (RFC 7807)

#### Scenario: Soft-deleted product returns 404
- **WHEN** GET /api/v1/productos/{id} is called with the ID of a soft-deleted product (eliminado_en is not null)
- **THEN** response is 404 Not Found
