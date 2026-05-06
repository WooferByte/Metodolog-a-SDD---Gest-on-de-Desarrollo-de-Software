# Specification: Domain Entities – Products & Catalog

Product catalog entities: Categoria, Producto, Ingrediente, and N:M relationship tables.

## ADDED Requirements

### Requirement: Categoria Entity with Hierarchical Self-Reference

The system SHALL support hierarchical product categories using parent-child relationships via self-referencing foreign key.

#### Scenario: Create root category
- **WHEN** Categoria created with:
  - `nombre` (unique per parent)
  - `descripcion`
  - `padre_id` (NULL for root categories)
  - `orden` (sort order, optional)
- **THEN** category stored with `padre_id = NULL` (root)
- **AND** `creado_en`, `actualizado_en` set to current UTC
- **AND** `eliminado_en` set to NULL (active)

#### Scenario: Create subcategory
- **WHEN** Categoria created with `padre_id` = existing parent category ID
- **THEN** parent category must exist in database
- **AND** child category linked via FK constraint
- **AND** hierarchical depth allowed: unlimited (e.g., Beverages → Hot → Coffee → Espresso)

#### Scenario: Enforce category name uniqueness per parent
- **WHEN** attempt to create two categories with same `nombre` under same `padre_id`
- **THEN** unique constraint violation: no duplicate names under same parent allowed
- **AND** same name allowed under different parents (e.g., "Bundle" under "Pizzas" AND "Desserts")

#### Scenario: Query category hierarchy
- **WHEN** application queries child categories of parent
- **THEN** query: `SELECT * FROM categoria WHERE padre_id = ? AND eliminado_en IS NULL`
- **AND** child categories returned in `orden` sequence

#### Scenario: Soft delete category
- **WHEN** `categoria.eliminado_en` set to current timestamp
- **THEN** category invisible in product listings
- **AND** products in this category may still exist (FK does NOT cascade soft delete)
- **AND** child categories remain (parent soft-delete independent of children)

### Requirement: Producto Entity with Price, Stock, Availability, Soft Delete

The system SHALL store product information with pricing, inventory tracking, and soft deletion.

#### Scenario: Create producto
- **WHEN** Producto created with:
  - `nombre` (product name)
  - `descripcion` (optional markdown)
  - `sku` (stock keeping unit, unique)
  - `precio` (current selling price in ARS)
  - `costo` (cost for margin calculation, optional)
  - `stock` (quantity on hand)
  - `minimo_stock` (reorder threshold)
  - `categoria_id` (primary FK)
  - `disponible` (boolean; default true)
- **THEN** product stored with all fields
- **AND** `creado_en`, `actualizado_en` set to current UTC
- **AND** `eliminado_en` set to NULL

#### Scenario: Update producto price
- **WHEN** price changed (e.g., promotional discount)
- **THEN** new price stored; `actualizado_en` updated to current UTC
- **AND** existing orders unaffected (orders use price snapshot, not live price)

#### Scenario: Track availability
- **WHEN** `disponible` set to false
- **THEN** product hidden from customer listings
- **AND** existing orders can still reference product (historical records preserved)
- **AND** `stock` may still be > 0 (product temporarily unavailable, not deleted)

#### Scenario: Soft delete producto
- **WHEN** `producto.eliminado_en` set to current timestamp
- **THEN** product invisible in normal queries
- **AND** historical orders referencing this product still readable (foreign key intact, soft-delete independent)

#### Scenario: Query available products
- **WHEN** customer browses catalog
- **THEN** query: `SELECT * FROM producto WHERE eliminado_en IS NULL AND disponible = true AND stock > 0`
- **AND** products listed by category with prices

### Requirement: Ingrediente Entity with Allergen Flag

The system SHALL store ingredients with allergen information for compliance and customer notifications.

#### Scenario: Create ingrediente
- **WHEN** Ingrediente created with:
  - `nombre` (e.g., "Mozzarella", "Gluten")
  - `es_alergeno` (boolean; default false)
  - `descripcion` (optional)
- **THEN** ingredient stored
- **AND** `creado_en` set to current UTC

#### Scenario: Flag ingredient as allergen
- **WHEN** `es_alergeno = true` set on Ingrediente
- **THEN** products containing this ingredient must show allergen warning in API response
- **AND** customer can filter products: "exclude ingredients with es_alergeno = true"

#### Scenario: Query allergen information
- **WHEN** application prepares order response
- **THEN** query allergen ingredients: `SELECT i.* FROM ingrediente i JOIN producto_ingrediente pi ON i.id = pi.ingrediente_id WHERE pi.producto_id = ? AND i.es_alergeno = true`
- **AND** list of allergen warnings included in response

### Requirement: N:M Pivot – ProductoCategoria

The system SHALL support products in multiple categories via many-to-many relationship.

#### Scenario: Link producto to categoria
- **WHEN** ProductoCategoria record created with `producto_id` and `categoria_id`
- **THEN** both FKs validated; must exist
- **AND** composite primary key `(producto_id, categoria_id)` prevents duplicates
- **AND** product now appears in two categories (primary via `producto.categoria_id`, secondary via `producto_categoria.categoria_id`)

#### Scenario: Query products in category
- **WHEN** application queries products in a category
- **THEN** join both sources:
  - Direct: `SELECT * FROM producto WHERE categoria_id = ? AND eliminado_en IS NULL`
  - Indirect: `SELECT p.* FROM producto p JOIN producto_categoria pc ON p.id = pc.producto_id WHERE pc.categoria_id = ? AND p.eliminado_en IS NULL`
- **AND** union results; no duplicates if product in multiple categories

### Requirement: N:M Pivot – ProductoIngrediente with Removibility

The system SHALL link products to ingredients with removibility flag for customization.

#### Scenario: Link producto to ingrediente
- **WHEN** ProductoIngrediente record created with:
  - `producto_id` (FK)
  - `ingrediente_id` (FK)
  - `es_removible` (boolean; default false)
- **THEN** both FKs validated
- **AND** composite primary key `(producto_id, ingrediente_id)` prevents duplicate links
- **AND** `es_removible = true` indicates customer can exclude this ingredient (e.g., "no onions")

#### Scenario: Customer excludes ingredient
- **WHEN** DetallePedido created with `excluded_ingredients = [1, 3, 5]` (JSON array of ingredient IDs)
- **THEN** only ingredients with `es_removible = true` allowed in exclusion
- **AND** if `es_removible = false` for any excluded ingredient, validation error returned

#### Scenario: Query product ingredients
- **WHEN** application builds product detail response
- **THEN** query: `SELECT i.*, pi.es_removible FROM ingrediente i JOIN producto_ingrediente pi ON i.id = pi.ingrediente_id WHERE pi.producto_id = ? ORDER BY pi.es_removible DESC`
- **AND** response includes list of ingredients with removibility flags
