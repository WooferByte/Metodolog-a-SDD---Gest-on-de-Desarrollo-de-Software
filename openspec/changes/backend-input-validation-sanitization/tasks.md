## 1. Shared Sanitization Utility

- [x] 1.1 Create `backend/core/sanitize.py` with `sanitize_text(value: str | None) -> str | None` using `re.sub(r'<[^>]+>', '', value)` to strip all HTML tags
- [x] 1.2 Add module docstring to `sanitize.py` clarifying that this is for XSS/HTML only and that SQL injection is handled by SQLModel parametrized queries
- [x] 1.3 Export `sanitize_text` from `backend/core/__init__.py`

## 2. Auth Schemas

- [x] 2.1 Create `backend/auth/schemas.py` with `LoginRequest(email: EmailStr, password: str = Field(min_length=1))`
- [x] 2.2 Add `RegisterRequest` with `email: EmailStr`, `password: str = Field(min_length=8, max_length=128)`, `nombre: str = Field(min_length=1, max_length=100)`, `apellido: Optional[str] = Field(default=None, max_length=100)`
- [x] 2.3 Add `TokenResponse` with `access_token: str`, `refresh_token: str`, `token_type: str = "bearer"`
- [x] 2.4 Add `RefreshRequest` with `refresh_token: str = Field(min_length=1)`
- [x] 2.5 Apply `@field_validator('nombre', 'apellido', mode='before')` on RegisterRequest calling `sanitize_text`

## 3. Usuarios Schemas

- [x] 3.1 Create `backend/usuarios/schemas.py` with `UsuarioCreate` (same fields as RegisterRequest plus optional `telefono: str = Field(default=None, max_length=20)`)
- [x] 3.2 Add `UsuarioUpdate` with all optional fields: `nombre`, `apellido`, `telefono`, `activo`
- [x] 3.3 Add `UsuarioResponse` (public-safe fields: `id`, `email`, `nombre`, `apellido`, `activo`, `creado_en` — NO `hashed_password`)
- [x] 3.4 Apply `@field_validator('nombre', 'apellido', mode='before')` on UsuarioCreate and UsuarioUpdate calling `sanitize_text`

## 4. Productos Schemas

- [x] 4.1 Create `backend/productos/schemas.py` with `ProductoCreate`: `nombre: str = Field(min_length=1, max_length=255)`, `descripcion: Optional[str] = None`, `precio_base: Decimal = Field(gt=0)`, `stock_cantidad: int = Field(default=0, ge=0)`, `disponible: bool = True`, `imagen_url: Optional[str] = None`
- [x] 4.2 Add `ProductoUpdate` with all fields optional but same validators
- [x] 4.3 Add `ProductoResponse` with `id`, `nombre`, `descripcion`, `precio_base`, `stock_cantidad`, `disponible`, `imagen_url`, `creado_en`
- [x] 4.4 Apply `@field_validator('nombre', 'descripcion', mode='before')` calling `sanitize_text`

## 5. Categorias Schemas

- [x] 5.1 Create `backend/categorias/schemas.py` with `CategoriaCreate`: `nombre: str = Field(min_length=1, max_length=255)`, `descripcion: Optional[str] = None`, `padre_id: Optional[int] = None`
- [x] 5.2 Add `CategoriaUpdate` with optional fields
- [x] 5.3 Add `CategoriaResponse` with `id`, `nombre`, `descripcion`, `padre_id`, `creado_en`
- [x] 5.4 Apply `@field_validator('nombre', 'descripcion', mode='before')` calling `sanitize_text`
- [x] 5.5 Add `@field_validator('nombre', mode='before')` that calls `.strip()` to reject whitespace-only names

## 6. Ingredientes Schemas

- [x] 6.1 Create `backend/ingredientes/schemas.py` with `IngredienteCreate`: `nombre: str = Field(min_length=1, max_length=255)`, `es_alergeno: bool = False`
- [x] 6.2 Add `IngredienteUpdate` with optional fields
- [x] 6.3 Add `IngredienteResponse` with `id`, `nombre`, `es_alergeno`, `creado_en`
- [x] 6.4 Apply `@field_validator('nombre', mode='before')` calling `sanitize_text`

## 7. Pedidos Schemas

- [x] 7.1 Create `backend/pedidos/schemas.py` with `DetallePedidoCreate`: `producto_id: int`, `cantidad: int = Field(ge=1)`, `ingredientes_excluidos: Optional[list[int]] = None`
- [x] 7.2 Add `PedidoCreate`: `direccion_entrega_id: int`, `forma_pago_id: int`, `observacion: Optional[str] = Field(default=None, max_length=500)`, `items: list[DetallePedidoCreate] = Field(min_length=1)`
- [x] 7.3 Add `PedidoResponse` and `DetallePedidoResponse` with snapshot fields
- [x] 7.4 Apply `@field_validator('observacion', mode='before')` on PedidoCreate calling `sanitize_text`

## 8. Pagos Schemas

- [x] 8.1 Create `backend/pagos/schemas.py` with `PagoCreate`: `pedido_id: int`, `forma_pago_id: int`
- [x] 8.2 Add `WebhookIPNRequest` with MercadoPago IPN fields: `id: str`, `topic: str`
- [x] 8.3 Add `PagoResponse` with `id`, `pedido_id`, `mp_payment_id`, `mp_status`, `external_reference`, `creado_en`

## 9. Direcciones Schemas

- [x] 9.1 Create `backend/direcciones/schemas.py` with `DireccionCreate`: `alias: str = Field(min_length=1, max_length=100)`, `linea1: str = Field(min_length=1, max_length=255)`, `piso: Optional[str] = None`, `departamento: Optional[str] = None`, `ciudad: str = Field(min_length=1, max_length=100)`, `codigo_postal: str = Field(min_length=4, max_length=10)`, `referencia: Optional[str] = Field(default=None, max_length=255)`, `es_principal: bool = False`
- [x] 9.2 Add `DireccionUpdate` with all optional fields
- [x] 9.3 Add `DireccionResponse` with all public fields
- [x] 9.4 Apply `@field_validator('alias', 'linea1', 'referencia', mode='before')` calling `sanitize_text`

## 10. Tests

- [x] 10.1 Create `backend/tests/test_sanitize.py` — unit tests for `sanitize_text`: strips script tags, strips HTML tags, passes clean text, handles None, handles empty string
- [x] 10.2 Create `backend/tests/test_auth_schemas.py` — test LoginRequest rejects bad email, RegisterRequest rejects short password, RegisterRequest sanitizes nombre
- [x] 10.3 Create `backend/tests/test_producto_schemas.py` — test negative price rejected, negative stock rejected, script tag stripped from nombre
- [x] 10.4 Create `backend/tests/test_pedido_schemas.py` — test cantidad=0 rejected, empty items list rejected
- [x] 10.5 Run `cd backend && python -m pytest tests/test_sanitize.py tests/test_auth_schemas.py tests/test_producto_schemas.py tests/test_pedido_schemas.py -v` and verify all pass
