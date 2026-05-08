# xss-sanitization Specification

## Purpose
TBD - created by archiving change backend-input-validation-sanitization. Update Purpose after archive.
## Requirements
### Requirement: Shared sanitization utility
The system SHALL provide a shared function `sanitize_text(value: str) -> str` in `backend/core/sanitize.py` that strips HTML and script tags from any string input.

#### Scenario: HTML tags stripped from input
- **WHEN** the sanitize_text function receives a string containing HTML tags (e.g., `"<script>alert('xss')</script>Hello"`)
- **THEN** it returns the string with all tags removed (e.g., `"Hello"`)

#### Scenario: Clean text passed through unchanged
- **WHEN** the sanitize_text function receives a string with no HTML tags (e.g., `"Manzana roja"`)
- **THEN** it returns the same string unchanged

#### Scenario: None/empty input handled gracefully
- **WHEN** the sanitize_text function receives None or an empty string
- **THEN** it returns the same value without raising an exception

### Requirement: XSS sanitization applied on all free-text schema fields
The system SHALL apply the `sanitize_text` utility via Pydantic v2 `field_validator` (mode='before') on all free-text fields across request schemas.

Free-text fields that MUST be sanitized:
- `nombre` in: UsuarioCreate, ProductoCreate, ProductoUpdate, CategoriaCreate, IngredienteCreate
- `descripcion` in: ProductoCreate, ProductoUpdate, CategoriaCreate
- `alias`, `linea1`, `referencia` in: DireccionCreate
- `observacion` in: PedidoCreate

#### Scenario: Script tag stripped from producto nombre
- **WHEN** a client sends `{"nombre": "<script>evil()</script>Pizza", ...}` to the product endpoint
- **THEN** the schema stores `nombre = "Pizza"` after sanitization, validation passes, and no script is persisted

#### Scenario: Bold tag stripped from categoria descripcion
- **WHEN** a client sends `{"nombre": "Bebidas", "descripcion": "<b>Refrescos</b>"}` to the category endpoint
- **THEN** the schema stores `descripcion = "Refrescos"` after sanitization

#### Scenario: Sanitization runs before length validation
- **WHEN** a string field contains tags that, when stripped, fall within the valid length range
- **THEN** the schema accepts the sanitized value (sanitize runs in mode='before')

### Requirement: SQL injection prevention documented
The system SHALL document that SQLModel's parametrized queries prevent SQL injection; no additional escaping is required in schemas.

#### Scenario: Documentation present in sanitize.py
- **WHEN** a developer reads `backend/core/sanitize.py`
- **THEN** there is a docstring or comment clarifying that SQL injection is handled by the ORM layer, and this utility is for XSS/HTML only

